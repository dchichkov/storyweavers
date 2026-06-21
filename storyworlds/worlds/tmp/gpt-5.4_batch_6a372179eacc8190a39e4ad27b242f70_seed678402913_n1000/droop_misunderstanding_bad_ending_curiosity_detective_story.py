#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/droop_misunderstanding_bad_ending_curiosity_detective_story.py
==========================================================================================

A standalone storyworld for a tiny detective-style tale about a curious child who
sees a drooping plant, misunderstands the real cause, and makes things worse.

Core premise
------------
A child loves pretending to be a detective. One day the class plant droops. The
child notices clues, grows curious, and invents a mystery: maybe someone hurt the
plant on purpose, or maybe a helper moved it, or maybe a shadow means the plant
was "hiding." Instead of asking a grown-up right away, the child secretly tests
the theory in a way that keeps the plant from getting the water or sunlight it
needs. By the time the truth is understood, the plant has died.

World-model note
----------------
This world cares about one very small piece of common sense:

* A plant droops for a plausible physical reason: it is thirsty, too dark, or
  root-bound.
* A detective child may misread that droop as a sabotage clue.
* Only actions that actually worsen the plant's condition are allowed.
* The story ends sadly when the delay plus the unhelpful action pushes the plant
  past recovery.

The prose is driven by simulated state: thirst, light, health, suspicion,
curiosity, regret, and whether the plant can still recover.

Run it
------
python storyworlds/worlds/gpt-5.4/droop_misunderstanding_bad_ending_curiosity_detective_story.py
python storyworlds/worlds/gpt-5.4/droop_misunderstanding_bad_ending_curiosity_detective_story.py --plant sunflower --cause thirsty --theory sabotage --action hide_in_closet
python storyworlds/worlds/gpt-5.4/droop_misunderstanding_bad_ending_curiosity_detective_story.py --cause rootbound --action skip_watering
python storyworlds/worlds/gpt-5.4/droop_misunderstanding_bad_ending_curiosity_detective_story.py --all
python storyworlds/worlds/gpt-5.4/droop_misunderstanding_bad_ending_curiosity_detective_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/droop_misunderstanding_bad_ending_curiosity_detective_story.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    living: bool = False
    movable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher_female"}
        male = {"boy", "father", "dad", "man", "teacher_male"}
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
            "teacher_female": "teacher",
            "teacher_male": "teacher",
        }.get(self.type, self.type)


@dataclass
class PlantCfg:
    id: str
    label: str
    phrase: str
    bloom: str
    plural_petals: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class PlaceCfg:
    id: str
    label: str
    phrase: str
    keeper: str
    hiding_spot: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CauseCfg:
    id: str
    label: str
    clue: str
    true_need: str
    worsened_by: set[str] = field(default_factory=set)
    spread: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class TheoryCfg:
    id: str
    label: str
    suspect: str
    hunch: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ActionCfg:
    id: str
    label: str
    effect_text: str
    discovery_text: str
    sense: int
    harms: set[str] = field(default_factory=set)
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


