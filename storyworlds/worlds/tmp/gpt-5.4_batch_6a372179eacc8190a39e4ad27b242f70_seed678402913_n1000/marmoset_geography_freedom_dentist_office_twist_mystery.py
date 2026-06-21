#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/marmoset_geography_freedom_dentist_office_twist_mystery.py
=====================================================================================

A standalone story world for a tiny mystery in a dentist office.

Domain sketch
-------------
A child arrives at a dentist office feeling nervous. In the waiting room there is
a little geography corner with maps, a globe, and a mascot marmoset toy. Then the
marmoset goes missing. A clue points toward one hiding place, the child whispers
about freedom and escape, and an adult helper investigates. The twist is that no
wild animal is loose at all: the "missing marmoset" is a toy or puppet that got
stuck in an ordinary, physical way. Solving the mystery calms the child for the
dentist visit.

Reasonableness constraint
-------------------------
Not every mascot can plausibly end up in every hiding place.

* a wind-up marmoset can roll under the dental chair base
* a scarf-wearing plush marmoset can snag in the brochure rack
* a finger puppet marmoset can slip behind the globe stand

The rescue method must match the hiding place as well. The world refuses
unreasonable pairings and exposes the same constraint through an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/marmoset_geography_freedom_dentist_office_twist_mystery.py
    python storyworlds/worlds/gpt-5.4/marmoset_geography_freedom_dentist_office_twist_mystery.py --mascot windup --hiding chair_base
    python storyworlds/worlds/gpt-5.4/marmoset_geography_freedom_dentist_office_twist_mystery.py --mascot plush --hiding chair_base
    python storyworlds/worlds/gpt-5.4/marmoset_geography_freedom_dentist_office_twist_mystery.py --all
    python storyworlds/worlds/gpt-5.4/marmoset_geography_freedom_dentist_office_twist_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/marmoset_geography_freedom_dentist_office_twist_mystery.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "dentist_f", "hygienist_f", "receptionist_f"}
        male = {"boy", "father", "dad", "man", "dentist_m", "hygienist_m", "receptionist_m"}
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
            "dentist_f": "dentist",
            "dentist_m": "dentist",
            "hygienist_f": "hygienist",
            "hygienist_m": "hygienist",
            "receptionist_f": "receptionist",
            "receptionist_m": "receptionist",
        }
        return mapping.get(self.type, self.type or self.label)


