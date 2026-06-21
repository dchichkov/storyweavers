#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/power_ful_law_teamwork_nursery_rhyme.py
=================================================================

A standalone story world for a gentle nursery-rhyme-style tale about small
friends who learn that a simple lane law makes them stronger together:
when a load is too much for one, teamwork makes little bodies feel
"power-ful".

This world models a tiny hauling problem:
- one small hero tries to move a load along a path,
- the path and cargo together may be too much for one child,
- a bumpy path can also make a delicate or sloshy load wobble,
- two friends can help by pushing and/or steadying,
- the ending proves what changed: the load arrives because they worked
  together and followed the law of the lane.

Run it
------
    python storyworlds/worlds/gpt-5.4/power_ful_law_teamwork_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/power_ful_law_teamwork_nursery_rhyme.py --cargo soup_pot --vehicle wagon --path cobbles
    python storyworlds/worlds/gpt-5.4/power_ful_law_teamwork_nursery_rhyme.py --cargo pumpkin --vehicle tray
    python storyworlds/worlds/gpt-5.4/power_ful_law_teamwork_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/power_ful_law_teamwork_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/power_ful_law_teamwork_nursery_rhyme.py --verify
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
from contextlib import redirect_stdout
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
        female = {"girl", "hen", "duck", "goose", "mother", "woman"}
        male = {"boy", "rooster", "drake", "father", "man"}
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
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    wobble: int
    delicate: bool
    aroma: str
    ending_image: str
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
class Vehicle:
    id: str
    label: str
    phrase: str
    capacity: int
    base_force: int
    stability: int
    rhyme_sound: str
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
class Pathway:
    id: str
    label: str
    phrase: str
    pull_need: int
    bump: int
    scene: str
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


def challenge(cargo: Cargo, path: Pathway) -> int:
    return cargo.weight + path.pull_need


def steady_needed(cargo: Cargo, vehicle: Vehicle, path: Pathway) -> bool:
    return cargo.wobble + path.bump > vehicle.stability


def team_force(vehicle: Vehicle, cargo: Cargo, path: Pathway) -> int:
    helpers_pushing = 1 if steady_needed(cargo, vehicle, path) else 2
    return vehicle.base_force + 1 + helpers_pushing


def solo_force(vehicle: Vehicle) -> int:
    return vehicle.base_force + 1


def cargo_fits(cargo: Cargo, vehicle: Vehicle) -> bool:
    return cargo.weight <= vehicle.capacity


def valid_combo(cargo: Cargo, vehicle: Vehicle, path: Pathway) -> bool:
    if not cargo_fits(cargo, vehicle):
        return False
    need = challenge(cargo, path)
    if solo_force(vehicle) >= need:
        return False
    if team_force(vehicle, cargo, path) < need:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cargo_id, cargo in CARGOS.items():
        for vehicle_id, vehicle in VEHICLES.items():
            for path_id, path in PATHS.items():
                if valid_combo(cargo, vehicle, path):
                    combos.append((cargo_id, vehicle_id, path_id))
    return combos


def _r_strain(world: World) -> list[str]:
    hero = world.get("hero")
    cart = world.get("vehicle")
    cargo = world.get("cargo")
    if world.facts["mode"] != "solo_try":
        return []
    sig = ("strain",)
    if sig in world.fired:
        return []
    if hero.meters["pull"] >= world.facts["need"] and cart.meters["loaded"] >= THRESHOLD:
        return []
    world.fired.add(sig)
    cart.meters["stuck"] += 1
    hero.memes["strain"] += 1
    hero.memes["frustration"] += 1
    return ["__stuck__"]


def _r_wobble(world: World) -> list[str]:
    cart = world.get("vehicle")
    cargo = world.get("cargo")
    if cart.meters["loaded"] < THRESHOLD:
        return []
    if world.facts["mode"] not in {"solo_try", "team_try"}:
        return []
    sig = ("wobble", world.facts["mode"])
    if sig in world.fired:
        return []
    if not world.facts["needs_steady"]:
        return []
    if world.facts["mode"] == "team_try" and world.facts["steadying"]:
        return []
    world.fired.add(sig)
    cargo.meters["wobble"] += 1
    return ["__wobble__"]


