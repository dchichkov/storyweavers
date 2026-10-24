"""Independent frozen H/G4 acceptance using the production registry and reader.

Run from the repository root:
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=storyscenes .venv/bin/python -m unittest test_capability_holdout -v

No custom operations, event/receipt injection, hand-authored Statements, promises,
or repairs are used. Renderer failures are acceptance failures, not expectedFailure.
"""
import unittest

from capabilities import api, realize
from capabilities.core import (
    Action, Entity, Query, WorldSpec, execute, fingerprint, proposals,
    replay, replay_selection, select_events,
)
from capabilities.epistemic import (
    BeliefPolicy, Channel, Exposure, Fact, Proposition, Result,
)
from capabilities.physical import Container, Ownership, Parent
from capabilities.reading import Reader
from capabilities.social import ActionSpec


REQUEST = "certify_internal_seal"
REASON = ("I cannot certify the internal seal safe because I have inspected only "
          "the external indicator, not the internal seal.")
WARNING = "Only the external indicator was checked; the internal seal has not been inspected."
BASELINE = (
    "focus_indicator", "inspect_indicator", "warning", "receive_first", "understand_first",
    "focus_internal", "draft_request", "deliver_request", "decline", "later",
    "warning", "receive_repeat", "understand_repeat",
)
ROOTS = ("understand_first:1", "decline:1", "understand_repeat:1")
FIRST_WARNING = ("warning:1", "receive_first:1", "understand_first:1")
SECOND_WARNING = ("warning:2", "receive_repeat:1", "understand_repeat:1")
PHYSICAL = ("parents", "ownership", "containers", "loans", "receipts")


def act(action_id, operation, actor="a", *, reason=None, support=(), max_uses=1, **args):
    return Action(id=action_id, operation=operation, actor=actor, args=args,
                  reason=reason, reason_support=support, max_uses=max_uses)


def holdout_spec(*, internal_safety="safe"):
    """The indicator is outside the closed instrument; the seal is inside it.

    The partial indicator signal has a complete *visible* domain. Its finite
    alternatives do not originate from reading the inaccessible internal fact.
    """
    records = {
        "entities": (
            Entity(id="a", name="A", kind="actor"),
            Entity(id="b", name="B", kind="actor"),
            Entity(id="bench", name="harbor bench", kind="place"),
            Entity(id="instrument", name="sealed instrument", kind="container"),
            Entity(id="indicator", name="external indicator", kind="object"),
            Entity(id="seal", name="internal seal", kind="object"),
        ),
        "parents": (
            Parent(id="a", parent="bench"), Parent(id="b", parent="bench"),
            Parent(id="instrument", parent="bench"), Parent(id="indicator", parent="bench"),
            Parent(id="seal", parent="instrument"),
        ),
        "containers": (Container(id="instrument", open=False, latchable=True, latched=True),),
        "ownership": (Ownership(id="instrument", owner="b"), Ownership(id="seal", owner="b"),
                      Ownership(id="indicator", owner="b")),
        "propositions": (
            Proposition(id="indicator_signal", subject="seal", predicate="internal safety",
                result=Result(kind="partial", alternatives=("safe", "unsafe")),
                scope="internal certification", reference_start=0, reference_end=0),
            Proposition(id="internal_signal", subject="seal", predicate="internal safety",
                result=Result(kind="exact", value=internal_safety), scope="internal certification",
                reference_start=0, reference_end=0),
        ),
        "facts": (
            Fact(id="indicator_fact", carrier="indicator", proposition="indicator_signal",
                 live=True, domain=("indicator",)),
            Fact(id="internal_fact", carrier="seal", proposition="internal_signal",
                 live=True, domain=("seal",)),
        ),
        "exposures": (
            Exposure(id="indicator_view", fact="indicator_fact", coverage=("indicator",)),
            Exposure(id="seal_view", fact="internal_fact", coverage=("seal",)),
        ),
        "channels": (Channel(id="sight", kind="observation"), Channel(id="speech", kind="speech")),
        "belief_policies": (BeliefPolicy(id="percept", kind="percept"),),
        "action_specs": (ActionSpec(id="certification_terms", operation="inspection", actor="a",
            object="seal", destination="bench", result_value="safe", inspection_fact="internal_fact",
            coverage=("seal",), terms="certify the internal seal safe now", version=1,
            checkpoint=5, deadline="inclusive_by"),),
    }
    actions = (
        act("focus_indicator", "attend", attention="indicator_focus", source="indicator", channel="sight", until=5),
        act("inspect_indicator", "observe", evidence="partial_indicator", fact="indicator_fact",
            exposure="indicator_view", channel="sight", attention="indicator_focus"),
        act("warning", "speak", audience="b", channel="speech", evidence="partial_indicator",
            reason=WARNING, support=("inspect_indicator:1",), max_uses=2),
        act("receive_first", "deliver", "b", claim="warning:1", receipt="first_receipt"),
        act("understand_first", "comprehend", "b", receipt="first_receipt", comprehension="first_understanding"),
        act("focus_internal", "attend", attention="internal_focus", source="seal", channel="sight", until=5),
        act("inspect_internal", "observe", evidence="internal_exam", fact="internal_fact",
            exposure="seal_view", channel="sight", attention="internal_focus"),
        act("draft_request", "create_request", "b", request=REQUEST, responder="a",
            action_spec="certification_terms", version=1),
        act("deliver_request", "deliver_request", "b", request=REQUEST, version=1),
        act("decline", "refuse", interaction="request", target=REQUEST, version=1,
            decision_id="certification_decline", reason_kind="inability", reason=REASON,
            support=("inspect_indicator:1",), max_uses=2),
        act("later", "advance_time", to_tick=1),
        act("receive_repeat", "deliver", "b", claim="warning:2", receipt="repeat_receipt"),
        act("understand_repeat", "comprehend", "b", receipt="repeat_receipt", comprehension="repeat_understanding"),
        # The separate accessible branch follows, never rewriting the baseline.
        act("branch_time", "advance_time", to_tick=2),
        act("open_instrument", "set_container", container="instrument", open=True),
        act("adopt_exact", "update_belief", disposition="fresh_internal_decision", mode="init",
            head="internal_safety", policy="percept", proposition="internal_exam:proposition",
            evidence_ids=("internal_exam",)),
    )
    return WorldSpec(title="Independent holdout H: the unperformed certification", records=records,
        actions=actions, goal=(Query(table="requests", key=REQUEST, field="response", value="declined"),),
        max_steps=40)


