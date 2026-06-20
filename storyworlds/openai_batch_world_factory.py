#!/usr/bin/env python3
"""Prepare and submit OpenAI Batch API jobs for storyworld generation.

The Batch API cannot edit this checkout directly. Each request asks the model to
return one JSON object containing the target path and complete Python source; a
separate materialization/review pass can then write and verify the generated
files.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STORYWORLDS_DIR = Path(__file__).resolve().parent
WORLDS_DIR = STORYWORLDS_DIR / "worlds"
STORY_CONTRACT_PATH = STORYWORLDS_DIR / "STORY.md"
TODO_PATH = STORYWORLDS_DIR / "TODO.md"
BATCH_DIR = STORYWORLDS_DIR / "batches"
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_ENDPOINT = "/v1/responses"
SLUG_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(slots=True)
class StoryworldJob:
    custom_id: str
    name: str
    target: str
    seed: int
    words: list[str]
    setting: str
    features: list[str]
    style: str
    seed_text: str
    domain: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, submit, inspect, and download storyworld Batch API jobs."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_generation_args(ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "-n",
            "--count",
            type=int,
            default=10,
            help="number of storyworld requests to prepare; default: 10",
        )
        ap.add_argument(
            "--seed",
            type=int,
            default=None,
            help="base seed for deterministic story seeds; default: fresh random seed",
        )
        ap.add_argument(
            "--words-per-seed",
            type=int,
            default=None,
            help="words per generated seed; default: random 1-3 per job",
        )
        ap.add_argument(
            "--features-per-seed",
            type=int,
            default=None,
            help="features per generated seed; default: random 1-3 per job",
        )
        ap.add_argument(
            "--model",
            default=DEFAULT_MODEL,
            help=f"model for every request body; default: {DEFAULT_MODEL}",
        )
        ap.add_argument(
            "--max-output-tokens",
            type=int,
            default=14000,
            help="max output tokens per storyworld response; default: 14000",
        )
        ap.add_argument(
            "--endpoint",
            default=DEFAULT_ENDPOINT,
            choices=(DEFAULT_ENDPOINT,),
            help=f"Batch endpoint; default: {DEFAULT_ENDPOINT}",
        )
        ap.add_argument(
            "--completion-window",
            default="24h",
            choices=("24h",),
            help="Batch completion window; currently OpenAI supports 24h",
        )
        ap.add_argument(
            "--metadata-tag",
            default="storyworld_factory",
            help="short metadata tag attached to submitted batches",
        )
        ap.add_argument(
            "--output-dir",
            type=Path,
            default=BATCH_DIR,
            help="where to write JSONL and manifest files",
        )
        ap.add_argument(
            "--full-instructions",
            action="store_true",
            help="inline storyworlds/TODO.md along with STORY.md",
        )
        ap.add_argument(
            "--dry-run",
            action="store_true",
            help="print the first request and do not write/upload files",
        )

    prepare = sub.add_parser("prepare", help="write a Batch JSONL file and manifest")
    add_generation_args(prepare)

    submit = sub.add_parser("submit", help="write, upload, and create a Batch job")
    add_generation_args(submit)

    status = sub.add_parser("status", help="retrieve a Batch job")
    status.add_argument("batch_id", help="Batch id, e.g. batch_...")

    download = sub.add_parser("download", help="download a Batch output or error file")
    download.add_argument("batch_id", help="Batch id, e.g. batch_...")
    download.add_argument(
        "--kind",
        choices=("output", "error"),
        default="output",
        help="which batch file to download; default: output",
    )
    download.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output path; default: storyworlds/batches/<batch_id>.<kind>.jsonl",
    )
    return parser


def require_openai_client():
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit(
            "The OpenAI Python SDK is not importable. Install it in ./.venv, "
            "then rerun submit/status/download."
        ) from exc
    return OpenAI()


def read_prompt_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def slugify(parts: list[str], *, max_parts: int = 7) -> str:
    words: list[str] = []
    for part in parts:
        words.extend(SLUG_WORD_RE.findall(part.lower()))
    slug = "_".join(words[:max_parts]).strip("_")
    if not slug:
        slug = "storyworld"
    if not slug[0].isalpha():
        slug = f"world_{slug}"
    return slug


def unique_slug(base: str, used: set[str]) -> str:
    candidate = base
    index = 2
    while candidate in used or (WORLDS_DIR / f"{candidate}.py").exists():
        candidate = f"{base}_{index}"
        index += 1
    used.add(candidate)
    return candidate


def generated_domain(seed_obj: Any) -> str:
    words = ", ".join(seed_obj.words)
    features = ", ".join(seed_obj.features)
    setting = getattr(seed_obj, "setting", "")
    setting_text = f" Set it in {setting}." if setting else ""
    return (
        "Build a small simulated story domain from this generated seed. "
        f"Include {words}; use {features}; keep the style close to {seed_obj.style}."
        f"{setting_text}"
    )


def validate_generation_args(args: argparse.Namespace) -> None:
    if args.count < 1:
        raise SystemExit("--count must be at least 1")
    if args.words_per_seed is not None and args.words_per_seed < 1:
        raise SystemExit("--words-per-seed must be at least 1")
    if args.features_per_seed is not None and args.features_per_seed < 1:
        raise SystemExit("--features-per-seed must be at least 1")
    if args.max_output_tokens < 1000:
        raise SystemExit("--max-output-tokens should be at least 1000")


def make_jobs(args: argparse.Namespace) -> tuple[int, list[StoryworldJob]]:
    sys.path.insert(0, str(STORYWORLDS_DIR))
    import seed as seed_module

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    used = {path.stem for path in WORLDS_DIR.glob("*.py")}
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
        )
        jobs.append(
            StoryworldJob(
                custom_id=f"storyworld:{index + 1:05d}:{name}",
                name=name,
                target=f"storyworlds/worlds/{name}.py",
                seed=job_seed,
                words=list(seed_obj.words),
                setting=seed_obj.setting,
                features=list(seed_obj.features),
                style=seed_obj.style,
                seed_text=seed_obj.render(),
                domain=generated_domain(seed_obj),
            )
        )
    return base_seed, jobs


def build_storyworld_prompt(job: StoryworldJob, *, full_instructions: bool) -> str:
    story_contract = read_prompt_file(STORY_CONTRACT_PATH)
    todo_block = ""
    if full_instructions:
        todo_block = f"""

