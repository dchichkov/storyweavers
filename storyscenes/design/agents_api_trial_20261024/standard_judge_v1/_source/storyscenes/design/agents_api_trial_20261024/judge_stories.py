"""Judge untouched Sol prose using the existing Terra rubric and campaign cap."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "storyscenes/evaluation"))
from storyscenes import authoring_api as api, harbor_judge_protocol as protocol
import openai_world_set_quality as quality

OUT = HERE / "standard_judge_v1"
SOURCE = HERE / "gpt-6.1-sol_oneshot/check.json"


def prepare():
    report = json.loads(SOURCE.read_text())
    attempts = report["attempts"]
    if len(attempts) != 100 or not all(row["ok"] for row in attempts):
        raise ValueError("Expected all 100 saved runnable positions, not a filtered subset")
    rows = [row["row"] for row in attempts]
    item = quality.select_set("sol_oneshot_kite", rows, 777, count=10)
    body = protocol.request_body(quality, item)
    body["store"] = False
    OUT.mkdir(exist_ok=False)
    api.save(OUT / "input.json", item)
    api.save(OUT / "request.json", body)
    selected = [rows[s["source_index"]] for s in item["stories"]]
    api.save(OUT / "selected_rows.json", selected)
    sources = [Path(__file__), Path(api.__file__), Path(protocol.__file__),
               Path(quality.__file__), Path(quality.legacy.__file__),
               Path(quality.trial_cost.__file__), Path(quality.api_requests.__file__)]
    hashes = {}
    for source in sources:
        relative = source.relative_to(ROOT)
        target = OUT / "_source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[str(relative)] = api.digest(source.read_bytes())
    api.save(OUT / "settings.json", dict(
        model=quality.DEFAULT_MODEL, service_tier="flex", reasoning="none",
        source_sha256=api.digest(SOURCE.read_bytes()), source_hashes=hashes,
        input_sha256=api.digest((OUT / "input.json").read_bytes()),
        request_sha256=api.digest((OUT / "request.json").read_bytes()),
        idempotency_key=str(uuid.uuid4()), duplicates_retained=True,
        exact_texts=len({r["story"] for r in selected}),
        outcomes=dict(Counter(r["final_state"]["story.outcome"] for r in selected)),
        positions=[dict(id=s["id"], seed=r["seed"], scenes=r["scene_count"])
                   for s, r in zip(item["stories"], selected)],
        pricing_note="Budget estimate uses the published Terra STANDARD input plus cache-write premium and output rates as a conservative allowance for this small Flex request; not an invoice.",
        pricing_url="https://developers.openai.com/api/docs/models/gpt-5.6-terra"))
    (OUT / "STORIES.md").write_text("# Random Sol One-Shot Stories\n\n" + "\n\n".join(
        f"## {s['id']}: seed {r['seed']}, {r['scene_count']} scenes\n\n{r['story']}"
        for s, r in zip(item["stories"], selected)) + "\n")
    print(json.dumps({"stories": len(selected), "outcomes": Counter(
        r["final_state"]["story.outcome"] for r in selected)}, indent=2))


def returned_cost(usage):
    if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0
            for k in ("input_tokens", "output_tokens")):
        return None
    cached = (usage.get("input_tokens_details") or {}).get("cached_tokens", 0)
    if type(cached) is not int or not 0 <= cached <= usage["input_tokens"]:
        return None
    return ((usage["input_tokens"] - cached) * 2.5 + cached * .2 + usage["output_tokens"] * 12) / 1e6


def judge(key):
    settings = json.loads((OUT / "settings.json").read_text())
    for name, digest in settings["source_hashes"].items():
        if api.digest((ROOT / name).read_bytes()) != digest:
            raise ValueError(f"Judge source changed: {name}")
    for filename, key_name in (("input.json", "input_sha256"), ("request.json", "request_sha256")):
        if api.digest((OUT / filename).read_bytes()) != settings[key_name]:
            raise ValueError(f"Prepared {filename} changed")
    if api.digest(SOURCE.read_bytes()) != settings["source_sha256"]:
        raise ValueError("Source assessment changed")
    if (OUT / "dispatch.json").exists():
        raise ValueError("Already dispatched; never automatically repeat a paid request")
    body = json.loads((OUT / "request.json").read_text())
    item = json.loads((OUT / "input.json").read_text())
    # UTF-8 byte count deliberately overbounds input tokens for this text-only
    # request. Include the schema and a framing margin, plus all output tokens.
    reserve = (len(json.dumps(body, ensure_ascii=False).encode()) + 4000) * 2.5 / 1e6
    reserve += body["max_output_tokens"] * 12 / 1e6
    ledger = api.Ledger(HERE)
    index = ledger.reserve("sol_oneshot_standard_judge_v1", reserve)
    api.save(OUT / "dispatch.json", dict(reservation_index=index, reserved_usd=reserve,
        started_at=time.time(), idempotency_key=settings["idempotency_key"]))
    client = api.API(key)
    try:
        response = client.request("POST", "responses", json=body, timeout=900,
            headers={"Idempotency-Key": settings["idempotency_key"]}).json()
        api.save(OUT / "response.json", response)
        served = response.get("model", "")
        if response.get("service_tier") != "flex" or not (served == settings["model"] or served.startswith(settings["model"] + "-")):
            raise ValueError("Unexpected model/tier; reservation retained")
        estimate = returned_cost(response.get("usage"))
        ledger.settle(index, estimate, usage=response.get("usage"), pricing_note=settings["pricing_note"])
        if response.get("status") != "completed":
            raise ValueError("Incomplete response")
        result = protocol.validate(quality, json.loads(quality.final_text(response)), item)
        result.update(script=item["script"], ok=True, budget_estimate_usd=estimate,
                      response={k: response.get(k) for k in ("model", "service_tier", "status", "usage")})
        api.save(OUT / "result.json", result)
        print(json.dumps({k: result[k] for k in ("rating", "diversity", "plot_groups", "budget_estimate_usd")}, indent=2))
    except BaseException as exc:
        api.save(OUT / "error.json", {"error": f"{type(exc).__name__}: {exc}"})
        raise
    finally:
        client.client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "judge"))
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    with api.campaign_lock(HERE):
        if args.phase == "prepare":
            prepare()
        else:
            judge(args.api_key_file.read_text().strip())
