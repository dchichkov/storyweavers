"""Check compiled batch gradients against execution and numerical derivatives."""

from copy import deepcopy
import math
from pathlib import Path
import tempfile
import unittest

from .grammar import Alt, Gap, GrammarNeuron, Ref, Rule, Seq, Token
from .learning import LearningBatch
from .learning_emulation import compact_pos_copies, compare, propose_carrier, propose_factored_carrier
from .neuron_review import VERSION, evaluate_proposal, model_fingerprint
from .neuron_spec import neuron_spec
from .neuron_review import metrics
from .transformer import GrammarHead, GrammarProjection, Storyformer, StoryformerBlock


class LearningTests(unittest.TestCase):
    def model(self):
        # Multiple matching derivations and a semantic distinction on one word.
        roots = {
            "a": GrammarNeuron("a", (
                Rule(Gap(2), dict(pos="n", flag=True), 2.),
                Rule(Gap(2), dict(pos="n", flag=False), 1.),
                Rule(Alt(Gap(2), Gap(2), weights=(1., 3.)), dict(pos="n", flag=True), .7))),
            "b": GrammarNeuron("b", (Rule(Gap(2), dict(pos="n", flag=False), 1.5),)),
        }
        return Storyformer(GrammarProjection(roots), num_layers=1, context_size=2, top_k=1)

    def documents(self):
        return [[dict(token="a", pos="n", flag=True), dict(token="b", pos="n", flag=False),
                 dict(token="a", pos="n", flag=False), dict(token="a", pos="n", flag=True)]]

    def test_full_target_loss_matches_executor_with_windowing_and_top_one(self):
        model, documents = self.model(), self.documents()
        original = deepcopy(documents)
        batch = LearningBatch(model, documents)
        self.assertEqual(documents, original)
        self.assertEqual(batch.targets, 4)
        self.assertAlmostEqual(batch.report()["joint_nll"], metrics(model, documents)["joint_nll"], places=12)
        for context, views, _, targets in batch.rows:
            self.assertEqual(views, model.forward(context).residual_stream)
        batch.fit(steps=15)
        self.assertAlmostEqual(batch.report()["joint_nll"], metrics(model, documents)["joint_nll"], places=12)

    def test_batch_update_matches_numerical_full_joint_log_weight_gradient(self):
        model, documents = self.model(), self.documents()
        batch = LearningBatch(model, documents)
        weights, gradients, epsilon = [r.weight for r in batch.rules], [], 1e-5
        for rule in batch.rules:
            old = rule.weight
            rule.weight = old * math.exp(epsilon)
            high = metrics(model, documents)["joint_nll"]
            rule.weight = old * math.exp(-epsilon)
            low = metrics(model, documents)["joint_nll"]
            rule.weight = old
            gradients.append(-(high - low) / (2 * epsilon))
        batch.fit(steps=1, learning_rate=.2)
        for old, rule, gradient in zip(weights, batch.rules, gradients):
            self.assertAlmostEqual(math.log(rule.weight / old), .2 * gradient, places=8)

    def test_stale_batches_and_unrepresentable_targets_fail_explicitly(self):
        model, documents = self.model(), self.documents()
        batch = LearningBatch(model, documents)
        model.projection.neurons["a"].rules[0].weight += 1
        with self.assertRaisesRegex(ValueError, "stale"):
            batch.fit(steps=1)
        documents[0][0]["flag"] = 1  # Numeric one is not boolean true.
        batch = LearningBatch(model, documents)
        self.assertLess(batch.report()["coverage"], 1)
        with self.assertRaisesRegex(ValueError, "support"):
            batch.fit(steps=1)

    def test_heads_are_not_updated_indirectly_through_shared_rule_weights(self):
        model = self.model()
        shared = model.projection.neurons["a"].rules[0]
        model.layers = (StoryformerBlock((GrammarHead(GrammarNeuron("shared", (shared,))),)),)
        with self.assertRaisesRegex(ValueError, "separate"):
            LearningBatch(model, self.documents())

    def test_pos_compaction_rewires_consumer_and_preserves_prediction(self):
        feature = "__grammar_1"
        head = GrammarHead(GrammarNeuron("copy_pos", (Rule(Seq(Gap(4), Token(pos="n")), {feature: True}),)))
        root = GrammarNeuron("a", (Rule(Gap(4), dict(pos="n")),
                                  Rule(Seq(Gap(4), Token(**{feature: True})), dict(pos="n"), 3.)))
        model = Storyformer(GrammarProjection({"a": root}), layers=(StoryformerBlock((head,)),), context_size=4,
                           features={feature: dict(type="boolean", origin="learned", description="noun detector")})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.json"
            model.save(path)
            model = Storyformer.load(path)
        revised, proposals = compact_pos_copies(model)
        self.assertEqual(len(proposals), 1)
        self.assertFalse(any(revised.layers[0].heads))
        for context in ([], [dict(token="a", pos="n")], [dict(token="a", pos="v")]):
            self.assertEqual(model.predict(context).to_dict(), revised.predict(context).to_dict())

    def test_carrier_reads_prefix_only_and_does_not_cross_clause_boundary(self):
        from .learning_emulation import FEATURE

        model = Storyformer(context_size=16)
        revised, _ = propose_carrier(model, [])
        head = revised.layers[0].heads[0].neuron
        rows = [dict(token=token, pos=pos) for token, pos in
                (("Lily", "pn"), ("ate", "v"), ("the", "det"), ("red", "adj"))]
        self.assertEqual(head.activate(rows)[0].value, {FEATURE: "ate"})
        self.assertFalse(head.activate(rows + [dict(token=".", pos="punct")]))
        old = deepcopy(rows)
        short = revised.forward(rows).residual_stream
        long = revised.forward(rows + [dict(token="apples", pos="n")]).residual_stream
        self.assertEqual(short, long[:len(rows)])
        self.assertEqual(rows, old)

    def test_factored_revision_preserves_noun_mass_and_learns_preferences_from_counts(self):
        from .induction import induce
        from .synthetic import make_corpus

        training = make_corpus(7, 64, 4, 4)["train"]
        source = induce(training, max_rules=8, weight_steps=2).model
        source, _ = compact_pos_copies(source)
        revised, proposal = propose_factored_carrier(source, training)
        self.assertTrue(proposal["replaced_rules"])
        for context, target in source.examples(training):
            if target["pos"] == "n":
                before = sum(row["probability"] for row in source.predict(context).joint if row["latent"]["pos"] == "n")
                after = sum(row["probability"] for row in revised.predict(context).joint if row["latent"]["pos"] == "n")
                self.assertAlmostEqual(before, after, places=12)
        self.assertGreater(proposal["probabilities"]["ate"]["apples"], proposal["probabilities"]["ate"]["scissors"])
        self.assertGreater(proposal["probabilities"]["used"]["scissors"], proposal["probabilities"]["used"]["apples"])

    def test_update_cannot_replace_a_better_unchanged_checkpoint(self):
        control = Storyformer(GrammarProjection({word: GrammarNeuron(word, (Rule(Gap(4), {"pos": "n"}),))
                                                 for word in ("a", "b")}), context_size=4)
        candidate = deepcopy(control)
        candidate.projection.neurons["b"].rules[0].weight = 2.
        fingerprint = model_fingerprint(control)
        with tempfile.TemporaryDirectory() as folder:
            selected, report = compare(candidate, control, [[dict(token="a", pos="n")]],
                                       [[dict(token="b", pos="n")]], Path(folder) / "round", steps=4)
        self.assertFalse(report["accepted"])
        self.assertEqual(report["adopted"], "unchanged")
        self.assertEqual(model_fingerprint(selected), fingerprint)

    def test_single_neuron_gate_also_checks_checkpoint_before_weight_fitting(self):
        model = Storyformer(GrammarProjection({word: GrammarNeuron(word, (Rule(Gap(4), {"pos": "n"}),))
                                               for word in ("a", "b")}), context_size=4)
        proposal = dict(format=VERSION, base_model_sha256=model_fingerprint(model),
                        address=dict(kind="output", token="b"), neuron=neuron_spec(model.projection.neurons["b"]),
                        feature_definitions={}, bindings=[], rationale="Keep grammar unchanged while updating weights.")
        _, report = evaluate_proposal(model, proposal, [[dict(token="a", pos="n")]],
                                      [[dict(token="b", pos="n")]], fit_epochs=1, learning_rate=4.)
        self.assertAlmostEqual(report["before"]["joint_nll"], report["after"]["joint_nll"])
        self.assertGreater(report["after"]["joint_nll"], report["unchanged"]["joint_nll"])
        self.assertFalse(report["accepted"])


if __name__ == "__main__":
    unittest.main()
