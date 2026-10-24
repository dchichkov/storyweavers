"""Offline falsifiers for the social slice, composed with real domain actions."""
from dataclasses import FrozenInstanceError, replace
import unittest

from storyscenes.capabilities import epistemic as ep, physical as ph, social as so
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import (
    Action, CapabilityError, Entity, Query, Registry, WorldSpec, execute,
    fingerprint, replay, replay_selection,
)
from storyscenes.capabilities.reading import Document, Reader, Statement


def action(action_id, op, actor="worker", *, reason=None, reason_support=(), max_uses=1, **args):
    return Action(id=action_id, operation=op, actor=actor, args=args, reason=reason,
                  reason_support=reason_support, max_uses=max_uses)


def terms(id="job", **changes):
    values = dict(id=id, operation="booking", actor="worker", object="slot",
                  destination="room", result="booked", terms="reserve", version=1,
                  checkpoint=2, deadline="inclusive_by")
    values.update(changes)
    return so.ActionSpec(**values)


def request_actions():
    return [action("ask", "create_request", "requester", request="r", responder="worker",
                   action_spec="job", version=1),
            action("deliver", "deliver_request", "requester", request="r", version=1),
            action("accept", "respond_request", request="r", version=1, decision="accepted", max_uses=2)]


def promise_action(id="promise", *, promise="p", action_spec="job", version=1, **kw):
    return action(id, "make_promise", promise=promise, beneficiary="requester",
                  action_spec=action_spec, version=version, **kw)


def booking(id="book", **kw):
    return action(id, "perform_booking", slot=kw.pop("slot", "slot"),
                  version=kw.pop("version", 1), terms=kw.pop("terms", "reserve"), **kw)


def assess(id="assess", **kw):
    return action(id, "assess_promise", promise=kw.pop("promise", "p"),
                  version=kw.pop("version", 1), **kw)


class Harness:
    def __init__(self, actions, *, specs=None, records=None, parent_changes=None):
        self.registry = Registry()
        ph.register(self.registry)
        ep.register(self.registry)
        so.register(self.registry)
        entities = tuple(Entity(id=k, name=k, kind=kind) for k, kind in (
            ("requester", "actor"), ("worker", "actor"), ("other", "actor"),
            ("room", "place"), ("far", "place"), ("prop", "object"), ("otherprop", "object")))
        parents = {e.id: ph.Parent(id=e.id, parent="room") for e in entities if e.kind != "place"}
        for key, value in (parent_changes or {}).items():
            parents[key] = ph.Parent(id=key, parent=value)
        rows = {"entities": entities, "parents": tuple(parents.values()),
                "action_specs": tuple(specs if specs is not None else (terms(),)),
                "booking_slots": (so.BookingSlot(id="slot", place="room"),)}
        rows.update(records or {})
        self.spec = WorldSpec(title="Social falsifiers", records=rows, actions=tuple(actions),
                              goal=(Query(table="clock", key="clock", field="tick", value=3),), max_steps=100)
        self.state = self.registry.initial(self.spec)
        self.actions = {a.id: a for a in actions}

    def run(self, *ids):
        for id in ids:
            after = execute(self.registry, self.spec, self.state, self.actions[id])
            if after is None:
                raise AssertionError(f"Unexpected rejection: {id}")
            self.state = after
        return self.state

    def rejects(self, id):
        before = fingerprint(self.state)
        if execute(self.registry, self.spec, self.state, self.actions[id]) is not None:
            raise AssertionError(f"Unexpected success: {id}")
        if before != fingerprint(self.state):
            raise AssertionError("Rejected candidate changed state/history")


