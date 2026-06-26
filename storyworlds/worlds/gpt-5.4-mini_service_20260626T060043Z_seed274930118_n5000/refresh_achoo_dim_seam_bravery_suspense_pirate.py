#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about a brave kid on a ship, a worrying seam,
and a refreshing fix after an achoo-dim mishap.

The seed tale imagined for this world:
---
A young pirate named Mira loved exploring the deck of the ship. One windy day,
she noticed a loose seam in the main sail. Soon after, a sneeze from the cabin
lantern-holder made the lamp flame dip achoo-dim, and the deck felt a little
spooky. Mira wanted to stay brave. With the captain's help, she mended the seam,
shook out the sail, and poured fresh water over the lantern shade so the ship
felt bright and safe again.
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
# Core world model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    region: object | None = None
    captain: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate"}
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
class Trouble:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(place="the ship", indoors=False, affords={"seam", "refresh"}),
    "harbor": Setting(place="the harbor", indoors=False, affords={"refresh", "seam"}),
}

TROUBLES = {
    "seam": Trouble(
        id="seam",
        verb="mend the seam",
        gerund="mending the seam",
        rush="dash to the sail",
        mess="torn",
        soil="more torn",
        tags={"seam", "cloth"},
    ),
    "refresh": Trouble(
        id="refresh",
        verb="refresh the lantern shade",
        gerund="refreshing the lantern shade",
        rush="grab the water bucket",
        mess="dull",
        soil="dull and tired",
        tags={"refresh", "water"},
    ),
    "achoo-dim": Trouble(
        id="achoo-dim",
        verb="brighten after the achoo-dim",
        gerund="waiting through the achoo-dim hush",
        rush="hurry for the hatch",
        mess="dim",
        soil="dim and spooky",
        tags={"achoo-dim", "dim", "sneeze"},
    ),
}

PRIZES = {
    "sash": Prize(
        label="sash",
        phrase="a red sailor sash",
        type="sash",
        region="torso",
    ),
    "hat": Prize(
        label="hat",
        phrase="a shiny pirate hat",
        type="hat",
        region="head",
    ),
    "boots": Prize(
        label="boots",
        phrase="sturdy deck boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="needlekit",
        label="a little needle kit",
        covers={"torso"},
        guards={"torn"},
        prep="take out a little needle kit and stitch the sail seam",
        tail="stitched up the seam with careful little threads",
    ),
    Gear(
        id="watercloth",
        label="a wet cloth",
        covers={"head", "torso"},
        guards={"dim", "dull"},
        prep="dip a cloth in cool water and wipe the lantern shade",
        tail="wiped away the dimness with the wet cloth",
    ),
    Gear(
        id="spyglasswrap",
        label="a bright wrap",
        covers={"head", "torso"},
        guards={"dim", "dull", "torn"},
        prep="wrap the lamp and the torn patch in bright cloth",
        tail="wrapped the trouble until the deck looked safer",
    ),
]

NAMES = ["Mira", "Nico", "Suri", "Pip", "Lena", "Tao"]
TRAITS = ["brave", "curious", "steady", "bold"]


# ---------------------------------------------------------------------------
# Logic helpers
# ---------------------------------------------------------------------------

def prize_at_risk(trouble: Trouble, prize: Prize) -> bool:
    if trouble.id == "seam":
        return prize.region == "torso"
    if trouble.id == "refresh":
        return prize.region in {"head", "torso"}
    if trouble.id == "achoo-dim":
        return prize.region in {"head", "torso"}
    return False


def select_gear(trouble: Trouble, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if trouble.mess in g.guards and prize.region in g.covers:
            return g
    return None


def predict_mess(world: World, hero: Entity, trouble: Trouble, prize_id: str) -> dict:
    sim = world.copy()
    _do_trouble(sim, sim.get(hero.id), trouble, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get(trouble.mess, 0.0) >= THRESHOLD}


def _do_trouble(world: World, hero: Entity, trouble: Trouble, narrate: bool = True) -> None:
    if trouble.id not in world.setting.affords:
        return
    if trouble.id == "seam":
        hero.meters["torn"] = hero.meters.get("torn", 0.0) + 1
        world.trace_bits.append("seam_spotted")
        if narrate:
            world.say(f"{hero.id} noticed the seam tugging loose on the sail.")
    elif trouble.id == "refresh":
        hero.meters["dull"] = hero.meters.get("dull", 0.0) + 1
        world.trace_bits.append("refresh_needed")
        if narrate:
            world.say(f"The lantern shade looked tired, and everyone wanted a refresh.")
    elif trouble.id == "achoo-dim":
        hero.meters["dim"] = hero.meters.get("dim", 0.0) + 1
        hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
        world.trace_bits.append("achoo_dim")
        if narrate:
            world.say(f"Then came an achoo-dim hush, and the deck felt spooky for a blink.")


def reasonableness_gate(trouble: Trouble, prize: Prize) -> bool:
    return prize_at_risk(trouble, prize) and select_gear(trouble, prize) is not None


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, captain: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.traits[0]} pirate who loved the salty wind and the creak of the deck."
    )
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like treasure, and {captain.label} kept watch with a kind eye."
    )


