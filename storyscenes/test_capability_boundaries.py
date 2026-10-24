"""Independent adversarial regressions for the shared capability boundary.

These assert the required behavior, not the defects observed on 2026-10-22.
Known failures and small proposed fixes are recorded in implementation/core_review.md.
No domain-family implementation or prose entailment is assumed here.
"""
from copy import deepcopy
from dataclasses import dataclass, replace
import json
import unittest

from capabilities.codec import dumps, loads
from capabilities.core import (
    Action, CapabilityError, Entity, Query, Record, Registry, WorldSpec,
    execute, fingerprint, proposals, replay, replay_selection,
)
from capabilities.reading import Document, Reader, Statement


@dataclass(frozen=True, kw_only=True)
class ReviewFact(Record):
    value: int


@dataclass(frozen=True, kw_only=True)
class ReviewPayload(Record):
    values: list[int]


@dataclass(frozen=True, kw_only=True)
class ReviewAccessible(Record):
    accessible: bool
    value: int


def boundary_fixture():
    registry = Registry()
    registry.table("review_facts", ReviewFact)

    def warn(tx, text):
        tx.emit(kind="warning", text=text, details={"checked": ["indicator"]})

    registry.operation("review_warn", warn, reads=set(), writes=set())
    warning = Action(id="warning", operation="review_warn", actor="ada",
                     args={"text": "The seal has not been inspected."}, max_uses=2)
    spec = WorldSpec(title="Boundary review", records={
        "entities": (Entity(id="ada", name="Ada", kind="actor"),),
        "review_facts": (ReviewFact(id="done", value=0),),
    }, actions=(warning,), goal=(Query(table="review_facts", key="done",
                                      field="value", value=1),))
    return registry, spec


