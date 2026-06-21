#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/goad_suspense_foreshadowing_moral_value_animal_story.py
===================================================================================

A standalone story world for a small animal tale about being goaded into a risky
choice near a stream, then learning that teasing is a poor guide and careful
listening is wiser.

Core shape
----------
A young animal spots something tempting on the far bank of a stream. Another
young animal uses teasing to goad the hero into proving how brave they are.
An older helper notices signs that the crossing is unsafe and warns them.
Depending on the ages and relationship, the warning may avert the attempt; if
not, the hero tries the crossing, the danger becomes real, and the helper uses
a sensible rescue method. The next day the animals choose a safer path.

The world is built around:
- typed entities with physical meters and emotional memes
- a tiny forward-chaining causal model
- a Python reasonableness gate plus an inline ASP twin
- state-driven prose, grounded Q&A, trace/debug output, and JSON output

Run it
------
    python storyworlds/worlds/gpt-5.4/goad_suspense_foreshadowing_moral_value_animal_story.py
    python storyworlds/worlds/gpt-5.4/goad_suspense_foreshadowing_moral_value_animal_story.py --route log --weather stormy
    python storyworlds/worlds/gpt-5.4/goad_suspense_foreshadowing_moral_value_animal_story.py --route path
    python storyworlds/worlds/gpt-5.4/goad_suspense_foreshadowing_moral_value_animal_story.py --helper basket
    python storyworlds/worlds/gpt-5.4/goad_suspense_foreshadowing_moral_value_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/goad_suspense_foreshadowing_moral_value_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/goad_suspense_foreshadowing_moral_value_animal_story.py --verify
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
NERVE_INIT = 5.0
STEADY_TRAITS = {"careful", "steady", "thoughtful", "patient"}


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
    floating: bool = False
    supportive: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class AnimalRole:
    id: str
    species: str
    home: str
    paws: str
    movement: str
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
    phrase: str
    smell: str
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
    crossing: str
    foothold: str
    risky: bool
    risk: int
    clue: str
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
class Weather:
    id: str
    opener: str
    omen: str
    water: str
    severity: int
    safe_for: set[str] = field(default_factory=set)
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
class HelperMethod:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
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


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "goader"}]

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = {}
        return clone
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