def _r_move(world: World) -> list[str]:
    hero = world.get("hero")
    cart = world.get("vehicle")
    if cart.meters["loaded"] < THRESHOLD:
        return []
    sig = ("move", world.facts["mode"])
    if sig in world.fired:
        return []
    if hero.meters["pull"] < world.facts["need"]:
        return []
    world.fired.add(sig)
    cart.meters["rolled"] += 1
    return ["__rolled__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="strain", tag="physical", apply=_r_strain),
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="move", tag="physical", apply=_r_move),
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


def predict(world: World, *, mode: str, steadying: bool) -> dict:
    sim = world.copy()
    sim.facts["mode"] = mode
    sim.facts["steadying"] = steadying
    hero = sim.get("hero")
    hero.meters["pull"] = float(team_force(CARGOS[sim.facts["cargo_id"]], VEHICLES[sim.facts["vehicle_id"]], PATHS[sim.facts["path_id"]])) if mode == "team_try" else float(solo_force(VEHICLES[sim.facts["vehicle_id"]]))
    propagate(sim, narrate=False)
    return {
        "stuck": sim.get("vehicle").meters["stuck"] >= THRESHOLD,
        "wobble": sim.get("cargo").meters["wobble"] >= THRESHOLD,
        "rolled": sim.get("vehicle").meters["rolled"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper1: Entity, helper2: Entity, path: Pathway) -> None:
    world.say(
        f"{hero.id} and {helper1.id} and {helper2.id}, three small friends in morning light, "
        f"skipped to {path.phrase} where daisies nodded white."
    )


def show_load(world: World, hero: Entity, cargo: Cargo, vehicle: Vehicle) -> None:
    world.say(
        f"There waited {cargo.phrase} in {vehicle.phrase} -- "
        f"{cargo.aroma}, snug and bright."
    )


def nursery_goal(world: World, cargo: Cargo) -> None:
    world.say(
        f"It was meant for the noon-time cloth, where lunch and laughter would sit just right."
    )


def law_sign(world: World, path: Pathway) -> None:
    world.say(
        f"By {path.label} stood a painted sign with a jingly little law: "
        f'"When wheels feel heavy, friends pull true; when things wobble, paws must stay in awe."'
    )


def try_alone(world: World, hero: Entity, cargo: Cargo, vehicle: Vehicle, path: Pathway) -> None:
    world.facts["mode"] = "solo_try"
    world.facts["steadying"] = False
    hero.meters["pull"] = float(solo_force(vehicle))
    hero.memes["eager"] += 1
    world.say(
        f'"I can do it by myself," sang {hero.id}, and {hero.pronoun()} gave the {vehicle.label} a tug.'
    )
    propagate(world, narrate=False)
    if world.get("vehicle").meters["stuck"] >= THRESHOLD:
        hero.memes["worry"] += 1
        world.say(
            f"But the {vehicle.label} gave only a grunt and a nudge, for {path.label} was not a gentle rug."
        )
    if world.get("cargo").meters["wobble"] >= THRESHOLD:
        world.say(
            f"The {cargo.label} wibbled and wobbled and made {hero.id} bite {hero.pronoun('possessive')} lip."
        )


def explain_turn(world: World, hero: Entity, helper1: Entity, helper2: Entity, cargo: Cargo, vehicle: Vehicle, path: Pathway) -> None:
    solo = predict(world, mode="solo_try", steadying=False)
    team = predict(world, mode="team_try", steadying=steady_needed(cargo, vehicle, path))
    world.facts["solo_prediction"] = solo
    world.facts["team_prediction"] = team
    world.say(
        f"{helper1.id} tapped the sign. {helper2.id} read it twice. "
        f'"That is the lane law," {helper2.pronoun()} said. '
        f'"One alone may puff and puff, but together we are power-ful."'
    )


def assign_teamwork(world: World, hero: Entity, helper1: Entity, helper2: Entity, cargo: Cargo, vehicle: Vehicle, path: Pathway) -> None:
    needs_steady = steady_needed(cargo, vehicle, path)
    world.facts["mode"] = "team_try"
    world.facts["steadying"] = needs_steady
    hero.meters["pull"] = float(team_force(vehicle, cargo, path))
    helper1.memes["helping"] += 1
    helper2.memes["helping"] += 1
    hero.memes["hope"] += 1
    if needs_steady:
        world.facts["roles"] = {"hero": "pull", "helper1": "push", "helper2": "steady"}
        world.say(
            f"So {hero.id} took the handle, {helper1.id} leaned in to push, "
            f"and {helper2.id} walked beside to keep the {cargo.label} from swaying."
        )
    else:
        world.facts["roles"] = {"hero": "pull", "helper1": "push", "helper2": "push"}
        world.say(
            f"So {hero.id} took the handle, and {helper1.id} and {helper2.id} came behind with cheerful shoes to push."
        )


def team_move(world: World, hero: Entity, helper1: Entity, helper2: Entity, cargo: Cargo, vehicle: Vehicle, path: Pathway) -> None:
    propagate(world, narrate=False)
    world.say(
        f"They counted, " + '"One, two, three!" ' +
        f"and wheels went bump, and little feet went patter-pat through {path.scene}."
    )
    if world.get("cargo").meters["wobble"] >= THRESHOLD:
        raise StoryError("(Internal inconsistency: the team attempt still let the cargo wobble.)")
    if world.get("vehicle").meters["rolled"] < THRESHOLD:
        raise StoryError("(Internal inconsistency: the team attempt did not move the load.)")
    hero.memes["joy"] += 1
    helper1.memes["joy"] += 1
    helper2.memes["joy"] += 1
    world.say(
        f"Over went the hard part, through went the {vehicle.label}, and nobody spilled a drop or squashed a crumb."
    )


def ending(world: World, hero: Entity, helper1: Entity, helper2: Entity, cargo: Cargo) -> None:
    hero.memes["lesson"] += 1
    helper1.memes["lesson"] += 1
    helper2.memes["lesson"] += 1
    world.say(
        f"At the cloth they set it down, and there was {cargo.ending_image}."
    )
    world.say(
        f'Then {hero.id} laughed, "{cargo.label.capitalize()} came through because we worked as one." '
        f'And from that day on, the three friends liked the little law.'
    )


def tell(cargo: Cargo, vehicle: Vehicle, path: Pathway,
         hero_name: str, hero_type: str,
         helper1_name: str, helper1_type: str,
         helper2_name: str, helper2_type: str) -> World:
    if not valid_combo(cargo, vehicle, path):
        raise StoryError(explain_rejection(cargo, vehicle, path))

    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    helper1 = world.add(Entity(id=helper1_name, kind="character", type=helper1_type, role="helper", label=helper1_name))
    helper2 = world.add(Entity(id=helper2_name, kind="character", type=helper2_type, role="helper", label=helper2_name))
    vehicle_ent = world.add(Entity(id="vehicle", type="vehicle", label=vehicle.label))
    cargo_ent = world.add(Entity(id="cargo", type="cargo", label=cargo.label))

    world.facts.update(
        cargo_id=cargo.id,
        vehicle_id=vehicle.id,
        path_id=path.id,
        cargo=cargo,
        vehicle=vehicle,
        path=path,
        hero=hero,
        helper1=helper1,
        helper2=helper2,
        need=challenge(cargo, path),
        needs_steady=steady_needed(cargo, vehicle, path),
        mode="setup",
        steadying=False,
        roles={},
    )

    vehicle_ent.meters["loaded"] = 1.0
    cargo_ent.meters["packed"] = 1.0
    hero.meters["pull"] = 0.0

    introduce(world, hero, helper1, helper2, path)
    show_load(world, hero, cargo, vehicle)
    nursery_goal(world, cargo)

    world.para()
    law_sign(world, path)
    try_alone(world, hero, cargo, vehicle, path)

    world.para()
    explain_turn(world, hero, helper1, helper2, cargo, vehicle, path)
    assign_teamwork(world, hero, helper1, helper2, cargo, vehicle, path)
    team_move(world, hero, helper1, helper2, cargo, vehicle, path)

    world.para()
    ending(world, hero, helper1, helper2, cargo)

    world.facts.update(
        outcome="team_success",
        stuck=vehicle_ent.meters["stuck"] >= THRESHOLD,
        wobbled=cargo_ent.meters["wobble"] >= THRESHOLD,
        moved=vehicle_ent.meters["rolled"] >= THRESHOLD,
    )
    return world


CARGOS = {
    "soup_pot": Cargo(
        id="soup_pot",
        label="soup pot",
        phrase="a round soup pot with a lid that chimed",
        weight=2,
        wobble=2,
        delicate=False,
        aroma="warm carrot steam curled up in the air",
        ending_image="three bowls steaming in a row and spoons shining like moons",
        tags={"soup", "teamwork"},
    ),
    "berry_tart": Cargo(
        id="berry_tart",
        label="berry tart",
        phrase="a berry tart with a shiny crust",
        weight=1,
        wobble=2,
        delicate=True,
        aroma="sweet berry smell floated after it",
        ending_image="purple berries gleaming while crumbs stayed neatly in their place",
        tags={"tart", "baking", "teamwork"},
    ),
    "pumpkin": Cargo(
        id="pumpkin",
        label="pumpkin",
        phrase="a plump orange pumpkin with a curly stem",
        weight=3,
        wobble=0,
        delicate=False,
        aroma="it smelled like earth and autumn leaves",
        ending_image="a bright pumpkin sitting proud beside the picnic bread",
        tags={"pumpkin", "harvest", "teamwork"},
    ),
    "seed_basket": Cargo(
        id="seed_basket",
        label="seed basket",
        phrase="a seed basket tied with blue ribbon",
        weight=2,
        wobble=1,
        delicate=True,
        aroma="it rustled with husks and sunny grain",
        ending_image="golden seeds pouring safely into waiting little hands",
        tags={"seeds", "garden", "teamwork"},
    ),
}

VEHICLES = {
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="a red wagon",
        capacity=3,
        base_force=1,
        stability=2,
        rhyme_sound="agon",
        tags={"wagon"},
    ),
    "barrow": Vehicle(
        id="barrow",
        label="barrow",
        phrase="a blue garden barrow",
        capacity=3,
        base_force=0,
        stability=2,
        rhyme_sound="arrow",
        tags={"barrow", "garden"},
    ),
    "tray": Vehicle(
        id="tray",
        label="tray",
        phrase="a flat wooden tray",
        capacity=1,
        base_force=0,
        stability=0,
        rhyme_sound="ay",
        tags={"tray"},
    ),
}

