#!/usr/bin/env python3
"""
A small nursery-rhyme story world about a plunk in a little pond, friendship,
foreshadowing, and a brief flashback to how two friends made a kindly plan.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
class Place:
    name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
    outdoors: bool = False
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
class Action:
    id: str
    verb: str
    gerund: str
    sound: str
    risk: str
    zone: set[str]
    keyword: str = "plunk"
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
class Keepsake:
    id: str
    label: str
    phrase: str
    region: str
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
class Gift:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def worn(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.meters.get("worn_by") == actor.id]


@dataclass
class StoryParams:
    place: str
    action: str
    keepsake: str
    name: str
    gender: str
    friend: str
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


PLACES = {
    "pond": Place("the pond", outdoors=True, affords={"plunk"}),
    "garden": Place("the garden", outdoors=True, affords={"plunk"}),
    "brook": Place("the brook", outdoors=True, affords={"plunk"}),
    "playroom": Place("the playroom", outdoors=False, affords={"plunk"}),
}

ACTIONS = {
    "plunk": Action(
        id="plunk",
        verb="drop pebbles in the water",
        gerund="dropping pebbles into the water",
        sound="plunk",
        risk="wet and muddy",
        zone={"hands", "feet"},
        keyword="plunk",
    ),
}

KEEPSAKES = {
    "shoes": Keepsake("shoes", "shoes", "tiny ribbon shoes", "feet", {"girl", "boy"}),
    "socks": Keepsake("socks", "socks", "soft white socks", "feet", {"girl", "boy"}),
    "dress": Keepsake("dress", "dress", "a bright little dress", "torso", {"girl"}),
    "shirt": Keepsake("shirt", "shirt", "a clean blue shirt", "torso", {"girl", "boy"}),
}

GIFTS = [
    Gift("boots", "rain boots", "rain boots", {"feet"}, {"wet", "muddy"}, "put on rain boots", "walked back for the rain boots"),
    Gift("smock", "smock", "an old smock", {"torso"}, {"wet", "muddy"}, "wear an old smock", "went to get the smock"),
    Gift("apron", "apron", "a little apron", {"torso"}, {"wet"}, "tie on a little apron", "came back with the apron"),
]


def reason_ok(action: Action, keepsake: Keepsake) -> bool:
    return keepsake.region in action.zone


def select_gift(action: Action, keepsake: Keepsake) -> Optional[Gift]:
    for g in GIFTS:
        if keepsake.region in g.covers and action.risk.split()[0] in g.guards:
            return g
    return None


def predict_soil(world: World, actor: Entity, action: Action, keepsake: Entity) -> bool:
    sim = world.copy()
    do_action(sim, sim.get(actor.id), action, narrate=False)
    return sim.get(keepsake.id).meters.get("dirty", 0.0) >= THRESHOLD


def do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.place.affords:
        return
    actor.meters[action.id] = actor.meters.get(action.id, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} loved {action.gerund}, and the pond said {action.sound}, plunk.")

    for e in list(world.entities.values()):
        if e.meters.get("worn_by") == actor.id:
            if e.label and e.meters.get("dirty", 0.0) < THRESHOLD and e.meters.get("protected", 0.0) < THRESHOLD:
                if reason_ok(action, KEEPSAKES.get(e.id, KEEPSAKES.get("shirt"))) and e.id in {"shoes", "socks", "dress", "shirt"}:
                    e.meters["dirty"] = e.meters.get("dirty", 0.0) + 1
                    e.meters["wet"] = e.meters.get("wet", 0.0) + 1


def set_keepsake_story(world: World, hero: Entity, friend: Entity, keepsake: Entity) -> None:
    world.say(f"{hero.id} wore {keepsake.phrase} and {friend.id} watched with a grin.")
    world.say(f"They were friends from the first soft day, when a bluebird trilled in the tree.")


def flashback(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Flashback: long ago, when {hero.id} was shy, {friend.id} shared a berry and said, "
        f"\"We can play in the gentle way.\""
    )
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1


def foreshadow(world: World, hero: Entity, keepsake: Entity, action: Action) -> None:
    world.say(
        f"A little sign hung near the water: a leaf was stuck to a stone, and it looked like a warning "
        f"that {keepsake.label} might get {action.risk}."
    )


def warn(world: World, friend: Entity, hero: Entity, action: Action, keepsake: Entity) -> bool:
    if not predict_soil(world, hero, action, keepsake):
        return False
    world.facts["predicted_risk"] = action.risk
    world.say(
        f"\"If you go plunk in the pond,\" {friend.id} said, "
        f"\"your {keepsake.label} may get {action.risk}.\""
    )
    return True


def resolve(world: World, hero: Entity, friend: Entity, action: Action, keepsake: Entity) -> None:
    gift = select_gift(action, _safe_lookup(KEEPSAKES, keepsake.id))
    if gift is None:
        pass
    world.add(Entity(id=gift.id, kind="thing", type="gift", label=gift.label, phrase=gift.phrase))
    world.get(gift.id).meters["worn_by"] = hero.id
    world.get(gift.id).meters["protected"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(f"{hero.id} nodded, and {friend.id} smiled. \"Then we can {gift.prep} first.\"")
    world.say(
        f"They {gift.tail}, and soon {hero.id} was {action.gerund}, while {keepsake.phrase} stayed neat and dry."
    )


def tell(place: Place, action: Action, keepsake: Keepsake, name: str, gender: str, friend_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend", label=friend_name))
    item = world.add(Entity(id=keepsake.id, kind="thing", type=keepsake.id, label=keepsake.label, phrase=keepsake.phrase))
    item.meters["worn_by"] = hero.id

    world.say(f"{name} was a little {gender} who loved a bright day and a merry game.")
    set_keepsake_story(world, hero, friend, item)
    world.para()
    foreshadow(world, hero, item, action)
    world.say(f"One day, {name} heard the pond go plunk, plunk, plunk, and wanted to {action.verb}.")
    warn(world, friend, hero, action, item)
    world.say(f"{name} remembered the soft promise from long ago.")
    flashback(world, hero, friend)
    world.para()
    world.say(f"{name} could have rushed ahead, but {friend_name} held up a hand and shared a kinder way.")
    resolve(world, hero, friend, action, item)

    world.facts.update(hero=hero, friend=friend, keepsake=item, action=action, place=place)
    return world


SETTINGS = {"pond": PLACES["pond"], "garden": PLACES["garden"], "brook": PLACES["brook"], "playroom": PLACES["playroom"]}


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, p in SETTINGS.items():
        for action in ACTIONS:
            if action in p.affords:
                for kid, k in KEEPSAKES.items():
                    if reason_ok(_safe_lookup(ACTIONS, action), k):
                        out.append((place, kid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    keepsake = _safe_fact(world, f, "keepsake")
    action = _safe_fact(world, f, "action")
    place = _safe_fact(world, f, "place")
    return [
        f"Write a nursery-rhyme story about {hero.id}, a {keepsake.label}, and a plunk at {place.name}.",
        f"Tell a gentle story where friends remember a flashback and choose a safer way before {hero.id} can {action.verb}.",
        f"Write a rhyme with the word \"{action.keyword}\" about friendship and a small warning near the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    keepsake = _safe_fact(world, f, "keepsake")
    action = _safe_fact(world, f, "action")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who wanted to go to {place.name} and {action.verb}?",
            answer=f"{hero.id} wanted to go to {place.name} and {action.verb}.",
        ),
        QAItem(
            question=f"Why did {friend.id} warn {hero.id} about the {keepsake.label}?",
            answer=f"{friend.id} warned {hero.id} because the {keepsake.label} could get {action.risk} near the water.",
        ),
        QAItem(
            question="What old memory came back in the story?",
            answer=f"A flashback showed that {hero.id} and {friend.id} had promised to play in a gentle way before.",
        ),
        QAItem(
            question="How did the friends end the story?",
            answer=f"They chose a safer plan, and {hero.id} still got to enjoy the plunking play while the {keepsake.label} stayed clean.",
        ),
    ]


KNOWLEDGE = {
    "plunk": [
        QAItem(
            question="What does plunk sound like?",
            answer="Plunk is a soft, round sound, like a pebble dropping into water.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share, and help one another.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that goes back to something that happened earlier.",
        )
    ],
    "foreshadowing": [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important may happen later.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["plunk"])
    out.extend(KNOWLEDGE["friendship"])
    out.extend(KNOWLEDGE["foreshadowing"])
    out.extend(KNOWLEDGE["flashback"])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


ASP_RULES = r"""
place(P) :- setting(P).
valid_combo(P,K) :- place(P), keepsake(K), action(plunk), affords(P,plunk), worn_on(K,R), splashes(plunk,R).

