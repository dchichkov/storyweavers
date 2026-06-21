#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shear_foreshadowing_bedtime_story.py
===============================================================

A standalone storyworld for a gentle bedtime tale about a child who remembers a
freshly shorn farm animal just as the night begins to turn cold. The story is
state-driven: an afternoon shear leaves the animal more vulnerable, evening
signs foreshadow trouble, and a caring grown-up helps the child make the stall
snug before sleep.

Run it
------
    python storyworlds/worlds/gpt-5.4/shear_foreshadowing_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/shear_foreshadowing_bedtime_story.py --animal lamb --weather windy --shelter loft_window --comfort inner_stall
    python storyworlds/worlds/gpt-5.4/shear_foreshadowing_bedtime_story.py --comfort humming
    python storyworlds/worlds/gpt-5.4/shear_foreshadowing_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/shear_foreshadowing_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/shear_foreshadowing_bedtime_story.py --verify
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
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
class AnimalCfg:
    id: str
    species: str
    name: str
    coat: str
    voice: str
    vulnerability: int
    bundle: str
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
    sign: str
    sky: str
    sound: str
    chill: int
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
    draft: int
    flaw: str
    place_line: str
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
class Comfort:
    id: str
    sense: int
    power: int
    seals_draft: bool
    name: str
    action: str
    ending: str
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


