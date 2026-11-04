#!/usr/bin/env python3
"""Reproducible inventory, scripted witnesses, and random traversal diagnostics."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import unittest

from content import BEATS, ENDINGS, EXCHANGES, MIXINS
from engine import Session, replay
from play import DEMOS, run_demo
from test_drama import all_performances, assert_world


def inventory():
    performances = list(all_performances())
    lines = [line for p in performances for line in p.lines]
    root = Path(__file__).resolve().parent
    return {
        "sequenced_beats": len(BEATS),
        "within_beat_goals": sum(len(b.goals) for b in BEATS),
        "terminal_outcomes": len(ENDINGS),
        "terminal_performances": sum(len(v) for _, v, _ in ENDINGS),
        "global_mixin_topics": len(MIXINS),
        "global_mixin_tiers": sum(len(tiers) for tiers in MIXINS.values()),
        "social_exchange_bindings": len(EXCHANGES),
        "performance_slots": len(performances),
        "authored_line_slots": len(lines),
        "unique_authored_lines": len(set(lines)),
        "authored_word_slots": sum(len(line.split()) for line in lines),
        "engine_source_lines": len((root / "engine.py").read_text().splitlines()),
        "content_source_lines": len((root / "content.py").read_text().splitlines()),
        "note": "Slots include alternatives and shared lines. Runtime refusal/resume/input text is not counted. These are not human-equivalent effort estimates.",
    }


def audit(count):
    check = unittest.TestCase()
    demos = {name: run_demo(name) for name in DEMOS}
    outcomes, paths, seen_beats = Counter(), set(), set()
    goal_variants, failures = set(), []
    for seed in range(count):
        rng = random.Random(seed)
        session = Session(seed)
        session.start()
        # Predeclared exploratory policy: uniform supported actions plus eight listens.
        actions = list(session.actions()) + ["listen"] * 8
        try:
            while not session.outcome and session.state["turn"] < 24:
                session.step(rng.choice(actions))
                assert_world(check, session)
            check.assertIsNotNone(session.outcome)
            check.assertEqual(replay(session.export()).export(), session.export())
        except (AssertionError, ValueError, RuntimeError) as error:
            failures.append({"seed": seed, "commands": session.commands, "error": str(error)})
        outcomes[session.outcome] += 1
        selection_path = tuple(d["chosen"] for d in session.selections if "chosen" in d)
        paths.add(selection_path)
        seen_beats.update(selection_path)
        goal_variants.update((e["source"], e["variant"]) for e in session.events if e["kind"] == "goal")
    report = {
        "inventory": inventory(),
        "random_traversal": {
            "sessions": count, "seeds": "0.." + str(count - 1),
            "policy": "uniform supported actions plus eight extra listen entries",
            "outcomes": dict(outcomes), "unique_selected_beat_paths": len(paths),
            "beats_reached": sorted(seen_beats), "goal_variants_reached": len(goal_variants),
            "failures": failures,
        },
        "scripted_witnesses": {name: {"outcome": s.outcome, "turns": s.state["turn"],
                                      "completed_beats": s.completed, "aborted_beats": s.aborted}
                               for name, s in demos.items()},
        "counterfactual": {
            "changed_inputs": "Only the two early empathize actions become blame actions.",
            "warm_outcome": demos["repair"].outcome, "cold_outcome": demos["distrust"].outcome,
            "same_remaining_script": DEMOS["repair"][4:] == DEMOS["distrust"][4:],
            "different_completed_beat_paths": demos["repair"].completed != demos["distrust"].completed,
        },
        "limits": "Traversal checks termination, replay, state chains, and knowledge invariants; it does not grade dialogue quality. Path counts are not counts of distinct stories. No human baseline, timed extension trial, or cost reduction has been measured.",
    }
    return report, demos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=500)
    parser.add_argument("--write", action="store_true", help="Regenerate examples and audit.json in this directory")
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    report, demos = audit(args.samples)
    if args.write:
        root = Path(__file__).resolve().parent
        (root / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (root / "examples").mkdir(exist_ok=True)
        for name, session in demos.items():
            (root / "examples" / (name + ".txt")).write_text(
                "\n\n".join(session.transcript) + "\n\n[Ending: " + session.outcome + "]\n", encoding="utf-8")
            # One full record is sufficient to make replay inspectable without large fixtures.
            if name == "repair":
                session.save(root / "examples" / "repair.trace.json")
    print(json.dumps(report, indent=2))
    if report["random_traversal"]["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
