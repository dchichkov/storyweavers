#!/usr/bin/env python3
"""Evaluate archived training stories with the unchanged StoryWorld set judge."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import hashlib
import gzip
import json
from pathlib import Path
import random
import shutil
import statistics
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "storyworlds"))
sys.path.insert(0, str(ROOT))
import compression_review
import dataset_score
import openai_world_set_quality as judge
from training.storyworld_chat.analyze_world_contributors import story_skeleton


def story_record(row: dict, line_number: int) -> dict | None:
    metadata = row.get("metadata", {})
    task = metadata.get("task")
    packed = metadata.get("packed_tasks", [])
    if task != "story" and not (task == "multiturn" and packed and packed[0] == "story"):
        return None
    world = metadata.get("world")
    if not isinstance(world, str) or not world:
        raise ValueError(f"missing world at line {line_number}")
    messages = row.get("messages", [])
    story = next((m.get("content") for m in messages if m.get("role") == "assistant"), None)
    if not isinstance(story, str) or not story.strip():
        raise ValueError(f"missing story at line {line_number}")
    return dict(world=world, story=story, params=metadata.get("params", {}),
                source_line=line_number, metadata=metadata, messages=messages)


def collect(handle, count: int, seed: int) -> tuple[dict, dict]:
    """Keep the lowest seeded world hashes, independent of row order or row counts."""
    if count < 1:
        raise ValueError("world count must be positive")
    digest = hashlib.sha256()
    ranks, pools, counts, unique = {}, {}, Counter(), {}
    tasks = Counter()
    lines = 0
    for lines, line in enumerate(handle, 1):
        digest.update(line)
        if not line.strip():
            continue
        row = json.loads(line)
        tasks[row.get("metadata", {}).get("task", "missing")] += 1
        record = story_record(row, lines)
        if record is None:
            continue
        world, story = record["world"], record["story"]
        counts[world] += 1
        story_hash = hashlib.sha256(story.encode("utf-8")).hexdigest()
        unique.setdefault(world, set()).add(story_hash)
        if counts[world] == 1:
            rank = (hashlib.sha256(f"{seed}\n{world}".encode()).hexdigest(), world)
            if len(ranks) < count or rank < max(ranks.values()):
                if len(ranks) == count:
                    evicted = max(ranks, key=ranks.get)
                    del ranks[evicted], pools[evicted]
                ranks[world], pools[world] = rank, {}
        if world in pools:
            pools[world].setdefault(story_hash, record)
        if lines % 100000 == 0:
            print(f"Scanned {lines:,} rows; {len(counts):,} worlds", flush=True)
    ordered = {world: list(pools[world].values()) for world in sorted(pools, key=ranks.get)}
    summary = dict(source_sha256=digest.hexdigest(), lines=lines, tasks=dict(tasks),
                   story_rows=sum(counts.values()), worlds=len(counts),
                   unique_story_world_pairs=sum(map(len, unique.values())),
                   requested_worlds=count, selected_worlds=len(ordered), seed=seed,
                   selection="lowest seeded SHA256 world hashes; uniform worlds, not packed rows",
                   world_counts={world: dict(rows=counts[world], unique_stories=len(unique[world]))
                                 for world in sorted(counts)})
    return ordered, summary


def compression(groups: dict[str, list[dict]], out: Path) -> dict:
    out.mkdir(exist_ok=False)
    per_world = []
    for index, (world, rows) in enumerate(groups.items()):
        stories = [row["story"] for row in rows]
        _, sizes = compression_review.pack(stories, shuffle=True)
        per_world.append(dict(world=world, stories=len(stories),
            skeletons=len({story_skeleton(row["story"], row.get("params", {})) for row in rows}),
            mean_words=statistics.mean(len(text.split()) for text in stories),
            xz=sizes, compression=dataset_score.compression_retention(stories)))
        if (index + 1) % 10 == 0:
            print(f"Compressed {index + 1}/{len(groups)} worlds", flush=True)
    growth = []
    shuffled = []
    for world, rows in groups.items():
        rows = list(rows)
        random.Random(world).shuffle(rows)
        shuffled.append(rows)
    for cap in (10, 50, 100):
        texts = [row["story"] for rows in shuffled for row in rows[:cap]]
        packed, metrics = compression_review.pack(texts, shuffle=True)
        (out / f"up_to_{cap}.stories.jsonl.xz").write_bytes(packed)
        growth.append(dict(cap=cap, **metrics))
    texts = [row["story"] for rows in groups.values() for row in rows]
    packed, metrics = compression_review.pack(texts, shuffle=True)
    (out / "all_retained.stories.jsonl.xz").write_bytes(packed)
    result = dict(protocol="archived_retained_story_compression_v1", worlds=per_world,
                  pooled=dict(**metrics, exact_unique=len(set(texts)),
                              compression=dataset_score.compression_retention(texts)),
                  growth=growth, dictionary_bytes=dataset_score.DICTIONARY_BYTES,
                  warning="Already deduplicated retained stories, not 1000 fresh draws. "
                          "Skeleton counts are not plot counts. Higher retention means less cross-story reuse.")
    judge.save(out / "summary.json", result)
    return result


def prepare(archive: Path, member: str, out: Path, *, count: int, seed: int,
            expected_sha256: str | None = None) -> None:
    out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, "r:gz") as bundle:
        handle = bundle.extractfile(member)
        if handle is None:
            raise ValueError("archive member is not a regular file")
        with handle:
            groups, source = collect(handle, count, seed)
    if expected_sha256 and source["source_sha256"] != expected_sha256:
        raise ValueError("source JSONL checksum mismatch; no judging allowed")
    source.update(archive=str(archive.resolve()), member=member,
                  expected_sha256=expected_sha256,
                  checksum_verified=bool(expected_sha256),
                  deduplication="Exact base-story strings once per world; packed QA repetitions removed.",
                  full_pipeline_score=None,
                  full_pipeline_score_reason="Static training text cannot establish runtime, verify, replay, "
                                             "or 1000-draw yield gates. QA is not graded by this story-only judge.")
    judge.save(out / "source.json", source)
    (out / "pools").mkdir()
    inputs, catalog = [], []
    for index, (world, rows) in enumerate(groups.items()):
        pool = out / "pools" / f"{index:03d}.jsonl"
        with pool.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        world_seed = int(hashlib.sha256(f"{seed}\njudge\n{world}".encode()).hexdigest()[:16], 16)
        item = None
        if len(rows) >= 2:
            item = judge.select_set(world, rows, world_seed)
            item.update(sample_file=str(pool.resolve()), source_jsonl_sha256=source["source_sha256"],
                        pool_origin="as-trained, exact base-story strings once per world")
            inputs.append(item)
        catalog.append(dict(world=world, pool=str(pool.relative_to(out)), stories=len(rows),
                            judge_eligible=item is not None,
                            judge_stories=len(item["stories"]) if item else 0))
    judge.save(out / "catalog.json", catalog)
    judge.save(out / "judge_inputs.json", inputs)
    for file in (Path(__file__), Path(compression_review.__file__), Path(dataset_score.__file__)):
        shutil.copyfile(file, out / file.name)
    compression(groups, out / "compression")
    print(f"Prepared {len(groups)} worlds, {sum(len(x) for x in groups.values())} retained stories; "
          f"{len(inputs)} judge-eligible worlds", flush=True)


def report(out: Path) -> dict:
    rows = [json.loads(line) for line in (out / "judge" / "quality.jsonl").read_text().splitlines()]
    good = [row for row in rows if row.get("ok")]
    summary = judge.summarize(rows)
    source = json.loads((out / "source.json").read_text())
    summary.update(selected_worlds=source["selected_worlds"],
        mean_world_quality=statistics.mean(row["rating"]["overall"] for row in good) if good else None,
        worlds_quality_at_least_six=sum(row["rating"]["overall"] >= 6 for row in good),
        worlds_quality_six_diversity_three=sum(row["rating"]["overall"] >= 6 and
                                              row["diversity"]["overall"] >= 3 for row in good),
        worlds_quality_six_diversity_four=sum(row["rating"]["overall"] >= 6 and
                                             row["diversity"]["overall"] >= 4 for row in good),
        plot_groups=Counter(str(len(row["plot_groups"])) for row in good),
        full_pipeline_score=None, full_pipeline_score_reason=source["full_pipeline_score_reason"])
    judge.save(out / "summary.json", summary)
    return summary


def compare_retained(out: Path, trials: list[Path], *, count: int = 50,
                     samples: int = 100, seed: int = 20260908) -> dict:
    """Equal-size compression panels, never selected using quality ratings."""
    if count < 1 or samples < 1:
        raise ValueError("positive comparison sizes required")
    panels = {}
    catalog = json.loads((out / "catalog.json").read_text())
    panels["production_train"] = [dict(world=r["world"], path=out / r["pool"])
                                   for r in catalog if r["stories"] >= samples]
    for trial in trials:
        if trial.name in panels:
            raise ValueError("duplicate comparison label")
        rows = [json.loads(line) for line in (trial / "qc" / "worlds.jsonl").read_text().splitlines()]
        panels[trial.name] = [dict(world=r["script"], path=ROOT / r["samples_file"])
                             for r in rows if r["runtime_ok"] and r["verify_ok"]
                             and r["exact_unique"] >= samples]
    if any(len(rows) < count for rows in panels.values()):
        raise ValueError(f"not enough eligible worlds: {[(k, len(v)) for k, v in panels.items()]}")
    target = out / "retained_comparison"
    target.mkdir(exist_ok=False)
    result = dict(worlds_per_panel=count, unique_stories_per_world=samples, seed=seed,
                  selection="uniform seeded world hashes among eligible worlds; "
                            "uniform exact-unique stories within world; no score-based selection",
                  caveats="Old worlds are from the as-trained sample; new worlds must pass sample+verify. "
                          "Both require at least the requested number of exact-unique retained stories. "
                          "This conditions on variation capacity, excludes small pools, and is not a yield score. "
                          "Different task distributions remain a confound.", panels={})
    for label, candidates in panels.items():
        selected = sorted(candidates, key=lambda r: hashlib.sha256(
            f"{seed}\ncomparison\n{r['world']}".encode()).hexdigest())[:count]
        groups, provenance = {}, []
        for candidate in selected:
            path = candidate["path"]
            opener = gzip.open if path.suffix == ".gz" else open
            with opener(path, "rt", encoding="utf-8") as handle:
                unique = {}
                for line in handle:
                    row = json.loads(line)
                    unique.setdefault(row["story"], row)
            rows = random.Random(f"{seed}\n{candidate['world']}").sample(
                sorted(unique.values(), key=lambda r: r["story"]), samples)
            groups[candidate["world"]] = rows
            provenance.append(dict(world=candidate["world"], file=str(path),
                available_unique=len(unique),
                selected_story_sha256=[hashlib.sha256(r["story"].encode()).hexdigest() for r in rows]))
        metrics = compression(groups, target / label)
        judge.save(target / label / "selection.json", provenance)
        result["panels"][label] = dict(eligible_worlds=len(candidates), pooled=metrics["pooled"],
            growth=metrics["growth"],
            mean_world_retention=statistics.mean(r["compression"]["retention"] for r in metrics["worlds"]),
            median_world_retention=statistics.median(r["compression"]["retention"] for r in metrics["worlds"]),
            mean_story_words=statistics.mean(r["mean_words"] for r in metrics["worlds"]))
    judge.save(target / "summary.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Omit to judge/report an already prepared directory")
    parser.add_argument("--member", default="training/storyworld_chat/data/production_20260904/train.jsonl")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--worlds", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--judge", action="store_true", help="Paid Terra/Flex judge; no retry or fallback")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--compare-trial", type=Path, action="append", default=[])
    parser.add_argument("--comparison-worlds", type=int, default=50)
    parser.add_argument("--comparison-stories", type=int, default=100)
    args = parser.parse_args()
    if args.archive:
        prepare(args.archive, args.member, args.out, count=args.worlds, seed=args.seed,
                expected_sha256=args.expected_sha256)
    if args.judge:
        inputs = json.loads((args.out / "judge_inputs.json").read_text())
        asyncio.run(judge.run_sets(inputs, args.out / "judge", concurrency=args.concurrency))
    if args.compare_trial:
        compare_retained(args.out, args.compare_trial, count=args.comparison_worlds,
                         samples=args.comparison_stories, seed=args.seed)
    if (args.out / "judge" / "summary.json").exists():
        print(json.dumps(report(args.out), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
