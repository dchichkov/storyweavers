#!/usr/bin/env python3
"""
storyworlds/worlds/fund_curiosity_comedy.py
===========================================

A tiny story world about a curious child, a community fund, and a comic
misunderstanding that turns into a cheerful fix.

The seed premise:
- A small fund is set aside for something fun and useful.
- A curious child wants to look inside or help count it.
- A mix-up creates a humorous problem.
- The child and an adult resolve it with a simple plan.

The world model tracks:
- Physical meters: money, mess, signs, and object state.
- Emotional memes: curiosity, worry, embarrassment, delight, relief.

This world is intentionally small and constraint-driven so the story stays
plausible and child-facing.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    fund: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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


@dataclass
class Setting:
    place: str
    kind: str = "room"
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
class Fund:
    id: str
    label: str
    purpose: str
    container: str
    stored_place: str
    value_range: tuple[int, int]
    can_be_misread_as: str
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
class Mischief:
    id: str
    verb: str
    action: str
    accident: str
    comic_twist: str
    risk: str
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


@dataclass
class Fix:
    id: str
    label: str
    plan: str
    result: str
    protects_from: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    setting: str
    fund: str
    mischief: str
    fix: str
    name: str
    gender: str
    adult: str
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


SETTINGS = {
    "school_office": Setting(place="the school office", kind="room", affords={"count", "label", "sort"}),
    "library_desk": Setting(place="the library desk", kind="room", affords={"count", "label"}),
    "club_room": Setting(place="the club room", kind="room", affords={"count", "sort", "decorate"}),
}

FUNDS = {
    "field_trip": Fund(
        id="field_trip",
        label="field trip fund",
        purpose="a class trip to the science museum",
        container="a blue jar with a brass lid",
        stored_place="on the high shelf",
        value_range=(8, 24),
        can_be_misread_as="a cookie jar",
        tags={"money", "trip", "jar"},
    ),
    "pet_day": Fund(
        id="pet_day",
        label="pet day fund",
        purpose="snacks and ribbons for pet day",
        container="a clear tin box",
        stored_place="behind the sign-up sheets",
        value_range=(6, 18),
        can_be_misread_as="a lunch box",
        tags={"money", "pet", "box"},
    ),
    "stage_show": Fund(
        id="stage_show",
        label="stage show fund",
        purpose="paper stars and a tiny curtain",
        container="a striped cash box",
        stored_place="inside the cabinet",
        value_range=(10, 30),
        can_be_misread_as="a toy box",
        tags={"money", "show", "box"},
    ),
}

MISCHIEF = {
    "peek": Mischief(
        id="peek",
        verb="peek at",
        action="tiptoe up to",
        accident="he would only take a tiny peek",
        comic_twist="the lid made a loud squeak like a squeaky duck",
        risk="someone might think the fund was being stolen",
        tags={"curiosity", "peek", "squeak"},
    ),
    "count": Mischief(
        id="count",
        verb="count",
        action="carefully count",
        accident="he would only check the totals",
        comic_twist="he counted with his tongue out and looked very serious",
        risk="he might mix up the coins and make a funny mess of numbers",
        tags={"curiosity", "count"},
    ),
    "label": Mischief(
        id="label",
        verb="label",
        action="put new labels on",
        accident="he would only help make things neat",
        comic_twist="he used stickers so big they looked like hats for the boxes",
        risk="he might put the wrong sign on the wrong thing",
        tags={"curiosity", "label", "sticker"},
    ),
    "sort": Mischief(
        id="sort",
        verb="sort",
        action="sort out",
        accident="he would only make the shelf tidy",
        comic_twist="he sorted by color and then by how silly the boxes looked",
        risk="he might hide the fund behind the wrong pile",
        tags={"curiosity", "sort"},
    ),
}

FIXES = {
    "ledger": Fix(
        id="ledger",
        label="the ledger",
        plan="count the coins together from the ledger and the jar",
        result="the numbers make sense again",
        protects_from={"count", "peek"},
    ),
    "labels": Fix(
        id="labels",
        label="big stickers",
        plan="put clear labels on every box and jar",
        result="nobody mistakes the fund for snacks or toys anymore",
        protects_from={"label", "sort"},
    ),
    "tray": Fix(
        id="tray",
        label="a tray",
        plan="move the fund to a tray on the desk while they sort the shelf",
        result="the money stays safe and easy to see",
        protects_from={"sort", "peek"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Tess", "June", "Ivy"]
BOY_NAMES = ["Leo", "Max", "Ben", "Finn", "Theo", "Sam", "Noah", "Jules"]
TRAITS = ["curious", "cheerful", "bouncy", "bright-eyed", "sly", "giggle-prone"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A curious comedy about a small fund and a comic fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fund", choices=FUNDS)
    ap.add_argument("--mischief", choices=MISCHIEF)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=["teacher", "librarian", "coach"])
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


def _adult_label(kind: str) -> str:
    return {"teacher": "the teacher", "librarian": "the librarian", "coach": "the coach"}[kind]


def _fund_at_risk(mischief: Mischief, fund: Fund) -> bool:
    return True if mischief.id in {"peek", "count", "sort", "label"} else False


def _compatible_fix(mischief: Mischief, fix: Fix) -> bool:
    return mischief.id in fix.protects_from


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for f in FUNDS:
            for m in MISCHIEF:
                for x in FIXES:
                    if _fund_at_risk(MISCHIEF[m], _safe_lookup(FUNDS, f)) and _compatible_fix(MISCHIEF[m], _safe_lookup(FIXES, x)):
                        out.append((s, f, m, x))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "mischief", None) and getattr(args, "fix", None):
        if not _compatible_fix(MISCHIEF[getattr(args, "mischief", None)], _safe_lookup(FIXES, getattr(args, "fix", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "fund", None) is None or c[1] == getattr(args, "fund", None))
        and (getattr(args, "mischief", None) is None or c[2] == getattr(args, "mischief", None))
        and (getattr(args, "fix", None) is None or c[3] == getattr(args, "fix", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, fund, mischief, fix = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = getattr(args, "adult", None) or rng.choice(["teacher", "librarian", "coach"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting, fund, mischief, fix, name, gender, adult, trait)


ASP_RULES = r"""
fund_risk(M,F) :- mischief(M), fund(F).
fixes(M,X) :- mischief(M), fix(X), compatible(M,X).
valid_story(S,F,M,X) :- setting(S), fund(F), mischief(M), fix(X), fund_risk(M,F), fixes(M,X).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for f in FUNDS:
        lines.append(asp.fact("fund", f))
    for m in MISCHIEF:
        lines.append(asp.fact("mischief", m))
    for x in FIXES:
        lines.append(asp.fact("fix", x))
    for m in MISCHIEF:
        for x in FIXES:
            if _compatible_fix(MISCHIEF[m], _safe_lookup(FIXES, x)):
                lines.append(asp.fact("compatible", m, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def _intro(world: World, hero: Entity, adult: Entity, fund: Entity, trait: str) -> None:
    world.say(
        f"{hero.id} was a {trait} {hero.type} who liked asking questions about everything."
    )
    world.say(
        f"At {world.setting.place}, {hero.id} kept noticing {fund.label} and wondering what was inside."
    )
    world.say(
        f"{adult.label} watched over {fund.label}, because it was for {fund.phrase}."
    )


def _setup(world: World, hero: Entity, fund: Entity, mischief: Mischief) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} wanted to {mischief.verb} the {fund.label} because curiosity itched in {hero.pronoun('possessive')} head."
    )
    world.say(
        f"{hero.pronoun().capitalize()} said {mischief.accident}, which sounded harmless enough."
    )


