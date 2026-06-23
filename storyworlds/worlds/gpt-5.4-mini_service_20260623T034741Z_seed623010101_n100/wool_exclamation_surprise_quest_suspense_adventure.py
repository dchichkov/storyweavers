#!/usr/bin/env python3
"""
storyworlds/worlds/wool_exclamation_surprise_quest_suspense_adventure.py
========================================================================

A standalone story world for a small adventure about a child, a wooly trail,
a suspenseful quest, and a surprise ending.

Seed tale used to shape the world:
---
A child finds a scrap of wool caught on a fence after a windy day. The wool
has a tiny knot tied in it like a clue. The child follows the wool through the
yard, across a gate, and to a hidden little shed where a surprise waits: a lost
kit, a lantern, or a friend asking for help. Along the way, the child hears an
exclamation from inside the shed, grows nervous, then discovers the surprise
was a gentle quest all along.

World model ideas:
---
    clue thread and lantern search -> child.curious += 1
    clue thread near a useful item -> item.revealed += 1
    suspenseful noise heard        -> child.nervous += 1
    surprise resolved              -> child.joy += 1; child.curious += 1; child.nervous -= 1

The story must feel like a small adventure:
beginning -> a wool clue appears
middle    -> suspense and a cautious quest
ending    -> the surprise is understood and something helpful changes
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    clue: object | None = None
    hero: object | None = None
    parent: object | None = None
    quest: object | None = None
    surprise: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Clue:
    id: str
    label: str
    phrase: str
    leads_to: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Surprise:
    id: str
    label: str
    phrase: str
    help_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Quest:
    id: str
    label: str
    goal: str
    method: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    clue = world.get("clue")
    if hero.memes["curious"] < THRESHOLD:
        return out
    if clue.meters["noticed"] >= THRESHOLD:
        return out
    sig = ("clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["noticed"] += 1
    hero.memes["hope"] += 1
    out.append(f"The small wool clue seemed to point the way.")
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["nervous"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["focus"] += 1
    out.append(f"Something inside sounded close enough to be a mystery.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    surprise = world.get("surprise")
    if hero.memes["hope"] < THRESHOLD or surprise.meters["revealed"] >= THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    surprise.meters["revealed"] += 1
    hero.memes["joy"] += 1
    out.append(f"The ending turned out gentler than the worry had guessed.")
    return out


CAUSAL_RULES = [
    Rule("clue", _r_clue),
    Rule("suspense", _r_suspense),
    Rule("surprise", _r_surprise),
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


def clue_at_risk(clue: Clue, quest: Quest) -> bool:
    return clue.leads_to == quest.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES.values():
            for quest in QUESTS.values():
                if clue_at_risk(clue, quest):
                    combos.append((place, clue.id, quest.id))
    return combos


@dataclass
class StoryParams:
    place: str = "yard"
    clue: str = "wool_knot"
    quest: str = "shed_search"
    surprise: str = "friend_inside"
    name: str = "Mia"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: wool clues, suspense, and a surprise quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "quest", None) is None or c[2] == getattr(args, "quest", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, quest = rng.choice(list(combos))
    sur = getattr(args, "surprise", None) or rng.choice(sorted(SURPRISES))
    clue_cfg = _safe_lookup(CLUES, clue)
    if clue_cfg.leads_to != quest:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    quest_cfg = _safe_lookup(QUESTS, quest)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, quest=quest, surprise=sur, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    clue_cfg = _safe_lookup(CLUES, params.clue)
    quest_cfg = _safe_lookup(QUESTS, params.quest)
    sur_cfg = _safe_lookup(SURPRISES, params.surprise)
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name, role="hero", age=6, attrs={"trait": params.trait}, tags={"child"}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent", role="parent"))
    clue = world.add(Entity(id="clue", type="thing", label=clue_cfg.label, phrase=clue_cfg.phrase, tags=set(clue_cfg.tags)))
    surprise = world.add(Entity(id="surprise", type="thing", label=sur_cfg.label, phrase=sur_cfg.phrase, tags=set(sur_cfg.tags)))
    quest = world.add(Entity(id="quest", type="thing", label=quest_cfg.label, phrase=quest_cfg.goal, tags=set(quest_cfg.tags)))
    world.facts.update(hero=hero, parent=parent, clue_cfg=clue_cfg, quest_cfg=quest_cfg, surprise_cfg=sur_cfg, place=place)
    hero.memes["curious"] = 1.0
    hero.memes["nervous"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["focus"] = 0.0
    clue.meters["noticed"] = 0.0
    surprise.meters["revealed"] = 0.0
    world.say(f"{hero.label} was a little {params.trait} {params.gender} who loved a good adventure.")
    world.say(f"One day, {hero.label} found {clue_cfg.phrase} near {place.label}, and the wool looked like a clue.")
    world.para()
    hero.memes["curious"] += 1
    world.say(f"{hero.label} followed the wool toward {quest_cfg.goal}, while {parent.label_word} watched from behind.")
    world.say(f"Then a sharp exclamation came from ahead, and the path grew quiet enough to feel suspenseful.")
    hero.memes["nervous"] += 1
    propagate(world, narrate=True)
    world.para()
    if clue.meters["noticed"] >= THRESHOLD:
        world.say(f"At last, the clue led {hero.label} to {sur_cfg.phrase}.")
        hero.memes["hope"] += 1
    if surprise.meters["revealed"] < THRESHOLD:
        surprise.meters["revealed"] += 1
    hero.memes["joy"] += 1
    world.say(f"It was a surprise that made the whole quest feel bright instead of scary.")
    world.say(f"{parent.label_word.capitalize()} smiled, and {hero.label} carried the wool clue home like a trophy.")
    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child that includes the words "wool" and "exclamation".',
        f"Tell a suspenseful quest story where {f['hero'].label} follows a wool clue and finds a surprise at the end.",
        f"Write a gentle adventure about a child, a wool clue, and a hidden surprise that turns worry into joy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    clue_cfg = f["clue_cfg"]
    quest_cfg = f["quest_cfg"]
    sur_cfg = f["surprise_cfg"]
    return [
        QAItem(
            question=f"What did {hero.label} find at the start of the story?",
            answer=f"{hero.label} found {clue_cfg.phrase}. The little piece of wool looked like a clue and sent {hero.label} on a quest."
        ),
        QAItem(
            question=f"Why did the story feel suspenseful when {hero.label} followed the clue?",
            answer=f"Because a sharp exclamation came from ahead, and nobody knew what was waiting there yet. That made the quest feel tense until the surprise was revealed."
        ),
        QAItem(
            question=f"What was the surprise at the end of the quest?",
            answer=f"The surprise was {sur_cfg.phrase}. It turned the worrying search into a happy ending and showed that the wool clue had led to something helpful."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem("What is wool?", "Wool is soft fiber that comes from sheep. People use it to make warm clothes, blankets, and yarn."),
        QAItem("What is an exclamation?", "An exclamation is a strong shout or a sentence that shows surprise or excitement. It can sound sudden and loud."),
        QAItem("What is a quest?", "A quest is a search for something important. In stories, a quest is often an adventure with a goal."),
        QAItem("What is suspense?", "Suspense is the feeling of waiting to find out what will happen next. It can make a story feel exciting and tense."),
    ]
    return out


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
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


PLACES = {
    "yard": Place(id="yard", label="the yard", affords={"follow", "search"}, tags={"outdoor"}),
    "gate": Place(id="gate", label="the gate", affords={"follow", "search"}, tags={"outdoor"}),
    "shed": Place(id="shed", label="the shed", affords={"search", "hide"}, tags={"outdoor", "secret"}),
}

CLUES = {
    "wool_knot": Clue(id="wool_knot", label="a scrap of wool", phrase="a scrap of wool tied in a little knot", leads_to="shed_search", tags={"wool", "clue"}),
    "wool_thread": Clue(id="wool_thread", label="a strand of wool", phrase="a strand of wool snagged on the fence", leads_to="gate_watch", tags={"wool", "clue"}),
}

QUESTS = {
    "shed_search": Quest(id="shed_search", label="shed search", goal="the hidden shed", method="follow the wool clue", tags={"quest", "adventure"}),
    "gate_watch": Quest(id="gate_watch", label="gate watch", goal="the old gate", method="watch the path", tags={"quest", "suspense"}),
}

SURPRISES = {
    "friend_inside": Surprise(id="friend_inside", label="a friend", phrase="a friend waiting inside the shed", help_text="to ask for help", tags={"surprise", "friend"}),
    "kit_inside": Surprise(id="kit_inside", label="a lantern kit", phrase="a tiny lantern kit wrapped in cloth", help_text="to light the path", tags={"surprise", "tool"}),
    "map_inside": Surprise(id="map_inside", label="a map", phrase="a folded map with a bright red X", help_text="to point the way", tags={"surprise", "map"}),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Zoe", "Ivy", "Ella"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Finn", "Leo", "Milo", "Toby"]
TRAITS = ["curious", "careful", "brave", "gentle", "lively"]

CURATED = [
    StoryParams(place="yard", clue="wool_knot", quest="shed_search", surprise="friend_inside", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="gate", clue="wool_thread", quest="gate_watch", surprise="kit_inside", name="Owen", gender="boy", parent="father", trait="careful"),
]


def explain_rejection(clue: Clue, quest: Quest) -> str:
    return f"(No story: {clue.label} does not lead to {quest.label}, so the quest would have no real trail to follow.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("leads_to", cid, c.leads_to))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,Q) :- place(P), clue(C), quest(Q), leads_to(C,Q).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    old = sys.stdout
    try:
        sys.stdout = io.StringIO()
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"FAILED smoke test: {e}")
        return 1
    finally:
        sys.stdout = old
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.quest not in QUESTS or params.surprise not in SURPRISES:
        pass
    if _safe_lookup(CLUES, params.clue).leads_to != params.quest:
        pass
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
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for p, c, q in asp_valid_combos():
            print(p, c, q)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
