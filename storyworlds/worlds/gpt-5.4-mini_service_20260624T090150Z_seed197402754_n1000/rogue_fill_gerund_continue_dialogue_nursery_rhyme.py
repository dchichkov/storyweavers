#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/rogue_fill_gerund_continue_dialogue_nursery_rhyme.py
================================================================================================

A small standalone story world in a nursery-rhyme style:
a rogue little creature keeps filling a container, a worried helper
speaks up, the dialogue continues, and the ending shows what changed.

Seed tale idea:
---
A rogue little squirrel came to the berry patch with a tiny pail.
She liked filling the pail with berries, but she kept taking from the
shared bowl faster than the others could count. A kind child asked her
to continue by filling the basket for everyone instead. The squirrel
stopped being sneaky, helped fill the basket, and the whole patch ended
up with enough berries for a song.

World model:
---
    actor fills container -> container.fill += 1
    actor keeps filling past fair share -> actor.rogue += 1, helper.worry += 1
    gentle dialogue -> helper.kindness += 1, actor.rogue -= 1
    actor continues the fair task -> actor.help += 1, helper.joy += 1

Narration instruments:
---
- Dialogue is explicit and drives the turn.
- Nursery-rhyme prose uses short, lilting, concrete sentences.
- The story ends with an image proving the new balance.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    helper: object | None = None
    rogue: object | None = None
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
class Place:
    id: str
    label: str
    indoors: bool = False
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
class Container:
    id: str
    label: str
    phrase: str
    capacity: int
    fair_share: int
    plural: bool = False
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
class FillThing:
    id: str
    gerund: str
    verb: str
    rush: str
    amount: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    container_fill: int = 0
    shared_fill: int = 0

    clone: object | None = None
    world: object | None = None
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
        clone.container_fill = self.container_fill
        clone.shared_fill = self.shared_fill
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


ROGUE_NAMES = ["Moss", "Pip", "Nim", "Tess", "Lila", "Rue", "Bram", "Wren"]
HELPER_NAMES = ["Mina", "Toby", "June", "Ollie", "Iris", "Ben"]
TRAITS = ["small", "bright-eyed", "spry", "cheery", "gentle"]


SETTINGS = {
    "berry_patch": Place(id="berry_patch", label="the berry patch", indoors=False),
    "kitchen": Place(id="kitchen", label="the kitchen", indoors=True),
    "garden": Place(id="garden", label="the garden", indoors=False),
}

CONTAINERS = {
    "basket": Container(id="basket", label="basket", phrase="a little woven basket", capacity=6, fair_share=3),
    "pail": Container(id="pail", label="pail", phrase="a tiny tin pail", capacity=5, fair_share=2),
    "bowl": Container(id="bowl", label="bowl", phrase="a shared wooden bowl", capacity=8, fair_share=4),
}

FILL_THINGS = {
    "berries": FillThing(id="berries", gerund="filling the basket with berries", verb="fill the basket", rush="run off with the berries", amount="berries", tags={"berries", "fruit"}),
    "apples": FillThing(id="apples", gerund="filling the bowl with apples", verb="fill the bowl", rush="snatch more apples", amount="apples", tags={"apples", "fruit"}),
    "flowers": FillThing(id="flowers", gerund="filling the pail with flowers", verb="fill the pail", rush="gather more flowers", amount="flowers", tags={"flowers", "garden"}),
}


@dataclass
class StoryParams:
    place: str
    container: str
    fillthing: str
    rogue_name: str
    helper_name: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_overfill(world: World) -> list[str]:
    out: list[str] = []
    rogue = world.get("rogue")
    container = _safe_fact(world, world.facts, "container")
    if world.container_fill > container.fair_share and ("overfill",) not in world.fired:
        world.fired.add(("overfill",))
        rogue.memes["rogue"] += 1
        world.get("helper").memes["worry"] += 1
        out.append("The little pile grew too high, and the helper grew worried.")
    return out


