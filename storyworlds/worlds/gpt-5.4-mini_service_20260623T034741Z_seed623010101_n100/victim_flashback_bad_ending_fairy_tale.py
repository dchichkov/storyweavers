#!/usr/bin/env python3
"""
storyworlds/worlds/victim_flashback_bad_ending_fairy_tale.py
===========================================================

A small fairy-tale story world about a victim, a remembered past, and a bad end.

The seed idea is a classic fairy tale beat: a little villager remembers an old
warning, follows a trail into the woods, and meets a sly trickster. The world
models a few concrete entities with physical meters and emotional memes, lets
state drive narration, and keeps a declared ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SCARE_THRESHOLD = 1.0
TRUST_THRESHOLD = 1.0



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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guardian: object | None = None
    relic: object | None = None
    trail: object | None = None
    victim: object | None = None
    wolf: object | None = None
    woodsman: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "witch", "woman"}
        male = {"boy", "father", "king", "wolf", "man", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
    id: str
    label: str
    dark: bool = False
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
class Warning:
    id: str
    text: str
    danger: str
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
class Trick:
    id: str
    label: str
    lure: str
    hunger: int
    deceit: int
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
class Relic:
    id: str
    label: str
    prized: bool = True
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    c: object | None = None
    w: object | None = None
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
        c = World(place=self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("lost", 0.0) < THRESHOLD:
            continue
        sig = ("lost", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] = ent.memes.get("fear", 0.0) + 1
        out.append("__lost__")
    return out


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("hurt", 0.0) < THRESHOLD:
            continue
        sig = ("hurt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["sorrow"] = ent.memes.get("sorrow", 0.0) + 1
        out.append("__hurt__")
    return out


CAUSAL_RULES = [Rule("lost", "physical", _r_lost), Rule("hurt", "physical", _r_hurt)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def warn_missing(place: Place, warning: Warning) -> bool:
    return place.dark and "woods" in place.tags and warning.danger == "wolves"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for warn_id, warn in WARNINGS.items():
            for trick_id, trick in TRICKS.items():
                if warn_missing(place, warn) and trick.deceit >= 2:
                    combos.append((place_id, warn_id, trick_id))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    warning: str = ""
    trick: str = ""
    victim_name: str = ""
    victim_gender: str = ""
    guardian: str = ""
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


class WorldStory:
    pass


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        pass
    if params.warning not in WARNINGS:
        pass
    if params.trick not in TRICKS:
        pass
    place = _safe_lookup(PLACES, params.place)
    warning = _safe_lookup(WARNINGS, params.warning)
    trick = _safe_lookup(TRICKS, params.trick)
    if not warn_missing(place, warning):
        pass

    w = World(place=place)
    victim = w.add(Entity(
        id="victim", kind="character", type=params.victim_gender, role="victim",
        label=params.victim_name, attrs={"guardian": params.guardian},
        meters={"lost": 0.0, "hurt": 0.0}, memes={"hope": 1.0, "fear": 0.0, "trust": 1.0},
    ))
    guardian = w.add(Entity(
        id="guardian", kind="character", type="mother" if params.guardian == "mother" else "father",
        label=params.guardian, role="guardian",
        meters={"worry": 0.0}, memes={"care": 1.0},
    ))
    woodsman = w.add(Entity(
        id="woodsman", kind="character", type="man", label="woodsman", role="woodsman",
        meters={"late": 0.0}, memes={"help": 0.0},
    ))
    trail = w.add(Entity(
        id="trail", type="thing", label="trail", attrs={"place": place.label},
        meters={"twist": 1.0}, memes={},
    ))
    wolf = w.add(Entity(
        id="wolf", kind="character", type="wolf", label=trick.label, role="trickster",
        attrs={"lure": trick.lure}, meters={"hungry": float(trick.hunger), "caught": 0.0},
        memes={"sly": float(trick.deceit)},
    ))
    relic = w.add(Entity(
        id="relic", type="thing", label="the little silver ribbon", meters={"held": 1.0}, memes={}
    ))
    w.facts.update(
        victim=victim, guardian=guardian, woodsman=woodsman, trail=trail, wolf=wolf,
        relic=relic, warning=warning, trick=trick, place=place,
        remembered_warning=False, followed_lure=False, rescued=False, bad_end=False,
    )

    w.say(f"In {place.label}, {victim.label} was a little {params.victim_gender} who loved bright paths and old songs.")
    w.say(f"{guardian.label_word.capitalize()} had once warned, '{warning.text}'")
    w.say(f"But one gray afternoon, {victim.label} found {trick.lure} and followed it toward the woods.")

    w.para()
    flashback(w, victim, guardian, warning)
    choose_lure(w, victim, wolf, trail)

    w.para()
    meet_bad_ending(w, victim, wolf, woodsman, relic, place)
    return w


def flashback(world: World, victim: Entity, guardian: Entity, warning: Warning) -> None:
    victim.memes["hope"] += 1
    victim.memes["trust"] += 0.5
    world.facts["remembered_warning"] = True
    world.say(
        f"As {victim.label} walked, a flashback came back like a little bell in the mind: "
        f"{guardian.label_word.capitalize()} had said, '{warning.text}'"
    )
    world.say(
        f"For a moment {victim.label} slowed down, but the promise of the shining path still tugged at {victim.label_word}."
    )


def victim_label(victim: Entity) -> str:
    return victim.label or victim.id


def choose_lure(world: World, victim: Entity, wolf: Entity, trail: Entity) -> None:
    victim.meters["lost"] += 1.0
    wolf.memes["sly"] = wolf.memes.get("sly", 0.0) + 1
    world.facts["followed_lure"] = True
    world.say(
        f"{victim_label(victim)} followed {wolf.label_word if hasattr(wolf, 'label_word') else wolf.label} and the trail curled deeper under the trees."
    )


def meet_bad_ending(world: World, victim: Entity, wolf: Entity, woodsman: Entity, relic: Entity, place: Place) -> None:
    victim.meters["hurt"] += 1.0
    world.facts["rescued"] = False
    world.facts["bad_end"] = True
    propagate(world, narrate=False)
    world.say(
        f"At last the wolf reached {victim_label(victim)} first. The woodsman was too late, and the wolf kept the little silver ribbon."
    )
    world.say(
        f"{victim_label(victim)} went home with empty hands, and the woods by {place.label} stayed quiet, as if the trees themselves were sorry."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story that includes the word "victim" and remembers an old warning before the end.',
        f"Tell a short fairy tale where {f['victim'].label} hears a warning from {f['guardian'].label_word} in a flashback, then follows a sly wolf and loses the treasure.",
        f"Write a sad fairy tale ending where a victim remembers a warning too late and the woodsman arrives after the wolf is gone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    v = f["victim"]
    g = f["guardian"]
    w = f["warning"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {v.label}, the victim of the wolf's trick. {v.label} starts out hopeful, but the path leads to a bad ending."
        ),
        QAItem(
            question=f"What did {g.label_word} warn about?",
            answer=f"{g.label_word.capitalize()} warned, '{w.text}' That warning mattered because the woods were dark and full of trickery."
        ),
        QAItem(
            question="What happened in the flashback?",
            answer=f"{v.label} remembered the warning from {g.label_word} while walking through the woods. The memory came back clearly, but it was too late to change the choice."
        ),
        QAItem(
            question="Why was the ending bad?",
            answer="The wolf reached the victim first, and the woodsman arrived too late. Because of that, the treasure was lost and the little hero went home sad."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a victim?", "A victim is someone who is harmed or tricked by something bad. In stories, a victim is often the one who needs help or protection."),
        QAItem("What is a flashback?", "A flashback is a moment in a story when a character remembers something from before. It helps explain why the character feels worried or careful now."),
        QAItem("What makes a bad ending?", "A bad ending is when the problem does not get fixed in time. The danger wins, and the character loses something important."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={dict(e.attrs)}")
    out.append(f"  facts={{{', '.join(sorted(world.facts.keys()))}}}")
    return "\n".join(out)


PLACES = {
    "woods": Place(id="woods", label="the whispering woods", dark=True, tags={"woods"}),
    "hill": Place(id="hill", label="the moonlit hill", dark=True, tags={"woods"}),
    "path": Place(id="path", label="the thorny path", dark=True, tags={"woods"}),
}

WARNINGS = {
    "wolf": Warning(id="wolf", text="Never follow a wolf into the dark.", danger="wolves", tags={"wolf"}),
    "berries": Warning(id="berries", text="Do not trade your way home for sweet berries.", danger="wolves", tags={"wolf", "berries"}),
    "song": Warning(id="song", text="Beware the singing shadow by the trees.", danger="wolves", tags={"wolf", "song"}),
}

TRICKS = {
    "trail": Trick(id="trail", label="a silver trail", lure="a silver trail", hunger=2, deceit=3, tags={"trail"}),
    "bell": Trick(id="bell", label="a tiny bell", lure="a tiny bell", hunger=2, deceit=2, tags={"bell"}),
    "apple": Trick(id="apple", label="a red apple", lure="a red apple", hunger=3, deceit=4, tags={"apple"}),
}

GIRL_NAMES = ["Mina", "Elin", "Tara", "Lena", "Nora"]
BOY_NAMES = ["Owen", "Finn", "Jude", "Pavel", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world with flashback and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "warning", None) is None or c[1] == getattr(args, "warning", None))
              and (getattr(args, "trick", None) is None or c[2] == getattr(args, "trick", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, warning, trick = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = getattr(args, "guardian", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, warning=warning, trick=trick, victim_name=name, victim_gender=gender, guardian=guardian)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.warning not in WARNINGS or params.trick not in TRICKS:
        pass
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


ASP_RULES = r"""
valid(P,W,T) :- place(P), warning(W), trick(T), dark(P), woods(P), warns_of(W, wolves), deceit(T,D), D >= 2.
flashback(V) :- victim(V), remembers_warning(V).
bad_end(V) :- victim(V), follows_lure(V), wolf_reaches_first(V).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if "woods" in p.tags:
            lines.append(asp.fact("woods", pid))
    for wid, w in WARNINGS.items():
        lines.append(asp.fact("warning", wid))
        lines.append(asp.fact("warns_of", wid, w.danger))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        lines.append(asp.fact("deceit", tid, t.deceit))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    if not sample.story or "flashback" not in " ".join(sample.prompts).lower():
        print("MISMATCH: smoke test failed.")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


CURATED = [
    StoryParams(place="woods", warning="wolf", trick="trail", victim_name="Mina", victim_gender="girl", guardian="mother"),
    StoryParams(place="hill", warning="berries", trick="apple", victim_name="Owen", victim_gender="boy", guardian="father"),
    StoryParams(place="path", warning="song", trick="bell", victim_name="Lena", victim_gender="girl", guardian="mother"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not fit a fairy-tale warning in the dark woods.)"


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

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
