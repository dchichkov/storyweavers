#!/usr/bin/env python3
"""Preserve 10/30/100-story replication iterations under one shared judging cap."""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from copy import deepcopy
import gzip
import importlib
import json
import lzma
from pathlib import Path
import random
import shutil
import statistics

import compare_capability_judges as comparison
from storyscenes import harbor_judge_protocol
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import plain, replay

trial, f = comparison.trial, comparison.f
ROOT = Path(__file__).resolve().parent
PRIOR = tuple(ROOT / "runs" / name for name in ("capability_judge_comparison_v1", "capability_judge_comparison_v2"))


def campaign(path):
    """Retain even explicit rejected reservations from earlier scoring."""
    target = path / "settings.json"
    prior_paths = (tuple(Path(p) for p in json.loads(target.read_text())["previous_budget_sha256"])
                   if target.exists() else PRIOR)
    prior = {str(p.resolve()): f.digest(p / "budget.json") for p in prior_paths}
    committed = sum(sum(e["reserved_usd"] for e in json.loads((p / "budget.json").read_text())["entries"]) for p in prior_paths)
    settings = dict(authorized_usd=5, previous_committed_usd=committed, remaining_cap_usd=5 - committed,
                    previous_budget_sha256=prior)
    if settings["remaining_cap_usd"] <= 0:
        raise ValueError("No remaining authorized scoring budget")
    if target.exists():
        if json.loads(target.read_text()) != settings:
            raise ValueError("Previous spending or campaign authorization changed")
    else:
        path.mkdir(parents=True, exist_ok=True)
        f.save(target, settings)
    amendment = path / "authorization_increase.json"
    if amendment.exists():
        change = json.loads(amendment.read_text())
        if (change.get("previous_authorized_usd") != 5 or change.get("authorized_usd") != 10
                or change.get("previous_settings_sha256") != f.digest(target)):
            raise ValueError("Unrecognized campaign authorization amendment")
        return dict(settings, authorized_usd=10, remaining_cap_usd=10 - committed,
                    authorization_sha256=f.digest(amendment))
    return settings


def generator(world):
    if world not in {"harbor", "greenhouse", "theater", "harbor_composition", "harbor_tradeoffs", "harbor_questions", "harbor_favors"}:
        raise ValueError("Unknown replication script")
    return importlib.import_module(f"storyscenes.{world}_story")


def sources(world="harbor"):
    module = generator(world)
    prose = importlib.import_module(f"storyscenes.{world}_prose")
    extra = (ROOT / "harbor_interactions.py", ROOT / "harbor_interaction_prose.py") if world == "harbor" else ()
    if world == "harbor_composition":
        extra = (ROOT / "goal_planning.py",)
    elif world == "harbor_tradeoffs":
        extra = (ROOT / "goal_planning.py", ROOT / "harbor_composition_story.py", ROOT / "harbor_composition_prose.py")
    elif world == "harbor_questions":
        extra = (ROOT / "harbor_attempts.py", ROOT / "harbor_attempts_prose.py", ROOT / "harbor_recovery.py")
    return dict(trial.sources(), **{str(p.relative_to(ROOT.parent)): p for p in (
        Path(__file__), Path(module.__file__), Path(prose.__file__),
        Path(harbor_judge_protocol.__file__), Path(comparison.__file__), *extra)})


def paired_jobs(rows, *, story_only=False):
    """Judge EVERY position together for diversity; retain exact duplicates."""
    if not rows or not all(r["ok"] for r in rows):
        raise ValueError("Complete valid local corpus required")
    worlds = {r["world"] for r in rows}
    if len(worlds) != 1:
        raise ValueError("Within-script evaluation requires exactly one script")
    world = worlds.pop()
    item = f.quality.select_set(world, rows, 777, count=len(rows))
    selected = [rows[s["source_index"]] for s in item["stories"]]
    for story, row in zip(item["stories"], selected):
        story["sample_id"] = row["sample_id"]
    body = harbor_judge_protocol.request_body(f.quality, item)
    originals = [dict(phase="story_quality", stage=world, input=item, body=body)]
    for offset in (() if story_only else range(0, len(selected), 5)):
        batch = selected[offset:offset + 5]
        originals.append(dict(phase="qa_quality", stage=f"{world}_{offset // 5:02d}", input=batch,
                              body=comparison.cq.request_body(batch)))
    jobs = []
    for original in originals:
        for model in comparison.MODELS:
            job = deepcopy(original)
            job["model"] = model
            job["body"].update(model=model, store=False)
            jobs.append(job)
    return jobs, selected


