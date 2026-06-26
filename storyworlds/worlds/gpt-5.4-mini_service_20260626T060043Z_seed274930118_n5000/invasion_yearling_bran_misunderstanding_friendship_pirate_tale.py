#!/usr/bin/env python3
"""
A standalone storyworld for a small pirate-tale misunderstanding: a dockside
"invansion" rumor, a yearling in danger of being blamed, and a sack of bran
that turns a frightened mistake into friendship.

Seed-image premise:
- A pirate crew comes to a quiet harbor.
- A young yearling and a sack of bran are mistaken for part of an invasion plot.
- The misunderstanding is cleared when the characters talk and help each other.
- The ending proves the change through a shared, peaceful image.

The world models physical meters and emotional memes:
- meters: danger, damage, noise, hunger, wetness, distance
- memes: fear, trust, suspicion, friendship, relief, pride

This file follows the Storyweavers world contract:
- build_parser, resolve_params, generate, emit, main
- QAItem, StoryError, StorySample imported eagerly from results
- ASP helpers imported lazily in ASP functions
- inline ASP_RULES twin of the Python reasonableness gate
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bran: object | None = None
    hero: object | None = None
    pirate: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Setting:
    place: str = "the harbor"
    setting_kind: str = "dockside"
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
class Event:
    id: str
    label: str
    verb: str
    suspicion: str
    danger: str
    misunderstanding: str
    resolution: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "cargo"
    plural: bool = False
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


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.event_in_play: Optional[str] = None

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.event_in_play = self.event_in_play
        return clone


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.meme("suspicion") < THRESHOLD:
            continue
        sig = ("misunderstanding", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["fear"] = ch.meme("fear") + 1
        out.append(f"{ch.label or ch.id} backed away, thinking the danger was for real.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.meme("trust") < THRESHOLD or ch.meme("fear") < THRESHOLD:
            continue
        sig = ("friendship", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["friendship"] = ch.meme("friendship") + 1
        ch.memes["relief"] = ch.meme("relief") + 1
        out.append(f"The worry loosened, and {ch.label or ch.id} found a new friend.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_misunderstanding, _r_friendship):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_misunderstanding(world: World, actor: Entity, event: Event, prize_id: str) -> dict:
    sim = world.copy()
    do_event(sim, sim.get(actor.id), event, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "misunderstood": bool(prize and prize.meme("suspicion") >= THRESHOLD),
        "fear": sum(e.meme("fear") for e in sim.characters()),
    }


def do_event(world: World, actor: Entity, event: Event, narrate: bool = True) -> None:
    world.event_in_play = event.id
    actor.meters["noise"] = actor.meter("noise") + 1
    actor.memes["pride"] = actor.meme("pride") + 1
    if event.id == "invasion":
        for ent in list(world.entities.values()):
            if ent.kind == "thing" and ent.type in {"bran_sack", "basket", "flag"}:
                ent.memes["suspicion"] = ent.meme("suspicion") + 1
    propagate(world, narrate=narrate)


def tell_story(world: World, hero: Entity, friend: Entity, prize: Entity, event: Event, gear: Gear) -> None:
    world.say(
        f"At {world.setting.place}, {hero.label} the yearling noticed a strange {event.label} on the pier."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was young, quick-footed, and full of questions; the smell of {prize.label} was on the wind."
    )
    world.say(
        f"{friend.label} the pirate had come in laughing, but {hero.label} heard the word '{event.label}' and thought it meant trouble."
    )

    world.para()
    world.say(
        f"The harbor looked busy, and {hero.label} thought the crew might be planning an invasion."
    )
    world.say(
        f"{hero.label} pointed at the {prize.label} and backed away, while {friend.label} frowned at the alarm."
    )
    hero.memes["suspicion"] += 1
    do_event(world, friend, event, narrate=True)
    world.say(
        f"The fear made the little yearling's hooves drum on the boards, and the sack of {prize.label} tipped over."
    )

    world.para()
    world.say(
        f"Then {friend.label} knelt down and explained that the noisy crew was only unloading food and rope, not starting a fight."
    )
    hero.memes["trust"] += 1
    hero.memes["fear"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{friend.label} offered {hero.label} a handful of {prize.label}, and the yearling softened at once."
    )
    world.say(
        f"To help fix the mess, {hero.label} nosed the spilled {prize.label} into a neat pile, and {friend.label} tied the sack closed with a grin."
    )

    world.para()
    hero.memes["friendship"] += 1
    hero.memes["relief"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"By sunset, the dock was calm again."
    )
    world.say(
        f"{hero.label} stood beside {friend.label}, sharing the last little bits of {prize.label}, and the supposed invasion had become a new friendship instead."
    )
    world.say(
        f"The yearling's ears were relaxed, and the pirate's hand rested gently on the rail while the harbor glowed gold."
    )


SETTINGS = {
    "harbor": Setting(place="the harbor", setting_kind="dockside", affords={"invasion"}),
    "pier": Setting(place="the pier", setting_kind="dockside", affords={"invasion"}),
    "islet": Setting(place="the little islet", setting_kind="shore", affords={"invasion"}),
}

EVENTS = {
    "invasion": Event(
        id="invasion",
        label="invasion",
        verb="sail in noisily",
        suspicion="suspicion",
        danger="danger",
        misunderstanding="misunderstanding",
        resolution="friendship",
        tags={"invasion", "pirate"},
    ),
}

PRIZES = {
    "bran": Prize(
        label="bran",
        phrase="a sack of bran",
        type="bran_sack",
        region="cargo",
        tags={"bran", "food"},
    ),
    "rope": Prize(
        label="rope",
        phrase="a coil of rope",
        type="rope_coil",
        region="cargo",
        tags={"rope", "ship"},
    ),
}

GEAR = [
    Gear(
        id="quiet_brag",
        label="a quiet story",
        prep="explain what the crew was really doing",
        tail="sat down and listened until the misunderstanding faded",
        guards={"misunderstanding"},
        covers={"ears"},
    ),
    Gear(
        id="shared_bran",
        label="shared bran",
        prep="offer a little bran as a peace gift",
        tail="shared the bran while the dock grew calm",
        guards={"misunderstanding", "fear"},
        covers={"cargo"},
    ),
]

HERO_NAMES = ["Mabel", "Tobin", "Junie", "Rowan", "Pip", "Nell", "Bram"]
PIRATE_NAMES = ["Captain Reed", "Sailor Tansy", "Old Hook", "Mira the Mate", "Sly Finn"]


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    hero: str
    pirate: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for event in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, event, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that uses the words "{f["event"].label}", "{f["hero"].label}", and "{f["prize"].label}".',
        f"Tell a short story where {f['pirate'].label} seems like a threat, but the young yearling {f['hero'].label} discovers a misunderstanding about {f['prize'].label}.",
        f"Write a gentle dockside story that begins with an invasion scare and ends with friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    pirate = _safe_fact(world, f, "pirate")
    prize = _safe_fact(world, f, "prize")
    event = _safe_fact(world, f, "event")
    return [
        QAItem(
            question=f"Who was the young yearling in the story?",
            answer=f"The young yearling was {hero.label}. {hero.label} first thought the {event.label} meant danger, but later learned it was a misunderstanding.",
        ),
        QAItem(
            question=f"What did {hero.label} think the pirates were doing at {world.setting.place}?",
            answer=f"{hero.label} thought the pirates were starting an invasion, because the dock was loud and busy.",
        ),
        QAItem(
            question=f"What turned the scare into friendship?",
            answer=f"{pirate.label} explained the truth and shared {prize.label}, so the misunderstanding faded and friendship grew.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} and {pirate.label} calm together at {world.setting.place}, sharing {prize.label} and feeling friendly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yearling?",
            answer="A yearling is a young animal that is about one year old.",
        ),
        QAItem(
            question="What is bran?",
            answer="Bran is the outer part of grain, often used as food for animals or mixed into baking.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what is going on.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people or animals care about each other and act kindly together.",
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
        lines.append(f"  {e.id:10} ({e.type:10}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "event", None) and getattr(args, "prize", None):
        if getattr(args, "event", None) not in EVENTS or getattr(args, "prize", None) not in PRIZES:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event, prize = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    pirate = getattr(args, "pirate", None) or rng.choice(PIRATE_NAMES)
    return StoryParams(place=place, event=event, prize=prize, hero=hero, pirate=pirate)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    event = _safe_lookup(EVENTS, params.event)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="character", type="yearling", label=params.hero,
        meters={"fear": 0.0, "trust": 0.0, "friendship": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "friendship": 0.0, "suspicion": 0.0},
    ))
    pirate = world.add(Entity(
        id="pirate", kind="character", type="pirate", label=params.pirate,
        meters={"noise": 0.0},
        memes={"pride": 0.0, "trust": 0.0},
    ))
    bran = world.add(Entity(
        id="bran", type=prize.type, label=prize.label, phrase=prize.phrase,
        owner=pirate.id, caretaker=pirate.id, plural=prize.plural,
        meters={}, memes={"suspicion": 0.0},
    ))

    world.facts.update(hero=hero, pirate=pirate, prize=bran, event=event, setting=setting)

    tell_story(world, hero, pirate, bran, event, GEAR[1])

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


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        for t in sorted(e.tags):
            lines.append(asp.fact("tag", eid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gk in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gk))
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(E) :- event(E), tag(E, invasion).
friendship(G) :- gear(G), guards(G, misunderstanding).
valid_story(P, E, PR) :- affords(P, E), event(E), prize(PR), misunderstanding(E).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with an invasion misunderstanding and friendship.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--event", choices=sorted(EVENTS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--hero")
    ap.add_argument("--pirate")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for t in combos:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="harbor", event="invasion", prize="bran", hero="Mabel", pirate="Captain Reed"),
            StoryParams(place="pier", event="invasion", prize="rope", hero="Pip", pirate="Sailor Tansy"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
