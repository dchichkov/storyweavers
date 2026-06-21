#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/splice_moral_value_comedy.py
=======================================================

A standalone storyworld about a child trying to fix a broken parade prop with a
"hurry-up splice" and learning that honesty works better than a sneaky cover-up.

The seed asked for:
- the word "splice"
- a Moral Value feature
- a Comedy style

So this little world models a comic school-parade problem:

    A child has a funny parade prop or costume piece.
    It breaks right before the walk.
    The child is tempted to hide the problem with a goofy quick splice.
    A friend warns that the patch may fail.
    If the child tells the truth, a grown-up helper makes a proper repair and the
    story ends warmly.
    If the child hides the problem, the silly splice fails in public and the child
    has to admit the truth afterward.

The world prefers a small number of plausible variants over wide but weak
coverage.  A proper repair must match the prop material, and a quick splice must
at least be a physically possible attachment.  Unreasonable explicit choices are
rejected with StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/splice_moral_value_comedy.py
    python storyworlds/worlds/gpt-5.4/splice_moral_value_comedy.py --prop dragon_tail --fix tape --choice honest
    python storyworlds/worlds/gpt-5.4/splice_moral_value_comedy.py --prop balloon_trunk --fix thread
    python storyworlds/worlds/gpt-5.4/splice_moral_value_comedy.py --all
    python storyworlds/worlds/gpt-5.4/splice_moral_value_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/splice_moral_value_comedy.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
    material: str = ""
    attachable: bool = False
    flexible: bool = False
    # meters = physical, memes = feelings/social state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_female"}
        male = {"boy", "father", "man", "teacher_male", "janitor"}
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
            "teacher_female": "teacher",
            "teacher_male": "teacher",
            "janitor": "janitor",
        }.get(self.type, self.label or self.type)


