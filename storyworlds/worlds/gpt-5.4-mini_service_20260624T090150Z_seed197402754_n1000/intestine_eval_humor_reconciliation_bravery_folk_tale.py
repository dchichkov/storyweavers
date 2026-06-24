#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/intestine_eval_humor_reconciliation_bravery_folk_tale.py
================================================================================

A small folk-tale storyworld about a brave child or animal courier, a comic
misunderstanding, a stern judgment from Elder Eval, and a warm reconciliation.

Seed tale idea:
- A young courier must cross a twisty, belly-like river path called the Intestine.
- A funny mishap makes the village laugh, but the task still matters.
- Elder Eval weighs the result, and the hero finds a brave, kind way to mend the
  rift and finish the errand.
- The ending proves the village is closer, the fear is gone, and everyone can
  laugh together.

The world is intentionally tiny and classical: one premise, one tension, one
turn, one resolution.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    elder: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the village"
    affordances: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


def _r_comic_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in list(world.entities.values()):
        if actor.kind != "character":
            continue
        if actor.memes.get("giggled", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("mess", 0.0) < THRESHOLD:
            continue
        sig = ("comic_mess", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["embarrassment"] = actor.memes.get("embarrassment", 0.0) + 1
        out.append(f"The village giggled, and {actor.id} felt their cheeks grow hot.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    elder = world.entities.get("elder")
    if not hero or not elder:
        return out
    if hero.memes.get("apology", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    elder.memes["warmth"] = elder.memes.get("warmth", 0.0) + 1
    out.append(f"By speaking kindly, {hero.id} and Elder Eval found their way back to one another.")
    return out


RULES = [
    ("comic_mess", _r_comic_mess),
    ("reconcile", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _name, rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(quest: Quest, prize: Prize, remedy: Remedy) -> bool:
    return (quest.risk in remedy.helps) and (prize.region in {"torso", "feet", "hands", "mouth"})


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in {"feet", "torso", "mouth"}


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    elder: str
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


SETTINGS = {
    "village": Setting(place="the village green", affordances={"cross", "carry"}),
    "lane": Setting(place="the windy lane", affordances={"cross"}),
    "market": Setting(place="the market square", affordances={"carry", "cross"}),
}

QUESTS = {
    "intestine": Quest(
        id="intestine",
        verb="cross the Intestine Path",
        gerund="crossing the Intestine Path",
        rush="dash across the swaying path",
        risk="slippery",
        tags={"intestine", "path", "river"},
    ),
    "eval": Quest(
        id="eval",
        verb="bring the pie to Elder Eval",
        gerund="carrying the pie to Elder Eval",
        rush="hurry with the pie basket",
        risk="dropping",
        tags={"eval", "judge", "pie"},
    ),
}

PRIZES = {
    "pie": Prize(label="pie", phrase="a plum pie", type="pie", region="hands"),
    "bell": Prize(label="bell", phrase="a brass bell", type="bell", region="hands"),
    "cloak": Prize(label="cloak", phrase="a red cloak", type="cloak", region="torso"),
}

REMEDIES = [
    Remedy(id="straw_sandals", label="straw sandals", prep="put on straw sandals", tail="stepped carefully in straw sandals", helps={"slippery"}),
    Remedy(id="cloth_wrap", label="a cloth wrap", prep="wrap the pie in a cloth", tail="carried the pie safely in a cloth wrap", helps={"dropping"}),
]


HERO_NAMES = {
    "girl": ["Mina", "Tali", "Sera", "Ira"],
    "boy": ["Jori", "Pavel", "Milo", "Ren"],
}
TRAITS = ["brave", "kind", "quick", "cheerful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale world of humor, reconciliation, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--trait")
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
    quest_id = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    prize_id = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    quest = _safe_lookup(QUESTS, quest_id)
    prize = _safe_lookup(PRIZES, prize_id)
    if not prize_at_risk(quest, prize):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in prize.genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(HERO_NAMES, gender))
    elder = getattr(args, "elder", None) or "Eval"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest_id, prize=prize_id, name=name, gender=gender, elder=elder, trait=trait)


def _intro(world: World, hero: Entity, elder: Entity, quest: Quest, prize: Entity) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there lived a {hero.pronoun('possessive')} little {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.id} was {hero.traits[0]} and loved {quest.gerund}, even when the road was as twisty as a braid."
    )
    world.say(
        f"One market day, {elder.id} trusted {hero.id} with {prize.phrase}, and the errand felt important."
    )


def _turn(world: World, hero: Entity, elder: Entity, quest: Quest, prize: Entity) -> None:
    world.para()
    world.say(
        f"But when {hero.id} reached {world.setting.place}, the {quest.id} way began to wobble and whisper."
    )
    world.say(
        f"{hero.id} wanted to {quest.verb}, yet a funny mishap made the villagers chuckle."
    )
    hero.meters["mess"] = hero.meters.get("mess", 0.0) + 1
    hero.memes["giggled"] = hero.memes.get("giggled", 0.0) + 1
    propagate(world, narrate=True)


def _resolve(world: World, hero: Entity, elder: Entity, quest: Quest, prize: Entity, remedy: Remedy) -> None:
    world.para()
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(
        f"Still, {hero.id} drew a brave breath, bowed to Elder Eval, and said sorry with an honest heart."
    )
    hero.memes["apology"] = hero.memes.get("apology", 0.0) + 1
    if quest.risk == "slippery":
        world.say(f"Then {hero.id} chose to {remedy.prep} before trying again.")
    else:
        world.say(f"Then {hero.id} chose to {remedy.prep} before trying again.")
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    world.say(
        f"{hero.id} {remedy.tail}, and the little crowd watched in surprised silence."
    )
    if quest.id == "eval":
        world.say(f"Elder Eval smiled at the careful hands and called the errand well done.")
    else:
        world.say(f"Elder Eval smiled at the careful feet and called the crossing well done.")
    hero.memes["reconciled"] = 1
    elder.memes["reconciled"] = 1
    propagate(world, narrate=True)
    world.say(
        f"In the end, {hero.id} went home with a lighter heart, and even the old path seemed to laugh kindly in the moonlight."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, hero_type: str, trait: str, elder_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "little"]))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label=elder_name, traits=["wise"]))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region, plural=prize_cfg.plural))
    hero.memes["bravery"] = 0.0
    elder.memes["warmth"] = 0.0

    _intro(world, hero, elder, quest, prize)
    _turn(world, hero, elder, quest, prize)

    remedy = _safe_lookup(REMEDIES, 0 if quest.risk == "slippery" else 1)
    world.para()
    world.say(f"At last, {elder.id} offered a gentle way forward.")
    world.say(f"{hero.id} listened, nodded, and chose the safer path.")
    _resolve(world, hero, elder, quest, prize, remedy)

    world.facts.update(hero=hero, elder=elder, prize=prize, quest=quest, remedy=remedy, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a folk tale for a young child about {hero.id} and the {quest.id} path, with a funny mishap and a kind ending.',
        f"Tell a short story where {hero.id} must {quest.verb} while carrying {prize.phrase}, and Elder Eval helps make peace.",
        f'Write a brave, gentle tale that includes the words "intestine" and "eval" in a magical village errand.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, quest, prize = f["hero"], f["elder"], f["quest"], f["prize"]
    return [
        QAItem(
            question=f"Who is the folk tale about?",
            answer=f"It is about {hero.id}, a little {hero.type} who learns to be brave while finishing a village errand.",
        ),
        QAItem(
            question=f"What did {hero.id} have to do with {prize.label}?",
            answer=f"{hero.id} had to {quest.verb} while taking care not to lose {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did Elder Eval matter in the story?",
            answer=f"Elder Eval helped judge the mishap kindly, and that made room for apology and reconciliation.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"By the end, {hero.id} was brave enough to mend the trouble, and the village was smiling again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is bravery?", "Bravery is doing something even though you feel a little afraid."),
        QAItem("What is reconciliation?", "Reconciliation is when people mend a hurt and become friendly again."),
        QAItem("Why can humor help?", "Humor can help people relax, share a laugh, and stop feeling so stuck."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
prize_at_risk(Quest, Prize) :- quest(Quest), prize(Prize), risky_region(Quest, Region), prize_region(Prize, Region).
compatible_remedy(Quest, Remedy) :- quest(Quest), remedy(Remedy), risk(Quest, Risk), helps(Remedy, Risk).
valid_story(Place, Quest, Prize) :- setting(Place), quest(Quest), prize(Prize), prize_at_risk(Quest, Prize), compatible_remedy(Quest, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("risk", qid, q.risk))
        for tag in sorted(q.tags):
            lines.append(asp.fact("tag", qid, tag))
        if qid == "intestine":
            lines.append(asp.fact("risky_region", qid, "hands"))
        else:
            lines.append(asp.fact("risky_region", qid, "hands"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for rid, r in [(rm.id, rm) for rm in REMEDIES]:
        lines.append(asp.fact("remedy", rid))
        for h in sorted(r.helps):
            lines.append(asp.fact("helps", rid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for qid, q in QUESTS.items():
            for pid, p in PRIZES.items():
                if prize_at_risk(q, p):
                    combos.append((place, qid, pid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only asp:", sorted(cl - py))
    return 1


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
    StoryParams(place="village", quest="intestine", prize="cloak", name="Mina", gender="girl", elder="Eval", trait="brave"),
    StoryParams(place="market", quest="eval", prize="pie", name="Jori", gender="boy", elder="Eval", trait="kind"),
]


def explain_rejection() -> str:
    return "No story: the chosen prize and quest do not create a meaningful comic risk for this folk tale."


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(PRIZES, params.prize), params.name, "girl" if params.gender == "girl" else "boy", params.trait, params.elder)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
