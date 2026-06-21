#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/decorative_problem_solving_repetition_happy_ending_pirate.py
========================================================================================

A standalone storyworld for a tiny pirate-tale domain: two children turn a room
into a pirate ship and try to hang one decorative pirate decoration before their
treasure voyage. The decoration keeps slipping until they choose a fix that
actually suits the weight of the decoration and the kind of place they are
attaching it.

This world is built for:
- decorative
- problem solving
- repetition
- happy ending
- pirate-tale style

Run it
------
    python storyworlds/worlds/gpt-5.4/decorative_problem_solving_repetition_happy_ending_pirate.py
    python storyworlds/worlds/gpt-5.4/decorative_problem_solving_repetition_happy_ending_pirate.py --decoration banner --anchor mast --fix rope_tie
    python storyworlds/worlds/gpt-5.4/decorative_problem_solving_repetition_happy_ending_pirate.py --decoration shell_chain --anchor mast
    python storyworlds/worlds/gpt-5.4/decorative_problem_solving_repetition_happy_ending_pirate.py --all
    python storyworlds/worlds/gpt-5.4/decorative_problem_solving_repetition_happy_ending_pirate.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/decorative_problem_solving_repetition_happy_ending_pirate.py --qa --json
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
class Decoration:
    id: str
    label: str
    phrase: str
    weight: int
    style_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Anchor:
    id: str
    label: str
    phrase: str
    surface: str
    capacity: int
    scene_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    strength: int
    sense: int
    for_surfaces: set[str]
    action_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


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


def fits_surface(fix: Fix, anchor: Anchor) -> bool:
    return anchor.surface in fix.for_surfaces


def can_hold(decoration: Decoration, anchor: Anchor) -> bool:
    return anchor.capacity >= decoration.weight


def valid_fix(fix: Fix, decoration: Decoration, anchor: Anchor) -> bool:
    return fix.sense >= SENSE_MIN and fits_surface(fix, anchor)


def reliable_fix(fix: Fix, decoration: Decoration, anchor: Anchor) -> bool:
    return valid_fix(fix, decoration, anchor) and fix.strength >= decoration.weight


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for dec_id, decoration in DECORATIONS.items():
        for anc_id, anchor in ANCHORS.items():
            if not can_hold(decoration, anchor):
                continue
            if any(valid_fix(fix, decoration, anchor) for fix in FIXES.values()):
                combos.append((dec_id, anc_id))
    return combos


@dataclass
class StoryParams:
    decoration: str
    anchor: str
    fix: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    parent: str
    starter_fix: str
    ship_name: str
    seed: Optional[int] = None


def attempt_outcome(fix: Fix, decoration: Decoration, anchor: Anchor) -> str:
    if not valid_fix(fix, decoration, anchor):
        return "refused"
    if reliable_fix(fix, decoration, anchor):
        return "steady"
    return "slip"


def final_outcome(params: StoryParams) -> str:
    decoration = DECORATIONS[params.decoration]
    anchor = ANCHORS[params.anchor]
    fix = FIXES[params.fix]
    return attempt_outcome(fix, decoration, anchor)


def explain_rejection(decoration: Decoration, anchor: Anchor) -> str:
    if not can_hold(decoration, anchor):
        return (
            f"(No story: {anchor.phrase} is too flimsy for {decoration.phrase}. "
            f"A pirate decoration that cannot be held up leaves no honest problem-solving win.)"
        )
    return (
        f"(No story: none of the sensible fixes in this world fit {anchor.phrase}. "
        f"The children need a real way to fasten the decoration.)"
    )


def explain_fix_rejection(fix: Fix, anchor: Anchor) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it is too weak on common sense here "
            f"(sense={fix.sense} < {SENSE_MIN}). Pick a steadier, more careful fix.)"
        )
    if not fits_surface(fix, anchor):
        return (
            f"(Refusing fix '{fix.id}': {fix.label} does not suit {anchor.phrase}. "
            f"Choose a fix that can really attach to that surface.)"
        )
    return "(Refusing fix: this choice does not fit the problem.)"


