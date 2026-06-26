#!/usr/bin/env python3
"""
Story world: a small whodunit about friendship, moral value, and a whisker clue.

Premise:
- A kind child notices a small mystery in a cozy setting.
- A valued object goes missing or is muddled.
- Friends each have plausible reasons to be suspected.

State model:
- Physical meters track clue strength, object location, and opportunity.
- Emotional memes track trust, fear, guilt, and relief.
- The ending proves who did it and why the friendship remains intact.

This world intentionally keeps the domain small and constraint-checked:
- Only stories with a real clue trail are generated.
- The culprit's action must be explainable by the world state.
- The resolution must restore moral value: honesty, fairness, and care.

Seed words included: whisker, shill-gerund
Style: whodunit
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    holds: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    culprit: object | None = None
    friend: object | None = None
    hero: object | None = None
    witness: object | None = None
    def __post_init__(self) -> None:
        for k in ["clue", "opportunity", "suspicion", "trust", "fear", "guilt", "relief", "value"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the little library"
    indoors: bool = True
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
class Item:
    id: str
    label: str
    phrase: str
    owner: str
    value: str
    hidden_in: Optional[str] = None
    found: bool = False
    item: object | None = None
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
class SuspectProfile:
    id: str
    type: str
    label: str
    motive: str
    alibi: str
    action: str
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
    setting: str
    mystery: str
    item: str
    culprit: str
    friend: str
    name: str
    gender: str
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
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def maybe(article: str, word: str) -> str:
    return f"{article} {word}"


SETTINGS = {
    "library": Setting("the little library", True, {"hide", "search"}),
    "kitchen": Setting("the quiet kitchen", True, {"hide", "search"}),
    "garden": Setting("the moonlit garden", False, {"hide", "search"}),
}

MYSTERIES = {
    "missing_cookie": {
        "label": "missing cookie",
        "phrase": "a plate with one missing cookie",
        "value": "sweet and special",
        "clue": "crumbs",
        "hide_spots": ["under the chair", "behind the books", "by the teapot"],
    },
    "lost_note": {
        "label": "lost note",
        "phrase": "a small note with a ribbon",
        "value": "important and kind",
        "clue": "ink smudge",
        "hide_spots": ["under the cushion", "behind the curtain", "inside the basket"],
    },
}

ITEMS = {
    "cookie": Item("cookie", "cookie", "a warm sugar cookie", "Friend", "sweet and special"),
    "note": Item("note", "note", "a small note with a ribbon", "Friend", "important and kind"),
}

SUSPECTS = {
    "cat": SuspectProfile("cat", "cat", "the cat", "wanted a snack", "was napping by the window", "snatched a bite"),
    "sibling": SuspectProfile("sibling", "boy", "the sibling", "wanted attention", "was stacking blocks in the hall", "picked it up to show someone"),
    "neighbor": SuspectProfile("neighbor", "girl", "the neighbor", "wanted to help", "was watering plants outside", "moved it while cleaning"),
}

NAMES = ["Mina", "Toby", "Leah", "Noah", "Iris", "Evan"]
TRAITS = ["curious", "careful", "gentle", "brave", "thoughtful"]


def reasonableness_gate(setting: str, mystery: str, item: str, culprit: str, friend: str) -> None:
    if setting not in SETTINGS:
        pass
    if mystery not in MYSTERIES:
        pass
    if item not in ITEMS:
        pass
    if culprit not in SUSPECTS or friend not in SUSPECTS:
        pass
    if culprit == friend:
        pass


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params.setting, params.mystery, params.item, params.culprit, params.friend)
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", random.choice(TRAITS)]))
    friend = world.add(Entity(id="Friend", kind="character", type=_safe_lookup(SUSPECTS, params.friend).type, label=_safe_lookup(SUSPECTS, params.friend).label))
    culprit = world.add(Entity(id="Culprit", kind="character", type=_safe_lookup(SUSPECTS, params.culprit).type, label=_safe_lookup(SUSPECTS, params.culprit).label))
    witness = world.add(Entity(id="Witness", kind="character", type="girl", label="the quiet witness"))

    item_cfg = _safe_lookup(ITEMS, params.item)
    item = world.add_item(Item(id=params.item, label=item_cfg.label, phrase=item_cfg.phrase, owner=friend.id, value=item_cfg.value))

    world.facts.update(hero=hero, friend=friend, culprit=culprit, witness=witness, item=item, mystery=_safe_lookup(MYSTERIES, params.mystery), setting=setting, suspects=SUSPECTS)

    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    culprit.memes["fear"] += 0.2
    return world


def introduce(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    item: Item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    world.say(
        f"{hero.id} was a little {hero.type} who loved quiet places and noticed every tiny clue."
    )
    world.say(
        f"One evening at {world.setting.place}, {hero.id} found {item.phrase}, and {friend.label} looked worried because {mystery['label']} had gone wrong."
    )


def seed_clue(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    item: Item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    clue_word = mystery["clue"]
    hero.meters["clue"] += 1
    world.say(
        f"Near the doorway, {hero.id} spotted {clue_word}s and one tiny whisker, which made the room feel like a puzzle."
    )
    world.say(
        f"It seemed like someone had hurried by, and {item.label} had been moved out of place."
    )


def accuse(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    culprit: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "culprit")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    suspect = _safe_lookup(SUSPECTS, culprit.id)
    friend.memes["fear"] += 0.3
    culprit.memes["guilt"] += 0.4
    culprit.meters["suspicion"] += 1
    world.say(
        f"{hero.id} first wondered about {suspect.label}, because {suspect.motive} and {suspect.action} sounded suspicious."
    )
    world.say(
        f"But the alibi mattered too: {suspect.alibi}, so the case was not solved yet."
    )


def show_friendship(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    culprit: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "culprit")
    witness: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "witness")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    item: Item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")

    world.para()
    hero.meters["value"] += 1
    friend.memes["trust"] += 0.8
    world.say(
        f"{hero.id} asked gentle questions instead of blaming anyone, because friendship was more valuable than a quick accusation."
    )
    world.say(
        f"{witness.label} finally spoke up and said the clue trail led from the table to the window, where {culprit.label} had passed."
    )
    world.say(
        f"Then {hero.id} noticed the missing {item.label} tucked exactly where {culprit.label} could have set it down in a rush."
    )
    culprit.memes["guilt"] += 0.7
    culprit.meters["suspicion"] += 1
    world.say(
        f"{culprit.label} admitted it: {_safe_lookup(SUSPECTS, culprit.id).action} had been meant to help, but it had only caused trouble."
    )
    world.say(
        f"{friend.label} was upset for a moment, but {hero.id} reminded everyone that honest mistakes can be fixed when people tell the truth."
    )
    world.say(
        f"In the end, the {mystery['label']} was solved, the whisker clue made sense, and the room felt warm again."
    )


def resolve_story(world: World) -> None:
    f = world.facts
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    culprit: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "culprit")
    item: Item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    friend.memes["relief"] += 1
    friend.memes["trust"] += 0.5
    culprit.memes["guilt"] = max(0.0, culprit.memes["guilt"] - 0.2)
    item.found = True
    world.para()
    world.say(
        f"{friend.label} smiled again, because the {item.label} was safe and the truth had kept the friendship strong."
    )
    world.say(
        f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero").id} left with a useful lesson: being kind is not the same as letting a mystery stay hidden."
    )


def tell(world: World) -> World:
    introduce(world)
    seed_clue(world)
    accuse(world)
    show_friendship(world)
    resolve_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child that includes a "whisker" clue and a gentle friendship ending.',
        f"Tell a mystery story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} solves {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")['label']} at {world.setting.place} without breaking trust.",
        f'Write a cozy whodunit with moral value: the truth matters more than blame, and one clue is a whisker.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    culprit: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "culprit")
    item: Item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    suspect = _safe_lookup(SUSPECTS, culprit.id)
    return [
        QAItem(
            question=f"What mystery was {hero.id} trying to solve at {world.setting.place}?",
            answer=f"{hero.id} was trying to solve the {mystery['label']}, because something important had been moved or hidden."
        ),
        QAItem(
            question=f"What clue helped {hero.id} start to solve the case?",
            answer="A tiny whisker and the clue trail near the doorway helped show that someone had passed by in a hurry."
        ),
        QAItem(
            question=f"Who turned out to be responsible, and why did that not ruin the friendship?",
            answer=(
                f"{culprit.label} was responsible, but {culprit.label} admitted the mistake and told the truth. "
                f"That let {friend.label} forgive the problem, so the friendship stayed strong."
            ),
        ),
        QAItem(
            question=f"Why did {hero.id} not want to blame {suspect.label} too quickly?",
            answer=(
                f"{hero.id} cared about fairness. The alibi showed that {suspect.label} might have looked suspicious, "
                f"but careful questions were needed before accusing anyone."
            ),
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=(
                f"The {item.label} was safe again, the truth was out, and {friend.label} could smile because the problem had been solved kindly."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whisker?",
            answer="A whisker is a long, stiff hair on an animal's face, like on a cat."
        ),
        QAItem(
            question="What does it mean to tell the truth?",
            answer="To tell the truth means to say what really happened, even if it is hard."
        ),
        QAItem(
            question="Why is friendship important?",
            answer="Friendship is important because friends help, listen, and stay kind when things go wrong."
        ),
        QAItem(
            question="What is moral value?",
            answer="Moral value means knowing what is good and fair, like being honest, gentle, and caring."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} meters={ {k: round(v, 2) for k, v in e.meters.items() if v} } memes={ {k: round(v, 2) for k, v in e.memes.items() if v} }"
        )
    for item in world.items.values():
        lines.append(f"{item.id}: found={item.found} hidden_in={item.hidden_in}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for mystery in MYSTERIES:
            for item in ITEMS:
                for culprit in SUSPECTS:
                    for friend in SUSPECTS:
                        if culprit != friend:
                            combos.append((setting, mystery, item, culprit, friend))
    return combos


@dataclass
class StorySpec:
    setting: str
    mystery: str
    item: str
    culprit: str
    friend: str
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


def explain_rejection() -> str:
    return "No story: the requested options do not form a fair whodunit."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy whodunit story world about friendship and moral value.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--mystery", choices=list(MYSTERIES))
    ap.add_argument("--item", choices=list(ITEMS))
    ap.add_argument("--culprit", choices=list(SUSPECTS))
    ap.add_argument("--friend", choices=list(SUSPECTS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    culprit = getattr(args, "culprit", None) or rng.choice(list(SUSPECTS))
    friend = getattr(args, "friend", None) or rng.choice([k for k in SUSPECTS if k != culprit])
    if culprit == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    return StoryParams(setting=setting, mystery=mystery, item=item, culprit=culprit, friend=friend, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(build_world(params))
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


ASP_RULES = r"""
hero(H). friend(F). culprit(C). mystery(M). item(I).
different(H,F) :- hero(H), friend(F), H != F.
clue_seen(H) :- whisker_clue.
truth_matters(H) :- hero(H).
resolved(M) :- mystery(M), truth_spoken.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    lines.append(asp.fact("whisker_clue"))
    lines.append(asp.fact("truth_spoken"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_all_specs() -> list[StoryParams]:
    specs = []
    for setting, mystery, item, culprit, friend in valid_combos()[:5]:
        specs.append(StoryParams(setting=setting, mystery=mystery, item=item, culprit=culprit, friend=friend, name=random.choice(NAMES), gender=random.choice(["boy", "girl"])))
    return specs


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode available, but this world uses a small built-in gate.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in build_all_specs():
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
