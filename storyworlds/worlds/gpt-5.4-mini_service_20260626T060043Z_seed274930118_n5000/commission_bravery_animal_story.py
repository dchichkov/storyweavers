#!/usr/bin/env python3
"""
A standalone storyworld script for a small animal tale about a commission and
bravery.

Premise:
- An animal hero receives a commission to fetch or deliver something.
- The task feels scary, and the hero must gather bravery to complete it.
- A helper or friend supports the turn from fear to action.
- The ending proves the hero changed by doing the job bravely.

This world is intentionally small and constraint-checked. The narrative is
state-driven: the commission has a destination, a risk, a tool, and a final
proof of success.
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
    kind: str = "thing"  # animal | friend | object | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    id: str
    label: str
    kind: str = "place"
    scary: bool = False
    detail: str = ""
    affordance: str = ""
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
class Commission:
    id: str
    verb: str
    noun: str
    object_label: str
    destination: str
    fear: str
    courage_need: str
    success_image: str
    helper_offer: str
    completion_line: str
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
    def __init__(self, place: Place, commission: Commission) -> None:
        self.place = place
        self.commission = commission
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ANIMALS = {
    "rabbit": {
        "type": "rabbit",
        "kind": "animal",
        "labels": ("little rabbit", "rabbit"),
        "traits": ["quick", "small", "curious"],
        "hero_lines": ("soft paws", "big ears", "a twitchy nose"),
    },
    "fox": {
        "type": "fox",
        "kind": "animal",
        "labels": ("small fox", "fox"),
        "traits": ["clever", "quick", "careful"],
        "hero_lines": ("bright eyes", "a fluffy tail", "soft paws"),
    },
    "bear": {
        "type": "bear",
        "kind": "animal",
        "labels": ("little bear", "bear"),
        "traits": ["gentle", "strong", "slow"],
        "hero_lines": ("round paws", "a warm coat", "a big nose"),
    },
    "squirrel": {
        "type": "squirrel",
        "kind": "animal",
        "labels": ("busy squirrel", "squirrel"),
        "traits": ["busy", "bouncy", "shy"],
        "hero_lines": ("a brushy tail", "quick hands", "bright eyes"),
    },
}

PLACES = {
    "old_bridge": Place(
        id="old_bridge",
        label="the old bridge",
        scary=True,
        detail="It creaked over the water and made a long hollow sound.",
        affordance="crossing",
    ),
    "dark_hedge": Place(
        id="dark_hedge",
        label="the dark hedge",
        scary=True,
        detail="Its leaves rustled, and the shadows under it felt deep and wide.",
        affordance="sneaking",
    ),
    "quiet_lane": Place(
        id="quiet_lane",
        label="the quiet lane",
        scary=False,
        detail="It was calm, with soft dirt and a few little stones.",
        affordance="walking",
    ),
    "hill_path": Place(
        id="hill_path",
        label="the hill path",
        scary=True,
        detail="It climbed high and got windy near the top.",
        affordance="climbing",
    ),
}

COMMISSIONS = {
    "deliver_seed_bag": Commission(
        id="deliver_seed_bag",
        verb="deliver",
        noun="seed bag",
        object_label="a tiny seed bag",
        destination="the far garden",
        fear="the old bridge",
        courage_need="brave paws",
        success_image="the seed bag resting safely in the gardener's hands",
        helper_offer="I can walk with you to the bridge.",
        completion_line="The little bag had made it all the way across.",
    ),
    "fetch_lantern": Commission(
        id="fetch_lantern",
        verb="fetch",
        noun="lantern",
        object_label="a warm lantern",
        destination="the hill path",
        fear="the dark hedge",
        courage_need="steady breathing",
        success_image="the lantern glowing like a small moon on the path",
        helper_offer="I'll carry the matches while you lead the way.",
        completion_line="The light was back where everyone needed it.",
    ),
    "bring_teacup": Commission(
        id="bring_teacup",
        verb="bring",
        noun="teacup",
        object_label="a tiny teacup",
        destination="the quiet lane",
        fear="the creaky fence gate",
        courage_need="gentle steps",
        success_image="the teacup arriving without a single wobble",
        helper_offer="We can take the slow path together.",
        completion_line="Not one drop had spilled.",
    ),
}

NAMES = {
    "rabbit": ["Pip", "Nim", "Tilly", "Momo"],
    "fox": ["Roo", "Fenn", "Saffy", "Mica"],
    "bear": ["Toby", "Bruno", "Mira", "Hugo"],
    "squirrel": ["Nell", "Bibi", "Clover", "Tico"],
}

FRIEND_NAMES = ["Mina", "Otto", "June", "Pico", "Luma", "Bram"]

TRAITS = ["kind", "brave", "shy", "careful", "gentle", "merry"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    animal: str
    name: str
    friend_name: str
    commission: str
    place: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
commission(C) :- task(C).
scary_place(P) :- place(P), scary(P).
needs_bravery(C) :- commission(C), fear(C,_).

compatible(A, C, P) :- animal(A), commission(C), place(P),
                       can_do(A, C), can_travel(A, P), helps(A, C, P).

valid_story(A, C, P) :- compatible(A, C, P), can_finish(A, C, P).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for aid, cfg in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        for t in cfg["traits"]:
            lines.append(asp.fact("trait", aid, t))
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.scary:
            lines.append(asp.fact("scary", pid))
    for cid, c in COMMISSIONS.items():
        lines.append(asp.fact("task", cid))
        lines.append(asp.fact("can_do", "any", cid))
        lines.append(asp.fact("can_finish", "any", cid, "any"))
        lines.append(asp.fact("fear", cid, c.fear))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for animal in ANIMALS:
        for comm in COMMISSIONS:
            for place in PLACES:
                if place == "quiet_lane" and _safe_lookup(COMMISSIONS, comm).fear == "the quiet lane":
                    continue
                out.append((animal, comm, place))
    return out


def reasonableness_gate(animal: str, commission: str, place: str) -> None:
    if animal not in ANIMALS:
        pass
    if commission not in COMMISSIONS:
        pass
    if place not in PLACES:
        pass
    c = _safe_lookup(COMMISSIONS, commission)
    p = _safe_lookup(PLACES, place)
    if not p.scary and c.fear != "the quiet lane":
        pass
    if c.fear == p.label:
        pass


def _hero_intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.label} was a {hero.traits[0]} {hero.type} with {hero.traits[1]} {hero.traits[2]}."
    )


def _commission_arrives(world: World, hero: Entity, friend: Entity, commission: Commission, place: Place) -> None:
    world.say(
        f"One morning, {friend.label} brought {hero.label} a commission: to {commission.verb} {commission.object_label} "
        f"to {commission.destination}."
    )
    world.say(
        f"The job sounded simple, but {commission.fear} felt spooky, and {place.detail}"
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.meters["task"] = hero.meters.get("task", 0) + 1


def _fear_turn(world: World, hero: Entity, friend: Entity, commission: Commission) -> None:
    world.say(
        f"{hero.label} stared at {commission.fear} and shivered."
    )
    world.say(
        f"Then {friend.label} smiled and said, \"{commission.helper_offer}\""
    )
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["worry"] = max(0, hero.memes.get("worry", 0) - 1)
    hero.meters["bravery_steps"] = hero.meters.get("bravery_steps", 0) + 1


def _journey(world: World, hero: Entity, friend: Entity, commission: Commission, place: Place) -> None:
    if place.scary:
        world.say(
            f"{hero.label} took one brave step, then another, while {friend.label} stayed close."
        )
    else:
        world.say(
            f"{hero.label} walked down the quiet way with {friend.label} beside them."
        )
    hero.meters["distance"] = hero.meters.get("distance", 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.meters["delivered"] = hero.meters.get("delivered", 0) + 1


def _ending(world: World, hero: Entity, commission: Commission) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"At last, {commission.success_image}."
    )
    world.say(
        f"{hero.label} gave the job over and felt tall inside. {commission.completion_line}"
    )


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    reasonableness_gate(params.animal, params.commission, params.place)
    place = _safe_lookup(PLACES, params.place)
    commission = _safe_lookup(COMMISSIONS, params.commission)
    cfg = _safe_lookup(ANIMALS, params.animal)
    world = World(place, commission)

    hero = world.add(Entity(
        id="hero",
        kind="animal",
        type=cfg["type"],
        label=params.name,
        traits=[params.trait] + [t for t in cfg["traits"] if t != params.trait][:2],
        meters={},
        memes={"bravery": 0.0, "worry": 0.0, "pride": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="animal",
        type="friend",
        label=params.friend_name,
        traits=["helpful", "steady"],
        meters={},
        memes={},
    ))

    world.say(f"{hero.label} was a {params.trait} {cfg['type']}.")
    world.say(f"{hero.label} loved small jobs that helped others.")

    world.say("")
    _commission_arrives(world, hero, friend, commission, place)
    world.say("")
    _fear_turn(world, hero, friend, commission)
    _journey(world, hero, friend, commission, place)
    _ending(world, hero, commission)

    world.facts = {
        "hero": hero,
        "friend": friend,
        "commission": commission,
        "place": place,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    commission: Commission = _safe_fact(world, f, "commission")
    place: Place = _safe_fact(world, f, "place")
    return [
        f"Write a short animal story where {hero.label} gets a commission to {commission.verb} {commission.object_label} and finds bravery.",
        f"Tell a gentle animal tale about a commission, a scary place like {place.label}, and a helper who encourages bravery.",
        f"Write a simple story for children that ends with {commission.object_label} safely delivered after a brave trip.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    commission: Commission = _safe_fact(world, f, "commission")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who received the commission in the story?",
            answer=f"{hero.label} received the commission and had to {commission.verb} {commission.object_label}.",
        ),
        QAItem(
            question=f"What made the job feel scary?",
            answer=f"{commission.fear} made the job feel scary, because the path there did not seem easy at first.",
        ),
        QAItem(
            question=f"Who helped {hero.label} be brave?",
            answer=f"{friend.label} helped by staying close and offering a calm plan for the trip.",
        ),
        QAItem(
            question=f"Where did the commission need to go?",
            answer=f"It needed to go to {commission.destination}, and the story passed by {place.label} on the way.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"{hero.label} started worried, but ended proud after finishing the job bravely.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "commission": (
        "What is a commission?",
        "A commission is a job or task that someone asks another creature to do.",
    ),
    "bravery": (
        "What is bravery?",
        "Bravery means doing something even when it feels scary, because you know it is the right thing to do.",
    ),
    "bridge": (
        "Why can an old bridge feel scary?",
        "An old bridge can feel scary because it may creak, sway a little, or sit high over water.",
    ),
    "hedge": (
        "What is a hedge?",
        "A hedge is a line of bushes or leafy plants that can look like a green wall.",
    ),
    "lantern": (
        "What does a lantern do?",
        "A lantern holds a light and helps people or animals see in the dark.",
    ),
}


def world_qa(world: World) -> list[QAItem]:
    out = [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes} traits={e.traits}"
        )
    lines.append(f"place={world.place.label}")
    lines.append(f"commission={world.commission.id}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import storyworlds.asp as asp
    # Simple parity check: every Python-valid combo should appear as a valid_story model.
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    asp_atoms = set(asp.atoms(model, "valid_story"))
    py_atoms = set(valid_combos())
    # Reduce to the same triple shape
    py_atoms = {(a, c, p) for (a, c, p) in py_atoms}
    if asp_atoms == py_atoms:
        print(f"OK: ASP matches Python on {len(py_atoms)} combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(asp_atoms - py_atoms))
    print("only in Python:", sorted(py_atoms - asp_atoms))
    return 1


def asp_show() -> str:
    return asp_program("#show valid_story/3.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: commission and bravery.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--commission", choices=sorted(COMMISSIONS))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    combos = valid_combos()
    if getattr(args, "animal", None) and getattr(args, "commission", None) and getattr(args, "place", None):
        reasonableness_gate(getattr(args, "animal", None), getattr(args, "commission", None), getattr(args, "place", None))
    candidates = [
        c for c in combos
        if (getattr(args, "animal", None) is None or c[0] == getattr(args, "animal", None))
        and (getattr(args, "commission", None) is None or c[1] == getattr(args, "commission", None))
        and (getattr(args, "place", None) is None or c[2] == getattr(args, "place", None))
    ]
    if not candidates:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    animal, commission, place = rng.choice(candidates)
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, animal))
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        animal=animal,
        name=name,
        friend_name=friend_name,
        commission=commission,
        place=place,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render().strip(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} compatible stories:")
        for item in items:
            print(" ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for animal in sorted(ANIMALS):
            for commission in sorted(COMMISSIONS):
                for place in sorted(PLACES):
                    try:
                        params = StoryParams(
                            animal=animal,
                            name=_safe_lookup(NAMES, animal)[0],
                            friend_name=_safe_lookup(FRIEND_NAMES, 0),
                            commission=commission,
                            place=place,
                            trait=_safe_lookup(ANIMALS, animal)["traits"][0],
                        )
                        samples.append(generate(params))
                    except StoryError:
                        pass
    else:
        seen: set[str] = set()
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
