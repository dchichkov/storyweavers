#!/usr/bin/env python3
"""
usher_kindness_humor_slice_of_life.py
====================================

A small, self-contained storyworld about an usher, kindness, and a light
slice-of-life mishap that ends warmly.

Premise:
- A child or young teen is helping as an usher at a simple community event.
- Someone arrives confused, late, or carrying too much.
- A small funny problem appears, and kindness turns it into a good ending.

The world models:
- physical meters: busy, misplaced, full, dropped, organized
- emotional memes: kind, amused, embarrassed, relieved, proud

The story stays grounded in a tiny day-in-the-life domain:
- a venue
- an usher
- a guest
- a small task
- a humorous turn
- a helpful resolution
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    entities: set[str] = field(default_factory=set)
    guest: object | None = None
    usher: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "daughter"}
        male = {"boy", "man", "father", "dad", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Venue:
    place: str
    event: str
    noise: str
    seats: int
    has_ticket_table: bool = True
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
class Role:
    id: str
    label: str
    helper: bool = False
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
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    chaos: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    prep: str
    effect: str
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


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        clone = World(self.venue)
        clone.entities = {k: Entity(**{
            **vars(v),
            "meters": dict(v.meters),
            "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    venue: str
    task: str
    fix: str
    usher_name: str
    usher_type: str
    guest_name: str
    guest_type: str
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


VENUES = {
    "school_hall": Venue(place="the school hall", event="a winter concert", noise="soft applause", seats=40),
    "community_center": Venue(place="the community center", event="a neighborhood movie night", noise="murmurs", seats=50),
    "library_room": Venue(place="the library meeting room", event="a story reading", noise="quiet whispers", seats=24),
    "little_theater": Venue(place="the little theater", event="a puppet show", noise="happy chatter", seats=36),
}

ROLES = {
    "boy": Role(id="boy", label="boy"),
    "girl": Role(id="girl", label="girl"),
    "man": Role(id="man", label="man"),
    "woman": Role(id="woman", label="woman"),
}

TASKS = {
    "seat_finding": Task(
        id="seat_finding",
        verb="find the right seat",
        gerund="finding seats",
        risk="confused",
        chaos="mixed-up",
        keyword="seat",
        tags={"seat", "crowd", "help"},
    ),
    "ticket_help": Task(
        id="ticket_help",
        verb="find the ticket table",
        gerund="checking tickets",
        risk="lost",
        chaos="missing",
        keyword="ticket",
        tags={"ticket", "paper", "help"},
    ),
    "coat_carrying": Task(
        id="coat_carrying",
        verb="carry too many coats",
        gerund="carrying coats",
        risk="dropped",
        chaos="piled",
        keyword="coat",
        tags={"coat", "busy", "help"},
    ),
    "snack_spill": Task(
        id="snack_spill",
        verb="balance a snack tray",
        gerund="balancing snacks",
        risk="wobbly",
        chaos="tilting",
        keyword="snack",
        tags={"snack", "spill", "humor"},
    ),
}

FIXES = [
    Fix(id="flashlight", label="a tiny flashlight", prep="hold up a tiny flashlight", effect="helps people see the row numbers", helps={"seat_finding"}),
    Fix(id="extra_sign", label="an extra sign", prep="hang an extra sign at the door", effect="points the way to the ticket table", helps={"ticket_help"}),
    Fix(id="coat_cart", label="a coat cart", prep="roll over a coat cart", effect="gives the coats a safe place to rest", helps={"coat_carrying"}),
    Fix(id="napkins", label="a stack of napkins", prep="grab a stack of napkins", effect="soaks up little drips before they spread", helps={"snack_spill"}),
]

USHER_NAMES = ["Mina", "Leo", "Nora", "Finn", "Ava", "Theo", "Lena", "Eli"]
GUEST_NAMES = ["Mrs. Bell", "Mr. Green", "Ms. Park", "Sam", "Jules", "Tia", "Noah", "Rosa"]


def problem_risk(task: Task) -> bool:
    return True


def select_fix(task: Task) -> Optional[Fix]:
    for fx in FIXES:
        if task.id in fx.helps:
            return fx
    return None


ASP_RULES = r"""
task_risk(T) :- task(T), risky(T).
has_fix(T) :- task(T), fix(F), helps(F, T).
valid_story(V, T, F) :- venue(V), task(T), fix(F), has_fix(T), risk(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for vid in VENUES:
        lines.append(asp.fact("venue", vid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("risky", tid))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for t in sorted(fx.helps):
            lines.append(asp.fact("helps", fx.id, t))
    for vid in VENUES:
        for tid in TASKS:
            if select_fix(_safe_lookup(TASKS, tid)) is not None:
                lines.append(asp.fact("risk", vid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [(v, t, select_fix(_safe_lookup(TASKS, t)).id) for v in VENUES for t in TASKS if select_fix(_safe_lookup(TASKS, t))]


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(asp_valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny slice-of-life storyworld about an usher and a kind fix.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--fix", choices=[f.id for f in FIXES])
    ap.add_argument("--name")
    ap.add_argument("--guest")
    ap.add_argument("--type", choices=["boy", "girl", "man", "woman"])
    ap.add_argument("--guest-type", choices=["boy", "girl", "man", "woman"])
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
    venue = getattr(args, "venue", None) or rng.choice(list(VENUES))
    task = getattr(args, "task", None) or rng.choice(list(TASKS))
    fix = getattr(args, "fix", None) or select_fix(_safe_lookup(TASKS, task)).id
    if select_fix(_safe_lookup(TASKS, task)) is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "fix", None) and getattr(args, "fix", None) != select_fix(_safe_lookup(TASKS, task)).id:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    usher_type = getattr(args, "type", None) or rng.choice(["boy", "girl"])
    guest_type = getattr(args, "guest_type", None) or rng.choice(["man", "woman", "boy", "girl"])
    usher_name = getattr(args, "name", None) or rng.choice(USHER_NAMES)
    guest_name = getattr(args, "guest", None) or rng.choice(GUEST_NAMES)
    return StoryParams(venue=venue, task=task, fix=fix, usher_name=usher_name, usher_type=usher_type, guest_name=guest_name, guest_type=guest_type)


def introduce(world: World, usher: Entity) -> None:
    world.say(f"{usher.id} was an usher at {world.venue.place}, and {usher.pronoun()} liked making people feel welcome.")


def setup(world: World, usher: Entity, guest: Entity, task: Task) -> None:
    world.say(f"That evening, {world.venue.place} was busy with {world.venue.event}.")
    world.say(f"{guest.id} arrived with {task.chaos} hands and a worried look, because {task.verb} was not as easy as it sounded.")
    usher.memes["kind"] += 1
    guest.memes["embarrassed"] += 1


def make_tension(world: World, usher: Entity, guest: Entity, task: Task) -> None:
    guest.meters["mess"] = guest.meters.get("mess", 0) + 1
    guest.memes["amused"] = guest.memes.get("amused", 0) + 1
    world.say(f"{guest.id} laughed a little at the mix-up, then said, \"I think I need a hand.\"")
    world.say(f"{usher.id} smiled right away and decided to help with kindness instead of making it bigger.")


def resolve(world: World, usher: Entity, guest: Entity, task: Task, fix: Fix) -> None:
    usher.memes["proud"] += 1
    guest.memes["relieved"] += 1
    guest.meters["mess"] = 0
    world.say(f"{usher.id} used {fix.label} and {fix.prep}.")
    world.say(f"That small fix {fix.effect}, so {guest.id} could {task.verb} without more trouble.")
    world.say(f"By the end, {guest.id} was smiling, and {usher.id} was smiling too, because the evening felt lighter for everyone.")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(VENUES, params.venue))
    usher = world.add(Entity(id=params.usher_name, kind="character", type=params.usher_type))
    guest = world.add(Entity(id=params.guest_name, kind="character", type=params.guest_type))
    task = _safe_lookup(TASKS, params.task)
    fx = next(f for f in FIXES if f.id == params.fix)

    introduce(world, usher)
    world.para()
    setup(world, usher, guest, task)
    make_tension(world, usher, guest, task)
    world.para()
    resolve(world, usher, guest, task, fx)

    world.facts = {"usher": usher, "guest": guest, "task": task, "fix": fx, "venue": world.venue}
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a warm slice-of-life story about an usher named {f['usher'].id} helping a guest at {world.venue.place}.",
        f"Tell a short story where {f['guest'].id} has trouble with {f['task'].verb}, and {f['usher'].id} solves it kindly and with a little humor.",
        f"Write a child-friendly story that includes an usher, a small problem, and a gentle happy ending at {world.venue.event}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    usher: Entity = f["usher"]
    guest: Entity = f["guest"]
    task: Task = f["task"]
    fix: Fix = f["fix"]
    venue: Venue = f["venue"]
    return [
        QAItem(
            question=f"Who was the usher in the story?",
            answer=f"{usher.id} was the usher, and {usher.pronoun()} helped people at {venue.place}.",
        ),
        QAItem(
            question=f"What small problem did {guest.id} have?",
            answer=f"{guest.id} had trouble {task.gerund}, so the moment felt a little awkward at first.",
        ),
        QAItem(
            question=f"How did {usher.id} help?",
            answer=f"{usher.id} used {fix.label} to make the problem smaller and help {guest.id} feel okay again.",
        ),
        QAItem(
            question=f"Why did the story feel funny but kind?",
            answer=f"It felt funny because the problem was small and a little mixed-up, but {usher.id} answered with patience and a helpful smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an usher do?",
            answer="An usher helps people find their seats, makes them feel welcome, and points them the right way in a place like a theater or hall.",
        ),
        QAItem(
            question="Why can a tiny flashlight be useful in a dark room?",
            answer="A tiny flashlight can help people see a little better when the room is dim, so they can walk safely to the right place.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about how someone else feels.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is when something is funny or a little silly and makes people smile or laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams(venue="community_center", task="ticket_help", fix="extra_sign", usher_name="Mina", usher_type="girl", guest_name="Mr. Green", guest_type="man"),
    StoryParams(venue="school_hall", task="seat_finding", fix="flashlight", usher_name="Leo", usher_type="boy", guest_name="Mrs. Bell", guest_type="woman"),
    StoryParams(venue="little_theater", task="coat_carrying", fix="coat_cart", usher_name="Nora", usher_type="girl", guest_name="Jules", guest_type="boy"),
    StoryParams(venue="library_room", task="snack_spill", fix="napkins", usher_name="Theo", usher_type="boy", guest_name="Tia", guest_type="girl"),
]


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
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.usher_name}: {p.task} at {p.venue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
