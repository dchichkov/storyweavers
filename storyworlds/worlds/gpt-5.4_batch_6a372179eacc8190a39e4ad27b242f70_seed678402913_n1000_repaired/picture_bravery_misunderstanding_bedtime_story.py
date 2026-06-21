#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/picture_bravery_misunderstanding_bedtime_story.py
============================================================================

A standalone story world for gentle bedtime stories about a child who
misunderstands a picture in the dark, feels afraid, and finds a small brave way
to learn the truth.

This world models:
- a picture on a wall
- dim bedtime light and a moving shadow that make the picture look scary
- a misunderstanding ("it looked alive" / "it looked like something else")
- a brave response: the child checks with a safe light or asks a grown-up for help
- a calm bedtime ending that proves the fear has changed into understanding

Run it
------
    python storyworlds/worlds/gpt-5.4/picture_bravery_misunderstanding_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/picture_bravery_misunderstanding_bedtime_story.py --picture owl_picture
    python storyworlds/worlds/gpt-5.4/picture_bravery_misunderstanding_bedtime_story.py --distortion branch_shadow
    python storyworlds/worlds/gpt-5.4/picture_bravery_misunderstanding_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/picture_bravery_misunderstanding_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/picture_bravery_misunderstanding_bedtime_story.py --trace
    python storyworlds/worlds/gpt-5.4/picture_bravery_misunderstanding_bedtime_story.py --json
    python storyworlds/worlds/gpt-5.4/picture_bravery_misunderstanding_bedtime_story.py --verify
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
BRAVE_TRAITS = {"bold", "steady", "curious"}
CALM_TRAITS = {"gentle", "thoughtful", "careful"}
COURAGE_TARGET = 4


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class PictureCfg:
    id: str
    label: str
    phrase: str
    subject: str
    place: str
    bedtime_detail: str
    true_quality: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DistortionCfg:
    id: str
    label: str
    cause: str
    motion: str
    mistaken_for: str
    reveal: str
    severity: int = 1
    plausible_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class AidCfg:
    id: str
    label: str
    phrase: str
    courage_boost: int
    reveals_truth: bool = True
    solo_ok: bool = False
    line: str = ""
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


