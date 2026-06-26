#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/encore_valuable_fourth_curiosity_heartwarming.py
====================================================================================================

A small heartwarming story world about Curiosity, a valuable keepsake, a fourth
practice, and an encore that only happens when the people in the room feel safe
and ready to cheer.

Seed tale used as the premise:
---
Curiosity was a little performer who loved trying again. One evening, Curiosity
wanted to play a song for the neighbors. Curiosity also wore a valuable little
locket from a beloved family member, and the grown-up worried it might slip off
during the show.

After a few tries, Curiosity got better and better. On the fourth practice, the
song finally felt right. The grown-up suggested a soft ribbon pouch for the
locket so Curiosity could keep it close without losing it. Curiosity smiled,
played the song, and the neighbors clapped so loudly that they asked for an
encore.

The world model tracks both physical meters and emotional memes:
- the locket can be safe, worn, tucked away, or missing
- practice increases skill and confidence
- applause can invite an encore
- reassurance lowers worry and lets the performance shine
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
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    grownup: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "skill": 0.0,
                "applause": 0.0,
                "safe": 0.0,
                "lost": 0.0,
            }
        if not self.memes:
            self.memes = {
                "curiosity": 0.0,
                "worry": 0.0,
                "joy": 0.0,
                "pride": 0.0,
                "hope": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
    affordances: set[str] = field(default_factory=set)
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
    practice: str
    applause_line: str
    chance: str
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
    risk: str
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
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
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
        self.facts: dict = {}

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_practice(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Curiosity")
    act = _safe_fact(world, world.facts, "activity")
    if hero.meters["skill"] < 4:
        sig = ("practice", hero.meters["skill"])
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["skill"] += 1
            hero.memes["hope"] += 0.5
            out.append(f"Curiosity practiced {act.gerund} once more.")
    return out


def _r_applause(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Curiosity")
    if hero.meters["skill"] >= 4 and hero.meters["applause"] < 1:
        sig = ("applause",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["applause"] = 1
            hero.memes["joy"] += 1
            out.append("The room was ready to clap.")
    return out


CAUSAL_RULES = [_r_practice, _r_applause]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, hero: Entity, prize: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] += 1
    if prize.worn_by == hero.id and not prize.protective:
        return True
    return False


def valid_combo(activity: Activity, prize: Prize) -> bool:
    return prize.risk in activity.tags


SETTINGS = {
    "little_hall": Setting(place="the little hall", affordances={"song", "dance"}),
    "porch": Setting(place="the porch", affordances={"song"}),
    "school_stage": Setting(place="the school stage", affordances={"song", "dance"}),
}

ACTIVITIES = {
    "song": Activity(
        id="song",
        verb="sing a song",
        gerund="singing softly",
        practice="practice the chorus",
        applause_line="the song filled the room with a warm, bright feeling",
        chance="encore",
        keyword="encore",
        tags={"sound", "movement"},
    ),
    "dance": Activity(
        id="dance",
        verb="dance a little dance",
        gerund="dancing in a small circle",
        practice="practice the steps",
        applause_line="the little steps made everyone smile",
        chance="encore",
        keyword="fourth",
        tags={"movement"},
    ),
}

PRIZES = {
    "locket": Prize(
        label="locket",
        phrase="a valuable silver locket",
        type="locket",
        risk="movement",
    ),
    "ribbon": Prize(
        label="ribbon",
        phrase="a valuable blue ribbon",
        type="ribbon",
        risk="sound",
    ),
}

GEAR = [
    Gear(
        id="pouch",
        label="a soft ribbon pouch",
        prep="tuck the locket into a soft ribbon pouch",
        tail="held the pouch close while Curiosity performed",
        guards={"movement"},
    ),
    Gear(
        id="clip",
        label="a tiny clip",
        prep="clip the ribbon to a safe pin",
        tail="let the ribbon stay neat while Curiosity sang",
        guards={"sound"},
    ),
]

CURIOUS_NAMES = ["Curiosity"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str = "Curiosity"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming story world about practice, worry, and an encore.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affordances:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if valid_combo(act, prize):
                    combos.append((place, act_id, prize_id))
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or "Curiosity"
    return StoryParams(place=place, activity=activity, prize=prize, name=name)


def _gear_for(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if prize.risk in g.guards and valid_combo(activity, prize):
            return g
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="child", label=name))
    grownup = world.add(Entity(id="Mara", kind="character", type="aunt", label="Aunt Mara"))
    prize = world.add(Entity(
        id="keepsake",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=grownup.id,
    ))
    hero.memes["curiosity"] += 1

    world.say(f"{hero.id} was a little performer with a big, curious heart.")
    world.say(f"{hero.id} loved trying again, because each new try felt valuable in a different way.")
    world.say(f"One evening at {setting.place}, {hero.id} wanted to {activity.verb} for the neighbors.")
    world.say(f"{hero.id} also wore {prize.phrase}, which made {grownup.label} a little worried.")

    world.para()
    world.say(f"The grown-up explained that the {prize.label} should stay safe if the room got lively.")
    hero.memes["worry"] += 1
    world.say(f"{hero.id} nodded and decided to practice first.")

    while hero.meters["skill"] < 4:
        propagate(world, narrate=True)
    world.para()
    world.say(f"On the fourth try, {hero.id} finally {activity.practice} without stumbling.")
    world.say(activity.applause_line + ".")

    gear = _gear_for(activity, prize_cfg)
    if gear is not None:
        world.say(f'{grownup.label} smiled and said, "{gear.prep}, and then you can keep going."')
        prize.protective = True
        prize.worn_by = hero.id
        world.say(f"{hero.id} listened, and {gear.tail}.")
    else:
        prize.worn_by = hero.id

    world.para()
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.id} bowed with a shy grin.")
    world.say(f"The neighbors clapped so warmly that someone called, \"Encore!\"")
    world.say(f"{hero.id} laughed, did one more {activity.verb}, and the room felt cozy and bright.")

    world.facts.update(hero=hero, grownup=grownup, prize=prize, activity=activity, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about {f['hero'].id}, who keeps trying until the fourth practice and hears an encore.",
        f"Tell a gentle story where a valuable keepsake is kept safe while {f['hero'].id} performs at {world.setting.place}.",
        f"Write a child-friendly story using the words Curiosity, valuable, fourth, and encore.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    grownup = _safe_fact(world, f, "grownup")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little performer with a curious heart.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb} for the neighbors.",
        ),
        QAItem(
            question=f"Why was {grownup.label} worried about the {prize.label}?",
            answer=f"{grownup.label} was worried because the {prize.label} was valuable and should stay safe while the room got lively.",
        ),
        QAItem(
            question=f"What happened on the fourth try?",
            answer=f"On the fourth try, {hero.id} got the {activity.gerund} just right.",
        ),
        QAItem(
            question=f"What did the neighbors ask for at the end?",
            answer="They asked for an encore because they wanted to hear one more happy turn of the song.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does encore mean?",
            answer="An encore is one more performance that people ask for because they enjoyed the first one so much.",
        ),
        QAItem(
            question="What does it mean if something is valuable?",
            answer="If something is valuable, it is important, special, or worth a lot to the people who care about it.",
        ),
        QAItem(
            question="What does fourth mean?",
            answer="Fourth means the number after third and before fifth.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- setting(P).
valid_story(P,A,R) :- valid_place(P), activity(A), prize(R), afford(P,A), compatible(A,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("afford", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid, prize in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("risk", rid, prize.risk))
    for aid, act in ACTIVITIES.items():
        for rid, prize in PRIZES.items():
            if valid_combo(act, prize):
                lines.append(asp.fact("compatible", aid, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = {
        (p, a, r)
        for p, setting in SETTINGS.items()
        for a in setting.affordances
        for r, prize in PRIZES.items()
        if valid_combo(_safe_lookup(ACTIVITIES, a), prize)
    }
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid stories ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(python_set - clingo_set))
    print("clingo only:", sorted(clingo_set - python_set))
    return 1


CURATED = [
    StoryParams(place="little_hall", activity="song", prize="locket", name="Curiosity"),
    StoryParams(place="school_stage", activity="song", prize="ribbon", name="Curiosity"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
