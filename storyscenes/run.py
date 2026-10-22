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
    p.add_argument("--qa", action="store_true", help="Add offline conversational QA using the current QA library")
    p.add_argument("--qa-seed", type=int, default=777)
    p.add_argument("--qa-limit", type=int, default=6)
    args = p.parse_args()
    if args.count < 1:
        p.error("count must be positive")
    if args.qa:
        command = [sys.executable, str(Path(__file__).with_name('qa.py')), str(args.world),
                   '--seed', str(args.seed), '-n', str(args.count), '--qa-seed', str(args.qa_seed),
                   '--limit', str(args.qa_limit)]
        if args.prose_seed is not None: command += ['--prose-seed', str(args.prose_seed)]
        if args.json: command.append('--json')
        raise SystemExit(subprocess.call(command))
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
