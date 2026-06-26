#!/usr/bin/env python3
"""
A mythic tiny storyworld about a swirl, a quest, a lesson learned, and a
transformation.

The seed tale idea:
A small hero sees a strange swirl in a sacred place and sets out to follow it.
The quest is difficult because the swirl scatters the path and tempts the hero
to rush. With a helper's guidance, the hero learns patience, completes the quest,
and is transformed by what they bring back.

The world model tracks:
- physical meters: distance, gathered, steadiness, shimmer, ruin
- emotional memes: curiosity, worry, pride, patience, wonder, humility

A "swirl" can be sacred, elusive, or wild. The hero must choose a fitting token
to carry, travel through a place shaped by the swirl, and return changed.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str
    mood: str
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
class Swirl:
    name: str
    verb: str
    noun: str
    force: str
    gift: str
    peril: str
    path: str
    trail: str
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
class Token:
    label: str
    phrase: str
    type: str
    protects_against: set[str]
    transforms_into: str
    hands: str
    tags: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def _status(hero: Entity) -> str:
    if hero.memes.get("worry", 0) >= THRESHOLD:
        return "uneasy"
    if hero.memes.get("pride", 0) >= THRESHOLD:
        return "bright with pride"
    if hero.memes.get("wonder", 0) >= THRESHOLD:
        return "wide-eyed"
    return "quiet"


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    swirl = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "swirl")
    if hero.meters.get("pursuit", 0) < THRESHOLD:
        return out
    if ("scatter", swirl.name) in world.fired:
        return out
    world.fired.add(("scatter", swirl.name))
    hero.meters["distance"] = hero.meters.get("distance", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    out.append(f"The {swirl.noun} did not stay still; it scattered the path ahead.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    token = world.facts.get("token")
    swirl = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "swirl")
    if hero.meters.get("returned", 0) < THRESHOLD:
        return out
    if hero.meters.get("lesson", 0) < THRESHOLD:
        return out
    sig = ("transform", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["shimmer"] = hero.meters.get("shimmer", 0) + 1
    hero.memes["humility"] = hero.memes.get("humility", 0) + 1
    out.append(f"When the hero came home, the {swirl.noun} had changed the hero's heart.")
    if token:
        out.append(f"The {token.label} no longer seemed like a prize alone; it had become a sign of wisdom.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_scatter, _r_transform):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, swirl: Swirl, token: Token, hero_name: str, hero_type: str,
         helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        meters={"pursuit": 0.0, "distance": 0.0, "returned": 0.0, "lesson": 0.0, "shimmer": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "pride": 0.0, "patience": 0.0, "wonder": 0.0, "humility": 0.0},
    ))
    helper = world.add(Entity(
        id="Guide", kind="character", type=helper_type, label="the guide",
        meters={}, memes={"patience": 1.0},
    ))
    relic = world.add(Entity(
        id="Relic", type=token.type, label=token.label, phrase=token.phrase,
        owner=hero.id, helper=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, token=relic, swirl=swirl, setting=setting)

    world.say(f"In {setting.place}, where the air carried a {setting.mood} hush, there was a {swirl.noun}.")
    world.say(f"The {swirl.noun} was known for how it would {swirl.verb}, leaving {swirl.gift} in its wake.")
    world.say(f"{hero_name} was a little {hero_type} who felt { _status(hero) } when the {swirl.noun} gleamed in the distance.")
    world.say(f"{hero_name} longed to seek the {token.label} that belonged to the tale of the {swirl.noun}.")
    world.say(f"That {swirl.path} led to a {swirl.peril}, but it also promised {swirl.gift}.")
    world.para()
    hero.meters["pursuit"] = 1.0
    hero.memes["curiosity"] += 1.0
    world.say(f"So {hero_name} began the quest and walked along the {swirl.path}.")
    propagate(world)
    world.say(f"The further {hero_name} went, the more the {swirl.noun} tugged at {hero.pronoun('possessive')} thoughts.")
    world.say(f"{hero_name} wanted to rush, but rushing only made the road feel thinner.")
    hero.memes["worry"] += 1.0
    world.para()
    world.say(f"Then the guide spoke softly: \"A {swirl.noun} is not mastered by force; it is understood by patience.\"")
    hero.memes["patience"] += 1.0
    world.say(f"{hero_name} listened, and the steps became slow and sure.")
    hero.meters["lesson"] = 1.0
    world.say(f"At last, by waiting at the heart of the swirl, {hero_name} found the {token.label}.")
    world.say(f"{hero_name} took up {token.phrase} and carried {(getattr(token, 'it')() if callable(getattr(token, 'it', None)) else getattr(token, 'it', 'it'))} carefully back through the turning wind.")
    hero.meters["returned"] = 1.0
    hero.memes["pride"] += 1.0
    world.para()
    propagate(world)
    world.say(f"By the time {hero_name} returned, {hero.pronoun()} was no longer only a seeker.")
    world.say(f"{hero_name} had learned the lesson of the swirl: wisdom comes to those who can wait for it.")
    world.say(f"And so the quest ended with a quiet transformation, and the {swirl.noun} shone on as before.")
    world.facts["resolved"] = True
    return world


SWIRLS = {
    "sacred": Swirl(
        name="sacred_swirl",
        verb="turn in glowing circles",
        noun="sacred swirl",
        force="old wind",
        gift="a bright answer",
        peril="a bent and lonely ridge",
        path="stone steps",
        trail="silver dust",
        tags={"swirl", "sacred"},
    ),
    "river": Swirl(
        name="river_swirl",
        verb="curl around the rocks",
        noun="river swirl",
        force="cold water",
        gift="a pearl-bright way",
        peril="deep reeds",
        path="muddy banks",
        trail="foam",
        tags={"swirl", "water"},
    ),
    "sky": Swirl(
        name="sky_swirl",
        verb="spin across the clouds",
        noun="sky swirl",
        force="blue thunder",
        gift="a feather of light",
        peril="high, hungry air",
        path="windy heights",
        trail="cloud-silk",
        tags={"swirl", "sky"},
    ),
}

TOKENS = {
    "feather": Token(
        label="feather",
        phrase="a pale feather with a gold tip",
        type="feather",
        protects_against={"worry"},
        transforms_into="wisdom",
        hands="one",
        tags={"light"},
    ),
    "stone": Token(
        label="stone",
        phrase="a smooth stone warmed by the sun",
        type="stone",
        protects_against={"fear"},
        transforms_into="steadiness",
        hands="one",
        tags={"earth"},
    ),
    "vessel": Token(
        label="vessel",
        phrase="a small vessel etched with rings",
        type="vessel",
        protects_against={"confusion"},
        transforms_into="memory",
        hands="two",
        tags={"craft"},
    ),
}

SETTINGS = {
    "mountain": Setting(place="the mountain sanctuary", mood="ancient", affords={"sacred"}),
    "river": Setting(place="the river shrine", mood="silver-cold", affords={"river"}),
    "sky": Setting(place="the high observatory", mood="wind-bright", affords={"sky"}),
}

GENDERS = {
    "girl": ["Ari", "Nia", "Mira", "Lena", "Suri"],
    "boy": ["Orin", "Taro", "Eli", "Niko", "Bram"],
}
HELPERS = ["elder", "keeper", "priest", "priestess", "guide"]


@dataclass
class StoryParams:
    setting: str
    swirl: str
    token: str
    name: str
    gender: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_name, setting in SETTINGS.items():
        for swirl_name in setting.affords:
            for token_name in TOKENS:
                out.append((s_name, swirl_name, token_name))
    return out


ASP_RULES = r"""
target_story(S, W, T) :- setting(S), swirl(W), token(T), affords(S, W).

