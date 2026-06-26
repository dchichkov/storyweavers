#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/doom_enclave_nag_rhyme_cautionary_happy_ending.py
====================================================================================================================================

A standalone *story world* sketch for a cautionary folk tale with rhyme,
featuring doom, enclave, nag, and a happy ending.

Initial story (used to build a world model):
---
In a cozy woodland enclave, young Pip loved to nag for treats and sweets.
"More honey! More nuts!" he'd whine each day. His mother warned, "Too many
sweets will bring doom to your teeth!" But Pip just nagged louder.

One morning, Pip's teeth began to ache. A deep, terrible doom-pain filled
his mouth. He cried and cried. His mother took him to the wise old hedgehog,
who gave him bitter medicine. "Sweets rot what you love most," said the
hedgehog.

Pip learned his lesson. From that day, he asked politely for crunchy apples
and shared them with his friends. The enclave rejoiced at Pip's happy change,
and his teeth grew strong and white again.
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

# ---------------------------------------------------------------------------
# Rhyme helpers
# ---------------------------------------------------------------------------
def rhyme_line(hero: str, verb: str, object_: str) -> str:
    """Produce a simple rhyming line for the folk-tale style."""
    endings = {
        "nag": ("bag", "zag", "wag"),
        "sweet": ("feet", "treat", "neat"),
        "ache": ("shake", "quake", "break"),
        "doom": ("room", "boom", "gloom"),
        "change": ("range", "strange", "arrange"),
    }
    key = verb if verb in endings else object_.lower().rstrip("s")
    if key in endings:
        return f"{hero} did {verb} for {object_}, what a {random.choice(endings[key])}!"
    return f"{hero} did {verb} for {object_}, oh my!"

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

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
    type: str = "creature"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    rhyme_key: str = ""

    helper_ent: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "girl", "hen"}
        male = {"boy", "father", "hedgehog"}
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
    place: str = "the woodland enclave"
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
    verb: str            # "nag for treats"
    gerund: str          # "nagging for sweets"
    mess: str            # "toothache"
    consequence: str     # "doom-pain in the mouth"
    cure: str            # "bitter medicine"
    keyword: str = "nag"
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
class Helper:
    id: str
    label: str
    cure: str
    wisdom: str

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
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
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


def _r_nag_pain(world: World) -> list[str]:
    out: list[str] = []
    for hero in [e for e in world.entities.values() if e.kind == "character" and "hero" in e.traits]:
        if hero.memes["nag"] < THRESHOLD:
            continue
        sig = ("pain", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["toothache"] += 1
        hero.memes["doom"] += 1
        out.append(f"Then came the doom-pain, a terrible ache!")
    return out

def _r_doom_fear(world: World) -> list[str]:
    out: list[str] = []
    for hero in [e for e in world.entities.values() if "hero" in e.traits]:
        if hero.memes["doom"] < THRESHOLD:
            continue
        sig = ("fear", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["fear"] += 1
        out.append(f"{hero.id} cried out, 'Oh, what a fright! The doom has come in the dark of night!'")
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="nag_pain", apply=_r_nag_pain),
    Rule(name="doom_fear", apply=_r_doom_fear),
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

# ---------------------------------------------------------------------------
# Folk tale verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(f"In a cozy woodland enclave, young {hero.id} lived each day,")
    world.say(f"With a hunger for sweets that would not go away.")

def nag_for_sweets(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["nag"] += 1
    hero.memes["desire"] += 1
    world.say(rhyme_line(hero.id, activity.verb, "sweets and treats"))
    propagate(world)

def warn_about_doom(world: World, parent: Entity, hero: Entity) -> None:
    world.say(f'"{hero.id}, my dear, too many sweets,')
    world.say(f'Will bring doom to your teeth, a bitter defeat!"')
    world.say(f"So said {parent.label} with a worried sigh,")
    world.say(f"But {hero.id} just nagged, letting out a cry.")

def doom_arrives(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["toothache"] += 1
    hero.memes["doom"] += 1
    world.say(f"One morn, a sharp pain, a terrible ache!")
    world.say(f"The doom had arrived, for goodness' sake!")
    propagate(world)

def seek_help(world: World, parent: Entity, hero: Entity, helper: Helper) -> None:
    world.say(f"{hero.id} cried and cried, what could they do?")
    world.say(f"{parent.label} took {hero.pronoun('object')} to the wise one, true.")
    world.say(f"The {helper.label} spoke: '{helper.wisdom}'")
    world.say(f"And gave {hero.pronoun('object')} {helper.cure} to make things good.")

def learn_lesson(world: World, hero: Entity, helper: Helper) -> None:
    hero.memes["nag"] = 0
    hero.memes["doom"] = 0
    hero.memes["joy"] += 1
    world.say(f"{hero.id} learned the lesson, clear and bright,")
    world.say(f"No more nagging, day or night!")
    world.say(f"Politely {hero.pronoun()} asked for apples, crunchy and sweet,")
    world.say(f"And shared them with friends, a happy treat.")

def happy_ending(world: World, hero: Entity, enclave: str) -> None:
    world.say(f"The {enclave} rejoiced, the doom was gone,")
    world.say(f"{hero.id}'s teeth grew strong from that happy dawn.")
    world.say(f"A cautionary tale, with a happy end,")
    world.say(f"Where nagging gave way to a wiser friend.")

# ---------------------------------------------------------------------------
# Tell the story
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, helper: Helper,
         hero_name: str = "Pip", parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type="creature",
        traits=["hero", "young", "stubborn"],
        rhyme_key="nag",
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label=parent_type,
        rhyme_key="warn",
    ))
    helper_ent = world.add(Entity(
        id="Helper", kind="character", type=helper.label, label=helper.label,
        rhyme_key="wise",
    ))

    # Act 1: Nagging
    introduce(world, hero)
    nag_for_sweets(world, hero, activity)
    warn_about_doom(world, parent, hero)
    nag_for_sweets(world, hero, activity)

    # Act 2: Doom
    world.para()
    doom_arrives(world, hero, activity)
    seek_help(world, parent, hero, helper_ent)

    # Act 3: Happy ending
    world.para()
    learn_lesson(world, hero, helper_ent)
    happy_ending(world, hero, setting.place)

    world.facts.update(
        hero=hero, parent=parent, helper=helper_ent,
        activity=activity, setting=setting,
        has_doom=hero.memes["doom"] > 0,
        has_lesson=True,
    )
    return world

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "enclave": Setting(place="the woodland enclave", affords={"nag"}),
    "village": Setting(place="the cozy village", affords={"nag"}),
    "glen": Setting(place="the sunny glen", affords={"nag"}),
}

