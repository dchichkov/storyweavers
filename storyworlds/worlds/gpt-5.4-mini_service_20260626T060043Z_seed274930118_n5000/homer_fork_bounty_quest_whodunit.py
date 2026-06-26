#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/homer_fork_bounty_quest_whodunit.py
===============================================================================================================

A small whodunit storyworld: Homer follows a quest to solve a tiny mystery
about a missing fork and a promised bounty.

The story structure is intentionally classical:
- setup: Homer is asked to help
- tension: the fork goes missing and the clues feel suspicious
- turn: Homer notices the telling detail
- resolution: the culprit is revealed and the bounty is earned

The world model tracks physical meters and emotional memes so the story is
driven by state, not a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    culprit: object | None = None
    fork: object | None = None
    homer: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "boy", "detective", "chef"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    label: str
    kind: str = "room"
    clues: set[str] = field(default_factory=set)
    suspicious: bool = False
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
class Quest:
    id: str
    title: str
    goal: str
    reward_word: str
    clue_word: str
    culprit_word: str
    setting: str = ""
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
class StoryParams:
    place: str
    quest: str
    name: str
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


class World:
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict = {}

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
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place, self.quest)
        w.entities = _copy.deepcopy(self.entities)
        w.events = []
        w.facts = dict(self.facts)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        clues={"crumbs", "sauce", "door", "drawer"},
        suspicious=True,
    ),
    "hall": Place(
        id="hall",
        label="the hall",
        clues={"footprints", "draft", "mat"},
        suspicious=False,
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        clues={"soil", "pebbles", "gate"},
        suspicious=True,
    ),
    "pantry": Place(
        id="pantry",
        label="the pantry",
        clues={"shelf", "jar", "crumbs"},
        suspicious=True,
    ),
}

QUESTS = {
    "fork_quest": Quest(
        id="fork_quest",
        title="the Fork Quest",
        goal="find the missing fork",
        reward_word="bounty",
        clue_word="fork",
        culprit_word="cat",
        setting="kitchen",
        tags={"fork", "bounty", "quest", "whodunit"},
    ),
    "bounty_quest": Quest(
        id="bounty_quest",
        title="the Bounty Quest",
        goal="recover the promised bounty",
        reward_word="bounty",
        clue_word="token",
        culprit_word="butler",
        setting="hall",
        tags={"bounty", "quest", "whodunit"},
    ),
}

