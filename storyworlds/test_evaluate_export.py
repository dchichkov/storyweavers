"""Training-set sampling must not mistake packed answers for extra stories."""

import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.storyworld_chat.evaluate_export import collect, compare_retained, prepare, story_record


def row(world, story, task="multiturn", packed=None):
    return dict(metadata=dict(world=world, task=task,
                              packed_tasks=packed if packed is not None else ["story", "world_qa"]),
                messages=[dict(role="user", content="Task: write_story"),
                          dict(role="assistant", content=story),
                          dict(role="user", content="Why?"),
                          dict(role="assistant", content="Not another story.")])


def stream(rows):
    return io.BytesIO(b"".join((json.dumps(r) + "\n").encode() for r in rows))


class ExportEvaluationTests(unittest.TestCase):
    def test_packing_repetition_is_not_diversity(self):
        rows = [row("a", "First."), row("a", "First."), row("a", "Second.")]
        groups, summary = collect(stream(rows), 100, 7)
        self.assertEqual([r["story"] for r in groups["a"]], ["First.", "Second."])
        self.assertEqual(summary["story_rows"], 3)
        self.assertEqual(summary["unique_story_world_pairs"], 2)
        self.assertEqual(summary["source_sha256"], hashlib.sha256(stream(rows).getvalue()).hexdigest())

    def test_qa_only_is_not_a_story(self):
        self.assertIsNone(story_record(row("a", "Answer.", task="world_qa"), 1))
        self.assertIsNone(story_record(row("a", "Answer.", packed=["world_qa"]), 1))
        self.assertEqual(story_record(row("a", "  Story.\n", task="story"), 2)["story"], "  Story.\n")

    def test_world_selection_is_order_and_packing_invariant(self):
        rows = [row(str(i), f"Story {i}.") for i in range(50)]
        groups, summary = collect(stream(rows), 7, 123)
        reordered, _ = collect(stream(list(reversed(rows)) + [rows[0]] * 30), 7, 123)
        self.assertEqual(list(groups), list(reordered))
        self.assertEqual(summary["worlds"], 50)
        self.assertEqual(summary["selected_worlds"], 7)
        for world in groups:
            self.assertEqual([r["story"] for r in groups[world]], [r["story"] for r in reordered[world]])

    def test_selected_world_keeps_all_interleaved_stories(self):
        rows = [row(str(i), f"First {i}.") for i in range(50)]
        rows += [row(str(i), f"Second {i}.") for i in reversed(range(50))]
        groups, _ = collect(stream(rows), 7, 42)
        self.assertTrue(all(len(values) == 2 for values in groups.values()))

    def test_invalid_story_fails_closed(self):
        with self.assertRaises(ValueError):
            collect(stream([row("a", "")]), 1, 7)
        with self.assertRaises(ValueError):
            collect(stream([]), 0, 7)

    def test_comparison_checks_capacity_before_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "catalog.json").write_text(json.dumps([
                dict(world="a", pool="pools/000.jsonl", stories=2)]))
            with self.assertRaises(ValueError):
                compare_retained(out, [], count=1, samples=100)
            self.assertFalse((out / "retained_comparison").exists())

    def test_bad_archive_checksum_does_not_prepare_paid_input(self):
        import tarfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = stream([row("a", "First."), row("a", "Second.")]).getvalue()
            archive = root / "data.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                info = tarfile.TarInfo("train.jsonl")
                info.size = len(data)
                bundle.addfile(info, io.BytesIO(data))
            with patch("training.storyworld_chat.evaluate_export.compression") as compress:
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    prepare(archive, "train.jsonl", root / "out", count=1, seed=7,
                            expected_sha256="incorrect")
                compress.assert_not_called()
            self.assertFalse((root / "out" / "judge_inputs.json").exists())


if __name__ == "__main__":
    unittest.main()