class Holdout:
    def __init__(self, *, internal_safety="safe"):
        self.registry = api.registry()
        self.spec = holdout_spec(internal_safety=internal_safety)
        self.initial = self.registry.initial(self.spec)
        self.state = self.initial
        self.actions = {a.id: a for a in self.spec.actions}

    def run(self, *action_ids):
        for key in action_ids:
            after = execute(self.registry, self.spec, self.state, self.actions[key])
            if after is None:
                raise AssertionError(f"Holdout enacted operation rejected: {key}")
            self.state = after
        return self.state

    def baseline(self, *, reply=True, repeat=True):
        for index, key in enumerate(BASELINE):
            if key == "decline" and not reply:
                continue
            if not repeat and (key in {"receive_repeat", "understand_repeat"}
                               or (key == "warning" and index > BASELINE.index("warning"))):
                continue
            self.run(key)
        return self.state

    def reject(self, key):
        before = fingerprint(self.state)
        result = execute(self.registry, self.spec, self.state, self.actions[key])
        if result is not None:
            raise AssertionError(f"Holdout invalid candidate enacted: {key}")
        if fingerprint(self.state) != before:
            raise AssertionError("Rejected candidate changed history/state")

    def document(self, *, visible=None, state=None):
        return realize.render(self.spec, state or self.state, visible=visible)


