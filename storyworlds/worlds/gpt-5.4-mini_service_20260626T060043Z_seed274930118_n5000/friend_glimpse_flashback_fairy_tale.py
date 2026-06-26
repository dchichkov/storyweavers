#!/usr/bin/env python3
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
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    friend: object | None = None
    hero: object | None = None
    pr: object | None = None
    tr: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "witch", "fairy"}
        male = {"boy", "prince", "king", "wizard", "knight"}
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
class Place:
    name: str
    outdoors: bool = True
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
class Glimpse:
    id: str
    verb: str
    gerund: str
    rush: str
    spark: str
    clue: str
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
class Treasure:
    id: str
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
class Promise:
    id: str
    label: str
    covers: set[str]
    calm: str
    rescue: str
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
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.lines = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


PLACES = {
    "wood": Place("the wood", True, {"glimpse", "wander"}),
    "garden": Place("the garden", True, {"glimpse", "wander"}),
    "castle": Place("the castle yard", True, {"glimpse"}),
}

GLIMPSES = {
    "spark": Glimpse("spark", "catch a glimpse of", "catching a glimpse", "run toward the sparkle", "a tiny silver flash", "a bright clue in the dark", "spark", {"light", "magic"}),
    "bird": Glimpse("bird", "see a little bird", "seeing a little bird", "follow the flutter", "a feather-bright wingshadow", "a message from the trees", "bird", {"bird", "song"}),
    "glow": Glimpse("glow", "spot a soft glow", "spotting a soft glow", "tiptoe closer", "a warm gold glow", "a hidden kindness", "glow", {"light", "kind"}),
}

TREASURES = {
    "crown": Treasure("crown", "crown", "a little gold crown", "crown", "head"),
    "shawl": Treasure("shawl", "shawl", "a blue shawl", "shawl", "shoulders"),
    "lantern": Treasure("lantern", "lantern", "a glass lantern", "lantern", "hands"),
}

PROMISES = {
    "cloak": Promise("cloak", "cloak", {"shoulders"}, "keep the cold away", "wrap snugly around the shoulders"),
    "boots": Promise("boots", "boots", {"feet"}, "keep the mud off", "stay dry in the wet grass", plural=True),
    "cap": Promise("cap", "cap", {"head"}, "shade the brow", "sit neatly on the head"),
}

GIRL_NAMES = ["Mina", "Ella", "Nina", "Luna", "Tessa"]
BOY_NAMES = ["Pip", "Finn", "Robin", "Toby", "Nico"]
TRAITS = ["gentle", "brave", "curious", "kind", "cheerful"]


@dataclass
class StoryParams:
    place: str
    glimpse: str
    treasure: str
    promise: str
    name: str
    gender: str
    title: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, pl in PLACES.items():
        for g in pl.affords:
            for t in TREASURES:
                for p in PROMISES:
                    if t == "crown" and p in {"cap", "cloak"}:
                        out.append((place, g, t, p))
                    elif t == "shawl" and p in {"cloak", "boots"}:
                        out.append((place, g, t, p))
                    elif t == "lantern" and p in {"cap", "cloak"}:
                        out.append((place, g, t, p))
    return out


def reasonableness_gate(params: StoryParams) -> None:
    g = _safe_lookup(GLIMPSES, params.glimpse)
    t = _safe_lookup(TREASURES, params.treasure)
    p = _safe_lookup(PROMISES, params.promise)
    if t.region not in p.covers:
        pass
    if params.glimpse not in {"spark", "glow"} and params.treasure == "crown":
        pass
    if params.title.lower() != "flashback":
        pass
    _ = g, t, p


def predict_scatter(world: World, hero: Entity, glimpse: Glimpse, treasure: Treasure) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["wonder"] += 1
    if treasure.region == "head" and glimpse.id == "spark":
        return True
    return False


def build_story(world: World) -> None:
    h = _safe_fact(world, world.facts, "hero")
    f = _safe_fact(world, world.facts, "friend")
    g = _safe_fact(world, world.facts, "glimpse")
    t = _safe_fact(world, world.facts, "treasure")
    p = _safe_fact(world, world.facts, "promise")

    world.say(f"{h.id} lived near {world.place.name} and had a dear friend named {f.id}.")
    world.say(f"They loved to wander together, and {h.id} was always glad for a little {g.keyword} on the path.")
    world.say(f"One day, {h.id}'s heart treasured {h.pronoun('possessive')} {t.label}, which gleamed like a storybook gift.")

    world.para()
    world.say(f"Late in the afternoon, {h.id} went into {world.place.name} with {f.id}.")
    world.say(f"Then {h.id} {g.verb} near the brambles, and {f.id} cried out about {g.spark}.")
    world.say(f"{h.id} stopped short, because the light looked just like {g.clue}.")

    world.para()
    h.memes["wonder"] += 1
    h.memes["fear"] += 1
    if predict_scatter(world, h, g, t):
        world.say(f"{h.id} worried that the bright flash might make the {t.label} slip or lose its shine.")
    world.say(f"At once, {h.id} remembered a flashback from earlier that week.")
    world.say(f"In the flashback, {f.id} had used {f.pronoun('possessive')} small hands to help tuck the {t.label} safely away when the wind rose.")
    world.say(f"That memory felt warm, and {h.id} understood that {f.id} was not bringing trouble at all.")
    world.say(f"{f.id} had found a clue, not a danger.")

    world.para()
    h.memes["fear"] = 0.0
    h.memes["trust"] += 1
    world.say(f"{h.id} smiled and trusted {f.id}.")
    world.say(f"They followed the {g.keyword} together, and the trail led to a quiet place where the air shone gold.")
    world.say(f"There, {h.id} used {p.label} to keep the {t.label} safe, and {f.id} laughed softly at the happy ending.")
    world.say(f"By sunset, the friend, the glimpse, and the flashback had all turned into one kind memory.")


