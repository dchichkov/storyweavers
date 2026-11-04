"""Small standalone world kernel: content algebra, atomic effects, and provenance."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
import random
from typing import Callable


class StoryError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Memeplex:
    """Immutable weighted content; an unembedded expression has no world effects.

    Atoms can name concepts, people, actions, or compound stories. Algebra operates
    on content; physical transitions still require an admitted executable action.
    """
    terms: tuple[tuple[str, float], ...] = ()

    def __post_init__(self):
        if len(dict(self.terms)) != len(self.terms):
            raise StoryError("Duplicate content atom")
        if any(not k or not math.isfinite(v) or v < 0 for k, v in self.terms):
            raise StoryError("Content weights must be finite and nonnegative")

    @classmethod
    def atom(cls, name, weight=1):
        return cls(((name, float(weight)),))

    def __add__(self, other):
        if not isinstance(other, Memeplex):
            return NotImplemented
        values = dict(self.terms)
        for k, v in other.terms:
            values[k] = values.get(k, 0) + v
        return Memeplex(tuple(sorted(values.items())))

    def __truediv__(self, divisor):
        if not math.isfinite(divisor) or divisor < 1:
            raise StoryError("Attention divisor must be finite and at least one")
        return Memeplex(tuple((k, v / divisor) for k, v in self.terms))


@dataclass
class Event:
    id: str
    drama: str
    action: str
    actors: list[str]
    before_hash: str
    after_hash: str
    changes: dict
    reads: dict
    causes: list[str]
    transfers: list[dict]
    checks: list[str]


class Transaction:
    def __init__(self, world):
        self.world = world
        self.state = deepcopy(world.state)
        self.reads = {}
        self.transfers = []
        self.checks = []

    def get(self, key):
        if key not in self.state:
            raise StoryError(f"Undeclared key: {key}")
        # Capture the action's initial dependency even after a local write.
        self.reads[key] = deepcopy(self.world.state[key])
        return self.state[key]

    def require(self, condition, reason):
        if not condition:
            raise StoryError(reason)
        self.checks.append(reason)

    def set(self, key, value):
        old = self.get(key)
        numeric = type(old) in (int, float) and type(value) in (int, float)
        self.require(numeric or type(old) is type(value), f"Type of {key} is preserved")
        self.state[key] = deepcopy(value)

    def add(self, key, value):
        self.set(key, self.get(key) + value)

    def embed(self, carrier, content):
        self.require(carrier in self.world.entities, "Content has a physical carrier")
        for name, weight in content.terms:
            self.add(f"{carrier}.meme.{name}", weight)

    def absorb(self, source, target, *, divisor=1, terms=None):
        self.require(source in self.world.entities and target in self.world.entities,
                     "Both transmission endpoints exist")
        self.require(self.get(source + ".location") == self.get(target + ".location"),
                     "Transmission endpoints share a location")
        if self.world.entities[source]["kind"] == "book":
            self.require(self.get(source + ".accessible"), "The source book is physically accessible")
        prefix = source + ".meme."
        names = list(terms) if terms is not None else [k[len(prefix):] for k in self.state if k.startswith(prefix)]
        content = Memeplex(tuple((name, float(self.get(prefix + name))) for name in names)) / divisor
        self.require(any(v > 0 for _, v in content.terms), "The source actually carries the content")
        self.embed(target, content)
        self.transfers.append({"source": source, "target": target, "divisor": divisor,
                               "content": dict(content.terms)})

    def move(self, carrier, destination):
        self.require(destination in self.world.locations, "Destination exists")
        self.set(carrier + ".location", destination)

    def observe(self, actor, subject, key, memory):
        self.require(self.get(actor + ".location") == self.get(subject + ".location"),
                     "Observer is present with the observed subject")
        self.require(key.startswith(subject + ".") and memory.startswith(actor + "."),
                     "Observation preserves subject and observer roles")
        self.set(memory, self.get(key))


class World:
    def __init__(self, entities, locations, initial, validator):
        self.entities = deepcopy(entities)
        self.locations = tuple(locations)
        self.state = deepcopy(initial)
        self.initial = deepcopy(initial)
        self.validator = validator
        self.history = []
        self.last_writer = {}
        self.validate(self.state)

    def validate(self, state):
        if set(state) != set(self.initial):
            raise StoryError("The state schema cannot change during a run")
        for key, value in state.items():
            if key.partition(".")[0] not in self.entities:
                raise StoryError(f"Unembedded state: {key}")
            if type(value) not in (str, bool, int, float):
                raise StoryError(f"Non-scalar state: {key}")
            if type(value) in (int, float) and not math.isfinite(value):
                raise StoryError("Nonfinite state")
            if ".meme." in key and (type(value) not in (int, float) or value < 0):
                raise StoryError("Invalid embedded magnitude")
            if key.endswith(".location") and value not in self.locations:
                raise StoryError("Unknown location")
            if key.endswith(".owner") and value not in self.entities:
                raise StoryError("Unknown owner")
        self.validator(deepcopy(state))

    def act(self, drama, action, actors, mutate):
        if any(actor not in self.entities for actor in actors):
            raise StoryError("Unknown action participant")
        tx = Transaction(self)
        mutate(tx)
        self.validate(tx.state)
        changes = {k: {"before": deepcopy(self.state[k]), "after": deepcopy(v)}
                   for k, v in tx.state.items() if v != self.state[k]}
        if not changes:
            raise StoryError("An action must change the world")
        event = Event(f"e{len(self.history)+1:03}", drama, action, list(actors),
                      digest(self.state), digest(tx.state), changes, tx.reads,
                      sorted({self.last_writer[k] for k in tx.reads if k in self.last_writer}),
                      tx.transfers, tx.checks)
        self.state = tx.state
        self.history.append(event)
        for key in changes:
            self.last_writer[key] = event.id
        return event


@dataclass(frozen=True)
class Microdrama:
    id: str
    admits: Callable[[dict], bool]
    perform: Callable[[World, object], None]
    priority: int = 10
    # Multiple encounters can share a practice while binding different objects.
    practice: str = "encounter"


@dataclass
class Episode:
    id: str
    before: dict
    after: dict
    event_ids: list[str]


def compose(world, dramas, params, seed=0):
    if len({d.id for d in dramas}) != len(dramas):
        raise StoryError("Microdrama ids must be unique")
    rng = random.Random(seed)
    used, episodes, choices = set(), [], []
    for _ in range(len(dramas) + 1):
        if world.state["valley.ended"]:
            return episodes, choices
        available = [d for d in dramas if d.id not in used and d.admits(deepcopy(world.state))]
        if not available:
            raise StoryError("No admitted microdrama; incomplete story")
        best = max(d.priority for d in available)
        selected = rng.choice(sorted((d for d in available if d.priority == best), key=lambda d: d.id))
        choices.append({"selected": selected.id, "eligible": [d.id for d in available],
                        "priority": best, "state_hash": digest(world.state)})
        before, offset = deepcopy(world.state), len(world.history)
        # Whole encounters are atomic as well as their constituent operations.
        trial = deepcopy(world)
        selected.perform(trial, params)
        if len(trial.history) == offset:
            raise StoryError("Empty microdrama")
        trial.validate(trial.state)
        if trial.history[:offset] != world.history:
            raise StoryError("A microdrama cannot rewrite committed history")
        if replay(before, trial.history[offset:]) != trial.state:
            raise StoryError("Microdrama state contains an unrecorded effect")
        world.state, world.history, world.last_writer = trial.state, trial.history, trial.last_writer
        episodes.append(Episode(selected.id, before, deepcopy(world.state),
                                [e.id for e in world.history[offset:]]))
        used.add(selected.id)
    raise StoryError("Composition exceeded the finite encounter budget")


def replay(initial, events):
    state = deepcopy(initial)
    for row in events:
        event = row.__dict__ if isinstance(row, Event) else row
        if digest(state) != event["before_hash"]:
            raise StoryError("Replay base fingerprint differs")
        for key, value in event["reads"].items():
            if state.get(key) != value:
                raise StoryError("Replay dependency differs")
        for key, change in event["changes"].items():
            if key not in state or state[key] != change["before"]:
                raise StoryError("Replay exact precondition differs")
            state[key] = deepcopy(change["after"])
        if digest(state) != event["after_hash"]:
            raise StoryError("Replay result fingerprint differs")
    return state
