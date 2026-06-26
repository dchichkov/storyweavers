#!/usr/bin/env python3
"""
A small animal-story world about a fifth puppy, a bit of conflict, and a funny
turn that ends happily.

The generated seed suggests:
- seed words: fifth, puppy
- features: Conflict, Humor
- style: Animal Story

This world models a tiny puppy family scene with one focused tension:
the fifth puppy wants something silly and important at the same time, and the
grown-up dog helps solve it in a gentle, comic way.
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
    kind: str = "thing"      # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    fifth: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"dog", "puppy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id
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
class Den:
    name: str = "the yard"
    place: str = "the yard"
    affords: set[str] = field(default_factory=set)
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
class Toy:
    id: str
    label: str
    phrase: str
    kind: str = "toy"
    noisy: bool = False
    fragile: bool = False
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


class World:
    def __init__(self, den: Den) -> None:
        self.den = den
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
        clone = World(self.den)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Story ingredients
# ---------------------------------------------------------------------------

DEN_REGISTRY = {
    "yard": Den(name="the yard", place="the yard", affords={"fetch", "bounce", "dig"}),
    "porch": Den(name="the porch", place="the porch", affords={"fetch", "bounce"}),
    "garden": Den(name="the garden", place="the garden", affords={"fetch", "dig"}),
}

TOYS = {
    "ball": Toy(id="ball", label="red ball", phrase="a bright red ball", noisy=True),
    "bone": Toy(id="bone", label="squeaky bone", phrase="a squeaky bone", noisy=True),
    "stick": Toy(id="stick", label="stick", phrase="a long stick", fragile=False),
}

# Simple puppy siblings, including the fifth puppy as seed-mandated focus.
PUPPY_NAMES = ["Pip", "Milo", "Sunny", "Nip", "Fifth"]  # fifth puppy is named Fifth


@dataclass
class StoryParams:
    place: str = ""
    activity: str = ""
    toy: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Causal rules
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for pup in world.characters():
        toy = world.entities.get(pup.facts["toy_id"]) if "toy_id" in pup.__dict__.get("facts", {}) else None
        if toy is None:
            continue
        if pup.meters.get("play", 0) < THRESHOLD:
            continue
    return out


# We keep the causal system small and focused.
def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    fifth = world.get("Fifth")
    parent = world.get("Parent")
    toy = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "toy").id)
    if fifth.memes.get("want", 0) >= THRESHOLD and parent.memes.get("block", 0) >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            fifth.memes["conflict"] = fifth.memes.get("conflict", 0) + 1
            out.append(f"Fifth let out a tiny huff.")
    return out


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    fifth = world.get("Fifth")
    if fifth.memes.get("conflict", 0) >= THRESHOLD and world.facts.get("silly_solution"):
        sig = ("humor",)
        if sig not in world.fired:
            world.fired.add(sig)
            fifth.memes["humor"] = fifth.memes.get("humor", 0) + 1
            out.append("The funny part made everyone blink, then smile.")
    return out


CAUSAL_RULES = [
    Rule("conflict", _r_conflict),
    Rule("humor", _r_humor),
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


def predict_conflict(world: World, fifth: Entity, parent: Entity, toy: Toy) -> bool:
    sim = world.copy()
    sim.get(fifth.id).memes["want"] = 1
    sim.get(parent.id).memes["block"] = 1
    sim.facts["toy"] = toy
    propagate(sim, narrate=False)
    return sim.get(fifth.id).memes.get("conflict", 0) >= THRESHOLD


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def intro(world: World) -> None:
    world.say("At the yard, there were five puppies who loved big, bouncy days.")
    world.say("The fifth puppy was named Fifth, and he was the silliest one of the bunch.")


def setup(world: World, toy: Toy) -> None:
    parent = world.get("Parent")
    fifth = world.get("Fifth")
    world.say(f"One morning, Fifth spotted {toy.phrase}.")
    world.say(f"He wanted it right away, because it looked funny and fun.")
    world.say(f"His parent, the big dog, watched with a careful eye.")


def conflict(world: World, toy: Toy) -> None:
    fifth = world.get("Fifth")
    parent = world.get("Parent")
    world.say(f"Fifth tried to snatch the {toy.label}, but his parent said, \"Not yet.\"")
    fifth.memes["want"] = 1
    parent.memes["block"] = 1
    if predict_conflict(world, fifth, parent, toy):
        world.say("Fifth scrunched up his nose and made the grumpiest puppy face he could manage.")


def turn(world: World, toy: Toy) -> None:
    fifth = world.get("Fifth")
    parent = world.get("Parent")
    world.facts["silly_solution"] = True
    world.say("Then the parent had a funny idea.")
    world.say(f'\"If you can count to five without dropping the {toy.label}, you can have it,\" he said.')
    world.say("Fifth blinked. That sounded hard and funny at the same time.")
    world.say("He balanced the toy on his nose and counted, wobbling like a tiny tree in a windstorm.")


def resolution(world: World, toy: Toy) -> None:
    fifth = world.get("Fifth")
    parent = world.get("Parent")
    fifth.memes["conflict"] = 0
    fifth.memes["joy"] = 1
    world.say("At the fifth count, the toy popped up, and Fifth caught it with a happy bark.")
    world.say(f"His parent laughed so hard his ears bounced.")
    world.say(f"Fifth trotted in a little circle with {toy.label}, proud and pleased.")
    world.say("The yard felt brighter when the puppies were laughing together.")


def tell_story(world: World) -> World:
    intro(world)
    world.para()
    setup(world, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "toy"))
    conflict(world, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "toy"))
    propagate(world, narrate=True)
    world.para()
    turn(world, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "toy"))
    propagate(world, narrate=True)
    world.para()
    resolution(world, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "toy"))
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    toy = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "toy")
    return [
        'Write a short animal story about a fifth puppy who wants a toy and has a funny disagreement with a parent dog.',
        f'Write a gentle story for small children that includes the phrase "{toy.label}" and ends with a laugh.',
        'Tell a playful puppy story with conflict and humor in the yard.',
    ]


def story_qa(world: World) -> list[QAItem]:
    toy = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "toy")
    return [
        QAItem(
            question="Who was the fifth puppy in the story?",
            answer="The fifth puppy was named Fifth. He was the puppy who caused the funny little conflict.",
        ),
        QAItem(
            question=f"What did Fifth want at the start?",
            answer=f"Fifth wanted the {toy.label} right away because it looked fun and silly.",
        ),
        QAItem(
            question="Why did Fifth scrunch up his nose?",
            answer="He scrunched up his nose because his parent said not yet, and Fifth felt grumpy for a moment.",
        ),
        QAItem(
            question="How did the problem turn into a happy ending?",
            answer="The parent made a funny challenge, Fifth balanced the toy and counted to five, and then everyone laughed together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puppy?",
            answer="A puppy is a young dog, small and playful, who likes to run, bounce, and explore.",
        ),
        QAItem(
            question="Why can counting be helpful in a game?",
            answer="Counting can make a game fair and give everyone a clear turn or goal.",
        ),
        QAItem(
            question="What is humor in a story?",
            answer="Humor is when something is funny and makes the reader smile or laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

valid(place,yard).
valid(place,porch).
valid(place,garden).

activity(fetch).
activity(bounce).
activity(dig).

toy(ball).
toy(bone).
toy(stick).

valid_story(Place,Act,Toy) :- valid(place,Place), activity(Act), toy(Toy).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in DEN_REGISTRY:
        lines.append(asp.fact("valid_place", place))
    for act in {"fetch", "bounce", "dig"}:
        lines.append(asp.fact("activity", act))
    for toy in TOYS:
        lines.append(asp.fact("toy", toy))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, a, t) for p in DEN_REGISTRY for a in {"fetch", "bounce", "dig"} for t in TOYS}
    if asp_set != py_set:
        print("MISMATCH between ASP and Python.")
        if asp_set - py_set:
            print("only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("only in Python:", sorted(py_set - asp_set))
        return 1
    print(f"OK: ASP matches Python ({len(py_set)} combos).")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a fifth puppy, conflict, and humor.")
    ap.add_argument("--place", choices=sorted(DEN_REGISTRY))
    ap.add_argument("--activity", choices=["fetch", "bounce", "dig"])
    ap.add_argument("--toy", choices=sorted(TOYS))
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
    place = getattr(args, "place", None) or rng.choice(list(DEN_REGISTRY))
    activity = getattr(args, "activity", None) or rng.choice(["fetch", "bounce", "dig"])
    toy = getattr(args, "toy", None) or rng.choice(list(TOYS))
    den = _safe_lookup(DEN_REGISTRY, place)
    if activity not in den.affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, activity=activity, toy=toy)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(DEN_REGISTRY, params.place))
    parent = world.add(Entity(id="Parent", kind="character", type="dog", label="the parent dog"))
    fifth = world.add(Entity(id="Fifth", kind="character", type="puppy", label="Fifth"))
    toy = _safe_lookup(TOYS, params.toy)
    world.facts["toy"] = toy

    tell_story(world)
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
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
    StoryParams(place="yard", activity="fetch", toy="ball"),
    StoryParams(place="porch", activity="bounce", toy="bone"),
    StoryParams(place="garden", activity="dig", toy="stick"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
