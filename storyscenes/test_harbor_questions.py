from dataclasses import replace
from itertools import product
import unittest

from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import CapabilityError, execute, matches, replay
from storyscenes.capabilities.epistemic import Result
from storyscenes.capabilities.reading import Reader
from storyscenes.harbor_questions_story import Conditions, KINDS, build, generate, registry


class HarborQuestionTests(unittest.TestCase):
    def test_full_declared_grid_replays_after_json_and_retains_visible_qa(self):
        for kind, actual, readable, reported, busy, first in product(KINDS, *((False, True),) * 5):
            with self.subTest(kind=kind, actual=actual, readable=readable, reported=reported, busy=busy, first=first):
                row, spec, state, doc = generate(config=Conditions(kind=kind, actual=actual, readable=readable,
                    reported=reported, prior_commitment=busy, keep_promise_first=first))
                self.assertEqual(replay(registry(), loads(registry(), dumps(spec)), row["path"]), state)
                self.assertTrue(all(matches(state, q) for q in spec.goal))
                self.assertGreaterEqual(len(row["qa"]), 6)
                self.assertEqual(len(row["qa"]), len({q["question"] for q in row["qa"]}))
                anchors = {e.id for e in state.events}
                for statement, span in zip(doc.statements, doc.spans()):
                    self.assertTrue(set(statement.event_ids) <= anchors)
                    self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
                self.assertFalse(Reader(doc.mask(("opening",))).questions())
                self.assertFalse(Reader(doc.mask(("inspection",))).ask("ending", "ari").supported)

    def test_occluded_truth_does_not_leak_into_story_decision_or_qa(self):
        for kind, reported in product(KINDS, (False, True)):
            first, _, state, _ = generate(config=Conditions(kind=kind, reported=reported, readable=False, actual=False))
            second, _, _, _ = generate(config=Conditions(kind=kind, reported=reported, readable=False, actual=True))
            self.assertEqual(first["story"], second["story"])
            self.assertEqual(first["qa"], second["qa"])
            self.assertEqual(first["path"], second["path"])
            self.assertEqual(first["plot"]["outcome"], "known_lane" if kind == "shortcut" else "deferred")
            self.assertEqual(state.get("belief_heads", "ari_view").belief, "prior")
            if kind == "shortcut":
                self.assertIsNotNone(state.get("requests", "help").completion_receipt)
                self.assertEqual(state.get("parents", "crate").parent, "jetty")
            else:
                self.assertIsNone(state.get("requests", "help").completion_receipt)
                self.assertIsNotNone(state.get("requests", "help").withdrawal_event)

    def test_changed_evidence_changes_actual_custody_route_or_tool_use(self):
        expected = {"load": ("bench", "cart"), "parcel": ("bench", "boat"),
                    "shortcut": ("jetty", "jetty"), "tool": ("bench", "bench")}
        for kind in KINDS:
            a, _, sa, _ = generate(config=Conditions(kind=kind, actual=False))
            b, _, sb, _ = generate(config=Conditions(kind=kind, actual=True))
            self.assertEqual((sa.get("parents", "crate").parent, sb.get("parents", "crate").parent), expected[kind])
            self.assertNotEqual(a["path"], b["path"])
            self.assertNotEqual(a["plot"]["outcome"], b["plot"]["outcome"])
        self.assertEqual(sa.get("parents", "scissors").parent, "cy")
        self.assertEqual(sb.get("parents", "scissors").parent, "ari")

    def test_hearing_without_understanding_cannot_revise_belief(self):
        row, spec, _, _ = generate(config=Conditions(kind="load", reported=True))
        before = replay(registry(), spec, row["path"][:row["path"].index("understand")])
        action = next(a for a in spec.actions if a.id == "resolve")
        self.assertIsNone(execute(registry(), spec, before, action))

    def test_acceptance_does_not_count_as_completed_loading(self):
        row, spec, _, _ = generate(config=Conditions(kind="load", actual=True))
        before = replay(registry(), spec, row["path"][:row["path"].index("cy_take")])
        action = next(a for a in spec.actions if a.id == "finish")
        self.assertIsNone(execute(registry(), spec, before, action))

    def test_closed_bridge_is_rejected_even_if_request_is_accepted(self):
        row, spec, _, _ = generate(config=Conditions(kind="shortcut", actual=False))
        before = replay(registry(), spec, row["path"][:row["path"].index("lane")])
        bridge = next(a for a in spec.actions if a.id == "bridge")
        self.assertIsNone(execute(registry(), spec, before, bridge))
        self.assertNotIn("bridge", row["path"])

    def test_resolution_cannot_be_preloaded(self):
        _, spec, state, _ = generate(config=Conditions())
        records = dict(spec.records, harbor_resolutions=tuple(state.tables["harbor_resolutions"].values()))
        with self.assertRaisesRegex(CapabilityError, "enacted"):
            registry().initial(replace(spec, records=records))

    def test_reported_inspection_has_actual_information_transfer(self):
        row, _, state, _ = generate(config=Conditions(kind="tool", reported=True, actual=False))
        self.assertLess(row["path"].index("understand"), row["path"].index("resolve"))
        belief = state.get("beliefs", state.get("belief_heads", "ari_view").belief)
        self.assertEqual(belief.comprehension_ids, ("understood",))
        self.assertEqual(belief.evidence_ids, ())
        self.assertEqual(belief.predecessor, "prior")

    def test_sampler_does_not_confine_uncertainty_to_odd_numbered_problem_types(self):
        from storyscenes.harbor_questions_story import conditions
        unclear = {conditions(seed).kind for seed in range(1000) if not conditions(seed).readable}
        self.assertEqual(unclear, set(KINDS))

    def test_unknown_parcel_is_not_called_a_proven_mistake(self):
        row, _, _, _ = generate(config=Conditions(kind="parcel", readable=False))
        self.assertNotIn("one fewer mistake", row["story"])
        self.assertNotIn("cups were still cups", row["story"])

    def test_unknown_qa_names_the_actual_object_without_unresolved_alternatives(self):
        for kind, noun in (("load", "crate"), ("parcel", "box"), ("tool", "parcel")):
            _, _, _, doc = generate(config=Conditions(kind=kind, readable=False))
            answer = next(s.answer for s in doc.statements if s.id == "action")
            self.assertIn(f"The {noun} remained", answer)
            self.assertNotIn(" or ", answer)

    def test_unknown_parcel_inspection_does_not_preempt_report_dialogue(self):
        _, _, _, doc = generate(config=Conditions(kind="parcel", readable=False, reported=True))
        inspection = next(s.text for s in doc.statements if s.id == "inspection")
        self.assertNotIn("Ari", inspection)
        self.assertNotIn('"', inspection)

    def test_revision_answer_keeps_inspector_separate_from_decision_maker(self):
        for reported, name in ((False, "Ari"), (True, "Cy")):
            _, _, _, doc = generate(config=Conditions(kind="tool", actual=False, reported=reported))
            answer = next(s.answer for s in doc.statements if s.id == "revision")
            self.assertTrue(answer.startswith(f"{name} had found a bow,"))
            self.assertIn("Ari withdrew", answer)

    def test_unknown_shortcut_uses_known_alternative_without_inventing_a_bridge_result(self):
        row, spec, state, _ = generate(config=Conditions(kind="shortcut", readable=False, actual=True))
        self.assertIn("lane", row["path"])
        self.assertNotIn("bridge", row["path"])
        self.assertEqual(state.get("evidence", "seen").outcome, "unknown")
        self.assertEqual(state.get("belief_heads", "ari_view").belief, "prior")
        before = replay(registry(), spec, row["path"][:row["path"].index("lane")])
        bridge = next(a for a in spec.actions if a.id == "bridge")
        self.assertIsNone(execute(registry(), spec, before, bridge))

    def test_prior_priority_changes_real_work_and_promise_performance(self):
        keep, _, kept, _ = generate(config=Conditions(kind="load", actual=True, prior_commitment=True))
        help_first, _, late, _ = generate(config=Conditions(kind="load", actual=True, prior_commitment=True, keep_promise_first=False))
        self.assertEqual(keep["plot"]["outcome"], "waiting_for_help")
        self.assertEqual(kept.get("parents", "crate").parent, "workshop")
        self.assertEqual(kept.get("promises", "key_return").status, "fulfilled")
        self.assertEqual(help_first["plot"]["outcome"], "help_completed")
        self.assertEqual(late.get("parents", "crate").parent, "cart")
        self.assertEqual(late.get("promises", "key_return").status, "breached")
        self.assertEqual(late.get("promises", "key_return").repair_receipt, "key_return:1")
        self.assertEqual(late.get("parents", "key").parent, "bo")

    def test_declined_light_load_can_be_completed_by_requester(self):
        row, _, state, _ = generate(config=Conditions(kind="parcel", actual=True, prior_commitment=True))
        self.assertEqual(row["plot"]["outcome"], "self_loaded")
        self.assertEqual(state.get("parents", "crate").parent, "boat")
        self.assertEqual(state.get("requests", "help").response, "declined")
        self.assertIsNone(state.get("requests", "help").completion_receipt)
        self.assertEqual(state.get("promises", "key_return").status, "fulfilled")

    def test_refusal_question_focuses_on_the_character_named_in_its_answer(self):
        for kind in ("load", "parcel"):
            _, _, _, doc = generate(config=Conditions(kind=kind, actual=True, prior_commitment=True))
            statement = next(s for s in doc.statements if s.id == "revision")
            self.assertEqual(statement.question, "Why did Cy decline this request?")
            self.assertTrue(statement.answer.startswith("Cy declined"))

    def test_same_destination_and_quick_handoff_do_not_create_false_conflicts(self):
        for kind in ("shortcut", "tool"):
            row, _, state, _ = generate(config=Conditions(kind=kind, actual=True, prior_commitment=True))
            self.assertEqual(state.get("requests", "help").response, "accepted")
            self.assertIsNotNone(state.get("requests", "help").completion_receipt)
            self.assertEqual(state.get("promises", "key_return").status, "fulfilled")
            self.assertNotIn("refuse", row["path"])
            self.assertNotIn("I will do this first", row["story"])

    def test_refusal_needs_the_enacted_promise_and_confirmed_need(self):
        row, spec, _, _ = generate(config=Conditions(kind="load", actual=True, prior_commitment=True))
        refuse = next(a for a in spec.actions if a.id == "refuse")
        before = replay(registry(), spec, row["path"][:row["path"].index("inspect")])
        self.assertIsNone(execute(registry(), spec, before, refuse))
        self.assertEqual(refuse.reason_support, ("prior_promise:1",))

    def test_finish_cannot_substitute_for_the_actual_key_return(self):
        row, spec, _, _ = generate(config=Conditions(kind="load", actual=True, prior_commitment=True))
        before = replay(registry(), spec, row["path"][:row["path"].index("key_return")])
        finish = next(a for a in spec.actions if a.id == "finish")
        self.assertIsNone(execute(registry(), spec, before, finish))

    def test_known_alternative_requires_positive_actor_knowledge(self):
        row, spec, _, _ = generate(config=Conditions(kind="shortcut", readable=False))
        records = dict(spec.records)
        records["propositions"] = tuple(replace(p, result=Result(kind="exact", value=False))
                                         if p.id == "known_lane" else p for p in records["propositions"])
        spec = replace(spec, records=records)
        state = replay(registry(), spec, row["path"][:row["path"].index("accept")])
        accept = next(a for a in spec.actions if a.id == "accept")
        self.assertIsNone(execute(registry(), spec, state, accept))

    def test_help_first_work_cannot_skip_its_authored_time_cost(self):
        row, spec, _, _ = generate(config=Conditions(kind="load", actual=True,
            prior_commitment=True, keep_promise_first=False))
        state = replay(registry(), spec, row["path"][:row["path"].index("time_3")])
        take = next(a for a in spec.actions if a.id == "cy_take")
        self.assertIsNone(execute(registry(), spec, state, take))

    def test_promise_priority_cannot_be_ignored_by_accepting_the_conflicting_job(self):
        row, spec, _, _ = generate(config=Conditions(kind="load", actual=True, prior_commitment=True))
        state = replay(registry(), spec, row["path"][:row["path"].index("refuse")])
        accept = next(a for a in spec.actions if a.id == "accept")
        self.assertIsNone(execute(registry(), spec, state, accept))


if __name__ == "__main__":
    unittest.main()
