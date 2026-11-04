"""Behavioral tests for grammar, semantics, probabilities, and complete stories."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import math
import random
import unittest

from .engine import advance, build_forest, generate, sample_sentence, score_frame
from .grammar import Derivation, Forest, Grammar, choice, expand, seq, tokenize
from .world import BY_NAME, Frame, SCENARIOS, commit, frames, grounded_action, make_world


class GrammarTests(unittest.TestCase):
    def test_composition_and_normalization(self):
        grammar = seq("sentence", choice("subject", "Lily", "Sam", weights=(3, 1)),
                      choice("predicate", "runs", seq("transitive", "carries", "the kitten")))
        rows = list(expand(grammar))
        self.assertEqual(len(rows), 4)
        self.assertAlmostEqual(sum(p for _, p, _ in rows), 1)
        self.assertEqual({len(t) for t, _, _ in rows}, {2, 4})

    def test_exact_prefix_marginalization_and_stopping(self):
        a, b = Frame("a", "hero"), Frame("b", "hero")
        forest = Forest([
            Derivation(("she", "runs"), 0.2, a, ()),
            Derivation(("she", "runs", "home"), 0.3, b, ()),
            Derivation(("she", "walks"), 0.5, a, ()),
        ], {})
        self.assertEqual({c["word"]: c["probability"] for c in forest.predict(("she",))["choices"]},
                         {"runs": 0.5, "walks": 0.5})
        self.assertEqual({c["word"]: c["probability"] for c in forest.predict(("she", "runs"))["choices"]},
                         {"home": 0.6, "<END>": 0.4})
        self.assertFalse(forest.predict(("she", "eats"))["choices"])

    def test_grammar_branches_by_words_not_position(self):
        world = advance("rescue", 2, 1)
        forest = build_forest(world)
        choices = {c["word"] for c in forest.predict(("she",))["choices"]}
        self.assertTrue({"asked", "reached", "realized", "wanted"} <= choices)
        self.assertEqual({c["word"] for c in forest.predict(("she", "wanted"))["choices"]}, {"to"})
        self.assertIn("that", {c["word"] for c in forest.predict(("she", "realized"))["choices"]})
        self.assertNotIn("that", {c["word"] for c in forest.predict(("she", "wanted"))["choices"]})
        self.assertFalse(forest.predict(("she", "are"))["choices"])

    def test_agreement_inflection(self):
        world = make_world()
        grammar = Grammar(world, "present")
        self.assertEqual(grammar.verb("carry", world.hero), "carries")
        self.assertEqual(grammar.be(world.hero), "is")
        world.entities[world.hero].number = "plural"
        self.assertEqual(grammar.verb("carry", world.hero), "carry")
        self.assertEqual(grammar.be(world.hero), "are")


class WorldTests(unittest.TestCase):
    def test_affordances_and_unknown_carriers(self):
        world = make_world()
        self.assertTrue(grounded_action(world, "eat", "hero", "bread")[0])
        self.assertFalse(grounded_action(world, "eat", "hero", "water")[0])
        self.assertFalse(grounded_action(world, "eat", "hero", "stone")[0])
        self.assertTrue(grounded_action(world, "drink", "hero", "water")[0])
        self.assertFalse(grounded_action(world, "carry", "stone", "target")[0])
        self.assertFalse(grounded_action(world, "carry", "ghost", "target")[0])
        self.assertFalse(grounded_action(world, "rescue", "hero", "target", "stone")[0])

    def test_no_state_mutation_during_prediction(self):
        world = advance("rescue", 2, 1)
        before = deepcopy(world)
        forest = build_forest(world)
        forest.predict(("she",))
        self.assertEqual(world, before)
        self.assertNotIn("prepared", world.flags)

    def test_cannot_skip_physical_preconditions(self):
        world = make_world("key")
        bad = Frame("solve", "hero", "target", "tool", "cottage", ("problem", "obstacle", "tool_available"))
        with self.assertRaises(ValueError):
            commit(world, bad, "She found the key.")
        world.flags.update({"noticed", "prepared"})
        self.assertNotIn("solve", {k.name for k, _ in frames(world)})
        world.entities["tool"].location = "hero"
        self.assertIn("solve", {k.name for k, _ in frames(world)})
        world.entities["tool"].properties.remove("illuminate")
        self.assertNotIn("solve", {k.name for k, _ in frames(world)})

    def test_removed_problem_and_absent_helper(self):
        world = make_world("kite")
        world.entities["target"].state.remove("torn")
        self.assertFalse(frames(world))
        world = advance("kite", 2, 1)
        world.entities["helper"].location = "elsewhere"
        self.assertNotIn("ask", {k.name for k, _ in frames(world)})
        self.assertIn("think", {k.name for k, _ in frames(world)})

    def test_false_ending_cannot_be_narrated(self):
        world = make_world("rescue")
        world.flags.update({"noticed", "planned", "prepared", "solved", "resolved"})
        self.assertNotIn("ending", {k.name for k, _ in frames(world)})

    def test_attention_refreshes_physical_locations(self):
        world = make_world("rescue")
        world.entities[world.tool].location = world.hero
        tool_fact = next(f for f in world.facts_for_attention() if f.id == "tool_available")
        self.assertIn("holding", tool_fact.text)
        self.assertNotIn("shed", tool_fact.text)
        world.entities[world.helper].location = "elsewhere"
        self.assertNotIn("helper_available", {f.id for f in world.facts_for_attention()})

    def test_attention_interventions_change_real_word_probabilities(self):
        low = advance("rescue", 2, 1, fear=0)
        high = advance("rescue", 2, 1, fear=1)
        def distribution(world, attention=True):
            return {c["word"]: c["probability"]
                    for c in build_forest(world, attention=attention).predict(("she",))["choices"]}
        self.assertGreater(distribution(high)["asked"], distribution(low)["asked"])
        self.assertLess(distribution(high)["reached"], distribution(low)["reached"])
        self.assertEqual(distribution(high, False), distribution(low, False))
        evidence = score_frame(high, BY_NAME["ask"])
        self.assertAlmostEqual(sum(x["attention_weight"] for x in evidence["attention"]), 1)
        self.assertTrue(any(x["fact"] == "hero.Fear" and x["contribution"] > 0 for x in evidence["attention"]))


class StoryTests(unittest.TestCase):
    def test_exhaustive_reachable_worlds(self):
        from .audit import audit_world
        for scenario in SCENARIOS:
            result = audit_world(scenario)
            self.assertGreater(result["states"], 10)
            self.assertGreater(result["instantiated_derivations"], 100)
            self.assertLessEqual(result["max_story_sentences"], 10)

    def test_reproducibility_and_surface_likelihood(self):
        self.assertEqual(generate(seed=19), generate(seed=19))
        world = advance("rescue", 2, 1)
        forest = build_forest(world)
        result = sample_sentence(world, random.Random(29))
        matching = [d for d in forest.derivations if list(d.tokens) == result["tokens"]]
        self.assertAlmostEqual(result["probability"], sum(d.probability for d in matching))

    def test_random_stories_are_complete_and_grounded(self):
        signatures, lengths, structures = set(), set(), set()
        counts = Counter()
        for scenario in SCENARIOS:
            for tense in ("past", "present"):
                for seed in range(30):
                    result = generate(scenario, seed, tense=tense)
                    final = result["final_world"]
                    self.assertIn("ended", final["flags"])
                    self.assertEqual(result["sentences"][0]["frame"]["kind"], "notice")
                    self.assertEqual(result["sentences"][-1]["frame"]["kind"], "ending")
                    self.assertGreaterEqual(len(result["sentences"]), 6)
                    self.assertLessEqual(len(result["sentences"]), 10)
                    state = set(final["entities"]["target"]["state"])
                    if scenario == "rescue":
                        self.assertTrue({"safe", "warm", "resting"} <= state)
                        self.assertFalse({"cold", "stranded", "frightened"} & state)
                    elif scenario == "kite":
                        self.assertTrue({"repaired", "flying"} <= state)
                        self.assertNotIn("torn", state)
                    else:
                        self.assertIn("found", state)
                        self.assertEqual(final["entities"]["door"]["state"], ["open"])
                        self.assertEqual(final["entities"]["hero"]["location"], "cottage")
                    kinds = tuple(s["frame"]["kind"] for s in result["sentences"])
                    signatures.add(kinds)
                    self.assertLess(kinds.index("solve"), kinds.index("finish"))
                    self.assertFalse("attempt" in kinds and kinds.index("attempt") >
                                     min(kinds.index(k) for k in ("ask", "think") if k in kinds))
                    counts.update(kinds)
                    # Replay from the actual preceding state to verify candidate legality.
                    world = make_world(scenario, seed)
                    for sentence in result["sentences"]:
                        frame = Frame(**{**sentence["frame"], "cause_ids": tuple(sentence["frame"]["cause_ids"])})
                        self.assertIn(frame, [f for _, f in frames(world)])
                        self.assertTrue(set(frame.cause_ids) <= set(world.facts))
                        commit(world, frame, sentence["text"])
                        lengths.add(sentence["word_count"])
                        self.assertNotIn("  ", sentence["text"])
                        self.assertNotIn(" .", sentence["text"])
                        for step in sentence["word_trace"]:
                            self.assertAlmostEqual(sum(c["probability"] for c in step["choices"]), 1)
                            self.assertTrue(all(c["probability"] > 0 for c in step["choices"]))
                            self.assertIn(step["selected"], {c["word"] for c in step["choices"]})
                            for candidate in step["choices"]:
                                structures.update(candidate["grammar_rules"])
                    self.assertEqual(world.to_dict(), final)
        self.assertEqual(set(counts), set(BY_NAME))
        self.assertGreater(len(signatures), 5)
        self.assertGreater(len(lengths), 10)
        self.assertGreater(len(structures), 20)


if __name__ == "__main__":
    unittest.main()
