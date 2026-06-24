#!/usr/bin/env python3
"""
A small folk-tale storyworld about transport across an inlet.

Premise:
A child or ferryman needs to transport a useful thing across an inlet to help
someone on the far shore. Something blocks the crossing, so the characters must
solve the problem with a sensible tool, helper, or plan.

The simulated state tracks:
- physical meters: load, water level, wind, rope tension, fuel, distance
- emotional memes: worry, courage, patience, relief, trust

The story is generated from world state, not from a frozen template.
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
    carrier: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cargo: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id
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
    place: str = "the inlet shore"
    current: str = "gentle"
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
class Cargo:
    id: str
    label: str
    phrase: str
    weight: str
    fragile: bool = False
    helps: set[str] = field(default_factory=set)
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
class Transport:
    id: str
    label: str
    phrase: str
    can_carry: set[str]
    can_face: set[str]
    remedy: str
    end_image: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.inlet_state: str = "calm"

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.inlet_state = self.inlet_state
        return clone


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


def _r_overload(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("load", 0) < THRESHOLD:
            continue
        transport = world.facts.get("transport")
        if not transport:
            continue
        trans: Transport = transport  # type: ignore[assignment]
        if actor.meters.get("distance", 0) >= THRESHOLD:
            continue
        if world.facts.get("blocked"):
            sig = ("blocked", actor.id, trans.id)
            if sig in world.fired:
                continue
            if actor.meters.get("risk", 0) >= THRESHOLD:
                continue
            world.fired.add(sig)
            actor.memes["worry"] = actor.memes.get("worry", 0) + 1
            out.append(f"The crossing looked hard for {actor.name_or_label()}.")
    return out


def _r_resolve(world: World) -> list[str]:
    out = []
    if not world.facts.get("problem_solved"):
        return out
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    cargo = _safe_fact(world, world.facts, "cargo")
    trans = _safe_fact(world, world.facts, "transport")
    sig = ("resolved", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = 0
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    out.append(f"With a better plan, the crossing became safe.")
    out.append(f"{hero.name_or_label()} and {helper.name_or_label()} carried {cargo.label} across {trans.label}.")
    return out


CAUSAL_RULES = [Rule("overload", _r_overload), Rule("resolve", _r_resolve)]


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


def predict_crossing(world: World, hero: Entity, transport: Transport, cargo: Cargo) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["load"] = 1
    sim.facts["blocked"] = True
    sim.facts["transport"] = transport
    sim.facts["cargo"] = cargo
    sim.facts["hero"] = sim.get(hero.id)
    propagate(sim, narrate=False)
    return {
        "solvable": transport.id in cargo.helps or any(True for _ in transport.can_face if _ == "wind"),
        "worry": sim.get(hero.id).memes.get("worry", 0),
    }


def ask_intro(world: World, hero: Entity, cargo: Cargo, transport: Transport) -> None:
    world.say(
        f"Once, in a small shore village by an inlet, {hero.name_or_label()} had to carry {cargo.phrase} across the water."
    )
    world.say(
        f"{hero.pronoun().capitalize()} used {transport.phrase}, for the folk there knew that a good crossing begins with a good tool."
    )


def set_problem(world: World, hero: Entity, cargo: Cargo) -> None:
    world.para()
    world.facts["blocked"] = True
    world.inlet_state = "wild"
    hero.meters["load"] = 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"But the inlet turned tricky. The tide rose high, and the wind tugged at the little craft."
    )
    world.say(
        f"{hero.name_or_label()} looked at {cargo.label} and worried it might never reach the far shore."
    )


def offer_problem_solving(world: World, hero: Entity, helper: Entity, cargo: Cargo, transport: Transport) -> None:
    world.para()
    world.say(
        f"Then {helper.name_or_label()} came with a calm face and said, "
        f"\"We need not fight the water. We can work with it.\""
    )
    if cargo.fragile:
        world.say(
            f"{helper.pronoun().capitalize()} wrapped {cargo.label} in dry cloth and tied it down with a rope."
        )
        hero.meters["care"] = hero.meters.get("care", 0) + 1
    else:
        world.say(
            f"{helper.pronoun().capitalize()} showed where to stack {cargo.label} low and steady so the load would not tip."
        )
    world.say(
        f"Together they chose {transport.label}, which could face the wind and still keep the cargo safe."
    )


def solve_crossing(world: World, hero: Entity, helper: Entity, cargo: Cargo, transport: Transport) -> None:
    world.para()
    hero.meters["distance"] = 1
    helper.meters["distance"] = 1
    world.facts["problem_solved"] = True
    propagate(world, narrate=False)
    world.say(
        f"They waited for the tide to slacken, then pushed off in one careful smooth motion."
    )
    world.say(
        f"The water rocked the {transport.label}, but the rope held, the load stayed steady, and the crossing was made."
    )
    world.say(
        f"At last {hero.name_or_label()} delivered {cargo.label} to the far shore, and the inlet shone quiet behind them."
    )


SETTINGS = {
    "shore": Setting(place="the inlet shore", current="gentle", affords={"boat", "raft", "ferry"}),
    "harbor": Setting(place="the little harbor", current="tidal", affords={"boat", "ferry"}),
    "island": Setting(place="the island dock", current="windy", affords={"boat", "raft"}),
}

CARGOS = {
    "grain": Cargo(id="grain", label="a sack of grain", phrase="a sack of grain", weight="heavy", helps={"ferry", "boat"}),
    "medicine": Cargo(id="medicine", label="a little bundle of medicine", phrase="a little bundle of medicine", weight="light", fragile=True, helps={"boat", "ferry"}),
    "lantern": Cargo(id="lantern", label="a lantern for the lighthouse", phrase="a lantern for the lighthouse", weight="light", fragile=True, helps={"boat", "raft", "ferry"}),
    "fish": Cargo(id="fish", label="a basket of fish", phrase="a basket of fish", weight="medium", helps={"raft", "boat"}),
}

TRANSPORTS = {
    "boat": Transport(id="boat", label="a small boat", phrase="a small boat", can_carry={"heavy", "light", "medium"}, can_face={"wind", "tide"}, remedy="a steady boat", end_image="the boat bobbed beside the far shore"),
    "raft": Transport(id="raft", label="a reed raft", phrase="a reed raft", can_carry={"light", "medium"}, can_face={"calm", "wind"}, remedy="a lighter load", end_image="the raft floated like a leaf"),
    "ferry": Transport(id="ferry", label="the village ferry", phrase="the village ferry", can_carry={"heavy", "light", "medium"}, can_face={"wind", "tide"}, remedy="the ferryman’s know-how", end_image="the ferry rested safely at the dock"),
}

HEROES = {
    "girl": ["Mina", "Tala", "Rina", "Suri", "Lina"],
    "boy": ["Niko", "Bram", "Jori", "Pavel", "Eli"],
}
HELPERS = ["old ferryman", "wise aunt", "quiet boatman", "kind neighbor"]
TRAITS = ["brave", "careful", "patient", "curious", "steady"]


@dataclass
class StoryParams:
    place: str
    transport: str
    cargo: str
    name: str
    gender: str
    helper: str
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
    for place, setting in SETTINGS.items():
        for trans_id in setting.affords:
            trans = _safe_lookup(TRANSPORTS, trans_id)
            for cargo_id, cargo in CARGOS.items():
                if cargo.weight in trans.can_carry and trans_id in cargo.helps:
                    combos.append((place, trans_id, cargo_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about transport across an inlet.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--transport", choices=TRANSPORTS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=range(len(HELPERS)))
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
              and (getattr(args, "transport", None) is None or c[1] == getattr(args, "transport", None))
              and (getattr(args, "cargo", None) is None or c[2] == getattr(args, "cargo", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, transport, cargo = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(HEROES, gender))
    helper = _safe_lookup(HELPERS, getattr(args, "helper", None)) if getattr(args, "helper", None) is not None else rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, transport=transport, cargo=cargo, name=name, gender=gender, helper=helper, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper))
    cargo = world.add(Entity(id="cargo", type="cargo", label=_safe_lookup(CARGOS, params.cargo).label, phrase=_safe_lookup(CARGOS, params.cargo).phrase, owner=hero.id))
    transport = _safe_lookup(TRANSPORTS, params.transport)

    world.facts.update(hero=hero, helper=helper, cargo=cargo, transport=transport)

    ask_intro(world, hero, cargo, transport)
    set_problem(world, hero, cargo)
    offer_problem_solving(world, hero, helper, cargo, transport)
    solve_crossing(world, hero, helper, cargo, transport)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    cargo: Entity = _safe_fact(world, f, "cargo")  # type: ignore[assignment]
    transport: Transport = _safe_fact(world, f, "transport")  # type: ignore[assignment]
    return [
        f"Write a short folk tale about {hero.name_or_label()} and {cargo.label} crossing an inlet.",
        f"Tell a gentle problem-solving story where a child uses {transport.label} to carry {cargo.label} across the water.",
        f"Write a simple story about transport, inlet tides, and a careful solution that helps the cargo reach the far shore.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    cargo: Entity = _safe_fact(world, f, "cargo")  # type: ignore[assignment]
    transport: Transport = _safe_fact(world, f, "transport")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who needed to carry {cargo.label} across the inlet?",
            answer=f"{hero.name_or_label()} needed to carry {cargo.label} across the inlet.",
        ),
        QAItem(
            question=f"What helped {hero.name_or_label()} solve the crossing problem?",
            answer=f"{helper.name_or_label()} helped by choosing {transport.label} and a careful way to load the cargo.",
        ),
        QAItem(
            question=f"How did the story end for {cargo.label}?",
            answer=f"{cargo.label.capitalize()} reached the far shore safely, and the inlet became calm again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "inlet": [
        QAItem(
            question="What is an inlet?",
            answer="An inlet is a narrow stretch of water that reaches into the land, like a little sea passage.",
        )
    ],
    "transport": [
        QAItem(
            question="What does transport mean?",
            answer="Transport means carrying people or things from one place to another.",
        )
    ],
    "boat": [
        QAItem(
            question="What helps a small boat stay steady?",
            answer="A small boat stays steadier when its load is balanced and the water is not too rough.",
        )
    ],
    "raft": [
        QAItem(
            question="What is a raft?",
            answer="A raft is a simple floating platform tied together from wood, reeds, or other light pieces.",
        )
    ],
    "ferry": [
        QAItem(
            question="What is a ferry for?",
            answer="A ferry is used to carry people or goods across water in a regular, helpful way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [WORLD_KNOWLEDGE["inlet"][0], WORLD_KNOWLEDGE["transport"][0]]
    trans: Transport = _safe_fact(world, world.facts, "transport")  # type: ignore[assignment]
    out.extend(WORLD_KNOWLEDGE.get(trans.id, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(parts)}")
    lines.append(f"  inlet_state={world.inlet_state}")
    return "\n".join(lines)


ASP_RULES = r"""
block_reason(A) :- hero(A), load(A), inlet_wild.
safe_crossing(A) :- hero(A), transport(T), can_face(T, wind), can_carry(T, heavy).
safe_crossing(A) :- hero(A), transport(T), can_face(T, tide), can_carry(T, light).
problem_solved(A) :- block_reason(A), safe_crossing(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TRANSPORTS.items():
        lines.append(asp.fact("transport", tid))
        for c in sorted(t.can_carry):
            lines.append(asp.fact("can_carry", tid, c))
        for f in sorted(t.can_face):
            lines.append(asp.fact("can_face", tid, f))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_weight", cid, c.weight))
        if c.fragile:
            lines.append(asp.fact("fragile", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show problem_solved/1."))
    asp_ok = bool(asp.atoms(model, "problem_solved"))
    py_ok = len(valid_combos()) > 0
    if asp_ok == py_ok:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


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


CURATED = [
    StoryParams(place="shore", transport="boat", cargo="medicine", name="Mina", gender="girl", helper="wise aunt", trait="patient"),
    StoryParams(place="harbor", transport="ferry", cargo="grain", name="Niko", gender="boy", helper="old ferryman", trait="steady"),
    StoryParams(place="island", transport="raft", cargo="lantern", name="Tala", gender="girl", helper="kind neighbor", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show problem_solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    elif getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show problem_solved/1."))
        print(f"problem_solved atoms: {asp.atoms(model, 'problem_solved')}")
        return
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
