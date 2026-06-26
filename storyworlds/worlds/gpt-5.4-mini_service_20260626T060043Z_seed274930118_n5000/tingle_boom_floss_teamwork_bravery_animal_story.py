#!/usr/bin/env python3
"""
storyworlds/worlds/tingle_boom_floss_teamwork_bravery_animal_story.py
======================================================================

A small animal story world about a scary boom, a brave helper, and a
teamwork fix that uses floss as a simple tool.

Seed tale:
---
A little mouse heard a loud boom in the garden and felt a tingle in her paws.
Her friend was stuck on the other side of a shallow creek. The mouse was scared,
but she and two animal friends worked together. They used a bit of floss to tie
a safe pull-line, crossed the creek, and helped their friend get home.

Story shape:
- Setup: an animal notices something small and strange, then a boom makes the
  problem feel bigger.
- Tension: one friend is stuck or lost; the hero feels nervous.
- Turn: bravery shows up as a choice to act.
- Resolution: teamwork makes the fix possible, and the ending image proves the
  change.

This world keeps the prose concrete, child-facing, and state-driven.
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
# World model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"mouse", "rabbit", "cat", "duck", "squirrel", "deer", "fox"}
        male = {"mouse", "rabbit", "cat", "duck", "squirrel", "deer", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the garden"
    indoors: bool = False
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    sound: str
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
        self.zone: set[str] = set()
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.zone = set(self.zone)
        c.fired = set(self.fired)
        return c

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        for item in self.worn_items(actor):
            if item.id in PROTECTIVE_IDS and region in PROTECTIVE_MAP[item.id].covers:
                return True
        return False


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, affords={"boom", "tingle"}),
    "creekside": Setting(place="the creek", indoors=False, affords={"boom", "floss"}),
    "barnyard": Setting(place="the barnyard", indoors=False, affords={"boom"}),
}

ACTIVITIES = {
    "boom": Activity(
        id="boom",
        verb="go look at the boom",
        gerund="looking at the boom",
        rush="run toward the boom",
        mess="shaken",
        soil="all shaky",
        zone={"ears", "paws"},
        sound="boom",
        keyword="boom",
        tags={"boom", "sound", "bravery"},
    ),
    "tingle": Activity(
        id="tingle",
        verb="follow the tingle",
        gerund="following the tingle",
        rush="skip toward the tingle",
        mess="tickled",
        soil="all tingly",
        zone={"nose", "paws"},
        sound="tingle",
        keyword="tingle",
        tags={"tingle", "sound"},
    ),
    "floss": Activity(
        id="floss",
        verb="use the floss",
        gerund="using the floss",
        rush="pull on the floss",
        mess="tangled",
        soil="all tangled",
        zone={"paws"},
        sound="soft swish",
        keyword="floss",
        tags={"floss", "tool", "teamwork"},
    ),
}

PRIZES = {
    "blue_scarf": Prize(
        label="scarf",
        phrase="a soft blue scarf",
        type="scarf",
        region="neck",
    ),
    "red_boots": Prize(
        label="boots",
        phrase="tiny red boots",
        type="boots",
        region="paws",
        plural=True,
    ),
    "basket": Prize(
        label="basket",
        phrase="a little berry basket",
        type="basket",
        region="paws",
    ),
}

GEAR = [
    Gear(
        id="earmuffs",
        label="earmuffs",
        covers={"ears"},
        guards={"shaken"},
        prep="put on earmuffs first",
        tail="took the earmuffs along",
        plural=True,
    ),
    Gear(
        id="gloves",
        label="gloves",
        covers={"paws"},
        guards={"tangled"},
        prep="pull on soft gloves first",
        tail="carried the soft gloves",
        plural=True,
    ),
    Gear(
        id="towel",
        label="a towel",
        covers={"neck", "paws"},
        guards={"shaken", "tangled"},
        prep="wrap up in a towel first",
        tail="brought the towel along",
    ),
]

PROTECTIVE_MAP = {g.id: g for g in GEAR}
PROTECTIVE_IDS = set(PROTECTIVE_MAP)

ANIMALS = [
    ("mila", "mouse"),
    ("pip", "squirrel"),
    ("rory", "rabbit"),
    ("dot", "duck"),
    ("nib", "mouse"),
    ("luna", "cat"),
]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning
# ---------------------------------------------------------------------------
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if prize.region in g.covers and activity.mess in g.guards:
            return g
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    out.append((place, act_id, prize_id))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    h = rng.choice(ANIMALS)
    helper = rng.choice([a for a in ANIMALS if a != h])
    friend = rng.choice([a for a in ANIMALS if a != h and a != helper])
    return StoryParams(place, activity, prize, h[0], h[1], helper[0], helper[1], friend[0], friend[1])


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type))
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    prize = world.add(Entity(
        id="prize", kind="thing", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, plural=prize_cfg.plural, owner=hero.id,
        caretaker=helper.id,
    ))
    prize.worn_by = hero.id
    return world


def _do_activity(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    world.zone = set(act.zone)
    actor.meters[act.mess] = actor.meters.get(act.mess, 0) + 1
    actor.memes["brave"] = actor.memes.get("brave", 0) + 0.5
    if narrate:
        world.say(f"{actor.id} went to {act.verb}.")


def predict_mess(world: World, actor: Entity, act: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), act, narrate=False)
    prize = sim.entities[prize_id]
    soiled = prize.region in act.zone and not sim.covered(sim.get(actor.id), prize.region)
    return {"soiled": soiled}


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved quiet paths and soft grass.")


def setup(world: World, hero: Entity, helper: Entity, friend: Entity, act: Activity, prize: Entity) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0) + 1
    world.say(f"{hero.id} felt a tiny {act.keyword} in {hero.pronoun('paws') if False else 'her'} paws and turned to listen.")
    world.say(f"Then a loud boom rolled over {world.setting.place}, and {hero.id}'s heart gave a quick thump.")
    world.say(f"{friend.id} froze near the creek, too far to cross alone.")
    world.say(f"{helper.id} looked at {prize.phrase} and knew the breeze could tug it loose in the scramble.")


def ask_and_worry(world: World, hero: Entity, helper: Entity, friend: Entity, act: Activity, prize: Entity) -> None:
    pred = predict_mess(world, hero, act, prize.id)
    if pred["soiled"]:
        world.facts["predicted_soil"] = act.soil
        world.say(f"{hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} paws shook.")
        world.say(f'"If I rush, my {prize.label} will get {act.soil}," {hero.id} whispered.')


def brave_turn(world: World, hero: Entity, helper: Entity, friend: Entity, act: Activity, prize: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(f"Still, {hero.id} took one deep breath and decided to be brave.")
    gear = select_gear(act, prize)
    if gear:
        item = world.add(Entity(id=gear.id, kind="thing", type="gear", label=gear.label, plural=gear.plural))
        item.worn_by = hero.id
        world.say(f"{helper.id} smiled and said, '{gear.prep}.'")
        world.say(f"{hero.id} nodded, and together they {gear.tail}.")


def teamwork(world: World, hero: Entity, helper: Entity, friend: Entity, act: Activity, prize: Entity) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    friend.memes["safe"] = friend.memes.get("safe", 0) + 1
    world.say(f"{hero.id}, {helper.id}, and {friend.id} worked as a small team.")
    world.say(f"They used a piece of floss to make a gentle pull-line, just strong enough to help.")
    world.say(f"With one careful tug, {friend.id} crossed the creek, and the boom no longer felt so big.")


def ending(world: World, hero: Entity, helper: Entity, friend: Entity, act: Activity, prize: Prize) -> None:
    world.say(f"In the end, {hero.id} was still a little shaky, but {hero.id} was smiling.")
    world.say(f"{friend.id} was safe, {helper.id} was laughing, and the {prize.label} stayed clean.")
    world.say(f"The soft floss line lay tucked in {hero.pronoun('possessive')} pocket like a tiny promise for next time.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get(params.hero)
    helper = world.get(params.helper)
    friend = world.get(params.friend)
    prize = world.get("prize")
    act = _safe_lookup(ACTIVITIES, params.activity)
    intro(world, hero)
    world.para()
    setup(world, hero, helper, friend, act, prize)
    ask_and_worry(world, hero, helper, friend, act, prize)
    world.para()
    brave_turn(world, hero, helper, friend, act, prize)
    teamwork(world, hero, helper, friend, act, prize)
    ending(world, hero, helper, friend, act, prize)
    world.facts.update(hero=hero, helper=helper, friend=friend, prize=prize, activity=act, gear=select_gear(act, prize))
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story about {f['hero'].id}, a little {f['hero'].type}, who hears a {f['activity'].keyword} and becomes brave.",
        f"Tell a short story where {f['hero'].id} and friends use floss to help after a boom near {world.setting.place}.",
        "Write a child-friendly animal story that includes teamwork, bravery, boom, tingle, and floss.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, friend, prize, act = f["hero"], f["helper"], f["friend"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, who was scared at first but became brave with help from {helper.id} and {friend.id}.",
        ),
        QAItem(
            question=f"What scary sound made the day feel bigger?",
            answer=f"A loud boom rolled over {world.setting.place}, and that made the little problem feel much bigger for {hero.id}.",
        ),
        QAItem(
            question=f"How did they help {friend.id} cross safely?",
            answer="They worked together and used a piece of floss as a gentle pull-line, so the friend could cross without falling in.",
        ),
        QAItem(
            question=f"What stayed safe at the end?",
            answer=f"The {prize.label} stayed clean and safe, and the friends could smile together afterward.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people or animals help each other and do a job together, so the job is easier or safer.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something scary or hard even when you feel nervous, because it is the right thing to do.",
        ),
        QAItem(
            question="What is floss?",
            answer="Floss is a thin string people use to clean between teeth, and a strong string can also help tie or pull something in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} kind={e.kind} worn_by={e.worn_by} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - asp_set:
        print("only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("only in asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: tingle, boom, floss; teamwork and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    StoryParams("garden", "boom", "blue_scarf", "mila", "mouse", "rory", "rabbit", "dot", "duck"),
    StoryParams("creekside", "floss", "red_boots", "pip", "squirrel", "luna", "cat", "mila", "mouse"),
    StoryParams("barnyard", "boom", "basket", "nib", "mouse", "rory", "rabbit", "dot", "duck"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
            except StoryError:
                continue
            params.seed = (getattr(args, "seed", None) or 0) + i
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
        header = f"### sample {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
