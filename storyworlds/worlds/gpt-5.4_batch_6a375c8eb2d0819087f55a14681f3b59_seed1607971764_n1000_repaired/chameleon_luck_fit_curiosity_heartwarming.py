#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chameleon_luck_fit_curiosity_heartwarming.py
=======================================================================

A standalone story world about a curious child who notices a tiny chameleon in
need of a cozy hiding place. The child tries to help, but only a shelter that
really fits the chameleon and can handle the weather makes a good story.

The seed called for the words "chameleon", "luck", and "fit", with Curiosity
and a heartwarming tone. This world treats curiosity as the engine of the
middle: the child keeps looking, asks why the chameleon is uncomfortable, and
learns to match a small creature with a shelter that truly fits.

Reasonableness constraint
-------------------------
Not every pretty object makes a good shelter for a tiny animal. This world
checks two things:

1. Fit: the shelter must be big enough for the chameleon, but not wildly too
   large to feel exposed.
2. Safety: in breezy weather, only stable shelters work. Delicate blossoms and
   loose caps are refused in windy stories.

That means the world will reject combinations that have no honest problem-fix
arc. The story prose is driven by world state: failed ideas increase worry,
curiosity pushes the search forward, and the ending image changes depending on
what safe shelter was found.

Run it
------
    python storyworlds/worlds/gpt-5.4/chameleon_luck_fit_curiosity_heartwarming.py
    python storyworlds/worlds/gpt-5.4/chameleon_luck_fit_curiosity_heartwarming.py --weather breezy --shelter tulip
    python storyworlds/worlds/gpt-5.4/chameleon_luck_fit_curiosity_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/chameleon_luck_fit_curiosity_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/chameleon_luck_fit_curiosity_heartwarming.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    size: int = 0
    stable: bool = False
    soft: bool = False
    open_top: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class Setting:
    id: str
    place: str
    color_line: str
    sounds: str
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
    adjective: str
    problem: str
    sky_line: str
    wind: int
    damp: int
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
class Shelter:
    id: str
    label: str
    phrase: str
    found_at: str
    size: int
    stable: bool
    soft: bool
    open_top: bool
    cozy_line: str
    ending_line: str
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
class Finder:
    id: str
    style: str
    question: str
    wonder: str
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
    def __init__(self, setting: Setting, weather: Weather) -> None:
        self.setting = setting
        self.weather = weather
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
        clone = World(self.setting, self.weather)
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


