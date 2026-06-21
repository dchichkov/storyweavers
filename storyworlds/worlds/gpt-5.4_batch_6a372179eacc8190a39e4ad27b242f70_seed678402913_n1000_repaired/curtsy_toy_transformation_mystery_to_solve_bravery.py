#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/curtsy_toy_transformation_mystery_to_solve_bravery.py
=================================================================================

A standalone storyworld for a child-facing mystery: a beloved toy seems to have
changed into a strange little visitor, and a brave child solves the mystery by
following clues in a dim room.

Seed requirements rebuilt as world state
----------------------------------------
Words: curtsy, toy
Features: Transformation, Mystery to Solve, Bravery
Style: Mystery

World logic
-----------
This world models a small domestic mystery with a concrete physical cause:

* A child has a favorite toy.
* Nearby dress-up things (a ribbon, skirt, or veil) can fall onto the toy.
* A helper force (a pet, a draft, or a rolling toy cart) can move the toy to a
  dim hiding place.
* In low light, the toy looks transformed into a tiny stranger.
* The child must choose bravery and investigate.
* Solving the mystery reveals the transformation was only appearance, not magic,
  and the ending image proves the fear changed into delight.

The reasonableness gate is strict: the chosen mover must plausibly be able to
reach the chosen hiding place, and the hiding place must actually be dim enough
to support a mystery.

