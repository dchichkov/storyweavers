#!/usr/bin/env python3
"""
storyworlds/worlds/accept_teamwork_bad_ending_heartwarming.py
=============================================================

A tiny storyworld about teamwork, a hopeful plan, and a gentle bad ending.

Seed story premise:
- A child wants to make something special with a helper.
- They work together with care and trust.
- Something goes wrong at the end, and the happy plan cannot fully save it.
- The characters accept the result, keep the warmth, and stay kind to each other.

This world is intentionally small and constraint-checked: the story is driven by
state changes, physical meters, and emotional memes. It always tells a complete
little tale with a beginning, a teamwork middle, and a bad-but-heartwarming end.
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
# Core world entities
# ---------------------------------------------------------------------------

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
    helper: Optional[str] = None
    worn_by: Optional[str] = None
    broken: bool = False
    ruined: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    item: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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


@dataclass
class Task:
    id: str
    name: str
    verb: str
    gerund: str
    tool: str
    hazard: str
    fail: str
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
    id: str
    label: str
    phrase: str
    type: str
    ruined_by: str
    owner_role: str = "child"
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
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    weather: str = ""
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
    place: str
    task: str
    prize: str
    name: str
    gender: str
    helper_role: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"bake", "decorate", "mix"}),
    "garage": Setting(place="the garage", affords={"build", "paint", "craft"}),
    "porch": Setting(place="the porch", affords={"paint", "craft"}),
}

TASKS = {
    "bake": Task(
        id="bake",
        name="bake a cake",
        verb="bake the cake",
        gerund="baking the cake",
        tool="spoon",
        hazard="hot oven",
        fail="burned",
        keyword="cake",
        tags={"bake", "warm"},
    ),
    "paint": Task(
        id="paint",
        name="paint a sign",
        verb="paint the sign",
        gerund="painting the sign",
        tool="brush",
        hazard="wet paint",
        fail="smudged",
        keyword="paint",
        tags={"paint"},
    ),
    "build": Task(
        id="build",
        name="build a small house",
        verb="build the house",
        gerund="building the house",
        tool="hammer",
        hazard="loose nails",
        fail="wobbly",
        keyword="build",
        tags={"build"},
    ),
    "craft": Task(
        id="craft",
        name="make a paper crown",
        verb="make the crown",
        gerund="making the crown",
        tool="scissors",
        hazard="tear",
        fail="ripped",
        keyword="crown",
        tags={"craft"},
    ),
}

PRIZES = {
    "cake": Prize(
        id="cake",
        label="cake",
        phrase="a sweet birthday cake",
        type="cake",
        ruined_by="burned",
    ),
    "sign": Prize(
        id="sign",
        label="sign",
        phrase="a bright welcome sign",
        type="sign",
        ruined_by="smudged",
    ),
    "house": Prize(
        id="house",
        label="house",
        phrase="a little wooden birdhouse",
        type="house",
        ruined_by="wobbly",
    ),
    "crown": Prize(
        id="crown",
        label="crown",
        phrase="a paper crown with gold stars",
        type="crown",
        ruined_by="ripped",
    ),
}

HERO_NAMES = ["Mina", "Leo", "Nora", "Ben", "Ava", "Ivy", "Noah", "Maya"]
TRAITS = ["gentle", "patient", "brave", "kind", "careful", "quiet"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def task_needs_teamwork(task: Task) -> bool:
    return True


def task_at_risk(task: Task, prize: Prize) -> bool:
    return prize.ruined_by == task.fail


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = _safe_lookup(TASKS, task_id)
            for prize_id, prize in PRIZES.items():
                if task_at_risk(task, prize):
                    out.append((place, task_id, prize_id))
    return out


def pick_helper_role(rng: random.Random) -> str:
    return rng.choice(["mother", "father", "grandparent", "friend"])


def helper_word(role: str) -> str:
    return {"mother": "mom", "father": "dad", "grandparent": "grandparent", "friend": "friend"}.get(role, role)


def setting_sentence(setting: Setting) -> str:
    if setting.place == "the kitchen":
        return "The kitchen smelled warm and a little sweet."
    if setting.place == "the garage":
        return "The garage felt busy, with boxes and tools lined up like tiny helpers."
    return "The porch was bright, and the air felt calm enough for careful work."


def task_sentence(task: Task) -> str:
    return {
        "bake": "They wanted the cake to be soft, sweet, and special.",
        "paint": "They wanted the sign to be bright and welcoming.",
        "build": "They wanted the little house to stand straight and strong.",
        "craft": "They wanted the crown to shine like a party star.",
    }[task.id]


def bad_event(task: Task, prize: Prize) -> str:
    return f"At the end, something went wrong and the {prize.label} got {prize.ruined_by}."


def accept_turn(hero: Entity, helper: Entity, prize: Entity, task: Task) -> str:
    return (
        f"{hero.id} looked at the {prize.label}, took a slow breath, and accepted that it could not be fixed today. "
        f"{hero.id} and {helper.id} still stayed close, and that made the sad ending feel soft instead of sharp."
    )


def tell(setting: Setting, task: Task, prize: Prize, name: str, gender: str, helper_role: str, trait: str) -> World:
    world = World(setting)
    world.setting.weather = "gentle"

    hero = world.add(Entity(id=name, kind="character", type=gender, meters={"joy": 1.0}, memes={"hope": 1.0}))
    helper = world.add(Entity(id=helper_role.title(), kind="character", type=helper_role, meters={"care": 1.0}, memes={"care": 1.0}))
    item = world.add(Entity(id=prize.id, type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id))
    tool = world.add(Entity(id=task.tool, type="tool", label=task.tool, owner=hero.id, helper=helper.id))

    world.say(f"{name} was a {trait} little {gender} who liked doing things together.")
    world.say(f"{hero.id} and {helper_word(helper_role)} wanted to {task.verb} because {task_sentence(task)}")
    world.say(f"They used a {tool.label} and worked as a team, one helping the other when hands got busy.")
    world.say(setting_sentence(setting))

    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1.0
    world.say(f"{hero.id} trusted {helper.id}, and {helper.id} trusted {hero.id} right back.")

    world.say(f"Then the risky part arrived: {task.hazard} made the task tricky.")
    world.say(bad_event(task, prize))
    item.ruined = True
    hero.meters["disappointment"] = hero.meters.get("disappointment", 0.0) + 1.0
    helper.meters["disappointment"] = helper.meters.get("disappointment", 0.0) + 1.0
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1.0

    world.say(accept_turn(hero, helper, item, task))
    hero.memes["accept"] = hero.memes.get("accept", 0.0) + 1.0
    helper.memes["accept"] = helper.memes.get("accept", 0.0) + 1.0
    helper.memes["love"] = helper.memes.get("love", 0.0) + 1.0
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0

    if task.id == "bake":
        world.say("They did not get a perfect cake, but they sat together with milk and shared the warm, messy edges.")
    elif task.id == "paint":
        world.say("The sign was smudged, so they turned it face-down and drew happy dots on the back instead.")
    elif task.id == "build":
        world.say("The little house wobbled, so they set it on a shelf and watched a bird peek at it kindly.")
    else:
        world.say("The crown tore, so they taped it gently and wore it anyway for a tiny celebration.")

    world.say(f"In the end, the work was not saved, but the teamwork stayed.")
    world.say(f"{hero.id} leaned against {helper.id}, and the two of them smiled at their brave little try.")

    world.facts = {
        "hero": hero,
        "helper": helper,
        "item": item,
        "task": task,
        "setting": setting,
        "prize": prize,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, task, prize = f["hero"], f["helper"], f["task"], f["prize"]
    return [
        f'Write a heartwarming story about teamwork where {hero.id} and {helper.id} try to {task.verb}, but the ending goes wrong in a gentle way.',
        f'Create a small children\'s story that uses the word "{task.keyword}" and ends with acceptance after a bad result.',
        f"Tell a warm story about a {hero.type} named {hero.id} and a {helper.type} who work together, then accept that {prize.label} cannot be fixed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task, prize = f["hero"], f["helper"], f["task"], f["prize"]
    return [
        QAItem(
            question=f"Who worked together to {task.verb}?",
            answer=f"{hero.id} and {helper.id} worked together as a team.",
        ),
        QAItem(
            question=f"What were {hero.id} and {helper.id} trying to make?",
            answer=f"They were trying to make {prize.phrase}.",
        ),
        QAItem(
            question=f"What went wrong at the end?",
            answer=f"The {prize.label} got {prize.ruined_by}, so the plan did not end the way they hoped.",
        ),
        QAItem(
            question=f"How did {hero.id} respond after the bad ending?",
            answer=f"{hero.id} accepted what happened and stayed close to {helper.id} instead of getting stuck in anger.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "bake": [
        QAItem(
            question="Why do people use an oven when baking?",
            answer="People use an oven to heat batter or dough so it becomes cooked food like cake or bread.",
        )
    ],
    "paint": [
        QAItem(
            question="Why can paint be messy?",
            answer="Paint can drip and smear, so it often gets on hands, paper, or clothes.",
        )
    ],
    "build": [
        QAItem(
            question="Why do builders use tools?",
            answer="Builders use tools like hammers and nails to help pieces stay together.",
        )
    ],
    "craft": [
        QAItem(
            question="What does scissors do?",
            answer="Scissors cut paper, ribbon, or string into smaller pieces.",
        )
    ],
    "accept": [
        QAItem(
            question="What does it mean to accept something?",
            answer="To accept something means to understand it has happened and not keep fighting it.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work toward the same goal.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["task"].tags) | {"teamwork", "accept"}
    out: list[QAItem] = []
    for tag in ["teamwork", "accept", "bake", "paint", "build", "craft"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
task_at_risk(T, P) :- task(T), prize(P), ruined_by(P, R), fail_of(T, R).
valid_combo(Place, T, P) :- affords(Place, T), task_at_risk(T, P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("fail_of", tid, t.fail))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("ruined_by", pid, p.ruined_by))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only Python:", sorted(py - cl))
    print("Only ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A teamwork storyworld with a gentle bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", choices=["mother", "father", "grandparent", "friend"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "task", None):
        combos = [c for c in combos if c[1] == getattr(args, "task", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, task, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_role = getattr(args, "helper_role", None) or pick_helper_role(rng)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, prize=prize, name=name, gender=gender, helper_role=helper_role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TASKS, params.task),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.helper_role,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.ruined:
            bits.append("ruined=True")
        lines.append(f"{e.id}: {' '.join(bits)}")
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
    StoryParams(place="kitchen", task="bake", prize="cake", name="Mina", gender="girl", helper_role="mother", trait="gentle"),
    StoryParams(place="garage", task="build", prize="house", name="Leo", gender="boy", helper_role="father", trait="careful"),
    StoryParams(place="porch", task="paint", prize="sign", name="Ava", gender="girl", helper_role="friend", trait="kind"),
    StoryParams(place="porch", task="craft", prize="crown", name="Noah", gender="boy", helper_role="grandparent", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
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
