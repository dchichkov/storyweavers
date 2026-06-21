#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/modify_acrobatics_mystery_to_solve_inner_monologue.py
================================================================================

A small myth-shaped storyworld about a child apprentice who must solve a gentle
mystery before a temple festival begins. A sacred object has been moved, a clue
points toward the hidden truth, and the hero's inner monologue helps them
replace blame with understanding. The ending turns on a wise modification to the
festival's acrobatics so the world is safer for a small creature.

Run it
------
    python storyworlds/worlds/gpt-5.4/modify_acrobatics_mystery_to_solve_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/modify_acrobatics_mystery_to_solve_inner_monologue.py --artifact sun_ribbon
    python storyworlds/worlds/gpt-5.4/modify_acrobatics_mystery_to_solve_inner_monologue.py --culprit ember_fox
    python storyworlds/worlds/gpt-5.4/modify_acrobatics_mystery_to_solve_inner_monologue.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "goddess", "mother"}
        male = {"boy", "man", "god", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name_or_label(self) -> str:
        return self.id if self.kind == "character" else self.label


@dataclass
class Festival:
    id: str
    temple: str
    sky_image: str
    opening: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    resting_place: str
    ceremony_use: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    text: str
    thought: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    path_text: str
    find_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    type: str
    clue: str
    spots: set[str]
    targets: set[str]
    adjustments: set[str]
    concern: str
    confession: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Adjustment:
    id: str
    label: str
    plan_text: str
    perform_text: str
    effect_text: str
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


def _r_missing_worry(world: World) -> list[str]:
    artifact = world.get("artifact")
    hero = world.get("hero")
    if artifact.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", artifact.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["duty"] += 1
    return []


def _r_clue_curiosity(world: World) -> list[str]:
    clue = world.get("clue")
    hero = world.get("hero")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_curiosity", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["wonder"] += 1
    return []


def _r_truth_relief(world: World) -> list[str]:
    culprit = world.get("culprit")
    hero = world.get("hero")
    elder = world.get("elder")
    if culprit.meters["understood"] < THRESHOLD:
        return []
    sig = ("truth_relief", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] = 0.0
    hero.memes["compassion"] += 1
    elder.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="clue_curiosity", tag="emotion", apply=_r_clue_curiosity),
    Rule(name="truth_relief", tag="emotion", apply=_r_truth_relief),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


FESTIVALS = {
    "sun_steps": Festival(
        id="sun_steps",
        temple="the Temple of Seven Winds",
        sky_image="high cliffs where dawn always seemed to arrive a little early",
        opening="the children of the temple would greet the sun with music and acrobatics on a long painted court",
        closing="the mountain seemed to accept the new kindness and pour gold across the stones",
        tags={"myth", "festival"},
    ),
    "moon_bridge": Festival(
        id="moon_bridge",
        temple="the Moon-Bridge Shrine",
        sky_image="white stairs cut into a hill above a silver river",
        opening="the young keepers would honor the sky with ribbons, bells, and acrobatics under hanging lamps",
        closing="the river held the lamps like a second sky and the whole shrine glowed softly",
        tags={"myth", "festival"},
    ),
}

ARTIFACTS = {
    "sun_ribbon": Artifact(
        id="sun_ribbon",
        label="sun ribbon",
        phrase="the long sun ribbon",
        resting_place="the eastern hook beside the court",
        ceremony_use="to begin the first circling leap",
        ending_image="the sun ribbon streamed behind the dancers like a piece of morning",
        tags={"ribbon", "festival"},
    ),
    "moon_mask": Artifact(
        id="moon_mask",
        label="moon mask",
        phrase="the carved moon mask",
        resting_place="the cedar stand by the shrine door",
        ceremony_use="for the balance dance before the lamps were lit",
        ending_image="the moon mask shone pale and calm above the smiling face beneath it",
        tags={"mask", "festival"},
    ),
    "bronze_hoop": Artifact(
        id="bronze_hoop",
        label="bronze hoop",
        phrase="the bronze hoop",
        resting_place="the polished peg near the drum",
        ceremony_use="for the bright acrobatics at the heart of the festival",
        ending_image="the bronze hoop flashed once in the lamplight and then settled into gentle hands",
        tags={"acrobatics", "festival"},
    ),
}

