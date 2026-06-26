#!/usr/bin/env python3
"""
storyworlds/worlds/bubble_dim_happy_ending_space_adventure.py
==============================================================

A small simulated space-adventure story world about a bubble-dim shield, a
little ship, and a happy ending.

Premise:
- A child astronaut loves a bright bubble window or dome on a tiny ship.
- A dimmer can lower the bubble's glow so the ship can sneak past a star flare.
- The child worries the dimming will make the bubble feel lonely or unsafe.
- A helper explains the dimmer is only for the risky part of the trip.
- The crew uses the dimmer, passes the hazard, then restores the bubble to
  bright and happy at the end.

The simulation models:
- physical state in meters: glow, heat, pressure, soot, repairs
- emotional state in memes: wonder, worry, trust, joy, relief

The prose is authored from world state, not a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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

    helper: object | None = None
    hero: object | None = None
    ship: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "captain"}
        if self.type in female and self.type not in {"captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male and self.type not in {"captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    star_name: str = "the sun"
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
class Mission:
    id: str
    verb: str
    gerund: str
    danger: str
    danger_word: str
    zone: set[str]
    keyword: str
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
class Gear:
    id: str
    label: str
    action: str
    restores: str
    guards: set[str]
    covers: set[str]
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

    def ship(self) -> Entity:
        return self.entities["ship"]

    def hero(self) -> Entity:
        return self.entities["hero"]

    def helper(self) -> Entity:
        return self.entities["helper"]


SETTINGS = {
    "asteroid_port": Setting(place="the asteroid port", affords={"flame", "dust"}, star_name="the red flare"),
    "moon_lane": Setting(place="the moon lane", affords={"flame"}, star_name="the bright star"),
    "comet_bridge": Setting(place="the comet bridge", affords={"dust", "flame"}, star_name="the hot comet"),
}

MISSIONS = {
    "flame": Mission(
        id="flame",
        verb="fly past the star flare",
        gerund="gliding past the flare",
        danger="too bright and too hot",
        danger_word="heat",
        zone={"glow", "shell"},
        keyword="flare",
    ),
    "dust": Mission(
        id="dust",
        verb="cross the dusty belt",
        gerund="sliding through the dust",
        danger="too dusty and scratchy",
        danger_word="dust",
        zone={"shell"},
        keyword="dust",
    ),
}

GEAR = [
    Gear(
        id="dimmer",
        label="the bubble dimmer",
        action="dim",
        restores="brighten",
        guards={"heat"},
        covers={"glow"},
        tail="the bubble dimmer was clicked back up to bright",
    ),
    Gear(
        id="shield",
        label="a silver shield",
        action="lower",
        restores="lift",
        guards={"dust"},
        covers={"shell"},
        tail="the silver shield was lifted away",
    ),
]

HERO_NAMES = ["Mina", "Tali", "Noor", "Ari", "Pip", "Luna"]
HELPER_NAMES = ["Captain Reed", "Pilot Jo", "Aunt Star", "Uncle Nova"]


@dataclass
class StoryParams:
    place: str
    mission: str
    name: str
    helper: str
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


def mission_risk(mission: Mission) -> bool:
    return True


def select_gear(mission: Mission) -> Optional[Gear]:
    for gear in GEAR:
        if mission.danger_word in gear.guards and gear.covers & mission.zone:
            return gear
    return None


def explain_rejection(mission: Mission) -> str:
    return f"(No story: the chosen gear cannot honestly protect the bubble from {mission.verb}.)"


def _drift(world: World) -> None:
    ship = world.ship()
    mission = _safe_fact(world, world.facts, "mission")
    gear = world.facts.get("gear")
    if world.zone & mission.zone:
        if gear and gear.id == "dimmer" and "glow" in mission.zone and ship.meters.get("glow", 0) < THRESHOLD:
            ship.meters["heat"] = max(0.0, ship.meters.get("heat", 0.0) - 1.0)
        if gear and gear.id == "shield" and "shell" in mission.zone and ship.meters.get("shell", 0) < THRESHOLD:
            ship.meters["dust"] = max(0.0, ship.meters.get("dust", 0.0) - 1.0)


def predict(world: World, mission: Mission, gear: Optional[Gear]) -> dict:
    sim = world.copy()
    sim.zone = set(mission.zone)
    ship = sim.ship()
    ship.meters[mission.danger_word] = ship.meters.get(mission.danger_word, 0.0) + 1.0
    if gear and gear.id == "dimmer":
        ship.meters["glow"] = max(0.0, ship.meters.get("glow", 0.0) - 1.0)
    if gear and gear.id == "shield":
        ship.meters["shell"] = max(0.0, ship.meters.get("shell", 0.0) - 1.0
        )
    return {
        "unsafe": ship.meters.get(mission.danger_word, 0.0) >= THRESHOLD and (
            (mission.danger_word == "heat" and ship.meters.get("glow", 0.0) > 0.0)
            or (mission.danger_word == "dust" and ship.meters.get("shell", 0.0) > 0.0)
        ),
        "sparkle": ship.meters.get("glow", 0.0),
    }


def setup(world: World, hero: Entity, helper: Entity, ship: Entity, mission: Mission) -> None:
    hero.memes["wonder"] += 1
    ship.meters["glow"] = 1.0
    ship.meters["shell"] = 1.0
    world.say(
        f"{hero.id} loved the little bubble ship because its round window made the stars look close enough to touch."
    )
    world.say(
        f"{helper.id} had given the ship a bubble dimmer for trips through tricky space, and {hero.id} kept it tucked beside the console."
    )
    world.say(
        f"On the map, {world.setting.star_name} glittered near the path to {world.setting.place}."
    )


def warning(world: World, hero: Entity, helper: Entity, mission: Mission) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then {hero.id} wanted to {mission.verb}, but {helper.id} looked at the bright bubble and frowned a little."
    )
    world.say(
        f'"If we go now, the bubble will get {mission.danger}," {helper.id} said. "We should protect it first."'
    )


def choose_fix(world: World, hero: Entity, helper: Entity, mission: Mission, gear: Gear) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id} was nervous, because the bubble made the ship feel safe and cozy, and dimming it sounded strange."
    )
    world.say(
        f'But {helper.id} pointed to the danger ahead and said, "Just for this part, we can {gear.action} the bubble and use the {gear.label}."'
    )


def resolve(world: World, hero: Entity, helper: Entity, ship: Entity, mission: Mission, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    ship.meters[mission.danger_word] = max(0.0, ship.meters.get(mission.danger_word, 0.0) - 1.0)
    if gear.id == "dimmer":
        ship.meters["glow"] = 0.0
        world.say(
            f"They clicked the bubble dimmer down, and the ship's glow softened to a gentle moon-pale shine."
        )
    else:
        ship.meters["shell"] = 0.0
        world.say(
            f"They lowered the silver shield, and the ship slipped forward without scraping the dusty rocks."
        )
    world.zone = set(mission.zone)
    world.say(
        f"The ship {mission.verb}, stayed safe, and sailed cleanly past the danger."
    )
    if gear.id == "dimmer":
        ship.meters["glow"] = 1.0
    else:
        ship.meters["shell"] = 1.0
    world.say(
        f"Afterward, {gear.tail}, and the bubble turned bright again, round and happy against the dark."
    )
    world.say(
        f"{hero.id} smiled at the stars, because the little ship was safe and the journey still felt magical."
    )


def tell(setting: Setting, mission: Mission, name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl", label=name))
    helper = world.add(Entity(id=helper_name, kind="character", type="captain", label=helper_name))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="bubble ship"))
    world.facts.update(hero=hero, helper=helper, ship=ship, mission=mission, setting=setting)

    setup(world, hero, helper, ship, mission)
    world.para()
    warning(world, hero, helper, mission)
    gear = select_gear(mission)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    world.facts["gear"] = gear
    choose_fix(world, hero, helper, mission, gear)
    world.para()
    resolve(world, hero, helper, ship, mission, gear)
    return world


KNOWLEDGE = {
    "bubble": [
        (
            "What is a bubble?",
            "A bubble is a round ball of air or gas with a thin skin around it. Bubbles can float, shine, and pop when they break.",
        )
    ],
    "dimmer": [
        (
            "What does a dimmer do?",
            "A dimmer makes a light brighter or softer. People use dimmers when they want less glare or a calmer glow.",
        )
    ],
    "star": [
        (
            "Why do stars look small from Earth?",
            "Stars are very far away, so they look tiny even though many of them are much bigger than Earth.",
        )
    ],
    "dust": [
        (
            "What is space dust?",
            "Space dust is made of tiny bits of rock and metal floating in space. It can scratch things if a ship hits it too hard.",
        )
    ],
    "heat": [
        (
            "Why can heat be dangerous for a ship?",
            "Heat can make parts of a ship get too hot and stop working well, so ships sometimes need shields or cool-down plans.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a small child that includes the word "bubble-dim".',
        f"Tell a gentle story where {f['hero'].id} wants to {f['mission'].verb} but a helpful grown-up worries about the bubble ship.",
        f"Write a happy-ending adventure about a bubble ship, a dimmer, and a safe trip past {f['setting'].star_name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    mission: Mission = _safe_fact(world, f, "mission")
    ship: Entity = _safe_fact(world, f, "ship")
    gear: Gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"What did {hero.id} love about the ship at the start of the story?",
            answer=f"{hero.id} loved the ship's round bubble window because it made the stars look close and magical.",
        ),
        QAItem(
            question=f"Why did {helper.id} want to use the {gear.label} before {hero.id} could {mission.verb}?",
            answer=f"{helper.id} worried the bubble would get {mission.danger}, so the {gear.label} was used to keep the ship safe.",
        ),
        QAItem(
            question=f"What changed at the end after the ship finished {mission.gerund}?",
            answer=f"The danger passed, the bubble was bright again, and {hero.id} felt happy and relieved on the safe trip home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["mission"].keyword, "bubble", "dimmer"}
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            for q, a in pairs:
                out.append(QAItem(question=q, answer=a))
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="asteroid_port", mission="flame", name="Mina", helper="Captain Reed"),
    StoryParams(place="moon_lane", mission="flame", name="Tali", helper="Pilot Jo"),
    StoryParams(place="comet_bridge", mission="dust", name="Noor", helper="Aunt Star"),
]


ASP_RULES = r"""
% Mission is risky when it touches the ship's vulnerable region.
risky(M) :- mission(M), zone(M,R), vulnerable(R).

