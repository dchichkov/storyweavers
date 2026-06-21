#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chaos_classify_bravery_bedtime_story.py
==================================================================

A standalone bedtime-flavoured story world about a child whose bedtime treasures
spill into gentle chaos. To find one missing keepsake, the child must bravely
look into a dark hiding place and classify the scattered things into neat little
groups.

The world is intentionally small and constraint-checked:

* A missing keepsake must belong to the chosen collection.
* The chosen sorting plan must actually help separate that keepsake from the
  other spilled objects.
* The chosen light must be child-safe and bright enough for the hiding place.

The emotional turn is about bravery rather than danger. A child may search
alone, or may need a parent's hand nearby, depending on the depth of the dark
place and the child's bravery. Either way, the story ends with order restored
and a calmer room.

Run it
------
    python storyworlds/worlds/gpt-5.4/chaos_classify_bravery_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/chaos_classify_bravery_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/chaos_classify_bravery_bedtime_story.py --collection buttons --missing moon_button --sort shape
    python storyworlds/worlds/gpt-5.4/chaos_classify_bravery_bedtime_story.py --light hallway_glow
    python storyworlds/worlds/gpt-5.4/chaos_classify_bravery_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/chaos_classify_bravery_bedtime_story.py --verify
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
SAFE_LIGHT_MIN = 1


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


@dataclass
class Collection:
    id: str
    label: str
    phrase: str
    spill_text: str
    bedtime_line: str
    items: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingThing:
    id: str
    collection: str
    label: str
    phrase: str
    sort_values: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)


@dataclass
class SortPlan:
    id: str
    verb: str
    noun: str
    prompt: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    depth: int
    reach_text: str
    found_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LightTool:
    id: str
    label: str
    phrase: str
    power: int
    glow: str
    child_safe: bool = True
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


