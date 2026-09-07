import asyncio
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

import openai_world_set_quality as judge
import trial_cost


class SetQualityTest(unittest.TestCase):
    def setUp(self):
        self.item = judge.select_set("test.py", [dict(story=f"Story {i % 3}.") for i in range(100)], 777)
        self.value = dict(
            stories=[dict(id=row["id"], rating={key: 7 + i % 2 for key in judge.legacy.RATING_KEYS}, note="Complete story.")
                     for i, row in enumerate(self.item["stories"])],
            diversity={key: 2 for key in judge.DIVERSITY_KEYS}, diversity_evidence="Same plot across samples.",
            plot_groups=[dict(story_ids=[row["id"] for row in self.item["stories"]], summary="Same causal structure.")])

    def test_selection_reproducible_not_deduplicated(self):
        same = judge.select_set("other.py", [dict(story=f"Story {i % 3}.") for i in range(100)], 777)
        self.assertEqual(same["stories"], self.item["stories"])
        self.assertEqual(len(self.item["stories"]), 10)
        self.assertEqual(len({row["id"] for row in self.item["stories"]}), 10)
        self.assertLessEqual(len({row["story"] for row in self.item["stories"]}), 3)
        with self.assertRaises(ValueError):
            judge.select_set("test", [dict(story="Only one.")], 1)

    def test_request_explicit_terra_flex_no_reasoning(self):
        body = judge.request_body(self.item)
        self.assertEqual(body["model"], "gpt-5.6-terra")
        self.assertEqual(body["service_tier"], "flex")
        self.assertEqual(body["reasoning"], dict(effort="none"))
        self.assertEqual(body["text"]["format"]["schema"]["properties"]["stories"]["minItems"], 10)

    def test_validate_preserves_fractional_world_means(self):
        rating = judge.validate(self.value, self.item)
        self.assertEqual(rating["rating"]["overall"], 7.5)
        self.assertEqual(rating["judged_stories"], 10)
        summary = judge.summarize([dict(ok=True, **rating)])
        self.assertEqual(summary["mean_quality"]["overall"], 7.5)
        self.assertEqual(summary["rated_stories"], 10)

    def test_validation_fails_closed(self):
        edits = [lambda v: v["stories"].pop(),
                 lambda v: v["stories"][0].update(id=v["stories"][1]["id"]),
                 lambda v: v["stories"][0]["rating"].update(overall=True),
                 lambda v: v["diversity"].update(overall=10),
                 lambda v: v["plot_groups"][0]["story_ids"].pop(),
                 lambda v: v["plot_groups"][0]["story_ids"].append("unknown"),
                 lambda v: v["plot_groups"][0].update(summary=""),
                 lambda v: v.update(diversity_evidence="")]
        for edit in edits:
            value = copy.deepcopy(self.value)
            edit(value)
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                judge.validate(value, self.item)

    def test_no_commentary_in_final_json(self):
        body = dict(output=[dict(type="message", phase="commentary", content=[dict(type="output_text", text="Examining stories")]),
                            dict(type="message", phase="final_answer", content=[dict(type="output_text", text="{}")])])
        self.assertEqual(judge.final_text(body), "{}")

    def test_paid_request_artifacts_errors_and_no_overwrite(self):
        client = AsyncMock()
        client.__aenter__.return_value = client
        body = dict(id="r1", model="gpt-5.6-terra", service_tier="flex", status="completed",
                    usage=dict(input_tokens=6000, output_tokens=1800),
                    output=[dict(type="message", content=[dict(type="output_text", text=json.dumps(self.value))])])
        response = Mock()
        response.model_dump.return_value = body
        client.responses.create.return_value = response
        with tempfile.TemporaryDirectory() as tmp, patch("openai.AsyncOpenAI", return_value=client) as factory:
            path = Path(tmp) / "eval"
            rows = asyncio.run(judge.run_sets([self.item], path))
            factory.assert_called_once_with(base_url="https://api.openai.com/v1", timeout=900.0, max_retries=0)
            self.assertTrue(rows[0]["ok"])
            self.assertTrue((path / "response_000.json").exists())
            self.assertTrue((path / "requests.jsonl").exists())
            with self.assertRaises(FileExistsError):
                asyncio.run(judge.run_sets([self.item], path))
            self.assertEqual(client.responses.create.await_count, 1)
            body["status"] = "incomplete"
            failed = asyncio.run(judge.run_sets([self.item], Path(tmp) / "bad"))
            self.assertFalse(failed[0]["ok"])
            self.assertIn("usage", failed[0]["response"])
            self.assertEqual(trial_cost.summarize(failed)["priced_requests"], 1)

    def test_dry_run_never_constructs_client(self):
        with tempfile.TemporaryDirectory() as tmp, patch("openai.AsyncOpenAI", side_effect=AssertionError("no API")):
            path = Path(tmp) / "dry"
            asyncio.run(judge.run_sets([self.item], path, dry_run=True))
            self.assertTrue((path / "inputs.json").exists())
            self.assertFalse((path / "attempts.jsonl").exists())


class TrialCostTest(unittest.TestCase):
    def test_cache_writes_reads_output_not_double_counted(self):
        usage = dict(input_tokens=10000, input_tokens_details=dict(cached_tokens=2000, cache_write_tokens=3000), output_tokens=4000)
        cost = trial_cost.token_cost("gpt-5.6-luna-2026-08-01", usage)
        self.assertAlmostEqual(cost["usd_low"], (5000*.1 + 2000*.01 + 3000*.125 + 4000*.6)/1e6)
        self.assertEqual(cost["usd_low"], cost["usd_high"])
        self.assertEqual(trial_cost.token_cost("gpt-5.6-luna", usage, "default")["usd_low"], 2*cost["usd_low"])

    def test_missing_cache_writes_bounded_and_actual_tier_used(self):
        usage = dict(input_tokens=6000, output_tokens=1800)
        cost = trial_cost.token_cost("gpt-5.6-terra", usage)
        self.assertAlmostEqual(cost["usd_low"], .0168)
        self.assertAlmostEqual(cost["usd_high"], .0183)
        summary = trial_cost.summarize([dict(response=dict(model="gpt-5.6-terra", usage=usage)), dict(error="timeout")])
        self.assertEqual(summary["unpriced_requests"], 2)
        self.assertFalse(trial_cost.token_cost("unknown", usage)["known"])


if __name__ == "__main__":
    unittest.main()
