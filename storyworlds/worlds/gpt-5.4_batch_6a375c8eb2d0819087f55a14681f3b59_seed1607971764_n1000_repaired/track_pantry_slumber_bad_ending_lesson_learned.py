#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/track_pantry_slumber_bad_ending_lesson_learned.py
=============================================================================

A standalone story world for a tiny superhero-flavored safety tale: a child
stays up too late pretending to be a night hero, then tries to race on a toy
track to reach the pantry for a secret snack. Because slumber was skipped, the
hero is too sleepy to steer well, crashes, and learns the hard way that real
heroes rest before they race.

The domain is intentionally small and constraint-checked. The world prefers
plausible pairings where the "rescue plan" does not actually prevent the crash;
this world is built around a bad ending with a lesson learned. The ending is
sad but child-safe: no severe injury, just a frightening tumble, a broken toy,
and a clear bedtime lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/track_pantry_slumber_bad_ending_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/track_pantry_slumber_bad_ending_lesson_learned.py --hero flashwing --vehicle scooter --goal pantry_cookie
    python storyworlds/worlds/gpt-5.4/track_pantry_slumber_bad_ending_lesson_learned.py --goal apple
    python storyworlds/worlds/gpt-5.4/track_pantry_slumber_bad_ending_lesson_learned.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/track_pantry_slumber_bad_ending_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4/track_pantry_slumber_bad_ending_lesson_learned.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    safe_for_sleepy: bool = False
    reachable_by_sleepy: bool = False
    breakable: bool = False
    food: bool = False
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
class HeroMode:
    id: str
    title: str
    boast: str
    motto: str
    landing: str
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
    lane: str
    sound: str
    speed: int
    safe_for_sleepy: bool
    breakable: bool
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
class Goal:
    id: str
    label: str
    phrase: str
    where: str
    pantry_item: bool
    food: bool
    reward: str
    healthy: bool
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
class AdultResponse:
    id: str
    sense: int
    text: str
    comfort: str
    lesson: str
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
class Risk:
    id: str
    label: str
    speed_need: int
    sleepy_need: int
    break_severity: int
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


