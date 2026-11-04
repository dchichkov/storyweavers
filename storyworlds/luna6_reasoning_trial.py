"""Bounded adapter over the existing matched StoryWorld prompt-trial pipeline.

Uses the unchanged 20-reference authoring contract and story-set judge rubric.
Only author reasoning varies; judge reasoning is fixed. Generated programs run
without credentials or repository access in the existing macOS sandbox pattern.
"""
from __future__ import annotations

import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

import prompt_trials as pipeline
import openai_world_set_quality as judge
from openai import AsyncOpenAI

ROOT = pipeline.ROOT
CAMPAIGN = ROOT / "storyworlds/batches/luna6_reasoning_20261024"
REFERENCES = ROOT / "storyworlds/reference_sets/luna_top20_20260907.json"
MODEL = "gpt-6-luna"
LEVELS = ("low", "medium", "high")
NAMES = [f"luna6_reasoning_{level}_20261024" for level in LEVELS]
RATES = (.05, .005, .0625, .25)
CAP = 3.0
ORIGINAL_CALL = pipeline.service.call_one


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cost(usage):
    if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0
            for k in ("input_tokens", "output_tokens")):
        return None
    inputs, outputs = usage["input_tokens"], usage["output_tokens"]
    details = usage.get("input_tokens_details") or {}
    cached = details.get("cached_tokens", 0)
    if type(cached) is not int or not 0 <= cached <= inputs:
        return None
    # Bound unknown writes at the published 12h write rate; reasoning is output.
    return ((inputs - cached) * .125 + cached * .005 + outputs * .25) / 1e6


class Ledger:
    def __init__(self, path):
        self.path = Path(path)
        self.data = pipeline.read(self.path) if self.path.exists() else {
            "cap_usd": CAP, "pricing_date": "2026-10-24", "entries": {},
            "pricing_url": "https://developers.openai.com/api/docs/pricing",
            "note": "Conservative returned-usage estimates, not invoices. Unknown calls retain reservations."}

    def reserve(self, key, body):
        if key in self.data["entries"]:
            raise ValueError("Previously dispatched request is never automatically repeated")
        # UTF-8 bytes upper-bound text token count, plus ample message overhead.
        bound = (len(json.dumps(body["input"], ensure_ascii=False).encode()) + 2048) * .125 / 1e6
        bound += body["max_output_tokens"] * .25 / 1e6
        if self.total() + bound > self.data["cap_usd"]:
            raise ValueError("Trial spending cap reached")
        self.data["entries"][key] = {"reserved_usd": bound, "status": "outstanding",
            "request_sha256": hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()}
        self.save()

    def settle(self, key, response):
        entry = self.data["entries"][key]
        estimate = cost(response.get("usage"))
        if response.get("model", "").startswith(MODEL) and response.get("service_tier") == "flex" and estimate is not None:
            entry.update(reserved_usd=estimate, status="returned_estimate")
        entry.update(response_id=response.get("id"), model=response.get("model"),
                     service_tier=response.get("service_tier"), usage=response.get("usage"))
        self.save()

    def total(self):
        return sum(e["reserved_usd"] for e in self.data["entries"].values())

    def save(self):
        pipeline.save(self.path, self.data)


def sandbox_policy(work):
    allowed = [work, Path(sys.prefix) / "lib/python3.12/site-packages"]
    exceptions = " ".join(f'(subpath {json.dumps(str(p))})' for p in allowed)
    return ('(version 1)(allow default)(deny network*)'
        '(deny file-read-data (require-all (require-any (subpath "/Users") '
        '(subpath "/Volumes") (subpath "/private/tmp") (subpath "/private/var/folders")) '
        f'(require-not (require-any {exceptions}))))'
        '(deny file-write* (require-all (require-not (subpath "/dev")) '
        f'(require-not (subpath {json.dumps(str(work))}))))')


