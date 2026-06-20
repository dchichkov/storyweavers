#!/usr/bin/env python3
"""Launch a one-shot Codex SDK job to create a storyworld script.

Use --dry-run first to inspect the exact prompt:

    ./.venv/bin/python storyworlds/codex_world_factory.py moss_cookie_v2 \
        --words moss cookie --features misunderstanding kindness --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORLDS_DIR = Path(__file__).resolve().parent / "worlds"
STORY_CONTRACT_PATH = Path(__file__).resolve().parent / "STORY.md"
TODO_PATH = Path(__file__).resolve().parent / "TODO.md"
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SLUG_WORD_RE = re.compile(r"[a-z0-9]+")
MODEL_DIR_RE = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(slots=True)
class StreamedTurnResult:
    status: Any
    error: Any
    final_response: str | None
    item_count: int
    usage: Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask Codex SDK to create one or more storyworld scripts."
    )
    parser.add_argument(
        "name",
        nargs="?",
        help=(
            "new world slug, e.g. moss_cookie_v2; writes "
            "storyworlds/worlds/<model>/<name>.py"
        ),
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=None,
        metavar="N",
        help="generate N seeded storyworld jobs and run them asynchronously",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        metavar="N",
        help="maximum concurrent SDK jobs in --batch mode; default: 1",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="base seed for --batch story seeds; default: fresh random seed",
    )
    parser.add_argument(
        "--words-per-seed",
        type=int,
        default=None,
        help="words per generated seed in --batch mode; default: random 1-3",
    )
    parser.add_argument(
        "--features-per-seed",
        type=int,
        default=None,
        help="features per generated seed in --batch mode; default: random 1-3",
    )
    parser.add_argument(
        "--words",
        nargs="*",
        default=(),
        help="seed words or objects the world should include",
    )
    parser.add_argument(
        "--features",
        nargs="*",
        default=(),
        help="story features, genres, or constraints to include",
    )
    parser.add_argument(
        "--domain",
        default="",
        help="free-form description of the story domain",
    )
    parser.add_argument(
        "--style",
        default="TinyStories-style, child-facing, artful but concrete",
        help="prose style guidance",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.4",
        help="Codex model passed to thread_start/run; default: gpt-5.4",
    )
    parser.add_argument(
        "--sandbox",
        choices=("read-only", "workspace-write", "full-access"),
        default="workspace-write",
        help="Codex SDK sandbox mode; default: workspace-write",
    )
    parser.add_argument(
        "--approval-mode",
        choices=("deny_all", "auto_review"),
        default="deny_all",
        help="Codex SDK approval mode; default: deny_all",
    )
    parser.add_argument(
        "--persist-thread",
        action="store_true",
        help="create a non-ephemeral SDK thread",
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=None,
        help=(
            "optional isolated directory for spawned Codex sqlite runtime state; "
            "batch mode creates one child directory per job"
        ),
    )
    parser.add_argument(
        "--isolate-codex-home",
        action="store_true",
        help="also set CODEX_HOME to --codex-home; requires separate auth/config",
    )
    parser.add_argument(
        "--full-instructions",
        action="store_true",
        help=(
            "inline storyworlds/TODO.md cleanup notes along with STORY.md"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the SDK prompt without launching Codex",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=600,
        help="maximum time to wait for the SDK run; default: 600",
    )
    return parser


def validate_name(name: str) -> None:
    if not SLUG_RE.fullmatch(name):
        raise SystemExit(
            "name must be a lowercase Python slug: start with a letter, then "
            "letters, numbers, or underscores"
        )


def model_dir_name(model: str) -> str:
    name = MODEL_DIR_RE.sub("_", model.strip()).strip("._-")
    return name or "model"


def output_worlds_dir(model: str) -> Path:
    return WORLDS_DIR / model_dir_name(model)


def output_world_path(args: argparse.Namespace) -> Path:
    return output_worlds_dir(args.model) / f"{args.name}.py"


def validate_world_path(args: argparse.Namespace) -> None:
    validate_name(args.name)
    target = output_world_path(args)
    if target.exists():
        raise SystemExit(f"{target.relative_to(ROOT)} already exists")


def validate_cli(args: argparse.Namespace) -> None:
    if args.concurrency < 1:
        raise SystemExit("--concurrency must be at least 1")
    if args.batch is None:
        if not args.name:
            raise SystemExit("name is required unless --batch is used")
        validate_world_path(args)
        return
    if args.batch < 1:
        raise SystemExit("--batch must be at least 1")
    if args.name:
        raise SystemExit("positional name is for single-world mode; omit it with --batch")
    if args.isolate_codex_home:
        raise SystemExit("--isolate-codex-home is not supported with --batch")
    if args.words or args.features or args.domain:
        raise SystemExit(
            "--batch seeds itself; use --words-per-seed/--features-per-seed "
            "instead of --words/--features/--domain"
        )


def bullet(label: str, values: tuple[str, ...] | list[str]) -> str:
    if not values:
        return f"- {label}: choose what best serves the story."
    return f"- {label}: {', '.join(values)}."


def read_prompt_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_prompt(args: argparse.Namespace) -> str:
    target = output_world_path(args).relative_to(ROOT).as_posix()
    domain = args.domain.strip() or "Build a small simulated story domain from the supplied words and features."
    seed_text = getattr(args, "seed_text", "")
    seed_block = f"\nSeed prompt:\n{seed_text}\n" if seed_text else ""
    story_contract = read_prompt_file(STORY_CONTRACT_PATH)
    if args.full_instructions:
        todo_notes = read_prompt_file(TODO_PATH)
        guidance = f"""The storyworld contract is inlined below from storyworlds/STORY.md.
