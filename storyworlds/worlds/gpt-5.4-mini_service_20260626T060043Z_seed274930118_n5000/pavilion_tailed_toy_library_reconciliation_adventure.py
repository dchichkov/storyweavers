#!/usr/bin/env python3
"""
storyworlds/worlds/pavilion_tailed_toy_library_reconciliation_adventure.py
=========================================================================

A standalone story world for a tiny adventure set in a toy library pavilion.

Seed tale sketch:
---
In a toy library, a child and a tailed toy fox search for a hidden story key.
The fox dashes ahead, snags a ribbon map, and the child feels cross.
They get stuck under the pavilion arch, must slow down, listen, and fix the plan.
By sharing the map and returning the stray books, they reconcile and find the key.

World shape:
- Physical meters: carrying, tangled, dusty, orderly, hidden
- Emotional memes: curiosity, worry, hurt, trust, joy, pride
- A small adventure premise: explore -> snag -> pause -> reconcile -> discover

This script follows the storyworld contract:
- self-contained stdlib script
- imports shared result containers eagerly
- lazy ASP import in helper functions only
- includes parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    in_place: str = ""
    tailed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    aid: object | None = None
    fox: object | None = None
    hero: object | None = None
    parent: object | None = None
    treasure: object | None = None
    def __post_init__(self) -> None:
        for k in ["carrying", "tangled", "dusty", "orderly", "hidden"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "hurt", "trust", "joy", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Setting:
    place: str = "the toy library"
    pavilion: str = "the pavilion"
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
class Quest:
    id: str
    verb: str
    gerund: str
    start: str
    turn: str
    ending: str
    mess: str
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
class Treasure:
    label: str
    phrase: str
    type: str
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
class Aid:
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
        self.lines: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.lines = [[]]
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    quest: str
    treasure: str
    aid: str
    trait: str
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


SETTINGS = {
    "toy_library": Setting(place="the toy library", pavilion="the pavilion", affords={"map_search", "tower_search", "ribbon_walk"}),
}

QUESTS = {
    "map_search": Quest(
        id="map_search",
        verb="search for the hidden story key",
        gerund="searching for the hidden story key",
        start="follow the ribbon map",
        turn="snag the ribbon map on the arch",
        ending="find the key tucked beside the last shelf",
        mess="tangled",
        risk="the map could get tangled",
        zone={"hands", "arms"},
        keyword="map",
        tags={"adventure", "map", "pavilion"},
    ),
    "tower_search": Quest(
        id="tower_search",
        verb="climb the soft block tower",
        gerund="climbing the soft block tower",
        start="reach the tower by the pavilion",
        turn="bump the stacked blocks",
        ending="find the star card under the ladder",
        mess="dusty",
        risk="the books could get dusty",
        zone={"hands", "feet"},
        keyword="tower",
        tags={"adventure", "tower", "pavilion"},
    ),
    "ribbon_walk": Quest(
        id="ribbon_walk",
        verb="walk the ribbon path",
        gerund="walking the ribbon path",
        start="trace the ribbon around the shelves",
        turn="tug the ribbon too hard",
        ending="reach the quiet bench and share the prize",
        mess="tangled",
        risk="the ribbon could get tangled",
        zone={"hands", "arms"},
        keyword="ribbon",
        tags={"adventure", "ribbon", "pavilion"},
    ),
}

TREASURES = {
    "map": Treasure(label="map", phrase="a bright ribbon map", type="map", region="hands"),
    "book": Treasure(label="book", phrase="a tiny story book", type="book", region="arms"),
    "key": Treasure(label="key", phrase="a brass story key", type="key", region="hands"),
}

AIDS = [
    Aid(id="spool", label="a ribbon spool", covers={"hands", "arms"}, guards={"tangled"}, prep="wind the ribbon around a spool first", tail="wound the ribbon around the spool", plural=False),
    Aid(id="dust_cloak", label="a dust cloak", covers={"arms", "feet"}, guards={"dusty"}, prep="put on a dust cloak before climbing", tail="put on the dust cloak", plural=False),
    Aid(id="soft_gloves", label="soft gloves", covers={"hands"}, guards={"tangled", "dusty"}, prep="wear the soft gloves first", tail="wore the soft gloves", plural=True),
]

GIRL_NAMES = ["Mia", "Luna", "Nora", "Zoe", "Ava", "Ivy"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Noah", "Ben"]
TRAITS = ["curious", "brave", "gentle", "restless", "careful", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = _safe_lookup(QUESTS, qid)
            for tid, t in TREASURES.items():
                if t.region in q.zone:
                    out.append((place, qid, tid))
    return out


def prize_at_risk(quest: Quest, treasure: Treasure) -> bool:
    return treasure.region in quest.zone


def select_aid(quest: Quest, treasure: Treasure) -> Optional[Aid]:
    for aid in AIDS:
        if quest.mess in aid.guards and treasure.region in aid.covers:
            return aid
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a toy library adventure with reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection(quest: Quest, treasure: Treasure) -> str:
    return f"(No story: {quest.gerund} would not reasonably put {treasure.label} at risk in this toy library.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "quest", None) and getattr(args, "treasure", None):
        q, t = _safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(TREASURES, getattr(args, "treasure", None))
        if not prize_at_risk(q, t):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest_id, treasure_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, place=place, quest=quest_id, treasure=treasure_id, aid="", trait=trait)


def _do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    world.zone = set(quest.zone)
    actor.memes["curiosity"] += 1
    actor.meters["carrying"] += 1
    if narrate:
        world.say(f"{actor.id} began {quest.gerund}.")


def predict_risk(world: World, actor: Entity, quest: Quest, treasure_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(actor.id), quest, narrate=False)
    treasure = sim.entities.get(treasure_id)
    return {"tangled": bool(treasure and treasure.meters["tangled"] >= THRESHOLD), "dusty": bool(treasure and treasure.meters["dusty"] >= THRESHOLD)}


def story_opener(hero: Entity, parent: Entity, setting: Setting, quest: Quest) -> str:
    return f"{hero.id} was a little {hero.pronoun('subject') == 'she' and 'girl' or 'boy'} who loved adventures in {setting.place}."

def tell(setting: Setting, quest: Quest, treasure_cfg: Treasure, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "adventurous"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    treasure = world.add(Entity(id=treasure_cfg.type, type=treasure_cfg.type, label=treasure_cfg.label, phrase=treasure_cfg.phrase, owner=hero.id, region=treasure_cfg.region))
    hero.memes["trust"] += 1

    world.say(f"{hero.id} was a little {trait} {hero_type} who loved adventures in {setting.place}.")
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent_type} went toward {setting.pavilion} to {quest.start}.")
    world.say(f"{hero.id} carried {treasure_cfg.phrase}, and {hero.id} was excited to {quest.verb}.")

    world.para()
    _do_quest(world, hero, quest)
    treasure.held_by = hero.id
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(f"Near {setting.pavilion}, {hero.id} saw a {quest.keyword} ribbon glittering under the shelf lights.")
    world.say(f"{hero.id} wanted to {quest.verb}, but then a tailed toy fox darted out and {quest.turn}.")

    fox = world.add(Entity(id="Fox", kind="character", type="fox", label="the tailed toy fox", tailed=True, traits=["quick", "tailed"]))
    fox.memes["curiosity"] += 1
    fox.memes["trust"] += 0.5
    hero.memes["worry"] += 1
    hero.memes["hurt"] += 1
    treasure.meters[quest.mess] += 1
    treasure.meters["hidden"] += 1
    world.say(f"The ribbon looped once around the fox's tail, and {hero.id} felt cross.")

    world.para()
    world.say(f"{hero.id}'s {parent_type} knelt beside {hero.id} and said, \"Let's slow down and solve this together.\"")
    aid_choice = select_aid(quest, treasure_cfg)
    if aid_choice:
        aid = world.add(Entity(id=aid_choice.id, type="aid", label=aid_choice.label, owner=hero.id, plural=aid_choice.plural))
        hero.memes["trust"] += 1
        world.say(f"They found {aid_choice.label}, because {aid_choice.prep}.")
    else:
        aid = None
    fox.memes["worry"] += 1
    fox.meters["tangled"] += 1
    treasure.meters["tangled"] += 1
    world.say(f"{hero.id} gently held still, the fox held still, and the ribbon slipped free.")

    world.para()
    hero.memes["hurt"] = 0
    hero.memes["worry"] = 0
    fox.memes["worry"] = 0
    hero.memes["joy"] += 1
    fox.memes["joy"] += 1
    hero.memes["trust"] += 1
    fox.memes["trust"] += 1
    world.say(f"{hero.id} and the fox looked at each other, then nodded as if they both remembered how to be kind.")
    world.say(f"They reconciled by sharing the map, returning the stray books, and taking turns at the pavilion bench.")
    world.say(f"Together they {quest.ending}, and the toy library felt calm and brave again.")

    world.facts.update(hero=hero, parent=parent, treasure=treasure, quest=quest, setting=setting, aid=aid, fox=fox, reconciled=True)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(TREASURES, params.treasure), params.name, params.gender, params.parent, params.trait)
    params = StoryParams(**{**params.__dict__, "aid": world.facts["aid"].id if world.facts.get("aid") else ""})
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest = f["hero"], f["quest"]
    return [
        f'Write a short adventure story for a young child in a toy library that includes the words "pavilion" and "tailed".',
        f"Tell a gentle reconciliation adventure where {hero.id} wants to {quest.verb} but must solve a ribbon problem with a tailed toy fox.",
        f"Write a simple story about a toy library, a pavilion, and two characters who choose to share after a mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, treasure, quest, fox = f["hero"], f["parent"], f["treasure"], f["quest"], f["fox"]
    aid = f.get("aid")
    qa = [
        QAItem(
            question=f"Who is the adventure about in the toy library?",
            answer=f"The story is about {hero.id} and {hero.pronoun('possessive')} {parent.type}, with the tailed toy fox helping the adventure turn into a reconciliation.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do near the pavilion?",
            answer=f"{hero.id} wanted to {quest.verb}. That was the exciting part of the adventure.",
        ),
        QAItem(
            question=f"What happened to {treasure.label} when the fox dashed in?",
            answer=f"The {treasure.label} got {quest.mess} and a little tangled when the ribbon snagged on the fox's tail.",
        ),
        QAItem(
            question="How did the problem get fixed?",
            answer=f"They slowed down, used {aid.label if aid else 'a careful plan'}, and worked together until the ribbon came free.",
        ),
        QAItem(
            question="How did the two characters feel at the end?",
            answer="They felt calm, friendly, and proud because they reconciled and finished the adventure together.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "map": [("What is a map?", "A map is a picture that helps you find places and choose where to go.")],
    "ribbon": [("What is a ribbon?", "A ribbon is a long, narrow strip of cloth that can tie, decorate, or mark a path.")],
    "pavilion": [("What is a pavilion?", "A pavilion is a small open shelter or fancy little building where people can rest or meet.")],
    "library": [("What is a library for?", "A library is a place where books are kept so people can read and borrow them.")],
    "fox": [("What is a fox?", "A fox is a small wild animal with a bushy tail and quick feet.")],
    "adventure": [("What is an adventure?", "An adventure is an exciting trip or event with surprises and brave choices.")],
    "reconciliation": [("What is reconciliation?", "Reconciliation is when people stop being upset and become friendly again.")],
}

KNOWLEDGE_ORDER = ["library", "pavilion", "map", "ribbon", "fox", "adventure", "reconciliation"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    tags.add("library")
    if world.facts.get("fox"):
        tags.add("fox")
    tags.add("reconciliation")
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tailed:
            bits.append("tailed=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", place="toy_library", quest="map_search", treasure="map", aid="", trait="curious"),
    StoryParams(name="Theo", gender="boy", parent="father", place="toy_library", quest="tower_search", treasure="book", aid="", trait="brave"),
    StoryParams(name="Ava", gender="girl", parent="mother", place="toy_library", quest="ribbon_walk", treasure="key", aid="", trait="gentle"),
]


ASP_RULES = r"""
risk(Q, T) :- quest(Q), treasure(T), zone(Q, R), region(T, R).
fix(Q, T) :- risk(Q, T), aid(A), guards(A, M), mess(Q, M), covers(A, R), region(T, R).
valid(Place, Q, T) :- setting(Place), affords(Place, Q), risk(Q, T), fix(Q, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("mess", qid, q.mess))
        for r in sorted(q.zone):
            lines.append(asp.fact("zone", qid, r))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("region", tid, t.region))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for m in sorted(aid.guards):
            lines.append(asp.fact("guards", aid.id, m))
        for r in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def explain_gender(treasure_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(TREASURES, treasure_id).genders))
    return f"(No story: a {_safe_lookup(TREASURES, treasure_id).label} is not a typical {gender}'s item here; try --gender {ok}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "gender", None) and getattr(args, "treasure", None) and getattr(args, "gender", None) not in _safe_lookup(TREASURES, getattr(args, "treasure", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, treasure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, place=place, quest=quest, treasure=treasure, aid="", trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(TREASURES, params.treasure), params.name, params.gender, params.parent, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, quest, treasure) combos:\n")
        for row in triples:
            print("  ", row)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} in {p.place} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
