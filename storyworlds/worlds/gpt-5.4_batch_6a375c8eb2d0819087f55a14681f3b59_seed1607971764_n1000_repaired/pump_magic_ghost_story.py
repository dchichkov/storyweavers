#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pump_magic_ghost_story.py
====================================================

A standalone story world for a gentle ghost story with an old pump, a thirsty
magical plant, and a child who learns that spooky sounds can hide a kind reason.

The world model is small and classical:
- an old hand pump at night
- a magical plant that must be watered before moonrise
- a garden ghost who cannot manage the heavy iron handle alone
- a child whose fear or courage changes what happens next

The reasonableness gate is simple and explicit:
- the place must actually be a place where the chosen magical plant can grow
- the chosen primer must really hold water, because an old pump needs a splash
  of water to prime it before it can pull fresh water up

Run it
------
python storyworlds/worlds/gpt-5.4/pump_magic_ghost_story.py
python storyworlds/worlds/gpt-5.4/pump_magic_ghost_story.py --plant moonflower --primer feather
python storyworlds/worlds/gpt-5.4/pump_magic_ghost_story.py --all
python storyworlds/worlds/gpt-5.4/pump_magic_ghost_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/pump_magic_ghost_story.py --json
python storyworlds/worlds/gpt-5.4/pump_magic_ghost_story.py --asp
python storyworlds/worlds/gpt-5.4/pump_magic_ghost_story.py --verify
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
HELP_THRESHOLD = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path: str
    sky: str
    affords: set[str] = field(default_factory=set)
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
class Plant:
    id: str
    label: str
    phrase: str
    glow: str
    bloom: str
    need_line: str
    urgency: int
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
class Primer:
    id: str
    label: str
    phrase: str
    splash: str
    holds_water: bool = True
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
class Charm:
    id: str
    label: str
    phrase: str
    comfort: int
    magic_line: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_scare(world: World) -> list[str]:
    child = world.get("child")
    ghost = world.get("ghost")
    pump = world.get("pump")
    if ghost.meters["visible"] < THRESHOLD or pump.meters["groaning"] < THRESHOLD:
        return []
    sig = ("scare",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    return []


def _r_water_flow(world: World) -> list[str]:
    pump = world.get("pump")
    plant = world.get("plant")
    if pump.meters["primed"] < THRESHOLD or pump.meters["pumped"] < THRESHOLD:
        return []
    sig = ("water_flow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["watered"] += 1
    plant.meters["thirst"] = 0.0
    return []


def _r_bloom(world: World) -> list[str]:
    plant = world.get("plant")
    child = world.get("child")
    ghost = world.get("ghost")
    if plant.meters["watered"] < THRESHOLD:
        return []
    sig = ("bloom",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["blooming"] += 1
    child.memes["wonder"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    ghost.memes["relief"] += 1
    ghost.meters["peace"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="scare", tag="emotion", apply=_r_scare),
    Rule(name="water_flow", tag="physical", apply=_r_water_flow),
    Rule(name="bloom", tag="magic", apply=_r_bloom),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) != before:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "moon_garden": Place(
        id="moon_garden",
        label="the moon garden",
        opening="Behind the cottage, a moon garden slept under pale mist.",
        path="a narrow path of white stones",
        sky="The clouds kept sliding away from the moon, letting silver light spill over the beds.",
        affords={"moonflower", "star_lily", "silver_fern"},
        tags={"garden", "night"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the old courtyard",
        opening="At the side of the house, the old courtyard looked full of shadows and ivy.",
        path="a ring of dark bricks",
        sky="Moonlight rested in the corners like milk poured into tiny bowls.",
        affords={"star_lily", "silver_fern"},
        tags={"courtyard", "night"},
    ),
    "glasshouse": Place(
        id="glasshouse",
        label="the glasshouse",
        opening="Past the back door, the glasshouse gleamed with foggy silver panes.",
        path="a damp path between long planting tables",
        sky="The moon shone through the glass roof and drew quiet bars of light on the floor.",
        affords={"moonflower", "silver_fern"},
        tags={"glasshouse", "night"},
    ),
}

PLANTS = {
    "moonflower": Plant(
        id="moonflower",
        label="moonflower",
        phrase="a moonflower vine with folded white buds",
        glow="a pearly shine",
        bloom="the white flowers opened all at once, as wide and soft as little moons",
        need_line="Moonflowers drink just before the moon climbs high.",
        urgency=1,
        tags={"moonflower", "flower", "magic"},
    ),
    "star_lily": Plant(
        id="star_lily",
        label="star lily",
        phrase="a clump of star lilies with tight silver buds",
        glow="a cool blue gleam",
        bloom="the star lilies lifted their faces and spilled blue light over the stones",
        need_line="Star lilies wake only if they get a drink before midnight.",
        urgency=2,
        tags={"lily", "flower", "magic"},
    ),
    "silver_fern": Plant(
        id="silver_fern",
        label="silver fern",
        phrase="a silver fern curled up like a sleeping umbrella",
        glow="a green-silver shimmer",
        bloom="the fern uncurling made the whole bed shine like brushed silver",
        need_line="A silver fern uncurls only after a fresh pull from the pump.",
        urgency=2,
        tags={"fern", "magic", "garden"},
    ),
}

PRIMERS = {
    "tin_cup": Primer(
        id="tin_cup",
        label="tin cup",
        phrase="a little tin cup",
        splash="splashed the first little drink of water into the pump mouth",
        holds_water=True,
        tags={"cup", "pump"},
    ),
    "blue_jar": Primer(
        id="blue_jar",
        label="blue jar",
        phrase="a blue jar",
        splash="tipped the jar carefully and wet the dry throat of the pump",
        holds_water=True,
        tags={"jar", "pump"},
    ),
    "little_can": Primer(
        id="little_can",
        label="little watering can",
        phrase="a little watering can",
        splash="poured a patient ribbon of water into the pump until it stopped coughing",
        holds_water=True,
        tags={"watering_can", "pump"},
    ),
    "feather": Primer(
        id="feather",
        label="feather",
        phrase="a soft gray feather",
        splash="waved the feather at the pump",
        holds_water=False,
        tags={"feather"},
    ),
}

CHARMS = {
    "bell": Charm(
        id="bell",
        label="brass bell",
        phrase="a tiny brass bell",
        comfort=2,
        magic_line="It gave a brave little chime that sounded warmer than the dark.",
        tags={"bell", "magic"},
    ),
    "ribbon": Charm(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon from the child's pocket",
        comfort=1,
        magic_line="The ribbon fluttered as if it already knew a kind wind was nearby.",
        tags={"ribbon", "magic"},
    ),
    "stone": Charm(
        id="stone",
        label="moon stone",
        phrase="a smooth moon stone",
        comfort=2,
        magic_line="The stone kept a pocket of cool light in the child's hand.",
        tags={"stone", "magic"},
    ),
    "none": Charm(
        id="none",
        label="nothing",
        phrase="nothing but a steady breath",
        comfort=0,
        magic_line="The child had no charm at all, only a quick heartbeat in the dark.",
        tags=set(),
    ),
}

TRAIT_BRAVERY = {
    "timid": 2,
    "careful": 3,
    "curious": 4,
    "brave": 5,
    "gentle": 3,
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ivy", "Lucy", "Ella", "Zoe", "Ada"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Ben", "Leo", "Eli", "Noah"]
TRAITS = list(TRAIT_BRAVERY.keys())


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for plant_id in sorted(place.affords):
            for primer_id, primer in PRIMERS.items():
                if primer.holds_water:
                    combos.append((place_id, plant_id, primer_id))
    return combos


def explain_rejection(place: Place, plant: Plant, primer: Primer) -> str:
    if plant.id not in place.affords:
        return (
            f"(No story: {plant.phrase} does not belong in {place.label}, so the "
            f"night problem would not naturally happen there. Pick a place that "
            f"actually grows {plant.label}.)"
        )
    if not primer.holds_water:
        return (
            f"(No story: {primer.phrase} cannot carry the little splash of water an old "
            f"pump needs before it can pull from the well. Choose a cup, jar, or can.)"
        )
    return "(No story: this combination does not make sense in this world.)"


def courage_score(trait: str, charm_id: str) -> int:
    return TRAIT_BRAVERY[trait] + CHARMS[charm_id].comfort


def outcome_of(params: "StoryParams") -> str:
    plant = PLANTS[params.plant]
    in_time = params.delay <= plant.urgency
    if not in_time:
        return "missed"
    return "friend" if courage_score(params.trait, params.charm) >= HELP_THRESHOLD else "shared"


def predict_bloom(place_id: str, plant_id: str, primer_id: str, delay: int) -> dict:
    place = PLACES[place_id]
    plant = PLANTS[plant_id]
    primer = PRIMERS[primer_id]
    return {
        "valid_place": plant_id in place.affords,
        "can_prime": primer.holds_water,
        "in_time": delay <= plant.urgency,
    }


def introduce(world: World, child: Entity, elder: Entity, plant: Plant, charm: Charm) -> None:
    world.say(f"{child.id} was staying with {child.pronoun('possessive')} {elder.label_word} for the week.")
    world.say(world.place.opening)
    world.say(
        f"By the gate stood an old iron pump, black and still, and nearby grew {plant.phrase}."
    )
    world.say(world.place.sky)
    if charm.id != "none":
        world.say(
            f"In {child.pronoun('possessive')} pocket, {child.pronoun()} carried {charm.phrase}. "
            f"{charm.magic_line}"
        )


def hear_pump(world: World, child: Entity) -> None:
    pump = world.get("pump")
    pump.meters["groaning"] += 1
    world.say(
        f"Then the quiet broke. Clank. Creak. The pump handle moved by itself and gave a long hollow groan."
    )
    propagate(world, narrate=False)
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"{child.id} stopped on {world.place.path}. For one chilly moment, {child.pronoun()} was sure a ghost had found the pump."
        )


def see_need(world: World, child: Entity, plant: Plant) -> None:
    plant_ent = world.get("plant")
    plant_ent.meters["thirst"] = 1.0
    world.say(
        f"Under the spooky sound, {child.id} noticed something else: the {plant.label} drooped sadly, as if the night were passing too fast."
    )
    world.say(f"A dry rustle came from the leaves, and it almost sounded like words: \"{plant.need_line}\"")


def reveal_ghost(world: World, child: Entity, ghost: Entity, plant: Plant) -> None:
    ghost.meters["visible"] += 1
    ghost.memes["kindness"] = 1.0
    propagate(world, narrate=False)
    world.say(
        "A pale shape rose beside the pump, thin as moon-mist and wearing a gardener's hat that never quite touched its head."
    )
    world.say(
        f'''\"Please don't run,\" whispered the ghost. \"I only mean to water the {plant.label}. I can lift the handle, but I cannot prime the pump.\"'''
    )
    if child.memes["fear"] >= 2:
        world.say(
            f"{child.id}'s knees felt wobbly, but the ghost's voice sounded lonely instead of mean."
        )


def decide(world: World, child: Entity, elder: Entity, charm: Charm) -> None:
    score = courage_score(world.facts["trait"], charm.id)
    world.facts["courage"] = score
    if score >= HELP_THRESHOLD:
        child.memes["courage"] += 1
        world.say(
            f"{child.id} squeezed {charm.phrase if charm.id != 'none' else 'small hands'} and took one slow breath. The dark still felt strange, but not quite as terrible as before."
        )
    else:
        child.memes["fear"] += 1
        world.say(
            f'''{child.id} took a step back and whispered toward the kitchen door, \"{elder.label_word.capitalize()}, please come.\"'''
        )


def wait_delay(world: World, delay: int) -> None:
    for _ in range(delay):
        world.get("plant").meters["lateness"] += 1
    if delay == 1:
        world.say("A cloud slid over the moon, and another quiet minute slipped by.")
    elif delay >= 2:
        world.say("Two long, hushy minutes slipped by while the night grew deeper and the buds stayed shut.")


def prime_and_pump(world: World, actor: Entity, primer: Primer) -> None:
    pump = world.get("pump")
    pump.meters["primed"] = 1.0
    pump.meters["pumped"] = 1.0
    world.say(
        f"{actor.id} used {primer.phrase} and {primer.splash}. Then {actor.pronoun()} pulled the handle down with both hands."
    )
    world.say("The pump coughed once, shuddered twice, and then clear water rushed out in a bright silver stream.")
    propagate(world, narrate=False)


def bloom_scene(world: World, plant: Plant) -> None:
    if world.get("plant").meters["blooming"] >= THRESHOLD:
        world.say(
            f"The water ran around the roots, and at once {plant.bloom}. A soft {plant.glow} spread over the garden."
        )


def elder_arrives(world: World, elder: Entity) -> None:
    elder.memes["care"] += 1
    world.say(
        f"{elder.label_word.capitalize()} came out with a warm lantern, saw the drooping plant and the trembling ghost, and listened before saying a single word."
    )
    world.say(
        f'''\"Well,\" {elder.pronoun()} said gently, \"a thirsty plant is a serious thing, even in a ghost story.\"'''
    )


def comfort_after_bloom(world: World, child: Entity, ghost: Entity, elder: Optional[Entity], plant: Plant) -> None:
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    if elder is not None:
        world.say(
            f"The ghost gardener touched the brim of {ghost.pronoun('possessive')} hat to both of them. \"You were brave together,\" {ghost.pronoun()} whispered."
        )
    else:
        world.say(
            f"The ghost gardener smiled so softly that {child.id} stopped feeling hunted and started feeling helpful."
        )
    world.say(
        f"From then on, the old pump did not sound like a warning to {child.id}. It sounded like a secret job being done at the right time."
    )
    if plant.id == "moonflower":
        world.say("The open flowers shone over the path like a row of tiny moons.")
    elif plant.id == "star_lily":
        world.say("Blue light from the lilies made every wet stone look polished and new.")
    else:
        world.say("The silver fern glittered as if the moon had chosen to rest inside its leaves.")


def missed_scene(world: World, child: Entity, elder: Entity, ghost: Entity, plant: Plant, primer: Primer) -> None:
    elder_arrives(world, elder)
    prime_and_pump(world, elder, primer)
    world.say(
        f"The water reached the roots, but the night was already too far along. The {plant.label} trembled, brightened for one hopeful second, and then stayed closed."
    )
    ghost.memes["relief"] += 1
    ghost.meters["peace"] += 1
    child.memes["sadness"] += 1
    world.say(
        f'''\"Too late for tonight,\" said the ghost, though {ghost.pronoun('possessive')} voice was kind. \"But not too late forever.\"'''
    )
    world.say(
        f"The next evening, {child.id} and {elder.label_word} primed the pump before sunset, and the {plant.label} opened at moonrise as if it had been waiting just for them."
    )
    world.say(
        f"After that, the pump's lonely creak no longer sounded frightening. It sounded like a promise they knew how to keep."
    )

def tell(
    child_name: str,
    child_type: ChildType,
    elder_type: ElderType,
    trait: str,
    delay: Delay,
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            traits=[trait],
            attrs={},
            tags={"child"},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            attrs={},
            tags={"adult"},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label="the ghost gardener",
            attrs={},
            tags={"ghost", "magic"},
        )
    )
    pump = world.add(
        Entity(
            id="pump",
            kind="thing",
            type="pump",
            label="old hand pump",
            attrs={"needs_prime": True},
            tags={"pump"},
        )
    )
    plant_ent = world.add(
        Entity(
            id="plant",
            kind="thing",
            type=plant.id,
            label=plant.label,
            attrs={"urgency": plant.urgency},
            tags=set(plant.tags),
        )
    )

    child.memes["fear"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["sadness"] = 0.0
    ghost.meters["visible"] = 0.0
    ghost.meters["peace"] = 0.0
    ghost.memes["relief"] = 0.0
    pump.meters["groaning"] = 0.0
    pump.meters["primed"] = 0.0
    pump.meters["pumped"] = 0.0
    plant_ent.meters["thirst"] = 0.0
    plant_ent.meters["watered"] = 0.0
    plant_ent.meters["blooming"] = 0.0
    plant_ent.meters["lateness"] = 0.0

    world.facts.update(
        place=place,
        plant_cfg=plant,
        primer=primer,
        charm=charm,
        child=child,
        elder=elder,
        ghost=ghost,
        pump=pump,
        plant=plant_ent,
        trait=trait,
        delay=delay,
    )

    introduce(world, child, elder, plant, charm)
    world.para()
    hear_pump(world, child)
    see_need(world, child, plant)
    reveal_ghost(world, child, ghost, plant)
    decide(world, child, elder, charm)
    wait_delay(world, delay)

    outcome = outcome_of(
        StoryParams(
            place=place.id,
            plant=plant.id,
            primer=primer.id,
            charm=charm.id,
            name=child_name,
            gender=child_type,
            elder=elder_type,
            trait=trait,
            delay=delay,
            seed=None,
        )
    )
    world.para()
    if outcome == "friend":
        prime_and_pump(world, child, primer)
        bloom_scene(world, plant)
        comfort_after_bloom(world, child, ghost, None, plant)
    elif outcome == "shared":
        elder_arrives(world, elder)
        prime_and_pump(world, child, primer)
        bloom_scene(world, plant)
        comfort_after_bloom(world, child, ghost, elder, plant)
    else:
        missed_scene(world, child, elder, ghost, plant, primer)

    world.facts["outcome"] = outcome
    world.facts["bloomed"] = world.get("plant").meters["blooming"] >= THRESHOLD
    world.facts["peace"] = world.get("ghost").meters["peace"] >= THRESHOLD
    return world
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
    "pump": [
        (
            "What is a hand pump?",
            "A hand pump is a tool with a handle that people move up and down to pull water from below the ground. Old pumps often need a little water first so they can start working.",
        )
    ],
    "ghost": [
        (
            "Are ghosts in stories always mean?",
            "No. In stories, some ghosts are sad or lonely, and some are kind. A ghost story can be spooky without being cruel.",
        )
    ],
    "moonflower": [
        (
            "What is a moonflower?",
            "A moonflower is a flower people imagine opening at night in pale moonlight. In a magic story, it can glow and bloom when the night is just right.",
        )
    ],
    "lily": [
        (
            "What is a lily?",
            "A lily is a kind of flower with petals that open around the middle. In stories, lilies are often used to make a garden feel quiet and magical.",
        )
    ],
    "fern": [
        (
            "What is a fern?",
            "A fern is a leafy plant with fronds that uncurl as it grows. Some ferns look feathery and can make a shady place feel cool and secret.",
        )
    ],
    "bell": [
        (
            "Why can a little bell feel brave in a story?",
            "A bell makes a clear sound in the dark. That can help a character feel less alone.",
        )
    ],
    "night": [
        (
            "Why do places seem spooky at night?",
            "At night, there is less light and more shadow, so familiar things can look strange. Sounds also seem louder when everything is quiet.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pump", "ghost", "moonflower", "lily", "fern", "bell", "night"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    plant = f["plant_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    if outcome == "friend":
        return [
            'Write a gentle ghost story for a 3-to-5-year-old that includes the word "pump" and a magical night garden.',
            f"Tell a spooky-but-safe story where {child.id} hears an old pump in {place.label}, meets a kind ghost, and helps save a {plant.label}.",
            f"Write a story where a child is frightened by a ghostly sound, learns the truth, and ends with {plant.bloom}.",
        ]
    if outcome == "shared":
        return [
            'Write a child-friendly ghost story with magic, moonlight, and the word "pump".',
            f"Tell a story where {child.id} hears a ghost at the pump, calls a trusted grown-up, and together they help a magical {plant.label}.",
            f"Write a spooky story with a warm ending where fear turns into teamwork and kindness.",
        ]
    return [
        'Write a gentle ghost story that includes the word "pump" and ends with hope instead of harm.',
        f"Tell a story where {child.id} is almost too late to help a magical {plant.label}, but learns how to be ready the next night.",
        f"Write a moonlit ghost story where a scary sound hides a kind reason and the ending shows what the child learned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    plant = f["plant_cfg"]
    primer = f["primer"]
    ghost = f["ghost"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {elder.label_word}, and a ghost gardener near an old pump. The magical plant in the garden matters too, because it is the reason the ghost appears.",
        ),
        (
            "Why did the pump sound spooky at first?",
            f"The pump groaned in the dark and its handle moved before {child.id} understood why. In the quiet night, that made the sound seem ghostly and frightening.",
        ),
        (
            f"Why did the ghost need help with the pump?",
            f"The ghost wanted to water the {plant.label}, but the old pump needed to be primed first. The first splash had to be carried in {primer.phrase}, and the ghost could not manage that part alone.",
        ),
    ]
    if outcome == "friend":
        qa.append(
            (
                f"How did {child.id} solve the problem?",
                f"{child.id} stayed, primed the pump, and pulled the handle until the water came. Because {child.pronoun()} helped in time, the {plant.label} bloomed and the ghost could finally relax.",
            )
        )
        qa.append(
            (
                f"How did {child.id} feel at the end?",
                f"{child.id} felt amazed and relieved instead of scared. The blooming plant showed that the spooky moment had really been a chance to help.",
            )
        )
    elif outcome == "shared":
        qa.append(
            (
                f"Why did {child.id} call {elder.label_word}?",
                f"{child.id} was still afraid and wanted a trusted grown-up nearby. That choice helped turn fear into teamwork instead of panic.",
            )
        )
        qa.append(
            (
                "What changed after the water came out of the pump?",
                f"The {plant.label} opened and lit the place with magic, and the ghost looked peaceful instead of worried. The bright bloom proved that the night sound had a kind cause.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the {plant.label} not open that same night?",
                f"Too much time passed before the pump was working, so the moment for blooming was gone. Even so, the child and {elder.label_word} learned what to do and came back ready the next evening.",
            )
        )
        qa.append(
            (
                "How did the story still end happily?",
                f"The next night they primed the pump before sunset and the plant opened at moonrise. That later success shows the child changed from frightened and unsure to prepared and helpful.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pump", "ghost", "night"} | set(world.facts["plant_cfg"].tags) | set(world.facts["primer"].tags) | set(world.facts["charm"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    plant: str
    primer: str
    charm: str
    name: str
    gender: str
    elder: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="moon_garden",
        plant="moonflower",
        primer="tin_cup",
        charm="stone",
        name="Lila",
        gender="girl",
        elder="grandmother",
        trait="curious",
        delay=0,
        seed=None,
    ),
    StoryParams(
        place="courtyard",
        plant="star_lily",
        primer="blue_jar",
        charm="none",
        name="Owen",
        gender="boy",
        elder="grandfather",
        trait="careful",
        delay=1,
        seed=None,
    ),
    StoryParams(
        place="glasshouse",
        plant="moonflower",
        primer="little_can",
        charm="ribbon",
        name="Mina",
        gender="girl",
        elder="grandmother",
        trait="timid",
        delay=2,
        seed=None,
    ),
    StoryParams(
        place="moon_garden",
        plant="silver_fern",
        primer="little_can",
        charm="bell",
        name="Theo",
        gender="boy",
        elder="grandfather",
        trait="brave",
        delay=0,
        seed=None,
    ),
]


ASP_RULES = r"""
valid(Place, Plant, Primer) :- place(Place), plant(Plant), primer(Primer),
                               affords(Place, Plant), holds_water(Primer).

score(S + C) :- chosen_trait(T), trait_bravery(T, S), chosen_charm(H), charm_comfort(H, C).
brave_enough :- score(V), help_threshold(H), V >= H.
in_time      :- chosen_plant(P), urgency(P, U), delay(D), D <= U.

outcome(friend) :- in_time, brave_enough.
outcome(shared) :- in_time, not brave_enough.
outcome(missed) :- not in_time.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for plant_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, plant_id))
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        lines.append(asp.fact("urgency", plant_id, plant.urgency))
    for primer_id, primer in PRIMERS.items():
        lines.append(asp.fact("primer", primer_id))
        if primer.holds_water:
            lines.append(asp.fact("holds_water", primer_id))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        lines.append(asp.fact("charm_comfort", charm_id, charm.comfort))
    for trait, score in TRAIT_BRAVERY.items():
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("trait_bravery", trait, score))
    lines.append(asp.fact("help_threshold", HELP_THRESHOLD))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_plant", params.plant),
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_charm", params.charm),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
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
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: an old pump, a magical plant, and a child who learns what the spooky sound really means."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--primer", choices=PRIMERS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.place and args.plant and args.primer:
        place = PLACES[args.place]
        plant = PLANTS[args.plant]
        primer = PRIMERS[args.primer]
        if not (args.plant in place.affords and primer.holds_water):
            raise StoryError(explain_rejection(place, plant, primer))
    if args.primer and not PRIMERS[args.primer].holds_water:
        plant = PLANTS[args.plant] if args.plant else PLANTS["moonflower"]
        place = PLACES[args.place] if args.place else PLACES["moon_garden"]
        raise StoryError(explain_rejection(place, plant, PRIMERS[args.primer]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.plant is None or combo[1] == args.plant)
        and (args.primer is None or combo[2] == args.primer)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, plant_id, primer_id = rng.choice(sorted(combos))
    charm_id = args.charm or rng.choice(sorted(CHARMS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place_id,
        plant=plant_id,
        primer=primer_id,
        charm=charm_id,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.primer not in PRIMERS:
        raise StoryError(f"(Unknown primer: {params.primer})")
    if params.charm not in CHARMS:
        raise StoryError(f"(Unknown charm: {params.charm})")
    if params.trait not in TRAIT_BRAVERY:
        raise StoryError(f"(Unknown trait: {params.trait})")
    place = PLACES[params.place]
    plant = PLANTS[params.plant]
    primer = PRIMERS[params.primer]
    if not (params.plant in place.affords and primer.holds_water):
        raise StoryError(explain_rejection(place, plant, primer))

    world = tell(
        place,
        plant,
        primer,
        CHARMS[params.charm],
        child_name=params.name,
        child_type=params.gender,
        elder_type=params.elder,
        trait=params.trait,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (place, plant, primer) combos:\n")
        for place, plant, primer in combos:
            print(f"  {place:12} {plant:12} {primer}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.plant} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
