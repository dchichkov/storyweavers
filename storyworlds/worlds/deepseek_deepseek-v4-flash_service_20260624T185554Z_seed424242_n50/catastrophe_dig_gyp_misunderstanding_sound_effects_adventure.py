#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/catastrophe_dig_gyp_misunderstanding_sound_effects_adventure.py
=========================================================================================================================================

A standalone *story world* sketch for an adventure tale about a misunderstood
map, a digging mishap, and a small catastrophe rescued by sound cues and
friendship.

Seed words: *catastrophe*, *dig*, *gyp*
Features: *Misunderstanding*, *Sound Effects*
Style: *Adventure*

Story premise (used to build the world model):
---
Alex and his friend Gyp found an old map in the attic. The map had an 'X' that
pointed to "the big hill". Alex was sure the map meant the hill behind the barn,
where they had once found a shiny rock. Gyp was not so sure, but Alex was
excited. They grabbed their shovels and set off.

When they reached the big hill, Alex began to dig right away. The earth was
hard, and soon a deep hole appeared. Inside the hole something glinted – was it
treasure? Alex dug faster. Then came a low rumble (RUMBLE!) and the walls of the
hole started to crumble. Rocks tumbled down. "Catastrophe!" shouted Gyp. Alex
looked up – a huge boulder was about to fall. Gyp saw it and yelled "DUCK!",
pulling Alex out of the hole just in time. They hugged and agreed that next time
they would check the map twice before digging.

Causal state updates:
---
    dig action                  -> hero.energy -= 1; hole.depth += 1; hero.hope += 1
    dig in wrong location       -> ground.unstable += 1
    ground.unstable >= 2        -> catastrophe (rocks fall) -> hero.scared += 1; hero.danger += 1
    friend rescues              -> hero.friendship += 1; hero.safe = True

Sound effects introduced as prose tags: "SSHHHRRR", "THUMP", "CRAAAACK", etc.
Misunderstanding: the map's "big hill" was actually the hill in the garden,
not the barn hill.  The hero digs at the wrong hill, leading to the catastrophe.
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
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
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
    kind: str = "character"          # character | thing
    type: str = "thing"             # boy, girl, dog, map, shovel, rock, treasure
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    # Physical meters
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    # Emotional memes
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    friend: object | None = None
    ground: object | None = None
    hero: object | None = None
    map_obj: object | None = None
    shovel: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "dad", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mom", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"dog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
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
class Setting:
    place: str = "the hill"
    wrong_place: str = "the garden hill"
    right_place: str = "the barn hill"
    affords: set[str] = field(default_factory=lambda: {"digging"})
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
    weather: str = "sunny"
    keyword: str = "dig"
    sound_effects: list[str] = field(default_factory=list)
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hole"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})
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
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: callable
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


