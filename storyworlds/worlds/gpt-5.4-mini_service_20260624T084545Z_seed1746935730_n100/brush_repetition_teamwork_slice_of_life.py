#!/usr/bin/env python3
"""
brush_repetition_teamwork_slice_of_life.py
=========================================

A small slice-of-life story world about brushing, repetition, and teamwork.

Seed tale:
---
A child keeps brushing and brushing a little rug that got fuzzy crumbs on it.
Each pass helps a little, but the crumbs stay stuck in the loops. A parent
brings a small hand brush, and together they brush in the same direction,
again and again. Bit by bit, the rug looks neat, the crumbs are gone, and the
two of them finish with a tidy room and a happy sigh.
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

    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
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
class Setting:
    place: str = "the living room"
    affords: set[str] = field(default_factory=set)
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
class Task:
    id: str
    repeated_action: str
    first_action: str
    harder_action: str
    label: str
    messy: str
    progress_key: str
    goal_key: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    boost: float
    teamwork_phrase: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class StoryParams:
    setting: str
    task: str
    tool: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "living_room": Setting(place="the living room", affords={"brush_rug", "brush_pet", "brush_table"}),
    "porch": Setting(place="the porch", affords={"brush_rug", "brush_pet"}),
    "hall": Setting(place="the hall", affords={"brush_rug", "brush_table"}),
}

TASKS = {
    "rug": Task(
        id="rug",
        repeated_action="brush the little rug",
        first_action="brush the little rug",
        harder_action="keep brushing the little rug",
        label="rug",
        messy="crumbs",
        progress_key="cleanliness",
        goal_key="crumbs_left",
        tags={"brush", "repetition", "teamwork", "slice_of_life"},
    ),
    "pet": Task(
        id="pet",
        repeated_action="brush the fluffy pet",
        first_action="brush the fluffy pet",
        harder_action="keep brushing the fluffy pet",
        label="pet",
        messy="fur",
        progress_key="smoothness",
        goal_key="tangles_left",
        tags={"brush", "repetition", "teamwork", "slice_of_life"},
    ),
    "table": Task(
        id="table",
        repeated_action="brush the table mat",
        first_action="brush the table mat",
        harder_action="keep brushing the table mat",
        label="table mat",
        messy="dust",
        progress_key="cleanliness",
        goal_key="dust_left",
        tags={"brush", "repetition", "teamwork", "slice_of_life"},
    ),
}

TOOLS = {
    "hand_brush": Tool(
        id="hand_brush",
        label="a small hand brush",
        phrase="a small hand brush",
        helps_with={"brush_rug", "brush_pet", "brush_table"},
        boost=1.0,
        teamwork_phrase="They worked side by side, each using a brush.",
    ),
    "soft_brush": Tool(
        id="soft_brush",
        label="a soft brush",
        phrase="a soft brush",
        helps_with={"brush_rug", "brush_pet"},
        boost=0.8,
        teamwork_phrase="The soft brush helped them move in the same careful rhythm.",
    ),
    "wide_brush": Tool(
        id="wide_brush",
        label="a wide brush",
        phrase="a wide brush",
        helps_with={"brush_rug", "brush_table"},
        boost=1.2,
        teamwork_phrase="The wider brush made their shared strokes cover more at once.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Max", "Finn", "Sam"]
HELPERS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["calm", "curious", "gentle", "patient", "busy", "cheerful"]


ASP_RULES = r"""
task(Task) :- task_fact(Task).
tool(Tool) :- tool_fact(Tool).
setting(Place) :- setting_fact(Place).

matches(T, U) :- task_uses(T, U), tool_helps(U, T).

