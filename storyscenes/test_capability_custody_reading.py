"""Custody QA uses event-time visible paths, never a final-state lookup."""
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.core import replay, replay_selection
from storyscenes.capabilities.examples import delayed_report_story, loan_story
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render


class CapabilityCustodyReadingTests(unittest.TestCase):
    def test_bench_placement_separates_location_holder_owner_and_borrower(self):
        scenario = loan_story()
        state = replay(registry(), scenario.spec, scenario.path)
        doc = render(scenario.spec, state)
        reader = Reader(doc)
        expected = {"location": "inside the carrying bag at the courtyard",
                    "holder": "No one was physically holding the atlas",
                    "owner": "Inez still owned the atlas",
                    "borrower": "Nia remained responsible for returning the atlas"}
        for kind, text in expected.items():
            with self.subTest(kind=kind):
                answer = reader.ask(kind, "item", event_id="rest:1")
                self.assertTrue(answer.supported)
                self.assertIn(text, answer.answer)
                self.assertEqual(answer.reference_tick, 0)
                self.assertIn("pack:1", answer.event_ids)
                self.assertIn("rest:1", answer.event_ids)
        self.assertIn("outstanding", reader.ask("loan_status", "L", event_id="rest:1").answer)
        self.assertIn("settled", reader.ask("loan_status", "L", event_id="deposit:1").answer)
        self.assertFalse(reader.ask("holder", "item").supported)  # Several event times, no guessed latest.

    def test_masked_path_or_current_placement_suppresses_custody_followup(self):
        scenario = loan_story()
        state = replay(registry(), scenario.spec, scenario.path)
        doc = render(scenario.spec, state)
        for sid in ("pack:1/placement/item", "rest:1/placement/bag", "rest:1/holder/item"):
            with self.subTest(hidden=sid):
                reader = Reader(doc.mask([sid]))
                self.assertFalse(reader.ask("holder", "item", event_id="rest:1").supported)
        reader = Reader(doc)
        self.assertTrue(reader.ask("location", "item", event_id="rest:1").supported)
        self.assertIn("No one", reader.follow_up("holder").answer)
        self.assertIn("Nia", reader.follow_up("borrower").answer)

    def test_closed_container_movement_never_answers_contents_from_hidden_truth(self):
        scenario = delayed_report_story(open_after=False)
        state = replay(registry(), scenario.spec, scenario.path)
        reader = Reader(render(scenario.spec, state))
        for event_id in ("lift:1", "move:1", "put_down:1"):
            self.assertFalse(reader.ask("location", "gauge", event_id=event_id).supported)
            self.assertFalse(reader.ask("holder", "gauge", event_id=event_id).supported)
        answer = reader.ask("observation", "fresh").answer
        self.assertIn("tried to inspect", answer)
        self.assertIn("did not establish", answer)

    def test_selected_replay_preserves_custody_text_and_evidence(self):
        scenario = loan_story()
        engine = registry()
        state = replay(engine, scenario.spec, scenario.path)
        retained = replay_selection(engine, scenario.spec, state, ["rest:1"])
        selected = {event.id for event in retained.events}
        doc = render(scenario.spec, state, visible=selected)
        self.assertEqual(doc, render(scenario.spec, retained))
        self.assertTrue(Reader(doc).ask("holder", "item", event_id="rest:1").supported)

    def test_no_prior_variant_does_not_narrate_a_prediction(self):
        scenario = delayed_report_story(extrapolate=False)
        self.assertNotIn("expected", scenario.premise)
        state = replay(registry(), scenario.spec, scenario.path)
        doc = render(scenario.spec, state, premise=scenario.premise)
        self.assertNotIn("revised the earlier belief", doc.story)

    def test_late_receipt_and_belief_keep_historical_reference_time(self):
        scenario = delayed_report_story()
        state = replay(registry(), scenario.spec, scenario.path)
        doc = render(scenario.spec, state)
        for kind, focus in (("receipt", "report"), ("belief", "cy_old")):
            answer = Reader(doc).ask(kind, focus)
            self.assertTrue(answer.supported)
            self.assertEqual(answer.reference_tick, 0)
            statement = next(s for s in doc.statements if s.kind == kind and s.focus == focus)
            self.assertEqual(statement.acquired_tick, 2)
        self.assertIn("At time 2", Reader(doc).ask("receipt", "report").answer)
        self.assertIn("at time 0", Reader(doc).ask("belief", "cy_old").answer)


if __name__ == "__main__":
    unittest.main()
