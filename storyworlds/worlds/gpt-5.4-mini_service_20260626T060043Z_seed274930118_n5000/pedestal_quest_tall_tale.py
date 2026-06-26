#!/usr/bin/env python3
"""
A standalone story world for a Tall Tale quest about a pedestal.

The seed image: a small town with a stubborn child, a grand pedestal, and a
quest that feels bigger than the sky. The simulation keeps the story concrete:
someone wants to place a treasure on a pedestal, the journey strains the body
and the nerves, and a clever helper turns trouble into triumph.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    placed_on: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    grownup: object | None = None
    hero: object | None = None
    prize: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    id: str
    name: str
    inside: bool = False
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Quest:
    id: str
    goal: str
    peril: str
    stride: str
    turn: str
    finish: str
    scale: str
    required_place: str = ""
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
class Treasure:
    id: str
    label: str
    phrase: str
    size: str
    weight: str
    pedestal_fit: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Aid:
    id: str
    label: str
    phrase: str
    power: str
    covers: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.quest_started = False
        self.quest_failed = False
        self.quest_done = False
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "town_square": Place(id="town_square", name="the town square", affords={"quest"}),
    "river_road": Place(id="river_road", name="the river road", affords={"quest"}),
    "hayfield": Place(id="hayfield", name="the hayfield", affords={"quest"}),
}

QUESTS = {
    "pedestal_quest": Quest(
        id="pedestal_quest",
        goal="carry the town's prize to the pedestal",
        peril="the prize is too awkward to haul alone",
        stride="marching like a parade drum in boots",
        turn="a rolling wagon and a clever rope trick",
        finish="the prize stood where the sun could salute it",
        scale="tall",
        required_place="town_square",
        tags={"pedestal", "quest"},
    )
}

TREASURES = {
    "star": Treasure(
        id="star",
        label="gold star",
        phrase="a bright gold star with a shine like morning",
        size="hand-sized",
        weight="surprisingly heavy",
    ),
    "bell": Treasure(
        id="bell",
        label="brass bell",
        phrase="a brass bell that could sing clear across a field",
        size="basket-sized",
        weight="heavy",
    ),
    "crown": Treasure(
        id="crown",
        label="paper crown",
        phrase="a paper crown painted with red and blue swirls",
        size="light",
        weight="light as a feather",
    ),
}

AIDS = {
    "wagon": Aid(
        id="wagon",
        label="wagon",
        phrase="a red wagon with squeaky wheels",
        power="rolling heavy things",
        covers={"carry"},
        tags={"quest"},
    ),
    "rope": Aid(
        id="rope",
        label="rope",
        phrase="a long rope with a good knot",
        power="pulling and guiding",
        covers={"lift"},
        tags={"quest"},
    ),
    "stepstool": Aid(
        id="stepstool",
        label="stepstool",
        phrase="a wooden stepstool with three brave steps",
        power="reaching high places",
        covers={"reach"},
        tags={"pedestal"},
    ),
}

GIRL_NAMES = ["Mina", "Ruby", "Tess", "Della", "Nora"]
BOY_NAMES = ["Jeb", "Otis", "Walt", "Benn", "Clive"]
TRAITS = ["sturdy", "plucky", "cheerful", "mighty", "curious"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    treasure: str
    aid: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
    p: object | None = None
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


ASP_RULES = r"""
quest_ready(P, Q, T) :- place(P), quest(Q), treasure(T), can_start(Q, P), goal(Q, T).
needs_aid(Q, A) :- quest(Q), aid(A), helps(A, Q).
valid_story(P, Q, T, A) :- quest_ready(P, Q, T), needs_aid(Q, A), compatible(P, Q, T, A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.inside:
            lines.append(asp.fact("inside", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("goal", qid, q.id))
        lines.append(asp.fact("can_start", qid, q.required_place or "town_square"))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("goal", "pedestal_quest", tid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("helps", aid, "pedestal_quest"))
        lines.append(asp.fact("compatible", "town_square", "pedestal_quest", "star", aid))
        lines.append(asp.fact("compatible", "town_square", "pedestal_quest", "bell", aid))
        lines.append(asp.fact("compatible", "town_square", "pedestal_quest", "crown", aid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: Place, quest: Quest, treasure: Treasure, aid: Aid) -> bool:
    if place.id != quest.required_place:
        return False
    if quest.id != "pedestal_quest":
        return False
    if "quest" not in place.affords:
        return False
    if treasure.label == "paper crown" and aid.id == "wagon":
        return False
    return True

def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for qid, q in QUESTS.items():
            for tid, t in TREASURES.items():
                for aid, a in AIDS.items():
                    if valid_combo(p, q, t, a):
                        out.append((pid, qid, tid, aid))
    return out

def explain_rejection(place: Place, quest: Quest, treasure: Treasure, aid: Aid) -> str:
    if place.id != quest.required_place:
        return "(No story: this quest belongs in the town square, where the pedestal stands."
    if treasure.label == "paper crown" and aid.id == "wagon":
        return "(No story: a paper crown does not need a wagon, and a wagon cannot help a tiny crown climb a pedestal.)"
    return "(No story: that combination does not fit the quest well enough.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

def tell(place: Place, quest: Quest, treasure: Treasure, aid: Aid,
         name: str, gender: str, parent: str, trait: str) -> World:
    w = World(place)
    hero = w.add(Entity(id=name, kind="character", type=gender, meters={"tired": 0.0}, memes={"hope": 0.0}))
    grownup = w.add(Entity(id="grownup", kind="character", type=parent, label=f"the {parent}"))
    prize = w.add(Entity(
        id=treasure.id,
        kind="thing",
        type=treasure.label,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=hero.id,
        caretaker=grownup.id,
    ))
    tool = w.add(Entity(
        id=aid.id,
        kind="thing",
        type=aid.label,
        label=aid.label,
        phrase=aid.phrase,
        owner=hero.id,
        caretaker=grownup.id,
    ))

    # Act 1
    w.say(f"{name} was a {trait} little {gender} who could spot a hard road from a mile away.")
    w.say(f"{hero.pronoun().capitalize()} had a quest as tall as a chimney: {quest.goal}.")
    w.say(f"The town had given {hero.pronoun('object')} {prize.phrase}, and everybody said it belonged on the pedestal.")
    w.para()

    # Act 2
    w.say(f"One bright day, {name} marched to {place.name} with {quest.stride}.")
    hero.memes["hope"] += 1.0
    hero.meters["carried"] = 1.0
    w.say(f"But the prize was {treasure.weight}, and by the time {name} reached the square, {hero.pronoun()} was puffing like a kettle.")
    hero.meters["tired"] += 1.0
    w.say(f"{grownup.label} warned, \"That {treasure.label} is too awkward to haul alone, and the pedestal stands too high for a wobble.\"")
    w.say(f"{name} tried anyway, but the wind gave the prize a twist and the whole plan looked as crooked as a hound's grin.")
    w.para()

    # Turn
    w.say(f"Then {name} spied {tool.phrase}. That was the turn in the trail.")
    w.say(f"{grownup.label} said, \"We can use the {tool.label} for {aid.power}, and the quest can still end proud.\"")
    tool.meters["used"] = 1.0
    hero.memes["hope"] += 1.0
    hero.meters["tired"] += 0.5
    w.say(f"So they tied the rope, rolled the wagon, and gave the job enough help to move a barn if it had to.")
    w.para()

    # Resolution
    prize.carried_by = hero.id
    prize.placed_on = "pedestal"
    hero.meters["tired"] += 0.5
    hero.memes["joy"] = 2.0
    w.quest_done = True
    w.say(f"At last {name} climbed the last step and set the {prize.label} on the pedestal.")
    w.say(f"The whole square seemed to lean in and admire it. Even the pigeons looked proper and polite.")
    w.say(f"{quest.finish.capitalize()}, and {name} stood grinning so wide it nearly split the morning in two.")

    w.facts.update(
        hero=hero,
        grownup=grownup,
        prize=prize,
        tool=tool,
        quest=quest,
        place=place,
        treasure=treasure,
        aid=aid,
        resolved=True,
    )
    return w


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    return [
        f"Write a tall tale about {hero.id} and a pedestal quest in {f['place'].name}.",
        f"Tell a child-friendly story where someone needs {f['treasure'].label} on a pedestal but cannot do it alone.",
        f"Write a grand, funny story that includes a pedestal, a quest, and a helper tool.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    quest = _safe_fact(world, f, "quest")
    place = _safe_fact(world, f, "place")
    grownup = _safe_fact(world, f, "grownup")
    return [
        QAItem(
            question=f"What was {hero.id}'s quest?",
            answer=f"{hero.id}'s quest was to {quest.goal}.",
        ),
        QAItem(
            question=f"Why did {grownup.label} worry about the trip to {place.name}?",
            answer=f"{grownup.label} worried because the {prize.label} was {f['treasure'].weight} and the pedestal stood too high for a shaky climb.",
        ),
        QAItem(
            question=f"What helped {hero.id} finish the quest?",
            answer=f"The {tool.label} helped because it made the heavy job easier, and the rope and wagon kept the prize steady.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"By the end, the {prize.label} stood on the pedestal, and {hero.id} felt proud instead of worn out.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pedestal?",
            answer="A pedestal is a stand or base that holds something up so people can see it better.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a big mission or journey to get something done, often with trouble along the way.",
        ),
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


# ---------------------------------------------------------------------------
# Params resolution / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale pedestal quest storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--aid", choices=AIDS)
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
    place = _safe_lookup(PLACES, getattr(args, "place", None)) if getattr(args, "place", None) else rng.choice(list(PLACES.values()))
    quest = _safe_lookup(QUESTS, getattr(args, "quest", None)) if getattr(args, "quest", None) else QUESTS["pedestal_quest"]
    treasure = _safe_lookup(TREASURES, getattr(args, "treasure", None)) if getattr(args, "treasure", None) else rng.choice(list(TREASURES.values()))
    aid = _safe_lookup(AIDS, getattr(args, "aid", None)) if getattr(args, "aid", None) else rng.choice(list(AIDS.values()))
    if not valid_combo(place, quest, treasure, aid):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = choose_name(gender, rng)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place.id,
        quest=quest.id,
        treasure=treasure.id,
        aid=aid.id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    treasure = _safe_lookup(TREASURES, params.treasure)
    aid = _safe_lookup(AIDS, params.aid)
    world = tell(place, quest, treasure, aid, params.name, params.gender, params.parent, params.trait)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.placed_on:
                bits.append(f"placed_on={e.placed_on}")
            if e.carried_by:
                bits.append(f"carried_by={e.carried_by}")
            print(f"  {e.id} ({e.type}) {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for pid, qid, tid, aid in valid_combos():
            p = StoryParams(
                place=pid,
                quest=qid,
                treasure=tid,
                aid=aid,
                name=choose_name("girl", random.Random(base_seed)),
                gender="girl",
                parent="mother",
                trait="plucky",
                seed=base_seed,
            )
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
