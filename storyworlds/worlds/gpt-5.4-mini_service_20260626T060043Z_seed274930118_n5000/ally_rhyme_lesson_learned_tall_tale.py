#!/usr/bin/env python3
"""
storyworlds/worlds/ally_rhyme_lesson_learned_tall_tale.py
==========================================================

A small tall-tale storyworld about a boastful feat, a steadfast ally, a comic
setback, and a lesson learned in rhyme.

Premise:
- A child wants to perform an outsized task in a wide-open place.
- A loyal ally helps with a simple tool and a steady rhyme.
- The task goes wrong in a way that makes a new method necessary.
- The ending proves the lesson: going slow, sharing the load, and using a
  rhyme to remember the safer way.

This world models physical meters and emotional memes, and it keeps the prose
child-facing and state-driven rather than a fixed paragraph template.
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
# Core world model
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
    ally_of: Optional[str] = None
    instrument: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ally: object | None = None
    hero: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        for k in ("bent", "scattered", "stuck", "dusty", "safe"):
            self.meters.setdefault(k, 0.0)
        for k in ("pride", "worry", "joy", "shame", "resolve", "friendship", "relief", "lesson"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    place: str = "the prairie"
    wide: bool = True
    echoes: bool = True
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
    trouble: str
    outcome_bad: str
    outcome_good: str
    keyword: str
    requires_ally: bool = True
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
    phrase: str
    helps: str
    safe_method: str
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
        self.fired: set[tuple] = set()
        self.task: Optional[Task] = None

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.task = self.task
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "prairie": Setting(place="the prairie", wide=True, echoes=True),
    "hill": Setting(place="the hill", wide=True, echoes=True),
    "riverbank": Setting(place="the riverbank", wide=True, echoes=True),
}

TASKS = {
    "stack": Task(
        id="stack",
        verb="stack the tallest tower",
        gerund="stacking the tallest tower",
        rush="dash at the pile of blocks",
        trouble="the blocks could tumble",
        outcome_bad="a heap of wobbly blocks",
        outcome_good="a neat tower that stood up straight",
        keyword="tower",
    ),
    "pullcart": Task(
        id="pullcart",
        verb="pull the big cart",
        gerund="pulling the big cart",
        rush="yank the cart across the ground",
        trouble="the cart could get stuck",
        outcome_bad="a cart sunk in the dirt",
        outcome_good="a cart rolling easy and true",
        keyword="cart",
    ),
    "kite": Task(
        id="kite",
        verb="fly the giant kite",
        gerund="flying the giant kite",
        rush="run with the kite rope",
        trouble="the kite could dive",
        outcome_bad="a kite nosedown in a bush",
        outcome_good="a kite sailing high and bright",
        keyword="kite",
    ),
}

TOOLS = {
    "buddy_rope": Tool(
        id="buddy_rope",
        label="a buddy rope",
        phrase="a bright buddy rope",
        helps="share the pull",
        safe_method="walk together and take steady steps",
    ),
    "song": Tool(
        id="song",
        label="a counting song",
        phrase="a counting song that kept the timing right",
        helps="keep the rhythm",
        safe_method="sing and lift on the beat",
    ),
    "lever": Tool(
        id="lever",
        label="a long lever",
        phrase="a long lever with a smooth grip",
        helps="pry things free",
        safe_method="slide the lever under and lift slowly",
    ),
}

NAMES = ["Ada", "Bea", "Cleo", "Dani", "Eli", "Finn", "Gus", "Hana", "Ivy", "Jude"]
TRAITS = ["bold", "cheery", "quick", "stubborn", "sparky", "lively"]


# ---------------------------------------------------------------------------
# World parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility / reasonableness
# ---------------------------------------------------------------------------
    params: object | None = None
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, task) for place in SETTINGS for task in TASKS]


def explain_rejection(task: Task) -> str:
    return f"(No story: {task.verb} needs a real ally and a safer method, but none is compatible here.)"


def choose_tool(task: Task) -> Optional[Tool]:
    if task.id == "stack":
        return TOOLS["song"]
    if task.id == "pullcart":
        return TOOLS["buddy_rope"]
    if task.id == "kite":
        return TOOLS["lever"]
    return None


# ---------------------------------------------------------------------------
# Motion and narration
# ---------------------------------------------------------------------------

def propagate(world: World) -> None:
    task = world.task
    if task is None:
        return
    hero = world.get("hero")
    ally = world.get("ally")
    tool = world.get("tool")
    if hero.meters["wobble"] >= 1 and ally.memes["resolve"] >= 1:
        if task.id == "stack":
            hero.meters["stacked"] += 1
            hero.meters["wobble"] = max(0.0, hero.meters["wobble"] - 1)
        elif task.id == "pullcart":
            hero.meters["pulled"] += 1
            hero.meters["stuck"] = max(0.0, hero.meters["stuck"] - 1)
        elif task.id == "kite":
            hero.meters["soared"] += 1
            hero.meters["tangled"] = max(0.0, hero.meters["tangled"] - 1)
        ally.memes["joy"] += 1
        hero.memes["relief"] += 1
        hero.memes["lesson"] += 1


def opening(world: World, hero: Entity, ally: Entity, task: Task) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was a {hero.memes.get('trait_word', 'bold')} "
        f"{hero.type} with a big dream: {task.verb}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {task.gerund}, and {ally.id} stayed close as {hero.pronoun('possessive')} ally."
    )


def boast(world: World, hero: Entity, task: Task) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} laughed and said, \"Watch me!\" Then {hero.pronoun()} tried to {task.rush}."
    )


def trouble(world: World, hero: Entity, task: Task) -> None:
    hero.meters["wobble"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But {task.trouble}, and soon the day looked like {task.outcome_bad}."
    )


def ally_steps_in(world: World, hero: Entity, ally: Entity, task: Task, tool: Tool) -> None:
    ally.memes["resolve"] += 1
    ally.memes["friendship"] += 1
    world.say(
        f"Then {ally.id} stepped in with {tool.phrase}; {tool.helps}."
    )
    world.say(
        f'\"Easy now,\" said {ally.id}. \"Try this rhyme: '
        f'\"Slow and low, then steady go.\"\"'
    )


def lesson_turn(world: World, hero: Entity, ally: Entity, task: Task, tool: Tool) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} took a breath, nodded to {ally.id}, and chose to {tool.safe_method}."
    )
    if task.id == "stack":
        hero.meters["stacked"] += 1
        hero.meters["wobble"] = 0
        world.say(
            f"The blocks stopped wobbling, and the tower rose straight as a fence post."
        )
    elif task.id == "pullcart":
        hero.meters["pulled"] += 1
        hero.meters["stuck"] = 0
        world.say(
            f"The cart rolled free, humming over the dirt like it had learned to dance."
        )
    elif task.id == "kite":
        hero.meters["soared"] += 1
        hero.meters["tangled"] = 0
        world.say(
            f"The kite climbed the sky and stayed there, bright as a flag on a windy hill."
        )
    propagate(world)
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"In the end, {hero.id} remembered the rhyme, and {ally.id} grinned like a lantern in the dusk."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(setting: Setting, task: Task, name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="boy" if name in {"Eli", "Finn", "Gus", "Jude"} else "girl"))
    ally = world.add(Entity(id="ally", kind="character", type="friend", label="ally"))
    tool_def = choose_tool(task)
    if tool_def is None:
        pass
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=tool_def.label, phrase=tool_def.phrase, owner=hero.id, ally_of=ally.id, instrument=tool_def.id))
    world.task = task

    hero.memes["trait_word"] = trait  # harmless internal note for narration
    opening(world, hero, ally, task)
    world.para()
    boast(world, hero, task)
    trouble(world, hero, task)
    world.para()
    ally_steps_in(world, hero, ally, task, tool_def)
    lesson_turn(world, hero, ally, task, tool_def)
    world.facts.update(hero=hero, ally=ally, tool=tool, task=task, setting=setting, tool_def=tool_def)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, ally, task = f["hero"], f["ally"], f["task"]
    return [
        f'Write a tall-tale story for a child about {hero.id}, an ally, and a rhyme that teaches a lesson.',
        f"Tell a playful story where {hero.id} tries to {task.verb} and {ally.id} helps with a rhyme.",
        f"Write a short tall tale that ends with a lesson learned and a brave helper named {ally.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ally, task, tool = f["hero"], f["ally"], f["task"], f["tool_def"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the beginning?",
            answer=f"{hero.id} wanted to {task.verb} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Who helped when {task.trouble} happened?",
            answer=f"{ally.id} helped with {tool.phrase} and a little rhyme.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"The lesson was to slow down, share the load, and try the safer way instead of rushing ahead.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud, relieved, and happier after learning the new way.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "rhyme": [("What is a rhyme?", "A rhyme is a pattern of words that sound alike at the end, like sing and bring.")],
    "lesson": [("What is a lesson?", "A lesson is something helpful you learn that can guide your choices later.")],
    "ally": [("What is an ally?", "An ally is a helper on your side who supports you with a task or a problem.")],
    "tall tale": [("What is a tall tale?", "A tall tale is a playful story with a giant-feeling feat, a big voice, and a fun exaggeration.")],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for key in ("ally", "rhyme", "lesson", "tall tale") for q, a in WORLD_KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "trait_word"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:6} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
good_task(T) :- task(T), tool(Tool), helps_tool(Tool, T).
lesson_learned(H) :- hero(H), helper(A), ally_of(A, H), rhyme_available, good_task(T), task(T).
compatible(P, T) :- setting(P), task(T), good_task(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_keyword", tid, t.keyword))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helps_tool", tid, tid.replace("_", "")))
    lines.append(asp.fact("rhyme_available"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "ally"))
    lines.append(asp.fact("ally_of", "ally", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show compatible/2.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = {(p, t) for p in SETTINGS for t in TASKS}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about an ally, a rhyme, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name", choices=NAMES)
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
    if getattr(args, "task", None) and getattr(args, "task", None) not in TASKS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    task = getattr(args, "task", None) or rng.choice(list(TASKS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), params.name, params.trait)
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
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:")
        for p, t in combos:
            print(f"  {p:10} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            for task in TASKS:
                params = StoryParams(place=place, task=task, name=random.choice(NAMES), trait=random.choice(TRAITS))
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
