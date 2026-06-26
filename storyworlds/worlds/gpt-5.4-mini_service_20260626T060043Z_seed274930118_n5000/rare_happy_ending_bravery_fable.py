#!/usr/bin/env python3
"""
storyworlds/worlds/rare_happy_ending_bravery_fable.py
======================================================

A small fable-style storyworld about rare things, bravery, and a happy ending.

Premise:
- A small animal hero wants to do something kind.
- A rare prize or bundle is at risk from a challenge.
- A wise helper notices the danger.
- The hero chooses bravery, accepts help, and the story ends warmly.

This world is intentionally narrow: it favors a few strong, fable-like
premises over many weak ones.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid: object | None = None
    hero: object | None = None
    mentor: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ("weight", "damage", "distance", "shiver"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "bravery", "hope", "relief", "worry", "love"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "hare", "deer", "squirrel", "fox", "bird"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case] if self.type in {"mouse", "rabbit", "hare", "squirrel", "bird"} else {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""
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
class Challenge:
    id: str
    verb: str
    gerund: str
    danger: str
    zone: set[str]
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
    plural: bool = False
    rare: bool = True
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
class Aid:
    id: str
    label: str
    covers: set[str]
    blocks: set[str]
    prep: str
    tail: str
    plural: bool = False
    gentle: str = ""
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.challenge_zone: set[str] = set()
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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.challenge_zone = set(self.challenge_zone)
        clone.paragraphs = [[]]
        return clone


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for chal in CHALLENGES.values():
            if actor.meters[chal.id] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.challenge_zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("spoil", actor.id, item.id, chal.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["damage"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} was spoiled by the {chal.id}.")
    return out


def _r_fear_to_bravery(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["bravery"] >= THRESHOLD:
            continue
        if actor.memes["fear"] >= THRESHOLD and actor.memes["hope"] >= THRESHOLD:
            sig = ("brave", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["bravery"] += 1
            out.append(f"{actor.id} stood taller and found a brave heart.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["relief"] >= THRESHOLD:
            continue
        if actor.memes["bravery"] >= THRESHOLD and actor.memes["worry"] >= THRESHOLD:
            sig = ("relief", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["relief"] += 1
            out.append(f"{actor.id} felt relief once the danger had a kinder path.")
    return out


RULES = [_r_spoil, _r_fear_to_bravery, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(challenge: Challenge, prize: Prize) -> bool:
    return prize.region in challenge.zone


def select_aid(challenge: Challenge, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if challenge.id in aid.blocks and prize.region in aid.covers:
            return aid
    return None


def predict(world: World, actor: Entity, challenge: Challenge, prize_id: str) -> dict:
    sim = world.copy()
    _do_challenge(sim, sim.get(actor.id), challenge, narrate=False)
    prize = sim.entities[prize_id]
    return {"damaged": prize.meters["damage"] >= THRESHOLD}


def _do_challenge(world: World, actor: Entity, challenge: Challenge, narrate: bool = True) -> None:
    if challenge.id not in world.setting.affords:
        return
    world.challenge_zone = set(challenge.zone)
    actor.meters[challenge.id] += 1
    actor.memes["fear"] += 1
    actor.memes["worry"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity) -> None:
    world.say(
        f"In {world.setting.place}, there lived a little {hero.type} named {hero.id}, "
        f"who loved to do the kind thing even when the path looked hard."
    )


def rare_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"One day, {hero.id} was trusted with {hero.pronoun('possessive')} {prize.label}, "
        f"a rare treasure that should be carried with care."
    )


def warning(world: World, mentor: Entity, hero: Entity, challenge: Challenge, prize: Entity) -> None:
    pred = predict(world, hero, challenge, prize.id)
    if pred["damaged"]:
        world.say(
            f'"If you go to {challenge.verb}, your {prize.label} may be harmed," '
            f"{mentor.label or mentor.id} said. "
            f'"A wise heart thinks before it leaps."'
        )


def hesitant(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} looked at the road and trembled a little, for the {challenge.danger} seemed large."
    )
    world.say(f"Still, {hero.pronoun().capitalize()} wanted to {challenge.verb}, because kindness mattered more than hiding.")


def choose_brave(world: World, hero: Entity, mentor: Entity, challenge: Challenge) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{mentor.label or mentor.id} offered a steady paw and a soft word, and {hero.id} chose to be brave."
    )


def accept_aid(world: World, hero: Entity, mentor: Entity, challenge: Challenge, prize: Entity, aid_def: Aid) -> None:
    aid = world.add(Entity(
        id=aid_def.id,
        type="thing",
        label=aid_def.label,
        owner=hero.id,
        caretaker=mentor.id,
        protective=True,
        covers=set(aid_def.covers),
        plural=aid_def.plural,
    ))
    aid.worn_by = hero.id
    hero.memes["bravery"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"They used {aid_def.label} and went on together. {aid_def.gentle}"
    )
    _do_challenge(world, hero, challenge, narrate=True)
    hero.memes["relief"] += 1


def ending(world: World, hero: Entity, mentor: Entity, prize: Entity, challenge: Challenge) -> None:
    world.say(
        f"At last, {hero.id} finished the task, and {hero.pronoun('possessive')} {prize.label} stayed safe."
        f" {hero.id} smiled at {mentor.label or mentor.id}, because bravery had led to a happy ending."
    )
    world.say(
        f"From that day on, the little {hero.type} was not the kind who never felt fear; "
        f"{hero.pronoun().capitalize()} was the kind who acted kindly anyway."
    )


def tell(setting: Setting, challenge: Challenge, prize_cfg: Prize, hero_name: str, hero_type: str, mentor_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label=f"the {mentor_type}"))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    opening(world, hero)
    rare_prize(world, hero, prize)
    world.para()
    warning(world, mentor, hero, challenge, prize)
    hesitant(world, hero, challenge)
    choose_brave(world, hero, mentor, challenge)
    world.para()
    aid_def = select_aid(challenge, prize)
    if aid_def:
        accept_aid(world, hero, mentor, challenge, prize, aid_def)
    ending(world, hero, mentor, prize, challenge)

    world.facts.update(hero=hero, mentor=mentor, prize=prize, challenge=challenge, aid=aid_def, setting=setting)
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", kind="outdoor", affords={"cross_stream", "climb_hill"}, mood="bright"),
    "woods": Setting(place="the woods", kind="outdoor", affords={"cross_stream", "enter_cave"}, mood="shadowy"),
    "riverbank": Setting(place="the riverbank", kind="outdoor", affords={"cross_stream"}, mood="watery"),
}

CHALLENGES = {
    "cross_stream": Challenge(
        id="cross_stream",
        verb="cross the stream",
        gerund="crossing the stream",
        danger="cold water",
        zone={"feet", "legs"},
        tags={"water", "cold", "stream"},
    ),
    "climb_hill": Challenge(
        id="climb_hill",
        verb="climb the hill",
        gerund="climbing the hill",
        danger="sharp stones",
        zone={"feet", "legs"},
        tags={"hill", "stones"},
    ),
    "enter_cave": Challenge(
        id="enter_cave",
        verb="enter the cave",
        gerund="entering the cave",
        danger="dark echoes",
        zone={"torso"},
        tags={"dark", "echo", "cave"},
    ),
}

PRIZES = {
    "bell": Prize(id="bell", label="silver bell", phrase="a tiny silver bell", region="torso"),
    "seed": Prize(id="seed", label="golden seed", phrase="a rare golden seed", region="feet"),
    "cloak": Prize(id="cloak", label="leaf cloak", phrase="a delicate leaf cloak", region="torso"),
}

AIDS = [
    Aid(id="boots", label="little boots", covers={"feet"}, blocks={"cross_stream", "climb_hill"}, prep="put on the boots", tail="walked on", gentle="The boots kept the feet dry and steady."),
    Aid(id="lantern", label="a lantern", covers={"torso"}, blocks={"enter_cave"}, prep="carry the lantern", tail="went in", gentle="The lantern made the dark feel less scary."),
    Aid(id="rope", label="a soft rope", covers={"feet", "legs"}, blocks={"climb_hill"}, prep="tie on the rope", tail="climbed safely", gentle="The rope helped the little feet keep their balance."),
]

NAMES = ["Milo", "Nina", "Pip", "Tavi", "Luma", "Rowan", "Bram", "Fina"]
TYPES = ["mouse", "rabbit", "hare", "squirrel", "bird"]
MENTORS = ["tortoise", "owl", "badger", "deer"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    hero_type: str
    mentor_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ch in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(_safe_lookup(CHALLENGES, ch), prize) and select_aid(_safe_lookup(CHALLENGES, ch), prize):
                    combos.append((place, ch, prize_id))
    return combos


def explain_rejection(challenge: Challenge, prize: Prize) -> str:
    return f"(No story: {challenge.verb} does not create a believable danger for {prize.label}, so the fable would not have a real problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about rare things and brave hearts.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--mentor-type", choices=MENTORS)
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
    if getattr(args, "challenge", None) and getattr(args, "prize", None):
        ch, pr = _safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(ch, pr) and select_aid(ch, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        challenge=challenge,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(TYPES),
        mentor_type=getattr(args, "mentor_type", None) or rng.choice(MENTORS),
    )


ASP_RULES = r"""
prize_at_risk(C, P) :- challenge(C), prize(P), zone(C, R), region(P, R).
aid_fits(A, C, P) :- aid(A), prize_at_risk(C, P), blocks(A, C), covers(A, R), region(P, R).
valid(Place, C, P) :- affords(Place, C), prize_at_risk(C, P), aid_fits(_, C, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for ch in sorted(setting.affords):
            lines.append(asp.fact("affords", place, ch))
    for ch_id, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", ch_id))
        for z in sorted(ch.zone):
            lines.append(asp.fact("zone", ch_id, z))
    for pr_id, pr in PRIZES.items():
        lines.append(asp.fact("prize", pr_id))
        lines.append(asp.fact("region", pr_id, pr.region))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for b in sorted(aid.blocks):
            lines.append(asp.fact("blocks", aid.id, b))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children about a rare thing, a brave choice, and a happy ending in {f["setting"].place}.',
        f"Tell a gentle story where {f['hero'].id} must {f['challenge'].verb} to protect {f['prize'].label}.",
        f'Write a fable that uses the word "rare" and ends with bravery leading to a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, prize, challenge = f["hero"], f["mentor"], f["prize"], f["challenge"]
    return [
        QAItem(
            question=f"What rare thing did {hero.id} carry?",
            answer=f"{hero.id} carried {prize.phrase}, and it stayed safe to the end.",
        ),
        QAItem(
            question=f"Why did {mentor.label or mentor.id} worry about {hero.id}?",
            answer=f"{mentor.label or mentor.id} worried because {hero.id} had to {challenge.verb}, and the danger could have spoiled the {prize.label}.",
        ),
        QAItem(
            question=f"What changed when {hero.id} chose bravery?",
            answer=f"{hero.id} stopped trembling, accepted help, and finished the task with a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does brave mean?",
            answer="Brave means being willing to do something hard or scary when it is the right thing to do.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHALLENGES, params.challenge), _safe_lookup(PRIZES, params.prize), params.name, params.hero_type, params.mentor_type)
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
    StoryParams(place="meadow", challenge="cross_stream", prize="seed", name="Milo", hero_type="mouse", mentor_type="owl"),
    StoryParams(place="woods", challenge="enter_cave", prize="bell", name="Nina", hero_type="rabbit", mentor_type="tortoise"),
    StoryParams(place="riverbank", challenge="cross_stream", prize="cloak", name="Pip", hero_type="hare", mentor_type="badger"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:\n")
        for place, ch, pr in triples:
            print(f"  {place:10} {ch:14} {pr}")
        return

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
