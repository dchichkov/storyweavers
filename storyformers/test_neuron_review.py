"""Neuron evidence, typed revisions, consumer rewiring and acceptance gates."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock

from .grammar import Alt, Gap, GrammarNeuron, Lookup, OneOf, Ref, Rule, Seq, Token
from .induction import induce
from .neuron_review import (collect, evaluate_proposal, locate, metrics, model_fingerprint,
                            proposal_template, stage)
from .neuron_spec import check_value, neuron_spec, parse_neuron, registry_for
from .refine import load_documents, propose, revision_request
from .synthetic import make_corpus
from .transformer import GrammarHead, GrammarProjection, JointDistribution, Storyformer, StoryformerBlock


class TypedGrammarTests(unittest.TestCase):
    def test_known_full_story_annotations_are_not_used_as_causal_training_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "annotations.json"
            document = [dict(token="Lily", pos="n")]
            path.write_text(json.dumps(document))
            metadata = path.with_name("metadata.json")
            metadata.write_text(json.dumps(dict(annotation_mode="full_story_offline")))
            with self.assertRaises(ValueError):
                load_documents(path)
            metadata.write_text(json.dumps(dict(annotation_mode="prefix_last_word")))
            self.assertEqual(load_documents(path), [document])

    def test_boolean_is_distinct_from_number_in_matching_and_target_scoring(self):
        literal = GrammarNeuron("bool", (Rule(Token(flag=True), {"ok": True}),))
        choice = GrammarNeuron("one_of", (Rule(Token(flag=OneOf((True,))), {"ok": True}),))
        for neuron in (literal, choice):
            self.assertTrue(neuron.activate([dict(token="x", flag=True)]))
            self.assertFalse(neuron.activate([dict(token="x", flag=1)]))
        p = JointDistribution([(dict(token="x", flag=True), 1)])
        self.assertEqual(p.probability(dict(token="x", flag=1)), 0)
        self.assertEqual(p.probability(dict(token="x", flag=True)), 1)
        with self.assertRaises(ValueError):
            check_value("true", dict(type="boolean"))
        with self.assertRaises(ValueError):
            check_value(1, dict(type="boolean"))

    def test_readable_grammar_roundtrip_preserves_capture_lookup_and_alternatives(self):
        neuron = GrammarNeuron("copy_actor", (Rule(Seq(Gap(maximum=8),
            Token(bind="actor", pos=OneOf(("n", "pn"))),
            Alt(Token(token="took"), Token(token="got"), weights=(2, 1))),
            {"actor": Ref("actor.token"), "event": Lookup("events", "take")}, 3),),
            tables={"events": {"take": "obtain object"}})
        context = [dict(token="Lily", pos="pn"), dict(token="took", pos="v")]
        spec = neuron_spec(neuron)
        restored = parse_neuron(json.loads(json.dumps(spec)), context_size=8)
        self.assertEqual(restored.activate(context), neuron.activate(context))
        self.assertEqual(neuron_spec(restored), spec)

    def test_unknown_operations_excessive_repeat_and_extra_fields_fail(self):
        spec = neuron_spec(GrammarNeuron("x", (Rule(Gap(maximum=8), {}),)))
        for change in (dict(kind="python", code="anything"),
                       dict(kind="repeat", children=[dict(kind="token", tests={})], minimum=0, maximum=1000),
                       dict(kind="token", tests={}, surprise=True)):
            bad = deepcopy(spec)
            bad["rules"][0]["pattern"] = change
            with self.assertRaises(ValueError):
                parse_neuron(bad, context_size=8)


class RevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = make_corpus(7, 32, 8, 8)
        cls.model = induce(cls.corpus["train"], max_rules=8, min_support=3, weight_steps=10).model
        cls.slot = next(index for index, head in enumerate(cls.model.layers[0].heads)
                        if head and head.neuron.rules[0].pattern.children[-1].tests == {"pos": "v"})
        cls.address = dict(kind="head", layer=0, head=cls.slot)
        cls.packet = collect(cls.model, cls.corpus["train"], cls.address, max_examples=2)
        cls.source = next(iter(locate(cls.model, cls.address).rules[0].emit))

    def proposal(self):
        return proposal_template(self.packet)

    def test_packet_contains_training_statistics_and_actionable_examples(self):
        p = self.packet
        self.assertEqual(p["stats"]["matched_targets"], 32)
        self.assertEqual(sum(row["count"] for row in p["stats"]["outcomes"]), 32)
        self.assertTrue(p["examples"]["helpful_matches"])
        self.assertTrue(p["examples"]["unmatched_high_loss"])
        self.assertEqual(p["registry"][self.source]["type"], "boolean")
        self.assertTrue(p["feature_consumers"][self.source]["readers"])
        for example in p["examples"]["helpful_matches"]:
            self.assertEqual(example["neuron_input_tail"][-1]["pos"], "v")
            self.assertGreater(example["probability"], example["ablated_probability"])
        self.assertNotIn("validation", p)
        self.assertEqual(p["base_model_sha256"], model_fingerprint(self.model))
        self.assertEqual(p["head_controls"]["operation"], "add")
        json.dumps(p, allow_nan=False)

    def test_rename_changes_all_consumers_and_persists_without_changing_predictions(self):
        proposal = self.proposal()
        proposal["neuron"]["name"] = "detect_current_verb"
        proposal["feature_definitions"] = {"ends_in_verb": dict(type="boolean", description="The current token has POS v.")}
        proposal["bindings"] = [dict(source=self.source, target="ends_in_verb", value=True)]
        before = model_fingerprint(self.model)
        candidate, report = evaluate_proposal(self.model, proposal, self.corpus["train"], self.corpus["validation"])
        self.assertTrue(report["accepted"], report)
        self.assertEqual(model_fingerprint(self.model), before)
        context = [dict(token="Lily", pos="pn"), dict(token="took", pos="v")]
        self.assertEqual(candidate.predict(context).to_dict(), self.model.predict(context).to_dict())
        view = candidate.forward(context).residual_stream[-1]
        self.assertTrue(view["ends_in_verb"])
        self.assertNotIn(self.source, view)
        self.assertTrue(any("ends_in_verb" in str(neuron_spec(root)) for root in candidate.projection.neurons.values()))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.json"
            candidate.save(path)
            restored = Storyformer.load(path)
        self.assertEqual(restored.features, candidate.features)
        self.assertEqual(restored.predict(context).to_dict(), candidate.predict(context).to_dict())

    def test_existing_categorical_feature_can_replace_private_boolean_detector(self):
        proposal = self.proposal()
        proposal["bindings"] = [dict(source=self.source, target="pos", value="v")]
        candidate, report = evaluate_proposal(self.model, proposal, self.corpus["train"], self.corpus["validation"])
        self.assertTrue(report["accepted"], report)
        self.assertEqual(locate(candidate, self.address).rules[0].emit, {"pos": "v"})
        self.assertEqual(report["before"]["joint_nll"], report["after"]["joint_nll"])
        self.assertEqual(report["after"]["observed_attribute_conflicts"], 0)

    def test_grammar_change_is_executed_and_regression_is_rejected(self):
        proposal = self.proposal()
        proposal["neuron"]["rules"] = []
        candidate, report = evaluate_proposal(self.model, proposal, self.corpus["train"], self.corpus["validation"])
        self.assertIsNotNone(candidate)
        self.assertFalse(report["accepted"])
        self.assertGreater(report["after"]["joint_nll"], report["before"]["joint_nll"])

    def test_semantically_conflicting_write_is_rejected_even_when_likelihood_is_unchanged(self):
        head = GrammarHead(GrammarNeuron("private", (Rule(Gap(), {"private_flag": True}),)))
        model = Storyformer(GrammarProjection({"x": GrammarNeuron("x", (Rule(Gap(), {"pos": "v"}),))}),
                           layers=(StoryformerBlock((head,)),))
        documents = [[dict(token="x", pos="v"), dict(token="x", pos="v")]]
        packet = collect(model, documents, dict(kind="head", layer=0, head=0))
        proposal = proposal_template(packet)
        proposal["bindings"] = [dict(source="private_flag", target="pos", value="n")]
        _, report = evaluate_proposal(model, proposal, documents, documents)
        self.assertFalse(report["accepted"])
        self.assertEqual(report["before"]["joint_nll"], report["after"]["joint_nll"])
        self.assertGreater(report["after"]["observed_attribute_conflicts"], 0)

    def test_invalid_types_protected_writes_and_undeclared_features_fail(self):
        for field, value in ((self.source, "true"), ("token", "changed"), ("unregistered", True)):
            proposal = self.proposal()
            proposal["neuron"]["rules"][0]["emit"] = {field: value}
            _, report = evaluate_proposal(self.model, proposal, self.corpus["train"], self.corpus["validation"])
            self.assertFalse(report["accepted"])
            self.assertNotIn("after", report)

    def test_observed_schema_is_not_renamed_or_retyped(self):
        proposal = self.proposal()
        proposal["bindings"] = [dict(source="pos", target=self.source, value=True)]
        _, report = evaluate_proposal(self.model, proposal, self.corpus["train"], self.corpus["validation"])
        self.assertFalse(report["accepted"])
        proposal = self.proposal()
        proposal["feature_definitions"] = {"pos": dict(type="boolean", description="verb")}
        _, report = evaluate_proposal(self.model, proposal, self.corpus["train"], self.corpus["validation"])
        self.assertFalse(report["accepted"])

    def test_stale_identity_and_exhausted_match_budget_are_rejected(self):
        proposal = self.proposal()
        proposal["base_model_sha256"] = "stale"
        _, report = evaluate_proposal(self.model, proposal, self.corpus["train"], self.corpus["validation"])
        self.assertFalse(report["accepted"])
        self.assertIn("stale", report["reason"])
        proposal = self.proposal()
        proposal["neuron"]["max_states"] = 1
        _, report = evaluate_proposal(self.model, proposal, self.corpus["train"], self.corpus["validation"])
        self.assertFalse(report["accepted"])
        self.assertIn("MatchBudgetExceeded", report["reason"])

    def test_output_neuron_weights_can_be_revised_and_fitted_fairly(self):
        roots = {word: GrammarNeuron(word, (Rule(Gap(), {"pos": "n"}),)) for word in ("a", "b")}
        model = Storyformer(GrammarProjection(roots), num_layers=0)
        train = [[dict(token="a", pos="n")]] * 4
        validation = [[dict(token="a", pos="n")]] * 2
        packet = collect(model, train, dict(kind="output", token="a"))
        proposal = proposal_template(packet)
        proposal["neuron"]["rules"][0]["weight"] = 3
        candidate, report = evaluate_proposal(model, proposal, train, validation, fit_epochs=1)
        self.assertTrue(report["accepted"], report)
        self.assertLess(report["after"]["joint_nll"], report["before"]["joint_nll"])
        self.assertEqual(model.projection.neurons["a"].rules[0].weight, 1)

    def test_shared_neuron_and_rule_identities_survive_staging(self):
        shared = Rule(Gap(), {"pos": "n"})
        first, second = GrammarNeuron("first", (shared,)), GrammarNeuron("second", (shared,))
        head = GrammarHead(first)
        model = Storyformer(GrammarProjection({"a": first, "b": second}), layers=(StoryformerBlock((head, head)),))
        train = [[dict(token="a", pos="n")]]
        packet = collect(model, train, dict(kind="output", token="a"))
        proposal = proposal_template(packet)
        proposal["neuron"]["name"] = "renamed"
        candidate = stage(model, proposal, registry_for(model, train))
        a, b = candidate.projection.neurons["a"], candidate.projection.neurons["b"]
        self.assertIs(a, candidate.layers[0].heads[0].neuron)
        self.assertIs(a, candidate.layers[0].heads[1].neuron)
        self.assertIs(a.rules[0], b.rules[0])
        self.assertEqual(len(packet["sharing"]["instances"]), 3)

    def test_a_head_has_no_activation_when_the_residual_stream_is_empty(self):
        head = GrammarHead(GrammarNeuron("constant", (Rule(Gap(), {"private_flag": True}),)))
        model = Storyformer(GrammarProjection({"x": GrammarNeuron("x", (Rule(Gap(), {"pos": "n"}),))}),
                           layers=(StoryformerBlock((head,)),))
        packet = collect(model, [[dict(token="x", pos="n")]], dict(kind="head", layer=0, head=0))
        self.assertEqual(packet["stats"]["matched_targets"], 0)


class LLMRevisionTests(unittest.IsolatedAsyncioTestCase):
    async def test_cached_request_and_saved_response_reuse_need_no_new_call(self):
        model = Storyformer(GrammarProjection({"a": GrammarNeuron("a", (Rule(Gap(), {"pos": "n"}),))}), num_layers=0)
        packet = collect(model, [[dict(token="a", pos="n")]], dict(kind="output", token="a"))
        payload = proposal_template(packet)
        payload["neuron"]["name"] = "emit_a"
        raw = dict(model="gpt-6-luna", service_tier="flex", status="completed", usage={},
                   output=[dict(type="message", content=[dict(type="output_text", text=json.dumps(payload))])])
        client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(
            return_value=SimpleNamespace(model_dump=lambda **_: raw))))
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.assertEqual(await propose(packet, directory, client=client), payload)
            self.assertEqual(await propose(packet, directory), payload)
            client.responses.create.assert_awaited_once()
        request = revision_request(packet)
        named_request = revision_request(packet, goal="Clarify the names without changing behavior.")
        self.assertEqual(request["prompt_cache_key"], named_request["prompt_cache_key"])
        self.assertEqual(request["input"][0], named_request["input"][0])
        self.assertEqual(request["service_tier"], "flex")
        self.assertEqual(request["prompt_cache_options"], {"mode": "explicit", "ttl": "30m"})
        self.assertIn("prompt_cache_breakpoint", request["input"][0]["content"][0])
        self.assertNotIn("prompt_cache_breakpoint", request["input"][1])
        with tempfile.TemporaryDirectory() as folder:
            await propose(packet, Path(folder), client=client, prepare_only=True)
            self.assertFalse((Path(folder) / "response.json").exists())
        client.responses.create.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