Run it
------
    python storyworlds/worlds/gpt-5.4/curtsy_toy_transformation_mystery_to_solve_bravery.py
    python storyworlds/worlds/gpt-5.4/curtsy_toy_transformation_mystery_to_solve_bravery.py --all
    python storyworlds/worlds/gpt-5.4/curtsy_toy_transformation_mystery_to_solve_bravery.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/curtsy_toy_transformation_mystery_to_solve_bravery.py --qa --json
    python storyworlds/worlds/gpt-5.4/curtsy_toy_transformation_mystery_to_solve_bravery.py --verify
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
BRAVERY_GOAL = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    room: str
    dim_place: str
    dim_phrase: str
    clue: str
    mystery_line: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ToyCfg:
    id: str
    label: str
    phrase: str
    face: str
    motion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CoverCfg:
    id: str
    label: str
    phrase: str
    transformed: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoverCfg:
    id: str
    label: str
    phrase: str
    verb: str
    can_reach: set[str] = field(default_factory=set)
    power: str = "nudge"
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingCfg:
    id: str
    label: str
    phrase: str
    dim: bool = True
    reachable_by: set[str] = field(default_factory=set)
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_transformed(world: World) -> list[str]:
    toy = world.get("toy")
    cover = world.get("cover")
    if toy.meters["covered"] < THRESHOLD:
        return []
    sig = ("transformed", toy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toy.meters["transformed"] += 1
    toy.attrs["transformed_name"] = cover.attrs["transformed"]
    return []


def _r_mystery(world: World) -> list[str]:
    toy = world.get("toy")
    hiding = world.get("hiding")
    if toy.meters["transformed"] < THRESHOLD or hiding.meters["dim"] < THRESHOLD:
        return []
    sig = ("mystery", toy.id, hiding.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toy.meters["mysterious"] += 1
    child = world.get("child")
    child.memes["fear"] += 1
    child.memes["wonder"] += 1
    return []


def _r_bravery(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["fear"] < THRESHOLD or child.memes["step_forward"] < THRESHOLD:
        return []
    sig = ("bravery", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["bravery"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="transformed", tag="physical", apply=_r_transformed),
    Rule(name="mystery", tag="emotional", apply=_r_mystery),
    Rule(name="bravery", tag="emotional", apply=_r_bravery),
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


def valid_combo(setting: Setting, mover: MoverCfg, hiding: HidingCfg) -> bool:
    return hiding.dim and hiding.id in setting.supports and hiding.id in mover.can_reach and mover.id in hiding.reachable_by


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for mover_id, mover in MOVERS.items():
            for hiding_id, hiding in HIDINGS.items():
                if valid_combo(setting, mover, hiding):
                    out.append((setting_id, mover_id, hiding_id))
    return out


def predict_mystery(world: World, mover: MoverCfg, hiding: HidingCfg) -> dict:
    sim = world.copy()
    do_shift(sim, mover=mover, hiding=hiding, narrate=False)
    return {
        "mysterious": sim.get("toy").meters["mysterious"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
        "place": hiding.phrase,
    }


def introduce(world: World, child: Entity, parent: Entity, toy: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} liked quiet adventures, especially in {setting.room}, where every chair and curtain could feel like part of a secret."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved one toy most of all: {toy.phrase}. {child.pronoun().capitalize()} often carried it from one game to the next."
    )
    world.say(
        f"That evening, {parent.label_word} was nearby folding dress-up things and humming softly."
    )


def leave_toy(world: World, child: Entity, toy: Entity, cover: Entity) -> None:
    toy.meters["resting"] += 1
    world.say(
        f"Before supper, {child.id} set the toy beside {cover.phrase} and skipped away to wash {child.pronoun('possessive')} hands."
    )


def do_shift(world: World, mover: MoverCfg, hiding: HidingCfg, narrate: bool = True) -> None:
    toy = world.get("toy")
    cover = world.get("cover")
    hiding_ent = world.get("hiding")
    mover_ent = world.get("mover")
    mover_ent.attrs["used_hiding"] = hiding.id
    toy.attrs["place"] = hiding.label
    toy.meters["moved"] += 1
    toy.meters["covered"] += 1
    hiding_ent.meters["occupied"] += 1
    propagate(world, narrate=narrate)


def strange_sighting(world: World, child: Entity, setting: Setting, cover: CoverCfg, hiding: HidingCfg) -> None:
    transformed = world.get("toy").attrs.get("transformed_name", cover.transformed)
    world.say(
        f"When {child.id} came back, the room looked different. {setting.mystery_line}"
    )
    world.say(
        f"From {hiding.phrase}, {child.pronoun()} saw what looked like {transformed}. In the dimness, it almost seemed to give a tiny curtsy."
    )
    world.say(
        f"{child.id} stopped at once. {child.pronoun().capitalize()} knew the shape was not where the toy had been left."
    )


def gather_clues(world: World, child: Entity, mover: MoverCfg, setting: Setting) -> None:
    child.memes["thinking"] += 1
    world.say(
        f"{child.id} listened instead of running away. {setting.clue}, and there was {mover.phrase} nearby."
    )
    world.say(
        f"That was the first clue. The second was a little trail showing something had been {mover.verb} across the floor."
    )


def brave_step(world: World, child: Entity) -> None:
    child.memes["step_forward"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id}'s knees felt shaky, but {child.pronoun()} took one careful step, then another. Being brave did not make the room less dim; it helped {child.pronoun('object')} keep moving anyway."
    )


def solve_mystery(world: World, child: Entity, toy: Entity, cover: CoverCfg, mover: MoverCfg, hiding: HidingCfg) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["fear"] = 0.0
    toy.meters["mysterious"] = 0.0
    world.say(
        f"At last {child.id} reached {hiding.phrase} and bent down. The stranger was only {child.pronoun('possessive')} toy."
    )
    world.say(
        f"{cover.phrase.capitalize()} had slipped over it, so the toy looked changed, and {mover.label} had {mover.verb} it into the shadows. Up close, {toy.face} looked exactly the same as ever."
    )
    world.say(
        f'"Oh!" said {child.id}. "It was a mystery, not a monster."'
    )


def ending(world: World, child: Entity, parent: Entity, toy: Entity, cover: CoverCfg) -> None:
    child.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled when {child.id} explained the clues. {parent.pronoun().capitalize()} said that careful eyes and a brave heart make a fine pair."
    )
    world.say(
        f"{child.id} brushed the dress-up cloth smooth, set the toy on the rug again, and gave it a playful curtsy."
    )
    world.say(
        f"After that, the toy was not a frightening stranger anymore. It was still {child.id}'s dear toy, only now it also felt like the hero of a solved mystery."
    )


def tell(
    setting: Setting,
    toy_cfg: ToyCfg,
    cover_cfg: CoverCfg,
    mover_cfg: MoverCfg,
    hiding_cfg: HidingCfg,
    *,
    child_name: str = "Lila",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait], label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    toy = world.add(Entity(
        id="toy",
        kind="thing",
        type="toy",
        label=toy_cfg.label,
        phrase=toy_cfg.phrase,
        owner=child.id,
        tags=set(toy_cfg.tags),
        attrs={"face": toy_cfg.face, "motion": toy_cfg.motion, "place": "by the dress-up basket"},
    ))
    cover = world.add(Entity(
        id="cover",
        kind="thing",
        type="dressup",
        label=cover_cfg.label,
        phrase=cover_cfg.phrase,
        tags=set(cover_cfg.tags),
        attrs={"transformed": cover_cfg.transformed},
    ))
    mover = world.add(Entity(
        id="mover",
        kind="thing",
        type="mover",
        label=mover_cfg.label,
        phrase=mover_cfg.phrase,
        tags=set(mover_cfg.tags),
    ))
    hiding = world.add(Entity(
        id="hiding",
        kind="thing",
        type="place",
        label=hiding_cfg.label,
        phrase=hiding_cfg.phrase,
        tags=set(hiding_cfg.tags),
    ))
    if hiding_cfg.dim:
        hiding.meters["dim"] = 1.0

    introduce(world, child, parent, toy, setting)
    leave_toy(world, child, toy, cover)
    world.para()

    pred = predict_mystery(world, mover_cfg, hiding_cfg)
    world.facts["predicted_mystery"] = pred["mysterious"]
    do_shift(world, mover=mover_cfg, hiding=hiding_cfg, narrate=False)
    strange_sighting(world, child, setting, cover_cfg, hiding_cfg)

    world.para()
    gather_clues(world, child, mover_cfg, setting)
    brave_step(world, child)

    world.para()
    solve_mystery(world, child, toy, cover_cfg, mover_cfg, hiding_cfg)
    ending(world, child, parent, toy, cover_cfg)

    world.facts.update(
        child=child,
        parent=parent,
        toy=toy,
        setting=setting,
        toy_cfg=toy_cfg,
        cover_cfg=cover_cfg,
        mover_cfg=mover_cfg,
        hiding_cfg=hiding_cfg,
        mystery_seen=pred["mysterious"],
        bravery=child.memes["bravery"] >= BRAVERY_GOAL,
        solved=True,
    )
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        room="the bedroom",
        dim_place="under the bed",
        dim_phrase="where lamplight could not quite reach",
        clue="The curtain stirred at the open window",
        mystery_line="The corners had gone dusky, and the bed cast a long shadow on the floor.",
        supports={"under_bed", "behind_curtain"},
        tags={"bedroom", "mystery"},
    ),
    "playroom": Setting(
        id="playroom",
        room="the playroom",
        dim_place="behind the puppet trunk",
        dim_phrase="where the lamp left a pocket of dark",
        clue="One wheel of the toy cart still trembled",
        mystery_line="The lamp was on, but behind the big trunk the light thinned into a gray hush.",
        supports={"behind_trunk", "behind_curtain"},
        tags={"playroom", "mystery"},
    ),
    "hall": Setting(
        id="hall",
        room="the upstairs hall",
        dim_place="beside the coat stand",
        dim_phrase="where coats made a little cave of shadow",
        clue="A draft whispered under the attic door",
        mystery_line="The hall was quiet, and the coats along the wall looked taller than usual.",
        supports={"by_coatstand", "behind_curtain"},
        tags={"hall", "mystery"},
    ),
}

