#!/usr/bin/env python3
"""
Storyworld: yarn_kindness_bravery_rhyme_nursery_rhyme

A tiny nursery-rhyme style world about a child, a ball of yarn, a little worry,
and a brave kind rhyme that helps set things right.
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
# Domain model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    yarn: object | None = None
    def __post_init__(self) -> None:
        for k in ("tangle", "mend", "worry", "joy", "bravery", "kindness", "rhyme"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child", "girl-child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Place:
    name: str
    weather: str
    setting_detail: str
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
class Treasure:
    label: str
    phrase: str
    type: str
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
    treasure: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
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


PLACES = {
    "nursery": Place(
        name="the nursery",
        weather="soft and still",
        setting_detail="A moonbeam lay on the rug, and a toy basket sat by the wall.",
    ),
    "garden": Place(
        name="the garden gate",
        weather="bright and breezy",
        setting_detail="Little flowers nodded beside the path, and the fence sang in the wind.",
    ),
    "porch": Place(
        name="the porch",
        weather="rain-tapped and gray",
        setting_detail="The porch steps were shiny with rain, and a little puddle blinked below.",
    ),
}

TREASURES = {
    "yarn": Treasure(
        label="ball of yarn",
        phrase="a soft blue ball of yarn",
        type="yarn",
    ),
    "ribbon": Treasure(
        label="ribbon spool",
        phrase="a bright red ribbon spool",
        type="ribbon",
    ),
    "sock": Treasure(
        label="sock bundle",
        phrase="a tidy bundle of striped socks",
        type="sock-bundle",
    ),
}

HERO_NAMES = ["Mia", "Nora", "June", "Pip", "Eli", "Bea", "Luna", "Theo"]
HELPER_NAMES = ["Mama", "Papa", "Gran", "Auntie", "Baba", "Uncle Ben"]

TRAITS = ["small", "cheery", "curious", "gentle", "brave", "kind"]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

class SimWorld:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _tangle(world: SimWorld) -> None:
    hero = world.get("hero")
    yarn = world.get("yarn")
    if hero.memes["bravery"] >= THRESHOLD and hero.memes["kindness"] >= THRESHOLD:
        if "tangled" not in world.fired:
            world.fired.add("tangled")
            yarn.meters["tangle"] += 1
            hero.memes["worry"] += 1
            world.say(f"The yarn grew tangled as a kitten might purr in a knot of light.")


def _mend(world: SimWorld) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    yarn = world.get("yarn")
    if hero.memes["kindness"] >= THRESHOLD and hero.memes["bravery"] >= THRESHOLD and hero.memes["rhyme"] >= THRESHOLD:
        if "mended" not in world.fired:
            world.fired.add("mended")
            yarn.meters["tangle"] = 0
            yarn.meters["mend"] += 1
            hero.memes["joy"] += 1
            helper.memes["joy"] += 1
            world.say(f"The knot came loose, and the soft blue yarn was smooth and neat once more.")


def _resolve(world: SimWorld) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    yarn = world.get("yarn")
    if yarn.meters["mend"] >= THRESHOLD and "resolved" not in world.fired:
        world.fired.add("resolved")
        hero.memes["worry"] = 0
        helper.memes["kindness"] += 1
        world.say(f"Kindness held the room, and Bravery hopped along with Rhyme, light as a feather.")


def propagate(world: SimWorld) -> None:
    _tangle(world)
    _mend(world)
    _resolve(world)


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def intro(world: SimWorld, hero: Entity, helper: Entity, treasure: Entity) -> None:
    world.say(
        f"In {world.place.name}, {hero.id} was a {hero_type_word(hero)} with a heart both small and true, "
        f"and {helper.id} was near, with a smile that knew what to do."
    )
    world.say(
        f"They loved the {treasure.label}, for {treasure.phrase} could be wound into nests and games and bows."
    )


def _get_subject_name(e: Entity) -> str:
    return e.id


def hero_type_word(hero: Entity) -> str:
    return hero.type


def complication(world: SimWorld, hero: Entity, helper: Entity, treasure: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} reached for the {treasure.label}, but the string caught on a chair-back hook."
    )
    hero.memes["worry"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took a breath so deep and wide, then said a tiny rhyme to steady the tide:"
    )
    world.say(
        f"\"If yarn may knot, then so may not; with kindness now, we'll smooth the spot.\""
    )
    hero.memes["rhyme"] += 1
    hero.memes["kindness"] += 1
    propagate(world)


def resolution(world: SimWorld, hero: Entity, helper: Entity, treasure: Entity) -> None:
    world.para()
    world.say(
        f"{helper.id} knelt right down and held the ball, and {hero.id} held the loose, bright thread."
    )
    hero.memes["bravery"] += 1
    hero.memes["kindness"] += 1
    hero.memes["rhyme"] += 1
    propagate(world)
    world.say(
        f"Together they sang the little rhyme once more, and the yarn lay gentle, tidy, and well-bred."
    )
    world.say(
        f"Then {hero.id} smiled a warm small smile, and {helper.id} laughed like bells in a row."
    )


def tell_story(params: StoryParams) -> SimWorld:
    place = _safe_lookup(PLACES, params.place)
    treasure = _safe_lookup(TREASURES, params.treasure)
    world = SimWorld(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    yarn = world.add(Entity(id="yarn", kind="thing", type="yarn", label="yarn", phrase=treasure.phrase))
    world.facts.update(hero=hero, helper=helper, yarn=yarn, treasure=treasure, place=place)

    intro(world, hero, helper, treasure)
    complication(world, hero, helper, treasure)
    resolution(world, hero, helper, treasure)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: SimWorld) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    treasure = _safe_fact(world, world.facts, "treasure")
    return [
        f"Write a short nursery-rhyme story about {hero.id}, {helper.id}, and {treasure.phrase}.",
        f"Tell a gentle story where kindness, bravery, and rhyme help untangle the yarn.",
        f"Make a small rhyming tale set in {world.place.name} with a soft, child-friendly ending.",
    ]


def story_qa(world: SimWorld) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    treasure = _safe_fact(world, world.facts, "treasure")
    place = world.place.name
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about {hero.id}, who was with {helper.id} in {place}.",
        ),
        QAItem(
            question=f"What got tangled in the story?",
            answer=f"The {treasure.label} got tangled, but the friends worked it loose.",
        ),
        QAItem(
            question="What helped solve the problem?",
            answer="Kindness, Bravery, and Rhyme helped smooth the trouble away.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calm when the yarn lay neat again.",
        ),
    ]


def world_knowledge_qa(world: SimWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is yarn used for?",
            answer="Yarn is used for knitting, crocheting, wrapping, and making soft things.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, caring, and helpful to others.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: SimWorld) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(nursery).
place(garden).
place(porch).

treasure(yarn).
treasure(ribbon).
treasure(sock).

feature(kindness).
feature(bravery).
feature(rhyme).

good_story(P, T) :- place(P), treasure(T), compatible(P, T).
compatible(nursery, yarn).
compatible(garden, yarn).
compatible(porch, yarn).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    for f in ("kindness", "bravery", "rhyme"):
        lines.append(asp.fact("feature", f))
    for p in PLACES:
        for t in TREASURES:
            if p == "nursery" and t == "yarn":
                lines.append(asp.fact("compatible", p, t))
            if p == "garden" and t == "yarn":
                lines.append(asp.fact("compatible", p, t))
            if p == "porch" and t == "yarn":
                lines.append(asp.fact("compatible", p, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = {
        ("nursery", "yarn"),
        ("garden", "yarn"),
        ("porch", "yarn"),
    }
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [("nursery", "yarn"), ("garden", "yarn"), ("porch", "yarn")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with yarn, kindness, bravery, and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy", "child"], default="child")
    ap.add_argument("--helper-type", choices=["mother", "father", "grandparent", "aunt", "uncle"], default="mother")
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
    if getattr(args, "treasure", None) and getattr(args, "treasure", None) != "yarn":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    treasure = "yarn"
    if (place, treasure) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    hero_type = getattr(args, "hero_type", None)
    helper_type = getattr(args, "helper_type", None)
    return StoryParams(place=place, treasure=treasure, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


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
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:")
        for p, t in combos:
            print(f"  {p:8} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in ("nursery", "garden", "porch"):
            params = StoryParams(
                place=place,
                treasure="yarn",
                hero_name="Mia",
                hero_type="child",
                helper_name="Mama",
                helper_type="mother",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
