"""Quality-gated geometric score using pooled, cross-story compression reuse."""

from __future__ import annotations

from functools import lru_cache
import json
import lzma
import math
import random


PROTOCOL = "quality_diversity_geometric_v1"
DEFAULT_MINIMUM_QUALITY = 6.0
DICTIONARY_BYTES = 64 * 1024 * 1024


def policy(minimum_quality: float = DEFAULT_MINIMUM_QUALITY) -> dict:
    if not math.isfinite(minimum_quality) or not 0 <= minimum_quality <= 9:
        raise ValueError("minimum quality must be between 0 and 9")
    return dict(protocol=PROTOCOL, minimum_quality=minimum_quality,
                formula="100 * usable_unique_yield * sqrt(mean_quality/9 * compression_retention)",
                duplicates="exact story strings count once; use lowest qualifying source-world rating",
                compression="raw LZMA2, preset 6, empty-stream bytes subtracted",
                dictionary_bytes=DICTIONARY_BYTES, shuffle_seed=0)


def encode_story(story: str) -> bytes:
    return (json.dumps(story, ensure_ascii=False) + "\n").encode("utf-8")


def compressed_size(data: bytes, dictionary_bytes: int) -> int:
    filters = [dict(id=lzma.FILTER_LZMA2, preset=6, dict_size=dictionary_bytes)]
    packed = lzma.compress(data, format=lzma.FORMAT_RAW, filters=filters)
    empty = lzma.compress(b"", format=lzma.FORMAT_RAW, filters=filters)
    return max(0, len(packed) - len(empty))


@lru_cache(maxsize=32768)
def individual_size(story: str) -> int:
    data = encode_story(story)
    # A larger dictionary cannot add history to a story that fits in 64 KiB.
    dictionary = 65536 if len(data) <= 65536 else DICTIONARY_BYTES
    return compressed_size(data, dictionary)


def compression_retention(stories: list[str]) -> dict:
    if not stories:
        return dict(stories=0, pooled_bytes=0, independent_bytes=0, retention=0.0)
    if any(not isinstance(story, str) or not story.strip() for story in stories):
        raise ValueError("compression scoring requires nonempty story strings")
    ordered = sorted(stories)
    random.Random(0).shuffle(ordered)
    pooled = compressed_size(b"".join(map(encode_story, ordered)), DICTIONARY_BYTES)
    independent = sum(individual_size(story) for story in ordered)
    return dict(stories=len(stories), pooled_bytes=pooled, independent_bytes=independent,
                retention=min(1.0, pooled / independent) if independent else 0.0)


def score_dataset(checks: list[dict], ratings: dict[str, dict], groups: list[list[dict]],
                  requested_per_world: int, *, minimum_quality=DEFAULT_MINIMUM_QUALITY) -> dict:
    """Score an arm or whole trial from its actual pooled, quality-qualified stories."""
    settings = policy(minimum_quality)
    if not checks or len(checks) != len(groups) or requested_per_world < 1:
        raise ValueError("aligned nonempty checks/groups and positive requested count are required")
    if len({check["script"] for check in checks}) != len(checks):
        raise ValueError("duplicate world identifiers")
    result = dict(policy=settings, planned_worlds=len(checks), usable_worlds=0, unrated_worlds=0,
                  runtime_rejected_worlds=0, quality_rejected_worlds=0,
                  requested_samples=len(checks) * requested_per_world, usable_samples=0,
                  yield_fraction=None, quality=None, quality_mean=None, diversity=None, score=None)
    quality_by_story = {}
    qualified_returned = 0
    for check, samples in zip(checks, groups):
        if not check["final"]["ok"] or not check["verify"]["ok"] or not samples:
            result["runtime_rejected_worlds"] += 1
            continue
        rating = ratings.get(check["script"], {})
        rating_data = rating.get("rating") or {}
        overall = rating_data.get("overall") if isinstance(rating_data, dict) else None
        if not rating.get("ok") or not isinstance(overall, (int, float)) or isinstance(overall, bool) or not math.isfinite(overall) or not 0 <= overall <= 9:
            result["unrated_worlds"] += 1
            continue
        if overall < minimum_quality:
            result["quality_rejected_worlds"] += 1
            continue
        selected = [sample["story"] for sample in samples[:requested_per_world]]
        for story in selected:
            quality_by_story[story] = min(overall, quality_by_story.get(story, overall))
        qualified_returned += len(selected)
        result["usable_worlds"] += 1
    if result["unrated_worlds"]:
        result["status"] = "unrated"
        return result
    compression = compression_retention(list(quality_by_story))
    count = len(quality_by_story)
    q = math.fsum(quality_by_story.values()) / (9 * count) if count else 0.0
    coverage = count / result["requested_samples"]
    d = compression["retention"]
    result.update(status="complete", usable_samples=count, yield_fraction=coverage,
                  qualified_returned_samples=qualified_returned,
                  exact_duplicates_removed=qualified_returned - count,
                  quality=q, quality_mean=q * 9, diversity=d, compression=compression,
                  score=100 * coverage * math.sqrt(q * d))
    return result
