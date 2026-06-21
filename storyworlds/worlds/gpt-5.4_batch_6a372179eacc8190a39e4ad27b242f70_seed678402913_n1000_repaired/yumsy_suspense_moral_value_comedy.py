#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yumsy_suspense_moral_value_comedy.py
===============================================================

A standalone storyworld about a child, a tempting snack, and the funny suspense
of trying to hide a small mistake. The moral center is honesty: when something
goes wrong, telling the truth helps people fix it together.

Seed constraints:
- include the word "yumsy"
- use suspense and moral value
- keep the tone close to comedy

Run it
------
python storyworlds/worlds/gpt-5.4/yumsy_suspense_moral_value_comedy.py
python storyworlds/worlds/gpt-5.4/yumsy_suspense_moral_value_comedy.py --tray buns --guest teacher
python storyworlds/worlds/gpt-5.4/yumsy_suspense_moral_value_comedy.py --cover napkin --response ignore
python storyworlds/worlds/gpt-5.4/yumsy_suspense_moral_value_comedy.py --all
python storyworlds/worlds/gpt-5.4/yumsy_suspense_moral_value_comedy.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/yumsy_suspense_moral_value_comedy.py --trace
python storyworlds/worlds/gpt-5.4/yumsy_suspense_moral_value_comedy.py --json
python storyworlds/worlds/gpt-5.4/yumsy_suspense_moral_value_comedy.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    edible: bool = False
    coverable: bool = False
    replaceable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
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
class TrayKind:
    id: str
    label: str
    phrase: str
    single: str
    smell: str
    crumbs: str
    extra: str
    plural: bool = True
    replaceable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class GuestKind:
    id: str
    label: str
    phrase: str
    reason: str
    arrival_sound: str
    thanks: str
    type: str = "guest"
    tags: set[str] = field(default_factory=set)


@dataclass
class CoverKind:
    id: str
    label: str
    phrase: str
    works_on_tray: bool
    funny_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ResponseKind:
    id: str
    sense: int
    power: int
    text: str
    confession_text: str
    fix_text: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_causes_suspense(world: World) -> list[str]:
    out: list[str] = []
    tray = world.get("tray")
    child = world.get("child")
    if tray.meters["missing_piece"] < THRESHOLD:
        return out
    sig = ("suspense", "tray")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tray.memes["noticed_odd"] += 1
    child.memes["worry"] += 1
    out.append("__suspense__")
    return out


def _r_crumbs_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["crumbs_on_face"] < THRESHOLD:
        return out
    sig = ("reveal", "crumbs")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["caught"] += 1
    world.get("adult").modes = "not used" if False else "not used"
    out.append("__reveal__")
    return out


def _r_confession_brings_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["honest"] < THRESHOLD:
        return out
    sig = ("relief", "honest")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    world.get("adult").memes["trust"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_causes_suspense", tag="social", apply=_r_missing_causes_suspense),
    Rule(name="crumbs_reveal", tag="social", apply=_r_crumbs_reveal),
    Rule(name="confession_brings_relief", tag="social", apply=_r_confession_brings_relief),
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


def valid_combo(tray: TrayKind, guest: GuestKind, cover: CoverKind) -> bool:
    return tray.replaceable and cover.works_on_tray and bool(guest.reason)


def sensible_responses() -> list[ResponseKind]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> ResponseKind:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def outcome_of(params: "StoryParams") -> str:
    response = RESPONSES[params.response]
    if response.power >= 2:
        return "confessed"
    return "discovered"


def explain_cover(cover: CoverKind) -> str:
    return (
        f"(No story: {cover.phrase} would not really cover a snack tray, so it "
        f"cannot create the funny suspense of a child trying to hide a missing piece.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). A small mistake is best handled by "
        f"honesty, not by pretending nothing happened. Try: {better}.)"
    )


def predict_discovery(world: World) -> dict:
    sim = world.copy()
    tray = sim.get("tray")
    child = sim.get("child")
    tray.meters["missing_piece"] += 1
    child.meters["crumbs_on_face"] += 1
    propagate(sim, narrate=False)
    return {
        "odd_tray": tray.memes["noticed_odd"] >= THRESHOLD,
        "caught": child.memes["caught"] >= THRESHOLD,
        "worry": child.memes["worry"],
    }


def introduce(world: World, child: Entity, adult: Entity, tray_cfg: TrayKind, guest_cfg: GuestKind) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {child.id} helped {child.pronoun('possessive')} "
        f"{adult.label_word} carry {tray_cfg.phrase} onto the kitchen table."
    )
    world.say(
        f"The whole room smelled {tray_cfg.smell}, so {child.id} whispered the family's "
        f"funniest word for a good smell: \"yumsy.\""
    )
    world.say(
        f"These treats were for {guest_cfg.phrase}, because {guest_cfg.reason}."
    )


