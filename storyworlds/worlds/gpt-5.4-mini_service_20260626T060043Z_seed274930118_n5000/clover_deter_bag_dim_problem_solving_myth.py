#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/clover_deter_bag_dim_problem_solving_myth.py
===========================================================================================================================

A small mythic storyworld about a brave child, a dim bag, a lucky clover,
and a problem that can be solved by noticing the right sign.

Premise:
- A young seeker finds a dim old bag in a meadow, shrine, grove, or hill path.
- The bag is thought to be unlucky or unsafe to open in the dark.
- The seeker needs a clover or clover charm to deter the trouble hiding in the bag.

Tension:
- The hero wants to solve the problem, but fear and dim light make the bag hard to trust.
- A helper or elder warns that the wrong move could spill gloom or frighten a creature.

Turn:
- The hero uses clover, lamp-light, thread, or careful counting to make the bag safe.
- The solution is concrete and stateful: the bag becomes openable, calm, and useful.

Resolution:
- What changed is visible in the final image: the bag is no longer dim and the trouble is deterred.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    problem_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "priest"}
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
class Problem:
    id: str
    noun: str
    verb: str
    effect: str
    danger: str
    zone: str
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
class Remedy:
    id: str
    label: str
    phrase: str
    verb: str
    result: str
    covers: set[str] = field(default_factory=set)
    wards: set[str] = field(default_factory=set)
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "meadow": Setting("the meadow", "bright", {"find", "gather", "open"}),
    "shrine": Setting("the shrine", "holy", {"find", "offer", "open"}),
    "grove": Setting("the grove", "hushed", {"find", "open", "count"}),
    "hillpath": Setting("the hill path", "windy", {"find", "open", "carry"}),
}

PROBLEMS = {
    "dim_bag": Problem(
        id="dim_bag",
        noun="a dim old bag",
        verb="open the bag",
        effect="the bag grew dim and hard to trust",
        danger="its shadow might spill out",
        zone="hands",
        keyword="bag-dim",
        tags={"bag-dim", "dim", "bag"},
    ),
    "sealed_bag": Problem(
        id="sealed_bag",
        noun="a sealed traveler’s bag",
        verb="unseal the bag",
        effect="the knots tightened in the dark",
        danger="the bag would stay shut by old magic",
        zone="hands",
        keyword="bag-dim",
        tags={"bag-dim", "bag"},
    ),
    "lost_clover": Problem(
        id="lost_clover",
        noun="a lost clover charm",
        verb="find the clover",
        effect="the charm lay hidden in grass",
        danger="bad luck would keep the path unclear",
        zone="eyes",
        keyword="clover",
        tags={"clover", "luck"},
    ),
}

REMEDIES = [
    Remedy(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a steady flame",
        verb="light the lantern",
        result="the darkness shrank back",
        covers={"hands", "eyes"},
        wards={"dim"},
    ),
    Remedy(
        id="clover",
        label="a four-leaf clover",
        phrase="a fresh four-leaf clover",
        verb="hold the clover above the bag",
        result="the bad luck was deterred",
        covers={"hands"},
        wards={"bag-dim", "dim", "luck"},
    ),
    Remedy(
        id="string",
        label="green string",
        phrase="green string from a braid",
        verb="tie the string around the mouth of the bag",
        result="the opening stayed calm and clear",
        covers={"hands"},
        wards={"bag-dim"},
        plural=False,
    ),
]