def local_run(script, flags, timeout, *, standalone=False, hash_seed="0"):
    if not script.exists():
        return {"ok": False, "error": "missing generated script"}
    if not Path("/usr/bin/sandbox-exec").exists():
        raise RuntimeError("Generated-code audit requires macOS sandbox-exec")
    with tempfile.TemporaryDirectory(prefix="luna6-world-audit-") as td:
        work = Path(td).resolve()
        local = work / script.relative_to(ROOT)
        local.parent.mkdir(parents=True)
        shutil.copyfile(script, local)
        shared = work / "storyworlds"
        for name in ("results.py", "asp.py"):
            shutil.copyfile(ROOT / "storyworlds" / name, shared / name)
        env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(work),
               "TMPDIR": str(work), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": hash_seed}
        # The executable resolves outside this venv; explicitly retain installed
        # solver packages without exposing the repository on the import path.
        packages = str(Path(sys.prefix) / "lib/python3.12/site-packages")
        env["PYTHONPATH"] = packages if standalone else str(shared) + os.pathsep + packages
        try:
            proc = subprocess.run(["/usr/bin/sandbox-exec", "-p", sandbox_policy(work),
                str(Path(sys.executable).resolve()), str(local), *flags], cwd=work, env=env,
                capture_output=True, text=True, timeout=timeout)
            return {"ok": proc.returncode == 0, "returncode": proc.returncode,
                    "stdout": proc.stdout, "stderr": proc.stderr}
        except (subprocess.TimeoutExpired, OSError) as exc:
            return {"ok": False, "error": str(exc)}


def prepare():
    CAMPAIGN.mkdir(parents=True, exist_ok=False)
    refs = pipeline.read(REFERENCES)
    assert len(refs) == 20
    assert all(sha(ROOT / r["source"]) == r["sha256"] for r in refs)
    configs = []
    for level, name in zip(LEVELS, NAMES):
        args = pipeline.build_parser().parse_args(["prepare", name, "--seed", "2026102401",
            "--example-manifest", str(REFERENCES), "--per-example", "1", "--unique-tasks",
            "--model", MODEL, "--reasoning-effort", level, "--concurrency", "5",
            "--local-samples", "1000", "--timeout", "45", "--prompt-cache-mode", "explicit"])
        directory = pipeline.prepare(args)
        config = pipeline.read(directory / "trial.json")
        config.update(judge=MODEL, judge_reasoning="medium", compact_checks=True)
        # Freeze store=False too, and avoid sharing cache keys between reasoning arms.
        for arm in config["arms"]:
            path = ROOT / arm["requests"]
            requests = pipeline.jsonl(path)
            for row in requests:
                row["body"]["store"] = False
                row["body"]["prompt_cache_key"] += f":luna6:{level}"
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in requests))
            arm["requests_sha256"] = sha(path)
        pipeline.save(directory / "trial.json", config)
        configs.append(config)
    task_lists = [[{k: r["job"][k] for k in ("seed", "words", "setting", "features", "style", "domain")}
                   for a in c["arms"] for r in pipeline.jsonl(ROOT / a["requests"])] for c in configs]
    assert task_lists[0] == task_lists[1] == task_lists[2] and len(task_lists[0]) == 20
    pipeline.save(CAMPAIGN / "protocol.json", {"model": MODEL, "levels": LEVELS, "trials": NAMES,
        "attempts_per_level": 20, "local_samples": 1000, "judge_model": MODEL, "judge_reasoning": "medium",
        "judge_protocol": judge.PROTOCOL, "judge_stories": 10, "duplicates_retained": True,
        "seed": 2026102401, "generation_only_variable": "reasoning effort (apart from output paths/cache keys)",
        "reference_manifest": str(REFERENCES.relative_to(ROOT)), "reference_hashes_verified": True,
        "repairs": "Existing deterministic repair_source only; no manual or model repairs",
        "paid_retries": 0, "service_tier": "flex", "cap_usd": CAP,
        "caveat": "Luna judge scores are not directly interchangeable with historical Terra scores."})
    shutil.copyfile(__file__, CAMPAIGN / "runner_snapshot.py")
    print("Prepared 60 frozen requests; no paid calls.", flush=True)


async def judged_sets(inputs, output, *, concurrency=5, dry_run=False):
    output.mkdir(parents=True, exist_ok=False)
    pipeline.save(output / "inputs.json", inputs)
    pipeline.save(output / "settings.json", {"model": MODEL, "service_tier": "flex",
        "reasoning_effort": "medium", "protocol": judge.PROTOCOL, "max_retries": 0,
        "selection": "10 uniform positions; no deduplication or score filtering"})
    for module in (judge, judge.legacy, pipeline.trial_cost):
        shutil.copyfile(module.__file__, output / Path(module.__file__).name)
    semaphore = asyncio.Semaphore(concurrency)
    async def one(index, item):
        body = judge.request_body(item)
        body.update(model=MODEL, reasoning={"effort": "medium"}, store=False, max_output_tokens=8000)
        pipeline.save(output / f"request_{index:03d}.json", body)
        key = str(output.relative_to(ROOT)) + f":{index}"
        result = {"script": item["script"], "ok": False}
        async with semaphore:
            try:
                LEDGER.reserve(key, body)
                response = (await CLIENT.responses.create(**sdk_body(body))).model_dump(mode="json")
                pipeline.save(output / f"response_{index:03d}.json", response)
                LEDGER.settle(key, response)
                ensure_response(response)
                result.update(judge.validate(json.loads(judge.final_text(response)), item), ok=True)
                result["response"] = {k: response.get(k) for k in ("id", "model", "status", "service_tier", "usage")}
            except Exception as exc:
                result["error"] = f"{type(exc).__name__}: {exc}"
            pipeline.append(output / "quality.jsonl", result)
            print(f"Judge {index + 1}/{len(inputs)}: {'OK' if result['ok'] else result['error']}", flush=True)
        return result
    rows = await asyncio.gather(*(one(i, item) for i, item in enumerate(inputs)))
    summary = judge.summarize(rows)
    summary["reasoning_effort"] = "medium"
    pipeline.save(output / "summary.json", summary)
    return rows


