#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/imaginary_inner_monologue_foreshadowing_conflict_bedtime_story.py
==============================================================================================

A standalone story world about bedtime worries, imaginary creatures, and the calm
grown-up help that turns a scary room back into an ordinary one.

This world rebuilds a tiny bedtime-story domain rather than one fixed paragraph:
a child goes to bed, a harmless ordinary cause makes the room feel strange, the
child's inner monologue turns that strangeness into something imaginary, and a
small conflict follows -- hide alone, or ask for help? A grown-up then uses a
reasonable bedtime fix that actually matches the cause, and the ending image
shows what changed in the room and in the child's heart.

Run it
------
    python storyworlds/worlds/gpt-5.4/imaginary_inner_monologue_foreshadowing_conflict_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/imaginary_inner_monologue_foreshadowing_conflict_bedtime_story.py --cause curtain_shadow --helper clip_curtain
    python storyworlds/worlds/gpt-5.4/imaginary_inner_monologue_foreshadowing_conflict_bedtime_story.py --cause branch_tap --helper tidy_chair
    python storyworlds/worlds/gpt-5.4/imaginary_inner_monologue_foreshadowing_conflict_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/imaginary_inner_monologue_foreshadowing_conflict_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/imaginary_inner_monologue_foreshadowing_conflict_bedtime_story.py --verify
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
class Cause:
    id: str
    label: str
    phrase: str
    foreshadow: str
    sign_text: str
    imagined: str
    reveal: str
    fix_modes: set[str] = field(default_factory=set)
    signs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    action_text: str = ""
    reveal_text: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_signs_raise_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    child = world.entities.get("child")
    cause = world.entities.get("cause")
    if not room or not child or not cause:
        return out
    if cause.meters["active"] < THRESHOLD or room.meters["truth_known"] >= THRESHOLD:
        return out

    if cause.attrs.get("visual") and ("visual",) not in world.fired:
        world.fired.add(("visual",))
        room.meters["odd_visual"] += 1
        child.memes["fear"] += 1
        out.append("__visual__")
    if cause.attrs.get("sound") and ("sound",) not in world.fired:
        world.fired.add(("sound",))
        room.meters["odd_sound"] += 1
        child.memes["fear"] += 1
        out.append("__sound__")
    return out