def _r_chill(world: World) -> list[str]:
    animal = world.get("animal")
    child = world.get("child")
    barn = world.get("barn")
    if animal.meters["night"] < THRESHOLD:
        return []
    if animal.meters["cover"] >= animal.meters["risk"]:
        return []
    sig = ("chill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["cold"] += 1
    animal.memes["unease"] += 1
    child.memes["worry"] += 1
    barn.meters["draft_feels_real"] += 1
    return ["__chill__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="chill", tag="physical", apply=_r_chill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ANIMALS = {
    "lamb": AnimalCfg(
        id="lamb",
        species="lamb",
        name="Mallow",
        coat="spring wool",
        voice="bleat",
        vulnerability=1,
        bundle="a little round bundle",
        tags={"lamb", "wool"},
    ),
    "sheep": AnimalCfg(
        id="sheep",
        species="sheep",
        name="Cloud",
        coat="thick fleece",
        voice="maa",
        vulnerability=1,
        bundle="a soft pearly pile",
        tags={"sheep", "wool"},
    ),
    "alpaca": AnimalCfg(
        id="alpaca",
        species="alpaca",
        name="Tansy",
        coat="fluffy coat",
        voice="hum",
        vulnerability=2,
        bundle="a silky cloud of fiber",
        tags={"alpaca", "wool"},
    ),
}

WEATHERS = {
    "breeze": Weather(
        id="breeze",
        sign="the weather vane gave one small squeak",
        sky="the moon climbed through a thin silver cloud",
        sound="the grass whispered against the fence",
        chill=1,
        tags={"weather_vane", "night_air"},
    ),
    "windy": Weather(
        id="windy",
        sign="the weather vane squeaked again and again",
        sky="clouds brushed over the moon in slow gray strips",
        sound="the leaves hissed along the yard",
        chill=2,
        tags={"weather_vane", "night_air", "wind"},
    ),
    "misty": Weather(
        id="misty",
        sign="a cool mist curled low over the path",
        sky="the moon looked soft behind a pale white veil",
        sound="the damp air made every board seem to sigh",
        chill=2,
        tags={"mist", "night_air"},
    ),
}

SHELTERS = {
    "half_latch": Shelter(
        id="half_latch",
        label="the little side stall",
        draft=1,
        flaw="the side door had not caught all the way",
        place_line="The stall stood nearest the yard, where night air could peep in.",
        tags={"barn", "door"},
    ),
    "loft_window": Shelter(
        id="loft_window",
        label="the loft stall",
        draft=2,
        flaw="the loft window had been left a finger-width open",
        place_line="High above, a narrow window looked straight at the dark field.",
        tags={"barn", "window"},
    ),
    "corner_pen": Shelter(
        id="corner_pen",
        label="the corner pen",
        draft=1,
        flaw="one corner board had a slim crack between the planks",
        place_line="The pen was cozy by day, but a night breeze could still find that crack.",
        tags={"barn", "boards"},
    ),
}

COMFORTS = {
    "quilt": Comfort(
        id="quilt",
        sense=2,
        power=3,
        seals_draft=False,
        name="tiny quilt",
        action="lifted a tiny quilt from a peg and draped it over the animal's bare back",
        ending="under the little quilt, the animal looked tucked in for a story of its own",
        qa_text="covered the animal with a tiny quilt",
        tags={"quilt"},
    ),
    "straw_nest": Comfort(
        id="straw_nest",
        sense=2,
        power=3,
        seals_draft=False,
        name="fresh straw nest",
        action="banked fresh straw all around the animal until only a sleepy nose and ears showed",
        ending="nestled in the straw, the animal looked like a warm moon-colored muffin",
        qa_text="banked fresh straw around the animal like a nest",
        tags={"straw"},
    ),
    "shutter_and_straw": Comfort(
        id="shutter_and_straw",
        sense=3,
        power=4,
        seals_draft=True,
        name="closed shutter and straw",
        action="closed the opening against the wind and piled fresh straw in a deep ring around the animal",
        ending="with the draft shut out and the straw all around, the stall held its warmth like cupped hands",
        qa_text="shut out the draft and piled fresh straw around the animal",
        tags={"straw", "shutter"},
    ),
    "inner_stall": Comfort(
        id="inner_stall",
        sense=3,
        power=4,
        seals_draft=True,
        name="inner stall",
        action="led the animal to the inner stall, where the air stayed still, and laid down clean straw there",
        ending="safe in the inner stall, the animal folded down as if the whole barn had whispered good night",
        qa_text="moved the animal to the inner stall and made a warm bed there",
        tags={"straw", "barn"},
    ),
    "humming": Comfort(
        id="humming",
        sense=1,
        power=0,
        seals_draft=False,
        name="humming only",
        action="hummed a sweet little tune beside the stall",
        ending="the tune was kind, but it could not stop the cold air",
        qa_text="only hummed a tune",
        tags={"song"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ella", "Ava", "Ruby", "Ivy", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Leo", "Finn", "Owen", "Max", "Eli"]
TRAITS = ["gentle", "careful", "sleepy", "thoughtful", "quiet", "kind"]


def effective_cover(comfort: Comfort, shelter: Shelter) -> int:
    bonus = shelter.draft if comfort.seals_draft else 0
    return comfort.power + bonus


def total_risk(animal: AnimalCfg, weather: Weather, shelter: Shelter) -> int:
    return animal.vulnerability + weather.chill + shelter.draft


def comfort_works(animal: AnimalCfg, weather: Weather, shelter: Shelter, comfort: Comfort) -> bool:
    return comfort.sense >= SENSE_MIN and effective_cover(comfort, shelter) >= total_risk(animal, weather, shelter)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for animal_id, animal in ANIMALS.items():
        for weather_id, weather in WEATHERS.items():
            for shelter_id, shelter in SHELTERS.items():
                for comfort_id, comfort in COMFORTS.items():
                    if comfort_works(animal, weather, shelter, comfort):
                        combos.append((animal_id, weather_id, shelter_id, comfort_id))
    return combos


@dataclass
class StoryParams:
    animal: str
    weather: str
    shelter: str
    comfort: str
    child: str
    gender: str
    caregiver: str
    trait: str
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
    "shear": [
        (
            "What is a shear?",
            "A shear is a cutting tool grown-ups use to trim wool from animals like sheep or alpacas. It must be used gently and carefully.",
        )
    ],
    "wool": [
        (
            "Why does wool keep an animal warm?",
            "Wool traps little pockets of air close to the body. That helps hold warmth in when the air turns cool.",
        )
    ],
    "lamb": [
        (
            "What is a lamb?",
            "A lamb is a young sheep. Lambs are smaller than grown sheep and can get chilly more quickly.",
        )
    ],
    "alpaca": [
        (
            "What is an alpaca?",
            "An alpaca is a gentle farm animal with soft fiber. People sometimes shear alpacas to trim that warm coat.",
        )
    ],
    "straw": [
        (
            "Why does straw make a warm bed?",
            "Straw lifts an animal up off the cold floor and holds dry air around it. That makes a nest that feels warmer.",
        )
    ],
    "shutter": [
        (
            "Why does closing a window or door help at night?",
            "Closing an opening stops cold air from slipping in. When the draft goes away, it is easier to stay warm.",
        )
    ],
    "barn": [
        (
            "What is a barn for?",
            "A barn is a farm building where animals and supplies can stay sheltered. It helps keep them dry and safer from wind.",
        )
    ],
    "weather_vane": [
        (
            "What does a weather vane show?",
            "A weather vane moves with the wind. If it starts squeaking and turning, that can be a sign the air is getting lively.",
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a thin cloud close to the ground made of tiny drops of water. It can make the air feel cooler and damper.",
        )
    ],
    "night_air": [
        (
            "Why can the air feel colder at night?",
            "After the sun goes down, the ground and air lose warmth. That is why a place can feel much cooler at bedtime than it did in the afternoon.",
        )
    ],
}
KNOWLEDGE_ORDER = ["shear", "wool", "lamb", "alpaca", "straw", "shutter", "barn", "weather_vane", "mist", "night_air"]


def require_choice(table: dict, key: str, field_name: str):
    try:
        return table[key]
    except KeyError as exc:
        raise StoryError(f"(Unknown {field_name}: {key})") from exc


def intro(world: World, child: Entity, caregiver: Entity, animal_cfg: AnimalCfg) -> None:
    animal = world.get("animal")
    child.memes["tenderness"] += 1
    world.say(
        f"At the edge of the little farm, {child.id} was getting ready for bed when "
        f"{child.pronoun('possessive')} {caregiver.label_word} carried in one last basket from the barn."
    )
    world.say(
        f"That afternoon, {caregiver.label_word.capitalize()} had used a gentle shear to trim "
        f"{animal.id}'s {animal_cfg.coat} into {animal_cfg.bundle}. The day had been warm, and "
        f"{animal.id} had seemed light and pleased without all that fluff."
    )


def foreshadow(world: World, child: Entity, weather: Weather, shelter: Shelter) -> None:
    world.say(
        f"But as the house grew dim and sleepy, {weather.sign}, and {weather.sky}. "
        f"Outside, {weather.sound}."
    )
    world.say(
        f"{child.id} paused with one foot already turned toward the stairs. "
        f"{child.pronoun().capitalize()} remembered that in the barn, {shelter.flaw}."
    )


def night_turn(world: World, child: Entity, animal_cfg: AnimalCfg, weather: Weather, shelter: Shelter) -> None:
    animal = world.get("animal")
    barn = world.get("barn")
    animal.meters["night"] = 1.0
    animal.meters["risk"] = float(total_risk(animal_cfg, weather, shelter))
    animal.meters["cover"] = 0.0
    barn.meters["draft"] = float(shelter.draft)
    barn.meters["chill"] = float(weather.chill)
    propagate(world, narrate=False)
    world.say(
        f'"Wait," {child.id} whispered. "After the shear, {animal.id} has less wool tonight."'
    )
    world.say(
        f"{child.id} could almost feel the cold path the air might take through {shelter.label}. "
        f"The thought made bedtime seem less soft than a moment before."
    )


def check_barn(world: World, child: Entity, caregiver: Entity, shelter: Shelter) -> None:
    animal = world.get("animal")
    world.say(
        f"{caregiver.label_word.capitalize()} did not laugh. "
        f"{caregiver.pronoun().capitalize()} took {child.id}'s hand, and together they walked to the barn with a lantern glow sliding over the boards."
    )
    world.say(
        f"Inside {shelter.label}, {shelter.place_line} {animal.id} stood very still for a moment, then tucked in close and gave a small {animal.attrs['voice']}."
    )


def fix_problem(world: World, child: Entity, caregiver: Entity, comfort: Comfort, shelter: Shelter) -> None:
    animal = world.get("animal")
    cover = effective_cover(comfort, shelter)
    animal.meters["cover"] = float(cover)
    if comfort.seals_draft:
        world.get("barn").meters["draft"] = 0.0
    if animal.meters["cover"] >= animal.meters["risk"]:
        animal.meters["cold"] = 0.0
        animal.meters["cozy"] = 1.0
        animal.memes["unease"] = 0.0
        animal.memes["calm"] += 1
        child.memes["worry"] = 0.0
        child.memes["relief"] += 1
        child.memes["sleepiness"] += 1
        caregiver.memes["care"] += 1
    world.say(
        f"{caregiver.label_word.capitalize()} {comfort.action}. "
        f'"There now," {caregiver.pronoun()} murmured. "Warm first, sleep after."'
    )
    world.say(
        f"Soon {animal.id} let out a slower breath and sank down. {comfort.ending}."
    )


def return_to_bed(world: World, child: Entity, caregiver: Entity, weather: Weather) -> None:
    animal = world.get("animal")
    world.say(
        f"{child.id} listened for one more moment and heard no restless stamping now, only the soft sound of {animal.id} settling into the straw."
    )
    world.say(
        f"Back in bed, with {weather.sky.lower()} outside the window, {child.id} tucked the blanket under {child.pronoun('possessive')} chin and closed {child.pronoun('possessive')} eyes. "
        f"It was easier to sleep when the barn sounded peaceful too."
    )


def tell(
    animal_cfg: AnimalCfg,
    weather: Weather,
    shelter: Shelter,
    comfort: Comfort,
    child_name: str,
    child_gender: str,
    caregiver_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
        )
    )
    caregiver = world.add(
        Entity(
            id="Caregiver",
            kind="character",
            type=caregiver_type,
            role="caregiver",
            label="the caregiver",
        )
    )
    animal = world.add(
        Entity(
            id=animal_cfg.name,
            kind="character",
            type=animal_cfg.species,
            role="animal",
            label=animal_cfg.species,
            attrs={"voice": animal_cfg.voice},
        )
    )
    barn = world.add(
        Entity(
            id="barn",
            kind="thing",
            type="barn",
            label=shelter.label,
        )
    )

    child.memes["worry"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["sleepiness"] = 0.0
    caregiver.memes["care"] = 0.0
    animal.meters["risk"] = 0.0
    animal.meters["cover"] = 0.0
    animal.meters["cold"] = 0.0
    animal.meters["night"] = 0.0
    animal.meters["cozy"] = 0.0
    barn.meters["draft"] = 0.0
    barn.meters["chill"] = 0.0

    intro(world, child, caregiver, animal_cfg)
    world.para()
    foreshadow(world, child, weather, shelter)
    night_turn(world, child, animal_cfg, weather, shelter)
    world.para()
    check_barn(world, child, caregiver, shelter)
    fix_problem(world, child, caregiver, comfort, shelter)
    world.para()
    return_to_bed(world, child, caregiver, weather)

    world.facts.update(
        child=child,
        caregiver=caregiver,
        animal=animal,
        animal_cfg=animal_cfg,
        weather=weather,
        shelter=shelter,
        comfort=comfort,
        risk=total_risk(animal_cfg, weather, shelter),
        effective=effective_cover(comfort, shelter),
        foreshadow_sign=weather.sign,
        draft_flaw=shelter.flaw,
        cozy=animal.meters["cozy"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    animal_cfg = f["animal_cfg"]
    weather = f["weather"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "shear" and uses foreshadowing.',
        f"Tell a gentle nighttime farm story where {child.id} remembers that {animal_cfg.name} was shorn earlier and notices a sign that the air is turning cold.",
        f"Write a soft, reassuring story in which {child.id} and {child.pronoun('possessive')} {caregiver.label_word} make a freshly shorn {animal_cfg.species} warm before sleep, using {weather.sign} as foreshadowing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    animal = f["animal"]
    animal_cfg = f["animal_cfg"]
    weather = f["weather"]
    shelter = f["shelter"]
    comfort = f["comfort"]
    risk = f["risk"]
    effective = f["effective"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {caregiver.label_word}, and {animal.id} the {animal_cfg.species}. The story happens at bedtime on their little farm.",
        ),
        (
            f"Why did {child.id} start to worry?",
            f"{child.id} remembered that {animal.id} had been shorn with a gentle shear that afternoon, so there was less warm wool to hold the heat in. Then {weather.sign}, which made {child.pronoun('object')} think the night air might feel cold in {shelter.label}.",
        ),
        (
            "What was the foreshadowing sign?",
            f"The foreshadowing sign was that {weather.sign}. It hinted that the air was changing before anyone went back to the barn.",
        ),
        (
            f"How did they help {animal.id}?",
            f"{caregiver.label_word.capitalize()} {comfort.qa_text}. That worked because the help gave {animal.id} more warmth than the chilly, drafty stall could take away.",
        ),
        (
            "How did the story end?",
            f"It ended peacefully, with {animal.id} settled and cozy in the barn. Because the worry was answered with a real fix, {child.id} could go back to bed and sleep softly.",
        ),
    ]
    if risk > 0:
        out.append(
            (
                f"Why was {comfort.name} a good idea?",
                f"The night risk was {risk} altogether, coming from the fresh shear, the weather, and the draft in the shelter. The chosen comfort covered that need with {effective} points of warmth, so it truly matched the problem instead of only sounding nice.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"shear"} | set(f["animal_cfg"].tags) | set(f["weather"].tags) | set(f["shelter"].tags) | set(f["comfort"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="lamb",
        weather="breeze",
        shelter="half_latch",
        comfort="quilt",
        child="Nora",
        gender="girl",
        caregiver="grandmother",
        trait="thoughtful",
        seed=1,
    ),
    StoryParams(
        animal="sheep",
        weather="windy",
        shelter="loft_window",
        comfort="inner_stall",
        child="Ben",
        gender="boy",
        caregiver="grandpa",
        trait="careful",
        seed=2,
    ),
    StoryParams(
        animal="alpaca",
        weather="misty",
        shelter="corner_pen",
        comfort="shutter_and_straw",
        child="Mia",
        gender="girl",
        caregiver="grandmother",
        trait="gentle",
        seed=3,
    ),
    StoryParams(
        animal="lamb",
        weather="windy",
        shelter="corner_pen",
        comfort="shutter_and_straw",
        child="Theo",
        gender="boy",
        caregiver="grandpa",
        trait="quiet",
        seed=4,
    ),
    StoryParams(
        animal="sheep",
        weather="breeze",
        shelter="half_latch",
        comfort="straw_nest",
        child="Ivy",
        gender="girl",
        caregiver="grandmother",
        trait="sleepy",
        seed=5,
    ),
]


def explain_comfort_rejection(animal: AnimalCfg, weather: Weather, shelter: Shelter, comfort: Comfort) -> str:
    if comfort.sense < SENSE_MIN:
        return (
            f"(Refusing comfort '{comfort.id}': it is kind but not practical enough for this world. "
            f"A bedtime fix must truly warm the animal, not only sound sweet.)"
        )
    risk = total_risk(animal, weather, shelter)
    eff = effective_cover(comfort, shelter)
    return (
        f"(No story: {comfort.name} is too weak here. The night risk is {risk}, but that comfort only gives {eff}, "
        f"so the freshly shorn animal would still be cold.)"
    )


ASP_RULES = r"""
sensible(C) :- comfort(C), sense(C,S), sense_min(M), S >= M.

risk(A,W,S, V + Ch + Dr) :-
    animal(A), vulnerability(A,V),
    weather(W), chill(W,Ch),
    shelter(S), draft(S,Dr).

effective(C,S, P + Dr) :-
    comfort(C), power(C,P), seals_draft(C),
    shelter(S), draft(S,Dr).

effective(C,S, P) :-
    comfort(C), power(C,P), not seals_draft(C),
    shelter(S).

valid(A,W,S,C) :-
    sensible(C),
    risk(A,W,S,R),
    effective(C,S,E),
    E >= R.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("vulnerability", animal_id, animal.vulnerability))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("chill", weather_id, weather.chill))
    for shelter_id, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", shelter_id))
        lines.append(asp.fact("draft", shelter_id, shelter.draft))
    for comfort_id, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", comfort_id))
        lines.append(asp.fact("sense", comfort_id, comfort.sense))
        lines.append(asp.fact("power", comfort_id, comfort.power))
        if comfort.seals_draft:
            lines.append(asp.fact("seals_draft", comfort_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_comforts() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime farm storyworld about a fresh shear, foreshadowing, and making a stall snug for the night."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.comfort is not None and args.comfort in COMFORTS and COMFORTS[args.comfort].sense < SENSE_MIN:
        if args.animal and args.weather and args.shelter:
            raise StoryError(
                explain_comfort_rejection(
                    require_choice(ANIMALS, args.animal, "animal"),
                    require_choice(WEATHERS, args.weather, "weather"),
                    require_choice(SHELTERS, args.shelter, "shelter"),
                    require_choice(COMFORTS, args.comfort, "comfort"),
                )
            )
        raise StoryError(
            f"(Refusing comfort '{args.comfort}': it is kind but not practical enough for this world.)"
        )

    combos = [
        combo
        for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.weather is None or combo[1] == args.weather)
        and (args.shelter is None or combo[2] == args.shelter)
        and (args.comfort is None or combo[3] == args.comfort)
    ]

    if not combos:
        if args.animal and args.weather and args.shelter and args.comfort:
            raise StoryError(
                explain_comfort_rejection(
                    require_choice(ANIMALS, args.animal, "animal"),
                    require_choice(WEATHERS, args.weather, "weather"),
                    require_choice(SHELTERS, args.shelter, "shelter"),
                    require_choice(COMFORTS, args.comfort, "comfort"),
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    animal, weather, shelter, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        animal=animal,
        weather=weather,
        shelter=shelter,
        comfort=comfort,
        child=child,
        gender=gender,
        caregiver=caregiver,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    animal_cfg = require_choice(ANIMALS, params.animal, "animal")
    weather = require_choice(WEATHERS, params.weather, "weather")
    shelter = require_choice(SHELTERS, params.shelter, "shelter")
    comfort = require_choice(COMFORTS, params.comfort, "comfort")

    if not comfort_works(animal_cfg, weather, shelter, comfort):
        raise StoryError(explain_comfort_rejection(animal_cfg, weather, shelter, comfort))

    world = tell(
        animal_cfg=animal_cfg,
        weather=weather,
        shelter=shelter,
        comfort=comfort,
        child_name=params.child,
        child_gender=params.gender,
        caregiver_type=params.caregiver,
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

    clingo_sense = set(asp_sensible_comforts())
    python_sense = {cid for cid, comfort in COMFORTS.items() if comfort.sense >= SENSE_MIN}
    if clingo_sense == python_sense:
        print(f"OK: sensible comforts match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible comforts: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    smoke_cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        try:
            ns = parser.parse_args([])
            params = resolve_params(ns, random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"SMOKE MISMATCH: default resolve_params failed for seed {seed}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            with io.StringIO() as buf, redirect_stdout(buf):
                emit(sample, trace=False, qa=(i == 1), header="" if i != 1 else "### smoke")
        except Exception as exc:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE FAIL on case {i}: {params} -> {exc}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show sensible/1.\n#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible_comforts()
        print(f"sensible comforts: {', '.join(sensible)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, weather, shelter, comfort) combos:\n")
        for animal, weather, shelter, comfort in combos:
            print(f"  {animal:7} {weather:7} {shelter:11} {comfort}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.child}: {p.animal}, {p.weather}, {p.shelter}, {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
