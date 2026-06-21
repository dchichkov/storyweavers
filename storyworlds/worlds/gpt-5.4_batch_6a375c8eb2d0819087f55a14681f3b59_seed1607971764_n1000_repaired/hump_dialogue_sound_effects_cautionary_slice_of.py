#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hump_dialogue_sound_effects_cautionary_slice_of.py
==============================================================================

A standalone story world for a small slice-of-life cautionary tale about a child
rolling something over a floor hump too fast, hearing a warning, and learning a
safer way to play.

The seed asked for:
- the word "hump"
- dialogue
- sound effects
- a cautionary tone
- slice-of-life style

This world models a simple home scene: a child uses a wheeled toy to carry
something across a room; a hump in a floor covering makes the route risky; a
helper warns them; either the child listens and no spill happens, or the wheels
hit the hump and the cargo spills; then a grown-up fixes the room sensibly and
the children continue more safely.

Run it
------
    python storyworlds/worlds/gpt-5.4/hump_dialogue_sound_effects_cautionary_slice_of.py
    python storyworlds/worlds/gpt-5.4/hump_dialogue_sound_effects_cautionary_slice_of.py --route rug_corner --vehicle wagon
    python storyworlds/worlds/gpt-5.4/hump_dialogue_sound_effects_cautionary_slice_of.py --route tile_step
    python storyworlds/worlds/gpt-5.4/hump_dialogue_sound_effects_cautionary_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/hump_dialogue_sound_effects_cautionary_slice_of.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hump_dialogue_sound_effects_cautionary_slice_of.py --trace
    python storyworlds/worlds/gpt-5.4/hump_dialogue_sound_effects_cautionary_slice_of.py --verify
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
SENSE_MIN = 2
BOLD_INIT = 5.0
CAREFUL_TRAITS = {"careful", "steady", "patient", "watchful"}


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
    wheels: bool = False
    soft_cargo: bool = False
    can_flatten: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class RoomTheme:
    id: str
    room: str
    setup: str
    errand: str
    ending_image: str
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
class Vehicle:
    id: str
    label: str
    phrase: str
    wheels_size: int
    sound_roll: str
    sound_bump: str
    carry_verb: str
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
class Route:
    id: str
    label: str
    phrase: str
    hump_name: str
    severity: int
    movable: bool
    flatten_text: str
    safe_after: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    spill_text: str
    tidy_text: str
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"driver", "helper"}]

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


