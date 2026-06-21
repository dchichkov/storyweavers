#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/baffle_indignation_sew_suspense_happy_ending_misunderstanding.py
================================================================================================

A standalone story world for a rhyming, child-facing tale about a small
misunderstanding: a child sees secret sewing, grows puzzled and indignant, and
fears a beloved item is being spoiled or stolen. In truth, a caring friend or
grown-up is quietly mending it in time for a special event. The suspense comes
from hidden clues and a delayed reveal; the ending is happy and proves what
changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/baffle_indignation_sew_suspense_happy_ending_misunderstanding.py
    python storyworlds/worlds/gpt-5.4/baffle_indignation_sew_suspense_happy_ending_misunderstanding.py --theme parade --item cape
    python storyworlds/worlds/gpt-5.4/baffle_indignation_sew_suspense_happy_ending_misunderstanding.py --damage muddy
    python storyworlds/worlds/gpt-5.4/baffle_indignation_sew_suspense_happy_ending_misunderstanding.py --all --qa
    python storyworlds/worlds/gpt-5.4/baffle_indignation_sew_suspense_happy_ending_misunderstanding.py --verify
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
    repair_skill: bool = False
    sewable: bool = False
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
class Theme:
    id: str
    room: str
    event: str
    chant: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SewItem:
    id: str
    label: str
    phrase: str
    use_line: str
    proof_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Damage:
    id: str
    label: str
    mendable: bool
    clue: str
    repair_line: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hider:
    id: str
    type: str
    title: str
    manner: str
    can_sew: bool
    comfort_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RevealSpot:
    id: str
    label: str
    whisper_line: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    owner = world.entities.get("owner")
    item = world.entities.get("item")
    if owner is None or item is None:
        return out
    if owner.memes["suspicion"] < THRESHOLD:
        return out
    if item.meters["hidden"] < THRESHOLD:
        return out
    sig = ("worry", owner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["fear"] += 1
    out.append("__worry__")
    return out


def _r_indignation(world: World) -> list[str]:
    out: list[str] = []
    owner = world.entities.get("owner")
    item = world.entities.get("item")
    if owner is None or item is None:
        return out
    if owner.memes["fear"] < THRESHOLD:
        return out
    if item.meters["snipped"] < THRESHOLD:
        return out
    sig = ("indignation", owner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["indignation"] += 1
    out.append("__indignation__")
    return out


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    item = world.entities.get("item")
    if helper is None or item is None:
        return out
    if helper.meters["sewing"] < THRESHOLD:
        return out
    if item.meters["torn"] < THRESHOLD:
        return out
    if item.meters["mended"] >= THRESHOLD:
        return out
    sig = ("mend", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["mended"] += 1
    item.meters["torn"] = 0.0
    out.append("__mended__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    owner = world.entities.get("owner")
    helper = world.entities.get("helper")
    item = world.entities.get("item")
    if owner is None or helper is None or item is None:
        return out
    if item.meters["mended"] < THRESHOLD:
        return out
    if owner.memes["understands"] < THRESHOLD:
        return out
    sig = ("relief", owner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["fear"] = 0.0
    owner.memes["indignation"] = 0.0
    owner.memes["joy"] += 1
    helper.memes["care"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="indignation", tag="emotional", apply=_r_indignation),
    Rule(name="mend", tag="physical", apply=_r_mend),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


def can_make_story(item: SewItem, damage: Damage, hider: Hider) -> bool:
    return damage.mendable and hider.can_sew


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for item_id, item in ITEMS.items():
            for damage_id, damage in DAMAGES.items():
                for hider_id, hider in HIDERS.items():
                    if can_make_story(item, damage, hider):
                        combos.append((theme_id, item_id, damage_id, hider_id))
    return combos


def explain_rejection(item: SewItem, damage: Damage, hider: Hider) -> str:
    if not damage.mendable:
        return (
            f"(No story: {damage.label} would not be fixed by sewing. "
            f"A story in this world needs a real reason to sew {item.label}.)"
        )
    if not hider.can_sew:
        return (
            f"(No story: {hider.title} is not a sewing helper in this world, so "
            f"there is no sensible hidden repair to reveal.)"
        )
    return "(No story: this combination does not support the sewing misunderstanding.)"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    owner = sim.get("owner")
    item = sim.get("item")
    owner.memes["suspicion"] += 1
    item.meters["hidden"] += 1
    item.meters["snipped"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": owner.memes["fear"],
        "indignation": owner.memes["indignation"],
    }


def introduce(world: World, owner: Entity, theme: Theme, item: Entity) -> None:
    owner.memes["joy"] += 1
    owner.memes["love"] += 1
    world.say(
        f"In {theme.room}, soft as a tune, {owner.id} hummed to the afternoon moon. "
        f"{owner.pronoun().capitalize()} twirled with {item.phrase}, light as a scrape, "
        f"for soon came {theme.event} and {theme.chant}."
    )


def show_damage(world: World, owner: Entity, item: Entity, damage: Damage) -> None:
    item.meters["torn"] += 1
    world.say(
        f"But oh, what a wobble, what troublesome news: {damage.clue}. "
        f"{owner.id} went still in {owner.pronoun('possessive')} bright little shoes."
    )


def promise_to_fetch(world: World, helper: Entity, owner: Entity, spot: RevealSpot) -> None:
    helper.memes["care"] += 1
    world.say(
        f'"Wait here just a minute," said {helper.id} with a grin, '
        f'and slipped toward {spot.label} where the lamplight was thin.'
    )


def hide_and_sew(world: World, helper: Entity, item: Entity, spot: RevealSpot, damage: Damage) -> None:
    helper.meters["sewing"] += 1
    item.meters["hidden"] += 1
    item.meters["snipped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Behind {spot.label}, {helper.id} bent low in a row, "
        f"with a hush and a needle and thread in a glow. "
        f"{spot.whisper_line} {damage.repair_line}"
    )


def misunderstand(world: World, owner: Entity, helper: Entity, item: Entity, damage: Damage) -> None:
    pred = predict_trouble(world)
    owner.memes["suspicion"] += 1
    propagate(world, narrate=False)
    baffled = "baffle" if pred["fear"] >= THRESHOLD else "puzzle"
    indignation = "A spark of indignation hopped up in a flash." if pred["indignation"] >= THRESHOLD else ""
    world.say(
        f"{owner.id} peeked once and gasped at the sight. "
        f'"Oh dear, what a {baffled}! Something is not right!" '
        f"{owner.pronoun().capitalize()} saw a bright snip and a quick silver gleam, "
        f"and feared {helper.id} might spoil {item.label} and {owner.pronoun('possessive')} dream. "
        f"{indignation}"
    )
    world.say(
        f'"Please do not cut it!" cried {owner.id}. "{damage.label.capitalize()} or no, '
        f'I love it too much to just let it go!"'
    )


def pause_before_reveal(world: World, helper: Entity, owner: Entity) -> None:
    world.say(
        f"For one tiny heartbeat the room felt tight. "
        f"{helper.id} looked up softly, not cross and not spiteful, just bright."
    )


def reveal(world: World, helper: Entity, owner: Entity, item: Entity, damage: Damage, theme: Theme) -> None:
    owner.memes["understands"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I would never spoil it," said {helper.id}. "I wanted to sew '
        f'you a fix as a sweet little surprise before {theme.event}." '
        f"{damage.reveal_line}"
    )
    world.say(
        f"{helper.id} held up {item.phrase}, neat as could be. "
        f"The stitches sat snug as a bee in a tree."
    )


def comfort_and_end(world: World, helper: Entity, owner: Entity, item: Entity, theme: Theme, hider: Hider) -> None:
    world.say(
        f"{owner.id}'s cheeks turned pink, then light as the sun. "
        f"{hider.comfort_line} The misunderstanding melted and ran."
    )
    world.say(
        f"Soon {owner.id} wore {item.label} with a skip and a sway. "
        f"{item.attrs['proof_line']} {theme.closing}"
    )


def tell(
    theme: Theme,
    item_cfg: SewItem,
    damage: Damage,
    hider: Hider,
    spot: RevealSpot,
    owner_name: str = "Mina",
    owner_type: str = "girl",
    helper_name: str = "Nell",
) -> World:
    world = World()
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_type, role="owner"))
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=hider.type,
            role="helper",
            label=hider.title,
            repair_skill=hider.can_sew,
            attrs={"manner": hider.manner},
            tags=set(hider.tags),
        )
    )
    item = world.add(
        Entity(
            id="item",
            type="item",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="beloved_item",
            sewable=True,
            attrs={"use_line": item_cfg.use_line, "proof_line": item_cfg.proof_line},
            tags=set(item_cfg.tags),
        )
    )
    world.facts["theme"] = theme
    world.facts["item_cfg"] = item_cfg
    world.facts["damage"] = damage
    world.facts["hider_cfg"] = hider
    world.facts["spot"] = spot

    introduce(world, owner, theme, item)
    show_damage(world, owner, item, damage)

    world.para()
    promise_to_fetch(world, helper, owner, spot)
    hide_and_sew(world, helper, item, spot, damage)
    misunderstand(world, owner, helper, item, damage)

    world.para()
    pause_before_reveal(world, helper, owner)
    reveal(world, helper, owner, item, damage, theme)
    comfort_and_end(world, helper, owner, item, theme, hider)

    world.facts.update(
        owner=owner,
        helper=helper,
        item=item,
        repaired=item.meters["mended"] >= THRESHOLD,
        feared=owner.memes["fear"] >= THRESHOLD,
        indignant=owner.memes["indignation"] >= THRESHOLD,
        understood=owner.memes["understands"] >= THRESHOLD,
    )
    return world


THEMES = {
    "parade": Theme(
        id="parade",
        room="the dress-up room",
        event="the moon parade",
        chant="they would swish in a silver cape",
        closing="Out they went laughing, no longer undone, and the moon parade shimmered with song and fun.",
        tags={"parade", "moon"},
    ),
    "play": Theme(
        id="play",
        room="the play corner",
        event="the puppet play",
        chant="they would bow in a brave little show",
        closing="Then the puppet play sparkled from beginning to end, with claps for the costume and cheers for the friend.",
        tags={"play", "puppet"},
    ),
    "picnic": Theme(
        id="picnic",
        room="the sunny kitchen",
        event="the berry picnic",
        chant="they would twirl with a ribboned apron",
        closing="Then off to the picnic they skipped through the day, with crumbs, songs, and giggles all bright on the way.",
        tags={"picnic", "berries"},
    ),
}

ITEMS = {
    "cape": SewItem(
        id="cape",
        label="cape",
        phrase="a silver cape",
        use_line="it would swoosh behind every grand parade leap",
        proof_line="The cape swooshed behind her in one shining sweep.",
        tags={"cape", "cloth"},
    ),
    "puppet": SewItem(
        id="puppet",
        label="puppet cloak",
        phrase="a tiny velvet puppet cloak",
        use_line="it would flutter when the puppet bowed on stage",
        proof_line="The puppet cloak fluttered each time it took a bow.",
        tags={"puppet", "cloth"},
    ),
    "apron": SewItem(
        id="apron",
        label="apron",
        phrase="a ribboned apron",
        use_line="it would keep berry juice off her dress at the picnic",
        proof_line="The apron bobbed as she poured out the tea.",
        tags={"apron", "cloth"},
    ),
}

DAMAGES = {
    "tear": Damage(
        id="tear",
        label="tear",
        mendable=True,
        clue="A small tear showed up by the hem with a sigh",
        repair_line="The torn place lay open where a neat seam would go.",
        reveal_line="There by the hem, where the tear used to be, ran a tiny new seam, neat as neatness could be.",
        tags={"tear", "sew"},
    ),
    "loose_hem": Damage(
        id="loose_hem",
        label="loose hem",
        mendable=True,
        clue="Its hem had come floppy and droopy and wide",
        repair_line="A loose little hem needed tucks on the side.",
        reveal_line="The hem sat smooth now, with no floppy flap, just a tidy sewn edge all snug in its lap.",
        tags={"hem", "sew"},
    ),
    "missing_button": Damage(
        id="missing_button",
        label="missing button",
        mendable=True,
        clue="A button had popped and gone rolling away",
        repair_line="A round little button was waiting to stay.",
        reveal_line="A bright little button now winked in its place, stitched on with a smile and a tiny round face.",
        tags={"button", "sew"},
    ),
    "muddy": Damage(
        id="muddy",
        label="muddy stain",
        mendable=False,
        clue="A muddy brown blotch had splashed on the side",
        repair_line="But thread could not wash what the puddles had spread.",
        reveal_line="No stitch could make mud into clean cloth instead.",
        tags={"mud", "wash"},
    ),
}

HIDERS = {
    "sister": Hider(
        id="sister",
        type="girl",
        title="sister",
        manner="quick and gentle",
        can_sew=True,
        comfort_line='"I am sorry I shouted," said {owner}. "I did not understand." "I know," said {helper}, "and now it is grand."',
        tags={"sibling", "sew"},
    ),
    "grandma": Hider(
        id="grandma",
        type="woman",
        title="grandma",
        manner="slow and kind",
        can_sew=True,
        comfort_line='"I am sorry I shouted," said {owner}. Grandma smiled. "A worried heart can leap a long mile."',
        tags={"grandma", "sew"},
    ),
    "brother": Hider(
        id="brother",
        type="boy",
        title="brother",
        manner="careful and proud",
        can_sew=True,
        comfort_line='"I am sorry I shouted," said {owner}. "{helper}, I was wrong." "{owner}," said {helper}, "the fix was my song."',
        tags={"sibling", "sew"},
    ),
    "cat": Hider(
        id="cat",
        type="thing",
        title="cat",
        manner="pouncy",
        can_sew=False,
        comfort_line='',
        tags={"cat"},
    ),
}

SPOTS = {
    "curtain": RevealSpot(
        id="curtain",
        label="the blue curtain",
        whisper_line="There came a hush-hush rustle, a click, and then slow,",
        tags={"curtain"},
    ),
    "table": RevealSpot(
        id="table",
        label="the round table",
        whisper_line="Under the round table came snip after snip,",
        tags={"table"},
    ),
    "rocker": RevealSpot(
        id="rocker",
        label="the old rocker",
        whisper_line="By the old rocker came thread through the cloth, soft and low,",
        tags={"rocker"},
    ),
}


@dataclass
class StoryParams:
    theme: str
    item: str
    damage: str
    hider: str
    spot: str
    owner_name: str
    owner_type: str
    helper_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="parade",
        item="cape",
        damage="tear",
        hider="sister",
        spot="curtain",
        owner_name="Mina",
        owner_type="girl",
        helper_name="Nell",
    ),
    StoryParams(
        theme="play",
        item="puppet",
        damage="loose_hem",
        hider="grandma",
        spot="rocker",
        owner_name="Pip",
        owner_type="boy",
        helper_name="Grandma May",
    ),
    StoryParams(
        theme="picnic",
        item="apron",
        damage="missing_button",
        hider="brother",
        spot="table",
        owner_name="Lila",
        owner_type="girl",
        helper_name="Tess",
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Poppy", "Nora", "Elsie", "June", "Tia", "Ruby"]
BOY_NAMES = ["Pip", "Owen", "Milo", "Theo", "Evan", "Noel", "Luca", "Ben"]

KNOWLEDGE = {
    "sew": [
        (
            "What does it mean to sew something?",
            "To sew means to join cloth with thread, usually using a needle. Sewing can fix a tear or hold a button in place."
        )
    ],
    "tear": [
        (
            "What is a tear in cloth?",
            "A tear is a rip in fabric where the cloth has pulled apart. If someone sews it, the edges can be joined again."
        )
    ],
    "hem": [
        (
            "What is a hem?",
            "A hem is the folded edge at the bottom of a piece of cloth. Sewing keeps the edge neat so it does not flop open."
        )
    ],
    "button": [
        (
            "What does a button do on clothes?",
            "A button helps hold parts of clothing closed or in place. If a button falls off, someone can sew a new one on."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something is wrong but has not understood the real reason yet. Talking kindly can clear it up."
        )
    ],
    "surprise": [
        (
            "Why might someone hide a kind surprise?",
            "Sometimes people hide a kind surprise because they want the reveal to feel special. The hiding is not mean when the secret is meant to help."
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is a cheerful line of people moving along together, often with music, costumes, or waving. People dress up to look bright and festive."
        )
    ],
    "puppet": [
        (
            "What is a puppet?",
            "A puppet is a toy figure that someone moves with a hand or strings to act like it is alive. Clothes on a puppet can be sewn too."
        )
    ],
    "apron": [
        (
            "What is an apron for?",
            "An apron is a cloth you wear over your clothes to help keep them cleaner while you cook, paint, or serve food."
        )
    ],
}
KNOWLEDGE_ORDER = ["sew", "tear", "hem", "button", "misunderstanding", "surprise", "parade", "puppet", "apron"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    helper = f["helper"]
    theme = f["theme"]
    item = f["item"]
    damage = f["damage"]
    return [
        'Write a rhyming story for a 3-to-5-year-old that includes the word "baffle" and the word "sew".',
        f"Tell a gentle suspense story where {owner.id} misunderstands secret sewing and feels indignation, but {helper.id} is really fixing a {damage.label} in {item.label} before {theme.event}.",
        f"Write a child-facing rhyme about a misunderstanding that turns into a happy ending, ending with {item.label} ready for {theme.event}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    helper = f["helper"]
    theme = f["theme"]
    item = f["item"]
    damage = f["damage"]
    hider_cfg = f["hider_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id}, who loved {item.label}, and {helper.id}, who quietly tried to help. The story follows their misunderstanding before {theme.event}."
        ),
        (
            f"What problem did {item.label} have?",
            f"The {item.label} had a {damage.label}. That mattered because {owner.id} wanted to wear it for {theme.event}."
        ),
        (
            f"Why did {owner.id} feel worried and indignant?",
            f"{owner.id} peeked in and saw hidden sewing, a bright snip, and a secretive scene. Without knowing the plan, {owner.pronoun()} thought {helper.id} might be ruining the {item.label}, so worry jumped into indignation."
        ),
        (
            f"What was {helper.id} really doing?",
            f"{helper.id} was trying to sew the {item.label} back into good shape. The hiding was part of a kind surprise, not a mean trick."
        ),
    ]
    if f.get("repaired"):
        qa.append(
            (
                "How was the misunderstanding solved?",
                f"{helper.id} explained the truth and showed the repaired {item.label}. Once {owner.id} understood the real reason for the hidden sewing, the fear melted into relief."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily, with the {item.label} mended and ready for {theme.event}. The ending image proves the change because {owner.id} could wear it proudly instead of fearing it was lost."
        )
    )
    if hider_cfg.id in {"sister", "brother", "grandma"}:
        qa.append(
            (
                f"Was {helper.id} trying to be unkind?",
                f"No. {helper.id} was being caring and patient, even after the misunderstanding. The sewing was meant to help {owner.id}, not to upset {owner.pronoun('object')}."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"misunderstanding", "surprise"}
    tags |= set(f["damage"].tags)
    tags |= set(f["theme"].tags)
    tags |= set(f["item_cfg"].tags)
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
    for ent in world.entities.values():
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
        flags = [name for name, on in (("repair_skill", ent.repair_skill), ("sewable", ent.sewable)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonable story gate:
valid(T, I, D, H) :- theme(T), item(I), damage(D), hider(H), mendable(D), can_sew(H).

% End-state inference for this world:
repair_happens :- chosen_damage(D), mendable(D), chosen_hider(H), can_sew(H).
story_possible :- repair_happens.
#defined story_possible.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for damage_id, damage in DAMAGES.items():
        lines.append(asp.fact("damage", damage_id))
        if damage.mendable:
            lines.append(asp.fact("mendable", damage_id))
    for hider_id, hider in HIDERS.items():
        lines.append(asp.fact("hider", hider_id))
        if hider.can_sew:
            lines.append(asp.fact("can_sew", hider_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_possible(params: StoryParams) -> bool:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_damage", params.damage),
            asp.fact("chosen_hider", params.hider),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show story_possible/0."))
    return bool(asp.atoms(model, "story_possible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    rng = random.Random(7)
    for _ in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        possible_py = can_make_story(ITEMS[params.item], DAMAGES[params.damage], HIDERS[params.hider])
        possible_asp = asp_story_possible(params)
        if possible_py != possible_asp:
            bad += 1
    if bad == 0:
        print(f"OK: ASP story_possible agrees with Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} story_possible results differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming sewing misunderstanding storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--hider", choices=HIDERS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--owner-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
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


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.damage and args.hider:
        item_probe = ITEMS[args.item] if args.item else next(iter(ITEMS.values()))
        if not can_make_story(item_probe, DAMAGES[args.damage], HIDERS[args.hider]):
            raise StoryError(explain_rejection(item_probe, DAMAGES[args.damage], HIDERS[args.hider]))
    if args.hider and not HIDERS[args.hider].can_sew:
        item_probe = ITEMS[args.item] if args.item else next(iter(ITEMS.values()))
        damage_probe = DAMAGES[args.damage] if args.damage else next(iter(DAMAGES.values()))
        raise StoryError(explain_rejection(item_probe, damage_probe, HIDERS[args.hider]))
    if args.damage and not DAMAGES[args.damage].mendable:
        item_probe = ITEMS[args.item] if args.item else next(iter(ITEMS.values()))
        hider_probe = HIDERS[args.hider] if args.hider else next(iter(HIDERS.values()))
        raise StoryError(explain_rejection(item_probe, DAMAGES[args.damage], hider_probe))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.item is None or combo[1] == args.item)
        and (args.damage is None or combo[2] == args.damage)
        and (args.hider is None or combo[3] == args.hider)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, item_id, damage_id, hider_id = rng.choice(sorted(combos))
    spot_id = args.spot or rng.choice(sorted(SPOTS))
    owner_type = args.gender or rng.choice(["girl", "boy"])
    owner_name = args.owner_name or choose_name(rng, owner_type)
    helper_defaults = {
        "sister": ("girl", rng.choice([n for n in GIRL_NAMES if n != owner_name] or GIRL_NAMES)),
        "brother": ("boy", rng.choice([n for n in BOY_NAMES if n != owner_name] or BOY_NAMES)),
        "grandma": ("woman", "Grandma May"),
    }
    helper_name = args.helper_name
    if helper_name is None:
        helper_name = helper_defaults.get(hider_id, ("thing", "Patch"))[1]

    return StoryParams(
        theme=theme_id,
        item=item_id,
        damage=damage_id,
        hider=hider_id,
        spot=spot_id,
        owner_name=owner_name,
        owner_type=owner_type,
        helper_name=helper_name,
    )


def _validated_lookup(mapping: dict, key: str, field_name: str):
    if key not in mapping:
        raise StoryError(f"(Invalid {field_name}: {key})")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    theme = _validated_lookup(THEMES, params.theme, "theme")
    item_cfg = _validated_lookup(ITEMS, params.item, "item")
    damage = _validated_lookup(DAMAGES, params.damage, "damage")
    hider = _validated_lookup(HIDERS, params.hider, "hider")
    spot = _validated_lookup(SPOTS, params.spot, "spot")
    if not can_make_story(item_cfg, damage, hider):
        raise StoryError(explain_rejection(item_cfg, damage, hider))

    world = tell(
        theme=theme,
        item_cfg=item_cfg,
        damage=damage,
        hider=hider,
        spot=spot,
        owner_name=params.owner_name,
        owner_type=params.owner_type,
        helper_name=params.helper_name,
    )

    owner = world.facts["owner"]
    helper = world.facts["helper"]
    hider_cfg = world.facts["hider_cfg"]
    comfort_line = hider_cfg.comfort_line.format(owner=owner.id, helper=helper.id)

    story = world.render().replace(hider_cfg.comfort_line, comfort_line)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/4.\n#show story_possible/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, item, damage, hider) combos:\n")
        for theme_id, item_id, damage_id, hider_id in combos:
            print(f"  {theme_id:8} {item_id:8} {damage_id:14} {hider_id}")
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
            header = f"### {p.owner_name}: {p.item} with {p.damage} ({p.theme}, helper: {p.hider})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