CLUES = {
    "silver_down": Clue(
        id="silver_down",
        label="silver down",
        text="a curl of silver down caught on the hook",
        thought="Silver down does not walk by itself, the child thought. Something from the high air brushed past here.",
        tags={"feather", "clue"},
    ),
    "reed_drops": Clue(
        id="reed_drops",
        label="reed drops",
        text="tiny water drops and a bent reed on the floor",
        thought="Those drops are too neat for spilled water, the child thought. Someone from the pool came in quietly.",
        tags={"reed", "water", "clue"},
    ),
    "ash_paws": Clue(
        id="ash_paws",
        label="ash paw marks",
        text="three ash-gray paw marks near the empty place",
        thought="Ash tells its own story, the child thought. A warm little creature came from the kiln side.",
        tags={"ash", "clue"},
    ),
}

SPOTS = {
    "bell_nest": Spot(
        id="bell_nest",
        label="the bell tower nest",
        path_text="up the bell stairs where the air smelled of cedar and cloud",
        find_text="inside a nest woven between the silent bells",
        tags={"tower", "nest"},
    ),
    "lotus_reeds": Spot(
        id="lotus_reeds",
        label="the lotus reeds",
        path_text="down the moon path to the pool where reeds whispered at the water's edge",
        find_text="beneath a bent arch of lotus leaves",
        tags={"pool", "reeds"},
    ),
    "warm_kiln": Spot(
        id="warm_kiln",
        label="the warm kiln alcove",
        path_text="behind the kitchen shrine where old kiln stones still held last night's heat",
        find_text="beside a stack of warm bricks in a quiet red alcove",
        tags={"kiln", "warmth"},
    ),
}

CULPRITS = {
    "cloud_foal": Culprit(
        id="cloud_foal",
        label="cloud foal",
        phrase="a young cloud foal no bigger than a goat, with silver fluff along its neck",
        type="spirit",
        clue="silver_down",
        spots={"bell_nest"},
        targets={"sun_ribbon", "moon_mask"},
        adjustments={"soft_start", "high_path"},
        concern="the great opening crash of bells would frighten its sleepy new chick in the tower nest",
        confession='"I did not steal it," the cloud foal murmured. "I hid it because the first thunder of the festival was too loud for a baby sky-bird."',
        tags={"cloud_foal", "gentleness"},
    ),
    "reed_sprite": Culprit(
        id="reed_sprite",
        label="reed sprite",
        phrase="a reed sprite with green hair and bright wet eyes",
        type="spirit",
        clue="reed_drops",
        spots={"lotus_reeds"},
        targets={"moon_mask", "sun_ribbon"},
        adjustments={"soft_steps", "water_circle"},
        concern="heavy stamping would shake the shallow pool where tiny eggs rested under the reeds",
        confession='"I only borrowed it," said the reed sprite. "If the court booms too hard, the eggs in the pool may tremble and split before their time."',
        tags={"reed_sprite", "water"},
    ),
    "ember_fox": Culprit(
        id="ember_fox",
        label="ember fox",
        phrase="an ember fox with a tail like a red brush-tip",
        type="spirit",
        clue="ash_paws",
        spots={"warm_kiln"},
        targets={"bronze_hoop", "sun_ribbon"},
        adjustments={"high_path", "torch_shift"},
        concern="the leaping ring path would drive sparks toward a sleeping litter tucked in the warm bricks",
        confession='"I pulled it away before the sparks began," the ember fox said. "Little ones are sleeping nearby, and your fast ring dance would have sent heat right over them."',
        tags={"ember_fox", "fire"},
    ),
}