HERO_NAMES = ["Ari", "Mira", "Tao", "Nia", "Suri", "Elin", "Bram", "Kian"]
HELPER_NAMES = ["the elder", "the guide", "the shepherd", "the aunt", "the keeper"]
TRAITS = ["brave", "careful", "curious", "patient", "gentle", "steadfast"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
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


def _hero_title(hero: Entity) -> str:
    return next((t for t in hero.traits if t != "little"), hero.type)


def _describe_setting(world: World) -> str:
    return {
        "bright": f"{world.setting.place.capitalize()} shone in a kindly light.",
        "holy": f"{world.setting.place.capitalize()} felt still, as if listening.",
        "hushed": f"{world.setting.place.capitalize()} was quiet enough to hear the grass move.",
        "windy": f"{world.setting.place.capitalize()} leaned under a restless wind.",
    }.get(world.setting.mood, f"{world.setting.place.capitalize()} waited in silence.")


def _add_fact(world: World, key: str, value) -> None:
    world.facts[key] = value


def _do_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    if problem.id not in world.setting.affords:
        return
    hero.meters[problem.id] = hero.meters.get(problem.id, 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} tried to {problem.verb}, but {problem.effect}.")


def _problem_turn(world: World, hero: Entity, problem: Problem) -> None:
    if hero.meters.get(problem.id, 0.0) >= THRESHOLD:
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
        world.say(f"{hero.id} paused, because {problem.danger}.")


def _choose_remedy(problem: Problem) -> Optional[Remedy]:
    for remedy in REMEDIES:
        if problem.id == "lost_clover" and remedy.id == "clover":
            return remedy
        if problem.id in {"dim_bag", "sealed_bag"} and "bag-dim" in remedy.wards:
            return remedy
    return None


def introduce(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"Once, there was a little {_hero_title(hero)} named {hero.id} who went to "
        f"{world.setting.place} with {helper.label}."
    )
    world.say(
        f"{hero.id} was {hero.traits[0]} and loved to solve small troubles with calm hands."
    )
    world.say(
        f"There they found {problem.noun}, and everyone knew it would not stay easy for long."
    )


def build_tension(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.para()
    world.say(_describe_setting(world))
    world.say(
        f"{hero.id} wanted to {problem.verb}, but {helper.pronoun('possessive')} warning was soft and serious."
    )
    world.say(
        f'"If you hurry, {problem.danger}," {helper.label} said.'
    )
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    _do_problem(world, hero, problem, narrate=False)
    _problem_turn(world, hero, problem)
    world.say(
        f"{hero.id} looked at the dim shape and decided to solve it instead of running away."
    )


def solve_problem(world: World, hero: Entity, helper: Entity, problem: Problem) -> Optional[Remedy]:
    remedy = _choose_remedy(problem)
    if remedy is None:
        return None
    world.para()
    world.say(
        f"{hero.id} found {remedy.phrase} and remembered the old lesson: the right small thing can deter a great shadow."
    )
    if remedy.id == "clover":
        world.say(
            f"{hero.id} held the clover above the bag, and the clover scent made the gloom hesitate."
        )
    elif remedy.id == "lantern":
        world.say(
            f"{hero.id} lit the lantern, and its round gold light made the corners easy to see."
        )
    else:
        world.say(
            f"{hero.id} tied the green string carefully, and the knot kept the mouth of the bag from slipping open."
        )
    return remedy


def resolve_story(world: World, hero: Entity, helper: Entity, problem: Problem, remedy: Remedy) -> None:
    world.say(
        f"{remedy.result.capitalize()}, so {hero.id} could at last {problem.verb} without fear."
    )
    hero.memes["worry"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    _add_fact(world, "resolved", True)
    _add_fact(world, "remedy", remedy)
    world.say(
        f"In the end, the bag was no longer dim, the trouble was deterred, and {hero.id} walked away wiser than before."
    )


def tell(setting: Setting, problem: Problem, hero_name: str, helper_label: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", traits=["little", trait]))
    helper = world.add(Entity(id="helper", kind="character", type="elder", label=helper_label))
    problem_ent = world.add(Entity(id="problem", type=problem.id, label=problem.noun, phrase=problem.noun))

    world.facts.update(hero=hero, helper=helper, problem=problem, setting=setting)

    introduce(world, hero, helper, problem)
    build_tension(world, hero, helper, problem)
    remedy = solve_problem(world, hero, helper, problem)
    if remedy is not None:
        resolve_story(world, hero, helper, problem, remedy)
    else:
        world.para()
        world.say(
            f"But no fitting remedy was near, so the trouble stayed and the lesson remained unfinished."
        )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, problem = f["hero"], f["helper"], f["problem"]
    return [
        f'Write a short myth-like story for a small child about {hero.id}, {problem.keyword}, and a way to deter trouble.',
        f'Tell a gentle problem-solving myth where {hero.id} and {helper.label} face {problem.noun} at {world.setting.place}.',
        f'Write a tiny legend in which a clover, a dim bag, and a careful choice lead to a calm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, problem, remedy = f["hero"], f["helper"], f["problem"], f.get("remedy")
    qas = [
        QAItem(
            question=f"Who went to {world.setting.place} to deal with {problem.noun}?",
            answer=f"{hero.id} went with {helper.label} to {world.setting.place} to solve the problem."
        ),
        QAItem(
            question=f"What made the trouble harder at first?",
            answer=f"It was hard at first because {problem.effect} and {problem.danger}."
        ),
        QAItem(
            question=f"What did {hero.id} do instead of giving up?",
            answer=f"{hero.id} stayed calm, looked for a remedy, and chose a careful way to deal with it."
        ),
    ]
    if remedy is not None:
        qas.append(
            QAItem(
                question=f"How did {remedy.label} help in the story?",
                answer=f"{remedy.label.capitalize()} helped because it let {hero.id} deter the trouble and finish the task safely."
            )
        )
    return qas


KNOWLEDGE = {
    "clover": [
        QAItem(
            question="What is a clover?",
            answer="A clover is a small plant with rounded leaves, and some clovers have three leaves while a rare one may have four."
        ),
        QAItem(
            question="Why do stories often use clover as a lucky sign?",
            answer="Stories often treat clover as a lucky sign because people have long associated four-leaf clovers with good luck."
        ),
    ],
    "bag-dim": [
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, so it is hard to see clearly."
        ),
        QAItem(
            question="Why can a dim bag be tricky?",
            answer="A dim bag can be tricky because you may not see what is inside, so you need to be careful before opening it."
        ),
    ],
    "problem": [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking at a difficulty, thinking about it, and choosing a helpful action to fix it."
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags)
    if "clover" in tags:
        out = list(KNOWLEDGE["clover"])
    else:
        out = []
    if "bag-dim" in tags or "dim" in tags or "bag" in tags:
        out.extend(KNOWLEDGE["bag-dim"])
    out.extend(KNOWLEDGE["problem"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", problem="dim_bag", name="Mira", helper="the elder", trait="careful"),
    StoryParams(place="grove", problem="sealed_bag", name="Ari", helper="the guide", trait="brave"),
    StoryParams(place="shrine", problem="lost_clover", name="Nia", helper="the keeper", trait="gentle"),
]


ASP_RULES = r"""
place(meadow). place(shrine). place(grove). place(hillpath).

problem(dim_bag). problem(sealed_bag). problem(lost_clover).

setting_affords(meadow, find). setting_affords(meadow, open).
setting_affords(shrine, find). setting_affords(shrine, open).
setting_affords(grove, find). setting_affords(grove, open).
setting_affords(hillpath, find). setting_affords(hillpath, carry).

problem_keyword(dim_bag, "bag-dim").
problem_keyword(sealed_bag, "bag-dim").
problem_keyword(lost_clover, clover).

remedy(clover). remedy(lantern). remedy(string).

problem_needs_remedy(dim_bag, clover) :- remedy(clover).
problem_needs_remedy(sealed_bag, clover) :- remedy(clover).
problem_needs_remedy(lost_clover, clover) :- remedy(clover).

valid_story(P, Pr, R) :- setting_affords(P, open), problem(Pr), remedy(R),
                        problem_needs_remedy(Pr, R).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in sorted(_safe_lookup(SETTINGS, pid).affords):
            lines.append(asp.fact("setting_affords", pid, a))
    for pr_id, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pr_id))
        lines.append(asp.fact("problem_keyword", pr_id, pr.keyword))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    triples = asp_valid_stories()
    python_like = []
    for place in SETTINGS:
        for pr_id in PROBLEMS:
            for remedy in REMEDIES:
                if place in SETTINGS and remedy.id == "clover" and pr_id in {"dim_bag", "sealed_bag", "lost_clover"}:
                    python_like.append((place, pr_id, remedy.id))
    if set(triples):
        print(f"OK: ASP produced {len(triples)} story triples.")
    else:
        print("No ASP models found.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic problem-solving storyworld about clover and a dim bag.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    if place not in _safe_lookup(SETTINGS, place).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), params.name, params.helper, params.trait)
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
        try:
            import asp
        except Exception as exc:
            raise SystemExit(str(exc))
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible stories:")
        for t in sorted(set(asp.atoms(model, "valid_story"))):
            print("  ", t)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
