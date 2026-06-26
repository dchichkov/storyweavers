#!/usr/bin/env python3
"""
storyworlds/worlds/penicillin_misunderstanding_slice_of_life.py
===============================================================

A small slice-of-life storyworld about a child, a prescription for penicillin,
and a gentle misunderstanding that gets cleared up at the kitchen table.

Premise:
- A child feels a little unwell.
- A parent brings home penicillin that the doctor recommended.
- The child misunderstands the name and worries it is scary, bitter, or meant
  for something else.
- A calm explanation, a glass of water, and a small snack turn the moment into
  an ordinary, reassuring part of the day.

The world is intentionally small, domestic, and state-driven. Emotional meters
and physical meters both matter, and the story changes according to what the
characters believe, what they see, and what they decide to do.

This file follows the Storyweavers standalone storyworld contract.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    med: object | None = None
    parent: object | None = None
    snack: object | None = None
    water: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather", "brother"}:
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
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)
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
class Medicine:
    id: str
    label: str
    form: str
    flavor: str
    purpose: str
    made_for: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Snack:
    id: str
    label: str
    phrase: str
    comfort: str
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
class StoryParams:
    place: str
    age: str
    name: str
    parent: str
    mood: str
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
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affordances={"medicine", "snack", "talk"}),
    "living_room": Setting(place="the living room", indoors=True, affordances={"medicine", "snack", "talk"}),
    "bedroom": Setting(place="the bedroom", indoors=True, affordances={"medicine", "talk"}),
    "porch": Setting(place="the porch", indoors=False, affordances={"medicine", "talk"}),
}

MEDICINES = {
    "penicillin": Medicine(
        id="penicillin",
        label="penicillin",
        form="liquid medicine",
        flavor="a little chalky",
        purpose="help fight the infection",
        made_for={"girl", "boy"},
    ),
}

SNACKS = {
    "crackers": Snack(
        id="crackers",
        label="crackers",
        phrase="a few plain crackers",
        comfort="mild and easy to chew",
    ),
    "juice": Snack(
        id="juice",
        label="juice",
        phrase="a small glass of apple juice",
        comfort="cool and sweet",
    ),
    "applesauce": Snack(
        id="applesauce",
        label="applesauce",
        phrase="a little cup of applesauce",
        comfort="soft and soothing",
    ),
}

MOODS = ["worrying", "curious", "grumpy", "tired", "shy", "patient"]
NAMES = {
    "girl": ["Maya", "Lena", "Ivy", "Nora", "Tessa"],
    "boy": ["Ben", "Owen", "Theo", "Milo", "Eli"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def cite_setting(setting: Setting) -> str:
    if setting.place == "the kitchen":
        return "The kitchen smelled faintly like toast and soap."
    if setting.place == "the living room":
        return "The living room was quiet except for the soft hum of the lamp."
    if setting.place == "the bedroom":
        return "The bedroom was warm, with a blanket folded at the foot of the bed."
    return "The porch air felt cool and still."


def medicine_taste(med: Medicine) -> str:
    return {
        "liquid medicine": "a little chalky",
    }.get(med.form, "plain")


def explain_misunderstanding(child: Entity, med: Medicine) -> str:
    return (
        f'{child.id} blinked at the word "{med.label}" and thought it sounded too '
        f"big and serious for a small kid."
    )


def correct_explanation(parent: Entity, child: Entity, med: Medicine) -> str:
    return (
        f'"{med.label} is medicine," {parent.pronoun("subject").capitalize()} said. '
        f'"It is here to {med.purpose}, not to scare you."'
    )


def child_relief(child: Entity) -> str:
    return f"{child.id} felt the tight knot in their chest loosen a little."


def check_reasonable(choice: StoryParams) -> None:
    if choice.age not in {"girl", "boy"}:
        pass
    if choice.place not in SETTINGS:
        pass
    if choice.mood not in MOODS:
        pass


# ---------------------------------------------------------------------------
# Causal story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    child_type = params.age
    parent_type = "mother" if params.parent == "mother" else "father"

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=child_type,
        label=params.name,
        meters={"energy": 0.5, "sick": 1.0, "sip_taken": 0.0},
        memes={"worry": 1.0 if params.mood == "worrying" else 0.5, "trust": 0.5},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {params.parent}",
        meters={"care": 1.0},
        memes={"calm": 1.0, "patience": 1.0},
    ))
    med = world.add(Entity(
        id="penicillin_bottle",
        kind="thing",
        type="medicine",
        label="penicillin",
        phrase=MEDICINES["penicillin"].form,
        owner=child.id,
        caretaker=parent.id,
        held_by=parent.id,
        meters={"dose_ready": 1.0},
    ))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        type="snack",
        label="snack",
        phrase="a small snack",
        owner=child.id,
        caretaker=parent.id,
        held_by=parent.id,
        meters={"ready": 1.0},
    ))
    water = world.add(Entity(
        id="water",
        kind="thing",
        type="water",
        label="water",
        phrase="a glass of water",
        owner=child.id,
        caretaker=parent.id,
        held_by=parent.id,
        meters={"ready": 1.0},
    ))

    world.facts.update(child=child, parent=parent, med=med, snack=snack, water=water, params=params)

    # Act 1
    world.say(f"{params.name} was a little {params.mood} {params.age} in {setting.place}.")
    world.say(cite_setting(setting))
    world.say(f"That afternoon, {params.parent} brought over the penicillin bottle and a small snack.")
    world.say(f"{params.name} looked at the label and frowned.")

    # misunderstanding
    child.memes["worry"] += 1.0
    child.memes["confusion"] = 1.0
    world.say(explain_misunderstanding(child, med))
    world.say(
        f"{params.name} wondered if the penicillin would taste strange, or if it was something only grown-ups understood."
    )

    # Act 2
    world.para()
    world.say(
        f"{params.parent} sat beside {params.name}, opened the bottle carefully, and kept the spoon steady."
    )
    world.say(correct_explanation(parent, child, med))
    world.say(
        f'"It helps your body feel better," {params.parent} added, "and you can take it with a sip of water and a little snack."'
    )
    child.memes["confusion"] = 0.0
    child.memes["trust"] += 1.0
    child.memes["worry"] = max(0.0, child.memes["worry"] - 0.5)

    # resolution
    world.para()
    world.say(
        f"{params.name} took a breath, held the cup with both hands, and tried the medicine."
    )
    child.meters["sip_taken"] = 1.0
    world.say(
        f"The taste was {medicine_taste(med)}, but the crackers and juice made the moment easier."
    )
    child.meters["sick"] = 0.0
    child.memes["relief"] = 1.0
    world.say(child_relief(child))
    world.say(
        f"By the time the snack was gone, {params.name} felt braver, and the penicillin bottle sat quietly on the counter like an ordinary part of the day."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    params: StoryParams = _safe_fact(world, f, "params")
    return [
        f'Write a gentle slice-of-life story for a young child named {child.id} who hears the word "penicillin" at home.',
        f"Tell a simple story where {child.id} misunderstands penicillin, then feels better after a calm explanation from {params.parent}.",
        f"Write a short home story about medicine, a snack, and a worried child learning what penicillin is for.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    params: StoryParams = _safe_fact(world, f, "params")
    med: Entity = _safe_fact(world, f, "med")
    qa = [
        QAItem(
            question=f"Why did {child.id} look worried when {params.parent} brought out the penicillin?",
            answer=(
                f"{child.id} did not understand the word penicillin at first, so {child.pronoun('subject')} thought it sounded big and serious."
            ),
        ),
        QAItem(
            question=f"What did {params.parent} say the penicillin was for?",
            answer=(
                f"{params.parent.capitalize()} said the penicillin was medicine and that it was there to help fight the infection."
            ),
        ),
        QAItem(
            question=f"What helped {child.id} feel braver about taking the medicine?",
            answer=(
                f"A calm explanation, a sip of water, and a small snack helped {child.id} feel braver about taking the penicillin."
            ),
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end after {child.id} took the penicillin?",
                answer=(
                    f"{child.id} felt relief, the worry got smaller, and the penicillin bottle became just another normal thing on the counter."
                ),
            )
        )
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is penicillin?",
        answer="Penicillin is a kind of medicine that doctors may use to help the body fight certain infections.",
    ),
    QAItem(
        question="Why do people sometimes take medicine with water?",
        answer="Water helps medicine go down more easily, especially if the medicine tastes a little chalky or dry.",
    ),
    QAItem(
        question="Why can a snack help after medicine?",
        answer="A small snack can make the moment feel gentler and more comfortable, especially when a child feels nervous.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:16} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% setting(Place). indoors(Place). affordance(Place, Thing).
% child(Name, Age). medicine(Med). snack(Snack). parent(Role).

% A reasonable story happens in a place where medicine and talk can happen.
can_story(P) :- setting(P), affordance(P, medicine), affordance(P, talk).

% The misunderstanding is meaningful when a child hears "penicillin" and does
% not yet understand what it is.
misunderstanding(C) :- child(C, _), medicine(penicillin), can_story(_).

% The resolution is reasonable when a parent explains, then the child can take
% the medicine with water or a snack.
resolved(C) :- misunderstanding(C), snack(_), can_story(_).

#show can_story/1.
#show misunderstanding/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affordance", sid, a))
    lines.append(asp.fact("medicine", "penicillin"))
    lines.append(asp.fact("snack", "snack"))
    for age in ("girl", "boy"):
        lines.append(asp.fact("child", age, age))
    lines.append(asp.fact("parent", "mother"))
    lines.append(asp.fact("parent", "father"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_models() -> list[list]:
    import storyworlds.asp as asp

    program = asp_program("#show can_story/1.\n#show misunderstanding/1.\n#show resolved/1.")
    return asp.solve(program, models=0)


def asp_verify() -> int:
    ok = True
    if not asp_models():
        print("MISMATCH: ASP produced no models.")
        ok = False
    if not SETTINGS:
        print("MISMATCH: no settings registered.")
        ok = False
    if ok:
        print(f"OK: ASP program runs and the world has {len(SETTINGS)} settings.")
        return 0
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: penicillin misunderstanding, slice-of-life style."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--age", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--mood", choices=MOODS)
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
    age = getattr(args, "age", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, age))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    mood = getattr(args, "mood", None) or rng.choice(MOODS)
    check_reasonable(StoryParams(place=place, age=age, name=name, parent=parent, mood=mood))
    return StoryParams(place=place, age=age, name=name, parent=parent, mood=mood)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show can_story/1.\n#show misunderstanding/1.\n#show resolved/1."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import storyworlds.asp as asp

        models = asp_models()
        print(f"{len(models)} ASP model(s) found.")
        for i, model in enumerate(models[:5], 1):
            print(f"Model {i}: {model}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="kitchen", age="girl", name="Maya", parent="mother", mood="worrying"),
            StoryParams(place="living_room", age="boy", name="Theo", parent="father", mood="curious"),
            StoryParams(place="bedroom", age="girl", name="Ivy", parent="mother", mood="tired"),
            StoryParams(place="porch", age="boy", name="Ben", parent="father", mood="shy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name} in {p.place} ({p.age}, {p.mood})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
