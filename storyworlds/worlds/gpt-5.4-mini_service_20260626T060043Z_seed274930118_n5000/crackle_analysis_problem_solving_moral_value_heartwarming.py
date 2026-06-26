#!/usr/bin/env python3
"""
storyworlds/worlds/crackle_analysis_problem_solving_moral_value_heartwarming.py
==============================================================================

A small heartwarming storyworld about a child who hears a crackle, does a bit
of careful analysis, and solves a cozy problem with kindness.

Seed tale inspiration:
---
A child hears a strange crackle in the kitchen while tea is being made. At
first, the sound feels worrying. The child looks closely, thinks about what
could be causing it, and helps the grown-up fix the problem. In the end, the
tea is ready, the sound is safe, and everyone feels proud of the careful,
helpful choice.

World premise:
---
- A warm kitchen, a family tea ritual, and a little problem that makes a
  crackling sound.
- The child can notice clues, make an analysis, and choose a helpful action.
- The moral turn is that asking, observing, and helping kindly matter more than
  guessing or panicking.

Narrative instruments:
---
- Problem Solving: the child tests a cause, removes the issue, and restores
  calm.
- Moral Value: honesty, patience, and helping a family member.
- Heartwarming: the resolution ends in shared warmth, praise, and tea.
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
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    cup: object | None = None
    helper: object | None = None
    pot: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
    place: str = "the kitchen"
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
class Cause:
    id: str
    label: str
    clue: str
    fix: str
    crackle: str
    analysis: str
    action: str
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


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    region: str
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
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.sound: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.sound = self.sound
        return clone


def _sound_crackle(world: World) -> list[str]:
    out: list[str] = []
    pot = world.entities.get("pot")
    if not pot:
        return out
    if pot.meters.get("low_water", 0) < THRESHOLD:
        return out
    sig = ("crackle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.sound = "crackle"
    pot.meters["crackle"] = 1
    out.append("The little pot made a sharp crackle.")
    return out


def _heat_problem(world: World) -> list[str]:
    out: list[str] = []
    pot = world.entities.get("pot")
    if not pot:
        return out
    if pot.meters.get("low_water", 0) < THRESHOLD:
        return out
    sig = ("problem",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot.memes["worry"] += 1
    out.append("That meant the tea was not quite safe yet.")
    return out


def _fix_restore(world: World) -> list[str]:
    out: list[str] = []
    pot = world.entities.get("pot")
    child = world.entities.get("child")
    if not pot or not child:
        return out
    if not pot.meters.get("fixed", 0) >= THRESHOLD:
        return out
    sig = ("restore",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot.meters["crackle"] = 0
    pot.memes["worry"] = 0
    child.memes["pride"] += 1
    out.append("After that, the kitchen felt calm again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_sound_crackle, _heat_problem, _fix_restore):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_fix(world: World, action: str) -> bool:
    sim = world.copy()
    pot = sim.get("pot")
    if action == "add_water":
        pot.meters["low_water"] = 0
        pot.meters["fixed"] = 1
    elif action == "ask_help":
        pot.memes["worry"] += 0
    propagate(sim, narrate=False)
    return sim.entities["pot"].meters.get("crackle", 0) == 0 and sim.entities["pot"].meters.get("fixed", 0) >= THRESHOLD


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"tea"}),
    "sunroom": Setting(place="the sunroom", affords={"tea"}),
}

CAUSES = {
    "low_water": Cause(
        id="low_water",
        label="low water",
        clue="the pot crackled because the water level was too low",
        fix="add more water",
        crackle="crackle",
        analysis="analysis",
        action="refill the pot",
        tags={"tea", "water", "crackle"},
    )
}

OBJECTS = {
    "teacup": ObjectCfg(
        id="teacup",
        label="teacup",
        phrase="a blue teacup with tiny stars",
        region="hand",
    ),
    "kettle": ObjectCfg(
        id="kettle",
        label="kettle",
        phrase="a small silver kettle",
        region="hand",
    ),
}

TOOLS = {
    "water": Tool(
        id="water",
        label="water",
        prep="carefully pour in a little more water",
        tail="poured in a little more water",
        helps="it gave the hot bottom something safe to warm",
        tags={"water", "tea"},
    ),
    "mitt": Tool(
        id="mitt",
        label="oven mitt",
        prep="use an oven mitt and check the handle",
        tail="used an oven mitt to hold the pot",
        helps="it kept the hand safe",
        tags={"safety"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Ada", "Elena"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Noah", "Milo", "Eli"]
TRAITS = ["curious", "gentle", "careful", "kind", "patient", "helpful"]


@dataclass
class StoryParams:
    place: str
    cause: str
    object: str
    name: str
    gender: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, o) for p in SETTINGS for c in CAUSES for o in OBJECTS]


def explain_rejection(place: str, cause: str, obj: str) -> str:
    return f"(No story: this domain only supports a cozy {place} tea problem with {cause} and a {obj}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming story world about crackle, analysis, and a helpful fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa"])
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
    if getattr(args, "place", None) and getattr(args, "cause", None) and getattr(args, "object", None):
        if (getattr(args, "place", None), getattr(args, "cause", None), getattr(args, "object", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    cause = getattr(args, "cause", None) or rng.choice(list(CAUSES))
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandma", "grandpa"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, cause=cause, object=obj, name=name, gender=gender, helper=helper, trait=trait)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name, traits=[params.trait, "kind"]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    pot = world.add(Entity(id="pot", type="kettle", label="little pot", phrase="a little pot for tea"))
    cup = world.add(Entity(id="cup", type="thing", label="teacup", phrase=_safe_lookup(OBJECTS, params.object).phrase))
    world.facts = {"child": child, "helper": helper, "pot": pot, "cup": cup, "params": params}
    return world


def tell_story(world: World, params: StoryParams) -> World:
    child = world.get("child")
    helper = world.get("helper")
    pot = world.get("pot")
    pot.meters["low_water"] = 1
    pot.memes["worry"] = 0

    world.say(f"{child.label} was a {params.trait} little {params.gender} who loved helping in {world.setting.place}.")
    world.say(f"{helper.label.capitalize()} was making tea when the pot began to {_safe_lookup(CAUSES, params.cause).crackle}.")
    world.say(f"{child.label} noticed the sound right away and listened with careful {_safe_lookup(CAUSES, params.cause).analysis}.")
    world.para()
    world.say(f'"That crackle means something," {child.label} said, looking at the pot instead of guessing.')
    world.say(f"{child.label} thought about the clues, asked {helper.label} a few questions, and found the problem: the pot was too low on water.")
    world.say(f"With a small nod, {child.label} chose to {TOOLS['water'].prep}.")
    pot.meters["fixed"] = 1
    pot.meters["low_water"] = 0
    propagate(world, narrate=True)
    world.para()
    world.say(f"Then {helper.label} smiled and thanked {child.label} for the calm {_safe_lookup(CAUSES, params.cause).analysis} and kind {_safe_lookup(CAUSES, params.cause).action}.")
    world.say(f"Soon the tea was ready, the crackle was gone, and {child.label} sat beside {helper.label} with a warm cup and a proud heart.")
    child.memes["joy"] = 1
    child.memes["pride"] = 1
    helper.memes["love"] = 1
    world.facts.update({"resolved": True, "cause": params.cause, "sound": "crackle"})
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short heartwarming story for a small child about a {p.trait} child, a {_safe_lookup(CAUSES, p.cause).crackle}, and a helpful {_safe_lookup(CAUSES, p.cause).analysis}.',
        f"Tell a gentle story where {p.name} hears a {_safe_lookup(CAUSES, p.cause).crackle} in {world.setting.place} and solves the problem kindly.",
        f'Write a simple story that includes the words "crackle" and "analysis" and ends with tea, relief, and a warm smile.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    child = _safe_fact(world, world.facts, "child")
    helper = _safe_fact(world, world.facts, "helper")
    return [
        QAItem(
            question=f"What did {child.label} hear in {world.setting.place}?",
            answer=f"{child.label} heard a little crackle from the pot while tea was being made.",
        ),
        QAItem(
            question=f"How did {child.label} figure out what was wrong?",
            answer=f"{child.label} listened carefully, did a calm analysis, and noticed the pot had too little water.",
        ),
        QAItem(
            question=f"What did {child.label} do to help {helper.label}?",
            answer=f"{child.label} helped by adding more water so the pot could warm safely and the tea could finish.",
        ),
        QAItem(
            question=f"Why was this story heartwarming?",
            answer=f"It was heartwarming because {child.label} stayed calm, helped kindly, and made things better for {helper.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does crackle usually sound like?",
            answer="Crackle is a sharp, popping sound, like a tiny series of snaps.",
        ),
        QAItem(
            question="What is analysis?",
            answer="Analysis means looking at clues carefully and thinking about what they mean.",
        ),
        QAItem(
            question="Why is it good to ask for help when something seems wrong?",
            answer="Asking for help can keep people safe and often helps solve the problem faster.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:6} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place,Cause,Object) :- place(Place), cause(Cause), object(Object).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CAUSES:
        lines.append(asp.fact("cause", c))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world, params)
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
    StoryParams(place="kitchen", cause="low_water", object="teacup", name="Mina", gender="girl", helper="grandma", trait="careful"),
    StoryParams(place="sunroom", cause="low_water", object="kettle", name="Owen", gender="boy", helper="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
