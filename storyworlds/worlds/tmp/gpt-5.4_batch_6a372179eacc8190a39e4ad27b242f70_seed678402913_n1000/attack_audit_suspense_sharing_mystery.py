#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/attack_audit_suspense_sharing_mystery.py
==================================================================

A standalone storyworld for a child-facing mystery about a missing snack, a
whispered "attack," and a careful audit that turns fear into sharing.

The domain is small on purpose: two children prepare a snack to share, discover
that some of it is missing, and solve the case by checking clues instead of
panicking. The final beat always proves what changed: they share what remains,
sometimes helped by a small reserve.

Run it
------
    python storyworlds/worlds/gpt-5.4/attack_audit_suspense_sharing_mystery.py
    python storyworlds/worlds/gpt-5.4/attack_audit_suspense_sharing_mystery.py --setting garden --snack berries --culprit crow
    python storyworlds/worlds/gpt-5.4/attack_audit_suspense_sharing_mystery.py --reserve no
    python storyworlds/worlds/gpt-5.4/attack_audit_suspense_sharing_mystery.py --all
    python storyworlds/worlds/gpt-5.4/attack_audit_suspense_sharing_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/attack_audit_suspense_sharing_mystery.py --verify
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
SHARE_GOAL = 4


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }
        return mapping.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
    reserve_from: str = ""


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    count: int
    plate: str
    share_line: str
    vulnerable_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    loss: int
    clue: str
    sound: str
    attack_line: str
    proper_share: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "kid"]

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


def _r_missing_makes_worry(world: World) -> list[str]:
    snack = world.get("snack")
    if snack.meters["lost"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["suspense"] += 1
        kid.memes["curiosity"] += 1
    return []


def _r_audit_brings_clarity(world: World) -> list[str]:
    helper = world.get("helper")
    if helper.memes["auditing"] < THRESHOLD:
        return []
    sig = ("clarity",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.get("snack").memes["mystery_solved"] += 1
    return []


def _r_sharing_softens_loss(world: World) -> list[str]:
    snack = world.get("snack")
    if snack.memes["shared"] < THRESHOLD:
        return []
    sig = ("sharing",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["generosity"] += 1
        kid.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_makes_worry", tag="emotional", apply=_r_missing_makes_worry),
    Rule(name="audit_brings_clarity", tag="emotional", apply=_r_audit_brings_clarity),
    Rule(name="sharing_softens_loss", tag="social", apply=_r_sharing_softens_loss),
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
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the back garden",
        mood="The tall beans clicked softly against their sticks, and every leaf seemed to be listening.",
        affords={"ants", "crow", "puppy"},
        reserve_from="the kitchen door",
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        mood="The boards held the day's warmth, but the shadows under the bench looked full of secrets.",
        affords={"ants", "puppy"},
        reserve_from="the bread box inside",
    ),
    "park": Setting(
        id="park",
        place="the little park",
        mood="The swings were still, and the trees made a dark green roof over the bench.",
        affords={"crow", "ants"},
        reserve_from="a canvas bag",
    ),
}

SNACKS = {
    "berries": Snack(
        id="berries",
        label="berries",
        phrase="a plate of bright berries",
        count=6,
        plate="the blue plate",
        share_line="They had planned to share the berries after the mystery game.",
        vulnerable_to={"ants", "crow"},
        tags={"berries", "sharing"},
    ),
    "muffins": Snack(
        id="muffins",
        label="mini muffins",
        phrase="a basket of mini muffins",
        count=4,
        plate="the picnic basket lid",
        share_line="They had saved the mini muffins so everyone could have one.",
        vulnerable_to={"crow", "puppy"},
        tags={"muffins", "sharing"},
    ),
    "crackers": Snack(
        id="crackers",
        label="star crackers",
        phrase="a tin of star crackers",
        count=8,
        plate="the red napkin",
        share_line="They wanted to share the star crackers while they played detectives.",
        vulnerable_to={"ants", "puppy"},
        tags={"crackers", "sharing"},
    ),
}

CULPRITS = {
    "ants": Culprit(
        id="ants",
        label="ants",
        phrase="a marching line of ants",
        loss=3,
        clue="a tiny black trail winding toward one sweet crumb",
        sound="nothing at all, which somehow felt even more mysterious",
        attack_line="It looked less like a monster attack and more like a tiny crumb attack by ants.",
        proper_share="a few safe crumbs outside on a far stone, away from the children's snack",
        tags={"ants", "audit"},
    ),
    "crow": Culprit(
        id="crow",
        label="crow",
        phrase="a glossy black crow",
        loss=3,
        clue="a shiny feather and one peck mark beside the plate",
        sound="a flap above their heads and one raspy caw",
        attack_line="The plate looked as if a quick crow attack had swooped in and out.",
        proper_share="a small handful of seeds tossed under the hedge, far from the plate",
        tags={"crow", "audit"},
    ),
    "puppy": Culprit(
        id="puppy",
        label="puppy",
        phrase="the neighbor's floppy-eared puppy",
        loss=2,
        clue="two muddy paw prints and a happy, muffin-smelling nose print",
        sound="a soft snuffle under the bench",
        attack_line="It was not a scary attack at all, only a hungry puppy attack on the snack.",
        proper_share="one proper dog biscuit from the tin by the door",
        tags={"puppy", "audit"},
    ),
}


def valid_combo(setting_id: str, snack_id: str, culprit_id: str) -> bool:
    if setting_id not in SETTINGS or snack_id not in SNACKS or culprit_id not in CULPRITS:
        return False
    setting = SETTINGS[setting_id]
    snack = SNACKS[snack_id]
    return culprit_id in setting.affords and culprit_id in snack.vulnerable_to


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for snack_id in SNACKS:
            for culprit_id in CULPRITS:
                if valid_combo(setting_id, snack_id, culprit_id):
                    out.append((setting_id, snack_id, culprit_id))
    return out


def outcome_of(params: "StoryParams") -> str:
    if not valid_combo(params.setting, params.snack, params.culprit):
        raise StoryError("(No story: that culprit would not sensibly take that snack in that place.)")
    snack = SNACKS[params.snack]
    culprit = CULPRITS[params.culprit]
    remaining = snack.count - culprit.loss
    if remaining >= SHARE_GOAL:
        return "ample"
    if params.reserve == "yes":
        return "restored"
    return "small"


@dataclass
class StoryParams:
    setting: str
    snack: str
    culprit: str
    reserve: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


def scene_setup(world: World, a: Entity, b: Entity, helper: Entity, snack: Snack) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} called themselves the Afternoon Mystery Club and spread clues across a bench in {world.setting.place}."
    )
    world.say(world.setting.mood)
    world.say(
        f"{helper.label_word.capitalize()} set down {snack.phrase} on {snack.plate}. {snack.share_line}"
    )