def _r_slip(world: World) -> list[str]:
    route = world.get("route")
    stream = world.get("stream")
    hero = world.get("hero")
    if hero.meters["crossing"] < THRESHOLD:
        return []
    if stream.meters["surge"] < THRESHOLD and route.meters["shaky"] < THRESHOLD:
        return []
    sig = ("slip",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["slipping"] += 1
    hero.memes["fear"] += 1
    return ["__slip__"]


def _r_distress(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.meters["slipping"] < THRESHOLD:
        return []
    sig = ("distress",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["alarm"] += 1
    world.get("stream").meters["danger"] += 1
    return ["__distress__"]


CAUSAL_RULES = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="distress", tag="social", apply=_r_distress),
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


def route_is_dangerous(route: Route, weather: Weather) -> bool:
    return route.risky and route.id not in weather.safe_for


def sensible_methods() -> list[HelperMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def crossing_severity(route: Route, weather: Weather) -> int:
    return route.risk + weather.severity


def is_rescued(method: HelperMethod, route: Route, weather: Weather) -> bool:
    return method.power >= crossing_severity(route, weather)


def initial_steady(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def would_back_down(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = (initial_steady(trait) + 1.0) + (3.0 if helper_older else 0.0)
    return helper_older and authority > NERVE_INIT


def predict_crossing(world: World) -> dict:
    sim = world.copy()
    attempt(sim, narrate=False)
    return {
        "slips": sim.get("hero").meters["slipping"] >= THRESHOLD,
        "danger": sim.get("stream").meters["danger"],
    }


def introduce(world: World, hero: Entity, goader: Entity, animal: AnimalRole,
              lure: Lure, weather: Weather) -> None:
    hero.memes["joy"] += 1
    goader.memes["mischief"] += 1
    world.say(
        f"{weather.opener}, {hero.id} the little {animal.species} padded out from "
        f"{animal.home}. On the far bank of the stream sat {lure.phrase}, and "
        f"{lure.smell} drifted over the water."
    )
    world.say(
        f"{goader.id} trotted beside {hero.pronoun('object')}, whiskers twitching "
        f"with curiosity."
    )


def foreshadow(world: World, route: Route, weather: Weather) -> None:
    route_ent = world.get("route")
    stream = world.get("stream")
    route_ent.meters["shaky"] = 1.0 if route.risk >= 2 else 0.0
    stream.meters["surge"] = 1.0 if weather.severity >= 2 else 0.0
    world.say(
        f"But the stream did not look friendly. {weather.omen}, and {route.clue}."
    )
    world.say(
        f"Below, the water {weather.water}, as if it already knew the day might "
        f"turn troublesome."
    )


def temptation(world: World, hero: Entity, goader: Entity, lure: Lure, route: Route) -> None:
    hero.memes["want"] += 1
    world.say(
        f'"Look at {lure.phrase}!" {goader.id} chirped. "If you hurry across '
        f'{route.phrase}, you can have it before anyone else."'
    )


def goad(world: World, hero: Entity, goader: Entity, route: Route) -> None:
    hero.memes["pride"] += 1
    hero.memes["nerve"] += 1
    world.say(
        f'Then {goader.id} gave a little laugh. "Or maybe you are not brave '
        f'enough for {route.crossing}," {goader.pronoun()} said, trying to goad '
        f'{hero.id} into proving something.'
    )


def warn(world: World, helper: Entity, hero: Entity, route: Route, weather: Weather) -> None:
    pred = predict_crossing(world)
    world.facts["predicted_slip"] = pred["slips"]
    world.facts["predicted_danger"] = pred["danger"]
    helper.memes["care"] += 1
    extra = ""
    if helper.memes["steady"] >= 6:
        extra = f" {helper.id} planted {helper.pronoun('possessive')} feet and would not smile at the teasing."
    world.say(
        f'{helper.id}, who was watching from a smooth stone nearby, called out, '
        f'"Do not race onto {route.phrase}. The stream is rising, and that way is '
        f'not safe today."{extra}'
    )


def back_down(world: World, hero: Entity, helper: Entity, route: Route, lure: Lure) -> None:
    hero.memes["relief"] += 1
    hero.memes["nerve"] = 0.0
    helper.memes["relief"] += 1
    world.say(
        f'{hero.id} looked at {route.phrase}, then at the water sliding past the '
        f'stones. The teasing suddenly sounded small.'
    )
    world.say(
        f'"You are right," {hero.id} admitted. "I do not want {lure.label} badly '
        f'enough to tumble into the stream."'
    )


def defy(world: World, hero: Entity, goader: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But {goader.id} smirked, and the silly challenge stung. {hero.id} lifted '
        f'{hero.pronoun("possessive")} chin and said, "I will show you."'
    )


def attempt(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    route = world.get("route")
    hero.meters["crossing"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"{hero.id} stepped onto {route.label}. For one heartbeat it held, "
            f"and then the whole crossing gave a nervous wobble."
        )


def peril(world: World, hero: Entity, route: Route) -> None:
    propagate(world, narrate=False)
    if hero.meters["slipping"] >= THRESHOLD:
        world.say(
            f"One paw skidded on {route.foothold}, and {hero.id} lurched sideways. "
            f"The stream snapped at the air below like a hungry mouth."
        )
        world.say(f'"Help!" cried {hero.id}.')
    else:
        world.say(
            f"{hero.id} hurried over {route.phrase}, though every step felt much "
            f"too close to the rushing water."
        )


def rescue(world: World, helper: Entity, method: HelperMethod, route: Route) -> None:
    hero = world.get("hero")
    hero.meters["slipping"] = 0.0
    hero.meters["safe"] += 1
    world.get("stream").meters["danger"] = 0.0
    world.say(
        f"{helper.id} moved at once and {method.text.replace('{route}', route.label)}."
    )
    world.say(
        f"In another breath, {hero.id} was back on the bank, trembling but safe."
    )


def rescue_fail(world: World, helper: Entity, method: HelperMethod, route: Route) -> None:
    hero = world.get("hero")
    hero.meters["soaked"] += 1
    hero.meters["safe"] += 1
    world.get("stream").meters["danger"] += 1
    world.say(
        f"{helper.id} {method.fail.replace('{route}', route.label)}."
    )
    world.say(
        f"{hero.id} splashed into the cold edge of the stream before scrambling to "
        f"the muddy bank, soaked and shivering."
    )


def lesson(world: World, helper: Entity, hero: Entity, goader: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["love"] += 1
    goader.memes["shame"] += 1
    world.say(
        f'{helper.id} wrapped {hero.id} in a broad leaf and spoke softly. "Real '
        f'bravery is not jumping because someone laughs. Real bravery is stopping '
        f'to think."'
    )
    world.say(
        f"{goader.id} stared at the ground. The teasing that had seemed funny a "
        f"moment ago now felt mean and foolish."
    )


def grim_lesson(world: World, helper: Entity, hero: Entity, goader: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["fear"] += 1
    goader.memes["shame"] += 1
    world.say(
        f'{helper.id} held {hero.id} close until the shivering slowed. "Let this '
        f'be the last time teasing pushes you toward danger," {helper.pronoun()} said.'
    )
    world.say(
        f"{goader.id} whispered an apology. No one argued after that, because the "
        f"cold stream had already given the lesson."
    )


def safe_end(world: World, hero: Entity, helper: Entity, lure: Lure) -> None:
    hero.memes["joy"] += 1
    hero.memes["safety"] += 1
    world.say(
        f"The next day, when the water lay low and clear, {helper.id} led "
        f"{hero.id} along the shallow stepping place upstream."
    )
    world.say(
        f"Together they reached {lure.phrase} without a single wobble, and "
        f"{hero.id} carried it home with quiet pride instead of showy pride."
    )


ANIMALS = {
    "rabbit": AnimalRole(
        id="rabbit",
        species="rabbit",
        home="the ferny burrow",
        paws="paws",
        movement="hopped",
        tags={"rabbit", "forest"},
    ),
    "squirrel": AnimalRole(
        id="squirrel",
        species="squirrel",
        home="the oak hollow",
        paws="paws",
        movement="scampered",
        tags={"squirrel", "forest"},
    ),
    "mouse": AnimalRole(
        id="mouse",
        species="mouse",
        home="the warm hedge hole",
        paws="paws",
        movement="scurried",
        tags={"mouse", "forest"},
    ),
}

LURES = {
    "berries": Lure(
        id="berries",
        label="berries",
        phrase="a bright patch of blackberries",
        smell="their sweet smell",
        tags={"berries", "food"},
    ),
    "apple": Lure(
        id="apple",
        label="apple",
        phrase="a red fallen apple",
        smell="the crisp apple smell",
        tags={"apple", "food"},
    ),
    "mushrooms": Lure(
        id="mushrooms",
        label="mushrooms",
        phrase="a neat ring of fat mushrooms",
        smell="their earthy smell",
        tags={"mushrooms", "forest_food"},
    ),
}

ROUTES = {
    "log": Route(
        id="log",
        label="the mossy log",
        phrase="the mossy log",
        crossing="that slippery log",
        foothold="the slick green moss",
        risky=True,
        risk=2,
        clue="the mossy log sagged in the middle",
        tags={"log", "crossing"},
    ),
    "branch": Route(
        id="branch",
        label="the narrow branch bridge",
        phrase="the narrow branch bridge",
        crossing="that narrow branch bridge",
        foothold="the thin bark",
        risky=True,
        risk=3,
        clue="the branch bridge gave a soft creak with every gust",
        tags={"bridge", "crossing"},
    ),
    "stones": Route(
        id="stones",
        label="the wet stepping stones",
        phrase="the wet stepping stones",
        crossing="those wet stepping stones",
        foothold="the shiny stone edge",
        risky=True,
        risk=1,
        clue="the stepping stones shone with a skin of water",
        tags={"stones", "crossing"},
    ),
    "path": Route(
        id="path",
        label="the dry bank path",
        phrase="the dry bank path",
        crossing="that dry bank path",
        foothold="the packed earth",
        risky=False,
        risk=0,
        clue="the path curled safely beside the reeds",
        tags={"path"},
    ),
}

WEATHERS = {
    "breezy": Weather(
        id="breezy",
        opener="On a pale breezy afternoon",
        omen="small leaves spun in circles over the water",
        water="shivered around the roots",
        severity=1,
        safe_for={"stones"},
        tags={"wind"},
    ),
    "misty": Weather(
        id="misty",
        opener="On a cool misty morning",
        omen="a damp hush sat over the bank and hid the far reeds",
        water="slid dark and secret between the stones",
        severity=1,
        safe_for={"stones"},
        tags={"mist"},
    ),
    "stormy": Weather(
        id="stormy",
        opener="Before a stormy evening",
        omen="the reeds bowed low and the clouds pressed down like a gray lid",
        water="growled and swelled against the bank",
        severity=2,
        safe_for=set(),
        tags={"storm"},
    ),
}

METHODS = {
    "vine": HelperMethod(
        id="vine",
        label="a trailing vine",
        sense=3,
        power=4,
        text="caught a trailing vine in {helper_possessive} teeth and swung it over {route}",
        fail="swung a trailing vine toward {route}, but the current jerked harder than the vine could hold",
        qa_text="used a trailing vine to pull the child back from the crossing",
        tags={"vine", "rescue"},
    ),
    "branch_hook": HelperMethod(
        id="branch_hook",
        label="a forked branch",
        sense=3,
        power=3,
        text="snatched up a forked branch and hooked it firmly across {route} for a hold",
        fail="jabbed a forked branch toward {route}, but it slid away on the wet wood",
        qa_text="used a forked branch to give the child something safe to grab",
        tags={"branch", "rescue"},
    ),
    "basket": HelperMethod(
        id="basket",
        label="a berry basket",
        sense=1,
        power=1,
        text="shoved a berry basket toward {route}",
        fail="pushed a berry basket toward {route}, but it bumped uselessly in the current",
        qa_text="tried to help with a berry basket",
        tags={"basket"},
    ),
}

GIRLISH_NAMES = ["Pip", "Mimi", "Tansy", "Nibbles", "Moss"]
BOYISH_NAMES = ["Bram", "Hazel", "Rill", "Nutkin", "Pico"]
NEUTRAL_NAMES = ["Pip", "Moss", "Nib", "Fern", "Rill", "Tumble", "Pebble"]
TRAITS = ["careful", "steady", "thoughtful", "patient", "curious", "bouncy", "eager"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_methods():
        return combos
    for animal_id in ANIMALS:
        for route_id, route in ROUTES.items():
            for weather_id, weather in WEATHERS.items():
                if route_is_dangerous(route, weather):
                    combos.append((animal_id, route_id, weather_id))
    return combos


@dataclass
class StoryParams:
    animal: str
    lure: str
    route: str
    weather: str
    helper: str
    hero: str
    goader: str
    helper_name: str
    trait: str
    relation: str
    hero_age: int = 4
    helper_age: int = 6
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
    "log": [
        (
            "Why can a mossy log be slippery?",
            "Moss holds water and makes the wood slick. Small feet can slide on it very easily.",
        )
    ],
    "bridge": [
        (
            "Why is a narrow bridge harder to cross safely?",
            "A narrow bridge leaves very little room for your feet. One wobble can throw you off balance.",
        )
    ],
    "stones": [
        (
            "Why can wet stones be tricky to walk on?",
            "Wet stones get shiny and slick. If you rush, your feet can slide.",
        )
    ],
    "storm": [
        (
            "Why is a stream more dangerous before a storm?",
            "Wind and rain can make the water rise and move faster. That means a crossing that was safe before can become unsafe.",
        )
    ],
    "mist": [
        (
            "Why can mist make things harder to judge?",
            "Mist hides edges and makes the air look blurry. That can make a path seem calmer than it really is.",
        )
    ],
    "wind": [
        (
            "Why can wind make a crossing harder?",
            "Wind shakes branches and pushes at your body. Even a small gust can upset your balance.",
        )
    ],
    "vine": [
        (
            "How can a vine help in a rescue?",
            "A strong vine can give someone something to hold onto or be pulled by. It is useful only if it is strong enough and someone uses it quickly.",
        )
    ],
    "branch": [
        (
            "How can a forked branch help near water?",
            "A forked branch can reach farther than a paw. It can give a slipping animal a safe thing to grab.",
        )
    ],
    "rescue": [
        (
            "What should you do if a friend is in danger near water?",
            "Call for help from a grown helper right away. Then use a safe rescue tool instead of rushing into danger yourself.",
        )
    ],
    "food": [
        (
            "Why should you not hurry into danger just for food?",
            "Food can wait, but danger can grow quickly. It is wiser to stay safe and find another way.",
        )
    ],
    "teasing": [
        (
            "Why is teasing a bad reason to do something risky?",
            "Teasing tries to push feelings instead of using good sense. A brave choice should come from thinking, not from wanting to impress someone.",
        )
    ],
}
KNOWLEDGE_ORDER = ["log", "bridge", "stones", "storm", "mist", "wind", "vine", "branch", "rescue", "food", "teasing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    route = f["route_cfg"]
    lure = f["lure"]
    weather = f["weather"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write an animal story for a young child that includes the word "goad" and a warning about crossing {route.phrase}.',
            f"Tell a suspenseful forest story where {f['goader'].id} tries to goad {hero.id}, but an older helper's warning stops the risky choice before anything bad happens.",
            f"Write a gentle moral tale with foreshadowing signs like {weather.omen}, where a young animal chooses sense over pride and waits for a safer way to reach {lure.phrase}.",
        ]
    if outcome == "rescued":
        return [
            f'Write an animal story for a young child that includes the word "goad" and a dangerous crossing over {route.phrase}.',
            f"Tell a suspenseful animal tale where teasing pushes {hero.id} toward danger, the warning signs come true, and a helper rescues the child safely.",
            f"Write a moral story with foreshadowing and a happy ending, showing that teasing is a poor guide and careful listening is wiser than showing off.",
        ]
    return [
        f'Write an animal story for a young child that includes the word "goad" and a stream crossing gone wrong.',
        f"Tell a suspenseful cautionary tale where a teasing animal pushes {hero.id} onto {route.phrase} before a storm, and the rescue is only partly successful.",
        f"Write a moral animal story with foreshadowing, danger, and an apology after a foolish challenge leads to a cold lesson.",
    ]


def pair_noun(relation: str) -> str:
    return "siblings" if relation == "siblings" else "friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    goader = f["goader"]
    helper = f["helper"]
    lure = f["lure"]
    route = f["route_cfg"]
    weather = f["weather"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {f['animal_cfg'].species}, {goader.id} who teased {hero.pronoun('object')}, and {helper.id} who tried to keep everyone safe.",
        ),
        (
            f"What tempted {hero.id} to cross the stream?",
            f"{hero.id} wanted {lure.phrase} on the far bank. The food looked close enough to reach, which made the dangerous crossing feel tempting.",
        ),
        (
            f"How did {goader.id} try to push {hero.id} into danger?",
            f"{goader.id} tried to goad {hero.id} by teasing {hero.pronoun('object')} about bravery. That made the choice feel like something to prove instead of something to think about.",
        ),
        (
            "What warning signs came before the danger?",
            f"The story showed warning signs first: {weather.omen}, and {route.clue}. Those details foreshadowed that the crossing would not hold steady.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"Why did {hero.id} decide not to cross?",
                f"{hero.id} listened to {helper.id} and finally noticed how unsafe the stream looked. The teasing lost its power once {hero.pronoun('object')} thought about the real danger.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and safely. The next day they used a shallow stepping place instead of {route.phrase}, which shows they learned to wait for a better way.",
            )
        )
    elif f["outcome"] == "rescued":
        qa.append(
            (
                f"What happened when {hero.id} stepped onto {route.phrase}?",
                f"{hero.id} slipped and cried for help. The danger the story hinted at became real as soon as the crossing wobbled under {hero.pronoun('possessive')} feet.",
            )
        )
        qa.append(
            (
                f"How did {helper.id} help?",
                f"{helper.id} {method.qa_text}. The rescue worked because {helper.pronoun()} acted quickly with a tool strong enough for the rushing water.",
            )
        )
        qa.append(
            (
                "What was the lesson?",
                f"The lesson was that you should not let teasing choose for you. Thinking first is braver than showing off.",
            )
        )
    else:
        qa.append(
            (
                f"Was the rescue easy?",
                f"No. {helper.id} tried to help, but the stream was stronger than the tool. {hero.id} got out safely in the end, yet came away soaked and badly frightened.",
            )
        )
        qa.append(
            (
                "What did everyone learn?",
                f"They learned that teasing can push a small mistake into a real danger. After the cold tumble, even {goader.id} understood that pride is not worth the risk.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["route_cfg"].tags) | set(f["weather"].tags) | set(f["method"].tags)
    tags |= {"rescue", "teasing"}
    tags |= set(f["lure"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(
    animal: AnimalRole,
    lure: Lure,
    route: Route,
    weather: Weather,
    method: HelperMethod,
    hero_name: str = "Pip",
    goader_name: str = "Nib",
    helper_name: str = "Aunt Bramble",
    trait: str = "careful",
    relation: str = "siblings",
    hero_age: int = 4,
    helper_age: int = 6,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=animal.species,
            label=hero_name,
            role="hero",
            age=hero_age,
            attrs={"relation": relation},
        )
    )
    goader = world.add(
        Entity(
            id=goader_name,
            kind="character",
            type=animal.species,
            label=goader_name,
            role="goader",
            age=hero_age,
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=animal.species,
            label=helper_name,
            role="helper",
            age=helper_age,
            attrs={"relation": relation},
        )
    )
    route_ent = world.add(
        Entity(
            id="route",
            kind="thing",
            type="route",
            label=route.label,
            fragile=route.risky,
            attrs={"route_id": route.id},
        )
    )
    world.add(
        Entity(
            id="stream",
            kind="thing",
            type="stream",
            label="the stream",
            attrs={"weather": weather.id},
        )
    )

    hero.memes["nerve"] = NERVE_INIT
    helper.memes["steady"] = initial_steady(trait)
    goader.memes["mischief"] = 1.0
    hero.meters["crossing"] = 0.0
    hero.meters["slipping"] = 0.0
    hero.meters["safe"] = 0.0
    world.get("stream").meters["danger"] = 0.0
    world.get("stream").meters["surge"] = 0.0
    route_ent.meters["shaky"] = 0.0

    introduce(world, hero, goader, animal, lure, weather)
    foreshadow(world, route, weather)

    world.para()
    temptation(world, hero, goader, lure, route)
    goad(world, hero, goader)
    warn(world, helper, hero, route, weather)

    averted = would_back_down(relation, hero_age, helper_age, trait)
    if averted:
        back_down(world, hero, helper, route, lure)
        world.para()
        safe_end(world, hero, helper, lure)
        outcome = "averted"
    else:
        defy(world, hero, goader)
        world.para()
        attempt(world, narrate=True)
        peril(world, hero, route)
        world.para()
        if hero.meters["slipping"] >= THRESHOLD:
            if is_rescued(method, route, weather):
                rescue(world, helper, method, route)
                lesson(world, helper, hero, goader)
                world.para()
                safe_end(world, hero, helper, lure)
                outcome = "rescued"
            else:
                rescue_fail(world, helper, method, route)
                grim_lesson(world, helper, hero, goader)
                outcome = "soaked"
        else:
            world.say(
                f"{hero.id} reached the far bank, but the crossing scared {hero.pronoun('object')} more than the prize pleased {hero.pronoun('object')}."
            )
            lesson(world, helper, hero, goader)
            world.para()
            safe_end(world, hero, helper, lure)
            outcome = "rescued"

    world.facts.update(
        animal_cfg=animal,
        lure=lure,
        route_cfg=route,
        weather=weather,
        method=method,
        hero=hero,
        goader=goader,
        helper=helper,
        outcome=outcome,
        relation=relation,
        predicted_slip=world.facts.get("predicted_slip", False),
        predicted_danger=world.facts.get("predicted_danger", 0.0),
    )
    return world


CURATED = [
    StoryParams(
        animal="rabbit",
        lure="berries",
        route="log",
        weather="stormy",
        helper="vine",
        hero="Pip",
        goader="Nib",
        helper_name="Aunt Bramble",
        trait="careful",
        relation="siblings",
        hero_age=4,
        helper_age=7,
    ),
    StoryParams(
        animal="squirrel",
        lure="apple",
        route="branch",
        weather="misty",
        helper="branch_hook",
        hero="Moss",
        goader="Rill",
        helper_name="Old Hazel",
        trait="thoughtful",
        relation="friends",
        hero_age=5,
        helper_age=8,
    ),
    StoryParams(
        animal="mouse",
        lure="mushrooms",
        route="branch",
        weather="stormy",
        helper="branch_hook",
        hero="Fern",
        goader="Pebble",
        helper_name="Grandma Thistle",
        trait="bouncy",
        relation="friends",
        hero_age=4,
        helper_age=6,
    ),
    StoryParams(
        animal="rabbit",
        lure="apple",
        route="stones",
        weather="breezy",
        helper="vine",
        hero="Tumble",
        goader="Rill",
        helper_name="Aunt Bramble",
        trait="steady",
        relation="siblings",
        hero_age=4,
        helper_age=7,
    ),
    StoryParams(
        animal="squirrel",
        lure="berries",
        route="log",
        weather="misty",
        helper="vine",
        hero="Pebble",
        goader="Nib",
        helper_name="Old Hazel",
        trait="patient",
        relation="friends",
        hero_age=5,
        helper_age=8,
    ),
]


def explain_rejection(route: Route, weather: Weather) -> str:
    if not route.risky:
        return (
            f"(No story: {route.phrase} is already safe, so there is no real suspense, rescue, or moral turn. "
            f"Pick a risky crossing like a log, branch bridge, or wet stones.)"
        )
    if route.id in weather.safe_for:
        return (
            f"(No story: in {weather.id} weather, {route.phrase} is calm enough that the crossing is not truly dangerous. "
            f"Pick rougher weather or a riskier route.)"
        )
    return "(No story: this route and weather do not make a convincing danger.)"


def explain_method(mid: str) -> str:
    m = METHODS[mid]
    better = ", ".join(sorted(x.id for x in sensible_methods()))
    return (
        f"(Refusing helper method '{mid}': it scores too low on common sense "
        f"(sense={m.sense} < {SENSE_MIN}). Try a stronger rescue like {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_back_down(params.relation, params.hero_age, params.helper_age, params.trait):
        return "averted"
    method = METHODS[params.helper]
    route = ROUTES[params.route]
    weather = WEATHERS[params.weather]
    return "rescued" if is_rescued(method, route, weather) else "soaked"


ASP_RULES = r"""
dangerous(Route, Weather) :- route(Route), weather(Weather), risky(Route), not safe_for(Weather, Route).

sensible(Method) :- method(Method), sense(Method, S), sense_min(M), S >= M.

valid(Animal, Route, Weather) :- animal(Animal), dangerous(Route, Weather).

steady_now(T) :- trait(T), is_steady(T).
init_steady(5) :- trait(T), steady_now(T).
init_steady(3) :- trait(T), not steady_now(T).
helper_older :- relation(siblings), hero_age(H), helper_age(A), A > H.
bonus(3) :- helper_older.
bonus(0) :- not helper_older.
authority(S + 1 + B) :- init_steady(S), bonus(B).
averted :- helper_older, authority(A), nerve_init(N), A > N.

severity(R + W) :- chosen_route(Route), chosen_weather(Weather), risk(Route, R), weather_severity(Weather, W).
rescued :- chosen_method(Method), power(Method, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(rescued) :- not averted, rescued.
outcome(soaked) :- not averted, not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id in ANIMALS:
        lines.append(asp.fact("animal", animal_id))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        if route.risky:
            lines.append(asp.fact("risky", route_id))
        lines.append(asp.fact("risk", route_id, route.risk))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("weather_severity", weather_id, weather.severity))
        for rid in sorted(weather.safe_for):
            lines.append(asp.fact("safe_for", weather_id, rid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("nerve_init", int(NERVE_INIT)))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("is_steady", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_method", params.helper),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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

    clingo_sens = set(asp_sensible())
    python_sens = {m.id for m in sensible_methods()}
    if clingo_sens == python_sens:
        print(f"OK: sensible methods match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for s in range(200):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a young animal is goaded toward a risky crossing and learns a safer kind of bravery."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--helper", choices=METHODS)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, avoid: set[str]) -> str:
    pool = [n for n in NEUTRAL_NAMES if n not in avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and not ROUTES[args.route].risky:
        weather = WEATHERS[args.weather] if args.weather else next(iter(WEATHERS.values()))
        raise StoryError(explain_rejection(ROUTES[args.route], weather))
    if args.route and args.weather:
        route = ROUTES[args.route]
        weather = WEATHERS[args.weather]
        if not route_is_dangerous(route, weather):
            raise StoryError(explain_rejection(route, weather))
    if args.helper and METHODS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_method(args.helper))

    combos = [
        c
        for c in valid_combos()
        if (args.animal is None or c[0] == args.animal)
        and (args.route is None or c[1] == args.route)
        and (args.weather is None or c[2] == args.weather)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal, route, weather = rng.choice(sorted(combos))
    lure = args.lure or rng.choice(sorted(LURES))
    helper = args.helper or rng.choice(sorted(m.id for m in sensible_methods()))
    relation = args.relation or rng.choice(["siblings", "friends"])
    hero = pick_name(rng, set())
    goader = pick_name(rng, {hero})
    helper_name = rng.choice(["Aunt Bramble", "Old Hazel", "Grandma Thistle", "Uncle Reed"])
    trait = rng.choice(TRAITS)
    hero_age = rng.choice([3, 4, 5])
    helper_age = rng.choice([6, 7, 8])
    return StoryParams(
        animal=animal,
        lure=lure,
        route=route,
        weather=weather,
        helper=helper,
        hero=hero,
        goader=goader,
        helper_name=helper_name,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal '{params.animal}'.)")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure '{params.lure}'.)")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route '{params.route}'.)")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather '{params.weather}'.)")
    if params.helper not in METHODS:
        raise StoryError(f"(Unknown helper method '{params.helper}'.)")

    route = ROUTES[params.route]
    weather = WEATHERS[params.weather]
    method = METHODS[params.helper]
    if not route_is_dangerous(route, weather):
        raise StoryError(explain_rejection(route, weather))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.helper))

    world = tell(
        animal=ANIMALS[params.animal],
        lure=LURES[params.lure],
        route=route,
        weather=weather,
        method=method,
        hero_name=params.hero,
        goader_name=params.goader,
        helper_name=params.helper_name,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, route, weather) combos:\n")
        for animal, route, weather in combos:
            print(f"  {animal:8} {route:8} {weather}")
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
            header = f"### {p.hero}: {p.route} in {p.weather} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