foreshadowing(P,K) :- valid_combo(P,K), warning_sign(P,K).
friendship_story(P,K) :- valid_combo(P,K), has_friend(P), has_flashback(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
        for r in sorted(_safe_lookup(ACTIONS, aid).zone):
            lines.append(asp.fact("splashes", aid, r))
    for kid, k in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("worn_on", kid, k.region))
        for g in sorted(k.genders):
            lines.append(asp.fact("for_gender", kid, g))
    lines.append(asp.fact("warning_sign", "pond", "shoes"))
    lines.append(asp.fact("warning_sign", "pond", "socks"))
    lines.append(asp.fact("warning_sign", "garden", "dress"))
    lines.append(asp.fact("has_friend", "pond"))
    lines.append(asp.fact("has_friend", "garden"))
    lines.append(asp.fact("has_flashback", "pond"))
    lines.append(asp.fact("has_flashback", "garden"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme world of plunk, friendship, foreshadowing, and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "keepsake", None):
        combos = [c for c in combos if c[1] == getattr(args, "keepsake", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, keepsake = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(KEEPSAKES, keepsake).genders))
    name = getattr(args, "name", None) or rng.choice(["Mila", "Nora", "Finn", "Toby"])
    friend = getattr(args, "friend", None) or rng.choice(["Pip", "June", "Bea", "Wren"])
    return StoryParams(place=place, action="plunk", keepsake=keepsake, name=name, gender=gender, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(KEEPSAKES, params.keepsake), params.name, params.gender, params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="pond", action="plunk", keepsake="shoes", name="Mila", gender="girl", friend="Pip"),
    StoryParams(place="garden", action="plunk", keepsake="shirt", name="Finn", gender="boy", friend="Bea"),
    StoryParams(place="brook", action="plunk", keepsake="socks", name="Nora", gender="girl", friend="June"),
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
        print(asp_program("#show valid_combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_combo/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.place} with {p.keepsake}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
