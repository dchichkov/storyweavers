#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/protect_alert_bravery_slice_of_life.py
=================================================================

A standalone story world about an ordinary afternoon, an open way out, and one
child choosing to be brave enough to notice danger, stay alert, and protect
someone smaller.

The little domain:
- A child is with a grown-up during a normal home chore.
- A gate or door is left ajar for a moment.
- A toddler sibling or small pet is tempted toward the opening by something
  ordinary and exciting.
- The child feels a jolt of fear, becomes alert, and tries to protect the
  wanderer while calling for help.
- A grown-up secures the opening, and the ending image proves the family has
  changed what they do next.

The world enforces reasonableness:
- Lures only pair with wanderers who would honestly follow them.
- Protective moves must fit the wanderer (holding a toddler's hand, scooping up
  a puppy, etc.).
- Outcome is determined by bravery, how strong the lure is, the wanderer's
  speed, the chosen protect move, and how quickly the grown-up can join in.

Run it
------
    python storyworlds/worlds/gpt-5.4/protect_alert_bravery_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/protect_alert_bravery_slice_of_life.py --place front_yard --wanderer puppy --lure leaf
    python storyworlds/worlds/gpt-5.4/protect_alert_bravery_slice_of_life.py --wanderer brother --move scoop_up
    python storyworlds/worlds/gpt-5.4/protect_alert_bravery_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/protect_alert_bravery_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/protect_alert_bravery_slice_of_life.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/protect_alert_bravery_slice_of_life.py --json
    python storyworlds/worlds/gpt-5.4/protect_alert_bravery_slice_of_life.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
