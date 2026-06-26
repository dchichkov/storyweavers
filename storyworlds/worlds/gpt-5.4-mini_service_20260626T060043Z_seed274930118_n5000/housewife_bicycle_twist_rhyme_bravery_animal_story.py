#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/housewife_bicycle_twist_rhyme_bravery_animal_story.py
===============================================================================================================================

A small story world in an Animal-Story style: a housewife, a bicycle, a tiny
problem, a brave twist, and a rhyming ending.

Premise:
- A housewife keeps her bicycle for errands and visits.
- The bicycle can wobble, snag, or lose its chain.

Turn:
- A sudden twist creates trouble.
- The housewife uses bravery and a careful rhyme-like reminder to fix it.

Resolution:
- The bicycle is made safe again.
- The ending image proves the change in the world state.

This script keeps the world small and state-driven rather than swapping nouns
into a frozen template. It also includes an inline ASP twin for the same
reasonableness checks used by the Python generator.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    ridden_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bicycle: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "housewife"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "husband"}:
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
    name: str
    affords: set[str] = field(default_factory=set)
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
class Twist:
    id: str
    label: str
    problem: str
    danger: str
    result: str
    tag: str
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
class Gear:
    id: str
    label: str
    fix: str
    protects: set[str] = field(default_factory=set)
    message: str = ""
    rhyme: str = ""
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
    def __init__(self, place: Place):
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

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    twist: str
    gear: str
    name: str
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


PLACES = {
    "lane": Place(name="the lane", affords={"wobble", "chain", "rain"}),
    "yard": Place(name="the yard", affords={"wobble", "chain"}),
    "hill": Place(name="the hill road", affords={"wobble", "rain"}),
}

TWISTS = {
    "wobble": Twist(
        id="wobble",
        label="a wobble",
        problem="wobbled",
        danger="might tip over",
        result="rode steady again",
        tag="twist",
    ),
    "chain": Twist(
        id="chain",
        label="a dropped chain",
        problem="lost its chain",
        danger="would not move",
        result="rolled smoothly again",
        tag="twist",
    ),
    "rain": Twist(
        id="rain",
        label="a rain-slick turn",
        problem="slipped on the wet path",
        danger="might skid",
        result="found a safer path",
        tag="twist",
    ),
}

GEAR = {
    "patch": Gear(
        id="patch",
        label="a tidy patch kit",
        fix="patched the problem",
        protects={"chain"},
        message="A patch can help a chain stay put.",
        rhyme="Patch the latch, and catch the match.",
    ),
    "pump": Gear(
        id="pump",
        label="a small air pump",
        fix="gave the tire more air",
        protects={"wobble"},
        message="A tire with good air is less wobbly.",
        rhyme="Pump and hum; the bike can run.",
    ),
    "cloak": Gear(
        id="cloak",
        label="a bright rain cloak",
        fix="kept the rider dry",
        protects={"rain"},
        message="Dry clothes and good balance help on wet ground.",
        rhyme="Rain goes by; stay dry, oh my.",
    ),
}

