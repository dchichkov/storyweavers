#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fang_thrower_bad_ending_comedy.py
============================================================

A standalone storyworld for a silly "fang thrower" fair-booth comedy.

Premise
-------
A child brings a homemade fang thrower to a monster game at a school fair.
A friend warns that the thrower is too bouncy for the space and the fang is
too hard. Sometimes the child listens and uses a hand toss instead. Sometimes
the shot lands cleanly. Sometimes it ricochets into a nearby pudding castle or
juice tower, and the ending is a sticky little disaster.

The domain is intentionally small and child-facing:
- typed entities with physical meters and emotional memes
- a short causal rule engine
- a Python reasonableness gate plus an inline ASP twin
- complete stories with setup, turn, and ending image
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
CAREFUL_TRAITS = {"careful", "cautious", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    edible: bool = False
    springy: bool = False
    soft: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher_f": "teacher",
            "teacher_m": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
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
    opening: str
    roominess: int
    nearby: str
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
class Fang:
    id: str
    label: str
    phrase: str
    weight: int
    hardness: int
    bounce: str
    adjective: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Thrower:
    id: str
    label: str
    phrase: str
    power: int
    capacity: int
    sound: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class NearbyProp:
    id: str
    label: str
    phrase: str
    fragility: int
    collapse_text: str
    aftermath: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Prize:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "shot_mode": "",
            "predicted_bad": False,
            "predicted_score": 0,
            "outcome": "",
            "used_hand_toss": False,
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
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


def _r_launch_effect(world: World) -> list[str]:
    launcher = world.get("thrower")
    if launcher.meters["fired"] < THRESHOLD:
        return []
    sig = ("launch_effect", world.facts["shot_mode"])
    if sig in world.fired:
        return []
    world.fired.add(sig)

    if world.facts["shot_mode"] == "score":
        world.get("monster").meters["fed"] += 1
        world.get("hero").memes["triumph"] += 1
    elif world.facts["shot_mode"] == "bad":
        world.get("nearby").meters["wobble"] += 1
        world.get("hero").memes["alarm"] += 1
        world.get("friend").memes["alarm"] += 1
    return []


def _r_collapse(world: World) -> list[str]:
    prop = world.get("nearby")
    if prop.meters["wobble"] < THRESHOLD or not prop.fragile:
        return []
    sig = ("collapse", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prop.meters["collapsed"] += 1
    world.get("room").meters["mess"] += 1
    world.get("hero").memes["embarrassment"] += 1
    world.get("friend").memes["laughter"] += 1
    world.get("adult").memes["work"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="launch_effect", tag="physical", apply=_r_launch_effect),
    Rule(name="collapse", tag="physical", apply=_r_collapse),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def fits_thrower(fang: Fang, thrower: Thrower) -> bool:
    return fang.weight <= thrower.capacity


def allowed_in_place(place: Place, thrower: Thrower) -> bool:
    return thrower.power <= place.roominess + 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for fang_id, fang in FANGS.items():
            for thrower_id, thrower in THROWERS.items():
                if fits_thrower(fang, thrower) and allowed_in_place(place, thrower):
                    combos.append((place_id, fang_id, thrower_id))
    return combos


def chaos_score(place: Place, fang: Fang, thrower: Thrower) -> int:
    return thrower.power + fang.hardness - place.roominess


def clean_score(place: Place, fang: Fang, thrower: Thrower, nearby: NearbyProp) -> bool:
    return chaos_score(place, fang, thrower) < nearby.fragility


def would_avert(relation: str, hero_age: int, friend_age: int, trait: str) -> bool:
    return relation == "siblings" and friend_age > hero_age and trait in CAREFUL_TRAITS


def predict_shot(world: World, place: Place, fang: Fang, thrower: Thrower, nearby: NearbyProp) -> dict:
    sim = world.copy()
    sim.facts["shot_mode"] = "score" if clean_score(place, fang, thrower, nearby) else "bad"
    sim.get("thrower").meters["fired"] += 1
    propagate(sim, narrate=False)
    return {
        "bad": sim.get("nearby").meters["collapsed"] >= THRESHOLD,
        "fed": sim.get("monster").meters["fed"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
        "score": chaos_score(place, fang, thrower),
    }


def introduce(world: World, hero: Entity, friend: Entity, place: Place, prize: Prize) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On fair day, {hero.id} and {friend.id} hurried to {place.label}, where the class had built a cardboard monster booth."
    )
    world.say(
        f"{place.opening} If someone fed the monster a fang, the winner got {prize.phrase}."
    )


def invent(world: World, hero: Entity, fang: Fang, thrower: Thrower) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"But {hero.id} did not want to toss the fang by hand. {hero.pronoun().capitalize()} had brought {thrower.phrase}, which {hero.pronoun()} called a fang thrower."
    )
    world.say(
        f'With a grin, {hero.pronoun()} lifted {fang.phrase}. "{fang.label.capitalize()} plus thrower equals glory," {hero.pronoun()} declared.'
    )


def warn(world: World, hero: Entity, friend: Entity, adult: Entity, place: Place, fang: Fang,
         thrower: Thrower, nearby: NearbyProp) -> None:
    pred = predict_shot(world, place, fang, thrower, nearby)
    world.facts["predicted_bad"] = pred["bad"]
    world.facts["predicted_score"] = pred["score"]
    friend.memes["caution"] += 1
    detail = ""
    if pred["bad"]:
        detail = f" If that shot goes wild, it could hit {nearby.phrase}."
    world.say(
        f'{friend.id} squinted at the setup. "That fang thrower is awfully bouncy for {place.label}," {friend.pronoun()} said.{detail}'
    )
    world.say(
        f'{adult.label_word.capitalize()} glanced from the monster mouth to {nearby.phrase}. "Funny inventions are fine," {adult.pronoun()} said, "but indoor pudding and flying plastic rarely stay friends."'
    )


def defy(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} puffed up like a parade balloon. \"It will be perfect,\" {hero.pronoun()} said, and hooked the fang into the thrower."
    )


