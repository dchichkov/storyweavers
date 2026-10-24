"""G3/S7/T2: actual competing choices, not just a boundary-time delivery."""
from dataclasses import replace
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.choices import CHOICE_BINDINGS, competing_promise_story
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import execute, matches, plain, replay, replay_selection, select_events
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render


class CapabilityChoiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = registry()

    def before(self, scenario, action_id):
        return replay(self.engine, scenario.spec, scenario.path[:scenario.path.index(action_id)])

    def enact(self, scenario, state, action_id):
        action = next(a for a in scenario.spec.actions if a.id == action_id)
        return execute(self.engine, scenario.spec, state, action)

    def finish(self, scenario):
        state = replay(self.engine, scenario.spec, scenario.path)
        self.assertTrue(all(matches(state, q) for q in scenario.spec.goal))
        self.engine.validate(state)
        return state

    def test_empty_dynamic_tables_and_accepted_requests_are_not_actions_or_promises(self):
        x = competing_promise_story()
        initial = self.engine.initial(x.spec)
        for table in ("requests", "promises", "refusals", "receipts", "readiness", "attention",
                      "evidence", "claims", "claim_receipts", "comprehensions", "beliefs", "belief_heads",
                      "dispositions", "domain_receipts", "loans"):
            self.assertFalse(initial.tables[table], table)
        accepted = self.before(x, "promise_first")
        self.assertEqual(accepted.get("requests", "R_first").response, "accepted")
        self.assertEqual(accepted.get("parents", "resource").parent, "worker")
        self.assertFalse(accepted.tables["promises"])
        self.assertFalse(accepted.tables["receipts"])

    def test_both_understood_promises_physically_selectable_then_consumption_blocks_other(self):
        for binding in CHOICE_BINDINGS:
            for priority in ("first", "second"):
                with self.subTest(setting=binding.title, priority=priority):
                    x = competing_promise_story(binding=binding, priority=priority)
                    before = self.before(x, f"choose_{priority}")
                    self.assertEqual(before.tick, 1)
                    self.assertEqual(before.get("ownership", "resource").owner, "worker")
                    self.assertFalse(before.tables["receipts"])
                    original = plain(before)
                    for role in ("first", "second"):
                        p = before.get("promises", f"P_{role}")
                        self.assertEqual(p.status, "active")
                        req = before.get("requests", f"R_{role}")
                        self.assertIsNotNone(req.understood_event)
                        event = next(e for e in before.events if e.id == p.created_event)
                        self.assertEqual(event.data["understood_by"], role)
                        option = self.enact(x, before, f"choose_{role}")
                        self.assertIsNotNone(option, "Each actual handoff must execute from the identical pre-state")
                        self.assertEqual(option.get("parents", "resource").parent, role)
                        self.assertEqual(option.get("receipts", f"choose_{role}:1").tick, 1)
                    self.assertEqual(plain(before), original)
                    chosen = self.enact(x, before, f"choose_{priority}")
                    other = "second" if priority == "first" else "first"
                    snapshot = plain(chosen)
                    self.assertIsNone(self.enact(x, chosen, f"choose_{other}"))
                    self.assertIsNone(self.enact(x, chosen, "ready_recovery"))
                    self.assertIsNone(self.enact(x, chosen, "recover_resource"))
                    self.assertEqual(plain(chosen), snapshot)
                    self.assertEqual(len(chosen.tables["receipts"]), 1)
                    # A physical effect is not the promise assessment writer.
                    self.assertEqual(chosen.get("promises", f"P_{other}").status, "active")
                    self.assertEqual(chosen.get("ownership", "resource").owner, "worker")

    def test_resource_choice_not_names_or_title_changes_semantic_outcome(self):
        signatures = []
        for binding in CHOICE_BINDINGS:
            outcomes = []
            for priority in ("first", "second"):
                x = competing_promise_story(binding=binding, priority=priority)
                state = self.finish(x)
                self.assertEqual(state.get("parents", "resource").parent, priority)
                self.assertEqual(state.get("requests", f"R_{priority}").completion_receipt,
                                 f"choose_{priority}:1")
                other = "second" if priority == "first" else "first"
                self.assertIsNone(state.get("requests", f"R_{other}").completion_receipt)
                self.assertEqual(state.get("promises", f"P_{priority}").status, "fulfilled")
                self.assertEqual(state.get("promises", f"P_{other}").status, "breached")
                outcomes.append((state.get("parents", "resource").parent,
                                 tuple((p.id, p.status) for p in state.tables["promises"].values())))
                renamed = replace(x.spec, title="An unrelated title", records={
                    table: tuple(replace(r, name=f"renamed {r.id}") if table == "entities" else r for r in rows)
                    for table, rows in x.spec.records.items()})
                changed_names = replay(self.engine, renamed, x.path)
                self.assertEqual(changed_names.events, state.events)
                self.assertEqual(changed_names.tables["promises"], state.tables["promises"])
            self.assertNotEqual(*outcomes)
            signatures.append(outcomes)
        self.assertTrue(all(s == signatures[0] for s in signatures))

    def test_communication_comprehension_and_belief_adoption_remain_distinct(self):
        x = competing_promise_story()
        received = self.before(x, "understand_need")
        self.assertTrue(received.tables["evidence"])
        self.assertTrue(received.tables["claims"])
        self.assertTrue(received.tables["claim_receipts"])
        self.assertFalse(received.tables["comprehensions"])
        self.assertFalse(received.tables["beliefs"])
        understood = self.before(x, "adopt_need")
        self.assertTrue(understood.tables["comprehensions"])
        self.assertFalse(understood.tables["beliefs"])
        adopted = self.before(x, "choose_first")
        belief = adopted.get("beliefs", "priority_decision:belief")
        self.assertEqual(belief.comprehension_ids, ("need_understood",))
        self.assertEqual(belief.source_ids, ("signal",))
        self.assertEqual(adopted.get("propositions", belief.proposition).result.value, "first")

    def test_action_without_promising_keeps_receipt_and_completion_but_no_commitment(self):
        for binding in CHOICE_BINDINGS:
            x = competing_promise_story(binding=binding, intervention="action_only")
            state = self.finish(x)
            self.assertFalse(state.tables["promises"])
            self.assertEqual(state.get("receipts", "choose_first:1").destination, "first")
            self.assertEqual(state.get("requests", "R_first").completion_receipt, "choose_first:1")
            self.assertEqual(state.get("requests", "R_new").response, "declined")
            self.assertFalse(Reader(render(x.spec, state)).ask("promise_status", "P_second").supported)

    def test_promising_without_acting_breaches_both_despite_available_ability(self):
        for binding in CHOICE_BINDINGS:
            x = competing_promise_story(binding=binding, intervention="promise_only")
            state = self.finish(x)
            self.assertFalse(state.tables["receipts"])
            self.assertEqual(state.get("parents", "resource").parent, "worker")
            for role in ("first", "second"):
                p = state.get("promises", f"P_{role}")
                self.assertEqual(p.status, "breached")
                self.assertIsNone(p.performance_receipt)
                self.assertIsNone(p.release_event)
                # Deadline status does not disable a physical operation.
                self.assertIsNotNone(self.enact(x, state, f"choose_{role}"))
            doc = render(x.spec, state, premise=x.premise, ending=x.ending)
            self.assertFalse(Reader(doc).ask("why", "resource").supported)
            self.assertIn("both waiting hands were empty", doc.story)

    def test_new_request_refusal_after_breach_cannot_cancel_old_promise(self):
        x = competing_promise_story()
        before = self.before(x, "decline_new")
        self.assertEqual(before.get("promises", "P_second").status, "breached")
        self.assertEqual(before.get("requests", "R_new").response, "pending")
        state = self.finish(x)
        self.assertEqual(state.tables["promises"], before.tables["promises"])
        self.assertEqual(state.tables["parents"], before.tables["parents"])
        self.assertEqual(state.get("requests", "R_second").response, "accepted")
        self.assertIsNone(state.get("promises", "P_second").release_event)
        refusal = state.get("refusals", "decline_new:1")
        self.assertEqual((refusal.target, refusal.reason_kind), ("R_new", "unwillingness"))
        # Worker owns and holds the substitute and can hand it over: this is
        # unwillingness, not inability or absent/unknown lending authority.
        self.assertEqual(state.get("ownership", "substitute").owner, "worker")
        self.assertIsNotNone(self.enact(x, state, "deliver_substitute"))

    def test_restoring_ability_and_late_exact_performance_never_erase_breach(self):
        x = competing_promise_story()
        state = self.finish(x)
        breach = state.get("promises", "P_second")
        for action_id in ("ready_recovery", "recover_resource"):
            state = self.enact(x, state, action_id)
            self.assertIsNotNone(state)
        self.assertEqual(state.get("parents", "resource").parent, "worker")
        self.assertEqual(state.get("promises", "P_second"), breach)
        state = self.enact(x, state, "choose_second")
        self.assertIsNotNone(state)
        self.assertEqual(state.get("promises", "P_second"), breach)
        repaired = self.enact(x, state, "repair_other")
        p = repaired.get("promises", "P_second")
        self.assertEqual((p.status, p.repair_receipt), ("breached", "choose_second:1"))
        self.assertEqual(p.assessment_event, breach.assessment_event)
        self.assertIsNone(p.performance_receipt)
        self.assertIsNone(self.enact(x, repaired, "complete_second"))

    def test_release_plus_new_exact_terms_preserves_original_and_matches_only_substitute(self):
        for binding in CHOICE_BINDINGS:
            for priority in ("first", "second"):
                x = competing_promise_story(binding=binding, priority=priority, intervention="release_new")
                other = "second" if priority == "first" else "first"
                state = self.finish(x)
                old = state.get("promises", f"P_{other}")
                new = state.get("promises", "P_replacement")
                self.assertEqual((old.status, old.version, old.action_spec), ("released", 1, f"task_{other}"))
                self.assertIsNone(old.assessment_event)
                self.assertIsNone(old.performance_receipt)
                self.assertEqual((new.status, new.version, new.replaces), ("fulfilled", 2, old.id))
                self.assertEqual(new.performance_receipt, "deliver_substitute:1")
                self.assertEqual(state.get("requests", f"R_{other}").response, "accepted")
                self.assertIsNone(state.get("requests", f"R_{other}").completion_receipt)
                self.assertIsNone(self.enact(x, state, f"complete_{other}"))
                wrong_receipt_spec = replace(x.spec, actions=tuple(
                    replace(a, args={**a.args, "receipt": "deliver_substitute:1"})
                    if a.id == f"complete_{other}" else a for a in x.spec.actions))
                wrong_receipt = next(a for a in wrong_receipt_spec.actions if a.id == f"complete_{other}")
                snapshot = plain(state)
                self.assertIsNone(execute(self.engine, wrong_receipt_spec, state, wrong_receipt))
                self.assertEqual(plain(state), snapshot)
                # Remove the release: replacement cannot create itself or edit
                # original terms. Remove substitute: the first delivery cannot
                # stand in as an exact v2 receipt.
                unreleased_path = x.path[:x.path.index("release_old")]
                unreleased = replay(self.engine, x.spec, unreleased_path)
                self.assertIsNone(self.enact(x, unreleased, "promise_replacement"))
                no_substitute = replay(self.engine, x.spec, [a for a in x.path
                                      if a not in {"deliver_substitute", "assess_replacement"}])
                failed = self.enact(x, no_substitute, "assess_replacement")
                self.assertEqual(failed.get("promises", "P_replacement").status, "breached")
                self.assertEqual(failed.get("promises", old.id).status, "released")

    def test_replay_pruning_retains_choice_evidence_promises_and_refusal_not_every_event(self):
        for binding in CHOICE_BINDINGS:
            x = competing_promise_story(binding=binding)
            self.assertEqual(loads(self.engine, dumps(x.spec)), x.spec)
            full = self.finish(x)
            self.assertEqual(replay(self.engine, x.spec, x.path), full)
            roots = ("complete_first:1", "assess_first:1", "assess_second:1", "decline_new:1")
            selected = select_events(full, roots)
            kept = replay_selection(self.engine, x.spec, full, roots)
            self.assertEqual(kept.events, selected)
            self.assertLess(len(kept.events), len(full.events))
            ids = {e.id for e in kept.events}
            self.assertNotIn("ack_first:1", ids)
            self.assertNotIn("ack_second:1", ids)
            self.assertTrue({"choose_first:1", "see_need:1", "report_need:1", "receive_need:1",
                             "understand_need:1", "adopt_need:1", "promise_first:1", "promise_second:1",
                             "deliver_new_request:1"} <= ids)
            for table in ("promises", "requests", "parents", "beliefs", "evidence", "refusals"):
                self.assertEqual(kept.tables[table], full.tables[table])
            full_doc = render(x.spec, full, visible=ids)
            kept_doc = render(x.spec, kept)
            self.assertEqual(full_doc, kept_doc)
            self.assertEqual(Reader(full_doc).questions(), Reader(kept_doc).questions())

    def test_reader_qa_motive_mask_and_focused_followups_use_rendered_choice(self):
        for binding in CHOICE_BINDINGS:
            x = competing_promise_story(binding=binding)
            state = self.finish(x)
            doc = render(x.spec, state, premise=x.premise, ending=x.ending)
            reader = Reader(doc)
            action_answer = reader.ask("placement", "resource", event_id="choose_first:1")
            self.assertTrue(action_answer.supported)
            why = reader.follow_up("why")
            self.assertTrue(why.supported)
            self.assertIn("give " + binding.first + "'s session priority", why.answer)
            self.assertEqual(why.event_ids, ("choose_first:1",))
            self.assertEqual(why.reference_tick, 1)
            self.assertIn("choose_first:1/placement/resource", why.statement_ids)
            self.assertTrue(reader.ask("promise_status", "P_second").supported)
            self.assertTrue(reader.ask("response", "R_new").supported)
            self.assertTrue(reader.follow_up("why").supported)
            for hidden in ("choose_first:1/why/resource", "choose_first:1/placement/resource"):
                masked = Reader(doc.mask([hidden]))
                self.assertFalse(masked.ask("why", "resource", event_id="choose_first:1").supported)
            masked = Reader(doc.mask(["choose_first:1/why/resource"]))
            self.assertTrue(masked.ask("placement", "resource").supported)
            self.assertFalse(masked.follow_up("why").supported)
            self.assertTrue(masked.ask("promise_status", "P_second").supported)
            self.assertFalse(Reader(doc.mask(["deliver_new_request:1/request/R_new"]))
                             .ask("response", "R_new").supported)
            for span, statement in zip(doc.spans(), doc.statements):
                self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
            self.assertTrue(all(a.supported and a.statement_ids and a.event_ids for a in reader.questions()))

    def test_reason_changes_with_fixed_props_and_guards_are_not_motives(self):
        baseline = competing_promise_story()
        changed = competing_promise_story(priority_reason="I put the earlier agreed session first.")
        self.assertEqual(baseline.spec.records, changed.spec.records)
        first, second = self.finish(baseline), self.finish(changed)
        self.assertEqual(first.tables, second.tables)
        self.assertNotEqual(Reader(render(baseline.spec, first)).ask("why", "resource").answer,
                            Reader(render(changed.spec, second)).ask("why", "resource").answer)
        no_reason = replace(baseline.spec, actions=tuple(
            replace(a, reason=None) if a.id == "choose_first" else a for a in baseline.spec.actions))
        state = replay(self.engine, no_reason, baseline.path)
        self.assertEqual(state.tables, first.tables)
        choice_event = next(e for e in state.events if e.id == "choose_first:1")
        self.assertIn("adopt_need:1", choice_event.causes)
        doc = render(no_reason, state)
        self.assertTrue(Reader(doc).ask("placement", "resource").supported)
        self.assertFalse(Reader(doc).ask("why", "resource").supported)

    def test_promise_outcome_prose_and_qa_identify_the_exact_task(self):
        x = competing_promise_story()
        state = replay(self.engine, x.spec, x.path)
        reader = Reader(render(x.spec, state))
        for promise, recipient, outcome in (("P_first", "Bea", "had kept"),
                                             ("P_second", "Cleo", "had not kept")):
            answer = reader.ask("promise_status", promise)
            self.assertTrue(answer.supported)
            self.assertIn(f"hand the only projector to {recipient}", answer.answer)
            self.assertIn(f"hand the only projector to {recipient}", answer.question)
            self.assertIn(outcome, answer.answer)


if __name__ == "__main__":
    unittest.main()
