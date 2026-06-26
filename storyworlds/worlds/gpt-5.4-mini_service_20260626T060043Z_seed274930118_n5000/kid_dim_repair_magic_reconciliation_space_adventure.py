#!/usr/bin/env python3
"""
A standalone story world for a small space-adventure tale about a kid-sized
repair job, a little magic, and a reconciliation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    broken: bool = False
    fixed: bool = False
    energized: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    friend: object | None = None
    kid: object | None = None
    magic: object | None = None
    thing: object | None = None
    tool: object | None = None
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
    indoors: bool = False
    stars_visible: bool = True
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
class Kid:
    id: str
    type: str
    gender: str
    trait: str
    small: bool = True
    name_style: str = "kid-dim"
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
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    requires_magic: bool = False
    repairs: set[str] = field(default_factory=set)
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
class Magic:
    id: str
    label: str
    phrase: str
    glow: str
    repairs: set[str] = field(default_factory=set)
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "starport": Setting(place="the starport bay", indoors=True, stars_visible=False, affords={"repair", "magic"}),
    "moon_hangar": Setting(place="the moon hangar", indoors=True, stars_visible=True, affords={"repair", "magic"}),
    "orbital_garden": Setting(place="the orbital garden", indoors=False, stars_visible=True, affords={"repair", "magic"}),
}

KIDS = {
    "lina": Kid(id="Lina", type="girl", gender="girl", trait="curious"),
    "max": Kid(id="Max", type="boy", gender="boy", trait="brave"),
    "maya": Kid(id="Maya", type="girl", gender="girl", trait="gentle"),
    "tio": Kid(id="Tio", type="boy", gender="boy", trait="bright"),
}

TOOLS = {
    "kit": Tool(id="repair_kit", label="repair kit", phrase="a little repair kit", kind="tool", repairs={"drone", "lamp"}),
    "patcher": Tool(id="patcher", label="patch wand", phrase="a tiny patch wand", kind="tool", requires_magic=True, repairs={"drone", "panel"}),
}

MAGICS = {
    "spark": Magic(id="spark", label="sparkle spell", phrase="a sparkle spell", glow="silver", repairs={"drone", "panel", "lamp"}),
    "mend": Magic(id="mend", label="mend charm", phrase="a warm mend charm", glow="gold", repairs={"drone", "lamp", "panel"}),
}

BROKEN_THINGS = {
    "drone": Entity(id="drone", type="toy", label="toy drone", phrase="a tiny toy drone", broken=True, caretaker="Friend"),
    "lamp": Entity(id="lamp", type="thing", label="signal lamp", phrase="a small signal lamp", broken=True, caretaker="Friend"),
    "panel": Entity(id="panel", type="thing", label="control panel", phrase="a moon control panel", broken=True, caretaker="Friend"),
}

TRAITS = ["curious", "brave", "gentle", "bright"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def setup_world(params: "StoryParams") -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    kid = world.add(Entity(id="Kid", kind="character", type=params.gender, label=params.name))
    friend = world.add(Entity(id="Friend", kind="character", type=params.friend_gender, label=params.friend_name))
    thing = world.add(Entity(
        id="Thing",
        kind="thing",
        type=params.thing_kind,
        label=_safe_lookup(BROKEN_THINGS, params.thing_kind).label,
        phrase=_safe_lookup(BROKEN_THINGS, params.thing_kind).phrase,
        broken=True,
        caretaker=friend.id,
    ))
    tool = world.add(Entity(
        id="Tool",
        kind="thing",
        type="tool",
        label=_safe_lookup(TOOLS, params.tool).label,
        phrase=_safe_lookup(TOOLS, params.tool).phrase,
        owner=kid.id,
    ))
    magic = world.add(Entity(
        id="Magic",
        kind="thing",
        type="magic",
        label=_safe_lookup(MAGICS, params.magic).label,
        phrase=_safe_lookup(MAGICS, params.magic).phrase,
        owner=kid.id,
    ))
    world.facts.update(kid=kid, friend=friend, thing=thing, tool=tool, magic=magic, params=params)
    return world


def _maybe_repair(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("Kid")
    thing = world.get("Thing")
    tool = world.get("Tool")
    magic = world.get("Magic")
    sig = ("repair", thing.id)
    if sig in world.fired:
        return out
    if not thing.broken:
        return out
    if thing.type in _safe_lookup(TOOLS, tool.id).repairs and thing.type in _safe_lookup(MAGICS, magic.id).repairs:
        if kid.memes.get("hope", 0) >= THRESHOLD and kid.meters.get("focus", 0) >= THRESHOLD:
            world.fired.add(sig)
            thing.broken = False
            thing.fixed = True
            thing.energized = True
            kid.meters["repair_done"] = kid.meters.get("repair_done", 0) + 1
            out.append(f"The broken {thing.label} clicked back to life.")
    return out


def _maybe_reconcile(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("Kid")
    friend = world.get("Friend")
    thing = world.get("Thing")
    sig = ("reconcile", friend.id)
    if sig in world.fired:
        return out
    if friend.memes.get("hurt", 0) < THRESHOLD:
        return out
    if thing.fixed:
        world.fired.add(sig)
        friend.memes["hurt"] = 0
        friend.memes["trust"] = friend.memes.get("trust", 0) + 1
        kid.memes["sorry"] = 0
        kid.memes["love"] = kid.memes.get("love", 0) + 1
        out.append("The two friends looked at each other and let the hurt drift away.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_maybe_repair, _maybe_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: "StoryParams") -> World:
    world = setup_world(params)
    kid = world.get("Kid")
    friend = world.get("Friend")
    thing = world.get("Thing")
    tool = world.get("Tool")
    magic = world.get("Magic")

    kid.memes["wonder"] = 1
    kid.memes["hope"] = 1
    kid.meters["focus"] = 1

    world.say(
        f"{kid.label} was a little {params.trait} kid with a kid-dim pocket full of moon dust and brave plans."
    )
    world.say(
        f"{kid.label} and {friend.label} were on {world.setting.place} when they saw {thing.phrase} sitting dark and broken."
    )
    world.say(
        f"{kid.label} had {tool.phrase}, and {kid.label} also knew {magic.phrase} would shine if the repair was gentle enough."
    )

    world.para()
    kid.memes["guilt"] = 1
    friend.memes["hurt"] = 1
    world.say(
        f"While they were reaching for the broken {thing.label}, {kid.label} bumped it by accident, and the little {thing.label} went still."
    )
    world.say(
        f"{friend.label} frowned, because the space mission felt lonely when the favorite thing was snapped and quiet."
    )

    world.para()
    kid.memes["sorry"] = 1
    kid.memes["hope"] += 1
    kid.meters["focus"] += 1
    world.say(
        f"{kid.label} took a slow breath, opened the repair kit, and traced the crack with a careful hand."
    )
    world.say(
        f"Then {kid.label} whispered the {magic.label}, and the silver glow settled over the broken place like a tiny star."
    )
    propagate(world, narrate=True)

    world.para()
    if thing.fixed:
        world.say(
            f"The {thing.label} blinked on again, bright as a happy beacon, and {friend.label}'s mouth softened into a smile."
        )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{kid.label} said sorry for the bump, and {friend.label} forgave {kid.label} with a nod and a warm hug."
    )
    if thing.fixed:
        world.say(
            f"After that, they flew their little mission together, with the repaired {thing.label} humming beside them like a new moon."
        )

    world.facts.update(repaired=thing.fixed, reconciled=True)
    return world


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    trait: str
    friend_name: str
    friend_gender: str
    thing_kind: str
    tool: str
    magic: str
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
    ap = argparse.ArgumentParser(description="Kid-dim repair magic reconciliation space adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=[k.id for k in KIDS.values()])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--thing-kind", choices=sorted(BROKEN_THINGS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--magic", choices=sorted(MAGICS))
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice([k.id for k in KIDS.values()])
    gender = getattr(args, "gender", None) or _safe_lookup(KIDS, name.lower()).gender if name.lower() in KIDS else rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    friend_gender = getattr(args, "friend_gender", None) or rng.choice(["girl", "boy"])
    friend_name = getattr(args, "friend_name", None) or rng.choice(["Nova", "Iris", "Pip", "Rin", "Juno", "Tess"])
    thing_kind = getattr(args, "thing_kind", None) or rng.choice(list(BROKEN_THINGS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGICS))

    if thing_kind not in _safe_lookup(TOOLS, tool).repairs or thing_kind not in _safe_lookup(MAGICS, magic).repairs:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place, name, gender, trait, friend_name, friend_gender, thing_kind, tool, magic)


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short space adventure for a young child that includes kid-dim and repair.',
        f"Tell a gentle story where {p.name} uses a {world.get('Tool').label} and {world.get('Magic').label} to fix a broken {world.get('Thing').label} and make up with a friend.",
        f"Write a child-friendly tale set at {world.setting.place} about a mistake, a magical repair, and a happy reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    kid = world.get("Kid")
    friend = world.get("Friend")
    thing = world.get("Thing")
    tool = world.get("Tool")
    magic = world.get("Magic")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {kid.label}, a little kid who stayed brave in a kid-dim space place.",
        ),
        QAItem(
            question=f"What was broken at the start?",
            answer=f"{thing.phrase} was broken and quiet at the start of the story.",
        ),
        QAItem(
            question=f"What did {kid.label} use to help fix it?",
            answer=f"{kid.label} used {tool.phrase} and then {magic.phrase} to help repair it.",
        ),
        QAItem(
            question=f"How did the friends feel at the end?",
            answer=f"They felt happy again, because the repair worked and they reconciled after the mistake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a repair kit for?",
            answer="A repair kit is for fixing something that is broken or loose.",
        ),
        QAItem(
            question="What does a magic spell do in a story?",
            answer="In a story, a magic spell can make something glow, change, or mend in a special way.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a fight or hurt feeling so people can be friends again.",
        ),
        QAItem(
            question="Why do spaceships need careful fixing?",
            answer="Spaceships need careful fixing because their parts have to work together safely in a faraway place.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.broken:
            bits.append("broken=True")
        if e.fixed:
            bits.append("fixed=True")
        if e.energized:
            bits.append("energized=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:6} ({e.kind:7} {e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
thing_repairs_with(T, X) :- repair_tool(T), repairs(T, X).
thing_repairs_with_magic(M, X) :- magic(M), repairs_magic(M, X).
valid_story(P, T, M, X) :- place(P), repair_tool(T), magic(M), thing(X),
                           thing_repairs_with(T, X), thing_repairs_with_magic(M, X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("repair_tool", tid))
        for x in sorted(tool.repairs):
            lines.append(asp.fact("repairs", tid, x))
    for mid, magic in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        for x in sorted(magic.repairs):
            lines.append(asp.fact("repairs_magic", mid, x))
    for x in BROKEN_THINGS:
        lines.append(asp.fact("thing", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    asp_set = set(asp_valid_stories())
    py_set = set()
    for place in SETTINGS:
        for tool in TOOLS:
            for magic in MAGICS:
                for thing in BROKEN_THINGS:
                    if thing in _safe_lookup(TOOLS, tool).repairs and thing in _safe_lookup(MAGICS, magic).repairs:
                        py_set.add((place, tool, magic, thing))
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("starport", "Lina", "girl", "curious", "Nova", "girl", "drone", "kit", "spark"),
    StoryParams("moon_hangar", "Max", "boy", "brave", "Tess", "girl", "panel", "patcher", "mend"),
    StoryParams("orbital_garden", "Maya", "girl", "gentle", "Pip", "boy", "lamp", "kit", "mend"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Kid-dim repair magic reconciliation space adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--thing-kind", choices=sorted(BROKEN_THINGS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--magic", choices=sorted(MAGICS))
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(asp.atoms(model, "valid_story"))
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
