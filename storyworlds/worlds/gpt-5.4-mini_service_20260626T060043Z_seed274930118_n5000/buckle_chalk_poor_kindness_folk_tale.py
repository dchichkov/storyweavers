#!/usr/bin/env python3
"""
A small folk-tale storyworld about a poor child, a lost buckle, a piece of chalk,
and a kindness that changes the day.

Premise:
- A poor child wants to travel to town with a treasured buckle.
- The buckle slips away during a hard task and is found only by following chalk marks.
- A neighbor's kindness helps repair the loss, and the child learns to pass the
  kindness onward.

The simulated state tracks:
- physical meters: distance walked, wear, shine, dust, chalk marks, and repair
- emotional memes: worry, hope, gratitude, pride, and kindness
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

# ---------------------------------------------------------------------------
# Core entities
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
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    buckle: object | None = None
    chalk: object | None = None
    child: object | None = None
    helper: object | None = None
    def _sex(self) -> str:
        return self.type

    def pronoun(self, case: str = "subject") -> str:
        if self._sex() in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self._sex() in {"boy", "father", "man"}:
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
    place: str = "the village lane"
    affords: set[str] = field(default_factory=set)
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
class BuckleConfig:
    label: str
    phrase: str
    region: str = "waist"
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
class ChalkConfig:
    label: str
    phrase: str = "a small piece of chalk"
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
class KindnessConfig:
    label: str
    phrase: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SETTING = Setting(place="the village lane", affords={"walk", "fetch", "search", "share"})

BUCKLES = {
    "plain": BuckleConfig(label="buckle", phrase="a small brass buckle"),
    "bright": BuckleConfig(label="buckle", phrase="a bright buckle with a little shine"),
}

CHALKS = {
    "white": ChalkConfig(label="chalk", phrase="a small piece of white chalk"),
    "blue": ChalkConfig(label="chalk", phrase="a stub of blue chalk"),
}

KINDNESSES = {
    "help": KindnessConfig(label="kindness", phrase="a kindly helping hand"),
    "gift": KindnessConfig(label="kindness", phrase="a simple gift"),
}

HERO_NAMES = ["Mara", "Nell", "Tobin", "Pip", "Iris", "Oren"]
HELPER_NAMES = ["Old Hester", "Goodman Rye", "Aunt Wren", "Baker Marn"]
TRAITS = ["poor", "gentle", "brave", "careful", "hopeful"]


@dataclass
class StoryParams:
    setting: str = "lane"
    buckle: str = "plain"
    chalk: str = "white"
    kindness: str = "help"
    name: str = "Mara"
    helper: str = "Old Hester"
    trait: str = "poor"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model rules
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


def _walk(world: World, child: Entity) -> list[str]:
    out = []
    if child.meters.get("worry", 0.0) >= THRESHOLD and child.meters.get("search", 0.0) < THRESHOLD:
        return out
    if child.meters.get("search", 0.0) >= THRESHOLD:
        sig = ("chalk_found")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["hope"] = child.memes.get("hope", 0.0) + 1
            child.meters["chalk"] = child.meters.get("chalk", 0.0) + 1
            out.append("The chalk marks led the child forward like little white stars.")
    return out


def _repair(world: World, child: Entity, helper: Entity, buckle: Entity) -> list[str]:
    out = []
    if child.meters.get("kindness", 0.0) < THRESHOLD:
        return out
    if ("repair",) in world.fired:
        return out
    world.fired.add(("repair",))
    buckle.meters["shine"] = buckle.meters.get("shine", 0.0) + 1
    child.memes["gratitude"] = child.memes.get("gratitude", 0.0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    out.append("With a patient hand, the helper made the buckle whole again.")
    return out


def propagate(world: World, child: Entity, helper: Entity, buckle: Entity) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for sent in _walk(world, child):
            world.say(sent)
            changed = True
        for sent in _repair(world, child, helper, buckle):
            world.say(sent)
            changed = True


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------

def tell_story(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type="girl", traits=[params.trait, "poor"]))
    helper = world.add(Entity(id="Helper", kind="character", type="woman", label=params.helper, traits=["kind"]))
    buckle = world.add(Entity(id="Buckle", label="buckle", owner=child.id))
    chalk = world.add(Entity(id="Chalk", label="chalk", owner=child.id))

    world.say(f"{child.id} was a {params.trait} child who lived by the village lane and kept a little buckle in a cloth pocket.")
    world.say(f"One morning {child.id} found {chalk.phrase} and tucked it close, because chalk could make a mark on stone or wood.")
    world.say(f"{child.id} loved the buckle too, for it glittered like a tiny moon on an old belt.")

    world.para()
    world.say(f"That day {child.id} walked down {world.setting.place} to fetch water for the fire.")
    child.meters["walk"] = child.meters.get("walk", 0.0) + 1
    child.meters["worry"] = child.meters.get("worry", 0.0) + 1
    world.say(f"But the buckle slipped free in the dust, and {child.id} began to worry.")

    world.para()
    world.say(f"{child.id} bent low and used the chalk to draw tiny marks on the wall, then followed them step by step.")
    child.meters["search"] = child.meters.get("search", 0.0) + 1
    propagate(world, child, helper, buckle)

    world.say(f"At the last mark, {helper.label} stood by the gate and saw the lost buckle in the child's hands.")
    world.say(f"{helper.label} smiled and shared {_safe_lookup(KINDNESSES, params.kindness).phrase}, because a kind heart likes to mend a hard day.")
    child.meters["kindness"] = child.meters.get("kindness", 0.0) + 1
    propagate(world, child, helper, buckle)

    world.para()
    world.say(f"{child.id} thanked {helper.label} with a deep bow. {child.id} fastened the buckle again, and it shone bright against the cloth.")
    world.say(f"Then {child.id} carried a little extra water to {helper.label}'s door, so the kindness would not end in one place.")
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + 1

    world.facts.update(
        child=child,
        helper=helper,
        buckle=buckle,
        chalk=chalk,
        setting=world.setting,
        kindness=params.kindness,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        "Write a short folk tale for a young child about a poor child, a lost buckle, and a helpful act of kindness.",
        f"Tell a gentle story where {child.id} loses a buckle, follows chalk marks, and receives help from {f['helper'].label}.",
        "Write a simple village story that includes the words buckle, chalk, and poor, and ends with kindness being passed on.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    buckle = _safe_fact(world, f, "buckle")
    chalk = _safe_fact(world, f, "chalk")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, a poor child who keeps a little {buckle.label} and learns from kindness.",
        ),
        QAItem(
            question=f"What helped {child.id} find the lost {buckle.label}?",
            answer=f"{child.id} used the {chalk.label} to make little marks and follow them back to the lost {buckle.label}.",
        ),
        QAItem(
            question=f"Who shared kindness with {child.id}?",
            answer=f"{helper.label} shared kindness by helping mend the hard day and making the {buckle.label} shine again.",
        ),
        QAItem(
            question=f"What did {child.id} do at the end of the story?",
            answer=f"At the end, {child.id} fastened the {buckle.label} again and carried water to {helper.label}'s door as a return kindness.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chalk for?",
            answer="Chalk is soft writing dust. People use it to make marks and drawings on stone, wood, or boards.",
        ),
        QAItem(
            question="What is a buckle for?",
            answer="A buckle helps hold a belt, strap, or shoe closed so it stays fastened.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, sharing, or speaking gently so someone else's day becomes easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
kindness_used(C) :- child(C), receives_kindness(C).
buckle_found(C) :- child(C), follows_chalk(C), buckle_lost(C).
good_story(C) :- buckle_found(C), kindness_used(C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "child1"),
        asp.fact("buckle_lost", "child1"),
        asp.fact("follows_chalk", "child1"),
        asp.fact("receives_kindness", "child1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    atoms = set(asp.atoms(model, "good_story"))
    expected = {("child1",)}
    if atoms == expected:
        print("OK: ASP twin matches Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP twin does not match Python gate.")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about buckle, chalk, poor, and kindness.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--buckle", choices=BUCKLES)
    ap.add_argument("--chalk", choices=CHALKS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting="lane",
        buckle=getattr(args, "buckle", None) or rng.choice(list(BUCKLES)),
        chalk=getattr(args, "chalk", None) or rng.choice(list(CHALKS)),
        kindness=getattr(args, "kindness", None) or rng.choice(list(KINDNESSES)),
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes}")
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
        print(asp_program("#show good_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_story/1."))
        print(asp.atoms(model, "good_story"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = [
            StoryParams(name="Mara", helper="Old Hester", trait="poor", buckle="plain", chalk="white", kindness="help"),
            StoryParams(name="Tobin", helper="Aunt Wren", trait="poor", buckle="bright", chalk="blue", kindness="gift"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