Additional cleanup notes from storyworlds/TODO.md:

{read_prompt_file(TODO_PATH)}
"""

    return f"""You are generating one standalone storyworld source file for the Storyweavers repo.
You do not have filesystem access in this batch job. Return exactly one JSON object and no markdown.

JSON object schema:
{{
  "path": "{job.target}",
  "content": "<complete Python source for that file>",
  "checks": ["./.venv/bin/python {job.target} --verify", "./.venv/bin/python {job.target} -n 10 --seed 777 --qa", "./.venv/bin/python {job.target} --json"],
  "quality_risks": ["<short grounded risk, or empty list>"]
}}

Storyworld contract from storyworlds/STORY.md:

{story_contract}
{todo_block}

Seed request:
- Target file: {job.target}
- Domain: {job.domain}
- Seed words: {", ".join(job.words)}
- Setting: {job.setting}
- Features: {", ".join(job.features)}
- Style: {job.style}

Seed prompt:
{job.seed_text}

Implementation requirements:
- Write a complete, valid, stdlib-only Python script.
- Import and use storyworlds/results.py in the same style as existing worlds.
- Include StoryParams, build_parser, resolve_params, generate, emit, -n, --all,
  --seed, --trace, --qa, --json, --asp, --verify, and --show-asp.
- Include a Python valid_combos checker plus an inline ASP twin. --verify must
  exit 0 when run from the repo with ./.venv/bin/python.
- Make random samples read like complete stories: clear premise, state-driven
  turn, and ending image that proves what changed.
- QA must be grounded in simulated state/history, with natural two-or-three
  sentence answers where the trace supports cause/effect.
- Avoid scaffold leaks, raw template fragments, unresolved braces, underscored
  debug ids, doubled articles, and in-story implementation jargon.
