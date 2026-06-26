#!/usr/bin/env python3
"""
storyworlds/worlds/canoe_reunion_bravery_bedtime_story.py
==========================================================

A standalone story world sketch about a child who bravely paddles a canoe 
to reunite with a loved one, learning that courage comes from the heart.

Initial story seed:
---
Once upon a time in a little house by the lake, a small child named 
Elara lived with Grandma. Every evening, Grandma told stories about 
faraway shores. One morning, Grandma felt achy and tired and needed 
to rest. "I wish I could bring you a special flower from the island," 
Elara whispered, but the lake was wide and the canoe looked wobbly.

That afternoon, Elara remembered Grandma's stories about brave 
paddlers. Elara put on a life jacket, climbed into the old green canoe, 
and pushed off from the dock. The water splashed and the wind pushed 
back, but Elara kept paddling. When the canoe reached the island, 
Elara picked a golden flower and paddled all the way home.

That evening, Elara gave Grandma the golden flower. Grandma hugged 
Elara tight and said, "You are the bravest paddler I know." Elara 
smiled, feeling warm inside. The flower stayed on the windowsill, 
and every night it glowed in the moonlight.

Causal state updates:
---
    start journey          -> actor.<courage> += 1
    paddle through wave    -> actor.<courage> += 1, canoe.<stability> -= 0.2
    reach shore            -> actor.<joy> += 1, actor.<bravery> += 1
    give gift              -> actor.<love> += 1, recipient.<love> += 1
    rest after journey     -> actor.<tired> += 1

Scripted emotional beats:
---
    worry about loved one  -> actor.<concern> += 1
    remember a story       -> actor.<inspiration> += 1
    brave action           -> actor.<courage> += 1
    successful return      -> actor.<relief> += 1, actor.<pride> += 1
    hug and praise         -> actor.<joy> += 1, actor.<love> += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

LAKE_NAMES = ["Silver Lake", "Moon Lake", "Lily Pond", "Blue Water Lake", "Mirror Lake"]
FLOWERS = ["golden flower", "pink lily", "yellow daisy", "purple starflower", "white moonbell"]
BOAT_NAMES = ["old green canoe", "little blue boat", "white rowboat", "yellow kayak", "red dinghy"]
GIFT_WORDS = {"flower": "the bright petals made the room feel like a garden",
              "shell": "the seashell whispered stories of the deep",
              "stone": "the smooth stone held the warmth of the sun"}
RELATIVES = ["Grandma", "Grandpa", "Papa", "Mama", "Aunt Rosa"]
REST_CONDITIONS = ["felt tired and achy", "had a bad cold", "felt sleepy all day",
                   "had a sore knee", "felt weak and stayed in bed"]



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
    kind: str = "character"
    type: str = "child"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    relative: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "child", "aunt"}
        male = {"boy", "child", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type
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
    place: str = "Silver Lake"
    island: str = "the little island"
    distance: str = "far across the water"
    weather: str = "sunny"
    wind: str = "gentle"
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
class Journey:
    verb: str
    gerund: str
    rush: str
    gift_item: str
    gift_type: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass
class Gear:
    label: str
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False
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


CHILDREN_NAMES = {
    "girl": ["Elara", "Maya", "Luna", "Sophie", "Clara", "Iris", "Hazel", "Violet", "Ruby", "Pearl"],
    "boy": ["Finn", "Oliver", "Leo", "Theo", "Jasper", "Miles", "Oscar", "Arthur", "Henry", "Liam"],
}
TRAITS = ["brave", "gentle", "determined", "curious", "thoughtful", "loving"]


SETTINGS = {
    "lake": Setting(place="Silver Lake", island="the little island", distance="far across the water", weather="sunny", wind="gentle"),
    "moonlake": Setting(place="Moon Lake", island="the rock island", distance="past the reeds and ripples", weather="calm", wind="soft"),
    "lily": Setting(place="Lily Pond", island="the mossy bank", distance="through the lily pads", weather="warm", wind="still"),
    "bluewater": Setting(place="Blue Water Lake", island="the sandy shore", distance="where the water turns blue", weather="clear", wind="breezy"),
    "mirror": Setting(place="Mirror Lake", island="the tiny cove", distance="across the glassy water", weather="bright", wind="quiet"),
}

JOURNEYS = {
    "flower": Journey(
        verb="paddle to the island to pick a flower",
        gerund="paddling across the lake",
        rush="push the canoe into the water",
        gift_item="a golden flower",
        gift_type="flower",
        keyword="flower",
        tags={"flower", "boat", "bravery"},
    ),
    "shell": Journey(
        verb="row to the island to find a shell",
        gerund="rowing across the lake",
        rush="climb into the little boat",
        gift_item="a shiny seashell",
        gift_type="shell",
        keyword="shell",
        tags={"shell", "boat", "bravery"},
    ),
    "stone": Journey(
        verb="sail to the island for a smooth stone",
        gerund="sailing across the water",
        rush="set off in the little white boat",
        gift_item="a smooth white stone",
        gift_type="stone",
        keyword="stone",
        tags={"stone", "boat", "bravery"},
    ),
}

GEAR = [
    Gear(label="a life jacket", covers={"torso"}, prep="put on a life jacket", tail="wore the bright life jacket"),
    Gear(label="a little hat", covers={"head"}, prep="put on a little sun hat", tail="wore the little sun hat"),
    Gear(label="water shoes", covers={"feet"}, prep="put on water shoes", tail="slipped on the water shoes", plural=True),
]

PRIZES = {
    "flower": {"label": "flower", "phrase": "a golden flower", "type": "flower", "region": "hand"},
    "shell": {"label": "shell", "phrase": "a shiny seashell", "type": "shell", "region": "hand"},
    "stone": {"label": "stone", "phrase": "a smooth white stone", "type": "stone", "region": "hand"},
}


@dataclass
class World:
    clone: object | None = None
    world: object | None = None
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_paddle_courage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["paddling"] >= THRESHOLD and actor.memes["courage"] < THRESHOLD:
            sig = ("courage_boost", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["courage"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} heart beat faster, but {actor.pronoun()} kept going.")
    return out


def _r_shore_joy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["reached_shore"] >= THRESHOLD:
            sig = ("shore_joy", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["joy"] += 1
            actor.memes["bravery"] += 1
            out.append(f"Stepping onto the shore filled {actor.id} with a warm braveness.")
    return out


def _r_gift_love(world: World) -> list[str]:
    out: list[str] = []
    for eid, ent in list(world.entities.items()):
        if ent.memes["receives_gift"] >= THRESHOLD:
            sig = ("gift_love", eid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["love"] += 1
            giver = [a for a in world.characters() if a.memes["gave_gift"] >= THRESHOLD]
            if giver:
                giver[0].memes["love"] += 1
                out.append(f"Love filled the room like golden light.")
    return out


def _r_tired_rest(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["journey_complete"] >= THRESHOLD:
            sig = ("tired", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["tired"] += 1
            out.append(f"{actor.id} felt tired but happy, like after a long, good day.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="paddle_courage", tag="emotional", apply=_r_paddle_courage),
    Rule(name="shore_joy", tag="emotional", apply=_r_shore_joy),
    Rule(name="gift_love", tag="emotional", apply=_r_gift_love),
    Rule(name="tired_rest", tag="physical", apply=_r_tired_rest),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _introduce(world: World, child: Entity, relative: Entity, setting: Setting) -> None:
    trait = next((t for t in child.traits if t != "little"), "")
    desc = f"little {trait} {child.type}".strip()
    world.say(f"Once upon a time, in a {desc} named {child.id}, there was a {desc} who lived with {relative.id} by {setting.place}.")
    world.say(f"Every evening, {relative.id} told {child.id} stories about {setting.island} {setting.distance}.")


def _loved_one_rests(world: World, child: Entity, relative: Entity, rest_condition: str) -> None:
    child.memes["concern"] += 1
    world.say(f"One morning, {relative.id} {rest_condition}. \"I wish I could bring you a special gift from {world.setting.island},\" {child.pronoun()} whispered, looking at the water.")


def _remembers_story(world: World, child: Entity, journey: Journey) -> None:
    child.memes["inspiration"] += 1
    world.say(f"Then {child.id} remembered {child.pronoun('possessive')} {world.get('Relative').id}'s story about brave paddlers.")
    world.say(f"\"I can do this,\" {child.pronoun()} said softly, feeling a flicker of bravery.")


def _prepares_gear(world: World, child: Entity, gear: Gear) -> None:
    child.memes["prepared"] += 1
    if gear.plural:
        world.say(f"{child.pronoun().capitalize()} {gear.prep} and climbed into the boat.")
    else:
        world.say(f"{child.pronoun().capitalize()} {gear.prep} and climbed into the boat.")


def _launches_boat(world: World, child: Entity, boat_name: str) -> None:
    child.memes["paddling"] += 1
    world.say(f"The {boat_name} wobbled as {child.id} pushed off from the dock.")
    world.say(f"The water splashed and the {world.setting.wind} wind pushed back, but {child.pronoun()} kept paddling.")


def _wave_encounter(world: World, child: Entity) -> None:
    child.memes["courage"] += 1
    world.facts["had_wave"] = True
    world.say(f"A small wave rocked the canoe, but {child.id} held tight and paddled harder.")
    propagate(world)


def _reaches_island(world: World, child: Entity, journey: Journey) -> None:
    child.memes["reached_shore"] += 1
    propagate(world)
    world.say(f"At last, the canoe reached {world.setting.island}. {child.pronoun().capitalize()} stepped out and found {journey.gift_item} waiting, just like in {world.get('Relative').id}'s stories.")


def _picks_gift(world: World, child: Entity, journey: Journey) -> None:
    child.memes["gave_gift"] += 1
    world.say(f"{child.id} carefully picked {journey.gift_item} and held it close.")


def _returns_home(world: World, child: Entity) -> None:
    child.memes["journey_complete"] += 1
    world.say(f"Then {child.pronoun()} climbed back into the canoe and paddled all the way home, the gift safe in {child.pronoun('possessive')} lap.")
    propagate(world)


def _presents_gift(world: World, child: Entity, relative: Entity, journey: Journey) -> None:
    relative.memes["receives_gift"] += 1
    propagate(world)
    world.say(f"That evening, {child.id} gave {relative.id} {journey.gift_item}. {relative.id} hugged {child.pronoun('object')} tight and said, \"You are the bravest paddler I know.\"")
    world.say(f"{child.id} smiled, feeling warm inside. The {journey.gift_item.split()[-1]} stayed on the windowsill, and every night it glowed in the moonlight.")


def tell(setting: Setting, journey: Journey, gear: Gear,
         child_name: str = "Elara", child_type: str = "girl",
         child_traits: Optional[list[str]] = None,
         relative_type: str = "Grandma",
         boat_name: str = "old green canoe",
         rest_condition: str = "felt tired and achy") -> World:
    world = World(setting)

    relative = world.add(Entity(
        id=relative_type, kind="character", type=relative_type,
        label="the relative",
    ))
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type,
        traits=["little"] + (child_traits or ["brave", "loving"]),
    ))

    _introduce(world, child, relative, setting)
    world.para()
    _loved_one_rests(world, child, relative, rest_condition)
    _remembers_story(world, child, journey)
    world.para()
    _prepares_gear(world, child, gear)
    _launches_boat(world, child, boat_name)
    _wave_encounter(world, child)
    _reaches_island(world, child, journey)
    _picks_gift(world, child, journey)
    _returns_home(world, child)
    world.para()
    _presents_gift(world, child, relative, journey)

    world.facts.update(
        child=child, relative=relative, journey=journey,
        setting=setting, gear=gear, boat_name=boat_name,
        rest_condition=rest_condition,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    journey: str
    gear: str
    name: str
    gender: str
    relative: str
    trait: str
    boat_name: str
    rest_condition: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for jid in JOURNEYS:
            for gid, _ in enumerate(GEAR):
                combos.append((place, jid, f"gear{gid}"))
    return combos


KNOWLEDGE = {
    "bravery": [("What does it mean to be brave?",
                 "Being brave means doing something even when you feel a little scared inside. It is not about not being scared, but about trying anyway.")],
    "boat": [("How does a canoe stay afloat on water?",
              "A canoe floats because it is hollow and made of light materials like wood or plastic. The shape pushes water aside and keeps the boat on top.")],
    "lake": [("What is a lake?",
              "A lake is a large body of still water surrounded by land. It is bigger than a pond and smaller than an ocean.")],
    "flower": [("Why do flowers grow on islands?",
                "Flowers grow on islands because seeds travel by wind, water, or birds. The soil and sunlight help them bloom.")],
    "shell": [("How do shells get to the shore?",
               "Seashells wash up on shores when waves carry them. They are the hard homes of sea creatures like clams and snails.")],
    "stone": [("Why are some stones smooth?",
               "Stones become smooth when water flows over them for a long time. The water rubs off the rough edges.")],
}
KNOWLEDGE_ORDER = ["bravery", "boat", "lake", "flower", "shell", "stone"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, rel, journey = f["child"], f["relative"], f["journey"]
    return [
        f'Write a gentle bedtime story about a {child.type} named {child.id} who shows bravery by taking a canoe across a lake.',
        f"Tell a short story for a young child about reunion and courage, where someone paddles a boat to bring a gift to a loved one.",
        f'Write a story that uses the word "{journey.keyword}" and ends with a warm hug by a windowsill.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, rel, journey = f["child"], f["relative"], f["journey"]
    setting = _safe_fact(world, f, "setting")
    pw = rel.label_word
    sub, obj, pos = child.pronoun("subject"), child.pronoun("object"), child.pronoun("possessive")
    trait = next((t for t in child.traits if t != "little"), child.type)
    rest = _safe_fact(world, f, "rest_condition")
    qa: list[QAItem] = [
        QAItem(
            question=f"Who wanted to bring a gift to {pw} across {setting.place}?",
            answer=f"A brave little {trait} {child.type} named {child.id} wanted to bring a special gift to {pw}."
        ),
        QAItem(
            question=f"Why did {child.id} decide to paddle the canoe to {setting.island}?",
            answer=f"{pw} {rest} and {child.id} wanted to cheer {pw} up with a gift. {sub} remembered {pw}'s stories and felt brave enough to try."
        ),
        QAItem(
            question=f"What did {child.id} bring back from {setting.island}?",
            answer=f"{sub} brought back {journey.gift_item} and gave it to {pw} with a big hug."
        ),
    ]
    if f.get("had_wave"):
        qa.append(QAItem(
            question=f"How did the wave make {child.id} feel during the canoe ride?",
            answer=f"The wave made the canoe wobble and {child.id} felt scared, but {sub} held tight and kept paddling. That was brave."
        ))
    qa.append(QAItem(
        question=f"How did {pw} feel when {child.id} gave {pos} the gift?",
        answer=f"{pw.capitalize()} hugged {child.id} tight and said {sub} was the bravest paddler. They both felt warm and happy inside."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["journey"].tags)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags or tag == "bravery":
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="lake", journey="flower", gear="gear0",
        name="Elara", gender="girl", relative="Grandma",
        trait="brave", boat_name="old green canoe",
        rest_condition="felt tired and achy",
    ),
    StoryParams(
        setting="moonlake", journey="shell", gear="gear1",
        name="Finn", gender="boy", relative="Grandpa",
        trait="determined", boat_name="little blue boat",
        rest_condition="had a bad cold",
    ),
    StoryParams(
        setting="lily", journey="stone", gear="gear2",
        name="Maya", gender="girl", relative="Mama",
        trait="curious", boat_name="white rowboat",
        rest_condition="felt sleepy all day",
    ),
    StoryParams(
        setting="bluewater", journey="flower", gear="gear0",
        name="Oliver", gender="boy", relative="Papa",
        trait="loving", boat_name="yellow kayak",
        rest_condition="had a sore knee",
    ),
    StoryParams(
        setting="mirror", journey="shell", gear="gear1",
        name="Luna", gender="girl", relative="Aunt Rosa",
        trait="thoughtful", boat_name="red dinghy",
        rest_condition="felt weak and stayed in bed",
    ),
]


def explain_rejection(activity: str, prize: str) -> str:
    return "(No story: that combination does not make sense for a bravery bedtime tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bravery-themed bedtime story about a canoe reunion.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--journey", choices=JOURNEYS)
    ap.add_argument("--gear", choices=[f"gear{i}" for i in range(len(GEAR))])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--relative", choices=RELATIVES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "journey", None):
        combos = [c for c in combos if c[1] == getattr(args, "journey", None)]
    if getattr(args, "gear", None):
        combos = [c for c in combos if c[2] == getattr(args, "gear", None)]

    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, journey, gear_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(CHILDREN_NAMES, gender))
    relative = getattr(args, "relative", None) or rng.choice(RELATIVES)
    trait = rng.choice(TRAITS)
    boat_name = rng.choice(BOAT_NAMES)
    rest_condition = rng.choice(REST_CONDITIONS)

    return StoryParams(
        setting=setting,
        journey=journey,
        gear=gear_id,
        name=name,
        gender=gender,
        relative=relative,
        trait=trait,
        boat_name=boat_name,
        rest_condition=rest_condition,
    )


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    journey = _safe_lookup(JOURNEYS, params.journey)
    gear_idx = int(params.gear.replace("gear", ""))
    gear = GEAR[gear_idx]
    world = tell(setting, journey, gear,
                 params.name, params.gender,
                 [params.trait], params.relative,
                 params.boat_name, params.rest_condition)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
% All combinations are valid in this domain
valid_setting(S) :- setting(S).
valid_journey(J) :- journey(J).
valid_gear(G) :- gear(G).
valid_combo(S, J, G) :- valid_setting(S), valid_journey(J), valid_gear(G).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for jid in JOURNEYS:
        lines.append(asp.fact("journey", jid))
    for gid in range(len(GEAR)):
        lines.append(asp.fact("gear", f"gear{gid}"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, journey, gear) combos:\n")
        for s, j, g in combos:
            print(f"  {s:10} {j:8} {g}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.journey} at {p.setting} (relative: {p.relative})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