ANIMAL_STORY_NAMES = ["Mina", "Tessa", "Lila", "Nora", "Betsy", "Penny", "Ruby"]
TRAITS = ["kind", "cheerful", "brave", "gentle", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for twist_id in place.affords:
            twist = _safe_lookup(TWISTS, twist_id)
            for gear_id, gear in GEAR.items():
                if twist_id in gear.protects:
                    out.append((place_id, twist_id, gear_id))
    return out


def explain_rejection(twist: Twist, gear: Gear) -> str:
    return (
        f"(No story: {gear.label} does not honestly solve {twist.label}. "
        f"The fix must match the problem, so this combination is rejected.)"
    )


def prize_at_risk(twist: Twist) -> bool:
    return True


def select_gear(twist: Twist) -> Optional[Gear]:
    for gear in GEAR.values():
        if twist.id in gear.protects:
            return gear
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a housewife, a bicycle, a twist, a rhyme, and bravery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gear", choices=GEAR)
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
    if getattr(args, "twist", None) and getattr(args, "gear", None):
        tw, gr = _safe_lookup(TWISTS, getattr(args, "twist", None)), GEAR[getattr(args, "gear", None)]
        if tw.id not in gr.protects:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "twist", None) is None or c[1] == getattr(args, "twist", None))
        and (getattr(args, "gear", None) is None or c[2] == getattr(args, "gear", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, twist, gear = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(ANIMAL_STORY_NAMES)
    return StoryParams(place=place, twist=twist, gear=gear, name=name)


def intro(world: World, hero: Entity, bicycle: Entity) -> None:
    world.say(
        f"{hero.id} was a housewife who loved her bicycle. "
        f"{hero.pronoun('subject').capitalize()} kept it neat, bright, and ready for errands."
    )
    world.say(
        f"The bicycle was not fancy, but it was dear to {hero.pronoun('object')}; "
        f"it carried baskets, bread, and little visits across {world.place.name}."
    )


def setup(world: World, hero: Entity, bicycle: Entity, twist: Twist) -> None:
    world.say(
        f"One day, {hero.id} rode into {world.place.name} when the path gave a sudden {twist.label}."
    )
    if twist.id == "wobble":
        bicycle.meters["wobble"] += 1
        bicycle.memes["uneasy"] += 1
        world.say("The front wheel began to shimmy, and the bicycle trembled under her hands.")
    elif twist.id == "chain":
        bicycle.meters["broken"] += 1
        bicycle.memes["stuck"] += 1
        world.say("Then the chain slipped loose with a soft clink, and the bicycle would not roll.")
    else:
        bicycle.meters["slip"] += 1
        bicycle.memes["careful"] += 1
        world.say("A wet turn glistened ahead, and the bicycle needed a slower, safer way.")


def bravery_turn(world: World, hero: Entity, twist: Twist, gear: Gear) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took a deep breath. She was scared for a moment, but she stayed brave."
    )
    world.say(
        f"She remembered a small rhyme: \"{gear.rhyme}\" It was a tiny song that helped her think."
    )
    world.say(gear.message)


def fix_it(world: World, hero: Entity, bicycle: Entity, twist: Twist, gear: Gear) -> None:
    if twist.id == "wobble":
        bicycle.meters["wobble"] = 0
        bicycle.memes["uneasy"] = 0
        bicycle.meters["safe"] += 1
        world.say(
            f"Using {gear.label}, {hero.id} made the wheel steady again, and the bicycle stopped wobbling."
        )
    elif twist.id == "chain":
        bicycle.meters["broken"] = 0
        bicycle.memes["stuck"] = 0
        bicycle.meters["safe"] += 1
        world.say(
            f"With {gear.label}, {hero.id} set the chain back in place, and the bicycle rolled smoothly again."
        )
    else:
        bicycle.meters["slip"] = 0
        bicycle.memes["careful"] = 0
        bicycle.meters["safe"] += 1
        world.say(
            f"With {gear.label}, {hero.id} stayed dry enough to guide the bicycle past the wet turn."
        )
    hero.memes["relief"] += 1
    bicycle.memes["happy"] += 1
    world.say(
        f"At last, {hero.id} rode on. The bicycle moved calmly, and the lane felt bright and kind."
    )


def tell(place: Place, twist: Twist, gear: Gear, name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="housewife"))
    bicycle = world.add(Entity(id="bicycle", type="bicycle", owner=hero.id, caretaker=hero.id))
    bicycle.ridden_by = hero.id

    intro(world, hero, bicycle)
    world.para()
    setup(world, hero, bicycle, twist)
    world.para()
    bravery_turn(world, hero, twist, gear)
    fix_it(world, hero, bicycle, twist, gear)

    world.facts.update(hero=hero, bicycle=bicycle, twist=twist, gear=gear, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    twist = _safe_fact(world, f, "twist")
    gear = _safe_fact(world, f, "gear")
    return [
        f'Write a gentle animal-story-style tale about a housewife named {hero.id} and a bicycle, including the word "twist".',
        f"Tell a small bravery story where {hero.id} uses {gear.label} to solve {twist.label} on {world.place.name}.",
        f"Write a child-friendly story with rhyme and bravery where a bicycle becomes safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    twist = _safe_fact(world, f, "twist")
    gear = _safe_fact(world, f, "gear")
    bicycle = _safe_fact(world, f, "bicycle")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a housewife who cares for a bicycle.",
        ),
        QAItem(
            question=f"What problem happened to the bicycle?",
            answer=f"The bicycle had {twist.label}, which made it {twist.problem} and feel like it {twist.danger}.",
        ),
        QAItem(
            question=f"What helped {hero.id} fix the problem?",
            answer=f"{gear.label} helped {hero.id} solve the trouble, because it was the right tool for that twist.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem bravely?",
            answer=f"{hero.id} stayed brave, remembered a small rhyme, and used {gear.label} to help the bicycle recover.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the bicycle was safe again and could move calmly through {world.place.name}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bicycle for?",
            answer="A bicycle is a vehicle with two wheels that a person can ride for travel or fun.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing what needs to be done even when you feel scared.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a short, playful bit of language where words sound alike at the end.",
        ),
        QAItem(
            question="What is a housewife?",
            answer="A housewife is a person who helps care for a home and often takes care of everyday tasks there.",
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.name}")
    return "\n".join(lines)


ASP_RULES = r"""
twist_ok(P, T, G) :- place(P), twist(T), gear(G), protects(G, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for t in sorted(gear.protects):
            lines.append(asp.fact("protects", gid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show twist_ok/3.\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show twist_ok/3."))
    return sorted(set(asp.atoms(model, "twist_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TWISTS, params.twist), GEAR[params.gear], params.name)
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


def resolve(params: StoryParams, rng: random.Random) -> StoryParams:
    return params


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="lane", twist="chain", gear="patch", name="Mina"),
        StoryParams(place="yard", twist="wobble", gear="pump", name="Tessa"),
        StoryParams(place="hill", twist="rain", gear="cloak", name="Ruby"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show twist_ok/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, twist, gear) combos:\n")
        for p, t, g in triples:
            print(f"  {p:6} {t:8} {g}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in build_curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                place = getattr(args, "place", None) or rng.choice(list(PLACES))
                twist = getattr(args, "twist", None) or rng.choice([t for t in _safe_lookup(PLACES, place).affords])
                gear = getattr(args, "gear", None) or rng.choice([g for g, gg in GEAR.items() if twist in gg.protects])
                name = getattr(args, "name", None) or rng.choice(ANIMAL_STORY_NAMES)
                params = StoryParams(place=place, twist=twist, gear=gear, name=name, seed=seed)
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.name}: {p.twist} at {p.place} (gear: {p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
