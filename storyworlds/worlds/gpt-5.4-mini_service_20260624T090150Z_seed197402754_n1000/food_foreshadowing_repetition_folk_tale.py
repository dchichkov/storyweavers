#!/usr/bin/env python3
"""
storyworlds/worlds/food_foreshadowing_repetition_folk_tale.py
=============================================================

A small folk-tale story world about food, a warning sign, repeated tries, and a
kind resolution.

Seed premise:
---
A hungry child or small creature wants a special food. A little foreshadowing
hint suggests the first plan may go wrong. The character tries again, learns a
safer way, and ends with a warm, satisfying meal.

World model:
---
- Characters have emotional memes like hunger, hope, worry, and joy.
- Food items have physical meters like warmth, sweetness, crunch, and fullness.
- Foreshadowing is encoded as a visible clue that predicts a small problem.
- Repetition matters: the hero makes the same kind of attempt twice, and the
  second try changes because of what the first try revealed.
- The ending must prove that something changed in the world: the food is ready,
  shared, or transformed.

This script keeps the prose child-facing, concrete, and lightly folkloric.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    basket: object | None = None
    clue: object | None = None
    feast: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
    indoors: bool = False
    lends: set[str] = field(default_factory=set)
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
class Food:
    id: str
    label: str
    phrase: str
    hot_path: bool = False
    sweet: bool = False
    crunchy: bool = False
    soft: bool = False
    needs_pot: bool = False
    needs_fire: bool = False
    lends: set[str] = field(default_factory=set)
    keyword: str = "food"
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
class Tool:
    id: str
    label: str
    helps: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    food: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
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
    "cottage": Place(id="cottage", label="the little cottage", indoors=True, lends={"stew", "porridge", "bread"}),
    "kitchen": Place(id="kitchen", label="the warm kitchen", indoors=True, lends={"stew", "bread", "pie"}),
    "garden": Place(id="garden", label="the garden gate", indoors=False, lends={"berries", "pies"}),
    "wood": Place(id="wood", label="the edge of the wood", indoors=False, lends={"bread", "berries"}),
}

FOODS = {
    "stew": Food(
        id="stew",
        label="stew",
        phrase="a steaming pot of stew",
        hot_path=True,
        soft=True,
        needs_pot=True,
        needs_fire=True,
        lends={"pot", "spoon", "firewood"},
        keyword="stew",
    ),
    "porridge": Food(
        id="porridge",
        label="porridge",
        phrase="a bowl of porridge with honey",
        sweet=True,
        soft=True,
        needs_pot=True,
        needs_fire=True,
        lends={"pot", "spoon"},
        keyword="food",
    ),
    "bread": Food(
        id="bread",
        label="bread",
        phrase="a round loaf of bread",
        crunchy=True,
        lends={"knife", "basket"},
        keyword="bread",
    ),
    "berries": Food(
        id="berries",
        label="berries",
        phrase="a handful of bright berries",
        sweet=True,
        lends={"basket"},
        keyword="berries",
    ),
    "pie": Food(
        id="pie",
        label="pie",
        phrase="a golden pie with a shining crust",
        hot_path=True,
        crunchy=True,
        needs_fire=True,
        lends={"pan", "oven"},
        keyword="pie",
    ),
}

TOOLS = {
    "basket": Tool(id="basket", label="a woven basket", helps={"berries", "bread"}, prep="put the berries in a basket", tail="carried the basket home"),
    "pot": Tool(id="pot", label="a heavy pot", helps={"stew", "porridge"}, prep="set the pot over the fire", tail="kept the pot steady by the coals"),
    "spoon": Tool(id="spoon", label="a wooden spoon", helps={"stew", "porridge"}, prep="stir the pot with a wooden spoon", tail="stirred until the steam rose"),
    "firewood": Tool(id="firewood", label="dry firewood", helps={"stew", "pie", "porridge"}, prep="feed the fire with dry wood", tail="fed the fire until it glowed"),
    "knife": Tool(id="knife", label="a small knife", helps={"bread"}, prep="slice the loaf with a small knife", tail="cut the loaf into neat pieces"),
    "pan": Tool(id="pan", label="a baking pan", helps={"pie"}, prep="put the pie into a baking pan", tail="slid the pan close to the heat"),
    "oven": Tool(id="oven", label="the oven", helps={"pie"}, prep="bake the pie in the oven", tail="baked until the crust turned golden"),
}

NAMES = ["Mina", "Tomo", "Lea", "Pip", "Nora", "Olin", "Mara", "Jem"]
TYPES = ["girl", "boy", "cat", "rabbit", "fox"]
HELPER_TYPES = ["grandmother", "grandfather", "mother", "father", "old woman", "old man"]


def food_at_risk(food: Food, place: Place) -> bool:
    return food.id in place.lends or bool(food.needs_fire or food.needs_pot)


def select_tool(food: Food) -> Optional[Tool]:
    for tool in TOOLS.values():
        if food.id in tool.helps:
            return tool
    return None


def explain_invalid(food: Food, place: Place) -> str:
    if not food_at_risk(food, place):
        return f"(No story: {food.label} does not have enough trouble here for a folk-tale turn.)"
    if select_tool(food) is None:
        return f"(No story: nothing in the tool basket truly helps with {food.label}.)"
    return "(No story: this combination cannot make a clean foreshadowing-and-repetition tale.)"


ASP_RULES = r"""
food_at_risk(F,P) :- food(F), place(P), needs_fire(F).
food_at_risk(F,P) :- food(F), place(P), needs_pot(F).
food_at_risk(F,P) :- food(F), place(P), lends(P,F).