def _r_scare(world: World) -> list[str]:
    room = world.entities.get("room")
    hero = world.entities.get("hero")
    if room is None or hero is None:
        return []
    if room.meters["chaos"] < THRESHOLD or room.meters["darkness"] < THRESHOLD:
        return []
    sig = ("scare", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return ["__fear__"]


def _r_sort_calm(world: World) -> list[str]:
    room = world.entities.get("room")
    hero = world.entities.get("hero")
    if room is None or hero is None:
        return []
    if room.meters["classified"] < THRESHOLD:
        return []
    sig = ("calm", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["chaos"] = max(0.0, room.meters["chaos"] - 1.0)
    hero.memes["calm"] += 1
    return []


def _r_light_steady(world: World) -> list[str]:
    room = world.entities.get("room")
    hero = world.entities.get("hero")
    if room is None or hero is None:
        return []
    if room.meters["lit"] < THRESHOLD:
        return []
    sig = ("steady", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="scare", tag="emotional", apply=_r_scare),
    Rule(name="sort_calm", tag="emotional", apply=_r_sort_calm),
    Rule(name="light_steady", tag="emotional", apply=_r_light_steady),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


COLLECTIONS = {
    "buttons": Collection(
        id="buttons",
        label="button box",
        phrase="a round button box full of tiny treasures",
        spill_text="buttons pattered over the rug like bright little raindrops",
        bedtime_line="At bedtime, the little button box always sat by the lamp.",
        items=["moon_button", "heart_button", "star_button"],
        tags={"buttons", "sorting"},
    ),
    "beads": Collection(
        id="beads",
        label="bead tin",
        phrase="a silver tin of bedtime beads",
        spill_text="beads skipped and clicked across the floorboards",
        bedtime_line="At bedtime, the bead tin made a soft tink-tink when it was lifted.",
        items=["striped_bead", "gold_bead", "round_bead"],
        tags={"beads", "sorting"},
    ),
    "toy_animals": Collection(
        id="toy_animals",
        label="animal basket",
        phrase="a willow basket of small toy animals",
        spill_text="toy animals tumbled out in a little parade of paws and tails",
        bedtime_line="At bedtime, the animal basket waited beside the pillow.",
        items=["lamb_figure", "fox_figure", "whale_figure"],
        tags={"animals", "sorting"},
    ),
}

MISSING = {
    "moon_button": MissingThing(
        id="moon_button",
        collection="buttons",
        label="moon button",
        phrase="the moon button with a sleepy silver curve",
        sort_values={"color": "silver", "shape": "moon"},
        tags={"buttons", "moon"},
    ),
    "heart_button": MissingThing(
        id="heart_button",
        collection="buttons",
        label="heart button",
        phrase="the heart button with a cherry-red shine",
        sort_values={"color": "red", "shape": "heart"},
        tags={"buttons", "heart"},
    ),
    "star_button": MissingThing(
        id="star_button",
        collection="buttons",
        label="star button",
        phrase="the star button with five tiny points",
        sort_values={"color": "gold", "shape": "star"},
        tags={"buttons", "star"},
    ),
    "striped_bead": MissingThing(
        id="striped_bead",
        collection="beads",
        label="striped bead",
        phrase="the striped bead with two pale blue rings",
        sort_values={"color": "blue", "pattern": "striped"},
        tags={"beads", "striped"},
    ),
    "gold_bead": MissingThing(
        id="gold_bead",
        collection="beads",
        label="gold bead",
        phrase="the gold bead that gleamed like honey",
        sort_values={"color": "gold", "pattern": "plain"},
        tags={"beads", "gold"},
    ),
    "round_bead": MissingThing(
        id="round_bead",
        collection="beads",
        label="round bead",
        phrase="the round bead smooth as a tiny marble",
        sort_values={"shape": "round", "color": "green"},
        tags={"beads", "round"},
    ),
    "lamb_figure": MissingThing(
        id="lamb_figure",
        collection="toy_animals",
        label="little lamb",
        phrase="the little lamb with tucked white legs",
        sort_values={"family": "farm", "size": "small"},
        tags={"animals", "farm"},
    ),
    "fox_figure": MissingThing(
        id="fox_figure",
        collection="toy_animals",
        label="fox figure",
        phrase="the fox figure with a bright brushy tail",
        sort_values={"family": "forest", "size": "small"},
        tags={"animals", "forest"},
    ),
    "whale_figure": MissingThing(
        id="whale_figure",
        collection="toy_animals",
        label="whale figure",
        phrase="the whale figure smooth and blue",
        sort_values={"family": "sea", "size": "big"},
        tags={"animals", "sea"},
    ),
}

SORTS = {
    "color": SortPlan(
        id="color",
        verb="classify the scattered things by color",
        noun="color piles",
        prompt="put the blue with blue, the gold with gold, and the red with red",
        tags={"sorting", "color"},
    ),
    "shape": SortPlan(
        id="shape",
        verb="classify the scattered things by shape",
        noun="shape piles",
        prompt="set the round with round, the moon with moon, and the star with star",
        tags={"sorting", "shape"},
    ),
    "pattern": SortPlan(
        id="pattern",
        verb="classify the scattered things by pattern",
        noun="pattern piles",
        prompt="place the striped beside the plain and the spotted beside the smooth",
        tags={"sorting", "pattern"},
    ),
    "family": SortPlan(
        id="family",
        verb="classify the scattered things by animal family",
        noun="animal families",
        prompt="let the farm friends stand together and the sea friends rest together",
        tags={"sorting", "family"},
    ),
    "size": SortPlan(
        id="size",
        verb="classify the scattered things by size",
        noun="big and small groups",
        prompt="make one place for the small ones and one place for the big ones",
        tags={"sorting", "size"},
    ),
}

HIDING = {
    "under_bed": HidingPlace(
        id="under_bed",
        label="under the bed",
        phrase="the dark space under the bed",
        depth=2,
        reach_text="the far shadows under the bed looked deeper than they really were",
        found_text="right beside a lost sock, tucked near the back board",
        tags={"bed", "dark"},
    ),
    "behind_curtain": HidingPlace(
        id="behind_curtain",
        label="behind the curtain",
        phrase="the fold behind the curtain",
        depth=1,
        reach_text="the curtain swayed and made a long soft shadow",
        found_text="caught in the hem where moonlight touched the cloth",
        tags={"curtain", "dark"},
    ),
    "beside_bookcase": HidingPlace(
        id="beside_bookcase",
        label="beside the bookcase",
        phrase="the narrow gap beside the bookcase",
        depth=1,
        reach_text="the bookcase made a thin stripe of darkness along the wall",
        found_text="between the skirting board and a stack of sleepy books",
        tags={"bookcase", "dark"},
    ),
}

LIGHTS = {
    "flashlight": LightTool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        power=2,
        glow="made a steady yellow circle on the floor",
        child_safe=True,
        tags={"flashlight", "light"},
    ),
    "lantern": LightTool(
        id="lantern",
        label="bedside lantern",
        phrase="the bedside lantern",
        power=2,
        glow="glowed softly like a patient little moon",
        child_safe=True,
        tags={"lantern", "light"},
    ),
    "nightlight": LightTool(
        id="nightlight",
        label="night-light",
        phrase="the plug-in night-light",
        power=1,
        glow="spilled a gentle puddle of light near the wall",
        child_safe=True,
        tags={"nightlight", "light"},
    ),
    "hallway_glow": LightTool(
        id="hallway_glow",
        label="hallway glow",
        phrase="the far hallway glow",
        power=0,
        glow="barely reached the corners of the room",
        child_safe=False,
        tags={"light"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ella", "Rosie", "Ava", "June", "Tessa"]
BOY_NAMES = ["Owen", "Leo", "Max", "Ben", "Theo", "Finn", "Eli", "Noah"]
TRAITS = ["sleepy", "gentle", "curious", "careful", "quiet", "thoughtful"]


@dataclass
class StoryParams:
    collection: str
    missing: str
    sort: str
    hiding: str
    light: str
    name: str
    gender: str
    parent: str
    trait: str
    bravery: int
    seed: Optional[int] = None


def sort_helps(missing_id: str, sort_id: str) -> bool:
    thing = MISSING[missing_id]
    return sort_id in thing.sort_values


def light_can_reach(light_id: str, hiding_id: str) -> bool:
    light = LIGHTS[light_id]
    place = HIDING[hiding_id]
    return light.child_safe and light.power >= place.depth and light.power >= SAFE_LIGHT_MIN


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for collection_id, collection in COLLECTIONS.items():
        for missing_id in collection.items:
            for sort_id in SORTS:
                if not sort_helps(missing_id, sort_id):
                    continue
                for hiding_id in HIDING:
                    for light_id in LIGHTS:
                        if light_can_reach(light_id, hiding_id):
                            combos.append((collection_id, missing_id, sort_id, hiding_id, light_id))
    return combos


def sensible_lights() -> list[str]:
    return sorted(light_id for light_id, light in LIGHTS.items()
                  if light.child_safe and light.power >= SAFE_LIGHT_MIN)


def explain_collection_mismatch(collection_id: str, missing_id: str) -> str:
    return (f"(No story: {MISSING[missing_id].label} does not belong in the "
            f"{COLLECTIONS[collection_id].label}. Pick a keepsake from that collection.)")


def explain_sort(missing_id: str, sort_id: str) -> str:
    thing = MISSING[missing_id]
    return (f"(No story: you cannot honestly classify the spill by {sort_id} to find "
            f"{thing.label}, because that keepsake is not distinct by that feature here.)")


def explain_light(light_id: str, hiding_id: str) -> str:
    light = LIGHTS[light_id]
    place = HIDING[hiding_id]
    if not light.child_safe:
        return (f"(No story: {light.label} is not treated as a child-safe bedtime light. "
                f"Choose a flashlight, lantern, or night-light instead.)")
    return (f"(No story: {light.label} is too weak for {place.label}. "
            f"The searching light must reach into the dark place.)")


def helper_needed(bravery: int, hiding_id: str) -> bool:
    return bravery < HIDING[hiding_id].depth + 1


def outcome_of(params: StoryParams) -> str:
    return "with_help" if helper_needed(params.bravery, params.hiding) else "solo"


def predicted_search(world: World, light_id: str, hiding_id: str) -> dict:
    sim = world.copy()
    room = sim.get("room")
    room.meters["lit"] += 1
    room.meters["darkness"] = max(0.0, room.meters["darkness"] - LIGHTS[light_id].power)
    room.meters["classified"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("hero").memes["fear"],
        "calm": sim.get("hero").memes["calm"],
        "can_reach": light_can_reach(light_id, hiding_id),
    }


def introduce(world: World, hero: Entity, parent: Entity, collection: Collection) -> None:
    world.say(
        f"One quiet night, {hero.id} was meant to be getting sleepy. "
        f"{collection.bedtime_line}"
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved that box because it held small things worth keeping, "
        f"and {parent.label_word} said each one remembered a gentle part of the day."
    )


def spill(world: World, hero: Entity, collection: Collection, missing: MissingThing,
          hiding: HidingPlace) -> None:
    room = world.get("room")
    room.meters["chaos"] += 1
    room.meters["darkness"] += hiding.depth
    hero.memes["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} tugged the blanket up, the {collection.label} tipped. "
        f"In one tiny burst of chaos, {collection.spill_text}."
    )
    world.say(
        f"When the room grew still again, {missing.phrase} was gone. It had slipped into "
        f"{hiding.phrase}, and {hiding.reach_text}."
    )


def worry(world: World, hero: Entity, parent: Entity, missing: MissingThing) -> None:
    fear = hero.memes["fear"]
    line = f'"Oh dear," whispered {hero.id}. "I cannot see {missing.label} anywhere."'
    if fear >= THRESHOLD:
        line += f" The dark made {hero.pronoun('object')} pause beside the bed."
    world.say(line)
    world.say(
        f'{parent.label_word.capitalize()} came to the doorway in slippers and listened before speaking.'
    )


def suggest_plan(world: World, hero: Entity, parent: Entity, sort_cfg: SortPlan,
                 light: LightTool, hiding: HidingPlace) -> None:
    pred = predicted_search(world, light.id, hiding.id)
    world.facts["pred_can_reach"] = pred["can_reach"]
    world.facts["pred_fear"] = pred["fear"]
    world.facts["pred_calm"] = pred["calm"]
    world.say(
        f'"First," said {parent.label_word}, "let us {sort_cfg.verb}. '
        f'When a room feels muddled, we can classify one small thing at a time."'
    )
    world.say(
        f'"Then we will use {light.phrase}, which {light.glow}, and look carefully instead of rushing."'
    )


def classify_items(world: World, hero: Entity, sort_cfg: SortPlan, missing: MissingThing) -> None:
    room = world.get("room")
    room.meters["classified"] += 1
    hero.memes["focus"] += 1
    propagate(world, narrate=False)
    key = missing.sort_values[sort_cfg.id]
    world.say(
        f"{hero.id} knelt on the rug and began to classify the spill. "
        f"{hero.pronoun().capitalize()} made {sort_cfg.noun}, trying to {sort_cfg.prompt}."
    )
    world.say(
        f"Soon the room no longer felt wild. One neat little group showed what they were looking for: "
        f"the {sort_cfg.id} they needed was {key}."
    )


def light_room(world: World, hero: Entity, light: LightTool) -> None:
    room = world.get("room")
    room.meters["lit"] += 1
    room.meters["darkness"] = max(0.0, room.meters["darkness"] - light.power)
    hero.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} clicked on {light.phrase}. It {light.glow}, and the corners of the room stopped "
        f"feeling quite so large."
    )


def search_solo(world: World, hero: Entity, missing: MissingThing, hiding: HidingPlace) -> None:
    hero.memes["brave_act"] += 1
    world.say(
        f"{hero.id} took one slow breath, then another. Being brave did not mean feeling no flutter at all; "
        f"it meant moving kindly through it."
    )
    world.say(
        f"With the light in one hand, {hero.pronoun()} reached into {hiding.label} and found {missing.label} "
        f"{hiding.found_text}."
    )


def search_with_help(world: World, hero: Entity, parent: Entity, missing: MissingThing,
                     hiding: HidingPlace) -> None:
    hero.memes["brave_act"] += 1
    hero.memes["supported"] += 1
    world.say(
        f"{hero.id} wanted to be brave, but the dark place still looked deep. "
        f"So {parent.label_word} knelt nearby and offered a warm hand."
    )
    world.say(
        f"Together they counted to three. Then {hero.id} reached into {hiding.label} and found "
        f"{missing.label} {hiding.found_text}."
    )


def settle(world: World, hero: Entity, parent: Entity, collection: Collection,
           missing: MissingThing) -> None:
    room = world.get("room")
    room.meters["restored"] += 1
    hero.memes["relief"] += 1
    hero.memes["sleepy"] += 1
    world.say(
        f"{hero.id} tucked {missing.label} back into the {collection.label}, and the last of the bedtime chaos "
        f"seemed to fold itself away."
    )
    world.say(
        f'{parent.label_word.capitalize()} kissed {hero.pronoun("possessive")} forehead. '
        f'"Now the room knows where everything belongs," {parent.pronoun()} said.'
    )
    world.say(
        f"Soon the lamp was low, the treasures were quiet, and {hero.id} fell asleep feeling braver than before."
    )


def tell(collection: Collection, missing: MissingThing, sort_cfg: SortPlan,
         hiding: HidingPlace, light: LightTool, name: str = "Lila",
         gender: str = "girl", parent_type: str = "mother",
         trait: str = "gentle", bravery: int = 2) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=gender,
        label=name,
        phrase=name,
        traits=[trait],
        role="hero",
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="bedroom",
    ))
    hero.attrs["display_name"] = name
    hero.memes["bravery"] = float(bravery)
    world.facts["display_name"] = name

    introduce(world, hero, parent, collection)
    world.para()
    spill(world, hero, collection, missing, hiding)
    worry(world, hero, parent, missing)
    suggest_plan(world, hero, parent, sort_cfg, light, hiding)
    world.para()
    classify_items(world, hero, sort_cfg, missing)
    light_room(world, hero, light)
    if helper_needed(bravery, hiding.id):
        search_with_help(world, hero, parent, missing, hiding)
        outcome = "with_help"
    else:
        search_solo(world, hero, missing, hiding)
        outcome = "solo"
    world.para()
    settle(world, hero, parent, collection, missing)

    world.facts.update(
        hero=hero,
        parent=parent,
        collection=collection,
        missing=missing,
        sort=sort_cfg,
        hiding=hiding,
        light=light,
        outcome=outcome,
        bravery=bravery,
        found=True,
        helper=(outcome == "with_help"),
    )
    return world


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display_name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    name = display_name(f["hero"])
    missing = f["missing"]
    sort_cfg = f["sort"]
    hiding = f["hiding"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "chaos" and "classify".',
        f"Tell a gentle nighttime story where {name} loses {missing.label} in {hiding.label}, and bravery means looking carefully instead of rushing.",
        f"Write a soft, child-facing story where a spilled collection is put back in order by using {sort_cfg.id} to classify the pieces before bed.",
    ]


