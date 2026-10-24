"""Slice 2 semantic falsifiers; prose masking belongs to coordinator integration."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
import unittest

from storyscenes.capabilities import epistemic as ep
from storyscenes.capabilities import physical as ph
from storyscenes.capabilities.core import (
    Action, CapabilityError, Clock, Entity, Query, Record, Registry, WorldSpec,
    execute, proposals, replay, replay_selection,
)


def proposition(id="p", value="clear", *, subject="token", predicate="condition",
                start=0, end=None, scope="sector", result=None):
    return ep.Proposition(id=id, subject=subject, predicate=predicate, scope=scope,
                          reference_start=start, reference_end=start if end is None else end,
                          result=result or ep.Result(kind="exact", value=value))


def action(id, operation, actor="a", *, max_uses=1, **args):
    return Action(id=id, operation=operation, actor=actor, args=args, max_uses=max_uses)


def advance(tx, *, tick):
    tx.require(type(tick) is int and tx.tick < tick <= 200, "Forward finite time only")
    tx.put("clock", Clock(id="clock", tick=tick))
    tx.emit(kind="test_clock", tick=tick)


def set_exposure(tx, *, exposure, exposed):
    tx.put("exposures", replace(tx.get("exposures", exposure), exposed=exposed))


def set_container(tx, *, open):
    tx.put("containers", replace(tx.get("containers", "box"), open=open))


class EpistemicTests(unittest.TestCase):
    def registry(self):
        registry = Registry()
        ph.register(registry)
        ep.register(registry)
        registry.operation("test_advance", advance, reads=set(), writes={"clock"})
        registry.operation("test_exposure", set_exposure, reads={"exposures"}, writes={"exposures"})
        registry.operation("test_container", set_container, reads={"containers"}, writes={"containers"})
        return registry

    def records(self):
        entities = tuple(Entity(id=id, name=id, kind=kind) for id, kind in (
            ("a", "actor"), ("b", "actor"), ("c", "actor"),
            ("room", "place"), ("elsewhere", "place"), ("box", "container"),
            ("token", "object"), ("signal", "object"), ("validity", "object")))
        return {
            "entities": entities,
            "parents": tuple(ph.Parent(id=e.id, parent="room") for e in entities if e.kind != "place"),
            "containers": (ph.Container(id="box"),),
            "ownership": (ph.Ownership(id="token", owner="a"), ph.Ownership(id="box", owner="a")),
            "routes": (ph.Route(id="out", source="room", destination="elsewhere"),
                       ph.Route(id="back", source="elsewhere", destination="room")),
            "propositions": (proposition(),),
            "facts": (ep.Fact(id="f", carrier="signal", proposition="p", live=True),),
            "exposures": (ep.Exposure(id="view", fact="f"),),
            "channels": (ep.Channel(id="eye", kind="observation"),
                         ep.Channel(id="voice", kind="speech"),
                         ep.Channel(id="post", kind="delayed", delay=2)),
            "attention": (ep.Attention(id="focus", actor="a", source="signal", channel="eye", until=100),),
            "belief_policies": (ep.BeliefPolicy(id="percept", kind="percept"),
                                ep.BeliefPolicy(id="trust-a", kind="testimony", source="a"),
                                ep.BeliefPolicy(id="authored", kind="authored", modes=("init",)),
                                ep.BeliefPolicy(id="defer", kind="defer", modes=("defer", "reject"))),
        }

    def spec(self, actions=(), records=None):
        return WorldSpec(title="Epistemic conformance", records=records or self.records(),
                         actions=tuple(actions), goal=(Query(table="entities", key="a", value="a"),))

    def run_actions(self, registry, spec, ids, state=None):
        state = registry.initial(spec) if state is None else state
        by_id = {a.id: a for a in spec.actions}
        for id in ids:
            after = execute(registry, spec, state, by_id[id])
            self.assertIsNotNone(after, f"Rejected {id}")
            state = after
        return state

    def inspect(self, id="look", evidence="e", **overrides):
        return action(id, "observe", evidence=evidence, fact="f", exposure="view",
                      channel="eye", attention="focus", **overrides)

    def initial_belief(self, rows, *, actor="a", value="wrong", start=0):
        rows["propositions"] += (proposition("prior-p", value, start=start),)
        rows["beliefs"] = (ep.Belief(id="prior", actor=actor, proposition="prior-p", policy="authored",
                                    source_ids=(actor,)),)
        rows["belief_heads"] = (ep.BeliefHead(id="head", actor=actor, belief="prior"),)

    def test_registration_and_frozen_keyword_only_records(self):
        registry = self.registry()
        for name, cls in ep.TABLES.items():
            self.assertIs(registry.tables[name], cls)
            self.assertTrue(issubclass(cls, Record))
            self.assertTrue(cls.__dataclass_params__.frozen)
            self.assertTrue(all(field.kw_only for field in fields(cls)))
        self.assertEqual({k: registry.operations[k] for k in ep.OPERATIONS}, ep.OPERATIONS)
        writers = [name for name, (_, writes) in registry.contracts.items()
                   if writes and "belief_heads" in writes]
        self.assertEqual(writers, ["update_belief"])
        self.assertIsNot(registry.tables["receipts"], registry.tables["claim_receipts"])
        with self.assertRaises(FrozenInstanceError):
            proposition().scope = "other"

    def test_record_validation_rejects_ambiguous_time_unknown_false_and_bad_policy(self):
        registry = self.registry()
        bad = [proposition(start=None, end=1), proposition(start=3, end=1),
               proposition(result=ep.Result(kind="unknown", value=False, reason="hidden")),
               proposition(result=ep.Result(kind="exact", value=None)),
               proposition(result=ep.Result(kind="partial", alternatives=("crack",)))]
        for p in bad:
            with self.subTest(p=p):
                rows = self.records()
                rows["propositions"] = (p,)
                with self.assertRaises(CapabilityError):
                    registry.initial(self.spec(records=rows))
        rows = self.records()
        rows["belief_policies"] += (ep.BeliefPolicy(id="shortcut", kind="authored", modes=("resolve",)),)
        with self.assertRaises(CapabilityError):
            registry.initial(self.spec(records=rows))

    def test_codec_roundtrip_nested_results_and_all_concrete_record_fields(self):
        from storyscenes.capabilities.codec import dumps, loads
        registry = self.registry()
        spec = self.spec((self.inspect(),))
        self.assertEqual(loads(registry, dumps(spec)), spec)

    def test_attention_then_inspection_has_real_event_time_paths_no_belief(self):
        registry = self.registry()
        rows = self.records()
        rows["attention"] = ()
        actions = (action("attend", "attend", attention="focus", source="signal", channel="eye", until=5),
                   self.inspect())
        spec = self.spec(actions, rows)
        initial = registry.initial(spec)
        self.assertIsNone(execute(registry, spec, initial, actions[1]))
        state = self.run_actions(registry, spec, ("attend", "look"))
        e = state.get("evidence", "e")
        self.assertEqual((e.event_id, e.acquired_at, e.actor_path, e.source_path),
                         ("look:1", 0, ("a", "room"), ("signal", "room")))
        self.assertIn(("parents", "signal"), state.events[-1].reads)
        self.assertIn("attend:1", state.events[-1].causes)
        self.assertFalse(state.tables["beliefs"])

    def test_ef1_evidence_orders_have_one_explicit_resolution_and_immutable_prior(self):
        registry = self.registry()
        rows = self.records()
        self.initial_belief(rows, actor="b")
        rows["attention"] += (ep.Attention(id="b-focus", actor="b", source="signal", channel="eye", until=20),)
        actions = (
            self.inspect(),
            action("say", "speak", claim="correction", audience="b", channel="voice", evidence="e"),
            action("hear", "deliver", "b", claim="correction", receipt="r"),
            action("understand", "comprehend", "b", receipt="r", comprehension="u"),
            action("perceive", "observe", "b", evidence="direct", fact="f", exposure="view", channel="eye", attention="b-focus"),
            action("resolve", "update_belief", "b", disposition="decision", mode="resolve", head="head",
                   policy="percept", proposition="direct:proposition", predecessor="prior",
                   evidence_ids=("direct",), comprehension_ids=("u",), max_uses=2),
        )
        spec = self.spec(actions, rows)
        results = []
        for order in (("look", "say", "hear", "understand", "perceive"),
                      ("perceive", "look", "say", "hear", "understand")):
            before = self.run_actions(registry, spec, order)
            self.assertEqual(before.get("belief_heads", "head").belief, "prior")
            after = self.run_actions(registry, spec, ("resolve",), before)
            self.assertEqual(after.get("beliefs", "prior"), rows["beliefs"][0])
            self.assertEqual(len(after.tables["dispositions"]), 1)
            self.assertEqual(len(after.tables["beliefs"]), 2)
            self.assertIsNone(execute(registry, spec, after, actions[-1]))
            self.assertEqual(after.tables["parents"], before.tables["parents"])
            results.append(after.tables["beliefs"])
        self.assertEqual(*results)

    def test_ef1_unknown_prior_initializes_without_discovery(self):
        registry = self.registry()
        actions = (self.inspect(), action("init", "update_belief", disposition="d", mode="init", head="head",
                                          policy="percept", proposition="e:proposition", evidence_ids=("e",)))
        spec = self.spec(actions)
        state = self.run_actions(registry, spec, ("look", "init"))
        self.assertIsNone(state.get("beliefs", "d:belief").predecessor)
        self.assertEqual(state.get("dispositions", "d").mode, "init")
        self.assertNotIn("mistake", str(state.events[-1].data))

    def test_ef2_wrong_or_old_inscription_is_only_ink_without_narrow_authority(self):
        registry = self.registry()
        for kind in ("ledger", "exposure_identity"):
            for validity, acquired in ((True, 0), (False, 0), (True, 1)):
                with self.subTest(kind=kind, validity=validity, acquired=acquired):
                    rows = self.records()
                    rows["clock"] = (Clock(id="clock", tick=acquired),)
                    rows["propositions"] = (
                        proposition("p", "reserved-for-a", subject="signal", predicate="inscription"),
                        proposition("assertion", "a", predicate="reserved_for"),
                        proposition("valid", validity, subject="validity", predicate="source_valid"),
                    )
                    rows["facts"] = (ep.Fact(id="f", carrier="signal", proposition="p", assertion="assertion"),
                                     ep.Fact(id="valid-f", carrier="validity", proposition="valid", live=True))
                    rows["exposures"] += (ep.Exposure(id="valid-view", fact="valid-f"),)
                    rows["attention"] += (ep.Attention(id="valid-focus", actor="a", source="validity", channel="eye", until=10),)
                    rows["authority_policies"] = (ep.AuthorityPolicy(id="authority", kind=kind, fact="f",
                        assertion="assertion", validity_fact="valid-f", valid_from=0, valid_until=0),)
                    rows["belief_policies"] += (ep.BeliefPolicy(id="narrow", kind="authority", authority="authority"),)
                    actions = (self.inspect(),
                        action("valid-look", "observe", evidence="valid-e", fact="valid-f", exposure="valid-view",
                               channel="eye", attention="valid-focus"),
                        action("ink-not-truth", "update_belief", disposition="bad", mode="init", head="booking",
                               policy="percept", proposition="assertion", evidence_ids=("e",)),
                        action("missing-validity", "update_belief", disposition="bad2", mode="init", head="booking",
                               policy="narrow", proposition="assertion", evidence_ids=("e",)),
                        action("authority", "update_belief", disposition="d", mode="init", head="booking",
                               policy="narrow", proposition="assertion", evidence_ids=("e", "valid-e")))
                    spec = self.spec(actions, rows)
                    state = self.run_actions(registry, spec, ("look", "valid-look"))
                    self.assertEqual(state.get("propositions", "e:proposition").predicate, "inscription")
                    self.assertIsNone(execute(registry, spec, state, actions[2]))
                    self.assertIsNone(execute(registry, spec, state, actions[3]))
                    after = execute(registry, spec, state, actions[4])
                    self.assertEqual(after is not None, validity and acquired == 0)

    def test_ef2_g2_delayed_report_copies_stored_time_not_current_truth(self):
        registry = self.registry()
        rows = self.records()
        rows["parents"] = tuple(replace(p, parent="box") if p.id == "token" else p for p in rows["parents"])
        rows["facts"] = (ep.Fact(id="f", carrier="token", proposition="p", live=True, projection="location"),)
        rows["attention"] = (ep.Attention(id="focus", actor="a", source="token", channel="eye", until=100),)
        self.initial_belief(rows, actor="b", value="room")
        actions = (
            self.inspect(),
            action("write", "speak", claim="old", audience="b", channel="post", evidence="e",
                   attributed_source="unverified clock", attributed_reference_start=99, attributed_reference_end=99),
            action("close", "test_container", open=False),
            action("take-box", "pickup", "c", object="box", source="room"),
            action("move", "travel", "c", route="out"),
            action("time", "test_advance", tick=2),
            action("receive", "deliver", "b", claim="old", receipt="r"),
            action("understand", "comprehend", "b", receipt="r", comprehension="u"),
            action("adopt-old", "update_belief", "b", disposition="dated", mode="adopt", head="head",
                   policy="trust-a", proposition="e:proposition", predecessor="prior", comprehension_ids=("u",)),
        )
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, tuple(a.id for a in actions))
        self.assertEqual(state.get("parents", "token").parent, "box")
        self.assertEqual(state.get("parents", "c").parent, "elsewhere")
        self.assertEqual(state.get("beliefs", "prior"), rows["beliefs"][0])
        p = state.get("propositions", state.get("claims", "old").proposition)
        self.assertEqual((p.result.value, p.reference_start, p.reference_end), ("room", 0, 0))
        self.assertEqual(state.get("claims", "old").attributed_reference_start, 99)
        self.assertEqual(state.get("claim_receipts", "r").received_at, 2)
        self.assertNotIn(("facts", "f"), state.events[-2].reads)
        self.assertEqual(state.get("beliefs", "dated:belief").proposition, "e:proposition")
        self.assertFalse(state.tables["evidence"].keys() - {"e"})

    def test_distinct_reference_times_need_distinct_heads_even_with_same_value(self):
        registry = self.registry()
        actions = (self.inspect(),
            action("init", "update_belief", disposition="d0", mode="init", head="old", policy="percept",
                   proposition="e:proposition", evidence_ids=("e",)),
            action("time", "test_advance", tick=2), self.inspect("again", "e2"),
            action("not-same", "update_belief", disposition="bad", mode="adopt", head="old", policy="percept",
                   proposition="e2:proposition", predecessor="d0:belief", evidence_ids=("e2",)),
            action("new-time", "update_belief", disposition="d2", mode="init", head="current", policy="percept",
                   proposition="e2:proposition", evidence_ids=("e2",)))
        spec = self.spec(actions)
        state = self.run_actions(registry, spec, ("look", "init", "time", "again"))
        self.assertIsNone(execute(registry, spec, state, actions[-2]))
        state = self.run_actions(registry, spec, ("new-time",), state)
        self.assertEqual(state.get("belief_heads", "old").belief, "d0:belief")
        self.assertEqual(state.get("belief_heads", "current").belief, "d2:belief")

    def test_ef3_occluded_failed_partial_inspection_preserves_prior_not_absence(self):
        registry = self.registry()
        for exposed, domain, coverage, expected in (
                (False, (), (), "unknown"),
                (True, ("upper", "lower"), ("upper",), "unknown"),
                (True, (), (), "partial")):
            with self.subTest(exposed=exposed, domain=domain):
                rows = self.records()
                self.initial_belief(rows, value="accepted-diagnosis")
                if expected == "partial":
                    rows["propositions"] = (proposition(result=ep.Result(kind="partial", alternatives=("wet", "crack"))),
                                              rows["propositions"][-1])
                rows["facts"] = (replace(rows["facts"][0], domain=domain),)
                rows["exposures"] = (ep.Exposure(id="view", fact="f", exposed=exposed, coverage=coverage),)
                actions = (action("later", "test_advance", tick=2), self.inspect(),
                    action("bad", "update_belief", disposition="bad", mode="resolve", head="head", policy="percept",
                           proposition="e:proposition", predecessor="prior", evidence_ids=("e",)),
                    action("defer", "update_belief", disposition="deferred", mode="defer", head="head", policy="defer",
                           predecessor="prior", evidence_ids=("e",), max_uses=2))
                spec = self.spec(actions, rows)
                state = self.run_actions(registry, spec, ("later", "look"))
                self.assertEqual(state.get("propositions", "e:proposition").result.kind, expected)
                self.assertIsNone(execute(registry, spec, state, actions[2]))
                after = self.run_actions(registry, spec, ("defer",), state)
                self.assertEqual(after.tables["beliefs"], state.tables["beliefs"])
                self.assertEqual(after.tables["belief_heads"], state.tables["belief_heads"])
                self.assertIsNone(execute(registry, spec, after, actions[-1]))

    def test_ef3_complete_visible_domain_exact_false_and_zero_are_not_unknown(self):
        registry = self.registry()
        for value in (False, 0):
            rows = self.records()
            rows["propositions"] = (proposition(value=value),)
            rows["facts"] = (replace(rows["facts"][0], domain=("upper", "lower")),)
            rows["exposures"] = (ep.Exposure(id="view", fact="f", coverage=("upper", "lower")),)
            actions = (self.inspect(), action("init", "update_belief", disposition="d", mode="init", head="h",
                                              policy="percept", proposition="e:proposition", evidence_ids=("e",)))
            spec = self.spec(actions, rows)
            state = self.run_actions(registry, spec, ("look", "init"))
            result = state.get("propositions", "e:proposition").result
            self.assertEqual(result.kind, "exact")
            self.assertIs(type(result.value), type(value))

    def test_false_zero_result_equality_and_resolution_are_type_sensitive(self):
        self.assertNotEqual(ep.Result(kind="exact", value=False), ep.Result(kind="exact", value=0))
        self.assertNotEqual(ep.Result(kind="exact", value=1), ep.Result(kind="exact", value=1.0))
        self.assertNotEqual(ep.Result(kind="partial", alternatives=(False, "x")),
                            ep.Result(kind="partial", alternatives=(0, "x")))
        registry = self.registry()
        rows = self.records()
        self.initial_belief(rows, value=False)
        rows["propositions"] = (proposition(value=0), rows["propositions"][-1])
        actions = (self.inspect(),
            action("adopt", "update_belief", disposition="bad", mode="adopt", head="head", policy="percept",
                   proposition="e:proposition", predecessor="prior", evidence_ids=("e",)),
            action("resolve", "update_belief", disposition="d", mode="resolve", head="head", policy="percept",
                   proposition="e:proposition", predecessor="prior", evidence_ids=("e",)))
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, ("look",))
        self.assertIsNone(execute(registry, spec, state, actions[1]))
        state = self.run_actions(registry, spec, ("resolve",), state)
        self.assertEqual(state.get("belief_heads", "head").belief, "d:belief")

    def test_ef4_closed_container_motion_does_not_observe_or_fulfill_inspection(self):
        # Requests/promises and their performance adapters are integration-owned.
        registry = self.registry()
        rows = self.records()
        rows["parents"] = tuple(replace(p, parent="box") if p.id == "signal" else p for p in rows["parents"])
        rows["containers"] = (ph.Container(id="box", open=False),)
        actions = (action("take", "pickup", object="box", source="room"),
                   action("walk", "travel", route="out"), self.inspect(),
                   self.inspect("attempt", "failed", attempt=True),
                   action("open", "test_container", open=True), self.inspect("actual", "actual-e"))
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, ("take", "walk"))
        self.assertFalse(state.tables["evidence"])
        self.assertFalse(state.tables["beliefs"])
        self.assertIsNone(execute(registry, spec, state, actions[2]))
        self.assertEqual(len(state.events), 2)
        state = self.run_actions(registry, spec, ("attempt", "open", "actual"), state)
        self.assertEqual(state.get("evidence", "failed").outcome, "inaccessible")
        self.assertEqual(state.get("evidence", "actual-e").source_path, ("signal", "box", "a", "elsewhere"))
        self.assertEqual(state.get("evidence", "actual-e").event_id, "actual:1")
        self.assertFalse(state.tables["beliefs"])
        selected = replay_selection(registry, spec, state, ("actual:1",))
        self.assertNotIn("attempt:1", {e.id for e in selected.events})
        self.assertIn("open:1", {e.id for e in selected.events})

    def test_ef5_repeated_warning_reinspection_one_source_bounded_and_replayable(self):
        registry = self.registry()
        actions = (self.inspect(),
            action("warning", "speak", claim="warning-1", audience="b", channel="voice", evidence="e"),
            action("hear", "deliver", "b", claim="warning-1", receipt="r1"),
            action("understand", "comprehend", "b", receipt="r1", comprehension="u1"),
            action("repeat", "speak", claim="warning-2", audience="b", channel="voice", evidence="e"),
            action("hear-again", "deliver", "b", claim="warning-2", receipt="r2"),
            action("time", "test_advance", tick=1), self.inspect("inspect-again", "e2"),
            action("adopt", "update_belief", "b", disposition="d", mode="init", head="head", policy="trust-a",
                   proposition="e:proposition", comprehension_ids=("u1",), max_uses=2))
        spec = self.spec(actions)
        state = self.run_actions(registry, spec, tuple(a.id for a in actions))
        self.assertEqual(state.get("claims", "warning-1").source_ids, ("signal",))
        self.assertEqual(state.get("claims", "warning-2").source_ids, ("signal",))
        self.assertEqual(state.get("claims", "warning-2").evidence_ids, ("e",))
        self.assertEqual(state.get("evidence", "e2").source_ids, ("signal",))
        self.assertEqual((state.get("evidence", "e").acquired_at, state.get("evidence", "e2").acquired_at), (0, 1))
        self.assertEqual(state.get("beliefs", "d:belief").source_ids, ("signal",))
        self.assertIsNone(execute(registry, spec, state, actions[-1]))
        self.assertIsNone(execute(registry, spec, state, actions[4]))
        self.assertEqual(replay(registry, spec, tuple(a.id for a in actions)).events, state.events)
        retained = replay_selection(registry, spec, state, ("adopt:1", "hear-again:1", "inspect-again:1"))
        self.assertEqual(retained.events, state.events)

    def test_forwarded_report_retains_actual_source_and_parent_not_attribution(self):
        registry = self.registry()
        actions = (self.inspect(),
            action("say", "speak", claim="c1", audience="b", channel="voice", evidence="e"),
            action("hear", "deliver", "b", claim="c1", receipt="r"),
            action("understand", "comprehend", "b", receipt="r", comprehension="u"),
            action("forward", "speak", "b", claim="c2", audience="c", channel="voice", comprehension="u",
                   attributed_source="different and unverified"))
        state = self.run_actions(registry, self.spec(actions), tuple(a.id for a in actions))
        c = state.get("claims", "c2")
        self.assertEqual((c.parents, c.source_ids, c.evidence_ids, c.proposition),
                         (("c1",), ("signal",), ("e",), "e:proposition"))

    def test_receipt_and_comprehension_are_not_adoption_and_unheard_basis_fails(self):
        registry = self.registry()
        rows = self.records()
        self.initial_belief(rows, actor="a", value="honest-but-wrong")
        actions = (action("say", "speak", claim="c", audience="b", channel="voice", belief="prior"),
            action("hear", "deliver", "b", claim="c", receipt="r"),
            action("understand", "comprehend", "b", receipt="r", comprehension="u"),
            action("adopt", "update_belief", "b", disposition="d", mode="init", head="b-head", policy="trust-a",
                   proposition="prior-p", comprehension_ids=("u",)))
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, ("say", "hear"))
        self.assertEqual(len(state.tables["beliefs"]), 1)
        self.assertIsNone(execute(registry, spec, state, actions[-1]))
        state = self.run_actions(registry, spec, ("understand",), state)
        self.assertEqual(len(state.tables["beliefs"]), 1)
        state = self.run_actions(registry, spec, ("adopt",), state)
        self.assertEqual(state.get("beliefs", "d:belief").proposition, "prior-p")

    def test_no_unsupported_revision_no_latest_writer_no_opposite_on_reject(self):
        registry = self.registry()
        rows = self.records()
        self.initial_belief(rows)
        actions = (self.inspect(),
            action("unsupported", "update_belief", disposition="bad", mode="resolve", head="head", policy="percept",
                   proposition="p", predecessor="prior"),
            action("overwrite", "update_belief", disposition="bad2", mode="adopt", head="head", policy="percept",
                   proposition="e:proposition", predecessor="prior", evidence_ids=("e",)),
            action("reject", "update_belief", disposition="r", mode="reject", head="head", policy="defer",
                   predecessor="prior", evidence_ids=("e",)))
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, ("look",))
        before = deepcopy(state)
        for candidate in actions[1:3]:
            self.assertIsNone(execute(registry, spec, state, candidate))
            self.assertEqual(state, before)
        state = self.run_actions(registry, spec, ("reject",), state)
        self.assertEqual(state.tables["beliefs"], before.tables["beliefs"])

    def test_intents_allow_only_own_belief_records_not_hidden_truth_or_other_beliefs(self):
        registry = self.registry()
        rows = self.records()
        self.initial_belief(rows)
        own = Query(table="beliefs", key="prior", field="proposition", value="prior-p")
        good = replace(self.inspect(), intent=(own,))
        state = registry.initial(self.spec((good,), rows))
        self.assertEqual(proposals(self.spec((good,), rows), state, "a"), (good,))
        for q in (Query(table="facts", key="f", field="proposition", value="p"),
                  Query(table="propositions", key="p", field="result", value=ep.Result(kind="exact", value="clear"))):
            with self.assertRaises(CapabilityError):
                registry.initial(self.spec((replace(good, intent=(q,)),), rows))
        with self.assertRaises(CapabilityError):
            registry.initial(self.spec((replace(good, actor="b"),), rows))

    def test_explicit_unknown_prior_initializes_not_resolves(self):
        registry = self.registry()
        rows = self.records()
        self.initial_belief(rows)
        rows["propositions"] = (rows["propositions"][0], proposition(
            "prior-p", start=None, result=ep.Result(kind="unknown", reason="not_yet_observed")))
        actions = (self.inspect(),
            action("not-mistake", "update_belief", disposition="bad", mode="resolve", head="head", policy="percept",
                   proposition="e:proposition", predecessor="prior", evidence_ids=("e",)),
            action("init", "update_belief", disposition="d", mode="init", head="head", policy="percept",
                   proposition="e:proposition", predecessor="prior", evidence_ids=("e",)))
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, ("look",))
        self.assertIsNone(execute(registry, spec, state, actions[1]))
        state = self.run_actions(registry, spec, ("init",), state)
        self.assertEqual(state.get("dispositions", "d").mode, "init")
        self.assertEqual(state.get("beliefs", "d:belief").predecessor, "prior")

    def test_hidden_truth_variations_offer_identical_belief_based_intents(self):
        registry = self.registry()
        options = []
        for hidden_value in ("clear", "cloud"):
            rows = self.records()
            self.initial_belief(rows, value="expected-clear")
            rows["propositions"] = (proposition(value=hidden_value), rows["propositions"][-1])
            candidate = replace(self.inspect(), intent=(
                Query(table="belief_heads", key="head", field="belief", value="prior"),))
            spec = self.spec((candidate,), rows)
            options.append(proposals(spec, registry.initial(spec), "a"))
        self.assertEqual(*options)

    def test_authored_initial_assumption_can_be_wrong_but_cannot_revise(self):
        registry = self.registry()
        rows = self.records()
        rows["propositions"] += (proposition("wrong", "wrong"),)
        actions = (action("assume", "update_belief", disposition="d", mode="init", head="head",
                          policy="authored", proposition="wrong"), self.inspect(),
            action("shortcut", "update_belief", disposition="bad", mode="resolve", head="head", policy="authored",
                   proposition="e:proposition", predecessor="d:belief", evidence_ids=("e",)))
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, ("assume", "look"))
        self.assertEqual(state.get("beliefs", "d:belief").proposition, "wrong")
        self.assertIsNone(execute(registry, spec, state, actions[-1]))

    def test_adoption_adds_new_matching_support_only_once(self):
        registry = self.registry()
        actions = (self.inspect(), self.inspect("second-sample", "e2"),
            action("init", "update_belief", disposition="d", mode="init", head="head", policy="percept",
                   proposition="e:proposition", evidence_ids=("e",)),
            action("adopt", "update_belief", disposition="d2", mode="adopt", head="head", policy="percept",
                   proposition="e2:proposition", predecessor="d:belief", evidence_ids=("e2",)),
            action("duplicate", "update_belief", disposition="d3", mode="adopt", head="head", policy="percept",
                   proposition="e2:proposition", predecessor="d2:belief", evidence_ids=("e2",)))
        spec = self.spec(actions)
        state = self.run_actions(registry, spec, ("look", "second-sample", "init", "adopt"))
        self.assertEqual(state.get("beliefs", "d2:belief").evidence_ids, ("e", "e2"))
        self.assertEqual(state.get("beliefs", "d2:belief").source_ids, ("signal",))
        self.assertIsNone(execute(registry, spec, state, actions[-1]))

    def test_one_belief_slot_per_actor_scope_and_reference_interval(self):
        registry = self.registry()
        actions = (self.inspect(),
            action("init", "update_belief", disposition="d", mode="init", head="head", policy="percept",
                   proposition="e:proposition", evidence_ids=("e",)),
            action("alias", "update_belief", disposition="alias", mode="init", head="new-head", policy="percept",
                   proposition="e:proposition", evidence_ids=("e",)))
        spec = self.spec(actions)
        state = self.run_actions(registry, spec, ("look", "init"))
        self.assertIsNone(execute(registry, spec, state, actions[-1]))

    def test_independent_carriers_of_same_exposure_keep_one_underlying_source(self):
        registry = self.registry()
        rows = self.records()
        rows["facts"] = (replace(rows["facts"][0], source_ids=("token",)),
                         ep.Fact(id="copy", carrier="validity", proposition="p", live=True, source_ids=("token",)))
        rows["exposures"] += (ep.Exposure(id="copy-view", fact="copy"),)
        rows["attention"] += (ep.Attention(id="copy-focus", actor="a", source="validity", channel="eye", until=10),)
        actions = (self.inspect(),
            action("copy-look", "observe", evidence="copy-e", fact="copy", exposure="copy-view", channel="eye", attention="copy-focus"),
            action("init", "update_belief", disposition="d", mode="init", head="head", policy="percept",
                   proposition="e:proposition", evidence_ids=("e", "copy-e")))
        state = self.run_actions(registry, self.spec(actions, rows), tuple(a.id for a in actions))
        self.assertNotEqual(state.get("evidence", "e").source, state.get("evidence", "copy-e").source)
        self.assertEqual(state.get("beliefs", "d:belief").source_ids, ("token",))

    def test_repeated_action_auto_ids_use_finite_budget_without_dummy_world_flags(self):
        registry = self.registry()
        actions = (action("inspect", "observe", fact="f", exposure="view", channel="eye", attention="focus", max_uses=2),
                   action("warning", "speak", audience="b", channel="voice", evidence="inspect:1", max_uses=2))
        spec = self.spec(actions)
        state = self.run_actions(registry, spec, ("inspect", "warning", "warning", "inspect"))
        self.assertEqual(tuple(state.tables["claims"]), ("warning:1", "warning:2"))
        self.assertEqual(tuple(state.tables["evidence"]), ("inspect:1", "inspect:2"))
        self.assertEqual(state.get("claims", "warning:2").source_ids, ("signal",))
        for candidate in actions:
            self.assertIsNone(execute(registry, spec, state, candidate))
        self.assertFalse(state.tables["beliefs"])
        self.assertEqual(replay_selection(registry, spec, state, ("inspect:2", "warning:2")).events, state.events)

    def test_g4_partial_warning_receipts_do_not_certify_internal_safety(self):
        registry = self.registry()
        rows = self.records()
        rows["propositions"] = (
            proposition(result=ep.Result(kind="partial", alternatives=("safe", "unsafe"))),
            proposition("safe", "safe"))
        actions = (self.inspect(),
            action("warning", "speak", claim="warning", audience="b", channel="voice", evidence="e"),
            action("repeat", "speak", claim="repeated", audience="b", channel="voice", evidence="e"),
            action("hear", "deliver", "b", claim="warning", receipt="r"),
            action("hear-repeat", "deliver", "b", claim="repeated", receipt="r2"),
            action("understand", "comprehend", "b", receipt="r", comprehension="u"),
            action("certify", "update_belief", "b", disposition="bad", mode="init", head="safety", policy="trust-a",
                   proposition="safe", comprehension_ids=("u",)))
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, tuple(a.id for a in actions[:-1]))
        self.assertEqual(state.get("evidence", "e").outcome, "partial")
        self.assertEqual(state.tables["parents"], registry.initial(spec).tables["parents"])
        self.assertEqual(len(state.tables["claims"]), 2)
        self.assertEqual(len(state.tables["claim_receipts"]), 2)
        self.assertIsNone(execute(registry, spec, state, actions[-1]))
        self.assertFalse(state.tables["beliefs"])

    def test_inaccessible_channels_instruments_and_failed_delivery_are_atomic(self):
        registry = self.registry()
        for channel in (ep.Channel(id="eye", kind="observation", instrument="validity"),
                        ep.Channel(id="eye", kind="observation", carrier="validity")):
            rows = self.records()
            rows["parents"] = tuple(replace(p, parent="box") if p.id == "validity" else p for p in rows["parents"])
            rows["containers"] = (ph.Container(id="box", open=False),)
            rows["channels"] = (channel,) + rows["channels"][1:]
            candidate = self.inspect()
            spec = self.spec((candidate,), rows)
            state = registry.initial(spec)
            self.assertIsNone(execute(registry, spec, state, candidate))
            self.assertFalse(state.events or state.tables["evidence"])
        actions = (self.inspect(),
                   action("write", "speak", claim="c", audience="b", channel="post", evidence="e"),
                   action("early", "deliver", "b", claim="c", receipt="r"))
        spec = self.spec(actions)
        state = self.run_actions(registry, spec, ("look", "write"))
        self.assertIsNone(execute(registry, spec, state, actions[-1]))
        self.assertFalse(state.tables["claim_receipts"])

    def test_inspection_reads_current_finite_fact_but_speech_never_reads_truth(self):
        registry = self.registry()
        rows = self.records()
        rows["propositions"] += (proposition("new-truth", "cloud"),)

        def change_signal(tx):
            tx.put("facts", replace(tx.get("facts", "f"), proposition="new-truth"))

        registry.operation("test_change", change_signal, reads={"facts"}, writes={"facts"})
        actions = (self.inspect(), action("change", "test_change"), self.inspect("fresh", "fresh-e"),
                   action("report", "speak", claim="old", audience="b", channel="voice", evidence="e"))
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, tuple(a.id for a in actions))
        self.assertEqual(state.get("propositions", "fresh-e:proposition").result.value, "cloud")
        self.assertEqual(state.get("claims", "old").proposition, "e:proposition")
        self.assertEqual(state.get("propositions", "e:proposition").result.value, "clear")
        self.assertFalse({table for table, _ in state.events[-1].reads} & {"facts", "exposures"})

    def test_historical_records_are_immutable_and_cycles_reject_initial_world(self):
        registry = self.registry()

        def tamper(tx):
            tx.put("propositions", replace(tx.get("propositions", "e:proposition"), scope="fabricated"))

        registry.operation("test_tamper", tamper, reads={"propositions"}, writes={"propositions"})
        actions = (self.inspect(), action("tamper", "test_tamper"))
        spec = self.spec(actions)
        state = self.run_actions(registry, spec, ("look",))
        self.assertIsNone(execute(registry, spec, state, actions[-1]))
        self.assertEqual(state.get("propositions", "e:proposition").scope, "sector")
        rows = self.records()
        self.initial_belief(rows)
        rows["beliefs"] += (replace(rows["beliefs"][0], id="other", predecessor="prior"),)
        rows["beliefs"] = (replace(rows["beliefs"][0], predecessor="other"), rows["beliefs"][-1])
        with self.assertRaises(CapabilityError):
            registry.initial(self.spec(records=rows))

    def test_ef4_requested_promised_inspection_needs_actual_accessible_event(self):
        from storyscenes.capabilities import social

        registry = self.registry()
        social.register(registry)
        rows = self.records()
        rows["parents"] = tuple(replace(p, parent="box") if p.id == "signal" else p for p in rows["parents"])
        rows["containers"] = (ph.Container(id="box", open=False),)
        rows["action_specs"] = (social.ActionSpec(id="inspect-terms", operation="inspection", actor="a",
            terms="internal-read", version=1, checkpoint=4, object="signal", destination="room",
            inspection_fact="f", result_value="clear", reference_start=0, reference_end=0),)
        actions = (
            action("request", "create_request", "b", request="req", responder="a", action_spec="inspect-terms", version=1),
            action("deliver-request", "deliver_request", "b", request="req", version=1),
            action("accept", "respond_request", request="req", version=1, decision="accepted"),
            action("promise", "make_promise", promise="undertaking", beneficiary="b", action_spec="inspect-terms", version=1, request="req"),
            self.inspect(), action("open", "test_container", open=True), self.inspect("actual", "e2"),
            action("complete", "complete_request", request="req", version=1, table="evidence", receipt="e2"),
            action("close-interval", "test_advance", tick=5),
            action("assess", "assess_promise", promise="undertaking", version=1))
        spec = self.spec(actions, rows)
        state = self.run_actions(registry, spec, tuple(a.id for a in actions[:4]))
        self.assertFalse(state.tables["evidence"] or state.tables["beliefs"])
        self.assertEqual(state.get("promises", "undertaking").status, "active")
        self.assertIsNone(execute(registry, spec, state, actions[4]))
        self.assertIsNone(execute(registry, spec, state, actions[7]))
        no_inspection = self.run_actions(registry, spec, ("close-interval", "assess"), state)
        self.assertEqual(no_inspection.get("promises", "undertaking").status, "breached")
        with_inspection = self.run_actions(registry, spec, ("open", "actual", "complete", "close-interval", "assess"), state)
        self.assertEqual(with_inspection.get("promises", "undertaking").status, "fulfilled")
        self.assertEqual(with_inspection.get("promises", "undertaking").performance_table, "evidence")
        self.assertEqual(with_inspection.get("requests", "req").completion_receipt, "e2")
        self.assertEqual(with_inspection.get("evidence", "e2").source_path, ("signal", "box", "room"))
        self.assertFalse(with_inspection.tables["beliefs"])


if __name__ == "__main__":
    unittest.main()