ACTIVITIES = {
    "nag": Activity(
        id="nag",
        verb="nag",
        gerund="nagging for sweets",
        mess="toothache",
        consequence="doom-pain in the mouth",
        cure="bitter medicine",
        keyword="nag",
        tags={"nag", "sweets", "toothache"},
    ),
}

HELPERS = {
    "hedgehog": Helper(
        id="hedgehog",
        label="wise old hedgehog",
        cure="bitter medicine from the root of the sorrow tree",
        wisdom="'Sweets rot what you love most, little one. Choose wisely.'",
    ),
    "owl": Helper(
        id="owl",
        label="wise old owl",
        cure="sour berry juice with a touch of willow bark",
        wisdom="'Too much of a sweet thing brings doom, my child.'",
    ),
    "badger": Helper(
        id="badger",
        label="wise old badger",
        cure="a paste of herb and honey (just a little!)",
        wisdom="'The nagging heart gets a bitter reward. Be kind.'",
    ),
}

PRIZES = {
    "teeth": Prize(label="teeth", phrase="strong white teeth", type="teeth"),
    "smile": Prize(label="smile", phrase="a bright happy smile", type="smile"),
}

HERO_NAMES = ["Pip", "Toby", "Molly", "Finn", "Bella", "Jasper", "Ruby", "Theo"]
TRAITS = ["young", "curious", "stubborn", "playful", "silly"]

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for act_id in ["nag"]:
            for helper_id in HELPERS:
                combos.append((place, act_id, helper_id))
    return combos

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    helper: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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
    "nag": [("What does it mean to nag?",
             "Nagging means asking for something over and over, even after someone says no.")],
    "doom": [("What is doom in this story?",
              "Doom means a bad thing that happens because of a wrong choice, like a terrible toothache.")],
    "enclave": [("What is an enclave?",
                 "An enclave is a small, safe place where creatures live together, like a cozy woodland home.")],
    "sweets": [("Why can too many sweets be bad?",
                "Too many sweets can hurt your teeth and give you a painful ache. That is the doom of too much sugar.")],
    "lesson": [("Why is it good to learn a lesson?",
                "Learning a lesson helps you make better choices so you can be happy and healthy.")],
}

KNOWLEDGE_ORDER = ["nag", "doom", "enclave", "sweets", "lesson"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity = f["hero"], f["activity"]
    return [
        f'Write a cautionary folk tale in rhyme about a {hero.type} who learns not to {activity.verb} for sweets.',
        f'Tell a rhyming story about doom and a happy ending in a woodland enclave.',
        f'Create a folk tale where a young creature nags too much and faces the consequences.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, helper, activity = f["hero"], f["parent"], f["helper"], f["activity"]
    where = world.setting.place
    qa = [
        QAItem(
            question=f"What did {hero.id} do every day in {where}?",
            answer=f"{hero.id} nagged for sweets and treats every day in {where}, wanting more honey and nuts.",
        ),
        QAItem(
            question=f"What did {parent.label} warn {hero.pronoun('object')} about?",
            answer=f"{parent.label.capitalize()} warned that too many sweets would bring doom to {hero.pronoun('possessive')} teeth.",
        ),
        QAItem(
            question=f"What happened when the doom arrived for {hero.id}?",
            answer=f"When the doom arrived, {hero.pronoun('possessive')} teeth ached terribly and {hero.pronoun()} cried in pain.",
        ),
        QAItem(
            question=f"Who helped {hero.id} and what was the cure?",
            answer=f"The {helper.label} helped {hero.pronoun('object')} and gave {hero.pronoun('object')} {helper.cure}.",
        ),
        QAItem(
            question=f"How did {hero.id} change at the end of the story?",
            answer=f"{hero.id} stopped nagging and politely asked for crunchy apples, sharing them with friends. The enclave rejoiced with a happy ending.",
        ),
    ]
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags or tag == "lesson":
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(Place, Act, Helper) :- setting(Place), activity(Act), helper(Helper).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary folk tale about doom, enclave, and nagging.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
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

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    place, activity, helper_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        helper=helper_id,
        name=name,
        parent=parent,
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity),
                 _safe_lookup(HELPERS, params.helper), params.name, params.parent)
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

CURATED = [
    StoryParams(place="enclave", activity="nag", helper="hedgehog", name="Pip", parent="mother", trait="young"),
    StoryParams(place="village", activity="nag", helper="owl", name="Molly", parent="father", trait="curious"),
    StoryParams(place="glen", activity="nag", helper="badger", name="Toby", parent="mother", trait="stubborn"),
]

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, activity, helper) combos:\n")
        for place, act, helper in stories:
            print(f"  {place:9} {act:8} {helper:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (helper: {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
