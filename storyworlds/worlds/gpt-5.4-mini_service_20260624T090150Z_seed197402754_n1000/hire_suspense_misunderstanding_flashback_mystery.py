#!/usr/bin/env python3
"""
A small mystery storyworld about hiring a helper, a suspenseful search, a
misunderstanding, and a flashback that reveals the clue.

Premise:
- A worried child or grown-up hires a helper to solve a small missing-object mystery.
- Suspense grows while the search goes on.
- A misunderstanding makes the search feel worse.
- A flashback reveals what really happened.
- The helper uses the remembered clue to solve the mystery.

This world is intentionally compact and classical:
- one setting
- one mystery object
- one hired helper
- one misunderstanding
- one flashback reveal
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    label: str
    detail: str
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


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    hiding_place: str
    clue: str
    flashback_line: str
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
class Hire:
    id: str
    label: str
    type: str
    method: str
    tool: str
    title: str = "helper"
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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

    def debug(self) -> str:
        lines = [f"setting: {self.place.label}"]
        for e in self.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            lines.append(
                f"{e.id}: kind={e.kind} type={e.type} label={e.label} "
                f"meters={meters} memes={memes}"
            )
        lines.append(f"facts: {self.facts}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "library": Place(
        id="library",
        label="the little library",
        detail="Tall shelves made quiet shadows between the rows of books.",
    ),
    "museum": Place(
        id="museum",
        label="the museum hall",
        detail="Glass cases and polished floors made every step sound small.",
    ),
    "station": Place(
        id="station",
        label="the train station",
        detail="A bright clock ticked over the bench where people waited.",
    ),
}

MYSTERIES = {
    "bookmark": Mystery(
        id="bookmark",
        label="a red bookmark",
        phrase="a thin red bookmark with a gold tassel",
        hiding_place="under a heavy book",
        clue="the tassel was caught on a shelf edge",
        flashback_line="The child remembered leaning over a shelf and brushing something red out of sight.",
    ),
    "key": Mystery(
        id="key",
        label="a brass key",
        phrase="a small brass key on a blue ribbon",
        hiding_place="behind a potted plant",
        clue="a blue ribbon thread was stuck on the plant pot",
        flashback_line="The child remembered the ribbon slipping off while they hurried past the doorway.",
    ),
    "toy": Mystery(
        id="toy",
        label="a tiny toy train",
        phrase="a tiny green toy train with one silver wheel",
        hiding_place="inside a display crate",
        clue="one wheel mark matched a dusty crate corner",
        flashback_line="The child remembered rolling the toy into a crate during a quick game of hide-and-seek.",
    ),
}

HIRE_HELPERS = {
    "detective": Hire(
        id="detective",
        label="a detective",
        type="detective",
        method="careful questions and slow walking",
        tool="a small magnifying glass",
    ),
    "helper": Hire(
        id="helper",
        label="a helper",
        type="helper",
        method="quiet looking and gentle hints",
        tool="a flashlight",
    ),
}

NAMES = {
    "child": ["Milo", "Nina", "Tia", "Eli", "June", "Pip"],
    "adult": ["Mrs. Lane", "Mr. Finch", "Aunt Rosa", "Uncle Ben"],
}

CHILD_TYPES = ["boy", "girl"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    hire: str
    name: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
% A mystery is solvable when a clue exists for the hidden object.
solvable(M) :- mystery(M), clue(M, _).

% A hire is reasonable when the helper's method is suitable for careful search.
good_hire(H) :- hire(H), careful(H).

% Valid stories need a place, a solvable mystery, and a reasonable helper.
valid_story(P, M, H) :- place(P), mystery(M), hire(H), solvable(M), good_hire(H).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("detail", pid, place.detail))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
    for hid, h in HIRE_HELPERS.items():
        lines.append(asp.fact("hire", hid))
        lines.append(asp.fact("careful", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    triples = set(asp_valid_stories())
    python = set(valid_combos())
    if triples == python:
        print(f"OK: clingo gate matches valid_combos() ({len(triples)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if triples - python:
        print("  only in clingo:", sorted(triples - python))
    if python - triples:
        print("  only in python:", sorted(python - triples))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for m in MYSTERIES:
            for h in HIRE_HELPERS:
                out.append((p, m, h))
    return out


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def opening(world: World, child: Entity, adult: Entity, mystery: Mystery) -> None:
    world.say(
        f"In {world.place.label}, {child.id} and {adult.label} noticed that "
        f"{mystery.phrase} had gone missing."
    )
    world.say(world.place.detail)
    child.memes["worry"] += 1
    adult.memes["worry"] += 1


def hire_helper(world: World, adult: Entity, helper: Entity, mystery: Mystery) -> None:
    adult.memes["hope"] += 1
    world.say(
        f"After a worried pause, {adult.label} hired {helper.label} to help look for "
        f"{mystery.label}."
    )
    world.say(
        f"{helper.label.capitalize()} came at once with {world.facts['tool']} and a calm voice."
    )


def suspense_search(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["suspense"] += 1
    helper.meters["search_steps"] = helper.meters.get("search_steps", 0) + 1
    world.say(
        f"They searched slowly. Every creak of the floor sounded louder than usual, "
        f"and every shelf looked a little secret."
    )
    world.say(
        f"{helper.label.capitalize()} looked under a bench, behind a stack, and near the dark corners."
    )


def misunderstanding(world: World, child: Entity, adult: Entity, helper: Entity) -> None:
    child.memes["fear"] += 1
    adult.memes["fear"] += 1
    world.say(
        f"Then came a misunderstanding: {child.id} saw {helper.label} reach for a dusty crate "
        f"and thought {helper.pronoun('subject')} had found something wrong."
    )
    world.say(
        f"But {helper.label} only wanted to check the clue more closely."
    )


def flashback(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["memory"] += 1
    world.say(
        f"That made {child.id} stop and think. A flashback flickered through {child.id}'s mind."
    )
    world.say(f"{mystery.flashback_line}")


def solve(world: World, child: Entity, adult: Entity, helper: Entity, mystery: Mystery) -> None:
    adult.memes["relief"] += 1
    child.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"At last, the clue made sense. {helper.label} followed it to {mystery.hiding_place} "
        f"and found {mystery.phrase} waiting there."
    )
    world.say(
        f"{child.id} laughed with relief, and {adult.label} thanked {helper.label} for the careful help."
    )
    world.say(
        f"By the end, the mystery was solved, the room felt bright again, and {mystery.label} was safely back where it belonged."
    )


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------
def valid_story_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.mystery not in MYSTERIES:
        pass
    if params.hire not in HIRE_HELPERS:
        pass


def generate_world(params: StoryParams) -> World:
    valid_story_params(params)
    world = World(_safe_lookup(PLACES, params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.role))
    adult = world.add(Entity(id="adult", kind="character", type="adult", label="the grown-up"))
    helper_def = _safe_lookup(HIRE_HELPERS, params.hire)
    helper = world.add(Entity(id=helper_def.id, kind="character", type=helper_def.type, label=helper_def.label))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world.facts = {
        "tool": helper_def.tool,
        "method": helper_def.method,
        "mystery": mystery,
        "helper": helper_def,
        "child": child,
        "adult": adult,
    }

    opening(world, child, adult, mystery)
    world.para()
    hire_helper(world, adult, helper, mystery)
    suspense_search(world, child, helper, mystery)
    world.para()
    misunderstanding(world, child, adult, helper)
    flashback(world, child, mystery)
    solve(world, child, adult, helper, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    m: Mystery = _safe_fact(world, world.facts, "mystery")
    h: Hire = _safe_fact(world, world.facts, "helper")
    child: Entity = _safe_fact(world, world.facts, "child")
    return [
        f"Write a short mystery story for children that includes hiring {h.label} to find {m.label}.",
        f"Tell a suspenseful but gentle story about {child.id}, a missing {m.label}, and a careful helper.",
        f"Write a mystery story where a misunderstanding leads to a flashback that reveals where {m.label} is hiding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m: Mystery = _safe_fact(world, world.facts, "mystery")
    h: Hire = _safe_fact(world, world.facts, "helper")
    child: Entity = _safe_fact(world, world.facts, "child")
    adult: Entity = _safe_fact(world, world.facts, "adult")
    return [
        QAItem(
            question=f"What did {adult.label} hire {h.label} to do?",
            answer=f"{adult.label.capitalize()} hired {h.label} to help search for {m.label}.",
        ),
        QAItem(
            question=f"What made the search feel suspenseful?",
            answer="The search felt suspenseful because they looked slowly, listened to every little sound, and did not know where the missing thing had been hidden.",
        ),
        QAItem(
            question=f"What was the misunderstanding in the story?",
            answer=f"{child.id} saw {h.label} reaching toward a dusty crate and thought the helper had found something bad, but the helper was only checking the clue.",
        ),
        QAItem(
            question=f"What did the flashback help {child.id} remember?",
            answer=f"The flashback helped {child.id} remember the moment when {m.label} was brushed out of sight during a quick move near the shelf.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{h.label.capitalize()} followed the clue and found {m.phrase}, so the mystery was solved and everyone felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    m: Mystery = _safe_fact(world, world.facts, "mystery")
    h: Hire = _safe_fact(world, world.facts, "helper")
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something that happened earlier, so the reader can understand what is going on now.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling that something important is about to happen, so you keep wondering what will come next.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is a clue?",
            answer=f"A clue is a small hint that helps solve a mystery, like {m.clue}.",
        ),
        QAItem(
            question="Why do people hire helpers?",
            answer=f"People hire helpers when they need support, time, or special skills, like careful searching and calm thinking.",
        ),
        QAItem(
            question="Why do mysteries often use clues?",
            answer="Mysteries use clues because clues give the characters a way to figure out what really happened.",
        ),
        QAItem(
            question="What does careful searching mean?",
            answer=f"Careful searching means looking slowly and paying attention to details, which is exactly how {h.label} worked in the story.",
        ),
    ]


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
    return world.debug()


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with hire, suspense, misunderstanding, and flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hire", choices=HIRE_HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=CHILD_TYPES)
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
    valid = valid_combos()
    chosen = []
    for p, m, h in valid:
        if getattr(args, "place", None) and p != getattr(args, "place", None):
            continue
        if getattr(args, "mystery", None) and m != getattr(args, "mystery", None):
            continue
        if getattr(args, "hire", None) and h != getattr(args, "hire", None):
            continue
        chosen.append((p, m, h))
    if not chosen:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, hire = rng.choice(sorted(chosen))
    role = getattr(args, "role", None) or rng.choice(CHILD_TYPES)
    name = getattr(args, "name", None) or rng.choice(NAMES["child"])
    return StoryParams(place=place, mystery=mystery, hire=hire, name=name, role=role)


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
    StoryParams(place="library", mystery="bookmark", hire="detective", name="Milo", role="boy"),
    StoryParams(place="museum", mystery="key", hire="helper", name="Nina", role="girl"),
    StoryParams(place="station", mystery="toy", hire="detective", name="Tia", role="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, mystery, hire) combos:\n")
        for p, m, h in stories:
            print(f"  {p:8} {m:9} {h}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