def _r_droop(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["stress"] < THRESHOLD:
        return out
    sig = ("droop", int(plant.meters["stress"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["droop"] = 1.0
    out.append("__droop__")
    return out


def _r_decline(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["stress"] < 2.0:
        return out
    sig = ("decline", int(plant.meters["stress"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["health"] -= 1.0
    out.append("__decline__")
    return out


def _r_death(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["health"] > 0.0:
        return out
    sig = ("dead", plant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["dead"] = 1.0
    out.append("__dead__")
    return out


RULES = [
    Rule(name="droop", tag="physical", apply=_r_droop),
    Rule(name="decline", tag="physical", apply=_r_decline),
    Rule(name="death", tag="physical", apply=_r_death),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def action_helps_cause(cause: CauseCfg, action: ActionCfg) -> bool:
    return bool(cause.worsened_by & action.harms)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for plant_id in PLANTS:
            for cause_id, cause in CAUSES.items():
                for theory_id in THEORIES:
                    for action_id, action in ACTIONS.items():
                        if action.sense >= SENSE_MIN and action_helps_cause(cause, action):
                            combos.append((place_id, plant_id, cause_id, theory_id, action_id))
    return combos


def stress_severity(cause: CauseCfg, delay: int, action: ActionCfg) -> int:
    return cause.spread + delay + len(cause.worsened_by & action.harms)


def plant_dies(cause: CauseCfg, delay: int, action: ActionCfg) -> bool:
    return stress_severity(cause, delay, action) >= 3


def predict_outcome(cause: CauseCfg, delay: int, action: ActionCfg) -> dict:
    return {
        "harmful": action_helps_cause(cause, action),
        "severity": stress_severity(cause, delay, action),
        "dies": plant_dies(cause, delay, action),
    }


def explain_rejection(cause: CauseCfg, action: ActionCfg) -> str:
    if action.sense < SENSE_MIN:
        return (
            f"(No story: action '{action.id}' is below the common-sense floor "
            f"(sense={action.sense} < {SENSE_MIN}). The world only tells detective "
            f"stories with plausible mistaken actions.)"
        )
    return (
        f"(No story: {action.label} does not actually make a {cause.label} plant worse. "
        f"The misunderstanding must have a real bad consequence, not just a guess.)"
    )


def introduce(world: World, child: Entity, sidekick: Entity, place: PlaceCfg, plant: PlantCfg) -> None:
    child.memes["curiosity"] += 1
    child.memes["play"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"{child.id} liked to solve tiny mysteries and called {child.pronoun('object')}self "
        f"a detective whenever something looked odd."
    )
    world.say(
        f"One morning, {child.id} and {sidekick.id} were in {place.phrase} when they noticed "
        f"{plant.phrase} by the window."
    )
    world.say(
        f"The {plant.label}'s head seemed to droop, and {cause_line(world)}"
    )


def cause_line(world: World) -> str:
    cause = world.facts["cause_cfg"]
    return cause.clue


def notice_and_misread(world: World, child: Entity, sidekick: Entity, theory: TheoryCfg, cause: CauseCfg) -> None:
    child.memes["suspicion"] += 1
    sidekick.memes["worry"] += 1
    world.say(
        f"{child.id} narrowed {child.pronoun('possessive')} eyes. "
        f'"This is a case," {child.pronoun()} whispered. "{theory.hunch}"'
    )
    world.say(
        f"{sidekick.id} looked from the drooping leaves to the room and felt a little unsure. "
        f"The true problem was that the plant was {cause.label}, but neither child understood that yet."
    )


def investigate(world: World, child: Entity, sidekick: Entity, place: PlaceCfg, theory: TheoryCfg) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Curiosity tugged {child.pronoun('object')} along. Instead of asking {place.keeper} at once, "
        f"{child.id} began hunting for clues around the pot, the sill, and the floor."
    )
    world.say(
        f"{child.pronoun().capitalize()} decided that {theory.suspect} must be connected somehow, "
        f"and {sidekick.id} followed because the game of detective work felt exciting."
    )


def take_action(world: World, child: Entity, sidekick: Entity, action: ActionCfg) -> None:
    plant = world.get("plant")
    child.memes["secretive"] += 1
    sidekick.memes["uneasy"] += 1
    world.say(action.effect_text.format(child=child.id, sidekick=sidekick.id))
    if "dark" in action.harms:
        plant.meters["light"] -= 1.0
    if "dry" in action.harms:
        plant.meters["water"] -= 1.0
    if "crowded" in action.harms:
        plant.meters["roots"] -= 1.0
    plant.meters["stress"] += float(len(action.harms & world.facts["cause_cfg"].worsened_by))
    propagate(world, narrate=False)


def delay_passes(world: World, child: Entity, cause: CauseCfg, delay: int) -> None:
    plant = world.get("plant")
    child.memes["worry"] += 1
    plant.meters["stress"] += cause.spread + delay
    propagate(world, narrate=False)
    world.say(
        f"Time passed while the children watched and guessed. Instead of perking up, the {plant.label} "
        f"only seemed to droop lower."
    )


def discover_truth(world: World, adult: Entity, place: PlaceCfg, cause: CauseCfg, action: ActionCfg) -> None:
    child = world.get("child")
    sidekick = world.get("sidekick")
    plant = world.get("plant")
    world.say(
        f"At last {place.keeper} came over and saw the whole scene at once."
    )
    world.say(
        f'"Oh dear," {adult.pronoun()} said softly. "No one was stealing or hiding anything. '
        f'This poor {plant.label} was {cause.label}, and {action.discovery_text}"'
    )
    child.memes["regret"] += 1
    sidekick.memes["regret"] += 1


def sad_ending(world: World, child: Entity, sidekick: Entity, place: PlaceCfg, plant_cfg: PlantCfg) -> None:
    plant = world.get("plant")
    child.memes["sadness"] += 1
    sidekick.memes["sadness"] += 1
    world.say(
        f"The grown-up tried to help, but it was too late. By afternoon, the {plant_cfg.label} was dead."
    )
    world.say(
        f"{child.id} did not feel like a detective anymore. {child.pronoun().capitalize()} stood very still, "
        f"thinking about how curiosity had rushed ahead of kindness and questions."
    )
    world.say(
        f"{place.ending_image.capitalize()}, and the brown stem gave one last droop over the rim of the pot."
    )


def tell(
    *,
    place: PlaceCfg,
    plant_cfg: PlantCfg,
    cause: CauseCfg,
    theory: TheoryCfg,
    action: ActionCfg,
    child_name: str = "Nell",
    child_gender: str = "girl",
    sidekick_name: str = "Owen",
    sidekick_gender: str = "boy",
    adult_type: str = "teacher_female",
    delay: int = 1,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="detective"))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=sidekick_gender, label=sidekick_name, role="friend"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the grown-up", role="keeper"))
    plant = world.add(Entity(id="plant", kind="thing", type="plant", label=plant_cfg.label, phrase=plant_cfg.phrase, living=True, movable=True))
    child.attrs["name"] = child_name
    sidekick.attrs["name"] = sidekick_name
    adult.attrs["name"] = "Ms. Reed" if adult_type == "teacher_female" else "Mr. Reed"
    plant.meters["health"] = 1.0

    world.facts.update(
        place_cfg=place,
        plant_cfg=plant_cfg,
        cause_cfg=cause,
        theory_cfg=theory,
        action_cfg=action,
        delay=delay,
        child=child,
        sidekick=sidekick,
        adult=adult,
        predicted=predict_outcome(cause, delay, action),
    )

    introduce(world, child, sidekick, place, plant_cfg)
    notice_and_misread(world, child, sidekick, theory, cause)

    world.para()
    investigate(world, child, sidekick, place, theory)
    take_action(world, child, sidekick, action)
    delay_passes(world, child, cause, delay)

    world.para()
    discover_truth(world, adult, place, cause, action)
    sad_ending(world, child, sidekick, place, plant_cfg)

    world.facts.update(
        outcome="dead" if plant.meters["dead"] >= THRESHOLD else "wilted",
        actual_dead=plant.meters["dead"] >= THRESHOLD,
        stress=plant.meters["stress"],
        droop=plant.meters["droop"] >= THRESHOLD,
    )
    return world


PLANTS = {
    "sunflower": PlantCfg(
        id="sunflower",
        label="sunflower",
        phrase="the class sunflower in a painted pot",
        bloom="a wide yellow face",
        tags={"plant", "flower"},
    ),
    "bean": PlantCfg(
        id="bean",
        label="bean plant",
        phrase="the bean plant with a thin green stem",
        bloom="small white blossoms",
        tags={"plant", "bean"},
    ),
    "daisy": PlantCfg(
        id="daisy",
        label="daisy",
        phrase="the little daisy on the reading shelf",
        bloom="a white flower head",
        tags={"plant", "flower"},
    ),
}

PLACES = {
    "classroom": PlaceCfg(
        id="classroom",
        label="classroom",
        phrase="their classroom",
        keeper="their teacher",
        hiding_spot="the supply closet",
        ending_image="the classroom felt strangely quiet beside the window",
        tags={"school"},
    ),
    "library": PlaceCfg(
        id="library",
        label="library",
        phrase="the library corner at school",
        keeper="the librarian",
        hiding_spot="the dark return cart nook",
        ending_image="the pages on the nearby table stayed open in the hush",
        tags={"school", "library"},
    ),
    "hallway": PlaceCfg(
        id="hallway",
        label="hallway",
        phrase="the sunny hallway outside the art room",
        keeper="the art teacher",
        hiding_spot="the tall cabinet by the sink",
        ending_image="the long hallway gleamed, but the pot looked lonelier than before",
        tags={"school"},
    ),
}

CAUSES = {
    "thirsty": CauseCfg(
        id="thirsty",
        label="thirsty",
        clue="the soil looked pale and crumbly, but to curious eyes it seemed like scattered evidence.",
        true_need="water",
        worsened_by={"dry", "dark"},
        spread=1,
        tags={"water", "plant"},
    ),
    "too_dark": CauseCfg(
        id="too_dark",
        label="stuck in too much shade",
        clue="the leaves leaned hard toward the window, though that looked like sneaking to a detective mind.",
        true_need="sunlight",
        worsened_by={"dark"},
        spread=1,
        tags={"sunlight", "plant"},
    ),
    "rootbound": CauseCfg(
        id="rootbound",
        label="crowded in its pot",
        clue="tiny roots poked from the drain hole, which looked almost like a secret message.",
        true_need="a bigger pot",
        worsened_by={"crowded", "dry"},
        spread=1,
        tags={"roots", "plant"},
    ),
}

THEORIES = {
    "sabotage": TheoryCfg(
        id="sabotage",
        label="sabotage",
        suspect="a secret plant-hurter",
        hunch="Someone hurt this flower on purpose.",
        tags={"misunderstanding", "mystery"},
    ),
    "stolen_sun": TheoryCfg(
        id="stolen_sun",
        label="stolen sun",
        suspect="whoever moved the blinds",
        hunch="Someone stole its sunshine and tried to hide the clue.",
        tags={"misunderstanding", "mystery", "sun"},
    ),
    "night_hiding": TheoryCfg(
        id="night_hiding",
        label="night hiding",
        suspect="the shelf itself",
        hunch="It must be hiding from a nighttime villain.",
        tags={"misunderstanding", "mystery"},
    ),
}

ACTIONS = {
    "skip_watering": ActionCfg(
        id="skip_watering",
        label="keeping the plant dry to preserve clues",
        effect_text=(
            '{child} whispered that detectives should not "wash away the evidence," '
            'so {child} and {sidekick} left the soil dry and watched the pot instead of asking for water.'
        ),
        discovery_text="keeping it dry only made the thirst worse.",
        sense=2,
        harms={"dry"},
        tags={"water", "mistake"},
    ),
    "hide_in_closet": ActionCfg(
        id="hide_in_closet",
        label="hiding the plant in a dark place to catch the culprit",
        effect_text=(
            "{child} lifted the pot with great care, and the two children tucked it into a dark corner "
            "so they could wait for the imaginary culprit to return."
        ),
        discovery_text="putting it in the dark made the poor thing weaker.",
        sense=2,
        harms={"dark"},
        tags={"dark", "mistake"},
    ),
    "tie_in_same_pot": ActionCfg(
        id="tie_in_same_pot",
        label="tying the stem upright without fixing the cramped roots",
        effect_text=(
            "{child} decided the droop must be part of a struggle, so {child} tied the stem to a ruler "
            "and pressed the crowded soil down harder, certain that neatness would solve the mystery."
        ),
        discovery_text="pressing the soil and leaving it cramped hurt the roots even more.",
        sense=2,
        harms={"crowded"},
        tags={"roots", "mistake"},
    ),
    "close_blinds_and_wait": ActionCfg(
        id="close_blinds_and_wait",
        label="closing the blinds for a stakeout",
        effect_text=(
            "{child} pulled the blinds almost shut and said a real detective should watch from the shadows, "
            "so the stakeout lasted all through quiet reading time."
        ),
        discovery_text="the long wait in the dim room stole the light it needed.",
        sense=2,
        harms={"dark", "dry"},
        tags={"dark", "water", "mistake"},
    ),
    "shake_for_fingerprint": ActionCfg(
        id="shake_for_fingerprint",
        label="shaking the pot for fingerprints",
        effect_text=(
            "{child} gently wiggled the pot, hoping some clue would fall out, but nothing did except a little dust."
        ),
        discovery_text="that did not explain the droop, and it was not the real problem anyway.",
        sense=1,
        harms=set(),
        tags={"mistake"},
    ),
}

GIRL_NAMES = ["Nell", "Mia", "Tess", "Lila", "Ruby", "June", "Eva", "Ivy"]
BOY_NAMES = ["Owen", "Max", "Ben", "Theo", "Finn", "Eli", "Sam", "Leo"]


@dataclass
class StoryParams:
    place: str
    plant: str
    cause: str
    theory: str
    action: str
    child_name: str
    child_gender: str
    sidekick_name: str
    sidekick_gender: str
    adult_type: str
    delay: int = 1
    seed: Optional[int] = None


KNOWLEDGE = {
    "plant": [
        (
            "What can make a plant droop?",
            "A plant can droop when it does not have what it needs, like enough water, enough light, or room for its roots. Drooping is often a sign that something is wrong, not a clue in a mystery.",
        )
    ],
    "water": [
        (
            "Why does a thirsty plant droop?",
            "Water helps a plant keep its stems and leaves firm. When the plant is thirsty, those parts lose their stiffness and begin to sag.",
        )
    ],
    "sunlight": [
        (
            "Why do plants need sunlight?",
            "Plants use sunlight to make food for themselves. If they stay in too much darkness, they grow weak and unhealthy.",
        )
    ],
    "roots": [
        (
            "What does it mean when a plant is crowded in its pot?",
            "It means the roots do not have enough room to spread. Then the plant can have trouble finding water and staying healthy.",
        )
    ],
    "mystery": [
        (
            "What does a detective do first in a real mystery?",
            "A good detective looks carefully and asks honest questions before making a big guess. Guessing too soon can lead to a misunderstanding.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what is going on, but they are wrong. It can cause trouble if nobody stops to check the truth.",
        )
    ],
}
KNOWLEDGE_ORDER = ["plant", "water", "sunlight", "roots", "mystery", "misunderstanding"]


CURATED = [
    StoryParams(
        place="classroom",
        plant="sunflower",
        cause="thirsty",
        theory="sabotage",
        action="hide_in_closet",
        child_name="Nell",
        child_gender="girl",
        sidekick_name="Owen",
        sidekick_gender="boy",
        adult_type="teacher_female",
        delay=1,
    ),
    StoryParams(
        place="library",
        plant="daisy",
        cause="too_dark",
        theory="stolen_sun",
        action="close_blinds_and_wait",
        child_name="Ruby",
        child_gender="girl",
        sidekick_name="Ben",
        sidekick_gender="boy",
        adult_type="teacher_female",
        delay=1,
    ),
    StoryParams(
        place="hallway",
        plant="bean",
        cause="rootbound",
        theory="night_hiding",
        action="tie_in_same_pot",
        child_name="Theo",
        child_gender="boy",
        sidekick_name="Ivy",
        sidekick_gender="girl",
        adult_type="teacher_male",
        delay=1,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sidekick = f["sidekick"]
    place = f["place_cfg"]
    plant = f["plant_cfg"]
    cause = f["cause_cfg"]
    theory = f["theory_cfg"]
    action = f["action_cfg"]
    return [
        f'Write a child-facing detective story that includes the word "droop" and ends sadly.',
        f"Tell a mystery-style story where {child.attrs['name']} grows curious about a drooping {plant.label} in {place.label}, misunderstands the cause, and makes a bad choice.",
        f"Write a story about {child.attrs['name']} and {sidekick.attrs['name']} acting like detectives after they see a {cause.label} {plant.label}, wrongly believing {theory.label}, and secretly {action.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    sidekick = f["sidekick"]
    place = f["place_cfg"]
    plant = f["plant_cfg"]
    cause = f["cause_cfg"]
    theory = f["theory_cfg"]
    action = f["action_cfg"]
    adult = f["adult"]
    child_name = child.attrs["name"]
    sidekick_name = sidekick.attrs["name"]
    adult_word = adult.label_word
    return [
        (
            "Who were the detectives in the story?",
            f"The child detectives were {child_name} and {sidekick_name}. They treated the drooping {plant.label} like a mystery to solve.",
        ),
        (
            f"What first made {child_name} curious?",
            f"{child_name} noticed that the {plant.label} seemed to droop. That odd sight made the plant feel like a case instead of a living thing that needed help.",
        ),
        (
            f"What misunderstanding did {child_name} have?",
            f"{child_name} thought the problem was {theory.label} and looked for a culprit. But the real problem was that the {plant.label} was {cause.label}.",
        ),
        (
            f"What did the children do that made things worse?",
            f"They chose {action.label}. That was a mistake because {action.discovery_text[:-1]}",
        ),
        (
            "Why did the story end sadly?",
            f"It ended sadly because the children spent time guessing instead of asking {place.keeper} for help. By the time the truth was understood, the {plant.label} was too weak to recover.",
        ),
        (
            f"What did {child_name} learn at the end?",
            f"{child_name} learned that curiosity is not enough by itself. A careful detective asks questions and checks the truth before acting on a guess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["plant_cfg"].tags) | set(f["cause_cfg"].tags) | set(f["theory_cfg"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:9} ({e.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonableness gate: only actions that actually worsen the real problem.
helpful_harm(C, A) :- worsened_by(C, H), harms(A, H).
valid(P, Pl, C, T, A) :- place(P), plant(Pl), cause(C), theory(T), action(A),
                         sense(A, S), sense_min(M), S >= M, helpful_harm(C, A).

% Outcome: plant dies when spread + delay + number of matching harms reaches 3.
match_count(C, A, N) :- N = #count { H : worsened_by(C, H), harms(A, H) }, cause(C), action(A).
severity(C, A, D, V) :- cause_spread(C, S), match_count(C, A, N), delay(D), V = S + D + N.
dies(C, A, D) :- severity(C, A, D, V), V >= 3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PLANTS:
        lines.append(asp.fact("plant", pid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_spread", cid, cause.spread))
        for harm in sorted(cause.worsened_by):
            lines.append(asp.fact("worsened_by", cid, harm))
    for tid in THEORIES:
        lines.append(asp.fact("theory", tid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, action.sense))
        for harm in sorted(action.harms):
            lines.append(asp.fact("harms", aid, harm))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_dies(cause: str, action: str, delay: int) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("delay", delay),
            asp.fact("chosen", cause, action),
            f"chosen_dies :- chosen(C, A), dies(C, A, {delay}).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show chosen_dies/0."))
    return bool(asp.atoms(model, "chosen_dies"))


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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        py = plant_dies(CAUSES[params.cause], params.delay, ACTIONS[params.action])
        cl = asp_dies(params.cause, params.action, params.delay)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke-tested normal generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style storyworld: a curious child misunderstands a drooping plant and causes a sad ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--theory", choices=THEORIES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time spent guessing before a grown-up notices")
    ap.add_argument("--adult", choices=["teacher_female", "teacher_male"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.action:
        cause = CAUSES[args.cause]
        action = ACTIONS[args.action]
        if not (action.sense >= SENSE_MIN and action_helps_cause(cause, action)):
            raise StoryError(explain_rejection(cause, action))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.plant is None or c[1] == args.plant)
        and (args.cause is None or c[2] == args.cause)
        and (args.theory is None or c[3] == args.theory)
        and (args.action is None or c[4] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, plant, cause, theory, action = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    sidekick_gender = "boy" if child_gender == "girl" else "girl"
    child_name = pick_name(rng, child_gender)
    sidekick_name = pick_name(rng, sidekick_gender, avoid=child_name)
    adult_type = args.adult or rng.choice(["teacher_female", "teacher_male"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        place=place,
        plant=plant,
        cause=cause,
        theory=theory,
        action=action,
        child_name=child_name,
        child_gender=child_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        adult_type=adult_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        plant = PLANTS[params.plant]
        cause = CAUSES[params.cause]
        theory = THEORIES[params.theory]
        action = ACTIONS[params.action]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not (action.sense >= SENSE_MIN and action_helps_cause(cause, action)):
        raise StoryError(explain_rejection(cause, action))
    if not plant_dies(cause, params.delay, action):
        raise StoryError("(No story: this combination does not lead to the required sad ending.)")

    world = tell(
        place=place,
        plant_cfg=plant,
        cause=cause,
        theory=theory,
        action=action,
        child_name=params.child_name,
        child_gender=params.child_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        adult_type=params.adult_type,
        delay=params.delay,
    )

    story_text = world.render().replace("child", params.child_name).replace("sidekick", params.sidekick_name)
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/5.\n#show dies/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible detective-story combos:\n")
        for place, plant, cause, theory, action in combos:
            print(f"  {place:10} {plant:10} {cause:10} {theory:12} {action}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            try:
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.child_name}: {p.plant} in {p.place} ({p.cause}, {p.theory}, {p.action})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
