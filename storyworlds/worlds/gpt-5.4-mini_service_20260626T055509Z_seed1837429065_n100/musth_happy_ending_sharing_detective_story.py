#!/usr/bin/env python3
"""
storyworlds/worlds/musth_happy_ending_sharing_detective_story.py
=================================================================

A small detective-style story world about a careful child detective, a tricky
zoo clue, and a happy ending built through sharing.

Seed inspiration:
- musth
- Happy Ending
- Sharing
- Detective Story

The story premise is that a child detective notices a worried zoo scene: a bull
elephant is in musth, a snack basket is missing, and the clues point to a small
mix-up rather than anything scary. The turn comes when the detective follows
the evidence and realizes that sharing the snacks calms everyone down and helps
the keeper solve the problem safely.

The world keeps typed entities with physical meters and emotional memes. The
prose is generated from stateful simulation rather than from a frozen template.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    basket: object | None = None
    clues: object | None = None
    detective: object | None = None
    elephant: object | None = None
    keeper: object | None = None
    shared: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
    place: str = "the zoo"
    indoors: bool = False
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
class Case:
    id: str
    clue: str
    verb: str
    evidence: str
    turn: str
    resolution: str
    keyword: str = "musth"
    tags: set[str] = field(default_factory=set)
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
class Remedy:
    id: str
    label: str
    action: str
    safety: str
    supports: set[str] = field(default_factory=set)
    calms: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_lines: list[str] = []

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


@dataclass
class Rule:
    name: str
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


def _r_calm_from_sharing(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes.get("shared", 0) >= THRESHOLD and e.memes.get("worry", 0) >= THRESHOLD:
            sig = ("calm", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["worry"] = 0.0
            e.memes["joy"] = e.memes.get("joy", 0.0) + 1
            out.append(f"{e.label or e.id} felt calmer after the sharing.")
    return out


def _r_reveal_munch(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.entities.values() if e.kind == "character" and e.type == "girl"), None)
    basket = world.entities.get("basket")
    if detective and basket and basket.meters.get("found", 0) >= THRESHOLD:
        sig = ("reveal", basket.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["certainty"] = detective.memes.get("certainty", 0.0) + 1
            out.append("The clues all fit together at last.")
    return out


CAUSAL_RULES = [
    Rule("calm_from_sharing", _r_calm_from_sharing),
    Rule("reveal_munch", _r_reveal_munch),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_safe(case: Case, remedy: Remedy) -> bool:
    return case.id in remedy.supports and "musth" in remedy.calms


def choose_remedy(case: Case) -> Optional[Remedy]:
    for rem in REMEDIES:
        if story_safe(case, rem):
            return rem
    return None


def predict(world: World, detective: Entity, case: Case, remedy: Remedy) -> dict:
    sim = world.copy()
    detective2 = sim.get(detective.id)
    detective2.memes["worry"] += 1
    sim.get("basket").meters["found"] += 1
    remedy2 = sim.get(remedy.id)
    remedy2.memes["shared"] = 1
    propagate(sim, narrate=False)
    return {
        "calm": detective2.memes.get("worry", 0) == 0,
        "found": sim.get("basket").meters.get("found", 0) >= THRESHOLD,
    }


def introduce(world: World, detective: Entity) -> None:
    world.say(
        f"{detective.label} was a small detective who loved neat clues and careful questions."
    )
    world.say(
        f"{detective.pronoun().capitalize()} kept a notebook for every case, even the tiny ones."
    )


def setup(world: World, detective: Entity, keeper: Entity, case: Case, basket: Entity, elephant: Entity) -> None:
    world.say(
        f"One bright morning at {world.setting.place}, {detective.label} noticed a funny clue near the elephant yard."
    )
    world.say(
        f"A sign said the bull elephant was in musth, so everyone had to move slowly and stay calm."
    )
    world.say(
        f"{keeper.label} looked worried because the snack basket was missing, and {detective.label} wanted to find it."
    )
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
    elephant.memes["worry"] = elephant.memes.get("worry", 0.0) + 1
    basket.meters["missing"] = 1


def gather_clues(world: World, detective: Entity, basket: Entity, case: Case) -> None:
    world.para()
    world.say(
        f"{detective.label} followed the clues: a crumb trail, a dusty footprint, and a banana peel by the bench."
    )
    world.say(
        f"The crumbs were small, so {detective.pronoun()} knew the basket had not been stolen by a grown-up."
    )
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 1


def ask_questions(world: World, detective: Entity, keeper: Entity, elephant: Entity) -> None:
    world.say(
        f'"Who was here last?" {detective.label} asked.'
    )
    world.say(
        f'{keeper.label} said, "Two friends shared the snacks with the baby elephant, and then the basket got left near the gate."'
    )
    elephant.memes["shared"] = elephant.memes.get("shared", 0.0) + 1


def turn_and_fix(world: World, detective: Entity, keeper: Entity, basket: Entity, elephant: Entity, remedy: Remedy) -> None:
    world.para()
    world.say(
        f"{detective.label} solved the case: nobody had done anything bad."
    )
    world.say(
        f"The basket had been moved during a sharing break, and the snacks were still safe."
    )
    basket.meters["found"] += 1
    detective.memes["certainty"] = detective.memes.get("certainty", 0.0) + 1

    shared = world.add(Entity(
        id=remedy.id,
        kind="thing",
        type="snack",
        label=remedy.label,
        phrase=remedy.label,
    ))
    shared.memes["shared"] = 1
    detective.memes["shared"] = detective.memes.get("shared", 0.0) + 1
    keeper.memes["shared"] = keeper.memes.get("shared", 0.0) + 1
    elephant.memes["shared"] = elephant.memes.get("shared", 0.0) + 1

    world.say(
        f'{keeper.label} smiled and said, "Let us share the remaining bananas carefully, so everyone gets enough."'
    )
    world.say(
        f"{detective.label} helped pass out the fruit, and even the elephant settled down with a gentle trunk curl."
    )
    propagate(world, narrate=True)


def ending(world: World, detective: Entity, keeper: Entity, elephant: Entity) -> None:
    world.para()
    world.say(
        f"By sunset, the yard was tidy again, the elephant was calm, and the missing basket had been found."
    )
    world.say(
        f"{detective.label} wrote in the notebook: the best clue was sharing, and the happiest endings are the safe ones."
    )
    world.say(
        f"{keeper.label} waved goodbye while the elephant stood quietly, no longer worried, as the stars came out over the zoo."
    )
    detective.memes["joy"] = detective.memes.get("joy", 0.0) + 1
    keeper.memes["joy"] = keeper.memes.get("joy", 0.0) + 1
    elephant.memes["joy"] = elephant.memes.get("joy", 0.0) + 1


def tell(setting: Setting, case: Case, remedy: Remedy, name: str = "Mina") -> World:
    world = World(setting)
    detective = world.add(Entity(id="detective", kind="character", type="girl", label=name))
    keeper = world.add(Entity(id="keeper", kind="character", type="man", label="Mr. Hale"))
    elephant = world.add(Entity(id="elephant", kind="character", type="thing", label="Bramble"))
    basket = world.add(Entity(id="basket", kind="thing", type="thing", label="snack basket"))
    clues = world.add(Entity(id="clues", kind="thing", type="thing", label="clues"))

    world.facts.update(
        detective=detective,
        keeper=keeper,
        elephant=elephant,
        basket=basket,
        clues=clues,
        case=case,
        remedy=remedy,
    )

    introduce(world, detective)
    setup(world, detective, keeper, case, basket, elephant)
    gather_clues(world, detective, basket, case)
    ask_questions(world, detective, keeper, elephant)
    turn_and_fix(world, detective, keeper, basket, elephant, remedy)
    ending(world, detective, keeper, elephant)
    return world


SETTINGS = {
    "zoo": Setting(place="the city zoo", indoors=False, affords={"musth", "sharing", "detective"}),
    "yard": Setting(place="the elephant yard", indoors=False, affords={"musth", "sharing", "detective"}),
}

CASES = {
    "musth": Case(
        id="musth",
        clue="a sign about musth",
        verb="look carefully",
        evidence="crumbs, footprints, and a banana peel",
        turn="the basket had only been moved",
        resolution="the friends were sharing snacks safely",
        keyword="musth",
        tags={"musth", "elephant", "sharing"},
    ),
}

REMEDIES = [
    Remedy(
        id="bananas",
        label="a plate of bananas",
        action="share",
        safety="carefully",
        supports={"musth"},
        calms={"musth", "elephant"},
    ),
    Remedy(
        id="water",
        label="a cup of water",
        action="share",
        safety="gently",
        supports={"musth"},
        calms={"musth"},
    ),
]


@dataclass
class StoryParams:
    setting: str
    case: str
    remedy: str
    name: str = "Mina"
    seed: Optional[int] = None
    p: object | None = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CASES:
            for r in REMEDIES:
                if story_safe(_safe_lookup(CASES, c), r):
                    out.append((s, c, r.id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = _safe_fact(world, f, "case")  # type: ignore[assignment]
    return [
        f'Write a gentle detective story for a young child that includes the word "{case.keyword}".',
        f"Tell a short mystery where {f['detective'].label} follows clues at {world.setting.place} and ends with sharing.",
        "Write a happy-ending zoo detective story where nobody is in real danger and the clues lead to kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = _safe_fact(world, f, "detective")  # type: ignore[assignment]
    keeper: Entity = _safe_fact(world, f, "keeper")  # type: ignore[assignment]
    elephant: Entity = _safe_fact(world, f, "elephant")  # type: ignore[assignment]
    basket: Entity = _safe_fact(world, f, "basket")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who solved the mystery at {world.setting.place}?",
            answer=f"{detective.label} solved it by following the clues carefully.",
        ),
        QAItem(
            question="Why did the keeper worry at the beginning?",
            answer=f"{keeper.label} worried because the snack basket was missing and the elephant yard needed to stay calm.",
        ),
        QAItem(
            question="What made the happy ending possible?",
            answer="Sharing the bananas helped everyone calm down, and then the basket was found and the zoo became peaceful again.",
        ),
        QAItem(
            question=f"Which animal was in musth?",
            answer=f"{elephant.label} the bull elephant was in musth, so everyone had to move slowly and safely.",
        ),
        QAItem(
            question="What did the detective find out about the basket?",
            answer=f"The basket had only been moved during a sharing break, so it was not stolen.",
        ),
        QAItem(
            question="What did the notebook say at the end?",
            answer="It said the best clue was sharing, and the happiest endings are the safe ones.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and solves problems by asking careful questions.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving some of what you have to someone else so everyone can have enough.",
        ),
        QAItem(
            question="What is musth?",
            answer="Musth is a time when a bull elephant can feel very strong and must be handled carefully and safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:9} {e.type:8} {' '.join(bits)}")
    out.append(f"  fired={sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
relevant_case(C) :- case(C).
valid_story(S, C, R) :- setting(S), case(C), remedy(R), supports(R, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for rem in REMEDIES:
        lines.append(asp.fact("remedy", rem.id))
        for c in rem.supports:
            lines.append(asp.fact("supports", rem.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world with musth, sharing, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--remedy", choices=[r.id for r in REMEDIES])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "case", None) is None or c[1] == getattr(args, "case", None))
              and (getattr(args, "remedy", None) is None or c[2] == getattr(args, "remedy", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    s, c, r = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Mina", "Ivy", "Nora", "Tess"])
    return StoryParams(setting=s, case=c, remedy=r, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(CASES, params.case), next(r for r in REMEDIES if r.id == params.remedy), params.name)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for s in SETTINGS:
            for c in CASES:
                for r in REMEDIES:
                    if story_safe(_safe_lookup(CASES, c), r):
                        p = StoryParams(setting=s, case=c, remedy=r.id, name="Mina")
                        samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