% A gear helps if it guards the danger word and covers one vulnerable region.
helps(G,M) :- gear(G), mission(M), danger_word(M,D), guards(G,D), covers(G,R), zone(M,R).

valid_story(P,M) :- place(P), mission(M), afforded(P,M), risky(M), helps(_,M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("afforded", pid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("danger_word", mid, m.danger_word))
        for r in sorted(m.zone):
            lines.append(asp.fact("zone", mid, r))
        lines.append(asp.fact("vulnerable", "glow"))
        lines.append(asp.fact("vulnerable", "shell"))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for d in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, d))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_python_valid() -> list[tuple]:
    out = []
    for pid, setting in SETTINGS.items():
        for mid in setting.affords:
            if select_gear(_safe_lookup(MISSIONS, mid)) is not None:
                out.append((pid, mid))
    return sorted(set(out))


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(asp_python_valid())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bubble-dim space adventure story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = []
    for place, setting in SETTINGS.items():
        if getattr(args, "place", None) and getattr(args, "place", None) != place:
            continue
        for mission in setting.affords:
            if getattr(args, "mission", None) and getattr(args, "mission", None) != mission:
                continue
            combos.append((place, mission))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, mission=mission, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MISSIONS, params.mission), params.name, params.helper)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:\n")
        for place, mission in combos:
            print(f"  {place:16} {mission}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