class RequestTests(unittest.TestCase):
    def test_acceptance_acknowledgment_and_performance_are_distinct(self):
        h = Harness(request_actions() + [
            action("ack", "acknowledge_request", request="r", version=1), booking(),
            action("done", "complete_request", request="r", version=1,
                   receipt="book:1", table="domain_receipts")])
        h.run("ask", "deliver", "ack")
        self.assertEqual(h.state.get("requests", "r").response, "pending")
        h.run("accept")
        self.assertEqual(h.state.tables["promises"], {})
        self.assertIsNone(h.state.get("booking_slots", "slot").booked_by)
        self.assertIsNone(h.state.get("requests", "r").completion_receipt)
        h.rejects("accept")
        h.rejects("done")
        h.run("book", "done")
        self.assertEqual(h.state.get("requests", "r").completion_receipt, "book:1")

    def test_undelivered_stale_proxy_and_duplicate_responses_emit_nothing(self):
        h = Harness(request_actions() + [
            action("stale", "respond_request", request="r", version=2, decision="accepted"),
            action("proxy", "respond_request", "other", request="r", version=1, decision="accepted"),
            action("decline", "refuse", interaction="request", target="r", version=1,
                   reason="I prefer another task", reason_kind="unwillingness", max_uses=2)])
        h.run("ask")
        h.rejects("accept")
        h.rejects("decline")
        h.run("deliver")
        h.rejects("stale")
        h.rejects("proxy")
        h.run("decline")
        self.assertEqual(len(h.state.tables["refusals"]), 1)
        h.rejects("decline")
        h.rejects("accept")

    def test_falsifier_one_withdrawal_preserves_acceptance_and_old_promise(self):
        h = Harness(request_actions() + [
            promise_action(request="r"),
            action("decline", "refuse", interaction="request", target="r", version=1,
                   reason="I changed my mind", reason_kind="unwillingness"),
            action("withdraw", "withdraw_request", "requester", request="r", version=1),
            booking(), action("done", "complete_request", request="r", version=1,
                              receipt="book:1", table="domain_receipts"),
            action("clock", "advance_time", to_tick=3), assess()])
        h.run("ask", "deliver", "accept", "promise")
        h.rejects("decline")
        h.run("withdraw")
        req = h.state.get("requests", "r")
        self.assertEqual(req.response, "accepted")
        self.assertEqual(req.response_event, "accept:1")
        self.assertEqual(h.state.get("promises", "p").status, "active")
        h.run("book")  # Independent work remains physically/domain-selectable.
        h.rejects("done")
        h.run("clock", "assess")
        self.assertEqual(h.state.get("promises", "p").status, "fulfilled")

    def test_only_requester_withdraws_and_other_request_is_independent(self):
        actions = request_actions() + [
            action("bad", "withdraw_request", request="r", version=1),
            action("withdraw", "withdraw_request", "requester", request="r", version=1),
            action("ask2", "create_request", "requester", request="r2", responder="worker", action_spec="job", version=1),
            action("deliver2", "deliver_request", "requester", request="r2", version=1),
            action("accept2", "respond_request", request="r2", version=1, decision="accepted")]
        h = Harness(actions)
        h.run("ask", "deliver", "accept")
        h.rejects("bad")
        h.run("withdraw", "ask2", "deliver2", "accept2")
        self.assertIsNone(h.state.get("requests", "r2").withdrawal_event)

    def test_direct_delivery_understanding_and_promise_require_reach(self):
        h = Harness(request_actions() + [promise_action()], parent_changes={"worker": "far"})
        h.run("ask")
        h.rejects("deliver")
        h.rejects("accept")
        h.rejects("promise")
        self.assertIsNone(h.state.get("requests", "r").understood_event)

    def test_receipt_before_acceptance_does_not_complete_request(self):
        h = Harness(request_actions() + [booking(), action("done", "complete_request", request="r", version=1,
                   receipt="book:1", table="domain_receipts")])
        h.run("ask", "deliver", "book", "accept")
        h.rejects("done")


