#!/usr/bin/env python3
"""Find duplicate generated story QA pairs and point at static QA source lines."""

from __future__ import annotations

import argparse
import ast
import json
import os
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORLDS_DIR = Path(__file__).resolve().parent / "worlds"


@dataclass
class QAOccurrence:
    path: Path
    sample_index: int
    question: str
    answer: str


@dataclass
class SourceHit:
    path: Path
    line: int
    snippet: str
    question_static: bool
    answer_static: bool
    question_key: str | None = None
    answer_key: str | None = None


@dataclass
class WorldRun:
    path: Path
    seed: int
    samples: int
    stderr: str = ""


@dataclass
class CheckResult:
    runs: list[WorldRun] = field(default_factory=list)
    failures: list[tuple[Path, int, str]] = field(default_factory=list)
    duplicates: dict[tuple[str, str], list[QAOccurrence]] = field(default_factory=dict)
    source_hits: dict[tuple[str, str], list[SourceHit]] = field(default_factory=dict)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def discover_worlds(worlds_dir: Path, include_tmp: bool, recursive: bool) -> list[Path]:
    worlds: list[Path] = []
    paths = worlds_dir.rglob("*.py") if recursive else worlds_dir.glob("*.py")
    for path in paths:
        parts = set(path.parts)
        if path.name.startswith("_") or "__pycache__" in parts:
            continue
        if not include_tmp and "tmp" in parts:
            continue
        worlds.append(path)
    return sorted(worlds)


def select_worlds(worlds: list[Path], count: int, rng: random.Random, allow_repeat: bool) -> list[Path]:
    if count < 1:
        raise SystemExit("count must be at least 1")
    if not worlds:
        raise SystemExit("no storyworld scripts found")
    if allow_repeat:
        return [rng.choice(worlds) for _ in range(count)]
    if count > len(worlds):
        raise SystemExit(
            f"count={count} exceeds available worlds={len(worlds)}; "
            "use --allow-repeat to sample with replacement"
        )
    return rng.sample(worlds, count)


