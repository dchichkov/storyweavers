"""Grammar matching/projection, causal residual updates, and full-latent learning."""

from copy import deepcopy
import math
from pathlib import Path
import random
import tempfile
import unittest

from . import (Alt, Gap, GrammarHead, GrammarNeuron, GrammarProjection, Lookup, OneOf,
               Present, Ref, Repeat, Rule, Search, Seq, Storyformer, StoryformerBlock, Token)
from .demo import make_demo
from .grammar import MatchBudgetExceeded
from .transformer import JointDistribution, Residual, complete


def constant(word, weight=1., **attributes):
    return GrammarNeuron(word, (Rule(Gap(), attributes, weight),))


class GrammarTests(unittest.TestCase):
    def test_entire_context_nonlocal_capture_copy_and_lookup(self):
        grammar = GrammarNeuron("retrieve", (Rule(
            Seq(Token(bind="actor", entity=Present()), Gap(), Token(bind="v", lemma=OneOf(("take", "get")))),
            {"actor": Ref("actor.token"), "event": Lookup("events", Ref("v.lemma"))}, 3),),
            tables={"events": {"take": "obtain object"}})
        context = [{"token": "Lily", "entity": "girl"}, {"token": "slowly"}, {"token": "took", "lemma": "take"}]
        before = deepcopy(context)
        matches = grammar.activate(context)
        self.assertEqual([(m.value, m.mass) for m in matches], [({"actor": "Lily", "event": "obtain object"}, 3)])
        self.assertEqual(context, before)
        context[-1]["lemma"] = "get"  # Match but missing KV value abstains.
        self.assertEqual(grammar.activate(context), [])
        self.assertEqual(grammar.activate(context[:-1]), [])

    def test_normalized_alternatives_and_bounded_repetition(self):
        pattern = Repeat(Alt(Token(token="a"), Token(token="b"), weights=(3, 1)), 2, 2)
        grammar = GrammarNeuron("alternatives", (Rule(pattern, {"value": "yes"}),))
        self.assertEqual(grammar.activate([{"token": "a"}, {"token": "b"}])[0].mass, 3 / 16)
        self.assertEqual(grammar.activate([{"token": "a"}]), [])
        self.assertEqual(grammar.activate([{"token": "a"}] * 3), [])

    def test_search_and_capture_equality_and_nested_fields(self):
        grammar = GrammarNeuron("relative", (Rule(Search(Seq(
            Token(bind="first", **{"position.sentence": 0}),
            Token(token=Ref("first.token")))), {"copy": Ref("first.token")}),))
        rows = [{"token": "x", "position": {"sentence": 1}}, {"token": "a", "position": {"sentence": 0}},
                {"token": "a", "position": {"sentence": 0}}, {"token": "z"}]
        self.assertEqual([m.value for m in grammar.activate(rows)], [{"copy": "a"}])

    def test_invalid_weights_and_nullable_repeat_and_explicit_budget(self):
        for weight in (-1, 0, math.inf, math.nan):
            with self.assertRaises(ValueError):
                Rule(Token(), {}, weight)
        with self.assertRaises(ValueError):
            GrammarNeuron("nullable", (Rule(Repeat(Seq(), maximum=2), {}),)).activate([])
        with self.assertRaises(MatchBudgetExceeded):
            GrammarNeuron("bounded", (Rule(Gap(), {}),), max_states=2).activate([{"token": "a"}])


