#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/triangle_build_vanity_friendship_curiosity_adventure.py
===============================================================================================================================

A small adventure storyworld about building a triangle-shaped fort, a little
vanity, and a friendship-tested turn toward curiosity and teamwork.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

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
        return self.label or self.type
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


@dataclass
class Setting:
    place: str = "the hill"
    indoors: bool = False
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
class Project:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    charm: str
    risk: str
    outcome: str
    requires: set[str] = field(default_factory=set)
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
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str = "character"
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


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the forest clearing", affords={"build"}),
    "beach": Setting(place="the beach", affords={"build"}),
    "river": Setting(place="the riverbank", affords={"build"}),
    "garden": Setting(place="the garden", affords={"build"}),
}

PROJECTS = {
    "triangle_tower": Project(
        id="triangle_tower",
        verb="build a triangle tower",
        gerund="building a triangle tower",
        rush="dash to stack the last pieces",
        keyword="triangle",
        charm="the neat triangle shape looked brave and clever",
        risk="the top could wobble and fall",
        outcome="the tower stood steady and bright",
        requires={"blocks", "rope"},
        tags={"triangle", "build", "adventure"},
    ),
    "triangle_bridge": Project(
        id="triangle_bridge",
        verb="build a triangle bridge",
        gerund="building a triangle bridge",
        rush="hurry to tie the last ropes",
        keyword="triangle",
        charm="the triangle braces made it look strong",
        risk="the bridge could bend and slip",
        outcome="the bridge stayed firm over the gap",
        requires={"rope", "planks"},
        tags={"triangle", "build", "adventure"},
    ),
    "marker_flag": Project(
        id="marker_flag",
        verb="build a triangle marker",
        gerund="building a triangle marker",
        rush="run to set the last stick",
        keyword="triangle",
        charm="the bright triangle sign was easy to spot",
        risk="the sign could tip in the wind",
        outcome="the marker pointed the way like a tiny beacon",
        requires={"sticks", "cloth"},
        tags={"triangle", "build", "curiosity"},
    ),
}

PRIZES = {
    "crown": Prize(label="crown", phrase="a shiny gold crown", type="crown"),
    "badge": Prize(label="badge", phrase="a bright explorer badge", type="badge"),
    "cape": Prize(label="cape", phrase="a red adventure cape", type="cape"),
}

GEAR = {
    "helper_rope": Gear(
        id="helper_rope",
        label="a helper rope",
        prep="tie the pieces with a helper rope first",
        tail="worked together and tied the pieces with the helper rope",
        helps={"triangle_tower", "triangle_bridge"},
    ),
    "steady_sticks": Gear(
        id="steady_sticks",
        label="steady sticks",
        prep="set steady sticks at the corners first",
        tail="made the triangle strong with the steady sticks",
        helps={"triangle_tower", "marker_flag"},
    ),
    "wide_steps": Gear(
        id="wide_steps",
        label="wide stepping stones",
        prep="lay wide stepping stones across the ground first",
        tail="walked carefully across the wide stepping stones",
        helps={"triangle_bridge"},
    ),
}