PATHS = {
    "cobbles": Pathway(
        id="cobbles",
        label="the cobbles",
        phrase="the old cobbled lane",
        pull_need=1,
        bump=2,
        scene="the click-clack lane",
        tags={"cobbles", "bumpy"},
    ),
    "windy_lane": Pathway(
        id="windy_lane",
        label="the windy lane",
        phrase="the windy lane by the hedge",
        pull_need=1,
        bump=1,
        scene="the breezy hedge-side bend",
        tags={"wind", "path"},
    ),
    "little_hill": Pathway(
        id="little_hill",
        label="the little hill",
        phrase="the little hill by the willow",
        pull_need=2,
        bump=0,
        scene="the green rise under the willow",
        tags={"hill", "path"},
    ),
}

GIRL_NAMES = ["Pip", "Molly", "Tansy", "Wren", "Daisy", "Mina", "Poppy", "Dot"]
BOY_NAMES = ["Ben", "Tob", "Ned", "Rory", "Finn", "Milo", "Pipkin", "Tom"]
KINDS = {
    "girl": "girl",
    "boy": "boy",
    "duck": "duck",
    "hen": "hen",
    "goose": "goose",
}
TRAIT_TYPES = ["girl", "boy", "duck", "hen"]


@dataclass
class StoryParams:
    cargo: str
    vehicle: str
    path: str
    hero_name: str
    hero_type: str
    helper1_name: str
    helper1_type: str
    helper2_name: str
    helper2_type: str
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
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other do one job together. When they share the work, hard things can become possible."
        )
    ],
    "law": [
        (
            "What can the word law mean in a simple story?",
            "In a simple story, a law can mean a rule everyone agrees to follow. It helps people know the safe or sensible way to do something."
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon is a small cart with wheels for carrying things. Wheels help with the load, but someone still has to pull or push."
        )
    ],
    "barrow": [
        (
            "What is a garden barrow?",
            "A garden barrow is a little cart used to move things like soil, pumpkins, or tools. It helps carry weight, but balance still matters."
        )
    ],
    "tray": [
        (
            "Why is a tray hard to carry on a bumpy path?",
            "A tray is flat and open, so things can wobble on it. On a bumpy path, a tray needs very careful hands."
        )
    ],
    "cobbles": [
        (
            "Why do cobbles make wheels bump?",
            "Cobbles are uneven stones, so wheels hop from one hard piece to the next. That makes a cart shake and rattle."
        )
    ],
    "hill": [
        (
            "Why is it harder to push something up a hill?",
            "A hill lifts the load upward as you move, so your body has to work harder. Heavy things feel even heavier going uphill."
        )
    ],
    "wind": [
        (
            "How can wind make carrying harder?",
            "Wind can push against you and make a light load wobble. It can also make you slow down or lean harder."
        )
    ],
    "soup": [
        (
            "Why does soup wobble when a cart bumps?",
            "Soup is liquid, so it moves and sloshes when the pot shakes. A steady hand helps keep it from spilling."
        )
    ],
    "tart": [
        (
            "Why should a tart be carried carefully?",
            "A tart has a soft top and a delicate crust. If it tips or jolts too much, the filling can slide and the crust can crack."
        )
    ],
    "pumpkin": [
        (
            "Why is a pumpkin hard to move?",
            "A pumpkin can be round and heavy, so it takes a strong push or pull to get it rolling. Its weight is the hard part, even if it does not slosh."
        )
    ],
    "seeds": [
        (
            "Why are seeds worth carrying carefully?",
            "Seeds are small, but they are important because they can grow into plants later. If they spill in the wrong place, they are hard to gather again."
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "law", "wagon", "barrow", "tray", "cobbles", "hill", "wind", "soup", "tart", "pumpkin", "seeds"]


CURATED = [
    StoryParams(
        cargo="soup_pot",
        vehicle="wagon",
        path="cobbles",
        hero_name="Pip",
        hero_type="girl",
        helper1_name="Ben",
        helper1_type="boy",
        helper2_name="Dot",
        helper2_type="duck",
        seed=None,
    ),
    StoryParams(
        cargo="pumpkin",
        vehicle="wagon",
        path="little_hill",
        hero_name="Molly",
        hero_type="girl",
        helper1_name="Tom",
        helper1_type="boy",
        helper2_name="Wren",
        helper2_type="hen",
        seed=None,
    ),
    StoryParams(
        cargo="berry_tart",
        vehicle="barrow",
        path="windy_lane",
        hero_name="Daisy",
        hero_type="hen",
        helper1_name="Finn",
        helper1_type="boy",
        helper2_name="Mina",
        helper2_type="girl",
        seed=None,
    ),
    StoryParams(
        cargo="seed_basket",
        vehicle="barrow",
        path="little_hill",
        hero_name="Tansy",
        hero_type="girl",
        helper1_name="Ned",
        helper1_type="boy",
        helper2_name="Poppy",
        helper2_type="girl",
        seed=None,
    ),
]


def explain_rejection(cargo: Cargo, vehicle: Vehicle, path: Pathway) -> str:
    if not cargo_fits(cargo, vehicle):
        return (
            f"(No story: {cargo.label} is too heavy for the {vehicle.label}. "
            f"The vehicle cannot honestly carry that load.)"
        )
    need = challenge(cargo, path)
    if solo_force(vehicle) >= need:
        return (
            f"(No story: {vehicle.label} on {path.label} makes the job too easy for one child. "
            f"This world wants a real teamwork turn, so pick a heavier load or harder path.)"
        )
    return (
        f"(No story: even with teamwork, a {vehicle.label} cannot move {cargo.label} across {path.label}. "
        f"Pick a steadier or stronger vehicle, or an easier path.)"
    )


def generation_prompts(world: World) -> list[str]:
    cargo = world.facts["cargo"]
    path = world.facts["path"]
    hero = world.facts["hero"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "power-ful" and "law".',
        f"Tell a gentle story where {hero.id} tries to move a {cargo.label} alone, fails, and then succeeds through teamwork on {path.label}.",
        f"Write a rhythmic story in which a little sign teaches a simple law: friends who pull together can do a hard job safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    cargo = world.facts["cargo"]
    vehicle = world.facts["vehicle"]
    path = world.facts["path"]
    hero = world.facts["hero"]
    helper1 = world.facts["helper1"]
    helper2 = world.facts["helper2"]
    needs_steady = world.facts["needs_steady"]
    roles = world.facts["roles"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {helper1.id}, and {helper2.id}, three small friends moving a {cargo.label}. They begin with one child trying alone, and they finish by helping each other."
        ),
        (
            f"Why could {hero.id} not move the {cargo.label} alone?",
            f"{hero.id} could not move it alone because the {path.label} and the load together were too hard for one small pull. The cart stuck before the job was done, so the problem was real and physical."
        ),
        (
            "What did the little sign say about the law?",
            "The sign taught that heavy wheels need friends pulling together, and wobbly things need steady hands too. That law gave the children a clear plan instead of more puffing and straining."
        ),
    ]
    if needs_steady:
        qa.append(
            (
                f"How did the friends share the job?",
                f"{hero.id} pulled, {helper1.id} pushed, and {helper2.id} steadied the {cargo.label}. They needed both strength and balance, because the path could make the load wobble."
            )
        )
    else:
        qa.append(
            (
                f"How did the friends share the job?",
                f"{hero.id} pulled while {helper1.id} and {helper2.id} pushed from behind. That gave the {vehicle.label} enough force to keep rolling."
            )
        )
    qa.append(
        (
            "Why did the story say they were power-ful?",
            f"It called them power-ful because they became stronger by working as one team. None of them changed size, but together they had enough force to move the load safely."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the {cargo.label} set down safely at the cloth, and the ending image showed {cargo.ending_image}. That happy picture proves the teamwork worked."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"teamwork", "law"}
    cargo = world.facts["cargo"]
    vehicle = world.facts["vehicle"]
    path = world.facts["path"]
    tags |= cargo.tags | vehicle.tags | path.tags
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: need={world.facts.get('need')} needs_steady={world.facts.get('needs_steady')} roles={world.facts.get('roles')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(C,V) :- cargo(C), vehicle(V), weight(C,W), capacity(V,Cap), W <= Cap.
need(C,P,N) :- weight(C,W), pull_need(P,Pu), N = W + Pu.
solo_force(V,S) :- base_force(V,B), S = B + 1.
needs_steady(C,V,P) :- wobble(C,Wb), bump(P,Bm), stability(V,St), Wb + Bm > St.
team_force(C,V,P,T) :- base_force(V,B), needs_steady(C,V,P), T = B + 2.
team_force(C,V,P,T) :- base_force(V,B), not needs_steady(C,V,P), T = B + 3.

valid(C,V,P) :- fits(C,V), need(C,P,N), solo_force(V,S), S < N, team_force(C,V,P,T), T >= N.

chosen_needs_steady :- chosen_cargo(C), chosen_vehicle(V), chosen_path(P), needs_steady(C,V,P).
chosen_need(N) :- chosen_cargo(C), chosen_path(P), need(C,P,N).
chosen_solo(S) :- chosen_vehicle(V), solo_force(V,S).
chosen_team(T) :- chosen_cargo(C), chosen_vehicle(V), chosen_path(P), team_force(C,V,P,T).

outcome(team_success) :- chosen_need(N), chosen_solo(S), chosen_team(T), S < N, T >= N.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cargo_id, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("weight", cargo_id, cargo.weight))
        lines.append(asp.fact("wobble", cargo_id, cargo.wobble))
    for vehicle_id, vehicle in VEHICLES.items():
        lines.append(asp.fact("vehicle", vehicle_id))
        lines.append(asp.fact("capacity", vehicle_id, vehicle.capacity))
        lines.append(asp.fact("base_force", vehicle_id, vehicle.base_force))
        lines.append(asp.fact("stability", vehicle_id, vehicle.stability))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("pull_need", path_id, path.pull_need))
        lines.append(asp.fact("bump", path_id, path.bump))
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
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_vehicle", params.vehicle),
        asp.fact("chosen_path", params.path),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    cargo = CARGOS[params.cargo]
    vehicle = VEHICLES[params.vehicle]
    path = PATHS[params.path]
    return "team_success" if valid_combo(cargo, vehicle, path) else "invalid"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
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
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        sink = io.StringIO()
        with redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme teamwork storyworld: a little law, a hard pull, and a power-ful team."
    )
    ap.add_argument("--cargo", choices=sorted(CARGOS))
    ap.add_argument("--vehicle", choices=sorted(VEHICLES))
    ap.add_argument("--path", choices=sorted(PATHS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, typ: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if typ in {"girl", "hen", "duck", "goose"} else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    if not choices:
        choices = [f"{typ}_{len(avoid)}"]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.vehicle and args.path:
        cargo = CARGOS[args.cargo]
        vehicle = VEHICLES[args.vehicle]
        path = PATHS[args.path]
        if not valid_combo(cargo, vehicle, path):
            raise StoryError(explain_rejection(cargo, vehicle, path))

    combos = [
        combo for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.vehicle is None or combo[1] == args.vehicle)
        and (args.path is None or combo[2] == args.path)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, vehicle_id, path_id = rng.choice(sorted(combos))
    types = [rng.choice(TRAIT_TYPES) for _ in range(3)]
    avoid: set[str] = set()
    hero_name = pick_name(rng, types[0], avoid)
    avoid.add(hero_name)
    helper1_name = pick_name(rng, types[1], avoid)
    avoid.add(helper1_name)
    helper2_name = pick_name(rng, types[2], avoid)
    return StoryParams(
        cargo=cargo_id,
        vehicle=vehicle_id,
        path=path_id,
        hero_name=hero_name,
        hero_type=types[0],
        helper1_name=helper1_name,
        helper1_type=types[1],
        helper2_name=helper2_name,
        helper2_type=types[2],
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGOS or params.vehicle not in VEHICLES or params.path not in PATHS:
        raise StoryError("(Invalid params: unknown cargo, vehicle, or path.)")
    world = tell(
        cargo=CARGOS[params.cargo],
        vehicle=VEHICLES[params.vehicle],
        path=PATHS[params.path],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper1_name=params.helper1_name,
        helper1_type=params.helper1_type,
        helper2_name=params.helper2_name,
        helper2_type=params.helper2_type,
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
        print(asp_program("", "#show valid/3.\n#show needs_steady/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cargo, vehicle, path) combos:\n")
        for cargo_id, vehicle_id, path_id in combos:
            cargo = CARGOS[cargo_id]
            vehicle = VEHICLES[vehicle_id]
            path = PATHS[path_id]
            steady = "steady" if steady_needed(cargo, vehicle, path) else "push-push"
            print(f"  {cargo_id:11} {vehicle_id:7} {path_id:11} [{steady}]")
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
            header = f"### {p.hero_name} and friends: {p.cargo} by {p.path} in a {p.vehicle}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
