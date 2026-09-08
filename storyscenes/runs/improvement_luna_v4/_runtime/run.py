#!/usr/bin/env python3
"""Sample a Storyscenes world locally; no OpenAI dependency or runtime API calls."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import worker


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("world", type=Path, help="world directory containing generator.py")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--prose-seed", type=int)
    p.add_argument("-n", "--count", type=int, default=1)
    p.add_argument("--json", action="store_true", help="JSONL including state, evidence and QA")
    args = p.parse_args()
    if args.count < 1:
        p.error("count must be positive")
    frozen = args.world.resolve().parent / "_runtime" / "run.py"
    if frozen.exists() and frozen.resolve() != Path(__file__).resolve():
        raise SystemExit(subprocess.call([sys.executable, str(frozen), *sys.argv[1:]]))
    for row in worker.sample(args.world, range(args.seed, args.seed + args.count), prose=True, prose_seed=args.prose_seed):
        if args.json:
            print(json.dumps(row, ensure_ascii=False))
        else:
            print(f"{row['title']} (seed {row['seed']})\n\n{row['story']}\n")


if __name__ == "__main__":
    main()
