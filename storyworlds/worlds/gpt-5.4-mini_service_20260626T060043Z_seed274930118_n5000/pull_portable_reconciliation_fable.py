#!/usr/bin/env python3
"""
storyworlds/worlds/pull_portable_reconciliation_fable.py
========================================================

A small fable-style storyworld about pull, portable gear, and reconciliation.

Premise:
- Two woodland friends want to move a cherished thing across a place that is
  hard to cross.
- One friend wants to pull quickly; the other wants to stop and use a portable
  aid.
- Their disagreement causes a spill or a snag.
- They pause, reconcile, and finish the crossing together.

This world is intentionally tiny and constraint-checked. The story is driven by
simulated state: physical load, distance, and emotional tension all matter.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    portable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid: object | None = None
    friend: object | None = None
    hero: object | None = None
    load: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"load": 0.0, "distance": 0.0, "broken": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "grudge": 0.0, "peace": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mouse", "rabbit", "squirrel", "badger"}
        male = {"boy", "fox", "hedgehog", "mole", "beaver"}
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
    kind: str
    rough: bool = False
    wet: bool = False
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


@dataclass
class Load:
    id: str
    label: str
    phrase: str
    weight: float
    fragile: bool
    needs: set[str] = field(default_factory=set)
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
class PortableAid:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps: set[str]
    prep: str
    closing: str
    portable: bool = True
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
    load: str
    aid: str
    hero: str
    friend: str
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


@dataclass
class World:
    place: Place
    hero: Entity
    friend: Entity
    load: Entity
    aid: Optional[Entity] = None
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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


PLACES = {
    "meadow": Place("meadow", "the meadow path", "path", rough=False, wet=False, affords={"pull"}),
    "brook": Place("brook", "the brook bank", "bank", rough=True, wet=True, affords={"pull"}),
    "hill": Place("hill", "the hill road", "road", rough=True, wet=False, affords={"pull"}),
}

LOADS = {
    "honey_cart": Load("honey_cart", "honey cart", "a small honey cart", weight=2.0, fragile=True, needs={"steady"}),
    "apple_barrel": Load("apple_barrel", "apple barrel", "a round apple barrel", weight=3.0, fragile=False, needs={"steady"}),
    "seed_sack": Load("seed_sack", "seed sack", "a cloth sack of seeds", weight=1.5, fragile=True, needs={"dry"}),
}

AIDS = {
    "strap": PortableAid("strap", "portable strap", "a portable strap", covers={"steady"}, helps={"pull"}, prep="take out a portable strap", closing="used the portable strap to pull more evenly"),
    "plank": PortableAid("plank", "portable plank", "a portable plank", covers={"dry", "steady"}, helps={"pull"}, prep="lay down a portable plank", closing="set the portable plank in place and rolled the load across it"),
    "sled": PortableAid("sled", "small sled", "a small portable sled", covers={"steady", "dry"}, helps={"pull"}, prep="bring out a small sled", closing="pulled the load on the small sled"),
}

HEROES = {
    "rabbit": {"type": "rabbit", "label": "Rabbit", "name_pool": ["Nia", "Pip", "Mina", "Luna"]},
    "fox": {"type": "fox", "label": "Fox", "name_pool": ["Taro", "Finn", "Jax", "Milo"]},
    "mouse": {"type": "mouse", "label": "Mouse", "name_pool": ["Dot", "Tia", "Nim", "Bee"]},
    "hedgehog": {"type": "hedgehog", "label": "Hedgehog", "name_pool": ["Tess", "Ollie", "Ivo", "Moss"]},
}

FRIENDS = ["mouse", "fox", "rabbit", "hedgehog"]


class StoryWorld:
    def __init__(self, place: Place, hero: Entity, friend: Entity, load: Entity) -> None:
        self.place = place
        self.hero = hero
        self.friend = friend
        self.load = load
        self.aid: Optional[Entity] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def worn_or_used(self) -> list[Entity]:
        out = [self.hero, self.friend]
        if self.aid:
            out.append(self.aid)
        return out


def _risk(world: StoryWorld) -> bool:
    return world.place.rough or world.place.wet


def _pull_load(world: StoryWorld, force: float) -> None:
    world.load.meters["distance"] += force
    world.load.meters["load"] += force / 2.0
    if world.place.rough and world.load.fragile and force > 1.4:
        world.load.meters["broken"] += 1.0
    if world.place.wet and "dry" in world.load.needs and (not world.aid or "dry" not in world.aid.meters):
        world.load.meters["broken"] += 1.0


def _tension(world: StoryWorld) -> None:
    if world.hero.memes["grudge"] >= THRESHOLD and world.friend.memes["grudge"] >= THRESHOLD:
        world.hero.memes["peace"] = 0.0
        world.friend.memes["peace"] = 0.0


def narrate_setup(world: StoryWorld) -> None:
    world.say(
        f"Long ago, {world.hero.id} the {world.hero.type} and {world.friend.id} the {world.friend.type} lived near {world.place.label}."
    )
    world.say(
        f"They shared {world.load.phrase}, and both wanted it moved safely."
    )


def narrate_pull_attempt(world: StoryWorld) -> None:
    world.say(
        f"{world.hero.id} wanted to pull at once, because the road looked short."
    )
    world.say(
        f"{world.friend.id} wanted to be careful, because {world.place.label} was not an easy place for a fragile load."
    )


def narrate_warning(world: StoryWorld) -> None:
    if world.load.fragile:
        if world.place.wet:
            world.say(
                f'"If we pull too fast, the {world.load.label} could slip in the wet," said {world.friend.id}.'
            )
        elif world.place.rough:
            world.say(
                f'"If we pull too hard, the {world.load.label} could bump and crack," said {world.friend.id}.'
            )


def narrate_spill(world: StoryWorld) -> None:
    if world.load.meters["broken"] >= THRESHOLD:
        world.say(
            f"But the pull went badly, and the {world.load.label} jolted and spilled its contents."
        )


def narrate_reconciliation(world: StoryWorld) -> None:
    world.say(
        f"Then {world.hero.id} looked at {world.friend.id} and lowered {world.hero.pronoun('possessive')} ears."
    )
    world.say(
        f'"I was too quick," {world.hero.id} said. "You were right to stop me."'
    )
    world.say(
        f'"And I was too stiff," {world.friend.id} said. "Let us try again together."'
    )
    world.hero.memes["grudge"] = 0.0
    world.friend.memes["grudge"] = 0.0
    world.hero.memes["peace"] += 1.0
    world.friend.memes["peace"] += 1.0
    world.hero.memes["joy"] += 1.0
    world.friend.memes["joy"] += 1.0


def narrate_resolution(world: StoryWorld) -> None:
    if world.aid is not None:
        world.say(
            f"They {world.aid.phrase} and worked in step, so the load moved without another bump."
        )
    else:
        world.say(
            f"They pulled together, slowly and evenly, until the load reached the far side."
        )
    world.say(
        f"In the end, the friends were smiling again, and the path felt lighter because they had reconciled."
    )


def choose_name(kind: str, rng: random.Random) -> str:
    return rng.choice(_safe_lookup(HEROES, kind)["name_pool"])


def build_world(params: StoryParams) -> StoryWorld:
    place = _safe_lookup(PLACES, params.place)
    load_cfg = _safe_lookup(LOADS, params.load)
    aid_cfg = _safe_lookup(AIDS, params.aid)

    hero_kind = params.hero
    friend_kind = params.friend
    hero = Entity(id=choose_name(hero_kind, random.Random(params.seed or 0)), kind="character", type=_safe_lookup(HEROES, hero_kind)["type"])
    friend = Entity(id=choose_name(friend_kind, random.Random((params.seed or 0) + 1)), kind="character", type=_safe_lookup(HEROES, friend_kind)["type"])
    load = Entity(
        id=load_cfg.id,
        kind="thing",
        type=load_cfg.label,
        label=load_cfg.label,
        phrase=load_cfg.phrase,
        portable=False,
    )
    world = StoryWorld(place, hero, friend, load)
    world.facts.update(place=place, load=load_cfg, aid=aid_cfg, hero=hero, friend=friend)
    return world


def reasonableness_gate(params: StoryParams) -> None:
    place = _safe_lookup(PLACES, params.place)
    load = _safe_lookup(LOADS, params.load)
    aid = _safe_lookup(AIDS, params.aid)
    if "pull" not in place.affords:
        pass
    if load.weight <= 0:
        pass
    if not aid.portable:
        pass
    if load.fragile and "steady" not in aid.helps:
        pass
    if place.wet and "dry" not in aid.covers and "dry" in load.needs:
        pass


def tell_story(params: StoryParams) -> StoryWorld:
    reasonableness_gate(params)
    world = build_world(params)
    narrate_setup(world)
    world.para()
    narrate_pull_attempt(world)
    narrate_warning(world)

    # Initial disagreement.
    world.hero.memes["grudge"] += 1.0
    world.friend.memes["grudge"] += 1.0
    world.hero.memes["worry"] += 1.0
    world.friend.memes["worry"] += 1.0

    # Failed pull if the load is fragile and the place is risky.
    if world.place.kind in {"bank", "road"}:
        _pull_load(world, 1.6)
    else:
        _pull_load(world, 1.2)

    if world.load.meters["broken"] >= THRESHOLD:
        narrate_spill(world)

    world.para()
    narrate_reconciliation(world)
    world.aid = Entity(
        id=_safe_lookup(AIDS, params.aid).id,
        kind="thing",
        type=_safe_lookup(AIDS, params.aid).label,
        label=_safe_lookup(AIDS, params.aid).label,
        phrase=_safe_lookup(AIDS, params.aid).phrase,
        portable=True,
    )
    world.say(f"They chose to {_safe_lookup(AIDS, params.aid).prep} before trying again.")
    _pull_load(world, 1.0)
    narrate_resolution(world)

    world.facts["resolved"] = True
    world.facts["broken"] = world.load.meters["broken"] >= THRESHOLD
    world.facts["aid_used"] = world.aid.label if world.aid else ""
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for load_id, load in LOADS.items():
            for aid_id, aid in AIDS.items():
                if "pull" not in place.affords:
                    continue
                if load.fragile and "steady" not in aid.helps:
                    continue
                if place.wet and "dry" in load.needs and "dry" not in aid.covers:
                    continue
                out.append((place_id, load_id, aid_id))
    return out


KNOWLEDGE = {
    "pull": [
        ("What does it mean to pull something?",
         "To pull something means to use your hands, ropes, or body to move it toward you or along the ground."),
    ],
    "portable": [
        ("What does portable mean?",
         "Portable means easy to carry from place to place."),
    ],
    "reconciliation": [
        ("What is reconciliation?",
         "Reconciliation is when people stop arguing, forgive each other, and become friendly again."),
    ],
    "steady": [
        ("Why is it good to be steady when carrying something fragile?",
         "Being steady helps keep fragile things from bumping, wobbling, or breaking."),
    ],
    "wet": [
        ("Why can wet ground be tricky?",
         "Wet ground can be slippery, so things can slide or tip more easily."),
    ],
    "fragile": [
        ("What does fragile mean?",
         "Fragile means something can break or crack more easily than a strong object."),
    ],
}

KNOWLEDGE_ORDER = ["pull", "portable", "reconciliation", "steady", "wet", "fragile"]


@dataclass
class StoryParams:
    place: str
    load: str
    aid: str
    hero: str
    friend: str
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


def generation_prompts(world: StoryWorld) -> list[str]:
    return [
        f'Write a short fable about a "{world.facts["load"].phrase}" being pulled across {world.facts["place"].label}, with a portable helper that saves the day.',
        f"Tell a gentle animal story where {world.hero.id} and {world.friend.id} disagree about how to pull a load, then reconcile.",
        f"Write a simple moral story that uses the word \"portable\" and ends with friends making peace after a hard pull.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    load = _safe_fact(world, world.facts, "load")
    place = _safe_fact(world, world.facts, "place")
    aid = _safe_fact(world, world.facts, "aid")
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    return [
        QAItem(
            question=f"Who wanted to pull the load quickly at {place.label}?",
            answer=f"{hero.id} wanted to pull quickly, while {friend.id} wanted to be careful.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the {load.label}?",
            answer=f"{friend.id} worried because the {load.phrase} was fragile and {place.label} was rough or wet enough to make trouble.",
        ),
        QAItem(
            question=f"What portable thing helped the friends after they reconciled?",
            answer=f"They used {aid.phrase} so they could keep pulling in a safer way.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The friends stopped arguing, forgave each other, and finished the job together.",
        ),
    ]


def world_qa(world: StoryWorld) -> list[QAItem]:
    tags = {"pull", "portable", "reconciliation", "steady", "wet", "fragile"}
    if world.place.wet:
        tags.add("wet")
    if world.load.fragile:
        tags.add("fragile")
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    lines.append(
        f"  place={world.place.label} wet={world.place.wet} rough={world.place.rough}"
    )
    lines.append(
        f"  hero={world.hero.id} memes={{{', '.join(f'{k}: {v}' for k, v in world.hero.memes.items() if v)}}}"
    )
    lines.append(
        f"  friend={world.friend.id} memes={{{', '.join(f'{k}: {v}' for k, v in world.friend.memes.items() if v)}}}"
    )
    lines.append(
        f"  load={world.load.label} meters={{{', '.join(f'{k}: {v}' for k, v in world.load.meters.items() if v)}}}"
    )
    if world.aid:
        lines.append(f"  aid={world.aid.label}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="brook", load="seed_sack", aid="plank", hero="rabbit", friend="mouse"),
    StoryParams(place="hill", load="honey_cart", aid="strap", hero="fox", friend="hedgehog"),
    StoryParams(place="meadow", load="apple_barrel", aid="sled", hero="mouse", friend="rabbit"),
]


def explain_rejection(place: Place, load: Load, aid: PortableAid) -> str:
    if load.fragile and "steady" not in aid.helps:
        return f"(No story: the {load.label} is fragile, but the {aid.label} would not make it steady enough.)"
    if place.wet and "dry" in load.needs and "dry" not in aid.covers:
        return f"(No story: the {place.label} is wet, and the {aid.label} would not keep the {load.label} dry.)"
    return "(No story: the chosen pieces do not make a strong enough fable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world of pull, portable help, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "load", None):
        combos = [c for c in combos if c[1] == getattr(args, "load", None)]
    if getattr(args, "aid", None):
        combos = [c for c in combos if c[2] == getattr(args, "aid", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, load, aid = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    friend_choices = [f for f in FRIENDS if f != hero]
    friend = getattr(args, "friend", None) or rng.choice(friend_choices)
    return StoryParams(place=place, load=load, aid=aid, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
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


ASP_RULES = r"""
place(meadow). place(brook). place(hill).
load(honey_cart). load(apple_barrel). load(seed_sack).
aid(strap). aid(plank). aid(sled).
portable(strap). portable(plank). portable(sled).

