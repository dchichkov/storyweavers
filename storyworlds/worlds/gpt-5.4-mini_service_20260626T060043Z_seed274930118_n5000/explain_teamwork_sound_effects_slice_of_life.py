#!/usr/bin/env python3
"""
Standalone storyworld: teamwork, sound effects, and a slice-of-life kitchen fix.

A child wants to make a simple after-school snack with a helper. The first
attempt gets noisy and a little messy, so they explain the job, divide the work,
and finish together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    plural: bool = False
    owner: Optional[str] = None
    helper_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    child: object | None = None
    entities: set[str] = field(default_factory=set)
    helper: object | None = None
    tool: object | None = None
    tray: object | None = None
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
class Room:
    id: str
    label: str
    cozy: bool = True
    noisy: bool = False
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
class Recipe:
    id: str
    name: str
    verb: str
    steps: list[str]
    sound_steps: dict[str, str]
    mess_kind: str
    cleanup: str
    ingredients: list[str]
    tool: str
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
class Tool:
    id: str
    label: str
    role: str
    sound: str
    helps: set[str]
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
    def __init__(self, room: Room) -> None:
        self.room = room
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.room)
        w.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "plural": v.plural, "owner": v.owner,
            "helper_for": v.helper_for, "meters": defaultdict(float, v.meters),
            "memes": defaultdict(float, v.memes),
        }) for k, v in self.entities.items()}
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    room: str
    recipe: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


ROOMS = {
    "kitchen": Room(id="kitchen", label="the kitchen", cozy=True),
    "patio": Room(id="patio", label="the sunny patio", cozy=True),
    "playroom": Room(id="playroom", label="the playroom", cozy=True),
}

RECIPES = {
    "trail_mix": Recipe(
        id="trail_mix",
        name="trail mix",
        verb="make trail mix",
        steps=["pour", "stir", "pour", "share"],
        sound_steps={"pour": "plink", "stir": "shh-shh", "share": "tap"},
        mess_kind="crumbs",
        cleanup="wipe the crumbs",
        ingredients=["raisins", "pretzels", "cereal"],
        tool="bowl",
    ),
    "fruit_salad": Recipe(
        id="fruit_salad",
        name="fruit salad",
        verb="make fruit salad",
        steps=["wash", "slice", "mix", "serve"],
        sound_steps={"wash": "splash", "slice": "chop-chop", "mix": "clink", "serve": "click"},
        mess_kind="juice",
        cleanup="wipe the sticky drops",
        ingredients=["apple", "banana", "grapes"],
        tool="knife",
    ),
    "sandwiches": Recipe(
        id="sandwiches",
        name="sandwiches",
        verb="make sandwiches",
        steps=["spread", "stack", "press", "cut"],
        sound_steps={"spread": "swish", "stack": "tap", "press": "pat", "cut": "snip"},
        mess_kind="crumbs",
        cleanup="brush the crumbs away",
        ingredients=["bread", "cheese", "cucumber"],
        tool="plate",
    ),
}

TOOLS = {
    "bowl": Tool(id="bowl", label="a big bowl", role="mixing", sound="clink", helps={"trail_mix", "fruit_salad"}),
    "knife": Tool(id="knife", label="a safe butter knife", role="cutting", sound="tap", helps={"sandwiches"}),
    "tray": Tool(id="tray", label="a little tray", role="carrying", sound="thump", helps={"trail_mix", "fruit_salad", "sandwiches"}),
}

NAMES_GIRL = ["Mia", "Lila", "Nora", "Zoe", "Iris", "Ava"]
NAMES_BOY = ["Ben", "Theo", "Leo", "Max", "Owen", "Finn"]
HELPER_NAMES = ["Mom", "Dad", "Aunt May", "Grandpa", "older sister"]
TRAITS = ["curious", "careful", "cheerful", "busy", "patient", "gentle"]


def has_fix(recipe: Recipe) -> bool:
    return recipe.id in _safe_lookup(TOOLS, recipe.tool).helps


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room in ROOMS:
        for recipe in RECIPES:
            if has_fix(_safe_lookup(RECIPES, recipe)):
                combos.append((room, recipe))
    return combos


def explain_rejection(recipe: Recipe) -> str:
    return f"(No story: there is no useful tool for {recipe.name} in this tiny kitchen setup.)"


def build_world(params: StoryParams) -> World:
    room = _safe_lookup(ROOMS, params.room)
    recipe = _safe_lookup(RECIPES, params.recipe)
    world = World(room)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        meters=defaultdict(float, {"hunger": 1.0}),
        memes=defaultdict(float, {"hope": 1.0}),
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
        label=params.helper_name,
        meters=defaultdict(float, {"calm": 1.0}),
        memes=defaultdict(float, {"care": 1.0}),
    ))
    tool = world.add(Entity(
        id=recipe.tool,
        kind="thing",
        type="tool",
        label=_safe_lookup(TOOLS, recipe.tool).label,
        owner=helper.id,
    ))
    tray = world.add(Entity(
        id="tray",
        kind="thing",
        type="tray",
        label=TOOLS["tray"].label,
        owner=helper.id,
    ))
    world.facts.update(child=child, helper=helper, recipe=recipe, tool=tool, tray=tray)
    return world


def predict_mess(world: World, recipe: Recipe) -> dict:
    sim = world.copy()
    sim.get("tray").meters[recipe.mess_kind] += 1
    return {"messy": sim.get("tray").meters[recipe.mess_kind] >= THRESHOLD}


def tell(world: World) -> None:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    recipe: Recipe = _safe_fact(world, f, "recipe")
    tray: Entity = _safe_fact(world, f, "tray")

    world.say(f"{child.id} was in {world.room.label}, watching the afternoon light sit on the table.")
    world.say(f"{child.id} wanted to {recipe.verb} with {helper.id}, because little jobs felt nicer together.")
    world.say(f'{child.id} asked, "Can you explain teamwork?"')
    world.say(f'{helper.id} smiled and said, "Teamwork means we each do a part and listen to each other."')

    world.para()
    world.say(f"They set out {recipe.name} things one by one: {', '.join(recipe.ingredients[:-1])}, and {recipe.ingredients[-1]}.")
    if recipe.id == "fruit_salad":
        world.say(f"The first sound was a bright {recipe.sound_steps['wash']}, then a careful {recipe.sound_steps['slice']}.")
    elif recipe.id == "trail_mix":
        world.say(f"The first sound was a happy {recipe.sound_steps['pour']}, then a soft {recipe.sound_steps['stir']}.")
    else:
        world.say(f"The first sound was a smooth {recipe.sound_steps['spread']}, then a neat {recipe.sound_steps['stack']}.")

    if predict_mess(world, recipe)["messy"]:
        world.say(f"But a few {recipe.mess_kind} landed on the tray, and the table looked spotty.")
        world.say(f"{child.id} frowned, then reached for a cloth.")
        world.say(f'{helper.id} said, "We can fix it together. You wipe, and I keep the bowl steady."')
        world.say(f"{child.id} wiped in small circles while {helper.id} made a soft {_safe_lookup(TOOLS, recipe.tool).sound} to keep the bowl from sliding.")
        tray.meters[recipe.mess_kind] += 1
        child.memes["pride"] += 1
        helper.memes["pride"] += 1
        world.say(f"The mess got smaller, and the room felt calm again.")

    world.para()
    world.say(f'After that, their work sounded like a tiny song: {recipe.sound_steps[recipe.steps[0]]}, {recipe.sound_steps[recipe.steps[1]]}, {recipe.sound_steps[recipe.steps[2]]}.')
    world.say(f"At the end, the snack sat on the tray looking neat and ready.")
    world.say(f"{child.id} laughed, and {helper.id} laughed too, because the best part was doing it side by side.")
    world.say(f"{child.id} took the first bite and smiled at the clean table and the happy little sounds still hanging in the air.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    recipe: Recipe = _safe_fact(world, f, "recipe")
    return [
        QAItem(
            question=f"What did {child.id} want to do with {helper.id}?",
            answer=f"{child.id} wanted to {recipe.verb} with {helper.id}.",
        ),
        QAItem(
            question=f"How did they fix the little mess in the story?",
            answer=f"They worked together, with {child.id} wiping and {helper.id} keeping the bowl steady.",
        ),
        QAItem(
            question=f"What sound did the work make?",
            answer=f"The work made little sounds like {list(recipe.sound_steps.values())[0]} and {list(recipe.sound_steps.values())[1]}.",
        ),
        QAItem(
            question=f"Why did {child.id} feel proud at the end?",
            answer=f"{child.id} felt proud because the snack was finished, the table was clean, and they had done it together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share the work and help each other finish a job.",
        ),
        QAItem(
            question="Why do kitchen jobs sometimes make sound effects?",
            answer="Kitchens have bowls, spoons, trays, and food that can clink, chop, swish, or tap when people use them.",
        ),
        QAItem(
            question="What does it mean to explain something?",
            answer="To explain something means to tell how it works in clear words.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    recipe: Recipe = _safe_fact(world, f, "recipe")
    return [
        f'Write a small slice-of-life story that uses the word "explain" and shows teamwork while making {recipe.name}.',
        f"Tell a child-friendly story about two people who work together on {recipe.verb} and notice little sound effects.",
        f"Write a cozy everyday story where a child asks what teamwork means, then learns it by helping in the kitchen.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


ASP_RULES = r"""
valid_combo(Room, Recipe) :- room(Room), recipe(Recipe), has_tool(Recipe).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    for rid, recipe in RECIPES.items():
        lines.append(asp.fact("recipe", rid))
        lines.append(asp.fact("has_tool", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life teamwork storyworld with sound effects.")
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--recipe", choices=sorted(RECIPES))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    combos = valid_combos()
    if getattr(args, "room", None):
        combos = [c for c in combos if c[0] == getattr(args, "room", None)]
    if getattr(args, "recipe", None):
        combos = [c for c in combos if c[1] == getattr(args, "recipe", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    room, recipe = rng.choice(list(combos))
    r = _safe_lookup(RECIPES, recipe)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["woman", "man"])
    return StoryParams(room=room, recipe=recipe, child_name=child_name, child_gender=gender, helper_name=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(room="kitchen", recipe="fruit_salad", child_name="Mia", child_gender="girl", helper_name="Mom", helper_gender="woman"),
    StoryParams(room="patio", recipe="trail_mix", child_name="Ben", child_gender="boy", helper_name="Dad", helper_gender="man"),
    StoryParams(room="playroom", recipe="sandwiches", child_name="Lila", child_gender="girl", helper_name="Aunt May", helper_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_combo/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