ADULT_SPEED = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        animal = {"puppy", "dog", "kitten", "cat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    barrier: str
    outside: str
    chore: str
    opening_phrase: str
    ending_spot: str
    distance: int
    image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Wanderer:
    id: str
    label: str
    type: str
    noun: str
    relation: str
    gait: str
    speed: int
    target_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Lure:
    id: str
    label: str
    appearance: str
    call: str
    pull: int
    target_tags: set[str] = field(default_factory=set)
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class ProtectMove:
    id: str
    label: str
    modes: set[str] = field(default_factory=set)
    speed: int = 0
    brave_bonus: int = 0
    approach: str = ""
    contact: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Bravery:
    id: str
    label: str
    value: int
    line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_open_way_risk(world: World) -> list[str]:
    out: list[str] = []
    barrier = world.get("barrier")
    wanderer = world.get("wanderer")
    hero = world.get("hero")
    if barrier.meters["open"] < THRESHOLD or wanderer.meters["moving_out"] < THRESHOLD:
        return out
    sig = ("risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    barrier.meters["risk"] += 1
    wanderer.meters["risk"] += 1
    hero.memes["fear"] += 1
    hero.memes["alert"] += 1
    out.append("__risk__")
    return out


def _r_secured_relief(world: World) -> list[str]:
    out: list[str] = []
    barrier = world.get("barrier")
    wanderer = world.get("wanderer")
    hero = world.get("hero")
    adult = world.get("adult")
    if barrier.meters["secured"] < THRESHOLD or wanderer.meters["protected"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] += 1
    adult.memes["relief"] += 1
    wanderer.memes["calm"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="open_way_risk", tag="physical", apply=_r_open_way_risk),
    Rule(name="secured_relief", tag="emotional", apply=_r_secured_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


def lure_matches(wanderer: Wanderer, lure: Lure) -> bool:
    return bool(wanderer.target_tags & lure.target_tags)


def move_matches(wanderer: Wanderer, move: ProtectMove) -> bool:
    return bool(wanderer.tags & move.modes)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for wanderer_id, wanderer in WANDERERS.items():
            for lure_id, lure in LURES.items():
                if not lure_matches(wanderer, lure):
                    continue
                for move_id, move in PROTECT_MOVES.items():
                    if move_matches(wanderer, move):
                        combos.append((place_id, wanderer_id, lure_id, move_id))
    return combos


def readiness(bravery: Bravery, move: ProtectMove) -> int:
    return bravery.value + 1 + move.brave_bonus


def adult_in_time(params: "StoryParams") -> bool:
    place = PLACES[params.place]
    wanderer = WANDERERS[params.wanderer]
    return (ADULT_SPEED - params.delay) >= wanderer.speed and place.distance >= wanderer.speed


def hero_in_time(params: "StoryParams") -> bool:
    wanderer = WANDERERS[params.wanderer]
    move = PROTECT_MOVES[params.move]
    bravery = BRAVERIES[params.bravery]
    lure = LURES[params.lure]
    return readiness(bravery, move) >= lure.pull and move.speed >= wanderer.speed


def outcome_of(params: "StoryParams") -> str:
    if hero_in_time(params):
        return "hero_protects"
    if adult_in_time(params):
        return "adult_protects"
    return "unsafe"


@dataclass
class StoryParams:
    place: str
    wanderer: str
    lure: str
    move: str
    bravery: str
    hero: str
    hero_gender: str
    parent: str
    delay: int = 0
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


def predict_outcome(place: Place, wanderer: Wanderer, lure: Lure, move: ProtectMove,
                    bravery: Bravery, delay: int) -> dict:
    temp = StoryParams(
        place=place.id,
        wanderer=wanderer.id,
        lure=lure.id,
        move=move.id,
        bravery=bravery.id,
        hero="Ava",
        hero_gender="girl",
        parent="mother",
        delay=delay,
        seed=None,
    )
    return {
        "ready": readiness(bravery, move),
        "pull": lure.pull,
        "outcome": outcome_of(temp),
    }


def introduce(world: World, hero: Entity, adult: Entity, wanderer: Entity, place: Place) -> None:
    world.say(
        f"After school, {hero.id} stayed near {adult.label_word} while {adult.pronoun()} was "
        f"{place.chore}. {place.image}"
    )
    world.say(
        f"{wanderer.id} was nearby too, making the ordinary afternoon feel full and busy in a soft family way."
    )


def ordinary_detail(world: World, place: Place, wanderer: Wanderer) -> None:
    world.say(
        f"{wanderer.label.capitalize()} kept close to {place.ending_spot}, and everything would have stayed calm if {place.opening_phrase} had not been left just a little open."
    )


def opening(world: World, barrier: Entity, place: Place) -> None:
    barrier.meters["open"] = 1
    world.say(
        f"For one small moment, {place.opening_phrase} stood ajar."
    )


def notice_lure(world: World, hero: Entity, wanderer: Entity, lure: Lure) -> None:
    wanderer.memes["curiosity"] += 1
    world.say(
        lure.appearance
    )
    world.say(
        f"{wanderer.id} noticed {lure.label} and {wanderer.gait} that way at once."
    )


def risk_builds(world: World, hero: Entity, wanderer: Entity, place: Place, bravery: Bravery) -> None:
    wanderer.meters["moving_out"] = 1
    wanderer.meters["distance"] = float(place.distance)
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} saw the open {world.get('barrier').label} and felt {hero.pronoun('possessive')} stomach give one quick wobble."
    )
    world.say(
        f"{bravery.line} That was the moment {hero.pronoun()} grew alert."
    )


def alert_adult(world: World, hero: Entity, adult: Entity, wanderer: Entity, place: Place) -> None:
    hero.memes["care"] += 1
    world.say(
        f'"{adult.label_word.capitalize()}, wait!" {hero.id} called. "{wanderer.id} is going to {place.outside}!"'
    )


def hero_protects(world: World, hero: Entity, wanderer: Entity, adult: Entity,
                  place: Place, move: ProtectMove, lure: Lure) -> None:
    wanderer.meters["protected"] = 1
    wanderer.meters["moving_out"] = 0
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} did not stay frozen. {move.approach}"
    )
    world.say(
        f"{move.contact} {hero.pronoun().capitalize()} wanted to protect {wanderer.id} before {lure.call.lower()} pulled {wanderer.pronoun('object')} any farther."
    )
    world.get("barrier").meters["secured"] = 1
    world.get("barrier").meters["open"] = 0
    propagate(world, narrate=False)
    adult.memes["pride"] += 1
    world.say(
        f"{adult.label_word.capitalize()} hurried over, fastened the {world.get('barrier').label}, and let out a long breath."
    )
    world.say(
        f'"You were so alert," {adult.pronoun()} said. "You helped protect {wanderer.id}."'
    )


