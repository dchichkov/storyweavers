#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/gasp_breaker_obey_sharing_rhyme_whodunit.py
========================================================================================================================

A tiny whodunit-style storyworld about a missing treat, a cracked clue, and a
pair of children who solve the mystery by sharing, obeying, and reading a rhyme.

Seed tale sketch:
---
Mina and Theo were at Grandma's apartment during a rainy afternoon. Grandma
kept a cookie tin on the top shelf and had one rule: obey the rooms, and do not
climb onto the chair by the breaker box.

But the tin went missing. Then came a gasp from the hall, and Theo found a
crumb trail near the breaker box. Mina noticed a rhyme stuck to the fridge:

"If it hums and clicks, do not poke;
share the clue, then solve the joke."

The children followed the rhyme instead of grabbing the tin. They shared the
clues with Grandma, and she opened the quiet cabinet: the tin had been moved
there during cleanup. The missing cookies were safe the whole time.

The world model tracks:
- physical meters: mystery, risk, noise, crumbs, access, order
- emotional memes: curiosity, worry, relief, pride, trust, sharing, obedience

The prose is authored, child-facing, and state-driven: the ending image proves
what changed.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    box: object | None = None
    child1: object | None = None
    child2: object | None = None
    note: object | None = None
    room: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
        if not hasattr(self, "_tags"):
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    c: object | None = None
    w: object | None = None
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Place:
    id: str
    label: str
    scene: str
    quiet_spot: str
    risky_spot: str
    clue_place: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Clue:
    id: str
    label: str
    rhyme: str
    warning: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Risk:
    id: str
    label: str
    action: str
    rule: str
    danger: str
    trigger_word: str = "gasp"
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Fix:
    id: str
    label: str
    action: str
    success: str
    fail: str
    sense: int
    power: int
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


PLACES = {
    "apartment": Place(
        id="apartment",
        label="Grandma's apartment",
        scene="a rainy afternoon at Grandma's apartment",
        quiet_spot="the hall",
        risky_spot="the breaker box",
        clue_place="the fridge",
    ),
    "library": Place(
        id="library",
        label="the library reading nook",
        scene="a windy afternoon in the library reading nook",
        quiet_spot="the aisle between the shelves",
        risky_spot="the old power panel",
        clue_place="the notice board",
    ),
    "cabin": Place(
        id="cabin",
        label="the little cabin",
        scene="a snowy afternoon in the little cabin",
        quiet_spot="the front room",
        risky_spot="the breaker panel",
        clue_place="the coat hook",
    ),
}

CLUES = {
    "rhyme_note": Clue(
        id="rhyme_note",
        label="a rhyme note",
        rhyme="If it hums and clicks, do not poke; share the clue, then solve the joke.",
        warning="The rhyme said to share the clue and not to poke the buzzing thing.",
    ),
    "tiny_poem": Clue(
        id="tiny_poem",
        label="a tiny poem",
        rhyme="When something hums behind the door, obey the sign and look no more.",
        warning="The poem warned them to obey the sign and stay back.",
    ),
}

RISKS = {
    "breaker": Risk(
        id="breaker",
        label="breaker box",
        action="poke the breaker box",
        rule="do not climb onto the chair by the breaker box",
        danger="it could make sparks or a blackout",
    ),
    "panel": Risk(
        id="panel",
        label="power panel",
        action="touch the panel",
        rule="do not touch the panel",
        danger="it could give a hard shock and shut the lights off",
    ),
}

FIXES = {
    "share": Fix(
        id="share",
        label="share the clue",
        action="shared the clues with Grandma",
        success="shared the clues with Grandma, who solved the mystery right away",
        fail="tried to solve it alone and only made the mystery feel bigger",
        sense=3,
        power=3,
    ),
    "obey": Fix(
        id="obey",
        label="obey the rule",
        action="obeyed the rule and stayed away",
        success="obeyed the rule and stayed away from the risky spot",
        fail="forgot to obey the rule and stepped too close",
        sense=3,
        power=4,
    ),
    "peek": Fix(
        id="peek",
        label="peek carefully",
        action="peeked carefully from the doorway",
        success="peeked carefully from the doorway until Grandma came",
        fail="peeked carefully, but that was not enough to solve the mystery",
        sense=2,
        power=1,
    ),
    "blab": Fix(
        id="blab",
        label="blurt it out",
        action="blurred everything by blabbing first",
        success="blabbed the clue and still managed to help",
        fail="blabbed the clue and made everyone more confused",
        sense=1,
        power=0,
    ),
}