class CapabilityBoundaryTests(unittest.TestCase):
    def test_json_requires_an_explicit_schema_field(self):
        registry, spec = boundary_fixture()
        document = json.loads(dumps(spec))
        del document["schema"]
        with self.assertRaises(CapabilityError):
            loads(registry, json.dumps(document))

    def test_json_world_metadata_is_strictly_typed(self):
        registry, spec = boundary_fixture()
        for key, value in (("max_steps", True), ("max_steps", 1.5),
                           ("title", 17), ("title", ["not a string"])):
            with self.subTest(key=key, value=value):
                document = json.loads(dumps(spec))
                document[key] = value
                with self.assertRaises(CapabilityError):
                    loads(registry, json.dumps(document))

    def test_operation_argument_shape_rejected_at_the_initial_boundary(self):
        registry, spec = boundary_fixture()
        for args in ({}, {"text": "hello", "typo": True}, {"text": "hello", "tx": None}):
            with self.subTest(args=args):
                malformed = replace(spec, actions=(replace(spec.actions[0], args=args),))
                for boundary in ("python", "json"):
                    with self.subTest(boundary=boundary):
                        with self.assertRaisesRegex(CapabilityError, "Invalid arguments"):
                            if boundary == "python":
                                registry.initial(malformed)
                            else:
                                loads(registry, dumps(malformed))
        with self.assertRaisesRegex(CapabilityError, "weight"):
            registry.initial(replace(spec, actions=(replace(spec.actions[0], weight=True),)))

    def test_same_value_write_is_not_a_meaningful_enacted_event(self):
        registry, spec = boundary_fixture()

        def noop(tx):
            tx.put("review_facts", tx.get("review_facts", "done"))

        registry.operation("review_noop", noop, reads={"review_facts"}, writes={"review_facts"})
        action = Action(id="noop", operation="review_noop", actor="ada")
        spec = replace(spec, actions=(action,))
        before = registry.initial(spec)
        self.assertIsNone(execute(registry, spec, before, action))
        self.assertEqual(before.events, ())

    def test_rejected_handler_cannot_mutate_the_declared_action(self):
        registry, spec = boundary_fixture()

        def mutate_and_reject(tx, text):
            tx.action.args["text"] = "Changed outside the transaction writer."
            tx.require(False, "Recipient is not ready")

        registry.operation("review_mutate", mutate_and_reject, reads=set(), writes=set())
        action = replace(spec.actions[0], operation="review_mutate")
        spec = replace(spec, actions=(action,))
        before = registry.initial(spec)
        original = deepcopy(spec)
        self.assertIsNone(execute(registry, spec, before, action))
        self.assertEqual(spec, original)

    def test_committed_event_payload_and_action_are_deeply_immutable(self):
        registry, spec = boundary_fixture()
        for target in ("payload", "action"):
            with self.subTest(target=target):
                event = replay(registry, spec, ["warning"]).events[0]
                original = fingerprint(event)
                try:
                    if target == "payload":
                        event.data["details"]["checked"].append("internal seal")
                    else:
                        event.action.args["text"] = "The internal seal is safe."
                except (TypeError, AttributeError):
                    pass
                self.assertEqual(fingerprint(event), original,
                                 "A consumer rewrote committed narrative provenance")

    def test_change_snapshots_do_not_alias_live_or_predecessor_records(self):
        registry, spec = boundary_fixture()
        registry.table("review_payloads", ReviewPayload)

        def update(tx):
            tx.put("review_payloads", ReviewPayload(id="p", values=[2]))

        registry.operation("review_update", update, reads={"review_payloads"},
                           writes={"review_payloads"})
        action = Action(id="update", operation="review_update", actor="ada")
        spec = replace(spec, records={**spec.records, "review_payloads": (
            ReviewPayload(id="p", values=[1]),)}, actions=(action,))
        for side in ("before", "after"):
            with self.subTest(side=side):
                before = registry.initial(spec)
                after = execute(registry, spec, before, action)
                self.assertIsNotNone(after)
                original = fingerprint(after.events[0])
                live = before if side == "before" else after
                try:
                    live.get("review_payloads", "p").values.append(99)
                except (TypeError, AttributeError):
                    pass
                self.assertEqual(fingerprint(after.events[0]), original,
                                 "Live state rewrote an immutable change snapshot")

    def test_pruning_second_event_only_use_preserves_its_identity(self):
        registry, spec = boundary_fixture()
        full = replay(registry, spec, ["warning", "warning"])
        retained = replay_selection(registry, spec, full, ["warning:2"])
        self.assertIn(full.events[1], retained.events)
        self.assertEqual(retained.counts["warning"], 2)
        self.assertIsNone(execute(registry, spec, retained, spec.actions[0]))

    def test_intent_access_is_rechecked_after_access_changes(self):
        registry, spec = boundary_fixture()
        registry.table("review_access", ReviewAccessible)
        registry.intent_validators.append(
            lambda state, actor, query: query.table == "review_access"
            and state.get(query.table, query.key) is not None
            and state.get(query.table, query.key).accessible)

        def hide(tx, value):
            tx.put("review_access", ReviewAccessible(id="private", accessible=False,
                                                     value=value))

        registry.operation("review_hide", hide, reads={"review_access"}, writes={"review_access"})
        check = replace(spec.actions[0], intent=(Query(table="review_access", key="private",
                                                      field="value", value=1),))
        hide_actions = tuple(Action(id=f"hide{value}", operation="review_hide", actor="ada",
                                    args={"value": value}) for value in (0, 1))
        spec = replace(spec, records={**spec.records, "review_access": (
            ReviewAccessible(id="private", accessible=True, value=0),)},
            actions=(check,) + hide_actions)
        # Both legal branches consume identical actions; only the inaccessible value differs.
        hidden_zero = replay(registry, spec, ["hide1", "hide0"])
        hidden_one = replay(registry, spec, ["hide0", "hide1"])
        with self.subTest(boundary="proposals"):
            self.assertEqual(proposals(spec, hidden_zero, "ada"),
                             proposals(spec, hidden_one, "ada"))
        with self.subTest(boundary="execute"):
            self.assertIsNone(execute(registry, spec, hidden_one, check))

    def test_followup_preserves_the_explicitly_selected_event_not_first_support(self):
        document = Document(title="Two inspections", statements=(
            Statement(id="summary", text="Ada checked the indicator twice.",
                      kind="what", focus="indicator", answer="Ada checked it twice.",
                      event_ids=("inspect:1", "inspect:2"), reference_tick=0),
            Statement(id="first", text="The first check followed Bea's request.",
                      kind="why", focus="indicator", answer="Bea requested the first check.",
                      event_ids=("inspect:1",), reference_tick=0),
            Statement(id="second", text="Ada repeated the check at Cal's request.",
                      kind="why", focus="indicator", answer="Cal requested the second check.",
                      event_ids=("inspect:2",), reference_tick=0),
        ))
        for mask_second in (False, True):
            with self.subTest(mask_second=mask_second):
                reader = Reader(document.mask(["second"]) if mask_second else document)
                self.assertTrue(reader.ask("what", "indicator", event_id="inspect:2").supported)
                followup = reader.follow_up("why")
                if mask_second:
                    self.assertFalse(followup.supported)
                else:
                    self.assertTrue(followup.supported)
                    self.assertEqual(followup.statement_ids, ("second",))
                    self.assertEqual(followup.event_ids, ("inspect:2",))


if __name__ == "__main__":
    unittest.main()
