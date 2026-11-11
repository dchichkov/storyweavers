"""Prefix isolation, reusable cache boundaries, parallel dispatch and local gaps."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from .annotation import MODEL, empty_annotation, story_tokens
from .annotate import read, save
from .annotate_prefixes import annotate_jobs, annotate_word, extract, prepare, run
from .prefix_annotation import (EXAMPLES, PROMPT, assemble, prefix_request, request_prefix,
                                shared_prefix, validate_record)


def raw_response(record, **overrides):
    return {"model": MODEL, "service_tier": "flex", "status": "completed", "id": "test-prefix",
            "output": [dict(type="message", content=[dict(type="output_text", text=json.dumps(record))])],
            "usage": dict(input_tokens=4000, input_tokens_details=dict(cached_tokens=3000, cache_write_tokens=10)),
            **overrides}


def args(folder, story="Lily took scissors."):
    return SimpleNamespace(story=story, story_file=None, input=None, text_key="story", limit=None,
                           out=Path(folder), prompt_file=PROMPT, examples_file=EXAMPLES, concurrency=2,
                           reasoning="low", max_output_tokens=2048, prepare_only=False, api_key_file=None)


class PrefixContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = json.loads(EXAMPLES.read_text())
        cls.prefix = shared_prefix()

    def test_examples_are_single_prefix_only_records(self):
        self.assertEqual(len(self.examples), 8)
        for example in self.examples:
            self.assertEqual(validate_record(example["prefix"], example["response"]), example["response"])
        self.assertEqual(self.examples[1]["response"]["patients"], [])
        self.assertEqual(self.examples[2]["response"]["event"], "obtain object")
        self.assertIsNone(self.examples[4]["response"]["location"])
        self.assertIsNone(self.examples[5]["response"]["event_id"])

    def test_future_suffix_cannot_change_request_or_cache_key(self):
        first = prefix_request("Lily took scissors. She mended a coat.", 2, prefix=self.prefix)
        second = prefix_request("Lily took apples. She ate them.", 2, prefix=self.prefix)
        self.assertEqual(first, second)
        self.assertEqual(request_prefix(first), "Lily took")
        self.assertEqual(first["text"]["format"]["schema"]["type"], "object")
        self.assertNotIn("annotations", first["text"]["format"]["schema"]["properties"])
        self.assertEqual(first["service_tier"], "flex")
        self.assertEqual(first["model"], MODEL)

    def test_word_blocks_preserve_earlier_cache_endpoints(self):
        short = prefix_request("Lily took scissors.", 0, prefix=self.prefix)
        long = prefix_request("Lily took scissors.", 4, prefix=self.prefix)
        self.assertEqual(short["input"][0], long["input"][0])
        self.assertEqual(short["input"][1]["content"][:-1], long["input"][1]["content"][:1])
        self.assertEqual(short["prompt_cache_key"], long["prompt_cache_key"])
        self.assertEqual(long["prompt_cache_options"], {"mode": "explicit", "ttl": "30m"})
        for block in long["input"][1]["content"][:-1]:
            self.assertEqual(block["prompt_cache_breakpoint"], {"mode": "explicit"})
        self.assertNotIn("prompt_cache_breakpoint", long["input"][1]["content"][-1])
        changed = prefix_request("Lily", 0, prefix=self.prefix + "\nChanged instructions")
        self.assertNotEqual(short["prompt_cache_key"], changed["prompt_cache_key"])

    def test_unicode_offsets_and_nonword_synthesis(self):
        story = " \tLily  took\r\nscisors, 🐇! "
        rows = []
        for span in story_tokens(story):
            if span["kind"] == "word":
                body = prefix_request(story, span["index"], prefix=self.prefix)
                self.assertEqual(request_prefix(body), story[:span["end"]])
                rows.append(empty_annotation(span["index"], span["token"]))
            else:
                with self.assertRaises(ValueError):
                    prefix_request(story, span["index"], prefix=self.prefix)
        output = assemble(story, rows)
        self.assertEqual("".join(row["token"] for row in output), story)
        for row in output:
            self.assertEqual(row["token"], story[row["start"]:row["end"]])
            self.assertEqual(row["position"]["token"], row["index"])
            if row["kind"] != "word":
                self.assertEqual(row["pos"], row["kind"])
                self.assertIsNone(row["event"])

    def test_exact_single_record_and_prefix_grounding_are_required(self):
        example = self.examples[1]
        for update in (dict(index=True), dict(token="take"), dict(patients=["e99"]),
                       dict(actor_id="e2"), dict(event_id="ev9"), dict(actor="Lili"),
                       dict(unexpected="extra"), dict(attributes=[dict(name="BadName", value="x")])):
            with self.assertRaises(ValueError):
                validate_record(example["prefix"], {**example["response"], **update})
        for malformed in ([example["response"]], {"annotations": [example["response"]]}):
            with self.assertRaises(ValueError):
                validate_record(example["prefix"], malformed)

    def test_assembly_validates_links_without_backfilling_trigger_arguments(self):
        records = [deepcopy(example["response"]) for example in self.examples[:3]]
        output = assemble("Lily took scissors.", records)
        self.assertEqual(output[2]["patients"], [])
        self.assertEqual(output[4]["event_id"], output[2]["event_id"])
        self.assertEqual(output[4]["location"], "Lily")
        records[-1]["event"] = "obtain repair tool"
        with self.assertRaisesRegex(ValueError, "consistent prefix-local trigger"):
            assemble("Lily took scissors.", records)
        with self.assertRaises(ValueError):
            assemble("Lily took scissors.", records[:2])

    def test_later_discovery_does_not_require_rewriting_an_earlier_unknown(self):
        first = empty_annotation(0, "Orange")
        action = empty_annotation(2, "rolled", pos="v", event="move", event_id="ev3", event_type="move",
                                  actor="Orange", actor_id="e1", role="action", factuality="asserted")
        rows = assemble("Orange rolled", [first, action])
        self.assertIsNone(rows[0]["entity_id"])
        self.assertEqual(rows[2]["actor_id"], "e1")
        first = empty_annotation(0, "saw")
        noun = empty_annotation(2, "scissors", pos="n", entity="scissors", entity_id="e3", entity_name="scissors",
                                event="perceive", event_id="ev1", role="patient")
        rows = assemble("saw scissors", [first, noun])
        self.assertIsNone(rows[0]["event_id"])
        self.assertEqual(rows[2]["event_id"], "ev1")

    def test_wrong_model_tier_incomplete_refusal_or_wrapper_are_rejected(self):
        example = self.examples[0]
        body = prefix_request(example["prefix"], 0, prefix=self.prefix)
        for update in (dict(model="other"), dict(service_tier="default"), dict(status="incomplete")):
            with self.assertRaises(ValueError):
                extract(body, raw_response(example["response"], **update))
        with self.assertRaises(ValueError):
            extract(body, raw_response({"annotations": [example["response"]]}))
        refused = raw_response(example["response"])
        refused["output"][0]["content"] = [dict(type="refusal")]
        with self.assertRaises(ValueError):
            extract(body, refused)


class PrefixDispatchTests(unittest.IsolatedAsyncioTestCase):
    async def test_mock_run_resumes_without_calls_or_keys_and_preserves_positions(self):
        examples = {example["prefix"]: example["response"] for example in json.loads(EXAMPLES.read_text())}
        sent = []

        async def create(**body):
            text = request_prefix(body)
            sent.append(text)
            raw = raw_response(examples[text])
            return SimpleNamespace(model_dump=lambda **_: raw)

        client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(side_effect=create)))
        with tempfile.TemporaryDirectory() as folder:
            options = args(folder)
            await run(options, client)
            self.assertEqual(sent[0], "Lily")
            self.assertEqual(set(sent), {"Lily", "Lily took", "Lily took scissors"})
            manifest = read(Path(folder) / "manifest.json")
            output = Path(folder) / manifest[0]["directory"] / "annotations.json"
            rows = read(output)
            self.assertEqual("".join(row["token"] for row in rows), options.story)
            self.assertEqual(rows[2]["patients"], [])
            self.assertEqual(rows[4]["position"], dict(token=4, sentence=0, in_sentence=4))
            await run(options)  # Saved responses need neither a client nor credentials.
            self.assertEqual(client.responses.create.await_count, 3)
            self.assertEqual(rows, read(output))
            self.assertEqual(read(Path(folder) / "summary.json")["stories"][0]["word_count"], 3)
            with self.assertRaises(ValueError):
                prepare(args(folder, "Changed story."))

    async def test_shortest_warmup_finishes_before_bounded_parallel_waves(self):
        events, active, peak = [], 0, 0

        async def fake(directory, client, **kwargs):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            events.append(("start", directory.name))
            await asyncio.sleep(0)
            events.append(("end", directory.name))
            active -= 1
            return dict(cached_tokens=0, cache_write_tokens=0)

        with tempfile.TemporaryDirectory() as folder, patch("storyformers.annotate_prefixes.annotate_word", side_effect=fake):
            jobs = [dict(directory=Path(folder) / str(index), prefix_words=index, prefix_end=index * 3)
                    for index in (5, 3, 1, 4, 2)]
            await annotate_jobs(jobs, None, concurrency=2)
        self.assertEqual(events[:2], [("start", "1"), ("end", "1")])
        self.assertEqual(peak, 2)
        self.assertLess(events.index(("end", "3")), events.index(("start", "4")))

    async def test_failed_wave_retains_inflight_completions_and_stops_later_waves(self):
        completed = []

        async def fake(directory, client, **kwargs):
            if directory.name == "2":
                raise ValueError("bad record")
            await asyncio.sleep(0)
            completed.append(directory.name)
            return dict(cached_tokens=0, cache_write_tokens=0)

        with tempfile.TemporaryDirectory() as folder, patch("storyformers.annotate_prefixes.annotate_word", side_effect=fake):
            jobs = [dict(directory=Path(folder) / str(index), prefix_words=index, prefix_end=index) for index in range(1, 5)]
            with self.assertRaises(ValueError):
                await annotate_jobs(jobs, None, concurrency=2)
        self.assertEqual(completed, ["1", "3"])

    async def test_uncertain_or_invalid_completed_calls_are_not_resubmitted(self):
        with tempfile.TemporaryDirectory() as folder:
            _, jobs = prepare(args(folder, "Lily"))
            client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(side_effect=TimeoutError())))
            with self.assertRaises(TimeoutError):
                await annotate_word(jobs[0]["directory"], client)
            with self.assertRaises(RuntimeError):
                await annotate_word(jobs[0]["directory"], client)
            client.responses.create.assert_awaited_once()
        with tempfile.TemporaryDirectory() as folder:
            _, jobs = prepare(args(folder, "Lily"))
            raw = raw_response({"annotations": []})
            client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(
                return_value=SimpleNamespace(model_dump=lambda **_: raw))))
            for _ in range(2):
                with self.assertRaises(ValueError):
                    await annotate_word(jobs[0]["directory"], client)
            client.responses.create.assert_awaited_once()
            self.assertTrue((jobs[0]["directory"] / "response.json").exists())
            self.assertFalse(read(jobs[0]["directory"] / "validation.json")["ok"])

    async def test_capacity_rejection_retries_on_flex_only(self):
        record = json.loads(EXAMPLES.read_text())[0]["response"]
        raw = raw_response(record)
        error = RuntimeError("capacity")
        error.status_code, error.code = 429, "flex_unavailable"
        client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(
            side_effect=[error, SimpleNamespace(model_dump=lambda **_: raw)])))
        with tempfile.TemporaryDirectory() as folder, patch("storyformers.annotate_prefixes.asyncio.sleep", new=AsyncMock()):
            _, jobs = prepare(args(folder, "Lily"))
            await annotate_word(jobs[0]["directory"], client)
            self.assertEqual(client.responses.create.await_count, 2)

    async def test_prepare_only_and_nonword_stories_never_contact_provider(self):
        client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock()))
        with tempfile.TemporaryDirectory() as folder:
            options = args(folder)
            options.prepare_only = True
            await run(options, client)
            client.responses.create.assert_not_awaited()
            self.assertEqual(len(list(Path(folder).rglob("request.json"))), 3)
        with tempfile.TemporaryDirectory() as folder:
            await run(args(folder, " \r\n...🐇!"))
            summary = read(Path(folder) / "summary.json")["stories"][0]
            self.assertEqual(summary["word_count"], 0)
            self.assertEqual(summary["cached_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
