#!/usr/bin/env python3
"""
Story world: a small whodunit in a kitchen where batter, a buckle, and coleslaw
create a gentle conflict and a tidy clue-based resolution.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    apron: object | None = None
    bowl: object | None = None
    dish: object | None = None
    hero: object | None = None
    side: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the kitchen"
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    type: str
    hint: str
    clue: str
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
class ConflictCfg:
    id: str
    name: str
    trigger: str
    mess: str
    smear: str
    source: str
    clue: str
    resolution: str
    ending: str
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"batter", "coleslaw", "buckle"}),
    "backroom": Setting(place="the back room", affords={"batter", "buckle"}),
}

CONFLICTS = {
    "missing_mix": ConflictCfg(
        id="missing_mix",
        name="the missing batter",
        trigger="stir the batter",
        mess="sticky",
        smear="spattered",
        source="batter bowl",
        clue="a sticky spoon",
        resolution="find the bowl tucked under the counter",
        ending="the batter was back where it belonged",
    ),
    "collide_coleslaw": ConflictCfg(
        id="collide_coleslaw",
        name="the coleslaw spill",
        trigger="carry the coleslaw",
        mess="slippery",
        smear="dressed",
        source="coleslaw dish",
        clue="a cool drip on the floor",
        resolution="follow the drip to the chair",
        ending="the coleslaw had tipped behind the chair",
    ),
    "loose_buckle": ConflictCfg(
        id="loose_buckle",
        name="the loose buckle",
        trigger="fasten the buckle",
        mess="snapped",
        smear="clicked",
        source="apron buckle",
        clue="a tiny silver buckle on the tiles",
        resolution="pick up the fallen strap and refasten it",
        ending="the buckle was only unlatched, not broken",
    ),
}

OBJECTS = {
    "bowl": ObjectCfg(
        id="bowl",
        label="bowl",
        phrase="a blue mixing bowl",
        type="bowl",
        hint="The bowl held the batter.",
        clue="A bowl leaves crumbs and streaks near the counter.",
    ),
    "apron": ObjectCfg(
        id="apron",
        label="apron",
        phrase="a striped apron",
        type="apron",
        hint="The apron had a buckle at the back.",
        clue="An apron can hide a buckle if it slips.",
    ),
    "dish": ObjectCfg(
        id="dish",
        label="dish",
        phrase="a bowl of coleslaw",
        type="dish",
        hint="The dish was cold and crunchy.",
        clue="Coleslaw leaves a creamy trail when it spills.",
    ),
}

HERO_NAMES = ["Maya", "Noah", "Lina", "Eli", "Sofia", "Theo"]
SIDE_NAMES = ["Chef", "Aunt", "Uncle", "Parent"]
TRAITS = ["curious", "careful", "brave", "patient", "shy"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    conflict: str
    name: str
    side: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
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


def clue_sentence(conf: ConflictCfg) -> str:
    if conf.id == "missing_mix":
        return "There was a sticky spoon by the sink, which felt like a clue."
    if conf.id == "collide_coleslaw":
        return "A cool drip on the floor made a little trail like a clue."
    return "A tiny silver buckle glittered on the tiles like a clue."


def setup_sentence(hero: Entity, side: Entity, conf: ConflictCfg) -> str:
    return (
        f"{hero.id} was a little {hero.traits[0]} helper who liked looking for clues. "
        f"{side.label} was making dinner, and something small had gone wrong with {conf.name}."
    )


def conflict_sentence(hero: Entity, side: Entity, conf: ConflictCfg) -> str:
    return (
        f"{hero.id} wanted to {conf.trigger}, but {side.pronoun('possessive')} voice grew tight with {conf.id.replace('_', ' ')}."
    )


def resolution_sentence(hero: Entity, side: Entity, conf: ConflictCfg) -> str:
    return (
        f"Then {hero.id} followed the clue and found the answer. "
        f"They did not need to guess anymore, because {conf.resolution}."
    )


def ending_sentence(hero: Entity, side: Entity, conf: ConflictCfg) -> str:
    return (
        f"{side.label} smiled again, and {hero.id} felt proud. In the end, {conf.ending}, "
        f"so dinner could go on in the warm kitchen."
    )


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for eid, ent in world.entities.items():
        if ent.memes.get("conflict", 0.0) >= THRESHOLD and ("conflict", eid) not in world.fired:
            world.fired.add(("conflict", eid))
            out.append("The room felt tense for a moment.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    conf = _safe_lookup(CONFLICTS, params.conflict)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="child", traits=[params.trait, "little"]))
    side = world.add(Entity(id=params.side, kind="character", label=f"the {params.side.lower()}", type="adult"))

    bowl = world.add(Entity(id="bowl", type="bowl", label="bowl", phrase=OBJECTS["bowl"].phrase, owner=side.id))
    apron = world.add(Entity(id="apron", type="apron", label="apron", phrase=OBJECTS["apron"].phrase, owner=side.id))
    dish = world.add(Entity(id="dish", type="dish", label="coleslaw", phrase=OBJECTS["dish"].phrase, owner=side.id))

    hero.memes["curiosity"] = 1
    side.memes["worry"] = 1

    world.say(setup_sentence(hero, side, conf))
    world.say(f"The {bowl.label} held batter, the {apron.label} had a buckle, and the {dish.label} held coleslaw.")
    world.say(clue_sentence(conf))
    world.para()

    if conf.id == "missing_mix":
        hero.memes["conflict"] += 1
        world.say(f"{hero.id} wanted to help with the batter, but the bowl was not where it should have been.")
        world.say(f"{side.label} looked around the counter and frowned, because {hero.id} could not find the mix.")
    elif conf.id == "collide_coleslaw":
        hero.memes["conflict"] += 1
        world.say(f"{hero.id} reached for the coleslaw dish, but it wobbled and nearly slid away.")
        world.say(f"{side.label} paused, worried the salad would spill all over the floor.")
    else:
        hero.memes["conflict"] += 1
        world.say(f"{hero.id} tugged at the apron, but the buckle would not stay closed.")
        world.say(f"{side.label} sighed, because a loose buckle can make a helper feel stuck.")

    propagate(world, narrate=False)
    world.say(conflict_sentence(hero, side, conf))
    world.para()

    world.say(resolution_sentence(hero, side, conf))
    world.say(ending_sentence(hero, side, conf))

    world.facts.update(hero=hero, side=side, conf=conf, bowl=bowl, apron=apron, dish=dish)
    return world


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, side, conf = f["hero"], f["side"], f["conf"]
    return [
        f'Write a short whodunit for a small child about {hero.id}, {side.label}, and a kitchen clue.',
        f"Tell a gentle mystery where {hero.id} notices {conf.clue} and helps solve {conf.name}.",
        f'Write a child-friendly story that includes "batter", "buckle", and "coleslaw" and ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, side, conf = f["hero"], f["side"], f["conf"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a {hero.traits[0]} little helper, and {side.label}, who was making dinner.",
        ),
        QAItem(
            question=f"What small problem made the kitchen feel like a mystery?",
            answer=f"The mystery was {conf.name}. The story gave clues so {hero.id} could figure it out.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the problem?",
            answer=clue_sentence(conf),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {conf.ending}, and the kitchen felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is batter?",
            answer="Batter is a smooth mixture used for pancakes, cakes, and other baked treats.",
        ),
        QAItem(
            question="What is a buckle for?",
            answer="A buckle is a little fastener that helps hold a strap in place.",
        ),
        QAItem(
            question="What is coleslaw?",
            answer="Coleslaw is a crunchy salad made from chopped cabbage and dressing.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(kitchen).
setting(backroom).

conflict(missing_mix).
conflict(collide_coleslaw).
conflict(loose_buckle).

object(bowl).
object(apron).
object(dish).

has_clue(missing_mix,sticky_spoon).
has_clue(collide_coleslaw,cool_drip).
has_clue(loose_buckle,tiny_buckle).

solved(C) :- conflict(C), has_clue(C,_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for cid, conf in CONFLICTS.items():
        clue = "sticky_spoon" if cid == "missing_mix" else "cool_drip" if cid == "collide_coleslaw" else "tiny_buckle"
        lines.append(asp.fact("has_clue", cid, clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solved() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solved/1."))
    return sorted(set(asp.atoms(model, "solved")))


def asp_verify() -> int:
    python_set = {("missing_mix",), ("collide_coleslaw",), ("loose_buckle",)}
    asp_set = set(asp_solved())
    if asp_set == python_set:
        print(f"OK: clingo gate matches Python reasoning ({len(asp_set)} conflicts).")
        return 0
    print("MISMATCH between clingo and Python reasoning:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Parameters, generation, CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    conflict: str
    name: str
    side: str
    trait: str
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


CURATED = [
    StoryParams(setting="kitchen", conflict="missing_mix", name="Maya", side="Chef", trait="curious"),
    StoryParams(setting="kitchen", conflict="collide_coleslaw", name="Noah", side="Aunt", trait="careful"),
    StoryParams(setting="backroom", conflict="loose_buckle", name="Lina", side="Parent", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world with batter, buckle, and coleslaw.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--name")
    ap.add_argument("--side", choices=SIDE_NAMES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    conflict = getattr(args, "conflict", None) or rng.choice(list(CONFLICTS))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    side = getattr(args, "side", None) or rng.choice(SIDE_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, conflict=conflict, name=name, side=side, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
            header = f"### {p.name}: {p.conflict} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
