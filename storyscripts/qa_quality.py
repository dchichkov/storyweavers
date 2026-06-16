#!/usr/bin/env python3
"""
Measure generated QA quality for standalone story scripts.

This is intentionally lightweight: it runs each generator in JSONL mode, reads
the emitted questions, and reports structural quality/diversity signals.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SCRIPTS = (
    "quest.py",
    "journey.py",
    "friendship.py",
    "discovery.py",
    "encounter.py",
    "loss.py",
    "conflict.py",
    "apology.py",
    "cautionary.py",
    "gift.py",
    "rescue.py",
    "transformation.py",
    "surprise.py",
)


@dataclass
class Metrics:
    records: int = 0
    unique_stories: int = 0
    unique_story_shapes: int = 0
    duplicate_story_shapes: int = 0
    questions: int = 0
    empty_answers: int = 0
    empty_followups: int = 0
    quote_mismatches: int = 0
    multi_turn: int = 0
    full_answers: int = 0
    answer_sentences: int = 0
    question_shapes: Counter[str] = None
    followup_shapes: Counter[str] = None
    story_shapes: Counter[str] = None

    def __post_init__(self) -> None:
        if self.question_shapes is None:
            self.question_shapes = Counter()
        if self.followup_shapes is None:
            self.followup_shapes = Counter()
        if self.story_shapes is None:
            self.story_shapes = Counter()


def sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+(?:\s+|$)", text.strip()) if part.strip()])


QUESTION_WORDS = {
    "Who", "What", "Where", "When", "Why", "How", "Which",
    "Did", "Does", "Do", "Was", "Were", "Is", "Are",
}


def shape(text: str) -> str:
    def replace_name(match: re.Match[str]) -> str:
        word = match.group(0)
        return word if word in QUESTION_WORDS else "NAME"

    text = re.sub(r"\b[A-Z][a-z]+\b", replace_name, text.strip())
    text = re.sub(r"\b\d+\b", "N", text)
    return re.sub(r"\s+", " ", text).lower()


def story_shape(text: str) -> str:
    text = re.sub(r'"[^"]+"', '"QUOTE"', text)
    text = re.sub(r"\b[A-Z][a-z]+\b", "NAME", text)
    text = re.sub(r"there was (?:a|an) [^.]+? named NAME", "there was CHARACTER named NAME", text, flags=re.I)
    text = re.sub(r"\b(?:boy|girl|bunny|cat|dog|bear|frog|duck|bee|squirrel|child)\b", "CHARACTER", text, flags=re.I)
    text = re.sub(r"\b(?:red|blue|green|yellow|purple|shiny|little|small|big|bright|soft|warm|old|new)\b", "ATTR", text, flags=re.I)
    return re.sub(r"\s+", " ", text.strip().lower())


def quoted_parts(text: str) -> list[str]:
    return [part.strip() for part in re.findall(r'"([^"]+)"', text) if part.strip()]


def sample_script(script: str, count: int, seed: int) -> list[dict]:
    path = SCRIPT_DIR / script
    cmd = [sys.executable, str(path), "-n", str(count), "--seed", str(seed), "--format", "jsonl"]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def measure(records: list[dict]) -> Metrics:
    metrics = Metrics(records=len(records))
    stories = [record.get("story", "") for record in records]
    metrics.unique_stories = len(set(stories))
    for story in stories:
        metrics.story_shapes[story_shape(story)] += 1
    metrics.unique_story_shapes = len(metrics.story_shapes)
    metrics.duplicate_story_shapes = sum(count - 1 for count in metrics.story_shapes.values() if count > 1)

    for record in records:
        story = record.get("story", "")
        for qa in record.get("questions", []):
            metrics.questions += 1
            question = qa.get("question", "")
            answer = qa.get("answer", "")
            follow_question = qa.get("follow_up_question", "")
            follow_answer = qa.get("follow_up_answer", "")
            turns = qa.get("turns", [])

            answer_sents = sentence_count(answer)
            metrics.answer_sentences += answer_sents
            if answer_sents >= 2:
                metrics.full_answers += 1
            if not answer.strip():
                metrics.empty_answers += 1
            if not follow_question.strip() or not follow_answer.strip():
                metrics.empty_followups += 1
            if len(turns) >= 4:
                metrics.multi_turn += 1
            for quote in quoted_parts(answer) + quoted_parts(follow_answer):
                if quote and quote not in story:
                    metrics.quote_mismatches += 1
            metrics.question_shapes[shape(question)] += 1
            if follow_question:
                metrics.followup_shapes[shape(follow_question)] += 1
    return metrics


def print_report(name: str, metrics: Metrics) -> None:
    avg_q = metrics.questions / metrics.records if metrics.records else 0.0
    avg_sentences = metrics.answer_sentences / metrics.questions if metrics.questions else 0.0
    full_pct = 100 * metrics.full_answers / metrics.questions if metrics.questions else 0.0
    turn_pct = 100 * metrics.multi_turn / metrics.questions if metrics.questions else 0.0
    print(f"== {name} ==")
    print(f"records: {metrics.records}")
    print(f"unique stories: {metrics.unique_stories}; story shapes: {metrics.unique_story_shapes} unique, {metrics.duplicate_story_shapes} duplicate-shaped")
    print(f"questions: {metrics.questions} ({avg_q:.2f} per story)")
    print(f"answer sentences: {avg_sentences:.2f} avg; {full_pct:.1f}% have 2+ sentences")
    print(f"multi-turn: {turn_pct:.1f}%")
    print(f"empty answers: {metrics.empty_answers}; empty follow-ups: {metrics.empty_followups}; quote mismatches: {metrics.quote_mismatches}")
    print(f"question shapes: {len(metrics.question_shapes)} unique")
    print(f"follow-up shapes: {len(metrics.followup_shapes)} unique")
    common = ", ".join(f"{k} ({v})" for k, v in metrics.question_shapes.most_common(5))
    print(f"common question shapes: {common}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure standalone story QA output.")
    parser.add_argument("-n", "--num", type=int, default=100, help="Stories to sample per script.")
    parser.add_argument("--seed", type=int, default=42, help="Seed passed to each story script.")
    parser.add_argument("--scripts", nargs="+", default=list(DEFAULT_SCRIPTS), help="Script filenames in storyscripts/.")
    args = parser.parse_args()

    for script in args.scripts:
        records = sample_script(script, args.num, args.seed)
        print_report(script, measure(records))


if __name__ == "__main__":
    main()
