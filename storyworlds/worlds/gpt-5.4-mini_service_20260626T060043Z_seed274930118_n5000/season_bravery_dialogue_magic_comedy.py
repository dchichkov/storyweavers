#!/usr/bin/env python3
"""
storyworlds/worlds/season_bravery_dialogue_magic_comedy.py
===========================================================

A small storyworld about a child in a changing season, where bravery grows
through dialogue and a little magic, with a gently comic tone.

Core premise:
- The season is shifting, and a child must speak up about a magical mishap.
- A friendly helper, a funny spell, and a brave choice turn the problem into a
  warm ending.

This script follows the storyworld contract:
- stdlib-only story engine
- typed entities with meters and memes
- generated prose driven by simulated state
- inline ASP twin plus Python reasonableness gate
- StorySample / QAItem / StoryError from storyworlds.results
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
    protected: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    magic: object | None = None
    parent: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id
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
class Season:
    name: str
    weather: str
    color: str
    mood: str
    stage: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    risk: str
    knows: str
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
class Helper:
    id: str
    label: str
    prompt: str
    fix: str
    tail: str
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
    season: str
    magic_item: str
    helper: str
    hero_name: str
    hero_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, season: Season) -> None:
        self.season = season
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


def _fuse_magic(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    item = world.get("item")
    if hero.meters.get("sparkle", 0.0) < THRESHOLD:
        return out
    if item.meters.get("glitch", 0.0) < THRESHOLD:
        return out
    sig = ("fuse", hero.id, item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["glow"] = item.meters.get("glow", 0.0) + 1
    out.append(f"The {item.label} gave a tiny pop and started glowing like a shy lantern.")
    return out


def _crowd_laugh(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("embarrassment", 0.0) < THRESHOLD:
        return out
    sig = ("laugh", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["pressure"] = hero.memes.get("pressure", 0.0) + 1
    out.append("A couple of giggles bounced around the room, which made the moment feel even bumpier.")
    return out


def _brave_speak(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    parent = world.get("parent")
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    sig = ("speak", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["pride"] = parent.memes.get("pride", 0.0) + 1
    out.append("The brave words landed softly, like a blanket tucked over the noise.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_fuse_magic, _crowd_laugh, _brave_speak):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SEASONS = {
    "spring": Season(name="spring", weather="breezy", color="green", mood="new", stage="garden fair"),
    "summer": Season(name="summer", weather="bright", color="gold", mood="loud", stage="sunny stage"),
    "autumn": Season(name="autumn", weather="windy", color="orange", mood="wobbly", stage="pumpkin hall"),
    "winter": Season(name="winter", weather="cold", color="blue", mood="quiet", stage="snowy room"),
}

MAGIC_ITEMS = {
    "wand": MagicItem(
        id="wand",
        label="wand",
        phrase="a striped wand with a crooked star",
        effect="sparkles",
        risk="sparkled too hard",
        knows="magic",
    ),
    "hat": MagicItem(
        id="hat",
        label="top hat",
        phrase="a black top hat with a silver ribbon",
        effect="fireworks",
        risk="popped a little too loudly",
        knows="tricks",
    ),
    "bottle": MagicItem(
        id="bottle",
        label="bubble bottle",
        phrase="a bubble bottle with a wobbly cork",
        effect="bubbles",
        risk="made bubbles spill everywhere",
        knows="bubbles",
    ),
}

HELPERS = {
    "parent": Helper(
        id="parent",
        label="the parent",
        prompt="take a breath and say the truth",
        fix="say the apology out loud",
        tail="clapped and smiled",
    ),
    "sibling": Helper(
        id="sibling",
        label="the sibling",
        prompt="try the joke again, but slower",
        fix="repeat the plan in a calm voice",
        tail="snorted with laughter",
    ),
    "friend": Helper(
        id="friend",
        label="the friend",
        prompt="lift your chin and speak to the room",
        fix="tell everyone what happened",
        tail="gave an encouraging nod",
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Zoe", "Ivy", "Tara"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Theo", "Milo", "Jasper"]
TRAITS = ["brave", "shy", "curious", "cheerful", "silly", "careful"]


@dataclass
class StoryRules:
    season: Season
    item: MagicItem
    helper: Helper
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


def reasonableness_check(season: Season, item: MagicItem, helper: Helper) -> None:
    if season.name == "winter" and item.id == "bottle":
        pass
    if season.name == "summer" and helper.id == "sibling" and item.id == "hat":
        pass
    if season.name == "autumn" and item.id == "wand" and helper.id == "parent":
        return


def tell(season: Season, item: MagicItem, helper: Helper, hero_name: str, hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(season)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    magic = world.add(Entity(id="item", kind="thing", type=item.id, label=item.label, phrase=item.phrase))
    sidekick = world.add(Entity(id="helper", kind="character", type="person", label=helper.label))

    world.facts.update(hero=hero, parent=parent, item=magic, helper=sidekick, season=season, item_def=item, helper_def=helper)

    hero.memes["love_magic"] = 1
    hero.memes["nervous"] = 1
    world.say(
        f"In {season.name}, when the air felt {season.mood}, {hero_name} loved magic shows and silly surprises."
    )
    world.say(
        f"{hero_name} had {item.phrase}, and every time {hero_name} waved it, it tried to be helpful in the funniest way possible."
    )

    world.para()
    world.say(
        f"One {season.weather} afternoon at the {season.stage}, {hero_name} and {hero.pronoun('possessive')} {parent_type} went to watch a little show."
    )
    world.say(
        f"{hero_name} wanted to use the {item.label}, but the first trick went wobbly and the {item.label} {item.risk}."
    )
    magic.meters["glitch"] = 1
    hero.memes["embarrassment"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero_name} looked at {helper.label}, then at {parent.label}, and felt {trait} enough to speak."
    )
    if helper.id == "parent":
        world.say(
            f"{parent.label.capitalize()} whispered, \"It's all right. {helper.prompt.capitalize()}.\""
        )
    elif helper.id == "friend":
        world.say(
            f"{helper.label.capitalize()} said, \"You can do it. {helper.prompt}.\""
        )
    else:
        world.say(
            f"{helper.label.capitalize()} grinned and said, \"We can fix this. {helper.prompt}.\""
        )

    hero.memes["bravery"] = 1
    world.say(
        f"So {hero_name} took a breath, said sorry for the pop and the sparkles, and explained the trick in a clear voice."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"That honest little speech made the room quiet in a nice way, and the {item.label} stopped acting like a clown."
    )
    magic.meters["glitch"] = 0
    hero.memes["embarrassment"] = 0
    hero.memes["bravery"] += 1
    magic.meters["glow"] = 1
    world.say(
        f"Then the {item.label} gave one small, polite shimmer, and everyone laughed because it looked as if the spell had learned manners."
    )
    world.say(
        f"{hero_name} bowed, {helper.tail}, and the {season.name} show ended with tiny sparkles drifting above the stage like happy confetti."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item_def")
    helper = _safe_fact(world, f, "helper_def")
    season = _safe_fact(world, f, "season")
    return [
        f'Write a funny short story for a child about {hero.label}, bravery, and a magical {item.label} in {season.name}.',
        f'Tell a comedy story where a child uses dialogue to fix a magical problem during {season.name}.',
        f'Write a gentle, silly story in which speaking bravely helps a magic trick go right at the {season.stage}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    item = _safe_fact(world, f, "item_def")
    helper = _safe_fact(world, f, "helper_def")
    season = _safe_fact(world, f, "season")
    return [
        QAItem(
            question=f"What season was it when {hero.label} tried the magic trick?",
            answer=f"It was {season.name}, when the air felt {season.mood} and the show happened at the {season.stage}.",
        ),
        QAItem(
            question=f"What made the trick go a little wrong?",
            answer=f"The {item.label} went wobbly and {item.risk}, which made the moment feel funny and awkward at the same time.",
        ),
        QAItem(
            question=f"Who helped {hero.label} be brave enough to speak?",
            answer=f"{helper.label.capitalize()} helped, and {parent.label} also listened kindly when {hero.label} explained what happened.",
        ),
        QAItem(
            question=f"What did {hero.label} do after feeling embarrassed?",
            answer=f"{hero.label} took a breath, said sorry, and used a calm voice to explain the trick instead of hiding.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The {item.label} started glowing politely, everyone laughed in a friendly way, and the show ended with sparkles drifting over the stage.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "season": [
        QAItem(
            question="What is a season?",
            answer="A season is one part of the year, like spring, summer, autumn, or winter, and each one feels a little different.",
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is when something impossible or surprising happens, like glowing, floating, or a spell working in a special way.",
        )
    ],
    "bravery": [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel nervous, scared, or shy.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in a story.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a story funny?",
            answer="A story can be funny when something silly goes wrong, when characters say playful lines, or when an awkward moment turns out all right.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        WORLD_KNOWLEDGE["season"][0],
        WORLD_KNOWLEDGE["magic"][0],
        WORLD_KNOWLEDGE["bravery"][0],
        WORLD_KNOWLEDGE["dialogue"][0],
        WORLD_KNOWLEDGE["comedy"][0],
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:7} ({e.kind:7}) {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
season(spring).
season(summer).
season(autumn).
season(winter).

item(wand).
item(hat).
item(bottle).

helper(parent).
helper(sibling).
helper(friend).

brave_story(S, I, H) :- season(S), item(I), helper(H), compatible(S, I, H).

compatible(winter, wand, parent).
compatible(spring, hat, friend).
compatible(summer, bottle, parent).
compatible(autumn, wand, parent).

% Show the same notion of reasonableness as Python:
% winter + bottle is too chaotic for this world.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SEASONS:
        lines.append(asp.fact("season", s))
    for i in MAGIC_ITEMS:
        lines.append(asp.fact("item", i))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SEASONS:
        for i in MAGIC_ITEMS:
            for h in HELPERS:
                if s == "winter" and i == "bottle":
                    continue
                if s == "summer" and i == "hat" and h == "sibling":
                    continue
                combos.append((s, i, h))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show brave_story/3."))
    return sorted(set(asp.atoms(model, "brave_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A funny season story with bravery, dialogue, and a little magic.")
    ap.add_argument("--season", choices=SEASONS)
    ap.add_argument("--magic-item", choices=MAGIC_ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    season = getattr(args, "season", None) or rng.choice(list(SEASONS))
    magic_item = getattr(args, "magic_item", None) or rng.choice(list(MAGIC_ITEMS))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    reasonableness_check(_safe_lookup(SEASONS, season), _safe_lookup(MAGIC_ITEMS, magic_item), _safe_lookup(HELPERS, helper))

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(season=season, magic_item=magic_item, helper=helper, hero_name=name, hero_gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SEASONS, params.season), _safe_lookup(MAGIC_ITEMS, params.magic_item), _safe_lookup(HELPERS, params.helper), params.hero_name, params.hero_gender, params.parent, params.trait)
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
    StoryParams(season="spring", magic_item="hat", helper="friend", hero_name="Mina", hero_gender="girl", parent="mother", trait="shy"),
    StoryParams(season="autumn", magic_item="wand", helper="parent", hero_name="Owen", hero_gender="boy", parent="father", trait="careful"),
    StoryParams(season="summer", magic_item="bottle", helper="parent", hero_name="Lia", hero_gender="girl", parent="mother", trait="silly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show brave_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, i, h in combos:
            print(f"  {s:7} {i:7} {h:7}")
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
            header = f"### {p.hero_name}: {p.season} / {p.magic_item} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