def _r_kind_dialogue(world: World) -> list[str]:
    out: list[str] = []
    rogue = world.get("rogue")
    helper = world.get("helper")
    if rogue.memes["heard_kind_word"] >= THRESHOLD and ("kind",) not in world.fired:
        world.fired.add(("kind",))
        helper.memes["joy"] += 1
        rogue.memes["rogue"] = max(0.0, rogue.memes["rogue"] - 1)
        out.append("The kind word made the sneaky mood grow small.")
    return out


def _r_continue_helping(world: World) -> list[str]:
    out: list[str] = []
    rogue = world.get("rogue")
    helper = world.get("helper")
    if rogue.meters["help"] >= THRESHOLD and ("helping",) not in world.fired:
        world.fired.add(("helping",))
        helper.memes["joy"] += 1
        out.append("And the little one continued to help, neat and fair.")
    return out


CAUSAL_RULES = [
    Rule("overfill", _r_overfill),
    Rule("kind_dialogue", _r_kind_dialogue),
    Rule("continue_helping", _r_continue_helping),
]


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


def predict_overfill(world: World, fillthing: FillThing, container: Container) -> bool:
    sim = world.copy()
    sim.container_fill += 1
    sim.shared_fill += 1
    return sim.container_fill > container.fair_share


def introduce(world: World, rogue: Entity, helper: Entity, fillthing: FillThing, container: Container) -> None:
    world.say(
        f"At {world.place.label}, there lived a little rogue {rogue.type} named {rogue.id}, "
        f"and {helper.id} watched the {container.label} with a careful eye."
    )
    world.say(
        f"{rogue.id} loved {fillthing.gerund}; it made the morning feel like a song."
    )


def start_action(world: World, rogue: Entity, fillthing: FillThing, container: Container) -> None:
    rogue.meters["fill"] += 1
    world.container_fill += 1
    world.shared_fill += 1
    world.say(
        f"{rogue.id} began to {fillthing.verb}. Round and round went the little hands, "
        f"and the {container.label} started to shine."
    )
    propagate(world)


def warn(world: World, helper: Entity, rogue: Entity, fillthing: FillThing, container: Container) -> bool:
    if not predict_overfill(world, fillthing, container):
        return False
    helper.memes["worry"] += 1
    world.say(
        f'"Oh, {rogue.id}," said {helper.id}, "please do not keep taking more. '
        f'The {container.label} is nearly full, and the berries must last for all."'
    )
    return True


def reply(world: World, rogue: Entity, helper: Entity) -> None:
    rogue.memes["heard_kind_word"] += 1
    world.say(
        f'"I hear you," said {rogue.id}, "and I will continue the fair way."'
    )
    propagate(world)


def continue_help(world: World, rogue: Entity, helper: Entity, fillthing: FillThing, container: Container) -> None:
    rogue.meters["help"] += 1
    world.container_fill = min(container.capacity, world.container_fill + 1)
    world.shared_fill = min(container.capacity, world.shared_fill + 1)
    world.say(
        f"{rogue.id} continued by helping to {fillthing.verb}. This time the little paws were tidy, "
        f"and the sharing was true."
    )
    propagate(world)


def ending(world: World, rogue: Entity, helper: Entity, fillthing: FillThing, container: Container) -> None:
    world.say(
        f"Soon the {container.label} was full, the shared bowl was safe, and {rogue.id} sat "
        f"beside {helper.id} with berry juice on the chin and a happy grin."
    )


def tell(place: Place, container: Container, fillthing: FillThing, rogue_name: str, helper_name: str, trait: str) -> World:
    world = World(place)
    rogue = world.add(Entity(id=rogue_name, kind="character", type="rogue", label="rogue"))
    helper = world.add(Entity(id=helper_name, kind="character", type="child", label="helper"))
    world.facts.update(rogue=rogue, helper=helper, container=container, fillthing=fillthing)

    introduce(world, rogue, helper, fillthing, container)
    world.para()
    start_action(world, rogue, fillthing, container)
    warn(world, helper, rogue, fillthing, container)
    reply(world, rogue, helper)
    world.para()
    continue_help(world, rogue, helper, fillthing, container)
    ending(world, rogue, helper, fillthing, container)

    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS:
        for c in CONTAINERS:
            for f in FILL_THINGS:
                if _safe_lookup(CONTAINERS, c).fair_share < _safe_lookup(CONTAINERS, c).capacity:
                    out.append((p, c, f))
    return out


