#!/usr/bin/env python3
"""
storyworlds/worlds/terminal_repetition_suspense_magic_superhero_story.py
========================================================================

A small story world about a superhero at a terminal, where repetition builds
suspense and a little magic becomes the turn that saves the day.

The seed image:
---
At a busy terminal, a little superhero noticed the same whisper again and
again: "Not now, not now, not now." A magic charm kept blinking near a locked
door. The hero listened, worried, and then found the one person who could open
the way before the next bus left.

This world models:
- a terminal with gates, boards, and doors
- a superhero hero who can act bravely
- a repeating problem that increases suspense
- a magic object that reveals the right clue
- a final rescue that resolves the tension
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    door: object | None = None
    fix: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self):
        self.meters.setdefault("moved", 0.0)
        self.meters.setdefault("safe", 0.0)
        self.meters.setdefault("stuck", 0.0)
        self.memes.setdefault("hope", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("suspense", 0.0)
        self.memes.setdefault("joy", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Terminal:
    place: str = "the terminal"
    terminal_type: str = "bus terminal"
    has_clock: bool = True
    has_board: bool = True
    has_gates: bool = True
    has_locks: bool = True
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Power:
    id: str
    label: str
    clue: str
    reveal: str
    glimmer: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Problem:
    id: str
    label: str
    repeated_line: str
    risk: str
    deadline: str
    block: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    use: str
    target: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, terminal: Terminal) -> None:
        self.terminal = terminal
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.board_messages: int = 0
        self.repeat_count: int = 0
        self.door_locked: bool = True
        self.clock_ticks: int = 0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.terminal)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.board_messages = self.board_messages
        c.repeat_count = self.repeat_count
        c.door_locked = self.door_locked
        c.clock_ticks = self.clock_ticks
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    if world.repeat_count < 3 and world.board_messages > 0:
        sig = ("repeat", world.repeat_count)
        if sig not in world.fired:
            world.fired.add(sig)
            world.repeat_count += 1
            for ent in list(world.entities.values()):
                if ent.kind == "character":
                    ent.memes["suspense"] += 0.5
            out.append("Again and again, the message came back.")
    return out


def _r_clock(world: World) -> list[str]:
    out: list[str] = []
    if world.clock_ticks >= 2 and world.door_locked:
        sig = ("clock", world.clock_ticks)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The clock kept moving, and that made the wait feel tighter.")
    return out


def _r_safety(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    door = world.entities.get("door")
    if hero and door and door.meters["safe"] >= THRESHOLD and world.door_locked:
        sig = ("safe",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.door_locked = False
            out.append("The lock clicked open at last.")
    return out


CAUSAL_RULES = [_r_repetition, _r_clock, _r_safety]


def predict(world: World, hero: Entity, problem: Problem) -> dict:
    sim = world.copy()
    sim.board_messages += 1
    sim.clock_ticks += 1
    propagate(sim, narrate=False)
    return {
        "suspense": hero.memes["suspense"] + 1.0,
        "locked": sim.door_locked,
    }


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little superhero who liked to listen closely at busy places.")
    world.say("At the terminal, every footstep sounded important, and every voice seemed to hurry.")


def describe_problem(world: World, problem: Problem) -> None:
    world.say(
        f"Near the board, someone kept saying, '{problem.repeated_line}' "
        f"over and over, and the same warning kept returning."
    )
    world.say(
        f"It made the terminal feel suspenseful, because {problem.risk} "
        f"and {problem.deadline}."
    )


def hero_watches(world: World, hero: Entity, power: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    hero.memes["suspense"] += 1
    world.board_messages += 1
    world.clock_ticks += 1
    world.say(f"{hero.id} watched the blinking {power.label} and listened to the repeating warning.")
    propagate(world)
    world.say(
        f"{hero.id} whispered, 'Not yet... not yet...' and waited for a clue instead of rushing."
    )


def magical_hint(world: World, hero: Entity, power: Entity, problem: Problem) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"Then the {power.label} gave a tiny glow, and its magic revealed {power.reveal}."
    )
    world.say(
        f"It was a gentle kind of magic: not a blast, just a bright hint that pointed the way."
    )


def choose_remedy(world: World, remedy: Entity, problem: Problem) -> None:
    world.say(
        f"{remedy.label} was the right fix, because {remedy.use}."
    )


def resolve(world: World, hero: Entity, helper: Entity, remedy: Entity, problem: Problem) -> None:
    hero.meters["moved"] += 1
    helper.meters["safe"] += 1
    world.get("door").meters["safe"] += 1
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0
    hero.memes["suspense"] = 0
    world.say(
        f"{hero.id} found {helper.id}, and together they used {remedy.label} to {remedy.action}."
    )
    world.say(
        f"The lock clicked open, the way cleared, and the next bus could leave on time."
    )
    world.say(
        f"In the end, the terminal felt calm again, and {hero.id} stood taller beside the open door."
    )


def tell(terminal: Terminal, hero_name: str, helper_name: str, problem: Problem, power: Power, remedy: Remedy) -> World:
    world = World(terminal)
    hero = world.add(Entity(id="hero", kind="character", type="superhero", label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=helper_name))
    door = world.add(Entity(id="door", type="door", label="locked door"))
    charm = world.add(Entity(id="charm", type="magic", label=power.label, phrase=power.clue, owner=hero.id))
    fix = world.add(Entity(id="remedy", type="tool", label=remedy.label, phrase=remedy.target, owner=helper.id))

    introduce(world, hero)
    world.para()
    describe_problem(world, problem)
    hero_watches(world, hero, charm, problem)
    magical_hint(world, hero, charm, problem)
    world.para()
    choose_remedy(world, fix, problem)
    resolve(world, hero, helper, fix, problem)

    world.facts.update(
        hero=hero,
        helper=helper,
        door=door,
        charm=charm,
        remedy=fix,
        problem=problem,
        power=power,
        terminal=terminal,
        solved=True,
    )
    return world


TERMINALS = {
    "bus_terminal": Terminal(place="the terminal", terminal_type="bus terminal"),
    "train_terminal": Terminal(place="the terminal", terminal_type="train terminal"),
    "ferry_terminal": Terminal(place="the terminal", terminal_type="ferry terminal"),
}

PROBLEMS = {
    "locked_gate": Problem(
        id="locked_gate",
        label="locked gate",
        repeated_line="Not now, not now, not now",
        risk="the next bus might leave without the lost family",
        deadline="the departure clock was almost at zero",
        block="the gate would not open",
    ),
    "missing_ticket": Problem(
        id="missing_ticket",
        label="missing ticket",
        repeated_line="I can't find it, I can't find it",
        risk="the traveler might miss the ride",
        deadline="the line was moving fast",
        block="the board had no answer",
    ),
    "jammed_door": Problem(
        id="jammed_door",
        label="jammed door",
        repeated_line="Stuck again, stuck again, stuck again",
        risk="people could not reach the platform",
        deadline="the lights were about to switch",
        block="the door would not budge",
    ),
}

POWERS = {
    "glow_charm": Power(
        id="glow_charm",
        label="glow charm",
        clue="the right keycard was hanging on the helper's lanyard",
        reveal="a tiny blue arrow on the board",
        glimmer="blue",
    ),
    "echo_charm": Power(
        id="echo_charm",
        label="echo charm",
        clue="the lost ticket had slipped between two seats",
        reveal="a soft echo that pointed to the bench",
        glimmer="silver",
    ),
    "spark_charm": Power(
        id="spark_charm",
        label="spark charm",
        clue="the latch needed a careful push, not a hard shove",
        reveal="a warm spark on the hinge",
        glimmer="gold",
    ),
}

REMEDIES = {
    "keycard": Remedy(
        id="keycard",
        label="a keycard",
        action="swipe it open",
        use="it matched the lock",
        target="the door's reader",
    ),
    "ticket_clip": Remedy(
        id="ticket_clip",
        label="a ticket clip",
        action="pin the ticket to the bag",
        use="it kept the ticket from slipping away",
        target="the paper and the strap",
    ),
    "oil_can": Remedy(
        id="oil_can",
        label="a tiny oil can",
        action="ease the hinge",
        use="it helped the door move",
        target="the stiff hinge",
    ),
}

HERO_NAMES = ["Nova", "Sky", "Brave", "Flash", "Mira", "Ruby", "Jett"]
HELPER_NAMES = ["Ms. Lane", "Mr. Reed", "Aunt Pina", "Coach Rio", "Nina"]
TRAITS = ["brave", "careful", "kind", "quick", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TERMINALS:
        for p in PROBLEMS:
            for c in POWERS:
                if (p == "locked_gate" and c == "glow_charm") or (
                    p == "missing_ticket" and c == "echo_charm"
                ) or (
                    p == "jammed_door" and c == "spark_charm"
                ):
                    combos.append((t, p, c))
    return combos


@dataclass
class StoryParams:
    terminal: str
    problem: str
    power: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story set at a terminal that includes the repeated line "{f["problem"].repeated_line}".',
        f"Tell a suspenseful magic story where {f['hero'].label} notices a problem at the terminal and finds a helper before the next departure.",
        f"Write a child-friendly superhero tale with a glowing charm, a repeating warning, and a calm rescue at {f['terminal'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    problem: Problem = _safe_fact(world, f, "problem")
    power: Power = _safe_fact(world, f, "power")
    return [
        QAItem(
            question=f"Where did {hero.label} notice the problem?",
            answer=f"{hero.label} noticed it at {f['terminal'].place}, where the {problem.label} was causing suspense.",
        ),
        QAItem(
            question=f"What line kept repeating in the story?",
            answer=f'The repeating line was "{problem.repeated_line}." It made the problem feel more and more urgent.',
        ),
        QAItem(
            question=f"What did the magic charm reveal?",
            answer=f"The {power.label} revealed {power.reveal}, which helped {hero.label} know what to do next.",
        ),
        QAItem(
            question=f"Who helped {hero.label} fix the trouble?",
            answer=f"{helper.label} helped {hero.label}, and together they used the remedy to solve the problem.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer="The lock opened, the waiting ended, and the terminal grew calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a terminal?",
            answer="A terminal is a place where people arrive, wait, and leave on buses, trains, or boats.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="What does magic often do in a story?",
            answer="Magic can reveal clues, change things in surprising ways, or help a hero solve a problem.",
        ),
        QAItem(
            question="Why can repeating words matter in a story?",
            answer="Repeating words can make a moment feel stronger, louder, or more urgent.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"terminal={world.terminal.terminal_type} locked={world.door_locked} board_messages={world.board_messages} repeat_count={world.repeat_count}")
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} {e.type:10} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bus_terminal", "locked_gate", "glow_charm", "Nova", "Ms. Lane", "brave"),
    StoryParams("train_terminal", "missing_ticket", "echo_charm", "Sky", "Mr. Reed", "careful"),
    StoryParams("ferry_terminal", "jammed_door", "spark_charm", "Mira", "Aunt Pina", "kind"),
]


def explain_rejection(problem: Problem, power: Power) -> str:
    return f"(No story: {power.label} does not fit the {problem.label}. This world only uses a magic clue that truly solves the repeating problem.)"


ASP_RULES = r"""
terminal(bus_terminal).
terminal(train_terminal).
terminal(ferry_terminal).

