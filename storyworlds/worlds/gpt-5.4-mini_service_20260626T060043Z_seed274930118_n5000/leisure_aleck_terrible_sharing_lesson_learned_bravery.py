#!/usr/bin/env python3
"""
A standalone story world: leisure time aboard a small space station, where
Aleck learns that sharing, bravery, and a hard lesson can turn a terrible
problem into a better ending.

The simulated premise is simple:
- Aleck is enjoying leisure time in a dockside habitat.
- A valuable glow-gadget is needed for a shared game.
- A terrible snag threatens the fun.
- Aleck has to choose between keeping things for himself or sharing.
- A small brave act leads to a lesson learned and a warmer ending image.

This file follows the Storyweavers single-script contract:
- self-contained stdlib script
- shared result containers imported eagerly
- ASP helper imported lazily
- generate / emit / parser / main / params
- world state drives prose and Q&A
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    region: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
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
class Prize:
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
class Helper:
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.id in self.entities and region in getattr(item, "covers", set()) for item in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "leisure_deck": Setting(place="the leisure deck", indoors=True, affords={"float_kite", "starglow", "snap_ball"}),
    "observation_bay": Setting(place="the observation bay", indoors=True, affords={"float_kite", "starglow"}),
    "moon_garden": Setting(place="the moon garden", indoors=False, affords={"snap_ball"}),
}

ACTIVITIES = {
    "float_kite": Activity(
        id="float_kite",
        verb="fly the float-kite",
        gerund="flying the float-kite",
        rush="dash after the float-kite",
        risk="the kite string could tangle the lights",
        mess="twisted",
        zone={"hands", "torso"},
        keyword="kite",
        tags={"kite", "brave"},
    ),
    "starglow": Activity(
        id="starglow",
        verb="chase starlight beads",
        gerund="chasing starlight beads",
        rush="run toward the beacon",
        risk="the glow gel might smear on the gloves",
        mess="glowy",
        zone={"hands"},
        keyword="starlight",
        tags={"light", "glow"},
    ),
    "snap_ball": Activity(
        id="snap_ball",
        verb="play snap-ball",
        gerund="playing snap-ball",
        rush="leap for the bouncing ball",
        risk="the ball might knock a snack tray over",
        mess="scuffed",
        zone={"hands", "feet"},
        keyword="ball",
        tags={"ball", "game"},
    ),
}

PRIZES = {
    "badge": Prize(label="badge", phrase="a shiny badge", type="badge", region="torso"),
    "gloves": Prize(label="gloves", phrase="soft pilot gloves", type="gloves", region="hands", plural=True),
    "cap": Prize(label="cap", phrase="a bright captain cap", type="cap", region="head"),
}

HELPERS = [
    Helper(
        id="tether",
        label="a tether clip",
        covers={"hands", "torso"},
        guards={"twisted"},
        prep="clip on a tether first",
        tail="clipped on the tether and tried again",
    ),
    Helper(
        id="cleanwrap",
        label="a clean wrap",
        covers={"hands"},
        guards={"glowy"},
        prep="wrap the gloves first",
        tail="wrapped the gloves and returned to the game",
    ),
    Helper(
        id="softpads",
        label="soft pads",
        covers={"hands", "feet"},
        guards={"scuffed"},
        prep="put on soft pads first",
        tail="put on soft pads and came back smiling",
        plural=True,
    ),
]

NAMES = ["Aleck", "Mina", "Jori", "Nia", "Pip", "Toma", "Luna", "Rey"]
TRAITS = ["curious", "careful", "brave", "playful", "quiet"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str = "Aleck"
    gender: str = "boy"
    parent: str = "captain"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
prize_at_risk(A,P) :- zone_of(A,R), prize_region(P,R).
fix(A,P) :- prize_at_risk(A,P), activity_mess(A,M), helper_guards(G,M), helper_covers(G,R), prize_region(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), fix(A,P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("activity_mess", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone_of", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for g in sorted(h.guards):
            lines.append(asp.fact("helper_guards", h.id, g))
        for c in sorted(h.covers):
            lines.append(asp.fact("helper_covers", h.id, c))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone

def select_helper(activity: Activity, prize: Prize) -> Optional[Helper]:
    for h in HELPERS:
        if activity.mess in h.guards and prize.region in h.covers:
            return h
    return None

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_helper(act, prize):
                    out.append((place, act_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    act = sim.get(actor.id)
    act.memes["excited"] = act.memes.get("excited", 0) + 1
    act.meters[activity.mess] = act.meters.get(activity.mess, 0) + 1
    prize = sim.get(prize_id)
    soiled = prize.region in activity.zone
    return {"soiled": soiled}

def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved quiet time on the station.")

def establish_leisure(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"During leisure time, {hero.id} loved {activity.gerund} under the soft ship lights.")

def present_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} had given {hero.id} {hero.pronoun('object')} {prize.phrase}.")

def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")

def want_and_warn(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.risk
    world.say(f'"If you do that, {hero.id}, {activity.risk}," {hero.pronoun("possessive")} {parent.label} said.')
    return True

def feel_terrible(world: World, hero: Entity) -> None:
    hero.memes["trouble"] = hero.memes.get("trouble", 0) + 1
    world.say(f"That sounded terrible to {hero.id}, and the fun felt stuck for a moment.")

def brave_turn(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(f"Still, {hero.id} took a brave breath and reached for a better way forward.")

def share_and_fix(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> Optional[Helper]:
    helper = select_helper(activity, prize)
    if helper is None:
        return None
    world.say(f"{hero.id}'s {parent.label} offered {helper.label}, saying, \"We can share the good gear.\"")
    world.say(f"{hero.id} nodded and agreed to {helper.prep}.")
    return helper

def lesson_learned(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, helper: Helper) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["lesson"] = hero.memes.get("lesson", 0) + 1
    world.say(f"{hero.id} {helper.tail}, and the game felt fun again.")
    world.say(f"That day, {hero.id} learned that sharing could be braver than clinging to one thing.")
    world.say(f"At the end, {hero.id} was {activity.gerund}, and {prize.label} stayed safe and bright.")

def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, hero_traits: Optional[list[str]] = None, parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little"] + (hero_traits or ["curious"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="captain"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    establish_leisure(world, hero, activity)
    present_prize(world, parent, hero, prize)
    world.para()
    arrive(world, hero, parent)
    want_and_warn(world, hero, parent, activity, prize)
    feel_terrible(world, hero)
    brave_turn(world, hero, parent, activity)
    helper = share_and_fix(world, hero, parent, activity, prize)
    world.para()
    if helper:
        lesson_learned(world, hero, parent, activity, prize, helper)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, helper=helper, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short space-adventure story for a child about {hero.id} during leisure time, with sharing and bravery.',
        f"Tell a gentle story where {hero.id} wants to {act.verb}, but a {prize.label} might get ruined, so the crew finds a better plan.",
        f'Write a small story that includes the words "leisure", "terrible", and "lesson learned" in a space setting.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    helper = f.get("helper")
    qa = [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is about {hero.id}, a little brave child who is having leisure time on the station.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {activity.verb} and enjoy the game.",
        ),
        QAItem(
            question=f"Why did the captain worry?",
            answer=f"The captain worried because {prize.phrase} could get messy if {hero.id} kept going without a safer plan.",
        ),
    ]
    if helper:
        qa.append(QAItem(
            question=f"What helped the children keep playing safely?",
            answer=f"They shared {helper.label} and used it before playing, so the fun could continue without ruining {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that sharing and a brave choice can fix a terrible moment and make the game better.",
        ))
    return qa

WORLD_KNOWLEDGE = {
    "leisure": [
        QAItem(
            question="What does leisure time mean?",
            answer="Leisure time means free time when someone can rest, play, or enjoy a favorite activity.",
        )
    ],
    "sharing": [
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing is helpful because more than one person can use something, and it can make play kinder and fairer.",
        )
    ],
    "bravery": [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right or helpful thing even when it feels a little scary.",
        )
    ],
    "lesson": [
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something a person understands better after trying, making a mistake, or solving a problem.",
        )
    ],
    "space": [
        QAItem(
            question="What is a space station?",
            answer="A space station is a place built for people to live and work while floating above a planet.",
        )
    ],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ["leisure", "sharing", "bravery", "lesson", "space"] for item in WORLD_KNOWLEDGE[key]]

def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy
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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure leisure story world about sharing, bravery, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["captain"])
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

def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {prize.label} would not be at risk during {activity.gerund}.)"
    if select_helper(activity, prize) is None:
        return f"(No story: nothing in the helper set can safely fix {activity.gerund} for a {prize.label}.)"
    return "(No story: invalid combination.)"

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, prize) and select_helper(act, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, act_id, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=act_id,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=getattr(args, "parent", None) or "captain",
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, [params.trait, "stubborn"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)

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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="leisure_deck", activity="float_kite", prize="badge", name="Aleck", gender="boy", trait="brave"),
            StoryParams(place="leisure_deck", activity="starglow", prize="gloves", name="Mina", gender="girl", trait="curious"),
            StoryParams(place="observation_bay", activity="starglow", prize="cap", name="Aleck", gender="boy", trait="playful"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
