#!/usr/bin/env python3
"""Export official TinyStories metadata into StoryWorld-compatible chat JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SYSTEM = (
    "You are StoryWorld, a grounded children's-story model. "
    "Write complete, child-facing stories and answers that preserve the given "
    "characters, objects, causes, and outcomes."
)
IM_START = "<|im_start|>"
IM_END = "<|im_end|>"


@dataclass
class SplitState:
    name: str
    target_tokens: int
    output: Path
    budget_tolerance: int
    handle: Any = None
    rows: int = 0
    tokens: int = 0
    assistant_tokens: int = 0
    digest: Any = field(default_factory=hashlib.sha256)
    source_counts: Counter[str] = field(default_factory=Counter)
    token_counts: list[int] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return self.tokens >= self.target_tokens - self.budget_tolerance

    def improves_budget(self, row_tokens: int) -> bool:
        if self.complete:
            return False
        before = abs(self.target_tokens - self.tokens)
        after = abs(self.target_tokens - self.tokens - row_tokens)
        return after < before

    def write(self, row: dict[str, Any], row_tokens: int, assistant_tokens: int) -> None:
        rendered = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        self.handle.write(rendered)
        self.digest.update(rendered.encode("utf-8"))
        self.rows += 1
        self.tokens += row_tokens
        self.assistant_tokens += assistant_tokens
        self.token_counts.append(row_tokens)
        self.source_counts[str(row["metadata"]["source_model"])] += 1


class ExactTokenCounter:
    """Match OpenAIChatJsonlDataset's segmented encoding exactly."""

    def __init__(self, tokenizer_path: Path) -> None:
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise SystemExit("--tokenizer requires transformers") from exc
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    def encode(self, text: str) -> list[int]:
        return self.tokenizer.encode(text, add_special_tokens=False)

    def count_messages(self, messages: list[dict[str, str]]) -> tuple[int, int]:
        total = len(self.encode(self.tokenizer.bos_token or ""))
        assistant = 0
        for message in messages:
            header = len(self.encode(f"{IM_START}{message['role']}\n"))
            content = len(self.encode(message["content"]))
            footer = len(self.encode(f"{IM_END}\n"))
            total += header + content + footer
            if message["role"] == "assistant":
                assistant += content + footer
        return total, assistant


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--train-out", type=Path, required=True)
    parser.add_argument("--dev-out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--train-target-tokens", type=int, default=410_187_389)
    parser.add_argument("--dev-target-tokens", type=int, default=21_694_272)
    parser.add_argument("--max-context-tokens", type=int, default=1024)
    parser.add_argument(
        "--budget-tolerance",
        type=int,
        default=1024,
        help="maximum token undershoot per split; default: one context window",
    )
    parser.add_argument("--seed", type=int, default=20260905)
    parser.add_argument(
        "--source",
        choices=("gpt4", "gpt35", "all"),
        default="gpt4",
        help="source model filter; default: gpt4",
    )
    parser.add_argument("--system", default=DEFAULT_SYSTEM)
    parser.add_argument(
        "--max-source-stories",
        type=int,
        default=None,
        help="stop after this many source records; useful for smoke tests",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="write outputs even when the archive cannot satisfy both budgets",
    )
    return parser


