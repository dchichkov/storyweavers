#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sorcerer_moral_value_foreshadowing_inner_monologue_whodunit.py
==========================================================================================

A small whodunit-style story world about a missing magical object, a young
apprentice, and a kindly sorcerer. The mystery is never truly wicked: someone
borrowed the object to solve a private problem and was too ashamed to ask.

The world model tracks physical clues and emotional changes so the prose comes
from simulated state rather than noun-swapping. The story always includes:
- a sorcerer
- foreshadowing
- inner monologue
- a moral value about honesty and asking for help

Run it
------
    python storyworlds/worlds/gpt-5.4/sorcerer_moral_value_foreshadowing_inner_monologue_whodunit.py
    python storyworlds/worlds/gpt-5.4/sorcerer_moral_value_foreshadowing_inner_monologue_whodunit.py --item ember_orb --culprit gardener
    python storyworlds/worlds/gpt-5.4/sorcerer_moral_value_foreshadowing_inner_monologue_whodunit.py --culprit baker --approach stern
    python storyworlds/worlds/gpt-5.4/sorcerer_moral_value_foreshadowing_inner_monologue_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/sorcerer_moral_value_foreshadowing_inner_monologue_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/sorcerer_moral_value_foreshadowing_inner_monologue_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    power: str
    shine: str
    use_effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CulpritProfile:
    id: str
    label: str
    phrase: str
    type: str
    clue_mark: str
    clue_plural: bool
    need_power: str
    worry: str
    use_place: str
    use_scene: str
    hiding_place: str
    apology: str
    timid: bool = False
    tags: set[str] = field(default_factory=set)

    def mark_phrase(self) -> str:
        if self.clue_plural:
            return self.clue_mark
        return f"a {self.clue_mark}"


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


ITEMS = {
    "ember_orb": Item(
        id="ember_orb",
        label="ember orb",
        phrase="the ember orb",
        power="warm",
        shine="glowed like a peach-colored coal inside glass",
        use_effect="sent a soft, safe heat into the air",
        tags={"warm", "magic"},
    ),
    "moon_lantern": Item(
        id="moon_lantern",
        label="moon lantern",
        phrase="the moon lantern",
        power="glow",
        shine="shone with a pearly light that reached into corners",
        use_effect="filled dark shelves with silver light",
        tags={"light", "magic"},
    ),
    "silver_rune_key": Item(
        id="silver_rune_key",
        label="silver rune key",
        phrase="the silver rune key",
        power="unlock",
        shine="winked with tiny blue letters along its handle",
        use_effect="clicked old locks open without breaking them",
        tags={"unlock", "magic"},
    ),
}

CULPRITS = {
    "gardener": CulpritProfile(
        id="gardener",
        label="Moss the gardener",
        phrase="Moss the tower gardener",
        type="man",
        clue_mark="crumbs of damp soil",
        clue_plural=True,
        need_power="warm",
        worry="a frost had bitten the smallest moon-vine in the greenhouse",
        use_place="the greenhouse",
        use_scene="the little vine was drooping in a cracked blue pot",
        hiding_place="under a seed basket",
        apology="I should have asked before I borrowed it. I was trying to save the vine before sunrise.",
        timid=True,
        tags={"soil", "garden"},
    ),
    "baker": CulpritProfile(
        id="baker",
        label="Pella the baker",
        phrase="Pella the tower baker",
        type="woman",
        clue_mark="flour dust",
        clue_plural=True,
        need_power="glow",
        worry="the cellar oven-light had gone out while the festival buns were still rising",
        use_place="the bakery cellar",
        use_scene="rows of dough were sleeping on trays in the dark",
        hiding_place="inside a bread basket lined with cloth",
        apology="I thought I would bring it right back. I did not want the buns for the feast to fail.",
        timid=False,
        tags={"flour", "bakery"},
    ),
    "librarian": CulpritProfile(
        id="librarian",
        label="Quill the librarian",
        phrase="Quill the tower librarian",
        type="man",
        clue_mark="blue ink smudges",
        clue_plural=True,
        need_power="unlock",
        worry="the little history room had stuck shut, and tonight's song book was inside",
        use_place="the archive hall",
        use_scene="the narrow oak door still stood a finger-width open",
        hiding_place="behind the biggest atlas on the lowest shelf",
        apology="I panicked when the door stuck. I meant to return it before anyone noticed.",
        timid=True,
        tags={"ink", "library"},
    ),
}