@dataclass
class Mascot:
    id: str
    label: str
    phrase: str
    motion: str
    clue_text: str
    false_guess: str
    twist_reveal: str
    can_roll: bool = False
    can_snag: bool = False
    can_slip: bool = False
    makes_sound: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    trap_type: str
    clue_style: str
    suspicion: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
    trap_type: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperRole:
    id: str
    label: str
    type_f: str
    type_m: str
    opening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_trapped_clue(world: World) -> list[str]:
    mascot = world.entities.get("mascot")
    child = world.entities.get("child")
    room = world.entities.get("room")
    if mascot is None or child is None or room is None:
        return []
    if mascot.meters["trapped"] < THRESHOLD:
        return []
    sig = ("trapped_clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["mystery"] += 1
    child.memes["curiosity"] += 1
    child.memes["jitters"] += 1
    return ["__clue__"]


def _r_solved_calms(world: World) -> list[str]:
    child = world.entities.get("child")
    mascot = world.entities.get("mascot")
    if child is None or mascot is None:
        return []
    if mascot.meters["free"] < THRESHOLD:
        return []
    sig = ("solved_calms",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["calm"] += 2
    child.memes["bravery"] += 1
    child.memes["fear"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="trapped_clue", tag="mystery", apply=_r_trapped_clue),
    Rule(name="solved_calms", tag="emotion", apply=_r_solved_calms),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(mascot: Mascot, hiding: HidingPlace) -> bool:
    if hiding.trap_type == "roll":
        return mascot.can_roll
    if hiding.trap_type == "snag":
        return mascot.can_snag
    if hiding.trap_type == "slip":
        return mascot.can_slip
    return False


def select_rescue(hiding: HidingPlace, rescue_id: Optional[str] = None) -> Rescue:
    if rescue_id is not None:
        if rescue_id not in RESCUES:
            raise StoryError(f"(Unknown rescue '{rescue_id}'.)")
        rescue = RESCUES[rescue_id]
        if rescue.sense < SENSE_MIN:
            raise StoryError(explain_rescue(rescue_id))
        if rescue.trap_type != hiding.trap_type:
            raise StoryError(explain_bad_rescue(hiding, rescue))
        return rescue
    options = [r for r in RESCUES.values() if r.sense >= SENSE_MIN and r.trap_type == hiding.trap_type]
    if not options:
        raise StoryError("(No sensible rescue fits this hiding place.)")
    return options[0]


def predict_clue(mascot: Mascot, hiding: HidingPlace) -> dict:
    return {
        "mystery": valid_combo(mascot, hiding),
        "sound": mascot.makes_sound and hiding.id == "chair_base",
        "visible_wobble": hiding.id == "brochure_rack",
    }


def introduce(world: World, child: Entity, parent: Entity, helper: Entity) -> None:
    world.say(
        f"{child.id} went to the dentist office with {child.pronoun('possessive')} "
        f"{parent.label_word}. The room smelled like mint, and the bright floor "
        f"made every little sound seem crisp."
    )
    world.say(
        f"{child.id} felt a flutter in {child.pronoun('possessive')} tummy about "
        f"the checkup, so {helper.label_word} pointed to the waiting-room geography corner."
    )


def geography_corner(world: World, mascot: Mascot) -> None:
    world.say(
        "There was a paper world map on the wall, a spinning globe on a low stand, "
        "and a basket of travel cards that asked children to match animals to places."
    )
    world.say(
        f"On the top shelf sat {mascot.phrase}, the little marmoset mascot for the "
        "geography game."
    )


def vanish(world: World, child: Entity, mascot: Entity) -> None:
    mascot.meters["missing"] += 1
    child.memes["fear"] += 1
    world.say(
        f"But when {child.id} looked back, the marmoset was gone. The shelf had a "
        "small empty patch where it usually sat."
    )


def clue_appears(world: World, mascot_cfg: Mascot, hiding: HidingPlace, child: Entity) -> None:
    mascot = world.get("mascot")
    mascot.meters["trapped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {mascot_cfg.clue_text} {hiding.clue_style}. The whole dentist office "
        "suddenly felt like the start of a mystery."
    )
    world.say(
        f'"Maybe the marmoset wanted freedom," {child.id} whispered. '
        f'{mascot_cfg.false_guess}'
    )


def ask_helper(world: World, child: Entity, helper: Entity, hiding: HidingPlace, mascot_cfg: Mascot) -> None:
    pred = predict_clue(mascot_cfg, hiding)
    extra = ""
    if pred["sound"]:
        extra = " The sound was too tiny and regular to be a real jungle animal."
    elif pred["visible_wobble"]:
        extra = " Something in the rack gave a small nervous tremble."
    world.say(
        f'{child.id} tugged at {helper.label_word}\'s sleeve and pointed toward '
        f'{hiding.phrase}.{extra}'
    )
    world.say(
        f'{helper.label_word.capitalize()} crouched down, listening carefully, and did not laugh.'
    )


def solve(world: World, helper: Entity, mascot_cfg: Mascot, hiding: HidingPlace, rescue: Rescue) -> None:
    mascot = world.get("mascot")
    mascot.meters["trapped"] = 0.0
    mascot.meters["free"] += 1
    world.get("room").meters["mystery"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"With slow fingers, {helper.label_word} {rescue.text}."
    )
    world.say(mascot_cfg.twist_reveal)
    world.say(
        f"It had not run away for freedom at all; it had simply been stuck in {hiding.label}."
    )


def comfort(world: World, child: Entity, helper: Entity, parent: Entity) -> None:
    world.say(
        f'{child.id} let out a long breath, and the scary flutter in '
        f'{child.pronoun("possessive")} tummy eased.'
    )
    world.say(
        f'"You solved a very small mystery very carefully," {helper.label_word} said. '
        f'{parent.label_word.capitalize()} squeezed {child.pronoun("possessive")} hand.'
    )


def ending(world: World, child: Entity, helper: Entity, mascot_cfg: Mascot, hiding: HidingPlace) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Before the dentist called {child.id}'s name, {helper.label_word} set the "
        f"marmoset beside the globe again."
    )
    world.say(
        f"{child.id} touched the world map, then smiled at the little marmoset. "
        f"{hiding.ending_image}"
    )
    world.say(
        f"For the first time that morning, the dentist office did not feel like a trap. "
        f"It felt bright, knowable, and almost adventurous."
    )


def tell(
    mascot_cfg: Mascot,
    hiding: HidingPlace,
    rescue: Rescue,
    helper_role: HelperRole,
    child_name: str = "Nora",
    child_gender: str = "girl",
    parent_type: str = "mother",
    helper_gender: str = "female",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    helper_type = helper_role.type_f if helper_gender == "female" else helper_role.type_m
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_role.label, role="helper"))
    room = world.add(Entity(id="room", kind="thing", type="room", label="dentist office"))
    mascot = world.add(
        Entity(
            id="mascot",
            kind="thing",
            type="toy",
            label=mascot_cfg.label,
            phrase=mascot_cfg.phrase,
            tags=set(mascot_cfg.tags),
        )
    )

    child.memes["fear"] = 1.0
    child.memes["hope"] = 1.0

    introduce(world, child, parent, helper)
    geography_corner(world, mascot_cfg)

    world.para()
    vanish(world, child, mascot)
    clue_appears(world, mascot_cfg, hiding, child)
    ask_helper(world, child, helper, hiding, mascot_cfg)

    world.para()
    solve(world, helper, mascot_cfg, hiding, rescue)
    comfort(world, child, helper, parent)

    world.para()
    ending(world, child, helper, mascot_cfg, hiding)

    world.facts.update(
        child=child,
        parent=parent,
        helper=helper,
        mascot_cfg=mascot_cfg,
        hiding=hiding,
        rescue=rescue,
        solved=mascot.meters["free"] >= THRESHOLD,
        child_name=child_name,
    )
    return world


