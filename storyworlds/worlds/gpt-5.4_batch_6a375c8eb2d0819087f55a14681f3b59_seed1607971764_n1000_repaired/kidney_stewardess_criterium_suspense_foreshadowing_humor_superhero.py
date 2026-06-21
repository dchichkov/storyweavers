#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kidney_stewardess_criterium_suspense_foreshadowing_humor_superhero.py
==================================================================================================

A standalone storyworld for a tiny superhero domain:

A child superhero is traveling with a grown-up carrying a cooler with a donor
kidney for a hospital. A friendly stewardess notices the child hero's gear on
the plane and, with a little foreshadowing and humor, points out what may be
useful later. After landing, a city street is blocked by a bicycle criterium,
and the child plus helpers must use the *right* route to get the kidney to the
hospital on time.

The world enforces one simple reasonableness constraint:
the chosen route must actually bypass the chosen blockage. A blocked street
cannot honestly be solved by another street route, and a roof route makes sense
only when the hero has a flying aid. The story then branches by urgency and
route speed into either a just-in-time save or a missed-time sad ending.

Required seed words included in the domain and prose:
- kidney
- stewardess
- criterium

Features:
- suspense: the ticking clock and city blockage
- foreshadowing: a small early object later becomes the fix
- humor: cape/snack-cart/comic beats in a gentle superhero tone
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "stewardess", "doctor"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Config records
# ---------------------------------------------------------------------------
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
class HeroMode:
    id: str
    title: str
    opening: str
    move_text: str
    joke: str
    flight: bool = False
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
class Blockage:
    id: str
    label: str
    scene: str
    danger_line: str
    bypasses: set[str] = field(default_factory=set)
    severity: int = 1
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
class Route:
    id: str
    label: str
    speed: int
    bypasses: set[str] = field(default_factory=set)
    needs_flight: bool = False
    leadin: str = ""
    success: str = ""
    fail: str = ""
    qa_success: str = ""
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
class HospitalNeed:
    id: str
    label: str
    urgency: int
    patient: str
    end_image: str
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
class Foreshadow:
    id: str
    object_label: str
    plane_bit: str
    later_help: str
    route_bonus_to: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_delay_anxiety(world: World) -> list[str]:
    out: list[str] = []
    if world.get("city").meters["delay"] < THRESHOLD:
        return out
    sig = ("delay_anxiety",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["worry"] += 1
    world.get("adult").memes["worry"] += 1
    world.get("kidney").meters["risk"] += 1
    out.append("__delay__")
    return out


def _r_helper_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("stewardess").memes["encourage"] < THRESHOLD:
        return out
    sig = ("helper_calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["brave"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="delay_anxiety", tag="social", apply=_r_delay_anxiety),
    Rule(name="helper_calm", tag="social", apply=_r_helper_calm),
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


# ---------------------------------------------------------------------------
# Constraints and timing
# ---------------------------------------------------------------------------
def route_works(blockage: Blockage, route: Route, hero: HeroMode) -> bool:
    if route.needs_flight and not hero.flight:
        return False
    return blockage.id in route.bypasses


def route_speed(route: Route, foreshadow: Foreshadow) -> int:
    bonus = 1 if foreshadow.route_bonus_to == route.id else 0
    return route.speed + bonus


def arrives_in_time(route: Route, need: HospitalNeed, foreshadow: Foreshadow) -> bool:
    return route_speed(route, foreshadow) >= need.urgency


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hero_id, hero in HEROES.items():
        for block_id, blockage in BLOCKAGES.items():
            for route_id, route in ROUTES.items():
                if not route_works(blockage, route, hero):
                    continue
                for need_id in NEEDS:
                    combos.append((hero_id, block_id, route_id, need_id))
    return combos


def explain_rejection(hero: HeroMode, blockage: Blockage, route: Route) -> str:
    if route.needs_flight and not hero.flight:
        return (
            f"(No story: {hero.title} cannot honestly use the {route.label} route "
            f"without a flying aid. Pick a flying hero or a ground route.)"
        )
    return (
        f"(No story: the {route.label} route does not truly bypass the {blockage.label}. "
        f"Choose a route that gets around that blockage.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_trip(world: World, route_id: str) -> dict:
    sim = world.copy()
    route = ROUTES[route_id]
    foreshadow = sim.facts["foreshadow"]
    need = sim.facts["need"]
    sim.get("city").meters["delay"] += 1
    propagate(sim, narrate=False)
    return {
        "speed": route_speed(route, foreshadow),
        "in_time": arrives_in_time(route, need, foreshadow),
        "risk": sim.get("kidney").meters["risk"],
    }


# ---------------------------------------------------------------------------
# Beats
# ---------------------------------------------------------------------------
def open_story(world: World, hero: Entity, adult: Entity, stewardess: Entity,
               hero_cfg: HeroMode, need: HospitalNeed, foreshadow: Foreshadow) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} loved pretending to be {hero_cfg.title}, the sort of hero who "
        f"never ran from a hard job. {hero_cfg.opening}"
    )
    world.say(
        f"That morning, {adult.label_word.capitalize()} carried a small cold cooler "
        f"with a donor kidney inside. It had to reach {need.patient} at City Hospital."
    )
    world.say(
        f"On the plane, a kind stewardess named {stewardess.id} noticed {hero.id}'s "
        f"{foreshadow.object_label}. {foreshadow.plane_bit}"
    )


def plane_humor(world: World, hero: Entity, stewardess: Entity, hero_cfg: HeroMode) -> None:
    stewardess.memes["encourage"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When the snack cart rolled by, {hero.id}'s cape tried to make friends with it "
        f"and got one silly little tug. {stewardess.id} laughed, untangled it, and said, "
        f'"Every superhero needs practice."'
    )
    world.say(hero_cfg.joke)


def landing_and_block(world: World, hero: Entity, adult: Entity, blockage: Blockage) -> None:
    world.get("city").meters["delay"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But after the plane landed, the city sounded wrong. {blockage.scene}"
    )
    world.say(
        f'{adult.label_word.capitalize()} stared ahead. "{blockage.danger_line}"'
    )


def warning(world: World, hero: Entity, stewardess: Entity, route: Route) -> None:
    pred = predict_trip(world, route.id)
    world.facts["predicted_speed"] = pred["speed"]
    world.facts["predicted_in_time"] = pred["in_time"]
    stewardess.memes["focus"] += 1
    world.say(
        f"{stewardess.id} knelt beside {hero.id}. "
        f'"Remember what I said on the plane? {world.facts["foreshadow"].later_help}"'
    )


def choose_route(world: World, hero: Entity, adult: Entity, route: Route, hero_cfg: HeroMode) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} took a deep breath. {hero.pronoun().capitalize()} was only a child, "
        f"but this felt like a real superhero moment."
    )
    world.say(
        f"{route.leadin} {hero_cfg.move_text}"
    )


