import json
from pathlib import Path
import tempfile
import unittest

import luna6_reasoning_trial as trial


class TrialAccountingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "ledger.json"
        self.ledger = trial.Ledger(self.path)
        self.body = {"input": [{"role": "user", "content": "Hello"}], "max_output_tokens": 32000}

    def test_unknown_attempt_cannot_be_repeated_after_restart(self):
        self.ledger.reserve("request", self.body)
        restarted = trial.Ledger(self.path)
        with self.assertRaisesRegex(ValueError, "never automatically repeated"):
            restarted.reserve("request", self.body)
        self.assertGreater(restarted.total(), 0)

    def test_cap_is_checked_before_new_entry(self):
        self.ledger.data["cap_usd"] = .000001
        with self.assertRaisesRegex(ValueError, "cap reached"):
            self.ledger.reserve("request", self.body)
        self.assertEqual(self.ledger.data["entries"], {})

    def test_missing_usage_and_wrong_tier_keep_reservation(self):
        self.ledger.reserve("request", self.body)
        reserved = self.ledger.total()
        self.ledger.settle("request", {"model": trial.MODEL, "service_tier": "flex"})
        self.assertEqual(self.ledger.total(), reserved)
        self.ledger.settle("request", {"model": trial.MODEL, "service_tier": "default",
            "usage": {"input_tokens": 100, "output_tokens": 10}})
        self.assertEqual(self.ledger.total(), reserved)

    def test_reasoning_in_output_is_not_subtracted(self):
        usage = {"input_tokens": 100, "output_tokens": 1000,
                 "output_tokens_details": {"reasoning_tokens": 900}}
        self.assertGreater(trial.cost(usage), .00025)

    def test_unexpected_model_tier_and_incomplete_rejected(self):
        valid = {"model": trial.MODEL, "service_tier": "flex", "status": "completed"}
        trial.ensure_response(valid)
        for change in ({"model": "gpt-6.1-sol"}, {"service_tier": "default"}, {"status": "incomplete"}):
            with self.assertRaises(ValueError):
                trial.ensure_response(dict(valid, **change))

    def test_sdk_adapter_preserves_explicit_cache_wire_fields(self):
        body = {"prompt_cache_options": {"mode": "explicit", "ttl": "30m"},
                "input": [{"content": [{"text": "x", "prompt_cache_breakpoint": {"mode": "explicit"}}]}]}
        adapted = trial.sdk_body(body)
        self.assertIn("prompt_cache_options", body)
        self.assertEqual(adapted["extra_body"]["prompt_cache_options"], body["prompt_cache_options"])
        self.assertEqual(adapted["input"], body["input"])


if __name__ == "__main__":
    unittest.main()