def make_plan(world: World, a: Entity, b: Entity, snack: Snack) -> None:
    world.say(
        f'"No one eats until the case begins," {a.id} whispered, making the snack seem even more special.'
    )
    world.say(
        f'{b.id} nodded and counted the {snack.label} with great care, then tucked the number into {b.pronoun("possessive")} detective notebook.'
    )
    world.facts["start_count"] = snack.count


def whisper_attack(world: World, a: Entity, b: Entity, snack_ent: Entity, culprit: Culprit) -> None:
    snack_ent.meters["lost"] += culprit.loss
    snack_ent.meters["count"] -= culprit.loss
    for kid in (a, b):
        kid.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When they turned back, the plate was wrong. There were fewer {snack_ent.label} than before, and the quiet around the bench felt tight."
    )
    world.say(
        f'Then they heard {culprit.sound}. "{a.id}," {b.id} whispered, "do you think there was an attack?"'
    )
    world.say(
        f"{a.id} stared at {snack_ent.label}. In a mystery club, even a missing bite could feel enormous."
    )


def begin_audit(world: World, helper: Entity, culprit: Culprit, snack: Snack) -> None:
    helper.memes["auditing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} came closer, but instead of guessing, {helper.pronoun()} knelt by the bench."
    )
    world.say(
        f'"Before we panic," {helper.pronoun()} said, "let us do a snack audit. We will count what is left and follow the clues."'
    )
    world.say(
        f"They counted softly: one, two, three. Then they found {culprit.clue}."
    )
    world.facts["audit_done"] = True
    world.facts["remaining"] = snack.count - culprit.loss


def solve_case(world: World, a: Entity, b: Entity, helper: Entity, culprit: Culprit) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f'The clue did not point to a robber at all. It pointed to {culprit.phrase}.'
    )
    world.say(culprit.attack_line)
    world.say(
        f'{helper.label_word.capitalize()} smiled a little. "Mysteries get smaller when we look closely," {helper.pronoun()} said.'
    )
    world.facts["solved_with"] = culprit.label


