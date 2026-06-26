#!/usr/bin/env python3
"""
Storyworld: filter_kindness_adventure
====================================

A small Adventure-style story world about a child on a little quest, a filter,
and a kindness choice that changes what happens next.

Premise:
- The hero is on an outdoor adventure with a grown-up guide or a friend.
- They want to keep exploring a place where the water is muddy or dusty.
- The guide worries because the hero's water can get ruined or unusable.
- The hero first rushes ahead, then notices someone else who needs help.
- A filter becomes the gentle, practical compromise: clean the water, share it,
  and keep going.

The world keeps both physical meters and emotional memes:
- meters track things like dirtiness, thirst, filtration, and travel progress.
- memes track feelings like excitement, worry, kindness, and relief.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports shared results eagerly
- imports storyworlds.asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports the standard CLI flags
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
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bottle: object | None = None
    filter_ent: object | None = None
    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    risk: str
    zone: set[str]
    mess: str
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
class FilterGear:
    id: str
    label: str
    phrase: str
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        self.zone: set[str] = set()
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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

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
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "forest": Setting(place="the forest", affords={"stream", "trail"}),
    "canyon": Setting(place="the canyon", affords={"trail", "ridge"}),
    "camp": Setting(place="the campsite", affords={"stream", "trail", "fire"}),
    "harbor": Setting(place="the harbor path", affords={"dock", "trail"}),
}

ACTIVITIES = {
    "stream": Activity(
        id="stream",
        verb="cross the stream",
        gerund="crossing the stream",
        rush="rush into the water",
        risk="the water will turn muddy and unsuited for drinking",
        zone={"hands", "feet"},
        mess="muddy",
        keyword="stream",
        tags={"water", "mud", "filter"},
    ),
    "trail": Activity(
        id="trail",
        verb="follow the trail deeper",
        gerund="following the trail",
        rush="dash ahead on the trail",
        risk="dust and grit will get into the bottle",
        zone={"hands"},
        mess="dusty",
        keyword="trail",
        tags={"path", "kindness"},
    ),
    "ridge": Activity(
        id="ridge",
        verb="climb the ridge",
        gerund="climbing the ridge",
        rush="scramble up the rocks",
        risk="the wind will scatter grit everywhere",
        zone={"hands", "face"},
        mess="dusty",
        keyword="ridge",
        tags={"rocks", "kindness"},
    ),
    "dock": Activity(
        id="dock",
        verb="walk along the dock",
        gerund="walking along the dock",
        rush="run to the edge",
        risk="the bottle can spill in the spray",
        zone={"hands"},
        mess="wet",
        keyword="dock",
        tags={"water", "help"},
    ),
}

FILTERS = {
    "bottle_filter": FilterGear(
        id="bottle_filter",
        label="a bottle filter",
        phrase="a small bottle filter",
        guards={"muddy", "dusty"},
        prep="twist the bottle filter onto the water bottle",
        tail="twisted the bottle filter on and waited for the clean drops",
    ),
    "cloth_filter": FilterGear(
        id="cloth_filter",
        label="a cloth filter",
        phrase="a clean cloth filter",
        guards={"muddy"},
        prep="wrap the cloth filter over the cup",
        tail="wrapped the cloth filter over the cup and poured slowly",
    ),
    "pump_filter": FilterGear(
        id="pump_filter",
        label="a hand pump filter",
        phrase="a little hand pump filter",
        guards={"muddy", "dusty", "wet"},
        prep="set up the hand pump filter by the creek",
        tail="used the hand pump filter until the water looked clear",
        plural=False,
    ),
}

NAMES = ["Mia", "Noah", "Lina", "Ben", "Ava", "Theo", "Zoe", "Eli"]
GUIDES = ["mother", "father", "aunt", "uncle", "big sister", "big brother"]
TRAITS = ["brave", "curious", "quick", "gentle", "spirited"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for gear_id in FILTERS:
                if act.mess in _safe_lookup(FILTERS, gear_id).guards:
                    combos.append((place, act_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    filter: str
    name: str
    guide: str
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


def _predicted_mess(world: World, hero: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    return {
        "mess": sum(e.meters.get(activity.mess, 0) for e in sim.entities.values()),
        "kindness": sum(e.memes.get("kindness", 0) for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0) + 1
    if narrate:
        world.say(f"{actor.id} {activity.gerund}, and the adventure got louder.")


def tell(setting: Setting, activity: Activity, gear: FilterGear, hero_name: str, guide_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Noah", "Ben", "Theo", "Eli"} else "girl"))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_kind, label=f"the {guide_kind}"))
    bottle = world.add(Entity(
        id="bottle",
        type="bottle",
        label="water bottle",
        phrase="a water bottle for the hike",
        owner=hero.id,
        caretaker=guide.id,
        carried_by=hero.id,
    ))
    filter_ent = world.add(Entity(
        id=gear.id,
        type="filter",
        label=gear.label,
        phrase=gear.phrase,
        owner=hero.id,
        carried_by=hero.id,
        protective=True,
    ))

    world.say(f"{hero.id} was a {trait} young adventurer who loved the path into {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} had {bottle.phrase}, and {gear.phrase} waited in the pack for a busy day.")

    world.para()
    world.say(f"One bright day, {hero.id} and {hero.pronoun('possessive')} {guide_kind} went out to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, because {activity.gerund} felt like a real quest.")

    pred = _predicted_mess(world, hero, activity)
    if pred["mess"] >= THRESHOLD:
        world.say(f"But {guide_kind} frowned a little. \"If you {activity.verb}, the water may get too {activity.mess} to use,\" {guide_kind} said.")
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1

    world.say(f"{hero.id} started to {activity.rush}, then stopped when {hero.pronoun('subject')} noticed a small thirsty bird near the path.")
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    guide.memes["hope"] = guide.memes.get("hope", 0) + 1
    world.say(f"{hero.id} wanted to help first, because kindness mattered more than hurrying ahead.")

    world.para()
    if activity.mess in gear.guards:
        world.say(f"{hero.id}'s {guide_kind} smiled and said, \"Let's {gear.prep} and help the bird too.\"")
        filter_ent.carried_by = None
        filter_ent.meters["used"] = filter_ent.meters.get("used", 0) + 1
        world.say(f"They {gear.tail}. Clear water dripped into the bottle, and the bird drank safely from a leaf.")
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        guide.memes["relief"] = guide.memes.get("relief", 0) + 1
        bottle.meters["dirty"] = 0
        bottle.meters["clean"] = 1
    else:
        pass

    world.say(f"Then {hero.id} kept going, a little kinder and a lot smarter, with the bottle ready for the rest of the trail.")

    world.facts.update(
        hero=hero,
        guide=guide,
        bottle=bottle,
        filter=filter_ent,
        setting=setting,
        activity=activity,
        gear=gear,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    activity = _safe_fact(world, f, "activity")
    gear = _safe_fact(world, f, "gear")
    return [
        f'Write a short adventure story for a young child that includes the word "filter" and a kindness choice.',
        f"Tell a gentle adventure where {hero.id} wants to {activity.verb} but {hero.pronoun('possessive')} {guide.type} needs a safe, clean way to keep going.",
        f"Write a small quest story where a {gear.label} helps {hero.id} do the right thing for someone who is thirsty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    activity = _safe_fact(world, f, "activity")
    gear = _safe_fact(world, f, "gear")
    bottle = _safe_fact(world, f, "bottle")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Why did {hero.id} and {hero.pronoun('possessive')} {guide.type} go to {place}?",
            answer=f"They went there for a little adventure, and {hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"What was the problem with the water when {hero.id} wanted to {activity.verb}?",
            answer=f"The water could turn too {activity.mess} to use, so the bottle would not stay ready for drinking.",
        ),
        QAItem(
            question=f"How did the {gear.label} help the story turn out well?",
            answer=f"The {gear.label} helped clean the water, so {hero.id} could keep the bottle safe and help the thirsty bird.",
        ),
        QAItem(
            question=f"What changed in {hero.id}'s feelings after the bird needed help?",
            answer=f"{hero.id} became kinder and more thoughtful, because {hero.pronoun('subject')} chose helping over rushing.",
        ),
        QAItem(
            question=f"What was ready at the end of the adventure?",
            answer=f"{bottle.label.capitalize()} was ready again, and the trail could continue with clean water and a happier heart.",
        ),
    ]


KNOWLEDGE = {
    "filter": [
        QAItem(
            question="What does a filter do?",
            answer="A filter helps trap dirt or bits in water so the water comes out cleaner.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone helps, shares, or cares about another creature's needs.",
        )
    ],
    "water": [
        QAItem(
            question="Why should muddy water be cleaned?",
            answer="Muddy water can carry dirt, so cleaning it makes the water safer and nicer to drink.",
        )
    ],
    "bird": [
        QAItem(
            question="What do birds need on a hot day?",
            answer="Birds need safe water and a calm place to rest.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["filter", "kindness", "water", "bird"]:
        if tag in tags or tag in {"filter", "kindness"}:
            out.extend(KNOWLEDGE[tag])
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
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
activity_happens(A) :- chosen(A).
mess_risk(A) :- activity_happens(A), activity(A).

compatible_filter(F, A) :- filter(F), activity(A), guards(F, M), mess_of(A, M).
valid_story(Place, A, F) :- setting(Place), affords(Place, A), compatible_filter(F, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(s.affords):
            lines.append(asp.fact("affords", sid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
    for fid, gear in FILTERS.items():
        lines.append(asp.fact("filter", fid))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", fid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = {(p, a) for (p, a, f) in asp_valid_stories()}
    if py == cl:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure-style kindness storyworld with a filter and a clean-water choice."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--filter", dest="filter_kind", choices=FILTERS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--guide", choices=GUIDES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity = rng.choice(list(combos))
    gear = getattr(args, "filter_kind", None) or rng.choice(sorted(FILTERS))
    if _safe_lookup(ACTIVITIES, activity).mess not in _safe_lookup(FILTERS, gear).guards:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        activity=activity,
        filter=gear,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        guide=getattr(args, "guide", None) or rng.choice(GUIDES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


CURATED = [
    StoryParams(place="forest", activity="stream", filter="bottle_filter", name="Mia", guide="mother", trait="brave"),
    StoryParams(place="camp", activity="stream", filter="pump_filter", name="Noah", guide="father", trait="curious"),
    StoryParams(place="canyon", activity="ridge", filter="pump_filter", name="Lina", guide="aunt", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(FILTERS, params.filter),
        params.name,
        params.guide,
        params.trait,
    )
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, activity, filter) combos:\n")
        for place, activity, gear in stories:
            print(f"  {place:8} {activity:8} {gear:14}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (filter: {p.filter})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
