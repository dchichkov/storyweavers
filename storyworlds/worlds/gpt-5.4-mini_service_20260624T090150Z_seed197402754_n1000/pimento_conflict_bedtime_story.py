#!/usr/bin/env python3
"""
A tiny bedtime-story world about a child, a late-night craving, and a gentle
conflict that ends in a cozy compromise.

The seed idea is simple: a sleepy child wants a pimento snack at bedtime, but
the parent worries that the snack will make a mess or keep the child awake.
The story turns on a realistic offer: make the snack small, quiet, and neat, so
the child can enjoy it and still settle down for sleep.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    edible: bool = False
    warm: bool = False
    bedtime_safe: bool = False
    quiet: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
class Setting:
    place: str = "the kitchen"
    bedtime: bool = True
    affords: set[str] = field(default_factory=set)
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
class Snack:
    id: str
    label: str
    phrase: str
    crumbly: bool
    red: bool = False
    warm: bool = False
    bedtime_safe: bool = True
    small: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Comfort:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_crumbs(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("eaten", 0.0) < THRESHOLD:
            continue
        snack_id = world.facts.get("snack_id")
        if not snack_id:
            continue
        snack = world.entities[snack_id]
        if not snack.crumbly:
            continue
        sig = ("crumbs", actor.id, snack.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["crumbs"] = actor.meters.get("crumbs", 0.0) + 1
        out.append(f"Small crumbs fell onto the table.")
    return out


def _r_sticky_fingers(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("eaten", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("crumbs", 0.0) < THRESHOLD:
            continue
        sig = ("sticky", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["sticky_hands"] = actor.memes.get("sticky_hands", 0.0) + 1
        out.append(f"{actor.pronoun('possessive').capitalize()} fingers felt sticky.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    parent = world.facts.get("parent")
    snack = world.facts.get("snack")
    if not child or not parent or not snack:
        return out
    if child.memes.get("want_snack", 0.0) < THRESHOLD:
        return out
    if parent.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("conflict", child.id, snack.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    out.append(f"The room felt a little tense.")
    return out


CAUSAL_RULES = [
    Rule("crumbs", _r_crumbs),
    Rule("sticky", _r_sticky_fingers),
    Rule("conflict", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", bedtime=True, affords={"pimento_snack"}),
    "window": Setting(place="the window seat", bedtime=True, affords={"pimento_snack"}),
}

SNACKS = {
    "pimento_toast": Snack(
        id="pimento_toast",
        label="pimento toast",
        phrase="a tiny slice of toast with pimento spread",
        crumbly=True,
        red=True,
        warm=True,
        bedtime_safe=False,
        small=True,
        tags={"pimento", "toast", "red"},
    ),
    "pimento_crackers": Snack(
        id="pimento_crackers",
        label="pimento crackers",
        phrase="a few crackers with pimento cheese",
        crumbly=True,
        red=True,
        warm=False,
        bedtime_safe=False,
        small=True,
        tags={"pimento", "crackers", "cheese"},
    ),
    "plain_milk": Snack(
        id="plain_milk",
        label="warm milk",
        phrase="a small cup of warm milk",
        crumbly=False,
        red=False,
        warm=True,
        bedtime_safe=True,
        small=True,
        tags={"milk", "warm"},
    ),
}

COMFORTS = [
    Comfort(
        id="napkin",
        label="a soft napkin",
        phrase="a soft napkin",
        covers={"hands"},
        guards={"crumbly"},
        prep="put a napkin under the snack",
        tail="set the snack on a napkin and ate slowly",
    ),
    Comfort(
        id="tiny_plate",
        label="a tiny plate",
        phrase="a tiny plate",
        covers={"table"},
        guards={"crumbly"},
        prep="use a tiny plate",
        tail="used the tiny plate and kept the table neat",
    ),
    Comfort(
        id="storybook",
        label="a bedtime storybook",
        phrase="a bedtime storybook",
        covers={"mind"},
        guards={"awake"},
        prep="read one quiet page first",
        tail="read one quiet page and felt ready for sleep",
    ),
]

NAMES = ["Mina", "Theo", "Lily", "Noah", "Ava", "Eli", "Maya", "Finn"]
TRAITS = ["sleepy", "gentle", "curious", "tired", "patient"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    snack: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
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


def can_raise_conflict(snack: Snack) -> bool:
    return snack.red or snack.crumbly or not snack.bedtime_safe


def choose_comfort(snack: Snack) -> Optional[Comfort]:
    for c in COMFORTS:
        if snack.crumbly and "crumbly" in c.guards:
            return c
        if not snack.bedtime_safe and "awake" in c.guards:
            return c
    return None


def predict(world: World, child: Entity, snack: Snack) -> dict:
    sim = world.copy()
    sim.get(child.id).meters["eaten"] = 1.0
    propagate(sim, narrate=False)
    sticky = sim.get(child.id).memes.get("sticky_hands", 0.0) >= THRESHOLD
    conflict = sim.get(child.id).memes.get("conflict", 0.0) >= THRESHOLD
    return {"sticky": sticky, "conflict": conflict}


def introduce(world: World, child: Entity, parent: Entity, snack: Entity) -> None:
    world.say(
        f"{child.id} was a little {next((t for t in child.traits if t != 'little'), 'sleepy')} child "
        f"who was starting to yawn."
    )
    world.say(
        f"{child.id} loved the smell of {snack.label}, even at bedtime."
    )


def bedtime_setup(world: World, child: Entity, parent: Entity, snack: Entity) -> None:
    world.say(
        f"One bedtime night, {child.id} and {child.pronoun('possessive')} {parent.type} "
        f"sat in {world.setting.place} with the lamp turned low."
    )
    world.say(
        f"There was {snack.phrase} on the counter, and it looked bright and tasty."
    )


def wants_snack(world: World, child: Entity, snack: Entity) -> None:
    child.memes["want_snack"] = 1.0
    world.say(
        f"{child.id} wanted {snack.label} right away."
    )


def warns(world: World, parent: Entity, child: Entity, snack: Entity) -> bool:
    pred = predict(world, child, _safe_lookup(SNACKS, snack.id))
    parent.memes["worry"] = 1.0
    if not pred["sticky"] and not pred["conflict"]:
        return False
    if snack.label.startswith("pimento"):
        world.say(
            f'"That snack is a little messy for bedtime," {parent.pronoun("subject")} said. '
            f'"It could leave little red crumbs and keep you up."'
        )
    else:
        world.say(
            f'"That snack might keep you awake," {parent.pronoun("subject")} said softly.'
        )
    return True


def child_protests(world: World, child: Entity, snack: Entity) -> None:
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    world.say(
        f"{child.id} frowned. {child.pronoun('subject').capitalize()} wanted the pimento taste and did not want to wait."
    )


def offer_compromise(world: World, parent: Entity, child: Entity, snack: Entity) -> Optional[Comfort]:
    comfort = choose_comfort(_safe_lookup(SNACKS, snack.id))
    if comfort is None:
        return None
    world.say(
        f"{parent.id} smiled and offered a quieter way: {comfort.prep}."
    )
    return comfort


def accept_compromise(world: World, child: Entity, parent: Entity, snack: Entity, comfort: Comfort) -> None:
    child.meters["eaten"] = 1.0
    child.meters["crumbs"] = 0.0
    child.memes["conflict"] = 0.0
    child.memes["peace"] = child.memes.get("peace", 0.0) + 1
    world.say(
        f"{child.id} nodded and agreed. Soon {child.id} {comfort.tail}, "
        f"with {snack.label} tasting bright but staying neat."
    )
    world.say(
        f"After that, the room grew quiet again, and {child.id} felt sleepy enough for bed."
    )


def tell(
    setting: Setting,
    snack_cfg: Snack,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    parent_type: str = "mother",
    hero_traits: Optional[list[str]] = None,
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=["little"] + (hero_traits or ["sleepy", "gentle"]),
        )
    )
    parent = world.add(
        Entity(id="Parent", kind="character", type=parent_type, label="the parent")
    )
    snack = world.add(
        Entity(
            id=snack_cfg.id,
            type="snack",
            label=snack_cfg.label,
            phrase=snack_cfg.phrase,
            owner=child.id,
            edible=True,
            warm=snack_cfg.warm,
            bedtime_safe=snack_cfg.bedtime_safe,
            quiet=not snack_cfg.crumbly,
        )
    )

    world.facts.update(child=child, parent=parent, snack=snack, snack_id=snack.id)

    introduce(world, child, parent, snack)
    bedtime_setup(world, child, parent, snack)
    world.para()
    wants_snack(world, child, snack)
    warns(world, parent, child, snack)
    child_protests(world, child, snack)
    propagate(world, narrate=True)
    world.para()
    comfort = offer_compromise(world, parent, child, snack)
    if comfort:
        accept_compromise(world, child, parent, snack, comfort)
        world.facts["comfort"] = comfort
        world.facts["resolved"] = True
    else:
        world.say("They sat together and found another quiet plan.")
        world.facts["resolved"] = False
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    snack = _safe_fact(world, f, "snack")
    return [
        'Write a bedtime story for a small child that includes the word "pimento".',
        f"Tell a gentle story where {child.id} wants {snack.label} at bedtime, but {parent.id} worries and they find a calm compromise.",
        f"Write a cozy story about a child, a bedtime snack, and a little conflict that ends quietly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, snack = _safe_fact(world, f, "child"), _safe_fact(world, f, "parent"), _safe_fact(world, f, "snack")
    qa = [
        QAItem(
            question=f"Who wanted the pimento snack at bedtime?",
            answer=f"{child.id} wanted {snack.label} at bedtime.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the snack?",
            answer=f"{parent.id} worried because {snack.label} could leave crumbs and make bedtime less quiet.",
        ),
        QAItem(
            question=f"What helped the child and parent make peace?",
            answer=f"They chose a small, quiet way to enjoy the snack, so {child.id} could eat it neatly and still get sleepy.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with {child.id} feeling calm and ready for bed after the snack was handled in a neat way.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "pimento": [
        (
            "What is pimento?",
            "Pimento is a small red pepper with a sweet, mild taste. People sometimes chop it up or spread it into soft foods.",
        )
    ],
    "crumbly": [
        (
            "Why do crumbs fall from crackers or toast?",
            "Crackers and toast are dry and break into tiny pieces easily, so little crumbs can fall when you bite them.",
        )
    ],
    "bedtime": [
        (
            "Why do kids need calm routines at bedtime?",
            "Calm bedtime routines help a child slow down, feel safe, and get ready to sleep.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["snack"].tags)
    out: list[QAItem] = []
    if "pimento" in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["pimento"])
    if world.facts["snack"].crumbly:
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["crumbly"])
    out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["bedtime"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_wants(C, S) :- child(C), snack(S), wants_snack(C, S).
parent_worries(P, S) :- parent(P), snack(S), bedtime_safe(S), not quiet(S).
parent_worries(P, S) :- parent(P), snack(S), crumbly(S).

problem(C, S) :- child_wants(C, S), parent_worries(_, S).
conflict(C, S) :- problem(C, S), worries(_, S).
compromise(C, S) :- problem(C, S), comfort(K), helps(K, S).
resolved(C, S) :- conflict(C, S), compromise(C, S).

% the snack is bedtime-friendly only if it is quiet or not crumbly and not red
quiet_choice(S) :- snack(S), not crumbly(S), not red(S).
safe_bedtime(S) :- snack(S), bedtime_safe(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, sn in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if sn.crumbly:
            lines.append(asp.fact("crumbly", sid))
        if sn.red:
            lines.append(asp.fact("red", sid))
        if sn.warm:
            lines.append(asp.fact("warm", sid))
        if sn.bedtime_safe:
            lines.append(asp.fact("bedtime_safe", sid))
        if sn.small:
            lines.append(asp.fact("small", sid))
        for tag in sorted(sn.tags):
            lines.append(asp.fact("tag", sid, tag))
    for cid, c in zip([c.id for c in COMFORTS], COMFORTS):
        lines.append(asp.fact("comfort", cid))
        for g in sorted(c.guards):
            lines.append(asp.fact("helps", cid, g))
    lines.append(asp.fact("wants_snack", "mina", "pimento_toast"))
    lines.append(asp.fact("worries", "parent", "pimento_toast"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show quiet_choice/1.\n#show safe_bedtime/1."))
    atoms = set()
    for sym in model:
        if sym.name in {"quiet_choice", "safe_bedtime"}:
            atoms.add((sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)))
    expected = {("safe_bedtime", ("pimento_toast",)), ("safe_bedtime", ("plain_milk",))}
    if atoms >= expected:
        print("OK: ASP rules loaded and evaluated.")
        return 0
    print("Mismatch or insufficient ASP result.")
    print("Model atoms:", sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# Params, parser, resolution, generation, emit, main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="kitchen", snack="pimento_toast", name="Mina", gender="girl", parent="mother", trait="sleepy"),
    StoryParams(place="window", snack="pimento_crackers", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="kitchen", snack="plain_milk", name="Ava", gender="girl", parent="mother", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about pimento, conflict, and a gentle compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "snack", None) and not can_raise_conflict(_safe_lookup(SNACKS, getattr(args, "snack", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    places = [p for p in SETTINGS if getattr(args, "place", None) is None or getattr(args, "place", None) == p]
    snacks = [s for s in SNACKS if getattr(args, "snack", None) is None or getattr(args, "snack", None) == s]
    if not places or not snacks:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(places)
    snack = getattr(args, "snack", None) or rng.choice(snacks)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, snack=snack, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SNACKS, params.snack), params.name, params.gender, params.parent, [params.trait])
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
        print(asp_program("#show quiet_choice/1.\n#show safe_bedtime/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show quiet_choice/1.\n#show safe_bedtime/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
            header = f"### {p.name}: {p.snack} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
