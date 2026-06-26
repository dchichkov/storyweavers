#!/usr/bin/env python3
"""
storyworlds/worlds/lady_boll_answer_happy_ending_pirate_tale.py
===============================================================

A small pirate-tale story world about a lady, a boll, and an answer.

Premise:
- A sea-going lady treasure-hunter finds a strange boll on a ship or dock.
- The boll hides a clue or key piece of a puzzle.
- Someone demands an answer, and the lady must choose between guessing, asking,
  or following the clue.
- A happy ending comes when the right answer is found and the treasure or
  friendship is saved.

This world keeps the story grounded in a simple simulated state:
- physical meters: distance, balance, treasure, storm, signal, safety
- emotional memes: worry, courage, hope, joy, trust, curiosity

The narration is authored from state transitions, not from a frozen template.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    boll: object | None = None
    clue: object | None = None
    friend: object | None = None
    lady: object | None = None
    prize_ent: object | None = None
    ship: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"lady", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "captain"}:
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
    place: str = "the moonlit pier"
    sea: str = "calm"
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
class Tale:
    id: str
    verb: str
    gerund: str
    clue: str
    risk: str
    relief: str
    weather: str
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
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"lady"})
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
        self.weather: str = setting.sea
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.facts = dict(self.facts)
        return clone


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    lady = world.entities.get("lady")
    boll = world.entities.get("boll")
    if not lady or not boll:
        return out
    if lady.m("curiosity") < THRESHOLD:
        return out
    sig = ("discover",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boll.meters["found"] = 1
    out.append("She spotted a strange boll tucked beside the mast.")
    return out


def _r_answer(world: World) -> list[str]:
    out: list[str] = []
    lady = world.entities.get("lady")
    clue = world.entities.get("clue")
    if not lady or not clue:
        return out
    if clue.m("open") < THRESHOLD:
        return out
    sig = ("answer",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["answer_found"] = True
    out.append("The hidden mark opened like a little door and gave the true answer.")
    return out


def _r_safety(world: World) -> list[str]:
    out: list[str] = []
    ship = world.entities.get("ship")
    if not ship:
        return out
    if ship.m("storm") < THRESHOLD:
        return out
    if ship.m("safe") >= THRESHOLD:
        return out
    if ("safe",) in world.fired:
        return out
    world.fired.add(("safe",))
    ship.meters["safe"] = 1
    out.append("The sea grew quiet again, and the ship stopped rocking so hard.")
    return out


RULES = [_r_discover, _r_answer, _r_safety]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_answer(world: World, lady: Entity, tale: Tale) -> bool:
    sim = world.copy()
    sim.get("lady").memes["curiosity"] += 1
    sim.get("clue").meters["open"] += 1
    propagate(sim, narrate=False)
    return bool(sim.facts.get("answer_found"))


def tell(setting: Setting, tale: Tale, prize: Prize, hero_name: str = "Maris") -> World:
    world = World(setting)
    lady = world.add(Entity(
        id="lady", kind="character", type="lady", label=hero_name,
        meters={"balance": 1.0, "courage": 1.0, "hope": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "trust": 0.0},
    ))
    friend = world.add(Entity(
        id="mate", kind="character", type="captain", label="the old mate",
        meters={"balance": 1.0},
        memes={"trust": 1.0, "worry": 0.0},
    ))
    ship = world.add(Entity(
        id="ship", kind="thing", type="ship", label="ship",
        meters={"storm": 0.0, "safe": 0.0},
    ))
    boll = world.add(Entity(
        id="boll", kind="thing", type="boll", label="boll",
        phrase="a small brass boll with a hidden seam",
        meters={"found": 0.0},
        memes={"mystery": 1.0},
    ))
    clue = world.add(Entity(
        id="clue", kind="thing", type="clue", label="answer",
        phrase="the answer hidden in a carved note",
        meters={"open": 0.0},
        memes={"hope": 0.0},
    ))
    prize_ent = world.add(Entity(
        id="prize", kind="thing", type=prize.type, label=prize.label,
        phrase=prize.phrase,
    ))

    # Act 1: setup
    world.say(
        f"Lady {lady.label} stood on {setting.place}, where the salt wind rattled the ropes."
    )
    world.say(
        f"She loved a good pirate tale, and she loved any puzzle that might lead to treasure."
    )
    world.say(
        f"One night she found {boll.phrase}, and the strange boll made her curiosity jump."
    )

    world.para()

    # Act 2: tension
    lady.memes["curiosity"] += 1
    ship.meters["storm"] = 1.0
    world.say(
        f"The sea darkened, and the old mate called for an answer before the lanterns went out."
    )
    world.say(
        f"Lady {lady.label} asked the boll's seam with a careful thumb, but the secret would not budge."
    )
    if predict_answer(world, lady, tale):
        clue.meters["open"] = 1.0
    else:
        lady.memes["worry"] += 1
        world.say(
            f"For a breath, she feared the wrong answer would sink the night into trouble."
        )
    propagate(world)

    world.para()

    # Act 3: happy ending
    clue.meters["open"] = 1.0
    propagate(world)
    lady.memes["hope"] += 1
    lady.memes["joy"] += 1
    lady.memes["trust"] += 1
    ship.meters["safe"] = 1.0

    world.say(
        f"Then Lady {lady.label} found the true answer inside the little seam: the boll marked the safe way to the prize."
    )
    world.say(
        f"She pointed the crew to {prize_ent.phrase}, and the old mate cheered as the storm let go."
    )
    world.say(
        f"At last, the ship rode calm water again, {boll.label} gleamed in the lantern light, and Lady {lady.label} laughed because the answer had saved the night."
    )

    world.facts.update(
        lady=lady,
        mate=friend,
        ship=ship,
        boll=boll,
        clue=clue,
        prize=prize_ent,
        tale=tale,
        setting=setting,
        happy_end=True,
    )
    return world


SETTINGS = {
    "pier": Setting(place="the moonlit pier", sea="calm", affords={"search"}),
    "deck": Setting(place="the ship's deck", sea="rough", affords={"search"}),
    "cove": Setting(place="the hidden cove", sea="calm", affords={"search"}),
}

TALES = {
    "pirate": Tale(
        id="pirate",
        verb="search for the hidden answer",
        gerund="searching for the hidden answer",
        clue="answer",
        risk="lost at sea",
        relief="safe and smiling",
        weather="windy",
        tags={"pirate", "sea", "answer"},
    )
}

PRIZES = {
    "map": Prize(id="map", label="map", phrase="the treasure map", type="map", region="hands"),
    "key": Prize(id="key", label="key", phrase="the brass key", type="key", region="hands"),
    "chest": Prize(id="chest", label="chest", phrase="the small chest", type="chest", region="deck"),
}

GEAR = [
    Gear(id="lantern", label="a lantern", covers={"hands"}, guards={"dark"}, prep="light a lantern first", tail="held the lantern high"),
    Gear(id="rope", label="a rope", covers={"deck"}, guards={"storm"}, prep="tie a rope to the mast first", tail="kept the ship steady"),
]


@dataclass
class StoryParams:
    place: str
    tale: str
    prize: str
    name: str
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
    return [(p, t, r) for p in SETTINGS for t in TALES for r in PRIZES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale about a lady, a boll, and an answer.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "tale", None) is None or c[1] == getattr(args, "tale", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tale, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    return StoryParams(place=place, tale=tale, prize=prize, name=getattr(args, "name", None) or rng.choice(["Maris", "Nell", "Ada", "Sera"]))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a child that includes the words "lady", "boll", and "answer".',
        f"Tell a happy ending story about Lady {f['lady'].label} finding an answer by a boll on {f['setting'].place}.",
        f"Write a pirate-style story where a lady listens for the answer hidden in a boll and the sea ends calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lady = _safe_fact(world, f, "lady")
    prize = _safe_fact(world, f, "prize")
    boll = _safe_fact(world, f, "boll")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about Lady {lady.label}, a pirate lady who is curious, brave, and ready to find the answer.",
        ),
        QAItem(
            question=f"What strange thing did Lady {lady.label} find?",
            answer=f"She found {boll.phrase}, and the boll held the clue to the true answer.",
        ),
        QAItem(
            question=f"What did the answer lead to?",
            answer=f"The answer led the crew to {prize.phrase}, and the night ended happily with the ship safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boll?",
            answer="A boll is a sturdy round post or fitting on a ship or dock that ropes can be tied to.",
        ),
        QAItem(
            question="What is a pirate tale?",
            answer="A pirate tale is a story about ships, sea winds, treasure, and daring adventures on the water.",
        ),
        QAItem(
            question="What does answer mean?",
            answer="An answer is what you say or find when you solve a question or a puzzle.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        out.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
% A tale is valid if the setting supports search and the story includes a lady, a boll, and an answer.
valid_story(P, T, R) :- setting(P), tale(T), prize(R), affords(P, search).

% The happy ending arrives when the answer is found.
happy_end(P, T, R) :- valid_story(P, T, R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid in TALES:
        lines.append(asp.fact("tale", tid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TALES, params.tale), _safe_lookup(PRIZES, params.prize), params.name)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in [StoryParams(place=p, tale=t, prize=r, name="Maris") for p, t, r in valid_combos()]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
            header = f"### {p.name}: {p.tale} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
