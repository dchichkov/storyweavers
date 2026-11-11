"""Data-only proposal learning, causal compilation, and held-out evaluation."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from .grammar import GrammarNeuron, Rule, canonical
from .induction import Atom, Clause, examples, induce
from .synthetic import evaluate, make_corpus, run
from .transformer import Storyformer


class DataTests(unittest.TestCase):
    def test_reproducible_compositional_split_without_shared_documents(self):
        corpus = make_corpus(7, 64, 16, 16)
        self.assertEqual(corpus, make_corpus(7, 64, 16, 16))
        self.assertNotEqual(corpus, make_corpus(8, 64, 16, 16))
        documents, pairs = {}, {}
        for split, rows in corpus.items():
            documents[split] = {canonical(doc) for doc in rows}
            pairs[split] = {(doc[0]["token"], next(row["token"] for row in doc if row["pos"] == "v"))
                            for doc in rows}
            self.assertTrue(all(set(row) == {"token", "pos"} for doc in rows for row in doc))
        for first, second in (("train", "validation"), ("train", "test"), ("validation", "test")):
            self.assertFalse(documents[first] & documents[second])
            self.assertFalse(pairs[first] & pairs[second])
        vocabulary = {canonical(row) for doc in corpus["train"] for row in doc}
        self.assertTrue(all(canonical(row) in vocabulary for doc in corpus["test"] for row in doc))

    def test_targets_and_their_pos_never_enter_their_own_prefix(self):
        document = [dict(token=word, pos=pos) for word, pos in (("Lily", "pn"), ("took", "v"), ("scissors", "n"))]
        pairs = list(examples([document], context_size=1))
        self.assertEqual(pairs[0], ([], document[0]))
        self.assertEqual(pairs[-1], ([document[1]], document[2]))
        with self.assertRaises(ValueError):
            induce([[dict(token="took", pos="v", obj="scissors")]])
        with self.assertRaises(ValueError):
            induce([[dict(token="took", pos=None)]])

    def test_clause_and_compiled_grammar_agree_on_offsets_and_short_prefixes(self):
        clause = Clause((Atom(-3, "pos", "pn"), Atom(-1, "token", "took")))
        neuron = GrammarNeuron("candidate", (Rule(clause.pattern(8), {"match": True}),))
        row = lambda word, pos: dict(token=word, pos=pos)
        for context in ([], [row("took", "v")], [row("Lily", "pn"), row("quickly", "adv"), row("took", "v")],
                        [row("extra", "n"), row("Ben", "pn"), row("slowly", "adv"), row("took", "v")],
                        [row("Lily", "n"), row("quickly", "adv"), row("took", "v")]):
            self.assertEqual(bool(neuron.activate(context)), clause.matches(context))
        empty = GrammarNeuron("start", (Rule(Clause().pattern(8), {}),))
        self.assertTrue(empty.activate([]))
        self.assertFalse(empty.activate([row("Lily", "pn")]))


class InductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = make_corpus(11, 64, 12, 12)
        cls.result = induce(cls.corpus["train"], max_rules=10, weight_steps=40)

    def test_learned_residual_layer_improves_unseen_combinations(self):
        result, test = self.result, self.corpus["test"]
        learned, baseline = evaluate(result.model, test), evaluate(result.unigram, test)
        self.assertLess(learned["joint_nll"], baseline["joint_nll"] * .65)
        self.assertGreater(learned["pos_accuracy"], baseline["pos_accuracy"] + .4)
        self.assertEqual(learned["coverage"], 1)
        self.assertEqual(len(result.model.layers), 1)
        self.assertEqual(len(result.model.layers[0].heads), 16)
        self.assertTrue(any(atom["field"] == "pos" for rule in result.rules for atom in rule["atoms"]))
        self.assertTrue(all(next_nll < nll for nll, next_nll in zip(result.history, result.history[1:])))

    def test_removing_heads_changes_predictions_and_worsens_loss(self):
        ablated = deepcopy(self.result.model)
        ablated.layers[0].heads = (None,) * 16
        self.assertGreater(evaluate(ablated, self.corpus["test"])["joint_nll"],
                           evaluate(self.result.model, self.corpus["test"])["joint_nll"] + .5)
        prefix = self.corpus["test"][0][:3]
        original = deepcopy(prefix)
        result = self.result.model.forward(prefix)
        self.assertTrue(result.trace)
        self.assertTrue(any(key.startswith("__grammar_") for key in result.residual_stream[-1]))
        self.assertEqual(prefix, original)

    def test_compilation_matches_the_selection_objective(self):
        result = induce(self.corpus["train"][:24], max_rules=6, weight_steps=0, min_support=3)
        self.assertAlmostEqual(evaluate(result.model, self.corpus["train"][:24])["joint_nll"],
                               result.history[-1], places=10)

    def test_feature_names_have_no_predefined_english_meaning(self):
        tags = {pos: f"class_{index}" for index, pos in enumerate(
            sorted({row["pos"] for doc in self.corpus["train"] for row in doc}))}
        renamed = [[dict(token=row["token"], pos=tags[row["pos"]]) for row in doc]
                   for doc in self.corpus["train"][:32]]
        result = induce(renamed, max_rules=8, min_support=3, weight_steps=0)
        self.assertTrue(any(atom["field"] == "pos" for rule in result.rules for atom in rule["atoms"]))
        self.assertTrue(all(atom["value"].startswith("class_") for rule in result.rules
                            for atom in rule["atoms"] if atom["field"] == "pos"))

    def test_validation_veto_uses_held_out_likelihood_without_adding_vocabulary(self):
        result = induce(self.corpus["train"], validation_documents=self.corpus["validation"],
                        max_rules=16, weight_steps=0)
        self.assertTrue(result.rules)
        self.assertTrue(all(rule["validation_gain_nats"] > 0 for rule in result.rules))
        self.assertTrue(all(after < before for before, after in
                            zip(result.validation_history, result.validation_history[1:])))
        self.assertAlmostEqual(evaluate(result.model, self.corpus["validation"])["joint_nll"],
                               result.validation_history[-1], places=10)
        self.assertEqual(result.vocabulary, self.result.vocabulary)
        with self.assertRaisesRegex(ValueError, "outside training vocabulary"):
            induce(self.corpus["train"], validation_documents=[[dict(token="unseen", pos="unknown")]])
        with self.assertRaises(ValueError):
            induce(self.corpus["train"], validation_documents=[])

    def test_conjunctions_can_be_discovered_and_ambiguous_pos_is_joint(self):
        documents = [[dict(token=a, pos="X"), dict(token=b, pos="Y"),
                      dict(token="yes" if a == "a" and b == "b" else "no", pos="Z")]
                     for _ in range(8) for a in ("a", "c") for b in ("b", "d")]
        result = induce(documents, max_rules=12, min_support=2, complexity=0, weight_steps=0)
        self.assertTrue(any(len(rule["atoms"]) == 2 for rule in result.rules))
        ambiguous = [[dict(token="we", pos="pn"), dict(token="saw", pos="v")],
                     [dict(token="the", pos="det"), dict(token="saw", pos="n")]] * 8
        model = induce(ambiguous, max_rules=6, min_support=2, weight_steps=10).model
        context = [dict(token="we", pos="pn")]
        saw = {row["latent"]["pos"]: row["probability"] for row in model.predict(context).joint
               if row["latent"]["token"] == "saw"}
        self.assertEqual(set(saw), {"n", "v"})
        self.assertGreater(saw["v"], saw["n"])

    def test_checkpoint_and_causal_suffix_invariance(self):
        prefix = self.corpus["test"][0][:3]
        short = self.result.model.forward(prefix)
        long = self.result.model.forward(self.corpus["test"][0])
        self.assertEqual(short.residual_stream, long.residual_stream[:3])
        self.assertEqual(short.next_latent.to_dict(), long.predictions[2].to_dict())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "learned.json"
            self.result.model.save(path)
            loaded = Storyformer.load(path)
        self.assertEqual(loaded.predict(prefix).to_dict(), short.next_latent.to_dict())

    def test_explicit_bounds_and_unsupported_vocabulary(self):
        for options in (dict(lookback=0), dict(max_rules=17), dict(max_literals=0), dict(weight_steps=-1)):
            with self.assertRaises(ValueError):
                induce(self.corpus["train"], **options)
        with self.assertRaisesRegex(ValueError, "proposal budget"):
            induce(self.corpus["train"], max_proposals=1)
        with self.assertRaises(ValueError):
            induce([])
        result = induce(self.corpus["train"][:4], max_rules=0, weight_steps=0)
        self.assertEqual(result.rules, [])
        self.assertEqual(result.model.predict([]).to_dict(), result.unigram.predict([]).to_dict())
        metrics = evaluate(result.model, [[dict(token="unseen", pos="unknown")]])
        self.assertEqual(metrics["coverage"], 0)
        self.assertIsNone(metrics["joint_nll"])

    def test_small_run_writes_inspectable_corpus_checkpoint_and_report(self):
        with tempfile.TemporaryDirectory() as folder:
            report, result = run(train=24, validation=3, test=3, max_rules=4, weight_steps=4, out=folder)
            saved = json.loads((Path(folder) / "report.json").read_text())
            self.assertEqual(saved, report)
            rows = [json.loads(line) for line in (Path(folder) / "train.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 24)
            self.assertTrue(all(set(row) == {"token", "pos"} for doc in rows for row in doc))
            loaded = Storyformer.load(Path(folder) / "model.json")
            self.assertEqual(loaded.predict(rows[0][:2]).to_dict(), result.model.predict(rows[0][:2]).to_dict())


if __name__ == "__main__":
    unittest.main()
