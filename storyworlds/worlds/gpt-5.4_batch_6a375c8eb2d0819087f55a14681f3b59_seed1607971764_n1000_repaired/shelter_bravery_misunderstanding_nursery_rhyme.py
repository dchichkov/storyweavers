#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shelter_bravery_misunderstanding_nursery_rhyme.py
============================================================================

A standalone story world for a nursery-rhyme-style tale about a brave child, a
small misunderstanding, and finding shelter.

The domain is deliberately tiny and constraint-checked:

- Two children are outdoors when weather turns blustery or wet.
- A worried child misunderstands an ordinary thing as something scary.
- A braver child goes near, looks closely, and learns the truth.
- Then they hurry into a suitable shelter and end with a calm, changed image.

The world model drives the turn:
fear, wetness, courage, trust, and shelter are simulated as typed entities with
physical meters and emotional memes. A Python reasonableness gate refuses weak
or implausible combinations, and an inline ASP twin mirrors that gate and the
outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/shelter_bravery_misunderstanding_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/shelter_bravery_misunderstanding_nursery_rhyme.py --place green --weather rain --mistake sheet --shelter gazebo
    python storyworlds/worlds/gpt-5.4/shelter_bravery_misunderstanding_nursery_rhyme.py --weather storm --shelter tree
    python storyworlds/worlds/gpt-5.4/shelter_bravery_misunderstanding_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/shelter_bravery_misunderstanding_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/shelter_bravery_misunderstanding_nursery_rhyme.py --verify
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
BRAVERY_MIN = 5
CALM_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    open_top: bool = False
    windbreak: bool = False
    ordinary: bool = False
    hanging: bool = False
    rooted: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id.lower()
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
    rhyme_open: str
    rhyme_close: str
    affords_mistakes: set[str] = field(default_factory=set)
    affords_shelters: set[str] = field(default_factory=set)
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
    line: str
    drip_word: str
    severity: int
    needs_roof: bool
    needs_windbreak: bool
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
class Mistake:
    id: str
    label: str
    phrase: str
    appears_as: str
    truth: str
    sound: str
    requires: set[str] = field(default_factory=set)
    place_tags: set[str] = field(default_factory=set)
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
class ShelterKind:
    id: str
    label: str
    phrase: str
    roof: bool
    windbreak: bool
    cozy_line: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"brave", "worried"}]

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


