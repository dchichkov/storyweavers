"""Initial worlds are authored premises, not receipt/history checkpoints."""
from copy import deepcopy
from dataclasses import replace
import unittest

from storyscenes.capabilities import epistemic as ep, physical as ph, social as so
from storyscenes.capabilities.api import load_world, registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import (
    Action, CapabilityError, Entity, Query, State, WorldSpec,
    execute, replay, replay_selection,
)


def action(key, operation, actor="ada", *, reason=None, **args):
    return Action(id=key, operation=operation, actor=actor, args=args, reason=reason)


def fixture():
    entities = tuple(Entity(id=key, name=key, kind=kind) for key, kind in (
        ("ada", "actor"), ("bea", "actor"), ("room", "place"),
        ("signal", "object"), ("validity", "object"), ("prop", "object")))
    records = {
        "entities": entities,
        "parents": tuple(ph.Parent(id=e.id, parent="room") for e in entities if e.kind != "place"),
        "propositions": (
            ep.Proposition(id="p", subject="prop", predicate="condition", scope="motor",
                           result=ep.Result(kind="exact", value="working"),
                           reference_start=0, reference_end=0),
            ep.Proposition(id="ink", subject="signal", predicate="inscription", scope="motor",
                           result=ep.Result(kind="exact", value="working"),
                           reference_start=0, reference_end=0),
            ep.Proposition(id="valid", subject="validity", predicate="source_valid", scope="motor",
                           result=ep.Result(kind="exact", value=True),
                           reference_start=0, reference_end=0),
            ep.Proposition(id="wrong", subject="prop", predicate="condition", scope="motor",
                           result=ep.Result(kind="exact", value="jammed"),
                           reference_start=0, reference_end=0),
        ),
        "facts": (ep.Fact(id="f", carrier="signal", proposition="p", live=True),
                  ep.Fact(id="ledger", carrier="signal", proposition="ink", assertion="p"),
                  ep.Fact(id="valid-f", carrier="validity", proposition="valid", live=True)),
        "exposures": (ep.Exposure(id="view", fact="f"),),
        "channels": (ep.Channel(id="eye", kind="observation"),
                     ep.Channel(id="voice", kind="speech")),
        "attention": (ep.Attention(id="focus", actor="ada", source="signal", channel="eye", until=10),),
        "authority_policies": (ep.AuthorityPolicy(id="authority", kind="ledger", fact="ledger",
                              assertion="p", validity_fact="valid-f", valid_from=0, valid_until=10),),
        "belief_policies": (ep.BeliefPolicy(id="authored", kind="authored", modes=("init",)),
                            ep.BeliefPolicy(id="percept", kind="percept"),
                            ep.BeliefPolicy(id="trust", kind="testimony", source="ada"),
                            ep.BeliefPolicy(id="ledger-policy", kind="authority", authority="authority")),
        "beliefs": (ep.Belief(id="prior", actor="ada", proposition="wrong", policy="authored",
                             source_ids=("ada",)),),
        "belief_heads": (ep.BeliefHead(id="head", actor="ada", belief="prior"),),
        "action_specs": (so.ActionSpec(id="job", operation="booking", actor="ada", object="slot",
                                      destination="room", result="booked", terms="reserve", version=1,
                                      checkpoint=2),),
        "booking_slots": (so.BookingSlot(id="slot", place="room"),
                          so.BookingSlot(id="occupied", place="room", booked_by="bea")),
    }
    actions = (
        action("look", "observe", evidence="e", fact="f", exposure="view", channel="eye", attention="focus"),
        action("say", "speak", claim="c", audience="bea", channel="voice", evidence="e"),
        action("hear", "deliver", "bea", claim="c", receipt="r"),
        action("understand", "comprehend", "bea", receipt="r", comprehension="u"),
        action("resolve", "update_belief", disposition="d", mode="resolve", head="head", policy="percept",
               proposition="e:proposition", predecessor="prior", evidence_ids=["e"]),
        action("adopt", "update_belief", "bea", disposition="b", mode="init", head="bea-head",
               policy="trust", proposition="e:proposition", comprehension_ids=["u"]),
        action("assume", "update_belief", "bea", disposition="assumption", mode="init", head="assumption-head",
               policy="authored", proposition="p"),
        action("say-prior", "speak", claim="prior-claim", audience="bea", channel="voice", belief="prior"),
        action("ask", "create_request", "bea", request="req", responder="ada", action_spec="job", version=1),
        action("deliver", "deliver_request", "bea", request="req", version=1),
        action("accept", "respond_request", request="req", version=1, decision="accepted"),
        action("promise", "make_promise", promise="promise", beneficiary="bea", action_spec="job", version=1),
        action("book", "perform_booking", slot="slot", version=1, terms="reserve"),
        action("complete", "complete_request", request="req", version=1, receipt="book:1", table="domain_receipts"),
        action("close", "advance_time", to_tick=3),
        action("assess", "assess_promise", promise="promise", version=1),
        action("decline", "refuse", interaction="request", target="req", version=1,
               reason="I prefer another task.", reason_kind="unwillingness", decision_id="no"),
        action("check", "check_booking", slot="occupied", version=1, terms="inspect"),
        action("pickup", "pickup", object="prop", source="room"),
    )
    return WorldSpec(title="Initial provenance", records=records, actions=actions,
                     goal=(Query(table="clock", key="clock", field="tick", value=3),))


class InitialProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.engine = registry()
        self.spec = fixture()

    def assert_boundary_rejects(self, spec):
        # Prove these are consistent records, not unrelated schema/type negatives.
        tables = {name: {} for name in self.engine.tables}
        tables.update({table: {row.id: row for row in rows} for table, rows in spec.records.items()})
        if not tables["clock"]:
            tables["clock"] = self.engine.initial(self.spec).tables["clock"]
        self.engine.validate(State(tables=tables))
        for boundary in ("python", "json", "public-json", "replay"):
            with self.subTest(boundary=boundary):
                with self.assertRaisesRegex(CapabilityError, "history must start empty"):
                    if boundary == "python":
                        self.engine.initial(spec)
                    elif boundary == "json":
                        loads(self.engine, dumps(spec))
                    elif boundary == "public-json":
                        load_world(dumps(spec))
                    else:
                        replay(self.engine, spec, ())

    def snapshot(self, state):
        return replace(self.spec, records={table: tuple(rows.values())
                                          for table, rows in state.tables.items()})

    def test_static_configuration_wrong_authored_belief_and_booking_occupancy_survive(self):
        engine, spec = load_world(dumps(self.spec))
        self.assertEqual(spec, self.spec)
        initial = engine.initial(spec)
        self.assertEqual(initial.events, ())
        self.assertEqual(initial.get("beliefs", "prior"), self.spec.records["beliefs"][0])
        self.assertEqual(initial.get("booking_slots", "occupied").booked_by, "bea")
        self.assertEqual(initial.get("attention", "focus"), self.spec.records["attention"][0])
        checked = replay(engine, spec, ("check",))
        self.assertEqual(checked.get("domain_receipts", "check:1").result, "occupied")
        self.assertIsNone(execute(engine, spec, checked, next(a for a in spec.actions if a.id == "check")))

    def test_forged_inspection_claim_receipt_comprehension_and_revision_are_rejected(self):
        path = ("look", "say", "hear", "understand", "resolve", "adopt")
        for length in range(1, len(path) + 1):
            with self.subTest(stage=path[length - 1]):
                # Valid enacted rows cannot be laundered into an initial world
                # merely by keeping their event IDs while dropping the events.
                state = replay(self.engine, self.spec, path[:length])
                self.assert_boundary_rejects(self.snapshot(state))

    def test_claim_from_authored_belief_is_still_an_enacted_utterance(self):
        state = replay(self.engine, self.spec, ("say-prior",))
        self.assertFalse(state.tables["evidence"])
        self.assert_boundary_rejects(self.snapshot(state))

    def test_runtime_authored_initialization_is_not_an_initial_assumption_record(self):
        state = replay(self.engine, self.spec, ("assume",))
        self.assertFalse(state.tables["evidence"])
        self.assertFalse(state.tables["claims"])
        self.assert_boundary_rejects(self.snapshot(state))

    def test_each_epistemic_history_table_and_event_belief_has_its_own_initial_guard(self):
        state = replay(self.engine, self.spec, ("look", "say", "hear", "understand", "resolve"))
        for table in ("evidence", "claims", "claim_receipts", "comprehensions", "dispositions", "beliefs"):
            with self.subTest(table=table):
                isolated = self.engine.initial(self.spec)
                isolated.tables[table] = deepcopy(state.tables[table])
                with self.assertRaisesRegex(CapabilityError, "history must start empty"):
                    ep.validate_initial(isolated)

    def test_pending_delivered_accepted_declined_and_completed_requests_are_not_initial(self):
        for path in (("ask",), ("ask", "deliver"), ("ask", "deliver", "accept"),
                     ("ask", "deliver", "decline"), ("ask", "deliver", "accept", "book", "complete")):
            with self.subTest(path=path):
                state = replay(self.engine, self.spec, path)
                spec = replace(self.spec, records={**self.spec.records, "requests": tuple(state.tables["requests"].values())})
                self.assert_boundary_rejects(spec)

    def test_promises_refusals_and_domain_receipts_are_not_static_configuration(self):
        for table, path in (("promises", ("promise",)),
                            ("refusals", ("ask", "deliver", "decline")),
                            ("domain_receipts", ("book",)), ("domain_receipts", ("check",))):
            with self.subTest(table=table, path=path):
                state = replay(self.engine, self.spec, path)
                spec = replace(self.spec, records={**self.spec.records, table: tuple(state.tables[table].values())})
                self.assert_boundary_rejects(spec)

    def test_legitimate_operations_full_replay_and_selected_replay_remain_valid(self):
        path = ("look", "say", "hear", "understand", "resolve", "adopt", "ask", "deliver",
                "accept", "promise", "book", "complete", "close", "assess", "pickup")
        state = self.engine.initial(self.spec)
        actions = {a.id: a for a in self.spec.actions}
        for key in path:
            state = execute(self.engine, self.spec, state, actions[key])
            self.assertIsNotNone(state, key)
        self.engine.validate(state)
        self.assertEqual(replay(self.engine, loads(self.engine, dumps(self.spec)), path), state)
        self.assertEqual(state.get("beliefs", "d:belief").predecessor, "prior")
        self.assertIsNone(state.get("beliefs", "prior").event_id)
        self.assertEqual(state.get("beliefs", "b:belief").source_ids, ("signal",))
        self.assertEqual(state.get("requests", "req").completion_receipt, "book:1")
        self.assertEqual(state.get("promises", "promise").status, "fulfilled")
        retained = replay_selection(self.engine, self.spec, state,
                                    ("adopt:1", "resolve:1", "complete:1", "assess:1"))
        self.assertNotIn("pickup:1", {e.id for e in retained.events})
        for table in ("evidence", "claims", "claim_receipts", "comprehensions", "beliefs",
                      "belief_heads", "dispositions", "requests", "promises", "domain_receipts"):
            self.assertEqual(retained.tables[table], state.tables[table], table)
        # Even a genuine snapshot is not a supported checkpoint-loading format.
        self.assert_boundary_rejects(self.snapshot(state))


if __name__ == "__main__":
    unittest.main()