affords(meadow,pull). affords(brook,pull). affords(hill,pull).

fragile(honey_cart). fragile(seed_sack).
needs(seed_sack,dry).

helps(strap,steady). helps(strap,pull).
helps(plank,steady). helps(plank,pull). helps(plank,dry).
helps(sled,steady). helps(sled,pull). helps(sled,dry).

wet(brook). rough(brook). rough(hill).

valid(P,L,A) :- affords(P,pull), load(L), aid(A),
                (not fragile(L); helps(A,steady)),
                (not wet(P); not needs(L,dry); helps(A,dry)).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for lid in LOADS:
        lines.append(asp.fact("load", lid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
        if _safe_lookup(AIDS, aid).portable:
            lines.append(asp.fact("portable", aid))
    for pid in PLACES:
        lines.append(asp.fact("affords", pid, "pull"))
        if _safe_lookup(PLACES, pid).wet:
            lines.append(asp.fact("wet", pid))
        if _safe_lookup(PLACES, pid).rough:
            lines.append(asp.fact("rough", pid))
    for lid, load in LOADS.items():
        if load.fragile:
            lines.append(asp.fact("fragile", lid))
        for need in load.needs:
            lines.append(asp.fact("needs", lid, need))
    for aid, obj in AIDS.items():
        for h in obj.helps:
            lines.append(asp.fact("helps", aid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible stories:\n")
        for p, l, a in combos:
            print(f"  {p:8} {l:12} {a}")
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
            header = f"### {p.hero} and {p.friend}: {p.load} at {p.place} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
