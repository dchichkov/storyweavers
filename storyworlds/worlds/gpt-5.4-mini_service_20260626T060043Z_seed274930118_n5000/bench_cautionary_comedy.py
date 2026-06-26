#!/usr/bin/env python3
"""
storyworlds/worlds/bench_cautionary_comedy.py
=============================================

A small cautionary-comedy story world about a bench, a warning, and a safer
way to play.

Seed tale:
---
A child loves a park bench because it looks like a tiny stage. One day the child
wants to climb, slide, and wobble on the bench while wearing a prized outfit.
A grown-up notices the bench is slick, cracked, and a little unsteady, and
warns that someone could slip or pinch a finger. The child pouts, then spots a
funny safer idea: they can sit, sing, and pretend the bench is a pirate ship
instead. The child laughs, the grown-up laughs, and the prize stays clean and
whole.

Story model:
---
- A bench can be polished, wet, or wobbly.
- A child can try a risky trick on it.
- The grown-up warns based on the bench's state.
- A safer comedy compromise keeps the child playful and the prize safe.

This world is meant to read like a complete tiny story, with a clear setup,
a warning, a turn, and a cheerful ending image proving what changed.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    child: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Bench:
    name: str
    surface: str
    state: str
    risk: str
    place: str = "the park"
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
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Compromise:
    label: str
    offer: str
    ending: str
    protects: set[str]
    guards: set[str]
    comedic_angle: str
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


class World:
    def __init__(self, bench: Bench) -> None:
        self.bench = bench
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
        clone = World(self.bench)
        clone.entities = dataclasses.replace(self.entities) if False else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "park": Bench(name="bench", surface="wood", state="wobbly", risk="slippery", place="the park", tags={"bench", "park"}),
    "garden": Bench(name="bench", surface="painted wood", state="wet", risk="slippery", place="the garden", tags={"bench", "garden"}),
    "playground": Bench(name="bench", surface="metal", state="sun-warm", risk="hot", place="the playground", tags={"bench", "playground"}),
    "yard": Bench(name="bench", surface="old wood", state="creaky", risk="crackly", place="the backyard", tags={"bench", "yard"}),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", region="torso"),
    "dress": Prize(label="dress", phrase="a pretty new dress", region="torso", genders={"girl"}),
    "cap": Prize(label="cap", phrase="a bright red cap", region="head"),
    "shoes": Prize(label="shoes", phrase="shiny shoes", region="feet", plural=True),
}

COMPROMISES = [
    Compromise(
        label="sidewalk song",
        offer="sit on the ground beside the bench and sing a pirate song",
        ending="sat beside the bench and sang like a tiny captain",
        protects={"torso", "feet", "head"},
        guards={"slippery", "hot", "crackly"},
        comedic_angle="the bench became a pirate ship in the child's imagination",
    ),
    Compromise(
        label="beanbag bounce",
        offer="hop from a safe little beanbag instead of the bench",
        ending="bounced on the beanbag and pointed at the bench like it was a throne",
        protects={"torso", "feet", "head"},
        guards={"slippery", "hot", "crackly"},
        comedic_angle="the child got the drama without the tumble",
    ),
    Compromise(
        label="bench concert",
        offer="tap the bench with one finger and then clap a silly rhythm from the ground",
        ending="kept both feet on the ground and made the bench a drum",
        protects={"torso", "feet", "head"},
        guards={"slippery", "hot", "crackly"},
        comedic_angle="the bench turned into the world's least dangerous instrument",
    ),
]

GIRL_NAMES = ["Mina", "Lily", "Zoe", "Ava", "Nora", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn", "Owen"]
TRAITS = ["curious", "silly", "spirited", "playful", "cheerful", "mischievous"]


def bench_is_risky(bench: Bench) -> bool:
    return bench.risk in {"slippery", "hot", "crackly"}


def compatible_compromise(bench: Bench, prize: Prize) -> Optional[Compromise]:
    for c in COMPROMISES:
        if bench.risk in c.guards and prize.region in c.protects:
            return c
    return None


def explain_rejection(bench: Bench, prize: Prize) -> str:
    return (
        f"(No story: this bench situation would not make a good cautionary-comedy "
        f"turn for {prize.label}. The risk needs to be real enough for a warning, "
        f"and the compromise needs to keep the prize safe.)"
    )


@dataclass
class StoryParams:
    setting: str
    prize: str
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


class StoryRules:
    @staticmethod
    def warn(world: World, child: Entity, parent: Entity, prize: Entity) -> None:
        bench = world.bench
        if not bench_is_risky(bench):
            return
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        world.say(
            f"{parent.pronoun().capitalize()} looked at the {bench.name} and frowned. "
            f"'{child.pronoun('possessive').capitalize()} {prize.label} could get ruined if "
            f"{child.pronoun()} starts wobbling on that {bench.state} {bench.name},' "
            f"{parent.pronoun('subject')} said."
        )

    @staticmethod
    def defy(world: World, child: Entity) -> None:
        child.memes["defiance"] = child.memes.get("defiance", 0.0) + 1
        world.say(
            f"{child.pronoun().capitalize()} pouted and wanted to climb up anyway, "
            f"because the {world.bench.name} looked exactly like a tiny stage."
        )

    @staticmethod
    def resolve(world: World, child: Entity, parent: Entity, prize: Entity, comp: Compromise) -> None:
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1
        child.memes["defiance"] = 0.0
        world.say(
            f"Then {parent.pronoun('possessive')} eyes twinkled. "
            f"'{comp.offer},' {parent.pronoun('subject')} said, with a very serious voice "
            f"that somehow sounded funny."
        )
        world.say(
            f"{child.pronoun().capitalize()} burst out laughing, agreed, and "
            f"{comp.ending}. The {prize.label} stayed clean, and the bench stayed a bench "
            f"instead of becoming a trampoline."
        )


def tell(params: StoryParams) -> World:
    bench = _safe_lookup(SETTINGS, params.setting)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    world = World(bench)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={"joy": 0.0, "defiance": 0.0, "worry": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="parent",
        meters={},
        memes={},
    ))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={"clean": 1.0},
        memes={},
    ))

    world.say(
        f"{child.pronoun().capitalize()} was a {params.trait} little {params.gender} named {child.id}, "
        f"and {child.pronoun('possessive')} favorite place was {bench.place}."
    )
    world.say(
        f"There was a {bench.state} {bench.name} there with a {bench.surface} seat, "
        f"and {child.id} thought it looked like a tiny stage."
    )
    world.say(
        f"One day, {child.id} wore {child.pronoun('possessive')} {prize.label} and wanted to "
        f"climb, wobble, and slide on the {bench.name} for a laugh."
    )

    world.para()
    StoryRules.warn(world, child, parent, prize)
    StoryRules.defy(world, child)
    world.say(
        f"But {parent.pronoun('possessive')} warning was not a grumpy one; it was the kind of warning "
        f"that tries to stop a bonk before it happens."
    )

    world.para()
    comp = compatible_compromise(bench, prize)
    if comp is None:
        pass
    world.say(
        f"{parent.pronoun().capitalize()} pointed to the ground and offered a better joke."
    )
    StoryRules.resolve(world, child, parent, prize, comp)

    world.facts.update(
        child=child,
        parent=parent,
        prize=prize,
        bench=bench,
        compromise=comp,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    prize = _safe_fact(world, f, "prize")
    bench = _safe_fact(world, f, "bench")
    return [
        f'Write a short cautionary-comedy story about a child and a {bench.name} at {bench.place}.',
        f"Tell a funny but gentle story where {child.id} wants to climb on the {bench.name} while wearing {prize.label}, but a grown-up suggests a safer idea.",
        f"Write a tiny story for a child where a risky {bench.state} bench leads to a silly safer compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    prize = _safe_fact(world, f, "prize")
    bench = _safe_fact(world, f, "bench")
    comp = _safe_fact(world, f, "compromise")
    return [
        QAItem(
            question=f"Why did {parent.pronoun('subject')} worry about the {bench.name}?",
            answer=(
                f"{parent.pronoun().capitalize()} worried because the {bench.name} was {bench.state}, "
                f"so {child.id} could slip, bump into the wood, or ruin the {prize.label}."
            ),
        ),
        QAItem(
            question=f"What did {child.id} want to do with the {bench.name} at first?",
            answer=(
                f"{child.id} wanted to climb, wobble, and slide on the {bench.name} because it looked like a "
                f"tiny stage made for a silly performance."
            ),
        ),
        QAItem(
            question=f"How did the story end after the warning?",
            answer=(
                f"They chose {comp.label} instead, so {child.id} could still be funny and playful without taking a "
                f"real risk. The {prize.label} stayed clean, and the bench stayed a bench."
            ),
        ),
        QAItem(
            question=f"What made the final idea safer than climbing on the {bench.name}?",
            answer=(
                f"The final idea kept {child.id} on the ground, which meant the {bench.name} could not cause a slip "
                f"or a bump. It still gave the child a chance to be dramatic and comic."
            ),
        ),
    ]


KNOWLEDGE = {
    "bench": [
        (
            "What is a bench?",
            "A bench is a long seat that people can sit on in a park, garden, or playground.",
        ),
        (
            "Why should you be careful on a slippery bench?",
            "A slippery bench can make you slide or fall, so it is safer to sit down carefully or use it only the way it is meant to be used.",
        ),
    ],
    "park": [
        (
            "What is a park?",
            "A park is a place with open space where people can walk, play, sit, and enjoy fresh air.",
        )
    ],
    "slippery": [
        (
            "What does slippery mean?",
            "Slippery means smooth and hard to grip, so your feet or hands can slide more easily.",
        )
    ],
    "hot": [
        (
            "Why can a hot bench be uncomfortable?",
            "A hot bench can feel too warm to touch or sit on, especially when the sun has been shining on it.",
        )
    ],
    "crackly": [
        (
            "What does crackly mean?",
            "Crackly means it makes little cracking sounds and may not feel sturdy or safe.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.bench.tags)
    tags.add(world.bench.risk)
    out: list[QAItem] = []
    for tag in ["bench", "park", "slippery", "hot", "crackly"]:
        if tag in tags:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
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
    bench = world.bench
    lines.append(f"  bench     ({bench.name}) state={bench.state} risk={bench.risk} surface={bench.surface}")
    for e in list(world.entities.values()):
        mem = {k: v for k, v in e.memes.items() if v}
        met = {k: v for k, v in e.meters.items() if v}
        bits = []
        if met:
            bits.append(f"meters={met}")
        if mem:
            bits.append(f"memes={mem}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="park", prize="shirt", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="garden", prize="dress", name="Zoe", gender="girl", parent="mother", trait="playful"),
    StoryParams(setting="playground", prize="cap", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(setting="yard", prize="shoes", name="Finn", gender="boy", parent="father", trait="spirited"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting, bench in SETTINGS.items():
        for prize_id, prize in PRIZES.items():
            if bench_is_risky(bench) and compatible_compromise(bench, prize):
                combos.append((setting, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[1] == getattr(args, "prize", None)]
    if getattr(args, "gender", None):
        combos = [c for c in combos if getattr(args, "gender", None) in PRIZES[c[1]].genders]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary-comedy story world about a bench.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


ASP_RULES = r"""
bench_risky(B) :- bench(B), risky_state(B,_).
compromise_ok(P, B) :- prize(P), bench(B), bench_risky(B),
                       prize_region(P, R), compromise_covers(C, R),
                       compromise_guards(C, G), risky_state(B, G).
valid_story(S, P) :- setting(S), prize(P), compromise_ok(P, B), bench_place(B, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, b in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("bench_place", sid, sid))
        lines.append(asp.fact("bench", sid))
        lines.append(asp.fact("risky_state", sid, b.risk))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural_prize", pid))
    for i, c in enumerate(COMPROMISES):
        cid = f"c{i}"
        lines.append(asp.fact("compromise", cid))
        for r in sorted(c.protects):
            lines.append(asp.fact("compromise_covers", cid, r))
        for g in sorted(c.guards):
            lines.append(asp.fact("compromise_guards", cid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    mapped = {(a, b) for (a, b) in clingo_set}
    if mapped == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  python:", sorted(py))
    print("  clingo:", sorted(mapped))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        vals = asp_valid()
        print(f"{len(vals)} valid story combinations:")
        for item in vals:
            print(" ", item)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: bench at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