def back_down(world: World, hero: Entity, friend: Entity) -> None:
    world.facts["used_hand_toss"] = True
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{hero.id} looked at {friend.id}, then at the wobbling stack beside the booth, and made a face. \"Fine,\" {hero.pronoun()} said. \"No launch. Hand toss.\""
    )
    world.say(
        f"The fang thrower went under the table, and suddenly the whole game looked much less dangerous and much more sensible."
    )


def hand_toss_success(world: World, hero: Entity, fang: Fang, prize: Prize) -> None:
    world.get("monster").meters["fed"] += 1
    hero.memes["triumph"] += 1
    world.say(
        f"{hero.id} flicked the {fang.label} gently, and it plopped straight into the monster mouth."
    )
    world.say(
        f"The booth bell rang, everyone clapped, and {hero.id} won {prize.phrase} without launching anything at all."
    )


def fire_thrower(world: World, hero: Entity, fang: Fang, thrower: Thrower, mode: str) -> None:
    world.facts["shot_mode"] = mode
    world.get("thrower").meters["fired"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{thrower.sound}! The {fang.label} shot out of the fang thrower so fast that even {hero.id} blinked."
    )


def clean_win(world: World, hero: Entity, prize: Prize) -> None:
    hero.memes["joy"] += 1
    world.say(
        "The fang zipped through the air, bonked the cardboard tongue, and vanished neatly into the monster mouth."
    )
    world.say(
        f'{hero.id} froze, then burst out laughing. "I meant to do that," {hero.pronoun()} said, and the booth helper handed over {prize.phrase}.'
    )


def bad_ending(world: World, hero: Entity, friend: Entity, adult: Entity, nearby: NearbyProp,
               prize: Prize) -> None:
    hero.memes["regret"] += 1
    friend.memes["laughter"] += 1
    world.say(
        f"But the shot missed the monster by a mile and smacked {nearby.phrase}."
    )
    world.say(
        nearby.collapse_text
    )
    world.say(
        f"{adult.label_word.capitalize()} shut the booth for cleaning. Instead of {prize.phrase}, {hero.id} got a mop and one tiny napkin."
    )
    world.say(
        f"{nearby.aftermath} It was a bad ending, even if {friend.id} laughed so hard {friend.pronoun()} had to sit down."
    )


