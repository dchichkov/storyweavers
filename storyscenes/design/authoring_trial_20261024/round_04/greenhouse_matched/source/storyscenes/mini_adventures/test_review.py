from copy import deepcopy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import review


@dataclass(frozen=True, kw_only=True)
class Parameters:
    count: int = 7


def initial(params):
    return {"actor.turn": 0, "story.outcome": "", "story.ended": False}


def generate(seed=0, *, count=7, params=None):
    params = params or Parameters(count=count)
    state = initial(params)
    episodes = []
    for n in range(count):
        before = deepcopy(state)
        state["actor.turn"] += 1
        if n == count - 1:
            state.update({"story.outcome": "done", "story.ended": True})
        episodes.append({"id": f"s{n}", "before": before, "after": deepcopy(state),
                         "text": f'"Step {n}," said Ada.',
                         "events": [{"action": "step", "requires": {"actor.turn": n},
                                     "changes": {k: {"before": before[k], "after": v}
                                                 for k, v in state.items() if before[k] != v}}]})
    return {"seed": seed, "parameters": asdict(params), "scene_count": count,
            "path": [e["id"] for e in episodes], "episodes": episodes,
            "story": "\n\n".join(e["text"] for e in episodes), "final_state": state,
            "search_attempts": count}


def fixture():
    return SimpleNamespace(Parameters=Parameters, initial=initial,
                           SCENES=tuple(f"s{n}" for n in range(8)),
                           guard=lambda scene, state: scene == f"s{state['actor.turn']}",
                           validate=lambda state: None, generate=generate,
                           replay=lambda params, path: generate(count=len(path), params=params)["episodes"])


class ReviewTests(unittest.TestCase):
    def test_valid_trace_and_exact_replay(self):
        for count in (7, 8):
            row = generate(seed=13, count=count)
            self.assertEqual(review.verify_row(fixture(), row, 13, count), row)

    def test_false_precondition_is_not_hidden_by_valid_final_state(self):
        row = generate()
        row["episodes"][1]["events"][0]["requires"]["actor.turn"] = 44
        with self.assertRaisesRegex(ValueError, "False action precondition"):
            review.verify_row(fixture(), row, 0, 7)

    def test_unrecorded_effect_rejected(self):
        row = generate()
        row["episodes"][0]["after"]["story.outcome"] = "unearned"
        with self.assertRaisesRegex(ValueError, "Unrecorded scene effect"):
            review.verify_row(fixture(), row, 0, 7)

    def test_replay_prose_drift_rejected(self):
        module = fixture()
        module.replay = lambda params, path: []
        with self.assertRaisesRegex(ValueError, "Replay changed"):
            review.verify_row(module, generate(), 0, 7)

    def test_diagnostics_keep_duplicates(self):
        row = generate()
        stats = review.describe([row, row])
        self.assertEqual(stats["successful"], 2)
        self.assertEqual(stats["exact_texts"], 1)
        self.assertEqual(stats["outcomes"], {"done": 2})
        self.assertEqual(stats["lzma"]["raw_bytes"], len((row["story"] + "\n\n" + row["story"]).encode()))

    def test_nonfinite_values_rejected(self):
        with self.assertRaises(ValueError):
            review.json_native({"value": float("nan")})

    def test_malformed_story_payload_does_not_break_failure_report(self):
        self.assertEqual(review.saved_text({"row": [], "error": "bad shape"}), "bad shape")
        self.assertEqual(review.saved_text({"row": {"story": None}, "error": "bad text"}), "bad text")

    def test_snapshot_preserves_importable_layout_and_hashes(self):
        import hashlib
        with TemporaryDirectory() as directory:
            root = Path(directory) / "repo" / "storyscenes" / "mini_adventures"
            root.mkdir(parents=True)
            source = root / "inventory.py"
            source.write_text("VALUE = 42\n")
            out = Path(directory) / "snapshot"
            with patch.object(review, "ROOT", root), patch.object(review, "source_files", return_value=[source]):
                hashes = review.snapshot("fake", out)
            key = "storyscenes/mini_adventures/inventory.py"
            self.assertEqual(hashes, {key: hashlib.sha256(source.read_bytes()).hexdigest()})
            self.assertEqual((out / "source" / key).read_bytes(), source.read_bytes())

    def test_output_directory_is_never_overwritten(self):
        with TemporaryDirectory() as directory, patch.object(review, "load", return_value=fixture()):
            with self.assertRaises(FileExistsError):
                review.audit("fake", seeds=[0], out=directory)

    def test_failed_generation_is_preserved_without_resampling(self):
        module = fixture()
        module.generate = lambda *a, **kw: (_ for _ in ()).throw(ValueError("fixture failure"))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fake").mkdir()
            (root / "fake/reference_story.md").write_text("# Title\n\nOne short reference.\n")
            out = root / "audit"
            with patch.object(review, "ROOT", root), patch.object(review, "load", return_value=module), \
                    patch.object(review, "snapshot", return_value={}), \
                    patch.object(review, "source_files", return_value=[]), \
                    patch.object(review, "check_inventory", return_value={"scenes": []}):
                result = review.audit("fake", seeds=[0, 1], out=out)
            self.assertEqual(result["requested"], 4)
            self.assertEqual(result["failures"], 4)
            rows = [json.loads(line) for line in (out / "attempts.jsonl").read_text().splitlines()]
            self.assertEqual([(r["seed"], r["scene_count"]) for r in rows], [(0, 7), (1, 7), (0, 8), (1, 8)])
            self.assertTrue(all("fixture failure" in r["error"] for r in rows))
            self.assertEqual((out / "stories.jsonl").read_text(), "")


if __name__ == "__main__":
    unittest.main()
