"""The sample ladder must not quietly subsample or deduplicate judge inputs."""
from copy import deepcopy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import harbor_trial as trial


class HarborTrialTests(unittest.TestCase):
    def test_cap_increase_is_additive_preserves_history_and_counts_old_reserves(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            prior = root / "prior"
            prior.mkdir()
            trial.f.save(prior / "budget.json", dict(entries=[dict(reserved_usd=1.5, status="unknown")]))
            with patch.object(trial, "PRIOR", (prior,)):
                path = root / "campaign"
                before = trial.campaign(path)
                original = (path / "settings.json").read_bytes()
                trial.f.save(path / "authorization_increase.json", dict(previous_authorized_usd=5,
                    authorized_usd=10, previous_settings_sha256=trial.f.digest(path / "settings.json")))
                after = trial.campaign(path)
                self.assertEqual(before["remaining_cap_usd"], 3.5)
                self.assertEqual(after["remaining_cap_usd"], 8.5)
                self.assertEqual(after["authorized_usd"], 10)
                self.assertEqual((path / "settings.json").read_bytes(), original)
                self.assertIn("authorization_sha256", after)
                trial.f.save(path / "authorization_increase.json", dict(previous_authorized_usd=5,
                    authorized_usd=11, previous_settings_sha256=trial.f.digest(path / "settings.json")))
                with self.assertRaisesRegex(ValueError, "Unrecognized"):
                    trial.campaign(path)

    def rows(self, count):
        return [dict(sample_id=f"harbor:{i}", world="harbor", seed=i, ok=True,
                     story="Deliberately identical visible story.", hidden_trace="DO NOT SEND",
                     conversations=[dict(id=f"c{j}", turns=[dict(question="What happened?", answer="A complete visible answer.")])
                                    for j in range(6)]) for i in range(count)]

    def test_every_position_is_graded_together_at_each_stage(self):
        for count in (10, 30, 100):
            with self.subTest(count=count):
                jobs, selected = trial.paired_jobs(self.rows(count))
                self.assertEqual(len(selected), count)
                self.assertEqual(len({r["sample_id"] for r in selected}), count)
                for model in trial.comparison.MODELS:
                    arm = [j for j in jobs if j["model"] == model]
                    stories = [j for j in arm if j["phase"] == "story_quality"]
                    self.assertEqual(len(stories), 1)
                    self.assertEqual(len(stories[0]["input"]["stories"]), count)
                    payload = json.loads(stories[0]["body"]["input"][-1]["content"])
                    self.assertEqual(len(payload["stories"]), count)
                    self.assertEqual(len({r["story"] for r in payload["stories"]}), 1)
                    qa = [j for j in arm if j["phase"] == "qa_quality"]
                    self.assertEqual(sum(len(j["input"]) for j in qa), count)
                for job in jobs:
                    self.assertNotIn("DO NOT SEND", json.dumps(job["body"]))

    def test_pair_differs_only_in_model(self):
        jobs, _ = trial.paired_jobs(self.rows(30))
        for first, second in zip(jobs[::2], jobs[1::2]):
            a, b = deepcopy(first["body"]), deepcopy(second["body"])
            self.assertEqual((a.pop("model"), b.pop("model")), trial.comparison.MODELS)
            self.assertEqual(a, b)
            self.assertFalse(a["store"])
            self.assertEqual(a["service_tier"], "flex")

    def test_local_failures_are_not_silently_filtered(self):
        rows = self.rows(10)
        rows[5]["ok"] = False
        with self.assertRaisesRegex(ValueError, "Complete valid"):
            trial.paired_jobs(rows)

    def test_group_membership_is_attached_to_every_rating(self):
        quality = trial.f.quality
        item = quality.select_set("harbor", self.rows(2), 777, count=2)
        value = dict(stories=[dict(id=s["id"], rating={k: 7 for k in quality.legacy.RATING_KEYS},
                                  note="Grounded note.", group_id=0) for s in item["stories"]],
                     diversity={k: 3 for k in quality.DIVERSITY_KEYS}, diversity_evidence="Repeated plot.",
                     plot_groups=[dict(group_id=0, summary="Same plot.")])
        result = trial.harbor_judge_protocol.validate(quality, value, item)
        self.assertEqual(result["judged_stories"], 2)
        self.assertEqual(set(result["plot_groups"][0]["story_ids"]), {s["id"] for s in item["stories"]})
        body = trial.harbor_judge_protocol.request_body(quality, item)
        self.assertTrue(body["input"][0]["content"].startswith(quality.SYSTEM))
        broken = deepcopy(value)
        broken["stories"][0]["group_id"] = 1
        with self.assertRaisesRegex(ValueError, "undefined"):
            trial.harbor_judge_protocol.validate(quality, broken, item)
        broken = deepcopy(value)
        broken["stories"][0]["id"] = broken["stories"][1]["id"]
        with self.assertRaisesRegex(ValueError, "IDs"):
            trial.harbor_judge_protocol.validate(quality, broken, item)

    def test_story_only_mode_does_not_repeat_qa(self):
        jobs, selected = trial.paired_jobs(self.rows(30), story_only=True)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(len(selected), 30)
        self.assertEqual({j["phase"] for j in jobs}, {"story_quality"})

    def test_replication_identity_and_sources_are_not_harbor_only(self):
        rows = self.rows(10)
        for row in rows:
            row.update(world="greenhouse", sample_id=f"greenhouse:{row['seed']}")
        jobs, _ = trial.paired_jobs(rows)
        self.assertEqual(jobs[0]["stage"], "greenhouse")
        self.assertIn("storyscenes/greenhouse_story.py", trial.sources("greenhouse"))
        self.assertIn("storyscenes/greenhouse_prose.py", trial.sources("greenhouse"))
        rows[0]["world"] = "harbor"
        with self.assertRaisesRegex(ValueError, "exactly one"):
            trial.paired_jobs(rows)


if __name__ == "__main__":
    unittest.main()
