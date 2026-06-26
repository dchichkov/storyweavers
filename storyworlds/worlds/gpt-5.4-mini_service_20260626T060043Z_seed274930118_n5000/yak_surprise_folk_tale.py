#!/usr/bin/env python3
"""
storyworlds/worlds/yak_surprise_folk_tale.py
===========================================

A small folk-tale storyworld about a yak, a surprising discovery, and a gentle
turn toward sharing.

Premise:
- A child or villager cares for a yak in a mountain meadow.
- The yak is dear, sturdy, and useful, but a surprise interrupts the day.
- The surprise is not random noise in prose; it is a world state: a hidden
  object, a mistaken expectation, or an unexpected guest.

Tension:
- Someone expects one thing and finds another.
- The yak's path, load, or basket changes the state of the world.
- A helper or elder notices the surprise and reacts.

Turn:
- The surprise is explained or used well.
- The yak helps reveal a lost item, a visitor, or a gift.
- The story resolves with warmth, wonder, and a concrete final image.

This world keeps the tale close to a folk-story cadence: simple actions, a
clear object of value, a surprise in the middle, and a closing image that proves
the change.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    elder: object | None = None
    gift: object | None = None
    surprise: object | None = None
    yak: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        return mapping[case]

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
    place: str
    detail: str
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
class Surprise:
    id: str
    label: str
    reveal: str
    phrase: str
    kind: str
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
class Gift:
    id: str
    label: str
    phrase: str
    region: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(
        place="the mountain meadow",
        detail="The grass was soft, and the wind moved like a quiet song.",
        affords={"carry", "search", "walk"},
    ),
    "village": Setting(
        place="the village path",
        detail="The path wound past low fences and warm chimneys.",
        affords={"carry", "search", "walk"},
    ),
    "riverbank": Setting(
        place="the riverbank",
        detail="The water sang over stones and reeds nodded in the breeze.",
        affords={"carry", "search", "walk"},
    ),
}

SURPRISES = {
    "bell": Surprise(
        id="bell",
        label="a small silver bell",
        reveal="rang softly from the yak's pack",
        phrase="a small silver bell wrapped in cloth",
        kind="gift",
        tags={"bell", "gift", "sound"},
    ),
    "lamb": Surprise(
        id="lamb",
        label="a lost lamb",
        reveal="peeked out from behind the yak",
        phrase="a woolly little lamb",
        kind="visitor",
        tags={"lamb", "animal", "found"},
    ),
    "map": Surprise(
        id="map",
        label="a folded map",
        reveal="slipped from beneath the yak's saddle blanket",
        phrase="a folded map with a red cross",
        kind="clue",
        tags={"map", "lost", "find"},
    ),
    "cake": Surprise(
        id="cake",
        label="a honey cake",
        reveal="waited inside the basket tied to the yak",
        phrase="a honey cake in a round basket",
        kind="gift",
        tags={"cake", "gift", "sweet"},
    ),
}

GIFTS = {
    "scarf": Gift(
        id="scarf",
        label="a blue scarf",
        phrase="a blue scarf with tassels",
        region="neck",
    ),
    "bells": Gift(
        id="bells",
        label="a ribbon of bells",
        phrase="a ribbon of bells for the harness",
        region="back",
        plural=False,
    ),
    "bread": Gift(
        id="bread",
        label="fresh bread",
        phrase="fresh bread wrapped in linen",
        region="back",
        plural=False,
    ),
}

PEOPLE = {
    "child": ["Mira", "Pavel", "Anya", "Oren", "Lina", "Toma"],
    "elder": ["Grandmother", "Grandfather", "Auntie", "Uncle"],
}

TRAITS = ["gentle", "curious", "brave", "kind", "quiet", "cheerful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    surprise: str
    gift: str
    name: str
    elder: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
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


def surprise_is_reasonable(setting: Setting, surprise: Surprise) -> bool:
    return "search" in setting.affords and surprise.id in SURPRISES


def gift_is_reasonable(gift: Gift) -> bool:
    return gift.id in GIFTS


def explain_rejection(setting: Setting, surprise: Surprise) -> str:
    return f"(No story: {setting.place} does not support a folk-tale surprise like {surprise.label}.)"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"joy": 1.0},
        memes={"wonder": 1.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type="elder",
        label=params.elder,
        meters={"care": 1.0},
        memes={"calm": 1.0},
    ))
    yak = world.add(Entity(
        id="yak",
        kind="character",
        type="yak",
        label="the yak",
        meters={"strength": 2.0, "weight": 2.0},
        memes={"patience": 1.0},
        owner=child.id,
        caretaker=elder.id,
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=_safe_lookup(GIFTS, params.gift).label,
        phrase=_safe_lookup(GIFTS, params.gift).phrase,
        owner=elder.id,
        caretaker=elder.id,
        plural=_safe_lookup(GIFTS, params.gift).plural,
    ))
    surprise = world.add(Entity(
        id="surprise",
        kind="thing",
        type="surprise",
        label=_safe_lookup(SURPRISES, params.surprise).label,
        phrase=_safe_lookup(SURPRISES, params.surprise).phrase,
        owner=yak.id,
        caretaker=child.id,
    ))
    world.facts.update(child=child.id, elder=elder.id, yak=yak.id, gift=gift.id, surprise=surprise.id)
    return world


def intro(world: World, params: StoryParams) -> None:
    world.say(
        f"In {world.setting.place}, there lived a {params.trait} child named {params.name} "
        f"who loved the steady yak."
    )
    world.say(world.setting.detail)


def bond(world: World, params: StoryParams) -> None:
    yak = world.get("yak")
    yak.memes["trusted"] = yak.memes.get("trusted", 0.0) + 1.0
    world.say(
        f"{params.name} brushed the yak each morning, and the yak lowered its great head "
        f"as if it knew a kind friend had come."
    )


def set_out(world: World, params: StoryParams) -> None:
    world.say(
        f"One clear day, {params.name} and {params.elder} led the yak along the path, "
        f"carrying the small gift for a neighbor."
    )


def surprise_turn(world: World, params: StoryParams) -> None:
    surprise = world.get("surprise")
    world.say(
        f"Then came a surprise: {surprise.reveal}."
    )
    if surprise.id == "lamb":
        world.get("yak").memes["alert"] = 1.0
        world.say(
            f"The yak had stopped beside a thicket, and there the little lamb shivered, "
            f"too afraid to bleat."
        )
    elif surprise.id == "map":
        world.get("yak").meters["find"] = 1.0
        world.say(
            f"The yak had pawed at the earth, and the map was hidden where the grass was flat."
        )
    elif surprise.id == "bell":
        world.get("yak").memes["playful"] = 1.0
        world.say(
            f"The bell had been tied to the yak's harness all along, waiting for the right moment to sing."
        )
    elif surprise.id == "cake":
        world.get("yak").meters["carry"] = 1.0
        world.say(
            f"The basket had been kept safe against the yak's warm side, and the honey cake was still whole."
        )


def resolve(world: World, params: StoryParams) -> None:
    surprise = world.get("surprise")
    child = world.get(params.name)
    elder = world.get("elder")
    if surprise.id == "lamb":
        world.say(
            f"{params.name} and {params.elder} guided the lamb home, and the yak walked slow and proud behind them."
        )
    elif surprise.id == "map":
        world.say(
            f"The map showed the way to a lost jar of seeds, so the family followed it and found the hidden box."
        )
    elif surprise.id == "bell":
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
        world.say(
            f"{params.name} laughed when the bell rang, and {params.elder} tied it so it would sing only on festival nights."
        )
    elif surprise.id == "cake":
        child.meters["sated"] = 1.0
        world.say(
            f"They shared the honey cake beside the riverbank, and the yak ate the last crumbs from {params.elder}'s palm."
        )
    world.para()
    world.say(
        f"By dusk, the yak stood beneath the evening sky, and the surprise had become a warm story to tell."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts
    surprise = world.get("surprise").label
    return [
        f"Write a short folk tale about a yak and a surprise called {surprise}.",
        f"Tell a gentle mountain story where {p['child']} leads a yak and discovers an unexpected {surprise}.",
        f"Write a child-friendly tale with a yak, an elder, and a surprising turn that ends in kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get(next(k for k in world.facts.keys() if k not in {"elder", "yak", "gift", "surprise"}))
    elder = world.get("elder")
    yak = world.get("yak")
    surprise = world.get("surprise")
    qs = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.label}, {elder.label}, and the steady yak they care for together.",
        ),
        QAItem(
            question=f"What was the surprise?",
            answer=f"The surprise was {surprise.label}, and it {surprise.reveal}.",
        ),
        QAItem(
            question=f"How did the surprise change the day?",
            answer=f"It turned an ordinary walk into a kinder adventure, because the yak helped reveal what had been hidden or needed help.",
        ),
        QAItem(
            question=f"What did the yak do at the end?",
            answer=f"The yak stood calmly with the others, and the surprise had become part of a happy memory.",
        ),
    ]
    if surprise.id == "lamb":
        qs.append(QAItem(
            question="Why did the child and elder slow down on the path?",
            answer="They slowed down because they found a frightened lamb and wanted to guide it safely home.",
        ))
    elif surprise.id == "map":
        qs.append(QAItem(
            question="Why did the family keep following the map?",
            answer="They kept following it because it showed a useful way to find a lost thing hidden nearby.",
        ))
    elif surprise.id == "bell":
        qs.append(QAItem(
            question="Why did the bell matter to the story?",
            answer="The bell mattered because it made a gentle sound and turned the yak into a tiny festival surprise.",
        ))
    elif surprise.id == "cake":
        qs.append(QAItem(
            question="Why was the cake special?",
            answer="It was special because it stayed safe in the basket and became a shared treat at the end of the walk.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    surprise = world.get("surprise")
    yak = world.get("yak")
    items = [
        QAItem(
            question="What is a yak?",
            answer="A yak is a strong, shaggy animal that can live in cold mountain places and carry things on its back.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes people stop, look again, and feel wonder or joy.",
        ),
    ]
    if surprise.id == "bell":
        items.append(QAItem(
            question="What does a bell do?",
            answer="A bell makes a ringing sound when it moves or is struck, so people can hear it from far away.",
        ))
    if surprise.id == "map":
        items.append(QAItem(
            question="What is a map for?",
            answer="A map shows where things are and helps people find a place or a path.",
        ))
    if surprise.id == "cake":
        items.append(QAItem(
            question="Why do people share cake?",
            answer="People share cake to celebrate, to be kind, and to make a happy moment feel special.",
        ))
    return items


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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(P, S, G) :- place(P), surprise(S), gift(G), afford(P, search), surprise_ok(S), gift_ok(G).
valid_story(P, S, G, C) :- valid(P, S, G), child(C).

surprise_ok(bell).
surprise_ok(lamb).
surprise_ok(map).
surprise_ok(cake).

gift_ok(scarf).
gift_ok(bells).
gift_ok(bread).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in sorted(_safe_lookup(SETTINGS, p).affords):
            lines.append(asp.fact("afford", p, a))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for c in PEOPLE["child"]:
        lines.append(asp.fact("child", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "search" not in setting.affords:
            continue
        for sid in SURPRISES:
            for gid in GIFTS:
                combos.append((place, sid, gid))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about a yak and a surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=sorted(set(PEOPLE["elder"])))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    setting = _safe_lookup(SETTINGS, place)
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    gift = getattr(args, "gift", None) or rng.choice(list(GIFTS))
    if getattr(args, "place", None) and getattr(args, "surprise", None) and not surprise_is_reasonable(setting, _safe_lookup(SURPRISES, surprise)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gift", None) and not gift_is_reasonable(_safe_lookup(GIFTS, getattr(args, "gift", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(PEOPLE["child"])
    elder = getattr(args, "elder", None) or rng.choice(PEOPLE["elder"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, surprise=surprise, gift=gift, name=name, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    intro(world, params)
    world.para()
    bond(world, params)
    set_out(world, params)
    surprise_turn(world, params)
    world.para()
    resolve(world, params)
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
    StoryParams(place="meadow", surprise="lamb", gift="scarf", name="Mira", elder="Grandmother", trait="gentle"),
    StoryParams(place="village", surprise="bell", gift="bells", name="Pavel", elder="Auntie", trait="curious"),
    StoryParams(place="riverbank", surprise="map", gift="bread", name="Anya", elder="Uncle", trait="brave"),
    StoryParams(place="meadow", surprise="cake", gift="scarf", name="Lina", elder="Grandfather", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, surprise, gift) combos ({len(stories)} with child):\n")
        for place, surprise, gift in triples:
            children = sorted(c for (p, s, g, c) in stories if (p, s, g) == (place, surprise, gift))
            print(f"  {place:10} {surprise:8} {gift:8}  [{', '.join(children)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
