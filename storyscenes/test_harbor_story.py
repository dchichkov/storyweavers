"""Story-level interventions, prose support and exact replay, not score assertions."""
from dataclasses import replace
import unittest

from storyscenes.harbor_story import Conditions, build, generate, simulate
from storyscenes.capabilities.api import registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import execute, fingerprint, replay
from storyscenes.capabilities.reading import Reader


class HarborStoryTests(unittest.TestCase):
    def test_ten_predeclared_seeds_replay_and_have_distinct_questions(self):
        outcomes, plots = set(), set()
        for seed in range(10):
            with self.subTest(seed=seed):
                row, spec, state, doc = generate(seed)
                self.assertEqual(replay(registry(), spec, row["path"]), state)
                self.assertGreater(len(row["qa"]), 5)
                self.assertEqual(len(row["qa"]), len({q["question"] for q in row["qa"]}))
                events = {e.id for e in state.events}
                facts = {f"initial/{f.id}" for f in spec.records["facts"]}
                for statement, span in zip(doc.statements, doc.spans()):
                    self.assertTrue(set(statement.event_ids) <= events | facts)
                    self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
                outcomes.add(row["plot"]["outcome"])
                plots.add(fingerprint(row["plot"]))
        self.assertGreaterEqual(len(outcomes), 2)
        self.assertGreaterEqual(len(plots), 5)

    def test_early_message_enables_real_request_and_handoff(self):
        c = Conditions(message_delay=0, moved=True, case_shut=True)
        row, spec, state, _ = generate(config=c)
        self.assertIn("give_stick", row["path"])
        self.assertNotIn("bo_deposit", row["path"])
        self.assertEqual(state.get("requests", "stick").completion_receipt, "give_stick:1")
        self.assertEqual(state.get("parents", "case").parent, "bo")
        self.assertEqual(state.get("parents", "gauge").parent, "cy")
        self.assertEqual(state.get("ownership", "gauge").owner, "cy")

    def test_initial_timing_changes_physical_outcome_not_just_words(self):
        c = Conditions(message_delay=0, last_launch=4, basin_available=True)
        early, _, _, _ = generate(config=c)
        late, _, _, _ = generate(config=replace(c, message_delay=4))
        self.assertEqual(early["plot"]["outcome"], "pool")
        self.assertEqual(late["plot"]["outcome"], "basin")
        self.assertNotEqual(early["path"], late["path"])

    def test_waiting_for_correction_avoids_the_wrong_place(self):
        c = Conditions(message_delay=2, moved=True, correction=True, cautious=True)
        careful, _, _, _ = generate(config=c)
        hasty, _, _, _ = generate(config=replace(c, cautious=False))
        self.assertFalse(careful["plot"]["wrong_place"])
        self.assertTrue(hasty["plot"]["wrong_place"])
        self.assertIn("fresh_receive", careful["path"])
        self.assertIn("fresh_receive", hasty["path"])

    def test_no_correction_is_an_enacted_search_not_a_fabricated_report(self):
        c = Conditions(message_delay=2, moved=True, correction=False, cautious=True)
        row, _, state, _ = generate(config=c)
        self.assertNotIn("fresh_send", row["path"])
        self.assertIsNone(state.get("claims", "fresh"))
        self.assertEqual(state.get("evidence", "search").outcome, "inaccessible")
        self.assertEqual(state.get("evidence", "find").outcome, "exact")
        self.assertIn("There was one other place", row["story"])

    def test_closed_path_requires_real_detour_and_can_cost_launch_window(self):
        c = Conditions(message_delay=2, moved=False, cautious=False, last_launch=4)
        direct, _, _, _ = generate(config=c)
        detour, _, _, _ = generate(config=replace(c, direct_path=False))
        self.assertEqual(direct["plot"]["outcome"], "pool")
        self.assertNotEqual(detour["plot"]["outcome"], "pool")
        self.assertIn("cy_workshop_quay", detour["path"])
        self.assertNotIn("cy_workshop_jetty", detour["path"])

    def test_unavailable_basin_produces_real_postponement(self):
        c = Conditions(message_delay=4, last_launch=4, basin_available=False)
        row, _, state, _ = generate(config=c)
        self.assertEqual(row["plot"]["outcome"], "rack")
        self.assertEqual(state.get("parents", "boat").parent, "rack")
        self.assertNotIn("launch", row["path"])
        self.assertIn("dry shelf", row["story"])

    def test_another_characters_detour_is_not_attributed_to_cy(self):
        c = Conditions(cautious=True, direct_path=False, last_launch=8)
        row, _, _, _ = generate(config=c)
        self.assertFalse(row["plot"]["detour"])
        self.assertNotIn("cy_workshop_quay", row["path"])
        self.assertNotIn("long way", row["story"])

    def test_launch_needs_the_instrument_backed_measurement(self):
        c = Conditions(message_delay=0)
        spec, state = simulate(c)
        path = [e.action.id for e in state.events]
        before = replay(registry(), spec, path[:path.index("measure")])
        launch = next(a for a in spec.actions if a.id == "launch")
        self.assertIsNone(execute(registry(), spec, before, launch))

    def test_prose_seed_does_not_change_the_events(self):
        a, _, _, _ = generate(2, prose_seed=1, config=Conditions())
        b, _, _, _ = generate(2, prose_seed=2, config=Conditions())
        self.assertEqual(a["trace_sha256"], b["trace_sha256"])
        self.assertEqual(a["plot"], b["plot"])
        self.assertNotEqual(a["story"], b["story"])

    def test_hiding_the_report_removes_dependent_reading_answers(self):
        _, _, _, doc = generate(config=Conditions(cautious=True))
        hidden = doc.mask(["new_message"])
        self.assertTrue(Reader(doc).ask("where", "cy", event_id="find_look:1").supported)
        self.assertFalse(Reader(hidden).ask("where", "cy", event_id="find_look:1").supported)

    def test_world_round_trip_preserves_execution(self):
        spec, state = simulate(Conditions())
        restored = loads(registry(), dumps(spec))
        self.assertEqual(replay(registry(), restored, [e.action.id for e in state.events]), state)

    def test_shallow_measurement_blocks_launch_even_when_early(self):
        c = Conditions(message_delay=0, pool_deep=False, basin_available=True)
        row, spec, state, _ = generate(config=c)
        before = replay(registry(), spec, row["path"][:row["path"].index("measure") + 1])
        self.assertLessEqual(before.tick, c.last_launch)
        self.assertIsNone(execute(registry(), spec, before, next(a for a in spec.actions if a.id == "launch")))
        self.assertIn("basin_shallow", row["path"])
        self.assertIn("too shallow", " ".join(q["answer"] for q in row["qa"]))
        restored = loads(registry(), dumps(spec))
        self.assertEqual(replay(registry(), restored, row["path"]), state)

    def test_shallow_water_without_basin_preserves_boat(self):
        row, _, _, _ = generate(config=Conditions(message_delay=0, pool_deep=False, basin_available=False))
        self.assertIn("postpone_shallow", row["path"])
        self.assertNotIn("time on the harbor timetable had passed", row["story"])

    def test_capacity_and_helper_change_delivery_plan(self):
        c = Conditions(purpose="carry", correction=True, direct_path=False, last_launch=4)
        helped, _, state, _ = generate(config=c)
        self.assertEqual(helped["plot"]["outcome"], "helped_delivery")
        self.assertEqual(state.get("parents", "rope").parent, "jetty")
        alone, spec, state, _ = generate(config=replace(c, correction=False))
        self.assertEqual(alone["plot"]["outcome"], "partial_delivery")
        self.assertEqual(state.get("parents", "rope").parent, "workshop")
        engine = registry()
        self.assertIsNone(execute(engine, spec, engine.initial(spec), next(a for a in spec.actions if a.id == "try_full_case")))
        enough, _, _, _ = generate(config=replace(c, correction=False, last_launch=8))
        self.assertEqual(enough["plot"]["outcome"], "two_trips")

    def test_lending_returns_custody_but_does_not_transfer_ownership(self):
        c = Conditions(purpose="lend", message_delay=4, moved=True, direct_path=False, last_launch=4)
        row, _, state, _ = generate(config=c)
        self.assertEqual(row["plot"]["outcome"], "late_return")
        self.assertEqual(state.get("loans", "boat_loan").status, "discharged")
        self.assertEqual(state.get("parents", "boat").parent, "cy")
        self.assertEqual(state.get("ownership", "boat").owner, "cy")
        declined, _, state, _ = generate(config=replace(c, cautious=True))
        self.assertEqual(declined["plot"]["outcome"], "declined")
        self.assertIsNone(state.get("loans", "boat_loan"))
        self.assertNotIn("exhibit", declined["path"])
        self.assertEqual(state.get("parents", "chart").parent, "display")
        self.assertIn("display_chart", declined["path"])

    def test_all_purposes_saved_world_replay(self):
        for purpose in ("trial", "carry", "lend", "parcel"):
            row, spec, state, _ = generate(config=Conditions(purpose=purpose))
            restored = loads(registry(), dumps(spec))
            self.assertEqual(replay(registry(), restored, row["path"]), state)

    def test_parcel_inspection_and_correction_follow_contents(self):
        c = Conditions(purpose="parcel", moved=True, cautious=False)
        late, _, state, _ = generate(config=c)
        self.assertTrue(late["plot"]["wrong_trip"])
        self.assertEqual(state.get("parents", "red_box").parent, "bo")
        self.assertEqual(state.get("parents", "lamp_tag").parent, "red_box")
        self.assertEqual(state.get("parents", "cloth").parent, "blue_box")
        self.assertEqual(state.get("parents", "blue_box").parent, "workshop")
        early, _, _, _ = generate(config=replace(c, cautious=True))
        self.assertFalse(early["plot"]["wrong_trip"])
        self.assertIn("inspect_blue", early["path"])
        correct, _, _, _ = generate(config=replace(c, moved=False))
        self.assertEqual(correct["plot"]["outcome"], "correct_delivery")
        self.assertNotIn("fix_lamp_tag", correct["path"])

    def test_delivery_resources_are_required_for_the_final_launch(self):
        row, spec, state, _ = generate(config=Conditions(purpose="carry", correction=True))
        engine = registry()
        opening = next(a for a in spec.actions if a.id == "open_tub")
        self.assertIsNone(execute(engine, spec, engine.initial(spec), opening))
        before = replay(engine, spec, row["path"][:row["path"].index("open_tub")])
        self.assertFalse(before.get("containers", "tub").open)
        self.assertIsNone(execute(engine, spec, before, next(a for a in spec.actions if a.id == "sail_tub")))
        self.assertEqual(state.get("parents", "boat").parent, "tub")
        self.assertTrue(state.get("containers", "tub").open)

    def test_shutter_must_open_before_light_can_be_observed(self):
        row, spec, state, _ = generate(config=Conditions(purpose="parcel", moved=False))
        engine = registry()
        before = replay(engine, spec, row["path"][:row["path"].index("open_shutter")])
        see = next(a for a in spec.actions if a.id == "see_light")
        self.assertIsNone(execute(engine, spec, before, see))
        self.assertEqual(state.get("evidence", "light").outcome, "exact")
        self.assertEqual(state.get("propositions", "light:proposition").result.value, True)

    def test_carry_qa_does_not_leak_an_unmentioned_starting_place(self):
        row, _, _, doc = generate(3001)
        self.assertNotIn("workshop", row["story"])
        answers = {s.id: s.answer for s in doc.statements}
        self.assertNotIn("workshop", answers["purpose"])
        self.assertEqual(answers["journey"], "Cy took the short path to the jetty.")

    def test_retrieval_answer_does_not_skip_the_search_and_handover(self):
        row, spec, _, doc = generate(config=Conditions(purpose="lend", moved=True))
        before_return = replay(registry(), spec, row["path"][:row["path"].index("offer_back")])
        self.assertEqual(before_return.get("loans", "boat_loan").status, "active")
        retrieval = next(s for s in doc.statements if s.id == "retrieval")
        self.assertIn("It still had to reach Cy's hands.", retrieval.answer)
        self.assertNotIn("return", retrieval.needs)


if __name__ == "__main__":
    unittest.main()