KNOWLEDGE = {
    "sorting": [(
        "What does it mean to classify things?",
        "To classify things means to sort them into groups that match. You might put things together by color, shape, size, or family."
    )],
    "light": [(
        "Why is it easier to find something with a light?",
        "A light helps your eyes see corners and shadows clearly. When you can see better, it is easier to look carefully instead of guessing."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery means doing the next safe thing even when you feel a little afraid. You can be brave all by yourself, or brave while holding someone's hand."
    )],
    "buttons": [(
        "What is a button box?",
        "A button box is a little container that holds buttons for sewing or keeping. Buttons can be different colors and shapes, so they are easy to sort."
    )],
    "beads": [(
        "What are beads?",
        "Beads are small pieces with holes that can be used for stringing or saving. They often have colors, patterns, and shapes that make good sorting groups."
    )],
    "animals": [(
        "What is a toy animal collection?",
        "A toy animal collection is a group of small pretend animals kept together. You can sort them by where they live or what kind of animal they are."
    )],
    "nightlight": [(
        "What is a night-light?",
        "A night-light is a small lamp that gives a gentle glow in the dark. It helps a room feel calmer at bedtime."
    )],
    "flashlight": [(
        "What does a flashlight do?",
        "A flashlight shines a beam where you point it. That makes it useful for looking under beds or into corners."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a light that glows softly around itself. It can brighten a small space in a calm way."
    )],
}
KNOWLEDGE_ORDER = [
    "sorting", "bravery", "light", "buttons", "beads", "animals",
    "nightlight", "flashlight", "lantern",
]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    name = display_name(hero)
    pw = parent.label_word
    collection = f["collection"]
    missing = f["missing"]
    sort_cfg = f["sort"]
    hiding = f["hiding"]
    light = f["light"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child getting ready for sleep, and {name}'s {pw}. Together they turn a muddled bedtime moment into a calm one."
        ),
        (
            "What caused the chaos in the room?",
            f"The {collection.label} tipped when bedtime was beginning, and the little treasures spilled everywhere. That is why the room suddenly felt full of chaos."
        ),
        (
            f"Why did {name} need to classify the spilled things?",
            f"{name} needed to find {missing.label}, and sorting the spill into groups made the room easier to understand. Classifying the pieces also helped the room feel calmer instead of muddled."
        ),
        (
            f"How did the light help {name}?",
            f"They used {light.phrase}, and it {light.glow}. The extra light made {hiding.label} easier to search carefully."
        ),
    ]
    if f["outcome"] == "solo":
        qa.append((
            f"How was {name} brave in the story?",
            f"{name} still felt a small flutter, but took slow breaths and searched anyway. The bravery came from doing the next careful thing alone."
        ))
    else:
        qa.append((
            f"How was {name} brave in the story?",
            f"{name} admitted the dark still felt deep, and then searched while {pw} stayed close. That is brave too, because asking for a steady hand can be part of being brave."
        ))
    qa.append((
        "How did the story end?",
        f"It ended quietly, with {missing.label} back in the {collection.label} and the room neat again. {name} fell asleep feeling braver than before."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"sorting", "bravery", "light"}
    collection = f["collection"]
    if collection.id == "buttons":
        tags.add("buttons")
    elif collection.id == "beads":
        tags.add("beads")
    else:
        tags.add("animals")
    light = f["light"]
    if light.id == "nightlight":
        tags.add("nightlight")
    elif light.id == "flashlight":
        tags.add("flashlight")
    elif light.id == "lantern":
        tags.add("lantern")

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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
member_of(M, C) :- missing(M), collection(C), belongs(M, C).
useful_sort(M, S) :- missing(M), sort(S), sort_value(M, S, _).
safe_light(L) :- light(L), child_safe(L), power(L, P), safe_light_min(M), P >= M.
reachable(H, L) :- hiding(H), light(L), power(L, P), depth(H, D), P >= D.
valid(C, M, S, H, L) :- belongs(M, C), useful_sort(M, S), safe_light(L), reachable(H, L).

needs_help :- bravery(B), chosen_hiding(H), depth(H, D), B < D + 1.
outcome(with_help) :- needs_help.
outcome(solo) :- not needs_help.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in COLLECTIONS:
        lines.append(asp.fact("collection", cid))
    for mid, thing in MISSING.items():
        lines.append(asp.fact("missing", mid))
        lines.append(asp.fact("belongs", mid, thing.collection))
        for sid, value in sorted(thing.sort_values.items()):
            lines.append(asp.fact("sort_value", mid, sid, value))
    for sid in SORTS:
        lines.append(asp.fact("sort", sid))
    for hid, place in HIDING.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("depth", hid, place.depth))
    for lid, light in LIGHTS.items():
        lines.append(asp.fact("light", lid))
        lines.append(asp.fact("power", lid, light.power))
        if light.child_safe:
            lines.append(asp.fact("child_safe", lid))
    lines.append(asp.fact("safe_light_min", SAFE_LIGHT_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_lights() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show safe_light/1."))
    return sorted(x for (x,) in asp.atoms(model, "safe_light"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("bravery", params.bravery),
        asp.fact("chosen_hiding", params.hiding),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        collection="buttons",
        missing="moon_button",
        sort="shape",
        hiding="under_bed",
        light="flashlight",
        name="Lila",
        gender="girl",
        parent="mother",
        trait="gentle",
        bravery=3,
    ),
    StoryParams(
        collection="beads",
        missing="striped_bead",
        sort="pattern",
        hiding="behind_curtain",
        light="nightlight",
        name="Owen",
        gender="boy",
        parent="father",
        trait="thoughtful",
        bravery=1,
    ),
    StoryParams(
        collection="toy_animals",
        missing="lamb_figure",
        sort="family",
        hiding="beside_bookcase",
        light="lantern",
        name="Nora",
        gender="girl",
        parent="mother",
        trait="quiet",
        bravery=2,
    ),
    StoryParams(
        collection="buttons",
        missing="heart_button",
        sort="color",
        hiding="behind_curtain",
        light="nightlight",
        name="Ben",
        gender="boy",
        parent="father",
        trait="careful",
        bravery=2,
    ),
    StoryParams(
        collection="toy_animals",
        missing="whale_figure",
        sort="size",
        hiding="under_bed",
        light="lantern",
        name="Ella",
        gender="girl",
        parent="mother",
        trait="curious",
        bravery=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a spill, a missing keepsake, a brave search, and a calm ending."
    )
    ap.add_argument("--collection", choices=COLLECTIONS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--sort", choices=SORTS)
    ap.add_argument("--hiding", choices=HIDING)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--bravery", type=int, choices=[1, 2, 3], help="1 = needs more support, 3 = boldest")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.collection and args.missing:
        if MISSING[args.missing].collection != args.collection:
            raise StoryError(explain_collection_mismatch(args.collection, args.missing))
    if args.missing and args.sort:
        if not sort_helps(args.missing, args.sort):
            raise StoryError(explain_sort(args.missing, args.sort))
    if args.light and args.hiding:
        if not light_can_reach(args.light, args.hiding):
            raise StoryError(explain_light(args.light, args.hiding))
    if args.light and args.light not in sensible_lights():
        raise StoryError(explain_light(args.light, args.hiding or "behind_curtain"))

    combos = [
        combo for combo in valid_combos()
        if (args.collection is None or combo[0] == args.collection)
        and (args.missing is None or combo[1] == args.missing)
        and (args.sort is None or combo[2] == args.sort)
        and (args.hiding is None or combo[3] == args.hiding)
        and (args.light is None or combo[4] == args.light)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    collection_id, missing_id, sort_id, hiding_id, light_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    bravery = args.bravery if args.bravery is not None else rng.choice([1, 2, 3])

    return StoryParams(
        collection=collection_id,
        missing=missing_id,
        sort=sort_id,
        hiding=hiding_id,
        light=light_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    if params.collection not in COLLECTIONS:
        raise StoryError(f"(Unknown collection: {params.collection})")
    if params.missing not in MISSING:
        raise StoryError(f"(Unknown missing keepsake: {params.missing})")
    if params.sort not in SORTS:
        raise StoryError(f"(Unknown sorting plan: {params.sort})")
    if params.hiding not in HIDING:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if MISSING[params.missing].collection != params.collection:
        raise StoryError(explain_collection_mismatch(params.collection, params.missing))
    if not sort_helps(params.missing, params.sort):
        raise StoryError(explain_sort(params.missing, params.sort))
    if not light_can_reach(params.light, params.hiding):
        raise StoryError(explain_light(params.light, params.hiding))

    world = tell(
        collection=COLLECTIONS[params.collection],
        missing=MISSING[params.missing],
        sort_cfg=SORTS[params.sort],
        hiding=HIDING[params.hiding],
        light=LIGHTS[params.light],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos parity holds ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_lights = set(sensible_lights())
    asp_lights = set(asp_sensible_lights())
    if py_lights == asp_lights:
        print(f"OK: sensible lights match ({sorted(py_lights)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible lights: python={sorted(py_lights)} clingo={sorted(asp_lights)}")

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve_params failure on seed {seed}.")
            break

    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome disagreements.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(sample, trace=False, qa=False)
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1.\n#show safe_light/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible lights: {', '.join(asp_sensible_lights())}\n")
        print(f"{len(combos)} compatible (collection, missing, sort, hiding, light) combos:\n")
        for collection_id, missing_id, sort_id, hiding_id, light_id in combos:
            print(f"  {collection_id:12} {missing_id:12} {sort_id:8} {hiding_id:15} {light_id}")
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
                f"### {p.name}: {p.collection}/{p.missing} with {p.sort} "
                f"at {p.hiding} using {p.light} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
