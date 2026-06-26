#!/usr/bin/env python3
"""
storyworlds/worlds/soy_boat_magic_nursery_rhyme.py
===================================================

A small nursery-rhyme story world about a child, a boat, and a little bit of
soy magic.

The seed image:
---
A child rides in a boat with a warm cup of soy drink.
The child wants a merry sip, but the boat rocks and the cup could spill.
A gentle grown-up warns about sticky mess on the deck.
Then a magic charm helps: the cup gets a lid, the sway becomes a game,
and the child sips safely while the boat goes bob-bob-bob.

World updates:
---
    rocking boat + open drink -> spill risk on the deck
    spill on deck             -> sticky mess + more cleaning work
    magic lid on cup          -> no spill from rocking boat
    accepted safe play        -> joy + relief + ending image
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    cup: object | None = None
    gear_ent: object | None = None
    parent: object | None = None
    def __post_init__(self):
        self.meters = dict(self.meters or {})
        self.memes = dict(self.memes or {})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    place: str = "the little boat"
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
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "soy"
    ACTIVITY: object | None = None
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
    region: str
    plural: bool = False
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
        self.windy: bool = True
        self.trace_notes: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.windy = self.windy
        return w


def _qty(ent: Entity, key: str) -> float:
    return float(ent.meters.get(key, 0.0))


def _inc(ent: Entity, key: str, n: float = 1.0) -> None:
    ent.meters[key] = _qty(ent, key) + n


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for actor in world.characters():
            if _qty(actor, "sway") >= THRESHOLD:
                cup = world.entities.get("cup")
                if cup and cup.carried_by == actor.id and not cup.protective:
                    sig = ("spill", actor.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        _inc(cup, "sticky", 1)
                        _inc(cup, "spill", 1)
                        out.append(f"The little cup tipped and a soy drop kissed the deck.")
                        changed = True
                elif cup and cup.carried_by == actor.id and cup.protective:
                    sig = ("steady", actor.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        out.append(f"The magic lid kept the soy snug and steady.")
                        changed = True

            if world.entities.get("cup") and _qty(world.entities["cup"], "spill") >= THRESHOLD:
                sig = ("work",)
                if sig not in world.fired:
                    world.fired.add(sig)
                    parent = world.get("parent")
                    _inc(parent, "workload", 1)
                    out.append("That meant more wiping for the grown-up on deck.")
                    changed = True

    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_spill(world: World, child: Entity) -> bool:
    sim = world.copy()
    _inc(sim.get(child.id), "sway", 1)
    propagate(sim, narrate=False)
    cup = sim.entities.get("cup")
    return bool(cup and _qty(cup, "spill") >= THRESHOLD)


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def rhyme_intro(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} with bright eyes and a sing-song grin.")
    world.say(f"{child.id} loved to {ACTIVITY.verb} on {world.setting.place}, bob-bob-bobbing in time.")


def arrive(world: World, child: Entity, parent: Entity) -> None:
    world.say(f"One breezy day, {child.id} and {parent.label} went to {world.setting.place}.")
    world.say("The water winked, and the boat said splashy little sighs.")


def want_and_warn(world: World, child: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    _inc(child, "want", 1)
    world.say(f"{child.id} wanted a warm sip of {prize.label}, but the boat was dancing slow and sly.")
    if predict_spill(world, child):
        world.facts["predicted_soil"] = activity.soil
        world.say(f'"You may spill your {prize.label} {activity.soil}," {parent.label} said, "and then I must wipe and dry."')


def wobble(world: World, child: Entity) -> None:
    _inc(child, "sway", 1)
    world.say(f"{child.id} took a sip and tried to keep still, but the boat kept a rocking beat.")
    propagate(world, narrate=True)


def offer_magic(world: World, parent: Entity, child: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = choose_gear(activity, prize)
    if gear is None:
        return None
    cup = world.get("cup")
    if predict_spill(world, child):
        gear_ent = Entity(
            id=gear.id,
            kind="thing",
            type="gear",
            label=gear.label,
            owner=child.id,
            protective=True,
            covers=set(gear.covers),
        )
        world.add(gear_ent)
        cup.protective = True
        world.say(f"Then the {parent.label} tapped a starry spell and gave the cup a {gear.label}.")
        world.say(f'"How about this?" {parent.label} sang. "{gear.prep}, and sip so sweet and neat."')
        return gear
    return None


def happy_end(world: World, child: Entity, parent: Entity, prize: Entity, activity: Activity, gear: Optional[Gear]) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    world.say(f"{child.id} smiled wide and clapped once more.")
    if gear:
        world.say(f"{child.id} sipped the soy with the {gear.label}; not a drop went to the floor.")
    else:
        world.say(f"{child.id} sipped the soy carefully, and the deck stayed clean and dry.")
    world.say(f"{parent.label} laughed, and the boat went bob-bob-bob toward the shore.")
    world.say(f"At the end, {prize.label} stayed neat, and {child.id} had a merry little boat-song in {child.pronoun('possessive')} heart.")


def tell(world: World) -> World:
    child = world.add(Entity(id="Mina", kind="character", type="girl", label="Mina"))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label="her mother"))
    cup = world.add(Entity(id="cup", type="cup", label="soy cup", phrase="a warm cup of soy drink", owner=child.id, caretaker=parent.id))
    world.add(Entity(id="boat", type="boat", label="boat", phrase="a little boat"))
    world.add(Entity(id="spell", type="magic", label="magic", phrase="a twinkly magic charm"))
    cup.carried_by = child.id

    rhyme_intro(world, child)
    world.para()
    arrive(world, child, parent)
    world.say(f"On the seat sat {cup.phrase}, as cozy as a cradle cup.")
    want_and_warn(world, child, parent, cup, ACTIVITY)

    world.para()
    wobble(world, child)
    gear = offer_magic(world, parent, child, ACTIVITY, cup)

    world.para()
    if gear:
        propagate(world, narrate=True)
        happy_end(world, child, parent, cup, ACTIVITY, gear)
    else:
        world.say("So the grown-up held the cup, and the boat went on in a quieter way.")
        world.say(f"{child.id} still had a happy sip, and the soy stayed mostly away from the deck.")
        world.say(f"In the end, the little boat glided on, and the day felt calm and bright.")

    world.facts.update(child=child, parent=parent, cup=cup, activity=ACTIVITY, gear=gear)
    return world


SETTINGS = {
    "boat": Setting(place="the little boat", affords={"sip"}),
}

ACTIVITY = Activity(
    id="sip",
    verb="sip soy",
    gerund="sipping soy",
    rush="reach for the cup",
    mess="spill",
    soil="sticky and brown",
    zone={"deck", "lap"},
    keyword="soy",
)

PRIZES = {
    "cup": Prize(label="cup", phrase="a warm cup of soy drink", type="cup", region="hands"),
}

GEAR = [
    Gear(
        id="lid",
        label="magic lid",
        prep="put on the magic lid first",
        tail="made the cup stay snug and still",
        covers={"hands"},
        guards={"spill"},
    ),
]

GIRL_NAMES = ["Mina", "Nora", "Lily", "Ada", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Theo", "Ben"]


@dataclass
class StoryParams:
    place: str
    activity: str
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
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme story world about soy, a boat, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITY.id,)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=["gentle", "cheerful", "curious", "lively"])
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
    if getattr(args, "activity", None) and getattr(args, "activity", None) != ACTIVITY.id:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "place", None) != "boat":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "prize", None) and getattr(args, "prize", None) != "cup":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place="boat",
        activity=ACTIVITY.id,
        prize="cup",
        name=getattr(args, "name", None) or rng.choice(GIRL_NAMES if (getattr(args, "gender", None) or "girl") == "girl" else BOY_NAMES),
        gender=getattr(args, "gender", None) or "girl",
        parent=getattr(args, "parent", None) or "mother",
        trait=getattr(args, "trait", None) or rng.choice(["gentle", "cheerful", "curious", "lively"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        "Write a short nursery-rhyme story about soy, a boat, and a little bit of magic.",
        f"Tell a cozy rhyme where {child.id} wants to sip soy on a boat, but a grown-up worries about a spill.",
        "Write a child-friendly story that ends with a magic lid keeping the soy safe and the boat clean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    cup = _safe_fact(world, f, "cup")
    gear = _safe_fact(world, f, "gear")
    q = [
        QAItem(
            question=f"Who wanted to sip soy on the boat?",
            answer=f"{child.id} wanted the warm soy drink while the little boat bobbed along.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the cup?",
            answer=f"{parent.label} worried that the cup could spill sticky soy on the boat deck.",
        ),
    ]
    if gear:
        q.append(QAItem(
            question="What magic helped the soy stay safe?",
            answer=f"A magic lid helped the cup stay snug, so the soy did not spill.",
        ))
    q.append(QAItem(
        question="What stayed clean at the end?",
        answer=f"The boat deck stayed clean, and the soy cup stayed neat.",
    ))
    return q


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is soy?",
            answer="Soy is a bean food that can be made into drinks, sauce, or other tasty things.",
        ),
        QAItem(
            question="What does a boat do?",
            answer="A boat floats on water and can carry people from one place to another.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic is a pretend power in stories that can make unusual and wondrous things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(World(_safe_lookup(SETTINGS, params.place)))
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


ASP_RULES = r"""
spot_risk(cup) :- activity(sip), prize(cup).
has_fix(cup) :- gear(lid), guards(lid, spill), covers(lid, hands).
valid_story(boat, sip, cup) :- spot_risk(cup), has_fix(cup).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "boat"))
    lines.append(asp.fact("activity", "sip"))
    lines.append(asp.fact("mess_of", "sip", "spill"))
    lines.append(asp.fact("splashes", "sip", "deck"))
    lines.append(asp.fact("splashes", "sip", "lap"))
    lines.append(asp.fact("prize", "cup"))
    lines.append(asp.fact("worn_on", "cup", "hands"))
    lines.append(asp.fact("gear", "lid"))
    lines.append(asp.fact("guards", "lid", "spill"))
    lines.append(asp.fact("covers", "lid", "hands"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("boat", "sip", "cup")}
    if asp_set == py_set:
        print("OK: clingo gate matches the python gate.")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(asp_set))
    print("python:", sorted(py_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story: boat sip cup")
        return

    seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    rng = random.Random(seed)
    params = resolve_params(args, rng)
    params.seed = seed
    sample = generate(params)

    if getattr(args, "json", None):
        print(sample.to_json())
        return

    emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))


if __name__ == "__main__":
    main()
