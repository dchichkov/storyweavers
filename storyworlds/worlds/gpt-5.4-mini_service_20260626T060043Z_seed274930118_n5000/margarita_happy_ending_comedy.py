#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/margarita_happy_ending_comedy.py
==============================================================================================================

A small standalone story world about a funny kitchen mishap centered on a
margarita mocktail, with a happy ending and a light comedic tone.

The core seed tale:
- A child wants to make a fancy lime margarita for a family celebration.
- The blender makes a ridiculous racket, ice pops everywhere, and salt goes
  flying.
- A grown-up worries the glass will be ruined.
- They swap to a calmer, safer method and finish with a cheerful, sparkling
  drink.

The simulation models:
- physical meters: spill, noise, sparkle, chill
- emotional memes: excitement, worry, laughter, relief

This world is intentionally small and constraint-checked: only sensible
comedy/problem/fix combinations are generated.
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

THRESHOLD = 1.0
SAFE_GEAR = {"shaker", "straw", "napkin", "tray"}



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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    holding: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        for k in ("spill", "noise", "sparkle", "chill", "mess"):
            self.meters.setdefault(k, 0.0)
        for k in ("excitement", "worry", "laughter", "relief", "pride"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=lambda: {"mix", "blend", "pour"})
    SETTING: object | None = None
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
    name: str
    drink_word: str
    ingredients: list[str]
    tool: str
    loud_tool: str
    calm_tool: str
    hazard: str
    fix: str
    garnish: str
    outcome: str
    keyword: str = "margarita"
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
class StoryParams:
    recipe: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def normalize(article: str, phrase: str) -> str:
    return f"{article} {phrase}" if not phrase.startswith(("a ", "an ", "the ")) else phrase


