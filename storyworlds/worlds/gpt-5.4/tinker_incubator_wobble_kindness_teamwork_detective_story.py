#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tinker_incubator_wobble_kindness_teamwork_detective_story.py
=======================================================================================

A standalone story world about two children who notice an incubator wobble,
follow clues like gentle little detectives, and solve the problem with kindness
and teamwork.

The domain is intentionally small and constraint-checked: each wobble cause only
fits certain incubator setups, and each fix only works for the cause it truly
addresses. The prose is driven by simulated state, not by swapping nouns into a
single paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/tinker_incubator_wobble_kindness_teamwork_detective_story.py
    python storyworlds/worlds/gpt-5.4/tinker_incubator_wobble_kindness_teamwork_detective_story.py --place classroom --cause paper_wedge
    python storyworlds/worlds/gpt-5.4/tinker_incubator_wobble_kindness_teamwork_detective_story.py --fix tighten_wheel
    python storyworlds/worlds/gpt-5.4/tinker_incubator_wobble_kindness_teamwork_detective_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/tinker_incubator_wobble_kindness_teamwork_detective_story.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so go up three levels to
# the package dir storyworlds/.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))    # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    scene: str
    sound: str
    helper_type: str
    helper_label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class IncubatorCfg:
    id: str
    label: str
    phrase: str
    support: str             # table | cart | shelf
    cargo: str
    risk_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    clue: str
    support: str
    kind: str                # wedge | wheel | bump
    suspect: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    handles: str
    action: str
    teamwork: str
    kindly: str
    tags: set[str] = field(default_factory=set)


PLACES = {
    "classroom": Place(
        "classroom",
        "the classroom science corner",
        "sunlight made bright squares on the floor beside the reading rug",
        "the little fan hummed softly",
        "teacher",
        "their teacher",
        affords={"table", "cart"},
    ),
    "library": Place(
        "library",
        "the library makerspace",
        "a row of books watched over the worktable like tall, quiet witnesses",
        "the clock ticked between the shelves",
        "teacher",
        "the librarian",
        affords={"table", "cart"},
    ),
    "barn": Place(
        "barn",
        "the barn loft nursery",
        "gold straw glowed in a thin line of morning light",
        "pigeons rustled in the rafters",
        "aunt",
        "their aunt",
        affords={"table", "shelf"},
    ),
}

INCUBATORS = {
    "egg_tray": IncubatorCfg(
        "egg_tray",
        "incubator",
        "a clear little incubator with warm eggs tucked in a tray",
        "table",
        "the warm eggs",
        "If the incubator kept wobbling, the eggs might knock and cool before hatching.",
        tags={"incubator", "eggs"},
    ),
    "duck_cart": IncubatorCfg(
        "duck_cart",
        "incubator",
        "a round-window incubator resting on a rolling cart",
        "cart",
        "the duck eggs",
        "If the incubator kept wobbling, the duck eggs might jiggle too hard and lose their steady warmth.",
        tags={"incubator", "eggs"},
    ),
    "chick_shelf": IncubatorCfg(
        "chick_shelf",
        "incubator",
        "a humming incubator set on a low wooden shelf",
        "shelf",
        "the chick eggs",
        "If the incubator kept wobbling, the chick eggs might bump one another instead of resting safely.",
        tags={"incubator", "eggs"},
    ),
}

CAUSES = {
    "paper_wedge": Cause(
        "paper_wedge",
        "a folded paper star under one leg",
        "a bright folded paper star peeking from under one table leg",
        "table",
        "wedge",
        "a sneaky bump in the floor",
        "When they crouched down, they found a folded paper star wedged under one leg. It had tilted the whole incubator just enough to make it wobble.",
        tags={"paper", "wobble"},
    ),
    "loose_wheel": Cause(
        "loose_wheel",
        "one wheel left unlocked",
        "one cart wheel twitching whenever the cart was touched",
        "cart",
        "wheel",
        "an invisible floor monster",
        "When they looked at the cart together, they saw one wheel was still loose and unlocked. Every tiny nudge made the incubator wobble from side to side.",
        tags={"wheel", "wobble"},
    ),
    "curious_kitten": Cause(
        "curious_kitten",
        "a kitten rubbing the shelf",
        "soft gray fur and a tiny tail flicking beside the shelf",
        "shelf",
        "bump",
        "a ghostly shake",
        "Then the mystery moved all by itself: a curious kitten was rubbing against the shelf. The shelf gave a little wobble each time the kitten asked for attention.",
        tags={"kitten", "wobble", "kindness"},
    ),
}

