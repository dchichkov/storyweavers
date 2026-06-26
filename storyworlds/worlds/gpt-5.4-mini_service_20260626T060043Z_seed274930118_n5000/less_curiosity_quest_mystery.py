#!/usr/bin/env python3
"""
storyworlds/worlds/less_curiosity_quest_mystery.py
===================================================

A small mystery storyworld about curiosity, a quest, and learning that
sometimes less noise makes the clue easier to find.

Seed tale premise:
---
A child with a curious mind hears that a little brass key has gone missing
from a tiny museum room. The room is full of shiny objects, but the clue is
small and quiet. The child follows a simple quest: look less at the shiny
crowd, listen more, and notice the one place that feels out of place.

World idea:
- curiosity is both a strength and a risk
- a quest is a deliberate search for one missing thing
- mystery-style narration is built from clues, false leads, and a final reveal
- "less" matters because reducing noise, clutter, or hurried guessing helps
  the answer appear

This script implements a compact story domain with a single child, a guide,
a place, a missing item, and a clue trail. The story is driven by world state:
the child becomes curious, follows the quest, gets misled by clutter, then
chooses less distraction and finds the missing item in a quiet hiding place.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
LESS_TAG = "less"



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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "guide"}
        male = {"boy", "father", "dad", "man", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str
    detail: str
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
class Quest:
    id: str
    verb: str
    gerund: str
    search_style: str
    false_lead: str
    clue_word: str
    reveal_word: str
    tag: str = "mystery"
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


@dataclass
class MissingItem:
    label: str
    phrase: str
    hidden_in: str
    size: str
    kind: str = "thing"
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
class StoryParams:
    place: str
    quest: str
    missing: str
    name: str
    gender: str
    guide: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "museum": Setting(
        place="the tiny museum room",
        detail="Glass cases stood in tidy rows, and the whole room felt like it was holding its breath.",
        affords={"key_quest", "map_quest"},
    ),
    "library": Setting(
        place="the quiet library nook",
        detail="Books made soft walls around the room, and even the footsteps sounded careful.",
        affords={"key_quest", "map_quest"},
    ),
    "attic": Setting(
        place="the old attic",
        detail="Dust floated in the light like sleepy sparks, and every box seemed to keep a secret.",
        affords={"key_quest", "map_quest"},
    ),
}

QUESTS = {
    "key_quest": Quest(
        id="key_quest",
        verb="solve the missing-key mystery",
        gerund="solving the missing-key mystery",
        search_style="look less at the shiny clutter and more at the quiet corners",
        false_lead="the glittering display case",
        clue_word="quiet",
        reveal_word="key",
    ),
    "map_quest": Quest(
        id="map_quest",
        verb="solve the missing-map mystery",
        gerund="solving the missing-map mystery",
        search_style="look less at the piles and more at the tidy shelf gaps",
        false_lead="the big stack of labels",
        clue_word="gap",
        reveal_word="map",
    ),
}

MISSING_ITEMS = {
    "key": MissingItem(
        label="brass key",
        phrase="a tiny brass key",
        hidden_in="a little tin cup behind the curtain",
        size="small",
    ),
    "map": MissingItem(
        label="folded map",
        phrase="a folded paper map",
        hidden_in="inside a book with a bent corner",
        size="flat",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lina", "Ava", "Tess", "Ivy"]
BOY_NAMES = ["Eli", "Theo", "Noah", "Finn", "Max", "Leo"]
TRAITS = ["curious", "careful", "brave", "thoughtful", "quiet"]


@dataclass
class StoryParams:
    place: str
    quest: str
    missing: str
    name: str
    gender: str
    guide: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery story world: curiosity, quest, and less noise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--missing", choices=MISSING_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=["librarian", "guard", "aunt"])
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
    if getattr(args, "quest", None) and getattr(args, "missing", None):
        if getattr(args, "quest", None) == "key_quest" and getattr(args, "missing", None) != "key":
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if getattr(args, "quest", None) == "map_quest" and getattr(args, "missing", None) != "map":
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    missing = getattr(args, "missing", None) or ("key" if quest == "key_quest" else "map")
    if place not in SETTINGS or quest not in _safe_lookup(SETTINGS, place).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if missing not in MISSING_ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(["librarian", "guard", "aunt"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, missing=missing, name=name, gender=gender, guide=guide, trait=trait)


def _hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def _guide_type(guide: str) -> str:
    return {"librarian": "guide", "guard": "guard", "aunt": "woman"}[guide]


def tell(setting: Setting, quest: Quest, missing: MissingItem, hero_name: str, gender: str, guide: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=_hero_type(gender),
        traits=["little", trait],
    ))
    helper = world.add(Entity(
        id="Guide",
        kind="character",
        type=_guide_type(guide),
        label=guide,
        traits=["helpful", "patient"],
    ))
    item = world.add(Entity(
        id="Missing",
        type=missing.kind,
        label=missing.label,
        phrase=missing.phrase,
        hidden_in=missing.hidden_in,
    ))
    world.facts.update(hero=hero, helper=helper, item=item, quest=quest, missing=missing)

    hero.memes["curiosity"] = 0.0
    hero.memes["resolve"] = 0.0
    hero.memes["confidence"] = 0.0
    helper.memes["calm"] = 0.0

    world.say(
        f"{hero_name} was a little {trait} {hero.type} with a curious mind. "
        f"{hero_name} loved clues, secret corners, and any story that felt like a mystery."
    )
    world.say(
        f"One day, {hero_name} heard about {missing.phrase} that had disappeared from {setting.place}. "
        f"{hero_name}'s {guide} said there was a simple quest: {quest.verb}."
    )

    world.para()
    world.say(setting.detail)
    world.say(
        f"{hero_name} started to {quest.search_style}, because too much shiny noise could hide the answer."
    )
    hero.memes["curiosity"] += 1
    hero.memes["resolve"] += 1

    world.say(
        f"The first clue seemed to point at {quest.false_lead}, but it felt wrong. "
        f"There was too much fuss there and not enough silence."
    )
    hero.memes["confusion"] += 1

    world.para()
    world.say(
        f"{helper.label.capitalize()} leaned closer and whispered that sometimes the best way to solve a mystery was to choose less guessing and less rushing."
    )
    helper.memes["calm"] += 1
    hero.memes["less_noise"] = 1
    world.say(
        f"{hero_name} slowed down, looked less at the crowded tables, and listened for the one place that felt still."
    )

    hidden_place = missing.hidden_in
    world.say(
        f"At last, {hero_name} noticed a clue-word: {quest.clue_word}. It led to {hidden_place}."
    )
    hero.memes["confidence"] += 1

    world.para()
    world.say(
        f"There, tucked away from the bright clutter, was {missing.phrase}. "
        f"{hero_name} smiled, because the mystery had been solved by paying attention to less noise and more truth."
    )
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0

    world.say(
        f"{hero_name} brought the {missing.label} back, and the room felt lighter. "
        f"The little quest was over, and the quiet clue had won."
    )
    world.facts["resolved"] = True
    world.facts["less"] = True
    return world


def _prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    missing = _safe_fact(world, f, "missing")
    return [
        f'Write a short mystery story for a young child about "{LESS_TAG}" clues, a curious hero, and a small quest.',
        f"Tell a gentle mystery where {hero.id} tries to {quest.verb} and learns that less noise can help find {missing.phrase}.",
        f'Write a child-friendly quest story that uses the word "{LESS_TAG}" and ends with the missing item found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    quest = _safe_fact(world, f, "quest")
    missing = _safe_fact(world, f, "missing")
    place = world.setting.place
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} at {place}?",
            answer=(
                f"It is a mystery about a curious little {hero.type} named {hero.id}. "
                f"{hero.id} follows a quest to {quest.verb} and find {missing.phrase}."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} learn to do when the clue trail got noisy?",
            answer=(
                f"{hero.id} learned to choose less noise and less guessing. "
                f"That helped {hero.id} notice the quiet clue and keep going."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id} on the quest?",
            answer=(
                f"The {f['helper'].label} helped by staying calm and reminding {hero.id} that a mystery can be solved by looking carefully."
            ),
        ),
        QAItem(
            question=f"Where was {missing.phrase} found?",
            answer=(
                f"It was found in {missing.hidden_in}, after {hero.id} followed the clue-word {quest.clue_word}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more, ask questions, and look for answers.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special search or mission to find something important or solve a problem.",
        ),
        QAItem(
            question="Why can less noise help when you are looking for clues?",
            answer="Less noise can help because it makes it easier to notice small sounds, small marks, and other quiet clues.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="museum", quest="key_quest", missing="key", name="Mia", gender="girl", guide="librarian", trait="curious"),
    StoryParams(place="library", quest="map_quest", missing="map", name="Eli", gender="boy", guide="guard", trait="careful"),
    StoryParams(place="attic", quest="key_quest", missing="key", name="Nora", gender="girl", guide="aunt", trait="thoughtful"),
]


ASP_RULES = r"""
quest_place(P,Q) :- affords(P,Q).
mystery(P,Q,M) :- quest_place(P,Q), missing_item(M), clue_makes_sense(Q,M).
less_helpful(P,Q) :- mystery(P,Q,M), quiet_place(P), less_noise(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("clue_makes_sense", qid, q.reveal_word))
    for mid, m in MISSING_ITEMS.items():
        lines.append(asp.fact("missing_item", m.label))
        if m.hidden_in:
            lines.append(asp.fact("hidden_place", mid, m.hidden_in))
    lines.append(asp.fact("quiet_place", "museum"))
    lines.append(asp.fact("quiet_place", "library"))
    lines.append(asp.fact("less_noise", "key_quest"))
    lines.append(asp.fact("less_noise", "map_quest"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for q in setting.affords:
            if q == "key_quest":
                combos.append((place, q, "key"))
            if q == "map_quest":
                combos.append((place, q, "map"))
    return combos


def build_sample(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(QUESTS, params.quest),
        _safe_lookup(MISSING_ITEMS, params.missing),
        params.name,
        params.gender,
        params.guide,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_gender_ok(missing: str, gender: str) -> bool:
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    missing = getattr(args, "missing", None) or ("key" if quest == "key_quest" else "map")
    if quest not in _safe_lookup(SETTINGS, place).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if quest == "key_quest" and missing != "key":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if quest == "map_quest" and missing != "map":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(["librarian", "guard", "aunt"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, missing=missing, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - clingo_set))
    print("only clingo:", sorted(clingo_set - py))
    return 1


def build_asp_story_program() -> str:
    return asp_program("#show valid/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
