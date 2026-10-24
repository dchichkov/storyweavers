import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import literary_calibration as calibration


class LiteraryCalibrationTests(unittest.TestCase):
    def cases(self):
        return {name: f"Visible story about {name}." for name in (
            "crate", "paint", "discovery", "gift", "apology", "puddles", "nell",
            "race", "discovery_log", "puddles_contradiction")}

    def test_pairs_reverse_exact_stories_without_provenance(self):
        cases = self.cases()
        ids, pairs = calibration.pairings(cases)
        stories = {ids[k]: v for k, v in cases.items()}
        jobs = calibration.jobs_for(stories, pairs)
        self.assertEqual(len(jobs), 32)
        for model in calibration.comparison.MODELS:
            for pair in pairs:
                pair_jobs = {j["orientation"]: j for j in jobs if j["model"] == model and j["pair_id"] == pair["id"]}
                fwd, rev = (json.loads(pair_jobs[k]["body"]["input"][1]["content"]) for k in ("forward", "reverse"))
                self.assertEqual(set(fwd), {"A", "B"})
                self.assertEqual(fwd["A"], rev["B"])
                self.assertEqual(fwd["B"], rev["A"])
                self.assertEqual(pair_jobs["forward"]["body"]["service_tier"], "flex")
                self.assertFalse(pair_jobs["forward"]["body"]["store"])

    def test_validation_rejects_wrong_side_or_fabricated_evidence(self):
        valid = dict(preferred="A", acceptable_A=True, acceptable_B=False,
                     reason="A resolves its premise.", evidence_A="Alpha", evidence_B="Beta")
        self.assertEqual(calibration.validate(valid, "Alpha wins.", "Beta waits."), valid)
        for update in ({"evidence_A": "Beta"}, {"evidence_B": "invented"},
                       {"preferred": "source one"}, {"acceptable_A": 1}, {"reason": ""}, {"source": "known"}):
            with self.assertRaises(ValueError):
                calibration.validate(dict(valid, **update), "Alpha wins.", "Beta waits.")

    def test_order_bias_is_not_counted_as_agreement(self):
        pair = dict(id="p00", left="s00", right="s01")
        rows = []
        for orientation, a, b in (("forward", "s00", "s01"), ("reverse", "s01", "s00")):
            rows.append(dict(model=calibration.comparison.MODELS[0], pair_id="p00", orientation=orientation,
                stage=orientation, A=a, B=b, ok=True,
                assessment=dict(preferred="A", acceptable_A=True, acceptable_B=False)))
        report = calibration.summarize(rows, [pair], {"p00": "left"})
        arm = report["arms"][calibration.comparison.MODELS[0]]
        self.assertEqual(arm["complete_pairs"], 1)
        self.assertEqual(arm["order_consistent_pairs"], 0)
        self.assertEqual(arm["human_matched_pairs"], 0)
        self.assertFalse(arm["pairs"][0]["acceptance_agreement"])

    def test_quote_wrappers_do_not_change_the_verified_words(self):
        text = "Alpha wins. Beta waits."
        for evidence in ('"Alpha wins."', '\u201cAlpha wins.\u201d', "'Alpha wins.'"):
            self.assertEqual(calibration.quoted_excerpt(evidence, text), "Alpha wins.")
        for evidence in ('"Alpha wins" conflicts with "Beta waits"', '"Alpha loses."', "", '""'):
            self.assertIsNone(calibration.quoted_excerpt(evidence, text))

    def test_reversed_answers_map_to_same_preference(self):
        pair = dict(id="p00", left="s00", right="s01")
        rows = [dict(model=calibration.comparison.MODELS[0], pair_id="p00", stage=o, orientation=o,
            A=a, B=b, ok=True, assessment=dict(preferred=p, acceptable_A=accept_a, acceptable_B=not accept_a))
            for o, a, b, p, accept_a in (("forward", "s00", "s01", "A", True), ("reverse", "s01", "s00", "B", False))]
        report = calibration.summarize(rows, [pair], {"p00": "left"})
        arm = report["arms"][calibration.comparison.MODELS[0]]
        self.assertEqual(arm["human_matched_pairs"], 1)
        self.assertTrue(arm["pairs"][0]["acceptance_agreement"])

    def test_missing_results_and_labels_are_not_success(self):
        pair = dict(id="p00", left="s00", right="s01")
        report = calibration.summarize([], [pair], {"p00": None})
        self.assertIn("uncalibrated", report["calibration_status"])
        for arm in report["arms"].values():
            self.assertEqual(arm["complete_pairs"], 0)
            self.assertEqual(arm["human_compared_pairs"], 0)
        with self.assertRaises(ValueError):
            calibration.summarize([], [pair], {"p00": "presumed better"})

    def test_offline_revalidation_preserves_originals_without_api(self):
        model = calibration.comparison.MODELS[0]
        stories = {"s00": "Alpha wins.", "s01": "Beta waits."}
        pairs = [dict(id="p00", left="s00", right="s01")]
        job = dict(model=model, stage="p00_forward", pair_id="p00", orientation="forward", A="s00", B="s01", body={})
        value = dict(preferred="A", acceptable_A=True, acceptable_B=False,
                     reason="A resolves the action.", evidence_A='"Alpha wins."', evidence_B='"Beta waits."')
        response = dict(model=model, service_tier="flex", status="completed", output=[dict(type="message",
            content=[dict(type="output_text", text=json.dumps(value))])])
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            directory = out / model
            directory.mkdir()
            calibration.f.save(directory / "p00_forward.request.json", {})
            calibration.f.save(directory / "p00_forward.response.json", response)
            original = directory / "p00_forward.result.json"
            calibration.f.save(original, dict(job, ok=False, error="original quote error"))
            before = original.read_bytes()
            calibration.f.save(out / "human_labels.json", {"p00": None})
            with patch.object(calibration, "load", return_value=({}, stories, pairs, [job])), \
                    patch.object(calibration.f, "api_artifact", side_effect=AssertionError("No paid retry")) as api:
                report = calibration.revalidate(out)
                api.assert_not_called()
            self.assertEqual(original.read_bytes(), before)
            self.assertEqual(report["additional_api_calls"], 0)
            result = json.loads((out / "revalidated_quotes_v2" / model / original.name).read_text())
            self.assertTrue(result["ok"])
            self.assertEqual(result["verified_excerpts"], dict(A="Alpha wins.", B="Beta waits."))

    def test_sampling_reproduces_and_restores_global_random(self):
        before = random.getstate()
        cases, sources = calibration.select_cases()
        self.assertEqual(before, random.getstate())
        self.assertEqual((cases, sources), calibration.select_cases())
        self.assertEqual(len(cases), 10)
        self.assertIn("The second trip was as real as the first", cases["paint"])
        self.assertEqual(sources["puddles"]["sample_id"], "s000276")

    def test_frozen_inputs_and_planned_requests_cannot_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.py"
            source.write_text("pass\n")
            campaign = root / "campaign"
            campaign.mkdir()
            (campaign / "settings.json").write_text("{}")
            money = dict(remaining_cap_usd=9, previous_committed_usd=1, authorized_usd=10,
                         authorization_sha256="amendment")
            cases = self.cases()
            with patch.object(calibration, "source_files", return_value={"source.py": source}), \
                    patch.object(calibration, "select_cases", return_value=(cases, {k: {} for k in cases})), \
                    patch.object(calibration.harbor, "campaign", return_value=money):
                out = root / "batch"
                calibration.prepare(out, campaign)
                _, _, _, jobs = calibration.load(out)
                with self.assertRaises(ValueError):
                    calibration.prepare(out, campaign)
                job = jobs[0]
                plan = out / job["model"] / f"{job['stage']}.planned.json"
                plan.write_text("{}")
                with self.assertRaisesRegex(ValueError, "Planned request changed"):
                    calibration.load(out)
                calibration.f.save(plan, job["body"])
                (out / "stories.json").write_text("{}")
                with self.assertRaisesRegex(ValueError, "Frozen input changed"):
                    calibration.load(out)


if __name__ == "__main__":
    unittest.main()
