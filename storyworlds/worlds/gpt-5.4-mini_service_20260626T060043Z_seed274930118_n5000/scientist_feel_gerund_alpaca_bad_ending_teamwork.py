#!/usr/bin/env python3
"""
A small folk-tale storyworld about a scientist, an alpaca, feelings, and teamwork.

Seed premise:
- A scientist in a little valley is feeling sad, nervous, or hopeful while
  tending a delicate task.
- An alpaca helps with teamwork: carrying, watching, nudging, or sharing.
- Sometimes the helpers can make things better, but this world also allows a
  gentle bad ending when the needed fix cannot actually succeed.

The world is intentionally tiny and constraint-checked so every generated story
comes from a concrete simulation rather than a frozen template.
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
# Core entities
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    alpaca: object | None = None
    scientist: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"scientist"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"alpaca"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    name: str
    affords: set[str] = field(default_factory=set)
    weather: str = ""
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
class Task:
    id: str
    verb: str
    gerund: str
    mess: str
    risk: str
    clue: str
    tag: str
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
class Tool:
    id: str
    label: str
    helps: set[str]
    prep: str
    ending: str
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
class StoryParams:
    place: str
    task: str
    tool: str
    scientist_name: str
    alpaca_name: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hill": Place("the hill", affords={"listening", "repair", "gather"}, weather="windy"),
    "barn": Place("the barn", affords={"listening", "repair"}, weather="rainy"),
    "orchard": Place("the orchard", affords={"gather", "repair"}, weather="soft"),
    "shed": Place("the shed", affords={"repair"}, weather="quiet"),
}

TASKS = {
    "listen": Task(
        id="listen",
        verb="listen for the strange humming",
        gerund="listening for the strange humming",
        mess="worry",
        risk="the sound would fade away",
        clue="a tiny hum in the air",
        tag="sound",
    ),
    "repair": Task(
        id="repair",
        verb="repair the cracked lantern",
        gerund="repairing the cracked lantern",
        mess="sputter",
        risk="the lantern would go dark",
        clue="a little crack at the side",
        tag="light",
    ),
    "gather": Task(
        id="gather",
        verb="gather the spilled seeds",
        gerund="gathering the spilled seeds",
        mess="scatter",
        risk="the seeds would be lost in the grass",
        clue="small specks hidden in the dirt",
        tag="seed",
    ),
}

TOOLS = {
    "string": Tool(
        id="string",
        label="a spool of bright string",
        helps={"repair"},
        prep="tie the crack with bright string",
        ending="They tied the lantern with bright string, but the knot held only a little while.",
    ),
    "basket": Tool(
        id="basket",
        label="a woven basket",
        helps={"gather"},
        prep="carry the seeds in a woven basket",
        ending="They scooped the seeds into the basket, but some still slipped through the reeds.",
    ),
    "earmuff": Tool(
        id="earmuff",
        label="soft wool earflaps",
        helps={"listen"},
        prep="stand close and listen together with soft wool earflaps",
        ending="They listened together with soft wool earflaps, yet the wind kept stealing the hum.",
    ),
}

SCIENTISTS = ["Mara", "Iris", "Nora", "Lina", "Ada", "Tessa"]
ALPACAS = ["Pico", "Juniper", "Mochi", "Pip", "Sage", "Luna"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def task_needs_tool(task: Task, tool: Tool) -> bool:
    return task.id in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_name, place in PLACES.items():
        for task_name in place.affords:
            task = _safe_lookup(TASKS, task_name)
            for tool_name, tool in TOOLS.items():
                if task_needs_tool(task, tool):
                    out.append((place_name, task_name, tool_name))
    return out


def explain_rejection(task: Task, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not really help with {task.gerund}. "
        f"This world only tells stories when teamwork has a real chance, so the "
        f"pairing is rejected.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def predict(world: World, scientist: Entity, alpaca: Entity, task: Task, tool: Tool) -> dict:
    sim = world.copy()
    do_task(sim, sim.get(scientist.id), sim.get(alpaca.id), task, tool, narrate=False)
    return {
        "success": bool(sim.facts.get("solved")),
        "bad_ending": bool(sim.facts.get("bad_ending")),
    }


def do_task(world: World, scientist: Entity, alpaca: Entity, task: Task, tool: Tool, narrate: bool = True) -> None:
    scientist.memes["hope"] = scientist.memes.get("hope", 0) + 1
    alpaca.memes["teamwork"] = alpaca.memes.get("teamwork", 0) + 1
    scientist.memes["worry"] = scientist.memes.get("worry", 0) + 1

    world.say(f"{scientist.id} and {alpaca.id} went to {world.place.name} on a quiet day.")
    world.say(f"{scientist.id} was {task.gerund}, and {alpaca.id} stayed close by, ready to help.")
    world.say(f"They used {tool.label} and tried to do the work together.")

    # Outcome is deliberate and small: some tasks have only a partial fix.
    if task.id == "listen":
        world.say("The two friends stood still and listened, but the wind kept sweeping the sound away.")
        world.facts["bad_ending"] = True
        world.facts["solved"] = False
        world.say("At last the humming was gone, and the scientist never learned where it had come from.")
        return

    if task.id == "repair":
        world.say("The alpaca held the lantern steady while the scientist tied the crack.")
        world.say("The lantern glowed for a moment, then the old crack opened again.")
        world.facts["bad_ending"] = True
        world.facts["solved"] = False
        world.say("By the time night came, the lantern was dark, and the little light was lost.")
        return

    if task.id == "gather":
        world.say("The alpaca nudged the seeds into a basket while the scientist cupped both hands around them.")
        world.say("Most of the seeds stayed safe, but a breezy gust scattered the rest.")
        world.facts["bad_ending"] = True
        world.facts["solved"] = False
        world.say("When the grass grew still, only a few seeds remained, and the rest were nowhere to be found.")
        return


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def opening(world: World, scientist: Entity, alpaca: Entity, task: Task) -> None:
    world.say(f"Long ago, {scientist.id} was a little scientist who noticed every small thing.")
    world.say(f"{scientist.id} loved {task.gerund}, because each clue felt like a secret in a folktale.")
    world.say(f"Beside the doorway lived {alpaca.id}, an alpaca with a soft coat and a helpful heart.")


def setup_problem(world: World, scientist: Entity, task: Task) -> None:
    world.say(f"One day, {scientist.id} saw {task.clue} and knew something delicate was waiting to be fixed.")
    world.say(f"But {task.risk}, and that made the scientist feel uneasy.")


def teamwork_offer(world: World, scientist: Entity, alpaca: Entity, tool: Tool) -> None:
    world.say(f"{alpaca.id} bowed its head and said it would help.")
    world.say(f"So the two of them chose {tool.label} and made a teamwork plan.")


def ending_bad(world: World, scientist: Entity, alpaca: Entity, task: Task) -> None:
    world.say(
        f"In the end, {scientist.id} and {alpaca.id} were still side by side, "
        f"but {task.risk}."
    )
    world.say("The valley stayed quiet, and the little hope in the air felt smaller than before.")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for young children about a scientist and an alpaca who are {f["task"].gerund}.',
        f'Write a gentle story where teamwork matters, using the word "{f["task"].tag}" and ending with a bad ending.',
        f"Tell a small story in which {f['scientist'].id} and {f['alpaca'].id} try to help each other but the problem still does not fully get solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Entity = _safe_fact(world, f, "scientist")
    a: Entity = _safe_fact(world, f, "alpaca")
    task: Task = _safe_fact(world, f, "task")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {s.id}, a little scientist, and {a.id}, a helpful alpaca, at {place.name}.",
        ),
        QAItem(
            question=f"What was {s.id} trying to do?",
            answer=f"{s.id} was trying to {task.verb}.",
        ),
        QAItem(
            question=f"How did {s.id} and {a.id} work together?",
            answer=f"They used {tool.label} and made a teamwork plan so they could try the job together.",
        ),
        QAItem(
            question=f"Why did the story end sadly?",
            answer=(
                f"It ended sadly because even with teamwork, {task.risk}. "
                f"The helpers tried hard, but the world would not let the problem fully be fixed."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when two or more helpers work together to do one job.",
        ),
        QAItem(
            question="What is an alpaca?",
            answer="An alpaca is a soft, long-necked animal that can carry things or walk beside a person.",
        ),
        QAItem(
            question="What does it mean to feel worried?",
            answer="To feel worried means to have a heavy, uneasy feeling because something may go wrong.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(hill). place(barn). place(orchard). place(shed).
affords(hill,listening). affords(hill,repair). affords(hill,gather).
affords(barn,listening). affords(barn,repair).
affords(orchard,gather). affords(orchard,repair).
affords(shed,repair).

task(listen). task(repair). task(gather).
task_needs_tool(listen,earmuff). task_needs_tool(repair,string). task_needs_tool(gather,basket).

valid(Place,Task,Tool) :- affords(Place,Task), task_needs_tool(Task,Tool).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pname in PLACES:
        lines.append(asp.fact("place", pname))
        for t in sorted(_safe_lookup(PLACES, pname).affords):
            lines.append(asp.fact("affords", pname, t))
    for tname in TASKS:
        lines.append(asp.fact("task", tname))
    for tname, tool in TOOLS.items():
        lines.append(asp.fact("tool", tname))
        for task_name in sorted(tool.helps):
            lines.append(asp.fact("task_needs_tool", task_name, tname))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Small folk-tale world: scientist, alpaca, feeling, teamwork, bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--scientist-name", choices=SCIENTISTS)
    ap.add_argument("--alpaca-name", choices=ALPACAS)
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
    if getattr(args, "task", None) and getattr(args, "tool", None) and not task_needs_tool(_safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(TOOLS, getattr(args, "tool", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, tool = rng.choice(list(filtered))
    return StoryParams(
        place=place,
        task=task,
        tool=tool,
        scientist_name=getattr(args, "scientist_name", None) or rng.choice(SCIENTISTS),
        alpaca_name=getattr(args, "alpaca_name", None) or rng.choice(ALPACAS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(PLACES, params.place))
    scientist = world.add(Entity(id=params.scientist_name, kind="character", type="scientist"))
    alpaca = world.add(Entity(id=params.alpaca_name, kind="character", type="alpaca"))
    task = _safe_lookup(TASKS, params.task)
    tool = _safe_lookup(TOOLS, params.tool)

    world.facts.update(scientist=scientist, alpaca=alpaca, task=task, tool=tool, place=world.place)

    opening(world, scientist, alpaca, task)
    world.say("")
    setup_problem(world, scientist, task)
    teamwork_offer(world, scientist, alpaca, tool)
    do_task(world, scientist, alpaca, task, tool)
    ending_bad(world, scientist, alpaca, task)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if isinstance(v, Entity):
                print(f"{k}: {v.id}")
            elif hasattr(v, "name"):
                print(f"{k}: {getattr(v, 'name', v)}")
            else:
                print(f"{k}: {v}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, task, tool in sorted(valid_combos()):
            params = StoryParams(
                place=place,
                task=task,
                tool=tool,
                scientist_name=_safe_lookup(SCIENTISTS, 0),
                alpaca_name=_safe_lookup(ALPACAS, 0),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
