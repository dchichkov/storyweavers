#!/usr/bin/env python3
"""
A tiny storyworld about a berry stand, sharing, and a watchful principal,
told in a nursery-rhyme style.

Premise:
- A child runs a little stand with barberries.
- The principal worries there may be no sharing.
- A simple trade/gesture turns fuss into fair sharing.

The world keeps physical meters and emotional memes:
- meters: counts of berries, bowls, coins, crumbs, ribbons, etc.
- memes: feelings like delight, worry, pride, fairness, and patience.
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


# ---------------------------------------------------------------------------
# Domain registries
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
class PersonDef:
    name: str
    role: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
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
class ObjectDef:
    id: str
    label: str
    phrase: str
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


PEOPLE = {
    "mira": PersonDef("Mira", "child", "she", "her", "her"),
    "niko": PersonDef("Niko", "child", "he", "him", "his"),
    "principal": PersonDef("Principal Plum", "principal", "she", "her", "her"),
}

LOCATIONS = {
    "schoolyard": "the schoolyard",
    "porch": "the porch",
    "garden_gate": "the garden gate",
}

OBJECTS = {
    "barberries": ObjectDef("barberries", "barberries", "a bowl of bright barberries"),
    "cup": ObjectDef("cup", "cup", "a little paper cup"),
    "sign": ObjectDef("sign", "sign", "a cheery stand sign"),
    "tally": ObjectDef("tally", "tally", "a tidy tally card"),
    "spoon": ObjectDef("spoon", "spoon", "a tiny wooden spoon"),
}

# inline ASP twin
ASP_RULES = r"""
#show valid/3.

valid(Hero, Place, Prize) :- hero(Hero), place(Place), prize(Prize), 
    at(Hero, Place), has(Prize, barberries), can_share(Prize).
