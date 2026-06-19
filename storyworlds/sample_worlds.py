#!/usr/bin/env python3
"""Sample random stories across storyworld scripts.

Examples:
    ./.venv/bin/python storyworlds/sample_worlds.py
    ./.venv/bin/python storyworlds/sample_worlds.py -n 10 --seed 42
    ./.venv/bin/python storyworlds/sample_worlds.py -n 5 --no-qa
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORLDS_DIR = Path(__file__).resolve().parent / "worlds"


def discover_worlds(worlds_dir: Path) -> list[Path]:
    return sorted(
        path for path in worlds_dir.glob("*.py")
        if not path.name.startswith("_")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a random sample of storyworld scripts."
    )
    parser.add_argument(
        "-n", "--count", type=int, default=10,
        help="number of world scripts to sample; default: 10",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="seed for reproducible world selection and per-world seeds",
    )
    parser.add_argument(
        "--worlds-dir", type=Path, default=DEFAULT_WORLDS_DIR,
        help="directory containing storyworld scripts",
    )
    parser.add_argument(
        "--allow-repeat", action="store_true",
        help="allow sampling the same world more than once",
    )
    parser.add_argument(
        "--qa", dest="qa", action="store_true", default=True,
        help="include each world's QA output; default",
    )
    parser.add_argument(
        "--no-qa", dest="qa", action="store_false",
        help="show stories only",
    )
    parser.add_argument(
        "--trace", action="store_true",
        help="include each world's trace output",
    )
    parser.add_argument(
        "--python", default=sys.executable,
        help="Python executable used to run each world; default: current Python",
    )
    return parser


def select_worlds(worlds: list[Path], count: int, rng: random.Random,
                  allow_repeat: bool) -> list[Path]:
    if count < 1:
        raise SystemExit("count must be at least 1")
    if not worlds:
        raise SystemExit("no storyworld scripts found")
    if allow_repeat:
        return [rng.choice(worlds) for _ in range(count)]
    if count > len(worlds):
        raise SystemExit(
            f"count={count} exceeds available worlds={len(worlds)}; "
            "use --allow-repeat to sample with replacement"
        )
    return rng.sample(worlds, count)


def run_world(python: str, world: Path, seed: int, qa: bool,
              trace: bool) -> subprocess.CompletedProcess[str]:
    cmd = [python, str(world), "-n", "1", "--seed", str(seed)]
    if qa:
        cmd.append("--qa")
    if trace:
        cmd.append("--trace")
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )


def main() -> int:
    args = build_parser().parse_args()
    rng = random.Random(args.seed)
    worlds_dir = args.worlds_dir.resolve()
    worlds = discover_worlds(worlds_dir)
    chosen = select_worlds(worlds, args.count, rng, args.allow_repeat)

    failures: list[tuple[Path, int, str]] = []
    for index, world in enumerate(chosen, 1):
        story_seed = rng.randrange(2 ** 31)
        rel = world.relative_to(ROOT) if world.is_relative_to(ROOT) else world
        print(f"===== {index}. {rel} seed={story_seed} =====")
        result = run_world(args.python, world, story_seed, args.qa, args.trace)
        output = result.stdout.rstrip()
        if output:
            print(output)
        if result.returncode:
            error = result.stderr.rstrip()
            if error:
                print(error, file=sys.stderr)
            failures.append((rel, result.returncode, error))
        if index != len(chosen):
            print()

    if failures:
        print("\nFailures:", file=sys.stderr)
        for path, code, error in failures:
            first = error.splitlines()[0] if error else "(no stderr)"
            print(f"- {path}: rc={code}: {first}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
