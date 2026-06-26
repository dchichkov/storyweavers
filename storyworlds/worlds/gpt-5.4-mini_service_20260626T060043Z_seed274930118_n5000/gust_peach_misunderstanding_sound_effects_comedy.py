#!/usr/bin/env python3
"""
A small comedy storyworld about a gust, a peach, and a noisy misunderstanding.

A seed tale is imagined first:
- A child carries a ripe peach to a picnic.
- A sudden gust makes a funny sound and blows the napkin away.
- Everyone misunderstands the situation and thinks the peach itself made the noise.
- They discover the real cause, laugh, and use a lid and a bowl to keep the peach safe.

The simulated world tracks:
- physical meters: windblown, exposed, safe, dropped, intact
- emotional memes: confusion, worry, embarrassment, amusement, relief

The narrative is state-driven: the gust changes physical exposure, the sound effects
cause confusion, and the ending proves the peach stayed safe after a comic fix.
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


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------


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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Place:
    id: str
    label: str
    indoor: bool
    affordances: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    protected: bool = False
    covers: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Beat:
    id: str
    name: str
    sound: str
    effect: str
    risk: str
    fix: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str
    beat: str
    prop: str
    name: str
    helper: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


PLACES = {
    "picnic": Place(id="picnic", label="the picnic table", indoor=False, affordances={"gust", "peach"}),
    "porch": Place(id="porch", label="the porch", indoor=False, affordances={"gust", "peach"}),
    "kitchen": Place(id="kitchen", label="the kitchen", indoor=True, affordances={"peach"}),
    "market": Place(id="market", label="the little market stall", indoor=False, affordances={"gust", "peach"}),
}

BEATS = {
    "napkin_whirl": Beat(
        id="napkin_whirl",
        name="napkin whirl",
        sound="whoooosh",
        effect="the napkin flew up and fluttered like a surprised bird",
        risk="the peach was left exposed",
        fix="they put the peach in a bowl with a lid",
        tags={"gust", "sound"},
    ),
    "basket_tap": Beat(
        id="basket_tap",
        name="basket tap",
        sound="tap-tap-pop",
        effect="the basket rattled and everyone looked at the peach",
        risk="the peach might tumble out",
        fix="they tucked the peach under a cloth",
        tags={"gust", "sound"},
    ),
    "windy_boop": Beat(
        id="windy_boop",
        name="windy boop",
        sound="boop-BOOO",
        effect="the wind made a silly moan through a paper bag",
        risk="the peach rolled close to the edge",
        fix="they set the peach into a deep dish",
        tags={"gust", "sound"},
    ),
}

PROPS = {
    "peach": Prop(id="peach", label="peach", phrase="a ripe peach", kind="fruit"),
    "bowl": Prop(id="bowl", label="bowl", phrase="a sturdy bowl", kind="dish", protected=True, covers={"fruit"}),
    "lid": Prop(id="lid", label="lid", phrase="a smooth little lid", kind="cover", protected=True, covers={"fruit"}),
    "cloth": Prop(id="cloth", label="cloth", phrase="a clean kitchen cloth", kind="cover", protected=True, covers={"fruit"}),
    "dish": Prop(id="dish", label="dish", phrase="a deep dish", kind="dish", protected=True, covers={"fruit"}),
}

NAMES = ["Mia", "Noah", "Lena", "Owen", "Tia", "Ben", "Ava", "Leo"]
HELPERS = ["mom", "dad", "grandma", "grandpa", "older sister", "older brother"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None
    covered_by: Optional[str] = None
    exposed: bool = False

    cover: object | None = None
    helper: object | None = None
    hero: object | None = None
    peach: object | None = None
    def __post_init__(self) -> None:
        for key in ("windblown", "safe", "dropped", "intact"):
            self.meters.setdefault(key, 0.0)
        for key in ("confusion", "worry", "embarrassment", "amusement", "relief"):
            self.memes.setdefault(key, 0.0)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, place: Place, beat: Beat) -> None:
        self.place = place
        self.beat = beat
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.soundlines: list[str] = []

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
        clone = World(self.place, self.beat)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def pronoun(name: str, case: str = "subject") -> str:
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def _gust_confusion(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    peach = world.get("peach")
    if hero.meters["windblown"] < 1:
        return out
    sig = ("confusion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["confusion"] += 1
    hero.memes["worry"] += 1
    world.facts["misunderstanding"] = True
    out.append("Everyone paused, because the gust sounded suspiciously like a tiny trumpet.")
    if peach.exposed:
        out.append("The peach sat there looking innocent, which somehow made it look even guiltier.")
    return out


def _safe_fix(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    peach = world.get("peach")
    cover = world.entities.get("cover")
    if not cover or not cover.covered_by:
        return out
    if ("safe",) in world.fired:
        return out
    if peach.exposed:
        return out
    world.fired.add(("safe",))
    peach.meters["safe"] += 1
    peach.meters["intact"] += 1
    hero.memes["amusement"] += 1
    hero.memes["relief"] += 1
    hero.memes["confusion"] = 0.0
    out.append("Once the lid snapped on, the mystery calmed down at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_gust_confusion, _safe_fix):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity, peach: Entity) -> None:
    world.say(
        f"{hero.label} was carrying {peach.label} to {world.place.label} with {helper.label} beside {pronoun(hero.id, 'object')}."
    )
    world.say(
        f"{hero.label} loved how shiny and round {pronoun(hero.id, 'possessive')} {peach.label} looked in the sun."
    )


def gust_blast(world: World, hero: Entity, peach: Entity) -> None:
    hero.meters["windblown"] += 1
    peach.exposed = True
    world.say(
        f"Then a gust went {world.beat.sound}! {world.beat.effect}."
    )
    world.say(
        f"That made {hero.label} blink and say, \"Did the {peach.label} make that noise?\""
    )
    propagate(world, narrate=True)


def misunderstanding(world: World, hero: Entity, helper: Entity, peach: Entity) -> None:
    hero.memes["confusion"] += 1
    helper.memes["confusion"] += 1
    helper.memes["amusement"] += 1
    world.say(
        f"{helper.label} stared at the {peach.label} and said, \"I don't think peaches usually go {world.beat.sound}.\""
    )
    world.say(
        f"{hero.label} looked even more puzzled, because {world.beat.risk}."
    )


def fix(world: World, hero: Entity, helper: Entity, peach: Entity) -> None:
    cover = Entity(
        id="cover",
        kind="container",
        label="lid",
        covered_by="bowl",
        exposed=False,
    )
    world.add(cover)
    world.say(
        f"Then {helper.label} laughed and said, \"Nope, the gust was the noisy one.\""
    )
    world.say(
        f"They used {world.beat.fix}."
    )
    peach.exposed = False
    peach.meters["safe"] += 1
    peach.meters["intact"] += 1
    cover.covered_by = "bowl"
    propagate(world, narrate=True)
    world.say(
        f"After that, the {peach.label} stayed safe, and everybody laughed at the very dramatic wind."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for young children about a gust, a peach, and a misunderstanding at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place_label")}.',
        f"Tell a comedy where a child thinks a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fruit")} caused a silly sound, but the real trouble was a gust.",
        f'Write a short, child-friendly story that includes "{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sound")}" and ends with laughter and a safe peach.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero_name")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper_label")
    peach = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fruit")
    beat = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "beat_name")
    return [
        QAItem(
            question=f"What did {hero} think made the noise at first?",
            answer=f"{hero} first thought the {peach} made the noise, because the gust sounded so strange and surprising.",
        ),
        QAItem(
            question=f"Why did {helper} laugh during the misunderstanding?",
            answer=f"{helper} laughed because the real noisy thing was the gust, not the {peach}, and the whole mistake was silly.",
        ),
        QAItem(
            question=f"What did they use to keep the {peach} safe in the end?",
            answer=f"They used {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fix_text")} so the {peach} would stay covered and safe after {beat}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {peach} safe, the wind being blamed for the noise, and everyone laughing at the joke of it all.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "gust": [
        QAItem(
            question="What is a gust?",
            answer="A gust is a short burst of wind that can make leaves, paper, and napkins blow around quickly.",
        )
    ],
    "peach": [
        QAItem(
            question="What kind of fruit is a peach?",
            answer="A peach is a soft, juicy fruit with fuzzy skin and a sweet taste.",
        )
    ],
    "sound": [
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are noises that help tell what is happening, like whooshes, taps, or pops.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think something is true, but they have guessed wrong.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a story feel like comedy?",
            answer="A comedy story makes people smile or laugh, often because something funny or surprising goes wrong and then gets fixed.",
        )
    ],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts.get("tags", []))
    out: list[QAItem] = []
    for key in ("gust", "peach", "sound", "misunderstanding", "comedy"):
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A gust can expose a fruit if it happens at a place that allows gust stories.
gust_story(P, B, F) :- place(P), beat(B), fruit(F), affords(P, gust), affords(P, peach).

% The misunderstanding happens when the hero attributes the sound to the peach.
misunderstanding(P, B, F) :- gust_story(P, B, F), sound_of(B, S), suspicious(F), confusing(S).

% A fix is reasonable if there is a container or cover for fruit.
fix(P, B, F) :- gust_story(P, B, F), cover(C), protects(C, fruit), fruit(F).

% A valid story needs both the misunderstanding and the fix.
valid(P, B, F) :- misunderstanding(P, B, F), fix(P, B, F).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, a))
    for bid, beat in BEATS.items():
        lines.append(asp.fact("beat", bid))
        lines.append(asp.fact("sound_of", bid, beat.sound))
        lines.append(asp.fact("confusing", beat.sound))
    for fid in PROPS:
        lines.append(asp.fact("fruit", fid) if fid == "peach" else asp.fact("cover", fid))
    for cid in ("bowl", "lid", "cloth", "dish"):
        lines.append(asp.fact("cover", cid))
        lines.append(asp.fact("protects", cid, "fruit"))
    lines.append(asp.fact("suspicious", "peach"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for beat in BEATS.values():
            if "gust" not in place.affordances or "peach" not in place.affordances:
                continue
            for prop in PROPS.values():
                if prop.id != "peach":
                    continue
                if any(p.protected and "fruit" in p.covers for p in PROPS.values() if p.id != "peach"):
                    combos.append((place.id, beat.id, prop.id))
    return combos


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    beat = _safe_lookup(BEATS, params.beat)
    world = World(place, beat)

    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", label=params.helper))
    peach = world.add(Entity(id="peach", kind="thing", label="the peach", owner=hero.id))
    world.facts.update(
        hero_name=params.name,
        helper_label=params.helper,
        fruit="peach",
        beat_name=beat.sound,
        place_label=place.label,
        fix_text=beat.fix,
        tags={"gust", "peach", "sound", "misunderstanding", "comedy"},
    )

    introduce(world, hero, helper, peach)
    world.para()
    gust_blast(world, hero, peach)
    misunderstanding(world, hero, helper, peach)
    world.para()
    fix(world, hero, helper, peach)
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy world: gust, peach, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--beat", choices=BEATS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if getattr(args, "prop", None) and getattr(args, "prop", None) != "peach":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    beat = getattr(args, "beat", None) or rng.choice(list(BEATS))
    prop = "peach"
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, beat=beat, prop=prop, name=name, helper=helper)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.kind:9}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for p, b, f in combos:
            print(f"  {p:8} {b:12} {f}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="picnic", beat="napkin_whirl", prop="peach", name="Mia", helper="mom"),
            StoryParams(place="porch", beat="basket_tap", prop="peach", name="Noah", helper="dad"),
            StoryParams(place="market", beat="windy_boop", prop="peach", name="Lena", helper="grandma"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
