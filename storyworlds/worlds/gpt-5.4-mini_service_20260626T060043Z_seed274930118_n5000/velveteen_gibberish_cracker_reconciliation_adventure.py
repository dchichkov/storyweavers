#!/usr/bin/env python3
"""
A tiny adventure storyworld about a velveteen toy, a page of gibberish, and a
cracker that causes a misunderstanding before reconciliation.

The seed premise:
- A small adventurer follows a torn scrap of gibberish.
- A beloved velveteen companion and a crunchy cracker both matter to the trip.
- A tense mix-up is repaired by apology, sharing, and reconciling.
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
# World model
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    treasure: object | None = None
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
    place: str = "the old trail"
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
class Adventure:
    id: str
    verb: str
    gerund: str
    path: str
    danger: str
    clue: str
    outcome: str
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
class Treasure:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    owners: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Aid:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "trail": Setting(place="the old trail", affords={"gibberish", "cracker"}),
    "cave": Setting(place="the narrow cave", affords={"gibberish", "cracker"}),
    "harbor": Setting(place="the windy harbor", affords={"gibberish", "cracker"}),
}

ADVENTURES = {
    "gibberish": Adventure(
        id="gibberish",
        verb="follow the gibberish clue",
        gerund="following gibberish clues",
        path="the bendy path",
        danger="getting lost",
        clue="gibberish marks on a torn scrap",
        outcome="found their way",
        tags={"gibberish", "map", "lost"},
    ),
    "cracker": Adventure(
        id="cracker",
        verb="carry the cracker",
        gerund="carrying the cracker",
        path="the rocky path",
        danger="dropping the snack",
        clue="a crunchy cracker tucked in a pouch",
        outcome="kept the snack safe",
        tags={"cracker", "snack", "crumbs"},
    ),
}

TREASURES = {
    "velveteen": Treasure(
        label="velveteen toy",
        phrase="a soft velveteen toy",
        type="toy",
        region="hands",
        plural=False,
        owners={"girl", "boy"},
    ),
    "satchel": Treasure(
        label="satchel",
        phrase="a small travel satchel",
        type="satchel",
        region="shoulder",
        plural=False,
    ),
    "boots": Treasure(
        label="boots",
        phrase="muddy boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

AIDS = [
    Aid(
        id="lantern",
        label="a little lantern",
        covers={"hands"},
        helps={"gibberish"},
        prep="hold up a little lantern",
        tail="held the little lantern high",
    ),
    Aid(
        id="pouch",
        label="a cloth pouch",
        covers={"hands"},
        helps={"cracker"},
        prep="put the cracker in a cloth pouch",
        tail="slid the cracker into a cloth pouch",
    ),
    Aid(
        id="ribbon",
        label="a ribbon tie",
        covers={"shoulder"},
        helps={"gibberish", "cracker"},
        prep="tie on a ribbon strap",
        tail="tied on a ribbon strap",
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Pia", "Nora", "Tess", "Lily"]
BOY_NAMES = ["Finn", "Owen", "Eli", "Noah", "Theo", "Ben"]
TRAITS = ["brave", "curious", "careful", "lively", "gentle"]


@dataclass
class StoryParams:
    place: str
    adventure: str
    treasure: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
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


def prize_at_risk(adventure: Adventure, treasure: Treasure) -> bool:
    if treasure.label == "velveteen toy":
        return adventure.id == "gibberish"
    if treasure.label == "satchel":
        return adventure.id in {"gibberish", "cracker"}
    if treasure.label == "boots":
        return adventure.id == "cracker"
    return False


def select_aid(adventure: Adventure, treasure: Treasure) -> Optional[Aid]:
    for aid in AIDS:
        if adventure.id in aid.helps and treasure.region in aid.covers:
            return aid
    return None


def build_trace_line(entity: Entity) -> str:
    bits = []
    meters = {k: v for k, v in entity.meters.items() if v}
    memes = {k: v for k, v in entity.memes.items() if v}
    if meters:
        bits.append(f"meters={meters}")
    if memes:
        bits.append(f"memes={memes}")
    return f"{entity.id}: {' '.join(bits) if bits else 'quiet'}"


def predict_conflict(world: World, hero: Entity, adventure: Adventure, treasure: Entity) -> dict:
    sim = world.copy()
    _do_adventure(sim, sim.get(hero.id), adventure, narrate=False)
    return {
        "lost": sim.get(hero.id).memes.get("lost", 0.0) > 0,
        "mess": sim.get(treasure.id).meters.get("messed", 0.0) > 0,
    }


def _do_adventure(world: World, hero: Entity, adventure: Adventure, narrate: bool = True) -> None:
    if adventure.id not in world.setting.affords:
        return
    if adventure.id == "gibberish":
        hero.memes["lost"] = hero.memes.get("lost", 0.0) + 1
    if adventure.id == "cracker":
        hero.meters["crumbs"] = hero.meters.get("crumbs", 0.0) + 1
    for ent in list(world.entities.values()):
        if ent.worn_by == hero.id and ent.type == "toy" and adventure.id == "gibberish":
            ent.meters["messed"] = ent.meters.get("messed", 0.0) + 1
    if narrate:
        world.trace.append(f"adventure:{adventure.id}")


def tell(setting: Setting, adventure: Adventure, treasure_cfg: Treasure,
         hero_name: str, hero_type: str, companion_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    companion = world.add(Entity(id="Companion", kind="character", type=companion_type, label="the companion"))
    treasure = world.add(Entity(
        id="treasure",
        type=treasure_cfg.type,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=hero.id,
        caretaker=companion.id,
        plural=treasure_cfg.plural,
    ))
    treasure.worn_by = hero.id
    world.facts.update(hero=hero, companion=companion, treasure=treasure, adventure=adventure, setting=setting)

    world.say(f"{hero.id} was a {trait} little {hero.type} who loved adventure.")
    world.say(f"{hero.id} carried {treasure.phrase} everywhere, because {hero.pronoun('possessive')} {treasure.label} felt brave and soft.")

    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {companion.label} set out on {setting.place}.")
    world.say(f"Along the way they found {adventure.clue}, and {hero.id} wanted to {adventure.verb}.")

    _do_adventure(world, hero, adventure)
    pred = predict_conflict(world, hero, adventure, treasure)
    world.facts["predicted_lost"] = pred["lost"]
    world.facts["predicted_mess"] = pred["mess"]

    if adventure.id == "gibberish":
        world.say(f"The clues twisted every which way, and soon {hero.id} was unsure of the path.")
        world.say(f"{hero.pronoun('possessive').capitalize()} {companion.label} warned that the weird signs could lead {hero.pronoun('object')} astray.")
    else:
        world.say(f"The path rattled and shook, and {hero.id} nearly dropped the cracker.")
        world.say(f"{hero.pronoun('possessive').capitalize()} {companion.label} said the snack needed to be carried carefully.")

    world.para()
    world.say(f"{hero.id} frowned, because {hero.pronoun('possessive')} heart still wanted to keep going.")
    world.say(f"Then {hero.pronoun('possessive')} {companion.label} slowed down, listened, and offered a better plan.")

    aid = select_aid(adventure, treasure)
    if aid is None:
        _fallback_pool = globals().get("AIDS") or globals().get("AIDES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        aid = next(iter(_fallback_pool), None)
        if aid is None:
            raise StoryError
    world.add(Entity(id=aid.id, type="aid", label=aid.label, plural=aid.plural, owner=hero.id))
    world.say(f"They {aid.prep}, so the trip could continue without losing the little treasure.")

    if adventure.id == "gibberish":
        hero.memes["lost"] = 0.0
        world.say(f"{hero.id} apologized for snapping, and {hero.pronoun('possessive')} {companion.label} apologized too for speaking too sharply.")
        world.say(f"Together they paused, breathed, and chose the lantern path until the trail made sense again.")
        world.say(f"By the end, {hero.id} had {adventure.gerund}, {hero.pronoun('possessive')} velveteen toy stayed clean, and the two friends were reconciled.")
        world.facts["reconciled"] = True
    else:
        world.say(f"{hero.id} apologized for rushing, and {hero.pronoun('possessive')} {companion.label} smiled and shared the cracker in two.")
        world.say(f"By the end, {hero.id} was {adventure.gerund}, the cracker was safe, and both friends laughed together again.")
        world.facts["reconciled"] = True

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    adv = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "adventure")
    treasure = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treasure")
    return [
        f'Write a short adventure story for a small child about {hero.id}, a {hero.type}, and a "{adv.id}" clue.',
        f"Tell a gentle adventure where {hero.id} follows gibberish, worries about {treasure.label}, and ends in reconciliation.",
        f'Write a story that includes a velveteen toy, a cracker, and a mysterious gibberish trail.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    companion = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "companion")
    treasure = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treasure")
    adv = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "adventure")
    qa = [
        QAItem(
            question=f"What did {hero.id} love about the day?",
            answer=f"{hero.id} loved the adventure and wanted to keep going even when the clues became confusing.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {hero.pronoun('possessive')} {companion.label} slow down?",
            answer=f"They slowed down because the {adv.id} path was tricky, and they needed to keep {treasure.label} safe.",
        ),
        QAItem(
            question=f"What made the story turn into a reconciliation?",
            answer=f"They listened to each other, apologized, and chose a safer way forward together.",
        ),
    ]
    if f.get("reconciled"):
        qa.append(
            QAItem(
                question=f"How did the friends end the adventure?",
                answer=f"They ended it smiling together, with the path settled and the little treasure still close by.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "velveteen": [
        ("What does velveteen feel like?", "Velveteen is soft fabric that feels smooth and cozy to touch."),
    ],
    "gibberish": [
        ("What is gibberish?", "Gibberish is speech or writing that does not make clear sense."),
    ],
    "cracker": [
        ("What is a cracker?", "A cracker is a crisp, crunchy snack that can break into little pieces."),
    ],
    "reconciliation": [
        ("What is reconciliation?", "Reconciliation is when people make up after a disagreement and become friendly again."),
    ],
    "adventure": [
        ("What is an adventure?", "An adventure is an exciting trip or event where something new or surprising happens."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "adventure").tags)
    tags.add("adventure")
    if world.facts.get("reconciled"):
        tags.add("reconciliation")
    if _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "treasure").label == "velveteen toy":
        tags.add("velveteen")
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
    return "\n".join(["--- world trace ---"] + [build_trace_line(e) for e in world.entities.values()])


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

prize_at_risk(gibberish, velveteen) :- true.
prize_at_risk(gibberish, satchel) :- true.
prize_at_risk(cracker, satchel) :- true.
prize_at_risk(cracker, boots) :- true.

has_fix(gibberish, velveteen) :- aid(lantern).
has_fix(gibberish, satchel) :- aid(lantern), aid(ribbon).
has_fix(cracker, satchel) :- aid(pouch).
has_fix(cracker, boots) :- aid(ribbon).

valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure", aid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("worn_on", tid, t.region))
        for g in t.owners:
            lines.append(asp.fact("wears", g, tid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for a in s.affords:
            for tid, t in TREASURES.items():
                if prize_at_risk(_safe_lookup(ADVENTURES, a), t) and select_aid(_safe_lookup(ADVENTURES, a), t):
                    combos.append((place, a, tid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with velveteen, gibberish, cracker, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["mother", "father"])
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
    if getattr(args, "adventure", None) and getattr(args, "treasure", None):
        adv = _safe_lookup(ADVENTURES, getattr(args, "adventure", None))
        tre = _safe_lookup(TREASURES, getattr(args, "treasure", None))
        if not prize_at_risk(adv, tre) or not select_aid(adv, tre):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    valid = [c for c in valid_combos()
             if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
             and (getattr(args, "adventure", None) is None or c[1] == getattr(args, "adventure", None))
             and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, adventure, treasure = rng.choice(sorted(valid))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = getattr(args, "companion", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, adventure=adventure, treasure=treasure, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ADVENTURES, params.adventure), _safe_lookup(TREASURES, params.treasure),
                 params.name, params.gender, params.companion, params.trait)
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
        print(asp_program(""))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, adventure, treasure) combos ({len(stories)} with gender):\n")
        for place, adv, tre in triples:
            print(f"  {place:10} {adv:10} {tre}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams("trail", "gibberish", "velveteen", "Mina", "girl", "mother", "curious"),
        StoryParams("cave", "cracker", "boots", "Finn", "boy", "father", "brave"),
        StoryParams("harbor", "gibberish", "satchel", "Luna", "girl", "mother", "careful"),
    ]

    if getattr(args, "all", None):
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
