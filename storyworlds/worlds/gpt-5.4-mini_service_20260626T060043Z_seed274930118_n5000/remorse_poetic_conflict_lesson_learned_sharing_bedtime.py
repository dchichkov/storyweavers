#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/remorse_poetic_conflict_lesson_learned_sharing_bedtime.py
================================================================================================

A small bedtime-story world about sharing, conflict, remorse, and a poetic
lesson learned.

Seed tale:
---
At bedtime, a child clung to a favorite moon pillow and refused to share it
with a younger sibling. The sibling felt hurt, the parent warned that cozy
things are happier when shared, and the child soon felt remorse. A soft,
poetic apology turned the night gentle again, and both children ended up
sharing the pillow under the blanket while the room glowed with quiet stars.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    obj: object | None = None
    parent: object | None = None
    sibling: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the bedroom"
    affordances: set[str] = field(default_factory=set)
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
class ObjectConfig:
    id: str
    label: str
    phrase: str
    kind: str
    mood: str
    comfort: str
    shared_bonus: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    setting: str = ""
    object: str = ""
    name: str = ""
    gender: str = ""
    sibling_name: str = ""
    sibling_gender: str = ""
    parent: str = ""
    trait: str = ""
    seed: Optional[int] = None
    place: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    sibling = world.entities.get("sibling")
    if not hero or not sibling:
        return out
    if hero.memes.get("refuse", 0.0) < THRESHOLD:
        return out
    if sibling.memes.get("hurt", 0.0) < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    return ["__conflict__"]


