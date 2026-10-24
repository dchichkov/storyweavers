#!/usr/bin/env python3
"""Compare three preserved 100-story corpora; judge a predeclared balanced 90.

All 300 positions, including duplicates, enter compression. Only the first 30
positions of each script enter pooled semantic judging; no QA is judged again.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
import lzma
from pathlib import Path
import random
import shutil

import harbor_trial as harness

f, trial, comparison = harness.f, harness.trial, harness.comparison
WORLD_ORDER = ("harbor", "greenhouse", "theater")
SCOPE = ("Evaluate a balanced sample of 90 stories from THREE independent procedural scripts "
         "(30 positions each). Judge diversity of this pooled set, not within one script. "
         "Setting or character changes alone do not earn diversity; compare problem, causal "
         "development and resolution across scripts too. All duplicates are retained.")


def corpus_stats(rows):
    shuffled = random.Random(777).sample(rows, len(rows))
    raw = "\n".join(json.dumps(r["story"], ensure_ascii=False) for r in shuffled).encode()
    packed = lzma.compress(raw, preset=9)
    return dict(positions=len(rows), exact_unique=len({r["story"] for r in rows}), raw_bytes=len(raw),
                compressed_bytes=len(packed), ratio=len(packed) / len(raw),
                bytes_per_story=len(packed) / len(rows)), packed


def pooled_jobs(rows):
    if len(rows) != 90 or any(sum(r["world"] == w for r in rows) != 30 for w in WORLD_ORDER):
        raise ValueError("Require thirty unfiltered positions from each script")
    item = f.quality.select_set("pooled_three_scripts", rows, 777, count=90)
    for s in item["stories"]:
        s["sample_id"] = rows[s["source_index"]]["sample_id"]
    body = harness.harbor_judge_protocol.request_body(f.quality, item)
    original = "Evaluate a random sample of stories from ONE procedural StoryWorld."
    if not body["input"][0]["content"].startswith(original):
        raise ValueError("Story rubric changed; review pooled scope explicitly")
    body["input"][0]["content"] = body["input"][0]["content"].replace(original, SCOPE, 1)
    body["input"][0]["content"] = body["input"][0]["content"].replace(
        "within this shared domain.", "across this pooled set.").replace(
        "Shared setting is expected;", "Shared or different settings alone are not diversity;")
    jobs = []
    for model in comparison.MODELS:
        request = deepcopy(body)
        request.update(model=model, store=False)
        jobs.append(dict(model=model, phase="story_quality", stage="pooled_90", input=item, body=request))
    return jobs


def source_files():
    files = harness.sources()
    files["storyscenes/replication_comparison.py"] = Path(__file__)
    return files


def prepare(out, batches, campaign_path):
    if out.exists():
        raise ValueError("Preserve previous comparisons; choose a new directory")
    money = harness.campaign(campaign_path)
    all_rows, selected, input_hashes, per_world = [], [], {}, {}
    for world, batch in zip(WORLD_ORDER, batches):
        settings = json.loads((batch / "settings.json").read_text())
        if settings["world"] != world or settings["count"] != 100 or settings["seed_start"] != 10000:
            raise ValueError("Expected the predeclared seed-10000 replication corpus")
        report = json.loads((batch / "comparison.json").read_text())
        if any(report["arms"][m]["story"]["rated_stories"] != 100 for m in comparison.MODELS):
            raise ValueError("Complete within-script story judging first")
        if f.digest(batch / "attempts.jsonl") != settings["attempts_sha256"]:
            raise ValueError("Source corpus changed")
        rows = trial.read_rows(batch / "attempts.jsonl")
        if len(rows) != 100 or any(not r["ok"] or r["world"] != world or r["seed"] != 10000 + i for i, r in enumerate(rows)):
            raise ValueError("Do not remove or replace failed or duplicate positions")
        for name in ("settings.json", "comparison.json", "attempts.jsonl"):
            input_hashes[str((batch / name).resolve())] = f.digest(batch / name)
        all_rows.extend(rows)
        selected.extend(rows[:30])
        per_world[world] = {str(n): corpus_stats(rows[:n])[0] for n in (10, 30, 100)}
    stats, packed = corpus_stats(all_rows)
    separate = sum(v["100"]["compressed_bytes"] for v in per_world.values())
    stats.update(per_world_prefixes=per_world, separate_compressed_bytes=separate,
                 pooled_saving_fraction=1 - stats["compressed_bytes"] / separate,
                 format="UTF-8 JSON strings; shuffled seed 777; XZ preset 9")
    out.mkdir(parents=True)
    f.save(out / "compression.json", stats)
    (out / "all_300_stories.jsonl.xz").write_bytes(packed)
    with (out / "attempts.jsonl").open("x") as stream:
        for row in selected:
            trial.append(stream, row)
    files = source_files()
    for name, path in files.items():
        target = out / "_source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    hashes = {name: f.digest(path) for name, path in files.items()}
    f.save(out / "source_hashes.json", hashes)
    jobs = pooled_jobs(selected)
    settings = dict(protocol="cross_script_replication_v1", campaign=str(campaign_path.resolve()),
        campaign_settings_sha256=f.digest(campaign_path / "settings.json"),
        budget_usd=money["remaining_cap_usd"], previous_committed_usd=money["previous_committed_usd"], combined_authorized_usd=5,
        attempts_sha256=f.digest(out / "attempts.jsonl"), source_hashes_sha256=f.digest(out / "source_hashes.json"),
        input_hashes=input_hashes,
        manifest=[trial.fingerprint(j["body"]) for j in jobs],
        scope_notes=["Cross-script assessment, not directly the same experiment as within-script diversity.",
            "Compression uses all 300 positions. Semantic judging uses seeds 10000-10029 from each script, 90 total.",
            "No score selection or deduplication. No new QA calls. Same story calibration and rating dimensions.",
            "Only the scope sentences change from one shared world to a pooled three-script set.",
            "Uses the existing shared $5 campaign cap. No automatic retries or fallback tiers."])
    f.save(out / "settings.json", settings)
    for job in jobs:
        path = out / job["model"] / job["phase"]
        path.mkdir(parents=True)
        f.save(path / "pooled_90.planned.json", job["body"])
    print(json.dumps(stats, indent=2))


def load(out):
    settings = json.loads((out / "settings.json").read_text())
    if f.digest(out / "source_hashes.json") != settings["source_hashes_sha256"]:
        raise ValueError("Source manifest changed")
    hashes = json.loads((out / "source_hashes.json").read_text())
    if {n: f.digest(p) for n, p in source_files().items()} != hashes:
        raise ValueError("Working sources changed; use preserved runtime")
    if any(f.digest(out / "_source" / n) != h for n, h in hashes.items()):
        raise ValueError("Frozen source changed")
    if any(f.digest(Path(n)) != h for n, h in settings["input_hashes"].items()):
        raise ValueError("Parent batch changed")
    if f.digest(out / "attempts.jsonl") != settings["attempts_sha256"]:
        raise ValueError("Pooled sample changed")
    campaign_path = Path(settings["campaign"])
    harness.campaign(campaign_path)
    if f.digest(campaign_path / "settings.json") != settings["campaign_settings_sha256"]:
        raise ValueError("Campaign authorization changed")
    jobs = pooled_jobs(trial.read_rows(out / "attempts.jsonl"))
    if [trial.fingerprint(j["body"]) for j in jobs] != settings["manifest"]:
        raise ValueError("Pooled requests changed")
    return settings, jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "judge"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--batches", type=Path, nargs=3, metavar=("HARBOR", "GREENHOUSE", "THEATER"))
    parser.add_argument("--campaign", type=Path, default=harness.ROOT / "runs/harbor_iteration_campaign")
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    if args.phase == "prepare":
        if not args.batches:
            parser.error("prepare requires --batches HARBOR GREENHOUSE THEATER")
        prepare(args.out, args.batches, args.campaign)
    else:
        settings, jobs = load(args.out)
        budget = comparison.Budget(Path(settings["campaign"]) / "budget.json", settings["budget_usd"])
        result = asyncio.run(comparison.evaluate(jobs, args.out, settings["budget_usd"], args.api_key_file, 2, budget=budget,
            story_validator=lambda value, item: harness.harbor_judge_protocol.validate(f.quality, value, item)))
        print(json.dumps(dict(cost=result["cost"], committed=result["committed_upper_usd"]), indent=2))


if __name__ == "__main__":
    main()