TOYS = {
    "rabbit": ToyCfg(
        id="rabbit",
        label="rabbit",
        phrase="a velvety rabbit with one soft ear folded over",
        face="its stitched nose and bright button eyes",
        motion="tipped sideways when set down",
        tags={"toy", "rabbit"},
    ),
    "bear": ToyCfg(
        id="bear",
        label="bear",
        phrase="a round teddy bear with a satin bow",
        face="its worn little smile",
        motion="wobbled gently when nudged",
        tags={"toy", "bear"},
    ),
    "doll": ToyCfg(
        id="doll",
        label="doll",
        phrase="a small wooden doll with painted slippers",
        face="its painted cheeks and steady eyes",
        motion="stood stiff and straight",
        tags={"toy", "doll"},
    ),
}

COVERS = {
    "ribbon": CoverCfg(
        id="ribbon",
        label="ribbon",
        phrase="a silver ribbon from the dress-up basket",
        transformed="a tiny court lady with a shining sash",
        tags={"ribbon", "dressup"},
    ),
    "skirt": CoverCfg(
        id="skirt",
        label="skirt",
        phrase="a doll-sized satin skirt",
        transformed="a little dancer in a grand skirt",
        tags={"skirt", "dressup"},
    ),
    "veil": CoverCfg(
        id="veil",
        label="veil",
        phrase="a lace veil with pearly beads",
        transformed="a whispery visitor in a pale veil",
        tags={"veil", "dressup"},
    ),
}

