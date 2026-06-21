#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shrink_rhyme_suspense_tall_tale.py
=============================================================

A standalone story world about a child, a giant fair balloon, and the safest
way to make it shrink before the wind steals it. The prose leans playful and
tall-tale big, with a little rhyme threaded through the suspense.

Reference seed:
---------------
Write a story that includes the word "shrink", uses rhyme and suspense, and
stays close to the style of a tall tale.

Run it
------
python storyworlds/worlds/gpt-5.4/shrink_rhyme_suspense_tall_tale.py
python storyworlds/worlds/gpt-5.4/shrink_rhyme_suspense_tall_tale.py --shape dragon --weather squall --tether twine
python storyworlds/worlds/gpt-5.4/shrink_rhyme_suspense_tall_tale.py --response pin_prick
python storyworlds/worlds/gpt-5.4/shrink_rhyme_suspense_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/shrink_rhyme_suspense_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/shrink_rhyme_suspense_tall_tale.py --verify
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
SENSE_MIN = 2
BRAVADO_INIT = 5.0
CAREFUL_TRAITS = {"careful", "steady", "sensible", "patient"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "uncle": "uncle", "aunt": "aunt"}.get(
            self.type, self.type
        )
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
class Shape:
    id: str
    label: str
    boast: str
    opener: str
    sky_compare: str
    lift: int
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
class Weather:
    id: str
    sky: str
    gust_line: str
    strength: int
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
class Tether:
    id: str
    label: str
    phrase: str
    grip: int
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
class Response:
    id: str
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
class StoryParams:
    shape: str = "rooster"
    weather: str = "gusty"
    tether: str = "rope"
    response: str = "reel_and_valve"
    hero: str = "Boone"
    hero_gender: str = "boy"
    helper: str = "June"
    helper_gender: str = "girl"
    grownup: str = "uncle"
    trait: str = "careful"
    delay: int = 0
    hero_age: int = 7
    helper_age: int = 5
    relation: str = "siblings"
    trust: int = 6
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
        return [e for e in self.entities.values() if e.role in {"hero", "helper"}]

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


def _r_wind_strain(world: World) -> list[str]:
    balloon = world.get("balloon")
    if balloon.meters["lift"] < THRESHOLD:
        return []
    weather_strength = world.facts["weather_strength"]
    tether_grip = world.facts["tether_grip"]
    risk = weather_strength + balloon.meters["lift"] - tether_grip
    if risk < 1:
        return []
    sig = ("strain", int(risk))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    balloon.meters["strain"] += float(risk)
    world.get("yard").meters["danger"] += 1.0
    for kid in world.kids():
        kid.memes["fear"] += 1.0
    return ["__strain__"]


