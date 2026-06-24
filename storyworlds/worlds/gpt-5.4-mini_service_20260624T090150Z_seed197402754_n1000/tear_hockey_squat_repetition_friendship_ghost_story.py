#!/usr/bin/env python3
"""
A small storyworld for a ghost-story-style hockey tale with repetition and friendship.

Core premise:
- A child and a friendly ghost meet at a quiet hockey rink.
- A tiny torn thing causes trouble: the child's lucky ribbon tears.
- The ghost helps by repeating a simple squat-and-slide practice that steadies nerves.
- Repetition turns worry into confidence, and friendship makes the ending feel warm.

This file follows the Storyweavers world contract:
- self-contained stdlib script
- shared results imported eagerly
- asp imported lazily in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    friend: object | None = None
    hero: object | None = None
    ribbon: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    quiet: bool = True
    indoors: bool = True
    echo: bool = False
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
class Action:
    id: str
    verb: str
    gerund: str
    repeat_line: str
    mess: str
    zone: set[str]
    tension: str
    resolve_line: str
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
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []
        self.zone: set[str] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return False


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_tear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("tear", 0.0) < THRESHOLD:
            continue
        sig = ("tear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.id}'s worry rose like a cold draft.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("practice", 0.0) < 2 * THRESHOLD:
            continue
        sig = ("practice", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["confidence"] = actor.memes.get("confidence", 0.0) + 1
        out.append(f"After repeating it again and again, {actor.id} looked steadier.")
    return out


CAUSAL_RULES = [Rule("tear", _r_tear), Rule("repetition", _r_repetition)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_helper(action: Action, prize: Prize) -> Optional[Helper]:
    for h in HELPERS:
        if action.mess in h.guards and prize.region in h.covers:
            return h
    return None


def predict(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = World(world.place)
    import copy
    sim.entities = copy.deepcopy(world.entities)
    sim.fired = set(world.fired)
    sim.zone = set(world.zone)
    sim.facts = dict(world.facts)
    sim.get(actor.id).meters[action.mess] = sim.get(actor.id).meters.get(action.mess, 0.0) + 1
    sim.get(actor.id).meters["practice"] = sim.get(actor.id).meters.get("practice", 0.0) + 2
    prize = sim.entities[prize_id]
    if action.mess == "tear" and prize.region in action.zone:
        prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
    return {
        "soiled": bool(prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "confidence": sim.get(actor.id).memes.get("confidence", 0.0),
    }


def act_practice(world: World, actor: Entity, action: Action) -> None:
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1
    actor.meters["practice"] = actor.meters.get("practice", 0.0) + 1
    world.zone = set(action.zone)
    world.say(f"{actor.id} tried once, then tried again, then tried one more time.")
    world.say(action.repeat_line)
    propagate(world)


def intro(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    world.say(
        f"On a hush-dark night, {hero.id} met {friend.id} at the rink where the ice shone pale."
    )
    world.say(
        f"{hero.id} liked {prize.phrase}, but {friend.id} liked to float nearby and keep company."
    )


def trouble(world: World, hero: Entity, friend: Entity, action: Action, prize: Entity) -> None:
    hero.meters[action.mess] = hero.meters.get(action.mess, 0.0) + 1
    world.zone = set(action.zone)
    world.say(
        f"Then the ribbon on {hero.pronoun('possessive')} {prize.label} gave a little tear."
    )
    world.say(
        f"{hero.id} wanted to {action.verb}, but the torn edge made {hero.pronoun('object')} feel shaky."
    )
    world.say(
        f"{friend.id} drifted closer and whispered, '{action.tension}'"
    )
    propagate(world)


def offer_help(world: World, hero: Entity, friend: Entity, action: Action, prize: Prize) -> Optional[Helper]:
    helper = select_helper(action, prize)
    if helper is None:
        return None
    world.say(
        f'{friend.id} smiled and said, "{helper.prep}, and we will go back to the rink together."'
    )
    return helper


def resolve(world: World, hero: Entity, friend: Entity, action: Action, prize: Prize, helper: Helper) -> None:
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} nodded, and the two of them followed the plan."
    )
    world.say(
        f"{helper.tail}. Soon {hero.id} was {action.gerund}, and {prize.label} stayed safe."
    )
    world.say(
        f"At the end, {friend.id} and {hero.id} laughed softly while the rink echoed like a friendly cave."
    )


def tell(place: Place, action: Action, prize: Prize, hero_name: str, hero_type: str, friend_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["small", "brave"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="ghost", label="the friendly ghost"))
    ribbon = world.add(Entity(id="prize", type="ribbon", label=prize.label, phrase=prize.phrase, region=prize.region, plural=prize.plural))
    friend.memes["friendship"] = 1.0

    intro(world, hero, friend, ribbon)
    world.para()
    trouble(world, hero, friend, action, ribbon)
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    act_practice(world, hero, action)
    world.para()
    helper = offer_help(world, hero, friend, action, ribbon)
    if helper:
        resolve(world, hero, friend, action, ribbon, helper)
    world.facts.update(hero=hero, friend=friend, prize=ribbon, action=action, place=place, helper=helper)
    return world


SETTINGS = {
    "rink": Place(id="rink", label="the old hockey rink", quiet=True, indoors=True, echo=True, affords={"hockey", "squat"}),
    "basement": Place(id="basement", label="the basement rink room", quiet=True, indoors=True, echo=True, affords={"squat"}),
    "yard": Place(id="yard", label="the snowy yard", quiet=True, indoors=False, echo=False, affords={"hockey", "squat"}),
}

ACTIONS = {
    "hockey": Action(
        id="hockey",
        verb="play hockey",
        gerund="playing hockey",
        repeat_line="They practiced the same glide, the same swing, and the same turn until it felt easy.",
        mess="tear",
        zone={"torso"},
        tension="A torn ribbon can tug at your heart when you are trying to be brave.",
        resolve_line="The puck could wait.",
        tags={"hockey", "repeat"},
    ),
    "squat": Action(
        id="squat",
        verb="do slow squats",
        gerund="doing slow squats",
        repeat_line="Down, up, down, up, down, up; each squat made the body feel more ready.",
        mess="tear",
        zone={"legs"},
        tension="Sometimes a little repetition can calm a shaky night.",
        resolve_line="The knees learned the rhythm.",
        tags={"squat", "repeat"},
    ),
}

PRIZES = {
    "scarf": Prize(id="scarf", label="scarf", phrase="a soft red scarf", region="torso"),
    "jersey": Prize(id="jersey", label="jersey", phrase="a bright team jersey", region="torso"),
    "pants": Prize(id="pants", label="pants", phrase="new hockey pants", region="legs"),
}

HELPERS = [
    Helper(id="scarfwrap", label="a scarf wrap", prep="we can wrap the tear with a warm scarf first", tail="They wrapped the scarf around the rip", covers={"torso"}, guards={"tear"}),
    Helper(id="knee_pad", label="knee pads", prep="we can put on knee pads and practice the squat steps first", tail="They buckled on the knee pads and repeated the squat steps", covers={"legs"}, guards={"tear"}),
]

HERO_NAMES = ["Mina", "Rowan", "Ivy", "Noah", "Tess", "Eli"]
GHOST_NAMES = ["Boo", "Moss", "Pip", "Echo"]
TRAITS = ["quiet", "curious", "gentle", "brave"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    hero_name: str
    hero_type: str
    ghost_name: str
    trait: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, p in SETTINGS.items():
        for action, a in ACTIONS.items():
            if action not in p.affords:
                continue
            for prize, pr in PRIZES.items():
                if prize_at_risk(a, pr) and select_helper(a, pr):
                    out.append((place, action, prize))
    return out


KNOWLEDGE = {
    "hockey": [("What is hockey?", "Hockey is a game where players use sticks to guide a puck on ice or on a slippery surface.")],
    "squat": [("What is a squat?", "A squat is a bend-and-stand exercise that helps legs get stronger.")],
    "tear": [("What does tear mean?", "A tear is a small rip or split in cloth or paper.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other, help each other, and enjoy being together.")],
    "repetition": [("What is repetition?", "Repetition means doing the same thing again and again. It can help you learn or feel ready.")],
    "ghost": [("What is a ghost in a story?", "A ghost in a story is often a spooky or magical character, and sometimes it can be kind and helpful.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story about {f['hero'].id} and a friendly ghost at {f['place'].label}.",
        f"Tell a short story where {f['hero'].id} needs repetition to feel ready for {f['action'].verb}.",
        f"Write a child-friendly story with hockey, a tear, and a friendship that helps the ending feel safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, action, place = f["hero"], f["friend"], f["prize"], f["action"], f["place"]
    helper = f.get("helper")
    return [
        QAItem(
            question=f"Where did {hero.id} meet {friend.id}?",
            answer=f"{hero.id} met {friend.id} at {place.label}. It was a quiet place with a spooky, echoing feeling.",
        ),
        QAItem(
            question=f"What happened to {hero.pronoun('possessive')} {prize.label}?",
            answer=f"The ribbon on {hero.pronoun('possessive')} {prize.label} gave a little tear, so {hero.id} felt shaky before the game.",
        ),
        QAItem(
            question=f"What did {hero.id} repeat before trying to {action.verb}?",
            answer=f"{hero.id} repeated the practice steps again and again, and that repetition helped the night feel less scary.",
        ),
    ] + (
        [
            QAItem(
                question=f"How did {friend.id} help {hero.id} feel better?",
                answer=f"{friend.id} helped by offering {helper.label} and staying close while {hero.id} practiced.",
            ),
            QAItem(
                question=f"What changed at the end of the story?",
                answer=f"At the end, {hero.id} felt braver, the tear was managed with help, and the two friends finished together with a warm feeling.",
            ),
        ] if helper else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    tags.add("friendship")
    tags.add("ghost")
    out: list[QAItem] = []
    for t in ["hockey", "squat", "tear", "repetition", "friendship", "ghost"]:
        if t in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[t])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- action(A), prize(P), zone(A, R), region(P, R).
has_help(A, P) :- prize_at_risk(A, P), helper(H), guards(H, tear), covers(H, R), region(P, R).
valid(Place, A, P) :- place(Place), affords(Place, A), prize_at_risk(A, P), has_help(A, P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, g))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, c))
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
    print("MISMATCH between clingo and python:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A quiet ghost-story hockey world about repetition and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--ghost")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(filtered))
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    ghost_name = getattr(args, "ghost", None) or rng.choice(GHOST_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    return StoryParams(place=place, action=action, prize=prize, hero_name=hero_name, hero_type=gender, ghost_name=ghost_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.hero_name, params.hero_type, params.ghost_name)
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
    StoryParams(place="rink", action="hockey", prize="jersey", hero_name="Mina", hero_type="girl", ghost_name="Echo", trait="curious"),
    StoryParams(place="basement", action="squat", prize="pants", hero_name="Eli", hero_type="boy", ghost_name="Boo", trait="gentle"),
    StoryParams(place="yard", action="hockey", prize="scarf", hero_name="Ivy", hero_type="girl", ghost_name="Pip", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, action, prize) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