def closing_image(world: World, hero: Entity, outcome: str) -> None:
    if outcome == "bad":
        world.say(
            f"By the time the fair music started again, {hero.id} was still swabbing the floor, and the famous fang thrower sat in a bucket with a sign that said NOT AGAIN."
        )
    elif outcome == "clean":
        world.say(
            f"After that, everyone wanted one careful turn, and {hero.id} held the fang thrower much more gently than before."
        )
    else:
        world.say(
            f"After that, {hero.id} kept the fang thrower as a joke and used plain old tossing when a prize was sitting nearby."
        )


def tell(place: Place, fang: Fang, thrower: Thrower, prize: Prize,
         hero_name: str = "Milo", hero_gender: str = "boy",
         friend_name: str = "Tess", friend_gender: str = "girl",
         adult_type: str = "teacher_f", trait: str = "careful",
         hero_age: int = 6, friend_age: int = 7, relation: str = "siblings") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        traits=["showy"],
        attrs={"relation": relation},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        age=friend_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the adult",
    ))
    world.add(Entity(id="room", type="room", label=place.label))
    world.add(Entity(id="monster", type="monster", label="monster mouth"))
    world.add(Entity(id="thrower", type="tool", label=thrower.label, springy=True))
    world.add(Entity(id="fang", type="toy", label=fang.label, soft=fang.hardness <= 1))
    nearby_cfg = NEARBY[place.nearby]
    world.add(Entity(
        id="nearby",
        type="prop",
        label=nearby_cfg.label,
        fragile=True,
        edible="pudding" in nearby_cfg.label or "juice" in nearby_cfg.label,
    ))

    introduce(world, hero, friend, place, prize)
    invent(world, hero, fang, thrower)

    world.para()
    warn(world, hero, friend, adult, place, fang, thrower, nearby_cfg)

    if would_avert(relation, hero_age, friend_age, trait):
        back_down(world, hero, friend)
        world.para()
        hand_toss_success(world, hero, fang, prize)
        outcome = "averted"
    else:
        defy(world, hero)
        world.para()
        mode = "score" if clean_score(place, fang, thrower, nearby_cfg) else "bad"
        fire_thrower(world, hero, fang, thrower, mode)
        if mode == "score":
            clean_win(world, hero, prize)
            outcome = "clean"
        else:
            bad_ending(world, hero, friend, adult, nearby_cfg, prize)
            outcome = "bad"

    world.para()
    closing_image(world, hero, outcome)
    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        place=place,
        fang_cfg=fang,
        thrower_cfg=thrower,
        nearby_cfg=nearby_cfg,
        prize_cfg=prize,
        outcome=outcome,
        collapsed=world.get("nearby").meters["collapsed"] >= THRESHOLD,
        scored=world.get("monster").meters["fed"] >= THRESHOLD,
        relation=relation,
        trait=trait,
        hero_age=hero_age,
        friend_age=friend_age,
    )
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom fair corner",
        opening="A purple paper banner flapped over the game, and a pudding castle waited beside it for the snack table.",
        roominess=1,
        nearby="pudding_castle",
        tags={"classroom", "pudding"},
    ),
    "cafeteria": Place(
        id="cafeteria",
        label="the cafeteria game row",
        opening="Every table wore bat wings made of black paper, and a tall juice tower sparkled near the tickets.",
        roominess=2,
        nearby="juice_tower",
        tags={"cafeteria", "juice"},
    ),
    "gym": Place(
        id="gym",
        label="the gym prize lane",
        opening="The floor was wide and shiny, and a paper bat mobile floated safely above the side bench.",
        roominess=3,
        nearby="paper_mobile",
        tags={"gym", "paper"},
    ),
}

FANGS = {
    "foam": Fang(
        id="foam",
        label="foam fang",
        phrase="a squishy foam fang",
        weight=1,
        hardness=1,
        bounce="boingy",
        adjective="squishy",
        tags={"foam", "fang"},
    ),
    "rubber": Fang(
        id="rubber",
        label="rubber fang",
        phrase="a bendy rubber fang",
        weight=2,
        hardness=2,
        bounce="rubbery",
        adjective="bendy",
        tags={"rubber", "fang"},
    ),
    "plastic": Fang(
        id="plastic",
        label="plastic fang",
        phrase="a shiny plastic fang",
        weight=3,
        hardness=3,
        bounce="clacky",
        adjective="shiny",
        tags={"plastic", "fang"},
    ),
}