def sample_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    parts = [str(DEFAULT_WORLDS_DIR.parent)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def run_world(python: str, world: Path, seed: int, variants: int, timeout: float) -> subprocess.CompletedProcess[str]:
    cmd = [python, str(world), "-n", str(variants), "--seed", str(seed), "--json"]
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=sample_env(),
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def parse_json_samples(raw: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    samples: list[dict[str, Any]] = []
    pos = 0
    while pos < len(raw):
        while pos < len(raw) and raw[pos].isspace():
            pos += 1
        if pos >= len(raw):
            break
        payload, pos = decoder.raw_decode(raw, pos)
        if isinstance(payload, dict):
            samples.append(payload)
        elif isinstance(payload, list):
            samples.extend(item for item in payload if isinstance(item, dict))
    return samples


def collect_occurrences(result: CheckResult, world: Path, seed: int, samples: list[dict[str, Any]]) -> None:
    result.runs.append(WorldRun(path=world, seed=seed, samples=len(samples)))
    pair_occurrences: dict[tuple[str, str], list[QAOccurrence]] = result.duplicates
    for sample_index, sample in enumerate(samples, 1):
        for item in sample.get("story_qa") or []:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question") or "").strip()
            answer = str(item.get("answer") or "").strip()
            if not question or not answer:
                continue
            key = (normalize(question), normalize(answer))
            pair_occurrences.setdefault(key, []).append(
                QAOccurrence(world, sample_index, question, answer)
            )


def static_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        pieces: list[str] = []
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                return None
            piece = static_string(value)
            if piece is None:
                return None
            pieces.append(piece)
        return "".join(pieces)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = static_string(node.left)
        right = static_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def get_kw(call: ast.Call, name: str) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def qa_nodes_from_call(call: ast.Call) -> tuple[ast.AST | None, ast.AST | None] | None:
    if isinstance(call.func, ast.Name) and call.func.id == "QAItem":
        question = get_kw(call, "question") or (call.args[0] if len(call.args) >= 1 else None)
        answer = get_kw(call, "answer") or (call.args[1] if len(call.args) >= 2 else None)
        return question, answer
    return None


def is_story_qa_scope(node: ast.AST) -> bool:
    parent = getattr(node, "_parent", None)
    while parent is not None:
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent.name == "story_qa"
        parent = getattr(parent, "_parent", None)
    return False


def attach_parents(tree: ast.AST) -> None:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "_parent", parent)


def build_result(args: argparse.Namespace) -> CheckResult:
    rng = random.Random(args.seed)
    worlds_dir = args.worlds_dir.resolve()
    worlds = discover_worlds(worlds_dir, args.include_tmp, args.recursive)
    chosen = select_worlds(worlds, args.count, rng, args.allow_repeat)
    result = CheckResult()

    for world in chosen:
        story_seed = rng.randrange(2**31)
        completed = None
        for attempt in range(3):
            try:
                completed = run_world(args.python, world, story_seed, args.variants, args.timeout)
                break
            except subprocess.TimeoutExpired as exc:
                result.failures.append((world, -1, f"timed out after {args.timeout:g}s"))
                if exc.stderr:
                    result.runs.append(WorldRun(world, story_seed, 0, str(exc.stderr).strip()))
                break
            except OSError as exc:
                if getattr(exc, "errno", None) == 35 and attempt < 2:
                    time.sleep(0.25 * (attempt + 1))
                    continue
                result.failures.append((world, -1, str(exc)))
                break
        if completed is None:
            continue
        if completed.returncode:
            result.failures.append((world, completed.returncode, completed.stderr.strip()))
            continue
        try:
            samples = parse_json_samples(completed.stdout)
        except json.JSONDecodeError as exc:
            result.failures.append((world, completed.returncode, f"invalid JSON: {exc}"))
            continue
        collect_occurrences(result, world, story_seed, samples)

    result.duplicates = {
        key: occs
        for key, occs in result.duplicates.items()
        if len(occs) > 1
    }
    return result


def extract_source_candidates(path: Path) -> list[SourceHit]:
    try:
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return []
    attach_parents(tree)
    lines = source.splitlines()
    out: list[SourceHit] = []
    for node in ast.walk(tree):
        question_node: ast.AST | None = None
        answer_node: ast.AST | None = None
        if isinstance(node, ast.Call):
            pair = qa_nodes_from_call(node)
            if pair is None:
                continue
            question_node, answer_node = pair
        elif isinstance(node, ast.Tuple) and is_story_qa_scope(node) and len(node.elts) >= 2:
            question_node, answer_node = node.elts[0], node.elts[1]
        else:
            continue
        question = static_string(question_node)
        answer = static_string(answer_node)
        if question is None and answer is None:
            continue
        line = getattr(node, "lineno", 1)
        snippet = lines[line - 1].strip() if 0 < line <= len(lines) else ""
        out.append(
            SourceHit(
                path=path,
                line=line,
                snippet=snippet,
                question_static=question is not None,
                answer_static=answer is not None,
                question_key=normalize(question) if question is not None else None,
                answer_key=normalize(answer) if answer is not None else None,
            )
        )
    return out


def attach_source_hits(result: CheckResult) -> None:
    duplicate_paths = {occ.path for occs in result.duplicates.values() for occ in occs}
    for path in duplicate_paths:
        candidates = extract_source_candidates(path)
        for key, occs in result.duplicates.items():
            if not any(occ.path == path for occ in occs):
                continue
            question_key, answer_key = key
            exact = [
                hit for hit in candidates
                if hit.question_key == question_key and hit.answer_key == answer_key
            ]
            partial = [
                hit for hit in candidates
                if hit not in exact
                and (hit.question_key == question_key or hit.answer_key == answer_key)
            ]
            for hit in exact + partial:
                result.source_hits.setdefault(key, []).append(hit)


def print_report(result: CheckResult, top: int) -> None:
    total_samples = sum(run.samples for run in result.runs)
    print(
        f"Sampled {len(result.runs)} world script(s), {total_samples} generated sample(s). "
        f"Duplicate story QA pair groups: {len(result.duplicates)}."
    )
    if result.failures:
        print()
        print("Run failures:")
        for path, code, stderr in result.failures[:top]:
            first = stderr.splitlines()[0] if stderr else "(no stderr)"
            print(f"- {display_path(path)}: rc={code}: {first}")

    if not result.duplicates:
        return

    print()
    print("Task list:")
    ranked = sorted(result.duplicates.items(), key=lambda item: (-len(item[1]), item[1][0].question))
    for i, (key, occs) in enumerate(ranked[:top], 1):
        first = occs[0]
        print(f"{i}. [ ] Parameterize duplicated story QA pair seen {len(occs)} times")
        print(f"   Q: {first.question}")
        print(f"   A: {first.answer}")
        hits = result.source_hits.get(key, [])
        if hits:
            for hit in sorted(hits, key=lambda h: (display_path(h.path), h.line))[:6]:
                static_bits = []
                if hit.question_static:
                    static_bits.append("static question")
                if hit.answer_static:
                    static_bits.append("static answer")
                detail = f" ({', '.join(static_bits)})" if static_bits else ""
                print(f"   - {display_path(hit.path)}:{hit.line}{detail}: {hit.snippet}")
        else:
            paths = sorted({display_path(occ.path) for occ in occs})
            print(f"   - No exact static QA literal found; emitted by: {', '.join(paths[:6])}")
        print("   Fix: replace literal story-specific QA with values from StoryParams/world.facts, or move generic material to world_qa.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sample storyworld scripts and report duplicate static story QA pairs."
    )
    parser.add_argument("-n", "--count", type=int, default=20, help="number of world scripts to sample; default: 20")
    parser.add_argument("--variants", type=int, default=3, help="generated variants per script; default: 3")
    parser.add_argument("--seed", type=int, default=42, help="seed for reproducible world and story selection")
    parser.add_argument("--worlds-dir", type=Path, default=DEFAULT_WORLDS_DIR, help="directory containing storyworld scripts")
    parser.add_argument("--recursive", action="store_true", help="search worlds-dir recursively instead of only direct children")
    parser.add_argument("--include-tmp", action="store_true", help="include storyworlds/worlds/tmp batch output")
    parser.add_argument("--allow-repeat", action="store_true", help="allow sampling the same world more than once")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run worlds")
    parser.add_argument("--timeout", type=float, default=30.0, help="timeout per world in seconds")
    parser.add_argument("--top", type=int, default=20, help="maximum findings to print")
    parser.add_argument("--no-fail", action="store_true", help="always exit 0 after printing the report")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_result(args)
    attach_source_hits(result)
    print_report(result, args.top)
    if args.no_fail:
        return 0
    if result.failures:
        return 1
    if result.duplicates:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
