#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/catastrophe_dig_gyp_misunderstanding_sound_effects_adventure.py
=============================================================================================================================================================

A standalone story world sketch for an adventure tale where a child mishears a 
grown-up's instruction (Misunderstanding) and goes digging for treasure, setting 
off a silly chain of sound-effects (Sound Effects) that could become a 
catastrophe (Catastrophe). The core premise is a gyp (trick or deception) 
that turns into a playful discovery.

Initial story (used to build a world model):
---
Once upon a time, there was a little brave boy named Max. He loved exploring 
and digging in the garden. One afternoon, Max's grandmother told him: 
"Max, please dig up the old gourd patch so I can plant new seeds."

But Max misheard her! He thought she said: "Dig up the old gyp patch!" 
A gyp was a trick or a hidden treasure in Max's imagination. He grabbed 
his little shovel and ran to the far corner of the yard where he imagined 
the treasure was buried.

As Max dug, he made funny sound effects: "Whish! Thump! Clink!" 
He dug deeper and deeper. Soon he hit something hard -- it made a 
"BOING!" noise. Oh no! He had dug right into the sprinkler pipe. 
Water shot up like a fountain! "Catastrophe!" cried Grandmother.

But Max quickly plugged the pipe with his toy boat, and the water 
stopped. Grandmother laughed and said, "Well, you did dig up a trick 
-- you found the pipe!" They fixed it together and planted new 
gourd seeds in a different spot.

Causal state updates:
---
    do digging                          -> hero.meters["dirt"] += 1
                                          hero.memes["excitement"] += 1
    hero using gear (shovel)            -> gear.meters["wear"] += 1
    dig in wrong location               -> hero.metes["misunderstanding"] += 1
    hit pipe                            -> pipe.meters["damage"] += 1
                                          hero.memes["surprise"] += 1
                                          hero.memes["confusion"] += 1
    water spray active                  -> hero.meters["wet"] += 1
                                          garden.meters["flooded"] += 1
    plug pipe with toy                  -> toy.meters["used"] += 1
                                          hero.memes["cleverness"] += 1
    fix together                        -> hero.memes["joy"] += 1
                                          parent.memes["pride"] += 1

Scripted social/emotional beats:
---
    mishearing                         -> hero.memes["confusion"] += 1
    discovery of pipe                  -> hero.memes["surprise"] += 1
    catastrophe declared               -> hero.memes["fear"] += 1
    clever fix                         -> hero.memes["cleverness"] += 1
    laughter and resolution            -> hero.memes["joy"] += 1
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

