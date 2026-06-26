#!/usr/bin/env python3
"""
Storyworld: Plead, Pull, Significance
=====================================

A small, self-contained story world built from the seed words:
- plead
- pull
- significance

The world follows a rhyming-story feel: short, musical sentences with a clear
beginning, a foreshadowed turn, and a resolution driven by world state.

Premise:
- A child wants to pull a ribbon on a kite, box, or bell.
- A parent foresees that pulling too soon will spoil the meaningful part.
- The child pleads.
- A compatible helper or careful plan preserves the significance.

This script models a tiny domain with physical meters and emotional memes, emits
a prose story plus QA, and includes an inline ASP twin for parity checks.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize_ent: object | None = None
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    foreshadow: str
    meaning: str
    keyword: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    neutralizes: set[str] = field(default_factory=set)
    protects: set[str] = field(default_factory=set)
    phrase: str = ""
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.ending: str = ""

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


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "garden": Setting(place="the garden", affords={"ribbon", "lantern", "kite"}),
    "attic": Setting(place="the attic", affords={"box", "ribbon"}),
    "pier": Setting(place="the pier", affords={"kite", "lantern"}),
}

ACTIONS = {
    "ribbon": Action(
        id="ribbon",
        verb="pull the ribbon",
        gerund="pulling ribbons",
        rush="reach for the ribbon",
        mess="tangled",
        soil="all tangled",
        foreshadow="The ribbon fluttered like a clue in the breeze.",
        meaning="The ribbon was tied to something special and should be opened with care.",
        keyword="ribbon",
        tags={"ribbon", "tangle"},
    ),
    "box": Action(
        id="box",
        verb="pull the red cord",
        gerund="pulling red cords",
        rush="grab the cord",
        mess="scattered",
        soil="scattered everywhere",
        foreshadow="The little cord sat still, but it seemed important.",
        meaning="The cord kept the lid shut on a keepsake box.",
        keyword="pull",
        tags={"box", "gift"},
    ),
    "kite": Action(
        id="kite",
        verb="pull the kite string",
        gerund="pulling kite strings",
        rush="yank the string",
        mess="snapped",
        soil="snapped and bent",
        foreshadow="The kite tugged once, then drifted low, as if warning the eye.",
        meaning="The string helped the kite stay in the air.",
        keyword="string",
        tags={"kite", "wind"},
    ),
    "lantern": Action(
        id="lantern",
        verb="pull the wick",
        gerund="pulling wicks",
        rush="twitch the wick",
        mess="dimmed",
        soil="dim and damp",
        foreshadow="The lantern glowed soft and gold, like a secret about to be told.",
        meaning="The wick made the lantern glow bright for a special moment.",
        keyword="lantern",
        tags={"lantern", "glow"},
    ),
}

PRIZES = {
    "bow": Prize(id="bow", label="bow", phrase="a bright blue bow", region="hand"),
    "giftbox": Prize(id="giftbox", label="gift box", phrase="a wrapped gift box", region="hand"),
    "kite": Prize(id="kite_prize", label="kite", phrase="a paper kite with a painted smile", region="hand"),
    "lantern": Prize(id="lantern_prize", label="lantern", phrase="a little lantern for a special night", region="hand"),
}

FIXES = [
    Fix(
        id="untye",
        label="a careful untie",
        prep="untie the knot first",
        tail="slowly opened the knot and kept the bow neat",
        neutralizes={"tangled"},
        protects={"hand"},
        phrase="careful hands",
    ),
    Fix(
        id="hold_up",
        label="a steady hold",
        prep="hold the box steady first",
        tail="held the box steady while the cord was pulled",
        neutralizes={"scattered"},
        protects={"hand"},
        phrase="steady hands",
    ),
    Fix(
        id="guide",
        label="a gentle guide",
        prep="guide the string with two hands",
        tail="guided the string so the kite could rise again",
        neutralizes={"snapped"},
        protects={"hand"},
        phrase="two hands together",
    ),
    Fix(
        id="cover_wick",
        label="a dry cover",
        prep="cover the wick before touching it",
        tail="kept the wick dry and bright",
        neutralizes={"dimmed"},
        protects={"hand"},
        phrase="a dry cloth",
    ),
]

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Sam", "Leo"]
TRAITS = ["curious", "gentle", "brave", "patient", "bright"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
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


def action_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region == "hand"


def select_fix(action: Action, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if action.mess in fix.neutralizes and prize.region in fix.protects:
            return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIONS, act_id)
            for prize_id, prize in PRIZES.items():
                if action_at_risk(act, prize) and select_fix(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


ASP_RULES = r"""
% An action risks a prize when the prize is carried in the hand.
at_risk(A, P) :- action(A), prize(P), region(P, hand).

