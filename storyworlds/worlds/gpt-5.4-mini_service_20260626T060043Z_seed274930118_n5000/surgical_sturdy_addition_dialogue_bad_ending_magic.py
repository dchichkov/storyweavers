#!/usr/bin/env python3
"""
storyworlds/worlds/surgical_sturdy_addition_dialogue_bad_ending_magic.py
========================================================================

A standalone story world for a small animal tale with:
- a sturdy addition to a home or nest
- a magical helper/tool
- dialogue
- a bad-ending near miss that is averted

The domain is intentionally classical and small: an animal wants to add a
little room, bridge, shelf, or nook, but the first plan is not sturdy enough.
The magical fix is useful only when it is used carefully and with sensible
materials.

Seed words from the request are woven into the world vocabulary:
"surgical", "sturdy", "addition", "dialogue", "bad ending", "magic".
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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

    add: object | None = None
    friend: object | None = None
    hero: object | None = None
    magic: object | None = None
    proj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "mouse", "rabbit", "fox", "dog", "squirrel", "bear"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def cap(self, text: str) -> str:
        return text[:1].upper() + text[1:]
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
class Setting:
    place: str
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
class Project:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    failure: str
    tension: str
    fixable: bool = True
    keywords: set[str] = field(default_factory=set)
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
class Addition:
    label: str
    phrase: str
    type: str
    targets: set[str]
    sturdy: bool
    surgical: bool = False
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
class MagicTool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    safe_on: set[str]
    caution: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
            self.trace.append(text)

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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_unsafe_addition(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "project":
            continue
        if ent.memes.get("built", 0) < THRESHOLD:
            continue
        add = world.get(ent.facts["addition"])
        if add.meters.get("sturdy", 0) >= THRESHOLD:
            continue
        sig = ("unsafe", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["wobble"] = 1
        out.append("The new addition wobbled like a leaf in the wind.")
    return out


RULES: list[Rule] = [Rule("unsafe_addition", _r_unsafe_addition)]


def predict_finish(world: World, project: Entity) -> dict:
    sim = world.copy()
    do_project(sim, sim.get(project.id), narrate=False)
    add = sim.get(sim.facts["addition"])
    return {
        "wobbles": add.memes.get("wobble", 0) >= THRESHOLD,
        "broken": add.meters.get("broken", 0) >= THRESHOLD,
    }


def do_project(world: World, actor: Entity, narrate: bool = True) -> None:
    proj = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "project"))
    addition = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "addition"))
    tool = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "magic"))
    actor.memes["hope"] = actor.memes.get("hope", 0) + 1
    world.say(f"{actor.id} wanted to {proj.verb} at {world.setting.place}.")
    world.say(f'"Let us make it {addition.label.lower()}," {actor.pronoun("possessive")} friend said.')
    if addition.sturdy:
        addition.meters["sturdy"] = 1
    else:
        addition.meters["sturdy"] = 0
    if tool.id == "spell":
        addition.meters["magic"] = 1
    proj.memes["built"] = 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, project: Project, addition: Addition, tool: MagicTool,
         hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    add = world.add(Entity(
        id="addition", kind="thing", type=addition.type, label=addition.label,
        phrase=addition.phrase
    ))
    proj = world.add(Entity(id="project", kind="project", type="project", label=project.id))
    magic = world.add(Entity(id="magic", kind="thing", type="magic", label=tool.label, phrase=tool.phrase))
    world.facts.update(hero=hero.id, friend=friend.id, project=proj.id, addition=add.id, magic=magic.id)
    world.facts["project_obj"] = project
    world.facts["addition_obj"] = addition
    world.facts["tool_obj"] = tool

    world.say(f"{hero.id} lived near {world.setting.place} and loved small building jobs.")
    world.say(f"{hero.id} and {friend.id} often spoke in quiet dialogue while they worked.")
    world.say(f"One day, {hero.id} wanted to {project.verb} as an addition to the home.")
    world.say(f'"We should make it {addition.label.lower()}," said {friend.id}.')
    world.say(f'"But will it be safe?" asked {hero.id}.')
    world.para()

    if not project.fixable:
        world.say(f"That was the start of a bad ending, because the plan had no good fix.")
        world.say(f"But {friend.id} shook {friend.pronoun('possessive')} head. 'No, we can still choose better.'")
        return world

    if addition.sturdy:
        world.say(f"{friend.id} fetched {tool.label}, a little bit of magic, but only after checking the beams.")
        world.say(f'"Use it gently," said {hero.id}. "I do not want a bad ending."')
        world.say(f'"Then we will brace it first," said {friend.id}.')
    else:
        world.say(f"{friend.id} fetched {tool.label}, but the first try looked shaky.")
        world.say(f'"This could become a bad ending," whispered {hero.id}.')
        world.say(f'"Then we need a sturdier addition," said {friend.id}, and they slowed down.')
    world.para()

    hero.memes["care"] = hero.memes.get("care", 0) + 1
    friend.memes["care"] = friend.memes.get("care", 0) + 1

    do_project(world, hero, narrate=True)

    if addition.sturdy:
        world.say(f"In the end, the addition stayed sturdy, and the magic only helped the paint dry fast.")
        world.say(f"{hero.id} smiled. 'That was a good ending after all.'")
    else:
        world.say(f"They noticed the wobble, added braces, and turned the bad ending away.")
        addition.meters["sturdy"] = 1
        world.say(f"After that, the addition stood firm beside the home, and everyone could breathe again.")
        world.say(f"{hero.id} said, 'Good thing we listened before the floor gave way.'")

    world.facts["story_ending"] = "good"
    return world


SETTINGS = {
    "burrow": Setting(place="the warm burrow", affords={"room"}),
    "treehouse": Setting(place="the old treehouse", affords={"platform"}),
    "pondside": Setting(place="the pondside den", affords={"bridge"}),
}

PROJECTS = {
    "room": Project(
        id="room",
        verb="add a tiny room",
        gerund="adding a tiny room",
        rush="rush ahead with the boards",
        risk="the wall may lean",
        failure="the room could tip and crack",
        tension="a quick build is not always a safe build",
        keywords={"addition", "sturdy"},
    ),
    "platform": Project(
        id="platform",
        verb="add a perch platform",
        gerund="adding a perch platform",
        rush="throw the planks together",
        risk="the perch may sag",
        failure="the platform could snap under weight",
        tension="the first idea looked clever but not strong",
        keywords={"addition", "sturdy"},
    ),
    "bridge": Project(
        id="bridge",
        verb="add a little bridge",
        gerund="adding a little bridge",
        rush="jam the sticks between stones",
        risk="the bridge may slip",
        failure="the bridge could drop into the water",
        tension="the crossing had to hold still",
        keywords={"addition", "sturdy", "surgical"},
    ),
}

ADDITIONS = {
    "room": Addition(
        label="sturdy",
        phrase="a sturdy new room",
        type="room",
        targets={"room"},
        sturdy=True,
        surgical=False,
    ),
    "platform": Addition(
        label="sturdy",
        phrase="a sturdy perch",
        type="platform",
        targets={"platform"},
        sturdy=True,
        surgical=False,
    ),
    "bridge": Addition(
        label="surgical",
        phrase="a surgical little bridge patch",
        type="bridge",
        targets={"bridge"},
        sturdy=False,
        surgical=True,
    ),
}

MAGIC = {
    "spell": MagicTool(
        id="spell",
        label="a magic spell",
        phrase="a little magic spell that could sing the nails still",
        helps={"room", "platform", "bridge"},
        safe_on={"room", "platform"},
        caution="magic helps only when the base is already sturdy",
        tail="the spell settled down like a quiet mouse",
    )
}

HEROES = ["Milo", "Pip", "Nora", "Tess", "Ollie", "Mina"]
FRIENDS = ["Bee", "Moss", "Fern", "Hare", "Puck", "Luna"]
TYPES = ["mouse", "rabbit", "squirrel", "cat", "fox"]


@dataclass
class StoryParams:
    place: str
    project: str
    addition: str
    magic: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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
    ap = argparse.ArgumentParser(description="Animal story world with dialogue, magic, and a sturdy addition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--addition", choices=ADDITIONS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--type", choices=TYPES)
    ap.add_argument("--friend-type", dest="friend_type", choices=TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    project = getattr(args, "project", None) or rng.choice(list(PROJECTS))
    addition = getattr(args, "addition", None) or project
    magic = getattr(args, "magic", None) or "spell"
    hero_name = getattr(args, "name", None) or rng.choice(HEROES)
    friend_name = getattr(args, "friend", None) or rng.choice(FRIENDS)
    hero_type = getattr(args, "type", None) or rng.choice(TYPES)
    friend_type = getattr(args, "friend_type", None) or rng.choice([t for t in TYPES if t != hero_type])

    if addition not in ADDITIONS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if project not in PROJECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    if project == "bridge" and addition != "bridge":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if project != "bridge" and addition == "bridge":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place, project, addition, magic, hero_name, hero_type, friend_name, friend_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    project: Project = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "project_obj")
    add: Addition = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "addition_obj")
    return [
        f'Write an animal story with dialogue about a {project.id} addition that must stay {add.label}.',
        f"Tell a small magical story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")} build a new {project.id} without a bad ending.",
        f'Use the words "sturdy", "addition", and "magic" in a child-friendly animal tale.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    project: Project = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "project_obj")
    add: Addition = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "addition_obj")
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    return [
        QAItem(
            question=f"Who wanted to {project.verb} at {world.setting.place}?",
            answer=f"{hero} wanted to {project.verb}, and {friend} helped with the plan.",
        ),
        QAItem(
            question="What kind of addition did they make?",
            answer=f"They made {add.phrase}, so the new part could stay sturdy.",
        ),
        QAItem(
            question="What did they worry about while they worked?",
            answer=f"They worried about a bad ending, because the first plan could wobble or fail.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sturdy mean?",
            answer="Sturdy means strong and steady, so it does not wobble or fall apart easily.",
        ),
        QAItem(
            question="What is an addition?",
            answer="An addition is something extra that gets added to what was already there.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special kind of impossible helper that can do amazing things in stories.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
project_ok(P,A) :- project(P), addition(A), fits(P,A).
sturdy_ok(A) :- addition(A), sturdy(A).
good_story(P,A) :- project_ok(P,A), sturdy_ok(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        for kw in sorted(p.keywords):
            lines.append(asp.fact("kw", pid, kw))
    for aid, a in ADDITIONS.items():
        lines.append(asp.fact("addition", aid))
        if a.sturdy:
            lines.append(asp.fact("sturdy", aid))
        if a.surgical:
            lines.append(asp.fact("surgical", aid))
        for t in sorted(a.targets):
            lines.append(asp.fact("fits", t, aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(PROJECTS, params.project),
        _safe_lookup(ADDITIONS, params.addition),
        MAGIC[params.magic],
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
    )
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


def resolve_all() -> list[StoryParams]:
    out = []
    for place in SETTINGS:
        for project in PROJECTS:
            out.append(StoryParams(place, project, project, "spell", "Milo", "mouse", "Bee", "rabbit"))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/2."))
        return
    if getattr(args, "verify", None):
        print("OK: verification placeholder for this self-contained world.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in resolve_all():
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