def adult_protects(world: World, hero: Entity, wanderer: Entity, adult: Entity,
                   move: ProtectMove, lure: Lure) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} started forward at once, but the scary surprise made {hero.pronoun('possessive')} feet stick for one tiny beat."
    )
    wanderer.meters["protected"] = 1
    wanderer.meters["moving_out"] = 0
    world.get("barrier").meters["secured"] = 1
    world.get("barrier").meters["open"] = 0
    propagate(world, narrate=False)
    adult.memes["pride"] += 1
    world.say(
        f"{adult.label_word.capitalize()} turned at the shout, reached {wanderer.pronoun('object')} first, and {move.contact[0].lower() + move.contact[1:]}"
    )
    world.say(
        f'"Thank you for being alert," {adult.pronoun()} told {hero.id}. "Your call helped me protect {wanderer.id} in time."'
    )


def settle_end(world: World, hero: Entity, wanderer: Entity, adult: Entity,
               place: Place, lure: Lure) -> None:
    hero.memes["joy"] += 1
    wanderer.memes["joy"] += 1
    world.say(
        f"After that, nobody hurried near the {world.get('barrier').label} again. {adult.label_word.capitalize()} checked the latch with one careful hand."
    )
    if lure.ending_image:
        world.say(
            f"{hero.id} and {wanderer.id} watched {lure.ending_image} from {place.ending_spot} instead."
        )
    else:
        world.say(
            f"Soon the afternoon felt ordinary again, only safer than before."
        )
    world.say(
        f"{hero.id}'s heartbeat slowed, and {hero.pronoun()} stayed close to {wanderer.id}, a little steadier and a little prouder than at the start."
    )