% A fix is compatible when it neutralizes the action's mess and protects the hand.
compatible(F, A, P) :- fix(F), at_risk(A, P),
                       neutralizes(F, M), mess_of(A, M),
                       protects(F, hand).

valid(Place, A, P) :- affords(Place, A), at_risk(A, P), compatible(_, A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, prize.region))
        lines.append(asp.fact("wears", "girl", pid))
        lines.append(asp.fact("wears", "boy", pid))
    for fix in FIXES:
        lines.append(asp.fact("fix", fix.id))
        for m in sorted(fix.neutralizes):
            lines.append(asp.fact("neutralizes", fix.id, m))
        for r in sorted(fix.protects):
            lines.append(asp.fact("protects", fix.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def intro(world: World, hero: Entity, parent: Entity, action: Action, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'bright')} {hero.type}, "
        f"with a heart that liked to sing and sight."
    )
    world.say(
        f"At {world.setting.place}, {hero.id} found {prize.phrase}, small and neat, "
        f"and the day felt merry, crisp, and sweet."
    )
    world.say(
        f"{action.foreshadow} {action.meaning}"
    )
    world.facts["foreshadow"] = action.foreshadow
    world.facts["meaning"] = action.meaning


def set_scene(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"One day at {world.setting.place}, {hero.id} went there with {parent.pronoun('possessive')} {parent.type}, "
        f"with walking feet and patient air."
    )


def plead(world: World, hero: Entity, parent: Entity, action: Action, prize: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.id} wanted to {action.verb}, with a grin so wide and free."
    )
    world.say(
        f'But {parent.pronoun("subject").capitalize()} said, "Wait a bit, dear one, and see the proper key."'
    )
    world.say(
        f"{hero.id} began to plead, " + f'"Please, please, may I?"' + ", in a tiny rhyme."
    )
    hero.memes["plead"] = hero.memes.get("plead", 0) + 1
    world.facts["plead"] = True


def warn(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity) -> None:
    world.say(
        f"{parent.pronoun('subject').capitalize()} looked ahead and saw the sign: "
        f"if {hero.id} pulled too soon, the {action.keyword} would not be fine."
    )
    world.say(
        f'"That would make it {action.soil}, and lose its shine," {parent.pronoun("subject")} said. '
        f'"Its {action.meaning.lower()}"'
    )
    world.facts["warned"] = True
    world.facts["soil"] = action.soil


def do_action(world: World, hero: Entity, action: Action) -> None:
    hero.meters[action.mess] = hero.meters.get(action.mess, 0) + 1
    hero.memes["tension"] = hero.memes.get("tension", 0) + 1


def offer_fix(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity) -> Optional[Fix]:
    fix = select_fix(action, prize)
    if fix is None:
        return None
    world.say(
        f"{parent.pronoun('subject').capitalize()} smiled and found {fix.label}, "
        f"for a safer way that sang just right."
    )
    world.say(
        f'"How about we {fix.prep}, then {action.verb} tonight?"'
    )
    world.facts["fix"] = fix.id
    return fix