class BlockTests(unittest.TestCase):
    def test_add_suppress_conflict_unknown_and_protected_observations(self):
        rows = [Residual.from_latent({"token": "rabbit", "pos": "v", "position": {"token": 0}})]
        add = GrammarHead(GrammarNeuron("noun", (Rule(Token(), {"pos": "n"}, 3),)))
        suppress = GrammarHead(GrammarNeuron("verb", (Rule(Token(), {"pos": "v"}, 3),)), "suppress", 3)
        first, trace = StoryformerBlock((add, suppress)).forward(rows)
        second, _ = StoryformerBlock((suppress, add)).forward(rows)
        self.assertEqual(first[0].scores, second[0].scores)
        self.assertEqual(first[0].view()["pos"], "n")
        self.assertEqual(rows[0].view()["pos"], "v")
        self.assertGreater(next(v["probability"] for v in first[0].probabilities("pos") if v["value"] is None), 0)
        unknown, _ = StoryformerBlock((suppress,)).forward(rows)
        self.assertIsNone(unknown[0].view()["pos"])
        self.assertEqual(len(trace), 2)
        for attribute in ("token", "position", "index"):
            with self.assertRaises(ValueError):
                GrammarHead(GrammarNeuron("bad", (Rule(Token(), {attribute: "overwrite"}),)))

    def test_heads_share_snapshot_and_next_layer_can_read_new_attributes(self):
        make_actor = GrammarHead(GrammarNeuron("actor", (Rule(Token(), {"actor": "Lily"}),)))
        copy_actor = GrammarHead(GrammarNeuron("location", (Rule(Token(actor=Present()), {"location": Ref("query.actor")}),)))
        layer = StoryformerBlock((make_actor, copy_actor))
        stream = [Residual.from_latent({"token": "scissors", "position": {"token": 0}})]
        first, _ = layer.forward(stream)
        self.assertIsNone(first[0].view()["location"])
        second, _ = layer.forward(first)
        self.assertEqual(second[0].view()["location"], "Lily")
        self.assertEqual(len(layer.heads), 16)

    def test_disabled_heads_and_weak_match_remain_neutral_or_uncertain(self):
        neuron = GrammarNeuron("weak", (Rule(Token(), {"location": "Lily"}, .001),))
        stream = [Residual.from_latent({"token": "scissors", "position": {"token": 0}})]
        identity, trace = StoryformerBlock((GrammarHead(neuron, strength=0),)).forward(stream)
        self.assertEqual(identity, stream)
        self.assertEqual(trace, [])
        changed, _ = StoryformerBlock((GrammarHead(neuron),)).forward(stream)
        p = next(row["probability"] for row in changed[0].probabilities("location") if row["value"] == "Lily")
        self.assertLess(p, .501)


class ProjectionTests(unittest.TestCase):
    def test_joint_bundle_correlations_and_duplicate_derivation_mass(self):
        grammar = GrammarNeuron("scissors", (
            Rule(Gap(), {"role": "patient", "location": "Lily"}, 2),
            Rule(Gap(), {"role": "patient", "location": "Lily"}, 1),
            Rule(Gap(), {"role": "instrument", "location": "Ben"}, 1)))
        p = GrammarProjection({"scissors": grammar, "needle": constant("needle", 2)}).read([])
        self.assertEqual(p.probabilities, {"scissors": 4 / 6, "needle": 2 / 6})
        scissors = [row for row in p.joint if row["latent"]["token"] == "scissors"]
        self.assertEqual(len(scissors), 2)
        self.assertEqual({(r["latent"]["role"], r["latent"]["location"]) for r in scissors},
                         {("patient", "Lily"), ("instrument", "Ben")})
        self.assertEqual(sum(row["probability"] for row in p.joint), 1)

    def test_top_ten_marginalizes_before_cut_and_keeps_attribute_alternatives(self):
        roots = {f"word{i:02d}": constant(f"word{i:02d}", i + 1) for i in range(12)}
        p = GrammarProjection(roots).read([])
        self.assertEqual(len(p.probabilities), 10)
        self.assertEqual(next(iter(p.probabilities)), "word11")
        self.assertAlmostEqual(p.retained_mass, 75 / 78)
        self.assertAlmostEqual(sum(p.probabilities.values()), 1)
        self.assertAlmostEqual(p.probability(complete({"token": "word00"})), 1 / 78)
        self.assertNotIn("word00", p.probabilities)

    def test_full_target_distinguishes_wrong_attributes_and_empty_support(self):
        p = GrammarProjection({"scissors": constant("scissors", location="Lily")}).read([])
        self.assertEqual(p.probability(complete({"token": "scissors", "location": "Lily"})), 1)
        self.assertEqual(p.probability(complete({"token": "scissors", "location": "Ben"})), 0)
        self.assertEqual(JointDistribution([]).probabilities, {})
        with self.assertRaises(ValueError):
            JointDistribution([]).sample()
        bad = GrammarProjection({"scissors": GrammarNeuron("bad", (Rule(Gap(), {"token": "needle"}),))})
        with self.assertRaises(ValueError):
            bad.read([])


