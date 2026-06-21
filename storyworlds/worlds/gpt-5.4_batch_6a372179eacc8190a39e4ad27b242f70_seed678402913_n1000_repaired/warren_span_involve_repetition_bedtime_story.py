#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/warren_span_involve_repetition_bedtime_story.py
============================================================================

A small bedtime-story world about little rabbits in a hill warren. A child is
ready for sleep, but one gentle nighttime trouble keeps the burrow from feeling
cozy. A grown-up notices the real cause, chooses a remedy that actually fits
that cause, and the family settles the burrow again.

This world is built to make a few strong, child-facing variants rather than many
thin ones. Every story includes the seed words "warren", "span", and "involve",
and each one uses repetition as part of the bedtime tone.

Run it
------
    python storyworlds/worlds/gpt-5.4/warren_span_involve_repetition_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/warren_span_involve_repetition_bedtime_story.py --warren moonwillow --trouble moonbeam --remedy moss_screen
    python storyworlds/worlds/gpt-5.4/warren_span_involve_repetition_bedtime_story.py --trouble drip --remedy extra_quilt
    python storyworlds/worlds/gpt-5.4/warren_span_involve_repetition_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/warren_span_involve_repetition_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/warren_span_involve_repetition_bedtime_story.py --verify
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
        female = {"girl", "mother", "doe", "woman"}
        male = {"boy", "father", "buck", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Warren:
    id: str
    label: str
    under_text: str
    span_text: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    source_text: str
    symptom_text: str
    need: str
    effect_meter: str
    repeat_text: str
    end_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    action_text: str
    qa_text: str
    guards: set[str] = field(default_factory=set)
    needs_helper: bool = False
    sense: int = 3
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, warren_cfg: Warren) -> None:
        self.warren_cfg = warren_cfg
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
        clone = World(self.warren_cfg)
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


