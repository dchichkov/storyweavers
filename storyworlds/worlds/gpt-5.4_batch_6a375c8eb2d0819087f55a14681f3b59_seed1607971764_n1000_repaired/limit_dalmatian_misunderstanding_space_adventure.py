#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/limit_dalmatian_misunderstanding_space_adventure.py
================================================================================

A standalone storyworld about a backyard-style space adventure driven by a
misunderstanding of the word "limit".

The core story shape is:

- a child and a family dalmatian prepare a pretend space mission
- a posted payload/seat limit makes the child think the dalmatian is being
  rejected from the adventure
- a calm grown-up explains that a limit is about weight and room, not love
- the mission is reorganized in a way that really fits the craft
- the ending image proves the dalmatian still belongs in the adventure

Run it
------
    python storyworlds/worlds/gpt-5.4/limit_dalmatian_misunderstanding_space_adventure.py
    python storyworlds/worlds/gpt-5.4/limit_dalmatian_misunderstanding_space_adventure.py --craft moon_buggy --cargo beacon --plan ground_control
    python storyworlds/worlds/gpt-5.4/limit_dalmatian_misunderstanding_space_adventure.py --craft star_scooter --cargo crate --plan dog_ride
    python storyworlds/worlds/gpt-5.4/limit_dalmatian_misunderstanding_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/limit_dalmatian_misunderstanding_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/limit_dalmatian_misunderstanding_space_adventure.py --verify
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

CHILD_WEIGHT = 2
DALMATIAN_WEIGHT = 2


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
class Mission:
    id: str
    place: str
    destination: str
    danger: str
    sparkle: str
    ending: str
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
class CraftConfig:
    id: str
    label: str
    seat_limit: int
    payload_limit: int
    launch_line: str
    motion: str
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
class CargoConfig:
    id: str
    label: str
    phrase: str
    weight: int
    purpose: str
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
class PlanConfig:
    id: str
    label: str
    dog_role: str
    summary: str
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


def _r_over_limit(world: World) -> list[str]:
    craft = world.get("craft")
    payload = craft.meters["payload"]
    riders = craft.meters["riders"]
    payload_limit = craft.attrs["payload_limit"]
    seat_limit = craft.attrs["seat_limit"]
    if payload <= payload_limit and riders <= seat_limit:
        return []
    sig = ("over_limit", int(payload), int(riders))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    craft.meters["unsafe"] += 1
    world.get("hero").memes["worry"] += 1
    return ["__over_limit__"]


