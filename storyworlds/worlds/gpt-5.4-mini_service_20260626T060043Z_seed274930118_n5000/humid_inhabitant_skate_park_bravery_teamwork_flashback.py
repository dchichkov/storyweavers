#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale skate park story about a humid
inhabitant, bravery, teamwork, and a flashback that changes the ending.

The premise:
- A small skate park is full of humid air after a warm drizzle.
- A shy inhabitant wants to cross the big bowl on a skate deck.
- A team of helpers remembers an older, braver moment and uses that memory
  to guide the present turn.

The story is generated from world state, not from a fixed paragraph. A child
hero, a prized object, a risky action, a protective/assisting plan, and a
flashback all change meters and memes as the tale unfolds.
"""

from __future__ import annotations

import argparse
import dataclasses
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0
SKATE_AREAS = ("flat", "ramp", "rail", "bowl", "bench", "deck")
HAZARDS = ("slick", "wobble", "crowd", "drop")
MOODS = ("bravery", "teamwork", "flashback", "worry", "joy", "pride")


# ---------------------------------------------------------------------------
# Entities and world state
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "skater-girl"}
        male = {"boy", "father", "dad", "man", "skater-boy"}
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
    place: str = "the skate park"
    humid: bool = True
    surfaces: tuple[str, ...] = ("flat", "ramp", "rail", "bowl")
    affords: set[str] = field(default_factory=lambda: {"roll", "trick", "ride"})
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    zone: set[str]
    keyword: str
    story_word: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "skate_park": Setting(place="the skate park", humid=True, affords={"roll", "trick", "ride"}),
}

CHALLENGES = {
    "flashback": Challenge(
        id="flashback",
        verb="cross the bowl",
        gerund="crossing the bowl",
        rush="race toward the bowl",
        hazard="drop",
        zone={"deck", "ramp", "bowl"},
        keyword="flashback",
        story_word="flashback",
        tags={"flashback", "bravery"},
    ),
    "rail": Challenge(
        id="rail",
        verb="balance on the rail",
        gerund="balancing on the rail",
        rush="dash for the rail",
        hazard="wobble",
        zone={"rail", "deck"},
        keyword="rail",
        story_word="balance",
        tags={"teamwork"},
    ),
    "ramp": Challenge(
        id="ramp",
        verb="roll down the ramp",
        gerund="rolling down the ramp",
        rush="glide toward the ramp",
        hazard="slick",
        zone={"ramp", "deck"},
        keyword="ramp",
        story_word="ramp",
        tags={"bravery", "humid"},
    ),
}

GEAR = [
    Gear(
        id="pads",
        label="knee pads",
        covers={"deck", "ramp", "bowl"},
        guards={"drop", "slick", "wobble"},
        prep="strap on the knee pads",
        tail="strapped on the knee pads",
        plural=True,
    ),
    Gear(
        id="helmet",
        label="a helmet",
        covers={"deck", "ramp", "rail", "bowl"},
        guards={"drop", "wobble"},
        prep="put on a helmet",
        tail="put on the helmet",
    ),
    Gear(
        id="friend_line",
        label="a helper line of friends",
        covers={"deck", "rail", "ramp", "bowl"},
        guards={"drop", "slick", "wobble"},
        prep="gather a helper line of friends",
        tail="made a helper line of friends",
        plural=True,
    ),
]

HERO_NAMES = ["Milo", "June", "Pip", "Mara", "Toby", "Iris", "Nico", "Lena"]
TRAITS = ["bold", "small", "spunky", "careful", "curious", "cheerful"]


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------
def challenge_at_risk(ch: Challenge, prize: Entity) -> bool:
    return prize.owner is not None and prize.worn_by == prize.owner and prize.label in {"board", "skateboard", "deck"}


def select_gear(ch: Challenge, prize: Entity) -> Optional[Gear]:
    for gear in GEAR:
        if ch.hazard in gear.guards and gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for challenge_id, ch in CHALLENGES.items():
            for prize_id, prize in PRIZES.items():
                if prize.region in ch.zone and select_gear(ch, prize):
                    combos.append((place, challenge_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Story setup content
# ---------------------------------------------------------------------------
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


PRIZES = {
    "board": Prize(label="board", phrase="a shiny skateboard", type="skateboard", region="deck"),
    "deck": Prize(label="deck", phrase="a new maple deck", type="deck", region="deck"),
}


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def _narrate_intro(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    world.say(
        f"In the humid skate park, {hero.id} was a {hero.label} inhabitant with a brave little heart and a board that gleamed like a river stone."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {prize.phrase}, and {friend.id} was the kind of friend who could spot a wobble from three ramps away."
    )


def _narrate_setup(world: World, hero: Entity, friend: Entity, ch: Challenge, prize: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"One warm afternoon, {hero.id} wanted to {ch.verb}, but the park felt slick and the bowl looked as deep as a wishing well."
    )
    world.say(
        f"{friend.id} pointed at the shine on the concrete and said the humid air could make a careful rider slip if bravery forgot teamwork."
    )
    hero.memes["bravery"] += 1
    world.facts["problem"] = ch.id
    world.facts["risk"] = ch.hazard


def _narrate_flashback(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["flashback"] += 1
    friend.memes["flashback"] += 1
    world.say(
        f"Then {hero.id} had a flashback, plain as lightning in a teacup: last summer, {friend.id} had once held the rail steady while {hero.id} learned not to freeze at the edge."
    )
    world.say(
        f"That old memory did not just sit there; it stood up, brushed the dust off its boots, and walked right into the present with a grin."
    )


def _narrate_teamwork(world: World, hero: Entity, friend: Entity, ch: Challenge) -> Gear:
    gear = select_gear(ch, world.get("board"))
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    helper = world.add(Entity(id=gear.id, type="gear", label=gear.label, plural=gear.plural))
    helper.worn_by = hero.id
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(
        f"So {friend.id} said, '{gear.prep}, and I'll stay close.'"
    )
    world.say(
        f"With {friend.id} beside {hero.id}, the brave plan felt less like a leap and more like a tug-of-war won by the whole team."
    )
    return gear


def _narrate_resolution(world: World, hero: Entity, friend: Entity, ch: Challenge, prize: Entity, gear: Gear) -> None:
    hero.meters["motion"] = 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"At last, {hero.id} rolled forward, {ch.gerund}, while {friend.id} kept pace at the side like a good lantern in the dark."
    )
    world.say(
        f"The board stayed steady, the bowl did not swallow courage, and {hero.id} crossed cleanly with a shout that rang off the ramps."
    )
    world.say(
        f"By the end, {hero.id} had {gear.tail}, {prize.label} was still sound, and the humid skate park seemed to clap with its own echo."
    )


def tell(setting: Setting, challenge: Challenge, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="skater-child", label=f"{trait}"))
    friend = world.add(Entity(id="Penny", kind="character", type="skater-child", label="steady"))
    prize = world.add(Entity(id="board", type="skateboard", label="board", phrase="a shiny skateboard", owner=hero.id, caretaker=friend.id, worn_by=hero.id))
    _narrate_intro(world, hero, friend, prize)
    world.para()
    _narrate_setup(world, hero, friend, challenge, prize)
    _narrate_flashback(world, hero, friend)
    world.para()
    gear = _narrate_teamwork(world, hero, friend, challenge)
    _narrate_resolution(world, hero, friend, challenge, prize, gear)
    world.facts.update(hero=hero, friend=friend, prize=prize, challenge=challenge, gear=gear, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ch = _safe_fact(world, f, "challenge")
    return [
        f"Write a tall-tale style story about a humid skate park inhabitant who needs bravery and teamwork to {ch.verb}.",
        f"Tell a child-sized adventure where {hero.id} remembers a flashback and then gets help from a friend at the skate park.",
        f"Write a story with the words humid, inhabitant, bravery, teamwork, and flashback that ends with a steady ride.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    ch = _safe_fact(world, f, "challenge")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small skate park inhabitant with a brave heart, and {friend.id}, who helped make the plan work.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the skate park?",
            answer=f"{hero.id} wanted to {ch.verb}. The wet, humid park made that feel tricky at first.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=f"The flashback helped {hero.id} remember an older day when {friend.id} had already helped at the rail, so teamwork could do the hard work again.",
        ),
        QAItem(
            question=f"How did bravery and teamwork change the ending?",
            answer=f"Bravery got {hero.id} rolling, and teamwork kept the ride steady. In the end, {hero.id} crossed the park without losing {hero.pronoun('possessive')} board.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does humid mean?",
            answer="Humid means the air is thick with moisture, so everything can feel warm, damp, and a little sticky.",
        ),
        QAItem(
            question="What is an inhabitant?",
            answer="An inhabitant is a person or animal that lives in a place.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the feeling that helps someone do something scary or hard anyway.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something that would be harder alone.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory of an earlier moment that shows up again during the story.",
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A challenge is at risk when its zone overlaps the prize region.
risk(C, P) :- challenge(C), prize(P), zone(C, R), region(P, R).

% Gear is compatible when it guards the hazard and covers at least one zone.
fix(G, C, P) :- gear(G), risk(C, P), guards(G, H), hazard(C, H), covers(G, R), zone(C, R).

valid_story(Place, C, P) :- setting(Place), challenge(C), prize(P), risk(C, P), fix(_, C, P).

% The tall-tale ingredients are part of the story logic.
featured(Place, C, P) :- valid_story(Place, C, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.humid:
            lines.append(asp.fact("humid", place))
        for s in setting.surfaces:
            lines.append(asp.fact("surface", place, s))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("hazard", cid, ch.hazard))
        for z in sorted(ch.zone):
            lines.append(asp.fact("zone", cid, z))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, h))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
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


CURATED = [
    StoryParams(place="skate_park", challenge="flashback", name="Milo", trait="bold"),
    StoryParams(place="skate_park", challenge="rail", name="June", trait="careful"),
    StoryParams(place="skate_park", challenge="ramp", name="Pip", trait="spunky"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale skate park storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
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
    combos = [(p, c) for p in SETTINGS for c in CHALLENGES]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "challenge", None):
        combos = [c for c in combos if c[1] == getattr(args, "challenge", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge = rng.choice(combos)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHALLENGES, params.challenge), params.name, params.trait)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