class PromiseTests(unittest.TestCase):
    def test_falsifier_two_strict_and_inclusive_same_tick(self):
        h = Harness([
            promise_action(), promise_action("promise2", promise="p2", action_spec="strict"),
            action("boundary", "advance_time", to_tick=2), booking(), assess(),
            assess("assess2", promise="p2"), action("close", "advance_time", to_tick=3)],
            specs=[terms(), terms("strict", deadline="strict_before")])
        h.run("promise", "promise2", "boundary", "book")
        h.rejects("assess")
        h.rejects("assess2")
        h.run("close", "assess", "assess2")
        self.assertEqual(h.state.get("promises", "p").status, "fulfilled")
        self.assertEqual(h.state.get("promises", "p2").status, "breached")

    def test_same_tick_but_precreation_receipt_cannot_fulfill(self):
        h = Harness([booking(), promise_action(), action("close", "advance_time", to_tick=3), assess()])
        h.run("book", "promise", "close", "assess")
        self.assertEqual(h.state.get("promises", "p").status, "breached")

    def test_same_tick_postcreation_receipt_can_fulfill_and_replay(self):
        h = Harness([promise_action(), booking(), action("close", "advance_time", to_tick=3), assess()])
        h.run("promise", "book", "close", "assess")
        self.assertEqual(h.state.get("promises", "p").status, "fulfilled")
        result = replay_selection(h.registry, h.spec, h.state, ["assess:1"])
        self.assertEqual(result.get("promises", "p"), h.state.get("promises", "p"))
        self.assertEqual(replay(h.registry, h.spec, ["promise", "book", "close", "assess"]), h.state)

    def test_late_repair_does_not_erase_breach(self):
        h = Harness([promise_action(), action("close", "advance_time", to_tick=3), assess(), booking(),
                     action("repair", "record_late_repair", promise="p", version=1,
                            receipt="book:1", table="domain_receipts"),
                     assess("again"), action("release", "release_promise", "requester", promise="p", version=1)])
        h.run("promise", "close", "assess", "book", "repair")
        p = h.state.get("promises", "p")
        self.assertEqual((p.status, p.assessment_event, p.repair_receipt), ("breached", "assess:1", "book:1"))
        h.rejects("again")
        h.run("release")
        self.assertEqual(h.state.get("promises", "p").status, "breached")

    def test_transaction_cannot_rewrite_recorded_breach_as_fulfillment(self):
        h = Harness([promise_action(), action("close", "advance_time", to_tick=3), assess()])

        def counterfeit(tx):
            old = tx.get("promises", "p")
            tx.put("promises", replace(old, status="fulfilled", performance_receipt="invented"))
            tx.emit(kind="counterfeit")

        h.registry.operation("counterfeit", counterfeit, reads={"promises"}, writes={"promises"})
        fake = action("forge", "counterfeit")
        h.spec = replace(h.spec, actions=h.spec.actions + (fake,))
        h.actions["forge"] = fake
        h.run("promise", "close", "assess")
        h.rejects("forge")
        self.assertEqual(h.state.get("promises", "p").status, "breached")

    def test_release_and_new_linked_terms_preserve_original(self):
        h = Harness([promise_action(),
                     action("release", "release_promise", "requester", promise="p", version=1),
                     promise_action("replacement", promise="p2", action_spec="newjob", version=2, replaces="p"),
                     booking("chart", slot="chartslot", version=2, terms="chart"),
                     action("close", "advance_time", to_tick=3), assess(), assess("newassess", promise="p2", version=2)],
                    specs=[terms(), terms("newjob", object="chartslot", version=2, terms="chart")],
                    records={"booking_slots": (so.BookingSlot(id="slot", place="room"),
                                               so.BookingSlot(id="chartslot", place="room", version=2))})
        h.run("promise")
        h.rejects("replacement")
        h.run("release", "replacement", "chart", "close")
        h.rejects("assess")
        h.run("newassess")
        self.assertEqual(h.state.get("promises", "p").status, "released")
        self.assertIsNone(h.state.get("promises", "p").performance_receipt)
        self.assertEqual(h.state.get("promises", "p2").status, "fulfilled")
        self.assertEqual(h.state.get("promises", "p2").replaces, "p")

    def test_release_is_beneficiary_authorized_not_fulfillment(self):
        h = Harness([promise_action(), action("bad", "release_promise", promise="p", version=1),
                     action("release", "release_promise", "requester", promise="p", version=1),
                     action("close", "advance_time", to_tick=3), assess()])
        h.run("promise")
        h.rejects("bad")
        h.run("release", "close")
        h.rejects("assess")
        self.assertEqual(h.state.get("promises", "p").status, "released")

    def test_exact_domain_actor_object_operation_result_terms_version(self):
        variants = [dict(actor="other"), dict(object="other-slot"), dict(operation="inspection", result="available"),
                    dict(result="not-booked"), dict(terms="different"), dict(version=2)]
        for changed in variants:
            with self.subTest(changed=changed):
                spec = terms(**changed)
                h = Harness([promise_action(version=spec.version), booking(),
                             action("close", "advance_time", to_tick=3), assess(version=spec.version, actor=spec.actor)],
                            specs=[spec])
                if spec.actor == "other":
                    h.actions["promise"] = replace(h.actions["promise"], actor="other")
                    h.spec = replace(h.spec, actions=tuple(h.actions.values()))
                h.run("promise", "book", "close", "assess")
                self.assertEqual(h.state.get("promises", "p").status, "breached")

    def test_initial_fabricated_receipt_is_not_execution(self):
        fake = so.DomainReceipt(id="fake", operation="booking", actor="worker", object="slot", destination="room",
                                result="booked", terms="reserve", version=1, event_id="claim:1", tick=0)
        h = Harness([promise_action(), action("close", "advance_time", to_tick=3), assess()])
        forged = replace(h.spec, records={**h.spec.records, "domain_receipts": (fake,)})
        with self.assertRaisesRegex(CapabilityError, "history must start empty"):
            h.registry.initial(forged)
        with self.assertRaisesRegex(CapabilityError, "history must start empty"):
            loads(h.registry, dumps(forged))

        # Deliberate post-initial corruption independently exercises the matcher.
        h.run("promise")
        h.state.tables["domain_receipts"][fake.id] = fake
        self.assertNotIn(fake.event_id, {event.id for event in h.state.events})
        h.run("close", "assess")
        self.assertEqual(h.state.get("promises", "p").status, "breached")
        self.assertIsNone(h.state.get("promises", "p").performance_receipt)

    def test_new_refusal_does_not_cancel_old_breached_promise(self):
        h = Harness([promise_action(), action("close", "advance_time", to_tick=3), assess()] + request_actions() + [
            action("no", "refuse", interaction="request", target="r", version=1,
                   reason="I am doing another task", reason_kind="unwillingness")],
                    specs=[terms(), terms("newjob", checkpoint=5)])
        # The new request must have its own still-open action terms.
        changed = replace(h.actions["ask"], args={**h.actions["ask"].args, "action_spec": "newjob"})
        h.actions["ask"] = changed
        h.spec = replace(h.spec, actions=tuple(h.actions.values()))
        h.run("promise", "close", "assess", "ask", "deliver", "no")
        self.assertEqual(h.state.get("promises", "p").status, "breached")
        self.assertEqual(h.state.get("requests", "r").response, "declined")


