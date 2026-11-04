"""Grade saved trial prose with the unchanged standard Terra story-set judge."""
import argparse
import asyncio
from collections import Counter
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "storyscenes"))
import harbor_trial as harbor

f = harbor.f
OUT = HERE / "standard_judge_v1"
CAMPAIGN = ROOT / "storyscenes/runs/harbor_iteration_campaign"


def prepare():
    money = harbor.campaign(CAMPAIGN)
    OUT.mkdir(exist_ok=False)
    inputs, provenance = [], {}
    for pack in ("bakery", "greenhouse"):
        source = HERE / "round_04" / f"{pack}_holdout" / "stories.jsonl"
        rows = [json.loads(line) for line in source.read_text().splitlines()]
        assert len(rows) == 100
        item = f.quality.select_set(pack, rows, 777, count=10)
        inputs.append(item)
        selected = [rows[s["source_index"]] for s in item["stories"]]
        provenance[pack] = dict(source=str(source.relative_to(ROOT)), sha256=f.digest(source),
            positions=[dict(id=s["id"], seed=r["seed"], scenes=r["scene_count"])
                       for s, r in zip(item["stories"], selected)],
            exact_texts=len({r["story"] for r in selected}),
            outcomes=dict(Counter(r["final_state"]["story.outcome"] for r in selected)))
        body = harbor.harbor_judge_protocol.request_body(f.quality, item)
        body["store"] = False
        f.save(OUT / f"{pack}.planned.json", body)
    sources = [Path(__file__), Path(harbor.__file__), Path(f.__file__),
               Path(harbor.harbor_judge_protocol.__file__), Path(f.quality.__file__),
               Path(f.quality.legacy.__file__), Path(f.trial_cost.__file__),
               ROOT / "storyscenes/api_requests.py"]
    hashes = {}
    for source in sources:
        relative = source.relative_to(ROOT)
        target = OUT / "_source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[str(relative)] = f.digest(source)
    f.save(OUT / "inputs.json", inputs)
    f.save(OUT / "provenance.json", provenance)
    f.save(OUT / "settings.json", dict(model=f.quality.DEFAULT_MODEL, count_per_pack=10,
        selection_seed=777, duplicates_retained=True, story_only=True,
        campaign=str(CAMPAIGN), money=money, source_hashes=hashes,
        inputs_sha256=f.digest(OUT / "inputs.json"),
        request_hashes={p: f.digest(OUT / f"{p}.planned.json") for p in provenance},
        pricing_note="Uses the existing historical Terra rate table; not invoice reconciliation."))
    print(json.dumps(provenance, indent=2))


async def judge(key):
    from openai import AsyncOpenAI
    settings = json.loads((OUT / "settings.json").read_text())
    for name, digest in settings["source_hashes"].items():
        assert f.digest(ROOT / name) == f.digest(OUT / "_source" / name) == digest
    assert f.digest(OUT / "inputs.json") == settings["inputs_sha256"]
    money = harbor.campaign(CAMPAIGN)
    assert money == settings["money"]
    budget = f.Budget(CAMPAIGN / "budget.json", money["remaining_cap_usd"])
    f.load_key(key)
    results = []
    async with AsyncOpenAI(base_url="https://api.openai.com/v1", timeout=900, max_retries=0) as client:
        for item in json.loads((OUT / "inputs.json").read_text()):
            pack = item["script"]
            planned = OUT / f"{pack}.planned.json"
            assert f.digest(planned) == settings["request_hashes"][pack]
            body = json.loads(planned.read_text())
            result_path = OUT / f"{pack}.result.json"
            if result_path.exists():
                results.append(json.loads(result_path.read_text()))
                continue
            result = dict(script=pack, ok=False)
            try:
                text = await asyncio.wait_for(f.api_artifact(client, budget, OUT, pack, body), 900)
                response = json.loads((OUT / f"{pack}.response.json").read_text())
                served = response.get("model", "")
                if response.get("service_tier") != "flex" or not (
                    served == settings["model"] or served.startswith(settings["model"] + "-")):
                    raise ValueError("Unexpected model/tier; no fallback authorized")
                result.update(harbor.harbor_judge_protocol.validate(f.quality, json.loads(text), item))
                result["ok"] = True
            except Exception as exc:
                result["error"] = f"{type(exc).__name__}: {exc}"
            response_path = OUT / f"{pack}.response.json"
            if response_path.exists():
                response = json.loads(response_path.read_text())
                result["response"] = {k: response.get(k) for k in ("id", "model", "status", "service_tier", "usage")}
            f.save(result_path, result)
            results.append(result)
            print(pack, "complete" if result["ok"] else result["error"], flush=True)
    f.save(OUT / "summary.json", f.quality.summarize(results))
    f.save(OUT / "campaign_budget_after.json", json.loads(budget.path.read_text()))
    (OUT / "REPORT.md").write_text(f.quality.render_report(results) + "\n\n"
        "Saved round-4 holdout pools, 100 positions per pack, seeds 1000-1049 at both lengths. "
        "Uniform selection seed 777, ten per pack, duplicates retained. Only prose and the "
        "standard calibration were sent, not source, traces, references or manual reviews. "
        "No QA graded; no generator edits or automatic paid retries. "
        "Cost uses the historical Terra rate table, not a newly verified price or invoice.\n")
    print(json.dumps(f.quality.summarize(results), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "judge"))
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare()
    else:
        asyncio.run(judge(args.api_key_file))
