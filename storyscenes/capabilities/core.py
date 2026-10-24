"""Versioned records, bounded events and atomic capability transactions.

Domain handlers inspect one pre-state and stage record replacements. Only the
executor commits them after every domain invariant has been checked.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, fields, is_dataclass
import hashlib
import inspect
import json
import math
import random

SCHEMA = "storyscenes.capabilities.v1"


class CapabilityError(ValueError):
    """Malformed definitions or broken invariants, not a character's failure."""


class Rejected(CapabilityError):
    """Illegal candidate. No event or partial state survives rejection."""


class FrozenDict(dict):
    """Read-only JSON mapping in committed history (including nested payloads)."""
    def _immutable(self, *args, **kwargs):
        raise TypeError("Committed event data is immutable")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _immutable

    def __deepcopy__(self, memo):
        return self


def freeze(value):
    if is_dataclass(value):
        return type(value)(**{f.name: freeze(getattr(value, f.name)) for f in fields(value)})
    if isinstance(value, dict):
        return FrozenDict({k: freeze(v) for k, v in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(freeze(v) for v in value)
    return value


@dataclass(frozen=True, kw_only=True)
class Record:
    id: str


@dataclass(frozen=True, kw_only=True)
class Entity(Record):
    name: str
    kind: str  # actor / place / object / container
    capacity: int = 10
    mass: int = 1


@dataclass(frozen=True, kw_only=True)
class Clock(Record):
    tick: int = 0


@dataclass(frozen=True, kw_only=True)
class Query:
    table: str
    key: str
    field: str = "id"
    op: str = "eq"
    value: object = None


@dataclass(frozen=True, kw_only=True)
class Action:
    id: str
    operation: str
    actor: str
    args: dict = field(default_factory=dict)
    requires: tuple[Query, ...] = ()
    intent: tuple[Query, ...] = ()
    max_uses: int = 1
    weight: float = 1.0
    reason: str | None = None
    reason_support: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class WorldSpec:
    title: str
    records: dict[str, tuple[Record, ...]]
    actions: tuple[Action, ...]
    goal: tuple[Query, ...]
    schema: str = SCHEMA
    max_steps: int = 60


@dataclass(frozen=True, kw_only=True)
class Change:
    table: str
    key: str
    before: Record | None
    after: Record


@dataclass(frozen=True, kw_only=True)
class Event:
    id: str
    action: Action
    tick: int
    changes: tuple[Change, ...]
    reads: tuple[tuple[str, str], ...]
    causes: tuple[str, ...]
    data: dict


@dataclass
class State:
    tables: dict[str, dict[str, Record]]
    events: tuple[Event, ...] = ()
    counts: dict[str, int] = field(default_factory=dict)
    writers: dict[tuple[str, str], str] = field(default_factory=dict)
    _registry: object = field(default=None, repr=False, compare=False, metadata={"serialize": False})

    def get(self, table, key):
        return self.tables.get(table, {}).get(key)

    @property
    def tick(self):
        return self.tables["clock"]["clock"].tick


def plain(value):
    if is_dataclass(value):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value) if f.metadata.get("serialize", True)}
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def fingerprint(value):
    return hashlib.sha256(json.dumps(plain(value), sort_keys=True, allow_nan=False).encode()).hexdigest()


def query_value(state, query):
    record = state.get(query.table, query.key)
    return getattr(record, query.field) if record is not None else None


def matches(state, query):
    value = query_value(state, query)
    if query.op == "eq":
        return value == query.value
    if query.op == "ne":
        return value != query.value
    if query.op == "in":
        return value in query.value
    raise CapabilityError(f"Unknown query operator: {query.op}")