def clean_story(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def clean_instruction(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    text = re.sub(r"\s*Possible story:\s*$", "", text, flags=re.IGNORECASE)
    return text.strip()


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def source_allowed(source: str, mode: str) -> bool:
    normalized = source.casefold().replace(" ", "")
    if mode == "all":
        return normalized in {"gpt-4", "gpt-3.5"}
    if mode == "gpt4":
        return normalized == "gpt-4"
    return normalized == "gpt-3.5"


def source_records(archive: Path) -> Iterable[tuple[str, int, dict[str, Any]]]:
    with tarfile.open(archive, "r|gz") as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith(".json"):
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            values = json.loads(extracted.read().decode("utf-8"))
            if not isinstance(values, list):
                continue
            for index, value in enumerate(values):
                if isinstance(value, dict):
                    yield member.name, index, value


def prompt_and_params(item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    instruction = item.get("instruction")
    if not isinstance(instruction, dict):
        return "", {}
    prompt = clean_instruction(instruction.get("prompt:") or instruction.get("prompt"))
    params = {
        "features": string_list(instruction.get("features")),
        "words": string_list(instruction.get("words")),
    }
    return prompt, params


def make_messages(system: str, prompt: str, params: dict[str, Any], story: str) -> list[dict[str, str]]:
    compact_params = json.dumps(params, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    user = f"Task: write_story\nPrompt: {prompt}\nParams: {compact_params}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
        {"role": "assistant", "content": story},
    ]


def split_for_digest(digest: bytes, dev_fraction: float, seed: int) -> str:
    seeded = hashlib.sha256(seed.to_bytes(8, "big", signed=False) + digest).digest()
    value = int.from_bytes(seeded[:8], "big") / 2**64
    return "dev" if value < dev_fraction else "train"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


def split_manifest(state: SplitState) -> dict[str, Any]:
    return {
        "output": str(state.output.resolve()),
        "sha256": state.digest.hexdigest(),
        "target_tokens": state.target_tokens,
        "actual_tokens": state.tokens,
        "token_delta": state.tokens - state.target_tokens,
        "assistant_tokens": state.assistant_tokens,
        "rows": state.rows,
        "source_models": dict(state.source_counts),
        "token_stats": {
            "mean": round(state.tokens / state.rows, 2) if state.rows else None,
            "min": min(state.token_counts) if state.token_counts else None,
            "p50": percentile(state.token_counts, 0.50),
            "p90": percentile(state.token_counts, 0.90),
            "p99": percentile(state.token_counts, 0.99),
            "max": max(state.token_counts) if state.token_counts else None,
        },
    }


def main() -> int:
    args = build_parser().parse_args()
    if args.train_target_tokens < 1 or args.dev_target_tokens < 1:
        raise SystemExit("token targets must be positive")
    if args.max_context_tokens < 1:
        raise SystemExit("--max-context-tokens must be positive")
    if not 0 <= args.budget_tolerance <= args.max_context_tokens:
        raise SystemExit("--budget-tolerance must be between 0 and max context")
    if not 0 <= args.seed < 2**64:
        raise SystemExit("--seed must fit in an unsigned 64-bit integer")
    if args.train_out.resolve() == args.dev_out.resolve():
        raise SystemExit("--train-out and --dev-out must differ")

    counter = ExactTokenCounter(args.tokenizer)
    train = SplitState(
        "train", args.train_target_tokens, args.train_out, args.budget_tolerance
    )
    dev = SplitState("dev", args.dev_target_tokens, args.dev_out, args.budget_tolerance)
    states = {"train": train, "dev": dev}
    dev_fraction = args.dev_target_tokens / (
        args.train_target_tokens + args.dev_target_tokens
    )
    for state in states.values():
        state.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    temp_paths = {
        name: state.output.with_name(state.output.name + ".tmp")
        for name, state in states.items()
    }

    source_seen = accepted = 0
    skipped: Counter[str] = Counter()
    seen_stories: set[bytes] = set()
    try:
        for name, state in states.items():
            state.handle = temp_paths[name].open("w", encoding="utf-8")
        for member, source_index, item in source_records(args.archive):
            source_seen += 1
            if args.max_source_stories is not None and source_seen > args.max_source_stories:
                break
            source_model = str(item.get("source") or "")
            if not source_allowed(source_model, args.source):
                skipped["source_filter"] += 1
                continue
            story = clean_story(item.get("story"))
            prompt, params = prompt_and_params(item)
            if not story or not prompt:
                skipped["missing_story_or_prompt"] += 1
                continue
            story_digest = hashlib.sha256(story.encode("utf-8")).digest()
            if story_digest in seen_stories:
                skipped["duplicate_story"] += 1
                continue
            seen_stories.add(story_digest)
            split = split_for_digest(story_digest, dev_fraction, args.seed)
            state = states[split]
            if state.complete:
                skipped[f"{split}_complete"] += 1
                if train.complete and dev.complete:
                    break
                continue
            messages = make_messages(args.system, prompt, params, story)
            row_tokens, assistant_tokens = counter.count_messages(messages)
            if row_tokens > args.max_context_tokens:
                skipped["over_context"] += 1
                continue
            if not state.improves_budget(row_tokens):
                skipped[f"{split}_budget_overshoot"] += 1
                continue
            row_id = f"tinystories:{story_digest.hex()[:24]}"
            row = {
                "id": row_id,
                "messages": messages,
                "metadata": {
                    "task": "story",
                    "dataset": "roneneldan/TinyStories",
                    "archive_member": member,
                    "source_index": source_index,
                    "source_model": source_model,
                    "summary": clean_story(item.get("summary")),
                    "params": params,
                    "max_context_tokens": args.max_context_tokens,
                    "estimated_tokens": row_tokens,
                    "assistant_tokens": assistant_tokens,
                },
            }
            state.write(row, row_tokens, assistant_tokens)
            accepted += 1
            if accepted % 10_000 == 0:
                print(
                    f"accepted={accepted} source={source_seen} "
                    f"train={train.rows}/{train.tokens} dev={dev.rows}/{dev.tokens}",
                    flush=True,
                )
            if train.complete and dev.complete:
                break
        for state in states.values():
            state.handle.close()
            state.handle = None

        complete = train.complete and dev.complete
        if not complete and not args.allow_incomplete:
            raise RuntimeError(
                "archive exhausted before satisfying token budgets: "
                f"train={train.tokens}/{train.target_tokens}, "
                f"dev={dev.tokens}/{dev.target_tokens}"
            )
        for name, state in states.items():
            temp_paths[name].replace(state.output)
    except Exception:
        for state in states.values():
            if state.handle is not None:
                state.handle.close()
        for path in temp_paths.values():
            path.unlink(missing_ok=True)
        raise

    manifest = {
        "dataset": "roneneldan/TinyStories",
        "source_archive": str(args.archive.resolve()),
        "source_archive_sha256": file_sha256(args.archive),
        "source_filter": args.source,
        "system": args.system,
        "prompt_format": "Task: write_story\\nPrompt: {original_instruction}\\nParams: {features,words}",
        "tokenizer": str(args.tokenizer.resolve()),
        "max_context_tokens": args.max_context_tokens,
        "budget_tolerance": args.budget_tolerance,
        "split_seed": args.seed,
        "dev_fraction": dev_fraction,
        "source_records_seen": source_seen,
        "unique_stories_seen": len(seen_stories),
        "skipped": dict(skipped),
        "train": split_manifest(train),
        "dev": split_manifest(dev),
    }
    args.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote train={train.rows} rows/{train.tokens} tokens and "
        f"dev={dev.rows} rows/{dev.tokens} tokens; manifest={args.manifest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
