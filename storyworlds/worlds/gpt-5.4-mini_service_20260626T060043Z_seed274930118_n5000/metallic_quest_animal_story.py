#!/usr/bin/env python3
"""
storyworlds/worlds/metallic_quest_animal_story.py
=================================================

A small animal quest story world about a shiny metallic prize, a snag, and a
helpful turn that makes the quest feel complete.

Premise:
- A young animal loves a simple quest.
- The quest points toward a metallic object or place.
- A caretaker or friend worries that the quest is too hard or unsafe.

State model:
- Characters and objects carry physical meters and emotional memes.
- The quest can raise excitement, tiredness, or concern.
- A metal object can be found, repaired, polished, or delivered, depending on
  the chosen scene.

The script generates a tiny classical story with a clear setup, a turn, and a
resolution, plus grounded Q&A and a matching ASP gate.
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


# ---------------------------------------------------------------------------
# World model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    indoors: bool = False
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
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: str
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
    id: str
    label: str
    phrase: str
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
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
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
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0
COSTLY = {"heavy", "stuck", "cold", "noisy"}


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"search", "lift"}),
    "cave": Setting(place="the cave", affords={"search", "lift"}),
    "forest": Setting(place="the forest", affords={"search", "lift"}),
    "riverbank": Setting(place="the riverbank", affords={"search", "lift"}),
    "workshop": Setting(place="the little workshop", indoors=True, affords={"repair", "polish"}),
}

QUESTS = {
    "seek_key": Quest(
        id="seek_key",
        verb="find the key",
        gerund="looking for the key",
        rush="dash toward the old roots",
        risk="might get lost in the dark",
        zone="search",
        keyword="key",
        tags={"metallic", "key"},
    ),
    "seek_coin": Quest(
        id="seek_coin",
        verb="find the coin",
        gerund="searching for the coin",
        rush="run toward the shiny stones",
        risk="might slip on the bank",
        zone="search",
        keyword="coin",
        tags={"metallic", "coin"},
    ),
    "seek_shell": Quest(
        id="seek_shell",
        verb="find the shell charm",
        gerund="searching for the shell charm",
        rush="hurry toward the tide line",
        risk="might lose the trail",
        zone="search",
        keyword="shell",
        tags={"metallic", "charm"},
    ),
    "repair_bell": Quest(
        id="repair_bell",
        verb="repair the bell",
        gerund="repairing the bell",
        rush="rush to the workbench",
        risk="might bend the wire",
        zone="repair",
        keyword="bell",
        tags={"metallic", "repair"},
    ),
    "polish_star": Quest(
        id="polish_star",
        verb="polish the star medal",
        gerund="polishing the star medal",
        rush="hurry to the cloth",
        risk="might scratch the shine",
        zone="polish",
        keyword="metallic",
        tags={"metallic", "polish"},
    ),
}

PRIZES = {
    "amulet": Prize(id="amulet", label="amulet", phrase="a tiny silver amulet", region="neck"),
    "badge": Prize(id="badge", label="badge", phrase="a bright metal badge", region="shirt"),
    "ring": Prize(id="ring", label="ring", phrase="a smooth brass ring", region="paw", plural=False),
}

GEAR = [
    Gear(
        id="lantern",
        label="a lantern",
        prep="take a lantern and walk together",
        tail="walked back with the lantern glowing softly",
        covers={"search"},
        guards={"dark"},
    ),
    Gear(
        id="gloves",
        label="soft gloves",
        prep="put on soft gloves first",
        tail="went back for the soft gloves",
        covers={"repair", "polish"},
        guards={"cold", "scrape"},
        plural=True,
    ),
    Gear(
        id="cloth",
        label="a polishing cloth",
        prep="use a polishing cloth first",
        tail="kept the polishing cloth for the last careful rub",
        covers={"polish"},
        guards={"scratch"},
    ),
]

ANIMAL_NAMES = {
    "fox": ["Pip", "Fenn", "Rue", "Milo"],
    "rabbit": ["Tilly", "Nip", "Luna", "Sage"],
    "bear": ["Bram", "Hugo", "Nori", "Patch"],
    "mouse": ["Mimi", "Pico", "Dot", "Nell"],
    "otter": ["Otis", "Mira", "Bix", "Penny"],
}

ANIMAL_TYPES = list(ANIMAL_NAMES.keys())
PARENT_TYPES = ["mother", "father", "aunt", "uncle"]
TRAITS = ["brave", "curious", "gentle", "bouncy", "careful"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    animal: str
    animal_type: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
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


def quest_at_risk(quest: Quest, prize: Prize) -> bool:
    if quest.zone == "search":
        return True
    if quest.zone == "repair":
        return prize.region in {"paw", "shirt"}
    if quest.zone == "polish":
        return prize.label in {"amulet", "badge", "ring"}
    return False


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.zone in gear.covers:
            return gear
        if quest.zone == "polish" and "polish" in gear.covers:
            return gear
        if quest.zone == "repair" and "repair" in gear.covers:
            return gear
        if quest.zone == "search" and "search" in gear.covers:
            return gear
    return None


def predict_outcome(world: World, hero: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    do_quest(sim, sim.get(hero.id), quest, narrate=False)
    prize = sim.get(prize_id)
    return {
        "ruined": bool(prize.memes.get("worry", 0.0) >= THRESHOLD),
        "tired": hero.meters.get("tired", 0.0),
    }


# ---------------------------------------------------------------------------
# Narrative actions
# ---------------------------------------------------------------------------
def do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    hero.meters[quest.zone] = hero.meters.get(quest.zone, 0.0) + 1
    hero.meters["tired"] = hero.meters.get("tired", 0.0) + 1
    if quest.zone == "search":
        hero.memes["excitement"] = hero.memes.get("excitement", 0.0) + 1
    elif quest.zone == "repair":
        hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    elif quest.zone == "polish":
        hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} started to {quest.verb}.")


def setup(world: World, hero: Entity, caretaker: Entity, prize: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved {quest.gerund} at {world.setting.place}."
    )
    world.say(
        f"One day, {caretaker.pronoun('possessive')} {caretaker.type} gave {hero.id} "
        f"{prize.phrase} and said it was very special."
    )
    prize.worn_by = hero.id
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1


def turn(world: World, hero: Entity, caretaker: Entity, prize: Entity, quest: Quest) -> bool:
    pred = predict_outcome(world, hero, quest, prize.id)
    if not quest_at_risk(quest, _safe_lookup(PRIZES, world.facts.get("prize"))):
        return False
    world.facts["predicted_ruin"] = pred["ruined"]
    world.say(
        f"{hero.id} wanted to {quest.verb}, but {caretaker.id} worried because "
        f"{quest.risk}."
    )
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    caretaker.memes["worry"] = caretaker.memes.get("worry", 0.0) + 1
    return True


def conflict(world: World, hero: Entity, caretaker: Entity, quest: Quest) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(
        f"{hero.id} still tried to {quest.rush}, but {caretaker.id} held up a paw and said to wait."
    )


def compromise(world: World, hero: Entity, caretaker: Entity, quest: Quest, prize: Prize) -> Optional[Gear]:
    gear = select_gear(quest, prize)
    if gear is None:
        return None
    world.say(
        f"{caretaker.id} smiled and suggested they {gear.prep} so the quest could stay safe."
    )
    return gear


def resolve(world: World, hero: Entity, caretaker: Entity, prize: Entity, quest: Quest, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0
    hero.meters["tired"] = max(0.0, hero.meters.get("tired", 0.0) - 0.5)
    world.say(
        f"{hero.id} grinned, and together they {gear.tail}. "
        f"Then {hero.id} could {quest.verb} while {prize.label} stayed safe and shiny."
    )


# ---------------------------------------------------------------------------
# World construction
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(setting)
    world.facts["prize"] = params.prize

    hero = world.add(Entity(
        id=params.animal,
        kind="character",
        type=params.animal_type,
        meters={"tired": 0.0},
        memes={"hope": 0.0, "joy": 0.0, "love": 0.0},
    ))
    caretaker = world.add(Entity(
        id=params.caretaker,
        kind="character",
        type=params.caretaker,
        meters={"worry": 0.0},
        memes={"worry": 0.0},
    ))
    prize_ent = world.add(Entity(
        id="prize",
        type=prize.id,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=caretaker.id,
        worn_by=hero.id,
        plural=prize.plural,
        meters={},
        memes={"shine": 1.0},
    ))

    setup(world, hero, caretaker, prize_ent, quest)
    world.say(f"{params.animal.capitalize()} loved the quest because it felt {params.trait} and full of wonder.")
    world.say(f"At {world.setting.place}, the air made everything seem ready for adventure.")

    world.say("")
    turn(world, hero, caretaker, prize_ent, quest)
    conflict(world, hero, caretaker, quest)
    gear = compromise(world, hero, caretaker, quest, prize)
    if gear is not None:
        resolve(world, hero, caretaker, prize_ent, quest, gear)
        world.facts["gear"] = gear.id
        world.facts["resolved"] = True
    else:
        world.say(
            f"They could not find a good way to make the quest safe, so they chose a slower path."
        )
        world.facts["resolved"] = False

    world.facts.update(
        hero=hero,
        caretaker=caretaker,
        quest=quest,
        prize_ent=prize_ent,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story about a {f["hero"].type} who wants to {f["quest"].verb} and finds a metallic treasure.',
        f"Tell a gentle quest story at {f['setting'].place} where {f['hero'].id} must choose a safe way to handle {f['prize_ent'].phrase}.",
        "Write a simple story with an animal hero, a metallic object, a worry, and a kind compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    caretaker = _safe_fact(world, f, "caretaker")
    quest = _safe_fact(world, f, "quest")
    prize = _safe_fact(world, f, "prize_ent")
    place = _safe_fact(world, f, "setting").place
    qa = [
        QAItem(
            question=f"Who is the story about at {place}?",
            answer=f"It is about {hero.id}, a little {hero.type} who loves a quest and carries {prize.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {quest.verb}, which made the day feel exciting.",
        ),
        QAItem(
            question=f"Why did {caretaker.id} worry about the quest?",
            answer=f"{caretaker.id} worried because {quest.risk}, and the special {prize.label} could be put in danger.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="How did they make the quest safe?",
                answer=f"They used {GEAR_BY_ID[f['gear']].label} first, so {hero.id} could keep going without hurting {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is metallic?",
            answer="Metallic means shiny like metal, or made to look like metal.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special goal or journey someone tries to complete.",
        ),
        QAItem(
            question="Why do careful helpers slow down a quest?",
            answer="They slow it down so the hero can stay safe and protect something valuable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_at_risk(Q) :- quest(Q), risk(Q, _).
compatible(Q,G) :- quest(Q), gear(G), zone(Q,Z), covers(G,Z), guards(G,_).
valid_story(P,Q,R) :- place(P), quest(Q), prize(R), affords(P,Z), zone(Q,Z), prize_at_risk(Q,R), compatible(Q,_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("zone", qid, q.zone))
        lines.append(asp.fact("risk", qid, q.risk))
        for t in sorted(q.tags):
            lines.append(asp.fact("tag", qid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    for qid, q in QUESTS.items():
        for pid, p in PRIZES.items():
            if quest_at_risk(q, p):
                lines.append(asp.fact("prize_at_risk", qid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set((p, q, r) for (p, q, r) in asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: ASP matches Python for {len(python_set)} valid stories.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in python:", sorted(python_set - asp_set))
    print("only in asp:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Validation and sampling
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = _safe_lookup(QUESTS, qid)
            for pid, prize in PRIZES.items():
                if quest_at_risk(quest, prize) and select_gear(quest, prize):
                    combos.append((place, qid, pid))
    return sorted(set(combos))


def explain_rejection(quest: Quest, prize: Prize) -> str:
    return (
        f"(No story: {quest.gerund} does not have a safe helpful gear match for {prize.label}. "
        f"Try a different quest/prize pairing.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal quest story world with a metallic prize.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--animal-type", choices=ANIMAL_TYPES)
    ap.add_argument("--animal")
    ap.add_argument("--caretaker", choices=PARENT_TYPES)
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
    if getattr(args, "quest", None) and getattr(args, "prize", None):
        if not quest_at_risk(_safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))) or not select_gear(_safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    animal_type = getattr(args, "animal_type", None) or rng.choice(ANIMAL_TYPES)
    animal = getattr(args, "animal", None) or rng.choice(_safe_lookup(ANIMAL_NAMES, animal_type))
    caretaker = getattr(args, "caretaker", None) or rng.choice(PARENT_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, animal=animal, animal_type=animal_type, caretaker=caretaker, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


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
    StoryParams(place="harbor", quest="seek_key", prize="amulet", animal="Pip", animal_type="fox", caretaker="mother", trait="curious"),
    StoryParams(place="forest", quest="seek_coin", prize="badge", animal="Tilly", animal_type="rabbit", caretaker="aunt", trait="bouncy"),
    StoryParams(place="workshop", quest="polish_star", prize="ring", animal="Bram", animal_type="bear", caretaker="father", trait="careful"),
    StoryParams(place="cave", quest="repair_bell", prize="amulet", animal="Mimi", animal_type="mouse", caretaker="uncle", trait="gentle"),
]

GEAR_BY_ID = {g.id: g for g in GEAR}


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
            header = f"### {p.animal}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
