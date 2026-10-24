"""Test that theatrical resolutions are executable, not just narrated."""
from dataclasses import replace
import unittest

from storyscenes.theater_story import Conditions, generate, registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import execute, replay
from storyscenes.capabilities.reading import Reader


class TheaterStoryTests(unittest.TestCase):
    def world(self, config):
        row, spec, state, doc = generate(config=config)
        return row, spec, state, doc, registry(), {a.id: a for a in spec.actions}

    def test_ten_positions_replay_and_have_real_support(self):
        for seed in range(10):
            row, spec, state, doc = generate(seed)
            self.assertEqual(replay(registry(), loads(registry(), dumps(spec)), row["path"]), state)
            anchors = {e.id for e in state.events} | {f"initial/{t}/{r.id}" for t, rs in spec.records.items() for r in rs}
            for statement, span in zip(doc.statements, doc.spans()):
                self.assertTrue(set(statement.event_ids) <= anchors)
                self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
            self.assertGreaterEqual(len(row["qa"]), 6)
            self.assertEqual(len(row["qa"]), len({q["question"] for q in row["qa"]}))

    def test_projection_size_changes_from_actual_manipulation(self):
        row, spec, state, _, eng, actions = self.world(Conditions())
        start = eng.initial(spec)
        self.assertIsNone(execute(eng, spec, start, actions["see_large"]))
        first = replay(eng, spec, ["large_shadow", "see_large"])
        self.assertEqual(first.get("theater_notices", "first_shadow").value, "3")
        second = replay(eng, spec, row["path"][:4])
        self.assertEqual(second.get("theater_notices", "second_shadow").value, "1")
        self.assertEqual(state.get("theater_props", "lamp").units, 1)
        giant, _, giant_state, _, _, _ = self.world(Conditions(giant_ending=True))
        self.assertIn("restore_large", giant["path"])
        self.assertEqual(giant_state.get("theater_props", "lamp").units, 0)

    def test_shadow_source_cannot_be_seen_from_stage_or_assumed_at_end(self):
        _, spec, _, _, eng, actions = self.world(Conditions())
        self.assertIsNone(execute(eng, spec, eng.initial(spec), actions["inspect_source"]))
        before = replay(eng, spec, ["large_shadow", "small_shadow"])
        self.assertIsNone(execute(eng, spec, before, actions["perform"]))

    def test_source_answer_does_not_reuse_the_earlier_shadow_distance(self):
        for giant in (False, True):
            row, spec, _, doc, eng, _ = self.world(Conditions(giant_ending=giant))
            path = row["path"][:row["path"].index("inspect_source") + 1]
            seen = replay(eng, spec, path)
            self.assertEqual(seen.get("theater_projections", "screen").distance, 3)
            answer = next(s.answer for s in doc.statements if s.id == "source")
            self.assertIn("lit by the lamp", answer)
            self.assertNotIn("near the lamp", answer)

    def test_noise_changes_recovery_channel(self):
        for noisy in (False, True):
            row, spec, state, _, eng, _ = self.world(Conditions(purpose="cue", noisy=noisy))
            heard = replay(eng, spec, ["read_jo", "cue"])
            self.assertEqual(heard.get("theater_players", "mina").line is None, noisy)
            self.assertEqual("read_mina" in row["path"], noisy)
            self.assertEqual(state.get("theater_players", "mina").line, "The door is open. Come in.")
            self.assertEqual(state.get("parents", "jo").parent, "stage")

    def test_blank_page_requires_inspection_then_wordless_action(self):
        row, spec, state, _, eng, actions = self.world(Conditions(purpose="cue", written_line=False))
        self.assertIsNone(execute(eng, spec, eng.initial(spec), actions["mime"]))
        self.assertIsNone(execute(eng, spec, eng.initial(spec), actions["enter"]))
        self.assertLess(row["path"].index("read_mina"), row["path"].index("mime"))
        self.assertEqual(state.get("theater_notices", "read_mina").value, "blank page")
        self.assertIsNone(state.get("theater_players", "mina").line)
        self.assertEqual(state.get("performances", "stage").ending, "wordless_welcome")
        self.assertTrue(state.get("containers", "door").open)

    def test_costume_fitting_failure_has_a_physical_result(self):
        row, spec, state, _, eng, _ = self.world(Conditions(purpose="crown", large_crown=True))
        tried = replay(eng, spec, ["try_crown"])
        self.assertEqual(tried.get("parents", "crown").parent, "tray")
        self.assertIsNone(tried.get("theater_players", "mina").wearing)
        self.assertEqual(state.get("theater_props", "clip").units, 0)
        self.assertEqual(state.get("theater_props", "crown").size, 1)
        self.assertEqual(state.get("parents", "crown").parent, "mina")
        self.assertIn("retry_crown", row["path"])

    def test_no_clip_means_display_not_imaginary_fitting(self):
        row, spec, state, _, eng, actions = self.world(Conditions(purpose="crown", clip=False))
        before = replay(eng, spec, ["try_crown"])
        self.assertIsNone(execute(eng, spec, before, actions["resize"]))
        self.assertEqual(state.get("parents", "crown").parent, "chair")
        self.assertEqual(state.get("theater_props", "crown").size, 2)
        self.assertIsNone(state.get("theater_players", "mina").wearing)
        self.assertEqual(state.get("ownership", "crown").owner, "jo")

    def test_masking_source_removes_dependent_qa(self):
        _, _, _, doc, _, _ = self.world(Conditions())
        self.assertLess(len(Reader(doc.mask(["source"])).questions()), len(Reader(doc).questions()))

    def test_prose_seed_does_not_change_trace(self):
        first, _, _, _ = generate(0, prose_seed=1)
        second, _, _, _ = generate(0, prose_seed=4)
        self.assertEqual(first["trace_sha256"], second["trace_sha256"])
        self.assertEqual(first["plot"], second["plot"])


if __name__ == "__main__":
    unittest.main()
