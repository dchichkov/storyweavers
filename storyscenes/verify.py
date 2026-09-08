#!/usr/bin/env python3
"""Replay pinned stories and check fresh, previously unjudged world seeds offline."""
import argparse
import asyncio
import json
from pathlib import Path
import factory as f


async def verify(root, count=100, seed=9000):
    results = []
    for world in sorted(p for p in root.iterdir() if (p / "generator.py").exists()):
        row = dict(world=world.name, ok=False)
        try:
            summary = json.loads((world / "summary.json").read_text())
            for name in ("simulation", "generator"):
                if f.digest(world / f"{name}.py") != summary[f"{name}_sha256"]:
                    raise ValueError(f"{name} differs from sampled source")
            pinned = json.loads((world / "samples_with_trace.json").read_text())
            replay = await f.execute(world, [r["seed"] for r in pinned], prose=True)
            if replay != pinned:
                raise ValueError("Pinned prose/trace/QA replay changed")
            alternate = await f.execute(world, [pinned[0]["seed"]], prose=True, prose_seed=8675309)
            if alternate[0]["trace"] != pinned[0]["trace"]:
                raise ValueError("Trace replay changed")
            fresh = await f.execute(world, list(range(seed, seed + count)), prose=True)
            rows = [r["trace"] for r in fresh]
            kernels = {e["kernel"] for r in rows for e in r["events"]}
            edges = sum(bool(e["causes"]) for r in rows for e in r["events"])
            if not kernels.intersection({"Observe", "Tell", "Transfer"}):
                raise ValueError("No shared knowledge/ownership kernel executed")
            if not edges:
                raise ValueError("No causal state dependencies across scenes")
            row.update(ok=True, pinned_replays=len(pinned), fresh_samples=count,
                       alternate_prose_seed=8675309, prose_changed=alternate[0]["story"] != pinned[0]["story"],
                       seeds=[seed, seed + count - 1], kernels=sorted(kernels),
                       events_with_causal_parents=edges,
                       distinct_ordered_paths=len({tuple(e["scene"] for e in r["events"]) for r in rows}),
                       event_count_range=[min(len(r["events"]) for r in rows), max(len(r["events"]) for r in rows)])
        except Exception as exc:
            row["error"] = str(exc)
        results.append(row)
        print(f"{world.name}: {'verified' if row['ok'] else row['error']}", flush=True)
    return results


async def main(args):
    results = await verify(args.run.resolve(), args.count, args.seed)
    f.save(args.run / "verification.json", results)
    return int(not results or any(not r["ok"] for r in results))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--count", type=int, default=100)
    p.add_argument("--seed", type=int, default=9000)
    args = p.parse_args()
    if args.count < 1:
        p.error("count must be positive")
    raise SystemExit(asyncio.run(main(args)))