def _r_sleepy_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    vehicle = world.get("vehicle")
    risk = world.get("risk")
    if hero.meters["sleepiness"] < risk.attrs["sleepy_need"]:
        return out
    if vehicle.attrs["speed"] < risk.attrs["speed_need"]:
        return out
    sig = ("wobble", hero.id, vehicle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["wobble"] += 1
    hero.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_wobble_crash(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    vehicle = world.get("vehicle")
    risk = world.get("risk")
    if hero.meters["wobble"] < THRESHOLD:
        return out
    sig = ("crash", hero.id, vehicle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["bruise"] += 1
    hero.meters["fallen"] += 1
    vehicle.meters["broken"] += risk.attrs["break_severity"]
    world.get("room").meters["mess"] += 1
    hero.memes["joy"] = 0.0
    hero.memes["regret"] += 1
    out.append("__crash__")
    return out


CAUSAL_RULES = [
    Rule(name="sleepy_wobble", tag="physical", apply=_r_sleepy_wobble),
    Rule(name="wobble_crash", tag="physical", apply=_r_wobble_crash),
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


def danger_possible(vehicle: Vehicle, risk: Risk) -> bool:
    return vehicle.speed >= risk.speed_need and risk.sleepy_need >= 2


def sensible_responses() -> list[AdultResponse]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def crash_happens(vehicle: Vehicle, risk: Risk, slumber_missed: bool) -> bool:
    if not slumber_missed:
        return False
    return danger_possible(vehicle, risk)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hero_id in HEROES:
        for vehicle_id, vehicle in VEHICLES.items():
            for goal_id in GOALS:
                if danger_possible(vehicle, RISKS["sleepy_track"]):
                    combos.append((hero_id, vehicle_id, goal_id))
    return combos


@dataclass
class StoryParams:
    hero: str
    vehicle: str
    goal: str
    response: str
    child_name: str
    child_gender: str
    parent: str
    bedtime_item: str = ""
    pet: str = ""
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


def introduce(world: World, hero_mode: HeroMode, child: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After sunset, {child.id} tied on a towel cape and became {hero_mode.title}. "
        f"{hero_mode.boast}"
    )
    world.say(
        f'"{hero_mode.motto}" {child.id} whispered, striking {hero_mode.landing}.'
    )


def miss_bedtime(world: World, child: Entity, parent: Entity) -> None:
    child.meters["sleepiness"] += 2
    child.memes["defiance"] += 1
    world.say(
        f"But when {child.id}'s {parent.label_word} said it was time for slumber, "
        f"{child.id} stayed up for one more secret mission."
    )
    item = child.attrs.get("bedtime_item")
    if item:
        world.say(
            f"{item.capitalize()} sat waiting on the pillow, but {child.id} hurried past it."
        )


def spot_goal(world: World, child: Entity, goal: Goal) -> None:
    child.memes["desire"] += 1
    world.say(
        f"From the hallway, {child.id} saw {goal.phrase} {goal.where}. "
        f"It looked like a prize for a hungry superhero."
    )


def build_track(world: World, child: Entity, vehicle: Vehicle) -> None:
    vehicle_ent = world.get("vehicle")
    vehicle_ent.meters["ready"] += 1
    world.say(
        f"Across the kitchen floor, foam blocks and books made a shiny track, "
        f"and {child.id} set {vehicle.phrase} at the start of {vehicle.lane}."
    )
    world.say(
        f'"{vehicle.sound}!" {child.id} said. "This hero will zoom to the pantry before anyone notices."'
    )


def warn(world: World, child: Entity, parent: Entity, vehicle: Vehicle, risk: Risk, goal: Goal) -> None:
    pred = predict_crash(world)
    world.facts["predicted_crash"] = pred["crash"]
    world.facts["predicted_break"] = pred["broken"]
    target = "the pantry" if goal.pantry_item else "the kitchen shelf"
    world.say(
        f'{parent.label_word.capitalize()} peeked around the corner. '
        f'"Night heroes still need slumber," {parent.pronoun()} said. '
        f'"If you race {vehicle.label} when you are sleepy, you can wobble on the track before you even reach {target}."'
    )


def defy(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But {child.id} lifted {child.pronoun('possessive')} chin. "
        f'"A real superhero can do one more mission," {child.pronoun()} insisted.'
    )


def ride(world: World, child: Entity, vehicle: Vehicle) -> None:
    world.get("vehicle").meters["moving"] += 1
    world.say(
        f"{child.id} pushed off hard, and the {vehicle.label} flew down the track."
    )
    propagate(world, narrate=False)
    if child.meters["wobble"] >= THRESHOLD:
        world.say(
            f"At first it felt fast and grand. Then sleepy eyes blinked, the front wheel twitched, "
            f"and the whole ride began to sway."
        )


def crash(world: World, child: Entity, vehicle: Vehicle, goal: Goal) -> None:
    if child.meters["fallen"] < THRESHOLD:
        return
    pantry_line = (
        "The pantry door stayed closed, and the secret snack mission was over before it began."
        if goal.pantry_item else
        "The little prize on the shelf was forgotten at once."
    )
    world.say(
        f"With a clatter, {child.id} spilled off the {vehicle.label}. {pantry_line}"
    )
    if world.get("vehicle").meters["broken"] >= THRESHOLD:
        world.say(
            f"One wheel bent sideways, and the brave-looking machine suddenly looked small and broken."
        )


def comfort_and_lesson(world: World, child: Entity, parent: Entity, response: AdultResponse) -> None:
    child.memes["love"] += 1
    child.memes["shame"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried over, checked the little bruise, and {response.comfort}."
    )
    world.say(
        f'{response.text} "{response.lesson}"'
    )


def ending(world: World, child: Entity, vehicle: Vehicle, pet: str) -> None:
    extra = ""
    if pet:
        extra = f" Even {pet} stayed quiet beside the wall."
    world.say(
        f"That night, {child.id} climbed into bed much earlier than before.{extra} "
        f"The broken {vehicle.label} waited by the door, and it reminded {child.pronoun('object')} that tired heroes make poor choices."
    )


def tell(
    hero_mode: HeroMode,
    vehicle: Vehicle,
    goal: Goal,
    response: AdultResponse,
    child_name: str = "Milo",
    child_gender: str = "boy",
    parent_type: str = "mother",
    bedtime_item: str = "",
    pet: str = "",
) -> World:
    world = World()
    child = world.add(Entity(
        id="hero",
        kind="character",
        type=child_gender,
        label=child_name,
        role="hero",
        attrs={"bedtime_item": bedtime_item, "pet": pet},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(id="room", type="room", label="kitchen"))
    vehicle_ent = world.add(Entity(
        id="vehicle",
        type="vehicle",
        label=vehicle.label,
        safe_for_sleepy=vehicle.safe_for_sleepy,
        breakable=vehicle.breakable,
        attrs={"speed": vehicle.speed},
    ))
    risk_ent = world.add(Entity(
        id="risk",
        type="risk",
        label="sleepy track danger",
        attrs={
            "speed_need": RISKS["sleepy_track"].speed_need,
            "sleepy_need": RISKS["sleepy_track"].sleepy_need,
            "break_severity": RISKS["sleepy_track"].break_severity,
        },
    ))
    goal_ent = world.add(Entity(
        id="goal",
        type="goal",
        label=goal.label,
        reachable_by_sleepy=goal.healthy,
        food=goal.food,
    ))

    child.id = child_name
    world.entities["hero"] = world.entities.pop("hero")
    world.entities[child_name] = world.entities.pop("hero")
    # restore stable ids for rule helpers
    world.entities["hero"] = child
    del world.entities[child_name]
    child.id = child_name
    parent.id = "Parent"
    world.entities["parent"] = world.entities.pop("parent")
    world.entities["Parent"] = world.entities.pop("parent")
    parent.id = "Parent"
    world.entities["parent"] = parent

    # Initialize all rule-read values before any propagation.
    child.meters["sleepiness"] = 0.0
    child.meters["wobble"] = 0.0
    child.meters["fallen"] = 0.0
    child.meters["bruise"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["regret"] = 0.0
    child.memes["joy"] = 0.0
    vehicle_ent.meters["broken"] = 0.0
    room.meters["mess"] = 0.0

    introduce(world, hero_mode, child)
    world.para()
    miss_bedtime(world, child, parent)
    spot_goal(world, child, goal)
    build_track(world, child, vehicle)
    warn(world, child, parent, vehicle, RISKS["sleepy_track"], goal)
    defy(world, child)

    world.para()
    ride(world, child, vehicle)
    crash(world, child, vehicle, goal)

    world.para()
    comfort_and_lesson(world, child, parent, response)
    ending(world, child, vehicle, pet)

    world.facts.update(
        hero=child,
        parent=parent,
        hero_mode=hero_mode,
        vehicle_cfg=vehicle,
        goal_cfg=goal,
        response=response,
        risk=RISKS["sleepy_track"],
        pet=pet,
        bedtime_item=bedtime_item,
        crashed=child.meters["fallen"] >= THRESHOLD,
        broken=vehicle_ent.meters["broken"] >= THRESHOLD,
        bruised=child.meters["bruise"] >= THRESHOLD,
        outcome="bad_ending_lesson",
    )
    return world


def predict_crash(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    sim.get("vehicle").meters["moving"] += 1
    propagate(sim, narrate=False)
    return {
        "crash": hero.meters["fallen"] >= THRESHOLD,
        "broken": sim.get("vehicle").meters["broken"],
    }


HEROES = {
    "flashwing": HeroMode(
        id="flashwing",
        title="Flashwing",
        boast="In the dark window glass, the cape looked like real hero fire.",
        motto="Flashwing never quits a mission",
        landing="a shadowy pose by the couch",
        tags={"superhero"},
    ),
    "moonbolt": HeroMode(
        id="moonbolt",
        title="Moonbolt",
        boast="The silver spoon on the table gleamed like a hero badge.",
        motto="Moonbolt guards the house at midnight",
        landing="a moon-still pose near the chair",
        tags={"superhero"},
    ),
    "captain_comet": HeroMode(
        id="captain_comet",
        title="Captain Comet",
        boast="Every hallway light stripe looked like a secret launch path.",
        motto="Captain Comet always answers a call",
        landing="a rocket pose with one hand high",
        tags={"superhero"},
    ),
}

VEHICLES = {
    "scooter": Vehicle(
        id="scooter",
        label="scooter",
        phrase="the red scooter",
        lane="the fastest lane",
        sound="Zip-zip",
        speed=3,
        safe_for_sleepy=False,
        breakable=True,
        tags={"wheel", "speed"},
    ),
    "skateboard": Vehicle(
        id="skateboard",
        label="skateboard",
        phrase="the wobbling skateboard",
        lane="the narrow center lane",
        sound="Rrrr-zoom",
        speed=3,
        safe_for_sleepy=False,
        breakable=True,
        tags={"wheel", "speed"},
    ),
    "ride_car": Vehicle(
        id="ride_car",
        label="ride-on car",
        phrase="the little ride-on car",
        lane="the long blue lane",
        sound="Vroom",
        speed=2,
        safe_for_sleepy=False,
        breakable=True,
        tags={"wheel", "speed"},
    ),
}

GOALS = {
    "pantry_cookie": Goal(
        id="pantry_cookie",
        label="cookie box",
        phrase="a bright cookie box",
        where="inside the pantry",
        pantry_item=True,
        food=True,
        reward="a sweet secret crunch",
        healthy=False,
        tags={"pantry", "snack"},
    ),
    "pantry_crackers": Goal(
        id="pantry_crackers",
        label="cracker box",
        phrase="a box of crackers",
        where="inside the pantry",
        pantry_item=True,
        food=True,
        reward="a salty bedtime nibble",
        healthy=True,
        tags={"pantry", "snack"},
    ),
    "apple": Goal(
        id="apple",
        label="apple",
        phrase="a shiny apple",
        where="on the low kitchen shelf",
        pantry_item=False,
        food=True,
        reward="a crisp bite",
        healthy=True,
        tags={"fruit", "snack"},
    ),
}

RISKS = {
    "sleepy_track": Risk(
        id="sleepy_track",
        label="sleepy track crash",
        speed_need=2,
        sleepy_need=2,
        break_severity=1,
        tags={"sleep", "track"},
    )
}

RESPONSES = {
    "carry_to_bed": AdultResponse(
        id="carry_to_bed",
        sense=3,
        text="Then Mom gathered the cape, lifted the tired little hero up, and spoke softly.",
        comfort="kissed the top of the child's head and rubbed the shaky shoulder",
        lesson="Even superheroes need slumber before they try big, fast missions.",
        qa_text="carried the child to bed after checking the bruise",
        tags={"bedtime", "comfort"},
    ),
    "ice_and_bed": AdultResponse(
        id="ice_and_bed",
        sense=3,
        text="Then Dad set a cool cloth on the bruise and tucked the cape under one arm.",
        comfort="held the child close until the crying turned into sniffles",
        lesson="A tired body cannot steer well, and bedtime is part of being strong tomorrow.",
        qa_text="used a cool cloth and then took the child to bed",
        tags={"bedtime", "comfort"},
    ),
    "scold_only": AdultResponse(
        id="scold_only",
        sense=1,
        text="Then the grown-up only frowned from far away.",
        comfort="did not kneel down first",
        lesson="You should have listened.",
        qa_text="only scolded from across the room",
        tags={"bad_response"},
    ),
}

GIRL_NAMES = ["Lia", "Maya", "Nora", "Ruby", "Ava", "Ella", "Mina"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Sam", "Eli", "Noah", "Leo"]
BEDTIME_ITEMS = ["sleepy rabbit", "little moon blanket", "star pillow", ""]
PETS = ["the cat", "the puppy", "their goldfish", ""]


KNOWLEDGE = {
    "sleep": [(
        "Why do children need sleep?",
        "Sleep helps bodies and brains rest, grow, and work well the next day. When someone is very tired, it is harder to think clearly and move safely."
    )],
    "track": [(
        "What is a track?",
        "A track is a path or lane that something follows as it moves. Toy cars, scooters, and runners can all use a track."
    )],
    "pantry": [(
        "What is a pantry?",
        "A pantry is a place where a family keeps food, snacks, and kitchen supplies. It is often a cupboard or a small closet near the kitchen."
    )],
    "bruise": [(
        "What is a bruise?",
        "A bruise is a sore spot that can happen after a bump or fall. It usually gets better with rest and gentle care."
    )],
    "bedtime": [(
        "Why does bedtime matter?",
        "Bedtime gives your body a regular chance to rest. Good bedtime habits help you feel calmer, steadier, and safer."
    )],
}
KNOWLEDGE_ORDER = ["sleep", "track", "pantry", "bruise", "bedtime"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["hero"]
    hero_mode = f["hero_mode"]
    vehicle = f["vehicle_cfg"]
    goal = f["goal_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "track", "pantry", and "slumber".',
        f"Tell a cautionary story where {child.id} pretends to be {hero_mode.title}, skips slumber, races a {vehicle.label} on a track, and learns a lesson after a bad ending.",
        f"Write a child-facing story in a superhero style where a secret trip toward {goal.where} goes wrong because the hero is too sleepy."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["hero"]
    parent = f["parent"]
    hero_mode = f["hero_mode"]
    vehicle = f["vehicle_cfg"]
    goal = f["goal_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who pretended to be {hero_mode.title}, and {child.id}'s {parent.label_word} who helped after the crash."
        ),
        (
            "Why was the child riding on the track?",
            f"{child.id} wanted to do one more secret superhero mission and reach {goal.phrase} {goal.where}. The track made the trip feel fast and daring."
        ),
        (
            "What mistake did the child make before the ride?",
            f"{child.id} skipped slumber and stayed up when bedtime had already come. That choice made {child.pronoun('object')} too sleepy for a quick mission."
        ),
        (
            "What went wrong on the track?",
            f"{child.id} became wobbly while riding the {vehicle.label} and crashed before reaching the goal. The fall happened because tired eyes and a fast ride do not work well together."
        ),
        (
            "What was the bad ending?",
            f"The secret mission failed, the {vehicle.label} was damaged, and {child.id} got a small bruise. It was frightening enough to stop the game and show that the warning had been true."
        ),
        (
            f"How did {child.id}'s {parent.label_word} help?",
            f"{parent.label_word.capitalize()} {response.qa_text}. After helping with the hurt feelings and the sore spot, {parent.pronoun()} turned the accident into a calm lesson."
        ),
        (
            "What lesson did the child learn?",
            f"{child.id} learned that real heroes need slumber before they try speedy stunts. Rest is part of being safe, not something brave people can skip."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sleep", "track", "bruise", "bedtime"}
    if world.facts["goal_cfg"].pantry_item:
        tags.add("pantry")
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


CURATED = [
    StoryParams(
        hero="flashwing",
        vehicle="scooter",
        goal="pantry_cookie",
        response="carry_to_bed",
        child_name="Milo",
        child_gender="boy",
        parent="mother",
        bedtime_item="star pillow",
        pet="the cat",
    ),
    StoryParams(
        hero="moonbolt",
        vehicle="skateboard",
        goal="pantry_crackers",
        response="ice_and_bed",
        child_name="Ruby",
        child_gender="girl",
        parent="father",
        bedtime_item="sleepy rabbit",
        pet="the puppy",
    ),
    StoryParams(
        hero="captain_comet",
        vehicle="ride_car",
        goal="apple",
        response="carry_to_bed",
        child_name="Theo",
        child_gender="boy",
        parent="mother",
        bedtime_item="little moon blanket",
        pet="",
    ),
]


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo(vehicle: Vehicle, risk: Risk) -> str:
    return (
        f"(No story: a {vehicle.label} is too slow or too steady to make the sleepy track crash matter here. "
        f"Pick a faster ride like {', '.join(sorted(VEHICLES))}.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). "
        f"Try one of: {good}.)"
    )


ASP_RULES = r"""
hero_choice(H) :- hero(H).
vehicle_choice(V) :- vehicle(V).
goal_choice(G) :- goal(G).

danger(V) :- vehicle(V), speed(V,S), risk_speed_need(R), S >= R.
valid(H,V,G) :- hero(H), vehicle(V), goal(G), danger(V).

slumber_missed.
crash :- chosen_vehicle(V), danger(V), slumber_missed.
outcome(bad_ending_lesson) :- crash.

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for vid, vehicle in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        lines.append(asp.fact("speed", vid, vehicle.speed))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
    lines.append(asp.fact("risk_speed_need", RISKS["sleepy_track"].speed_need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    extra = "\n".join([
        asp.fact("chosen_vehicle", params.vehicle),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    return "bad_ending_lesson" if crash_happens(VEHICLES[params.vehicle], RISKS["sleepy_track"], True) else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a sleepy superhero, a track, and a hard bedtime lesson."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vehicle:
        if not danger_possible(VEHICLES[args.vehicle], RISKS["sleepy_track"]):
            raise StoryError(explain_combo(VEHICLES[args.vehicle], RISKS["sleepy_track"]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.hero is None or c[0] == args.hero)
        and (args.vehicle is None or c[1] == args.vehicle)
        and (args.goal is None or c[2] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero, vehicle, goal = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    bedtime_item = rng.choice(BEDTIME_ITEMS)
    pet = rng.choice(PETS)
    return StoryParams(
        hero=hero,
        vehicle=vehicle,
        goal=goal,
        response=response,
        child_name=name,
        child_gender=gender,
        parent=parent,
        bedtime_item=bedtime_item,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (("hero", HEROES), ("vehicle", VEHICLES), ("goal", GOALS), ("response", RESPONSES)):
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(Unknown {key}: {value})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not danger_possible(VEHICLES[params.vehicle], RISKS["sleepy_track"]):
        raise StoryError(explain_combo(VEHICLES[params.vehicle], RISKS["sleepy_track"]))

    world = tell(
        hero_mode=HEROES[params.hero],
        vehicle=VEHICLES[params.vehicle],
        goal=GOALS[params.goal],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        bedtime_item=params.bedtime_item,
        pet=params.pet,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(py_set - asp_set))
        print("  only in clingo:", sorted(asp_set - py_set))

    py_sense = {r.id for r in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sense == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sense)} clingo={sorted(asp_sense)}")

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Failed to resolve params at seed {seed}.")
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print(f"MISMATCH outcome for {p}: asp={asp_outcome(p)} python={outcome_of(p)}")
            break

    # smoke test normal generation / emit
    try:
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, vehicle, goal) combos:\n")
        for hero, vehicle, goal in combos:
            print(f"  {hero:14} {vehicle:10} {goal}")
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
            header = f"### {p.child_name}: {p.hero}, {p.vehicle}, {p.goal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
