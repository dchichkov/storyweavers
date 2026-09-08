#!/usr/bin/env python3
"""Offline reference screening from a retained large-run catalog; no API calls."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import statistics

import prompt_trials as trials


def strict(row):
    return (row["runtime_ok"] and row["verify_ok"] and row["standalone_ok"]
            and row["replay_equal"] and row["samples"] == row["requested_samples"])


def eligible(row):
    return row["runtime_ok"] and row["verify_ok"] and row["samples"] >= 2


def wilson(successes, count):
    z = 1.959963984540054
    p = successes / count
    center = (p + z * z / (2 * count)) / (1 + z * z / count)
    radius = z * math.sqrt(p * (1 - p) / count + z * z / (4 * count * count)) / (1 + z * z / count)
    return [max(0.0, center - radius), min(1.0, center + radius)]


def aggregate(reference, worlds, score, *, minimum_rated=5, quality_floor=6, diversity_floor=3):
    if not worlds or len({w["script"] for w in worlds}) != len(worlds):
        raise ValueError("nonempty, unique generated worlds required")
    rated = [w for w in worlds if w["judge_ok"]]
    if any(not eligible(w) for w in rated):
        raise ValueError("rated world did not pass the recorded judge gate")
    missing = [w for w in worlds if eligible(w) and not w["judge_ok"]]
    quality = [w["quality"]["overall"] for w in rated]
    diversity = [w["diversity"]["overall"] for w in rated]
    if any(not math.isfinite(v) or not 0 <= v <= 9 for v in quality + diversity):
        raise ValueError("invalid quality/diversity rating")

    def delivered(q, d):
        return sum(strict(w) and w["quality"]["overall"] >= q and w["diversity"]["overall"] >= d
                   for w in rated)

    wins = delivered(quality_floor, diversity_floor)
    unknown = sum(strict(w) for w in missing)
    quality_only = [w for w in rated if w["quality"]["overall"] >= quality_floor]
    return dict(**reference, attempted=len(worlds), eligible=sum(eligible(w) for w in worlds),
        rated=len(rated), unrated_eligible=len(missing), strict=sum(strict(w) for w in worlds),
        quality_mean=statistics.mean(quality) if quality else None,
        diversity_mean=statistics.mean(diversity) if diversity else None,
        quality_range=[min(quality), max(quality)] if quality else None,
        diversity_range=[min(diversity), max(diversity)] if diversity else None,
        quality_qualified=len(quality_only),
        quality_qualified_within_world_uniques=sum(w["exact_unique"] for w in quality_only),
        strict_joint_successes=wins, strict_joint_unknown=unknown,
        strict_joint_observed_bounds=[wins / len(worlds), (wins + unknown) / len(worlds)],
        strict_joint_wilson95=wilson(wins, len(worlds)) if not missing else None,
        strict_q6_d4=delivered(6, 4), strict_q7_d3=delivered(7, 3),
        general_repairs=sum(w["automatic_repair_accepted"] for w in worlds),
        underfilled=sum(0 < w["samples"] < w["requested_samples"] for w in worlds),
        qualified_compression_retention=score.get("diversity"), dataset_index=score["score"],
        screening_eligible=not missing and len(rated) >= minimum_rated)


def rankings(rows):
    complete = [r for r in rows if r["screening_eligible"]]
    return {
        "strict_joint_delivery": sorted(complete, key=lambda r: (
            -r["strict_joint_wilson95"][0], -r["quality_mean"], -r["diversity_mean"], r["label"])),
        "quality": sorted(complete, key=lambda r: (-r["quality_mean"], -r["diversity_mean"], r["label"])),
        "semantic_diversity": sorted(complete, key=lambda r: (-r["diversity_mean"], -r["quality_mean"], r["label"])),
        "dataset_index": sorted([r for r in complete if r["dataset_index"] is not None],
                                key=lambda r: (-r["dataset_index"], r["label"])),
    }


def table(rows, report):
    def number(value):
        return "-" if value is None else f"{value:.2f}"

    lines = ["| Reference | Rated / tried | Unrated | Strict | Quality /9 | Diversity /9 | Strict Q+D | Index /100 |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in rows:
        link = Path(os.path.relpath(trials.ROOT / r["source"], report.parent)).as_posix()
        name = f"[{r['label']}: {Path(r['source']).stem}]({link})"
        joint = f"{r['strict_joint_successes']}/{r['attempted']}"
        if r["strict_joint_unknown"]:
            joint += f" (+{r['strict_joint_unknown']} unknown)"
        lines.append(f"| {name} | {r['rated']}/{r['attempted']} | {r['unrated_eligible']} | "
                     f"{r['strict']}/{r['attempted']} | {number(r['quality_mean'])} | "
                     f"{number(r['diversity_mean'])} | {joint} | {number(r['dataset_index'])} |")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--out", type=Path, required=True, help="new Markdown report; sibling JSON keeps all metrics")
    parser.add_argument("--shortlist", nargs="+", default=[], help="reference labels for an explicit candidate manifest")
    args = parser.parse_args()
    directory, config = trials.load_trial(args.name)
    out = args.out.resolve()
    json_out = out.with_suffix(".json")
    manifest_out = out.with_suffix(".references.json")
    if any(p.exists() for p in (out, json_out, manifest_out)):
        raise ValueError("choose a new output path; retained analyses are not overwritten")
    reference_path = directory / "inputs/storyworlds/batches" / f"{args.name}.references.json"
    references = trials.read(reference_path)
    catalog_path = directory / "qc/worlds.jsonl"
    score_path = directory / "qc/dataset_scores.json"
    worlds = trials.jsonl(catalog_path)
    if len({w["script"] for w in worlds}) != len(worlds):
        raise ValueError("duplicate generated world in catalog")
    if {w["example"] for w in worlds} != {r["label"] for r in references}:
        raise ValueError("catalog and reference labels differ")
    scores = trials.read(score_path)
    rows = []
    for reference in references:
        snapshot = directory / "inputs" / reference["source"]
        source = trials.ROOT / reference["source"]
        row = aggregate(reference, [w for w in worlds if w["example"] == reference["label"]], scores[reference["label"]])
        row.update(snapshot=trials.relative(snapshot), source_sha256=trials.digest(snapshot),
                   current_source_matches_snapshot=source.exists() and trials.digest(source) == trials.digest(snapshot))
        rows.append(row)
    by_label = {r["label"]: r for r in rows}
    if len(set(args.shortlist)) != len(args.shortlist) or any(label not in by_label for label in args.shortlist):
        raise ValueError("shortlist must contain distinct known labels")
    chosen = [by_label[label] for label in args.shortlist]
    if any(not r["current_source_matches_snapshot"] for r in chosen):
        raise ValueError("shortlisted current source differs from the evaluated reference snapshot")
    ranked = rankings(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    trials.save(json_out, dict(run=args.name, world_unit="one generated script; sibling story ratings averaged first",
        screening=dict(minimum_rated=5, no_missing_judgements=True, quality_floor=6, diversity_floor=3,
                       sort="95% Wilson lower endpoint of strict joint deliveries; quality/diversity break ties",
                       warning="Exploratory, unmatched tasks; no multiple-comparison or winner-selection adjustment"),
        input_hashes={trials.relative(path): trials.digest(path) for path in (reference_path, catalog_path, score_path)},
        analysis_source_sha256=trials.digest(Path(__file__)), references=rows,
        rankings={key: [r["label"] for r in values] for key, values in ranked.items()}, shortlist=args.shortlist))
    if chosen:
        trials.save(manifest_out, [dict(label=r["label"], source=r["source"], sha256=r["source_sha256"]) for r in chosen])
    lines = [f"# Reference Screening: {args.name}", "", "Offline analysis only. No API calls or canonical changes.", "",
        "Quality/diversity are conditional on valid judgements of worlds that passed sampling and verification.",
        "Means weight generated worlds equally, not sibling stories as independent experiments.",
        "Strict means full requested count, standalone CLI, verification, and deterministic replay.",
        "Strict Q+D means strict AND world-average quality >=6 AND semantic diversity >=3.",
        "Diversity 3 is only a modest floor (minor branch variation), not strong narrative diversity.",
        "The JSON also gives Q>=6,D>=4 and Q>=7,D>=3 sensitivity counts.", "",
        "Primary screens require >=5 rated worlds and no missing eligible judgements.",
        "Strict-delivery sorting uses the lower endpoint of a descriptive 95% Wilson interval;",
        "these intervals do not correct for selecting winners from 106 references or unmatched task difficulty.",
        "Missing judge scores are not replaced by zero. Incomplete references appear separately.",
        "The existing quality-gated exact-unique/compression index is unchanged and does NOT include semantic diversity.",
        "Nine or ten tasks/reference give a shortlist to retest, not a demonstrated causal ranking.", ""]
    if chosen:
        lines += ["## Candidate Manifest", "", "Explicit exploratory shortlist, not a canonical replacement.", ""] + table(chosen, out)
    for label, title in (("strict_joint_delivery", "Strict Joint Delivery"), ("quality", "Conditional Quality"),
                         ("semantic_diversity", "Conditional Semantic Diversity"), ("dataset_index", "Existing Dataset Index")):
        lines += ["", f"## {title}", ""] + table(ranked[label][:12], out)
    lines += ["", "## Incomplete Judge Coverage", ""] + table([r for r in rows if r["unrated_eligible"]], out)
    lines += ["", "## All References", "", "Original reference order; incomplete is not synonymous with poor.", ""] + table(rows, out)
    out.write_text("\n".join(lines) + "\n")
    print(out)
    print(json_out)
    if chosen:
        print(manifest_out)


if __name__ == "__main__":
    main()