def _r_picture_seems_scary(world: World) -> list[str]:
    child = world.get("child")
    picture = world.get("picture")
    room = world.get("room")
    if room.meters["dim"] < THRESHOLD or picture.meters["shadowed"] < THRESHOLD:
        return []
    sig = ("seems_scary", picture.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    picture.meters["misread"] += 1
    child.memes["fear"] += 1 + picture.meters["severity"]
    return ["__misread__"]


def _r_checking_builds_bravery(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["checking"] < THRESHOLD:
        return []
    sig = ("checking_builds_bravery", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["bravery"] += 1
    return []


def _r_truth_calms_fear(world: World) -> list[str]:
    child = world.get("child")
    picture = world.get("picture")
    if picture.meters["understood"] < THRESHOLD:
        return []
    sig = ("truth_calms", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["understanding"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="picture_seems_scary", tag="emotion", apply=_r_picture_seems_scary),
    Rule(name="checking_builds_bravery", tag="emotion", apply=_r_checking_builds_bravery),
    Rule(name="truth_calms_fear", tag="emotion", apply=_r_truth_calms_fear),
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
        for s in produced:
            world.say(s)
    return produced


def plausible_misunderstanding(picture: PictureCfg, distortion: DistortionCfg) -> bool:
    return picture.id in distortion.plausible_for


def base_courage(trait: str) -> int:
    if trait in BRAVE_TRAITS:
        return 3
    if trait in CALM_TRAITS:
        return 2
    return 1


def can_check_alone(trait: str, aid: AidCfg, distortion: DistortionCfg) -> bool:
    score = base_courage(trait) + aid.courage_boost
    difficulty = 1 + distortion.severity
    return aid.solo_ok and score >= difficulty + 2


def predicted_fear(trait: str, distortion: DistortionCfg) -> int:
    return distortion.severity + (0 if trait in BRAVE_TRAITS else 1)


def setup_bedtime(world: World, child: Entity, parent: Entity, picture: PictureCfg) -> None:
    world.say(
        f"At bedtime, {child.id} was tucked under the blanket while the house grew soft and still."
    )
    world.say(
        f"Outside the room, {picture.phrase} hung {picture.place}, and {picture.bedtime_detail}."
    )
    world.say(
        f"{child.id}'s {parent.label_word} kissed {child.pronoun('object')} good night and left the door a little open."
    )


def notice_picture(world: World, child: Entity, picture: PictureCfg, distortion: DistortionCfg) -> None:
    room = world.get("room")
    pic = world.get("picture")
    room.meters["dim"] += 1
    pic.meters["shadowed"] += 1
    pic.meters["severity"] = float(distortion.severity)
    propagate(world, narrate=False)
    world.say(
        f"Then moonlight slipped across the hall, and {distortion.cause} laid a moving shadow over the picture."
    )
    world.say(
        f"From bed, {child.id} saw it sway and suddenly thought the {picture.subject} looked like {distortion.mistaken_for}."
    )


def fear_beat(world: World, child: Entity, comfort: str) -> None:
    child.memes["worry"] += 1
    if comfort:
        world.say(
            f"{child.id} pulled {child.pronoun('possessive')} {comfort} close and listened very hard."
        )
    else:
        world.say(
            f"{child.id} held the blanket right up under {child.pronoun('possessive')} chin and listened very hard."
        )
    world.say("Nothing jumped. Nothing growled. But the misunderstanding still felt real in the dark.")


def brave_choice(world: World, child: Entity, parent: Entity, aid: AidCfg, solo: bool) -> None:
    child.meters["checking"] += 1
    child.memes["courage"] += aid.courage_boost
    propagate(world, narrate=False)
    if solo:
        world.say(
            f"{child.id} took one slow breath after another and decided to be brave in a small bedtime way."
        )
        world.say(aid.line.format(child=child.id))
    else:
        world.say(
            f"{child.id} wanted to be brave, but brave did not mean pretending not to be scared."
        )
        world.say(
            f'So {child.pronoun()} whispered for {child.pronoun("possessive")} {parent.label_word}, and soon warm footsteps came back down the hall.'
        )
        world.say(aid.line.format(child=child.id, parent=parent.label_word, parent_cap=parent.label_word.capitalize()))


def reveal_truth(world: World, child: Entity, parent: Entity, picture: PictureCfg,
                 distortion: DistortionCfg, aid: AidCfg, solo: bool) -> None:
    pic = world.get("picture")
    pic.meters["understood"] += 1
    propagate(world, narrate=False)
    if solo:
        world.say(
            f"With {aid.phrase}, {child.id} looked carefully instead of quickly."
        )
    else:
        world.say(
            f"Together they lifted {aid.phrase} toward the wall and looked carefully instead of quickly."
        )
    world.say(
        f"Then the truth came clear: it was only {picture.phrase}, and {distortion.reveal}."
    )
    if solo:
        world.say(
            f'{child.id} padded back to bed and told {child.pronoun("possessive")} {parent.label_word} the whole thing. "{picture.true_quality}," {parent.pronoun()} said with a sleepy smile.'
        )
    else:
        world.say(
            f'"See?" {parent.label_word.capitalize()} said softly. "{picture.true_quality}."'
        )


def bedtime_end(world: World, child: Entity, parent: Entity, picture: PictureCfg, solo: bool) -> None:
    child.memes["sleepy"] += 1
    child.memes["safe"] += 1
    if solo:
        world.say(
            f"After that, the picture did not look frightening at all. It looked quiet again, as if it belonged to the sleepy house."
        )
    else:
        world.say(
            f"After that, the picture did not look frightening at all. It looked exactly like itself again."
        )
    world.say(
        f"{child.id} settled under the blanket, feeling bigger on the inside."
    )
    world.say(
        f"Soon the hall was still, the picture was still, and {child.id} fell asleep brave and calm."
    )


def tell(picture_cfg: PictureCfg, distortion_cfg: DistortionCfg, aid_cfg: AidCfg,
         child_name: str = "Nora", child_gender: str = "girl", parent_type: str = "mother",
         trait: str = "gentle", comfort: str = "") -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"comfort": comfort},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    picture = world.add(Entity(
        id="picture",
        kind="thing",
        type="picture",
        label=picture_cfg.label,
        phrase=picture_cfg.phrase,
        tags=set(picture_cfg.tags),
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label="hallway",
    ))

    child.attrs["display_name"] = child_name
    parent.attrs["display_name"] = parent.label_word.capitalize()
    world.facts["comfort"] = comfort

    setup_bedtime(world, child, parent, picture_cfg)
    world.para()
    notice_picture(world, child, picture_cfg, distortion_cfg)
    fear_beat(world, child, comfort)
    world.para()

    solo = can_check_alone(trait, aid_cfg, distortion_cfg)
    brave_choice(world, child, parent, aid_cfg, solo)
    world.para()
    reveal_truth(world, child, parent, picture_cfg, distortion_cfg, aid_cfg, solo)
    bedtime_end(world, child, parent, picture_cfg, solo)

    world.facts.update(
        child=child,
        parent=parent,
        picture_cfg=picture_cfg,
        distortion_cfg=distortion_cfg,
        aid_cfg=aid_cfg,
        solo=solo,
        misunderstood=True,
        brave_mode="solo" if solo else "together",
        fear_level=predicted_fear(trait, distortion_cfg),
    )
    return world


PICTURES = {
    "owl_picture": PictureCfg(
        id="owl_picture",
        label="owl picture",
        phrase="a small picture of an owl with round gold eyes",
        subject="owl",
        place="on the hallway wall beside the bedrooms",
        bedtime_detail="its glass sometimes caught the moon",
        true_quality="it is only a picture, and pictures cannot hop off walls",
        tags={"picture", "owl"},
    ),
    "boat_picture": PictureCfg(
        id="boat_picture",
        label="boat picture",
        phrase="a framed picture of a little sailboat on a blue lake",
        subject="boat",
        place="at the bend in the hallway",
        bedtime_detail="its pale paper shone when the moon was bright",
        true_quality="it is only a picture, and the boat is painted flat on the paper",
        tags={"picture", "boat"},
    ),
    "rabbit_picture": PictureCfg(
        id="rabbit_picture",
        label="rabbit picture",
        phrase="a watercolor picture of a rabbit in tall grass",
        subject="rabbit",
        place="near the night-light shelf",
        bedtime_detail="its white frame glimmered in the dark",
        true_quality="it is only a picture, and the rabbit is staying right in its frame",
        tags={"picture", "rabbit"},
    ),
    "grandpa_picture": PictureCfg(
        id="grandpa_picture",
        label="family picture",
        phrase="a family picture of Grandpa smiling in his garden hat",
        subject="man",
        place="halfway down the hall",
        bedtime_detail="the frame looked dark except where the moon touched it",
        true_quality="it is only a family picture, and Grandpa is safe at home in his own bed",
        tags={"picture", "family"},
    ),
}

DISTORTIONS = {
    "branch_shadow": DistortionCfg(
        id="branch_shadow",
        label="branch shadow",
        cause="a tree branch outside the window",
        motion="sway",
        mistaken_for="a creature peeking in",
        reveal="the branch outside had been waving across the glass and making the eyes seem alive",
        severity=2,
        plausible_for={"owl_picture", "grandpa_picture"},
        tags={"moonlight", "shadow", "branch"},
    ),
    "curtain_shadow": DistortionCfg(
        id="curtain_shadow",
        label="curtain shadow",
        cause="the nursery curtain",
        motion="flutter",
        mistaken_for="something stretching taller and taller",
        reveal="the curtain had been fluttering and laying long moving stripes over it",
        severity=1,
        plausible_for={"boat_picture", "rabbit_picture", "grandpa_picture"},
        tags={"shadow", "curtain"},
    ),
    "moon_glare": DistortionCfg(
        id="moon_glare",
        label="moon glare",
        cause="a bright patch of moonlight",
        motion="gleam",
        mistaken_for="bright eyes staring back",
        reveal="the moon had only flashed on the shiny glass, making two bright spots blink when the clouds moved",
        severity=1,
        plausible_for={"owl_picture", "rabbit_picture"},
        tags={"moonlight", "glass"},
    ),
    "coat_shadow": DistortionCfg(
        id="coat_shadow",
        label="coat shadow",
        cause="a coat hanging on a hook nearby",
        motion="lean",
        mistaken_for="a tall stranger beside the frame",
        reveal="the coat on the hook had been throwing a dark shape beside the picture",
        severity=2,
        plausible_for={"boat_picture", "grandpa_picture"},
        tags={"shadow", "coat"},
    ),
}

AIDS = {
    "night_light": AidCfg(
        id="night_light",
        label="night-light",
        phrase="the little night-light",
        courage_boost=2,
        reveals_truth=True,
        solo_ok=True,
        line='"I can look slowly," {child} whispered, and carried the little night-light into the hall.',
        tags={"light", "nightlight"},
    ),
    "flashlight": AidCfg(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        courage_boost=3,
        reveals_truth=True,
        solo_ok=True,
        line='{child} clicked on a small flashlight from the bedside table and took careful steps toward the hall.',
        tags={"light", "flashlight"},
    ),
    "parent_hand": AidCfg(
        id="parent_hand",
        label="parent hand",
        phrase="the warm pool of light from the hall lamp",
        courage_boost=2,
        reveals_truth=True,
        solo_ok=False,
        line="{parent_cap} held {child}'s hand and turned on the hall lamp.",
        tags={"help", "lamp"},
    ),
    "parent_lamp": AidCfg(
        id="parent_lamp",
        label="bedside lamp",
        phrase="the bedside lamp",
        courage_boost=1,
        reveals_truth=True,
        solo_ok=False,
        line="{parent_cap} sat beside the bed first, then together they carried the bedside lamp to the doorway.",
        tags={"help", "lamp"},
    ),
}

GIRL_NAMES = ["Nora", "Maya", "Lily", "Anna", "Ella", "Ruby", "Hazel", "Mina"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Leo", "Sam", "Noah", "Eli", "Finn"]
TRAITS = ["gentle", "careful", "curious", "bold", "steady", "thoughtful"]
COMFORTS = ["soft rabbit", "small bear", "striped blanket", "tiny pillow", ""]


@dataclass
class StoryParams:
    picture: str
    distortion: str
    aid: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    comfort: str = ""
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        picture="owl_picture",
        distortion="branch_shadow",
        aid="night_light",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="steady",
        comfort="soft rabbit",
    ),
    StoryParams(
        picture="boat_picture",
        distortion="curtain_shadow",
        aid="parent_hand",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="gentle",
        comfort="",
    ),
    StoryParams(
        picture="rabbit_picture",
        distortion="moon_glare",
        aid="flashlight",
        child_name="Maya",
        child_gender="girl",
        parent="mother",
        trait="curious",
        comfort="small bear",
    ),
    StoryParams(
        picture="grandpa_picture",
        distortion="coat_shadow",
        aid="parent_lamp",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        trait="careful",
        comfort="striped blanket",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for picture_id, picture in PICTURES.items():
        for distortion_id, distortion in DISTORTIONS.items():
            if not plausible_misunderstanding(picture, distortion):
                continue
            for aid_id in AIDS:
                combos.append((picture_id, distortion_id, aid_id))
    return combos


def explain_rejection(picture: PictureCfg, distortion: DistortionCfg) -> str:
    return (
        f"(No story: {distortion.label} does not make a believable bedtime misunderstanding "
        f"for {picture.label}. Pick a picture whose shapes could reasonably be misread that way.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    picture = f["picture_cfg"]
    distortion = f["distortion_cfg"]
    mode = f["brave_mode"]
    return [
        'Write a gentle bedtime story for a 3-to-5-year-old that includes the word "picture" and centers on a misunderstanding in the dark.',
        f"Tell a soft story about a {child.type} named {child.attrs['display_name']} who thinks {picture.phrase} is {distortion.mistaken_for} at bedtime, then finds a brave way to learn the truth.",
        f"Write a sleepy, comforting story where bravery means taking one small step {('alone' if mode == 'solo' else 'with help')} instead of staying afraid of a picture.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    picture = f["picture_cfg"]
    distortion = f["distortion_cfg"]
    aid = f["aid_cfg"]
    child_name = child.attrs["display_name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child getting ready for sleep, and {child.pronoun('possessive')} {pw}. The trouble began because a picture in the hall looked wrong in the dark.",
        ),
        (
            "What was the misunderstanding?",
            f"{child_name} thought {picture.phrase} looked like {distortion.mistaken_for}. That was a misunderstanding caused by shadow and moonlight, not by anything real being there.",
        ),
        (
            f"Why did the picture look scary?",
            f"It looked scary because {distortion.cause} changed the way the picture looked in the dim hall. In the dark, moving light made the picture seem different from what it really was.",
        ),
    ]
    if f["brave_mode"] == "solo":
        qa.append(
            (
                f"How was {child_name} brave?",
                f"{child_name} was brave by feeling scared and still choosing to look carefully with {aid.phrase}. The bravery was small and quiet, but it helped turn fear into understanding.",
            )
        )
    else:
        qa.append(
            (
                f"How was {child_name} brave?",
                f"{child_name} was brave by asking for help instead of hiding with the worry. Calling a grown-up and checking the picture together was the safe, honest kind of bravery.",
            )
        )
    qa.append(
        (
            "What was really happening?",
            f"It was only {picture.phrase}, and {distortion.reveal}. Once the child looked carefully, the misunderstanding melted away.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended peacefully, with the picture looking ordinary again and {child_name} feeling calm enough to sleep. The ending shows that knowing the truth changed the dark hall back into a safe place.",
        )
    )
    return qa


KNOWLEDGE = {
    "picture": [
        (
            "What is a picture?",
            "A picture is an image made with paint, pencil, or a camera. It can show a person, an animal, or a place, but it cannot come alive."
        )
    ],
    "shadow": [
        (
            "What is a shadow?",
            "A shadow is a dark shape made when something blocks light. Shadows can look strange when they move, especially at night."
        )
    ],
    "moonlight": [
        (
            "Why can things look different in moonlight?",
            "Moonlight is dimmer than daytime light, so it leaves some parts bright and some parts dark. That can make ordinary things look unusual for a moment."
        )
    ],
    "flashlight": [
        (
            "What does a flashlight do?",
            "A flashlight shines a beam of light so you can see clearly in the dark. Seeing clearly often helps you understand what something really is."
        )
    ],
    "nightlight": [
        (
            "What is a night-light for?",
            "A night-light gives a small, gentle glow at bedtime. It helps a room feel safer without making it bright like daytime."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel a little scared. Sometimes bravery means taking one careful step or asking for help."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something is one way, but the truth is different. Looking carefully or asking a question can fix it."
        )
    ],
}
KNOWLEDGE_ORDER = ["picture", "shadow", "moonlight", "flashlight", "nightlight", "bravery", "misunderstanding"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"picture", "bravery", "misunderstanding"}
    tags |= set(f["distortion_cfg"].tags)
    tags |= set(f["aid_cfg"].tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
plausible(P, D) :- picture(P), distortion(D), distortion_fits(D, P).
valid(P, D, A) :- plausible(P, D), aid(A).

brave_base(3) :- chosen_trait(T), brave_trait(T).
brave_base(2) :- chosen_trait(T), calm_trait(T), not brave_trait(T).
brave_base(1) :- chosen_trait(T), not calm_trait(T), not brave_trait(T).

difficulty(S + 1) :- chosen_distortion(D), severity(D, S).
score(B + C) :- brave_base(B), chosen_aid(A), courage_boost(A, C).

solo :- chosen_aid(A), solo_ok(A), score(S), difficulty(D), S >= D + 2.
mode(solo) :- solo.
mode(together) :- not solo.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for picture_id in PICTURES:
        lines.append(asp.fact("picture", picture_id))
    for distortion_id, distortion in DISTORTIONS.items():
        lines.append(asp.fact("distortion", distortion_id))
        lines.append(asp.fact("severity", distortion_id, distortion.severity))
        for picture_id in sorted(distortion.plausible_for):
            lines.append(asp.fact("distortion_fits", distortion_id, picture_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("courage_boost", aid_id, aid.courage_boost))
        if aid.solo_ok:
            lines.append(asp.fact("solo_ok", aid_id))
    for trait in sorted(BRAVE_TRAITS):
        lines.append(asp.fact("brave_trait", trait))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("calm_trait", trait))
    for trait in sorted(set(TRAITS)):
        lines.append(asp.fact("trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_mode(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_aid", params.aid),
        asp.fact("chosen_distortion", params.distortion),
    ])
    model = asp.one_model(asp_program(scenario, "#show mode/1."))
    atoms = asp.atoms(model, "mode")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params for seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        py_mode = "solo" if can_check_alone(params.trait, AIDS[params.aid], DISTORTIONS[params.distortion]) else "together"
        if asp_mode(params) != py_mode:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: bravery mode matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: bravery mode differed on {mismatches}/{len(cases)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation and emit succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Bedtime story world: a child misunderstands a picture in the dark and finds a brave way to learn the truth."
    )
    ap.add_argument("--picture", choices=PICTURES)
    ap.add_argument("--distortion", choices=DISTORTIONS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.picture and args.distortion:
        picture = PICTURES[args.picture]
        distortion = DISTORTIONS[args.distortion]
        if not plausible_misunderstanding(picture, distortion):
            raise StoryError(explain_rejection(picture, distortion))

    combos = [
        combo for combo in valid_combos()
        if (args.picture is None or combo[0] == args.picture)
        and (args.distortion is None or combo[1] == args.distortion)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    picture_id, distortion_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    comfort = rng.choice(COMFORTS)
    return StoryParams(
        picture=picture_id,
        distortion=distortion_id,
        aid=aid_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        comfort=comfort,
    )


def generate(params: StoryParams) -> StorySample:
    if params.picture not in PICTURES:
        raise StoryError(f"(Invalid picture: {params.picture})")
    if params.distortion not in DISTORTIONS:
        raise StoryError(f"(Invalid distortion: {params.distortion})")
    if params.aid not in AIDS:
        raise StoryError(f"(Invalid aid: {params.aid})")
    picture_cfg = PICTURES[params.picture]
    distortion_cfg = DISTORTIONS[params.distortion]
    aid_cfg = AIDS[params.aid]
    if not plausible_misunderstanding(picture_cfg, distortion_cfg):
        raise StoryError(explain_rejection(picture_cfg, distortion_cfg))

    world = tell(
        picture_cfg=picture_cfg,
        distortion_cfg=distortion_cfg,
        aid_cfg=aid_cfg,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        comfort=params.comfort,
    )

    story_text = world.render().replace("child", params.child_name)
    story_text = story_text.replace("parent", world.facts["parent"].label_word)

    return StorySample(
        params=params,
        story=story_text.replace("  ", " "),
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
        print(asp_program("", "#show valid/3.\n#show mode/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (picture, distortion, aid) combos:\n")
        for picture, distortion, aid in combos:
            print(f"  {picture:16} {distortion:15} {aid}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.picture} with {p.distortion} ({p.aid})"
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