def introduce(world: World, captain: Entity, mate: Entity, anchor: Anchor, ship_name: str) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id} turned the living room into a pirate ship named {ship_name}. "
        f"{anchor.scene_line}"
    )
    world.say(
        f'"Captain {captain.id}!" cried {mate.id}. "If we are sailing for treasure, our ship needs one special decoration."'
    )


def choose_decoration(world: World, captain: Entity, mate: Entity, decoration: Decoration) -> None:
    world.say(
        f"They chose {decoration.phrase}. {decoration.style_line} "
        f'"It is decorative and perfect for a pirate ship," said {captain.id}.'
    )


def first_attempt(world: World, captain: Entity, mate: Entity, starter: Fix, decoration: Decoration, anchor: Anchor) -> None:
    world.say(
        f"First they tried {starter.phrase}. {captain.id} {starter.action_line.format(decoration=decoration.label, anchor=anchor.label)}."
    )
    world.say(
        f"For one small moment, the {decoration.label} seemed to stay."
    )


def slip(world: World, decoration: Decoration, anchor: Anchor, count: int) -> None:
    adverb = {1: "Then", 2: "Again", 3: "And again"}.get(count, "Again")
    world.say(
        f'{adverb}, the {decoration.label} slipped from the {anchor.label} and drooped sadly to one side.'
    )


def feel_problem(world: World, captain: Entity, mate: Entity) -> None:
    captain.memes["frustration"] += 1
    mate.memes["frustration"] += 1
    world.say(
        f'"Oh no," said {mate.id}. "{captain.id}, our ship keeps looking lopsided."'
    )


def think_together(world: World, captain: Entity, mate: Entity, decoration: Decoration, anchor: Anchor) -> None:
    captain.memes["thinking"] += 1
    mate.memes["thinking"] += 1
    world.say(
        f"They looked at the {decoration.label}, looked at the {anchor.label}, and looked again. "
        f'"Too heavy for a quick little fix," {captain.id} murmured.'
    )
    world.say(
        f'"We need something steadier," said {mate.id}. "Not just once. Every time it slips, we can think again."'
    )


def final_fix_scene(world: World, captain: Entity, mate: Entity, fix: Fix, decoration: Decoration, anchor: Anchor) -> None:
    captain.memes["hope"] += 1
    mate.memes["hope"] += 1
    world.say(
        f"At last they chose {fix.phrase}. Together they {fix.action_line.format(decoration=decoration.label, anchor=anchor.label)}."
    )


def parent_help(world: World, parent: Entity, captain: Entity, mate: Entity, fix: Fix) -> None:
    captain.memes["love"] += 1
    mate.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt beside them, not to do the job for them, but to hold the ship steady while they worked."
    )
    world.say(
        f'"Good pirates solve one small problem at a time," {parent.pronoun()} said. "Try it carefully."'
    )


def steady_result(world: World, decoration: Decoration, anchor: Anchor) -> None:
    deco = world.get("decoration")
    anc = world.get("anchor")
    deco.meters["steady"] += 1
    anc.meters["decorated"] += 1
    world.say(
        f"This time the {decoration.label} stayed fast on the {anchor.label}. It no longer drooped or slid."
    )


def launch(world: World, captain: Entity, mate: Entity, decoration: Decoration, ship_name: str) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    captain.memes["pride"] += 1
    mate.memes["pride"] += 1
    world.say(
        f'Soon the little ship looked bright and brave. The {decoration.label} fluttered in place, and {ship_name} looked ready for sea.'
    )
    world.say(
        f'"Treasure ahead!" shouted {captain.id}. "{ship_name}, sail!"'
    )
    world.say(
        f"And off went the two pirates across the rug waves, grinning at their decorative ship because they had fixed the problem together."
    )