ADJUSTMENTS = {
    "soft_start": Adjustment(
        id="soft_start",
        label="a soft beginning",
        plan_text="begin with one flute and a bow before any loud bells",
        perform_text="So the festival opened with a single flute note, then a slow bow, and only later did the bells answer softly.",
        effect_text="The quiet beginning let the tower nest stay calm while the people still welcomed the day.",
        tags={"flute", "gentle"},
    ),
    "high_path": Adjustment(
        id="high_path",
        label="a higher path",
        plan_text="modify the acrobatics so the leaps traveled along the upper painted line, far from the hidden resting place",
        perform_text="So the acrobatics rose along the upper painted line, bright and careful, with every leap turning away from the fragile place below.",
        effect_text="The new path kept heat and feet away from the little creatures while the dance still looked brave.",
        tags={"modify", "acrobatics"},
    ),
    "soft_steps": Adjustment(
        id="soft_steps",
        label="soft steps",
        plan_text="trade the stamping steps for light toe-taps and hand bells",
        perform_text="So the dancers gave toe-taps and little bell-shakes instead of hard stamping.",
        effect_text="The pool stayed still, and the eggs under the reeds did not shiver.",
        tags={"bells", "gentle"},
    ),
    "water_circle": Adjustment(
        id="water_circle",
        label="a water circle",
        plan_text="move the dance into a wide outer circle so no one pounded near the pool",
        perform_text="So the dance widened into a moon-bright circle around the far edge of the court.",
        effect_text="The shrine still felt festive, but the quiet pool kept its peace.",
        tags={"circle", "gentle"},
    ),
    "torch_shift": Adjustment(
        id="torch_shift",
        label="shifted torches",
        plan_text="move the torch stands to the north wall before the ring dance began",
        perform_text="So the elder moved the torches to the north wall, and the firelight watched from a safer distance.",
        effect_text="No sparks reached the warm bricks, and the sleeping litter stayed safe.",
        tags={"fire", "safety"},
    ),
}


def compatible(culprit: Culprit, artifact: Artifact, clue: Clue, spot: Spot, adjustment: Adjustment) -> bool:
    return (
        clue.id == culprit.clue
        and artifact.id in culprit.targets
        and spot.id in culprit.spots
        and adjustment.id in culprit.adjustments
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for festival_id in FESTIVALS:
        for artifact_id, artifact in ARTIFACTS.items():
            for culprit_id, culprit in CULPRITS.items():
                for clue_id, clue in CLUES.items():
                    for spot_id, spot in SPOTS.items():
                        for adjustment_id, adjustment in ADJUSTMENTS.items():
                            if compatible(culprit, artifact, clue, spot, adjustment):
                                combos.append(
                                    (festival_id, artifact_id, culprit_id, clue_id, spot_id, adjustment_id)
                                )
    return combos


@dataclass
class StoryParams:
    festival: str
    artifact: str
    culprit: str
    clue: str
    spot: str
    adjustment: str
    hero_name: str
    hero_gender: str
    elder_type: str
    hero_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        festival="sun_steps",
        artifact="sun_ribbon",
        culprit="cloud_foal",
        clue="silver_down",
        spot="bell_nest",
        adjustment="soft_start",
        hero_name="Iria",
        hero_gender="girl",
        elder_type="woman",
        hero_trait="nimble",
    ),
    StoryParams(
        festival="moon_bridge",
        artifact="moon_mask",
        culprit="reed_sprite",
        clue="reed_drops",
        spot="lotus_reeds",
        adjustment="soft_steps",
        hero_name="Tarin",
        hero_gender="boy",
        elder_type="woman",
        hero_trait="watchful",
    ),
    StoryParams(
        festival="sun_steps",
        artifact="bronze_hoop",
        culprit="ember_fox",
        clue="ash_paws",
        spot="warm_kiln",
        adjustment="high_path",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="man",
        hero_trait="thoughtful",
    ),
    StoryParams(
        festival="moon_bridge",
        artifact="sun_ribbon",
        culprit="ember_fox",
        clue="ash_paws",
        spot="warm_kiln",
        adjustment="torch_shift",
        hero_name="Daro",
        hero_gender="boy",
        elder_type="man",
        hero_trait="swift",
    ),
    StoryParams(
        festival="sun_steps",
        artifact="moon_mask",
        culprit="cloud_foal",
        clue="silver_down",
        spot="bell_nest",
        adjustment="high_path",
        hero_name="Sena",
        hero_gender="girl",
        elder_type="woman",
        hero_trait="quiet",
    ),
]

GIRL_NAMES = ["Iria", "Mira", "Sena", "Luma", "Neri", "Aya", "Tala", "Orin"]
BOY_NAMES = ["Tarin", "Daro", "Pelin", "Sorin", "Kavi", "Nilo", "Rami", "Eran"]
TRAITS = ["nimble", "watchful", "thoughtful", "quiet", "swift", "careful"]


