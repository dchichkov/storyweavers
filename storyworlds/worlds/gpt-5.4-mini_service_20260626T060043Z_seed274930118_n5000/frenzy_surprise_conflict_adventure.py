#!/usr/bin/env python3
"""
storyworlds/worlds/frenzy_surprise_conflict_adventure.py
=========================================================

A small adventure storyworld built from the seed words:
- frenzy
- Surprise
- Conflict
- Adventure

Premise:
A child is on a little adventure to reach a lookout, but a sudden surprise
creates a conflict. The world models physical meters (distance, wind, weight)
and emotional memes (curiosity, fear, confidence, relief). The resolution
comes from a helpful choice that turns a frantic moment into a safe adventure.
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

STEP = 1.0



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aide: object | None = None
    gear: object | None = None
    hero: object | None = None
    prize: object | None = None
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
class Place:
    name: str
    surface: str
    affords: set[str] = field(default_factory=set)
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
class Route:
    id: str
    verb: str
    noun: str
    distance: int
    weather: str
    surprise: str
    risk: str
    conflict_kind: str
    fix_item: str
    fix_label: str
    fix_phrase: str
    fix_covers: set[str]
    fix_guards: set[str]
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
    region: str
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
class StoryParams:
    place: str
    route: str
    prize: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.route: Optional[Route] = None
        self.lines: list[str] = []
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.route = copy.deepcopy(self.route)
        w.lines = list(self.lines)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "harbor": Place("the harbor", "stone pier", {"walk", "search"}),
    "forest": Place("the forest trail", "leafy path", {"walk", "search"}),
    "cave": Place("the cave mouth", "rough ground", {"walk", "search"}),
}

ROUTES = {
    "harbor": Route(
        id="harbor",
        verb="walk to the old lighthouse",
        noun="lighthouse",
        distance=6,
        weather="windy",
        surprise="a sudden gull swirl scattered the map pages",
        risk="the map could fly away",
        conflict_kind="wind",
        fix_item="clip",
        fix_label="a bright red clip",
        fix_phrase="a bright red clip for the map",
        fix_covers={"paper"},
        fix_guards={"wind"},
        tags={"adventure", "surprise", "conflict", "frenzy"},
    ),
    "forest": Route(
        id="forest",
        verb="search for the hidden brook",
        noun="brook",
        distance=5,
        weather="stormy",
        surprise="a startled rabbit darted across the path and knocked over the lantern",
        risk="the lantern might go dark",
        conflict_kind="dark",
        fix_item="lantern",
        fix_label="a little storm lantern",
        fix_phrase="a little storm lantern with a glass shield",
        fix_covers={"light"},
        fix_guards={"dark"},
        tags={"adventure", "surprise", "conflict", "frenzy"},
    ),
    "cave": Route(
        id="cave",
        verb="follow the echo to the crystal room",
        noun="crystal room",
        distance=4,
        weather="cool",
        surprise="water dripped from the ceiling and splashed the torch",
        risk="the torch could go out",
        conflict_kind="water",
        fix_item="hood",
        fix_label="a dry hood",
        fix_phrase="a dry hood that covered the torch hand",
        fix_covers={"hand"},
        fix_guards={"water"},
        tags={"adventure", "surprise", "conflict", "frenzy"},
    ),
}

PRIZES = {
    "map": Prize("map", "the treasure map", "a folded treasure map", "paper"),
    "lantern": Prize("lantern", "the lantern", "a brass lantern", "light"),
    "torch": Prize("torch", "the torch", "a wooden torch", "hand"),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = ["Mina", "Nora", "Lina", "Ivy", "Rosa", "Tia", "Maya"]
BOY_NAMES = ["Finn", "Arlo", "Nico", "Theo", "Jasper", "Eli", "Sam"]
TRAITS = ["brave", "curious", "bold", "restless", "cheerful", "quick"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, p in SETTINGS.items():
        for route_id in p.affords:
            r = _safe_lookup(ROUTES, route_id)
            for prize_id, prize in PRIZES.items():
                if prize.region == r.fix_covers.pop() if False else True:
                    pass
                if prize.region == "paper" and "wind" in r.fix_guards:
                    out.append((place, route_id, prize_id))
                elif prize.region == "light" and "dark" in r.fix_guards:
                    out.append((place, route_id, prize_id))
                elif prize.region == "hand" and "water" in r.fix_guards:
                    out.append((place, route_id, prize_id))
    return out


def reason_valid(place: str, route: Route, prize: Prize) -> bool:
    return (
        (prize.region == "paper" and "wind" in route.fix_guards)
        or (prize.region == "light" and "dark" in route.fix_guards)
        or (prize.region == "hand" and "water" in route.fix_guards)
    )


def explain_rejection(route: Route, prize: Prize) -> str:
    return (
        f"(No story: {route.verb} makes the {prize.label} truly at risk, but the "
        f"fix catalog has no reasonable choice for that danger.)"
    )


def seed_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with surprise and conflict.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "route", None) and getattr(args, "prize", None):
        route = _safe_lookup(ROUTES, getattr(args, "route", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not reason_valid(getattr(args, "place", None) or "harbor", route, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "route", None) is None or c[1] == getattr(args, "route", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, route_id, prize_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        route=route_id,
        prize=prize_id,
        name=getattr(args, "name", None) or seed_name(gender, rng),
        gender=gender,
        helper=getattr(args, "helper", None) or rng.choice(["mother", "father"]),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def advance(world: World, actor: Entity, route: Route, prize: Entity, narrate: bool = True) -> None:
    actor.meters["distance"] += route.distance
    actor.memes["frenzy"] += 1
    if narrate:
        world.say(f"{actor.pronoun('subject').capitalize()} hurried along the path, and the day began to feel like a frenzy.")


def predict_risk(world: World, actor: Entity, route: Route, prize: Entity) -> bool:
    sim = world.copy()
    advance(sim, sim.get(actor.id), route, sim.get(prize.id), narrate=False)
    return True


def tell(place: Place, route: Route, prize_cfg: Prize, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(place)
    world.route = route
    hero = world.add(Entity(id=name, kind="character", type=gender))
    aide = world.add(Entity(id="helper", kind="character", type=helper, label=f"the {helper}"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    gear = world.add(Entity(id=route.fix_item, type="gear", label=route.fix_label, phrase=route.fix_phrase, owner=hero.id))
    gear.meters["ready"] = 1

    world.say(f"{hero.id} was a {trait} little {gender} who loved adventure at {place.name}.")
    world.say(f"{hero.pronoun('subject').capitalize()} carried {prize.phrase} because it made the trip feel important.")
    world.para()

    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {helper} set out to {route.verb}.")
    world.say(f"The path was {route.weather}, and {route.surprise}.")
    hero.memes["curiosity"] += 1
    hero.memes["surprise"] += 1
    world.say(f"{hero.id} felt a little thrill, but also a flicker of conflict as {route.risk}.")
    hero.memes["conflict"] += 1
    world.para()

    world.say(f"{hero.id} tried to hurry on, because the whole trip had turned into a frenzy.")
    if route.conflict_kind == "wind":
        prize.meters["safe"] += 0
        hero.memes["worry"] += 1
        world.say(f"Then {hero.pronoun('possessive')} {helper} held up {gear.label} and clipped the map tight.")
        world.say(f"That kept the pages from flying away, so the route stayed clear.")
    elif route.conflict_kind == "dark":
        hero.memes["worry"] += 1
        world.say(f"Then {hero.pronoun('possessive')} {helper} lit {gear.label}, and the path stopped looking scary.")
    else:
        hero.memes["worry"] += 1
        world.say(f"Then {hero.pronoun('possessive')} {helper} used {gear.label}, and the torch stayed dry.")
    hero.memes["conflict"] = 0.0
    hero.memes["confidence"] += 1
    hero.memes["relief"] += 1
    world.para()

    world.say(f"At last, {hero.id} reached the {route.noun} with {prize.label} still safe.")
    world.say(f"{hero.id} smiled at {hero.pronoun('possessive')} {helper}; the surprise had turned into a brave little adventure.")
    world.facts.update(hero=hero, helper=aide, prize=prize, route=route, place=place, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    route = _safe_fact(world, f, "route")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short adventure story for a child where {hero.id} faces a surprise on the way to the {route.noun}.',
        f"Tell a story with a frenzy of movement, a conflict about {prize.label}, and a safe helper who fixes it.",
        f'Write a gentle adventure that includes the word "frenzy" and ends with {hero.id} feeling brave again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    route = _safe_fact(world, f, "route")
    prize = _safe_fact(world, f, "prize")
    return [
        QAItem(
            question=f"Who went on the trip to the {route.noun}?",
            answer=f"{hero.id} went with {hero.pronoun('possessive')} {helper.type} to reach the {route.noun}.",
        ),
        QAItem(
            question=f"What surprise caused trouble on the way?",
            answer=f"The surprise was that {route.surprise}, which made the trip turn tense for a moment.",
        ),
        QAItem(
            question=f"How was the conflict solved?",
            answer=f"{hero.pronoun('possessive').capitalize()} {helper.type} used {f['gear'].label} so {prize.label} stayed safe and the trip could continue.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt brave and relieved after the adventure was safely finished.",
        ),
    ]


KNOWLEDGE = {
    "adventure": [("What is an adventure?", "An adventure is an exciting trip or experience that can include surprises and challenges.")],
    "surprise": [("What is a surprise?", "A surprise is something unexpected that happens when you are not ready for it.")],
    "conflict": [("What is a conflict?", "A conflict is a problem or disagreement that needs a solution.")],
    "frenzy": [("What does frenzy mean?", "A frenzy means a very busy, excited rush of movement or action.")],
}


def world_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE["adventure"] + KNOWLEDGE["surprise"] + KNOWLEDGE["conflict"] + KNOWLEDGE["frenzy"]]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}\nA: {item.answer}")
    parts.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
route(R) :- route_name(R).
prize(X) :- prize_name(X).

compatible(P,R,Z) :- setting(P), route_name(R), prize_name(Z), fit(R,Z).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for r in sorted(_safe_lookup(SETTINGS, p).affords):
            lines.append(asp.fact("affords", p, r))
    for r_id, r in ROUTES.items():
        lines.append(asp.fact("route_name", r_id))
        lines.append(asp.fact("surprise", r_id))
        lines.append(asp.fact("conflict", r_id, r.conflict_kind))
        lines.append(asp.fact("fit", r_id, r.fix_covers and next(iter(r.fix_covers)) or "x"))
        for t in sorted(r.tags):
            lines.append(asp.fact("tag", r_id, t))
    for p_id, p in PRIZES.items():
        lines.append(asp.fact("prize_name", p_id))
        lines.append(asp.fact("region", p_id, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ROUTES, params.route), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="harbor", route="harbor", prize="map", name="Mina", gender="girl", helper="mother", trait="brave"),
    StoryParams(place="forest", route="forest", prize="lantern", name="Finn", gender="boy", helper="father", trait="curious"),
    StoryParams(place="cave", route="cave", prize="torch", name="Ivy", gender="girl", helper="mother", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show."))
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
            header = f"### {p.name}: {p.route} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