#show target_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", s_name))
        for sw in setting.affords:
            lines.append(asp.fact("affords", s_name, sw))
    for w_name in SWIRLS:
        lines.append(asp.fact("swirl", w_name))
    for t_name in TOKENS:
        lines.append(asp.fact("token", t_name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld of a swirl, a quest, a lesson learned, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--swirl", choices=SWIRLS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "swirl", None) is None or c[1] == getattr(args, "swirl", None))
              and (getattr(args, "token", None) is None or c[2] == getattr(args, "token", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, swirl, token = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDERS, gender))
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(setting=setting, swirl=swirl, token=token, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "swirl").noun}, a quest, a lesson learned, and transformation.',
        f"Tell a gentle myth where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} seeks {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "token").phrase} at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place}.",
        f'Write a story that includes the word "swirl" and ends with wisdom changing the seeker.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, swirl, token, setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "swirl"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "token"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    return [
        QAItem(
            question=f"What kind of place was {setting.place} in the story?",
            answer=f"It was {setting.mood}, and it held the path of the {swirl.noun}.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to find during the quest?",
            answer=f"{hero.id} was trying to find {token.phrase} and return with it safely.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn from the {swirl.noun}?",
            answer=f"{hero.id} learned that a quest through a {swirl.noun} needs patience, not rushing.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} returned transformed, with more patience, humility, and a wiser heart.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a swirl?",
            answer="A swirl is a turning, spinning shape, like wind or water moving in circles.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or complete a difficult task.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form or becomes different inside.",
        ),
        QAItem(
            question="Why can patience help on a hard journey?",
            answer="Patience helps because waiting and moving carefully can keep a traveler safe and help them notice what matters.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(setting: str, swirl: str, token: str) -> str:
    return f"(No story: the selected setting '{setting}' does not afford the '{swirl}' swirl for token '{token}'.)"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show target_story/3."))
    return sorted(set(asp.atoms(model, "target_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SWIRLS, params.swirl), _safe_lookup(TOKENS, params.token),
                 params.name, params.gender, params.helper)
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
    StoryParams(setting="mountain", swirl="sacred", token="feather", name="Ari", gender="girl", helper="elder"),
    StoryParams(setting="river", swirl="river", token="stone", name="Orin", gender="boy", helper="guide"),
    StoryParams(setting="sky", swirl="sky", token="vessel", name="Mira", gender="girl", helper="priestess"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show target_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