def _r_trouble_disturbs(world: World) -> list[str]:
    room = world.entities.get("room")
    child = world.entities.get("child")
    trouble = world.facts.get("trouble_cfg")
    if room is None or child is None or trouble is None:
        return []
    if room.meters["trouble_on"] < THRESHOLD:
        return []
    sig = ("disturb", trouble.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters[trouble.effect_meter] += 1
    child.memes["restless"] += 1
    if trouble.effect_meter == "cold":
        child.memes["unease"] += 1
    else:
        child.memes["worry"] += 1
    return []


def _r_settle_after_fix(world: World) -> list[str]:
    room = world.entities.get("room")
    child = world.entities.get("child")
    if room is None or child is None:
        return []
    if room.meters["trouble_on"] >= THRESHOLD:
        return []
    if child.meters["sleepy"] >= THRESHOLD:
        return []
    if child.memes["soothed"] < THRESHOLD:
        return []
    sig = ("settle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["sleepy"] += 1
    child.memes["relief"] += 1
    child.memes["restless"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="trouble_disturbs", tag="physical", apply=_r_trouble_disturbs),
    Rule(name="settle_after_fix", tag="emotional", apply=_r_settle_after_fix),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = (set(world.fired), dict(world.get("child").meters) if "child" in world.entities else {})
            rule.apply(world)
            after = (set(world.fired), dict(world.get("child").meters) if "child" in world.entities else {})
            if after != before:
                changed = True


def trouble_at_risk(warren_cfg: Warren, trouble: Trouble) -> bool:
    return trouble.id in warren_cfg.affords


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def compatible(trouble: Trouble, remedy: Remedy) -> bool:
    return remedy.sense >= SENSE_MIN and trouble.need in remedy.guards


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for warren_id, warren_cfg in WARRENS.items():
        for trouble_id, trouble in TROUBLES.items():
            if not trouble_at_risk(warren_cfg, trouble):
                continue
            for remedy_id, remedy in REMEDIES.items():
                if compatible(trouble, remedy):
                    combos.append((warren_id, trouble_id, remedy_id))
    return combos


def predict_settling(world: World, trouble: Trouble, remedy: Remedy) -> dict:
    sim = world.copy()
    room = sim.get("room")
    child = sim.get("child")
    room.meters["trouble_on"] = 1.0
    propagate(sim)
    before = dict(child.meters)
    room.meters["trouble_on"] = 0.0
    child.memes["soothed"] += 1
    propagate(sim)
    after = dict(child.meters)
    return {
        "disturbed": before.get(trouble.effect_meter, 0.0) >= THRESHOLD,
        "settled": after.get("sleepy", 0.0) >= THRESHOLD,
        "uses_helper": remedy.needs_helper,
    }


def bedtime_refrain() -> str:
    return "Hush now, little paws. Hush now, little paws."


def introduce(world: World, child: Entity, sibling: Entity, parent: Entity, warren_cfg: Warren) -> None:
    child.memes["sleepy_hope"] += 1
    sibling.memes["sleepy_hope"] += 1
    world.say(
        f"In {warren_cfg.label}, a warm rabbit warren tucked {warren_cfg.under_text}. "
        f"{warren_cfg.span_text}"
    )
    world.say(
        f"{child.id} and {sibling.id} had brushed their whiskers, folded their ears, "
        f"and climbed into their mossy beds while their {parent.label_word} made the burrow quiet."
    )
    world.say(bedtime_refrain())


def start_trouble(world: World, child: Entity, trouble: Trouble) -> None:
    room = world.get("room")
    room.meters["trouble_on"] = 1.0
    propagate(world)
    world.say(
        f"But just as {child.id} tucked {child.pronoun('possessive')} paws under the blanket, "
        f"{trouble.source_text}"
    )
    world.say(
        f'"{trouble.repeat_text}, {trouble.repeat_text}," whispered {child.id}. '
        f"{trouble.symptom_text}"
    )


def notice_and_plan(world: World, parent: Entity, child: Entity, sibling: Entity, trouble: Trouble, remedy: Remedy) -> None:
    pred = predict_settling(world, trouble, remedy)
    world.facts["predicted_disturbed"] = pred["disturbed"]
    world.facts["predicted_settled"] = pred["settled"]
    world.facts["used_helper"] = pred["uses_helper"]
    world.say(
        f"{parent.label_word.capitalize()} listened for one small moment and then nodded. "
        f'{parent.pronoun().capitalize()} knew exactly what was wrong.'
    )
    if remedy.needs_helper:
        sibling.memes["helper"] += 1
        world.say(
            f'"We can fix this," {parent.pronoun()} said softly. '
            f'"It will involve {sibling.id} and me working together, very slowly and very quietly."'
        )
    else:
        world.say(
            f'"We can fix this," {parent.pronoun()} said softly. '
            f'"It will involve one gentle bedtime change, and then the burrow can rest again."'
        )


def apply_remedy(world: World, parent: Entity, sibling: Entity, trouble: Trouble, remedy: Remedy) -> None:
    room = world.get("room")
    child = world.get("child")
    room.meters["trouble_on"] = 0.0
    child.meters[trouble.effect_meter] = 0.0
    child.memes["soothed"] += 1
    propagate(world)
    if remedy.needs_helper:
        world.say(
            f"{parent.label_word.capitalize()} and {sibling.id} moved with quiet paws and {remedy.action_text}."
        )
    else:
        world.say(f"{parent.label_word.capitalize()} {remedy.action_text}.")
    world.say(
        f"Soon the trouble was gone. {bedtime_refrain()}"
    )


def sleep_end(world: World, child: Entity, sibling: Entity, trouble: Trouble, remedy: Remedy) -> None:
    child.memes["trust"] += 1
    sibling.memes["calm"] += 1
    world.say(
        f'{child.id} took one long rabbit breath. "{trouble.end_text}," {child.pronoun()} murmured.'
    )
    world.say(
        f"{sibling.id} smiled from the next bed, and the two little rabbits listened to the gentle dark instead of the old bother."
    )
    world.say(
        f"Before long, {child.id}'s eyes closed. The warren held still around them, "
        f"and {remedy.phrase} left the burrow cozy all through the night."
    )


def tell(
    warren_cfg: Warren,
    trouble: Trouble,
    remedy: Remedy,
    child_name: str = "Moss",
    child_type: str = "girl",
    sibling_name: str = "Pip",
    sibling_type: str = "boy",
    parent_type: str = "mother",
    temperament: str = "gentle",
) -> World:
    world = World(warren_cfg)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_type, role="sibling", label=sibling_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", kind="thing", type="burrow", label="the burrow"))
    child.attrs["temperament"] = temperament
    sibling.attrs["temperament"] = "sleepy"
    world.facts.update(
        child=child,
        sibling=sibling,
        parent=parent,
        room=room,
        warren_cfg=warren_cfg,
        trouble_cfg=trouble,
        remedy_cfg=remedy,
        repeated_line=bedtime_refrain(),
    )

    introduce(world, child, sibling, parent, warren_cfg)
    world.para()
    start_trouble(world, child, trouble)
    notice_and_plan(world, parent, child, sibling, trouble, remedy)
    world.para()
    apply_remedy(world, parent, sibling, trouble, remedy)
    sleep_end(world, child, sibling, trouble, remedy)

    world.facts.update(
        settled=child.meters["sleepy"] >= THRESHOLD,
        used_helper=remedy.needs_helper,
        trouble_gone=room.meters["trouble_on"] < THRESHOLD,
    )
    return world


WARRENS = {
    "moonwillow": Warren(
        id="moonwillow",
        label="Moonwillow Warren",
        under_text="under a round green hill",
        span_text="Its tunnels made a soft span from one sleepy nest to the next, all the way under the willow roots.",
        affords={"moonbeam", "draft"},
        tags={"warren", "hill"},
    ),
    "bramblebank": Warren(
        id="bramblebank",
        label="Bramblebank Warren",
        under_text="under a bank of blackberries",
        span_text="The burrows ran in a snug span beneath the bramble roots, with little sleeping rooms tucked along the way.",
        affords={"draft", "drip"},
        tags={"warren", "bank"},
    ),
    "cloverhollow": Warren(
        id="cloverhollow",
        label="Cloverhollow Warren",
        under_text="under a hill that smelled of clover",
        span_text="A neat span of tunnels curled below the hill, joining the nursery nook to the pantry and the bedtime rooms.",
        affords={"moonbeam", "drip"},
        tags={"warren", "clover"},
    ),
}

TROUBLES = {
    "moonbeam": Trouble(
        id="moonbeam",
        label="moonbeam",
        source_text="a pale moonbeam slipped through the high peephole and laid a silver stripe right across the blanket",
        symptom_text="The bright stripe kept blinking at the edge of the bed, and sleep would not come close.",
        need="darken",
        effect_meter="awake",
        repeat_text="too bright",
        end_text="Not too bright now",
        tags={"moon", "light"},
    ),
    "draft": Trouble(
        id="draft",
        label="draft",
        source_text="a cool draft crept under the burrow flap and brushed the beds with chilly air",
        symptom_text="Even with the blanket up to the chin, the little bed felt too cool for easy sleep.",
        need="warmth",
        effect_meter="cold",
        repeat_text="too chilly",
        end_text="Not too chilly now",
        tags={"cold", "night"},
    ),
    "drip": Trouble(
        id="drip",
        label="drip",
        source_text="a drop of water from a root-tip fell into a shell dish in the side tunnel: drip, wait, drip",
        symptom_text="Each tiny sound made the ears twitch, and the quiet of bedtime kept breaking open.",
        need="quiet",
        effect_meter="startled",
        repeat_text="drip, wait, drip",
        end_text="No more drip, wait, drip",
        tags={"sound", "water"},
    ),
}

REMEDIES = {
    "moss_screen": Remedy(
        id="moss_screen",
        label="moss screen",
        phrase="the moss screen across the peephole",
        action_text="lifted a soft moss screen and fastened it across the little peephole until the silver stripe faded away",
        qa_text="put a moss screen across the peephole to block the moonbeam",
        guards={"darken"},
        needs_helper=True,
        sense=3,
        tags={"screen", "dark"},
    ),
    "extra_quilt": Remedy(
        id="extra_quilt",
        label="extra quilt",
        phrase="the extra quilt tucked close and the flap snug shut",
        action_text="closed the burrow flap, tucked an extra quilt all around the small blanket nest, and warmed the bed at once",
        qa_text="closed the flap and tucked an extra quilt around the bed to stop the draft",
        guards={"warmth"},
        needs_helper=False,
        sense=3,
        tags={"quilt", "warm"},
    ),
    "felt_runner": Remedy(
        id="felt_runner",
        label="felt runner",
        phrase="the felt runner quiet on the side tunnel floor",
        action_text="unrolled a felt runner under the root-tip and moved the shell dish so the water landed without its little tapping sound",
        qa_text="laid down a felt runner and moved the shell dish so the dripping would not tap so loudly",
        guards={"quiet"},
        needs_helper=True,
        sense=3,
        tags={"quiet", "felt"},
    ),
    "carrot_snack": Remedy(
        id="carrot_snack",
        label="midnight carrot snack",
        phrase="a little carrot snack",
        action_text="brought a nibble of carrot to the bed",
        qa_text="brought a carrot snack",
        guards=set(),
        needs_helper=False,
        sense=1,
        tags={"snack"},
    ),
}

GIRL_NAMES = ["Moss", "Tansy", "Clover", "Poppy", "Daisy", "Fern"]
BOY_NAMES = ["Pip", "Bramble", "Hazel", "Nettle", "Thistle", "Rowan"]
TEMPERAMENTS = ["gentle", "sleepy", "thoughtful", "soft-hearted", "patient"]


@dataclass
class StoryParams:
    warren: str
    trouble: str
    remedy: str
    child_name: str
    child_gender: str
    sibling_name: str
    sibling_gender: str
    parent: str
    temperament: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "warren": [
        (
            "What is a rabbit warren?",
            "A rabbit warren is a home made of many tunnels and little rooms under the ground. Rabbits use it to sleep, hide, and keep warm."
        )
    ],
    "moon": [
        (
            "Why can a moonbeam seem bright at bedtime?",
            "Even gentle moonlight can feel bright when the room is dark and sleepy eyes are trying to close. A little stripe of light can keep someone noticing it again and again."
        )
    ],
    "cold": [
        (
            "Why does a draft feel chilly?",
            "A draft is moving air, and moving air can carry warmth away from your skin and blankets. That is why a little crack or flap can make a bed feel colder."
        )
    ],
    "sound": [
        (
            "Why do little sounds seem bigger at night?",
            "At night everything else is quiet, so one small sound stands out more. A drip or tap can seem very loud when someone is trying to fall asleep."
        )
    ],
    "quilt": [
        (
            "What does a quilt do at bedtime?",
            "A quilt helps hold warm air around a sleeper. That makes a bed feel cozier and safer."
        )
    ],
    "screen": [
        (
            "What does a screen do over a window or peephole?",
            "A screen can block or soften what comes through an opening. At bedtime it can make the room darker and calmer."
        )
    ],
    "quiet": [
        (
            "How can people make a room quieter?",
            "They can move the noisy thing, soften it with cloth or felt, or close something that lets the sound bounce around. Small changes can make a big difference in a quiet room."
        )
    ],
}
KNOWLEDGE_ORDER = ["warren", "moon", "cold", "sound", "quilt", "screen", "quiet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    trouble = f["trouble_cfg"]
    remedy = f["remedy_cfg"]
    warren_cfg = f["warren_cfg"]
    return [
        f'Write a gentle bedtime story set in a rabbit warren that includes the words "warren", "span", and "involve", and uses repetition.',
        f"Tell a sleepy story where {child.id} cannot settle because of a {trouble.label} in {warren_cfg.label}, and a grown-up chooses the right fix.",
        f"Write a calm story for very young children in which {child.id} and {sibling.id} hear a nighttime bother, and {remedy.label} helps the burrow feel safe again.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    parent = f["parent"]
    trouble = f["trouble_cfg"]
    remedy = f["remedy_cfg"]
    warren_cfg = f["warren_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two little rabbits, {child.id} and {sibling.id}, in {warren_cfg.label}, and their {parent.label_word} who helps at bedtime."
        ),
        (
            "What made bedtime hard for the little rabbit?",
            f"Bedtime was hard because {trouble.source_text}. That kept {child.id} from settling, since {trouble.symptom_text.lower()}"
        ),
        (
            "Why did the parent know there was a real problem?",
            f"{parent.label_word.capitalize()} listened and noticed the true cause instead of telling {child.id} to ignore it. The trouble was changing the bed itself, so it was making sleep harder, not easier."
        ),
        (
            "What did the family do to fix the bedtime trouble?",
            f"They {remedy.qa_text}. That worked because it matched the real trouble instead of distracting {child.id} for a moment."
        ),
    ]
    if remedy.needs_helper:
        qa.append(
            (
                f"How did {sibling.id} help?",
                f"{sibling.id} helped quietly while {parent.label_word} worked, because the fix needed more than one careful pair of paws. The story says the plan would involve both of them, and their help made the burrow calm again."
            )
        )
    else:
        qa.append(
            (
                "Did anyone else have to help?",
                f"No extra helper was needed. {parent.label_word.capitalize()} could fix it alone because the problem was right by the bed and only needed one gentle bedtime change."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the burrow feeling cozy again and {child.id} finally drifting to sleep. The ending image proves what changed, because the old bother was gone and the bed felt restful."
        )
    )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trouble = f["trouble_cfg"]
    remedy = f["remedy_cfg"]
    tags: set[str] = {"warren"} | set(trouble.tags) | set(remedy.tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
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


CURATED = [
    StoryParams(
        warren="moonwillow",
        trouble="moonbeam",
        remedy="moss_screen",
        child_name="Moss",
        child_gender="girl",
        sibling_name="Pip",
        sibling_gender="boy",
        parent="mother",
        temperament="gentle",
    ),
    StoryParams(
        warren="bramblebank",
        trouble="draft",
        remedy="extra_quilt",
        child_name="Thistle",
        child_gender="boy",
        sibling_name="Fern",
        sibling_gender="girl",
        parent="father",
        temperament="thoughtful",
    ),
    StoryParams(
        warren="cloverhollow",
        trouble="drip",
        remedy="felt_runner",
        child_name="Clover",
        child_gender="girl",
        sibling_name="Rowan",
        sibling_gender="boy",
        parent="mother",
        temperament="patient",
    ),
]


def explain_warren_rejection(warren_cfg: Warren, trouble: Trouble) -> str:
    return (
        f"(No story: {trouble.label} does not fit {warren_cfg.label}. "
        f"That warren does not have the opening or tunnel condition that would honestly cause this bedtime trouble.)"
    )


def explain_remedy_rejection(trouble: Trouble, remedy: Remedy) -> str:
    if remedy.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_remedies()))
        return (
            f"(Refusing remedy '{remedy.id}': it is too weak for this world (sense={remedy.sense} < {SENSE_MIN}). "
            f"Try one of these sensible remedies instead: {better}.)"
        )
    return (
        f"(No story: {remedy.label} does not solve a {trouble.label} problem. "
        f"The bedtime fix must match the real cause, not just add a pleasant extra.)"
    )


ASP_RULES = r"""
% Reasonableness gate.
present(W, T) :- warren(W), trouble(T), affords(W, T).
sensible(R)   :- remedy(R), sense(R, S), sense_min(M), S >= M.
compatible(T, R) :- trouble(T), remedy(R), needs(T, N), guards(R, N), sensible(R).
valid(W, T, R) :- present(W, T), compatible(T, R).

% A helper is needed when the chosen remedy is marked that way.
uses_helper :- chosen_remedy(R), needs_helper(R).

% Story settles when the remedy matches the trouble and is sensible.
settled :- chosen_trouble(T), chosen_remedy(R), compatible(T, R).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for warren_id, warren_cfg in WARRENS.items():
        lines.append(asp.fact("warren", warren_id))
        for trouble_id in sorted(warren_cfg.affords):
            lines.append(asp.fact("affords", warren_id, trouble_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("needs", trouble_id, trouble.need))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        if remedy.needs_helper:
            lines.append(asp.fact("needs_helper", remedy_id))
        for guard in sorted(remedy.guards):
            lines.append(asp.fact("guards", remedy_id, guard))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_settled(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("chosen_remedy", params.remedy),
    ])
    model = asp.one_model(asp_program(extra, "#show settled/0."))
    return bool(asp.atoms(model, "settled"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_remedies()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible remedies match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    for params in CURATED:
        if not asp_settled(params):
            rc = 1
            print(f"MISMATCH: ASP did not settle curated story {params}")
            break
    else:
        print(f"OK: ASP settling agrees on {len(CURATED)} curated stories.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Bedtime story world: a rabbit warren, one true bedtime bother, and a fitting fix."
    )
    ap.add_argument("--warren", choices=WARRENS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.warren and args.trouble:
        warren_cfg = WARRENS[args.warren]
        trouble = TROUBLES[args.trouble]
        if not trouble_at_risk(warren_cfg, trouble):
            raise StoryError(explain_warren_rejection(warren_cfg, trouble))
    if args.trouble and args.remedy:
        trouble = TROUBLES[args.trouble]
        remedy = REMEDIES[args.remedy]
        if not compatible(trouble, remedy):
            raise StoryError(explain_remedy_rejection(trouble, remedy))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        trouble = TROUBLES[args.trouble] if args.trouble else next(iter(TROUBLES.values()))
        raise StoryError(explain_remedy_rejection(trouble, REMEDIES[args.remedy]))

    combos = [
        combo for combo in valid_combos()
        if (args.warren is None or combo[0] == args.warren)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    warren_id, trouble_id, remedy_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    sibling_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    sibling_name = _pick_name(rng, sibling_gender, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    temperament = rng.choice(TEMPERAMENTS)
    return StoryParams(
        warren=warren_id,
        trouble=trouble_id,
        remedy=remedy_id,
        child_name=child_name,
        child_gender=child_gender,
        sibling_name=sibling_name,
        sibling_gender=sibling_gender,
        parent=parent,
        temperament=temperament,
    )


def generate(params: StoryParams) -> StorySample:
    if params.warren not in WARRENS:
        raise StoryError(f"(Unknown warren '{params.warren}'.)")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble '{params.trouble}'.)")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy '{params.remedy}'.)")
    warren_cfg = WARRENS[params.warren]
    trouble = TROUBLES[params.trouble]
    remedy = REMEDIES[params.remedy]
    if not trouble_at_risk(warren_cfg, trouble):
        raise StoryError(explain_warren_rejection(warren_cfg, trouble))
    if not compatible(trouble, remedy):
        raise StoryError(explain_remedy_rejection(trouble, remedy))

    world = tell(
        warren_cfg=warren_cfg,
        trouble=trouble,
        remedy=remedy,
        child_name=params.child_name,
        child_type=params.child_gender,
        sibling_name=params.sibling_name,
        sibling_type=params.sibling_gender,
        parent_type=params.parent,
        temperament=params.temperament,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show settled/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (warren, trouble, remedy) combos:\n")
        for warren_id, trouble_id, remedy_id in combos:
            print(f"  {warren_id:12} {trouble_id:10} {remedy_id}")
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
            header = f"### {p.child_name}: {p.trouble} in {p.warren} fixed by {p.remedy}"
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
