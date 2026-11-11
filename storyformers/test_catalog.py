"""Integration and adversarial checks for the proposed catalog, not accuracy claims."""

from copy import deepcopy
import json
import re
import unittest

from .catalog.api import AdapterRequired, CatalogIndex, prepare_context
from .catalog.build import ROOT, assemble, encode_rows, validate
from .grammar import Gap, GrammarNeuron, Ref, Rule, Seq, Token
from .transformer import GrammarProjection, Storyformer


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = assemble()
        cls.index = CatalogIndex()

    def test_complete_catalog_and_all_native_examples(self):
        sources = {row["id"] for row in json.loads((ROOT / "sources.json").read_text())}
        report = validate(self.records, source_ids=sources)
        self.assertTrue(report["valid"], report["errors"])
        self.assertGreater(report["native_examples_executed"], 400)
        self.assertGreater(report["native_suppression_checks"], 0)
        self.assertEqual(report["adapter_seed_matchers"], 64)
        self.assertEqual(report["adapter_seed_examples_executed"], 128)

    def test_generated_files_are_reproducible(self):
        for kind, rows in self.records.items():
            self.assertEqual((ROOT / f"{kind}.jsonl").read_text(), encode_rows(rows))

    def test_known_conflicting_senses_abstain(self):
        cases = [("measure_unit", "seconds", "second:extra_serving"),
                 ("temporal_granularity", "second", "second:ordinal"),
                 ("temporal_bound_cue", "since", "since:causal"),
                 ("quantity_approximation_cue", "about", "about:topic")]
        for key, token, sense in cases:
            grammar_id = self.index.by_key[key]["grammar_ids"][0]
            self.assertFalse(self.index.neuron(grammar_id).activate([{"token": token, "lexical_sense_id": sense}]))

    def test_lexical_sense_chain_reuses_the_same_identifier(self):
        row = {"token": "scissors", "lemma": "scissors", "pos": "n"}
        first = self.index.neuron(self.index.by_key["lexical_sense_id"]["grammar_ids"][0]).activate([row])[0].value
        gloss = self.index.neuron(self.index.by_key["lexical_gloss"]["grammar_ids"][0]).activate([{**row, **first}])
        self.assertTrue(gloss)
        self.assertIn("blades", gloss[0].value["lexical_gloss"])

    def test_provenance_cannot_cross_claims_events_or_scopes(self):
        carriers = [g for g in self.records["grammars"] if g["family"] == "semantic_evidence"
                    and self.index.heads[g["head_ids"][0]]["mechanism"] == "same_identity_adjacent_copy"]
        self.assertEqual(len(carriers), 12)
        for grammar in carriers:
            neuron = self.index.neuron(grammar["id"])
            for field, value in (("event_id", "ev_other"), ("scope_id", "s_other")):
                context = deepcopy(grammar["examples"][0]["context"])
                context[-1][field] = value
                self.assertFalse(neuron.activate(context), (grammar["id"], field))
            context = deepcopy(grammar["examples"][0]["context"])
            context[0].pop("source_claim_id")
            self.assertFalse(neuron.activate(context), grammar["id"])

    def test_adapter_contracts_cannot_be_loaded_as_native_heads(self):
        head = next(h for h in self.index.heads.values() if h["runtime_support"] == "adapter_required")
        with self.assertRaisesRegex(AdapterRequired, "requires"):
            self.index.head(head["id"])

    def test_whitespace_adapter_preserves_original_source_positions(self):
        rows = [{"token": "at", "index": 0}, {"token": " ", "index": 1},
                {"token": "least", "index": 2}, {"token": " ", "index": 3},
                {"token": "three", "index": 4, "cardinal_value": 3}]
        before = deepcopy(rows)
        prepared = prepare_context(rows)
        self.assertEqual([r["index"] for r in prepared], [0, 2, 4])
        self.assertEqual([r["position"]["token"] for r in prepared], [0, 2, 4])
        self.assertEqual(rows, before)

    def test_native_head_can_feed_full_next_latent_projection(self):
        head_id = self.index.by_key["quantity_lower_bound"]["producer_head_ids"][0]
        projection = GrammarProjection({word: GrammarNeuron(word, (
            Rule(Seq(Gap(), Token(quantity_lower_bound=3)),
                 {"pos": "n", "entity": word, "role": "patient", "location": None,
                  "event": None, "quantity_lower_bound": Ref("query.quantity_lower_bound")}, weight=weight),
        )) for word, weight in [("apples", 2.0), ("pears", 1.0)]})
        model = Storyformer(projection, layers=(self.index.block([head_id]),),
                            features=self.index.feature_registry(["quantity_lower_bound", "cardinal_value"]))
        output = model.predict(prepare_context([{"token": "at"}, {"token": "least"},
                                               {"token": "three", "cardinal_value": 3}]))
        self.assertAlmostEqual(output.probabilities["apples"], 2/3)
        self.assertAlmostEqual(output.probabilities["pears"], 1/3)
        self.assertTrue(all(row["latent"]["quantity_lower_bound"] == 3 for row in output.joint))

    def test_suppression_associations_are_not_false_producers(self):
        control = self.index.by_key["evidence_retracted"]
        head = self.index.heads[control["grammar_ids"][0].replace("G", "H", 1)]
        self.assertEqual(head["operation"], "suppress")
        self.assertNotIn(head["id"], control["producer_head_ids"])
        self.assertIn(head["id"], self.index.by_key["truth_commitment"]["suppressor_head_ids"])

    def test_predecessor_crosswalk_has_valid_links_and_explicit_gaps(self):
        crosswalk = json.loads((ROOT / "research/head_crosswalk.json").read_text())
        self.assertEqual({row["old_head_id"] for row in crosswalk["entries"]},
                         {f"P{i:03d}" for i in range(1, 65)})
        for row in crosswalk["entries"]:
            self.assertIn(row["relation"], crosswalk["relation_definitions"])
            for link in row["links"]:
                self.assertEqual(self.index.by_key[link["attribute_key"]]["id"], link["attribute_id"])
                for gid, support in link["runtime_support"].items():
                    self.assertEqual(self.index.grammars[gid]["runtime_support"], support)
                for hid, fields in link["actual_write_fields"].items():
                    self.assertEqual(self.index.heads[hid]["writes"], fields)
                    self.assertEqual(self.index.heads[hid]["operation"], link["head_operations"][hid])

    def test_world_witnesses_keep_projected_entities_bound_to_the_prefix(self):
        def entity_ids(value):
            if isinstance(value, str):
                return {value} if re.fullmatch(r"e[1-9]\d*", value) else set()
            children = value.values() if isinstance(value, dict) else value if isinstance(value, list) else []
            result = set()
            for child in children:
                result.update(entity_ids(child))
            return result

        for grammar in self.records["grammars"]:
            if grammar["family"].startswith("world."):
                for example in grammar["examples"]:
                    self.assertFalse(entity_ids(example["expect"]) - entity_ids(example["context"]), grammar["id"])


if __name__ == "__main__":
    unittest.main()
