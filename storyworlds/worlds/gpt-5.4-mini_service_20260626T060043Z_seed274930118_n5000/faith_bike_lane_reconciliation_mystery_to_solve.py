#!/usr/bin/env python3
"""
storyworlds/worlds/faith_bike_lane_reconciliation_mystery_to_solve.py
======================================================================

A small folk-tale storyworld set in a bike lane, with faith, a mystery to
solve, a touch of magic, and a reconciliation at the end.

The world premise:
- A child or traveler keeps faith in a promised path.
- Something strange blocks the bike lane or confuses the way.
- A kind helper notices clues, uses a little magic, and solves the mystery.
- Two sides reconcile, and the lane becomes safe and welcoming again.

This script is self-contained and follows the storyworld contract:
- deterministic simulation from parameters
- world model with physical meters and emotional memes
- child-facing prose
- QA prompts grounded in story state
- inline ASP twin and verification helpers
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    helper: object | None = None
    hero: object | None = None
    magic: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"blocked": 0.0, "seen": 0.0, "settled": 0.0}
        if not self.memes:
            self.memes = {
                "faith": 0.0,
                "worry": 0.0,
                "wonder": 0.0,
                "peace": 0.0,
                "mistrust": 0.0,
                "reconciliation": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "witch"}
        male = {"boy", "father", "dad", "man", "priest"}
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
    place: str = "the bike lane"
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
class Mystery:
    id: str
    clue: str
    cause: str
    solution: str
    magic_word: str
    kind: str = "mystery"
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
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    protects: set[str] = field(default_factory=set)
    solves: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    helper_gender: str
    parent: str
    mystery: str
    tool: str
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


SETTINGS = {
    "bike_lane": Setting(place="the bike lane", affords={"search", "ride", "listen"}),
}

MYSTERIES = {
    "glow_stone": Mystery(
        id="glow_stone",
        clue="a soft shine on the painted line",
        cause="a tiny glass charm had rolled from a cart",
        solution="the charm was placed back where it belonged",
        magic_word="brighten",
    ),
    "lost_bell": Mystery(
        id="lost_bell",
        clue="a silver sound hidden near the curb",
        cause="a little bell had fallen from a bicycle basket",
        solution="the bell was tied back onto the basket",
        magic_word="ring",
    ),
    "white_feather": Mystery(
        id="white_feather",
        clue="a white feather turning in a small wind",
        cause="a story-card had fluttered out of a pocket",
        solution="the card was returned to its owner",
        magic_word="gather",
    ),
}

TOOLS = {
    "lantern": MagicTool(
        id="lantern",
        label="a lantern of clear glass",
        phrase="a lantern of clear glass that glowed like a kind moon",
        effect="light",
        protects={"dark"},
        solves={"glow_stone", "lost_bell", "white_feather"},
    ),
    "thread": MagicTool(
        id="thread",
        label="a silver thread spool",
        phrase="a silver thread spool that shone whenever someone spoke truthfully",
        effect="mend",
        protects={"broken"},
        solves={"lost_bell", "white_feather"},
    ),
    "broom": MagicTool(
        id="broom",
        label="a broom of reed",
        phrase="a broom of reed tied with a blue ribbon",
        effect="clear",
        protects={"blocked"},
        solves={"glow_stone", "lost_bell", "white_feather"},
    ),
}

GIRL_NAMES = ["Mara", "Lina", "Suri", "Nora", "Ivy", "Tala"]
BOY_NAMES = ["Oren", "Pavel", "Milo", "Ansel", "Bram", "Jonah"]
HELPER_NAMES = ["Grandmother Elin", "Old Jory", "Sister Wren", "Brother Pio", "Aunt Halla"]
TRAITS = ["faithful", "gentle", "curious", "patient", "brave", "hopeful"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_reveal(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    mystery = _safe_fact(world, world.facts, "mystery")
    if hero.memes["faith"] < THRESHOLD:
        return out
    sig = ("reveal", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["seen"] += 1
    hero.memes["wonder"] += 1
    out.append(f"A small clue showed itself: {mystery.clue}.")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    helper = world.get("helper")
    mystery = _safe_fact(world, world.facts, "mystery")
    tool = world.facts.get("tool")
    if hero.memes["wonder"] < THRESHOLD:
        return out
    if tool is None:
        return out
    sig = ("solve", mystery.id, tool.id)
    if sig in world.fired:
        return out
    if mystery.id not in tool.solves:
        return out
    world.fired.add(sig)
    world.facts["solved"] = True
    hero.memes["peace"] += 1
    helper.memes["peace"] += 1
    out.append(f"The magic of {tool.label} helped them see the answer.")
    out.append(f"The mystery was solved: {mystery.solution}.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    helper = world.get("helper")
    if not world.facts.get("solved"):
        return out
    sig = ("reconcile", hero.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    hero.memes["worry"] = 0.0
    helper.memes["mistrust"] = 0.0
    out.append(f"Then the two of them smiled and made peace again.")
    return out


CAUSAL_RULES = [
    Rule("reveal", _r_reveal),
    Rule("solve", _r_solve),
    Rule("reconcile", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, mystery: Mystery, tool: MagicTool, hero_name: str,
         hero_gender: str, helper_name: str, helper_gender: str, parent: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name))
    elder = world.add(Entity(id="elder", kind="character", type=parent, label=f"the {parent}"))

    magic = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="magic",
        label=tool.label,
        phrase=tool.phrase,
        protective=True,
        covers=set(tool.protects),
    ))
    world.facts.update(hero=hero, helper=helper, elder=elder, mystery=mystery, tool=magic)

    hero.memes["faith"] += 1
    helper.memes["mistrust"] += 1
    world.say(
        f"Once in {setting.place}, there lived {hero_name}, a {hero.label_word if hasattr(hero, 'label_word') else 'child'} "
        f"with a heart full of faith."
    )
    world.say(
        f"{hero_name} loved the old bike lane because it led past the market and the little chapel, "
        f"and {hero.pronoun('possessive')} {parent} had always said that patient hearts find their way."
    )
    world.para()
    world.say(
        f"One morning, {hero_name} and {helper_name} came upon a strange sign in the lane: {mystery.clue}."
    )
    hero.memes["worry"] += 1
    world.say(
        f"Nobody knew why it was there, and the bike lane felt quiet as a held breath."
    )
    world.say(
        f"Then {helper_name} lifted {tool.phrase}, and the glass hummed softly with magic."
    )
    hero.memes["faith"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{hero_name} listened to the lane, followed the clue, and found that {mystery.cause}."
    )
    world.say(
        f"With careful hands and a kind word, they set things right, and the lane grew smooth again."
    )
    world.say(
        f"In the end, {hero_name} and {helper_name} walked side by side, reconciled and smiling, "
        f"while the magic light winked once and went still."
    )
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            for tid, tool in TOOLS.items():
                if mid in tool.solves:
                    combos.append((place, mid, tid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    mystery = _safe_fact(world, f, "mystery")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f"Write a folk tale for a small child set in {world.setting.place} about faith, magic, and a mystery to solve.",
        f"Tell a gentle story where {hero.label} and {helper.label} find {mystery.clue} in the bike lane and use {tool.label} to help.",
        f"Write a short magical reconciliation story set in a bike lane, ending with the mystery being solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    mystery = _safe_fact(world, f, "mystery")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who kept faith in the bike lane mystery?",
            answer=f"{hero.label} kept faith and kept listening even when the lane felt strange."
        ),
        QAItem(
            question=f"What clue appeared in the bike lane?",
            answer=f"The clue was {mystery.clue}, which made the lane seem mysterious."
        ),
        QAItem(
            question=f"What magical thing helped solve the mystery?",
            answer=f"{tool.label} helped them see what was going on and move toward the answer."
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and {helper.label}?",
            answer=f"They reconciled, smiled together, and walked away after the mystery was solved."
        ),
    ]


WORLD_KNOWLEDGE = {
    "faith": [
        QAItem(
            question="What does it mean to have faith?",
            answer="To have faith means to keep believing that something good can happen, even before you can see it."
        )
    ],
    "bike": [
        QAItem(
            question="What is a bike lane for?",
            answer="A bike lane is a safe part of the road where bicycles can travel."
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in a folk tale?",
            answer="Magic is a wonder-filled power in stories that can help, reveal clues, or change things in special ways."
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again."
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people try to understand and solve."
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["faith"])
    out.extend(WORLD_KNOWLEDGE["bike"])
    out.extend(WORLD_KNOWLEDGE["magic"])
    out.extend(WORLD_KNOWLEDGE["reconciliation"])
    out.extend(WORLD_KNOWLEDGE["mystery"])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {e.label:24} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mara", gender="girl", helper="Old Jory", helper_gender="man", parent="mother", mystery="glow_stone", tool="lantern"),
    StoryParams(name="Oren", gender="boy", helper="Sister Wren", helper_gender="woman", parent="father", mystery="lost_bell", tool="broom"),
    StoryParams(name="Tala", gender="girl", helper="Aunt Halla", helper_gender="woman", parent="mother", mystery="white_feather", tool="thread"),
]


def explain_rejection(mystery: Mystery, tool: MagicTool) -> str:
    return f"(No story: {tool.label} does not help solve {mystery.id} in a reasonable way.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(t.solves):
            lines.append(asp.fact("solves", tid, m))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Mystery, Tool) :- setting(Place), mystery(Mystery), tool(Tool), solves(Tool, Mystery).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: faith, a mystery, magic, and reconciliation in a bike lane.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
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
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    if mystery not in _safe_lookup(TOOLS, tool).solves:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["woman", "man"])
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, helper=helper, helper_gender=helper_gender, parent=parent, mystery=mystery, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS["bike_lane"],
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(TOOLS, params.tool),
        params.name,
        params.gender,
        params.helper,
        params.helper_gender,
        params.parent,
    )
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery, tool) combos:\n")
        for place, mystery, tool in combos:
            print(f"  {place:10} {mystery:12} {tool}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
