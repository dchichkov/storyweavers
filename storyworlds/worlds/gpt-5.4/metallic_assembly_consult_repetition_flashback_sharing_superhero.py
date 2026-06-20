#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/metallic_assembly_consult_repetition_flashback_sharing_superhero.py
================================================================================================

A standalone story world for a small superhero-style school tale: a child is
building a shiny rescue gadget for the morning assembly, discovers one crucial
metallic part is missing, consults a trusted grown-up, remembers an older lesson,
and is helped when another child shares the needed piece. The world model tracks
physical completion and emotional shifts so the prose follows state, not just
slot-filling.

Seed requirements rebuilt as simulation
---------------------------------------
Words:
    metallic, assembly, consult

Features:
    Repetition, Flashback, Sharing

Style:
    Superhero Story

Run it
------
    python storyworlds/worlds/gpt-5.4/metallic_assembly_consult_repetition_flashback_sharing_superhero.py
    python storyworlds/worlds/gpt-5.4/metallic_assembly_consult_repetition_flashback_sharing_superhero.py --gadget wing_pack --part clip
    python storyworlds/worlds/gpt-5.4/metallic_assembly_consult_repetition_flashback_sharing_superhero.py --consultant mr_lopez --gadget beam_bracelet
    python storyworlds/worlds/gpt-5.4/metallic_assembly_consult_repetition_flashback_sharing_superhero.py --all
    python storyworlds/worlds/gpt-5.4/metallic_assembly_consult_repetition_flashback_sharing_superhero.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/metallic_assembly_consult_repetition_flashback_sharing_superhero.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REFRAIN = "Tap, twist, click"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    need_part: str
    intro: str
    finish: str
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Part:
    id: str
    label: str
    phrase: str
    fix_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Consultant:
    id: str
    name: str
    type: str
    label: str
    knows: set[str]
    consult_line: str
    advice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sharer:
    id: str
    name: str
    type: str
    carries: set[str]
    share_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {"refrain": REFRAIN}

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


def _r_missing_makes_worry(world: World) -> list[str]:
    hero = world.get("hero")
    gadget = world.get("gadget")
    if gadget.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry", gadget.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gadget.meters["unstable"] += 1
    hero.memes["worry"] += 1
    return []