class HoldoutSemanticsTests(unittest.TestCase):
    def assert_unchanged_physics(self, holdout):
        for table in PHYSICAL:
            self.assertEqual(holdout.initial.tables[table], holdout.state.tables[table], table)
        self.assertEqual(holdout.state.tables["promises"], {})
        self.assertEqual(holdout.state.tables["domain_receipts"], {})
        self.assertEqual(holdout.state.tables["beliefs"], {})
        self.assertEqual(holdout.state.tables["belief_heads"], {})
        self.assertFalse(any(e.action.operation in {"make_promise", "record_late_repair", "complete_request"}
                             for e in holdout.state.events))

    def test_baseline_distinguishes_partial_unknown_and_declined_without_performance(self):
        h = Holdout()
        h.baseline()
        self.assert_unchanged_physics(h)
        self.assertEqual(h.state.get("parents", "instrument").parent, "bench")
        self.assertEqual(h.state.get("parents", "a").parent, "bench")
        self.assertEqual(h.state.get("parents", "seal").parent, "instrument")
        self.assertFalse(h.state.get("containers", "instrument").open)
        self.assertTrue(h.state.get("containers", "instrument").latched)
        evidence = h.state.get("evidence", "partial_indicator")
        partial = h.state.get("propositions", evidence.proposition)
        self.assertEqual(evidence.outcome, "partial")
        self.assertEqual(partial.result.kind, "partial")
        self.assertIsNone(partial.result.value)
        self.assertEqual(partial.result.alternatives, ("safe", "unsafe"))
        self.assertNotEqual(partial.result, Result(kind="exact", value=False))
        self.assertNotEqual(partial.result, Result(kind="unknown", reason="inaccessible"))
        self.assertEqual(evidence.coverage, ("indicator",))
        self.assertEqual(evidence.actor_path, ("a", "bench"))
        self.assertEqual(evidence.source_path, ("indicator", "bench"))
        self.assertEqual(set(h.state.tables["evidence"]), {"partial_indicator"})
        self.assertIsNone(h.state.get("evidence", "internal_exam"))
        req = h.state.get("requests", REQUEST)
        self.assertEqual((req.response, req.response_event), ("declined", "decline:1"))
        self.assertEqual(req.delivery_event, "deliver_request:1")
        self.assertEqual(req.understood_event, "deliver_request:1")
        self.assertIsNone(req.completion_receipt)
        refusal = h.state.get("refusals", "certification_decline")
        self.assertEqual((refusal.interaction, refusal.target, refusal.version), ("request", REQUEST, 1))
        self.assertEqual((refusal.actor, refusal.audience), ("a", "b"))
        self.assertEqual(refusal.attributed_reason, REASON)
        self.assertEqual(refusal.support, ("inspect_indicator:1",))
        self.assertEqual(len(h.state.events), 13)
        self.assertEqual(tuple(e.id for e in h.state.events), (
            "focus_indicator:1", "inspect_indicator:1", *FIRST_WARNING,
            "focus_internal:1", "draft_request:1", "deliver_request:1", "decline:1", "later:1",
            *SECOND_WARNING))
        h.reject("decline")  # Finite budget is not permission for a second initial response.

    def test_both_warnings_have_one_source_and_distinct_receipts_not_corroboration(self):
        h = Holdout()
        h.baseline()
        first, second = (h.state.get("claims", key) for key in ("warning:1", "warning:2"))
        self.assertNotEqual(first.id, second.id)
        self.assertEqual((first.emitted_at, second.emitted_at), (0, 1))
        self.assertEqual(first.proposition, second.proposition)
        self.assertEqual(first.source_ids, ("indicator",))
        self.assertEqual(second.source_ids, first.source_ids)
        self.assertEqual(first.evidence_ids, ("partial_indicator",))
        self.assertEqual(second.evidence_ids, first.evidence_ids)
        self.assertEqual(first.parents, ())
        self.assertEqual(second.parents, ())
        for claim_id, receipt_id, comprehension_id in (
                ("warning:1", "first_receipt", "first_understanding"),
                ("warning:2", "repeat_receipt", "repeat_understanding")):
            receipt = h.state.get("claim_receipts", receipt_id)
            comprehension = h.state.get("comprehensions", comprehension_id)
            self.assertEqual((receipt.claim, receipt.recipient), (claim_id, "b"))
            self.assertEqual((comprehension.receipt, comprehension.actor), (receipt_id, "b"))
        self.assertEqual(h.state.tables["dispositions"], {})
        self.assertEqual(h.state.counts["warning"], 2)
        self.assertEqual(h.actions["warning"].max_uses, 2)
        h.reject("warning")
        self.assertEqual(h.state.counts["warning"], 2)

    def test_rejected_inaccessible_candidate_never_becomes_attempt_reply_or_source(self):
        h = Holdout()
        h.baseline()
        h.reject("inspect_internal")
        self.assertNotIn("inspect_internal", h.state.counts)
        self.assertFalse(any(e.action.id == "inspect_internal" for e in h.state.events))
        self.assertEqual(h.state.get("requests", REQUEST).response_event, "decline:1")
        self.assertNotIn("internal_exam", h.document().story)
        self.assert_unchanged_physics(h)

    def test_root_selection_replays_actual_support_without_unused_attention(self):
        h = Holdout()
        h.baseline()
        h.reject("inspect_internal")
        selected = select_events(h.state, ROOTS)
        self.assertEqual(tuple(e.id for e in selected),
                         tuple(e.id for e in h.state.events if e.id != "focus_internal:1"))
        retained = replay_selection(h.registry, h.spec, h.state, ROOTS)
        self.assertEqual(retained.events, selected)
        self.assertEqual(len(retained.events), 12)
        self.assertEqual(retained.get("requests", REQUEST), h.state.get("requests", REQUEST))
        self.assertEqual(retained.get("refusals", "certification_decline"),
                         h.state.get("refusals", "certification_decline"))
        for key in ("partial_indicator",):
            self.assertEqual(retained.get("evidence", key), h.state.get("evidence", key))
        self.assertEqual(replay(h.registry, h.spec, BASELINE), h.state)
        full_document = h.document(visible={e.id for e in selected})
        retained_document = h.document(state=retained)
        self.assertEqual(full_document, retained_document)
        self.assertEqual(Reader(full_document).questions(), Reader(retained_document).questions())

    def test_remove_reply_keeps_pending_without_inferred_reason_or_target(self):
        baseline, intervention = Holdout(), Holdout()
        baseline.baseline()
        intervention.baseline(reply=False)
        intervention.reject("inspect_internal")
        self.assertEqual(tuple(e for e in baseline.state.events if e.id != "decline:1"), intervention.state.events)
        req = intervention.state.get("requests", REQUEST)
        self.assertEqual(req.response, "pending")
        self.assertIsNone(req.response_event)
        self.assertEqual(intervention.state.tables["refusals"], {})
        doc = intervention.document()
        reader = Reader(doc)
        self.assertFalse(reader.ask("response", REQUEST).supported)
        self.assertFalse(reader.ask("why", REQUEST).supported)
        self.assertFalse(reader.follow_up("response").supported)
        self.assertNotIn("I decline", doc.story)
        self.assertNotIn(REASON, doc.story)
        self.assert_unchanged_physics(intervention)
        retained = replay_selection(intervention.registry, intervention.spec, intervention.state,
                                    ("understand_first:1", "deliver_request:1", "understand_repeat:1"))
        self.assertEqual(retained.get("requests", REQUEST), req)
        self.assertEqual(intervention.document(state=retained), doc)

    def test_suppress_second_warning_removes_only_its_utterance_receipt_and_understanding(self):
        baseline, intervention = Holdout(), Holdout()
        baseline.baseline()
        intervention.baseline(repeat=False)
        self.assertEqual(tuple(e for e in baseline.state.events if e.id not in SECOND_WARNING),
                         intervention.state.events)
        for table in ("evidence", "requests", "refusals", "beliefs", "belief_heads", "dispositions"):
            self.assertEqual(baseline.state.tables[table], intervention.state.tables[table], table)
        self.assertEqual(set(intervention.state.tables["claims"]), {"warning:1"})
        self.assertEqual(set(intervention.state.tables["claim_receipts"]), {"first_receipt"})
        self.assertEqual(set(intervention.state.tables["comprehensions"]), {"first_understanding"})
        self.assertEqual(intervention.state.get("claims", "warning:1").source_ids, ("indicator",))
        removed = {s.id for s in baseline.document().statements if set(s.event_ids) & set(SECOND_WARNING)}
        self.assertEqual(baseline.document().mask(removed), intervention.document())
        self.assertFalse(Reader(intervention.document()).ask("claim", "warning:2").supported)
        self.assert_unchanged_physics(intervention)
        retained = replay_selection(intervention.registry, intervention.spec, intervention.state,
                                    ("understand_first:1", "decline:1"))
        self.assertEqual(retained.get("requests", REQUEST), intervention.state.get("requests", REQUEST))
        self.assertEqual(intervention.document(state=retained), intervention.document())

    def test_hidden_internal_safety_does_not_change_intentional_options_or_baseline(self):
        safe, unsafe = Holdout(internal_safety="safe"), Holdout(internal_safety="unsafe")
        self.assertEqual(proposals(safe.spec, safe.state, "a"), proposals(unsafe.spec, unsafe.state, "a"))
        safe.baseline()
        unsafe.baseline()
        self.assertEqual(proposals(safe.spec, safe.state, "a"), proposals(unsafe.spec, unsafe.state, "a"))
        self.assertEqual(safe.state.events, unsafe.state.events)
        self.assertEqual(safe.document(), unsafe.document())
        safe.reject("inspect_internal")
        unsafe.reject("inspect_internal")

    def test_accessible_exact_branch_preserves_prior_partial_decline_and_requires_explicit_belief(self):
        h = Holdout()
        h.baseline()
        prior_events = h.state.events
        prior_partial = h.state.get("evidence", "partial_indicator")
        prior_decline = h.state.get("refusals", "certification_decline")
        prior_request = h.state.get("requests", REQUEST)
        prior_document = h.document()
        h.reject("inspect_internal")
        h.run("branch_time", "open_instrument", "inspect_internal")
        exact = h.state.get("evidence", "internal_exam")
        prop = h.state.get("propositions", exact.proposition)
        self.assertEqual((exact.outcome, prop.result.kind, prop.result.value), ("exact", "exact", "safe"))
        self.assertEqual((exact.acquired_at, prop.reference_start, prop.reference_end), (2, 2, 2))
        self.assertEqual(exact.source_ids, ("seal",))
        self.assertEqual(exact.source_path, ("seal", "instrument", "bench"))
        self.assertEqual(exact.actor_path, ("a", "bench"))
        self.assertEqual(h.state.tables["beliefs"], {})
        self.assertEqual(h.state.get("requests", REQUEST), prior_request)
        h.run("adopt_exact")
        belief = h.state.get("beliefs", h.state.get("belief_heads", "internal_safety").belief)
        self.assertEqual(belief.evidence_ids, ("internal_exam",))
        self.assertEqual(belief.proposition, prop.id)
        self.assertEqual(h.state.events[:len(prior_events)], prior_events)
        self.assertEqual(h.state.get("evidence", "partial_indicator"), prior_partial)
        self.assertEqual(h.state.get("refusals", "certification_decline"), prior_decline)
        self.assertEqual(h.state.get("requests", REQUEST), prior_request)
        self.assertIsNone(prior_request.completion_receipt)
        self.assertEqual(h.state.tables["promises"], {})
        self.assertEqual(h.state.tables["receipts"], {})
        self.assertEqual(h.document(visible={e.id for e in prior_events}), prior_document)
        reader = Reader(h.document())
        old = reader.ask("observation", "partial_indicator", reference_tick=0)
        new = reader.ask("observation", "internal_exam", reference_tick=2)
        self.assertTrue(old.supported)
        self.assertIn("unresolved", old.answer.lower())
        self.assertTrue(new.supported)
        self.assertIn("safe", new.answer.lower())
        self.assertNotIn("unsafe", new.answer.lower())
        retained = replay_selection(h.registry, h.spec, h.state, (*ROOTS, "adopt_exact:1"))
        self.assertEqual(retained.events, h.state.events)
        self.assertEqual(h.document(state=retained), h.document())


