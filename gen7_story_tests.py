#!/usr/bin/env python3
"""Snapshot runner for the gen7 StoryWorld vertical slice."""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import random
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
    "data00:76647",
    "data00:39989",
    "data00:69968",
    "data00:49677",
    "data01:21684",
    "data00:73784",
    "data00:87204",
    "data00:84855",
    "data01:50117",
    "data00:34986",
    "data01:21606",
    "data00:92560",
    "data01:9606",
    "data00:99939",
    "data01:73907",
    "data00:14971",
    "data00:18138",
    "data00:18146",
    "data00:9315",
    "data01:3375",
    "data00:47709",
    "data00:67975",
    "data00:69885",
    "data00:99040",
    "data01:79405",
    "data00:40043",
    "data00:75795",
    "data01:29057",
    "data01:35953",
    "data01:44968",
    "data01:70172",
    "data01:736",
    "data01:81695",
    "data00:14223",
    "data00:22532",
    "data00:29570",
    "data00:49296",
    "data00:49741",
    "data00:6868",
    "data00:70047",
    "data01:45689",
    "data00:14843",
    "data00:29609",
    "data00:87381",
    "data01:49007",
    "data01:50258",
    "data01:61444",
    "data01:80028",
    "data01:86168",
    "data00:31075",
    "data00:32293",
    "data00:52281",
    "data00:70806",
    "data01:10250",
    "data01:74091",
    "data01:77353",
    "data01:92444",
]

SNAPSHOT_DIR = Path(__file__).parent / "gen7_story_tests"
DATA_DIR = Path(__file__).parent / "TinyStories_kernels"
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


def generated_qa(story_id: str, limit: int) -> list[gen7.QA]:
    row = gen7.load_story(story_id)
    return gen7.generate_qa(row.get("kernel", "") or "", limit=limit)


def snapshot_text(story_id: str) -> str:
    return f"STORY_ID: {story_id}\n\n{generated_text(story_id)}\n"


def dataset_path(dataset: str) -> Path:
    return DATA_DIR / f"{dataset}.kernels.jsonl"


def iter_story_rows(datasets: list[str], scan: int):
    for dataset in datasets:
        path = dataset_path(dataset)
        with path.open() as f:
            for i, raw in enumerate(f):
                if i >= scan:
                    break
                try:
                    row = json.loads(raw)
                except Exception:
                    continue
                yield f"{dataset}:{i}", row


def sample_story_ids(count: int, seed: int, datasets: list[str], scan: int) -> list[str]:
    pinned = set(STORY_IDS)
    candidates: list[str] = []
    for story_id, row in iter_story_rows(datasets, scan):
        if story_id in pinned:
            continue
        kernel = row.get("kernel", "") or ""
        if not kernel.strip():
            continue
        try:
            ast.parse(kernel)
            if gen7.generate(kernel).strip():
                candidates.append(story_id)
        except Exception:
            continue
    rng = random.Random(seed)
    if len(candidates) > count:
        candidates = rng.sample(candidates, count)
    return sorted(candidates)


def print_sample(story_ids: list[str], show_kernel: bool, show_qa: bool, qa_limit: int) -> None:
    for story_id in story_ids:
        row = gen7.load_story(story_id)
        print(f"=== {story_id} ===")
        summary = (row.get("summary") or "").strip()
        if summary:
            print(f"SUMMARY: {summary}")
        print()
        print("GENERATED:")
        print(generated_text(story_id))
        if show_qa:
            print()
            print("QA:")
            for qa in generated_qa(story_id, qa_limit):
                print(f"Q: {qa.question}")
                print(f"A: {qa.answer}")
        if show_kernel:
            print()
            print("KERNEL:")
            print((row.get("kernel") or "").strip())
        original = (row.get("story") or "").strip()
        if original:
            print()
            print("ORIGINAL:")
            print(original)
        print()


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