def tell(place: Place, wanderer_cfg: Wanderer, lure: Lure, move: ProtectMove,
         bravery: Bravery, hero_name: str = "Ava", hero_gender: str = "girl",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World(place=place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[bravery.label],
        age=7,
        attrs={},
    ))
    adult = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="adult",
        traits=["calm"],
        age=34,
        attrs={},
    ))
    wanderer = world.add(Entity(
        id=wanderer_cfg.label.split()[-1].capitalize() if wanderer_cfg.type in {"brother", "sister"} else wanderer_cfg.label.capitalize(),
        kind="character" if wanderer_cfg.type in {"brother", "sister"} else "thing",
        type=wanderer_cfg.type,
        label=wanderer_cfg.label,
        role="wanderer",
        traits=[],
        age=2 if wanderer_cfg.type in {"brother", "sister"} else 1,
        attrs={"relation": wanderer_cfg.relation},
    ))
    barrier = world.add(Entity(
        id="barrier",
        kind="thing",
        type="barrier",
        label=place.barrier,
        role="barrier",
        attrs={},
    ))

    for ent in (hero, adult, wanderer, barrier):
        ent.meters["open"] = ent.meters["open"]
        ent.meters["secured"] = ent.meters["secured"]
        ent.meters["moving_out"] = ent.meters["moving_out"]
        ent.meters["protected"] = ent.meters["protected"]
        ent.meters["risk"] = ent.meters["risk"]
        ent.meters["distance"] = ent.meters["distance"]
        ent.memes["fear"] = ent.memes["fear"]
        ent.memes["alert"] = ent.memes["alert"]
        ent.memes["relief"] = ent.memes["relief"]
        ent.memes["care"] = ent.memes["care"]
        ent.memes["bravery"] = ent.memes["bravery"]
        ent.memes["pride"] = ent.memes["pride"]
        ent.memes["joy"] = ent.memes["joy"]
        ent.memes["curiosity"] = ent.memes["curiosity"]
        ent.memes["calm"] = ent.memes["calm"]

    world.facts.update(
        place=place,
        wanderer_cfg=wanderer_cfg,
        lure=lure,
        move=move,
        bravery=bravery,
        delay=delay,
        hero=hero,
        adult=adult,
        wanderer=wanderer,
        barrier=barrier,
        predicted={},
    )

    introduce(world, hero, adult, wanderer, place)
    ordinary_detail(world, place, wanderer_cfg)

    world.para()
    opening(world, barrier, place)
    notice_lure(world, hero, wanderer, lure)
    risk_builds(world, hero, wanderer, place, bravery)
    predicted = predict_outcome(place, wanderer_cfg, lure, move, bravery, delay)
    world.facts["predicted"] = predicted
    alert_adult(world, hero, adult, wanderer, place)

    world.para()
    outcome = outcome_of(StoryParams(
        place=place.id,
        wanderer=wanderer_cfg.id,
        lure=lure.id,
        move=move.id,
        bravery=bravery.id,
        hero=hero_name,
        hero_gender=hero_gender,
        parent=parent_type,
        delay=delay,
        seed=None,
    ))
    if outcome == "hero_protects":
        hero_protects(world, hero, wanderer, adult, place, move, lure)
    elif outcome == "adult_protects":
        adult_protects(world, hero, wanderer, adult, move, lure)
    else:
        raise StoryError("(No safe story: the child freezes and the grown-up is too far away. Pick a safer combination.)")

    world.para()
    settle_end(world, hero, wanderer, adult, place, lure)

    world.facts.update(
        outcome=outcome,
        secured=barrier.meters["secured"] >= THRESHOLD,
        protected=wanderer.meters["protected"] >= THRESHOLD,
    )
    return world


