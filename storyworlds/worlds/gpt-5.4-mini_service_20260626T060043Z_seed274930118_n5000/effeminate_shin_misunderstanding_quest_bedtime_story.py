#!/usr/bin/env python3
"""
A tiny story world for a bedtime-style misunderstanding quest.

Seed tale used to shape the world:
---
At bedtime, a child named Pip wore a soft silver costume and loved to twirl
in front of the mirror. One evening, Pip showed a bright ribbon on a shin and
called it a "quest mark." A grown-up heard the words and misunderstood, thinking
Pip had been hurt. After a gentle talk, they found the ribbon was only part of a
playful quest to collect moonlight stickers before sleep.

World model:
- The child has physical state in meters: ribbon tied on a shin, pajamas clean or
  wrinkled, lantern lit or dim.
- Emotional state in memes: excitement, worry, embarrassment, comfort, wonder.
- A misunderstanding arises when the grown-up reads the shin ribbon as an injury.
- The quest resolves when the child explains the costume game and the grown-up
  helps with a cozy, bedtime-safe version of the quest.
"""

from __future__ import annotations

import argparse
import dataclasses
from dataclasses import dataclass, field
import json
import os
import random
import sys
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    place: str = "the bedroom"
    bedtime: bool = True
    SETTING: object | None = None
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
class Quest:
    id: str
    object_name: str
    object_phrase: str
    goal: str
    clue: str
    keyword: str = "quest"
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
class Misunderstanding:
    id: str
    trigger: str
    mistaken_reading: str
    gentle_fix: str
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
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    quest: str
    misunderstanding: str
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
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


QUESTS = {
    "moonlight": Quest(
        id="moonlight",
        object_name="moonlight stickers",
        object_phrase="shiny moonlight stickers",
        goal="collect moonlight stickers from a paper star map",
        clue="a silver ribbon tied near the shin",
        keyword="quest",
    ),
    "button": Quest(
        id="button",
        object_name="button stars",
        object_phrase="tiny button stars",
        goal="find button stars tucked into a quilt pocket",
        clue="a soft sash wrapped around the shin",
        keyword="quest",
    ),
}

MISUNDERSTANDINGS = {
    "injury": Misunderstanding(
        id="injury",
        trigger="shin ribbon",
        mistaken_reading="a hurt shin",
        gentle_fix="Pip explained that the ribbon was only part of a costume for the quest",
    ),
    "trouble": Misunderstanding(
        id="trouble",
        trigger="quiet costume",
        mistaken_reading="something was wrong before sleep",
        gentle_fix="the grown-up learned it was only a bedtime game with gentle rules",
    ),
}


SETTING = Setting(place="the bedroom", bedtime=True)
CHILDREN = ["Pip", "Milo", "Nia", "Luna", "Toby", "Ruby", "Ezra", "Ada"]
TRAITS = ["gentle", "dreamy", "spirited", "curious", "playful", "soft-spoken"]
PARENTS = ["mother", "father"]


