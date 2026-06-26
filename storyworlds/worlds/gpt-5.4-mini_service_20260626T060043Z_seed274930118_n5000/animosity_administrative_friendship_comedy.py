#!/usr/bin/env python3
"""
A tiny storyworld about administrative fuss, friendship, and comic repairs.

Premise:
- Two friends try to finish a small administrative job together.
- A strict rule or lost paper creates friction and a little animosity.
- The friends argue, then use a silly, practical teamwork trick to fix the mess.
- The ending proves that friendship can survive forms, stamps, and confusion.

This file is a standalone storyworld script.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    a: object | None = None
    b: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    place: str
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
    mess: str
    soil: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
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


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    fixes: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False
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


def bump(obj: Entity, key: str, amount: float = 1.0) -> None:
    obj.meters[key] = obj.meters.get(key, 0.0) + amount


def mood(obj: Entity, key: str, amount: float = 1.0) -> None:
    obj.memes[key] = obj.memes.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "office": Setting(place="the office", affords={"forms", "stamps", "sorting"}),
    "hall": Setting(place="the hallway desk", affords={"forms", "stamps"}),
    "library": Setting(place="the library counter", affords={"forms", "sorting"}),
}

TASKS = {
    "forms": Task(
        id="forms",
        verb="fill out the forms",
        gerund="filling out forms",
        rush="snatch the forms and scribble fast",
        mess="ink",
        soil="ink-smudged",
        keyword="forms",
        tags={"administrative"},
    ),
    "stamps": Task(
        id="stamps",
        verb="stamp the papers",
        gerund="stamping papers",
        rush="jiggle the stamp too hard",
        mess="ink",
        soil="ink-spattered",
        keyword="stamp",
        tags={"administrative"},
    ),
    "sorting": Task(
        id="sorting",
        verb="sort the files",
        gerund="sorting files",
        rush="pile everything in a silly heap",
        mess="paper",
        soil="a paper tornado",
        keyword="files",
        tags={"administrative"},
    ),
}

PRIZES = {
    "badge": Prize(label="badge", phrase="a bright helper badge", type="badge", region="torso"),
    "shirt": Prize(label="shirt", phrase="a neat blue shirt", type="shirt", region="torso"),
    "clipboard": Prize(label="clipboard", phrase="a striped clipboard cover", type="clipboard", region="hands"),
}

AIDS = [
    Aid(
        id="sticker",
        label="a cheerful sticker chart",
        prep="put up a cheerful sticker chart",
        tail="set up the sticker chart",
        fixes={"forms", "sorting"},
        covers={"hands"},
    ),
    Aid(
        id="washcloth",
        label="a damp washcloth",
        prep="grab a damp washcloth",
        tail="used the damp washcloth",
        fixes={"forms", "stamps"},
        covers={"torso", "hands"},
    ),
    Aid(
        id="clip",
        label="a giant paper clip",
        prep="use a giant paper clip",
        tail="clipped the papers together",
        fixes={"sorting"},
        covers={"hands"},
    ),
]

NAMES = ["Mina", "Jo", "Toby", "Lena", "Pip", "Anya", "Noah", "Rae"]
TRAITS = ["friendly", "silly", "patient", "quick-witted", "cheerful", "curious"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name_a: str
    name_b: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def task_at_risk(task: Task, prize: Prize) -> bool:
    return True if prize.region in {"torso", "hands"} else False


def select_aid(task: Task, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if task.id in aid.fixes:
            if prize.region in aid.covers:
                return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = _safe_lookup(TASKS, task_id)
            for prize_id, prize in PRIZES.items():
                if task_at_risk(task, prize) and select_aid(task, prize):
                    out.append((place, task_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Causal narrative
# ---------------------------------------------------------------------------

def predict_mess(world: World, task: Task, prize_id: str) -> bool:
    prize = world.get(prize_id)
    return task.mess == "ink" and prize.region in {"torso", "hands"}


def intro(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"{a.id} and {b.id} were best friends who liked to laugh at boring jobs."
    )
    world.say(
        f"They called small office chores an adventure, even when the papers looked sleepy."
    )


def setup(world: World, a: Entity, b: Entity, task: Task, prize: Entity) -> None:
    mood(a, "friendship", 1)
    mood(b, "friendship", 1)
    world.say(
        f"One day, they went to {world.setting.place} to {task.verb}."
    )
    world.say(
        f"{a.id} wore {a.pronoun('possessive')} {prize.label}, because it made {a.id} feel ready."
    )


def conflict(world: World, a: Entity, b: Entity, task: Task, prize: Entity) -> None:
    if predict_mess(world, task, prize.id):
        mood(a, "animosity", 1)
        mood(b, "animosity", 1)
        world.say(
            f"Then the stamp pad tipped, and the papers got {task.soil}."
        )
        world.say(
            f"{b.id} groaned, and {a.id} snapped back with a grumpy look."
        )
        world.say(
            f"For a moment, the two friends sounded like tiny rival managers in a very silly office."
        )


def try_bad_fix(world: World, a: Entity, task: Task) -> None:
    world.say(
        f"{a.id} tried to {task.rush}, but that only made the pile wobble more."
    )


def resolve(world: World, a: Entity, b: Entity, task: Task, prize: Entity) -> Optional[Aid]:
    aid = select_aid(task, prize)
    if aid is None:
        return None
    world.say(
        f"Then {b.id} grinned and said, \"Let's not fight the papers. Let's be clever.\""
    )
    world.say(
        f"They decided to {aid.prep}."
    )
    world.say(
        f"That worked: the mess stayed under control, and {aid.tail}."
    )
    mood(a, "friendship", 2)
    mood(b, "friendship", 2)
    a.memes["animosity"] = 0.0
    b.memes["animosity"] = 0.0
    world.say(
        f"{a.id} laughed so hard that {a.id}'s serious face vanished."
    )
    world.say(
        f"By the end, {a.id} and {b.id} were side by side again, making the office feel less stern and more funny."
    )
    return aid


def tell(setting: Setting, task: Task, prize_cfg: Prize, name_a: str, name_b: str) -> World:
    world = World(setting)
    a = world.add(Entity(id=name_a, kind="character", type="boy", traits=["friendly", "silly"]))
    b = world.add(Entity(id=name_b, kind="character", type="girl", traits=["friendly", "cheerful"]))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=a.id,
            region=prize_cfg.region,
        )
    )

    intro(world, a, b)
    world.para()
    setup(world, a, b, task, prize)
    conflict(world, a, b, task, prize)
    try_bad_fix(world, a, task)
    world.para()
    aid = resolve(world, a, b, task, prize)
    world.facts.update(a=a, b=b, prize=prize, task=task, aid=aid, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, task, prize = f["a"], f["b"], f["task"], f["prize"]
    return [
        f'Write a short comedy about two friends at {world.setting.place} dealing with {task.keyword}.',
        f"Tell a child-friendly story where {a.id} and {b.id} try to {task.verb} without ruining {a.pronoun('possessive')} {prize.label}.",
        f'Create a funny story about friendship, administrative fuss, and a messy {task.keyword}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, task, prize = f["a"], f["b"], f["task"], f["prize"]
    aid = _safe_fact(world, f, "aid")
    qa = [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {a.id} and {b.id}, two friends who try to handle a small office job together.",
        ),
        QAItem(
            question=f"What job did they try to do at {world.setting.place}?",
            answer=f"They tried to {task.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What problem made the job funny and stressful?",
            answer=f"The papers got {task.soil}, which made the work feel messy and caused a little animosity.",
        ),
    ]
    if aid is not None:
        qa.append(
            QAItem(
                question=f"How did they fix the problem?",
                answer=f"They used {aid.label} and worked together, so the mess stayed under control and the task got finished.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did the friends feel at the end?",
            answer=f"They felt friendly again, and the ending showed that their friendship was stronger than the office trouble.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does administrative mean?",
            answer="Administrative means connected to organizing, managing, or taking care of office work and records.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond between people who like each other, help each other, and enjoy being together.",
        ),
        QAItem(
            question="Why can comedy make a story fun?",
            answer="Comedy uses funny moments, silly mistakes, and playful surprises to make a story feel light and enjoyable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
at_risk(P) :- prize(P), worn_on(P, torso).
at_risk(P) :- prize(P), worn_on(P, hands).

fix(Task, Aid) :- task(Task), aid(Aid), fixes(Aid, Task).
valid(Place, Task, Prize) :- affords(Place, Task), at_risk(Prize), fix(Task, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, prize.region))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for t in sorted(aid.fixes):
            lines.append(asp.fact("fixes", aid.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about friendship and administrative fuss.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        pass
    place, task, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        task=task,
        prize=prize,
        name_a=getattr(args, "name_a", None) or rng.choice(NAMES),
        name_b=getattr(args, "name_b", None) or rng.choice([n for n in NAMES if n != getattr(args, "name_a", None)]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), params.name_a, params.name_b)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id} ({e.type}) " + " ".join(bits))
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
    StoryParams(place="office", task="forms", prize="shirt", name_a="Mina", name_b="Jo"),
    StoryParams(place="hall", task="stamps", prize="badge", name_a="Toby", name_b="Rae"),
    StoryParams(place="library", task="sorting", prize="clipboard", name_a="Lena", name_b="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos")
        for combo in combos:
            print(combo)
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
            params = valid_story_params(args, random.Random(seed))
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
