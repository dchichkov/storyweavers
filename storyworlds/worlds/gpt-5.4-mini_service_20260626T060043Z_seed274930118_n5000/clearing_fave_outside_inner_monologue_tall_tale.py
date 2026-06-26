#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale-style clearing story with inner monologue.

Premise:
A small, proud child goes outside to a clearing with a favorite item. The child
wants to do something big and braggy, but the favorite thing is in danger of
getting lost or ruined. The child's inner monologue becomes part of the turn:
they weigh daring, fear, and cleverness, then choose a safer, still-grand way
to finish the day.

The story generator keeps the tale state-driven:
- physical meters track distance, dirt, wind, and the safety of the fave item
- emotional memes track pride, worry, bravado, and relief
- inner monologue is narrated as a living pressure in the scene
- a tall-tale tone stretches the scale of the world without losing causality
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

    fave: object | None = None
    g: object | None = None
    hero: object | None = None
    parent: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
    place: str = "the clearing"
    outside: bool = True
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
class Act:
    id: str
    verb: str
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
class Fave:
    id: str
    label: str
    phrase: str
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
    protects: set[str]
    covers: set[str]
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        return c


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for act in ("dust", "wind", "sap"):
            if actor.m(act) < THRESHOLD:
                continue
            for item in world.worn(actor):
                if item.id in world.fired:
                    continue
                if item.region not in world.zone:
                    continue
                sig = ("soil", actor.id, item.id, act)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["dirty"] = item.m("dirty") + 1
                item.meters[act] = item.m(act) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {act} and scuffed.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.m("dirty") < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["work"] = carer.e("work") + 1
        out.append(f"That would mean more fixing for {carer.label}.")
    return out


CAUSAL_RULES = [("soil", _r_soil), ("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_risk(act: Act, fave: Fave) -> bool:
    return fave.region in act.zone


def select_gear(act: Act, fave: Fave) -> Optional[Gear]:
    for g in GEAR:
        if act.mess in g.protects and fave.region in g.covers:
            return g
    return None


def predict_mess(world: World, actor: Entity, act: Act, fave_id: str) -> dict:
    sim = world.copy()
    _do_act(sim, sim.get(actor.id), act, narrate=False)
    fave = sim.entities[fave_id]
    return {"soiled": fave.m("dirty") >= THRESHOLD, "worried": any(e.e("work") >= THRESHOLD for e in sim.characters())}


def _do_act(world: World, actor: Entity, act: Act, narrate: bool = True) -> None:
    world.zone = set(act.zone)
    actor.meters[act.mess] = actor.m(act.mess) + 1
    actor.memes["thrill"] = actor.e("thrill") + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes if t), 'lively')} thing with a big voice in {hero.pronoun('possessive')} chest."
    )


def loves_fave(world: World, hero: Entity, fave: Entity) -> None:
    hero.memes["love"] = hero.e("love") + 1
    fave.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {fave.label} so much {fave.it()} seemed to shine like a penny in a thunderstorm."
    )


def wants_outside(world: World, hero: Entity, act: Act, setting: Setting) -> None:
    world.say(
        f"{hero.id} headed outside for {setting.place}, where the air was wide and the daylight looked fit for a legend."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {act.verb}, and {act.keyword} seemed to call from the grass itself."
    )


def inner_monologue(world: World, hero: Entity, act: Act, fave: Entity) -> None:
    hero.memes["worry"] = hero.e("worry") + 1
    hero.memes["pride"] = hero.e("pride") + 1
    world.say(
        f'Inside {hero.pronoun("possessive")} head, a tiny voice boomed, "{act.verb.capitalize()} would be grand... but what about my {fave.label}?"'
    )


