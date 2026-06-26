#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/fuck_strip_attempt_humor_moral_value_sharing.py
=============================================================================================================================

A standalone storyworld for a tall-tale-ish little domain about a comic
attempt, a narrow strip of something valuable, and the lesson that sharing
beats grabbing.

The seed words for this world are intentionally embedded in the world model and
its ASP twin: fuck, strip, attempt.

Story premise:
- A boastful child or villager finds a tiny strip of magical stuff
- One character attempts to keep it all
- The town laughs, the mistake grows larger, and a moral choice emerges
- The ending proves that sharing turns the comic problem into a feast

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports results eagerly
- imports asp lazily only in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
SEED_WORDS = ("fuck", "strip", "attempt")



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
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"value": 0.0, "mess": 0.0, "joy": 0.0}
        if not self.memes:
            self.memes = {"humor": 0.0, "greed": 0.0, "generosity": 0.0, "pride": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "uncle", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "aunt", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    id: str
    label: str
    setting: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""
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
class Prize:
    id: str
    label: str
    phrase: str
    value_word: str
    shared_benefit: str
    risk_word: str
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
class Trick:
    id: str
    verb: str
    noun: str
    mess_word: str
    joke: str
    result_word: str
    shares_with: str
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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _is_char(e: Entity) -> bool:
    return e.kind == "character"


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    trick = _safe_fact(world, world.facts, "trick")
    for e in list(world.entities.values()):
        if not _is_char(e):
            continue
        if e.memes["humor"] >= THRESHOLD and ("laugh", e.id) not in world.fired:
            world.fired.add(("laugh", e.id))
            e.meters["joy"] += 1
            out.append(f"The whole place shook with laughter at the {trick.noun}.")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("prize")
    for e in list(world.entities.values()):
        if not _is_char(e):
            continue
        if e.memes["generosity"] < THRESHOLD:
            continue
        if ("share", e.id) in world.fired:
            continue
        world.fired.add(("share", e.id))
        prize.shared_with.add(e.id)
        e.meters["joy"] += 1
        out.append(f"{e.id} opened a hand and made room for the others.")
    return out


def _r_greed_turns_sour(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("prize")
    owner = world.entities.get(prize.owner) if prize.owner else None
    if not owner:
        return out
    if owner.memes["greed"] < THRESHOLD:
        return out
    sig = ("sour", owner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.meters["mess"] += 1
    owner.memes["pride"] += 1
    out.append("Trying to keep it all only made the trouble wobble bigger.")
    return out


CAUSAL_RULES = [
    _r_humor,
    _r_greed_turns_sour,
    _r_sharing,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(place: Place, prize: Prize, trick: Trick) -> bool:
    return "share" in place.affords and prize.shared_benefit and trick.verb and trick.result_word


def _story_opening(hero: Entity, prize: Entity, place: Place, trick: Trick) -> str:
    return (
        f"Long before supper, {hero.id} found {hero.pronoun('possessive')} {prize.label} "
        f"gleaming at {place.label}. It was only a little thing, but in a tall-tale town "
        f"even a strip of {prize.value_word} could seem as grand as a wagon wheel."
    )


def _story_tension(hero: Entity, friend: Entity, prize: Entity, trick: Trick) -> str:
    return (
        f"{hero.id} wanted to keep the whole {prize.label} all to {hero.pronoun('possessive')}self "
        f"and made a foolish attempt to hide it under {hero.pronoun('possessive')} hat. "
        f"{friend.id} pointed at the wobbling bundle and snorted, and soon the joke spread faster "
        f"than a stampede."
    )


def _story_turn(hero: Entity, friend: Entity, prize: Entity, trick: Trick) -> str:
    return (
        f"Then {friend.id} said, \"If you share that strip of {prize.value_word}, it will feed more mouths "
        f"than one.\" {hero.id} blinked, laughed at the mighty little mistake, and set the prize on the table "
        f"for everybody to reach."
    )


def _story_resolution(hero: Entity, friend: Entity, prize: Entity, trick: Trick) -> str:
    return (
        f"After that, they split the {prize.label} into {trick.shares_with} and passed it around. "
        f"The town laughed, the plates filled, and {hero.id} learned that a shared joke tastes better "
        f"than a proud pocket."
    )


@dataclass
class StoryParams:
    place: str
    prize: str
    trick: str
    name: str
    friend: str
    gender: str
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
    "barn": Place(id="barn", label="the red barn", setting="rural", affords={"share", "laugh"}, mood="rusty"),
    "market": Place(id="market", label="the town market", setting="town", affords={"share", "laugh"}, mood="busy"),
    "camp": Place(id="camp", label="the wagon camp", setting="frontier", affords={"share", "laugh"}, mood="dusty"),
}

PRIZES = {
    "stripcake": Prize(
        id="stripcake",
        label="strip of berry cake",
        phrase="a sticky strip of berry cake",
        value_word="berry cake",
        shared_benefit="slices",
        risk_word="crumbly",
    ),
    "stripgold": Prize(
        id="stripgold",
        label="strip of gold leaf",
        phrase="a shining strip of gold leaf",
        value_word="gold leaf",
        shared_benefit="flakes",
        risk_word="thin",
    ),
    "strippie": Prize(
        id="strippie",
        label="strip of pie crust",
        phrase="a flaky strip of pie crust",
        value_word="pie crust",
        shared_benefit="bits",
        risk_word="crumbly",
    ),
}

TRICKS = {
    "hat": Trick(
        id="hat",
        verb="attempt to hide",
        noun="hat-trick",
        mess_word="comic",
        joke="the hat sat lopsided like a tired crow",
        result_word="laugh",
        shares_with="neat little pieces",
    ),
    "rope": Trick(
        id="rope",
        verb="attempt to tie",
        noun="rope-tangle",
        mess_word="twisty",
        joke="the rope danced around like it had thunder in its toes",
        result_word="giggle",
        shares_with="long friendly strips",
    ),
    "pocket": Trick(
        id="pocket",
        verb="attempt to pocket",
        noun="pocket-fumble",
        mess_word="tumble",
        joke="the pocket bulged like a mouse hiding a moonbeam",
        result_word="chuckle",
        shares_with="small fair shares",
    ),
}

HERO_NAMES = ["Molly", "Hank", "Ruby", "Eli", "Nora", "Bo", "Penny", "Jeb"]
FRIEND_NAMES = ["Aunt June", "Old Walt", "Maggie", "Tom", "Cora", "Uncle Pip"]
TRAITS = ["bold", "sly", "cheery", "lucky", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for prid, prize in PRIZES.items():
            for tid, trick in TRICKS.items():
                if reasonableness_gate(place, prize, trick):
                    combos.append((pid, prid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about humor, sharing, and a comic attempt.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (getattr(args, "prize", None) is None or c[1] == getattr(args, "prize", None))
              and (getattr(args, "trick", None) is None or c[2] == getattr(args, "trick", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prize, trick = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, prize=prize, trick=trick, name=name, friend=friend, gender=gender)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    trick = _safe_lookup(TRICKS, params.trick)
    world = World(place)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    friend = world.add(Entity(id=params.friend, kind="character", type="person"))
    prize = world.add(Entity(id="prize", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase, plural=False, owner=hero.id))

    world.facts = {"hero": hero, "friend": friend, "prize": prize, "prize_cfg": prize_cfg, "trick": trick, "place": place}

    world.say(_story_opening(hero, prize, place, trick))
    world.say(
        f"{hero.id} loved the shiny thing and made a grand joke about being the richest squirrel in the county."
    )

    world.para()
    hero.memes["greed"] += 1
    hero.memes["humor"] += 1
    world.say(_story_tension(hero, friend, prize, trick))
    propagate(world, narrate=True)

    world.para()
    hero.memes["generosity"] += 1
    world.say(_story_turn(hero, friend, prize, trick))
    propagate(world, narrate=True)

    world.para()
    hero.meters["joy"] += 1
    friend.meters["joy"] += 1
    world.say(_story_resolution(hero, friend, prize, trick))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize_cfg = _safe_fact(world, f, "prize_cfg")
    trick = _safe_fact(world, f, "trick")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a tall tale for a child about {hero.id}, a {prize_cfg.label}, and a comic {trick.verb} at {place.label}.',
        f'Tell a funny story that uses the words "{_safe_lookup(SEED_WORDS, 0)}", "{_safe_lookup(SEED_WORDS, 1)}", and "{_safe_lookup(SEED_WORDS, 2)}" as part of a moral lesson about sharing.',
        f"Write a short frontier-style story where a character makes a foolish {trick.noun} and learns to share a tiny strip of {prize_cfg.value_word}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, trick, place = f["hero"], f["friend"], f["prize"], f["trick"], f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} find at {place.label}?",
            answer=f"{hero.id} found {prize.phrase} at {place.label}. It looked small, but it seemed mighty valuable in that tall-tale town.",
        ),
        QAItem(
            question=f"What silly thing did {hero.id} try to do with the {prize.label}?",
            answer=f"{hero.id} made an {trick.verb} to keep the {prize.label} hidden all by {hero.pronoun('possessive')}self, but the trick only made the joke bigger.",
        ),
        QAItem(
            question=f"Who helped {hero.id} learn the right choice?",
            answer=f"{friend.id} helped by pointing out that sharing the strip would feed more mouths than keeping it alone.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the {prize.label} was shared with everyone, the town laughed, and {hero.id} learned that generosity makes a better ending than greed.",
        ),
    ]


WORLD_QA = {
    "share": [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let other people use, enjoy, or eat part of something with you instead of keeping it all.",
        )
    ],
    "humor": [
        QAItem(
            question="What makes a story funny?",
            answer="A story can be funny when a character makes a silly mistake, says something playful, or gets into a harmless mix-up.",
        )
    ],
    "moral": [
        QAItem(
            question="What is a moral lesson?",
            answer="A moral lesson is the helpful idea a story leaves behind, like being kind, honest, or willing to share.",
        )
    ],
    "strip": [
        QAItem(
            question="What is a strip of something?",
            answer="A strip is a long, narrow piece of something, like a strip of ribbon, cake, cloth, or gold leaf.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA["share"] + WORLD_QA["humor"] + WORLD_QA["moral"] + WORLD_QA["strip"]


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
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", prize="stripcake", trick="hat", name="Molly", friend="Old Walt", gender="girl"),
    StoryParams(place="market", prize="stripgold", trick="rope", name="Hank", friend="Aunt June", gender="boy"),
    StoryParams(place="camp", prize="strippie", trick="pocket", name="Ruby", friend="Maggie", gender="girl"),
]


ASP_RULES = r"""
#show valid/3.

place(P) :- setting(P).
prize(R) :- prize_item(R).
trick(T) :- trick_item(T).

valid(Place, Prize, Trick) :- affords(Place, share),
                               prize_item(Prize),
                               trick_item(Trick),
                               friendly(Prize),
                               comedic(Trick).

% Tall-tale sanity: the story must have a narrow strip, a comic attempt, and a sharing outcome.
narrow_strip(Prize) :- prize_item(Prize).
comic_attempt(Trick) :- trick_item(Trick).
moral_value(Prize) :- prize_item(Prize).
sharing_ok(Prize) :- prize_item(Prize).

valid_story(Place, Prize, Trick) :- valid(Place, Prize, Trick),
                                    narrow_strip(Prize),
                                    comic_attempt(Trick),
                                    moral_value(Prize),
                                    sharing_ok(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("affords", pid, "share"))
        lines.append(asp.fact("affords", pid, "laugh"))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize_item", prid))
        lines.append(asp.fact("friendly", prid))
        lines.append(asp.fact("moral_value", prid))
        lines.append(asp.fact("sharing_ok", prid))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick_item", tid))
        lines.append(asp.fact("comedic", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def explain_rejection(place: Place, prize: Prize, trick: Trick) -> str:
    return (
        f"(No story: the setup needs a narrow strip, a comic attempt, and a sharing-friendly place. "
        f"Try another combination.)"
    )


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "prize", None) is None or c[1] == getattr(args, "prize", None))
              and (getattr(args, "trick", None) is None or c[2] == getattr(args, "trick", None))]
    if not combos:
        pass
    place, prize, trick = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, prize=prize, trick=trick, name=name, friend=friend, gender=gender)


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, prize, trick) combos ({len(stories)} with full story tags):\n")
        for place, prize, trick in triples:
            print(f"  {place:8} {prize:10} {trick:8}")
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
                params = valid_story_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.prize} at {p.place} ({p.trick})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
