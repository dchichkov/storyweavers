#!/usr/bin/env python3
"""
A standalone story world for a small myth-like moral tale about candid truth,
pride, and repair.

Seed words: sup, candid
Style: Myth
Feature: Moral Value
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
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
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gift: object | None = None
    hero: object | None = None
    parent: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "maiden", "woman"}
        male = {"boy", "father", "king", "smith", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
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
class Place:
    name: str
    indoors: bool = False
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
class Gift:
    id: str
    label: str
    phrase: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Trial:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    moral: str
    keyword: str
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


@dataclass
class Remedy:
    id: str
    label: str
    covers: set[str]
    helps: str
    prep: str
    tail: str
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


@dataclass
class StoryParams:
    place: str
    trial: str
    gift: str
    name: str
    gender: str
    parent: str
    virtue: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.lines = list(self.lines)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w


PLACES = {
    "hill": Place("the hill", False, {"harp", "echo"}),
    "forest": Place("the forest", False, {"harp", "river"}),
    "temple": Place("the temple", True, {"tablet"}),
    "spring": Place("the spring", False, {"water", "echo"}),
}

TRIALS = {
    "harp": Trial(
        id="harp",
        verb="play the silver harp",
        gerund="playing the silver harp",
        rush="run to the hilltop harp",
        risk="struck a false note that broke the harmony",
        zone={"sound"},
        moral="candid",
        keyword="sup",
    ),
    "water": Trial(
        id="water",
        verb="carry the sacred water",
        gerund="carrying the sacred water",
        rush="hurry to the spring",
        risk="spilled the blessing across the stones",
        zone={"hands"},
        moral="candid",
        keyword="sup",
    ),
    "tablet": Trial(
        id="tablet",
        verb="read the prophecy aloud",
        gerund="reading the prophecy aloud",
        rush="step onto the temple dais",
        risk="shook the holy tablets with a boast",
        zone={"voice", "hands"},
        moral="candid",
        keyword="candid",
    ),
}

GIFTS = {
    "crown": Gift("crown", "crown", "a bright golden crown", "head"),
    "cup": Gift("cup", "cup", "a polished cup", "hands"),
    "cloak": Gift("cloak", "cloak", "a blue cloak", "torso"),
}

REMEDIES = [
    Remedy("quiet", "quiet sandals", {"feet"}, "soften each step", "wear quiet sandals first", "walked on in quiet sandals"),
    Remedy("veil", "a veil of humility", {"voice"}, "cool a boastful tongue", "set on a veil of humility", "spoke with a gentler voice"),
    Remedy("gloves", "river gloves", {"hands"}, "keep the blessing steady", "put on river gloves first", "went forward with river gloves"),
]

NAMES = ["Ari", "Nia", "Milo", "Tala", "Sera", "Leif"]
TRAITS = ["brave", "wise", "steady", "bold", "gentle", "curious"]


def valid_combo(place: Place, trial: Trial, gift: Gift) -> bool:
    return trial.zone <= {"sound", "hands", "voice"} and gift.region in {"head", "hands", "torso"} and place.affords


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pname, place in PLACES.items():
        for tname in place.affords:
            trial = _safe_lookup(TRIALS, tname)
            for gname, gift in GIFTS.items():
                if trial.id == "harp" and gift.region == "head":
                    continue
                if trial.id == "water" and gift.region != "hands":
                    continue
                if trial.id == "tablet" and gift.region != "torso":
                    continue
                out.append((pname, tname, gname))
    return out


def select_remedy(trial: Trial, gift: Gift) -> Optional[Remedy]:
    for remedy in REMEDIES:
        if trial.id == "harp" and "voice" in remedy.covers:
            continue
        if trial.id == "water" and gift.region in {"hands"} and "hands" in remedy.covers:
            return remedy
        if trial.id == "tablet" and "voice" in remedy.covers:
            return remedy
    if trial.id == "harp":
        return _safe_lookup(REMEDIES, 0)
    return None


def predict_damage(world: World, hero: Entity, trial: Trial, gift: Entity) -> bool:
    sim = world.copy()
    do_trial(sim, sim.get(hero.id), trial, narrate=False)
    return sim.get(gift.id).meter("spoiled") >= THRESHOLD


def do_trial(world: World, hero: Entity, trial: Trial, narrate: bool = True) -> None:
    if trial.id not in world.place.affords:
        return
    hero.meters[trial.id] = hero.meters.get(trial.id, 0.0) + 1
    if trial.id == "water":
        if world.get("gift").worn_by == hero.id:
            world.get("gift").meters["spoiled"] = world.get("gift").meters.get("spoiled", 0.0) + 1
    if trial.id == "tablet":
        hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} began {trial.gerund}, and the world grew tense.")


def story_intro(world: World, hero: Entity, parent: Entity, trial: Trial, gift: Entity) -> None:
    world.say(f"In old days, {hero.id} was a {hero.meters.get('age', 0) or 'young'} {hero.type} known for {hero.memes.get('virtue', 0) and 'virtue' or 'quiet'} courage.")
    world.say(f"{hero.pronoun().capitalize()} loved {trial.gerund}, yet {hero.pronoun('possessive')} {parent.label} feared for {hero.pronoun('possessive')} {gift.label}.")


def story_turn(world: World, hero: Entity, parent: Entity, trial: Trial, gift: Entity) -> None:
    world.para()
    world.say(f"One dawn, {hero.id} and {hero.pronoun('possessive')} {parent.label} came to {world.place.name}.")
    world.say(f"{hero.id} wanted to {trial.verb}, but the path was narrow and the hour was solemn.")
    if predict_damage(world, hero, trial, gift):
        world.say(f'"If you go now," {parent.id} said, "your {gift.label} may {trial.risk}."')
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    hero.memes["test"] = hero.memes.get("test", 0.0) + 1
    hero.memes["candid"] = hero.memes.get("candid", 0.0) + 1
    world.say(f"At first, {hero.id} tried to hide {hero.pronoun('possessive')} fear, but then {hero.pronoun()} chose to be candid.")


def story_resolution(world: World, hero: Entity, parent: Entity, trial: Trial, gift: Entity) -> None:
    world.para()
    remedy = select_remedy(trial, gift)
    if remedy is None:
        pass
    world.say(f"{parent.id} gave a small nod and offered {remedy.label}.")
    world.say(f'"Be candid," {parent.id} said. "Truth can be kinder than boasting."')
    hero.memes["pride"] = max(0.0, hero.memes.get("pride", 0.0) - 1)
    hero.memes["candid"] = hero.memes.get("candid", 0.0) + 1
    world.say(f"{hero.id} chose {remedy.prep}, and then {hero.id} could {trial.verb} without disaster.")
    world.say(f"In the end, {hero.id} {remedy.tail}, and {gift.label} stayed bright.")


def tell(place: Place, trial: Trial, gift_cfg: Gift, name: str, gender: str, parent_type: str, virtue: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, meters={"age": 1.0}, memes={"virtue": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=parent_type))
    gift = world.add(Entity(id="gift", type=gift_cfg.id, label=gift_cfg.label, phrase=gift_cfg.phrase, owner=hero.id))
    gift.worn_by = hero.id

    world.facts.update(hero=hero, parent=parent, gift=gift, trial=trial, place=place, virtue=virtue)
    story_intro(world, hero, parent, trial, gift)
    story_turn(world, hero, parent, trial, gift)
    do_trial(world, hero, trial, narrate=True)
    story_resolution(world, hero, parent, trial, gift)
    return world


KNOWLEDGE = {
    "candid": [("What does candid mean?", "Candid means honest and open, with no hiding or pretending.")],
    "sup": [("What is a sup?", "A sup is a tiny sip or drink, the kind you take to wet your mouth.")],
    "harp": [("What is a harp?", "A harp is a stringed instrument that makes gentle, shining music when you pluck its strings.")],
    "water": [("Why must sacred water be carried carefully?", "Because it can spill, and then the blessing is lost before it reaches its place.")],
    "tablet": [("What is a tablet in old stories?", "A tablet is a flat stone or clay board where important words are carved.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trial = f["trial"]
    gift = f["gift"]
    return [
        f'Write a myth-like story for a small child that includes the word "candid" and the word "sup".',
        f"Tell a short tale where {hero.id} wants to {trial.verb} while guarding {hero.pronoun('possessive')} {gift.label}, and truth matters.",
        f"Write an ending in which {hero.id} learns that being candid is wiser than boasting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    trial = f["trial"]
    gift = f["gift"]
    qa = [
        QAItem(
            question=f"Who is the myth about?",
            answer=f"It is about {hero.id}, a young {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.place.name}?",
            answer=f"{hero.id} wanted to {trial.verb}, but needed to be careful with {hero.pronoun('possessive')} {gift.label}.",
        ),
        QAItem(
            question=f"Why did honesty matter in the story?",
            answer=f"Honesty mattered because {hero.id} had to be candid about the risk instead of pretending everything was safe.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["trial"].keyword, world.facts["trial"].id, "candid"}
    out: list[QAItem] = []
    for tag in ["candid", "sup", "harp", "water", "tablet"]:
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class RegistryItem:
    pass
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


def explain_rejection(place: Place, trial: Trial, gift: Gift) -> str:
    return f"(No story: {trial.verb} at {place.name} does not reasonably endanger {gift.label} in this world.)"


def valid_story_combos() -> list[tuple[str, str, str]]:
    out = []
    for pname, place in PLACES.items():
        for tname in place.affords:
            trial = _safe_lookup(TRIALS, tname)
            for gname, gift in GIFTS.items():
                if trial.id == "harp" and gift.region == "head":
                    out.append((pname, tname, gname))
                elif trial.id == "water" and gift.region == "hands":
                    out.append((pname, tname, gname))
                elif trial.id == "tablet" and gift.region == "torso":
                    out.append((pname, tname, gname))
    return out


ASP_RULES = r"""
place(P) :- place_fact(P).
trial(T) :- trial_fact(T).
gift(G) :- gift_fact(G).