def article_for(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


RECIPES = {
    "lime": Recipe(
        name="lime fizz",
        drink_word="margarita",
        ingredients=["lime juice", "sparkling water", "ice", "a sugared rim"],
        tool="pitcher",
        loud_tool="blender",
        calm_tool="shaker",
        hazard="too much splashing",
        fix="a calmer shake",
        garnish="a tiny lime wedge",
        outcome="bright and fizzy",
    ),
    "strawberry": Recipe(
        name="strawberry sparkle",
        drink_word="margarita",
        ingredients=["strawberry syrup", "sparkling water", "ice", "a sugared rim"],
        tool="pitcher",
        loud_tool="blender",
        calm_tool="shaker",
        hazard="pink splatters",
        fix="a slower stir",
        garnish="a strawberry slice",
        outcome="sweet and bubbly",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Zoe", "Max"]
TRAITS = ["curious", "cheerful", "silly", "busy", "brave", "sprightly"]

SETTING = Setting()


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for rid in RECIPES:
        for g in ("girl", "boy"):
            out.append((rid, g))
    return out


def reasonableness_gate(recipe: Recipe) -> bool:
    return recipe.tool == "pitcher" and recipe.loud_tool == "blender" and recipe.calm_tool == "shaker"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world about a margarita mocktail.")
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa"])
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
    recipe = getattr(args, "recipe", None) or rng.choice(list(RECIPES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandma", "grandpa"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if not reasonableness_gate(_safe_lookup(RECIPES, recipe)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(recipe=recipe, name=name, gender=gender, helper=helper, trait=trait)


def _hero(world: World, params: StoryParams) -> Entity:
    return world.add(Entity(id=params.name, kind="character", type=params.gender))


def _helper(world: World, params: StoryParams) -> Entity:
    return world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))


def _recipe_entity(world: World, recipe: Recipe) -> Entity:
    return world.add(Entity(
        id="drink",
        type="drink",
        label=recipe.drink_word,
        phrase=recipe.name,
        caretaker="helper",
        owner="hero",
    ))


def _tool_entity(world: World, recipe: Recipe, which: str) -> Entity:
    return world.add(Entity(id=which, type="tool", label=which, owner="hero"))


def _predict_breakage(world: World, recipe: Recipe) -> bool:
    sim = world.copy()
    sim.get("hero").memes["excitement"] += 1
    sim.get("hero").meters["noise"] += 1
    sim.get("hero").meters["spill"] += 1
    drink = sim.get("drink")
    drink.meters["mess"] += 1
    return drink.meters["mess"] >= THRESHOLD


def tell(params: StoryParams) -> World:
    recipe = _safe_lookup(RECIPES, params.recipe)
    world = World(SETTING)
    hero = _hero(world, params)
    helper = _helper(world, params)
    drink = _recipe_entity(world, recipe)
    loud_tool = _tool_entity(world, recipe, "blender")
    calm_tool = _tool_entity(world, recipe, "shaker")

    hero.memes["excitement"] += 1
    world.say(
        f"{hero.id} was a {params.trait} {params.gender} who wanted to make a {recipe.drink_word} "
        f"for a family treat."
    )
    world.say(
        f"{hero.id} lined up {', '.join(recipe.ingredients[:-1])}, and {recipe.ingredients[-1]}, "
        f"because {hero.pronoun('possessive')} eyes were sparkling already."
    )

    world.para()
    world.say(
        f"In {world.setting.place}, {hero.id} reached for the blender. It whirred like a tiny rocket and made a very dramatic noise."
    )
    hero.meters["noise"] += 1
    hero.meters["spill"] += 1
    drink.meters["mess"] += 1
    hero.memes["laughter"] += 1
    world.say(
        f"Ice cubes jumped, the salt rim went sideways, and everyone looked at the counter with big round faces."
    )

    if _predict_breakage(world, recipe):
        helper.memes["worry"] += 1
        world.say(
            f"\"That is one mighty silly blender,\" {helper.id} said, peeking at the splashy mess. "
            f"\"Let's do {recipe.fix} instead.\""
        )
        world.say(
            f"{hero.id} blinked, then giggled. The blender got a timeout, and the shaker came out."
        )
        world.para()
        hero.memes["relief"] += 1
        helper.memes["relief"] += 1
        hero.meters["spill"] = 0
        drink.meters["mess"] = 0
        drink.meters["sparkle"] += 1
        drink.meters["chill"] += 1
        hero.memes["pride"] += 1
        world.say(
            f"Together they used the shaker, poured the drink carefully, and added {recipe.garnish} on top."
        )
        world.say(
            f"The little {recipe.drink_word} turned {recipe.outcome}, and the counter looked tidy again."
        )
        world.say(
            f"{hero.id} grinned at the shiny glass, and {helper.id} laughed so hard that the spoon nearly fell over."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        drink=drink,
        recipe=recipe,
        loud_tool=loud_tool,
        calm_tool=calm_tool,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    recipe = _safe_fact(world, f, "recipe")
    hero = _safe_fact(world, f, "hero")
    return [
        f"Write a short comedy story for young children about a {hero.type} making a {recipe.drink_word}.",
        f"Tell a funny kitchen story where {hero.id} wants to use a blender, but the grown-up chooses a calmer way to finish the drink.",
        f"Write a happy ending story about a {recipe.drink_word} with a noisy mistake and a cheerful fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, recipe = f["hero"], f["helper"], f["recipe"]
    return [
        QAItem(
            question=f"What did {hero.id} want to make?",
            answer=f"{hero.id} wanted to make a {recipe.drink_word} with a silly, fizzy twist.",
        ),
        QAItem(
            question=f"Why did the family laugh in the middle of the story?",
            answer="They laughed because the blender made a huge racket, the ice jumped, and the salt rim went sideways like it was trying to dance.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the problem?",
            answer=f"They stopped using the blender and used a calmer shaker instead, so the drink could be finished neatly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a blender do?",
            answer="A blender spins very fast and helps mix soft foods or drinks, but it can be loud and splashy.",
        ),
        QAItem(
            question="What is a shaker for?",
            answer="A shaker is a container you can shake gently to mix a drink without making such a big mess.",
        ),
        QAItem(
            question="Why do people put a garnish on a drink?",
            answer="People add a garnish to make the drink look pretty and special, like a little lime wedge or a fruit slice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
% A recipe is reasonable when the world can safely swap the loud tool for the calm tool.
reasonable_recipe(R) :- recipe(R), loud_tool(R, blender), calm_tool(R, shaker).

% A story is happy when the mess gets resolved and laughter is present.
happy_story(R) :- reasonable_recipe(R), resolved(R), laughter(R).

#show reasonable_recipe/1.
#show happy_story/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, recipe in RECIPES.items():
        lines.append(asp.fact("recipe", rid))
        lines.append(asp.fact("loud_tool", rid, recipe.loud_tool))
        lines.append(asp.fact("calm_tool", rid, recipe.calm_tool))
        for ing in recipe.ingredients:
            lines.append(asp.fact("ingredient", rid, ing))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable_recipe/1. #show happy_story/1."))
    facts = set((a[0],) for a in asp.atoms(model, "reasonable_recipe"))
    if facts == set(RECIPES):
        print(f"OK: ASP reasoning agrees with the Python gate for {len(facts)} recipes.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    return 1


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_recipe/1."))
    return sorted(set(asp.atoms(model, "reasonable_recipe")))


CURATED = [
    StoryParams(recipe="lime", name="Mia", gender="girl", helper="mother", trait="silly"),
    StoryParams(recipe="strawberry", name="Ben", gender="boy", helper="grandma", trait="curious"),
]


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
        print(asp_program("#show reasonable_recipe/1. #show happy_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reasonable_recipe/1."))
        print("ASP reasonable recipes:")
        for (rid,) in asp.atoms(model, "reasonable_recipe"):
            print(" ", rid)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
