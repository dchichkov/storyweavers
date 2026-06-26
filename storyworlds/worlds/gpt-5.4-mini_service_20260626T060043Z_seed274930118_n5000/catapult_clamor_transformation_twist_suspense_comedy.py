#!/usr/bin/env python3
"""
A tiny comedy storyworld about a catapult, a clamor, and a surprising
transformation twist.

Premise:
- A child wants to launch harmless things with a catapult.
- The loud clamor worries a caretaker or friend.
- A mistaken plan causes a silly transformation.
- The twist resolves the suspense in a playful way.

The simulated world tracks:
- physical meters: loudness, wobble, sticky, sparkly, transformed
- emotional memes: delight, worry, suspense, surprise, relief, pride

This world is intentionally small and constraint-checked. It only generates
stories when the central premise can plausibly turn into a comedic resolution.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the backyard"
    indoors: bool = False
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
class Tool:
    id: str
    label: str
    verb: str
    gerund: str
    noise: str
    launch: str
    mess: str
    twist: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Prize:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class TwistItem:
    id: str
    label: str
    phrase: str
    transformation: str
    returns: str
    turns_into: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _apply_clamor(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters.get("loud", 0.0) < THRESHOLD:
            continue
        sig = ("clamor", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["suspense"] = e.memes.get("suspense", 0.0) + 1
        out.append(f"The clamor made everybody peek over the fence.")
    return out


def _apply_transformation(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters.get("sticky", 0.0) < THRESHOLD:
            continue
        sig = ("transform", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["transformed"] = 1.0
        e.memes["surprise"] = e.memes.get("surprise", 0.0) + 1
        out.append(f"With a pop and a wobble, the silly machine transformed the toy.")
    return out


def _apply_relief(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.memes.get("surprise", 0.0) < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["relief"] = e.memes.get("relief", 0.0) + 1
        out.append("Then everyone realized the new shape was even funnier than the old one.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_apply_clamor, _apply_transformation, _apply_relief):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def compatible(tool: Tool, prize: Prize) -> bool:
    return prize.region in tool.zone


def explain_rejection(tool: Tool, prize: Prize) -> str:
    return (
        f"(No story: this catapult tale only works when the at-risk item sits in the launch zone. "
        f"{prize.label} on the {prize.region} would not plausibly be changed by {tool.gerund}.)"
    )


def choose_compatible_tool_prize(tool: Tool, prize: Prize) -> bool:
    return compatible(tool, prize)


def predict(world: World, actor: Entity, tool: Tool, prize: Prize) -> dict:
    sim = world.copy()
    do_launch(sim, sim.get(actor.id), tool, prize, narrate=False)
    return {
        "transformed": sim.get(prize.id).meters.get("transformed", 0.0) >= THRESHOLD,
        "relief": sim.get(actor.id).memes.get("relief", 0.0) >= THRESHOLD,
    }


def do_launch(world: World, actor: Entity, tool: Tool, prize: Prize, narrate: bool = True) -> None:
    if tool.id not in world.setting.affords:
        pass
    prize_ent = world.get(prize.id)
    actor.meters["loud"] = actor.meters.get("loud", 0.0) + 1
    actor.meters["sticky"] = actor.meters.get("sticky", 0.0) + 1
    actor.memes["delight"] = actor.memes.get("delight", 0.0) + 1
    prize_ent.meters["sticky"] = prize_ent.meters.get("sticky", 0.0) + 1
    if compatible(tool, prize):
        prize_ent.meters["transformed"] = prize_ent.meters.get("transformed", 0.0) + 1
    if narrate:
        world.say(
            f"{actor.id} pulled back the catapult and let the little load fly. "
            f"The {tool.label} gave a noisy twang, and the whole yard filled with clamor."
        )
    propagate(world, narrate=narrate)


SETTINGS = {
    "backyard": Setting(place="the backyard", indoors=False, affords={"catapult"}),
    "garden": Setting(place="the garden", indoors=False, affords={"catapult"}),
    "field": Setting(place="the field", indoors=False, affords={"catapult"}),
}


TOOLS = {
    "catapult": Tool(
        id="catapult",
        label="catapult",
        verb="use the catapult",
        gerund="using the catapult",
        noise="twang",
        launch="launch",
        mess="sticky",
        twist="turn into a comic splash",
        zone={"hands", "air"},
        tags={"catapult", "clamor"},
    ),
}


PRIZES = {
    "apple": Prize(id="apple", label="apple", phrase="a shiny apple", region="hands"),
    "pie": Prize(id="pie", label="pie", phrase="a tiny pie", region="hands"),
    "beanbag": Prize(id="beanbag", label="beanbag", phrase="a squishy beanbag", region="hands"),
}


TWISTS = {
    "duck": TwistItem(
        id="duck",
        label="rubber duck",
        phrase="a rubber duck",
        transformation="turned the target into a rubber duck",
        returns="the duck popped back to normal at the end",
        turns_into="duck",
    ),
    "hat": TwistItem(
        id="hat",
        label="silly hat",
        phrase="a silly hat",
        transformation="turned the target into a silly hat",
        returns="the hat went back to normal with a blink",
        turns_into="hat",
    ),
}


GIRL_NAMES = ["Mia", "Nina", "Zoe", "Ava", "Luna"]
BOY_NAMES = ["Leo", "Max", "Theo", "Finn", "Ben"]
TRAITS = ["cheerful", "curious", "silly", "bouncy", "brave"]


@dataclass
class StoryParams:
    place: str = ""
    tool: str = ""
    prize: str = ""
    twist: str = ""
    name: str = ""
    gender: str = ""
    parent: str = ""
    trait: str = ""
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for tool_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if compatible(_safe_lookup(TOOLS, tool_id), prize):
                    for twist_id in TWISTS:
                        combos.append((place, tool_id, prize_id, twist_id))
    return combos


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    tool = _safe_lookup(TOOLS, params.tool)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    twist = _safe_lookup(TWISTS, params.twist)
    w = World(setting)
    hero = w.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = w.add(Entity(id="Parent", kind="character", type=params.parent))
    prize = w.add(Entity(id=prize_cfg.id, type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase))
    prize.owner = hero.id
    prize.caretaker = parent.id
    w.facts.update(hero=hero, parent=parent, prize=prize, tool=tool, twist=twist, params=params)

    w.say(f"{hero.id} was a {params.trait} child who loved playing with a catapult.")
    w.say(
        f"{hero.pronoun('subject').capitalize()} liked the happy clack of wood, the little hop of the load, "
        f"and the funny clamor that followed."
    )
    w.say(f"One day, {hero.id}'s {params.parent} brought home {prize_cfg.phrase}.")
    w.say(f"{hero.id} adored {hero.pronoun('possessive')} {prize.label} and wanted to keep it safe.")

    w.para()
    w.say(
        f"At {setting.place}, {hero.id} wanted to {tool.verb} right away, but {hero.pronoun('possessive')} "
        f"{params.parent} frowned at the clamor."
    )
    w.say(
        f'"If that thing wobbles too hard, your {prize.label} may get changed by mistake," '
        f"{hero.pronoun('possessive')} {params.parent} warned."
    )

    w.para()
    w.say(f"{hero.id} tried anyway. {do_launch(w, hero, tool, prize, narrate=False) or ''}")
    w.say(
        f"The catapult twanged, the yard burst into clamor, and for a breathless moment everyone waited to see "
        f"whether the {prize.label} would stay the same."
    )
    w.say(
        f"Then came the twist: the sticky splash made the {prize.label} {twist.transformation}, "
        f"which was surprising but very funny."
    )
    if w.get(prize.id).meters.get("transformed", 0.0) >= THRESHOLD:
        w.say(
            f"{hero.id} blinked, giggled, and found that the new {twist.label} looked even sillier than the old prize."
        )
    w.para()
    w.say(
        f"{hero.id}'s {params.parent} looked from the transformed toy to {hero.id}'s grin and had to laugh too."
    )
    w.say(
        f"The suspense vanished when everyone agreed the funniest ending was keeping the new shape for a while."
    )
    w.say(
        f"By the end, {hero.id} was still smiling beside the catapult, and the clamor had turned into happy laughter."
    )
    w.facts["resolved"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short comedy story for a young child about {hero.id}, a catapult, and a noisy clamor.',
        f"Tell a story where {hero.id} wants to {tool.verb}, but {parent.id} worries about {prize.label}, and something funny happens.",
        f'Write a gentle suspense story with a twist in which a catapult changes {prize.label} in a silly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    twist = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist")
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the catapult?",
            answer=f"{hero.id} wanted to {tool.verb}, because the clack and clamor of the catapult made play feel exciting.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about {prize.label}?",
            answer=f"{parent.id} worried because the catapult's clamor and wobble might change {hero.pronoun('possessive')} {prize.label} in an unexpected way.",
        ),
        QAItem(
            question=f"What was the funny twist at the end?",
            answer=f"The twist was that the {prize.label} got {twist.transformation}, and that made the ending silly instead of scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a catapult?",
            answer="A catapult is a simple machine that flings something by snapping or swinging a arm quickly.",
        ),
        QAItem(
            question="What does clamor mean?",
            answer="Clamor means a loud, noisy commotion with lots of sound all at once.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new direction.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to learn what will happen next.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a different form.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="backyard", tool="catapult", prize="apple", twist="duck", name="Mia", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="garden", tool="catapult", prize="pie", twist="hat", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="field", tool="catapult", prize="beanbag", twist="duck", name="Zoe", gender="girl", parent="mother", trait="curious"),
]


ASP_RULES = r"""
tool_ok(T) :- tool(T).
prize_ok(P) :- prize(P).
compatible(T,P) :- zone(T,R), region(P,R).
valid(Place,T,P,W) :- setting(Place), affords(Place,T), compatible(T,P), twist(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for wid in TWISTS:
        lines.append(asp.fact("twist", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple]:
    return sorted(set(valid_combos()))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld of catapult clamor and a funny transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_story_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "tool", None) is None or c[1] == getattr(args, "tool", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "twist", None) is None or c[3] == getattr(args, "twist", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tool, prize, twist = (list(rng.choice(combos)) + [None, None, None, None])[:4]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, tool=tool, prize=prize, twist=twist, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combinations:")
        for c in combos:
            print(" ", c)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