def _r_plan_plus_shared_part_repairs(world: World) -> list[str]:
    gadget = world.get("gadget")
    hero = world.get("hero")
    if hero.memes["guided"] < THRESHOLD or gadget.meters["shared_part"] < THRESHOLD:
        return []
    sig = ("repair", gadget.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gadget.meters["missing"] = 0.0
    gadget.meters["assembled"] += 1
    gadget.meters["stable"] += 1
    gadget.meters["unstable"] = 0.0
    hero.memes["hope"] += 1
    hero.memes["worry"] = 0.0
    return []


def _r_sharing_builds_bond(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    gadget = world.get("gadget")
    if gadget.meters["shared_part"] < THRESHOLD:
        return []
    sig = ("bond", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["gratitude"] += 1
    friend.memes["kindness"] += 1
    hero.memes["belonging"] += 1
    friend.memes["belonging"] += 1
    return []


def _r_stable_gadget_wins_assembly(world: World) -> list[str]:
    hall = world.get("hall")
    gadget = world.get("gadget")
    hero = world.get("hero")
    if hall.meters["assembly_started"] < THRESHOLD or gadget.meters["stable"] < THRESHOLD:
        return []
    sig = ("success", gadget.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    hall.meters["cheers"] += 1
    return []


CAUSAL_RULES = [
    Rule("missing_makes_worry", "emotional", _r_missing_makes_worry),
    Rule("plan_plus_shared_part_repairs", "physical", _r_plan_plus_shared_part_repairs),
    Rule("sharing_builds_bond", "social", _r_sharing_builds_bond),
    Rule("stable_gadget_wins_assembly", "social", _r_stable_gadget_wins_assembly),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def can_consult(consultant: Consultant, gadget: Gadget) -> bool:
    return gadget.id in consultant.knows


def can_share(sharer: Sharer, part: Part) -> bool:
    return part.id in sharer.carries


def valid_combo(gadget: Gadget, part: Part, consultant: Consultant, sharer: Sharer) -> bool:
    return gadget.need_part == part.id and can_consult(consultant, gadget) and can_share(sharer, part)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for gid, gadget in GADGETS.items():
        for pid, part in PARTS.items():
            for cid, consultant in CONSULTANTS.items():
                for sid, sharer in SHARERS.items():
                    if valid_combo(gadget, part, consultant, sharer):
                        out.append((gid, pid, cid, sid))
    return out


def explain_invalid(gadget: Gadget, part: Part, consultant: Consultant, sharer: Sharer) -> str:
    if gadget.need_part != part.id:
        needed = PARTS[gadget.need_part].label
        return (
            f"(No story: the {gadget.label} needs {needed}, not {part.label}. "
            f"A superhero fix only works when the missing part matches the gadget.)"
        )
    if not can_consult(consultant, gadget):
        known = ", ".join(sorted(CONSULTANTS[consultant.id].knows))
        return (
            f"(No story: {consultant.name} does not know how to steady a {gadget.label}. "
            f"Try a consultant who knows this gadget instead of guessing. "
            f"{consultant.name}'s known gadgets here: {known}.)"
        )
    if not can_share(sharer, part):
        carries = ", ".join(sorted(sharer.carries))
        return (
            f"(No story: {sharer.name} is not carrying {part.label}. "
            f"Sharing has to give the hero the exact part that is missing. "
            f"{sharer.name} can share: {carries}.)"
        )
    return "(No story: this combination does not make a reasonable repair.)"


def predict_fix(world: World, consultant_id: str, sharer_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    gadget = sim.get("gadget")
    consultant = sim.get(consultant_id)
    sharer = sim.get(sharer_id)
    hero.memes["guided"] += 1
    consultant.memes["helped"] += 1
    gadget.meters["shared_part"] += 1
    sharer.memes["shared"] += 1
    propagate(sim, narrate=False)
    return {
        "stable": gadget.meters["stable"] >= THRESHOLD,
        "worry": hero.memes["worry"],
    }


def morning_setup(world: World, hero: Entity, friend: Entity, gadget: Gadget) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At Sunrise School, the gym was being turned into a superhero headquarters for the morning assembly. "
        f"{hero.id} and {friend.id} knelt by a bright blue mat with {gadget.phrase} between them."
    )
    world.say(
        f'"{REFRAIN}, {REFRAIN}, {REFRAIN}," {hero.id} whispered as the class worked through the last steps of the assembly. '
        f"The words felt like tiny drumbeats for brave hands."
    )
    world.say(gadget.intro)


def discover_missing(world: World, hero: Entity, gadget: Entity, part: Part) -> None:
    gadget.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} stopped. The place for {part.phrase} was empty. "
        f"Without it, the gadget gave a sad wobble instead of a hero hum."
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"A hot little worry zipped through {hero.id}'s chest. If the {gadget.label} shook apart at assembly time, "
            f"everyone would see."
        )


def hesitate(world: World, hero: Entity) -> None:
    hero.memes["stubborn"] += 1
    world.say(
        f'{hero.id} pressed {hero.pronoun("possessive")} lips together. '
        f'"I can do it myself," {hero.pronoun()} muttered, even while the wobble kept answering no.'
    )


def consult_helper(world: World, hero: Entity, consultant: Entity, consultant_cfg: Consultant, gadget: Gadget, part: Part, sharer: Sharer) -> None:
    pred = predict_fix(world, consultant.id, "sharer")
    hero.memes["guided"] += 1
    consultant.memes["helped"] += 1
    world.facts["predicted_stable"] = pred["stable"]
    world.say(
        f'{hero.id} took a breath. "I need to consult {consultant_cfg.name}," {hero.pronoun()} said at last.'
    )
    world.say(consultant_cfg.consult_line)
    world.say(
        f'{consultant_cfg.name} crouched beside the mat, touched the half-built {gadget.label}, and nodded. '
        f'"{consultant_cfg.advice} You do not need to be a lone hero."'
    )
    world.facts["consulted"] = consultant_cfg.name
    world.facts["needed_part"] = part.label
    world.facts["sharer_name"] = sharer.name


def flashback(world: World, hero: Entity) -> None:
    hero.memes["memory"] += 1
    world.facts["flashback"] = True
    world.say(
        f"That made {hero.id} flash back to last week's art table, when glitter stars had spilled everywhere. "
        f"{hero.id} had tried to guard the whole tray alone, and the mess had only grown bigger."
    )
    world.say(
        f"In the memory, the art helper had laughed softly and said, "
        f'"Real heroes ask, and real heroes share." The old words clicked into place now like a secret switch.'
    )


def offer_share(world: World, hero: Entity, friend: Entity, gadget: Entity, part: Part, sharer_cfg: Sharer) -> None:
    gadget.meters["shared_part"] += 1
    friend.memes["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{friend.id}, who had been sorting parts nearby, lifted a hand. "{sharer_cfg.share_line}"'
    )
    world.say(
        f"{friend.id} placed {part.phrase} into {hero.id}'s palm. The small metallic piece felt cool, bright, and suddenly full of hope."
    )


def rebuild(world: World, hero: Entity, friend: Entity, gadget: Gadget, part: Part) -> None:
    world.say(
        f"Together they tried again. {REFRAIN}. {REFRAIN}. {REFRAIN}. "
        f"This time the {part.label} held fast, and {gadget.finish}"
    )
    if world.get("gadget").meters["stable"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s shoulders loosened. The wobble was gone. In its place came the neat, brave sound of something ready."
        )


def start_assembly(world: World, hero: Entity, friend: Entity, gadget: Gadget) -> None:
    hall = world.get("hall")
    hall.meters["assembly_started"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon the principal called the assembly to order, and the gym lights shone on capes, posters, and eager faces. "
        f"{hero.id} stepped onto the little stage with {gadget.phrase} tucked close."
    )
    if hall.meters["cheers"] >= THRESHOLD:
        world.say(
            f"When {hero.id} {gadget.action}, the class gasped first and then burst into cheers. "
            f"The whole room felt as if a superhero comic had opened right inside the school."
        )
    world.say(
        f'But {hero.id} did not keep the moment alone. "{friend.id} shared the missing part, and {world.facts["consulted"]} showed me what to do," '
        f'{hero.pronoun()} told the room. "That is how this hero machine became ready."'
    )
    world.say(
        f"The cheers grew even warmer then, because everyone could see what had changed: the gadget was steady, and so was {hero.id}."
    )


def ending_image(world: World, hero: Entity, friend: Entity, gadget: Gadget) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"After the assembly, {hero.id} and {friend.id} let the younger children touch the safe switches one at a time. "
        f"The shiny {gadget.label} flashed under the windows, and {hero.id} kept repeating the new hero rule in a happy whisper: "
        f'"Ask, share, shine."'
    )


def tell(
    gadget_cfg: Gadget,
    part_cfg: Part,
    consultant_cfg: Consultant,
    sharer_cfg: Sharer,
    hero_name: str = "Maya",
    hero_type: str = "girl",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=sharer_cfg.type, label=sharer_cfg.name, role="sharer"))
    consultant = world.add(
        Entity(id="consultant", kind="character", type=consultant_cfg.type, label=consultant_cfg.name, role="consultant")
    )
    hall = world.add(Entity(id="hall", type="place", label="the gym"))
    gadget = world.add(Entity(id="gadget", type="gadget", label=gadget_cfg.label))
    world.add(Entity(id="part", type="part", label=part_cfg.label))

    morning_setup(world, hero, friend, gadget_cfg)
    world.para()
    discover_missing(world, hero, gadget, part_cfg)
    hesitate(world, hero)
    consult_helper(world, hero, consultant, consultant_cfg, gadget_cfg, part_cfg, sharer_cfg)
    flashback(world, hero)
    world.para()
    offer_share(world, hero, friend, gadget, part_cfg, sharer_cfg)
    rebuild(world, hero, friend, gadget_cfg, part_cfg)
    world.para()
    start_assembly(world, hero, friend, gadget_cfg)
    ending_image(world, hero, friend, gadget_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        consultant=consultant,
        consultant_cfg=consultant_cfg,
        sharer_cfg=sharer_cfg,
        gadget_cfg=gadget_cfg,
        part_cfg=part_cfg,
        stable=gadget.meters["stable"] >= THRESHOLD,
        shared=gadget.meters["shared_part"] >= THRESHOLD,
        cheered=hall.meters["cheers"] >= THRESHOLD,
    )
    return world


GADGETS = {
    "wing_pack": Gadget(
        "wing_pack",
        "wing pack",
        "a silver-blue wing pack",
        "clip",
        "The wing pack was supposed to open like two tiny thunderbird wings.",
        "the wing panels clicked level and straight",
        "spread the wing panels with a whoosh",
        tags={"wings", "assembly", "metallic"},
    ),
    "shield_sled": Gadget(
        "shield_sled",
        "shield sled",
        "a gleaming rescue shield sled",
        "bolt",
        "The shield sled was supposed to skim low across the stage like a city-saving disc.",
        "the rescue shield sat firm on its runners",
        "sent the shield sled sliding in one smooth silver line",
        tags={"shield", "assembly", "metallic"},
    ),
    "beam_bracelet": Gadget(
        "beam_bracelet",
        "beam bracelet",
        "a bright rescue beam bracelet",
        "ring",
        "The beam bracelet was supposed to cast a star of light over the curtain.",
        "the bracelet band closed in a perfect circle",
        "raised the bracelet and painted a star of light on the wall",
        tags={"bracelet", "assembly", "metallic"},
    ),
}

PARTS = {
    "clip": Part(
        "clip",
        "metallic clip",
        "a tiny metallic clip",
        "snapped the clip into the wing hinge",
        tags={"metallic", "clip"},
    ),
    "bolt": Part(
        "bolt",
        "metallic bolt",
        "a tiny metallic bolt",
        "turned the bolt until the runners stopped rattling",
        tags={"metallic", "bolt"},
    ),
    "ring": Part(
        "ring",
        "metallic ring",
        "a small metallic ring",
        "slid the ring into the bracelet latch",
        tags={"metallic", "ring"},
    ),
}

CONSULTANTS = {
    "ms_vega": Consultant(
        "ms_vega",
        "Ms. Vega",
        "woman",
        "science teacher",
        {"wing_pack", "beam_bracelet"},
        "Ms. Vega was pinning lightning-bolt posters by the curtain, so consulting her felt like calling mission control.",
        "Find the exact part, ask for help, and let another pair of hands make the plan stronger",
        tags={"consult", "teacher"},
    ),
    "mr_lopez": Consultant(
        "mr_lopez",
        "Mr. Lopez",
        "man",
        "custodian",
        {"wing_pack", "shield_sled"},
        "Mr. Lopez was checking the wheels on the folding stage, and he loved anything with screws, tracks, or moving plates.",
        "A hero gadget stops wobbling when the right piece and the right teamwork arrive together",
        tags={"consult", "tools"},
    ),
    "coach_comet": Consultant(
        "coach_comet",
        "Coach Comet",
        "woman",
        "volunteer coach",
        {"wing_pack", "shield_sled", "beam_bracelet"},
        "Coach Comet was helping children tie capes, and even her whistle looked ready for adventure.",
        "Do not fight the problem alone; name the missing piece, then let the team answer it",
        tags={"consult", "sharing"},
    ),
}

SHARERS = {
    "mina": Sharer(
        "mina",
        "Mina",
        "girl",
        {"clip", "ring"},
        "I have an extra one in my tray. Heroes do not let each other wobble.",
        tags={"sharing", "friend"},
    ),
    "theo": Sharer(
        "theo",
        "Theo",
        "boy",
        {"bolt"},
        "I packed a spare for emergencies. You can use it, and we can both watch it fly.",
        tags={"sharing", "friend"},
    ),
    "zara": Sharer(
        "zara",
        "Zara",
        "girl",
        {"bolt", "ring"},
        "Take my extra piece. A team sparkle is better than a lonely sparkle.",
        tags={"sharing", "friend"},
    ),
}

GIRL_NAMES = ["Maya", "Luna", "Ava", "Zoe", "Nora", "Ivy", "Mila", "Aria"]
BOY_NAMES = ["Leo", "Max", "Eli", "Finn", "Noah", "Theo", "Owen", "Kai"]


@dataclass
class StoryParams:
    gadget: str
    part: str
    consultant: str
    sharer: str
    hero_name: str
    hero_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "metallic": [
        (
            "What does metallic mean?",
            "Metallic means something is made of metal or shines like metal. Metallic things often feel smooth, cool, and bright.",
        )
    ],
    "assembly": [
        (
            "What is a school assembly?",
            "A school assembly is a time when many students gather together in one room. They might listen, sing, clap, or watch classmates present something.",
        )
    ],
    "consult": [
        (
            "What does it mean to consult someone?",
            "To consult someone means to ask a trusted person for advice or help. You do it when you want a wiser plan instead of just guessing.",
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful?",
            "Sharing helps people solve problems together. When one person has what another person needs, sharing can turn a hard moment into a happy one.",
        )
    ],
    "clip": [
        (
            "What does a clip do in a gadget?",
            "A clip helps hold one part onto another part. If a clip is missing, the gadget can wobble or come apart.",
        )
    ],
    "bolt": [
        (
            "What does a bolt do?",
            "A bolt fastens parts together tightly. It helps machines stay steady instead of rattling loose.",
        )
    ],
    "ring": [
        (
            "What can a ring-shaped part do in a bracelet or latch?",
            "A ring-shaped part can help a bracelet or latch close in a circle. When it fits in the right place, the whole piece can work properly.",
        )
    ],
}
KNOWLEDGE_ORDER = ["metallic", "assembly", "consult", "sharing", "clip", "bolt", "ring"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    gadget = f["gadget_cfg"]
    part = f["part_cfg"]
    consultant = f["consultant_cfg"]
    friend = f["sharer_cfg"]
    return [
        'Write a superhero story for a 3-to-5-year-old that includes the words "metallic", "assembly", and "consult".',
        f"Tell a school superhero story where {hero.label} discovers that {gadget.phrase} is missing {part.phrase}, consults {consultant.name}, and is helped when {friend.name} shares the right piece.",
        f'Write a gentle action story that uses repetition, a flashback, and sharing, and ends with a child hero learning that asking for help can make a team stronger.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    gadget = f["gadget_cfg"]
    part = f["part_cfg"]
    consultant = f["consultant_cfg"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child getting ready for a superhero school assembly. {friend.label} and {consultant.name} help when the gadget problem appears.",
        ),
        (
            f"What problem did {hero.label} find?",
            f"{hero.label} found that the {gadget.label} was missing {part.phrase}. Without that exact part, the gadget wobbled and did not feel ready for the assembly.",
        ),
        (
            f"Why did {hero.label} decide to consult {consultant.name}?",
            f"{hero.label} was worried because the gadget might fail in front of everyone. Consulting {consultant.name} gave {hero.pronoun('object')} a wiser plan instead of leaving {hero.pronoun('object')} alone with the problem.",
        ),
        (
            "What happened in the flashback?",
            f"{hero.label} remembered an earlier time at the art table when trying to handle everything alone only made the mess bigger. That memory reminded {hero.pronoun('object')} that real heroes ask and real heroes share.",
        ),
        (
            f"How did sharing change the story?",
            f"{friend.label} shared the missing {part.label}, so the repair could finally happen. The gift fixed the gadget and also made {hero.label} brave enough to share the credit out loud.",
        ),
    ]
    if f["stable"]:
        qa.append(
            (
                f"How did the assembly end?",
                f"The assembly ended happily because the {gadget.label} worked on stage and the room cheered. {hero.label} also told everyone who had helped, which showed that the real change was not only in the machine but in {hero.pronoun('possessive')} heart.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"metallic", "assembly", "consult", "sharing"}
    tags |= set(world.facts["part_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("wing_pack", "clip", "ms_vega", "mina", "Maya", "girl"),
    StoryParams("shield_sled", "bolt", "mr_lopez", "theo", "Leo", "boy"),
    StoryParams("beam_bracelet", "ring", "coach_comet", "zara", "Nora", "girl"),
    StoryParams("wing_pack", "clip", "coach_comet", "mina", "Finn", "boy"),
]


ASP_RULES = r"""
needs(G, P) :- gadget(G), required_part(G, P).
can_consult(C, G) :- consultant(C), knows(C, G).
can_share(S, P) :- sharer(S), carries(S, P).

valid(G, P, C, S) :- needs(G, P), can_consult(C, G), can_share(S, P).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid, gadget in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        lines.append(asp.fact("required_part", gid, gadget.need_part))
    for pid in PARTS:
        lines.append(asp.fact("part", pid))
    for cid, consultant in CONSULTANTS.items():
        lines.append(asp.fact("consultant", cid))
        for gid in sorted(consultant.knows):
            lines.append(asp.fact("knows", cid, gid))
    for sid, sharer in SHARERS.items():
        lines.append(asp.fact("sharer", sid))
        for pid in sorted(sharer.carries):
            lines.append(asp.fact("carries", sid, pid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    for s in range(5):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            smoke_cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during smoke param generation for seed {s}.")
            continue

    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise RuntimeError("empty story")
            buf = io.StringIO()
            with redirect_stdout(buf):
                emit(sample, trace=True, qa=True, header="### smoke")
        print(f"OK: smoke-tested generate/emit on {len(smoke_cases)} scenarios.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero school-assembly storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--part", choices=PARTS)
    ap.add_argument("--consultant", choices=CONSULTANTS)
    ap.add_argument("--sharer", choices=SHARERS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gadget and args.part and args.consultant and args.sharer:
        if not valid_combo(GADGETS[args.gadget], PARTS[args.part], CONSULTANTS[args.consultant], SHARERS[args.sharer]):
            raise StoryError(
                explain_invalid(
                    GADGETS[args.gadget],
                    PARTS[args.part],
                    CONSULTANTS[args.consultant],
                    SHARERS[args.sharer],
                )
            )
    elif args.gadget and args.part and GADGETS[args.gadget].need_part != args.part:
        any_consultant = CONSULTANTS[args.consultant] if args.consultant else next(iter(CONSULTANTS.values()))
        any_sharer = SHARERS[args.sharer] if args.sharer else next(iter(SHARERS.values()))
        raise StoryError(explain_invalid(GADGETS[args.gadget], PARTS[args.part], any_consultant, any_sharer))
    elif args.gadget and args.consultant and not can_consult(CONSULTANTS[args.consultant], GADGETS[args.gadget]):
        needed = PARTS[GADGETS[args.gadget].need_part]
        any_sharer = SHARERS[args.sharer] if args.sharer else next(iter(SHARERS.values()))
        raise StoryError(explain_invalid(GADGETS[args.gadget], needed, CONSULTANTS[args.consultant], any_sharer))
    elif args.part and args.sharer and not can_share(SHARERS[args.sharer], PARTS[args.part]):
        any_gadget = GADGETS[args.gadget] if args.gadget else next(iter(GADGETS.values()))
        any_consultant = CONSULTANTS[args.consultant] if args.consultant else next(iter(CONSULTANTS.values()))
        raise StoryError(explain_invalid(any_gadget, PARTS[args.part], any_consultant, SHARERS[args.sharer]))

    combos = [
        c
        for c in valid_combos()
        if (args.gadget is None or c[0] == args.gadget)
        and (args.part is None or c[1] == args.part)
        and (args.consultant is None or c[2] == args.consultant)
        and (args.sharer is None or c[3] == args.sharer)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    gadget, part, consultant, sharer = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(gadget, part, consultant, sharer, hero, gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        GADGETS[params.gadget],
        PARTS[params.part],
        CONSULTANTS[params.consultant],
        SHARERS[params.sharer],
        params.hero_name,
        params.hero_gender,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (gadget, part, consultant, sharer) combos:\n")
        for gadget, part, consultant, sharer in combos:
            print(f"  {gadget:14} {part:6} {consultant:12} {sharer}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name}: {p.gadget} with {p.consultant} and {p.sharer}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
