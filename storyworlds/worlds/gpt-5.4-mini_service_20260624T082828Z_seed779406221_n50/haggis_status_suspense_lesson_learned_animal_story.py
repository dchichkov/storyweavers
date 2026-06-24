#!/usr/bin/env python3
"""
storyworlds/worlds/haggis_status_suspense_lesson_learned_animal_story.py
========================================================================

A small animal-story world about a haggis, status, suspense, and a lesson
learned.

Seed-tale sketch:
---
A young haggis wants status in the clan. It sees a shiny status ribbon awarded
to the bravest runner at the high hill path. The haggis wants it badly, but the
path is steep and a sudden fog makes the stones slippery. An older haggis warns
that chasing status alone could lead to a tumble. The young haggis hurries
anyway, gets stuck on a ledge, and feels scared. Then it notices another small
animal below waiting for help. The young haggis shares its rope and guides the
other safely across. The clan sees the kindness, and the haggis learns that
true status comes from helping, not just being seen first.

World model:
---
- Physical meters track travel, balance, rope use, and storm danger.
- Emotional memes track desire, pride, worry, fear, help, and status.
- Suspense is driven by a forecasted slip on a high path in fog.
- Lesson learned resolves the tale: status rises when the hero helps others.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    elder: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self):
        for k in ["travel", "balance", "danger", "help", "damage"]:
            self.meters.setdefault(k, 0.0)
        for k in ["desire", "pride", "worry", "fear", "status", "kindness", "lesson"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "ma", "mom", "aunt", "sister", "girl", "female"}
        male = {"father", "pa", "dad", "uncle", "brother", "boy", "male"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    high_path: bool
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    danger_word: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        self.path_danger = 0.0
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.path_danger = self.path_danger
        w.paragraphs = [[]]
        return w


def _r_slip(world: World) -> list[str]:
    out = []
    if world.path_danger < THRESHOLD:
        return out
    for actor in world.characters():
        if actor.meters["balance"] <= 0:
            continue
        sig = ("slip", actor.id, int(world.path_danger))
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["balance"] -= 1
        actor.memes["fear"] += 1
        actor.memes["worry"] += 1
        out.append(f"The stones wobbled under {actor.id}'s feet.")
    return out


def _r_help(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["help"] < THRESHOLD:
            continue
        sig = ("help", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["kindness"] += 1
        actor.memes["status"] += 1
        actor.memes["lesson"] += 1
        out.append(f"The clan noticed {actor.id}'s kind heart.")
    return out


CAUSAL_RULES = [
    _r_slip,
    _r_help,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def forecast_slip(world: World, actor: Entity, quest: Quest) -> bool:
    sim = world.copy()
    sim.path_danger = max(sim.path_danger, 1.0)
    sim.get(actor.id).meters["balance"] += 1
    sim.get(actor.id).meters["travel"] += 1
    propagate(sim, narrate=False)
    return sim.get(actor.id).memes["fear"] >= THRESHOLD


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if quest.danger_word in g.guards and prize.region in g.covers:
            return g
    return None


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.tags


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "small")
    world.say(f"{hero.id} was a {trait} haggis with bright eyes and quick feet.")


def loves_status(world: World, hero: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} loved the idea of status, especially when the clan noticed brave deeds.")


def story_setup(world: World, hero: Entity, elder: Entity, prize: Entity, quest: Quest) -> None:
    world.say(
        f"At {world.setting.place}, the elders hung a shiny {prize.label} for the animal who could finish the {quest.verb}."
    )
    world.say(
        f"{hero.id} wanted that {prize.label} badly, and {elder.id} gave a calm warning about the high path."
    )


def turn_to_suspense(world: World, hero: Entity, elder: Entity, prize: Entity, quest: Quest) -> None:
    world.para()
    world.path_danger = 1.0
    hero.memes["worry"] += 1
    world.say(
        f"One foggy morning, {hero.id} and {elder.id} went to {world.setting.place}."
    )
    world.say(
        f"{hero.id} wanted to {quest.verb}, but the high stones looked slick and the hill seemed to vanish into mist."
    )
    if forecast_slip(world, hero, quest):
        world.say(
            f'"If you rush for status," {elder.id} said, "you may slip before you reach the top."'
        )


def risky_choice(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["pride"] += 1
    hero.meters["travel"] += 1
    world.say(f"{hero.id} still tried to {quest.rush}, even though its paws felt nervous.")
    propagate(world, narrate=True)


def rescue_and_lesson(world: World, hero: Entity, other: Entity, elder: Entity, prize: Entity, gear: Gear, quest: Quest) -> None:
    world.para()
    hero.meters["help"] += 1
    hero.memes["fear"] += 0.5
    world.say(
        f"Then {hero.id} heard a tiny cry below the ledge: {other.id} had slipped on the narrow trail."
    )
    world.say(
        f"{hero.id} gripped {gear.label}, lowered it carefully, and helped {other.id} climb to safe ground."
    )
    hero.memes["kindness"] += 1
    hero.memes["status"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"The elders smiled, because {hero.id} had learned that real status grows when you help someone else."
    )
    world.say(
        f"At the end, {hero.id} earned the {prize.label}, not just for being first, but for being brave and kind."
    )


SETTINGS = {
    "hill": Setting(place="the high hill path", high_path=True, affords={"race"}),
    "glen": Setting(place="the misty glen trail", high_path=False, affords={"search"}),
    "bridge": Setting(place="the little rope bridge", high_path=True, affords={"cross"}),
}

QUESTS = {
    "race": Quest(
        id="race",
        verb="win the race",
        gerund="racing up the hill",
        rush="dash up the stones",
        danger_word="slippery",
        keyword="status",
        tags={"path", "slippery"},
    ),
    "search": Quest(
        id="search",
        verb="find the bell",
        gerund="searching the glen",
        rush="hurry through the fog",
        danger_word="foggy",
        keyword="status",
        tags={"path", "foggy"},
    ),
    "cross": Quest(
        id="cross",
        verb="cross the bridge",
        gerund="crossing the bridge",
        rush="run across the rope bridge",
        danger_word="swaying",
        keyword="status",
        tags={"bridge", "swaying"},
    ),
}

PRIZES = {
    "ribbon": Prize(label="status ribbon", phrase="a shiny status ribbon", type="ribbon", region="torso"),
    "leaf_pin": Prize(label="leaf pin", phrase="a bright leaf pin", type="pin", region="torso"),
}

GEAR = [
    Gear(id="rope", label="a sturdy rope", covers={"torso"}, guards={"slippery", "swaying", "foggy"}, prep="take the sturdy rope", tail="used the rope to make a safe path"),
    Gear(id="stick", label="a walking stick", covers={"feet"}, guards={"slippery"}, prep="pick up a walking stick", tail="leaned on the stick as they walked"),
]

HEROES = ["Moss", "Bracken", "Nip", "Pip", "Merry"]
ELDERS = ["Gran Haggis", "Old Bracken", "Aunt Thistle"]
SMALL_FRIENDS = ["Robin", "Mole", "Otterling"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    hero: str
    elder: str
    friend: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for q in s.affords:
            quest = _safe_lookup(QUESTS, q)
            for p_id, prize in PRIZES.items():
                if prize_at_risk(quest, prize) and select_gear(quest, prize):
                    combos.append((place, q, p_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a haggis learns that true status comes from kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--elder")
    ap.add_argument("--friend")
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
    if getattr(args, "quest", None) and getattr(args, "prize", None):
        q, p = _safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(q, p) and select_gear(q, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        quest=quest,
        prize=prize,
        hero=getattr(args, "hero", None) or rng.choice(HEROES),
        elder=getattr(args, "elder", None) or rng.choice(ELDERS),
        friend=getattr(args, "friend", None) or rng.choice(SMALL_FRIENDS),
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type="haggis", traits=["young", "curious"]))
    elder = world.add(Entity(id=params.elder, kind="character", type="haggis", traits=["older", "wise"]))
    friend = world.add(Entity(id=params.friend, kind="character", type="animal", traits=["small", "shy"]))
    prize = world.add(Entity(id="prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=hero.id, caretaker=elder.id, region=_safe_lookup(PRIZES, params.prize).region))
    gear = GEAR[0]
    quest = _safe_lookup(QUESTS, params.quest)
    hero.worn = prize

    introduce(world, hero)
    loves_status(world, hero)
    story_setup(world, hero, elder, prize, quest)
    turn_to_suspense(world, hero, elder, prize, quest)
    risky_choice(world, hero, quest)
    rescue_and_lesson(world, hero, friend, elder, prize, gear, quest)

    world.facts.update(hero=hero, elder=elder, friend=friend, prize=prize, quest=quest, gear=gear, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a child about a haggis named {f["hero"].id} who wants status at {f["setting"].place}.',
        f"Tell a suspenseful but gentle story where {f['hero'].id} tries to {f['quest'].verb} and learns a lesson about kindness.",
        f"Write a simple story that uses the word 'status' and ends with {f['hero'].id} helping a smaller animal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, friend, prize, quest = f["hero"], f["elder"], f["friend"], f["prize"], f["quest"]
    return [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"It is mostly about {hero.id}, a young haggis who wanted status at {f['setting'].place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want at the start of the story?",
            answer=f"{hero.id} wanted the {prize.label} and hoped it would give them status.",
        ),
        QAItem(
            question=f"Why was the middle of the story suspenseful?",
            answer=f"It was suspenseful because {hero.id} was on a high, slippery path in the fog and could have slipped while trying to {quest.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} do when {friend.id} needed help?",
            answer=f"{hero.id} lowered the rope and helped {friend.id} get safely across the danger.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that real status comes from being kind and helping others, not from rushing ahead alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a haggis in this story world?",
            answer="A haggis is a small hill animal with quick feet and a big heart in this story world.",
        ),
        QAItem(
            question="What does status mean here?",
            answer="Status means the respect or honor other animals give someone for doing a good deed.",
        ),
        QAItem(
            question="Why is a rope helpful on a high path?",
            answer="A rope can help an animal keep balance and cross safely when the ground is slippery or swaying.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    out.append(f"path_danger={world.path_danger}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- activity(Q).
prize(X) :- item(X).

valid(P,Q,I) :- affords(P,Q), needs_risk(Q,I), has_gear(Q,I).
needs_risk(Q,I) :- quest(Q), prize(I), risk_region(Q,R), worn_on(I,R).
has_gear(Q,I) :- needs_risk(Q,I), gear(G), guards(G,M), danger_of(Q,M), covers(G,R), worn_on(I,R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.high_path:
            lines.append(asp.fact("high_path", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("activity", qid))
        lines.append(asp.fact("danger_of", qid, q.danger_word))
        for t in sorted(q.tags):
            lines.append(asp.fact("risk_region", qid, t))
    for iid, p in PRIZES.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("worn_on", iid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(a - p))
    print(" only in python:", sorted(p - a))
    return 1


CURATED = [
    StoryParams(place="hill", quest="race", prize="ribbon", hero="Moss", elder="Gran Haggis", friend="Robin"),
    StoryParams(place="bridge", quest="cross", prize="leaf_pin", hero="Bracken", elder="Aunt Thistle", friend="Mole"),
]


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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