valid_story(Place, Task, Tool) :- setting(Place), task(Task), tool(Tool), affords(Place, Task), matches(Task, Tool).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task_fact", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool_fact", uid))
        for a in sorted(u.helps_with):
            lines.append(asp.fact("tool_helps", uid, a))
    for tid in TASKS:
        for uid in TOOLS:
            if any(uid == x for x in TOOLS):
                pass
    for tid, t in TASKS.items():
        for uid in TOOLS:
            if f"brush_{t.id}" in _safe_lookup(TOOLS, uid).helps_with:
                lines.append(asp.fact("task_uses", tid, uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life brushing story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    task = getattr(args, "task", None) or rng.choice([t for t in TASKS if f"brush_{t}" in _safe_lookup(SETTINGS, setting).affords])
    tool = getattr(args, "tool", None) or rng.choice([uid for uid, u in TOOLS.items() if f"brush_{_safe_lookup(TASKS, task).id}" in u.helps_with])
    if f"brush_{_safe_lookup(TASKS, task).id}" not in _safe_lookup(TOOLS, tool).helps_with:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(setting=setting, task=task, tool=tool, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    tool = world.add(Entity(id=params.tool, type="tool", label=_safe_lookup(TOOLS, params.tool).label, phrase=_safe_lookup(TOOLS, params.tool).phrase))
    task = _safe_lookup(TASKS, params.task)

    start_progress = 0.0
    crumbs_left = 5.0
    teamwork = 0.0

    world.say(f"{hero.id} was in {world.setting.place} with {helper.label}.")
    world.say(f"There was {tool.phrase} on the floor, and {hero.id} wanted to {task.first_action}.")
    world.say(f"{hero.id} started to {task.harder_action}, one careful pass after another.")

    world.para()
    world.say(f"At first, the little strokes helped only a little. The {task.label} still held onto the {task.mess}.")
    for _ in range(2):
        crumbs_left -= 0.7
        start_progress += 0.6
        world.say(f"{hero.id} brushed again, and the work looked a bit better.")
    world.say(f"Still, some {task.mess} stayed stuck, so {helper.label} leaned in to help.")
    teamwork += 1.0

    world.para()
    world.say(f"{helper.label.capitalize()} picked up {tool.phrase} and matched {hero.id}'s pace.")
    world.say(_safe_lookup(TOOLS, params.tool).teamwork_phrase)
    for _ in range(3):
        crumbs_left -= 1.1
        start_progress += 1.0
        teamwork += 0.5
        world.say(f"Together they brushed, again and again, in the same direction.")
    crumbs_left = max(0.0, crumbs_left)
    if crumbs_left > 0:
        world.say(f"The {task.mess} was still a little there, so they kept going.")

    world.para()
    crumbs_left = 0.0
    start_progress = 3.2
    world.say(f"In the end, the {task.label} looked neat and soft.")
    world.say(f"{hero.id} smiled, because the repeated brushing finally worked when they did it together.")
    world.say(f"They set {tool.it()} down and looked at the tidy room like it was a small job well done.")

    world.facts.update(
        hero=hero,
        helper=helper,
        tool=tool,
        task=task,
        setting=world.setting,
        repeated=task.repeated_action,
        crumbs_left=crumbs_left,
        progress=start_progress,
        teamwork=teamwork,
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
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    return [
        f'Write a short slice-of-life story about {hero.id} learning to {task.repeated_action} with help from {helper.label}.',
        f"Tell a gentle story where brushing the {task.label} takes patience and teamwork.",
        f'Write a small everyday story that includes the word "brush" and shows repetition making a job easier.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    place = f["setting"].place
    return [
        QAItem(
            question=f"What was {hero.id} trying to do in {place}?",
            answer=f"{hero.id} was trying to {task.repeated_action}.",
        ),
        QAItem(
            question=f"Why did {helper.label} join in?",
            answer=f"{helper.label.capitalize()} joined in because the {task.mess} was still stuck after {hero.id} kept brushing, and teamwork made the job easier.",
        ),
        QAItem(
            question=f"What tool helped them work together?",
            answer=f"They used {tool.phrase} and brushed again and again until the {task.label} looked neat.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {task.label} clean, {hero.id} smiling, and both of them feeling proud of the shared work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to brush something?",
            answer="To brush something means to use a brush to move dust, crumbs, fur, or loose bits away with short strokes.",
        ),
        QAItem(
            question="Why does repeating a small action help sometimes?",
            answer="Repeating a small action can help because each pass removes a little more, and many small changes can make a big difference.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other do a job together, so the task can get done more smoothly.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} ({e.type}) meters={e.meters} memes={e.memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts_and_rules() -> str:
    return asp_program("#show valid_story/3.")


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set((s, t, u) for s in SETTINGS for t in TASKS for u in TOOLS if f"brush_{t}" in _safe_lookup(SETTINGS, s).affords and f"brush_{t}" in _safe_lookup(TOOLS, u).helps_with)
    if clingo_set == py_set:
        print(f"OK: clingo gate matches python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


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
        print(asp_facts_and_rules())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for item in stories:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        combos = []
        for setting in SETTINGS:
            for task in TASKS:
                if f"brush_{task}" not in _safe_lookup(SETTINGS, setting).affords:
                    continue
                for tool in TOOLS:
                    if f"brush_{task}" not in _safe_lookup(TOOLS, tool).helps_with:
                        continue
                    combos.append((setting, task, tool))
        for i, (setting, task, tool) in enumerate(combos):
            p = StoryParams(setting=setting, task=task, tool=tool, name=_safe_lookup(GIRL_NAMES, i % len(GIRL_NAMES)), gender="girl" if i % 2 == 0 else "boy", helper=_safe_lookup(HELPERS, i % len(HELPERS)), seed=base_seed + i)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.task} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
