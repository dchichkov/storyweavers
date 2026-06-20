#!/usr/bin/env python3
"""Rate generated storyworld stories with an OpenAI-compatible Responses API.

The eval is baseline-calibrated rather than paired to each script's original
TinyStories source: every generated story is rated after the same fixed
TinyStories example and its known score.

Examples:
    OPENAI_API_KEY=... ./.venv/bin/python storyworlds/openai_story_quality.py
    OPENAI_API_KEY=... ./.venv/bin/python storyworlds/openai_story_quality.py \
        --manifest storyworlds/batches/storyworld_batch_20260620T221838Z_seed912640337_n100.manifest.json
    ./.venv/bin/python storyworlds/openai_story_quality.py --dry-run --limit 3
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STORYWORLDS_DIR = Path(__file__).resolve().parent
WORLDS_DIR = STORYWORLDS_DIR / "worlds"
BATCH_DIR = STORYWORLDS_DIR / "batches"

DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_LIMIT = 100
DEFAULT_BATCH_SIZE = 20
DEFAULT_SAMPLE_CONCURRENCY = 8
DEFAULT_SAMPLE_TIMEOUT = 20.0
PROMPT_PROTOCOL = "story_quality_baseline_v1"

SYSTEM_PROMPT = (
    "rate two stories, for [coherence, style, grammar, storytelling, overall] "
    "ratings, please. from 0 to 9, where zero would be an absolute disaster, "
    "and 9 would be a good one. output your results in json, and in the order "
    "above."
)

BASELINE_STORY = (
    "Once upon a time, in a peaceful town, there lived a little boy named Tim. "
    "Tim loved to run and play outside. One day, Tim saw a race in the park. "
    "He was excited and wanted to join the race.  Tim went to his friend, "
    "Sarah, and said, \"Let's start the race!\" Sarah smiled and said, "
    "\"Yes, let's go!\" They lined up with the other kids and waited for the "
    "race to begin. When they heard the word \"Go!\", they started running as "
    "fast as they could.  Tim and Sarah ran with all their speed, laughing and "
    "having fun. They could feel the wind in their hair as they raced to the "
    "finish line. In the end, Tim won the race and Sarah came in second. They "
    "were both so happy and proud of themselves. They celebrated with their "
    "friends and had a great day at the park."
)

BASELINE_RATING = {
    "coherence": 7,
    "style": 6,
    "grammar": 7,
    "storytelling": 7,
    "overall": 7,
}

RATING_KEYS = ("coherence", "style", "grammar", "storytelling", "overall")


@dataclass(slots=True)
class StoryInput:
    index: int
    script: str
    seed: int
    story: str


@dataclass(slots=True)
class SampleFailure:
    index: int
    script: str
    seed: int
    error: str
    stderr: str = ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rate generated storyworld stories with the Responses API."
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        help=f"Responses model; default: OPENAI_MODEL or {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL"),
        help="optional OpenAI-compatible base URL; defaults to OpenAI",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="environment variable containing the API key; default: OPENAI_API_KEY",
    )
    parser.add_argument(
        "--worlds-dir",
        type=Path,
        default=WORLDS_DIR,
        help="directory to discover scripts from; default: storyworlds/worlds",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="optional storyworld batch manifest; uses its job targets in order",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"maximum successful input stories to rate; default: {DEFAULT_LIMIT}",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"number of concurrent Responses calls per chunk; default: {DEFAULT_BATCH_SIZE}",
    )
    parser.add_argument(
        "--sample-concurrency",
        type=int,
        default=DEFAULT_SAMPLE_CONCURRENCY,
        help=f"concurrent script samples while collecting inputs; default: {DEFAULT_SAMPLE_CONCURRENCY}",
    )
    parser.add_argument(
        "--sample-timeout",
        type=float,
        default=DEFAULT_SAMPLE_TIMEOUT,
        help=f"seconds allowed per script sample; default: {DEFAULT_SAMPLE_TIMEOUT:g}",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=777,
        help="base sample seed; each script receives base seed + index; default: 777",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output JSONL path; default: storyworlds/batches/story_quality_<timestamp>.jsonl",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=None,
        help="summary JSON path; default: <out stem>.summary.json",
    )
    parser.add_argument(
        "--aggregate",
        type=Path,
        default=None,
        help="summarize an existing story-quality JSONL file without calling OpenAI",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="number of lowest/highest examples to include in summaries; default: 5",
    )
    parser.add_argument(
        "--prompt-cache-key",
        default=None,
        help="override the shared prompt_cache_key",
    )
    parser.add_argument(
        "--prompt-cache-retention",
        choices=("in_memory", "24h"),
        default="24h",
        help="Responses prompt cache retention; default: 24h",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=200,
        help="max output tokens per rating response; default: 200",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="sampling temperature for ratings; default: 0",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to run storyworld scripts; default: current Python",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="collect input stories and print a preview without calling OpenAI",
    )
    return parser


def now_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def default_output_path() -> Path:
    return BATCH_DIR / f"story_quality_{now_stamp()}.jsonl"


def default_summary_path(output_path: Path) -> Path:
    if output_path.suffix == ".jsonl":
        return output_path.with_suffix(".summary.json")
    return output_path.with_name(f"{output_path.name}.summary.json")


def prompt_cache_key() -> str:
    digest = hashlib.sha256()
    for part in (
        PROMPT_PROTOCOL,
        SYSTEM_PROMPT,
        BASELINE_STORY,
        json.dumps(BASELINE_RATING, separators=(",", ":")),
        json.dumps(rating_schema(), sort_keys=True, separators=(",", ":")),
    ):
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return f"story_quality:{digest.hexdigest()[:16]}"


def rating_schema() -> dict[str, Any]:
    score_schema = {"type": "integer", "enum": list(range(10))}
    return {
        "type": "object",
        "properties": {key: score_schema for key in RATING_KEYS},
        "required": list(RATING_KEYS),
        "additionalProperties": False,
    }


def text_format() -> dict[str, Any]:
    return {
        "format": {
            "type": "json_schema",
            "name": "story_quality_rating",
            "strict": True,
            "schema": rating_schema(),
        },
        "verbosity": "low",
    }


def response_input(story: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": BASELINE_STORY},
        {
            "role": "assistant",
            "content": json.dumps(BASELINE_RATING, separators=(",", ":")),
        },
        {"role": "user", "content": story},
    ]


def discover_scripts(worlds_dir: Path) -> list[Path]:
    base = worlds_dir.resolve()
    return sorted(
        path
        for path in base.rglob("*.py")
        if not path.name.startswith("_") and "__pycache__" not in path.parts
    )


def manifest_scripts(manifest_path: Path) -> list[Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scripts: list[Path] = []
    seen: set[Path] = set()
    for job in manifest.get("jobs", []):
        target = job.get("target")
        if not isinstance(target, str):
            continue
        path = (ROOT / target).resolve()
        try:
            path.relative_to(WORLDS_DIR.resolve())
        except ValueError:
            continue
        if path.suffix == ".py" and path.exists() and path not in seen:
            scripts.append(path)
            seen.add(path)
    return scripts


def sample_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    parts = [str(STORYWORLDS_DIR)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


async def sample_script(
    python: str,
    script: Path,
    index: int,
    seed: int,
    timeout: float,
    env: dict[str, str],
) -> StoryInput | SampleFailure:
    rel = script.relative_to(ROOT).as_posix() if script.is_relative_to(ROOT) else str(script)
    cmd = [python, str(script), "--json", "--seed", str(seed)]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=ROOT,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        return SampleFailure(index=index, script=rel, seed=seed, error="timeout")
    except OSError as exc:
        return SampleFailure(index=index, script=rel, seed=seed, error=str(exc))

    stdout = stdout_b.decode("utf-8", errors="replace")
    stderr = stderr_b.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        first = stderr.splitlines()[0] if stderr.strip() else f"returncode={proc.returncode}"
        return SampleFailure(index=index, script=rel, seed=seed, error=first, stderr=stderr)

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return SampleFailure(index=index, script=rel, seed=seed, error=f"invalid_json:{exc}")

    story = payload.get("story")
    if not isinstance(story, str) or not story.strip():
        return SampleFailure(index=index, script=rel, seed=seed, error="missing_story")

    return StoryInput(index=index, script=rel, seed=seed, story=story.strip())


async def collect_inputs(args: argparse.Namespace, scripts: list[Path]) -> tuple[list[StoryInput], list[SampleFailure]]:
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if args.sample_concurrency < 1:
        raise SystemExit("--sample-concurrency must be at least 1")

    env = sample_env()
    inputs: list[StoryInput] = []
    failures: list[SampleFailure] = []
    next_index = 0

    while next_index < len(scripts) and len(inputs) < args.limit:
        chunk = scripts[next_index : next_index + args.sample_concurrency]
        tasks = [
            sample_script(
                args.python,
                script,
                next_index + offset + 1,
                args.seed + next_index + offset,
                args.sample_timeout,
                env,
            )
            for offset, script in enumerate(chunk)
        ]
        for result in await asyncio.gather(*tasks):
            if isinstance(result, StoryInput):
                if len(inputs) < args.limit:
                    inputs.append(result)
            else:
                failures.append(result)
        next_index += len(chunk)

    return inputs, failures


def make_client(args: argparse.Namespace):
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise SystemExit(
            "The OpenAI Python SDK is not importable. Install it in ./.venv first."
        ) from exc

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"{args.api_key_env} is not set.")
    kwargs: dict[str, Any] = {"api_key": api_key}
    if args.base_url:
        kwargs["base_url"] = args.base_url
    return AsyncOpenAI(**kwargs)


def output_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    data = response.model_dump() if hasattr(response, "model_dump") else response
    chunks: list[str] = []
    for item in data.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                chunks.append(content.get("text", ""))
    return "\n".join(chunks).strip()


def compact_response(response: Any) -> dict[str, Any]:
    data = response.model_dump() if hasattr(response, "model_dump") else response
    return {
        "id": data.get("id"),
        "model": data.get("model"),
        "status": data.get("status"),
        "usage": data.get("usage"),
    }


def validate_rating(payload: Any) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise ValueError("rating is not a JSON object")
    rating: dict[str, int] = {}
    for key in RATING_KEYS:
        value = payload.get(key)
        if not isinstance(value, int) or not 0 <= value <= 9:
            raise ValueError(f"{key} must be an integer from 0 to 9")
        rating[key] = value
    return rating


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if isinstance(row, dict):
                rows.append(row)
    return rows


def usage_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "total_tokens": 0,
    }
    for row in rows:
        usage = (row.get("response") or {}).get("usage") or {}
        if not isinstance(usage, dict):
            continue
        totals["input_tokens"] += int(usage.get("input_tokens") or 0)
        totals["output_tokens"] += int(usage.get("output_tokens") or 0)
        totals["total_tokens"] += int(usage.get("total_tokens") or 0)
        input_details = usage.get("input_tokens_details") or {}
        output_details = usage.get("output_tokens_details") or {}
        if isinstance(input_details, dict):
            totals["cached_input_tokens"] += int(input_details.get("cached_tokens") or 0)
        if isinstance(output_details, dict):
            totals["reasoning_tokens"] += int(output_details.get("reasoning_tokens") or 0)
    return totals


def compact_example(row: dict[str, Any]) -> dict[str, Any]:
    story = row.get("story")
    excerpt = story if isinstance(story, str) else ""
    excerpt = " ".join(excerpt.split())
    if len(excerpt) > 240:
        excerpt = excerpt[:237].rstrip() + "..."
    return {
        "script": row.get("script"),
        "seed": row.get("seed"),
        "rating": row.get("rating"),
        "story_excerpt": excerpt,
    }


def aggregate_rows(rows: list[dict[str, Any]], *, top_n: int = 5) -> dict[str, Any]:
    ok_rows = [
        row for row in rows
        if row.get("ok") is True and isinstance(row.get("rating"), dict)
    ]
    failed_rows = [row for row in rows if row.get("ok") is not True]

    averages: dict[str, float | None] = {}
    mins: dict[str, int | None] = {}
    maxes: dict[str, int | None] = {}
    histograms: dict[str, dict[str, int]] = {}
    baseline_deltas: dict[str, float | None] = {}
    for key in RATING_KEYS:
        values = [
            row["rating"][key]
            for row in ok_rows
            if isinstance(row["rating"].get(key), int)
        ]
        if values:
            averages[key] = round(sum(values) / len(values), 3)
            mins[key] = min(values)
            maxes[key] = max(values)
            hist = Counter(values)
            histograms[key] = {str(score): hist.get(score, 0) for score in range(10)}
            baseline_deltas[key] = round(averages[key] - BASELINE_RATING[key], 3)
        else:
            averages[key] = None
            mins[key] = None
            maxes[key] = None
            histograms[key] = {str(score): 0 for score in range(10)}
            baseline_deltas[key] = None

    def sort_key(row: dict[str, Any]) -> tuple[int, int, int, str]:
        rating = row.get("rating") or {}
        return (
            int(rating.get("overall") or 0),
            int(rating.get("storytelling") or 0),
            int(rating.get("grammar") or 0),
            str(row.get("script") or ""),
        )

    lowest = sorted(ok_rows, key=sort_key)[: max(0, top_n)]
    highest = sorted(ok_rows, key=sort_key, reverse=True)[: max(0, top_n)]
    errors = Counter(str(row.get("error") or "unknown_error") for row in failed_rows)

    return {
        "created_at": now_stamp(),
        "rows": len(rows),
        "ok": len(ok_rows),
        "failed": len(failed_rows),
        "baseline_rating": BASELINE_RATING,
        "averages": averages,
        "baseline_deltas": baseline_deltas,
        "mins": mins,
        "maxes": maxes,
        "histograms": histograms,
        "lowest_overall": [compact_example(row) for row in lowest],
        "highest_overall": [compact_example(row) for row in highest],
        "error_counts": dict(errors.most_common()),
        "usage": usage_summary(rows),
    }


def write_summary(summary: dict[str, Any], path: Path | None) -> None:
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    print(text)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {path}")


def summarize_file(path: Path, summary_out: Path | None, *, top_n: int) -> int:
    rows = load_jsonl(path)
    out_path = summary_out or default_summary_path(path)
    summary = aggregate_rows(rows, top_n=top_n)
    summary["input_path"] = str(path)
    write_summary(summary, out_path)
    return 0 if summary["ok"] else 1


async def rate_story(client: Any, args: argparse.Namespace, item: StoryInput, cache_key: str) -> dict[str, Any]:
    started = time.monotonic()
    try:
        response = await client.responses.create(
            model=args.model,
            input=response_input(item.story),
            text=text_format(),
            temperature=args.temperature,
            max_output_tokens=args.max_output_tokens,
            prompt_cache_key=cache_key,
            prompt_cache_retention=args.prompt_cache_retention,
        )
        elapsed = time.monotonic() - started
        raw_text = output_text(response)
        rating = validate_rating(json.loads(raw_text))
        return {
            "ok": True,
            "index": item.index,
            "script": item.script,
            "seed": item.seed,
            "story": item.story,
            "baseline_story": BASELINE_STORY,
            "baseline_rating": BASELINE_RATING,
            "rating": rating,
            "raw_response_text": raw_text,
            "response": compact_response(response),
            "elapsed_seconds": round(elapsed, 3),
        }
    except Exception as exc:
        elapsed = time.monotonic() - started
        return {
            "ok": False,
            "index": item.index,
            "script": item.script,
            "seed": item.seed,
            "story": item.story,
            "baseline_rating": BASELINE_RATING,
            "error": str(exc),
            "elapsed_seconds": round(elapsed, 3),
        }


async def run_ratings(args: argparse.Namespace, inputs: list[StoryInput], out_path: Path) -> int:
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1")

    cache_key = args.prompt_cache_key or prompt_cache_key()
    client = make_client(args)
    ok = failed = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)

    async with client:
        with out_path.open("w", encoding="utf-8") as handle:
            for start in range(0, len(inputs), args.batch_size):
                batch = inputs[start : start + args.batch_size]
                tasks = [rate_story(client, args, item, cache_key) for item in batch]
                for row in await asyncio.gather(*tasks):
                    if row["ok"]:
                        ok += 1
                    else:
                        failed += 1
                    row["model"] = args.model
                    row["prompt_cache_key"] = cache_key
                    row["prompt_cache_retention"] = args.prompt_cache_retention
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    handle.flush()
                print(
                    f"rated {min(start + len(batch), len(inputs))}/{len(inputs)} "
                    f"ok={ok} failed={failed}",
                    flush=True,
                )

    print(f"Wrote {out_path} ok={ok} failed={failed}")
    return 0 if ok else 1


def print_dry_run(inputs: list[StoryInput], failures: list[SampleFailure], args: argparse.Namespace) -> None:
    print(
        json.dumps(
            {
                "dry_run": True,
                "model": args.model,
                "input_count": len(inputs),
                "sample_failure_count": len(failures),
                "batch_size": args.batch_size,
                "prompt_cache_key": args.prompt_cache_key or prompt_cache_key(),
                "prompt_cache_retention": args.prompt_cache_retention,
                "first_input": None if not inputs else {
                    "script": inputs[0].script,
                    "seed": inputs[0].seed,
                    "story": inputs[0].story,
                    "messages": response_input(inputs[0].story),
                },
                "first_failures": [
                    {
                        "script": failure.script,
                        "seed": failure.seed,
                        "error": failure.error,
                    }
                    for failure in failures[:5]
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


async def async_main(args: argparse.Namespace) -> int:
    if args.top_n < 0:
        raise SystemExit("--top-n must be non-negative")
    if args.aggregate is not None:
        return summarize_file(args.aggregate, args.summary_out, top_n=args.top_n)

    scripts = manifest_scripts(args.manifest) if args.manifest else discover_scripts(args.worlds_dir)
    if not scripts:
        raise SystemExit("no storyworld scripts found")

    rng = random.Random(args.seed)
    if args.manifest is None:
        scripts = list(scripts)
        rng.shuffle(scripts)

    inputs, failures = await collect_inputs(args, scripts)
    print(
        f"collected {len(inputs)} input stories from {len(scripts)} scripts "
        f"(sample failures={len(failures)})",
        flush=True,
    )
    if not inputs:
        for failure in failures[:10]:
            print(f"sample failed: {failure.script}: {failure.error}", file=sys.stderr)
        return 1

    if args.dry_run:
        print_dry_run(inputs, failures, args)
        return 0

    out_path = args.out or default_output_path()
    status = await run_ratings(args, inputs, out_path)
    summarize_file(out_path, args.summary_out, top_n=args.top_n)
    return status


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
