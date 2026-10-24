"""Story purposes must change executable behavior, not only the wording."""
from dataclasses import replace
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import execute, fingerprint, replay
from storyscenes.capabilities.examples import action
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render_story
from storyscenes.capabilities import story_examples


class StoryPlotTests(unittest.TestCase):
    def setUp(self):
        self.engine = registry()

    def before(self, scenario, action_id):
        return replay(self.engine, scenario.spec, scenario.path[:scenario.path.index(action_id)])

    def try_action(self, scenario, state, action_id):
        before = fingerprint(state)
        result = execute(self.engine, scenario.spec, state, next(a for a in scenario.spec.actions if a.id == action_id))
        self.assertEqual(before, fingerprint(state))
        return result

    def test_library_trip_performs_the_requested_inspection_and_informs_owner(self):
        x = story_examples.loan_story()
        state = replay(self.engine, x.spec, x.path)
        self.assertEqual(state.get("requests", "R").completion_table, "evidence")
        self.assertEqual(state.get("requests", "R").completion_receipt, "marker_reading")
        self.assertEqual(state.get("belief_heads", "garden_name").belief, "learn_marker:belief")
        evidence = state.get("evidence", "marker_reading")
        self.assertIn("item", evidence.instrument_path)
        self.assertEqual(evidence.actor_path[-1], "yard")
        self.assertEqual(state.get("loans", "L").status, "discharged")
        doc = render_story(x.spec, state)
        self.assertIn("Using the atlas", doc.story)
        self.assertIn("walled garden", Reader(doc).ask("belief", "garden_name").answer)

    def test_inaccessible_atlas_prevents_inspection_without_partial_evidence(self):
        x = story_examples.loan_story()
        close = action("close_bag", "set_container", "borrower", container="bag", open=False)
        spec = replace(x.spec, actions=x.spec.actions + (close,))
        prefix = x.path[:x.path.index("read_marker")] + (close.id,)
        state = replay(self.engine, spec, prefix)
        result = execute(self.engine, spec, state, next(a for a in spec.actions if a.id == "read_marker"))
        self.assertIsNone(result)
        self.assertIsNone(state.get("evidence", "marker_reading"))

    def test_unreadable_marker_cannot_be_treated_as_a_completed_task(self):
        x = story_examples.loan_story(readable=False)
        state = self.try_action(x, self.before(x, "read_marker"), "read_marker")
        self.assertEqual(state.get("evidence", "marker_reading").outcome, "unknown")
        self.assertIsNone(self.try_action(x, state, "complete"))
        self.assertIsNone(self.try_action(x, state, "relift"))

    def test_calibration_availability_changes_actual_promise_outcome(self):
        for reading_at, expected in ((6, "fulfilled"), (8, "breached"), (10, "breached")):
            with self.subTest(reading_at=reading_at):
                x = story_examples.promise_story(reading_at=reading_at)
                state = replay(self.engine, x.spec, x.path)
                self.assertEqual(state.get("evidence", "calibration_reading").acquired_at, reading_at)
                self.assertEqual(state.get("receipts", "handoff:1").tick, reading_at)
                self.assertEqual(state.get("promises", "P").status, expected)
                self.assertEqual(state.get("parents", "chart").parent, "vale")

    def test_future_reading_is_rejected_even_without_story_clock_guard(self):
        x = story_examples.promise_story()
        state = self.before(x, "boundary")
        check = replace(next(a for a in x.spec.actions if a.id == "check_card"), requires=())
        spec = replace(x.spec, actions=tuple(check if a.id == check.id else a for a in x.spec.actions))
        self.assertIsNone(execute(self.engine, spec, state, check))
        self.assertIsNone(self.try_action(x, state, "handoff"))

    def test_corrected_report_changes_cys_action_and_final_custody(self):
        x = story_examples.delayed_report_story()
        state = replay(self.engine, x.spec, x.path)
        self.assertEqual(state.get("parents", "cy").parent, "jetty")
        self.assertEqual(state.get("parents", "gauge").parent, "cy")
        self.assertEqual(state.get("propositions", "old:proposition").result.value, "workshop")
        self.assertEqual(state.get("propositions", "fresh:proposition").result.value, "jetty")
        before = self.before(x, "adopt_correction")
        self.assertIsNone(self.try_action(x, before, "fetch_gauge"))

    def test_blocked_correction_does_not_give_cy_hidden_location_knowledge(self):
        x = story_examples.delayed_report_story(correction_enabled=False)
        state = self.before(x, "send_correction")
        self.assertIsNone(self.try_action(x, state, "send_correction"))
        self.assertIsNone(self.try_action(x, state, "fetch_gauge"))
        self.assertIsNone(self.try_action(x, state, "take_gauge"))
        self.assertIsNone(state.get("belief_heads", "cy_latest"))

    def test_later_inspection_cannot_be_consumed_during_the_original_visit(self):
        x = story_examples.delayed_report_story()
        state = self.engine.initial(x.spec)
        self.assertIsNone(self.try_action(x, state, "look_new"))
        closed = self.before(x, "lift")
        self.assertIsNone(self.try_action(x, closed, "open"))
        ready = self.before(x, "look_new")
        inspected = self.try_action(x, ready, "look_new")
        self.assertEqual(inspected.get("propositions", "fresh:proposition").reference_start, 2)
        self.assertEqual(inspected.get("propositions", "fresh:proposition").result.value, "jetty")

    def test_causal_qa_loses_report_support_when_masked(self):
        x = story_examples.delayed_report_story()
        state = replay(self.engine, x.spec, x.path)
        doc = render_story(x.spec, state)
        reader = Reader(doc)
        self.assertTrue(reader.ask("location", "cy", event_id="fetch_gauge:1").supported)
        answer = reader.follow_up("why")
        self.assertTrue(answer.supported)
        self.assertIn("send_correction:1/claim/correction", answer.statement_ids)
        for sid in ("send_correction:1/claim/correction", "receive_correction:1/receipt/correction",
                    "adopt_correction:1/belief/cy_latest"):
            self.assertFalse(Reader(doc.mask([sid])).ask("why", "cy", event_id="fetch_gauge:1").supported)
        hidden = render_story(x.spec, state, visible={e.id for e in state.events} - {"adopt_correction:1"})
        self.assertFalse(Reader(hidden).ask("why", "cy", event_id="fetch_gauge:1").supported)

    def test_profiles_roundtrip_and_visible_qa_remains_distinct(self):
        for build in (story_examples.loan_story, story_examples.promise_story, story_examples.delayed_report_story):
            x = build()
            restored = loads(self.engine, dumps(x.spec))
            self.assertEqual(dumps(restored), dumps(x.spec))
            state = replay(self.engine, x.spec, x.path)
            self.assertEqual(replay(self.engine, restored, x.path), state)
            doc = render_story(x.spec, state)
            questions = Reader(doc).questions()
            self.assertEqual(len({q.question for q in questions}), len(questions))
            for span, statement in zip(doc.spans(), doc.statements):
                self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)


if __name__ == "__main__":
    unittest.main()
