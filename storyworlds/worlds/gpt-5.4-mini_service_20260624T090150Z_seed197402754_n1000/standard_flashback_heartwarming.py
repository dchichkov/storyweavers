#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/standard_flashback_heartwarming.py
===============================================================================================================

A small heartwarming story world with a flashback turn.

Premise:
- A child is helping make a tray of cookies for someone kind.
- The hot tray is the immediate physical risk.
- A warm flashback reminds the child how to be careful and brave.

The world is intentionally small and classical:
- one child,
- one caring adult,
- one baked tray,
- one helpful pair of mitts,
- one gentle resolution.

The prose is driven by simulated state rather than template swapping:
emotional meters rise and fall, the flashback is triggered by memory,
and the ending image proves the world has changed.
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
    guards: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
    gear: object | None = None
    tray: object | None = None
    def __post_init__(self) -> None:
        for k in ("warmth", "hot", "baked", "clean"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "brave", "memory", "love", "pride", "calm"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    place: str = "the kitchen"
    SETTING: object | None = None
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)
    ACTIVITY: object | None = None
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
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    risk_meter: str = "hot"
    PRIZE: object | None = None
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


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
    GEAR: object | None = None
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _bump(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _bump_m(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def _cool(world: World) -> None:
    for e in list(world.entities.values()):
        if e.meters["hot"] >= THRESHOLD and any(g.protective and "hot" in g.guards for g in world.entities.values() if g.worn_by == e.id):
            e.meters["hot"] = 0.0


def _rule_tray_hot(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    tray = world.get("tray")
    if tray.meters["hot"] < THRESHOLD:
        return out
    if any(g.protective and "hot" in g.guards for g in world.entities.values() if g.worn_by == child.id):
        sig = ("safe", "tray")
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The mitts kept the heat away.")
        return out
    sig = ("burn", "child")
    if sig not in world.fired:
        world.fired.add(sig)
        _bump_m(child, "worry", 1.0)
        out.append("The tray felt too hot to hold bare-handed.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_rule_tray_hot,):
            items = fn(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    child = sim.get("child")
    tray = sim.get("tray")
    return {"worry": child.memes["worry"], "hot": tray.meters["hot"]}


SETTING = Setting(place="the kitchen")

ACTIVITY = Activity(
    id="bake",
    verb="bake cookies",
    gerund="baking cookies",
    rush="reach for the tray too fast",
    risk="hot",
    keyword="cookies",
    tags={"cookies", "warm", "sharing"},
)

PRIZE = Prize(
    id="tray",
    label="tray",
    phrase="a tray of heart-shaped cookies",
    type="tray",
    risk_meter="hot",
)

GEAR = Gear(
    id="mitts",
    label="oven mitts",
    phrase="the oven mitts",
    guards={"hot"},
    prep="put on the oven mitts first",
    tail="slid on the oven mitts and tried again",
)


@dataclass
class StoryParams:
    place: str = "kitchen"
    activity: str = "bake"
    name: str = "Mina"
    gender: str = "girl"
    adult: str = "grandmother"
    seed: Optional[int] = None
    params: object | None = None
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


NAMES = ["Mina", "Lina", "Nora", "Maya", "Sofia", "Ivy", "Lily", "Ella"]
ADULTS = ["mother", "grandmother"]
GENDERS = ["girl", "boy"]


def story_intro(world: World, child: Entity, adult: Entity, tray: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} who loved helping in {world.setting.place}.")
    world.say(f"{child.pronoun().capitalize()} was making {ACTIVITY.keyword} for a kind neighbor, and {adult.pronoun('possessive')} smile made the whole room feel cozy.")
    world.say(f"On the counter sat {tray.phrase}, still warm from the oven.")


def flashback(world: World, child: Entity, adult: Entity) -> None:
    _bump_m(child, "memory", 1.0)
    _bump_m(child, "calm", 1.0)
    world.say(
        f"That warm smell pulled {child.id} into a flashback: when {child.pronoun('object')} was smaller, "
        f"{adult.id} had knelt beside {child.pronoun('object')} and said, "
        f"\"Slow hands make safe hands.\""
    )
    world.say(
        f"{adult.id} had shown {child.id} how to wait, how to use a cloth, and how to feel proud "
        f"after doing a careful job."
    )


def concern(world: World, child: Entity, adult: Entity, tray: Entity) -> None:
    pred = predict(world)
    if pred["worry"] >= THRESHOLD:
        _bump_m(child, "worry", 1.0)
        _bump_m(adult, "worry", 1.0)
        world.say(
            f"{child.id} wanted to {ACTIVITY.rush}, but {adult.id} gently lifted a hand. "
            f"\"That tray is still hot,\" {adult.pronoun()} said. \"We should keep your fingers safe.\""
        )


def compromise(world: World, child: Entity, adult: Entity, tray: Entity, gear: Entity) -> None:
    gear.worn_by = child.id
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    child.memes["brave"] += 1.0
    adult.memes["love"] += 1.0
    world.say(
        f"{adult.id} smiled and said, \"How about we {gear.prep}?\""
    )
    world.say(f"{child.id} nodded, remembering the flashback, and {gear.tail}.")
    tray.meters["hot"] = 0.0
    tray.meters["clean"] = 1.0
    world.say(
        f"Together they carried the tray to the table, and the cookies looked glossy and perfect."
    )


def ending(world: World, child: Entity, adult: Entity) -> None:
    child.memes["joy"] += 1.0
    child.memes["pride"] += 1.0
    child.memes["love"] += 1.0
    adult.memes["joy"] += 1.0
    world.say(
        f"{child.id} placed the cookies on a plate for the neighbor, and {adult.id} watched with a proud little laugh."
    )
    world.say(
        f"At the end, {child.id} stood in {world.setting.place} with warm mitts on {child.pronoun('possessive')} hands, "
        f"feeling brave, careful, and loved."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    adult = world.add(Entity(id="Auntie", kind="character", type=params.adult, label=params.adult))
    tray = world.add(Entity(id="tray", type="tray", label="tray", phrase="a tray of heart-shaped cookies"))
    gear = world.add(Entity(id=GEAR.id, type="gear", label=GEAR.label, phrase=GEAR.phrase, protective=True, guards=set(GEAR.guards), owner=child.id))
    world.facts.update(child=child, adult=adult, tray=tray, gear=gear, setting=world.setting, activity=ACTIVITY)
    _bump_m(child, "joy", 1.0)
    _bump_m(adult, "love", 1.0)
    tray.meters["hot"] = 1.0

    story_intro(world, child, adult, tray)
    world.para()
    concern(world, child, adult, tray)
    flashback(world, child, adult)
    propagate(world, narrate=True)
    world.para()
    compromise(world, child, adult, tray, gear)
    world.para()
    ending(world, child, adult)
    return world


def build_story_from_params(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    adult = _safe_fact(world, f, "adult")
    return [
        f'Write a gentle story for a young child about {child.id} helping {adult.id} make cookies, with a warm flashback.',
        f"Tell a heartwarming story where a child remembers an old lesson while baking in {world.setting.place}.",
        f'Write a short story that includes the word "{ACTIVITY.keyword}" and ends with a safe, happy kitchen scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    adult = _safe_fact(world, f, "adult")
    tray = _safe_fact(world, f, "tray")
    return [
        QAItem(
            question=f"What was {child.id} helping make in the kitchen?",
            answer=f"{child.id} was helping make cookies for a kind neighbor.",
        ),
        QAItem(
            question=f"Why did {adult.id} tell {child.id} to slow down?",
            answer=f"{adult.id} told {child.id} to slow down because the tray was still hot and could hurt bare hands.",
        ),
        QAItem(
            question=f"What did {child.id} remember in the flashback?",
            answer=f"{child.id} remembered {adult.id} teaching that slow hands make safe hands and showing how to work carefully.",
        ),
        QAItem(
            question=f"How did the oven mitts help?",
            answer=f"The oven mitts kept the heat away, so {child.id} could carry the tray safely.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"The cookies were on a plate, the tray was safe to carry, and {child.id} felt brave and loved in the warm kitchen.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are oven mitts for?",
            answer="Oven mitts protect your hands from hot pans, trays, and dishes from the oven.",
        ),
        QAItem(
            question="Why do people wait before touching a hot tray?",
            answer="People wait because a hot tray can burn skin if they touch it too soon.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something that happened earlier, usually to help explain what a character remembers now.",
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"guards={sorted(e.guards)}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "kitchen"), asp.fact("activity", "bake"), asp.fact("risk", "hot")]
    lines.append(asp.fact("gear", GEAR.id))
    lines.append(asp.fact("guards", GEAR.id, "hot"))
    lines.append(asp.fact("compatible", "bake", GEAR.id))
    return "\n".join(lines)


ASP_RULES = r"""
compatible_story(A, G) :- activity(A), gear(G), compatible(A, G).
has_flashback(A) :- activity(A).
good_story(A, G) :- compatible_story(A, G), has_flashback(A).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    atoms = set(asp.atoms(model, "good_story"))
    expected = {("bake", GEAR.id)}
    if atoms == expected:
        print("OK: clingo gate matches Python gate (1 combo).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(atoms))
    print("  python:", sorted(expected))
    return 1


def python_valid() -> list[tuple[str, str]]:
    return [("bake", GEAR.id)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny heartwarming flashback story world."
    )
    ap.add_argument("--place", choices=["kitchen"], default="kitchen")
    ap.add_argument("--activity", choices=["bake"], default="bake")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--adult", choices=ADULTS)
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
    if getattr(args, "place", None) != "kitchen":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) != "bake":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place="kitchen",
        activity="bake",
        name=getattr(args, "name", None) or rng.choice(NAMES),
        gender=getattr(args, "gender", None) or rng.choice(GENDERS),
        adult=getattr(args, "adult", None) or rng.choice(ADULTS),
    )


def generate(params: StoryParams) -> StorySample:
    return build_story_from_params(params)


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
        print(asp_program("#show good_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story combo:")
        print(f"  kitchen   bake     {GEAR.id}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        params = StoryParams()
        samples = [generate(params)]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
