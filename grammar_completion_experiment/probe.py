#!/usr/bin/env python3
"""Probe a real classical predictive grammar; replay saved results offline.

    python grammar_completion_experiment/probe.py
    python grammar_completion_experiment/probe.py --verify
    python grammar_completion_experiment/probe.py --prefix 'she wants to'
    python grammar_completion_experiment/probe.py --refresh

--refresh queries the public GF service with synthetic test sentences. No LLM,
installation, or user documents are involved. Normal runs only read the fixture.
Probabilities below are an explicitly uniform BASELINE over legal next words,
including <END> when a full parse exists. GF's completion API does not supply
calibrated next-word probabilities. Grammar constructors are NOT production rules.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


END = "<END>"
ENDPOINT = "https://cloud.grammaticalframework.org/grammars/Phrasebook.pgf"
FIXTURE = Path(__file__).with_name("observations.json")
PREFIXES = (
    "", "she", "they", "she wants", "she wants to", "she wants to eat",
    "she wants to eat the", "she is", "they are", "she are", "they is",
    "she wants to eats", "she wants to eat bread", "she wants to eat beer",
)


def request(command: str, **parameters):
    url = ENDPOINT + "?" + urlencode({"command": command, **parameters})
    with urlopen(url, timeout=25) as response:
        return json.load(response)


def collect(prefix: str) -> dict:
    # Trailing whitespace means complete the NEXT word, not the current fragment.
    completions = request("complete", **{"from": "PhrasebookEng", "cat": "Sentence",
                                          "input": prefix + " " if prefix else ""})
    parses = request("parse", **{"from": "PhrasebookEng", "cat": "Sentence",
                                 "input": prefix, "limit": 1})
    return dict(prefix=prefix, completion_response=completions, parse_response=parses)


def summarize(observation: dict) -> dict:
    words = sorted({word for entry in observation["completion_response"]
                    for word in entry.get("completions", [])})
    trees = [tree for entry in observation["parse_response"]
             for tree in (entry.get("trees") or [])]
    choices = words + ([END] if trees else [])
    probability = 1 / len(choices) if choices else 0
    return dict(prefix=observation["prefix"], legal_word_count=len(words),
                can_end=bool(trees), valid_prefix=bool(choices),
                distribution=[dict(word=w, probability=probability) for w in choices],
                probability_source="uniform baseline supplied by this probe, not GF",
                example_parse=trees[0] if trees else None)


def verify(data: dict) -> None:
    rows = {o["prefix"]: summarize(o) for o in data["observations"]}

    def support(prefix):
        return {c["word"] for c in rows[prefix]["distribution"]}

    assert "is" in support("she") and "are" not in support("she")
    assert "are" in support("they") and "is" not in support("they")
    assert "eat" in support("she wants to") and "eats" not in support("she wants to")
    assert {"to", "bread"} <= support("she wants")
    for prefix in ("she are", "they is", "she wants to eats"):
        assert not rows[prefix]["valid_prefix"], prefix
    assert END in support("she wants to eat")
    assert END not in support("she wants to eat the")
    assert END in support("she wants to eat bread")
    # Deliberately document the semantics gap, rather than hide it by filtering.
    assert END in support("she wants to eat beer")
    for row in rows.values():
        if row["distribution"]:
            assert abs(sum(c["probability"] for c in row["distribution"]) - 1) < 1e-12
    print("PASS: saved live observations check agreement, verb forms, branching,")
    print("      optional stopping, normalization, and the documented semantics gap.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--refresh", action="store_true", help="query GF and replace saved observations")
    parser.add_argument("--prefix", help="inspect a recorded prefix; combine with --refresh for a new one")
    parser.add_argument("--json", action="store_true", help="show complete uniform distributions")
    parser.add_argument("--verify", action="store_true", help="check saved observations offline")
    args = parser.parse_args()
    prefix = " ".join(args.prefix.split()) if args.prefix is not None else None
    if args.refresh:
        metadata = request("grammar")
        observations = [collect(p) for p in dict.fromkeys((*PREFIXES, *((prefix,) if prefix is not None else ())))]
        data = dict(endpoint=ENDPOINT, recorded_at=datetime.now(timezone.utc).isoformat(),
                    grammar=metadata, observations=observations)
        # Only replace the fixture after every request has succeeded.
        temporary = FIXTURE.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2) + "\n")
        temporary.replace(FIXTURE)
    else:
        if not FIXTURE.exists():
            parser.error("no saved observations; run with --refresh")
        data = json.loads(FIXTURE.read_text())
    if args.verify:
        verify(data)
        return
    rows = [summarize(o) for o in data["observations"]
            if prefix is None or o["prefix"] == prefix]
    if not rows:
        parser.error("prefix not recorded; use --refresh --prefix to query it")
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    grammar = data["grammar"]
    print(f"GF {grammar['name']}: {len(grammar['functions'])} abstract constructors, "
          f"{len(grammar['categories'])} categories, {len(grammar['languages'])} languages.")
    print(f"Saved observations: {data['recorded_at']}; English, Sentence category.")
    print("Uniform baseline probabilities; these are not learned or provided by GF.\n")
    for row in rows:
        print(f"Prefix {row['prefix']!r}: {row['legal_word_count']} legal next words; "
              f"can end: {row['can_end']}")
        choices = row["distribution"]
        shown = choices if prefix is not None else choices[:8]
        print("  " + (", ".join(f"{c['word']} ({c['probability']:.1%})" for c in shown) or "rejected"))
        if len(shown) < len(choices):
            print(f"  ... {len(choices) - len(shown)} more alternatives (use --json for all)")


if __name__ == "__main__":
    main()