def share_resolution(world: World, a: Entity, b: Entity, helper: Entity, snack: Snack, culprit: Culprit, reserve: str) -> None:
    snack_ent = world.get("snack")
    remaining = int(snack_ent.meters["count"])
    outcome = outcome_of(world.facts["params"])
    world.para()
    if outcome == "ample":
        snack_ent.memes["shared"] += 1
        propagate(world, narrate=False)
        world.say(
            f"There were still {remaining} {snack.label} left, enough for calm hands and fair turns."
        )
        world.say(
            f"{a.id} and {b.id} split them evenly and even made a tiny proper share for the visitor: {culprit.proper_share}."
        )
        world.say(
            f"By the end, the mystery club was not guarding food anymore. It was sharing it."
        )
    elif outcome == "restored":
        snack_ent.meters["reserve_used"] += 1
        snack_ent.meters["count"] += 2
        snack_ent.memes["shared"] += 1
        propagate(world, narrate=False)
        world.say(
            f"There were only {remaining} {snack.label} left, not quite enough for the cheerful sharing they had planned."
        )
        world.say(
            f"So {helper.label_word} opened {world.setting.reserve_from} and added two extra slices to the plate."
        )
        world.say(
            f"Then {a.id} and {b.id} shared everything fairly and set out {culprit.proper_share} somewhere safe and separate."
        )
        world.say(
            "The bench no longer felt shadowy. It felt busy, kind, and solved."
        )
    else:
        snack_ent.memes["shared"] += 1
        propagate(world, narrate=False)
        world.say(
            f"There were only {remaining} {snack.label} left, so the snack looked small after all the excitement."
        )
        world.say(
            f'{b.id} broke the pieces into smaller parts. "{helper.label_word.capitalize()} was right," {b.pronoun()} said. "We can still share."'
        )
        world.say(
            f"So they did: one careful portion for {a.id}, one for {b.id}, and {culprit.proper_share} set well away from the bench."
        )
        world.say(
            "The last thing to disappear was the worry. In its place was a quiet, solved sort of happiness."
        )
    world.facts["outcome"] = outcome
    world.facts["final_count"] = int(snack_ent.meters["count"])


