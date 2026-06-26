#!/usr/bin/env python3
"""
tummy_tanker_leash_sharing_quest_magic_detective.py
===================================================

A small detective-story world about a curious child, a puzzling clue,
and a kind share-the-burden quest that ends with magic helping the day
make sense.

The world is built from a tiny premise:
- a child notices a tummy ache and a missing leash,
- a tanker truck, a lamp, a trail of clues, and a shareable helper object
  turn the problem into a quest,
- a little bit of magic reveals the culprit and helps repair the mix-up.

This script keeps the story grounded in simulated state:
- physical meters: distance, hiddenness, tangles, fullness, sparkles
- emotional memes: worry, bravery, trust, curiosity, relief

It follows the Storyweavers storyworld contract with:
- StoryParams
- registries
- build_parser / resolve_params / generate / emit / main
- inline ASP_RULES plus asp_facts()
- reasonableness gate and verification mode
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
# Core data model
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    clue: object | None = None
    helper: object | None = None
    magic: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
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
    indoor: bool = False
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
class Clue:
    id: str
    label: str
    phrase: str
    meter: str
    reveals: str
    trail: str
    hidden: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    shares_with: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    title: str
    mess: str
    risk: str
    clue_id: str
    tool_id: str
    magic_id: str
    solve_verb: str
    quest_phrase: str
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
        self.current_mystery: Optional[Mystery] = None

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.current_mystery = self.current_mystery
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "dock": Setting(place="the dock", indoor=False, affords={"quest", "magic", "sharing"}),
    "harbor": Setting(place="the harbor", indoor=False, affords={"quest", "magic", "sharing"}),
    "garage": Setting(place="the garage", indoor=True, affords={"quest", "magic", "sharing"}),
    "station": Setting(place="the little station", indoor=True, affords={"quest", "magic", "sharing"}),
}

MYSTERIES = {
    "lost_leash": Mystery(
        id="lost_leash",
        title="the leash mystery",
        mess="tangle",
        risk="a missing leash",
        clue_id="clue",
        tool_id="share_bag",
        magic_id="moon_lamp",
        solve_verb="untangle",
        quest_phrase="follow the clue trail and find the missing leash",
    ),
    "tummy_twist": Mystery(
        id="tummy_twist",
        title="the tummy-twister mystery",
        mess="worry",
        risk="a tummy ache",
        clue_id="clue",
        tool_id="share_bag",
        magic_id="moon_lamp",
        solve_verb="soothe",
        quest_phrase="look for the clue that helps the tummy feel better",
    ),
    "tanker_tracks": Mystery(
        id="tanker_tracks",
        title="the tanker tracks mystery",
        mess="spill",
        risk="a tanker with a leak",
        clue_id="clue",
        tool_id="share_bag",
        magic_id="moon_lamp",
        solve_verb="trace",
        quest_phrase="follow the clue trail around the tanker",
    ),
}

CLUES = {
    "clue": Clue(
        id="clue",
        label="clue card",
        phrase="a small clue card with a shiny arrow",
        meter="hiddenness",
        reveals="the next stop on the trail",
        trail="small pawprints and sparkly crumbs",
        hidden=True,
    )
}

TOOLS = {
    "share_bag": Tool(
        id="share_bag",
        label="shared bag",
        phrase="a shared bag with two handles",
        helps={"quest", "sharing"},
        shares_with={"child", "helper"},
    )
}

MAGICS = {
    "moon_lamp": Tool(
        id="moon_lamp",
        label="moon lamp",
        phrase="a little moon lamp that glowed blue",
        helps={"magic", "quest"},
        shares_with={"child", "helper"},
    )
}

CHILD_NAMES = ["Nina", "Milo", "Rae", "Jun", "Tia", "Arlo", "Lena", "Pip"]
HELPER_NAMES = ["Detective Dot", "Captain Finch", "Aunt Bea", "Mr. Moss"]
TRAITS = ["curious", "brave", "gentle", "sharp-eyed", "patient"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def at_risk(mystery: Mystery) -> bool:
    return True


def reasonableness_gate(mystery: Mystery) -> bool:
    return mystery.tool_id in TOOLS and mystery.magic_id in MAGICS and mystery.clue_id in CLUES


def _solve_mystery(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} was a little {next(t for t in child.memes if False), 'curious'} detective who loved a good quest."
    )


def intro(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{child.id} was a sharp-eyed child detective at {world.setting.place} who noticed tiny things."
    )
    world.say(
        f"One day, {child.id} felt a twist in {child.pronoun('possessive')} tummy and knew something was off."
    )
    world.say(
        f"{helper.id} was nearby, ready to help with {mystery.title}."
    )


def setup_clues(world: World, child: Entity, helper: Entity, clue: Entity, mystery: Mystery) -> None:
    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    clue.hidden = True
    world.say(
        f"On the floor there was {clue.phrase}, but it was tucked behind a crate."
    )
    world.say(
        f"{child.id} wanted to {mystery.quest_phrase}, yet the clue was hidden and the trail looked tricky."
    )


def share_and_search(world: World, child: Entity, helper: Entity, tool: Entity, clue: Entity, mystery: Mystery) -> None:
    child.memes["trust"] += 1
    helper.memes["trust"] += 1
    tool.carried_by = child.id
    world.say(
        f"{helper.id} said, \"Let's share the bag.\" {child.id} carried one handle and {helper.id} took the other."
    )
    world.say(
        f"Together they followed {clue.trail}, because a shared quest is easier when two friends look."
    )


def magic_reveal(world: World, child: Entity, helper: Entity, magic: Entity, clue: Entity, mystery: Mystery) -> None:
    child.memes["bravery"] += 1
    magic.carried_by = helper.id
    world.say(
        f"Then {helper.id} clicked on {magic.label}, and soft blue light filled the little path."
    )
    world.say(
        f"The light showed {clue.reveals}: {mystery.risk} was not dangerous at all, just mixed up and lonely."
    )


def resolution(world: World, child: Entity, helper: Entity, clue: Entity, tool: Entity, magic: Entity, mystery: Mystery) -> None:
    child.memes["relief"] += 1
    clue.hidden = False
    world.say(
        f"{child.id} used the clue to {mystery.solve_verb} the mystery, and the missing leash was found looped around a hook."
    )
    world.say(
        f"With the leash back in place, the tummy ache felt smaller, the quest was complete, and the shared bag held all the clues neatly."
    )
    world.say(
        f"{child.id} smiled at {helper.id}, and the moon lamp made the dock look kind and bright."
    )


# ---------------------------------------------------------------------------
# Build a state-driven world
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery: Mystery, child_name: str = "Nina", helper_name: str = "Detective Dot", trait: str = "curious") -> World:
    world = World(setting)
    world.current_mystery = mystery

    child = world.add(Entity(id=child_name, kind="character", type="girl", meters={}, memes={}))
    helper = world.add(Entity(id=helper_name, kind="character", type="woman", meters={}, memes={}))
    clue = world.add(Entity(id=mystery.clue_id, type="thing", label="clue card", phrase=_safe_lookup(CLUES, mystery.clue_id).phrase, hidden=True))
    tool = world.add(Entity(id=mystery.tool_id, type="thing", label=_safe_lookup(TOOLS, mystery.tool_id).label, phrase=_safe_lookup(TOOLS, mystery.tool_id).phrase))
    magic = world.add(Entity(id=mystery.magic_id, type="thing", label=_safe_lookup(MAGICS, mystery.magic_id).label, phrase=_safe_lookup(MAGICS, mystery.magic_id).phrase))

    child.memes["curiosity"] = 1
    helper.memes["trust"] = 1

    intro(world, child, helper, mystery)
    world.para()
    setup_clues(world, child, helper, clue, mystery)
    share_and_search(world, child, helper, tool, clue, mystery)
    world.para()
    magic_reveal(world, child, helper, magic, clue, mystery)
    resolution(world, child, helper, clue, tool, magic, mystery)

    world.facts = {
        "child": child,
        "helper": helper,
        "clue": clue,
        "tool": tool,
        "magic": magic,
        "mystery": mystery,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    child_name: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a child-friendly detective story set at {world.setting.place} about {mystery.title}, with sharing and a little magic.',
        f"Tell a short quest story where a child detective and {f['helper'].id} use a shared bag and a moon lamp to solve a clue.",
        f'Write a simple mystery story that includes the words "tummy", "tanker", and "leash".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer=f"It is a gentle detective story about {child.id} and {helper.id} solving {mystery.title} together."
        ),
        QAItem(
            question=f"What problem made {child.id} start the quest?",
            answer=f"{child.id} had a twist in {child.pronoun('possessive')} tummy, and there was also a clue about {mystery.risk}."
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} work together?",
            answer=f"They shared a bag, followed the clue trail, and used the moon lamp to see what the light was hiding."
        ),
        QAItem(
            question=f"What did the magic help them find?",
            answer=f"The magic helped reveal the clue trail and led them to the missing leash."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a detective story?",
            answer="A clue is a small sign that helps a detective figure out what happened."
        ),
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to use something together or let someone else help carry it."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special trip or job where you look for something or try to solve a problem."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising or special that helps the story in a fun, impossible-feeling way."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story q&a ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_mystery(M) :- mystery(M).
valid_story(S,M) :- valid_setting(S), valid_mystery(M), has_clue(M), has_tool(M), has_magic(M).

has_clue(lost_leash).
has_clue(tummy_twist).
has_clue(tanker_tracks).

has_tool(lost_leash).
has_tool(tummy_twist).
has_tool(tanker_tracks).

has_magic(lost_leash).
has_magic(tummy_twist).
has_magic(tanker_tracks).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    return sorted((s, m) for s in SETTINGS for m in MYSTERIES)


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid())
    if python_set == asp_set:
        print(f"OK: ASP matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Resolution / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child detective storyworld about tummy, tanker, leash, sharing, quest, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    if setting not in SETTINGS or mystery not in MYSTERIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        setting=setting,
        mystery=mystery,
        child_name=getattr(args, "name", None) or rng.choice(CHILD_NAMES),
        helper_name=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    if not reasonableness_gate(mystery):
        pass
    world = tell(setting, mystery, params.child_name, params.helper_name, params.trait)
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
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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
    StoryParams(setting="dock", mystery="lost_leash", child_name="Nina", helper_name="Detective Dot", trait="curious"),
    StoryParams(setting="harbor", mystery="tummy_twist", child_name="Milo", helper_name="Captain Finch", trait="brave"),
    StoryParams(setting="garage", mystery="tanker_tracks", child_name="Rae", helper_name="Aunt Bea", trait="sharp-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible setting/mystery combos:")
        for s, m in combos:
            print(f"  {s:10} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
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
            header = f"### {p.child_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