# ---------------------------------------------------------------------------
# Config registries
# ---------------------------------------------------------------------------
@dataclass
class ParadeProp:
    id: str
    phrase: str
    label: str
    broken_part: str
    material: str
    joke_line: str
    march_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuickFix:
    id: str
    label: str
    phrase: str
    sense: int
    works_on: set[str] = field(default_factory=set)
    strength: int = 0
    wobble_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ProperRepair:
    id: str
    label: str
    phrase: str
    helps_on: set[str] = field(default_factory=set)
    text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    label: str
    phrase: str
    calm_line: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    prop = world.entities.get("prop")
    if prop is None:
        return out
    if prop.meters["patched"] < THRESHOLD:
        return out
    if prop.meters["patch_strength"] >= prop.meters["needed_strength"]:
        return out
    sig = ("wobble", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.meters["wobbling"] += 1
    child = world.get("child")
    friend = world.get("friend")
    child.memes["worry"] += 1
    friend.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_spill_laughter(world: World) -> list[str]:
    out: list[str] = []
    prop = world.entities.get("prop")
    if prop is None or prop.meters["fell_apart"] < THRESHOLD:
        return out
    sig = ("laughter", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room = world.get("room")
    room.meters["noise"] += 1
    child = world.get("child")
    child.memes["embarrassment"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill_laughter", tag="social", apply=_r_spill_laughter),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def can_splice(prop: ParadeProp, fix: QuickFix) -> bool:
    return prop.material in fix.works_on


def sensible_fixes() -> list[QuickFix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def proper_match(prop: ParadeProp, repair: ProperRepair) -> bool:
    return prop.material in repair.helps_on


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for prop_id, prop in PROPS.items():
        for fix_id, fix in FIXES.items():
            if not can_splice(prop, fix):
                continue
            for repair_id, repair in REPAIRS.items():
                if not proper_match(prop, repair):
                    continue
                for helper_id in HELPERS:
                    combos.append((prop_id, fix_id, repair_id, helper_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    prop = PROPS[params.prop]
    fix = FIXES[params.fix]
    if params.choice == "honest":
        return "honest_success"
    return "sneaky_success" if fix.strength >= REQUIRED_STRENGTH[prop.material] else "sneaky_fail"


def explain_rejection(prop: ParadeProp, fix: QuickFix) -> str:
    return (
        f"(No story: {fix.label} cannot really splice {prop.phrase}. "
        f"It does not suit {prop.material}, so the patch would not even hold for one step.)"
    )


def explain_repair(prop: ParadeProp, repair: ProperRepair) -> str:
    return (
        f"(No story: {repair.label} is not the right kind of repair for {prop.phrase}. "
        f"Pick a repair that actually works on {prop.material}.)"
    )


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction and verbs
# ---------------------------------------------------------------------------
def predict_quick_patch(world: World) -> dict:
    sim = world.copy()
    prop = sim.get("prop")
    propagate(sim, narrate=False)
    return {
        "wobble": prop.meters["wobbling"] >= THRESHOLD,
        "success": prop.meters["patch_strength"] >= prop.meters["needed_strength"],
    }


def setup_scene(world: World, child: Entity, friend: Entity, prop_cfg: ParadeProp) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At school, {child.id} and {friend.id} were getting ready for the Funny March. "
        f"{child.id} had made {prop_cfg.phrase}, and everyone who saw it giggled."
    )
    world.say(prop_cfg.joke_line)


def break_prop(world: World, child: Entity, prop_cfg: ParadeProp) -> None:
    prop = world.get("prop")
    prop.meters["broken"] += 1
    child.memes["shock"] += 1
    world.say(
        f"But just as {child.id} lifted it for one proud twirl, {prop_cfg.broken_part} came loose. "
        f"The silly prop sagged in the middle like it had suddenly fallen asleep."
    )


def tempting_fix(world: World, child: Entity, fix: QuickFix) -> None:
    child.memes["scheme"] += 1
    world.say(
        f'"Wait!" said {child.id}. "I can splice it with {fix.phrase}." '
        f"For one second, the hurry-up idea sounded wonderfully clever."
    )


def warn_friend(world: World, child: Entity, friend: Entity, prop_cfg: ParadeProp, fix: QuickFix) -> None:
    prop = world.get("prop")
    prop.meters["patched"] += 1
    prop.meters["patch_strength"] = float(fix.strength)
    propagate(world, narrate=False)
    pred = predict_quick_patch(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_success"] = pred["success"]
    prop.meters["patched"] = 0.0
    prop.meters["patch_strength"] = 0.0
    if pred["wobble"]:
        world.say(
            f'{friend.id} peered at the broken {prop_cfg.label}. "{fix.label.capitalize()} might hold for one funny puff, '
            f'but not for the whole march," {friend.pronoun()} said. '
            f'"You should tell a grown-up before your splice turns into a flop."'
        )
    else:
        world.say(
            f'{friend.id} blinked at the idea. "That might hold," {friend.pronoun()} said, '
            f'"but hiding the break would still feel wrong. You should tell the truth anyway."'
        )


def make_sneaky_splice(world: World, child: Entity, prop_cfg: ParadeProp, fix: QuickFix) -> None:
    prop = world.get("prop")
    prop.meters["patched"] += 1
    prop.meters["patch_strength"] = float(fix.strength)
    child.memes["defiance"] += 1
    propagate(world, narrate=False)
    wobble = prop.meters["wobbling"] >= THRESHOLD
    extra = f" {fix.wobble_line}" if wobble and fix.wobble_line else ""
    world.say(
        f"{child.id} glanced around, took a deep breath, and made a quick splice with {fix.phrase}. "
        f"The repair looked neat from far away, but the funny {prop_cfg.label} gave a tiny shiver.{extra}"
    )


def honest_confession(world: World, child: Entity, helper: Entity, prop_cfg: ParadeProp) -> None:
    child.memes["honesty"] += 1
    child.memes["relief"] += 1
    world.say(
        f'{child.id} hugged the droopy {prop_cfg.label} to {child.pronoun("possessive")} chest and hurried to {helper.label_word}. '
        f'"I broke it," {child.pronoun()} admitted. "I wanted to hide it, but I think I should tell the truth."'
    )


def helper_repairs(world: World, helper: Entity, child: Entity, repair: ProperRepair, prop_cfg: ParadeProp) -> None:
    prop = world.get("prop")
    prop.meters["patched"] = 1.0
    prop.meters["patch_strength"] = float(REQUIRED_STRENGTH[prop_cfg.material] + 1)
    prop.meters["broken"] = 0.0
    child.memes["trust"] += 1
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"{helper.phrase} smiled instead of scolding. {helper.calm_line} "
        f"Then {helper.pronoun()} {repair.text.format(part=prop_cfg.broken_part, label=prop_cfg.label)}."
    )
    world.say(
        f"When {child.id} lifted the {prop_cfg.label} again, it swished proudly instead of drooping."
    )


def march_happy(world: World, child: Entity, friend: Entity, prop_cfg: ParadeProp) -> None:
    child.memes["pride"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Soon the music started, and {child.id} marched beside {friend.id}. {prop_cfg.march_line} "
        f"This time the joke stayed funny because the fix was real."
    )
    world.say(
        f"{child.id} grinned all the way down the hall, glad that telling the truth had made room for help."
    )


def march_sneaky(world: World, child: Entity, friend: Entity, prop_cfg: ParadeProp, fix: QuickFix) -> None:
    prop = world.get("prop")
    world.say(
        f"Then the Funny March began. {child.id} stepped forward, trying to act as if nothing at all was wrong."
    )
    if prop.meters["patch_strength"] >= prop.meters["needed_strength"]:
        child.memes["relief"] += 1
        world.say(
            f"To {child.pronoun('possessive')} great surprise, the splice held. "
            f"The room laughed at the prop on purpose, not by accident, and {friend.id} still gave {child.pronoun('object')} a look that said, "
            f'"Next time, tell first."'
        )
        world.say(
            f"After the march, {child.id} went to a grown-up anyway and confessed about the quick patch. "
            f"It had worked for the moment, but {child.pronoun()} learned that hiding a problem feels wobblier than fixing it honestly."
        )
    else:
        prop.meters["fell_apart"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Three steps later, the splice gave up. {prop_cfg.broken_part.capitalize()} popped loose, spun through the air, "
            f"and landed on the floor with a comic plop."
        )
        world.say(
            f"The room burst into surprised laughter, and even {child.id} had to blink at the ridiculous disaster."
        )
        child.memes["honesty"] += 1
        world.say(
            f'With red cheeks, {child.id} picked up the runaway piece and said, "I tried to hide the break." '
            f'{friend.id} squeezed {child.pronoun("possessive")} arm, and together they went to tell a grown-up the truth.'
        )


def after_fail_repair(world: World, helper: Entity, child: Entity, repair: ProperRepair, prop_cfg: ParadeProp) -> None:
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{helper.phrase} listened, nodded, and did not laugh meanly. {helper.calm_line} "
        f"Then {helper.pronoun()} {repair.text.format(part=prop_cfg.broken_part, label=prop_cfg.label)}."
    )
    world.say(
        f"By the time the class made one last silly lap, the {prop_cfg.label} was mended, and {child.id} could laugh for the right reason again."
    )


def tell_story(
    prop_cfg: ParadeProp,
    fix: QuickFix,
    repair: ProperRepair,
    helper_cfg: HelperCfg,
    choice: str,
    child_name: str = "Mia",
    child_type: str = "girl",
    friend_name: str = "Ben",
    friend_type: str = "boy",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            tags=set(helper_cfg.tags),
        )
    )
    room = world.add(Entity(id="room", type="room", label="hall"))
    prop = world.add(
        Entity(
            id="prop",
            type="prop",
            label=prop_cfg.label,
            phrase=prop_cfg.phrase,
            material=prop_cfg.material,
            attachable=True,
            flexible=prop_cfg.material in {"fabric", "paper"},
            tags=set(prop_cfg.tags),
        )
    )
    prop.meters["needed_strength"] = float(REQUIRED_STRENGTH[prop_cfg.material])

    setup_scene(world, child, friend, prop_cfg)
    break_prop(world, child, prop_cfg)

    world.para()
    tempting_fix(world, child, fix)
    warn_friend(world, child, friend, prop_cfg, fix)

    if choice == "honest":
        world.para()
        honest_confession(world, child, helper, prop_cfg)
        helper_repairs(world, helper, child, repair, prop_cfg)
        world.para()
        march_happy(world, child, friend, prop_cfg)
    else:
        world.para()
        make_sneaky_splice(world, child, prop_cfg, fix)
        world.para()
        march_sneaky(world, child, friend, prop_cfg, fix)
        if outcome_of(
            StoryParams(
                prop=prop_cfg.id,
                fix=fix.id,
                repair=repair.id,
                helper=helper_cfg.id,
                choice=choice,
                child_name=child_name,
                child_gender=child_type,
                friend_name=friend_name,
                friend_gender=friend_type,
            )
        ) == "sneaky_fail":
            world.para()
            after_fail_repair(world, helper, child, repair, prop_cfg)

    world.facts.update(
        child=child,
        friend=friend,
        helper=helper,
        prop_cfg=prop_cfg,
        prop=prop,
        fix=fix,
        repair=repair,
        helper_cfg=helper_cfg,
        choice=choice,
        outcome=outcome_of(
            StoryParams(
                prop=prop_cfg.id,
                fix=fix.id,
                repair=repair.id,
                helper=helper_cfg.id,
                choice=choice,
                child_name=child_name,
                child_gender=child_type,
                friend_name=friend_name,
                friend_gender=friend_type,
            )
        ),
        predicted_wobble=world.facts.get("predicted_wobble", False),
        predicted_success=world.facts.get("predicted_success", False),
        confessed=child.memes["honesty"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PROPS = {
    "dragon_tail": ParadeProp(
        id="dragon_tail",
        phrase="a green dragon tail made from shiny fabric",
        label="dragon tail",
        broken_part="the end of the tail",
        material="fabric",
        joke_line='It was so long and swishy that one child said it looked like a cucumber trying to dance.',
        march_line="The tail curled behind like a cheerful green question mark, and every swish made the class laugh.",
        tags={"parade", "fabric", "dragon"},
    ),
    "robot_antenna": ParadeProp(
        id="robot_antenna",
        phrase="a silver robot hat with a springy paper antenna",
        label="robot antenna",
        broken_part="the springy antenna",
        material="paper",
        joke_line='When the antenna bobbed, it made the hat look as if it was trying to think extra hard.',
        march_line="The robot hat bobbed and wiggled like it was receiving jokes from the ceiling.",
        tags={"parade", "paper", "robot"},
    ),
    "balloon_trunk": ParadeProp(
        id="balloon_trunk",
        phrase="a silly elephant nose made from a long balloon",
        label="balloon trunk",
        broken_part="the front of the trunk",
        material="balloon",
        joke_line='It bounced so much that it kept booping the air in front of it.',
        march_line="The balloon trunk bounced with every step, and the class trumpeted along behind it.",
        tags={"parade", "balloon", "elephant"},
    ),
}

FIXES = {
    "tape": QuickFix(
        id="tape",
        label="tape",
        phrase="a strip of clear tape",
        sense=3,
        works_on={"fabric", "paper", "balloon"},
        strength=2,
        wobble_line="A corner lifted at once and fluttered like a tiny flag.",
        tags={"tape"},
    ),
    "thread": QuickFix(
        id="thread",
        label="thread",
        phrase="blue thread from the craft box",
        sense=3,
        works_on={"fabric"},
        strength=3,
        wobble_line="The knot looked lumpy, but it sat still.",
        tags={"thread"},
    ),
    "sticker": QuickFix(
        id="sticker",
        label="sticker",
        phrase="a giant smiling star sticker",
        sense=2,
        works_on={"paper", "balloon"},
        strength=1,
        wobble_line="The smiling star sticker wrinkled at the edges as if it already had doubts.",
        tags={"sticker"},
    ),
    "chewing_gum": QuickFix(
        id="chewing_gum",
        label="chewing gum",
        phrase="a blob of chewing gum",
        sense=1,
        works_on={"paper"},
        strength=0,
        wobble_line="The gum made the prop smell like minty trouble.",
        tags={"gum"},
    ),
}

REPAIRS = {
    "sew": ProperRepair(
        id="sew",
        label="sewing",
        phrase="a neat line of stitches",
        helps_on={"fabric"},
        text="sewed {part} back onto the {label} with small, firm stitches",
        tags={"sewing"},
    ),
    "retape": ProperRepair(
        id="retape",
        label="fresh craft tape",
        phrase="careful craft tape",
        helps_on={"paper", "balloon"},
        text="used fresh craft tape and patient hands to fasten {part} back onto the {label}",
        tags={"tape"},
    ),
    "replace_piece": ProperRepair(
        id="replace_piece",
        label="a spare piece",
        phrase="a spare matching piece",
        helps_on={"paper", "balloon"},
        text="found a spare bit in the supply box and rebuilt {part} on the {label}",
        tags={"repair"},
    ),
}

HELPERS = {
    "teacher": HelperCfg(
        id="teacher",
        type="teacher_female",
        label="the teacher",
        phrase="Ms. Ada",
        calm_line='"Thank you for telling me before the whole thing got sillier," she said.',
        tags={"teacher"},
    ),
    "janitor": HelperCfg(
        id="janitor",
        type="janitor",
        label="the janitor",
        phrase="Mr. Bell",
        calm_line='"Good thing you came now," he said. "Problems are easier to mend than to hide."',
        tags={"janitor"},
    ),
}

REQUIRED_STRENGTH = {
    "fabric": 3,
    "paper": 2,
    "balloon": 2,
}


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    prop: str
    fix: str
    repair: str
    helper: str
    choice: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Noah", "Eli", "Theo"]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "parade": [
        (
            "What is a parade?",
            "A parade is when people walk together in a line or group, often wearing fun things or carrying decorations, while others watch."
        )
    ],
    "splice": [
        (
            "What does splice mean?",
            "To splice means to join two broken or separate parts together. People use the word when they mend, connect, or patch something."
        )
    ],
    "honesty": [
        (
            "Why is honesty helpful when something breaks?",
            "Honesty helps people solve the real problem sooner. When you tell the truth, a helper can use the right fix instead of guessing."
        )
    ],
    "tape": [
        (
            "What is tape good for?",
            "Tape can hold light things together for a while. It works best when the material and the job match."
        )
    ],
    "thread": [
        (
            "What is thread used for?",
            "Thread is a thin string used for sewing fabric together. It is useful when cloth tears and needs stitches."
        )
    ],
    "teacher": [
        (
            "What can a teacher help with at school?",
            "A teacher can help with problems, supplies, and hurt feelings. Teachers often know where to find tools and how to keep children calm."
        )
    ],
    "janitor": [
        (
            "What does a janitor do?",
            "A janitor helps take care of a building. That can include cleaning, fixing small problems, and bringing tools when something needs mending."
        )
    ],
    "sewing": [
        (
            "Why do stitches hold fabric well?",
            "Stitches pass thread through cloth and tie the torn parts together. That makes a stronger join than just sticking the surface."
        )
    ],
    "repair": [
        (
            "What is a repair?",
            "A repair is a fix that makes something work again. A good repair matches the material and the kind of break."
        )
    ],
}
KNOWLEDGE_ORDER = ["parade", "splice", "honesty", "tape", "thread", "teacher", "janitor", "sewing", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prop_cfg = f["prop_cfg"]
    helper = f["helper"]
    outcome = f["outcome"]
    if outcome == "honest_success":
        return [
            'Write a funny, gentle story for a 3-to-5-year-old that uses the word "splice" and teaches honesty.',
            f"Tell a comedy story where {child.id}'s {prop_cfg.label} breaks before a school parade, and {child.pronoun()} is tempted to hide it with a quick splice but chooses to tell {helper.label_word} the truth.",
            "Write a short moral story where a child learns that asking for help early is less embarrassing than pretending a bad fix is good.",
        ]
    if outcome == "sneaky_success":
        return [
            'Write a light comedy story that includes the word "splice" and ends with a child admitting the truth after a shaky quick fix works for a moment.',
            f"Tell a parade story where {child.id} hides a break with a quick splice, gets away with it briefly, and still learns honesty matters more than luck.",
            "Write a funny moral tale where a child sees that even a lucky shortcut feels wobblier than telling the truth.",
        ]
    return [
        'Write a funny story for a 3-to-5-year-old that includes the word "splice" and teaches honesty after a silly mistake.',
        f"Tell a comedy story where {child.id} makes a sneaky splice on a broken parade prop, and the patch fails in public before {child.pronoun()} admits the truth.",
        "Write a moral story with a comic flop in the middle and a warm ending that shows why honest words are better than hiding trouble.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    helper = f["helper"]
    prop_cfg = f["prop_cfg"]
    fix = f["fix"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was getting ready for a funny school parade, and {friend.id}, who tried to help. A grown-up helper also mattered because the broken prop needed a real repair."
        ),
        (
            f"What broke?",
            f"{prop_cfg.broken_part.capitalize()} on the {prop_cfg.label} came loose. That is the problem that pushed {child.id} toward the idea of making a quick splice."
        ),
        (
            f"What did {child.id} want to use as a splice?",
            f"{child.id} wanted to use {fix.phrase} as a quick splice. It seemed fast and clever in the moment, which is why the idea was tempting."
        ),
    ]
    if f.get("predicted_wobble"):
        qa.append(
            (
                f"Why did {friend.id} worry about the quick splice?",
                f"{friend.id} worried because the patch looked too weak for the whole march. In the world model, the quick splice would wobble before the parade was over."
            )
        )
    else:
        qa.append(
            (
                f"Why did {friend.id} still say {child.id} should tell the truth?",
                f"{friend.id} knew the patch might hold, but hiding the break would still be dishonest. The warning was about character as well as the repair."
            )
        )
    if outcome == "honest_success":
        qa.append(
            (
                f"What happened when {child.id} told the truth?",
                f"{child.id} went to {helper.phrase} and admitted the break. Because {child.pronoun()} was honest early, the helper could use {repair.label} to make a real fix."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                f"The moral is that honesty makes room for help. Telling the truth quickly turned a scary mistake into a fixable one."
            )
        )
    elif outcome == "sneaky_success":
        qa.append(
            (
                "Did the sneaky patch work?",
                f"Yes, it held long enough for the march. But {child.id} still felt the hidden problem wobbling inside, so {child.pronoun()} confessed afterward."
            )
        )
        qa.append(
            (
                "What did the child learn?",
                "The child learned that luck is not the same as doing the right thing. Even when a shortcut works, honesty is steadier."
            )
        )
    else:
        qa.append(
            (
                "What happened during the march?",
                f"The quick splice failed and the broken piece flew off with a silly plop. That public flop forced {child.id} to stop hiding the truth and ask for real help."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                "The moral is that hiding trouble often makes a bigger mess. Honest words may feel hard at first, but they lead to better help and a kinder ending."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"parade", "splice", "honesty"}
    tags |= set(f["fix"].tags)
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["repair"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.material:
            bits.append(f"material={e.material}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
can_splice(P, F) :- prop(P), fix(F), material(P, M), works_on(F, M).
repair_ok(P, R)  :- prop(P), repair(R), material(P, M), helps_on(R, M).
valid(P, F, R, H) :- prop(P), fix(F), repair(R), helper(H), can_splice(P, F), repair_ok(P, R).

sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.

% --- outcomes --------------------------------------------------------------
needed(N)   :- chosen_prop(P), material(P, M), required_strength(M, N).
quick_ok    :- chosen_fix(F), strength(F, S), needed(N), S >= N.

outcome(honest_success) :- choice(honest).
outcome(sneaky_success) :- choice(hide), quick_ok.
outcome(sneaky_fail)    :- choice(hide), not quick_ok.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("material", pid, prop.material))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("strength", fid, fix.strength))
        for mat in sorted(fix.works_on):
            lines.append(asp.fact("works_on", fid, mat))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        for mat in sorted(repair.helps_on):
            lines.append(asp.fact("helps_on", rid, mat))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for mat, need in REQUIRED_STRENGTH.items():
        lines.append(asp.fact("required_strength", mat, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_prop", params.prop),
            asp.fact("chosen_fix", params.fix),
            asp.fact("choice", params.choice),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    clingo_sens = set(asp_sensible())
    python_sens = {f.id for f in sensible_fixes()}
    if clingo_sens == python_sens:
        print(f"OK: sensible fixes match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(p)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # smoke test: ordinary generation should not crash
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        prop="dragon_tail",
        fix="tape",
        repair="sew",
        helper="teacher",
        choice="honest",
        child_name="Mia",
        child_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
    ),
    StoryParams(
        prop="robot_antenna",
        fix="sticker",
        repair="replace_piece",
        helper="teacher",
        choice="hide",
        child_name="Leo",
        child_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
    ),
    StoryParams(
        prop="dragon_tail",
        fix="thread",
        repair="sew",
        helper="janitor",
        choice="hide",
        child_name="Ava",
        child_gender="girl",
        friend_name="Max",
        friend_gender="boy",
    ),
    StoryParams(
        prop="balloon_trunk",
        fix="tape",
        repair="retape",
        helper="janitor",
        choice="honest",
        child_name="Finn",
        child_gender="boy",
        friend_name="Lucy",
        friend_gender="girl",
    ),
]


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Comedy storyworld: a broken parade prop, a quick splice, and an honesty lesson."
    )
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--choice", choices=["honest", "hide"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    if args.prop and args.fix and not can_splice(PROPS[args.prop], FIXES[args.fix]):
        raise StoryError(explain_rejection(PROPS[args.prop], FIXES[args.fix]))
    if args.prop and args.repair and not proper_match(PROPS[args.prop], REPAIRS[args.repair]):
        raise StoryError(explain_repair(PROPS[args.prop], REPAIRS[args.repair]))

    combos = [
        c for c in valid_combos()
        if (args.prop is None or c[0] == args.prop)
        and (args.fix is None or c[1] == args.fix)
        and (args.repair is None or c[2] == args.repair)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    prop_id, fix_id, repair_id, helper_id = rng.choice(sorted(combos))
    choice = args.choice or rng.choice(["honest", "hide"])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=child_name)

    return StoryParams(
        prop=prop_id,
        fix=fix_id,
        repair=repair_id,
        helper=helper_id,
        choice=choice,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop: {params.prop})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.choice not in {"honest", "hide"}:
        raise StoryError(f"(Unknown choice: {params.choice})")

    prop = PROPS[params.prop]
    fix = FIXES[params.fix]
    repair = REPAIRS[params.repair]
    helper = HELPERS[params.helper]

    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not can_splice(prop, fix):
        raise StoryError(explain_rejection(prop, fix))
    if not proper_match(prop, repair):
        raise StoryError(explain_repair(prop, repair))

    world = tell_story(
        prop_cfg=prop,
        fix=fix,
        repair=repair,
        helper_cfg=helper,
        choice=params.choice,
        child_name=params.child_name,
        child_type=params.child_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (prop, fix, repair, helper) combos:\n")
        for prop, fix, repair, helper in combos:
            print(f"  {prop:14} {fix:10} {repair:13} {helper}")
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
            header = f"### {p.child_name}: {p.prop}, {p.fix}, {p.choice}"
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
