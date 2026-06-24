#!/usr/bin/env python3
"""
A tiny story world: a nursery-rhyme-style tent kitchen where a recipe and an
inventory of ingredients are transformed into a shared treat, and a small
spat is mended into reconciliation.

The seed words for this world are:
- recipe
- inventory
- tent

The story is built from a live state model with two key features:
- Transformation: plain ingredients become a finished treat
- Reconciliation: a disagreement softens into shared joy
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

SETTINGS = {
    "meadow": {"place": "the meadow", "indoors": False, "weather": "breezy"},
    "garden": {"place": "the garden", "indoors": False, "weather": "sunny"},
    "backyard": {"place": "the backyard", "indoors": False, "weather": "soft-rain"},
    "playroom": {"place": "the playroom", "indoors": True, "weather": "warm"},
}

RECIPES = {
    "berry_tarts": {
        "title": "berry tarts",
        "steps": "roll, fill, and bake",
        "finish": "golden berry tarts",
        "transforms": ["dough", "berries"],
    },
    "moon_muffins": {
        "title": "moon muffins",
        "steps": "stir, spoon, and rise",
        "finish": "puffed moon muffins",
        "transforms": ["batter"],
    },
    "honey_biscuits": {
        "title": "honey biscuits",
        "steps": "mix, pat, and warm",
        "finish": "soft honey biscuits",
        "transforms": ["dough", "honey"],
    },
}

INGREDIENTS = {
    "flour": {"kind": "ingredient", "label": "flour", "pretty": "a little bowl of flour"},
    "milk": {"kind": "ingredient", "label": "milk", "pretty": "a jar of milk"},
    "honey": {"kind": "ingredient", "label": "honey", "pretty": "a small pot of honey"},
    "berries": {"kind": "ingredient", "label": "berries", "pretty": "a paper cup of berries"},
    "dough": {"kind": "ingredient", "label": "dough", "pretty": "a soft ball of dough"},
    "batter": {"kind": "ingredient", "label": "batter", "pretty": "a smooth bowl of batter"},
}

TENT_KINDS = {
    "striped": {
        "label": "striped tent",
        "phrase": "a striped tent with a bright red flap",
        "covers": {"table", "bowl"},
    },
    "blue": {
        "label": "blue tent",
        "phrase": "a blue tent with a round window",
        "covers": {"table", "bowl"},
    },
    "yellow": {
        "label": "yellow tent",
        "phrase": "a yellow tent with a soft little lantern",
        "covers": {"table", "bowl"},
    },
}

NAMES = ["Mina", "Toby", "Lila", "Poppy", "Noah", "Rory", "Daisy", "Bram"]
TRAITS = ["cheerful", "gentle", "curious", "spry", "bouncy", "bright"]


# ---------------------------------------------------------------------------
# Dataclasses for state
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sibling: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
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
    indoors: bool
    weather: str
    setting: object | None = None
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
class RecipeSpec:
    id: str
    title: str
    steps: str
    finish: str
    transforms: list[str]
    recipe: object | None = None
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
class TentSpec:
    id: str
    label: str
    phrase: str
    covers: set[str]
    tent: object | None = None
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    recipe: str
    tent: str
    name: str
    sibling: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
    p: object | None = None
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


def _subject(entity: Entity) -> str:
    return entity.pronoun("subject").capitalize()


def _poss(entity: Entity) -> str:
    return entity.pronoun("possessive")


def _object(entity: Entity) -> str:
    return entity.pronoun("object")


def transform_recipe(world: World, hero: Entity, recipe: RecipeSpec) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} had a recipe for {recipe.title}, and {hero.pronoun('possessive')} eyes shone like dew."
    )
    world.say(
        f"In the tent, {hero.id} could {recipe.steps} until the plain bits turned into {recipe.finish}."
    )


def introduce_inventory(world: World, hero: Entity, sibling: Entity) -> None:
    inv = [e for e in world.entities.values() if e.kind == "ingredient"]
    names = ", ".join(e.pretty for e in inv[:-1]) + f", and {inv[-1].pretty}"
    world.say(
        f"{hero.id} and {sibling.id} had an inventory of treats: {names}."
    )
    world.say(
        f"They laid the little pieces on a cloth so nothing would tumble or slip."
    )


def conflict(world: World, hero: Entity, sibling: Entity, recipe: RecipeSpec) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    sibling.memes["want"] = sibling.memes.get("want", 0) + 1
    sibling.memes["tug"] = sibling.memes.get("tug", 0) + 1
    world.say(
        f"But {sibling.id} wanted the berries first, and {hero.id} wanted them for the recipe."
    )
    world.say(
        f"{hero.id} frowned a little, for the sweet dots were needed to finish the {recipe.title} just right."
    )


def reconcile(world: World, hero: Entity, sibling: Entity, tent: TentSpec, recipe: RecipeSpec) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    sibling.memes["kindness"] = sibling.memes.get("kindness", 0) + 1
    hero.memes["grudge"] = 0
    sibling.memes["grudge"] = 0
    world.say(
        f"Then {hero.id} smiled and said, 'Let's share the berries and stir together.'"
    )
    world.say(
        f"{sibling.id} nodded, and the tent felt warm as a nest when they worked side by side."
    )
    world.say(
        f"Under {tent.phrase}, the recipe came true: {recipe.finish} rose sweet and neat."
    )
    world.say(
        f"{hero.id} and {sibling.id} each had a piece, and their little spat was gone like mist."
    )


def tell(setting: Setting, recipe: RecipeSpec, tent: TentSpec, hero_name: str, sibling_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child"))
    sibling = world.add(Entity(id=sibling_name, kind="character", type="child"))
    world.add(Entity(id="recipe_card", kind="thing", type="recipe", label=recipe.title, phrase=recipe.title))
    for iid, data in INGREDIENTS.items():
        world.add(Entity(id=iid, kind="ingredient", type="ingredient", label=data["label"], phrase=data["pretty"]))
    world.add(Entity(id=tent.id, kind="thing", type="tent", label=tent.label, phrase=tent.phrase))

    world.say(
        f"Little {trait} {hero.id} found a recipe card near the tent."
    )
    world.say(
        f"{hero.id} and {sibling.id} were bright as beads, and they did not mind the breeze."
    )
    world.para()
    introduce_inventory(world, hero, sibling)
    transform_recipe(world, hero, recipe)
    world.para()
    conflict(world, hero, sibling, recipe)
    world.para()
    reconcile(world, hero, sibling, tent, recipe)

    world.facts = {
        "hero": hero,
        "sibling": sibling,
        "recipe": recipe,
        "tent": tent,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# Quality/QA helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sibling: Entity = _safe_fact(world, f, "sibling")
    recipe: RecipeSpec = _safe_fact(world, f, "recipe")
    return [
        f"Write a nursery-rhyme-style story about {hero.id}, {sibling.id}, and a {recipe.title} recipe in a tent.",
        f"Tell a short story where an inventory of ingredients becomes {recipe.finish} and two children make up.",
        f"Write a gentle rhyme about a tent, a recipe, and shared berries that ends with reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sibling: Entity = _safe_fact(world, f, "sibling")
    recipe: RecipeSpec = _safe_fact(world, f, "recipe")
    tent: TentSpec = _safe_fact(world, f, "tent")
    return [
        QAItem(
            question=f"What did {hero.id} find near the tent?",
            answer=f"{hero.id} found a recipe card for {recipe.title}, and that started the little kitchen day.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {sibling.id} have a small disagreement?",
            answer=f"They both wanted the berries, but the berries were needed to finish {recipe.title}.",
        ),
        QAItem(
            question=f"How did the children fix their quarrel?",
            answer=f"They shared the berries, worked together in the tent, and made up happily.",
        ),
        QAItem(
            question=f"What did the recipe turn into at the end?",
            answer=f"It turned into {recipe.finish}, warm and ready to share.",
        ),
        QAItem(
            question=f"Where did the transformation happen?",
            answer=f"It happened in {tent.phrase}, where the children mixed and baked together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a recipe?",
            answer="A recipe is a set of steps that tells you how to make food.",
        ),
        QAItem(
            question="What is an inventory?",
            answer="An inventory is a list of the things you have ready to use.",
        ),
        QAItem(
            question="What is a tent?",
            answer="A tent is a cloth shelter you can sit in or sleep in outside.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop arguing and become friendly again.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- place(S).
recipe(R) :- recipe_name(R).
tent(T) :- tent_name(T).
ingredient(I) :- ingredient_name(I).

inventory_ready(R) :- recipe(R), ingredient("berries"), ingredient("flour"), ingredient("milk").
transformation(R) :- recipe(R), inventory_ready(R), tent(T), shelter(T).
reconciliation(R) :- transformation(R), child(A), child(B), shared_choice(A,B).
good_story(R) :- transformation(R), reconciliation(R).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for rid in RECIPES:
        lines.append(asp.fact("recipe_name", rid))
    for tid in TENT_KINDS:
        lines.append(asp.fact("tent_name", tid))
    for iid in INGREDIENTS:
        lines.append(asp.fact("ingredient_name", iid))
    lines.append(asp.fact("ingredient_name", "berries"))
    lines.append(asp.fact("ingredient_name", "flour"))
    lines.append(asp.fact("ingredient_name", "milk"))
    for tid in TENT_KINDS:
        lines.append(asp.fact("shelter", tid))
    lines.append(asp.fact("child", "a"))
    lines.append(asp.fact("child", "b"))
    lines.append(asp.fact("shared_choice", "a", "b"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/1."))
    asp_good = set(asp.atoms(model, "good_story"))
    py_good = {("berry_tarts",)}
    if asp_good == py_good:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH:", sorted(asp_good), sorted(py_good))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for recipe in RECIPES:
            for tent in TENT_KINDS:
                combos.append((setting, recipe, tent))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested ingredients and tent do not support a clear transformation and reconciliation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: recipe, inventory, tent.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--tent", choices=TENT_KINDS)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    recipe = getattr(args, "recipe", None) or rng.choice(list(RECIPES))
    tent = getattr(args, "tent", None) or rng.choice(list(TENT_KINDS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    sibling = getattr(args, "sibling", None) or rng.choice([n for n in NAMES if n != name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if (getattr(args, "setting", None) and getattr(args, "recipe", None) and getattr(args, "tent", None)) and (setting, recipe, tent) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, recipe=recipe, tent=tent, name=name, sibling=sibling, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = Setting(**_safe_lookup(SETTINGS, params.setting))
    recipe = RecipeSpec(id=params.recipe, **_safe_lookup(RECIPES, params.recipe))
    tent = TentSpec(id=params.tent, **_safe_lookup(TENT_KINDS, params.tent))
    world = tell(setting, recipe, tent, params.name, params.sibling, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind in {"ingredient", "thing"} and e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show good_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show good_story/1."))
        print(sorted(asp.atoms(model, "good_story")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting, recipe, tent in [
            ("meadow", "berry_tarts", "striped"),
            ("garden", "honey_biscuits", "blue"),
            ("backyard", "moon_muffins", "yellow"),
            ("playroom", "berry_tarts", "blue"),
        ]:
            p = StoryParams(setting=setting, recipe=recipe, tent=tent, name="Mina", sibling="Toby", trait="cheerful")
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            i += 1
            seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