Do not spend time opening AGENTS.md or STORY.md; use this embedded contract.

{story_contract}

Additional cleanup notes inlined from storyworlds/TODO.md:

{todo_notes}"""
        implementation_guidance = (
            "Follow the embedded STORY.md contract plus the embedded TODO.md "
            "cleanup notes."
        )
        final_guidance = "the embedded STORY.md/TODO.md guidance"
    else:
        guidance = f"""The storyworld contract is inlined below from storyworlds/STORY.md.
Do not spend time opening AGENTS.md, STORY.md, or TODO.md unless you are blocked.
You may inspect an existing world only if you need an API detail.

{story_contract}"""
        implementation_guidance = "Follow the embedded STORY.md contract exactly."
        final_guidance = "the embedded STORY.md contract"
    return f"""In {ROOT}, create exactly one file:
{target}

You are not alone in this worktree. Do not revert or touch unrelated files.
{guidance}

Story request:
- Domain: {domain}
{bullet("Seed words", list(args.words))}
{bullet("Features", list(args.features))}
- Style: {args.style}
{seed_block}

Implementation requirements:
- Start from the seed by writing a short source tale internally, then implement
  the world model from that tale. Do not copy an existing world file.
- {implementation_guidance}

Run these checks before finishing:
./.venv/bin/python {target} --verify
./.venv/bin/python {target} -n 10 --seed 777 --qa
./.venv/bin/python {target} --json
git diff --check -- {target}