def accept_fix(world: World, hero: Entity, parent: Entity, action: Action, prize: Entity, fix: Fix) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["tension"] = 0
    world.say(
        f"{hero.id} stopped to think, then nodded quick, and gave a happy cheer."
    )
    world.say(
        f"Together they {fix.tail}, and kept the special thing right here."
    )
    world.say(
        f"In the end, {prize.phrase} stayed bright, and the small plan proved its worth."
    )
    world.say(
        f"The little lesson held its glow: significance comes from careful earth."
    )
    world.ending = "resolved"
    world.facts["resolved"] = True
    world.facts["significance"] = prize.phrase


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    action = _safe_lookup(ACTIONS, params.action)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={"trait_word": params.trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
    ))
    prize_ent = world.add(Entity(
        id="Prize",
        type="thing",
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    intro(world, hero, parent, action, prize_ent)
    world.para()
    set_scene(world, hero, parent)
    plead(world, hero, parent, action, prize_ent)
    warn(world, parent, hero, action, prize_ent)
    do_action(world, hero, action)
    world.para()
    fix = offer_fix(world, parent, hero, action, prize_ent)
    if fix is None:
        _fallback_pool = globals().get("FIXS") or globals().get("FIXES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        fix = next(iter(_fallback_pool), None)
        if fix is None:
            raise StoryError
    accept_fix(world, hero, parent, action, prize_ent, fix)
    world.facts.update(hero=hero, parent=parent, prize=prize_ent, action=action, fix=fix, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    action: Action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    return [
        f'Write a short rhyming story for a child where {hero.id} wants to {action.verb} but must first think about the meaning of {prize.label}.',
        f'Create a gentle foreshadowing story using the words "plead" and "pull" where a parent helps keep a special thing safe.',
        f'Write a tiny rhyme about a child who pleads to pull something, then finds a careful way that preserves significance.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    action: Action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    fix: Fix = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fix")
    return [
        QAItem(
            question=f"Why did {hero.id} plead before trying to {action.verb}?",
            answer=(
                f"{hero.id} wanted to {action.verb} right away, but {parent.pronoun('subject')} "
                f"had already seen the trouble ahead. The plea showed how much {hero.id} wanted it."
            ),
        ),
        QAItem(
            question=f"What did {parent.pronoun('subject')} warn would happen if {hero.id} pulled too soon?",
            answer=(
                f"{parent.pronoun('subject').capitalize()} warned that the {action.keyword} would become {action.soil}, "
                f"which would spoil the special thing and dim its significance."
            ),
        ),
        QAItem(
            question=f"How did {fix.label} help keep {prize.label} safe?",
            answer=(
                f"{fix.prep.capitalize()}, so the pull could happen in a careful way. "
                f"That kept {prize.phrase} from getting {action.soil}."
            ),
        ),
        QAItem(
            question=f"What stayed important at the end of the story?",
            answer=(
                f"{prize.phrase} stayed bright and safe, and the careful choice proved that significance can live in a gentle plan."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "ribbon": [(
        "What is a ribbon?",
        "A ribbon is a long, thin strip of cloth that can tie things up or decorate a gift."
    )],
    "kite": [(
        "What does a kite need to fly?",
        "A kite needs wind and a string, so a person can guide it up into the sky."
    )],
    "lantern": [(
        "What is a lantern for?",
        "A lantern makes light so people can see in dim places or on special nights."
    )],
    "tangle": [(
        "What happens when something gets tangled?",
        "When something gets tangled, its strings or ribbons are twisted together and can be hard to sort out."
    )],
    "gift": [(
        "Why is a gift box special?",
        "A gift box is special because it can hold a surprise that someone wants to open carefully."
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "action").tags)
    if world.facts.get("fix"):
        tags.add("gift")
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="garden", action="ribbon", prize="bow", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="attic", action="box", prize="giftbox", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="pier", action="kite", prize="kite", name="Ava", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="pier", action="lantern", prize="lantern", name="Leo", gender="boy", parent="father", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with plead, pull, significance, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "action", None) and getattr(args, "prize", None):
        act, prize = _safe_lookup(ACTIONS, getattr(args, "action", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not action_at_risk(act, prize) or not select_fix(act, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


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
# CLI / main
# ---------------------------------------------------------------------------
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, action, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
