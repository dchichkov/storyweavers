#!/usr/bin/env python3
"""Generate storyworlds with regular async Responses API calls.

This is the non-Batch sibling of openai_batch_world_factory.py. It reuses the
same prompt/tool protocol, but calls the service directly with AsyncOpenAI and
materializes each emitted Python file into this checkout as responses complete.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openai_batch_world_factory import (
    BATCH_DIR,
    DEFAULT_MODEL,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_REASONING_EFFORT,
    DEFAULT_SERVICE_TIER,
    EMIT_TOOL_NAME,
    EMIT_MODES,
    EXAMPLE_WORLD_CHOICES,
    PROMPT_PROTOCOL,
    ROOT,
    STORYWORLDS_DIR,
    WORLDS_DIR,
    StoryworldJob,
    build_storyworld_prompt,
    emit_python_tool,
    extract_python_source,
    generated_domain,
    model_dir_name,
    prompt_cache_key,
    safe_target_path,
    slugify,
    unique_slug,
)


DEFAULT_CONCURRENCY = 5
DEFAULT_MAX_OUTPUT_TOKENS = 32000
DEFAULT_PROMPT_CACHE_RETENTION = "24h"
SERVICE_PROTOCOL = f"{PROMPT_PROTOCOL}_service_async_v1"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate storyworld files with direct async Responses API calls."
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=100,
        help="number of storyworlds to generate; default: 100",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="base seed for deterministic story seeds; default: fresh random seed",
    )
    parser.add_argument(
        "--words-per-seed",
        type=int,
        default=None,
        help="words per generated seed; default: random 1-3 per job",
    )
    parser.add_argument(
        "--features-per-seed",
        type=int,
        default=None,
        help="features per generated seed; default: random 1-3 per job",
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
        "--emit-mode",
        choices=EMIT_MODES,
        default="source",
        help="how the model should emit Python: custom tool or raw source message; default: source",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=DEFAULT_MAX_OUTPUT_TOKENS,
        help=f"max output tokens per storyworld response; default: {DEFAULT_MAX_OUTPUT_TOKENS}",
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=("off", "none", "minimal", "low", "medium", "high", "xhigh"),
        default=DEFAULT_REASONING_EFFORT,
        help=f"Responses API reasoning effort; default: {DEFAULT_REASONING_EFFORT}",
    )
    parser.add_argument(
        "--service-tier",
        default=DEFAULT_SERVICE_TIER,
        help=f"Responses API service_tier; default: {DEFAULT_SERVICE_TIER}",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"concurrent Responses calls; default: {DEFAULT_CONCURRENCY}",
    )
    parser.add_argument(
        "--prompt-cache-retention",
        choices=("in_memory", "24h"),
        default=DEFAULT_PROMPT_CACHE_RETENTION,
        help=f"Responses prompt cache retention; default: {DEFAULT_PROMPT_CACHE_RETENTION}",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=None,
        help=(
            "directory for generated world files; default is a run-specific "
            "storyworlds/worlds/<model>_service_<stamp>_seed<seed>_n<count>"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BATCH_DIR,
        help="where to write manifest and response JSONL; default: storyworlds/batches",
    )
    parser.add_argument(
        "--prompt-addendum",
        type=Path,
        default=None,
        help="optional extra prompt instructions appended to every storyworld request",
    )
    parser.add_argument(
        "--example-worlds",
        choices=EXAMPLE_WORLD_CHOICES,
        default="all",
        help="which bundled example worlds to include in prompts; default: all",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace existing target files",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="write responses even when the response status is incomplete",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the first request preview and do not call OpenAI or write files",
    )
    return parser


def now_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def validate_args(args: argparse.Namespace) -> None:
    if args.count < 1:
        raise SystemExit("--count must be at least 1")
    if args.words_per_seed is not None and args.words_per_seed < 1:
        raise SystemExit("--words-per-seed must be at least 1")
    if args.features_per_seed is not None and args.features_per_seed < 1:
        raise SystemExit("--features-per-seed must be at least 1")
    if args.max_output_tokens < 1000:
        raise SystemExit("--max-output-tokens should be at least 1000")
    if args.concurrency < 1:
        raise SystemExit("--concurrency must be at least 1")


def make_client(args: argparse.Namespace) -> Any:
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise SystemExit(
            "The OpenAI Python SDK is not importable. Install it in ./.venv first."
        ) from exc

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"{args.api_key_env} is not set.")
    kwargs: dict[str, Any] = {"api_key": api_key, "timeout": DEFAULT_REQUEST_TIMEOUT}
    if args.base_url:
        kwargs["base_url"] = args.base_url
    return AsyncOpenAI(**kwargs)


def safe_target_dir(path: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to(WORLDS_DIR.resolve())
    return resolved


def run_dir(model: str, stamp: str, base_seed: int, count: int) -> Path:
    return WORLDS_DIR / f"{model_dir_name(model)}_service_{stamp}_seed{base_seed}_n{count}"


def make_jobs(args: argparse.Namespace, *, stamp: str) -> tuple[int, Path, list[StoryworldJob]]:
    sys.path.insert(0, str(STORYWORLDS_DIR))
    import seed as seed_module

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    target_dir = args.target_dir or run_dir(args.model, stamp, base_seed, args.count)
    if not target_dir.is_absolute():
        target_dir = ROOT / target_dir
    target_dir = safe_target_dir(target_dir)

    used = {path.stem for path in target_dir.glob("*.py")}
    jobs: list[StoryworldJob] = []
    for index in range(args.count):
        job_seed = base_seed + index
        rng = random.Random(job_seed)
        n_words = args.words_per_seed if args.words_per_seed is not None else rng.randint(1, 3)
        n_features = (
            args.features_per_seed
            if args.features_per_seed is not None
            else rng.randint(1, 3)
        )
        seed_obj = seed_module.sample(rng, n_words, n_features)
        name = unique_slug(
            slugify(
                [
                    *seed_obj.words,
                    getattr(seed_obj, "setting", ""),
                    *seed_obj.features,
                    seed_obj.style,
                ]
            ),
            used,
            target_dir,
        )
        target = (target_dir / f"{name}.py").relative_to(ROOT).as_posix()
        jobs.append(
            StoryworldJob(
                custom_id=f"storyworld:{index + 1:05d}:{name}",
                name=name,
                target=target,
                seed=job_seed,
                words=list(seed_obj.words),
                setting=seed_obj.setting,
                features=list(seed_obj.features),
                style=seed_obj.style,
                domain=generated_domain(seed_obj),
            )
        )
    return base_seed, target_dir, jobs


def request_body(args: argparse.Namespace, job: StoryworldJob) -> dict[str, Any]:
    prompt = build_storyworld_prompt(
        job,
        prompt_addendum=args.prompt_addendum,
        example_worlds=args.example_worlds,
        emit_mode=args.emit_mode,
    )
    request = {
        "model": args.model,
        "prompt_cache_key": prompt_cache_key(
            prompt_addendum=args.prompt_addendum,
            example_worlds=args.example_worlds,
            emit_mode=args.emit_mode,
        ),
        "prompt_cache_retention": args.prompt_cache_retention,
        "service_tier": args.service_tier,
        "input": [
            {
                "role": "user",
                "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        }
                ],
            }
        ],
        "max_output_tokens": args.max_output_tokens,
        **(
            {
                "tools": [emit_python_tool()],
                "tool_choice": "required",
                "parallel_tool_calls": False,
            }
            if args.emit_mode == "tool"
            else {}
        ),
    }
    if args.reasoning_effort != "off":
        request["reasoning"] = {"effort": args.reasoning_effort}
    return request


def json_model_dump(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return json.loads(json.dumps(obj, default=lambda item: getattr(item, "__dict__", str(item))))


def response_row(
    *,
    job: StoryworldJob,
    request: dict[str, Any],
    response: Any | None,
    error: str | None,
    elapsed: float,
) -> dict[str, Any]:
    body = json_model_dump(response) if response is not None else None
    return {
        "custom_id": job.custom_id,
        "target": job.target,
        "request": {
            "model": request.get("model"),
            "prompt_cache_key": request.get("prompt_cache_key"),
            "prompt_cache_retention": request.get("prompt_cache_retention"),
            "reasoning": request.get("reasoning"),
            "service_tier": request.get("service_tier"),
            "max_output_tokens": request.get("max_output_tokens"),
        },
        "response": {
            "status_code": 200 if response is not None else None,
            "body": body,
        },
        "error": error,
        "elapsed_seconds": round(elapsed, 3),
    }


def materialize_row(
    row: dict[str, Any],
    *,
    overwrite: bool,
    allow_incomplete: bool,
) -> tuple[bool, str]:
    target = str(row.get("target") or "")
    body = (row.get("response") or {}).get("body") or {}
    status = body.get("status")
    if status != "completed" and not allow_incomplete:
        return False, f"status={status}"

    source, source_kind = extract_python_source(row, target)
    if source is None:
        return False, source_kind

    try:
        path = safe_target_path(target)
    except ValueError as exc:
        return False, str(exc)

    if path.exists() and not overwrite:
        return False, f"exists:{path}"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.rstrip() + "\n", encoding="utf-8")
    return True, f"wrote:{path.relative_to(ROOT).as_posix()}:{source_kind}:{len(source)}"


async def call_one(
    client: Any,
    args: argparse.Namespace,
    job: StoryworldJob,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    request = request_body(args, job)
    started = time.monotonic()
    async with semaphore:
        try:
            response = await client.with_options(timeout=DEFAULT_REQUEST_TIMEOUT).responses.create(**request)
            elapsed = time.monotonic() - started
            return response_row(
                job=job,
                request=request,
                response=response,
                error=None,
                elapsed=elapsed,
            )
        except Exception as exc:
            elapsed = time.monotonic() - started
            return response_row(
                job=job,
                request=request,
                response=None,
                error=str(exc),
                elapsed=elapsed,
            )


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


async def run(args: argparse.Namespace) -> int:
    validate_args(args)
    stamp = now_stamp()
    base_seed, target_dir, jobs = make_jobs(args, stamp=stamp)
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    stem = f"storyworld_service_{stamp}_seed{base_seed}_n{len(jobs)}"
    response_jsonl = output_dir / f"{stem}.responses.jsonl"
    manifest_path = output_dir / f"{stem}.manifest.json"

    manifest: dict[str, Any] = {
        "created_at": stamp,
        "base_seed": base_seed,
        "count": len(jobs),
        "model": args.model,
        "service": "responses",
        "output_protocol": SERVICE_PROTOCOL,
        "emit_mode": args.emit_mode,
        "emit_tool_name": EMIT_TOOL_NAME,
        "max_output_tokens": args.max_output_tokens,
        "reasoning_effort": args.reasoning_effort,
        "service_tier": args.service_tier,
        "concurrency": args.concurrency,
        "prompt_cache_key": prompt_cache_key(
            prompt_addendum=args.prompt_addendum,
            example_worlds=args.example_worlds,
            emit_mode=args.emit_mode,
        ),
        "prompt_cache_retention": args.prompt_cache_retention,
        "prompt_addendum": None if args.prompt_addendum is None else str(args.prompt_addendum),
        "example_worlds": args.example_worlds,
        "target_dir": target_dir.relative_to(ROOT).as_posix(),
        "response_jsonl": response_jsonl.relative_to(ROOT).as_posix(),
        "manifest_path": manifest_path.relative_to(ROOT).as_posix(),
        "jobs": [asdict(job) for job in jobs],
    }

    if args.dry_run:
        preview = {
            "dry_run": True,
            "manifest": manifest,
            "first_request": request_body(args, jobs[0]),
        }
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    write_manifest(manifest_path, manifest)

    client = make_client(args)
    semaphore = asyncio.Semaphore(args.concurrency)
    ok = failed = written = skipped = 0

    async with client:
        with response_jsonl.open("w", encoding="utf-8") as handle:
            tasks = [
                asyncio.create_task(call_one(client, args, job, semaphore))
                for job in jobs
            ]
            for index, task in enumerate(asyncio.as_completed(tasks), 1):
                row = await task
                if row.get("error"):
                    ok_flag = False
                    detail = row["error"]
                    failed += 1
                else:
                    ok_flag, detail = materialize_row(
                        row,
                        overwrite=args.overwrite,
                        allow_incomplete=args.allow_incomplete,
                    )
                    if ok_flag:
                        ok += 1
                        written += 1
                    else:
                        failed += 1
                        skipped += 1
                row["materialized"] = ok_flag
                row["materialize_detail"] = detail
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                status = "ok" if ok_flag else "failed"
                print(
                    f"[{index}/{len(jobs)}] {status} {row.get('target')} {detail}",
                    flush=True,
                )

    manifest["completed_at"] = now_stamp()
    manifest["ok"] = ok
    manifest["failed"] = failed
    manifest["written"] = written
    manifest["skipped"] = skipped
    write_manifest(manifest_path, manifest)

    print(f"Wrote {response_jsonl.relative_to(ROOT).as_posix()}")
    print(f"Wrote {manifest_path.relative_to(ROOT).as_posix()}")
    print(f"Generated {ok}/{len(jobs)} storyworld(s), failed={failed}, skipped={skipped}")
    return 0 if ok == len(jobs) else 1


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
