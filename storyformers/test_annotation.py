"""Offline quality gates for the Luna annotation pipeline and API contract."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from .annotation import (EXAMPLES, MODEL, annotation_request, empty_annotation, sdk_kwargs,
                         shared_prefix, story_tokens, validate_annotations)
from .annotate import annotate_one, extract_response, load_stories, prepare, read, save


def response(payload, **overrides):
    return dict(model=MODEL, service_tier="flex", status="completed", id="test-response",
                output=[{"type": "message", "content": [{"type": "output_text", "text": json.dumps(payload)}]}],
                usage={"input_tokens": 6000, "input_tokens_details": {"cached_tokens": 5000, "cache_write_tokens": 0}},
                **overrides)


class AnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = json.loads(EXAMPLES.read_text())
        cls.prefix = shared_prefix()

    def test_all_examples_reconstruct_exact_story(self):
        self.assertEqual(len(self.examples), 6)
        for example in self.examples:
            rows = validate_annotations(example["story"], example["response"])
            self.assertEqual("".join(row["token"] for row in rows), example["story"])
            for row in rows:
                self.assertEqual(example["story"][row["start"]:row["end"]], row["token"])
                if row["kind"] != "word":
                    self.assertIsNone(row["event"])
                    self.assertIsNone(row["entity"])
                    self.assertIsNone(row["location"])

    def test_unicode_spaces_punctuation_and_exact_spelling(self):
        story = "  Lily\t took scisors,\r\n café’s 🐇_! "
        words = [row for row in story_tokens(story) if row["kind"] == "word"]
        payload = {"annotations": [empty_annotation(row["index"], row["token"]) for row in words]}
        rows = validate_annotations(story, payload)
        self.assertEqual("".join(row["token"] for row in rows), story)
        self.assertIn("\r\n ", [row["token"] for row in rows])
        self.assertIn("scisors", [row["token"] for row in rows])

    def test_omissions_rewrites_reordering_and_extras_fail(self):
        example = self.examples[0]
        for mutate in (
            lambda rows: rows.pop(),
            lambda rows: rows[0].update(token="Lili"),
            lambda rows: rows.reverse(),
            lambda rows: rows[0].update(surprise="ignored?"),
            lambda rows: rows[0].update(index=True),
        ):
            payload = deepcopy(example["response"])
            mutate(payload["annotations"])
            with self.assertRaises(ValueError):
                validate_annotations(example["story"], payload)

    def test_ungrounded_references_and_role_drift_fail(self):
        example = self.examples[1]
        for index, fields in ((1, {"patients": ["e99"]}), (1, {"actor": "Benn"}),
                              (5, {"entity_name": "Someone else"}), (0, {"event_id": "ev99"}),
                              (0, {"patients": ["e2"]}), (1, {"factuality": None})):
            payload = deepcopy(example["response"])
            payload["annotations"][index].update(fields)
            with self.assertRaises(ValueError):
                validate_annotations(example["story"], payload)

    def test_negated_events_and_pronouns_are_in_examples(self):
        transfer = self.examples[1]["response"]["annotations"]
        self.assertEqual(transfer[5]["token"], "She")
        self.assertEqual(transfer[5]["entity_id"], transfer[2]["entity_id"])
        denied = next(row for row in self.examples[3]["response"]["annotations"] if row["token"] == "take")
        self.assertEqual(denied["factuality"], "negated")

    def test_contrast_examples_do_not_invent_repair_purpose(self):
        purposeful = next(row for row in self.examples[0]["response"]["annotations"] if row["token"] == "took")
        unspecified = next(row for row in self.examples[4]["response"]["annotations"] if row["token"] == "took")
        self.assertEqual(purposeful["event"], "obtain repair tool")
        self.assertEqual(unspecified["event"], "obtain object")

    def test_use_to_repair_links_to_one_grounded_event(self):
        example = self.examples[0]
        rows = deepcopy(example["response"]["annotations"])
        by_token = {row["token"]: row for row in rows}
        self.assertEqual(by_token["used"]["event_id"], by_token["mend"]["event_id"])
        self.assertEqual(by_token["them"]["event_id"], by_token["mend"]["event_id"])
        self.assertEqual(by_token["used"]["event"], by_token["mend"]["event"])
        by_token["used"]["event_id"] = "ev3"
        with self.assertRaisesRegex(ValueError, "no annotated trigger"):
            validate_annotations(example["story"], {"annotations": rows})

    def test_object_dictionary_carries_event_role_and_holder(self):
        rows = validate_annotations(self.examples[0]["story"], self.examples[0]["response"])
        scissors = next(row for row in rows if row["token"] == "scissors")
        self.assertEqual({key: scissors[key] for key in ("token", "pos", "entity", "role", "location", "event")},
                         {"token": "scissors", "pos": "n", "entity": "scissors", "role": "patient",
                          "location": "Lily", "event": "obtain repair tool"})

    def test_locations_follow_each_transfer_instead_of_final_state(self):
        example = self.examples[5]
        needles = [row for row in validate_annotations(example["story"], example["response"]) if row["token"] == "needle"]
        self.assertEqual([row["location"] for row in needles], ["Ava", "Ben"])
        self.assertEqual([row["event"] for row in needles], ["give object", "return object"])
        self.assertEqual(needles[0]["entity_id"], needles[1]["entity_id"])
        denied = next(row for row in self.examples[3]["response"]["annotations"] if row["token"] == "it")
        self.assertIsNone(denied["location"])

    def test_unknown_holder_and_participant_label_drift_fail(self):
        example = self.examples[0]
        for changes in ({"location": "Lili"}, {"location": "unmentioned room"},
                        {"location": "scissors"}, {"event": "give object"}, {"event": None}):
            payload = deepcopy(example["response"])
            scissors = next(row for row in payload["annotations"] if row["token"] == "scissors")
            scissors.update(changes)
            with self.assertRaises(ValueError):
                validate_annotations(example["story"], payload)

    def test_participant_label_cannot_substitute_for_event_trigger(self):
        example = self.examples[0]
        payload = deepcopy(example["response"])
        took = next(row for row in payload["annotations"] if row["token"] == "took")
        took.update(role="other", event_type=None, factuality=None, actor=None, actor_id=None, patients=[])
        with self.assertRaisesRegex(ValueError, "no annotated trigger"):
            validate_annotations(example["story"], payload)

    def test_cache_boundary_and_key_are_shared_across_stories(self):
        a = annotation_request("First story.", prefix=self.prefix)
        b = annotation_request("Entirely different story.", prefix=self.prefix)
        self.assertEqual(a["input"][0], b["input"][0])
        self.assertEqual(a["prompt_cache_key"], b["prompt_cache_key"])
        self.assertNotEqual(a["input"][1], b["input"][1])
        self.assertEqual(a["prompt_cache_options"], {"mode": "explicit", "ttl": "30m"})
        self.assertEqual(a["input"][0]["content"][0]["prompt_cache_breakpoint"], {"mode": "explicit"})
        wire = sdk_kwargs(a)
        self.assertEqual(wire["extra_body"]["prompt_cache_options"], a["prompt_cache_options"])
        self.assertEqual(wire["service_tier"], "flex")
        self.assertEqual(wire["model"], "gpt-6-luna")
        self.assertEqual(wire["input"], a["input"])
        self.assertTrue(wire["text"]["format"]["strict"])
        # Changed shared labels or reasoning must not be confused with the old cache.
        self.assertNotEqual(a["prompt_cache_key"], annotation_request("First story.", prefix=self.prefix + "changed")["prompt_cache_key"])
        self.assertNotEqual(a["prompt_cache_key"], annotation_request("First story.", prefix=self.prefix, reasoning="none")["prompt_cache_key"])

    def test_cache_usage_is_reported_without_claiming_a_hit(self):
        example = self.examples[0]
        body = annotation_request(example["story"], prefix=self.prefix)
        raw = response(example["response"])
        rows, metadata = extract_response(example["story"], body, raw)
        self.assertEqual(metadata["cached_tokens"], 5000)
        raw["usage"]["input_tokens_details"]["cached_tokens"] = 0
        self.assertEqual(extract_response(example["story"], body, raw)[1]["cached_tokens"], 0)
        self.assertEqual(len(rows), len(story_tokens(example["story"])))

    def test_wrong_model_tier_incomplete_and_refusal_fail(self):
        example = self.examples[0]
        body = annotation_request(example["story"], prefix=self.prefix)
        for field, value in (("model", "other"), ("service_tier", "default"), ("status", "incomplete")):
            raw = response(example["response"])
            raw[field] = value
            with self.assertRaises(ValueError):
                extract_response(example["story"], body, raw)
        raw = response(example["response"])
        raw["output"][0]["content"] = [{"type": "refusal", "refusal": "Cannot annotate"}]
        with self.assertRaises(ValueError):
            extract_response(example["story"], body, raw)

    def test_corpus_and_story_file_preserve_whitespace(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "story.txt"
            path.write_bytes(b"  Lily took thread.\r\n\tShe sewed.  ")
            args = SimpleNamespace(story=None, story_file=path)
            self.assertEqual(list(load_stories(args)), ["  Lily took thread.\r\n\tShe sewed.  "])
            args = SimpleNamespace(story=None, story_file=None, input=path, text_key="story", limit=1)
            self.assertEqual(list(load_stories(args)), ["  Lily took thread."])


class DispatchTests(unittest.IsolatedAsyncioTestCase):
    async def test_live_dispatch_and_resume_use_saved_result(self):
        example = json.loads(EXAMPLES.read_text())[0]
        raw = response(example["response"])
        client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(
            return_value=SimpleNamespace(model_dump=lambda **_: raw))))
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            prepare(example["story"], directory)
            first = await annotate_one(directory, client)
            second = await annotate_one(directory, client)
            self.assertEqual(first, second)
            client.responses.create.assert_awaited_once()
            self.assertEqual("".join(row["token"] for row in read(directory / "annotations.json")), example["story"])
            with self.assertRaises(ValueError):
                prepare("Changed story.", directory)

    async def test_uncertain_dispatch_is_not_silently_repeated(self):
        client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(side_effect=TimeoutError())))
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            prepare("Lily took thread.", directory)
            with self.assertRaises(TimeoutError):
                await annotate_one(directory, client)
            with self.assertRaises(RuntimeError):
                await annotate_one(directory, client)
            client.responses.create.assert_awaited_once()

    async def test_invalid_completed_output_is_saved_and_not_rebilled(self):
        raw = response({"annotations": []})
        client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(
            return_value=SimpleNamespace(model_dump=lambda **_: raw))))
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            prepare("Lily took thread.", directory)
            for _ in range(2):
                with self.assertRaises(ValueError):
                    await annotate_one(directory, client)
            client.responses.create.assert_awaited_once()
            self.assertFalse(read(directory / "validation.json")["ok"])
            self.assertFalse((directory / "annotations.json").exists())
            self.assertTrue((directory / "response.json").exists())

    async def test_only_definite_flex_unavailable_retries(self):
        example = json.loads(EXAMPLES.read_text())[0]
        error = RuntimeError("capacity unavailable")
        error.status_code, error.code = 429, "flex_unavailable"
        raw = response(example["response"])
        client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(
            side_effect=[error, SimpleNamespace(model_dump=lambda **_: raw)])))
        with tempfile.TemporaryDirectory() as folder, patch("storyformers.annotate.asyncio.sleep", new=AsyncMock()):
            directory = Path(folder)
            prepare(example["story"], directory)
            await annotate_one(directory, client)
            self.assertEqual(client.responses.create.await_count, 2)
            self.assertEqual(len(list((directory / "attempts").iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
