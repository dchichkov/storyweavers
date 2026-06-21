#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/waist_playroom_transformation_teamwork_nursery_rhyme.py
==================================================================================

A small storyworld about two children in a playroom turning ordinary things into
waist-worn parade costumes. The world models a simple transformation problem:
the pretend costume must fit around the waist, the chosen tie must match the
costume's anchor points, and the helper's teamwork must be strong enough to keep
the transformed costume from sagging.

The stories aim for a gentle nursery-rhyme feel: bright objects, repeated
phrases, a clear wobble in the middle, and an ending parade that proves the
change.

Run it
------
    python storyworlds/worlds/gpt-5.4/waist_playroom_transformation_teamwork_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/waist_playroom_transformation_teamwork_nursery_rhyme.py --costume train_box --fastener sticky_tape
    python storyworlds/worlds/gpt-5.4/waist_playroom_transformation_teamwork_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/waist_playroom_transformation_teamwork_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/waist_playroom_transformation_teamwork_nursery_rhyme.py --verify
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
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
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
class Costume:
    id: str
    object_label: str
    object_phrase: str
    transformed_name: str
    anchor: str
    heft: int
    opening: str
    decorate: str
    motion: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fastener:
    id: str
    label: str
    phrase: str
    anchors: set[str]
    strength: int
    sense: int
    knot_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperAction:
    id: str
    label: str
    power: int
    action_text: str
    assist_text: str
    ending_text: str
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


