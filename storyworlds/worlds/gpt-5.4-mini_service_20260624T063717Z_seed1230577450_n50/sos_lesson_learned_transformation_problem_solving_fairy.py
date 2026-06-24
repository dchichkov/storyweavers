#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/sos_lesson_learned_transformation_problem_solving_fairy.py
===============================================================================================================================

A tiny fairy-tale storyworld about a magical SOS, a lesson learned, and a
gentle transformation achieved through problem solving.

Premise:
- A small fairy realm faces a practical problem: something valuable is stuck,
  hidden, or out of reach.
- A childlike fairy tries one approach, calls for SOS when it fails, and then
  learns a better way.
- The story ends with a transformation in the world and in the character's
  understanding.

This world models:
- physical meters: distance, stuckness, brightness, rustle, height, etc.
- emotional memes: worry, courage, kindness, pride, relief, wisdom, etc.

The prose is state-driven: a solved problem changes the world, and the ending
proves what changed.

Contract notes:
- Self-contained stdlib script.
- Imports storyworlds/results eagerly for QAItem, StoryError, StorySample.
- Imports storyworlds/asp lazily inside ASP helpers only.
- Supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "fairy", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def display(self) -> str:
        return self.label or self.type
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


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)
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
        return None


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    obstacle: str
    zone: str
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
class Treasure:
    label: str
    phrase: str
    type: str
    zone: str
    plural: bool = False
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


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def meter_value(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme_value(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def bump_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = meter_value(ent, key) + amount


def bump_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = meme_value(ent, key) + amount


def set_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = amount


def safe_article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


SETTINGS = {
    "moon_garden": Setting("the moon garden", indoors=False, affords={"find", "lift", "cross"}),
    "lantern_hall": Setting("the lantern hall", indoors=True, affords={"find", "lift", "cross"}),
    "rose_bridge": Setting("the rose bridge", indoors=False, affords={"cross", "lift"}),
}

CHALLENGES = {
    "gate": Challenge(
        id="gate",
        verb="open the silver gate",
        gerund="opening the silver gate",
        rush="push at the silver gate",
        obstacle="the gate was stuck shut",
        zone="door",
        keyword="gate",
        tags={"metal", "stuck"},
    ),
    "bloom": Challenge(
        id="bloom",
        verb="reach the sleeping bloom",
        gerund="reaching the sleeping bloom",
        rush="stretch for the sleeping bloom",
        obstacle="the bloom was high on a vine",
        zone="high",
        keyword="bloom",
        tags={"flower", "high"},
    ),
    "bridge": Challenge(
        id="bridge",
        verb="cross the narrow bridge",
        gerund="crossing the narrow bridge",
        rush="dash onto the narrow bridge",
        obstacle="the bridge swayed over the brook",
        zone="crossing",
        keyword="bridge",
        tags={"water", "wobbly"},
    ),
}

TREASURES = {
    "crown": Treasure("crown", "a tiny gold crown", "crown", "high"),
    "key": Treasure("key", "a bright little key", "key", "door"),
    "star": Treasure("star", "a soft silver star", "star", "crossing"),
}

AIDS = [
    Aid(
        id="ribbon",
        label="a moon ribbon",
        prep="tie on a moon ribbon so the way would be easier to see",
        tail="followed the shining ribbon",
        protects={"high"},
        fixes={"find"},
    ),
    Aid(
        id="lantern",
        label="a lantern",
        prep="lifted a lantern to see the path",
        tail="walked by lantern-light",
        protects={"dark"},
        fixes={"find", "cross"},
    ),
    Aid(
        id="bridgeboard",
        label="a little bridge board",
        prep="put a little bridge board across the wobble",
        tail="crossed on the little bridge board",
        protects={"crossing"},
        fixes={"cross"},
    ),
    Aid(
        id="oil",
        label="a drop of silver oil",
        prep="touched the gate with a drop of silver oil",
        tail="turned the silver gate with a soft click",
        protects={"door"},
        fixes={"lift", "find"},
    ),
]


GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Elsa", "Faye"]
BOY_NAMES = ["Pip", "Theo", "Oren", "Jules", "Bram", "Rowan"]
TRAITS = ["brave", "curious", "gentle", "quick", "earnest", "kind"]


def challenge_needs(ch: Challenge, tr: Treasure) -> bool:
    return ch.zone == tr.zone


def select_aid(ch: Challenge) -> Optional[Aid]:
    for aid in AIDS:
        if ch.zone in aid.protects or ch.id in aid.fixes:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ch_id in setting.affords:
            ch = _safe_lookup(CHALLENGES, ch_id)
            for tr_id, tr in TREASURES.items():
                if challenge_needs(ch, tr) and select_aid(ch):
                    combos.append((place, ch_id, tr_id))
    return combos


@dataclass
class StoryParams:
    place: str
    challenge: str
    treasure: str
    name: str
    gender: str
    parent: str
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
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about SOS, lesson learned, transformation, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--treasure", choices=TREASURES)
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


def explain_rejection(ch: Challenge, tr: Treasure) -> str:
    return f"(No story: {ch.gerund} does not reasonably threaten {tr.phrase}, so there is no honest problem to solve.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "challenge", None) and getattr(args, "treasure", None):
        ch, tr = _safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(TREASURES, getattr(args, "treasure", None))
        if not challenge_needs(ch, tr):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, challenge, treasure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) if hasattr(args, "trait") and getattr(args, "trait", None) else rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, treasure=treasure, name=name, gender=gender, parent=parent, trait=trait)


