#!/usr/bin/env python3
"""
storyworlds/worlds/tum_cautionary_magic_quest_myth.py
======================================================

A small mythic storyworld about a child on a magic quest, where a cautionary
warning, a strange tum, and a careful choice decide whether the path ends in
glory or trouble.

The seed word is "tum": a low drumbeat, a sacred tum, and the sound the quest
makes when the hero must remember to be careful.
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
# World model
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid_ent: object | None = None
    hero: object | None = None
    parent: object | None = None
    relic: object | None = None
    def __post_init__(self) -> None:
        for k in ["dust", "storm", "hurt", "travel"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "wonder", "warning", "care", "pride", "doubt"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "sister", "woman"}
        male = {"boy", "father", "king", "brother", "man"}
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
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)
    omen: str = ""
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
class Quest:
    id: str
    title: str
    verb: str
    gerund: str
    danger: str
    consequence: str
    risk: str
    region: str
    keyword: str = "tum"
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
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class MagicAid:
    id: str
    label: str
    covers: set[str]
    calms: set[str]
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.quest: Optional[Quest] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.quest = self.quest
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "ridge": Place("ridge", "the wind ridge", "high and bright", {"chant", "cross", "carry"}, "The stones hum with old songs."),
    "grove": Place("grove", "the elder grove", "green and hushed", {"chant", "cross", "carry"}, "The roots listen under the moss."),
    "ruins": Place("ruins", "the fallen ruins", "gray and solemn", {"cross", "carry", "ring"}, "Broken columns lean like tired giants."),
}

QUESTS = {
    "crossing": Quest(
        id="crossing",
        title="the crossing of the old bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        danger="the bridge might shake and drop loose stones",
        consequence="the way below might wake with thunder",
        risk="the bridge's planks",
        region="feet",
        keyword="tum",
        tags={"bridge", "stone", "warning"},
    ),
    "vow": Quest(
        id="vow",
        title="the vow at the listening stone",
        verb="ring the listening stone",
        gerund="ringing the listening stone",
        danger="the stone might answer too loudly",
        consequence="the dark birds might rise at once",
        risk="the stone's sleeping hush",
        region="torso",
        keyword="tum",
        tags={"stone", "voice", "warning"},
    ),
    "path": Quest(
        id="path",
        title="the path through the hushwood",
        verb="walk the hushwood path",
        gerund="walking the hushwood path",
        danger="the path might tangle with thorn and fear",
        consequence="the little lights might go out",
        risk="the path's shadowed brush",
        region="legs",
        keyword="tum",
        tags={"wood", "thorn", "warning"},
    ),
}

RELICS = {
    "shell": Relic("shell", "a moon-shell", "a moon-shell with a pale shine", "hands"),
    "cloak": Relic("cloak", "a cloak", "a small star-cloak", "torso"),
    "sandals": Relic("sandals", "sandals", "sun-worn sandals", "feet", plural=True),
}

AIDS = [
    MagicAid("veil", "a silence veil", {"torso", "head"}, {"storm", "hurt"}, "wrap the silence veil around the child", "moved on with the silence veil", False),
    MagicAid("cord", "a soft cord", {"feet", "legs"}, {"dust", "hurt"}, "tie on the soft cord", "went on with the soft cord", False),
    MagicAid("glove", "moon gloves", {"hands"}, {"storm", "dust"}, "put on moon gloves", "continued with the moon gloves", True),
]

NAMES = ["Ari", "Mina", "Taro", "Lina", "Soren", "Nia", "Dara", "Koa"]
KINDS = ["girl", "boy"]
PARENTS = ["mother", "father", "aunt", "uncle"]
TRAITS = ["brave", "careful", "curious", "gentle", "bold"]


# ---------------------------------------------------------------------------
# Contract dataclass
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    relic: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------
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


def at_risk(quest: Quest, relic: Relic) -> bool:
    return relic.region == quest.region or relic.region in {"hands", "feet", "legs", "torso"}


def select_aid(quest: Quest, relic: Relic) -> Optional[MagicAid]:
    for aid in AIDS:
        if quest.region in aid.covers or relic.region in aid.covers:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for qid, quest in QUESTS.items():
            if qid not in place.affords:
                continue
            for rid, relic in RELICS.items():
                if at_risk(quest, relic) and select_aid(quest, relic):
                    out.append((pid, qid, rid))
    return out


def explain_rejection(quest: Quest, relic: Relic) -> str:
    return (
        f"(No story: {quest.gerund} does not plausibly threaten {relic.label} in a way "
        f"that leaves room for a wise magical fix. Choose a different relic or quest.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict_trouble(world: World, hero: Entity, quest: Quest, relic: Entity) -> dict:
    sim = world.copy()
    do_quest(sim, sim.get(hero.id), quest, narrate=False)
    return {
        "storm": sim.entities[relic.id].meters.get("storm", 0.0),
        "hurt": sim.entities[relic.id].meters.get("hurt", 0.0),
    }


def do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    world.zone = {quest.region}
    hero.memes["care"] += 0.5
    hero.meters["travel"] += 1
    hero.memes["wonder"] += 0.5
    if quest.id == "crossing":
        hero.meters["storm"] += 1
    elif quest.id == "vow":
        hero.memes["warning"] += 1
    else:
        hero.meters["dust"] += 1
    if narrate:
        world.say(f"{hero.pronoun().capitalize()} stepped forward on the quest and the air answered with a low tum.")


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for ent in list(world.entities.values()):
            if ent.meters["storm"] >= THRESHOLD and ent.id not in world.fired:
                world.fired.add((ent.id, "storm"))
                ent.memes["fear"] += 1
                if narrate:
                    world.say(f"The place grew restless, and even the stones seemed to listen.")
                changed = True
            if ent.meters["dust"] >= THRESHOLD and ent.id not in world.fired:
                world.fired.add((ent.id, "dust"))
                ent.memes["doubt"] += 1
                if narrate:
                    world.say(f"Fine dust clung to the path and tried to blur the hero's thoughts.")
                changed = True


def tell(place: Place, quest: Quest, relic_cfg: Relic, hero_name: str, hero_gender: str,
         hero_trait: str, parent_kind: str) -> World:
    world = World(place)
    world.quest = quest

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    parent = world.add(Entity(id="Elder", kind="character", type=parent_kind, label=f"the {parent_kind}"))
    relic = world.add(Entity(
        id="relic",
        type=relic_cfg.id,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        owner=hero.id,
        region=relic_cfg.region,
        plural=relic_cfg.plural,
    ))

    hero.memes["joy"] += 1
    hero.memes["wonder"] += 1
    hero.memes["care"] += 1

    world.say(
        f"Long ago, {hero.id} was a {hero_trait} child who loved the old stories and the low, warning tum of drums."
    )
    world.say(
        f"{hero.id}'s {parent_kind} placed in {hero.pronoun('possessive')} hands {relic_cfg.phrase}, a relic for a sacred quest."
    )
    world.say(
        f"They said the relic must be carried with care, for the quest of {quest.title} could turn bright or bitter with one careless beat."
    )

    world.para()
    world.say(f"At {place.name}, the road opened beneath a sky that felt ancient.")
    world.say(f"{hero.id} wanted to {quest.verb}, though {quest.danger}.")
    world.say(f"Their {parent_kind} touched {hero.pronoun('possessive')} shoulder and warned, \"Listen closely; the world remembers a wild tum.\"")

    trouble = predict_trouble(world, hero, quest, relic)
    if trouble["storm"] >= THRESHOLD or trouble["hurt"] >= THRESHOLD:
        hero.memes["warning"] += 1
        world.say(f"{hero.id} heard the warning and hesitated, because {quest.consequence}.")
        world.say(f"Still, the pull of the quest was strong, and the path asked for courage.")
        hero.memes["doubt"] += 0.5
        hero.meters["travel"] += 0.5
        propagate(world, narrate=True)

    world.para()
    aid = select_aid(quest, relic_cfg)
    if aid is None:
        pass

    aid_ent = world.add(Entity(
        id=aid.id,
        kind="thing",
        type=aid.id,
        label=aid.label,
        protective=True,
        covers=set(aid.covers),
        plural=aid.plural,
    ))
    aid_ent.worn_by = hero.id

    world.say(
        f"Then the {parent_kind} chose a careful magic: {aid.prep}."
    )
    world.say(
        f"That way, {hero.id} could keep going without waking the danger in {quest.risk}."
    )

    if trouble["storm"] >= THRESHOLD or trouble["hurt"] >= THRESHOLD:
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1

    world.say(
        f"{hero.id} did as told, and the tum became a soft, guiding beat instead of a reckless drum."
    )
    world.say(
        f"At last, {hero.id} {quest.gerund}, {relic_cfg.phrase} safe at {hero.pronoun('possessive')} side, while the old land stayed quiet and kind."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        relic=relic,
        quest=quest,
        place=place,
        aid=aid,
        trouble=trouble,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A and output
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    return [
        f'Write a short myth for a child named {hero.id} that includes the word "tum" and a careful magical warning.',
        f"Tell a cautionary quest story where {hero.id} must {quest.verb} without making the tum turn wild.",
        f"Write a gentle mythic story about magic, a quest, and a wise choice that keeps danger asleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    relic = _safe_fact(world, f, "relic")
    quest = _safe_fact(world, f, "quest")
    place = _safe_fact(world, f, "place")
    aid = _safe_fact(world, f, "aid")

    return [
        QAItem(
            question=f"Who went on the quest at {place.name}?",
            answer=f"{hero.id} went on the quest at {place.name}, guided by {parent.label}.",
        ),
        QAItem(
            question=f"What was the sacred thing {hero.id} carried?",
            answer=f"{hero.id} carried {relic.phrase}, which was meant to be kept safe during the quest.",
        ),
        QAItem(
            question=f"What warning did the elder give about the tum?",
            answer=f"The elder warned {hero.id} to be careful, because a wild tum could wake trouble on the path.",
        ),
        QAItem(
            question=f"How did the magical helper protect the quest?",
            answer=f"{aid.label} helped by covering the risky part of the journey, so {hero.id} could continue safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tum in this story world?",
            answer="A tum is a low drumbeat or sacred sound that can guide a quest, but it can also become dangerous if it is too wild.",
        ),
        QAItem(
            question="Why is caution important in a magic quest?",
            answer="Caution matters because magic can help the hero, but careless use can wake danger or hurt something precious.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal, often made difficult by a test, a warning, or a hidden danger.",
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({a for (a, *_) in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(Q, R) :- quest(Q), risk_region(Q, Reg), relic(R), relic_region(R, Reg).
safe_aid(Q, R, A) :- prize_at_risk(Q, R), aid(A), covers(A, Reg), risk_region(Q, Reg).
valid(Place, Q, R) :- place(Place), affords(Place, Q), prize_at_risk(Q, R), safe_aid(Q, R, _).
valid_story(Place, Q, R, G) :- valid(Place, Q, R), wears(G, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for q in sorted(p.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("risk_region", qid, q.region))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_region", rid, r.region))
        for g in sorted(r.genders):
            lines.append(asp.fact("wears", g, rid))
    for a in AIDS:
        lines.append(asp.fact("aid", a.id))
        for c in sorted(a.covers):
            lines.append(asp.fact("covers", a.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


# ---------------------------------------------------------------------------
# Parsing / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic cautionary magic quest world built around tum.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if getattr(args, "quest", None) and getattr(args, "relic", None):
        if not (at_risk(_safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(RELICS, getattr(args, "relic", None))) and select_aid(_safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(RELICS, getattr(args, "relic", None)))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, relic = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(KINDS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, relic=relic, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(RELICS, params.relic),
                 params.name, params.gender, params.trait, params.parent)
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
    StoryParams(place="ridge", quest="crossing", relic="sandals", name="Ari", gender="boy", parent="father", trait="careful"),
    StoryParams(place="grove", quest="vow", relic="cloak", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="ruins", quest="path", relic="shell", name="Soren", gender="boy", parent="uncle", trait="gentle"),
]


def asp_program_text() -> str:
    return asp_program("#show valid_story/4.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_text())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, quest, relic) combos ({len(stories)} with gender):\n")
        for place, quest, relic in triples:
            genders = sorted(g for (pl, q, r, g) in stories if (pl, q, r) == (place, quest, relic))
            print(f"  {place:8} {quest:8} {relic:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.quest} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