class BoundedEventTests(unittest.TestCase):
    def test_rejected_booking_is_not_attempt_but_real_check_is_evidence(self):
        h = Harness([booking(), action("check", "check_booking", slot="slot", version=1, terms="inspect")],
                    records={"booking_slots": (so.BookingSlot(id="slot", place="room", booked_by="other"),)})
        h.rejects("book")
        self.assertEqual(h.state.events, ())
        h.run("check")
        self.assertEqual(h.state.get("domain_receipts", "check:1").result, "occupied")
        self.assertEqual(h.state.events[-1].data["booked_by"], "other")

    def test_booking_and_inspection_are_not_remote_omniscient_checks(self):
        h = Harness([booking(), action("check", "check_booking", slot="slot", version=1, terms="inspect")],
                    parent_changes={"worker": "far"})
        h.rejects("book")
        h.rejects("check")

    def test_reaffirmation_is_separate_bounded_event_with_attributed_reason(self):
        h = Harness(request_actions() + [
            action("no", "refuse", interaction="request", target="r", version=1,
                   decision_id="d", reason="I think the motor is jammed", reason_kind="inability", max_uses=2),
            action("again", "acknowledge_refusal", refusal="d", max_uses=2)])
        h.run("ask", "deliver", "no")
        before = dict(h.state.tables["requests"])
        h.rejects("no")
        h.run("again", "again")
        h.rejects("again")
        self.assertEqual(h.state.tables["requests"], before)
        self.assertEqual(h.state.get("refusals", "d").attributed_reason, "I think the motor is jammed")
        self.assertIn("no:1", h.state.events[-1].causes)

    def test_codec_and_frozen_typed_records(self):
        h = Harness(request_actions() + [promise_action()])
        self.assertEqual(loads(h.registry, dumps(h.spec)), h.spec)
        with self.assertRaises(FrozenInstanceError):
            terms().version = 2
        with self.assertRaises(CapabilityError):
            Harness([], specs=[terms(checkpoint=-1)])


