#!/usr/bin/env python3
"""
storyworlds/worlds/bewitch_pistol_pallette_bad_ending_surprise_magic.py
=======================================================================

A small, standalone Storyweavers world about a child, a paint pallette, a toy
pistol, and a surprising bit of magic that goes wrong before it turns warm
again.

Seed tale shape:
- A child loves a special pallette for painting.
- A playful toy pistol appears as part of a surprise.
- A tiny bewitchment makes the toy act in an unexpected way.
- The surprise ruins the painting day, but the people in the story stay kind.

This world keeps the prose child-facing and concrete, while the simulated state
tracks who owns what, which item is at risk, and how the surprise changes the
ending image.
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
    kind: str = "thing"  # "character" | "thing"
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

    child: object | None = None
    parent: object | None = None
    prize: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Room:
    place: str = "the art room"
    indoors: bool = True
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
class Surprise:
    id: str
    label: str
    kind: str
    action: str
    twist: str
    fallout: str
    tags: set[str] = field(default_factory=set)
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
    area: str
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
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


ROOMS = {
    "art_room": Room(place="the art room", indoors=True, affords={"paint", "magic"}),
    "kitchen_table": Room(place="the kitchen table", indoors=True, affords={"paint", "magic"}),
    "back_porch": Room(place="the back porch", indoors=False, affords={"paint", "magic"}),
}

SURPRISES = {
    "bewitch": Surprise(
        id="bewitch",
        label="a little bewitching",
        kind="magic",
        action="say a funny magic word",
        twist="the spell woke up the toy pistol",
        fallout="it splattered the pallette with bright, sticky sparks",
        tags={"magic", "surprise"},
    ),
    "pistol": Surprise(
        id="pistol",
        label="a toy pistol surprise",
        kind="toy",
        action="pull the tiny trigger",
        twist="the toy pistol popped open and flashed",
        fallout="the flash jumped onto the pallette and made a messy surprise",
        tags={"surprise"},
    ),
    "pallette": Surprise(
        id="pallette",
        label="a pallette surprise",
        kind="art",
        action="mix the colors",
        twist="the colors began to shimmer like they had a secret",
        fallout="the pallette glowed too hard and cracked a little",
        tags={"magic", "surprise"},
    ),
}

PRIZES = {
    "pallette": Prize(
        label="pallette",
        phrase="a bright wooden pallette with little color wells",
        type="pallette",
        area="hands",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a paint apron",
        covers={"hands", "torso"},
        guards={"glitter", "paint", "magic"},
        prep="put on a paint apron first",
        tail="walked back for the apron",
    ),
    Gear(
        id="gloves",
        label="soft art gloves",
        covers={"hands"},
        guards={"paint", "spark", "glitter"},
        prep="wear soft art gloves",
        tail="picked up the soft art gloves",
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ruby", "Iris", "Tia"]
BOY_NAMES = ["Ben", "Owen", "Milo", "Theo", "Ari", "Leo"]
TRAITS = ["curious", "gentle", "hopeful", "playful", "careful"]


@dataclass
class StoryParams:
    room: str
    surprise: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room_id, room in ROOMS.items():
        for surprise_id in room.affords:
            for prize_id in PRIZES:
                combos.append((room_id, surprise_id, prize_id))
    return combos


def prize_at_risk(surprise: Surprise, prize: Prize) -> bool:
    return prize.area in {"hands", "torso"} and "magic" in surprise.tags


def select_gear(surprise: Surprise, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.area in gear.covers and (surprise.kind in gear.guards or "magic" in gear.guards):
            return gear
    return None


ASP_RULES = r"""
prize_at_risk(S, P) :- surprise(S), prize(P), prize_area(P, hands), surprise_tag(S, magic).
protects(G, S, P) :- gear(G), prize_at_risk(S, P), covers(G, hands), guards(G, magic).
valid(Room, S, P) :- affords(Room, S), prize_at_risk(S, P), protects(_, S, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for s in sorted(room.affords):
            lines.append(asp.fact("affords", room_id, s))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("surprise_tag", sid, *sorted(s.tags)) if False else "")
        for t in sorted(s.tags):
            lines.append(asp.fact("surprise_tag", sid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_area", pid, p.area))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gk in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gk))
    return "\n".join([x for x in lines if x])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    if py - asp_set:
        print(" only in python:", sorted(py - asp_set))
    if asp_set - py:
        print(" only in asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming surprise-magic story world.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--surprise", choices=SURPRISES)
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


def explain_rejection(surprise: Surprise, prize: Prize) -> str:
    return f"(No story: this surprise cannot honestly threaten the {prize.label} in a way that fits the room.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "surprise", None) and getattr(args, "prize", None):
        s, p = _safe_lookup(SURPRISES, getattr(args, "surprise", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(s, p) and select_gear(s, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "room", None) is None or c[0] == getattr(args, "room", None))
              and (getattr(args, "surprise", None) is None or c[1] == getattr(args, "surprise", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    room, surprise, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(room=room, surprise=surprise, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(ROOMS, params.room))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    prize = world.add(Entity(id="pallette", type="pallette", label="pallette",
                             phrase=PRIZES["pallette"].phrase, owner=child.id,
                             caretaker=parent.id, worn_by=child.id))
    toy = world.add(Entity(id="toy_pistol", type="toy", label="toy pistol", owner=child.id))
    world.facts.update(child=child, parent=parent, prize=prize, toy=toy, params=params)
    return world


def predict_wreck(world: World, surprise: Surprise, prize: Entity) -> bool:
    if surprise.id == "bewitch":
        return True
    if surprise.id == "pistol":
        return True
    return surprise.id == "pallette"


def tell(world: World, params: StoryParams) -> World:
    child = world.get(params.name)
    parent = world.get("Parent")
    prize = world.get("pallette")
    surprise = _safe_lookup(SURPRISES, params.surprise)

    add_meme(child, "love", 1)
    add_meme(child, "joy", 1)
    world.say(f"{child.id} was a little {params.trait} {child.type} who loved the pallette.")

    world.say(f"The {parent.label} had brought home {prize.phrase}, and {child.id} used it for tiny pictures every day.")
    world.para()
    world.say(f"One day at {world.room.place}, {child.id} noticed {surprise.label} waiting by the table.")
    world.say(f"It was supposed to {surprise.action}, but instead it {surprise.twist}.")

    if predict_wreck(world, surprise, prize):
        add_meter(prize, "broken", 1)
        add_meter(prize, "mess", 1)
        add_meme(child, "surprise", 1)
        add_meme(parent, "worry", 1)
        world.say(f"{surprise.fallout.capitalize()}.")
        world.say(f"The pallette got messy, and that made the room go very quiet for a moment.")

    world.para()
    if meter(prize, "broken") >= THRESHOLD:
        gear = select_gear(surprise, PRIZES["pallette"])
        if gear:
            add_meme(child, "calm", 1)
            add_meme(parent, "care", 1)
            world.say(f"Then {parent.pronoun('subject').capitalize()} smiled kindly and said, \"We can still make this gentle.\"")
            world.say(f"They could {gear.prep}, but the surprise had already happened, so the old pallette stayed cracked.")
            world.say(f"Still, {child.id} and {parent.id} sat close together, mixed new colors on scrap paper, and drew a tiny sun on the corner.")
            world.say(f"In the end, the bad surprise did not take away their warmth; it only made their hug bigger.")
    else:
        world.say(f"Nothing bad happened after all, and the pallette stayed bright.")
    world.facts.update(surprise=surprise, child=child, parent=parent, prize=prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = _safe_fact(world, f, "params")
    return [
        f'Write a heartwarming story for young children that includes the words "bewitch", "pistol", and "pallette".',
        f"Tell a gentle tale where {p.name} finds a surprise with magic in {_safe_lookup(ROOMS, p.room).place} and the pallette gets into trouble.",
        f"Write a simple story about a toy pistol, a bewitching surprise, and a child learning to stay kind when things go wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = _safe_fact(world, f, "params")
    child, parent, prize, surprise = f["child"], f["parent"], f["prize"], f["surprise"]
    qa = [
        QAItem(
            question=f"What did {child.id} love in the story?",
            answer=f"{child.id} loved the pallette and using it to make little pictures.",
        ),
        QAItem(
            question=f"What kind of surprise did {child.id} find?",
            answer=f"{child.id} found {surprise.label}, and it turned into a magical problem.",
        ),
        QAItem(
            question=f"Why was the ending a bad surprise?",
            answer=f"The surprise made the pallette get messy and cracked, so the day did not go as planned.",
        ),
        QAItem(
            question=f"How did {parent.id} respond when things went wrong?",
            answer=f"{parent.id} stayed kind, talked gently, and helped {child.id} make a new little picture anyway.",
        ),
    ]
    if meter(prize, "broken") >= THRESHOLD:
        qa.append(QAItem(
            question="What finally proved the story was still heartwarming?",
            answer="They sat close together, made a tiny new drawing, and turned the sad moment into a caring one.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pallette used for?",
            answer="A pallette holds paint colors so someone can mix them while making a picture.",
        ),
        QAItem(
            question="What is a toy pistol?",
            answer="A toy pistol is a pretend gun for play, not a real one.",
        ),
        QAItem(
            question="What does it mean to bewitch something?",
            answer="To bewitch something means to use magic on it, often in a surprising or tricky way.",
        ),
        QAItem(
            question="What can happen when magic goes wrong?",
            answer="When magic goes wrong, it can make a mess or change something in a way nobody expected.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(room="art_room", surprise="bewitch", prize="pallette", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(room="kitchen_table", surprise="pistol", prize="pallette", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(room="back_porch", surprise="pallette", prize="pallette", name="Nora", gender="girl", parent="mother", trait="hopeful"),
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


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    world = tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
        print(sorted(set(asp.atoms(model, "valid"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