FIXES = {
    "remove_wedge": Fix(
        "remove_wedge",
        "pull the paper out and steady the leg",
        "wedge",
        "slid the folded paper star out and pressed the table leg flat on the floor again",
        "One child held the incubator still while the other reached underneath",
        "They smoothed the paper instead of tearing it and set it aside for its owner",
        tags={"paper_fix", "teamwork"},
    ),
    "tighten_wheel": Fix(
        "tighten_wheel",
        "lock the cart wheel",
        "wheel",
        "clicked the loose wheel into its lock and checked the cart from both sides",
        "One child watched the incubator while the other knelt by the wheel",
        "They spoke in quiet voices so the eggs would stay calm while they worked",
        tags={"wheel_fix", "teamwork"},
    ),
    "move_kitten_bed": Fix(
        "move_kitten_bed",
        "make the kitten a soft bed away from the shelf",
        "bump",
        "carried over a basket with a folded towel and gently lured the kitten to a cozy spot beside the window",
        "One child fetched the basket while the other stroked the kitten and kept it from bumping the shelf again",
        "They did not scold the kitten, because it had only wanted warmth and company",
        tags={"kitten_fix", "kindness", "teamwork"},
    ),
}

GIRL_NAMES = ["Lina", "Mina", "Sophie", "Nora", "Ella", "Ruth", "Tessa", "Maya"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Eli", "Jonah", "Sam", "Leo"]
TRAITS = ["patient", "careful", "bright", "gentle", "thoughtful", "steady"]


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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    inc = world.get("incubator")
    if inc.meters["wobble"] < THRESHOLD:
        return out
    sig = ("risk", "incubator")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    inc.meters["danger"] += 1
    for eid in ("sleuth", "partner"):
        world.get(eid).memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    inc = world.get("incubator")
    if inc.meters["wobble"] >= THRESHOLD:
        return out
    if inc.meters["danger"] < THRESHOLD:
        return out
    sig = ("relief", "incubator")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    inc.meters["safe"] += 1
    inc.meters["danger"] = 0.0
    for eid in ("sleuth", "partner"):
        kid = world.get(eid)
        kid.memes["relief"] += 1
        kid.memes["worry"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("risk", "physical", _r_risk),
    Rule("relief", "emotional", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def compatible(place: Place, incubator: IncubatorCfg, cause: Cause, fix: Fix) -> bool:
    return (
        incubator.support in place.affords
        and cause.support == incubator.support
        and fix.handles == cause.kind
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for inc_id, inc in INCUBATORS.items():
            for cause_id, cause in CAUSES.items():
                for fix_id, fix in FIXES.items():
                    if compatible(place, inc, cause, fix):
                        combos.append((place_id, inc_id, cause_id, fix_id))
    return combos


def explain_rejection(place: Place, incubator: IncubatorCfg, cause: Cause, fix: Fix) -> str:
    if incubator.support not in place.affords:
        return (
            f"(No story: {place.label} does not suit an incubator on a {incubator.support}. "
            f"Choose a place that can reasonably hold that setup.)"
        )
    if cause.support != incubator.support:
        return (
            f"(No story: {cause.label} would make a {cause.support} wobble, not a "
            f"{incubator.support}. The clue must fit the real support under the incubator.)"
        )
    if fix.handles != cause.kind:
        return (
            f"(No story: {fix.label} does not solve {cause.label}. The detective ending "
            f"only works when the fix truly matches the cause.)"
        )
    return "(No story: the requested combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Simulation verbs
# ---------------------------------------------------------------------------
def introduce(world: World, place: Place, sleuth: Entity, partner: Entity, helper: Entity,
              incubator: IncubatorCfg) -> None:
    sleuth.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"In {place.label}, {sleuth.id} and {partner.id} liked to tinker with small, careful jobs "
        f"and pretend they were detectives. That morning, {place.scene}, and {place.sound}."
    )
    world.say(
        f"Near the window stood {incubator.phrase}. {helper.id} had asked them only to watch it quietly, "
        f"because inside were {incubator.cargo} waiting for a safe, steady day."
    )


def first_clue(world: World, sleuth: Entity, partner: Entity, cause: Cause) -> None:
    world.say(
        f"But when {sleuth.id} leaned close to the tiny window, the incubator gave a wobble. "
        f"{partner.id} saw it too, and both children went still."
    )
    inc = world.get("incubator")
    inc.meters["wobble"] += 1
    inc.meters["warmth_risk"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"That is our first clue," whispered {sleuth.id}. "{cause.clue}."'
    )


def worry(world: World, incubator: IncubatorCfg) -> None:
    if world.get("incubator").meters["danger"] >= THRESHOLD:
        world.say(incubator.risk_line)


def investigate(world: World, sleuth: Entity, partner: Entity, cause: Cause) -> None:
    sleuth.memes["focus"] += 1
    partner.memes["focus"] += 1
    world.say(
        f"The two detectives did not poke or shake anything. Instead, they circled the stand slowly, "
        f"looked low, looked high, and traded observations in careful voices."
    )
    world.say(
        f"At first, {cause.suspect} seemed to be the answer. Then they checked again together."
    )
    world.say(cause.reveal)


def ask_for_help(world: World, helper: Entity, sleuth: Entity, partner: Entity) -> None:
    helper.memes["trust"] += 1
    sleuth.memes["kindness"] += 1
    partner.memes["kindness"] += 1
    world.say(
        f'"We found the problem," said {partner.id}, "but we want to fix it gently." '
        f'{helper.id} smiled and nodded. "Good detectives are careful detectives," {helper.pronoun()} said.'
    )


def repair(world: World, sleuth: Entity, partner: Entity, fix: Fix) -> None:
    sleuth.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    sleuth.memes["kindness"] += 1
    partner.memes["kindness"] += 1
    world.say(fix.teamwork + ".")
    world.say(
        f"Together they {fix.action}. {fix.kindly}."
    )
    inc = world.get("incubator")
    inc.meters["wobble"] = 0.0
    propagate(world, narrate=False)


def proof(world: World, sleuth: Entity, partner: Entity, helper: Entity) -> None:
    inc = world.get("incubator")
    if inc.meters["safe"] >= THRESHOLD:
        world.say(
            f"After that, the incubator stood still. No wobble. Only a soft hum and the warm little promise inside."
        )
    world.say(
        f"{sleuth.id} and {partner.id} grinned at each other. They had solved the mystery by working as a team, "
        f"and they had done it kindly enough for everyone in the room—eggs, grown-up, and even the smallest visitor—to stay calm."
    )
    world.say(
        f'{helper.id} called them "the best detectives in the building," and the children stood a little taller as they kept watch beside the quiet incubator.'
    )


def tell(place: Place, incubator: IncubatorCfg, cause: Cause, fix: Fix,
         sleuth_name: str = "Lina", sleuth_gender: str = "girl",
         partner_name: str = "Owen", partner_gender: str = "boy",
         trait: str = "careful") -> World:
    world = World()
    sleuth = world.add(Entity(id=sleuth_name, kind="character", type=sleuth_gender,
                              role="sleuth", traits=[trait, "observant"]))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender,
                               role="partner", traits=["kind", "steady"]))
    helper = world.add(Entity(id=place.helper_label.title(), kind="character",
                              type=place.helper_type, role="helper", label=place.helper_label))
    inc = world.add(Entity(id="incubator", type="incubator", label="incubator"))
    world.facts["kitten_present"] = cause.id == "curious_kitten"

    introduce(world, place, sleuth, partner, helper, incubator)

    world.para()
    first_clue(world, sleuth, partner, cause)
    worry(world, incubator)
    investigate(world, sleuth, partner, cause)

    world.para()
    ask_for_help(world, helper, sleuth, partner)
    repair(world, sleuth, partner, fix)
    proof(world, sleuth, partner, helper)

    world.facts.update(
        place=place,
        incubator_cfg=incubator,
        cause=cause,
        fix=fix,
        sleuth=sleuth,
        partner=partner,
        helper=helper,
        incubator=inc,
        solved=inc.meters["safe"] >= THRESHOLD,
        teamwork=(sleuth.memes["teamwork"] + partner.memes["teamwork"]) >= THRESHOLD,
        kindness=(sleuth.memes["kindness"] + partner.memes["kindness"]) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    incubator: str
    cause: str
    fix: str
    sleuth_name: str
    sleuth_gender: str
    partner_name: str
    partner_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "incubator": [
        ("What is an incubator?",
         "An incubator is a warm box or machine that keeps eggs at a steady temperature so they can grow safely.")
    ],
    "eggs": [
        ("Why do eggs in an incubator need to stay steady?",
         "Eggs in an incubator need gentle, steady warmth. Too much shaking or cooling can make it harder for them to hatch well.")
    ],
    "wobble": [
        ("What does wobble mean?",
         "Wobble means something rocks or shakes from side to side instead of standing still.")
    ],
    "wheel": [
        ("Why can an unlocked wheel make something wobble?",
         "An unlocked wheel can roll or twist a little when it is touched. That small movement can make everything on top shake too.")
    ],
    "paper": [
        ("How can paper under a table leg make it uneven?",
         "A folded piece of paper can lift one leg just a bit higher than the others. Then the table does not sit flat on the floor.")
    ],
    "kitten": [
        ("Why should you be kind to a curious kitten?",
         "A curious kitten is usually exploring, not trying to cause trouble. Kindness means keeping it safe while also protecting the things around it.")
    ],
    "kindness": [
        ("What does kindness look like during a problem?",
         "Kindness means speaking gently, thinking about others, and solving the problem without being mean or rough.")
    ],
    "teamwork": [
        ("Why is teamwork helpful in solving a mystery?",
         "Teamwork helps because one person can notice a clue while another checks it. Together, people can solve problems more carefully than alone.")
    ],
}
KNOWLEDGE_ORDER = ["incubator", "eggs", "wobble", "paper", "wheel", "kitten", "kindness", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, cause, fix = f["place"], f["cause"], f["fix"]
    sleuth, partner = f["sleuth"], f["partner"]
    return [
        'Write a gentle detective story for a 3-to-5-year-old that includes the words "tinker", "incubator", and "wobble".',
        f"Tell a mystery story where {sleuth.id} and {partner.id} notice an incubator wobble in {place.label}, follow clues, and solve it with teamwork and kindness.",
        f"Write a child-facing detective tale in which the real cause is {cause.label}, and the children fix it by {fix.label} without scolding anyone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth, partner, helper = f["sleuth"], f["partner"], f["helper"]
    place, inc, cause, fix = f["place"], f["incubator_cfg"], f["cause"], f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the detectives in the story?",
            f"The detectives are {sleuth.id} and {partner.id}. They like to tinker with careful jobs and look closely at clues together."
        ),
        (
            "What was the mystery?",
            f"The mystery was why the incubator had begun to wobble. That mattered because {inc.risk_line.lower()}"
        ),
        (
            "What clue did they notice first?",
            f"They first noticed {cause.clue}. That clue made them stop and investigate instead of guessing."
        ),
        (
            "How did they solve the problem?",
            f"They solved it by teamwork: {fix.teamwork.lower()}. Then they {fix.action}, which stopped the wobble."
        ),
    ]
    if f["kindness"]:
        if cause.id == "curious_kitten":
            answer = (
                "They stayed kind by helping the kitten instead of blaming it. They made it a cozy place away from the shelf, so the incubator could stay still and the kitten could still feel safe."
            )
        else:
            answer = (
                "They stayed kind by speaking softly and fixing the problem gently. Instead of fussing or blaming, they worked carefully so the eggs and the grown-up helper would stay calm."
            )
        qa.append(("How did the children show kindness?", answer))
    if f["solved"]:
        qa.append((
            "How did the story end?",
            "It ended with the incubator standing steady again. The quiet hum at the end showed that the mystery was solved and the eggs were safe."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["incubator_cfg"].tags) | set(f["cause"].tags) | set(f["fix"].tags) | {"kindness", "teamwork", "wobble"}
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
supports_incubator(P, I) :- place(P), incubator(I), incubator_support(I, S), place_support(P, S).
cause_fits(C, I) :- cause(C), incubator(I), cause_support(C, S), incubator_support(I, S).
fix_fits(F, C) :- fix(F), cause(C), fix_handles(F, K), cause_kind(C, K).

valid(P, I, C, F) :- supports_incubator(P, I), cause_fits(C, I), fix_fits(F, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(place.affords):
            lines.append(asp.fact("place_support", pid, s))
    for iid, inc in INCUBATORS.items():
        lines.append(asp.fact("incubator", iid))
        lines.append(asp.fact("incubator_support", iid, inc.support))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_support", cid, cause.support))
        lines.append(asp.fact("cause_kind", cid, cause.kind))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_handles", fid, fix.handles))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    # Smoke tests: ordinary generation must work.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        for params in CURATED[:2]:
            _ = generate(params).story
        print("OK: curated samples generate successfully.")
    except Exception as err:
        rc = 1
        print(f"CURATED GENERATION FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("classroom", "egg_tray", "paper_wedge", "remove_wedge", "Lina", "girl", "Owen", "boy", "careful"),
    StoryParams("library", "duck_cart", "loose_wheel", "tighten_wheel", "Milo", "boy", "Nora", "girl", "steady"),
    StoryParams("barn", "chick_shelf", "curious_kitten", "move_kitten_bed", "Ella", "girl", "Theo", "boy", "gentle"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a wobbling incubator mystery solved with kindness and teamwork."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--incubator", choices=INCUBATORS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--sleuth-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--sleuth-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap

def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.incubator and args.cause and args.fix:
        place, inc = PLACES[args.place], INCUBATORS[args.incubator]
        cause, fix = CAUSES[args.cause], FIXES[args.fix]
        if not compatible(place, inc, cause, fix):
            raise StoryError(explain_rejection(place, inc, cause, fix))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.incubator is None or c[1] == args.incubator)
              and (args.cause is None or c[2] == args.cause)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        if args.place and args.incubator and args.cause and args.fix:
            raise StoryError(explain_rejection(PLACES[args.place], INCUBATORS[args.incubator],
                                               CAUSES[args.cause], FIXES[args.fix]))
        raise StoryError("(No valid combination matches the given options.)")

    place, inc, cause, fix = rng.choice(sorted(combos))
    sg = args.sleuth_gender or rng.choice(["girl", "boy"])
    pg = args.partner_gender or rng.choice(["girl", "boy"])
    sleuth_name = args.sleuth_name or _pick_name(rng, sg)
    partner_name = args.partner_name or _pick_name(rng, pg, avoid=sleuth_name)
    trait = rng.choice(TRAITS)
    return StoryParams(place, inc, cause, fix, sleuth_name, sg, partner_name, pg, trait)

def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        INCUBATORS[params.incubator],
        CAUSES[params.cause],
        FIXES[params.fix],
        params.sleuth_name,
        params.sleuth_gender,
        params.partner_name,
        params.partner_gender,
        params.trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, incubator, cause, fix) combos:\n")
        for place, incubator, cause, fix in combos:
            print(f"  {place:10} {incubator:12} {cause:15} {fix}")
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
            header = f"### {p.sleuth_name} & {p.partner_name}: {p.cause} -> {p.fix} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