class Registry:
    def __init__(self):
        self.tables = {"entities": Entity, "clock": Clock}
        self.operations = {}
        self.validators = []
        self.initial_validators = []
        self.intent_validators = []
        self.contracts = {}
        self.operation("advance_time", advance_time, reads={"clock"}, writes={"clock"})

    def table(self, name, record_type):
        if name in self.tables or not issubclass(record_type, Record):
            raise CapabilityError(f"Invalid/duplicate record table: {name}")
        self.tables[name] = record_type

    def operation(self, name, handler, *, reads=None, writes=None):
        if name in self.operations:
            raise CapabilityError(f"Duplicate operation: {name}")
        self.operations[name] = handler
        self.contracts[name] = (None if reads is None else frozenset(reads),
                                None if writes is None else frozenset(writes))

    def validate(self, state):
        if set(state.tables) != set(self.tables):
            raise CapabilityError("State has unknown or missing tables")
        if sum(map(len, state.tables.values())) > 10000:
            raise CapabilityError("Record budget exceeded")
        for table, rows in state.tables.items():
            for key, row in rows.items():
                if type(row) is not self.tables[table] or row.id != key or not key:
                    raise CapabilityError(f"Invalid record in {table}: {key}")
                json.dumps(plain(row), allow_nan=False)
        for entity in state.tables["entities"].values():
            if entity.kind not in {"actor", "place", "object", "container"} or not entity.name:
                raise CapabilityError("Invalid physical entity")
            if type(entity.capacity) is not int or entity.capacity < 0 or type(entity.mass) is not int or entity.mass < 0:
                raise CapabilityError("Invalid mass/capacity")
        if set(state.tables["clock"]) != {"clock"} or type(state.tick) is not int or state.tick < 0:
            raise CapabilityError("Invalid finite clock")
        for validator in self.validators:
            validator(state)

    def validate_query(self, query):
        if not isinstance(query, Query) or query.table not in self.tables:
            raise CapabilityError("Unknown query table")
        if query.field not in {f.name for f in fields(self.tables[query.table])}:
            raise CapabilityError("Unknown query field")
        if query.op not in {"eq", "ne", "in"}:
            raise CapabilityError("Unknown query operator")
        if query.op == "in" and not isinstance(query.value, (tuple, list)):
            raise CapabilityError("Membership query needs finite alternatives")

    def initial(self, spec):
        if spec.schema != SCHEMA:
            raise CapabilityError("Explicit capability schema required; no implicit legacy migration")
        if not isinstance(spec.title, str) or not spec.title or not spec.goal or type(spec.max_steps) is not int or not 1 <= spec.max_steps <= 200:
            raise CapabilityError("A bounded world needs a title, goal and step budget")
        if set(spec.records) - set(self.tables):
            raise CapabilityError("Unknown record table")
        state = State(tables={table: {} for table in self.tables}, _registry=self)
        state.tables["clock"]["clock"] = Clock(id="clock")
        for table, rows in spec.records.items():
            if len({r.id for r in rows}) != len(rows):
                raise CapabilityError(f"Duplicate record: {table}")
            state.tables[table] = {r.id: deepcopy(r) for r in rows}
        self.validate(state)
        for validator in self.initial_validators:
            validator(state)
        if len(spec.actions) > 1000 or len({a.id for a in spec.actions}) != len(spec.actions):
            raise CapabilityError("Duplicate actions or action budget exceeded")
        for action in spec.actions:
            if not action.id or action.operation not in self.operations:
                raise CapabilityError(f"Unknown operation: {action.operation}")
            actor = state.get("entities", action.actor)
            if actor is None or actor.kind != "actor":
                raise CapabilityError("Actions must be embedded in an actor")
            if type(action.max_uses) is not int or not 1 <= action.max_uses <= 20:
                raise CapabilityError("Actions require a finite usage bound")
            if type(action.weight) not in (int, float) or not math.isfinite(action.weight) or action.weight <= 0:
                raise CapabilityError("Invalid action weight")
            if not isinstance(action.args, dict):
                raise CapabilityError("Operation arguments must be a mapping")
            try:
                inspect.signature(self.operations[action.operation]).bind(None, **action.args)
            except TypeError as exc:
                raise CapabilityError(f"Invalid arguments for {action.operation}: {exc}") from exc
            if len(json.dumps(plain(action), allow_nan=False)) > 64000:
                raise CapabilityError("Action definition too large")
            for query in action.requires + action.intent:
                self.validate_query(query)
            for query in action.intent:
                if not any(v(state, action.actor, query) for v in self.intent_validators):
                    raise CapabilityError("Intentional choices may only read the actor's accessible records")
        for query in spec.goal:
            self.validate_query(query)
        return state


