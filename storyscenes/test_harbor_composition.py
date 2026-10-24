from dataclasses import replace
from itertools import product
import unittest

from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import execute, matches, replay
from storyscenes.capabilities.reading import Reader
from storyscenes.harbor_composition_story import Conditions, generate, registry


class ComposedHarborTests(unittest.TestCase):
    def test_chart_can_be_dismantled_and_restored_after_launch(self):
        row, spec, state, _ = generate(config=Conditions())
        path = row["path"]
        self.assertEqual(path.count("hang_chart"), 2)
        self.assertLess(path.index("take_chart_rope"), path.index("launch"))
        self.assertLess(path.index("launch"), len(path) - 1 - path[::-1].index("hang_chart"))
        self.assertEqual(state.get("parents", "chart").parent, "rope")
        self.assertEqual(state.get("parents", "rope").parent, "display")

    def test_alternative_support_removes_dependency_not_just_wording(self):
        c = Conditions(clip=True, supports=("clip", "rope", "board"))
        clipped, _, state, _ = generate(config=c)
        without, _, _, _ = generate(config=replace(c, clip=False))
        self.assertEqual(state.get("parents", "chart").parent, "clip")
        self.assertNotIn("take_chart_rope", clipped["path"])
        self.assertIn("take_chart_rope", without["path"])
        self.assertNotIn("chart down", clipped["story"])

    def test_light_condition_changes_launch_prerequisites(self):
        row, spec, _, _ = generate(config=Conditions())
        before = replay(registry(), spec, row["path"][:row["path"].index("lamp_jetty")])
        launch = next(a for a in spec.actions if a.id == "launch")
        self.assertIsNone(execute(registry(), spec, before, launch))
        daylight, _, _, _ = generate(config=Conditions(dark_launch=False))
        self.assertNotIn("lamp_jetty", daylight["path"])
        self.assertIn("take_lantern_display", row["path"])
        self.assertNotIn("move_light", [s["statement_ids"][-1] for s in daylight["qa"]])

    def test_board_cannot_replace_a_requested_lit_window_display(self):
        c = Conditions(board=True, supports=("board", "rope", "clip"))
        window, _, state, _ = generate(config=c)
        jetty, _, elsewhere, _ = generate(config=replace(c, light_window=False))
        self.assertNotIn("board_chart", window["path"])
        self.assertEqual(state.get("parents", "chart").parent, "rope")
        self.assertEqual(elsewhere.get("parents", "chart").parent, "board")
        self.assertNotEqual(window["story"], jetty["story"])

    def test_rope_cannot_leave_window_with_chart_still_hanging(self):
        row, spec, _, _ = generate(config=Conditions())
        before = replay(registry(), spec, row["path"][:row["path"].index("take_chart_rope")])
        take = next(a for a in spec.actions if a.id == "take_rope_display")
        self.assertIsNone(execute(registry(), spec, before, take))

    def test_late_lighting_does_not_narrate_a_future_launch(self):
        c = Conditions(priorities=("boat", "chart", "lamp"), dark_launch=False, light_window=False)
        row, _, _, _ = generate(config=c)
        self.assertLess(row["path"].index("launch"), row["path"].index("lamp_jetty"))
        self.assertIn("already floating on the water", row["story"])
        self.assertNotIn("would lower the boat", row["story"])

    def test_small_matrix_replays_and_retains_readable_qa(self):
        for clip, board, dark, window in product((False, True), repeat=4):
            row, spec, state, doc = generate(config=Conditions(clip=clip, board=board,
                dark_launch=dark, light_window=window, supports=("board", "clip", "rope")))
            self.assertEqual(replay(registry(), loads(registry(), dumps(spec)), row["path"]), state)
            self.assertTrue(all(matches(state, q) for q in spec.goal))
            anchors = {e.id for e in state.events} | {f"initial/{f.id}" for f in spec.records["facts"]}
            for statement, span in zip(doc.statements, doc.spans()):
                self.assertTrue(set(statement.event_ids) <= anchors)
                self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
            self.assertGreaterEqual(len(row["qa"]), 6)
            self.assertFalse(Reader(doc.mask(("opening",))).questions())

    def test_answers_do_not_expose_hidden_lamp_or_load_details(self):
        for config in (Conditions(), Conditions(light_window=False, dark_launch=False)):
            _, _, _, doc = generate(config=config)
            delivery = next(s for s in doc.statements if s.id == "delivery")
            self.assertNotIn("too heavy", delivery.answer)
            self.assertIn("rope", delivery.answer)
            self.assertIn("jetty", delivery.answer)
            for statement in doc.statements:
                self.assertNotIn("bulb", statement.answer)
                if statement.id.startswith("lamp_") and "shutter" not in statement.text:
                    self.assertNotIn("shutter", statement.answer)

    def test_first_window_visit_is_not_described_as_a_return(self):
        row, _, _, _ = generate(config=Conditions(priorities=("boat", "lamp", "chart")))
        self.assertEqual(row["path"].count("lamp_quay"), 1)
        self.assertIn("carried the lantern to the window", row["story"])
        self.assertNotIn("lantern back to the window", row["story"])
        self.assertNotIn("chart to return", row["story"])
        self.assertFalse(any("back to the quay window" in q["answer"] for q in row["qa"]))
        returned, _, _, _ = generate(config=Conditions())
        self.assertGreater(returned["path"].count("lamp_quay"), 1)
        self.assertIn("lantern back to the window", returned["story"])


if __name__ == "__main__":
    unittest.main()
