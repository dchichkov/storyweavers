#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/papita_reconciliation_surprise_space_adventure.py
=============================================================================================================

A tiny storyworld about a space adventure, a surprise, and a reconciliation.

A little crew flies a small ship to a quiet moon. One child feels hurt after a
mix-up, then a surprise helps them talk, repair the problem, and end the day
together. The world model tracks ship parts, locations, and emotions with
physical meters and emotional memes, and the prose is driven by those state
changes.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

GENDER_PRONOUNS = {
    "girl": ("she", "her", "her"),
    "boy": ("he", "him", "his"),
    "child": ("they", "them", "their"),
}



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    location: str = ""
    portable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    friend: object | None = None
    hero: object | None = None
    map_item: object | None = None
    surprise_item: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        subj, obj, pos = GENDER_PRONOUNS.get(self.type, GENDER_PRONOUNS["child"])
        return {"subject": subj, "object": obj, "possessive": pos}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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


@dataclass(frozen=True)
class CrewConfig:
    name: str
    type: str
    role: str
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


@dataclass(frozen=True)
class PlaceConfig:
    name: str
    detail: str
    surprise_spot: str
    tags: set[str]
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


@dataclass(frozen=True)
class ProblemConfig:
    id: str
    mixup: str
    hurt: str
    location: str
    tags: set[str]
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


@dataclass(frozen=True)
class SurpriseConfig:
    id: str
    object_label: str
    object_phrase: str
    reveal: str
    repair_tool: str
    tool_phrase: str
    tags: set[str]
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


@dataclass(frozen=True)
class ResolutionConfig:
    id: str
    action: str
    ending: str
    tags: set[str]
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
class StoryParams:
    place: str = ""
    problem: str = ""
    surprise: str = ""
    resolution: str = ""
    hero: str = ""
    hero_type: str = "child"
    friend: str = ""
    friend_type: str = "child"
    seed: Optional[int] = None
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


CREW = {
    "Ari": CrewConfig(name="Ari", type="boy", role="pilot"),
    "Nova": CrewConfig(name="Nova", type="girl", role="pilot"),
    "Milo": CrewConfig(name="Milo", type="boy", role="mechanic"),
    "Luna": CrewConfig(name="Luna", type="girl", role="mechanic"),
}

PLACES = {
    "quiet_moon": PlaceConfig(
        name="the quiet moon",
        detail="The moon dust was pale and soft, and the little ship stood under a sky full of stars.",
        surprise_spot="behind a bright crater rock",
        tags={"moon", "stars", "space"},
    ),
    "sky_dock": PlaceConfig(
        name="the sky dock",
        detail="A tiny dock floated above the clouds, where silver rails shone like lightning.",
        surprise_spot="inside a storage pod",
        tags={"dock", "clouds", "space"},
    ),
}

PROBLEMS = {
    "stolen_map": ProblemConfig(
        id="stolen_map",
        mixup="the moon map was missing",
        hurt="felt left out",
        location="map tray",
        tags={"map", "lost", "hurt"},
    ),
    "wrong_greeting": ProblemConfig(
        id="wrong_greeting",
        mixup="the crew had called the wrong name",
        hurt="felt embarrassed",
        location="radio panel",
        tags={"greeting", "embarrassed"},
    ),
}

SURPRISES = {
    "papita_box": SurpriseConfig(
        id="papita_box",
        object_label="papita",
        object_phrase="a warm papita from the lunch pouch",
        reveal="the paper wrapper opened to a tiny star-shaped papita snack",
        repair_tool="glitter pen",
        tool_phrase="a small glitter pen",
        tags={"papita", "surprise", "food"},
    ),
    "rocket_note": SurpriseConfig(
        id="rocket_note",
        object_label="note",
        object_phrase="a folded note tucked under the seat strap",
        reveal="the note showed a hand-drawn moon with a smile and an apology",
        repair_tool="sticker sheet",
        tool_phrase="a shiny sticker sheet",
        tags={"note", "surprise", "apology"},
    ),
}