Final response: list the changed file, checks run, remaining quality risks, and
one short note on how the script follows {final_guidance}. Do not make a git commit.
"""


def describe_item(item: Any) -> str:
    root = getattr(item, "root", item)
    kind = root.__class__.__name__
    phase = getattr(root, "phase", None)
    if phase is not None:
        phase = getattr(phase, "value", phase)
        return f"{kind} phase={phase}"
    return kind


def slugify(parts: list[str], *, max_parts: int = 6) -> str:
    words: list[str] = []
    for part in parts:
        words.extend(SLUG_WORD_RE.findall(part.lower()))
    slug = "_".join(words[:max_parts]).strip("_")
    if not slug:
        slug = "storyworld"
    if not slug[0].isalpha():
        slug = f"world_{slug}"
    return slug


def unique_slug(base: str, used: set[str], worlds_dir: Path) -> str:
    candidate = base
    index = 2
    while candidate in used or (worlds_dir / f"{candidate}.py").exists():
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


def make_batch_jobs(args: argparse.Namespace) -> list[argparse.Namespace]:
    import seed as seed_module

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    args.batch_seed = base_seed
    print(f"[batch] base seed: {base_seed}", flush=True)
    worlds_dir = output_worlds_dir(args.model)
    used = {path.stem for path in worlds_dir.glob("*.py")}
    jobs: list[argparse.Namespace] = []
    for index in range(args.batch):
        rng = random.Random(base_seed + index)
        n_words = args.words_per_seed if args.words_per_seed is not None else rng.randint(1, 3)
        n_features = (
            args.features_per_seed
            if args.features_per_seed is not None
            else rng.randint(1, 3)
        )
        seed_obj = seed_module.sample(rng, n_words, n_features)
        slug_base = slugify(
            [
                *seed_obj.words,
                getattr(seed_obj, "setting", ""),
                *seed_obj.features,
                seed_obj.style,
            ],
            max_parts=7,
        )
        job = argparse.Namespace(**vars(args))
        job.name = unique_slug(slug_base, used, worlds_dir)
        job.words = tuple(seed_obj.words)
        job.features = tuple(seed_obj.features)
        job.style = seed_obj.style
        job.domain = generated_domain(seed_obj)
        job.seed_text = seed_obj.render()
        job.job_index = index + 1
        job.job_seed = base_seed + index
        jobs.append(job)
    return jobs


def final_response_from_items(items: list[Any]) -> str | None:
    fallback: str | None = None
    for item in reversed(items):
        root = getattr(item, "root", item)
        text = getattr(root, "text", None)
        if not isinstance(text, str) or not text:
            continue
        phase = getattr(root, "phase", None)
        phase_value = getattr(phase, "value", phase)
        if phase_value == "final_answer":
            return text
        if fallback is None:
            fallback = text
    return fallback


async def stream_turn(turn: Any, label: str = "codex") -> StreamedTurnResult:
    from openai_codex.generated.v2_all import (
        ItemCompletedNotification,
        ThreadTokenUsageUpdatedNotification,
        TurnCompletedNotification,
    )

    completed = None
    items: list[Any] = []
    usage = None
    async for event in turn.stream():
        payload = event.payload
        if isinstance(payload, ItemCompletedNotification) and payload.turn_id == turn.id:
            items.append(payload.item)
            print(f"[{label}] item: {describe_item(payload.item)}", flush=True)
            continue
        if (
            isinstance(payload, ThreadTokenUsageUpdatedNotification)
            and payload.turn_id == turn.id
        ):
            usage = payload.token_usage
            print(f"[{label}] usage updated", flush=True)
            continue
        if isinstance(payload, TurnCompletedNotification) and payload.turn.id == turn.id:
            completed = payload.turn
            status = getattr(completed.status, "value", completed.status)
            print(f"[{label}] turn completed: {status}", flush=True)

    if completed is None:
        raise RuntimeError("turn completed event not received")
    return StreamedTurnResult(
        status=completed.status,
        error=completed.error,
        final_response=final_response_from_items(items),
        item_count=len(items),
        usage=usage,
    )


async def run_codex(
    args: argparse.Namespace,
    prompt: str,
    *,
    label: str = "codex",
    codex_home: Path | None = None,
) -> int:
    config_env: dict[str, str] | None = None
    config_overrides: tuple[str, ...] = ()
    selected_home = codex_home if codex_home is not None else args.codex_home
    if selected_home is not None:
        selected_home = selected_home.expanduser().resolve()
        selected_home.mkdir(parents=True, exist_ok=True)
        sqlite_home = selected_home / "sqlite"
        sqlite_home.mkdir(parents=True, exist_ok=True)
        config_overrides = (f"sqlite_home={json.dumps(str(sqlite_home))}",)
        if args.isolate_codex_home:
            os.environ["CODEX_HOME"] = str(selected_home)
            config_env = {"CODEX_HOME": str(selected_home)}

    try:
        from openai_codex import ApprovalMode, AsyncCodex, CodexConfig, Sandbox
    except ImportError as exc:
        raise SystemExit(
            "openai_codex is not importable. Install it in ./.venv, then rerun."
        ) from exc

    sandbox = Sandbox(args.sandbox)
    approval_mode = ApprovalMode(args.approval_mode)
    async with AsyncCodex(
        CodexConfig(env=config_env, config_overrides=config_overrides)
    ) as codex:
        thread = await codex.thread_start(
            model=args.model,
            cwd=str(ROOT),
            sandbox=sandbox,
            approval_mode=approval_mode,
            ephemeral=not args.persist_thread,
        )
        print(f"[{label}] thread: {thread.id}", flush=True)
        turn = await thread.turn(
            prompt,
            model=args.model,
            cwd=str(ROOT),
            sandbox=sandbox,
            approval_mode=approval_mode,
        )
        print(f"[{label}] turn: {turn.id}", flush=True)
        try:
            result = await asyncio.wait_for(
                stream_turn(turn, label),
                timeout=args.timeout_seconds,
            )
        except asyncio.TimeoutError:
            await turn.interrupt()
            raise RuntimeError(
                f"Codex turn timed out after {args.timeout_seconds} seconds"
            )

    if result.final_response:
        print(f"[{label}] final response:\n{result.final_response}")
    if result.error:
        print(f"[{label}] {result.error}", file=sys.stderr)
        return 1
    status = getattr(result.status, "value", result.status)
    return 0 if status == "completed" else 1


async def run_batch(args: argparse.Namespace, jobs: list[argparse.Namespace]) -> int:
    semaphore = asyncio.Semaphore(args.concurrency)
    failures: list[tuple[str, int]] = []
    batch_home = args.codex_home
    if batch_home is None:
        batch_home = Path("/private/tmp") / f"storyweavers-codex-factory-{args.batch_seed}"

    async def run_job(job: argparse.Namespace) -> tuple[str, int]:
        async with semaphore:
            prompt = build_prompt(job)
            label = f"job {job.job_index}/{len(jobs)} {job.name}"
            job_home = batch_home / job.name
            print(
                f"[batch] starting {job.name} seed={job.job_seed}: "
                f"{', '.join(job.words)}",
                flush=True,
            )
            try:
                code = await run_codex(job, prompt, label=label, codex_home=job_home)
            except Exception as exc:
                print(f"[{label}] error: {exc}", file=sys.stderr, flush=True)
                return job.name, 1
            return job.name, code

    tasks = [asyncio.create_task(run_job(job)) for job in jobs]
    for task in asyncio.as_completed(tasks):
        name, code = await task
        if code:
            failures.append((name, code))
            print(f"[batch] failed {name}: rc={code}", flush=True)
        else:
            print(f"[batch] completed {name}", flush=True)

    if failures:
        print("[batch] failures:", file=sys.stderr)
        for name, code in failures:
            print(f"- {name}: rc={code}", file=sys.stderr)
        return 1
    print(f"[batch] completed all {len(jobs)} jobs", flush=True)
    return 0


def main() -> int:
    args = build_parser().parse_args()
    validate_cli(args)
    if args.batch is not None:
        jobs = make_batch_jobs(args)
        if args.dry_run:
            for job in jobs:
                print(f"===== {job.name} seed={job.job_seed} =====")
                print(build_prompt(job))
            return 0
        try:
            return asyncio.run(run_batch(args, jobs))
        except KeyboardInterrupt:
            print("interrupted", file=sys.stderr)
            return 130
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    prompt = build_prompt(args)
    if args.dry_run:
        print(prompt)
        return 0
    try:
        return asyncio.run(run_codex(args, prompt))
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
