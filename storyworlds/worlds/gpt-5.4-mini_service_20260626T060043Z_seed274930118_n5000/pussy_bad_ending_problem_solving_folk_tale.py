#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pussy_bad_ending_problem_solving_folk_tale.py
=========================================================================================================================

A small folk-tale story world about a pussycat who faces a simple problem,
tries to solve it, and sometimes ends with a bad ending image instead of a
happy one.

The seed idea is a classic folk tale shape:
- a little pussycat wants something dear,
- a problem blocks the way,
- a clever fix is tried,
- the fix may work partly or fail,
- the ending leaves a clear image of what changed.

This world keeps the cast tiny and the tone child-facing, concrete, and
storybook-like.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pussy", "cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "father", "old man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "mother", "old woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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


@dataclass(frozen=True)
class Place:
    name: str
    weather: str
    afford: str
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


@dataclass(frozen=True)
class Problem:
    id: str
    want: str
    trouble: str
    fix: str
    risk: str
    ending: str
    tags: tuple[str, ...] = ()
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


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    helps: tuple[str, ...]
    covers: tuple[str, ...] = ()
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _narrate_name(ent: Entity) -> str:
    return ent.label or ent.id


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


PLACES = {
    "wood": Place(name="the wood", weather="misty", afford="hunt"),
    "cottage": Place(name="the cottage yard", weather="windy", afford="sneak"),
    "river": Place(name="the riverbank", weather="cold", afford="fish"),
    "barn": Place(name="the old barn", weather="dark", afford="hide"),
}

PROBLEMS = {
    "mouse": Problem(
        id="mouse",
        want="catch the mouse",
        trouble="the mouse hid behind a sack of oats",
        fix="wait beside the wall and listen for tiny feet",
        risk="the mouse would slip into a hole and get away",
        ending="the mouse escaped into the dark grass",
        tags=("mouse", "hunt"),
    ),
    "bread": Problem(
        id="bread",
        want="bring home the warm bread",
        trouble="the bread basket sat high on a shelf",
        fix="stack a stool and reach carefully",
        risk="the stool could wobble and spill the bread",
        ending="the bread tumbled into the dust",
        tags=("bread", "cottage"),
    ),
    "fish": Problem(
        id="fish",
        want="catch the silver fish",
        trouble="the river kept tugging the net downstream",
        fix="tie the net to a root and hold it steady",
        risk="the rope could snap and the fish would dart off",
        ending="the net tore and the fish flashed away",
        tags=("fish", "river"),
    ),
}

TOOLS = {
    "stool": Tool(id="stool", label="a little stool", helps=("bread",)),
    "net": Tool(id="net", label="a woven net", helps=("fish",)),
    "lamp": Tool(id="lamp", label="a small lamp", helps=("mouse", "bread")),
    "rope": Tool(id="rope", label="a stout rope", helps=("fish", "bread")),
}