class HoldoutReaderTests(unittest.TestCase):
    def setUp(self):
        self.h = Holdout()
        self.h.baseline()
        self.doc = self.h.document()

    def test_observation_qa_names_actual_visible_check_and_unresolved_internal_safety(self):
        reader = Reader(self.doc)
        checked = reader.ask("observation", "partial_indicator", question="What did A check, and what remained unknown?")
        self.assertTrue(checked.supported)
        self.assertIn("external indicator", checked.answer.lower())
        self.assertIn("internal safety", checked.answer.lower())
        self.assertIn("unresolved", checked.answer.lower())
        self.assertNotIn("was safe", checked.answer.lower())
        self.assertNotIn("was unsafe", checked.answer.lower())
        self.assertEqual(checked.event_ids, ("inspect_indicator:1",))
        self.assertEqual(checked.reference_tick, 0)

    def test_delivered_request_prose_preserves_internal_safety_certification_not_generic_inspection(self):
        request = Reader(self.doc).ask("request", REQUEST, event_id="deliver_request:1")
        self.assertTrue(request.supported)
        self.assertIn("certif", request.answer.lower(),
                      "H asks for internal safety certification, not just another generic inspection")
        self.assertIn("internal seal", request.answer.lower())
        self.assertIn("safe", request.answer.lower())

    def test_reply_target_qa_names_the_declined_certification_and_focused_reason(self):
        reader = Reader(self.doc)
        target = reader.ask("response", REQUEST, event_id="decline:1",
                            question="Which request did A decline?")
        self.assertTrue(target.supported)
        self.assertIn("certif", target.answer.lower(), "An invisible focus ID is not an answer about the reply target")
        self.assertIn("internal seal", target.answer.lower())
        self.assertIn("safe", target.answer.lower())
        why = reader.follow_up("why")
        self.assertTrue(why.supported)
        self.assertIn(REASON, why.answer)
        self.assertIn("decline:1", why.event_ids)
        self.assertEqual(why.reference_tick, target.reference_tick)

    def test_attributed_reason_and_followup_use_exact_response_event_and_time(self):
        reader = Reader(self.doc)
        response = reader.ask("response", REQUEST, event_id="decline:1", reference_tick=0)
        self.assertTrue(response.supported)
        why = reader.follow_up("why")
        self.assertTrue(why.supported)
        self.assertIn(REASON, why.answer)
        self.assertIn("gave this reason", why.answer.lower())
        self.assertIn("decline:1", why.event_ids)
        self.assertEqual(why.reference_tick, 0)
        self.assertFalse(reader.ask("why", REQUEST, event_id="warning:2").supported)

    def test_repeated_historical_warning_followup_keeps_second_event_not_first(self):
        reader = Reader(self.doc)
        warning = reader.ask("claim", "warning:2", event_id="warning:2")
        self.assertTrue(warning.supported)
        self.assertEqual(warning.reference_tick, 0)
        why = reader.follow_up("why")
        self.assertTrue(why.supported,
                        "The repeated warning's reference time must not hide its actual same-event explanation")
        self.assertIn(WARNING, why.answer)
        self.assertIn("warning:2", why.event_ids)
        self.assertNotIn("warning:1", why.event_ids)

    def test_mask_all_reason_text_abstains_without_changing_trace_or_reply(self):
        state_id = fingerprint(self.h.state)
        hidden = {s.id for s in self.doc.statements if s.kind == "observation"
                  or (s.kind in {"claim", "why"} and s.focus in {"warning:1", "warning:2", REQUEST})}
        masked = self.doc.mask(hidden)
        self.assertEqual(fingerprint(self.h.state), state_id)
        self.assertNotIn(REASON, masked.story)
        self.assertNotIn(WARNING, masked.story)
        self.assertNotIn("external indicator", masked.story.lower())
        reader = Reader(masked)
        self.assertTrue(reader.ask("response", REQUEST, event_id="decline:1").supported)
        self.assertFalse(reader.follow_up("why").supported)
        self.assertFalse(reader.ask("why", REQUEST).supported)
        self.assert_exact_mask(self.doc, masked, hidden)

    def test_mask_all_reply_target_text_abstains_and_never_uses_hidden_focus_id(self):
        state_id = fingerprint(self.h.state)
        hidden = {s.id for s in self.doc.statements if s.focus == REQUEST}
        self.assertTrue(hidden)
        masked = self.doc.mask(hidden)
        self.assertEqual(fingerprint(self.h.state), state_id)
        self.assertNotIn("I decline", masked.story)
        self.assertNotIn(REASON, masked.story)
        self.assertFalse(Reader(masked).ask("response", REQUEST, question="Which request did A decline?").supported)
        self.assertFalse(Reader(masked).ask("why", REQUEST).supported)
        reader = Reader(masked)
        self.assertTrue(reader.ask("claim", "warning:2", event_id="warning:2").supported)
        self.assertFalse(reader.follow_up("response").supported)
        self.assert_exact_mask(self.doc, masked, hidden)

    def test_every_support_span_is_exact_selected_event_entity_and_time_text(self):
        events = {e.id: e for e in self.h.state.events}
        entities = set(self.h.state.tables["entities"])
        for span, statement in zip(self.doc.spans(), self.doc.statements):
            self.assertEqual(self.doc.story[span["start"]:span["end"]], statement.text)
            self.assertTrue(statement.event_ids)
            self.assertLessEqual(set(statement.event_ids), set(events))
            self.assertLessEqual(set(statement.entity_ids), entities)
            self.assertTrue(all(statement.acquired_tick == events[key].tick for key in statement.event_ids))
        self.assertFalse(any("inspect_internal" in key for s in self.doc.statements for key in s.event_ids))

    def assert_exact_mask(self, original, masked, hidden):
        self.assertEqual(masked.statements, tuple(s for s in original.statements if s.id not in hidden))
        self.assertEqual(masked.story, "\n\n".join(s.text for s in original.statements if s.id not in hidden))
        for span, statement in zip(masked.spans(), masked.statements):
            self.assertEqual(masked.story[span["start"]:span["end"]], statement.text)


if __name__ == "__main__":
    unittest.main()
