#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lisp_gremlin_close_flashback_tall_tale.py
===============================================================================================================

A tiny, self-contained story world in a tall-tale mode:
a child and a gremlin with a lisp, a close call, and a flashback
that explains why they trust each other so much.

The story is driven by a small simulated world model with physical meters
and emotional memes. The flashback is not decoration; it is the reason the
pair are already close when the main problem appears.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gremlin: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id
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
    indoor: bool = False
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
    weather: str
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
    location: str
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
class Gear:
    id: str
    label: str
    guards: set[str]
    protects: set[str]
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
        self.facts: dict = {}
        self.weather: str = ""

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.weather = self.weather
        c.facts = dict(self.facts)
        return c


def _mget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _memget(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _inc_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = _mget(ent, key) + amount


def _inc_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = _memget(ent, key) + amount


def _r_close_call(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    for token in ("climb", "reach", "peek"):
        if _mget(child, token) < THRESHOLD:
            continue
        sig = ("close_call", token)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _inc_meme(child, "alarm", 1)
        out.append("The way ahead looked mighty close to trouble.")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    gremlin = world.get("gremlin")
    if _memget(gremlin, "trust") < THRESHOLD or _memget(child, "alarm") < THRESHOLD:
        return out
    sig = ("comfort",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _inc_meme(child, "calm", 1)
    out.append("The gremlin kept close and helped steady the moment.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_close_call, _r_comfort):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback_line(hero: Entity, gremlin: Entity) -> str:
    return (
        f"Before that, there was a flashback as wide as a wagon wheel: "
        f"one stormy evening, {hero.id} had found {gremlin.name_word()} wedged inside a teacup, "
        f"and {hero.id} had lifted {gremlin.pronoun('object')} out with a spoon and a grin. "
        f"Since then, the two had stayed close as peas in a pod."
    )


def introduce(world: World, hero: Entity, gremlin: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big imagination, and {gremlin.name_word()} "
        f"was a gremlin who spoke with a lisp and a spark in {gremlin.pronoun('possessive')} eyes."
    )
    world.say(
        f"They were close friends, the sort who could finish each other’s stories before the next breath."
    )


def setup_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.carried_by = hero.id
    _inc_meme(hero, "fondness", 1)
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} close to {hero.pronoun('possessive')} chest, "
        f"because {prize.phrase} was the sort of prize that made a child stand a little taller."
    )


def main_premise(world: World, hero: Entity, gremlin: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"One day at {world.setting.place}, {hero.id} wanted to {activity.verb}, "
        f"and the whole sky seemed to tip its hat and watch."
    )
    world.say(
        f"{gremlin.name_word()} warned, “Be careful now. That path is as {activity.risk} as a spoon in a thunderstorm.”"
    )
    _inc_meter(hero, activity.id, 1)
    _inc_meme(gremlin, "worry", 1)
    propagate(world)


def flashback(world: World, hero: Entity, gremlin: Entity) -> None:
    world.para()
    world.say(flashback_line(hero, gremlin))


def turn_and_fix(world: World, hero: Entity, gremlin: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    world.para()
    _inc_meme(gremlin, "trust", 1)
    world.say(
        f"{gremlin.name_word()} lisped, “I can help keep the {prize.label} safe.” "
        f"Then {gremlin.id} fetched {gear.label} and said, “If we use this, you can still {activity.verb}.”"
    )
    world.say(
        f"{hero.id} nodded, and together they used {gear.prep}."
    )
    world.say(
        f"At last, {hero.id} went on to {activity.gerund}, while {prize.phrase} stayed safe and close."
    )
    world.say(
        f"And the whole business ended with a laugh so loud it nearly shook the leaves loose from the trees."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["small", "bold"],
    ))
    gremlin = world.add(Entity(
        id="gremlin",
        kind="character",
        type="gremlin",
        label="Moss",
        traits=["lisping", "mischievous", "kind"],
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=hero.id,
    ))

    introduce(world, hero, gremlin)
    flashback(world, hero, gremlin)
    world.para()
    setup_prize(world, hero, prize)
    main_premise(world, hero, gremlin, activity, prize)
    return world


SETTINGS = {
    "hayloft": Setting(place="the hayloft", indoor=True, affords={"climb", "peek"}),
    "orchard": Setting(place="the orchard", indoor=False, affords={"climb", "reach"}),
    "pond": Setting(place="the pond bank", indoor=False, affords={"peek", "reach"}),
}

ACTIVITIES = {
    "climb": Activity(
        id="climb",
        verb="climb the apple ladder",
        gerund="climbing the apple ladder",
        rush="scramble up the rungs",
        risk="high and shaky",
        weather="sunny",
        keyword="ladder",
        tags={"height"},
    ),
    "reach": Activity(
        id="reach",
        verb="reach for the sky-berries",
        gerund="reaching for sky-berries",
        rush="stretch for the highest branch",
        risk="long and wobbly",
        weather="sunny",
        keyword="berries",
        tags={"height"},
    ),
    "peek": Activity(
        id="peek",
        verb="peek into the moon puddle",
        gerund="peeking into the moon puddle",
        rush="lean close over the water",
        risk="slippery and splashy",
        weather="moonlit",
        keyword="puddle",
        tags={"water"},
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a little brass lantern with a bright glass belly",
        type="lantern",
        location="hand",
    ),
    "jamjar": Prize(
        label="jam jar",
        phrase="a jar of strawberry jam",
        type="jar",
        location="basket",
    ),
    "kite": Prize(
        label="kite",
        phrase="a striped kite with a tail like ribbon",
        type="kite",
        location="hand",
    ),
}

GEAR = [
    Gear(
        id="rope",
        label="a sturdy rope",
        guards={"high and shaky", "long and wobbly"},
        protects={"climb", "reach"},
        prep="tying the rope to the old beam",
        tail="tied the rope fast and used it like a promise",
    ),
    Gear(
        id="boots",
        label="rubber boots",
        guards={"slippery and splashy"},
        protects={"peek"},
        prep="pulling on rubber boots",
        tail="stepped careful and stayed dry",
    ),
]

GIRL_NAMES = ["Mabel", "Hattie", "Nell", "Ruby", "Ivy"]
BOY_NAMES = ["Otis", "Will", "Bram", "Jasper", "Eli"]
TRAITS = ["bold", "curious", "cheerful", "spry"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                act = _safe_lookup(ACTIVITIES, act_id)
                if act.id in {"climb", "reach"} and prize.location == "hand":
                    combos.append((place, act_id, prize_id))
                elif act.id == "peek" and prize.location in {"hand", "basket"}:
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} is not a good fit for {prize.phrase} in this small world. "
        f"Try a prize that makes sense to carry close during that action.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tall-tale story world about a lisping gremlin, a close friend, and a flashback."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        pr = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if (act.id, pr.location) not in {("climb", "hand"), ("reach", "hand"), ("peek", "hand"), ("peek", "basket")}:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall tale for a child about a lisping gremlin and a close friend in {f["place"]}.',
        f"Tell a flashback story where {f['hero']} and Moss once met in a teacup, and now they solve a close call together.",
        f'Write a gentle story that uses the words "lisp", "gremlin", and "close".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero_entity")
    gremlin: Entity = _safe_fact(world, f, "gremlin_entity")
    prize: Entity = _safe_fact(world, f, "prize_entity")
    act: Activity = _safe_fact(world, f, "activity_obj")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id} and Moss, a lisping gremlin who was already close friends with {hero.id}.",
        ),
        QAItem(
            question=f"What was the flashback about?",
            answer=(
                f"The flashback said {hero.id} once found Moss stuck in a teacup during a stormy night, "
                f"and that help made them close friends."
            ),
        ),
        QAItem(
            question=f"What did Moss help protect?",
            answer=f"Moss helped protect {hero.pronoun('possessive')} {prize.label} while {hero.id} {act.verb}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gremlin?",
            answer="A gremlin is a small make-believe creature, often described as mischievous or clever.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that looks back to something that happened earlier.",
        ),
        QAItem(
            question="What does lisp mean in speech?",
            answer="A lisp is a way of speaking where some sounds come out in a softer or different way.",
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place(hayloft). place(orchard). place(pond).
activity(climb). activity(reach). activity(peek).
prize(lantern). prize(jamjar). prize(kite).

affords(hayloft,climb). affords(hayloft,peek).
affords(orchard,climb). affords(orchard,reach).
affords(pond,peek). affords(pond,reach).

safe_combo(Place,Act,Prize) :- affords(Place,Act), compatible(Act,Prize).

compatible(climb,lantern).
compatible(climb,kite).
compatible(reach,lantern).
compatible(reach,kite).
compatible(peek,lantern).
compatible(peek,jamjar).

#show safe_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for pr in PRIZES:
        lines.append(asp.fact("prize", pr))
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            lines.append(asp.fact("affords", place, act))
    for act_id, pr in [("climb", "lantern"), ("climb", "kite"), ("reach", "lantern"), ("reach", "kite"), ("peek", "lantern"), ("peek", "jamjar")]:
        lines.append(asp.fact("compatible", act_id, pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_combo/3."))
    return sorted(set(asp.atoms(model, "safe_combo")))


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
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender)
    world.facts.update(
        hero=params.name,
        place=_safe_lookup(SETTINGS, params.place).place,
        hero_entity=world.get("child"),
        gremlin_entity=world.get("gremlin"),
        prize_entity=world.get("prize"),
        activity_obj=_safe_lookup(ACTIVITIES, params.activity),
    )
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
    StoryParams(place="orchard", activity="climb", prize="lantern", name="Mabel", gender="girl"),
    StoryParams(place="hayloft", activity="peek", prize="jamjar", name="Otis", gender="boy"),
    StoryParams(place="pond", activity="reach", prize="kite", name="Ivy", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show safe_combo/3."))
        combos = sorted(set(asp.atoms(model, "safe_combo")))
        for c in combos:
            print(c)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
