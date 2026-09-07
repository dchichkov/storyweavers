#!/usr/bin/env python3
"""Offline, story-only compression review of canonical worlds or saved samples."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import random
import shutil
import sys

import canonical_examples

ROOT = canonical_examples.ROOT
sys.path.insert(0, str(ROOT))
from training.storyworld_chat.analyze_world_contributors import story_skeleton

DICTIONARY_BYTES = 64 * 1024 * 1024


def pack(stories: list[str], *, shuffle: bool, dictionary_bytes=DICTIONARY_BYTES) -> tuple[bytes, dict]:
    stories = list(stories)
    if shuffle:
        stories.sort()
        random.Random(0).shuffle(stories)
    data = "".join(json.dumps(story, ensure_ascii=False) + "\n" for story in stories).encode("utf-8")
    compressed = lzma.compress(data, format=lzma.FORMAT_XZ,
                              filters=[dict(id=lzma.FILTER_LZMA2, preset=6, dict_size=dictionary_bytes)])
    return compressed, dict(stories=len(stories), input_bytes=len(data), xz_bytes=len(compressed),
                            ratio=len(compressed) / len(data) if data else None,
                            bytes_per_story=len(compressed) / len(stories) if stories else None,
                            sha256=hashlib.sha256(compressed).hexdigest())


def pooled_review(samples: list[dict], output: Path, *, groups: list[list[dict]] | None = None) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    stories = [sample["story"] for sample in samples]
    skeletons = [story_skeleton(row["story"], row.get("params", {})) for row in samples]
    # Destroy word order without adding vocabulary: a sanity control, not training data.
    rng = random.Random(0)
    scrambled = []
    for story in stories:
        words = story.split()
        rng.shuffle(words)
        scrambled.append(" ".join(words))
    variants = {
        "all_grouped": (stories, False),
        "all_shuffled": (stories, True),
        "exact_deduplicated": (sorted(set(stories)), True),
        "all_skeletons": (skeletons, True),
        "unique_skeletons": (sorted(set(skeletons)), True),
        "word_order_destroyed_control": (scrambled, True),
    }
    result = dict(dictionary_bytes=DICTIONARY_BYTES, lzma2_preset=6, shuffle_seed=0,
                  format="XZ of UTF-8 JSONL; each line is only a JSON story string", variants={})
    for name, (texts, shuffle) in variants.items():
        compressed, metrics = pack(texts, shuffle=shuffle)
        path = output / f"{name}.stories.jsonl.xz"
        path.write_bytes(compressed)
        result["variants"][name] = dict(file=path.name, **metrics)
    if groups:
        result["growth_curve"] = []
        for count in (10, 50, 100, 250, 500, 1000):
            texts = [row["story"] for group in groups for row in group[:count]]
            _, metrics = pack(texts, shuffle=True)
            result["growth_curve"].append(dict(max_per_world=count, **metrics))
    (output / "compression.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def render_report(worlds: list[dict], pooled: dict, count: int, seed: int) -> str:
    lines = ["# Canonical Story Compression", "",
             f"Offline sampling: {count} requested per world, seed {seed}. No API calls or code repairs.",
             "Only story text is compressed, not prompts, params, QA, filenames, or trace metadata.",
             "LZMA2 preset 6, explicit 64 MiB dictionary, XZ container. Lower XZ/input ratio means more predictable/compressible text.", "",
             "| World | Returned | Exact unique | Skeleton unique | Text MiB | XZ KiB | XZ/input | XZ bytes/story |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in worlds:
        stats = row["compression"]
        ratio = f"{stats['ratio']:.2%}" if stats["ratio"] is not None else "-"
        per_story = f"{stats['bytes_per_story']:.1f}" if stats["bytes_per_story"] is not None else "-"
        lines.append(f"| {row['name']} | {row['samples']} | {row['exact_unique']} | {row['skeleton_unique']} | "
                     f"{stats['input_bytes'] / 2**20:.2f} | {stats['xz_bytes'] / 1024:.1f} | {ratio} | {per_story} |")
    lines += ["", "## Pooled Corpus", "",
              "| Variant | Stories | Text MiB | XZ KiB | XZ/input | XZ bytes/story |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name, stats in pooled["variants"].items():
        ratio = f"{stats['ratio']:.2%}" if stats["ratio"] is not None else "-"
        per_story = f"{stats['bytes_per_story']:.1f}" if stats["bytes_per_story"] is not None else "-"
        lines.append(f"| [{name}](pooled/{stats['file']}) | {stats['stories']} | {stats['input_bytes'] / 2**20:.2f} | "
                     f"{stats['xz_bytes'] / 1024:.1f} | {ratio} | {per_story} |")
    summed = sum(row["compression"]["xz_bytes"] for row in worlds)
    combined = pooled["variants"]["all_shuffled"]["xz_bytes"]
    lines += ["", f"Sum of individually compressed worlds: {summed / 1024:.1f} KiB; pooled shuffled: {combined / 1024:.1f} KiB."]
    if pooled.get("growth_curve"):
        lines += ["", "## Compression Growth", "",
                  "| Up to stories/world | Returned stories | XZ KiB | XZ/input | XZ bytes/story |",
                  "| --- | ---: | ---: | ---: | ---: |"]
        for stats in pooled["growth_curve"]:
            if stats["stories"]:
                lines.append(f"| {stats['max_per_world']} | {stats['stories']} | {stats['xz_bytes'] / 1024:.1f} | "
                             f"{stats['ratio']:.2%} | {stats['bytes_per_story']:.1f} |")
    lines += [
              "", "## Interpretation", "",
              "Exact duplicates count repeated complete strings. Skeleton counts also remove known parameter values; they are not a count of plots.",
              "Compare all_shuffled with exact_deduplicated to see repetition left after ordinary deduplication.",
              "Grouped versus shuffled checks ordering sensitivity. The word-order-destroyed control tests whether a compression-only optimizer could reward bad prose.",
              "These are reference generators, not 21 newly generated worlds. A matched natural-story control is still needed before setting an absolute acceptance threshold.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--samples-jsonl", type=Path, nargs="+", help="pool existing sample files instead of running canonical worlds")
    args = parser.parse_args()
    if args.count < 1 or args.timeout <= 0:
        parser.error("count and timeout must be positive")
    if args.out.exists():
        parser.error("output already exists; use a new directory to retain earlier data")
    args.out.mkdir(parents=True)
    import prompt_trials as trials

    worlds = []
    all_rows = []
    groups = []
    selected = args.samples_jsonl or list(canonical_examples.CANONICAL_EXAMPLES.values())
    names = ([f"samples_{index + 1}" for index in range(len(selected))] if args.samples_jsonl
             else list(canonical_examples.CANONICAL_EXAMPLES))
    for name, source in zip(names, selected):
        output = args.out / name
        output.mkdir()
        if args.samples_jsonl:
            rows = trials.jsonl(source)
            rows = [row.get("sample", row) for row in rows]
            status = dict(ok=bool(rows))
        else:
            shutil.copyfile(source, output / "source.py")
            status, rows = trials.sample(source, args.count, args.seed, args.timeout)
            trials.save(output / "run.json", status)
        for row in rows:
            trials.append(output / "samples.jsonl", row)
        compressed, stats = pack([row["story"] for row in rows], shuffle=True)
        (output / "stories.jsonl.xz").write_bytes(compressed)
        result = dict(name=name, source=str(source), source_sha256=trials.digest(source),
                      ok=status["ok"], samples=len(rows),
                      exact_unique=len({row["story"] for row in rows}),
                      skeleton_unique=len({story_skeleton(row["story"], row.get("params", {})) for row in rows}),
                      compression=stats)
        trials.save(output / "metrics.json", result)
        worlds.append(result)
        all_rows.extend(rows)
        groups.append(rows)
        print(f"{name}: {len(rows)} samples, {result['exact_unique']} exact, XZ/input={stats['ratio']}", flush=True)
    pooled = pooled_review(all_rows, args.out / "pooled", groups=groups)
    trials.save(args.out / "review.json", dict(requested_per_world=args.count, seed=args.seed, worlds=worlds, pooled=pooled))
    (args.out / "report.md").write_text(render_report(worlds, pooled, args.count, args.seed))
    print(f"Wrote {args.out / 'report.md'}")
    return int(any(not row["ok"] for row in worlds))


if __name__ == "__main__":
    raise SystemExit(main())
