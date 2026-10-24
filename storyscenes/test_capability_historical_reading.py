"""Non-vacuous report accuracy, reference-time and missing-view contrasts."""
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.core import replay, replay_selection
from storyscenes.capabilities.examples import delayed_report_story
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render


class HistoricalReadingTests(unittest.TestCase):
    def run_case(self, **kwargs):
        x = delayed_report_story(**kwargs)
        state = replay(registry(), x.spec, x.path)
        return x, state, render(x.spec, state)

    def test_old_accurate_report_has_positive_control_then_each_mask_abstains(self):
        x, state, doc = self.run_case()
        answer = Reader(doc).ask("historical_truth", "report")
        self.assertTrue(answer.supported)
        self.assertIn("matched", answer.answer)
        self.assertIn("workshop at time 0", answer.answer)
        self.assertEqual(answer.reference_tick, 0)
        self.assertTrue({"look_old:1/observation/old", "report:1/claim/report"}.issubset(answer.statement_ids))
        for support in answer.statement_ids:
            with self.subTest(hidden=support):
                self.assertFalse(Reader(doc.mask([support])).ask("historical_truth", "report").supported)
        visible = render(x.spec, state, visible={"report:1"})
        self.assertFalse(Reader(visible).ask("historical_truth", "report").supported)

    def test_later_change_is_not_a_historical_lie_or_current_refresh(self):
        _, _, doc = self.run_case()
        reader = Reader(doc)
        change = reader.ask("later_change", "report")
        self.assertTrue(change.supported)
        self.assertIn("jetty at time 2", change.answer)
        self.assertEqual(change.reference_tick, 2)
        self.assertIn("look_old:1", change.event_ids)
        self.assertIn("look_new:1", change.event_ids)
        for support in change.statement_ids:
            self.assertFalse(Reader(doc.mask([support])).ask("later_change", "report").supported)
        applicability = reader.ask("present_applicability", "report")
        self.assertTrue(applicability.supported)
        self.assertIn("did not establish the current location", applicability.answer)
        self.assertNotRegex(doc.story.lower(), r"\b(?:lie|lied|liar)\b")

    def test_omit_second_observation_retains_belief_without_claiming_changed_truth(self):
        x, state, doc = self.run_case(second_observation=False)
        self.assertIsNone(state.get("evidence", "fresh"))
        self.assertIsNone(state.get("dispositions", "revision"))
        self.assertEqual(state.get("belief_heads", "current").belief, "prediction")
        self.assertTrue(Reader(doc).ask("historical_truth", "report").supported)
        self.assertTrue(Reader(doc).ask("present_applicability", "report").supported)
        self.assertFalse(Reader(doc).ask("later_change", "report").supported)
        self.assertFalse(Reader(doc).ask("location", "gauge", reference_tick=2).supported)
        kept = replay_selection(registry(), x.spec, state, ["accept_old:1"])
        self.assertEqual(render(x.spec, kept), render(x.spec, state, visible={e.id for e in kept.events}))

    def test_changed_reference_claim_needs_matching_time_evidence_to_be_disproved(self):
        x, state, doc = self.run_case(report_reference=2)
        self.assertEqual(state.get("claims", "report").proposition, "prediction")
        before = replay(registry(), x.spec, x.path[:x.path.index("look_new")])
        self.assertFalse(Reader(render(x.spec, before)).ask("historical_truth", "report").supported)
        answer = Reader(doc).ask("historical_truth", "report")
        self.assertTrue(answer.supported)
        self.assertIn("did not match", answer.answer)
        self.assertIn("jetty at time 2", answer.answer)
        self.assertEqual(answer.reference_tick, 2)
        self.assertNotIn("look_old:1", answer.event_ids)
        self.assertFalse(Reader(doc.mask(["look_new:1/observation/fresh"]))
                         .ask("historical_truth", "report").supported)
        self.assertFalse(Reader(doc).ask("later_change", "report").supported)
        _, _, unresolved = self.run_case(report_reference=2, second_observation=False)
        self.assertFalse(Reader(unresolved).ask("historical_truth", "report").supported)

    def test_answer_event_roots_keep_exact_comparison_support_through_pruning(self):
        for kwargs, kind in (({}, "historical_truth"), ({}, "later_change"),
                              ({"report_reference": 2}, "historical_truth")):
            x, state, doc = self.run_case(**kwargs)
            answer = Reader(doc).ask(kind, "report")
            self.assertTrue(answer.supported)
            retained = replay_selection(registry(), x.spec, state, answer.event_ids)
            selected_doc = render(x.spec, state, visible={e.id for e in retained.events})
            self.assertEqual(selected_doc, render(x.spec, retained))
            self.assertEqual(Reader(selected_doc).ask(kind, "report"), answer)


if __name__ == "__main__":
    unittest.main()
