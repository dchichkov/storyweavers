"""Offline checks for sampling integrity and strict judge-result validation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from . import judge


class JudgeTests(unittest.TestCase):
    def fixture(self):
        rows = judge.sample_pool("rescue", 2, 777)
        item = judge.quality.select_set("rescue", rows, 777, count=2)
        value = dict(stories=[dict(id=s["id"], group_id=0, note="Readable but repetitive.",
            rating={k: 6 for k in judge.quality.legacy.RATING_KEYS}) for s in item["stories"]],
            diversity={k: 2 for k in judge.quality.DIVERSITY_KEYS},
            diversity_evidence="Both stories use the same rescue plot.",
            plot_groups=[dict(group_id=0, summary="Rescue an animal using a ladder.")])
        response = dict(model=judge.MODEL, status="completed", service_tier="flex",
            output=[dict(type="message", content=[dict(type="output_text", text=json.dumps(value))])])
        return item, value, response

    def test_reproducible_sampling_without_deduplication(self):
        rows = judge.sample_pool("kite", 4, 777)
        self.assertEqual(rows, judge.sample_pool("kite", 4, 777))
        self.assertEqual([r["seed"] for r in rows], [777, 778, 779, 780])
        repeated = [rows[0]] * 4
        item = judge.quality.select_set("kite", repeated, 777, count=3)
        self.assertEqual(len(item["stories"]), 3)
        self.assertEqual(len({s["id"] for s in item["stories"]}), 3)
        metrics = judge.diversity_metrics(repeated)
        self.assertEqual(metrics["exact_unique_texts"], 1)
        self.assertEqual(metrics["unique_event_kind_paths"], 1)
        self.assertEqual(metrics["mean_pairwise_trigram_jaccard"], 1)

    def test_cosmetic_variation_does_not_inflate_event_paths(self):
        rows = judge.sample_pool("rescue", 2, 777)
        rows[1] = deepcopy(rows[0])
        rows[1]["story"] += " A different phrase."
        metrics = judge.diversity_metrics(rows)
        self.assertEqual(metrics["exact_unique_texts"], 2)
        self.assertEqual(metrics["unique_event_kind_paths"], 1)

    def test_strict_id_and_plot_partition(self):
        item, value, response = self.fixture()
        result = judge.assess(response, item)
        self.assertEqual(result["judged_stories"], 2)
        self.assertEqual(result["rating"]["overall"], 6)
        for change in ("duplicate", "missing_group", "score"):
            bad = deepcopy(value)
            if change == "duplicate":
                bad["stories"][1]["id"] = bad["stories"][0]["id"]
            elif change == "missing_group":
                bad["stories"][0]["group_id"] = 1
            else:
                bad["stories"][0]["rating"]["overall"] = 10
            with self.assertRaises(ValueError):
                judge.protocol.validate(judge.quality, bad, item)

    def test_wrong_model_tier_or_incomplete_is_rejected(self):
        item, _, response = self.fixture()
        for key, value in (("model", "other-model"), ("service_tier", "default"), ("status", "incomplete")):
            with self.assertRaises(ValueError):
                judge.assess(dict(response, **{key: value}), item)

    def test_retry_only_definite_flex_rejections_and_preserve_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            judge.save(out / "dispatch.json", {"idempotency_key": "first"})
            judge.save(out / "result.json", dict(ok=False, error="timeout"))
            with self.assertRaises(ValueError):
                judge.retry_unavailable(out)
            self.assertTrue((out / "dispatch.json").exists())
            judge.save(out / "result.json", dict(ok=False, http_status=429, error_code="flex_unavailable"))
            judge.retry_unavailable(out)
            self.assertFalse((out / "dispatch.json").exists())
            self.assertEqual(judge.read(out / "rejected_attempts/1/dispatch.json")["idempotency_key"], "first")
            self.assertEqual(judge.read(out / "rejected_attempts/1/result.json")["http_status"], 429)

    def test_prepare_keeps_world_state_out_of_judge_prompt_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "run"
            judge.prepare(out, pool_size=3, judge_count=2)
            self.assertFalse(judge.read(out / "summary.json")["complete"])
            settings = judge.verify_artifacts(out)
            self.assertEqual(settings["model"], judge.MODEL)
            request = judge.read(out / "rescue/request.json")
            payload = json.loads(request["input"][1]["content"])
            self.assertEqual(set(payload), {"calibration", "stories"})
            for story in payload["stories"]:
                self.assertEqual(set(story), {"id", "story"})
            self.assertEqual(payload["calibration"]["rating"], judge.quality.legacy.BASELINE_RATING)
            self.assertTrue(request["input"][0]["content"].startswith(judge.quality.SYSTEM))
            with self.assertRaises(FileExistsError):
                judge.prepare(out, pool_size=3, judge_count=2)
            (out / "rescue/request.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "artifact changed"):
                judge.verify_artifacts(out)


if __name__ == "__main__":
    unittest.main()
