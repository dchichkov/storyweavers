#!/usr/bin/env python3
"""
storyworlds/worlds/lack_color_monger_happy_ending_cautionary_rhyming.py
=======================================================================

A small storyworld about a color monger, a little lack of color, and a tidy
happy ending with a cautionary rhyme.

Premise:
- A child visits a color monger who sells bright jars of color.
- The child has a lack of color in their picture: a blank gray page and a mood
  that feels flat.
- The child wants to splash the page with color, but first must heed a warning
  about mixing the wrong things or wasting the jars.

This world is intentionally tiny and strongly constrained:
- A story only generates when the chosen scene is reasonable.
- The child can only get a happy ending if the caution is acknowledged and a
  fitting fix is chosen.
- The prose is built from world state rather than a frozen paragraph.

Style goals:
- Rhyming, child-facing, concrete.
- Gentle caution: careful handling, no spills, no scorch, no mess.
- Clear arc: lack -> warning -> choice -> bright ending.

The inline ASP twin mirrors the Python reasonableness gate.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    protective: bool = False
    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    monger: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Place:
    id: str
    label: str
    indoor: bool = False
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
class Problem:
    id: str
    lack: str
    verb: str
    gerund: str
    warning: str
    risk: str
    mood: str
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
class Item:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    protective: bool = False
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "shop": Place("shop", "the color shop", indoor=True),
    "stall": Place("stall", "the market stall", indoor=False),
    "studio": Place("studio", "the little studio", indoor=True),
}

PROBLEMS = {
    "gray_page": Problem(
        id="gray_page",
        lack="a blank gray page",
        verb="paint a bright scene",
        gerund="painting bright scenes",
        warning="If you mix the jars in a rush, the page may go dull",
        risk="the picture could turn muddy and dim",
        mood="flat",
        tags={"color", "paint", "warning"},
    ),
    "winter_cloak": Problem(
        id="winter_cloak",
        lack="a pale winter cloak",
        verb="stain a pattern",
        gerund="staining patterns",
        warning="If the dye spills, the cloak may lose its shine",
        risk="the cloak could end up stained and plain",
        mood="cold",
        tags={"dye", "cloth", "warning"},
    ),
    "faded_flag": Problem(
        id="faded_flag",
        lack="a faded little flag",
        verb="restore a brave stripe",
        gerund="restoring brave stripes",
        warning="If the color drips, the flag may lose its glow",
        risk="the flag could end up streaky and slow",
        mood="worn",
        tags={"color", "cloth", "warning"},
    ),
}

ITEMS = {
    "crayons": Item("crayons", "crayons", "a box of bright crayons", guards={"dry"}, plural=True),
    "paint": Item("paint", "paint pots", "three small paint pots", guards={"dry"}, plural=True),
    "dye": Item("dye", "dye cups", "two tidy dye cups", guards={"dry"}, plural=True),
    "apron": Item("apron", "apron", "a clean apron", guards={"spills"}, covers={"torso"}),
    "cloth": Item("cloth", "cloth", "a soft cloth", guards={"wipe"}, covers={"hands"}),
}

HERO_NAMES = ["Mina", "Nico", "Lila", "Ravi", "Tessa", "Pip", "Milo", "Sana"]
TRAITS = ["gentle", "cheery", "curious", "careful", "spry", "bright"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    item: str
    name: str
    gender: str
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


def problem_needs_item(problem: Problem, item: Item) -> bool:
    if problem.id == "gray_page":
        return item.id in {"crayons", "paint"}
    if problem.id in {"winter_cloak", "faded_flag"}:
        return item.id in {"dye", "paint"}
    return False


def compatible_fix(problem: Problem, item: Item) -> bool:
    if problem.id == "gray_page" and item.id == "crayons":
        return True
    if problem.id == "winter_cloak" and item.id == "dye":
        return True
    if problem.id == "faded_flag" and item.id == "paint":
        return True
    return False


def explain_rejection(problem: Problem, item: Item) -> str:
    return (
        f"(No story: {item.label} does not reasonably fix {problem.lack}. "
        f"The cautionary rhyme needs a real helper, not a mismatch.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for item in ITEMS:
                if compatible_fix(_safe_lookup(PROBLEMS, problem), _safe_lookup(ITEMS, item)):
                    combos.append((place, problem, item))
    return combos


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def setup_story(world: World, hero: Entity, problem: Problem, item: Item, monger: Entity) -> None:
    world.say(
        f"{hero.id} went by with a sigh so slight, "
        f"for {problem.lack} had dimmed the day to gray and white."
    )
    world.say(
        f"{hero.id} wished to {problem.verb}, to sing in a coloring light, "
        f"and the color monger smiled with jars that shone so bright."
    )
    world.say(
        f"The monger showed {hero.pronoun('object')} {item.phrase}, neat as could be, "
        f"and said, “Take care, dear heart, and listen carefully.”"
    )


def conflict_story(world: World, hero: Entity, problem: Problem, item: Item) -> None:
    world.para()
    world.say(
        f"“{problem.warning},” the monger said with a measured beat. "
        f"“A careless splash can make a merry mess turn incomplete.”"
    )
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    world.say(
        f"{hero.id} wanted color, quick and grand, but knew the rhyme was true: "
        f"fast hands can blur a picture, and the wrong mix can sneak on through."
    )


def resolution_story(world: World, hero: Entity, problem: Problem, item: Item, helper: Item) -> None:
    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"So {hero.id} chose the careful way, with {helper.label} held just right, "
        f"and kept the colors lined in rows, not rushed nor wild nor spright."
    )
    world.say(
        f"With steady hands and patient plans, {hero.id} made the page sing bright; "
        f"the gray was gone, the mood was warm, and the picture beamed with light."
    )
    world.say(
        f"The monger chuckled, “See? Take care pays well; a cautious heart brings cheer. "
        f"Now the page is full of color, and the ending's happy here.”"
    )


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    item_def = _safe_lookup(ITEMS, params.item)
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
        meters={"joy": 0.0},
        memes={},
    ))
    monger = world.add(Entity(
        id="Monger",
        kind="character",
        type="person",
        label="color monger",
        meters={},
        memes={"care": 1.0},
    ))
    item = world.add(Entity(
        id=item_def.id,
        kind="thing",
        type=item_def.id,
        label=item_def.label,
        phrase=item_def.phrase,
        protective=item_def.protective,
        meters={},
        memes={},
        plural=item_def.plural,
    ))
    helper = world.add(Entity(
        id="helper",
        kind="thing",
        type="apron",
        label="apron",
        phrase="a clean apron",
        protective=True,
        meters={},
        memes={},
    ))

    world.facts.update(hero=hero, monger=monger, item=item, helper=helper, problem=problem, place=place)

    setup_story(world, hero, problem, item, monger)
    conflict_story(world, hero, problem, item)
    resolution_story(world, hero, problem, item, helper)

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a child who has {f["problem"].lack} and visits a color monger.',
        f"Tell a cautionary but happy story where {f['hero'].id} learns to use {f['item'].label} carefully.",
        f"Write a short rhyming tale about a color monger, a warning, and a bright ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    item = _safe_fact(world, f, "item")
    return [
        QAItem(
            question=f"What did {hero.id} lack at the start of the story?",
            answer=f"{hero.id} lacked {problem.lack}, so the day felt flat and gray.",
        ),
        QAItem(
            question=f"Why did the color monger give a caution?",
            answer=f"The monger warned that if the colors were mixed in a rush, {problem.risk}.",
        ),
        QAItem(
            question=f"What helped {hero.id} get a happy ending?",
            answer=f"Using {item.phrase} carefully helped {hero.id} make a bright picture without making a mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a color monger do?",
            answer="A color monger sells colors, paints, and other bright things people can use to make pictures or decorate cloth.",
        ),
        QAItem(
            question="Why should paint be handled carefully?",
            answer="Paint can drip, spill, or mix into a muddy color, so careful hands help keep clothes and pictures clean and bright.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking ahead so you can avoid a mistake or a mess.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(shop). place(stall). place(studio).

problem(gray_page). problem(winter_cloak). problem(faded_flag).

item(crayons). item(paint). item(dye). item(apron). item(cloth).

fix(gray_page, crayons).
fix(winter_cloak, dye).
fix(faded_flag, paint).

valid(Place, Problem, Item) :- place(Place), problem(Problem), item(Item), fix(Problem, Item).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about a color monger and careful brightening.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if getattr(args, "problem", None) and getattr(args, "item", None):
        prob = _safe_lookup(PROBLEMS, getattr(args, "problem", None))
        item = _safe_lookup(ITEMS, getattr(args, "item", None))
        if not compatible_fix(prob, item):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, problem, item = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, item=item, name=name, gender=gender, trait=trait)


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("shop", "gray_page", "crayons", "Mina", "girl", "careful"),
            StoryParams("stall", "winter_cloak", "dye", "Nico", "boy", "curious"),
            StoryParams("studio", "faded_flag", "paint", "Lila", "girl", "bright"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.problem} with {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