def setup_tension(world: World, hero: Entity, captain: Entity, trouble: Trouble, prize: Entity) -> None:
    world.para()
    world.say(f"One windy day, {hero.id} and {captain.label} were on {world.setting.place}.")
    world.say(f"{hero.id} wanted to {trouble.verb}, but the ship was feeling tricky.")
    _do_trouble(world, hero, trouble, narrate=True)
    if trouble.id == "achoo-dim":
        world.say("The sudden achoo-dim made the shadows stretch long and strange.")


def warn_and_turn(world: World, captain: Entity, hero: Entity, trouble: Trouble, prize: Entity) -> Optional[Gear]:
    if not predict_mess(world, hero, trouble, prize.id)["soiled"]:
        return None
    world.say(
        f'"If we do that now, your {prize.label} will get {trouble.soil}," {captain.label} said.'
    )
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.say(f"{hero.id} swallowed hard, but {hero.pronoun()} kept {hero.pronoun('possessive')} bravery close.")
    gear = select_gear(trouble, prize)
    if gear is None:
        return None
    world.say(
        f"Then {captain.label} smiled and said, \"How about we {gear.prep}?\""
    )
    return gear


def resolve(world: World, hero: Entity, captain: Entity, trouble: Trouble, prize: Entity, gear: Gear) -> None:
    world.para()
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.memes["suspense"] = 0.0
    world.say(
        f"{hero.id}'s face grew bright with bravery, and {hero.id} nodded."
    )
    world.say(
        f"They {gear.tail}. Soon {hero.id} was {trouble.gerund}, {prize.label} stayed safe, and the deck felt fresh again."
    )
    if trouble.id == "refresh":
        world.say("The wet cloth gave the lantern a refreshing shine.")
    elif trouble.id == "seam":
        world.say("The sail seam held tight, and the wind filled it like a proud white wing.")
    elif trouble.id == "achoo-dim":
        world.say("After the sneezy dimness passed, the ship looked warm and golden once more.")


@dataclass
class StoryParams:
    place: str
    trouble: str
    prize: str
    name: str
    trait: str
    captain: str
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


