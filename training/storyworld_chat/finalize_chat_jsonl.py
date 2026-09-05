#!/usr/bin/env python3
"""Merge, validate, and globally deduplicate OpenAI chat JSONL shards."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ALLOWED_ROLES = {"system", "user", "assistant"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--max-context-tokens", type=int, default=1024)
    return parser


def validate_row(row: Any, source: Path, line_number: int, max_tokens: int) -> None:
    where = f"{source}:{line_number}"
    if not isinstance(row, dict) or not isinstance(row.get("id"), str):
        raise ValueError(f"{where}: expected an object with a string id")
    messages = row.get("messages")
    if not isinstance(messages, list) or len(messages) < 3:
        raise ValueError(f"{where}: expected at least three messages")
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"{where}: message {index} is not an object")
        if message.get("role") not in ALLOWED_ROLES:
            raise ValueError(f"{where}: invalid role in message {index}")
        if not isinstance(message.get("content"), str) or not message["content"].strip():
            raise ValueError(f"{where}: empty content in message {index}")
    if messages[0]["role"] != "system":
        raise ValueError(f"{where}: first message must be system")
    expected = "user"
    for index, message in enumerate(messages[1:], start=1):
        if message["role"] != expected:
            raise ValueError(f"{where}: expected {expected} at message {index}")
        expected = "assistant" if expected == "user" else "user"
    if messages[-1]["role"] != "assistant":
        raise ValueError(f"{where}: final message must be assistant")
    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"{where}: metadata must be an object")
    tokens = metadata.get("estimated_tokens")
    if not isinstance(tokens, int) or tokens < 1 or tokens > max_tokens:
        raise ValueError(f"{where}: invalid estimated_tokens={tokens!r}")


def percentile(values: list[int], fraction: float) -> int:
    return values[min(len(values) - 1, int((len(values) - 1) * fraction))]


def main() -> int:
    args = build_parser().parse_args()
    inputs = [path.resolve() for path in args.inputs]
    if args.out.resolve() in inputs:
        raise SystemExit("--out must not also be an input")
    if args.max_context_tokens < 1:
        raise SystemExit("--max-context-tokens must be positive")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    temp = args.out.with_name(args.out.name + ".tmp")
    seen_ids: dict[str, str] = {}
    seen_messages: set[str] = set()
    source_rows: Counter[str] = Counter()
    task_rows: Counter[str] = Counter()
    tokens: list[int] = []
    input_rows = 0
    duplicates_removed = 0
    digest = hashlib.sha256()

    try:
        with temp.open("w", encoding="utf-8") as output:
            for source in inputs:
                with source.open("r", encoding="utf-8") as handle:
                    for line_number, line in enumerate(handle, start=1):
                        if not line.strip():
                            continue
                        input_rows += 1
                        row = json.loads(line)
                        validate_row(row, source, line_number, args.max_context_tokens)
                        message_key = json.dumps(
                            row["messages"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
                        )
                        prior = seen_ids.get(row["id"])
                        if prior is not None and prior != message_key:
                            raise ValueError(f"{source}:{line_number}: conflicting duplicate id {row['id']}")
                        seen_ids[row["id"]] = message_key
                        if message_key in seen_messages:
                            duplicates_removed += 1
                            continue
                        seen_messages.add(message_key)
                        rendered = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                        output.write(rendered)
                        digest.update(rendered.encode("utf-8"))
                        source_rows[str(source)] += 1
                        task_rows[str(row["metadata"].get("task", "unknown"))] += 1
                        tokens.append(row["metadata"]["estimated_tokens"])
        temp.replace(args.out)
    except Exception:
        temp.unlink(missing_ok=True)
        raise

    ordered_tokens = sorted(tokens)
    total_tokens = sum(tokens)
    manifest = {
        "inputs": [str(path) for path in inputs],
        "output": str(args.out.resolve()),
        "sha256": digest.hexdigest(),
        "max_context_tokens": args.max_context_tokens,
        "input_rows": input_rows,
        "output_rows": len(tokens),
        "exact_conversation_duplicates_removed": duplicates_removed,
        "unique_ids": len(seen_ids),
        "source_rows": dict(source_rows),
        "task_rows": dict(task_rows),
        "token_stats": {
            "total": total_tokens,
            "mean": round(total_tokens / len(tokens), 2) if tokens else None,
            "min": ordered_tokens[0] if tokens else None,
            "p50": percentile(ordered_tokens, 0.50) if tokens else None,
            "p90": percentile(ordered_tokens, 0.90) if tokens else None,
            "p95": percentile(ordered_tokens, 0.95) if tokens else None,
            "p99": percentile(ordered_tokens, 0.99) if tokens else None,
            "max": ordered_tokens[-1] if tokens else None,
        },
    }
    args.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"wrote {len(tokens)} rows ({total_tokens} tokens); "
        f"removed {duplicates_removed} exact conversation duplicates -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
