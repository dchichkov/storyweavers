#!/usr/bin/env python3
"""Merge completed world artifacts, run the copied judge, and report the trial."""
import argparse
import asyncio
import json
import lzma
from pathlib import Path
import shutil
import statistics
import factory as f


def report(root):
    worlds = json.loads((root / "summary.json").read_text())
    quality_path = root / "quality" / "quality.jsonl"
    judges = [json.loads(x) for x in quality_path.read_text().splitlines()] if quality_path.exists() else []
    judge = {r["script"]: r for r in judges if r["ok"]}
    verification = json.loads((root / "verification.json").read_text()) if (root / "verification.json").exists() else []
    raw = [{"response": json.loads(p.read_text())} for p in root.glob("*/*.response.json")]
    costs = f.trial_cost.summarize(raw + judges)
    ledger_total = sum(json.loads(p.read_text())["committed_upper_usd"] for p in root.glob("*budget.json"))
    f.save(root / "total_cost.json", costs)
    summary = f.quality.summarize(judges) if judges else {}
    lines = ["# Storyscenes initial prototype", "",
        f"The staged pipeline produced {len(worlds)} standalone world generators over one shared constraint engine. "
        "Luna authored theater plans and attempted initial mechanics. Terra completed or repaired the executable simulations; "
        "Luna authored the final prose. Saved generators make no API calls.", "",
        f"Completed worlds: **{sum(r['ok'] for r in worlds)}/{len(worlds)}**. "
        f"Sample pool: **{sum(r.get('samples', 0) for r in worlds)} stories**. "
        f"Judged: **{sum(r.get('judged_stories', 0) for r in judges if r['ok'])} stories**.", "",
        "| World | Quality /9 | Diversity /9 | Plot groups in 10 | Ordered paths /100 | Words | Samples |",
        "|---|---:|---:|---:|---:|---:|---|"]
    compression = []
    for row in worlds:
        j = judge.get(row["world"], {})
        q = f"{j['rating']['overall']:.2f}" if j else "—"
        d = str(j["diversity"]["overall"]) if j else "—"
        groups = str(len(j["plot_groups"])) if j else "—"
        words = "–".join(map(str, row.get("word_range", [])))
        lines.append(f"| {row['world']} | {q} | {d} | {groups} | {row.get('distinct_scene_paths', '—')} | {words} | [read]({row['world']}/samples.md) |")
        if row["ok"]:
            pool = [json.loads(x) for x in (root / row["world"] / "samples.jsonl").read_text().splitlines()]
            data = "\n\n".join(r["story"] for r in pool).encode()
            compression.append(dict(world=row["world"], stories=len(pool), distinct_texts=len({r["story"] for r in pool}),
                                    utf8_bytes=len(data), lzma_bytes=len(lzma.compress(data, preset=6))))
    if judge:
        lines += ["", f"Mean overall quality: **{statistics.mean(j['rating']['overall'] for j in judge.values()):.2f}/9**. "
                       f"Mean within-world diversity: **{statistics.mean(j['diversity']['overall'] for j in judge.values()):.2f}/9**."]
    lines += ["", "Quality uses the unchanged, TinyStories-calibrated StoryWorld set rubric, with Terra judging ten "
        "uniformly sampled positions per 100-story pool (selection seed 777), without deduplication. "
        "The judge sees the stories, not the simulation trace. Ordered-path counts include permutations "
        "and optional scenes; they are not a count of meaningfully different plots.", "",
        f"Offline verification: **{sum(r['ok'] for r in verification)}/{len(verification)} worlds**, "
        f"**{sum(r.get('fresh_samples', 0) for r in verification if r['ok'])} fresh samples**, "
        f"**{sum(r.get('pinned_replays', 0) for r in verification if r['ok'])} pinned replays**. "
        "Direct and final-generator traces agree, every scene is legal under its authored rules, "
        "and trace-linked paragraphs cover the selected events.", "",
        "The common engine is the reusable part: guards, atomic effects, invariants, bounded search, "
        "knowledge/ownership kernels, causal dependencies, and frozen realization. Literary scene "
        "implementations remain world-specific. This tests an initial composition interface; it does "
        "not establish a universal narrative-kernel library or superiority over one-stage generation.", "",
        f"Returned-usage cost estimate: **${costs['usd_low']:.3f}–${costs['usd_high']:.3f}**, "
        f"for {costs['priced_requests']} priced responses. Blocked-network and interrupted calls have no returned "
        f"usage; their conservative reservations remain in the ledger. **${ledger_total:.3f}** is accounted "
        "for including those reservations, below the $10 ceiling. Estimates are not invoice reconciliation.", "",
        "Artifacts: [quality evidence](quality/report.md), [verification](verification.json), "
        "[costs](total_cost.json), [original budget ledger](budget.json), "
        "[recovery ledger](recovery_budget.json), [compression diagnostics](compression.json).", "",
        "Compression is an auxiliary lexical-repetition diagnostic (UTF-8 story text, two-newline separator, "
        "LZMA preset 6). It is not the canonical 1,000-sample compression experiment and cannot measure "
        "semantic diversity. See the judge's plot groups instead.", ""]
    manual = root / "manual_review.md"
    if manual.exists():
        lines += [manual.read_text()]
    f.save(root / "compression.json", compression)
    (root / "REPORT.md").write_text("\n".join(lines))
    f.save(root / "quality_summary.json", summary)
    return costs


async def main(args):
    root = args.run.resolve()
    expected = json.loads((root / "settings.json").read_text())["count"]
    summaries = [json.loads(p.read_text()) for p in sorted(root.glob("*/summary.json"))
                 if (p.parent / "simulation.py").exists() and (p.parent / "generator.py").exists()]
    if len(summaries) != expected or any(not s.get("ok") for s in summaries):
        raise ValueError(f"Need {expected} completed worlds; found {len(summaries)}")
    # Preserve the first authoring outcome, including failed worlds later repaired.
    original = root / "initial_authoring_summary.json"
    if not original.exists() and (root / "summary.json").exists():
        shutil.copyfile(root / "summary.json", original)
    f.save(root / "summary.json", summaries)
    for name in ("runtime.py", "worker.py", "factory.py", "recover.py"):
        shutil.copyfile(f.ROOT / name, root / ("snapshot_" + name))
    f.save(root / "runtime_provenance.json", {name: f.digest(f.ROOT / name) for name in ("runtime.py", "worker.py", "factory.py", "recover.py")})
    if args.evaluate:
        f.load_key(args.api_key_file)
        # Both authoring processes must be finished before finalization.
        spent = sum(json.loads((root / name).read_text())["committed_upper_usd"]
                    for name in ("budget.json", "recovery_budget.json") if (root / name).exists())
        budget = f.Budget(root / "judge_budget.json", max(0, 10.0 - spent))
        await f.evaluate(root, budget, args.concurrency)
    costs = report(root)
    print(f"Report: {root / 'REPORT.md'}; returned usage ${costs['usd_low']:.3f}–${costs['usd_high']:.3f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--evaluate", action="store_true")
    p.add_argument("--api-key-file", type=Path)
    p.add_argument("--concurrency", type=int, default=3)
    asyncio.run(main(p.parse_args()))
