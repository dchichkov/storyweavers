#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/default_happy_ending_fable.py
========================================================

A standalone story world in a gentle fable style.

Seed:
    Words: default
    Features: Happy Ending
    Style: Fable

World premise
-------------
Small animals prepare for a windy day. One character is tempted to take the
"easy default" choice instead of the proper shelter-making material. Trouble
comes when the wind arrives, a wiser helper proves the weak choice will fail,
and together they rebuild the nest or den the sturdy way. The ending image
shows the creature safe at home, having learned that the easiest default choice
is not always the wisest one.

Run it
------
    python storyworlds/worlds/gpt-5.4/default_happy_ending_fable.py
    python storyworlds/worlds/gpt-5.4/default_happy_ending_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/default_happy_ending_fable.py --all --qa
    python storyworlds/worlds/gpt-5.4/default_happy_ending_fable.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goose", "sister", "mother", "girl"}
        male = {"mouse", "beaver", "fox", "brother", "father", "boy"}
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
class AnimalKind:
    id: str
    noun: str
    home: str
    plural_home: str
    sound: str
    virtue: str
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
class Place:
    id: str
    label: str
    detail: str
    weather_sign: str
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
class WeakMaterial:
    id: str
    label: str
    phrase: str
    source: str
    fragility: int
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
class StrongMaterial:
    id: str
    label: str
    phrase: str
    source: str
    strength: int
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
    label: str
    sign: str
    force: int
    verb: str
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
class HelperAct:
    id: str
    label: str
    sense: int
    boost: int
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def shelter_need(weather: Weather) -> int:
    return weather.force


def shelter_power(weak: WeakMaterial, strong: StrongMaterial, helper: HelperAct, reinforce: bool) -> int:
    base = strong.strength if reinforce else weak.fragility
    return base + helper.boost


def weak_choice_fails(weak: WeakMaterial, weather: Weather) -> bool:
    return weak.fragility < shelter_need(weather)


def is_sensible(helper: HelperAct) -> bool:
    return helper.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for animal_id in ANIMALS:
        for place_id in PLACES:
            for weak_id, weak in WEAK_MATERIALS.items():
                for strong_id, strong in STRONG_MATERIALS.items():
                    for weather_id, weather in WEATHERS.items():
                        if weak_choice_fails(weak, weather) and strong.strength >= shelter_need(weather):
                            combos.append((animal_id, place_id, weak_id, strong_id, weather_id))
    return combos


def _r_collapse(world: World) -> list[str]:
    home = world.get("home")
    if home.meters["risky"] < THRESHOLD:
        return []
    sig = ("collapse", "home")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    home.meters["shaken"] += 1
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["fear"] += 1
    helper.memes["care"] += 1
    return ["__collapse__"]


