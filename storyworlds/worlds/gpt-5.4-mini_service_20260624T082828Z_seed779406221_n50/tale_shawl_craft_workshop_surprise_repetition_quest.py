#!/usr/bin/env python3
"""
storyworlds/worlds/tale_shawl_craft_workshop_surprise_repetition_quest.py
=========================================================================

A small slice-of-life story world set in a craft workshop.

Seed premise:
- A child or maker visits a craft workshop.
- They are making a shawl for a tale night.
- Surprise interrupts the calm routine.
- Repetition appears as steady stitches, rows, or patterns.
- A Quest carries the maker through the room to find a needed piece.
- The ending proves the shawl changed, and so did the mood of the room.

The world model tracks both physical meters and emotional memes, and the prose
is driven from those state changes rather than a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    maker: object | None = None
    shawl: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
class Workshop:
    name: str = "the craft workshop"
    places: list[str] = field(default_factory=lambda: ["the shelf", "the basket", "the yarn bin", "the table", "the drawer"])
    WORKSHOP: object | None = None
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Maker:
    id: str
    type: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Shawl:
    label: str = "shawl"
    phrase: str = "a soft shawl with a calm color"
    pattern: str = "rows"
    color: str = "blue"
    material: str = "yarn"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Clue:
    id: str
    label: str
    place: str
    helps: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    def __init__(self, workshop: Workshop) -> None:
        self.workshop = workshop
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.path: list[str] = []

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
        import copy as _copy

        clone = World(self.workshop)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.path = list(self.path)
        return clone


@dataclass
class StoryParams:
    maker_name: str
    maker_type: str
    trait: str
    tale: str
    shawl_color: str
    clue: str
    seed: Optional[int] = None
    params: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


WORKSHOP = Workshop()

MAKER_TYPES = {
    "girl": ["girl", "woman"],
    "boy": ["boy", "man"],
}

TRAITS = ["careful", "curious", "patient", "gentle", "bright", "steady"]

TALES = {
    "bedtime": "bedtime tale",
    "forest": "forest tale",
    "moon": "moon tale",
    "rain": "rain tale",
}

SHAWLS = {
    "blue": Shawl(label="shawl", phrase="a soft blue shawl", pattern="rows", color="blue", material="yarn"),
    "green": Shawl(label="shawl", phrase="a soft green shawl", pattern="stripes", color="green", material="yarn"),
    "gold": Shawl(label="shawl", phrase="a warm gold shawl", pattern="dots", color="gold", material="yarn"),
}

CLUES = {
    "tape": Clue(id="tape", label="tape", place="the drawer", helps="held the edges in place"),
    "button": Clue(id="button", label="button", place="the basket", helps="could brighten the shawl"),
    "tag": Clue(id="tag", label="tag", place="the shelf", helps="named the bundle neatly"),
    "ribbon": Clue(id="ribbon", label="ribbon", place="the yarn bin", helps="tied the story bundle together"),
}

NAMES = ["Mina", "Lina", "Sage", "Noa", "Iris", "Ari", "Milo", "Eli"]


def _set_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _set_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _do_repetition(world: World, maker: Entity, shawl: Entity) -> None:
    sig = ("repeat", maker.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    _set_meter(shawl, "rows", 1)
    _set_meme(maker, "calm", 1)
    _set_meme(maker, "focus", 1)
    world.say(
        f"{maker.id} kept working in steady rows, one after another, and the shawl began to look smoother."
    )
    world.say(f"Each repeat made the edges neater and made {maker.pronoun()} feel more settled.")


def _find_clue(world: World, maker: Entity, clue: Entity) -> None:
    sig = ("quest", clue.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    _set_meme(maker, "hope", 1)
    world.path.append(clue.place)
    world.say(
        f"Then came the Quest: {maker.id} walked to {clue.place} to look for the missing {clue.label}."
    )
    world.say(f"There, {maker.id} found the {clue.label}, and it {clue.helps}.")


def _surprise(world: World, maker: Entity, shawl: Entity, clue: Entity) -> None:
    sig = ("surprise", clue.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    _set_meme(maker, "surprise", 1)
    _set_meme(maker, "worry", 1)
    _set_meter(shawl, "unfinished", 1)
    world.say(
        f"Just when the pattern was going well, a surprise popped up: the {clue.label} for the finished bow was missing."
    )
    world.say(f"{maker.id} paused beside the table and looked around the workshop with a worried face.")


def _finish(world: World, maker: Entity, shawl: Entity, clue: Entity) -> None:
    sig = ("finish", shawl.color)
    if sig in world.fired:
        return
    world.fired.add(sig)
    _set_meter(shawl, "done", 1)
    _set_meme(maker, "pride", 1)
    _set_meme(maker, "calm", 1)
    world.say(
        f"After the Quest, {maker.id} returned to the table, added the {clue.label}, and finished the shawl."
    )
    world.say(
        f"In the end, the {shawl.color} shawl lay folded on the table, and the tale was ready to be shared."
    )


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        maker = world.get("maker")
        shawl = world.get("shawl")
        clue = world.get("clue")
        if shawl.meters.get("rows", 0.0) >= THRESHOLD and "surprised" not in world.fired:
            _surprise(world, maker, shawl, clue)
            changed = True
        if shawl.meters.get("rows", 0.0) >= THRESHOLD and clue.id not in world.fired:
            _find_clue(world, maker, clue)
            changed = True
        if shawl.meters.get("rows", 0.0) >= THRESHOLD and clue.id in world.fired and "finish" not in world.fired:
            _finish(world, maker, shawl, clue)
            changed = True


def tell(params: StoryParams) -> World:
    world = World(WORKSHOP)

    maker = world.add(Entity(id="maker", kind="character", type=params.maker_type, label=params.maker_name))
    shawl_cfg = _safe_lookup(SHAWLS, params.shawl_color)
    shawl = world.add(Entity(id="shawl", type="shawl", label="shawl", phrase=shawl_cfg.phrase, owner=maker.id))
    clue_cfg = _safe_lookup(CLUES, params.clue)
    clue = world.add(Entity(id="clue", type="object", label=clue_cfg.label, phrase=clue_cfg.label))

    world.facts.update(
        maker=maker,
        shawl=shawl,
        clue=clue,
        tale=params.tale,
        workshop=WORKSHOP.name,
        trait=params.trait,
    )

    world.say(
        f"{maker.label_word} was a {params.trait} {maker.type} in the craft workshop, making {shawl_cfg.phrase} for a {_safe_lookup(TALES, params.tale)}."
    )
    world.say(
        f"{maker.id} liked the work because every row had a place, and every place had room for another careful stitch."
    )
    world.para()
    world.say(
        f"{maker.id} started the shawl and worked in repeating rows across the table."
    )
    _do_repetition(world, maker, shawl)
    propagate(world)
    world.para()
    world.say(
        f"At first, the room felt quiet, with yarn, paper, and little tools resting in their own spots."
    )
    world.say(
        f"Then {maker.id} reached for the last part of the plan and noticed something was not where it should be."
    )
    propagate(world)
    world.para()
    world.say(
        f"{maker.id} chose the Quest, looked through the workshop, and came back with what the shawl needed."
    )
    propagate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maker: Entity = f["maker"]
    return [
        "Write a slice-of-life story about a craft workshop, a shawl, a surprise, a repetition, and a quest.",
        f"Tell a small story where {maker.label_word} makes a shawl for a {f['tale']} and has to look for a missing piece.",
        "Write a gentle workshop story that ends with a finished shawl and a calmer heart.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker: Entity = f["maker"]
    shawl: Entity = f["shawl"]
    clue: Entity = f["clue"]
    tale = f["tale"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What was {maker.label_word} making in the craft workshop?",
            answer=f"{maker.label_word} was making {shawl.phrase} for a {_safe_lookup(TALES, tale)}.",
        ),
        QAItem(
            question=f"What happened after {maker.label_word} worked in repeating rows?",
            answer=f"A surprise showed up when the {clue.label} was missing, so {maker.label_word} had to slow down and think.",
        ),
        QAItem(
            question=f"How did the Quest help {maker.label_word} finish the shawl?",
            answer=f"{maker.label_word} searched the workshop, found the {clue.label}, and then finished the shawl with a steadier feeling.",
        ),
        QAItem(
            question=f"How did {maker.label_word} feel at the end?",
            answer=f"{maker.label_word} felt proud and calm, because the {trait} work was done and the shawl was ready for the tale.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "shawl": [
        QAItem(
            question="What is a shawl?",
            answer="A shawl is a piece of cloth that people wear around their shoulders to feel cozy or to look nice.",
        )
    ],
    "tale": [
        QAItem(
            question="What is a tale?",
            answer="A tale is a story that someone tells or reads, often with people, places, and something that happens.",
        )
    ],
    "craft": [
        QAItem(
            question="What do people do in a craft workshop?",
            answer="In a craft workshop, people make things by hand, like sewing, painting, cutting, or tying materials together.",
        )
    ],
    "repetition": [
        QAItem(
            question="Why can repetition help with making things?",
            answer="Repetition can help because doing the same careful action again and again can make a pattern neat and steady.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest in a story?",
            answer="A quest is a search for something important, where the character goes looking and keeps trying until they find it.",
        )
    ],
    "surprise": [
        QAItem(
            question="Why does a surprise matter in a story?",
            answer="A surprise matters because it changes what is happening and gives the character a new problem or a new idea.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ["shawl", "tale", "craft", "repetition", "quest", "surprise"] for q in WORLD_KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  path: {world.path}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tale in TALES:
        for shawl in SHAWLS:
            for clue in CLUES:
                combos.append((tale, shawl, clue))
    return combos


ASP_RULES = r"""
tale(T) :- tale_name(T).
shawl(S) :- shawl_color(S).
clue(C) :- clue_name(C).

