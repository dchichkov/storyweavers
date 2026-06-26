#!/usr/bin/env python3
"""
storyworlds/worlds/waltz_inner_monologue_fable.py
=================================================

A small fable-style storyworld about a waltz, guided by a character's
inner monologue.

Premise:
- A small creature wants to dance the waltz at a lantern clearing.
- The creature worries that its clumsy steps will spoil the dance.
- A friend offers patient guidance.
- The creature chooses to listen inwardly, slow down, and find the rhythm.

The simulation tracks physical meters and emotional memes:
- meters: balance, sound, dust, shine
- memes: worry, courage, pride, kindness, patience

The narrative is driven by state changes rather than a frozen paragraph.
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
# Core entities
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gift: object | None = None
    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "hare", "fox", "rabbit"}:
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
class Place:
    id: str
    label: str
    indoors: bool
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Tune:
    id: str
    name: str
    mood: str
    tempo: str
    steps: str
    risk: str
    keyword: str = "waltz"
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
class Gift:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    worn_on: str = "paws"
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
class StoryParams:
    place: str
    tune: str
    gift: str
    name: str
    kind: str
    guide: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.tension: float = 0.0

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.tension = self.tension
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "clearing": Place(id="clearing", label="the moonlit clearing", indoors=False, affords={"waltz"}),
    "hall": Place(id="hall", label="the little hall", indoors=True, affords={"waltz"}),
    "porch": Place(id="porch", label="the porch", indoors=False, affords={"waltz"}),
}

TUNES = {
    "slow_waltz": Tune(
        id="slow_waltz",
        name="a slow waltz",
        mood="gentle",
        tempo="slow",
        steps="slow, round steps",
        risk="stumbling",
        tags={"music", "dance", "waltz"},
    ),
    "bright_waltz": Tune(
        id="bright_waltz",
        name="a bright waltz",
        mood="glad",
        tempo="lively",
        steps="three neat steps",
        risk="losing the beat",
        tags={"music", "dance", "waltz"},
    ),
}

GIFTS = {
    "ribbon": Gift(
        id="ribbon",
        label="a red ribbon",
        phrase="a soft red ribbon",
        helps={"steadiness"},
        worn_on="neck",
    ),
    "slippers": Gift(
        id="slippers",
        label="soft slippers",
        phrase="a pair of soft slippers",
        helps={"balance"},
        worn_on="paws",
        plural=True,
    ),
    "lamp": Gift(
        id="lamp",
        label="a little lamp",
        phrase="a tiny lamp for the dance path",
        helps={"confidence"},
    ),
}

NAMES = {
    "mouse": ["Milo", "Nina", "Pip", "Luna", "Toby", "Clover"],
    "hare": ["Hattie", "Juniper", "Bruno", "Mabel", "Otis", "Fern"],
    "fox": ["Fenn", "Rosie", "Galen", "Iris", "Rowan", "Violet"],
    "rabbit": ["Benny", "Pippa", "Soren", "Eliza", "Tansy", "Wren"],
}

KINDS = ["mouse", "hare", "fox", "rabbit"]
TRAITS = ["small", "timid", "earnest", "gentle", "careful", "spirited"]


# ---------------------------------------------------------------------------
# Reasonable world model
# ---------------------------------------------------------------------------
def can_risk(tune: Tune, gift: Gift) -> bool:
    return tune.keyword == "waltz" and ("balance" in gift.helps or "steadiness" in gift.helps or "confidence" in gift.helps)


def choose_gift(tune: Tune) -> Optional[Gift]:
    for gift in GIFTS.values():
        if can_risk(tune, gift):
            return gift
    return None


def inner_monologue(hero: Entity, tune: Tune) -> str:
    if hero.memes.get("worry", 0) >= 1:
        return (
            f"{hero.pronoun('subject').capitalize()} thought, "
            f'"If I rush, I may trip and spoil the waltz. If I listen, I may still learn."'
        )
    return (
        f"{hero.pronoun('subject').capitalize()} thought, "
        f'"I can hear the beat. I only need to trust my feet."'
    )


def predict_finish(world: World, hero: Entity, tune: Tune, gift: Gift) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.meters["balance"] += 1
    if "balance" in gift.helps:
        h.meters["balance"] += 1
    h.memes["worry"] = max(0, h.memes.get("worry", 0) - 1)
    h.memes["courage"] = h.memes.get("courage", 0) + 1
    return {
        "dance_ok": h.meters["balance"] >= 2,
        "calm": h.memes["worry"] <= 0,
    }


def reasonableness_gate(place: Place, tune: Tune, gift: Gift) -> bool:
    if "waltz" not in place.affords:
        return False
    return can_risk(tune, gift)


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, guide: Entity, tune: Tune, gift: Gift) -> None:
    world.say(
        f"{hero.id} was a {hero.meters.get('size_word', 0) or 'small'} {hero.type} "
        f"who loved the waltz."
    )
    world.say(
        f"At {world.place.label}, {guide.label} had brought {gift.phrase} for the dance."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(f"{hero.id} watched the gift and felt a little flutter of pride.")


def worry(world: World, hero: Entity, tune: Tune) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.tension += 1
    world.say(
        f"{hero.id} heard {tune.name} beginning and felt the beat in {hero.pronoun('possessive')} chest."
    )
    world.say(inner_monologue(hero, tune))


def advice(world: World, guide: Entity, hero: Entity, tune: Tune, gift: Gift) -> None:
    hero.memes["patience"] = hero.memes.get("patience", 0) + 1
    guide.memes["kindness"] = guide.memes.get("kindness", 0) + 1
    world.say(
        f"{guide.label} smiled and said, "
        f'"Slow steps can still be beautiful. The waltz is a friend to patient feet."'
    )
    world.say(f"{hero.id} looked down at {gift.label} and took one careful breath.")


def dance(world: World, hero: Entity, tune: Tune, gift: Gift) -> None:
    hero.meters["balance"] = hero.meters.get("balance", 0) + 1
    if "balance" in gift.helps:
        hero.meters["balance"] += 1
    hero.meters["sound"] = hero.meters.get("sound", 0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    if hero.meters["balance"] >= 2:
        hero.memes["worry"] = max(0, hero.memes.get("worry", 0) - 1)
    world.say(
        f"{hero.id} set {hero.pronoun('possessive')} paws to {tune.steps}."
    )
    world.say(
        f"The rhythm carried {hero.id} forward, and {hero.pronoun('subject')} did not fall."
    )


def resolution(world: World, hero: Entity, guide: Entity, tune: Tune, gift: Gift) -> None:
    state = predict_finish(world, hero, tune, gift)
    if not state["dance_ok"]:
        pass
    hero.memes["worry"] = 0
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    guide.memes["patience"] = guide.memes.get("patience", 0) + 1
    world.say(
        f"Before long, {hero.id} found the turn of the waltz and smiled at {hero.pronoun('possessive')} own surprise."
    )
    world.say(
        f"{guide.label} watched with warm eyes, and the little dance became a fine evening to remember."
    )


def tell(place: Place, tune: Tune, gift_cfg: Gift, hero_name: str, hero_kind: str, guide_kind: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_kind,
        meters={"balance": 0, "sound": 0},
        memes={"worry": 0, "courage": 0, "pride": 0, "patience": 0},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=guide_kind,
        label=f"the {guide_kind}",
        meters={},
        memes={"kindness": 0, "patience": 0},
    ))
    gift = world.add(Entity(
        id=gift_cfg.id,
        type="thing",
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        owner=hero.id,
        plural=gift_cfg.plural,
    ))
    hero.meters["size_word"] = 1

    hero.memes["worry"] = 1
    introduce(world, hero, guide, tune, gift)
    world.para()
    worry(world, hero, tune)
    advice(world, guide, hero, tune, gift)
    dance(world, hero, tune, gift)
    world.para()
    resolution(world, hero, guide, tune, gift)

    world.facts.update(hero=hero, guide=guide, gift=gift, tune=tune, place=place, trait=trait)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    tune = _safe_fact(world, f, "tune")
    gift = _safe_fact(world, f, "gift")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a gentle fable for a young child about {hero.id} learning a waltz at {place.label}.',
        f"Tell a short story where {hero.id} hears {tune.name}, worries inwardly, and then finds courage.",
        f'Write a child-friendly fable that includes the word "{tune.keyword}" and ends with a peaceful dance.',
        f"Compose a little story in which {hero.id} thinks to {hero.pronoun('object')}self, then accepts help with {gift.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide: Entity = _safe_fact(world, f, "guide")
    gift: Entity = _safe_fact(world, f, "gift")
    tune: Tune = _safe_fact(world, f, "tune")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who is the story mainly about at {place.label}?",
            answer=(
                f"The story is mainly about {hero.id}, a small {hero.type} who wanted to dance the waltz."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} worry about before the dance?",
            answer=(
                f"{hero.id} worried about stumbling and spoiling the waltz, because the beat felt fast in {hero.pronoun('possessive')} head."
            ),
        ),
        QAItem(
            question=f"What did the {guide.type} say to help {hero.id}?",
            answer=(
                f"The {guide.type} said that slow steps can still be beautiful, and that patient feet can follow the waltz."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} keep steady during {tune.name}?",
            answer=(
                f"{gift.label} helped {hero.id} keep steady, so {hero.pronoun('subject')} could follow the steps without falling."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=(
                f"{hero.id} felt proud and calm at the end, because the waltz turned into a happy, careful dance."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a waltz?",
            answer="A waltz is a kind of dance with a steady rhythm and gentle turning steps.",
        ),
        QAItem(
            question="Why do people listen to music while dancing?",
            answer="People listen to music while dancing so they can move with the beat and keep the steps together.",
        ),
        QAItem(
            question="What does patience help someone do?",
            answer="Patience helps someone slow down, keep trying, and do a careful job.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- place(P), affords(P,waltz).
gift_ok(G) :- gift(G), helps(G,balance).
compatible(P,T,G) :- place_ok(P), tune(T), gift_ok(G), tune_name(T,waltz).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TUNES.items():
        lines.append(asp.fact("tune", tid))
        lines.append(asp.fact("tune_name", tid, "waltz"))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = {
        (p, t, g)
        for p in PLACES
        for t in TUNES
        for g in GIFTS
        if reasonableness_gate(_safe_lookup(PLACES, p), _safe_lookup(TUNES, t), _safe_lookup(GIFTS, g))
    }
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print(" only in asp:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about a waltz and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tune", choices=TUNES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--guide", choices=["mouse", "hare", "fox", "rabbit"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for t in TUNES.values():
            for g in GIFTS.values():
                if reasonableness_gate(p, t, g):
                    combos.append((p.id, t.id, g.id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "tune", None):
        combos = [c for c in combos if c[1] == getattr(args, "tune", None)]
    if getattr(args, "gift", None):
        combos = [c for c in combos if c[2] == getattr(args, "gift", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tune, gift = rng.choice(list(combos))
    kind = getattr(args, "kind", None) or rng.choice(KINDS)
    guide = getattr(args, "guide", None) or rng.choice([k for k in KINDS if k != kind])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, kind))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, tune=tune, gift=gift, name=name, kind=kind, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(TUNES, params.tune),
        _safe_lookup(GIFTS, params.gift),
        params.name,
        params.kind,
        params.guide,
        params.trait,
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


CURATED = [
    StoryParams(place="clearing", tune="slow_waltz", gift="slippers", name="Milo", kind="mouse", guide="hare", trait="timid"),
    StoryParams(place="hall", tune="bright_waltz", gift="ribbon", name="Hattie", kind="hare", guide="fox", trait="earnest"),
    StoryParams(place="porch", tune="slow_waltz", gift="lamp", name="Violet", kind="fox", guide="rabbit", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, t, g in combos:
            print(f"  {p:9} {t:12} {g}")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name}: {p.tune} at {p.place} ({p.kind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
