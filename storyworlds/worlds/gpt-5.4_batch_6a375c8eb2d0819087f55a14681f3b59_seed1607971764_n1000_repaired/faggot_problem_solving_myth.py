#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/faggot_problem_solving_myth.py
========================================================

A standalone story world for a tiny myth-shaped tale of problem solving:
after a storm, a child must carry a sacred ember home from a hill shrine.
The path is hard, and a bare coal would die in the weather, so the child and
an elder must choose a sensible way to protect and feed the ember. One of the
possible fuel bundles is a **faggot**: a tied bundle of dry sticks.

The world model enforces a simple common-sense rule:
a working solution needs both

1. a carrier that protects the ember from the chosen hazard, and
2. fuel strong enough to keep the ember alive for the length of the path.

So the story is not a frozen paragraph with swapped nouns. The middle turn
depends on whether the chosen carrier truly shields the ember and whether the
fuel bundle can keep it glowing long enough to reach the village hearth.

Run it
------
    python storyworlds/worlds/gpt-5.4/faggot_problem_solving_myth.py
    python storyworlds/worlds/gpt-5.4/faggot_problem_solving_myth.py --quest sun_hill --hazard wind --carrier ember_pot --fuel faggot
    python storyworlds/worlds/gpt-5.4/faggot_problem_solving_myth.py --carrier open_shell
    python storyworlds/worlds/gpt-5.4/faggot_problem_solving_myth.py --all
    python storyworlds/worlds/gpt-5.4/faggot_problem_solving_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/faggot_problem_solving_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "woman", "mother", "priestess", "grandmother"}
        male = {"boy", "man", "father", "priest", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "priestess": "priestess",
            "priest": "priest",
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
class Quest:
    id: str
    village: str
    source: str
    source_image: str
    goal: str
    path: str
    distance: int
    opening: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    threat: str
    step_text: str
    intensity: int
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
class Carrier:
    id: str
    label: str
    phrase: str
    sense: int
    guards: set[str] = field(default_factory=set)
    image: str = ""
    warning: str = ""
    success: str = ""
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
class Fuel:
    id: str
    label: str
    phrase: str
    burn: int
    dry: bool = True
    kindling_text: str = ""
    ending_text: str = ""
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_hazard_hits(world: World) -> list[str]:
    ember = world.get("ember")
    carrier = world.get("carrier")
    if ember.meters["carried"] < THRESHOLD:
        return []
    hazard_id = world.facts["hazard"].id
    sig = ("hazard_hits", hazard_id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if hazard_id not in carrier.attrs.get("guards", set()):
        ember.meters["heat"] -= world.facts["hazard"].intensity
        ember.meters["exposed"] += 1
        world.get("hero").memes["fear"] += 1
        return ["__hazard_exposed__"]
    ember.meters["safe"] += 1
    world.get("hero").memes["hope"] += 1
    return ["__hazard_guarded__"]


def _r_fuel_feeds(world: World) -> list[str]:
    ember = world.get("ember")
    fuel = world.get("fuel")
    if ember.meters["carried"] < THRESHOLD:
        return []
    sig = ("fuel_feeds", fuel.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ember.meters["heat"] += fuel.attrs.get("burn", 0)
    ember.meters["fed"] += 1
    return ["__fuel__"]


def _r_arrival(world: World) -> list[str]:
    ember = world.get("ember")
    quest = world.facts["quest"]
    sig = ("arrival", quest.id)
    if ember.meters["heat"] < quest.distance or sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hearth").meters["lit"] += 1
    world.get("hero").memes["relief"] += 1
    world.get("hero").memes["pride"] += 1
    return ["__hearth_lit__"]


CAUSAL_RULES = [
    Rule(name="hazard_hits", tag="physical", apply=_r_hazard_hits),
    Rule(name="fuel_feeds", tag="physical", apply=_r_fuel_feeds),
    Rule(name="arrival", tag="physical", apply=_r_arrival),
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
                produced.extend(out)
    return produced


def protects(carrier: Carrier, hazard: Hazard) -> bool:
    return hazard.id in carrier.guards


def ember_lasts(quest: Quest, hazard: Hazard, carrier: Carrier, fuel: Fuel) -> bool:
    base_heat = 2
    penalty = 0 if protects(carrier, hazard) else hazard.intensity
    return (base_heat - penalty + fuel.burn) >= quest.distance


def valid_solution(quest: Quest, hazard: Hazard, carrier: Carrier, fuel: Fuel) -> bool:
    return carrier.sense >= SENSE_MIN and protects(carrier, hazard) and ember_lasts(quest, hazard, carrier, fuel)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for qid, quest in QUESTS.items():
        for hid, hazard in HAZARDS.items():
            for cid, carrier in CARRIERS.items():
                for fid, fuel in FUELS.items():
                    if valid_solution(quest, hazard, carrier, fuel):
                        out.append((qid, hid, cid, fid))
    return out


def explain_rejection(quest: Quest, hazard: Hazard, carrier: Carrier, fuel: Fuel) -> str:
    if carrier.sense < SENSE_MIN:
        return (
            f"(No story: {carrier.phrase} is known in the world, but it is too flimsy for a careful myth. "
            f"It does not sound like a wise answer to {hazard.phrase}. Pick a sturdier carrier.)"
        )
    if not protects(carrier, hazard):
        return (
            f"(No story: {carrier.phrase} does not protect an ember from {hazard.phrase}, "
            f"so the coal would die on the path from {quest.source} to {quest.goal}.)"
        )
    if not ember_lasts(quest, hazard, carrier, fuel):
        return (
            f"(No story: {fuel.phrase} would not keep the ember alive long enough for the {quest.path}. "
            f"The solution needs stronger or longer-burning fuel.)"
        )
    return "(No story: this combination does not make a complete problem-solving myth.)"


def sensible_carriers() -> list[Carrier]:
    return [c for c in CARRIERS.values() if c.sense >= SENSE_MIN]


def predict_trip(world: World, carrier_id: str, fuel_id: str) -> dict:
    sim = world.copy()
    sim.entities["carrier"] = copy.deepcopy(sim.entities["carrier"])
    sim.entities["fuel"] = copy.deepcopy(sim.entities["fuel"])
    sim.get("carrier").id = carrier_id
    sim.get("carrier").label = CARRIERS[carrier_id].label
    sim.get("carrier").attrs["guards"] = set(CARRIERS[carrier_id].guards)
    sim.get("carrier").attrs["sense"] = CARRIERS[carrier_id].sense
    sim.get("fuel").id = fuel_id
    sim.get("fuel").label = FUELS[fuel_id].label
    sim.get("fuel").attrs["burn"] = FUELS[fuel_id].burn
    sim.get("ember").meters["carried"] = 1
    propagate(sim, narrate=False)
    return {
        "heat": sim.get("ember").meters["heat"],
        "will_arrive": sim.get("hearth").meters["lit"] >= THRESHOLD,
        "exposed": sim.get("ember").meters["exposed"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity, quest: Quest) -> None:
    world.say(
        f"In the old days, when hills were said to remember the footsteps of gods, "
        f"there was a child named {hero.id} in {quest.village}. {quest.opening}"
    )
    world.say(
        f"Only one live ember still glowed, high at {quest.source}, where {quest.source_image}."
    )
    world.say(
        f"{elder.id}, the village {elder.label_word}, said that if a new spark reached {quest.goal}, "
        f"warmth and supper would return before the moon climbed high."
    )


def problem(world: World, hero: Entity, quest: Quest, hazard: Hazard) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"So {hero.id} took the little ember with both hands and looked up the {quest.path}. "
        f"But {hazard.phrase} lay across the way, and everyone knew {hazard.threat}."
    )


def foolish_idea(world: World, hero: Entity, carrier: Carrier) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'At first, {hero.id} thought of hurrying with the coal in {carrier.phrase}. '
        f"{carrier.warning}"
    )


def counsel(world: World, hero: Entity, elder: Entity, quest: Quest, hazard: Hazard,
            carrier: Carrier, fuel: Fuel) -> None:
    pred = predict_trip(world, carrier.id, fuel.id)
    world.facts["predicted_heat"] = pred["heat"]
    world.facts["predicted_arrival"] = pred["will_arrive"]
    world.facts["predicted_exposed"] = pred["exposed"]
    hero.memes["wonder"] += 1
    world.say(
        f'But {elder.id} watched the weather and said, "{hazard.phrase.capitalize()} is stronger than quick feet. '
        f'Think like the old makers. Do not carry the ember bare; give it a house and food."'
    )
    world.say(
        f"Together they chose {carrier.phrase} and {fuel.phrase}. {fuel.kindling_text}"
    )


def set_out(world: World, hero: Entity, quest: Quest, hazard: Hazard) -> None:
    world.get("ember").meters["carried"] = 1
    world.say(
        f"{hero.id} tucked the red coal deep inside the carrier and started along {quest.path}. "
        f"{hazard.step_text}"
    )


def cross_path(world: World, hero: Entity, carrier: Carrier, fuel: Fuel, hazard: Hazard) -> None:
    markers = propagate(world, narrate=False)
    if "__hazard_guarded__" in markers:
        world.say(
            f"When the trouble came, {carrier.success}. The ember did not blink out."
        )
    if "__fuel__" in markers:
        world.say(
            f"Inside, {fuel.ending_text}, so the red heart of the fire stayed alive."
        )
    if "__hearth_lit__" in markers:
        world.say(
            f"By the time {hero.id} reached {quest.goal}, the coal still shone like a berry in winter."
        )
    else:
        raise StoryError("Internal error: a supposedly valid solution did not light the hearth.")


def ending(world: World, hero: Entity, elder: Entity, quest: Quest, fuel: Fuel) -> None:
    world.say(
        f"{hero.id} tipped the ember onto waiting twigs, and the village hearth breathed back into flame. "
        f"Soon bowls steamed, hands warmed, and the shadows stepped away from the walls."
    )
    world.say(
        f"{elder.id} smiled and called the child wise, not because {hero.pronoun()} had been the strongest, "
        f"but because {hero.pronoun()} had solved the hard part before the walking began."
    )
    world.say(quest.ending)
    if fuel.id == "faggot":
        world.say(
            "And for many winters after, people remembered the little faggot of dry sticks that helped carry the fire home."
        )


def tell(quest: Quest, hazard: Hazard, carrier: Carrier, fuel: Fuel,
         hero_name: str = "Iria", hero_gender: str = "girl",
         elder_type: str = "priestess") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    ember = world.add(Entity(id="ember", type="ember", label="ember"))
    hearth = world.add(Entity(id="hearth", type="hearth", label="hearth"))
    carrier_ent = world.add(Entity(id="carrier", type="carrier", label=carrier.label,
                                   attrs={"guards": set(carrier.guards), "sense": carrier.sense}))
    fuel_ent = world.add(Entity(id="fuel", type="fuel", label=fuel.label,
                                attrs={"burn": fuel.burn, "dry": fuel.dry}))

    ember.meters["heat"] = 2
    ember.meters["carried"] = 0
    ember.meters["safe"] = 0
    ember.meters["exposed"] = 0
    ember.meters["fed"] = 0
    hearth.meters["lit"] = 0
    hero.memes["fear"] = 0
    hero.memes["hope"] = 0
    hero.memes["relief"] = 0
    hero.memes["pride"] = 0

    world.facts.update(
        quest=quest,
        hazard=hazard,
        carrier=carrier,
        fuel=fuel,
        hero=hero,
        elder=elder,
    )

    introduce(world, hero, elder, quest)
    world.para()
    problem(world, hero, quest, hazard)
    foolish_idea(world, hero, carrier)
    counsel(world, hero, elder, quest, hazard, carrier, fuel)
    world.para()
    set_out(world, hero, quest, hazard)
    cross_path(world, hero, carrier, fuel, hazard)
    world.para()
    ending(world, hero, elder, quest, fuel)
    world.facts.update(
        solved=world.get("hearth").meters["lit"] >= THRESHOLD,
        exposed=world.get("ember").meters["exposed"] >= THRESHOLD,
        heat=world.get("ember").meters["heat"],
    )
    return world


QUESTS = {
    "sun_hill": Quest(
        id="sun_hill",
        village="Ash Hollow",
        source="the Hill of the Sun",
        source_image="a stone bowl held the last temple flame beneath a ring of carved birds",
        goal="the cold village hearth",
        path="the goat path down the hill",
        distance=4,
        opening="After three nights of storm, every cookfire in the hollow had gone dark.",
        ending="That night the fire shone in every doorway, and the hill seemed less lonely.",
        tags={"hearth", "myth"},
    ),
    "moon_cave": Quest(
        id="moon_cave",
        village="Reed Ford",
        source="the Moon Cave",
        source_image="a silver crack in the rock sheltered a patient blue spark",
        goal="the river shrine hearth",
        path="the stepping-stone trail by the reeds",
        distance=3,
        opening="A bitter rain had drowned the lamps, and the river people sat wrapped in blankets.",
        ending="Even the reeds by the ford whispered as if they approved of the answer.",
        tags={"hearth", "myth"},
    ),
    "oak_spring": Quest(
        id="oak_spring",
        village="Fern Vale",
        source="the Spring of the Old Oak",
        source_image="a watch-fire burned beneath roots twisted like sleeping serpents",
        goal="the meeting-house hearth",
        path="the root-shadowed lane through the vale",
        distance=5,
        opening="When mist lay heavy for seven mornings, the valley hearths thinned to smoke and ash.",
        ending="The old oak kept its silence, but from then on the people bowed to it with grateful smiles.",
        tags={"hearth", "myth"},
    ),
}

HAZARDS = {
    "wind": Hazard(
        id="wind",
        label="wind",
        phrase="a sharp hill wind",
        threat="a bare coal can lose its breath in a single gust",
        step_text="The wind worried at the child's cloak and tugged at every loose thing.",
        intensity=2,
        tags={"wind"},
    ),
    "drizzle": Hazard(
        id="drizzle",
        label="drizzle",
        phrase="a thin silver drizzle",
        threat="raindrops can kiss a small ember dead",
        step_text="Fine drops stitched the air and made the stones shine.",
        intensity=1,
        tags={"rain"},
    ),
    "mist": Hazard(
        id="mist",
        label="mist",
        phrase="a thick walking mist",
        threat="damp air can smother a weak spark before it reaches home",
        step_text="Mist curled around the path until the world seemed made of breath.",
        intensity=2,
        tags={"mist"},
    ),
}

CARRIERS = {
    "ember_pot": Carrier(
        id="ember_pot",
        label="ember pot",
        phrase="a little clay ember pot with a lid",
        sense=3,
        guards={"wind", "drizzle", "mist"},
        image="clay with a mouth like a sleeping bird",
        warning="A naked coal would have all the sky against it.",
        success="the lid turned the weather aside and kept the spark in a warm red cave",
        tags={"pot", "fire"},
    ),
    "horn_lantern": Carrier(
        id="horn_lantern",
        label="horn lantern",
        phrase="a horn lantern bound with copper",
        sense=3,
        guards={"wind", "mist"},
        image="amber walls that glowed like honey",
        warning="It would be foolish to trust an open ember to the path.",
        success="the horn sides softened the gusts and let the ember breathe without going bare",
        tags={"lantern", "fire"},
    ),
    "braided_hood": Carrier(
        id="braided_hood",
        label="braided reed hood",
        phrase="a braided reed hood lined with clay",
        sense=2,
        guards={"drizzle", "mist"},
        image="reeds crossed like a nest around clay",
        warning="Quick hands alone could not keep the ember safe.",
        success="the clay lining held the heat while the woven hood turned the damp away",
        tags={"reed", "fire"},
    ),
    "open_shell": Carrier(
        id="open_shell",
        label="open shell",
        phrase="an open shell in two cupped hands",
        sense=1,
        guards=set(),
        image="pale and pretty, but bare",
        warning="It looked swift, but it left the little fire naked to weather.",
        success="",
        tags={"shell"},
    ),
}

FUELS = {
    "faggot": Fuel(
        id="faggot",
        label="faggot",
        phrase="a small faggot of dry sticks tied with rushes",
        burn=3,
        dry=True,
        kindling_text="The tied sticks would feed the ember a little at a time and keep a warm pocket around it.",
        ending_text="the faggot of dry sticks gave off a slow, patient heat",
        tags={"sticks", "kindling", "faggot"},
    ),
    "pine_cones": Fuel(
        id="pine_cones",
        label="pine cones",
        phrase="three resin-rich pine cones in a cloth pouch",
        burn=2,
        dry=True,
        kindling_text="Their resin would help the coal hold on through the dark parts of the walk.",
        ending_text="the pine cones smoldered sweetly",
        tags={"pine", "kindling"},
    ),
    "moss_nest": Fuel(
        id="moss_nest",
        label="moss nest",
        phrase="a nest of dry moss and cedar bark",
        burn=2,
        dry=True,
        kindling_text="The soft nest would cradle the ember and let it eat slowly.",
        ending_text="the moss and cedar bark glowed gently under the coal",
        tags={"moss", "kindling"},
    ),
    "leaf_scraps": Fuel(
        id="leaf_scraps",
        label="leaf scraps",
        phrase="a handful of leaf scraps",
        burn=1,
        dry=True,
        kindling_text="The leaves would flash, but not for long.",
        ending_text="the last leaf-curled sparks faded fast",
        tags={"leaves"},
    ),
}

GIRL_NAMES = ["Iria", "Nera", "Tala", "Mira", "Seli", "Luma"]
BOY_NAMES = ["Daran", "Oren", "Pavel", "Tarin", "Milo", "Soren"]
TRAITS = ["brave", "careful", "thoughtful", "quick", "steady"]


@dataclass
class StoryParams:
    quest: str
    hazard: str
    carrier: str
    fuel: str
    hero_name: str
    hero_gender: str
    elder_type: str
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
    "faggot": [
        (
            "What does the word faggot mean in this story?",
            "Here it means a tied bundle of sticks used for carrying or burning as fuel. In the story, the child uses a small faggot of dry sticks to help keep the ember alive.",
        )
    ],
    "kindling": [
        (
            "What is kindling?",
            "Kindling is small, dry material that catches fire more easily than big logs. People use it to help a fire start or stay alive.",
        )
    ],
    "ember": [
        (
            "What is an ember?",
            "An ember is a small, glowing piece of fire that stays hot after the flame grows small. A careful person can use an ember to start a new fire.",
        )
    ],
    "wind": [
        (
            "Why can wind be bad for a little fire?",
            "Wind can blow heat away from a weak fire and scatter its tiny glowing bits. A small ember needs shelter so it does not fade.",
        )
    ],
    "rain": [
        (
            "Why is drizzle dangerous for an ember?",
            "Even small drops of water can cool an ember and put it out. That is why a carrier with cover matters in the story.",
        )
    ],
    "mist": [
        (
            "Why can damp mist trouble a spark?",
            "Mist fills the air with moisture, and moisture steals heat from a weak spark. A sheltered ember lasts longer.",
        )
    ],
    "pot": [
        (
            "Why is a clay ember pot useful?",
            "Clay can hold warmth and a lid can shield a coal from weather. That makes an ember pot a smart tool for carrying fire safely.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do for a small flame?",
            "A lantern gives the fire walls around it, so moving air cannot hit it as hard. In stories and in real life, that protection helps a small light survive.",
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is wrong, thinking about why it is wrong, and choosing a plan that truly helps. The child in the story solves the problem before starting the walk.",
        )
    ],
}
KNOWLEDGE_ORDER = ["faggot", "kindling", "ember", "wind", "rain", "mist", "pot", "lantern", "problem_solving"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    hazard = f["hazard"]
    carrier = f["carrier"]
    fuel = f["fuel"]
    return [
        f'Write a short myth for a young child about carrying a sacred ember home, and include the word "{fuel.label}".',
        f"Tell a myth-like story where {hero.id} must bring fire from {quest.source} to {quest.goal} while facing {hazard.phrase}, and solves the problem by choosing {carrier.phrase}.",
        "Write a gentle myth about wisdom instead of strength, where a child studies a danger, chooses a careful plan, and brings warmth back to the village.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    quest = f["quest"]
    hazard = f["hazard"]
    carrier = f["carrier"]
    fuel = f["fuel"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child from {quest.village}, and {elder.id}, the village {elder.label_word}. Together they work out how to carry a sacred ember home.",
        ),
        (
            "What problem did the child need to solve?",
            f"{hero.id} had to bring a live ember from {quest.source} to {quest.goal}. The problem was that {hazard.threat}, so a bare coal would not make it safely home.",
        ),
        (
            f"Why was {hazard.label} a danger?",
            f"{hazard.phrase.capitalize()} could hurt the ember on the way. That mattered because the village needed the ember to light the hearth again.",
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} did not just hurry and hope. {hero.pronoun().capitalize()} used {carrier.phrase} and {fuel.phrase}, so the ember was both sheltered and fed on the journey.",
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                "How do we know the plan worked?",
                f"The ember reached {quest.goal} still glowing, and the hearth lit again. That shows the plan matched the danger instead of guessing at it.",
            )
        )
    if fuel.id == "faggot":
        qa.append(
            (
                "What was the faggot used for in the story?",
                f"In this story, the faggot was a tied bundle of dry sticks. It fed the ember slowly and helped keep a warm pocket around it while {hero.id} walked.",
            )
        )
    if world.facts.get("predicted_arrival"):
        qa.append(
            (
                f"What did {elder.id} understand before the walk began?",
                f"{elder.id} understood that a wise answer had to do two jobs at once: protect the ember and keep it hot enough. Because of that, the child solved the hardest part before stepping onto the path.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ember", "kindling", "problem_solving"}
    hazard = world.facts["hazard"]
    carrier = world.facts["carrier"]
    fuel = world.facts["fuel"]
    if hazard.id == "wind":
        tags.add("wind")
    if hazard.id == "drizzle":
        tags.add("rain")
    if hazard.id == "mist":
        tags.add("mist")
    tags |= set(carrier.tags)
    tags |= set(fuel.tags)
    if "faggot" in fuel.tags:
        tags.add("faggot")
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
        if e.attrs:
            shown = {}
            for k, v in e.attrs.items():
                shown[k] = sorted(v) if isinstance(v, set) else v
            bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="sun_hill",
        hazard="wind",
        carrier="ember_pot",
        fuel="faggot",
        hero_name="Iria",
        hero_gender="girl",
        elder_type="priestess",
        trait="thoughtful",
    ),
    StoryParams(
        quest="moon_cave",
        hazard="mist",
        carrier="horn_lantern",
        fuel="pine_cones",
        hero_name="Oren",
        hero_gender="boy",
        elder_type="grandfather",
        trait="steady",
    ),
    StoryParams(
        quest="sun_hill",
        hazard="drizzle",
        carrier="braided_hood",
        fuel="moss_nest",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="grandmother",
        trait="careful",
    ),
    StoryParams(
        quest="oak_spring",
        hazard="wind",
        carrier="ember_pot",
        fuel="faggot",
        hero_name="Tarin",
        hero_gender="boy",
        elder_type="priest",
        trait="brave",
    ),
    StoryParams(
        quest="moon_cave",
        hazard="wind",
        carrier="horn_lantern",
        fuel="faggot",
        hero_name="Seli",
        hero_gender="girl",
        elder_type="priestess",
        trait="quick",
    ),
]


ASP_RULES = r"""
% A valid solution needs a sensible carrier, protection from the hazard,
% and enough total heat to survive the trip.

sensible_carrier(C) :- carrier(C), sense(C, S), sense_min(M), S >= M.
protects(C, H) :- guards(C, H).
base_heat(2).

remaining_heat(Q, H, C, F, B - Pen + Burn) :-
    quest(Q), hazard(H), carrier(C), fuel(F),
    base_heat(B), distance(Q, D), intensity(H, I), burn(F, Burn),
    protects(C, H), Pen = 0, D >= 0.

remaining_heat(Q, H, C, F, B - Pen + Burn) :-
    quest(Q), hazard(H), carrier(C), fuel(F),
    base_heat(B), distance(Q, D), intensity(H, I), burn(F, Burn),
    not protects(C, H), Pen = I, D >= 0.

lasts(Q, H, C, F) :-
    remaining_heat(Q, H, C, F, R),
    distance(Q, D),
    R >= D.

valid(Q, H, C, F) :-
    quest(Q), hazard(H), carrier(C), fuel(F),
    sensible_carrier(C), protects(C, H), lasts(Q, H, C, F).

success(Q, H, C, F) :- valid(Q, H, C, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("distance", qid, q.distance))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("intensity", hid, h.intensity))
    for cid, c in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        for h in sorted(c.guards):
            lines.append(asp.fact("guards", cid, h))
    for fid, f in FUELS.items():
        lines.append(asp.fact("fuel", fid))
        lines.append(asp.fact("burn", fid, f.burn))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_success(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_quest", params.quest),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_carrier", params.carrier),
            asp.fact("chosen_fuel", params.fuel),
            "picked_success :- success(Q,H,C,F), chosen_quest(Q), chosen_hazard(H), chosen_carrier(C), chosen_fuel(F).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_success/0."))
    return bool(asp.atoms(model, "picked_success"))


def outcome_of(params: StoryParams) -> str:
    if params.quest not in QUESTS or params.hazard not in HAZARDS or params.carrier not in CARRIERS or params.fuel not in FUELS:
        return "invalid"
    return "success" if valid_solution(QUESTS[params.quest], HAZARDS[params.hazard], CARRIERS[params.carrier], FUELS[params.fuel]) else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combo gate matches ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad = 0
    for p in cases:
        py_ok = outcome_of(p) == "success"
        asp_ok = asp_success(p)
        if py_ok != asp_ok:
            bad += 1
    if bad == 0:
        print(f"OK: success model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} success judgements differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation passed.")
    except Exception as err:  # pragma: no cover - explicit verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child solves how to carry sacred fire home in a mythic world."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--fuel", choices=FUELS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--elder", choices=["priestess", "priest", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.hazard and args.carrier and args.fuel:
        q = QUESTS[args.quest]
        h = HAZARDS[args.hazard]
        c = CARRIERS[args.carrier]
        f = FUELS[args.fuel]
        if not valid_solution(q, h, c, f):
            raise StoryError(explain_rejection(q, h, c, f))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.carrier is None or combo[2] == args.carrier)
        and (args.fuel is None or combo[3] == args.fuel)
    ]
    if not combos:
        qid = args.quest or next(iter(QUESTS))
        hid = args.hazard or next(iter(HAZARDS))
        cid = args.carrier or next(iter(CARRIERS))
        fid = args.fuel or next(iter(FUELS))
        raise StoryError(explain_rejection(QUESTS[qid], HAZARDS[hid], CARRIERS[cid], FUELS[fid]))

    quest, hazard, carrier, fuel = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.hero_name or rng.choice(name_pool)
    elder_type = args.elder or rng.choice(["priestess", "priest", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        quest=quest,
        hazard=hazard,
        carrier=carrier,
        fuel=fuel,
        hero_name=hero_name,
        hero_gender=gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.fuel not in FUELS:
        raise StoryError(f"(Unknown fuel: {params.fuel})")
    quest = QUESTS[params.quest]
    hazard = HAZARDS[params.hazard]
    carrier = CARRIERS[params.carrier]
    fuel = FUELS[params.fuel]
    if not valid_solution(quest, hazard, carrier, fuel):
        raise StoryError(explain_rejection(quest, hazard, carrier, fuel))
    world = tell(
        quest=quest,
        hazard=hazard,
        carrier=carrier,
        fuel=fuel,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/4.\n#show success/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, hazard, carrier, fuel) combos:\n")
        for q, h, c, f in combos:
            print(f"  {q:10} {h:8} {c:13} {f}")
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
            header = f"### {p.hero_name}: {p.quest}, {p.hazard}, {p.carrier}, {p.fuel}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