repetition(T, S, C) :- tale(T), shawl(S), clue(C).
surprise(T, S, C) :- repetition(T, S, C), clue_missing(C).
quest(T, S, C) :- surprise(T, S, C), can_search(C).
valid_story(T, S, C) :- repetition(T, S, C), surprise(T, S, C), quest(T, S, C).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import path-safe when run as package
    lines = []
    for tale in TALES:
        lines.append(asp.fact("tale_name", tale))
    for shawl in SHAWLS:
        lines.append(asp.fact("shawl_color", shawl))
    for clue in CLUES:
        lines.append(asp.fact("clue_name", clue))
        lines.append(asp.fact("clue_missing", clue))
        lines.append(asp.fact("can_search", clue))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life craft workshop story world about a shawl, a surprise, and a quest.")
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--shawl", choices=SHAWLS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if getattr(args, "tale", None):
        combos = [c for c in combos if c[0] == getattr(args, "tale", None)]
    if getattr(args, "shawl", None):
        combos = [c for c in combos if c[1] == getattr(args, "shawl", None)]
    if getattr(args, "clue", None):
        combos = [c for c in combos if c[2] == getattr(args, "clue", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    tale, shawl, clue = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if gender == "girl" and name in ["Milo", "Eli"]:
        name = rng.choice(NAMES[:4])
    if gender == "boy" and name in ["Mina", "Lina", "Iris", "Ari"]:
        name = rng.choice(NAMES[4:])
    return StoryParams(maker_name=name, maker_type=gender, trait=trait, tale=tale, shawl_color=shawl, clue=clue)


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (tale, shawl, clue) combos:\n")
        for t, s, c in triples:
            print(f"  {t:8} {s:8} {c:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for tale, shawl, clue in sorted(valid_combos()):
            params = StoryParams(
                maker_name="Mina",
                maker_type="girl",
                trait="careful",
                tale=tale,
                shawl_color=shawl,
                clue=clue,
                seed=base_seed,
            )
            samples.append(generate(params))
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
            header = f"### {p.maker_name}: {p.tale} / {p.shawl_color} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