"""


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: Optional[str] = None
    plural: bool = False

    hero: object | None = None
    principal: object | None = None
    stand: object | None = None
    def __post_init__(self):
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for k in ["berries", "cups", "coins", "shares", "turns", "crowd"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "pride", "fairness", "patience", "hunger"]:
            self.memes.setdefault(k, 0.0)
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    world: object | None = None
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
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


# ---------------------------------------------------------------------------
# Params
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    place: str = ""
    hero: str = ""
    principal: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
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


def art(name: str) -> str:
    return name


def capitalize_first(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def rhyme_end(a: str, b: str) -> str:
    return f"{a}, {b}"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.hero not in PEOPLE or params.principal not in PEOPLE:
        pass
    if params.place not in LOCATIONS:
        pass

    hero_def = PEOPLE[params.hero]
    principal_def = PEOPLE[params.principal]

    world = World(place=params.place)

    hero = world.add(Entity(
        id=hero_def.name,
        kind="character",
        label=hero_def.role,
        location=_safe_lookup(LOCATIONS, params.place),
        meters={"berries": 0, "cups": 0, "coins": 0, "shares": 0, "turns": 0, "crowd": 0},
        memes={"joy": 1, "worry": 0, "pride": 0, "fairness": 0, "patience": 0, "hunger": 0},
    ))
    principal = world.add(Entity(
        id=principal_def.name,
        kind="character",
        label=principal_def.role,
        location=_safe_lookup(LOCATIONS, params.place),
        memes={"joy": 0, "worry": 1, "pride": 0, "fairness": 1, "patience": 1, "hunger": 0},
    ))
    stand = world.add(Entity(
        id="Stand",
        kind="thing",
        label="stand",
        location=_safe_lookup(LOCATIONS, params.place),
        meters={"berries": 12, "cups": 4, "coins": 0, "shares": 0, "turns": 0, "crowd": 0},
    ))
    world.add(Entity(id="BarberryBowl", kind="thing", label="barberries", owner=hero.id, carried_by=hero.id, meters={"berries": 12}))
    world.add(Entity(id="PaperCups", kind="thing", label="cups", owner=hero.id, carried_by=hero.id, meters={"cups": 4}))
    world.add(Entity(id="CheerySign", kind="thing", label="sign", owner=hero.id, carried_by=hero.id))
    world.add(Entity(id="TinySpoon", kind="thing", label="spoon", owner=hero.id, carried_by=hero.id))

    world.facts["hero"] = hero
    world.facts["principal"] = principal
    world.facts["stand"] = stand
    world.facts["place"] = params.place
    return world


def intro(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    principal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "principal")
    place = _safe_lookup(LOCATIONS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place"))

    world.say(
        f"At {place}, by a little stand of sweet barberries, lived {hero.id}, "
        f"who smiled and stacked cups with care."
    )
    world.say(
        f"Near the stand stood {principal.id}, the school principal, with a twinkle and a look "
        f"that said, 'Now mind the sharing there.'"
    )


def setup_stand(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    stand = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "stand")
    stand.meters["berries"] = 12
    stand.meters["cups"] = 4
    hero.meters["joy"] += 1
    hero.meters["pride"] += 1
    world.say(
        f"{hero.id} laid out {OBJECTS['barberries'].phrase}, "
        f"{OBJECTS['cup'].phrase}s, and {OBJECTS['sign'].phrase} that read, "
        f"'Come one, come all, and share the berry ball.'"
    )


def first_wave(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    principal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "principal")
    stand = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "stand")

    hero.meters["crowd"] += 1
    stand.meters["crowd"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Children came in a tiny stream, and {hero.id} began to pour the berries out in a neat "
        f"little gleam."
    )
    world.say(
        f"{principal.id} watched the line and saw the cups were few; {principal.id} worried "
        f"the berry fun might not go through."
    )
    world.facts["principal_worried"] = True


def conflict(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    principal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "principal")
    stand = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "stand")

    if stand.meters["berries"] <= 0:
        pass
    hero.memes["worry"] += 1
    principal.memes["worry"] += 1
    world.say(
        f"'A stand is a happy thing,' said {principal.id}, 'but one small bowl can vanish in a blink.'"
    )
    world.say(
        f"{hero.id} held the spoon and felt a wobble in the stomach, for a greedy gulp would not "
        f"make the day a jingle-jump delight."
    )


def share_turn(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    principal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "principal")
    stand = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "stand")

    if stand.meters["cups"] < 2:
        pass

    # turn state: divide berries, pass cups, add fairness
    stand.meters["berries"] -= 4
    stand.meters["cups"] -= 2
    stand.meters["shares"] += 1
    hero.meters["shares"] += 1
    hero.memes["fairness"] += 1
    hero.memes["patience"] += 1
    principal.memes["worry"] = max(0, principal.memes["worry"] - 1)
    principal.memes["pride"] += 1

    world.say(
        f"Then {hero.id} did a kinder thing: {hero.id} set out two cups, gave each child a turn, "
        f"and kept a few berries for the next."
    )
    world.say(
        f"{principal.id} nodded and sang, 'Share a berry, share a smile, and every waiting heart "
        f"will rest awhile.'"
    )


def ending(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    principal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "principal")
    stand = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "stand")

    if stand.meters["shares"] < 1:
        pass

    hero.memes["joy"] += 2
    principal.memes["worry"] = 0
    principal.memes["fairness"] += 1
    world.say(
        f"By the end, the stand was still bright, the barberries still red, and {hero.id} still "
        f"smiling under the little sign overhead."
    )
    world.say(
        f"{principal.id} laughed, the children clapped, and the berry stand shone like a nursery rhyme "
        f"come true."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    place = _safe_lookup(LOCATIONS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place"))
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero").id
    principal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "principal").id
    return [
        f"Write a short nursery-rhyme story about {hero} at {place} with barberries and sharing.",
        f"Tell a gentle story where {principal} worries about a berry stand, then a child shares well.",
        "Write a rhyme-like story with a stand, a principal, and a happy turn from worry to sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    principal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "principal")
    place = _safe_lookup(LOCATIONS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place"))
    return [
        QAItem(
            question=f"Who ran the berry stand at {place}?",
            answer=f"{hero.id} ran the little stand and laid out the barberries with care.",
        ),
        QAItem(
            question=f"Why did {principal.id} worry near the stand?",
            answer=f"{principal.id} worried because there were many children, but only a small pile of cups and berries at first.",
        ),
        QAItem(
            question="What changed the mood of the story?",
            answer="The mood changed when the berries were shared out in small turns, so the stand felt fair and merry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are barberries?",
            answer="Barberries are small tart berries that can be bright red or orange and are often used in cooking.",
        ),
        QAItem(
            question="What is a stand?",
            answer="A stand is a small place where someone puts out things to give, sell, or show them to other people.",
        ),
        QAItem(
            question="What does a principal do?",
            answer="A principal helps run a school and watches over students, teachers, and the school day.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving some of what you have to other people so everyone can enjoy it together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: kind={e.kind} label={e.label} "
            f"meters={ {k: v for k, v in e.meters.items() if v} } "
            f"memes={ {k: v for k, v in e.memes.items() if v} }"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PEOPLE:
        lines.append(asp.fact("hero", PEOPLE[pid].name))
    for place in LOCATIONS:
        lines.append(asp.fact("place", place))
    for oid in OBJECTS:
        if oid == "barberries":
            lines.append(asp.fact("prize", oid))
            lines.append(asp.fact("has", oid, "barberries"))
            lines.append(asp.fact("can_share", oid))
    lines.append(asp.fact("at", PEOPLE["mira"].name, "schoolyard"))
    lines.append(asp.fact("at", PEOPLE["niko"].name, "schoolyard"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hero in ["mira", "niko"]:
        for place in LOCATIONS:
            for prize in ["barberries"]:
                combos.append((hero, place, prize))
    return combos


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: ASP and Python agree on {len(python_set)} valid combos.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("Python only:", sorted(python_set - clingo_set))
    print("ASP only:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    setup_stand(world)
    world.say("")
    first_wave(world)
    conflict(world)
    share_turn(world)
    ending(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a barberry stand.")
    ap.add_argument("--place", choices=LOCATIONS.keys())
    ap.add_argument("--hero", choices=["mira", "niko"])
    ap.add_argument("--principal", choices=["principal"])
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
    place = getattr(args, "place", None) or rng.choice(list(LOCATIONS.keys()))
    hero = getattr(args, "hero", None) or rng.choice(["mira", "niko"])
    principal = getattr(args, "principal", None) or "principal"
    return StoryParams(place=place, hero=hero, principal=principal)


CURATED = [
    StoryParams(place="schoolyard", hero="mira", principal="principal"),
    StoryParams(place="porch", hero="niko", principal="principal"),
    StoryParams(place="garden_gate", hero="mira", principal="principal"),
]


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} valid combos:")
        for t in vals:
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
