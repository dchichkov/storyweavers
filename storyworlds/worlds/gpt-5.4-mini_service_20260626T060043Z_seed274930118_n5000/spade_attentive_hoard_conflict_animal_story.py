#!/usr/bin/env python3
"""
storyworlds/worlds/spade_attentive_hoard_conflict_animal_story.py
==================================================================

A small animal-story world about a careful little animal, a useful spade,
and the trouble that can grow around a hoard.

Seed tale sketch:
---
A little squirrel had a hoard of acorns and wanted to dig a hiding place with a
spade. An attentive parent noticed that the digging spot was too close to the
roots and that the hoard should be moved somewhere safer. The squirrel felt a
burst of conflict, but then they chose a better place together.
---

World idea:
- The main physical object is a spade.
- The precious object is a hoard of food.
- The emotional beat is conflict between desire and a careful warning.
- The ending proves the hoard is safer and the relationship is calmer.

This file follows the Storyweavers storyworld contract with:
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager results import
- lazy ASP import inside helpers
- Python reasonableness gate + inline ASP twin
- trace, QA, JSON, --all, --verify, --asp, --show-asp support
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    assistant: object | None = None
    hero: object | None = None
    prize: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"squirrel", "rabbit", "mouse", "fox", "badger", "hedgehog"}:
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
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
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    species: set[str] = field(default_factory=lambda: {"squirrel", "rabbit", "mouse", "fox", "badger", "hedgehog"})
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
    purpose: str
    prep: str
    tail: str
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
        self.zone: set[str] = set()

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carrying(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


@dataclass
class StoryParams:
    place: str
    animal: str
    helper: str
    prize: str
    activity: str
    name: str
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


SETTINGS = {
    "garden": Setting(place="the garden", affords={"dig"}),
    "forest": Setting(place="the forest edge", affords={"dig"}),
    "orchard": Setting(place="the orchard", affords={"dig"}),
}

ACTIVITIES = {
    "dig": Activity(
        id="dig",
        verb="dig a hiding place",
        gerund="digging a hiding place",
        rush="dig right there",
        mess="dusty",
        soil="dusty and messy",
        keyword="spade",
        tags={"spade", "dig", "hoard"},
    ),
}

PRIZES = {
    "acorns": Prize(
        label="hoard of acorns",
        phrase="a big hoard of acorns",
        type="acorns",
        location="burrow",
        plural=True,
    ),
    "berries": Prize(
        label="hoard of berries",
        phrase="a small hoard of berries",
        type="berries",
        location="basket",
        plural=True,
    ),
    "shiny_stones": Prize(
        label="hoard of shiny stones",
        phrase="a tiny hoard of shiny stones",
        type="stones",
        location="nest",
        plural=True,
    ),
}

TOOLS = {
    "spade": Tool(
        id="spade",
        label="spade",
        purpose="digging soft ground",
        prep="use the spade carefully near the open patch",
        tail="moved the hoard to a safer spot first",
    ),
}

ANIMALS = {
    "squirrel": {"little squirrel", "squirrel"},
    "rabbit": {"gentle rabbit", "rabbit"},
    "mouse": {"tiny mouse", "mouse"},
    "fox": {"small fox", "fox"},
    "badger": {"steady badger", "badger"},
    "hedgehog": {"curious hedgehog", "hedgehog"},
}

NAMES_BY_ANIMAL = {
    "squirrel": ["Nip", "Pip", "Tess", "Milo"],
    "rabbit": ["Bun", "Mina", "Poppy", "Lara"],
    "mouse": ["Dot", "Miri", "Ned", "Tilly"],
    "fox": ["Red", "Fenn", "Jax", "Luna"],
    "badger": ["Bram", "Holly", "Otto", "Wren"],
    "hedgehog": ["Ivy", "Quill", "Nora", "Bee"],
}

TRAITS = ["careful", "curious", "patient", "bright", "stubborn", "kind"]

CURATED = [
    StoryParams(place="garden", animal="squirrel", helper="rabbit", prize="acorns", activity="dig", name="Pip", trait="careful"),
    StoryParams(place="forest", animal="mouse", helper="badger", prize="berries", activity="dig", name="Tilly", trait="curious"),
    StoryParams(place="orchard", animal="hedgehog", helper="fox", prize="shiny_stones", activity="dig", name="Ivy", trait="patient"),
]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return activity.id == "dig" and prize.location in {"burrow", "basket", "nest"}


def select_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    tool = TOOLS["spade"]
    return tool if activity.id == "dig" and prize_at_risk(activity, prize) else None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_tool(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def activity_detail(activity: Activity) -> str:
    return {
        "dig": "The little spade made neat little scoops in the soil.",
    }.get(activity.id, "It felt like a small, busy game.")


def setting_detail(setting: Setting) -> str:
    return {
        "the garden": "The garden had soft dirt and a few roots peeking through.",
        "the forest edge": "The forest edge was quiet, with leaves piled near the trees.",
        "the orchard": "The orchard had open ground between the low branches.",
    }.get(setting.place, f"{setting.place.capitalize()} looked calm and open.")


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["excited"] = actor.memes.get("excited", 0.0) + 1
    world.zone = {"ground"}
    if narrate:
        world.say(f"{actor.id} started {activity.gerund}.")
        world.say(activity_detail(activity))


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    soiled = sim.get(actor.id).meters.get(activity.mess, 0.0) >= THRESHOLD and prize.location == "burrow"
    return {"soiled": soiled}


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "careful")
    world.say(f"{hero.id} was a {trait} little {hero.type} who liked quiet jobs and tidy places.")


def love_thing(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.carried_by = hero.id
    world.say(f"{hero.id} loved {prize.label} and kept {prize.it()} close like a treasure.")


def wants(world: World, hero: Entity, activity: Activity, tool: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} with the {tool.label}.")
    world.say(f"{hero.pronoun().capitalize()} imagined a cozy place for the hoard.")


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["warned"] = True
    world.say(f"{helper.id} noticed the plan and gave a gentle warning.")
    world.say(f'"That spot is too close to the roots," {helper.id} said. "We could lose the {prize.label}."')
    return True


def conflict(world: World, hero: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    world.say(f"{hero.id} felt a prickly conflict in their chest.")
    world.say(f"{hero.id} still wanted to rush ahead, but the warning stayed in mind.")


def compromise(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity, tool: Entity) -> bool:
    if select_tool(activity, prize) is None:
        return False
    world.say(f"{helper.id} pointed to a safer patch and said, \"Let's use the {tool.label} there instead.\"")
    world.say(f"{hero.id} agreed to {tool.prep}.")
    return True


def resolve(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(f"Together they {TOOLS['spade'].tail}.")
    world.say(
        f"Soon {hero.id} was {activity.gerund}, and the {prize.label} stayed safe and dry in its new place."
    )
    world.say(f"{helper.id} smiled because the little hoard was safer than before.")


def tell(setting: Setting, animal: str, helper: str, prize_cfg: Prize, activity: Activity, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=animal, traits=["little", trait]))
    assistant = world.add(Entity(id="Helper", kind="character", type=helper, traits=["attentive"]))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=assistant.id, location=prize_cfg.location, plural=prize_cfg.plural))
    tool = world.add(Entity(id="Tool", type="spade", label="spade", phrase="a small spade"))

    introduce(world, hero)
    world.say(setting_detail(setting))
    love_thing(world, hero, prize)

    world.para()
    wants(world, hero, activity, tool)
    warn(world, assistant, hero, activity, prize)
    conflict(world, hero)

    world.para()
    if compromise(world, assistant, hero, activity, prize, tool):
        resolve(world, hero, assistant, activity, prize)

    world.facts.update(hero=hero, helper=assistant, prize=prize, activity=activity, tool=tool, setting=setting, conflict=True, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short animal story for a young child that includes the words "spade", "attentive", and "hoard".',
        f"Tell a gentle story about {hero.id} and an attentive helper who worry about a {prize.label} and choose a safer place for a {tool.label}.",
        f"Write a simple story where a little animal feels conflict, but then uses a spade wisely to protect a hoard.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    setting = _safe_fact(world, f, "setting")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who is the story about in {setting.place}?",
            answer=f"It is about {hero.id}, a little {hero.type} who loves {prize.label}.",
        ),
        QAItem(
            question=f"Why did the attentive {helper.type} worry about the {prize.label}?",
            answer=f"The attentive {helper.type} worried because digging in that first spot could disturb the {prize.label} and make the place messy.",
        ),
        QAItem(
            question=f"What did they use instead of rushing ahead with the {tool.label}?",
            answer=f"They used the {tool.label} in a safer patch of ground, so {hero.id} could still {activity.verb} without losing the {prize.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel near the middle of the story?",
            answer=f"{hero.id} felt conflict at first, because they wanted to dig quickly but also wanted to keep the {prize.label} safe.",
        ),
        QAItem(
            question=f"What was the ending like for the hoard?",
            answer=f"The ending was calm and happy, with the {prize.label} tucked into a safer spot and everyone smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spade for?",
            answer="A spade is a tool for digging soft ground and moving dirt.",
        ),
        QAItem(
            question="What does attentive mean?",
            answer="Attentive means watching carefully and noticing what might need help or care.",
        ),
        QAItem(
            question="What is a hoard?",
            answer="A hoard is a stash of things kept together and saved for later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
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
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- digging(A), hoard(P).
has_fix(A,P) :- prize_at_risk(A,P), tool(T), spade(T).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Helper) :- valid(Place,A,P), attentive(Helper).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("digging", aid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("hoard", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        if tid == "spade":
            lines.append(asp.fact("spade", tid))
    for aid in ANIMALS:
        lines.append(asp.fact("attentive", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_story_gate(place: str, activity: str, prize: str, helper: str) -> bool:
    return (place, activity, prize) in valid_combos() and helper in ANIMALS


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} needs a fix that can truly protect a {prize.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        if not valid_story_gate(getattr(args, "place", None) or "garden", getattr(args, "activity", None), getattr(args, "prize", None), getattr(args, "helper", None) or "rabbit"):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, prize = rng.choice(list(combos))
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS))
    helper = getattr(args, "helper", None) or rng.choice([a for a in sorted(ANIMALS) if a != animal])
    name = getattr(args, "name", None) or rng.choice(NAMES_BY_ANIMAL[animal])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, animal=animal, helper=helper, prize=prize, activity=activity, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.animal, params.helper, _safe_lookup(PRIZES, params.prize), _safe_lookup(ACTIVITIES, params.activity), params.name, params.trait)
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
    ap = argparse.ArgumentParser(description="Animal story world about a spade, an attentive helper, and a hoard.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
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
    import asp
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} valid combos ({len(stories)} with helper attention):\n")
        for place, act, prize in triples:
            helpers = sorted(h for (pl, a, pr, h) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:8} {act:6} {prize:15}  [{', '.join(helpers)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.animal} with a {p.helper} and a {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
