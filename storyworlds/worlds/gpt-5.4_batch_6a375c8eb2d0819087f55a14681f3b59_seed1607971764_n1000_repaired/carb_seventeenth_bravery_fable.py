#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/carb_seventeenth_bravery_fable.py
============================================================

A standalone storyworld for a tiny fable-like domain: a small animal carries a
humble food gift along a tricky path, reaches the seventeenth marker where fear
and duty meet, and discovers that bravery grows when one stops to help.

The seed words "carb" and "seventeenth" are woven directly into the prose. The
world state, not string substitution, drives the middle turn and the ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/carb_seventeenth_bravery_fable.py
    python storyworlds/worlds/gpt-5.4/carb_seventeenth_bravery_fable.py --path stepping_stones --tool reed_pole
    python storyworlds/worlds/gpt-5.4/carb_seventeenth_bravery_fable.py --path log_bridge --weather drizzly
    python storyworlds/worlds/gpt-5.4/carb_seventeenth_bravery_fable.py --all
    python storyworlds/worlds/gpt-5.4/carb_seventeenth_bravery_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/carb_seventeenth_bravery_fable.py --trace
    python storyworlds/worlds/gpt-5.4/carb_seventeenth_bravery_fable.py --json
    python storyworlds/worlds/gpt-5.4/carb_seventeenth_bravery_fable.py --verify
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose", "ewe"}
        male = {"boy", "father", "mouse", "squirrel", "rabbit", "hedgehog", "mole", "ant", "toad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class HeroSpec:
    id: str
    type: str
    home: str
    gait: str
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
class PathSpec:
    id: str
    label: str
    route: str
    landmark: str
    danger: str
    scenery: str
    ending: str
    risk: int
    allowed_weather: set[str] = field(default_factory=set)
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
class ToolSpec:
    id: str
    label: str
    phrase: str
    use_text: str
    supports: set[str] = field(default_factory=set)
    steady: int = 1
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
class FoodSpec:
    id: str
    label: str
    phrase: str
    crumb_word: str
    carb_line: str
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
class WeatherSpec:
    id: str
    label: str
    sky: str
    path_effect: str
    fear: int
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


def _r_gratitude_hint(world: World) -> list[str]:
    hero = world.get("hero")
    ant = world.get("ant")
    if ant.meters["free"] < THRESHOLD:
        return []
    sig = ("hint",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["balance"] += 1
    hero.memes["bravery"] += 1
    world.facts["hinted"] = True
    return ["__hint__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="gratitude_hint", tag="social", apply=_r_gratitude_hint),
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


HEROES = {
    "mouse": HeroSpec(
        id="mouse",
        type="mouse",
        home="a little burrow near the mill",
        gait="quick brown feet",
        tags={"mouse"},
    ),
    "squirrel": HeroSpec(
        id="squirrel",
        type="squirrel",
        home="a hollow oak above the lane",
        gait="light paws and a balancing tail",
        tags={"squirrel"},
    ),
    "rabbit": HeroSpec(
        id="rabbit",
        type="rabbit",
        home="a warm den under fern roots",
        gait="soft hopping feet",
        tags={"rabbit"},
    ),
}

PATHS = {
    "stepping_stones": PathSpec(
        id="stepping_stones",
        label="stepping stones",
        route="a string of stepping stones over the brook",
        landmark="the seventeenth stone",
        danger="one dark stone wore a coat of moss",
        scenery="The brook made silver sounds under the stones.",
        ending="the far bank where the reeds bowed low",
        risk=2,
        allowed_weather={"calm", "drizzly"},
        tags={"stones", "brook"},
    ),
    "log_bridge": PathSpec(
        id="log_bridge",
        label="log bridge",
        route="a fallen log laid over the ditch",
        landmark="the seventeenth ring of the old log",
        danger="the bark had peeled smooth in the middle",
        scenery="Below the log, the ditch whispered through nettles.",
        ending="the meadow side where clover grew thick",
        risk=3,
        allowed_weather={"calm"},
        tags={"log", "ditch"},
    ),
    "hill_steps": PathSpec(
        id="hill_steps",
        label="hill steps",
        route="a steep stair of roots and stones",
        landmark="the seventeenth step",
        danger="the slope narrowed where the hill bent into the wind",
        scenery="Above the path, thyme and wildflowers trembled on the bank.",
        ending="the high garden under the elder tree",
        risk=2,
        allowed_weather={"calm", "drizzly", "windy"},
        tags={"steps", "hill"},
    ),
}

TOOLS = {
    "reed_pole": ToolSpec(
        id="reed_pole",
        label="reed pole",
        phrase="a smooth reed pole",
        use_text="set the reed pole ahead like a third leg and felt the path answer back",
        supports={"stepping_stones", "hill_steps"},
        steady=1,
        tags={"pole"},
    ),
    "vine_loop": ToolSpec(
        id="vine_loop",
        label="vine loop",
        phrase="a loop of tough vine",
        use_text="held the vine loop tight and kept the shaking path from bossing him",
        supports={"log_bridge", "hill_steps"},
        steady=1,
        tags={"vine"},
    ),
    "twig_staff": ToolSpec(
        id="twig_staff",
        label="twig staff",
        phrase="a forked twig staff",
        use_text="leaned on the twig staff and placed each foot with care",
        supports={"hill_steps", "stepping_stones"},
        steady=1,
        tags={"staff"},
    ),
}

FOODS = {
    "barley_bun": FoodSpec(
        id="barley_bun",
        label="barley bun",
        phrase="a barley bun wrapped in dock leaf",
        crumb_word="bun crumb",
        carb_line='The old mole called it "a plain carb for a long road," and smiled at the grand word.',
        tags={"carb", "bun"},
    ),
    "oat_cake": FoodSpec(
        id="oat_cake",
        label="oat cake",
        phrase="a round oat cake tied with grass",
        crumb_word="cake crumb",
        carb_line='Even a humble oat cake, she said, was a carb, and a good carb could keep a small traveler going.',
        tags={"carb", "oat"},
    ),
    "seed_roll": FoodSpec(
        id="seed_roll",
        label="seed roll",
        phrase="a warm seed roll in a fern napkin",
        crumb_word="seed crumb",
        carb_line='The kitchen smelled sweet, and the aunt said the roll was only a simple carb, but simple things often did honest work.',
        tags={"carb", "roll"},
    ),
}

WEATHERS = {
    "calm": WeatherSpec(
        id="calm",
        label="calm",
        sky="The morning was still, and even the reeds seemed to listen.",
        path_effect="The path looked narrow but not angry.",
        fear=0,
        tags={"calm"},
    ),
    "drizzly": WeatherSpec(
        id="drizzly",
        label="drizzly",
        sky="A fine drizzle stitched the air with tiny silver threads.",
        path_effect="Every board and stone carried a cool, slick shine.",
        fear=1,
        tags={"rain"},
    ),
    "windy": WeatherSpec(
        id="windy",
        label="windy",
        sky="The wind kept hurrying across the hill and fussing with leaves.",
        path_effect="Each narrow place felt smaller when the gusts pushed at a traveler's ears.",
        fear=1,
        tags={"wind"},
    ),
}

TRAITS = {
    "bold": 3.0,
    "steady": 2.0,
    "careful": 1.0,
}

HERO_NAMES = {
    "mouse": ["Pip", "Moss", "Nip", "Tumble"],
    "squirrel": ["Hazel", "Quicktail", "Bramble", "Nim"],
    "rabbit": ["Thimble", "Clover", "Skip", "Burr"],
}

AUNT_TYPES = {
    "mole": "mole",
    "hedgehog": "hedgehog",
}

ANT_NAMES = ["Ash", "Dot", "Pin"]


def tool_fits(path_id: str, tool_id: str) -> bool:
    return tool_id in TOOLS and path_id in TOOLS[tool_id].supports


def weather_allows(path_id: str, weather_id: str) -> bool:
    return weather_id in WEATHERS and weather_id in PATHS[path_id].allowed_weather


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for path_id in PATHS:
        for tool_id in TOOLS:
            if not tool_fits(path_id, tool_id):
                continue
            for weather_id in WEATHERS:
                if weather_allows(path_id, weather_id):
                    combos.append((path_id, tool_id, weather_id))
    return combos


@dataclass
class StoryParams:
    hero: str
    name: str
    aunt_type: str
    ant_name: str
    path: str
    tool: str
    food: str
    weather: str
    trait: str
    seed: Optional[int] = None
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


def predict_crossing(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    ant = sim.get("ant")
    path = sim.facts["path_cfg"]
    weather = sim.facts["weather_cfg"]
    help_first = sim.facts["help_first"]
    if help_first:
        ant.meters["free"] += 1
        hero.memes["compassion"] += 1
        propagate(sim, narrate=False)
    risk = path.risk + weather.fear
    courage = hero.memes["bravery"] + hero.meters["balance"]
    return {"risk": risk, "courage": courage, "crosses_alone": courage >= risk}


def introduce(world: World, hero: Entity, aunt: Entity, food: FoodSpec, weather: WeatherSpec) -> None:
    world.say(
        f"In {hero.attrs['home']}, {hero.id} the little {hero.type} was asked to carry "
        f"{food.phrase} to Aunt {aunt.id} on the far side of the way."
    )
    world.say(food.carb_line)
    world.say(weather.sky)


def assign_task(world: World, hero: Entity, aunt: Entity, food: FoodSpec) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'"Take it while it is warm," said Aunt {aunt.id}. "A kind errand grows cold if it waits."'
    )
    world.say(
        f"{hero.id} tucked the {food.label} close and promised to walk carefully."
    )


def set_out(world: World, hero: Entity, path: PathSpec, tool: ToolSpec, weather: WeatherSpec) -> None:
    hero.meters["balance"] += float(tool.steady)
    world.say(
        f"So off went {hero.id} with {tool.phrase}, following {path.route}. {path.scenery}"
    )
    world.say(weather.path_effect)


def reach_landmark(world: World, hero: Entity, ant: Entity, path: PathSpec) -> None:
    hero.meters["progress"] = 17.0
    hero.memes["fear"] += float(path.risk)
    world.say(
        f"He counted under his breath until he reached {path.landmark}. There {path.danger}."
    )
    world.say(
        f"At that same place, little Ant {ant.id} was pinned by a curled leaf and kicking his legs in vain."
    )


def choose_help(world: World, hero: Entity, tool: ToolSpec, ant: Entity) -> None:
    world.facts["helped"] = True
    hero.memes["compassion"] += 1
    world.say(
        f"{hero.id} could have hurried on, yet the sight of a smaller creature in trouble tugged harder than fear."
    )
    world.say(
        f"He used the {tool.label} to lift the leaf edge, and Ant {ant.id} wriggled free at last."
    )
    ant.meters["free"] += 1
    ant.memes["gratitude"] += 1
    propagate(world, narrate=False)
    if world.facts.get("hinted"):
        world.say(
            f'"Step where the stone is pale, not green," said Ant {ant.id}. '
            f'"The dry part holds better."'
        )


def choose_return(world: World, hero: Entity, aunt: Entity, ant: Entity) -> None:
    world.facts["helped"] = False
    hero.memes["honesty"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} bent toward the leaf, then looked at the shaking path and felt his heart thump like a fist on a door."
    )
    world.say(
        f"He did not pretend to be bigger than he was. Holding tight to the bundle, he turned back and went to Aunt {aunt.id} for help."
    )
    world.para()
    world.say(
        f"Aunt {aunt.id} listened, took a longer stride beside him, and said, "
        f'"Bravery does not always go alone. Sometimes it tells the truth and asks for a wiser paw."'
    )
    ant.meters["free"] += 1
    ant.memes["gratitude"] += 1
    hero.memes["bravery"] += 1
    hero.meters["balance"] += 1
    world.facts["asked_help"] = True
    propagate(world, narrate=False)
    world.say(
        f"Together they lifted the curled leaf and freed Ant {ant.id}, who bowed so low that even his feelers touched the ground."
    )


def cross_alone(world: World, hero: Entity, ant: Entity, path: PathSpec, tool: ToolSpec) -> None:
    hero.meters["crossed"] = 1.0
    world.say(
        f"Then {hero.id} {tool.use_text}. Ant {ant.id} trotted beside him until the narrow place was past."
    )
    world.say(
        f"In a few brave breaths, {hero.id} reached {path.ending}."
    )


def cross_with_aunt(world: World, hero: Entity, aunt: Entity, path: PathSpec, tool: ToolSpec) -> None:
    hero.meters["crossed"] = 1.0
    world.say(
        f"With Aunt {aunt.id} on one side and the {tool.label} on the other, "
        f"{hero.id} took the hard place step by step."
    )
    world.say(
        f"Soon the steepest part was behind them, and they came safely to {path.ending}."
    )


def deliver(world: World, hero: Entity, food: FoodSpec, ant: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"The {food.label} arrived warm enough to share, and {hero.id} even broke off a {food.crumb_word} for Ant {ant.id}."
    )


def ending_moral(world: World, hero: Entity, aunt: Entity) -> None:
    if world.facts.get("asked_help"):
        world.say(
            f"Aunt {aunt.id} nodded and said that the bravest heart is not the loudest one, but the one that faces the truth and still does the kind thing."
        )
    else:
        world.say(
            f"Aunt {aunt.id} said that fear shrinks when kindness stands up before it."
        )
    world.say(
        f"And so {hero.id} learned that on the seventeenth hard place, bravery may begin with helping another creature before helping oneself."
    )


def tell(
    hero_cfg: HeroSpec,
    hero_name: str,
    aunt_type: str,
    ant_name: str,
    path_cfg: PathSpec,
    tool_cfg: ToolSpec,
    food_cfg: FoodSpec,
    weather_cfg: WeatherSpec,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_cfg.type,
        label=hero_cfg.type,
        traits=[trait],
        role="hero",
        attrs={"home": hero_cfg.home},
    ))
    aunt = world.add(Entity(
        id=aunt_type.capitalize(),
        kind="character",
        type=aunt_type,
        label=aunt_type,
        role="aunt",
        attrs={},
    ))
    ant = world.add(Entity(
        id=ant_name,
        kind="character",
        type="ant",
        label="ant",
        role="helper",
        attrs={},
    ))
    world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        role="tool",
        attrs={},
    ))
    world.add(Entity(
        id="food",
        kind="thing",
        type="food",
        label=food_cfg.label,
        role="food",
        attrs={},
    ))

    hero.memes["bravery"] = TRAITS[trait]
    hero.memes["fear"] = float(weather_cfg.fear)
    hero.meters["balance"] = 0.0
    ant.meters["free"] = 0.0
    ant.memes["gratitude"] = 0.0

    help_first = hero.memes["bravery"] >= float(path_cfg.risk + weather_cfg.fear)
    world.facts.update(
        hero=hero,
        aunt=aunt,
        ant=ant,
        path_cfg=path_cfg,
        tool_cfg=tool_cfg,
        food_cfg=food_cfg,
        weather_cfg=weather_cfg,
        help_first=help_first,
        helped=False,
        asked_help=False,
        hinted=False,
    )

    introduce(world, hero, aunt, food_cfg, weather_cfg)
    assign_task(world, hero, aunt, food_cfg)

    world.para()
    set_out(world, hero, path_cfg, tool_cfg, weather_cfg)
    reach_landmark(world, hero, ant, path_cfg)

    world.para()
    if help_first:
        choose_help(world, hero, tool_cfg, ant)
        outcome = predict_crossing(world)
        if outcome["crosses_alone"]:
            cross_alone(world, hero, ant, path_cfg, tool_cfg)
        else:
            choose_return(world, hero, aunt, ant)
            world.para()
            cross_with_aunt(world, hero, aunt, path_cfg, tool_cfg)
    else:
        choose_return(world, hero, aunt, ant)
        world.para()
        cross_with_aunt(world, hero, aunt, path_cfg, tool_cfg)

    world.para()
    deliver(world, hero, food_cfg, ant)
    ending_moral(world, hero, aunt)

    world.facts["outcome"] = "alone" if not world.facts["asked_help"] else "with_help"
    world.facts["crossed"] = hero.meters["crossed"] >= THRESHOLD
    world.facts["final_bravery"] = hero.memes["bravery"]
    return world


