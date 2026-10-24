"""Fresh scoring adapter must preserve failures, protocols, budget and provenance."""
from copy import deepcopy
import json
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch

import capability_trial as trial


class CapabilityTrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row, cls.trace = trial.sample_one(("library", 19000, 6000, 5.0))
        assert cls.row["ok"], cls.row

    def test_real_seeded_output_is_replay_verified_without_pinned_flourishes(self):
        row = self.row
        self.assertEqual(row["sample_id"], "library:19000")
        self.assertTrue(row["trace_sha256"])
        self.assertNotIn("opening", {s["id"] for s in self.trace["statements"]})
        self.assertNotIn("ending", {s["id"] for s in self.trace["statements"]})
        again, _ = trial.sample_one(("library", 19000, 6000, 5.0))
        for key in ("story", "path", "qa", "conversations", "trace_sha256"):
            self.assertEqual(again[key], row[key])

    def test_timeout_is_retained_as_failure_and_timer_is_cleared(self):
        row, trace = trial.sample_one(("choice", 19000, 6000, 0.000001))
        self.assertFalse(row["ok"])
        self.assertEqual(row["error_type"], "CPUTimeout")
        self.assertIsNone(trace)
        self.assertEqual(signal.getitimer(signal.ITIMER_PROF), (0.0, 0.0))

    def test_parent_kills_and_reaps_child_on_wall_timeout(self):
        row, trace = trial.supervise(("choice", 19000, 6000, 100), .001)
        self.assertEqual(row["error_type"], "WallTimeout")
        self.assertFalse(row["ok"])
        self.assertIsNone(row["cpu_seconds"])
        self.assertIsNone(trace)

    def test_supervisor_returns_actual_replay_verified_output(self):
        row, trace = trial.supervise(("library", 19000, 6000, 5), 10)
        self.assertEqual(row["story"], self.row["story"])
        self.assertEqual(trace, json.loads(json.dumps(self.trace)))

    def test_interruption_cancels_queued_sampling(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(trial, "supervise", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                trial.prepare(Path(temp) / "trial", count=2, workers=1)

    def test_quality_selection_retains_duplicates_and_does_not_send_hidden_trace(self):
        rows = [dict(deepcopy(self.row), seed=i, sample_id=f"library:{i}", hidden="DO_NOT_SEND_TRACE") for i in range(20)]
        rows.append(dict(world="library", seed=100, sample_id="library:100", ok=False, error_type="TimeoutError"))
        jobs, selected = trial.jobs_for(rows)
        self.assertEqual(len(selected), 10)
        self.assertEqual(len({r["story"] for r in selected}), 1)
        self.assertEqual(len(jobs), 3)
        for job in jobs:
            self.assertEqual(job["body"]["model"], "gpt-5.6-terra")
            self.assertEqual(job["body"]["service_tier"], "flex")
            self.assertNotIn("DO_NOT_SEND_TRACE", json.dumps(job["body"]))
            self.assertNotIn("trace_sha256", json.dumps(job["body"]))
        self.assertEqual(jobs[0]["body"], trial.f.quality.request_body(jobs[0]["input"], cache_prompts=True))
        self.assertEqual(jobs[1]["body"], trial.cq.request_body(jobs[1]["input"]))

    def test_mechanical_summary_does_not_drop_failure_denominator(self):
        bad = dict(world="library", ok=False, error_type="TimeoutError", cpu_seconds=2)
        report = trial.mechanical_summary([self.row, bad], 2)
        self.assertFalse(report["complete"])
        self.assertEqual(report["requested"], 8)
        library = report["worlds"]["library"]
        self.assertEqual((library["attempts"], library["returned"], library["exact_unique"]), (2, 1, 1))
        self.assertEqual(library["failures"], {"TimeoutError": 1})

    def test_prepare_resume_preserves_existing_attempts_and_freezes_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "trial"
            trial.prepare(out, count=1, workers=2, cpu_seconds=.01)
            before = (out / "attempts.jsonl").read_bytes()
            self.assertEqual(len(trial.read_rows(out / "attempts.jsonl")), 4)
            self.assertTrue((out / "stories.jsonl.xz").exists())
            self.assertTrue((out / "_source/storyscenes/capabilities/core.py").exists())
            trial.prepare(out, count=1, workers=2, cpu_seconds=.01)
            self.assertEqual((out / "attempts.jsonl").read_bytes(), before)
            with self.assertRaisesRegex(ValueError, "changed trial settings"):
                trial.prepare(out, count=2, workers=2, cpu_seconds=.01)

    def test_budget_reservations_survive_resume_and_uncertain_outcomes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "budget.json"
            budget = trial.f.Budget(path, .05)
            body = dict(model="gpt-5.6-terra", max_output_tokens=2000)
            budget.reserve("first", body)
            resumed = trial.f.Budget(path, .05)
            with self.assertRaisesRegex(ValueError, "Budget cap"):
                resumed.reserve("second", body)
            self.assertEqual(len(resumed.entries), 1)
            self.assertEqual(resumed.entries[0]["status"], "reserved")


if __name__ == "__main__":
    unittest.main()
