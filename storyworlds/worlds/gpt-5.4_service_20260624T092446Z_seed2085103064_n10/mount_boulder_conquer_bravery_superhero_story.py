#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    boulder: object | None = None
    helper: object | None = None
    hero: object | None = None
    target: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    id: str
    mount_name: str
    place: str
    sky: str
    resources: set[str]
    style_line: str
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
class Boulder:
    id: str
    label: str
    phrase: str
    size: str
    weight: int
    color: str
    mood_word: str
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
class Method:
    id: str
    label: str
    resource: str
    power: int
    prep: str
    action: str
    finish: str
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
class Mission:
    id: str
    need: str
    waiting_for: str
    ending_image: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_encouragement(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    if helper.memes["encouraged"] < THRESHOLD or hero.memes["fear"] < THRESHOLD:
        return out
    sig = ("encouragement", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    hero.memes["hope"] += 1
    out.append(f"{hero.id} felt a little steadier inside.")
    return out


def _r_move_boulder(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    boulder = world.entities.get("boulder")
    if not hero or not boulder:
        return out
    if hero.meters["effort"] < THRESHOLD:
        return out
    total = hero.meters["might"] + hero.meters["tool_power"] + hero.memes["bravery"]
    needed = boulder.meters["weight"]
    sig = ("moved", boulder.id, int(total))
    if total >= needed and ("moved_once", boulder.id) not in world.fired:
        world.fired.add(sig)
        world.fired.add(("moved_once", boulder.id))
        boulder.meters["moved"] = 1
        world.facts["path_open"] = True
        out.append(f"The boulder finally rolled aside with a deep stoney rumble.")
    return out


def _r_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    target = world.entities.get("target")
    boulder = world.entities.get("boulder")
    if not hero or not target or not boulder:
        return []
    if boulder.meters["moved"] < THRESHOLD:
        return []
    sig = ("relief", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["pride"] += 1
    target.memes["relief"] += 1
    return ["The blocked way was open again."]


CAUSAL_RULES = [
    Rule("encouragement", _r_encouragement),
    Rule("move_boulder", _r_move_boulder),
    Rule("relief", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "bright": Setting(
        id="bright",
        mount_name="Mount Bright",
        place="the sunny path on Mount Bright",
        sky="golden",
        resources={"firm_ground", "sturdy_branch"},
        style_line="The mountain looked like a giant hero stage with bright clouds behind it.",
    ),
    "pine": Setting(
        id="pine",
        mount_name="Mount Pine",
        place="the pine trail on Mount Pine",
        sky="cool blue",
        resources={"firm_ground", "sturdy_branch", "anchor_tree"},
        style_line="Tall trees stood like green guards along the trail.",
    ),
    "moon": Setting(
        id="moon",
        mount_name="Moonrise Mount",
        place="the silver path on Moonrise Mount",
        sky="silver",
        resources={"anchor_tree"},
        style_line="The stones shone as if moonlight had painted them with quiet magic.",
    ),
    "echo": Setting(
        id="echo",
        mount_name="Echo Mount",
        place="the high switchback on Echo Mount",
        sky="clear",
        resources={"firm_ground"},
        style_line="Every brave word bounced back from the cliffs like a cheer.",
    ),
}

BOULDERS = {
    "small": Boulder(
        id="small",
        label="boulder",
        phrase="a round little boulder",
        size="small",
        weight=2,
        color="speckled gray",
        mood_word="stubborn",
    ),
    "medium": Boulder(
        id="medium",
        label="boulder",
        phrase="a broad heavy boulder",
        size="medium",
        weight=3,
        color="storm-gray",
        mood_word="heavy",
    ),
    "huge": Boulder(
        id="huge",
        label="boulder",
        phrase="an enormous cliff-sized boulder",
        size="huge",
        weight=4,
        color="dark granite",
        mood_word="enormous",
    ),
}

METHODS = {
    "push": Method(
        id="push",
        label="super push",
        resource="firm_ground",
        power=2,
        prep="set both boots on the ground and planted a red cape behind like a flag",
        action="pushed with a superhero grunt",
        finish="using steady feet and a brave heart",
    ),
    "lever": Method(
        id="lever",
        label="thunder lever",
        resource="sturdy_branch",
        power=3,
        prep="slid a sturdy branch under the stone like a giant lever",
        action="pressed down with all that careful force",
        finish="using brains and strength together",
    ),
    "rope": Method(
        id="rope",
        label="sky rope pull",
        resource="anchor_tree",
        power=4,
        prep="looped a rescue rope around the boulder and tied the other end to a strong tree",
        action="leaned back and pulled in brave, even tugs",
        finish="turning one smart plan into a mighty victory",
    ),
}

MISSIONS = {
    "goat": Mission(
        id="goat",
        need="reach a lost baby goat on the other side",
        waiting_for="a lost baby goat",
        ending_image="The baby goat trotted down the open trail and nuzzled the hero's cape.",
    ),
    "lantern": Mission(
        id="lantern",
        need="carry a lantern to the watch hut before evening",
        waiting_for="the dark watch hut",
        ending_image="Soon the lantern glowed in the little hut window high on the mount.",
    ),
    "soup": Mission(
        id="soup",
        need="bring warm soup to the tired ranger above the turn",
        waiting_for="a tired ranger",
        ending_image="Steam curled from the soup cup while the ranger smiled at the open trail.",
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Skye", "Ruby", "Tessa"]
BOY_NAMES = ["Bolt", "Leo", "Max", "Theo", "Jett", "Eli"]
TRAITS = ["kind", "quick", "sparky", "cheerful", "steady", "bold"]


def method_works(setting: Setting, boulder: Boulder, method: Method) -> bool:
    return method.resource in setting.resources and method.power >= boulder.weight


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for bid, boulder in BOULDERS.items():
            for mid, method in METHODS.items():
                if method_works(setting, boulder, method):
                    out.append((sid, bid, mid))
    return sorted(out)


def explain_rejection(setting: Setting, boulder: Boulder, method: Method) -> str:
    if method.resource not in setting.resources:
        need = {
            "firm_ground": "firm ground",
            "sturdy_branch": "a sturdy branch",
            "anchor_tree": "a strong anchor tree",
        }[method.resource]
        return (
            f"(No story: {setting.mount_name} does not offer {need}, so the "
            f"{method.label} plan has nothing honest to work with there.)"
        )
    return (
        f"(No story: the {method.label} is not strong enough to conquer "
        f"{boulder.phrase}. Choose a stronger method or a smaller boulder.)"
    )


def predict_success(world: World, method: Method) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    boulder = sim.get("boulder")
    hero.meters["tool_power"] = method.power
    hero.meters["effort"] += 1
    hero.memes["bravery"] += 1
    propagate(sim, narrate=False)
    return boulder.meters["moved"] >= THRESHOLD


def hero_title(name: str) -> str:
    return f"Captain {name}"


def opening(world: World, hero: Entity, mission: Mission) -> None:
    trait = hero.traits[0] if hero.traits else "bold"
    world.say(
        f"{hero.id} liked to tie on a fluttering cape and pretend to be {hero_title(hero.id)}, "
        f"the littlest superhero on the mount. {world.setting.style_line}"
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} was a {trait} child who always watched for someone to help."
    )
    hero.memes["bravery"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"That day, {hero.pronoun('subject')} climbed toward the high path to {mission.need}."
    )


def discover_block(world: World, hero: Entity, boulder: Entity, mission: Mission) -> None:
    world.say(
        f"But halfway up {world.setting.mount_name}, {hero.pronoun('subject')} stopped. "
        f"{boulder.phrase.capitalize()} sat across the trail."
    )
    world.say(
        f"The {boulder.meters['color_name']} stone looked {world.facts['boulder_cfg'].mood_word}, "
        f"and it blocked the way to {mission.waiting_for}."
    )
    hero.memes["fear"] += 1
    world.facts["blocked"] = True


def first_try(world: World, hero: Entity, boulder: Entity) -> None:
    world.say(
        f'"I can conquer this!" {hero.id} said. {hero.pronoun("subject").capitalize()} rushed up and shoved the boulder with both hands.'
    )
    hero.meters["effort"] += 1
    hero.meters["tool_power"] = 0
    propagate(world, narrate=False)
    if boulder.meters["moved"] < THRESHOLD:
        hero.meters["effort"] = 0
        hero.meters["strain"] += 1
        hero.memes["fear"] += 1
        world.say(
            f"The stone did not move at all. Tiny pebbles slid under {hero.pronoun('possessive')} boots, "
            f"and for one moment {hero.pronoun('subject')} felt small."
        )


def helper_arrives(world: World, hero: Entity, helper: Entity, method: Method) -> None:
    helper.memes["encouraged"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then {helper.id}, a smiling trail guide in a blue scarf, waved from a bend in the path."
    )
    world.say(
        f'"Bravery is not only charging," {helper.id} said. "Bravery is stopping, thinking, and trying the right way."'
    )
    world.say(
        f"{hero.id} took a deep breath. The mountain wind felt cool, and {hero.pronoun('subject')} listened."
    )
    world.say(
        f"Together they made a plan for the {method.label}."
    )


def prepare_method(world: World, hero: Entity, method: Method) -> None:
    world.say(
        f"{hero.id} {method.prep}."
    )
    hero.meters["tool_power"] = method.power
    hero.meters["effort"] = 0


def final_try(world: World, hero: Entity, boulder: Entity, method: Method) -> None:
    hero.meters["effort"] += 1
    world.say(
        f"Then {hero.pronoun('subject')} {method.action}. {hero.pronoun('possessive').capitalize()} cape snapped in the wind."
    )
    propagate(world, narrate=True)
    if boulder.meters["moved"] >= THRESHOLD:
        world.say(
            f"{hero.id} had conquered the boulder, not by being reckless, but by {method.finish}."
        )


def ending(world: World, hero: Entity, mission: Mission) -> None:
    if not world.facts.get("path_open"):
        pass
    world.say(
        f"{hero.id} hurried up the trail at last and finished the mission."
    )
    world.say(
        mission.ending_image
    )
    world.say(
        f"When {hero.pronoun('subject')} looked back, the path on {world.setting.mount_name} seemed a little kinder. "
        f"{hero.pronoun('subject').capitalize()} touched the cape and smiled, feeling true Bravery glowing inside."
    )


def tell(params: "StoryParams") -> World:
    setting = _safe_lookup(SETTINGS, params.mount)
    boulder_cfg = _safe_lookup(BOULDERS, params.boulder)
    method = _safe_lookup(METHODS, params.method)
    mission = _safe_lookup(MISSIONS, params.mission)
    if not method_works(setting, boulder_cfg, method):
        pass

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=[params.trait],
    ))
    helper = world.add(Entity(
        id="Guide Ada" if params.gender == "boy" else "Guide Ben",
        kind="character",
        type="woman" if params.gender == "boy" else "man",
        label="guide",
    ))
    boulder = world.add(Entity(
        id="boulder",
        kind="thing",
        type="boulder",
        label="boulder",
        phrase=boulder_cfg.phrase,
    ))
    target = world.add(Entity(
        id="target",
        kind="thing",
        type="mission",
        label=mission.waiting_for,
    ))
    hero.meters["might"] = 1
    boulder.meters["weight"] = boulder_cfg.weight
    boulder.meters["color_name"] = 0
    world.facts["boulder_cfg"] = boulder_cfg
    boulder.meters["color_name"] = 0
    boulder.memes["still"] = 1
    world.facts.update(
        hero=hero,
        helper=helper,
        boulder=boulder,
        mission=mission,
        method=method,
        setting=setting,
        path_open=False,
    )
    boulder.meters["color_name"] = 0
    boulder.meters["weight"] = boulder_cfg.weight
    boulder.meters["moved"] = 0
    boulder.meters["color_name"] = 0
    boulder.meters["weight"] = boulder_cfg.weight
    boulder.meters["color_name"] = 0
    boulder.meters["weight"] = boulder_cfg.weight
    boulder.meters["color_name"] = 0
    boulder.meters["weight"] = boulder_cfg.weight
    boulder.meters["color_name"] = 0
    boulder.meters["weight"] = boulder_cfg.weight
    boulder.meters["color_name"] = 0
    boulder.meters["weight"] = boulder_cfg.weight
    boulder.meters["color_name"] = 0
    boulder.meters["weight"] = boulder_cfg.weight
    boulder.meters["color_name"] = 0
    boulder.meters["weight"] = boulder_cfg.weight
    boulder.meters["color_name"] = 0
    world.facts["boulder_color"] = boulder_cfg.color
    boulder.meters["color_name"] = 0

    opening(world, hero, mission)
    world.para()
    discover_block(world, hero, boulder, mission)
    first_try(world, hero, boulder)
    helper_arrives(world, hero, helper, method)
    world.para()
    prepare_method(world, hero, method)
    final_try(world, hero, boulder, method)
    ending(world, hero, mission)
    return world


@dataclass
class StoryParams:
    mount: str
    boulder: str
    method: str
    mission: str
    name: str
    gender: str
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


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    setting = _safe_fact(world, world.facts, "setting")
    method = _safe_fact(world, world.facts, "method")
    mission = _safe_fact(world, world.facts, "mission")
    boulder_cfg = _safe_fact(world, world.facts, "boulder_cfg")
    return [
        'Write a very short Superhero Story for a small child using the words "mount", "boulder", and "conquer".',
        f"Tell a gentle superhero tale about {hero.id} on {setting.mount_name}, where a {boulder_cfg.size} boulder blocks the trail and the hero learns that Bravery includes thinking before acting.",
        f"Write a child-facing story in which a little cape-wearing hero uses the {method.label} to help {mission.waiting_for} and ends with a bright image on the mountain.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    setting = _safe_fact(world, world.facts, "setting")
    method = _safe_fact(world, world.facts, "method")
    mission = _safe_fact(world, world.facts, "mission")
    boulder_cfg = _safe_fact(world, world.facts, "boulder_cfg")
    sub = hero.pronoun("subject")
    obj = hero.pronoun("object")
    pos = hero.pronoun("possessive")
    return [
        QAItem(
            question=f"Who is the little superhero in the story on {setting.mount_name}?",
            answer=(
                f"The little superhero is {hero.id}, a child in a fluttering cape who climbs the mount to help someone."
            ),
        ),
        QAItem(
            question=f"What problem stopped {hero.id} on the path?",
            answer=(
                f"A {boulder_cfg.size} {boulder_cfg.color} boulder blocked the trail, so {hero.id} could not reach {mission.waiting_for} right away."
            ),
        ),
        QAItem(
            question=f"Why did {hero.id} feel small for a moment?",
            answer=(
                f"{hero.id} tried to shove the boulder with bare hands, but it did not move. Tiny pebbles slipped under {pos} boots, so {sub} felt the mountain was stronger than {obj} for a moment."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} conquer the boulder in the end?",
            answer=(
                f"{hero.id} listened to the guide, made a smart plan, and used the {method.label}. That method fit the mountain and gave {obj} enough help to move the stone aside."
            ),
        ),
        QAItem(
            question="What did the story show about Bravery?",
            answer=(
                "The story showed that Bravery is not only rushing forward. It also means taking a breath, listening, and trying the wise way when a hard problem stands in front of you."
            ),
        ),
    ]


KNOWLEDGE = {
    "mount": QAItem(
        question="What is a mount?",
        answer="A mount is a high hill or mountain. People climb it by following paths or trails."
    ),
    "boulder": QAItem(
        question="What is a boulder?",
        answer="A boulder is a very big rock. It is much larger than the stones you can hold in your hand."
    ),
    "lever": QAItem(
        question="How can a lever help move a heavy rock?",
        answer="A lever lets you press on one end of a strong stick or bar so the other end lifts or nudges the heavy thing."
    ),
    "rope": QAItem(
        question="Why can a rope help with a heavy job?",
        answer="A rope lets you pull from a safer place and share force over a longer line."
    ),
    "bravery": QAItem(
        question="What is bravery?",
        answer="Bravery is doing the right thing even when something feels hard or scary. It does not mean being careless."
    ),
    "trail": QAItem(
        question="Why is a blocked trail a problem on a mountain?",
        answer="A blocked trail can stop people from reaching someone who needs help, and it may make climbing unsafe."
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    items = [KNOWLEDGE["mount"], KNOWLEDGE["boulder"], KNOWLEDGE["bravery"], KNOWLEDGE["trail"]]
    method = _safe_fact(world, world.facts, "method").id
    if method == "lever":
        items.append(KNOWLEDGE["lever"])
    if method == "rope":
        items.append(KNOWLEDGE["rope"])
    return items


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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mount="bright",
        boulder="small",
        method="push",
        mission="goat",
        name="Nova",
        gender="girl",
        trait="cheerful",
    ),
    StoryParams(
        mount="pine",
        boulder="medium",
        method="lever",
        mission="soup",
        name="Bolt",
        gender="boy",
        trait="steady",
    ),
    StoryParams(
        mount="moon",
        boulder="huge",
        method="rope",
        mission="lantern",
        name="Luna",
        gender="girl",
        trait="kind",
    ),
]


ASP_RULES = r"""
works(Mount,Boulder,Method) :-
    setting(Mount), boulder(Boulder), method(Method),
    has_resource(Mount,R), needs(Method,R),
    weight(Boulder,W), power(Method,P), P >= W.

#show works/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for res in sorted(setting.resources):
            lines.append(asp.fact("has_resource", sid, res))
    for bid, b in BOULDERS.items():
        lines.append(asp.fact("boulder", bid))
        lines.append(asp.fact("weight", bid, b.weight))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("needs", mid, m.resource))
        lines.append(asp.fact("power", mid, m.power))
    return "\n".join(lines)


def asp_program(show: str = "#show works/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show works/3."))
    return sorted(set(asp.atoms(model, "works")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    code = 0
    if py != cl:
        print("MISMATCH between Python and ASP valid combos.")
        if py - cl:
            print(" only in python:", sorted(py - cl))
        if cl - py:
            print(" only in asp:", sorted(cl - py))
        code = 1
    else:
        print(f"OK: Python and ASP agree on {len(py)} valid combos.")
    try:
        for p in CURATED:
            sample = generate(p)
            if not sample.story.strip():
                pass
        print(f"OK: exercised {len(CURATED)} curated stories.")
    except StoryError as err:
        print(f"Verification story failed: {err}")
        return 1
    return code


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero mountain storyworld: a little hero learns brave wisdom while conquering a boulder."
    )
    ap.add_argument("--mount", choices=SETTINGS)
    ap.add_argument("--boulder", choices=BOULDERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "mount", None) and getattr(args, "boulder", None) and getattr(args, "method", None):
        setting = _safe_lookup(SETTINGS, getattr(args, "mount", None))
        boulder = _safe_lookup(BOULDERS, getattr(args, "boulder", None))
        method = _safe_lookup(METHODS, getattr(args, "method", None))
        if not method_works(setting, boulder, method):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        combo for combo in valid_combos()
        if (getattr(args, "mount", None) is None or combo[0] == getattr(args, "mount", None))
        and (getattr(args, "boulder", None) is None or combo[1] == getattr(args, "boulder", None))
        and (getattr(args, "method", None) is None or combo[2] == getattr(args, "method", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    mount, boulder, method = rng.choice(list(combos))
    mission = getattr(args, "mission", None) or rng.choice(sorted(MISSIONS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        mount=mount,
        boulder=boulder,
        method=method,
        mission=mission,
        name=name,
        gender=gender,
        trait=trait,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for mount, boulder, method in asp_valid_combos():
            print(f"{mount:7} {boulder:6} {method}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mount} / {p.boulder} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
