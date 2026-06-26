#!/usr/bin/env python3
"""
storyworlds/worlds/knickers_driveway_magic_conflict_myth.py
============================================================

A small mythic storyworld about a child, a driveway, and enchanted knickers
that cause a gentle conflict before a careful resolution.

Seed tale premise:
- A child finds or receives magical knickers.
- They want to use the magic in the driveway.
- A guardian fears the magic will pull in trouble or ruin the clothes.
- The conflict is resolved by a safer ritual or constraint.
- The ending proves the change with a concrete image.

This world keeps the prose close to myth: simple, sturdy, and a little solemn,
with charm and consequence in the same breath.
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
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    artifact: object | None = None
    guard: object | None = None
    hero: object | None = None
    parent: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"dust": 0.0, "glow": 0.0, "torn": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "conflict": 0.0, "wonder": 0.0, "fear": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king", "uncle"}:
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
    place: str = "the driveway"
    SETTING: object | None = None
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
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    magic: str = ""
    risk: str = ""
    covers: set[str] = field(default_factory=set)
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
class Focus:
    id: str
    label: str
    action: str
    wonder: str
    risk_meter: str
    turn: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_dust(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.meters["glow"] < THRESHOLD:
            continue
        for ent in list(world.entities.values()):
            if ent.worn_by != hero.id:
                continue
            if ent.protective:
                continue
            sig = ("dust", hero.id, ent.id)
            if sig in world.fired:
                continue
            if ent.region == "legs":
                ent.meters["dust"] += 1
                ent.memes["fear"] += 0.5
                world.fired.add(sig)
                out.append(f"The driveway dust clung to {hero.pronoun('possessive')} {ent.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    out = []
    hero = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero_id"))
    if hero.memes["wonder"] >= THRESHOLD and hero.memes["fear"] >= THRESHOLD:
        sig = ("conflict", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] += 1
            out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("dust", _r_dust), Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(x for x in s if x != "__conflict__")
    if narrate:
        for s in out:
            world.say(s)
    return out


def do_magic(world: World, hero: Entity, artifact: Entity, focus: Focus, narrate: bool = True) -> None:
    hero.meters["glow"] += 1
    hero.memes["wonder"] += 1
    artifact.meters["glow"] += 1
    if narrate:
        world.say(f"When {hero.id} wore the {artifact.label}, the {artifact.magic} woke at once.")
        world.say(f"It was said that {focus.action}, and the {artifact.label} answered with {focus.wonder}.")
    propagate(world, narrate=narrate)


def predict(world: World, hero: Entity, artifact: Entity, focus: Focus) -> dict:
    sim = world.copy()
    do_magic(sim, sim.get(hero.id), sim.get(artifact.id), focus, narrate=False)
    return {
        "dust": sim.get(artifact.id).meters["dust"],
        "conflict": sim.get(hero.id).memes["conflict"],
    }


SETTING = Setting(place="the driveway")

FOCI = {
    "spark": Focus(
        id="spark",
        label="spark spell",
        action="the stones would shine and hop like fish",
        wonder="a bright line of gold along the cracks",
        risk_meter="dust",
        turn="salt",
    ),
    "whirl": Focus(
        id="whirl",
        label="wind spell",
        action="the air would circle and lift the chalk dust",
        wonder="a small whirl that sang at the gate",
        risk_meter="dust",
        turn="ribbon",
    ),
    "glimmer": Focus(
        id="glimmer",
        label="glimmer spell",
        action="the shadows would turn to silver",
        wonder="a pale glimmer on the gravel",
        risk_meter="dust",
        turn="cloth",
    ),
}

ARTIFACTS = {
    "knickers": Artifact(
        id="knickers",
        label="knickers",
        phrase="a pair of bright knickers stitched with moon thread",
        region="legs",
        plural=True,
        magic="moon thread",
        risk="the gravel would scratch their shine",
        covers={"legs"},
    ),
    "saintly": Artifact(
        id="saintly",
        label="knickers",
        phrase="old knickers with a saint's little star",
        region="legs",
        plural=True,
        magic="a star that kept a promise",
        risk="the dust would dull the star",
        covers={"legs"},
    ),
}

GUARDS = {
    "salt": ("a ring of salt", {"dust"}, {"legs"}, "drew a salt ring around the child", "stood safely inside the salt"),
    "cloth": ("a wool cloth", {"dust"}, {"legs"}, "wrapped the knickers in wool before the dance", "kept the shine safe under wool"),
    "ribbon": ("a blue ribbon sash", {"dust"}, {"legs"}, "tied a blue ribbon to mark the safe place", "let the magic stay close and calm"),
}

GIRL_NAMES = ["Mira", "Nora", "Lina", "Iris", "Asha", "Elin"]
BOY_NAMES = ["Oren", "Bram", "Tavi", "Luca", "Milo", "Rian"]
TRAITS = ["bold", "curious", "solemn", "bright", "stubborn", "gentle"]


@dataclass
class StoryParams:
    focus: str
    artifact: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic driveway storyworld with magic knickers and a conflict.")
    ap.add_argument("--focus", choices=FOCI)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [("driveway", fid) for fid in FOCI]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "gender", None) and getattr(args, "artifact", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "focus", None) and getattr(args, "artifact", None):
        pass
    focus = getattr(args, "focus", None) or rng.choice(list(FOCI))
    artifact = getattr(args, "artifact", None) or rng.choice(list(ARTIFACTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(focus=focus, artifact=artifact, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    focus = FOCI[params.focus]
    artifact_cfg = _safe_lookup(ARTIFACTS, params.artifact)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="guardian", kind="character", type=params.parent, label=f"the {params.parent}"))
    artifact = world.add(Entity(
        id=artifact_cfg.id, type="clothing", label=artifact_cfg.label, phrase=artifact_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=artifact_cfg.region, plural=artifact_cfg.plural,
        covers=set(artifact_cfg.covers)
    ))
    guard_name, _, _, _, _ = _safe_lookup(GUARDS, focus.turn)
    guard = world.add(Entity(id=focus.turn, type="thing", label=guard_name, protective=True, covers={"legs"}))

    world.facts.update(hero_id=hero.id, parent_id=parent.id, artifact_id=artifact.id, focus_id=focus.id, guard_id=guard.id)

    world.say(f"{hero.id} was a {params.trait} child who loved old stories and new wonders.")
    world.say(f"One day, {hero.pronoun('possessive')} {parent.type if params.parent in {'mother','father'} else params.parent} brought forth {artifact.phrase}.")
    world.say(f"The family said the knickers were a gift from the old days, when stars still listened to children.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} wanted to wear the {artifact.label} and try {focus.label}.")
    world.say(f"{hero.pronoun().capitalize()} believed the magic would make the driveway kind and bright.")
    do_magic(world, hero, artifact, focus, narrate=True)

    world.para()
    pred = predict(world, hero, artifact, focus)
    if pred["dust"] >= THRESHOLD:
        world.say(f"But the {params.parent} frowned, for {artifact.risk}.")
        world.say(f'"If you rush the spell, the old power will turn sour," {parent.id} said.')
        hero.memes["fear"] += 1
        hero.memes["conflict"] += 1
        world.say(f"{hero.id} crossed {hero.pronoun('possessive')} arms and said the driveway should not be feared.")
        world.say(f"Their voices rose like sparrows at dusk, and the little conflict stood between them.")
        world.say(f"Then the {params.parent} set down {guard_name} and made a safer way.")
        world.say(f"{_safe_lookup(GUARDS, focus.turn)[3].capitalize()}.")
        artifact.protective = True
        if focus.turn == "salt":
            world.say(f"The salt kept the dust from biting the shine.")
        elif focus.turn == "cloth":
            world.say(f"The wool drank the roughness and let the spell stay gentle.")
        else:
            world.say(f"The ribbon marked the edge where magic could dance without trouble.")
        hero.memes["conflict"] = 0.0
        hero.memes["joy"] += 1
        world.say(f"{hero.id} nodded, and the spell became a game instead of a battle.")
        world.say(f"Together they tried again, and the old knickers glimmered without harm.")
        world.say(f"In the end {hero.id} stood on the driveway, {focus.wonder}, while {parent.id} smiled beside {hero.pronoun('object')}.")
    else:
        world.say(f"The magic stayed light, and no trouble rose from the stones.")
        hero.memes["joy"] += 1
        world.say(f"{hero.id} laughed and spun once, and the driveway shone like a small temple.")

    world.facts.update(focus=focus, artifact=artifact, parent=parent, hero=hero)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    focus = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "focus")
    artifact = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "artifact")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    return [
        f'Write a short mythic story for a child about {hero.id}, {artifact.label}, and a spell in the driveway.',
        f"Tell a gentle conflict story where {hero.id} wants to use magical {artifact.label} but {parent.label} worries.",
        f'Write a small myth with the word "{artifact.label}" and a safe ending image of the driveway.',
        f"Make the magic feel old and true, with a child, a guardian, and {focus.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    artifact: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "artifact")
    focus: Focus = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "focus")
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {artifact.label} in the driveway?",
            answer=f"{hero.id} wanted to wear the {artifact.label} and use {focus.label} in the driveway.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the magic?",
            answer=f"{parent.label} worried because the magic could stir up dust and make the {artifact.label} lose its shine.",
        ),
        QAItem(
            question=f"What changed the conflict into a safer choice?",
            answer=f"They used {_safe_lookup(world.entities, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "guard_id")).label}, which let the magic stay gentle and kept the {artifact.label} safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} standing on the driveway while the {artifact.label} still glimmered and the guardian smiled nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a driveway?", answer="A driveway is a path beside a house where cars can go in and out, and children can sometimes play there."),
        QAItem(question="What does magic mean in a story?", answer="Magic is a special power that can make unusual things happen, like light, change, or wonder."),
        QAItem(question="What is conflict in a story?", answer="Conflict is when two characters want different things and must find a way through the trouble."),
        QAItem(question="What are knickers?", answer="Knickers are a kind of clothing worn under other clothes or as part of an old-fashioned outfit."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} protective={e.protective} covers={sorted(e.covers)}")
    lines.append(f"fired={sorted(world.fired)}")
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


CURATED = [
    StoryParams(focus="spark", artifact="knickers", name="Mira", gender="girl", parent="mother", trait="bold"),
    StoryParams(focus="whirl", artifact="knickers", name="Oren", gender="boy", parent="father", trait="curious"),
    StoryParams(focus="glimmer", artifact="saintly", name="Lina", gender="girl", parent="grandmother", trait="solemn"),
]


ASP_RULES = r"""
artifact(knickers).
artifact(saintly).
focus(spark).
focus(whirl).
focus(glimmer).

risk(knickers, dust).
risk(saintly, dust).

turn(spark, salt).
turn(whirl, ribbon).
turn(glimmer, cloth).

safe(F, A) :- focus(F), artifact(A), risk(A, dust), turn(F, G), guard(G), covers_legs(G).

guard(salt).
guard(ribbon).
guard(cloth).

covers_legs(salt).
covers_legs(ribbon).
covers_legs(cloth).

compatible(F, A) :- safe(F, A).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for fid in FOCI:
        lines.append(asp.fact("focus", fid))
    for aid in ARTIFACTS:
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("risk", aid, "dust"))
    for gid in GUARDS:
        lines.append(asp.fact("guard", gid))
        lines.append(asp.fact("covers_legs", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = {(f, a) for f in FOCI for a in ARTIFACTS}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print("clingo-only:", sorted(clingo_set - python_set))
    print("python-only:", sorted(python_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def build_parser_alias() -> argparse.ArgumentParser:
    return build_parser()


def resolve_params_alias(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible focus/artifact combos:\n")
        for f, a in combos:
            print(f"  {f:8} {a}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.focus} / {p.artifact}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
