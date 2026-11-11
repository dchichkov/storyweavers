"""Deterministic symbolic position features, computed locally over exact tokens."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Sequence


END_MARKS = frozenset(".!?。！？")
CLOSERS = frozenset("\"'’”»)]}")
ABBREVIATIONS = frozenset({"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st"})
POSITION_ENCODING = {"version": 1, "index_base": 0, "counts": "all_tokens",
                     "sentence_boundaries": "punctuation_rules"}


def add_positions(tokens: Sequence[dict]) -> list[dict]:
    """Add global token, sentence and within-sentence indices without an LLM.

    Spaces and punctuation count as tokens. End punctuation, closing quotes and
    following whitespace stay in the preceding sentence. A new sentence starts
    at the next content token. Decimal tokens remain whole; common title
    abbreviations do not end sentences. This is a heuristic, not a parser.
    """
    result = []
    sentence = in_sentence = 0
    pending_boundary = False
    boundary_gap = False
    previous_content = ""
    for index, source in enumerate(tokens):
        token = source["token"]
        if not isinstance(token, str) or not token:
            raise ValueError("position encoding requires nonempty string tokens")
        space = token.isspace()
        closing = all(c in END_MARKS or c in CLOSERS for c in token)
        if boundary_gap and token in {"\"", "'"}:
            closing = False  # A quote after a sentence-ending gap opens the next sentence.
        if pending_boundary and not space and not closing:
            sentence += 1
            in_sentence = 0
            pending_boundary = False
            boundary_gap = False
        row = deepcopy(source)
        row["position"] = {"token": index, "sentence": sentence, "in_sentence": in_sentence}
        result.append(row)
        in_sentence += 1
        if all(c in END_MARKS for c in token):
            if token != "." or previous_content.casefold() not in ABBREVIATIONS:
                pending_boundary = True
                boundary_gap = False
        if space and pending_boundary:
            boundary_gap = True
        if not space:
            previous_content = token
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="existing annotation JSON array")
    parser.add_argument("--output", type=Path, required=True, help="destination; may equal input")
    args = parser.parse_args()
    rows = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(add_positions(rows), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
