#!/usr/bin/env python3
"""
whoop_quest_pirate_tale.py
==========================

A tiny pirate-quest storyworld with a cheerful "whoop" beat.

Premise:
A small crew sails out to fetch a needed quest prize from a tricky island.
One pirate gets excited, another worries about the route or the storm,
and the crew ends by choosing a clever pirate way forward.

The world is intentionally small and constraint-checked:
- only a few plausible quest targets
- only a few plausible ship tools / fixes
- every generated story is a complete beginning / turn / ending
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    captain: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "mate", "sailor"}
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
    sea: str
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
    goal: str
    gerund: str
    danger: str
    risk: str
    zone: set[str]
    weather: str
    keyword: str = "quest"
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
class Fix:
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
        self.zone: set[str] = set()
        self.weather: str = ""
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", sea="the blue sea", affords={"sail", "quest"}),
    "cove": Setting(place="the cove", sea="the green sea", affords={"sail", "quest"}),
    "reef": Setting(place="the reef", sea="the bright sea", affords={"sail", "quest"}),
}

QUESTS = {
    "map": Quest(
        id="map",
        goal="find the hidden map",
        gerund="following the treasure map",
        danger="the spray and wind",
        risk="the map could blow overboard",
        zone={"hands", "torso"},
        weather="windy",
        keyword="map",
        tags={"map", "paper"},
    ),
    "lantern": Quest(
        id="lantern",
        goal="carry the lantern to the cave",
        gerund="carrying the lantern",
        danger="the splashing waves",
        risk="the lantern could get soaked",
        zone={"hands"},
        weather="stormy",
        keyword="lantern",
        tags={"lantern", "light"},
    ),
    "compass": Quest(
        id="compass",
        goal="bring the compass to the captain",
        gerund="guarding the compass",
        danger="the sharp rain",
        risk="the compass could rust",
        zone={"hands", "torso"},
        weather="rainy",
        keyword="compass",
        tags={"compass", "metal"},
    ),
    "key": Quest(
        id="key",
        goal="deliver the old key",
        gerund="carrying the old key",
        danger="the rough sea wind",
        risk="the key could be lost in a jolt",
        zone={"hands"},
        weather="windy",
        keyword="key",
        tags={"key", "metal"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="the hidden map", type="map", region="hands"),
    "lantern": Prize(label="lantern", phrase="a brass lantern", type="lantern", region="hands"),
    "compass": Prize(label="compass", phrase="a pocket compass", type="compass", region="hands"),
    "key": Prize(label="key", phrase="an old brass key", type="key", region="hands"),
}

FIXES = [
    Fix(
        id="oilcloth",
        label="an oilcloth wrap",
        covers={"hands", "torso"},
        guards={"wet", "rust"},
        prep="wrap the prize in oilcloth first",
        tail="used the oilcloth wrap before they sailed on",
    ),
    Fix(
        id="gloves",
        label="dry gloves",
        covers={"hands"},
        guards={"wet", "rust"},
        prep="put on dry gloves first",
        tail="pulled on the dry gloves and kept watch",
    ),
    Fix(
        id="chest",
        label="a small chest",
        covers={"hands"},
        guards={"wet", "rust", "wind"},
        prep="stash it in a small chest",
        tail="locked it in a small chest and tied it down",
        plural=False,
    ),
]

CREW_NAMES = ["Pip", "Mara", "Ned", "Jory", "Bea", "Finn", "Tess", "Rook"]
TRAITS = ["brave", "spry", "quick", "curious", "cheery", "stubborn"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    title: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Logic helpers
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


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_fix(quest: Quest, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if prize.region in fix.covers and quest.risk.split()[-1].strip(".") in fix.guards or quest.weather:
            if any(g in fix.guards for g in {"wet", "rust", "wind"}) and prize.region in fix.covers:
                return fix
    # simpler rule: if it covers the region and guards the relevant hazard, it's okay
    for fix in FIXES:
        if prize.region in fix.covers:
            if quest.id in {"map", "key"} and ("wind" in fix.guards or "wet" in fix.guards):
                return fix
            if quest.id in {"lantern", "compass"} and ("wet" in fix.guards or "rust" in fix.guards):
                return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = _safe_lookup(QUESTS, qid)
            for pid, prize in PRIZES.items():
                if prize_at_risk(quest, prize) and select_fix(quest, prize):
                    combos.append((place, qid, pid))
    return combos


def explain_rejection(quest: Quest, prize: Prize) -> str:
    if not prize_at_risk(quest, prize):
        return (
            f"(No story: {quest.gerund} doesn't really threaten a {prize.label}; "
            f"the prize isn't in the splash zone, so there is no honest pirate worry.)"
        )
    return (
        f"(No story: no fix in this little catalog can reasonably protect a {prize.label} "
        f"for that quest.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    world.zone = set(quest.zone)
    hero.meters["pressure"] = hero.meters.get("pressure", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    if narrate:
        world.say(f"{hero.pronoun().capitalize()} set off on the quest.")
    # minor physical consequence
    if quest.weather == "stormy":
        hero.meters["wet"] = hero.meters.get("wet", 0) + 1


def predict_risk(world: World, hero: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    prize = sim.entities[prize_id]
    return {"risk": bool(prize and sim.zone and prize.region in sim.zone), "wet": sim.get(hero.id).meters.get("wet", 0)}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait', 'small')} pirate who loved a good quest.")


def set_sail(world: World, hero: Entity, setting: Setting, quest: Quest) -> None:
    world.say(
        f"One morning, {hero.id} and the crew looked out over {setting.sea} from {setting.place}."
    )
    world.say(f"They were ready for a {quest.keyword} quest.")


def want_quest(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.id} wanted to {quest.goal}, but the prize was precious and the route was rough."
    )


def warn(world: World, captain: Entity, hero: Entity, quest: Quest, prize: Entity) -> bool:
    pred = predict_risk(world, hero, quest, prize.id)
    if not pred["risk"]:
        return False
    world.facts["predicted_wet"] = pred["wet"]
    world.say(
        f'"Whoop," said {captain.id}, "if ye rush in, that {prize.label} may get lost in the spray."'
    )
    return True


def whoop(world: World, hero: Entity) -> None:
    hero.memes["excitement"] = hero.memes.get("excitement", 0) + 1
    world.say(f'{hero.id} gave a bright "Whoop!" and leaned toward the quest.')
    world.say(f"But {hero.id} still had to listen to the warning.")


def choose_fix(world: World, captain: Entity, hero: Entity, quest: Quest, prize: Entity) -> Optional[Fix]:
    fix = select_fix(quest, prize)
    if fix is None:
        return None
    world.say(
        f'{captain.id} smiled. "How about we {fix.prep}?"'
    )
    return fix


def accept_fix(world: World, hero: Entity, captain: Entity, quest: Quest, prize: Entity, fix: Fix) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} nodded, took the {fix.label}, and set the prize safely for the trip."
    )
    world.say(
        f'Then they {fix.tail}. Soon the crew were {quest.gerund}, and the {prize.label} stayed safe.'
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, hero_type: str, title: str, trait: str) -> World:
    world = World(setting)
    world.weather = quest.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"trait": trait}))
    captain = world.add(Entity(id="Captain", kind="character", type=title, label="the captain"))
    prize = world.add(Entity(
        id=prize_cfg.label,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        owner=hero.id,
        caretaker=captain.id,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    set_sail(world, hero, setting, quest)
    want_quest(world, hero, quest, prize)
    world.para()
    warn(world, captain, hero, quest, prize)
    whoop(world, hero)
    world.para()
    fix = choose_fix(world, captain, hero, quest, prize)
    if fix:
        accept_fix(world, hero, captain, quest, prize, fix)

    world.facts.update(
        hero=hero,
        captain=captain,
        prize=prize,
        quest=quest,
        setting=setting,
        fix=fix,
        resolved=fix is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest, prize = f["hero"], f["quest"], f["prize"]
    return [
        f'Write a short pirate tale for a child that includes the word "whoop" and the word "{quest.keyword}".',
        f"Tell a gentle pirate story where {hero.id} wants to {quest.goal} but worries about {prize.phrase}.",
        f"Write a quest story at {world.setting.place} with a cheerful pirate who says 'Whoop!' before a careful choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, quest = f["hero"], f["captain"], f["prize"], f["quest"]
    qa = [
        QAItem(
            question=f"Who is the pirate story about?",
            answer=f"It's about {hero.id}, a {hero.memes.get('trait', 'small')} pirate, and {captain.label} on a quest together.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.goal}, which is why the crew set out from {world.setting.place}.",
        ),
        QAItem(
            question=f"What prize was in danger?",
            answer=f"The prize was {prize.phrase}. The crew worried it could get damaged on the quest.",
        ),
    ]
    if f.get("resolved"):
        fix = _safe_fact(world, f, "fix")
        qa.append(
            QAItem(
                question=f"How did the crew keep the prize safe?",
                answer=f"They used {fix.label} so the prize could stay safe while they went on with the quest.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt happy and proud, and even after the warning, the story ended with a bright whoop and a safer plan.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "map": [
        QAItem(
            question="What is a map?",
            answer="A map is a drawing that shows where places are and helps people find their way.",
        )
    ],
    "lantern": [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light so people can see in dark places.",
        )
    ],
    "compass": [
        QAItem(
            question="What is a compass for?",
            answer="A compass helps people know which way is north and helps them travel in the right direction.",
        )
    ],
    "key": [
        QAItem(
            question="What is a key for?",
            answer="A key is used to open a lock or a door.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    qid = _safe_fact(world, world.facts, "quest").id
    out.extend(WORLD_KNOWLEDGE.get(qid, []))
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
    lines.append("== (3) World knowledge ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(Q, P) :- quest(Q), zone(Q, R), prize(P), worn_on(P, R).
has_fix(Q, P) :- prize_at_risk(Q, P), fix(F), covers(F, R), worn_on(P, R), guards(F, H), hazard(Q, H).
valid(Place, Q, P) :- afford(Place, Q), prize_at_risk(Q, P), has_fix(Q, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for qid in setting.affords:
            lines.append(asp.fact("afford", pid, qid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for r in q.zone:
            lines.append(asp.fact("zone", qid, r))
        for tag in q.tags:
            lines.append(asp.fact("hazard", qid, tag))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for c in fx.covers:
            lines.append(asp.fact("covers", fx.id, c))
        for g in fx.guards:
            lines.append(asp.fact("guards", fx.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate quest storyworld with a whoop.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--title", choices=["captain", "mate"])
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
    if getattr(args, "quest", None) and getattr(args, "prize", None):
        q, p = _safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(q, p) and select_fix(q, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CREW_NAMES)
    title = getattr(args, "title", None) or rng.choice(["captain", "mate"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, title=title, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.title, params.trait)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="harbor", quest="map", prize="map", name="Pip", gender="boy", title="captain", trait="brave"),
    StoryParams(place="cove", quest="lantern", prize="lantern", name="Mara", gender="girl", title="mate", trait="curious"),
    StoryParams(place="reef", quest="compass", prize="compass", name="Jory", gender="boy", title="captain", trait="cheery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:\n")
        for place, q, p in vals:
            print(f"  {place:8} {q:8} {p:8}")
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