def explain_rejection(
    artifact: Optional[Artifact],
    culprit: Optional[Culprit],
    clue: Optional[Clue],
    spot: Optional[Spot],
    adjustment: Optional[Adjustment],
) -> str:
    if culprit and clue and clue.id != culprit.clue:
        return (
            f"(No story: {clue.label} does not point to the {culprit.label}. "
            f"That spirit leaves {CLUES[culprit.clue].label} instead.)"
        )
    if culprit and artifact and artifact.id not in culprit.targets:
        return (
            f"(No story: the {culprit.label} would not sensibly move the {artifact.label}. "
            f"Pick an artifact that matches its concern.)"
        )
    if culprit and spot and spot.id not in culprit.spots:
        return (
            f"(No story: the {culprit.label} would not hide anything at {spot.label}. "
            f"Choose one of its plausible hiding places.)"
        )
    if culprit and adjustment and adjustment.id not in culprit.adjustments:
        return (
            f"(No story: {adjustment.label} does not solve the {culprit.label}'s problem. "
            f"The fix must answer the creature's actual concern.)"
        )
    return "(No valid combination matches the given options.)"


def predict_truth(world: World, culprit_id: str, artifact_id: str, adjustment_id: str) -> dict:
    sim = world.copy()
    culprit = CULPRITS[culprit_id]
    artifact = ARTIFACTS[artifact_id]
    adjustment = ADJUSTMENTS[adjustment_id]
    sim.facts["predicted_care"] = culprit.concern
    return {
        "artifact_can_return": artifact.id in culprit.targets,
        "adjustment_helps": adjustment.id in culprit.adjustments,
        "concern": culprit.concern,
    }


def introduce(world: World, hero: Entity, elder: Entity, festival: Festival, artifact: Artifact) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In {festival.temple}, among {festival.sky_image}, lived {hero.id}, a {hero.traits[0]} temple child "
        f"who loved stories of gods, birds, and brave feet on painted stone."
    )
    world.say(
        f"On the morning of the festival, {festival.opening}. {hero.id}'s task was to carry {artifact.phrase} "
        f"from {artifact.resting_place} and set it ready {artifact.ceremony_use}."
    )
    world.say(
        f"{elder.id}, the old keeper of the court, smiled and said, "
        f'"Today your hands must be steady, and your heart must listen as carefully as your eyes."'
    )


def discover_missing(world: World, hero: Entity, artifact: Artifact) -> None:
    world.get("artifact").meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} reached {artifact.resting_place}, the place was empty. "
        f"{artifact.phrase.capitalize()} was gone."
    )
    world.say(
        f'{hero.id} felt a cold flutter under {hero.pronoun("possessive")} ribs. '
        f'"If the festival cannot begin, will the mountain think we forgot our promise?" {hero.pronoun()} wondered.'
    )


def search_clue(world: World, hero: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} knelt by the empty place and found {clue.text}."
    )
    world.say(clue.thought)


def consult_elder(world: World, hero: Entity, elder: Entity, culprit: Culprit, artifact: Artifact, adjustment: Adjustment) -> None:
    pred = predict_truth(world, culprit.id, artifact.id, adjustment.id)
    world.facts["predicted_concern"] = pred["concern"]
    world.say(
        f'{hero.id} ran to {elder.id}. "Someone has taken {artifact.phrase}," {hero.pronoun()} said.'
    )
    world.say(
        f'{elder.id} did not scold. "{hero.id}," {elder.pronoun()} said, '
        f'"the world of a temple has many hands in it. Find why before you decide who."'
    )
    world.say(
        f'{hero.id} breathed once and thought, "Then I must solve the mystery with more than fear. '
        f'Maybe I must modify my guess before I speak it aloud."'
    )


def follow_path(world: World, hero: Entity, spot: Spot) -> None:
    hero.meters["steps_taken"] += 1
    world.say(
        f"So {hero.id} followed the sign {spot.path_text}."
    )


