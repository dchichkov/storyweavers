import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import luna_direct_stories as direct


class DirectStoriesTests(unittest.TestCase):
    def test_matched_requests_and_budget_bound(self):
        entries = direct.read(direct.MANIFEST)["entries"]
        self.assertEqual(len(entries), 20)
        for entry in entries:
            body = direct.request(entry)
            self.assertEqual(body["reasoning"], {"effort": "high"})
            self.assertEqual(body["model"], "gpt-6-luna")
            self.assertEqual(body["service_tier"], "flex")
            self.assertIn("750-850", body["input"])
            for value in [entry["premise"], entry["setting"], str(entry["task_seed"]), *entry["words"]]:
                self.assertIn(value, body["input"])
            ceiling = direct.api.usage_cost("gpt-6-luna", dict(
                input_tokens=len(json.dumps(body).encode()) + 4000,
                output_tokens=body["max_output_tokens"]))
            self.assertLess(ceiling, .03)

    def test_judge_includes_every_row_and_keeps_rubric(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(direct, "OUT", Path(tmp)):
            rows = [dict(story=f"Story number {i}.") for i in range(20)]
            direct.api.save(Path(tmp) / "stories.json", rows)
            with patch.object(direct, "verify", return_value={"source_hashes": {}}):
                direct.prepare_judge()
            item = direct.read(Path(tmp) / "quality/input.json")
            body = direct.read(Path(tmp) / "quality/request.json")
            self.assertEqual({s["source_index"] for s in item["stories"]}, set(range(20)))
            original = direct.protocol.request_body(direct.quality, item)
            self.assertEqual(body["text"], original["text"])
            self.assertEqual(body["input"][1], original["input"][1])
            self.assertEqual(body["model"], "gpt-5.6-terra")
            self.assertNotIn("ONE procedural StoryWorld", body["input"][0]["content"])


if __name__ == "__main__":
    unittest.main()
