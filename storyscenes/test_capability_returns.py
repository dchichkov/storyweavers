"""Production evidence for P-F1/P-F4/S-F3, not full slice acceptance.

Production-reader regressions preserve the three renderer defects first found
here; handwritten reading statements cannot manufacture their evidence.
"""
from copy import deepcopy
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.core import execute, fingerprint, matches, replay, replay_selection
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render
from storyscenes.capabilities.returns import receive_only_story, stale_authority_story, two_offer_story


class CapabilityReturnTests(unittest.TestCase):
    def setUp(self):
        self.engine = registry()

    def run_path(self, scenario, path=None):
        return replay(self.engine, scenario.spec, scenario.path if path is None else path)

    def step(self, scenario, state, *ids):
        by_id = {a.id: a for a in scenario.spec.actions}
        for action_id in ids:
            before = deepcopy(state)
            after = execute(self.engine, scenario.spec, state, by_id[action_id])
            self.assertIsNotNone(after, action_id)
            self.assertEqual(state, before, "successful execution mutated the input")
            state = after
        return state

    def reject(self, scenario, state, action_id):
        before = deepcopy(state)
        digest = fingerprint(state)
        candidate = next(a for a in scenario.spec.actions if a.id == action_id)
        # Avoid confusing domain rejection with exhausted authored action budget.
        self.assertLess(state.counts.get(action_id, 0), candidate.max_uses)
        self.assertIsNone(execute(self.engine, scenario.spec, state, candidate), action_id)
        self.assertEqual(state, before)
        self.assertEqual(fingerprint(state), digest)

    def check_replay(self, scenario, state, roots):
        self.assertEqual(self.run_path(scenario, tuple(e.action.id for e in state.events)), state)
        retained = replay_selection(self.engine, scenario.spec, state, roots)
        self.assertEqual(tuple(retained.events), tuple(e for e in state.events
                         if e.id in {r.id for r in retained.events}))
        self.assertTrue(set(roots) <= {e.id for e in retained.events})
        self.assertEqual(render(scenario.spec, retained), render(scenario.spec, state,
                         visible={e.id for e in retained.events}))
        return retained

    def answer_and_mask(self, document, kind, focus, event_id, *, contains=(), dependency=None):
        answer = Reader(document).ask(kind, focus, event_id=event_id)
        self.assertTrue(answer.supported, (kind, focus, event_id))
        self.assertIn(event_id, answer.event_ids)
        self.assertIn(f"{event_id}/{kind}/{focus}", answer.statement_ids)
        for text in contains:
            self.assertIn(text, answer.answer)
        for hidden in (f"{event_id}/{kind}/{focus}", dependency):
            if hidden:
                self.assertIn(hidden, answer.statement_ids)
                self.assertFalse(Reader(document.mask([hidden])).ask(kind, focus, event_id=event_id).supported)
        return answer

    def test_p_f1_historical_a1_and_current_a2_receive_only_then_later_authority(self):
        x = receive_only_story()
        before = self.run_path(x, x.path[:x.path.index("receive_only")])
        a1 = before.get("loans", "A1")
        a1_receipt = before.get("receipts", a1.settlement_receipt)
        a2 = before.get("loans", "A2")
        self.assertEqual((a1.status, a1.settlement_receipt), ("discharged", "finish1:1"))
        self.assertEqual((a2.status, a2.settlement_receipt), ("active", None))
        self.assertTrue(before.get("grants", "receive2").active)
        self.assertFalse(before.get("grants", "settle2").active)
        retained_before = self.check_replay(x, before, ["finish1:1", "collect2:1", "receive_ready:1"])
        self.assertEqual(retained_before.get("loans", "A1"), a1)
        self.assertEqual(retained_before.get("loans", "A2"), a2)

        received = self.step(x, before, "receive_only")
        new_receipts = set(received.tables["receipts"]) - set(before.tables["receipts"])
        self.assertEqual(new_receipts, {"receive_only:1"})
        receipt = received.get("receipts", "receive_only:1")
        self.assertEqual((receipt.operation, receipt.loan_id, receipt.source, receipt.destination),
                         ("handoff", "A2", "borrower", "receiver"))
        self.assertEqual(received.get("parents", "prop").parent, "receiver")
        self.assertEqual(received.get("loans", "A1"), a1)
        self.assertEqual(received.get("receipts", a1_receipt.id), a1_receipt)
        self.assertEqual(received.get("loans", "A2"), a2)
        self.reject(x, received, "receive_only")
        self.reject(x, received, "finish1")
        self.reject(x, received, "stale_old_offer")
        retained_received = self.check_replay(x, received, ["finish1:1", "receive_only:1"])
        self.assertEqual(retained_received.get("loans", "A2"), a2)

        after = self.step(x, received, "later_authority")
        self.assertEqual(after.tables["loans"], received.tables["loans"])
        self.assertEqual(after.tables["receipts"], received.tables["receipts"])
        self.assertEqual(after.tables["parents"], received.tables["parents"])
        self.assertTrue(all(matches(after, q) for q in x.spec.goal))
        for op in ("settle_receipt", "settle_loan"):
            self.assertNotIn(op, self.engine.operations)
        retained = self.check_replay(x, after, ["finish1:1", "receive_only:1", "later_authority:1"])
        self.assertEqual(retained.tables, after.tables)
        for state in (before, received, after):
            doc = render(x.spec, state)
            self.answer_and_mask(doc, "loan_status", "A1", "finish1:1", contains=("settled",),
                                 dependency="finish1:1/placement/prop")
        for state in (received, after, retained):
            doc = render(x.spec, state)
            self.answer_and_mask(doc, "placement", "prop", "receive_only:1", contains=("Sol",))
            later_status = Reader(doc).ask("loan_status", "A2", event_id="later_authority:1")
            if later_status.supported:
                self.assertIn("outstanding", later_status.answer)
        self.answer_and_mask(render(x.spec, after), "authority", "settle2", "later_authority:1", contains=("authorized",))

    def test_p_f4_real_stale_claim_delivery_comprehension_adoption_and_atomic_rejection(self):
        for operation in ("return", "lend"):
            with self.subTest(operation=operation):
                x = stale_authority_story(operation=operation)
                grant, attempt = (("settle1", "finish1") if operation == "return" else ("lend2", "collect2"))
                pre = self.run_path(x, x.path[:x.path.index("revoke")])
                self.assertTrue(pre.get("grants", grant).active)
                # Same custody, consent, capacity, and readiness succeed without revocation.
                reporting = x.path[x.path.index("claim_authority"):]
                control = self.step(x, pre, *reporting, attempt)
                self.assertIsNotNone(control.get("receipts", f"{attempt}:1"))
                self.check_replay(x, pre, ["remember_authority:1", "later:1"])
                revoked = self.step(x, pre, "revoke")
                adopted = self.run_path(x)
                self.assertEqual(adopted.get("claims", "authority_claim").speaker, "receiver")
                self.assertEqual(adopted.get("claim_receipts", "authority_receipt").claim, "authority_claim")
                self.assertEqual(adopted.get("comprehensions", "understood").receipt, "authority_receipt")
                self.assertEqual(adopted.get("beliefs", "adopted:belief").proposition, "authority_seen:proposition")
                self.assertFalse(adopted.get("grants", grant).active)
                self.assertEqual(adopted.tables["parents"], revoked.tables["parents"])
                self.assertEqual(adopted.tables["receipts"], revoked.tables["receipts"])
                self.assertEqual(adopted.tables["loans"], revoked.tables["loans"])
                self.reject(x, adopted, attempt)
                self.assertNotIn(f"{attempt}:1", {e.id for e in adopted.events})
                self.assertIsNone(adopted.get("receipts", f"{attempt}:1"))
                self.assertFalse(adopted.get("readiness", "return_ready1" if operation == "return" else "ready2").consumed)
                if operation == "return":
                    self.assertEqual(adopted.get("loans", "A1").status, "active")
                    self.assertEqual(adopted.get("return_offers", "return_offer").status, "accepted")
                else:
                    self.assertIsNone(adopted.get("loans", "A2"))
                    self.assertEqual(adopted.get("loan_offers", "O2").status, "accepted")
                retained = self.check_replay(x, adopted, ["revoke:1", "adopt_authority:1"])
                self.assertFalse(retained.get("grants", grant).active)
                self.assertEqual(retained.get("beliefs", "adopted:belief"), adopted.get("beliefs", "adopted:belief"))
                for state in (adopted, retained):
                    doc = render(x.spec, state)
                    answer = self.answer_and_mask(doc, "claim", "authority_claim", "claim_authority:1",
                                                  contains=("authorized", "time 0"))
                    self.assertEqual(answer.reference_tick, 0)
                    self.answer_and_mask(doc, "receipt", "authority_claim", "hear_authority:1",
                                         dependency="claim_authority:1/claim/authority_claim")
                    self.answer_and_mask(doc, "belief", "borrower_authority", "adopt_authority:1", contains=("accepted", "time 0"))
                    self.answer_and_mask(doc, "authority", grant, "revoke:1", contains=("withdrew authorization",))
                    self.assertFalse(Reader(doc).ask("placement", "prop", event_id=f"{attempt}:1").supported)
                restored = self.step(x, adopted, "restore", attempt)
                self.check_replay(x, restored, ["restore:1", f"{attempt}:1", "adopt_authority:1"])

    def test_s_f3_declined_first_separately_accepted_second_settles_once(self):
        x = two_offer_story()
        before = self.run_path(x, x.path[:x.path.index("decline_first")])
        self.assertEqual(before.get("return_offers", "first_return").status, "pending")
        declined = self.step(x, before, "decline_first")
        refusal = declined.get("refusals", "decline_first:1")
        first = declined.get("return_offers", "first_return")
        self.assertEqual(first.status, "declined")
        self.assertEqual(declined.get("offer_responses", "decline_first:1").offer, "first_return")
        self.assertEqual(declined.get("parents", "prop").parent, "borrower")
        self.assertEqual(declined.get("loans", "A1").status, "active")
        self.reject(x, declined, "decline_first")
        self.reject(x, declined, "late_yes_first")
        self.check_replay(x, declined, ["decline_first:1"])
        accepted = self.step(x, declined, "second_return", "yes2", "return_ready2")
        self.assertEqual(accepted.get("return_offers", "second_return").status, "accepted")
        self.assertEqual(accepted.get("parents", "prop").parent, "borrower")
        self.assertEqual(accepted.get("loans", "A1").status, "active")
        self.assertIsNone(accepted.get("receipts", "finish2:1"))
        self.reject(x, accepted, "finish_declined")
        self.check_replay(x, accepted, ["decline_first:1", "yes2:1", "return_ready2:1"])
        final = self.step(x, accepted, "finish2")
        self.assertEqual(final.get("return_offers", "first_return"), first)
        self.assertEqual(final.get("refusals", refusal.id), refusal)
        self.assertEqual(final.get("offer_responses", "yes2:1").offer, "second_return")
        self.assertEqual(final.get("return_offers", "second_return").status, "completed")
        self.assertEqual(final.get("loans", "A1").settlement_receipt, "finish2:1")
        self.assertEqual([r.id for r in final.tables["receipts"].values() if r.operation == "complete_return"], ["finish2:1"])
        self.assertTrue(all(matches(final, q) for q in x.spec.goal))
        self.reject(x, final, "finish2")
        retained = self.check_replay(x, final, ["decline_first:1", "finish2:1"])
        self.assertEqual(retained.tables, final.tables)

    def test_s_f3_production_reader_exact_offer_ids_responses_reasons_and_masks(self):
        x = two_offer_story()
        final = self.run_path(x)
        retained = self.check_replay(x, final, ["decline_first:1", "finish2:1"])
        for state in (final, retained):
            doc = render(x.spec, state, premise=x.premise, ending=x.ending)
            self.answer_and_mask(doc, "response", "first_return", "decline_first:1", contains=('"No,"',),
                                 dependency="first_return:1/return_offer/first_return")
            self.answer_and_mask(doc, "response", "second_return", "yes2:1", contains=('"Yes,"',),
                                 dependency="second_return:1/return_offer/second_return")
            self.assertFalse(Reader(doc).ask("response", "first_return", event_id="yes2:1").supported)
            self.assertFalse(Reader(doc).ask("response", "second_return", event_id="decline_first:1").supported)
            # Removing the other offer must not erase this offer's answer.
            self.assertTrue(Reader(doc.mask(["first_return:1/return_offer/first_return"]))
                            .ask("response", "second_return", event_id="yes2:1").supported)
            self.assertTrue(Reader(doc.mask(["second_return:1/return_offer/second_return"]))
                            .ask("response", "first_return", event_id="decline_first:1").supported)
            self.answer_and_mask(doc, "why", "first_return", "decline_first:1", contains=("clear a space",),
                                 dependency="first_return:1/return_offer/first_return")
            reader = Reader(doc)
            self.assertTrue(reader.ask("response", "first_return", event_id="decline_first:1").supported)
            self.assertIn("clear a space", reader.follow_up("why").answer)
            self.answer_and_mask(doc, "loan_status", "A1", "finish2:1", contains=("settled",),
                                 dependency="finish2:1/placement/prop")
            qa = Reader(doc).questions()
            for event in ("decline_first:1", "yes2:1", "finish2:1"):
                self.assertTrue(any(event in row.event_ids for row in qa))

    def test_harbor_dry_bench_current_capacity_and_exact_grant_interventions(self):
        x = two_offer_story(harbor=True)
        accepted = self.run_path(x, x.path[:-1])
        baseline = self.step(x, accepted, "finish2")
        self.assertEqual(baseline.get("parents", "prop").parent, "receiver")
        full = self.step(x, accepted, "fill_hands")
        self.reject(x, full, "finish2")
        self.assertFalse(full.get("readiness", "return_ready2").consumed)
        self.assertEqual(full.get("return_offers", "second_return").status, "accepted")
        self.check_replay(x, full, ["decline_first:1", "yes2:1", "return_ready2:1", "fill_hands:1"])
        freed = self.step(x, full, "free_hands", "finish2")
        self.assertIn("free_hands:1", freed.events[-1].causes)
        self.check_replay(x, freed, ["decline_first:1", "finish2:1"])
        revoked = self.step(x, accepted, "revoke")
        self.assertTrue(revoked.get("grants", "settle2").active, "Wrong-loan grant remains available")
        self.reject(x, revoked, "finish2")
        self.assertEqual(revoked.get("parents", "prop").parent, "borrower")
        self.assertEqual(revoked.get("loans", "A1").status, "active")
        self.check_replay(x, revoked, ["decline_first:1", "yes2:1", "return_ready2:1", "revoke:1"])
        restored = self.step(x, revoked, "restore", "finish2")
        retained = self.check_replay(x, restored, ["decline_first:1", "finish2:1"])
        for state in (baseline, freed, restored, retained):
            doc = render(x.spec, state)
            self.answer_and_mask(doc, "location", "prop", "finish2:1", contains=("dry bench",),
                                 dependency="finish2:1/placement/prop")
            self.answer_and_mask(doc, "response", "second_return", "yes2:1",
                                 dependency="second_return:1/return_offer/second_return")

    def test_renderer_gap_receive_only_handoff_preserves_exact_current_debt_qa(self):
        x = receive_only_story()
        state = self.run_path(x)
        doc = render(x.spec, state)
        # Non-vacuous baseline: production already exposes A2 when collected.
        self.answer_and_mask(doc, "loan_status", "A2", "collect2:1", contains=("outstanding",),
                             dependency="collect2:1/placement/prop")
        # A1's old settlement and A2's new handoff must not be conflated.
        self.answer_and_mask(doc, "loan_status", "A2", "receive_only:1", contains=("outstanding",),
                             dependency="receive_only:1/placement/prop")

    def test_renderer_gap_two_offer_questions_and_settlement_name_exact_offer(self):
        x = two_offer_story()
        doc = render(x.spec, self.run_path(x))
        first = Reader(doc).ask("response", "first_return", event_id="decline_first:1")
        second = Reader(doc).ask("response", "second_return", event_id="yes2:1")
        settlement = Reader(doc).ask("loan_status", "A1", event_id="finish2:1")
        self.assertTrue(first.supported and second.supported and settlement.supported)
        # Distinct focus IDs alone do not make identical English questions exact.
        self.assertNotEqual(first.question, second.question)
        self.assertIn("first", first.question.lower())
        self.assertIn("first", first.answer.lower())
        self.assertIn("second", second.question.lower())
        self.assertIn("second", second.answer.lower())
        self.assertIn("second", settlement.answer.lower())

    def test_renderer_gap_settlement_requires_exact_second_offer_and_acceptance(self):
        x = two_offer_story()
        doc = render(x.spec, self.run_path(x))
        self.assertTrue(Reader(doc).ask("loan_status", "A1", event_id="finish2:1").supported)
        for hidden in ("second_return:1/return_offer/second_return", "yes2:1/response/second_return"):
            self.assertFalse(Reader(doc.mask([hidden])).ask("loan_status", "A1", event_id="finish2:1").supported)

    def test_premises_do_not_preperform_the_enacted_checkout_or_return(self):
        for x in (receive_only_story(), two_offer_story(), two_offer_story(harbor=True)):
            self.assertNotIn("borrowed", x.premise)
            self.assertNotIn("brought", x.premise)
        x = stale_authority_story(operation="lend")
        self.assertNotIn("The atlas had not moved", x.ending)


if __name__ == "__main__":
    unittest.main()
