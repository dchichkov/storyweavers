#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/individual_curiosity_slice_of_life.py
================================================================

A standalone storyworld about a child's curiosity in an ordinary day. The world
models one small, observable thing in a familiar place -- an individual snail,
ant, seedling, or spider web -- and a child who wants to look more closely
without spoiling what made it interesting.

The core constraint is simple: the chosen focus item must actually fit the
setting, and the chosen way of learning must make sense for that kind of thing.
A magnifying glass or sketchbook is gentle and reasonable for tiny outdoor
details; tugging at a spider web or flooding an ant trail is not. The world
knows about some poor ideas so it can refuse them with clear explanations.

The generated stories are slice-of-life tales with a small tension:
curiosity pulls the child closer, impatience risks disturbing the scene, and a
calm helper turns that energy into careful watching. The ending image proves the
change: the child still gets to learn, but in a gentler way.

Run it
------
    python storyworlds/worlds/gpt-5.4/individual_curiosity_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/individual_curiosity_slice_of_life.py --setting garden --focus snail
    python storyworlds/worlds/gpt-5.4/individual_curiosity_slice_of_life.py --focus web --approach tug
    python storyworlds/worlds/gpt-5.4/individual_curiosity_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/individual_curiosity_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/individual_curiosity_slice_of_life.py --json
    python storyworlds/worlds/gpt-5.4/individual_curiosity_slice_of_life.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
    indoor: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Focus:
    id: str
    label: str
    phrase: str
    kind: str
    where_text: str
    motion_text: str
    detail_text: str
    reason_to_wait: str
    upset_text: str
    plural: bool = False
    living: bool = False
    fragile: bool = False
    habitat: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    label: str
    sense: int
    gentle: bool
    power: int
    works_for: set[str] = field(default_factory=set)
    text: str = ""
    closing: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_disturb(world: World) -> list[str]:
    out: list[str] = []
    focus = world.get("focus")
    child = world.get("child")
    if focus.meters["disturbed"] < THRESHOLD:
        return out
    sig = ("disturb", focus.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["curiosity"] -= 0.5
    if focus.attrs.get("living"):
        out.append("__living_disturb__")
    else:
        out.append("__fragile_disturb__")
    return out


def _r_gentle_learning(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    focus = world.get("focus")
    helper = world.get("helper")
    if child.meters["observed"] < THRESHOLD or focus.meters["seen_clearly"] < THRESHOLD:
        return out
    sig = ("learn", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["understanding"] += 1
    child.memes["calm"] += 1
    helper.memes["pride"] += 1
    out.append("__learned__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="disturb", tag="social", apply=_r_disturb),
    Rule(name="gentle_learning", tag="knowledge", apply=_r_gentle_learning),
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


def focus_fits(setting: Setting, focus: Focus) -> bool:
    return focus.id in setting.affords and setting.id in focus.habitat


def approach_works(focus: Focus, approach: Approach) -> bool:
    return focus.kind in approach.works_for


def sensible_approaches() -> list[Approach]:
    return [a for a in APPROACHES.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for fid, focus in FOCI.items():
            if not focus_fits(setting, focus):
                continue
            for aid, approach in APPROACHES.items():
                if approach.sense >= SENSE_MIN and approach_works(focus, approach):
                    combos.append((sid, fid, aid))
    return combos


def explain_focus_rejection(setting: Setting, focus: Focus) -> str:
    return (
        f"(No story: {focus.phrase} does not belong in {setting.place} here. "
        f"Pick a focus item that a child could honestly notice in that setting.)"
    )


def explain_approach_rejection(focus: Focus, approach: Approach) -> str:
    if approach.sense < SENSE_MIN:
        return (
            f"(Refusing approach '{approach.id}': it scores too low on common sense "
            f"(sense={approach.sense} < {SENSE_MIN}). A curiosity story should protect "
            f"the interesting thing instead of spoiling it.)"
        )
    return (
        f"(No story: {approach.label} is not a good way to learn about {focus.phrase}. "
        f"Choose a gentler approach that fits what the child is watching.)"
    )


def predict_disturbance(world: World, focus: Focus, poke_level: int) -> dict:
    sim = world.copy()
    focus_ent = sim.get("focus")
    child = sim.get("child")
    focus_ent.meters["disturbed"] += float(poke_level)
    child.memes["impatience"] += float(poke_level)
    propagate(sim, narrate=False)
    return {
        "disturbed": focus_ent.meters["disturbed"] >= THRESHOLD,
        "worry": child.memes["worry"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(
        f"{child.id} was a little {trait} {child.type} who liked to stop for small things "
        f"other people hurried past."
    )
    world.say(
        f"That afternoon, {child.pronoun('possessive')} {helper.label_word} was nearby, "
        f"folding towels and keeping half an eye on the day."
    )


def arrive(world: World, child: Entity, focus: Focus) -> None:
    world.say(
        f"They were in {world.setting.place}, where {world.setting.detail}."
    )
    world.say(
        f"Near {focus.where_text}, {child.id} noticed {focus.phrase}. {focus.motion_text}"
    )


def notice(world: World, child: Entity, focus: Focus) -> None:
    child.memes["curiosity"] += 1
    world.get("focus").meters["noticed"] += 1
    world.say(
        f"{child.pronoun().capitalize()} crouched lower. It was only one small thing, "
        f"an individual {focus.label}, but it felt worth a whole minute of looking."
    )
    world.say(
        f'"What is it doing?" {child.pronoun()} whispered.'
    )


def reach_too_fast(world: World, child: Entity, focus: Focus, poke_level: int) -> None:
    child.memes["impatience"] += 1
    pred = predict_disturbance(world, focus, poke_level)
    world.facts["predicted_disturb"] = pred["disturbed"]
    if focus.living:
        line = f"{child.id} put out one finger, wanting to make {focus.label} move faster."
    else:
        line = f"{child.id} reached toward it, wanting to touch the delicate part before it changed."
    world.say(line)
    if pred["disturbed"]:
        world.say(
            f"{child.pronoun('possessive').capitalize()} {world.get('helper').label_word} saw at once that {focus.reason_to_wait}."
        )


def guide(world: World, helper: Entity, child: Entity, focus: Focus, approach: Approach) -> None:
    child.memes["listening"] += 1
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} touched {child.pronoun("possessive")} shoulder and said, '
        f'"Let\'s be gentle. {approach.text}"'
    )
    world.say(
        f"{child.id} pulled {child.pronoun('possessive')} hand back and looked again instead of grabbing."
    )


def do_approach(world: World, child: Entity, focus: Focus, approach: Approach) -> None:
    child.meters["observed"] += 1
    world.get("focus").meters["seen_clearly"] += 1
    child.memes["curiosity"] += 0.5
    world.say(approach.closing)
    world.say(focus.detail_text)
    propagate(world, narrate=False)


def disturbed_turn(world: World, focus: Focus) -> None:
    focus_ent = world.get("focus")
    focus_ent.meters["disturbed"] += 1
    propagate(world, narrate=False)
    if focus.living:
        world.say(
            f"At the first quick touch, {focus.upset_text}. The tiny surprise in the scene was gone just that fast."
        )
    else:
        world.say(
            f"At the first quick touch, {focus.upset_text}. The lovely shape would not sit quite the same again."
        )


def soothe_and_retry(world: World, helper: Entity, child: Entity, focus: Focus, approach: Approach) -> None:
    child.memes["calm"] += 1
    world.say(
        f'{helper.label_word.capitalize()} was not cross. "{focus.reason_to_wait.capitalize()}," '
        f'{helper.pronoun()} said softly. "We can still learn if we slow down."'
    )
    do_approach(world, child, focus, approach)


def ending(world: World, child: Entity, helper: Entity, focus: Focus, approach: Approach) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"After that, {child.id} stayed very still. {child.pronoun().capitalize()} watched until the little scene made sense."
    )
    if approach.id == "sketchbook":
        world.say(
            f"When they went back inside, {child.pronoun()} drew {focus.phrase} from memory, one careful line at a time."
        )
    elif approach.id == "magnifier":
        world.say(
            f"Before the light changed, {child.pronoun()} took one last look through the magnifying glass and smiled."
        )
    elif approach.id == "quiet_wait":
        world.say(
            f"A minute later, the ordinary corner of {world.setting.place} did not feel ordinary at all."
        )
    else:
        world.say(
            f"By the time {helper.label_word} called for a snack, {child.id} had learned more by being quiet than by rushing."
        )
    world.say(
        f"All evening, {child.pronoun()} kept talking about that individual {focus.label} and how much there was to notice when {child.pronoun()} looked gently."
    )


def tell(
    setting: Setting,
    focus: Focus,
    approach: Approach,
    *,
    child_name: str = "Lina",
    child_type: str = "girl",
    helper_type: str = "mother",
    child_trait: str = "curious",
    poke_level: int = 1,
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=["little", child_trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    focus_ent = world.add(Entity(
        id="focus",
        kind="thing",
        type=focus.kind,
        label=focus.label,
        phrase=focus.phrase,
        attrs={"living": focus.living, "fragile": focus.fragile},
        tags=set(focus.tags),
    ))

    introduce(world, child, helper)
    arrive(world, child, focus)
    world.para()
    notice(world, child, focus)
    reach_too_fast(world, child, focus, poke_level)
    world.para()

    if poke_level >= 2:
        disturbed_turn(world, focus)
        soothe_and_retry(world, helper, child, focus, approach)
    else:
        guide(world, helper, child, focus, approach)
        do_approach(world, child, focus, approach)

    world.para()
    ending(world, child, helper, focus, approach)

    world.facts.update(
        child=child,
        helper=helper,
        focus_cfg=focus,
        focus=focus_ent,
        approach=approach,
        setting=setting,
        poke_level=poke_level,
        disturbed=focus_ent.meters["disturbed"] >= THRESHOLD,
        learned=child.memes["understanding"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden behind the building",
        detail="the mint leaves leaned over the bricks and the watering can was still dripping",
        affords={"snail", "ant", "seedling"},
        indoor=False,
        tags={"garden"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        detail="the steps held a little warmth from the sun and one flowerpot shadow touched the railing",
        affords={"ant", "web"},
        indoor=False,
        tags={"porch"},
    ),
    "windowsill": Setting(
        id="windowsill",
        place="the kitchen windowsill",
        detail="a jar of wooden spoons stood nearby and the late light made a gold square on the paint",
        affords={"seedling", "web"},
        indoor=True,
        tags={"window"},
    ),
}

FOCI = {
    "snail": Focus(
        id="snail",
        label="snail",
        phrase="a small snail with a clean brown shell",
        kind="creature",
        where_text="the edge of a damp flowerpot",
        motion_text="Its horns were out, and it was sliding along so slowly that watching it made the whole afternoon slow down too.",
        detail_text="Through the careful look, they could see the shell's soft swirl and the shining trail left behind on the pot.",
        reason_to_wait="if you poke a snail, it pulls into its shell and stops showing you anything",
        upset_text="the snail tucked itself away inside its shell",
        living=True,
        fragile=False,
        habitat={"garden"},
        tags={"snail", "garden"},
    ),
    "ant": Focus(
        id="ant",
        label="ant",
        phrase="an ant carrying a crumb bigger than its head",
        kind="creature",
        where_text="a crack between two porch boards",
        motion_text="It hurried in a straight little path, then wobbled, then found its balance again without dropping the crumb.",
        detail_text="Once they waited instead of crowding it, they saw the ant feel the boards with its tiny front legs and tug the crumb through the narrow crack.",
        reason_to_wait="if you splash or block an ant trail, the ant loses its path",
        upset_text="the ant darted away under the wood and took the crumb with it",
        living=True,
        fragile=False,
        habitat={"garden", "porch"},
        tags={"ant"},
    ),
    "seedling": Focus(
        id="seedling",
        label="seedling",
        phrase="a green seedling bent in a yogurt cup",
        kind="plant",
        where_text="the little row of cups by the light",
        motion_text="Its two leaves were open like tiny hands, and a pale stem leaned toward the window.",
        detail_text="Looking carefully, they could see the seed coat still resting near the dirt and the thin stem turning toward the bright part of the glass.",
        reason_to_wait="if you keep digging around a seedling, you can break the tiny roots that are trying to grow",
        upset_text="the dirt shifted and the seedling leaned over sadly",
        living=False,
        fragile=True,
        habitat={"garden", "windowsill"},
        tags={"seed", "plant"},
    ),
    "web": Focus(
        id="web",
        label="web",
        phrase="a spider web holding three bright drops of water",
        kind="fragile_thing",
        where_text="the corner where the railing met the wall",
        motion_text="The web only showed itself when the light hit it, and then every thread looked silver for a second.",
        detail_text="When they looked from the side, they could see how each thread met the next in neat little lines, with the drops hanging like beads.",
        reason_to_wait="if you tug a web, the pattern tears and you cannot see how it was made",
        upset_text="one thread snapped and the shining drops slid away",
        living=False,
        fragile=True,
        habitat={"porch", "windowsill"},
        tags={"web", "spider"},
    ),
}

APPROACHES = {
    "magnifier": Approach(
        id="magnifier",
        label="a magnifying glass",
        sense=3,
        gentle=True,
        power=2,
        works_for={"creature", "plant", "fragile_thing"},
        text="We can use a magnifying glass and let it stay right where it is.",
        closing="Helper fetched a magnifying glass from the hallway drawer, and together they held it steady above the tiny thing without touching.",
        qa_text="used a magnifying glass and looked without touching",
        tags={"magnifier"},
    ),
    "sketchbook": Approach(
        id="sketchbook",
        label="a sketchbook",
        sense=3,
        gentle=True,
        power=2,
        works_for={"creature", "plant", "fragile_thing"},
        text="Let's watch first and make a little sketch of what we see.",
        closing="Helper opened the back of an old receipt envelope for notes, and Child traced the shape with a finger in the air before drawing it carefully.",
        qa_text="watched quietly and made a sketch",
        tags={"drawing"},
    ),
    "quiet_wait": Approach(
        id="quiet_wait",
        label="quiet waiting",
        sense=2,
        gentle=True,
        power=1,
        works_for={"creature", "plant", "fragile_thing"},
        text="Sometimes the best way to learn is to wait and let it go on being itself.",
        closing="So they simply stayed still, shoulder to shoulder, and let another minute pass.",
        qa_text="waited quietly and watched what happened next",
        tags={"patience"},
    ),
    "tug": Approach(
        id="tug",
        label="pulling or tugging at it",
        sense=1,
        gentle=False,
        power=0,
        works_for={"fragile_thing"},
        text="",
        closing="",
        qa_text="",
        tags={"harm"},
    ),
    "splash": Approach(
        id="splash",
        label="splashing water to make it move",
        sense=1,
        gentle=False,
        power=0,
        works_for={"creature"},
        text="",
        closing="",
        qa_text="",
        tags={"harm"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ivy", "Ella", "Zoe", "Lucy", "Anna"]
BOY_NAMES = ["Owen", "Noah", "Ben", "Milo", "Theo", "Eli", "Sam", "Finn"]
TRAITS = ["curious", "careful", "quiet", "thoughtful", "patient", "gentle"]


@dataclass
class StoryParams:
    setting: str
    focus: str
    approach: str
    child_name: str
    child_type: str
    helper_type: str
    child_trait: str
    poke_level: int = 1
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    focus = f["focus_cfg"]
    approach = f["approach"]
    setting = f["setting"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "individual" and centers on curiosity.',
        f"Tell a gentle story where a little {child.type} named {child.id} notices {focus.phrase} in {setting.place} and almost rushes, but a grown-up helps {child.pronoun('object')} look carefully instead.",
        f"Write a quiet everyday story about learning through {approach.label}, with a calm ending image that shows the child still thinking about one individual {focus.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    focus = f["focus_cfg"]
    approach = f["approach"]
    setting = f["setting"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little {child.type} named {child.id} and {child.pronoun('possessive')} {helper_word}. "
            f"They are together in {setting.place} when {child.id} notices something small and interesting."
        ),
        (
            f"What did {child.id} notice?",
            f"{child.id} noticed {focus.phrase}. "
            f"The tiny details made {child.pronoun('object')} want to know what it was doing or how it was made."
        ),
        (
            f"Why did {child.id} need to slow down?",
            f"{child.id} was excited and wanted to get close right away, but {focus.reason_to_wait}. "
            f"Slowing down was the only way to keep the interesting little scene from being spoiled."
        ),
    ]
    if f["disturbed"]:
        qa.append(
            (
                "What went wrong in the middle of the story?",
                f"{child.id} moved too fast and {focus.upset_text}. "
                f"That changed the scene for a moment, but {helper_word} stayed calm and showed {child.pronoun('object')} a better way to learn."
            )
        )
    qa.append(
        (
            f"How did {child.id} learn more in the end?",
            f"{helper_word.capitalize()} helped {child.id} by using {approach.label}. "
            f"They {approach.qa_text}, which let {child.pronoun('object')} notice {focus.detail_text[0].lower() + focus.detail_text[1:]}"
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended quietly, with {child.id} still thinking about that individual {focus.label}. "
            f"The ending shows that curiosity became careful attention instead of a grabby rush."
        )
    )
    return qa


KNOWLEDGE = {
    "snail": [
        (
            "Why does a snail pull into its shell?",
            "A snail pulls into its shell when it feels unsafe. The shell helps protect its soft body."
        )
    ],
    "ant": [
        (
            "Why do ants follow little paths?",
            "Ants often follow scent trails that help them find food and return to their nest. If the trail is disturbed, they can lose the path for a while."
        )
    ],
    "seed": [
        (
            "What is a seedling?",
            "A seedling is a very young plant that has just started to grow. Its roots and stem are still small and easy to damage."
        )
    ],
    "web": [
        (
            "Why do spider webs shine in the light?",
            "A spider web can shine when light catches the thin threads. Water drops can make the threads even easier to see."
        )
    ],
    "magnifier": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes small things look bigger, so it is easier to see fine details without touching them."
        )
    ],
    "drawing": [
        (
            "Why is drawing a good way to study something?",
            "Drawing makes you slow down and notice shapes, lines, and small parts. It helps your eyes keep looking carefully."
        )
    ],
    "patience": [
        (
            "Why can waiting help you learn?",
            "Waiting gives a small creature or fragile thing time to stay natural and still. Then you can notice what it does without scaring or changing it."
        )
    ],
}
KNOWLEDGE_ORDER = ["snail", "ant", "seed", "web", "magnifier", "drawing", "patience"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["focus_cfg"].tags) | set(world.facts["approach"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        focus="snail",
        approach="magnifier",
        child_name="Lina",
        child_type="girl",
        helper_type="mother",
        child_trait="curious",
        poke_level=1,
    ),
    StoryParams(
        setting="porch",
        focus="ant",
        approach="quiet_wait",
        child_name="Owen",
        child_type="boy",
        helper_type="father",
        child_trait="thoughtful",
        poke_level=1,
    ),
    StoryParams(
        setting="windowsill",
        focus="seedling",
        approach="sketchbook",
        child_name="Maya",
        child_type="girl",
        helper_type="grandmother",
        child_trait="careful",
        poke_level=2,
    ),
    StoryParams(
        setting="porch",
        focus="web",
        approach="magnifier",
        child_name="Ben",
        child_type="boy",
        helper_type="mother",
        child_trait="quiet",
        poke_level=1,
    ),
]


ASP_RULES = r"""
focus_fits(S, F) :- setting(S), focus(F), affords(S, F), habitat(F, S).
sensible(A)      :- approach(A), sense(A, V), sense_min(M), V >= M.
works(F, A)      :- focus_kind(F, K), works_for(A, K).
valid(S, F, A)   :- focus_fits(S, F), sensible(A), works(F, A).

disturb_if_fast  :- poke_level(P), P >= 2.
outcome(disturbed) :- disturb_if_fast.
outcome(guided)    :- not disturb_if_fast.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for fid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, fid))
    for fid, focus in FOCI.items():
        lines.append(asp.fact("focus", fid))
        lines.append(asp.fact("focus_kind", fid, focus.kind))
        for hid in sorted(focus.habitat):
            lines.append(asp.fact("habitat", fid, hid))
    for aid, approach in APPROACHES.items():
        lines.append(asp.fact("approach", aid))
        lines.append(asp.fact("sense", aid, approach.sense))
        for k in sorted(approach.works_for):
            lines.append(asp.fact("works_for", aid, k))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def outcome_of(params: StoryParams) -> str:
    return "disturbed" if params.poke_level >= 2 else "guided"


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([asp.fact("poke_level", params.poke_level)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {a.id for a in sensible_approaches()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible approaches match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible approaches: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: one curious child, one small detail, one gentler way to look."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--focus", choices=FOCI)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--child-name")
    ap.add_argument("--poke-level", type=int, choices=[1, 2], help="1 = guided before touching, 2 = quick mistake first")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, focus, approach) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.focus:
        if not focus_fits(SETTINGS[args.setting], FOCI[args.focus]):
            raise StoryError(explain_focus_rejection(SETTINGS[args.setting], FOCI[args.focus]))
    if args.focus and args.approach:
        if not approach_works(FOCI[args.focus], APPROACHES[args.approach]) or APPROACHES[args.approach].sense < SENSE_MIN:
            raise StoryError(explain_approach_rejection(FOCI[args.focus], APPROACHES[args.approach]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.focus is None or combo[1] == args.focus)
        and (args.approach is None or combo[2] == args.approach)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, focus_id, approach_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(pool)
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandmother", "grandfather"])
    child_trait = rng.choice(TRAITS)
    poke_level = args.poke_level if args.poke_level is not None else rng.choice([1, 2])
    return StoryParams(
        setting=setting_id,
        focus=focus_id,
        approach=approach_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        child_trait=child_trait,
        poke_level=poke_level,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.focus not in FOCI:
        raise StoryError(f"Unknown focus: {params.focus}")
    if params.approach not in APPROACHES:
        raise StoryError(f"Unknown approach: {params.approach}")

    setting = SETTINGS[params.setting]
    focus = FOCI[params.focus]
    approach = APPROACHES[params.approach]

    if not focus_fits(setting, focus):
        raise StoryError(explain_focus_rejection(setting, focus))
    if not approach_works(focus, approach) or approach.sense < SENSE_MIN:
        raise StoryError(explain_approach_rejection(focus, approach))

    world = tell(
        setting=setting,
        focus=focus,
        approach=approach,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
        child_trait=params.child_trait,
        poke_level=params.poke_level,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible approaches: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, focus, approach) combos:\n")
        for setting, focus, approach in combos:
            print(f"  {setting:10} {focus:10} {approach}")
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
            header = f"### {p.child_name}: {p.focus} at {p.setting} with {p.approach}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
