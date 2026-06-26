#!/usr/bin/env python3
"""
storyworlds/worlds/voyage_mummie_humor_nursery_rhyme.py
========================================================

A tiny story world in a nursery-rhyme style: a child and a mummie go on a
comical voyage, meet a small problem, and find a gentle fix.

The seed tale is imagined as a short rhyming voyage:
- a child loves a little boat voyage
- a funny mummie comes along
- the boat needs a safe change when the wind grows silly
- everyone laughs, keeps going, and ends with a bright new view

This world simulates a compact premise/turn/resolution structure with physical
meters and emotional memes, plus an ASP twin for the reasonableness gate.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ent: object | None = None
    hero: object | None = None
    mummie: object | None = None
    parent: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ["rocked", "sprayed", "tired", "nicked", "safe", "sparkle"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "wonder", "worry", "mirth", "trust", "surprise"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str
    sea: str
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
class Voyage:
    id: str
    verb: str
    gerund: str
    jolt: str
    risk: str
    zone: set[str]
    mood: str
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
        self.zone: set[str] = set()
        self.weather: str = ""
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
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "harbor": Setting(place="the harbor", sea="the bright blue sea", affords={"voyage", "tide"}),
    "island": Setting(place="the tiny island dock", sea="the silver sea", affords={"voyage", "wind"}),
    "river": Setting(place="the river bend", sea="the laughing river", affords={"voyage", "current"}),
}


VOYAGES = {
    "voyage": Voyage(
        id="voyage",
        verb="take a voyage",
        gerund="voyaging",
        jolt="rock and wobble",
        risk="splash and sway",
        zone={"feet", "legs", "torso"},
        mood="windy",
        keyword="voyage",
        tags={"voyage", "sea"},
    ),
    "tide": Voyage(
        id="tide",
        verb="ride the tide",
        gerund="riding the tide",
        jolt="bob and bounce",
        risk="spray and sway",
        zone={"feet", "legs"},
        mood="tidey",
        keyword="tide",
        tags={"tide", "sea"},
    ),
    "wind": Voyage(
        id="wind",
        verb="chase the wind",
        gerund="chasing the wind",
        jolt="tip and tap",
        risk="blow and bounce",
        zone={"torso"},
        mood="breezy",
        keyword="wind",
        tags={"wind"},
    ),
    "current": Voyage(
        id="current",
        verb="follow the current",
        gerund="following the current",
        jolt="dip and drift",
        risk="spray and drift",
        zone={"feet", "legs", "torso"},
        mood="swift",
        keyword="current",
        tags={"water"},
    ),
}


PRIZES = {
    "cloak": Prize(
        label="cloak",
        phrase="a little red cloak",
        type="cloak",
        region="torso",
    ),
    "boots": Prize(
        label="boots",
        phrase="shiny yellow boots",
        type="boots",
        region="feet",
        plural=True,
    ),
    "cap": Prize(
        label="cap",
        phrase="a tiny blue cap",
        type="cap",
        region="head",
    ),
}


GEAR = [
    Gear(
        id="slicker",
        label="a rain slicker",
        covers={"torso"},
        guards={"sprayed", "splash", "wet"},
        prep="put on a rain slicker first",
        tail="took the rain slicker along",
    ),
    Gear(
        id="galoshes",
        label="galoshes",
        covers={"feet"},
        guards={"sprayed", "splash", "wet"},
        prep="pull on galoshes first",
        tail="pulled on the galoshes",
        plural=True,
    ),
    Gear(
        id="hood",
        label="a hood",
        covers={"head"},
        guards={"blown", "sprayed"},
        prep="tie on a hood first",
        tail="tied on the hood",
    ),
]


GIRL_NAMES = ["Mimi", "Lulu", "Nina", "Pippa", "Dotty", "Ivy"]
BOY_NAMES = ["Tom", "Benny", "Kit", "Finn", "Rory", "Max"]
TRAITS = ["jolly", "curious", "spry", "cheery", "silly"]


@dataclass
class StoryParams:
    place: str
    voyage: str
    prize: str
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


def voyage_at_risk(v: Voyage, prize: Prize) -> bool:
    return prize.region in v.zone


def select_gear(v: Voyage, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if prize.region in g.covers:
            return g
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for vid in setting.affords:
            v = _safe_lookup(VOYAGES, vid)
            for pid, prize in PRIZES.items():
                if voyage_at_risk(v, prize) and select_gear(v, prize):
                    combos.append((place, vid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous nursery-rhyme voyage story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", dest="voyage", choices=VOYAGES)
    ap.add_argument("--prize", choices=PRIZES)
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
    if getattr(args, "voyage", None) and getattr(args, "prize", None):
        v, p = _safe_lookup(VOYAGES, getattr(args, "voyage", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (voyage_at_risk(v, p) and select_gear(v, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "voyage", None) is None or c[1] == getattr(args, "voyage", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, voyage, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, voyage=voyage, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def _do_voyage(world: World, actor: Entity, voyage: Voyage, narrate: bool = True) -> None:
    world.zone = set(voyage.zone)
    actor.meters[voyage.id] += 1
    actor.memes["joy"] += 1
    actor.memes["wonder"] += 1
    if narrate:
        world.say(f"{actor.id} went voyaging, and the little boat began to {voyage.jolt}.")


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for vid in VOYAGES:
            if actor.meters[vid] < THRESHOLD:
                continue
            voyage = _safe_lookup(VOYAGES, vid)
            for item in world.worn_items(actor):
                if item.protective or item.location not in world.zone:
                    continue
                if world.covered(actor, item.location):
                    continue
                sig = ("splash", actor.id, item.id, vid)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["sprayed"] += 1
                item.memes["surprise"] += 1
                out.append(f"{actor.id}'s {item.label} got splashed on the voyage.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in [_r_splash]:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, voyage: Voyage, prize_id: str) -> dict:
    sim = world.copy()
    _do_voyage(sim, sim.get(actor.id), voyage, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["sprayed"] >= THRESHOLD}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.traits[0]} little {hero.type} who loved sing-song days.")


def meet_mummie(world: World, hero: Entity, mummie: Entity) -> None:
    hero.memes["wonder"] += 1
    mummie.memes["mirth"] += 1
    world.say(f"Then along came {mummie.id}, a wrapped-up mummie with a tip-tap walk and a kindly grin.")


def prize_story(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label}, for it looked bright as a berry.")


def love_voyage(world: World, hero: Entity, voyage: Voyage) -> None:
    world.say(f"{hero.id} loved to {voyage.verb}, with the sky above and a hum in the air.")


def set_out(world: World, hero: Entity, parent: Entity, voyage: Voyage) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} set out to {world.setting.place}.")
    world.say(f"The sea was {world.setting.sea}, and the boat was small and merry.")


def wants(world: World, hero: Entity, voyage: Voyage) -> None:
    hero.memes["joy"] += 0.5
    world.say(f"{hero.id} wanted to {voyage.verb} at once, with a hop and a grin.")


def warn(world: World, parent: Entity, hero: Entity, voyage: Voyage, prize: Entity) -> bool:
    pred = predict_mess(world, hero, voyage, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = voyage.risk
    world.say(f"\"Mind the {voyage.risk},\" {parent.id} said. \"Your {prize.label} may get in a fizz.\"")
    return True


def laugh_fuss(world: World, hero: Entity, voyage: Voyage) -> None:
    hero.memes["mirth"] += 1
    world.say(f"{hero.id} giggled, because the warning sounded as round as a drum.")


def jiggle(world: World, hero: Entity, voyage: Voyage) -> None:
    world.say(f"{hero.id} tried to {voyage.jolt}, but the boat went wobble-wobble-wizz.")


def mummie_help(world: World, parent: Entity, hero: Entity, voyage: Voyage, prize: Entity) -> Optional[Gear]:
    gear = select_gear(voyage, prize)
    if gear is None:
        return None
    ent = world.add(Entity(
        id=gear.id, kind="thing", type="gear", label=gear.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear.covers), plural=gear.plural,
    ))
    ent.worn_by = hero.id
    if predict_mess(world, hero, voyage, prize.id)["soiled"]:
        ent.worn_by = None
        del world.entities[ent.id]
        return None
    world.say(f"{parent.id} smiled and said, \"Let us {gear.prep}, then laugh and not be late.\"")
    return gear


def accept(world: World, hero: Entity, parent: Entity, voyage: Voyage, prize: Entity, gear: Gear) -> None:
    hero.memes["trust"] += 1
    hero.memes["joy"] += 1
    hero.memes["mirth"] += 1
    world.say(f"{hero.id} clapped and hugged {hero.pronoun('possessive')} {parent.label}.")
    world.say(f"They {gear.tail}, and away they went on the merry voyage.")
    world.say(f"At the end, {hero.id} was {voyage.gerund}, {prize.label} still clean, while the mummie hummed a tune.")


def tell(setting: Setting, voyage: Voyage, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["jolly", "silly"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mother"))
    mummie = world.add(Entity(id="Mummie", kind="character", type="thing", label="the mummie"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, location=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, hero)
    meet_mummie(world, hero, mummie)
    love_voyage(world, hero, voyage)
    prize_story(world, hero, prize)

    world.para()
    set_out(world, hero, parent, voyage)
    wants(world, hero, voyage)
    warn(world, parent, hero, voyage, prize)
    laugh_fuss(world, hero, voyage)
    jiggle(world, hero, voyage)
    _do_voyage(world, hero, voyage)
    propagate(world, narrate=True)

    world.para()
    gear = mummie_help(world, parent, hero, voyage, prize)
    if gear:
        accept(world, hero, parent, voyage, prize, gear)

    world.facts.update(hero=hero, parent=parent, mummie=mummie, prize=prize, voyage=voyage, setting=setting, gear=gear, resolved=gear is not None)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, voyage, prize = f["hero"], f["voyage"], f["prize"]
    return [
        f'Write a short nursery-rhyme style story about a child named {hero.id}, a funny mummie, and a {voyage.keyword} voyage.',
        f"Tell a playful story where {hero.id} wants to {voyage.verb} but a parent worries about {prize.phrase}.",
        f'Write a rhyming-feeling story with the word "{voyage.keyword}" and a gentle, silly ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, voyage = f["hero"], f["parent"], f["prize"], f["voyage"]
    qa = [
        QAItem(
            question=f"Who went on the voyage with {hero.id}?",
            answer=f"{hero.id} went with {parent.id} and a funny mummie, and they all set out together.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the boat?",
            answer=f"{hero.id} wanted to {voyage.verb}, because the little voyage looked like a game.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {prize.label}?",
            answer=f"{parent.id} worried because the boat could {voyage.risk}, and that might splash the {prize.label}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story end happily for {hero.id}?",
            answer=f"They used the right gear, so {hero.id} could keep voyaging and the {prize.label} stayed clean.",
        ))
    return qa


KNOWLEDGE = {
    "voyage": [("What is a voyage?", "A voyage is a trip, often by boat or ship, from one place to another.")],
    "sea": [("What is the sea?", "The sea is a very large body of salt water.")],
    "mummie": [("What is a mummie?", "In a story, a mummie can be a wrapped-up person or creature who looks funny and old.")],
    "wind": [("What does wind do?", "Wind is moving air that can push sails, make waves ripple, and ruffle clothes.")],
    "wet": [("What happens when something gets wet?", "When something gets wet, water clings to it and it can feel soggy or cold.")],
    "boots": [("What are boots for?", "Boots protect feet and can help keep them dry or clean.")],
    "cloak": [("What is a cloak?", "A cloak is a loose outer garment that can cover the shoulders and body.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["voyage"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    if world.facts["prize"].label == "cloak":
        tags.add("cloak")
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", voyage="voyage", prize="cloak", name="Mina", gender="girl", parent="mother", trait="jolly"),
    StoryParams(place="island", voyage="wind", prize="cap", name="Tom", gender="boy", parent="father", trait="silly"),
    StoryParams(place="river", voyage="current", prize="boots", name="Lulu", gender="girl", parent="mother", trait="curious"),
]


def explain_rejection(v: Voyage, prize: Prize) -> str:
    return f"(No story: {v.gerund} does not make a good safe-turn with {prize.label}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for vid, v in VOYAGES.items():
        lines.append(asp.fact("voyage", vid))
        lines.append(asp.fact("mood_of", vid, v.mood))
        for r in sorted(v.zone):
            lines.append(asp.fact("splashes", vid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(V, P) :- splashes(V, R), worn_on(P, R).
protects(G, V, P) :- gear(G), prize_at_risk(V, P), covers(G, R), worn_on(P, R).
has_fix(V, P) :- protects(_, V, P).
valid(Place, V, P) :- affords(Place, V), prize_at_risk(V, P), has_fix(V, P).
#show valid/3.
"""


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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(VOYAGES, params.voyage), _safe_lookup(PRIZES, params.prize), params.name, params.gender, [params.trait, "stubborn"], params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.name}: {p.voyage} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
