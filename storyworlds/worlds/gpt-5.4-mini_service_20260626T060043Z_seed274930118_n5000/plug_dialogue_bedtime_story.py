#!/usr/bin/env python3
"""
storyworlds/worlds/plug_dialogue_bedtime_story.py
==================================================

A tiny bedtime-story world about a child, a plug, and a gentle nighttime
compromise.

Premise:
- A child wants to plug in a bedtime lamp or music toy.
- The parent worries because the plug is out of reach, loose, or unsafe.

Turn:
- They talk about it in a quiet bedroom at bedtime.
- The parent helps with a safe, warm fix.

Resolution:
- The child gets the cozy light or song, and the room settles into sleep.

This world keeps the prose close to a bedtime story:
soft setting, short dialogue, concrete objects, and a calm ending image.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    plug: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Room:
    name: str = "the bedroom"
    bedtime: bool = True
    outlets: int = 1
    dark: bool = True
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
class Toy:
    id: str
    label: str
    phrase: str
    needs_plug: bool = True
    cozy: str = ""
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
class Plug:
    id: str
    label: str
    phrase: str
    safe: bool = True
    helpful: str = ""
    result: str = ""
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
    room: str
    toy: str
    plug: str
    name: str
    gender: str
    parent: str
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
    def __init__(self, room: Room) -> None:
        self.room = room
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.room)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_nervous(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("worry", 0) < THRESHOLD:
            continue
        sig = ("nervous", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.pronoun('subject').capitalize()} looked worried in the dim room.")
    return out


def _r_safe_help(world: World) -> list[str]:
    out: list[str] = []
    parent = next((e for e in world.characters() if e.type in {"mother", "father", "mom", "dad"}), None)
    child = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    toy = world.entities.get("toy")
    plug = world.entities.get("plug")
    if not parent or not child or not toy or not plug:
        return out
    if parent.memes.get("care", 0) < THRESHOLD:
        return out
    if child.memes.get("hope", 0) < THRESHOLD:
        return out
    sig = ("safe_help",)
    if sig in world.fired:
        return out
    if plug.meters.get("safe", 0) < THRESHOLD:
        return out
    world.fired.add(sig)
    toy.meters["on"] = 1
    toy.memes["cozy"] = 1
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    world.room.dark = False
    out.append("The little light came on, soft and warm, like a bedtime star.")
    return out


CAUSAL_RULES = [
    _r_nervous,
    _r_safe_help,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, child: Entity, toy: Toy, plug: Plug) -> dict:
    sim = world.copy()
    child2 = sim.get(child.id)
    toy2 = sim.get(toy.id)
    plug2 = sim.get(plug.id)
    child2.memes["hope"] = 1
    if plug2.meters.get("safe", 0) >= THRESHOLD:
        toy2.meters["on"] = 1
    propagate(sim, narrate=False)
    return {"toy_on": toy2.meters.get("on", 0) >= THRESHOLD, "dark": sim.room.dark}


def bedtime_sparkle(toy: Toy) -> str:
    return {
        "night-light": "a tiny moon on the wall",
        "music box": "a gentle tune that floated like a blanket",
        "lamp": "a sleepy glow that made the shadows smaller",
    }.get(toy.id, "a cozy bedtime glow")


def setting_line(room: Room) -> str:
    if room.bedtime:
        return "The bedroom was quiet, and the blanket waited on the bed."
    return f"{room.name.capitalize()} was still and calm."


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who liked soft blankets, warm lights, and very short stories."
    )


def want_bedtime_toy(world: World, child: Entity, toy: Toy) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.say(
        f'"Can we {toy.phrase}?" {child.id} asked. "{toy.cozy}"'
    )


def parent_worries(world: World, parent: Entity, child: Entity, plug: Plug) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    parent.memes["care"] = parent.memes.get("care", 0) + 1
    world.say(
        f'"Not with that {plug.label}," {parent.id} said softly. '
        f'"I want the room to stay safe and sleepy."'
    )


def look_for_fix(world: World, parent: Entity, child: Entity, toy: Toy, plug: Plug) -> bool:
    pred = predict_outcome(world, child, toy, plug)
    if not pred["toy_on"]:
        return False
    world.say(
        f'"Let me help," {parent.id} said. "We can use the {plug.label} the safe way."'
    )
    return True


def plug_it_in(world: World, child: Entity, parent: Entity, toy: Toy, plug: Plug) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(
        f'{child.id} watched as {parent.id} fitted the {plug.label} in carefully.'
    )
    world.say(
        f'"Now look," {parent.id} whispered.'
    )
    propagate(world, narrate=True)
    world.say(
        f'{child.id} smiled at the {bedtime_sparkle(toy)}.'
    )


def tell(room: Room, toy_cfg: Toy, plug_cfg: Plug, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(room)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    toy = world.add(Entity(id="toy", type=toy_cfg.id, label=toy_cfg.label, phrase=toy_cfg.phrase, owner=child.id))
    plug = world.add(Entity(id="plug", type="plug", label=plug_cfg.label, phrase=plug_cfg.phrase))
    plug.meters["safe"] = 1 if plug_cfg.safe else 0

    world.say(setting_line(room))
    introduce(world, child)
    world.para()
    want_bedtime_toy(world, child, toy)
    parent_worries(world, parent, child, plug)
    world.para()
    if look_for_fix(world, parent, child, toy, plug):
        plug_it_in(world, child, parent, toy, plug)

    world.facts.update(
        child=child,
        parent=parent,
        toy=toy_cfg,
        plug=plug_cfg,
        room=room,
        resolved=bool(toy.meters.get("on", 0) >= THRESHOLD),
    )
    return world


ROOMS = {
    "bedroom": Room(name="the bedroom", bedtime=True, outlets=1, dark=True),
}

TOYS = {
    "night-light": Toy(id="night-light", label="night-light", phrase="plug in the night-light", cozy="It makes the room feel safe."),
    "music-box": Toy(id="music box", label="music box", phrase="wind up the music box and plug in its little light", cozy="It can play a sleepy tune."),
    "lamp": Toy(id="lamp", label="lamp", phrase="plug in the lamp", cozy="It makes a golden glow."),
}

PLUGS = {
    "straight-plug": Plug(id="straight-plug", label="plug", phrase="the plug", safe=True, helpful="fits into the wall gently", result="lights the toy"),
    "loose-plug": Plug(id="loose-plug", label="loose plug", phrase="the loose plug", safe=False, helpful="wobbles", result="might not work"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Theo", "Max"]
TRAITS = ["sleepy", "gentle", "curious", "brave", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for room_id, room in ROOMS.items():
        for toy_id in TOYS:
            for plug_id, plug in PLUGS.items():
                if room.bedtime and plug.safe:
                    out.append((room_id, toy_id, plug_id))
    return out


@dataclass
class StoryParams:
    room: str
    toy: str
    plug: str
    name: str
    gender: str
    parent: str
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


KNOWLEDGE = {
    "plug": [
        ("What is a plug?",
         "A plug is the part of an electric cord that fits into a wall outlet so a lamp or toy can get power.")
    ],
    "night-light": [
        ("What does a night-light do?",
         "A night-light gives off a small, soft glow so a room does not feel too dark at bedtime.")
    ],
    "lamp": [
        ("What is a lamp for?",
         "A lamp shines light, which helps people see when the room is dark.")
    ],
    "music box": [
        ("What does a music box do?",
         "A music box plays a little tune when it is used in a gentle way.")
    ],
}


class _ASP:
    pass


ASP_RULES = r"""
room_ok(R) :- bedtime_room(R).
safe_combo(R,T,P) :- room_ok(R), toy(T), plug(P), safe_plug(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("bedtime_room", rid))
        if room.bedtime:
            lines.append(asp.fact("bedtime", rid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    for pid, plug in PLUGS.items():
        lines.append(asp.fact("plug", pid))
        if plug.safe:
            lines.append(asp.fact("safe_plug", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_combo/3."))
    return sorted(set(asp.atoms(model, "safe_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short bedtime story for a young child about a {f["plug"].label} and a cozy light.',
        f'Tell a gentle story where {f["child"].id} wants to use the {f["toy"].label}, but a parent worries about the {f["plug"].label}.',
        f'Write a simple dialogue story set in {f["room"].name} that ends with a safe, sleepy glow.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, toy, plug, room = f["child"], f["parent"], f["toy"], f["plug"], f["room"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the {toy.label}?",
            answer=f"{child.id} wanted to {toy.phrase}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {plug.label}?",
            answer=f"{parent.id} wanted the room to stay safe and sleepy, so {parent.pronoun('subject')} watched the {plug.label} carefully.",
        ),
        QAItem(
            question=f"What changed by the end of the story in {room.name}?",
            answer=f"The toy was on, the room was soft and dim, and {child.id} had a cozy bedtime glow to fall asleep with.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["plug"].id, world.facts["toy"].id}
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(room="bedroom", toy="night-light", plug="straight-plug", name="Mia", gender="girl", parent="mother", trait="sleepy"),
    StoryParams(room="bedroom", toy="lamp", plug="straight-plug", name="Leo", gender="boy", parent="father", trait="quiet"),
    StoryParams(room="bedroom", toy="music-box", plug="straight-plug", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def explain_rejection(toy: Toy, plug: Plug) -> str:
    if not plug.safe:
        return "(No story: the loose plug would not make a calm, safe bedtime fix.)"
    return "(No story: that combination does not give a clear bedtime turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a plug, a child, and a gentle dialogue.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--plug", choices=PLUGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "toy", None) and getattr(args, "plug", None):
        if getattr(args, "plug", None) != "straight-plug":
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "room", None) is None or c[0] == getattr(args, "room", None))
              and (getattr(args, "toy", None) is None or c[1] == getattr(args, "toy", None))
              and (getattr(args, "plug", None) is None or c[2] == getattr(args, "plug", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    room, toy, plug = rng.choice(list(combos))
    toy_cfg = _safe_lookup(TOYS, toy)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(room=room, toy=toy, plug=plug, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(ROOMS, params.room), _safe_lookup(TOYS, params.toy), _safe_lookup(PLUGS, params.plug), params.name, params.gender, params.parent)
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
        print(asp_program("#show safe_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} safe combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