NAMES = ["Mina", "Pip", "Mara", "Tess", "Nell", "Oona", "Wren", "Bria"]
KEEPERS = ["old woman", "old man", "farmer", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    keeper: str
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


def reasonableness_gate(place: Place, problem: Problem) -> bool:
    return place.afford in {"hunt", "sneak", "fish"} and problem.id in PROBLEMS


def choose_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS.values():
        if problem.id in tool.helps:
            return tool
    return None


def predict_outcome(world: World, hero: Entity, problem: Problem, tool: Tool) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["trying"] += 1
    if problem.id == "fish" and tool.id == "net":
        success = False
    elif problem.id == "mouse" and tool.id == "lamp":
        success = False
    elif problem.id == "bread" and tool.id == "stool":
        success = False
    else:
        success = False
    return {"success": success, "bad_ending": True}


def tell(place: Place, problem: Problem, name: str, keeper: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="pussy", label="little pussycat"))
    adult = world.add(Entity(id="keeper", kind="character", type=keeper, label=f"the {keeper}"))
    treasure = world.add(Entity(id="treasure", kind="thing", type=problem.id, label=problem.want))
    tool = choose_tool(problem)

    world.say(
        f"Once in {place.name}, there lived {_narrate_name(hero)}, a little pussycat "
        f"with bright eyes and a hungry heart."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {problem.want}, because the little thing "
        f"that belonged to {adult.label} looked so tempting."
    )
    world.para()
    world.say(
        f"One {place.weather} day, {_narrate_name(hero)} found the trouble at last: {problem.trouble}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} knew a problem when {hero.pronoun('subject')} saw one, and "
        f"{hero.pronoun()} tried to think of a clever way."
    )

    if tool is None:
        pass

    forecast = predict_outcome(world, hero, problem, tool)
    world.facts.update(
        hero=hero,
        adult=adult,
        treasure=treasure,
        problem=problem,
        tool=tool,
        place=place,
        forecast=forecast,
    )

    world.para()
    world.say(
        f"{hero.pronoun().capitalize()} used {tool.label} and tried to {problem.fix}."
    )
    world.say(
        f"That seemed wise for a moment, but the old tale had a hard turn hidden inside it."
    )
    world.say(
        f"Before long, {problem.risk}, and the little plan could not hold."
    )

    world.para()
    world.say(
        f"In the end, {problem.ending}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} came home with empty paws, and the {keeper} had to look for another way."
    )
    return world


SETTINGS = PLACES
ACTIVITIES = PROBLEMS
GEAR = list(TOOLS.values())


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for pid, place in SETTINGS.items():
        for pr in ACTIVITIES:
            if reasonableness_gate(place, _safe_lookup(ACTIVITIES, pr)):
                out.append((pid, pr))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about a pussycat named {f["hero"].id} in {f["place"].name} who wants to {f["problem"].want}.',
        f"Tell a child-friendly story where {f['hero'].label} meets a problem, tries a clever fix, and the ending is a little sad.",
        f'Write a small folk tale that includes a pussycat, a tool like {(f.get("tool") or next(iter(TOOLS.values()))).label}, and a bad ending after a problem-solving attempt.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    place = _safe_fact(world, f, "place")
    adult = _safe_fact(world, f, "adult")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a little pussycat in {place.name}."
        ),
        QAItem(
            question=f"What did {hero.label} want to do?",
            answer=f"{hero.pronoun().capitalize()} wanted to {problem.want}."
        ),
        QAItem(
            question=f"What did {hero.label} try to use to solve the problem?",
            answer=f"{hero.pronoun().capitalize()} used {tool.label} to try to solve it."
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because {problem.ending}, so the clever plan did not save the day."
        ),
        QAItem(
            question=f"Who had to look for another way at the end?",
            answer=f"The {adult.type} had to look for another way after the little plan failed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pussycat?",
            answer="A pussycat is a cat, often a small and gentle one in a story."
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to think carefully and try a way that can fix the trouble."
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story that often feels simple, clever, and a little magical."
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
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="wood", problem="mouse", name="Mina", keeper="old woman"),
    StoryParams(place="river", problem="fish", name="Pip", keeper="farmer"),
    StoryParams(place="cottage", problem="bread", name="Nell", keeper="grandmother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world with a pussycat, a problem, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--keeper", choices=KEEPERS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "problem", None):
        combos = [c for c in combos if c[1] == getattr(args, "problem", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, problem_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    keeper = getattr(args, "keeper", None) or rng.choice(KEEPERS)
    return StoryParams(place=place_id, problem=problem_id, name=name, keeper=keeper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.problem), params.name, params.keeper)
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


ASP_RULES = r"""
place(P) :- setting(P).
problem(X) :- trouble(X).
pair(P,X) :- setting(P), trouble(X).

valid(P,X) :- setting(P), trouble(X), afford(P, A), fits(X, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("afford", pid, place.afford))
    for xid, problem in ACTIVITIES.items():
        lines.append(asp.fact("trouble", xid))
        lines.append(asp.fact("need", xid, problem.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        cl = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP unavailable or failed: {e}")
        return 1
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and python.")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.problem} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