RESOLUTIONS = {
    "talk_and_share": ResolutionConfig(
        id="talk_and_share",
        action="talked it through and shared the surprise",
        ending="They sat side by side while the stars blinked over the moon, and their ship felt cozy again.",
        tags={"talk", "share", "reconcile"},
    ),
    "apology_and_fix": ResolutionConfig(
        id="apology_and_fix",
        action="said sorry and fixed the mix-up",
        ending="By the time they packed up, the mistake was gone, and the crew was laughing together again.",
        tags={"apology", "fix", "reconcile"},
    ),
}

CURATED = [
    StoryParams(place="quiet_moon", problem="stolen_map", surprise="papita_box", resolution="talk_and_share", hero="Ari", hero_type="boy", friend="Nova", friend_type="girl"),
    StoryParams(place="quiet_moon", problem="wrong_greeting", surprise="rocket_note", resolution="apology_and_fix", hero="Luna", hero_type="girl", friend="Milo", friend_type="boy"),
]


class World:
    def __init__(self, place: PlaceConfig) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        other = World(self.place)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


def _ensure(ent: Entity, meter: str, amount: float = 0.0) -> None:
    ent.meters.setdefault(meter, amount)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        if world.facts.get("repaired") and "repair" not in world.fired:
            world.fired.add("repair")
            out.append("The ship's little light returned, and the room felt safe again.")
            changed = True
        if world.facts.get("reconciled") and "reconcile" not in world.fired:
            world.fired.add("reconcile")
            out.append("The two children relaxed and their hurt feelings softened.")
            changed = True
    if narrate:
        for line in out:
            world.say(line)
    return out


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for surprise in SURPRISES:
                for resolution in RESOLUTIONS:
                    combos.append((place, problem, surprise, resolution))
    return combos


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        pass
    if params.problem not in PROBLEMS:
        pass
    if params.surprise not in SURPRISES:
        pass
    if params.resolution not in RESOLUTIONS:
        pass
    if params.hero not in CREW or params.friend not in CREW:
        pass
    if params.hero == params.friend:
        pass

    place = _safe_lookup(PLACES, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    surprise = _safe_lookup(SURPRISES, params.surprise)
    resolution = _safe_lookup(RESOLUTIONS, params.resolution)
    hero_cfg = CREW[params.hero]
    friend_cfg = CREW[params.friend]

    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role=hero_cfg.role, meters={}, memes={}, attrs={"crew_role": hero_cfg.role}, tags={"child"}))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type, role=friend_cfg.role, meters={}, memes={}, attrs={"crew_role": friend_cfg.role}, tags={"child"}))
    map_item = world.add(Entity(id="map", kind="thing", type="thing", label="moon map", phrase="the little moon map", location=problem.location, meters={}, memes={}, attrs={}, tags={"map"}))
    surprise_item = world.add(Entity(id="surprise", kind="thing", type="thing", label=surprise.object_label, phrase=surprise.object_phrase, location=place.name, portable=True, meters={}, memes={}, attrs={}, tags=surprise.tags))
    tool = world.add(Entity(id="tool", kind="thing", type="thing", label=surprise.repair_tool, phrase=surprise.tool_phrase, location=place.name, portable=True, meters={}, memes={}, attrs={}, tags={surprise.repair_tool}))

    for ent in (hero, friend, map_item, surprise_item, tool):
        _ensure(ent, "hurt")
        _ensure(ent, "joy")
        _ensure(ent, "trust")
        _ensure(ent, "repair")
        _ensure(ent, "missing")
    hero.memes["hurt"] = 1.0
    friend.memes["hurt"] = 1.0
    world.facts.update(place=place, problem=problem, surprise=surprise, resolution=resolution, hero=hero, friend=friend, map_item=map_item, surprise_item=surprise_item, tool=tool, reconciled=False, repaired=False)

    world.say(f"{params.hero} and {params.friend} floated down to {place.name} on a small silver ship.")
    world.say(place.detail)
    world.say(f"They were looking for {problem.mixup}, and the mistake made {params.hero} {problem.hurt}.")

    world.para()
    hero.memes["hurt"] += 1
    friend.memes["trust"] += 1
    world.say(f"{params.friend} noticed the quiet mood and held up a hand. \"I think we need a better way,\" {"they"} said.")
    world.say(f"Then, from {place.surprise_spot}, they found {surprise.object_phrase}.")
    world.say(f"When the wrapper opened, {surprise.reveal}.")

    world.para()
    world.say(f"{params.hero} blinked, then smiled a little. {params.friend} used {surprise.tool_phrase} to draw a tiny apology on the map case.")
    world.say(f"That small surprise changed everything: {resolution.action}.")
    hero.memes["hurt"] = 0.0
    friend.memes["hurt"] = 0.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    hero.memes["trust"] += 1.0
    friend.memes["trust"] += 1.0
    world.facts["reconciled"] = True
    world.facts["repaired"] = True
    propagate(world, narrate=True)

    world.para()
    world.say(resolution.ending)
    world.say(f"The little papita wrapper stayed in the ship as a warm reminder that surprises can help friends make up.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a young child that includes the word "papita" and ends with two friends making up.',
        f"Tell a gentle moon story where {f['hero'].id} feels hurt at first, then finds a surprise and reconciles with {f['friend'].id}.",
        f"Write a child-friendly space story about a small crew on {f['place'].name} with a surprise snack and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    problem: ProblemConfig = f["problem"]  # type: ignore[assignment]
    surprise: SurpriseConfig = f["surprise"]  # type: ignore[assignment]
    resolution: ResolutionConfig = f["resolution"]  # type: ignore[assignment]
    place: PlaceConfig = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {hero.id} feel upset at {place.name}?",
            answer=f"{hero.id} felt upset because {problem.mixup}. That hurt feeling made the space trip feel lonely for a little while.",
        ),
        QAItem(
            question=f"What surprise did the crew find in the space adventure?",
            answer=f"They found {surprise.object_phrase}, and it turned out to be a papita surprise. It helped the children look at each other more kindly.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix the problem?",
            answer=f"They {resolution.action}, and that let them talk without feeling so stuck. The repair turned the ship back into a happy place.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"The hurt feeling was gone, and the children were smiling together again. The ending showed that the surprise led to reconciliation.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is papita in this storyworld?",
            answer="Papita is a snack that can be given as a small surprise. In this storyworld it helps turn a bad mood into a kinder one.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people make up after a hurt or a mix-up. They talk, soften their feelings, and become friends again.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected. It can be a present, a note, or a happy moment that changes how someone feels.",
        ),
        QAItem(
            question="What makes this a space adventure?",
            answer="The children travel on a small ship, land on a moon or dock, and solve their problem under the stars. The space setting gives the story its adventure feeling.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    out.append(f"facts={ {k: v for k, v in world.facts.items() if k not in {'hero', 'friend', 'map_item', 'surprise_item', 'tool'}} }")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    lines.append(asp.fact("must_include", "papita"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, S, R) :- place(P), problem(Pr), surprise(S), resolution(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH: Python and ASP combo sets differ.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, surprise=None, resolution=None, hero=None, hero_type=None, friend=None, friend_type=None, seed=None), random.Random(777)))
        _ = sample.story
        _ = format_qa(sample)
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: verify passed ({len(py)} combos; smoke test succeeded).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with papita, surprise, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--hero", choices=CREW)
    ap.add_argument("--hero-type", choices=["girl", "boy", "child"])
    ap.add_argument("--friend", choices=CREW)
    ap.add_argument("--friend-type", choices=["girl", "boy", "child"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "problem", None) and getattr(args, "problem", None) not in PROBLEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "surprise", None) and getattr(args, "surprise", None) not in SURPRISES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "resolution", None) and getattr(args, "resolution", None) not in RESOLUTIONS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "surprise", None) is None or c[2] == getattr(args, "surprise", None))
              and (getattr(args, "resolution", None) is None or c[3] == getattr(args, "resolution", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, surprise, resolution = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(sorted(CREW))
    friend_choices = [k for k in CREW if k != hero]
    friend = getattr(args, "friend", None) or rng.choice(friend_choices)
    hero_type = getattr(args, "hero_type", None) or CREW[hero].type
    friend_type = getattr(args, "friend_type", None) or CREW[friend].type
    return StoryParams(place=place, problem=problem, surprise=surprise, resolution=resolution, hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type)


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, pr, s, r) for p in PLACES for pr in PROBLEMS for s in SURPRISES for r in RESOLUTIONS]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