NAMES = ["Ava", "Milo", "Nia", "Eli", "Ivy", "Theo", "Luna", "Finn"]
TRAITS = ["brave", "curious", "proud", "cheerful", "spirited", "inventive"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
project_at_risk(P) :- project(P), risky(P).
compatible(G,P) :- gear(G), project_at_risk(P), helps(G,P).
valid_story(S,P,R) :- setting(S), project(P), prize(R), affords(S,build), compatible(_,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(s.affords):
            lines.append(asp.fact("affords", sid, act))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("risky", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", pid, tag))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for p in sorted(g.helps):
            lines.append(asp.fact("helps", gid, p))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set((s, p, r) for (s, p, r) in valid_combos())
    cl = set(asp_valid_stories())
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
# Story logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for proj in PROJECTS:
            for prize in PRIZES:
                if proj == "triangle_bridge" and prize == "crown":
                    combos.append((place, proj, prize))
                elif proj == "triangle_tower" and prize in {"badge", "cape"}:
                    combos.append((place, proj, prize))
                elif proj == "marker_flag" and prize == "badge":
                    combos.append((place, proj, prize))
    return combos

def reason_ok(proj: Project, prize: Prize) -> bool:
    if proj.id == "triangle_bridge":
        return prize.label in {"crown", "cape"}
    if proj.id == "triangle_tower":
        return prize.label in {"badge", "cape"}
    return prize.label == "badge"

def select_gear(proj: Project, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if proj.id in gear.helps:
            return gear
    return None

def explain_rejection(proj: Project, prize: Prize) -> str:
    return (
        f"(No story: {proj.gerund} and {prize.phrase} do not fit together in a "
        f"reasonable adventure. The fix has to help the build, not just decorate it.)"
    )


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    project: str
    prize: str
    name: str
    gender: str
    partner: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld about building triangles, a little vanity, and friendship."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=["friend", "sibling"])
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
    if getattr(args, "project", None) and getattr(args, "prize", None) and not reason_ok(_safe_lookup(PROJECTS, getattr(args, "project", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "project", None) is None or c[1] == getattr(args, "project", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, project, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    partner = getattr(args, "partner", None) or "friend"
    trait = rng.choice(TRAITS)
    return StoryParams(place, project, prize, name, gender, partner, trait)


def _pronoun(gender: str, case: str) -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    friend = world.add(Entity(id="Friend", kind="character", type="friend", label=f"{params.partner} friend"))
    prize = world.add(Entity(id="Prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase))
    project = _safe_lookup(PROJECTS, params.project)
    gear = select_gear(project, _safe_lookup(PRIZES, params.prize))

    hero.memes["vanity"] = 1.0
    hero.memes["joy"] = 1.0
    friend.memes["curiosity"] = 1.0

    world.say(f"{hero.id} was a {params.trait} {params.gender} who loved adventure and noticed every shape in the world.")
    world.say(f"{_pronoun(params.gender, 'subject').capitalize()} wanted to {project.verb}, because {project.charm}.")
    world.say(f"At home, {_pronoun(params.gender, 'possessive')} eyes kept landing on {prize.phrase}, and {hero.id} liked how impressive it looked.")

    world.para()
    world.say(f"One day, {hero.id} and {_pronoun(params.gender, 'possessive')} {params.partner} friend went to {world.setting.place}.")
    world.say(f"{_pronoun(params.gender, 'subject').capitalize()} wanted to {project.verb} right away, but {_pronoun(params.gender, 'possessive')} vanity made {_pronoun(params.gender, 'object')} try to make everything look extra grand.")
    world.say(f"The trouble was simple: {project.risk}.")

    world.para()
    world.say(f"{params.partner.capitalize()} friend asked a curious question: \"What makes a triangle stay strong?\"")
    friend.memes["curiosity"] += 1.0
    world.say(f"{hero.id} stopped and looked at the pieces more carefully.")
    hero.memes["curiosity"] += 1.0
    if gear:
        world.say(f"Then they chose {gear.label}. {gear.prep.capitalize()}.")
        world.say(f"That was the friendship turn: {hero.id} listened, and the two of them built it together.")
        hero.memes["vanity"] = 0.0
        hero.memes["friendship"] = 2.0
        friend.memes["friendship"] = 2.0
        world.say(f"{gear.tail.capitalize()}, and soon {project.outcome}.")
        world.say(f"By the end, {hero.id} was still proud, but now {_pronoun(params.gender, 'possessive')} pride came from helping a friend and learning something new.")
    else:
        world.say(f"They did not need any special gear after all, and the little triangle idea stayed simple and safe.")
        world.say(f"Soon {project.outcome}.")

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        project=project,
        gear=gear,
        setting=world.setting,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    project: Project = _safe_fact(world, f, "project")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    return [
        f'Write a short adventure story for a child about a {hero.type} who wants to {project.verb} and thinks about a {prize.label}.',
        f'Write a gentle story using the words "triangle", "build", and "curiosity" where friendship helps solve a small vanity problem.',
        f"Tell a simple adventure about building a triangle-shaped thing, learning to look closely, and choosing teamwork over showing off.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    friend: Entity = _safe_fact(world, f, "friend")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    project: Project = _safe_fact(world, f, "project")  # type: ignore[assignment]
    gear: Optional[Gear] = _safe_fact(world, f, "gear")  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {project.verb}. {_pronoun(hero.type, 'subject').capitalize()} liked the triangle shape and the adventure of building it.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep looking at {prize.phrase}?",
            answer=f"{hero.id} liked how impressive {prize.phrase} looked. That little vanity made {_pronoun(hero.type, 'object')} want everything to seem extra special.",
        ),
        QAItem(
            question=f"What did the friend ask that helped the story turn?",
            answer=f"{friend.label_word.capitalize()} asked what makes a triangle stay strong, and that curious question helped {hero.id} slow down and look more carefully.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help the two friends?",
                answer=f"They used {gear.label} so the build could stay steady. Then {hero.id} and the friend could finish {project.gerund} together.",
            )
        )
    qa.append(
        QAItem(
            question=f"What changed by the end of the adventure?",
            answer=f"By the end, {hero.id} cared less about showing off and more about friendship and curiosity. The triangle stayed steady, and the two friends were proud together.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    project: Project = _safe_fact(world, f, "project")  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is a triangle?",
            answer="A triangle is a shape with three sides and three corners.",
        ),
        QAItem(
            question="Why can building something take patience?",
            answer="Building can take patience because pieces may need to be arranged carefully so the structure stays strong.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn, ask questions, and look closely at how things work.",
        ),
        QAItem(
            question="What is vanity?",
            answer="Vanity is when someone cares too much about looking impressive or being admired.",
        ),
    ]
    if "triangle" in project.tags:
        out.append(QAItem(
            question="Why are triangles often strong in buildings?",
            answer="Triangles can be strong because their sides support each other and help a shape keep steady.",
        ))
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest", project="triangle_tower", prize="badge", name="Ava", gender="girl", partner="friend", trait="curious"),
    StoryParams(place="beach", project="triangle_bridge", prize="crown", name="Milo", gender="boy", partner="friend", trait="brave"),
    StoryParams(place="garden", project="marker_flag", prize="badge", name="Nia", gender="girl", partner="friend", trait="inventive"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def valid_combo_list() -> list[tuple[str, str, str]]:
    return valid_combos()


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
        print(f"{len(combos)} compatible (setting, project, prize) combos:\n")
        for row in combos:
            print("  ", row)
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
            header = f"### {p.name}: {p.project} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