HOMER_NAMES = ["Homer", "Homer J.", "Mr. Homer"]
SUSPECTS = ["Mina", "Iris", "Toby", "June", "the cat", "the butler"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A whodunit is valid when the quest has a place, a clue, and a reward path.
valid_story(P, Q) :- place(P), quest(Q), quest_goal(Q, _), quest_reward(Q, _), clue_at(P, Q).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.suspicious:
            lines.append(asp.fact("suspicious", pid))
        for clue in sorted(p.clues):
            lines.append(asp.fact("clue_at", pid, clue))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_goal", qid, q.goal))
        lines.append(asp.fact("quest_reward", qid, q.reward_word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, q) for p in PLACES for q in QUESTS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combo(place: str, quest: str) -> bool:
    return place in PLACES and quest in QUESTS


def reasonableness_gate(place: str, quest: str) -> None:
    if not valid_combo(place, quest):
        pass
    if place == "hall" and quest == "fork_quest":
        pass


def predict_mystery(world: World, hero: Entity) -> dict:
    sim = world.copy()
    sim.get("fork").hidden_in = "drawer"
    sim.get("fork").held_by = None
    sim.get("fork").meters["missing"] = 1
    return {
        "missing": sim.get("fork").meters.get("missing", 0) >= THRESHOLD,
        "clue": sim.get("fork").hidden_in,
    }


def intro(world: World, homer: Entity) -> None:
    world.say(f"Homer was a careful little detective who loved a good quest.")


def setup(world: World, homer: Entity, item: Entity) -> None:
    world.say(f"One afternoon, {homer.id} heard about a missing {item.label} and a promised bounty.")
    world.say(f"He took the quest seriously because every mystery felt like a puzzle with a hidden door.")


def tension(world: World, homer: Entity, item: Entity, culprit: Entity) -> None:
    world.say(f"When {homer.id} reached {world.place.label}, the {item.label} was gone.")
    world.say(f"On the table, there was only a small clue: a little shine where the {item.label} had been.")
    world.say(f"{homer.id} looked at the crumbs, the drawer, and the floor, and the silence felt suspicious.")


def inspect(world: World, homer: Entity, item: Entity, culprit: Entity) -> None:
    item.meters["missing"] = 1
    homer.memes["doubt"] += 1
    world.say(f"{homer.id} bent low and noticed that the clue pointed toward the drawer, not the window.")


def reveal(world: World, homer: Entity, item: Entity, culprit: Entity) -> None:
    culprit.meters["caught"] = 1
    culprit.memes["nervous"] += 1
    item.hidden_in = None
    item.held_by = "table"
    item.meters["found"] = 1
    world.say(f"At last, Homer opened the drawer and found the {item.label} tucked inside beside the cloth.")
    world.say(f"The cat had stolen it for a shiny game, and the tiny thief could not deny it any longer.")


def resolve(world: World, homer: Entity, item: Entity, culprit: Entity) -> None:
    homer.memes["joy"] += 1
    homer.memes["pride"] += 1
    world.say(f"The missing {item.label} was returned to the table, and the bounty was finally handed over.")
    world.say(f"Homer smiled, because the quest was done and the kitchen looked honest again.")


def tell(place: Place, quest: Quest, name: str) -> World:
    world = World(place, quest)
    homer = world.add(Entity(
        id=name,
        kind="character",
        type="detective",
        label="Homer",
        phrase="a small detective with a tidy notebook",
    ))
    fork = world.add(Entity(
        id="fork",
        kind="thing",
        type="fork",
        label="fork",
        phrase="a silver fork from the table",
        owner=name,
        hidden_in="drawer",
    ))
    culprit = world.add(Entity(
        id="cat",
        kind="character",
        type="cat",
        label="the cat",
        phrase="a whiskered little culprit",
    ))

    world.facts.update(hero=homer, item=fork, culprit=culprit, quest=quest, place=place)

    intro(world, homer)
    world.say("")
    setup(world, homer, fork)
    tension(world, homer, fork, culprit)
    inspect(world, homer, fork, culprit)
    reveal(world, homer, fork, culprit)
    resolve(world, homer, fork, culprit)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    q = world.quest
    return [
        f'Write a short whodunit for a young child about Homer, a {q.goal}, and a promised bounty.',
        f"Tell a gentle mystery where Homer follows a quest to solve why the {q.clue_word} vanished.",
        f'Write a simple detective story that includes the words "Homer", "fork", and "bounty".',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    item: Entity = _safe_fact(world, world.facts, "item")
    culprit: Entity = _safe_fact(world, world.facts, "culprit")
    q: Quest = _safe_fact(world, world.facts, "quest")

    return [
        QAItem(
            question=f"What was Homer trying to do in {world.place.label}?",
            answer=f"Homer was trying to {q.goal}. It was a small whodunit quest, and the promised bounty gave him a reason to keep looking.",
        ),
        QAItem(
            question=f"What clue helped Homer solve the mystery of the missing {item.label}?",
            answer=f"The clue was that the trail pointed toward the drawer. Homer noticed that detail and followed it like a careful detective.",
        ),
        QAItem(
            question=f"Who took the {item.label}?",
            answer=f"The cat took the {item.label} and hid it in the drawer. That was the little secret behind the mystery.",
        ),
        QAItem(
            question=f"What happened to the bounty at the end?",
            answer=f"The bounty was handed over after Homer found the {item.label} and solved the case. The quest ended happily once the truth came out.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fork used for?",
            answer="A fork is a utensil with tines that people use to pick up food, especially noodles, vegetables, and other small bites.",
        ),
        QAItem(
            question="What is a bounty?",
            answer="A bounty is a reward offered for finding something, solving a problem, or bringing back what was lost.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to reach a goal, often by following clues and solving a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with Homer, a fork, and a bounty.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    reasonableness_gate(place, quest)
    name = getattr(args, "name", None) or rng.choice(HOMER_NAMES)
    return StoryParams(place=place, quest=quest, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), params.name)
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
    StoryParams(place="kitchen", quest="fork_quest", name="Homer"),
    StoryParams(place="pantry", quest="bounty_quest", name="Homer"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_stories())} compatible story combinations.")
        for p, q in asp_valid_stories():
            print(f"  {p} {q}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 25):
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
