#!/usr/bin/env python3
"""
storyworlds/worlds/rue_grouch_hump_cautionary_folk_tale.py
===========================================================

A small cautionary folk-tale storyworld about a rueful traveler, a grouchy
neighbor, and a troublesome hump in the path.

The seed words suggest a tale with:
- rue: regret after a bad choice
- grouch: a grumpy character whose complaints stir trouble
- hump: a physical rise in a road, hill, or load that changes what can happen

This world models a simple village route with a narrow hump-backed bridge.
Characters can choose patience or stubbornness, and the wrong choice leads to a
messy delay, a damaged bundle, or a lonely ending image. The good ending comes
from listening early and taking the safer way.

The prose aims for a folk-tale cadence: concrete, slightly old-fashioned, and
cautionary rather than whimsical.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    burden: object | None = None
    hero: object | None = None
    neighbor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    path_kind: str
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
    risk: str
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
class Burden:
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
class Remedy:
    id: str
    label: str
    helps: set[str]
    fits: set[str]
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.route: str = ""
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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.route = self.route
        clone.paragraphs = [[]]
        return clone


def route_is_risky(trouble: Trouble, burden: Burden) -> bool:
    return burden.region == "back" and trouble.risk in {"stumbles", "snags", "soaks"}


def select_remedy(trouble: Trouble, burden: Burden) -> Optional[Remedy]:
    for r in REMEDIES:
        if trouble.mess in r.helps and burden.region in r.fits:
            return r
    return None


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_stumble(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("hurry", 0.0) < THRESHOLD:
            continue
        if world.route != "hump_bridge":
            continue
        sig = ("stumble", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["stumble"] = actor.meters.get("stumble", 0.0) + 1
        out.append(f"{actor.id} gave the hump bridge a bad step and nearly lost {actor.pronoun('possessive')} balance.")
    return out


def _r_spill(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("stumble", 0.0) < THRESHOLD:
            continue
        for item in world.carried_items(actor):
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            out.append(f"That jolt made {actor.pronoun('possessive')} {item.label} slip and get dirty.")
    return out


def _r_rue(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("stumble", 0.0) < THRESHOLD:
            continue
        sig = ("rue", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["rue"] = actor.memes.get("rue", 0.0) + 1
        out.append(f"By dusk, {actor.id} began to rue {actor.pronoun('possessive')} stubborn step.")
    return out


CAUSAL_RULES = [Rule("stumble", _r_stumble), Rule("spill", _r_spill), Rule("rue", _r_rue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, trouble: Trouble, burden_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["hurry"] = sim.get(actor.id).meters.get("hurry", 0.0) + 1
    sim.route = "hump_bridge" if trouble.id == "bridge" else "safe_lane"
    propagate(sim, narrate=False)
    burden = sim.entities.get(burden_id)
    return {
        "dirty": bool(burden and burden.meters.get("dirty", 0.0) >= THRESHOLD),
        "rue": sum(e.memes.get("rue", 0.0) for e in sim.characters()) > 0,
    }


def introduce(world: World, hero: Entity, neighbor: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "steady")
    world.say(f"In a village by the old road, there lived a little {trait} {hero.type} named {hero.id}.")
    world.say(f"Near the lane stood {neighbor.id}, who was known to grouch at every wet shoe and crooked stone.")


def set_scene(world: World, trouble: Trouble) -> None:
    world.say(f"Between the cottages ran {world.setting.place}, and in the middle of it rose {world.setting.path_kind}.")
    world.say(f"Folks called it the {trouble.keyword}, because it made carts tilt, bundles slide, and proud feet stumble.")


def warn(world: World, neighbor: Entity, hero: Entity, trouble: Trouble, burden: Entity) -> None:
    pred = predict(world, hero, trouble, burden.id)
    if pred["dirty"]:
        world.facts["predicted_dirty"] = True
        world.say(f"'{trouble.risk.capitalize()} will come of that,' {neighbor.id} said. 'Take the level path, and keep your {burden.label} dry.'")


def ignore_warning(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.meters["hurry"] = hero.meters.get("hurry", 0.0) + 1
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"But {hero.id} only shrugged and hurried on, as if a warning were no heavier than a feather.")
    world.say(f"{hero.id} tried to {trouble.rush},")


def take_hump(world: World, hero: Entity, trouble: Trouble) -> None:
    world.route = "hump_bridge"
    propagate(world, narrate=False)
    world.say(f"yet the path climbed the hump, and the whole load pitched to one side.")


def remedy_offer(world: World, neighbor: Entity, hero: Entity, trouble: Trouble, burden: Entity) -> Optional[Remedy]:
    remedy = select_remedy(trouble, burden)
    if remedy is None:
        return None
    world.say(f"Then {neighbor.id} stopped grouching, and in a softer voice said, 'How about we {remedy.prep}?'")
    return remedy


def accept(world: World, hero: Entity, neighbor: Entity, trouble: Trouble, burden: Entity, remedy: Remedy) -> None:
    hero.meters["hurry"] = 0.0
    hero.memes["stubborn"] = 0.0
    hero.memes["rue"] = max(hero.memes.get("rue", 0.0) - 1, 0.0)
    world.say(f"{hero.id} listened at last. Soon they {remedy.tail}, and the {burden.label} stayed sound.")
    world.say(f"By the time they reached the far gate, {hero.id} had no reason to rue the morning at all.")


SETTINGS = {
    "village lane": Setting(place="the village lane", path_kind="a hump-backed bridge", affords={"bridge"}),
    "ridge path": Setting(place="the ridge path", path_kind="a windy hump in the hill", affords={"ridge"}),
    "market way": Setting(place="the market way", path_kind="a stone hump over the stream", affords={"bridge"}),
}

TROUBLES = {
    "bridge": Trouble(
        id="bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        rush="dash across the bridge",
        mess="dirty",
        soil="mud-spattered",
        risk="stumbles",
        keyword="hump-backed bridge",
        tags={"bridge", "hump", "cautionary"},
    ),
    "ridge": Trouble(
        id="ridge",
        verb="climb the ridge",
        gerund="climbing the ridge",
        rush="race up the ridge",
        mess="dirty",
        soil="dusty",
        risk="snags",
        keyword="hump in the hill",
        tags={"ridge", "hump", "cautionary"},
    ),
}

BURDENS = {
    "basket": Burden(label="basket", phrase="a small berry basket", type="basket", region="back"),
    "parcel": Burden(label="parcel", phrase="a wrapped parcel of bread", type="parcel", region="back"),
    "lantern": Burden(label="lantern", phrase="a glass lantern", type="lantern", region="hand"),
}

REMEDIES = [
    Remedy(
        id="wait",
        label="a lantern-lit wait",
        helps={"dirty"},
        fits={"back"},
        prep="wait for the cart and take the flat path instead",
        tail="followed the flat path with the cart lantern bobbing ahead",
    ),
    Remedy(
        id="handcart",
        label="a little handcart",
        helps={"dirty"},
        fits={"back", "hand"},
        prep="put the burden on a little handcart and roll it carefully",
        tail="rolled the burden home without another bump",
        plural=False,
    ),
]


GIRL_NAMES = ["Mara", "Elsie", "Nell", "Tess", "Lina", "Rose"]
BOY_NAMES = ["Jory", "Pip", "Owen", "Bram", "Tobin", "Eli"]
TRAITS = ["steadfast", "curious", "quick-footed", "soft-hearted"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    burden: str
    name: str
    gender: str
    neighbor: str
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
    for s_id, setting in SETTINGS.items():
        for t_id in setting.affords:
            for b_id, burden in BURDENS.items():
                if route_is_risky(_safe_lookup(TROUBLES, t_id), burden) and select_remedy(_safe_lookup(TROUBLES, t_id), burden):
                    combos.append((s_id, t_id, b_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, neighbor, trouble, burden = f["hero"], f["neighbor"], f["trouble"], f["burden"]
    return [
        f'Write a short cautionary folk tale about a {hero.type} named {hero.id}, a grouchy neighbor, and a {trouble.keyword}.',
        f'Tell a village story where {hero.id} tries to {trouble.verb} while carrying {burden.phrase} and learns not to ignore a warning.',
        f'Write a simple folk tale with the words "rue", "grouch", and "hump" in which a bad choice leads to regret and a safer choice ends well.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, neighbor, trouble, burden = f["hero"], f["neighbor"], f["trouble"], f["burden"]
    qa = [
        QAItem(
            question=f"Who was the cautionary tale about in the village by the {trouble.keyword}?",
            answer=f"It was about {hero.id}, a little {next((t for t in hero.traits if t != 'little'), 'steady')} {hero.type}, and {neighbor.id}, the grouchy neighbor.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the hump-backed bridge?",
            answer=f"{hero.id} wanted to {trouble.verb}, even though {hero.pronoun('possessive')} {neighbor.id} warned that trouble could follow.",
        ),
        QAItem(
            question=f"What was {hero.id} carrying that could get ruined?",
            answer=f"{hero.id} was carrying {burden.phrase}, and the rough hump of the road could make it dirty or battered.",
        ),
    ]
    if f.get("warned"):
        qa.append(
            QAItem(
                question=f"Why did {neighbor.id} warn {hero.id} about the hump in the road?",
                answer=f"{neighbor.id} warned {hero.id} because the hump-backed way could jolt the load, make the burden dirty, and leave {hero.id} with rue instead of pride.",
            )
        )
    if f.get("resolved"):
        remedy = _safe_fact(world, f, "remedy")
        qa.append(
            QAItem(
                question=f"How did {hero.id} avoid ruining the burden at the end?",
                answer=f"They chose {remedy.label}, which let them take the safer path and keep the burden sound.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to rue something?",
            answer="To rue something means to feel sorry about it later because you wish you had chosen differently.",
        ),
        QAItem(
            question="What is a grouch?",
            answer="A grouch is a person who complains a lot and often sounds unhappy or cranky.",
        ),
        QAItem(
            question="What is a hump on a road?",
            answer="A hump on a road is a raised bump or hill that can make a cart, a bundle, or a traveler tilt and wobble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  route={world.route}")
    lines.append(f"  fired={sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="village lane", trouble="bridge", burden="basket", name="Mara", gender="girl", neighbor="Old Nib", trait="steadfast"),
    StoryParams(setting="market way", trouble="bridge", burden="parcel", name="Pip", gender="boy", neighbor="Old Nib", trait="quick-footed"),
    StoryParams(setting="ridge path", trouble="ridge", burden="basket", name="Nell", gender="girl", neighbor="Old Nib", trait="curious"),
]


def explain_rejection(trouble: Trouble, burden: Burden) -> str:
    return f"(No story: {trouble.keyword} does not honestly threaten a {burden.label} in this setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary folk-tale story world about rue, a grouch, and a hump.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--neighbor")
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "trouble", None) is None or c[1] == getattr(args, "trouble", None))
              and (getattr(args, "burden", None) is None or c[2] == getattr(args, "burden", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    s, t, b = rng.choice(list(combos))
    trouble = _safe_lookup(TROUBLES, t)
    burden = _safe_lookup(BURDENS, b)
    if getattr(args, "neighbor", None):
        neighbor = getattr(args, "neighbor", None)
    else:
        neighbor = "Old Nib"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(setting=s, trouble=t, burden=b, name=name, gender=gender, neighbor=neighbor, trait=trait)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    trouble = _safe_lookup(TROUBLES, params.trouble)
    burden_cfg = _safe_lookup(BURDENS, params.burden)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait, "stubborn"]))
    neighbor = world.add(Entity(id=params.neighbor, kind="character", type="person", label=params.neighbor))
    burden = world.add(Entity(id="burden", type=burden_cfg.type, label=burden_cfg.label, phrase=burden_cfg.phrase, carried_by=hero.id, region=burden_cfg.region, plural=burden_cfg.plural))

    introduce(world, hero, neighbor)
    set_scene(world, trouble)
    world.para()
    warn(world, neighbor, hero, trouble, burden)
    world.facts["warned"] = True
    ignore_warning(world, hero, trouble)
    take_hump(world, hero, trouble)
    world.para()
    remedy = remedy_offer(world, neighbor, hero, trouble, burden)
    if remedy:
        accept(world, hero, neighbor, trouble, burden, remedy)
    world.facts.update(hero=hero, neighbor=neighbor, trouble=trouble, burden=burden, remedy=remedy, resolved=remedy is not None)
    return world


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
risky(B) :- burden(B), back(B).
stumble(A) :- hurry(A), route(hump_bridge).
spill(B) :- stumble(_), burden(B).
rue(A) :- stumble(A).
valid(S,T,B) :- setting(S), trouble(T), burden(B), affords(S,T), risky(B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if t.keyword:
            lines.append(asp.fact("keyword", tid, t.keyword))
    for bid, b in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        if b.region == "back":
            lines.append(asp.fact("back", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.trouble} at {p.setting} (burden: {p.burden})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