def _r_misunderstood(world: World) -> list[str]:
    hero = world.get("hero")
    dog = world.get("dog")
    if world.facts.get("misunderstanding") != "dog_excluded":
        return []
    sig = ("misunderstood",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["sadness"] += 1
    dog.memes["confusion"] += 1
    return ["__misunderstood__"]


def _r_belonging_restored(world: World) -> list[str]:
    hero = world.get("hero")
    dog = world.get("dog")
    if not world.facts.get("clarified"):
        return []
    if not world.facts.get("plan_valid"):
        return []
    sig = ("belonging_restored", world.facts.get("plan"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    dog.memes["belonging"] += 1
    return ["__belonging__"]


CAUSAL_RULES = [
    Rule(name="over_limit", tag="physical", apply=_r_over_limit),
    Rule(name="misunderstood", tag="emotional", apply=_r_misunderstood),
    Rule(name="belonging_restored", tag="emotional", apply=_r_belonging_restored),
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


MISSIONS = {
    "moon": Mission(
        id="moon",
        place="the backyard launch pad",
        destination="the moon",
        danger="a silver ring of dust",
        sparkle="stars made tiny pinholes in the dark blue sky-cloth above the fence",
        ending="their moon mission felt bigger because everyone had a job",
        tags={"moon", "space"},
    ),
    "mars": Mission(
        id="mars",
        place="the driveway spaceport",
        destination="Mars",
        danger="a field of red pebbles",
        sparkle="the evening clouds glowed like a red planet beyond the rooftops",
        ending="their Mars mission ended with dusty shoes and shining smiles",
        tags={"mars", "space"},
    ),
    "comet": Mission(
        id="comet",
        place="the playroom command deck",
        destination="the comet trail",
        danger="a ribbon of icy light",
        sparkle="paper stars swung over the room like a turning galaxy",
        ending="their comet mission whooshed on with laughter and blinking lights",
        tags={"comet", "space"},
    ),
}

CRAFTS = {
    "star_scooter": CraftConfig(
        id="star_scooter",
        label="star scooter",
        seat_limit=1,
        payload_limit=3,
        launch_line="A taped sign on the side said: PAYLOAD LIMIT 3 UNITS. ONE RIDER.",
        motion="zipped over the paving stones like a tiny rocket skimming space",
        tags={"small_craft", "limit"},
    ),
    "moon_buggy": CraftConfig(
        id="moon_buggy",
        label="moon buggy",
        seat_limit=2,
        payload_limit=4,
        launch_line="A marker sign by the handle said: PAYLOAD LIMIT 4 UNITS. TWO RIDERS.",
        motion="rolled between flowerpots as if it were crossing a crater plain",
        tags={"rover", "limit"},
    ),
    "comet_cart": CraftConfig(
        id="comet_cart",
        label="comet cart",
        seat_limit=2,
        payload_limit=5,
        launch_line="A paper dashboard note said: PAYLOAD LIMIT 5 UNITS. TWO RIDERS.",
        motion="glided across the floor with the grand hush of a ship between stars",
        tags={"cart", "limit"},
    ),
}

CARGO = {
    "beacon": CargoConfig(
        id="beacon",
        label="beacon",
        phrase="a blinking beacon box",
        weight=1,
        purpose="plant a blinking beacon",
        tags={"beacon", "light"},
    ),
    "snack_pack": CargoConfig(
        id="snack_pack",
        label="snack pack",
        phrase="a silver snack pack",
        weight=1,
        purpose="carry space snacks for the long trip",
        tags={"snack", "supplies"},
    ),
    "crate": CargoConfig(
        id="crate",
        label="meteor crate",
        phrase="a heavy meteor crate",
        weight=2,
        purpose="deliver a crate of pretend meteor samples",
        tags={"crate", "cargo"},
    ),
}

PLANS = {
    "ground_control": PlanConfig(
        id="ground_control",
        label="ground control",
        dog_role="ground control chief",
        summary="The dalmatian stays on the launch pad with the radio and guides the mission.",
        tags={"radio", "teamwork"},
    ),
    "dog_ride": PlanConfig(
        id="dog_ride",
        label="dog ride",
        dog_role="co-pilot",
        summary="The cargo stays behind so the dalmatian can ride beside the child.",
        tags={"teamwork", "co_pilot"},
    ),
    "two_trips": PlanConfig(
        id="two_trips",
        label="two trips",
        dog_role="second-trip co-pilot",
        summary="The child makes one cargo trip and one trip with the dalmatian.",
        tags={"teamwork", "taking_turns"},
    ),
}

GIRL_NAMES = ["Luna", "Maya", "Zoe", "Ava", "Nora", "Ivy", "Lucy", "Mila"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Noah", "Sam", "Jack"]
TRAITS = ["eager", "curious", "brave", "careful", "dreamy", "clever"]


def wanted_payload(cargo_id: str) -> int:
    return CHILD_WEIGHT + DALMATIAN_WEIGHT + CARGO[cargo_id].weight


def wanted_riders() -> int:
    return 2


def plan_works(plan_id: str, craft_id: str, cargo_id: str) -> bool:
    craft = CRAFTS[craft_id]
    cargo = CARGO[cargo_id]
    if plan_id == "ground_control":
        return craft.seat_limit >= 1 and CHILD_WEIGHT + cargo.weight <= craft.payload_limit
    if plan_id == "dog_ride":
        return craft.seat_limit >= 2 and CHILD_WEIGHT + DALMATIAN_WEIGHT <= craft.payload_limit
    if plan_id == "two_trips":
        cargo_trip = craft.seat_limit >= 1 and CHILD_WEIGHT + cargo.weight <= craft.payload_limit
        dog_trip = craft.seat_limit >= 2 and CHILD_WEIGHT + DALMATIAN_WEIGHT <= craft.payload_limit
        return cargo_trip and dog_trip
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for craft_id in CRAFTS:
            for cargo_id in CARGO:
                initial_too_full = (
                    wanted_payload(cargo_id) > CRAFTS[craft_id].payload_limit
                    or wanted_riders() > CRAFTS[craft_id].seat_limit
                )
                if not initial_too_full:
                    continue
                for plan_id in PLANS:
                    if plan_works(plan_id, craft_id, cargo_id):
                        combos.append((mission_id, craft_id, cargo_id, plan_id))
    return combos


def explain_plan_rejection(plan_id: str, craft_id: str, cargo_id: str) -> str:
    craft = CRAFTS[craft_id]
    cargo = CARGO[cargo_id]
    if plan_id == "ground_control":
        return (
            f"(No story: if the dalmatian stays on the ground, the child and "
            f"the {cargo.label} still do not fit the {craft.label}'s limit. "
            f"Pick a lighter cargo or a stronger craft.)"
        )
    if plan_id == "dog_ride":
        return (
            f"(No story: leaving the {cargo.label} behind is not enough, because "
            f"the child and dalmatian still do not fit the {craft.label}'s seat "
            f"or payload limit together.)"
        )
    return (
        f"(No story: the {craft.label} cannot handle both the cargo trip and the "
        f"dalmatian trip within its limit, so two trips would not really solve the problem.)"
    )


def explain_combo_rejection(craft_id: str, cargo_id: str) -> str:
    craft = CRAFTS[craft_id]
    cargo = CARGO[cargo_id]
    return (
        f"(No misunderstanding story here: the child, the dalmatian, and the "
        f"{cargo.label} already fit the {craft.label}'s limit, so there is no real "
        f"space-adventure problem to solve.)"
    )


def board(world: World, *, hero_on: bool, dog_on: bool, cargo_on: bool) -> None:
    craft = world.get("craft")
    craft.meters["payload"] = 0.0
    craft.meters["riders"] = 0.0
    if hero_on:
        craft.meters["payload"] += float(CHILD_WEIGHT)
        craft.meters["riders"] += 1.0
    if dog_on:
        craft.meters["payload"] += float(DALMATIAN_WEIGHT)
        craft.meters["riders"] += 1.0
    if cargo_on:
        craft.meters["payload"] += float(world.get("cargo").attrs["weight"])
    propagate(world, narrate=False)


def predict_over_limit(world: World) -> dict:
    sim = world.copy()
    board(sim, hero_on=True, dog_on=True, cargo_on=True)
    craft = sim.get("craft")
    return {
        "payload": int(craft.meters["payload"]),
        "riders": int(craft.meters["riders"]),
        "unsafe": craft.meters["unsafe"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, dog: Entity, mission: Mission, craft: CraftConfig, cargo: CargoConfig) -> None:
    world.say(
        f"{hero.id} spent the afternoon in {mission.place}, turning a little wagon and a cardboard box into a {craft.label}. "
        f"{mission.sparkle}"
    )
    world.say(
        f"Beside {hero.pronoun('object')} trotted {dog.attrs['name']}, the family dalmatian, wearing a shiny scarf and carrying {cargo.phrase}. "
        f"Tonight's mission was to {cargo.purpose} on {mission.destination}."
    )


def launch_dream(world: World, hero: Entity, dog: Entity, craft: CraftConfig) -> None:
    hero.memes["joy"] += 1
    dog.memes["joy"] += 1
    world.say(
        f'"Commander {hero.id} and Scout {dog.attrs["name"]}!" {hero.id} said. '
        f'"Ready for launch?" The dalmatian answered with a happy bark and put both front paws on the rim of the {craft.label}.'
    )


def notice_limit(world: World, craft: CraftConfig) -> None:
    world.say(craft.launch_line)


def misunderstand(world: World, hero: Entity, dog: Entity, craft: CraftConfig, cargo: CargoConfig, parent: Entity) -> None:
    pred = predict_over_limit(world)
    world.facts["predicted_payload"] = pred["payload"]
    world.facts["predicted_riders"] = pred["riders"]
    world.facts["misunderstanding"] = "dog_excluded"
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} read the sign, looked at the dalmatian, and froze. "
        f'"Oh," {hero.pronoun()} whispered. "The limit means {dog.attrs["name"]} cannot be part of the mission."'
    )
    world.say(
        f"{dog.attrs['name']} tilted {dog.pronoun('possessive')} spotted head, and even {parent.label_word} could see {hero.id}'s face fall. "
        f"{hero.pronoun().capitalize()} had mixed up a weight-and-room rule with a rule about who was allowed to belong."
    )


def explain(world: World, parent: Entity, hero: Entity, dog: Entity, craft: CraftConfig) -> None:
    craft_ent = world.get("craft")
    world.facts["clarified"] = True
    world.facts["misunderstanding"] = ""
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} knelt beside the {craft.label} and touched the sign. "
        f'"Sweetheart, limit does not mean "{dog.attrs["name"]} is not wanted,"" {parent.pronoun()} said gently. '
        f'"It means this little ship can only carry so much weight and only so many riders at one time."'
    )
    world.say(
        f'"See? The ship can hold {craft_ent.attrs["payload_limit"]} units and {craft_ent.attrs["seat_limit"]} rider'
        f'{"s" if craft_ent.attrs["seat_limit"] != 1 else ""}. '
        f'You, the cargo, and the dalmatian together make {wanted_payload(world.get("cargo").attrs["cargo_id"])} units."'
    )


def choose_plan(world: World, hero: Entity, dog: Entity, craft: CraftConfig, cargo: CargoConfig, plan: PlanConfig, parent: Entity) -> None:
    world.facts["plan"] = plan.id
    world.facts["plan_valid"] = plan_works(plan.id, craft.id, cargo.id)
    propagate(world, narrate=False)
    if plan.id == "ground_control":
        world.say(
            f'{parent.label_word.capitalize()} smiled. "Then we change the jobs, not the love. '
            f'{dog.attrs["name"]} can be {plan.dog_role}, and you can fly the {cargo.label} up first."'
        )
        hero.attrs["dog_role"] = plan.dog_role
        dog.attrs["mission_role"] = plan.dog_role
    elif plan.id == "dog_ride":
        world.say(
            f'{parent.label_word.capitalize()} smiled. "Then we leave the {cargo.label} here for now. '
            f'{dog.attrs["name"]} can ride as your {plan.dog_role}, and the mission can be about mapping, not hauling."'
        )
        hero.attrs["dog_role"] = plan.dog_role
        dog.attrs["mission_role"] = plan.dog_role
    else:
        world.say(
            f'{parent.label_word.capitalize()} traced two little paths in the dust. "Then we split the mission in two. '
            f'First you take the {cargo.label}. After that, you and {dog.attrs["name"]} make a second lap together."'
        )
        hero.attrs["dog_role"] = plan.dog_role
        dog.attrs["mission_role"] = plan.dog_role


def execute_plan(world: World, hero: Entity, dog: Entity, craft: CraftConfig, cargo: CargoConfig, plan: PlanConfig, mission: Mission) -> None:
    if plan.id == "ground_control":
        board(world, hero_on=True, dog_on=False, cargo_on=True)
        dog.attrs["location"] = "launch pad"
        dog.attrs["radio"] = True
        world.say(
            f"{dog.attrs['name']} stayed on the launch pad beside a toy radio, ears up, while {hero.id} climbed in with the {cargo.label}. "
            f"When the wheels began to move, the dalmatian barked into the pretend microphone as if sending brave signals into space."
        )
        world.say(
            f"The {craft.label} {craft.motion}. {hero.id} delivered the cargo past {mission.danger}, then looked back to see {dog.attrs['name']} dancing in a circle below."
        )
    elif plan.id == "dog_ride":
        board(world, hero_on=True, dog_on=True, cargo_on=False)
        dog.attrs["location"] = "craft"
        world.say(
            f"{hero.id} set the {cargo.label} beside the launch chalk, and {dog.attrs['name']} hopped into the {craft.label} instead. "
            f"The dalmatian sat very straight, a proud little {plan.dog_role}, while the mission changed from hauling cargo to scouting stars."
        )
        world.say(
            f"Together they {craft.motion}. Every time the ship bumped, {dog.attrs['name']}'s black spots flashed like tiny moving constellations."
        )
    else:
        board(world, hero_on=True, dog_on=False, cargo_on=True)
        world.say(
            f"On the first trip, {hero.id} carried the {cargo.label} alone and steered through the pretend asteroids. "
            f"Then the child pilot hurried back to the launch line, cheeks glowing."
        )
        board(world, hero_on=True, dog_on=True, cargo_on=False)
        dog.attrs["location"] = "craft"
        world.say(
            f"On the second trip, the cargo stayed home and {dog.attrs['name']} jumped aboard as {plan.dog_role}. "
            f"This time the ship felt lighter, swifter, and full of happy barking."
        )


def ending(world: World, hero: Entity, dog: Entity, mission: Mission, plan: PlanConfig, parent: Entity) -> None:
    hero.memes["lesson"] += 1
    dog.memes["joy"] += 1
    world.say(
        f"By the end, {hero.id} understood that a limit was only a way to keep a ship safe. "
        f"It was not a way to measure friendship."
    )
    if plan.id == "ground_control":
        world.say(
            f"{hero.id} saluted the launch pad and called, \"Ground Control, report!\" "
            f"{dog.attrs['name']} gave one bright bark, and {parent.label_word} laughed. "
            f"{mission.ending}."
        )
    elif plan.id == "dog_ride":
        world.say(
            f"When they rolled to a stop, {hero.id} wrapped both arms around the dalmatian's spotted neck. "
            f'"Best co-pilot in the whole sky," {hero.pronoun()} said. '
            f"{mission.ending}."
        )
    else:
        world.say(
            f"After the second trip, {hero.id} drew two shining loops in the dust to remember both parts of the journey. "
            f"One loop was for the cargo, and one was for the dalmatian. {mission.ending}."
        )


def tell(
    mission: Mission,
    craft_cfg: CraftConfig,
    cargo_cfg: CargoConfig,
    plan_cfg: PlanConfig,
    *,
    hero_name: str = "Luna",
    hero_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "curious",
    dog_name: str = "Pepper",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    dog = world.add(
        Entity(
            id="dog",
            kind="character",
            type="animal",
            label="dalmatian",
            role="dog",
            attrs={"name": dog_name, "weight": DALMATIAN_WEIGHT, "radio": False, "mission_role": ""},
        )
    )
    craft = world.add(
        Entity(
            id="craft",
            type="craft",
            label=craft_cfg.label,
            attrs={"seat_limit": craft_cfg.seat_limit, "payload_limit": craft_cfg.payload_limit, "craft_id": craft_cfg.id},
        )
    )
    cargo = world.add(
        Entity(
            id="cargo",
            type="cargo",
            label=cargo_cfg.label,
            attrs={"weight": cargo_cfg.weight, "cargo_id": cargo_cfg.id},
        )
    )

    world.facts.update(
        mission=mission,
        craft_cfg=craft_cfg,
        cargo_cfg=cargo_cfg,
        plan_cfg=plan_cfg,
        hero=hero,
        parent=parent,
        dog=dog,
        craft=craft,
        cargo=cargo,
        misunderstanding="",
        clarified=False,
        plan="",
        plan_valid=False,
    )

    introduce(world, hero, dog, mission, craft_cfg, cargo_cfg)
    launch_dream(world, hero, dog, craft_cfg)

    world.para()
    notice_limit(world, craft_cfg)
    misunderstand(world, hero, dog, craft_cfg, cargo_cfg, parent)
    explain(world, parent, hero, dog, craft_cfg)
    choose_plan(world, hero, dog, craft_cfg, cargo_cfg, plan_cfg, parent)

    world.para()
    execute_plan(world, hero, dog, craft_cfg, cargo_cfg, plan_cfg, mission)
    ending(world, hero, dog, mission, plan_cfg, parent)

    world.facts.update(
        outcome="resolved",
        safe_payload=int(world.get("craft").meters["payload"]),
        safe_riders=int(world.get("craft").meters["riders"]),
        unsafe_initial=wanted_payload(cargo_cfg.id) > craft_cfg.payload_limit or wanted_riders() > craft_cfg.seat_limit,
    )
    return world


@dataclass
class StoryParams:
    mission: str
    craft: str
    cargo: str
    plan: str
    name: str
    gender: str
    parent: str
    trait: str
    dog_name: str = "Pepper"
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


KNOWLEDGE = {
    "limit": [
        (
            "What does a limit mean?",
            "A limit is a rule about how much or how many something can safely hold. It is there to keep people and things safe, not to hurt anyone's feelings.",
        )
    ],
    "dalmatian": [
        (
            "What is a dalmatian?",
            "A dalmatian is a kind of dog with black or brown spots on its coat. Many children notice dalmatians quickly because their spots are easy to see.",
        )
    ],
    "radio": [
        (
            "What does ground control do?",
            "Ground control stays off the ship and helps guide the mission. They watch carefully and send messages so the traveler knows what to do next.",
        )
    ],
    "payload": [
        (
            "What is payload in a space adventure?",
            "Payload means the things a ship is carrying, like tools, supplies, or cargo. If the payload is too heavy, the ship may not work safely.",
        )
    ],
    "rover": [
        (
            "What is a rover?",
            "A rover is a vehicle made to roll over rough ground. In space stories, a rover helps explorers cross dusty places like the moon or Mars.",
        )
    ],
    "taking_turns": [
        (
            "Why can taking turns solve a problem?",
            "Taking turns can make a hard problem smaller, because not everything has to happen at once. One safe trip now can be better than one overloaded trip.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means different helpers doing different jobs for the same goal. A mission can go better when everyone has a part to play.",
        )
    ],
}

KNOWLEDGE_ORDER = ["limit", "dalmatian", "payload", "radio", "rover", "taking_turns", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    mission = world.facts["mission"]
    craft = world.facts["craft_cfg"]
    cargo = world.facts["cargo_cfg"]
    hero = world.facts["hero"]
    dog = world.facts["dog"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "limit" and "dalmatian".',
        f"Tell a gentle story where {hero.id} thinks a posted limit means {dog.attrs['name']} the dalmatian is not allowed on the mission, but a grown-up explains the misunderstanding and helps save the adventure.",
        f"Write a child-facing space story about a small {craft.label}, a misunderstood safety rule, and a plan to {cargo.purpose} on {mission.destination}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    dog = world.facts["dog"]
    craft = world.facts["craft_cfg"]
    cargo = world.facts["cargo_cfg"]
    mission = world.facts["mission"]
    plan = world.facts["plan_cfg"]
    pred_payload = world.facts.get("predicted_payload", 0)
    pred_riders = world.facts.get("predicted_riders", 0)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child playing a space adventure, and {dog.attrs['name']}, the family dalmatian. {parent.label_word.capitalize()} also helps when the mission starts to feel confusing.",
        ),
        (
            "What mission were they pretending to do?",
            f"They were pretending to travel to {mission.destination} in a {craft.label}. The goal was to {cargo.purpose}.",
        ),
        (
            "What did the word limit make the child think?",
            f"{hero.id} thought the word limit meant {dog.attrs['name']} was not allowed to belong in the mission at all. That misunderstanding made the child sad because the dalmatian was supposed to be part of the team.",
        ),
        (
            "What did the grown-up explain about the limit sign?",
            f"{parent.label_word.capitalize()} explained that the sign was about safety, weight, and room, not about love. The ship could only hold {craft.payload_limit} units and {craft.seat_limit} rider"
            f'{"s" if craft.seat_limit != 1 else ""}, while the child, dalmatian, and cargo together made {pred_payload} units and {pred_riders} riders.',
        ),
    ]
    if plan.id == "ground_control":
        qa.append(
            (
                f"How did they solve the problem without leaving the dalmatian out?",
                f"They made {dog.attrs['name']} the ground control chief while {hero.id} took the cargo trip. The dalmatian still had an important job, because the new plan changed the roles instead of pushing a friend away.",
            )
        )
    elif plan.id == "dog_ride":
        qa.append(
            (
                f"How did the dalmatian stay part of the mission?",
                f"They left the cargo behind and let {dog.attrs['name']} ride as co-pilot. That worked because the smaller load fit the craft's limit, so the ship could be safe and the dalmatian could still belong.",
            )
        )
    else:
        qa.append(
            (
                "Why were two trips a good answer?",
                f"Two trips made each ride small enough to fit the limit. First {hero.id} took the cargo, and later the dalmatian got a second trip as co-pilot, so both jobs could happen safely.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the misunderstanding cleared up and the mission going forward safely. By the end, {hero.id} knew a limit was for safety, not for measuring friendship.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    craft = world.facts["craft_cfg"]
    plan = world.facts["plan_cfg"]
    tags = {"limit", "dalmatian", "payload", "teamwork"}
    if "rover" in craft.tags:
        tags.add("rover")
    if plan.id == "ground_control":
        tags.add("radio")
    if plan.id == "two_trips":
        tags.add("taking_turns")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or isinstance(v, (int, float))}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="moon",
        craft="moon_buggy",
        cargo="beacon",
        plan="ground_control",
        name="Luna",
        gender="girl",
        parent="mother",
        trait="curious",
        dog_name="Pepper",
    ),
    StoryParams(
        mission="mars",
        craft="comet_cart",
        cargo="crate",
        plan="dog_ride",
        name="Max",
        gender="boy",
        parent="father",
        trait="brave",
        dog_name="Pepper",
    ),
    StoryParams(
        mission="comet",
        craft="moon_buggy",
        cargo="crate",
        plan="two_trips",
        name="Maya",
        gender="girl",
        parent="mother",
        trait="clever",
        dog_name="Orbit",
    ),
    StoryParams(
        mission="moon",
        craft="star_scooter",
        cargo="beacon",
        plan="ground_control",
        name="Theo",
        gender="boy",
        parent="father",
        trait="dreamy",
        dog_name="Dot",
    ),
]


ASP_RULES = r"""
% Initial tension exists only when the desired load is too large for the craft.
wanted_payload(C, W + 4) :- cargo(C), cargo_weight(C, W).
wanted_riders(2).

too_full(Craft, Cargo) :- craft(Craft), cargo(Cargo),
                          wanted_payload(Cargo, P), payload_limit(Craft, L), P > L.
too_full(Craft, Cargo) :- craft(Craft), cargo(Cargo),
                          wanted_riders(R), seat_limit(Craft, S), R > S.

works(ground_control, Craft, Cargo) :- craft(Craft), cargo(Cargo),
                                       payload_limit(Craft, L), cargo_weight(Cargo, W), 2 + W <= L,
                                       seat_limit(Craft, S), S >= 1.

works(dog_ride, Craft, Cargo) :- craft(Craft), cargo(Cargo),
                                 payload_limit(Craft, L), 4 <= L,
                                 seat_limit(Craft, S), S >= 2.

works(two_trips, Craft, Cargo) :- works(ground_control, Craft, Cargo),
                                  works(dog_ride, Craft, Cargo).

valid(Mission, Craft, Cargo, Plan) :- mission(Mission), craft(Craft), cargo(Cargo), plan(Plan),
                                      too_full(Craft, Cargo), works(Plan, Craft, Cargo).

outcome(resolved) :- chosen_plan(P), chosen_craft(C), chosen_cargo(G), works(P, C, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for craft_id, craft in CRAFTS.items():
        lines.append(asp.fact("craft", craft_id))
        lines.append(asp.fact("payload_limit", craft_id, craft.payload_limit))
        lines.append(asp.fact("seat_limit", craft_id, craft.seat_limit))
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("cargo_weight", cargo_id, cargo.weight))
    for plan_id in PLANS:
        lines.append(asp.fact("plan", plan_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_plan", params.plan),
            asp.fact("chosen_craft", params.craft),
            asp.fact("chosen_cargo", params.cargo),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a small space adventure built around a misunderstanding of a safety limit."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--dog-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible generation")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.craft and args.cargo:
        initial_too_full = (
            wanted_payload(args.cargo) > CRAFTS[args.craft].payload_limit
            or wanted_riders() > CRAFTS[args.craft].seat_limit
        )
        if not initial_too_full:
            raise StoryError(explain_combo_rejection(args.craft, args.cargo))
    if args.plan and args.craft and args.cargo and not plan_works(args.plan, args.craft, args.cargo):
        raise StoryError(explain_plan_rejection(args.plan, args.craft, args.cargo))

    combos = [
        c
        for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.craft is None or c[1] == args.craft)
        and (args.cargo is None or c[2] == args.cargo)
        and (args.plan is None or c[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, craft_id, cargo_id, plan_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    dog_name = args.dog_name or rng.choice(["Pepper", "Dot", "Comet", "Patches"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        mission=mission_id,
        craft=craft_id,
        cargo=cargo_id,
        plan=plan_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        dog_name=dog_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.craft not in CRAFTS:
        raise StoryError(f"(Unknown craft: {params.craft})")
    if params.cargo not in CARGO:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    initial_too_full = (
        wanted_payload(params.cargo) > CRAFTS[params.craft].payload_limit
        or wanted_riders() > CRAFTS[params.craft].seat_limit
    )
    if not initial_too_full:
        raise StoryError(explain_combo_rejection(params.craft, params.cargo))
    if not plan_works(params.plan, params.craft, params.cargo):
        raise StoryError(explain_plan_rejection(params.plan, params.craft, params.cargo))

    world = tell(
        MISSIONS[params.mission],
        CRAFTS[params.craft],
        CARGO[params.cargo],
        PLANS[params.plan],
        hero_name=params.name,
        hero_gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
        dog_name=params.dog_name,
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed at seed {seed}")
            break

    outcome_bad = 0
    for params in cases:
        if asp_outcome(params) != "resolved":
            outcome_bad += 1
    if outcome_bad == 0:
        print(f"OK: ASP outcome model resolves all {len(cases)} checked scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {outcome_bad}/{len(cases)} outcomes were not resolved in ASP.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
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
        print(f"{len(combos)} compatible (mission, craft, cargo, plan) combos:\n")
        for mission_id, craft_id, cargo_id, plan_id in combos:
            print(f"  {mission_id:7} {craft_id:13} {cargo_id:10} {plan_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.mission} / {p.craft} / {p.cargo} / {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