class PhysicalIntegrationTests(unittest.TestCase):
    def test_actual_travel_receipt_fulfills_exact_actor_destination_promise(self):
        h = Harness([promise_action(), action("walk", "travel", route="road"),
                     action("close", "advance_time", to_tick=3), assess()],
                    specs=[terms(operation="travel", object="worker", destination="far", result=None)],
                    records={"routes": (ph.Route(id="road", source="room", destination="far"),)})
        h.run("promise", "walk", "close", "assess")
        self.assertEqual(h.state.get("promises", "p").performance_receipt, "walk:1")
        self.assertEqual(h.state.get("promises", "p").status, "fulfilled")

    def test_withdrawal_does_not_prohibit_independent_physical_action(self):
        h = Harness(request_actions() + [
            promise_action(request="r"), action("withdraw", "withdraw_request", "requester", request="r", version=1),
            action("pickup", "pickup", object="prop", source="room"),
            action("put", "put", object="prop", destination="room"),
            action("done", "complete_request", request="r", version=1, receipt="put:1"),
            action("close", "advance_time", to_tick=3), assess()],
            specs=[terms(operation="put", object="prop", destination="room", result=None)])
        h.run("ask", "deliver", "accept", "promise", "withdraw", "pickup", "put")
        h.rejects("done")
        h.run("close", "assess")
        self.assertEqual(h.state.get("parents", "prop").parent, "room")
        self.assertEqual(h.state.get("promises", "p").status, "fulfilled")

    def test_wrong_physical_object_and_actor_receipts_do_not_fulfill(self):
        for changed in (dict(object="otherprop"), dict(actor="other")):
            with self.subTest(changed=changed):
                spec = terms(operation="pickup", object="prop", destination="worker", result=None)
                spec = replace(spec, **changed)
                prom = promise_action()
                if spec.actor != prom.actor:
                    prom = replace(prom, actor=spec.actor)
                h = Harness([prom, action("pickup", "pickup", object="prop", source="room"),
                             action("close", "advance_time", to_tick=3), assess(actor=spec.actor)], specs=[spec])
                h.run("promise", "pickup", "close", "assess")
                self.assertEqual(h.state.get("promises", "p").status, "breached")

    def loan_harness(self, *, extra_actions=(), specs=None):
        records = {
            "ownership": (ph.Ownership(id="prop", owner="requester"),),
            "loan_terms": (ph.LoanTerms(id="lt", version=1, object="prop", owner="requester", lender="requester",
                borrower="worker", source="room", return_authority="requester", return_recipient="requester",
                return_destination="requester"),),
            "grants": (ph.Grant(id="settle", issuer="requester", grantee="requester", object="prop", right="settle",
                                scope="loan", destination="requester"),)}
        actions = [
            action("offer", "offer_loan", "requester", id="offer", terms="lt", version=1, loan_id="loan"),
            action("understand", "comprehend_loan", offer="offer", version=1),
            action("consent", "respond_loan", offer="offer", version=1),
            action("ready", "readiness", id="ready", giver="requester", object="prop", operation="activate_loan"),
            action("collect", "activate_loan", offer="offer", version=1, readiness_id="ready"),
            action("return1", "offer_return", id="return1", loan_id="loan", object="prop", recipient="requester",
                   destination="requester", version=1),
            action("no", "refuse", "requester", interaction="return_offer", target="return1", version=1,
                   reason="Please wait while I clear a space", reason_kind="unwillingness", max_uses=2),
            action("return2", "offer_return", id="return2", loan_id="loan", object="prop", recipient="requester",
                   destination="requester", version=1),
            action("yes", "respond_return", "requester", offer="return2", version=1),
            action("return-ready", "readiness", "requester", id="return-ready", giver="worker", object="prop", operation="complete_return"),
            action("finish", "complete_return", offer="return2", version=1, readiness_id="return-ready", max_uses=2),
            action("no-loan", "refuse", interaction="loan_offer", target="offer", version=1,
                   reason="I do not want to borrow it", reason_kind="unwillingness"),
        ]
        return Harness(actions + list(extra_actions), records=records, specs=specs)

    def test_exact_loan_receipt_and_version_are_required_without_duplicating_debt(self):
        for expected_loan, expected_version, expected in (("loan", 1, "fulfilled"),
                                                          ("wrong-loan", 1, "breached"),
                                                          ("loan", 2, "breached")):
            with self.subTest(loan=expected_loan, version=expected_version):
                spec = terms(operation="complete_return", object="prop", source="worker",
                             destination="requester", result=None, recipient="requester",
                             loan_id=expected_loan, loan_version=expected_version)
                h = self.loan_harness(specs=[spec], extra_actions=[promise_action(),
                    action("close", "advance_time", to_tick=3), assess()])
                h.run("offer", "understand", "consent", "ready", "collect", "promise")
                self.assertEqual(len(h.state.tables["loans"]), 1)
                self.assertEqual(h.state.get("loans", "loan").status, "active")
                h.run("return2", "yes", "return-ready", "finish", "close", "assess")
                self.assertEqual(h.state.get("promises", "p").status, expected)
                self.assertEqual(h.state.get("loans", "loan").status, "discharged")

    def test_future_loan_activation_can_be_promised_but_consent_is_not_performance(self):
        spec = terms(operation="activate_loan", object="prop", destination="worker", result=None,
                     recipient="worker", loan_id="loan", loan_version=1)
        h = self.loan_harness(specs=[spec], extra_actions=[promise_action(),
                              action("close", "advance_time", to_tick=3), assess()])
        h.run("promise", "offer", "understand", "consent")
        self.assertEqual(h.state.tables["loans"], {})
        self.assertEqual(h.state.get("promises", "p").status, "active")
        h.run("ready", "collect", "close", "assess")
        self.assertEqual(h.state.get("promises", "p").status, "fulfilled")

    def test_optional_loan_link_does_not_create_another_loan_or_settle_it(self):
        spec = terms(operation="complete_return", object="prop", destination="requester", result=None,
                     loan_id="loan", loan_version=1)
        h = self.loan_harness(specs=[spec], extra_actions=[promise_action(loan_id="loan"),
                              action("close", "advance_time", to_tick=3), assess()])
        h.run("offer", "understand", "consent", "ready", "collect")
        before = dict(h.state.tables["loans"])
        h.run("promise", "close", "assess")
        self.assertEqual(h.state.tables["loans"], before)
        self.assertEqual(h.state.get("promises", "p").status, "breached")

    def test_falsifier_three_typed_refused_return_then_separate_settlement(self):
        h = self.loan_harness()
        h.run("offer", "understand", "consent", "ready", "collect", "return1")
        h.run("no")
        self.assertEqual(h.state.get("parents", "prop").parent, "worker")
        self.assertEqual(h.state.get("loans", "loan").status, "active")
        self.assertEqual(h.state.get("return_offers", "return1").status, "declined")
        self.assertEqual(h.state.get("refusals", "no:1").audience, "worker")
        self.assertEqual(h.state.get("offer_responses", "no:1").decision, "declined")
        h.rejects("no")
        h.run("return2", "yes", "return-ready", "finish")
        self.assertEqual(h.state.get("loans", "loan").settlement_receipt, "finish:1")
        self.assertEqual(len([r for r in h.state.tables["receipts"].values() if r.operation == "complete_return"]), 1)
        h.rejects("finish")
        # Reader support is deliberately separate from hidden physical truth.
        doc = Document(title="Returned", statements=(Statement(id="s", text="The second return was completed.",
            kind="settlement", focus="loan", answer="The second offer settled the loan.", event_ids=("finish:1",)),))
        self.assertTrue(Reader(doc).ask("settlement", "loan").supported)
        self.assertFalse(Reader(doc.mask({"s"})).ask("settlement", "loan").supported)

    def test_loan_refusal_is_owned_by_physical_adapter(self):
        h = self.loan_harness()
        h.run("offer", "no-loan")
        self.assertEqual(h.state.get("loan_offers", "offer").status, "declined")
        self.assertEqual(h.state.get("refusals", "no-loan:1").audience, "requester")
        self.assertEqual(h.state.tables["loans"], {})
        self.assertEqual(h.state.get("parents", "prop").parent, "room")
        h.rejects("consent")


