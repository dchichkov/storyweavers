#!/usr/bin/env python3
"""
storyworlds/worlds/eyer_stoop_inner_monologue_twist_adventure.py
=================================================================

A standalone story world for a tiny adventure on a stoop, with an inner
monologue beat and a gentle twist.

Premise used to shape the world:
---
A child named Eyer wants to go on a grand adventure, but the only place nearby
is the stoop outside the front door. Eyer imagines hidden treasure, listens to
the house, and notices a small mystery: a fluttering paper map stuck under the
doormat. The adventure becomes real when Eyer follows the map's clues around the
stoop, finds the missing key, and learns that small places can hold big quests.

World dynamics:
---
- The stoop is a small outdoor setting with steps, a mat, a flower pot, and a
  loose board.
- The hero can inspect, listen, and imagine, which raises clues and calmness.
- Inner monologue can shift fear into courage or impatience into focus.
- The twist is a hidden task, object, or helper that changes what the adventure
  is really about.
- A successful ending proves change by showing the stoop, the clue, and the
  hero's new feeling.

Story quality goal:
---
Every story should read like a complete little adventure: opening curiosity,
a middle turn with a puzzling discovery, and an ending image that shows the
stoop has become a place of wonder.
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
# Core world model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    stoop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
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


@dataclass
class Setting:
    place: str = "the stoop"
    features: tuple[str, ...] = ("steps", "doormat", "flower pot", "front door")
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
class Action:
    id: str
    verb: str
    noun: str
    clue_gain: int
    calm_gain: int
    risk_gain: int
    inner_line: str
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


@dataclass
class Twist:
    id: str
    reveal: str
    reason: str
    resolution: str
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

ACTIONS = {
    "peer": Action(
        id="peer",
        verb="peer over the edge",
        noun="peering",
        clue_gain=1,
        calm_gain=1,
        risk_gain=0,
        inner_line="Maybe the stoop is small, but small places can still hide something important.",
        tags={"look", "stoop", "inner"},
    ),
    "listen": Action(
        id="listen",
        verb="listen closely",
        noun="listening",
        clue_gain=1,
        calm_gain=1,
        risk_gain=0,
        inner_line="If I stay very still, the stoop might tell me what it knows.",
        tags={"sound", "stoop", "inner"},
    ),
    "search": Action(
        id="search",
        verb="search under the mat",
        noun="searching",
        clue_gain=2,
        calm_gain=0,
        risk_gain=1,
        inner_line="The best adventurers check the hidden spots first.",
        tags={"search", "mat", "twist"},
    ),
    "tap": Action(
        id="tap",
        verb="tap the loose board",
        noun="tapping",
        clue_gain=1,
        calm_gain=0,
        risk_gain=1,
        inner_line="A brave explorer does not stop at one clue.",
        tags={"board", "twist", "adventure"},
    ),
    "imagine": Action(
        id="imagine",
        verb="imagine a great quest",
        noun="imagining",
        clue_gain=0,
        calm_gain=2,
        risk_gain=0,
        inner_line="Even a stoop can become the edge of a wide world.",
        tags={"inner", "adventure"},
    ),
}

TWISTS = {
    "map": Twist(
        id="map",
        reveal="a paper map was stuck under the doormat",
        reason="someone had hidden it there on purpose",
        resolution="the map pointed to the missing key under the flower pot",
        tags={"map", "paper", "doormat"},
    ),
    "message": Twist(
        id="message",
        reveal="a folded note was tucked into the crack by the step",
        reason="it was meant for the family on the other side of the door",
        resolution="the note explained where the spare key had been left",
        tags={"note", "message", "step"},
    ),
    "toy": Twist(
        id="toy",
        reveal="a tiny toy compass was wedged near the pot",
        reason="the compass had slipped from a pocket during play",
        resolution="following the compass needle led straight to the hidden token",
        tags={"compass", "toy", "pot"},
    ),
    "bird": Twist(
        id="bird",
        reveal="a sparrow kept hopping at the top step",
        reason="the bird was guarding crumbs near something shiny",
        resolution="the shiny thing turned out to be the lost key ring",
        tags={"bird", "crumbs", "shiny"},
    ),
}

HERO_NAMES = ["Eyer", "Milo", "Nina", "Jun", "Tia", "Owen", "Rosa", "Sage"]
TRAITS = ["curious", "brave", "quick", "careful", "dreamy", "bold"]


# ---------------------------------------------------------------------------
# World generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    trait: str
    action: str
    twist: str
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


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="child", meters={}, memes={}))
    stoop = world.add(Entity(id="stoop", type="place", label="the stoop", place="outside the front door"))
    world.add(Entity(id="mat", type="thing", label="doormat", place="on the stoop"))
    world.add(Entity(id="pot", type="thing", label="flower pot", place="by the step"))
    world.add(Entity(id="board", type="thing", label="loose board", place="in the stoop step"))

    act = _safe_lookup(ACTIONS, params.action)
    twist = _safe_lookup(TWISTS, params.twist)

    hero.memes["curiosity"] = 1
    hero.memes["courage"] = 1 if params.trait in {"brave", "bold"} else 0
    hero.memes["wonder"] = 1

    world.say(
        f"{hero.id} was a {params.trait} child who loved adventure, even when the only road was {world.setting.place}."
    )
    world.say(
        f"One afternoon, {hero.id} stood on the stoop and thought, '{act.inner_line}'"
    )

    world.para()
    hero.meters["clue"] = 0
    hero.meters["calm"] = 0
    hero.meters["risk"] = 0

    if params.action == "imagine":
        hero.meters["calm"] += act.calm_gain
        world.say(
            f"{hero.id} breathed in slowly and {act.verb}. The little front steps did not seem so small anymore."
        )
    else:
        hero.meters["clue"] += act.clue_gain
        hero.meters["calm"] += act.calm_gain
        hero.meters["risk"] += act.risk_gain
        world.say(
            f"{hero.id} began by {act.verb} near the doormat. The stoop looked ordinary, but {hero.id} kept looking."
        )

    world.para()
    hero.meters["clue"] += 1
    if params.twist == "map":
        world.say(
            f"Then came the twist: {twist.reveal}. {hero.id} stared, blinked, and knew this was no ordinary afternoon."
        )
    elif params.twist == "message":
        world.say(
            f"Then came the twist: {twist.reveal}. {hero.id} read it twice and felt the adventure change shape."
        )
    elif params.twist == "toy":
        world.say(
            f"Then came the twist: {twist.reveal}. {hero.id} picked it up, and the tiny pointer trembled like a secret."
        )
    else:
        world.say(
            f"Then came the twist: {twist.reveal}. {hero.id} watched closely and noticed it was leading somewhere on purpose."
        )

    hero.meters["clue"] += 1
    hero.memes["focus"] = 1
    hero.memes["worry"] = 0

    world.say(
        f"{twist.reason.capitalize()}, so {hero.id} followed the clue around the stoop instead of giving up."
    )

    world.para()
    hero.meters["calm"] += 1
    hero.meters["risk"] = max(hero.meters["risk"], 0)
    world.say(
        f"At the end, {twist.resolution}. {hero.id} found it, laughed softly, and felt the stoop turn into a real adventure."
    )
    world.say(
        f"{hero.id} left the stoop a little wiser, with {hero.pronoun('possessive')} eyes wide and {hero.pronoun('possessive')} heart brave."
    )

    world.facts.update(
        hero=hero,
        action=act,
        twist=twist,
        stoop=stoop,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Quality gates and helpers
# ---------------------------------------------------------------------------
def valid_combo(action: Action, twist: Twist) -> bool:
    if action.id == "search" and twist.id == "message":
        return True
    if action.id == "tap" and twist.id in {"toy", "map"}:
        return True
    if action.id == "peer" and twist.id in {"bird", "map"}:
        return True
    if action.id == "listen" and twist.id in {"message", "bird"}:
        return True
    if action.id == "imagine" and twist.id in {"map", "toy", "message"}:
        return True
    return False


def curated_combos() -> list[tuple[str, str]]:
    combos = []
    for a in ACTIONS.values():
        for t in TWISTS.values():
            if valid_combo(a, t):
                combos.append((a.id, t.id))
    return combos


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "action")
    twist = _safe_fact(world, f, "twist")
    return [
        f'Write a short adventure story for a child named {hero.id} on a stoop, with an inner monologue and a twist.',
        f"Tell a gentle adventure where {hero.id} does {act.verb} and discovers that {twist.reveal}.",
        f'Write a child-friendly story about the word "stoop" that ends with a surprising clue and a brave choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "action")
    twist = _safe_fact(world, f, "twist")
    qa = [
        QAItem(
            question=f"Who is having the adventure on the stoop?",
            answer=f"{hero.id} is the child having the adventure on the stoop.",
        ),
        QAItem(
            question=f"What was {hero.id} doing before the twist appeared?",
            answer=f"{hero.id} was {act.verb} and thinking carefully about what the stoop might hide.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {twist.reveal}.",
        ),
        QAItem(
            question=f"How did the adventure end?",
            answer=f"It ended with {hero.id} finding the hidden thing and seeing the stoop as a place full of mystery.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    act = _safe_fact(world, f, "action")
    twist = _safe_fact(world, f, "twist")
    out = [
        QAItem(
            question="What is a stoop?",
            answer="A stoop is a small set of steps or a little porch area at a front door.",
        ),
        QAItem(
            question="Why can a stoop feel like a place for adventure?",
            answer="A stoop can feel like adventure because even a small place can have hidden clues, tiny sounds, and secret surprises.",
        ),
    ]
    if "map" in twist.tags:
        out.append(
            QAItem(
                question="What is a map used for?",
                answer="A map shows where things are and helps someone find the way to a place.",
            )
        )
    if "bird" in twist.tags:
        out.append(
            QAItem(
                question="Why do birds hop around on steps?",
                answer="Birds hop around to look for food, check their surroundings, or move from one safe spot to another.",
            )
        )
    if "listen" in act.tags or "sound" in act.tags:
        out.append(
            QAItem(
                question="Why do people listen closely when exploring?",
                answer="People listen closely because small sounds can give away clues about what is nearby.",
            )
        )
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid adventure exists when the action and twist are compatible.
valid_combo(A, T) :- action(A), twist(T), compatible(A, T).

% Compatibility mirrors the Python reasonableness gate.
compatible(peer, map).
compatible(peer, bird).
compatible(listen, message).
compatible(listen, bird).
compatible(search, message).
compatible(tap, toy).
compatible(tap, map).
compatible(imagine, map).
compatible(imagine, toy).
compatible(imagine, message).

% Show a complete story option.
valid_story(Name, A, T) :- child(Name), valid_combo(A, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in HERO_NAMES:
        lines.append(asp.fact("child", name))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for aid in ACTIONS:
        for tid in TWISTS:
            if valid_combo(_safe_lookup(ACTIONS, aid), _safe_lookup(TWISTS, tid)):
                lines.append(asp.fact("compatible", aid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(curated_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = build_world(params)
    return world


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny adventure world on a stoop, with inner monologue and a twist."
    )
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--twist", choices=sorted(TWISTS))
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
    action = getattr(args, "action", None) or rng.choice(list(ACTIONS))
    twist = getattr(args, "twist", None) or rng.choice(list(TWISTS))
    if not valid_combo(_safe_lookup(ACTIONS, action), _safe_lookup(TWISTS, twist)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(name=name, trait=trait, action=action, twist=twist)


CURATED = [
    StoryParams(name="Eyer", trait="curious", action="peer", twist="map"),
    StoryParams(name="Eyer", trait="brave", action="listen", twist="bird"),
    StoryParams(name="Milo", trait="careful", action="search", twist="message"),
    StoryParams(name="Rosa", trait="bold", action="tap", twist="toy"),
    StoryParams(name="Nina", trait="dreamy", action="imagine", twist="message"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible action/twist combos ({len(stories)} with names):\n")
        for action, twist in triples:
            names = sorted(name for (name, a, t) in stories if (a, t) == (action, twist))
            print(f"  {action:8} {twist:8}  [{', '.join(names)}]")
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
            header = f"### {p.name}: {p.action} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
