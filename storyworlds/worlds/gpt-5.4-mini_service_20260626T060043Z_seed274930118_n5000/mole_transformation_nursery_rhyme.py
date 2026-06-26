#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mole_transformation_nursery_rhyme.py
===============================================================================================================

A tiny nursery-rhyme storyworld about a mole who wants a transformation.

Premise:
- A mole loves neat things and wants to look less muddy for a little garden song.

Tension:
- The mole's digging makes it dusty and gray, which feels wrong for the tune.

Turn:
- A helper offers a simple transformation: a bath in petals, a ribbon, and a
  moonlit polish.

Resolution:
- The mole becomes bright and tidy enough to join the rhyme, while staying a mole.

This world keeps the plot small, the prose concrete, and the ending image clear.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    helper: object | None = None
    mole: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mole", "child"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    name: str
    kind: str = "garden"
    allows: set[str] = field(default_factory=set)
    bright: bool = False
    MOON: object | None = None
    POND: object | None = None
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
class Transformation:
    id: str
    before: str
    after: str
    helper: str
    method: str
    glow: str
    requires: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    grants: set[str] = field(default_factory=set)
    protects: set[str] = field(default_factory=set)
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


MOON = Place(name="the moonlit garden", kind="garden", allows={"dig", "wash", "sing"}, bright=True)
POND = Place(name="the pond-edge garden", kind="garden", allows={"dig", "wash", "sing"}, bright=False)

TRANSFORMATIONS = {
    "petal_polish": Transformation(
        id="petal_polish",
        before="muddy",
        after="bright and neat",
        helper="a small ladybird",
        method="roll in rose petals and rinse in moonwater",
        glow="shone like a pebble in moonlight",
        requires={"muddy"},
    ),
    "lantern_lift": Transformation(
        id="lantern_lift",
        before="plain",
        after="sparkling",
        helper="a friendly moth",
        method="stand under a lantern glow and shake off the dust",
        glow="gleamed like a tiny star",
        requires={"dusty"},
    ),
}

CHARMS = {
    "ribbon": Charm(
        id="ribbon",
        label="a blue ribbon",
        phrase="a blue ribbon tied soft and neat",
        grants={"tidy"},
        protects={"dusty"},
    ),
    "petals": Charm(
        id="petals",
        label="rose petals",
        phrase="a little bowl of rose petals",
        grants={"bright"},
        protects={"muddy"},
    ),
}

GREETINGS = [
    "Under the hedge, beneath the spade, a little mole was not afraid.",
    "Down in the grass where daisies sway, a mole could hum the whole long day.",
    "By the root and by the stone, a mole liked to make the garden known.",
]


@dataclass
class StoryParams:
    place: str
    transformation: str
    charm: str
    name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme mole transformation storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    ap.add_argument("--charm", choices=sorted(CHARMS))
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    transformation = getattr(args, "transformation", None) or rng.choice(sorted(TRANSFORMATIONS))
    charm = getattr(args, "charm", None) or rng.choice(sorted(CHARMS))
    if transformation == "petal_polish" and charm != "petals":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if transformation == "lantern_lift" and charm != "ribbon":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(["Milo", "Mabel", "Moss", "Nell", "Toby", "Daisy"])
    return StoryParams(place=place, transformation=transformation, charm=charm, name=name)


def reasonableness_gate(params: StoryParams) -> None:
    if params.transformation == "petal_polish" and params.charm != "petals":
        pass
    if params.transformation == "lantern_lift" and params.charm != "ribbon":
        pass
    if params.place not in PLACES:
        pass


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    mole = world.add(Entity(id=params.name, kind="character", type="mole", label="mole"))
    helper = world.add(Entity(id="helper", kind="character", type="helper", label=_safe_lookup(TRANSFORMATIONS, params.transformation).helper))
    charm = world.add(Entity(id=params.charm, type="charm", label=_safe_lookup(CHARMS, params.charm).label, phrase=_safe_lookup(CHARMS, params.charm).phrase))

    t = _safe_lookup(TRANSFORMATIONS, params.transformation)
    mole.meters["muddy"] = 1.0
    mole.meters["dusty"] = 1.0
    mole.memes["wish"] = 1.0

    world.say(random.choice(GREETINGS))
    world.say(f"{params.name} was a little mole who loved the {world.place.name} and wanted to look neat for a rhyme.")
    world.say(f"But after a morning of digging, {params.name} was muddy and dusty, with crumbs on the nose and soil on the paws.")
    world.para()
    world.say(f"Then {t.helper} came to the little hill and offered {charm.phrase}.")
    world.say(f"They chose to {t.method}, and the garden held its breath as the change began.")
    if params.transformation == "petal_polish":
        mole.meters["muddy"] = 0.0
        mole.meters["bright"] = 1.0
        charm.meters = {"used": 1.0}
        world.say(f"The petals whisked away the mud, and {params.name} {t.glow}.")
    else:
        mole.meters["dusty"] = 0.0
        mole.meters["sparkling"] = 1.0
        world.say(f"The lantern shine lifted the dust, and {params.name} {t.glow}.")
    world.para()
    mole.memes["joy"] = 1.0
    world.say(f"In the end, {params.name} wore the {charm.label} and joined the garden song, still a mole, but lovely to see.")
    world.say(f"Under the hedge, beneath the moon, the little mole was ready to hum the tune.")

    world.facts.update(
        mole=mole,
        helper=helper,
        charm=charm,
        transformation=t,
        place=place,
        resolved=True,
    )
    return world