def meet_culprit(world: World, hero: Entity, culprit: Culprit, spot: Spot, artifact: Artifact) -> None:
    culprit_ent = world.get("culprit")
    world.say(
        f"There, {spot.find_text}, waited {culprit.phrase}, curled protectively around {artifact.phrase}."
    )
    world.say(culprit.confession)
    culprit_ent.meters["understood"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} looked more carefully and finally saw what had been hidden at first: "
        f"{culprit.concern}"
    )


def choose_mercy(world: World, hero: Entity, elder: Entity, adjustment: Adjustment) -> None:
    hero.memes["wisdom"] += 1
    world.say(
        f'"Then the mystery is not about meanness," {hero.id} thought. '
        f'"It is about something small asking for room."'
    )
    world.say(
        f"{hero.id} bowed to the creature and carried the truth back to {elder.id}. "
        f"Together they chose {adjustment.label}: they would {adjustment.plan_text}."
    )


def return_and_perform(world: World, hero: Entity, elder: Entity, artifact: Artifact, adjustment: Adjustment, festival: Festival) -> None:
    artifact_ent = world.get("artifact")
    artifact_ent.meters["missing"] = 0.0
    artifact_ent.meters["returned"] += 1
    hero.memes["joy"] += 1
    elder.memes["trust"] += 1
    world.say(
        f"{elder.id} nodded as if this answer had been waiting in the stones all along. "
        f'"A festival is strongest when it makes room for life," {elder.pronoun()} said.'
    )
    world.say(adjustment.perform_text)
    world.say(
        f"{artifact.ending_image}. {adjustment.effect_text} In that hour, {festival.closing}."
    )


def tell(
    festival: Festival,
    artifact: Artifact,
    culprit: Culprit,
    clue: Clue,
    spot: Spot,
    adjustment: Adjustment,
    hero_name: str = "Iria",
    hero_gender: str = "girl",
    elder_type: str = "woman",
    hero_trait: str = "nimble",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[hero_trait],
            label=hero_name,
            tags={"hero"},
        )
    )
    elder_name = "Elder Sorel" if elder_type == "man" else "Elder Nema"
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            tags={"elder"},
        )
    )
    world.add(
        Entity(
            id="artifact",
            kind="thing",
            type="artifact",
            label=artifact.label,
            phrase=artifact.phrase,
            tags=set(artifact.tags),
        )
    )
    world.add(
        Entity(
            id="clue",
            kind="thing",
            type="clue",
            label=clue.label,
            tags=set(clue.tags),
        )
    )
    world.add(
        Entity(
            id="culprit",
            kind="thing",
            type=culprit.type,
            label=culprit.label,
            phrase=culprit.phrase,
            tags=set(culprit.tags),
        )
    )

    introduce(world, hero, elder, festival, artifact)
    world.para()
    discover_missing(world, hero, artifact)
    search_clue(world, hero, clue)
    consult_elder(world, hero, elder, culprit, artifact, adjustment)
    world.para()
    follow_path(world, hero, spot)
    meet_culprit(world, hero, culprit, spot, artifact)
    choose_mercy(world, hero, elder, adjustment)
    world.para()
    return_and_perform(world, hero, elder, artifact, adjustment, festival)

    world.facts.update(
        festival=festival,
        artifact_cfg=artifact,
        clue_cfg=clue,
        culprit_cfg=culprit,
        spot_cfg=spot,
        adjustment_cfg=adjustment,
        hero=hero,
        elder=elder,
        solved=True,
        returned=world.get("artifact").meters["returned"] >= THRESHOLD,
        modified="modify" in adjustment.plan_text,
    )
    return world