MESS_KINDS = {"wet", "muddy", "dirty", "flooded"}
REGIONS = {"garden", "yard", "patch"}



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
    location: str = ""
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    gourd_patch: object | None = None
    hero: object | None = None
    parent: object | None = None
    pipe: object | None = None
    shovel: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandmother", "aunt", "woman"}
        male = {"boy", "grandfather", "uncle", "man"}
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
    place: str = "the backyard"
    indoor: bool = False
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
    zone: set[str]
    weather: str = ""
    keyword: str = ""
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
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}
        self.sound_effects: list[str] = []
        self.misunderstanding_triggered: bool = False
        self.catastrophe_declared: bool = False

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

    def copy(self) -> World:
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.sound_effects = list(self.sound_effects)
        clone.misunderstanding_triggered = self.misunderstanding_triggered
        clone.catastrophe_declared = self.catastrophe_declared
        clone.paragraphs = [[]]
        return clone


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


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for entity in list(world.entities.values()):
        if entity.meters["wet"] >= THRESHOLD and world.facts.get("pipe_broken"):
            sig = ("soak", entity.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if entity.kind == "character":
                out.append(
                    f"{entity.pronoun('possessive').capitalize()} clothes got wet."
                )
            else:
                out.append(f"The {entity.label} got soaked.")
    return out


def _r_catastrophe(world: World) -> list[str]:
    if not world.catastrophe_declared and world.facts.get("pipe_broken"):
        for entity in world.characters():
            if entity.memes["surprise"] >= THRESHOLD:
                sig = ("catastrophe", entity.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                world.catastrophe_declared = True
                return ["__catastrophe__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="catastrophe", tag="social", apply=_r_catastrophe),
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
                produced.extend(s for s in sents if s != "__catastrophe__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["excitement"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved exploring and digging in the garden.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}; "
        f"the soft earth and the promise of discovery made every day an adventure."
    )


def hear_instruction(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    world.say(
        f"One afternoon, {hero.id}'s {parent.label_word} said: "
        f"\"{hero.id}, please dig up the old gourd patch so I can plant new seeds.\""
    )


def misunderstand(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["confusion"] += 1
    hero.memes["desire"] += 1
    hero.meters["misunderstanding"] += 1
    world.misunderstanding_triggered = True
    world.say(
        f"But {hero.id} misheard! {hero.pronoun().capitalize()} thought "
        f"{hero.pronoun('possessive')} {parent.label_word} said: "
        f"\"Dig up the old gyp patch!\" A gyp was a trick, a hidden treasure "
        f"in {hero.id}'s imagination. {hero.pronoun().capitalize()} grabbed "
        f"the little shovel and ran to the far corner of the yard!"
    )
    world.facts["misunderstood_target"] = "the old gyp patch"


def sound_effect(world: World, effect: str) -> None:
    world.sound_effects.append(effect)
    world.say(f"\"{effect}!\"")


def dig_wrong_spot(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["dirt"] += 2
    hero.memes["excitement"] += 2
    world.say(
        f"As {hero.id} dug deeper and deeper, "
        f"{hero.pronoun()} made funny sound effects:"
    )
    sound_effect(world, "Whish! Thump! Clink!")
    world.say(
        f"The earth flew, and {hero.pronoun('possessive')} heart beat faster."
    )
    propagate(world)


def hit_pipe(world: World, hero: Entity) -> None:
    hero.memes["surprise"] += 1
    hero.meters["dirt"] += 1
    world.say(
        f"Suddenly, {hero.pronoun('possessive')} shovel hit something hard. "
        f"It went \"BOING!\" -- a loud, funny sound! "
        f"{hero.pronoun().capitalize()} had dug right into the sprinkler pipe!"
    )
    world.facts["pipe_broken"] = True
    world.say(
        f"Water shot up like a fountain! Splash! Splash! "
        f"{hero.id} was soaking wet."
    )
    hero.meters["wet"] += 3
    propagate(world)


def declare_catastrophe(world: World, parent: Entity, hero: Entity) -> None:
    world.catastrophe_declared = True
    hero.memes["fear"] += 1
    world.say(
        f"\"Catastrophe!\" cried {parent.label_word}. "
        f"\"The whole yard will be flooded!\""
    )


def clever_fix(world: World, hero: Entity, toy: Entity) -> None:
    hero.memes["cleverness"] += 1
    toy.meters["used"] += 1
    world.say(
        f"But {hero.id} was quick! {hero.pronoun().capitalize()} grabbed "
        f"{hero.pronoun('possessive')} toy boat and shoved it into the hole. "
        f"The water stopped. \"Phew!\" {hero.pronoun()} said."
    )


def resolution(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["joy"] += 1
    parent.memes["pride"] += 1
    hero.memes["fear"] = 0
    world.say(
        f"{parent.label_word.capitalize()} laughed and said, "
        f"\"Well, you did dig up a trick -- you found the pipe!\" "
        f"They fixed it together and planted new gourd seeds in a different spot. "
        f"{hero.id} learned that sometimes the best treasure is a good laugh."
    )


def tell(setting: Setting, activity: Activity, hero_name: str = "Max",
         hero_type: str = "boy", hero_traits: Optional[list[str]] = None,
         parent_type: str = "grandmother", toy_phrase: str = "his toy boat") -> World:
    world = World(setting)
    world.weather = "sunny"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "curious"]),
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the grandparent"
    ))
    shovel = world.add(Entity(
        id="shovel", kind="thing", type="shovel", label="shovel",
        phrase="a little red shovel", owner=hero.id,
    ))
    pipe = world.add(Entity(
        id="pipe", kind="thing", type="pipe", label="sprinkler pipe",
        phrase="an old sprinkler pipe", location="garden",
    ))
    toy = world.add(Entity(
        id="toy", kind="thing", type="toy", label="toy boat",
        phrase=toy_phrase, owner=hero.id,
    ))
    gourd_patch = world.add(Entity(
        id="gourd", kind="thing", type="gourd_patch", label="gourd patch",
        phrase="the old gourd patch", location="garden",
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)

    world.para()
    hear_instruction(world, parent, hero, activity)
    misunderstand(world, hero, parent)

    world.para()
    dig_wrong_spot(world, hero, activity)
    hit_pipe(world, hero)

    world.para()
    declare_catastrophe(world, parent, hero)
    clever_fix(world, hero, toy)

    world.para()
    resolution(world, parent, hero)

    world.facts.update(
        hero=hero, parent=parent, activity=activity, setting=setting,
        shovel=shovel, pipe=pipe, toy=toy, gourd_patch=gourd_patch,
        misunderstanding=True, catastrophe=True,
    )
    return world


SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False, affords={"digging"}),
    "garden": Setting(place="the garden", indoor=False, affords={"digging"}),
    "farm": Setting(place="the farm", indoor=False, affords={"digging"}),
}

ACTIVITIES = {
    "digging": Activity(
        id="digging",
        verb="dig for treasure",
        gerund="digging in the dirt",
        rush="start digging right away",
        mess="dirt",
        soil="covered in dirt",
        zone={"garden"},
        weather="sunny",
        keyword="dig",
        tags={"dig", "dirt"},
    ),
}

GEAR = []

PRIZES = {}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["brave", "curious", "playful", "spirited", "cheerful", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            combos.append((place, act_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
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


KNOWLEDGE = {
    "dig": [("Why do people dig in the garden?",
             "People dig in the garden to plant seeds, find things, or just "
             "to play in the soft dirt.")],
    "dirt": [("What is dirt made of?",
              "Dirt is made of tiny pieces of rock, dead leaves, and other "
              "natural things that mix together.")],
    "pipe": [("What is a sprinkler pipe?",
              "A sprinkler pipe carries water underground to help water "
              "the plants in the garden.")],
    "sound": [("Why do sound effects make stories fun?",
               "Sound effects like 'BOING!' or 'SPLASH!' make the story feel "
               "more real and exciting, as if you are right there.")],
    "catastrophe": [("What does 'catastrophe' mean?",
                     "A catastrophe is a big, messy problem that surprises "
                     "everyone, but can often be fixed with a clever idea.")],
    "misunderstanding": [("What is a misunderstanding?",
                          "A misunderstanding happens when you hear something "
                          "differently than it was meant, which can lead to "
                          "funny surprises.")],
    "gyp": [("What is a gyp?",
             "A gyp is a playful trick or deception; in this story, the child "
             "imagines it as a hidden treasure.")],
}
KNOWLEDGE_ORDER = ["dig", "dirt", "pipe", "sound", "catastrophe", "misunderstanding", "gyp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a silly '
        f'misunderstanding that becomes a fun adventure" that includes the '
        f'word "catastrophe".',
        f"Tell a gentle story where a {hero.type} named {hero.id} mishears "
        f"{hero.pronoun('possessive')} {parent.label_word} and goes digging "
        f"for a gyp, using funny sound effects along the way.",
        f'Write a simple story that uses the noun "gyp" and ends with a '
        f"laugh and a clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about and what did {hero.pronoun()} want to do?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id}. "
                f"{pos.capitalize()} {pw} asked {obj} to dig up the old gourd "
                f"patch, but {sub} thought {sub} heard 'gyp patch' and wanted "
                f"to dig for treasure."
            ),
        ),
        QAItem(
            question=(
                f"What funny sound effects did {hero.id} make while digging?"
            ),
            answer=(
                f"{pos.capitalize()} {hero.type} made 'Whish! Thump! Clink!' "
                f"sounds as {sub} dug, and then a loud 'BOING!' when "
                f"{sub} hit the sprinkler pipe."
            ),
        ),
        QAItem(
            question=(
                f"What happened when {hero.id} hit the pipe?"
            ),
            answer=(
                f"Water shot up like a fountain! {pos.capitalize()} {pw} "
                f"cried 'Catastrophe!' because the yard was getting flooded. "
                f"But {hero.id} quickly plugged the hole with "
                f"{pos} toy boat, stopping the water."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add("catastrophe")
    tags.add("misunderstanding")
    tags.add("gyp")
    tags.add("sound")
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  sound effects: {world.sound_effects}")
    lines.append(f"  misunderstanding: {world.misunderstanding_triggered}")
    lines.append(f"  catastrophe: {world.catastrophe_declared}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="backyard",
        activity="digging",
        name="Max",
        gender="boy",
        parent="grandmother",
        trait="brave",
    ),
    StoryParams(
        place="garden",
        activity="digging",
        name="Lily",
        gender="girl",
        parent="grandfather",
        trait="curious",
    ),
]

ASP_RULES = r"""
% Nothing to validate with ASP for this simple domain; all combos are valid.
valid(Place, A) :- affords(Place, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child, a misunderstanding, a catastrophe, sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity),
                 params.name, params.gender,
                 [params.trait, "curious"], params.parent)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity) combos:\n")
        for place, act in triples:
            print(f"  {place:9} {act:8}")
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
