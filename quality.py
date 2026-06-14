#!/usr/bin/env python3
"""
quality.py - Story-quality evaluation harness for the gen6 engine.

This is the machine half of an **agent-as-judge** evaluation (see QUALITY.md for
the rubric and procedure). It does NOT score anything itself — scoring is done by
a coding agent reading QUALITY.md. `quality.py` only:

  1. `--sample`  deterministically samples N stories into a gradeable JSONL
     worksheet (each record carries the kernel, the *original* TinyStories text,
     the gen6-*generated* text, the per-story kernel-coverage ratio, and an empty
     `scores` block the agent fills in).
  2. `--report`  reads a graded worksheet back and aggregates the scores
     (per-dimension means, overall, usable-rate, and defect-tag frequencies),
     broken down by coverage tier.

Because story IDs are stable and generation is deterministic, the same
`--seed` always selects the same stories, so runs are comparable over time.

Usage:
    # 1. Produce a 100-story worksheet (mix of coverage levels = honest system eval)
    python quality.py --sample -n 100 --seed 42 --out quality_runs/run.jsonl

    # 2. (agent grades each record per QUALITY.md, writing the `scores` block)

    # 3. Aggregate
    python quality.py --report quality_runs/run.jsonl
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import random
import sys
from collections import Counter, defaultdict
from statistics import mean

from coverage import extract_character_names, count_coverage
from gen6registry import REGISTRY, generate_story

# Scoring dimensions (1-5). Keep in sync with QUALITY.md.
DIMENSIONS = ["grammar", "coherence", "fidelity", "completeness", "naturalness", "overall"]

# Controlled defect vocabulary (keep in sync with QUALITY.md).
DEFECT_TAGS = [
    "verbed_noun", "missing_kernel_fallback", "literal_concept", "pronoun_error",
    "double_subject", "clause_in_noun_slot", "repetition", "article_error",
    "dropped_content", "incoherent_transition", "wrong_subject", "other",
]

EMPTY_SCORES = {d: None for d in DIMENSIONS}


def _data_tag(path: str) -> str:
    base = os.path.basename(path)
    return base.split(".", 1)[0] if "." in base else base


def sample(data_path: str, n: int, seed: int, scan: int, tier: str):
    """Collect eligible (id, record, cov, tot) and deterministically pick n."""
    tag = _data_tag(data_path)
    eligible = []
    with open(data_path) as f:
        for i, line in enumerate(f):
            if i >= scan:
                break
            try:
                rec = json.loads(line)
            except Exception:
                continue
            kernel = rec.get("kernel", "") or ""
            if not kernel.strip():
                continue
            try:
                ast.parse(kernel)
            except Exception:
                continue  # only parseable stories are gradeable
            ch = extract_character_names(kernel)
            cov, tot = count_coverage(kernel, set(REGISTRY.kernels), ch)
            if tot <= 0:
                continue
            ratio = cov / tot
            if tier == "covered" and cov != tot:
                continue
            if tier == "partial" and cov == tot:
                continue
            eligible.append((f"{tag}:{i}", rec, cov, tot))
    rng = random.Random(seed)
    if len(eligible) > n:
        eligible = rng.sample(eligible, n)
    eligible.sort(key=lambda e: e[0])
    out = []
    for sid, rec, cov, tot in eligible:
        kernel = rec.get("kernel", "") or ""
        try:
            generated = generate_story(kernel)
        except Exception as e:
            generated = f"[GENERATION ERROR: {e}]"
        out.append({
            "id": sid,
            "coverage": {"covered": cov, "total": tot, "ratio": round(cov / tot, 3)},
            "kernel": kernel,
            "original": rec.get("story", "") or "",
            "summary": rec.get("summary", "") or "",
            "generated": generated,
            "scores": dict(EMPTY_SCORES),
            "usable": None,          # bool: acceptable for a training dataset?
            "defects": [],           # subset of DEFECT_TAGS
            "notes": "",
        })
    return out


def cmd_sample(args):
    records = sample(args.data, args.num, args.seed, args.scan, args.tier)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} gradeable records to {args.out}")
    print(f"  data={args.data} seed={args.seed} tier={args.tier}")
    print("Next: grade each record's `scores`/`usable`/`defects` per QUALITY.md, "
          "then run:")
    print(f"  python quality.py --report {args.out}")


def _bar(value, width=20):
    filled = int(round((value - 1) / 4 * width)) if value is not None else 0
    return "#" * filled + "-" * (width - filled)


def cmd_report(args):
    graded, ungraded = [], 0
    with open(args.report) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            scs = r.get("scores") or {}
            if any(scs.get(d) is not None for d in DIMENSIONS):
                graded.append(r)
            else:
                ungraded += 1

    if not graded:
        print(f"No graded records in {args.report} (graded=0, ungraded={ungraded}).")
        print("Fill in the `scores` blocks first (see QUALITY.md).")
        return

    print("=" * 64)
    print(f"QUALITY REPORT  ({args.report})")
    print("=" * 64)
    print(f"graded: {len(graded)}   ungraded: {ungraded}")
    print()

    print("Mean scores (1-5):")
    for d in DIMENSIONS:
        vals = [r["scores"][d] for r in graded if r["scores"].get(d) is not None]
        if vals:
            m = mean(vals)
            print(f"  {d:13s} {m:.2f}  [{_bar(m)}]  (n={len(vals)})")

    usable = [r.get("usable") for r in graded if isinstance(r.get("usable"), bool)]
    if usable:
        print(f"\nusable rate: {sum(usable)}/{len(usable)} = {sum(usable)/len(usable):.0%}")

    # Quality broken down by coverage tier.
    print("\nOverall by coverage tier:")
    buckets = defaultdict(list)
    for r in graded:
        ratio = (r.get("coverage") or {}).get("ratio", 0)
        key = "full (100%)" if ratio >= 0.999 else ("high (>=80%)" if ratio >= 0.8 else "partial (<80%)")
        if r["scores"].get("overall") is not None:
            buckets[key].append(r["scores"]["overall"])
    for key in ("full (100%)", "high (>=80%)", "partial (<80%)"):
        if buckets[key]:
            print(f"  {key:16s} overall {mean(buckets[key]):.2f}  (n={len(buckets[key])})")

    # Defect frequency.
    defects = Counter()
    for r in graded:
        for d in (r.get("defects") or []):
            defects[d] += 1
    if defects:
        print("\nDefect frequency (per graded story):")
        for tag, c in defects.most_common():
            print(f"  {c:4d}  {tag}")

    # Worst stories for quick triage.
    rated = [r for r in graded if r["scores"].get("overall") is not None]
    rated.sort(key=lambda r: r["scores"]["overall"])
    print("\nLowest-rated (triage these):")
    for r in rated[:args.worst]:
        print(f"  {r['scores']['overall']}  {r['id']}  defects={','.join(r.get('defects') or []) or '-'}")
        if r.get("notes"):
            print(f"       note: {r['notes']}")


def main():
    p = argparse.ArgumentParser(description="gen6 story-quality eval harness (see QUALITY.md)")
    sub = p.add_subparsers(dest="cmd")

    ps = sub.add_parser("sample", help="(default) write a gradeable worksheet")
    ps.set_defaults(func=cmd_sample)

    # Allow flag-style too: `quality.py --sample ...` / `--report ...`.
    p.add_argument("--sample", dest="do_sample", action="store_true", help="write a gradeable worksheet")
    p.add_argument("--report", dest="report", metavar="FILE", help="aggregate a graded worksheet")
    p.add_argument("-n", "--num", type=int, default=100, help="stories to sample (default 100)")
    p.add_argument("--seed", type=int, default=42, help="random seed (default 42)")
    p.add_argument("--data", default="TinyStories_kernels/data00.kernels.jsonl", help="dataset jsonl")
    p.add_argument("--scan", type=int, default=40000, help="max lines to scan for eligibility")
    p.add_argument("--tier", choices=["all", "covered", "partial"], default="all",
                   help="all=every parseable story; covered=fully-implemented; partial=has a missing kernel")
    p.add_argument("--out", default="quality_runs/run.jsonl", help="worksheet output path")
    p.add_argument("--worst", type=int, default=10, help="how many lowest-rated to list in the report")

    args = p.parse_args()
    if args.report:
        cmd_report(args)
    elif args.do_sample or args.cmd == "sample":
        cmd_sample(args)
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