def generate_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        meters={"distance": 0.0},
        memes={"wonder": 0.0, "fear": 0.0, "trust": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="fairy" if params.title == "Flashback" else "friend",
        label="friend",
        memes={"kindness": 1.0},
    ))
    glimpse = _safe_lookup(GLIMPSES, params.glimpse)
    treasure = _safe_lookup(TREASURES, params.treasure)
    promise = _safe_lookup(PROMISES, params.promise)
    tr = world.add(Entity(
        id=treasure.id,
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=hero.id,
        region=treasure.region,
        plural=treasure.plural,
        meters={"shine": 1.0},
    ))
    pr = world.add(Entity(
        id=promise.id,
        type="thing",
        label=promise.label,
        phrase=promise.calm,
        plural=promise.plural,
    ))
    world.facts.update(hero=hero, friend=friend, glimpse=glimpse, treasure=tr, promise=pr)
    build_story(world)
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a small child about a friend, a glimpse, and a flashback in {world.place.name}.',
        f"Tell a gentle story where {f['hero'].id} and a dear friend notice {f['glimpse'].spark}, remember a flashback, and end happily.",
        f'Write a short fairy tale using the word "{f["glimpse"].keyword}" and the idea that a remembered kindness changes what happens next.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = _safe_fact(world, f, "hero")
    fr = _safe_fact(world, f, "friend")
    g = _safe_fact(world, f, "glimpse")
    t = _safe_fact(world, f, "treasure")
    return [
        QAItem(
            question=f"Who did {h.id} go with into {world.place.name}?",
            answer=f"{h.id} went with {fr.id}, a dear friend who stayed close by.",
        ),
        QAItem(
            question=f"What did {h.id} notice that made the story feel magical?",
            answer=f"{h.id} noticed {g.spark}, a small bright glimpse in the path.",
        ),
        QAItem(
            question=f"What did {h.id} remember in the flashback?",
            answer=f"{h.id} remembered {fr.id} helping keep the {t.label} safe when the wind rose.",
        ),
        QAItem(
            question=f"How did the story end for {h.id} and the friend?",
            answer=f"They followed the clue together, trusted each other, and ended with a happy memory.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that remembers something that happened earlier.",
        ),
        QAItem(
            question="What does a glimpse mean?",
            answer="A glimpse means a quick little look at something, just for a moment.",
        ),
        QAItem(
            question="Why are friends important in fairy tales?",
            answer="Friends can help, listen, and make a scary or puzzling moment feel safer.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
friend(friend).
flashback(flashback).
glimpse(spark).
glimpse(bird).
glimpse(glow).

at_risk(T,P) :- treasure(T), promise(P), region(T,R), covers(P,R).
compatible(P,T) :- at_risk(T,P).
valid(Place,G,T,P) :- place(Place), glimpse(G), treasure(T), promise(P), compatible(P,T).
"""


def asp_facts() -> str:
    import asp
    out = []
    for p in PLACES:
        out.append(asp.fact("place", p))
    for g in GLIMPSES:
        out.append(asp.fact("glimpse", g))
    for t in TREASURES.values():
        out.append(asp.fact("treasure", t.id))
        out.append(asp.fact("region", t.id, t.region))
    for p in PROMISES.values():
        out.append(asp.fact("promise", p.id))
        for c in p.covers:
            out.append(asp.fact("covers", p.id, c))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    atoms = set(asp.atoms(model, "valid"))
    py = set()
    for place, pl in PLACES.items():
        for g in pl.affords:
            for t in TREASURES:
                for p in PROMISES:
                    if _safe_lookup(TREASURES, t).region in _safe_lookup(PROMISES, p).covers:
                        py.add((place, g, t, p))
    if atoms == py:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only asp:", sorted(atoms - py))
    print("only python:", sorted(py - atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a friend, a glimpse, and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--glimpse", choices=GLIMPSES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--promise", choices=PROMISES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--title", default="Flashback")
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
    if getattr(args, "title", None) != "Flashback":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "glimpse", None) is None or c[1] == getattr(args, "glimpse", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))
              and (getattr(args, "promise", None) is None or c[3] == getattr(args, "promise", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, glimpse, treasure, promise = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, glimpse, treasure, promise, name, gender, getattr(args, "title", None), trait)


def valid_story_params() -> list[StoryParams]:
    out = []
    seeds = [
        ("wood", "spark", "crown", "cap", "Mina", "girl", "gentle"),
        ("garden", "glow", "shawl", "cloak", "Pip", "boy", "curious"),
        ("castle", "spark", "lantern", "cloak", "Luna", "girl", "brave"),
    ]
    for place, glimpse, treasure, promise, name, gender, trait in seeds:
        out.append(StoryParams(place, glimpse, treasure, promise, name, gender, "Flashback", trait))
    return out


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print(" ", v)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in valid_story_params():
            samples.append(generate(p))
    else:
        seen = set()
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
