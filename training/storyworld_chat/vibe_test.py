#!/usr/bin/env python3
"""Run repeatable qualitative checks against held-out StoryWorld chat rows.

The workflow deliberately separates prompt selection, local checkpoint
generation, API judging, and reporting.  A frozen prompt file can therefore be
reused for every checkpoint without changing the evaluation examples.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.openai_story_quality import (  # noqa: E402
    BASELINE_RATING,
    BASELINE_STORY,
    DEFAULT_MODEL,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_SERVICE_TIER,
    PROMPT_PROTOCOL,
    RATING_KEYS,
    compact_response,
    output_text,
    prompt_cache_key,
    response_input,
    text_format,
    validate_rating,
)


VIBE_PROTOCOL = "storyworld_dev_vibe_v1"
IM_END = "<|im_end|>"


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise SystemExit(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]], mode: str = "w") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode, encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()


def content_hash(messages: list[dict[str, str]]) -> str:
    encoded = json.dumps(messages, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def story_turns(row: dict[str, Any]) -> tuple[list[dict[str, str]], str] | None:
    messages = row.get("messages")
    if not isinstance(messages, list):
        return None
    prompt: list[dict[str, str]] = []
    for message in messages:
        if not isinstance(message, dict):
            return None
        role = message.get("role")
        content = message.get("content")
        if role == "assistant":
            if prompt and isinstance(content, str) and content.strip():
                return prompt, content.strip()
            return None
        if role not in {"system", "user"} or not isinstance(content, str):
            return None
        prompt.append({"role": role, "content": content})
    return None


def sample_prompts(args: argparse.Namespace) -> int:
    if args.count < 1:
        raise SystemExit("--count must be at least 1")
    rng = random.Random(args.seed)
    reservoir: list[tuple[int, dict[str, Any], list[dict[str, str]], str]] = []
    eligible = 0
    with args.dev_jsonl.open(encoding="utf-8") as handle:
        for source_line, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            turns = story_turns(row)
            if turns is None:
                continue
            prompt, reference = turns
            eligible += 1
            item = (source_line, row, prompt, reference)
            if len(reservoir) < args.count:
                reservoir.append(item)
            else:
                replacement = rng.randrange(eligible)
                if replacement < args.count:
                    reservoir[replacement] = item

    if len(reservoir) < args.count:
        raise SystemExit(f"requested {args.count} prompts but found only {eligible}")
    reservoir.sort(key=lambda item: item[0])
    rows = []
    for rank, (source_line, source, prompt, reference) in enumerate(reservoir, 1):
        digest = content_hash(prompt)
        rows.append(
            {
                "protocol": VIBE_PROTOCOL,
                "prompt_id": f"dev-{source_line}-{digest[:12]}",
                "sample_rank": rank,
                "source_line": source_line,
                "seed": args.seed,
                "prompt_messages": prompt,
                "reference_story": reference,
                "metadata": source.get("metadata", {}),
            }
        )
    write_jsonl(args.out, rows)
    print(f"Wrote {args.out}: {len(rows)} prompts from {eligible} eligible dev rows")
    return 0


def parse_model(value: str) -> tuple[str, Path]:
    if "=" in value:
        label, raw_path = value.split("=", 1)
    else:
        raw_path = value
        label = Path(value).name
    if not label.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("model must be LABEL=PATH or PATH")
    return label.strip(), Path(raw_path).expanduser()


def clean_generation(text: str) -> str:
    for marker in (IM_END, "<|endoftext|>", "<|im_start|>", "<|pad|>"):
        text = text.split(marker, 1)[0]
    return text.strip()


def trim_output_ids(output_ids: Any, stop_ids: list[int], pad_id: int | None) -> tuple[Any, bool]:
    """Trim generation padding while retaining the first stop token."""
    values = output_ids.tolist()
    end = len(values)
    stopped = False
    for index, token_id in enumerate(values):
        if token_id in stop_ids:
            end = index + 1
            stopped = True
            break
    if not stopped and pad_id is not None:
        while end and values[end - 1] == pad_id:
            end -= 1
    return output_ids[:end], stopped


def chunks(items: list[Any], size: int) -> Iterable[list[Any]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def generate(args: argparse.Namespace) -> int:
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1")
    if args.max_new_tokens < 1:
        raise SystemExit("--max-new-tokens must be at least 1")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise SystemExit("generate requires torch and transformers") from exc

    prompts = read_jsonl(args.prompts_jsonl)
    if not prompts:
        raise SystemExit("prompt set is empty")
    all_rows: list[dict[str, Any]] = []
    for label, model_path in args.model:
        if not model_path.exists():
            raise SystemExit(f"model does not exist: {model_path}")
        print(f"Loading {label} from {model_path}", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        tokenizer.padding_side = "left"
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        dtype = torch.bfloat16 if args.bf16 and torch.cuda.is_available() else None
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=dtype,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        model.eval()
        context_limit = int(getattr(model.config, "max_position_embeddings", 1024))
        im_end_id = tokenizer.convert_tokens_to_ids(IM_END)
        stop_ids = [tokenizer.eos_token_id]
        if isinstance(im_end_id, int) and im_end_id >= 0:
            stop_ids.append(im_end_id)
        stop_ids = list(dict.fromkeys(token for token in stop_ids if token is not None))

        for batch in chunks(prompts, args.batch_size):
            rendered = [
                tokenizer.apply_chat_template(
                    row["prompt_messages"], tokenize=False, add_generation_prompt=True
                )
                for row in batch
            ]
            encoded = tokenizer(
                rendered,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max(1, context_limit - args.max_new_tokens),
                add_special_tokens=False,
            )
            encoded.pop("token_type_ids", None)
            encoded = {key: value.to(model.device) for key, value in encoded.items()}
            prompt_width = int(encoded["input_ids"].shape[1])
            room = max(1, context_limit - prompt_width)
            started = time.monotonic()
            kwargs: dict[str, Any] = {
                "max_new_tokens": min(args.max_new_tokens, room),
                "eos_token_id": stop_ids,
                "pad_token_id": tokenizer.pad_token_id,
            }
            if args.temperature > 0:
                kwargs.update(
                    do_sample=True,
                    temperature=args.temperature,
                    top_p=args.top_p,
                )
            else:
                kwargs["do_sample"] = False
            with torch.inference_mode():
                generated = model.generate(**encoded, **kwargs)
            elapsed = time.monotonic() - started
            for row, sequence, mask in zip(batch, generated, encoded["attention_mask"]):
                output_ids, ended = trim_output_ids(
                    sequence[prompt_width:], stop_ids, tokenizer.pad_token_id
                )
                raw = tokenizer.decode(output_ids, skip_special_tokens=False)
                story = clean_generation(raw)
                all_rows.append(
                    {
                        **row,
                        "checkpoint": label,
                        "model_path": str(model_path),
                        "generated_story": story,
                        "prompt_tokens": int(mask.sum().item()),
                        "generated_tokens": int(output_ids.numel()),
                        "finish_reason": "stop" if ended else "length",
                        "generation_seconds_per_batch": round(elapsed, 3),
                        "generation": {
                            "max_new_tokens": args.max_new_tokens,
                            "temperature": args.temperature,
                            "top_p": args.top_p,
                        },
                    }
                )
            print(f"{label}: generated {len(all_rows)} total rows", flush=True)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    write_jsonl(args.out, all_rows, mode="a" if args.append else "w")
    print(f"Wrote {args.out}: {len(all_rows)} generations")
    return 0


def make_judge_client(args: argparse.Namespace):
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise SystemExit("judge requires the OpenAI Python SDK") from exc
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"{args.api_key_env} is not set")
    kwargs: dict[str, Any] = {"api_key": api_key, "timeout": args.timeout}
    if args.base_url:
        kwargs["base_url"] = args.base_url
    return AsyncOpenAI(**kwargs)


async def judge_one(
    client: Any, args: argparse.Namespace, item: dict[str, Any], cache_key: str
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        response = await client.with_options(timeout=args.timeout).responses.create(
            model=args.judge_model,
            input=response_input(item["story"]),
            text=text_format(),
            temperature=0.0,
            max_output_tokens=200,
            prompt_cache_key=cache_key,
            prompt_cache_retention="24h",
            service_tier=args.service_tier,
        )
        raw = output_text(response)
        return {
            **item,
            "ok": True,
            "rating": validate_rating(json.loads(raw)),
            "raw_response_text": raw,
            "response": compact_response(response),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except Exception as exc:
        return {
            **item,
            "ok": False,
            "error": str(exc),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }


def judging_items(generations: list[dict[str, Any]], include_references: bool) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen_references: set[str] = set()
    for row in generations:
        prompt_id = str(row.get("prompt_id"))
        if include_references and prompt_id not in seen_references:
            seen_references.add(prompt_id)
            items.append(
                {
                    "protocol": VIBE_PROTOCOL,
                    "quality_protocol": PROMPT_PROTOCOL,
                    "prompt_id": prompt_id,
                    "sample_rank": row.get("sample_rank"),
                    "source_line": row.get("source_line"),
                    "variant": "reference",
                    "story": row.get("reference_story", ""),
                    "prompt_messages": row.get("prompt_messages", []),
                    "metadata": row.get("metadata", {}),
                }
            )
        items.append(
            {
                "protocol": VIBE_PROTOCOL,
                "quality_protocol": PROMPT_PROTOCOL,
                "prompt_id": prompt_id,
                "sample_rank": row.get("sample_rank"),
                "source_line": row.get("source_line"),
                "variant": row.get("checkpoint", "generated"),
                "story": row.get("generated_story", ""),
                "prompt_messages": row.get("prompt_messages", []),
                "metadata": row.get("metadata", {}),
                "generation": row.get("generation", {}),
                "generation_stats": {
                    key: row.get(key)
                    for key in ("prompt_tokens", "generated_tokens", "finish_reason")
                },
            }
        )
    return items


async def judge_async(args: argparse.Namespace) -> int:
    if args.concurrency < 1:
        raise SystemExit("--concurrency must be at least 1")
    generations = read_jsonl(args.generations_jsonl)
    items = judging_items(generations, not args.skip_references)
    client = make_judge_client(args)
    cache_key = prompt_cache_key()
    output_rows: list[dict[str, Any]] = []
    async with client:
        for batch in chunks(items, args.concurrency):
            rows = await asyncio.gather(
                *(judge_one(client, args, item, cache_key) for item in batch)
            )
            output_rows.extend(rows)
            ok = sum(row["ok"] is True for row in output_rows)
            print(f"Judged {len(output_rows)}/{len(items)} ok={ok}", flush=True)
    for row in output_rows:
        row["judge_model"] = args.judge_model
        row["service_tier"] = args.service_tier
        row["baseline_story"] = BASELINE_STORY
        row["baseline_rating"] = BASELINE_RATING
    write_jsonl(args.out, output_rows)
    print(f"Wrote {args.out}: {len(output_rows)} ratings")
    return 0 if any(row["ok"] for row in output_rows) else 1


def word_count(text: Any) -> int:
    return len(re.findall(r"\b\w+\b", text if isinstance(text, str) else ""))


def variant_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [row for row in rows if row.get("ok") and isinstance(row.get("rating"), dict)]
    averages = {
        key: round(sum(row["rating"][key] for row in ok) / len(ok), 3) if ok else None
        for key in RATING_KEYS
    }
    lengths = [word_count(row.get("story")) for row in ok]
    return {
        "rows": len(rows),
        "ok": len(ok),
        "failed": len(rows) - len(ok),
        "averages": averages,
        "mean_words": round(sum(lengths) / len(lengths), 1) if lengths else None,
        "length_finishes": Counter(
            str((row.get("generation_stats") or {}).get("finish_reason"))
            for row in rows
            if row.get("variant") != "reference"
        ),
    }


def markdown_report(rows: list[dict[str, Any]], source: Path) -> tuple[str, dict[str, Any]]:
    by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_prompt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_variant[str(row.get("variant", "unknown"))].append(row)
        by_prompt[str(row.get("prompt_id", "unknown"))].append(row)
    summaries = {variant: variant_summary(items) for variant, items in by_variant.items()}
    order = ["reference"] + sorted(key for key in summaries if key != "reference")
    lines = [
        "# StoryWorld Dev Vibe Test",
        "",
        f"Generated: `{stamp()}`  ",
        f"Ratings: `{source}`  ",
        f"Quality protocol: `{PROMPT_PROTOCOL}` using the fixed baseline story.",
        "",
        "## Summary",
        "",
        "| Variant | Rated | Coherence | Style | Grammar | Storytelling | Overall | Mean words | Length stops |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant in order:
        summary = summaries[variant]
        scores = summary["averages"]
        length_stops = summary["length_finishes"].get("length", 0)
        lines.append(
            f"| {variant} | {summary['ok']}/{summary['rows']} | "
            + " | ".join(
                f"{scores[key]:.3f}" if scores[key] is not None else "-"
                for key in RATING_KEYS
            )
            + f" | {summary['mean_words'] or '-'} | {length_stops} |"
        )
    reference = summaries.get("reference", {}).get("averages", {})
    if reference:
        lines.extend(["", "## Delta From Reference", "", "| Variant | Coherence | Style | Grammar | Storytelling | Overall |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
        for variant in order:
            if variant == "reference":
                continue
            scores = summaries[variant]["averages"]
            lines.append(
                f"| {variant} | "
                + " | ".join(
                    f"{scores[key] - reference[key]:+.3f}"
                    if scores.get(key) is not None and reference.get(key) is not None
                    else "-"
                    for key in RATING_KEYS
                )
                + " |"
            )
    lines.extend(["", "## Samples", ""])
    prompt_groups = sorted(
        by_prompt.values(), key=lambda group: int(group[0].get("sample_rank") or 0)
    )
    for group in prompt_groups:
        first = group[0]
        lines.append(f"### {first.get('sample_rank')}. `{first.get('prompt_id')}`")
        lines.append("")
        for message in first.get("prompt_messages", []):
            lines.extend([f"**{str(message.get('role', '')).title()} prompt**", "", str(message.get("content", "")).strip(), ""])
        for row in sorted(group, key=lambda item: (item.get("variant") != "reference", str(item.get("variant")))):
            rating = row.get("rating")
            score_text = ", ".join(f"{key}={rating[key]}" for key in RATING_KEYS) if rating else f"ERROR: {row.get('error')}"
            lines.extend([f"**{row.get('variant')}**: {score_text}", "", str(row.get("story", "")).strip(), ""])
    summary_json = {
        "created_at": stamp(),
        "protocol": VIBE_PROTOCOL,
        "quality_protocol": PROMPT_PROTOCOL,
        "ratings_path": str(source),
        "variants": summaries,
    }
    return "\n".join(lines).rstrip() + "\n", summary_json


def report(args: argparse.Namespace) -> int:
    rows = read_jsonl(args.ratings_jsonl)
    markdown, summary = markdown_report(rows, args.ratings_jsonl)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown, encoding="utf-8")
    summary_path = args.summary_out or args.out.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=dict) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.out}")
    print(f"Wrote {summary_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    sample_parser = subparsers.add_parser("sample", help="freeze a uniform dev prompt set")
    sample_parser.add_argument("--dev-jsonl", type=Path, required=True)
    sample_parser.add_argument("--count", type=int, default=16)
    sample_parser.add_argument("--seed", type=int, default=20260905)
    sample_parser.add_argument("--out", type=Path, required=True)
    sample_parser.set_defaults(func=sample_prompts)

    generate_parser = subparsers.add_parser("generate", help="generate stories from local checkpoints")
    generate_parser.add_argument("--prompts-jsonl", type=Path, required=True)
    generate_parser.add_argument("--model", type=parse_model, action="append", required=True, metavar="LABEL=PATH")
    generate_parser.add_argument("--batch-size", type=int, default=8)
    generate_parser.add_argument("--max-new-tokens", type=int, default=768)
    generate_parser.add_argument("--temperature", type=float, default=0.0)
    generate_parser.add_argument("--top-p", type=float, default=0.95)
    generate_parser.add_argument("--bf16", action="store_true")
    generate_parser.add_argument("--append", action="store_true")
    generate_parser.add_argument("--out", type=Path, required=True)
    generate_parser.set_defaults(func=generate)

    judge_parser = subparsers.add_parser("judge", help="score references and generations")
    judge_parser.add_argument("--generations-jsonl", type=Path, required=True)
    judge_parser.add_argument("--judge-model", default=DEFAULT_MODEL)
    judge_parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"))
    judge_parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    judge_parser.add_argument("--service-tier", default=DEFAULT_SERVICE_TIER)
    judge_parser.add_argument("--timeout", type=float, default=DEFAULT_REQUEST_TIMEOUT)
    judge_parser.add_argument("--concurrency", type=int, default=16)
    judge_parser.add_argument("--skip-references", action="store_true")
    judge_parser.add_argument("--out", type=Path, required=True)
    judge_parser.set_defaults(async_func=judge_async)

    report_parser = subparsers.add_parser("report", help="render JSON and readable Markdown summaries")
    report_parser.add_argument("--ratings-jsonl", type=Path, required=True)
    report_parser.add_argument("--out", type=Path, required=True)
    report_parser.add_argument("--summary-out", type=Path, default=None)
    report_parser.set_defaults(func=report)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if hasattr(args, "async_func"):
        return asyncio.run(args.async_func(args))
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