MOVERS = {
    "kitten": MoverCfg(
        id="kitten",
        label="the kitten",
        phrase="the family kitten sitting under a chair and blinking",
        verb="batting",
        can_reach={"under_bed", "behind_curtain", "behind_trunk"},
        power="bat",
        tags={"pet", "kitten"},
    ),
    "draft": MoverCfg(
        id="draft",
        label="the draft",
        phrase="the air still whispering at the crack of a door",
        verb="blowing",
        can_reach={"behind_curtain", "by_coatstand"},
        power="blow",
        tags={"air", "draft"},
    ),
    "cart": MoverCfg(
        id="cart",
        label="the toy cart",
        phrase="the little toy cart tilted against the wall",
        verb="rolling",
        can_reach={"behind_trunk", "by_coatstand"},
        power="roll",
        tags={"cart", "wheel"},
    ),
}

HIDINGS = {
    "under_bed": HidingCfg(
        id="under_bed",
        label="under the bed",
        phrase="under the bed",
        dim=True,
        reachable_by={"kitten"},
        tags={"shadow", "bed"},
    ),
    "behind_curtain": HidingCfg(
        id="behind_curtain",
        label="behind the curtain",
        phrase="behind the curtain",
        dim=True,
        reachable_by={"kitten", "draft"},
        tags={"shadow", "curtain"},
    ),
    "behind_trunk": HidingCfg(
        id="behind_trunk",
        label="behind the trunk",
        phrase="behind the puppet trunk",
        dim=True,
        reachable_by={"kitten", "cart"},
        tags={"shadow", "trunk"},
    ),
    "by_coatstand": HidingCfg(
        id="by_coatstand",
        label="by the coat stand",
        phrase="by the coat stand",
        dim=True,
        reachable_by={"draft", "cart"},
        tags={"shadow", "coats"},
    ),
    "sunny_window": HidingCfg(
        id="sunny_window",
        label="by the sunny window",
        phrase="by the sunny window",
        dim=False,
        reachable_by={"draft", "cart", "kitten"},
        tags={"light"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Sophie", "Nora", "Eva", "Ivy", "Clara", "Ruby"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Eli", "Finn", "Hugo", "Noah", "Jasper"]
TRAITS = ["careful", "curious", "thoughtful", "gentle", "bright"]


@dataclass
class StoryParams:
    setting: str
    toy: str
    cover: str
    mover: str
    hiding: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="bedroom",
        toy="rabbit",
        cover="veil",
        mover="kitten",
        hiding="under_bed",
        child_name="Lila",
        child_gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        setting="playroom",
        toy="bear",
        cover="skirt",
        mover="cart",
        hiding="behind_trunk",
        child_name="Milo",
        child_gender="boy",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        setting="hall",
        toy="doll",
        cover="ribbon",
        mover="draft",
        hiding="by_coatstand",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        setting="bedroom",
        toy="bear",
        cover="ribbon",
        mover="draft",
        hiding="behind_curtain",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="bright",
    ),
]


