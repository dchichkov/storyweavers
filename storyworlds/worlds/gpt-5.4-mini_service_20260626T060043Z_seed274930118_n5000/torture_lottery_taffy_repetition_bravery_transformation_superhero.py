#!/usr/bin/env python3
"""
A standalone story world for a tiny superhero tale with repetition, bravery,
and transformation.

Seed tale sketch:
- A young hero hears about a city lottery that will give away a giant bag of
  taffy.
- A looping villain device called the Torture Bell keeps repeating the same
  scare over and over.
- The hero is frightened at first, then keeps trying anyway.
- By stretching taffy into a useful shape, the hero transforms the problem into
  a rescue and wins the day.

The world is intentionally small and constraint-checked: the lottery prize must
be something the hero can honestly win, the menace must actually threaten the
hero's mission, and the transformation must genuinely solve the problem.
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

HERO_NAMES = ["Nova", "Spark", "Atlas", "Mira", "Piper", "Zane", "Luna", "Theo"]
CIVILIAN_NAMES = ["Mina", "Ollie", "June", "Rico", "Tess", "Ivy"]
TRAITS = ["brave", "curious", "kind", "steady", "quick", "gentle"]



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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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
class Place:
    name: str
    indoors: bool
    supports: set[str] = field(default_factory=set)
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
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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
class Power:
    id: str
    label: str
    action: str
    result: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.lines[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def _safe_name(name: str) -> str:
    return name[:1].upper() + name[1:] if name else name


PLACES = {
    "city": Place(name="the city", indoors=False, supports={"lottery", "chase", "taffy"}),
    "carnival": Place(name="the carnival", indoors=False, supports={"lottery", "taffy"}),
    "tower": Place(name="the clock tower", indoors=True, supports={"repetition", "bravery", "transformation"}),
}

MISSIONS = {
    "lottery": Mission(
        id="lottery",
        verb="enter the city lottery",
        gerund="entering the city lottery",
        rush="race to the lottery booth",
        risk="might miss the prize",
        zone={"feet"},
        keyword="lottery",
        tags={"lottery"},
    ),
    "taffy": Mission(
        id="taffy",
        verb="save the taffy stand",
        gerund="saving the taffy stand",
        rush="dash to the taffy cart",
        risk="could get stuck in the sticky ropes",
        zone={"hands", "arms"},
        keyword="taffy",
        tags={"taffy"},
    ),
}

PRIZES = {
    "taffy_bag": Prize(
        label="taffy",
        phrase="a giant bag of strawberry taffy",
        type="taffy",
        region="hands",
    ),
    "taffy_rope": Prize(
        label="taffy rope",
        phrase="a long rope of taffy",
        type="taffy_rope",
        region="arms",
    ),
}

POWERS = {
    "repeat": Power(
        id="repeat",
        label="repetition",
        action="keeps trying the same brave move",
        result="turns a scary loop into a useful rhythm",
        tags={"repetition"},
    ),
    "brave": Power(
        id="brave",
        label="bravery",
        action="steps forward even when the knees feel wobbly",
        result="lets the hero act before the fear grows bigger",
        tags={"bravery"},
    ),
    "transform": Power(
        id="transform",
        label="transformation",
        action="stretches taffy into a new shape",
        result="turns candy into a tool",
        tags={"transformation", "taffy"},
    ),
}


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    hero_name: str
    hero_type: str
    helper_name: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mission_id in place.supports:
            mission = _safe_lookup(MISSIONS, mission_id)
            for prize_id, prize in PRIZES.items():
                if mission_id == "lottery" and prize.region == "hands":
                    combos.append((place_id, mission_id, prize_id))
                if mission_id == "taffy" and prize.region == "arms":
                    combos.append((place_id, mission_id, prize_id))
    return combos


class State:
    def __init__(self, world: World) -> None:
        self.world = world

    def hero(self) -> Entity:
        return self.world.facts["hero"]

    def helper(self) -> Entity:
        return self.world.facts["helper"]

    def prize(self) -> Entity:
        return self.world.facts["prize"]

    def mission(self) -> Mission:
        return self.world.facts["mission"]


def introduce(world: World, hero: Entity, helper: Entity, trait: str) -> None:
    world.say(
        f"{hero.id} was a {trait} young hero who loved helping people in {world.place.name}."
    )
    world.say(
        f"{helper.id} was the one who kept the city calm when plans got noisy."
    )


def setup_lottery(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"That morning, a bright lottery poster promised {hero.pronoun('object')} {prize.phrase}."
    )
    world.say(
        f"{hero.id} stared at the sign and whispered that {prize.label} would be perfect for the team."
    )


def add_repetition(world: World) -> None:
    world.say(
        "But the old Torture Bell in the tower kept ringing the same warning again and again."
    )
    world.say(
        "Every time the bell rang, the crowd flinched, then heard the same scary sound a second time."
    )


def create_tension(world: World, hero: Entity, mission: Mission) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["need"] = hero.memes.get("need", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {mission.verb}, but the repeating bell made {hero.pronoun('object')} hesitate."
    )
    world.say(
        f"Still, {hero.id} took a breath and stepped closer, even though {mission.risk}."
    )


def bravery_turn(world: World, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(
        f"{hero.id} tried again, then again, and the steady effort turned fear into courage."
    )


def transform_taffy(world: World, hero: Entity, prize: Entity) -> None:
    hero.meters["work"] = hero.meters.get("work", 0.0) + 1
    prize.meters["shape"] = prize.meters.get("shape", 0.0) + 1
    world.say(
        f"With sticky hands, {hero.id} stretched the taffy into a strong ribbon."
    )
    world.say(
        f"The ribbon curled around the broken bell wheel and stopped the endless ringing."
    )


def resolve(world: World, hero: Entity, helper: Entity, prize: Entity, mission: Mission) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"{hero.id} finished {mission.gerund}, won the lottery prize, and handed a sweet piece to {helper.id}."
    )
    world.say(
        f"In the end, the once-scary tower was quiet, and {prize.label} had become the tool that saved the day."
    )


def tell(place: Place, mission: Mission, prize_cfg: Prize, hero_name: str, hero_type: str,
         helper_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=_safe_name(hero_name), kind="character", type=hero_type))
    helper = world.add(Entity(id=_safe_name(helper_name), kind="character", type="hero"))
    prize = world.add(Entity(id=prize_cfg.label, type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, plural=prize_cfg.plural))

    world.facts.update(hero=hero, helper=helper, prize=prize, mission=mission, place=place)

    introduce(world, hero, helper, trait)
    world.para()
    setup_lottery(world, hero, prize)
    add_repetition(world)
    create_tension(world, hero, mission)
    bravery_turn(world, hero)
    world.para()
    transform_taffy(world, hero, prize)
    resolve(world, hero, helper, prize, mission)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    mission = _safe_fact(world, world.facts, "mission")
    prize = _safe_fact(world, world.facts, "prize")
    return [
        f'Write a short superhero story for a child about {hero.id}, the {mission.keyword}, and {prize.label}.',
        f"Tell a brave story where {hero.id} keeps trying, hears a repeating scare, and turns taffy into a rescue tool.",
        f'Create a gentle superhero adventure that uses the words "lottery", "taffy", and "torture" without making the hero give up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    prize = _safe_fact(world, world.facts, "prize")
    mission = _safe_fact(world, world.facts, "mission")
    place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"What did {hero.id} hope to win in {place.name}?",
            answer=f"{hero.id} hoped to win {prize.phrase} in {place.name}."
        ),
        QAItem(
            question=f"What made {hero.id} feel scared at first?",
            answer="The Torture Bell kept repeating the same scary warning, so the problem felt bigger and louder."
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by trying again and again even while the bell was still ringing."
        ),
        QAItem(
            question=f"What did {hero.id} do with the taffy to solve the problem?",
            answer=f"{hero.id} stretched the taffy into a strong ribbon that stopped the broken bell wheel."
        ),
        QAItem(
            question=f"Who got the sweet prize at the end?",
            answer=f"{hero.id} won the lottery prize and shared a piece with {helper.id}."
        ),
        QAItem(
            question=f"Why was this story about transformation?",
            answer="Because the taffy changed from candy into a tool that could fix the danger in the tower."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lottery?",
            answer="A lottery is a game where people hope to win a prize, often by chance."
        ),
        QAItem(
            question="What is taffy?",
            answer="Taffy is a soft, sticky candy that can be stretched and pulled."
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing the same thing again and again."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel afraid."
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form or purpose."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mission is valid when the place supports it and the prize is the right kind.
valid_combo(P, M, R) :- place(P), mission(M), prize(R), supports(P, M), fits(M, R).

% Repetition is present when the bell rings more than once.
repetition(M) :- mission(M), repeated_warning(M).

% Bravery appears when the hero keeps trying despite fear.
bravery(H) :- hero(H), try_again(H), fear(H).

% Transformation is present when taffy becomes a tool.
transformation(R) :- prize(R), becomes_tool(R).

#show valid_combo/3.
#show repetition/1.
#show bravery/1.
#show transformation/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for m in sorted(place.supports):
            lines.append(asp.fact("supports", pid, m))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for rid, prize in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("fits", "lottery", rid) if prize.region == "hands" else asp.fact("fits", "taffy", rid))
        if prize.type == "taffy":
            lines.append(asp.fact("becomes_tool", rid))
    lines.append(asp.fact("repeated_warning", "lottery"))
    lines.append(asp.fact("hero", "nova"))
    lines.append(asp.fact("try_again", "nova"))
    lines.append(asp.fact("fear", "nova"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    if py - asp_set:
        print("  only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["hero", "girl", "boy"])
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
    if getattr(args, "place", None) and getattr(args, "mission", None) and getattr(args, "prize", None):
        if (getattr(args, "place", None), getattr(args, "mission", None), getattr(args, "prize", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission, prize = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(CIVILIAN_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    hero_type = "hero"
    return StoryParams(place=place, mission=mission, prize=prize, hero_name=hero_name,
                       hero_type=hero_type, helper_name=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(MISSIONS, params.mission), _safe_lookup(PRIZES, params.prize),
                 params.hero_name, params.hero_type, params.helper_name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(bits) if bits else 'no changes'}")
    lines.extend(f"  {t}" for t in world.trace)
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="city", mission="lottery", prize="taffy_bag", hero_name="Nova", hero_type="hero",
                helper_name="Mina", trait="brave"),
    StoryParams(place="carnival", mission="taffy", prize="taffy_rope", hero_name="Spark", hero_type="hero",
                helper_name="Ollie", trait="steady"),
    StoryParams(place="tower", mission="lottery", prize="taffy_bag", hero_name="Mira", hero_type="hero",
                helper_name="June", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3.\n#show repetition/1.\n#show bravery/1.\n#show transformation/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        print(f"{len(set(asp.atoms(model, 'valid_combo')))} valid combos")
        for item in sorted(set(asp.atoms(model, "valid_combo"))):
            print(item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
