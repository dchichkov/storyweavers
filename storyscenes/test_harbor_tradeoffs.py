from dataclasses import replace
from itertools import permutations, product
import unittest

from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import CapabilityError, execute, matches, replay
from storyscenes.capabilities.reading import Reader
from storyscenes.harbor_tradeoffs_story import Conditions, build, conflicts, generate, registry, select_goals


class HarborTradeoffTests(unittest.TestCase):
    def test_same_resources_different_priority_changes_actual_boat_and_chart(self):
        c = Conditions(clip=False, board=False, dark_launch=False, keep_launch_light=False,
                       priorities=("chart", "boat", "lamp"))
        first, _, first_state, _ = generate(config=c)
        second, _, second_state, _ = generate(config=replace(c, priorities=("boat", "chart", "lamp")))
        self.assertEqual(first_state.get("parents", "boat").parent, "dry_dock")
        self.assertEqual(first_state.get("parents", "chart").parent, "rope")
        self.assertEqual(second_state.get("parents", "boat").parent, "tub")
        self.assertEqual(second_state.get("parents", "chart").parent, "display")
        self.assertNotIn("would hang", second["story"])
        self.assertNotEqual(first["plot"]["outcome"], second["plot"]["outcome"])

    def test_clip_removes_rope_conflict_but_not_light_conflict(self):
        c = Conditions(clip=True, board=False, priorities=("boat", "chart", "lamp"))
        row, spec, state, _ = generate(config=c)
        self.assertEqual(state.get("parents", "chart").parent, "clip")
        self.assertEqual(row["plot"]["deferred"], ["lamp"])
        self.assertEqual(row["plot"]["blockers"], ["lantern"])
        self.assertIn("clip_chart", row["path"])
        restored, _, _, _ = generate(config=replace(c, priorities=("chart", "boat", "lamp")))
        self.assertIn("restore the display", " ".join(q["question"] for q in restored["qa"]))
        without, _, _, _ = generate(config=replace(c, clip=False))
        self.assertEqual(set(without["plot"]["deferred"]), {"chart", "lamp"})

    def test_open_cover_prevents_retrieving_the_secured_rope(self):
        c = Conditions(clip=True, priorities=("boat", "chart", "lamp"))
        row, spec, state, _ = generate(config=c)
        path = row["path"][:row["path"].index("open_tub") + 1]
        before = replay(registry(), spec, path)
        take = next(a for a in spec.actions if a.id == "take_rope_jetty")
        self.assertEqual(before.get("parents", "ari").parent, "jetty")
        self.assertIsNone(execute(registry(), spec, before, take))

    def test_board_restores_displaced_chart_without_reusing_secured_rope(self):
        c = Conditions(board=True, clip=False, light_window=False,
                       priorities=("chart", "boat", "lamp"))
        row, _, state, _ = generate(config=c)
        self.assertEqual(row["plot"]["deferred"], [])
        self.assertTrue(row["plot"]["chart_rehung"])
        self.assertEqual(state.get("parents", "chart").parent, "board")
        self.assertEqual(state.get("parents", "rope").parent, "jetty")
        self.assertIn("board", row["story"])
        without, _, dry_state, _ = generate(config=replace(c, board=False))
        self.assertEqual(without["plot"]["deferred"], ["boat"])
        self.assertEqual(dry_state.get("parents", "boat").parent, "dry_dock")

    def test_launch_light_cannot_be_removed_after_launch(self):
        c = Conditions(clip=True, priorities=("boat", "chart", "lamp"))
        row, spec, _, _ = generate(config=c)
        before = replay(registry(), spec, row["path"][:row["path"].index("launch") + 1])
        take = next(a for a in spec.actions if a.id == "take_lantern_jetty")
        self.assertIsNone(execute(registry(), spec, before, take))

    def test_no_resource_persistence_restores_all_goal_feasibility(self):
        c = Conditions(hold_cover=False, keep_launch_light=False)
        row, _, state, _ = generate(config=c)
        self.assertEqual(row["plot"]["deferred"], [])
        self.assertEqual(state.get("parents", "boat").parent, "tub")
        self.assertEqual(state.get("parents", "lantern").parent, "display")

    def test_decision_is_enacted_before_use_and_cannot_be_forged(self):
        c = Conditions()
        row, spec, state, _ = generate(config=c)
        self.assertEqual(row["path"][0], "choose_goals")
        choose = next(a for a in spec.actions if a.id == "choose_goals")
        fake = replace(choose, args=dict(kept=("boat",)))
        forged = replace(spec, actions=tuple(fake if a.id == choose.id else a for a in spec.actions))
        self.assertIsNone(execute(registry(), forged, registry().initial(forged), fake))
        records = dict(spec.records)
        records["harbor_choices"] = (state.get("harbor_choices", "evening"),)
        with self.assertRaisesRegex(CapabilityError, "enacted"):
            registry().initial(replace(spec, records=records))
        records = dict(spec.records)
        records["ownership"] = tuple(replace(r, owner="bo") if r.id == "rope" else r for r in records["ownership"])
        foreign = replace(spec, records=records)
        self.assertIsNone(execute(registry(), foreign, registry().initial(foreign), choose))

    def test_selection_is_lexicographic_and_not_goal_count(self):
        exclusions = (("rope", frozenset(("chart", "boat"))), ("light", frozenset(("lamp", "boat"))))
        self.assertEqual(select_goals(("boat", "chart", "lamp"), exclusions), ("boat",))
        self.assertEqual(select_goals(("chart", "boat", "lamp"), exclusions), ("chart", "lamp"))

    def test_choice_answers_join_goals_and_distinguish_plural_plans(self):
        _, _, _, doc = generate(config=Conditions(priorities=("boat", "chart", "lamp")))
        answer = next(s.answer for s in doc.statements if s.id == "choice")
        self.assertEqual(answer, "Ari chose to launch the boat. The plans to hang the chart and light the window were deferred.")
        _, _, _, doc = generate(config=Conditions(hold_cover=False, keep_launch_light=False))
        answer = next(s.answer for s in doc.statements if s.id == "choice")
        self.assertIn("hang the chart, light the window and launch the boat", answer)

    def test_returned_lamp_does_not_imply_a_never_hung_chart_is_returning(self):
        row, _, _, _ = generate(config=Conditions(priorities=("lamp", "boat", "chart"),
            hold_cover=True, keep_launch_light=False, clip=False, board=False))
        self.assertEqual(row["plot"]["deferred"], ["chart"])
        self.assertIn("take_lantern_display", row["path"])
        self.assertNotIn("hang_chart", row["path"])
        self.assertNotIn("chart to return", row["story"])
        self.assertIn("empty window shelf", row["story"])

    def test_matrix_serialized_replay_and_visible_qa(self):
        for priority, clip, persistent_light in product(permutations(("chart", "lamp", "boat")), (False, True), (False, True)):
            c = Conditions(priorities=priority, clip=clip, keep_launch_light=persistent_light)
            row, spec, state, doc = generate(config=c)
            self.assertEqual(replay(registry(), loads(registry(), dumps(spec)), row["path"]), state)
            self.assertTrue(all(matches(state, q) for q in spec.goal))
            self.assertGreaterEqual(len(row["qa"]), 6)
            if c.keep_launch_light and c.dark_launch:
                self.assertIn("initial/darkness", doc.statements[0].event_ids)
            anchors = {e.id for e in state.events} | {f"initial/{f.id}" for f in spec.records["facts"]}
            for statement, span in zip(doc.statements, doc.spans()):
                self.assertTrue(set(statement.event_ids) <= anchors)
                self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
            self.assertFalse(Reader(doc.mask(("opening",))).questions())


if __name__ == "__main__":
    unittest.main()
