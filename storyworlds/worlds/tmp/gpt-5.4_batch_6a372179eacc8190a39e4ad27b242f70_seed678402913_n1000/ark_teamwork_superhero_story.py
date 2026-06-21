#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ark_teamwork_superhero_story.py
=========================================================

A standalone story world sketch for a small child-facing superhero tale about
**building a rescue ark together before a storm reaches a town garden**.

The world model is built around one core common-sense constraint:

    if the danger is rising water,
    then the chosen transport must float,
    have enough room for the rescued animals,
    and be built by helpers whose skills cover the needed jobs.

That keeps the domain narrow and authored. The story is not a frozen paragraph
with swapped nouns: physical state (water, wobble, carrying capacity, repairs)
and emotional state (worry, courage, trust, pride) drive the turn and the
ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/ark_teamwork_superhero_story.py
    python storyworlds/worlds/gpt-5.4/ark_teamwork_superhero_story.py --hero cape_comet --place rooftop_garden
    python storyworlds/worlds/gpt-5.4/ark_teamwork_superhero_story.py --vessel wagon
    python storyworlds/worlds/gpt-5.4/ark_teamwork_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/ark_teamwork_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ark_teamwork_superhero_story.py --verify
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
SKILLS_NEEDED = {"lift", "build", "steer"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class HeroConfig:
    id: str
    name: str
    type: str
    title: str
    arrival: str
    power: str
    emblem: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PlaceConfig:
    id: str
    label: str
    opening: str
    shelter: str
    flood_path: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalGroup:
    id: str
    label: str
    count: int
    small_sound: str
    nervous_move: str
    tags: set[str] = field(default_factory=set)


@dataclass
class VesselConfig:
    id: str
    label: str
    phrase: str
    floats: bool
    capacity: int
    balance: int
    build_text: str
    launch_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolConfig:
    id: str
    label: str
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperConfig:
    id: str
    name: str
    type: str
    title: str
    skill: str
    assist_text: str
    cheer_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_rising_water(world: World) -> list[str]:
    out: list[str] = []
    weather = world.get("weather")
    if weather.meters["storm"] < THRESHOLD:
        return out
    place = world.get("place")
    sig = ("flood", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["water"] += 1
    for eid in ("hero", "helper1", "helper2"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    if "animals" in world.entities:
        world.get("animals").memes["fear"] += 1
    out.append("__water__")
    return out


def _r_too_many_animals(world: World) -> list[str]:
    out: list[str] = []
    if "vessel" not in world.entities or "animals" not in world.entities:
        return out
    vessel = world.get("vessel")
    animals = world.get("animals")
    if animals.attrs.get("count", 0) <= vessel.attrs.get("capacity", 0):
        return out
    sig = ("crowded", vessel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vessel.meters["crowded"] += 1
    vessel.meters["wobble"] += 1
    out.append("__crowded__")
    return out


def _r_unfixed_crack(world: World) -> list[str]:
    out: list[str] = []
    if "vessel" not in world.entities:
        return out
    vessel = world.get("vessel")
    if vessel.meters["crack"] < THRESHOLD or vessel.meters["patched"] >= THRESHOLD:
        return out
    sig = ("leak", vessel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vessel.meters["leak"] += 1
    vessel.meters["wobble"] += 1
    out.append("__leak__")
    return out


def _r_teamwork_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helpers = [world.get("helper1"), world.get("helper2")]
    vessel = world.get("vessel")
    animals = world.get("animals")
    if not all(h.memes["working"] >= THRESHOLD for h in helpers):
        return out
    if hero.memes["leading"] < THRESHOLD:
        return out
    if vessel.meters["ready"] < THRESHOLD:
        return out
    sig = ("calm", "team")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["pride"] += 1
    for h in helpers:
        h.memes["pride"] += 1
        h.memes["worry"] = 0.0
    animals.memes["fear"] = 0.0
    out.append("__calm__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="rising_water", tag="physical", apply=_r_rising_water),
    Rule(name="too_many_animals", tag="physical", apply=_r_too_many_animals),
    Rule(name="unfixed_crack", tag="physical", apply=_r_unfixed_crack),
    Rule(name="teamwork_calm", tag="social", apply=_r_teamwork_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


HEROES = {
    "cape_comet": HeroConfig(
        id="cape_comet",
        name="Cape Comet",
        type="girl",
        title="the sky-bright hero",
        arrival="swooped down in a blue cape that flashed like morning",
        power="could zip through the air and spot trouble fast",
        emblem="a silver star on her cape",
        tags={"hero", "superhero"},
    ),
    "bolt_ben": HeroConfig(
        id="bolt_ben",
        name="Bolt Ben",
        type="boy",
        title="the thunder-foot hero",
        arrival="ran in so quickly that his red boots hummed on the path",
        power="could dash from one side of the garden to the other in a blink",
        emblem="a yellow lightning mark on his shirt",
        tags={"hero", "superhero"},
    ),
    "glow_guard": HeroConfig(
        id="glow_guard",
        name="Glow Guard",
        type="girl",
        title="the lantern-heart hero",
        arrival="stepped in with a shining belt that made puddles sparkle",
        power="could make gentle circles of light so everyone could see the safe way",
        emblem="a glowing sun on her chest",
        tags={"hero", "superhero"},
    ),
}

PLACES = {
    "rooftop_garden": PlaceConfig(
        id="rooftop_garden",
        label="the rooftop garden",
        opening="Flower boxes lined the roof, and little stepping stones made a path between the tomatoes.",
        shelter="the high wooden tool shed",
        flood_path="rainwater would slide across the tiles and pool around the boxes first",
        ending_image="the moon shone on wet leaves high above the quiet street",
        tags={"garden", "roof"},
    ),
    "river_park": PlaceConfig(
        id="river_park",
        label="the river park",
        opening="Bright benches sat near the reeds, and a little play bridge crossed a shallow stream.",
        shelter="the painted picnic shelter",
        flood_path="the stream would spill over its banks and race across the grass",
        ending_image="the last raindrops glimmered beside the sleepy river",
        tags={"park", "river"},
    ),
    "school_garden": PlaceConfig(
        id="school_garden",
        label="the school garden",
        opening="Bean poles leaned in neat rows, and a tiny scarecrow watched over the carrots.",
        shelter="the brick garden room",
        flood_path="water would slide down the playground slope and swirl between the garden beds",
        ending_image="a rainbow rested over the school fence",
        tags={"garden", "school"},
    ),
}

ANIMALS = {
    "ducklings": AnimalGroup(
        id="ducklings",
        label="ducklings",
        count=3,
        small_sound="peep-peeped",
        nervous_move="huddled under one leaf and trembled",
        tags={"animals", "duck"},
    ),
    "bunnies": AnimalGroup(
        id="bunnies",
        label="bunnies",
        count=2,
        small_sound="made tiny nose-sniffing sounds",
        nervous_move="pressed close together beside the herbs",
        tags={"animals", "bunny"},
    ),
    "kittens": AnimalGroup(
        id="kittens",
        label="kittens",
        count=2,
        small_sound="mewed in thin squeaky voices",
        nervous_move="crouched in a seed tray and blinked at the rain",
        tags={"animals", "kitten"},
    ),
}

VESSELS = {
    "crate_ark": VesselConfig(
        id="crate_ark",
        label="ark",
        phrase="a sturdy little ark made from a fruit crate and sealed boards",
        floats=True,
        capacity=3,
        balance=2,
        build_text="turned a fruit crate, two wide boards, and a coil of rope into a little ark",
        launch_text="set the ark onto the rising water and held it steady",
        tags={"ark", "boat", "float"},
    ),
    "tub_ark": VesselConfig(
        id="tub_ark",
        label="ark",
        phrase="a round wash-tub ark with rope handles",
        floats=True,
        capacity=2,
        balance=2,
        build_text="pulled over a big wash tub and fixed rope handles on its sides to make an ark",
        launch_text="lowered the tub ark onto the water and kept it from spinning",
        tags={"ark", "boat", "float"},
    ),
    "wagon": VesselConfig(
        id="wagon",
        label="wagon",
        phrase="a red garden wagon",
        floats=False,
        capacity=3,
        balance=1,
        build_text="rolled up a red garden wagon and tried to use it like a boat",
        launch_text="pushed the wagon toward the water",
        tags={"wagon", "wheels"},
    ),
}

TOOLS = {
    "rope": ToolConfig(
        id="rope",
        label="rope",
        fixes={"steer"},
        tags={"rope"},
    ),
    "boards": ToolConfig(
        id="boards",
        label="boards",
        fixes={"build"},
        tags={"wood"},
    ),
    "sealant": ToolConfig(
        id="sealant",
        label="sticky patch tape",
        fixes={"patch"},
        tags={"repair", "patch"},
    ),
}

HELPERS = {
    "mighty_mina": HelperConfig(
        id="mighty_mina",
        name="Mighty Mina",
        type="girl",
        title="the strong helper",
        skill="lift",
        assist_text="used her strong arms to carry the heavy pieces without dropping them",
        cheer_text='"I can lift the big part!"',
        tags={"teamwork", "strength"},
    ),
    "fixit_finn": HelperConfig(
        id="fixit_finn",
        name="Fix-It Finn",
        type="boy",
        title="the careful builder",
        skill="build",
        assist_text="knelt right away and fitted the boards so no edges stuck out",
        cheer_text='"I can make the sides snug and safe!"',
        tags={"teamwork", "building"},
    ),
    "steady_sky": HelperConfig(
        id="steady_sky",
        name="Steady Sky",
        type="girl",
        title="the calm guide",
        skill="steer",
        assist_text="held the rope in both hands and kept the little craft pointed the right way",
        cheer_text='"I can guide us through the splashy part!"',
        tags={"teamwork", "steering"},
    ),
    "zip_zane": HelperConfig(
        id="zip_zane",
        name="Zip Zane",
        type="boy",
        title="the quick runner",
        skill="steer",
        assist_text="darted ahead and tied the rope where the water would pull least",
        cheer_text='"I can make a safe path!"',
        tags={"teamwork", "steering"},
    ),
}


def danger_is_reasonable(vessel: VesselConfig, animals: AnimalGroup) -> bool:
    return vessel.floats and vessel.capacity >= animals.count


def teamwork_ready(helper1: HelperConfig, helper2: HelperConfig) -> bool:
    skills = {helper1.skill, helper2.skill}
    return {"build", "steer"}.issubset(skills)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hero_id in HEROES:
        for place_id in PLACES:
            for animal_id, animal in ANIMALS.items():
                for vessel_id, vessel in VESSELS.items():
                    if danger_is_reasonable(vessel, animal):
                        combos.append((hero_id, place_id, animal_id, vessel_id))
    return combos


def valid_team_pairs() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    helper_ids = sorted(HELPERS)
    for i, h1 in enumerate(helper_ids):
        for h2 in helper_ids[i + 1:]:
            if teamwork_ready(HELPERS[h1], HELPERS[h2]):
                pairs.append((h1, h2))
    return pairs


def explain_vessel(vessel: VesselConfig, animal: AnimalGroup) -> str:
    if not vessel.floats:
        return (f"(No story: {vessel.phrase} has wheels, not a hull, so it will not float as an ark. "
                f"The rescue needs a real boat for rising water.)")
    if vessel.capacity < animal.count:
        return (f"(No story: {vessel.phrase} only holds {vessel.capacity}, but there are "
                f"{animal.count} {animal.label} to rescue. The ark must have room for everyone.)")
    return "(No story: this transport is not a reasonable ark for the rescue.)"


def explain_team(helper1: HelperConfig, helper2: HelperConfig) -> str:
    skills = sorted({helper1.skill, helper2.skill})
    return (f"(No story: {helper1.name} and {helper2.name} only cover {skills}. "
            f"The rescue team needs a builder and a guide so the ark can be made and steered safely.)")


def predict_rescue(world: World, tool_id: str) -> dict:
    sim = world.copy()
    vessel = sim.get("vessel")
    tool = TOOLS[tool_id]
    if "patch" in tool.fixes and vessel.meters["crack"] >= THRESHOLD:
        vessel.meters["patched"] += 1
    if "steer" in tool.fixes:
        vessel.meters["guided"] += 1
    if vessel.meters["crack"] >= THRESHOLD and vessel.meters["patched"] < THRESHOLD:
        propagate(sim, narrate=False)
    safe = vessel.meters["wobble"] < THRESHOLD and vessel.meters["leak"] < THRESHOLD
    return {"safe": safe, "wobble": vessel.meters["wobble"], "leak": vessel.meters["leak"]}


def open_scene(world: World, hero: Entity, place: PlaceConfig, animal: AnimalGroup) -> None:
    world.say(
        f"In {place.label}, {place.opening} The day looked bright at first."
    )
    world.say(
        f"Then dark clouds folded over the sky, and some {animal.label} {animal.nervous_move}."
    )
    world.say(
        f"{hero.attrs['hero_name']}, {hero.attrs['hero_title']}, {hero.attrs['arrival']} "
        f"{hero.pronoun().capitalize()} {hero.attrs['power']}."
    )


def spot_danger(world: World, hero: Entity, place: PlaceConfig, animals: Entity) -> None:
    world.get("weather").meters["storm"] += 1
    hero.memes["leading"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.attrs['hero_name']} looked at the clouds and knew {place.flood_path}."
    )
    world.say(
        f'The little {animals.label} {animals.attrs["small_sound"]}. '
        f'"We need an ark before the water gets there," {hero.pronoun()} said.'
    )


def call_team(world: World, hero: Entity, helper1: Entity, helper2: Entity) -> None:
    hero.memes["trust"] += 1
    helper1.memes["working"] += 1
    helper2.memes["working"] += 1
    world.say(
        f"{helper1.attrs['name']} hurried over first. {helper1.attrs['cheer_text']} "
        f"Then {helper2.attrs['name']} came too. {helper2.attrs['cheer_text']}"
    )
    world.say(
        f'{hero.attrs["hero_name"]} pointed to the rain and the frightened animals. '
        f'"I cannot do every part alone," {hero.pronoun()} said. "Let\'s work together."'
    )


def build_ark(world: World, hero: Entity, helper1: Entity, helper2: Entity, vessel_cfg: VesselConfig) -> None:
    vessel = world.get("vessel")
    vessel.meters["built"] += 1
    world.say(
        f"At once, the three heroes {vessel_cfg.build_text}. "
        f"{helper1.attrs['name']} {helper1.attrs['assist_text']}"
    )
    world.say(
        f"{helper2.attrs['name']} {helper2.attrs['assist_text']} "
        f"{hero.attrs['hero_name']} tied the last knot beneath {hero.attrs['emblem']}."
    )


def storm_turn(world: World, hero: Entity, tool_cfg: ToolConfig) -> None:
    vessel = world.get("vessel")
    animals = world.get("animals")
    vessel.meters["crack"] += 1
    propagate(world, narrate=False)
    pred = predict_rescue(world, tool_cfg.id)
    world.facts["predicted_leak"] = pred["leak"]
    world.facts["predicted_wobble"] = pred["wobble"]
    world.say(
        f"Just then, a gust slapped the side of the little ark against a stone step. "
        f"A crack opened with a small pop, and the {animals.label} pressed even closer together."
    )
    if pred["safe"]:
        world.say(
            f'{hero.attrs["hero_name"]} spotted the problem at once. '
            f'"Good thing we brought the {tool_cfg.label}," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f'{hero.attrs["hero_name"]} stared hard at the crack. '
            f'"Without the right help, this ark will wobble and leak," {hero.pronoun()} said.'
        )


def repair_and_launch(world: World, hero: Entity, helper1: Entity, helper2: Entity,
                      place: PlaceConfig, tool_cfg: ToolConfig, vessel_cfg: VesselConfig) -> None:
    vessel = world.get("vessel")
    animals = world.get("animals")
    if "patch" in tool_cfg.fixes:
        vessel.meters["patched"] += 1
        vessel.meters["crack"] = 0.0
    if helper1.attrs["skill"] == "steer" or helper2.attrs["skill"] == "steer":
        vessel.meters["guided"] += 1
    if vessel.meters["crowded"] < THRESHOLD and vessel.meters["leak"] < THRESHOLD:
        vessel.meters["ready"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper1.attrs['name']} and {helper2.attrs['name']} held the sides while "
        f"{hero.attrs['hero_name']} wrapped on the {tool_cfg.label}."
    )
    world.say(
        f"Together they tucked the {animals.label} inside, and then they {vessel_cfg.launch_text} "
        f"toward {place.shelter}."
    )


def safe_arrival(world: World, hero: Entity, helper1: Entity, helper2: Entity,
                 place: PlaceConfig, vessel_cfg: VesselConfig) -> None:
    animals = world.get("animals")
    hero.memes["relief"] += 1
    helper1.memes["relief"] += 1
    helper2.memes["relief"] += 1
    world.say(
        f"The water swished and bumped, but the little {vessel_cfg.label} stayed level. "
        f"Soon the {animals.label} were safe inside {place.shelter}."
    )
    world.say(
        f'{helper1.attrs["name"]} and {helper2.attrs["name"]} laughed with wet hair and shining faces. '
        f'"Teamwork made the ark strong," {hero.attrs["hero_name"]} said.'
    )
    world.say(
        f"When the storm passed, {place.ending_image}, and the rescued animals blinked out from the doorway as if they knew who had helped them."
    )


def tell(hero_cfg: HeroConfig, place_cfg: PlaceConfig, animal_cfg: AnimalGroup,
         vessel_cfg: VesselConfig, helper1_cfg: HelperConfig, helper2_cfg: HelperConfig,
         tool_cfg: ToolConfig) -> World:
    world = World()

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_cfg.type,
        label=hero_cfg.name,
        role="hero",
        attrs={
            "hero_name": hero_cfg.name,
            "hero_title": hero_cfg.title,
            "arrival": hero_cfg.arrival,
            "power": hero_cfg.power,
            "emblem": hero_cfg.emblem,
        },
        tags=set(hero_cfg.tags),
    ))
    helper1 = world.add(Entity(
        id="helper1",
        kind="character",
        type=helper1_cfg.type,
        label=helper1_cfg.name,
        role="helper",
        attrs={
            "name": helper1_cfg.name,
            "title": helper1_cfg.title,
            "skill": helper1_cfg.skill,
            "assist_text": helper1_cfg.assist_text,
            "cheer_text": helper1_cfg.cheer_text,
        },
        tags=set(helper1_cfg.tags),
    ))
    helper2 = world.add(Entity(
        id="helper2",
        kind="character",
        type=helper2_cfg.type,
        label=helper2_cfg.name,
        role="helper",
        attrs={
            "name": helper2_cfg.name,
            "title": helper2_cfg.title,
            "skill": helper2_cfg.skill,
            "assist_text": helper2_cfg.assist_text,
            "cheer_text": helper2_cfg.cheer_text,
        },
        tags=set(helper2_cfg.tags),
    ))
    world.add(Entity(id="weather", type="weather", label="storm cloud"))
    world.add(Entity(id="place", type="place", label=place_cfg.label, tags=set(place_cfg.tags)))
    animals = world.add(Entity(
        id="animals",
        type="animals",
        label=animal_cfg.label,
        attrs={
            "count": animal_cfg.count,
            "small_sound": animal_cfg.small_sound,
            "nervous_move": animal_cfg.nervous_move,
        },
        tags=set(animal_cfg.tags),
    ))
    vessel = world.add(Entity(
        id="vessel",
        type="vessel",
        label=vessel_cfg.label,
        phrase=vessel_cfg.phrase,
        attrs={
            "floats": vessel_cfg.floats,
            "capacity": vessel_cfg.capacity,
            "balance": vessel_cfg.balance,
        },
        tags=set(vessel_cfg.tags),
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        attrs={"fixes": set(tool_cfg.fixes)},
        tags=set(tool_cfg.tags),
    ))

    open_scene(world, hero, place_cfg, animal_cfg)
    world.para()
    spot_danger(world, hero, place_cfg, animals)
    call_team(world, hero, helper1, helper2)
    build_ark(world, hero, helper1, helper2, vessel_cfg)
    world.para()
    storm_turn(world, hero, tool_cfg)
    repair_and_launch(world, hero, helper1, helper2, place_cfg, tool_cfg, vessel_cfg)
    world.para()
    safe_arrival(world, hero, helper1, helper2, place_cfg, vessel_cfg)

    world.facts.update(
        hero=hero,
        helper1=helper1,
        helper2=helper2,
        hero_cfg=hero_cfg,
        place_cfg=place_cfg,
        animal_cfg=animal_cfg,
        vessel_cfg=vessel_cfg,
        tool_cfg=tool_cfg,
        animals=animals,
        vessel=vessel,
        teamwork=helper1.memes["working"] >= THRESHOLD and helper2.memes["working"] >= THRESHOLD,
        rescued=vessel.meters["ready"] >= THRESHOLD,
        cracked=True,
    )
    return world


@dataclass
class StoryParams:
    hero: str
    place: str
    animals: str
    vessel: str
    helper1: str
    helper2: str
    tool: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        hero="cape_comet",
        place="rooftop_garden",
        animals="ducklings",
        vessel="crate_ark",
        helper1="fixit_finn",
        helper2="steady_sky",
        tool="sealant",
    ),
    StoryParams(
        hero="bolt_ben",
        place="river_park",
        animals="bunnies",
        vessel="crate_ark",
        helper1="mighty_mina",
        helper2="zip_zane",
        tool="sealant",
    ),
    StoryParams(
        hero="glow_guard",
        place="school_garden",
        animals="kittens",
        vessel="tub_ark",
        helper1="fixit_finn",
        helper2="zip_zane",
        tool="sealant",
    ),
]


KNOWLEDGE = {
    "ark": [(
        "What is an ark?",
        "An ark is a large boat or rescue boat used to carry living things safely through water. In stories, it often means a boat that protects many animals at once."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork means people helping one another to do a job together. One person may be strong, another careful, and another calm, and the job goes better because they share it."
    )],
    "storm": [(
        "Why is a storm dangerous for small animals?",
        "A storm can bring strong wind and rising water. Small animals can get cold, frightened, or stuck if they do not have a safe place."
    )],
    "boat": [(
        "Why does a rescue boat need to float?",
        "A rescue boat has to stay on top of the water so it can carry everyone safely. If it does not float, it cannot be used like an ark."
    )],
    "repair": [(
        "Why should you patch a crack in a boat?",
        "A crack can let water leak in and make the boat wobble. Patching it helps keep the boat strong and dry."
    )],
    "rope": [(
        "What can rope help with in a rescue?",
        "Rope can help people pull, tie, or guide something safely. It is useful when a team needs to hold an ark steady."
    )],
    "animals": [(
        "Why do rescuers help animals too?",
        "Animals can need help just like people do. A kind rescuer notices when a small creature is in danger and brings it somewhere safe."
    )],
    "superhero": [(
        "Does a superhero always work alone?",
        "No. A good superhero knows when friends and helpers make the plan safer and stronger. Asking for help can be part of being brave."
    )],
}
KNOWLEDGE_ORDER = ["ark", "teamwork", "storm", "boat", "repair", "rope", "animals", "superhero"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero_cfg"]
    place = f["place_cfg"]
    animal = f["animal_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "ark" and takes place in {place.label}.',
        f"Tell a Teamwork superhero story where {hero.name} and two helpers build a little ark to rescue some {animal.label} before a storm reaches them.",
        "Write a gentle action story where a hero cannot solve the whole problem alone, so the team shares the lifting, building, and guiding until everyone is safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper1 = f["helper1"]
    helper2 = f["helper2"]
    place = f["place_cfg"]
    animal = f["animal_cfg"]
    vessel = f["vessel_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['hero_name']}, {helper1.attrs['name']}, and {helper2.attrs['name']} working together as a rescue team. They were trying to save some {animal.label} before the storm water reached them."
        ),
        (
            "Why did they need an ark?",
            f"They needed an ark because rain was starting to flood {place.label}. The little {animal.label} were small and frightened, so they needed a floating place to ride to safety."
        ),
        (
            f"What did each helper do?",
            f"{helper1.attrs['name']} helped with {helper1.attrs['skill']}, and {helper2.attrs['name']} helped with {helper2.attrs['skill']}. The rescue worked because the jobs were shared instead of pushed onto one hero."
        ),
        (
            "What went wrong in the middle of the story?",
            f"A gust knocked the little ark and made a crack in its side. That mattered because a crack can turn into a leak and make a rescue boat wobble."
        ),
        (
            "How did they fix the problem?",
            f"They worked together and used {tool.label} on the crack while the team held the ark steady. After that, the little {vessel.label} was ready to carry the {animal.label} to shelter."
        ),
        (
            "How did the story end?",
            f"The {animal.label} reached safety in {place.shelter}, and the storm passed. The ending shows the change clearly: the animals were frightened in the rain at first, but at the end they were dry and safe because the team built and repaired the ark together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ark", "teamwork", "storm", "boat", "repair", "animals", "superhero"}
    if world.facts["tool_cfg"].id == "rope":
        tags.add("rope")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {}
            for k, v in ent.attrs.items():
                if isinstance(v, set):
                    if v:
                        shown[k] = sorted(v)
                elif v:
                    shown[k] = v
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid_combo(H, P, A, V) :- hero(H), place(P), animals(A), vessel(V), floats(V), capacity(V, C), animal_count(A, N), C >= N.

team_pair(X, Y) :- helper(X), helper(Y), X < Y, skill(X, build), skill(Y, steer).
team_pair(X, Y) :- helper(X), helper(Y), X < Y, skill(X, steer), skill(Y, build).

% --- chosen scenario validity ----------------------------------------------
chosen_ok :- chosen_vessel(V), chosen_animals(A), floats(V), capacity(V, C), animal_count(A, N), C >= N.
chosen_team_ok :- chosen_helper1(X), chosen_helper2(Y), X < Y, team_pair(X, Y).
chosen_team_ok :- chosen_helper1(X), chosen_helper2(Y), Y < X, team_pair(Y, X).

story_valid :- chosen_ok, chosen_team_ok.

% --- outcome model ---------------------------------------------------------
storm_rises.
crack_happens :- story_valid.
patched :- chosen_tool(T), patches(T), crack_happens.
guided  :- chosen_helper1(X), skill(X, steer), story_valid.
guided  :- chosen_helper2(Y), skill(Y, steer), story_valid.

rescued :- story_valid, patched, guided.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animals", animal_id))
        lines.append(asp.fact("animal_count", animal_id, animal.count))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        if vessel.floats:
            lines.append(asp.fact("floats", vessel_id))
        lines.append(asp.fact("capacity", vessel_id, vessel.capacity))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("skill", helper_id, helper.skill))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if "patch" in tool.fixes:
            lines.append(asp.fact("patches", tool_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_valid_teams() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show team_pair/2."))
    return sorted(set(asp.atoms(model, "team_pair")))


def asp_story_valid(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_vessel", params.vessel),
        asp.fact("chosen_animals", params.animals),
        asp.fact("chosen_helper1", params.helper1),
        asp.fact("chosen_helper2", params.helper2),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show story_valid/0."))
    return bool(asp.atoms(model, "story_valid"))


def asp_rescued(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_vessel", params.vessel),
        asp.fact("chosen_animals", params.animals),
        asp.fact("chosen_helper1", params.helper1),
        asp.fact("chosen_helper2", params.helper2),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show rescued/0."))
    return bool(asp.atoms(model, "rescued"))


def _python_story_valid(params: StoryParams) -> bool:
    if params.vessel not in VESSELS or params.animals not in ANIMALS:
        return False
    if params.helper1 not in HELPERS or params.helper2 not in HELPERS:
        return False
    if params.helper1 == params.helper2:
        return False
    return danger_is_reasonable(VESSELS[params.vessel], ANIMALS[params.animals]) and teamwork_ready(
        HELPERS[params.helper1], HELPERS[params.helper2]
    )


def _python_rescued(params: StoryParams) -> bool:
    if not _python_story_valid(params):
        return False
    helper_skills = {HELPERS[params.helper1].skill, HELPERS[params.helper2].skill}
    tool = TOOLS[params.tool]
    return "steer" in helper_skills and "patch" in tool.fixes


def asp_verify() -> int:
    rc = 0
    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))

    py_teams = set(valid_team_pairs())
    asp_teams = set(asp_valid_teams())
    if py_teams == asp_teams:
        print(f"OK: team pairs match ({len(py_teams)} pairs).")
    else:
        rc = 1
        print("MISMATCH in team pairs:")
        if asp_teams - py_teams:
            print("  only in clingo:", sorted(asp_teams - py_teams))
        if py_teams - asp_teams:
            print("  only in python:", sorted(py_teams - asp_teams))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    validity_bad = 0
    rescued_bad = 0
    for params in cases:
        if asp_story_valid(params) != _python_story_valid(params):
            validity_bad += 1
        if asp_rescued(params) != _python_rescued(params):
            rescued_bad += 1
    if validity_bad == 0:
        print(f"OK: story_valid parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: story_valid differs on {validity_bad}/{len(cases)} scenarios.")
    if rescued_bad == 0:
        print(f"OK: rescued parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: rescued differs on {rescued_bad}/{len(cases)} scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero team builds a little ark to rescue animals from rising water."
    )
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--animals", choices=sorted(ANIMALS))
    ap.add_argument("--vessel", choices=sorted(VESSELS))
    ap.add_argument("--helper1", choices=sorted(HELPERS))
    ap.add_argument("--helper2", choices=sorted(HELPERS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vessel and args.animals:
        vessel = VESSELS[args.vessel]
        animal = ANIMALS[args.animals]
        if not danger_is_reasonable(vessel, animal):
            raise StoryError(explain_vessel(vessel, animal))

    if args.helper1 and args.helper2:
        if args.helper1 == args.helper2:
            raise StoryError("(No story: the teamwork feature needs two different helpers.)")
        if not teamwork_ready(HELPERS[args.helper1], HELPERS[args.helper2]):
            raise StoryError(explain_team(HELPERS[args.helper1], HELPERS[args.helper2]))

    combos = [
        combo for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.place is None or combo[1] == args.place)
        and (args.animals is None or combo[2] == args.animals)
        and (args.vessel is None or combo[3] == args.vessel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hero_id, place_id, animals_id, vessel_id = rng.choice(sorted(combos))

    team_pairs = [
        pair for pair in valid_team_pairs()
        if (args.helper1 is None or args.helper1 in pair)
        and (args.helper2 is None or args.helper2 in pair)
    ]
    if not team_pairs:
        raise StoryError("(No valid helper pair matches the given options.)")
    helper1_id, helper2_id = rng.choice(sorted(team_pairs))
    if args.helper1 and args.helper2:
        helper1_id, helper2_id = args.helper1, args.helper2
    elif args.helper1 and args.helper1 not in {helper1_id, helper2_id}:
        raise StoryError("(No valid helper pair matches the given options.)")
    elif args.helper2 and args.helper2 not in {helper1_id, helper2_id}:
        raise StoryError("(No valid helper pair matches the given options.)")
    elif args.helper1 and not args.helper2:
        other = helper2_id if helper1_id == args.helper1 else helper1_id
        helper1_id, helper2_id = args.helper1, other
    elif args.helper2 and not args.helper1:
        other = helper2_id if helper1_id == args.helper2 else helper1_id
        helper1_id, helper2_id = other, args.helper2

    tool_id = args.tool or "sealant"
    if tool_id not in TOOLS:
        raise StoryError("(No story: unknown tool.)")

    params = StoryParams(
        hero=hero_id,
        place=place_id,
        animals=animals_id,
        vessel=vessel_id,
        helper1=helper1_id,
        helper2=helper2_id,
        tool=tool_id,
    )
    if not _python_story_valid(params):
        raise StoryError("(No story: the chosen team and ark do not make a safe rescue plan.)")
    return params


def generate(params: StoryParams) -> StorySample:
    for key, registry in [
        (params.hero, HEROES),
        (params.place, PLACES),
        (params.animals, ANIMALS),
        (params.vessel, VESSELS),
        (params.helper1, HELPERS),
        (params.helper2, HELPERS),
        (params.tool, TOOLS),
    ]:
        if key not in registry:
            raise StoryError("(No story: one of the requested options is unknown.)")
    if params.helper1 == params.helper2:
        raise StoryError("(No story: a teamwork story needs two different helpers.)")
    if not danger_is_reasonable(VESSELS[params.vessel], ANIMALS[params.animals]):
        raise StoryError(explain_vessel(VESSELS[params.vessel], ANIMALS[params.animals]))
    if not teamwork_ready(HELPERS[params.helper1], HELPERS[params.helper2]):
        raise StoryError(explain_team(HELPERS[params.helper1], HELPERS[params.helper2]))
    if "patch" not in TOOLS[params.tool].fixes:
        raise StoryError("(No story: the middle turn includes a crack, so the chosen tool must be able to patch it.)")

    world = tell(
        hero_cfg=HEROES[params.hero],
        place_cfg=PLACES[params.place],
        animal_cfg=ANIMALS[params.animals],
        vessel_cfg=VESSELS[params.vessel],
        helper1_cfg=HELPERS[params.helper1],
        helper2_cfg=HELPERS[params.helper2],
        tool_cfg=TOOLS[params.tool],
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
        print(asp_program("", "#show valid_combo/4.\n#show team_pair/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        teams = asp_valid_teams()
        print(f"{len(combos)} compatible (hero, place, animals, vessel) combos:\n")
        for hero_id, place_id, animals_id, vessel_id in combos:
            print(f"  {hero_id:12} {place_id:14} {animals_id:10} {vessel_id}")
        print(f"\n{len(teams)} valid helper pairs:\n")
        for h1, h2 in teams:
            print(f"  {h1:12} {h2}")
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
            header = f"### {p.hero} at {p.place}: {p.animals} rescued by {p.vessel}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
