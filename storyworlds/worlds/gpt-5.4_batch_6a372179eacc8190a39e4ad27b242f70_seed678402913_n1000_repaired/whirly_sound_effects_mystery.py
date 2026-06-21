#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whirly_sound_effects_mystery.py
=========================================================

A standalone storyworld for a small child-facing mystery: a child hears a
strange whirly sound, worries about what it might be, and then investigates
with a calm grown-up until the harmless cause is found and fixed.

This world focuses on:
- concrete sound effects in the prose ("whirr-whirr", "tap-tap", "clink")
- a clear mystery shape: strange clue -> worried guesses -> careful search
  -> reveal -> sensible fix -> ending image that proves the fear changed
- a small reasonableness gate: only location/source/tool combinations that
  physically fit are allowed
- a Python model plus an inline ASP twin for parity checks

Run it
------
    python storyworlds/worlds/gpt-5.4/whirly_sound_effects_mystery.py
    python storyworlds/worlds/gpt-5.4/whirly_sound_effects_mystery.py --place attic --source pinwheel_vent
    python storyworlds/worlds/gpt-5.4/whirly_sound_effects_mystery.py --source branch_window --kit flashlight_gloves
    python storyworlds/worlds/gpt-5.4/whirly_sound_effects_mystery.py --kit broom_only   # rejected
    python storyworlds/worlds/gpt-5.4/whirly_sound_effects_mystery.py --all
    python storyworlds/worlds/gpt-5.4/whirly_sound_effects_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/whirly_sound_effects_mystery.py --verify
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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    hiding_spot: str
    path: str
    mood: str
    sounds_like: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    sound: str
    loud: str
    cause_line: str
    reveal_line: str
    ending_image: str
    needs_reveal: str
    needs_fix: str
    allowed_places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Kit:
    id: str
    label: str
    phrase: str
    reveal_tags: set[str] = field(default_factory=set)
    fix_tags: set[str] = field(default_factory=set)
    success_line: str = ""
    fail_line: str = ""
    qa_line: str = ""
    tags: set[str] = field(default_factory=set)


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


