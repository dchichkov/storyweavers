#!/usr/bin/env python3
"""Offline matched prose review. Preserve old traces, then test new story plans."""
import argparse
import json
from pathlib import Path
import shutil
import statistics

import capability_trial as trial
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import fingerprint, plain, replay
from storyscenes.capabilities.realize import render, render_story
from storyscenes.capabilities.reading import Reader


def check_document(document):
    questions = Reader(document).questions()
    if len({q.question for q in questions}) != len(questions):
        raise ValueError("Duplicate visible question anchors")
    for statement, span in zip(document.statements, document.spans()):
        if document.story[span["start"]:span["end"]] != statement.text:
            raise ValueError("Invalid reading span")


def review(baseline, out, *, fresh_count=0, fresh_seed=44000):
    if fresh_count < 0:
        raise ValueError("Fresh count cannot be negative")
    if out.exists():
        raise ValueError("Review output already exists; keep each comparison batch")
    selection = json.loads((baseline / "judge_samples.json").read_text())
    old_files = [p for p in baseline.rglob("*") if p.is_file()]
    old_hashes = {str(p): trial.f.digest(p) for p in old_files}
    specs = {name: loads(trial.registry(), (baseline / "worlds" / f"{name}.json").read_text())
             for name in {r["world"] for r in selection}}
    sources = dict(trial.sources(), **{"storyscenes/review_capability_prose.py": Path(__file__)})
    hashes = {name: trial.f.digest(path) for name, path in sources.items()}
    out.mkdir(parents=True)
    for name, path in sources.items():
        target = out / "_source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    trial.f.save(out / "source_hashes.json", hashes)
    trial.f.save(out / "settings.json", dict(baseline=str(baseline.resolve()),
        selection_sha256=trial.f.digest(baseline / "judge_samples.json"), selected=len(selection),
        mode="same old paths, matched seeds, optional independent seeds", paid_calls=0,
        independent_seeds_per_world=fresh_count, independent_seed_start=fresh_seed))
    (out / "worlds").mkdir()
    for world in sorted(specs):
        (out / "worlds" / f"{world}.json").write_text(dumps(trial.BUILDERS[world]().spec))
    matched, fresh, independent = [], [], []
    with (out / "same_paths.jsonl").open("x") as comparisons, (out / "fresh_seeds.jsonl").open("x") as sampled:
        for old in selection:
            spec = specs[old["world"]]
            state = replay(trial.registry(), spec, old["path"])
            if fingerprint(state) != old["trace_sha256"] or render(spec, state).story != old["story"]:
                raise ValueError(f"Baseline replay/text changed: {old['sample_id']}")
            doc = render_story(spec, state)
            check_document(doc)
            row = dict(sample_id=old["sample_id"], world=old["world"], seed=old["seed"],
                old_story=old["story"], story=doc.story, path=old["path"], trace_sha256=fingerprint(state),
                old_words=len(old["story"].split()), words=len(doc.story.split()),
                old_paragraphs=len(old["story"].split("\n\n")), paragraphs=len(doc.story.split("\n\n")),
                old_questions=len(old["qa"]), qa=plain(Reader(doc).questions()),
                statements=plain(doc.statements), spans=doc.spans())
            trial.append(comparisons, row)
            matched.append(row)
            new, trace = trial.supervise((old["world"], old["seed"], 6000, 2.0), 6.0)
            trial.append(sampled, dict(new, evidence=trace))
            fresh.append(new)
            print(f"{old['sample_id']}: same-path {row['old_words']} -> {row['words']} words; fresh={new['ok']}", flush=True)
    with (out / "independent_seeds.jsonl").open("x") as sampled:
        for world in sorted(specs):
            for seed in range(fresh_seed, fresh_seed + fresh_count):
                row, trace = trial.supervise((world, seed, 6000, 2.0), 6.0)
                trial.append(sampled, dict(row, evidence=trace))
                independent.append(row)
            selected = [r for r in independent if r["world"] == world]
            print(f"Independent {world}: {sum(r['ok'] for r in selected)}/{len(selected)}", flush=True)
    for row in fresh + independent:
        if row["ok"] and len({a["question"] for a in row["qa"]}) != len(row["qa"]):
            raise ValueError(f"Duplicate visible question anchors: {row['sample_id']}")
    if {name: trial.f.digest(path) for name, path in sources.items()} != hashes:
        raise ValueError("Sources changed during review")
    if {str(p): trial.f.digest(p) for p in old_files} != old_hashes:
        raise ValueError("Historical corpus changed during review")
    totals = dict(selected=len(matched), unchanged_traces=len(matched), baseline_files_unchanged=True,
                  fresh_returned=sum(r["ok"] for r in fresh), fresh_attempted=len(fresh), paid_calls=0,
                  independent_returned=sum(r["ok"] for r in independent), independent_attempted=len(independent))
    trial.f.save(out / "summary.json", totals)
    lines = ["# Capability prose: local matched review", "",
             "No new judge scores. No API calls. Historical scores apply only to historical texts.", "",
             "Same-path comparisons keep the exact original simulation; fresh runs use the same selected seeds with narrative prerequisites.",
             "These are 30 previously successful, judge-selected positions, not an unbiased yield benchmark.", "",
             "| World | Old words | New words | Old paragraphs | New paragraphs | Fresh returns |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for world in sorted(specs):
        rows = [r for r in matched if r["world"] == world]
        counts = [statistics.mean(r[k] for r in rows) for k in ("old_words", "words", "old_paragraphs", "paragraphs")]
        good = sum(r["ok"] for r in fresh if r["world"] == world)
        lines.append(f"| {world} | " + " | ".join(f"{v:.1f}" for v in counts) + f" | {good}/{len(rows)} |")
    lines += ["", f"All {len(matched)} old trace hashes and diagnostic texts reproduced exactly; historical files were not changed.",
              "", "QA is regenerated from visible retained statements, so omission reduces question coverage as well as prose.",
              "Compaction is not evidence of better diversity, motivation or literary quality."]
    if independent:
        lines += ["", "## Independent seed smoke", "",
                  f"Seeds {fresh_seed} through {fresh_seed + fresh_count - 1}; 2 CPU seconds, 6 wall seconds, 6,000 nodes per position.",
                  "These are three fixed profiles, not a representative world population or a diversity benchmark."]
        for world in sorted(specs):
            selected = [r for r in independent if r["world"] == world]
            lines.append(f"- {world}: {sum(r['ok'] for r in selected)}/{len(selected)} returned and replayed.")
    for world in sorted(specs):
        row = next(r for r in matched if r["world"] == world)
        new = next(r for r in fresh if r["sample_id"] == row["sample_id"])
        lines += ["", f"## {row['sample_id']}: new rendering, original path", "", row["story"],
                  "", "### Fresh constrained path", "", new.get("story", new.get("error", "Failed"))]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n")
    return totals


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--fresh-count", type=int, default=0)
    parser.add_argument("--fresh-seed", type=int, default=44000)
    args = parser.parse_args()
    print(json.dumps(review(args.baseline, args.out, fresh_count=args.fresh_count, fresh_seed=args.fresh_seed), indent=2))