class StoryformerTests(unittest.TestCase):
    def test_demo_layers_change_complete_candidate_distributions(self):
        model, context = make_demo()
        before = deepcopy(context)
        result = model.forward(context)
        self.assertEqual(context, before)
        self.assertEqual([len(layer.heads) for layer in model.layers], [16, 16])
        self.assertEqual(len(result.residual_stream), 5)
        self.assertEqual(result.residual_stream[-1]["actor"], "Lily")
        self.assertEqual(result.residual_stream[-1]["event"], "obtain tool")
        full = next(row["latent"] for row in result.next_latent.candidates
                    if row["latent"]["token"] == "scissors" and row["latent"]["location"] == "Lily")
        self.assertEqual(full["role"], "patient")
        baseline = Storyformer(model.projection).predict(context)
        self.assertAlmostEqual(baseline.probabilities["scissors"], 1 / 3)
        self.assertGreater(result.next_latent.probabilities["scissors"], .58)
        self.assertFalse(any(e["neuron"] == "predicate_event" for e in result.trace if e["layer"] == 0))

    def test_causality_and_context_clipping_preserve_global_positions(self):
        head = GrammarHead(GrammarNeuron("remember", (Rule(Search(Token(bind="source", token="future")),
                                                           {"event": Ref("source.token")}),)))
        model = Storyformer(layers=(StoryformerBlock((head,)),))
        prefix = [{"token": "a"}, {"token": "b"}]
        short = model.forward(prefix)
        long = model.forward([*prefix, {"token": "future"}])
        self.assertEqual(short.residual_stream, long.residual_stream[:2])
        bounded = Storyformer(GrammarProjection({"x": constant("x")}), context_size=2)
        row = bounded.forward([{"token": word} for word in ("a", ".", " ", "b", "c")])
        self.assertEqual([v["position"]["token"] for v in row.residual_stream], [3, 4])
        self.assertEqual(row.next_latent.candidates[0]["latent"]["position"], {"token": 5, "sentence": 1, "in_sentence": 2})

    def test_generation_reuses_complete_predicted_attributes(self):
        roots = {"tool": GrammarNeuron("tool", (Rule(Seq(), {"entity": "scissors", "location": "Lily"}),)),
                 "worked": GrammarNeuron("use", (Rule(Seq(Gap(), Token(entity="scissors", location="Lily")),
                                                       {"pos": "v", "event": "repair"}),))}
        model = Storyformer(GrammarProjection(roots))
        generated = model.generate([], 2, seed=1)
        self.assertEqual([row["token"] for row in generated], ["tool", "worked"])
        self.assertEqual(generated[0]["location"], "Lily")
        self.assertTrue(all(all(key in row for key in ("token", "pos", "entity", "role", "location", "event", "position")) for row in generated))

    def test_fit_learns_full_bundle_weights_and_uses_pre_top_k_mass(self):
        neuron = GrammarNeuron("ambiguous", (Rule(Gap(), {"location": "Lily"}), Rule(Gap(), {"location": "Ben"})))
        model = Storyformer(GrammarProjection({"scissors": neuron, "needle": constant("needle", 5)}), top_k=1)
        documents = [[{"token": "scissors", "location": "Lily"}]]
        before = model.loss(documents)
        model.fit(documents, epochs=30, learning_rate=.3)
        self.assertLess(model.loss(documents), before / 4)
        self.assertGreater(neuron.rules[0].weight, neuron.rules[1].weight)
        self.assertEqual(model.predict([]).probabilities, {"scissors": 1})
        with self.assertRaises(ValueError):
            model.fit([[{"token": "missing"}]])
        tied_to_head = Storyformer(model.projection, layers=(StoryformerBlock((GrammarHead(neuron),)),))
        with self.assertRaisesRegex(ValueError, "separate from attention"):
            tied_to_head.fit(documents)

    def test_checkpoint_preserves_grammar_lookup_heads_weights_and_predictions(self):
        model, context = make_demo()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.json"
            model.save(path)
            restored = Storyformer.load(path)
        self.assertEqual(restored.predict(context).to_dict(), model.predict(context).to_dict())
        self.assertEqual(restored.forward(context).trace, model.forward(context).trace)
        self.assertEqual(restored.generate(context, 2, seed=4), model.generate(context, 2, seed=4))

    def test_checkpoint_preserves_shared_neurons_and_parameter_learning(self):
        shared = constant("shared")
        model = Storyformer(GrammarProjection({"a": shared, "b": shared, "c": constant("c")}))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "shared.json"
            model.save(path)
            restored = Storyformer.load(path)
        self.assertIs(restored.projection.neurons["a"], restored.projection.neurons["b"])
        data = [[{"token": "a"}]]
        model.fit(data, epochs=5)
        restored.fit(data, epochs=5)
        self.assertEqual(model.predict([]).to_dict(), restored.predict([]).to_dict())

    def test_block_accepts_latent_dictionaries_directly(self):
        head = GrammarHead(GrammarNeuron("object", (Rule(Token(), {"role": "patient"}),)))
        stream, _trace = StoryformerBlock((head,)).forward([{"token": "scissors"}])
        self.assertEqual(stream[0].view()["role"], "patient")
        self.assertEqual(stream[0].view()["position"]["token"], 0)


if __name__ == "__main__":
    unittest.main()