def travel_success(world: World, hero: Entity, adult: Entity, route: Route,
                   need: HospitalNeed, foreshadow: Foreshadow) -> None:
    world.get("kidney").meters["delivered"] += 1
    world.get("city").meters["delay"] = 0.0
    hero.memes["relief"] += 1
    adult.memes["relief"] += 1
    world.say(route.success)
    world.say(
        f"They reached the hospital doors just in time, and a nurse hurried the kidney inside."
    )
    world.say(
        f"Soon the doctor came back smiling. {need.end_image}"
    )


def travel_fail(world: World, hero: Entity, adult: Entity, route: Route,
                need: HospitalNeed) -> None:
    world.get("kidney").meters["late"] += 1
    hero.memes["sad"] += 1
    adult.memes["sad"] += 1
    world.say(route.fail)
    world.say(
        f"They still hurried the kidney to the hospital, but they were too late for {need.patient}'s surgery that day."
    )
    world.say(
        "The grown-ups promised they would keep helping and never stop trying, but the child hero learned that choosing the fastest true path matters."
    )


def ending_gift(world: World, hero: Entity, stewardess: Entity, foreshadow: Foreshadow) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"Back at the hospital, {stewardess.id} found them again and tapped {hero.id}'s "
        f"{foreshadow.object_label}. \"Looks like it really was part of the plan,\" she said."
    )
    world.say(
        f"{hero.id} stood a little taller. The city lights blinked below like tiny hero signals."
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def tell(hero_cfg: HeroMode, blockage: Blockage, route: Route, need: HospitalNeed,
         foreshadow: Foreshadow, hero_name: str = "Nova", hero_gender: str = "girl",
         adult_type: str = "mother", stewardess_name: str = "Mira") -> World:
    world = World()

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    adult = world.add(Entity(id="Parent", kind="character", type=adult_type, role="adult", label="the parent"))
    stewardess = world.add(Entity(id=stewardess_name, kind="character", type="stewardess", role="helper"))
    kidney = world.add(Entity(id="kidney", type="kidney", label="the kidney"))
    city = world.add(Entity(id="city", type="city", label="the city"))
    hero.attrs["mode"] = hero_cfg.id
    hero.attrs["foreshadow_item"] = foreshadow.object_label
    city.meters["delay"] = 0.0
    kidney.meters["risk"] = 0.0
    kidney.meters["delivered"] = 0.0
    kidney.meters["late"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["brave"] = 0.0
    stewardess.memes["encourage"] = 0.0
    stewardess.memes["focus"] = 0.0
    adult.memes["worry"] = 0.0

    world.facts.update(
        hero=hero,
        adult=adult,
        stewardess=stewardess,
        kidney=kidney,
        blockage=blockage,
        route=route,
        need=need,
        foreshadow=foreshadow,
        hero_cfg=hero_cfg,
    )

    open_story(world, hero, adult, stewardess, hero_cfg, need, foreshadow)
    plane_humor(world, hero, stewardess, hero_cfg)

    world.para()
    landing_and_block(world, hero, adult, blockage)
    warning(world, hero, stewardess, route)
    choose_route(world, hero, adult, route, hero_cfg)

    world.para()
    if arrives_in_time(route, need, foreshadow):
        travel_success(world, hero, adult, route, need, foreshadow)
        world.para()
        ending_gift(world, hero, stewardess, foreshadow)
        outcome = "saved"
    else:
        travel_fail(world, hero, adult, route, need)
        outcome = "late"

    world.facts.update(
        outcome=outcome,
        delivered=kidney.meters["delivered"] >= THRESHOLD,
        late=kidney.meters["late"] >= THRESHOLD,
        in_time=arrives_in_time(route, need, foreshadow),
        final_speed=route_speed(route, foreshadow),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HEROES = {
    "glider": HeroMode(
        id="glider",
        title="Sky Glider",
        opening="A silver scarf fluttered behind her like a brave little comet tail.",
        move_text="She snapped open her pocket glider and the wind tugged it awake.",
        joke='"I am one hundred percent ready," she whispered, and then added, "Maybe ninety-eight if my boots squeak again."',
        flight=True,
        tags={"hero", "flying"},
    ),
    "roller": HeroMode(
        id="roller",
        title="Turbo Roller",
        opening="His bright helmet shone so much that he called it his moon on wheels.",
        move_text="He leaned forward on his zoom skates and hummed his own hero music.",
        joke='"My feet are basically tiny rockets," he said, right before wobbling once and grinning at himself.',
        flight=False,
        tags={"hero", "wheels"},
    ),
    "spring": HeroMode(
        id="spring",
        title="Captain Springstep",
        opening="Her springy boots made tiny boing sounds that she claimed were superhero thunder.",
        move_text="She bounced from step to step, quick and light as a comic-book kangaroo.",
        joke='"Boing first, explain later," she said, which made even the serious grown-ups smile.',
        flight=False,
        tags={"hero", "jumping"},
    ),
}

BLOCKAGES = {
    "criterium": Blockage(
        id="criterium",
        label="criterium",
        scene="A bicycle criterium had looped bright ribbons, racers, and cheering crowds around the streets near the hospital.",
        danger_line="The roads by the hospital are closed for the criterium.",
        bypasses={"roofline", "riverwalk"},
        severity=2,
        tags={"criterium", "bikes"},
    ),
    "parade": Blockage(
        id="parade",
        label="parade",
        scene="A brass-band parade was bobbing through the avenue, all shiny horns and giant paper stars.",
        danger_line="The parade has stopped the avenue cold.",
        bypasses={"alley", "roofline"},
        severity=1,
        tags={"parade"},
    ),
    "market": Blockage(
        id="market",
        label="street market",
        scene="A busy street market had spilled baskets, wagons, and laughing shoppers into every lane.",
        danger_line="The market is packed too tight for a car to get through.",
        bypasses={"alley", "riverwalk"},
        severity=1,
        tags={"market"},
    ),
}

ROUTES = {
    "alley": Route(
        id="alley",
        label="alley",
        speed=2,
        bypasses={"parade", "market"},
        needs_flight=False,
        leadin="There was one narrow way left: the alleys behind the shops.",
        success="Past bins, brick walls, and one surprised orange cat, they zipped through the shady back way.",
        fail="The alley twisted and doubled back, and even their fastest dashing steps could not make it quick enough.",
        qa_success="They used the alley behind the shops to go around the blockage.",
        tags={"alley"},
    ),
    "riverwalk": Route(
        id="riverwalk",
        label="riverwalk",
        speed=2,
        bypasses={"criterium", "market"},
        needs_flight=False,
        leadin="The riverwalk curved behind the crowded streets like a secret silver ribbon.",
        success="They hurried along the riverwalk, where the water flashed beside them and the path stayed clear.",
        fail="The riverwalk was clear, but it was longer than they hoped, and every extra step felt heavy.",
        qa_success="They took the riverwalk around the blocked streets.",
        tags={"riverwalk"},
    ),
    "roofline": Route(
        id="roofline",
        label="roofline",
        speed=3,
        bypasses={"criterium", "parade"},
        needs_flight=True,
        leadin="Above them, the roofline stretched from building to building.",
        success="Up they went over the rooftops, with chimneys, pigeons, and flapping laundry cheering them on in their own funny way.",
        fail="They rose to the roofline, but the wind pushed back and the trip still stole too many precious moments.",
        qa_success="They used the roofline above the blocked streets.",
        tags={"roofline", "flying"},
    ),
}

NEEDS = {
    "urgent": HospitalNeed(
        id="urgent",
        label="very urgent",
        urgency=3,
        patient="a little boy named Ruben",
        end_image="Ruben would get his surgery after all, and his family cried happy tears into bright paper masks.",
        tags={"hospital", "urgent"},
    ),
    "steady": HospitalNeed(
        id="steady",
        label="steady",
        urgency=2,
        patient="a little girl named June",
        end_image="June's room felt lighter at once, as if hope had opened a curtain and let the sun in.",
        tags={"hospital"},
    ),
}

FORESHADOWS = {
    "goggles": Foreshadow(
        id="goggles",
        object_label="goggles",
        plane_bit='"Those goggles are not just for style," she said. "Good heroes see the true path before everyone else."',
        later_help="Use your goggles and look for the clear path, not the loud path.",
        route_bonus_to="roofline",
        tags={"goggles", "foreshadow"},
    ),
    "map_pin": Foreshadow(
        id="map_pin",
        object_label="map pin",
        plane_bit='"That little map pin on your glove is clever," she said. "Heroes win by knowing where tiny paths hide."',
        later_help="Check your map pin. Small paths can beat big traffic.",
        route_bonus_to="alley",
        tags={"map", "foreshadow"},
    ),
    "river_badge": Foreshadow(
        id="river_badge",
        object_label="river badge",
        plane_bit='"A river badge?" she said with a smile. "Then maybe the water will be your friend today."',
        later_help="Remember your river badge. Water paths can stay open when roads do not.",
        route_bonus_to="riverwalk",
        tags={"river", "foreshadow"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Zia", "Mira", "Ava", "Ivy", "Ruby", "Skye"]
BOY_NAMES = ["Max", "Leo", "Eli", "Finn", "Theo", "Jax", "Nico", "Sam"]
STEWARDESS_NAMES = ["Mira", "Tessa", "Joy", "Rina", "Lila"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hero_mode: str
    blockage: str
    route: str
    need: str
    foreshadow: str
    hero_name: str
    hero_gender: str
    adult_type: str
    stewardess_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "kidney": [
        (
            "What does a kidney do?",
            "A kidney is a body part that helps clean the blood and make waste leave the body. People have kidneys inside them, and doctors work hard to keep them healthy.",
        )
    ],
    "stewardess": [
        (
            "What does a stewardess do on a plane?",
            "A stewardess helps passengers stay safe and comfortable on a plane. She can give instructions, answer questions, and help people stay calm.",
        )
    ],
    "criterium": [
        (
            "What is a criterium?",
            "A criterium is a bicycle race on a short course with many laps. Riders go around the same loop again and again very fast.",
        )
    ],
    "foreshadow": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is a small clue early in the story that hints at something important later. It helps the ending feel surprising and fitting at the same time.",
        )
    ],
    "route": [
        (
            "Why does choosing the right route matter in an emergency?",
            "The right route saves time by avoiding places that are blocked or crowded. In an emergency, a few minutes can matter a lot.",
        )
    ],
    "hospital": [
        (
            "Why do hospitals need fast helpers sometimes?",
            "Hospitals help sick or hurt people, and sometimes they need medicine or supplies quickly. Fast helpers can make sure doctors have what they need in time.",
        )
    ],
    "hero": [
        (
            "What makes someone a hero?",
            "A hero helps when something important is at stake and tries to do the brave, caring thing. Being a hero can mean thinking clearly, not just being strong.",
        )
    ],
}
KNOWLEDGE_ORDER = ["kidney", "stewardess", "criterium", "foreshadow", "route", "hospital", "hero"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    hero_cfg = f["hero_cfg"]
    blockage = f["blockage"]
    need = f["need"]
    outcome = f["outcome"]
    route = f["route"]
    if outcome == "saved":
        return [
            'Write a short superhero story for a young child that includes the words "kidney", "stewardess", and "criterium".',
            f"Tell a suspenseful but gentle superhero story where {hero.id}, pretending to be {hero_cfg.title}, must help get a donor kidney to a hospital after a {blockage.label} blocks the roads.",
            f"Write a story with humor and foreshadowing where a stewardess notices a small hero item on a plane, and later that clue helps {hero.id} choose the {route.label} route in time to save the day.",
        ]
    return [
        'Write a short superhero story for a young child that includes the words "kidney", "stewardess", and "criterium".',
        f"Tell a suspenseful superhero story where {hero.id} tries to help bring a donor kidney to a hospital, but the {blockage.label} and a too-slow route make the job harder than expected.",
        "Write a story with foreshadowing and gentle humor that still teaches that heroes must choose the true fastest path in an emergency.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    stewardess = f["stewardess"]
    blockage = f["blockage"]
    route = f["route"]
    need = f["need"]
    foreshadow = f["foreshadow"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child pretending to be {f['hero_cfg'].title}, plus {hero.pronoun('possessive')} {adult.label_word} and a helpful stewardess named {stewardess.id}. Together they are trying to bring a kidney to the hospital.",
        ),
        (
            "What problem happened after the plane landed?",
            f"The roads were blocked by {blockage.scene.lower()} That created suspense because the kidney had to reach {need.patient} quickly.",
        ),
        (
            "What did the stewardess notice on the plane, and why did that matter later?",
            f"She noticed {hero.id}'s {foreshadow.object_label}. That small clue was foreshadowing, because her comment helped {hero.id} think of the better path later.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.pronoun().capitalize()} chose the {route.label} route, which truly bypassed the blockage. That let them reach the hospital in time with the kidney, because it was the clear path instead of the crowded one.",
            )
        )
        qa.append(
            (
                "Why did the ending feel heroic?",
                f"The ending felt heroic because {hero.id} stayed brave under pressure and used both help and good thinking. The smiling doctor and relieved family showed that something important had really changed.",
            )
        )
    else:
        qa.append(
            (
                f"Why were they too late?",
                f"They chose a route that was real but too slow for such an urgent need. The suspense turns sad there, because being brave was not enough without the fastest true path.",
            )
        )
        qa.append(
            (
                "What did the child hero learn?",
                f"{hero.id} learned that heroes must think clearly when time is short. A shiny-looking route is not always the best one, especially when someone at the hospital is waiting.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kidney", "stewardess", "route", "hospital", "hero", "foreshadow"}
    if world.facts["blockage"].id == "criterium":
        tags.add("criterium")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        hero_mode="glider",
        blockage="criterium",
        route="roofline",
        need="urgent",
        foreshadow="goggles",
        hero_name="Nova",
        hero_gender="girl",
        adult_type="mother",
        stewardess_name="Mira",
    ),
    StoryParams(
        hero_mode="roller",
        blockage="market",
        route="riverwalk",
        need="steady",
        foreshadow="river_badge",
        hero_name="Leo",
        hero_gender="boy",
        adult_type="father",
        stewardess_name="Joy",
    ),
    StoryParams(
        hero_mode="spring",
        blockage="parade",
        route="alley",
        need="steady",
        foreshadow="map_pin",
        hero_name="Zia",
        hero_gender="girl",
        adult_type="mother",
        stewardess_name="Tessa",
    ),
    StoryParams(
        hero_mode="roller",
        blockage="criterium",
        route="riverwalk",
        need="urgent",
        foreshadow="map_pin",
        hero_name="Max",
        hero_gender="boy",
        adult_type="father",
        stewardess_name="Rina",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% route is usable if it bypasses the blockage and any flight requirement is met
usable(H, B, R) :- hero(H), blockage(B), route(R),
                   bypasses(R, B),
                   not needs_flight(R).
usable(H, B, R) :- hero(H), blockage(B), route(R),
                   bypasses(R, B),
                   needs_flight(R), can_fly(H).

valid(H, B, R, N) :- usable(H, B, R), need(N).

bonus(R,1) :- foreshadow(F), bonus_route(F,R).
bonus(R,0) :- route(R), not bonus_route(_,R).

arrival_score(R, S + B) :- chosen_route(R), base_speed(R, S), chosen_foreshadow(F),
                           bonus_route(F, R), B = 1.
arrival_score(R, S) :- chosen_route(R), base_speed(R, S), chosen_foreshadow(F),
                       not bonus_route(F, R).

in_time :- chosen_need(N), urgency(N, U), arrival_score(_, A), A >= U.
outcome(saved) :- in_time.
outcome(late) :- not in_time.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, hero in HEROES.items():
        lines.append(asp.fact("hero", hid))
        if hero.flight:
            lines.append(asp.fact("can_fly", hid))
    for bid in BLOCKAGES:
        lines.append(asp.fact("blockage", bid))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("base_speed", rid, route.speed))
        if route.needs_flight:
            lines.append(asp.fact("needs_flight", rid))
        for b in sorted(route.bypasses):
            lines.append(asp.fact("bypasses", rid, b))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("urgency", nid, need.urgency))
    for fid, foreshadow in FORESHADOWS.items():
        lines.append(asp.fact("foreshadow", fid))
        lines.append(asp.fact("bonus_route", fid, foreshadow.route_bonus_to))
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
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_need", params.need),
        asp.fact("chosen_foreshadow", params.foreshadow),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    route = ROUTES[params.route]
    foreshadow = FORESHADOWS[params.foreshadow]
    need = NEEDS[params.need]
    return "saved" if arrives_in_time(route, need, foreshadow) else "late"


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
    for s in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed for seed {s}")
            break
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: normal generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child superhero, a stewardess, a blocked city, and a kidney delivery."
    )
    ap.add_argument("--hero-mode", choices=HEROES)
    ap.add_argument("--blockage", choices=BLOCKAGES)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--foreshadow", choices=FORESHADOWS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--stewardess-name")
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
    if args.hero_mode and args.blockage and args.route:
        hero = HEROES[args.hero_mode]
        blockage = BLOCKAGES[args.blockage]
        route = ROUTES[args.route]
        if not route_works(blockage, route, hero):
            raise StoryError(explain_rejection(hero, blockage, route))

    combos = [
        c for c in valid_combos()
        if (args.hero_mode is None or c[0] == args.hero_mode)
        and (args.blockage is None or c[1] == args.blockage)
        and (args.route is None or c[2] == args.route)
        and (args.need is None or c[3] == args.need)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_mode, blockage, route, need = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_type = args.adult or rng.choice(["mother", "father"])
    stewardess_name = args.stewardess_name or rng.choice(STEWARDESS_NAMES)
    hero_cfg = HEROES[hero_mode]
    possible_foreshadows = sorted(
        fid for fid, f in FORESHADOWS.items()
        if not (ROUTES[f.route_bonus_to].needs_flight and not hero_cfg.flight)
    )
    foreshadow = args.foreshadow or rng.choice(possible_foreshadows)
    return StoryParams(
        hero_mode=hero_mode,
        blockage=blockage,
        route=route,
        need=need,
        foreshadow=foreshadow,
        hero_name=name,
        hero_gender=gender,
        adult_type=adult_type,
        stewardess_name=stewardess_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero_mode not in HEROES:
        raise StoryError(f"(Unknown hero mode: {params.hero_mode})")
    if params.blockage not in BLOCKAGES:
        raise StoryError(f"(Unknown blockage: {params.blockage})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.foreshadow not in FORESHADOWS:
        raise StoryError(f"(Unknown foreshadow item: {params.foreshadow})")

    hero_cfg = HEROES[params.hero_mode]
    blockage = BLOCKAGES[params.blockage]
    route = ROUTES[params.route]
    need = NEEDS[params.need]
    foreshadow = FORESHADOWS[params.foreshadow]

    if not route_works(blockage, route, hero_cfg):
        raise StoryError(explain_rejection(hero_cfg, blockage, route))

    world = tell(
        hero_cfg=hero_cfg,
        blockage=blockage,
        route=route,
        need=need,
        foreshadow=foreshadow,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        adult_type=params.adult_type,
        stewardess_name=params.stewardess_name,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, blockage, route, need) combos:\n")
        for hero_mode, blockage, route, need in combos:
            print(f"  {hero_mode:8} {blockage:10} {route:10} {need}")
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
                f"### {p.hero_name}: {p.blockage} -> {p.route} "
                f"({p.hero_mode}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
