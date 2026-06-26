#!/usr/bin/env python3
"""
A bedtime-story world about a child discovering a vocation, weighing an option,
and solving a small kitchen problem with a gentle transformation.

The seed image behind this world:
- A sleepy child in a warm kitchen
- A spoonful of lard waiting on the counter
- Two possible options
- A quiet inner monologue
- A small problem solved through careful choosing
- A final transformation: simple ingredients become a golden treat, and worry
  becomes confidence
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
# Story data model
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ingredient: object | None = None
    mentor: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    mood: str
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
class Vocation:
    id: str
    label: str
    dream: str
    tool: str
    calm_result: str
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
class Problem:
    id: str
    label: str
    inner_worry: str
    outer_issue: str
    option_hint: str
    transformation: str
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
class Option:
    id: str
    label: str
    action: str
    safe: bool
    solves: set[str]
    transforms: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(
        place="the warm kitchen",
        mood="quiet and sleepy",
        affords={"bake", "mix"},
    ),
    "pantry": Setting(
        place="the pantry",
        mood="soft and cozy",
        affords={"bake", "sort"},
    ),
    "bakery": Setting(
        place="the little bakery",
        mood="golden and kind",
        affords={"bake", "mix"},
    ),
}

VOCATIONS = {
    "baker": Vocation(
        id="baker",
        label="baker",
        dream="to become a baker",
        tool="rolling pin",
        calm_result="a tray of golden buns",
        tags={"food", "warm"},
    ),
    "cook": Vocation(
        id="cook",
        label="cook",
        dream="to become a cook",
        tool="wooden spoon",
        calm_result="a gentle supper",
        tags={"food", "home"},
    ),
    "helper": Vocation(
        id="helper",
        label="helper",
        dream="to become a helper",
        tool="little apron",
        calm_result="a tidy counter",
        tags={"home", "gentle"},
    ),
}

PROBLEMS = {
    "too_hard": Problem(
        id="too_hard",
        label="hard dough",
        inner_worry="the dough might stay stiff and stubborn",
        outer_issue="the bowl was too dry",
        option_hint="something soft should be added",
        transformation="the dough softened and yielded",
        tags={"bake", "food"},
    ),
    "too_plain": Problem(
        id="too_plain",
        label="plain dough",
        inner_worry="the bun might feel dull and unfinished",
        outer_issue="the dough needed richness",
        option_hint="something rich should be stirred in",
        transformation="the dough turned smooth and tender",
        tags={"bake", "food"},
    ),
    "too_messy": Problem(
        id="too_messy",
        label="messy counter",
        inner_worry="the child could not think with crumbs everywhere",
        outer_issue="the counter was crowded",
        option_hint="something should be cleared away",
        transformation="the counter became calm and clear",
        tags={"home"},
    ),
}

OPTIONS = {
    "lard": Option(
        id="lard",
        label="lard",
        action="stir in a spoonful of lard",
        safe=True,
        solves={"too_hard", "too_plain"},
        transforms="the dough became soft, flaky, and easy to shape",
        tags={"food", "bake"},
    ),
    "butter": Option(
        id="butter",
        label="butter",
        action="add a little butter",
        safe=True,
        solves={"too_plain"},
        transforms="the dough grew tender and fragrant",
        tags={"food", "bake"},
    ),
    "tidy": Option(
        id="tidy",
        label="tidy cloth",
        action="wipe the crumbs into a neat pile",
        safe=True,
        solves={"too_messy"},
        transforms="the counter looked peaceful again",
        tags={"home"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ada", "Ivy", "Mila"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Owen", "Milo", "Finn"]
TRAITS = ["curious", "gentle", "sleepy", "brave", "thoughtful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    vocation: str
    problem: str
    option: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for v_id in VOCATIONS:
            for p_id, prob in PROBLEMS.items():
                for o_id, opt in OPTIONS.items():
                    if "bake" in setting.affords and (o_id in {"lard", "butter"}):
                        if p_id in opt.solves:
                            combos.append((s_id, p_id, o_id))
                    if o_id == "tidy" and p_id == "too_messy":
                        combos.append((s_id, p_id, o_id))
    return sorted(set(combos))


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    vocation = _safe_lookup(VOCATIONS, params.vocation)
    problem = _safe_lookup(PROBLEMS, params.problem)
    option = _safe_lookup(OPTIONS, params.option)

    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    mentor = world.add(Entity(id="mentor", kind="character", type="mother", label="Grandma"))
    tool = world.add(Entity(
        id="tool",
        type=vocation.tool,
        label=vocation.tool,
        phrase=vocation.tool,
        owner=child.id,
        role="tool",
    ))
    ingredient = world.add(Entity(
        id="ingredient",
        type="thing",
        label="lard",
        phrase="a little bowl of lard",
        caretaker=mentor.id,
        role="ingredient",
    ))

    child.memes["hope"] = 1
    child.memes["worry"] = 1
    child.memes["curiosity"] = 1

    world.say(f"{child.id} was a little {params.trait} child who dreamed {vocation.dream}.")
    world.say(
        f"Each evening, {child.pronoun('subject')} watched {mentor.label} work by the "
        f"lamplight, and the kitchen felt like a tiny school for that vocation."
    )
    world.say(
        f"On the counter sat {ingredient.phrase}, and beside it lay a {tool.label} waiting "
        f"for a careful hand."
    )

    world.para()
    world.say(
        f"That night, {child.id} wanted to try {vocation.label} work, but {problem.outer_issue}."
    )
    world.say(
        f"In {child.pronoun('possessive')} own quiet inner monologue, {child.id} thought, "
        f"'{problem.inner_worry}. What is the best option?"
    )
    child.memes["worry"] += 1

    world.say(
        f"{mentor.label} smiled and pointed to the bowl. 'Sometimes a small problem needs "
        f"a small, steady option,' {mentor.pronoun('subject')} said."
    )
    world.say(
        f"{child.id} looked at the choices, took a slow breath, and chose to {option.action}."
    )

    world.para()
    if option.id in {"lard", "butter"} and problem.id in option.solves:
        child.meters["mixing"] = 1
        child.memes["confidence"] = 1
        child.memes["worry"] = 0
        world.say(
            f"The spoon moved in circles. Soon {problem.transformation}, and "
            f"{option.transforms}."
        )
        world.say(
            f"The dough changed from stubborn to soft, as if it had learned to listen."
        )
        world.say(
            f"{child.id} felt {params.trait} and proud. Maybe this really was the beginning "
            f"of {vocation.dream}."
        )
        world.say(
            f"Together, they baked until the room smelled sweet and sleepy, and the result "
            f"was {vocation.calm_result}."
        )
    else:
        world.say(
            f"The choice did not solve the trouble, so {mentor.label} helped {child.id} try "
            f"a calmer step instead."
        )
        world.say(
            f"At last, the counter became neat, and the work could begin again."
        )

    world.facts.update(
        child=child,
        mentor=mentor,
        vocation=vocation,
        problem=problem,
        option=option,
        ingredient=ingredient,
        tool=tool,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    vocation = _safe_fact(world, f, "vocation")
    problem = _safe_fact(world, f, "problem")
    option = _safe_fact(world, f, "option")
    return [
        f"Write a bedtime story about {child.id} learning a vocation and choosing the right option.",
        f"Tell a gentle story where {child.id} uses {option.label} to solve {problem.label} and grow into {vocation.label} work.",
        f"Write a cozy kitchen story with inner monologue, problem solving, and transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    vocation = _safe_fact(world, f, "vocation")
    problem = _safe_fact(world, f, "problem")
    option = _safe_fact(world, f, "option")
    mentor = _safe_fact(world, f, "mentor")
    return [
        QAItem(
            question=f"What vocation did {child.id} dream about?",
            answer=f"{child.id} dreamed of becoming a {vocation.label}.",
        ),
        QAItem(
            question=f"What problem was making the work hard?",
            answer=f"The problem was {problem.outer_issue}, which made the kitchen task tricky.",
        ),
        QAItem(
            question=f"What option did {child.id} choose?",
            answer=f"{child.id} chose {option.label}, and that helped solve the trouble.",
        ),
        QAItem(
            question=f"Who guided {child.id} in the kitchen?",
            answer=f"{mentor.label} guided {child.id} with a calm voice and a patient smile.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt proud and more confident after the problem was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lard used for in cooking?",
            answer="Lard is a cooking fat that can help make pastry or dough rich and tender.",
        ),
        QAItem(
            question="What does the word option mean?",
            answer="An option is one choice you can pick from several possibilities.",
        ),
        QAItem(
            question="What is a vocation?",
            answer="A vocation is a kind of work or calling that someone feels meant to do.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a character does inside their own mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_name(S).
vocation(V) :- vocation_name(V).
problem(P) :- problem_name(P).
option(O) :- option_name(O).

solves(O,P) :- option_solve(O,P).
valid(S,P,O) :- setting(S), problem(P), option(O), solves(O,P), bake_place(S,O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_name", sid))
        if "bake" in s.affords:
            lines.append(asp.fact("bake_place", sid, "lard"))
            lines.append(asp.fact("bake_place", sid, "butter"))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for vid in VOCATIONS:
        lines.append(asp.fact("vocation_name", vid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_name", pid))
    for oid, opt in OPTIONS.items():
        lines.append(asp.fact("option_name", oid))
        for p in sorted(opt.solves):
            lines.append(asp.fact("option_solve", oid, p))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = {c for c in valid_combos()}
    cl = {tuple(x) for x in asp_valid_combos()}
    if py == cl:
        print(f"OK: clingo matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch between Python and clingo:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: lard, option, vocation, transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--vocation", choices=VOCATIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--option", choices=OPTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "option", None) is None or c[2] == getattr(args, "option", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, option = rng.choice(filtered)
    vocation = getattr(args, "vocation", None) or rng.choice(sorted(VOCATIONS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, vocation=vocation, problem=problem, option=option,
                       name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    lines.append(f"setting: {world.setting.place}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}): {' '.join(bits) if bits else 'quiet'}")
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
    StoryParams(setting="kitchen", vocation="baker", problem="too_hard", option="lard",
                name="Mina", gender="girl", trait="curious"),
    StoryParams(setting="bakery", vocation="baker", problem="too_plain", option="lard",
                name="Theo", gender="boy", trait="thoughtful"),
    StoryParams(setting="pantry", vocation="helper", problem="too_messy", option="tidy",
                name="Nora", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        for t in triples:
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
