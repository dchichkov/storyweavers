#!/usr/bin/env python3
"""Snapshot runner for the gen7 StoryWorld vertical slice."""

from __future__ import annotations

import argparse
import difflib
import re
from pathlib import Path

import gen7


STORY_IDS = [
    "data00:18697",
    "data00:29975",
    "data00:36222",
    "data00:36242",
    "data00:46773",
    "data00:26355",
    "data00:17954",
    "data00:46279",
    "data00:18065",
    "data00:18528",
    "data00:4480",
    "data00:61486",
    "data00:64208",
    "data00:6508",
    "data00:72721",
    "data01:77357",
    "data01:8592",
    "data01:2444",
    "data01:496",
    "data01:15691",
    "data01:66431",
    "data00:38678",
    "data00:63564",
    "data01:18980",
    "data00:46547",
    "data00:19246",
    "data00:13982",
    "data01:25809",
    "data01:6339",
    "data00:39499",
    "data01:56039",
    "data00:18590",
    "data00:83183",
    "data01:35822",
    "data00:75721",
    "data00:46547",
    "data00:76647",
    "data00:39989",
]

SNAPSHOT_DIR = Path(__file__).parent / "gen7_story_tests"
SELF_EVENT = re.compile(r"\b([A-Z][A-Za-z]+)\b came across \1\b")
FORBIDDEN = (
    "Something happened",
    "something happened",
    "Something was",
    "There was Fear",
    "There was Joy",
    "There was Love",
)


def snapshot_path(story_id: str) -> Path:
    return SNAPSHOT_DIR / f"{story_id.replace(':', '_')}.txt"


def generated_text(story_id: str) -> str:
    row = gen7.load_story(story_id)
    return gen7.generate(row.get("kernel", "") or "").strip()


def snapshot_text(story_id: str) -> str:
    return f"STORY_ID: {story_id}\n\n{generated_text(story_id)}\n"


def validate(story_id: str, text: str) -> list[str]:
    problems: list[str] = []
    for bad in FORBIDDEN:
        if bad in text:
            problems.append(f"{story_id}: forbidden phrase {bad!r}")
    if SELF_EVENT.search(text):
        problems.append(f"{story_id}: self-event pattern found")
    return problems


def pin(story_ids: list[str]) -> None:
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    for story_id in story_ids:
        path = snapshot_path(story_id)
        text = snapshot_text(story_id)
        path.write_text(text)
        print(f"pinned {story_id} -> {path.relative_to(Path.cwd())}")


def run(story_ids: list[str]) -> int:
    failures = 0
    for story_id in story_ids:
        path = snapshot_path(story_id)
        actual = snapshot_text(story_id)
        problems = validate(story_id, actual)
        if problems:
            failures += 1
            for problem in problems:
                print(problem)
        if not path.exists():
            failures += 1
            print(f"{story_id}: missing snapshot {path}")
            continue
        expected = path.read_text()
        if actual != expected:
            failures += 1
            print(f"--- {story_id} changed ---")
            print("".join(difflib.unified_diff(
                expected.splitlines(keepends=True),
                actual.splitlines(keepends=True),
                fromfile=str(path),
                tofile=f"current:{story_id}",
            )))
    if failures:
        print(f"{failures} gen7 snapshot check(s) failed")
        return 1
    print(f"ok - {len(story_ids)} gen7 snapshots matched")
    return 0


def select_ids(args: argparse.Namespace) -> list[str]:
    if args.story_id:
        return args.story_id
    return STORY_IDS


def main() -> int:
    ap = argparse.ArgumentParser(description="Pin or run gen7 story snapshots")
    ap.add_argument("--list", action="store_true", help="List pinned story ids")
    ap.add_argument("--pin", action="store_true", help="Write snapshots")
    ap.add_argument("--run", action="store_true", help="Compare snapshots")
    ap.add_argument("story_id", nargs="*", help="Optional story ids; defaults to the 20-story slice")
    args = ap.parse_args()

    story_ids = select_ids(args)
    if args.list:
        for story_id in story_ids:
            print(story_id)
        return 0
    if args.pin:
        pin(story_ids)
        return 0
    if args.run:
        return run(story_ids)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