def _r_catastrophe(world: World) -> list[str]:
    """If ground.unstable >= THRESHOLD and hero is in hole, catastrophe."""
    hero = world.entities.get("Hero")
    if not hero:
        return []
    if hero.meters["in_hole"] < THRESHOLD:
        return []
    if world.entities.get("Ground") and world.entities["Ground"].meters["unstable"] >= THRESHOLD:
        sig = ("catastrophe",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["scared"] += 1
            hero.memes["danger"] += 1
            return ["CRAAACK! RUMBLE! The ground shook!"]
    return []


def _r_rescue(world: World) -> list[str]:
    """Friend pulls hero out after catastrophe."""
    if "catastrophe" in {n for n, *_ in world.fired}:
        friend = world.entities.get("Gyp")
        hero = world.entities.get("Hero")
        if friend and hero and hero.memes["danger"] >= THRESHOLD:
            sig = ("rescue",)
            if sig not in world.fired:
                world.fired.add(sig)
                hero.memes["friendship"] += 1
                hero.meters["in_hole"] = 0.0
                return ["Gyp yelled 'DUCK!' and pulled Alex out just in time."]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("catastrophe", "physical", _r_catastrophe),
    Rule("rescue", "social", _r_rescue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def sound_effect(word: str) -> str:
    sounds = {
        "dig": "SSHHHRRR!",
        "rumble": "RUMBLE!",
        "crash": "CRAAAACK!",
        "thump": "THUMP!",
        "clank": "CLANK!",
        "whoosh": "WHOOOOSH!",
    }
    return sounds.get(word, f"**{word.upper()}**")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Alex", friend_name: str = "Gyp",
         hero_type: str = "boy", friend_type: str = "dog"
         ) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id="Hero", kind="character", type=hero_type,
        label=hero_name, traits=["brave", "curious"],
    ))
    friend = world.add(Entity(
        id="Gyp", kind="character", type=friend_type,
        label=friend_name, traits=["clever", "loyal"],
    ))
    map_obj = world.add(Entity(
        id="Map", kind="thing", type="map", label="the old map",
        phrase="a crinkly old map with a big red X",
    ))
    shovel = world.add(Entity(
        id="Shovel", kind="thing", type="shovel", label="the shovel",
        plural=True,
    ))
    treasure = world.add(Entity(
        id="Treasure", kind="thing", type="treasure", label="the treasure chest",
        phrase="a shiny little chest",
        plural=False,
    ))
    ground = world.add(Entity(
        id="Ground", kind="thing", type="ground", label="the earth",
        meters=defaultdict(float),
    ))

    # Act 1: discovery
    world.say(f"{hero.name} and {friend.name} found {map_obj.phrase} in the attic.")
    world.say(f'"{sound_effect("dig")}" said {hero.name}, pointing at the giant X.')
    world.say(f'"{friend.name} wagged its tail—it loved adventures!')

    # Act 2: misunderstanding
    world.para()
    world.say(f"They grabbed {shovel.label} and went to the big hill.")
    world.say(f"{hero.name} was sure it was the one behind the barn.")
    world.say(f"'{sound_effect('thump')}' — the shovel hit the ground.")
    hero.meters["in_hole"] += 1
    ground.meters["unstable"] += 2  # wrong spot
    propagate(world, narrate=True)

    # Act 3: catastrophe
    world.para()
    world.say(f"{hero.name} kept digging. Suddenly a {sound_effect('rumble')} came from below.")
    world.say(f"{sound_effect('crash')} Rocks tumbled down!")
    world.say(f"'{friend.name} shouted: 'Catastrophe! Duck!'")
    propagate(world, narrate=True)

    # Act 4: rescue + resolution
    world.para()
    world.say(f"{friend.name} pulled {hero.name} out of the hole.")
    world.say(f"They sat on the grass, breathing hard.")
    world.say(f'"{hero.name} said, "Let\'s check the map again."')
    world.say(f"They realized the X had a note: 'big hill' meant the garden hill, not the barn hill.")
    world.say(f"So they walked to the right hill and dug there. {sound_effect('clank')}")
    world.say(f"They found {treasure.phrase}!")
    world.say(f"'{sound_effect('whoosh')}' — they opened the chest and inside were shiny stickers.")
    world.say(f"Congratulations, adventurers!")

    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["map"] = map_obj
    world.facts["treasure"] = treasure
    world.facts["activity"] = activity
    world.facts["setting"] = setting
    world.facts["catastrophe_happened"] = True
    world.facts["sound_effects"] = ["SSHHHRRR", "RUMBLE", "CRAAAACK", "THUMP", "CLANK", "WHOOOOSH"]
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hill": Setting(place="the hill", wrong_place="the barn hill", right_place="the garden hill"),
    "cave": Setting(place="the cave", wrong_place="the dark tunnel", right_place="the crystal cave"),
}

ACTIVITIES = {
    "digging": Activity(
        id="digging",
        verb="dig for treasure",
        gerund="digging in the dirt",
        rush="jump into the hole",
        mess="dusty",
        soil="covered in dust",
        zone={"hole"},
        sound_effects=["SSHHHRRR", "THUMP", "RUMBLE", "CRAAAACK", "CLANK", "WHOOOOSH"],
    ),
}