def tell(
    decoration: Decoration,
    anchor: Anchor,
    final_fix: Fix,
    starter_fix: Fix,
    captain_name: str,
    captain_gender: str,
    mate_name: str,
    mate_gender: str,
    parent_type: str,
    ship_name: str,
) -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="anchor", type="anchor", label=anchor.label, phrase=anchor.phrase))
    world.add(Entity(id="decoration", type="decoration", label=decoration.label, phrase=decoration.phrase))

    introduce(world, captain, mate, anchor, ship_name)
    choose_decoration(world, captain, mate, decoration)

    world.para()
    first_attempt(world, captain, mate, starter_fix, decoration, anchor)
    slip(world, decoration, anchor, 1)
    feel_problem(world, captain, mate)
    think_together(world, captain, mate, decoration, anchor)

    retries = 1
    if not reliable_fix(starter_fix, decoration, anchor):
        world.say(
            f"They tried to straighten it once more with {starter_fix.label}, but the {decoration.label} sagged again."
        )
        retries += 1

    world.para()
    parent_help(world, parent, captain, mate, final_fix)
    final_fix_scene(world, captain, mate, final_fix, decoration, anchor)
    steady_result(world, decoration, anchor)

    world.para()
    launch(world, captain, mate, decoration, ship_name)

    world.facts.update(
        captain=captain,
        mate=mate,
        parent=parent,
        decoration_cfg=decoration,
        anchor_cfg=anchor,
        final_fix=final_fix,
        starter_fix=starter_fix,
        retries=retries,
        ship_name=ship_name,
        solved=True,
    )
    return world


DECORATIONS = {
    "banner": Decoration(
        id="banner",
        label="skull banner",
        phrase="a black skull banner with white teeth painted on it",
        weight=2,
        style_line="It rustled when they lifted it, and the painted teeth made it look fierce in the nicest way.",
        tags={"banner", "decorative", "pirate"},
    ),
    "shell_chain": Decoration(
        id="shell_chain",
        label="shell chain",
        phrase="a chain of shiny shells and paper gold circles",
        weight=3,
        style_line="The shells clicked softly together, making a tinkly pirate song.",
        tags={"shells", "decorative", "pirate"},
    ),
    "star_emblem": Decoration(
        id="star_emblem",
        label="gold star emblem",
        phrase="a gold star emblem cut from thick card",
        weight=1,
        style_line="It caught the light and made the ship seem ready for a royal treasure voyage.",
        tags={"star", "decorative", "pirate"},
    ),
}

ANCHORS = {
    "mast": Anchor(
        id="mast",
        label="mast",
        phrase="the broom-handle mast",
        surface="pole",
        capacity=3,
        scene_line="A broom stood tall for the mast, a blanket made the deck, and a striped cushion was the captain's seat.",
        tags={"mast", "ship"},
    ),
    "cabin": Anchor(
        id="cabin",
        label="cabin wall",
        phrase="the cardboard cabin wall",
        surface="flat",
        capacity=2,
        scene_line="A tall box was the captain's cabin, a blanket made the deck, and a pillow hill guarded the treasure bay.",
        tags={"cabin", "ship"},
    ),
    "chest": Anchor(
        id="chest",
        label="treasure chest lid",
        phrase="the shoebox treasure chest lid",
        surface="flat",
        capacity=1,
        scene_line="A shoebox waited as the treasure chest, a blanket made the deck, and a mop handle pointed toward the islands of the sofa.",
        tags={"chest", "ship"},
    ),
}

