#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/matzo_skimpy_magic_detective_story.py
================================================================

A standalone story world for a gentle magical detective tale built around the
seed words "matzo" and "skimpy".

Premise
-------
A child notices that a tray meant for a snack or family moment looks strangely
skimpy because some matzo has gone missing. Instead of jumping to blame, the
child becomes a little detective, follows material clues through a small
everyday setting, discovers a magical helper with a real reason, and helps
solve the problem honestly.

This world prefers a tight, plausible shape over many loose combinations:
the setting must support the helper, and the helper's motive must fit the kind
of place where the clues lead. The result is a small detective story with a
beginning, a clue-driven middle, a turn, and a closing image that proves what
changed.

Run it
------
python storyworlds/worlds/gpt-5.4/matzo_skimpy_magic_detective_story.py
python storyworlds/worlds/gpt-5.4/matzo_skimpy_magic_detective_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/matzo_skimpy_magic_detective_story.py --all --qa
python storyworlds/worlds/gpt-5.4/matzo_skimpy_magic_detective_story.py --trace --seed 777
python storyworlds/worlds/gpt-5.4/matzo_skimpy_magic_detective_story.py --json
python storyworlds/worlds/gpt-5.4/matzo_skimpy_magic_detective_story.py --verify
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
    scene: str
    clue_path: str
    adult_label: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    article: str
    home: str
    trail: str
    magic: str
    confession: str
    apology: str
    fix: str
    clue_kind: str
    roles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Purpose:
    id: str
    want: str
    evidence: str
    need_line: str
    repaired: str
    closing_image: str
    role: str
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