def run_qa(story_ids: list[str], qa_limit: int) -> int:
    failures = 0
    total_pairs = 0
    full_responses = 0
    multi_sentence_responses = 0
    duplicate_questions = 0
    kind_counts: dict[str, int] = {}
    for story_id in story_ids:
        pairs = generated_qa(story_id, qa_limit)
        if not pairs:
            failures += 1
            print(f"{story_id}: no QA generated")
            continue
        questions_seen: set[str] = set()
        for qa in pairs:
            total_pairs += 1
            kind_counts[qa.kind] = kind_counts.get(qa.kind, 0) + 1
            if not qa.question.endswith("?"):
                failures += 1
                print(f"{story_id}: malformed question {qa.question!r}")
            if not qa.answer.strip():
                failures += 1
                print(f"{story_id}: blank answer for {qa.question!r}")
            if qa.question.lower() in questions_seen:
                duplicate_questions += 1
            questions_seen.add(qa.question.lower())
            sentence_marks = re.findall(r"[.!?]", qa.answer.strip())
            if re.match(r"^[A-Z0-9].*[.!?]$", qa.answer.strip()) and " " in qa.answer.strip():
                full_responses += 1
            else:
                failures += 1
                print(f"{story_id}: bare/incomplete answer {qa.answer!r} for {qa.question!r}")
            if len(sentence_marks) >= 2:
                multi_sentence_responses += 1
            else:
                failures += 1
                print(f"{story_id}: answer is not multi-sentence {qa.answer!r} for {qa.question!r}")
    kind_total = len(kind_counts)
    if kind_total < 4:
        failures += 1
        print(f"QA kind diversity too low: {kind_total} kinds")
    duplicate_rate = (duplicate_questions / total_pairs * 100.0) if total_pairs else 0.0
    if duplicate_rate > 10.0:
        failures += 1
        print(f"QA duplicate question rate too high: {duplicate_rate:.1f}%")
    if failures:
        print(f"{failures} gen7 QA check(s) failed")
        return 1
    full_rate = (full_responses / total_pairs * 100.0) if total_pairs else 0.0
    multi_rate = (multi_sentence_responses / total_pairs * 100.0) if total_pairs else 0.0
    top_kinds = ", ".join(f"{kind}:{count}" for kind, count in sorted(kind_counts.items())[:8])
    print(
        f"ok - generated QA for {len(story_ids)} gen7 stories; "
        f"pairs={total_pairs}; full_response_rate={full_rate:.1f}%; "
        f"multi_sentence_rate={multi_rate:.1f}%; "
        f"kinds={kind_total}; duplicate_questions={duplicate_questions} ({duplicate_rate:.1f}%); "
        f"top_kinds={top_kinds}"
    )
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
    ap.add_argument("--run-qa", action="store_true", help="Smoke-test generated QA")
    ap.add_argument("--sample", type=int, metavar="N", help="Print N unpinned gen7 sample candidates")
    ap.add_argument("--seed", type=int, default=42, help="Seed for --sample")
    ap.add_argument("--scan", type=int, default=100000, help="Rows per dataset to scan for --sample")
    ap.add_argument("--data", nargs="+", default=["data00", "data01"], help="Datasets for --sample, e.g. data00 data01")
    ap.add_argument("--show-kernel", action="store_true", help="Include kernel source in --sample output")
    ap.add_argument("--show-qa", action="store_true", help="Include generated QA in --sample output")
    ap.add_argument("--qa-limit", type=int, default=6, help="Maximum QA pairs to show per sampled story")
    ap.add_argument("story_id", nargs="*", help="Optional story ids; defaults to the pinned gen7 suite")
    args = ap.parse_args()

    if args.sample is not None:
        story_ids = sample_story_ids(args.sample, args.seed, args.data, args.scan)
        print_sample(story_ids, args.show_kernel, args.show_qa, args.qa_limit)
        return 0

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
    if args.run_qa:
        return run_qa(story_ids, args.qa_limit)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
