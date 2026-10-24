from dataclasses import replace
from itertools import product
import unittest

from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import CapabilityError, execute, matches, replay
from storyscenes.capabilities.reading import Reader
from storyscenes.harbor_questions_story import Conditions, KINDS, build, generate, registry


class HarborAttemptTests(unittest.TestCase):
    def sample(self, **kw):
        return generate(config=Conditions(attempt_first=True, **kw))

    def before(self, row, spec, action):
        return replay(registry(), spec, row["path"][:row["path"].index(action)])

    def apply(self, spec, state, action):
        return execute(registry(), spec, state, next(a for a in spec.actions if a.id == action))

    def test_full_attempt_grid_replays_serialized_and_retains_visible_support(self):
        for kind, actual, readable, reported, busy, first in product(KINDS, *((False, True),) * 5):
            with self.subTest(kind=kind, actual=actual, readable=readable, reported=reported, busy=busy, first=first):
                row, spec, state, doc = self.sample(kind=kind, actual=actual, readable=readable,
                    reported=reported, prior_commitment=busy, keep_promise_first=first)
                self.assertEqual(replay(registry(), loads(registry(), dumps(spec)), row["path"]), state)
                self.assertTrue(all(matches(state, q) for q in spec.goal))
                # The two short self-success paths have only four meaningful questions.
                self.assertGreaterEqual(len(row["qa"]), 4)
                self.assertEqual(len(row["qa"]), len({q["question"] for q in row["qa"]}))
                anchors = {e.id for e in state.events}
                for statement, span in zip(doc.statements, doc.spans()):
                    self.assertTrue(set(statement.event_ids) <= anchors)
                    self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
                    self.assertGreaterEqual(len(statement.answer.split()), 12)
                self.assertFalse(Reader(doc.mask(("opening",))).questions())
                self.assertFalse(Reader(doc.mask(("attempt",))).ask("ending", "ari").supported)

    def test_failed_lift_does_not_move_grant_receipt_or_fulfill(self):
        spec = build(Conditions(kind="load", actual=True, attempt_first=True))
        state = self.apply(spec, registry().initial(spec), "first_try")
        self.assertEqual(state.get("harbor_trials", "first").result, "too_heavy")
        self.assertEqual(state.get("parents", "crate").parent, "workshop")
        self.assertFalse(state.tables["receipts"])
        self.assertIsNone(self.apply(spec, state, "early_take"))
        self.assertIsNone(self.apply(spec, state, "finish"))

    def test_attempt_reads_actual_capacity_not_the_initial_belief(self):
        spec = build(Conditions(kind="load", actual=True, attempt_first=True))
        records = dict(spec.records, entities=tuple(replace(e, capacity=30) if e.id == "ari" else e
                                                  for e in spec.records["entities"]))
        spec = replace(spec, records=records)
        state = self.apply(spec, registry().initial(spec), "first_try")
        self.assertEqual(state.get("harbor_trials", "first").result, "liftable")
        self.assertEqual(state.get("parents", "crate").parent, "workshop")
        self.assertIsNotNone(self.apply(spec, state, "early_take"))

    def test_early_movement_is_not_a_contents_observation(self):
        for kind in ("load", "parcel"):
            row, spec, state, doc = self.sample(kind=kind, actual=False, readable=False)
            self.assertEqual(row["plot"]["outcome"], "retracted_unverified")
            self.assertEqual(state.get("parents", "crate").parent, "workshop")
            self.assertEqual(state.get("evidence", "seen").outcome, "unknown")
            self.assertEqual(state.get("belief_heads", "ari_view").belief, "prior")
            before = self.before(row, spec, "inspect")
            self.assertFalse(before.tables["evidence"])
            self.assertFalse(before.tables["requests"])
            self.assertIsNone(self.apply(spec, self.before(row, spec, "unverified_place"), "finish"))
            inspection = next(s.answer for s in doc.statements if s.id == "inspection")
            self.assertIn("wrapping", inspection.lower())

    def test_hidden_parcel_contents_do_not_leak(self):
        a, _, _, _ = self.sample(kind="parcel", actual=False, readable=False)
        b, _, _, _ = self.sample(kind="parcel", actual=True, readable=False)
        for key in ("story", "qa", "path", "plot"):
            self.assertEqual(a[key], b[key])

    def test_hidden_load_names_a_visible_belief_not_established_contents(self):
        for actual in (False, True):
            _, _, state, doc = self.sample(kind="load", actual=actual, readable=False)
            opening = next(s for s in doc.statements if s.id == "opening")
            self.assertIn("Ari thought the crate held stone slabs", opening.text)
            self.assertEqual(state.get("evidence", "seen").outcome, "unknown")
            self.assertIn("believed", opening.answer)

    def test_wrong_delivery_requires_actual_placement_and_actual_repair(self):
        row, spec, state, _ = self.sample(kind="parcel", actual=False)
        self.assertLess(row["path"].index("early_place"), row["path"].index("inspect"))
        self.assertEqual(self.before(row, spec, "inspect").get("parents", "crate").parent, "boat")
        self.assertEqual(state.get("parents", "crate").parent, "bench")
        self.assertEqual(state.get("requests", "help").completion_receipt, "repair_put:1")
        self.assertIsNone(self.apply(spec, self.before(row, spec, "repair_put"), "finish"))
        initial = self.apply(spec, registry().initial(spec), "early_take")
        self.assertIsNone(self.apply(spec, initial, "first_try"))

    def test_correct_delivery_is_confirmed_not_repeated(self):
        row, _, state, _ = self.sample(kind="parcel", actual=True)
        self.assertEqual(row["plot"]["outcome"], "delivery_confirmed_afterward")
        self.assertEqual(state.get("parents", "crate").parent, "boat")
        self.assertFalse(state.tables["requests"])
        self.assertNotIn("undo_take", row["path"])

    def test_blocked_crossing_uses_actual_alternative(self):
        row, spec, state, _ = self.sample(kind="shortcut", actual=False)
        before = self.before(row, spec, "put_back")
        self.assertIsNone(self.apply(spec, before, "early_cross"))
        self.assertIn("lane", row["path"])
        self.assertEqual(state.get("parents", "crate").parent, "jetty")
        self.assertEqual(row["plot"]["outcome"], "rerouted_after_attempt")

    def test_passable_trial_does_not_replace_crossing_or_placement(self):
        row, spec, state, _ = self.sample(kind="shortcut", actual=True)
        for step in ("early_cross", "early_place"):
            self.assertIsNone(self.apply(spec, self.before(row, spec, step), "finish"))
        self.assertEqual(state.get("parents", "crate").parent, "jetty")
        self.assertFalse(state.tables["requests"])

    def test_failed_pull_leaves_parcel_closed_until_scissors_are_used(self):
        row, spec, state, _ = self.sample(kind="tool", actual=True)
        before = self.before(row, spec, "inspect")
        self.assertFalse(before.get("containers", "crate").open)
        self.assertIsNone(self.apply(spec, before, "early_open"))
        self.assertIn("resolve", row["path"])
        self.assertNotIn("adopt", row["path"])
        self.assertTrue(state.get("containers", "crate").open)
        self.assertEqual(state.get("parents", "scissors").parent, "ari")

    def test_loose_fastening_requires_real_opening_and_no_scissors(self):
        row, spec, state, _ = self.sample(kind="tool", actual=False)
        self.assertIsNone(self.apply(spec, self.before(row, spec, "early_open"), "finish"))
        self.assertTrue(state.get("containers", "crate").open)
        self.assertEqual(state.get("parents", "scissors").parent, "cy")
        self.assertFalse(state.tables["requests"])

    def test_promise_priority_changes_help_but_not_the_first_attempt(self):
        for kind in ("load", "parcel"):
            a, _, kept, _ = self.sample(kind=kind, actual=kind == "load", prior_commitment=True)
            b, _, late, _ = self.sample(kind=kind, actual=kind == "load", prior_commitment=True, keep_promise_first=False)
            self.assertEqual(a["plot"]["attempt"], b["plot"]["attempt"])
            self.assertEqual(kept.get("requests", "help").response, "declined")
            self.assertEqual(kept.get("promises", "key_return").status, "fulfilled")
            self.assertEqual(late.get("promises", "key_return").status, "breached")
            self.assertEqual(late.get("promises", "key_return").repair_receipt, "key_return:1")
            if kind == "parcel":
                self.assertIn("self_repair", a["path"])
                self.assertEqual(kept.get("parents", "crate").parent, "bench")
                self.assertIsNone(kept.get("requests", "help").completion_receipt)

    def test_trial_cannot_be_preloaded(self):
        _, spec, state, _ = self.sample()
        records = dict(spec.records, harbor_trials=tuple(state.tables["harbor_trials"].values()))
        with self.assertRaisesRegex(CapabilityError, "enacted"):
            registry().initial(replace(spec, records=records))

    def test_final_answer_keeps_main_task_when_promise_also_resolves(self):
        _, _, _, doc = self.sample(kind="parcel", actual=False, prior_commitment=True)
        final = next(s.answer for s in doc.statements if s.id == "ending")
        self.assertIn("paint box", final)
        self.assertIn("key", final)
        self.assertNotIn("just described", final)


if __name__ == "__main__":
    unittest.main()