def _r_weather_soaks(world: World) -> list[str]:
    out: list[str] = []
    weather = world.facts["weather_cfg"]
    if weather.severity <= 0:
        return out
    shelter = world.get("shelter")
    if shelter.meters["occupied"] >= THRESHOLD:
        return out
    for child in world.children():
        sig = ("wet", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.meters["wet"] += 1
        if weather.needs_windbreak:
            child.meters["windblown"] += 1
        out.append("__weather__")
    return out


def _r_fear_freezes(world: World) -> list[str]:
    out: list[str] = []
    worried = world.get("worried")
    if worried.memes["fear"] < THRESHOLD or world.facts.get("clarified", False):
        return out
    sig = ("freeze", worried.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    worried.memes["freeze"] += 1
    out.append("__freeze__")
    return out


def _r_clarity_calms(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("clarified", False):
        return out
    worried = world.get("worried")
    brave = world.get("brave")
    if worried.memes["fear"] <= 0:
        return out
    sig = ("calm", worried.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    worried.memes["fear"] = 0.0
    worried.memes["calm"] += 1
    worried.memes["trust"] += 1
    brave.memes["gentle"] += 1
    out.append("__calm__")
    return out


def _r_shelter_comforts(world: World) -> list[str]:
    out: list[str] = []
    shelter = world.get("shelter")
    if shelter.meters["occupied"] < THRESHOLD:
        return out
    for child in world.children():
        sig = ("comfort", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["comfort"] += 1
        if child.meters["wet"] > 0:
            child.meters["drying"] += 1
        out.append("__shelter__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="weather_soaks", tag="physical", apply=_r_weather_soaks),
    Rule(name="fear_freezes", tag="emotional", apply=_r_fear_freezes),
    Rule(name="clarity_calms", tag="emotional", apply=_r_clarity_calms),
    Rule(name="shelter_comforts", tag="emotional", apply=_r_shelter_comforts),
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


def place_allows(place: Place, mistake: Mistake, shelter: ShelterKind) -> bool:
    return mistake.id in place.affords_mistakes and shelter.id in place.affords_shelters


def mistake_matches_weather(place: Place, weather: Weather, mistake: Mistake) -> bool:
    if mistake.place_tags and not (place.tags & mistake.place_tags):
        return False
    return mistake.requires.issubset(weather.tags | place.tags)


def shelter_protects(weather: Weather, shelter: ShelterKind) -> bool:
    if weather.needs_roof and not shelter.roof:
        return False
    if weather.needs_windbreak and not shelter.windbreak:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for weather_id, weather in WEATHERS.items():
            for mistake_id, mistake in MISTAKES.items():
                for shelter_id, shelter in SHELTERS.items():
                    if (
                        place_allows(place, mistake, shelter)
                        and mistake_matches_weather(place, weather, mistake)
                        and shelter_protects(weather, shelter)
                    ):
                        combos.append((place_id, weather_id, mistake_id, shelter_id))
    return combos


def explain_rejection(place: Place, weather: Weather, mistake: Mistake, shelter: ShelterKind) -> str:
    if not place_allows(place, mistake, shelter):
        return (
            f"(No story: at {place.label}, {mistake.label} is not a good fit or "
            f"{shelter.phrase} is not really there to run to. Pick a place that honestly contains both.)"
        )
    if not mistake_matches_weather(place, weather, mistake):
        return (
            f"(No story: {mistake.phrase} does not make a convincing misunderstanding in {weather.id}. "
            f"This world only tells scenes where the mistaken thing could really seem spooky.)"
        )
    if not shelter_protects(weather, shelter):
        return (
            f"(No story: {shelter.phrase} is too weak for {weather.id}. "
            f"The shelter must truly keep the children safe from the weather.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_scare(world: World) -> dict:
    sim = world.copy()
    worried = sim.get("worried")
    worried.memes["fear"] += 1
    propagate(sim, narrate=False)
    return {
        "freezes": worried.memes["freeze"] >= THRESHOLD,
        "wet": worried.meters["wet"] >= THRESHOLD,
    }


def open_rhyme(world: World, brave: Entity, worried: Entity, place: Place, weather: Weather) -> None:
    brave.memes["cheer"] += 1
    worried.memes["cheer"] += 1
    world.say(
        f"In {place.label}, so trim and bright, {place.rhyme_open}. "
        f"{brave.id} and {worried.id} skipped side by side while {weather.line}."
    )
    world.say(
        f'"Trip and tap, tip and toe," sang {brave.id}. '
        f'"We can wander soft and slow."'
    )


def weather_turn(world: World, worried: Entity, weather: Weather) -> None:
    world.say(
        f"But soon the air changed tune. {weather.drip_word.capitalize()} went the day, "
        f"and the hedges gave a little sway."
    )
    worried.memes["unease"] += 1
    propagate(world, narrate=False)


def misunderstand(world: World, worried: Entity, mistake: Mistake) -> None:
    worried.memes["fear"] += 1
    pred = predict_scare(world)
    world.facts["predicted_freeze"] = pred["freezes"]
    world.say(
        f"Then {worried.id} saw {mistake.phrase} and gasped. "
        f'"Oh dear, oh my! It is {mistake.appears_as}!"'
    )
    if pred["freezes"]:
        world.say(
            f"{worried.id} stopped with still little shoes. "
            f"{worried.pronoun().capitalize()} did not want to go one step more."
        )
    propagate(world, narrate=False)


def brave_approach(world: World, brave: Entity, worried: Entity, mistake: Mistake) -> None:
    brave.memes["bravery"] = float(brave.attrs["bravery"])
    brave.memes["care"] += 1
    world.say(
        f'{brave.id} squeezed {worried.id}\'s hand. '
        f'"Stay by me. I will look, and I will look kindly too."'
    )
    world.say(
        f"So {brave.id} went pat-pat, not boom-boom, closer to the {mistake.label}."
    )


def clarify(world: World, brave: Entity, worried: Entity, mistake: Mistake) -> None:
    world.facts["clarified"] = True
    world.facts["clarifier"] = brave.id
    world.say(
        f"Near at hand, the fright grew small. It was not {mistake.appears_as} at all. "
        f"It was {mistake.truth}."
    )
    propagate(world, narrate=False)
    world.say(
        f'{brave.id} called back, "See? It only went {mistake.sound}. '
        f'It is ordinary, not awful."'
    )
    if worried.memes["calm"] >= CALM_MIN:
        world.say(
            f"{worried.id} blinked once, then twice, and gave a shy little nod."
        )


def run_to_shelter(world: World, brave: Entity, worried: Entity, shelter: ShelterKind) -> None:
    shelter_ent = world.get("shelter")
    shelter_ent.meters["occupied"] += 1
    world.say(
        f'"Come along now, quick but light; let us find some shelter bright." '
        f'Hand in hand, they hurried to {shelter.phrase}.'
    )
    propagate(world, narrate=False)
    world.say(shelter.cozy_line)
    world.say(
        f"There they stood while little drops or gusts stayed outside, and their breaths grew easy again."
    )


def ending(world: World, brave: Entity, worried: Entity, place: Place, weather: Weather) -> None:
    world.say(
        f'Soon {worried.id} gave a softer song: "I thought wrong, but not for long."'
    )
    world.say(
        f'{brave.id} smiled. "Brave can mean a gentle peek, and shelter can be warm though week feels bleak."'
    )
    world.say(
        f"So in {place.label}, snug and slight, {place.rhyme_close}. "
        f"The weather fussed outside, but inside their hearts were brave and right."
    )


def tell(
    place: Place,
    weather: Weather,
    mistake: Mistake,
    shelter: ShelterKind,
    brave_name: str = "Pip",
    brave_gender: str = "boy",
    worried_name: str = "Moll",
    worried_gender: str = "girl",
    bravery: int = 6,
) -> World:
    world = World()
    brave = world.add(
        Entity(
            id=brave_name,
            kind="character",
            type=brave_gender,
            role="brave",
            label=brave_name,
            attrs={"bravery": bravery},
            traits=["steady", "kind"],
        )
    )
    worried = world.add(
        Entity(
            id=worried_name,
            kind="character",
            type=worried_gender,
            role="worried",
            label=worried_name,
            attrs={"bravery": 2},
            traits=["small", "watchful"],
        )
    )
    world.add(
        Entity(
            id="mistake",
            kind="thing",
            type="ordinary_object",
            label=mistake.label,
            ordinary=True,
            hanging=("cloth" in mistake.tags),
            rooted=("plant" in mistake.tags),
        )
    )
    world.add(
        Entity(
            id="shelter",
            kind="thing",
            type="shelter",
            label=shelter.label,
            open_top=shelter.roof,
            windbreak=shelter.windbreak,
        )
    )

    world.facts.update(
        place_cfg=place,
        weather_cfg=weather,
        mistake_cfg=mistake,
        shelter_cfg=shelter,
        brave=brave,
        worried=worried,
        clarified=False,
        outcome="unclear",
    )

    open_rhyme(world, brave, worried, place, weather)
    weather_turn(world, worried, weather)

    world.para()
    misunderstand(world, worried, mistake)
    brave_approach(world, brave, worried, mistake)
    clarify(world, brave, worried, mistake)

    world.para()
    run_to_shelter(world, brave, worried, shelter)
    ending(world, brave, worried, place, weather)

    world.facts["outcome"] = "safe_and_clear"
    world.facts["fear_was_cleared"] = worried.memes["calm"] >= THRESHOLD
    world.facts["sheltered"] = world.get("shelter").meters["occupied"] >= THRESHOLD
    return world


PLACES = {
    "green": Place(
        id="green",
        label="the village green",
        rhyme_open="where daisies nodded and puddles held the light",
        rhyme_close="the bell of the green gave one mild ring for night",
        affords_mistakes={"sheet", "scarecrow"},
        affords_shelters={"gazebo", "porch", "tree"},
        tags={"green", "lane", "cloth", "field"},
    ),
    "garden": Place(
        id="garden",
        label="the cottage garden",
        rhyme_open="where mint bent low and roses bobbed in sight",
        rhyme_close="the small gate clicked and all the leaves sat light",
        affords_mistakes={"sheet", "bush"},
        affords_shelters={"porch", "tree"},
        tags={"garden", "cloth", "plant", "cottage"},
    ),
    "farm": Place(
        id="farm",
        label="the farm lane",
        rhyme_open="where straw stacks glowed beside the byre so white",
        rhyme_close="the hens grew still and tucked their heads in tight",
        affords_mistakes={"scarecrow", "bush"},
        affords_shelters={"porch", "shed"},
        tags={"farm", "field", "plant"},
    ),
}

WEATHERS = {
    "drizzle": Weather(
        id="drizzle",
        line="drizzle stitched silver threads through the air",
        drip_word="drip drop",
        severity=1,
        needs_roof=True,
        needs_windbreak=False,
        tags={"wet", "soft"},
    ),
    "rain": Weather(
        id="rain",
        line="rain drummed a round little beat on the path",
        drip_word="patter patter",
        severity=2,
        needs_roof=True,
        needs_windbreak=False,
        tags={"wet", "heavy"},
    ),
    "storm": Weather(
        id="storm",
        line="storm wind hummed and rain came slant and quick",
        drip_word="whoosh hush",
        severity=3,
        needs_roof=True,
        needs_windbreak=True,
        tags={"wet", "wind", "heavy"},
    ),
}

MISTAKES = {
    "sheet": Mistake(
        id="sheet",
        label="sheet on the washing line",
        phrase="a white sheet flapping on the line",
        appears_as="a tall pale ghost",
        truth="only the laundry dancing in the wind",
        sound="flap-flap",
        requires={"wet"},
        place_tags={"cloth"},
        tags={"misunderstanding", "cloth"},
    ),
    "scarecrow": Mistake(
        id="scarecrow",
        label="scarecrow",
        phrase="a bent scarecrow by the path",
        appears_as="a grumbling giant in a hat",
        truth="just a scarecrow with straw in its sleeves",
        sound="rustle-rustle",
        requires={"wind"},
        place_tags={"field"},
        tags={"misunderstanding", "field"},
    ),
    "bush": Mistake(
        id="bush",
        label="gooseberry bush",
        phrase="a gooseberry bush shaking in the gust",
        appears_as="a crouching beast with prickly back",
        truth="only a bush bowing and springing again",
        sound="swish-swish",
        requires={"wind"},
        place_tags={"plant"},
        tags={"misunderstanding", "plant"},
    ),
}

SHELTERS = {
    "porch": ShelterKind(
        id="porch",
        label="porch",
        phrase="the cottage porch",
        roof=True,
        windbreak=True,
        cozy_line="Under the porch roof, the boards stayed dry and the wind could not nip their knees.",
        tags={"porch", "shelter"},
    ),
    "gazebo": ShelterKind(
        id="gazebo",
        label="gazebo",
        phrase="the painted gazebo",
        roof=True,
        windbreak=False,
        cozy_line="In the gazebo, the roof kept off the drops, and the rails made a neat ring round them.",
        tags={"gazebo", "shelter"},
    ),
    "shed": ShelterKind(
        id="shed",
        label="shed",
        phrase="the red tool shed",
        roof=True,
        windbreak=True,
        cozy_line="Inside the shed door, it smelled of wood and apples, and the storm sounded far away.",
        tags={"shed", "shelter"},
    ),
    "tree": ShelterKind(
        id="tree",
        label="tree",
        phrase="the old willow tree",
        roof=False,
        windbreak=False,
        cozy_line="Beneath the willow, the leaves whispered over them.",
        tags={"tree", "shelter"},
    ),
}

GIRL_NAMES = ["Moll", "Nan", "Bess", "Dot", "May", "Tess", "Nell", "Wren"]
BOY_NAMES = ["Pip", "Tom", "Ned", "Kit", "Jem", "Will", "Rob", "Ben"]


@dataclass
class StoryParams:
    place: str
    weather: str
    mistake: str
    shelter: str
    brave_name: str
    brave_gender: str
    worried_name: str
    worried_gender: str
    bravery: int = 6
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
    "shelter": [
        (
            "What is shelter?",
            "Shelter is a safe place that keeps you from rain, wind, or too much sun. A porch, shed, or gazebo can be shelter when the weather turns rough.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding is when someone thinks something means one thing, but it really means another. Looking closely and asking calmly can help fix it.",
        )
    ],
    "bravery": [
        (
            "What can bravery look like?",
            "Bravery does not always mean being loud or charging ahead. Sometimes it means taking one careful step, finding the truth, and helping someone else feel safe.",
        )
    ],
    "storm": [
        (
            "Why do people go inside or under a strong shelter in a storm?",
            "Storms can bring hard rain and pushing wind, so a good shelter keeps both off your body. A strong roof and walls help much more than standing under open branches.",
        )
    ],
    "rain": [
        (
            "Why is a roof helpful in rain?",
            "A roof catches the falling drops before they land on you. That helps people stay drier and warmer.",
        )
    ],
    "sheet": [
        (
            "Why can a sheet on a line look spooky?",
            "When cloth flaps and twists, it can change shape quickly. From far away, that can make it look like something it is not.",
        )
    ],
    "scarecrow": [
        (
            "What is a scarecrow?",
            "A scarecrow is a figure farmers put in a field to scare birds away. It may look person-shaped, but it is only cloth, straw, and sticks.",
        )
    ],
    "bush": [
        (
            "Why can a bush seem scary in the wind?",
            "Wind can shake branches in sudden ways and make shadows jump. If you are already worried, your eyes may guess the wrong thing at first.",
        )
    ],
}
KNOWLEDGE_ORDER = ["shelter", "misunderstanding", "bravery", "storm", "rain", "sheet", "scarecrow", "bush"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place_cfg"]
    weather = world.facts["weather_cfg"]
    mistake = world.facts["mistake_cfg"]
    shelter = world.facts["shelter_cfg"]
    brave = world.facts["brave"]
    worried = world.facts["worried"]
    return [
        (
            f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the word "shelter", '
            f'with a brave child helping a frightened friend in {place.label}.'
        ),
        (
            f"Tell a gentle rhyming story where {worried.id} misunderstands {mistake.phrase} during {weather.id}, "
            f"and {brave.id} kindly checks the truth before leading them to {shelter.phrase}."
        ),
        (
            "Write a small story about bravery and misunderstanding where the danger feels real at first, "
            "but turns out ordinary, and the ending shows the children dry and calm together."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    brave = world.facts["brave"]
    worried = world.facts["worried"]
    place = world.facts["place_cfg"]
    weather = world.facts["weather_cfg"]
    mistake = world.facts["mistake_cfg"]
    shelter = world.facts["shelter_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {brave.id} and {worried.id}, two children out in {place.label}. "
            f"When the weather changed, one child worried and the other chose to help.",
        ),
        (
            f"What did {worried.id} think {worried.pronoun()} saw?",
            f"{worried.id} thought {mistake.phrase} was {mistake.appears_as}. "
            f"That was the misunderstanding that made {worried.pronoun('object')} stop and feel afraid.",
        ),
        (
            f"How did {brave.id} show bravery?",
            f"{brave.id} did not laugh or run away. {brave.pronoun().capitalize()} went closer carefully, looked at the scary shape, and found out it was really {mistake.truth}.",
        ),
        (
            "How was the misunderstanding fixed?",
            f"It was fixed when the children looked more closely and learned the truth. "
            f"Once they understood the ordinary object, the fear had much less power.",
        ),
        (
            "Why did they need shelter?",
            f"They needed shelter because the {weather.id} was making the day wet"
            + (" and windy." if weather.needs_windbreak else ".")
            + f" {shelter.phrase.capitalize()} gave them a safe place to stand while the weather stayed outside.",
        ),
        (
            "How did the story end?",
            f"It ended with the children together in {shelter.phrase}, calmer than before. "
            f"The ending proves two changes at once: the fright was understood, and they had found real shelter.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    weather = world.facts["weather_cfg"]
    mistake = world.facts["mistake_cfg"]
    tags = {"shelter", "misunderstanding", "bravery"}
    if weather.id == "storm":
        tags.add("storm")
    else:
        tags.add("rain")
    tags.add(mistake.id)

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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in [
            ("ordinary", e.ordinary),
            ("open_top", e.open_top),
            ("windbreak", e.windbreak),
            ("hanging", e.hanging),
            ("rooted", e.rooted),
        ] if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="green",
        weather="rain",
        mistake="sheet",
        shelter="gazebo",
        brave_name="Pip",
        brave_gender="boy",
        worried_name="Moll",
        worried_gender="girl",
        bravery=6,
    ),
    StoryParams(
        place="farm",
        weather="storm",
        mistake="scarecrow",
        shelter="shed",
        brave_name="Nan",
        brave_gender="girl",
        worried_name="Kit",
        worried_gender="boy",
        bravery=7,
    ),
    StoryParams(
        place="garden",
        weather="storm",
        mistake="bush",
        shelter="porch",
        brave_name="Wren",
        brave_gender="girl",
        worried_name="Ben",
        worried_gender="boy",
        bravery=6,
    ),
    StoryParams(
        place="garden",
        weather="drizzle",
        mistake="sheet",
        shelter="porch",
        brave_name="Tom",
        brave_gender="boy",
        worried_name="May",
        worried_gender="girl",
        bravery=5,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "safe_and_clear" if params.bravery >= BRAVERY_MIN else "stuck"


ASP_RULES = r"""
place_allows(P,M,S) :- place_has_mistake(P,M), place_has_shelter(P,S).

mistake_matches(W,P,M) :- mistake(M),
                          requires_all_met(M,W),
                          place_tag_fit(M,P).

requires_all_met(M,W) :- not missing_req(M,W).
missing_req(M,W) :- needs_tag(M,T), not weather_tag(W,T).

place_tag_fit(M,P) :- not missing_place_tag(M,P).
missing_place_tag(M,P) :- place_needs(M,T), not place_tag(P,T).

shelter_ok(W,S) :- shelter(S),
                   roof_need_met(W,S),
                   wind_need_met(W,S).

roof_need_met(W,S) :- weather_needs_roof(W), shelter_roof(S).
roof_need_met(W,_) :- not weather_needs_roof(W).

wind_need_met(W,S) :- weather_needs_windbreak(W), shelter_windbreak(S).
wind_need_met(W,_) :- not weather_needs_windbreak(W).

valid(P,W,M,S) :- place(P), weather(W), mistake(M), shelter(S),
                  place_allows(P,M,S),
                  mistake_matches(W,P,M),
                  shelter_ok(W,S).

brave_enough :- bravery(B), bravery_min(M), B >= M.
outcome(safe_and_clear) :- brave_enough.
outcome(stuck) :- not brave_enough.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for mid in sorted(place.affords_mistakes):
            lines.append(asp.fact("place_has_mistake", pid, mid))
        for sid in sorted(place.affords_shelters):
            lines.append(asp.fact("place_has_shelter", pid, sid))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", pid, tag))

    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        if weather.needs_roof:
            lines.append(asp.fact("weather_needs_roof", wid))
        if weather.needs_windbreak:
            lines.append(asp.fact("weather_needs_windbreak", wid))
        for tag in sorted(weather.tags):
            lines.append(asp.fact("weather_tag", wid, tag))

    for mid, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", mid))
        for req in sorted(mistake.requires):
            lines.append(asp.fact("needs_tag", mid, req))
        for tag in sorted(mistake.place_tags):
            lines.append(asp.fact("place_needs", mid, tag))

    for sid, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", sid))
        if shelter.roof:
            lines.append(asp.fact("shelter_roof", sid))
        if shelter.windbreak:
            lines.append(asp.fact("shelter_windbreak", sid))

    lines.append(asp.fact("bravery_min", BRAVERY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("bravery", params.bravery)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme-style story world: a misunderstanding, a brave child, and shelter."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--brave-name")
    ap.add_argument("--worried-name")
    ap.add_argument("--brave-gender", choices=["girl", "boy"])
    ap.add_argument("--worried-gender", choices=["girl", "boy"])
    ap.add_argument("--bravery", type=int, choices=[5, 6, 7], help="how steady the brave child is")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.weather and args.mistake and args.shelter:
        place = PLACES[args.place]
        weather = WEATHERS[args.weather]
        mistake = MISTAKES[args.mistake]
        shelter = SHELTERS[args.shelter]
        if not (
            place_allows(place, mistake, shelter)
            and mistake_matches_weather(place, weather, mistake)
            and shelter_protects(weather, shelter)
        ):
            raise StoryError(explain_rejection(place, weather, mistake, shelter))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.weather is None or c[1] == args.weather)
        and (args.mistake is None or c[2] == args.mistake)
        and (args.shelter is None or c[3] == args.shelter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, weather, mistake, shelter = rng.choice(sorted(combos))
    brave_gender = args.brave_gender or rng.choice(["girl", "boy"])
    worried_gender = args.worried_gender or rng.choice(["girl", "boy"])
    brave_name = args.brave_name or _pick_name(rng, brave_gender)
    worried_name = args.worried_name or _pick_name(rng, worried_gender, avoid=brave_name)
    bravery = args.bravery if args.bravery is not None else rng.choice([5, 6, 7])

    return StoryParams(
        place=place,
        weather=weather,
        mistake=mistake,
        shelter=shelter,
        brave_name=brave_name,
        brave_gender=brave_gender,
        worried_name=worried_name,
        worried_gender=worried_gender,
        bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        weather = WEATHERS[params.weather]
        mistake = MISTAKES[params.mistake]
        shelter = SHELTERS[params.shelter]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]}.)") from err

    if not (
        place_allows(place, mistake, shelter)
        and mistake_matches_weather(place, weather, mistake)
        and shelter_protects(weather, shelter)
    ):
        raise StoryError(explain_rejection(place, weather, mistake, shelter))
    if params.bravery < BRAVERY_MIN:
        raise StoryError("(No story: the brave child must be brave enough to check kindly and lead the way.)")

    world = tell(
        place=place,
        weather=weather,
        mistake=mistake,
        shelter=shelter,
        brave_name=params.brave_name,
        brave_gender=params.brave_gender,
        worried_name=params.worried_name,
        worried_gender=params.worried_gender,
        bravery=params.bravery,
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

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid_combos parity matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolve failed for seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcome parity on {len(mismatches)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation and emit succeeded.")
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
        print(f"{len(combos)} valid (place, weather, mistake, shelter) combos:\n")
        for place, weather, mistake, shelter in combos:
            print(f"  {place:7} {weather:7} {mistake:10} {shelter}")
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
                f"### {p.brave_name} & {p.worried_name}: {p.mistake} in {p.weather} at "
                f"{p.place} -> {p.shelter}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