RULES = [Rule(name="collapse", tag="physical", apply=_r_collapse)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_default_failure(world: World) -> dict:
    sim = world.copy()
    sim.get("home").meters["risky"] += 1
    propagate(sim, narrate=False)
    return {
        "shaken": sim.get("home").meters["shaken"] >= THRESHOLD,
        "fear": sim.get("hero").memes["fear"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, animal: AnimalKind, place: Place) -> None:
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On the edge of {place.label}, where {place.detail}, lived a little {animal.noun} named {hero.id}. "
        f"{hero.id} wished to make {hero.pronoun('possessive')} {animal.home} neat before rough weather came."
    )
    world.say(
        f"Nearby lived {helper.id}, a kindly {helper.type} known for being {animal.virtue}. "
        f"Among the grass and reeds, even small creatures listened when {helper.id} spoke."
    )


def weather_warning(world: World, weather: Weather, place: Place) -> None:
    world.say(
        f"That morning {place.weather_sign}, and the air carried a warning: soon a {weather.label} would {weather.verb}."
    )


def choose_default(world: World, hero: Entity, weak: WeakMaterial, animal: AnimalKind) -> None:
    hero.memes["hurry"] += 1
    world.say(
        f"{hero.id} found {weak.phrase} {weak.source} and thought, "
        f'"This is the easy default choice. I can finish my {animal.home} quickly."'
    )
    world.say(
        f"So {hero.pronoun()} tucked the {weak.label} into place and smiled at the neat shape of it."
    )


def helper_warn(world: World, hero: Entity, helper: Entity, weak: WeakMaterial, animal: AnimalKind) -> None:
    pred = predict_default_failure(world)
    world.facts["predicted_shaken"] = pred["shaken"]
    helper.memes["wisdom"] += 1
    world.say(
        f'But {helper.id} paused and looked closely. "{weak.label.capitalize()} may look tidy," '
        f"{helper.pronoun()} said, \"but a fast wind will pull it apart.\""
    )
    if pred["shaken"]:
        world.say(
            f"{helper.id} tapped the side of the little {animal.home}. "
            f'"If you trust the easy default when stronger work is needed, your home will tremble before night."'
        )


def ignore_warning(world: World, hero: Entity) -> None:
    hero.memes["stubborn"] += 1
    world.say(
        f"{hero.id} wanted the quick way more than the careful way, so {hero.pronoun()} kept working."
    )


def wind_strikes(world: World, weather: Weather, animal: AnimalKind) -> None:
    home = world.get("home")
    home.meters["risky"] += 1
    propagate(world, narrate=False)
    world.say(
        f"By dusk the {weather.label} came. It {weather.verb}, and the little {animal.home} gave a frightened shiver."
    )


def collapse_image(world: World, hero: Entity, weak: WeakMaterial) -> None:
    world.say(
        f"The {weak.label} rustled, slipped, and flew loose. {hero.id} heard {hero.pronoun('possessive')} own heart beat fast."
    )


def ask_help(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["humility"] += 1
    world.say(
        f'"Friend {helper.id}," cried {hero.id}, "you were right. Please show me the wiser way."'
    )


def rebuild(world: World, hero: Entity, helper: Entity, strong: StrongMaterial,
            helper_act: HelperAct, animal: AnimalKind) -> None:
    home = world.get("home")
    home.meters["risky"] = 0.0
    home.meters["shaken"] = 0.0
    home.meters["sturdy"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["gratitude"] += 1
    hero.memes["lesson"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{helper.id} did not laugh. {helper.pronoun().capitalize()} {helper_act.text} with {strong.phrase} {strong.source}."
    )
    world.say(
        f"Together they tucked, pressed, and wove until the small {animal.home} sat firm against the earth."
    )


def happy_ending(world: World, hero: Entity, helper: Entity, weather: Weather, animal: AnimalKind) -> None:
    hero.memes["peace"] += 1
    hero.memes["joy"] += 1
    helper.memes["peace"] += 1
    world.say(
        f"When the {weather.label} blew again, the little {animal.home} only hummed softly. "
        f"Inside, {hero.id} and {helper.id} listened to the sound and were not afraid."
    )
    world.say(
        f"From that day on, {hero.id} remembered that the easiest default is not always the safest one, "
        f"and a wise friend can help turn trouble into shelter."
    )


def moral(world: World) -> None:
    world.say("And so the small learned what the old already knew: haste likes the easy door, but wisdom builds the lasting one.")


def tell(animal: AnimalKind, place: Place, weak: WeakMaterial, strong: StrongMaterial,
         weather: Weather, helper_act: HelperAct,
         hero_name: str = "Pip", helper_name: str = "Moss",
         helper_type: str = "beaver") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=animal.id, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    home = world.add(Entity(id="home", kind="thing", type="home", label=animal.home))
    home.meters["risky"] = 0.0
    home.meters["shaken"] = 0.0
    hero.memes["fear"] = 0.0
    helper.memes["care"] = 0.0
    world.facts["animal"] = animal
    world.facts["place"] = place
    world.facts["weak"] = weak
    world.facts["strong"] = strong
    world.facts["weather"] = weather
    world.facts["helper_act"] = helper_act
    world.facts["hero_name"] = hero_name
    world.facts["helper_name"] = helper_name

    introduce(world, hero, helper, animal, place)
    weather_warning(world, weather, place)

    world.para()
    choose_default(world, hero, weak, animal)
    helper_warn(world, hero, helper, weak, animal)
    ignore_warning(world, hero)

    world.para()
    wind_strikes(world, weather, animal)
    collapse_image(world, hero, weak)
    ask_help(world, hero, helper)

    world.para()
    rebuild(world, hero, helper, strong, helper_act, animal)
    happy_ending(world, hero, helper, weather, animal)
    moral(world)

    world.facts.update(
        hero=hero,
        helper=helper,
        home=home,
        outcome="happy",
        default_failed=True,
        lesson_learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


ANIMALS = {
    "mouse": AnimalKind(
        id="mouse",
        noun="mouse",
        home="nest",
        plural_home="nests",
        sound="squeak",
        virtue="careful with small things",
        tags={"mouse", "home"},
    ),
    "wren": AnimalKind(
        id="wren",
        noun="wren",
        home="nest",
        plural_home="nests",
        sound="chirp",
        virtue="patient in the reeds",
        tags={"bird", "home"},
    ),
    "rabbit": AnimalKind(
        id="rabbit",
        noun="rabbit",
        home="burrow-door",
        plural_home="burrow-doors",
        sound="thump",
        virtue="steady in hard weather",
        tags={"rabbit", "home"},
    ),
}

PLACES = {
    "meadow": Place(
        id="meadow",
        label="the meadow",
        detail="clover nodded and the field mice kept their narrow paths",
        weather_sign="the tall grass bowed low",
        tags={"meadow"},
    ),
    "pond": Place(
        id="pond",
        label="the pond",
        detail="rushes leaned over the bank and dragonflies stitched the light",
        weather_sign="rings shivered across the water",
        tags={"pond"},
    ),
    "hedge": Place(
        id="hedge",
        label="the old hedge",
        detail="brambles held morning dew like beads of glass",
        weather_sign="the blackberries trembled on their stems",
        tags={"hedge"},
    ),
}

WEAK_MATERIALS = {
    "dry_grass": WeakMaterial(
        id="dry_grass",
        label="dry grass",
        phrase="a bundle of dry grass",
        source="from the sunny edge of the path",
        fragility=1,
        tags={"grass", "shelter"},
    ),
    "feathers": WeakMaterial(
        id="feathers",
        label="loose feathers",
        phrase="a drift of loose feathers",
        source="from under a willow",
        fragility=1,
        tags={"feather", "shelter"},
    ),
    "paper": WeakMaterial(
        id="paper",
        label="paper scraps",
        phrase="some paper scraps",
        source="beside the cart track",
        fragility=0,
        tags={"paper", "shelter"},
    ),
}

STRONG_MATERIALS = {
    "mud_twigs": StrongMaterial(
        id="mud_twigs",
        label="mud and twigs",
        phrase="mud and stout twigs",
        source="from the damp bank",
        strength=3,
        tags={"twigs", "mud", "shelter"},
    ),
    "woven_reeds": StrongMaterial(
        id="woven_reeds",
        label="woven reeds",
        phrase="long woven reeds",
        source="from the pond edge",
        strength=3,
        tags={"reeds", "shelter"},
    ),
    "root_fibers": StrongMaterial(
        id="root_fibers",
        label="root fibers",
        phrase="root fibers and packed earth",
        source="from beneath a fallen log",
        strength=2,
        tags={"roots", "earth", "shelter"},
    ),
}

WEATHERS = {
    "wind": Weather(
        id="wind",
        label="wind",
        sign="the leaves turned pale undersides upward",
        force=2,
        verb="whistled through every stem",
        tags={"wind", "weather"},
    ),
    "gust": Weather(
        id="gust",
        label="gusty evening",
        sign="the reeds bent and sprang back again",
        force=2,
        verb="rushed over the field in sharp breaths",
        tags={"wind", "weather"},
    ),
    "storm": Weather(
        id="storm",
        label="storm",
        sign="the clouds gathered in thick gray folds",
        force=3,
        verb="beat at every branch and bank",
        tags={"storm", "weather"},
    ),
}

HELPER_ACTS = {
    "brace": HelperAct(
        id="brace",
        label="brace the walls",
        sense=3,
        boost=1,
        text="showed how to brace the walls",
        qa_text="showed how to brace the walls with stronger material",
        tags={"repair", "help"},
    ),
    "weave": HelperAct(
        id="weave",
        label="weave it tight",
        sense=3,
        boost=1,
        text="showed how to weave each side tight",
        qa_text="showed how to weave the shelter tightly",
        tags={"repair", "help"},
    ),
    "pile_more_weak": HelperAct(
        id="pile_more_weak",
        label="pile on more weak bits",
        sense=1,
        boost=0,
        text="suggested only piling on more of the same weak pieces",
        qa_text="only added more weak pieces",
        tags={"repair"},
    ),
}

HERO_NAMES = ["Pip", "Nip", "Tansy", "Bram", "Miri", "Wisp"]
HELPER_NAMES = ["Moss", "Willow", "Brindle", "Hazel", "Reed", "Clover"]


@dataclass
class StoryParams:
    animal: str
    place: str
    weak_material: str
    strong_material: str
    weather: str
    helper_act: str
    hero_name: str
    helper_name: str
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
    "wind": [
        (
            "Why can wind knock apart a weak shelter?",
            "Wind pushes and tugs on loose pieces. If a shelter is not tied, packed, or woven well, the moving air can pull it open."
        )
    ],
    "storm": [
        (
            "What makes a storm stronger than a gentle breeze?",
            "A storm brings harder wind and rougher weather all at once. It shakes branches, grass, and small homes much more strongly."
        )
    ],
    "grass": [
        (
            "Why is dry grass not always a strong building material?",
            "Dry grass is light and brittle. It can scatter when wind catches it unless something stronger holds it in place."
        )
    ],
    "paper": [
        (
            "Why are paper scraps poor material for an outdoor home?",
            "Paper tears and blows away easily when it gets rough weather. It does not hold a shelter together for long."
        )
    ],
    "reeds": [
        (
            "Why are reeds useful for building?",
            "Long reeds can be bent and woven together. When they are tucked tightly, they help small walls stay in place."
        )
    ],
    "twigs": [
        (
            "What do twigs do in a small shelter?",
            "Twigs give a shelter a firm shape. They act like little ribs that help lighter material stay where it belongs."
        )
    ],
    "repair": [
        (
            "Why is asking for help sometimes wise?",
            "Another creature may see a problem you missed and know a better way to fix it. Asking for help can turn a mistake into a lesson."
        )
    ],
    "home": [
        (
            "Why do animals need sturdy homes?",
            "A sturdy home helps keep a small creature safe from weather and fear. Good shelter lets it rest, hide, and sleep in peace."
        )
    ],
}
KNOWLEDGE_ORDER = ["wind", "storm", "grass", "paper", "reeds", "twigs", "repair", "home"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal"]
    weak = f["weak"]
    weather = f["weather"]
    return [
        f'Write a short fable for a young child that uses the word "default" and features a little {animal.noun} choosing a weak material before {weather.label}.',
        f"Tell a happy-ending animal fable where the hero trusts an easy default, learns it is unwise, and rebuilds a safer home with help.",
        f"Write a gentle moral tale in a fable style about {weak.label}, weather, wise advice, and a safe home by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    animal = f["animal"]
    weak = f["weak"]
    strong = f["strong"]
    weather = f["weather"]
    helper_act = f["helper_act"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {animal.noun}, and {helper.id}, the wise friend who helped. The story follows how a small mistake became a lesson instead of a disaster."
        ),
        (
            f"Why did {hero.id} call the first choice the default choice?",
            f"{hero.id} called it the default choice because it was the easiest and quickest thing to use. It felt simple in the moment, even though it was not the safest plan."
        ),
        (
            f"Why did {helper.id} warn {hero.id} about the {weak.label}?",
            f"{helper.id} warned that the {weak.label} would not stand up to the {weather.label}. In the world of the story, the weak shelter was predicted to shake apart when rough weather came."
        ),
        (
            f"What happened when the {weather.label} arrived?",
            f"The little {animal.home} shivered and the weak pieces slipped loose. That frightening moment showed {hero.id} that the quick choice had been too fragile."
        ),
        (
            f"How did {helper.id} solve the problem?",
            f"{helper.id} {helper_act.qa_text} using {strong.phrase} {strong.source}. Together they rebuilt the {animal.home} so it stayed firm when the weather returned."
        ),
        (
            "How did the story end?",
            f"It ended happily, with the little {animal.home} standing strong while the wind blew outside. {hero.id} felt safe at last and remembered the lesson about easy defaults and wise work."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    f = world.facts
    tags |= f["animal"].tags
    tags |= f["weak"].tags
    tags |= f["strong"].tags
    tags |= f["weather"].tags
    tags |= f["helper_act"].tags
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="mouse",
        place="meadow",
        weak_material="dry_grass",
        strong_material="mud_twigs",
        weather="wind",
        helper_act="brace",
        hero_name="Pip",
        helper_name="Moss",
        helper_type="beaver",
    ),
    StoryParams(
        animal="wren",
        place="pond",
        weak_material="feathers",
        strong_material="woven_reeds",
        weather="gust",
        helper_act="weave",
        hero_name="Tansy",
        helper_name="Reed",
        helper_type="rabbit",
    ),
    StoryParams(
        animal="rabbit",
        place="hedge",
        weak_material="paper",
        strong_material="root_fibers",
        weather="storm",
        helper_act="brace",
        hero_name="Bram",
        helper_name="Hazel",
        helper_type="mouse",
    ),
]


def explain_combo_rejection(weak: WeakMaterial, strong: StrongMaterial, weather: Weather) -> str:
    if not weak_choice_fails(weak, weather):
        return (
            f"(No story: {weak.label} would already be strong enough for the {weather.label}, "
            f"so the warning, turn, and lesson would be too weak.)"
        )
    if strong.strength < shelter_need(weather):
        return (
            f"(No story: {strong.label} is not sturdy enough for the {weather.label}, "
            f"so this world cannot reach a happy ending.)"
        )
    return "(No story: this combination does not create a clear weak-choice and strong-fix contrast.)"


def explain_helper_rejection(helper_act: HelperAct) -> str:
    return (
        f"(Refusing helper action '{helper_act.id}': it scores too low on common sense "
        f"(sense={helper_act.sense} < {SENSE_MIN}). The helper must actually improve the shelter.)"
    )


def outcome_of(params: StoryParams) -> str:
    weak = WEAK_MATERIALS[params.weak_material]
    strong = STRONG_MATERIALS[params.strong_material]
    weather = WEATHERS[params.weather]
    helper = HELPER_ACTS[params.helper_act]
    if not weak_choice_fails(weak, weather):
        return "invalid"
    if not is_sensible(helper):
        return "invalid"
    if shelter_power(weak, strong, helper, reinforce=True) >= shelter_need(weather):
        return "happy"
    return "sad"


ASP_RULES = r"""
weak_choice_fails(W, Y) :- weak_material(W), weather(Y), fragility(W, F), force(Y, Need), F < Need.
strong_enough(S, Y) :- strong_material(S), weather(Y), strength(S, P), force(Y, Need), P >= Need.
sensible_helper(H) :- helper_act(H), sense(H, S), sense_min(M), S >= M.
valid(A, P, W, S, Y) :- animal(A), place(P), weak_material(W), strong_material(S), weather(Y),
                        weak_choice_fails(W, Y), strong_enough(S, Y).

reinforced_power(S, H, P + B) :- strength(S, P), boost(H, B), sensible_helper(H).
happy_outcome :- chosen_strong(S), chosen_weather(Y), chosen_helper(H),
                 force(Y, Need), reinforced_power(S, H, Power), Power >= Need.
outcome(happy) :- happy_outcome.
outcome(invalid) :- chosen_helper(H), helper_act(H), not sensible_helper(H).
#show valid/5.
#show sensible_helper/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for wid, weak in WEAK_MATERIALS.items():
        lines.append(asp.fact("weak_material", wid))
        lines.append(asp.fact("fragility", wid, weak.fragility))
    for sid, strong in STRONG_MATERIALS.items():
        lines.append(asp.fact("strong_material", sid))
        lines.append(asp.fact("strength", sid, strong.strength))
    for yid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", yid))
        lines.append(asp.fact("force", yid, weather.force))
    for hid, helper in HELPER_ACTS.items():
        lines.append(asp.fact("helper_act", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        lines.append(asp.fact("boost", hid, helper.boost))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_helpers() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(h for (h,) in asp.atoms(model, "sensible_helper"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_strong", params.strong_material),
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_helper", params.helper_act),
        ]
    )
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    if out:
        return out[0][0]
    strong = STRONG_MATERIALS[params.strong_material]
    weather = WEATHERS[params.weather]
    helper = HELPER_ACTS[params.helper_act]
    if is_sensible(helper) and strong.strength + helper.boost >= weather.force:
        return "happy"
    return "invalid"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_helpers = {hid for hid, h in HELPER_ACTS.items() if is_sensible(h)}
    asp_helpers = set(asp_sensible_helpers())
    if py_helpers == asp_helpers:
        print(f"OK: sensible helpers match ({sorted(py_helpers)}).")
    else:
        rc = 1
        print("MISMATCH in sensible helpers.")
        print("  python:", sorted(py_helpers))
        print("  clingo:", sorted(asp_helpers))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")  # ordinary generate/emit smoke test
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Happy-ending fable storyworld: a small creature learns the easy default is not always the wise choice."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--weak-material", dest="weak_material", choices=WEAK_MATERIALS)
    ap.add_argument("--strong-material", dest="strong_material", choices=STRONG_MATERIALS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--helper-act", dest="helper_act", choices=HELPER_ACTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mouse", "rabbit", "beaver", "wren"])
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
    if args.weak_material and args.weather and not weak_choice_fails(
        WEAK_MATERIALS[args.weak_material], WEATHERS[args.weather]
    ):
        raise StoryError(explain_combo_rejection(
            WEAK_MATERIALS[args.weak_material],
            STRONG_MATERIALS[args.strong_material] if args.strong_material else next(iter(STRONG_MATERIALS.values())),
            WEATHERS[args.weather],
        ))
    if args.strong_material and args.weather and STRONG_MATERIALS[args.strong_material].strength < shelter_need(WEATHERS[args.weather]):
        weak = WEAK_MATERIALS[args.weak_material] if args.weak_material else next(iter(WEAK_MATERIALS.values()))
        raise StoryError(explain_combo_rejection(weak, STRONG_MATERIALS[args.strong_material], WEATHERS[args.weather]))
    if args.helper_act and not is_sensible(HELPER_ACTS[args.helper_act]):
        raise StoryError(explain_helper_rejection(HELPER_ACTS[args.helper_act]))

    combos = [
        c for c in valid_combos()
        if (args.animal is None or c[0] == args.animal)
        and (args.place is None or c[1] == args.place)
        and (args.weak_material is None or c[2] == args.weak_material)
        and (args.strong_material is None or c[3] == args.strong_material)
        and (args.weather is None or c[4] == args.weather)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal, place, weak_material, strong_material, weather = rng.choice(sorted(combos))
    sensible = sorted(hid for hid, h in HELPER_ACTS.items() if is_sensible(h))
    helper_act = args.helper_act or rng.choice(sensible)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    helper_type = args.helper_type or rng.choice(["mouse", "rabbit", "beaver", "wren"])
    return StoryParams(
        animal=animal,
        place=place,
        weak_material=weak_material,
        strong_material=strong_material,
        weather=weather,
        helper_act=helper_act,
        hero_name=hero_name,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        animal = ANIMALS[params.animal]
        place = PLACES[params.place]
        weak = WEAK_MATERIALS[params.weak_material]
        strong = STRONG_MATERIALS[params.strong_material]
        weather = WEATHERS[params.weather]
        helper_act = HELPER_ACTS[params.helper_act]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not weak_choice_fails(weak, weather) or strong.strength < shelter_need(weather):
        raise StoryError(explain_combo_rejection(weak, strong, weather))
    if not is_sensible(helper_act):
        raise StoryError(explain_helper_rejection(helper_act))

    world = tell(
        animal=animal,
        place=place,
        weak=weak,
        strong=strong,
        weather=weather,
        helper_act=helper_act,
        hero_name=params.hero_name,
        helper_name=params.helper_name,
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
        print(f"sensible helpers: {', '.join(asp_sensible_helpers())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, place, weak, strong, weather) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{x:12}" for x in combo))
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
                f"### {p.hero_name}: {p.weak_material} -> {p.strong_material} "
                f"against {p.weather}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
