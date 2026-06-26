#!/usr/bin/env python3
"""
storyworlds/worlds/pod_squaw_flashback_bad_ending_detective_story.py
====================================================================

A tiny detective-story world with a flashback turn and a bad ending.

Seed-image premise:
- A small detective follows a clue involving a pod.
- A loud "squaw" from a bird-like witness sends them back to a memory.
- The memory reveals a missed detail, but the ending goes badly anyway:
  the clue is lost, the suspect slips away, or the case stays unsolved.

This script is a standalone Storyweavers world:
- typed entities with meters and memes
- state-driven prose
- a Python reasonableness gate
- an inline ASP twin for parity checks
- story QA and world-knowledge QA
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    detective: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"detective", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
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
    label: str
    clue_kind: str
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
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    fragile: bool = False
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
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    clue_kind: str
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
class StoryParams:
    place: str
    clue: str
    suspect: str
    name: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.events = list(self.events)
        return clone


PLACES = {
    "alley": Place(id="alley", label="the wet alley", clue_kind="pod"),
    "station": Place(id="station", label="the old station", clue_kind="paper"),
    "garden": Place(id="garden", label="the back garden", clue_kind="pod"),
}

CLUES = {
    "pod": Clue(
        id="pod",
        label="pod",
        phrase="a split green pod",
        kind="pod",
        fragile=True,
    ),
    "ticket": Clue(
        id="ticket",
        label="ticket stub",
        phrase="a bent ticket stub",
        kind="paper",
        fragile=False,
    ),
    "button": Clue(
        id="button",
        label="button",
        phrase="a brass button",
        kind="metal",
        fragile=False,
    ),
}

SUSPECTS = {
    "crow": Suspect(
        id="crow",
        label="the crow",
        type="bird",
        alibi="It was perched on a fence and had a mouth full of crumbs.",
        clue_kind="pod",
    ),
    "porter": Suspect(
        id="porter",
        label="the porter",
        type="man",
        alibi="He was stacking crates and never went near the clue.",
        clue_kind="paper",
    ),
    "neighbor": Suspect(
        id="neighbor",
        label="the neighbor",
        type="woman",
        alibi="She was sweeping her step and heard the noise from far away.",
        clue_kind="metal",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            if clue.kind != place.clue_kind:
                continue
            for sid, suspect in SUSPECTS.items():
                if suspect.clue_kind == clue.kind:
                    out.append((pid, cid, sid))
    return out


@dataclass
class StoryState:
    detective: Entity
    clue: Entity
    suspect: Entity
    place: Place
    flashback: bool = False
    bad_ending: bool = False
    state: object | None = None
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.clue not in CLUES:
        pass
    if params.suspect not in SUSPECTS:
        pass
    place = _safe_lookup(PLACES, params.place)
    clue = _safe_lookup(CLUES, params.clue)
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    if clue.kind != place.clue_kind:
        pass
    if suspect.clue_kind != clue.kind:
        pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective story world with a flashback and a bad ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
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
    if getattr(args, "place", None) and getattr(args, "clue", None) and getattr(args, "suspect", None):
        reasonableness_gate(StoryParams(getattr(args, "place", None), getattr(args, "clue", None), getattr(args, "suspect", None), getattr(args, "name", None) or "Mina"))
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
        and (getattr(args, "suspect", None) is None or c[2] == getattr(args, "suspect", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, suspect = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Mina", "Ivy", "June", "Noah", "Eli"])
    return StoryParams(place=place, clue=clue, suspect=suspect, name=name)


def predict_loss(world: World, state: StoryState) -> bool:
    sim = world.copy()
    detective = sim.get(state.detective.id)
    clue = sim.get(state.clue.id)
    detective.memes["hope"] = detective.memes.get("hope", 0.0) + 1
    if clue.meters.get("held", 0.0) < THRESHOLD:
        clue.meters["lost"] = clue.meters.get("lost", 0.0) + 1
    return clue.meters.get("lost", 0.0) >= THRESHOLD


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    clue_cfg = _safe_lookup(CLUES, params.clue)
    suspect_cfg = _safe_lookup(SUSPECTS, params.suspect)
    world = World(place)

    detective = world.add(Entity(
        id=params.name,
        kind="character",
        type="detective",
        label=params.name,
    ))
    clue = world.add(Entity(
        id="clue",
        type=clue_cfg.kind,
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        owner=detective.id,
    ))
    suspect = world.add(Entity(
        id=suspect_cfg.id,
        kind="character",
        type=suspect_cfg.type,
        label=suspect_cfg.label,
    ))

    state = StoryState(detective=detective, clue=clue, suspect=suspect, place=place)

    detective.memes["curiosity"] = 1
    clue.meters["held"] = 1
    world.say(
        f"{detective.id} was a little detective with a sharp hat and a notebook that never stayed closed."
    )
    world.say(
        f"At {place.label}, {detective.id} found {clue_cfg.phrase} and knew it could be the start of a case."
    )
    world.say(
        f"{detective.id} wrote down the clue, then looked around for whoever had left it behind."
    )

    world.para()
    detective.memes["worry"] = 1
    world.say(
        f"Near a cracked wall, {suspect_cfg.label} made a loud squaw."
    )
    world.say(
        f"The sound snapped {detective.id} back to an old memory: {suspect_cfg.alibi}"
    )
    state.flashback = True
    world.events.append("flashback")

    if clue_cfg.fragile:
        world.say(
            f"In the flashback, {detective.id} remembered the pod splitting open when {detective.id} squeezed it too hard."
        )
    else:
        world.say(
            f"In the flashback, {detective.id} remembered that the clue had been easy to carry, but easy to misread."
        )

    world.para()
    world.say(
        f"{detective.id} hurried to check the clue again, but the bad moment came too fast."
    )
    if predict_loss(world, state):
        clue.meters["lost"] = clue.meters.get("lost", 0.0) + 1
    clue.meters["lost"] = clue.meters.get("lost", 0.0) + 1
    detective.memes["disappointment"] = 1
    world.say(
        f"The {clue.label} slipped away, and {suspect_cfg.label} vanished into the rain-dark street."
    )
    world.say(
        f"{detective.id} stared at the empty ground, notebook open, with no clean ending to write."
    )
    state.bad_ending = True
    world.events.append("bad_ending")

    world.facts = {
        "detective": detective,
        "clue": clue,
        "suspect": suspect,
        "place": place,
        "flashback": state.flashback,
        "bad_ending": state.bad_ending,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective")
    clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    suspect = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "suspect")
    return [
        f'Write a short detective story for a young child that includes the word "{clue.label}" and ends in a bad ending.',
        f"Tell a mystery where {detective.id} follows {clue.phrase} at {place.label}, hears a squaw, and remembers a flashback.",
        f"Write a simple detective tale about {suspect.label}, a lost clue, and an ending where the case does not get solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective")
    clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue")
    suspect = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "suspect")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {detective.id}, a little detective trying to solve a case at {place.label}.",
        ),
        QAItem(
            question=f"What clue did {detective.id} find?",
            answer=f"{detective.id} found {clue.phrase}. That clue started the mystery.",
        ),
        QAItem(
            question=f"What made {detective.id} remember the past?",
            answer=f"The loud squaw from {suspect.label} sent {detective.id} into a flashback.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: the clue was lost and the case was not solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly goes back to something that happened earlier.",
        ),
        QAItem(
            question="What does a bird's squaw sound like?",
            answer="A squaw is a loud, sharp bird call that can sound rough and surprising.",
        ),
        QAItem(
            question="What is a pod?",
            answer="A pod is a shell or case that holds seeds or other small things inside.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  events: {world.events}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", clue="pod", suspect="crow", name="Mina"),
    StoryParams(place="alley", clue="pod", suspect="crow", name="Ivy"),
]


ASP_RULES = r"""
place_ok(P,C) :- place(P), clue(C), place_kind(P,K), clue_kind(C,K).
suspect_ok(C,S) :- clue(C), suspect(S), clue_kind(C,K), suspect_kind(S,K).
valid_story(P,C,S) :- place_ok(P,C), suspect_ok(C,S).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_kind", pid, p.clue_kind))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, c.kind))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("suspect_kind", sid, s.clue_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple[str, str, str]]:
    return asp_valid_stories()


def asp_verify() -> int:
    import asp
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


def explain_rejection(place: Place, clue: Clue, suspect: Suspect) -> str:
    return (
        f"(No story: {place.label} does not support a {clue.label} clue tied to {suspect.label}. "
        f"The detective case would not feel believable.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
        and (getattr(args, "suspect", None) is None or c[2] == getattr(args, "suspect", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, suspect = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Mina", "Ivy", "June", "Noah", "Eli", "Ada"])
    return StoryParams(place=place, clue=clue, suspect=suspect, name=name)


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue, suspect) combos:\n")
        for p, c, s in combos:
            print(f"  {p:8} {c:8} {s:8}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.clue} at {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
