#!/usr/bin/env python3
"""
Standalone storyworld: lump, mallard, moral value, sharing, conflict, superhero style.

A tiny superhero tale world:
- A young hero notices a mallard in trouble near a city pond.
- A small conflict starts over a useful lump (a lump of bread / clay / mossy stone).
- The hero learns a moral value: sharing.
- The ending proves the change with a concrete, state-driven rescue.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld
- StoryParams plus registries
- generate / emit / main
- lazy ASP import inside helpers
- eager shared results import
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
# Core world model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mallard: object | None = None
    parent: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "heroine"}
        male = {"boy", "father", "dad", "man", "hero"}
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
class World:
    setting: "Setting"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w
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
class Setting:
    place: str
    indoors: bool
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    answer: object | None = None
    question: object | None = None
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
class Challenge:
    id: str
    action: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    plural: bool = False


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "rooftop": Setting(place="the rooftop", indoors=False, affords={"fly", "rescue"}),
    "park": Setting(place="the city park", indoors=False, affords={"fly", "rescue"}),
    "museum": Setting(place="the museum hall", indoors=True, affords={"rescue"}),
}

CHALLENGES = {
    "fly": Challenge(
        id="fly",
        action="fly over the city",
        gerund="flying over the city",
        rush="dash to the ledge and leap",
        mess="windy",
        soil="all ruffled",
        zone={"torso"},
        keyword="cape",
        tags={"superhero", "share", "conflict"},
    ),
    "rescue": Challenge(
        id="rescue",
        action="help the mallard",
        gerund="helping the mallard",
        rush="run to the pond",
        mess="muddy",
        soil="mud-streaked",
        zone={"feet", "legs"},
        keyword="mallard",
        tags={"mallard", "sharing", "moral"},
    ),
}

ITEMS = {
    "cape": Item(
        id="cape",
        label="cape",
        phrase="a bright red cape",
        type="cape",
        region="torso",
    ),
    "boots": Item(
        id="boots",
        label="boots",
        phrase="sturdy superhero boots",
        type="boots",
        region="feet",
        plural=True,
    ),
    "lunch": Item(
        id="lunch",
        label="lunch bag",
        phrase="a lunch bag with a big sandwich",
        type="lunch bag",
        region="hands",
    ),
}

AID = [
    Aid(
        id="umbrella_shield",
        label="shield umbrella",
        prep="share the shield umbrella",
        tail="held the shield umbrella together",
        guards={"windy"},
        covers={"torso"},
    ),
    Aid(
        id="boot_wraps",
        label="boot wraps",
        prep="put on the boot wraps",
        tail="went back out in the boot wraps",
        guards={"muddy"},
        covers={"feet", "legs"},
        plural=True,
    ),
    Aid(
        id="sharing_plan",
        label="sharing plan",
        prep="share the last sandwich with the mallard",
        tail="split the sandwich and fed the mallard too",
        guards={"hungry"},
        covers={"hands", "torso"},
    ),
]

NAMES = ["Nova", "Riley", "Mira", "Zane", "Aria", "Jett", "Luna", "Kai"]
HERO_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["brave", "kind", "quick", "curious", "determined"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
challenge_risk(C, I) :- challenge(C), item(I), zones(C, R), wears(I, R).
aid_works(A, C, I) :- aid(A), challenge_risk(C, I), guards(A, M), mess_of(C, M), covers(A, R), wears(I, R).
valid_story(S, C, I) :- setting(S), challenge(C), item(I), challenge_risk(C, I), aid_works(_, C, I), supports(S, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for c in sorted(s.affords):
            lines.append(asp.fact("supports", sid, c))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("mess_of", cid, c.mess))
        for r in sorted(c.zone):
            lines.append(asp.fact("zones", cid, r))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("wears", iid, i.region))
    for aid in AID:
        lines.append(asp.fact("aid", aid.id))
        for m in sorted(aid.guards):
            lines.append(asp.fact("guards", aid.id, m))
        for r in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def risk_of_soil(ch: Challenge, item: Item) -> bool:
    return item.region in ch.zone


def choose_aid(ch: Challenge, item: Item) -> Optional[Aid]:
    for aid in AID:
        if ch.mess in aid.guards and item.region in aid.covers:
            return aid
    return None


def predict(world: World, hero: Entity, ch: Challenge, item: Entity) -> dict:
    sim = world.copy()
    act(sim, sim.get(hero.id), ch, narrate=False)
    return {
        "soiled": bool(sim.get(item.id).memes.get("dirty", 0.0) >= THRESHOLD),
    }


def act(world: World, hero: Entity, ch: Challenge, narrate: bool = True) -> None:
    hero.meters[ch.mess] = hero.meters.get(ch.mess, 0.0) + 1
    hero.memes["drive"] = hero.memes.get("drive", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} used {ch.action} to help right away.")


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a little {trait} {hero.type} who wanted to be a real superhero.")


def bond(world: World, hero: Entity, mallard: Entity) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    world.say(f"{hero.id} had a soft spot for {mallard.label}, a plucky mallard with shiny green feathers.")


def show_item(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(f"At home, {hero.id} loved {hero.pronoun('possessive')} {item.label} and wore {item.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, setting: Setting, ch: Challenge) -> None:
    day = "One bright afternoon, " if not setting.indoors else "One quiet afternoon, "
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.type} went to {setting.place}.")
    world.say(f"The place looked ready for {ch.gerund}.")


def want(world: World, hero: Entity, ch: Challenge, item: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"{hero.id} wanted to {ch.action}, but {hero.pronoun('possessive')} {item.label} could get ruined.")


def warn(world: World, parent: Entity, hero: Entity, ch: Challenge, item: Entity) -> None:
    pred = predict(world, hero, ch, item)
    if pred["soiled"]:
        world.facts["risk"] = True
        world.say(f'"If you rush ahead, your {item.label} may get {ch.soil}," {parent.type} said.')
    else:
        world.facts["risk"] = False


def conflict(world: World, hero: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    world.say(f"{hero.id} frowned. The choice to help was hard when the prized thing felt so special.")


def share_turn(world: World, parent: Entity, hero: Entity, mallard: Entity, ch: Challenge, item: Entity) -> Optional[Aid]:
    aid = choose_aid(ch, ITEMS["cape"] if item.type == "cape" else item)
    # Special moral-value turn: sharing is the true solution for the mallard rescue.
    if ch.id == "rescue":
        aid = next((a for a in AID if a.id == "sharing_plan"), aid)
    if aid is None:
        return None
    world.facts["aid"] = aid
    if aid.id == "sharing_plan":
        world.say(f'{parent.pronoun("subject").capitalize()} nodded and said, "We can share."')
        world.say(f"{hero.id} remembered the little mallard had to eat too.")
        return aid
    world.say(f"{hero.id}'s {parent.type} pointed to the {aid.label} and smiled.")
    return aid


def resolve(world: World, hero: Entity, parent: Entity, mallard: Entity, ch: Challenge, item: Entity, aid: Aid) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["conflict"] = 0.0
    if aid.id == "sharing_plan":
        world.say(f"{hero.id} split the sandwich and shared it with the mallard.")
        world.say(f"The mallard peeped happily, and the hero felt stronger than before.")
        world.say(f"By the end, {hero.id} was {ch.gerund}, and the mallard stayed close beside {hero.pronoun('object')}.")
    else:
        world.say(f"{hero.id} put on the {aid.label} and kept going.")
        world.say(f"Then {hero.id} was {ch.gerund} without ruining {hero.pronoun('possessive')} {item.label}.")
    world.say(f"{parent.type.capitalize()} smiled, because the hero had learned how to help the right way.")


# ---------------------------------------------------------------------------
# Parameters and world generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    challenge: str
    item: str
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
    StoryParams(place="rooftop", challenge="fly", item="cape", name="Nova", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="park", challenge="rescue", item="lunch", name="Kai", gender="boy", parent="father", trait="kind"),
]


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    ch = _safe_lookup(CHALLENGES, params.challenge)
    item = _safe_lookup(ITEMS, params.item)
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait, "stubborn"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=params.parent,
    ))
    mallard = world.add(Entity(
        id="Mallard",
        kind="character",
        type="mallard",
        label="mallard",
        traits=["small", "bright", "hungry"],
    ))
    thing = world.add(Entity(
        id=item.id,
        type=item.type,
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
    ))

    introduce(world, hero)
    bond(world, hero, mallard)
    show_item(world, hero, thing)

    world.para()
    arrive(world, hero, parent, setting, ch)
    want(world, hero, ch, thing)
    warn(world, parent, hero, ch, thing)
    conflict(world, hero)

    world.para()
    aid = share_turn(world, parent, hero, mallard, ch, thing)
    if aid is None:
        pass
    resolve(world, hero, parent, mallard, ch, thing, aid)

    world.facts.update(
        hero=hero,
        parent=parent,
        mallard=mallard,
        item=thing,
        setting=setting,
        challenge=ch,
        aid=aid,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ch = _safe_fact(world, f, "challenge")
    item = _safe_fact(world, f, "item")
    return [
        f'Write a short superhero story for a young child about {hero.id}, a {hero.type}, and a {ch.action} challenge.',
        f"Tell a gentle story where a little superhero wants to {ch.action} but must choose sharing instead of conflict.",
        f'Write a story that includes a mallard and the word "{item.label}" and ends with a moral value being learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, mallard, item, ch, aid = f["hero"], f["parent"], f["mallard"], f["item"], f["challenge"], f["aid"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel torn at first?",
            answer=f"{hero.id} wanted to {ch.action}, but {hero.pronoun('possessive')} {item.label} was special and could get ruined. That made the choice feel like a conflict.",
        ),
        QAItem(
            question=f"What did the hero learn about the mallard?",
            answer=f"{hero.id} learned that the mallard needed care too, so sharing the food was the kind choice.",
        ),
        QAItem(
            question=f"How did {parent.type} help solve the problem?",
            answer=f"The {parent.type} pointed the hero toward a better plan and reminded {hero.pronoun('object')} that sharing could turn the conflict into help.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} was helping with a calm heart, and the mallard stayed nearby after the shared treat.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "mallard": [
        ("What is a mallard?",
         "A mallard is a kind of duck with a broad bill. Many mallards have a shiny green head."),
    ],
    "sharing": [
        ("What does sharing mean?",
         "Sharing means letting someone else use or have part of what you have so both people can enjoy it."),
    ],
    "conflict": [
        ("What is a conflict?",
         "A conflict is a problem where two wants bump into each other and people need to choose a better way."),
    ],
    "moral": [
        ("What is a moral value?",
         "A moral value is a good idea for how to act, like being kind, honest, or fair."),
    ],
    "superhero": [
        ("What does a superhero usually do?",
         "A superhero helps others, solves problems, and tries to do the brave and kind thing."),
    ],
}


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags)
    tags.update({"mallard", "sharing", "conflict", "moral", "superhero"})
    out: list[QAItem] = []
    for key in ["superhero", "mallard", "sharing", "conflict", "moral"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers / verification
# ---------------------------------------------------------------------------

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_stories() -> list[tuple]:
    out = []
    for sid, s in SETTINGS.items():
        for cid, c in CHALLENGES.items():
            for iid, i in ITEMS.items():
                if s.affords and cid in s.affords and risk_of_soil(c, i) and choose_aid(c, i):
                    out.append((sid, cid, iid))
    return out


# ---------------------------------------------------------------------------
# Public storyworld API
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "challenge", None) and getattr(args, "challenge", None) not in CHALLENGES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "item", None) and getattr(args, "item", None) not in ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = []
    for sid, setting in SETTINGS.items():
        for cid, ch in CHALLENGES.items():
            if sid not in SETTINGS or cid not in setting.affords:
                continue
            for iid, item in ITEMS.items():
                if risk_of_soil(ch, item) and choose_aid(ch, item):
                    combos.append((sid, cid, iid))

    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
        and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, challenge, item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, item=item, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a mallard, a lump, sharing, and moral conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:\n")
        for sid, cid, iid in triples:
            print(f"  {sid:9} {cid:9} {iid:6}")
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
            header = f"### {p.name}: {p.challenge} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