def prepare(out, campaign_path, seed=0, count=10, *, story_only=False, world="harbor"):
    if count not in (10, 30, 100):
        raise ValueError("Use the predeclared 10, 30, 100 sample ladder")
    if out.exists():
        raise ValueError("Keep iterations: choose a new output directory")
    money = campaign(campaign_path)
    module = generator(world)
    source_files = sources(world)
    hashes = {name: f.digest(path) for name, path in source_files.items()}
    out.mkdir(parents=True)
    for name, path in source_files.items():
        dest = out / "_source" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    f.save(out / "source_hashes.json", hashes)
    (out / "worlds").mkdir()
    rows = []
    with (out / "attempts.jsonl").open("x") as samples, gzip.open(out / "traces.jsonl.gz", "wt") as traces:
        for index in range(seed, seed + count):
            try:
                row, spec, state, doc = module.generate(index)
                if row["world"] != world or row["sample_id"] != f"{world}:{index}" or row["seed"] != index:
                    raise ValueError("Generator returned a different sample identity")
                serialized = dumps(spec)
                if replay(module.registry(), loads(module.registry(), serialized), row["path"]) != state:
                    raise ValueError("Serialized world failed exact replay")
                chosen = random.Random(index).sample(row["qa"], min(6, len(row["qa"])))
                row["conversations"] = [dict(id=f"c{i:03d}", turns=[q]) for i, q in enumerate(chosen)]
                (out / "worlds" / f"{index}.json").write_text(serialized)
                traces.write(json.dumps(dict(sample_id=row["sample_id"], trace=plain(state),
                    statements=plain(doc.statements), spans=doc.spans())) + "\n")
            except Exception as exc:
                row = dict(sample_id=f"{world}:{index}", world=world, seed=index, ok=False, error=str(exc))
            rows.append(row)
            trial.append(samples, row)
    if {name: f.digest(path) for name, path in source_files.items()} != hashes:
        raise ValueError("Sources changed during sampling")
    good = [r for r in rows if r["ok"]]
    shuffled = random.Random(777).sample(good, len(good))
    corpus = "\n".join(json.dumps(r["story"], ensure_ascii=False) for r in shuffled).encode()
    compressed = lzma.compress(corpus, preset=9)
    (out / "stories.jsonl.xz").write_bytes(compressed)
    stats = dict(planned=count, returned=len(good), exact_unique=len({r["story"] for r in good}),
        plot_signatures=len({trial.fingerprint(r["plot"]) for r in good}),
        outcomes=dict(Counter(r["plot"]["outcome"] for r in good)),
        lzma=dict(raw_bytes=len(corpus), compressed_bytes=len(compressed),
                  ratio=len(compressed) / len(corpus) if corpus else None,
                  bytes_per_story=len(compressed) / len(good) if good else None,
                  format="UTF-8 JSON strings, one per line; shuffled seed 777; XZ preset 9"),
        mean_words=statistics.mean(r["words"] for r in good) if good else None)
    f.save(out / "local_summary.json", stats)
    lines = [f"# {world.title()} iteration: {count} predeclared samples", "",
             "No score-based selection or replacement. Plot signatures are mechanical descriptors, not a semantic diversity score.",
             "Each sample has up to six uniform single-turn QA conversations; no automatic Why follow-ups.", ""]
    for row in rows:
        lines += [f"## {row['sample_id']}", "", json.dumps(row.get("plot", {}), sort_keys=True), "",
                  row.get("story", row.get("error", "failed")), ""]
        for qa in row.get("qa", []):
            lines += [f"Q: {qa['question']}", f"A: {qa['answer']}", ""]
    (out / "SAMPLES.md").write_text("\n".join(lines))
    if len(good) != count:
        raise ValueError("Local failures preserved; fix in a new iteration before paying judges")
    jobs, selected = paired_jobs(rows, story_only=story_only)
    settings = dict(protocol="story_replication_iteration_v1", world=world, story_only=story_only, campaign=str(campaign_path.resolve()),
        campaign_settings_sha256=f.digest(campaign_path / "settings.json"), seed_start=seed, count=count,
        models=list(comparison.MODELS), budget_usd=money["remaining_cap_usd"],
        previous_committed_usd=money["previous_committed_usd"], combined_authorized_usd=money["authorized_usd"],
        campaign_authorization_sha256=money.get("authorization_sha256"),
        requests=len(jobs), conversations=sum(len(r["conversations"]) for r in rows),
        attempts_sha256=f.digest(out / "attempts.jsonl"), source_hashes_sha256=f.digest(out / "source_hashes.json"),
        manifest=[dict(model=j["model"], phase=j["phase"], stage=j["stage"],
                       request_sha256=trial.fingerprint(j["body"])) for j in jobs],
        scope_notes=[f"One {world} generator, {count} predeclared seed positions, no literary filtering.",
            f"Local outputs: {stats['exact_unique']} exact unique; {stats['plot_signatures']} mechanical signatures; outcomes {stats['outcomes']}.",
            "Up to six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.",
            "Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.",
            "Same literary rubric and rating dimensions, with output budget scaled to the required ratings.",
            "Output format v2 attaches plot-group membership to each mandatory story rating; literary rubric unchanged.",
            "Story-only assessment; no new QA requests." if story_only else "Story and QA assessment.",
            "Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.",
            "The budget below is shared across all replication iterations, not a fresh allowance for every version."])
    f.save(out / "settings.json", settings)
    f.save(out / "judge_samples.json", selected)
    for job in jobs:
        directory = out / job["model"] / job["phase"]
        directory.mkdir(parents=True, exist_ok=True)
        f.save(directory / f"{job['stage']}.planned.json", job["body"])
    print(json.dumps(stats, indent=2))