MASCOTS = {
    "windup": Mascot(
        id="windup",
        label="wind-up marmoset",
        phrase="a little wind-up marmoset with bright tin eyes",
        motion="roll",
        clue_text="a tiny chittering click came from somewhere low",
        false_guess="Maybe it had escaped to look at the whole world by itself.",
        twist_reveal="The twist was simple and funny: the wind-up toy had rolled off the shelf, bonked the chair base, and kept chittering under it.",
        can_roll=True,
        makes_sound=True,
        tags={"marmoset", "toy", "mystery"},
    ),
    "plush": Mascot(
        id="plush",
        label="plush marmoset",
        phrase="a soft plush marmoset wearing a striped explorer scarf",
        motion="snag",
        clue_text="one travel brochure kept bobbing as if something inside had sighed",
        false_guess="Maybe it had climbed away because shelf life felt too still for such a curious face.",
        twist_reveal="The twist was not wild at all: the plush toy's scarf had caught in the rack, and every swinging brochure made it seem like a secret creature was hiding there.",
        can_snag=True,
        tags={"marmoset", "plush", "mystery"},
    ),
    "puppet": Mascot(
        id="puppet",
        label="finger-puppet marmoset",
        phrase="a tiny finger-puppet marmoset with felt paws",
        motion="slip",
        clue_text="a row of little paper footprint stickers curved behind the globe stand",
        false_guess="Maybe it had sneaked off to start a journey across the map all on its own.",
        twist_reveal="The twist was hidden in plain sight: the finger puppet had slipped behind the globe stand when a child spun the world too fast, and the paper footprints were only part of the geography game.",
        can_slip=True,
        tags={"marmoset", "puppet", "mystery"},
    ),
}

HIDING_PLACES = {
    "chair_base": HidingPlace(
        id="chair_base",
        label="the round base of a dentist chair",
        phrase="the round base of the big dentist chair",
        trap_type="roll",
        clue_style="from under the round base of the big dentist chair",
        suspicion="The low sound made it seem as if something alive were hiding near the chair.",
        ending_image="The toy sat on the shelf again, and its tiny wheels were still.",
        tags={"chair", "dentist"},
    ),
    "brochure_rack": HidingPlace(
        id="brochure_rack",
        label="the brochure rack",
        phrase="the tall rack of shiny toothbrush brochures",
        trap_type="snag",
        clue_style="from the tall rack of shiny toothbrush brochures",
        suspicion="The wobbling paper made the rack look full of whispers.",
        ending_image="The plush tail hung safely over the shelf edge, no longer caught in paper.",
        tags={"brochure", "dentist"},
    ),
    "globe_stand": HidingPlace(
        id="globe_stand",
        label="the globe stand",
        phrase="the low globe stand under the map",
        trap_type="slip",
        clue_style="across the floor and behind the low globe stand",
        suspicion="The paper prints made the map corner look as if a tiny traveler had really passed through.",
        ending_image="The puppet leaned against the globe, as if it had finished its trip around the world.",
        tags={"globe", "geography"},
    ),
}

