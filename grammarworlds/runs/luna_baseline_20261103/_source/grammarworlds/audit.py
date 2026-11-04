"""Exhaustively audit the small reachable world graph and grammar realizations.

Counts distinguish authored kernel/rule labels from instantiated derivations.
Story-path counts are derivations, not a claim of independent plots or unique
English strings. This audit checks structural/physical invariants, not literary
quality or calibration against a trained model.
"""

from __future__ import annotations

import json
import math

from .grammar import Grammar, detokenize, expand
from .world import KERNELS, SCENARIOS, World, commit, frames, make_world


def audit_world(scenario: str, seed: int = 2, tense: str = "past") -> dict:
    seen, rules = {}, set()
    statistics = dict(states=0, semantic_transitions=0, instantiated_derivations=0,
                      max_sentence_derivations=0, terminal_states=0)
    lengths = set()

    def visit(world: World) -> tuple[int, int, int]:
        # Histories with the same physical/discourse state have the same support.
        # Scores may differ with the last event; this audit counts support only.
        key = json.dumps({"state": world.snapshot(), "focus": world.focus}, sort_keys=True)
        if key in seen:
            return seen[key]
        statistics["states"] += 1
        if world.finished:
            statistics["terminal_states"] += 1
            assert "resolved" in world.flags
            result = (1, 0, 0)
            seen[key] = result
            return result
        candidates = frames(world)
        assert candidates, f"nonterminal dead end: {world.scenario}, {world.flags}"
        grammar = Grammar(world, tense)
        total, minimum, maximum = 0, math.inf, 0
        per_state = 0
        for _, frame in candidates:
            variants = list(expand(grammar.for_frame(frame)))
            assert variants
            assert math.isclose(sum(p for _, p, _ in variants), 1)
            for tokens, p, labels in variants:
                assert p > 0 and tokens[-1] == "."
                assert all(isinstance(token, str) and token for token in tokens)
                rules.update(labels)
                lengths.add(sum(token[0].isalpha() for token in tokens))
            per_state += len(variants)
            statistics["semantic_transitions"] += 1
            statistics["instantiated_derivations"] += len(variants)
            next_world = world.clone()
            commit(next_world, frame, detokenize(variants[0][0]))
            assert world.flags < next_world.flags, "kernel must make monotonic story progress"
            count, low, high = visit(next_world)
            total += len(variants) * count
            minimum, maximum = min(minimum, 1 + low), max(maximum, 1 + high)
        statistics["max_sentence_derivations"] = max(statistics["max_sentence_derivations"], per_state)
        result = total, minimum, maximum
        seen[key] = result
        return result

    count, minimum, maximum = visit(make_world(scenario, seed))
    return dict(scenario=scenario, tense=tense, seed=seed, **statistics,
                grammar_rule_label_count=len(rules), grammar_rule_labels=sorted(rules),
                sentence_word_lengths=sorted(lengths), min_story_sentences=minimum,
                max_story_sentences=maximum, complete_story_derivation_paths=count)


def main() -> None:
    print(json.dumps({"authored_event_kernels": len(KERNELS),
                      "audits": [audit_world(scenario) for scenario in SCENARIOS]}, indent=2))


if __name__ == "__main__":
    main()