KNOWLEDGE = {
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story that often explains a place, a custom, or a mystery with gods, spirits, or magical creatures."
        )
    ],
    "acrobatics": [
        (
            "What are acrobatics?",
            "Acrobatics are careful jumps, balances, bends, and turns that take strength and control. Performers practice them so their bodies can move safely and gracefully."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure out something hidden. It does not answer the mystery by itself, but it points your thinking in the right direction."
        )
    ],
    "feather": [
        (
            "Why can a feather be a clue?",
            "A feather or bit of down can show that a bird or flying creature passed by. Small things can tell big stories if you notice them carefully."
        )
    ],
    "reed": [
        (
            "Why do reeds grow near water?",
            "Reeds like wet ground, so they grow by ponds and river edges. Seeing a reed indoors can hint that something came from the water."
        )
    ],
    "ash": [
        (
            "What does ash show?",
            "Ash shows that something was near fire or warm coals. It can cling to paws, feet, or cloth and leave a trail behind."
        )
    ],
    "gentle": [
        (
            "Why is being gentle important?",
            "Being gentle helps protect small or fragile living things. A strong person can still choose a soft way to act."
        )
    ],
    "festival": [
        (
            "What is a festival?",
            "A festival is a special time when people gather to celebrate with music, food, stories, or dancing. Many festivals also remember promises or traditions."
        )
    ],
    "fire": [
        (
            "Why should fire be moved carefully?",
            "Fire gives light and warmth, but sparks can travel where you do not expect. Moving torches carefully helps keep people, nests, and homes safe."
        )
    ],
    "water": [
        (
            "Why can loud stomping matter near water?",
            "Hard stomping can shake the ground and send ripples through shallow water. For tiny eggs or sleeping creatures, even a small shake can matter."
        )
    ],
}

