#!/usr/bin/env python3
"""
A tiny storyworld for an expensive quest in a rhyming-story style.

Premise:
A child wants to go on a quest for a shiny, expensive prize. A careful parent
fears the quest will waste money or damage the prize. The world turns on a
simple, child-facing compromise: choose a safer route, borrow useful gear, and
return with the prize still bright.

The prose aims for a light rhyming-story feel without forcing end-rhymes into
every line. The simulated world drives the turn and ending image.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    g: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ("damage", "dust", "cost", "joy", "worry", "hope", "resolve"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.kind == "group" else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Place:
    name: str
    indoors: bool = False
    has_market: bool = False
    has_path: bool = False
    has_bridge: bool = False
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
class Quest:
    id: str
    goal: str
    verb: str
    rhyming_line: str
    risky_step: str
    risk_kind: str
    risk_zone: str
    expensive: bool = True
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
class Gear:
    id: str
    label: str
    covers: set[str]
    helps_against: set[str]
    bargain_line: str
    ending_line: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def story_pulse(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    parent = _safe_fact(world, world.facts, "parent")
    quest = _safe_fact(world, world.facts, "quest")
    prize = _safe_fact(world, world.facts, "prize")
    world.say(
        f"{hero.id} loved a quest with a sparkle and a shine, "
        f"for {quest.goal} was costly and mighty fine."
    )
    world.say(
        f"{hero.pronoun().capitalize()} hummed, \"I can find it, I can race!\" "
        f"and skipped down the lane with a grin on {hero.pronoun('possessive')} face."
    )
    world.say(
        f"But {parent.id} said, \"Wait now, dear heart, take care; "
        f"an {prize.label} that expensive needs gentle air.\""
    )


def preview_quest(world: World, hero: Entity, quest: Quest) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["resolve"] += 1
    if quest.risky_step == "cross the crumbly bridge":
        if not any(e.protective and "feet" in e.covers for e in sim.characters() for _ in [0]):
            return {"damaged": True, "cost": 1}
    return {"damaged": False, "cost": 0}


def do_risky_step(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["resolve"] += 1
    hero.meters["cost"] += 1
    if quest.risk_zone == "bridge":
        if not any(e.worn_by == hero.id and e.protective and "feet" in e.covers for e in world.entities.values()):
            prize.meters["damage"] += 1
            hero.memes["worry"] += 1


def choose_gear(world: World, quest: Quest, prize: Entity) -> Optional[Gear]:
    for gear in GEAR:
        if quest.risk_kind in gear.helps_against and prize.id in {"glass_star", "golden_key", "pearled_map"}:
            if prize.region in gear.covers:
                return gear
    return None


def tell_story(place: Place, quest: Quest, prize_cfg: dict, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(
        id=prize_cfg["id"],
        type=prize_cfg["type"],
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        owner=hero.id,
        caretaker=parent.id,
    ))
    world.facts.update(hero=hero, parent=parent, quest=quest, prize=prize, trait=trait, place=place)

    story_pulse(world)
    world.para()
    world.say(f"The path was narrow, and wind made a whispery rhyme.")
    world.say(f"{hero.id} wanted to {quest.verb}, straight away in time.")
    world.say(f"{quest.rhyming_line}")
    preview = preview_quest(world, hero, quest)
    if preview["damaged"]:
        world.say(f"{parent.id} frowned, \"That route is rough; it may crack and clatter.\"")
        world.say(f"{hero.id} slowed down and asked, \"What could make it safer, and better, and brighter, and matter?\"")
        gear = choose_gear(world, quest, prize)
        if gear is None:
            pass
        world.para()
        g = world.add(Entity(
            id=gear.id,
            kind="thing",
            type="gear",
            label=gear.label,
            protective=True,
            covers=set(gear.covers),
            owner=hero.id,
        ))
        g.worn_by = hero.id
        world.say(f"{parent.id} brought {gear.label}, light as a song.")
        world.say(f"\"{gear.bargain_line}\" {parent.id} said, \"and then we can go along.\"")
        world.say(f"{hero.id} nodded, and joy grew bright in {hero.pronoun('possessive')} chest.")
        hero.memes["joy"] += 1
        hero.memes["hope"] += 1
        world.para()
        do_risky_step(world, hero, quest, prize)
        if prize.meters["damage"] >= 1:
            pass
        world.say(f"So off they went, with careful feet and a merry, soft tread.")
        world.say(f"They {quest.verb} at last, and the danger had fled.")
        world.say(f"{quest.ending_line}")
    else:
        world.say(f"{parent.id} smiled, \"That sounds safe enough today.\"")
        world.say(f"So {hero.id} went with a happy, hop-skip way.")
        world.say(f"{quest.ending_line}")
    hero.memes["joy"] += 1
    prize.meters["cost"] += 1
    world.facts["resolved"] = True
    world.facts["gear"] = next((e for e in world.entities.values() if e.kind == "thing" and e.protective), None)
    return world


SETTINGS = {
    "market": Place(name="the market", indoors=False, has_market=True, has_path=True),
    "harbor": Place(name="the harbor", indoors=False, has_path=True, has_bridge=True),
    "garden": Place(name="the garden", indoors=False, has_path=True),
}

QUESTS = {
    "bridge_star": Quest(
        id="bridge_star",
        goal="a silver star across the bridge",
        verb="seek the silver star",
        rhyming_line="Across the bridge it twinkled and gleamed, like a candle in a dream.",
        risky_step="cross the crumbly bridge",
        risk_kind="rough",
        risk_zone="bridge",
        tags={"quest", "bridge", "expensive"},
    ),
    "market_key": Quest(
        id="market_key",
        goal="a golden key at the market gate",
        verb="find the golden key",
        rhyming_line="In the market it shone, small and bright, a pocket-sized moon in the light.",
        risky_step="reach into a high stall",
        risk_kind="crowd",
        risk_zone="hand",
        tags={"quest", "market", "expensive"},
    ),
    "garden_map": Quest(
        id="garden_map",
        goal="a pearled map beneath the rose arch",
        verb="retrieve the pearled map",
        rhyming_line="By the roses it waited, neat and sweet, as if it had danced on a careful beat.",
        risky_step="step through thorny vines",
        risk_kind="thorn",
        risk_zone="legs",
        tags={"quest", "garden", "expensive"},
    ),
}

PRIZES = {
    "glass_star": {"id": "glass_star", "type": "star", "label": "glass star", "phrase": "an expensive glass star", "region": "feet"},
    "golden_key": {"id": "golden_key", "type": "key", "label": "golden key", "phrase": "an expensive golden key", "region": "hand"},
    "pearled_map": {"id": "pearled_map", "type": "map", "label": "pearled map", "phrase": "an expensive pearled map", "region": "legs"},
}

GEAR = [
    Gear(id="soft_boots", label="soft boots", covers={"feet"}, helps_against={"rough"}, bargain_line="Soft boots can keep the feet neat", ending_line="The star came home, still shining so sweet.", plural=True),
    Gear(id="coin_pouch", label="a coin pouch", covers={"hand"}, helps_against={"crowd"}, bargain_line="A pouch can keep the coins tucked tight", ending_line="The key was found, and it glowed in delight."),
    Gear(id="long_socks", label="long socks", covers={"legs"}, helps_against={"thorn"}, bargain_line="Long socks can hush the prickly trace", ending_line="The map stayed whole, with a pearly grace.", plural=True),
]

GIRL_NAMES = ["Lily", "Mina", "Tess", "Nora", "June"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Owen", "Jude"]
TRAITS = ["brave", "bright", "curious", "spry", "cheery"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Expensive quest storyworld with a rhyming-story feel.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in SETTINGS.items():
        for qid, q in QUESTS.items():
            for prid, pr in PRIZES.items():
                if q.risk_zone == pr["region"]:
                    combos.append((place, qid, prid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(QUESTS, params.quest),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short rhyming-story about a child named {hero.id} who wants to {quest.verb} for an expensive prize.',
        f'Tell a gentle story where {hero.id} and a parent solve a tricky quest for {prize.phrase}.',
        f'Write a child-friendly quest story with a careful ending and a sparkle of rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    quest = _safe_fact(world, f, "quest")
    prize = _safe_fact(world, f, "prize")
    gear = f.get("gear")
    items = [
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.verb} and bring home {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the quest?",
            answer=f"{parent.id} worried because {prize.phrase} was expensive and the quest could make it unsafe or messy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended with {hero.id} finishing the quest safely and keeping the prize in good shape.",
        ),
    ]
    if gear:
        items.append(QAItem(
            question=f"What helped make the quest safer?",
            answer=f"{gear.label} helped {hero.id} take the safer path.",
        ))
    return items


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does expensive mean?",
            answer="Expensive means something costs a lot of money.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or search to find something important.",
        ),
        QAItem(
            question="Why do careful travelers use gear?",
            answer="Careful travelers use gear to stay safe and keep important things from getting hurt.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_fact(Q).
prize(P) :- prize_fact(P).
at_risk(Q, Pz) :- quest_risk_zone(Q, Z), prize_region(Pz, Z).
compatible(P, Q, Pz) :- place(P), quest(Q), prize(Pz), quest_place(P, Q), at_risk(Q, Pz).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_fact", qid))
        lines.append(asp.fact("quest_place", qid, "any"))
        lines.append(asp.fact("quest_risk_zone", qid, q.risk_zone))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize_fact", pid))
        lines.append(asp.fact("prize_region", pid, pr["region"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


CURATED = [
    StoryParams(place="market", quest="market_key", prize="golden_key", name="Lily", gender="girl", parent="mother", trait="bright"),
    StoryParams(place="harbor", quest="bridge_star", prize="glass_star", name="Finn", gender="boy", parent="father", trait="brave"),
    StoryParams(place="garden", quest="garden_map", prize="pearled_map", name="Mina", gender="girl", parent="mother", trait="cheery"),
]


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
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