def _r_noise_to_feelings(world: World) -> list[str]:
    source = world.entities.get("source")
    child = world.entities.get("child")
    room = world.entities.get("room")
    if source is None or child is None or room is None:
        return []
    if source.meters["active"] < THRESHOLD:
        return []
    sig = ("noise_to_feelings",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["noise"] += 1
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    return ["__noise__"]


def _r_reveal_to_relief(world: World) -> list[str]:
    source = world.entities.get("source")
    child = world.entities.get("child")
    if source is None or child is None:
        return []
    if source.meters["revealed"] < THRESHOLD:
        return []
    sig = ("reveal_to_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["understanding"] += 1
    return []


def _r_fixed_to_calm(world: World) -> list[str]:
    source = world.entities.get("source")
    room = world.entities.get("room")
    child = world.entities.get("child")
    if source is None or room is None or child is None:
        return []
    if source.meters["fixed"] < THRESHOLD:
        return []
    sig = ("fixed_to_calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["active"] = 0.0
    room.meters["noise"] = 0.0
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="noise_to_feelings", tag="meme", apply=_r_noise_to_feelings),
    Rule(name="reveal_to_relief", tag="meme", apply=_r_reveal_to_relief),
    Rule(name="fixed_to_calm", tag="physical", apply=_r_fixed_to_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


PLACES = {
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the attic hallway",
        hiding_spot="the little vent above the attic stairs",
        path="up the narrow stairs",
        mood="dim and dusty",
        sounds_like="a place where every board remembered old footsteps",
        affords={"pinwheel_vent", "loose_shutter"},
        tags={"attic", "indoors"},
    ),
    "bedroom": Place(
        id="bedroom",
        label="bedroom",
        phrase="the bedroom",
        hiding_spot="the curtain rod by the window",
        path="across the room to the window",
        mood="soft and shadowy",
        sounds_like="a place where moonlight made corners look mysterious",
        affords={"branch_window", "loose_shutter"},
        tags={"bedroom", "indoors"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the back porch",
        hiding_spot="the hanging basket by the steps",
        path="out to the porch boards",
        mood="cool and breezy",
        sounds_like="a place where the evening wind liked to whisper",
        affords={"branch_window", "spinning_tag"},
        tags={"porch", "outdoors"},
    ),
}

SOURCES = {
    "pinwheel_vent": Source(
        id="pinwheel_vent",
        label="pinwheel",
        phrase="a tiny paper pinwheel",
        sound="whirr-whirr",
        loud="a thin whirly sound",
        cause_line="A draft from the vent had caught a tiny paper pinwheel and kept it spinning.",
        reveal_line="There, caught in the vent slats, was a tiny paper pinwheel twirling as if it wanted to be a secret machine.",
        ending_image="The pinwheel rested still in the helper's hand, and the attic felt ordinary again.",
        needs_reveal="high_light",
        needs_fix="lift_remove",
        allowed_places={"attic"},
        tags={"pinwheel", "wind", "vent"},
    ),
    "branch_window": Source(
        id="branch_window",
        label="branch",
        phrase="a thin tree branch",
        sound="scritch-whirr",
        loud="a scratchy whirly sound",
        cause_line="The wind kept sweeping a thin branch across the glass and back again.",
        reveal_line="A thin branch outside the window was skating across the pane and springing back with every puff of wind.",
        ending_image="After the branch was tied back, the window shone quietly and the room sounded sleepy again.",
        needs_reveal="window_light",
        needs_fix="tie_back",
        allowed_places={"bedroom", "porch"},
        tags={"branch", "window", "wind"},
    ),
    "spinning_tag": Source(
        id="spinning_tag",
        label="tag",
        phrase="the cardboard tag on a hanging planter",
        sound="whirly-flip",
        loud="a busy little whirly sound",
        cause_line="The wind was making the loose tag spin and slap the pot.",
        reveal_line="The tag on the hanging planter was spinning around and tapping the pot every time the wind curled through.",
        ending_image="Once the tag was tucked in, the planter only swayed softly, and the porch sounded peaceful.",
        needs_reveal="close_look",
        needs_fix="tuck_tag",
        allowed_places={"porch"},
        tags={"tag", "planter", "wind"},
    ),
    "loose_shutter": Source(
        id="loose_shutter",
        label="shutter hook",
        phrase="a loose shutter hook",
        sound="clink-whirr",
        loud="a whirly clinky sound",
        cause_line="The hook was wobbling in the breeze and knocking lightly against the wall.",
        reveal_line="A loose shutter hook trembled in the breeze and tapped the siding with a tiny metal shake.",
        ending_image="When the hook was fastened tight, the house stood still and quiet, as if the mystery had bowed and gone home.",
        needs_reveal="window_light",
        needs_fix="tighten_hook",
        allowed_places={"attic", "bedroom"},
        tags={"shutter", "hook", "wind"},
    ),
}

KITS = {
    "flashlight_stool": Kit(
        id="flashlight_stool",
        label="flashlight and step stool",
        phrase="a flashlight and a step stool",
        reveal_tags={"high_light", "window_light"},
        fix_tags={"lift_remove", "tuck_tag"},
        success_line="The helper shone the flashlight into the hiding spot and, standing safely on the step stool, reached the little troublemaker.",
        fail_line="They could see the sound, but they still could not fix it from the floor.",
        qa_line="used a flashlight to spot the problem and a step stool to reach it safely",
        tags={"flashlight", "stool"},
    ),
    "flashlight_gloves": Kit(
        id="flashlight_gloves",
        label="flashlight and garden gloves",
        phrase="a flashlight and garden gloves",
        reveal_tags={"window_light", "close_look"},
        fix_tags={"tie_back", "tuck_tag"},
        success_line="The helper shone the flashlight to follow the sound, then used gloved hands to hold and secure the moving piece.",
        fail_line="They found the problem, but without the right reach they could not get it settled.",
        qa_line="used a flashlight to follow the sound and gloves to hold the moving piece safely",
        tags={"flashlight", "gloves"},
    ),
    "toolbox": Kit(
        id="toolbox",
        label="small toolbox",
        phrase="a small toolbox with a flashlight",
        reveal_tags={"window_light", "high_light"},
        fix_tags={"tighten_hook", "lift_remove"},
        success_line="The helper opened the small toolbox, followed the sound with the flashlight, and tightened or lifted what was loose.",
        fail_line="The problem needed softer hands, not just tools.",
        qa_line="used the flashlight in the toolbox to find the source and then fixed the loose part",
        tags={"toolbox", "flashlight"},
    ),
    "broom_only": Kit(
        id="broom_only",
        label="broom",
        phrase="a broom",
        reveal_tags={"close_look"},
        fix_tags=set(),
        success_line="",
        fail_line="A broom could wave at the noise, but it could not honestly solve the mystery.",
        qa_line="",
        tags={"broom"},
    ),
}


def source_fits(place: Place, source: Source) -> bool:
    return source.id in place.affords and place.id in source.allowed_places


def kit_fits(source: Source, kit: Kit) -> bool:
    return source.needs_reveal in kit.reveal_tags and source.needs_fix in kit.fix_tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if not source_fits(place, source):
                continue
            for kit_id, kit in KITS.items():
                if kit_fits(source, kit):
                    combos.append((place_id, source_id, kit_id))
    return combos


def explain_place_source(place: Place, source: Source) -> str:
    return (
        f"(No story: {source.label} does not make sense in {place.phrase}. "
        f"This world only allows clues that physically fit the place.)"
    )


def explain_kit(source: Source, kit: Kit) -> str:
    return (
        f"(No story: {kit.label} is not a reasonable way to solve the {source.label} mystery. "
        f"The investigation kit must both reveal the sound and fix it safely.)"
    )


def predict_sound(world: World) -> dict:
    sim = world.copy()
    source = sim.get("source")
    source.meters["active"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    room = sim.get("room")
    return {
        "noise": room.meters["noise"],
        "curiosity": child.memes["curiosity"],
        "worry": child.memes["worry"],
    }


def begin_evening(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["cozy"] += 1
    world.say(
        f"One breezy evening, {child.id} was with {helper.label_word} near {place.phrase}. "
        f"The place felt {place.mood}, {place.sounds_like}."
    )


def hear_sound(world: World, child: Entity, source: Source, place: Place) -> None:
    world.get("source").meters["active"] += 1
    propagate(world, narrate=False)
    child.memes["fear"] += 1
    world.say(
        f"Then {child.pronoun('possessive')} ears caught {source.loud}: "
        f'"{source.sound}! {source.sound}!" It seemed to come from {place.hiding_spot}.'
    )


def guess_mystery(world: World, child: Entity) -> None:
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f'{child.id} went still. "Is it a tiny ghost? Is it a secret machine?" '
            f'{child.pronoun()} whispered.'
        )


def helper_stays_calm(world: World, helper: Entity, child: Entity) -> None:
    helper.memes["calm"] += 1
    child.memes["trust"] += 1
    world.say(
        f'{helper.label_word.capitalize()} smiled and squeezed {child.pronoun("possessive")} hand. '
        f'"Let\'s listen first," {helper.pronoun()} said. "Mysteries sound bigger before we understand them."'
    )


def fetch_kit(world: World, helper: Entity, kit: Kit, place: Place) -> None:
    world.say(
        f"Together they went {place.path} and brought {kit.phrase}. "
        f"The mystery still went {world.facts['source_cfg'].sound}, but now they had a plan."
    )


def investigate(world: World, helper: Entity, child: Entity, source: Source, kit: Kit) -> None:
    child.memes["brave"] += 1
    world.say(
        f"{helper.label_word.capitalize()} tilted {helper.pronoun('possessive')} head. "
        f'"Whirr... wait... there!" {helper.pronoun()} said, following the sound.'
    )
    world.say(kit.success_line)
    world.get("source").meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(source.reveal_line)
    world.say(source.cause_line)


def fix_problem(world: World, helper: Entity, source: Source) -> None:
    world.get("source").meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Carefully, {helper.label_word} fixed it. At once the sound stopped. "
        f'No more "{source.sound}!" Only the ordinary hush of the evening remained.'
    )


def ending(world: World, child: Entity, helper: Entity, source: Source) -> None:
    child.memes["wonder"] += 1
    world.say(
        f'{child.id} let out a long breath. "So that was the mystery," {child.pronoun()} said.'
    )
    world.say(
        f'{helper.label_word.capitalize()} nodded. "Not every strange sound is scary. '
        f'Sometimes the house is only telling us what the wind is doing."'
    )
    world.say(source.ending_image)
    world.say(
        f"Soon {child.id} could hear the quiet again, and this time it sounded friendly."
    )


def tell(place: Place, source_cfg: Source, kit_cfg: Kit,
         child_name: str = "Nora", child_type: str = "girl",
         helper_type: str = "grandmother", trait: str = "curious") -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=[trait],
        label=child_name,
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="place",
        label=place.label,
        phrase=place.phrase,
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source_cfg.label,
        phrase=source_cfg.phrase,
        tags=set(source_cfg.tags),
    ))
    child.memes["curiosity"] = 1.0 if trait in {"curious", "careful"} else 0.0
    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        source_cfg=source_cfg,
        kit_cfg=kit_cfg,
    )

    begin_evening(world, child, helper, place)
    hear_sound(world, child, source_cfg, place)
    guess_mystery(world, child)

    world.para()
    helper_stays_calm(world, helper, child)
    pred = predict_sound(world)
    world.facts["predicted_noise"] = pred["noise"]
    fetch_kit(world, helper, kit_cfg, place)
    investigate(world, helper, child, source_cfg, kit_cfg)

    world.para()
    fix_problem(world, helper, source_cfg)
    ending(world, child, helper, source_cfg)

    world.facts.update(
        resolved=source.meters["fixed"] >= THRESHOLD,
        revealed=source.meters["revealed"] >= THRESHOLD,
        sound_stopped=source.meters["active"] < THRESHOLD,
        child_calm=child.memes["calm"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "wind": [
        (
            "Why can wind make funny sounds around a house?",
            "Wind can move loose things like tags, branches, or hooks. When they rub or tap, they can make surprising noises."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for?",
            "A flashlight helps you see into dark or tucked-away places. It is useful for looking carefully when you hear a strange sound."
        )
    ],
    "stool": [
        (
            "Why should a grown-up use a step stool carefully?",
            "A step stool helps someone reach a high place, but it should be used slowly and safely. A grown-up can use it while keeping a child back from the risky spot."
        )
    ],
    "gloves": [
        (
            "Why do people wear garden gloves?",
            "Garden gloves protect hands from rough or scratchy things. They can help when you need to hold a moving branch or a dusty object."
        )
    ],
    "toolbox": [
        (
            "What can a toolbox help with?",
            "A toolbox holds simple tools for tightening or fixing loose things. It helps a grown-up solve little house problems safely."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet. You solve it by noticing clues and asking calm questions."
        )
    ],
    "pinwheel": [
        (
            "What is a pinwheel?",
            "A pinwheel is a toy with light blades that spin when air moves past them. Even a small breeze can make it whirl."
        )
    ],
    "branch": [
        (
            "Why can a branch tap on a window?",
            "If the wind pushes a branch against the glass, it can scrape or tap again and again. That can sound strange from inside."
        )
    ],
    "tag": [
        (
            "Why does a loose tag make noise?",
            "A loose tag can flip and spin in the wind. If it hits something hard, it can make a tapping sound."
        )
    ],
    "shutter": [
        (
            "What happens when a hook or shutter is loose?",
            "A loose part can wobble when the wind moves it. That wobbling can make little clinks or rattles."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "mystery", "wind", "flashlight", "stool", "gloves", "toolbox",
    "pinwheel", "branch", "tag", "shutter",
]


@dataclass
class StoryParams:
    place: str
    source: str
    kit: str
    child_name: str
    child_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ella", "Ava", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Sam", "Theo", "Eli", "Noah"]
TRAITS = ["curious", "careful", "thoughtful", "brave"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]

CURATED = [
    StoryParams(
        place="attic",
        source="pinwheel_vent",
        kit="flashlight_stool",
        child_name="Nora",
        child_type="girl",
        helper_type="grandmother",
        trait="curious",
    ),
    StoryParams(
        place="bedroom",
        source="branch_window",
        kit="flashlight_gloves",
        child_name="Ben",
        child_type="boy",
        helper_type="father",
        trait="careful",
    ),
    StoryParams(
        place="porch",
        source="spinning_tag",
        kit="flashlight_gloves",
        child_name="Mia",
        child_type="girl",
        helper_type="mother",
        trait="thoughtful",
    ),
    StoryParams(
        place="bedroom",
        source="loose_shutter",
        kit="toolbox",
        child_name="Theo",
        child_type="boy",
        helper_type="grandfather",
        trait="brave",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    source = f["source_cfg"]
    return [
        (
            f'Write a gentle mystery story for a 3-to-5-year-old that includes the word '
            f'"whirly" and uses sound effects. A child hears a strange noise near {place.phrase} and discovers a harmless cause.'
        ),
        (
            f"Tell a child-friendly mystery where {child.id} hears {source.sound} near {place.hiding_spot}, "
            f"feels worried, and solves the puzzle with a calm grown-up."
        ),
        (
            f"Write a simple story with sound effects and a cozy mystery mood, ending when the strange whirly sound "
            f"turns out to be something ordinary."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    source = f["source_cfg"]
    kit = f["kit_cfg"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who heard a strange sound, and {helper_word}, who helped solve the mystery."
        ),
        (
            "What made the story feel mysterious at the beginning?",
            f"The mystery began when {child.id} heard {source.loud} coming from {place.hiding_spot}. "
            f"Because the sound was hidden, it seemed bigger and stranger than it really was."
        ),
        (
            f"What did {child.id} think the sound might be?",
            f"{child.id} wondered if it was a tiny ghost or a secret machine. "
            f"That guess came from hearing the noise before seeing what made it."
        ),
        (
            f"How did {helper_word} help?",
            f"{helper_word.capitalize()} stayed calm, listened first, and brought {kit.phrase}. "
            f"That careful plan helped them follow the clue instead of being frightened by it."
        ),
        (
            "What was really making the sound?",
            f"It was {source.phrase}. {source.cause_line}"
        ),
        (
            "How did they solve the mystery?",
            f"They {kit.qa_line}. After that, the whirly sound stopped, which showed they had found the true cause."
        ),
        (
            f"How did {child.id} feel at the end?",
            f"{child.id} felt relieved and calm. Once the sound was understood, the place felt friendly instead of spooky."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"mystery", "wind"}
    source = f["source_cfg"]
    kit = f["kit_cfg"]
    if "pinwheel" in source.tags:
        tags.add("pinwheel")
    if "branch" in source.tags:
        tags.add("branch")
    if "tag" in source.tags:
        tags.add("tag")
    if "shutter" in source.tags:
        tags.add("shutter")
    for tag in kit.tags:
        if tag == "flashlight":
            tags.add("flashlight")
        if tag == "stool":
            tags.add("stool")
        if tag == "gloves":
            tags.add("gloves")
        if tag == "toolbox":
            tags.add("toolbox")
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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A source fits a place when the place affords it and the source allows the place.
source_fits(P, S) :- affords(P, S), allowed_place(S, P).

% A kit fits a source when it can both reveal and fix it.
kit_fits(S, K) :- needs_reveal(S, R), reveal_tag(K, R),
                  needs_fix(S, F), fix_tag(K, F).

valid(P, S, K) :- place(P), source(S), kit(K), source_fits(P, S), kit_fits(S, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for sid in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, sid))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("needs_reveal", source_id, source.needs_reveal))
        lines.append(asp.fact("needs_fix", source_id, source.needs_fix))
        for pid in sorted(source.allowed_places):
            lines.append(asp.fact("allowed_place", source_id, pid))
    for kit_id, kit in KITS.items():
        lines.append(asp.fact("kit", kit_id))
        for tag in sorted(kit.reveal_tags):
            lines.append(asp.fact("reveal_tag", kit_id, tag))
        for tag in sorted(kit.fix_tags):
            lines.append(asp.fact("fix_tag", kit_id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Random generation produced empty story during verify.")
        print("OK: random generation smoke test succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child hears a whirly sound and solves a gentle mystery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        if not source_fits(place, source):
            raise StoryError(explain_place_source(place, source))
    if args.source and args.kit:
        source = SOURCES[args.source]
        kit = KITS[args.kit]
        if not kit_fits(source, kit):
            raise StoryError(explain_kit(source, kit))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.kit is None or combo[2] == args.kit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, kit_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    helper_type = args.helper_type or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        source=source_id,
        kit=kit_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        source = SOURCES[params.source]
        kit = KITS[params.kit]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not source_fits(place, source):
        raise StoryError(explain_place_source(place, source))
    if not kit_fits(source, kit):
        raise StoryError(explain_kit(source, kit))

    world = tell(
        place=place,
        source_cfg=source,
        kit_cfg=kit,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
        trait=params.trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, kit) combos:\n")
        for place, source, kit in combos:
            print(f"  {place:8} {source:14} {kit}")
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
            header = f"### {p.child_name}: {p.source} at {p.place} with {p.kit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
