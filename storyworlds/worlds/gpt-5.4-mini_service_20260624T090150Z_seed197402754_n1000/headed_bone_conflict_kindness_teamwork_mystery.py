#!/usr/bin/env python3
"""
storyworlds/worlds/headed_bone_conflict_kindness_teamwork_mystery.py
====================================================================

A small mystery storyworld about a missing bone, a headed trip, and how
Conflict can turn into Kindness and Teamwork.

Premise:
- A child or animal heads to a place with an important bone.
- Something goes wrong: the bone is lost, suspected, or misplaced.
- The search creates Conflict, but a kind choice and teamwork solve the mystery.

This script models:
- physical meters: carrying, hiding, searching, distance, clue strength
- emotional memes: conflict, kindness, teamwork, worry, relief, curiosity

The prose is driven by state changes, not by a frozen template.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caretaking: object | None = None
    bone: object | None = None
    helper: object | None = None
    seeker: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type in {"dog", "cat", "animal"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    indoors: bool = False
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
class Clue:
    id: str
    label: str
    detail: str
    kind: str
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
class MysteryItem:
    id: str
    label: str
    phrase: str
    kind: str
    hidden_in: str
    clues: list[str] = field(default_factory=list)
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    seeker: str
    action: str
    item: str
    clue: str
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


SETTINGS = {
    "garden": Setting(place="the garden"),
    "yard": Setting(place="the back yard"),
    "shed": Setting(place="the shed", indoors=True),
    "porch": Setting(place="the porch"),
}

ACTIONS = {
    "headed": Action(
        id="headed",
        verb="head to the garden",
        gerund="heading to the garden",
        rush="hurry toward the gate",
        keyword="headed",
        tags={"headed", "search"},
    ),
    "search": Action(
        id="search",
        verb="look for the missing bone",
        gerund="searching for the missing bone",
        rush="search under the bushes",
        keyword="bone",
        tags={"bone", "search"},
    ),
}

MYSTERY_ITEMS = {
    "bone": MysteryItem(
        id="bone",
        label="bone",
        phrase="a smooth white bone",
        kind="bone",
        hidden_in="under the porch step",
        clues=["scratch", "pawprint"],
    ),
}

CLUES = {
    "scratch": Clue(
        id="scratch",
        label="scratch marks",
        detail="thin scratch marks near the dirt",
        kind="scratch",
    ),
    "pawprint": Clue(
        id="pawprint",
        label="pawprints",
        detail="small pawprints in the dust",
        kind="pawprints",
    ),
    "crumb": Clue(
        id="crumb",
        label="crumb trail",
        detail="a tiny trail of crumbs by the steps",
        kind="crumb",
    ),
}

CHAR_NAMES = ["Mia", "Noah", "Lena", "Owen", "Ivy", "Theo"]
DOG_NAMES = ["Scout", "Pip", "Milo", "Penny"]
TRAITS = ["curious", "gentle", "brave", "careful", "quiet"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.meters.get("lost", 0) < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] = e.memes.get("worry", 0) + 1
        e.memes["conflict"] = e.memes.get("conflict", 0) + 1
        out.append(f"{e.label_word.capitalize()} felt worried.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.memes.get("kindness", 0) < THRESHOLD:
            continue
        sig = ("kind", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["conflict"] = max(0.0, e.memes.get("conflict", 0) - 1)
        e.memes["relief"] = e.memes.get("relief", 0) + 1
        out.append(f"A kind choice helped calm the room.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = [e for e in world.entities.values() if e.kind == "character" and e.memes.get("helping", 0) >= THRESHOLD]
    if len(team) >= 2:
        sig = ("teamwork", tuple(sorted(e.id for e in team)))
        if sig not in world.fired:
            world.fired.add(sig)
            for e in team:
                e.memes["teamwork"] = e.memes.get("teamwork", 0) + 1
                e.memes["conflict"] = max(0.0, e.memes.get("conflict", 0) - 1)
            out.append("They worked together and the search became easier.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("kindness", _r_kindness), Rule("teamwork", _r_teamwork)]


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


def _seek(world: World, seeker: Entity, item: MysteryItem) -> None:
    seeker.meters["searching"] = seeker.meters.get("searching", 0) + 1
    world.say(f"{seeker.label_word.capitalize()} started searching for {item.label}.")
    world.say(f"{seeker.pronoun().capitalize()} looked around the {world.setting.place}.")

def _add_clue(world: World, clue: Clue) -> None:
    world.say(f"Then {clue.detail} caught their eye.")


def tell(setting: Setting, seeker_type: str, item: MysteryItem, name: str, clue: Clue, trait: str) -> World:
    world = World(setting)
    seeker = world.add(Entity(
        id=name,
        kind="character",
        type=seeker_type,
        label=name,
        meters={"searching": 0, "lost": 0},
        memes={"curiosity": 1, "conflict": 0, "kindness": 0, "helping": 0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="dog" if seeker_type != "dog" else "girl",
        label="Scout" if seeker_type != "dog" else "Mia",
        meters={"searching": 0},
        memes={"kindness": 1, "helping": 1},
    ))
    bone = world.add(Entity(
        id=item.id,
        type=item.kind,
        label=item.label,
        phrase=item.phrase,
        hidden_in=item.hidden_in,
        owner=seeker.id,
        caretaking=seeker.id,
    ))

    world.say(f"{seeker.label_word.capitalize()} was a {trait} {seeker_type} who had headed to {setting.place}.")
    world.say(f"{seeker.pronoun().capitalize()} wanted to keep {bone.phrase} safe.")
    world.para()

    _seek(world, seeker, item)
    world.say(f"At first, the bone was gone.")
    seeker.meters["lost"] = 1
    propagate(world)
    world.say(f"That made {seeker.pronoun('object')} feel stuck between Conflict and worry.")

    world.para()
    world.say(f"Then {helper.label_word} came close and chose Kindness over blame.")
    helper.memes["helping"] = 1
    seeker.memes["kindness"] = 1
    propagate(world)
    _add_clue(world, clue)
    world.say(f"{helper.label_word.capitalize()} and {seeker.label_word} followed the clue together.")
    world.say(f"They found {bone.phrase} tucked {item.hidden_in}.")

    bone.hidden_in = "with the seeker"
    seeker.meters["lost"] = 0
    seeker.memes["conflict"] = 0
    seeker.memes["teamwork"] = 1
    world.say(f"In the end, Teamwork solved the mystery, and the bone was safe again.")

    world.facts.update(
        seeker=seeker,
        helper=helper,
        item=bone,
        clue=clue,
        trait=trait,
        setting=setting,
    )
    return world


SETTINGS_REGISTRY = SETTINGS
ACTIONS_REGISTRY = ACTIONS
ITEMS_REGISTRY = MYSTERY_ITEMS
CLUES_REGISTRY = CLUES


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS_REGISTRY:
        for seeker in ["girl", "boy", "dog"]:
            for item in ITEMS_REGISTRY:
                for clue in CLUES_REGISTRY:
                    combos.append((place, seeker, item))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = _safe_fact(world, f, "seeker")
    item = _safe_fact(world, f, "item")
    return [
        f'Write a gentle mystery story for a small child about {seeker.label_word} who headed to {world.setting.place} and lost {item.label}.',
        f"Tell a short story where Conflict turns into Kindness and Teamwork while someone searches for {item.label}.",
        f'Write a simple mystery that includes the words "headed" and "{item.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = _safe_fact(world, f, "seeker")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item")
    clue = _safe_fact(world, f, "clue")
    trait = _safe_fact(world, f, "trait")
    qa = [
        QAItem(
            question=f"What did {seeker.label_word} head to {world.setting.place} to do?",
            answer=f"{seeker.label_word.capitalize()} headed to {world.setting.place} to look for {item.phrase}.",
        ),
        QAItem(
            question=f"Why was there Conflict in the story?",
            answer=f"There was Conflict because {item.label} went missing, and that made {seeker.label_word} worried and unsure where to look.",
        ),
        QAItem(
            question=f"Who showed Kindness first?",
            answer=f"{helper.label_word.capitalize()} showed Kindness first by coming close and helping with the search.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue was {clue.detail}, which led them toward {item.hidden_in}.",
        ),
        QAItem(
            question=f"How did Teamwork change the ending for {seeker.label_word}?",
            answer=f"Teamwork let {seeker.label_word} and {helper.label_word} search together, and that helped them find {item.phrase} safely.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of helpful information that can lead someone to the answer.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to do something.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What can a bone be in a story?",
            answer="A bone can be a pet's treasure or a missing object that characters need to find.",
        ),
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS_REGISTRY:
        lines.append(asp.fact("place", pid))
    for aid in ACTIONS_REGISTRY:
        act = ACTIONS_REGISTRY[aid]
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("keyword", aid, act.keyword))
    for iid, item in ITEMS_REGISTRY.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("kind", iid, item.kind))
        for c in item.clues:
            lines.append(asp.fact("has_clue", iid, c))
    for cid in CLUES_REGISTRY:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


ASP_RULES = r"""
% If someone heads somewhere and the bone is missing, there is a mystery.
mystery(P, I) :- place(P), item(I).

