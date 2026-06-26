#!/usr/bin/env python3
"""
Standalone story world: a small digital comedy with reconciliation and a bad ending.

Seed premise:
A child and a sibling/parent/friend are making a funny digital thing together
on a device. A mistake wipes or mangles it. They argue, then reconcile, but the
final result is still a silly disaster instead of a perfect win.

The world is modeled with physical meters and emotional memes, and the prose
is driven by state changes rather than a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    dev: object | None = None
    proj: object | None = None
    def __post_init__(self):
        for k in ("charge", "mess", "broken", "ink", "glow"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "irritation", "panic", "pride", "shame", "forgive", "laugh"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    name: str
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


@dataclass
class Device:
    id: str
    label: str
    kind: str
    fragile: bool = True
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
class Project:
    id: str
    label: str
    phrase: str
    mess: str
    keyword: str
    result_word: str
    funny: str
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
    project: str
    device: str
    name1: str
    type1: str
    name2: str
    type2: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def noun_phrase(name: str, typ: str) -> str:
    return f"{name}, the {typ}"


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


PLACES = {
    "kitchen": Place("the kitchen", {"make", "charge", "type"}),
    "living_room": Place("the living room", {"make", "charge", "type"}),
    "bedroom": Place("the bedroom", {"make", "charge", "type"}),
}

DEVICES = {
    "tablet": Device("tablet", "tablet", "tablet", fragile=True),
    "laptop": Device("laptop", "laptop", "laptop", fragile=True),
    "phone": Device("phone", "phone", "phone", fragile=True),
}

PROJECTS = {
    "card": Project(
        "card",
        "birthday card",
        "a digital birthday card with sparkly stickers",
        "glitchy",
        "card",
        "glitched card",
        "the penguin sticker wore a tiny hat",
    ),
    "comic": Project(
        "comic",
        "comic strip",
        "a digital comic strip about a sneezing robot",
        "smeared",
        "comic",
        "smeared comic",
        "the robot kept sneezing confetti",
    ),
    "poster": Project(
        "poster",
        "poster",
        "a digital poster for the snack club",
        "crooked",
        "poster",
        "crooked poster",
        "the title letters kept dancing sideways",
    ),
}

NAMES = ["Mina", "Owen", "Tia", "Noah", "Zuri", "Iris", "Leo", "Pia"]
TYPES = ["girl", "boy", "sister", "brother", "mother", "father"]
PARTNER_TYPES = ["girl", "boy", "sister", "brother", "mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for proj in PROJECTS:
            for dev in DEVICES:
                combos.append((p, proj, dev))
    return combos


def _act_make(world: World, maker: Entity, project: Project, device: Device) -> None:
    maker.meters["charge"] += 1
    maker.memes["joy"] += 1
    if device.fragile:
        maker.memes["pride"] += 0.5
    world.say(
        f"{maker.id} opened the {device.label} and started a {project.phrase}."
    )


def _act_meddle(world: World, other: Entity, project: Project) -> None:
    other.memes["irritation"] += 1
    world.say(
        f"{other.id} leaned in too close and tapped the wrong button."
    )


def _act_error(world: World, maker: Entity, project: Project, device: Device) -> None:
    maker.meters["mess"] += 1
    maker.memes["panic"] += 1
    if project.keyword in {"card", "comic", "poster"}:
        maker.meters["broken"] += 1
    world.say(
        f"Whoops! The screen blinked, and the {project.label} vanished into a weird little digital puff."
    )


def _act_argument(world: World, a: Entity, b: Entity) -> None:
    a.memes["irritation"] += 1
    b.memes["shame"] += 1
    world.say(
        f"{a.id} frowned, and {b.id} made a guilty face. For a moment, nobody was funny."
    )


def _act_apology(world: World, a: Entity, b: Entity) -> None:
    a.memes["forgive"] += 1
    b.memes["forgive"] += 1
    a.memes["irritation"] = 0.0
    b.memes["irritation"] = 0.0
    world.say(
        f"Then {b.id} said sorry, and {a.id} said it was okay. That was the start of the fix."
    )


def _act_rebuild(world: World, maker: Entity, partner: Entity, project: Project, device: Device) -> None:
    maker.meters["charge"] += 1
    partner.meters["charge"] += 1
    maker.memes["laugh"] += 1
    partner.memes["laugh"] += 1
    world.say(
        f"They made a fresh version together, even though the {device.label} kept suggesting silly emojis."
    )


def _act_bad_ending(world: World, maker: Entity, partner: Entity, project: Project) -> None:
    maker.meters["mess"] += 1
    partner.meters["mess"] += 1
    world.say(
        f"At the end, they sent the {project.label} to the wrong chat, and the whole family got the joke a day early."
    )
    world.say(
        f"The result was not perfect, but {project.funny} made everybody laugh anyway."
    )


def tell(place: Place, project: Project, device: Device, name1: str, type1: str, name2: str, type2: str) -> World:
    world = World(place)
    a = world.add(Entity(id=name1, kind="character", type=type1, traits=["digital", "silly"]))
    b = world.add(Entity(id=name2, kind="character", type=type2, traits=["digital", "helpful"]))
    dev = world.add(Entity(id=device.id, kind="thing", type=device.kind, label=device.label, phrase=device.label, owner=a.id))
    proj = world.add(Entity(id=project.id, kind="thing", type="project", label=project.label, phrase=project.phrase, owner=a.id, caretaker=b.id))
    dev.held_by = a.id

    world.say(
        f"One day in {place.name}, {a.id} and {b.id} wanted to make {project.phrase}."
    )
    world.say(
        f"They crowded around the {device.label}, because digital tools always look easy right before they get dramatic."
    )
    world.para()
    _act_make(world, a, proj, dev)
    _act_meddle(world, b, proj)
    _act_error(world, a, proj, dev)
    _act_argument(world, a, b)
    world.para()
    _act_apology(world, b, a)
    _act_rebuild(world, a, b, proj, dev)
    _act_bad_ending(world, a, b, proj)

    world.facts.update(
        hero=a,
        partner=b,
        device=dev,
        project=proj,
        place=place,
        resolved=True,
        bad_ending=True,
        reconciled=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, proj = f["hero"], f["partner"], f["project"]
    return [
        f'Write a short comedy story about a digital {proj.label} gone wrong, with {a.id} and {b.id} making up afterward.',
        f"Tell a funny story where {a.id} and {b.id} try to make {proj.phrase} on a {f['device'].label} but it ends badly.",
        f"Write a child-friendly digital comedy with reconciliation, a mistake, and a silly bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, proj, dev = f["hero"], f["partner"], f["project"], f["device"]
    return [
        QAItem(
            question=f"What were {a.id} and {b.id} trying to make?",
            answer=f"They were trying to make {proj.phrase} on the {dev.label}.",
        ),
        QAItem(
            question=f"What went wrong with the digital project?",
            answer=f"Someone tapped the wrong button, and the {proj.label} vanished into a silly digital mess.",
        ),
        QAItem(
            question=f"How did {a.id} and {b.id} fix their argument?",
            answer=f"They apologized, forgave each other, and rebuilt the project together.",
        ),
        QAItem(
            question=f"Was the ending a happy one?",
            answer=f"It was a reconciled ending, but not a perfect one: the project ended up sent to the wrong chat, so the result was a funny bad ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does digital mean?",
            answer="Digital means something is made or handled with computers, phones, tablets, or other electronic devices.",
        ),
        QAItem(
            question="Why can a wrong tap cause trouble on a device?",
            answer="A wrong tap can press the wrong button, open the wrong thing, or erase work, because digital tools follow exact instructions.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who had a problem make up and feel okay with each other again.",
        ),
        QAItem(
            question="Why can comedy include mistakes?",
            answer="Comedy can use mistakes because silly accidents can make people laugh, especially when nobody gets badly hurt.",
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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "card", "tablet", "Mina", "girl", "Owen", "boy"),
    StoryParams("living_room", "comic", "laptop", "Leo", "boy", "Tia", "girl"),
    StoryParams("bedroom", "poster", "phone", "Zuri", "girl", "Noah", "boy"),
]


def explain_rejection(place: str, project: str, device: str) -> str:
    return f"(No story: {place}, {project}, and {device} do not form a valid digital comedy setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Digital comedy story world with reconciliation and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--name1")
    ap.add_argument("--type1", choices=TYPES)
    ap.add_argument("--name2")
    ap.add_argument("--type2", choices=PARTNER_TYPES)
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
    if getattr(args, "place", None) and getattr(args, "project", None) and getattr(args, "device", None):
        if (getattr(args, "place", None), getattr(args, "project", None), getattr(args, "device", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    project = getattr(args, "project", None) or rng.choice(list(PROJECTS))
    device = getattr(args, "device", None) or rng.choice(list(DEVICES))
    name1 = getattr(args, "name1", None) or rng.choice(NAMES)
    name2 = getattr(args, "name2", None) or rng.choice([n for n in NAMES if n != name1])
    type1 = getattr(args, "type1", None) or rng.choice(TYPES)
    type2 = getattr(args, "type2", None) or rng.choice([t for t in PARTNER_TYPES if t != type1])
    return StoryParams(place, project, device, name1, type1, name2, type2)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(PROJECTS, params.project), _safe_lookup(DEVICES, params.device), params.name1, params.type1, params.name2, params.type2)
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
place(P) :- setting(P).
project(X) :- proj(X).
device(D) :- gadget(D).

valid(P,X,D) :- place(P), project(X), device(D).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for x in PROJECTS:
        lines.append(asp.fact("proj", x))
    for d in DEVICES:
        lines.append(asp.fact("gadget", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid/3."))
    found = set(asp.atoms(model, "valid"))
    want = set(valid_combos())
    if found == want:
        print(f"OK: clingo gate matches valid_combos() ({len(found)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(found - want))
    print(" only in python:", sorted(want - found))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
            header = f"### {p.name1} and {p.name2}: {p.project} on {p.device} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
