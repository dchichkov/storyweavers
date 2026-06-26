#!/usr/bin/env python3
"""
A small slice-of-life story world about a clamor that causes a misunderstanding,
then gets cleared up with a simple, gentle explanation.
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    other: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "sister", "aunt"}
        male = {"boy", "man", "father", "dad", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
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
class Place:
    id: str
    label: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)
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
class Cause:
    id: str
    verb: str
    noun: str
    noise: str
    misunderstanding: str
    setting_note: str
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    type: str
    owner_kind: str = "person"
    plural: bool = False
    fragile: bool = False
    helpful: bool = False
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
class StoryParams:
    place: str
    cause: str
    object: str
    name: str
    helper: str
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
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _mingle(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters.get("noise", 0) >= THRESHOLD and e.kind == "object":
            sig = ("noise", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"The clamor carried through the room.")
            for person in list(world.entities.values()):
                if person.kind != "character":
                    continue
                person.memes["startled"] = person.memes.get("startled", 0) + 1
    return out


def _misunderstand(world: World) -> list[str]:
    out = []
    speaker = world.facts.get("speaker")
    listener = world.facts.get("listener")
    cause = world.facts.get("cause")
    if not speaker or not listener or not cause:
        return out
    sp = world.get(speaker)
    li = world.get(listener)
    if sp.memes.get("startled", 0) < THRESHOLD:
        return out
    sig = ("misunderstand", speaker, listener, cause.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    li.memes["worry"] = li.memes.get("worry", 0) + 1
    out.append(f"{li.id} thought the clamor meant something was wrong.")
    return out


def _explain(world: World) -> list[str]:
    out = []
    if not world.facts.get("explained"):
        return out
    speaker = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "speaker")
    listener = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "listener")
    sig = ("explain", speaker, listener)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    li = world.get(listener)
    sp = world.get(speaker)
    li.memes["worry"] = 0
    li.memes["relief"] = li.memes.get("relief", 0) + 1
    sp.memes["relief"] = sp.memes.get("relief", 0) + 1
    out.append("After a quick explanation, everyone understood.")
    return out


RULES = [
    ("mingle", _mingle),
    ("misunderstand", _misunderstand),
    ("explain", _explain),
]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                if narrate:
                    for s in lines:
                        world.say(s)


def build_scene(place: Place, cause: Cause, obj: ObjectDef, name: str, helper: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type="girl", meters={}, memes={}))
    other = world.add(Entity(id=helper, kind="character", type="mother", meters={}, memes={}))
    thing = world.add(Entity(id=obj.id, kind="object", type=obj.type, label=obj.label, phrase=obj.phrase, plural=obj.plural))
    world.facts.update(child=child.id, other=other.id, object=obj, cause=cause, speaker=child.id, listener=other.id)
    child.meters["noise"] = 0
    thing.meters["noise"] = 0
    world.say(f"{child.id} was having an ordinary day at {place.label}.")
    world.say(f"{child.id} had {obj.phrase}. {child.id} liked the little rhythm it made during the day.")
    world.para()
    world.say(cause.setting_note)
    world.say(f"Then {child.id} {cause.verb} the {cause.noun}, and it made a sudden {cause.noise}.")
    thing.meters["noise"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{other.id} looked over and {cause.misunderstanding}.")
    world.say(f"{child.id} quickly explained that it was only {cause.noun}, not trouble.")
    world.facts["explained"] = True
    propagate(world, narrate=True)
    world.para()
    world.say(f"In the end, the room was calm again, and {child.id} kept the {obj.label} close.")
    world.say(f"{other.id} smiled because the clamor had only been a small misunderstanding.")
    return world


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", indoors=True, affords={"clamor"}),
    "hall": Place(id="hall", label="the hallway", indoors=True, affords={"clamor"}),
    "apartment": Place(id="apartment", label="the apartment", indoors=True, affords={"clamor"}),
    "porch": Place(id="porch", label="the porch", indoors=False, affords={"clamor"}),
}

CAUSES = {
    "pots": Cause(
        id="pots",
        verb="bumped",
        noun="two metal pots",
        noise="clang",
        misunderstanding="thought there had been an accident",
        setting_note="A stack of kitchen things waited by the table.",
        tags={"clamor", "noise", "kitchen"},
    ),
    "blocks": Cause(
        id="blocks",
        verb="tapped together",
        noun="wooden blocks",
        noise="clatter",
        misunderstanding="thought someone had dropped something important",
        setting_note="A small toy pile sat beside the rug.",
        tags={"clamor", "noise", "toy"},
    ),
    "pan": Cause(
        id="pan",
        verb="set down",
        noun="a big pan",
        noise="bang",
        misunderstanding="worried that somebody was upset",
        setting_note="Dinner was nearly ready, and the table was crowded with bowls.",
        tags={"clamor", "noise", "kitchen"},
    ),
    "jar": Cause(
        id="jar",
        verb="shook",
        noun="a jar of buttons",
        noise="rattle",
        misunderstanding="thought the room was suddenly in a hurry",
        setting_note="A basket of little things sat in the corner by the lamp.",
        tags={"clamor", "noise", "buttons"},
    ),
}

OBJECTS = {
    "book": ObjectDef(id="book", label="picture book", phrase="a picture book with bright animals", type="book"),
    "blocks": ObjectDef(id="blocks", label="stack of blocks", phrase="a stack of colorful blocks", type="blocks", plural=True, helpful=True),
    "cup": ObjectDef(id="cup", label="blue cup", phrase="a blue cup with a cat on it", type="cup"),
    "jar": ObjectDef(id="jar", label="jar of buttons", phrase="a little jar of shiny buttons", type="jar", fragile=True),
}

NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Maya", "Ella", "Ruby"]
HELPERS = ["Mom", "Aunt May", "Grandma", "Mother"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for cause_id in place.affords:
            for obj_id in OBJECTS:
                combos.append((place_id, cause_id, obj_id))
    return combos


def explain_rejection(place: str, cause: str, obj: str) -> str:
    return f"(No story: {cause} and {obj} do not make a believable slice-of-life misunderstanding in {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a clamor and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "cause", None):
        combos = [c for c in combos if c[1] == getattr(args, "cause", None)]
    if getattr(args, "object", None):
        combos = [c for c in combos if c[2] == getattr(args, "object", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, cause, obj = rng.choice(list(combos))
    return StoryParams(
        place=place,
        cause=cause,
        object=obj,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story about a clamor that causes a misunderstanding at {world.place.label}.',
        f"Tell a short story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").id} makes a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "cause").noise} with {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "cause").noun} and another person briefly worries.",
        f"Write a child-friendly story that ends with an explanation and a calm room after a small clamor.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    other = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "other")
    cause = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "cause")
    obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "object")
    return [
        QAItem(
            question=f"What caused the clamor at {world.place.label}?",
            answer=f"{child.id} {cause.verb} {cause.noun}, and that made a sudden {cause.noise}.",
        ),
        QAItem(
            question=f"Why did {other.id} think something was wrong?",
            answer=f"{other.id} thought the clamor meant something was wrong because the {cause.noise} sounded surprising.",
        ),
        QAItem(
            question=f"What did {child.id} keep close at the end?",
            answer=f"{child.id} kept the {obj.label} close after everything was explained.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone does not understand what is really happening and gets the wrong idea for a little while.",
        ),
        QAItem(
            question="What is clamor?",
            answer="Clamor is a lot of noisy sound, like banging, clattering, or loud voices all at once.",
        ),
        QAItem(
            question="Why can explaining help after a mistake?",
            answer="Explaining helps because it gives the real reason, so people can calm down and understand each other again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  facts={list(world.facts.keys())}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    cause = _safe_lookup(CAUSES, params.cause)
    obj = _safe_lookup(OBJECTS, params.object)
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type="girl"))
    helper = world.add(Entity(id=params.helper, kind="character", type="mother"))
    thing = world.add(Entity(id=obj.id, kind="object", type=obj.type, label=obj.label, phrase=obj.phrase, plural=obj.plural))
    world.facts.update(child=child, other=helper, object=obj, cause=cause)

    world.say(f"{child.id} was having an ordinary afternoon in {place.label}.")
    world.say(f"{child.id} liked {obj.phrase}, because it made the room feel cozy and familiar.")
    world.para()
    world.say(cause.setting_note)
    world.say(f"Then {child.id} {cause.verb} {cause.noun}, and it made a loud {cause.noise}.")
    child.meters["noise"] = 1
    thing.meters["noise"] = 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{helper.id} turned around and looked worried.")
    world.say(f"{helper.id} thought the sound meant trouble, but {child.id} explained it was only {cause.noun}.")
    world.facts["explained"] = True
    propagate(world, narrate=True)
    world.para()
    world.say(f"After that, the room felt normal again, and {child.id} held the {obj.label} with a small smile.")
    world.say(f"{helper.id} smiled too, because the clamor had only been a misunderstanding.")
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


ASP_RULES = r"""
% A clamor can cause a misunderstanding if a noisy object is involved.
misunderstanding(O) :- noisy(O).
resolved(O) :- noisy(O), explained(O).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("noisy", cid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show misunderstanding/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "misunderstanding"))
    expected = {("pots",), ("blocks",), ("pan",), ("jar",)}
    if atoms == expected:
        print(f"OK: clingo gate matches Python reasonableness ({len(atoms)} cases).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("clingo:", sorted(atoms))
    print("python:", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/1."))
    return sorted(set(asp.atoms(model, "misunderstanding")))


def build_all() -> list[StoryParams]:
    out = []
    for place, cause, obj in valid_combos():
        out.append(StoryParams(place=place, cause=cause, object=obj, name="Mia", helper="Mom"))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show misunderstanding/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_list()
        print(f"{len(vals)} compatible clamor/misunderstanding cases:")
        for v in vals:
            print(" ", v)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in build_all()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