THROWERS = {
    "straw": Thrower(
        id="straw",
        label="straw popper",
        phrase="a silly paper-tube popper",
        power=1,
        capacity=1,
        sound="Pffft",
        tags={"thrower", "gentle"},
    ),
    "spoon": Thrower(
        id="spoon",
        label="spoon launcher",
        phrase="a taped-up spoon launcher",
        power=2,
        capacity=2,
        sound="Fwip",
        tags={"thrower", "launcher"},
    ),
    "spring": Thrower(
        id="spring",
        label="spring snapper",
        phrase="a springy snapper made from a box and rubber bands",
        power=3,
        capacity=3,
        sound="TWANG",
        tags={"thrower", "spring"},
    ),
}

NEARBY = {
    "pudding_castle": NearbyProp(
        id="pudding_castle",
        label="pudding castle",
        phrase="the wobbling pudding castle",
        fragility=2,
        collapse_text="The pudding castle gave one noble shiver, folded like a sleepy accordion, and slid down the snack table in a brown wave.",
        aftermath="Chocolate pudding dripped from the ticket jar and one paper crown",
        tags={"pudding", "mess"},
    ),
    "juice_tower": NearbyProp(
        id="juice_tower",
        label="juice tower",
        phrase="the tall juice tower",
        fragility=3,
        collapse_text="The top cup hopped, the middle cups sighed, and then the whole juice tower burst apart in a pink splash that reached three chairs and one very surprised shoe.",
        aftermath="Pink juice spotted the floor in long comet tails",
        tags={"juice", "mess"},
    ),
    "paper_mobile": NearbyProp(
        id="paper_mobile",
        label="paper bat mobile",
        phrase="the paper bat mobile",
        fragility=4,
        collapse_text="The paper bats spun in frantic circles, but the strings held, so nothing truly terrible happened.",
        aftermath="Only a few black paper bats kept twirling over the bench",
        tags={"paper", "craft"},
    ),
}

PRIZES = {
    "cupcake": Prize(
        id="cupcake",
        label="cupcake",
        phrase="a crooked orange-frosted cupcake",
        tags={"cupcake"},
    ),
    "sticker": Prize(
        id="sticker",
        label="sticker",
        phrase="a sheet of glitter monster stickers",
        tags={"sticker"},
    ),
}

GIRL_NAMES = ["Tess", "Mina", "Zoe", "Lila", "Nora", "Pia"]
BOY_NAMES = ["Milo", "Benji", "Otis", "Theo", "Max", "Finn"]
TRAITS = ["careful", "cautious", "sensible", "steady", "curious", "giggly"]


@dataclass
class StoryParams:
    place: str
    fang: str
    thrower: str
    prize: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    adult: str
    trait: str
    hero_age: int = 6
    friend_age: int = 7
    relation: str = "siblings"
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


KNOWLEDGE = {
    "fang": [
        (
            "What is a fang?",
            "A fang is a long, pointy tooth. In silly games, people also make pretend fangs out of foam or plastic."
        )
    ],
    "thrower": [
        (
            "What is a thrower?",
            "A thrower is something that sends another object through the air. If it is springy or strong, you should only use it when a grown-up says it is safe."
        )
    ],
    "spring": [
        (
            "Why can a springy toy send things too far?",
            "A spring stores push and lets it go all at once. That can make a toy jump farther than you meant."
        )
    ],
    "pudding": [
        (
            "Why does pudding make such a big mess when it spills?",
            "Pudding is soft and slippery, so when it tips over it spreads across tables and floors very quickly."
        )
    ],
    "juice": [
        (
            "Why do stacked cups fall over easily?",
            "A tall stack can wobble if one cup gets bumped. Then the cups can tip into each other and fall in a chain."
        )
    ],
    "foam": [
        (
            "Why is foam safer than hard plastic for a game?",
            "Foam is soft and light, so it hurts less and usually does less damage if it bumps into something."
        )
    ],
}
KNOWLEDGE_ORDER = ["fang", "thrower", "spring", "foam", "pudding", "juice"]


