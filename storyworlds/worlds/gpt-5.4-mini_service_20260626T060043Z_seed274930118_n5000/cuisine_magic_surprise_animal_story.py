#!/usr/bin/env python3
"""
A standalone storyworld script for a tiny Animal Story-inspired cuisine domain.

Premise:
- An animal cook makes food in a kitchen.
- A magical surprise changes one ingredient or tool.
- The tension is whether the meal can still be finished.
- The resolution uses a sensible fix, helper, or substitution.

The world is modeled with physical meters and emotional memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    animal: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "dog", "rabbit", "fox", "bear", "mouse", "bird", "lion"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Kitchen:
    place: str = "the kitchen"
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
class Recipe:
    id: str
    verb: str
    gerund: str
    ingredient: str
    needed_tool: str
    surprise: str
    fix: str
    joy_gain: str
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
    kind: str
    usable_for: set[str] = field(default_factory=set)
    protective: bool = False
    tool: object | None = None
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
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.magic_twist: str = ""

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    animal: str
    name: str
    place: str
    recipe: str
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


KITCHENS = {
    "home": Kitchen(place="the kitchen", affords={"stir", "mix", "bake", "serve"}),
    "bakery": Kitchen(place="the bakery kitchen", affords={"stir", "mix", "bake", "serve"}),
    "camp": Kitchen(place="the camp kitchen", affords={"stir", "mix", "cook", "serve"}),
}

RECIPES = {
    "soup": Recipe(
        id="soup",
        verb="make soup",
        gerund="stirring soup",
        ingredient="carrots",
        needed_tool="ladle",
        surprise="the carrots turned into tiny stars",
        fix="use the spoon-shaped ladle",
        joy_gain="warm and proud",
        tags={"cuisine", "magic", "surprise"},
    ),
    "pie": Recipe(
        id="pie",
        verb="bake a pie",
        gerund="baking a pie",
        ingredient="berries",
        needed_tool="rolling pin",
        surprise="the berries began to float like balloons",
        fix="gently press the berries back into the crust",
        joy_gain="bright and relieved",
        tags={"cuisine", "magic", "surprise"},
    ),
    "bread": Recipe(
        id="bread",
        verb="make bread",
        gerund="kneading bread",
        ingredient="flour",
        needed_tool="mixing bowl",
        surprise="the flour puffed into a cloud of sparkles",
        fix="cover the bowl and keep mixing slowly",
        joy_gain="calm and cheerful",
        tags={"cuisine", "magic", "surprise"},
    ),
    "salad": Recipe(
        id="salad",
        verb="make salad",
        gerund="tossing salad",
        ingredient="lettuce",
        needed_tool="salad bowl",
        surprise="the lettuce began to dance on the plate",
        fix="tap the bowl with a wooden spoon",
        joy_gain="surprised but happy",
        tags={"cuisine", "magic", "surprise"},
    ),
}

ANIMALS = [
    ("cat", "Mimi"),
    ("dog", "Bingo"),
    ("rabbit", "Pip"),
    ("fox", "Rina"),
    ("bear", "Toby"),
    ("mouse", "Nia"),
    ("bird", "Coco"),
    ("lion", "Lulu"),
]

TRAITS = ["gentle", "brave", "curious", "cheerful", "busy", "patient"]

ASP_RULES = r"""
animal(A) :- animal_kind(A,_).
recipe(R) :- recipe_kind(R).
magic_surprise(R) :- recipe_kind(R), surprise(R,_).
needs_fix(R) :- recipe_kind(R), tool(R,_).
safe_story(A,R) :- animal(A), recipe(R), magic_surprise(R), needs_fix(R).
#show safe_story/2.
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal cuisine storyworld with a magical surprise.")
    ap.add_argument("--place", choices=KITCHENS)
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--animal", choices=[a for a, _ in ANIMALS])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in KITCHENS:
        for recipe in RECIPES:
            for animal, _ in ANIMALS:
                combos.append((place, recipe, animal))
    return combos


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a, _ in ANIMALS:
        lines.append(asp.fact("animal_kind", a, "animal"))
    for r in RECIPES.values():
        lines.append(asp.fact("recipe_kind", r.id))
        lines.append(asp.fact("surprise", r.id, r.surprise))
        lines.append(asp.fact("tool", r.id, r.needed_tool))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_story/2."))
    safe = set(asp.atoms(model, "safe_story"))
    py = {(animal, recipe) for _, recipe, animal in valid_combos()}
    if safe == py:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(safe - py))
    print("only in py:", sorted(py - safe))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "recipe", None):
        combos = [c for c in combos if c[1] == getattr(args, "recipe", None)]
    if getattr(args, "animal", None):
        combos = [c for c in combos if c[2] == getattr(args, "animal", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, recipe, animal = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice([n for a, n in ANIMALS if a == animal] or [rng.choice([n for _, n in ANIMALS])])
    return StoryParams(animal=animal, name=name, place=place, recipe=recipe)


def _setup(world: World, params: StoryParams) -> None:
    recipe = _safe_lookup(RECIPES, params.recipe)
    animal = world.add_entity(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=params.name,
        meters={"hunger": 1.0, "joy": 0.5},
        memes={"hope": 1.0},
    ))
    world.facts["hero"] = animal
    world.facts["recipe"] = recipe
    world.facts["place"] = world.kitchen
    world.say(f"{params.name} was a {rng_trait(params.seed)} {params.animal} who loved cooking in {world.kitchen.place}.")
    world.say(f"{animal.pronoun().capitalize()} wanted to {recipe.verb}, especially with {recipe.ingredient}.")
    world.para()
    world.say(f"One day, {params.name} started {recipe.gerund} when {recipe.surprise}!")
    animal.memes["surprise"] = 1.0
    animal.memes["worry"] = 1.0
    world.magic_twist = recipe.surprise
    world.say(f"{params.name} blinked at the surprise, but {animal.pronoun()} did not want the meal to stop.")


def rng_trait(seed: Optional[int]) -> str:
    rng = random.Random(seed)
    return rng.choice(TRAITS)


def _resolve(world: World, params: StoryParams) -> None:
    recipe = _safe_fact(world, world.facts, "recipe")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    tool = Item(id=recipe.needed_tool, label=recipe.needed_tool, kind="tool", usable_for={recipe.id})
    world.add_item(tool)
    world.para()
    world.say(f"{hero.pronoun().capitalize()} looked at the {recipe.needed_tool} and took a slow breath.")
    world.say(f"Then {hero.pronoun()} chose to {recipe.fix}, because the kitchen still smelled good and the food could still be saved.")
    hero.memes["hope"] += 1.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1.0
    world.say(f"After that, {params.name} finished {recipe.gerund}, and the dish came out {recipe.joy_gain}.")


def _ending(world: World, params: StoryParams) -> None:
    recipe = _safe_fact(world, world.facts, "recipe")
    world.para()
    world.say(f"When the plate was ready, {params.name} served it with a grin.")
    world.say(f"The magical surprise was still there, but now it made the meal feel special instead of scary.")
    world.say(f"By the end, {params.name} had {recipe.joy_gain} eyes and a happy kitchen full of {recipe.id}.")


def generate_storyworld(params: StoryParams) -> World:
    world = World(_safe_lookup(KITCHENS, params.place))
    _setup(world, params)
    _resolve(world, params)
    _ending(world, params)
    return world


def generation_prompts(params: StoryParams) -> list[str]:
    recipe = _safe_lookup(RECIPES, params.recipe)
    return [
        f"Write a short Animal Story about {params.name}, a {params.animal}, who wants to {recipe.verb} with a magical surprise.",
        f"Tell a child-friendly kitchen story where {params.name} keeps cooking after {recipe.surprise}.",
        f"Make a gentle story about {params.name} in {_safe_lookup(KITCHENS, params.place).place} using the word '{recipe.ingredient}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    recipe: Recipe = _safe_fact(world, world.facts, "recipe")
    return [
        QAItem(
            question=f"What did {hero.label} want to do in the kitchen?",
            answer=f"{hero.label} wanted to {recipe.verb}.",
        ),
        QAItem(
            question=f"What magical surprise happened while {hero.label} was cooking?",
            answer=f"{recipe.surprise.capitalize()}.",
        ),
        QAItem(
            question=f"How did {hero.label} solve the problem?",
            answer=f"{hero.label} chose to {recipe.fix}, and that helped finish the dish.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cuisine?",
            answer="Cuisine means cooking and the kinds of food people make and eat.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you were not ready for it.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something impossible in real life that can happen in a story, like sparkling food or floating berries.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
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
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    for i in world.items.values():
        lines.append(f"item {i.id}: label={i.label} kind={i.kind}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_storyworld(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
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
    StoryParams(animal="cat", name="Mimi", place="home", recipe="soup"),
    StoryParams(animal="rabbit", name="Pip", place="bakery", recipe="pie"),
    StoryParams(animal="bear", name="Toby", place="camp", recipe="bread"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show safe_story/2."))
        pairs = sorted(set(asp.atoms(model, "safe_story")))
        print(f"{len(pairs)} safe stories:")
        for animal, recipe in pairs:
            print(f"  {animal} + {recipe}")
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
            header = f"### {p.name}: {p.animal} making {p.recipe} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