def _r_remorse(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("conflict", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("remorse", 0.0) >= THRESHOLD:
        return out
    sig = ("remorse",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["remorse"] = 1.0
    out.append(f"{hero.id} felt a warm, prickly remorse in {hero.pronoun('possessive')} chest.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    sibling = world.entities.get("sibling")
    pillow = world.entities.get("object")
    if not hero or not sibling or not pillow:
        return out
    if hero.memes.get("remorse", 0.0) < THRESHOLD:
        return out
    if pillow.shared_with == {hero.id, sibling.id}:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pillow.shared_with = {hero.id, sibling.id}
    hero.memes["warmth"] = hero.memes.get("warmth", 0.0) + 1.0
    sibling.memes["comfort"] = sibling.memes.get("comfort", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    return ["__share__"]


CAUSAL_RULES: list[Rule] = [
    Rule("conflict", "social", _r_conflict),
    Rule("remorse", "social", _r_remorse),
    Rule("share", "social", _r_share),
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
                produced.extend(s for s in sents if s not in {"__conflict__", "__share__"})
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_conflict(world: World, hero: Entity, sibling: Entity, obj: Entity) -> dict:
    sim = world.copy()
    sim.get("hero").memes["refuse"] = 1.0
    sim.get("sibling").memes["hurt"] = 1.0
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("hero").memes.get("conflict", 0.0) >= THRESHOLD,
        "remorse": sim.get("hero").memes.get("remorse", 0.0) >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, sibling: Entity, obj: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} was a little {hero.traits[0]} {hero.type} "
        f"who loved {obj.phrase}."
    )
    world.say(
        f"{sibling.id}, {sibling.pronoun('subject')} {sibling.type} sibling, loved cozy bedtime things too."
    )


def setup_bedtime(world: World, parent: Entity, hero: Entity, sibling: Entity, obj: Entity) -> None:
    world.say(
        f"One bedtime, {hero.id} curled up with {hero.pronoun('possessive')} {obj.label}, "
        f"and {sibling.id} reached for it with a sleepy smile."
    )
    world.say(
        f"{parent.id} was nearby, ready to help the room stay gentle and calm."
    )


def refuse_and_conflict(world: World, hero: Entity, sibling: Entity, obj: Entity) -> None:
    hero.memes["refuse"] = 1.0
    sibling.memes["hurt"] = 1.0
    world.say(
        f"{hero.id} hugged the {obj.label} tight and said, \"No, it's mine.\""
    )
    world.say(
        f"{sibling.id}'s face fell, because {sibling.pronoun('subject')} had wanted to share."
    )
    propagate(world, narrate=True)


def parent_teaches(world: World, parent: Entity, hero: Entity, sibling: Entity, obj: Entity) -> None:
    world.say(
        f"{parent.id} spoke softly: \"Little things feel even nicer when they are shared.\""
    )
    world.say(
        f"The words floated like a lullaby, and {hero.id} looked down at the {obj.label} with new eyes."
    )


def apologize_and_share(world: World, hero: Entity, sibling: Entity, obj: Entity) -> None:
    if hero.memes.get("remorse", 0.0) < THRESHOLD:
        hero.memes["remorse"] = 1.0
        propagate(world, narrate=True)
    world.say(
        f"{hero.id} took a breath and said, in a small poetic voice, "
        f"\"I was a closed door, but I want to be a window; I am sorry for holding the moon all to myself.\""
    )
    propagate(world, narrate=True)
    if obj.shared_with == {hero.id, sibling.id}:
        world.say(
            f"Then {hero.id} scooted over, and both children tucked their hands around the {obj.label} together."
        )


def ending(world: World, hero: Entity, sibling: Entity, obj: Entity) -> None:
    if obj.shared_with == {hero.id, sibling.id}:
        world.say(
            f"The bedroom went quiet and soft. Under the blanket, the {obj.label} glowed like a tiny moon, "
            f"and {hero.id} had learned that sharing made bedtime warmer."
        )
    else:
        world.say(
            f"The room stayed hushed, but the lesson remained: bedtime feels kinder when everyone gets a turn."
        )


SETTING_REGISTRY = {
    "bedroom": Setting(place="the bedroom", affordances={"share"}),
    "nursery": Setting(place="the nursery", affordances={"share"}),
}

OBJECTS = {
    "moon_pillow": ObjectConfig(
        id="moon_pillow",
        label="moon pillow",
        phrase="a moon pillow with silver stars",
        kind="pillow",
        mood="sleepy",
        comfort="soft",
        shared_bonus="It felt warmer when two children hugged it at once.",
        genders={"girl", "boy"},
    ),
    "storybook": ObjectConfig(
        id="storybook",
        label="storybook",
        phrase="a bedtime storybook with a blue cover",
        kind="book",
        mood="dreamy",
        comfort="gentle",
        shared_bonus="The pages sounded sweeter when both children listened together.",
        genders={"girl", "boy"},
    ),
    "blanket": ObjectConfig(
        id="blanket",
        label="blanket",
        phrase="a star blanket stitched with tiny moons",
        kind="blanket",
        mood="cozy",
        comfort="warm",
        shared_bonus="It wrapped around both children like a cloudy night sky.",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Ruby", "Maya"]
BOY_NAMES = ["Theo", "Leo", "Finn", "Ben", "Max", "Noah", "Eli", "Sam"]
TRAITS = ["gentle", "curious", "stubborn", "quiet", "brave", "dreamy"]
PARENTS = ["mother", "father", "grown-up"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTING_REGISTRY:
        for obj in OBJECTS:
            combos.append((setting, obj))
    return combos


def explain_rejection(_: ObjectConfig) -> str:
    return "(No story: this bedtime world only supports sharing a cozy object at bedtime.)"


def explain_gender(obj_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(OBJECTS, obj_id).genders))
    return f"(No story: that object does not fit the requested gender here; try {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world about sharing, conflict, remorse, and a poetic lesson."
    )
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
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
    if getattr(args, "gender", None) and getattr(args, "object", None) and getattr(args, "gender", None) not in _safe_lookup(OBJECTS, getattr(args, "object", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              and getattr(args, "object", None) is None or c[1] == getattr(args, "object", None)]
    if getattr(args, "place", None) or getattr(args, "object", None):
        combos = [c for c in valid_combos()
                  if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                  and (getattr(args, "object", None) is None or c[1] == getattr(args, "object", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    obj = _safe_lookup(OBJECTS, obj_id)
    if gender not in obj.genders:
        gender = rng.choice(sorted(obj.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sibling_gender = getattr(args, "sibling_gender", None) or ("boy" if gender == "girl" else "girl")
    sibling_name = getattr(args, "sibling_name", None) or rng.choice(BOY_NAMES if sibling_gender == "boy" else GIRL_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj_id, name=name, gender=gender,
                       sibling_name=sibling_name, sibling_gender=sibling_gender,
                       parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTING_REGISTRY, params.setting if hasattr(params, "setting") else params.place))
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, traits=[params.trait, "little"]))
    sibling = world.add(Entity(id="sibling", kind="character", type=params.sibling_gender, traits=["little"]))
    parent = world.add(Entity(id="parent", kind="character", type="adult", label=params.parent))
    obj_cfg = _safe_lookup(OBJECTS, params.object)
    obj = world.add(Entity(id="object", kind="thing", type=obj_cfg.kind, label=obj_cfg.label,
                           phrase=obj_cfg.phrase, owner=hero.id, caretaker=parent.id))
    introduce(world, hero, sibling, obj)
    world.para()
    setup_bedtime(world, parent, hero, sibling, obj)
    refuse_and_conflict(world, hero, sibling, obj)
    world.para()
    parent_teaches(world, parent, hero, sibling, obj)
    apologize_and_share(world, hero, sibling, obj)
    ending(world, hero, sibling, obj)
    world.facts.update(hero=hero, sibling=sibling, parent=parent, obj=obj, obj_cfg=obj_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    sibling = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sibling")
    obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obj_cfg")
    return [
        f'Write a gentle bedtime story for a small child about sharing a {obj.label}.',
        f"Tell a bedtime story where {hero.id} and {sibling.id} have a conflict over {obj.phrase} "
        f"and learn to share it.",
        f'Write a poetic story that uses the word "remorse" and ends with two children sharing at bedtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sibling, parent, obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sibling"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obj_cfg")
    return [
        QAItem(
            question=f"What was {hero.id} holding at bedtime?",
            answer=f"{hero.id} was holding {obj.phrase} and did not want to share it at first.",
        ),
        QAItem(
            question=f"Why did {sibling.id} feel hurt?",
            answer=f"{sibling.id} felt hurt because {hero.id} refused to share the {obj.label}.",
        ),
        QAItem(
            question=f"What did {parent.label} teach about sharing?",
            answer="The parent taught that cozy things can feel even nicer when they are shared.",
        ),
        QAItem(
            question=f"How did the conflict get better?",
            answer=f"{hero.id} felt remorse, made a poetic apology, and then both children shared the {obj.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing is when two or more people let each other use or enjoy the same thing together.",
        ),
        QAItem(
            question="What is remorse?",
            answer="Remorse is the sad feeling you get when you realize you hurt someone and wish you had done better.",
        ),
        QAItem(
            question="What makes bedtime feel cozy?",
            answer="Soft blankets, quiet voices, warm lights, and gentle company can make bedtime feel cozy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
kind(hero).
kind(sibling).
kind(parent).
kind(object).

conflict(H) :- refuse(H), hurt(S), sibling_of(H,S).
remorse(H) :- conflict(H).
shared(H,O) :- remorse(H), object(O).
lesson_learned(H) :- shared(H,O).
happy_end(H,S,O) :- shared(H,O), sibling_of(H,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting in SETTING_REGISTRY:
        lines.append(asp.fact("setting", setting))
    for obj_id in OBJECTS:
        lines.append(asp.fact("object", obj_id))
    lines.append(asp.fact("sibling_of", "hero", "sibling"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show remorse/1.\n#show lesson_learned/1.\n#show shared/2.\n"))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    required = {("conflict", ("hero",)), ("remorse", ("hero",)), ("lesson_learned", ("hero",)), ("shared", ("hero", "moon_pillow"))}
    if required.issubset(atoms):
        print("OK: ASP twin can derive the core bedtime story signals.")
        return 0
    print("MISMATCH: ASP twin did not derive expected signals.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    return [(s, o) for s in SETTING_REGISTRY for o in OBJECTS]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show conflict/1.\n#show remorse/1.\n#show lesson_learned/1.\n#show shared/2.\n"))
        return
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible bedtime combos.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(setting="bedroom", object="moon_pillow", name="Mia", gender="girl",
                        sibling_name="Theo", sibling_gender="boy", parent="mother", trait="stubborn"),
            StoryParams(setting="nursery", object="storybook", name="Leo", gender="boy",
                        sibling_name="Lily", sibling_gender="girl", parent="father", trait="gentle"),
            StoryParams(setting="bedroom", object="blanket", name="Nora", gender="girl",
                        sibling_name="Ben", sibling_gender="boy", parent="mother", trait="dreamy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
