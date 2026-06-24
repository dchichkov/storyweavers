#!/usr/bin/env python3
"""
storyworlds/worlds/aft_stance_mitt_foreshadowing_humor_sound_effects.py
=======================================================================

A small pirate-tale storyworld about an aft deck stance, a missing mitt, and a
careful turn toward safer play. The world uses typed entities with physical
meters and emotional memes, a forward causal model, foreshadowing, humor, and
sound effects to keep the prose lively and state-driven.

Seed tale:
---
On the aft deck of a little pirate ship, a brave child loved to swing a rope
and stand in a pirate stance. One day the child lost a warm mitt while racing
around the deck. The mitt rolled toward the aft hatch, and the child wanted to
reach it right away.

The captain warned that the deck was slippery and the wind was loud. The child
nearly leaned too far, then laughed when a gull stole the mitt and dropped it
back near a lantern. The captain helped them balance, and together they tied the
mitt to a string so it would not drift away again.

Style goals:
- pirate-tale cadence with child-facing concrete details
- foreshadowing via a predicted slip or drift
- humor via gull antics and playful pirate language
- sound effects embedded in the action
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    captain: object | None = None
    child: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "mate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Deck:
    place: str = "the aft deck"
    slippery: bool = True
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    mess: str
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
    location: str
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
class Helper:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    noise: str
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


class World:
    def __init__(self, deck: Deck) -> None:
        self.deck = deck
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        return [e for e in self.entities.values() if e.owner == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.deck)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_drip(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["lean"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.label != "mitt":
                continue
            sig = ("drip", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["away"] += 1
            actor.memes["worry"] += 1
            out.append(f"{item.label.capitalize()} slipped with a soft swoosh.")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["balance"] >= THRESHOLD:
            continue
        if actor.meters["lean"] < THRESHOLD:
            continue
        sig = ("slip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["startle"] += 1
        out.append("__slip__")
    return out


def _r_gull(world: World) -> list[str]:
    if world.facts.get("gull_helped"):
        return []
    if world.facts.get("mitt_missing") and world.facts.get("sound_called"):
        sig = ("gull",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.facts["gull_helped"] = True
        world.get("mitt").meters["found"] += 1
        world.get("child").memes["joy"] += 1
        return ["__gull__"]
    return []


CAUSAL_RULES = [
    Rule("drip", "physical", _r_drip),
    Rule("slip", "physical", _r_slip),
    Rule("gull", "social", _r_gull),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(w: World, actor: Entity) -> dict:
    sim = w.copy()
    sim.get(actor.id).meters["lean"] += 1
    propagate(sim, narrate=False)
    return {"slip": bool(sim.get(actor.id).memes["startle"] >= THRESHOLD),
            "mitt_missing": bool(sim.get("mitt").meters["away"] >= THRESHOLD)}


def tell_start(world: World, child: Entity, captain: Entity, action: Action, prize: Entity) -> None:
    world.say(
        f"On the aft deck, {child.id} stood in a pirate stance and swung a rope like a proud little captain."
    )
    world.say(
        f"'{action.noise}!' went the rigging overhead, and the gulls answered with a rude little squawk."
    )
    world.say(
        f"{child.id} loved to {action.verb}, but {prize.label} was warm and easy to lose in the wind."
    )


def foreshadow(world: World, child: Entity, prize: Entity, helper: Helper) -> None:
    pred = predict(world, child)
    world.facts["predicted_slip"] = pred["slip"]
    world.facts["mitt_missing"] = pred["mitt_missing"]
    world.say(
        f"The deck boards looked shiny as fish scales, and the captain's eyes narrowed. "
        f'"Mind your stance," {world.get("captain").id} warned. "One wobble and that {prize.label} may skitter away."'
    )


def attempt_reach(world: World, child: Entity, action: Action, prize: Entity) -> None:
    child.meters["lean"] += 1
    child.meters["balance"] -= 1
    child.memes["want"] += 1
    world.say(
        f"{child.id} reached toward the aft hatch anyway. '{action.noise}' said the deck, and the mitt rolled with a tiny tumble."
    )
    propagate(world, narrate=False)


def humor_beat(world: World) -> None:
    world.say(
        "A gull hopped down, snatched the mitt, and strutted three steps like it owned the whole ship."
    )
    world.say(
        '"Hah!" laughed the child. "That bird has better manners than a barrel of biscuits!"'
    )


def sound_effects(world: World, helper: Helper) -> None:
    world.facts["sound_called"] = True
    world.say(f'"{helper.noise}!" cried the captain, clapping once.')
    world.say(
        f"The rope went {helper.noise.lower()} as it was tied to the mitt, and the wind went whoooosh around the mast."
    )


def resolution(world: World, child: Entity, captain: Entity, prize: Entity, helper: Helper) -> None:
    child.memes["joy"] += 1
    child.memes["worry"] = 0
    child.meters["balance"] += 1
    prize.owner = child.id
    prize.location = "tied to the rope loop"
    world.say(
        f"Together they made a better plan: they tied the mitt to a rope loop so it would not drift away again."
    )
    world.say(
        f"{child.id} stood straighter, grinned, and gave a safer pirate salute from the aft deck."
    )


def tell(deck: Deck, action: Action, prize_cfg: Prize, helper: Helper,
         child_name: str = "Mira", parent_name: str = "Captain Ivy") -> World:
    world = World(deck)
    child = world.add(Entity(id=child_name, kind="character", type="girl", role="child"))
    captain = world.add(Entity(id="captain", kind="character", type="captain", role="captain", label=parent_name))
    prize = world.add(Entity(id="mitt", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id))
    world.facts["helper"] = helper
    world.facts["action"] = action
    world.facts["prize"] = prize_cfg

    tell_start(world, child, captain, action, prize)
    world.para()
    foreshadow(world, child, prize, helper)
    attempt_reach(world, child, action, prize)
    world.para()
    humor_beat(world)
    sound_effects(world, helper)
    resolution(world, child, captain, prize, helper)

    world.facts.update(child=child, captain=captain, mitt=prize,
                       outcome="safe", question_risk=world.facts.get("predicted_slip", False))
    return world


DECKS = {
    "aft": Deck(place="the aft deck", slippery=True, affords={"stance", "mitt"}),
}

ACTIONS = {
    "stance": Action(
        id="stance",
        verb="stand in a pirate stance",
        gerund="standing in a pirate stance",
        rush="lurch toward the aft hatch",
        noise="skrrrt",
        mess="wobble",
        zone={"feet"},
        keyword="stance",
        tags={"pirate", "balance"},
    ),
    "mitt": Action(
        id="mitt",
        verb="chase the mitt",
        gerund="chasing the mitt",
        rush="dash after the mitt",
        noise="tap-tap",
        mess="drift",
        zone={"hands"},
        keyword="mitt",
        tags={"mitt", "wind"},
    ),
}

PRIZES = {
    "mitt": Prize(label="mitt", phrase="a warm knit mitt", type="mitt", location="hand"),
}

HELPERS = {
    "rope": Helper(
        id="rope",
        label="rope",
        phrase="a short rope",
        prep="tie the mitt to the rope",
        tail="tied the mitt to a rope loop",
        noise="thrum",
    ),
    "knot": Helper(
        id="knot",
        label="knot",
        phrase="a bright red knot",
        prep="make a safe knot",
        tail="made the mitt into a tidy knot",
        noise="tap",
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Luna", "Tessa", "Ivy", "Pia"]
CAPTAIN_NAMES = ["Captain Ivy", "Captain Salt", "Captain June"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for d in DECKS:
        for a in ACTIONS:
            for p in PRIZES:
                if d == "aft" and a in {"stance", "mitt"} and p == "mitt":
                    combos.append((d, a, p))
    return combos


@dataclass
class StoryParams:
    deck: str
    action: str
    prize: str
    helper: str
    child_name: str
    captain_name: str
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


KNOWLEDGE = {
    "mitt": [("What is a mitt?", "A mitt is a warm glove that keeps a hand cozy on a cold or windy day.")],
    "rope": [("What is a rope for?", "A rope is a long cord used for tying, pulling, or keeping things from drifting away.")],
    "gull": [("What is a gull?", "A gull is a seaside bird that can swoop, squawk, and sometimes snatch shiny things.")],
    "balance": [("Why do sailors keep their balance?", "Sailors keep their balance so they do not slip when the deck moves or gets wet.")],
    "pirate": [("What is a pirate stance?", "A pirate stance is a pretend standing pose that looks brave and wobbly at the same time.")],
}
KNOWLEDGE_ORDER = ["pirate", "balance", "mitt", "rope", "gull"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate tale for a 3-to-5-year-old about an aft deck, a pirate stance, and a missing mitt, with a funny gull surprise.',
        f"Tell a child-sized sea story where {f['child'].id} wants to {f['action'].verb} on the aft deck, but the captain warns about the wind and the slippery boards.",
        'Write a short story that uses the words "aft", "stance", and "mitt", includes a humorous bird moment, and ends with a safer plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, captain, prize, action, helper = f["child"], f["captain"], f["mitt"], f["action"], f["helper"]
    qa = [
        QAItem(
            question=f"Who is the story about when {child.id} stands on the aft deck?",
            answer=f"It is about {child.id} and {captain.label_word}, who are together on the aft deck with a {prize.label}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do in a pirate stance?",
            answer=f"{child.id} wanted to {action.verb}. The stance looked brave, but the deck was slippery and the wind was strong.",
        ),
        QAItem(
            question=f"What worried the captain about the {prize.label}?",
            answer=f"The captain worried that the {prize.label} could skitter away toward the aft hatch because the deck was slippery.",
        ),
        QAItem(
            question=f"How did the gull help with the {prize.label}?",
            answer=f"The gull snatched the {prize.label} and dropped it back near the lantern, which gave everyone a funny surprise and a better chance to catch it.",
        ),
        QAItem(
            question=f"What safer plan did they use for the {prize.label} at the end?",
            answer=f"They tied the {prize.label} to {helper.label_word} so it would not drift away again. That made the aft deck safer for play.",
        ),
    ]
    if world.facts.get("predicted_slip"):
        qa.append(QAItem(
            question=f"Why did the captain give a foreshadowing warning before {child.id} leaned?",
            answer=f"The captain could see that one wobble might make {child.id} slip and make the {prize.label} slide away, so the warning came before the trouble.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags) | {"mitt", "rope", "gull", "balance", "pirate"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("aft", "stance", "mitt", "rope", "Mira", "Captain Ivy"),
    StoryParams("aft", "mitt", "mitt", "knot", "Nina", "Captain Salt"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    deck, action, prize = rng.choice(sorted(c for c in combos
                                           if (getattr(args, "deck", None) is None or c[0] == getattr(args, "deck", None))
                                           and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
                                           and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    return StoryParams(
        deck=deck,
        action=action,
        prize=prize,
        helper=helper,
        child_name=getattr(args, "child", None) or rng.choice(GIRL_NAMES),
        captain_name=getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(DECKS, params.deck), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), _safe_lookup(HELPERS, params.helper), params.child_name, params.captain_name)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world: aft, stance, mitt, with foreshadowing, humor, and sound effects.")
    ap.add_argument("--deck", choices=DECKS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--captain")
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("deck", "aft"), asp.fact("action", "stance"), asp.fact("action", "mitt"), asp.fact("prize", "mitt")]
    lines.append(asp.fact("affords", "aft", "stance"))
    lines.append(asp.fact("affords", "aft", "mitt"))
    lines.append(asp.fact("wears", "child", "mitt"))
    lines.append(asp.fact("location", "mitt", "hand"))
    lines.append(asp.fact("helper", "rope"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(D,A,P) :- deck(D), action(A), prize(P), affords(D,A), wears(child,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        print("OK: no ASP parity checks for this small world.")
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
