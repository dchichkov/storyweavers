#!/usr/bin/env python3
"""
A standalone storyworld for a rhyming, child-facing tale about an abacus,
privacy, and a little machine that helps with counting.

Seed premise:
- A child wants to automate counting with an abacus.
- The child worries about privacy: the numbers and notes are private.
- A helpful adult suggests a safer way, and the child learns how to keep
  the counting fun without sharing secrets.

The story engine models:
- a child, a helper, an abacus, a note card, and a small counting helper
- physical state in meters and emotional state in memes
- an inner-monologue beat and a dialogue beat
- a rhyming, narrated resolution driven by world state
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Registries
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


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class CharacterSpec:
    type: str
    name_pool: tuple[str, ...]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    carries_secrets: bool = False
    protective: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class ToolSpec:
    label: str
    phrase: str
    purpose: str
    rhyming_closure: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


CHARACTERS = {
    "girl": CharacterSpec("girl", ("Mina", "Luna", "Ivy", "Nia", "Zoe", "Maya")),
    "boy": CharacterSpec("boy", ("Theo", "Nico", "Eli", "Finn", "Leo", "Owen")),
}

HELPERS = {
    "mother": CharacterSpec("mother", ("Mom",)),
    "father": CharacterSpec("father", ("Dad",)),
    "teacher": CharacterSpec("teacher", ("Ms. Lane", "Mr. Reed")),
}

OBJECTS = {
    "abacus": ObjectSpec(
        label="abacus",
        phrase="a bright little abacus with smooth wooden beads",
        carries_secrets=False,
    ),
    "note": ObjectSpec(
        label="note card",
        phrase="a tiny note card with private numbers",
        carries_secrets=True,
    ),
    "screen": ObjectSpec(
        label="privacy screen",
        phrase="a folded paper privacy screen",
        carries_secrets=False,
        protective=True,
    ),
}

TOOLS = {
    "automate": ToolSpec(
        label="counting helper",
        phrase="a tiny counting helper that could slide beads in a neat little line",
        purpose="automate counting",
        rhyming_closure="clickety-swipe, clickety-sway, it counted the private numbers in a safe little way",
    )
}


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries_secrets: bool = False
    protective: bool = False
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    abacus: object | None = None
    child: object | None = None
    helper: object | None = None
    helper_tool: object | None = None
    note: object | None = None
    screen: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "teacher", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


# meters/memes keys
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


SECRET_RISK = "secret_risk"
PRIVATE_TENSION = "private_tension"
JOY = "joy"
RELIEF = "relief"
CURIOUS = "curious"
CONFIDENCE = "confidence"
WORRY = "worry"


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def story_rhyme(a: str, b: str) -> str:
    return f"{a} ... {b}"


def is_private_item(obj: Entity) -> bool:
    return obj.carries_secrets


def risk_private_info(world: World, obj_id: str) -> bool:
    obj = world.get(obj_id)
    return is_private_item(obj) and obj.meters.get("seen", 0.0) < 1.0


def safe_for_automation(world: World, helper_id: str, obj_id: str) -> bool:
    helper = world.get(helper_id)
    obj = world.get(obj_id)
    screen = any(e.protective and e.owner == helper.owner for e in list(world.entities.values()))
    return helper.kind == "helper" and obj.label == "abacus" and screen


def predict_breach(world: World) -> bool:
    return world.get("note").meters.get("open", 0.0) >= 1.0 and not any(
        e.protective and e.worn_by == world.get("child").id for e in list(world.entities.values())
    )


# ---------------------------------------------------------------------------
# Inline screenplay
# ---------------------------------------------------------------------------

def _prose_title(setting: str) -> str:
    if setting:
        return f"In {setting}, where little sounds can ring"
    return "In a small, bright room where numbers sing"


def _inner_monologue(child: Entity, note: Entity, abacus: Entity, helper_tool: Entity) -> str:
    return (
        f"{child.pronoun('subject').capitalize()} peeked at the abacus and thought, "
        f'"If I can automate my counting, I can make it neat. '
        f'But if the note card stays open, my private lines might leak."'
    )


def _dialogue(helper: Entity, child: Entity) -> str:
    return (
        f'"Let’s use the privacy screen," said {helper.id}. '
        f'"Then your secret sums can stay tucked in, like a snug little bean."'
    )


def _resolve_rhyme(tool: ToolSpec, child: Entity, helper: Entity, abacus: Entity) -> str:
    return (
        f"{child.id} set up the screen and gave a small grin; "
        f"{tool.rhyming_closure}. "
        f"{child.pronoun('subject').capitalize()} and {helper.id} counted together, "
        f"and the room felt light again."
    )


def tell(setting: str, child_gender: str, helper_kind: str, seed: Optional[int] = None) -> World:
    rng = random.Random(seed)
    world = World(setting=setting)

    child_name = rng.choice(_safe_lookup(CHARACTERS, child_gender).name_pool)
    helper_name = rng.choice(_safe_lookup(HELPERS, helper_kind).name_pool)

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        meters={SECRET_RISK: 0.0, PRIVATE_TENSION: 0.0},
        memes={JOY: 0.0, CURIOUS: 1.0, CONFIDENCE: 0.0, WORRY: 0.0, RELIEF: 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="helper",
        type=helper_kind,
        meters={},
        memes={CONFIDENCE: 1.0},
        owner=child.id,
    ))
    abacus = world.add(Entity(
        id="abacus",
        kind="thing",
        type="abacus",
        label="abacus",
        phrase=OBJECTS["abacus"].phrase,
        owner=child.id,
        meters={"counted": 0.0},
    ))
    note = world.add(Entity(
        id="note",
        kind="thing",
        type="note",
        label="note card",
        phrase=OBJECTS["note"].phrase,
        owner=child.id,
        carries_secrets=True,
        meters={"open": 0.0, "seen": 0.0},
    ))
    screen = world.add(Entity(
        id="screen",
        kind="thing",
        type="screen",
        label="privacy screen",
        phrase=OBJECTS["screen"].phrase,
        owner=child.id,
        protective=True,
        worn_by=child.id,
    ))
    helper_tool = world.add(Entity(
        id="helper_tool",
        kind="thing",
        type="tool",
        label=TOOLS["automate"].label,
        phrase=TOOLS["automate"].phrase,
        owner=child.id,
        meters={"ready": 1.0},
    ))

    # Act 1: setup
    world.say(f"{_prose_title(setting)}.")
    world.say(
        f"{child.id} found an abacus at a tiny desk and liked the clack of each bead."
    )
    world.say(
        f"{child.id} also had a note card with private numbers, because some things are for one pair of eyes."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} wanted to {TOOLS['automate'].purpose} and make the counting sing."
    )

    # Act 2: tension
    world.para()
    world.say(_inner_monologue(child, note, abacus, helper_tool))
    note.meters["open"] = 1.0
    child.memes[WORRY] += 1.0
    child.meters[PRIVATE_TENSION] += 1.0

    if predict_breach(world):
        world.say(
            f"{child.id} worried that a peek at the note could make the private numbers leak like a creek."
        )
    world.say(_dialogue(helper, child))
    child.memes[CURIOUS] += 1.0

    # Act 3: resolution
    world.para()
    if not safe_for_automation(world, helper.id, abacus.id):
        pass

    child.meters[SECRET_RISK] += 0.0
    child.memes[JOY] += 1.0
    child.memes[RELIEF] += 1.0
    child.memes[CONFIDENCE] += 1.0
    note.meters["seen"] = 0.0
    abacus.meters["counted"] += 1.0
    world.say(
        f"{child.id} slid the beads while the screen stood near, and the private note stayed out of sight."
    )
    world.say(
        _resolve_rhyme(TOOLS["automate"], child, helper, abacus)
    )
    world.say(
        f"So {child.id} could automate the count with a gentle little flow, "
        f"and keep privacy tucked close, as soft as a snowflake's glow."
    )

    world.facts.update(
        child=child,
        helper=helper,
        abacus=abacus,
        note=note,
        screen=screen,
        helper_tool=helper_tool,
    )
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    return [
        "Write a short rhyming story for a child who wants to automate counting with an abacus.",
        f"Tell a gentle rhyme where {child.id} worries about privacy and {helper.id} offers a safer way.",
        "Create a tiny story with inner monologue and dialogue about keeping private numbers private.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    note: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "note")
    abacus: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "abacus")
    return [
        QAItem(
            question=f"What did {child.id} want to do with the abacus?",
            answer=f"{child.id} wanted to automate the counting so the beads could move in a neat, easy way.",
        ),
        QAItem(
            question=f"Why did {child.id} worry about the note card?",
            answer=f"{child.id} worried because the note card held private numbers, and those were not meant for everyone to see.",
        ),
        QAItem(
            question=f"What did {helper.id} suggest to protect the private numbers?",
            answer=f"{helper.id} suggested using a privacy screen so the note could stay hidden while {child.id} counted.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.id} could use the abacus to count happily while the private note stayed safely out of sight.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "abacus": [
        QAItem(
            question="What is an abacus?",
            answer="An abacus is a counting tool with beads that slide back and forth on rods or wires.",
        ),
    ],
    "privacy": [
        QAItem(
            question="What is privacy?",
            answer="Privacy means keeping some things for yourself or only sharing them with people you trust.",
        ),
    ],
    "screen": [
        QAItem(
            question="What does a privacy screen do?",
            answer="A privacy screen helps block other people from seeing what is behind it.",
        ),
    ],
    "automate": [
        QAItem(
            question="What does automate mean?",
            answer="To automate means to make a job happen with a helper or a machine, so it takes less work to do it by hand.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["abacus"])
    out.extend(WORLD_KNOWLEDGE["privacy"])
    out.extend(WORLD_KNOWLEDGE["screen"])
    out.extend(WORLD_KNOWLEDGE["automate"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when the child uses the abacus, privacy is protected,
% and the helper offers a screen before the note becomes visible.
valid_story(child, helper, abacus, screen) :-
    item(child, abacus),
    item(child, note),
    item(child, screen),
    helper(helper),
    protects(screen, note),
    hides(screen, note),
    not breached(note).

breached(note) :- seen(note).

private_ok(note) :- secret(note), not breached(note).

useful_tool(abacus) :- item(_, abacus).

% The narrative twin: automate + privacy + abacus must all coexist.
story_theme(automate, privacy, abacus) :- useful_tool(abacus), private_ok(note).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("theme", "automate"),
        asp.fact("theme", "privacy"),
        asp.fact("tool", "abacus"),
    ]
    for cname, spec in CHARACTERS.items():
        lines.append(asp.fact("character_kind", cname))
    for hname in HELPERS:
        lines.append(asp.fact("helper_kind", hname))
    lines.append(asp.fact("item", "child", "abacus"))
    lines.append(asp.fact("item", "child", "note"))
    lines.append(asp.fact("item", "child", "screen"))
    lines.append(asp.fact("secret", "note"))
    lines.append(asp.fact("protects", "screen", "note"))
    lines.append(asp.fact("hides", "screen", "note"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_theme/3.\n#show valid_story/4."))
    atoms = set(asp.atoms(model, "story_theme")) | set(asp.atoms(model, "valid_story"))
    ok = ("automate", "privacy", "abacus") in atoms
    if ok:
        print("OK: ASP twin includes automate/privacy/abacus and a valid story shape.")
        return 0
    print("MISMATCH: ASP twin failed to derive the core story theme.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str = ""
    child_gender: str = ""
    helper_kind: str = ""
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: automate, privacy, abacus.")
    ap.add_argument("--setting", choices=["tiny room", "study nook", "classroom"], default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper", choices=list(HELPERS), default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(["tiny room", "study nook", "classroom"])
    child_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_kind = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(setting=setting, child_gender=child_gender, helper_kind=helper_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.child_gender, params.helper_kind, seed=params.seed)
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
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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
    StoryParams(setting="tiny room", child_gender="girl", helper_kind="mother"),
    StoryParams(setting="study nook", child_gender="boy", helper_kind="father"),
    StoryParams(setting="classroom", child_gender="girl", helper_kind="teacher"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_theme/3.\n#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story_theme/3.\n#show valid_story/4."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen = set()
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