def ensure_response(response):
    if response.get("status") != "completed" or response.get("service_tier") != "flex" or not (
            response.get("model") == MODEL or response.get("model", "").startswith(MODEL + "-")):
        raise ValueError("Incomplete response or unexpected model/tier; no fallback")


def sdk_body(body):
    body = dict(body)
    if "prompt_cache_options" in body:
        body["extra_body"] = {"prompt_cache_options": body.pop("prompt_cache_options")}
    return body


async def generation_call(client, args, job, semaphore, *, request=None):
    key = job.target
    started = time.monotonic()
    async with GLOBAL_SEMAPHORE:
        try:
            LEDGER.reserve(key, request)
            response = await CLIENT.responses.create(**sdk_body(request))
            value = response.model_dump(mode="json")
            # Preserve the paid response even if it violates the requested tier/status.
            LEDGER.settle(key, value)
            row = pipeline.service.response_row(job=job, request=request, response=response,
                error=None, elapsed=time.monotonic() - started)
            try:
                ensure_response(value)
            except ValueError as exc:
                row["error"] = str(exc)
            return row
        except Exception as exc:
            return pipeline.service.response_row(job=job, request=request, response=None,
                error=str(exc), elapsed=time.monotonic() - started)


def configure():
    pipeline.local_run = local_run
    pipeline.service.call_one = generation_call
    judge.DEFAULT_MODEL = MODEL
    pipeline.JUDGE = MODEL
    judge.run_sets = judged_sets
    pipeline.trial_cost.FLEX_RATES[MODEL] = RATES
    # Only this process changes the date; historical source/rates stay untouched.
    pipeline.trial_cost.PRICING_DATE = "2026-10-24"


async def run(phase):
    global LEDGER, CLIENT, GLOBAL_SEMAPHORE
    configure()
    LEDGER = Ledger(CAMPAIGN / "budget.json")
    key = os.environ.get("OPENAI_API_KEY") or (ROOT / ".API_KEY").read_text().strip()
    CLIENT = AsyncOpenAI(api_key=key, base_url="https://api.openai.com/v1", timeout=900, max_retries=0)
    GLOBAL_SEMAPHORE = asyncio.Semaphore(5)
    async with CLIENT:
        if phase in ("run", "generate"):
            # Existing make_client must also remain retry-free, although requests
            # are sent through the shared guarded client above.
            pipeline.service.make_client = lambda args: AsyncOpenAI(api_key=key,
                base_url="https://api.openai.com/v1", timeout=900, max_retries=0)
            await asyncio.gather(*(pipeline.generate(*pipeline.load_trial(name)) for name in NAMES))
        if phase in ("run", "evaluate"):
            for name in NAMES:
                directory, config = pipeline.load_trial(name)
                if list(directory.glob("eval_*")):
                    print(f"Retaining existing evaluation for {name}; no paid repeat.", flush=True)
                    continue
                output = await pipeline.evaluate(directory, config, skip_quality=False)
                settings = pipeline.read(output / "settings.json")
                settings["judge_reasoning"] = "medium"
                pipeline.save(output / "settings.json", settings)
                summary = pipeline.read(output / "summary.json")
                summary["reasoning_effort"] = "medium"
                pipeline.save(output / "summary.json", summary)
    summarize()