def tell(
    setting: Setting,
    snack_cfg: Snack,
    culprit_cfg: Culprit,
    reserve: str,
    kid1: str,
    kid1_gender: str,
    kid2: str,
    kid2_gender: str,
    helper_name: str,
    helper_type: str,
) -> World:
    world = World(setting)
    a = world.add(Entity(id=kid1, kind="character", type=kid1_gender, role="kid"))
    b = world.add(Entity(id=kid2, kind="character", type=kid2_gender, role="kid"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    snack = world.add(Entity(id="snack", type="snack", label=snack_cfg.label, phrase=snack_cfg.phrase))
    snack.meters["count"] = float(snack_cfg.count)
    culprit = world.add(Entity(id="culprit", type="animal", label=culprit_cfg.label, phrase=culprit_cfg.phrase))

    scene_setup(world, a, b, helper, snack_cfg)
    make_plan(world, a, b, snack_cfg)

    world.para()
    whisper_attack(world, a, b, snack, culprit_cfg)
    begin_audit(world, helper, culprit_cfg, snack_cfg)
    solve_case(world, a, b, helper, culprit_cfg)

    world.facts["params"] = StoryParams(
        setting=setting.id,
        snack=snack_cfg.id,
        culprit=culprit_cfg.id,
        reserve=reserve,
        kid1=kid1,
        kid1_gender=kid1_gender,
        kid2=kid2,
        kid2_gender=kid2_gender,
        helper=helper_name,
        helper_type=helper_type,
    )

    share_resolution(world, a, b, helper, snack_cfg, culprit_cfg, reserve)

    world.facts.update(
        kid1=a,
        kid2=b,
        helper=helper,
        snack=snack,
        snack_cfg=snack_cfg,
        culprit=culprit,
        culprit_cfg=culprit_cfg,
        reserve=reserve,
        suspense=a.memes["fear"] + b.memes["fear"] > 0,
        shared=snack.memes["shared"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ants": [
        (
            "Why do ants come to crumbs?",
            "Ants look for food, and sweet crumbs smell interesting to them. If food is left low and open, ants may find it quickly.",
        )
    ],
    "crow": [
        (
            "Why might a crow peck at a snack?",
            "Crows are smart birds and they look for easy food. If they see something bright or tasty on a plate, they may swoop down to investigate.",
        )
    ],
    "puppy": [
        (
            "Why does a puppy sniff food?",
            "A puppy learns about the world with its nose. If something smells yummy, it may wander over and sniff or nibble unless a grown-up stops it.",
        )
    ],
    "audit": [
        (
            "What is an audit?",
            "An audit is a careful check. You count what you have and look closely so you can understand what really happened.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting other people have some too. It can also mean dividing something fairly when there is not very much.",
        )
    ],
    "mystery": [
        (
            "What makes something feel like a mystery?",
            "A mystery begins when something important is missing or unexplained. Clues, careful thinking, and patience help solve it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "audit", "sharing", "ants", "crow", "puppy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["kid1"]
    b = f["kid2"]
    snack = f["snack_cfg"]
    culprit = f["culprit_cfg"]
    return [
        f'Write a child-friendly mystery story that includes the words "attack" and "audit" and ends with sharing.',
        f"Tell a suspenseful but gentle story where {a.id} and {b.id} discover that some {snack.label} are missing and solve the case by doing an audit instead of panicking.",
        f"Write a small mystery in which a supposed snack attack turns out to be {culprit.phrase}, and the children choose fairness and sharing at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["kid1"]
    b = f["kid2"]
    helper = f["helper"]
    snack = f["snack_cfg"]
    culprit = f["culprit_cfg"]
    remaining = f["remaining"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children playing detectives, and their {helper.label_word} who helps them solve the case calmly.",
        ),
        (
            "What made the story feel mysterious at first?",
            f"Some of the {snack.label} were missing when the children turned back to the plate. The silence around the bench and the missing food made it feel like a real mystery.",
        ),
        (
            "Why did one child whisper about an attack?",
            f"{b.id} saw that the snack had changed and did not yet know why. In that tense moment, the missing bites felt sudden and spooky, so the word 'attack' fit their fear before the clues did.",
        ),
        (
            "What did the helper do during the audit?",
            f"{helper.label_word.capitalize()} did not guess right away. {helper.pronoun().capitalize()} counted what was left and looked for clues, which helped turn fear into understanding.",
        ),
        (
            "What clue solved the mystery?",
            f"The clue was {culprit.clue}. That detail pointed them to {culprit.phrase} instead of a robber or monster.",
        ),
    ]
    if outcome == "ample":
        qa.append(
            (
                "How did the story end?",
                f"There were still {remaining} {snack.label} left, so the children could share them fairly. They even set out {culprit.proper_share}, which shows the ending changed from worry to kindness.",
            )
        )
    elif outcome == "restored":
        qa.append(
            (
                "How did they manage to share even after some food was gone?",
                f"There were only {remaining} {snack.label} left, so their {helper.label_word} added two extra slices from nearby. After that, the children shared fairly and kept the visitor's proper food separate from their own snack.",
            )
        )
    else:
        qa.append(
            (
                "How did they share when there was not much left?",
                f"There were only {remaining} {snack.label} left, so {b.id} broke the snack into smaller parts. That way both children still shared, and the mystery ended with fairness instead of grumbling.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    culprit = world.facts["culprit_cfg"].id
    tags = {"mystery", "audit", "sharing", culprit}
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        snack="berries",
        culprit="crow",
        reserve="yes",
        kid1="Lily",
        kid1_gender="girl",
        kid2="Ben",
        kid2_gender="boy",
        helper="Grandma",
        helper_type="grandmother",
    ),
    StoryParams(
        setting="porch",
        snack="muffins",
        culprit="puppy",
        reserve="no",
        kid1="Max",
        kid1_gender="boy",
        kid2="Mia",
        kid2_gender="girl",
        helper="Dad",
        helper_type="father",
    ),
    StoryParams(
        setting="park",
        snack="berries",
        culprit="ants",
        reserve="yes",
        kid1="Nora",
        kid1_gender="girl",
        kid2="Sam",
        kid2_gender="boy",
        helper="Mom",
        helper_type="mother",
    ),
    StoryParams(
        setting="garden",
        snack="crackers",
        culprit="ants",
        reserve="no",
        kid1="Theo",
        kid1_gender="boy",
        kid2="Ava",
        kid2_gender="girl",
        helper="Grandpa",
        helper_type="grandfather",
    ),
    StoryParams(
        setting="garden",
        snack="muffins",
        culprit="puppy",
        reserve="yes",
        kid1="Ella",
        kid1_gender="girl",
        kid2="Finn",
        kid2_gender="boy",
        helper="Mom",
        helper_type="mother",
    ),
]


ASP_RULES = r"""
valid(S, Sn, C) :- setting(S), snack(Sn), culprit(C), affords(S, C), targets(C, Sn).

remaining(Sn, C, R) :- snack_count(Sn, N), loss(C, L), R = N - L.

outcome(ample) :- chosen_snack(Sn), chosen_culprit(C), remaining(Sn, C, R), share_goal(G), R >= G.
outcome(restored) :- chosen_snack(Sn), chosen_culprit(C), remaining(Sn, C, R), share_goal(G), R < G, reserve(yes).
outcome(small) :- chosen_snack(Sn), chosen_culprit(C), remaining(Sn, C, R), share_goal(G), R < G, reserve(no).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for culprit_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, culprit_id))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        lines.append(asp.fact("snack_count", snack_id, snack.count))
        for culprit_id in sorted(snack.vulnerable_to):
            lines.append(asp.fact("targets", culprit_id, snack_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("loss", culprit_id, culprit.loss))
    lines.append(asp.fact("share_goal", SHARE_GOAL))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_snack", params.snack),
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("reserve", params.reserve),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def explain_rejection(setting: str, snack: str, culprit: str) -> str:
    if setting not in SETTINGS:
        return f"(No story: unknown setting '{setting}'.)"
    if snack not in SNACKS:
        return f"(No story: unknown snack '{snack}'.)"
    if culprit not in CULPRITS:
        return f"(No story: unknown culprit '{culprit}'.)"
    s = SETTINGS[setting]
    sn = SNACKS[snack]
    if culprit not in s.affords:
        return (
            f"(No story: {CULPRITS[culprit].label} would not sensibly trouble a snack in {s.place}. "
            f"Pick a culprit that fits the place.)"
        )
    if culprit not in sn.vulnerable_to:
        return (
            f"(No story: {sn.label} are not a sensible target for {CULPRITS[culprit].label} in this world. "
            f"Pick a snack that matches the clue trail.)"
        )
    return "(No story: that combination does not fit the mystery world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny mystery storyworld about a snack attack, a calm audit, and sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--reserve", choices=["yes", "no"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.snack and args.culprit and not valid_combo(args.setting, args.snack, args.culprit):
        raise StoryError(explain_rejection(args.setting, args.snack, args.culprit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.snack is None or combo[1] == args.snack)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, snack_id, culprit_id = rng.choice(sorted(combos))
    reserve = args.reserve or rng.choice(["yes", "no"])
    kid1_gender = rng.choice(["girl", "boy"])
    kid2_gender = rng.choice(["girl", "boy"])
    kid1 = _pick_name(rng, kid1_gender)
    kid2 = _pick_name(rng, kid2_gender, avoid=kid1)
    helper_type = rng.choice(["mother", "father", "grandmother", "grandfather"])
    helper_names = {
        "mother": "Mom",
        "father": "Dad",
        "grandmother": "Grandma",
        "grandfather": "Grandpa",
    }
    return StoryParams(
        setting=setting_id,
        snack=snack_id,
        culprit=culprit_id,
        reserve=reserve,
        kid1=kid1,
        kid1_gender=kid1_gender,
        kid2=kid2,
        kid2_gender=kid2_gender,
        helper=helper_names[helper_type],
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.snack not in SNACKS:
        raise StoryError(f"(No story: unknown snack '{params.snack}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.reserve not in {"yes", "no"}:
        raise StoryError(f"(No story: reserve must be 'yes' or 'no', not '{params.reserve}'.)")
    if not valid_combo(params.setting, params.snack, params.culprit):
        raise StoryError(explain_rejection(params.setting, params.snack, params.culprit))

    world = tell(
        setting=SETTINGS[params.setting],
        snack_cfg=SNACKS[params.snack],
        culprit_cfg=CULPRITS[params.culprit],
        reserve=params.reserve,
        kid1=params.kid1,
        kid1_gender=params.kid1_gender,
        kid2=params.kid2,
        kid2_gender=params.kid2_gender,
        helper_name=params.helper,
        helper_type=params.helper_type,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    scenarios = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)

    bad = 0
    for params in scenarios:
        py_outcome = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_outcome != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(scenarios)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, snack, culprit) combos:\n")
        for setting_id, snack_id, culprit_id in combos:
            print(f"  {setting_id:8} {snack_id:9} {culprit_id}")
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
            header = f"### {p.kid1} & {p.kid2}: {p.snack} in {p.setting} ({p.culprit}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
