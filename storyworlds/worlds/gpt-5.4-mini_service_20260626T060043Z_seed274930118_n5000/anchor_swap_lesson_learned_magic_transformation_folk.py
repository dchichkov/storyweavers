#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/anchor_swap_lesson_learned_magic_transformation_folk.py
========================================================================================================

A small folk-tale storyworld about an anchor, a swap, and a lesson learned.

Seed tale imagined from the prompt:
---
In a little river village, a child found a magic anchor charm at the bottom of an old chest.
The child wanted to swap a plain thing for a brighter one, but the village elder warned that
magic should not be used for greedy swapping. When the child chose a fair trade and spoke a
kind wish, the anchor charm transformed the old thing into something useful and lovely.
The child learned that magic works best when it is tied to honesty, patience, and a good heart.

World model:
---
- A child, a possible trade partner, a special item, and a magic anchor charm.
- The hero may attempt a swap, but only some swaps are fair and reasonable.
- The magic anchor can transform one item when the story's lesson is learned.
- The ending proves a change in the world: a trade completed, a charm used well,
  and an object transformed into a better form.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    charm: object | None = None
    hero: object | None = None
    item: object | None = None
    parent: object | None = None
    partner: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    value: str
    transformed_into: str
    tags: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    kind: str
    effect: str
    turns: str
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
class Trade:
    id: str
    verb: str
    noun: str
    reason: str
    risk: str
    lesson: str
    keyword: str = "swap"
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.magic_power: float = 0.0
        self.lesson_seen: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.magic_power = self.magic_power
        clone.lesson_seen = self.lesson_seen
        return clone


SETTINGS = {
    "river_village": Setting(place="the river village", affords={"swap", "transform"}),
    "market_square": Setting(place="the market square", affords={"swap"}),
    "oak_grove": Setting(place="the oak grove", affords={"transform"}),
}

TRADE_ACTIONS = {
    "swap": Trade(
        id="swap",
        verb="swap",
        noun="swap",
        reason="they wanted something brighter or finer",
        risk="a greedy trade could leave someone disappointed",
        lesson="a fair trade should make both sides smile",
    ),
    "transform": Trade(
        id="transform",
        verb="transform",
        noun="transformation",
        reason="the charm could change a plain thing into a useful one",
        risk="magic used carelessly could make a mess",
        lesson="magic works best when it helps, not when it boasts",
    ),
}

ITEMS = {
    "wooden_spoon": Item(
        id="wooden_spoon",
        label="wooden spoon",
        phrase="a plain wooden spoon",
        type="spoon",
        value="plain",
        transformed_into="carved spoon",
        tags={"plain", "wood", "kitchen"},
    ),
    "tin_whistle": Item(
        id="tin_whistle",
        label="tin whistle",
        phrase="a tiny tin whistle",
        type="whistle",
        value="bright",
        transformed_into="silver whistle",
        tags={"music", "bright"},
    ),
    "bread_basket": Item(
        id="bread_basket",
        label="bread basket",
        phrase="a woven bread basket",
        type="basket",
        value="useful",
        transformed_into="flower basket",
        tags={"woven", "useful"},
    ),
    "river_stone": Item(
        id="river_stone",
        label="river stone",
        phrase="a smooth gray river stone",
        type="stone",
        value="plain",
        transformed_into="glowing charm",
        tags={"stone", "river", "plain"},
    ),
}