def _conflict(world: World, hero: Entity, adult: Entity, fund: Entity, mischief: Mischief) -> None:
    hero.memes["worry"] += 1
    adult.memes["worry"] += 1
    hero.memes["embarrassment"] += 1
    world.say(
        f"But then {mischief.comic_twist}, and {adult.label} looked over with a surprised face."
    )
    world.say(
        f'"Please do not make the {fund.label} look odd," {adult.pronoun("subject")} said, because {mischief.risk}.'
    )


def _fix(world: World, hero: Entity, adult: Entity, fund: Entity, fix: Fix) -> None:
    hero.memes["relief"] += 1
    adult.memes["relief"] += 1
    world.say(
        f"Then {adult.label} smiled and suggested {fix.label}: {fix.plan}."
    )
    world.say(
        f"{hero.id} helped right away, and soon {fix.result}."
    )
    world.say(
        f"In the end, {fund.label} stayed safe, and the room looked tidier than a toy shelf after a very serious giggle."
    )


def generate_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult, label=_adult_label(params.adult)))
    fund = world.add(Entity(id="fund", type="fund", label=_safe_lookup(FUNDS, params.fund).label, phrase=_safe_lookup(FUNDS, params.fund).purpose))
    mischief = MISCHIEF[params.mischief]
    fix = _safe_lookup(FIXES, params.fix)
    world.facts.update(hero=hero, adult=adult, fund=fund, mischief=mischief, fix=fix, params=params)

    _intro(world, hero, adult, fund, params.trait)
    world.para()
    _setup(world, hero, fund, mischief)
    _conflict(world, hero, adult, fund, mischief)
    world.para()
    _fix(world, hero, adult, fund, fix)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    fund = _safe_lookup(FUNDS, p.fund)
    mis = MISCHIEF[p.mischief]
    return [
        f"Write a funny short story about a curious child and a {fund.label}.",
        f"Tell a comedy story where {p.name} wants to {mis.verb} a fund, but an adult helps with a better plan.",
        f"Make a child-friendly story about a small fund for {fund.purpose} and a harmless misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    adult: Entity = _safe_fact(world, world.facts, "adult")
    fund: Entity = _safe_fact(world, world.facts, "fund")
    mis = _safe_fact(world, world.facts, "mischief")
    fix = _safe_fact(world, world.facts, "fix")
    return [
        QAItem(
            question=f"Why did {hero.id} want to look at the {fund.label}?",
            answer=f"{hero.id} was curious and wanted to {mis.verb} it, because curiosity kept tugging at {hero.pronoun('possessive')} thoughts.",
        ),
        QAItem(
            question=f"What made {adult.label} worry about the {fund.label}?",
            answer=f"{adult.label} worried because the comic mishap could make the fund look strange and confuse everyone about what it was for.",
        ),
        QAItem(
            question=f"How did they fix the problem with the {fund.label}?",
            answer=f"They used {fix.label} and followed the plan to {fix.plan}, which kept the fund safe and made the room easy to understand again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    fund = _safe_lookup(FUNDS, p.fund)
    out = [
        QAItem(
            question="What is a fund?",
            answer="A fund is money set aside for a particular purpose, like a trip, a project, or a special event.",
        ),
        QAItem(
            question="Why do people label boxes and jars?",
            answer="People use labels so they can tell one thing from another quickly and avoid silly mix-ups.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
        ),
    ]
    if "money" in fund.tags:
        out.append(QAItem(
            question="Why is it smart to keep fund money safe?",
            answer="It is smart to keep fund money safe so it can be used later for the thing it was saved for.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(setting="school_office", fund="field_trip", mischief="peek", fix="ledger", name="Mia", gender="girl", adult="teacher", trait="curious"),
    StoryParams(setting="library_desk", fund="pet_day", mischief="count", fix="ledger", name="Leo", gender="boy", adult="librarian", trait="giggle-prone"),
    StoryParams(setting="club_room", fund="stage_show", mischief="label", fix="labels", name="Nora", gender="girl", adult="coach", trait="bouncy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
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
            header = f"### {p.name}: {p.fund} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
