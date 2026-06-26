#!/usr/bin/env python3
"""
complete_surprise_myth.py

A small mythic storyworld about a complete ritual, a humble seeker, and a
surprise that changes the meaning of a gift.
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

    gift: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        if self.type in {"girl", "woman", "queen", "goddess", "maiden"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "man", "king", "god", "priest"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
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
class Place:
    name: str
    epithet: str
    qualities: set[str] = field(default_factory=set)
    wonders: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    risk: str
    surprise: str
    kind: str
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
class Gift:
    id: str
    label: str
    phrase: str
    reveals: str
    surprise: str
    kind: str
    sacred: bool = False
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
    hero_type: str
    hero_name: str
    title: str
    relic: str
    gift: str
    seed: Optional[int] = None
    params: object | None = None
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
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "mountain": Place("the mountain", "high and old", {"stone", "wind"}, {"echo", "cave"}),
    "temple": Place("the temple", "bright and quiet", {"stone", "incense"}, {"altar", "veil"}),
    "forest": Place("the forest", "deep and green", {"leaf", "shade"}, {"spring", "owl"}),
    "island": Place("the island", "salt and bright", {"wave", "shell"}, {"tide", "driftwood"}),
}

RELICS = {
    "crown": Relic("crown", "crown", "a gold crown", "it would crack if it was forced too long", "an old moonstone hidden inside", "head", {"girl", "boy"}),
    "cloak": Relic("cloak", "cloak", "a crimson cloak", "it would snag on jagged stone", "a tiny bell sewn into the hem", "shoulders", {"girl", "boy"}),
    "lantern": Relic("lantern", "lantern", "a silver lantern", "its flame would gutter in the dark wind", "a second wick already lit inside", "hands", {"girl", "boy"}),
    "bracelet": Relic("bracelet", "bracelet", "a braided bracelet", "its knot would loosen in rain", "a seed that still remembered spring", "wrist", {"girl", "boy"}),
}

GIFTS = {
    "stone": Gift("stone", "stone", "a smooth stone", "it opened like an egg", "a sleeping star within", "hands", sacred=False),
    "water": Gift("water", "cup of water", "a cup of water", "it reflected a face not yet seen", "the face of the river-spirit", "hands", sacred=False),
    "honey": Gift("honey", "jar of honey", "a jar of honey", "it carried a scent older than fire", "a beesong that knew the hero's name", "hands", sacred=True),
    "bread": Gift("bread", "loaf of bread", "a round loaf of bread", "it split to show warm light", "a small sun baked into the center", "hands", sacred=True),
}

HERO_TITLES = ["child", "shepherd", "scribe", "princess", "prince", "wanderer"]
GIRL_NAMES = ["Asha", "Lina", "Mira", "Nina", "Rhea", "Sera"]
BOY_NAMES = ["Arin", "Kian", "Tomas", "Leif", "Oren", "Dara"]
EPITHETS = ["the patient", "the brave", "the curious", "the quiet", "the steadfast"]


def complete_pairs() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for relic in RELICS:
            for gift in GIFTS:
                if valid_combo(place, relic, gift):
                    out.append((place, relic, gift))
    return out


def valid_combo(place: str, relic: str, gift: str) -> bool:
    p = _safe_lookup(PLACES, place)
    r = _safe_lookup(RELICS, relic)
    g = _safe_lookup(GIFTS, gift)
    if place == "mountain" and relic == "cloak" and gift == "stone":
        return False
    if place == "temple" and gift == "bread" and relic == "lantern":
        return True
    if place == "forest" and relic == "bracelet" and gift == "honey":
        return True
    if place == "island" and relic == "crown" and gift == "water":
        return True
    # Reasonable mythic fit: each story must have a place whose wonders can
    # plausibly reveal the surprise hidden in the gift.
    if place == "mountain" and relic in {"crown", "lantern"} and gift in {"stone", "bread"}:
        return True
    if place == "temple" and relic in {"cloak", "bracelet"} and gift in {"water", "honey"}:
        return True
    if place == "forest" and relic in {"cloak", "lantern"} and gift in {"stone", "water"}:
        return True
    if place == "island" and relic in {"crown", "bracelet"} and gift in {"bread", "honey"}:
        return True
    return False


def explain_rejection(place: str, relic: str, gift: str) -> str:
    return (
        f"(No story: at {_safe_lookup(PLACES, place).name}, that relic and gift do not make a "
        f"strong mythic surprise. The hidden thing would not feel discovered in a "
        f"complete way.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
relic(R) :- relic_fact(R).
gift(G) :- gift_fact(G).

fits(mountain,crown,stone).
fits(temple,cloak,water).
fits(temple,bracelet,honey).
fits(forest,cloak,stone).
fits(forest,lantern,water).
fits(island,crown,water).
fits(island,bracelet,bread).
fits(mountain,lantern,bread).

valid_story(P,R,G) :- fits(P,R,G), place_fact(P), relic_fact(R), gift_fact(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for r in RELICS:
        lines.append(asp.fact("relic_fact", r))
    for g in GIFTS:
        lines.append(asp.fact("gift_fact", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(complete_pairs())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches complete_pairs() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and complete_pairs():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def hero_name(hero_type: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)


def describe_place(place: Place) -> str:
    return f"{place.name}, {place.epithet}"


def generate_story(world: World, hero: Entity, relic: Entity, gift: Entity) -> None:
    place = world.place
    world.say(
        f"Long ago, {hero.id}, {hero.phrase}, came to {describe_place(place)}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} carried {relic.phrase} and offered {gift.phrase} at the shrine."
    )
    if gift.id == "stone":
        world.say("The stone stayed still in the hero's palm, and the air went very quiet.")
    elif gift.id == "water":
        world.say("The water trembled, as if it knew a secret song.")
    elif gift.id == "honey":
        world.say("The honey glowed warm, sweet as a remembered feast.")
    else:
        world.say("The bread smelled plain and humble, like a promise that had grown patient.")

    world.say(
        f"{hero.id} thought the offering was complete: a simple gift for a sacred wish."
    )
    world.say(
        f"But when {hero.pronoun('subject')} set down {gift.phrase}, the surprise awoke inside it."
    )
    world.say(
        f"It was not empty at all; it held {gift.surprise}."
    )
    world.say(
        f"Then the relic answered too. {relic.surprise.capitalize()}."
    )
    world.say(
        f"So the hero understood the old sign: what seemed finished was only the first half of the blessing."
    )
    world.say(
        f"{hero.id} bowed again, now smiling, because the complete offering had become a complete story."
    )


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.title,
        phrase=f"{params.title} {params.hero_name}",
    ))
    relic_cfg = _safe_lookup(RELICS, params.relic)
    gift_cfg = _safe_lookup(GIFTS, params.gift)
    relic = world.add(Entity(
        id=relic_cfg.id,
        type=relic_cfg.kind,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        owner=hero.id,
    ))
    gift = world.add(Entity(
        id=gift_cfg.id,
        type=gift_cfg.kind,
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        owner=hero.id,
    ))

    world.facts.update(
        place=place,
        hero=hero,
        relic=relic,
        gift=gift,
        relic_cfg=relic_cfg,
        gift_cfg=gift_cfg,
    )
    generate_story(world, hero, relic, gift)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f"Write a short myth about {hero.id} making a complete offering at {world.place.name}.",
        f"Tell a child-friendly legend where a gift hides a surprise and changes what the hero understands.",
        f"Write a simple mythic story about a sacred place, a humble relic, and a hidden blessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    relic_cfg: Relic = _safe_fact(world, f, "relic_cfg")
    gift_cfg: Gift = _safe_fact(world, f, "gift_cfg")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who came to {place.name} in the story?",
            answer=f"{hero.id}, {hero.label}, came to {place.name}.",
        ),
        QAItem(
            question=f"What gift did {hero.id} offer?",
            answer=f"{hero.id} offered {gift_cfg.phrase}.",
        ),
        QAItem(
            question=f"What was the surprise hidden inside the gift?",
            answer=f"The surprise was {gift_cfg.surprise}.",
        ),
        QAItem(
            question=f"What did the relic reveal?",
            answer=f"The relic revealed {relic_cfg.surprise}.",
        ),
        QAItem(
            question=f"How did the hero feel at the end?",
            answer=f"{hero.id} felt glad and understanding, because the offering turned out to be more complete than expected.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a relic in a myth?",
            answer="A relic is a special old object that people treat with respect because it is tied to a story, a place, or a god.",
        ),
        QAItem(
            question="What is an offering?",
            answer="An offering is something given with care, often to show thanks, respect, or hope for a blessing.",
        ),
        QAItem(
            question="Why do myths often include surprises?",
            answer="Myths often include surprises because they show that the world may hold hidden meanings, secret gifts, or lessons that are larger than they first seem.",
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place: {world.place.name} / {world.place.epithet}")
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic surprise storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--title", choices=HERO_TITLES)
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
    combos = complete_pairs()
    if getattr(args, "place", None) and getattr(args, "relic", None) and getattr(args, "gift", None) and not valid_combo(getattr(args, "place", None), getattr(args, "relic", None), getattr(args, "gift", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "relic", None) is None or c[1] == getattr(args, "relic", None))
        and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, relic, gift = rng.choice(list(filtered))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    title = getattr(args, "title", None) or rng.choice(HERO_TITLES)
    name = getattr(args, "hero_name", None) or hero_name(hero_type, rng)
    return StoryParams(place=place, hero_type=hero_type, hero_name=name, title=title, relic=relic, gift=gift)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible stories:\n")
        for p, r, g in combos:
            print(f"  {p:8} {r:8} {g:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    if getattr(args, "all", None):
        samples = []
        for p, r, g in complete_pairs():
            params = StoryParams(
                place=p,
                hero_type="girl",
                hero_name="Asha",
                title="the brave",
                relic=r,
                gift=g,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        samples = []
        seen = set()
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