def _r_breeze_unstable(world: World) -> list[str]:
    out: list[str] = []
    weather = world.weather
    cham = world.get("chameleon")
    shelter = world.entities.get("shelter")
    if shelter is None:
        return out
    if weather.wind < 1 or shelter.stable:
        return out
    sig = ("breeze_unstable", shelter.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shelter.meters["wobble"] += 1
    cham.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_tight_cramped(world: World) -> list[str]:
    out: list[str] = []
    cham = world.get("chameleon")
    shelter = world.entities.get("shelter")
    if shelter is None:
        return out
    if shelter.size >= cham.size:
        return out
    sig = ("tight", shelter.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cham.meters["cramped"] += 1
    cham.memes["worry"] += 1
    out.append("__tight__")
    return out


def _r_roomy_exposed(world: World) -> list[str]:
    out: list[str] = []
    cham = world.get("chameleon")
    shelter = world.entities.get("shelter")
    if shelter is None:
        return out
    if shelter.size <= cham.size + 2:
        return out
    sig = ("roomy", shelter.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cham.meters["exposed"] += 1
    cham.memes["worry"] += 1
    out.append("__roomy__")
    return out


def _r_soft_rest(world: World) -> list[str]:
    out: list[str] = []
    cham = world.get("chameleon")
    shelter = world.entities.get("shelter")
    if shelter is None or not shelter.soft:
        return out
    sig = ("soft", shelter.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cham.meters["rest"] += 1
    cham.memes["calm"] += 1
    out.append("__soft__")
    return out


CAUSAL_RULES = [
    Rule(name="breeze_unstable", tag="physical", apply=_r_breeze_unstable),
    Rule(name="tight_cramped", tag="physical", apply=_r_tight_cramped),
    Rule(name="roomy_exposed", tag="physical", apply=_r_roomy_exposed),
    Rule(name="soft_rest", tag="physical", apply=_r_soft_rest),
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


def fits(chameleon_size: int, shelter: Shelter) -> bool:
    return shelter.size >= chameleon_size and shelter.size <= chameleon_size + 2


def weather_safe(weather: Weather, shelter: Shelter) -> bool:
    return weather.wind == 0 or shelter.stable


def is_cozy(chameleon_size: int, weather: Weather, shelter: Shelter) -> bool:
    return fits(chameleon_size, shelter) and weather_safe(weather, shelter)


def explain_rejection(weather: Weather, shelter: Shelter) -> str:
    reasons: list[str] = []
    if shelter.size < CHAMELEON_SIZE:
        reasons.append(
            f"{shelter.phrase.capitalize()} is too small, so the chameleon would not fit"
        )
    elif shelter.size > CHAMELEON_SIZE + 2:
        reasons.append(
            f"{shelter.phrase.capitalize()} is far too roomy for a tiny chameleon and would feel exposed"
        )
    if weather.wind > 0 and not shelter.stable:
        reasons.append(
            f"on a {weather.adjective} day it would wobble and not feel safe"
        )
    if not reasons:
        return "(No story: this combination does not make a clear shelter problem.)"
    return "(No story: " + "; ".join(reasons) + ".)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for weather_id, weather in WEATHERS.items():
            for shelter_id, shelter in SHELTERS.items():
                if is_cozy(CHAMELEON_SIZE, weather, shelter):
                    combos.append((setting_id, weather_id, shelter_id))
    return combos


def predict_shelter(world: World, shelter: Shelter) -> dict:
    sim = world.copy()
    sim.entities["shelter"] = Entity(
        id="shelter",
        type="shelter",
        label=shelter.label,
        size=shelter.size,
        stable=shelter.stable,
        soft=shelter.soft,
        open_top=shelter.open_top,
    )
    propagate(sim, narrate=False)
    cham = sim.get("chameleon")
    return {
        "cramped": cham.meters["cramped"] >= THRESHOLD,
        "exposed": cham.meters["exposed"] >= THRESHOLD,
        "wobble": sim.get("shelter").meters["wobble"] >= THRESHOLD,
        "calm": cham.memes["calm"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, finder: Finder) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"One gentle afternoon in {world.setting.place}, {child.id} wandered slowly, "
        f"{finder.style}. {world.setting.color_line}"
    )
    world.say(world.weather.sky_line)
    world.say(
        f"{world.setting.sounds} {child.id} was the sort of child who always paused to ask, "
        f'"{finder.question}"'
    )


def spot_chameleon(world: World, child: Entity) -> None:
    cham = world.get("chameleon")
    cham.memes["worry"] += 1
    world.say(
        f"Under a curling leaf, {child.id} noticed a tiny chameleon no bigger than "
        f"a thumb. Its little sides puffed in and out, and it kept changing from leaf-green "
        f"to worried brown."
    )


def wonder(world: World, child: Entity, finder: Finder) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} knelt down very carefully. {finder.wonder} The chameleon blinked, "
        f"looked toward the path, and then toward the nearest hiding places as if it were "
        f"searching for somewhere to rest."
    )


def first_try(world: World, child: Entity, shelter: Shelter) -> None:
    world.facts["attempted"] = shelter.id
    world.say(
        f"With soft hands, {child.id} found {shelter.phrase} {shelter.found_at} and set it nearby. "
        f"It seemed like a lucky idea at first."
    )


def explain_misfit(world: World, child: Entity, shelter: Shelter, pred: dict) -> None:
    child.memes["curiosity"] += 1
    cham = world.get("chameleon")
    cham.memes["trust"] += 1
    if pred["cramped"]:
        world.say(
            f"But when the chameleon peeked in, {child.id} could see at once that it would not fit. "
            f"The little creature curled its tail tight and backed away."
        )
    elif pred["exposed"]:
        world.say(
            f"But the shelter was much too big. The chameleon stepped inside, then froze in the middle "
            f"as if the wide space made it feel seen instead of safe."
        )
    elif pred["wobble"]:
        world.say(
            f"But the breeze nudged the shelter from side to side. The chameleon clung to the rim, and "
            f"{child.id} understood that a pretty place is not always a safe one."
        )
    else:
        world.say(
            f"{child.id} studied the little scene and kept wondering whether there might be an even better fit."
        )


def ask_helper(world: World, child: Entity, helper: Entity) -> None:
    child.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f'"{helper.label_word.capitalize()}, what kind of place would feel best for such a tiny friend?" '
        f'{child.id} asked.'
    )
    world.say(
        f'{helper.label_word.capitalize()} came over and smiled. "A good hiding place should fit the chameleon, '
        f'and on a {world.weather.adjective} day it should stay steady too," {helper.pronoun()} said.'
    )


def find_better(world: World, child: Entity, shelter: Shelter) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"So {child.id} looked again, this time with kinder, sharper eyes, and found {shelter.phrase} "
        f"{shelter.found_at}. {shelter.cozy_line}"
    )


def settle(world: World, child: Entity, shelter: Shelter) -> None:
    world.entities["shelter"] = Entity(
        id="shelter",
        type="shelter",
        label=shelter.label,
        size=shelter.size,
        stable=shelter.stable,
        soft=shelter.soft,
        open_top=shelter.open_top,
    )
    propagate(world, narrate=False)
    cham = world.get("chameleon")
    cham.memes["worry"] = 0.0
    cham.memes["calm"] += 1
    cham.memes["trust"] += 1
    cham.meters["sheltered"] += 1
    world.say(
        f"The chameleon stepped in, turned one bright eye toward {child.id}, and slowly relaxed. "
        f"Its color softened back to green."
    )
    if shelter.soft:
        world.say(
            "Its tiny feet stopped clutching so hard, and its curled tail loosened like a ribbon."
        )


def closing(world: World, child: Entity, helper: Entity, shelter: Shelter) -> None:
    child.memes["joy"] += 1
    child.memes["care"] += 1
    world.say(
        f'"Maybe it was luck that we found it," {child.id} whispered, "but we still had to look closely '
        f'to find the right fit."'
    )
    world.say(
        f'{helper.label_word.capitalize()} squeezed {child.pronoun("possessive")} shoulder. '
        f'"That is what curiosity is for," {helper.pronoun()} said.'
    )
    world.say(
        shelter.ending_line
    )


def tell(
    setting: Setting,
    weather: Weather,
    failed_shelter: Shelter,
    final_shelter: Shelter,
    finder: Finder,
    child_name: str = "Mira",
    child_type: str = "girl",
    helper_type: str = "grandmother",
) -> World:
    world = World(setting, weather)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=["gentle", "curious"],
        attrs={"finder_style": finder.style},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={"relation": helper_type},
    ))
    chameleon = world.add(Entity(
        id="chameleon",
        kind="character",
        type="animal",
        role="chameleon",
        label="chameleon",
        size=CHAMELEON_SIZE,
        attrs={"colors": ["green", "brown"]},
    ))

    world.facts.update(
        child=child,
        helper=helper,
        finder=finder,
        setting=setting,
        weather=weather,
        failed_shelter=failed_shelter,
        final_shelter=final_shelter,
        problem_kind="",
        attempted=failed_shelter.id,
    )

    introduce(world, child, finder)
    spot_chameleon(world, child)
    wonder(world, child, finder)

    world.para()
    first_try(world, child, failed_shelter)
    failed_pred = predict_shelter(world, failed_shelter)
    world.facts["failed_prediction"] = failed_pred
    if failed_pred["cramped"]:
        world.facts["problem_kind"] = "too_small"
    elif failed_pred["exposed"]:
        world.facts["problem_kind"] = "too_big"
    elif failed_pred["wobble"]:
        world.facts["problem_kind"] = "unstable"
    else:
        world.facts["problem_kind"] = "unclear"
    explain_misfit(world, child, failed_shelter, failed_pred)
    ask_helper(world, child, helper)

    world.para()
    find_better(world, child, final_shelter)
    settle(world, child, final_shelter)
    closing(world, child, helper, final_shelter)

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden behind the house",
        color_line="Marigolds bobbed like little suns beside the path.",
        sounds="A fountain made small silver sounds by the wall.",
        tags={"garden"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the warm greenhouse",
        color_line="Glass panes held the afternoon light in clear, golden squares.",
        sounds="Water drops ticked softly from one leaf to another.",
        tags={"greenhouse"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the courtyard with its clay pots",
        color_line="Round pots lined the stones, and vines leaned over the fence.",
        sounds="Doves cooed from the roof beams above.",
        tags={"courtyard"},
    ),
}

