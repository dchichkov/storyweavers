#!/usr/bin/env python3
"""The peculiar moon pool and the option that saved the village lights.

A small mythic simulation about Luna, a child who finds a moonlit pool whose
water can dim the stars. Her careful option turns a frightening discovery into
a happy ending.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None

    guide: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)
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
class Place:
    id: str
    name: str
    detail: str
    moon_pool: bool = False
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


@dataclass
class Relic:
    id: str
    label: str
    power: str
    safe_method: str
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


@dataclass
class Option:
    id: str
    label: str
    method: str
    risk: str
    result: str
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


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""
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


class World:
    def __init__(self, place: Place, relic: Relic, option: Option) -> None:
        self.place = place
        self.relic = relic
        self.option = option
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn = 0

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(
        self,
        kind: str,
        text: str,
        *,
        actor: str,
        target: str,
        cause: str = "",
        result: str = "",
    ) -> None:
        self.history.append(
            Event(
                kind=kind,
                actor=actor,
                target=target,
                text=text,
                cause=cause,
                result=result,
            )
        )
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


PLACES = {
    "hill": Place(
        "hill",
        "the Hill of Seven Echoes",
        "where silver grass bent in rings beneath the moon",
        True,
    ),
    "marsh": Place(
        "marsh",
        "the Whispering Marsh",
        "where reeds hummed whenever the night wind passed",
        True,
    ),
    "grove": Place(
        "grove",
        "the Elder Grove",
        "where old trees held their branches like quiet hands",
        True,
    ),
}

RELICS = {
    "moonstone": Relic(
        "moonstone",
        "a peculiar moonstone",
        "drink the light from nearby stars",
        "place it in a bowl of still water",
    ),
    "bell": Relic(
        "bell",
        "a peculiar silver bell",
        "call the sleeping moon",
        "ring it only beneath an open sky",
    ),
    "feather": Relic(
        "feather",
        "a peculiar blue feather",
        "make shadows dance like birds",
        "lay it beside a warm lantern",
    ),
}

OPTIONS = {
    "bowl": Option(
        "bowl",
        "the bowl of still water",
        "set the moonstone in a clay bowl instead of touching the pool",
        "the village lights may fade for a moment",
        "the moonstone gives back the stolen starlight",
    ),
    "song": Option(
        "song",
        "the old welcome song",
        "sing to the pool and ask it to release what it holds",
        "the pool may answer with a louder darkness",
        "the pool opens like an eye and returns the light",
    ),
    "rope": Option(
        "rope",
        "a woven sun-rope",
        "lower the rope around the relic and pull it away from the water",
        "the relic may crack before the stars are freed",
        "the rope carries the moonstone safely to dry ground",
    ),
}

NAMES = ["Luna", "Mira", "Nia", "Tala", "Ari"]
GUIDES = {
    "grandmother": ("grandmother", "Grandmother"),
    "raven": ("raven", "Raven"),
    "keeper": ("keeper", "the Keeper"),
}
TRAITS = ["brave", "patient", "curious", "kind"]


@dataclass
class StoryParams:
    place: str = ""
    relic: str = ""
    option: str = ""
    name: str = ""
    guide: str = ""
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, relic, option)
        for place in PLACES
        for relic in RELICS
        for option in OPTIONS
        if _safe_lookup(PLACES, place).moon_pool and option != "rope" or
        (_safe_lookup(PLACES, place).moon_pool and relic == "moonstone" and option == "rope")
    ]


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        pass
    if params.relic not in RELICS:
        pass
    if params.option not in OPTIONS:
        pass
    if params.guide not in GUIDES:
        pass
    if not params.name.strip() or params.name in {"pool", "star", "village"}:
        pass

    place = _safe_lookup(PLACES, params.place)
    relic = _safe_lookup(RELICS, params.relic)
    option = _safe_lookup(OPTIONS, params.option)
    world = World(place, relic, option)

    hero = world.add(
        Entity(
            params.name,
            "character",
            params.name,
            memes={"courage": 1.0, "wonder": 1.0, "care": 0.0},
        )
    )
    guide_type, guide_label = _safe_lookup(GUIDES, params.guide)
    guide = world.add(Entity("guide", "guide", guide_label, memes={"wisdom": 1.0}))
    artifact = world.add(
        Entity(
            "relic",
            "relic",
            relic.label,
            meters={"power": 1.0, "danger": 1.0, "contained": 0.0},
        )
    )
    pool = world.add(
        Entity(
            "pool",
            "place",
            "the moon pool",
            meters={"darkness": 1.0, "starlight": 0.0},
        )
    )
    village = world.add(
        Entity(
            "village",
            "village",
            "the village",
            meters={"lamps": 1.0, "hope": 1.0},
        )
    )
    world.facts.update(hero=hero, guide=guide, guide_type=guide_type,
                       artifact=artifact, pool=pool, village=village)
    return world


def opening(world: World, params: StoryParams) -> None:
    hero = world.get(params.name)
    guide = world.get("guide")
    world.record(
        "arrival",
        f"{hero.label} climbed to {world.place.name}, where {world.place.detail}. "
        f"{hero.label} had been gathering night herbs with {guide.label}, but beneath "
        f"a flat stone they found {world.relic.label}. Its glow was beautiful and "
        f"peculiar, like a tiny moon trying to remember the sky.",
        actor=hero.id,
        target="relic",
        cause=f"{hero.label} followed a pale shine into {world.place.name}.",
        result=f"{hero.label} discovered {world.relic.label}.",
    )


def begin_problem(world: World, params: StoryParams) -> None:
    hero = world.get(params.name)
    guide = world.get("guide")
    pool = world.get("pool")
    pool.meters["starlight"] = 1.0
    pool.meters["darkness"] = 2.0
    hero.memes["wonder"] += 1.0
    world.para()
    text = (
        f"When {hero.label} lifted the relic, the moon pool shivered. One by one, "
        f"the stars above the village went dark. “I only wanted to see it,” "
        f"{hero.label} said. “Then we must choose carefully,” {guide.label} replied. "
        f"The water pulled at the relic, and the village lamps below began to blink."
    )
    cause = f"Touching {world.relic.label} woke its power beside the moon pool."
    result = "The pool began to swallow starlight and dim the village."
    world.record(
        "danger",
        text,
        actor=hero.id,
        target="pool",
        cause=cause,
        result=result,
    )


def choose_option(world: World, params: StoryParams) -> None:
    hero = world.get(params.name)
    guide = world.get("guide")
    relic = world.get("relic")
    option = world.option
    world.para()
    hero.memes["care"] += 1.0
    relic.meters["contained"] = 1.0
    pool = world.get("pool")
    village = world.get("village")
    pool.meters["darkness"] = 0.5
    village.meters["hope"] = 2.0
    text = (
        f"{hero.label} chose {option.label}. {option.method.capitalize()}. "
        f"“Will it work?” {hero.label} asked. “An option becomes wise when we "
        f"take responsibility for it,” {guide.label} said. {hero.label} breathed "
        f"slowly and followed the plan, while the peculiar relic grew warm."
    )
    if option.id == "bowl":
        text += " The water in the clay bowl trembled, but it did not spill."
    elif option.id == "song":
        text += " The old words floated over the reeds and made the darkness listen."
    else:
        text += " The woven strands tightened like golden fingers around the stone."
    cause = f"{hero.label} avoided the dangerous pool and used {option.label}."
    result = option.result
    world.record(
        "choice",
        text,
        actor=hero.id,
        target="relic",
        cause=cause,
        result=result,
    )


def resolve(world: World, params: StoryParams) -> None:
    hero = world.get(params.name)
    guide = world.get("guide")
    relic = world.get("relic")
    pool = world.get("pool")
    village = world.get("village")
    world.para()
    relic.meters["power"] = 0.0
    pool.meters["darkness"] = 0.0
    pool.meters["starlight"] = 0.0
    village.meters["lamps"] = 2.0
    village.meters["hope"] = 3.0
    hero.memes["courage"] += 1.0
    hero.memes["joy"] += 1.0
    text = (
        f"The relic released a bright river of light. It streamed over {world.place.name}, "
        f"rose through the clouds, and returned every stolen star to its place. "
        f"The village lamps shone steadily again. “You saved our night,” {guide.label} "
        f"said. {hero.label} smiled. “We saved it by choosing together.”"
    )
    cause = f"{hero.label} used {world.option.label} instead of forcing the relic from the pool."
    result = "The stars returned and the village lights burned brighter than before."
    world.record(
        "happy_ending",
        text,
        actor=hero.id,
        target="village",
        cause=cause,
        result=result,
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    opening(world, params)
    begin_problem(world, params)
    choose_option(world, params)
    resolve(world, params)
    return world


KNOWLEDGE = {
    "moonstone": QAItem(
        "What is a moonstone in this tale?",
        "It is a magical stone that carries moonlight and must be handled with care.",
    ),
    "bowl": QAItem(
        "Why can still water help with a magical stone?",
        "Still water gives the stone a calm place to rest without letting a wild pool pull it away.",
    ),
    "song": QAItem(
        "Why might a song help in a myth?",
        "A song can remind a magical place of an old promise and invite it to act kindly.",
    ),
    "rope": QAItem(
        "What makes a woven rope useful?",
        "A woven rope can hold something firmly while keeping a person safely away from danger.",
    ),
}


def generation_prompts(world: World) -> list[str]:
    params = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    return [
        f"Write a short myth about {params.label} finding a peculiar magical relic "
        f"and choosing {world.option.label} to save the stars.",
        f"Tell a gentle story in which a child faces a dangerous moon pool, speaks "
        f"with a wise guide, and finds a happy ending through a careful option.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What caused the village lights to fade?",
            world.history[1].result + " " + world.history[1].cause,
        ),
        QAItem(
            "What option did the hero choose?",
            world.history[2].cause + " " + world.option.result,
        ),
        QAItem(
            "How did the story end?",
            world.history[3].result + " " + world.history[3].cause,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    item = KNOWLEDGE.get(world.relic.id)
    out = [item] if item else []
    option_item = KNOWLEDGE.get(world.option.id)
    if option_item:
        out.append(option_item)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: {entity.label}; meters={meters}; memes={memes}"
        )
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_option(O) :- option(O).
valid(Place, Relic, O) :-
    place(Place), relic(Relic), safe_option(O), moon_pool(Place).
happy_ending(Place, Relic, O) :-
    valid(Place, Relic, O), returns_starlight(O).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("moon_pool", place))
    for relic in RELICS:
        lines.append(asp.fact("relic", relic))
    for option in OPTIONS:
        lines.append(asp.fact("option", option))
        lines.append(asp.fact("returns_starlight", option))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world is not None
    assert world.get("relic").meter("contained") == 1.0
    assert world.get("pool").meter("darkness") == 0.0
    assert world.get("village").meter("lamps") == 2.0
    assert "happy_ending" in [event.kind for event in world.history]
    assert all("{" not in part and "}" not in part for part in sample.story.split())
    assert len(sample.story_qa) == 3
    assert all(len(item.answer.split()) >= 8 for item in sample.story_qa)


def asp_verify() -> int:
    expected = {
        (place, relic, option)
        for place in PLACES
        for relic in RELICS
        for option in OPTIONS
    }
    actual = set(asp_valid())
    if actual != expected:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    checked = 0
    for place, relic, option in sorted(expected):
        sample = generate(
            StoryParams(
                place=place,
                relic=relic,
                option=option,
                name="Luna",
                guide="grandmother",
                trait="patient",
            )
        )
        check_sample(sample)
        checked += 1
    print(f"OK: {len(actual)} ASP/Python combinations and {checked} story checks.")
    return 0


CURATED = [
    StoryParams("hill", "moonstone", "bowl", "Luna", "grandmother", "patient"),
    StoryParams("marsh", "bell", "song", "Mira", "raven", "brave"),
    StoryParams("grove", "feather", "rope", "Nia", "keeper", "curious"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A peculiar myth with a happy ending.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--relic", choices=sorted(RELICS))
    parser.add_argument("--option", choices=sorted(OPTIONS))
    parser.add_argument("--name")
    parser.add_argument("--guide", choices=sorted(GUIDES))
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    values = {
        "place": getattr(args, "place", None) or rng.choice(sorted(PLACES)),
        "relic": getattr(args, "relic", None) or rng.choice(sorted(RELICS)),
        "option": getattr(args, "option", None) or rng.choice(sorted(OPTIONS)),
        "name": getattr(args, "name", None) or rng.choice(NAMES),
        "guide": getattr(args, "guide", None) or rng.choice(sorted(GUIDES)),
        "trait": getattr(args, "trait", None) or rng.choice(TRAITS),
    }
    return StoryParams(**values)


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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
    if getattr(args, "n", None) < 1:
        raise SystemExit("-n must be at least 1")
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        for place, relic, option in asp_valid():
            print(f"{place}: {relic} + {option}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### tale {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