def _r_skimpy_notice(world: World) -> list[str]:
    tray = world.get("tray")
    child = world.get("child")
    if tray.meters["missing"] < THRESHOLD:
        return []
    sig = ("skimpy",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tray.memes["skimpy"] += 1
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    return []


def _r_crumb_trail(world: World) -> list[str]:
    tray = world.get("tray")
    if tray.meters["missing"] < THRESHOLD:
        return []
    sig = ("crumbs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("clues").meters["crumbs"] += 1
    return []


def _r_found_helper(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    clues = world.get("clues")
    if child.meters["searched"] < THRESHOLD or clues.meters["crumbs"] < THRESHOLD:
        return []
    sig = ("found",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.meters["found"] += 1
    child.memes["wonder"] += 1
    return []


def _r_confession(world: World) -> list[str]:
    helper = world.get("helper")
    child = world.get("child")
    if helper.meters["found"] < THRESHOLD or helper.memes["cornered"] < THRESHOLD:
        return []
    sig = ("confess",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["honest"] += 1
    child.memes["understanding"] += 1
    return []


def _r_repair(world: World) -> list[str]:
    tray = world.get("tray")
    helper = world.get("helper")
    child = world.get("child")
    if helper.memes["honest"] < THRESHOLD or helper.meters["returned"] < THRESHOLD:
        return []
    sig = ("repair",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tray.meters["missing"] = 0.0
    tray.meters["full"] += 1
    child.memes["relief"] += 1
    child.memes["kindness"] += 1
    helper.memes["gratitude"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="skimpy_notice", tag="social", apply=_r_skimpy_notice),
    Rule(name="crumb_trail", tag="physical", apply=_r_crumb_trail),
    Rule(name="found_helper", tag="social", apply=_r_found_helper),
    Rule(name="confession", tag="social", apply=_r_confession),
    Rule(name="repair", tag="social", apply=_r_repair),
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


def helper_fits(setting: Setting, helper: HelperKind) -> bool:
    return helper.id in setting.affords


def purpose_fits(helper: HelperKind, purpose: Purpose) -> bool:
    return purpose.role in helper.roles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for hid, helper in HELPERS.items():
            if not helper_fits(setting, helper):
                continue
            for pid, purpose in PURPOSES.items():
                if purpose_fits(helper, purpose):
                    combos.append((sid, hid, pid))
    return combos


def explain_rejection(setting: Setting, helper: HelperKind, purpose: Purpose) -> str:
    if not helper_fits(setting, helper):
        return (
            f"(No story: {helper.article.capitalize()} {helper.label} does not fit {setting.place}. "
            f"That setting offers different kinds of magical clues.)"
        )
    if not purpose_fits(helper, purpose):
        return (
            f"(No story: a {helper.label} would not borrow matzo for {purpose.want}. "
            f"Choose a purpose that matches the helper's kind of work.)"
        )
    return "(No story: this combination does not make a coherent mystery.)"


def predict_discovery(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["searched"] += 1
    sim.get("helper").memes["cornered"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get("helper").meters["found"] >= THRESHOLD,
        "confesses": sim.get("helper").memes["honest"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} liked small mysteries more than loud games. In {setting.place}, "
        f"{setting.scene}"
    )
    world.say(
        f"{adult.label_word.capitalize()} set out a plate of matzo for an afternoon nibble, "
        f"all neat squares and soft little cracks."
    )


def notice_problem(world: World, child: Entity, tray: Entity) -> None:
    tray.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {child.id} came close, the plate looked skimpy, as if a careful row had been pinched away."
    )
    world.say(
        f'"That is a clue," {child.id} whispered. {child.pronoun().capitalize()} touched one crumb with one finger and squinted like a detective.'
    )


def inspect_scene(world: World, child: Entity, setting: Setting, helper: HelperKind, purpose: Purpose) -> None:
    pred = predict_discovery(world)
    world.facts["pred_found"] = pred["found"]
    world.facts["pred_confesses"] = pred["confesses"]
    world.say(
        f"There was no crash and no open window, only {helper.trail} leading {setting.clue_path}."
    )
    world.say(
        f'{child.id} followed the crumbs slowly, past {purpose.evidence}, listening for anything ordinary pretending not to be magical.'
    )


def search(world: World, child: Entity) -> None:
    child.meters["searched"] += 1
    world.get("helper").memes["cornered"] += 1
    propagate(world, narrate=False)


def reveal_helper(world: World, child: Entity, helper: Entity, helper_cfg: HelperKind) -> None:
    spark = helper_cfg.magic
    world.say(
        f"At the end of the trail, {child.id} found {helper_cfg.article} {helper_cfg.label} in {helper_cfg.home}. "
        f"{spark}"
    )
    world.say(
        f"{child.id} did not shout. A detective, {child.pronoun()} knew, should first ask the right question."
    )


def question(world: World, child: Entity, helper_cfg: HelperKind, purpose: Purpose) -> None:
    world.say(
        f'"Did you borrow the matzo?" {child.id} asked. "The plate looked skimpy, and the crumbs came right to you."'
    )
    world.say(
        f"{helper_cfg.article.capitalize()} {helper_cfg.label} tucked its chin and looked at {purpose.evidence}."
    )


def confess(world: World, helper: Entity, helper_cfg: HelperKind, purpose: Purpose) -> None:
    world.say(helper_cfg.confession.format(purpose=purpose.want))
    world.say(helper_cfg.apology)
    helper.meters["returned"] += 1
    propagate(world, narrate=False)


def adult_arrives(world: World, adult: Entity, child: Entity) -> None:
    world.say(
        f"{adult.label_word.capitalize()} had followed the hush and the crumbs. When {adult.pronoun()} saw {child.id} kneeling beside the tiny suspect, {adult.pronoun()} smiled instead of gasping."
    )
    world.say(
        f'"So that is our missing-piece mystery," {adult.pronoun()} said.'
    )


def repair(world: World, adult: Entity, child: Entity, helper_cfg: HelperKind, purpose: Purpose) -> None:
    world.say(
        f"{adult.label_word.capitalize()} listened to the whole story, then nodded. "
        f'"Next time, ask. We can share before the plate grows skimpy."'
    )
    world.say(
        helper_cfg.fix.format(repaired=purpose.repaired)
    )
    world.say(
        f"Soon the matzo was stacked neatly again, and {purpose.closing_image}"
    )


def tell(
    setting: Setting,
    helper_cfg: HelperKind,
    purpose: Purpose,
    child_name: str = "Mira",
    child_type: str = "girl",
    adult_type: str = "grandmother",
) -> World:
    world = World(setting=setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="detective"))
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label=setting.adult_label,
        )
    )
    tray = world.add(Entity(id="tray", type="plate", label="matzo plate", role="evidence"))
    clues = world.add(Entity(id="clues", type="crumbs", label="crumb trail", role="evidence"))
    helper = world.add(
        Entity(
            id="helper",
            type="magic_helper",
            label=helper_cfg.label,
            role="suspect",
            tags=set(helper_cfg.tags),
            attrs={"home": helper_cfg.home},
        )
    )

    introduce(world, child, adult, setting)
    notice_problem(world, child, tray)

    world.para()
    inspect_scene(world, child, setting, helper_cfg, purpose)
    search(world, child)
    reveal_helper(world, child, helper, helper_cfg)
    question(world, child, helper_cfg, purpose)

    world.para()
    confess(world, helper, helper_cfg, purpose)
    adult_arrives(world, adult, child)
    repair(world, adult, child, helper_cfg, purpose)

    world.facts.update(
        child=child,
        adult=adult,
        tray=tray,
        clues=clues,
        helper=helper,
        setting=setting,
        helper_cfg=helper_cfg,
        purpose=purpose,
        mystery_solved=tray.meters["full"] >= THRESHOLD,
        confessed=helper.memes["honest"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        scene="sunlight lay across the table and the chairs made long square shadows on the floor.",
        clue_path="under the table and toward the warm cupboard",
        adult_label="the grandmother",
        affords={"shelf_brownie", "teakettle_sprite"},
        tags={"kitchen"},
    ),
    "bookshop": Setting(
        id="bookshop",
        place="the little bookshop",
        scene="paper smelled sleepy and the bell above the door kept its own small secrets.",
        clue_path="between the low history shelf and the reading nook",
        adult_label="the aunt",
        affords={"bookmark_elf", "shelf_brownie"},
        tags={"bookshop"},
    ),
    "bakery": Setting(
        id="bakery",
        place="the bakery",
        scene="the back room glowed with flour dust and the cooling racks clicked as they settled.",
        clue_path="past the mixing bowl and behind the flour sacks",
        adult_label="the grandfather",
        affords={"teakettle_sprite", "oven_pixie"},
        tags={"bakery"},
    ),
}

HELPERS = {
    "shelf_brownie": HelperKind(
        id="shelf_brownie",
        label="shelf brownie",
        article="a",
        home="a crooked stack of recipe cards",
        trail="a neat run of pale crumbs",
        magic="Tiny blue sparks skipped from its sleeves whenever it blinked.",
        confession='"Yes," squeaked the shelf brownie. "I borrowed it for {purpose}."',
        apology='"I should have asked before I took even one square," it said.',
        fix="The shelf brownie fluttered up, {repaired}, and patted the crumbs into a tidy little pile.",
        clue_kind="crumbs",
        roles={"repair", "nest"},
        tags={"brownie", "magic"},
    ),
    "teakettle_sprite": HelperKind(
        id="teakettle_sprite",
        label="teakettle sprite",
        article="a",
        home="the shining space behind the kettle",
        trail="steam-damp crumbs",
        magic="A silver ribbon of steam curled around its head like a thinking cap.",
        confession='"Oh dear," whispered the teakettle sprite. "I borrowed it for {purpose}."',
        apology='"I was hurrying, and hurrying made me rude," it said.',
        fix="The teakettle sprite spun once, {repaired}, and set the extra pieces back in a crisp row.",
        clue_kind="crumbs",
        roles={"warm", "repair"},
        tags={"sprite", "magic", "steam"},
    ),
    "bookmark_elf": HelperKind(
        id="bookmark_elf",
        label="bookmark elf",
        article="a",
        home="the pocket of a giant atlas",
        trail="paper-dry crumbs",
        magic="Gold letters slid off a book spine and twinkled around its pointed cap.",
        confession='"I did," said the bookmark elf softly. "I borrowed it for {purpose}."',
        apology='"Mysteries are best solved with honesty," it admitted.',
        fix="The bookmark elf tapped the air, {repaired}, and laid the returned matzo beside the plate with both hands.",
        clue_kind="crumbs",
        roles={"nest", "message"},
        tags={"elf", "magic", "books"},
    ),
    "oven_pixie": HelperKind(
        id="oven_pixie",
        label="oven pixie",
        article="an",
        home="a safe cool corner beside the big mixing bowl",
        trail="toasty crumbs",
        magic="Warm amber light blinked in the pixie's hair like tiny oven stars.",
        confession='"It was me," said the oven pixie. "I borrowed it for {purpose}."',
        apology='"Borrowing without asking makes trouble rise too fast," it said.',
        fix="The oven pixie clapped once, {repaired}, and bowed to the child detective.",
        clue_kind="crumbs",
        roles={"warm", "message"},
        tags={"pixie", "magic", "bakery"},
    ),
}

PURPOSES = {
    "patch_roof": Purpose(
        id="patch_roof",
        want="patching a tiny roof over a rain-leaky mouse house",
        evidence="a doll-sized ladder and a thread spool",
        need_line="It needed something dry and flat to cover a leak.",
        repaired="mended the tiny roof with paper instead",
        closing_image="one fresh square waited for each person, while under the cupboard a tiny paper roof sat straight and proud.",
        role="repair",
        tags={"sharing", "home"},
    ),
    "warm_soup": Purpose(
        id="warm_soup",
        want="thickening a spoonful of soup for a shivery sparrow",
        evidence="a saucer no bigger than a leaf",
        need_line="It wanted to help something cold become warm.",
        repaired="carried over a crumb of bread from the grown-ups instead",
        closing_image="the plate no longer looked skimpy, and near the window a sparrow fluffed its feathers in a gentler steam.",
        role="warm",
        tags={"kindness", "warmth"},
    ),
    "write_note": Purpose(
        id="write_note",
        want="pressing a secret thank-you note flat so the ink would dry",
        evidence="a folded scrap of paper with shining purple loops",
        need_line="It needed a small weight for a fluttering page.",
        repaired="used a smooth stone to hold the note flat",
        closing_image="the note dried without a wrinkle, and the matzo plate looked generous again beside it.",
        role="message",
        tags={"notes", "honesty"},
    ),
    "make_nest": Purpose(
        id="make_nest",
        want="lining a tiny nest for a wobbling hatchling made of moonlight",
        evidence="a drift of silver thread",
        need_line="It wanted something crisp to prop the nest until morning.",
        repaired="tucked soft cloth into the nest instead",
        closing_image="the moonlight nest glimmered softly, and the matzo stood stacked in a full, cheerful row.",
        role="nest",
        tags={"nest", "care"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    helper: str
    purpose: str
    child_name: str
    child_type: str
    adult_type: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mira", "Leah", "Talia", "Nina", "Ruth", "Zoe", "Ava", "Lila"]
BOY_NAMES = ["Ezra", "Noam", "Ben", "Max", "Sam", "Leo", "Ari", "Micah"]

KNOWLEDGE = {
    "matzo": [
        (
            "What is matzo?",
            "Matzo is a flat, crisp bread. It breaks into light crumbs and snaps into squares, so in this story it leaves clues a detective can follow.",
        )
    ],
    "skimpy": [
        (
            "What does skimpy mean?",
            "Skimpy means there is less of something than you expected or wanted. A skimpy plate can make someone notice that pieces are missing.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks closely, notices clues, and asks careful questions. Good detectives do not only guess; they try to find out what really happened.",
        )
    ],
    "magic": [
        (
            "Why does magic make a mystery harder?",
            "Magic can make ordinary clues seem surprising, like sparkling crumbs or a hiding place that feels too small. A detective still has to stay calm and look carefully.",
        )
    ],
    "honesty": [
        (
            "Why is it better to ask before borrowing food?",
            "Asking shows respect and stops mix-ups before they grow into problems. Even a helpful reason does not make sneaking something away honest.",
        )
    ],
    "sharing": [
        (
            "How can sharing solve a problem?",
            "Sharing means everyone knows what is being given and why. That turns a secret loss into a kind choice made together.",
        )
    ],
}

KNOWLEDGE_ORDER = ["matzo", "skimpy", "detective", "magic", "honesty", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    helper = f["helper_cfg"]
    purpose = f["purpose"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the words "matzo" and "skimpy" and has gentle magic.',
        f"Tell a cozy mystery where {child.id} notices a skimpy plate of matzo in {setting.place}, follows crumbs, and discovers a {helper.label}.",
        f"Write a child-facing magical detective story where the missing food was taken for {purpose.want}, and the ending shows honesty and sharing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    helper_cfg = f["helper_cfg"]
    purpose = f["purpose"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little detective, and {adult.label_word} who set out the matzo. It is also about a magical {helper_cfg.label} who became the mystery's tiny suspect.",
        ),
        (
            "What was the mystery?",
            f"The plate of matzo looked skimpy because some pieces had been borrowed. {child.id} noticed the missing row and treated it like a real clue.",
        ),
        (
            f"How did {child.id} solve the case?",
            f"{child.id} followed the crumb trail instead of guessing. That careful search led {child.pronoun('object')} to the {helper_cfg.label} in {helper_cfg.home}.",
        ),
        (
            f"Why had the {helper_cfg.label} taken the matzo?",
            f"It had borrowed the matzo for {purpose.want}. The reason was kind, but it still should have asked first instead of taking food in secret.",
        ),
        (
            "How was the problem fixed?",
            f"{adult.label_word.capitalize()} listened, said they could share if asked properly, and the helper changed its plan. Then the matzo was stacked neatly again, which showed the mystery was solved and the missing food was returned.",
        ),
    ]
    if world.facts.get("mystery_solved"):
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly in {setting.place}, with the matzo plate looking full again. {purpose.closing_image[0].upper()}{purpose.closing_image[1:]}",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"matzo", "skimpy", "detective", "magic", "honesty", "sharing"}
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
        if ent.attrs:
            parts.append(f"attrs={ent.attrs}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="kitchen",
        helper="shelf_brownie",
        purpose="patch_roof",
        child_name="Leah",
        child_type="girl",
        adult_type="grandmother",
    ),
    StoryParams(
        setting="bookshop",
        helper="bookmark_elf",
        purpose="write_note",
        child_name="Ezra",
        child_type="boy",
        adult_type="mother",
    ),
    StoryParams(
        setting="bakery",
        helper="oven_pixie",
        purpose="write_note",
        child_name="Mira",
        child_type="girl",
        adult_type="grandfather",
    ),
    StoryParams(
        setting="kitchen",
        helper="teakettle_sprite",
        purpose="warm_soup",
        child_name="Noam",
        child_type="boy",
        adult_type="grandmother",
    ),
    StoryParams(
        setting="bookshop",
        helper="shelf_brownie",
        purpose="make_nest",
        child_name="Talia",
        child_type="girl",
        adult_type="aunt",
    ),
]


ASP_RULES = r"""
fits_setting(S, H) :- affords(S, H).
fits_purpose(H, P) :- helper_role(H, R), purpose_role(P, R).
valid(S, H, P) :- setting(S), helper(H), purpose(P), fits_setting(S, H), fits_purpose(H, P).
"""

ADULT_TYPES = ["mother", "father", "grandmother", "grandfather"]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, hid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for role in sorted(helper.roles):
            lines.append(asp.fact("helper_role", hid, role))
    for pid, purpose in PURPOSES.items():
        lines.append(asp.fact("purpose", pid))
        lines.append(asp.fact("purpose_role", pid, purpose.role))
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        print(f"OK: smoke test generated a story with {len(sample.story.split())} words.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Magical detective story world: a skimpy matzo plate, a clue trail, and a tiny honest solution."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--purpose", choices=PURPOSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.helper and args.purpose:
        setting = SETTINGS[args.setting]
        helper = HELPERS[args.helper]
        purpose = PURPOSES[args.purpose]
        if not (helper_fits(setting, helper) and purpose_fits(helper, purpose)):
            raise StoryError(explain_rejection(setting, helper, purpose))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.helper is None or c[1] == args.helper)
        and (args.purpose is None or c[2] == args.purpose)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, helper_id, purpose_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    return StoryParams(
        setting=setting_id,
        helper=helper_id,
        purpose=purpose_id,
        child_name=child_name,
        child_type=child_type,
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.purpose not in PURPOSES:
        raise StoryError(f"(Unknown purpose: {params.purpose})")

    setting = SETTINGS[params.setting]
    helper = HELPERS[params.helper]
    purpose = PURPOSES[params.purpose]
    if not helper_fits(setting, helper) or not purpose_fits(helper, purpose):
        raise StoryError(explain_rejection(setting, helper, purpose))

    world = tell(
        setting=setting,
        helper_cfg=helper,
        purpose=purpose,
        child_name=params.child_name,
        child_type=params.child_type,
        adult_type=params.adult_type,
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
        print(f"{len(combos)} compatible (setting, helper, purpose) combos:\n")
        for setting, helper, purpose in combos:
            print(f"  {setting:9} {helper:16} {purpose}")
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
            header = f"### {p.child_name}: {p.helper} in {p.setting} ({p.purpose})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
