"""Matched one-shot Responses and managed Agents API pack-authoring experiments.

Explicit allowlisted inputs, frozen requests, no paid retries or tier fallback.
The Agents API has no documented per-session hard dollar cap: polling is a
watchdog, not a billing guarantee. Outstanding runs retain their reservations.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

import httpx

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "storyscenes"
DEFAULT_CAMPAIGN = HERE / "design/agents_api_trial_20261024"
MODELS = ("gpt-6-luna", "gpt-6.1-sol")
# Official Flex rates checked 2026-10-24: input, cached read, 30m write, output.
RATES = {"gpt-6-luna": (.05, .005, .0625, .25), "gpt-6.1-sol": (1, .05, 1.25, 5)}
INPUTS = (
    "story.py", "storyscenes/__init__.py", "storyscenes/runtime.py",
    "storyscenes/smallest_sea.py", "storyscenes/smallest_sea_prose.py",
    "storyscenes/test_smallest_sea.py", "storyscenes/MINI_ADVENTURES.md",
    "storyscenes/EXPERIMENT_RETROSPECTIVE.md",
    "storyscenes/mini_adventures/__init__.py", "storyscenes/mini_adventures/local_play.py",
    "storyscenes/mini_adventures/test_local_play.py", "storyscenes/mini_adventures/review.py",
    "storyscenes/mini_adventures/inventory.py",
)
PREFIX = "storyscenes/mini_adventures/kite/"


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
        temp = stream.name
    os.replace(temp, path)


def digest(data):
    return hashlib.sha256(data).hexdigest()


@contextmanager
def campaign_lock(path):
    path.mkdir(parents=True, exist_ok=True)
    with (path / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


class Ledger:
    def __init__(self, campaign):
        self.path = campaign / "budget.json"
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {
            "authorized_usd": 10, "authorization": "User authorized up to $10 for one-shot versus Agents API trial", "entries": []}

    def reserve(self, arm, amount):
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError("Invalid reservation")
        if sum(e["reserved_usd"] for e in self.data["entries"]) + amount > self.data["authorized_usd"]:
            raise ValueError("Campaign budget exhausted")
        index = len(self.data["entries"])
        self.data["entries"].append({"arm": arm, "reserved_usd": amount, "status": "outstanding"})
        save(self.path, self.data)
        return index

    def settle(self, index, cost, **details):
        entry = self.data["entries"][index]
        if cost is not None:
            entry.update(reserved_usd=cost, status="returned_estimate")
        entry.update(details)
        save(self.path, self.data)


def usage_cost(model, usage, tier="flex"):
    if not isinstance(usage, dict) or tier not in ("flex", "default", "standard"):
        return None
    if not all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens")):
        return None
    inp, cached, write, output = RATES[model]
    details = usage.get("input_tokens_details") or {}
    read = details.get("cached_tokens", 0)
    if type(read) is not int or not 0 <= read <= usage["input_tokens"]:
        return None
    # Bound missing cache-write accounting at the highest published 12h write
    # rate, and long-context rates conservatively at 2x for both model families.
    return 2 * (1 if tier == "flex" else 2) * (
        (usage["input_tokens"] - read) * max(inp, 2 * write)
        + read * cached + usage["output_tokens"] * output) / 1e6


def bundle_schema():
    return {"type": "object", "properties": {"files": {"type": "array", "items": {
        "type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"], "additionalProperties": False}}},
        "required": ["files"], "additionalProperties": False}


def validate_bundle(value):
    if not isinstance(value, dict) or set(value) != {"files"} or not isinstance(value["files"], list):
        raise ValueError("Expected a files bundle")
    files = {}
    for row in value["files"]:
        if not isinstance(row, dict) or set(row) != {"path", "content"}:
            raise ValueError("Invalid file record")
        name, text = row["path"], row["content"]
        if not isinstance(name, str) or not isinstance(text, str):
            raise ValueError("Text files required")
        path = PurePosixPath(name)
        if (not name.startswith(PREFIX) or ".." in path.parts or "\\" in name
                or str(path) != name or any(p.startswith(".") for p in path.parts)
                or path.suffix not in (".py", ".md", ".json") or name in files):
            raise ValueError(f"Unsafe or duplicate output path: {name}")
        files[name] = text
    required = {PREFIX + n for n in ("__init__.py", "world.py", "test_world.py", "reference_story.md", "scene_inventory.json", "README.md")}
    if not required <= files.keys() or len(files) > 30 or sum(len(t.encode()) for t in files.values()) > 2_000_000:
        raise ValueError("Missing required outputs or oversized bundle")
    return files


def prepare(campaign, model, mode):
    arm = campaign / f"{model}_{mode}"
    arm.mkdir(parents=True, exist_ok=False)
    files = {name: (ROOT / name).read_text() for name in INPUTS}
    files["check_pack.py"] = (HERE / "authoring_api_check.py").read_text()
    task = (HERE / "authoring_api_task.md").read_text()
    files["TASK.md"] = task
    for name, text in files.items():
        target = arm / "input" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    settings = {"model": model, "mode": mode, "reasoning": "low", "service_tier": "flex",
        "source_hashes": {n: digest(t.encode()) for n, t in files.items()},
        "idempotency_key": str(uuid.uuid4()), "timeout_seconds": 900,
        "agent_stop_usd": .7 if model == "gpt-6-luna" else 1.2}
    if mode == "oneshot":
        body = {"model": model, "service_tier": "flex", "reasoning": {"effort": "low"},
            "store": False, "max_output_tokens": 32000,
            "input": [{"role": "developer", "content": task},
                      {"role": "user", "content": "Supplied read-only files:\n" + json.dumps(files, ensure_ascii=False)}],
            "text": {"format": {"type": "json_schema", "name": "authored_pack", "strict": True, "schema": bundle_schema()}}}
    else:
        body = {"agent": {"model": model, "service_tier": "flex", "reasoning": {"effort": "low"},
            "multi_agent": {"enabled": False}, "instructions": "Complete TASK.md. Work only in the supplied workspace. No network or paid calls. Save /workspace/outputs/bundle.json before finishing. Aim to finish in 12 minutes."},
            "environment": {"type": "openai_hosted", "container_size": "small", "network": {"access": "disabled"},
                "files": [{"type": "inline", "path": "/workspace/" + n,
                           "data": base64.b64encode(t.encode()).decode()} for n, t in files.items()]},
            "input": task, "metadata": {"experiment": "storyscenes_authoring_20261024", "arm": arm.name,
                                        "request_id": settings["idempotency_key"]}}
    save(arm / "request.json", body)
    settings["request_sha256"] = digest((arm / "request.json").read_bytes())
    save(arm / "settings.json", settings)
    return arm


class API:
    def __init__(self, key):
        self.client = httpx.Client(base_url="https://api.openai.com/v1/", timeout=30,
            headers={"Authorization": "Bearer " + key, "OpenAI-Beta": "agents=v1"})

    def request(self, method, path, **kwargs):
        response = self.client.request(method, path, **kwargs)
        if response.is_error:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:2000]}")
        return response

    def pages(self, path):
        rows, after = [], None
        for _ in range(100):
            page = self.request("GET", path, params={"limit": 100, **({"after": after} if after else {})}).json()
            rows.extend(page["data"])
            if not page.get("has_more"):
                return rows
            cursor = page.get("last_id") or page["data"][-1]["id"]
            if cursor == after:
                raise RuntimeError("Pagination did not advance")
            after = cursor
        raise RuntimeError("Pagination limit reached")


def collect_agent(api, arm, sid):
    for collection in ("items", "turns", "artifacts"):
        rows = api.pages(f"agents/sessions/{sid}/{collection}")
        save(arm / f"{collection}.json", rows)
        if collection == "artifacts":
            for artifact in rows:
                if artifact["path"] == "/workspace/outputs/bundle.json":
                    raw = api.request("GET", f"agents/sessions/{sid}/artifacts/{artifact['id']}/content").content
                    if len(raw) > 2_500_000:
                        raise ValueError("Artifact too large")
                    save(arm / "bundle.json", json.loads(raw))


def cleanup(api, arm, sid):
    errors = []
    try:
        api.request("POST", f"agents/sessions/{sid}/events", json={"events": [{"type": "agent.session.input.cancel"}]})
    except Exception as exc:
        errors.append(str(exc))
    for attempt in range(6):
        try:
            response = api.request("DELETE", f"agents/sessions/{sid}")
            save(arm / "cleanup.json", {"deleted": True,
                 "response": response.json() if response.content else None, "prior_errors": errors})
            return
        except Exception as exc:
            errors.append(str(exc))
            time.sleep(5)
    save(arm / "cleanup.json", {"deleted": False, "errors": errors})
    raise RuntimeError(f"Cleanup unconfirmed for {sid}; inspect before further spending")


def run(arm, key):
    settings = json.loads((arm / "settings.json").read_text())
    if digest((arm / "request.json").read_bytes()) != settings["request_sha256"]:
        raise ValueError("Prepared request changed")
    if (arm / "dispatch.json").exists():
        raise ValueError("Already dispatched; never automatically retry an uncertain paid request")
    body = json.loads((arm / "request.json").read_text())
    ledger = Ledger(arm.parent)
    model, mode = settings["model"], settings["mode"]
    reserve = (1 if model == "gpt-6.1-sol" else .15) if mode == "oneshot" else (5 if model == "gpt-6.1-sol" else 2)
    index = ledger.reserve(arm.name, reserve)
    save(arm / "dispatch.json", {"reservation_index": index, "started_at": time.time(), "idempotency_key": settings["idempotency_key"]})
    api, sid, session = API(key), None, None
    started = time.monotonic()
    try:
        response = api.request("POST", "responses" if mode == "oneshot" else "agents/sessions", json=body,
            headers={"Idempotency-Key": settings["idempotency_key"]}, timeout=900 if mode == "oneshot" else 60).json()
        save(arm / "response.json", response)
        if mode == "oneshot":
            cost = usage_cost(model, response.get("usage"), response.get("service_tier"))
            ledger.settle(index, cost, usage=response.get("usage"))
            served = response.get("model", "")
            if response.get("status") != "completed" or response.get("service_tier") != "flex" or not (served == model or served.startswith(model + "-")):
                raise ValueError("Incomplete response or unexpected model/tier")
            text = "".join(p["text"] for i in response["output"] if i["type"] == "message"
                           for p in i["content"] if p["type"] == "output_text")
            save(arm / "bundle.json", json.loads(text))
        else:
            sid = response["id"]
            session = response
            save(arm / "session.json", session)
            turns = []
            while True:
                session = api.request("GET", f"agents/sessions/{sid}").json()
                save(arm / "session.json", session)
                turns = api.pages(f"agents/sessions/{sid}/turns")
                save(arm / "turns.json", turns)
                elapsed = time.monotonic() - started
                cost = usage_cost(model, session.get("usage"))
                with (arm / "progress.jsonl").open("a") as log:
                    log.write(json.dumps({"elapsed": elapsed, "status": session["status"], "usage": session.get("usage"), "cost_upper": cost}) + "\n")
                print(arm.name, session["status"], "seconds", round(elapsed), "model-cost upper", cost, flush=True)
                if session["agent"]["model"] != model or session["agent"]["service_tier"] != "flex":
                    raise ValueError("Unexpected agent model/tier policy")
                if session["status"] == "idle" and turns and all(t["status"] in ("completed", "failed", "cancelled") for t in turns):
                    break
                if session["status"] in ("failed", "requires_action"):
                    raise RuntimeError(f"Agent stopped: {session['status']}")
                if elapsed > settings["timeout_seconds"] or (cost is not None and cost > settings["agent_stop_usd"]):
                    raise RuntimeError("Agent watchdog stop: time or spending threshold")
                if elapsed > 300 and (not session.get("usage") or session["usage"].get("total_tokens", 0) == 0):
                    raise RuntimeError("Agent watchdog stop: usage unavailable after five minutes")
                time.sleep(10)
            collect_agent(api, arm, sid)
            # Keep a sandbox/accounting margin and classify this as an estimate.
            cost = usage_cost(model, session.get("usage"))
            ledger.settle(index, None if cost is None else cost + .10, usage=session.get("usage"), sandbox_margin_usd=.10)
        if (arm / "bundle.json").exists():
            validate_bundle(json.loads((arm / "bundle.json").read_text()))
        save(arm / "outcome.json", {"returned_bundle": (arm / "bundle.json").exists(), "elapsed_seconds": time.monotonic() - started})
    except BaseException as exc:
        save(arm / "error.json", {"error": f"{type(exc).__name__}: {exc}", "session_id": sid})
        raise
    finally:
        if sid:
            cleanup(api, arm, sid)
        api.client.close()


def recover(arm, key):
    """Find only this arm's session, preserve artifacts, and stop/clean it up.

    Never repeat session creation. A creation timeout may have started paid work
    even if the client did not receive its ID. Match our unique request metadata.
    """
    if not (arm / "dispatch.json").exists():
        raise ValueError("This arm was never dispatched")
    settings = json.loads((arm / "settings.json").read_text())
    if settings["mode"] != "agent":
        raise ValueError("Recovery is only for managed sessions")
    api = API(key)
    try:
        if (arm / "session.json").exists():
            sid = json.loads((arm / "session.json").read_text())["id"]
        else:
            matches = [s for s in api.pages("agents/sessions")
                       if (s.get("metadata") or {}).get("request_id") == settings["idempotency_key"]]
            if len(matches) != 1:
                raise RuntimeError(f"Found {len(matches)} matching sessions; no creation retried")
            sid = matches[0]["id"]
        session = api.request("GET", f"agents/sessions/{sid}").json()
        save(arm / "session.json", session)
        try:
            collect_agent(api, arm, sid)
        finally:
            cleanup(api, arm, sid)
    finally:
        api.client.close()


def sandbox_policy(isolated):
    # Permit Darwin process/bootstrap metadata while restricting file contents,
    # writes and all network operations. Deny-default blocks Python startup on
    # some macOS releases before it can even report an error.
    work = json.dumps(str(isolated))
    policy = '(version 1)(allow default)(deny network*)'
    policy += ('(deny file-read-data (require-all (require-any '
               '(subpath "/Users") (subpath "/Volumes") (subpath "/private/tmp") '
               f'(subpath "/private/var/folders")) (require-not (subpath {work}))))')
    policy += ('(deny file-write* (require-all (require-not (subpath "/dev")) '
               f'(require-not (subpath {work}))))')
    return policy


def check(arm):
    settings = json.loads((arm / "settings.json").read_text())
    for name, expected in settings["source_hashes"].items():
        if digest((arm / "input" / name).read_bytes()) != expected:
            raise ValueError(f"Validation source changed: {name}")
    files = validate_bundle(json.loads((arm / "bundle.json").read_text()))
    workspace = arm / "workspace"
    shutil.copytree(arm / "input", workspace)
    for name, text in files.items():
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    # Do not execute generated code with repository/key access. Seatbelt is
    # available on this Mac; fail closed elsewhere until a sandbox is supplied.
    if not Path("/usr/bin/sandbox-exec").exists():
        raise RuntimeError("Isolated validation requires macOS sandbox-exec")
    with tempfile.TemporaryDirectory(prefix="storyscenes-api-check-") as td:
        isolated = Path(td).resolve()
        shutil.copytree(workspace, isolated / "work")
        work = isolated / "work"
        policy = sandbox_policy(isolated)
        env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(isolated), "TMPDIR": str(isolated), "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run(["/usr/bin/sandbox-exec", "-p", policy, str(Path(sys.executable).resolve()), "-I",
            str(work / "check_pack.py"), str(work)], cwd=work, env=env, capture_output=True, text=True, timeout=180)
        save(arm / "validation_process.json", {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if (work / "check.json").exists():
            shutil.copyfile(work / "check.json", arm / "check.json")
        elif result.returncode == 0:
            raise RuntimeError("Validator exited without an assessment")
        print(result.stdout, result.stderr)
        if result.returncode:
            raise RuntimeError("Isolated validator process failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run", "check", "recover"))
    parser.add_argument("--campaign", type=Path, default=DEFAULT_CAMPAIGN)
    parser.add_argument("--model", choices=MODELS, default="gpt-6-luna")
    parser.add_argument("--mode", choices=("oneshot", "agent"), default="agent")
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    campaign = args.campaign.resolve()
    arm = campaign / f"{args.model}_{args.mode}"
    with campaign_lock(campaign):
        if args.phase == "prepare":
            print(prepare(campaign, args.model, args.mode))
        elif args.phase in ("run", "recover"):
            key = args.api_key_file.read_text().strip() if args.api_key_file else os.environ["OPENAI_API_KEY"]
            (run if args.phase == "run" else recover)(arm, key)
        else:
            check(arm)


if __name__ == "__main__":
    main()
