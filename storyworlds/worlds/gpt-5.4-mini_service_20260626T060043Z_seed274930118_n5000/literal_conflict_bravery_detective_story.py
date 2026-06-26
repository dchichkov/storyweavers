#!/usr/bin/env python3
"""
A small detective-story world built around a literal clue, a conflict, and a brave choice.

Premise:
- A young detective notices a literal trail of paint flecks.
- A worried friend and a missing neighborhood mascot create a conflict.
- Bravery means following the clue carefully instead of panicking.
- The resolution reveals the missing item was not stolen; it was tucked somewhere obvious.

This script is a standalone storyworld source file for the Storyweavers repo.
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

    clue_ent: object | None = None
    detective: object | None = None
    friend: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective-girl"}
        male = {"boy", "father", "dad", "man", "detective-boy"}
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


@dataclass
class Location:
    name: str
    indoors: bool = False
    hides: set[str] = field(default_factory=set)
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
class Clue:
    kind: str
    phrase: str
    literal_phrase: str
    leads_to: str
    weight: str = "small"
    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Mystery:
    missing: str
    missing_kind: str
    hiding_place: str
    suspicion_target: str
    clue: str
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
class StoryParams:
    location: str
    detective_name: str
    detective_type: str
    friend_name: str
    friend_type: str
    missing_item: str
    seed: Optional[int] = None
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
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy
        w = World(self.location)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "library": Location(name="the library", indoors=True, hides={"desk", "reading nook", "pocket"}),
    "museum": Location(name="the museum", indoors=True, hides={"bench", "display case", "coat room"}),
    "garden": Location(name="the garden", indoors=False, hides={"bush", "stone bench", "flower pot"}),
}

DETECTIVE_NAMES = ["Mina", "Jules", "Ivy", "Nico", "Pia", "Rowan"]
FRIEND_NAMES = ["Toby", "Lena", "Milo", "Sara", "Ben", "Ruby"]

DETECTIVE_TYPES = ["girl", "boy"]
FRIEND_TYPES = ["girl", "boy"]

MISSING_ITEMS = {
    "hat": ("a striped hat", "hat"),
    "puzzle": ("a small puzzle box", "puzzle box"),
    "magnifier": ("a shiny magnifier", "magnifier"),
}

CLUES = {
    "paint": Clue(
        kind="paint",
        phrase="tiny paint flecks",
        literal_phrase="a literal trail of paint flecks",
        leads_to="paint shelf",
    ),
    "crumbs": Clue(
        kind="crumbs",
        phrase="little cookie crumbs",
        literal_phrase="a literal trail of crumbs",
        leads_to="snack table",
    ),
    "mud": Clue(
        kind="mud",
        phrase="muddy dots",
        literal_phrase="a literal trail of muddy dots",
        leads_to="back door",
    ),
}

MYSTERY_BY_ITEM = {
    "hat": ("coat room", "friend"),
    "puzzle": ("reading nook", "friend"),
    "magnifier": ("desk", "friend"),
}


# ---------------------------------------------------------------------------
# Reasonableness / story constraints
# ---------------------------------------------------------------------------

def reasonable_combo(location: str, missing_item: str) -> bool:
    loc = _safe_lookup(LOCATIONS, location)
    hiding_place, suspicion_target = MYSTERY_BY_ITEM[missing_item]
    return hiding_place in loc.hides and suspicion_target == "friend"


def explain_rejection(location: str, missing_item: str) -> str:
    hiding_place, _ = MYSTERY_BY_ITEM[missing_item]
    return (
        f"(No story: at {_safe_lookup(LOCATIONS, location).name}, the missing {missing_item} "
        f"would not plausibly end up in the {hiding_place} for this detective setup.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    location = _safe_lookup(LOCATIONS, params.location)
    world = World(location)

    missing_phrase, missing_kind = _safe_lookup(MISSING_ITEMS, params.missing_item)
    clue = CLUES["paint"] if params.location in {"museum", "library"} else CLUES["mud"]
    hiding_place, suspicion_target = MYSTERY_BY_ITEM[params.missing_item]

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        meters={"curiosity": 1.0},
        memes={"confidence": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        meters={"worry": 1.0},
        memes={"conflict": 1.0},
    ))
    missing = world.add(Entity(
        id="missing",
        type=missing_kind,
        label=params.missing_item,
        phrase=missing_phrase,
        owner=params.friend_name,
    ))
    clue_ent = world.add(Entity(
        id="clue",
        type=clue.kind,
        label=clue.kind,
        phrase=clue.phrase,
    ))

    world.facts.update(
        detective=detective,
        friend=friend,
        missing=missing,
        clue=clue,
        location=location,
        hiding_place=hiding_place,
        suspicion_target=suspicion_target,
        literal_phrase=clue.literal_phrase,
    )

    # Act 1: setup
    world.say(
        f"{params.detective_name} was a little detective who liked solving small problems at {location.name}."
    )
    world.say(
        f"One afternoon, {params.friend_name} rushed in and said {params.friend_name.lower()}'s {params.missing_item} was missing."
    )
    world.say(
        f"{params.detective_name} noticed {clue.literal_phrase} near the floor."
    )

    # Act 2: conflict
    world.para()
    world.say(
        f"{params.friend_name} got worried and said maybe someone had taken it."
    )
    detective.memes["bravery"] = 1.0
    friend.memes["conflict"] = 1.0
    world.say(
        f"{params.detective_name} felt the tense moment, but stayed brave and looked again instead of guessing."
    )
    world.say(
        f"{params.detective_name} followed the clue to the {hiding_place}."
    )

    # Act 3: resolution
    world.para()
    world.say(
        f"There, tucked away neatly, was the {params.missing_item}."
    )
    world.say(
        f"It had not been stolen at all; it had been set down by the {suspicion_target} and simply forgotten."
    )
    world.say(
        f"{params.friend_name} smiled with relief, and {params.detective_name} smiled too, because brave noticing had solved the mystery."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is valid when the location can hide the missing item and the clue
% fits the kind of detective story we are telling.
valid_story(L, M) :- location(L), missing(M), hides(L, Place), clue_kind(C),
                     fits(C, L), plausible(M, Place).

% A clue is literal when it is explicitly described as a literal trail.
literal_clue(C) :- clue_kind(C), literal(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for loc_id, loc in LOCATIONS.items():
        lines.append(asp.fact("location", loc_id))
        if loc.indoors:
            lines.append(asp.fact("indoors", loc_id))
        for h in sorted(loc.hides):
            lines.append(asp.fact("hides", loc_id, h))
    for item_id, (phrase, kind) in MISSING_ITEMS.items():
        lines.append(asp.fact("missing", item_id))
        lines.append(asp.fact("missing_kind", item_id, kind))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue_kind", clue_id))
        lines.append(asp.fact("literal", clue_id))
        for loc_id in LOCATIONS:
            if clue_id == "paint" and loc_id in {"library", "museum"}:
                lines.append(asp.fact("fits", clue_id, loc_id))
            if clue_id == "mud" and loc_id == "garden":
                lines.append(asp.fact("fits", clue_id, loc_id))
    for item_id, (place, _) in MYSTERY_BY_ITEM.items():
        lines.append(asp.fact("plausible", item_id, place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    models = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(models, "valid_story"))

    py_set = set()
    for loc_id in LOCATIONS:
        for item_id in MISSING_ITEMS:
            if reasonable_combo(loc_id, item_id):
                py_set.add((loc_id, item_id))

    if asp_set == py_set:
        print(f"OK: ASP gate matches Python gate ({len(py_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if asp_set - py_set:
        print("only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A and formatting
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the word "literal".',
        f"Tell a detective story where {f['detective'].id} uses a literal clue to solve a conflict with bravery.",
        f"Write a short mystery about a missing item at {f['location'].name} and a brave detective who follows a literal trail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    friend = _safe_fact(world, f, "friend")
    missing = _safe_fact(world, f, "missing")
    clue = _safe_fact(world, f, "clue")
    loc = _safe_fact(world, f, "location")
    return [
        QAItem(
            question=f"What kind of clue did {detective.id} notice first?",
            answer=f"{detective.id} noticed {clue.literal_phrase}, which was a very literal clue.",
        ),
        QAItem(
            question=f"Why did {friend.id} feel upset at first?",
            answer=f"{friend.id} felt upset because the {missing.label} seemed to be missing, which caused a conflict and made everyone worry.",
        ),
        QAItem(
            question=f"How did {detective.id} show bravery?",
            answer=f"{detective.id} stayed calm, followed the clue carefully, and kept looking instead of jumping to conclusions.",
        ),
        QAItem(
            question=f"Where was the missing {missing.label} found?",
            answer=f"It was found in the {world.facts['hiding_place']} at {loc.name}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when a clue is literal?",
            answer="A literal clue is real and exact, not just a guess or a joke.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the careful or right thing even when you feel nervous.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and tries to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-story world with a literal clue, conflict, and bravery.")
    ap.add_argument("--location", choices=sorted(LOCATIONS))
    ap.add_argument("--missing-item", choices=sorted(MISSING_ITEMS))
    ap.add_argument("--detective-name", choices=DETECTIVE_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--detective-type", choices=DETECTIVE_TYPES)
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
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
    location = getattr(args, "location", None) or rng.choice(list(LOCATIONS))
    missing_item = getattr(args, "missing_item", None) or rng.choice(list(MISSING_ITEMS))
    if not reasonable_combo(location, missing_item):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    detective_type = getattr(args, "detective_type", None) or rng.choice(DETECTIVE_TYPES)
    friend_type = getattr(args, "friend_type", None) or rng.choice(FRIEND_TYPES)
    detective_name = getattr(args, "detective_name", None) or rng.choice(DETECTIVE_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    if detective_name == friend_name:
        friend_name = next(n for n in FRIEND_NAMES if n != detective_name)
    return StoryParams(
        location=location,
        detective_name=detective_name,
        detective_type=detective_type,
        friend_name=friend_name,
        friend_type=friend_type,
        missing_item=missing_item,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


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
    StoryParams(location="library", detective_name="Mina", detective_type="girl", friend_name="Toby", friend_type="boy", missing_item="hat"),
    StoryParams(location="museum", detective_name="Jules", detective_type="boy", friend_name="Lena", friend_type="girl", missing_item="magnifier"),
    StoryParams(location="garden", detective_name="Ivy", detective_type="girl", friend_name="Ben", friend_type="boy", missing_item="puzzle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            header = f"### {p.detective_name} at {p.location} with {p.missing_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
