#!/usr/bin/env python3
"""Export StoryWorld samples as OpenAI-compatible chat JSONL.

The exporter runs standalone StoryWorld scripts through their public CLI:

    python storyworlds/worlds/puddles.py -n 10 --seed 123 --qa --json

It parses the returned StorySample JSON and writes line-oriented chat records:

    {"messages": [{"role": "system", ...}, {"role": "user", ...},
                  {"role": "assistant", ...}],
     "metadata": {...}}

This script intentionally has no ML dependencies.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import random
import re
import subprocess
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from math import ceil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORLDS_DIR = ROOT / "storyworlds" / "worlds"
DEFAULT_SYSTEM = (
    "You are StoryWorld, a grounded children's-story model. "
    "Write complete, child-facing stories and answers that preserve the given "
    "characters, objects, causes, and outcomes."
)
DEFAULT_WORLD_QA_PREAMBLES = [
    "",
    "",
    "",
    "Quick question: ",
    "One more thing: ",
    "Different question: ",
    "General question: ",
]


@dataclass
class WorldRun:
    index: int
    world: str
    seed: int
    ok: bool
    seconds: float
    samples: int = 0
    raw_samples: int = 0
    duplicate_samples_removed: int = 0
    samples_cap_dropped: int = 0
    rows: int = 0
    error: str | None = None


@dataclass
class WorldQAPoolStats:
    mode: str = "own"
    worlds_attempted: int = 0
    worlds_ok: int = 0
    worlds_failed: int = 0
    raw_items: int = 0
    unique_items: int = 0
    duplicate_items: int = 0
    failures: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ExportStats:
    started_at: float = field(default_factory=time.time)
    worlds_seen: int = 0
    worlds_ok: int = 0
    worlds_failed: int = 0
    samples: int = 0
    rows: int = 0
    rows_over_target: int = 0
    token_counts: list[int] = field(default_factory=list)
    message_counts: list[int] = field(default_factory=list)
    user_turn_counts: list[int] = field(default_factory=list)
    assistant_turn_counts: list[int] = field(default_factory=list)
    followup_counts: list[int] = field(default_factory=list)
    base_token_counts: list[int] = field(default_factory=list)
    row_task_counts: dict[str, int] = field(default_factory=dict)
    turn_task_counts: dict[str, int] = field(default_factory=dict)
    pack_questions_available: dict[str, int] = field(default_factory=dict)
    pack_questions_used: dict[str, int] = field(default_factory=dict)
    pack_questions_unused_fit: dict[str, int] = field(default_factory=dict)
    pack_stories_attempted: int = 0
    pack_stories_failed_to_fit: int = 0
    raw_samples: int = 0
    duplicate_samples_removed: int = 0
    samples_cap_dropped: int = 0
    failure_kinds: dict[str, int] = field(default_factory=dict)
    failures: list[dict[str, Any]] = field(default_factory=list)


class DuplicateTracker:
    """Track duplicated source content before chat rows are packed."""

    def __init__(self) -> None:
        self.groups: dict[str, dict[str, dict[str, Any]]] = {
            "story": {},
            "prompt": {},
            "story_qa_question": {},
            "story_qa_answer": {},
            "story_qa_pair": {},
            "world_qa_question_expected": {},
            "world_qa_answer_expected": {},
            "world_qa_pair_expected": {},
        }

    def add(self, group: str, text: str, where: str) -> None:
        key = normalize_for_duplicate(text)
        if not key:
            return
        bucket = self.groups[group]
        item = bucket.setdefault(
            key,
            {"count": 0, "preview": text[:240], "first": where, "examples": []},
        )
        item["count"] += 1
        if len(item["examples"]) < 5:
            item["examples"].append(where)

    def summary(self, topn: int = 10) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for group, bucket in self.groups.items():
            total = sum(item["count"] for item in bucket.values())
            duplicate_items = [item for item in bucket.values() if item["count"] > 1]
            duplicate_occurrences = sum(item["count"] - 1 for item in duplicate_items)
            duplicate_items.sort(key=lambda item: item["count"], reverse=True)
            out[group] = {
                "total": total,
                "unique": len(bucket),
                "duplicate_keys": len(duplicate_items),
                "duplicate_occurrences": duplicate_occurrences,
                "top_duplicates": duplicate_items[:topn],
            }
        return out


class TokenCounter:
    """Count chat-template tokens exactly when a tokenizer is supplied.

    Without a tokenizer, this uses a conservative character heuristic.  The
    exporter stays stdlib-only by default, but can become exact on the training
    machine after `train_tokenizer.py` has produced a tokenizer directory.
    """

    def __init__(self, tokenizer_path: Path | None, chars_per_token: float) -> None:
        self.tokenizer = None
        self.mode = "chars_per_token"
        self.chars_per_token = chars_per_token
        if tokenizer_path is None:
            return
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise SystemExit(
                "--tokenizer requires transformers; omit it to use approximate "
                "character-based token counts."
            ) from exc
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        self.mode = "tokenizer"

    def count_text(self, text: str) -> int:
        if self.tokenizer is not None:
            return len(self.tokenizer.encode(text, add_special_tokens=False))
        return max(1, ceil(len(text) / self.chars_per_token))

    def count_messages(self, messages: list[dict[str, str]]) -> int:
        rendered = "<|begin_of_text|>" + "".join(
            f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
            for m in messages
        )
        return self.count_text(rendered)


def summarize_numbers(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "min": None,
            "p50": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "max": None,
            "mean": None,
        }
    ordered = sorted(values)

    def pct(q: float) -> int:
        index = min(len(ordered) - 1, max(0, ceil(q * len(ordered)) - 1))
        return ordered[index]

    return {
        "count": len(ordered),
        "min": ordered[0],
        "p50": pct(0.50),
        "p90": pct(0.90),
        "p95": pct(0.95),
        "p99": pct(0.99),
        "max": ordered[-1],
        "mean": round(sum(ordered) / len(ordered), 2),
    }


def token_manifest(
    values: list[int],
    max_context_tokens: int,
    token_counter: TokenCounter,
) -> dict[str, Any]:
    summary = summarize_numbers(values)
    total = sum(values)
    capacity = len(values) * max_context_tokens
    return {
        "counter_mode": token_counter.mode,
        "chars_per_token": token_counter.chars_per_token
        if token_counter.mode == "chars_per_token"
        else None,
        "total_tokens_estimated": total,
        "target_context_tokens": max_context_tokens,
        "utilization_mean": round(total / capacity, 4) if capacity else None,
        "rows_over_target": sum(1 for value in values if value > max_context_tokens),
        "rows_at_or_above_90pct": sum(
            1 for value in values if value >= int(max_context_tokens * 0.9)
        ),
        "rows_below_50pct": sum(
            1 for value in values if value < int(max_context_tokens * 0.5)
        ),
        "token_count": summary,
    }


def inc(counter: dict[str, int], key: str, amount: int = 1) -> None:
    counter[key] = counter.get(key, 0) + amount


def normalize_for_duplicate(text: str) -> str:
    lowered = text.casefold().strip()
    return re.sub(r"\s+", " ", lowered)


def failure_kind(error: str) -> str:
    lowered = error.casefold()
    if "timeout" in lowered:
        return "timeout"
    if "invalid json" in lowered:
        return "invalid_json"
    if "syntaxerror" in lowered:
        return "syntax_error"
    if "storyerror" in lowered or "no valid combination" in lowered:
        return "story_error"
    if "recursionerror" in lowered:
        return "recursion_error"
    if "attributeerror" in lowered:
        return "attribute_error"
    if "keyerror" in lowered:
        return "key_error"
    if "typeerror" in lowered:
        return "type_error"
    if "traceback" in lowered:
        return "traceback"
    return "other"


def valid_qa_items(sample: dict[str, Any], task: str) -> list[dict[str, str]]:
    key = "story_qa" if task == "story_qa" else "world_qa"
    items: list[dict[str, str]] = []
    for qa in sample.get(key, []):
        if not isinstance(qa, dict) or not qa.get("question") or not qa.get("answer"):
            continue
        items.append({"question": qa["question"], "answer": qa["answer"]})
    return items


def update_duplicate_tracker(
    tracker: DuplicateTracker,
    *,
    world: Path,
    sample_index: int,
    sample: dict[str, Any],
) -> None:
    seed = sample.get("params", {}).get("seed", sample_index)
    where = f"{stable_rel(world)}:{seed}"
    tracker.add("story", sample.get("story", ""), where)
    for prompt_index, prompt in enumerate(sample.get("prompts", [])):
        if isinstance(prompt, str):
            tracker.add("prompt", prompt, f"{where}:prompt:{prompt_index}")
    for qa_index, qa in enumerate(valid_qa_items(sample, "story_qa")):
        question = qa["question"]
        answer = qa["answer"]
        tracker.add("story_qa_question", question, f"{where}:story_qa:{qa_index}")
        tracker.add("story_qa_answer", answer, f"{where}:story_qa:{qa_index}")
        tracker.add(
            "story_qa_pair",
            question + "\n---\n" + answer,
            f"{where}:story_qa:{qa_index}",
        )
    for qa_index, qa in enumerate(valid_qa_items(sample, "world_qa")):
        question = qa["question"]
        answer = qa["answer"]
        tracker.add(
            "world_qa_question_expected",
            question,
            f"{where}:world_qa:{qa_index}",
        )
        tracker.add(
            "world_qa_answer_expected",
            answer,
            f"{where}:world_qa:{qa_index}",
        )
        tracker.add(
            "world_qa_pair_expected",
            question + "\n---\n" + answer,
            f"{where}:world_qa:{qa_index}",
        )


def row_turn_tasks(row: dict[str, Any]) -> list[str]:
    metadata = row.get("metadata", {})
    task = metadata.get("task", "unknown")
    if task == "multiturn":
        packed = metadata.get("packed_tasks", [])
        return [str(item) for item in packed] if packed else ["multiturn"]
    return [str(task)]


def row_summary(row: dict[str, Any], preview_chars: int) -> dict[str, Any]:
    messages = row.get("messages", [])
    metadata = row.get("metadata", {})
    first_user = next(
        (m.get("content", "") for m in messages if m.get("role") == "user"),
        "",
    )
    first_assistant = next(
        (m.get("content", "") for m in messages if m.get("role") == "assistant"),
        "",
    )
    return {
        "id": row.get("id"),
        "task": metadata.get("task"),
        "world": metadata.get("world"),
        "tokens": metadata.get("estimated_tokens"),
        "messages": len(messages),
        "user_turns": sum(1 for m in messages if m.get("role") == "user"),
        "assistant_turns": sum(1 for m in messages if m.get("role") == "assistant"),
        "followups": metadata.get("packed_followups", 0),
        "turn_tasks": row_turn_tasks(row),
        "user_preview": first_user[:preview_chars],
        "assistant_preview": first_assistant[:preview_chars],
    }


def update_row_stats(stats: ExportStats, row: dict[str, Any], max_context_tokens: int) -> None:
    metadata = row.get("metadata", {})
    task = str(metadata.get("task", "unknown"))
    inc(stats.row_task_counts, task)
    messages = row.get("messages", [])
    user_turns = sum(1 for m in messages if m.get("role") == "user")
    assistant_turns = sum(1 for m in messages if m.get("role") == "assistant")
    stats.message_counts.append(len(messages))
    stats.user_turn_counts.append(user_turns)
    stats.assistant_turn_counts.append(assistant_turns)
    stats.followup_counts.append(int(metadata.get("packed_followups", 0) or 0))
    if isinstance(metadata.get("base_tokens"), int):
        stats.base_token_counts.append(metadata["base_tokens"])
    for turn_task in row_turn_tasks(row):
        inc(stats.turn_task_counts, turn_task)
    estimated_tokens = metadata.get("estimated_tokens")
    if isinstance(estimated_tokens, int):
        stats.token_counts.append(estimated_tokens)
        if estimated_tokens > max_context_tokens:
            stats.rows_over_target += 1


def update_pack_stats(stats: ExportStats, diagnostics: dict[str, Any]) -> None:
    for key, value in diagnostics.get("questions_available", {}).items():
        inc(stats.pack_questions_available, key, int(value))
    for key, value in diagnostics.get("questions_used", {}).items():
        inc(stats.pack_questions_used, key, int(value))
    for key, value in diagnostics.get("questions_unused_fit", {}).items():
        inc(stats.pack_questions_unused_fit, key, int(value))
    stats.pack_stories_attempted += int(diagnostics.get("stories_attempted", 0))
    stats.pack_stories_failed_to_fit += int(diagnostics.get("stories_failed_to_fit", 0))


def discover_worlds(worlds_dir: Path, recursive: bool) -> list[Path]:
    pattern = "**/*.py" if recursive else "*.py"
    return sorted(
        path for path in worlds_dir.glob(pattern)
        if not path.name.startswith("_") and "__pycache__" not in path.parts
    )


def stable_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    storyworlds_path = str(ROOT / "storyworlds")
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        storyworlds_path
        if not current
        else storyworlds_path + os.pathsep + current
    )
    return env


def compact_error(text: str, max_chars: int = 4000) -> str:
    stripped = text.strip() or "nonzero exit"
    if len(stripped) <= max_chars:
        return stripped
    return stripped[:1000] + "\n...\n" + stripped[-(max_chars - 1006):]


def run_world(
    python: str,
    world: Path,
    samples_per_world: int,
    seed: int,
    timeout: float,
) -> tuple[list[dict[str, Any]], str | None, float]:
    cmd = [
        python,
        str(world),
        "-n",
        str(samples_per_world),
        "--seed",
        str(seed),
        "--qa",
        "--json",
    ]
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=subprocess_env(),
        )
    except subprocess.TimeoutExpired:
        return [], f"timeout after {timeout:g}s", time.time() - start

    elapsed = time.time() - start
    if result.returncode:
        err = result.stderr or result.stdout
        return [], compact_error(err), elapsed

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return [], f"invalid JSON: {exc}", elapsed

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return [], f"expected JSON object/list, got {type(data).__name__}", elapsed
    samples = [x for x in data if isinstance(x, dict) and x.get("story")]
    return samples, None, elapsed


def filter_samples(
    samples: list[dict[str, Any]],
    *,
    dedupe_stories: bool,
    shuffle_samples: bool,
    sample_cap_per_world: int | None,
    seed: int,
) -> tuple[list[dict[str, Any]], int, int]:
    duplicate_removed = 0
    cap_dropped = 0
    filtered = samples

    if dedupe_stories:
        seen: set[str] = set()
        filtered = []
        for sample in samples:
            key = normalize_for_duplicate(str(sample.get("story") or ""))
            if key in seen:
                duplicate_removed += 1
                continue
            seen.add(key)
            filtered.append(sample)

    if shuffle_samples:
        filtered = list(filtered)
        random.Random(seed ^ 0x5A17A11).shuffle(filtered)

    if sample_cap_per_world is not None and len(filtered) > sample_cap_per_world:
        cap_dropped = len(filtered) - sample_cap_per_world
        filtered = filtered[:sample_cap_per_world]

    return filtered, duplicate_removed, cap_dropped


def collect_world_qa_pool(
    *,
    worlds: list[Path],
    python: str,
    samples_per_world: int,
    seed: int,
    timeout: float,
    jobs: int,
) -> tuple[list[dict[str, str]], WorldQAPoolStats]:
    stats = WorldQAPoolStats(
        mode="global",
        worlds_attempted=len(worlds),
    )
    if samples_per_world < 1 or not worlds:
        return [], stats

    rng = random.Random(seed ^ 0x51A7E5)
    world_seeds = [rng.randrange(2**31) for _ in worlds]
    by_pair: dict[str, dict[str, str]] = {}

    def submit_one(world: Path, world_seed: int) -> tuple[Path, int, list[dict[str, Any]], str | None]:
        samples, error, _elapsed = run_world(
            python,
            world,
            samples_per_world,
            world_seed,
            timeout,
        )
        return world, world_seed, samples, error

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        future_map = {
            pool.submit(submit_one, world, world_seed): (world, world_seed)
            for world, world_seed in zip(worlds, world_seeds)
        }
        for future in concurrent.futures.as_completed(future_map):
            world, world_seed = future_map[future]
            rel = stable_rel(world)
            try:
                _world, _seed, samples, error = future.result()
            except Exception as exc:  # pragma: no cover
                samples, error = [], repr(exc)
            if error:
                stats.worlds_failed += 1
                stats.failures.append({
                    "world": rel,
                    "seed": world_seed,
                    "error": error,
                    "kind": failure_kind(error),
                })
                continue
            stats.worlds_ok += 1
            for sample_index, sample in enumerate(samples):
                source_seed = sample.get("params", {}).get("seed", sample_index)
                for qa_index, qa in enumerate(valid_qa_items(sample, "world_qa")):
                    stats.raw_items += 1
                    pair_key = normalize_for_duplicate(qa["question"] + "\n---\n" + qa["answer"])
                    by_pair.setdefault(pair_key, {
                        "task": "world_qa",
                        "question": qa["question"],
                        "answer": qa["answer"],
                        "source": f"{rel}:{source_seed}:world_qa:{qa_index}",
                    })

    pool_items = list(by_pair.values())
    pool_items.sort(key=lambda item: (item["question"], item["answer"], item["source"]))
    stats.unique_items = len(pool_items)
    stats.duplicate_items = stats.raw_items - stats.unique_items
    return pool_items, stats


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def choose_prompt(sample: dict[str, Any], policy: str, rng: random.Random) -> list[str]:
    prompts = [p for p in sample.get("prompts", []) if isinstance(p, str) and p.strip()]
    if not prompts:
        return ["Write the story described by these StoryWorld parameters."]
    if policy == "first":
        return [prompts[0]]
    if policy == "random":
        return [rng.choice(prompts)]
    if policy == "all":
        return prompts
    raise ValueError(f"unknown prompt policy: {policy}")


def story_user_content(sample: dict[str, Any], prompt: str, user_format: str) -> str:
    params = sample.get("params", {})
    if user_format == "prompt":
        return prompt
    if user_format == "params":
        return "Task: write_story\nParams: " + compact_json(params)
    if user_format == "prompt+params":
        return (
            "Task: write_story\n"
            f"Prompt: {prompt}\n"
            "Params: " + compact_json(params)
        )
    raise ValueError(f"unknown user format: {user_format}")


def story_qa_user_content(sample: dict[str, Any], question: str) -> str:
    return (
        "Task: answer_story_question\n"
        "Use the story below. Answer with grounded, child-facing prose.\n\n"
        f"Story:\n{sample['story']}\n\n"
        f"Question: {question}"
    )


def world_qa_user_content(sample: dict[str, Any], question: str) -> str:
    return (
        "Task: answer_world_question\n"
        "Answer at a child-friendly level. Stay concrete and concise.\n"
        "Params: "
        + compact_json(sample.get("params", {}))
        + f"\nQuestion: {question}"
    )


def followup_user_content(task: str, question: str, preamble: str = "") -> str:
    if task == "story_qa":
        return question
    return preamble + question


def chat_row(
    *,
    row_id: str,
    system: str,
    user: str,
    assistant: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": row_id,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        "metadata": metadata,
    }


def messages_row(
    *,
    row_id: str,
    messages: list[dict[str, str]],
    metadata: dict[str, Any],
    token_counter: TokenCounter | None = None,
) -> dict[str, Any]:
    if token_counter is not None:
        metadata = {**metadata, "estimated_tokens": token_counter.count_messages(messages)}
    return {"id": row_id, "messages": messages, "metadata": metadata}


def world_qa_preamble(rng: random.Random) -> str:
    return rng.choice(DEFAULT_WORLD_QA_PREAMBLES)


def sample_global_world_qa_turns(
    *,
    pool: list[dict[str, str]],
    max_per_sample: int,
    rng: random.Random,
) -> list[dict[str, str]]:
    if not pool or max_per_sample <= 0:
        return []
    chosen = rng.sample(pool, min(max_per_sample, len(pool)))
    return [
        {
            "task": "world_qa",
            "question": item["question"],
            "answer": item["answer"],
            "source": item.get("source", "global_pool"),
            "preamble": world_qa_preamble(rng),
        }
        for item in chosen
    ]


def qa_turns(
    sample: dict[str, Any],
    tasks: set[str],
    rng: random.Random,
    *,
    world_qa_mode: str,
    world_qa_pool: list[dict[str, str]],
    world_qa_max_per_sample: int,
) -> list[dict[str, str]]:
    turns: list[dict[str, str]] = []
    if "story_qa" in tasks:
        for qa in valid_qa_items(sample, "story_qa"):
            turns.append({
                "task": "story_qa",
                "question": qa["question"],
                "answer": qa["answer"],
            })
    if "world_qa" in tasks:
        if world_qa_mode in ("own", "mixed"):
            for qa in valid_qa_items(sample, "world_qa"):
                turns.append({
                    "task": "world_qa",
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "source": "own_sample",
                    "preamble": world_qa_preamble(rng),
                })
        if world_qa_mode in ("global", "mixed"):
            seen_pairs = {
                normalize_for_duplicate(t["question"] + "\n---\n" + t["answer"])
                for t in turns
                if t["task"] == "world_qa"
            }
            for turn in sample_global_world_qa_turns(
                pool=world_qa_pool,
                max_per_sample=world_qa_max_per_sample,
                rng=rng,
            ):
                pair_key = normalize_for_duplicate(turn["question"] + "\n---\n" + turn["answer"])
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                turns.append(turn)
    rng.shuffle(turns)
    return turns


def rows_for_sample(
    *,
    world: Path,
    sample_index: int,
    sample: dict[str, Any],
    system: str,
    tasks: set[str],
    prompt_policy: str,
    user_format: str,
    row_mode: str,
    max_context_tokens: int,
    token_counter: TokenCounter,
    world_qa_mode: str,
    world_qa_pool: list[dict[str, str]],
    world_qa_max_per_sample: int,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    world_id = stable_rel(world)
    params = sample.get("params", {})
    seed = params.get("seed")
    base_id = f"{world.stem}:{seed if seed is not None else sample_index}"
    rows: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {
        "questions_available": {},
        "questions_used": {},
        "questions_unused_fit": {},
        "stories_attempted": 0,
        "stories_failed_to_fit": 0,
    }

    if row_mode in ("single", "both") and "story" in tasks:
        for prompt_index, prompt in enumerate(choose_prompt(sample, prompt_policy, rng)):
            row = chat_row(
                row_id=f"{base_id}:story:{prompt_index}",
                system=system,
                user=story_user_content(sample, prompt, user_format),
                assistant=sample["story"],
                metadata={
                    "task": "story",
                    "world": world_id,
                    "sample_index": sample_index,
                    "prompt_index": prompt_index,
                    "params": params,
                },
            )
            row["metadata"]["estimated_tokens"] = token_counter.count_messages(row["messages"])
            rows.append(row)

    if row_mode in ("single", "both") and "story_qa" in tasks:
        for qa_index, qa in enumerate(valid_qa_items(sample, "story_qa")):
            question = qa["question"]
            answer = qa["answer"]
            row = chat_row(
                row_id=f"{base_id}:story_qa:{qa_index}",
                system=system,
                user=story_qa_user_content(sample, question),
                assistant=answer,
                metadata={
                    "task": "story_qa",
                    "world": world_id,
                    "sample_index": sample_index,
                    "qa_index": qa_index,
                    "params": params,
                },
            )
            row["metadata"]["estimated_tokens"] = token_counter.count_messages(row["messages"])
            rows.append(row)

    if row_mode in ("single", "both") and "world_qa" in tasks:
        for qa_index, qa in enumerate(valid_qa_items(sample, "world_qa")):
            question = qa["question"]
            answer = qa["answer"]
            row = chat_row(
                row_id=f"{base_id}:world_qa:{qa_index}",
                system=system,
                user=world_qa_user_content(sample, question),
                assistant=answer,
                metadata={
                    "task": "world_qa",
                    "world": world_id,
                    "sample_index": sample_index,
                    "qa_index": qa_index,
                    "params": params,
                },
            )
            row["metadata"]["estimated_tokens"] = token_counter.count_messages(row["messages"])
            rows.append(row)

    if row_mode not in ("multiturn", "both") or "story" not in tasks:
        return rows, diagnostics

    for prompt_index, prompt in enumerate(choose_prompt(sample, prompt_policy, rng)):
        diagnostics["stories_attempted"] += 1
        base_messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": story_user_content(sample, prompt, user_format)},
            {"role": "assistant", "content": sample["story"]},
        ]
        base_tokens = token_counter.count_messages(base_messages)
        packed_index = 0
        current = list(base_messages)
        current_tasks = ["story"]
        current_turns = 0
        used_by_task: Counter[str] = Counter()
        unused_by_task: Counter[str] = Counter()

        turns = qa_turns(
            sample,
            tasks,
            rng,
            world_qa_mode=world_qa_mode,
            world_qa_pool=world_qa_pool,
            world_qa_max_per_sample=world_qa_max_per_sample,
        )
        for turn in turns:
            inc(diagnostics["questions_available"], turn["task"])
            candidate = current + [
                {
                    "role": "user",
                    "content": followup_user_content(
                        turn["task"],
                        turn["question"],
                        turn.get("preamble", ""),
                    ),
                },
                {"role": "assistant", "content": turn["answer"]},
            ]
            if token_counter.count_messages(candidate) > max_context_tokens and current_turns:
                row = messages_row(
                    row_id=f"{base_id}:multiturn:{prompt_index}:{packed_index}",
                    messages=current,
                    metadata={
                        "task": "multiturn",
                        "world": world_id,
                        "sample_index": sample_index,
                        "prompt_index": prompt_index,
                        "params": params,
                        "packed_followups": current_turns,
                        "packed_tasks": current_tasks,
                        "max_context_tokens": max_context_tokens,
                    },
                    token_counter=token_counter,
                )
                rows.append(row)
                packed_index += 1
                current = list(base_messages)
                current_tasks = ["story"]
                current_turns = 0
                candidate = current + [
                    {
                        "role": "user",
                        "content": followup_user_content(
                            turn["task"],
                            turn["question"],
                            turn.get("preamble", ""),
                        ),
                    },
                    {"role": "assistant", "content": turn["answer"]},
                ]

            if token_counter.count_messages(candidate) <= max_context_tokens:
                current = candidate
                current_tasks.append(turn["task"])
                current_turns += 1
                used_by_task[turn["task"]] += 1
                inc(diagnostics["questions_used"], turn["task"])
            else:
                unused_by_task[turn["task"]] += 1
                inc(diagnostics["questions_unused_fit"], turn["task"])

        if current_turns or base_tokens <= max_context_tokens:
            row = messages_row(
                row_id=f"{base_id}:multiturn:{prompt_index}:{packed_index}",
                messages=current,
                metadata={
                    "task": "multiturn",
                    "world": world_id,
                    "sample_index": sample_index,
                    "prompt_index": prompt_index,
                    "params": params,
                    "packed_followups": current_turns,
                    "packed_tasks": current_tasks,
                    "max_context_tokens": max_context_tokens,
                    "base_tokens": base_tokens,
                },
                token_counter=token_counter,
            )
            rows.append(row)
        elif not current_turns:
            diagnostics["stories_failed_to_fit"] += 1

    return rows, diagnostics


def shape_manifest(stats: ExportStats) -> dict[str, Any]:
    return {
        "message_count": summarize_numbers(stats.message_counts),
        "user_turn_count": summarize_numbers(stats.user_turn_counts),
        "assistant_turn_count": summarize_numbers(stats.assistant_turn_counts),
        "followup_count": summarize_numbers(stats.followup_counts),
        "base_token_count": summarize_numbers(stats.base_token_counts),
    }


def task_manifest(stats: ExportStats) -> dict[str, Any]:
    return {
        "rows_by_task": dict(sorted(stats.row_task_counts.items())),
        "assistant_turns_by_task": dict(sorted(stats.turn_task_counts.items())),
    }


def packing_manifest(stats: ExportStats) -> dict[str, Any]:
    return {
        "stories_attempted": stats.pack_stories_attempted,
        "stories_failed_to_fit": stats.pack_stories_failed_to_fit,
        "questions_available": dict(sorted(stats.pack_questions_available.items())),
        "questions_used": dict(sorted(stats.pack_questions_used.items())),
        "questions_unused_fit": dict(sorted(stats.pack_questions_unused_fit.items())),
    }


def duplicate_manifest(tracker: DuplicateTracker) -> dict[str, Any]:
    return tracker.summary(topn=10)


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_None._\n"
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(out) + "\n"


def preview_block(text: str) -> str:
    if not text:
        return "_empty_"
    return "```text\n" + text.replace("```", "'''") + "\n```"


def row_report_section(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"## {title}\n\n_None._\n"
    parts = [f"## {title}\n"]
    for row in rows:
        parts.append(
            "\n".join([
                f"### {row['id']}",
                "",
                f"- task: `{row['task']}`",
                f"- world: `{row['world']}`",
                f"- tokens: `{row['tokens']}`",
                f"- messages/user/assistant: `{row['messages']}` / `{row['user_turns']}` / `{row['assistant_turns']}`",
                f"- followups: `{row['followups']}`",
                f"- turn tasks: `{', '.join(row['turn_tasks'])}`",
                "",
                "**User Preview**",
                preview_block(row["user_preview"]),
                "**Assistant Preview**",
                preview_block(row["assistant_preview"]),
            ])
        )
    return "\n\n".join(parts) + "\n"


def duplicate_report_section(duplicate_stats: dict[str, Any]) -> str:
    groups = []
    for group, values in duplicate_stats.items():
        groups.append([
            group,
            values["total"],
            values["unique"],
            values["duplicate_keys"],
            values["duplicate_occurrences"],
        ])
    parts = [
        "## Duplicate Source Content",
        "",
        md_table(
            ["group", "total", "unique", "duplicate_keys", "duplicate_occurrences"],
            groups,
        ),
        (
            "`world_qa_*_expected` groups are allowed to duplicate; repeated "
            "world-knowledge questions are expected across worlds."
        ),
    ]
    for group, values in duplicate_stats.items():
        top = values.get("top_duplicates", [])
        if not top:
            continue
        parts.extend([
            "",
            f"### Top Duplicates: `{group}`",
            "",
            md_table(
                ["count", "first", "preview"],
                [
                    [
                        item["count"],
                        item["first"],
                        item["preview"].replace("\n", " ")[:180],
                    ]
                    for item in top[:5]
                ],
            ),
        ])
    return "\n".join(parts) + "\n"


def build_markdown_report(
    *,
    args: argparse.Namespace,
    stats: ExportStats,
    token_counter: TokenCounter,
    runs: list[WorldRun],
    row_summaries: list[dict[str, Any]],
    duplicate_stats: dict[str, Any],
    world_qa_pool_stats: WorldQAPoolStats,
) -> str:
    token_stats = token_manifest(stats.token_counts, args.max_context_tokens, token_counter)
    shape_stats = shape_manifest(stats)
    task_stats = task_manifest(stats)
    pack_stats = packing_manifest(stats)
    rng = random.Random(args.seed ^ 0xBADC0DE)
    random_rows = rng.sample(
        row_summaries,
        min(args.report_random_samples, len(row_summaries)),
    ) if row_summaries else []
    longest_rows = sorted(
        row_summaries,
        key=lambda row: row.get("tokens") or -1,
        reverse=True,
    )[: args.report_outlier_samples]
    shortest_rows = sorted(
        row_summaries,
        key=lambda row: row.get("tokens") if row.get("tokens") is not None else 10**12,
    )[: args.report_outlier_samples]

    lines = [
        "# StoryWorld Chat Export Report",
        "",
        f"- output: `{args.out}`",
        f"- worlds dir: `{args.worlds_dir}`",
        f"- recursive: `{args.recursive}`",
        f"- row mode: `{args.row_mode}`",
        f"- tasks: `{', '.join(args.tasks)}`",
        f"- target context tokens: `{args.max_context_tokens}`",
        f"- token counter: `{token_counter.mode}`",
        f"- rows: `{stats.rows}`",
        f"- samples: `{stats.samples}`",
        f"- raw samples before filters: `{stats.raw_samples}`",
        f"- duplicate story samples removed: `{stats.duplicate_samples_removed}`",
        f"- samples dropped by cap: `{stats.samples_cap_dropped}`",
        f"- worlds ok/failed: `{stats.worlds_ok}` / `{stats.worlds_failed}`",
        f"- timeout seconds: `{args.timeout}`",
        f"- world QA mode: `{args.world_qa_mode}`",
        "",
        "## Token Stats",
        "",
        md_table(
            ["metric", "value"],
            [
                ["total estimated tokens", token_stats["total_tokens_estimated"]],
                ["mean utilization", token_stats["utilization_mean"]],
                ["rows over target", token_stats["rows_over_target"]],
                ["rows >= 90% target", token_stats["rows_at_or_above_90pct"]],
                ["rows < 50% target", token_stats["rows_below_50pct"]],
            ],
        ),
        md_table(
            ["count", "min", "mean", "p50", "p90", "p95", "p99", "max"],
            [[
                token_stats["token_count"]["count"],
                token_stats["token_count"]["min"],
                token_stats["token_count"]["mean"],
                token_stats["token_count"]["p50"],
                token_stats["token_count"]["p90"],
                token_stats["token_count"]["p95"],
                token_stats["token_count"]["p99"],
                token_stats["token_count"]["max"],
            ]],
        ),
        "## Turn And Message Stats",
        "",
        md_table(
            ["field", "min", "mean", "p50", "p90", "max"],
            [
                [
                    name,
                    values["min"],
                    values["mean"],
                    values["p50"],
                    values["p90"],
                    values["max"],
                ]
                for name, values in shape_stats.items()
            ],
        ),
        "## Task Mix",
        "",
        "### Rows By Task",
        "",
        md_table(
            ["task", "rows"],
            [[task, count] for task, count in task_stats["rows_by_task"].items()],
        ),
        "### Assistant Turns By Task",
        "",
        md_table(
            ["task", "turns"],
            [[task, count] for task, count in task_stats["assistant_turns_by_task"].items()],
        ),
        "## Packing Losses",
        "",
        md_table(
            ["metric", "value"],
            [
                ["stories attempted", pack_stats["stories_attempted"]],
                ["stories failed to fit", pack_stats["stories_failed_to_fit"]],
            ],
        ),
        md_table(
            ["task", "available", "used", "unused_fit"],
            [
                [
                    task,
                    pack_stats["questions_available"].get(task, 0),
                    pack_stats["questions_used"].get(task, 0),
                    pack_stats["questions_unused_fit"].get(task, 0),
                ]
                for task in sorted(set(pack_stats["questions_available"]) | set(pack_stats["questions_used"]) | set(pack_stats["questions_unused_fit"]))
            ],
        ),
    ]
    lines.extend([
        "## World QA Pool",
        "",
        md_table(
            ["metric", "value"],
            [
                ["mode", world_qa_pool_stats.mode],
                ["worlds attempted", world_qa_pool_stats.worlds_attempted],
                ["worlds ok", world_qa_pool_stats.worlds_ok],
                ["worlds failed", world_qa_pool_stats.worlds_failed],
                ["raw items", world_qa_pool_stats.raw_items],
                ["unique items", world_qa_pool_stats.unique_items],
                ["duplicate items removed", world_qa_pool_stats.duplicate_items],
                ["max global per sample", args.world_qa_max_per_sample],
            ],
        ),
    ])
    if world_qa_pool_stats.failures:
        lines.extend([
            "### World QA Pool Failures",
            "",
            md_table(
                ["world", "seed", "kind", "error"],
                [
                    [f["world"], f["seed"], f["kind"], f["error"]]
                    for f in world_qa_pool_stats.failures[:50]
                ],
            ),
        ])
    if stats.failures:
        lines.extend([
            "## World Failures",
            "",
            md_table(
                ["kind", "count"],
                [[kind, count] for kind, count in sorted(stats.failure_kinds.items())],
            ),
            md_table(
                ["world", "seed", "error"],
                [
                    [failure["world"], failure["seed"], failure["error"]]
                    for failure in stats.failures[:50]
                ],
            ),
        ])
    lines.append(duplicate_report_section(duplicate_stats))
    lines.append(row_report_section("Random Row Samples", random_rows))
    lines.append(row_report_section("Longest Row Samples", longest_rows))
    lines.append(row_report_section("Shortest Row Samples", shortest_rows))
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worlds-dir", type=Path, default=DEFAULT_WORLDS_DIR)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument(
        "--shuffle-worlds",
        action="store_true",
        help="shuffle discovered worlds deterministically with --seed before slicing",
    )
    parser.add_argument(
        "--start-world",
        type=int,
        default=0,
        help="zero-based offset into the sorted discovered world list",
    )
    parser.add_argument("--max-worlds", type=int, default=None)
    parser.add_argument("--samples-per-world", type=int, default=10)
    parser.add_argument(
        "--dedupe-story-samples",
        action="store_true",
        help="dedupe samples from each world by rendered story text before packing rows",
    )
    parser.add_argument(
        "--shuffle-samples",
        action="store_true",
        help="shuffle each world's samples deterministically before applying --sample-cap-per-world",
    )
    parser.add_argument(
        "--sample-cap-per-world",
        type=int,
        default=None,
        help="maximum samples to keep per world after optional dedupe/shuffle",
    )
    parser.add_argument("--seed", type=int, default=20260621)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="optional markdown report with export statistics and samples",
    )
    parser.add_argument("--report-random-samples", type=int, default=5)
    parser.add_argument("--report-outlier-samples", type=int, default=5)
    parser.add_argument("--report-preview-chars", type=int, default=700)
    parser.add_argument(
        "--tasks",
        nargs="+",
        default=["story", "story_qa"],
        choices=["story", "story_qa", "world_qa"],
    )
    parser.add_argument(
        "--prompt-policy",
        choices=["first", "random", "all"],
        default="first",
    )
    parser.add_argument(
        "--user-format",
        choices=["prompt", "params", "prompt+params"],
        default="prompt+params",
    )
    parser.add_argument(
        "--row-mode",
        choices=["single", "multiturn", "both"],
        default="single",
        help=(
            "single writes one request/response per row; multiturn packs story "
            "plus follow-up QA turns into rows; both writes both forms"
        ),
    )
    parser.add_argument(
        "--max-context-tokens",
        type=int,
        default=1024,
        help="packing target for --row-mode multiturn/both",
    )
    parser.add_argument(
        "--tokenizer",
        type=Path,
        default=None,
        help="optional tokenizer directory for exact chat-template token counts",
    )
    parser.add_argument(
        "--chars-per-token",
        type=float,
        default=4.0,
        help="fallback approximate token counter when --tokenizer is omitted",
    )
    parser.add_argument(
        "--world-qa-mode",
        choices=["own", "global", "mixed"],
        default="own",
        help=(
            "how multiturn packing sources world_qa turns: own sample, "
            "deduped global pool, or both"
        ),
    )
    parser.add_argument(
        "--world-qa-pool-samples-per-world",
        type=int,
        default=1,
        help="samples per world for the global world_qa collection prepass",
    )
    parser.add_argument(
        "--world-qa-max-per-sample",
        type=int,
        default=3,
        help="maximum global world_qa turns sampled into each conversation",
    )
    parser.add_argument("--system", default=DEFAULT_SYSTEM)
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="stop after the first world failure",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples_per_world < 1:
        raise SystemExit("--samples-per-world must be at least 1")
    if args.sample_cap_per_world is not None and args.sample_cap_per_world < 1:
        raise SystemExit("--sample-cap-per-world must be at least 1 when set")
    if args.jobs < 1:
        raise SystemExit("--jobs must be at least 1")
    if args.max_context_tokens < 64:
        raise SystemExit("--max-context-tokens must be at least 64")
    if args.chars_per_token <= 0:
        raise SystemExit("--chars-per-token must be positive")
    if args.report_random_samples < 0 or args.report_outlier_samples < 0:
        raise SystemExit("report sample counts must be nonnegative")
    if args.report_preview_chars < 1:
        raise SystemExit("--report-preview-chars must be positive")
    if args.world_qa_pool_samples_per_world < 0:
        raise SystemExit("--world-qa-pool-samples-per-world must be nonnegative")
    if args.world_qa_max_per_sample < 0:
        raise SystemExit("--world-qa-max-per-sample must be nonnegative")
    if args.start_world < 0:
        raise SystemExit("--start-world must be nonnegative")

    worlds = discover_worlds(args.worlds_dir.resolve(), args.recursive)
    if args.shuffle_worlds:
        random.Random(args.seed).shuffle(worlds)
    if args.start_world:
        worlds = worlds[args.start_world:]
    if args.max_worlds is not None:
        worlds = worlds[: args.max_worlds]
    if not worlds:
        raise SystemExit("no StoryWorld scripts found")

    rng = random.Random(args.seed)
    world_seeds = [rng.randrange(2**31) for _ in worlds]
    tasks = set(args.tasks)
    token_counter = TokenCounter(args.tokenizer, args.chars_per_token)
    world_qa_pool: list[dict[str, str]] = []
    world_qa_pool_stats = WorldQAPoolStats(mode=args.world_qa_mode)
    if "world_qa" in tasks and args.world_qa_mode in ("global", "mixed"):
        world_qa_pool, world_qa_pool_stats = collect_world_qa_pool(
            worlds=worlds,
            python=args.python,
            samples_per_world=args.world_qa_pool_samples_per_world,
            seed=args.seed,
            timeout=args.timeout,
            jobs=args.jobs,
        )
        world_qa_pool_stats.mode = args.world_qa_mode
        print(
            "world_qa pool: "
            f"raw={world_qa_pool_stats.raw_items} "
            f"unique={world_qa_pool_stats.unique_items} "
            f"failed_worlds={world_qa_pool_stats.worlds_failed}"
        )
    stats = ExportStats(worlds_seen=len(worlds))
    runs: list[WorldRun] = []
    row_summaries: list[dict[str, Any]] = []
    duplicate_tracker = DuplicateTracker()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)

    def submit_one(index: int, world: Path, seed: int) -> tuple[int, Path, int, list[dict[str, Any]], str | None, float]:
        samples, error, elapsed = run_world(
            args.python,
            world,
            args.samples_per_world,
            seed,
            args.timeout,
        )
        return index, world, seed, samples, error, elapsed

    with args.out.open("w", encoding="utf-8") as out:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            future_map = {
                pool.submit(submit_one, index, world, seed): (index, world, seed)
                for index, (world, seed) in enumerate(zip(worlds, world_seeds))
            }
            for future in concurrent.futures.as_completed(future_map):
                index, world, seed = future_map[future]
                rel = stable_rel(world)
                try:
                    _, _, _, samples, error, elapsed = future.result()
                except Exception as exc:  # pragma: no cover - defensive around workers
                    samples, error, elapsed = [], repr(exc), 0.0

                if error:
                    stats.worlds_failed += 1
                    inc(stats.failure_kinds, failure_kind(error))
                    stats.failures.append({"world": rel, "seed": seed, "error": error})
                    runs.append(WorldRun(index, rel, seed, False, elapsed, error=error))
                    print(f"FAIL {rel}: {error}", file=sys.stderr)
                    if args.fail_fast:
                        raise SystemExit(1)
                    continue

                raw_sample_count = len(samples)
                samples, duplicate_removed, cap_dropped = filter_samples(
                    samples,
                    dedupe_stories=args.dedupe_story_samples,
                    shuffle_samples=args.shuffle_samples,
                    sample_cap_per_world=args.sample_cap_per_world,
                    seed=seed,
                )

                row_count = 0
                row_rng = random.Random(args.seed ^ 0xC0FFEE ^ (index * 1_000_003))
                for sample_index, sample in enumerate(samples):
                    update_duplicate_tracker(
                        duplicate_tracker,
                        world=world,
                        sample_index=sample_index,
                        sample=sample,
                    )
                    rows, diagnostics = rows_for_sample(
                        world=world,
                        sample_index=sample_index,
                        sample=sample,
                        system=args.system,
                        tasks=tasks,
                        prompt_policy=args.prompt_policy,
                        user_format=args.user_format,
                        row_mode=args.row_mode,
                        max_context_tokens=args.max_context_tokens,
                        token_counter=token_counter,
                        world_qa_mode=args.world_qa_mode,
                        world_qa_pool=world_qa_pool,
                        world_qa_max_per_sample=args.world_qa_max_per_sample,
                        rng=row_rng,
                    )
                    update_pack_stats(stats, diagnostics)
                    for row in rows:
                        update_row_stats(stats, row, args.max_context_tokens)
                        row_summaries.append(row_summary(row, args.report_preview_chars))
                        out.write(json.dumps(row, ensure_ascii=False) + "\n")
                        row_count += 1

                stats.worlds_ok += 1
                stats.raw_samples += raw_sample_count
                stats.duplicate_samples_removed += duplicate_removed
                stats.samples_cap_dropped += cap_dropped
                stats.samples += len(samples)
                stats.rows += row_count
                runs.append(
                    WorldRun(
                        index,
                        rel,
                        seed,
                        True,
                        elapsed,
                        samples=len(samples),
                        raw_samples=raw_sample_count,
                        duplicate_samples_removed=duplicate_removed,
                        samples_cap_dropped=cap_dropped,
                        rows=row_count,
                    )
                )
                print(
                    f"OK   {rel}: raw_samples={raw_sample_count} "
                    f"samples={len(samples)} rows={row_count}"
                )

    runs.sort(key=lambda run: run.index)
    if args.manifest:
        manifest = {
            "args": {
                "worlds_dir": str(args.worlds_dir),
                "recursive": args.recursive,
                "shuffle_worlds": args.shuffle_worlds,
                "start_world": args.start_world,
                "samples_per_world": args.samples_per_world,
                "dedupe_story_samples": args.dedupe_story_samples,
                "shuffle_samples": args.shuffle_samples,
                "sample_cap_per_world": args.sample_cap_per_world,
                "seed": args.seed,
                "tasks": sorted(tasks),
                "prompt_policy": args.prompt_policy,
                "user_format": args.user_format,
                "row_mode": args.row_mode,
                "max_context_tokens": args.max_context_tokens,
                "tokenizer": str(args.tokenizer) if args.tokenizer else None,
                "chars_per_token": args.chars_per_token,
                "world_qa_mode": args.world_qa_mode,
                "world_qa_pool_samples_per_world": args.world_qa_pool_samples_per_world,
                "world_qa_max_per_sample": args.world_qa_max_per_sample,
            },
            "stats": {
                **{
                    key: value
                    for key, value in asdict(stats).items()
                    if key
                    not in {
                        "token_counts",
                        "message_counts",
                        "user_turn_counts",
                        "assistant_turn_counts",
                        "followup_counts",
                        "base_token_counts",
                    }
                },
                "elapsed_seconds": time.time() - stats.started_at,
            },
            "token_stats": token_manifest(
                stats.token_counts,
                args.max_context_tokens,
                token_counter,
            ),
            "shape_stats": shape_manifest(stats),
            "task_stats": task_manifest(stats),
            "packing_stats": packing_manifest(stats),
            "duplicate_stats": duplicate_manifest(duplicate_tracker),
            "world_qa_pool_stats": asdict(world_qa_pool_stats),
            "runs": [asdict(run) for run in runs],
        }
        args.manifest.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    if args.report:
        args.report.write_text(
            build_markdown_report(
                args=args,
                stats=stats,
                token_counter=token_counter,
                runs=runs,
                row_summaries=row_summaries,
                duplicate_stats=duplicate_manifest(duplicate_tracker),
                world_qa_pool_stats=world_qa_pool_stats,
            ),
            encoding="utf-8",
        )

    print(
        f"wrote {stats.rows} rows from {stats.samples} samples "
        f"({stats.worlds_ok} worlds ok, {stats.worlds_failed} failed) -> {args.out}"
    )
    return 0 if stats.rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