def tell(setting: Setting, trouble: Trouble, prize_cfg: Prize, hero_name: str, trait: str, captain_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", traits=[trait, "pirate"]))
    captain = world.add(Entity(id=captain_name, kind="character", type="man", label="the captain"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    hero.meters["bravery"] = 1.0
    intro(world, hero, captain, prize)
    setup_tension(world, hero, captain, trouble, prize)
    gear = warn_and_turn(world, captain, hero, trouble, prize)
    if gear:
        resolve(world, hero, captain, trouble, prize, gear)
    world.facts.update(hero=hero, captain=captain, prize=prize, trouble=trouble, setting=setting, gear=gear)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trouble = _safe_fact(world, f, "trouble")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short pirate tale for a child where a brave pirate named {hero.id} faces a "{trouble.id}" problem and keeps going.',
        f"Tell a suspenseful story on {world.setting.place} where {hero.id} wants to {trouble.verb} without ruining {hero.pronoun('possessive')} {prize.label}.",
        f'Write a gentle pirate adventure that includes the words "refresh", "achoo-dim", and "seam".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    captain = _safe_fact(world, f, "captain")
    prize = _safe_fact(world, f, "prize")
    trouble = _safe_fact(world, f, "trouble")
    qa = [
        QAItem(
            question=f"Who was the brave pirate in the story?",
            answer=f"The brave pirate was {hero.id}, and {captain.label} stayed close by on the ship.",
        ),
        QAItem(
            question=f"What did the seam trouble threaten to do to the {prize.label}?",
            answer=f"It threatened to make the {prize.label} get {trouble.soil}, but the captain fixed it in time.",
        ),
        QAItem(
            question=f"How did the story end after the achoo-dim worry?",
            answer=f"It ended with the ship feeling fresh again, and {hero.id} kept {hero.pronoun('possessive')} bravery strong.",
        ),
    ]
    if f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qa.append(
            QAItem(
                question=f"What helped the pirates solve the problem?",
                answer=f"{gear.label.capitalize()} helped them fix the trouble, so the ship could stay safe and bright.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    trouble = _safe_fact(world, f, "trouble")
    out = []
    if "seam" in trouble.tags:
        out.append(QAItem(
            question="What is a seam?",
            answer="A seam is the line where two pieces of cloth are stitched together.",
        ))
    if "refresh" in trouble.tags:
        out.append(QAItem(
            question="What does refresh mean?",
            answer="Refresh means to make something feel clean, lively, or new again.",
        ))
    if "achoo-dim" in trouble.tags or "sneeze" in trouble.tags:
        out.append(QAItem(
            question="Why does a sneeze sometimes make a story feel funny or surprising?",
            answer="A sneeze can interrupt what is happening, so everyone pauses and looks around in surprise.",
        ))
    out.append(QAItem(
        question="What is bravery?",
        answer="Bravery means staying steady and doing the right thing even when something feels scary.",
    ))
    out.append(QAItem(
        question="What is suspense?",
        answer="Suspense is the nervous feeling you get when you wonder what will happen next.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(bits))
    lines.append(f"facts={world.trace_bits}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(T, P) :- trouble(T), prize(P), worn_on(P, torso), T = seam.
prize_at_risk(T, P) :- trouble(T), prize(P), worn_on(P, head), T = refresh.
prize_at_risk(T, P) :- trouble(T), prize(P), worn_on(P, torso), T = refresh.
prize_at_risk(T, P) :- trouble(T), prize(P), worn_on(P, head), T = achoo_dim.
prize_at_risk(T, P) :- trouble(T), prize(P), worn_on(P, torso), T = achoo_dim.

fix(T, P, G) :- prize_at_risk(T, P), gear(G), trouble_mess(T, M), guards(G, M), covers(G, R), worn_on(P, R).
valid(T, P) :- prize_at_risk(T, P), fix(T, P, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("trouble_mess", tid, t.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    vals = []
    for tid, t in TROUBLES.items():
        for pid, p in PRIZES.items():
            if prize_at_risk(t, p) and select_gear(t, p):
                vals.append((tid, pid))
    return sorted(vals)


def asp_verify() -> int:
    a, p = set(asp_valid()), set(python_valid())
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} valid pairs).")
        return 0
    print("MISMATCH:")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with bravery and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--captain", default="the captain")
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
    if getattr(args, "trouble", None) and getattr(args, "prize", None):
        t, p = _safe_lookup(TROUBLES, getattr(args, "trouble", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(t, p) and select_gear(t, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    places = [k for k, s in SETTINGS.items() if getattr(args, "trouble", None) is None or getattr(args, "trouble", None) in s.affords]
    if getattr(args, "place", None):
        places = [p for p in places if p == getattr(args, "place", None)]
    if not places:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(places)
    trouble_ids = [t for t in _safe_lookup(SETTINGS, place).affords if getattr(args, "trouble", None) is None or t == getattr(args, "trouble", None)]
    if not trouble_ids:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    trouble = getattr(args, "trouble", None) or rng.choice(sorted(trouble_ids))
    valid_prizes = [pid for pid, p in PRIZES.items()
                    if prize_at_risk(_safe_lookup(TROUBLES, trouble), p) and select_gear(_safe_lookup(TROUBLES, trouble), p)]
    if getattr(args, "prize", None):
        valid_prizes = [getattr(args, "prize", None)] if getattr(args, "prize", None) in valid_prizes else []
    if not valid_prizes:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    prize = getattr(args, "prize", None) or rng.choice(valid_prizes)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    captain = getattr(args, "captain", None)
    return StoryParams(place=place, trouble=trouble, prize=prize, name=name, trait=trait, captain=captain)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TROUBLES, params.trouble), _safe_lookup(PRIZES, params.prize), params.name, params.trait, params.captain)
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
    StoryParams(place="ship", trouble="seam", prize="sash", name="Mira", trait="brave", captain="the captain"),
    StoryParams(place="ship", trouble="refresh", prize="hat", name="Nico", trait="steady", captain="the captain"),
    StoryParams(place="harbor", trouble="achoo-dim", prize="boots", name="Suri", trait="bold", captain="the captain"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for v in vals:
            print(v)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
