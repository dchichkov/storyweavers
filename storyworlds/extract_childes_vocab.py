#!/usr/bin/env python3
"""Extract derived vocabulary counts from local CHILDES CHAT transcripts.

Expected input is a locally downloaded TalkBank CHILDES tree such as ``Eng-NA/``.
The script reads MOR tiers from ``.cha`` files and writes small derived wordlists;
it does not copy transcript text.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "Eng-NA"
DEFAULT_OUT_DIR = ROOT / "storyworlds" / "data" / "childes"

WORD_RE = re.compile(r"^[a-z][a-z'-]*$")
MOR_SUFFIX_RE = re.compile(
    r"(&[a-z0-9]+|-([a-z0-9]+|3s|pastp?|pres|presp|cond|cp|sup))$",
    re.IGNORECASE,
)
POS_ALIASES = {
    "n": "noun",
    "v": "verb",
    "adj": "adjective",
    "part": "verb",
}
SEED_POS = {"noun", "verb", "adjective"}
SKIP_LEMMAS = {
    "a",
    "an",
    "and",
    "alright",
    "be",
    "can",
    "could",
    "do",
    "does",
    "did",
    "go",
    "gonna",
    "have",
    "he",
    "her",
    "here",
    "him",
    "i",
    "it",
    "just",
    "last",
    "me",
    "mean",
    "my",
    "next",
    "not",
    "of",
    "okay",
    "on",
    "one",
    "real",
    "ready",
    "right",
    "same",
    "she",
    "that",
    "the",
    "there",
    "them",
    "they",
    "thing",
    "to",
    "was",
    "we",
    "whole",
    "will",
    "with",
    "you",
    "your",
}


@dataclass
class LemmaStats:
    child: int = 0
    other: int = 0
    files: set[str] = field(default_factory=set)

    @property
    def total(self) -> int:
        return self.child + self.other


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build derived vocabulary lists from local CHILDES .cha files."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="local CHILDES transcript directory; default: ./Eng-NA",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="directory for derived TSV/TXT files",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=20,
        help="minimum total lemma count for seed candidate lists",
    )
    parser.add_argument(
        "--min-files",
        type=int,
        default=3,
        help="minimum distinct transcript files for seed candidate lists",
    )
    parser.add_argument(
        "--top-per-pos",
        type=int,
        default=600,
        help="maximum candidates per noun/verb/adjective list",
    )
    return parser


def clean_lemma(raw: str) -> str:
    lemma = raw.lower().strip()
    lemma = lemma.split("=")[0]
    lemma = MOR_SUFFIX_RE.sub("", lemma)
    lemma = lemma.replace("_", " ")
    lemma = lemma.replace("0", "")
    lemma = lemma.strip("'-. ")
    return lemma


def pieces_from_mor_token(token: str) -> list[tuple[str, str, bool]]:
    pieces: list[tuple[str, str, bool]] = []
    for clitic in token.split("~"):
        if "|" not in clitic:
            continue
        pos, rest = clitic.split("|", 1)
        pos_root = pos.split(":", 1)[0]
        is_proper = "prop" in pos
        if "+" in rest:
            for part in rest.split("+"):
                if not part:
                    continue
                part_pos = pos_root
                part_lemma = part
                if "|" in part:
                    part_pos, part_lemma = part.split("|", 1)
                    part_pos = part_pos.split(":", 1)[0].lstrip("+")
                pieces.append((part_pos, part_lemma, is_proper or "prop" in part_pos))
            continue
        pieces.append((pos_root, rest, is_proper))
    return pieces


def parse_mor_tier(text: str) -> list[tuple[str, str, bool]]:
    rows: list[tuple[str, str, bool]] = []
    for token in text.split():
        token = token.strip()
        if not token or token in {".", ",", "?", "!", ";", ":"}:
            continue
        for pos, lemma, is_proper in pieces_from_mor_token(token):
            coarse = POS_ALIASES.get(pos)
            if coarse is None:
                continue
            cleaned = clean_lemma(lemma)
            if not WORD_RE.fullmatch(cleaned):
                continue
            rows.append((cleaned, coarse, is_proper))
    return rows


def iter_mor_records(path: Path) -> tuple[int, list[tuple[str, str]]]:
    speaker = ""
    mor_speaker = ""
    mor_parts: list[str] = []
    records: list[tuple[str, str]] = []
    lines = 0

    def flush_mor() -> None:
        nonlocal mor_parts, mor_speaker
        if mor_parts and mor_speaker:
            records.append((mor_speaker, " ".join(mor_parts)))
        mor_parts = []
        mor_speaker = ""

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        lines += 1
        if raw_line.startswith("*"):
            flush_mor()
            speaker = raw_line[1:].split(":", 1)[0]
            continue
        if raw_line.startswith("%mor:"):
            flush_mor()
            mor_speaker = speaker
            mor_parts = [raw_line.split(":", 1)[1].strip()]
            continue
        if mor_parts and raw_line.startswith("\t"):
            mor_parts.append(raw_line.strip())
            continue
        if raw_line.startswith("%") or raw_line.startswith("@"):
            flush_mor()
    flush_mor()
    return lines, records


def collect(input_dir: Path) -> tuple[dict[tuple[str, str], LemmaStats], dict[str, int]]:
    counts: dict[tuple[str, str], LemmaStats] = defaultdict(LemmaStats)
    summary = Counter()
    paths = sorted(input_dir.rglob("*.cha"))
    summary["files"] = len(paths)
    for path in paths:
        file_seen: set[tuple[str, str]] = set()
        lines, records = iter_mor_records(path)
        summary["lines"] += lines
        summary["mor_records"] += len(records)
        rel = path.relative_to(input_dir).as_posix()
        for speaker, mor_text in records:
            group = "child" if speaker == "CHI" else "other"
            for lemma, pos, is_proper in parse_mor_tier(mor_text):
                if is_proper:
                    summary["proper_skipped"] += 1
                    continue
                key = (lemma, pos)
                stats = counts[key]
                if group == "child":
                    stats.child += 1
                else:
                    stats.other += 1
                file_seen.add(key)
        for key in file_seen:
            counts[key].files.add(rel)
    summary["lemma_pos_rows"] = len(counts)
    return counts, dict(summary)


def candidate_rows(
    counts: dict[tuple[str, str], LemmaStats],
    *,
    pos: str,
    min_count: int,
    min_files: int,
    limit: int,
) -> list[tuple[str, LemmaStats]]:
    rows = [
        (lemma, stats)
        for (lemma, row_pos), stats in counts.items()
        if row_pos == pos
        and stats.total >= min_count
        and len(stats.files) >= min_files
        and lemma not in SKIP_LEMMAS
        and 3 <= len(lemma) <= 16
    ]
    rows.sort(key=lambda item: (-item[1].total, item[0]))
    return rows[:limit]


def write_counts(path: Path, counts: dict[tuple[str, str], LemmaStats]) -> None:
    rows = sorted(
        counts.items(),
        key=lambda item: (-item[1].total, item[0][1], item[0][0]),
    )
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["lemma", "pos", "child_count", "other_count", "total_count", "file_count"])
        for (lemma, pos), stats in rows:
            writer.writerow([lemma, pos, stats.child, stats.other, stats.total, len(stats.files)])


def write_candidates(
    out_dir: Path,
    counts: dict[tuple[str, str], LemmaStats],
    *,
    min_count: int,
    min_files: int,
    top_per_pos: int,
) -> None:
    for pos in sorted(SEED_POS):
        rows = candidate_rows(
            counts,
            pos=pos,
            min_count=min_count,
            min_files=min_files,
            limit=top_per_pos,
        )
        out_path = out_dir / f"childes_eng_na_{pos}s.txt"
        with out_path.open("w", encoding="utf-8") as f:
            f.write(
                f"# Derived from local CHILDES Eng-NA MOR tiers. "
                f"min_count={min_count}, min_files={min_files}\n"
            )
            for lemma, stats in rows:
                f.write(f"{lemma}\t{stats.total}\t{stats.child}\t{stats.other}\t{len(stats.files)}\n")


def write_vocab_txt(out_dir: Path, counts: dict[tuple[str, str], LemmaStats]) -> None:
    merged: dict[str, LemmaStats] = defaultdict(LemmaStats)
    for (lemma, pos), stats in counts.items():
        if lemma in SKIP_LEMMAS:
            continue
        if not WORD_RE.fullmatch(lemma):
            continue
        if not 3 <= len(lemma) <= 16:
            continue
        dest = merged[lemma]
        dest.child += stats.child
        dest.other += stats.other
        dest.files.update(stats.files)

    rows = sorted(merged.items(), key=lambda item: (-item[1].total, item[0]))
    out_path = out_dir / "childes_eng_na_vocab.txt"
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Derived from local CHILDES Eng-NA MOR tiers. One word per line.\n")
        f.write("# Columns: word, total_count, child_count, other_count, file_count\n")
        for lemma, stats in rows:
            f.write(f"{lemma}\t{stats.total}\t{stats.child}\t{stats.other}\t{len(stats.files)}\n")


def write_summary(path: Path, summary: dict[str, int], args: argparse.Namespace) -> None:
    lines = [
        "# CHILDES Eng-NA Derived Vocabulary",
        "",
        "Generated from local CHAT `.cha` transcripts. Raw transcript text is not copied.",
        "",
        f"- input: `{args.input}`",
        f"- files: {summary.get('files', 0)}",
        f"- MOR records: {summary.get('mor_records', 0)}",
        f"- lemma/POS rows: {summary.get('lemma_pos_rows', 0)}",
        f"- seed candidate minimum count: {args.min_count}",
        f"- seed candidate minimum files: {args.min_files}",
        "",
        "Files:",
        "- `childes_eng_na_word_counts.tsv`: full derived lemma/POS counts.",
        "- `childes_eng_na_vocab.txt`: merged one-word-per-line vocabulary counts.",
        "- `childes_eng_na_nouns.txt`, `childes_eng_na_verbs.txt`, "
        "`childes_eng_na_adjectives.txt`: seed-friendly candidates.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    input_dir = args.input.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    if not input_dir.exists():
        raise SystemExit(f"{input_dir} does not exist")
    out_dir.mkdir(parents=True, exist_ok=True)
    counts, summary = collect(input_dir)
    write_counts(out_dir / "childes_eng_na_word_counts.tsv", counts)
    write_candidates(
        out_dir,
        counts,
        min_count=args.min_count,
        min_files=args.min_files,
        top_per_pos=args.top_per_pos,
    )
    write_summary(out_dir / "README.md", summary, args)
    write_vocab_txt(out_dir, counts)
    print(
        f"read {summary.get('files', 0)} files, "
        f"{summary.get('mor_records', 0)} MOR records, "
        f"{summary.get('lemma_pos_rows', 0)} lemma/POS rows"
    )
    print(f"wrote {out_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
