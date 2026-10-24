"""Slice 1 conformance, including physical review falsifiers P-F1 through P-F5."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import unittest

from capabilities.codec import dumps, loads
from capabilities.core import (Action, CapabilityError, Entity, Query, Registry,
                               Transaction, WorldSpec, execute, replay,
                               replay_selection, select_events)
from capabilities.physical import (Container, Grant, LoanOffer, LoanTerms, Ownership, Parent,
                                   PhysicalReceipt, Route, accessible, holder,
                                   location, path, register, respond_loan,
                                   respond_return, validate_initial)


def action(action_id, operation_name, actor="borrower", **args):
    return Action(id=action_id, operation=operation_name, actor=actor, args=args, max_uses=2)


def fixture(*, extra=(), records=None, latch=False, source="box", borrower_capacity=10,
            receiver_capacity=10, collection_before=20):
    registry = Registry()
    register(registry)
    actors = tuple(Entity(id=n, name=n.title(), kind="actor",
                          capacity=borrower_capacity if n == "borrower" else
                          receiver_capacity if n == "receiver" else 10)
                   for n in ("owner", "lender", "borrower", "receiver", "stranger"))
    data = {
        "entities": actors + (
            Entity(id="bench", name="Bench", kind="place"),
            Entity(id="annex", name="Annex", kind="place"),
            Entity(id="box", name="Cabinet", kind="container", capacity=10),
            Entity(id="bag", name="Tote", kind="container", capacity=5),
            Entity(id="prop", name="Detector", kind="object"),
            Entity(id="stone", name="Stone", kind="object"),
            Entity(id="spare", name="Personal detector", kind="object")),
        "parents": tuple(Parent(id=a.id, parent="bench") for a in actors) + (
            Parent(id="box", parent="bench"), Parent(id="bag", parent="bench"),
            Parent(id="prop", parent=source), Parent(id="stone", parent="bench"),
            Parent(id="spare", parent="bench")),
        "ownership": (Ownership(id="prop", owner="owner"),),
        "containers": (Container(id="box", latchable=latch), Container(id="bag")),
        "routes": (Route(id="out", source="bench", destination="annex", max_load=2),
                   Route(id="back", source="annex", destination="bench", max_load=2)),
        "loan_terms": (LoanTerms(id="terms", version=1, object="prop", owner="owner",
                        lender="lender", borrower="borrower", source=source,
                        return_authority="owner", return_recipient="receiver",
                        return_destination="box" if latch else "receiver",
                        require_latch=latch, collection_before=collection_before),),
        "grants": (
            Grant(id="lend", issuer="owner", grantee="lender", object="prop", right="lend",
                  scope="terms", destination="borrower"),
            Grant(id="release", issuer="owner", grantee="lender", object="prop", right="release",
                  scope="terms", destination=source),
            Grant(id="settle", issuer="owner", grantee="receiver", object="prop", right="settle",
                  scope="loan1", destination="receiver"),
            Grant(id="deposit", issuer="owner", grantee="borrower", object="prop", right="deposit",
                  scope="loan1", destination="box", active=False)),
    }
    if records:
        data.update(records)
    actions = (
        action("offer", "offer_loan", "lender", id="offer1", terms="terms", version=1, loan_id="loan1"),
        action("understand", "comprehend_loan", offer="offer1", version=1),
        action("accept", "respond_loan", offer="offer1", version=1),
        action("decline", "respond_loan", offer="offer1", version=1, decision="declined"),
        action("ready", "readiness", id="ready1", giver="lender", object="prop", operation="activate_loan"),
        action("collect", "activate_loan", offer="offer1", version=1, readiness_id="ready1"),
        action("take_stone", "pickup", object="stone", source="bench"),
        action("fill_receiver", "pickup", "receiver", object="stone", source="bench"),
        action("take_bag", "pickup", object="bag", source="bench"),
        action("bag_prop", "put", object="prop", destination="bag"),
        action("bench_bag", "put", object="bag", destination="bench"),
        action("shelve", "put", object="prop", destination="box"),
        action("out", "travel", route="out"), action("back", "travel", route="back"),
        action("revoke", "set_grant", "owner", grant="lend", active=False),
        action("revoke_release", "set_grant", "owner", grant="release", active=False),
        action("revoke_settle", "set_grant", "owner", grant="settle", active=False),
        action("enable_deposit", "set_grant", "owner", grant="deposit", active=True),
        action("return_offer", "offer_return", id="return1", loan_id="loan1", object="prop",
               recipient="receiver", destination="receiver", version=1),
        action("return_accept", "respond_return", "receiver", offer="return1", version=1),
        action("return_decline", "respond_return", "receiver", offer="return1", version=1, decision="declined"),
        action("return_ready", "readiness", "receiver", id="return_ready1", giver="borrower",
               object="prop", operation="complete_return"),
        action("return_complete", "complete_return", offer="return1", version=1, readiness_id="return_ready1"),
        action("handoff_ready", "readiness", "receiver", id="handoff_ready1", giver="borrower", object="prop"),
        action("handoff", "handoff", object="prop", recipient="receiver", readiness_id="handoff_ready1", loan_id="loan1"),
        action("deposit", "authorized_deposit", object="prop", loan_id="loan1", destination="box"),
        action("close", "set_container", container="box", open=False),
        action("open", "set_container", container="box", open=True),
        action("close_bag", "set_container", container="bag", open=False),
        action("open_bag", "set_container", container="bag", open=True),
        action("time20", "advance_time", to_tick=20),
    ) + tuple(extra)
    spec = WorldSpec(title="Physical conformance", records=data, actions=actions,
                     goal=(Query(table="loans", key="loan1", field="status", value="discharged"),))
    return registry, spec


class PhysicalTests(unittest.TestCase):
    def start(self, **kwargs):
        self.registry, self.spec = fixture(**kwargs)
        self.state = self.registry.initial(self.spec)

    def do(self, *ids):
        by_id = {a.id: a for a in self.spec.actions}
        for id in ids:
            before = deepcopy(self.state)
            after = execute(self.registry, self.spec, self.state, by_id[id])
            self.assertIsNotNone(after, id)
            self.assertEqual(self.state, before, "executor mutated prestate")
            self.state = after
        return self.state

    def reject(self, id):
        before = deepcopy(self.state)
        candidate = next(a for a in self.spec.actions if a.id == id)
        self.assertIsNone(execute(self.registry, self.spec, self.state, candidate), id)
        self.assertEqual(self.state, before, "rejection left partial effects")

    def loan(self):
        self.do("offer", "understand", "accept", "ready", "collect")

    def accepted_return(self):
        self.do("return_offer", "return_accept", "return_ready")

    def tx(self):
        return Transaction(self.registry, self.state, self.spec.actions[0])

    def test_records_keyword_only_frozen_and_json_roundtrip(self):
        self.start()
        self.assertEqual(loads(self.registry, dumps(self.spec)), self.spec)
        with self.assertRaises(TypeError):
            Parent("prop", "box")
        with self.assertRaises(FrozenInstanceError):
            Parent(id="prop", parent="box").parent = "borrower"
        for operation in self.registry.operations:
            self.assertTrue(all(x is not None for x in self.registry.contracts[operation]))

    def test_initial_only_guard_rejects_authored_fake_history(self):
        self.start()
        validate_initial(self.state)
        fake = deepcopy(self.state)
        fake.tables["loan_offers"]["fake"] = LoanOffer(
            id="fake", terms="terms", version=1, loan_id="loan1", event_id="never:1")
        with self.assertRaises(CapabilityError):
            validate_initial(fake)
        spec = replace(self.spec, records={**self.spec.records,
                       "loan_offers": (fake.tables["loan_offers"]["fake"],)})
        with self.assertRaises(CapabilityError):
            self.registry.initial(spec)

    def test_p_f2_cabinet_collection_no_imaginary_holder(self):
        self.start()
        self.assertIsNone(holder(self.tx(), "prop"))
        self.loan()
        self.assertEqual(holder(self.tx(), "prop"), "borrower")
        self.assertEqual(self.state.get("ownership", "prop").owner, "owner")
        loan = self.state.get("loans", "loan1")
        self.assertEqual((loan.status, loan.borrower), ("active", "borrower"))
        receipt = self.state.get("receipts", loan.activation_receipt)
        self.assertEqual((receipt.source, receipt.destination, receipt.actor, receipt.recipient),
                         ("box", "borrower", "borrower", "borrower"))
        self.assertEqual(len(self.state.tables["receipts"]), 1)
        self.reject("collect")

    def test_cabinet_collection_does_not_require_lender_presence(self):
        self.start(extra=(action("lender_leaves", "travel", "lender", route="out"),))
        self.do("offer", "understand", "accept", "ready", "lender_leaves", "collect")
        self.assertEqual(location(self.tx(), "lender"), "annex")
        self.assertEqual(location(self.tx(), "prop"), "bench")
        self.assertEqual(self.state.get("receipts", "collect:1").source, "box")

    def test_actor_source_collection_and_permission_not_teleportation(self):
        self.start(source="lender")
        self.loan()
        self.assertEqual(self.state.get("receipts", "collect:1").source, "lender")
        self.start()
        self.do("offer", "understand", "accept", "ready", "out")
        self.reject("collect")
        self.assertIsNone(self.state.get("loans", "loan1"))

    def test_p_f2_bench_placement_removes_holder_not_debt(self):
        self.start()
        self.loan()
        self.do("take_bag", "bag_prop", "bench_bag")
        tx = self.tx()
        self.assertEqual(path(tx, "prop"), ("prop", "bag", "bench"))
        self.assertEqual(location(tx, "prop"), "bench")
        self.assertIsNone(holder(tx, "prop"))
        self.assertEqual(self.state.get("loans", "loan1").borrower, "borrower")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")
        self.assertTrue({("parents", "prop"), ("parents", "bag"), ("entities", "bench")} <= tx.reads)

    def test_consent_comprehension_and_readiness_are_distinct(self):
        self.start()
        self.do("offer")
        self.reject("accept")
        self.do("understand", "accept")
        self.assertIsNone(self.state.get("loans", "loan1"))
        self.assertEqual(self.state.tables["receipts"], {})
        self.assertEqual(self.state.get("parents", "prop").parent, "box")
        self.reject("collect")
        self.reject("decline")
        self.do("ready", "collect")

    def test_version_bound_declines_have_one_writer_and_no_movement(self):
        self.start(extra=(action("stale", "respond_loan", offer="offer1", version=2, decision="declined"),))
        self.do("offer")
        self.reject("stale")
        self.do("decline")
        self.assertEqual(self.state.get("loan_offers", "offer1").status, "declined")
        self.assertEqual(len(self.state.tables["offer_responses"]), 1)
        self.assertEqual(self.state.tables["receipts"], {})
        self.reject("decline")
        self.reject("accept")

    def test_p_f3_capacity_changes_after_loan_consent(self):
        self.start(borrower_capacity=1)
        self.do("offer", "understand", "accept", "ready", "take_stone")
        self.reject("collect")
        self.assertFalse(self.state.get("readiness", "ready1").consumed)
        self.assertEqual(self.state.get("loan_offers", "offer1").status, "accepted")
        self.assertIsNone(self.state.get("loans", "loan1"))
        self.assertEqual(len(self.state.tables["receipts"]), 1)

    def test_p_f3_current_lending_and_release_grants_rechecked(self):
        for revoke in ("revoke", "revoke_release"):
            with self.subTest(revoke=revoke):
                self.start()
                self.do("offer", "understand", "accept", "ready", revoke)
                self.reject("collect")
                self.assertFalse(self.state.get("readiness", "ready1").consumed)
                self.assertEqual(self.state.tables["receipts"], {})

    def test_collection_window_start_inclusive_end_exclusive_no_debt(self):
        self.start()
        self.do("offer", "understand", "accept", "ready", "time20")
        self.reject("collect")
        self.assertIsNone(self.state.get("loans", "loan1"))
        self.assertEqual(self.state.tables["receipts"], {})
        self.assertEqual(self.state.get("loan_offers", "offer1").status, "accepted")
        self.start(collection_before=21)
        self.do("offer", "understand", "accept", "ready", "time20", "collect")
        self.assertEqual(self.state.get("receipts", "collect:1").tick, 20)

    def test_g1_decline_then_new_offer_immediate_settlement(self):
        self.start(extra=(
            action("return2", "offer_return", id="return2", loan_id="loan1", object="prop",
                   recipient="receiver", destination="receiver", version=1),
            action("accept2", "respond_return", "receiver", offer="return2", version=1),
            action("complete2", "complete_return", offer="return2", version=1, readiness_id="return_ready1")))
        self.loan()
        self.do("return_offer", "return_decline")
        self.assertEqual(self.state.get("parents", "prop").parent, "borrower")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")
        self.reject("return_decline")
        self.reject("return_accept")
        self.do("return2", "accept2")
        self.reject("complete2")
        self.do("return_ready", "complete2")
        self.assertEqual(self.state.get("loans", "loan1").status, "discharged")
        self.assertEqual(self.state.get("parents", "prop").parent, "receiver")
        self.assertEqual(self.state.get("ownership", "prop").owner, "owner")
        self.assertEqual(self.state.get("return_offers", "return1").status, "declined")
        self.assertEqual(len(self.state.tables["receipts"]), 2)
        self.reject("complete2")

    def test_p_f3_readiness_does_not_reserve_recipient_capacity(self):
        self.start(receiver_capacity=1)
        self.loan()
        self.accepted_return()
        self.do("fill_receiver")
        self.reject("return_complete")
        self.assertFalse(self.state.get("readiness", "return_ready1").consumed)
        self.assertEqual(self.state.get("return_offers", "return1").status, "accepted")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")

    def test_freeing_recipient_capacity_is_retained_for_replay(self):
        _, original = fixture()
        parents = tuple(replace(p, parent="receiver") if p.id == "stone" else p
                        for p in original.records["parents"])
        self.start(receiver_capacity=1, records={"parents": parents}, extra=(
            action("free_hands", "put", "receiver", object="stone", destination="bench"),))
        self.loan()
        self.accepted_return()
        self.reject("return_complete")
        self.do("free_hands", "return_complete")
        self.assertIn("free_hands:1", self.state.events[-1].causes)
        self.assertIn(("parents", "*"), self.state.events[-1].reads)
        replayed = replay_selection(self.registry, self.spec, self.state, ("return_complete:1",))
        self.assertEqual(replayed.tables, self.state.tables)

    def test_current_return_authority_rechecked(self):
        self.start()
        self.loan()
        self.accepted_return()
        self.do("revoke_settle")
        self.reject("return_complete")
        self.assertEqual(self.state.get("parents", "prop").parent, "borrower")
        self.assertFalse(self.state.get("readiness", "return_ready1").consumed)

    def test_current_custody_source_and_access_rechecked_after_consent(self):
        for changes in (("close",), ("stranger_take",), ("stranger_take", "stranger_put")):
            self.start(extra=(
                action("stranger_take", "pickup", "stranger", object="prop", source="box"),
                action("stranger_put", "put", "stranger", object="prop", destination="bench")))
            self.do("offer", "understand", "accept", "ready", *changes)
            self.reject("collect")
            self.assertFalse(self.state.get("readiness", "ready1").consumed)
            self.assertIsNone(self.state.get("loans", "loan1"))
        self.start()
        self.loan()
        self.accepted_return()
        self.do("shelve")
        self.reject("return_complete")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")

    def second_loan_fixture(self):
        _, original = fixture()
        terms = replace(original.records["loan_terms"][0], id="terms2", lender="receiver", source="receiver")
        grants = original.records["grants"] + (
            Grant(id="lend2", issuer="owner", grantee="receiver", object="prop", right="lend",
                  scope="terms2", destination="borrower"),
            Grant(id="release2", issuer="owner", grantee="receiver", object="prop", right="release",
                  scope="terms2", destination="receiver"),)
        self.start(records={"loan_terms": original.records["loan_terms"] + (terms,), "grants": grants}, extra=(
            action("offer2", "offer_loan", "receiver", id="offer2", terms="terms2", version=1, loan_id="loan2"),
            action("understand2", "comprehend_loan", offer="offer2", version=1),
            action("loan_accept2", "respond_loan", offer="offer2", version=1),
            action("ready2", "readiness", id="ready2", giver="receiver", object="prop", operation="activate_loan"),
            action("collect2", "activate_loan", offer="offer2", version=1, readiness_id="ready2"),
            action("oldloan_offer", "offer_return", id="oldloan_return", loan_id="loan1", object="prop",
                   recipient="receiver", destination="receiver", version=1)))

    def test_one_active_loan_per_object_not_per_agreement(self):
        self.second_loan_fixture()
        self.loan()
        self.do("handoff_ready", "handoff", "offer2", "understand2", "loan_accept2", "ready2")
        self.reject("collect2")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")
        self.assertIsNone(self.state.get("loans", "loan2"))
        self.assertFalse(self.state.get("readiness", "ready2").consumed)

    def test_old_loan_receipt_and_offer_cannot_settle_new_checkout(self):
        self.second_loan_fixture()
        self.loan()
        self.accepted_return()
        self.do("return_complete")
        old_loan = self.state.get("loans", "loan1")
        old_receipt = self.state.get("receipts", old_loan.settlement_receipt)
        self.do("offer2", "understand2", "loan_accept2", "ready2", "collect2")
        self.reject("return_complete")
        self.reject("oldloan_offer")
        self.assertEqual(self.state.get("loans", "loan1"), old_loan)
        self.assertEqual(self.state.get("receipts", old_receipt.id), old_receipt)
        self.assertEqual(self.state.get("loans", "loan2").status, "active")
        self.assertIsNone(self.state.get("loans", "loan2").settlement_receipt)
        self.assertEqual(self.state.get("parents", "prop").parent, "borrower")

    def test_p_f1_receive_only_once_and_delayed_settlement_unsupported(self):
        self.start(extra=(action("later_authority", "set_grant", "owner", grant="settle", active=True),))
        self.loan()
        self.do("revoke_settle", "handoff_ready", "handoff")
        loan = self.state.get("loans", "loan1")
        self.assertEqual(loan.status, "active")
        self.assertIsNone(loan.settlement_receipt)
        self.assertEqual(holder(self.tx(), "prop"), "receiver")
        self.assertEqual(len(self.state.tables["receipts"]), 2)
        self.assertEqual(self.state.get("receipts", "handoff:1").loan_id, "loan1")
        self.reject("handoff")
        before_receipts = deepcopy(self.state.tables["receipts"])
        self.do("later_authority")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")
        self.assertEqual(self.state.tables["receipts"], before_receipts)
        self.assertEqual(self.state.get("parents", "prop").parent, "receiver")
        self.assertNotIn("settle_receipt", self.registry.operations)
        self.assertNotIn("settle_loan", self.registry.operations)

    def test_p_f4_claims_do_not_deliver_or_grant_authority(self):
        self.registry, self.spec = fixture(extra=(action("claim", "claim", text="Delivered and authorized", accepted=True),))
        self.registry.operation("claim", lambda tx, **data: tx.emit(kind="claim", **data), reads=set(), writes=set())
        self.state = self.registry.initial(self.spec)
        self.loan()
        self.do("revoke_settle")
        before_tables = deepcopy(self.state.tables)
        self.do("claim")
        self.assertEqual(self.state.tables, before_tables)
        self.accepted_return()
        self.reject("return_complete")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")
        self.assertEqual(self.state.get("parents", "prop").parent, "borrower")

    def test_p_f5_latched_deposit_and_dependencies_replay(self):
        self.start(latch=True)
        self.loan()
        self.reject("deposit")
        self.do("enable_deposit", "deposit")
        self.assertEqual(self.state.get("parents", "prop").parent, "box")
        self.assertEqual(self.state.get("containers", "box"), Container(id="box", open=False, latchable=True, latched=True))
        self.assertEqual(self.state.get("loans", "loan1").settlement_receipt, "deposit:1")
        self.assertIsNone(self.state.get("receipts", "deposit:1").recipient)
        self.assertIn("enable_deposit:1", self.state.events[-1].causes)
        self.assertIn("collect:1", self.state.events[-1].causes)
        retained = replay_selection(self.registry, self.spec, self.state, ("deposit:1",))
        self.assertEqual(retained.tables, self.state.tables)
        self.assertEqual(replay(self.registry, self.spec, [e.action.id for e in self.state.events]), self.state)
        self.reject("deposit")

    def test_g1_refused_return_then_scoped_authorized_deposit(self):
        self.start(latch=True)
        self.loan()
        self.do("return_offer", "return_decline")
        response = self.state.get("offer_responses", "return_decline:1")
        self.reject("deposit")
        self.do("enable_deposit", "deposit")
        self.assertEqual(self.state.get("offer_responses", "return_decline:1"), response)
        self.assertEqual(self.state.get("return_offers", "return1").status, "declined")
        self.assertEqual(self.state.get("loans", "loan1").status, "discharged")
        self.assertEqual(self.state.get("ownership", "prop").owner, "owner")
        self.assertIsNone(holder(self.tx(), "prop"))
        self.assertEqual(location(self.tx(), "prop"), "bench")
        self.assertEqual(len(self.state.tables["receipts"]), 2)

    def test_time_does_not_discharge_a_collected_loan(self):
        self.start()
        self.loan()
        self.do("time20")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")
        self.assertIsNone(self.state.get("loans", "loan1").settlement_receipt)

    def test_p_f5_missing_latch_rejects_all_effects(self):
        self.start(latch=True, records={"containers": (Container(id="box"), Container(id="bag"))})
        self.loan()
        self.do("enable_deposit")
        self.reject("deposit")
        self.assertEqual(self.state.get("parents", "prop").parent, "borrower")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")
        self.assertEqual(len(self.state.tables["receipts"]), 1)

    def test_generic_put_never_settles_or_latches(self):
        self.start(latch=True)
        self.loan()
        self.do("shelve")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")
        self.assertFalse(self.state.get("containers", "box").latched)
        self.assertTrue(self.state.get("containers", "box").open)

    def test_deposit_capacity_and_exact_grant_reject_atomically(self):
        for grant_change in (dict(scope="loan2"), dict(destination="bag"), dict(grantee="stranger")):
            _, original = fixture(latch=True)
            grants = tuple(replace(g, active=True, **grant_change) if g.id == "deposit" else g
                           for g in original.records["grants"])
            self.start(latch=True, records={"grants": grants})
            self.loan()
            self.reject("deposit")
            self.assertFalse(self.state.get("containers", "box").latched)
        _, original = fixture(latch=True)
        # Capacity is consumed after collection but before attempted deposit.
        entities = tuple(replace(e, capacity=1) if e.id == "box" else e
                         for e in original.records["entities"])
        self.start(latch=True, records={"entities": entities}, extra=(
            action("fill_box", "put", object="stone", destination="box"),))
        self.loan()
        self.do("enable_deposit", "take_stone", "fill_box")
        self.reject("deposit")
        self.assertFalse(self.state.get("containers", "box").latched)
        self.assertEqual(self.state.get("loans", "loan1").status, "active")

    def test_opening_remote_or_nonlatchable_container_rejected(self):
        self.start(extra=(action("latch", "set_container", container="box", open=False, latch=True),))
        self.reject("latch")
        self.do("out")
        self.reject("close")

    def test_loan_identity_wrong_object_target_and_version(self):
        self.start(extra=(
            action("wrongloan", "authorized_deposit", loan_id="loan99", object="prop", destination="box"),
            action("wrongobject", "authorized_deposit", loan_id="loan1", object="spare", destination="box"),
            action("wrongrecipient", "offer_return", id="bad_return", loan_id="loan1", object="prop",
                   recipient="stranger", destination="stranger", version=1),
            action("acceptwrong", "respond_return", "stranger", offer="bad_return", version=1),
            action("completewrong", "complete_return", offer="bad_return", version=1, readiness_id="return_ready1"),
            action("stalereturn", "respond_return", "receiver", offer="return1", version=2),
            action("outsider", "respond_return", "stranger", offer="return1", version=1)))
        self.loan()
        self.do("enable_deposit")
        for id in ("wrongloan", "wrongobject"):
            self.reject(id)
        self.do("wrongrecipient", "acceptwrong")
        self.reject("completewrong")
        self.do("return_offer")
        self.reject("stalereturn")
        self.reject("outsider")
        self.assertEqual(self.state.get("loans", "loan1").status, "active")

    def test_finite_routes_mass_and_exact_travel_receipt(self):
        self.start()
        self.loan()
        self.do("out")
        receipt = self.state.get("receipts", "out:1")
        self.assertEqual((receipt.object, receipt.actor, receipt.source, receipt.destination),
                         ("borrower", "borrower", "bench", "annex"))
        self.assertEqual(location(self.tx(), "prop"), "annex")
        self.reject("out")
        self.do("back", "take_stone", "take_bag")
        self.reject("out")
        self.assertEqual(location(self.tx(), "prop"), "bench")

    def test_route_closed_and_occupied_hands(self):
        for road in (Route(id="out", source="bench", destination="annex", open=False),
                     Route(id="out", source="bench", destination="annex", max_load=0)):
            self.start(records={"routes": (road,)})
            self.do("take_stone")
            self.reject("out")

    def test_closed_contents_move_without_exposure(self):
        self.start(extra=(action("carry_box", "pickup", object="box", source="bench"),))
        self.do("close", "carry_box", "out")
        self.assertEqual(location(self.tx(), "prop"), "annex")
        self.assertFalse(accessible(self.tx(), "borrower", "prop"))
        self.do("open")
        self.assertTrue(accessible(self.tx(), "borrower", "prop"))
        receipt = self.state.get("receipts", "carry_box:1")
        self.assertEqual(receipt.object, "box")
        self.assertEqual(len(self.state.tables["receipts"]), 2)

    def test_set_container_nested_outer_reach_and_explicit_latch(self):
        self.start(latch=True, extra=(
            action("nest", "put", object="box", destination="bag"),
            action("take_box", "pickup", object="box", source="bench"),
            action("latch", "set_container", container="box", open=False, latch=True)))
        self.do("take_box", "nest", "close_bag")
        self.reject("close")
        self.do("open_bag", "latch")
        self.assertTrue(self.state.get("containers", "box").latched)
        self.do("open")
        self.assertFalse(self.state.get("containers", "box").latched)
        self.assertEqual(len(self.state.tables["receipts"]), 2)
        self.reject("open")

    def test_pickup_wrong_source_remote_closed_and_other_holder(self):
        self.start(extra=(
            action("wrongsource", "pickup", object="prop", source="bench"),
            action("take_prop", "pickup", object="prop", source="box"),
            action("steal", "pickup", "stranger", object="prop", source="borrower")))
        self.reject("wrongsource")
        self.do("close")
        self.reject("take_prop")
        self.do("open", "out")
        self.reject("take_prop")
        self.do("back", "take_prop")
        self.reject("steal")
        self.assertEqual(self.state.get("ownership", "prop").owner, "owner")
        self.assertEqual(self.state.tables["loans"], {})

    def test_cycles_actor_parent_and_recursive_load_invariants(self):
        self.start(extra=(
            action("take_box", "pickup", object="box", source="bench"),
            action("nest", "put", object="box", destination="bag"),
            action("cycle", "put", object="bag", destination="box")))
        self.do("take_bag", "take_box", "nest")
        self.reject("cycle")
        invalids = (
            {"parents": tuple(replace(p, parent="box") if p.id == "borrower" else p
                              for p in self.spec.records["parents"])},
            {"entities": tuple(replace(e, capacity=0) if e.id == "box" else e
                               for e in self.spec.records["entities"])},
        )
        for records in invalids:
            registry, spec = fixture(records=records)
            with self.assertRaises(CapabilityError):
                registry.initial(spec)

    def test_readiness_bound_to_giver_object_recipient_operation(self):
        for args in (
            dict(giver="stranger", object="prop", operation="activate_loan"),
            dict(giver="lender", object="spare", operation="activate_loan"),
            dict(giver="lender", object="prop", operation="handoff"),
        ):
            self.start(extra=(action("badready", "readiness", id="ready1", **args),))
            self.do("offer", "understand", "accept", "badready")
            self.reject("collect")
        self.start(extra=(action("badready", "readiness", "stranger", id="ready1", giver="lender",
                                 object="prop", operation="activate_loan"),))
        self.do("offer", "understand", "accept", "badready")
        self.reject("collect")

    def test_grants_exact_scope_object_destination_and_original_issuer(self):
        for changes in (dict(scope="otherterms"), dict(destination="receiver"),
                        dict(grantee="stranger"), dict(right="receive"), dict(active=False)):
            _, original = fixture()
            grants = tuple(replace(g, **changes) if g.id == "lend" else g
                           for g in original.records["grants"])
            self.start(records={"grants": grants})
            self.reject("offer")
        _, original = fixture()
        forged = tuple(replace(g, issuer="stranger") if g.id == "lend" else g
                       for g in original.records["grants"])
        registry, spec = fixture(records={"grants": forged})
        with self.assertRaises(CapabilityError):
            registry.initial(spec)
        self.start(extra=(action("delegate", "set_grant", "lender", grant="deposit", active=True),))
        self.reject("delegate")

    def test_committed_receipts_are_immutable(self):
        self.registry, self.spec = fixture(extra=(action("forge", "forge"),))
        def forge(tx):
            row = tx.get("receipts", "collect:1")
            tx.put("receipts", replace(row, destination="stranger"))
        self.registry.operation("forge", forge, reads={"receipts"}, writes={"receipts"})
        self.state = self.registry.initial(self.spec)
        self.loan()
        self.reject("forge")

    def test_refuse_adapter_dispatches_owner_helper_without_double_writer(self):
        self.registry, self.spec = fixture(extra=(action("refuse_adapter", "refuse_adapter"),))
        def adapter(tx):
            respond_loan(tx, offer="offer1", version=1, decision="declined")
        self.registry.operation("refuse_adapter", adapter, reads=set(self.registry.tables),
                                writes={"loan_offers", "offer_responses"})
        self.state = self.registry.initial(self.spec)
        self.do("offer", "refuse_adapter")
        self.assertEqual(self.state.get("loan_offers", "offer1").status, "declined")
        self.reject("refuse_adapter")

    def test_path_and_authority_dependencies_survive_selection(self):
        self.start(latch=True)
        self.do("close", "open")
        self.loan()
        self.do("enable_deposit", "deposit")
        selected = select_events(self.state, ("deposit:1",))
        self.assertIn("open:1", {e.id for e in selected})
        self.assertIn("accept:1", {e.id for e in selected})
        replayed = replay_selection(self.registry, self.spec, self.state, ("deposit:1",))
        self.assertEqual(replayed.tables, self.state.tables)


if __name__ == "__main__":
    unittest.main()
