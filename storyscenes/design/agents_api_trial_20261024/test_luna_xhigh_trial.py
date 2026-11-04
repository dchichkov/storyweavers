import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import luna_xhigh_trial as trial


class XHighTrialTests(unittest.TestCase):
    def test_only_effort_changes_and_control_is_preserved(self):
        original = (trial.BASE / "request.json").read_bytes()
        with tempfile.TemporaryDirectory() as td:
            arm = Path(td) / "xhigh"
            with patch.object(trial, "ARM", arm):
                trial.prepare()
                with self.assertRaises(FileExistsError):
                    trial.prepare()
            before = json.loads(original)
            after = json.loads((arm / "request.json").read_text())
            self.assertEqual({k for k in before if before[k] != after[k]}, {"reasoning"})
            self.assertEqual(after["reasoning"], {"effort": "xhigh"})
            self.assertEqual(after["max_output_tokens"], 64000)
            settings = json.loads((arm / "settings.json").read_text())
            for name, expected in settings["source_hashes"].items():
                self.assertEqual(trial.api.digest((arm / "input" / name).read_bytes()), expected)
        self.assertEqual(original, (trial.BASE / "request.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