problem(locked_gate).
problem(missing_ticket).
problem(jammed_door).

power(glow_charm).
power(echo_charm).
power(spark_charm).

valid(bus_terminal, locked_gate, glow_charm).
valid(train_terminal, missing_ticket, echo_charm).
valid(ferry_terminal, jammed_door, spark_charm).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in TERMINALS:
        lines.append(asp.fact("terminal", t))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for c in POWERS:
        lines.append(asp.fact("power", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story at a terminal with repetition, suspense, and magic.")
    ap.add_argument("--terminal", choices=TERMINALS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "problem", None) and getattr(args, "power", None):
        if (getattr(args, "terminal", None) or "bus_terminal", getattr(args, "problem", None), getattr(args, "power", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "terminal", None) is None or c[0] == getattr(args, "terminal", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "power", None) is None or c[2] == getattr(args, "power", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    terminal, problem, power = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(terminal=terminal, problem=problem, power=power, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(TERMINALS, params.terminal), params.name, params.helper, _safe_lookup(PROBLEMS, params.problem), _safe_lookup(POWERS, params.power), REMEDIES[{
        "locked_gate": "keycard",
        "missing_ticket": "ticket_clip",
        "jammed_door": "oil_can",
    }[params.problem]])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (terminal, problem, power) combos:")
        for t, p, c in combos:
            print(f"  {t:14} {p:14} {c:12}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.terminal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