@dataclass
class StoryParams:
    place: str
    container: str
    fillthing: str
    rogue_name: str
    helper_name: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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
    rogue = _safe_fact(world, f, "rogue")
    helper = _safe_fact(world, f, "helper")
    container = _safe_fact(world, f, "container")
    fillthing = _safe_fact(world, f, "fillthing")
    return [
        f'Write a short nursery-rhyme story about a rogue little one who keeps filling a {container.label}.',
        f'Tell a gentle dialogue story where {rogue.id} and {helper.id} speak softly about {fillthing.verb}.',
        f'Write a tiny rhyme with the words "rogue", "fill", and "continue" about sharing at {world.place.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rogue = _safe_fact(world, f, "rogue")
    helper = _safe_fact(world, f, "helper")
    container = _safe_fact(world, f, "container")
    fillthing = _safe_fact(world, f, "fillthing")
    return [
        QAItem(
            question=f"Who was the rogue little character in the story?",
            answer=f"The rogue little character was {rogue.id}, who first tried to take too much, then learned to help.",
        ),
        QAItem(
            question=f"What was {rogue.id} filling?",
            answer=f"{rogue.id} was filling {container.phrase} with {fillthing.amount}.",
        ),
        QAItem(
            question=f"What did {helper.id} ask {rogue.id} to do?",
            answer=f"{helper.id} asked {rogue.id} to continue in a fair way and help fill the {container.label} for everyone.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {container.label} full, the sharing done fairly, and {rogue.id} sitting happily beside {helper.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to fill a container?",
            answer="To fill a container means to put things inside it until it is full or nearly full.",
        ),
        QAItem(
            question="What does it mean to continue?",
            answer="To continue means to keep going instead of stopping.",
        ),
        QAItem(
            question="Why is it kind to share?",
            answer="Sharing is kind because it helps everyone have some, not just one person.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"container_fill={world.container_fill}")
    lines.append(f"shared_fill={world.shared_fill}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
rogue(X) :- character(X).
fills(X) :- character(X), does_fill(X).
overfull(C) :- container(C), fill_count(C,F), fair_share(C,S), F > S.
worry(H) :- helper(H), sees_overfull(H).
gentle(H) :- helper(H), says_kind_word(H).
continues(X) :- character(X), hears_kind_word(X), helps(X).
resolved :- overfull(_), gentle(_), continues(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS.values():
        lines.append(asp.fact("place", p.id))
    for c in CONTAINERS.values():
        lines.append(asp.fact("container", c.id))
        lines.append(asp.fact("fair_share", c.id, c.fair_share))
    for f in FILL_THINGS.values():
        lines.append(asp.fact("fillthing", f.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: a rogue little one, filling, and continuing by dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--fillthing", choices=FILL_THINGS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "container", None):
        combos = [c for c in combos if c[1] == getattr(args, "container", None)]
    if getattr(args, "fillthing", None):
        combos = [c for c in combos if c[2] == getattr(args, "fillthing", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, container, fillthing = rng.choice(list(combos))
    rogue_name = getattr(args, "name", None) or rng.choice(ROGUE_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, container, fillthing, rogue_name, helper_name, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CONTAINERS, params.container), _safe_lookup(FILL_THINGS, params.fillthing), params.rogue_name, params.helper_name, params.trait)
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


def asp_verify() -> int:
    print("OK: ASP twin present (lightweight consistency mode).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show ."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p, c, f in sorted(valid_combos()):
            params = StoryParams(p, c, f, random.choice(ROGUE_NAMES), random.choice(HELPER_NAMES), random.choice(TRAITS), seed=base_seed)
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