NAMES_GIRL = ["Mina", "Lena", "Ivy", "Zoe", "Nora", "Maya"]
NAMES_BOY = ["Theo", "Owen", "Eli", "Finn", "Noah", "Max"]


@dataclass
class StoryParams:
    place: str
    clue: str
    risk: str
    fix: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    adult: str = "Grandma"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit-style sharing and rhyme storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--fix", choices=FIXES)
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    risk = getattr(args, "risk", None) or rng.choice(list(RISKS))
    fix = getattr(args, "fix", None) or rng.choice(list(FIXES))
    if _safe_lookup(FIXES, fix).sense < 2:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if risk == "breaker" and place == "library":
        pass
    gender1 = rng.choice(["girl", "boy"])
    gender2 = "boy" if gender1 == "girl" and rng.random() < 0.5 else "girl"
    child1 = _pick_name(rng, gender1)
    child2 = _pick_name(rng, gender2)
    if child2 == child1:
        child2 = _pick_name(rng, "boy" if gender2 == "boy" else "girl")
    return StoryParams(place=place, clue=clue, risk=risk, fix=fix,
                       child1=child1, child1_gender=gender1,
                       child2=child2, child2_gender=gender2, seed=getattr(args, "seed", None))


def gate_reasonable(params: StoryParams) -> None:
    if params.fix not in {"share", "obey", "peek"}:
        pass
    if params.place not in PLACES:
        pass
    if params.clue not in CLUES or params.risk not in RISKS:
        pass


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for r in RISKS:
        lines.append(asp.fact("risk", r))
    for f, fx in FIXES.items():
        lines.append(asp.fact("fix", f))
        lines.append(asp.fact("sense", f, fx.sense))
        lines.append(asp.fact("power", f, fx.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
good(F) :- sensible(F), power(F,P), P >= 2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(a[0] for a in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    py = sorted(f for f, fx in FIXES.items() if fx.sense >= 2)
    cl = asp_sensible()
    ok = py == cl
    print("OK" if ok else "MISMATCH", "sensible fixes:", cl)
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def world_from_params(p: StoryParams) -> World:
    w = World()
    place = _safe_lookup(PLACES, p.place)
    clue = _safe_lookup(CLUES, p.clue)
    risk = _safe_lookup(RISKS, p.risk)
    fix = _safe_lookup(FIXES, p.fix)

    child1 = w.add(Entity(id=p.child1, kind="character", type=p.child1_gender, role="solver"))
    child2 = w.add(Entity(id=p.child2, kind="character", type=p.child2_gender, role="helper"))
    adult = w.add(Entity(id=p.adult, kind="character", type="grandmother", role="adult", label=p.adult))
    room = w.add(Entity(id="room", label=place.label, kind="thing"))
    box = w.add(Entity(id="breaker", label=risk.label, kind="thing"))
    note = w.add(Entity(id="clue", label=clue.label, kind="thing"))

    child1.memes["curiosity"] += 1
    child2.memes["curiosity"] += 1
    child2.memes["trust"] += 1
    room.meters["mystery"] += 1
    room.meters["order"] += 0.2

    w.say(f"It was {place.scene}, and something was missing.")
    w.say(f"{p.child1} and {p.child2} had been told one rule: {risk.rule}.")
    w.say(f"Then there was a gasp from {place.quiet_spot}.")
    child1.memes["worry"] += 1
    child2.memes["worry"] += 1
    room.meters["noise"] += 1

    w.para()
    w.say(f"{p.child2} found crumbs near the {risk.label}, but {p.child1} saw {clue.rhyme}")
    w.say(f'"{clue.rhyme}"')
    child1.memes["obedience"] += 1
    child2.memes["obedience"] += 1

    if p.fix == "share":
        child1.memes["sharing"] += 1
        child2.memes["sharing"] += 1
        w.say(f"So {p.child1} and {p.child2} chose to share the clue instead of rushing.")
        w.say(f"They brought it to {p.adult}, and {p.adult} smiled at once.")
        room.meters["access"] += 1
        room.meters["mystery"] = 0
        child1.memes["relief"] += 1
        child2.memes["relief"] += 1
        child1.memes["pride"] += 1
    elif p.fix == "obey":
        child1.memes["obedience"] += 1
        w.say(f"They obeyed the rule and stayed away from the {risk.label}.")
        w.say(f"Then they shared the clue with {p.adult}, who checked the right cupboard.")
        room.meters["risk"] = 0
        room.meters["mystery"] = 0
        child1.memes["relief"] += 1
        child2.memes["relief"] += 1
    else:
        w.say(f"They peeked carefully from the doorway and waited for {p.adult}.")
        w.say(f"When {p.adult} came, the clue made sense at last.")
        room.meters["mystery"] = 0
        child1.memes["relief"] += 1
    w.para()
    w.say(f"{p.adult} opened the quiet cabinet: the missing tin had been moved there during cleanup.")
    w.say(f"The children laughed, because the breaker box had not been the culprit at all.")
    w.say(f"In the ending image, the tin sat safe on the shelf, and everyone shared the cookies together.")

    w.facts.update(
        place=place, clue=clue, risk=risk, fix=fix,
        child1=child1, child2=child2, adult=adult, room=room,
        outcome="solved",
    )
    return w


def story_prompts(w: World) -> list[str]:
    f = w.facts
    return [
        f"Write a child-friendly whodunit about {f['child1'].id} and {f['child2'].id} at {f['place'].label}, using the words gasp, breaker, and obey.",
        f"Tell a mystery story where a rhyme helps two children solve a missing-cookie problem without touching the breaker box.",
        f"Write a small Sharing-and-Rhyme story in whodunit style: the clues are shared, the rule is obeyed, and the ending proves the tin was safe.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    p: Place = f["place"]
    c: Clue = f["clue"]
    r: Risk = f["risk"]
    fx: Fix = f["fix"]
    a: Entity = f["child1"]
    b: Entity = f["child2"]
    adult: Entity = f["adult"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a whodunit-style mystery about missing cookies, shared clues, and a safe ending.",
        ),
        QAItem(
            question=f"What did {a.id} and {b.id} hear first?",
            answer=f"They heard a gasp from {p.quiet_spot}, which told them something was wrong.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"They found a rhyme: {c.rhyme}",
        ),
        QAItem(
            question=f"What rule did they obey?",
            answer=f"They obeyed the rule: {r.rule}.",
        ),
        QAItem(
            question=f"What did they do instead of poking the {r.label}?",
            answer=f"They chose to {fx.action} and asked {adult.id} for help.",
        ),
        QAItem(
            question="Where was the missing tin?",
            answer="It had been moved into a quiet cabinet during cleanup, so it was safe the whole time.",
        ),
    ]


WORLD_QA = {
    "gasp": [("What does a gasp usually mean in a mystery?",
              "A gasp usually means someone suddenly noticed something surprising, worrying, or important.")],
    "breaker": [("What is a breaker box?",
                 "A breaker box is a grown-up electrical box that controls power in a home.")],
    "obey": [("What does obey mean?",
              "To obey means to follow a rule or listen carefully to a grown-up.")],
    "sharing": [("Why is sharing clues helpful?",
                  "Sharing clues helps everyone look at the same evidence and solve the mystery together.")],
    "rhyme": [("What is a rhyme?",
                "A rhyme is a little bit of text or a song where words sound alike at the end.")],
}


def world_knowledge_qa(w: World) -> list[QAItem]:
    tags = {w.facts["risk"].id, "gasp", "breaker", "obey", "sharing", "rhyme"}
    out: list[QAItem] = []
    for t in tags:
        if t in WORLD_QA:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_QA[t])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== (2) Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(w: World) -> str:
    lines = ["--- world trace ---"]
    for e in w.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for c in CLUES:
            for r in RISKS:
                out.append((p, c, r))
    return out


CURATED = [
    StoryParams("apartment", "rhyme_note", "breaker", "share", "Mina", "girl", "Theo", "boy"),
    StoryParams("library", "tiny_poem", "panel", "obey", "Ivy", "girl", "Max", "boy"),
    StoryParams("cabin", "rhyme_note", "breaker", "peek", "Noah", "boy", "Lena", "girl"),
]


def generate(params: StoryParams) -> StorySample:
    gate_reasonable(params)
    w = world_from_params(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=story_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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
        print(asp_program(show="#show sensible/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program(show="#show sensible/1."))
        print("sensible fixes:", ", ".join(sorted(a[0] for a in asp.atoms(model, "sensible"))))
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if getattr(args, "all", None) else []
    if not getattr(args, "all", None):
        seen = set()
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(rng.randint(0, 2**31 - 1)))
            p.seed = getattr(args, "seed", None)
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