RESCUES = {
    "roll_chair": Rescue(
        id="roll_chair",
        label="roll the chair back",
        trap_type="roll",
        sense=3,
        text="gently pressed the pedal and rolled the chair back just enough to reach beneath the base",
        qa_text="rolled the chair back a little and reached the toy safely",
        tags={"chair", "help"},
    ),
    "untangle_scarf": Rescue(
        id="untangle_scarf",
        label="untangle the scarf",
        trap_type="snag",
        sense=3,
        text="pinched the striped scarf free from the metal rack and lifted the plush toy out",
        qa_text="freed the plush toy by untangling its scarf from the rack",
        tags={"rack", "help"},
    ),
    "tilt_globe": Rescue(
        id="tilt_globe",
        label="tilt the globe stand",
        trap_type="slip",
        sense=3,
        text="steadied the globe with one hand and tilted the stand just enough for the little puppet to slide out",
        qa_text="held the globe steady and slid the puppet out from behind the stand",
        tags={"globe", "help"},
    ),
    "poke_with_ruler": Rescue(
        id="poke_with_ruler",
        label="poke with a ruler",
        trap_type="roll",
        sense=1,
        text="jabbed at the dark space with a ruler",
        qa_text="poked around with a ruler",
        tags={"bad_idea"},
    ),
}