def warning(world: World, child: Entity, adult: Entity, tray_cfg: TrayKind) -> None:
    child.memes["tempted"] += 1
    world.say(
        f'"Please wait till our guest comes," {adult.label_word} said. '
        f'"Then everyone can have {tray_cfg.single} together."'
    )


def temptation(world: World, child: Entity, tray_cfg: TrayKind) -> None:
    child.memes["hunger"] += 1
    world.say(
        f"{child.id} nodded, but the {tray_cfg.label} sat there smelling so "
        f"{tray_cfg.smell} that waiting suddenly felt very long."
    )


def sneak_bite(world: World, child: Entity, tray_cfg: TrayKind) -> None:
    tray = world.get("tray")
    tray.meters["missing_piece"] += 1
    child.meters["crumbs_on_face"] += 1
    child.meters["sticky_fingers"] += 1
    child.memes["guilt"] += 1
    world.say(
        f"At last {child.id} glanced left, glanced right, and nibbled {tray_cfg.single}."
    )
    world.say(
        f"It was warm and {tray_cfg.smell}. It was also a terrible time for a crumb to land right on {child.pronoun('possessive')} nose."
    )
    propagate(world, narrate=False)


def hide_attempt(world: World, child: Entity, cover_cfg: CoverKind, tray_cfg: TrayKind, guest_cfg: GuestKind) -> None:
    pred = predict_discovery(world)
    world.facts["predicted_odd_tray"] = pred["odd_tray"]
    world.facts["predicted_caught"] = pred["caught"]
    child.memes["worry"] += pred["worry"]
    world.say(
        f'{child.id} tried to hide the empty spot with {cover_cfg.phrase}. '
        f"{cover_cfg.funny_line}"
    )
    world.say(
        f"Then came {guest_cfg.arrival_sound}. {child.id}'s tummy gave a tiny flip."
    )


def confess(world: World, child: Entity, adult: Entity, response_cfg: ResponseKind, tray_cfg: TrayKind) -> None:
    child.memes["honest"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Before anyone sat down, {child.id} blurted, "{response_cfg.confession_text}"'
    )
    world.say(
        f"{adult.label_word.capitalize()} looked at the crumbs on {child.pronoun('possessive')} face and had to smile."
    )
    world.say(response_cfg.text)
    world.say(
        f"Together they {response_cfg.fix_text.format(extra=tray_cfg.extra)}."
    )


def discovered(world: World, child: Entity, adult: Entity, guest: Entity, response_cfg: ResponseKind, tray_cfg: TrayKind) -> None:
    child.memes["caught"] += 1
    child.memes["worry"] += 1
    world.say(
        f"But when {guest.label} peeked under the cover, everyone saw the odd empty place at once."
    )
    world.say(
        f'The crumb on {child.id}\'s nose wiggled when {child.pronoun()} swallowed. That was clue enough.'
    )
    world.say(response_cfg.text)
    child.memes["honest"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I ate one," {child.id} admitted in a small voice.'
    )
    world.say(
        f"Then they {response_cfg.fix_text.format(extra=tray_cfg.extra)}."
    )


def ending(world: World, child: Entity, guest_cfg: GuestKind, tray_cfg: TrayKind, outcome: str) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    if outcome == "confessed":
        world.say(
            f"When the plate came back around, {guest_cfg.thanks} and {child.id} got a smaller but still very yumsy share."
        )
        world.say(
            f"The funniest thing was that the scary part ended the moment {child.pronoun()} told the truth."
        )
    else:
        world.say(
            f"{guest_cfg.thanks}, and soon even {child.id} gave a sheepish little laugh."
        )
        world.say(
            "The secret had felt huge in silence, but once the truth came out, it turned into a fixable little problem."
        )
    world.say(
        f"After that, whenever something smelled too good to wait for, {child.id} remembered that honesty works faster than hiding crumbs."
    )


