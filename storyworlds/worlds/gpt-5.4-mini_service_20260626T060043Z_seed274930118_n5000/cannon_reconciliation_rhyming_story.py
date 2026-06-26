#!/usr/bin/env python3
"""
storyworlds/worlds/cannon_reconciliation_rhyming_story.py
=========================================================

A small, classical story world with a cannon, a misunderstanding, and a warm
reconciliation, told in a lightly rhyming, child-facing style.

Premise:
- A child helps prepare a tiny harbor celebration.
- A ceremonial cannon is meant to announce the festival.
- A loud mistake creates worry and a hurt feeling.
- A gentle apology and a careful fix lead to reconciliation.

The story is not a frozen template; the simulated world state drives what
happens, what changes, and how the ending lands.
"""

from __future__ import annotations

import argparse
import dataclasses
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
# World entities
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    is_tool: bool = False
    is_precious: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    cannon: object | None = None
    child: object | None = None
    def __post_init__(self) -> None:
        for k in ("damage", "noise", "soot", "care", "repair"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "hurt", "pride", "reconcile", "calm"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Harbor:
    place: str = "the harbor"
    festival_name: str = "the lantern fête"
    has_water: bool = True
    has_stage: bool = True
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
class CharacterConfig:
    name: str
    gender: str
    role: str
    trait: str
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
class CannonConfig:
    label: str
    phrase: str
    loudness: int
    smoke: str
    rhythm: str
    safe: bool = True
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
class FixConfig:
    label: str
    phrase: str
    action: str
    effect: str
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
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_events: list[str] = []

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
            self.trace_events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.harbor)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    harbor: str
    child_gender: str
    child_name: str
    child_trait: str
    adult_role: str
    cannon: str
    fix: str
    seed: Optional[int] = None
    p: object | None = None
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


HARBORS = {
    "harbor": Harbor(place="the harbor", festival_name="the lantern fête"),
}

CHILDREN = {
    "girl": ["Mina", "Pip", "Luna", "Nia", "Ivy"],
    "boy": ["Noel", "Otto", "Finn", "Theo", "Milo"],
}

TRAITS = ["cheery", "brave", "careful", "curious", "spry"]

ADULT_ROLES = ["captain", "coach", "caretaker", "dockkeeper"]

CANNONS = {
    "festival": CannonConfig(
        label="festival cannon",
        phrase="a small festival cannon with a bright brass nose",
        loudness=3,
        smoke="puff",
        rhythm="boom-bim",
        safe=True,
    ),
    "signal": CannonConfig(
        label="signal cannon",
        phrase="a little signal cannon with a rope handle",
        loudness=4,
        smoke="puff",
        rhythm="boom",
        safe=True,
    ),
}

FIXES = {
    "apology": FixConfig(
        label="apology",
        phrase="a soft apology and a careful promise",
        action="say sorry and clean up together",
        effect="mended",
    ),
    "sharing": FixConfig(
        label="sharing",
        phrase="sharing the job and taking turns",
        action="take turns and work side by side",
        effect="smoothed",
    ),
    "cloth": FixConfig(
        label="cloth cover",
        phrase="a cloth cover to quiet the cannon",
        action="wrap the cannon and test it gently",
        effect="calmed",
    ),
}

# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
class NWorld(World):
    pass


def _rhyming_opening(child: Entity, adult: Entity, harbor: Harbor) -> str:
    return (
        f"At {harbor.place}, where gulls would glide, "
        f"{child.id} and {adult.label} stood side by side."
    )


def _rhyming_cannon_line(cannon: CannonConfig) -> str:
    return f"The {cannon.label} waited by the dock, all polished bright and sure as rock."


def _rhyming_happy_line(child: Entity) -> str:
    return f"{child.id} smiled wide, with a twinkly glow, ready for the show."


def _do_prepare(world: World, child: Entity, cannon: Entity) -> None:
    child.memes["pride"] += 1
    cannon.meters["repair"] += 1
    world.say(_rhyming_opening(child, world.get("adult"), world.harbor))
    world.say(_rhyming_cannon_line(_safe_lookup(CANNONS, cannon.type)))
    world.say(f"{child.id} helped polish it with care, so everything could sparkle there.")
    world.say(_rhyming_happy_line(child))


