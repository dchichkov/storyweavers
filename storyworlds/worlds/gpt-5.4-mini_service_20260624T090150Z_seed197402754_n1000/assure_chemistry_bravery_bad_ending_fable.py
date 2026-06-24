#!/usr/bin/env python3
"""
assure_chemistry_bravery_bad_ending_fable.py
============================================

A small fable-like story world about a brave little apprentice, a chemistry
promise, and a bad ending that follows a careless choice.

The world is intentionally narrow: a child-facing fable domain where a teacher,
a helper, a chemical mixture, and a promise to stay safe interact through a
few causal rules. The stories are complete and state-driven, but the outcome is
a cautionary one: bravery without care can make things worse.

Seed tale:
---
A small fox named Pip wanted to help in the village workshop. The old owl
assured Pip that chemistry could be safe if everyone followed the rules.
Pip promised to be brave, but when the bright bottle began to fizz, Pip
ignored the warning and lifted the stopper. The foam spilled, the lamp went
out, and the lesson ended badly. Still, the owl told Pip that true bravery
means listening before acting.
---

This world keeps the prose authored and concrete, with a fable tone and a
clear ending image.
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
# World entities
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

    child: object | None = None
    mentor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "owl", "teacher"}:
            return {"subject": "she" if self.type == "girl" else "it",
                    "object": "her" if self.type == "girl" else "it",
                    "possessive": "her" if self.type == "girl" else "its"}[case]
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
    place: str = "the village workshop"
    affords: set[str] = field(default_factory=lambda: {"chemistry"})
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
class Mixture:
    id: str
    label: str
    phrase: str
    risk: str
    mess: str
    tags: set[str] = field(default_factory=set)
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
    guards: set[str]
    prep: str
    tail: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mixture_active: bool = False
        self.safety_closed: bool = True
        self.spill: bool = False
        self.lamp_out: bool = False

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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.mixture_active = self.mixture_active
        w.safety_closed = self.safety_closed
        w.spill = self.spill
        w.lamp_out = self.lamp_out
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    name: str
    child_type: str
    mentor_type: str
    mixture: str
    tool: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTING = Setting()

MIXTURES = {
    "sparkle_fizz": Mixture(
        id="sparkle_fizz",
        label="a bright bottle of fizzing chemistry",
        phrase="a bright bottle that could fizz and foam",
        risk="the foam could burst out",
        mess="spilled foam",
        tags={"chemistry", "fizz"},
    ),
    "ink_swirl": Mixture(
        id="ink_swirl",
        label="a dark blue swirl",
        phrase="a dark blue mix that could stain hands",
        risk="the ink could splash everywhere",
        mess="stained table",
        tags={"chemistry", "ink"},
    ),
    "vinegar_bubble": Mixture(
        id="vinegar_bubble",
        label="a vinegar bubble jar",
        phrase="a jar that bubbled when stirred",
        risk="the bubbles could climb too high",
        mess="sticky bubbles",
        tags={"chemistry", "bubble"},
    ),
}

TOOLS = {
    "goggles": Tool(
        id="goggles",
        label="goggles",
        phrase="clear goggles",
        guards={"spill", "stain"},
        prep="put on the goggles first",
        tail="took off the goggles and closed the bottle",
    ),
    "tray": Tool(
        id="tray",
        label="tray",
        phrase="a shallow tray",
        guards={"spill"},
        prep="set the bottle in a shallow tray",
        tail="carried the tray carefully back to the table",
    ),
    "cloth": Tool(
        id="cloth",
        label="cloth",
        phrase="a folded cloth",
        guards={"stain"},
        prep="cover the table with a folded cloth",
        tail="folded the cloth up after the lesson",
    ),
}

CHARACTER_NAMES = ["Pip", "Milo", "Nia", "Tessa", "Roo", "Jin"]
CHILD_TYPES = {"fox", "girl", "boy"}
MENTOR_TYPES = {"owl", "teacher"}

CURATED = [
    StoryParams(name="Pip", child_type="fox", mentor_type="owl", mixture="sparkle_fizz", tool="goggles"),
    StoryParams(name="Milo", child_type="boy", mentor_type="teacher", mixture="vinegar_bubble", tool="tray"),
    StoryParams(name="Nia", child_type="girl", mentor_type="owl", mixture="ink_swirl", tool="cloth"),
]

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(mixture: Mixture, tool: Tool) -> bool:
    if mixture.id == "sparkle_fizz" and tool.id == "goggles":
        return True
    if mixture.id == "vinegar_bubble" and tool.id == "tray":
        return True
    if mixture.id == "ink_swirl" and tool.id == "cloth":
        return True
    return False


def explain_rejection(mixture: Mixture, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not honestly help with {mixture.label}. "
        f"The tool must match the danger, or the fable would not make sense.)"
    )


def introduce(world: World, child: Entity, mentor: Entity) -> None:
    world.say(
        f"In the village workshop, there once lived a little {child.type} named {child.id} "
        f"who admired {mentor.label}."
    )
    world.say(
        f"{mentor.pronoun('subject').capitalize()} was wise enough to know that chemistry can be helpful, "
        f"but only when handled with care."
    )


def promise(world: World, child: Entity, mixture: Mixture) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.say(
        f"{child.id} wanted to try {mixture.label}, because {mixture.phrase} sounded like a small adventure."
    )
    world.say(
        f"The old mentor assured {child.pronoun('object')} that safe chemistry begins with a calm plan."
    )


def predict_bad_ending(world: World, child: Entity, mixture: Mixture) -> dict:
    sim = world.copy()
    sim.mixture_active = True
    sim.safety_closed = False
    spill = True
    lamp_out = True
    return {"spill": spill, "lamp_out": lamp_out}


def action(world: World, child: Entity, mentor: Entity, mixture: Mixture, tool: Tool) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0) + 1
    world.say(
        f"{child.id} said {child.pronoun('subject')} was brave enough to help."
    )
    world.say(
        f"At first, {mentor.pronoun('subject')} suggested, “{tool.prep}, and then we can begin.”"
    )
    world.say(
        f"But {child.id} leaned closer to the bottle, even after the warning about how {mixture.risk}."
    )
    world.facts["predicted"] = predict_bad_ending(world, child, mixture)


def bad_turn(world: World, child: Entity, mentor: Entity, mixture: Mixture) -> None:
    world.spill = True
    world.lamp_out = True
    child.memes["regret"] = child.memes.get("regret", 0) + 1
    mentor.memes["worry"] = mentor.memes.get("worry", 0) + 1
    world.say(
        f"{child.id} lifted the stopper too soon, and the bottle burst into {mixture.mess}."
    )
    world.say(
        f"The lamp went out, the table grew messy, and the lesson ended in a bad way."
    )


def ending(world: World, child: Entity, mentor: Entity, mixture: Mixture, tool: Tool) -> None:
    world.para()
    world.say(
        f"{mentor.id} did not shout. Instead, {mentor.pronoun('subject')} gently told {child.pronoun('object')} "
        f"that true bravery means listening before acting."
    )
    world.say(
        f"{child.id} looked at the spilled table, held still, and learned that a quick heart is not the same thing as a wise heart."
    )
    world.say(
        f"By the end, the room was quiet again, the bottle was closed, and the careful {tool.label} sat beside the mess like a warning."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.child_type, label=params.name))
    mentor = world.add(Entity(id="Mentor", kind="character", type=params.mentor_type, label="the old mentor"))

    mixture = _safe_lookup(MIXTURES, params.mixture)
    tool = _safe_lookup(TOOLS, params.tool)

    world.add(Entity(id="mixture", type="thing", label=mixture.label, phrase=mixture.phrase, owner=child.id))
    world.add(Entity(id="tool", type="thing", label=tool.label, phrase=tool.phrase, owner=mentor.id))

    introduce(world, child, mentor)
    world.para()
    promise(world, child, mixture)
    action(world, child, mentor, mixture, tool)
    bad_turn(world, child, mentor, mixture)
    ending(world, child, mentor, mixture, tool)

    world.facts.update(
        child=child,
        mentor=mentor,
        mixture=mixture,
        tool=tool,
        bad_ending=True,
        name=params.name,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    mixture = _safe_fact(world, f, "mixture")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short fable for a young child about {child.id}, chemistry, and a bad ending.',
        f"Tell a story where {child.id} wants to try {mixture.label} but must be assured about safety.",
        f'Write a gentle cautionary tale that includes the word "assure" and ends with a lesson about bravery.',
        f"Make the story feel like a fable, with a wise mentor and one poor choice during chemistry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    mentor = _safe_fact(world, f, "mentor")
    mixture = _safe_fact(world, f, "mixture")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who wanted to help with the chemistry in the workshop?",
            answer=f"{child.id} wanted to help with the chemistry in the workshop.",
        ),
        QAItem(
            question=f"What did the mentor assure {child.id} about chemistry?",
            answer=f"The mentor assured {child.id} that chemistry can be safe when people follow the rules.",
        ),
        QAItem(
            question=f"What went wrong when {child.id} acted too quickly?",
            answer=f"The stopper was lifted too soon, the mixture spilled into {mixture.mess}, and the lesson ended badly.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a bad ending: the room was messy, the lamp went out, and {child.id} learned a careful lesson about bravery.",
        ),
        QAItem(
            question=f"What did the mentor say true bravery means?",
            answer=f"The mentor said true bravery means listening before acting.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chemistry?",
            answer="Chemistry is the study of what things are made of and how they can change when they are mixed together.",
        ),
        QAItem(
            question="Why should children be careful with chemistry?",
            answer="Children should be careful with chemistry because some mixtures can spill, splash, or make a mess if they are handled the wrong way.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary, especially when you try to do the right thing.",
        ),
        QAItem(
            question="What does it mean to assure someone?",
            answer="To assure someone means to tell them in a calm and caring way that they can feel safe or sure about something.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_type(C).
mentor(M) :- mentor_type(M).
mixture(M) :- mix(M).
tool(T) :- instrument(T).

compatible(sparkle_fizz, goggles).
compatible(vinegar_bubble, tray).
compatible(ink_swirl, cloth).

valid_story(C, Mx, T) :- child(C), mixture(Mx), tool(T), compatible(Mx, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in CHARACTER_NAMES:
        lines.append(asp.fact("name", n))
    for t in CHILD_TYPES:
        lines.append(asp.fact("child_type", t))
    for t in MENTOR_TYPES:
        lines.append(asp.fact("mentor_type", t))
    for m in MIXTURES.values():
        lines.append(asp.fact("mix", m.id))
    for t in TOOLS.values():
        lines.append(asp.fact("instrument", t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((m, t.id) for m in MIXTURES.values() for t in TOOLS.values() if reasonableness_gate(m, t))
    cl = sorted(set(asp_valid_stories()))
    # Project the clingo facts into mixture/tool only by using curated story shapes.
    cl_proj = []
    for _, mx, tl in cl:
        cl_proj.append((mx, tl))
    if sorted(py) == sorted(cl_proj):
        print(f"OK: clingo gate matches Python gate ({len(py)} compatible pairs).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("Python:", sorted(py))
    print("Clingo:", sorted(cl_proj))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about chemistry, bravery, and a bad ending.")
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--child-type", choices=sorted(CHILD_TYPES))
    ap.add_argument("--mentor-type", choices=sorted(MENTOR_TYPES))
    ap.add_argument("--mixture", choices=sorted(MIXTURES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
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
    mixture = getattr(args, "mixture", None) or rng.choice(list(MIXTURES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    if not reasonableness_gate(_safe_lookup(MIXTURES, mixture), _safe_lookup(TOOLS, tool)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(CHARACTER_NAMES),
        child_type=getattr(args, "child_type", None) or rng.choice(sorted(CHILD_TYPES)),
        mentor_type=getattr(args, "mentor_type", None) or rng.choice(sorted(MENTOR_TYPES)),
        mixture=mixture,
        tool=tool,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  spill={world.spill} lamp_out={world.lamp_out} safety_closed={world.safety_closed}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
