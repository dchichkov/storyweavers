"""Behavioral checks for the Python port and its original weighted sampler."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import random
import unittest

from grammarworlds.grammar import detokenize, expand
from grammarworlds.portable import language, nouns
from grammarworlds.portable.catalog import RULES, context
from grammarworlds.portable.discourse import Discourse
from grammarworlds.portable.runtime import build_forest, generate, sample_sentence, setup
from grammarworlds.world import Frame


def surfaces(sentence):
    return {detokenize(tokens) for tokens, _, _ in expand(language.Language.utter(sentence))}


class PortableGrammarTests(unittest.TestCase):
    def setUp(self):
        _, self.world = setup("music", 7)
        self.g = language.Language(self.world)

    def test_complement_types_prevent_hoped_a_duet(self):
        g = self.g
        with self.assertRaises(TypeError):
            g.v("hope", g.n("duet", det="a"))
        self.assertEqual(surfaces(g.s("hero", g.v("hope", g.v("play", g.n("duet", det="a"))))),
                         {"Nia hoped to play a duet."})
        with self.assertRaises(TypeError):
            g.s("hero", g.n("duet"))

    def test_number_person_case_possession_and_polarity(self):
        g = self.g
        players = g.both(g.ref("hero"), g.ref("partner"))
        self.assertEqual(surfaces(g.s(players, g.be("ready"))), {"Nia and Mateo were ready."})
        self.assertEqual(surfaces(g.s(players, g.v("play"), negative=True, tense="present")),
                         {"Nia and Mateo do not play."})
        self.assertEqual(surfaces(g.s(nouns.pronoun("I"), g.be("ready"), tense="present")), {"I am ready."})
        self.assertEqual(surfaces(g.s("hero", g.v("thank", nouns.pronoun("he")))), {"Nia thanked him."})
        self.assertEqual(surfaces(g.s("hero", g.v("return", g.possess(nouns.pronoun("he"), g.cn("drum"))))),
                         {"Nia returned his drum."})
        self.assertEqual(surfaces(g.s("hero", g.v("notice", g.possess(g.ref("partner"), g.cn("drum"))))),
                         {"Nia noticed Mateo's drum."})

    def test_article_and_irregulars(self):
        g = self.g
        self.assertEqual(surfaces(g.s("hero", g.v("find", g.n("answer", det="a")))), {"Nia found an answer."})
        self.assertEqual(surfaces(g.s("hero", g.v("find", g.n("drum", "empty", det="a")))), {"Nia found an empty drum."})
        with self.assertRaises(ValueError):
            g.n("tape", det="a")
        self.assertEqual(surfaces(g.s(g.n("shelf", number="plural"), g.be("empty"))), {"The shelves were empty."})
        self.assertEqual(surfaces(g.s("hero", g.v("open", g.n("door")))), {"Nia opened the door."})

    def test_saved_gf_reference_sentences(self):
        # Expectations were produced once by real GF/RGL. No GF import or
        # compiler is required to check the independent Python port.
        root = Path(language.__file__).parent
        cases = json.loads((root / "sources/gf_oracle.json").read_text())["cases"]
        g = self.g
        for case in cases:
            kind = case["kind"]
            if kind in {"transitive", "copula"}:
                subject = nouns.proper("Nia") if case["subject"] == "Nia" else nouns.pronoun(case["subject"])
                action = g.be("ready") if kind == "copula" else g.v(case["verb"], g.n(case["noun"]))
                sentence = g.s(subject, action, tense=case["tense"], negative=case["negative"])
            elif kind == "intention":
                sentence = g.s("hero", g.v("hope", g.v("play", g.n("duet", det="a"))))
            elif kind == "possession":
                sentence = g.s("hero", g.v("return", g.possess(nouns.pronoun("she"), g.cn("drum"))))
            else:
                sentence = g.s("hero", g.v("bring", nouns.pronoun("he"), g.n("drum")))
            with self.subTest(case=case):
                # RGL's default negative polarity contracts; our documented
                # subset chooses uncontracted forms and capitalizes sentences.
                expected = case["expected"]
                for short, full in {"didn't": "did not", "doesn't": "does not", "don't": "do not",
                                    "isn't": "is not", "aren't": "are not", "wasn't": "was not", "weren't": "were not"}.items():
                    expected = expected.replace(short, full)
                expected = expected[:1].upper() + expected[1:]
                self.assertEqual(surfaces(sentence), {expected})

    def test_scopes_and_feature_unification(self):
        d = Discourse()
        self.assertEqual(d.resolve(pronoun="it"), [])
        d.introduce("drum", pronoun="it", number="singular")
        d.push(); d.introduce("hypothetical_ladder", pronoun="it", number="singular")
        self.assertEqual(d.resolve(pronoun="it"), ["hypothetical_ladder", "drum"])
        self.assertEqual(d.resolve(number="plural"), [])
        d.pop()
        self.assertEqual(d.resolve(pronoun="it"), ["drum"])
        with self.assertRaises(ValueError):
            d.pop()
        # A negative embedded mention is not exported as an antecedent.
        node = language.Language.utter(self.g.s("hero", self.g.v("notice", self.g.ref("spare")), negative=True))
        rules = {r for _, _, path in expand(node) for r in path}
        self.assertNotIn("referent:spare", rules)
        self.assertIn("scoped_referent:spare", rules)

    def test_prediction_is_pure_and_provenance_is_preserved(self):
        pack, world = setup("rescue", 2)
        before = deepcopy(world.to_dict())
        forest = build_forest(pack, world)
        self.assertEqual(before, world.to_dict())
        for d in forest.derivations:
            self.assertIn("gf.UseCl", d.rules)
            self.assertIn("gf.PredVP", d.rules)
            self.assertIn("gf.DetCN", d.rules)
        self.assertAlmostEqual(sum(x["probability"] for x in forest.predict(())["choices"]), 1)
        self.assertFalse(forest.predict(("ungrounded",))["choices"])

    def test_same_kernel_different_frames_keep_separate_priors(self):
        pack, world = setup("music", 7, partner_willing=True)
        rng = random.Random(7)
        for _ in range(24):
            forest = build_forest(pack, world)
            returns = {d.frame for d in forest.derivations if d.frame.kind == "return"}
            if len(returns) == 2:
                masses = {f: sum(d.probability for d in forest.derivations if d.frame == f) for f in returns}
                self.assertEqual(len(forest.evidence), 2)
                self.assertAlmostEqual(sum(masses.values()), 1)
                self.assertTrue(all(p > 0 for p in masses.values()))
                return
            sample_sentence(pack, world, rng)
        self.fail("seed did not reach the two-instrument return state")

    def test_all_worlds_two_tenses_and_replay(self):
        for scenario in ("rescue", "kite", "key", "music", "heldout"):
            for tense in ("past", "present"):
                for seed in range(5):
                    result = generate(scenario, seed, tense=tense)
                    pack, world = setup(scenario, seed)
                    for sentence in result["sentences"]:
                        f = Frame(**{**sentence["frame"], "cause_ids": tuple(sentence["frame"]["cause_ids"])})
                        event = pack.commit(world, f, sentence["text"])
                        event["referents"] = sentence["referents"]
                        for step in sentence["word_trace"]:
                            self.assertAlmostEqual(sum(c["probability"] for c in step["choices"]), 1)
                    self.assertEqual(world.to_dict(), result["final_world"])
                    self.assertTrue(world.finished)

    def test_context_budget_and_dependency_closure(self):
        result = context("sentence negation", budget=2000)
        self.assertTrue(result["selected"])
        self.assertLessEqual(result["characters"], 2000)
        selected = set(result["selected"])
        self.assertTrue(all(set(RULES[k]["dependencies"]) <= selected for k in selected))
        # Metadata-only scale check: unrelated rule entries do not enter prompts.
        large = dict(RULES)
        for i in range(100_000):
            name = f"unrelated.{i}"
            large[name] = {"signature": name + "()", "contract": "unrelated", "dependencies": [], "tags": []}
        big = context("sentence negation", budget=2000, rules=large)
        self.assertEqual(result["context"], big["context"])

    def test_heldout_did_not_edit_frozen_shared_rules(self):
        root = Path(language.__file__).parent
        freeze = json.loads((root / "sources/pre_holdout_freeze.json").read_text())
        for name, expected in freeze["sha256"].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(hashlib.sha256((root / "lexicon/core.json").read_bytes()).hexdigest(), freeze["core_lexicon_sha256"])


if __name__ == "__main__":
    unittest.main()
