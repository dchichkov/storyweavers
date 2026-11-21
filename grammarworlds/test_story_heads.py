"""Causal interventions and end-to-end checks for live symbolic word heads."""
import math
import unittest

from .grammar import Derivation, Forest
from .world import Frame
from .symbolic_heads import ProgramRequired, load_library
from .storytelling.head_adapter import StoryHeads
from .storytelling.runtime import SCENARIOS, generate, replay, setup, build_forest
from .storytelling.qa import questions


class StoryHeadsTests(unittest.TestCase):
    def test_carrier_intervention_at_fixed_prefix_and_grammar(self):
        _, w = setup("kite", 7)
        prefix = ("Nora", "said", ",", "“", "I")
        forest = Forest([Derivation(prefix+(word,), .5, Frame("test", "hero"), ())
                         for word in ("want", "can")], {})
        heads = StoryHeads(w, head_ids=["P059"])
        w.entities["hero"].memes = {"Fear": .9}
        before = w.to_dict()
        high = heads.predict(forest, prefix, w, tense="past", available=[])
        self.assertEqual(w.to_dict(), before)
        w.entities["hero"].memes = {"Fear": .1}
        low = heads.predict(forest, prefix, w, tense="past", available=[])
        probabilities = lambda p: {c["word"]: c["probability"] for c in p["choices"]}
        self.assertLess(probabilities(high)["can"], probabilities(low)["can"])
        self.assertEqual(high["symbolic_heads"][0]["features"], {"Fear:high": 1})
        self.assertIn("entity:hero:memes:Fear", high["symbolic_heads"][0]["sources"][0]["source_id"])
        del w.entities["hero"]
        absent = heads.predict(forest, prefix, w, tense="past", available=[])
        self.assertEqual(probabilities(absent), {"can": .5, "want": .5})
        self.assertEqual(absent["symbolic_heads"], [])

    def test_tool_intervention_and_unchanged_grammar_support(self):
        pack, w = setup("pottery", 7)
        row = generate("pottery", 7)
        tested = False
        for event in row["final_world"]["history"]:
            forest, _ = build_forest(pack, w)
            heads = StoryHeads(w, head_ids=["P023"])
            prefixes = {d.tokens[:i] for d in forest.derivations for i in range(1, len(d.tokens))}
            for prefix in sorted(prefixes):
                p = heads.predict(forest, prefix, w, tense="past", available=pack.candidates(w))
                if p["head_total_variation"] < 1e-10:
                    continue
                before = w.to_dict()
                off = heads.predict(forest, prefix, w, tense="past", available=[])
                base = forest.predict(prefix)
                self.assertEqual(off["choices"], [{**c, "grammar_probability": c["probability"]} for c in base["choices"]])
                self.assertEqual({c["word"] for c in p["choices"]}, {c["word"] for c in base["choices"]})
                probs = {c["word"]: c["probability"] for c in p["choices"]}
                self.assertAlmostEqual(probs["used"], .7/2.7)
                self.assertEqual(w.to_dict(), before)
                # The same prefix/world/available union gives identical head
                # signals regardless of future derivation order or labels.
                reversed_forest = Forest(list(reversed(forest.derivations)), {})
                other = heads.predict(reversed_forest, prefix, w, tense="past", available=list(reversed(pack.candidates(w))))
                self.assertEqual(p["symbolic_heads"], other["symbolic_heads"])
                tested = True
                break
            if tested:
                break
            f = Frame(**{**event["frame"], "cause_ids": tuple(event["frame"]["cause_ids"])})
            record = pack.commit(w, f, event["sentence"])
            for k in ("referents", "speakers", "narrated"):
                record[k] = event[k]
        self.assertTrue(tested)

    def test_subject_scope_ambiguity_and_quote_speaker(self):
        _, w = setup("music", 7)
        self.assertEqual(StoryHeads.subject(w, ("She",)), (None, False))
        self.assertEqual(StoryHeads.subject(w, ("Mateo", "said", ",", "“", "I")), ("partner", True))
        self.assertEqual(StoryHeads.subject(w, ("Nia", "saw", "Mateo")), (None, False))
        self.assertEqual(StoryHeads.subject(w, ("Nia", "said", ",", "“", "I", "want", "to")), (None, True))

    def test_all_worlds_and_tenses_replay_grounded_qa_zero_strength(self):
        changed = set()
        for scenario in SCENARIOS:
            for tense in ("past", "present"):
                base = generate(scenario, 7, tense=tense)
                zero = generate(scenario, 7, tense=tense, symbolic_heads=True, head_strength=0)
                self.assertEqual(base["story"], zero["story"])
                self.assertEqual(base["final_world"], zero["final_world"])
                row = generate(scenario, 7, tense=tense, symbolic_heads=True)
                self.assertTrue(replay(row))
                self.assertNotIn("symbolic_heads", row["options"])
                qa = questions(row)
                self.assertGreaterEqual(len(qa), 5)
                self.assertEqual(len(qa), len({q["question"] for q in qa}))
                self.assertGreaterEqual(len({q["kind"] for q in qa}), 3)
                for q in qa:
                    for e in q["evidence"]:
                        self.assertEqual(row["story"][e["start"]:e["end"]], e["text"])
                for event in row["trace"]:
                    self.assertAlmostEqual(event["probability"], math.prod(p["selected_probability"] for p in event["word_trace"]))
                    for p in event["word_trace"]:
                        self.assertAlmostEqual(sum(c["probability"] for c in p["choices"]), 1)
                        self.assertTrue(all(c["probability"] > 0 and c["grammar_probability"] > 0 for c in p["choices"]))
                        if p["head_total_variation"] > 1e-10:
                            changed.add(tense)
        self.assertEqual(changed, {"past", "present"})

    def test_consent_guards_with_heads(self):
        for seed in range(5):
            row = generate("music", seed, symbolic_heads=True, head_strength=10, partner_willing=False)
            self.assertTrue(replay(row))
            self.assertNotIn("Nia and Mateo played", row["story"])
            self.assertFalse(any("private duet" in (q["question"]+q["answer"]).lower() for q in questions(row, 50)))

    def test_original_seeds_unchanged_and_deferred_heads_explicit(self):
        before = load_library().describe("P059")
        _, w = setup("music", 7)
        heads = StoryHeads(w)
        self.assertEqual(before, load_library().describe("P059"))
        self.assertEqual(len(heads.metadata()["awaiting_adapter"]), 9)
        with self.assertRaises(ProgramRequired):
            StoryHeads(w, head_ids=["P024"])
        for strength in (-1, float("nan"), float("inf"), 11):
            with self.assertRaises(ValueError):
                StoryHeads(w, strength=strength)


if __name__ == "__main__":
    unittest.main()
