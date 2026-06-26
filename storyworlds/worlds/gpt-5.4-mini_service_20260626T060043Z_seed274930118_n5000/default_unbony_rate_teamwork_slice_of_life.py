#!/usr/bin/env python3
"""
storyworlds/worlds/default_unbony_rate_teamwork_slice_of_life.py
=================================================================

A small, standalone storyworld about everyday teamwork in a gentle slice-of-life
scene.

Seed premise:
- A child wants to keep up with a cozy daily routine.
- A small snag appears in the ordinary plan.
- The people nearby notice, talk, and work together.
- A simple shared fix makes the day feel warm and complete.

This world keeps the prose concrete and state-driven: a task has to be done, a
pace can be too slow or too fast, and a team can adjust its "default" plan to
help everyone finish together.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    child: object | None = None
    helper: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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
class Setting:
    place: str = "the kitchen"
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    closing: str
    plural: bool = False
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"breakfast", "cleanup"}),
    "balcony": Setting(place="the balcony", affords={"watering", "cleanup"}),
    "community_room": Setting(place="the community room", affords={"crafts", "cleanup"}),
}

TASKS = {
    "breakfast": Task(
        id="breakfast",
        verb="make breakfast together",
        gerund="making breakfast together",
        rush="hurry to the counter",
        risk="the pancake batter could spill",
        keyword="default",
        tags={"default", "teamwork"},
    ),
    "watering": Task(
        id="watering",
        verb="water the plants together",
        gerund="watering the little plants",
        rush="run for the watering can",
        risk="the floor could get slippery",
        keyword="rate",
        tags={"rate", "teamwork"},
    ),
    "crafts": Task(
        id="crafts",
        verb="finish the paper banner together",
        gerund="cutting and gluing the banner",
        rush="reach for the glue stick",
        risk="the paint could smear",
        keyword="unbony",
        tags={"unbony", "teamwork"},
    ),
    "cleanup": Task(
        id="cleanup",
        verb="tidy up the room together",
        gerund="putting everything back in place",
        rush="move too fast through the room",
        risk="the pile could spread out again",
        keyword="default",
        tags={"default", "teamwork"},
    ),
}

TOOLS = [
    Tool(
        id="apron",
        label="an apron",
        phrase="a clean apron",
        helps={"breakfast", "crafts"},
        prep="put on an apron first",
        closing="put on the aprons and kept working side by side",
    ),
    Tool(
        id="towel",
        label="a towel",
        phrase="a folded towel",
        helps={"watering"},
        prep="lay down a towel first",
        closing="laid down the towel and watered the plants more carefully",
    ),
    Tool(
        id="tray",
        label="a tray",
        phrase="a sturdy tray",
        helps={"breakfast"},
        prep="set the bowls on a tray",
        closing="used the tray and carried breakfast together",
    ),
    Tool(
        id="clips",
        label="some paper clips",
        phrase="two paper clips",
        helps={"crafts", "cleanup"},
        prep="clip the loose edges first",
        closing="used the clips and finished the banner together",
        plural=True,
    ),
]

CHILD_NAMES = ["Nina", "Milo", "June", "Owen", "Iris", "Theo", "Lena", "Arlo"]
ADULT_NAMES = ["Mom", "Dad", "Aunt Pia", "Uncle Sam", "Grandma", "Grandpa"]
TRAITS = ["quiet", "cheerful", "curious", "patient", "gentle", "spry"]


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    age_role: str
    helper: str
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


def task_needs_help(task: Task) -> bool:
    return True


def select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.helps:
            return tool
    return None


def explain_rejection(task: Task) -> str:
    return f"(No story: the task '{task.id}' has no fitting teamwork tool in this world.)"


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    task = _safe_lookup(TASKS, params.task)
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.age_role,
        label=params.name,
        traits=[],
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="adult" if params.helper in ADULT_NAMES else "person",
        label=params.helper,
        traits=[],
    ))
    item = world.add(Entity(
        id="task_item",
        type="thing",
        label=task.keyword,
        phrase=task.keyword,
        owner=child.id,
        caretaker=helper.id,
    ))

    tool = select_tool(task)
    world.facts.update(child=child, helper=helper, task=task, item=item, tool=tool)

    world.say(f"{child.id} was a {params.trait} little {child.type} who liked helping at {world.setting.place}.")
    world.say(f"{child.id} liked the default plan for the morning, because it made the day feel calm and familiar.")
    world.say(f"Still, {child.id} wanted to {task.verb}, and {task.gerund} was the kind of small job that felt good to finish.")

    world.para()
    world.say(f"At {world.setting.place}, {child.id} started to {task.rush}, but {task.risk}.")
    world.say(f"{helper.id} noticed the trouble and said that the pace was a little too fast for one person to handle alone.")
    world.say(f"{child.id} looked at {helper.id}, and the two of them paused like a tiny team planning the next step.")

    world.para()
    if tool:
        world.say(f"{helper.id} picked up {tool.phrase} and suggested, \"Let's {tool.prep} and do it together.\"")
        world.say(f"{child.id} nodded right away, and soon they {tool.closing}.")
    else:
        world.say(f"{helper.id} found a slower way to work and showed {child.id} how to keep the task steady.")
    world.say(f"In the end, {child.id} was still smiling, {task.gerund}, and the room felt neat and warm again.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = _safe_fact(world, f, "task")
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    return [
        f"Write a slice-of-life story about {child.id} and {helper.id} working as a team at {world.setting.place}.",
        f"Tell a gentle story where a child wants to {task.verb} but needs help finding a better pace.",
        f"Write a short everyday story that includes the words default, unbony, and rate in a natural way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    task = _safe_fact(world, f, "task")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was about {child.id}, who wanted to {task.verb} with help from {helper.id}.",
        ),
        QAItem(
            question=f"What made {child.id} slow down and ask for teamwork?",
            answer=f"{task.risk} made the job harder to do alone, so {helper.id} stepped in to help.",
        ),
        QAItem(
            question=f"What tool or idea helped the team finish the job?",
            answer=(
                f"They used {tool.phrase} if it was needed, and they also chose a steadier rate so the work stayed easy and calm."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} smiling, the task finished, and the place looking tidy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other do a job, so the work goes better and feels easier.",
        ),
        QAItem(
            question="What is a default plan?",
            answer="A default plan is the usual plan you use when nothing special needs to change.",
        ),
        QAItem(
            question="What does rate mean?",
            answer="Rate can mean how fast something happens, like the pace of a task or the speed of a flow.",
        ),
        QAItem(
            question="What does it mean to do something at a steady rate?",
            answer="Doing something at a steady rate means keeping a calm, even pace instead of rushing.",
        ),
        QAItem(
            question="What is a slice-of-life story?",
            answer="A slice-of-life story shows a small everyday moment, like helping at home or working together in a familiar place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", task="breakfast", name="Nina", age_role="girl", helper="Mom", trait="cheerful"),
    StoryParams(place="balcony", task="watering", name="Milo", age_role="boy", helper="Dad", trait="curious"),
    StoryParams(place="community_room", task="crafts", name="June", age_role="girl", helper="Aunt Pia", trait="patient"),
]


ASP_RULES = r"""
child(C).
helper(H).
task(T).
place(P).

needs_tool(T) :- task(T).
good_fit(T,U) :- task(T), tool(U), helps(U,T).
team_story(P,T) :- place(P), task(T), needs_tool(T), good_fit(T,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for t in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, t))
    for name in CHILD_NAMES + ADULT_NAMES:
        lines.append(asp.fact("child", name))
        lines.append(asp.fact("helper", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show team_story/2."))
    return sorted(set(asp.atoms(model, "team_story")))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for p in SETTINGS:
        for t in TASKS:
            if select_tool(_safe_lookup(TASKS, t)) is not None:
                out.append((p, t))
    return out


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life teamwork storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--role", choices=["girl", "boy"])
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
    if getattr(args, "task", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        if select_tool(task) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    task = getattr(args, "task", None) or rng.choice(list(TASKS))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    role = getattr(args, "role", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or rng.choice(ADULT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, name=name, age_role=role, helper=helper, trait=trait)


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
        print(asp_program("#show team_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible place/task combos:\n")
        for p, t in combos:
            print(f"  {p:15} {t}")
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
