import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import judge_stories as judge
import luna_high_trial as trial


class HighTrialTests(unittest.TestCase):
    def test_duplicate_normalization_is_exact_and_conflicts_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw, fixed = root / "raw", root / "fixed"
            (raw / "input").mkdir(parents=True)
            trial.api.save(raw / "settings.json", {})
            rows = [dict(path=trial.api.PREFIX + name, content=name) for name in
                ("__init__.py", "world.py", "test_world.py", "reference_story.md", "scene_inventory.json", "README.md")]
            trial.api.save(raw / "bundle.json", dict(files=rows + [rows[3]]))
            with patch.object(trial, "ARM", raw), patch.object(trial, "NORMALIZED", fixed):
                trial.normalize_identical_duplicates()
                self.assertEqual(json.loads((fixed / "bundle.json").read_text())["files"], rows)
                trial.api.save(raw / "bundle.json", dict(files=rows + [dict(path=rows[3]["path"], content="different")]))
                with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
                    trial.normalize_identical_duplicates()

    def test_variant_changes_only_reasoning_and_headroom(self):
        with tempfile.TemporaryDirectory() as td:
            arm = Path(td) / "high"
            with patch.object(trial, "ARM", arm):
                trial.prepare()
                with self.assertRaises(FileExistsError):
                    trial.prepare()
            old = json.loads((trial.BASE / "request.json").read_text())
            new = json.loads((arm / "request.json").read_text())
            self.assertEqual({k for k in old if old[k] != new[k]}, {"reasoning", "max_output_tokens"})
            self.assertEqual(new["reasoning"], {"effort": "high"})
            self.assertEqual(new["max_output_tokens"], 64000)
            settings = json.loads((arm / "settings.json").read_text())
            for name, expected in settings["source_hashes"].items():
                self.assertEqual(trial.api.digest((arm / "input" / name).read_bytes()), expected)

    def test_parameterized_judge_preserves_rubric_and_selection(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "quality"
            judge.prepare(source=judge.SOURCE, out=out, label="test_label")
            old = json.loads((judge.OUT / "request.json").read_text())
            new = json.loads((out / "request.json").read_text())
            self.assertEqual(old, new)
            self.assertEqual(json.loads((out / "input.json").read_text())["script"], "test_label")
            self.assertFalse((out / "dispatch.json").exists())
            settings = json.loads((out / "settings.json").read_text())
            self.assertEqual(settings["source_sha256"], trial.api.digest(judge.SOURCE.read_bytes()))

    def test_repair_changes_only_two_code_fragments(self):
        original = (trial.NORMALIZED / "bundle.json").read_bytes()
        with tempfile.TemporaryDirectory() as td:
            repaired = Path(td) / "repaired"
            with patch.object(trial, "REPAIRED", repaired):
                trial.repair_two_runtime_errors()
                with self.assertRaises(FileExistsError):
                    trial.repair_two_runtime_errors()
            before = json.loads(original)["files"]
            after = json.loads((repaired / "bundle.json").read_text())["files"]
            changed = [(a, b) for a, b in zip(before, after) if a != b]
            self.assertEqual(len(before), len(after))
            self.assertEqual(len(changed), 1)
            self.assertEqual(changed[0][0]["path"], trial.api.PREFIX + "world.py")
            self.assertIn('state["pavel.comfort"] >= 2', changed[0][1]["content"])
            self.assertIn('if holder != "Nia":', changed[0][1]["content"])
        self.assertEqual(original, (trial.NORMALIZED / "bundle.json").read_bytes())

    def test_duplicate_judge_never_calls_api(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / "dispatch.json").write_text("{}")
            with patch.object(judge.api, "API") as client:
                with self.assertRaisesRegex(ValueError, "Already dispatched"):
                    judge.judge("unused", out=out)
                client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