def tell(
    tray_cfg: TrayKind,
    guest_cfg: GuestKind,
    cover_cfg: CoverKind,
    response_cfg: ResponseKind,
    *,
    child_name: str = "Milo",
    child_gender: str = "boy",
    adult_type: str = "mother",
    trait: str = "silly",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        label=f"the {adult_type}",
        role="adult",
    ))
    guest = world.add(Entity(
        id="Guest",
        kind="character",
        type=guest_cfg.type,
        label=guest_cfg.label,
        phrase=guest_cfg.phrase,
        role="guest",
        tags=set(guest_cfg.tags),
    ))
    tray = world.add(Entity(
        id="tray",
        kind="thing",
        type="tray",
        label=tray_cfg.label,
        phrase=tray_cfg.phrase,
        role="tray",
        edible=True,
        coverable=True,
        replaceable=tray_cfg.replaceable,
        tags=set(tray_cfg.tags),
    ))

    introduce(world, child, adult, tray_cfg, guest_cfg)
    warning(world, child, adult, tray_cfg)
    temptation(world, child, tray_cfg)

    world.para()
    sneak_bite(world, child, tray_cfg)
    hide_attempt(world, child, cover_cfg, tray_cfg, guest_cfg)

    outcome = "confessed" if response_cfg.power >= 2 else "discovered"
    world.para()
    if outcome == "confessed":
        confess(world, child, adult, response_cfg, tray_cfg)
    else:
        discovered(world, child, adult, guest, response_cfg, tray_cfg)

    world.para()
    ending(world, child, guest_cfg, tray_cfg, outcome)

    world.facts.update(
        child=child,
        adult=adult,
        guest=guest,
        tray_cfg=tray_cfg,
        guest_cfg=guest_cfg,
        cover_cfg=cover_cfg,
        response_cfg=response_cfg,
        outcome=outcome,
        odd_tray=tray.memes["noticed_odd"] >= THRESHOLD,
        crumbs=child.meters["crumbs_on_face"] >= THRESHOLD,
        honest=child.memes["honest"] >= THRESHOLD,
    )
    return world


TRAYS = {
    "buns": TrayKind(
        id="buns",
        label="buns",
        phrase="a tray of little cinnamon buns",
        single="one little bun",
        smell="warm and sugary",
        crumbs="brown sugar crumbs",
        extra="slice up some apples to make the plate feel full again",
        tags={"bun", "snack", "honesty"},
    ),
    "cookies": TrayKind(
        id="cookies",
        label="cookies",
        phrase="a tray of round honey cookies",
        single="one cookie",
        smell="buttery and sweet",
        crumbs="golden cookie crumbs",
        extra="set out orange slices beside the cookies",
        tags={"cookie", "snack", "honesty"},
    ),
    "muffins": TrayKind(
        id="muffins",
        label="muffins",
        phrase="a plate of tiny blueberry muffins",
        single="one tiny muffin",
        smell="soft and berry-sweet",
        crumbs="blueberry crumbs",
        extra="bring out yogurt and berries with the muffins",
        tags={"muffin", "snack", "honesty"},
    ),
}

GUESTS = {
    "teacher": GuestKind(
        id="teacher",
        label="Ms. Nila",
        phrase="Ms. Nila, the next-door teacher",
        reason="she had dropped off library books that morning",
        arrival_sound="a neat knock-knock at the door",
        thanks="Ms. Nila thanked them for the snack",
        type="teacher",
        tags={"teacher", "guest"},
    ),
    "grandpa": GuestKind(
        id="grandpa",
        label="Grandpa Jo",
        phrase="Grandpa Jo",
        reason="he was coming to help fix the squeaky gate",
        arrival_sound="boots thumping on the porch",
        thanks="Grandpa Jo chuckled and thanked them for the snack",
        type="man",
        tags={"grandpa", "guest"},
    ),
    "neighbor": GuestKind(
        id="neighbor",
        label="Mrs. Pei",
        phrase="Mrs. Pei from next door",
        reason="she had watered the garden for them",
        arrival_sound="the soft ring of the doorbell",
        thanks="Mrs. Pei smiled and thanked them for the snack",
        type="woman",
        tags={"neighbor", "guest"},
    ),
}

