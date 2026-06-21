#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stir_inquiry_sound_effects_flashback_foreshadowing_bedtime.py
=========================================================================================

A standalone storyworld for a bedtime tale about a child who hears a worrying
night sound, makes a soft inquiry, and learns the harmless cause. The world is
small and classical: a room, a child, a grown-up, a nighttime sound source, a
cozy helper, and a simple fix.

The prose always includes:
- the seed words "stir" and "inquiry"
- sound effects
- a brief flashback
- a light foreshadowing beat
- a bedtime-story tone

Run it
------
    python storyworlds/worlds/gpt-5.4/stir_inquiry_sound_effects_flashback_foreshadowing_bedtime.py
    python storyworlds/worlds/gpt-5.4/stir_inquiry_sound_effects_flashback_foreshadowing_bedtime.py --source branch --helper flashlight
    python storyworlds/worlds/gpt-5.4/stir_inquiry_sound_effects_flashback_foreshadowing_bedtime.py --source mice
    python storyworlds/worlds/gpt-5.4/stir_inquiry_sound_effects_flashback_foreshadowing_bedtime.py --all --qa
    python storyworlds/worlds/gpt-5.4/stir_inquiry_sound_effects_flashback_foreshadowing_bedtime.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so storyworlds/ is three
# directories up from here.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
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
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
@dataclass
class Source:
    id: str
    label: str
    place: str
    sound: str
    reveal: str
    fix: str
    needs_wind: bool = False
    indoors: bool = False
    spooky: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    glow: str
    calm_text: str
    works_outdoors: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Drink:
    id: str
    label: str
    phrase: str
    stir_line: str
    steam: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bedtime:
    id: str
    room: str
    window_text: str
    blanket: str
    closing_image: str


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sound_spreads(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    child = world.entities.get("child")
    room = world.entities.get("room")
    if source is None or child is None or room is None:
        return out
    if source.meters["rattling"] < THRESHOLD:
        return out
    sig = ("sound_spreads", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["noise"] += 1
    child.memes["worry"] += float(world.facts.get("source_cfg").spooky)
    out.append("__sound__")
    return out


def _r_inquiry_seeks(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    grown = world.entities.get("grown")
    if child is None or grown is None:
        return out
    if child.memes["inquiry"] < THRESHOLD:
        return out
    sig = ("inquiry_seeks", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    grown.memes["attention"] += 1
    out.append("__inquiry__")
    return out


def _r_explanation_calms(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    source = world.entities.get("source")
    if child is None or source is None:
        return out
    if source.meters["understood"] < THRESHOLD:
        return out
    sig = ("explanation_calms", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["sleepy"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sound_spreads", tag="physical", apply=_r_sound_spreads),
    Rule(name="inquiry_seeks", tag="social", apply=_r_inquiry_seeks),
    Rule(name="explanation_calms", tag="social", apply=_r_explanation_calms),
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


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def source_allowed(source: Source, wind: str) -> bool:
    if source.needs_wind and wind == "still":
        return False
    if source.indoors and wind == "gusty":
        return True
    return True


def helper_works(helper: Helper, source: Source) -> bool:
    if source.place == "outside the bedroom window" and not helper.works_outdoors:
        return False
    return True


def valid_combo(source_id: str, helper_id: str, drink_id: str, wind: str) -> bool:
    source = SOURCES[source_id]
    helper = HELPERS[helper_id]
    drink = DRINKS[drink_id]
    if not source_allowed(source, wind):
        return False
    if not helper_works(helper, source):
        return False
    if not drink.stir_line:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for source_id in SOURCES:
        for helper_id in HELPERS:
            for drink_id in DRINKS:
                for wind in WINDS:
                    if valid_combo(source_id, helper_id, drink_id, wind):
                        out.append((source_id, helper_id, drink_id, wind))
    return out


def explain_rejection(source: Source, helper: Helper, wind: str) -> str:
    if source.needs_wind and wind == "still":
        return (
            f"(No story: {source.label} only makes that bedtime sound when the air is moving, "
            f"but the wind is still.)"
        )
    if source.place == "outside the bedroom window" and not helper.works_outdoors:
        return (
            f"(No story: {helper.label} is too weak for looking outside the bedroom window. "
            f"Pick a brighter helper.)"
        )
    return "(No story: this bedtime setup does not make a reasonable sound mystery.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_worry(world: World) -> dict:
    sim = world.copy()
    source = sim.get("source")
    source.meters["rattling"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "worry": child.memes["worry"],
        "noise": sim.get("room").meters["noise"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def settle_night(world: World, child: Entity, grown: Entity, bedtime: Bedtime, drink: Drink, wind: str) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"It was bedtime, and {bedtime.room} had gone soft and dim. "
        f"{child.id} was tucked under {bedtime.blanket}, while {child.pronoun('possessive')} "
        f"{grown.label_word} carried in {drink.phrase}."
    )
    world.say(
        f"{drink.stir_line} {drink.steam} Outside, {bedtime.window_text}"
    )
    if wind == "gusty":
        world.say(
            "At the edge of the quiet, the night seemed ready to tell a tiny secret before anyone knew what it was."
        )
    else:
        world.say(
            "Everything felt almost still, the way a room does just before the last good-night kiss."
        )


def first_sound(world: World, source: Source) -> None:
    src = world.get("source")
    src.meters["rattling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the sound: \"{source.sound}\" It made the dark seem to stir around the corners of the room."
    )


def inquiry(world: World, child: Entity, grown: Entity, source: Source) -> None:
    pred = predict_worry(world)
    child.memes["inquiry"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{child.id} lifted {child.pronoun("possessive")} head from the pillow. '
        f'"{grown.label_word.capitalize()}," {child.pronoun()} whispered, '
        f'"may I make a small inquiry? What is going "{source.sound}" near {source.place}?"'
    )


def flashback(world: World, child: Entity, grown: Entity, source: Source) -> None:
    child.memes["memory"] += 1
    world.say(
        f"For one moment, {child.id} remembered another night when a simple thing had sounded grander in the dark. "
        f"Last week the wash basket had gone \"thump\" in the hall, and {grown.label_word} had shown that it was only a towel slipping down."
    )
    world.say(
        f"That memory helped a little, but \"{source.sound}\" still tickled at {child.pronoun('possessive')} thoughts."
    )


def investigate(world: World, child: Entity, grown: Entity, source: Source, helper: Helper) -> None:
    grown.memes["care"] += 1
    child.memes["trust"] += 1
    world.say(
        f'{grown.label_word.capitalize()} smiled the calm kind of smile that makes worries smaller. '
        f'"Let us look together," {grown.pronoun()} said, taking {helper.phrase}.'
    )
    world.say(
        f"{helper.glow} The two of them padded to the window, listening: \"{source.sound}\""
    )


def reveal(world: World, child: Entity, grown: Entity, source: Source, helper: Helper, wind: str) -> None:
    src = world.get("source")
    src.meters["understood"] += 1
    src.meters["fixed"] += 1
    propagate(world, narrate=False)
    wind_clause = "the wind gave it another nudge" if wind == "gusty" else "it shifted a tiny bit on its own"
    world.say(
        f"There it was. {source.reveal}, and {wind_clause}, making the very sound they had heard."
    )
    world.say(
        f'{grown.label_word.capitalize()} {source.fix}. "{helper.calm_text}," {grown.pronoun()} murmured.'
    )


def comfort_and_close(world: World, child: Entity, grown: Entity, bedtime: Bedtime, drink: Drink) -> None:
    child.memes["cozy"] += 1
    child.memes["sleepy"] += 1
    world.say(
        f"Back in bed, {child.id} took a warm sip of {drink.label}. "
        f"The cup no longer felt mysterious at all; it only smelled sweet and safe."
    )
    world.say(
        f"Soon the room was quiet again, and {bedtime.closing_image}"
    )


# ---------------------------------------------------------------------------
# Story driver
# ---------------------------------------------------------------------------
def tell(
    bedtime: Bedtime,
    source: Source,
    helper: Helper,
    drink: Drink,
    *,
    child_name: str,
    child_gender: str,
    grown_type: str,
    wind: str,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", label=child_name))
    grown = world.add(Entity(id="Grownup", kind="character", type=grown_type, role="grown", label="the grown-up"))
    room = world.add(Entity(id="room", type="room", label=bedtime.room))
    src = world.add(Entity(id="source", type="source", label=source.label, phrase=source.label, tags=set(source.tags)))
    tool = world.add(Entity(id="helper", type="helper", label=helper.label, phrase=helper.phrase, tags=set(helper.tags)))
    cup = world.add(Entity(id="drink", type="drink", label=drink.label, phrase=drink.phrase, tags=set(drink.tags)))

    world.facts.update(
        bedtime=bedtime,
        source_cfg=source,
        helper_cfg=helper,
        drink_cfg=drink,
        child=child,
        grown=grown,
        room=room,
        source=src,
        helper=tool,
        drink=cup,
        wind=wind,
    )

    settle_night(world, child, grown, bedtime, drink, wind)
    world.para()
    first_sound(world, source)
    inquiry(world, child, grown, source)
    flashback(world, child, grown, source)
    world.para()
    investigate(world, child, grown, source, helper)
    reveal(world, child, grown, source, helper, wind)
    world.para()
    comfort_and_close(world, child, grown, bedtime, drink)

    world.facts.update(
        resolved=src.meters["understood"] >= THRESHOLD,
        fixed=src.meters["fixed"] >= THRESHOLD,
        calm=child.memes["relief"] >= THRESHOLD,
        sleepy=child.memes["sleepy"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
BEDTIMES = {
    "bedroom": Bedtime(
        id="bedroom",
        room="the little bedroom",
        window_text="the moon made a silver square on the floor by the window",
        blanket="a patchwork blanket",
        closing_image="the moon-square rested quietly on the floor, and even the shadows looked ready for sleep.",
    ),
    "attic_nook": Bedtime(
        id="attic_nook",
        room="the attic nook bedroom",
        window_text="starlight lay across the slanted ceiling like pale ribbon",
        blanket="a thick blue quilt",
        closing_image="the slanted ceiling watched over the bed, peaceful as a folded wing.",
    ),
}

SOURCES = {
    "branch": Source(
        id="branch",
        label="a loose branch",
        place="outside the bedroom window",
        sound="tap-tap... scritch",
        reveal="A loose branch was brushing the glass",
        fix="looped the branch gently away from the pane",
        needs_wind=True,
        indoors=False,
        spooky=2,
        tags={"wind", "branch", "window"},
    ),
    "shades": Source(
        id="shades",
        label="the pull-cord of the bamboo shade",
        place="the window",
        sound="tik-tik... tik",
        reveal="The pull-cord of the bamboo shade was tapping the frame",
        fix="tucked the cord around its little hook",
        needs_wind=True,
        indoors=True,
        spooky=1,
        tags={"wind", "shade", "window"},
    ),
    "teaspoon": Source(
        id="teaspoon",
        label="a teaspoon in the kitchen mug",
        place="the kitchen",
        sound="ting... ting",
        reveal="A teaspoon was leaning against the side of a mug left by the sink",
        fix="laid the spoon flat on a small plate",
        needs_wind=False,
        indoors=True,
        spooky=1,
        tags={"kitchen", "spoon", "mug"},
    ),
}

HELPERS = {
    "flashlight": Helper(
        id="flashlight",
        label="flashlight",
        phrase="a little flashlight",
        glow="Click. A steady yellow circle slid over the floorboards.",
        calm_text="It sounds bigger than it is at bedtime",
        works_outdoors=True,
        tags={"flashlight"},
    ),
    "lantern": Helper(
        id="lantern",
        label="night lantern",
        phrase="the small night lantern",
        glow="Glow. Warm light spilled over the curtain and the windowsill.",
        calm_text="Now we know its true name",
        works_outdoors=True,
        tags={"lantern"},
    ),
    "candle_stub": Helper(
        id="candle_stub",
        label="tiny candle stub",
        phrase="a tiny candle stub in a saucer",
        glow="The tiny flame wobbled and made the room bright only in little patches.",
        calm_text="We found it, but a steadier light would be kinder",
        works_outdoors=False,
        tags={"candle"},
    ),
}

DRINKS = {
    "milk": Drink(
        id="milk",
        label="warm milk",
        phrase="a mug of warm milk with honey",
        stir_line='The spoon went "clink-clink" as the honey was stirred in, one last sleepy stir before the cup was set on the bedside table.',
        steam="A curl of steam rose like a soft ribbon.",
        tags={"milk"},
    ),
    "cocoa": Drink(
        id="cocoa",
        label="cocoa",
        phrase="a cup of cocoa",
        stir_line='The spoon went "swish, clink" as the cocoa was stirred smooth, and the sweet smell floated through the room.',
        steam="A little cloud of chocolate steam drifted up.",
        tags={"cocoa"},
    ),
    "tea": Drink(
        id="tea",
        label="herbal tea",
        phrase="a small cup of sleepy herbal tea",
        stir_line='The spoon made a tiny "ting" while the honey was stirred through the tea, slow and quiet as a lullaby.',
        steam="Steam lifted in a pale thread.",
        tags={"tea"},
    ),
}

WINDS = ["still", "breezy", "gusty"]

GIRL_NAMES = ["Lila", "Mina", "Eva", "Nora", "Tess", "Poppy"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Milo", "Finn", "Eli"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    bedtime: str
    source: str
    helper: str
    drink: str
    child_name: str
    child_gender: str
    grown_type: str
    wind: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "wind": [
        (
            "Why do things sound louder or stranger at night?",
            "At night the house is quieter, so a small sound stands out more. When you are sleepy, your imagination can make that sound seem bigger too.",
        )
    ],
    "branch": [
        (
            "Why does a branch tap on a window?",
            "When wind moves a loose branch, it can bump the glass again and again. That makes a tapping or scratching sound.",
        )
    ],
    "shade": [
        (
            "What can make a shade tap at a window?",
            "A shade cord can swing when air moves through a room. If it hits the frame, it can make a tiny ticking sound.",
        )
    ],
    "kitchen": [
        (
            "Why can a spoon ring against a mug?",
            "If a spoon is leaning inside a mug, even a small shake can make it touch the cup. That makes a light ringing sound.",
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for at night?",
            "A flashlight helps you see in the dark with a safe, steady light. It lets you check things closely without making the room scary.",
        )
    ],
    "lantern": [
        (
            "Why is a lantern cozy at bedtime?",
            "A small lantern gives a gentle glow that helps a room feel calm. Soft light can make nighttime exploring feel safer.",
        )
    ],
    "milk": [
        (
            "Why do people drink warm milk at bedtime?",
            "Warm milk feels soothing and gentle before sleep. Holding a warm cup can help your body settle down.",
        )
    ],
    "cocoa": [
        (
            "Why can stirring cocoa feel cozy?",
            "The warm smell and the little clinking spoon can feel comforting. Small bedtime routines often help children relax.",
        )
    ],
    "tea": [
        (
            "What is herbal tea?",
            "Herbal tea is a warm drink made from herbs or flowers instead of regular tea leaves. Some kinds are chosen because they taste gentle and calming.",
        )
    ],
}
KNOWLEDGE_ORDER = ["wind", "branch", "shade", "kitchen", "flashlight", "lantern", "milk", "cocoa", "tea"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    source = f["source_cfg"]
    drink = f["drink_cfg"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "stir" and "inquiry".',
        f'Write a gentle night story where a child hears "{source.sound}" and makes a soft inquiry about it, then learns the harmless cause.',
        f'Write a cozy bedtime tale with sound effects, a short flashback, a little foreshadowing, and {drink.label} being stirred before sleep.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grown = f["grown"]
    source = f["source_cfg"]
    helper = f["helper_cfg"]
    drink = f["drink_cfg"]
    bedtime = f["bedtime"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was trying to settle down for bed, and {grown.label_word}, who helped explain the night sound.",
        ),
        (
            "What happened at the beginning of the story?",
            f"{grown.label_word.capitalize()} brought {drink.phrase} while {child.id} was tucked into bed. As the room grew quiet, a strange sound began near {source.place}.",
        ),
        (
            f"What was {child.id}'s inquiry?",
            f"{child.id} softly asked what was making the sound \"{source.sound}\". The inquiry mattered because asking for help was the first step toward understanding the noise.",
        ),
        (
            "How did the story use a flashback?",
            f"{child.id} remembered another night when an ordinary sound had seemed bigger in the dark. That memory made the present worry smaller, even before the true cause was found.",
        ),
        (
            "What was making the sound?",
            f"{source.reveal}. Once they saw the real cause, the mystery shrank into something ordinary and safe.",
        ),
        (
            f"How did {grown.label_word} help?",
            f"{grown.label_word.capitalize()} used {helper.phrase} and went to look together with {child.id}. Then {grown.pronoun()} {source.fix}, which stopped the sound from troubling the room.",
        ),
        (
            "How did the story end?",
            f"It ended back in {bedtime.room}, with the room quiet again and {child.id} feeling calm enough to grow sleepy. The last image shows that the fear changed into rest.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["source_cfg"].tags)
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["drink_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A source is usable if its wind requirement is met.
usable_source(S, W) :- source(S), wind(W), not needs_wind(S).
usable_source(S, W) :- source(S), wind(W), needs_wind(S), W != still.

% A helper works if it can inspect an outdoor window source when needed.
usable_helper(H, S) :- helper(H), source(S), not outside_window(S).
usable_helper(H, S) :- helper(H), source(S), outside_window(S), works_outdoors(H).

valid(S, H, D, W) :- usable_source(S, W), usable_helper(H, S), drink(D), wind(W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.needs_wind:
            lines.append(asp.fact("needs_wind", source_id))
        if source.place == "outside the bedroom window":
            lines.append(asp.fact("outside_window", source_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        if helper.works_outdoors:
            lines.append(asp.fact("works_outdoors", helper_id))
    for drink_id in DRINKS:
        lines.append(asp.fact("drink", drink_id))
    for wind in WINDS:
        lines.append(asp.fact("wind", wind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        bedtime="bedroom",
        source="branch",
        helper="flashlight",
        drink="cocoa",
        child_name="Lila",
        child_gender="girl",
        grown_type="mother",
        wind="breezy",
    ),
    StoryParams(
        bedtime="attic_nook",
        source="shades",
        helper="lantern",
        drink="tea",
        child_name="Milo",
        child_gender="boy",
        grown_type="grandmother",
        wind="gusty",
    ),
    StoryParams(
        bedtime="bedroom",
        source="teaspoon",
        helper="flashlight",
        drink="milk",
        child_name="Nora",
        child_gender="girl",
        grown_type="father",
        wind="still",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime storyworld about a strange night sound, a soft inquiry, and a calm explanation."
    )
    ap.add_argument("--bedtime", choices=BEDTIMES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grown-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.helper and args.wind:
        source = SOURCES[args.source]
        helper = HELPERS[args.helper]
        if not valid_combo(args.source, args.helper, args.drink or next(iter(DRINKS)), args.wind):
            raise StoryError(explain_rejection(source, helper, args.wind))

    combos = [
        combo for combo in valid_combos()
        if (args.source is None or combo[0] == args.source)
        and (args.helper is None or combo[1] == args.helper)
        and (args.drink is None or combo[2] == args.drink)
        and (args.wind is None or combo[3] == args.wind)
    ]
    if not combos:
        if args.source and args.helper and args.wind:
            raise StoryError(explain_rejection(SOURCES[args.source], HELPERS[args.helper], args.wind))
        raise StoryError("(No valid combination matches the given options.)")

    source_id, helper_id, drink_id, wind = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    grown_type = args.grown_type or rng.choice(["mother", "father", "grandmother", "grandfather"])
    bedtime = args.bedtime or rng.choice(sorted(BEDTIMES))
    return StoryParams(
        bedtime=bedtime,
        source=source_id,
        helper=helper_id,
        drink=drink_id,
        child_name=child_name,
        child_gender=child_gender,
        grown_type=grown_type,
        wind=wind,
    )


def _validate_params(params: StoryParams) -> None:
    if params.bedtime not in BEDTIMES:
        raise StoryError(f"(No story: unknown bedtime setting '{params.bedtime}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.drink not in DRINKS:
        raise StoryError(f"(No story: unknown drink '{params.drink}'.)")
    if params.wind not in WINDS:
        raise StoryError(f"(No story: unknown wind '{params.wind}'.)")
    if not valid_combo(params.source, params.helper, params.drink, params.wind):
        raise StoryError(explain_rejection(SOURCES[params.source], HELPERS[params.helper], params.wind))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        BEDTIMES[params.bedtime],
        SOURCES[params.source],
        HELPERS[params.helper],
        DRINKS[params.drink],
        child_name=params.child_name,
        child_gender=params.child_gender,
        grown_type=params.grown_type,
        wind=params.wind,
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
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as err:
        print(f"ASP verify failed to run clingo: {err}")
        return 1
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "inquiry" not in sample.story.lower() or "stir" not in sample.story.lower():
            raise StoryError("smoke test story missing required seed words or story text")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"Smoke test failed: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (source, helper, drink, wind) combos:\n")
        for source_id, helper_id, drink_id, wind in combos:
            print(f"  {source_id:9} {helper_id:11} {drink_id:6} {wind}")
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
            header = f"### {p.child_name}: {p.source} with {p.helper} ({p.wind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