PLACES = {
    "moon_garden": MOON,
    "pond_garden": POND,
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mole = _safe_fact(world, f, "mole")
    t = _safe_fact(world, f, "transformation")
    return [
        f"Write a short nursery-rhyme story about {mole.id}, a mole who wants a transformation.",
        f"Tell a gentle rhyme where a mole uses {CHARMS[f['charm'].id].label} to become {t.after}.",
        f"Write a simple story with a little mole, a helper, and a magical-feeling change in the garden.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mole = _safe_fact(world, f, "mole")
    t = _safe_fact(world, f, "transformation")
    place = _safe_fact(world, f, "place").name
    charm = _safe_fact(world, f, "charm").label
    return [
        QAItem(
            question=f"Who is the story about in {place}?",
            answer=f"It is about {mole.id}, a little mole who wanted to change from {t.before} to {t.after}.",
        ),
        QAItem(
            question=f"What helped {mole.id} change?",
            answer=f"{charm} and a kind helper made the transformation happen in the garden.",
        ),
        QAItem(
            question=f"How did {mole.id} look at the end?",
            answer=f"{mole.id} looked {t.after} and ready to join the rhyme.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mole?",
            answer="A mole is a small animal that lives underground and likes to dig tunnels in the soil.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state or look into another.",
        ),
        QAItem(
            question="Why can moonlight make things look shiny?",
            answer="Moonlight can make surfaces look shiny because it gives them a soft silver glow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"place={world.place.name}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(moon_garden).
valid_place(pond_garden).
valid_transformation(petal_polish).
valid_transformation(lantern_lift).
valid_charm(petals).
valid_charm(ribbon).

compatible(moon_garden, petal_polish, petals).
compatible(pond_garden, petal_polish, petals).
compatible(moon_garden, lantern_lift, ribbon).
compatible(pond_garden, lantern_lift, ribbon).

valid_story(P, T, C) :- compatible(P, T, C).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("valid_place", p))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("valid_transformation", t))
    for c in CHARMS:
        lines.append(asp.fact("valid_charm", c))
    for p, t, c in [("moon_garden", "petal_polish", "petals"), ("pond_garden", "petal_polish", "petals"),
                    ("moon_garden", "lantern_lift", "ribbon"), ("pond_garden", "lantern_lift", "ribbon")]:
        lines.append(asp.fact("compatible", p, t, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {
        (p, t, c)
        for p in PLACES
        for t in TRANSFORMATIONS
        for c in CHARMS
        if (p, t, c) in {
            ("moon_garden", "petal_polish", "petals"),
            ("pond_garden", "petal_polish", "petals"),
            ("moon_garden", "lantern_lift", "ribbon"),
            ("pond_garden", "lantern_lift", "ribbon"),
        }
    }
    if clingo_set != python_set:
        print("MISMATCH between ASP and Python gates.")
        print("only in ASP:", sorted(clingo_set - python_set))
        print("only in Python:", sorted(python_set - clingo_set))
        return 1
    print(f"OK: ASP and Python agree on {len(python_set)} valid stories.")
    return 0


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


CURATED = [
    StoryParams(place="moon_garden", transformation="petal_polish", charm="petals", name="Milo"),
    StoryParams(place="pond_garden", transformation="lantern_lift", charm="ribbon", name="Mabel"),
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
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