COVERS = {
    "napkin": CoverKind(
        id="napkin",
        label="napkin",
        phrase="a flappy napkin",
        works_on_tray=True,
        funny_line="The napkin puffed up like a tiny hill, which only made the tray look more suspicious.",
        tags={"napkin"},
    ),
    "towel": CoverKind(
        id="towel",
        label="dish towel",
        phrase="a checkered dish towel",
        works_on_tray=True,
        funny_line="The towel slumped over one side as if it were trying to keep the secret all by itself.",
        tags={"towel"},
    ),
    "hat": CoverKind(
        id="hat",
        label="sun hat",
        phrase="a floppy sun hat",
        works_on_tray=False,
        funny_line="The hat did not fit the tray at all, so it only looked sillier.",
        tags={"hat"},
    ),
}

RESPONSES = {
    "confess_early": ResponseKind(
        id="confess_early",
        sense=3,
        power=3,
        text='"Thank you for telling me right away," Mom said. "A missing treat is a small problem. A hidden one feels bigger."',
        confession_text="I ate one because it smelled yumsy, and then I got scared and tried to hide the empty place.",
        fix_text="{extra}",
        tags={"honesty", "repair"},
    ),
    "apologize_at_table": ResponseKind(
        id="apologize_at_table",
        sense=2,
        power=2,
        text='"Next time, tell me sooner," Dad said gently. "Truth is easier to carry than a secret."',
        confession_text="I took one before our guest came, and I am sorry.",
        fix_text="{extra}",
        tags={"honesty", "repair"},
    ),
    "ignore": ResponseKind(
        id="ignore",
        sense=1,
        power=1,
        text='The grown-ups were quiet for a beat, because pretending not to notice would not teach the right lesson.',
        confession_text="",
        fix_text="{extra}",
        tags={"avoid"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Milo", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["silly", "bouncy", "curious", "playful", "cheerful", "wriggly"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for tray_id, tray in TRAYS.items():
        for guest_id, guest in GUESTS.items():
            for cover_id, cover in COVERS.items():
                if valid_combo(tray, guest, cover):
                    combos.append((tray_id, guest_id, cover_id))
    return combos


@dataclass
class StoryParams:
    tray: str
    guest: str
    cover: str
    response: str
    child_name: str
    child_gender: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bun": [(
        "What is a bun?",
        "A bun is a small baked bread or sweet roll. Some buns smell warm and sweet right out of the oven."
    )],
    "cookie": [(
        "What is a cookie?",
        "A cookie is a small sweet baked treat. Cookies can leave crumbs when you bite them."
    )],
    "muffin": [(
        "What is a muffin?",
        "A muffin is a small baked cake-like snack. Muffins can be sweet and often have fruit inside."
    )],
    "guest": [(
        "What is a guest?",
        "A guest is someone who comes to visit. Being a good host means you think about sharing and kindness."
    )],
    "honesty": [(
        "Why is it good to tell the truth when you make a mistake?",
        "Telling the truth helps grown-ups understand what happened and fix the problem. Hiding a mistake usually makes people worry more."
    )],
    "repair": [(
        "What does it mean to fix a problem together?",
        "It means people work calmly to make things better after something goes wrong. Helping after a mistake is part of being responsible."
    )],
    "napkin": [(
        "What is a napkin for?",
        "A napkin is a piece of cloth or paper people use to wipe hands or cover food for a short time."
    )],
    "towel": [(
        "What is a dish towel?",
        "A dish towel is a cloth used in the kitchen to dry dishes or hands. Sometimes it can cover food on a table."
    )],
}
KNOWLEDGE_ORDER = ["bun", "cookie", "muffin", "guest", "honesty", "repair", "napkin", "towel"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    tray = f["tray_cfg"]
    guest = f["guest_cfg"]
    return [
        f'Write a funny suspense story for a 3-to-5-year-old that includes the word "yumsy" and a child tempted by {tray.label}.',
        f"Tell a gentle moral story where {child.id} tries to hide eating a treat meant for {guest.phrase}, but learns that honesty is easier than hiding.",
        f"Write a comedy-leaning story with kitchen suspense, crumbs, and a warm ending about telling the truth.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    guest = f["guest_cfg"]
    tray = f["tray_cfg"]
    cover = f["cover_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was waiting with {child.pronoun('possessive')} {adult.label_word} for {guest.phrase}. The story follows the small, funny trouble that starts when {child.id} cannot wait for the snack."
        ),
        (
            f"Why did {child.id} call the smell \"yumsy\"?",
            f"{child.id} used \"yumsy\" as a silly family word because the {tray.label} smelled especially good. That happy smell is what made the temptation stronger."
        ),
        (
            f"What mistake did {child.id} make?",
            f"{child.id} ate {tray.single} even though the treats were supposed to wait for the guest. After that, {child.pronoun()} tried to hide the empty place instead of speaking up at once."
        ),
        (
            "Why did the story feel suspenseful?",
            f"It felt suspenseful because there was a missing treat, a crumb on {child.id}'s face, and {guest.arrival_sound} just as {child.id} was trying to hide everything with {cover.phrase}. The child knew the secret might be noticed any second."
        ),
    ]
    if outcome == "confessed":
        qa.append((
            f"How was the problem solved?",
            f"{child.id} told the truth before the snack was served. Then the grown-up calmly helped fix the plate by adding something extra, so honesty led straight to a solution."
        ))
        qa.append((
            "What is the lesson of the story?",
            f"The lesson is that telling the truth quickly makes a scary secret smaller. {child.id}'s worry faded as soon as {child.pronoun()} stopped hiding and started being honest."
        ))
    else:
        qa.append((
            f"How did everyone find out what happened?",
            f"The odd gap on the tray and the crumb on {child.id}'s nose gave the secret away. Once the truth came out, the adults could help fix the problem together."
        ))
        qa.append((
            "What is the lesson of the story?",
            f"The lesson is that hiding a mistake makes it feel bigger and stranger. Even in a funny story, the easier path is to tell the truth and let people help."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["tray_cfg"].tags) | set(f["response_cfg"].tags)
    if f["cover_cfg"].works_on_tray:
        tags |= set(f["cover_cfg"].tags)
    tags.add("guest")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        tray="buns",
        guest="teacher",
        cover="napkin",
        response="confess_early",
        child_name="Milo",
        child_gender="boy",
        adult_type="mother",
        trait="silly",
    ),
    StoryParams(
        tray="cookies",
        guest="grandpa",
        cover="towel",
        response="apologize_at_table",
        child_name="Lily",
        child_gender="girl",
        adult_type="father",
        trait="curious",
    ),
    StoryParams(
        tray="muffins",
        guest="neighbor",
        cover="napkin",
        response="confess_early",
        child_name="Ben",
        child_gender="boy",
        adult_type="mother",
        trait="bouncy",
    ),
]


