"""Paired inputs, actual model pricing and one durable campaign cap."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import compare_capability_judges as comparison


class CompareJudgesTests(unittest.TestCase):
    def test_only_model_differs_between_paired_requests(self):
        original = dict(phase="story_quality", stage="demo", input={"stories": []}, body=dict(
            model="gpt-5.6-terra", service_tier="flex", reasoning={"effort": "none"},
            max_output_tokens=4000, input=[{"role": "user", "content": "FROZEN"}]))
        before = deepcopy(original)
        with patch.object(comparison.trial, "jobs_for", return_value=([original], [])):
            jobs, _ = comparison.paired_jobs([])
        a, b = (dict(j["body"]) for j in jobs)
        self.assertEqual((a.pop("model"), b.pop("model")), comparison.MODELS)
        self.assertEqual(a, b)
        self.assertFalse(a["store"])
        self.assertEqual(original, before)

    def test_luna_cost_uses_actual_tier_and_cache_usage(self):
        usage = dict(input_tokens=1000, output_tokens=1000,
                     input_tokens_details=dict(cached_tokens=100, cache_write_tokens=50))
        response = dict(model="gpt-6-luna", service_tier="flex", usage=usage)
        cost = comparison.response_cost(response)
        expected = (850 * .05 + 100 * .005 + 50 * .0625 + 1000 * .25) / 1e6
        self.assertAlmostEqual(cost["usd_low"], expected)
        self.assertEqual(cost["usd_low"], cost["usd_high"])
        self.assertAlmostEqual(comparison.response_cost(dict(response, service_tier="default"))["usd_low"], 2 * expected)
        self.assertFalse(comparison.response_cost(dict(response, model="gpt-6.1-luna"))["known"])

    def test_missing_usage_and_cache_writes_remain_uncertain(self):
        self.assertFalse(comparison.response_cost(dict(model="gpt-6-luna", service_tier="flex"))["known"])
        cost = comparison.response_cost(dict(model="gpt-6-luna", service_tier="flex",
                                             usage=dict(input_tokens=1000, output_tokens=1000)))
        self.assertGreater(cost["usd_high"], cost["usd_low"])

    def test_shared_budget_reserves_terra_ceiling_and_survives_unknown_outcome(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "budget.json"
            budget = comparison.Budget(path, .04)
            request = dict(model="gpt-6-luna", max_output_tokens=2000)
            index = budget.reserve("luna", request)
            self.assertGreater(budget.entries[index]["reserved_usd"], .03)
            resumed = comparison.Budget(path, .04)
            with self.assertRaisesRegex(ValueError, "Budget cap"):
                resumed.reserve("terra", dict(request, model="gpt-5.6-terra"))
            resumed.settle(index, dict(id="test", model="gpt-6-luna", service_tier="flex"))
            self.assertEqual(resumed.entries[index]["reserved_usd"], budget.entries[index]["reserved_usd"])
            with self.assertRaisesRegex(ValueError, "Unapproved"):
                resumed.reserve("other", dict(request, model="gpt-6.1-luna"))

    def test_settlement_uses_luna_price_not_reserved_terra_price(self):
        with tempfile.TemporaryDirectory() as temp:
            budget = comparison.Budget(Path(temp) / "budget.json", 5)
            index = budget.reserve("test", dict(model="gpt-6-luna", max_output_tokens=7000))
            response = dict(id="test", model="gpt-6-luna", service_tier="flex",
                usage=dict(input_tokens=1000, output_tokens=1000, input_tokens_details=dict(cache_write_tokens=0)))
            budget.settle(index, response)
            self.assertAlmostEqual(budget.entries[index]["reserved_usd"], .0003)

    def test_pairing_uses_ids_and_reports_missing_items(self):
        def rating(score, usable):
            return dict(rating=dict(overall=score), usable=usable)
        left = {"a": rating(3, False), "b": rating(8, True), "unpaired": rating(0, False)}
        right = {"b": rating(7, True), "a": rating(6, True)}
        result = comparison.paired_scores(left, right)
        self.assertEqual(result["paired"], 2)
        self.assertEqual(result["terra_only"], 1)
        self.assertEqual(result["mean_delta"], 1)
        self.assertEqual(result["mean_absolute_difference"], 2)
        self.assertEqual(result["within_one_fraction"], .5)
        self.assertEqual(result["usability_counts"]["terra=False,luna=True"], 1)
        self.assertEqual(result["largest_disagreements"][0]["id"], "a")
        self.assertIsNone(comparison.paired_scores({}, {})["mean_delta"])

    def test_prepare_freezes_real_selection_and_refuses_changed_budget(self):
        baseline = Path(__file__).parent / "runs/capability_scoring_v2"
        if not baseline.exists():
            self.skipTest("Local frozen scoring corpus is not present")
        # This integration fixture belongs to the preserved runtime, not the
        # evolving working tree. Production source-lock validation stays on.
        hashes = json.loads((baseline / "source_hashes.json").read_text())
        frozen_sources = {name: baseline / "_source" / name for name in hashes}
        with tempfile.TemporaryDirectory() as temp, patch.object(comparison.trial, "sources", return_value=frozen_sources):
            out = Path(temp) / "comparison"
            jobs, settings = comparison.prepare(baseline, out, 5)
            self.assertEqual((len(jobs), settings["selected_stories"], settings["conversations"]), (18, 30, 180))
            self.assertFalse((out / "budget.json").exists())
            self.assertFalse(list(out.glob("**/*.request.json")))
            comparison.prepare(baseline, out, 5)
            with self.assertRaisesRegex(ValueError, "Frozen comparison"):
                comparison.prepare(baseline, out, 4)

    def review_paths(self):
        runs = Path(__file__).parent / "runs"
        review, previous = runs / "capability_prose_review_v4", runs / "capability_judge_comparison_v1"
        if not review.exists() or not previous.exists():
            self.skipTest("Local frozen prose review is not present")
        return review, previous

    def test_review_replays_saved_stories_and_sends_only_visible_text(self):
        review, previous = self.review_paths()
        hashes = json.loads((review / "source_hashes.json").read_text())
        frozen_sources = {name: review / "_source" / name for name in hashes}
        with tempfile.TemporaryDirectory() as temp, patch.object(comparison.trial, "sources", return_value=frozen_sources):
            out = Path(temp) / "comparison"
            jobs, settings = comparison.prepare_review(review, out, 1, previous)
            self.assertEqual((len(jobs), settings["selected_stories"], settings["conversations"]), (18, 30, 180))
            self.assertEqual(settings["unique_stories_by_world"], dict(library=1, harbor=1, observatory=1))
            self.assertLess(settings["previous_committed_usd"] + settings["budget_usd"], 5)
            self.assertFalse((out / "budget.json").exists())
            for job in jobs:
                body = job["body"]
                self.assertFalse(body["store"])
                payload = json.loads(body["input"][-1]["content"])
                if job["phase"] == "qa_quality":
                    for row in payload:
                        self.assertEqual(set(row), {"id", "story", "conversations"})
                        for conversation in row["conversations"]:
                            for turn in conversation["turns"]:
                                self.assertEqual(set(turn), {"question", "answer"})
                self.assertNotIn('"evidence"', json.dumps(payload))
            comparison.prepare_review(review, out, 1, previous)
            with self.assertRaisesRegex(ValueError, "Frozen comparison"):
                comparison.prepare_review(review, out, 2, previous)

    def test_review_rejects_missing_or_changed_samples(self):
        review, previous = self.review_paths()
        rows = comparison.trial.read_rows(review / "fresh_seeds.jsonl")
        hashes = json.loads((review / "source_hashes.json").read_text())
        frozen_sources = {name: review / "_source" / name for name in hashes}
        with tempfile.TemporaryDirectory() as temp, patch.object(comparison.trial, "sources", return_value=frozen_sources):
            with patch.object(comparison.trial, "read_rows", return_value=rows[:-1]):
                with self.assertRaisesRegex(ValueError, "every matched"):
                    comparison.prepare_review(review, Path(temp) / "missing", 1, previous)
            rows[0]["story"] += " A hidden addition."
            with patch.object(comparison.trial, "read_rows", return_value=rows):
                with self.assertRaisesRegex(ValueError, "does not reproduce"):
                    comparison.prepare_review(review, Path(temp) / "changed", 1, previous)

    def test_review_accounts_for_previous_campaign_spend(self):
        review, previous = self.review_paths()
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "shared \\$5"):
                comparison.prepare_review(review, Path(temp) / "out", 5, previous)
            unknown = Path(temp) / "unknown"
            unknown.mkdir()
            (unknown / "budget.json").write_text(json.dumps(dict(entries=[dict(status="reserved", reserved_usd=.1)])))
            with self.assertRaisesRegex(ValueError, "unknown reservations"):
                comparison.prepare_review(review, Path(temp) / "out", 1, unknown)


if __name__ == "__main__":
    unittest.main()
