"""Expanded continuations must preserve typed structure and physical semantics."""
from collections import Counter
import unittest

from .grammar import Derivation, Forest, expand
from .world import Frame
from .storytelling.continuations import ExpandedLanguage
from .storytelling.head_adapter import StoryHeads
from .storytelling.head_comparison import validate
from .storytelling.runtime import SCENARIOS, build_forest, generate, setup
from .storytelling.surface import detokenize


class ContinuationTests(unittest.TestCase):
    def test_typed_inflection_polarity_and_complements(self):
        pack, w = setup("library", 7)
        g = ExpandedLanguage(w, lexicon=pack.LEXICON)
        def strings(sentence):
            return {detokenize(t) for t,_,_ in expand(sentence.node)}
        # Negative alternatives retain do-support and all references remain in
        # the negative scope, rather than establishing a discovered object.
        negative = g.s("hero", g.v("find", g.ref("book")), negative=True)
        outputs = strings(negative)
        self.assertTrue(any("did not locate" in t for t in outputs))
        self.assertTrue(all("did not" in t for t in outputs))
        for _, _, labels in expand(negative.node):
            self.assertFalse(any(x.startswith("referent:") for x in labels))
        present = strings(g.s("hero", g.v("sketch", g.n("moon")), tense="present"))
        self.assertTrue(any("draws the moon" in t for t in present))
        self.assertFalse(any("draw the moon" in t for t in present))
        transfers = strings(g.s("helper", g.v("give", g.ref("friend"), g.ref("book"))))
        self.assertTrue(any("gave Jun the whale book" in t for t in transfers))
        self.assertTrue(any("handed the whale book to Jun" in t for t in transfers))
        self.assertFalse(any("to the whale book" in t for t in transfers))

    def test_same_state_retains_original_support_claims_and_event_priors(self):
        checked = 0
        increased = set()
        for scenario in SCENARIOS:
            for seed in (0, 7):
                row = generate(scenario, seed)
                pack, w = setup(scenario, seed)
                for saved in row["final_world"]["history"]:
                    before = w.to_dict()
                    for tense in ("past", "present"):
                        old, old_plans = build_forest(pack, w, tense)
                        new, new_plans = build_forest(pack, w, tense, continuations="expanded")
                        self.assertEqual(w.to_dict(), before)
                        self.assertLessEqual(len(new.derivations), 512*len(new_plans))
                        masses = []
                        for forest in (old, new):
                            mass = Counter()
                            for d in forest.derivations:
                                mass[d.frame] += d.probability
                            masses.append(mass)
                        self.assertEqual(masses[0].keys(), masses[1].keys())
                        for frame in masses[0]:
                            self.assertAlmostEqual(masses[0][frame], masses[1][frame])
                            a, b = old_plans[frame], new_plans[frame]
                            self.assertEqual(a.claims if a else [], b.claims if b else [])
                        old_support = {(d.frame,d.tokens) for d in old.derivations}
                        new_support = {(d.frame,d.tokens) for d in new.derivations}
                        self.assertTrue(old_support <= new_support, scenario)
                        if new_support > old_support:
                            increased.add(scenario)
                        checked += 1
                    f = Frame(**{**saved["frame"], "cause_ids": tuple(saved["frame"]["cause_ids"])})
                    event = pack.commit(w, f, saved["sentence"])
                    for key in ("referents", "speakers", "narrated"):
                        event[key] = saved[key]
        self.assertGreater(checked, 200)
        self.assertEqual(increased, set(SCENARIOS))

    def test_expanded_sampling_qa_and_zero_strength(self):
        for scenario in SCENARIOS:
            for tense in ("past", "present"):
                for seed in (0, 7):
                    off = generate(scenario, seed, tense=tense, continuations="expanded")
                    on = generate(scenario, seed, tense=tense, continuations="expanded", symbolic_heads=True)
                    zero = generate(scenario, seed, tense=tense, continuations="expanded", symbolic_heads=True, head_strength=0)
                    self.assertEqual(off["story"], zero["story"])
                    validate(off)
                    validate(on)
                    self.assertNotIn("continuations", on["options"])
                    self.assertLess(len(on["story"].split()), 145)
        for seed in (0, 7):
            row = generate("music", seed, continuations="expanded", symbolic_heads=True,
                           partner_willing=False, head_strength=10)
            validate(row)
            self.assertNotIn("private_plan", row["final_world"]["flags"])

    def test_agreement_receiver_does_not_choose_copula_over_modal(self):
        _, w = setup("kite", 7)
        prefix = ("Nora", "said", ",", "“", "I")
        forest = Forest([Derivation(prefix+(word,), .5, Frame("test", "hero"), ()) for word in ("am", "can")], {})
        heads = StoryHeads(w, head_ids=["P001", "P002"])
        pred = heads.predict(forest, prefix, w, tense="past", available=[])
        self.assertTrue(all(c["probability"] == .5 for c in pred["choices"]))
        self.assertTrue(all(h["receiver_gate"] == "no_competing_agreement_forms" for h in pred["symbolic_heads"]))

    def test_fronted_tool_still_resolves_actor(self):
        _, w = setup("pottery", 7)
        self.assertEqual(StoryHeads.subject(w, ("With", "the", "sponge", ",", "Bea")), ("hero", False))


if __name__ == "__main__":
    unittest.main()