def summarize():
    configure()
    rows = []
    for level, name in zip(LEVELS, NAMES):
        directory, config = pipeline.load_trial(name)
        completed = sorted(directory.glob("eval_*/completed.json"))
        if not completed:
            rows.append({"level": level, "complete": False})
            continue
        output = completed[-1].parent
        checks = pipeline.read(output / "checks.json")
        grades = pipeline.jsonl(output / "set_judge/quality.jsonl")
        good = [r for r in grades if r.get("ok")]
        generation = [r for a in config["arms"] for r in pipeline.jsonl((ROOT / a["manifest"]).parent / "responses.jsonl")]
        expenses = [cost((r.get("response") or {}).get("body", {}).get("usage")) for r in generation]
        strict = [c for c in checks if c["final"]["ok"] and c["verify"]["ok"] and c["standalone"]["ok"]
                  and c["hash_seed_replay_equal"] and c["complete_sample_count"]]
        by_script = {r["script"]: r for r in good}
        jointly = [c for c in strict if c["script"] in by_script
                   and by_script[c["script"]]["rating"]["overall"] >= 6
                   and by_script[c["script"]]["diversity"]["overall"] >= 3]
        mean = lambda values: statistics.mean(values) if values else None
        rows.append({"level": level, "complete": True, "attempts": 20,
            "materialized": sum(bool(r.get("materialized")) for r in generation),
            "raw_runnable": sum(c["raw_runnable"] is True for c in checks),
            "strict_pass": len(strict), "rated": len(good),
            "quality": mean([r["rating"]["overall"] for r in good]),
            "diversity": mean([r["diversity"]["overall"] for r in good]),
            "strict_quality6_diversity3": len(jointly),
            "generation_usd_upper": sum(v for v in expenses if v is not None),
            "unpriced_generation": sum(v is None for v in expenses),
            "cost_per_joint_world": (sum(v for v in expenses if v is not None) / len(jointly)) if jointly and all(v is not None for v in expenses) else None,
            "unique_texts": sum(c["exact_unique"] for c in checks),
            "returned_samples": sum(c["samples"] for c in checks)})
    pipeline.save(CAMPAIGN / "summary.json", rows)
    lines = ["# Luna 6 StoryWorld reasoning comparison", "",
        "Twenty matched reference/task pairs per level. Existing authoring prompt and deterministic repairs; 1,000 local draws per world.",
        "Fixed Luna 6 medium/Flex judge, ten uniform story positions with duplicates retained. Scores are conditional on valid ratings; not comparable to historical Terra scores.", "",
        "| Reasoning | Raw runnable /20 | Strict /20 | Rated | Quality /9 | Diversity /9 | Strict + Q≥6 + D≥3 /20 | Generation USD upper |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        if r["complete"]:
            fmt = lambda k: f"{r[k]:.3f}" if r[k] is not None else "-"
            lines.append(f"| {r['level']} | {r['raw_runnable']} | {r['strict_pass']} | {r['rated']} | {fmt('quality')} | {fmt('diversity')} | {r['strict_quality6_diversity3']} | {fmt('generation_usd_upper')} |")
        else:
            lines.append(f"| {r['level']} | pending | | | | | | |")
    lines += ["", "Strict requires full sample count, verify, standalone CLI and replay across hash seeds. Exact-unique texts are not independent plots.",
        "No manual/model repair or rejected-attempt replacement. Luna is both author and judge; manual review remains necessary. QA is sampled locally but not semantically graded by this story-only judge.", ""]
    if (CAMPAIGN / "budget.json").exists():
        ledger = Ledger(CAMPAIGN / "budget.json")
        lines += [f"Total conservative commitment, including grading and unknown outcomes: ${ledger.total():.6f} / ${CAP:.2f}.", ""]
    (CAMPAIGN / "REPORT.md").write_text("\n".join(lines))
    (CAMPAIGN / "DETAILS.md").write_text(pipeline.report(NAMES) +
        "\nAdapter override: all grading uses Luna 6 medium/Flex, with 8,000 output tokens including reasoning.\n")
    print(json.dumps(rows, indent=2), flush=True)


def preflight():
    configure()
    refs = pipeline.read(REFERENCES)
    def one(r):
        script = ROOT / r["source"]
        sampled, rows = pipeline.sample(script, 10, 777, 45)
        verified = local_run(script, ["--verify"], 45)
        pipeline.compact_run(sampled)
        pipeline.compact_run(verified)
        return {"label": r["label"], "sample": sampled, "verify": verified, "samples": len(rows)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks = list(pool.map(one, refs))
    pipeline.save(CAMPAIGN / "reference_preflight.json", checks)
    print(json.dumps({"references": len(checks), "sample_pass": sum(c['sample']['ok'] for c in checks),
        "verify_pass": sum(c['verify']['ok'] for c in checks)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "preflight", "run", "generate", "evaluate", "summarize"))
    args = parser.parse_args()
    if args.phase == "prepare": prepare()
    elif args.phase == "preflight": preflight()
    elif args.phase == "summarize": summarize()
    else:
        with pipeline.trial_lock(CAMPAIGN):
            asyncio.run(run(args.phase))
