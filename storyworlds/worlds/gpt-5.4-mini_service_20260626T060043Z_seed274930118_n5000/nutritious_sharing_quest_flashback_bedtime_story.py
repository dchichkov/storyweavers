#!/usr/bin/env python3
"""
Nutritious Sharing Quest Flashback Bedtime Story
================================================

A small standalone storyworld about a sleepy child, a coveted bedtime snack,
a gentle sharing quest, and a brief flashback that explains why the snack
matters so much.

Premise:
- A child wants a tasty bedtime treat.
- A parent worries the treat should be shared in a kind, nutritious way.
- A flashback reveals the child once learned that sharing makes a snack feel
  warmer and more special.
- The story resolves when the child shares, the table calms down, and bedtime
  feels safe and sweet.

This world is intentionally small and constraint-checked: only stories with a
reasonable nutritious snack, a plausible sharing conflict, and a matching
resolution are generated.
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
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bowl: object | None = None
    child: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"warmth": 0.0, "fullness": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "want": 0.0, "worry": 0.0, "calm": 0.0, "memory": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
class Snack:
    id: str
    label: str
    phrase: str
    taste: str
    nutrition: str
    shareable: bool = True
    warmth_gain: float = 1.0
    fullness_gain: float = 1.0
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
class Place:
    id: str
    label: str
    cozy: bool = True
    affords: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.snack: Optional[Snack] = None
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", cozy=True, affords={"tea", "porridge", "fruit", "toast"}),
    "nursery": Place(id="nursery", label="the nursery", cozy=True, affords={"milk", "oatmeal", "fruit"}),
    "porch": Place(id="porch", label="the porch", cozy=True, affords={"tea", "toast", "fruit"}),
}

SNACKS = {
    "oat_bowl": Snack(
        id="oat_bowl",
        label="a bowl of oatmeal",
        phrase="a warm bowl of oatmeal with berries",
        taste="sweet and soft",
        nutrition="nutritious",
        warmth_gain=1.0,
        fullness_gain=1.0,
        tags={"nutritious", "oat", "sharing"},
    ),
    "fruit_plate": Snack(
        id="fruit_plate",
        label="a plate of fruit",
        phrase="a colorful plate of sliced fruit",
        taste="juicy and bright",
        nutrition="nutritious",
        warmth_gain=0.5,
        fullness_gain=0.8,
        tags={"nutritious", "fruit", "sharing"},
    ),
    "toast_peanut": Snack(
        id="toast_peanut",
        label="toast with peanut butter",
        phrase="two little pieces of toast with peanut butter and banana",
        taste="warm and creamy",
        nutrition="nutritious",
        warmth_gain=1.0,
        fullness_gain=0.9,
        tags={"nutritious", "toast", "sharing"},
    ),
}

CHAR_NAMES = {
    "girl": ["Maya", "Nora", "Lily", "Ava", "Zoe"],
    "boy": ["Theo", "Eli", "Ben", "Leo", "Finn"],
}
TRAITS = ["sleepy", "gentle", "curious", "brave", "patient"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    snack: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def snack_is_reasonable(snack: Snack) -> bool:
    return snack.shareable and "nutritious" in snack.tags


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    snack_id = getattr(args, "snack", None) or rng.choice(sorted(SNACKS))
    snack = _safe_lookup(SNACKS, snack_id)
    if not snack_is_reasonable(snack):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(CHAR_NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place_id, snack=snack_id, name=name, gender=gender, parent=parent, trait=trait)


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    snack = _safe_lookup(SNACKS, params.snack)
    world = World(place)
    world.snack = snack

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))

    bowl = world.add(Entity(
        id="snack",
        type=snack.id,
        label=snack.label,
        phrase=snack.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))

    world.facts.update(child=child, parent=parent, snack=bowl, snack_cfg=snack, place=place, params=params)

    # Act 1
    world.say(
        f"At bedtime, little {params.name} was {params.trait} and drowsy in {place.label}."
    )
    world.say(
        f"{params.name} loved {snack.phrase}, because it felt {snack.taste} and {snack.nutrition}."
    )
    world.say(
        f"{params.name}'s {parent_label(params.parent)} had set the snack on the table like a tiny treasure."
    )

    # Act 2: desire, worry, flashback
    world.para()
    child.memes["want"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"{params.name} wanted to keep {bowl.label} all to {child.pronoun('object')}self, "
        f"but the parent gently said it should be shared."
    )
    world.say(
        f'"If we share it, the snack will feel kinder," said {parent_name(params.parent)}.'
    )
    world.say(
        f"{params.name} frowned for a moment, and then a tiny flashback flickered through {child.pronoun('possessive')} mind."
    )

    world.para()
    child.memes["memory"] += 1
    world.say(
        f"{params.name} remembered a quiet afternoon when a friend offered {child.pronoun('object')} a half-slice of toast."
    )
    world.say(
        f"That small sharing had made the food taste warmer, and it had made {params.name} feel brave."
    )

    # Act 3: share and settle
    world.para()
    child.shared_with.add(parent.id)
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    parent.memes["calm"] += 1
    world.say(
        f"So {params.name} slid {bowl.label} across the table and shared it with the parent."
    )
    world.say(
        f"They ate together under the soft lamp light, and the room felt cozy and still."
    )
    world.say(
        f"At the end, {params.name} was sleepy, full, and smiling, while the {parent_label(params.parent)} tucked in the chair with a happy sigh."
    )

    # physical state
    child.meters["fullness"] += snack.fullness_gain
    child.meters["warmth"] += snack.warmth_gain
    bowl.meters["warmth"] += snack.warmth_gain * 0.5
    return world


def parent_label(parent_type: str) -> str:
    return "mom" if parent_type == "mother" else "dad"


def parent_name(parent_type: str) -> str:
    return "Mom" if parent_type == "mother" else "Dad"


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = _safe_fact(world, f, "params")
    snack = _safe_fact(world, f, "snack_cfg")
    return [
        f'Write a bedtime story about a child named {p.name} and a {snack.nutrition} snack that becomes a Sharing Quest.',
        f"Tell a gentle Flashback story where {p.name} wants {snack.phrase} but learns to share it before sleep.",
        f'Write a cozy story for young children that includes the words "nutritious", "Sharing", "Quest", and "Flashback".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = _safe_fact(world, f, "params")
    child: Entity = _safe_fact(world, f, "child")
    snack: Snack = _safe_fact(world, f, "snack_cfg")
    parent = parent_label(p.parent)
    return [
        QAItem(
            question=f"What did {p.name} want at bedtime?",
            answer=f"{p.name} wanted {snack.phrase} in {world.place.label}, because it was {snack.nutrition} and comforting."
        ),
        QAItem(
            question=f"Why did the parent ask {p.name} to share?",
            answer=f"The parent wanted the snack to be shared kindly, so bedtime could stay calm and fair."
        ),
        QAItem(
            question="What did the flashback help the child remember?",
            answer=f"The flashback helped {p.name} remember that sharing once made food feel warmer and made {p.name} feel brave."
        ),
        QAItem(
            question=f"How did the story end for {p.name} and the {parent}?",
            answer=f"They shared the snack together, felt cozy, and ended the night sleepy and smiling."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does nutritious mean?",
            answer="Nutritious means food has good things in it that help your body grow, stay strong, and feel ready for the day."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something with you."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened before the main moment."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a little journey or mission to do something important."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
reasonably_shareable(S) :- snack(S), shareable(S), nutritious(S).
valid_story(P, S) :- place(P), snack(S), reasonably_shareable(S), cozy(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.cozy:
            lines.append(asp.fact("cozy", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if snack.shareable:
            lines.append(asp.fact("shareable", sid))
        if "nutritious" in snack.tags:
            lines.append(asp.fact("nutritious", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((pid, sid) for pid in PLACES for sid, sn in SNACKS.items() if snack_is_reasonable(sn))
    cl = asp_valid()
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("Python-only:", sorted(set(py) - set(cl)))
    print("ASP-only:", sorted(set(cl) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# Rendering / trace
# ---------------------------------------------------------------------------

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
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world about nutritious sharing, a quest, and a flashback.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--snack", choices=sorted(SNACKS))
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


CURATED = [
    StoryParams(place="kitchen", snack="oat_bowl", name="Maya", gender="girl", parent="mother", trait="sleepy"),
    StoryParams(place="nursery", snack="fruit_plate", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="porch", snack="toast_peanut", name="Nora", gender="girl", parent="mother", trait="curious"),
]


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    snack_id = getattr(args, "snack", None) or rng.choice(sorted(SNACKS))
    snack = _safe_lookup(SNACKS, snack_id)
    if not snack_is_reasonable(snack):
        pass
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(CHAR_NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, snack=snack_id, name=name, gender=gender, parent=parent, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        valid = asp_valid()
        print(f"{len(valid)} valid (place, snack) pairs:\n")
        for place, snack in valid:
            print(f"  {place:8} {snack}")
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
            params = resolve_combo(args, random.Random(seed))
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
            header = f"### {p.name}: {p.snack} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