CAUSAL_RULES = [
    Rule(name="wind_strain", tag="physical", apply=_r_wind_strain),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SHAPES = {
    "rooster": Shape(
        id="rooster",
        label="rooster balloon",
        boast="Its tail curled like six bright rainbows tied together.",
        opener="a rooster",
        sky_compare="a sunrise rooster",
        lift=1,
        tags={"balloon", "parade"},
    ),
    "catfish": Shape(
        id="catfish",
        label="catfish balloon",
        boast="Its whiskers were so long they looked fit to tickle the moon.",
        opener="a catfish",
        sky_compare="a silver catfish",
        lift=2,
        tags={"balloon", "parade"},
    ),
    "dragon": Shape(
        id="dragon",
        label="dragon balloon",
        boast="Its paper scales flashed so wide and wild that crows flew around it twice before believing what they saw.",
        opener="a dragon",
        sky_compare="a green dragon",
        lift=3,
        tags={"balloon", "parade"},
    ),
}

WEATHER = {
    "breezy": Weather(
        id="breezy",
        sky="The clouds loafed around like sleepy sheep.",
        gust_line="Then a breeze came skipping over the fairground and gave the balloon a teasing tug.",
        strength=1,
        tags={"wind"},
    ),
    "gusty": Weather(
        id="gusty",
        sky="The clouds stacked up like gray biscuits over the grandstand.",
        gust_line="Then the wind came whistling low and fast, and the balloon gave one hard pull that made every ribbon snap and clap.",
        strength=2,
        tags={"wind", "gust"},
    ),
    "squall": Weather(
        id="squall",
        sky="The sky hunched dark as if it meant to gulp the whole fair in one bite.",
        gust_line="Then a sharp squall shouldered through the midway, and the balloon lunged so hard the tether groaned like a wagon axle.",
        strength=3,
        tags={"wind", "gust", "storm"},
    ),
}

TETHERS = {
    "chain": Tether(
        id="chain",
        label="chain",
        phrase="a brass chain thick as a fence snake",
        grip=4,
        tags={"tether"},
    ),
    "rope": Tether(
        id="rope",
        label="rope",
        phrase="a rope braided thicker than a pony's tail",
        grip=2,
        tags={"tether"},
    ),
    "twine": Tether(
        id="twine",
        label="twine",
        phrase="a loop of bakery twine that looked brave but thin",
        grip=1,
        tags={"tether"},
    ),
}

RESPONSES = {
    "reel_and_valve": Response(
        id="reel_and_valve",
        sense=3,
        power=5,
        text="dug in hard, reeled the balloon down hand over hand, and opened the brass valve so the big thing could shrink with a long, hissing sigh",
        fail="dug in hard and reached for the brass valve, but the balloon was already jerking too high and too wild to bring down",
        qa_text="reeled the balloon down and opened the brass valve so it could shrink safely",
        tags={"valve", "safe"},
    ),
    "tail_hold_valve": Response(
        id="tail_hold_valve",
        sense=3,
        power=3,
        text="grabbed the balloon by its flapping tail, hugged it low, and turned the brass valve until it began to shrink slowly instead of bursting",
        fail="grabbed for the tail and turned the brass valve, but the wind snapped the balloon upward before enough air could hiss out",
        qa_text="held the balloon low and turned the brass valve until it shrank",
        tags={"valve", "safe"},
    ),
    "hang_on": Response(
        id="hang_on",
        sense=2,
        power=2,
        text="wrapped both arms around the tether, planted both boots, and kept hold until the helper could reach the brass valve and let the balloon shrink",
        fail="hung on with both hands, but hanging on alone could not tame the sky-pulling balloon",
        qa_text="held on to the tether long enough for the balloon to be shrunk",
        tags={"tether", "safe"},
    ),
    "pin_prick": Response(
        id="pin_prick",
        sense=1,
        power=1,
        text="jabbed the balloon with a hatpin to make it shrink all at once",
        fail="jabbed at the balloon with a hatpin and made the great thing leap and whirl",
        qa_text="jabbed the balloon with a pin",
        tags={"pin", "unsafe"},
    ),
}

GIRL_NAMES = ["June", "Mabel", "Willa", "Nell", "Clara", "Sadie", "Minnie", "Dora"]
BOY_NAMES = ["Boone", "Hank", "Toby", "Jesse", "Eli", "Cal", "Otis", "Beau"]
TRAITS = ["careful", "steady", "sensible", "patient", "curious", "bold"]


def risk_index(shape: Shape, weather: Weather, tether: Tether) -> int:
    return weather.strength + shape.lift - tether.grip


def suspense_at_risk(shape: Shape, weather: Weather, tether: Tether) -> bool:
    return risk_index(shape, weather, tether) >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity(shape: Shape, weather: Weather, tether: Tether, delay: int) -> int:
    return risk_index(shape, weather, tether) + delay


def is_contained(shape: Shape, weather: Weather, tether: Tether, response: Response, delay: int) -> bool:
    return response.power >= severity(shape, weather, tether, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = initial_care(trait) + 1.0 + (3.0 if helper_older else 0.0)
    return helper_older and authority > BRAVADO_INIT


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for shape_id, shape in SHAPES.items():
        for weather_id, weather in WEATHER.items():
            for tether_id, tether in TETHERS.items():
                if suspense_at_risk(shape, weather, tether):
                    combos.append((shape_id, weather_id, tether_id))
    return combos


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    balloon = sim.get("balloon")
    balloon.meters["lift"] += 1.0
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("yard").meters["danger"],
        "strain": balloon.meters["strain"],
    }


def introduce(world: World, hero: Entity, shape: Shape, tether: Tether) -> None:
    hero.memes["pride"] += 1.0
    world.say(
        f"At the county fair, {hero.id} puffed up {shape.opener} for the noon parade. "
        f"Before long it was less like a balloon and more like a floating barn with manners. {shape.boast}"
    )
    world.say(
        f"{hero.id} tied it down with {tether.phrase} and grinned. "
        f'"Big and bright, a windy sight," {hero.pronoun()} sang.'
    )


def weather_turn(world: World, weather: Weather) -> None:
    world.say(weather.sky)
    world.say(weather.gust_line)


def need_to_shrink(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f'The tether stretched tight enough to hum. "{helper.id}," {hero.id} said, '
        f'"if this thing climbs any higher, it will pull my boots clean through the ground."'
    )


def tempt(world: World, hero: Entity) -> None:
    hero.memes["bravado"] += 1.0
    world.say(
        f'{hero.id} swallowed once and pointed to the shiny brass valve. '
        f'"Maybe we can make it shrink nice and slow," {hero.pronoun()} said, '
        f"though the wind kept yanking at the words."
    )


def warn(world: World, helper: Entity, hero: Entity, grownup: Entity) -> None:
    pred = predict_trouble(world)
    helper.memes["care"] += 1.0
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_strain"] = pred["strain"]
    extra = ""
    if helper.memes["care"] >= 6:
        extra = f" {helper.id} set both feet wide and would not budge an inch."
    world.say(
        f'{helper.id} looked from the straining tether to {grownup.label_word}\'s tool apron. '
        f'"Not with a pin. If you prick it, it won\'t shrink slow. It will jump and whip and fly."{extra}'
    )
    if pred["strain"] >= THRESHOLD:
        world.say(
            f'{helper.id} added, "Hear that line sing? That is trouble on a string."'
        )


def back_down(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["relief"] += 1.0
    helper.memes["relief"] += 1.0
    world.say(
        f'{hero.id} looked at {helper.id}, then at the dancing valve, and let out a long breath. '
        f'"Slow, not fast. Small, not tall," {hero.pronoun()} said, and put the pin away without touching the balloon.'
    )


def reach_anyway(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["defiance"] += 1.0
    older_sib = hero.attrs.get("relation") == "siblings" and hero.age > helper.age
    if older_sib:
        world.say(
            f'{hero.id} shook {hero.pronoun("possessive")} head. "I can fix it quick," '
            f'{hero.pronoun()} said, and because {helper.id} had always seen {hero.pronoun("object")} act big, '
            f'{helper.id} could not stop {hero.pronoun("object")} in that first fast moment.'
        )
    else:
        world.say(
            f'{hero.id} shook {hero.pronoun("possessive")} head. "Quick is slick," '
            f'{hero.pronoun()} said, and reached anyway.'
        )


def strain(world: World, balloon: Entity, shape: Shape) -> None:
    balloon.meters["lift"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"The {shape.label} heaved upward so hard its shadow slid over the pie tent. "
        f"For one breath it seemed to stop, and for the next it tugged as if the whole sky had taken a bite."
    )


def alarm(world: World, helper: Entity, grownup: Entity) -> None:
    world.say(f'"{grownup.label_word.capitalize()}!" {helper.id} shouted. "Come quick!"')


def rescue(world: World, grownup: Entity, response: Response, shape: Shape) -> None:
    balloon = world.get("balloon")
    balloon.meters["lift"] = 0.0
    balloon.meters["strain"] = 0.0
    world.get("yard").meters["danger"] = 0.0
    world.say(
        f"{grownup.label_word.capitalize()} came over in three giant steps and {response.text}."
    )
    world.say(
        f"Down came the {shape.label}, big to mid, mid to small, until it bobbed at shoulder height instead of trying to boss the clouds."
    )


def lesson(world: World, grownup: Entity, hero: Entity, helper: Entity) -> None:
    for kid in (hero, helper):
        kid.memes["lesson"] += 1.0
        kid.memes["relief"] += 1.0
        kid.memes["fear"] = 0.0
    world.say(
        f'{grownup.label_word.capitalize()} knelt by the spool and hugged them close. '
        f'"When a balloon is too wild, you do not stab first and think later," {grownup.pronoun()} said. '
        f'"You shrink it slowly and keep your feet on the ground."'
    )
    world.say(
        f'"Slow and low beats rush and go," {helper.id} whispered, and {hero.id} nodded.'
    )


def parade_end(world: World, hero: Entity, helper: Entity, shape: Shape) -> None:
    hero.memes["joy"] += 1.0
    helper.memes["joy"] += 1.0
    world.say(
        f"A little later they led the tamed {shape.label} down the parade lane. "
        f"It still looked grand enough to make old farmers squint, but now it floated where children could wave at it instead of chasing it over three counties."
    )
    world.say(
        f'"Bright, not fright; tight, all right," sang {hero.id} and {helper.id}, and this time the rhyme fit the day.'
    )


def rescue_fail(world: World, grownup: Entity, response: Response, shape: Shape) -> None:
    balloon = world.get("balloon")
    balloon.meters["escaped"] += 1.0
    world.get("yard").meters["danger"] = 1.0
    world.say(
        f"{grownup.label_word.capitalize()} ran up and {response.fail}."
    )
    world.say(
        f"The {shape.label} gave one wild snap, then tore free and went sailing above the grandstand like a runaway moon."
    )


def loss_end(world: World, hero: Entity, helper: Entity, shape: Shape) -> None:
    hero.memes["sadness"] += 1.0
    helper.memes["sadness"] += 1.0
    hero.memes["lesson"] += 1.0
    helper.memes["lesson"] += 1.0
    world.say(
        f"Everyone on the midway stood with hats in their hands and eyes in the sky until the {shape.label} dwindled to a dot and then to nothing at all."
    )
    world.say(
        f'{hero.id} swallowed hard. {helper.id} touched {hero.pronoun("possessive")} sleeve, and together they promised that next time they would shrink trouble early instead of daring it to grow.'
    )
    world.say(
        "The parade went on, but whenever the wind hummed in a rope that day, both children listened."
    )


def tell(
    shape: Shape,
    weather: Weather,
    tether: Tether,
    response: Response,
    hero_name: str = "Boone",
    hero_gender: str = "boy",
    helper_name: str = "June",
    helper_gender: str = "girl",
    grownup_type: str = "uncle",
    trait: str = "careful",
    delay: int = 0,
    hero_age: int = 7,
    helper_age: int = 5,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            age=hero_age,
            attrs={"relation": relation},
            traits=["boastful"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            age=helper_age,
            attrs={"relation": relation, "trust": trust},
            traits=[trait],
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grown-up",
        )
    )
    yard = world.add(Entity(id="yard", type="fairground", label="the fairground"))
    balloon = world.add(Entity(id="balloon", type="balloon", label=shape.label))
    line = world.add(Entity(id="line", type="tether", label=tether.label))

    hero.memes["bravado"] = BRAVADO_INIT
    helper.memes["care"] = initial_care(trait)
    helper.memes["trust"] = float(trust)
    balloon.meters["lift"] = float(shape.lift)
    line.meters["grip"] = float(tether.grip)
    yard.meters["danger"] = 0.0
    world.facts["weather_strength"] = weather.strength
    world.facts["tether_grip"] = tether.grip
    world.facts["shape_lift"] = shape.lift
    world.facts["delay"] = delay

    introduce(world, hero, shape, tether)
    weather_turn(world, weather)
    need_to_shrink(world, hero, helper)

    world.para()
    tempt(world, hero)
    warn(world, helper, hero, grownup)

    averted = would_avert(relation, hero_age, helper_age, trait)
    if averted:
        back_down(world, hero, helper)
        world.para()
        rescue(world, grownup, RESPONSES["reel_and_valve"], shape)
        lesson(world, grownup, hero, helper)
        world.para()
        parade_end(world, hero, helper, shape)
        contained = True
        story_severity = 0
    else:
        reach_anyway(world, hero, helper)
        world.para()
        strain(world, balloon, shape)
        alarm(world, helper, grownup)
        story_severity = severity(shape, weather, tether, delay)
        contained = is_contained(shape, weather, tether, response, delay)
        balloon.meters["severity"] = float(story_severity)
        world.para()
        if contained:
            rescue(world, grownup, response, shape)
            lesson(world, grownup, hero, helper)
            world.para()
            parade_end(world, hero, helper, shape)
        else:
            rescue_fail(world, grownup, response, shape)
            loss_end(world, hero, helper, shape)

    outcome = "averted" if averted else ("contained" if contained else "lost")
    world.facts.update(
        shape=shape,
        weather=weather,
        tether=tether,
        response=response,
        hero=hero,
        helper=helper,
        grownup=grownup,
        balloon=balloon,
        line=line,
        risk=risk_index(shape, weather, tether),
        outcome=outcome,
        severity=story_severity,
        relation=relation,
        promised=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "balloon": [
        (
            "Why should a big balloon be let down slowly?",
            "Letting air out slowly keeps a big balloon calm and controlled. If you pop it or rush it, it can jump, whip, and scare people nearby.",
        )
    ],
    "wind": [
        (
            "Why can wind make a balloon hard to hold?",
            "Wind pushes on the wide side of a balloon like a hand shoving a sail. The bigger the balloon is, the more the wind can tug it around.",
        )
    ],
    "gust": [
        (
            "What is a gust?",
            "A gust is a quick, strong burst of wind. It can pull at kites, hats, and balloons all at once.",
        )
    ],
    "storm": [
        (
            "Why is a squall tricky?",
            "A squall is a sudden rough spell of wind or weather. Because it comes fast, people have less time to steady things and make a careful plan.",
        )
    ],
    "tether": [
        (
            "What does a tether do?",
            "A tether is a line that keeps something tied down so it does not drift away. A stronger tether can hold more pulling force.",
        )
    ],
    "valve": [
        (
            "What does a valve do on a balloon?",
            "A valve is the part you open to let air out in a controlled way. That helps the balloon shrink safely instead of bursting.",
        )
    ],
    "safe": [
        (
            "Why is slow sometimes safer than quick?",
            "Slow gives you time to stay steady and notice what is happening. Quick can be useful, but when something is jumpy or windy, rushing can make the problem worse.",
        )
    ],
    "pin": [
        (
            "Why is poking a balloon with a pin risky?",
            "A pin can make a balloon burst or jerk suddenly. That sudden movement can scare people and make the balloon harder to control.",
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is a cheerful line of people, music, and big decorations moving along a road or lane. Everyone watches as the bright things pass by.",
        )
    ],
}
KNOWLEDGE_ORDER = ["balloon", "wind", "gust", "storm", "tether", "valve", "safe", "pin", "parade"]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    shape, weather = f["shape"], f["weather"]
    outcome = f["outcome"]
    base = (
        f'Write a tall-tale style story for a 3-to-5-year-old that includes the word "shrink", '
        f"has a little rhyme, and centers on a giant {shape.label} at a county fair."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a suspenseful but gentle story where {hero.id} wants a quick fix for a wind-tugged balloon, "
            f"but {helper.id} talks {hero.pronoun('object')} into shrinking it slowly instead.",
            f'Write a rhyming tall tale where a careful older sibling stops a younger one from doing something rash, '
            f'and the giant balloon is saved before the {weather.id} wind can carry it off.',
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a story where the wind grows rough, the children get scared, and a grown-up helps the giant balloon shrink safely.",
            f"Write a child-facing tall tale with suspense, rhyme, and a happy ending in which {hero.id} learns that slow, careful help beats a quick risky trick.",
        ]
    return [
        base,
        f"Tell a cautionary tall tale where the wind becomes too strong, the balloon gets away, and the children learn they should have made it shrink sooner.",
        f"Write a suspenseful story with rhyme where a giant fair balloon escapes into the sky, but everyone stays safe and learns from it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, grownup = f["hero"], f["helper"], f["grownup"]
    shape, weather, tether, response = f["shape"], f["weather"], f["tether"], f["response"]
    relation = f["relation"]
    pair = pair_noun(hero, helper, relation)
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}, and their {grownup.label_word} at the county fair. They were trying to manage a giant {shape.label}.",
        ),
        (
            f"What made the story feel suspenseful?",
            f"The wind kept pulling harder on the giant balloon, and the tether was straining. That made everyone worry the balloon might break free and race into the sky.",
        ),
        (
            f"Why did they need the balloon to shrink?",
            f"They needed it to shrink because the wind was tugging it too hard to handle safely. A smaller balloon would be easier to control on the ground.",
        ),
        (
            f"Why did {helper.id} warn against using a pin?",
            f"{helper.id} knew a pin would not make the balloon shrink gently. It could make the balloon jump or burst all at once, which would be harder to control in the wind.",
        ),
    ]
    if f["outcome"] == "averted":
        out.append(
            (
                f"What changed after {helper.id} spoke up?",
                f"{hero.id} listened and gave up the risky quick fix before the trouble got worse. Because they chose a slow, careful plan early, the balloon stayed under control.",
            )
        )
        out.append(
            (
                "How did the story end?",
                f"It ended with the balloon tamed and ready for the parade. The children even sang a rhyme because the scary part had passed.",
            )
        )
    elif f["outcome"] == "contained":
        out.append(
            (
                f"How did the {grownup.label_word} solve the problem?",
                f"{grownup.label_word.capitalize()} {response.qa_text}. That worked because the careful method beat the wind before the balloon could tear loose.",
            )
        )
        out.append(
            (
                f"What did {hero.id} learn?",
                f"{hero.id} learned not to rush at a jumpy problem just because a quick trick looks easy. In the wind, slow and steady was the safer way to shrink the balloon.",
            )
        )
        out.append(
            (
                "How did the ending prove things had changed?",
                f"At the end, the balloon floated calmly in the parade instead of fighting the sky. That showed the danger was over and the children were wiser than before.",
            )
        )
    else:
        out.append(
            (
                "Did the grown-up save the balloon?",
                f"No. The grown-up tried, but the wind and delay had already made the balloon too wild to hold. It tore free and drifted away above the fairground.",
            )
        )
        out.append(
            (
                "What did the children learn from the ending?",
                f"They learned that waiting too long can turn a risky moment into a loss. They also learned that shrinking trouble early is better than daring it to grow.",
            )
        )
        out.append(
            (
                "Was everyone safe?",
                "Yes, everyone stayed safe even though the balloon was lost. The sad ending still mattered because it taught the children to act carefully sooner next time.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["shape"].tags) | set(world.facts["weather"].tags) | set(world.facts["tether"].tags)
    outcome = world.facts["outcome"]
    if outcome == "lost":
        tags |= set(world.facts["response"].tags)
    else:
        tags |= {"valve", "safe"}
        if world.facts["response"].id == "pin_prick":
            tags.add("pin")
        else:
            tags |= set(world.facts["response"].tags)
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
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if e.age:
            parts.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(shape: Shape, weather: Weather, tether: Tether) -> str:
    return (
        f"(No story: a {shape.label} tied with {tether.phrase} in {weather.id} weather does not create enough pull for real suspense. "
        f"This world needs a true tug-of-war with the wind so there is something urgent to shrink.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). A pin is a rash shortcut here. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.helper_age, params.trait):
        return "averted"
    shape = SHAPES[params.shape]
    weather = WEATHER[params.weather]
    tether = TETHERS[params.tether]
    response = RESPONSES[params.response]
    return "contained" if is_contained(shape, weather, tether, response, params.delay) else "lost"


ASP_RULES = r"""
% --- gate ---------------------------------------------------------------
risk(S,W,T,R) :- shape_lift(S,SL), weather_strength(W,WS), tether_grip(T,TG), R = WS + SL - TG.
hazard(S,W,T) :- risk(S,W,T,R), R >= 1.
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,W,T) :- shape(S), weather(W), tether(T), hazard(S,W,T).

% --- averted / contained / lost ----------------------------------------
care_now(T,5) :- trait(T), careful_trait(T).
care_now(T,3) :- trait(T), not careful_trait(T).
helper_older :- relation(siblings), hero_age(HA), helper_age(AA), AA > HA.
authority(C + 1 + B) :- care_now(T,C), trait(T), bonus(B).
bonus(3) :- helper_older.
bonus(0) :- not helper_older.
averted :- helper_older, authority(A), bravado_init(B), A > B.

scenario_severity(R + D) :- chosen_shape(S), chosen_weather(W), chosen_tether(T), risk(S,W,T,R), delay(D).
resp_power(P) :- chosen_response(R), power(R,P).
contained :- resp_power(P), scenario_severity(SV), P >= SV.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(lost) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, shape in SHAPES.items():
        lines.append(asp.fact("shape", sid))
        lines.append(asp.fact("shape_lift", sid, shape.lift))
    for wid, weather in WEATHER.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("weather_strength", wid, weather.strength))
    for tid, tether in TETHERS.items():
        lines.append(asp.fact("tether", tid))
        lines.append(asp.fact("tether_grip", tid, tether.grip))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravado_init", int(BRAVADO_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_shape", params.shape),
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_tether", params.tether),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        shape="rooster",
        weather="gusty",
        tether="rope",
        response="reel_and_valve",
        hero="Boone",
        hero_gender="boy",
        helper="June",
        helper_gender="girl",
        grownup="uncle",
        trait="careful",
        delay=0,
        hero_age=7,
        helper_age=5,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        shape="catfish",
        weather="squall",
        tether="twine",
        response="hang_on",
        hero="Mabel",
        hero_gender="girl",
        helper="Otis",
        helper_gender="boy",
        grownup="aunt",
        trait="steady",
        delay=1,
        hero_age=7,
        helper_age=6,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        shape="dragon",
        weather="gusty",
        tether="twine",
        response="tail_hold_valve",
        hero="Eli",
        hero_gender="boy",
        helper="Clara",
        helper_gender="girl",
        grownup="uncle",
        trait="patient",
        delay=0,
        hero_age=5,
        helper_age=8,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        shape="dragon",
        weather="squall",
        tether="rope",
        response="tail_hold_valve",
        hero="Sadie",
        hero_gender="girl",
        helper="Beau",
        helper_gender="boy",
        grownup="father",
        trait="curious",
        delay=2,
        hero_age=7,
        helper_age=7,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        shape="catfish",
        weather="gusty",
        tether="twine",
        response="reel_and_valve",
        hero="Toby",
        hero_gender="boy",
        helper="Nell",
        helper_gender="girl",
        grownup="mother",
        trait="sensible",
        delay=0,
        hero_age=6,
        helper_age=6,
        relation="siblings",
        trust=7,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a giant fair balloon, a risky quick fix, and the safest way to make it shrink."
    )
    ap.add_argument("--shape", choices=SHAPES)
    ap.add_argument("--weather", choices=WEATHER)
    ap.add_argument("--tether", choices=TETHERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--grownup", choices=["mother", "father", "uncle", "aunt"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time before help fully takes hold")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shape and args.weather and args.tether:
        shape = SHAPES[args.shape]
        weather = WEATHER[args.weather]
        tether = TETHERS[args.tether]
        if not suspense_at_risk(shape, weather, tether):
            raise StoryError(explain_rejection(shape, weather, tether))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.shape is None or combo[0] == args.shape)
        and (args.weather is None or combo[1] == args.weather)
        and (args.tether is None or combo[2] == args.tether)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shape_id, weather_id, tether_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero, hero_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=hero)
    grownup = args.grownup or rng.choice(["mother", "father", "uncle", "aunt"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, helper_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        shape=shape_id,
        weather=weather_id,
        tether=tether_id,
        response=response_id,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        grownup=grownup,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        helper_age=helper_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        shape = SHAPES[params.shape]
        weather = WEATHER[params.weather]
        tether = TETHERS[params.tether]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]}.)") from None

    if not suspense_at_risk(shape, weather, tether):
        raise StoryError(explain_rejection(shape, weather, tether))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        shape=shape,
        weather=weather,
        tether=tether,
        response=response,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        grownup_type=params.grownup,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        relation=params.relation,
        trust=params.trust,
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(200):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
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
            raise StoryError("(Smoke test failed: generated story was empty.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test passed for generate()/emit().")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (shape, weather, tether) combos:\n")
        for shape, weather, tether in combos:
            print(f"  {shape:8} {weather:7} {tether}")
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
            header = (
                f"### {p.hero} & {p.helper}: {p.shape} in {p.weather} weather "
                f"with {p.tether} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