class Transaction:
    def __init__(self, registry, state, action):
        self.registry = registry
        self.before = deepcopy(state)
        self.action = deepcopy(action)
        self.event_id = f"{action.id}:{state.counts.get(action.id, 0) + 1}"
        self.tick = state.tick
        self.reads = set()
        self.dependencies = set()
        self.writes = {}
        self.data = {}

    def require(self, condition, message):
        if not condition:
            raise Rejected(message)

    def maybe(self, table, key):
        if table not in self.registry.tables:
            raise CapabilityError(f"Unknown read table: {table}")
        self.reads.add((table, key))
        return deepcopy(self.before.get(table, key))

    def get(self, table, key):
        value = self.maybe(table, key)
        self.require(value is not None, f"Missing {table}/{key}")
        return value

    def all(self, table):
        # Table reads also depend on earlier insertions (including empty scans).
        self.reads.add((table, "*"))
        return deepcopy(tuple(self.before.tables[table].values()))

    def put(self, table, record):
        if table not in self.registry.tables or type(record) is not self.registry.tables[table]:
            raise CapabilityError(f"Wrong record type for {table}")
        key = (table, record.id)
        if key in self.writes:
            raise CapabilityError(f"Conflicting effect writers: {table}/{record.id}")
        self.maybe(table, record.id)
        self.writes[key] = deepcopy(record)

    def depend(self, event_id):
        self.require(any(e.id == event_id for e in self.before.events), "Unknown supporting event")
        self.dependencies.add(event_id)

    def emit(self, **data):
        if self.data:
            raise CapabilityError("Only one event payload owner per transaction")
        self.data = deepcopy(data)

    def entity(self, entity_id, kind=None):
        result = self.get("entities", entity_id)
        self.require(kind is None or result.kind == kind, "Entity role mismatch")
        return result


def advance_time(tx, *, to_tick):
    """Close a finite simulated interval. Later actions cannot be backdated."""
    tx.require(type(to_tick) is int and tx.tick < to_tick <= 10000, "Clock must advance within finite bounds")
    tx.put("clock", Clock(id="clock", tick=to_tick))
    tx.emit(kind="clock_advanced", from_tick=tx.tick, to_tick=to_tick)


def execute(registry, spec, state, action):
    """Return a new state; illegal candidates return None without emitting events."""
    if action not in spec.actions:
        raise CapabilityError("Action is not declared in this world")
    if state.counts.get(action.id, 0) >= action.max_uses or len(state.events) >= spec.max_steps:
        return None
    tx = Transaction(registry, state, action)
    tx.get("clock", "clock")
    try:
        for query in action.intent:
            tx.require(any(v(state, action.actor, query) for v in registry.intent_validators),
                       "Intent is no longer accessible to the actor")
        for query in action.requires + action.intent:
            tx.maybe(query.table, query.key)
            tx.require(matches(state, query), "Action prerequisite is not met")
        for event_id in action.reason_support:
            tx.depend(event_id)
        registry.operations[action.operation](tx, **deepcopy(action.args))
        if tx.before != state or tx.action != action:
            raise CapabilityError("Hidden mutation outside the transaction writer")
        allowed_reads, allowed_writes = registry.contracts[action.operation]
        guard_tables = {q.table for q in action.requires + action.intent}
        if allowed_reads is not None and {t for t, _ in tx.reads} - allowed_reads - guard_tables - {"clock"}:
            raise CapabilityError("Operation read outside its declared contract")
        if allowed_writes is not None and {t for t, _ in tx.writes} - allowed_writes:
            raise CapabilityError("Operation wrote outside its declared contract")
        tx.require(bool(tx.data or any(v != state.get(t, k) for (t, k), v in tx.writes.items())),
                   "An enacted action requires a meaningful effect or event")
        after = deepcopy(state)
        for (table, key), record in tx.writes.items():
            after.tables[table][key] = record
        try:
            registry.validate(after)
        except CapabilityError as exc:
            raise Rejected(f"Postcondition failed: {exc}") from exc
    except Rejected:
        return None
    changes = tuple(Change(table=t, key=k, before=freeze(state.get(t, k)), after=freeze(v))
                    for (t, k), v in sorted(tx.writes.items()) if v != state.get(t, k))
    causes = set(tx.dependencies)
    if state.counts.get(action.id, 0):
        causes.add(f"{action.id}:{state.counts[action.id]}")
    for table, key in tx.reads:
        if key == "*":
            causes.update(v for (t, _), v in state.writers.items() if t == table)
        elif (table, key) in state.writers:
            causes.add(state.writers[(table, key)])
    event = Event(id=tx.event_id, action=freeze(action), tick=after.tick,
                  changes=changes, reads=tuple(sorted(tx.reads)), causes=tuple(sorted(causes)), data=freeze(tx.data))
    after.events += (event,)
    after.counts[action.id] = state.counts.get(action.id, 0) + 1
    for change in changes:
        after.writers[(change.table, change.key)] = event.id
    return after