def _r_misunderstanding(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    quest = _safe_fact(world, world.facts, "quest")
    mis = _safe_fact(world, world.facts, "misunderstanding")

    if "seen" in world.fired:
        return []
    world.fired.add("seen")

    child.memes["excitement"] = child.memes.get("excitement", 0) + 1
    parent.memes["worry"] = parent.memes.get("worry", 0) + 1
    child.memes["embarrassment"] = child.memes.get("embarrassment", 0) + 1

    world.say(
        f"At bedtime in {world.setting.place}, {child.id} was still wearing "
        f"{quest.object_phrase} and smiling at the mirror."
    )
    world.say(
        f"{parent.pronoun().capitalize()} noticed the {mis.trigger} and thought it meant "
        f"{mis.mistaken_reading}."
    )
    return []


def _r_turn(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    quest = _safe_fact(world, world.facts, "quest")

    if "turn" in world.fired:
        return []
    world.fired.add("turn")

    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    parent.memes["worry"] = max(0, parent.memes.get("worry", 0) - 1)
    parent.memes["comfort"] = parent.memes.get("comfort", 0) + 1

    world.say(
        f"Then {child.id} held up the little map and said the ribbon was for a quiet {quest.keyword}, "
        f"not for a hurt shin."
    )
    world.say(
        f"{child.id} explained the bedtime plan: {quest.goal}, one sticker at a time, "
        f"with no running at all."
    )
    return []


def _r_resolution(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    quest = _safe_fact(world, world.facts, "quest")
    mis = _safe_fact(world, world.facts, "misunderstanding")

    if "resolve" in world.fired:
        return []
    world.fired.add("resolve")

    child.memes["comfort"] = child.memes.get("comfort", 0) + 1
    parent.memes["comfort"] = parent.memes.get("comfort", 0) + 1
    parent.memes["worry"] = 0

    world.say(
        f"{parent.pronoun().capitalize()} smiled and understood. "
        f"{mis.gentle_fix}, and {parent.pronoun()} helped choose a calmer way to finish."
    )
    world.say(
        f"Together they found the last moonlight sticker, tucked the map beside the pillow, "
        f"and {child.id} drifted to sleep with the shin ribbon still tied like a tiny promise."
    )
    return []


def propagate(world: World) -> None:
    _r_misunderstanding(world)
    _r_turn(world)
    _r_resolution(world)


def valid_combo(quest_id: str, misunderstanding_id: str) -> bool:
    return quest_id in QUESTS and misunderstanding_id in MISUNDERSTANDINGS


def curated_valid_combos() -> list[tuple[str, str]]:
    return [(q, m) for q in QUESTS for m in MISUNDERSTANDINGS if valid_combo(q, m)]


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(CHILDREN)


def select_parent(rng: random.Random) -> str:
    return rng.choice(PARENTS)


def select_trait(rng: random.Random) -> str:
    return rng.choice(TRAITS)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
        meters={"shin_ribbon": 1.0, "sleepy": 0.0},
        memes={"excitement": 1.0, "worry": 0.0, "embarrassment": 0.0, "comfort": 0.0, "wonder": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"lamp": 1.0},
        memes={"worry": 0.0, "comfort": 0.0},
    ))

    quest = _safe_lookup(QUESTS, params.quest)
    misunderstanding = _safe_lookup(MISUNDERSTANDINGS, params.misunderstanding)
    world.facts["quest"] = quest
    world.facts["misunderstanding"] = misunderstanding
    world.facts["child"] = child
    world.facts["parent"] = parent

    world.say(
        f"At the end of a soft day, {child.id} loved a small effeminate twirl in {world.setting.place}, "
        f"where the lamp glowed warm and kind."
    )
    world.say(
        f"{child.id} was on a {quest.keyword} to {quest.goal}, and the clue was "
        f"{quest.clue}."
    )
    world.para()
    propagate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    quest = _safe_fact(world, world.facts, "quest")
    child = _safe_fact(world, world.facts, "child")
    parent = _safe_fact(world, world.facts, "parent")
    return [
        f"Write a bedtime story about {child.id}, a small quest, and a gentle misunderstanding.",
        f"Tell a cozy tale where {child.id} and {parent.label} misread a shin ribbon, then find a kind explanation.",
        f"Write a child-friendly story about a {quest.keyword} ending with sleep, comfort, and a happy understanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    quest = _safe_fact(world, world.facts, "quest")
    child = _safe_fact(world, world.facts, "child")
    parent = _safe_fact(world, world.facts, "parent")
    mis = _safe_fact(world, world.facts, "misunderstanding")
    return [
        QAItem(
            question=f"What was {child.id} trying to do at bedtime?",
            answer=f"{child.id} was trying to finish a quiet {quest.keyword} by collecting {quest.object_name}.",
        ),
        QAItem(
            question=f"Why did {parent.label} misunderstand the shin ribbon?",
            answer=f"{parent.label} thought the ribbon meant {mis.mistaken_reading}, but it was really part of the costume for the quest.",
        ),
        QAItem(
            question=f"How did the misunderstanding get fixed?",
            answer=f"{mis.gentle_fix}, and then {parent.label} helped {child.id} finish the bedtime quest kindly.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"{child.id} fell asleep with the map beside the pillow and the shin ribbon still tied softly in place.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks they know what is going on, but they have read the situation the wrong way.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small mission or goal someone tries to complete, often by following clues one step at a time.",
        ),
        QAItem(
            question="What is a shin?",
            answer="A shin is the front part of your leg, between your knee and your ankle.",
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} traits={e.traits}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
quest_available(Q) :- quest(Q).
misunderstanding_available(M) :- misunderstanding(M).
valid_story(Q,M) :- quest_available(Q), misunderstanding_available(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
    for m in MISUNDERSTANDINGS.values():
        lines.append(asp.fact("misunderstanding", m.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(curated_valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP and Python agree on {len(py)} combos.")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a misunderstanding and a quest.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
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
    q = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    m = getattr(args, "misunderstanding", None) or rng.choice(list(MISUNDERSTANDINGS))
    if not valid_combo(q, m):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    return StoryParams(
        name=getattr(args, "name", None) or select_name(gender, rng),
        gender=gender,
        parent=getattr(args, "parent", None) or select_parent(rng),
        trait=getattr(args, "trait", None) or select_trait(rng),
        quest=q,
        misunderstanding=m,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} ASP story combos")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for q, m in curated_valid_combos():
            p = StoryParams(
                name="Pip",
                gender="girl",
                parent="mother",
                trait="gentle",
                quest=q,
                misunderstanding=m,
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