def pair_noun(hero: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and friend.type == "boy":
            return "two brothers"
        if hero.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    fang = f["fang_cfg"]
    thrower = f["thrower_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short comedy for a 3-to-5-year-old about a child who brings a "{fang.label}" and a "{thrower.label}" to {place.label}.'
    )
    if outcome == "bad":
        return [
            base,
            f"Tell a funny story where {hero.id} insists on using a fang thrower indoors, ignores {friend.id}'s warning, and causes a messy bad ending.",
            f'Write a slapstick fair-booth story that includes the exact words "fang" and "thrower" and ends with a comic disaster instead of a prize.',
        ]
    if outcome == "clean":
        return [
            base,
            f"Tell a light comedy where {hero.id}'s risky-looking invention works this one time, but everyone still learns to be more careful.",
            f'Write a school-fair story with the words "fang" and "thrower" where the shot lands, the crowd laughs, and the ending stays playful.',
        ]
    return [
        base,
        f"Tell a gentle comedy where {friend.id} talks {hero.id} out of using the fang thrower, and a simple hand toss saves the day.",
        f'Write a funny but safe story where a child nearly causes trouble with a thrower, then changes course before the bad ending can happen.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    place = f["place"]
    fang = f["fang_cfg"]
    thrower = f["thrower_cfg"]
    nearby = f["nearby_cfg"]
    prize = f["prize_cfg"]
    outcome = f["outcome"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, friend, relation)}, {hero.id} and {friend.id}, at a school fair. They were trying to feed a cardboard monster and win {prize.phrase}."
        ),
        (
            "What was the fang thrower?",
            f"It was {thrower.phrase} that {hero.id} used as a fang thrower. {hero.pronoun().capitalize()} wanted it to launch {fang.phrase} instead of tossing it by hand."
        ),
        (
            f"Why did {friend.id} and the {adult.label_word} worry?",
            f"They thought the shot might go wild in {place.label}. {nearby.phrase.capitalize()} was close by, so one hard bounce could turn the game into a mess."
        ),
    ]
    if outcome == "bad":
        qa.append(
            (
                f"What happened when {hero.id} fired the thrower?",
                f"The fang missed the monster and hit {nearby.phrase}. That made the nearby display collapse and splash everywhere, so the booth had to close for cleaning."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended badly but sillily: {hero.id} did not get {prize.phrase}. Instead, {hero.pronoun()} ended up with a mop, because the messy shot caused extra work for everyone."
            )
        )
    elif outcome == "clean":
        qa.append(
            (
                f"Did the thrower work?",
                f"Yes, this time it did. The fang flew into the monster mouth, so {hero.id} won {prize.phrase}, but the story still shows why the warning mattered."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"{hero.id} was still proud, but much more careful. The happy ending came because the risky plan happened not to hit the nearby display."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} stop using the thrower?",
                f"{hero.id} listened to {friend.id} and decided the joke was not worth a sticky disaster. That choice changed the ending, because a gentle hand toss fed the monster without knocking anything over."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely and happily. {hero.id} won {prize.phrase} with a hand toss, and the fang thrower stayed under the table instead of causing trouble."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["fang_cfg"].tags) | set(f["thrower_cfg"].tags) | set(f["nearby_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("fragile", ent.fragile),
            ("edible", ent.edible),
            ("springy", ent.springy),
            ("soft", ent.soft),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in sorted(world.facts.items()) if k in {'shot_mode', 'predicted_bad', 'predicted_score', 'outcome', 'used_hand_toss'})}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        fang="plastic",
        thrower="spring",
        prize="cupcake",
        hero="Milo",
        hero_gender="boy",
        friend="Tess",
        friend_gender="girl",
        adult="teacher_f",
        trait="curious",
        hero_age=7,
        friend_age=6,
        relation="friends",
    ),
    StoryParams(
        place="gym",
        fang="foam",
        thrower="spring",
        prize="sticker",
        hero="Zoe",
        hero_gender="girl",
        friend="Finn",
        friend_gender="boy",
        adult="teacher_m",
        trait="giggly",
        hero_age=6,
        friend_age=6,
        relation="friends",
    ),
    StoryParams(
        place="cafeteria",
        fang="rubber",
        thrower="spoon",
        prize="cupcake",
        hero="Benji",
        hero_gender="boy",
        friend="Mina",
        friend_gender="girl",
        adult="teacher_f",
        trait="careful",
        hero_age=5,
        friend_age=7,
        relation="siblings",
    ),
]