help(T,F) :- tool(T), food(F), helps(T,F).
valid(P,F) :- food_at_risk(F,P), help(T,F).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for f in sorted(p.lends):
            lines.append(asp.fact("lends", pid, f))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        if f.needs_pot:
            lines.append(asp.fact("needs_pot", fid))
        if f.needs_fire:
            lines.append(asp.fact("needs_fire", fid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for f in sorted(t.helps):
            lines.append(asp.fact("helps", tid, f))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PLACES:
        for f in FOODS:
            place = _safe_lookup(PLACES, p)
            food = _safe_lookup(FOODS, f)
            if food_at_risk(food, place) and select_tool(food) is not None:
                combos.append((p, f))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale about food, foreshadowing, and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "food", None):
        combos = [c for c in combos if c[1] == getattr(args, "food", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, food = rng.choice(list(combos))
    return StoryParams(
        place=place,
        food=food,
        hero=getattr(args, "name", None) or rng.choice(NAMES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(TYPES),
        helper=getattr(args, "helper", None) or rng.choice(NAMES),
        helper_type=getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES),
    )


def _make_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    food = _safe_lookup(FOODS, params.food)
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper))
    feast = world.add(Entity(id="food", type="food", label=food.label, phrase=food.phrase, owner=hero.id))
    clue = world.add(Entity(id="clue", type="thing", label="a cracked spoon", phrase="a cracked spoon on the table"))
    basket = world.add(Entity(id="tool", type="tool", label=select_tool(food).label if select_tool(food) else "a tool"))
    hero.memes.update(hunger=1.0, hope=1.0)
    helper.memes.update(wisdom=1.0)
    world.facts.update(hero=hero, helper=helper, food=feast, food_cfg=food, tool=basket, clue=clue)
    return world


def tell(world: World, params: StoryParams) -> World:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    food: Entity = _safe_fact(world, world.facts, "food")
    food_cfg: Food = _safe_fact(world, world.facts, "food_cfg")
    tool = select_tool(food_cfg)

    world.say(f"Once there was {hero.id}, a little {hero.type} with a hungry belly and a patient heart.")
    world.say(f"{hero.id} longed for {food.label}, for the smell of it was sweet in the air.")
    world.say(f"But on the table there lay {world.facts['clue'].label}, and that was the first sign that the day might not go smoothly.")
    world.para()

    # Foreshadowing + first attempt
    world.say(f"{hero.id} took up the {food.label} plan at {world.place.label}.")
    if food_cfg.needs_fire:
        hero.memes["worry"] += 1.0
        world.say(f"The pot was cold, and the little fire gave only a weak puff of smoke.")
    if food_cfg.needs_pot:
        world.say(f"The pot sat askew, and the spoon tapped it like a tiny warning drum.")
    world.say(f"Still, {hero.id} tried once.")
    hero.meters["attempts"] = hero.meters.get("attempts", 0) + 1
    if food_cfg.needs_fire:
        food.meters["warmth"] = food.meters.get("warmth", 0) + 0.2
        world.say(f"But the {food.label} stayed plain and not ready.")
    if food_cfg.needs_pot:
        food.meters["fullness"] = food.meters.get("fullness", 0) + 0.1
        world.say(f"The first try made almost no supper at all.")

    world.para()

    # Repetition with change
    world.say(f"{hero.id} tried again.")
    world.say(f"This time {helper.label} came with a kinder idea.")
    if tool:
        world.say(f"{helper.label} showed {hero.id} {tool.label}, because the old way had not been enough.")
        world.say(f"Together they {tool.prep}.")
    hero.memes["hope"] += 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1.0
    if food_cfg.needs_fire:
        food.meters["warmth"] = 1.0
    if food_cfg.needs_pot or food_cfg.needs_fire:
        food.meters["ready"] = 1.0
    if food_cfg.sweet:
        food.meters["sweetness"] = 1.0
    if food_cfg.crunchy:
        food.meters["crunch"] = 1.0
    if food_cfg.soft:
        food.meters["softness"] = 1.0

    world.para()
    world.say(f"At last, the food came right.")
    if food_cfg.hot_path:
        world.say(f"The steam curled up like a little white dragon, and {hero.id} knew the meal was safe and warm.")
    else:
        world.say(f"The {food.label} was gathered, set neatly, and ready to share.")
    world.say(f"{hero.id} and {helper.label} ate together, and the old worry went away like mist at sunrise.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child about {f["hero"].id} and {f["food"].label}, using a small clue to foreshadow trouble.',
        f"Tell a gentle story where the same food plan is tried twice, and the second try works better.",
        f'Write a story about food, a warning sign, and a happy ending that feels like an old tale.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    food_cfg: Food = _safe_fact(world, world.facts, "food_cfg")
    place: Place = world.place
    return [
        QAItem(
            question=f"What was {hero.id} hungry for in {place.label}?",
            answer=f"{hero.id} was hungry for {food_cfg.phrase}.",
        ),
        QAItem(
            question=f"What clue hinted that the first try might go wrong?",
            answer=f"The cracked spoon on the table was a small clue that the first try might not work well.",
        ),
        QAItem(
            question=f"Who helped {hero.id} on the second try?",
            answer=f"{helper.label} helped on the second try and showed a better way to make the food.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the {food_cfg.label} was ready, warm or neatly prepared, and {hero.id} could eat with a happy heart.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    food_cfg: Food = _safe_fact(world, world.facts, "food_cfg")
    out = [
        QAItem(
            question="Why do people cook food?",
            answer="People cook food to make it taste better, feel warmer, or become easier and safer to eat.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue that hints something important may happen later.",
        ),
        QAItem(
            question="Why can repeating an attempt help?",
            answer="Trying again can help because the second try can use what was learned from the first one.",
        ),
    ]
    if food_cfg.hot_path:
        out.append(QAItem(
            question="Why does hot food often need careful handling?",
            answer="Hot food needs careful handling because steam and heat can burn hands and mouths.",
        ))
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", food="porridge", hero="Mina", hero_type="girl", helper="Grandmother", helper_type="grandmother"),
    StoryParams(place="kitchen", food="stew", hero="Tomo", hero_type="boy", helper="Father", helper_type="father"),
    StoryParams(place="wood", food="bread", hero="Pip", hero_type="rabbit", helper="Old Man", helper_type="old man"),
]


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    world = tell(world, params)
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, food) combos:\n")
        for p, f in combos:
            print(f"  {p:10} {f}")
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
            header = f"### {p.hero}: {p.food} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