class EpistemicPerformanceTests(unittest.TestCase):
    def inspection_harness(self, *, exposed=True, result=None, reference=(0, 0)):
        records = {
            "propositions": (ep.Proposition(id="signal-p", subject="prop", predicate="condition", scope="motor",
                result=result or ep.Result(kind="exact", value="working"), reference_start=0, reference_end=0),),
            "facts": (ep.Fact(id="signal", carrier="prop", proposition="signal-p", domain=("motor",)),),
            "exposures": (ep.Exposure(id="view", fact="signal", exposed=exposed, coverage=("motor",)),),
            "channels": (ep.Channel(id="eyes", kind="observation"),),}
        spec = terms(operation="inspection", object="prop", destination="room", result=None,
                     inspection_fact="signal", result_value="working", reference_start=reference[0],
                     reference_end=reference[1], coverage=("motor",))
        actions = [promise_action(),
            action("attention", "attend", attention="focus", source="prop", channel="eyes", until=2),
            action("observe", "observe", evidence="seen", fact="signal", exposure="view", channel="eyes", attention="focus"),
            action("close", "advance_time", to_tick=3), assess()]
        return Harness(actions, specs=[spec], records=records)

    def test_actual_exact_inspection_fulfills_not_the_promise_itself(self):
        h = self.inspection_harness()
        h.run("promise", "attention", "observe", "close", "assess")
        p = h.state.get("promises", "p")
        self.assertEqual((p.status, p.performance_table, p.performance_receipt), ("fulfilled", "evidence", "seen"))
        self.assertIn("observe:1", h.state.events[-1].causes)

    def test_real_completion_claim_cannot_substitute_for_postcreation_performance(self):
        h = self.inspection_harness()
        claim = action("claim", "speak", claim="reported", audience="requester", channel="speech", evidence="seen")
        records = {**h.spec.records, "channels": h.spec.records["channels"] + (ep.Channel(id="speech", kind="speech"),)}
        h.spec = replace(h.spec, records=records, actions=h.spec.actions + (claim,))
        h.actions["claim"] = claim
        h.state = h.registry.initial(h.spec)
        h.run("attention", "observe", "promise", "claim", "close", "assess")
        self.assertIsNotNone(h.state.get("claims", "reported"))
        self.assertEqual(h.state.get("promises", "p").status, "breached")

    def test_unknown_partial_old_and_unperformed_inspections_do_not_fulfill(self):
        cases = [dict(exposed=False), dict(result=ep.Result(kind="partial", alternatives=("working", "jammed"))),
                 dict(reference=(1, 1)), {}]
        for index, kwargs in enumerate(cases):
            with self.subTest(kwargs=kwargs):
                h = self.inspection_harness(**kwargs)
                h.run("promise")
                if index != 3:
                    h.run("attention", "observe")
                h.run("close", "assess")
                self.assertEqual(h.state.get("promises", "p").status, "breached")


if __name__ == "__main__":
    unittest.main()