def proposals(spec, state, actor):
    """Intentional options, not a promise that hidden physical guards will succeed."""
    def accessible(action, query):
        return state._registry is not None and any(v(state, action.actor, query)
                                                   for v in state._registry.intent_validators)
    return tuple(a for a in spec.actions if a.actor == actor and state.counts.get(a.id, 0) < a.max_uses
                 and all(accessible(a, q) and matches(state, q) for q in a.intent))


def replay(registry, spec, action_ids):
    state = registry.initial(spec)
    actions = {a.id: a for a in spec.actions}
    for action_id in action_ids:
        if action_id not in actions:
            raise CapabilityError(f"Unknown replay action: {action_id}")
        after = execute(registry, spec, state, actions[action_id])
        if after is None:
            raise CapabilityError(f"Replay rejected {action_id}")
        state = after
    return state


def solve(registry, spec, seed=0, *, max_nodes=6000):
    """Bounded author-side search. Rejected candidates never enter the trace."""
    initial = registry.initial(spec)
    rng = random.Random(seed)
    visited = set()
    nodes = 0

    def visit(state):
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            raise CapabilityError("Search budget exhausted")
        if all(matches(state, q) for q in spec.goal):
            return state
        if len(state.events) >= spec.max_steps:
            return None
        # Keep event identity/order: no-change speech and evidence are real state.
        key = fingerprint([state.tables, state.counts, [e.id for e in state.events]])
        if key in visited:
            return None
        visited.add(key)
        candidates = sorted(spec.actions, key=lambda a: rng.random() ** (1 / a.weight), reverse=True)
        for action in candidates:
            after = execute(registry, spec, state, action)
            if after is not None:
                result = visit(after)
                if result is not None:
                    return result
        return None

    result = visit(initial)
    if result is None:
        raise CapabilityError("No outcome within bounded search")
    return result


def select_events(state, roots):
    """Dependency closure for selected narrative turns, not all available events."""
    by_id = {e.id: e for e in state.events}
    needed = set(roots)
    if needed - set(by_id):
        raise CapabilityError("Unknown narrative event")
    pending = list(needed)
    while pending:
        for cause in by_id[pending.pop()].causes:
            if cause not in needed:
                needed.add(cause)
                pending.append(cause)
    return tuple(e for e in state.events if e.id in needed)


def replay_selection(registry, spec, state, roots):
    selected = select_events(state, roots)
    result = replay(registry, spec, [e.action.id for e in selected])
    # IDs are per action/use, stable under removal of unrelated actions.
    if tuple(result.events) != selected:
        raise CapabilityError("Selection changed event meaning; retain its missing dependencies")
    return result
