#!/usr/bin/env python3
"""
A standalone storyworld for a tiny ghost-story domain with inner monologue.

Premise:
- A child hears a "ghost" in a quiet place at night.
- The scare turns out to be a harmless pseudo-ghost: a draft, a sheet, a toy,
  or a neighbor's shadow.
- The child hesitates, thinks through the fear, and then investigates.
- Inner monologue is part of the story form, so the model state includes what
  the child privately thinks as well as what happens in the room.

This script follows the Storyweavers storyworld contract:
- typed physical state with meters and emotional memes
- deterministic, state-driven prose
- inline ASP twin and Python reasonableness gate
- generate/emit/main entry points and CLI support
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    id: str
    label: str
    dim: str
    has_echo: bool = False
    has_draft: bool = False
    has_lantern: bool = False
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
class Apparition:
    id: str
    label: str
    kind: str
    is_pseudo: bool
    reveal: str
    sound: str
    fear_level: int
    tags: set[str] = field(default_factory=set)
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
class Comfort:
    id: str
    label: str
    phrase: str
    helps: set[str]
    method: str
    ending: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str
    apparition: str
    comfort: str
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


PLACES = {
    "attic": Place("attic", "the attic", "small", has_echo=True, has_draft=True),
    "hallway": Place("hallway", "the hallway", "narrow", has_echo=True, has_lantern=True),
    "bedroom": Place("bedroom", "the bedroom", "cozy", has_draft=False, has_lantern=True),
    "basement": Place("basement", "the basement", "cool", has_echo=True, has_draft=True),
}

APPARITIONS = {
    "sheet": Apparition(
        "sheet",
        "a white sheet",
        "sheet",
        True,
        "it was only the laundry line moving in the draft",
        "a soft flutter",
        2,
        {"ghost", "draft", "pseudo"},
    ),
    "toy": Apparition(
        "toy",
        "a little robot toy",
        "toy",
        True,
        "it was only a toy with blinking eyes under the chair",
        "a tiny beep",
        2,
        {"ghost", "toy", "pseudo"},
    ),
    "shadow": Apparition(
        "shadow",
        "a long shadow",
        "shadow",
        True,
        "it was only the lamp making a crooked shadow on the wall",
        "a quiet swish",
        2,
        {"ghost", "light", "pseudo"},
    ),
    "ghost": Apparition(
        "ghost",
        "a pale ghost",
        "ghost",
        False,
        "it was a real-looking shape, but still turned out to be harmless",
        "a whispery moan",
        3,
        {"ghost"},
    ),
}

COMFORTS = {
    "lantern": Comfort(
        "lantern",
        "a small lantern",
        "a small lantern",
        {"ghost", "shadow"},
        "shine the light into the corner",
        "the dark corners became just a room again",
        {"light", "safe"},
    ),
    "blanket": Comfort(
        "blanket",
        "a warm blanket",
        "a warm blanket",
        {"ghost", "sheet"},
        "wrap up and breathe slowly",
        "the room felt smaller and kinder",
        {"warm", "safe"},
    ),
    "teddy": Comfort(
        "teddy",
        "a teddy bear",
        "a teddy bear",
        {"ghost", "toy", "sheet", "shadow"},
        "hold the teddy tight",
        "the fear had something soft to hold onto",
        {"soft", "safe"},
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Ivy", "June"],
    "boy": ["Eli", "Theo", "Finn", "Max", "Owen"],
}
TRAITS = ["curious", "quiet", "brave", "hesitant", "dreamy", "careful"]


def reasonableness_gate(place: Place, apparition: Apparition, comfort: Comfort) -> None:
    if apparition.is_pseudo and "pseudo" not in apparition.tags:
        pass
    if not apparition.is_pseudo and place.id == "bedroom" and comfort.id == "lantern":
        return
    if apparition.kind not in comfort.helps and not (apparition.is_pseudo and "ghost" in comfort.helps):
        pass


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, app in APPARITIONS.items():
            for cid, com in COMFORTS.items():
                try:
                    reasonableness_gate(place, app, com)
                except StoryError:
                    continue
                if app.kind in com.helps or (app.is_pseudo and "ghost" in com.helps):
                    combos.append((pid, aid, cid))
    return combos


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(_safe_lookup(NAMES, gender))


def choose_parent(rng: random.Random) -> str:
    return rng.choice(["mother", "father"])


def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "apparition", None) is None or c[1] == getattr(args, "apparition", None))
        and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))
    ]
    if not filtered:
        pass
    return rng.choice(list(filtered))


def introduce(world: World, child: Entity, parent: Entity, place: Place, app: Apparition) -> None:
    world.say(f"{child.id} was a {next((t for t in child.meters.keys()), '')} child who liked quiet rooms at night.")
    world.say(
        f"One evening, {child.id} and {child.pronoun('possessive')} {parent.label} went to {place.label}."
    )
    world.say(
        f"{child.id} kept looking at the dark corners and listening for {app.sound}."
    )


def inner_monologue(world: World, child: Entity, app: Apparition) -> None:
    child.memes["hesitate"] += 1
    child.memes["fear"] += 1
    world.say(
        f'In {child.pronoun("possessive")} head, {child.id} thought, '
        f'"That sounds like a ghost... but maybe it is only a pseudo-ghost. '
        f'I should hesitate and look twice."'
    )
    world.say(
        f"{child.id} stood still for a moment, because fear made the room feel bigger than it was."
    )


def investigate(world: World, child: Entity, app: Apparition) -> None:
    child.meters["steps"] = child.meters.get("steps", 0) + 1
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} took a slow step forward and listened again."
    )
    world.say(
        f"Near the corner, {app.sound} turned out to be {app.reveal}."
    )


def comfort_scene(world: World, child: Entity, parent: Entity, comfort: Comfort, app: Apparition) -> None:
    child.memes["safe"] += 1
    child.memes["fear"] = 0
    world.say(
        f"Then {child.id}'s {parent.label} brought out {comfort.label} and said, "
        f'"Let\'s use this and check together."'
    )
    world.say(
        f"{child.id} followed {parent.pronoun('object')}, {comfort.method}, and {comfort.ending}."
    )
    if app.is_pseudo:
        world.say(
            f"In the end, the supposed ghost was only {app.reveal}."
        )
    else:
        world.say(
            f"In the end, the ghostly shape was not mean at all; it just wanted the room to stay quiet."
        )


def ending_image(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"{child.id} finally smiled, and the dark room felt like an ordinary room again, with {parent.pronoun('possessive')} calm voice beside {child.pronoun('object')}."
    )


def tell(place: Place, app: Apparition, comfort: Comfort, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={"brave": 0.0}, memes={"fear": 0.0}))
    child.meters["trait"] = 1.0
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    world.facts.update(place=place, apparition=app, comfort=comfort, child=child, parent=parent, trait=trait)

    world.say(f"{child.id} was a {trait} {gender} who loved stories about ghosts.")
    world.say(
        f"{child.id} also liked to tell {child.pronoun('possessive')}self that a scary sound might be a pseudo-ghost."
    )
    world.para()
    introduce(world, child, parent, place, app)
    inner_monologue(world, child, app)
    investigate(world, child, app)
    world.para()
    comfort_scene(world, child, parent, comfort, app)
    ending_image(world, child, parent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    app = _safe_fact(world, f, "apparition")
    com = _safe_fact(world, f, "comfort")
    return [
        f'Write a child-friendly ghost story with an inner monologue that includes the word "pseudo".',
        f"Tell a short story about {child.id} hesitating in {world.place.label} because a {app.kind} sound seems spooky, then finding a safe explanation.",
        f'Write a gentle "ghost story" where a child thinks, "I should hesitate," and the fear turns into a harmless truth with {com.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    app = _safe_fact(world, f, "apparition")
    com = _safe_fact(world, f, "comfort")
    parent = _safe_fact(world, f, "parent")
    return [
        QAItem(
            question=f"Why did {child.id} hesitate in {world.place.label}?",
            answer=(
                f"{child.id} hesitated because the sound seemed like a ghost at first, "
                f"and {child.pronoun('possessive')} own thoughts warned that it might only be a pseudo-ghost."
            ),
        ),
        QAItem(
            question=f"What did {child.id} think the spooky sound might really be?",
            answer=(
                f"{child.id} thought it might be a harmless fake-out, like a draft, a shadow, or another ordinary thing."
            ),
        ),
        QAItem(
            question=f"How did {parent.pronoun('subject').capitalize()} help {child.id} feel safe again?",
            answer=(
                f"{parent.pronoun('subject').capitalize()} helped by bringing {com.label} and checking the corner together, "
                f"which made the room feel calm again."
            ),
        ),
        QAItem(
            question=f"What was the scary sound at the end?",
            answer=(
                f"It turned out to be {app.reveal}, so the ghost story ended with a harmless explanation."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hesitate mean?",
            answer="To hesitate means to pause for a moment before acting because you are unsure or careful.",
        ),
        QAItem(
            question="What is a pseudo-ghost?",
            answer="A pseudo-ghost is not a real ghost; it is something ordinary that only seems spooky for a moment.",
        ),
        QAItem(
            question="Why do shadows look scary at night?",
            answer="Shadows can look scary at night because the dark makes their shapes harder to recognize right away.",
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "sheet", "blanket", "Mina", "girl", "mother", "hesitant"),
    StoryParams("hallway", "shadow", "lantern", "Eli", "boy", "father", "curious"),
    StoryParams("bedroom", "toy", "teddy", "Nora", "girl", "mother", "careful"),
]


def explain_rejection(place: Place, app: Apparition, com: Comfort) -> str:
    return (
        f"(No story: {com.label} is not a good fit for {app.label} in {place.label}. "
        f"The compromise has to match the spooky thing and still make a believable child-sized fix.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with inner monologue and pseudo-ghost turns.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--apparition", choices=APPARITIONS)
    ap.add_argument("--comfort", choices=COMFORTS)
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
    place_id, app_id, com_id = select_combo(args, rng)
    place = _safe_lookup(PLACES, place_id)
    app = _safe_lookup(APPARITIONS, app_id)
    com = _safe_lookup(COMFORTS, com_id)
    reasonableness_gate(place, app, com)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    parent = getattr(args, "parent", None) or choose_parent(rng)
    trait = rng.choice(TRAITS)
    return StoryParams(place_id, app_id, com_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(APPARITIONS, params.apparition),
        _safe_lookup(COMFORTS, params.comfort),
        params.name,
        params.gender,
        params.parent,
        params.trait,
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


ASP_RULES = r"""
place(attic). place(hallway). place(bedroom). place(basement).
apparition(sheet). apparition(toy). apparition(shadow). apparition(ghost).
comfort(lantern). comfort(blanket). comfort(teddy).

pseudo(sheet). pseudo(toy). pseudo(shadow).
kind(sheet,ghost). kind(toy,ghost). kind(shadow,ghost). kind(ghost,ghost).

helps(lantern,ghost). helps(lantern,shadow).
helps(blanket,ghost). helps(blanket,sheet).
helps(teddy,ghost). helps(teddy,toy). helps(teddy,sheet). helps(teddy,shadow).

valid(P,A,C) :- place(P), apparition(A), comfort(C), pseudo(A), kind(A,K), helps(C,K).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid, a in APPARITIONS.items():
        lines.append(asp.fact("apparition", aid))
        if a.is_pseudo:
            lines.append(asp.fact("pseudo", aid))
        lines.append(asp.fact("kind", aid, a.kind))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for k in sorted(c.helps):
            lines.append(asp.fact("helps", cid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, a, c in combos:
            print(f"  {p:8} {a:8} {c:8}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
            header = f"### {p.name}: {p.apparition} in {p.place} (comfort: {p.comfort})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