WEATHERS = {
    "still": Weather(
        id="still",
        adjective="still",
        problem="the little creature needed somewhere hidden and snug before evening",
        sky_line="The air was still and warm, with no hurry in it at all.",
        wind=0,
        damp=0,
        tags={"weather"},
    ),
    "breezy": Weather(
        id="breezy",
        adjective="breezy",
        problem="the breeze kept stirring the leaves and making every flimsy nook wobble",
        sky_line="A light breeze kept slipping through the leaves and touching every petal.",
        wind=1,
        damp=0,
        tags={"weather", "wind"},
    ),
}

SHELTERS = {
    "acorn_cap": Shelter(
        id="acorn_cap",
        label="acorn cap",
        phrase="an upside-down acorn cap",
        found_at="by the roots of the rosemary bush",
        size=1,
        stable=False,
        soft=False,
        open_top=True,
        cozy_line="It was neat and small, but it sat too lightly on the ground.",
        ending_line="Soon the tiny chameleon was resting snugly, and the whole garden seemed to breathe more softly around it.",
        tags={"acorn"},
    ),
    "tulip": Shelter(
        id="tulip",
        label="tulip bloom",
        phrase="a fallen tulip bloom",
        found_at="under the bench",
        size=3,
        stable=False,
        soft=True,
        open_top=True,
        cozy_line="The petals made a soft cup, bright as a tiny lantern.",
        ending_line="The petals held the little guest like a cradle, and even the flowers nearby looked pleased.",
        tags={"flower"},
    ),
    "teacup": Shelter(
        id="teacup",
        label="teacup",
        phrase="a chipped teacup",
        found_at="beside the potting table",
        size=5,
        stable=True,
        soft=False,
        open_top=True,
        cozy_line="It was steady and safe, but the hollow inside felt wide as a room.",
        ending_line="The teacup sat quietly by the path, and the tiny chameleon looked as peaceful as if it had always belonged there.",
        tags={"cup"},
    ),
    "mitten": Shelter(
        id="mitten",
        label="mitten pocket",
        phrase="a soft mitten with one thumb tucked in",
        found_at="on a low garden hook",
        size=4,
        stable=True,
        soft=True,
        open_top=True,
        cozy_line="The wool made a soft little cave, and the folded thumb kept the opening snug.",
        ending_line="When evening light turned honey-gold, the mitten made the perfect little home, and the chameleon blinked at them as if to say thank you.",
        tags={"mitten"},
    ),
}

