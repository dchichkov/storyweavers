#!/usr/bin/env python3
"""
storyworlds/worlds/sociopath_bamboo_liquid_curiosity_cautionary_tall_tale.py
=============================================================================

A standalone tall-tale story world about curiosity, caution, bamboo, and liquid.

Seed tale used to build the model:
---
In a wide river valley, a curious child kept poking at the tall bamboo that
grew along the bank. An old cautionary aunt warned that the bamboo was hollow
and that the sparkling liquid inside a cracked gourd should not be spilled near
the lanterns. Then a sly sociopath from the road tried to stir trouble by
shaking the bamboo and knocking the gourd loose. The child listened, the aunt
spoke plainly, and by choosing a safer trick with a reed cup and a bucket,
everyone kept the camp bright and dry.

The world model tracks:
- physical meters: wetness, spill, damage, distance, pressure
- emotional memes: curiosity, caution, fear, relief, pride, mischief
- a tall-tale risk: curiosity can tip into trouble when liquid meets bamboo
- a cautionary turn: warnings, a near-miss, and a safer method that avoids harm
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: str = ""
    aunt: object | None = None
    bamboo: object | None = None
    child: object | None = None
    jar: object | None = None
    sociopath: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Place:
    id: str
    label: str
    indoors: bool = False
    traits: set[str] = field(default_factory=set)
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


@dataclass
class Liquid:
    id: str
    label: str
    phrase: str
    mess: str
    soak: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
class BambooThing:
    id: str
    label: str
    phrase: str
    region: str
    hollow: bool = True
    keyword: str = "bamboo"
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def _addm(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _addq(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _r_spill(world: World) -> list[str]:
    out = []
    child = world.get("child")
    liquid = world.get("liquid")
    if child.meters.get("curious_pull", 0.0) < THRESHOLD:
        return out
    if liquid.meters.get("loose", 0.0) < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _addm(liquid, "spill", 1.0)
    _addm(child, "wet", 1.0)
    out.append("The liquid sloshed and splashed at the child's boots.")
    return out


def _r_damage_bamboo(world: World) -> list[str]:
    out = []
    liquid = world.get("liquid")
    bamboo = world.get("bamboo")
    if liquid.meters.get("spill", 0.0) < THRESHOLD:
        return out
    sig = ("damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _addm(bamboo, "stained", 1.0)
    out.append("The bamboo wore a shiny stain where the liquid kissed it.")
    return out


def _r_caution(world: World) -> list[str]:
    child = world.get("child")
    aunt = world.get("aunt")
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return []
    if aunt.memes.get("warning", 0.0) < THRESHOLD:
        return []
    sig = ("caution",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _addq(child, "care", 1.0)
    _addq(aunt, "pride", 1.0)
    return ["__caution__"]


CAUSAL_RULES = [_r_spill, _r_damage_bamboo, _r_caution]


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
            if s != "__caution__":
                world.say(s)
    return produced


def predict_near_miss(world: World) -> bool:
    sim = world.copy()
    child = sim.get("child")
    _addm(child, "curious_pull", 1.0)
    _addm(sim.get("liquid"), "loose", 1.0)
    propagate(sim, narrate=False)
    return sim.get("liquid").meters.get("spill", 0.0) >= THRESHOLD


def bamboo_risk(liquid: Liquid, bamboo: BambooThing) -> bool:
    return liquid.keyword in {"water", "tea", "syrup", "ink", "river"} and bamboo.hollow


def select_fix(liquid: Liquid, bamboo: BambooThing) -> Optional[Gear]:
    for gear in GEAR:
        if liquid.mess in gear.guards and bamboo.region in gear.covers:
            return gear
    return None


def invent_tall_tale_image(place: Place, liquid: Liquid, bamboo: BambooThing) -> str:
    return {
        "riverbank": "the bamboo stood straight as a parade flag and the water flashed like silver coins",
        "grove": "the bamboo rose higher than a barn roof and the liquid glittered like moonshine in a jar",
        "camp": "the bamboo clicked in the breeze like a fence full of fiddles",
    }.get(place.id, "the bamboo swayed like a story that could not wait to be told")


def tell(world: World, child_name: str, child_type: str, aunt_type: str, liquid: Liquid) -> World:
    child = world.add(Entity(
        id="child", kind="character", type=child_type, label=child_name,
        traits=["curious", "small", "bright"],
        meters={"curious_pull": 0.0, "wet": 0.0},
        memes={"curiosity": 1.0, "caution": 0.0, "fear": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    aunt = world.add(Entity(
        id="aunt", kind="character", type=aunt_type, label="Aunt Cora",
        traits=["cautionary", "steady"],
        memes={"warning": 0.0, "caution": 1.0, "relief": 0.0, "pride": 0.0},
    ))
    sociopath = world.add(Entity(
        id="sociopath", kind="character", type="man", label="Red Harker",
        traits=["sly", "troublemaking"],
        memes={"mischief": 1.0, "danger": 1.0},
    ))
    bamboo = world.add(Entity(
        id="bamboo", type="bamboo", label="the bamboo",
        phrase="a tall stand of bamboo", owner=None, region="hand", protective=False,
        meters={"stain": 0.0},
    ))
    jar = world.add(Entity(
        id="liquid", type="liquid", label=liquid.label, phrase=liquid.phrase,
        caretaker="aunt", meters={"loose": 0.0}, memes={"value": 1.0},
    ))

    world.say(
        f"Up in {world.place.label}, {child.label} was the sort of child whose curiosity "
        f"could smell a mystery before breakfast."
    )
    world.say(
        f"{child.label.capitalize()} loved the {bamboo.label} and the {liquid.phrase}; "
        f"{invent_tall_tale_image(world.place, liquid, bamboo)}."
    )
    world.say(
        f"But Aunt Cora was a cautionary soul. She said the {bamboo.label} was hollow, "
        f"and that the {liquid.label} should stay snug where it was."
    )

    world.para()
    world.say(
        f"One bright day, {child.label} and Aunt Cora were beside the river in {world.place.label}, "
        f"when Red Harker swaggered in with a grin as wide as a barn door."
    )
    world.say(
        f"He called himself a sociopath, though the camp children called him plain trouble."
    )
    world.say(
        f"He reached for the {bamboo.label}, as if a little shaking could turn an ordinary morning into a tumble."
    )

    world.facts.update(child=child, aunt=aunt, sociopath=sociopath, bamboo=bamboo, liquid=jar)
    _addq(child, "curiosity", 0.0)
    _addq(aunt, "caution", 0.0)

    world.para()
    child.meters["curious_pull"] += 1.0
    jar.meters["loose"] += 1.0
    if predict_near_miss(world):
        _addq(aunt, "warning", 1.0)
        world.say(
            f"Aunt Cora lifted a finger and warned, \"That liquid will run faster than a fox in a thunderstorm if you jostle it!\""
        )
    world.say(
        f"{child.label} listened. Even so, the curious child leaned close, then chose to use eyes instead of hands."
    )
    propagate(world)

    world.para()
    gear = select_fix(liquid, bamboo)
    if gear is None:
        pass
    world.add(Entity(
        id=gear.id, type="gear", label=gear.label, owner="child", protective=True,
        plural=gear.plural,
    )).worn_by = "child"
    world.say(
        f"Then Aunt Cora fetched {gear.label} and showed how to guide the {liquid.label} with a safer trick."
    )
    world.say(
        f"They used {gear.prep}, so the {liquid.label} stayed put and the {bamboo.label} stayed bright."
    )
    _addq(child, "relief", 1.0)
    _addq(child, "pride", 1.0)
    _addq(aunt, "relief", 1.0)
    world.say(
        f"{child.label.capitalize()} stood tall beside Aunt Cora, proud to have learned that curiosity is fine when caution holds the lantern."
    )
    return world


SETTINGS = {
    "riverbank": Place(id="riverbank", label="the riverbank", traits={"outdoors", "water", "bamboo"}),
    "grove": Place(id="grove", label="the bamboo grove", traits={"outdoors", "bamboo"}),
    "camp": Place(id="camp", label="the river camp", traits={"outdoors", "campfire"}),
}

LIQUIDS = {
    "water": Liquid(id="water", label="river water", phrase="a jar of clear river water", mess="wet", soak="soak", keyword="liquid", tags={"water", "wet"}),
    "tea": Liquid(id="tea", label="sweet tea", phrase="a tin cup of sweet tea", mess="sticky", soak="smear", keyword="liquid", tags={"tea", "sticky"}),
    "ink": Liquid(id="ink", label="blue ink", phrase="a little bottle of blue ink", mess="inky", soak="stain", keyword="liquid", tags={"ink", "messy"}),
}

BAMBOOS = {
    "tube": BambooThing(id="tube", label="bamboo tube", phrase="a hollow bamboo tube", region="hand"),
    "stalks": BambooThing(id="stalks", label="bamboo stalks", phrase="a bundle of bamboo stalks", region="hand"),
}

GEAR = [
    Gear(id="reedcup", label="a reed cup", covers={"hand"}, guards={"wet", "sticky", "inky"}, prep="pour the liquid into a reed cup", tail="kept the liquid from splashing", plural=False),
    Gear(id="bucket", label="a small bucket", covers={"hand"}, guards={"wet", "sticky", "inky"}, prep="set a small bucket under the tube", tail="caught every drop", plural=False),
]


@dataclass
class StoryParams:
    place: str
    liquid: str
    bamboo: str
    child_name: str
    child_type: str
    aunt_type: str
    seed: Optional[int] = None
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for children about curiosity, caution, bamboo, and a {f["liquid"].label}.',
        f"Tell a cautionary, funny story where {f['child'].label} wants to touch the {f['bamboo'].label} but Aunt Cora offers a safer way.",
        f'Write a short tall tale that includes the word "sociopath" as a troublemaking road character, but ends with a wise, safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    aunt = _safe_fact(world, f, "aunt")
    liquid = _safe_fact(world, f, "liquid")
    bamboo = _safe_fact(world, f, "bamboo")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who was the story about in {world.place.label}?",
            answer=f"It was about {child.label}, a curious child, and Aunt Cora, who was the cautionary grown-up keeping watch.",
        ),
        QAItem(
            question=f"Why did Aunt Cora worry about the {liquid.label} near the {bamboo.label}?",
            answer=f"She worried because the {bamboo.label} was hollow and the {liquid.label} could spill and make a mess if it was shaken.",
        ),
        QAItem(
            question=f"What did Red Harker do when he came to the river camp?",
            answer="He swaggered in, tried to stir trouble, and reached for the bamboo as if he could turn a calm morning upside down.",
        ),
        QAItem(
            question=f"How did {child.label} and Aunt Cora keep the {liquid.label} safe?",
            answer=f"They used {gear.label} and a safer trick, so the {liquid.label} stayed put instead of splashing everywhere.",
        ),
        QAItem(
            question=f"How did {child.label} feel at the end?",
            answer=f"{child.label} felt relieved and proud, because curiosity had listened to caution and the camp stayed bright and dry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bamboo?",
            answer="Bamboo is a tall, fast-growing plant with long green stalks. People can use it for poles, tubes, and all sorts of sturdy things.",
        ),
        QAItem(
            question="What is liquid?",
            answer="A liquid is something that can pour and flow, like water, tea, or juice.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking ahead so you can avoid trouble.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more and wanting to look, ask, or explore.",
        ),
    ]


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
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(E) :- meme(E, curiosity), meme(E, V), V >= 1.
warning(E) :- meme(E, caution), meme(E, V), V >= 1.
at_risk(L, B) :- liquid(L), bamboo(B), hollow(B), liquid_kind(L, wetlike).
can_fix(L, B) :- at_risk(L, B), gear(G), guards(G, wetlike), covers(G, hand).
valid_story(Place, L, B) :- place(Place), at_risk(L, B), can_fix(L, B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
    for lid, l in LIQUIDS.items():
        lines.append(asp.fact("liquid", lid))
        lines.append(asp.fact("liquid_kind", lid, "wetlike" if l.mess == "wet" else l.mess))
    for bid, b in BAMBOOS.items():
        lines.append(asp.fact("bamboo", bid))
        if b.hollow:
            lines.append(asp.fact("hollow", bid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, "wetlike" if m == "wet" else m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for place in SETTINGS:
        for lid, liquid in LIQUIDS.items():
            for bid, bamboo in BAMBOOS.items():
                if bamboo_risk(liquid, bamboo) and select_fix(liquid, bamboo):
                    py_set.add((place, lid, bid))
    if asp_set == py_set:
        print(f"OK: ASP matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: curiosity, caution, bamboo, and liquid.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--liquid", choices=LIQUIDS)
    ap.add_argument("--bamboo", choices=BAMBOOS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    liquid = getattr(args, "liquid", None) or rng.choice(list(LIQUIDS))
    bamboo = getattr(args, "bamboo", None) or rng.choice(list(BAMBOOS))
    child_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(["Mina", "Jo", "Toby", "Lena", "Sage", "Pip"])
    aunt_type = getattr(args, "parent", None) or "aunt"
    if not bamboo_risk(_safe_lookup(LIQUIDS, liquid), _safe_lookup(BAMBOOS, bamboo)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not select_fix(_safe_lookup(LIQUIDS, liquid), _safe_lookup(BAMBOOS, bamboo)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, liquid=liquid, bamboo=bamboo, child_name=child_name, child_type=child_type, aunt_type=aunt_type)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    world = tell(world, params.child_name, params.child_type, params.aunt_type, _safe_lookup(LIQUIDS, params.liquid))
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
    StoryParams(place="riverbank", liquid="water", bamboo="tube", child_name="Mina", child_type="girl", aunt_type="aunt"),
    StoryParams(place="grove", liquid="tea", bamboo="stalks", child_name="Toby", child_type="boy", aunt_type="aunt"),
    StoryParams(place="camp", liquid="ink", bamboo="tube", child_name="Lena", child_type="girl", aunt_type="aunt"),
]


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
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