def cause_sos(world: World, hero: Entity) -> None:
    bump_meme(hero, "worry")
    bump_meme(hero, "courage", 0.5)
    world.say(f"{hero.pronoun().capitalize()} called sos in a tiny voice, and the echo ran through the {world.setting.place.replace('the ', '')}.")


def predict_problem(world: World, hero: Entity, challenge: Challenge, treasure: Treasure) -> bool:
    return True


def solve_problem(world: World, hero: Entity, challenge: Challenge, treasure: Treasure, aid: Aid) -> None:
    bump_meme(hero, "wisdom")
    bump_meme(hero, "relief", 1.0)
    set_meme(hero, "worry", 0.0)
    world.say(f"{hero.pronoun().capitalize()} chose {aid.label} and used it with care.")
    world.say(f"Then {aid.tail}, and at last {treasure.phrase} could be reached safely.")


def transform(hero: Entity, treasure: Entity) -> None:
    bump_meme(hero, "kindness")
    bump_meme(hero, "wisdom", 1.0)
    treasure.meters["safe"] = 1.0


def tell_story(world: World, hero: Entity, parent: Entity, challenge: Challenge, treasure: Entity, aid: Aid) -> None:
    world.say(f"Once in {world.setting.place}, {hero.id} was a {hero.display} little {hero.type} who loved fairy chores and bright morning air.")
    world.say(f"One day, {hero.id} wanted to {challenge.verb}, but {challenge.obstacle}.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.display} warned that the way needed patience, not rushing.")
    world.para()
    world.say(f"{hero.id} tried to {challenge.rush}, and that did not work.")
    bump_meme(hero, "frustration")
    cause_sos(world, hero)
    world.say(f"After the sos, {hero.id} listened more carefully and thought about the problem.")
    world.say(f"At last, {hero.id} found {aid.label} and remembered that a gentle tool can be better than a strong push.")
    world.para()
    solve_problem(world, hero, challenge, treasure, aid)
    transform(hero, treasure)
    world.say(f"{hero.id} learned that asking for help can be wise, and that a slow answer can be the best answer.")
    world.say(f"In the end, {hero.id} was not only happier; {hero.pronoun()} was changed into a more thoughtful little helper, and {treasure.phrase} shone safely in {hero.pronoun('possessive')} hands.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about a child fairy who cries "sos" when {f["challenge"].obstacle}.',
        f"Tell a short story where {f['hero'].id} learns a lesson about asking for help and solving a problem with {f['aid'].label}.",
        f"Write a gentle tale with a transformation at the end, where {f['treasure'].phrase} is recovered safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    challenge: Challenge = f["challenge"]
    treasure: Treasure = f["treasure"]
    aid: Aid = f["aid"]
    return [
        QAItem(
            question=f"Why did {hero.id} call sos in the story?",
            answer=f"{hero.id} called sos because {challenge.obstacle}, and {hero.id} needed help solving the problem instead of pushing harder."
        ),
        QAItem(
            question=f"What helped {hero.id} solve the problem?",
            answer=f"{aid.label} helped because it matched the problem and gave {hero.id} a gentle way to reach {treasure.phrase}."
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that asking for help can be wise, and that careful problem solving works better than rushing."
        ),
        QAItem(
            question=f"How was {hero.id} transformed by the end?",
            answer=f"{hero.id} became calmer, wiser, and kinder after solving the problem and learning from the mistake."
        ),
        QAItem(
            question=f"What happened to {treasure.phrase} at the end?",
            answer=f"{treasure.phrase} was reached safely and ended up shining in {hero.pronoun('possessive')} hands."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does SOS mean?", answer="SOS is a simple call for help when someone needs urgent support."),
        QAItem(question="What is a lesson learned in a story?", answer="A lesson learned is the good idea or rule a character understands after something goes wrong."),
        QAItem(question="What is transformation in a fairy tale?", answer="Transformation means a character or situation changes in an important way by the end."),
        QAItem(question="What is problem solving?", answer="Problem solving means thinking, trying, and choosing a good way to fix a difficulty."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
challenge_needs(C, T) :- zone(C, Z), zone(T, Z).
has_aid(C) :- aid(A), fixes(A, C).
valid(Place, C, T) :- affords(Place, C), challenge_needs(C, T), has_aid(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for ch in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, ch))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("zone", cid, ch.zone))
    for tid, tr in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("zone", tid, tr.zone))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for c in sorted(aid.fixes):
            lines.append(asp.fact("fixes", aid.id, c))
        for p in sorted(aid.protects):
            lines.append(asp.fact("protects", aid.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.trait))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    treasure = world.add(Entity(id=params.treasure, type=treasure_type(params.treasure), label=params.treasure, phrase=_safe_lookup(TREASURES, params.treasure).phrase))
    aid = next(a for a in AIDS if a.id == select_aid(challenge).id)

    world.facts.update(hero=hero, parent=parent, challenge=challenge, treasure=treasure, aid=aid)

    tell_story(world, hero, parent, challenge, treasure, aid)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def treasure_type(tid: str) -> str:
    return _safe_lookup(TREASURES, tid).type


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
    StoryParams(place="moon_garden", challenge="gate", treasure="key", name="Mina", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="lantern_hall", challenge="bloom", treasure="crown", name="Pip", gender="boy", parent="father", trait="curious"),
    StoryParams(place="rose_bridge", challenge="bridge", treasure="star", name="Luna", gender="girl", parent="mother", trait="gentle"),
]


def resolve_allowed(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        pass
    place, challenge, treasure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, treasure=treasure, name=name, gender=gender, parent=parent, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/3."))
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
                params = resolve_allowed(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