% Conflict appears when the item is missing.
conflict(P, I) :- mystery(P, I).

% Kindness can be chosen once a helper helps.
kindness(P, I) :- conflict(P, I).

% Teamwork is achieved when kindness and a clue are both present.
teamwork(P, I) :- kindness(P, I), has_clue(I, _).

#show mystery/2.
#show conflict/2.
#show kindness/2.
#show teamwork/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {(p, i) for p, _, i in valid_combos()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: headed, bone, Conflict, Kindness, Teamwork, and a small mystery."
    )
    ap.add_argument("--place", choices=SETTINGS_REGISTRY)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "dog"])
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS_REGISTRY))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy", "dog"])
    name = getattr(args, "name", None) or rng.choice(DOG_NAMES if gender == "dog" else CHAR_NAMES)
    action = "headed"
    item = "bone"
    clue = rng.choice(list(CLUES_REGISTRY))
    return StoryParams(place=place, seeker=gender, action=action, item=item, clue=clue, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS_REGISTRY[params.place],
        params.seeker,
        _safe_lookup(MYSTERY_ITEMS, params.item),
        params.name or ("Scout" if params.seeker == "dog" else "Mia"),
        CLUES_REGISTRY[params.clue],
        rng_trait(),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def rng_trait() -> str:
    return random.choice(TRAITS)


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
    StoryParams(place="garden", seeker="girl", action="headed", item="bone", clue="pawprint", seed=1),
    StoryParams(place="yard", seeker="boy", action="headed", item="bone", clue="scratch", seed=2),
    StoryParams(place="porch", seeker="dog", action="headed", item="bone", clue="crumb", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery/2.\n#show conflict/2.\n#show kindness/2.\n#show teamwork/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery/2.\n#show conflict/2.\n#show kindness/2.\n#show teamwork/2."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