def _predict_misfire(world: World, child: Entity, cannon: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["worry"] += 0.0
    sim.get(cannon.id).meters["noise"] += _safe_lookup(CANNONS, cannon.type).loudness
    sim.get("adult").memes["hurt"] += 1
    return True


def _misfire(world: World, child: Entity, cannon: Entity, adult: Entity) -> None:
    sig = ("misfire", cannon.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    cannon.meters["noise"] += _safe_lookup(CANNONS, cannon.type).loudness
    cannon.meters["soot"] += 1
    adult.memes["hurt"] += 1
    child.memes["worry"] += 1
    world.say(f"Then came a sudden {_safe_lookup(CANNONS, cannon.type).rhythm}, a startled little shock.")
    world.say(f"It sent a dark gray puff of smoke puff-puffing from the dock.")
    world.say(f"{adult.label} frowned a bit; {child.id} looked small and blue, for loud mistakes can sting the mood.")


def _apologize(world: World, child: Entity, adult: Entity, fix: FixConfig) -> None:
    sig = ("reconcile", fix.label)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    adult.memes["hurt"] = max(0.0, adult.memes["hurt"] - 1)
    child.memes["reconcile"] += 1
    adult.memes["reconcile"] += 1
    adult.memes["calm"] += 1
    child.memes["calm"] += 1
    world.say(f"{child.id} took a breath and spoke with grace: \"I'm sorry for the noisy chase.\"")
    world.say(f"{adult.label} nodded slow, then soft and kind; {fix.phrase} was the fix they found.")
    world.say(f"They agreed to {fix.action}, and that made the worry fade away.")


def _resolution(world: World, child: Entity, adult: Entity, cannon: Entity, fix: FixConfig) -> None:
    child.memes["joy"] += 2
    adult.memes["joy"] += 2
    cannon.meters["repair"] += 1
    cannon.meters["noise"] = max(0.0, cannon.meters["noise"] - 2)
    world.say(f"{fix.effect} at last, the little cannon could try again, but gently this time, bright and plain.")
    world.say(f"This time it gave a tidy boom, like a drum in a room, and the festival light filled the afternoon.")
    world.say(f"{child.id} and {adult.label} shared a grin; the heavy mood had slipped right in and out again.")
    world.say(f"So the harbor felt warm, and the lesson was clear: when hearts repair, joy draws near.")


def tell(harbor: Harbor, child_cfg: CharacterConfig, cannon_cfg: CannonConfig, fix_cfg: FixConfig) -> World:
    world = NWorld(harbor)
    child = world.add(Entity(
        id=child_cfg.name,
        kind="character",
        type=child_cfg.gender,
        label=child_cfg.name,
        phrase=child_cfg.trait,
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=child_cfg.gender if child_cfg.gender in {"girl", "boy"} else "man",
        label=child_cfg.role,
        phrase=child_cfg.role,
    ))
    cannon = world.add(Entity(
        id="cannon",
        kind="thing",
        type="cannon",
        label=cannon_cfg.label,
        phrase=cannon_cfg.phrase,
        is_tool=True,
        is_precious=True,
    ))
    cannon.type = cannon_cfg.label

    world.say(f"{child.id} was a {child_cfg.trait} child who loved the harbor day.")
    world.say(f"{child.id} knew the {cannon_cfg.label} would cheer the crowd away.")
    world.say(f"The {adult.label} said, \"Let's keep it safe and tidy, so the boom will sound just right and bright.\"")
    world.para()

    _do_prepare(world, child, cannon)
    world.para()

    _misfire(world, child, cannon, adult)
    world.para()

    _apologize(world, child, adult, fix_cfg)
    _resolution(world, child, adult, cannon, fix_cfg)

    world.facts.update(
        child=child,
        adult=adult,
        cannon=cannon,
        fix=fix_cfg,
        harbor=harbor,
        misfire=True,
        reconciled=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    adult: Entity = _safe_fact(world, f, "adult")
    cannon = _safe_fact(world, f, "cannon")
    return [
        f'Write a short rhyming story for young children about {child.id}, a {cannon.label}, and a problem that ends in reconciliation.',
        f"Tell a gentle harbor tale where {child.id} helps {adult.label} with a {cannon.label}, makes a mistake, and then makes it right.",
        f'Write a child-friendly story that includes the word "cannon" and ends with everyone feeling calm again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    adult: Entity = _safe_fact(world, f, "adult")
    cannon: Entity = _safe_fact(world, f, "cannon")
    fix: FixConfig = _safe_fact(world, f, "fix")
    return [
        QAItem(
            question=f"What did {child.id} help prepare at the harbor?",
            answer=f"{child.id} helped prepare the {cannon.label} for the festival at the harbor.",
        ),
        QAItem(
            question=f"What went wrong when the {cannon.label} was used?",
            answer=f"It made a sudden loud boom, sent out a puff of smoke, and made {adult.label} feel hurt for a moment.",
        ),
        QAItem(
            question=f"How did {child.id} and {adult.label} make peace again?",
            answer=f"They reconciled by apologizing, calming down, and trying again gently with {fix.phrase}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "cannon": [
        QAItem(
            question="What is a cannon?",
            answer="A cannon is a device that makes a strong boom when it is used, and it has to be handled carefully.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who had a problem make peace again and feel friendly once more.",
        )
    ],
    "harbor": [
        QAItem(
            question="What is a harbor?",
            answer="A harbor is a safe place near water where boats can stop and people can work or visit.",
        )
    ],
    "smoke": [
        QAItem(
            question="What is smoke?",
            answer="Smoke is a gray cloud made by something burning or by a puff from an engine or device.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    return [
        WORLD_KNOWLEDGE["cannon"][0],
        WORLD_KNOWLEDGE["reconciliation"][0],
        WORLD_KNOWLEDGE["harbor"][0],
        WORLD_KNOWLEDGE["smoke"][0],
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combo(cannon_key: str, fix_key: str) -> bool:
    return cannon_key in CANNONS and fix_key in FIXES


def explain_rejection(cannon_key: str, fix_key: str) -> str:
    return f"(No story: the combination cannon={cannon_key!r} and fix={fix_key!r} is not available in this world.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts describe available canons and fixes.
valid_cannon(C) :- cannon(C).
valid_fix(F) :- fix(F).

% A story is valid when it has a cannon and a reconciliation fix.
valid_story(C, F) :- valid_cannon(C), valid_fix(F), can_reconcile(C, F).

can_reconcile(C, F) :- cannon(C), fix(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CANNONS:
        lines.append(asp.fact("cannon", cid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = sorted((c, f) for c in CANNONS for f in FIXES if valid_combo(c, f))
    cl = asp_valid_stories()
    if cl == py:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python:", py)
    print("clingo:", cl)
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming cannon story with reconciliation.")
    ap.add_argument("--harbor", choices=HARBORS.keys())
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-trait", choices=TRAITS)
    ap.add_argument("--adult-role", choices=ADULT_ROLES)
    ap.add_argument("--cannon", choices=CANNONS.keys())
    ap.add_argument("--fix", choices=FIXES.keys())
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
    cannon_key = getattr(args, "cannon", None) or rng.choice(list(CANNONS))
    fix_key = getattr(args, "fix", None) or rng.choice(list(FIXES))
    if not valid_combo(cannon_key, fix_key):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "child_gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "child_name", None) or rng.choice(CHILDREN[gender])
    trait = getattr(args, "child_trait", None) or rng.choice(TRAITS)
    role = getattr(args, "adult_role", None) or rng.choice(ADULT_ROLES)
    return StoryParams(
        harbor=getattr(args, "harbor", None) or "harbor",
        child_gender=gender,
        child_name=name,
        child_trait=trait,
        adult_role=role,
        cannon=cannon_key,
        fix=fix_key,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(HARBORS, params.harbor),
        CharacterConfig(
            name=params.child_name,
            gender=params.child_gender,
            role=params.adult_role,
            trait=params.child_trait,
        ),
        _safe_lookup(CANNONS, params.cannon),
        _safe_lookup(FIXES, params.fix),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for c in CANNONS:
            for f in FIXES:
                if valid_combo(c, f):
                    p = StoryParams(
                        harbor="harbor",
                        child_gender="girl",
                        child_name="Mina",
                        child_trait="curious",
                        adult_role="captain",
                        cannon=c,
                        fix=f,
                    )
                    samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
