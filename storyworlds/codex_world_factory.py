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
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORLDS_DIR = Path(__file__).resolve().parent / "worlds"
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(slots=True)
class StreamedTurnResult:
    status: Any
    error: Any
    final_response: str | None
    item_count: int
    usage: Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask Codex SDK to create one storyworld script."
    )
    parser.add_argument(
        "name",
        help="new world slug, e.g. moss_cookie_v2; writes storyworlds/worlds/<name>.py",
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
        help="optional isolated directory for spawned Codex sqlite runtime state",
    )
    parser.add_argument(
        "--isolate-codex-home",
        action="store_true",
        help="also set CODEX_HOME to --codex-home; requires separate auth/config",
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
    target = WORLDS_DIR / f"{name}.py"
    if target.exists():
        raise SystemExit(f"{target.relative_to(ROOT)} already exists")


def bullet(label: str, values: tuple[str, ...] | list[str]) -> str:
    if not values:
        return f"- {label}: choose what best serves the story."
    return f"- {label}: {', '.join(values)}."


def build_prompt(args: argparse.Namespace) -> str:
    target = f"storyworlds/worlds/{args.name}.py"
    domain = args.domain.strip() or "Build a small simulated story domain from the supplied words and features."
    return f"""In {ROOT}, create exactly one file:
{target}

You are not alone in this worktree. Do not revert or touch unrelated files.
Follow storyworlds/AGENTS.md and use storyworlds/worlds/puddles.py and
storyworlds/worlds/pirates.py as the reference shape.

Story request:
- Domain: {domain}
{bullet("Seed words", list(args.words))}
{bullet("Features", list(args.features))}
- Style: {args.style}

Implementation requirements:
- Make a standalone stdlib script that imports storyworlds/results.py.
- Include a StoryParams dataclass, build_parser, resolve_params, generate,
  emit, main, and StorySample output.
- Support -n, --all, --seed, --trace, --qa, --json, --asp, --verify, and
  --show-asp.
- Include a Python reasonableness gate and an inline ASP twin; --verify must
  compare them and exit 0.
- Render complete stories with a beginning, middle turn, and ending payoff.
- Generate grounded QA with full natural-language answers, usually two short
  sentences when cause/effect is available.
- Keep child-facing prose artful and concrete. Avoid trace dumps, internal ids,
  raw meter language, unresolved template fields, doubled articles, and generic
  endings.

Run these checks before finishing:
./.venv/bin/python {target} --verify
./.venv/bin/python {target} -n 10 --seed 777 --qa
./.venv/bin/python {target} --json
git diff --check -- {target}

Final response: list the changed file, the checks you ran, and any remaining
quality risks. Do not make a git commit.
"""


def describe_item(item: Any) -> str:
    root = getattr(item, "root", item)
    kind = root.__class__.__name__
    phase = getattr(root, "phase", None)
    if phase is not None:
        phase = getattr(phase, "value", phase)
        return f"{kind} phase={phase}"
    return kind


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


async def stream_turn(turn: Any) -> StreamedTurnResult:
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
            print(f"[codex] item: {describe_item(payload.item)}", flush=True)
            continue
        if (
            isinstance(payload, ThreadTokenUsageUpdatedNotification)
            and payload.turn_id == turn.id
        ):
            usage = payload.token_usage
            print("[codex] usage updated", flush=True)
            continue
        if isinstance(payload, TurnCompletedNotification) and payload.turn.id == turn.id:
            completed = payload.turn
            status = getattr(completed.status, "value", completed.status)
            print(f"[codex] turn completed: {status}", flush=True)

    if completed is None:
        raise RuntimeError("turn completed event not received")
    return StreamedTurnResult(
        status=completed.status,
        error=completed.error,
        final_response=final_response_from_items(items),
        item_count=len(items),
        usage=usage,
    )


async def run_codex(args: argparse.Namespace, prompt: str) -> int:
    config_env: dict[str, str] | None = None
    config_overrides: tuple[str, ...] = ()
    if args.codex_home is not None:
        codex_home = args.codex_home.expanduser().resolve()
        codex_home.mkdir(parents=True, exist_ok=True)
        sqlite_home = codex_home / "sqlite"
        sqlite_home.mkdir(parents=True, exist_ok=True)
        config_overrides = (f"sqlite_home={json.dumps(str(sqlite_home))}",)
        if args.isolate_codex_home:
            os.environ["CODEX_HOME"] = str(codex_home)
            config_env = {"CODEX_HOME": str(codex_home)}

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
        print(f"[codex] thread: {thread.id}", flush=True)
        turn = await thread.turn(
            prompt,
            model=args.model,
            cwd=str(ROOT),
            sandbox=sandbox,
            approval_mode=approval_mode,
        )
        print(f"[codex] turn: {turn.id}", flush=True)
        try:
            result = await asyncio.wait_for(
                stream_turn(turn),
                timeout=args.timeout_seconds,
            )
        except asyncio.TimeoutError:
            await turn.interrupt()
            raise RuntimeError(
                f"Codex turn timed out after {args.timeout_seconds} seconds"
            )

    if result.final_response:
        print(result.final_response)
    if result.error:
        print(result.error, file=sys.stderr)
        return 1
    status = getattr(result.status, "value", result.status)
    return 0 if status == "completed" else 1


def main() -> int:
    args = build_parser().parse_args()
    validate_name(args.name)
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