FIXES = {
    "paper_tape": Fix(
        id="paper_tape",
        label="paper tape",
        phrase="a strip of paper tape",
        strength=1,
        sense=2,
        for_surfaces={"flat"},
        action_line="pressed the {decoration} onto the {anchor} with careful little pats",
        qa_line="pressed it on with paper tape",
        tags={"tape"},
    ),
    "rope_tie": Fix(
        id="rope_tie",
        label="rope tie",
        phrase="a short piece of rope",
        strength=3,
        sense=3,
        for_surfaces={"pole"},
        action_line="looped the rope around the {anchor} and tied the {decoration} on with a sailor's knot",
        qa_line="tied it on with rope",
        tags={"rope"},
    ),
    "clothespin": Fix(
        id="clothespin",
        label="clothespin",
        phrase="a sturdy clothespin",
        strength=2,
        sense=3,
        for_surfaces={"flat"},
        action_line="clipped the {decoration} firmly to the edge of the {anchor}",
        qa_line="clipped it on with a clothespin",
        tags={"clip"},
    ),
    "chewing_gum": Fix(
        id="chewing_gum",
        label="chewing gum",
        phrase="a blob of old chewing gum",
        strength=1,
        sense=1,
        for_surfaces={"flat", "pole"},
        action_line="stuck the {decoration} to the {anchor} with gum",
        qa_line="stuck it on with gum",
        tags={"gum"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
SHIP_NAMES = ["the Bright Parrot", "the Golden Gull", "the Merry Shell", "the Starry Sail"]

KNOWLEDGE = {
    "decorative": [
        (
            "What does decorative mean?",
            "Decorative means something is added to make a place or object look prettier or more special. It is for beauty or style, not just for doing a job.",
        )
    ],
    "pirate": [
        (
            "What is a pirate ship?",
            "A pirate ship is a boat from pirate stories where the crew sails to look for treasure. In pretend play, children can make one from boxes, blankets, and imagination.",
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a long piece of cloth or paper with a picture or sign on it. People hang banners to decorate places or show a message.",
        )
    ],
    "shells": [
        (
            "What are shells?",
            "Shells are the hard covers that some sea animals live in. People sometimes collect pretty shells because they shine and make nice decorations.",
        )
    ],
    "rope": [
        (
            "Why is rope useful on a mast?",
            "Rope can wrap around a pole and hold things tightly in place. That makes it helpful when you need to fasten something to a mast.",
        )
    ],
    "tape": [
        (
            "What does tape do?",
            "Tape helps stick one thing to another thing. Some tape is fine for light jobs, but heavy things can still fall if the tape is not strong enough.",
        )
    ],
    "clip": [
        (
            "What does a clothespin do?",
            "A clothespin is a little clip that pinches things and holds them together. It works best when it can grab onto an edge.",
        )
    ],
    "problem": [
        (
            "What does it mean to solve a problem?",
            "Solving a problem means noticing what is wrong and trying a better idea. Sometimes you have to look, think, and try again before something works.",
        )
    ],
}
KNOWLEDGE_ORDER = ["decorative", "pirate", "banner", "shells", "rope", "tape", "clip", "problem"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    decoration = f["decoration_cfg"]
    anchor = f["anchor_cfg"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the word "decorative" and shows children solving a small problem together.',
        f"Tell a gentle story where {captain.id} and {mate.id} make a pirate ship, try to hang {decoration.phrase}, and keep thinking until it stays on the {anchor.label}.",
        f"Write a happy story with repetition where a decoration slips more than once, then a better idea fixes it and the pretend pirate voyage can begin.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    parent = f["parent"]
    decoration = f["decoration_cfg"]
    anchor = f["anchor_cfg"]
    final_fix = f["final_fix"]
    starter = f["starter_fix"]
    ship_name = f["ship_name"]
    retries = f["retries"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {captain.id} and {mate.id}, pretending to be pirates. {parent.label_word.capitalize()} helps by holding the ship steady while they solve their decorating problem.",
        ),
        (
            "What were they making?",
            f"They were turning the living room into a pirate ship named {ship_name}. They wanted one decorative pirate piece to make the ship look finished and brave.",
        ),
        (
            f"What problem did {captain.id} and {mate.id} have?",
            f"Their {decoration.label} kept slipping from the {anchor.label}. That meant the ship looked droopy instead of ready for adventure.",
        ),
        (
            "How does the story show repetition?",
            f"They tried to put the decoration up, and it slipped. Then they straightened it and it sagged again, so the story repeats the same small problem before the better fix finally works.",
        ),
    ]
    if retries >= 2:
        qa.append(
            (
                f"Why did they stop using {starter.label}?",
                f"They could see that {starter.label} was not holding the {decoration.label} steady. After it slipped again, they realized they needed a stronger or better-shaped fix for that spot.",
            )
        )
    qa.append(
        (
            f"How did they solve the problem?",
            f"They solved it by using {final_fix.phrase} and working together carefully. {final_fix.qa_line.capitalize()}, and that finally held the decoration in place.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily with the decoration staying up and the ship looking ready to sail. Then {captain.id} and {mate.id} launched their pirate game across the rug waves.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"decorative", "pirate", "problem"} | set(f["decoration_cfg"].tags) | set(f["final_fix"].tags)
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
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        decoration="banner",
        anchor="mast",
        fix="rope_tie",
        captain_name="Tom",
        captain_gender="boy",
        mate_name="Lily",
        mate_gender="girl",
        parent="mother",
        starter_fix="paper_tape",
        ship_name="the Bright Parrot",
    ),
    StoryParams(
        decoration="star_emblem",
        anchor="cabin",
        fix="clothespin",
        captain_name="Mia",
        captain_gender="girl",
        mate_name="Ben",
        mate_gender="boy",
        parent="father",
        starter_fix="paper_tape",
        ship_name="the Golden Gull",
    ),
    StoryParams(
        decoration="shell_chain",
        anchor="mast",
        fix="rope_tie",
        captain_name="Sam",
        captain_gender="boy",
        mate_name="Zoe",
        mate_gender="girl",
        parent="mother",
        starter_fix="paper_tape",
        ship_name="the Merry Shell",
    ),
    StoryParams(
        decoration="star_emblem",
        anchor="chest",
        fix="paper_tape",
        captain_name="Ava",
        captain_gender="girl",
        mate_name="Finn",
        mate_gender="boy",
        parent="father",
        starter_fix="paper_tape",
        ship_name="the Starry Sail",
    ),
]


ASP_RULES = r"""
can_hold(D, A) :- decoration(D), anchor(A), weight(D, W), capacity(A, C), C >= W.
fits_surface(F, A) :- fix(F), anchor(A), surface(A, S), for_surface(F, S).
valid_fix(F, A) :- fix(F), anchor(A), sense(F, N), sense_min(M), N >= M, fits_surface(F, A).
reliable_fix(D, A, F) :- decoration(D), anchor(A), fix(F), valid_fix(F, A),
                         weight(D, W), strength(F, T), T >= W.
valid(D, A) :- decoration(D), anchor(A), can_hold(D, A), valid_fix(_, A).

attempt(D, A, F, steady) :- reliable_fix(D, A, F).
attempt(D, A, F, slip) :- valid_fix(F, A), not reliable_fix(D, A, F).
attempt(D, A, F, refused) :- fix(F), not valid_fix(F, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for dec_id, decoration in DECORATIONS.items():
        lines.append(asp.fact("decoration", dec_id))
        lines.append(asp.fact("weight", dec_id, decoration.weight))
    for anc_id, anchor in ANCHORS.items():
        lines.append(asp.fact("anchor", anc_id))
        lines.append(asp.fact("surface", anc_id, anchor.surface))
        lines.append(asp.fact("capacity", anc_id, anchor.capacity))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("strength", fix_id, fix.strength))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for surface in sorted(fix.for_surfaces):
            lines.append(asp.fact("for_surface", fix_id, surface))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_attempt(decoration_id: str, anchor_id: str, fix_id: str) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_decoration", decoration_id),
            asp.fact("chosen_anchor", anchor_id),
            asp.fact("chosen_fix", fix_id),
            "attempt_result(R) :- chosen_decoration(D), chosen_anchor(A), chosen_fix(F), attempt(D, A, F, R).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show attempt_result/1."))
    atoms = asp.atoms(model, "attempt_result")
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

    for dec_id in DECORATIONS:
        for anc_id in ANCHORS:
            for fix_id in FIXES:
                py = attempt_outcome(FIXES[fix_id], DECORATIONS[dec_id], ANCHORS[anc_id])
                asp_out = asp_attempt(dec_id, anc_id, fix_id)
                if py != asp_out:
                    rc = 1
                    print(f"MISMATCH attempt: {(dec_id, anc_id, fix_id)} python={py} asp={asp_out}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirates solve a decorative problem by trying a better fix."
    )
    ap.add_argument("--decoration", choices=DECORATIONS)
    ap.add_argument("--anchor", choices=ANCHORS)
    ap.add_argument("--fix", choices=FIXES)
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def _starter_fix_for(anchor_id: str) -> str:
    anchor = ANCHORS[anchor_id]
    if anchor.surface == "flat":
        return "paper_tape"
    return "paper_tape"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.decoration and args.anchor:
        decoration = DECORATIONS[args.decoration]
        anchor = ANCHORS[args.anchor]
        if (args.decoration, args.anchor) not in set(valid_combos()):
            raise StoryError(explain_rejection(decoration, anchor))

    combos = [
        combo
        for combo in valid_combos()
        if (args.decoration is None or combo[0] == args.decoration)
        and (args.anchor is None or combo[1] == args.anchor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    decoration_id, anchor_id = rng.choice(sorted(combos))
    anchor = ANCHORS[anchor_id]

    if args.fix:
        chosen_fix = FIXES[args.fix]
        if not valid_fix(chosen_fix, DECORATIONS[decoration_id], anchor):
            raise StoryError(explain_fix_rejection(chosen_fix, anchor))
        fix_id = args.fix
    else:
        sensible = [fix_id for fix_id, fix in FIXES.items() if reliable_fix(fix, DECORATIONS[decoration_id], anchor)]
        if not sensible:
            raise StoryError("(No reliable fix matches the chosen decoration and anchor.)")
        fix_id = rng.choice(sorted(sensible))

    captain_name, captain_gender = _pick_kid(rng)
    mate_name, mate_gender = _pick_kid(rng, avoid=captain_name)
    parent = args.parent or rng.choice(["mother", "father"])
    starter_fix = _starter_fix_for(anchor_id)
    ship_name = rng.choice(SHIP_NAMES)

    return StoryParams(
        decoration=decoration_id,
        anchor=anchor_id,
        fix=fix_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        parent=parent,
        starter_fix=starter_fix,
        ship_name=ship_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.decoration not in DECORATIONS:
        raise StoryError(f"(Unknown decoration '{params.decoration}')")
    if params.anchor not in ANCHORS:
        raise StoryError(f"(Unknown anchor '{params.anchor}')")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix '{params.fix}')")
    if params.starter_fix not in FIXES:
        raise StoryError(f"(Unknown starter fix '{params.starter_fix}')")

    decoration = DECORATIONS[params.decoration]
    anchor = ANCHORS[params.anchor]
    final_fix_cfg = FIXES[params.fix]
    starter_fix_cfg = FIXES[params.starter_fix]

    if (params.decoration, params.anchor) not in set(valid_combos()):
        raise StoryError(explain_rejection(decoration, anchor))
    if not valid_fix(final_fix_cfg, decoration, anchor):
        raise StoryError(explain_fix_rejection(final_fix_cfg, anchor))
    if not reliable_fix(final_fix_cfg, decoration, anchor):
        raise StoryError(
            f"(Refusing fix '{params.fix}': it fits the {anchor.label}, but it is not strong enough to hold the {decoration.label} steadily.)"
        )

    world = tell(
        decoration=decoration,
        anchor=anchor,
        final_fix=final_fix_cfg,
        starter_fix=starter_fix_cfg,
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        ship_name=params.ship_name,
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
        print(asp_program("", "#show valid/2.\n#show attempt/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (decoration, anchor) combos:\n")
        for decoration_id, anchor_id in combos:
            fixes = [
                fix_id
                for fix_id, fix in FIXES.items()
                if reliable_fix(fix, DECORATIONS[decoration_id], ANCHORS[anchor_id])
            ]
            print(f"  {decoration_id:12} {anchor_id:8}  fixes=[{', '.join(sorted(fixes))}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain_name} & {p.mate_name}: {p.decoration} on {p.anchor} with {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