risk(P,T,G) :- affords(P,T), zone(T,R), gift_region(G,R2), R2 = R.
valid(P,T,G) :- risk(P,T,G), remedy_for(T,G).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pname, place in PLACES.items():
        lines.append(asp.fact("place_fact", pname))
        for t in sorted(place.affords):
            lines.append(asp.fact("affords", pname, t))
    for tname, trial in TRIALS.items():
        lines.append(asp.fact("trial_fact", tname))
        for z in sorted(trial.zone):
            lines.append(asp.fact("zone", tname, z))
    for gname, gift in GIFTS.items():
        lines.append(asp.fact("gift_fact", gname))
        lines.append(asp.fact("gift_region", gname, gift.region))
    for tname in TRIALS:
        for gname in GIFTS:
            if select_remedy(_safe_lookup(TRIALS, tname), _safe_lookup(GIFTS, gname)) is not None:
                lines.append(asp.fact("remedy_for", tname, gname))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_story_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic moral-value story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--gift", choices=GIFTS)
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
    combos = valid_story_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "trial", None):
        combos = [c for c in combos if c[1] == getattr(args, "trial", None)]
    if getattr(args, "gift", None):
        combos = [c for c in combos if c[2] == getattr(args, "gift", None)]
    if getattr(args, "gender", None):
        combos = [c for c in combos if getattr(args, "gender", None) in {"girl", "boy"}]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trial, gift = rng.choice(list(combos))
    gift_obj = _safe_lookup(GIFTS, gift)
    gender = getattr(args, "gender", None) or rng.choice(sorted(gift_obj.genders))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    virtue = rng.choice(TRAITS)
    return StoryParams(place=place, trial=trial, gift=gift, name=name, gender=gender, parent=parent, virtue=virtue)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TRIALS, params.trial), _safe_lookup(GIFTS, params.gift), params.name, params.gender, params.parent, params.virtue)
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


CURATED = [
    StoryParams(place="hill", trial="harp", gift="crown", name="Ari", gender="boy", parent="father", virtue="brave"),
    StoryParams(place="spring", trial="water", gift="cup", name="Nia", gender="girl", parent="mother", virtue="gentle"),
    StoryParams(place="temple", trial="tablet", gift="cloak", name="Tala", gender="girl", parent="mother", virtue="wise"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.trial} at {p.place} (gift: {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
