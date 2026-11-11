"""Causal catalog contract, typed features and shared parallel-runner integration."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from . import catalog_prefix_annotation as contract
from .annotation import story_tokens
from .annotate import read
from .annotate_prefixes import run
from .prefix_annotation import request_prefix
from .test_prefix_annotation import args, raw_response


class CatalogPrefixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = json.loads(contract.EXAMPLES.read_text())
        cls.prefix = contract.shared_prefix()

    def test_full_catalog_and_causal_examples_are_valid(self):
        for example in self.examples:
            self.assertEqual(contract.validate_record(example["prefix"], example["response"]), example["response"])
        for number in range(1, 1025):
            self.assertIn(f"A{number:04d} ", self.prefix)
        self.assertIs(self.examples[7]["response"]["generic_reference"], False)
        self.assertEqual(self.examples[8]["response"]["patients"], [])
        self.assertEqual(self.examples[8]["response"]["instruments"], [])
        self.assertEqual(self.examples[1]["response"]["patients"], [])
        self.assertNotIn("location", self.examples[3]["response"])

    def test_future_text_is_absent_and_cache_boundaries_match(self):
        short = contract.prefix_request("Lily took scissors.", 2, prefix=self.prefix)
        other = contract.prefix_request("Lily took apples. She ate them.", 2, prefix=self.prefix)
        longer = contract.prefix_request("Lily took scissors.", 4, prefix=self.prefix)
        self.assertEqual(short, other)
        self.assertEqual(request_prefix(short), "Lily took")
        self.assertEqual(short["input"][0], longer["input"][0])
        self.assertEqual(short["input"][1]["content"][:-1], longer["input"][1]["content"][:2])
        self.assertEqual(short["prompt_cache_key"], longer["prompt_cache_key"])
        self.assertEqual(short["prompt_cache_options"], {"mode": "explicit", "ttl": "30m"})
        self.assertEqual(short["text"]["format"], {"type": "json_object"})

    def test_reject_wrong_types_unregistered_features_and_future_references(self):
        example = self.examples[0]
        for update in (dict(reference_introduction="true"), dict(undocumented=True),
                       dict(index=True), dict(position={}), dict(scope_id="invented"),
                       dict(actor_id="e999"), dict(_evidence=[dict(indices=[99], note="future")])):
            with self.subTest(update=update), self.assertRaises(ValueError):
                contract.validate_record(example["prefix"], {**example["response"], **update})
        bad = deepcopy(self.examples[2]["response"])
        bad["_references"]["events"]["ev3"]["patients"] = ["e999"]
        with self.assertRaises(ValueError):
            contract.validate_record(self.examples[2]["prefix"], bad)
        bad = deepcopy(self.examples[2]["response"])
        bad["_references"]["entities"]["e999"] = dict(name="future", type="object")
        with self.assertRaises(ValueError):
            contract.validate_record(self.examples[2]["prefix"], bad)
        bad = deepcopy(self.examples[2]["response"])
        bad["_references"]["events"]["ev3"]["event_type"] = "cut"
        with self.assertRaisesRegex(ValueError, "nested value"):
            contract.validate_record(self.examples[2]["prefix"], bad)

    def test_local_gaps_and_reference_snapshots_do_not_backfill(self):
        responses = [e["response"] for e in self.examples[:3]]
        before = deepcopy(responses)
        result = contract.assemble("Lily took scissors.\n", responses)
        self.assertEqual("".join(r["token"] for r in result), "Lily took scissors.\n")
        self.assertEqual(result[2]["patients"], [])
        self.assertNotIn("event_id", result[0])
        self.assertEqual(responses, before)
        self.assertEqual(result[-1]["pos"], "space")
        self.assertTrue(all(r["position"]["token"] == r["index"] for r in result))
        self.assertFalse(any("_references" in r for r in result))


class CatalogRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_multiple_corrections_resume_and_account_for_every_response(self):
        correct = json.loads(contract.EXAMPLES.read_text())[0]["response"]
        bad_scope = {**correct, "scope_id": "s999"}
        bad_entity = {**correct, "entity": "wrong_type"}
        sent = []

        async def create(**body):
            sent.append(deepcopy(body))
            raw = raw_response([bad_scope, bad_entity, correct][len(sent) - 1])
            return SimpleNamespace(model_dump=lambda **_: raw)

        with tempfile.TemporaryDirectory() as folder:
            options = args(folder, "Lily")
            options.contract, options.prompt_file, options.examples_file = "catalog-v2", None, None
            client = SimpleNamespace(responses=SimpleNamespace(create=create))
            with self.assertRaises(ValueError):
                await run(options, client)
            self.assertEqual(len(sent), 2)
            options.validation_repairs = 3
            await run(options, client)
            await run(options)  # Both correction responses are reused offline.
            self.assertEqual(len(sent), 3)
            self.assertEqual(len({request_prefix(body) for body in sent}), 1)
            self.assertEqual(sent[0]["input"][0], sent[2]["input"][0])
            self.assertEqual(sent[0]["input"][1]["content"][:-1], sent[2]["input"][1]["content"][:-1])
            summary = read(Path(folder) / "summary.json")["stories"][0]
            self.assertEqual(summary["validation_repairs"], 2)
            self.assertEqual(summary["cached_tokens"], 9000)
            self.assertEqual(len(summary["usage"]), 3)

    async def test_rejected_correction_stops_after_two_calls(self):
        bad = deepcopy(json.loads(contract.EXAMPLES.read_text())[0]["response"])
        bad["scope_id"] = "s999"
        calls = []

        async def create(**body):
            calls.append(body)
            return SimpleNamespace(model_dump=lambda **_: raw_response(bad))

        with tempfile.TemporaryDirectory() as folder:
            options = args(folder, "Lily")
            options.contract, options.prompt_file, options.examples_file = "catalog-v2", None, None
            with self.assertRaises(ValueError):
                await run(options, SimpleNamespace(responses=SimpleNamespace(create=create)))
            self.assertEqual(len(calls), 2)
            with self.assertRaises(ValueError):
                await run(options)  # cached failures do not trigger a third call
            self.assertEqual(len(calls), 2)

    async def test_one_correction_uses_same_prefix_and_is_reused_without_network(self):
        correct = json.loads(contract.EXAMPLES.read_text())[0]["response"]
        bad = deepcopy(correct)
        bad["_references"]["entities"]["e2"] = dict(name="future", type="person")
        sent = []

        async def create(**body):
            sent.append(deepcopy(body))
            raw = raw_response(bad if len(sent) == 1 else correct)
            return SimpleNamespace(model_dump=lambda **_: raw)

        with tempfile.TemporaryDirectory() as folder:
            options = args(folder, "Lily")
            options.contract, options.prompt_file, options.examples_file = "catalog-v2", None, None
            await run(options, SimpleNamespace(responses=SimpleNamespace(create=create)))
            self.assertEqual(len(sent), 2)
            self.assertEqual(request_prefix(sent[0]), request_prefix(sent[1]))
            self.assertEqual(sent[0]["input"][0], sent[1]["input"][0])
            self.assertEqual(sent[0]["input"][1]["content"][:-1], sent[1]["input"][1]["content"][:-1])
            await run(options)
            self.assertEqual(len(sent), 2)
            summary = read(Path(folder) / "summary.json")["stories"][0]
            self.assertEqual(summary["validation_repairs"], 1)
            self.assertEqual(summary["cached_tokens"], 6000)
            self.assertEqual(len(summary["usage"]), 2)

    async def test_real_runner_dispatches_catalog_contract_and_resumes(self):
        examples = json.loads(contract.EXAMPLES.read_text())
        responses = {e["prefix"]: e["response"] for e in examples[:3]}
        sent = []

        async def create(**body):
            prefix = request_prefix(body)
            sent.append(prefix)
            raw = raw_response(responses[prefix])
            return SimpleNamespace(model_dump=lambda **_: raw)

        with tempfile.TemporaryDirectory() as folder:
            options = args(folder)
            options.contract, options.prompt_file, options.examples_file = "catalog-v2", None, None
            client = SimpleNamespace(responses=SimpleNamespace(create=create))
            await run(options, client)
            self.assertEqual(len(sent), 3)
            await run(options)  # no credentials/network when responses exist
            self.assertEqual(len(sent), 3)
            summary = read(Path(folder) / "summary.json")
            self.assertEqual(summary["version"], contract.VERSION)
            directory = Path(folder) / summary["stories"][0]["directory"]
            snapshots = read(directory / "reference_snapshots.json")
            self.assertEqual(snapshots["2"]["_references"]["events"]["ev3"]["patients"], [])
            self.assertEqual(snapshots["4"]["_references"]["events"]["ev3"]["patients"], ["e5"])
            self.assertEqual(read(directory / "annotations.json")[2]["patients"], [])


if __name__ == "__main__":
    unittest.main()