KNOWLEDGE = {
    "carb": [
        (
            "What is a carb?",
            "A carb is food that gives your body energy, like bread, oats, or a bun. It helps you move and work, though you still need many kinds of food to stay healthy.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel afraid. Sometimes it means stepping forward, and sometimes it means asking for help honestly.",
        )
    ],
    "ant": [
        (
            "Why might helping a smaller creature be brave?",
            "Helping a smaller creature can be brave because you stop thinking only about your own fear. Kindness can make your heart steadier.",
        )
    ],
    "stones": [
        (
            "Why can stepping stones be slippery?",
            "Stepping stones can be slippery when water and moss make their tops smooth. Small feet need to choose the dry parts carefully.",
        )
    ],
    "log": [
        (
            "Why is a log bridge tricky to cross?",
            "A log bridge is narrow, and its bark can be smooth or loose. That means your feet need balance and care.",
        )
    ],
    "steps": [
        (
            "Why can hill steps feel hard?",
            "Hill steps can feel hard because they are steep and uneven. Wind or rain can make them seem even taller.",
        )
    ],
    "pole": [
        (
            "How can a pole help on a narrow path?",
            "A pole gives you another point to steady yourself with. That can help your body keep balance.",
        )
    ],
    "vine": [
        (
            "How can a vine loop help?",
            "A vine loop gives a paw or foot something firm to hold. Holding on can make a shaking path feel less scary.",
        )
    ],
    "staff": [
        (
            "What does a walking staff do?",
            "A walking staff helps you place your weight more carefully. It can slow you down in a good way.",
        )
    ],
    "help": [
        (
            "Is asking for help a kind of bravery?",
            "Yes. Asking for help can be brave because you tell the truth about what is hard and still try to do what is right.",
        )
    ],
}
KNOWLEDGE_ORDER = ["carb", "bravery", "ant", "stones", "log", "steps", "pole", "vine", "staff", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    food = f["food_cfg"]
    path = f["path_cfg"]
    ant = f["ant"]
    if f["outcome"] == "alone":
        return [
            f'Write a short fable for a 3-to-5-year-old that includes the words "carb" and "seventeenth", where a little {hero.type} carries {food.label} along {path.route} and grows brave by helping an ant.',
            f"Tell a gentle bravery fable in which {hero.id} reaches {path.landmark}, frees Ant {ant.id}, and then finds the courage to cross safely.",
            f'Write a child-friendly animal fable with a clear moral: kindness at the seventeenth hard place can make fear smaller.',
        ]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "carb" and "seventeenth", where a little {hero.type} faces a hard path and learns that asking for help is also bravery.',
        f"Tell a gentle animal story in which {hero.id} turns back at {path.landmark}, tells the truth about being afraid, and then returns with help to do the kind errand well.",
        f'Write a fable with a moral showing that bravery may mean honest words, a helping elder, and kindness to a smaller creature.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    aunt = f["aunt"]
    ant = f["ant"]
    path = f["path_cfg"]
    tool = f["tool_cfg"]
    food = f["food_cfg"]
    weather = f["weather_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type}, carrying {food.phrase}, Aunt {aunt.id}, and Ant {ant.id}. The errand gives the story its purpose from the very beginning.",
        ),
        (
            f"What was {hero.id} carrying, and why is the word carb in the story?",
            f"{hero.id} was carrying {food.phrase}. The grown-up called it a carb to mean it was simple food that could give a traveler energy for the road.",
        ),
        (
            f"What happened at {path.landmark}?",
            f"At {path.landmark}, the path felt hardest and Ant {ant.id} was trapped under a curled leaf. That moment turned the walk into a test of character, not just a trip.",
        ),
        (
            f"Why did the path feel scary?",
            f"It felt scary because {path.danger} and {weather.path_effect.lower()} The danger was real, so bravery in this story meant meeting a true risk carefully.",
        ),
    ]
    if f["outcome"] == "alone":
        qa.append(
            (
                f"How did helping Ant {ant.id} make {hero.id} braver?",
                f"By stopping to help, {hero.id} thought about someone smaller instead of only about fear. Ant {ant.id} then pointed out the safer place to step, so kindness and courage worked together.",
            )
        )
        qa.append(
            (
                f"How did {hero.id} get across?",
                f"{hero.id} crossed by using the {tool.label} carefully and listening to Ant {ant.id}'s advice. The crossing succeeded because the help came before the hardest steps.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} go back to Aunt {aunt.id}?",
                f"{hero.id} went back because the hard place felt too big to manage alone. Telling the truth about fear let {hero.id} return with wiser help instead of pretending.",
            )
        )
        qa.append(
            (
                "Was asking for help shown as weakness?",
                f"No. The story treats it as a brave, honest choice because {hero.id} still returned to free Ant {ant.id} and finish the errand. The courage is in doing the kind thing after speaking the truth.",
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f"The moral is that bravery grows when kindness comes first. Whether alone or with help, {hero.id} became brave by choosing the right thing at the seventeenth hard place.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    path = f["path_cfg"]
    tool = f["tool_cfg"]
    tags: set[str] = {"carb", "bravery", "ant"}
    if path.id == "stepping_stones":
        tags.add("stones")
    elif path.id == "log_bridge":
        tags.add("log")
    else:
        tags.add("steps")
    if tool.id == "reed_pole":
        tags.add("pole")
    elif tool.id == "vine_loop":
        tags.add("vine")
    else:
        tags.add("staff")
    if f["outcome"] == "with_help":
        tags.add("help")

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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(path_id: str, tool_id: str, weather_id: str) -> str:
    if tool_id in TOOLS and path_id in PATHS and not tool_fits(path_id, tool_id):
        return (
            f"(No story: the {TOOLS[tool_id].label} is not a sensible support for "
            f"{PATHS[path_id].route}. Pick a tool that actually helps on that path.)"
        )
    if weather_id in WEATHERS and path_id in PATHS and not weather_allows(path_id, weather_id):
        return (
            f"(No story: {PATHS[path_id].label} in {WEATHERS[weather_id].label} weather is too unreasonable "
            f"for this gentle fable world. Choose calmer conditions or a sturdier path.)"
        )
    return "(No story: that combination does not fit the world.)"


CURATED = [
    StoryParams(
        hero="mouse",
        name="Pip",
        aunt_type="mole",
        ant_name="Dot",
        path="stepping_stones",
        tool="reed_pole",
        food="barley_bun",
        weather="calm",
        trait="bold",
    ),
    StoryParams(
        hero="rabbit",
        name="Clover",
        aunt_type="hedgehog",
        ant_name="Ash",
        path="hill_steps",
        tool="twig_staff",
        food="oat_cake",
        weather="drizzly",
        trait="steady",
    ),
    StoryParams(
        hero="squirrel",
        name="Hazel",
        aunt_type="mole",
        ant_name="Pin",
        path="hill_steps",
        tool="vine_loop",
        food="seed_roll",
        weather="windy",
        trait="careful",
    ),
    StoryParams(
        hero="mouse",
        name="Moss",
        aunt_type="hedgehog",
        ant_name="Dot",
        path="log_bridge",
        tool="vine_loop",
        food="oat_cake",
        weather="calm",
        trait="bold",
    ),
    StoryParams(
        hero="rabbit",
        name="Thimble",
        aunt_type="mole",
        ant_name="Ash",
        path="stepping_stones",
        tool="twig_staff",
        food="seed_roll",
        weather="drizzly",
        trait="careful",
    ),
]


ASP_RULES = r"""
fits(P,T) :- tool(T), path(P), supports(T,P).
safe_weather(P,W) :- path(P), weather(W), allows(P,W).
valid(P,T,W) :- fits(P,T), safe_weather(P,W).

base_bravery(3) :- chosen_trait(bold).
base_bravery(2) :- chosen_trait(steady).
base_bravery(1) :- chosen_trait(careful).

help_first :- chosen_path(P), chosen_weather(W), base_bravery(B),
              risk(P,R), weather_fear(W,F), B >= R + F.

outcome(alone) :- help_first.
outcome(with_help) :- not help_first.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("risk", path_id, path.risk))
        for weather_id in sorted(path.allowed_weather):
            lines.append(asp.fact("allows", path_id, weather_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for path_id in sorted(tool.supports):
            lines.append(asp.fact("supports", tool_id, path_id))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("weather_fear", weather_id, weather.fear))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
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
        asp.fact("chosen_path", params.path),
        asp.fact("chosen_weather", params.weather),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    path = PATHS[params.path]
    weather = WEATHERS[params.weather]
    bravery = TRAITS[params.trait]
    return "alone" if bravery >= float(path.risk + weather.fear) else "with_help"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
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
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        saved = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=False)
        finally:
            sys.stdout = saved
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny fable world: a small animal faces a hard path, a trapped ant, and a lesson in bravery."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--name")
    ap.add_argument("--aunt-type", choices=AUNT_TYPES)
    ap.add_argument("--ant-name")
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible path/tool/weather combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.path and args.tool and not tool_fits(args.path, args.tool):
        raise StoryError(explain_rejection(args.path, args.tool, args.weather or "calm"))
    if args.path and args.weather and not weather_allows(args.path, args.weather):
        raise StoryError(explain_rejection(args.path, args.tool or "reed_pole", args.weather))

    combos = [
        combo for combo in valid_combos()
        if (args.path is None or combo[0] == args.path)
        and (args.tool is None or combo[1] == args.tool)
        and (args.weather is None or combo[2] == args.weather)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    path_id, tool_id, weather_id = rng.choice(sorted(combos))
    hero_id = args.hero or rng.choice(sorted(HEROES))
    name = args.name or rng.choice(HERO_NAMES[hero_id])
    aunt_type = args.aunt_type or rng.choice(sorted(AUNT_TYPES))
    ant_name = args.ant_name or rng.choice(ANT_NAMES)
    food_id = args.food or rng.choice(sorted(FOODS))
    trait = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        hero=hero_id,
        name=name,
        aunt_type=aunt_type,
        ant_name=ant_name,
        path=path_id,
        tool=tool_id,
        food=food_id,
        weather=weather_id,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"(Unknown hero: {params.hero})")
    if params.aunt_type not in AUNT_TYPES:
        raise StoryError(f"(Unknown aunt type: {params.aunt_type})")
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if not tool_fits(params.path, params.tool) or not weather_allows(params.path, params.weather):
        raise StoryError(explain_rejection(params.path, params.tool, params.weather))

    world = tell(
        hero_cfg=HEROES[params.hero],
        hero_name=params.name,
        aunt_type=params.aunt_type,
        ant_name=params.ant_name,
        path_cfg=PATHS[params.path],
        tool_cfg=TOOLS[params.tool],
        food_cfg=FOODS[params.food],
        weather_cfg=WEATHERS[params.weather],
        trait=params.trait,
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
        print(f"{len(combos)} compatible (path, tool, weather) combos:\n")
        for path_id, tool_id, weather_id in combos:
            print(f"  {path_id:16} {tool_id:10} {weather_id}")
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
            header = f"### {p.name}: {p.path}, {p.tool}, {p.weather}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