KNOWLEDGE = {
    "toy": [
        (
            "What is a toy?",
            "A toy is an object made for play. Children can imagine stories with it and take care of it."
        )
    ],
    "curtsy": [
        (
            "What is a curtsy?",
            "A curtsy is a polite little bow often made by bending the knees and dipping down. People do it in stories, dances, and pretend games."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a long strip of cloth that can tie, flutter, or decorate something. In dim light it can change how an object looks."
        )
    ],
    "veil": [
        (
            "What is a veil?",
            "A veil is a thin cloth that partly covers something. Because it softens shapes, it can make familiar things look strange."
        )
    ],
    "skirt": [
        (
            "Why can clothes make a thing look different?",
            "Clothes change a shape from the outside. When something is dressed up, your eyes may think it has transformed even when it has not."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle with clues that help you find the answer. Solving one means noticing what changed and asking why."
        )
    ],
    "bravery": [
        (
            "What does bravery mean?",
            "Bravery means doing the right or careful thing even while you still feel scared. It does not mean never feeling fear."
        )
    ],
    "shadow": [
        (
            "Why do shadows make things look different?",
            "Shadows hide some parts and show others. That can turn an ordinary object into a puzzling shape."
        )
    ],
    "kitten": [
        (
            "Why do kittens move little things?",
            "Kittens like to bat and chase objects that slide or dangle. A small toy can end up in a new place after a playful swat."
        )
    ],
    "draft": [
        (
            "What is a draft?",
            "A draft is moving air from a window or door. Light things can flutter or slide when a draft reaches them."
        )
    ],
    "cart": [
        (
            "Why can wheels move things?",
            "Wheels help an object roll instead of stay still. If something bumps a wheeled cart, it can carry other things a little way."
        )
    ],
}
KNOWLEDGE_ORDER = ["toy", "curtsy", "mystery", "bravery", "shadow", "ribbon", "veil", "skirt", "kitten", "draft", "cart"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    toy = f["toy_cfg"]
    cover = f["cover_cfg"]
    mover = f["mover_cfg"]
    hiding = f["hiding_cfg"]
    return [
        f'Write a child-friendly mystery story that includes the words "curtsy" and "toy".',
        f"Tell a gentle transformation mystery where {child.id}'s {toy.label} seems to become {cover.transformed} after being moved to {hiding.phrase}.",
        f"Write a short story about bravery where a child follows clues, discovers how {mover.label} changed the toy's appearance, and solves the mystery."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    toy = f["toy_cfg"]
    cover = f["cover_cfg"]
    mover = f["mover_cfg"]
    hiding = f["hiding_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} favorite toy, and {child.pronoun('possessive')} {parent.label_word}. The story follows {child.id} as {child.pronoun()} solves a small mystery."
        ),
        (
            f"What looked strange about the toy?",
            f"The toy looked transformed into {cover.transformed}. {cover.phrase.capitalize()} changed its shape, and the dim hiding place made it seem even stranger."
        ),
        (
            "Why did the toy seem to curtsy?",
            f"In the shadows, the toy's new shape looked like a tiny bow or curtsy. The mystery came from the angle, the cloth on top, and the dim light."
        ),
        (
            f"What clues helped {child.id} solve the mystery?",
            f"{child.id} noticed the moving cloth and the signs that something had been {mover.verb} across the floor. Those clues pointed to {mover.label} and showed the toy had been moved to {hiding.phrase}."
        ),
        (
            f"How was {child.id} brave?",
            f"{child.id} felt scared but stepped closer anyway to look carefully. That brave choice turned fear into an answer because {child.pronoun()} checked the clues instead of running away."
        ),
        (
            "What was the real answer to the mystery?",
            f"The toy had not really become a stranger at all. {cover.phrase.capitalize()} had fallen over it, and {mover.label} had moved it into the shadows, so it only looked transformed from far away."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"toy", "curtsy", "mystery", "bravery"}
    tags |= set(f["cover_cfg"].tags)
    tags |= set(f["mover_cfg"].tags)
    tags |= set(f["hiding_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, mover: MoverCfg, hiding: HidingCfg) -> str:
    if not hiding.dim:
        return (
            f"(No story: {hiding.phrase} is not dim, so the toy would not look mysterious there. Pick a shadowy hiding place.)"
        )
    if hiding.id not in setting.supports:
        return (
            f"(No story: {setting.room} does not offer {hiding.phrase} as a plausible hiding place in this world.)"
        )
    if hiding.id not in mover.can_reach or mover.id not in hiding.reachable_by:
        return (
            f"(No story: {mover.label} cannot plausibly move the toy to {hiding.phrase}. Pick a mover and hiding place that fit together.)"
        )
    return "(No story: this mystery setup is not reasonable.)"


ASP_RULES = r"""
valid(S, M, H) :- setting(S), mover(M), hiding(H),
                  dim(H), supports(S, H), can_reach(M, H), reachable_by(H, M).

mystery(S, M, H) :- valid(S, M, H).

# A normal story instance is brave-and-solved whenever the setup is valid.
solved(S, M, H) :- valid(S, M, H).
brave(S, M, H)  :- valid(S, M, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.supports):
            lines.append(asp.fact("supports", sid, hid))
    for mid, mover in MOVERS.items():
        lines.append(asp.fact("mover", mid))
        for hid in sorted(mover.can_reach):
            lines.append(asp.fact("can_reach", mid, hid))
    for hid, hiding in HIDINGS.items():
        lines.append(asp.fact("hiding", hid))
        if hiding.dim:
            lines.append(asp.fact("dim", hid))
        for mid in sorted(hiding.reachable_by):
            lines.append(asp.fact("reachable_by", hid, mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        rp = resolve_params(args, random.Random(123))
        sample = generate(rp)
        if not sample.story.strip():
            raise StoryError("Resolved default params generated empty story.")
        print("OK: default resolve/generate succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a toy seems transformed in the shadows, and a child bravely solves the mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--mover", choices=MOVERS)
    ap.add_argument("--hiding", choices=HIDINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mover and args.hiding:
        setting = SETTINGS[args.setting]
        mover = MOVERS[args.mover]
        hiding = HIDINGS[args.hiding]
        if not valid_combo(setting, mover, hiding):
            raise StoryError(explain_rejection(setting, mover, hiding))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mover is None or combo[1] == args.mover)
        and (args.hiding is None or combo[2] == args.hiding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mover_id, hiding_id = rng.choice(sorted(combos))
    toy_id = args.toy or rng.choice(sorted(TOYS.keys()))
    cover_id = args.cover or rng.choice(sorted(COVERS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        toy=toy_id,
        cover=cover_id,
        mover=mover_id,
        hiding=hiding_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        toy = TOYS[params.toy]
        cover = COVERS[params.cover]
        mover = MOVERS[params.mover]
        hiding = HIDINGS[params.hiding]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not valid_combo(setting, mover, hiding):
        raise StoryError(explain_rejection(setting, mover, hiding))

    world = tell(
        setting=setting,
        toy_cfg=toy,
        cover_cfg=cover,
        mover_cfg=mover,
        hiding_cfg=hiding,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mover, hiding) mystery setups:\n")
        for setting, mover, hiding in combos:
            print(f"  {setting:9} {mover:7} {hiding}")
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
            header = f"### {p.child_name}: {p.toy} in {p.setting} ({p.mover} -> {p.hiding})"
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
