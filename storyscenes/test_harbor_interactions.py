"""Counterfactuals must change actual later possibilities, not just prose."""
from dataclasses import replace
import unittest

from storyscenes.harbor_story import Conditions, generate, registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import execute, replay


class HarborInteractionTests(unittest.TestCase):
    def config(self, **kw):
        return Conditions(purpose="shared_rope", display_ticks=5, last_launch=4, cautious=False, **kw)

    def test_same_initial_world_different_priority_changes_later_launch(self):
        early, early_spec, early_state, _ = generate(config=self.config(return_priority="promise"))
        late, late_spec, late_state, _ = generate(config=self.config(return_priority="display"))
        self.assertEqual(early["plot"]["outcome"], "shortened_display_and_sailing")
        self.assertEqual(late["plot"]["outcome"], "display_costs_sailing")
        self.assertEqual(early_state.get("parents", "boat").parent, "tub")
        self.assertEqual(late_state.get("parents", "boat").parent, "case")
        self.assertIn('"I promised to bring the rope back."', early["story"])
        self.assertNotIn("not my only promise", early["story"])
        self.assertNotIn("red sail", early["story"])
        for spec, state, row in ((early_spec, early_state, early), (late_spec, late_state, late)):
            self.assertEqual(replay(registry(), loads(registry(), dumps(spec)), row["path"]), state)
            self.assertEqual(state.get("parents", "rope").parent, "jetty")
            self.assertEqual(state.get("ownership", "rope").owner, "bo")
            self.assertEqual(state.get("loans", "rope_loan").status, "discharged")

    def test_borrowing_removes_weight_but_withholds_launch_resource(self):
        row, spec, state, _ = generate(config=self.config())
        eng, actions = registry(), {a.id: a for a in spec.actions}
        self.assertIsNone(execute(eng, spec, eng.initial(spec), actions["lift_case"]))
        borrowed = replay(eng, spec, row["path"][:row["path"].index("borrow_rope") + 1])
        self.assertIsNotNone(execute(eng, spec, borrowed, actions["lift_case"]))
        delivered = replay(eng, spec, row["path"][:row["path"].index("deliver_case") + 1])
        self.assertIsNone(execute(eng, spec, delivered, actions["open_tub"]))
        self.assertEqual(delivered.get("parents", "chart").parent, "rope")
        self.assertEqual(delivered.get("parents", "rope").parent, "display")

    def test_chart_must_be_hung_at_the_window_not_in_a_carried_coil(self):
        row, spec, _, _ = generate(config=self.config())
        eng = registry()
        before = replay(eng, spec, row["path"][:row["path"].index("hang_rope")])
        hang = next(a for a in spec.actions if a.id == "hang_chart")
        self.assertIsNone(execute(eng, spec, before, hang))

    def test_late_return_is_a_repaired_breach_not_a_kept_promise(self):
        row, spec, state, _ = generate(config=self.config(return_priority="display"))
        p = state.get("promises", "rope_return")
        self.assertEqual(p.status, "breached")
        self.assertEqual(p.repair_receipt, "return_rope:1")
        self.assertIsNone(p.performance_receipt)
        actions = {a.id: a for a in spec.actions}
        ready = replay(registry(), spec, row["path"][:row["path"].index("dry_dock")])
        self.assertIsNone(execute(registry(), spec, ready, actions["open_tub"]))

    def test_declining_preserves_both_ownership_and_launch_but_changes_display(self):
        row, spec, state, doc = generate(config=replace(self.config(), cautious=True))
        self.assertEqual(row["plot"]["outcome"], "flat_chart_and_sailing")
        self.assertIsNone(state.get("loans", "rope_loan"))
        self.assertIsNone(state.get("promises", "rope_return"))
        self.assertEqual(state.get("parents", "chart").parent, "display")
        self.assertNotIn("hang_chart", row["path"])
        self.assertEqual(state.get("parents", "boat").parent, "tub")
        offer = next(s for s in doc.statements if s.id == "offer")
        self.assertEqual(offer.question, "Who owned the rope Bo offered to lend?")
        self.assertNotIn("had to be returned", offer.answer)

    def test_short_display_can_finish_without_costing_the_launch(self):
        row, _, state, _ = generate(config=replace(self.config(), display_ticks=1))
        self.assertEqual(row["plot"]["outcome"], "both_plans")
        self.assertEqual(state.get("promises", "rope_return").status, "fulfilled")

    def test_shared_rope_has_grounded_qa_spans_and_varied_paths(self):
        paths = set()
        for duration in (1, 3, 5):
            for priority in ("promise", "display"):
                for direct in (False, True):
                    c = replace(self.config(), display_ticks=duration, return_priority=priority, direct_path=direct)
                    row, spec, state, doc = generate(config=c)
                    anchors = {e.id for e in state.events} | {f"initial/{f.id}" for f in spec.records["facts"]}
                    for s, span in zip(doc.statements, doc.spans()):
                        self.assertTrue(set(s.event_ids) <= anchors)
                        self.assertEqual(doc.story[span["start"]:span["end"]], s.text)
                    self.assertGreaterEqual(len(row["qa"]), 6)
                    paths.add(tuple(row["path"]))
        self.assertGreaterEqual(len(paths), 6)

    def test_clip_substitution_keeps_chart_hanging_without_replacing_launch_rope(self):
        row, spec, state, _ = generate(config=self.config(clip_available=True))
        self.assertEqual(row["plot"]["outcome"], "clip_preserves_both")
        self.assertEqual(state.get("parents", "chart").parent, "clip")
        self.assertEqual(state.get("parents", "clip").parent, "display")
        self.assertEqual(state.get("ownership", "clip").owner, "ari")
        before = replay(registry(), spec, row["path"][:row["path"].index("retrieve_rope")])
        actions = {a.id: a for a in spec.actions}
        self.assertIsNone(execute(registry(), spec, before, actions["open_tub"]))
        self.assertEqual(state.get("parents", "boat").parent, "tub")
        self.assertEqual(state.get("promises", "rope_return").status, "fulfilled")
        without, _, _, _ = generate(config=self.config())
        self.assertEqual(without["plot"]["outcome"], "shortened_display_and_sailing")

    def test_mounting_clip_must_precede_attaching_chart(self):
        row, spec, _, _ = generate(config=self.config(clip_available=True))
        prefix = row["path"][:row["path"].index("mount_clip")]
        before = replay(registry(), spec, prefix + ["unhang_chart"])
        attach = next(a for a in spec.actions if a.id == "clip_chart")
        self.assertIsNone(execute(registry(), spec, before, attach))

    def test_board_move_restores_hanging_time_lost_in_transit(self):
        c = self.config(jetty_board=True)
        row, spec, state, _ = generate(config=c)
        self.assertEqual(row["plot"]["outcome"], "display_moves_to_jetty")
        self.assertEqual(state.get("parents", "chart").parent, "board")
        self.assertIn("Bo held out both hands and accepted the rope.", row["story"])
        self.assertNotIn("Bo held out both hands and accepted it.", row["story"])
        times = {e.action.id: e.tick for e in state.events}
        hanging = times["unhang_chart"] - times["hang_chart"] + state.tick - times["board_chart"]
        self.assertGreaterEqual(hanging, c.display_ticks)
        self.assertEqual(state.get("promises", "rope_return").status, "fulfilled")
        records = dict(spec.records)
        records["containers"] = tuple(replace(b, open=False) if b.id == "board" else b for b in records["containers"])
        closed = replace(spec, records=records)
        before = replay(registry(), closed, row["path"][:row["path"].index("board_chart")])
        attach = next(a for a in closed.actions if a.id == "board_chart")
        self.assertIsNone(execute(registry(), closed, before, attach))

    def test_alternate_water_releases_deadline_not_the_loan(self):
        c = self.config(return_priority="display", flexible_sailing=True)
        row, spec, state, _ = generate(config=c)
        self.assertEqual(row["plot"]["outcome"], "released_deadline_and_basin")
        released = replay(registry(), spec, row["path"][:row["path"].index("release_deadline") + 1])
        self.assertEqual(released.get("promises", "rope_return").status, "released")
        self.assertEqual(released.get("loans", "rope_loan").status, "active")
        self.assertEqual(state.get("loans", "rope_loan").status, "discharged")
        self.assertEqual(state.get("parents", "boat").parent, "basin")
        self.assertFalse(state.get("containers", "tub").open)
        self.assertNotIn("assess_rope_promise", row["path"])
        without, _, _, _ = generate(config=replace(c, basin_available=False))
        self.assertEqual(without["plot"]["outcome"], "display_costs_sailing")
        self.assertEqual(without["plot"]["promise"], "breached")

    def test_deadline_release_cannot_retroactively_erase_lateness(self):
        row, spec, _, _ = generate(config=self.config(return_priority="display", flexible_sailing=True))
        prefix = row["path"][:row["path"].index("release_deadline")]
        late = replay(registry(), spec, prefix + ["time_5"])
        release = next(a for a in spec.actions if a.id == "release_deadline")
        self.assertIsNone(execute(registry(), spec, late, release))

    def test_alternatives_round_trip_and_keep_supported_reading(self):
        from itertools import product
        for clip, board, flexible, direct, priority in product((False, True), (False, True),
                                                              (False, True), (False, True), ("promise", "display")):
            c = self.config(clip_available=clip, jetty_board=board, flexible_sailing=flexible,
                            direct_path=direct, return_priority=priority)
            row, spec, state, doc = generate(config=c)
            self.assertEqual(replay(registry(), loads(registry(), dumps(spec)), row["path"]), state)
            self.assertGreaterEqual(len(row["qa"]), 6)
            anchors = {e.id for e in state.events} | {f"initial/{f.id}" for f in spec.records["facts"]}
            for statement, span in zip(doc.statements, doc.spans()):
                self.assertTrue(set(statement.event_ids) <= anchors)
                self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)


if __name__ == "__main__":
    unittest.main()
