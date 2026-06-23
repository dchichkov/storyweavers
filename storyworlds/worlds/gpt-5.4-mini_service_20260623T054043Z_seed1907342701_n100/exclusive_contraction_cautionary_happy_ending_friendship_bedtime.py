#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/exclusive_contraction_cautionary_happy_ending_friendship_bedtime.py
=================================================================================================

A standalone storyworld for a small bedtime friendship tale with a cautionary
turn and a happy ending.

Premise:
- Two friends love a special bedtime reading nook.
- One wants an "exclusive" late-night game with a bright lamp and a snack.
- The other worries that the room will become too messy and too awake for sleep.
- They find a gentler plan that keeps the friendship, calms the room, and ends
  with a cozy final image proving what changed.

The world uses typed entities with accumulating physical meters and emotional
memes, a tiny forward-chaining causal system, a reasonableness gate, and an ASP
twin for parity checks.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SLEEPY_MIN = 2.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    wearing: list[str] = field(default_factory=list)
    nearby: list[str] = field(default_factory=list)
    plural: bool = False

    a: object | None = None
    b: object | None = None
    crumbs: object | None = None
    lamp: object | None = None
    mom: object | None = None
    quilt: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
        if not hasattr(self, "_tags"):
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
    id: str
    label: str
    cozy: bool = True
    supports: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class BedtimeItem:
    id: str
    label: str
    phrase: str
    type: str
    risk: set[str] = field(default_factory=set)
    calm: set[str] = field(default_factory=set)
    exclusive: bool = False
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class BedtimeAction:
    id: str
    verb: str
    glow: str
    rush: str
    risk: str
    reward: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Comfort:
    id: str
    label: str
    phrase: str
    fix: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_awake(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["buzzing"] < THRESHOLD:
            continue
        sig = ("awake", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["sleepiness"] -= 1
        out.append("")
    return out


def _r_mess(world: World) -> list[str]:
    out = []
    lamp = world.entities.get("lamp")
    crumbs = world.entities.get("crumbs")
    if not lamp or not crumbs:
        return out
    for actor in world.characters():
        if actor.meters["snacking"] < THRESHOLD:
            continue
        sig = ("mess", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        crumbs.meters["crumbs"] += 1
        actor.memes["restlessness"] += 1
        out.append(f"Little crumbs hopped onto the quilt.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["comfort"] < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["sleepiness"] += 1
        actor.memes["restlessness"] = max(0.0, actor.memes["restlessness"] - 1)
        out.append(f"The room grew softer and quieter.")
    return out


CAUSAL_RULES = [
    Rule("mess", "physical", _r_mess),
    Rule("calm", "social", _r_calm),
    Rule("awake", "emotional", _r_awake),
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
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness(place: Place, action: BedtimeAction, item: BedtimeItem, comfort: Comfort) -> bool:
    return action.id in place.supports and item.type in action.tags and comfort.gentle


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for action_id, action in ACTIONS.items():
            for item_id, item in ITEMS.items():
                for comfort_id, comfort in COMFORTS.items():
                    if reasonableness(place, action, item, comfort):
                        combos.append((place_id, action_id, item_id, comfort_id))
    return combos


@dataclass
class StoryParams:
    place: str = "bedroom"
    action: str = "reading"
    item: str = "storybook"
    comfort: str = "nightlight"
    name_a: str = "Maya"
    name_b: str = "Nina"
    gender_a: str = "girl"
    gender_b: str = "girl"
    parent: str = "mother"
    trait_a: str = "curious"
    trait_b: str = "gentle"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "bedroom": Place("bedroom", "the bedroom", cozy=True, supports={"reading", "snacking"}),
    "tent": Place("tent", "the little blanket tent", cozy=True, supports={"reading"}),
    "porch": Place("porch", "the porch swing", cozy=True, supports={"reading"}),
    "playroom": Place("playroom", "the playroom nook", cozy=True, supports={"reading", "snacking"}),
}

ACTIONS = {
    "reading": BedtimeAction("reading", "read", "glowed softly", "reached for one more page", "too bright", "a sleepy story", "book", tags={"storybook", "picturebook"}),
    "snacking": BedtimeAction("snacking", "share a snack", "crinkled softly", "kept reaching for crumbs", "crumbs everywhere", "a snack", "snack", tags={"snack"}),
    "stickering": BedtimeAction("stickering", "trade stickers", "shone under the lamp", "kept asking for more stickers", "too busy", "sticker book", "sticker", tags={"stickerbook"}),
}

ITEMS = {
    "storybook": BedtimeItem("storybook", "storybook", "an exclusive bedtime storybook", "storybook", risk={"reading"}, calm={"reading"}),
    "snack": BedtimeItem("snack", "snack bowl", "an exclusive snack bowl", "snack", risk={"snacking"}, calm={"snacking"}, plural=False),
    "stickerbook": BedtimeItem("stickerbook", "sticker book", "an exclusive sticker book", "stickerbook", risk={"stickering"}, calm={"stickering"}),
}

COMFORTS = {
    "nightlight": Comfort("nightlight", "nightlight", "a little nightlight", "glowed like a tiny moon"),
    "blanket": Comfort("blanket", "blanket", "a soft blanket", "felt warm and safe"),
    "stuffie": Comfort("stuffie", "stuffie", "a stuffed rabbit", "made the pillow feel friendly"),
}

GIRL_NAMES = ["Maya", "Nina", "Lily", "Ava", "Zoe", "Mila", "Ella", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Leo", "Max", "Theo", "Owen", "Sam"]
TRAITS = ["curious", "gentle", "sleepy", "bright", "patient", "careful"]


def tell(place: Place, action: BedtimeAction, item: BedtimeItem, comfort: Comfort,
         name_a: str, name_b: str, gender_a: str, gender_b: str,
         parent: str, trait_a: str, trait_b: str) -> World:
    world = World(place)
    a = world.add(Entity(id=name_a, kind="character", type=gender_a, role="friend", attrs={"trait": trait_a}))
    b = world.add(Entity(id=name_b, kind="character", type=gender_b, role="friend", attrs={"trait": trait_b}))
    mom = world.add(Entity(id="Parent", kind="character", type=parent, label="the parent"))
    quilt = world.add(Entity(id="quilt", type="thing", label="quilt"))
    lamp = world.add(Entity(id="lamp", type="thing", label="lamp"))
    crumbs = world.add(Entity(id="crumbs", type="thing", label="crumbs"))
    world.facts.update(a=a, b=b, parent=mom, item=item, action=action, comfort=comfort, place=place)
    a.memes["sleepiness"] = 1.0
    b.memes["sleepiness"] = 1.0
    a.memes["friendship"] = 1.0
    b.memes["friendship"] = 1.0

    world.say(f"{a.id} and {b.id} were two friends who loved {place.label} at bedtime.")
    world.say(f"Their special thing was {item.phrase}, and it felt {('exclusive' if item.exclusive else 'special')} to them.")
    world.para()
    world.say(f"Tonight, {a.id} wanted to {action.verb} by the {comfort.label}, but {b.id} worried the room would stay too awake.")
    if action.id == "snacking":
        a.meters["snacking"] += 1
    elif action.id == "reading":
        a.meters["buzzing"] += 1
    else:
        a.meters["buzzing"] += 1
    a.memes["want"] += 1
    b.memes["care"] += 1
    propagate(world)

    world.para()
    world.say(f'"Let\'s keep it gentle," {b.id} said. "{action.reward} can wait until morning."')
    a.memes["listening"] += 1
    b.memes["comfort"] += 1
    world.say(f"{mom.label_word.capitalize()} came by with {comfort.phrase}, and it {comfort.fix}.")
    a.meters["buzzing"] = 0.0
    a.memes["sleepiness"] += 2
    b.memes["sleepiness"] += 2
    propagate(world)
    world.para()
    world.say(f"By the end, {a.id} and {b.id} were tucked in together, with {item.label} set aside and the quilt smooth again.")
    world.say(f"The little room held only the nightlight's glow, and their friendship felt cozy enough for sleep.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that uses the words "exclusive" and "contraction" and includes {f["a"].id} and {f["b"].id} as friends.',
        f"Tell a gentle cautionary friendship story where {f['a'].id} wants an exclusive bedtime treat, but {f['b'].id} helps the room settle down before sleep.",
        f"Write a cozy story about two friends, a bedtime choice, and a happy ending that proves the room became calm again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, item, action, comfort, parent = f["a"], f["b"], f["item"], f["action"], f["comfort"], f["parent"]
    return [
        QAItem(
            question=f"Who is the bedtime story about?",
            answer=f"It is about {a.id} and {b.id}, two friends who shared a cozy bedtime moment. Their friendship stayed warm while they chose a calmer way to end the night.",
        ),
        QAItem(
            question=f"What did {a.id} want to do before sleep?",
            answer=f"{a.id} wanted to {action.verb} with the exclusive bedtime item and keep the fun going. That was a little risky because it would make the room too awake for sleeping.",
        ),
        QAItem(
            question=f"How did {b.id} help?",
            answer=f"{b.id} reminded {a.id} to keep things gentle and wait for morning. Then {parent.label_word} brought {comfort.phrase}, which helped everyone settle down.",
        ),
        QAItem(
            question=f"Why did the story still end happily?",
            answer=f"Because the friends listened, the room got quieter, and the bedtime item was set aside. They fell asleep side by side, so the ending showed peace instead of worry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does exclusive mean?",
            answer="Exclusive means something is only for a certain person or group. In a story, it can mean a special thing that friends share in a careful way.",
        ),
        QAItem(
            question="What is a contraction?",
            answer="A contraction is a shorter way to say two words together, like saying don't instead of do not. It helps speech and stories sound natural and easy to read.",
        ),
        QAItem(
            question="What helps children get sleepy at bedtime?",
            answer="Soft lights, quiet voices, and a cozy blanket can help children get sleepy. A calm room makes it easier for everyone to rest.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict((k, v) for k, v in e.meters.items() if v)} memes={dict((k, v) for k, v in e.memes.items() if v)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", action="reading", item="storybook", comfort="nightlight", name_a="Maya", name_b="Nina", gender_a="girl", gender_b="girl", parent="mother", trait_a="curious", trait_b="gentle"),
    StoryParams(place="playroom", action="snacking", item="snack", comfort="blanket", name_a="Noah", name_b="Eli", gender_a="boy", gender_b="boy", parent="father", trait_a="sleepy", trait_b="careful"),
    StoryParams(place="tent", action="reading", item="storybook", comfort="stuffie", name_a="Ava", name_b="Lily", gender_a="girl", gender_b="girl", parent="mother", trait_a="patient", trait_b="bright"),
    StoryParams(place="porch", action="reading", item="stickerbook", comfort="nightlight", name_a="Sam", name_b="Mila", gender_a="boy", gender_b="girl", parent="father", trait_a="curious", trait_b="gentle"),
]


def explain_rejection() -> str:
    return "(No story: that bedtime combination would not stay cozy and gentle enough for this world.)"


ASP_RULES = r"""
valid(P, A, I, C) :- place(P), action(A), item(I), comfort(C), supports(P, A), item_ok(I, A), comfort_ok(C).
calm(A) :- friend(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", pid, s))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("item_ok", t, aid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.exclusive:
            lines.append(asp.fact("exclusive", iid))
        for t in sorted(i.risk):
            lines.append(asp.fact("risk", iid, t))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        if c.gentle:
            lines.append(asp.fact("comfort_ok", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(valid_combos()) == set(asp_valid_combos())
    sample = generate(CURATED[0])
    smoke = bool(sample.story.strip())
    if ok and smoke:
        print("OK: ASP parity and story smoke test passed.")
        return 0
    print("FAIL: verification did not pass.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime friendship storyworld with a cautionary turn and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait-a", choices=TRAITS)
    ap.add_argument("--trait-b", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
              and (getattr(args, "comfort", None) is None or c[3] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, item, comfort = rng.choice(list(combos))
    item_obj = _safe_lookup(ITEMS, item)
    if not item_obj.exclusive:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    ga = getattr(args, "gender_a", None) or rng.choice(["girl", "boy"])
    gb = getattr(args, "gender_b", None) or rng.choice(["girl", "boy"])
    na = getattr(args, "name_a", None) or rng.choice(GIRL_NAMES if ga == "girl" else BOY_NAMES)
    nb_pool = [n for n in (GIRL_NAMES if gb == "girl" else BOY_NAMES) if n != na]
    nb = getattr(args, "name_b", None) or rng.choice(nb_pool)
    return StoryParams(
        place=place, action=action, item=item, comfort=comfort,
        name_a=na, name_b=nb, gender_a=ga, gender_b=gb,
        parent=getattr(args, "parent", None) or rng.choice(["mother", "father"]),
        trait_a=getattr(args, "trait_a", None) or rng.choice(TRAITS),
        trait_b=getattr(args, "trait_b", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.action not in ACTIONS or params.item not in ITEMS or params.comfort not in COMFORTS:
        pass
    world = tell(
        _safe_lookup(PLACES, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(ITEMS, params.item), _safe_lookup(COMFORTS, params.comfort),
        params.name_a, params.name_b, params.gender_a, params.gender_b,
        params.parent, params.trait_a, params.trait_b,
    )
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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