- Do not copy an existing world. Create a fresh tiny domain from the seed.
"""


def request_line(
    job: StoryworldJob,
    *,
    model: str,
    endpoint: str,
    max_output_tokens: int,
    full_instructions: bool,
) -> dict[str, Any]:
    return {
        "custom_id": job.custom_id,
        "method": "POST",
        "url": endpoint,
        "body": {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": build_storyworld_prompt(
                                job,
                                full_instructions=full_instructions,
                            ),
                        }
                    ],
                }
            ],
            "max_output_tokens": max_output_tokens,
        },
    }


def now_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def prepare_files(args: argparse.Namespace) -> dict[str, Any]:
    validate_generation_args(args)
    base_seed, jobs = make_jobs(args)
    requests = [
        request_line(
            job,
            model=args.model,
            endpoint=args.endpoint,
            max_output_tokens=args.max_output_tokens,
            full_instructions=args.full_instructions,
        )
        for job in jobs
    ]

    if args.dry_run:
        print(json.dumps(requests[0], indent=2))
        print(f"\n[dry-run] prepared {len(requests)} request(s); base seed {base_seed}")
        return {
            "base_seed": base_seed,
            "jobs": [asdict(job) for job in jobs],
            "requests": requests,
        }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_stamp()
    stem = f"storyworld_batch_{stamp}_seed{base_seed}_n{len(jobs)}"
    jsonl_path = args.output_dir / f"{stem}.jsonl"
    manifest_path = args.output_dir / f"{stem}.manifest.json"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in requests:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "created_at": stamp,
        "base_seed": base_seed,
        "count": len(jobs),
        "model": args.model,
        "endpoint": args.endpoint,
        "completion_window": args.completion_window,
        "max_output_tokens": args.max_output_tokens,
        "full_instructions": args.full_instructions,
        "jsonl_path": str(jsonl_path),
        "manifest_path": str(manifest_path),
        "jobs": [asdict(job) for job in jobs],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def rewrite_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def cmd_prepare(args: argparse.Namespace) -> int:
    manifest = prepare_files(args)
    if args.dry_run:
        return 0
    print(f"Wrote {manifest['jsonl_path']}")
    print(f"Wrote {manifest['manifest_path']}")
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    manifest = prepare_files(args)
    if args.dry_run:
        return 0

    client = require_openai_client()
    jsonl_path = Path(manifest["jsonl_path"])
    print(f"Uploading {jsonl_path} ...", flush=True)
    with jsonl_path.open("rb") as handle:
        uploaded = client.files.create(file=handle, purpose="batch")

    print(f"Creating batch from input file {uploaded.id} ...", flush=True)
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint=manifest["endpoint"],
        completion_window=manifest["completion_window"],
        metadata={
            "tag": args.metadata_tag,
            "base_seed": str(manifest["base_seed"]),
            "count": str(manifest["count"]),
            "model": manifest["model"],
        },
    )

    manifest["openai_file_id"] = uploaded.id
    manifest["batch_id"] = batch.id
    manifest["batch_status"] = batch.status
    rewrite_manifest(Path(manifest["manifest_path"]), manifest)
    print(f"Submitted batch {batch.id} status={batch.status}")
    print(f"Updated {manifest['manifest_path']}")
    return 0


def json_model_dump(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return json.loads(json.dumps(obj, default=lambda item: getattr(item, "__dict__", str(item))))


def cmd_status(args: argparse.Namespace) -> int:
    client = require_openai_client()
    batch = client.batches.retrieve(args.batch_id)
    print(json.dumps(json_model_dump(batch), indent=2, default=str))
    return 0


def write_file_content(file_content: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(file_content, "write_to_file"):
        file_content.write_to_file(path)
        return
    if hasattr(file_content, "content"):
        data = file_content.content
        if isinstance(data, bytes):
            path.write_bytes(data)
            return
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
            return
    if hasattr(file_content, "text"):
        path.write_text(file_content.text, encoding="utf-8")
        return
    if isinstance(file_content, bytes):
        path.write_bytes(file_content)
        return
    path.write_text(str(file_content), encoding="utf-8")


def cmd_download(args: argparse.Namespace) -> int:
    client = require_openai_client()
    batch = client.batches.retrieve(args.batch_id)
    file_id = batch.output_file_id if args.kind == "output" else batch.error_file_id
    if not file_id:
        raise SystemExit(f"Batch {args.batch_id} has no {args.kind}_file_id yet.")

    out = args.out
    if out is None:
        suffix = "errors.jsonl" if args.kind == "error" else "output.jsonl"
        out = BATCH_DIR / f"{args.batch_id}.{suffix}"

    file_content = client.files.content(file_id)
    write_file_content(file_content, out)
    print(f"Wrote {out}")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "prepare":
        return cmd_prepare(args)
    if args.command == "submit":
        return cmd_submit(args)
    if args.command == "status":
        return cmd_status(args)
    if args.command == "download":
        return cmd_download(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
