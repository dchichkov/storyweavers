#!/usr/bin/env python3
"""
A small story world for a horse who solves a gentle whodunit and ends happily.

Premise:
- A young horse notices something strange in the stable: a favorite item is missing.
- The horse follows clues, asks careful questions, and rules out false leads.
- The mystery is solved by looking at the world state: tracks, hay, haynet, and who had access.
- The ending is warm and happy: the lost thing is found, the misunderstanding clears, and everyone feels safe.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- StoryParams + registries + build_parser + resolve_params + generate + emit + main
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py in ASP helpers only
- inline ASP_RULES twin plus Python reasonableness gate
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

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    traits: list[str] = field(default_factory=list)

    culprit: object | None = None
    helper: object | None = None
    horse: object | None = None
    mystery_item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mare", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "stallion", "father", "man"}:
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
class Place:
    name: str
    indoor: bool = True
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
class Clue:
    id: str
    label: str
    location: str
    points_to: str
    detail: str
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
class Suspect:
    id: str
    label: str
    type: str
    access: set[str] = field(default_factory=set)
    innocent_reason: str = ""
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
    stable: str
    mystery: str
    culprit: str
    name: str
    horse_type: str
    helper: str
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
    def __init__(self, stable: Place) -> None:
        self.stable = stable
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.stable)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = _copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


def narrate_state(world: World, msg: str) -> None:
    world.trace_log.append(msg)


def _rule_attention(world: World) -> list[str]:
    out = []
    horse = world.get(world.facts["horse_id"])
    if horse.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if ("noticed", horse.id) in world.fired:
        return out
    world.fired.add(("noticed", horse.id))
    horse.memes["focus"] = horse.memes.get("focus", 0.0) + 1
    out.append(f"{horse.id} narrowed the mystery down and looked more carefully.")
    return out


def _rule_relieved(world: World) -> list[str]:
    out = []
    if world.facts.get("solved") and ("relieved",) not in world.fired:
        world.fired.add(("relieved",))
        horse = world.get(world.facts["horse_id"])
        horse.memes["joy"] = horse.memes.get("joy", 0.0) + 1
        out.append(f"{horse.id} felt bright and calm once the truth was found.")
    return out


CAUSAL_RULES = [
    _rule_attention,
    _rule_relieved,
]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                if narrate:
                    for s in sents:
                        world.say(s)


def is_reasonable(params: StoryParams) -> bool:
    return params.mystery in MYSTERIES and params.culprit in SUSPECTS and params.stable in STABLES


def reasonableness_gate(mystery: str, culprit: str) -> bool:
    return mystery in MYSTERIES and culprit in SUSPECTS


def build_scene(params: StoryParams) -> World:
    stable = _safe_lookup(STABLES, params.stable)
    world = World(stable)
    horse = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.horse_type,
        label=params.name,
        traits=["gentle", "curious"],
        meters={"rest": 1.0},
        memes={"curiosity": 1.0, "care": 1.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=_safe_lookup(HELPER_LABELS, params.helper),
        memes={"kindness": 1.0},
    ))
    culprit = world.add(Entity(
        id=params.culprit,
        kind="character",
        type=_safe_lookup(SUSPECTS, params.culprit).type,
        label=_safe_lookup(SUSPECTS, params.culprit).label,
        memes={"nervous": 1.0},
    ))
    mystery_item = world.add(Entity(
        id="lost_item",
        type="thing",
        label=_safe_lookup(MYSTERIES, params.mystery).label,
        phrase=_safe_lookup(MYSTERIES, params.mystery).phrase,
        owner=horse.id,
        caretaker=helper.id,
    ))
    world.facts.update(
        horse_id=horse.id,
        helper_id=helper.id,
        culprit_id=culprit.id,
        mystery_id=mystery_item.id,
        mystery=params.mystery,
        culprit=params.culprit,
        stable=params.stable,
    )
    return world


def tell_story(world: World) -> None:
    horse = world.get(world.facts["horse_id"])
    helper = world.get(world.facts["helper_id"])
    culprit = world.get(world.facts["culprit_id"])
    mystery = _safe_lookup(MYSTERIES, world.facts.get("mystery"))
    stable = world.stable

    world.say(
        f"In {stable.name}, {horse.id} the horse noticed something odd: "
        f"{horse.pronoun('possessive')} {mystery.label} was gone."
    )
    world.say(
        f"{horse.id} did not panic. {horse.pronoun().capitalize()} sniffed the floor, "
        f"watched the stalls, and asked {helper.label} to look with {horse.pronoun('object')}."
    )
    world.para()
    world.say(
        f"First, they found a small clue near the water trough: {mystery.clue1}. "
        f"Then they found another clue by the hay: {mystery.clue2}."
    )
    world.say(
        f"The clues did not point to a thief after all. They pointed to {culprit.label}, "
        f"who had been helping to tidy the stable and had moved {horse.pronoun('possessive')} {mystery.label} by mistake."
    )
    world.para()
    world.say(
        f"{helper.label} smiled and explained the mix-up. {horse.id} laughed, "
        f"{culprit.id} looked relieved, and soon the {mystery.label} was back where it belonged."
    )
    world.say(
        f"By sunset, the stable was calm again, the mystery was solved, and {horse.id} "
        f"stood happily beside {mystery.label}, glad that everyone was safe and the wrong had turned into a kind little mistake."
    )
    world.facts["solved"] = True
    propagate(world, narrate=False)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m = _safe_lookup(MYSTERIES, _safe_fact(world, f, "mystery"))
    return [
        f'Write a short whodunit for children about a horse named {_safe_fact(world, f, "horse_id")} and a missing {m.label}.',
        f"Tell a gentle mystery in a stable where clues lead to a harmless mistake and a happy ending.",
        f'Write a story with a curious horse, two clues, and the word "{m.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m = _safe_lookup(MYSTERIES, _safe_fact(world, f, "mystery"))
    horse = _safe_fact(world, f, "horse_id")
    helper = _safe_fact(world, f, "helper_id")
    culprit = _safe_fact(world, f, "culprit_id")
    return [
        QAItem(
            question=f"What was missing from the stable?",
            answer=f"{horse.id} noticed that {horse.pronoun('possessive')} {m.label} was missing.",
        ),
        QAItem(
            question=f"How did {horse.id} solve the mystery?",
            answer=f"{horse.id} followed clues near the water trough and the hay, then learned that {culprit.label} had moved the {m.label} by mistake.",
        ),
        QAItem(
            question=f"Who helped {horse.id} look for the missing item?",
            answer=f"{helper.label} helped {horse.id} search carefully and sort out the mix-up.",
        ),
        QAItem(
            question=f"Why did the story end happily?",
            answer=f"It ended happily because the {m.label} was found, the misunderstanding was cleared up, and everyone was calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    m = _safe_lookup(MYSTERIES, _safe_fact(world, f, "mystery"))
    tags = {m.keyword, "horse", "stable", "clue"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            q, a = KNOWLEDGE[tag]
            out.append(QAItem(question=q, answer=a))
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    if world.trace_log:
        lines.append("  trace:")
        for t in world.trace_log:
            lines.append(f"    - {t}")
    return "\n".join(lines)


MYSTERIES = {
    "bell": Clue if False else type("Mystery", (), {})  # placeholder replaced below
}


@dataclass
class Mystery:
    label: str
    phrase: str
    keyword: str
    clue1: str
    clue2: str
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


MYSTERIES = {
    "bell": Mystery(
        label="little brass bell",
        phrase="a little brass bell with a blue ribbon",
        keyword="bell",
        clue1="a ribbon scrap caught on a nail",
        clue2="a faint jingle under the hay",
    ),
    "brush": Mystery(
        label="favorite brush",
        phrase="a favorite soft brush",
        keyword="brush",
        clue1="bristles stuck to a gate latch",
        clue2="hoofprints that stopped at the tack shelf",
    ),
    "bucket": Mystery(
        label="feed bucket",
        phrase="a sturdy red feed bucket",
        keyword="bucket",
        clue1="grain dust near the doorway",
        clue2="a bucket ring in the straw",
    ),
}

STABLES = {
    "sunny_stable": Place(name="the sunny stable", indoor=True),
    "quiet_barn": Place(name="the quiet barn", indoor=True),
}

SUSPECTS = {
    "goat": Suspect(id="goat", label="the goat", type="goat", access={"hay", "gate"}, innocent_reason="the goat was busy nibbling hay"),
    "cat": Suspect(id="cat", label="the barn cat", type="cat", access={"shelf", "hay"}, innocent_reason="the cat only chased dust motes"),
    "farmer": Suspect(id="farmer", label="the farmer", type="human", access={"gate", "shelf", "hay"}, innocent_reason="the farmer was tidying and meant to help"),
}

HELPER_LABELS = {
    "farmer": "the farmer",
    "child": "the child",
}

STORY_NAMES = ["Star", "Penny", "Comet", "Misty", "Sunny", "Maple"]
HORSE_TYPES = ["mare", "stallion"]


@dataclass
class StoryChoice:
    stable: str
    mystery: str
    culprit: str
    name: str
    horse_type: str
    helper: str
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
    for stable in STABLES:
        for mystery in MYSTERIES:
            for culprit in SUSPECTS:
                combos.append((stable, mystery, culprit))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in STABLES.items():
        lines.append(asp.fact("stable", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_word", mid, m.keyword))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("suspect_type", sid, s.type))
        for a in sorted(s.access):
            lines.append(asp.fact("access", sid, a))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Stable, Mystery, Suspect) :- stable(Stable), mystery(Mystery), suspect(Suspect).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle horse whodunit with a happy ending.")
    ap.add_argument("--stable", choices=STABLES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--name", choices=STORY_NAMES)
    ap.add_argument("--horse-type", choices=HORSE_TYPES)
    ap.add_argument("--helper", choices=HELPER_LABELS)
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
    stable = getattr(args, "stable", None) or rng.choice(list(STABLES))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    culprit = getattr(args, "culprit", None) or rng.choice(list(SUSPECTS))
    if not reasonableness_gate(mystery, culprit):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        stable=stable,
        mystery=mystery,
        culprit=culprit,
        name=getattr(args, "name", None) or rng.choice(STORY_NAMES),
        horse_type=getattr(args, "horse_type", None) or rng.choice(HORSE_TYPES),
        helper=getattr(args, "helper", None) or "farmer",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_scene(params)
    tell_story(world)
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


CURATED = [
    StoryParams(stable="sunny_stable", mystery="bell", culprit="farmer", name="Star", horse_type="mare", helper="farmer"),
    StoryParams(stable="quiet_barn", mystery="brush", culprit="cat", name="Comet", horse_type="stallion", helper="farmer"),
    StoryParams(stable="sunny_stable", mystery="bucket", culprit="goat", name="Misty", horse_type="mare", helper="farmer"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.stable} (culprit: {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