HELPERS = {
    "dentist": HelperRole(
        id="dentist",
        label="the dentist",
        type_f="dentist_f",
        type_m="dentist_m",
        opening="The dentist liked to speak softly so children felt brave.",
        tags={"dentist"},
    ),
    "hygienist": HelperRole(
        id="hygienist",
        label="the hygienist",
        type_f="hygienist_f",
        type_m="hygienist_m",
        opening="The hygienist always noticed little details.",
        tags={"hygienist"},
    ),
    "receptionist": HelperRole(
        id="receptionist",
        label="the receptionist",
        type_f="receptionist_f",
        type_m="receptionist_m",
        opening="The receptionist knew every corner of the waiting room.",
        tags={"receptionist"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ella", "Ava"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Theo", "Finn"]


@dataclass
class StoryParams:
    mascot: str
    hiding: str
    helper: str
    child_name: str
    child_gender: str
    parent: str
    helper_gender: str
    rescue: Optional[str] = None
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        mascot="windup",
        hiding="chair_base",
        helper="dentist",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        helper_gender="female",
        rescue="roll_chair",
    ),
    StoryParams(
        mascot="plush",
        hiding="brochure_rack",
        helper="receptionist",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        helper_gender="female",
        rescue="untangle_scarf",
    ),
    StoryParams(
        mascot="puppet",
        hiding="globe_stand",
        helper="hygienist",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        helper_gender="male",
        rescue="tilt_globe",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for mascot_id, mascot in MASCOTS.items():
        for hiding_id, hiding in HIDING_PLACES.items():
            if valid_combo(mascot, hiding):
                combos.append((mascot_id, hiding_id))
    return sorted(combos)


def explain_rejection(mascot: Mascot, hiding: HidingPlace) -> str:
    if hiding.trap_type == "roll":
        return (
            f"(No story: {mascot.phrase} cannot plausibly roll under a chair base. "
            f"Choose a wind-up marmoset for {hiding.label}.)"
        )
    if hiding.trap_type == "snag":
        return (
            f"(No story: {mascot.phrase} has nothing that could snag in the brochure rack. "
            f"Choose the plush marmoset with the scarf.)"
        )
    return (
        f"(No story: {mascot.phrase} would not naturally slip behind the globe stand. "
        f"Choose the finger-puppet marmoset for that hiding place.)"
    )


def explain_rescue(rescue_id: str) -> str:
    rescue = RESCUES[rescue_id]
    return (
        f"(Refusing rescue '{rescue_id}': it scores too low on common sense "
        f"(sense={rescue.sense} < {SENSE_MIN}). Choose a gentler, more fitting rescue.)"
    )


def explain_bad_rescue(hiding: HidingPlace, rescue: Rescue) -> str:
    return (
        f"(No story: rescue '{rescue.id}' does not match {hiding.label}. "
        f"The helper needs a method that fits a {hiding.trap_type} problem.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mascot = f["mascot_cfg"]
    hiding = f["hiding"]
    return [
        'Write a gentle mystery story for a 3-to-5-year-old set in a dentist office that includes the words "marmoset", "geography", and "freedom".',
        f"Tell a dentist-office mystery where {child.label} notices that a marmoset mascot is missing from a geography corner, whispers about freedom, and asks {helper.label_word} for help.",
        f"Write a story with a small twist: what first seems like an escaped marmoset near {hiding.label} turns out to be {mascot.label} stuck in an ordinary way.",
    ]


KNOWLEDGE = {
    "marmoset": [
        (
            "What is a marmoset?",
            "A marmoset is a very small monkey with quick hands and a long tail. In this story, the marmoset is a toy mascot, not a wild animal loose in the office.",
        )
    ],
    "geography": [
        (
            "What is geography?",
            "Geography is learning about places in the world, like countries, oceans, animals, and maps. A globe and a wall map are both geography tools.",
        )
    ],
    "freedom": [
        (
            "What does freedom mean?",
            "Freedom means being able to move or choose without being stuck. In the story, the child first imagines the marmoset wanted freedom, but really it just needed help getting unstuck.",
        )
    ],
    "dentist": [
        (
            "What does a dentist do?",
            "A dentist checks teeth and helps keep them clean and healthy. Dentist offices often try to help children feel calm and brave.",
        )
    ],
    "globe": [
        (
            "What is a globe?",
            "A globe is a round model of Earth. It helps you see where oceans and countries are.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem you solve by noticing clues and thinking carefully. Good clues help you find what really happened.",
        )
    ],
}
KNOWLEDGE_ORDER = ["marmoset", "geography", "freedom", "dentist", "globe", "mystery"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper = f["helper"]
    mascot = f["mascot_cfg"]
    hiding = f["hiding"]
    rescue = f["rescue"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, who came to the dentist office with {child.pronoun('possessive')} {parent.label_word}. It is also about {helper.label_word}, who helps solve the tiny mystery.",
        ),
        (
            "What made the dentist office feel like a mystery?",
            f"The marmoset mascot was suddenly missing from the geography corner, and then a strange clue appeared near {hiding.label}. That made the waiting room feel secret and puzzling instead of ordinary.",
        ),
        (
            f"Why did {child.label} whisper about freedom?",
            f"{child.label} first imagined that the missing marmoset had escaped because it wanted freedom. That guess came from the empty shelf and the odd clue, before {helper.label_word} discovered the toy was only stuck.",
        ),
        (
            "What was the twist?",
            f"The twist was that no real animal had escaped at all. The missing marmoset was actually {mascot.label}, and it had become stuck in {hiding.label} in a simple physical way.",
        ),
        (
            f"How did {helper.label_word} solve the problem?",
            f"{helper.label_word.capitalize()} {rescue.qa_text}. That careful rescue set the toy free without making the waiting room scary.",
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                f"How did the mystery change {child.label}'s feelings about the dentist office?",
                f"At first {child.label} felt jittery about the checkup and the missing toy made the room feel even stranger. After the mystery was solved, the office felt understandable again, and that helped {child.label} feel calmer and braver.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"marmoset", "geography", "freedom", "dentist", "mystery"}
    if world.facts["hiding"].id == "globe_stand":
        tags.add("globe")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_hide(M, H) :- rolls(M), hiding(H), trap(H, roll).
can_hide(M, H) :- snags(M), hiding(H), trap(H, snag).
can_hide(M, H) :- slips(M), hiding(H), trap(H, slip).

sensible_rescue(R) :- rescue(R), sense(R, S), sense_min(M), S >= M.
fits_rescue(H, R) :- hiding(H), rescue(R), trap(H, T), handles(R, T).

valid(M, H) :- mascot(M), hiding(H), can_hide(M, H).

usable(M, H, R) :- valid(M, H), sensible_rescue(R), fits_rescue(H, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mascot_id, mascot in MASCOTS.items():
        lines.append(asp.fact("mascot", mascot_id))
        if mascot.can_roll:
            lines.append(asp.fact("rolls", mascot_id))
        if mascot.can_snag:
            lines.append(asp.fact("snags", mascot_id))
        if mascot.can_slip:
            lines.append(asp.fact("slips", mascot_id))
    for hiding_id, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hiding_id))
        lines.append(asp.fact("trap", hiding_id, hiding.trap_type))
    for rescue_id, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rescue_id))
        lines.append(asp.fact("handles", rescue_id, rescue.trap_type))
        lines.append(asp.fact("sense", rescue_id, rescue.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_usable() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show usable/3."))
    return sorted(set(asp.atoms(model, "usable")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny dentist-office mystery about a missing marmoset mascot."
    )
    ap.add_argument("--mascot", choices=sorted(MASCOTS))
    ap.add_argument("--hiding", choices=sorted(HIDING_PLACES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--rescue", choices=sorted(RESCUES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["female", "male"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mascot is not None and args.mascot not in MASCOTS:
        raise StoryError(f"(Unknown mascot '{args.mascot}'.)")
    if args.hiding is not None and args.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place '{args.hiding}'.)")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{args.helper}'.)")

    if args.mascot and args.hiding:
        mascot = MASCOTS[args.mascot]
        hiding = HIDING_PLACES[args.hiding]
        if not valid_combo(mascot, hiding):
            raise StoryError(explain_rejection(mascot, hiding))

    if args.rescue:
        if args.rescue not in RESCUES:
            raise StoryError(f"(Unknown rescue '{args.rescue}'.)")
        rescue = RESCUES[args.rescue]
        if rescue.sense < SENSE_MIN:
            raise StoryError(explain_rescue(args.rescue))
        if args.hiding and rescue.trap_type != HIDING_PLACES[args.hiding].trap_type:
            raise StoryError(explain_bad_rescue(HIDING_PLACES[args.hiding], rescue))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mascot is None or combo[0] == args.mascot)
        and (args.hiding is None or combo[1] == args.hiding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mascot_id, hiding_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    helper_gender = args.helper_gender or rng.choice(["female", "male"])
    rescue = select_rescue(HIDING_PLACES[hiding_id], args.rescue).id

    return StoryParams(
        mascot=mascot_id,
        hiding=hiding_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        helper_gender=helper_gender,
        rescue=rescue,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mascot not in MASCOTS:
        raise StoryError(f"(Unknown mascot '{params.mascot}'.)")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place '{params.hiding}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    mascot = MASCOTS[params.mascot]
    hiding = HIDING_PLACES[params.hiding]
    if not valid_combo(mascot, hiding):
        raise StoryError(explain_rejection(mascot, hiding))
    rescue = select_rescue(hiding, params.rescue)
    world = tell(
        mascot_cfg=mascot,
        hiding=hiding,
        rescue=rescue,
        helper_role=HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        helper_gender=params.helper_gender,
    )
    # Replace child id with display name in final story.
    story = world.render().replace("child", params.child_name)
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP valid combos match Python ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    expected_usable = {
        (m_id, h_id, select_rescue(HIDING_PLACES[h_id]).id)
        for (m_id, h_id) in valid_combos()
    }
    asp_use = set(asp_usable())
    if expected_usable == asp_use:
        print(f"OK: ASP usable triples match rescue logic ({len(asp_use)} triples).")
    else:
        rc = 1
        print("MISMATCH in usable triples:")
        if asp_use - expected_usable:
            print("  only in clingo:", sorted(asp_use - expected_usable))
        if expected_usable - asp_use:
            print("  only in python:", sorted(expected_usable - asp_use))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test produced empty story.)")
        if "marmoset" not in sample.story.lower():
            raise StoryError("(Smoke test story is missing required seed word 'marmoset'.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show usable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        usable = asp_usable()
        print(f"{len(usable)} usable (mascot, hiding, rescue) triples:\n")
        for mascot, hiding, rescue in usable:
            print(f"  {mascot:8} {hiding:13} {rescue}")
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
            header = f"### {p.child_name}: {p.mascot} in {p.hiding} ({p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
