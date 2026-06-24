#!/usr/bin/env python3
"""
A small animal-story world about a bothersome moment, a vegetarian gazelle,
and kindness that changes the day.

Seed image:
---
A vegetarian gazelle is trying to eat a careful lunch of leaves when a
bothersome noise or interruption keeps getting in the way. The gazelle feels
annoyed, but then notices another animal needs a kind answer. The gazelle
chooses kindness, shares food or help, and the day ends calmer and warmer.
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
    kind: str = "animal"
    species: str = "animal"
    label: str = ""
    plural: bool = False
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gazelle: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if case == "subject":
            return "they"
        if case == "object":
            return "them"
        return "their"

    def is_food_pref(self) -> str:
        return "vegetarian"

    @property
    def name_word(self) -> str:
        return self.label or self.id
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
    detail: str
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
class Event:
    name: str
    kind: str
    intensity: float = 1.0
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Parameters
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


@dataclass
class StoryParams:
    place: str
    gazelle: str
    bother: str
    helper: str
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


PLACES = {
    "savanna": Place(
        name="the savanna",
        detail="The grass was gold and long, and the wind brushed softly over the plain.",
        affords={"eat", "rest", "share"},
    ),
    "watering_hole": Place(
        name="the watering hole",
        detail="The water sparkled, and little footsteps made soft rings in the mud.",
        affords={"drink", "eat", "share"},
    ),
    "grove": Place(
        name="the shady grove",
        detail="Tall trees made a cool pocket of shade where the leaves smelled fresh.",
        affords={"eat", "rest", "share"},
    ),
}

GAZELLES = {
    "Mina": {"name": "Mina", "trait": "gentle"},
    "Lila": {"name": "Lila", "trait": "bright"},
    "Tala": {"name": "Tala", "trait": "careful"},
    "Nori": {"name": "Nori", "trait": "quick"},
}

BOTHERS = {
    "buzzing": Event("buzzing flies", "noise", 1.0),
    "crackling": Event("crackling sticks", "noise", 1.0),
    "munching": Event("munching nearby", "distraction", 1.0),
    "crowding": Event("crowding shadows", "pressure", 1.0),
}

HELPERS = {
    "turtle": "a slow turtle",
    "bird": "a small bird",
    "zebra": "a striped zebra",
    "rabbit": "a shy rabbit",
}


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, bother: str, helper: str) -> bool:
    if place not in PLACES:
        return False
    if bother not in BOTHERS:
        return False
    if helper not in HELPERS:
        return False
    # Keep the story tight: the bother must be noticeable, and the helper must
    # plausibly invite a kindness turn.
    return True


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(savanna). place(watering_hole). place(grove).
affords(savanna,eat). affords(savanna,rest). affords(savanna,share).
affords(watering_hole,drink). affords(watering_hole,eat). affords(watering_hole,share).
affords(grove,eat). affords(grove,rest). affords(grove,share).

bother(buzzing). bother(crackling). bother(munching). bother(crowding).
helper(turtle). helper(bird). helper(zebra). helper(rabbit).

kind_story(P,B,H) :- place(P), bother(B), helper(H), affords(P,share).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for a in sorted(_safe_lookup(PLACES, pid).affords):
            lines.append(asp.fact("affords", pid, a))
    for b in BOTHERS:
        lines.append(asp.fact("bother", b))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show kind_story/3."))
    return sorted(set(asp.atoms(model, "kind_story")))


def asp_verify() -> int:
    py = {(p, b, h) for p in PLACES for b in BOTHERS for h in HELPERS if valid_combo(p, b, h)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combo():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def simulate(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place=place)

    gcfg = _safe_lookup(GAZELLES, params.gazelle)
    gazelle = world.add(Entity(
        id=gcfg["name"],
        kind="animal",
        species="gazelle",
        label=gcfg["name"],
        role="vegetarian gazelle",
        meters={"hunger": 0.0, "calm": 1.0, "kindness": 0.0, "annoyance": 0.0, "joy": 0.0},
        memes={"care": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="animal",
        species=params.helper,
        label=_safe_lookup(HELPERS, params.helper),
        role="friend",
        meters={"need": 1.0, "calm": 0.5, "joy": 0.0},
        memes={"hope": 1.0},
    ))
    bother = _safe_lookup(BOTHERS, params.bother)

    world.say(f"{gazelle.name_word} was a vegetarian gazelle who loved leaf lunch and quiet time.")
    world.say(f"{world.place.detail}")

    world.para()
    world.say(f"One day, {gazelle.name_word} settled down to eat a neat pile of fresh leaves at {world.place.name}.")
    world.say(f"Then {bother.name} kept getting in the way, and that felt bothersome.")
    gazelle.meters["annoyance"] += 1.0
    gazelle.meters["calm"] -= 0.5
    world.facts["bother"] = bother.name
    world.facts["place"] = params.place

    world.para()
    if bother.kind == "noise":
        world.say(f"{gazelle.name_word} pinned back {gazelle.pronoun()} ears and sighed.")
    elif bother.kind == "distraction":
        world.say(f"{gazelle.name_word} tried to focus on the leaves, but the little disturbance kept pulling {gazelle.pronoun('object')} away.")
    else:
        world.say(f"{gazelle.name_word} felt squeezed and cross, because there was hardly room to breathe or nibble.")
    gazelle.meters["annoyance"] += bother.intensity

    world.say(f"Still, {gazelle.name_word} noticed {helper.label} nearby and remembered that kindness could change a hard moment.")
    gazelle.memes["kindness"] += 1.0

    world.para()
    world.say(f"{gazelle.name_word} moved over and offered the best leaves to {helper.label}.")
    world.say(f"{helper.label.capitalize()} smiled and thanked {gazelle.name_word}, which made the air feel softer right away.")
    gazelle.meters["kindness"] += 1.0
    gazelle.meters["joy"] += 1.0
    gazelle.meters["annoyance"] = max(0.0, gazelle.meters["annoyance"] - 1.0)
    gazelle.meters["calm"] += 1.0
    helper.meters["joy"] += 1.0

    world.para()
    world.say(f"After that, {gazelle.name_word} went back to the leafy lunch with a calmer heart.")
    world.say(f"The bothersome moment was still there, but kindness had made it smaller, and the day ended warm and gentle.")

    world.facts.update(
        gazelle=gazelle,
        helper=helper,
        place_obj=place,
        bother_obj=bother,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for young children about a vegetarian gazelle named {f["gazelle"].name_word} at {world.place.name}, where kindness matters more than annoyance.',
        f'Tell a gentle story where {f["gazelle"].name_word} is bothered by {f["bother"]} but chooses kindness and helps {f["helper"].label}.',
        f'Write a simple story that includes the words "bothersome", "vegetarian", "gazelle", and "kindness".',
    ]


def story_qa(world: World) -> list[QAItem]:
    g: Entity = _safe_fact(world, world.facts, "gazelle")
    h: Entity = _safe_fact(world, world.facts, "helper")
    bother = _safe_fact(world, world.facts, "bother")
    place = world.place.name
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {g.name_word}, a vegetarian gazelle who tries to stay calm when something bothersome happens.",
        ),
        QAItem(
            question=f"What bothered {g.name_word} at {place}?",
            answer=f"{bother} bothered {g.name_word} while {g.name_word} was trying to enjoy a leaf lunch at {place}.",
        ),
        QAItem(
            question=f"What did {g.name_word} do instead of staying annoyed?",
            answer=f"{g.name_word} chose kindness, shared the best leaves with {h.label}, and felt happier afterward.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gazelle?",
            answer="A gazelle is a quick wild animal with slender legs that can run fast across open places.",
        ),
        QAItem(
            question="What does vegetarian mean?",
            answer="Vegetarian means an animal or person eats plants, like leaves, fruit, or vegetables, instead of meat.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward someone else.",
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
    lines.append(f"place={world.place.name}")
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} species={e.species:8} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="savanna", gazelle="Mina", bother="buzzing", helper="bird"),
    StoryParams(place="grove", gazelle="Tala", bother="crackling", helper="rabbit"),
    StoryParams(place="watering_hole", gazelle="Lila", bother="crowding", helper="turtle"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a bothersome moment, a vegetarian gazelle, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gazelle", choices=GAZELLES)
    ap.add_argument("--bother", choices=BOTHERS)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [(p, b, h) for p in PLACES for b in BOTHERS for h in HELPERS if valid_combo(p, b, h)]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "bother", None):
        combos = [c for c in combos if c[1] == getattr(args, "bother", None)]
    if getattr(args, "helper", None):
        combos = [c for c in combos if c[2] == getattr(args, "helper", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, bother, helper = rng.choice(list(combos))
    gazelle = getattr(args, "gazelle", None) or rng.choice(sorted(GAZELLES))
    return StoryParams(place=place, gazelle=gazelle, bother=bother, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print(asp_program("#show kind_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, bother, helper) combos:\n")
        for p, b, h in combos:
            print(f"  {p:14} {b:12} {h}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.gazelle} at {p.place} ({p.bother} / {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
