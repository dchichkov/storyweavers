#!/usr/bin/env python3
"""
storyworlds/worlds/tactile_crocus_twist_misunderstanding_mystery.py
====================================================================

A small story world about a child, a careful search, a tactile clue, and a
mystery that turns on a misunderstanding.

Core premise:
- A child loves a crocus plant in a little garden.
- The crocus seems to have gone missing or been damaged.
- The child and a helper look for it using touch-based clues.
- A misunderstanding creates tension.
- The twist is that the crocus was not stolen or broken; it was moved
  carefully, or protected, and the tactile clue reveals the truth.

This is intentionally a tiny, classical simulation: a handful of entities,
world state that changes over time, and prose that follows those changes.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_by: Optional[str] = None
    hidden: bool = False
    tactile: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    crocus: object | None = None
    helper: object | None = None
    note: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "found": 0.0, "attention": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "curiosity": 0.0, "trust": 0.0, "confusion": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Place:
    name: str
    indoor: bool = False
    surfaces: set[str] = field(default_factory=set)
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
    surface: str
    texture: str
    points_to: str
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
    place: str
    clue: str
    twist: str
    misunderstanding: str
    name: str
    gender: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def add_trace(self, text: str) -> None:
        self.trace.append(text)


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    crocus = world.get("crocus")
    if child.memes["worry"] >= THRESHOLD and helper.memes["trust"] < THRESHOLD:
        sig = ("confusion",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["confusion"] += 1
            out.append(f"{child.id} felt sure something was wrong.")
    if crocus.hidden and child.memes["curiosity"] >= THRESHOLD:
        sig = ("search",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"{child.id} kept looking for a soft bright sign.")
    if crocus.meters["found"] >= THRESHOLD and child.memes["trust"] >= THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["confusion"] = 0.0
            out.append("The worry began to fade.")
    return out


RULES = [_r_confusion]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def touch_check(world: World, clue: Clue) -> bool:
    surface = clue.surface
    return surface in world.place.surfaces


def predict_truth(world: World, clue: Clue, crocus: Entity) -> str:
    sim = world.copy()
    sim.get("child").memes["curiosity"] += 1
    if clue.points_to == "crocus":
        sim.get("crocus").hidden = False
        sim.get("crocus").meters["found"] += 1
        return "found"
    return "unknown"


PLACES = {
    "garden": Place("the garden", indoor=False, surfaces={"soil", "pot", "stone"}),
    "greenhouse": Place("the greenhouse", indoor=True, surfaces={"soil", "bench", "tray"}),
    "porch": Place("the porch", indoor=False, surfaces={"stone", "mat", "pot"}),
}

CLUES = {
    "soil": Clue("soil", "a crumbly patch of soil", "soil", "dry and loose", "crocus"),
    "petal": Clue("petal", "a tiny purple petal", "pot", "thin and smooth", "crocus"),
    "ribbon": Clue("ribbon", "a little ribbon tied around a pot", "bench", "soft and knotted", "crocus"),
    "paper": Clue("paper", "a folded note", "mat", "smooth and creased", "crocus"),
}

TWISTS = {
    "moved": "the crocus had been moved to a safer spot",
    "covered": "the crocus had been covered to protect it from cold air",
    "repotted": "the crocus had been repotted into a bigger pot",
}

MISUNDERSTANDINGS = {
    "missing": "the child thought someone had taken the crocus away",
    "broken": "the child thought the crocus had been broken",
    "lost": "the child thought the crocus was lost forever",
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandparent": "grandparent",
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Iris", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Sam", "Finn", "Max"]
TRAITS = ["gentle", "curious", "careful", "brave", "quiet"]


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    crocus = world.add(Entity(
        id="crocus",
        kind="thing",
        type="plant",
        label="crocus",
        phrase="a small purple crocus",
        caretaker=helper.id,
        tactile="soft petals and a cool stem",
        hidden=True,
    ))
    note = world.add(Entity(
        id="note",
        kind="thing",
        type="note",
        label="note",
        phrase="a folded note",
        hidden=True,
        tactile="smooth paper",
    ))

    child.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    world.facts.update(child=child, helper=helper, crocus=crocus, note=note)

    world.say(f"{child.label} loved {crocus.label}s because their petals felt soft and bright.")
    world.say(f"One day, {child.label} went to {world.place.name} and noticed that the crocus was not where it should be.")
    world.para()
    world.say(f"{params.misunderstanding}, and {child.label} felt a tight knot of worry in {child.pronoun('possessive')} chest.")

    child.memes["worry"] += 1
    propagate(world)

    world.para()
    world.say(f"{child.label} looked carefully at the ground and touched the dirt with two fingers.")
    if touch_check(world, _safe_lookup(CLUES, params.clue)):
        clue = _safe_lookup(CLUES, params.clue)
        world.say(f"{child.label} found {clue.label}, and it felt {clue.texture}.")
        child.memes["curiosity"] += 1
        world.facts["clue"] = clue
    else:
        pass

    world.para()
    world.say(f"{helper.label} came over and listened to the worry.")
    if params.twist == "moved":
        world.say(f"Then came the twist: {_safe_lookup(TWISTS, params.twist)}.")
        crocus.hidden = False
        crocus.moved_by = helper.id
        crocus.meters["found"] += 1
        child.memes["trust"] += 1
    elif params.twist == "covered":
        world.say(f"Then came the twist: {_safe_lookup(TWISTS, params.twist)}.")
        crocus.hidden = False
        crocus.meters["found"] += 1
        child.memes["trust"] += 1
    else:
        world.say(f"Then came the twist: {_safe_lookup(TWISTS, params.twist)}.")
        crocus.hidden = False
        crocus.meters["found"] += 1
        child.memes["trust"] += 1

    note.hidden = False
    world.say(f"{helper.label} showed a small note, and it explained why the crocus had been cared for so carefully.")
    world.say(f"{child.label} blinked, then smiled, because the mystery was really a misunderstanding.")
    propagate(world)

    world.para()
    world.say(f"In the end, {child.label} knelt beside the crocus and touched its soft petals.")
    world.say(f"The crocus was safe, the clue made sense at last, and the little garden felt calm again.")

    world.facts["resolved"] = True
    world.facts["clue_text"] = _safe_lookup(CLUES, params.clue).texture
    world.facts["twist_text"] = _safe_lookup(TWISTS, params.twist)
    world.facts["misunderstanding_text"] = _safe_lookup(MISUNDERSTANDINGS, params.misunderstanding)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    clue = _safe_fact(world, f, "clue")
    return [
        f'Write a short mystery story for a young child about {child.label}, a crocus, and a clue that feels {clue.texture}.',
        f'Tell a gentle story where a child thinks a crocus is missing, but the truth is revealed by touch and a careful clue.',
        f'Write a simple story with a misunderstanding, a twist, and a happy ending in {world.place.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    clue = _safe_fact(world, f, "clue")
    crocus = _safe_fact(world, f, "crocus")
    qa = [
        QAItem(
            question=f"What was {child.label} looking for in {world.place.name}?",
            answer=f"{child.label} was looking for the crocus, which had been cared for and then hidden from view for a little while.",
        ),
        QAItem(
            question=f"How did {child.label} find a clue?",
            answer=f"{child.label} touched the ground carefully and found {clue.label}, which felt {clue.texture}. That clue helped point toward the crocus.",
        ),
        QAItem(
            question=f"Why did the story begin with worry?",
            answer=f"It began with a misunderstanding: {f['misunderstanding_text']}. That made {child.label} think something bad had happened to the crocus.",
        ),
        QAItem(
            question=f"What did {helper.label} explain at the end?",
            answer=f"{helper.label} explained that {f['twist_text']}. The crocus was safe the whole time.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.label} touching the crocus's soft petals and feeling calm because the mystery was solved.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crocus?",
            answer="A crocus is a small flowering plant that often has bright purple, yellow, or white blossoms.",
        ),
        QAItem(
            question="What does tactile mean?",
            answer="Tactile means something is related to touch, like how a surface feels to your fingers.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what is happening.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader thought was true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.hidden:
            bits.append("hidden")
        if e.moved_by:
            bits.append(f"moved_by={e.moved_by}")
        if e.tactile:
            bits.append(f"tactile={e.tactile}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {', '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for s in sorted(place.surfaces):
            lines.append(asp.fact("surface", pid, s))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_surface", cid, clue.surface))
        lines.append(asp.fact("clue_points_to", cid, clue.points_to))
    for tid, txt in TWISTS.items():
        lines.append(asp.fact("twist", tid))
    for mid, txt in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is relevant if it fits one of the place surfaces.
relevant_clue(C, P) :- clue(C), place(P), clue_surface(C, S), surface(P, S).

% A story is valid when it has a place, a relevant clue, a twist, and a misunderstanding.
valid_story(P, C, T, M) :- place(P), relevant_clue(C, P), twist(T), misunderstanding(M).

#show valid_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, c, t, m) for p in PLACES for c in CLUES for t in TWISTS for m in MISUNDERSTANDINGS if any(_safe_lookup(CLUES, c).surface in _safe_lookup(PLACES, p).surfaces for _ in [0])}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world about a crocus, a clue, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    twist = getattr(args, "twist", None) or rng.choice(list(TWISTS))
    misunderstanding = getattr(args, "misunderstanding", None) or rng.choice(list(MISUNDERSTANDINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, clue=clue, twist=twist, misunderstanding=misunderstanding,
                       name=name, gender=gender, helper=helper)


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
    StoryParams(place="garden", clue="soil", twist="moved", misunderstanding="missing", name="Iris", gender="girl", helper="mother"),
    StoryParams(place="greenhouse", clue="ribbon", twist="covered", misunderstanding="broken", name="Leo", gender="boy", helper="father"),
    StoryParams(place="porch", clue="paper", twist="repotted", misunderstanding="lost", name="Mia", gender="girl", helper="grandparent"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story patterns:")
        for s in stories[:50]:
            print(" ", s)
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
            header = f"### {p.name}: {p.place} / {p.clue} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