PRIZES = {
    "treasure": Prize(label="treasure chest", phrase="a shiny little chest", type="treasure"),
    "gem": Prize(label="gem", phrase="a sparkly blue gem", type="gem"),
}

GEARS = []  # no protective gear in this adventure


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy"]
BOY_NAMES = ["Alex", "Ben", "Max", "Sam", "Leo", "Jack"]
FRIEND_NAMES = ["Gyp", "Rex", "Bolt", "Pip", "Tucker"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    return [
        f'Write a short adventure story for young children featuring the words "catastrophe", "dig", and "gypped" (tricked).',
        f"Tell a story where {hero.name} and {friend.name} go on a treasure hunt but a misunderstanding leads to a scary rock slide.",
        f'Use sound effects like "RUMBLE" and "CRAAAACK" to make the story exciting.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    place = _safe_fact(world, f, "setting").place
    qa = [
        QAItem(
            question=f"Where did {hero.name} and {friend.name} find the map?",
            answer=f"They found the map in the attic of their house.",
        ),
        QAItem(
            question=f"What did {hero.name} and {friend.name} use to dig?",
            answer=f"They used shovels to dig the hole.",
        ),
        QAItem(
            question=f"Why did the ground start to crumble and make a loud noise?",
            answer=f"The ground crumbled because {hero.name} dug too fast and hit a weak spot under the wrong hill. That caused a rock slide.",
        ),
        QAItem(
            question=f"Did {friend.name} help {hero.name} when the catastrophe happened?",
            answer=f"Yes, {friend.name} shouted 'Duck!' and pulled {hero.name} out of the hole just in time.",
        ),
        QAItem(
            question=f"What did they do after they were safe?",
            answer=f"They checked the map again and realized the X pointed to the garden hill, not the barn hill. So they went to the right hill and found the treasure.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    sounds = world.facts.get("sound_effects", [])
    qa = [
        QAItem(
            question="What does a rumble sound mean when you are digging?",
            answer="A rumble can mean the ground is loose and might fall. It is a warning sound to stop digging.",
        ),
        QAItem(
            question="What does 'catastrophe' mean?",
            answer="Catastrophe means a big, bad event like a crash or a rock slide. It is a strong word for something that goes very wrong.",
        ),
    ]
    if "CRAAAACK" in sounds:
        qa.append(QAItem(
            question="What might a loud 'CRAAAACK' mean when you are in a hole?",
            answer="It often means rocks or the walls of the hole are breaking apart. You should get out quickly.",
        ))
    return qa


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
        place="hill", activity="digging", prize="treasure",
        hero_name="Alex", hero_type="boy",
        friend_name="Gyp", friend_type="dog",
    ),
    StoryParams(
        place="cave", activity="digging", prize="gem",
        hero_name="Mia", hero_type="girl",
        friend_name="Rex", friend_type="dog",
    ),
]


def explain_rejection(activity, prize):
    return "(No story: all combos are valid in this simple world.)"


# ---------------------------------------------------------------------------
# ASP Twin (inline)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Every valid combo is valid (simple world).
valid(Place, A, P) :- setting(Place), activity(A), prize(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story: catastrophe, dig, gyp.")
    ap.add_argument("--place", choices=list(SETTINGS.keys()))
    ap.add_argument("--activity", choices=list(ACTIVITIES.keys()))
    ap.add_argument("--prize", choices=list(PRIZES.keys()))
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--friend-type", choices=["dog", "cat", "rabbit"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
    filtered = [c for c in combos
                if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
                and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, act, prize_id = rng.choice(filtered)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["boy", "girl"])
    friend_type = getattr(args, "friend_type", None) or rng.choice(["dog", "cat", "rabbit"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(BOY_NAMES if hero_type == "boy" else GIRL_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(
        place=place, activity=act, prize=prize_id,
        hero_name=hero_name, hero_type=hero_type,
        friend_name=friend_name, friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize),
        params.hero_name, params.friend_name,
        params.hero_type, params.friend_type,
    )
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combinations:")
        for p, a, pr in triples:
            print(f"  {p:6} {a:8} {pr:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero_name} & {p.friend_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