CHARACTER_NAMES = ["Mara", "Tobin", "Elin", "Nessa", "Jory", "Pippa"]
CHARACTER_TYPES = ["girl", "boy"]
ADJECTIVES = ["curious", "gentle", "brave", "patient", "kind", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            for item_id, item in ITEMS.items():
                if action == "swap" and "plain" in item.tags:
                    combos.append((place, action, item_id))
                if action == "transform" and item_id in {"wooden_spoon", "river_stone", "bread_basket"}:
                    combos.append((place, action, item_id))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
    name: str
    gender: str
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


def _do_swap(world: World, hero: Entity, partner: Entity, item: Entity, narrate: bool = True) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    partner.memes["consider"] = partner.memes.get("consider", 0.0) + 1
    item.meters["touched"] = item.meters.get("touched", 0.0) + 1
    world.magic_power += 0.5
    if narrate:
        world.say(f"{hero.id} asked to swap {hero.pronoun('possessive')} {item.label} for something nicer.")


def _do_transform(world: World, hero: Entity, item: Entity, narrate: bool = True) -> None:
    item.meters["changed"] = item.meters.get("changed", 0.0) + 1
    item.meters["bright"] = item.meters.get("bright", 0.0) + 1
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.lesson_seen = True
    if narrate:
        world.say(f"The magic anchor glowed, and {hero.pronoun('possessive')} {item.label} began to transform.")


def predict_outcome(world: World, hero: Entity, item: Entity, action: Trade) -> dict:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    sim_item = sim.get(item.id)
    _do_swap(sim, sim_hero, sim.get("partner"), sim_item, narrate=False)
    if action.id == "transform":
        _do_transform(sim, sim_hero, sim_item, narrate=False)
    return {
        "lesson_seen": sim.lesson_seen,
        "item_changed": bool(sim_item.meters.get("changed", 0) >= THRESHOLD),
        "magic_power": sim.magic_power,
    }


def setup_story(world: World, hero: Entity, parent: Entity, partner: Entity, item: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, {hero.id} was a little {hero.pronoun('possessive')} "
        f"{hero.type} who loved {hero.memes.get('love_word', 'bright tales')}."
    )
    world.say(
        f"{hero.id} kept {hero.pronoun('possessive')} {item.label} close, because it looked plain but felt special."
    )
    world.say(
        f"One day, {hero.pronoun('possessive')} {parent.pronoun('possessive')} elder said that "
        f"magic can be kind when it is guided by a good lesson."
    )


def desire_and_warning(world: World, hero: Entity, parent: Entity, partner: Entity, item: Entity, action: Trade) -> None:
    world.para()
    world.say(
        f"{hero.id} saw {partner.id} and wanted to {action.verb} {hero.pronoun('possessive')} {item.label} at once."
    )
    world.say(
        f"But {parent.id} frowned a little and warned, \"{action.risk.capitalize()}.\""
    )
    world.say(
        f"{hero.id} felt a tug of greed, yet {hero.pronoun('subject')} also remembered to listen."
    )
    hero.memes["greed"] = hero.memes.get("greed", 0.0) + 1
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1


def anchor_turn(world: World, hero: Entity, partner: Entity, item: Entity, action: Trade, charm: Charm) -> None:
    world.para()
    world.say(
        f"Then {hero.id} found {charm.phrase}. It was an anchor charm, heavy enough to settle a wandering wish."
    )
    world.say(
        f"{hero.id} held it tight and made a gentle promise: \"I will not swap in a mean way.\""
    )
    world.magic_power += 1.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["honesty"] = hero.memes.get("honesty", 0.0) + 1
    world.facts["anchored"] = True
    if action.id == "swap":
        world.say(f"The promise steadied the swap, so nobody would be cheated.")
    else:
        world.say(f"The promise steadied the magic, so the change would be useful and kind.")


def resolution(world: World, hero: Entity, partner: Entity, parent: Entity, item: Entity, action: Trade, charm: Charm) -> None:
    world.para()
    if action.id == "swap":
        world.say(
            f"{hero.id} traded fairly with {partner.id}, and both of them smiled at the honest swap."
        )
        item.meters["touched"] = item.meters.get("touched", 0.0) + 1
        item.meters["shared"] = item.meters.get("shared", 0.0) + 1
        world.facts["fair_trade"] = True
    else:
        _do_transform(world, hero, item, narrate=False)
        item.type = item.transformed_into
        item.label = item.transformed_into
        item.phrase = f"a lovely {item.transformed_into}"
        world.say(
            f"The anchor charm shone, and {hero.pronoun('possessive')} {item.label} transformed into "
            f"{item.transformed_into} as if the river itself had blessed it."
        )
        world.say(
            f"{parent.id} nodded and said, \"Now that is a good lesson learned: magic should make life kinder, not greedier.\""
        )
        world.facts["lesson"] = action.lesson
        world.facts["transformed"] = True
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1


def tell(setting: Setting, action: Trade, item_cfg: Item,
         hero_name: str = "Mara", hero_type: str = "girl",
         parent_type: str = "woman") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["little", "kind", "curious"]
    ))
    parent = world.add(Entity(id="elder", kind="character", type=parent_type))
    partner = world.add(Entity(id="partner", kind="character", type="girl" if hero_type == "girl" else "boy"))
    item = world.add(Entity(
        id="item", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id
    ))
    charm = world.add(Entity(id="anchor_charm", type="charm", label="anchor charm", phrase="a tiny anchor charm"))
    hero.memes["love_word"] = "folk songs"

    setup_story(world, hero, parent, partner, item)
    desire_and_warning(world, hero, parent, partner, item, action)
    anchor_turn(world, hero, partner, item, action, Charm("anchor_charm", "anchor charm", "a tiny anchor charm", "anchor", "steady magic", "settle"))
    resolution(world, hero, partner, parent, item, action, Charm("anchor_charm", "anchor charm", "a tiny anchor charm", "anchor", "steady magic", "settle"))

    world.facts.update(
        hero=hero, parent=parent, partner=partner, item=item, action=action, charm=charm
    )
    return world


