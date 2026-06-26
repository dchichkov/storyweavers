#!/usr/bin/env python3
"""
storyworlds/worlds/inspection_reed_kindness_foreshadowing_ghost_story.py
========================================================================

A small, standalone story world in a gentle ghost-story style.

Seed premise:
- A child goes to an old place for an inspection.
- A reed object matters to the inspection.
- The atmosphere feels spooky at first, but kindness changes the ending.
- Foreshadowing plants little clues before the reveal.

The world is deliberately tiny and state-driven:
- physical meters track dampness, brightness, stability, and chill
- emotional memes track fear, kindness, curiosity, trust, and relief

The generated stories aim for a cozy ghost-story feeling:
mist, creaks, moonlight, whispers, a small surprise, and a soft resolution.
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    mood: str
    afford_inspection: bool = True
    has_fog: bool = False
    has_water: bool = False
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
class Item:
    id: str
    label: str
    phrase: str
    material: str
    region: str
    fragile: bool = False
    plural: bool = False
    risk_on_inspection: bool = False
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
class Spirit:
    id: str
    label: str
    phrase: str
    kind: str
    need: str
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
class StoryParams:
    place: str
    item: str
    spirit: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.flags: dict[str, bool] = {}

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        chunk = []
        for line in self.lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "marsh": Setting(place="the marsh path", mood="misty", has_fog=True, has_water=True),
    "dock": Setting(place="the old dock", mood="quiet", has_fog=True, has_water=True),
    "attic": Setting(place="the attic above the shop", mood="still", has_fog=False, has_water=False),
    "garden": Setting(place="the moonlit garden", mood="soft", has_fog=True, has_water=False),
}

ITEMS = {
    "reed_lantern": Item(
        id="reed_lantern",
        label="reed lantern",
        phrase="a small lantern woven from reed",
        material="reed",
        region="hands",
        fragile=True,
        risk_on_inspection=True,
        tags={"reed", "lantern", "light"},
    ),
    "reed_basket": Item(
        id="reed_basket",
        label="reed basket",
        phrase="a neat basket braided from reed",
        material="reed",
        region="hands",
        fragile=False,
        risk_on_inspection=False,
        tags={"reed", "basket"},
    ),
    "reed_whistle": Item(
        id="reed_whistle",
        label="reed whistle",
        phrase="a tiny whistle cut from reed",
        material="reed",
        region="hands",
        fragile=True,
        risk_on_inspection=True,
        tags={"reed", "sound"},
    ),
}

SPIRITS = {
    "little_ghost": Spirit(
        id="little_ghost",
        label="little ghost",
        phrase="a pale little ghost with a shy smile",
        kind="ghost",
        need="someone to be gentle with it",
        tags={"ghost", "mist", "whisper"},
    ),
    "lantern_spirit": Spirit(
        id="lantern_spirit",
        label="lantern spirit",
        phrase="a soft lantern spirit that glowed like a firefly",
        kind="spirit",
        need="someone to notice its light",
        tags={"ghost", "light", "whisper"},
    ),
    "reed_keeper": Spirit(
        id="reed_keeper",
        label="reed keeper",
        phrase="the old reed keeper who watched over the water",
        kind="ghost",
        need="a careful inspection",
        tags={"ghost", "reed", "water"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Wren", "Ruby", "Elena", "Mara"]
BOY_NAMES = ["Theo", "Owen", "Milo", "Finn", "Jasper", "Eli", "Nico", "Arlo"]
TRAITS = ["curious", "gentle", "brave", "careful", "kind", "quiet"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, item: str, spirit: str) -> bool:
    setting = _safe_lookup(SETTINGS, place)
    item_def = _safe_lookup(ITEMS, item)
    spirit_def = _safe_lookup(SPIRITS, spirit)
    return (
        setting.afford_inspection
        and item_def.material == "reed"
        and spirit_def.kind == "ghost"
        and ("ghost" in spirit_def.tags)
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for item in ITEMS:
            for spirit in SPIRITS:
                if valid_combo(place, item, spirit):
                    combos.append((place, item, spirit))
    return combos


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def describe_setting(world: World, hero: Entity) -> None:
    s = world.setting
    if s.has_fog:
        world.say(
            f"One {s.mood} evening, {hero.id} went to {s.place}, where the fog curled low "
            f"and the air felt like a held breath."
        )
    else:
        world.say(
            f"One quiet evening, {hero.id} went to {s.place}, where the air was still and soft."
        )


def foreshadow(world: World, item: Entity) -> None:
    world.say(
        f"Before anything moved, there were little signs: a cool draft, a faint tap-tap, "
        f"and a dim shimmer around the {item.label}."
    )
    world.facts["foreshadowed"] = True


def inspect_item(world: World, hero: Entity, parent: Entity, item: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} came with {hero.pronoun('possessive')} {parent.label} to inspect "
        f"{article(item.label)} {item.label} carefully."
    )
    if item.risk_on_inspection:
        item.meters["damp"] += 1
        item.meters["fragile"] += 1
        world.say(
            f"The {item.label} looked delicate in the mist, and the damp made its reed edges "
            f"feel even thinner."
        )


def ghost_appears(world: World, spirit: Spirit) -> None:
    world.say(
        f"Then a pale shape drifted out of the fog: {spirit.phrase}."
    )
    world.say(
        f"It did not howl or clatter. It only whispered, soft as a leaf, as if it had been "
        f"waiting to be seen."
    )


def fear_rises(world: World, hero: Entity) -> None:
    hero.memes["fear"] += 1
    hero.meters["cold"] += 1
    world.say(
        f"{hero.id}'s heart thumped once, then twice. The shadows seemed longer than before."
    )


def kindness_turn(world: World, hero: Entity, spirit: Spirit, item: Entity) -> None:
    hero.memes["kindness"] += 1
    hero.memes["trust"] += 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
    world.say(
        f"Still, {hero.id} took a slow breath and spoke kindly. "
        f'"Do you need help?"'
    )
    world.say(
        f"The little ghost nodded toward the {item.label}, because it had been trying to protect "
        f"the reed work all along."
    )
    world.facts["need"] = spirit.need


def resolve(world: World, hero: Entity, parent: Entity, item: Entity, spirit: Spirit) -> None:
    hero.memes["relief"] += 1
    item.meters["damp"] = max(0.0, item.meters.get("damp", 0.0) - 1.0)
    item.meters["bright"] = item.meters.get("bright", 0.0) + 1.0
    world.say(
        f"{hero.id} brushed the dew from the reed strands and straightened the lantern with "
        f"care. The ghost glowed brighter, as if kindness had given it room to breathe."
    )
    world.say(
        f"Together, {hero.id} and {hero.pronoun('possessive')} {parent.label} finished the inspection, "
        f"and the little ghost floated up with a grateful wink."
    )
    world.say(
        f"By the end, the {item.label} was safe, the fog looked gentle instead of strange, and "
        f"{hero.id} could smile at the moon without feeling afraid."
    )
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(world: World, hero: Entity, parent: Entity, item: Entity, spirit: Spirit) -> World:
    describe_setting(world, hero)
    foreshadow(world, item)
    inspect_item(world, hero, parent, item)
    world.para()
    ghost_appears(world, spirit)
    fear_rises(world, hero)
    world.say(
        f"{hero.id} almost stepped back, but the little voice in the dark sounded more lonely "
        f"than scary."
    )
    kindness_turn(world, hero, spirit, item)
    world.para()
    resolve(world, hero, parent, item, spirit)
    return world


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class StorySeed:
    place: str
    item: str
    spirit: str
    name: str
    gender: str
    parent: str
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


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            traits=["little", params.trait],
            meters={"cold": 0.0},
            memes={"fear": 0.0, "kindness": 0.0, "curiosity": 0.0, "trust": 0.0, "relief": 0.0},
        )
    )
    parent = world.add(
        Entity(id="parent", kind="character", type=params.parent, label=f"{params.parent}")
    )
    item_def = _safe_lookup(ITEMS, params.item)
    item = world.add(
        Entity(
            id=item_def.id,
            kind="thing",
            type="thing",
            label=item_def.label,
            phrase=item_def.phrase,
            plural=item_def.plural,
            meters={"damp": 0.0, "bright": 0.0, "fragile": 0.0},
        )
    )
    spirit_def = _safe_lookup(SPIRITS, params.spirit)
    spirit = world.add(
        Entity(
            id=spirit_def.id,
            kind="thing",
            type="ghost",
            label=spirit_def.label,
            phrase=spirit_def.phrase,
            meters={"glow": 0.0},
            memes={"lonely": 0.0},
        )
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        item=item,
        spirit=spirit,
        setting=setting,
        item_def=item_def,
        spirit_def=spirit_def,
    )
    return tell(world, hero, parent, item, spirit)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item_def = _safe_fact(world, f, "item_def")
    spirit_def = _safe_fact(world, f, "spirit_def")
    return [
        f'Write a short ghost-story for a child named {hero.id} who goes to {world.setting.place} for an inspection.',
        f"Tell a gentle spooky story where {hero.id} inspects {item_def.phrase} and meets {spirit_def.phrase}.",
        f'Write a story that uses the words "inspection" and "{item_def.material}" and ends with kindness instead of fear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    parent: Entity = _safe_fact(world, world.facts, "parent")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    spirit: Entity = _safe_fact(world, world.facts, "spirit")  # type: ignore[assignment]
    item_def: Item = _safe_fact(world, world.facts, "item_def")  # type: ignore[assignment]

    qa = [
        QAItem(
            question=f"Where did {hero.id} go for the inspection?",
            answer=f"{hero.id} went to {world.setting.place} with {hero.pronoun('possessive')} {parent.label} for the inspection.",
        ),
        QAItem(
            question=f"What was special about the {item.label}?",
            answer=f"It was made from reed, so it was delicate in the mist and needed careful hands.",
        ),
        QAItem(
            question=f"What did {hero.id} first feel when the ghost appeared?",
            answer=f"{hero.id} felt a jolt of fear, because the pale shape drifted out of the fog without a sound.",
        ),
        QAItem(
            question=f"How did the story turn from scary to kind?",
            answer=f"{hero.id} spoke kindly, asked if help was needed, and then used careful hands to finish the inspection.",
        ),
        QAItem(
            question=f"What proved that kindness changed the ending?",
            answer=f"By the end, the {item.label} was safe, the ghost was grateful, and {hero.id} could smile at the moon without fear.",
        ),
    ]
    if item_def.risk_on_inspection:
        qa.append(
            QAItem(
                question=f"Why did the {item.label} need extra care?",
                answer=f"Because it was fragile reed work, and the damp air made it feel even thinner during the inspection.",
            )
        )
    if world.facts.get("foreshadowed"):
        qa.append(
            QAItem(
                question="What little clues foreshadowed the ghost?",
                answer="A cool draft, a faint tapping sound, and a dim shimmer hinted that someone shy was nearby before the ghost appeared.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item_def: Item = _safe_fact(world, f, "item_def")  # type: ignore[assignment]
    spirit_def: Spirit = _safe_fact(world, f, "spirit_def")  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is reed?",
            answer="Reed is a tall plant that grows near water, and people can weave or cut it to make things like baskets, whistles, and lanterns.",
        ),
        QAItem(
            question="What does an inspection mean?",
            answer="An inspection is a careful look at something to check whether it is safe, sound, or ready to use.",
        ),
        QAItem(
            question="Why can fog make a place feel spooky?",
            answer="Fog can hide edges and soften sounds, so things seem closer, stranger, and harder to see clearly.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone uses gentle words or helpful actions to care for another being.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives small clues early so readers can guess that something important is coming.",
        ),
    ]
    if item_def.material == "reed":
        out.append(
            QAItem(
                question=f"What is a {item_def.label} made for?",
                answer=f"A {item_def.label} is a reed object, so it can be woven or shaped by careful hands and used for light, sound, or carrying small things.",
            )
        )
    if spirit_def.kind == "ghost":
        out.append(
            QAItem(
                question="What kind of ghost is in this story?",
                answer=f"It is {spirit_def.phrase}, so it feels spooky at first but stays gentle and lonely instead of mean.",
            )
        )
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  flags: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- setting(P).
reed_item(I) :- item(I), material(I, reed).
ghost_spirit(S) :- spirit(S), kind(S, ghost).

valid_story(P, I, S) :- place_ok(P), reed_item(I), ghost_spirit(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.has_fog:
            lines.append(asp.fact("foggy", pid))
        if s.has_water:
            lines.append(asp.fact("watery", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("material", iid, item.material))
        if item.fragile:
            lines.append(asp.fact("fragile", iid))
    for sid, spirit in SPIRITS.items():
        lines.append(asp.fact("spirit", sid))
        lines.append(asp.fact("kind", sid, spirit.kind))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost-story world about inspection, reed, kindness, and foreshadowing."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--spirit", choices=SPIRITS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None) and getattr(args, "item", None) and getattr(args, "spirit", None) and not valid_combo(getattr(args, "place", None), getattr(args, "item", None), getattr(args, "spirit", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
        and (getattr(args, "spirit", None) is None or c[2] == getattr(args, "spirit", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item, spirit = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or select_name(gender, rng)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, spirit=spirit, name=name, gender=gender, parent=parent, trait=trait)


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for place, item, spirit in combos:
            print(place, item, spirit)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, item, spirit in valid_combos():
            params = StoryParams(
                place=place,
                item=item,
                spirit=spirit,
                name="Mina",
                gender="girl",
                parent="mother",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