KNOWLEDGE_ORDER = ["myth", "festival", "acrobatics", "clue", "feather", "reed", "ash", "gentle", "fire", "water"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    artifact = f["artifact_cfg"]
    culprit = f["culprit_cfg"]
    adjustment = f["adjustment_cfg"]
    festival = f["festival"]
    return [
        f'Write a short myth-like story for a 3-to-5-year-old that includes the words "modify" and "acrobatics" and begins with a missing ceremonial object.',
        f"Tell a gentle mystery-to-solve story where {hero.id} notices that {artifact.phrase} is missing before a festival at {festival.temple}, follows a clue, and learns a creature moved it for a caring reason.",
        f"Write a child-facing myth with inner monologue in which the hero first feels afraid, then decides to modify a mistaken guess, and the ending changes the acrobatics because of {culprit.label}'s concern.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    artifact = f["artifact_cfg"]
    clue = f["clue_cfg"]
    culprit = f["culprit_cfg"]
    spot = f["spot_cfg"]
    adjustment = f["adjustment_cfg"]
    festival = f["festival"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young temple child, and {elder.id}, the elder who helps {hero.pronoun('object')} think wisely. The mystery begins when {artifact.phrase} disappears before the festival."
        ),
        (
            f"What was the mystery?",
            f"The mystery was where {artifact.phrase} had gone and who moved it. The festival needed it, so its empty place made the problem feel urgent right away."
        ),
        (
            f"What clue did {hero.id} find?",
            f"{hero.id} found {clue.text}. That clue mattered because it pointed toward the kind of creature that had passed by."
        ),
        (
            f"How did {hero.id}'s inner thoughts help solve the problem?",
            f"{hero.id} stopped and listened to {hero.pronoun('possessive')} own thoughts instead of making a quick accusation. By deciding to modify {hero.pronoun('possessive')} first guess, {hero.pronoun()} stayed curious long enough to find the true reason."
        ),
        (
            f"Where was {artifact.phrase}?",
            f"It was hidden at {spot.label}. {hero.id} found it there with the {culprit.label}, which changed the mystery from theft into a plea for care."
        ),
        (
            f"Why had the {culprit.label} moved {artifact.phrase}?",
            f"The {culprit.label} moved it because {culprit.concern}. It was trying to protect something small, not ruin the celebration."
        ),
        (
            "How did the people solve the problem?",
            f"They returned {artifact.phrase} and chose {adjustment.label}: they would {adjustment.plan_text}. That new plan answered the creature's worry and still let the festival go on."
        ),
        (
            "How did the story end?",
            f"The festival still happened, but in a kinder shape. {adjustment.effect_text} and {festival.closing}."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"myth", "festival", "clue", "gentle"}
    artifact = world.facts["artifact_cfg"]
    clue = world.facts["clue_cfg"]
    culprit = world.facts["culprit_cfg"]
    adjustment = world.facts["adjustment_cfg"]
    tags |= set(artifact.tags)
    tags |= set(clue.tags)
    tags |= set(culprit.tags)
    tags |= set(adjustment.tags)
    if "acrobatics" in artifact.tags or "acrobatics" in adjustment.tags:
        tags.add("acrobatics")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(C, A, Cl, S, Ad) :-
    culprit(C), artifact(A), clue(Cl), spot(S), adjustment(Ad),
    leaves(C, Cl), targets(C, A), hides_at(C, S), solves_with(C, Ad).

valid(F, A, C, Cl, S, Ad) :-
    festival(F), compatible(C, A, Cl, S, Ad).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for festival_id in FESTIVALS:
        lines.append(asp.fact("festival", festival_id))
    for artifact_id in ARTIFACTS:
        lines.append(asp.fact("artifact", artifact_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for adjustment_id in ADJUSTMENTS:
        lines.append(asp.fact("adjustment", adjustment_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("leaves", culprit_id, culprit.clue))
        for artifact_id in sorted(culprit.targets):
            lines.append(asp.fact("targets", culprit_id, artifact_id))
        for spot_id in sorted(culprit.spots):
            lines.append(asp.fact("hides_at", culprit_id, spot_id))
        for adjustment_id in sorted(culprit.adjustments):
            lines.append(asp.fact("solves_with", culprit_id, adjustment_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED[:2])
    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic mystery storyworld: a temple child solves a gentle mystery and modifies a festival with compassion."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--adjustment", choices=ADJUSTMENTS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    artifact = ARTIFACTS.get(args.artifact) if args.artifact else None
    culprit = CULPRITS.get(args.culprit) if args.culprit else None
    clue = CLUES.get(args.clue) if args.clue else None
    spot = SPOTS.get(args.spot) if args.spot else None
    adjustment = ADJUSTMENTS.get(args.adjustment) if args.adjustment else None

    if culprit and clue and clue.id != culprit.clue:
        raise StoryError(explain_rejection(artifact, culprit, clue, spot, adjustment))
    if culprit and artifact and artifact.id not in culprit.targets:
        raise StoryError(explain_rejection(artifact, culprit, clue, spot, adjustment))
    if culprit and spot and spot.id not in culprit.spots:
        raise StoryError(explain_rejection(artifact, culprit, clue, spot, adjustment))
    if culprit and adjustment and adjustment.id not in culprit.adjustments:
        raise StoryError(explain_rejection(artifact, culprit, clue, spot, adjustment))

    combos = [
        combo
        for combo in valid_combos()
        if (args.festival is None or combo[0] == args.festival)
        and (args.artifact is None or combo[1] == args.artifact)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.clue is None or combo[3] == args.clue)
        and (args.spot is None or combo[4] == args.spot)
        and (args.adjustment is None or combo[5] == args.adjustment)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    festival_id, artifact_id, culprit_id, clue_id, spot_id, adjustment_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    elder_type = args.elder or rng.choice(["woman", "man"])
    hero_trait = rng.choice(TRAITS)
    return StoryParams(
        festival=festival_id,
        artifact=artifact_id,
        culprit=culprit_id,
        clue=clue_id,
        spot=spot_id,
        adjustment=adjustment_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.festival not in FESTIVALS:
        raise StoryError(f"(Unknown festival: {params.festival})")
    if params.artifact not in ARTIFACTS:
        raise StoryError(f"(Unknown artifact: {params.artifact})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.adjustment not in ADJUSTMENTS:
        raise StoryError(f"(Unknown adjustment: {params.adjustment})")

    artifact = ARTIFACTS[params.artifact]
    culprit = CULPRITS[params.culprit]
    clue = CLUES[params.clue]
    spot = SPOTS[params.spot]
    adjustment = ADJUSTMENTS[params.adjustment]
    if not compatible(culprit, artifact, clue, spot, adjustment):
        raise StoryError(explain_rejection(artifact, culprit, clue, spot, adjustment))

    world = tell(
        festival=FESTIVALS[params.festival],
        artifact=artifact,
        culprit=culprit,
        clue=clue,
        spot=spot,
        adjustment=adjustment,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
        hero_trait=params.hero_trait,
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
        print(asp_program("#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (festival, artifact, culprit, clue, spot, adjustment) combos:\n")
        for combo in combos:
            print("  " + "  ".join(combo))
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
            header = (
                f"### {p.hero_name}: {p.artifact} / {p.culprit} / {p.adjustment} "
                f"at {p.festival}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