def load(out):
    settings = json.loads((out / "settings.json").read_text())
    if f.digest(out / "source_hashes.json") != settings["source_hashes_sha256"]:
        raise ValueError("Frozen source manifest changed")
    hashes = json.loads((out / "source_hashes.json").read_text())
    if {name: f.digest(path) for name, path in sources(settings["world"]).items()} != hashes:
        raise ValueError("Working sources changed; use the preserved runtime or a new iteration")
    for name, digest in hashes.items():
        if f.digest(out / "_source" / name) != digest:
            raise ValueError("Frozen source copy changed")
    if f.digest(out / "attempts.jsonl") != settings["attempts_sha256"]:
        raise ValueError("Saved samples changed")
    campaign_path = Path(settings["campaign"])
    money = campaign(campaign_path)
    if f.digest(campaign_path / "settings.json") != settings["campaign_settings_sha256"]:
        raise ValueError("Campaign cap changed")
    if (settings.get("campaign_authorization_sha256") != money.get("authorization_sha256")
            or settings["budget_usd"] != money["remaining_cap_usd"]
            or settings["combined_authorized_usd"] != money["authorized_usd"]):
        raise ValueError("Campaign authorization changed; prepare a new iteration")
    jobs, selected = paired_jobs(trial.read_rows(out / "attempts.jsonl"), story_only=settings["story_only"])
    if selected != json.loads((out / "judge_samples.json").read_text()):
        raise ValueError("Selection changed")
    manifest = [dict(model=j["model"], phase=j["phase"], stage=j["stage"],
                     request_sha256=trial.fingerprint(j["body"])) for j in jobs]
    if manifest != settings["manifest"]:
        raise ValueError("Judge requests changed")
    return settings, jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "judge"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--campaign", type=Path, default=ROOT / "runs/harbor_iteration_campaign")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--count", type=int, choices=(10, 30, 100), default=10)
    parser.add_argument("--world", choices=("harbor", "greenhouse", "theater", "harbor_composition", "harbor_tradeoffs", "harbor_questions", "harbor_favors"), default="harbor")
    parser.add_argument("--story-only", action="store_true", help="For explicit story regrading; omit paid QA calls")
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--concurrency", type=int, default=2)
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare(args.out, args.campaign, args.seed, args.count, story_only=args.story_only, world=args.world)
    else:
        settings, jobs = load(args.out)
        budget = comparison.Budget(Path(settings["campaign"]) / "budget.json", settings["budget_usd"])
        result = asyncio.run(comparison.evaluate(jobs, args.out, settings["budget_usd"], args.api_key_file,
                                                args.concurrency, budget=budget,
                                                story_validator=lambda value, item: harbor_judge_protocol.validate(f.quality, value, item)))
        print(json.dumps(dict(cost=result["cost"], committed=result["committed_upper_usd"]), indent=2))


if __name__ == "__main__":
    main()