PLACES = {
    "front_yard": Place(
        id="front_yard",
        label="the front yard",
        barrier="gate",
        outside="the sidewalk",
        chore="watering the tomato pots by the fence",
        opening_phrase="the gate beside the mailbox",
        ending_spot="the warm front step",
        distance=3,
        image="The sun was low, and the hose made a silver line across the grass.",
        tags={"yard", "gate"},
    ),
    "hallway": Place(
        id="hallway",
        label="the apartment hallway",
        barrier="building door",
        outside="the elevator hall",
        chore="bringing in the last grocery bags",
        opening_phrase="the heavy building door",
        ending_spot="the little rug by the shoe basket",
        distance=2,
        image="The hall smelled faintly of soap and oranges from the shopping bag.",
        tags={"hallway", "door"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        barrier="screen door",
        outside="the front steps",
        chore="sorting shoes into pairs by the mat",
        opening_phrase="the screen door",
        ending_spot="the striped porch swing",
        distance=2,
        image="A breeze moved the hanging fern just enough to rustle its leaves.",
        tags={"porch", "door"},
    ),
}

WANDERERS = {
    "brother": Wanderer(
        id="brother",
        label="little brother",
        type="brother",
        noun="little brother",
        relation="sibling",
        gait="toddled",
        speed=1,
        target_tags={"child"},
        tags={"child"},
    ),
    "sister": Wanderer(
        id="sister",
        label="little sister",
        type="sister",
        noun="little sister",
        relation="sibling",
        gait="toddled",
        speed=1,
        target_tags={"child"},
        tags={"child"},
    ),
    "puppy": Wanderer(
        id="puppy",
        label="the puppy",
        type="puppy",
        noun="puppy",
        relation="pet",
        gait="trotted",
        speed=2,
        target_tags={"pet"},
        tags={"pet"},
    ),
}

LURES = {
    "ball": Lure(
        id="ball",
        label="a red ball wobbling down the path",
        appearance="Then a red ball, bumped loose from the step, began to wobble away.",
        call="that bright rolling ball",
        pull=5,
        target_tags={"child"},
        ending_image="the ball rock gently in a basket",
        tags={"ball"},
    ),
    "music": Lure(
        id="music",
        label="ice-cream music floating from the street",
        appearance="A tinkly bit of ice-cream music drifted in from outside.",
        call="that sweet faraway music",
        pull=5,
        target_tags={"child"},
        ending_image="the ice-cream truck pass while they waved from inside the gate",
        tags={"music"},
    ),
    "bubble": Lure(
        id="bubble",
        label="a soap bubble sailing toward the opening",
        appearance="One soap bubble slipped free from a tray and sailed toward the opening.",
        call="that floating bubble",
        pull=4,
        target_tags={"child", "pet"},
        ending_image="the last bubble pop in the air while they stayed together",
        tags={"bubble"},
    ),
    "leaf": Lure(
        id="leaf",
        label="a brown leaf skittering in the breeze",
        appearance="A dry brown leaf skipped over the ground on the breeze.",
        call="that dancing leaf",
        pull=4,
        target_tags={"pet"},
        ending_image="the leaf tumble in little circles beyond the latched door",
        tags={"leaf"},
    ),
}

PROTECT_MOVES = {
    "hold_hand": ProtectMove(
        id="hold_hand",
        label="hold a hand",
        modes={"child"},
        speed=2,
        brave_bonus=0,
        approach="She hurried after the small patter of feet and reached out before the next step could land outside.",
        contact="Her fingers found a warm little hand and held on gently but firmly.",
        qa_text="held the toddler's hand and stopped them short of the opening",
        tags={"hand"},
    ),
    "scoop_up": ProtectMove(
        id="scoop_up",
        label="scoop up",
        modes={"pet"},
        speed=3,
        brave_bonus=0,
        approach="She darted forward with both arms ready.",
        contact="In one quick motion, she scooped the puppy against her sweater.",
        qa_text="scooped the puppy up before it reached the opening",
        tags={"pickup"},
    ),
    "stand_wide": ProtectMove(
        id="stand_wide",
        label="stand wide",
        modes={"child", "pet"},
        speed=1,
        brave_bonus=1,
        approach="She moved into the opening first and made herself wide and still.",
        contact="That gave the wanderer one surprised pause right in front of her.",
        qa_text="stepped in front of the opening and made the wanderer pause",
        tags={"block"},
    ),
}

BRAVERIES = {
    "hesitant": Bravery(
        id="hesitant",
        label="hesitant",
        value=3,
        line="For a blink, being brave felt hard.",
        tags={"bravery"},
    ),
    "steady": Bravery(
        id="steady",
        label="steady",
        value=4,
        line="Her fear was real, but so was the steady part of her.",
        tags={"bravery"},
    ),
    "bold": Bravery(
        id="bold",
        label="bold",
        value=5,
        line="The brave part of her rose faster than the fear did.",
        tags={"bravery"},
    ),
}

GIRL_NAMES = ["Ava", "Lily", "Mia", "Nora", "Ella", "Lucy", "Zoe", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Noah", "Sam", "Theo", "Jack", "Eli"]


KNOWLEDGE = {
    "gate": [
        (
            "Why should a gate or door be latched when a little child or pet is nearby?",
            "A latch helps keep the safe inside space separate from the busy outside space. Little children and pets can move quickly when something catches their eye."
        )
    ],
    "alert": [
        (
            "What does it mean to stay alert?",
            "Staying alert means noticing what is happening around you instead of drifting past it. When you are alert, you can call for help early."
        )
    ],
    "protect": [
        (
            "What does it mean to protect someone smaller?",
            "To protect someone is to help keep them safe when they cannot manage the danger by themselves. Sometimes protecting means holding a hand, blocking a path, or calling a grown-up fast."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery does not mean never feeling scared. It means doing the careful right thing even while your body still feels frightened."
        )
    ],
    "puppy": [
        (
            "Why do puppies chase moving things?",
            "Puppies notice movement quickly and often want to follow it. Leaves, bubbles, and little rolling things can feel like a game to them."
        )
    ],
    "toddler": [
        (
            "Why do toddlers wander toward interesting things?",
            "Toddlers are curious, and they do not always understand where the safe boundary is. A sound or a bright moving thing can pull their attention right away."
        )
    ],
    "music": [
        (
            "Why can music from outside make children curious?",
            "A new sound can make children want to see where it is coming from. If they move before thinking, they may head toward places that need a grown-up with them."
        )
    ],
    "ball": [
        (
            "Why do rolling balls make people want to chase them?",
            "A rolling ball looks lively and easy to follow. That is why people often keep ball play away from streets and doors."
        )
    ],
    "bubble": [
        (
            "Why are bubbles hard to ignore?",
            "Bubbles drift and sparkle, so eyes want to follow them. They can carry play in a new direction before a child notices where their feet are going."
        )
    ],
    "leaf": [
        (
            "Why does a leaf blowing in the wind attract a puppy?",
            "A skittering leaf moves in sudden little jumps, which feels exciting to a puppy. The puppy may chase first and think later."
        )
    ],
}
KNOWLEDGE_ORDER = ["gate", "alert", "protect", "bravery", "toddler", "puppy", "music", "ball", "bubble", "leaf"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    wanderer_cfg = f["wanderer_cfg"]
    lure = f["lure"]
    place = f["place"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that uses the words "protect" and "alert".',
        f"Tell a gentle story where {hero.id} notices {wanderer_cfg.noun} heading toward {place.outside} because of {lure.label}, and bravery helps {hero.pronoun('object')} act in time.",
        f"Write a small family story about an ordinary chore, a suddenly open {place.barrier}, and one child becoming alert enough to protect someone smaller.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    wanderer = f["wanderer"]
    place = f["place"]
    lure = f["lure"]
    move = f["move"]
    bravery = f["bravery"]
    predicted = f["predicted"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {wanderer.label}, and {adult.label_word}. They were in {place.label} during an ordinary family chore when the danger appeared."
        ),
        (
            f"Why did {hero.id} become alert?",
            f"{hero.id} saw that {place.opening_phrase} was still open while {wanderer.id} moved toward it. {lure.label.capitalize()} had caught {wanderer.pronoun('possessive')} attention, so the open way out suddenly mattered."
        ),
        (
            f"How did bravery matter in this story?",
            f"{hero.id} still felt scared, but {hero.pronoun('possessive')} bravery helped {hero.pronoun('object')} act instead of pretending nothing was wrong. In the world model, {hero.pronoun('possessive')} readiness was {predicted['ready']} against a pull of {predicted['pull']}, which is why the moment turned toward help instead of drift."
        ),
    ]
    if outcome == "hero_protects":
        qa.append(
            (
                f"How did {hero.id} protect {wanderer.id}?",
                f"{hero.id} {move.qa_text}. Then {adult.label_word} fastened the {place.barrier}, so the risk ended in a real visible way."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} still help even though {adult.label_word} reached {wanderer.id} first?",
                f"Yes. {hero.id} called out right away, and that alert warning turned {adult.label_word}'s attention at the exact moment it was needed. The grown-up made the final grab, but the rescue started with {hero.id}'s voice."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended quietly and safely, with the latch checked and everyone staying together near {place.ending_spot}. The calm ending proves the family changed from rushing around an open exit to watching the boundary more carefully."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"gate", "alert", "protect", "bravery"}
    if f["wanderer_cfg"].id in {"brother", "sister"}:
        tags.add("toddler")
    if f["wanderer_cfg"].id == "puppy":
        tags.add("puppy")
    if f["lure"].id in KNOWLEDGE:
        tags.add(f["lure"].id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="front_yard",
        wanderer="brother",
        lure="ball",
        move="hold_hand",
        bravery="steady",
        hero="Ava",
        hero_gender="girl",
        parent="mother",
        delay=0,
        seed=None,
    ),
    StoryParams(
        place="hallway",
        wanderer="puppy",
        lure="leaf",
        move="scoop_up",
        bravery="bold",
        hero="Leo",
        hero_gender="boy",
        parent="father",
        delay=0,
        seed=None,
    ),
    StoryParams(
        place="porch",
        wanderer="sister",
        lure="music",
        move="stand_wide",
        bravery="hesitant",
        hero="Mia",
        hero_gender="girl",
        parent="mother",
        delay=0,
        seed=None,
    ),
    StoryParams(
        place="hallway",
        wanderer="brother",
        lure="bubble",
        move="hold_hand",
        bravery="bold",
        hero="Ben",
        hero_gender="boy",
        parent="father",
        delay=1,
        seed=None,
    ),
    StoryParams(
        place="front_yard",
        wanderer="puppy",
        lure="bubble",
        move="stand_wide",
        bravery="steady",
        hero="Nora",
        hero_gender="girl",
        parent="mother",
        delay=0,
        seed=None,
    ),
]


def explain_lure(wanderer: Wanderer, lure: Lure) -> str:
    return (
        f"(No story: {wanderer.noun} would not naturally chase {lure.label} in this world. "
        f"Pick a lure that fits {wanderer.noun}'s curiosity.)"
    )


def explain_move(wanderer: Wanderer, move: ProtectMove) -> str:
    return (
        f"(No story: '{move.id}' is not a sensible way to protect {wanderer.noun} here. "
        f"Choose a move that actually fits who is wandering.)"
    )


def explain_unsafe(params: StoryParams) -> str:
    return (
        f"(No safe story: with bravery={params.bravery}, move={params.move}, and delay={params.delay}, "
        f"the child cannot protect in time and the grown-up is too slow to fix it safely.)"
    )


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
lure_matches(W, L) :- wanderer(W), lure(L), wants_tag(W, T), tempts(L, T).
move_matches(W, M) :- wanderer(W), protect_move(M), kind(W, T), supports(M, T).
valid(P, W, L, M) :- place(P), lure_matches(W, L), move_matches(W, M).

% --- outcome model ----------------------------------------------------------
ready(B + 1 + Bonus) :- chosen_bravery(BR), bravery_value(BR, B),
                        chosen_move(M), brave_bonus(M, Bonus).
hero_protects :- ready(R), chosen_lure(L), pull(L, P), R >= P,
                 chosen_wanderer(W), wanderer_speed(W, WS),
                 chosen_move(M), move_speed(M, MS), MS >= WS.

adult_protects :- not hero_protects,
                  chosen_wanderer(W), wanderer_speed(W, WS),
                  delay(D), adult_speed(AS), AS - D >= WS.

unsafe :- not hero_protects, not adult_protects.

outcome(hero_protects) :- hero_protects.
outcome(adult_protects) :- adult_protects.
outcome(unsafe) :- unsafe.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for wid, wanderer in WANDERERS.items():
        lines.append(asp.fact("wanderer", wid))
        lines.append(asp.fact("kind", wid, next(iter(sorted(wanderer.tags)))))
        lines.append(asp.fact("wanderer_speed", wid, wanderer.speed))
        for tag in sorted(wanderer.target_tags):
            lines.append(asp.fact("wants_tag", wid, tag))
    for lid, lure in LURES.items():
        lines.append(asp.fact("lure", lid))
        lines.append(asp.fact("pull", lid, lure.pull))
        for tag in sorted(lure.target_tags):
            lines.append(asp.fact("tempts", lid, tag))
    for mid, move in PROTECT_MOVES.items():
        lines.append(asp.fact("protect_move", mid))
        lines.append(asp.fact("move_speed", mid, move.speed))
        lines.append(asp.fact("brave_bonus", mid, move.brave_bonus))
        for tag in sorted(move.modes):
            lines.append(asp.fact("supports", mid, tag))
    for bid, bravery in BRAVERIES.items():
        lines.append(asp.fact("bravery", bid))
        lines.append(asp.fact("bravery_value", bid, bravery.value))
    lines.append(asp.fact("adult_speed", ADULT_SPEED))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_wanderer", params.wanderer),
        asp.fact("chosen_lure", params.lure),
        asp.fact("chosen_move", params.move),
        asp.fact("chosen_bravery", params.bravery),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child notices danger, stays alert, and helps protect someone smaller."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wanderer", choices=WANDERERS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--move", choices=PROTECT_MOVES)
    ap.add_argument("--bravery", choices=BRAVERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how many beats before the grown-up can join in")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.wanderer and args.lure:
        wanderer = WANDERERS[args.wanderer]
        lure = LURES[args.lure]
        if not lure_matches(wanderer, lure):
            raise StoryError(explain_lure(wanderer, lure))
    if args.wanderer and args.move:
        wanderer = WANDERERS[args.wanderer]
        move = PROTECT_MOVES[args.move]
        if not move_matches(wanderer, move):
            raise StoryError(explain_move(wanderer, move))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.wanderer is None or combo[1] == args.wanderer)
        and (args.lure is None or combo[2] == args.lure)
        and (args.move is None or combo[3] == args.move)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, wanderer, lure, move = rng.choice(sorted(combos))
    bravery = args.bravery or rng.choice(sorted(BRAVERIES))
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])

    params = StoryParams(
        place=place,
        wanderer=wanderer,
        lure=lure,
        move=move,
        bravery=bravery,
        hero=hero,
        hero_gender=gender,
        parent=parent,
        delay=delay,
        seed=None,
    )
    if outcome_of(params) == "unsafe":
        safe_bravery = [
            bid for bid in sorted(BRAVERIES)
            if outcome_of(StoryParams(
                place=place,
                wanderer=wanderer,
                lure=lure,
                move=move,
                bravery=bid,
                hero=hero,
                hero_gender=gender,
                parent=parent,
                delay=delay,
                seed=None,
            )) != "unsafe"
        ]
        if args.bravery is not None:
            raise StoryError(explain_unsafe(params))
        if not safe_bravery:
            raise StoryError(explain_unsafe(params))
        params.bravery = rng.choice(safe_bravery)
    return params


def generate(params: StoryParams) -> StorySample:
    for key, registry, label in [
        (params.place, PLACES, "place"),
        (params.wanderer, WANDERERS, "wanderer"),
        (params.lure, LURES, "lure"),
        (params.move, PROTECT_MOVES, "move"),
        (params.bravery, BRAVERIES, "bravery"),
    ]:
        if key not in registry:
            raise StoryError(f"(No story: unknown {label} '{key}'.)")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unsupported gender '{params.hero_gender}'.)")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(No story: unsupported parent '{params.parent}'.)")
    if not lure_matches(WANDERERS[params.wanderer], LURES[params.lure]):
        raise StoryError(explain_lure(WANDERERS[params.wanderer], LURES[params.lure]))
    if not move_matches(WANDERERS[params.wanderer], PROTECT_MOVES[params.move]):
        raise StoryError(explain_move(WANDERERS[params.wanderer], PROTECT_MOVES[params.move]))
    if outcome_of(params) == "unsafe":
        raise StoryError(explain_unsafe(params))

    world = tell(
        place=PLACES[params.place],
        wanderer_cfg=WANDERERS[params.wanderer],
        lure=LURES[params.lure],
        move=PROTECT_MOVES[params.move],
        bravery=BRAVERIES[params.bravery],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(200):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            mismatches.append((params, py, asp))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")
        for params, py, asp in mismatches[:5]:
            print(f"  {params} -> python={py} asp={asp}")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, wanderer, lure, move) combos:\n")
        for place, wanderer, lure, move in combos:
            print(f"  {place:11} {wanderer:8} {lure:7} {move}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero}: {p.wanderer} + {p.lure} at {p.place} "
                f"({p.move}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
