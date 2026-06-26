#!/usr/bin/env python3
"""
storyworlds/worlds/terrible_discount_repetition_myth.py
=======================================================

A small mythic story world about a bargain that begins as a terrible discount
and changes through repetition.

Seed premise:
---
In an old story-land, a young seeker wants a sacred prize, but the price is too
high. A shrine keeper offers a terrible discount only after the seeker repeats
the right plea three times. The first repeats feel awkward, then stubborn, then
magical. At last the bargain shifts, and the child goes home with the prize.

World model:
---
- Prices are meters.
- Wonder, fear, and trust are memes.
- Repetition raises a chant meter and can change a god's mood.
- A terrible discount is a real but poor bargain at first; if the repetition
  succeeds, the bargain improves.

This file follows the Storyweavers storyworld contract.
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
# Core world model
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    keeper: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "goddess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Shrine:
    name: str
    place: str
    spark: str
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
class Prize:
    id: str
    label: str
    phrase: str
    base_price: int
    desired_by: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Bargain:
    id: str
    label: str
    repeated_phrase: str
    needed_repeats: int
    discount_step: int
    final_discount: int
    mood_needed: str
    lesson: str
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
    def __init__(self, shrine: Shrine) -> None:
        self.shrine = shrine
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.shrine)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SHRINES = {
    "oak_shrine": Shrine(
        name="the oak shrine",
        place="the oak shrine",
        spark="leaf-light",
        affords={"petition", "repeat"},
    ),
    "river_shrine": Shrine(
        name="the river shrine",
        place="the river shrine",
        spark="river-glow",
        affords={"petition", "repeat"},
    ),
    "hill_shrine": Shrine(
        name="the hill shrine",
        place="the hill shrine",
        spark="dawn-fire",
        affords={"petition", "repeat"},
    ),
}

PRIZES = {
    "lamp": Prize(
        id="lamp",
        label="lamp",
        phrase="a small golden lamp",
        base_price=12,
        desired_by={"girl", "boy"},
    ),
    "harp": Prize(
        id="harp",
        label="harp",
        phrase="a bright little harp",
        base_price=14,
        desired_by={"girl"},
    ),
    "shield": Prize(
        id="shield",
        label="shield",
        phrase="a round bronze shield",
        base_price=16,
        desired_by={"boy"},
    ),
    "crown": Prize(
        id="crown",
        label="crown",
        phrase="a tiny star crown",
        base_price=18,
        desired_by={"girl", "boy"},
    ),
}

BARGAINS = {
    "chant_three": Bargain(
        id="chant_three",
        label="chant of three repeats",
        repeated_phrase="Please, give the child a kinder price.",
        needed_repeats=3,
        discount_step=2,
        final_discount=6,
        mood_needed="listening",
        lesson="repetition can soften a hard bargain",
    ),
    "name_the_price": Bargain(
        id="name_the_price",
        label="naming the price three times",
        repeated_phrase="This price is too high; let it fall.",
        needed_repeats=3,
        discount_step=1,
        final_discount=4,
        mood_needed="watching",
        lesson="careful words can change a story's cost",
    ),
}

HERO_NAMES = ["Mira", "Niko", "Tala", "Ivo", "Sera", "Pavi", "Lina", "Orin"]
HERO_TYPES = {"girl": ["girl", "queen"], "boy": ["boy", "priest"]}


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    shrine: str
    prize: str
    bargain: str
    name: str
    gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Parsing / resolution
# ---------------------------------------------------------------------------
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
    ap = argparse.ArgumentParser(
        description="A mythic story world of a terrible discount, repeated into a better bargain."
    )
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--bargain", choices=BARGAINS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def explain_rejection(prize: Prize, gender: str) -> str:
    return f"(No story: a {prize.label} is not a typical {gender}'s prize in this myth.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for shrine_id, shrine in SHRINES.items():
        for prize_id, prize in PRIZES.items():
            for bargain_id in BARGAINS:
                combos.append((shrine_id, prize_id, bargain_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).desired_by:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "shrine", None) is None or c[0] == getattr(args, "shrine", None))
              and (getattr(args, "prize", None) is None or c[1] == getattr(args, "prize", None))
              and (getattr(args, "bargain", None) is None or c[2] == getattr(args, "bargain", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[1]].desired_by)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    shrine, prize, bargain = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(PRIZES, prize).desired_by))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    return StoryParams(shrine=shrine, prize=prize, bargain=bargain, name=name, gender=gender)


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def price_text(n: int) -> str:
    return f"{n} silver coins"


def setup(world: World, hero: Entity, prize: Entity, shrine: Shrine, bargain: Bargain) -> None:
    world.say(
        f"Long ago, {hero.id} came to {shrine.place} and saw {prize.phrase} shining under the old stone."
    )
    world.say(
        f"Yet the keeper named the price as {price_text(prize.meters['price'])}, which felt terrible to {hero.id}."
    )
    world.say(
        f"Then the keeper offered a terrible discount: only a small fall in the price, if {hero.id} could repeat {bargain.repeated_phrase!r}."
    )


def chant(world: World, hero: Entity, bargain: Bargain, prize: Entity) -> None:
    hero.meters["repeats"] += 1
    hero.memes["hope"] += 1
    if hero.meters["repeats"] == 1:
        world.say(f"{hero.id} said the words once, softly, and the shrine stayed quiet.")
    elif hero.meters["repeats"] == 2:
        world.say(f"{hero.id} said them again, and the old air seemed to listen.")
    else:
        world.say(f"{hero.id} said them a third time, and the spark in the shrine began to stir.")
    if hero.meters["repeats"] >= bargain.needed_repeats:
        hero.memes["favor"] += 1
        prize.meters["price"] = max(1, prize.meters["price"] - bargain.final_discount)
    else:
        prize.meters["price"] = max(1, prize.meters["price"] - bargain.discount_step)


def resolve(world: World, hero: Entity, prize: Entity, bargain: Bargain) -> None:
    if hero.meters["repeats"] < bargain.needed_repeats:
        hero.memes["doubt"] += 1
        world.say(
            f"At first the discount remained terrible, and {hero.id} wondered if the old keeper would ever listen."
        )
        return
    hero.memes["trust"] += 1
    world.say(
        f"At the third repeat, the keeper bowed and gave {hero.id} the better price."
    )
    world.say(
        f"So {hero.id} paid {price_text(prize.meters['price'])}, took {prize.phrase}, and walked home with a light heart."
    )
    world.say(
        f"The lesson stayed behind like a lamp in the dark: {bargain.lesson}."
    )


def tell(shrine: Shrine, prize_cfg: Prize, bargain: Bargain, hero_name: str, hero_gender: str) -> World:
    world = World(shrine)
    hero_type = _safe_lookup(HERO_TYPES, hero_gender)[0]
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    keeper = world.add(Entity(id="Keeper", kind="character", type="priest", label="the keeper"))
    prize = world.add(Entity(
        id=prize_cfg.id,
        kind="thing",
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=keeper.id,
        meters={"price": float(prize_cfg.base_price)},
        memes={"value": 1.0},
    ))
    world.facts.update(hero=hero, keeper=keeper, prize=prize, bargain=bargain, shrine=shrine)

    setup(world, hero, prize, shrine, bargain)
    world.para()
    world.say(f"{hero.id} stood before {shrine.place} and began the repetition.")
    chant(world, hero, bargain, prize)
    resolve(world, hero, prize, bargain)
    if hero.meters["repeats"] < bargain.needed_repeats:
        world.para()
        chant(world, hero, bargain, prize)
        resolve(world, hero, prize, bargain)
    if hero.meters["repeats"] < bargain.needed_repeats:
        world.para()
        chant(world, hero, bargain, prize)
        resolve(world, hero, prize, bargain)

    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    bargain = _safe_fact(world, f, "bargain")
    shrine = _safe_fact(world, f, "shrine")
    return [
        f'Write a short mythic story for a child about {hero.id} at {shrine.place}, with the words "terrible" and "discount".',
        f"Tell a gentle legend where {hero.id} repeats a plea three times to get {prize.phrase} at a better price.",
        f"Write a tiny myth in which repetition changes a terrible discount into a kinder bargain.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prize: Entity = _safe_fact(world, f, "prize")
    bargain: Bargain = _safe_fact(world, f, "bargain")
    shrine: Shrine = _safe_fact(world, f, "shrine")
    qa = [
        QAItem(
            question=f"What did {hero.id} want at {shrine.place}?",
            answer=f"{hero.id} wanted {prize.phrase}, which shone like a little treasure in the shrine.",
        ),
        QAItem(
            question=f"What made the first bargain terrible?",
            answer=(
                f"The keeper offered only a small discount at first, so the price was still too high for {hero.id}."
            ),
        ),
        QAItem(
            question=f"What had {hero.id} to do to change the price?",
            answer=(
                f"{hero.id} had to repeat {bargain.repeated_phrase!r} three times, because repetition was the key to the bargain."
            ),
        ),
    ]
    if hero.meters.get("repeats", 0) >= bargain.needed_repeats:
        qa.append(
            QAItem(
                question=f"How many times did {hero.id} repeat the words?",
                answer=f"{hero.id} repeated the words three times, and on the third time the price changed.",
            )
        )
        qa.append(
            QAItem(
                question=f"What happened after the repetition worked?",
                answer=(
                    f"The keeper gave {hero.id} the better price, so {hero.id} could carry {prize.phrase} home."
                ),
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "discount": [
        QAItem(
            question="What is a discount?",
            answer="A discount is when a price is made lower, so something costs less money.",
        )
    ],
    "repetition": [
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing the same thing again and again.",
        )
    ],
    "myth": [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story about special people, gods, or magical happenings.",
        )
    ],
    "terrible": [
        QAItem(
            question="What does terrible mean?",
            answer="Terrible means very bad or not good at all.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for key in ["terrible", "discount", "repetition", "myth"] for qa in WORLD_KNOWLEDGE[key]]


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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(P) :- prize(P).
needs_repetition(B) :- bargain(B).
good_bargain(P,B) :- prize(P), bargain(B).
valid_story(S,P,B) :- shrine(S), prize(P), bargain(B).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHRINES:
        lines.append(asp.fact("shrine", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for bid in BARGAINS:
        lines.append(asp.fact("bargain", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
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


# ---------------------------------------------------------------------------
# Sample generation / emit
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SHRINES, params.shrine), _safe_lookup(PRIZES, params.prize), _safe_lookup(BARGAINS, params.bargain), params.name, params.gender)
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
    StoryParams(shrine="oak_shrine", prize="lamp", bargain="chant_three", name="Mira", gender="girl"),
    StoryParams(shrine="river_shrine", prize="harp", bargain="name_the_price", name="Tala", gender="girl"),
    StoryParams(shrine="hill_shrine", prize="shield", bargain="chant_three", name="Orin", gender="boy"),
    StoryParams(shrine="oak_shrine", prize="crown", bargain="name_the_price", name="Sera", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shrine, prize, bargain) combos.")
        for c in combos:
            print("  ", c)
        return

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
            header = f"### {p.name}: {p.prize} at {p.shrine}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
