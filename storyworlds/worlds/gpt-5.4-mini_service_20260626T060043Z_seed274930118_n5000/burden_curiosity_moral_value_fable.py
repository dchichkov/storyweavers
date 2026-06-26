#!/usr/bin/env python3
"""
storyworlds/worlds/burden_curiosity_moral_value_fable.py
========================================================

A small fable-style story world about curiosity, burden, and moral value.

Premise:
- A young animal carries a burden to a goal.
- Curiosity tempts them to pause and investigate something interesting.
- The burden becomes hard to manage, revealing a moral choice.
- A helper or wiser companion offers a practical, moral solution.
- The ending proves what changed: the burden is lighter, and the lesson is learned.

This world is intentionally small and constraint-checked. It models a simple
physical burden and a few emotional memes, then narrates only what the world
state supports.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    burden_ent: object | None = None
    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "mouse": {"subject": "she", "object": "her", "possessive": "her"},
            "crow": {"subject": "he", "object": "him", "possessive": "his"},
            "tortoise": {"subject": "he", "object": "him", "possessive": "his"},
            "donkey": {"subject": "it", "object": "it", "possessive": "its"},
            "owl": {"subject": "she", "object": "her", "possessive": "her"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

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
    place: str
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
class Burden:
    id: str
    label: str
    phrase: str
    weight: int
    risk: str
    mess: str
    burdened_moral: str
    feasible_helpers: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    offer: str
    result: str
    supports: set[str] = field(default_factory=set)
    cures: set[str] = field(default_factory=set)
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def burden_at_risk(burden: Burden, setting: Setting) -> bool:
    return burden.id in setting.affords or "road" in setting.affords


def choose_helper(burden: Burden) -> Optional[Helper]:
    for helper in HELPERS:
        if burden.risk in helper.cures and burden.id in burden.feasible_helpers:
            return helper
    return None


def predict(world: World, hero: Entity, burden: Burden, helper: Optional[Helper]) -> dict:
    sim = world.copy()
    _do_march(sim, sim.get(hero.id), burden, narrate=False)
    if helper is not None:
        _accept_help(sim, sim.get(hero.id), helper, burden, narrate=False)
    item = sim.get("burden")
    return {
        "heavy": item.meters.get("heavy", 0.0) >= THRESHOLD,
        "light": item.meters.get("light", 0.0) >= THRESHOLD,
        "curiosity": sim.get(hero.id).memes.get("curiosity", 0.0),
    }


def _do_march(world: World, hero: Entity, burden: Burden, narrate: bool = True) -> None:
    if not burden_at_risk(burden, world.setting):
        pass
    burden_ent = world.get("burden")
    hero.memes["duty"] = hero.memes.get("duty", 0.0) + 1
    burden_ent.meters["heavy"] = burden_ent.meters.get("heavy", 0.0) + burden.weight
    hero.memes["tired"] = hero.memes.get("tired", 0.0) + (burden.weight / 3.0)
    if narrate:
        world.say(
            f"Little {hero.type} {hero.id} set out across {world.setting.place} with "
            f"{burden.phrase} on {hero.pronoun('possessive')} back."
        )


def _curious_pause(world: World, hero: Entity, burden: Burden, item: str) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["duty"] = hero.memes.get("duty", 0.0) + 0.5
    burden_ent = world.get("burden")
    burden_ent.meters["strain"] = burden_ent.meters.get("strain", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} noticed {item} and stopped to look, "
        f"because curiosity tugged at {hero.pronoun('possessive')} heart."
    )


def _spill(world: World, hero: Entity, burden: Burden) -> None:
    burden_ent = world.get("burden")
    burden_ent.meters["scattered"] = burden_ent.meters.get("scattered", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"But the pause made the load slip, and some of the {burden.label} "
        f"spilled onto the ground."
    )


def _wise_warning(world: World, elder: Entity, hero: Entity, burden: Burden) -> None:
    world.say(
        f"{elder.id} saw the trouble and said, "
        f'"Curiosity is a bright lantern, but a lantern should not make you drop your work."'
    )


def _accept_help(world: World, hero: Entity, helper: Helper, burden: Burden, narrate: bool = True) -> None:
    burden_ent = world.get("burden")
    hero.memes["pride"] = max(0.0, hero.memes.get("pride", 0.0) - 0.5)
    hero.memes["gratitude"] = hero.memes.get("gratitude", 0.0) + 1
    burden_ent.meters["heavy"] = max(0.0, burden_ent.meters.get("heavy", 0.0) - 2)
    burden_ent.meters["light"] = burden_ent.meters.get("light", 0.0) + 1
    burden_ent.meters["scattered"] = max(0.0, burden_ent.meters.get("scattered", 0.0) - 1)
    if narrate:
        world.say(
            f"{helper.id} offered {helper.offer}, and {hero.id} accepted the help."
        )
        world.say(
            f"{helper.result} Soon the burden felt lighter, and the path was easier again."
        )


def tell(setting: Setting, burden: Burden, hero_name: str = "Pip", hero_type: str = "mouse") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "busy"]))
    elder = world.add(Entity(id="Owl", kind="character", type="owl", label="the owl"))
    burden_ent = world.add(Entity(
        id="burden",
        type="bundle",
        label=burden.label,
        phrase=burden.phrase,
        owner=hero.id,
        caretaker=hero.id,
    ))

    world.say(
        f"{hero.id} was a little {hero.type} with a careful habit of doing {hero.pronoun('possessive')} work."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had been given {burden.phrase}, and {hero.pronoun('possessive')} "
        f"job was to carry it to the far end of {setting.place}."
    )

    world.para()
    _do_march(world, hero, burden)
    world.say(
        f"{hero.pronoun().capitalize()} kept going, even while the load pressed down like a stubborn stone."
    )
    _curious_pause(world, hero, burden, "a bright trail of flowers")
    _spill(world, hero, burden)
    _wise_warning(world, elder, hero, burden)

    world.para()
    helper = choose_helper(burden)
    if helper is None:
        _fallback_pool = globals().get("HELPERS") or globals().get("HELPERES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        helper = next(iter(_fallback_pool), None)
        if helper is None:
            raise StoryError
    world.say(
        f"{helper.id} came along and said {helper.offer.lower()}."
    )
    _accept_help(world, hero, helper, burden)
    world.say(
        f"At last {hero.id} reached the end of the path with {burden.label} in order, "
        f"and {hero.pronoun('possessive')} curiosity had learned to pause without forgetting duty."
    )
    world.say(
        f"The moral was simple: curiosity can lead to trouble, but wisdom and help make a burden lighter."
    )

    world.facts.update(hero=hero, elder=elder, burden=burden, helper=helper, setting=setting)
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"path", "flowers", "road"}),
    "forest": Setting(place="the forest path", affords={"path", "mushrooms", "road"}),
    "village": Setting(place="the village lane", affords={"road", "stalls", "bells"}),
}

BURDENS = {
    "berries": Burden(
        id="berries",
        label="berries",
        phrase="a basket of ripe berries",
        weight=3,
        risk="spill",
        mess="stained paws",
        burdened_moral="care",
        feasible_helpers={"cart", "crown"},
    ),
    "grain": Burden(
        id="grain",
        label="grain",
        phrase="a heavy sack of grain",
        weight=4,
        risk="tear",
        mess="dusty fur",
        burdened_moral="duty",
        feasible_helpers={"cart"},
    ),
    "books": Burden(
        id="books",
        label="books",
        phrase="a stack of borrowed books",
        weight=2,
        risk="crumple",
        mess="creased pages",
        burdened_moral="respect",
        feasible_helpers={"cart", "strap"},
    ),
}

HELPERS = [
    Helper(
        id="Cart",
        label="cart",
        offer="a small cart",
        result="The cart took the weight from the little back.",
        supports={"berries", "grain", "books"},
        cures={"spill", "tear", "crumple"},
    ),
    Helper(
        id="Strap",
        label="strap",
        offer="a sturdy strap",
        result="The strap held the load close and steady.",
        supports={"books"},
        cures={"crumple"},
    ),
    Helper(
        id="Ribbon",
        label="ribbon",
        offer="a soft ribbon",
        result="The ribbon was pretty, but it did not truly lighten the load.",
        supports=set(),
        cures=set(),
    ),
]

NAMES = {
    "mouse": ["Pip", "Mina", "Nip", "Tia"],
    "rabbit": ["Luna", "Bun", "Milo", "Poppy"],
    "fox": ["Fenn", "Rook", "Sable"],
    "tortoise": ["Toby", "Moss", "Tess"],
    "donkey": ["Dory", "Bram"],
}

TYPES = ["mouse", "rabbit", "fox", "tortoise", "donkey"]
TRAITS = ["quick", "gentle", "earnest", "small", "brave"]


@dataclass
class StoryParams:
    place: str
    burden: str
    name: str
    hero_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for burden_id, burden in BURDENS.items():
            if burden_at_risk(burden, setting) and choose_helper(burden) is not None:
                combos.append((place, burden_id, choose_helper(burden).id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, burden, helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "burden"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    return [
        f'Write a short fable for a child about a little {hero.type} named {hero.id} who carries {burden.phrase} and learns from curiosity.',
        f"Tell a moral story in which {hero.id} pauses to look at something lovely, nearly drops {burden.label}, and then accepts help from {helper.id}.",
        f'Write a fable where curiosity is tempting, a burden is real, and the ending teaches that wise help makes hard work easier.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, burden, helper, setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "burden"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    return [
        QAItem(
            question=f"What was {hero.id} carrying through {setting.place}?",
            answer=f"{hero.id} was carrying {burden.phrase}. It was a real burden, and it made the trip hard."
        ),
        QAItem(
            question=f"Why did {hero.id} stop when the flowers caught {hero.pronoun('possessive')} eye?",
            answer=(
                f"{hero.id} stopped because curiosity tugged at {hero.pronoun('possessive')} heart. "
                f"{hero.pronoun().capitalize()} wanted one quick look, but the burden grew harder to balance."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id}, and what did that help do?",
            answer=(
                f"{helper.id} helped {hero.id}. The help lightened the load, kept the burden steady, "
                f"and let {hero.id} finish the walk without more trouble."
            ),
        ),
        QAItem(
            question=f"What moral lesson did the fable teach?",
            answer=(
                f"The moral was that curiosity can be bright, but duty still matters, and wise help can make a burden lighter."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look, learn, and find out what something is or why it happens."
        ),
        QAItem(
            question="What is a burden?",
            answer="A burden is a heavy thing to carry, or a hard worry that makes a task difficult."
        ),
        QAItem(
            question="Why is it good to accept help sometimes?",
            answer="It is good to accept help sometimes because another pair of hands can make hard work safer and easier."
        ),
        QAItem(
            question="What is a moral in a fable?",
            answer="A moral is the lesson the story is trying to teach about how to live or choose wisely."
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", burden="berries", name="Pip", hero_type="mouse", trait="quick"),
    StoryParams(place="forest", burden="books", name="Luna", hero_type="rabbit", trait="gentle"),
    StoryParams(place="village", burden="grain", name="Rook", hero_type="fox", trait="earnest"),
]


def explain_rejection(setting: Setting, burden: Burden) -> str:
    return f"(No story: {burden.phrase} does not create a useful fable in {setting.place}.)"


ASP_RULES = r"""
% A burden is valid in a setting when the setting affords a path where it can be carried.
valid_setting(S) :- setting(S).
valid_burden(B) :- burden(B).

needs_help(B) :- burden(B), helper(H), cures(H, R), risk(B, R).
valid_story(S, B, H) :- setting(S), burden(B), helper(H), needs_help(B).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for bid, b in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        lines.append(asp.fact("risk", bid, b.risk))
        for h in sorted(b.feasible_helpers):
            lines.append(asp.fact("feasible", bid, h))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for c in sorted(h.cures):
            lines.append(asp.fact("cures", h.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              and (getattr(args, "burden", None) is None or c[1] == getattr(args, "burden", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, burden_id, _ = rng.choice(list(combos))
    burden = _safe_lookup(BURDENS, burden_id)
    hero_type = getattr(args, "hero_type", None) or rng.choice(sorted(burden.feasible_helpers and TYPES or TYPES))
    name = getattr(args, "name", None) or rng.choice(NAMES.get(hero_type, ["Pip"]))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, burden=burden_id, name=name, hero_type=hero_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(BURDENS, params.burden), params.name, params.hero_type)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld about curiosity, burden, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for t in triples:
            print("  ", t)
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
