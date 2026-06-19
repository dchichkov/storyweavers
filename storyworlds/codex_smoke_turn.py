#!/usr/bin/env python3
"""Run one tiny Codex SDK turn and print streamed events."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from openai_codex import ApprovalMode, AsyncCodex, CodexConfig, Sandbox
from openai_codex.generated.v2_all import (
    AgentMessageThreadItem,
    ItemCompletedNotification,
    TurnCompletedNotification,
)


ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-test one streamed SDK turn.")
    parser.add_argument(
        "--prompt",
        default="Reply with exactly this text and nothing else: SDK_SMOKE_OK",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        default=None,
        help="read the prompt from a text file instead of --prompt",
    )
    parser.add_argument(
        "--final-only",
        action="store_true",
        help="print only the final assistant response",
    )
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument(
        "--sqlite-home",
        type=Path,
        default=Path("/private/tmp/storyweavers-codex-smoke/sqlite"),
    )
    return parser


async def main_async() -> int:
    args = build_parser().parse_args()
    prompt = args.prompt
    if args.prompt_file is not None:
        prompt = args.prompt_file.read_text()
    sqlite_home = args.sqlite_home.expanduser().resolve()
    sqlite_home.mkdir(parents=True, exist_ok=True)

    config = CodexConfig(
        config_overrides=(f"sqlite_home={json.dumps(str(sqlite_home))}",)
    )
    async with AsyncCodex(config) as codex:
        thread = await codex.thread_start(
            model=args.model,
            cwd=str(ROOT),
            sandbox=Sandbox.read_only,
            approval_mode=ApprovalMode.deny_all,
            ephemeral=True,
        )
        if not args.final_only:
            print(f"thread {thread.id}", flush=True)
        turn = await thread.turn(
            prompt,
            model=args.model,
            cwd=str(ROOT),
            sandbox=Sandbox.read_only,
            approval_mode=ApprovalMode.deny_all,
        )
        if not args.final_only:
            print(f"turn {turn.id}", flush=True)

        final = None
        async for event in turn.stream():
            payload = event.payload
            if isinstance(payload, ItemCompletedNotification) and payload.turn_id == turn.id:
                item = getattr(payload.item, "root", payload.item)
                phase = getattr(getattr(item, "phase", None), "value", None)
                if not args.final_only:
                    print(f"item {item.__class__.__name__} {phase or ''}".rstrip(), flush=True)
                if isinstance(item, AgentMessageThreadItem):
                    final = item.text
            if isinstance(payload, TurnCompletedNotification) and payload.turn.id == turn.id:
                status = getattr(payload.turn.status, "value", payload.turn.status)
                if not args.final_only:
                    print(f"status {status}", flush=True)

    if args.final_only:
        print(final or "", flush=True)
    else:
        print(f"final {final}", flush=True)
    return 0


def main() -> int:
    try:
        return asyncio.run(main_async())
    except Exception as exc:
        print(f"error {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
