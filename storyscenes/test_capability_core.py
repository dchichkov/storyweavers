"""Atomicity, explicit versioning and event-aware replay for capability worlds."""
from dataclasses import dataclass, replace
import unittest

from capabilities.core import (Action, CapabilityError, Entity, Query, Record,
                               Registry, WorldSpec, execute, proposals, replay,
                               replay_selection, select_events, solve)
from capabilities.codec import dumps, loads


@dataclass(frozen=True, kw_only=True)
class Fact(Record):
    value: int


def fixture():
    registry = Registry()
    registry.table("facts", Fact)

    def set_fact(tx, key, value):
        tx.get("facts", key)
        tx.put("facts", Fact(id=key, value=value))
        tx.emit(kind="set", key=key, value=value)

    def say(tx, text, support=None):
        if support:
            tx.depend(support)
        tx.emit(kind="utterance", text=text)

    registry.operation("set", set_fact, reads={"facts"}, writes={"facts"})
    registry.operation("say", say, reads=set(), writes=set())
    spec = WorldSpec(title="Core conformance", records={
        "entities": (Entity(id="ada", name="Ada", kind="actor"),),
        "facts": (Fact(id="x", value=0), Fact(id="unused", value=0))}, actions=(
            Action(id="unused", operation="set", actor="ada", args=dict(key="unused", value=9)),
            Action(id="start", operation="say", actor="ada", args=dict(text="Please.")),
            Action(id="reply", operation="say", actor="ada", args=dict(text="No.", support="start:1")),
            Action(id="finish", operation="set", actor="ada", args=dict(key="x", value=1),
                   reason="I declined the request.", reason_support=("reply:1",))),
        goal=(Query(table="facts", key="x", field="value", value=1),))
    return registry, spec


class CapabilityCoreTests(unittest.TestCase):
    def test_explicit_version_boundary(self):
        registry, spec = fixture()
        with self.assertRaisesRegex(CapabilityError, "schema"):
            registry.initial(replace(spec, schema="legacy"))

    def test_json_roundtrip_and_strict_fields(self):
        registry, spec = fixture()
        self.assertEqual(loads(registry, dumps(spec)), spec)
        for invalid in ('{"schema": "x", "schema": "y"}', '{"a":NaN}'):
            with self.assertRaises(CapabilityError):
                loads(registry, invalid)
        with self.assertRaises(CapabilityError):
            loads(registry, dumps(spec).replace('"value": 0', '"value": false'))

    def test_rejection_is_not_attempt_and_is_atomic(self):
        registry, spec = fixture()

        def bad(tx):
            tx.put("facts", Fact(id="x", value=9))
            tx.require(False, "Missing consent")

        registry.operation("bad", bad)
        action = Action(id="bad", operation="bad", actor="ada")
        spec = replace(spec, actions=spec.actions + (action,))
        before = registry.initial(spec)
        self.assertIsNone(execute(registry, spec, before, action))
        self.assertEqual(before, registry.initial(spec))

    def test_one_writer_and_no_hidden_mutation(self):
        registry, spec = fixture()

        def conflict(tx):
            tx.put("facts", Fact(id="x", value=1))
            tx.put("facts", Fact(id="x", value=2))

        def hidden(tx):
            tx.before.tables["facts"]["x"] = Fact(id="x", value=7)
            tx.emit(kind="hidden")

        for name, handler in (("conflict", conflict), ("hidden", hidden)):
            registry.operation(name, handler)
            action = Action(id=name, operation=name, actor="ada")
            world = replace(spec, actions=spec.actions + (action,))
            before = registry.initial(world)
            with self.assertRaises(CapabilityError):
                execute(registry, world, before, action)
            self.assertEqual(before, registry.initial(world))

    def test_declared_read_write_contracts(self):
        registry, spec = fixture()
        registry.contracts["set"] = (frozenset(), frozenset())
        with self.assertRaisesRegex(CapabilityError, "contract"):
            execute(registry, spec, registry.initial(spec), spec.actions[0])

    def test_event_only_repeat_is_bounded(self):
        registry, spec = fixture()
        action = replace(spec.actions[1], max_uses=2)
        spec = replace(spec, actions=(action,))
        state = replay(registry, spec, ["start", "start"])
        self.assertEqual(state.tables, registry.initial(spec).tables)
        self.assertEqual([e.id for e in state.events], ["start:1", "start:2"])
        self.assertIsNone(execute(registry, spec, state, action))

    def test_dependency_pruning_retains_reply_and_reason_not_unused_action(self):
        registry, spec = fixture()
        full = replay(registry, spec, ["unused", "start", "reply", "finish"])
        selected = select_events(full, ["finish:1"])
        self.assertEqual([e.action.id for e in selected], ["start", "reply", "finish"])
        retained = replay_selection(registry, spec, full, ["finish:1"])
        self.assertEqual(retained.get("facts", "x").value, 1)
        self.assertEqual(retained.get("facts", "unused").value, 0)

    def test_seeded_search_and_replay(self):
        registry, spec = fixture()
        for seed in range(5):
            result = solve(registry, spec, seed)
            self.assertEqual(result, solve(registry, spec, seed))
            self.assertEqual(result, replay(registry, spec, [e.action.id for e in result.events]))

    def test_intent_does_not_query_hidden_truth(self):
        registry, spec = fixture()
        s1 = registry.initial(spec)
        s2 = registry.initial(spec)
        s2.tables["facts"]["x"] = Fact(id="x", value=9)
        self.assertEqual(proposals(spec, s1, "ada"), proposals(spec, s2, "ada"))
        action = replace(spec.actions[0], intent=(Query(table="facts", key="x", field="value", value=9),))
        with self.assertRaisesRegex(CapabilityError, "accessible"):
            registry.initial(replace(spec, actions=(action,)))

    def test_atomic_postcondition(self):
        registry, spec = fixture()

        def invariant(state):
            if state.get("facts", "unused").value > 5:
                raise CapabilityError("Capacity")

        registry.validators.append(invariant)
        before = registry.initial(spec)
        self.assertIsNone(execute(registry, spec, before, spec.actions[0]))
        self.assertEqual(before, registry.initial(spec))


if __name__ == "__main__":
    unittest.main()