APPROACHES = {"gentle": "gentle", "stern": "stern"}

GIRL_NAMES = ["Nia", "Lina", "Mira", "Ava", "Zoe", "Ella", "Iris", "Tara"]
BOY_NAMES = ["Oren", "Leo", "Finn", "Milo", "Toby", "Eli", "Theo", "Jules"]
SORCERER_NAMES = ["Sable", "Orin", "Maris", "Thorn", "Elowen", "Rowan"]


@dataclass
class StoryParams:
    item: str
    culprit: str
    approach: str
    apprentice_name: str
    apprentice_gender: str
    sorcerer_name: str
    sorcerer_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        item="ember_orb",
        culprit="gardener",
        approach="gentle",
        apprentice_name="Nia",
        apprentice_gender="girl",
        sorcerer_name="Sable",
        sorcerer_gender="woman",
    ),
    StoryParams(
        item="moon_lantern",
        culprit="baker",
        approach="stern",
        apprentice_name="Oren",
        apprentice_gender="boy",
        sorcerer_name="Maris",
        sorcerer_gender="woman",
    ),
    StoryParams(
        item="silver_rune_key",
        culprit="librarian",
        approach="gentle",
        apprentice_name="Mira",
        apprentice_gender="girl",
        sorcerer_name="Rowan",
        sorcerer_gender="man",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for item_id, item in ITEMS.items():
        for culprit_id, culprit in CULPRITS.items():
            if item.power == culprit.need_power:
                combos.append((item_id, culprit_id))
    return sorted(combos)


def explain_rejection(item_id: str, culprit_id: str) -> str:
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    return (
        f"(No story: {culprit.label} would need magic that can {culprit.need_power}, "
        f"but {item.phrase} is for {item.power}. The mystery works only when the "
        f"borrowed object could actually solve the culprit's problem.)"
    )


def reveal_of(approach: str, culprit_id: str) -> str:
    culprit = CULPRITS[culprit_id]
    if approach == "gentle":
        return "soft_confession"
    if culprit.timid:
        return "tearful_confession"
    return "brisk_confession"


def foreshadow_line(item: Item, culprit: CulpritProfile) -> str:
    if culprit.id == "gardener":
        return (
            f"Before breakfast, a few {culprit.clue_mark} dotted the white stair by the display shelf. "
            f"Nia-like little hints often meant nothing in the tower, but this one seemed to lean toward {culprit.use_place}."
        ).replace("Nia-like ", "")
    if culprit.id == "baker":
        return (
            f"Before the tower woke fully, {culprit.clue_mark} lay on the velvet cloth under the festival shelf. "
            f"It looked too fresh to belong to yesterday."
        )
    return (
        f"At dawn, {culprit.clue_mark} striped the brass rail beside the display shelf. "
        f"The marks were tiny, but they felt like the first knock of a mystery."
    )


def introduce(world: World, apprentice: Entity, sorcerer: Entity, item: Item) -> None:
    world.say(
        f"In the Lantern Tower, {apprentice.id} was the youngest apprentice to the old sorcerer {sorcerer.id}. "
        f"On festival mornings, the two of them always polished the glass hall together."
    )
    world.say(
        f"That day, {item.phrase} waited on a velvet stand and {item.shine}. "
        f"By sunset it was meant to lead the whole tower in a bright procession."
    )


def foreshadow(world: World, apprentice: Entity, culprit: CulpritProfile) -> None:
    apprentice.memes["notice"] += 1
    world.say(foreshadow_line(world.facts["item_cfg"], culprit))
    world.say(
        f'"That is odd," {apprentice.id} thought. "Maybe it matters. Maybe it does not. Still, I should remember it."'
    )


def discover_missing(world: World, apprentice: Entity, sorcerer: Entity, item: Item) -> None:
    item_ent = world.get("item")
    item_ent.meters["missing"] += 1
    apprentice.memes["worry"] += 1
    sorcerer.memes["worry"] += 1
    world.para()
    world.say(
        f"But when the tower bell rang for the feast, the velvet stand was empty. {item.phrase.capitalize()} was gone."
    )
    world.say(
        f'{sorcerer.id} pressed two fingers to {sorcerer.pronoun("possessive")} chin. '
        f'"No broken glass, no scorch mark, no snapped lock," {sorcerer.pronoun()} said. '
        f'"So this was not a smash-and-grab. Someone borrowed magic and forgot courage."'
    )


def inspect_clue(world: World, apprentice: Entity, culprit: CulpritProfile) -> None:
    trace = culprit.clue_mark
    apprentice.memes["suspicion"] += 1
    world.say(
        f"{apprentice.id} knelt by the stand and found {trace} clinging to the edge of the velvet."
    )
    world.say(
        f'"I saw that same sign earlier," {apprentice.id} thought. '
        f'"The mystery started whispering before the item even vanished."'
    )


def question_red_herrings(world: World, apprentice: Entity, culprit_id: str) -> None:
    others = [c for cid, c in CULPRITS.items() if cid != culprit_id]
    first, second = others[0], others[1]
    world.say(
        f"{apprentice.id} checked first on {first.label}, but {first.pronoun('subject')} had a plain answer for the marks around {first.pronoun('object')}: "
        f"{first.worry}. That worry did not fit the missing magic."
    )
    world.say(
        f"Then {apprentice.pronoun('subject')} visited {second.label}. Again there was a clue-shaped explanation, "
        f"but nothing there could have used the stolen power the right way."
    )


def follow_need(world: World, apprentice: Entity, culprit: CulpritProfile, item: Item) -> None:
    apprentice.memes["resolve"] += 1
    world.para()
    world.say(
        f"Then {apprentice.id} followed the trail toward {culprit.use_place}. {culprit.use_scene.capitalize()}, and beside it {item.phrase} {item.use_effect}."
    )
    world.say(
        f'"So it was not taken for meanness," {apprentice.id} thought. '
        f'"It was taken for worry. But worry does not turn borrowing into honesty."'
    )


def confront(world: World, apprentice: Entity, sorcerer: Entity, culprit_ent: Entity, culprit: CulpritProfile, approach: str) -> None:
    culprit_ent.memes["guilt"] += 1
    if approach == "gentle":
        apprentice.memes["kindness"] += 1
        world.say(
            f'{apprentice.id} kept {apprentice.pronoun("possessive")} voice soft. '
            f'"We found the truth," {apprentice.pronoun()} said. "If you were frightened, you could still tell us."'
        )
    else:
        apprentice.memes["sternness"] += 1
        world.say(
            f'{apprentice.id} stood very straight. "The clues lead here," {apprentice.pronoun()} said. '
            f'"The tower needs the truth before the feast begins."'
        )

    reveal = reveal_of(approach, culprit.id)
    world.facts["reveal"] = reveal
    if reveal == "tearful_confession":
        culprit_ent.memes["fear"] += 1
        world.say(
            f"{culprit.label} twisted {culprit_ent.pronoun('possessive')} hands and tears sprang up at once."
        )
    elif reveal == "brisk_confession":
        world.say(
            f"{culprit.label} let out a long breath and looked down at the floor."
        )
    else:
        world.say(
            f"{culprit.label} blinked hard, then nodded as if a heavy stone had finally rolled off {culprit_ent.pronoun('possessive')} chest."
        )

    world.say(
        f'"I took it," {culprit_ent.pronoun()} admitted. "{culprit.apology}"'
    )
    culprit_ent.memes["honesty"] += 1
    culprit_ent.memes["relief"] += 1
    sorcerer.memes["calm"] += 1


def resolve(world: World, apprentice: Entity, sorcerer: Entity, culprit_ent: Entity, culprit: CulpritProfile, item: Item) -> None:
    item_ent = world.get("item")
    item_ent.meters["missing"] = 0.0
    item_ent.meters["returned"] += 1
    apprentice.memes["relief"] += 1
    apprentice.memes["lesson"] += 1
    sorcerer.memes["lesson"] += 1
    world.para()
    world.say(
        f"{sorcerer.id} lifted {item.phrase} and set it back in {culprit.hiding_place} only long enough to show that no one would snatch it away in anger."
    )
    world.say(
        f'Then the sorcerer said, "Helping is good. Hiding is what makes trouble grow. Next time, ask. We share our tools much faster than we solve our hurt feelings."'
    )
    world.say(
        f"{culprit.label} apologized to the whole hall, and {apprentice.id} helped carry the magic where it was needed openly this time."
    )
    world.say(
        f"By evening, {item.phrase} led the lantern walk at the front of the stairs, and the mystery ended not with punishment, but with truth told in the light."
    )


def tell(
    item_cfg: Item,
    culprit_cfg: CulpritProfile,
    approach: str,
    apprentice_name: str,
    apprentice_gender: str,
    sorcerer_name: str,
    sorcerer_gender: str,
) -> World:
    world = World()
    apprentice = world.add(
        Entity(
            id=apprentice_name,
            kind="character",
            type=apprentice_gender,
            role="apprentice",
            label=apprentice_name,
            phrase=apprentice_name,
        )
    )
    sorcerer = world.add(
        Entity(
            id=sorcerer_name,
            kind="character",
            type=sorcerer_gender,
            role="sorcerer",
            label=sorcerer_name,
            phrase=f"the sorcerer {sorcerer_name}",
        )
    )
    culprit = world.add(
        Entity(
            id=culprit_cfg.id,
            kind="character",
            type=culprit_cfg.type,
            role="culprit",
            label=culprit_cfg.label,
            phrase=culprit_cfg.phrase,
            attrs={"timid": culprit_cfg.timid},
            tags=set(culprit_cfg.tags),
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="magic_item",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            attrs={"power": item_cfg.power},
            tags=set(item_cfg.tags),
        )
    )

    world.facts.update(
        apprentice=apprentice,
        sorcerer=sorcerer,
        culprit=culprit,
        culprit_cfg=culprit_cfg,
        item=item,
        item_cfg=item_cfg,
        approach=approach,
    )

    introduce(world, apprentice, sorcerer, item_cfg)
    foreshadow(world, apprentice, culprit_cfg)
    discover_missing(world, apprentice, sorcerer, item_cfg)
    inspect_clue(world, apprentice, culprit_cfg)
    question_red_herrings(world, apprentice, culprit_cfg.id)
    follow_need(world, apprentice, culprit_cfg, item_cfg)
    confront(world, apprentice, sorcerer, culprit, culprit_cfg, approach)
    resolve(world, apprentice, sorcerer, culprit, culprit_cfg, item_cfg)

    world.facts.update(
        solved=True,
        moral="It is good to help, but you must ask and tell the truth.",
        clue=culprit_cfg.clue_mark,
        use_place=culprit_cfg.use_place,
        worry=culprit_cfg.worry,
    )
    return world


KNOWLEDGE = {
    "warm": [
        (
            "What does warm magic do?",
            "Warm magic makes something gently hotter. It can help a cold plant or chilly room, but it should still be used carefully.",
        )
    ],
    "light": [
        (
            "Why is a lantern useful in dark places?",
            "A lantern helps people see where they are going. In a dark room, light can keep work safe and steady.",
        )
    ],
    "unlock": [
        (
            "What does a key do?",
            "A key opens a lock the right way. It helps you enter without forcing or breaking the door.",
        )
    ],
    "truth": [
        (
            "Why is telling the truth important?",
            "Telling the truth helps people solve problems together. Even when you made a mistake, honesty makes trust grow back.",
        )
    ],
    "sorcerer": [
        (
            "What is a sorcerer?",
            "A sorcerer is a person in stories who knows magic. A wise sorcerer uses magic to help and to teach others.",
        )
    ],
    "mystery": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, clues point toward the truth step by step.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sorcerer", "mystery", "warm", "light", "unlock", "truth"]


def generation_prompts(world: World) -> list[str]:
    apprentice = world.facts["apprentice"]
    sorcerer = world.facts["sorcerer"]
    item = world.facts["item_cfg"]
    culprit = world.facts["culprit_cfg"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old that includes the word "sorcerer" and a missing magical object.',
        f"Tell a gentle mystery where {apprentice.id}, an apprentice, helps the sorcerer {sorcerer.id} find {item.phrase} by noticing clues and thinking carefully.",
        f'Write a story with foreshadowing and inner monologue in which the real culprit borrowed magic for a worried reason, then learns that honesty matters more than hiding.',
        f"Make the culprit {culprit.label}, and end with a calm lesson about asking before borrowing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    apprentice = world.facts["apprentice"]
    sorcerer = world.facts["sorcerer"]
    culprit = world.facts["culprit"]
    culprit_cfg = world.facts["culprit_cfg"]
    item = world.facts["item_cfg"]
    approach = world.facts["approach"]
    reveal = world.facts["reveal"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {apprentice.id}, a young apprentice, and the sorcerer {sorcerer.id}. Together they solve the mystery of the missing {item.label}.",
        ),
        (
            f"What was missing from the velvet stand?",
            f"The missing object was {item.phrase}. It was supposed to lead the tower's festival walk that evening.",
        ),
        (
            "What was the foreshadowing clue at the beginning?",
            f"The story first showed {culprit_cfg.clue_mark} near the display shelf before anyone knew the item was gone. That early hint pointed toward the truth later.",
        ),
        (
            f"How did {apprentice.id} solve the mystery?",
            f"{apprentice.id} remembered the first clue, compared it with the marks on the empty stand, and followed the trail to {culprit_cfg.use_place}. There {apprentice.pronoun('subject')} found the missing magic being used to help with {culprit_cfg.worry}.",
        ),
        (
            f"Why did {culprit_cfg.label} take the item?",
            f"{culprit_cfg.label} took it because {culprit_cfg.worry}. The problem was real, but borrowing without asking still made the tower worry and turned help into a mystery.",
        ),
    ]
    if approach == "gentle":
        qa.append(
            (
                f"Why did the culprit tell the truth?",
                f"{apprentice.id} spoke kindly, so {culprit_cfg.label} felt safe enough to confess. The calm approach let honesty come out without a bigger scene.",
            )
        )
    elif reveal == "tearful_confession":
        qa.append(
            (
                "What happened when the apprentice sounded stern?",
                f"The stern voice made {culprit_cfg.label} cry before confessing. {culprit.pronoun('subject').capitalize()} was already guilty and frightened, so the truth came out in tears.",
            )
        )
    else:
        qa.append(
            (
                "What happened when the apprentice sounded stern?",
                f"{culprit_cfg.label} gave a quick, serious confession. The strong tone showed the mystery had reached its end, so hiding no longer seemed worth it.",
            )
        )
    qa.append(
        (
            "What lesson did the sorcerer teach?",
            "The sorcerer taught that helping others is good, but you must ask before borrowing and tell the truth quickly. Kindness and honesty work better together than secrecy.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item = world.facts["item_cfg"]
    tags = {"sorcerer", "mystery", "truth"}
    if item.power == "warm":
        tags.add("warm")
    elif item.power == "glow":
        tags.add("light")
    elif item.power == "unlock":
        tags.add("unlock")
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
            shown = {k: v for k, v in ent.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: reveal={world.facts.get('reveal')} clue={world.facts.get('clue')}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(I, C) :- item(I), culprit(C), power(I, P), needs(C, P).

soft_confession :- approach(gentle).
tearful_confession :- approach(stern), chosen_culprit(C), timid(C).
brisk_confession :- approach(stern), chosen_culprit(C), not timid(C).

reveal(soft_confession) :- soft_confession.
reveal(tearful_confession) :- tearful_confession.
reveal(brisk_confession) :- brisk_confession.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("power", item_id, item.power))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("needs", culprit_id, culprit.need_power))
        if culprit.timid:
            lines.append(asp.fact("timid", culprit_id))
    for approach_id in sorted(APPROACHES):
        lines.append(asp.fact("approach_name", approach_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reveal(approach: str, culprit_id: str) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("approach", approach),
            asp.fact("chosen_culprit", culprit_id),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show reveal/1."))
    atoms = asp.atoms(model, "reveal")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a sorcerer, a missing magical object, and a small whodunit with a moral about honesty."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--approach", choices=sorted(APPROACHES), help="how the apprentice speaks when the truth is found")
    ap.add_argument("--apprentice-name")
    ap.add_argument("--apprentice-gender", choices=["girl", "boy"])
    ap.add_argument("--sorcerer-name")
    ap.add_argument("--sorcerer-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (item, culprit) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.culprit:
        if (args.item, args.culprit) not in valid_combos():
            raise StoryError(explain_rejection(args.item, args.culprit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.culprit is None or combo[1] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, culprit_id = rng.choice(combos)
    apprentice_gender = args.apprentice_gender or rng.choice(["girl", "boy"])
    apprentice_name = args.apprentice_name or rng.choice(GIRL_NAMES if apprentice_gender == "girl" else BOY_NAMES)
    sorcerer_gender = args.sorcerer_gender or rng.choice(["woman", "man"])
    sorcerer_name = args.sorcerer_name or rng.choice([n for n in SORCERER_NAMES if n != apprentice_name])
    approach = args.approach or rng.choice(sorted(APPROACHES))
    return StoryParams(
        item=item_id,
        culprit=culprit_id,
        approach=approach,
        apprentice_name=apprentice_name,
        apprentice_gender=apprentice_gender,
        sorcerer_name=sorcerer_name,
        sorcerer_gender=sorcerer_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")
    if (params.item, params.culprit) not in valid_combos():
        raise StoryError(explain_rejection(params.item, params.culprit))

    world = tell(
        item_cfg=ITEMS[params.item],
        culprit_cfg=CULPRITS[params.culprit],
        approach=params.approach,
        apprentice_name=params.apprentice_name,
        apprentice_gender=params.apprentice_gender,
        sorcerer_name=params.sorcerer_name,
        sorcerer_gender=params.sorcerer_gender,
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

    reveal_cases = [
        ("gentle", "gardener"),
        ("stern", "gardener"),
        ("stern", "baker"),
        ("gentle", "librarian"),
    ]
    mismatches = []
    for approach, culprit_id in reveal_cases:
        py = reveal_of(approach, culprit_id)
        asp_val = asp_reveal(approach, culprit_id)
        if py != asp_val:
            mismatches.append((approach, culprit_id, py, asp_val))
    if not mismatches:
        print("OK: ASP reveal model matches Python reveal_of().")
    else:
        rc = 1
        print("MISMATCH in reveal model:")
        for row in mismatches:
            print(" ", row)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        if "sorcerer" not in smoke.story.lower():
            raise StoryError('(Smoke test failed: story did not include the required word "sorcerer".)')
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show reveal/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, culprit) combos:\n")
        for item_id, culprit_id in combos:
            print(f"  {item_id:16} {culprit_id}")
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
            header = f"### {p.item} / {p.culprit} / {p.approach}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
