#!/usr/bin/env python3
"""
storyworlds/worlds/air_retard_device_foreshadowing_lesson_learned_transformation.py
===================================================================================

A tiny heartwarming story world about air, a retard device, and the moment a
child learns that gentleness can be powerful.

Seed-image tale:
---
A child finds a noisy little fan device in a workshop. At first, the child
wants stronger air for a game, but a feather on the shelf keeps fluttering
almost off the table. A parent notices the clue and helps the child add a soft
cloth screen that retards the air. The device becomes calmer, the feather stays
safe, and the child learns that slowing something down can be the kindest way
to help.

World model:
---
- physical meters: air, noise, wobble, calm, warmth, dust
- emotional memes: curiosity, worry, pride, relief, care

Narrative instruments:
---
- Foreshadowing: small signs the air is too strong
- Lesson Learned: strength is not always kindness; gentleness matters
- Transformation: the device changes from loud and pushy to soft and helpful
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    device: object | None = None
    feather: object | None = None
    hero: object | None = None
    parent: object | None = None
    seed: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
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
    indoor: bool
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
class Device:
    id: str
    label: str
    phrase: str
    purpose: str
    foreshadow: str
    transform: str
    guards: set[str]
    slows: float
    boosts: float
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
    place: str
    device: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _rule_wobble(world: World) -> list[str]:
    out: list[str] = []
    device = next((e for e in world.entities.values() if e.kind == "device"), None)
    feather = world.entities.get("feather")
    if not device or not feather:
        return out
    if device.meters["air"] < THRESHOLD:
        return out
    sig = ("wobble", device.id)
    if sig in world.fired:
        return out
    if feather.meters["wobble"] >= THRESHOLD:
        return out
    world.fired.add(sig)
    feather.meters["wobble"] += 1
    out.append("A feather on the shelf trembled as the air grew too strong.")
    return out


def _rule_calm(world: World) -> list[str]:
    out: list[str] = []
    device = next((e for e in world.entities.values() if e.kind == "device"), None)
    feather = world.entities.get("feather")
    if not device or not feather:
        return out
    if device.meters["calm"] < THRESHOLD:
        return out
    sig = ("calm", device.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    feather.meters["wobble"] = 0
    out.append("The feather settled again, resting as lightly as a kiss.")
    return out


CAUSAL_RULES = [Rule("wobble", _rule_wobble), Rule("calm", _rule_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def describe_setting(setting: Setting) -> str:
    if setting.indoor:
        return f"The {setting.place} was snug and bright, with one small table by the window."
    return f"{setting.place.capitalize()} felt open and breezy, with room for a little experiment."


def predict_air(world: World, actor: Entity, device: Device, gentle: bool) -> dict:
    sim = world.copy()
    d = sim.entities["device"]
    d.meters["air"] += 1
    if gentle:
        d.meters["calm"] += device.slows
    else:
        d.meters["noise"] += 1
    propagate(sim, narrate=False)
    feather = sim.entities["feather"]
    return {"feather_wobble": feather.meters["wobble"], "calm": d.meters["calm"]}


def foreshadow_line(world: World, device: Device) -> str:
    return f"{device.foreshadow}."


def tell(setting: Setting, device_def: Device, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "curious", "kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    device = world.add(Entity(
        id="device",
        kind="device",
        type="device",
        label=device_def.label,
        phrase=device_def.phrase,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
    ))
    feather = world.add(Entity(id="feather", kind="thing", type="feather", label="feather", caretaker=parent.id))
    seed = world.add(Entity(id="seed", kind="thing", type="seed", label="seed pod", caretaker=parent.id))

    world.say(f"{hero.id} was a little {hero.type} who loved building helpful things.")
    world.say(f"{hero.pronoun().capitalize()} had {device.phrase}, and {hero.id} was proud of it.")
    world.say(f"{describe_setting(setting)}")
    world.say(f"{foreshadow_line(world, device_def)}")
    world.say(f"On the shelf nearby, a feather and a seed pod waited quietly, as if they were whispering to each other.")

    world.para()
    world.say(f"{hero.id} wanted to use the {device.label} to make a bigger breeze for play.")
    world.say(f"But when {hero.pronoun('possessive')} {parent.label if parent.label else parent_type} looked at the feather, there was a gentle worry in {hero.pronoun('possessive')} eyes.")
    world.say(f'"If the air is too hard, the little things will shake," {hero.pronoun("possessive")} {parent_type} said.')
    world.say("That was the first clue that this device needed to do more than simply push air.")

    device.meters["air"] += 1
    device.meters["noise"] += 1
    hero.memes["curiosity"] += 1
    hero.memes["pride"] += 1
    parent.memes["worry"] += 1
    propagate(world)

    world.para()
    world.say(f"{hero.id} tested it, and the air rushed out fast.")
    world.say(f"The feather wobbled hard, and even the seed pod slid a little on the table.")
    world.say(f"{hero.id} stopped and listened.")
    world.say(f'"Maybe stronger is not better," {hero.pronoun()} said softly, thinking about the trembling feather.')
    world.say(f"That was the lesson beginning to bloom.")

    world.para()
    world.say(f"Together, {hero.id} and {hero.pronoun('possessive')} {parent.label if parent.label else parent_type} found a soft cloth screen.")
    world.say(f"They tied it onto the front of the device so it would retard the air instead of blasting it.")
    world.say(f"Then the machine changed: the noisy puff became a gentle breeze, and the device felt new without being replaced.")
    device.meters["air"] += 0.5
    device.meters["calm"] += 1
    device.meters["noise"] = max(0.0, device.meters["noise"] - 1)
    hero.memes["relief"] += 1
    hero.memes["care"] += 1
    parent.memes["pride"] += 1
    propagate(world)

    world.para()
    world.say(f"Now the feather stayed still, the seed pod rested safely, and the little breeze was just right for drying paint on a card the child had made.")
    world.say(f"{hero.id} smiled at the transformed device and learned that kindness can be a kind of strength.")
    world.say(f"{hero.id} kept the cloth screen on the front, because the best device was the one that helped without hurting anything.")

    world.facts.update(
        hero=hero,
        parent=parent,
        device=device,
        device_def=device_def,
        feather=feather,
        seed=seed,
        setting=setting,
        gentle=True,
        learned=True,
        transformed=True,
    )
    return world


SETTINGS = {
    "workshop": Setting(place="the workshop", indoor=True, affords={"breeze"}),
    "porch": Setting(place="the porch", indoor=False, affords={"breeze"}),
    "sunroom": Setting(place="the sunroom", indoor=True, affords={"breeze"}),
}

DEVICES = {
    "fan": Device(
        id="fan",
        label="little fan",
        phrase="a little fan with round blue blades",
        purpose="make a breeze",
        foreshadow="A loose feather on the shelf kept twitching whenever the fan hummed",
        transform="The fan became soft and steady with a cloth screen on its face",
        guards={"wobble"},
        slows=1.0,
        boosts=1.0,
    ),
    "blower": Device(
        id="blower",
        label="hand blower",
        phrase="a small hand blower with a shiny handle",
        purpose="move air carefully",
        foreshadow="A paper ribbon on the table curled up each time the blower started",
        transform="The blower turned into a calm helper with a soft front guard",
        guards={"wobble"},
        slows=1.0,
        boosts=1.0,
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Nora", "Lily", "Ava"]
BOY_NAMES = ["Eli", "Theo", "Noah", "Ben", "Finn", "Leo"]
TRAITS = ["curious", "gentle", "thoughtful", "brave", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, did) for place, s in SETTINGS.items() for did in s.affords for _ in [0]]


@dataclass
class _AspProgram:
    text: str
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
    return [
        f'Write a heartwarming story for a young child about {f["hero"].id}, air, and a helpful device.',
        f"Tell a story where {f['hero'].id} learns why it is kinder to retard the air than to blast it.",
        f"Write a gentle tale set in {f['setting'].place} about a small device that changes after a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    device = _safe_fact(world, f, "device_def")
    qs = [
        QAItem(
            question=f"What did {hero.id} first want the device to do?",
            answer=f"{hero.id} first wanted the device to make a bigger breeze for play.",
        ),
        QAItem(
            question="What warning clue showed that the air was too strong?",
            answer="A feather on the shelf trembled, and the seed pod slid a little on the table.",
        ),
        QAItem(
            question="What change made the device gentle?",
            answer="They added a soft cloth screen, and that retarded the air so it moved more calmly.",
        ),
        QAItem(
            question="What did the child learn at the end?",
            answer="The child learned that stronger is not always better and that a gentle device can help more kindly.",
        ),
    ]
    qs.append(
        QAItem(
            question=f"How did {hero.id} and {parent.label if parent.label else 'the parent'} change the device?",
            answer=f"They kept {device.label} but gave it a soft cloth screen, so it became calmer and safer.",
        )
    )
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is air?",
            answer="Air is the invisible stuff all around us that we breathe and feel when it moves as wind or a breeze.",
        ),
        QAItem(
            question="What does it mean to retard something?",
            answer="To retard something means to slow it down a little.",
        ),
        QAItem(
            question="What is a device?",
            answer="A device is a tool or machine made to do a job and help people.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="workshop", device="fan", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="porch", device="blower", name="Theo", gender="boy", parent="father"),
]


ASP_RULES = r"""
useful(Place, Device) :- setting(Place), afford(Place, breeze), device(Device).
valid_story(Place, Device) :- useful(Place, Device).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", pid, a))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, d) for p, d in valid_combos()}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about air, a device, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "device", None):
        combos = [c for c in combos if c[1] == getattr(args, "device", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, device = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, device=device, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(DEVICES, params.device), params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, device in stories:
            print(f"  {place:10} {device}")
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
            header = f"### {p.name}: {p.device} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