PLACE_NAMES = ["river_village", "market_square", "oak_grove"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item")
    action = _safe_fact(world, f, "action")
    return [
        f"Write a short folk tale for children about {hero.id}, an anchor charm, and a careful {action.keyword}.",
        f"Tell a magical village story where a child wants to {action.verb} {hero.pronoun('possessive')} {item.label} but learns a kinder lesson.",
        f"Write a simple story that includes an anchor, a swap, and a transformation ending with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    partner = _safe_fact(world, f, "partner")
    item = _safe_fact(world, f, "item")
    action = _safe_fact(world, f, "action")
    qa = [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.type}, and the choice to use magic in a kind way.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with {hero.pronoun('possessive')} {item.label}?",
            answer=f"{hero.id} wanted to {action.verb} {hero.pronoun('possessive')} {item.label}, hoping for something better.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id}?",
            answer=f"{parent.id} warned {hero.id} because {action.risk}.",
        ),
        QAItem(
            question="What helped the child make a better choice?",
            answer="The anchor charm helped settle the wish, so the child could choose honesty and patience instead of greed.",
        ),
    ]
    if world.facts.get("transformed"):
        qa.append(
            QAItem(
                question=f"What happened to the {item.label} at the end?",
                answer=f"It transformed into {item.transformed_into}, and the village could see that the magic had been used well.",
            )
        )
    if world.facts.get("fair_trade"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} and {partner.id} finish the swap?",
                answer=f"They finished with a fair trade, and both of them smiled because nobody was cheated.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "anchor": [
        QAItem(
            question="What does an anchor do?",
            answer="An anchor is a heavy object that helps hold a boat still so it does not drift away.",
        )
    ],
    "swap": [
        QAItem(
            question="What does it mean to swap something?",
            answer="To swap means to trade one thing for another.",
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is when something impossible or special happens in a story, often with a spell or charm.",
        )
    ],
    "transform": [
        QAItem(
            question="What does transform mean?",
            answer="To transform means to change into a different form.",
        )
    ],
    "lesson": [
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful idea a character remembers after something happens.",
        )
    ],
    "folk": [
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story that people tell again and again, often with magic, a lesson, and a brave choice.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"anchor", "swap", "magic", "transform", "lesson", "folk"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
    return out


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  magic_power={world.magic_power}")
    lines.append(f"  lesson_seen={world.lesson_seen}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="river_village", action="swap", item="river_stone", name="Mara", gender="girl", parent="woman", trait="kind"),
    StoryParams(place="oak_grove", action="transform", item="wooden_spoon", name="Tobin", gender="boy", parent="man", trait="curious"),
    StoryParams(place="market_square", action="swap", item="bread_basket", name="Elin", gender="girl", parent="woman", trait="patient"),
]


def explain_rejection(action: Trade, item: Item) -> str:
    return f"(No story: this tale needs a reasonable {action.keyword} and a suitable item, but {item.label} does not fit.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "action", None) and getattr(args, "item", None):
        action = _safe_lookup(TRADE_ACTIONS, getattr(args, "action", None))
        item = _safe_lookup(ITEMS, getattr(args, "item", None))
        if (getattr(args, "action", None), getattr(args, "item", None)) not in [(a, i) for _, a, i in valid_combos()]:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(CHARACTER_TYPES)
    name = getattr(args, "name", None) or rng.choice(CHARACTER_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["woman", "man"])
    trait = getattr(args, "trait", None) or rng.choice(ADJECTIVES)
    return StoryParams(place=place, action=action, item=item, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TRADE_ACTIONS, params.action), _safe_lookup(ITEMS, params.item), params.name, params.gender, params.parent)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, action in TRADE_ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("lesson", aid, action.lesson))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for t in sorted(item.tags):
            lines.append(asp.fact("tag", iid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,I) :- affords(P,A), item(I), A = swap, tag(I, plain).
valid(P,A,I) :- affords(P,A), item(I), A = transform, tag(I, plain).
valid(P,A,I) :- affords(P,A), item(I), A = transform, tag(I, wood).
"""


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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale world about an anchor, a swap, magic, transformation, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=TRADE_ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=CHARACTER_TYPES)
    ap.add_argument("--parent", choices=["woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=ADJECTIVES)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
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
            header = f"### {p.name}: {p.action} at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
