"""Evaluate the two frozen microdrama authors with the standard Terra set judge."""
import argparse
import asyncio
from collections import Counter
import importlib
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "storyscenes"))
import factory as f
import harbor_judge_protocol as protocol
from microdrama.authoring_trial_20261024 import evaluate

OUT = HERE / "standard_judge_v1"
PACKS = ("floodgate", "orchard")


def prepare():
    OUT.mkdir(exist_ok=False)
    inputs, provenance = [], {}
    for name in PACKS:
        pack = importlib.import_module(f"microdrama.authoring_trial_20261024.{name}.pack")
        rows = []
        for case, config in enumerate(evaluate.configurations()):
            for seed in range(5):
                row = evaluate.produce(pack, config, seed)
                words = evaluate.validate(pack, row)
                assert row == evaluate.produce(pack, config, seed)
                row.update(case=case, words=words,
                    story=row["title"] + "\n\n" + "\n\n".join(p["text"] for p in row["paragraphs"]))
                rows.append(row)
        pool = OUT / f"{name}.samples.jsonl"
        pool.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        item = f.quality.select_set(name, rows, 777, count=10)
        inputs.append(item)
        selected = [rows[s["source_index"]] for s in item["stories"]]
        provenance[name] = dict(pool_sha256=f.digest(pool), pool_positions=len(rows),
            pool_exact_texts=len({r["story"] for r in rows}),
            pool_outcomes=dict(Counter(r["final"]["valley.outcome"] for r in rows)),
            selected_exact_texts=len({r["story"] for r in selected}),
            selected_outcomes=dict(Counter(r["final"]["valley.outcome"] for r in selected)),
            positions=[dict(id=s["id"], case=r["case"], seed=r["seed"], config=r["config"],
                            outcome=r["final"]["valley.outcome"])
                       for s, r in zip(item["stories"], selected)],
            seed_changes_text=any(len({r["story"] for r in rows if r["case"] == case}) > 1
                                  for case in range(8)))
        body = protocol.request_body(f.quality, item)
        body["store"] = False
        f.save(OUT / f"{name}.planned.json", body)
    sources = [Path(__file__), Path(evaluate.__file__), ROOT / "microdrama/engine.py",
               Path(f.__file__), Path(protocol.__file__), Path(f.quality.__file__),
               Path(f.quality.legacy.__file__), Path(f.trial_cost.__file__),
               ROOT / "storyscenes/api_requests.py"]
    sources += [HERE / name / "pack.py" for name in PACKS]
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
        sampling="8 boolean configurations x seeds 0..4, config-major order; uniform positions without replacement",
        local_spend_guard_usd=1.0, source_hashes=hashes,
        inputs_sha256=f.digest(OUT / "inputs.json"),
        request_hashes={p: f.digest(OUT / f"{p}.planned.json") for p in PACKS},
        pricing_note="Historical repository Terra rate table; not current pricing or invoice reconciliation."))
    print(json.dumps(provenance, indent=2))


async def judge(key):
    from openai import AsyncOpenAI
    settings = json.loads((OUT / "settings.json").read_text())
    for name, digest in settings["source_hashes"].items():
        assert f.digest(ROOT / name) == f.digest(OUT / "_source" / name) == digest
    assert f.digest(OUT / "inputs.json") == settings["inputs_sha256"]
    budget = f.Budget(OUT / "budget.json", settings["local_spend_guard_usd"])
    f.load_key(key)
    results = []
    async with AsyncOpenAI(base_url="https://api.openai.com/v1", timeout=900, max_retries=0) as client:
        for item in json.loads((OUT / "inputs.json").read_text()):
            name = item["script"]
            planned = OUT / f"{name}.planned.json"
            assert f.digest(planned) == settings["request_hashes"][name]
            body = json.loads(planned.read_text())
            result_path = OUT / f"{name}.result.json"
            if result_path.exists():
                results.append(json.loads(result_path.read_text()))
                continue
            result = dict(script=name, ok=False)
            try:
                text = await asyncio.wait_for(f.api_artifact(client, budget, OUT, name, body), 900)
                response = json.loads((OUT / f"{name}.response.json").read_text())
                served = response.get("model", "")
                if response.get("service_tier") != "flex" or not (
                    served == settings["model"] or served.startswith(settings["model"] + "-")):
                    raise ValueError("Unexpected model/tier; no fallback authorized")
                result.update(protocol.validate(f.quality, json.loads(text), item))
                result["ok"] = True
            except Exception as exc:
                result["error"] = f"{type(exc).__name__}: {exc}"
            response_path = OUT / f"{name}.response.json"
            if response_path.exists():
                response = json.loads(response_path.read_text())
                result["response"] = {k: response.get(k) for k in ("id", "model", "status", "service_tier", "usage")}
            f.save(result_path, result)
            results.append(result)
            print(name, "complete" if result["ok"] else result["error"], flush=True)
    f.save(OUT / "summary.json", f.quality.summarize(results))
    (OUT / "REPORT.md").write_text(f.quality.render_report(results) + "\n\n"
        "Each pool contains all eight boolean configurations at five seeds, in config-major order. "
        "Ten positions selected uniformly with seed 777; duplicate texts retained. "
        "Only prose and standard calibration were sent. No source, traces, QA, or manual reviews "
        "were sent to the judge. No generator edits, automatic paid retries, or cross-campaign budget changes. "
        "This evaluates the current repaired authors; it is not a fresh-author or revised-prompt trial. "
        "Cost uses the historical repository rate table, not invoice reconciliation.\n")
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
