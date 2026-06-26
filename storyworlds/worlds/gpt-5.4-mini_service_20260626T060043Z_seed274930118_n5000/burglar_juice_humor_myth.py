#!/usr/bin/env python3
"""
storyworlds/worlds/burglar_juice_humor_myth.py
==============================================

A small myth-flavored comedy world about a burglar, a jug of juice, and the
trouble that happens when a clever plan goes wrong.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    contains: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    burglar: object | None = None
    prize: object | None = None
    rep: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"woman", "girl", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"man", "boy", "king", "priest"}:
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
    name: str = "the old orchard"
    place_kind: str = "orchard"
    affords: set[str] = field(default_factory=set)
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
class Risk:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    target: str
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
    holder: str
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
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return w


def _narrate_join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _spill(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character" or e.meters.get("stealth", 0) < THRESHOLD:
            continue
        for obj in list(world.entities.values()):
            if obj.kind != "thing" or obj.held_by != e.id:
                continue
            if obj.label != "juice":
                continue
            sig = ("spill", e.id, obj.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            obj.meters["spilled"] = obj.meters.get("spilled", 0) + 1
            obj.meters["sticky"] = obj.meters.get("sticky", 0) + 1
            out.append("The juice leaped from the cup like a bright trickster.")
    return out


def _alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character" or e.meters.get("spilled", 0) < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["trouble"] = e.memes.get("trouble", 0) + 1
        out.append("The house-holders frowned, for the sweet stain was a loud witness.")
    return out


def _laugh(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character" or e.memes.get("trouble", 0) < THRESHOLD:
            continue
        sig = ("laugh", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["humor"] = e.memes.get("humor", 0) + 1
        out.append("Even so, the joke of the sticky footprints could not be hidden.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_spill, _alarm, _laugh):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def choose_remedy(risk: Risk, prize: Prize) -> Optional[Remedy]:
    for r in REMEDIES:
        if risk.mess in r.guards and prize.holder in r.helps:
            return r
    return None


def foretell(world: World, burglar: Entity, risk: Risk, prize: Entity) -> dict:
    sim = world.copy()
    sim.get(burglar.id).meters["stealth"] = 1
    sim.get(prize.id).held_by = burglar.id
    propagate(sim, narrate=False)
    return {
        "spilled": sim.get(prize.id).meters.get("spilled", 0) >= THRESHOLD,
        "trouble": sum(e.memes.get("trouble", 0) for e in sim.entities.values()),
    }


def opening(world: World, burglar: Entity, setting: Setting, risk: Risk) -> None:
    world.say(
        f"In {setting.name}, there lived a clever burglar named {burglar.id}, "
        f"who could creep as softly as a shadow at dusk."
    )
    world.say(
        f"{burglar.pronoun().capitalize()} loved to {risk.gerund}; "
        f"the thought of a daring little theft made {burglar.pronoun('possessive')} eyes shine."
    )


def setup_prize(world: World, burglar: Entity, prize: Entity) -> None:
    world.say(
        f"One day {burglar.id} saw {burglar.pronoun('possessive')} chance: {prize.phrase} sat alone, "
        f"waiting like treasure in a story."
    )
    world.say(
        f"{burglar.id} wanted it badly, because {prize.label} was sweet and bright and smelled like summer."
    )


def warning(world: World, burglar: Entity, risk: Risk, prize: Entity) -> bool:
    pred = foretell(world, burglar, risk, prize)
    if not pred["spilled"]:
        return False
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f'"If you try to {risk.verb}," a keeper warned, "the {prize.label} will {risk.soil}."'
    )
    return True


def mischief(world: World, burglar: Entity, risk: Risk, prize: Entity) -> None:
    burglar.meters["stealth"] = 1
    burglar.memes["boldness"] = burglar.memes.get("boldness", 0) + 1
    world.say(f"But {burglar.id} was already moving, drawn by the old itch to {risk.rush}.")
    world.say(f"{burglar.id} reached for the {prize.label}.")
    prize.held_by = burglar.id
    propagate(world, narrate=True)


def repent(world: World, burglar: Entity, prize: Entity, remedy: Remedy) -> None:
    burglar.memes["humor"] = burglar.memes.get("humor", 0) + 1
    burglar.memes["humility"] = burglar.memes.get("humility", 0) + 1
    world.say(
        f"Then {burglar.id} laughed at the shining disaster and said, "
        f'"A hero may be chased by fate, but I do not wish to be chased by stains."'
    )
    world.say(f"{burglar.id} used {remedy.label} and began to make amends.")
    world.say(
        f"{remedy.tail.capitalize()}, and soon the {prize.label} was safe again, "
        f"while the joke of the sticky floor lived on in the room."
    )


SETTINGS = {
    "orchard": Setting(name="the old orchard", place_kind="orchard", affords={"juice_theft"}),
    "market": Setting(name="the moonlit market", place_kind="market", affords={"juice_theft"}),
    "hall": Setting(name="the great hall", place_kind="hall", affords={"juice_theft"}),
}

RISKS = {
    "juice_theft": Risk(
        id="juice_theft",
        verb="snatch the juice",
        gerund="thieving juice",
        rush="dash to the cup",
        mess="sticky",
        soil="spill all over the floor",
        target="juice",
        keyword="juice",
        tags={"juice", "sticky", "humor"},
    )
}

PRIZES = {
    "juice": Prize(
        label="juice",
        phrase="a silver cup of honeyed juice",
        type="cup",
        holder="cup",
    )
}

REMEDIES = [
    Remedy(
        id="rag",
        label="a linen rag",
        prep="wipe the spill",
        tail="the rag soaked up the juice",
        guards={"sticky"},
        helps={"cup"},
    ),
    Remedy(
        id="broom",
        label="a long broom and a bucket",
        prep="sweep and scrub the floor",
        tail="the broom cleared the trail",
        guards={"sticky"},
        helps={"cup"},
    ),
]

NAMES = ["Milo", "Iris", "Nestor", "Pia", "Rhea", "Tarin", "Lena"]
TITLES = ["burglar", "thief", "shadow", "rascal"]


@dataclass
class StoryParams:
    place: str
    risk: str
    prize: str
    name: str
    title: str
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
    combos = []
    for place, setting in SETTINGS.items():
        for risk_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, risk_id, prize_id))
    return combos


def explain_rejection(_: Risk, __: Prize) -> str:
    return "(No story: this world only has one honest problem, and it is the juice theft.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic comic storyworld about a burglar and juice.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TITLES)
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
    if getattr(args, "risk", None) and getattr(args, "prize", None):
        if getattr(args, "risk", None) not in RISKS or getattr(args, "prize", None) not in PRIZES:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "risk", None) is None or c[1] == getattr(args, "risk", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, risk_id, prize_id = rng.choice(list(combos))
    return StoryParams(
        place=place,
        risk=risk_id,
        prize=prize_id,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        title=getattr(args, "title", None) or rng.choice(TITLES),
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    burglar = world.add(Entity(id=params.name, kind="character", type=params.title, label=params.title))
    prize = world.add(Entity(id="juice", kind="thing", type="cup", label="juice", phrase="a silver cup of honeyed juice"))
    risk = _safe_lookup(RISKS, params.risk)

    opening(world, burglar, world.setting, risk)
    world.para()
    setup_prize(world, burglar, prize)
    warning(world, burglar, risk, prize)
    mischief(world, burglar, risk, prize)
    world.para()

    remedy = choose_remedy(risk, prize)
    if remedy:
        rep = world.add(Entity(id=remedy.id, kind="thing", type="tool", label=remedy.label))
        rep.owner = burglar.id
        repent(world, burglar, prize, remedy)

    world.facts.update(burglar=burglar, prize=prize, risk=risk, remedy=remedy, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    b = _safe_fact(world, f, "burglar")
    r = _safe_fact(world, f, "risk")
    return [
        f"Write a short myth-like story for children about a {b.type} named {b.id} and the {r.keyword}.",
        f"Tell a funny old-style tale in which {b.id} tries to {r.verb} but learns a better way.",
        f"Write a gentle story with a burglar, juice, trouble, and a silly ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    b = _safe_fact(world, f, "burglar")
    p = _safe_fact(world, f, "prize")
    r = _safe_fact(world, f, "risk")
    qs = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {b.id}, a clever little {b.type} who gets into trouble over juice.",
        ),
        QAItem(
            question=f"What did {b.id} want to do with the juice?",
            answer=f"{b.id} wanted to {r.verb} and carry the juice away, but that plan made a sticky mess.",
        ),
        QAItem(
            question=f"Why did the warning matter?",
            answer=f"The warning mattered because if {b.id} tried to {r.verb}, the {p.label} would {r.soil}.",
        ),
    ]
    if f.get("remedy"):
        qs.append(QAItem(
            question="How did the story end after the mess?",
            answer=f"{b.id} laughed, used a rag to clean up, and the juice was safe again while everyone remembered the joke.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is juice?",
            answer="Juice is a sweet drink made from fruit. It can spill easily and make a sticky mess.",
        ),
        QAItem(
            question="What does a burglar do?",
            answer="A burglar sneaks in to take things that are not theirs. In stories, burglars often cause trouble.",
        ),
        QAItem(
            question="Why do people clean up spills?",
            answer="People clean up spills so the floor is safe and not sticky or slippery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world qa ==")
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
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(R, P) :- risky(R), prize(P).
has_fix(R, P) :- remedy(M), guards(M, sticky), helps(M, cup), risky(R), prize(P).
valid(Place, R, P) :- setting(Place), affords(Place, R), prize_at_risk(R, P), has_fix(R, P).
"""


def asp_facts() -> str:
    import asp
    out: list[str] = []
    for pid, s in SETTINGS.items():
        out.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            out.append(asp.fact("affords", pid, a))
    for rid in RISKS:
        out.append(asp.fact("risky", rid))
    for pid in PRIZES:
        out.append(asp.fact("prize", pid))
    for rem in REMEDIES:
        out.append(asp.fact("remedy", rem.id))
        for g in sorted(rem.guards):
            out.append(asp.fact("guards", rem.id, g))
        for h in sorted(rem.helps):
            out.append(asp.fact("helps", rem.id, h))
    return "\n".join(out)


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
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="orchard", risk="juice_theft", prize="juice", name="Milo", title="burglar"),
    StoryParams(place="market", risk="juice_theft", prize="juice", name="Iris", title="shadow"),
    StoryParams(place="hall", risk="juice_theft", prize="juice", name="Nestor", title="rascal"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp_program("#show valid/3."))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