FINDERS = {
    "pebbles": Finder(
        id="pebbles",
        style="collecting smooth pebbles in a pocket",
        question="Why does this look the way it does?",
        wonder="Curiosity tugged at her heart harder than hurry ever could.",
        tags={"curiosity"},
    ),
    "petals": Finder(
        id="petals",
        style="lining up fallen petals by color on the bench",
        question="What happened here before I arrived?",
        wonder="That question always opened the day wider for him.",
        tags={"curiosity"},
    ),
    "snails": Finder(
        id="snails",
        style="watching where the snails chose to go after watering time",
        question="How does a tiny creature decide what is safe?",
        wonder="The thought made her lean closer instead of walking on.",
        tags={"curiosity"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Nora", "Ava", "Ruby", "Tessa", "Lucy", "Maya"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Theo", "Ben", "Sam", "Leo", "Finn"]
HELPERS = ["grandmother", "grandfather", "mother", "father"]
CHAMELEON_SIZE = 3


@dataclass
class StoryParams:
    setting: str
    weather: str
    shelter: str
    finder: str
    child_name: str
    child_type: str
    helper_type: str
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
    "chameleon": [
        (
            "What is a chameleon?",
            "A chameleon is a kind of lizard. Many chameleons can change color, and they use their feet and tails to hold on as they climb."
        )
    ],
    "curiosity": [
        (
            "What does curiosity mean?",
            "Curiosity means wanting to know more. It makes you look closely, ask questions, and learn things you might have missed."
        )
    ],
    "fit": [
        (
            "What does it mean when something is a good fit?",
            "A good fit means something is the right size or shape for what it needs to do. If a shelter fits, it feels safe instead of too tight or too wide."
        )
    ],
    "luck": [
        (
            "What is luck?",
            "Luck is when something good happens by chance. But people still need to notice the chance and make a kind choice."
        )
    ],
    "wind": [
        (
            "Why can wind bother a tiny animal?",
            "Wind can shake leaves and light things around. For a tiny animal, that can make a resting place feel wobbly and unsafe."
        )
    ],
    "mitten": [
        (
            "Why is a mitten soft and warm?",
            "A mitten is usually made from cloth or wool, so it feels soft and helps hold warmth. That can make a small space feel cozy."
        )
    ],
    "flower": [
        (
            "Why can a flower feel soft but not sturdy?",
            "Petals are soft and gentle, but they bend and flap easily. Something can feel nice and still not be steady enough."
        )
    ],
    "cup": [
        (
            "Why can a cup be safe but not cozy for a tiny creature?",
            "A cup has firm sides, so it can stay still. But if the space inside is much too big, a tiny creature may not feel tucked in and protected."
        )
    ],
}
KNOWLEDGE_ORDER = ["chameleon", "curiosity", "fit", "luck", "wind", "mitten", "flower", "cup"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    weather = f["weather"]
    final_shelter = f["final_shelter"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "chameleon", "luck", and "fit".',
        f"Tell a gentle story where a curious child named {child.id} notices a tiny chameleon on a {weather.adjective} day and keeps looking until a shelter is the right fit.",
        f"Write a cozy story in which curiosity leads to kindness, and a small creature ends up resting in {final_shelter.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    weather = f["weather"]
    failed = f["failed_shelter"]
    final_shelter = f["final_shelter"]
    problem_kind = f["problem_kind"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child, and a tiny chameleon in {world.setting.place}. The story also includes {helper.label_word}, who helps {child.id} think about what would feel safe."
        ),
        (
            "Why did the child stop in the first place?",
            f"{child.id} stopped because curiosity made {child.pronoun('object')} look closely instead of hurrying past. That is how {child.pronoun()} noticed the tiny chameleon hiding under the leaf."
        ),
        (
            "Why was the chameleon having trouble?",
            f"The chameleon needed somewhere safe to rest, and the day was {weather.adjective}. {weather.problem[0].upper() + weather.problem[1:]}, so not every hiding place would work."
        ),
    ]
    if problem_kind == "too_small":
        qa.append(
            (
                f"Why did {failed.phrase} not work?",
                f"It did not work because it was too small, so the chameleon could not fit inside it comfortably. {child.id} saw the little animal back away, which showed that a kind idea still has to match the creature's real size."
            )
        )
    elif problem_kind == "too_big":
        qa.append(
            (
                f"Why did {failed.phrase} not work?",
                f"It was steady enough, but it was far too roomy for such a tiny chameleon. The wide space did not feel snug, so it felt exposed instead of tucked in."
            )
        )
    elif problem_kind == "unstable":
        qa.append(
            (
                f"Why did {failed.phrase} not work?",
                f"It looked soft and pretty, but the breeze made it wobble. {child.id} learned that a shelter must be safe as well as lovely."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They kept looking until they found {final_shelter.phrase}, which was a better fit for the chameleon. It matched the little animal's size and felt safe enough for the weather, so the chameleon could finally relax."
        )
    )
    qa.append(
        (
            "What did the child mean by talking about luck at the end?",
            f"{child.id} meant that it was lucky to notice the chameleon at all. But the happy ending came from using curiosity and care to keep searching for the right fit."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"chameleon", "curiosity", "fit", "luck"}
    if world.weather.wind > 0:
        tags.add("wind")
    final_shelter = world.facts["final_shelter"]
    if final_shelter.id == "mitten":
        tags.add("mitten")
    if final_shelter.id == "tulip":
        tags.add("flower")
    if final_shelter.id == "teacup":
        tags.add("cup")
    failed_shelter = world.facts["failed_shelter"]
    if failed_shelter.id == "tulip":
        tags.add("flower")
    if failed_shelter.id == "teacup":
        tags.add("cup")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.size:
            bits.append(f"size={ent.size}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.stable:
            bits.append("stable=True")
        if ent.soft:
            bits.append("soft=True")
        if ent.open_top:
            bits.append("open_top=True")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        weather="still",
        shelter="mitten",
        finder="pebbles",
        child_name="Mira",
        child_type="girl",
        helper_type="grandmother",
        seed=101,
    ),
    StoryParams(
        setting="greenhouse",
        weather="still",
        shelter="tulip",
        finder="snails",
        child_name="Owen",
        child_type="boy",
        helper_type="grandfather",
        seed=102,
    ),
    StoryParams(
        setting="courtyard",
        weather="breezy",
        shelter="mitten",
        finder="petals",
        child_name="Lila",
        child_type="girl",
        helper_type="mother",
        seed=103,
    ),
    StoryParams(
        setting="garden",
        weather="still",
        shelter="teacup",
        finder="snails",
        child_name="Theo",
        child_type="boy",
        helper_type="father",
        seed=104,
    ),
]


def fail_candidates(weather: Weather, success_id: str) -> list[str]:
    candidates = []
    for shelter_id, shelter in SHELTERS.items():
        if shelter_id == success_id:
            continue
        if not is_cozy(CHAMELEON_SIZE, weather, shelter):
            candidates.append(shelter_id)
    return candidates


def choose_failed_shelter(weather: Weather, success_id: str, rng: random.Random) -> str:
    candidates = fail_candidates(weather, success_id)
    if not candidates:
        raise StoryError("(No reasonable failed first try exists for this story.)")
    order = {"too_small": [], "unstable": [], "too_big": [], "other": []}
    for shelter_id in sorted(candidates):
        shelter = SHELTERS[shelter_id]
        if shelter.size < CHAMELEON_SIZE:
            order["too_small"].append(shelter_id)
        elif weather.wind > 0 and not shelter.stable:
            order["unstable"].append(shelter_id)
        elif shelter.size > CHAMELEON_SIZE + 2:
            order["too_big"].append(shelter_id)
        else:
            order["other"].append(shelter_id)
    prioritized = order["too_small"] + order["unstable"] + order["too_big"] + order["other"]
    return rng.choice(prioritized)


ASP_RULES = r"""
fits(S)        :- shelter(S), chameleon_size(C), size(S, Z), Z >= C, Z <= C + 2.
weather_safe(S) :- shelter(S), weather(W), wind(W, 0).
weather_safe(S) :- shelter(S), weather(W), wind(W, X), X > 0, stable(S).
valid(Place, W, S) :- setting(Place), weather(W), shelter(S), fits(S), weather_safe(S).

too_small(S) :- shelter(S), chameleon_size(C), size(S, Z), Z < C.
too_big(S)   :- shelter(S), chameleon_size(C), size(S, Z), Z > C + 2.
wobbly(W, S) :- weather(W), wind(W, X), X > 0, shelter(S), not stable(S).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("chameleon_size", CHAMELEON_SIZE))
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("wind", weather_id, weather.wind))
    for shelter_id, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", shelter_id))
        lines.append(asp.fact("size", shelter_id, shelter.size))
        if shelter.stable:
            lines.append(asp.fact("stable", shelter_id))
        if shelter.soft:
            lines.append(asp.fact("soft", shelter_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a curious child helps a tiny chameleon find a shelter that really fits."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--shelter", choices=SHELTERS, help="the final shelter that succeeds")
    ap.add_argument("--finder", choices=FINDERS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (setting, weather, shelter) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.weather and args.shelter:
        weather = WEATHERS[args.weather]
        shelter = SHELTERS[args.shelter]
        if not is_cozy(CHAMELEON_SIZE, weather, shelter):
            raise StoryError(explain_rejection(weather, shelter))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.weather is None or combo[1] == args.weather)
        and (args.shelter is None or combo[2] == args.shelter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, weather_id, shelter_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    finder_id = args.finder or rng.choice(sorted(FINDERS))
    helper_type = args.helper_type or rng.choice(HELPERS)
    return StoryParams(
        setting=setting_id,
        weather=weather_id,
        shelter=shelter_id,
        finder=finder_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")
    if params.shelter not in SHELTERS:
        raise StoryError(f"(Unknown shelter: {params.shelter})")
    if params.finder not in FINDERS:
        raise StoryError(f"(Unknown finder: {params.finder})")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child type: {params.child_type})")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")

    weather = WEATHERS[params.weather]
    final_shelter = SHELTERS[params.shelter]
    if not is_cozy(CHAMELEON_SIZE, weather, final_shelter):
        raise StoryError(explain_rejection(weather, final_shelter))

    rng = random.Random(params.seed if params.seed is not None else 0)
    failed_id = choose_failed_shelter(weather, final_shelter.id, rng)
    world = tell(
        setting=SETTINGS[params.setting],
        weather=weather,
        failed_shelter=SHELTERS[failed_id],
        final_shelter=final_shelter,
        finder=FINDERS[params.finder],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, weather, shelter) combos:\n")
        for setting_id, weather_id, shelter_id in combos:
            print(f"  {setting_id:10} {weather_id:7} {shelter_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.setting}, {p.weather}, final shelter {p.shelter}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
