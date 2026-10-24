from dataclasses import replace
from itertools import product
import unittest

from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import Action, execute, matches, replay
from storyscenes.capabilities.reading import Reader
from storyscenes.harbor_questions_story import Conditions, KINDS, generate, registry, understood_value


class HarborRecoveryTests(unittest.TestCase):
    def sample(self, **kw):
        return generate(config=Conditions(recover=True, **kw))

    def before(self, row, spec, id):
        return replay(registry(), spec, row["path"][:row["path"].index(id)])

    def apply(self, spec, state, id):
        return execute(registry(), spec, state, next(a for a in spec.actions if a.id == id))

    def test_full_recovery_grid_replays_and_keeps_reader_support(self):
        for kind, actual, readable, reported, busy, first, attempt in product(KINDS, *((False, True),) * 6):
            with self.subTest(kind=kind, actual=actual, readable=readable, reported=reported,
                              busy=busy, first=first, attempt=attempt):
                row, spec, state, doc = self.sample(kind=kind, actual=actual, readable=readable, reported=reported,
                    prior_commitment=busy, keep_promise_first=first, attempt_first=attempt)
                self.assertEqual(replay(registry(), loads(registry(), dumps(spec)), row["path"]), state)
                self.assertTrue(all(matches(state, q) for q in spec.goal))
                self.assertLessEqual(len(row["path"]), spec.max_steps)
                self.assertGreaterEqual(len(row["qa"]), 4)
                self.assertEqual(len(row["qa"]), len({q["question"] for q in row["qa"]}))
                self.assertFalse(Reader(doc.mask(("opening",))).questions())
                if state.get("evidence", "reseen"):
                    self.assertFalse(Reader(doc.mask(("reinspection",))).ask("ending", "ari").supported)
                for statement in doc.statements:
                    self.assertTrue(set(statement.event_ids) <= {e.id for e in state.events})

    def test_new_view_requires_actual_removal_not_only_a_deferred_question(self):
        for kind in ("load", "parcel", "tool"):
            row, spec, _, _ = self.sample(kind=kind, readable=False)
            before = self.before(row, spec, "peel_take")
            self.assertIsNone(self.apply(spec, before, "reinspect"))
            self.assertEqual(before.get("evidence", "seen").outcome, "unknown")
            after = self.apply(spec, self.apply(spec, before, "peel_take"), "peel_place")
            self.assertEqual(after.get("parents", "cover").parent, "bench")
            self.assertIsNone(after.get("evidence", "reseen"))
            self.assertIsNone(understood_value(after))
            self.assertIsNotNone(self.apply(spec, after, "reinspect"))

    def test_reinspection_preserves_first_unknown_evidence_and_its_deferred_belief(self):
        row, spec, state, _ = self.sample(kind="load", actual=True, readable=False)
        before = self.before(row, spec, "peel_take")
        self.assertEqual(state.get("evidence", "seen"), before.get("evidence", "seen"))
        self.assertEqual(state.get("propositions", "seen:proposition").result.kind, "unknown")
        self.assertEqual(state.get("dispositions", "decision").mode, "defer")
        self.assertTrue(understood_value(state))
        belief = state.get("beliefs", "recheck:belief")
        self.assertEqual(belief.predecessor, "prior")
        self.assertEqual(belief.evidence_ids, ("reseen",))

    def test_second_report_needs_fresh_hearing_and_comprehension(self):
        row, spec, state, _ = self.sample(kind="load", actual=False, readable=False, reported=True)
        before = self.before(row, spec, "reunderstand")
        self.assertIsNone(self.apply(spec, before, "reresolve"))
        self.assertIsNone(understood_value(before))
        self.assertEqual(state.get("beliefs", "recheck:belief").comprehension_ids, ("reunderstood",))
        self.assertFalse(understood_value(state))

    def test_first_inspection_qa_remains_unknown_after_successful_second_look(self):
        for attempt in (False, True):
            _, _, state, doc = self.sample(kind="load", actual=True, readable=False, attempt_first=attempt)
            self.assertEqual(state.get("evidence", "reseen").outcome, "exact")
            inspection = next(s for s in doc.statements if s.id == "inspection")
            self.assertIn("first", inspection.question)
            text = inspection.text
            self.assertIn("hid", text)
            self.assertNotIn("found two", text)
            second = next(s.text for s in doc.statements if s.id == "reinspection")
            self.assertIn("two stone slabs", second)

    def test_refusal_can_lead_to_separate_lifts_without_fulfilling_cys_request(self):
        for attempt in (False, True):
            row, _, state, _ = self.sample(kind="load", actual=True, prior_commitment=True, attempt_first=attempt)
            self.assertEqual(row["plot"]["outcome"], "divided_after_refusal")
            self.assertEqual(state.get("requests", "help").response, "declined")
            self.assertIsNone(state.get("requests", "help").completion_receipt)
            self.assertEqual(state.get("parents", "crate").parent, "cart")
            for part in ("clue", "second_slab"):
                self.assertEqual(state.get("parents", part).parent, "crate")
            self.assertEqual(state.get("promises", "key_return").status, "fulfilled")

    def test_both_slabs_together_still_exceed_capacity(self):
        row, spec, _, _ = self.sample(kind="load", actual=True, prior_commitment=True)
        whole = Action(id="whole", operation="pickup", actor="ari", args=dict(object="crate", source="workshop"))
        second = Action(id="both", operation="pickup", actor="ari", args=dict(object="second_slab", source="crate"))
        spec = replace(spec, actions=spec.actions + (whole, second))
        before = self.before(row, spec, "lift_part_one")
        self.assertIsNone(execute(registry(), spec, before, whole))
        after = self.apply(spec, before, "lift_part_one")
        self.assertIsNone(execute(registry(), spec, after, second))
        self.assertEqual(after.get("parents", "second_slab").parent, "crate")

    def test_small_lifts_are_not_guaranteed_when_capacity_changes(self):
        row, spec, _, _ = self.sample(kind="load", actual=True, prior_commitment=True)
        records = dict(spec.records, entities=tuple(replace(e, capacity=9) if e.id == "ari" else e
                                                  for e in spec.records["entities"]))
        spec = replace(spec, records=records)
        state = self.before(row, spec, "lift_part_one")
        self.assertIsNone(self.apply(spec, state, "lift_part_one"))

    def test_empty_crate_on_cart_is_not_completed_divided_loading(self):
        row, spec, _, _ = self.sample(kind="load", actual=True, prior_commitment=True)
        before = self.before(row, spec, "pack_part_two")
        # Settle the independent promise so it cannot mask the missing slab.
        for id in ("key_lane", "time_2", "key_round", "time_3", "key_ready", "key_return", "time_4", "key_assess"):
            before = self.apply(spec, before, id)
            self.assertIsNotNone(before, id)
        self.assertIsNone(self.apply(spec, before, "finish"))

    def test_fog_is_not_a_removable_wrapper(self):
        row, spec, state, _ = self.sample(kind="shortcut", readable=False)
        self.assertNotIn("peel_take", {a.id for a in spec.actions})
        self.assertEqual(state.get("evidence", "seen").outcome, "unknown")
        self.assertIsNone(state.get("evidence", "reseen"))
        self.assertEqual(row["plot"]["outcome"], "known_lane")


if __name__ == "__main__":
    unittest.main()
