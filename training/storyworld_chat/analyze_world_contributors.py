#!/usr/bin/env python3
"""Rank low-quality and low-diversity StoryWorld training contributors."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", action="append", type=Path, default=[])
    parser.add_argument("--manifest", action="append", type=Path, default=[])
    parser.add_argument("--quality-dir", type=Path)
    parser.add_argument("--target-count", type=int, default=120)
    parser.add_argument("--min-template-stories", type=int, default=50)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    return parser


def scalar_values(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for item in value.values():
            yield from scalar_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from scalar_values(item)
    elif isinstance(value, (str, int, float)) and not isinstance(value, bool):
        yield str(value)


def normalized(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", text).strip()


def story_skeleton(story: str, params: dict[str, Any]) -> str:
    result = normalized(story)
    values = {
        normalized(value)
        for value in scalar_values(params)
        if len(normalized(value)) >= 2
    }
    for value in sorted(values, key=len, reverse=True):
        result = re.sub(
            rf"(?<!\w){re.escape(value)}(?!\w)", "<slot>", result
        )
    return re.sub(r"\b\d+\b", "<num>", result)


def short_hash(text: str) -> bytes:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=12).digest()


def load_manifest_runs(paths: list[Path]) -> dict[str, dict[str, Any]]:
    worlds: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        split = "dev" if path.name.startswith("dev") else "train"
        for run in data.get("runs", []):
            world = run.get("world")
            if not run.get("ok") or not isinstance(world, str):
                continue
            raw = int(run.get("raw_samples", 0))
            duplicates = int(run.get("duplicate_samples_removed", 0))
            worlds[world] = {
                "world": world,
                "split": split,
                "manifest": str(path),
                "requested_samples": int(data.get("args", {}).get("samples_per_world", 0)),
                "raw_samples": raw,
                "exact_unique_samples": int(run.get("samples", 0)),
                "exact_duplicates_removed": duplicates,
                "exact_duplicate_rate": duplicates / raw if raw else 0.0,
            }
    return worlds


def load_quality(quality_dir: Path | None) -> dict[str, list[float]]:
    ratings: dict[str, list[float]] = defaultdict(list)
    if quality_dir is None:
        return ratings
    for path in quality_dir.glob("*quality*.jsonl"):
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rating = row.get("rating")
                overall = rating.get("overall") if isinstance(rating, dict) else None
                if row.get("ok") and isinstance(row.get("script"), str) and isinstance(
                    overall, (int, float)
                ):
                    ratings[row["script"]].append(float(overall))
    return ratings


def scan_jsonl(paths: list[Path]) -> dict[str, dict[str, int]]:
    samples_seen: set[tuple[str, Any, bytes]] = set()
    stories: dict[str, set[bytes]] = defaultdict(set)
    skeletons: dict[str, set[bytes]] = defaultdict(set)
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                metadata = row.get("metadata", {})
                world = metadata.get("world")
                params = metadata.get("params", {})
                if not isinstance(world, str) or not isinstance(params, dict):
                    continue
                story = next(
                    (
                        message.get("content", "")
                        for message in row.get("messages", [])
                        if message.get("role") == "assistant"
                    ),
                    "",
                )
                story_digest = short_hash(story)
                key = (world, params.get("seed"), story_digest)
                if key in samples_seen:
                    continue
                samples_seen.add(key)
                stories[world].add(story_digest)
                skeletons[world].add(short_hash(story_skeleton(story, params)))
    return {
        world: {
            "exported_unique_stories": len(values),
            "slot_normalized_skeletons": len(skeletons[world]),
        }
        for world, values in stories.items()
    }


def select_targets(
    rows: list[dict[str, Any]], count: int, min_template_stories: int
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(candidates: Iterable[dict[str, Any]], tier: str) -> None:
        for row in candidates:
            if len(selected) >= count:
                return
            if row["world"] in seen:
                continue
            seen.add(row["world"])
            selected.append({**row, "selection_tier": tier})

    low_quality_duplicates = sorted(
        (
            row
            for row in rows
            if row.get("quality_overall") is not None
            and row["quality_overall"] <= 5
            and row["exact_duplicates_removed"] > 0
        ),
        key=lambda row: (row["quality_overall"], -row["exact_duplicate_rate"]),
    )
    add(low_quality_duplicates, "low_quality_and_exact_duplicates")

    template_collapsed = sorted(
        (
            row
            for row in rows
            if row.get("exported_unique_stories", 0) >= min_template_stories
        ),
        key=lambda row: (
            row.get("skeleton_ratio", 1.0),
            -row.get("exported_unique_stories", 0),
            row["world"],
        ),
    )
    add(template_collapsed, "slot_normalized_template_collapse")

    exact_duplicates = sorted(
        rows,
        key=lambda row: (-row["exact_duplicate_rate"], row["world"]),
    )
    add(exact_duplicates, "exact_duplicate_rate")

    low_quality = sorted(
        (row for row in rows if row.get("quality_overall") is not None),
        key=lambda row: (row["quality_overall"], -row.get("exported_unique_stories", 0)),
    )
    add(low_quality, "low_quality")
    return selected


def markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# StoryWorld Contributor Ranking",
        "",
        "This report joins production export manifests, slot-normalized stories ",
        "from the final chat JSONL, and successful historical quality ratings.",
        "",
        f"- Production worlds: {summary['worlds']:,}",
        f"- Worlds with quality evidence: {summary['quality_worlds']:,}",
        f"- Selected repair targets: {len(summary['targets']):,}",
        "",
        "| Rank | Tier | Quality | Exact duplicates | Skeletons | Stories | Script |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for index, row in enumerate(summary["targets"], 1):
        quality = "" if row.get("quality_overall") is None else f"{row['quality_overall']:.2f}"
        lines.append(
            "| {rank} | {tier} | {quality} | {duplicates:.1%} | {skeletons} | "
            "{stories} | `{script}` |".format(
                rank=index,
                tier=row["selection_tier"],
                quality=quality,
                duplicates=row["exact_duplicate_rate"],
                skeletons=row.get("slot_normalized_skeletons", ""),
                stories=row.get("exported_unique_stories", ""),
                script=row["world"],
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = build_parser().parse_args()
    if args.target_count < 1:
        raise SystemExit("--target-count must be positive")
    worlds = load_manifest_runs(args.manifest)
    quality = load_quality(args.quality_dir)
    corpus = scan_jsonl(args.jsonl)
    rows = []
    for world, run in worlds.items():
        row = {**run, **corpus.get(world, {})}
        scores = quality.get(world, [])
        row["quality_overall"] = round(statistics.mean(scores), 3) if scores else None
        row["quality_ratings"] = len(scores)
        story_count = row.get("exported_unique_stories", 0)
        row["skeleton_ratio"] = (
            row.get("slot_normalized_skeletons", 0) / story_count
            if story_count
            else None
        )
        rows.append(row)
    targets = select_targets(rows, args.target_count, args.min_template_stories)
    summary = {
        "worlds": len(rows),
        "quality_worlds": sum(row["quality_overall"] is not None for row in rows),
        "targets": targets,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(markdown_report(summary), encoding="utf-8")
    print(f"wrote {args.out_json} and {args.out_md}: {len(targets)} targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
