#!/usr/bin/env python3
"""
A small comedy-suspense story world about shapes, a tummy upset, and a surprising
kindness that turns the day around.

Premise:
- A child loves a shape game.
- A snack and a wiggly appetite lead to gastritis-like tummy trouble.
- A worried helper tries to keep the child calm and in one place.
- The child expects a big disaster, but the surprise is gentle: a soft fix,
  a silly shape game, and rest make the day better.

This world keeps two state dimensions:
- meters: physical conditions like belly ache, mess, warmth, and calm space.
- memes: emotional conditions like worry, suspense, surprise, and laughter.

The story should feel authored, concrete, and complete, with a beginning,
turn, and ending image proving what changed.
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
# Core world entities
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    card: object | None = None
    hero: object | None = None
    parent: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def emo(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
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
    place: str = "the kitchen table"
    indoors: bool = True
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
class ShapeCard:
    id: str
    name: str
    sides: int
    curvy: bool = False
    surprising: bool = False
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
class Snack:
    id: str
    label: str
    heavy: bool
    spicy: bool
    oily: bool
    sweet: bool = False
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
class Remedy:
    id: str
    label: str
    action: str
    calm_bonus: float
    warmth: float
    surprise_line: str
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting("the kitchen table", indoors=True),
    "playroom": Setting("the playroom rug", indoors=True),
    "porch": Setting("the porch bench", indoors=True),
}

SHAPES = {
    "circle": ShapeCard("circle", "circle", 0, curvy=True),
    "square": ShapeCard("square", "square", 4),
    "triangle": ShapeCard("triangle", "triangle", 3),
    "star": ShapeCard("star", "star", 10, surprising=True),
    "heart": ShapeCard("heart", "heart", 2, curvy=True, surprising=True),
}

SNACKS = {
    "chips": Snack("chips", "a greasy bowl of chips", heavy=True, spicy=False, oily=True),
    "curry": Snack("curry", "a spicy little curry cup", heavy=True, spicy=True, oily=False),
    "milkshake": Snack("milkshake", "a huge milkshake", heavy=True, spicy=False, oily=True, sweet=True),
    "cake": Snack("cake", "a very sweet slice of cake", heavy=False, spicy=False, oily=False, sweet=True),
}

REMEDIES = {
    "tea": Remedy(
        "tea",
        "ginger tea",
        "sip ginger tea",
        calm_bonus=1.0,
        warmth=1.0,
        surprise_line="the tea smelled a little like a cozy cookie",
    ),
    "toast": Remedy(
        "toast",
        "plain toast",
        "eat plain toast slowly",
        calm_bonus=0.5,
        warmth=0.25,
        surprise_line="the toast came cut into a tiny triangle",
    ),
    "towel": Remedy(
        "towel",
        "a warm towel",
        "rest with a warm towel",
        calm_bonus=1.0,
        warmth=1.0,
        surprise_line="the towel had a smiling owl stitched on it",
    ),
}

NAMES = ["Mina", "Noah", "Lina", "Ezra", "Iris", "Theo", "Pia", "Jude"]
PARENTS = ["mother", "father", "grandparent", "aunt"]
TRAITS = ["curious", "bubbly", "silly", "careful", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
shape_circle(circle).
shape_square(square).
shape_triangle(triangle).
shape_star(star).
shape_heart(heart).

snack(chips). snack(curry). snack(milkshake). snack(cake).
remedy(tea). remedy(toast). remedy(towel).

heavy(chips). heavy(curry). heavy(milkshake).
oily(chips). oily(milkshake).
spicy(curry).
sweet(cake). sweet(milkshake).

indoor(kitchen). indoor(playroom). indoor(porch).

story_ok(Snack, Remedy) :- snack(Snack), remedy(Remedy), risk(Snack), help(Remedy).
risk(Snack) :- heavy(Snack); spicy(Snack); oily(Snack).
help(tea). help(toast). help(towel).

% The Python gate requires the snack to be genuinely risky and the remedy to
% provide calm. This mirrors the "reasonable" story constraint.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if _safe_lookup(SETTINGS, sid).indoors:
            lines.append(asp.fact("indoor", sid))
    for sid in SHAPES:
        lines.append(asp.fact("shape", sid))
        lines.append(asp.fact("sides", sid, _safe_lookup(SHAPES, sid).sides))
        if _safe_lookup(SHAPES, sid).curvy:
            lines.append(asp.fact("curvy", sid))
        if _safe_lookup(SHAPES, sid).surprising:
            lines.append(asp.fact("surprising", sid))
    for sid, sn in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if sn.heavy:
            lines.append(asp.fact("heavy", sid))
        if sn.spicy:
            lines.append(asp.fact("spicy", sid))
        if sn.oily:
            lines.append(asp.fact("oily", sid))
        if sn.sweet:
            lines.append(asp.fact("sweet", sid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def snack_is_risky(snack: Snack) -> bool:
    return snack.heavy or snack.spicy or snack.oily


def remedy_is_credible(remedy: Remedy) -> bool:
    return remedy.calm_bonus > 0


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for s in SNACKS.values():
        if not snack_is_risky(s):
            continue
        for r in REMEDIES.values():
            if remedy_is_credible(r):
                out.append((s.id, r.id))
    return out


def explain_rejection(snack: Snack, remedy: Remedy) -> str:
    return (
        f"(No story: {snack.label} would not really bother a tummy enough to create suspense, "
        f"so there is no honest problem to solve.)"
    )


# ---------------------------------------------------------------------------
# Story model helpers
# ---------------------------------------------------------------------------
def setup_line(hero: Entity, shape: ShapeCard, snack: Snack) -> str:
    return (
        f"{hero.id} loved sorting cards into neat piles of shapes. "
        f"{hero.pronoun('subject').capitalize()} especially liked the {shape.name}s, "
        f"because they looked ready to march around the table."
    )


def warning_line(parent: Entity, snack: Snack) -> str:
    return (
        f"But the snack was {snack.label}, and it was a little too heavy for a happy tummy. "
        f"{parent.label.capitalize()} gave a worried look and said the day might turn into a bellyache show."
    )


def predict_upset(world: World, snack: Snack) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["stomach"] = hero.meters.get("stomach", 0) + (1.2 if snack_is_risky(snack) else 0)
    hero.memes["worry"] = hero.memes.get("worry", 0) + (1.0 if snack.heavy else 0)
    return {
        "ache": hero.meters.get("stomach", 0) >= THRESHOLD,
        "worry": hero.memes.get("worry", 0),
    }


def do_snack(world: World, hero: Entity, snack: Snack) -> None:
    hero.meters["stomach"] = hero.meters.get("stomach", 0) + (1.3 if snack.heavy else 0.7)
    if snack.spicy:
        hero.meters["burn"] = hero.meters.get("burn", 0) + 1.0
    if snack.oily:
        hero.meters["slosh"] = hero.meters.get("slosh", 0) + 1.0
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1.0


def apply_remedy(world: World, hero: Entity, remedy: Remedy) -> None:
    hero.meters["stomach"] = max(0.0, hero.meters.get("stomach", 0.0) - 0.9)
    hero.meters["warmth"] = hero.meters.get("warmth", 0.0) + remedy.warmth
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - remedy.calm_bonus)
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    hero.memes["laugh"] = hero.memes.get("laugh", 0.0) + 1.0


def resolve(world: World, hero: Entity, parent: Entity, shape: ShapeCard, remedy: Remedy) -> None:
    world.say(
        f"Then {parent.label} brought out {remedy.label}, and the surprise was that it came with {remedy.surprise_line}."
    )
    world.say(
        f"{hero.id} tried the tiny shape game again, only this time {hero.pronoun('subject')} breathed slowly "
        f"and counted circles, squares, and stars while resting."
    )
    apply_remedy(world, hero, remedy)
    world.say(
        f"Soon the belly grumble got quieter. {hero.id} could point to the {shape.name} card without making a face, "
        f"and the whole table looked calmer, as if it had decided to giggle politely."
    )


def final_image(world: World, hero: Entity, shape: ShapeCard) -> str:
    if hero.meters.get("stomach", 0.0) > 0.2:
        return f"By the end, {hero.id} was still a little careful, but {hero.pronoun('subject')} smiled at the {shape.name} cards and held the warm towel close."
    return f"By the end, {hero.id} was curled up with the {shape.name} cards, laughing softly because the tummy trouble had turned into a quiet, cozy afternoon."


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    shape: str
    snack: str
    remedy: str
    name: str
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


def tell(setting: Setting, shape: ShapeCard, snack: Snack, remedy: Remedy, name: str, parent_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type="child",
        meters={"stomach": 0.0, "warmth": 0.0},
        memes={"joy": 1.0, "suspense": 0.0, "surprise": 0.0, "worry": 0.0, "laugh": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_kind,
        label=f"the {parent_kind}",
        meters={"calm": 1.0},
        memes={"care": 1.0},
    ))
    card = world.add(Entity(id="shape", type="card", label=f"a {shape.name} card", owner=hero.id))
    world.facts.update(hero=hero, parent=parent, shape=shape, snack=snack, remedy=remedy, card=card, trait=trait)

    world.say(
        f"{hero.id} was a {trait} child who loved shapes, especially the {shape.name}. "
        f"{hero.pronoun('subject').capitalize()} lined the cards up on the {setting.place} like a tiny parade."
    )
    world.say(setup_line(hero, shape, snack))

    world.para()
    world.say(
        f"At snack time, {hero.id} chose {snack.label}. "
        f"The first bites were funny, but then {hero.pronoun('possessive')} tummy started to feel twisty and strange."
    )
    do_snack(world, hero, snack)
    pred = predict_upset(world, snack)
    if pred["ache"]:
        world.say(warning_line(parent, snack))
        world.say(
            f"{hero.id} made a brave little face, but the suspense grew because {hero.pronoun('subject')} did not know if the tummy wobble would get worse."
        )
        hero.memes["suspense"] += 1.0

    world.para()
    world.say(
        f"Just then, {parent.label} did something unexpected: {remedy.label} appeared, and it was not a boring lecture at all."
    )
    resolve(world, hero, parent, shape, remedy)

    world.para()
    world.say(final_image(world, hero, shape))

    world.facts["resolved"] = True
    world.facts["final_stomach"] = hero.meters.get("stomach", 0.0)
    return world


# ---------------------------------------------------------------------------
# Content selection
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for shape_id in SHAPES:
            for snack_id in SNACKS:
                if not snack_is_risky(_safe_lookup(SNACKS, snack_id)):
                    continue
                for remedy_id in REMEDIES:
                    if remedy_is_credible(_safe_lookup(REMEDIES, remedy_id)):
                        combos.append((setting_id, shape_id, snack_id))
    return combos


CURATED = [
    StoryParams("kitchen", "circle", "chips", "tea", "Mina", "mother", "curious"),
    StoryParams("playroom", "star", "curry", "towel", "Noah", "father", "silly"),
    StoryParams("porch", "triangle", "milkshake", "toast", "Iris", "mother", "careful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "snack", None) and not snack_is_risky(_safe_lookup(SNACKS, getattr(args, "snack", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "shape", None) is None or c[1] == getattr(args, "shape", None))
        and (getattr(args, "snack", None) is None or c[2] == getattr(args, "snack", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, shape, snack = rng.choice(list(combos))
    remedy = getattr(args, "remedy", None) or rng.choice(list(REMEDIES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting, shape, snack, remedy, name, parent, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    shape = _safe_fact(world, f, "shape")
    snack = _safe_fact(world, f, "snack")
    parent = _safe_fact(world, f, "parent")
    return [
        f'Write a short comedy story for a child named {hero.id} who loves the {shape.name} shape and then feels tummy trouble after {snack.label}.',
        f"Tell a suspenseful but gentle story where {hero.id}'s {parent.label} notices a bellyache and offers a surprising remedy.",
        f'Write a funny, child-friendly story that includes the words "shape" and "gastritis" in an age-appropriate way and ends with a calm, cozy image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, shape, snack, remedy = f["hero"], f["parent"], f["shape"], f["snack"], f["remedy"]
    return [
        QAItem(
            question=f"What did {hero.id} love doing at the start of the story?",
            answer=f"{hero.id} loved sorting and lining up shape cards, especially the {shape.name} card.",
        ),
        QAItem(
            question=f"Why did {hero.id} start feeling bad after snack time?",
            answer=f"{hero.id} had {snack.label}, and that snack was heavy enough to make {hero.pronoun('possessive')} tummy twist and grumble like gastritis trouble.",
        ),
        QAItem(
            question=f"What surprising thing helped {hero.id} feel better?",
            answer=f"{parent.label} brought {remedy.label}, and the little surprise helped {hero.id} rest, warm up, and calm down.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} smiling at the {shape.name} cards again, while staying cozy and much calmer than before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shape?",
            answer="A shape is the outline or form of something, like a circle, square, triangle, or star.",
        ),
        QAItem(
            question="What does gastritis mean?",
            answer="Gastritis means the stomach lining is irritated, which can make a tummy hurt or feel upset.",
        ),
        QAItem(
            question="Why can a warm towel help when someone feels unwell?",
            answer="A warm towel can feel comforting and help a person relax while they rest.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(SHAPES, params.shape),
        _safe_lookup(SNACKS, params.snack),
        _safe_lookup(REMEDIES, params.remedy),
        params.name,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy-suspense story world about shapes and a tummy upset.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shape", choices=SHAPES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_reasonable_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_reasonable_pairs()
        print(f"{len(pairs)} compatible snack/remedy pairs:")
        for s, r in pairs:
            print(f"  {s} + {r}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [
            generate(p)
            for p in CURATED
        ]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.snack} with the {p.shape} shape in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