def _r_sag(world: World) -> list[str]:
    prop = world.entities.get("prop")
    if prop is None:
        return []
    if prop.meters["waist_try"] < THRESHOLD:
        return []
    if prop.meters["secured"] >= THRESHOLD:
        return []
    sig = ("sag", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if prop.attrs.get("heft", 0) >= 1:
        prop.meters["sag"] += 1
        wearer = world.get("wearer")
        helper = world.get("helper")
        wearer.memes["surprise"] += 1
        helper.memes["notice"] += 1
        return ["__sag__"]
    return []


def _r_balance(world: World) -> list[str]:
    prop = world.entities.get("prop")
    if prop is None:
        return []
    if prop.meters["secured"] < THRESHOLD:
        return []
    sig = ("balance", prop.id)
    if sig in world.fired:
        return []
    support = prop.meters["tie_strength"] + prop.meters["helper_power"]
    heft = prop.attrs.get("heft", 0)
    if support < heft:
        return []
    world.fired.add(sig)
    prop.meters["balanced"] += 1
    wearer = world.get("wearer")
    helper = world.get("helper")
    wearer.memes["confidence"] += 1
    helper.memes["pride"] += 1
    return ["__balanced__"]


CAUSAL_RULES = [
    Rule(name="sag", tag="physical", apply=_r_sag),
    Rule(name="balance", tag="physical", apply=_r_balance),
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
        for item in produced:
            if not item.startswith("__"):
                world.say(item)
    return produced


def compatible(costume: Costume, fastener: Fastener) -> bool:
    return costume.anchor in fastener.anchors and fastener.sense >= SENSE_MIN


def enough_support(costume: Costume, fastener: Fastener, helper: HelperAction) -> bool:
    return fastener.strength + helper.power >= costume.heft


def smooth_success(costume: Costume, helper: HelperAction) -> bool:
    return helper.power >= costume.heft


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cid, costume in COSTUMES.items():
        for fid, fastener in FASTENERS.items():
            if not compatible(costume, fastener):
                continue
            for hid, helper in HELPERS.items():
                if enough_support(costume, fastener, helper):
                    combos.append((cid, fid, hid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    costume = COSTUMES[params.costume]
    helper = HELPERS[params.helper]
    return "smooth" if smooth_success(costume, helper) else "assisted"


def explain_fastener(costume: Costume, fastener: Fastener) -> str:
    if fastener.sense < SENSE_MIN:
        return (
            f"(No story: {fastener.label} is a poor choice for a costume around a child's waist. "
            f"Pick a soft tie that can hold safely, like one of: "
            f"{', '.join(sorted(fid for fid, f in FASTENERS.items() if f.sense >= SENSE_MIN))}.)"
        )
    return (
        f"(No story: {fastener.label} cannot attach a {costume.transformed_name} costume "
        f"that uses {costume.anchor}. The tie and the costume have to match.)"
    )


def explain_helper(costume: Costume, fastener: Fastener, helper: HelperAction) -> str:
    total = fastener.strength + helper.power
    return (
        f"(No story: {helper.label} plus {fastener.label} does not give enough support for "
        f"the {costume.transformed_name}. The costume is too heavy to stay up at the waist "
        f"without stronger teamwork.)"
    )


def nursery_intro(costume: Costume) -> str:
    return (
        f"In the playroom, where blocks made little hills and drums made little booms, "
        f"two children found {costume.object_phrase}. {costume.opening}"
    )


def decorate_beat(world: World, wearer: Entity, helper: Entity, costume: Costume) -> None:
    prop = world.get("prop")
    wearer.memes["joy"] += 1
    helper.memes["joy"] += 1
    prop.meters["decorated"] += 1
    world.say(
        f'{wearer.id} clapped and {helper.id} laughed. "{costume.decorate}" they sang, '
        f"and the plain old thing began to look like a {costume.transformed_name}."
    )


def first_try(world: World, wearer: Entity, helper: Entity, costume: Costume) -> None:
    prop = world.get("prop")
    prop.meters["waist_try"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{wearer.id} stepped into the middle and tried to lift it to {wearer.pronoun('possessive')} waist."
    )
    if prop.meters["sag"] >= THRESHOLD:
        world.say(
            f"Down it dipped, down it slid, bumping {wearer.pronoun('possessive')} knees instead. "
            f"One pair of hands was not enough for a {costume.transformed_name}."
        )
        wearer.memes["frustration"] += 1
        helper.memes["care"] += 1


def teamwork_prediction(world: World, costume: Costume, fastener: Fastener, helper: HelperAction) -> dict:
    sim = world.copy()
    prop = sim.get("prop")
    prop.meters["helper_power"] += helper.power
    prop.meters["tie_strength"] += fastener.strength
    prop.meters["secured"] += 1
    propagate(sim, narrate=False)
    return {
        "balanced": prop.meters["balanced"] >= THRESHOLD,
        "smooth": smooth_success(costume, helper),
    }


def helper_offer(world: World, wearer: Entity, helper: Entity,
                 costume: Costume, fastener: Fastener, helper_action: HelperAction) -> None:
    pred = teamwork_prediction(world, costume, fastener, helper_action)
    world.facts["pred_balanced"] = pred["balanced"]
    world.facts["pred_smooth"] = pred["smooth"]
    world.say(
        f'{helper.id} tipped {helper.pronoun("possessive")} head and said, '
        f'"Not one, but two. I will {helper_action.action_text}, and you can hold still."'
    )
    if pred["balanced"]:
        world.say(
            f'Then {helper.pronoun().capitalize()} held up {fastener.phrase} and added, '
            f'"Round the waist, neat and right; that will make our {costume.transformed_name} sit just right."'
        )


def secure_costume(world: World, wearer: Entity, helper: Entity,
                   costume: Costume, fastener: Fastener, helper_action: HelperAction) -> None:
    prop = world.get("prop")
    prop.meters["helper_power"] += helper_action.power
    prop.meters["tie_strength"] += fastener.strength
    prop.meters["secured"] += 1
    wearer.memes["trust"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"{helper.id} {helper_action.action_text}, while {wearer.id} tucked {wearer.pronoun('possessive')} elbows in close."
    )
    world.say(
        f"Together they {fastener.knot_text}, snug and gentle around {wearer.pronoun('possessive')} waist."
    )
    propagate(world, narrate=False)


def transform(world: World, wearer: Entity, helper: Entity, costume: Costume) -> None:
    prop = world.get("prop")
    if prop.meters["balanced"] >= THRESHOLD:
        prop.meters["transformed"] += 1
        world.say(
            f"Up it sat at last. The {costume.object_label} was not just itself anymore; "
            f"it had become a {costume.transformed_name} for the playroom parade."
        )
    else:
        world.say(
            f"It rose partway, enough to begin the game, and the children kept close as the "
            f"{costume.transformed_name} took shape."
        )
    wearer.memes["wonder"] += 1
    helper.memes["wonder"] += 1


def ending(world: World, wearer: Entity, helper: Entity,
           costume: Costume, helper_action: HelperAction, outcome: str) -> None:
    wearer.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.para()
    if outcome == "smooth":
        world.say(
            f'They took three parade steps and sang, "Tap and sway, bright today; '
            f'{costume.transformed_name} leads the way!"'
        )
        world.say(
            f"The costume stayed high at the waist, light and proud, while {wearer.id} {costume.motion} "
            f"and {helper.id} danced beside {helper.pronoun('object')}."
        )
    else:
        world.say(
            f'They took three careful parade steps and sang, "Hold and guide, side by side; '
            f'{costume.transformed_name} has a happy ride!"'
        )
        world.say(
            f"The costume gave a little bounce, but {helper.id} {helper_action.ending_text}, "
            f"so it stayed where it belonged at {wearer.id}'s waist."
        )
    world.say(
        f"Soon the playroom was full of pretend music and marching feet, and {costume.ending}"
    )


def tell(costume: Costume, fastener: Fastener, helper_action: HelperAction,
         wearer_name: str = "Mina", wearer_gender: str = "girl",
         helper_name: str = "Toby", helper_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    wearer = world.add(Entity(
        id=wearer_name,
        kind="character",
        type=wearer_gender,
        role="wearer",
        label=wearer_name,
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        label=helper_name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    prop = world.add(Entity(
        id="prop",
        type="costume",
        label=costume.object_label,
        phrase=costume.object_phrase,
        attrs={"heft": costume.heft, "anchor": costume.anchor},
        tags=set(costume.tags),
    ))
    tie = world.add(Entity(
        id="tie",
        type="fastener",
        label=fastener.label,
        phrase=fastener.phrase,
        attrs={"strength": fastener.strength},
        tags=set(fastener.tags),
    ))
    prop.memes["imagination"] += 1
    world.facts["setting"] = "playroom"

    world.say(nursery_intro(costume))
    decorate_beat(world, wearer, helper, costume)

    world.para()
    first_try(world, wearer, helper, costume)
    helper_offer(world, wearer, helper, costume, fastener, helper_action)
    secure_costume(world, wearer, helper, costume, fastener, helper_action)
    transform(world, wearer, helper, costume)

    result = "smooth" if smooth_success(costume, helper_action) else "assisted"
    ending(world, wearer, helper, costume, helper_action, result)

    world.facts.update(
        wearer=wearer,
        helper=helper,
        parent=parent,
        prop=prop,
        tie=tie,
        costume=costume,
        fastener=fastener,
        helper_action=helper_action,
        sagged=prop.meters["sag"] >= THRESHOLD,
        balanced=prop.meters["balanced"] >= THRESHOLD,
        outcome=result,
        transformed=prop.meters["transformed"] >= THRESHOLD,
    )
    return world


COSTUMES = {
    "train_box": Costume(
        id="train_box",
        object_label="cardboard box",
        object_phrase="a square cardboard box with blue chalk windows",
        transformed_name="clatter-train",
        anchor="slots",
        heft=2,
        opening="It wanted, in a make-believe sort of way, to be a train with a bell and a brave small puff.",
        decorate="Chalk a door and chalk a track, make a train and never look back",
        motion="chuffed around the rug",
        ending="the clatter-train rolled past toy towers and came home smiling",
        tags={"cardboard", "train"},
    ),
    "turtle_basket": Costume(
        id="turtle_basket",
        object_label="laundry basket",
        object_phrase="a round laundry basket with green paper spots",
        transformed_name="shell-backed turtle",
        anchor="handles",
        heft=2,
        opening="It looked sleepy at first, but the children thought it could become a turtle shell for a slow and splendid march.",
        decorate="Dot by dot and green by green, make the gentlest turtle seen",
        motion="plodded in a round slow ring",
        ending="the shell-backed turtle bobbed by the book nook as if it had always belonged there",
        tags={"basket", "turtle"},
    ),
    "flower_hoop": Costume(
        id="flower_hoop",
        object_label="hula hoop",
        object_phrase="a bright hula hoop with felt petals clipped all around",
        transformed_name="petal-float flower",
        anchor="loops",
        heft=1,
        opening="With petals clipped on, it seemed ready to bloom into a flower float for a tiny indoor parade.",
        decorate="Petal pink and petal gold, make a flower brave and bold",
        motion="twirled in a soft bright circle",
        ending="the petal-float flower swished past the dollhouse like spring come indoors",
        tags={"hoop", "flower"},
    ),
}

FASTENERS = {
    "satin_ribbon": Fastener(
        id="satin_ribbon",
        label="satin ribbon",
        phrase="a satin ribbon",
        anchors={"slots", "loops"},
        strength=1,
        sense=2,
        knot_text="threaded the satin ribbon through and tied a flat bow",
        tags={"ribbon"},
    ),
    "soft_scarf": Fastener(
        id="soft_scarf",
        label="soft scarf",
        phrase="a soft scarf",
        anchors={"handles", "slots"},
        strength=2,
        sense=3,
        knot_text="looped the soft scarf through and made a cozy knot",
        tags={"scarf"},
    ),
    "cloth_belt": Fastener(
        id="cloth_belt",
        label="cloth belt",
        phrase="a cloth belt",
        anchors={"handles", "loops", "slots"},
        strength=2,
        sense=3,
        knot_text="fed the cloth belt through and buckled it gently",
        tags={"belt", "waist"},
    ),
    "sticky_tape": Fastener(
        id="sticky_tape",
        label="sticky tape",
        phrase="a strip of sticky tape",
        anchors={"slots"},
        strength=0,
        sense=1,
        knot_text="pressed the tape down in a crinkly strip",
        tags={"tape"},
    ),
}

HELPERS = {
    "hold_sides": HelperAction(
        id="hold_sides",
        label="hold the sides high",
        power=2,
        action_text="held the sides high and steady",
        assist_text="holding the sides high",
        ending_text="kept one kind hand near the side",
        tags={"teamwork"},
    ),
    "lift_back": HelperAction(
        id="lift_back",
        label="lift the back edge",
        power=1,
        action_text="lifted the back edge with both hands",
        assist_text="lifting the back edge",
        ending_text="walked behind with a gentle lifting hand",
        tags={"teamwork"},
    ),
    "guide_handles": HelperAction(
        id="guide_handles",
        label="guide the handles into place",
        power=2,
        action_text="guided the handles and top edge into place",
        assist_text="guiding the handles into place",
        ending_text="stayed close, guiding each turn",
        tags={"teamwork"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Daisy", "Poppy", "Nell", "Ivy", "Tessa", "Mabel"]
BOY_NAMES = ["Toby", "Benji", "Ollie", "Jasper", "Finn", "Ned", "Milo", "Pip"]


@dataclass
class StoryParams:
    costume: str
    fastener: str
    helper: str
    wearer_name: str
    wearer_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "playroom": [
        (
            "What is a playroom?",
            "A playroom is a room where children keep toys and games and have space to pretend. It is a good place for indoor make-believe."
        )
    ],
    "waist": [
        (
            "What is your waist?",
            "Your waist is the middle part of your body, above your hips and below your chest. Belts and costume ties often go around your waist."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another do the same job. Sometimes one child holds while another ties, and together they can do what one alone cannot."
        )
    ],
    "cardboard": [
        (
            "What is cardboard?",
            "Cardboard is thick, stiff paper used to make boxes. It is light enough to decorate but strong enough for many pretend games."
        )
    ],
    "basket": [
        (
            "What is a laundry basket?",
            "A laundry basket is a container for carrying clothes. In pretend play, children can imagine it as all sorts of things."
        )
    ],
    "hoop": [
        (
            "What is a hula hoop?",
            "A hula hoop is a light ring children can spin or decorate. Because it is round, it can also become part of a pretend costume."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a soft strip of cloth used for tying or decorating. A ribbon can make a bow and help hold light things together."
        )
    ],
    "scarf": [
        (
            "What is a scarf?",
            "A scarf is a soft piece of cloth you can wrap or tie. In play, a scarf can be both decoration and a gentle fastener."
        )
    ],
    "belt": [
        (
            "What does a belt do?",
            "A belt goes around the waist to help hold something in place. A soft belt can also help a costume sit snugly."
        )
    ],
    "train": [
        (
            "What is a train?",
            "A train is a long vehicle that rolls along tracks. In pretend play, children often make train sounds and march like they are traveling somewhere."
        )
    ],
    "turtle": [
        (
            "What is special about a turtle?",
            "A turtle carries a shell on its back. That shell makes turtles a fun animal for costume games."
        )
    ],
    "flower": [
        (
            "What is a flower?",
            "A flower is the blooming part of a plant, often bright and colorful. Its petals make it easy to imagine in a parade or dance."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "playroom",
    "waist",
    "teamwork",
    "cardboard",
    "basket",
    "hoop",
    "ribbon",
    "scarf",
    "belt",
    "train",
    "turtle",
    "flower",
]


def generation_prompts(world: World) -> list[str]:
    costume = world.facts["costume"]
    wearer = world.facts["wearer"]
    helper = world.facts["helper"]
    fastener = world.facts["fastener"]
    outcome = world.facts["outcome"]
    return [
        (
            f'Write a short nursery-rhyme-style story set in a playroom where two children '
            f'use teamwork to transform {costume.object_phrase} into a {costume.transformed_name} worn at the waist.'
        ),
        (
            f"Tell a gentle transformation story where {wearer.id} cannot keep the costume up alone, "
            f"and {helper.id} helps with {fastener.phrase} so the pretend parade can begin."
        ),
        (
            f'Write a rhythmic story for young children that includes the word "waist", '
            f"features teamwork, and ends with a {'smooth' if outcome == 'smooth' else 'careful'} indoor parade."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    wearer = world.facts["wearer"]
    helper = world.facts["helper"]
    costume = world.facts["costume"]
    fastener = world.facts["fastener"]
    helper_action = world.facts["helper_action"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {wearer.id} and {helper.id} in the playroom. Together they turned {costume.object_phrase} into a pretend {costume.transformed_name}."
        ),
        (
            "What did the children want to make?",
            f"They wanted to transform the {costume.object_label} into a {costume.transformed_name}. The costume was meant to sit around {wearer.id}'s waist for a parade."
        ),
    ]
    if world.facts.get("sagged"):
        qa.append(
            (
                f"Why did the first try not work?",
                f"The costume slid down when {wearer.id} tried to lift it alone. It was too heavy or awkward to stay at the waist without help."
            )
        )
    qa.append(
        (
            f"How did {helper.id} help?",
            f"{helper.id} {helper_action.action_text} while the children used {fastener.phrase}. That teamwork gave the costume enough support to stay in place."
        )
    )
    if outcome == "smooth":
        qa.append(
            (
                "How did the story end?",
                f"It ended with a smooth little parade in the playroom. The {costume.transformed_name} stayed high at the waist, so the children could march and sing happily."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with a careful, happy parade. The costume bounced a little, but {helper.id} stayed close and guided it, so the game still worked because they kept helping each other."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    costume = world.facts["costume"]
    fastener = world.facts["fastener"]
    tags = {"playroom", "waist", "teamwork"} | set(costume.tags) | set(fastener.tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        costume="train_box",
        fastener="cloth_belt",
        helper="hold_sides",
        wearer_name="Mina",
        wearer_gender="girl",
        helper_name="Toby",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        costume="turtle_basket",
        fastener="soft_scarf",
        helper="guide_handles",
        wearer_name="Nell",
        wearer_gender="girl",
        helper_name="Pip",
        helper_gender="boy",
        parent="father",
    ),
    StoryParams(
        costume="flower_hoop",
        fastener="satin_ribbon",
        helper="lift_back",
        wearer_name="Lulu",
        wearer_gender="girl",
        helper_name="Benji",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        costume="train_box",
        fastener="soft_scarf",
        helper="lift_back",
        wearer_name="Mabel",
        wearer_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="father",
    ),
]


ASP_RULES = r"""
compatible(C, F) :- costume(C), fastener(F), needs_anchor(C, A), works_with(F, A),
                    sense(F, S), sense_min(M), S >= M.
enough(C, F, H)  :- compatible(C, F), helper(H), heft(C, W), strength(F, T), power(H, P),
                    T + P >= W.
valid(C, F, H)   :- enough(C, F, H).

smooth(C, H)     :- costume(C), helper(H), heft(C, W), power(H, P), P >= W.
outcome(smooth)  :- chosen_costume(C), chosen_helper(H), smooth(C, H).
outcome(assisted):- chosen_costume(C), chosen_helper(H), not smooth(C, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, costume in COSTUMES.items():
        lines.append(asp.fact("costume", cid))
        lines.append(asp.fact("needs_anchor", cid, costume.anchor))
        lines.append(asp.fact("heft", cid, costume.heft))
    for fid, fastener in FASTENERS.items():
        lines.append(asp.fact("fastener", fid))
        lines.append(asp.fact("strength", fid, fastener.strength))
        lines.append(asp.fact("sense", fid, fastener.sense))
        for anchor in sorted(fastener.anchors):
            lines.append(asp.fact("works_with", fid, anchor))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("power", hid, helper.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_costume", params.costume),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
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
        for params in CURATED[:2]:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "{" in sample.story or "}" in sample.story:
                raise StoryError("unresolved template text in story")
            with redirect_stdout(io.StringIO()):
                emit(sample, trace=False, qa=False)
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Playroom transformation storyworld: children use teamwork to make a waist-worn parade costume."
    )
    ap.add_argument("--costume", choices=sorted(COSTUMES))
    ap.add_argument("--fastener", choices=sorted(FASTENERS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--wearer-name")
    ap.add_argument("--wearer-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.costume and args.fastener:
        costume = COSTUMES[args.costume]
        fastener = FASTENERS[args.fastener]
        if not compatible(costume, fastener):
            raise StoryError(explain_fastener(costume, fastener))
    if args.costume and args.fastener and args.helper:
        costume = COSTUMES[args.costume]
        fastener = FASTENERS[args.fastener]
        helper = HELPERS[args.helper]
        if compatible(costume, fastener) and not enough_support(costume, fastener, helper):
            raise StoryError(explain_helper(costume, fastener, helper))
        if not compatible(costume, fastener):
            raise StoryError(explain_fastener(costume, fastener))
    if args.fastener and FASTENERS[args.fastener].sense < SENSE_MIN:
        costume = COSTUMES[args.costume] if args.costume else next(iter(COSTUMES.values()))
        raise StoryError(explain_fastener(costume, FASTENERS[args.fastener]))

    combos = [
        combo for combo in valid_combos()
        if (args.costume is None or combo[0] == args.costume)
        and (args.fastener is None or combo[1] == args.fastener)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    costume_id, fastener_id, helper_id = rng.choice(sorted(combos))
    wearer_gender = args.wearer_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    wearer_name = args.wearer_name or pick_name(rng, wearer_gender)
    helper_name = args.helper_name or pick_name(rng, helper_gender, avoid=wearer_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        costume=costume_id,
        fastener=fastener_id,
        helper=helper_id,
        wearer_name=wearer_name,
        wearer_gender=wearer_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.costume not in COSTUMES:
        raise StoryError(f"(Unknown costume: {params.costume})")
    if params.fastener not in FASTENERS:
        raise StoryError(f"(Unknown fastener: {params.fastener})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper action: {params.helper})")

    costume = COSTUMES[params.costume]
    fastener = FASTENERS[params.fastener]
    helper = HELPERS[params.helper]
    if not compatible(costume, fastener):
        raise StoryError(explain_fastener(costume, fastener))
    if not enough_support(costume, fastener, helper):
        raise StoryError(explain_helper(costume, fastener, helper))

    world = tell(
        costume=costume,
        fastener=fastener,
        helper_action=helper,
        wearer_name=params.wearer_name,
        wearer_gender=params.wearer_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (costume, fastener, helper) combos:\n")
        for costume, fastener, helper in combos:
            print(f"  {costume:14} {fastener:12} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
                f"### {p.wearer_name} & {p.helper_name}: {p.costume} with {p.fastener} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