def explain_rejection(place: Place, fang: Fang, thrower: Thrower) -> str:
    if not fits_thrower(fang, thrower):
        return (
            f"(No story: {fang.label} is too heavy for the {thrower.label}. The fang would not sit properly in the thrower, so the game setup is unreasonable.)"
        )
    if not allowed_in_place(place, thrower):
        return (
            f"(No story: the {thrower.label} is too strong for {place.label}. This world refuses a setup that a grown-up would never sensibly allow in that space.)"
        )
    return "(No story: this combination is unreasonable.)"


ASP_RULES = r"""
fits(F,T) :- fang(F), thrower(T), weight(F,W), capacity(T,C), W <= C.
allowed(P,T) :- place(P), thrower(T), roominess(P,R), power(T,Po), Po <= R + 1.
valid(P,F,T) :- place(P), fang(F), thrower(T), fits(F,T), allowed(P,T).

careful_trait(T) :- trait(T), cautious(T).
older_sibling :- relation(siblings), hero_age(H), friend_age(F), F > H.
averted :- older_sibling, careful_trait(T).

chaos(P,F,T,S) :- chosen_place(P), chosen_fang(F), chosen_thrower(T),
                  power(T,Po), hardness(F,H), roominess(P,R), S = Po + H - R.
bad :- chosen_place(P), near(P,N), fragility(N,Fr), chaos(P,F,T,S), S >= Fr, not averted.
clean :- valid(P,F,T), chosen_place(P), chosen_fang(F), chosen_thrower(T),
         not averted, not bad.

outcome(averted) :- averted.
outcome(clean) :- clean.
outcome(bad) :- bad.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("roominess", pid, place.roominess))
        lines.append(asp.fact("near", pid, place.nearby))
    for fid, fang in FANGS.items():
        lines.append(asp.fact("fang", fid))
        lines.append(asp.fact("weight", fid, fang.weight))
        lines.append(asp.fact("hardness", fid, fang.hardness))
    for tid, thrower in THROWERS.items():
        lines.append(asp.fact("thrower", tid))
        lines.append(asp.fact("power", tid, thrower.power))
        lines.append(asp.fact("capacity", tid, thrower.capacity))
    for nid, nearby in NEARBY.items():
        lines.append(asp.fact("nearby_prop", nid))
        lines.append(asp.fact("fragility", nid, nearby.fragility))
    for tr in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("cautious", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_fang", params.fang),
        asp.fact("chosen_thrower", params.thrower),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    fang = FANGS[params.fang]
    thrower = THROWERS[params.thrower]
    nearby = NEARBY[place.nearby]
    if would_avert(params.relation, params.hero_age, params.friend_age, params.trait):
        return "averted"
    return "clean" if clean_score(place, fang, thrower, nearby) else "bad"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a silly fang thrower at a fair booth. Unspecified choices are selected at random from valid combinations."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--fang", choices=FANGS)
    ap.add_argument("--thrower", choices=THROWERS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--adult", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.fang and args.thrower:
        place = PLACES[args.place]
        fang = FANGS[args.fang]
        thrower = THROWERS[args.thrower]
        if not (fits_thrower(fang, thrower) and allowed_in_place(place, thrower)):
            raise StoryError(explain_rejection(place, fang, thrower))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.fang is None or combo[1] == args.fang)
        and (args.thrower is None or combo[2] == args.thrower)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, fang_id, thrower_id = rng.choice(sorted(combos))
    prize_id = args.prize or rng.choice(sorted(PRIZES))
    adult = args.adult or rng.choice(["teacher_f", "teacher_m"])
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero = _pick_name(rng, hero_gender)
    friend = _pick_name(rng, friend_gender, avoid=hero)
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    hero_age, friend_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        place=place_id,
        fang=fang_id,
        thrower=thrower_id,
        prize=prize_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        adult=adult,
        trait=trait,
        hero_age=hero_age,
        friend_age=friend_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        fang = FANGS[params.fang]
        thrower = THROWERS[params.thrower]
        prize = PRIZES[params.prize]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not (fits_thrower(fang, thrower) and allowed_in_place(place, thrower)):
        raise StoryError(explain_rejection(place, fang, thrower))

    world = tell(
        place=place,
        fang=fang,
        thrower=thrower,
        prize=prize,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        adult_type=params.adult,
        trait=params.trait,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
        relation=params.relation,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, fang, thrower) combos:\n")
        for place, fang, thrower in combos:
            print(f"  {place:10} {fang:8} {thrower}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.friend}: {p.fang} + {p.thrower} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