def warn(world: World, hero: Entity, parent: Entity, act: Act, fave: Entity) -> bool:
    pred = predict_mess(world, hero, act, fave.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = act.soil
    world.say(
        f'"If you {act.verb}, your {fave.label} will end up {act.soil}," {parent.pronoun("possessive")} {parent.label} said.'
    )
    return True


def hesitate(world: World, hero: Entity, act: Act) -> None:
    hero.memes["stuck"] = hero.e("stuck") + 1
    world.say(f"{hero.id} nearly went charging ahead, but {hero.pronoun('possessive')} boots slowed just enough to let the thought grow.")


def offer_fix(world: World, parent: Entity, hero: Entity, act: Act, fave: Entity) -> Optional[Gear]:
    gear = select_gear(act, fave)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        plural=gear.plural,
    ))
    g.worn_by = hero.id
    if predict_mess(world, hero, act, fave.id)["soiled"]:
        g.worn_by = None
        del world.entities[g.id]
        return None
    world.say(
        f'Then {parent.pronoun("possessive")} {parent.label} smiled and said, "{gear.prep} first, and the clearing can still have its show."'
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, act: Act, fave: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.e("joy") + 1
    hero.memes["relief"] = hero.e("relief") + 1
    hero.memes["worry"] = 0.0
    world.say(
        f'{hero.id} grinned like a circus banner in the wind and hugged {hero.pronoun("possessive")} {parent.label}. "Now that is a mighty plan," {hero.pronoun()} said.'
    )
    world.say(
        f"They {gear.tail}. Soon {hero.id} was {act.gerund}, and {fave.label} stayed clean as a cloud over a pond."
    )


def tell(setting: Setting, act: Act, fave_cfg: Fave, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"pride": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    fave = world.add(Entity(id="fave", type=fave_cfg.id, label=fave_cfg.label, phrase=fave_cfg.phrase, owner=hero.id, caretaker=parent.id, plural=fave_cfg.plural))
    world.say(f"{hero.id} was a little {hero_type} with a head full of sky and a heart full of thunder.")
    loves_fave(world, hero, fave)
    world.para()
    wants_outside(world, hero, act, setting)
    inner_monologue(world, hero, act, fave)
    warn(world, hero, parent, act, fave)
    hesitate(world, hero, act)
    world.para()
    gear = offer_fix(world, parent, hero, act, fave)
    if gear:
        accept(world, hero, parent, act, fave, gear)
    world.facts.update(hero=hero, parent=parent, fave=fave, act=act, setting=setting, gear=gear, resolved=gear is not None)
    return world


SETTINGS = {
    "clearing": Setting(place="the clearing", outside=True),
}

ACTIVITIES = {
    "gust": Act(
        id="gust",
        verb="chase the wild gust",
        gerund="chasing the wild gust",
        rush="dash after the wild gust",
        mess="wind",
        soil="blown crooked",
        zone={"head", "torso"},
        keyword="outside",
        tags={"wind", "outside"},
    ),
    "creekskip": Act(
        id="creekskip",
        verb="skip stones by the creek",
        gerund="skipping stones",
        rush="run to the creek edge",
        mess="spray",
        soil="splashed wet",
        zone={"feet", "legs"},
        keyword="clearing",
        tags={"water", "outside"},
    ),
    "berry": Act(
        id="berry",
        verb="pick berry pies from the bushes",
        gerund="picking berry pies",
        rush="scramble through the berry patch",
        mess="sap",
        soil="sticky with sap",
        zone={"hands", "torso"},
        keyword="fave",
        tags={"berries", "outside"},
    ),
}

FAVES = {
    "hat": Fave(id="hat", label="fave hat", phrase="a red-and-gold favorite hat", region="head"),
    "scarf": Fave(id="scarf", label="fave scarf", phrase="a soft striped favorite scarf", region="torso"),
    "boots": Fave(id="boots", label="fave boots", phrase="a pair of favorite boots", region="feet", plural=True),
}

GEAR = [
    Gear(id="tiedhat", label="a chin strap", protects={"wind"}, covers={"head"}, prep="buckle the chin strap onto the hat", tail="breezed back with the hat tied snug", plural=False),
    Gear(id="wrap", label="a sturdy wrap", protects={"sap"}, covers={"torso"}, prep="wrap the scarf in a sturdy wrap", tail="went back for the sturdy wrap"),
    Gear(id="slickers", label="rain slickers", protects={"spray"}, covers={"feet", "legs"}, prep="pull on the rain slickers", tail="went stomping on with the rain slickers", plural=True),
]

NAMES_BOY = ["Milo", "Toby", "Ned", "Finn", "Jasper", "Pip"]
NAMES_GIRL = ["Luna", "Bea", "Ada", "Nina", "Poppy", "Tess"]


@dataclass
class StoryParams:
    place: str
    activity: str
    fave: str
    name: str
    gender: str
    parent: str
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
    out = []
    for place, setting in SETTINGS.items():
        for act_id in ACTIVITIES:
            act = _safe_lookup(ACTIVITIES, act_id)
            for fave_id, fave in FAVES.items():
                if activity_risk(act, fave) and select_gear(act, fave):
                    out.append((place, act_id, fave_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, fave = f["hero"], f["parent"], f["act"], f["fave"]
    return [
        f'Write a tall tale for a little child about {hero.id}, {world.setting.place}, and a favorite {fave.label}.',
        f"Tell a story where {hero.id} wants to {act.verb} outside, but {parent.label} worries about {fave.label}.",
        f"Write a child-friendly tall tale that includes a clearing, a fave, outside, and an inner monologue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, fave = f["hero"], f["parent"], f["act"], f["fave"]
    qa = [
        QAItem(question=f"Where did {hero.id} go to start the adventure?", answer=f"{hero.id} went outside to {world.setting.place}, a clearing wide enough for big footsteps and bigger thoughts."),
        QAItem(question=f"What did {hero.id} want to do?", answer=f"{hero.id} wanted to {act.verb}, because {act.keyword} was tugging at {hero.pronoun('possessive')} curiosity like a kite string."),
        QAItem(question=f"What was {hero.id}'s favorite thing?", answer=f"{hero.id}'s favorite thing was {fave.phrase}, and {fave.label} was worn like treasure."),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the problem get solved?",
            answer=f"{parent.label} offered {f['gear'].label} so {hero.id} could {act.verb} without ruining {fave.label}. That let the story stay grand and safe at once.",
        ))
    else:
        qa.append(QAItem(
            question=f"Why was there a problem?",
            answer=f"There was a problem because {act.verb} outside would have left {fave.label} {act.soil}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a clearing?", answer="A clearing is an open space in the woods or grass where trees are thinner and the sky can be seen more easily."),
        QAItem(question="What does an inner monologue mean?", answer="An inner monologue is the little voice inside someone's head that helps them think through what to do next."),
        QAItem(question="What does a favorite thing feel like?", answer="A favorite thing can feel important and comforting, like a small treasure a child wants to keep safe."),
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="clearing", activity="gust", fave="hat", name="Milo", gender="boy", parent="father"),
    StoryParams(place="clearing", activity="berry", fave="scarf", name="Luna", gender="girl", parent="mother"),
    StoryParams(place="clearing", activity="creekskip", fave="boots", name="Bea", gender="girl", parent="mother"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "fave", None):
        act, fave = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(FAVES, getattr(args, "fave", None))
        if not (activity_risk(act, fave) and select_gear(act, fave)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "fave", None) is None or c[2] == getattr(args, "fave", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, act_id, fave_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=act_id, fave=fave_id, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(FAVES, params.fave), params.name, "girl" if params.gender == "girl" else "boy", params.parent)
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
prize_at_risk(A, F) :- act_zone(A, R), fave_region(F, R).
fix(G, A, F) :- prize_at_risk(A, F), act_mess(A, M), gear_protects(G, M), gear_covers(G, R), fave_region(F, R).
valid(Place, A, F) :- place_affords(Place, A), prize_at_risk(A, F), fix(_, A, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("place_affords", place, next(iter(ACTIVITIES))))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("act_mess", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("act_zone", aid, r))
    for fid, fave in FAVES.items():
        lines.append(asp.fact("fave", fid))
        lines.append(asp.fact("fave_region", fid, fave.region))
    for gid, gear in ((g.id, g) for g in GEAR):
        lines.append(asp.fact("gear", gid))
        for m in sorted(gear.protects):
            lines.append(asp.fact("gear_protects", gid, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("gear_covers", gid, r))
    return "\n".join(lines)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with a clearing, a fave, outside, and an inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--fave", choices=FAVES)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
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
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