ASP_RULES = r"""
valid_combo(T, G, C) :- tray(T), guest(G), cover(C), replaceable(T), cover_works(C), guest_reason(G).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

outcome(confessed) :- chosen_response(R), power(R, P), P >= 2.
outcome(discovered) :- chosen_response(R), power(R, P), P < 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, t in TRAYS.items():
        lines.append(asp.fact("tray", tid))
        if t.replaceable:
            lines.append(asp.fact("replaceable", tid))
    for gid, g in GUESTS.items():
        lines.append(asp.fact("guest", gid))
        if g.reason:
            lines.append(asp.fact("guest_reason", gid))
    for cid, c in COVERS.items():
        lines.append(asp.fact("cover", cid))
        if c.works_on_tray:
            lines.append(asp.fact("cover_works", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for s in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a tempting snack, a crumbly secret, and the moral comedy of telling the truth."
    )
    ap.add_argument("--tray", choices=TRAYS)
    ap.add_argument("--guest", choices=GUESTS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father"])
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
    if args.cover and not COVERS[args.cover].works_on_tray:
        raise StoryError(explain_cover(COVERS[args.cover]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.tray is None or c[0] == args.tray)
        and (args.guest is None or c[1] == args.guest)
        and (args.cover is None or c[2] == args.cover)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    tray, guest, cover = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_type = args.adult_type or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        tray=tray,
        guest=guest,
        cover=cover,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        adult_type=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.tray not in TRAYS:
        raise StoryError(f"(Unknown tray '{params.tray}'.)")
    if params.guest not in GUESTS:
        raise StoryError(f"(Unknown guest '{params.guest}'.)")
    if params.cover not in COVERS:
        raise StoryError(f"(Unknown cover '{params.cover}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    if not valid_combo(TRAYS[params.tray], GUESTS[params.guest], COVERS[params.cover]):
        raise StoryError("(These chosen story elements do not make a reasonable story.)")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        TRAYS[params.tray],
        GUESTS[params.guest],
        COVERS[params.cover],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
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
        print(asp_program("", "#show valid_combo/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tray, guest, cover) combos:\n")
        for tray, guest, cover in combos:
            print(f"  {tray:8} {guest:8} {cover}")
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
            header = f"### {p.child_name}: {p.tray} for {p.guest} ({p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
