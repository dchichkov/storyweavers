#!/usr/bin/env python3
"""
storyworlds/worlds/yule_cautionary_sharing_mystery_to_solve_ghost.py
=====================================================================

A small story world for a ghost-story-flavored yule tale with cautionary
warnings, a sharing problem, and a mystery that gets solved by careful kindness.

Premise:
- A child and a grandparent prepare for yule night in a snowy village.
- A shy ghost seems to be frightening the household by moving small things.
- The child is warned not to wander onto thin ice near the frozen pond.
- The solution is not bravery-by-ignoring-warnings, but sharing warm yule food
  and following a helpful clue to discover the ghost's true need.

The simulation keeps the story grounded in world state:
- Physical meters track cold, wet, hunger, light, and tidiness.
- Emotional memes track fear, caution, kindness, trust, and mystery.
- The mystery is solved by tracing what the ghost moved and why.
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
    kind: str = "thing"  # "character" | "ghost" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    visible: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cold": 0.0, "wet": 0.0, "hunger": 0.0, "tidy": 0.0, "light": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "caution": 0.0, "kindness": 0.0, "trust": 0.0, "mystery": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "mom", "grandmother", "woman"}
        male = {"boy", "father", "dad", "grandfather", "man"}
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
class Place:
    id: str
    label: str
    indoors: bool = False
    cold: float = 0.0
    affords: set[str] = field(default_factory=set)
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    location: str = ""
    carried_by: Optional[str] = None
    visible: bool = True
    edible: bool = False
    shareable: bool = False
    warm: bool = False
    clues: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"crumbed": 0.0, "warmth": 0.0, "empty": 0.0}
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_object(self, o: ObjectThing) -> ObjectThing:
        self.objects[o.id] = o
        return o

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.objects = _copy.deepcopy(self.objects)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village_square": Place(
        id="village_square",
        label="the village square",
        indoors=False,
        cold=1.0,
        affords={"walk", "gather", "share"},
    ),
    "snow_path": Place(
        id="snow_path",
        label="the snowy path",
        indoors=False,
        cold=2.0,
        affords={"walk", "search"},
    ),
    "old_cottage": Place(
        id="old_cottage",
        label="the old cottage",
        indoors=True,
        cold=0.5,
        affords={"share", "listen", "warm"},
    ),
    "frozen_pond": Place(
        id="frozen_pond",
        label="the frozen pond",
        indoors=False,
        cold=3.0,
        affords={"walk", "search"},
    ),
}

CHARACTER_KINDS = {
    "child": {"type": "girl", "label": "a child", "name": ["Mina", "Lena", "Iris", "Nora"]},
    "boy": {"type": "boy", "label": "a child", "name": ["Owen", "Finn", "Theo", "Eli"]},
}

GHOSTS = {
    "tink": {
        "label": "a small ghost named Tink",
        "phrase": "a small, shy ghost",
        "mood": "shy",
        "trouble": "hid the yule spoon",
        "need": "warm crumbs",
        "clue": "tiny silver crumbs",
    },
    "moss": {
        "label": "a pale ghost named Moss",
        "phrase": "a pale, worried ghost",
        "mood": "worried",
        "trouble": "moved the candle tray",
        "need": "a share of supper",
        "clue": "a trail of sugar dust",
    },
}

YULE_GOODS = {
    "cake": {
        "label": "yule cake",
        "phrase": "a warm yule cake with raisins",
        "shareable": True,
        "warm": True,
        "clues": {"crumbs", "sweet"},
    },
    "bread": {
        "label": "bread",
        "phrase": "a loaf of brown bread",
        "shareable": True,
        "warm": False,
        "clues": {"crumbs"},
    },
    "cider": {
        "label": "cider",
        "phrase": "a pot of hot cider",
        "shareable": True,
        "warm": True,
        "clues": {"sweet", "steam"},
    },
}

WARNINGS = [
    "the ice is thin near the pond",
    "the dark path can hide cracked snow",
    "the ghostly footprints lead away from the light",
]


@dataclass
class StoryParams:
    place: str
    ghost: str
    gift: str
    child_name: str
    child_kind: str
    caregiver: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for ghost_id in GHOSTS:
            for gift_id in YULE_GOODS:
                if place.indoors and ghost_id == "moss" and gift_id == "cake":
                    combos.append((place_id, ghost_id, gift_id))
                elif not place.indoors:
                    combos.append((place_id, ghost_id, gift_id))
    return combos


def explain_rejection(place: Place, ghost_id: str, gift_id: str) -> str:
    if place.indoors and ghost_id == "moss" and gift_id != "cider":
        return (
            f"(No story: at {place.label}, the worried ghost mystery wants something warm and easy to share, "
            f"so {_safe_lookup(YULE_GOODS, gift_id)['label']} is not the best fit.)"
        )
    return "(No story: that combination does not make a clear cautionary sharing mystery.)"


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def intro(world: World, child: Entity, caregiver: Entity, ghost_name: str, gift: ObjectThing) -> None:
    world.say(
        f"On a cold yule evening, {child.id} and {caregiver.id} were ready for the feast at {world.place.label}."
    )
    world.say(
        f"{child.id} carried {gift.phrase}, because {child.pronoun('possessive')} {caregiver.type} said the night was better when everyone could share."
    )
    world.facts["gift"] = gift.id
    world.facts["child"] = child.id
    world.facts["caregiver"] = caregiver.id
    world.facts["ghost_name"] = ghost_name


def ghost_mystery(world: World, child: Entity, ghost: Entity, gift: ObjectThing) -> None:
    child.memes["mystery"] += 1
    ghost.memes["mystery"] += 1
    world.say(
        f"But then odd things began to happen: {ghost.pronoun('possessive')} little footprints crossed the floor, and the {gift.label} seemed to shift by itself."
    )
    world.say(
        f"{child.id} felt a shiver of fear, because the ghost did not wail or rattle chains; {ghost.pronoun('subject').capitalize()} only hovered near the doorway and watched the food."
    )


def caution(world: World, caregiver: Entity, child: Entity, ghost: Entity) -> None:
    child.memes["caution"] += 1
    world.say(
        f"“Do not follow the footprints onto the frozen pond,” {caregiver.id} warned. “{_safe_lookup(WARNINGS, 0).capitalize()}.”"
    )
    world.say(
        f"{child.id} nodded, even though the mystery tugged at {child.pronoun('possessive')} toes."
    )


def search_clues(world: World, child: Entity, ghost: Entity, gift: ObjectThing) -> None:
    world.say(
        f"Instead of rushing outside, {child.id} looked carefully at the floor and found {ghost.location or 'a clue'}: {ghost.phrase} had left {ghost.memes.get('clue_seen', 0) or 'tiny silver crumbs'} near the table."
    )
    world.say(
        f"The crumbs matched the {gift.label}, and that made the strange haunting feel less frightening."
    )
    child.memes["trust"] += 1


def share_food(world: World, child: Entity, caregiver: Entity, ghost: Entity, gift: ObjectThing) -> None:
    if not gift.shareable:
        pass
    child.memes["kindness"] += 1
    ghost.memes["trust"] += 1
    gift.meters["empty"] += 1.0
    ghost.meters["hunger"] = max(0.0, ghost.meters["hunger"] - 1.0)
    world.say(
        f"{child.id} broke off a piece of the {gift.label} and held it out with both hands."
    )
    world.say(
        f"“You were not trying to scare us,” {child.id} said softly. “You were trying to ask for a share.”"
    )
    world.say(
        f"The ghost drifted closer, took the warm bite, and the room felt less cold at once."
    )


def resolve(world: World, child: Entity, caregiver: Entity, ghost: Entity, gift: ObjectThing) -> None:
    child.memes["fear"] = 0.0
    ghost.memes["mystery"] = 0.0
    child.memes["mystery"] = 0.0
    world.say(
        f"At last the mystery was solved: {ghost.id} had moved the spoon only because {ghost.pronoun('subject')} was hungry and wanted to join the yule table."
    )
    world.say(
        f"{caregiver.id} smiled and set out a small bowl for the ghost, so no one had to wander onto thin ice for answers."
    )
    world.say(
        f"By the end, the {gift.label} was smaller, the house was warmer, and {child.id} watched {ghost.id} sit happily beside the lamp like a shy new guest."
    )


# ---------------------------------------------------------------------------
# Content construction
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    child = world.add_entity(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_kind,
            label="child",
            location=place.id,
        )
    )
    caregiver = world.add_entity(
        Entity(
            id=params.caregiver,
            kind="character",
            type="grandmother" if params.caregiver == "Grandma" else "grandfather",
            label=params.caregiver.lower(),
            location=place.id,
        )
    )

    ghost_info = _safe_lookup(GHOSTS, params.ghost)
    ghost = world.add_entity(
        Entity(
            id=ghost_info["label"],
            kind="ghost",
            type="ghost",
            label=ghost_info["label"],
            phrase=ghost_info["phrase"],
            location=place.id,
            visible=False,
        )
    )
    ghost.meters["hunger"] = 1.0
    ghost.memes["mystery"] = 1.0
    ghost.memes["clue_seen"] = 0.0

    gift_info = _safe_lookup(YULE_GOODS, params.gift)
    gift = world.add_object(
        ObjectThing(
            id=params.gift,
            label=gift_info["label"],
            phrase=gift_info["phrase"],
            location=place.id,
            edible=True,
            shareable=gift_info["shareable"],
            warm=gift_info["warm"],
            clues=set(gift_info["clues"]),
        )
    )

    # State-driven trace before narration
    world.facts.update(
        place=place.id,
        child=child,
        caregiver=caregiver,
        ghost=ghost,
        gift=gift,
        ghost_info=ghost_info,
    )

    intro(world, child, caregiver, ghost_info["label"], gift)
    world.para()
    ghost_mystery(world, child, ghost, gift)
    caution(world, caregiver, child, ghost)
    world.para()
    ghost.memes["clue_seen"] = 1.0
    search_clues(world, child, ghost, gift)
    share_food(world, child, caregiver, ghost, gift)
    resolve(world, child, caregiver, ghost, gift)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    caregiver: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "caregiver")
    ghost_info = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ghost_info")
    gift: ObjectThing = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gift")
    place: Place = world.place
    return [
        f'Write a short ghost story for children about yule, where {child.id} sees a mystery in {place.label} and learns to share {gift.label}.',
        f"Tell a cautionary story in which {caregiver.id} warns {child.id} not to go to the frozen pond, but the real answer to the spooky mystery is kindness.",
        f'Write a gentle ghost story with the word "yule" in it, featuring {ghost_info["label"]}, a shareable {gift.label}, and a solved mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    caregiver: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "caregiver")
    ghost: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ghost")
    gift: ObjectThing = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gift")
    qa = [
        QAItem(
            question=f"What holiday was the family getting ready for at {world.place.label}?",
            answer=(
                f"They were getting ready for yule. The night began with warm food, a cold room, and a spooky little mystery."
            ),
        ),
        QAItem(
            question=f"Why did {caregiver.id} warn {child.id} about the frozen pond?",
            answer=(
                f"{caregiver.id} warned {child.id} because the ice could be thin and unsafe. The story was cautionary, so the warning was meant to keep {child.id} away from danger."
            ),
        ),
        QAItem(
            question=f"What strange thing first made {child.id} think there was a ghost problem?",
            answer=(
                f"The first clue was that {ghost.id} left little footprints and the {gift.label} seemed to move. That made the house feel mysterious before anyone understood the reason."
            ),
        ),
        QAItem(
            question=f"How was the mystery solved in the end?",
            answer=(
                f"The mystery was solved when {child.id} shared {gift.label} with the ghost and noticed the crumbs on the floor. The ghost was hungry and wanted a place at the yule table, not a way to scare anyone."
            ),
        ),
    ]
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is yule?",
        answer="Yule is a winter celebration with warm food, lights, and time spent together.",
    ),
    QAItem(
        question="Why should people be careful around thin ice?",
        answer="Thin ice can break if someone steps on it, so it is safer to stay away from it.",
    ),
    QAItem(
        question="Why do people share food during celebrations?",
        answer="People share food to be kind, to make sure everyone has enough, and to help others feel welcome.",
    ),
    QAItem(
        question="What is a ghost story?",
        answer="A ghost story is a tale about spooky things, but it can still be gentle or silly for children.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id} ({e.kind}/{e.type}) location={e.location} visible={e.visible} "
            f"meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    for o in world.objects.values():
        lines.append(
            f"  {o.id} (object) location={o.location} edible={o.edible} shareable={o.shareable} "
            f"meters={{{', '.join(f'{k}:{v}' for k, v in o.meters.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A place is compatible with a ghost-story yule sharing mystery when it can host
% the cautionary warning, the spooky clue-search, and the final sharing scene.
compatible(P,G,F) :- place(P), ghost(G), gift(F), supports(P, warn), supports(P, search), supports(P, share).

% The mystery is solvable if the gift is shareable and the ghost is hungry.
solvable(G,F) :- ghost(G), gift(F), shareable(F), hungry(G).

% We only keep story shapes where the warning matters and the solution is social.
valid_story(P,G,F) :- compatible(P,G,F), solvable(G,F).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("supports", pid, a))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("hungry", gid))
    for fid, f in YULE_GOODS.items():
        lines.append(asp.fact("gift", fid))
        if _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "shareable"):
            lines.append(asp.fact("shareable", fid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_story_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_story_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python valid story sets:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    ghost: str
    gift: str
    child_name: str
    child_kind: str
    caregiver: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghostly yule story world with caution, sharing, and a solved mystery.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--ghost", choices=GHOSTS.keys())
    ap.add_argument("--gift", choices=YULE_GOODS.keys())
    ap.add_argument("--child-kind", choices=["child", "boy"], dest="child_kind")
    ap.add_argument("--child-name")
    ap.add_argument("--caregiver", choices=["Grandma", "Grandpa"])
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "ghost", None) is None or c[1] == getattr(args, "ghost", None))
        and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, ghost, gift = rng.choice(list(filtered))
    child_kind = getattr(args, "child_kind", None) or rng.choice(["child", "boy"])
    child_name = getattr(args, "child_name", None) or rng.choice(_safe_lookup(CHARACTER_KINDS, child_kind)["name"])
    caregiver = getattr(args, "caregiver", None) or rng.choice(["Grandma", "Grandpa"])
    return StoryParams(
        place=place,
        ghost=ghost,
        gift=gift,
        child_name=child_name,
        child_kind=child_kind,
        caregiver=caregiver,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# Curated set and CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="old_cottage", ghost="tink", gift="cake", child_name="Mina", child_kind="child", caregiver="Grandma"),
    StoryParams(place="village_square", ghost="moss", gift="bread", child_name="Owen", child_kind="boy", caregiver="Grandpa"),
    StoryParams(place="frozen_pond", ghost="tink", gift="cider", child_name="Iris", child_kind="child", caregiver="Grandma"),
    StoryParams(place="snow_path", ghost="moss", gift="cake", child_name="Theo", child_kind="boy", caregiver="Grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story shapes:")
        for p, g, f in stories:
            print(f"  {p} {g} {f}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
            header = f"### {p.child_name}: {p.place} / {p.ghost} / {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
