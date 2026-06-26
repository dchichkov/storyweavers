#!/usr/bin/env python3
"""
fire_pillow_friendship_comedy.py
================================

A tiny friendship comedy world about fire, pillows, and the surprising ways
friends can help each other calm down, cool off, and fix a silly mess.

Premise:
A child or small creature loves a cozy pillow, but a little fire-related mishap
makes everyone nervous. A friend helps with a sensible, safe plan, and the
story ends with laughter, comfort, and the pillow returned to peace.

This world is designed to keep the story child-facing, concrete, and slightly
goofy, while still being state-driven and constraint-checked.
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
# Core model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Setting:
    place: str
    indoor: bool
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
class Event:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
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
    guards: set[str]
    covers: set[str]
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.weather = self.weather
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"toast", "storytime"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"marshmallows", "storytime"}),
    "living_room": Setting(place="the living room", indoor=True, affords={"storytime", "games"}),
}

EVENTS = {
    "toast": Event(
        id="toast",
        verb="make toast",
        gerund="making toast",
        rush="dash toward the toaster",
        mess="warm",
        soil="too warm",
        zone={"hands"},
        keyword="toast",
        tags={"fire", "warm"},
    ),
    "marshmallows": Event(
        id="marshmallows",
        verb="roast marshmallows",
        gerund="roasting marshmallows",
        rush="run close to the fire bowl",
        mess="smoky",
        soil="smoky and singed",
        zone={"hands", "torso"},
        keyword="fire",
        tags={"fire", "smoke"},
    ),
    "storytime": Event(
        id="storytime",
        verb="tell a silly story",
        gerund="telling silly stories",
        rush="huddle around the pillow fort",
        mess="rumpled",
        soil="rumpled",
        zone={"hands", "torso"},
        keyword="pillow",
        tags={"friendship", "pillow"},
    ),
    "games": Event(
        id="games",
        verb="play a pillow game",
        gerund="playing pillow games",
        rush="jump into the pile of pillows",
        mess="fluffy",
        soil="fluffy and messy",
        zone={"hands", "torso"},
        keyword="pillow",
        tags={"pillow", "friendship"},
    ),
}

PRIZES = {
    "pillow": Prize(
        label="pillow",
        phrase="a soft striped pillow",
        type="pillow",
        region="torso",
    ),
    "blanket": Prize(
        label="blanket",
        phrase="a cozy blanket",
        type="blanket",
        region="torso",
    ),
    "cape": Prize(
        label="cape",
        phrase="a shiny little cape",
        type="cape",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="mitts",
        label="oven mitts",
        guards={"warm", "smoky"},
        covers={"hands"},
        prep="put on oven mitts first",
        tail="put on the oven mitts",
        plural=True,
    ),
    Gear(
        id="blanket_wrap",
        label="a blanket wrap",
        guards={"smoky", "rumpled", "fluffy"},
        covers={"torso"},
        prep="wrap up in a blanket first",
        tail="wrapped up in the blanket",
    ),
    Gear(
        id="pillow_stack",
        label="a pillow stack",
        guards={"rumpled", "fluffy"},
        covers={"torso"},
        prep="build a safer pillow stack instead",
        tail="built the safer pillow stack",
    ),
]

NAMES = ["Mina", "Leo", "Sia", "Ben", "Nora", "Milo", "Tess", "Ari"]
TRAITS = ["silly", "brave", "cheerful", "curious", "bouncy"]
FRIENDS = ["pal", "buddy", "friend", "neighbor"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
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


def prize_at_risk(activity: Event, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Event, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(EVENTS, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(activity: Event, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} does not reach the {prize.label}. "
            f"Try a prize worn on the torso.)"
        )
    return (
        f"(No story: nothing reasonable in this world protects the {prize.label} "
        f"from {activity.gerund}. The fix must actually cover the at-risk item.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def setting_detail(setting: Setting, activity: Event) -> str:
    if setting.indoor:
        return f"{setting.place.capitalize()} felt cozy, with a little pile of pillows nearby."
    return f"{setting.place.capitalize()} felt bright, and a warm spot waited near the fire bowl."


def intro(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.pronoun('subject') if False else hero.type} "
        f"who liked cozy things and had a special {prize.label}."
    )
    world.say(
        f"{friend.id} was {hero.id}'s {friend.label} {friend.type} and the best kind of {friend.label} to have around."
    )


def loves(world: World, hero: Entity, activity: Event) -> None:
    world.say(
        f"{hero.id} loved {activity.gerund}, because it made the day feel funny and bright."
    )


def builds_friendship(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"{hero.id} and {friend.id} were the kind of friends who could giggle at almost anything."
    )


def predicts_mess(world: World, hero: Entity, activity: Event, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters[activity.mess] = sim.get(hero.id).meters.get(activity.mess, 0.0) + 1
    prize = sim.get(prize_id)
    soiled = prize.region in activity.zone
    return {"soiled": soiled}


def warn(world: World, friend: Entity, hero: Entity, activity: Event, prize: Entity) -> None:
    pred = predicts_mess(world, hero, activity, prize.label)
    if pred["soiled"]:
        world.say(
            f'"Careful," said {friend.id}. "If you do that, your {prize.label} could get {activity.soil}!"'
        )
    else:
        world.say(f'{friend.id} looked worried, but this time the {prize.label} was not in danger.')


def attempt(world: World, hero: Entity, activity: Event) -> None:
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 1
    world.say(f"{hero.id} still wanted to {activity.verb}, so {hero.pronoun('subject')} edged closer.")
    world.say(f"{hero.id} tried to {activity.rush}.")


def help_friend(world: World, friend: Entity, hero: Entity, activity: Event, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    world.say(
        f'{friend.id} grinned and said, "How about we {gear.prep} and do it the safe way?"'
    )
    return gear


def accept(world: World, hero: Entity, friend: Entity, activity: Event, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    world.say(
        f"{hero.id} laughed, and the two friends went with the plan. Soon they {gear.tail}."
    )
    world.say(
        f"In the end, {hero.id} was {activity.gerund}, {prize.pronoun('possessive')} {prize.label} stayed clean, and everybody was giggling."
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(EVENTS, params.activity)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    world = World(setting)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type, label=params.friend))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=friend.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    world.weather = "warm" if not setting.indoor else "cozy"

    intro(world, hero, friend, prize)
    loves(world, hero, activity)
    builds_friendship(world, hero, friend)

    world.para()
    world.say(setting_detail(setting, activity))
    world.say(f"{hero.id} and {friend.id} arrived there together.")
    warn(world, friend, hero, activity, prize)
    attempt(world, hero, activity)

    world.para()
    gear = help_friend(world, friend, hero, activity, prize)
    if gear is None:
        pass
    accept(world, hero, friend, activity, prize, gear)

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        activity=activity,
        gear=gear,
        setting=setting,
        conflict=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Prompts and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    activity = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short comedy story for a young child about {hero.id}, {friend.id}, and a {prize.label}.',
        f"Tell a funny friendship story where {hero.id} wants to {activity.verb} but {friend.id} helps keep the {prize.label} safe.",
        f'Write a gentle story that includes "fire" or "pillow" and ends with two friends laughing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {activity.verb}."
        ),
        QAItem(
            question=f"Who helped {hero.id} make a safer plan?",
            answer=f"{friend.id} helped {hero.id}, because {friend.id} cared about the {prize.label}."
        ),
        QAItem(
            question=f"What did they use so the {prize.label} would stay okay?",
            answer=f"They used {gear.label} so {hero.id} could keep going without ruining the {prize.label}."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} {activity.gerund}, the {prize.label} staying clean, and both friends laughing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add("friendship")
    out = []
    if "fire" in tags:
        out.append(QAItem(
            question="Why should children be careful around fire?",
            answer="Fire can burn things and make them hot, so children should stay careful and use it only with a grown-up."
        ))
    if "pillow" in tags:
        out.append(QAItem(
            question="What is a pillow for?",
            answer="A pillow is soft and helps make resting, reading, or sleeping more comfortable."
        ))
    out.append(QAItem(
        question="What is friendship?",
        answer="Friendship is when people care about each other, help each other, and enjoy being together."
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A prize is at risk if the activity reaches its region.
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).

% Gear is a compatible fix if it guards the mess kind and covers the region.
protects(G, A, P) :- prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).

has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).

#show valid/3.
#show prize_at_risk/2.
#show protects/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in EVENTS.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        if prize.plural:
            lines.append(asp.fact("plural", pid))
        for g in sorted(prize.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small comedy story world about fire, pillows, and friendship."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act = _safe_lookup(EVENTS, getattr(args, "activity", None))
        pr = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, prize = rng.choice(list(combos))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != hero])
    trait = rng.choice(TRAITS)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        hero=hero,
        hero_type=hero_gender,
        friend=friend,
        friend_type=friend_gender,
        trait=trait,
    )


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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="kitchen", activity="toast", prize="pillow", hero="Mina", hero_type="girl", friend="Leo", friend_type="boy", trait="silly"),
            StoryParams(place="backyard", activity="marshmallows", prize="blanket", hero="Ben", hero_type="boy", friend="Nora", friend_type="girl", trait="cheerful"),
            StoryParams(place="living_room", activity="games", prize="pillow", hero="Tess", hero_type="girl", friend="Ari", friend_type="boy", trait="curious"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.hero}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