def _r_fear_feeds_imagination(world: World) -> list[str]:
    child = world.entities.get("child")
    room = world.entities.get("room")
    if not child or not room:
        return []
    if child.memes["fear"] < THRESHOLD or room.meters["truth_known"] >= THRESHOLD:
        return []
    sig = ("imagining",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["imagining"] += 1
    return ["__imagining__"]


def _r_truth_brings_relief(world: World) -> list[str]:
    child = world.entities.get("child")
    room = world.entities.get("room")
    if not child or not room:
        return []
    if room.meters["truth_known"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    child.memes["courage"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="signs_raise_fear", tag="mood", apply=_r_signs_raise_fear),
    Rule(name="fear_feeds_imagination", tag="mood", apply=_r_fear_feeds_imagination),
    Rule(name="truth_brings_relief", tag="mood", apply=_r_truth_brings_relief),
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


CAUSES = {
    "curtain_shadow": Cause(
        id="curtain_shadow",
        label="curtain shadow",
        phrase="a pale curtain that puffed in and out beside the bed",
        foreshadow="Moonlight slid through the window and laid a long silver stripe across the rug.",
        sign_text="Now and then the curtain breathed toward the wall and made a tall shape that stretched and shrank.",
        imagined="an imaginary giant",
        reveal="it was only the curtain moving in the little draft from the window",
        fix_modes={"steady", "light"},
        signs={"visual"},
        tags={"shadow", "curtain", "bedtime"},
    ),
    "branch_tap": Cause(
        id="branch_tap",
        label="tapping branch",
        phrase="a tree branch outside the window",
        foreshadow="Outside, the wind kept brushing the tree against the house in soft, restless strokes.",
        sign_text="A tap-tap came at the glass, and a thin shadow flickered over the window frame.",
        imagined="an imaginary finger",
        reveal="the branch had been tapping the window whenever the wind pushed it near",
        fix_modes={"window", "light"},
        signs={"visual", "sound"},
        tags={"shadow", "window", "tree", "bedtime"},
    ),
    "laundry_chair": Cause(
        id="laundry_chair",
        label="laundry chair",
        phrase="a chair with a robe and a pile of folded clothes on it",
        foreshadow="At the far corner of the room, a chair stood very still, but its shapes were all lumpy in the dark.",
        sign_text="In the dim room, the robe on the chair looked broad at the shoulders and pointy at the top.",
        imagined="an imaginary bear",
        reveal="the scary shape was only a chair wearing a robe and carrying the laundry",
        fix_modes={"tidy", "light"},
        signs={"visual"},
        tags={"shadow", "laundry", "bedtime"},
    ),
    "toy_eyes": Cause(
        id="toy_eyes",
        label="toy eyes",
        phrase="a toy basket and a shiny train left by the shelf",
        foreshadow="A tiny bit of streetlight found its way between the curtains and touched the shelf in little glints.",
        sign_text="Two bright dots gleamed near the floor, and the blocks beside them made a crooked mouth.",
        imagined="an imaginary little dragon",
        reveal="the dots were the train's silver lamps and the crooked mouth was only a stack of blocks",
        fix_modes={"tidy", "light"},
        signs={"visual"},
        tags={"toy", "shadow", "bedtime"},
    ),
}

HELPERS = {
    "nightlight": Helper(
        id="nightlight",
        label="night-light",
        phrase="a small star-shaped night-light",
        handles={"light"},
        action_text="plugged in a small star-shaped night-light by the dresser",
        reveal_text="The soft gold glow reached the dark corner at once.",
        ending_image="The room stayed soft and clear, with no corners left pretending to be anything else.",
        tags={"nightlight", "light"},
    ),
    "clip_curtain": Helper(
        id="clip_curtain",
        label="curtain clip",
        phrase="a clothespin and a gentle tuck",
        handles={"steady"},
        action_text="gathered the curtain, clipped it neatly to the side, and closed the window the tiniest bit",
        reveal_text="At once the wall stopped changing shapes.",
        ending_image="The curtain rested flat and quiet, and the moon made only one small silver patch on the floor.",
        tags={"curtain", "bedtime"},
    ),
    "check_window": Helper(
        id="check_window",
        label="window check",
        phrase="a look at the window",
        handles={"window", "light"},
        action_text="walked to the window, peeked outside with the hall light behind them, and showed the branch swaying there",
        reveal_text="Once they saw the branch, the tapping lost its mystery.",
        ending_image="The branch still moved outside, but now it looked like a tree saying good night instead of a visitor asking to come in.",
        tags={"window", "tree", "light"},
    ),
    "tidy_corner": Helper(
        id="tidy_corner",
        label="tidy corner",
        phrase="a quick tidy-up",
        handles={"tidy"},
        action_text="crossed the room together and put the robe, clothes, and toys where they belonged",
        reveal_text="With the pile gone, the corner became only a corner again.",
        ending_image="The shelf and chair looked plain and sleepy, as if they had always meant to behave themselves.",
        tags={"tidy", "toy", "laundry"},
    ),
}

GIRL_NAMES = ["Nora", "Mila", "Ivy", "Lila", "June", "Cora", "Eva", "Ruby", "Tessa", "Wren"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Eli", "Jonah", "Leo", "Finn", "Toby", "Jude"]
TRAITS = ["dreamy", "careful", "brave", "thoughtful", "tender", "curious"]
COMFORTS = ["a quilt with moons on it", "a stuffed rabbit", "a soft blue blanket", "a little plush fox", "a pillow with stars"]
BEDTIMES = ["early bedtime", "a sleepy bedtime", "a quiet bedtime", "a windy bedtime"]


def helper_works(cause: Cause, helper: Helper) -> bool:
    return bool(cause.fix_modes & helper.handles)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for cause_id, cause in CAUSES.items():
        for helper_id, helper in HELPERS.items():
            if helper_works(cause, helper):
                combos.append((cause_id, helper_id))
    return sorted(combos)


@dataclass
class StoryParams:
    cause: str
    helper: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    comfort: str
    bedtime: str
    seed: Optional[int] = None


def introduce(world: World, child: Entity, parent: Entity, comfort: str, bedtime: str) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"It was {bedtime}, and {child.id}'s {parent.label_word} tucked {child.pronoun('object')} into bed with {comfort}."
    )
    world.say(
        f"{child.id} was a {child.attrs.get('trait')} little {child.type} who could think up whole worlds before a yawn had even finished."
    )


def foreshadow(world: World, cause: Cause) -> None:
    world.say(cause.foreshadow)
    world.say(f"In the room there was {cause.phrase}.")
    world.get("cause").meters["active"] += 1
    if "visual" in cause.signs:
        world.get("cause").attrs["visual"] = True
    if "sound" in cause.signs:
        world.get("cause").attrs["sound"] = True


def signs_begin(world: World, child: Entity, cause: Cause) -> None:
    propagate(world, narrate=False)
    world.say(cause.sign_text)
    if child.memes["fear"] >= 2:
        world.say(f"{child.id}'s shoulders crept up toward {child.pronoun('possessive')} ears.")
    else:
        world.say(f"{child.id} went very still and listened.")


def inner_monologue(world: World, child: Entity, cause: Cause) -> None:
    child.memes["worry"] += 1
    if child.memes["imagining"] >= THRESHOLD:
        world.say(
            f'In {child.pronoun("possessive")} head, {child.id} thought, "What if that is {cause.imagined}? '
            f'What if it is waiting for me to fall asleep?"'
        )
    else:
        world.say(
            f'In {child.pronoun("possessive")} head, {child.id} wondered whether the dark was trying to tell a trickier story than the room meant to tell.'
        )


def conflict(world: World, child: Entity, parent: Entity) -> None:
    child.memes["conflict"] += 1
    if child.attrs.get("trait") in {"brave", "curious"}:
        world.say(
            f"{child.id} pulled the blanket to {child.pronoun('possessive')} chin anyway. Part of {child.pronoun('object')} wanted to be brave alone, and part of {child.pronoun('object')} wanted to call for {child.pronoun('possessive')} {parent.label_word} right away."
        )
    else:
        world.say(
            f"{child.id} hid all the way to the nose under the covers. {child.pronoun().capitalize()} did not want to sound babyish, but {child.pronoun()} also did not want to stay scared and quiet."
        )
    world.say(f'At last {child.pronoun()} whispered, "{parent.label_word.capitalize()}, will you come look with me?"')
    child.memes["trust"] += 1


def arrive_to_help(world: World, parent: Entity, child: Entity) -> None:
    parent.memes["care"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came in softly and sat on the edge of the bed instead of laughing."
    )
    world.say(
        f'"Let us look together," {parent.pronoun()} said. "An imaginary worry can feel big in the dark, and it often turns small when we shine a kind light on it."'
    )
    child.memes["supported"] += 1


def apply_helper(world: World, parent: Entity, child: Entity, cause: Cause, helper: Helper) -> None:
    world.get("helper").meters["used"] += 1
    world.say(
        f"Then {parent.pronoun()} {helper.action_text}. {helper.reveal_text}"
    )
    world.get("cause").meters["active"] = 0.0
    world.get("room").meters["truth_known"] += 1
    world.get("room").meters["odd_visual"] = 0.0
    world.get("room").meters["odd_sound"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f'"See?" {parent.label_word.capitalize()} whispered. {cause.reveal[0].upper()}{cause.reveal[1:]}.'
    )
    child.memes["lesson"] += 1
    child.memes["love"] += 1


def settle(world: World, child: Entity, parent: Entity, helper: Helper, cause: Cause) -> None:
    world.say(
        f"{child.id} let out a long breath that {child.pronoun()} had been holding without knowing it."
    )
    if child.memes["relief"] >= THRESHOLD:
        world.say(
            f'"So it was not {cause.imagined} after all," {child.pronoun()} murmured, feeling a little shy and a lot lighter.'
        )
    world.say(
        f'{parent.label_word.capitalize()} kissed {child.pronoun("possessive")} forehead. "Rooms can look strange when we are tired," {parent.pronoun()} said, "but strange is not the same as dangerous."'
    )
    world.say(
        f"{helper.ending_image} Soon {child.id} curled close under {child.attrs.get('comfort')} and fell asleep in an ordinary room that no longer needed to pretend."
    )


def tell(
    cause: Cause,
    helper: Helper,
    child_name: str = "Nora",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "dreamy",
    comfort: str = "a quilt with moons on it",
    bedtime: str = "a quiet bedtime",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            attrs={"trait": trait, "comfort": comfort},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    world.add(
        Entity(
            id="room",
            type="room",
            label="bedroom",
        )
    )
    world.add(
        Entity(
            id="cause",
            type="cause",
            label=cause.label,
            attrs={"visual": False, "sound": False},
            tags=set(cause.tags),
        )
    )
    world.add(
        Entity(
            id="helper",
            type="helper",
            label=helper.label,
            tags=set(helper.tags),
        )
    )

    introduce(world, child, parent, comfort, bedtime)
    foreshadow(world, cause)

    world.para()
    signs_begin(world, child, cause)
    inner_monologue(world, child, cause)
    conflict(world, child, parent)

    world.para()
    arrive_to_help(world, parent, child)
    apply_helper(world, parent, child, cause, helper)
    settle(world, child, parent, helper, cause)

    world.facts.update(
        child=child,
        parent=parent,
        cause_cfg=cause,
        helper_cfg=helper,
        room=world.get("room"),
        comfort=comfort,
        bedtime=bedtime,
        imagined=cause.imagined,
        truth_known=world.get("room").meters["truth_known"] >= THRESHOLD,
        fear_before_help=child.memes["imagining"] >= THRESHOLD,
        resolved=child.memes["relief"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "bedtime": [
        (
            "Why can rooms look different at bedtime?",
            "At bedtime the room is darker, and tired eyes notice shadows and sounds more strongly. Ordinary things can seem strange until you look carefully."
        )
    ],
    "imaginary": [
        (
            "What does imaginary mean?",
            "Imaginary means something you can picture in your mind even though it is not really there. Imaginary stories can be fun, but imaginary worries can feel real until someone helps you check."
        )
    ],
    "shadow": [
        (
            "What is a shadow?",
            "A shadow is a dark shape made when light is blocked by something. When the light or the object moves, the shadow changes shape too."
        )
    ],
    "nightlight": [
        (
            "What is a night-light for?",
            "A night-light gives a small, gentle glow in the dark. It helps you see what things really are without making the room too bright for sleep."
        )
    ],
    "curtain": [
        (
            "Why can a curtain make scary shapes at night?",
            "A curtain can move in a draft, and moonlight can throw that moving shape onto the wall. In the dark, a simple cloth shape can look much bigger than it really is."
        )
    ],
    "window": [
        (
            "Why do branches tap on windows?",
            "When the wind blows, branches can swing and touch the glass. That makes a tapping sound even though nobody is outside trying to come in."
        )
    ],
    "tree": [
        (
            "Why do trees sound louder at night?",
            "Night feels quieter, so small sounds stand out more. A branch brushing a house can seem big when everything else is still."
        )
    ],
    "laundry": [
        (
            "Why can laundry on a chair look strange in the dark?",
            "Piled clothes make uneven shapes with bumps and corners. In dim light, your brain may guess a creature before it guesses a chair."
        )
    ],
    "toy": [
        (
            "Why can toys look spooky at night?",
            "Toys can have shiny parts, pointy corners, or faces painted on them. In the dark, those little details can look like eyes or teeth until you look closely."
        )
    ],
    "tidy": [
        (
            "How can tidying a room help at bedtime?",
            "Tidying puts odd shapes back where they belong, so the room is easier to read in the dark. A clear floor and a calm corner leave less for a worried mind to guess about."
        )
    ],
    "light": [
        (
            "Why does looking carefully help with a bedtime worry?",
            "Looking carefully gives your brain better information. When you can see the real thing, your fear usually has less mystery to feed on."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "imaginary",
    "bedtime",
    "shadow",
    "curtain",
    "window",
    "tree",
    "laundry",
    "toy",
    "nightlight",
    "tidy",
    "light",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cause = f["cause_cfg"]
    helper = f["helper_cfg"]
    parent = f["parent"]
    return [
        'Write a short bedtime story for a 3-to-5-year-old that includes the word "imaginary" and uses inner monologue, foreshadowing, and conflict.',
        f"Tell a gentle night story where {child.id} mistakes {cause.label} for {cause.imagined}, worries quietly in {child.pronoun('possessive')} own thoughts, and asks {child.pronoun('possessive')} {parent.label_word} for help.",
        f"Write a calm bedtime story in which a grown-up uses {helper.phrase} to show that a scary thing in the dark is ordinary after all.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    cause = f["cause_cfg"]
    helper = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type} getting ready to sleep, and {child.pronoun('possessive')} {parent.label_word} who comes to help. The story stays close to what {child.id} feels in the dark."
        ),
        (
            "What made bedtime feel scary?",
            f"{cause.sign_text} That ordinary sight or sound gave {child.id} something mysterious to worry about."
        ),
        (
            f"What did {child.id} imagine in {child.pronoun('possessive')} head?",
            f"{child.id} imagined {cause.imagined}. The worry grew because the room was dark and {child.pronoun()} could not yet see the real cause clearly."
        ),
        (
            f"What was the conflict for {child.id}?",
            f"{child.id} did not know whether to stay hidden under the covers or ask for help. {child.pronoun().capitalize()} wanted to seem brave, but {child.pronoun()} also wanted the scary feeling to stop."
        ),
        (
            f"How did {child.id}'s {parent.label_word} help?",
            f"{parent.label_word.capitalize()} {helper.action_text}. That helped {child.id} see that {cause.reveal}."
        ),
        (
            "How did the story end?",
            f"In the end, the room looked ordinary again and {child.id} felt calm enough to sleep. The ending proves the change by showing that the same room no longer seemed full of imaginary danger."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["cause_cfg"].tags) | set(f["helper_cfg"].tags) | {"imaginary"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cause="curtain_shadow",
        helper="clip_curtain",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="dreamy",
        comfort="a quilt with moons on it",
        bedtime="a windy bedtime",
    ),
    StoryParams(
        cause="branch_tap",
        helper="check_window",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="thoughtful",
        comfort="a soft blue blanket",
        bedtime="a quiet bedtime",
    ),
    StoryParams(
        cause="laundry_chair",
        helper="tidy_corner",
        child_name="Mila",
        child_gender="girl",
        parent="mother",
        trait="careful",
        comfort="a stuffed rabbit",
        bedtime="a sleepy bedtime",
    ),
    StoryParams(
        cause="toy_eyes",
        helper="nightlight",
        child_name="Finn",
        child_gender="boy",
        parent="father",
        trait="curious",
        comfort="a little plush fox",
        bedtime="an early bedtime",
    ),
    StoryParams(
        cause="curtain_shadow",
        helper="nightlight",
        child_name="Ruby",
        child_gender="girl",
        parent="mother",
        trait="brave",
        comfort="a pillow with stars",
        bedtime="a quiet bedtime",
    ),
]


def explain_rejection(cause: Cause, helper: Helper) -> str:
    need = " / ".join(sorted(cause.fix_modes))
    has = " / ".join(sorted(helper.handles))
    return (
        f"(No story: {helper.label} does not reasonably solve {cause.label}. "
        f"The cause needs a helper that handles {need}, but this helper handles {has}.)"
    )


ASP_RULES = r"""
works(C, H) :- cause(C), helper(H), fix_mode(C, M), handles(H, M).
valid(C, H) :- works(C, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for mode in sorted(cause.fix_modes):
            lines.append(asp.fact("fix_mode", cause_id, mode))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for mode in sorted(helper.handles):
            lines.append(asp.fact("handles", helper_id, mode))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def _smoke_generate(params: StoryParams) -> None:
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    sink = io.StringIO()
    with redirect_stdout(sink):
        emit(sample, trace=False, qa=False)


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        for params in CURATED:
            _smoke_generate(params)
        defaults = resolve_params(build_parser().parse_args([]), random.Random(123))
        _smoke_generate(defaults)
        print(f"OK: smoke-generated {len(CURATED) + 1} stories.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: bedtime worry, imaginary fear, calm help."
    )
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (cause, helper) set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {args.cause})")
    if args.helper and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")

    if args.cause and args.helper:
        cause = CAUSES[args.cause]
        helper = HELPERS[args.helper]
        if not helper_works(cause, helper):
            raise StoryError(explain_rejection(cause, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.cause is None or combo[0] == args.cause)
        and (args.helper is None or combo[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cause_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(names)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    comfort = rng.choice(COMFORTS)
    bedtime = rng.choice(BEDTIMES)
    return StoryParams(
        cause=cause_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        comfort=comfort,
        bedtime=bedtime,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    cause = CAUSES[params.cause]
    helper = HELPERS[params.helper]
    if not helper_works(cause, helper):
        raise StoryError(explain_rejection(cause, helper))

    world = tell(
        cause=cause,
        helper=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        comfort=params.comfort,
        bedtime=params.bedtime,
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cause, helper) combos:\n")
        for cause_id, helper_id in combos:
            print(f"  {cause_id:15} {helper_id}")
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
            header = f"### {p.child_name}: {p.cause} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