def _r_bump(world: World) -> list[str]:
    route = world.get("route")
    vehicle = world.get("vehicle")
    cargo = world.get("cargo")
    driver = world.get("driver")
    if route.meters["hump"] < THRESHOLD or vehicle.meters["rolling_fast"] < THRESHOLD:
        return []
    sig = ("bump", route.id, vehicle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if route.meters["roughness"] + route.meters["head_start"] >= vehicle.meters["stability"]:
        cargo.meters["spilled"] += 1
        driver.memes["alarm"] += 1
        world.get("helper").memes["alarm"] += 1
        world.get("room").meters["mess"] += 1
        return ["__spill__"]
    return []


def _r_work(world: World) -> list[str]:
    cargo = world.get("cargo")
    parent = world.get("parent")
    if cargo.meters["spilled"] < THRESHOLD:
        return []
    sig = ("work", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parent.meters["workload"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="bump", tag="physical", apply=_r_bump),
    Rule(name="work", tag="physical", apply=_r_work),
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


def route_at_risk(vehicle: Vehicle, route: Route) -> bool:
    return route.severity >= vehicle.wheels_size


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def is_contained(fix: Fix, route: Route) -> bool:
    return fix.power >= route.severity and route.movable


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, driver_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > driver_age
    authority = initial_care(trait) + 1.0 + (3.0 if helper_older else 0.0)
    return helper_older and authority > BOLD_INIT


def predict_spill(world: World) -> dict:
    sim = world.copy()
    do_roll(sim, narrate=False)
    cargo = sim.get("cargo")
    return {
        "spilled": cargo.meters["spilled"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
    }


def play_setup(world: World, theme: RoomTheme, driver: Entity, helper: Entity, cargo: Cargo) -> None:
    driver.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After an ordinary afternoon at home, {driver.id} and {helper.id} were in "
        f"the {theme.room}. {theme.setup}"
    )
    world.say(
        f'They had turned cleanup into a little game: {theme.errand} with {cargo.phrase}.'
    )


def notice_route(world: World, route: Route, helper: Entity) -> None:
    world.say(
        f"Across the floor, {route.phrase} made a small hump in the way."
    )
    world.say(
        f'{helper.id} looked at it and slowed down. "That hump could catch the wheels," '
        f'{helper.pronoun()} said.'
    )


def tempt(world: World, driver: Entity, vehicle: Vehicle) -> None:
    driver.memes["bold"] += 1
    world.say(
        f'{driver.id} grinned and grabbed {vehicle.phrase}. "{vehicle.sound_roll}!" '
        f'{driver.pronoun().capitalize()} whispered. "I can {vehicle.carry_verb} faster than walking."'
    )


def warn(world: World, helper: Entity, driver: Entity, parent: Entity, route: Route, cargo: Cargo) -> None:
    pred = predict_spill(world)
    helper.memes["care"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    second = ""
    if pred["spilled"]:
        second = f" If the wheels jump there, {cargo.label} could spill."
    world.say(
        f'"Slow down," {helper.id} said. "We should tell {parent.label_word} about '
        f'{route.hump_name} first.{second}"'
    )


def defy(world: World, driver: Entity, helper: Entity, vehicle: Vehicle) -> None:
    driver.memes["defiance"] += 1
    older_driver = driver.attrs.get("relation") == "siblings" and driver.age > helper.age
    if older_driver:
        world.say(
            f'"It is only a little hump," {driver.id} said. Because {driver.pronoun()} was '
            f'{helper.id}\'s older sibling, {helper.id} could not stop {driver.pronoun("object")} in time.'
        )
    else:
        world.say(
            f'"It is only a little hump," {driver.id} said, and gave {vehicle.label} a push.'
        )


def back_down(world: World, driver: Entity, helper: Entity, parent: Entity, route: Route) -> None:
    driver.memes["relief"] += 1
    helper.memes["relief"] += 1
    driver.memes["bold"] = 0.0
    world.say(
        f'{driver.id} looked at the hump again, then at {helper.id}, and let out a small breath. '
        f'"Okay," {driver.pronoun()} said. "Let\'s get {parent.label_word}."'
    )
    world.say(
        f'Together they left the wheels still and stood beside {route.hump_name} until a grown-up came.'
    )


def do_roll(world: World, narrate: bool = True) -> None:
    vehicle = world.get("vehicle")
    route = world.get("route")
    vehicle.meters["rolling_fast"] += 1
    route.meters["hump"] += 1
    propagate(world, narrate=narrate)


def bump_and_spill(world: World, driver: Entity, vehicle: Vehicle, cargo: Cargo, route: Route) -> None:
    do_roll(world, narrate=False)
    if cargo.id and world.get("cargo").meters["spilled"] >= THRESHOLD:
        world.say(
            f'{vehicle.sound_roll} went the wheels. Then {vehicle.sound_bump} over {route.hump_name} -- '
            f'and over tipped {cargo.label}. {cargo.spill_text}'
        )
    else:
        world.say(
            f'{vehicle.sound_roll} went the wheels. They jolted over {route.hump_name}, but nothing spilled.'
        )
    if cargo.meters["spilled"] >= THRESHOLD:
        world.say(f'"Oh no!" cried {driver.id}.')


def parent_arrives(world: World, parent: Entity) -> None:
    world.say(f'{parent.label_word.capitalize()} looked up at once and came over from the next room.')


def fix_scene(world: World, parent: Entity, route: Route, fix: Fix) -> None:
    route_ent = world.get("route")
    route_ent.meters["hump"] = 0.0
    route_ent.meters["roughness"] = 0.0
    world.get("room").meters["mess"] = 0.0
    world.say(
        f'"Nobody is hurt, and that is what matters," {parent.label_word} said. '
        f'Then {parent.pronoun()} {fix.text} {route.flatten_text}.'
    )


def lesson(world: World, parent: Entity, driver: Entity, helper: Entity, route: Route) -> None:
    driver.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    driver.memes["alarm"] = 0.0
    helper.memes["alarm"] = 0.0
    world.say(
        f'"A hump in the floor can feel small until wheels hit it fast," '
        f'{parent.label_word} said softly. "When something looks bumpy, stop and ask for help first."'
    )
    world.say(f'{driver.id} nodded, and {helper.id} nodded too.')


def tidy_and_retry(
    world: World,
    theme: RoomTheme,
    driver: Entity,
    helper: Entity,
    cargo: Cargo,
    route: Route,
    vehicle: Vehicle,
) -> None:
    driver.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'Together they {cargo.tidy_text}, then tried the little errand again {route.safe_after}.'
    )
    world.say(
        f'This time the wheels made only a soft {vehicle.sound_roll.lower()}, and {theme.ending_image}.'
    )


def rescue_after_near_miss(
    world: World,
    theme: RoomTheme,
    parent: Entity,
    driver: Entity,
    helper: Entity,
    route: Route,
    cargo: Cargo,
    vehicle: Vehicle,
    fix: Fix,
) -> None:
    world.say(f'{parent.label_word.capitalize()} came in, saw the raised place, and smiled at their caution.')
    fix_scene(world, parent, route, fix)
    world.say(
        f'"Good noticing," {parent.label_word} said. "You stopped before the hump made trouble."'
    )
    tidy_and_retry(world, theme, driver, helper, cargo, route, vehicle)


def tell(
    theme: RoomTheme,
    vehicle: Vehicle,
    route: Route,
    cargo: Cargo,
    fix: Fix,
    *,
    driver_name: str = "Mia",
    driver_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    driver_age: int = 5,
    helper_age: int = 7,
) -> World:
    world = World()
    driver = world.add(
        Entity(
            id=driver_name,
            kind="character",
            type=driver_gender,
            role="driver",
            age=driver_age,
            traits=["busy", "eager"],
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            age=helper_age,
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    world.add(Entity(id="room", type="room", label=theme.room))
    v_ent = world.add(Entity(id="vehicle", type="vehicle", label=vehicle.label, wheels=True))
    r_ent = world.add(Entity(id="route", type="route", label=route.label))
    c_ent = world.add(Entity(id="cargo", type="cargo", label=cargo.label, soft_cargo=True))

    driver.memes["bold_base"] = BOLD_INIT
    helper.memes["care_base"] = initial_care(trait)
    v_ent.meters["stability"] = float(vehicle.wheels_size)
    r_ent.meters["roughness"] = float(route.severity)
    r_ent.meters["head_start"] = 0.0
    c_ent.meters["spilled"] = 0.0
    world.get("room").meters["mess"] = 0.0
    parent.meters["workload"] = 0.0
    world.facts["relation"] = relation

    play_setup(world, theme, driver, helper, cargo)
    notice_route(world, route, helper)

    world.para()
    tempt(world, driver, vehicle)
    warn(world, helper, driver, parent, route, cargo)

    averted = would_avert(relation, driver_age, helper_age, trait)
    if averted:
        back_down(world, driver, helper, parent, route)
        world.para()
        rescue_after_near_miss(world, theme, parent, driver, helper, route, cargo, vehicle, fix)
        outcome = "averted"
    else:
        defy(world, driver, helper, vehicle)
        world.para()
        bump_and_spill(world, driver, vehicle, c_ent, route)
        parent_arrives(world, parent)
        world.para()
        if c_ent.meters["spilled"] >= THRESHOLD and is_contained(fix, route):
            fix_scene(world, parent, route, fix)
            lesson(world, parent, driver, helper, route)
            world.para()
            tidy_and_retry(world, theme, driver, helper, cargo, route, vehicle)
            outcome = "contained"
        else:
            raise StoryError("(No story: the chosen fix does not honestly solve this hump safely.)")

    world.facts.update(
        theme=theme,
        vehicle=vehicle,
        route_cfg=route,
        cargo_cfg=cargo,
        fix=fix,
        driver=driver,
        helper=helper,
        parent=parent,
        route=world.get("route"),
        cargo=world.get("cargo"),
        outcome=outcome,
        spilled=world.get("cargo").meters["spilled"] >= THRESHOLD,
        taught=driver.memes["lesson"] >= THRESHOLD or outcome == "averted",
    )
    return world


THEMES = {
    "living_room": RoomTheme(
        id="living_room",
        room="living room",
        setup="Folded laundry sat on the sofa, and a stack of books waited for the low shelf.",
        errand="they were pretending to be tiny delivery workers",
        ending_image="the books reached the shelf in a neat little line, and nobody rushed the corners anymore",
        tags={"home", "slice_of_life"},
    ),
    "hallway": RoomTheme(
        id="hallway",
        room="hallway",
        setup="Shoes lined the wall, and library books were waiting to go back to their basket.",
        errand="they were making a game of putting things where they belonged",
        ending_image="the basket reached the table without a wobble, and the hallway felt calm again",
        tags={"home", "slice_of_life"},
    ),
    "bedroom": RoomTheme(
        id="bedroom",
        room="bedroom",
        setup="Stuffed animals were on the rug, and crayons needed to be carried back to the art box.",
        errand="they were playing cleanup before supper",
        ending_image="the crayon box stayed snug, and the room looked ready for bedtime stories",
        tags={"home", "slice_of_life"},
    ),
}

VEHICLES = {
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="the little red wagon",
        wheels_size=1,
        sound_roll="Rrrr-rrr",
        sound_bump="bump-bump",
        carry_verb="pull this wagon",
        tags={"wagon", "wheels"},
    ),
    "stroller": Vehicle(
        id="stroller",
        label="doll stroller",
        phrase="the doll stroller",
        wheels_size=1,
        sound_roll="Trr-trr",
        sound_bump="thup-thup",
        carry_verb="push this stroller",
        tags={"stroller", "wheels"},
    ),
    "cart": Vehicle(
        id="cart",
        label="book cart",
        phrase="the toy book cart",
        wheels_size=2,
        sound_roll="Rumble-rumble",
        sound_bump="tok-tok",
        carry_verb="roll this cart",
        tags={"cart", "wheels"},
    ),
}

ROUTES = {
    "rug_corner": Route(
        id="rug_corner",
        label="rug corner",
        phrase="a loose corner of the rug",
        hump_name="the rug hump",
        severity=2,
        movable=True,
        flatten_text="smoothed the rug flat and tucked the corner safely down",
        safe_after="on a clear strip of floor",
        tags={"rug", "hump"},
    ),
    "door_mat": Route(
        id="door_mat",
        label="door mat",
        phrase="a door mat curled up at one edge",
        hump_name="the mat hump",
        severity=2,
        movable=True,
        flatten_text="straightened the mat and moved it snug against the wall",
        safe_after="with the mat moved out of the path",
        tags={"mat", "hump"},
    ),
    "blanket_fold": Route(
        id="blanket_fold",
        label="blanket fold",
        phrase="a blanket left in a thick fold across the floor",
        hump_name="the blanket hump",
        severity=1,
        movable=True,
        flatten_text="picked up the blanket and folded it onto a chair",
        safe_after="with the floor opened up and smooth",
        tags={"blanket", "hump"},
    ),
    "tile_step": Route(
        id="tile_step",
        label="tile step",
        phrase="a doorway with a hard raised step",
        hump_name="the doorway hump",
        severity=3,
        movable=False,
        flatten_text="looked at the hard step and chose another route",
        safe_after="by taking a longer path with no bump at all",
        tags={"step", "hump"},
    ),
}

CARGOES = {
    "books": Cargo(
        id="books",
        label="the books",
        phrase="a small stack of books",
        spill_text="The books slid out with a flap and a clatter across the floor.",
        tidy_text="picked up the books and stacked them straight again",
        tags={"books", "cleanup"},
    ),
    "crayons": Cargo(
        id="crayons",
        label="the crayons",
        phrase="an open crayon box",
        spill_text="Crayons shot out in bright little lines. Tap tap tap -- they rolled under the chair.",
        tidy_text="gathered the crayons back into the box",
        tags={"crayons", "cleanup"},
    ),
    "socks": Cargo(
        id="socks",
        label="the socks",
        phrase="a basket of rolled socks",
        spill_text="Soft socks bounced out and scattered in every direction.",
        tidy_text="collected the socks and tucked them back into the basket",
        tags={"laundry", "cleanup"},
    ),
}

FIXES = {
    "flatten": Fix(
        id="flatten",
        sense=3,
        power=2,
        text="knelt down and",
        qa_text="flattened the raised floor covering so the wheels had a smooth path",
        tags={"flatten", "safety"},
    ),
    "reroute": Fix(
        id="reroute",
        sense=3,
        power=3,
        text="looked for a smoother path and",
        qa_text="chose a clear route that avoided the hump",
        tags={"reroute", "safety"},
    ),
    "step_over": Fix(
        id="step_over",
        sense=1,
        power=1,
        text="told the children to just go faster and hope for the best, then",
        qa_text="told them to hurry over it",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Theo"]
TRAITS = ["careful", "steady", "patient", "watchful", "curious", "cheerful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for vehicle_id, vehicle in VEHICLES.items():
            for route_id, route in ROUTES.items():
                if not route_at_risk(vehicle, route):
                    continue
                for cargo_id in CARGOES:
                    for fix_id, fix in FIXES.items():
                        if fix.sense >= SENSE_MIN and route.movable and is_contained(fix, route):
                            combos.append((theme_id, vehicle_id, route_id, cargo_id, fix_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    vehicle: str
    route: str
    cargo: str
    fix: str
    driver_name: str
    driver_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    driver_age: int = 5
    helper_age: int = 7
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
    "wheels": [
        (
            "Why can small wheels get stuck on a hump?",
            "Small wheels do not climb over bumps easily. If they hit a raised edge too fast, they can jolt and tip what they are carrying.",
        )
    ],
    "hump": [
        (
            "What is a hump in a rug or mat?",
            "A hump is a raised bump where the floor covering does not lie flat. It can catch feet or wheels and make someone trip or spill things.",
        )
    ],
    "rug": [
        (
            "Why should a rug lie flat on the floor?",
            "A flat rug is safer to walk and roll over. When a corner curls up, it can become a tripping or bumping hazard.",
        )
    ],
    "mat": [
        (
            "Why can a curled mat be a problem?",
            "A curled mat makes a little ridge in the path. Shoes or wheels can catch on that ridge and make someone stumble.",
        )
    ],
    "blanket": [
        (
            "Why is a blanket safer on a chair than in a heap on the floor?",
            "A blanket left on the floor can make a soft hump that people or toys bump into. Putting it on a chair keeps the path clear.",
        )
    ],
    "books": [
        (
            "Why do books fall when a cart jolts?",
            "A sudden bump can throw books sideways because they keep moving when the cart stops or tilts. That is why bumpy paths can make a stack slide out.",
        )
    ],
    "crayons": [
        (
            "Why do crayons roll everywhere when a box tips?",
            "Crayons are smooth and round, so when the box tips they can roll away quickly. A little bump can send them under furniture.",
        )
    ],
    "laundry": [
        (
            "Why can a basket spill if it tips?",
            "When a basket tilts, the things inside slide toward the low side and fall out. Even soft things can make a big mess when they scatter.",
        )
    ],
    "flatten": [
        (
            "How does flattening a rug or mat help?",
            "Flattening it takes away the raised bump that catches wheels or toes. A smooth path is easier and safer to cross.",
        )
    ],
    "reroute": [
        (
            "Why is it smart to choose another route around a bump?",
            "A new path can avoid the risky spot completely. Sometimes going a little farther is the safest choice.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "wheels",
    "hump",
    "rug",
    "mat",
    "blanket",
    "books",
    "crayons",
    "laundry",
    "flatten",
    "reroute",
]


def pair_noun(driver: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if driver.type == "boy" and helper.type == "boy":
            return "two brothers"
        if driver.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    driver = f["driver"]
    helper = f["helper"]
    theme = f["theme"]
    vehicle = f["vehicle"]
    route = f["route_cfg"]
    cargo = f["cargo_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short slice-of-life cautionary story for a 3-to-5-year-old that includes '
        f'the word "hump", uses dialogue and sound effects, and takes place in a {theme.room}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a home story where {driver.id} wants to use a {vehicle.label} over {route.hump_name}, "
            f"but {helper.id} warns {driver.pronoun('object')} and they stop before {cargo.label} spills.",
            f'Write a gentle cautionary story with spoken lines and little sounds where children notice a floor hump, ask a grown-up for help, and end by playing more safely.',
        ]
    return [
        base,
        f"Tell a cautionary story where {driver.id} rolls {cargo.label} in a {vehicle.label}, hits {route.hump_name}, and a grown-up helps fix the problem.",
        f'Write a simple home story with dialogue, a few sound effects, and a lesson about slowing down when the floor has a hump in it.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    driver = f["driver"]
    helper = f["helper"]
    parent = f["parent"]
    vehicle = f["vehicle"]
    route = f["route_cfg"]
    cargo = f["cargo_cfg"]
    fix = f["fix"]
    relation = f["relation"]
    pair = pair_noun(driver, helper, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {driver.id} and {helper.id}, and their {pw}. They were doing an ordinary home chore and turned it into play.",
        ),
        (
            "What problem was in their path?",
            f"There was a little hump made by {route.phrase}. It seemed small, but it could catch the wheels of the {vehicle.label}.",
        ),
        (
            f"Why did {helper.id} warn {driver.id}?",
            f"{helper.id} saw that the hump could catch the wheels and make {cargo.label} spill. The warning came before the bump because {helper.pronoun()} noticed the risky spot in time.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {driver.id} do after the warning?",
                f"{driver.id} stopped and went to get {pw}. That kept the little problem from turning into a bigger mess.",
            )
        )
        qa.append(
            (
                f"How did {pw} help?",
                f"{pw.capitalize()} {fix.qa_text}. After that, the children could finish the job without rushing over the hump.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when the wheels hit the hump?",
                f"{cargo.label.capitalize()} spilled when the wheels jolted over the hump. The bump mattered because the path was uneven and {driver.id} tried to go anyway.",
            )
        )
        qa.append(
            (
                f"How did {pw} solve the problem?",
                f"{pw.capitalize()} {fix.qa_text}. Then they cleaned up and tried again on a safer path.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that a small hump can still cause a real problem when wheels hit it fast. Next time, they know to stop, look, and ask for help first.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["vehicle"].tags) | set(f["route_cfg"].tags) | set(f["cargo_cfg"].tags) | set(f["fix"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="living_room",
        vehicle="wagon",
        route="rug_corner",
        cargo="books",
        fix="flatten",
        driver_name="Mia",
        driver_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        driver_age=5,
        helper_age=7,
    ),
    StoryParams(
        theme="hallway",
        vehicle="stroller",
        route="door_mat",
        cargo="socks",
        fix="flatten",
        driver_name="Sam",
        driver_gender="boy",
        helper_name="Zoe",
        helper_gender="girl",
        parent="father",
        trait="steady",
        relation="friends",
        driver_age=5,
        helper_age=5,
    ),
    StoryParams(
        theme="bedroom",
        vehicle="cart",
        route="blanket_fold",
        cargo="crayons",
        fix="flatten",
        driver_name="Lily",
        driver_gender="girl",
        helper_name="Noah",
        helper_gender="boy",
        parent="mother",
        trait="patient",
        relation="siblings",
        driver_age=4,
        helper_age=6,
    ),
]


def explain_rejection(vehicle: Vehicle, route: Route) -> str:
    if not route.movable:
        return (
            f"(No story: {route.hump_name} is a hard raised step, not a loose floor covering. "
            f"This world only tells stories where a grown-up can honestly make the path safer by fixing or moving the hump.)"
        )
    return (
        f"(No story: the {vehicle.label} is steady enough for {route.hump_name}, so there is no believable bump-and-spill problem here.)"
    )


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of these safer fixes: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.driver_age, params.helper_age, params.trait):
        return "averted"
    return "contained"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
risky(V, R) :- vehicle(V), route(R), wheel_size(V, W), severity(R, S), S >= W.
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
solves(R, F) :- route(R), fix(F), movable(R), power(F, P), severity(R, S), P >= S.
valid(T, V, R, C, F) :- theme(T), vehicle(V), route(R), cargo(C), risky(V, R), sensible(F), solves(R, F).

% --- outcome model ---------------------------------------------------------
care_now(T) :- trait(T), careful_trait(T).
init_care(5) :- trait(T), care_now(T).
init_care(3) :- trait(T), not care_now(T).
helper_older :- relation(siblings), driver_age(DA), helper_age(HA), HA > DA.
bonus(3) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- helper_older, authority(A), bold_init(BI), A > BI.

outcome(averted) :- averted.
outcome(contained) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for vid, v in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        lines.append(asp.fact("wheel_size", vid, v.wheels_size))
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("severity", rid, r.severity))
        if r.movable:
            lines.append(asp.fact("movable", rid))
    for cid in CARGOES:
        lines.append(asp.fact("cargo", cid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bold_init", int(BOLD_INIT)))
    for tr in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("driver_age", params.driver_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {f.id for f in sensible_fixes()}
    if c_sens == p_sens:
        print(f"OK: sensible fixes match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            ns = parser.parse_args([])
            params = resolve_params(ns, random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a hump in the path, and a safer way to finish the chore."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.vehicle:
        if not route_at_risk(VEHICLES[args.vehicle], ROUTES[args.route]) or not ROUTES[args.route].movable:
            raise StoryError(explain_rejection(VEHICLES[args.vehicle], ROUTES[args.route]))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    if args.route and not ROUTES[args.route].movable:
        vehicle = VEHICLES[args.vehicle] if args.vehicle else next(iter(VEHICLES.values()))
        raise StoryError(explain_rejection(vehicle, ROUTES[args.route]))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.vehicle is None or c[1] == args.vehicle)
        and (args.route is None or c[2] == args.route)
        and (args.cargo is None or c[3] == args.cargo)
        and (args.fix is None or c[4] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, vehicle, route, cargo, fix = rng.choice(sorted(combos))
    driver_name, driver_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=driver_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    driver_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        theme=theme,
        vehicle=vehicle,
        route=route,
        cargo=cargo,
        fix=fix,
        driver_name=driver_name,
        driver_gender=driver_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        driver_age=driver_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        vehicle = VEHICLES[params.vehicle]
        route = ROUTES[params.route]
        cargo = CARGOES[params.cargo]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not route_at_risk(vehicle, route) or not route.movable:
        raise StoryError(explain_rejection(vehicle, route))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not is_contained(fix, route):
        raise StoryError("(No story: the chosen fix does not honestly solve this hump safely.)")

    world = tell(
        theme=theme,
        vehicle=vehicle,
        route=route,
        cargo=cargo,
        fix=fix,
        driver_name=params.driver_name,
        driver_gender=params.driver_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        driver_age=params.driver_age,
        helper_age=params.helper_age,
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
        print(asp_program("", "#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, vehicle, route, cargo, fix) combos:\n")
        for theme, vehicle, route, cargo, fix in combos:
            print(f"  {theme:12} {vehicle:8} {route:12} {cargo:8} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.driver_name} & {p.helper_name}: {p.vehicle} over {p.route} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
