#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/geometric_curiosity_reconciliation_folk_tale.py
==========================================================================

A standalone story world for a small folk-tale domain about curiosity,
misunderstanding, and reconciliation.

Premise
-------
Two young friends discover or arrange a beautiful geometric pattern from simple
materials such as pebbles, shells, leaves, or tiles. One child grows too
curious and touches the center before the pattern is finished or blessed. The
shape slips out of order, feelings are hurt, and an elder teaches them how to
repair both the pattern and their friendship. The ending image proves what
changed: the pattern returns, but so does trust.

This world prefers plausible combinations only:
- each place affords certain materials;
- each material can reasonably form only some geometric designs;
- each elder has a fitting repair method.

It includes:
- typed entities with physical meters and emotional memes,
- a Python reasonableness gate and an inline ASP twin,
- three Q&A sets generated from simulated state,
- standard CLI modes: random generation, curated set, JSON, trace, ASP, verify.

Run it
------
    python storyworlds/worlds/gpt-5.4/geometric_curiosity_reconciliation_folk_tale.py
    python storyworlds/worlds/gpt-5.4/geometric_curiosity_reconciliation_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/geometric_curiosity_reconciliation_folk_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/geometric_curiosity_reconciliation_folk_tale.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
    type: str = "thing"            # child, elder, pattern, material, place
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "aunt"}
        male = {"boy", "man", "grandfather", "uncle", "ferryman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "gardener": "gardener",
            "ferryman": "ferryman",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Param registries
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    opening: str
    afford_materials: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Pattern:
    id: str
    label: str
    shape_text: str
    center_piece: str
    allowed_materials: set[str]
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    plural: bool = True
    texture: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Elder:
    id: str
    type: str
    label: str
    arrival: str
    method: str
    can_repair: set[str]
    lesson: str
    tags: set[str] = field(default_factory=set)


PLACES = {
    "riverbank": Place(
        "riverbank",
        "the riverbank",
        "Long ago, beside a slow green river, two young friends liked to wander where the reeds whispered.",
        {"pebbles", "shells"},
        tags={"river"},
    ),
    "courtyard": Place(
        "courtyard",
        "the old courtyard",
        "Long ago, in an old courtyard behind a clay house, two young friends played where swallows dipped through the evening air.",
        {"tiles", "pebbles"},
        tags={"village"},
    ),
    "grove": Place(
        "grove",
        "the moonlit grove",
        "Long ago, in a moonlit grove at the edge of the village, two young friends gathered what the wind had left under the trees.",
        {"leaves", "pebbles"},
        tags={"forest"},
    ),
}

PATTERNS = {
    "star": Pattern(
        "star",
        "star",
        "a bright geometric star with six even points",
        "the small center stone",
        {"pebbles", "tiles", "shells"},
        "bright",
        tags={"star", "geometric"},
    ),
    "spiral": Pattern(
        "spiral",
        "spiral",
        "a geometric spiral that curled inward like a sleeping fern",
        "the quiet middle curl",
        {"pebbles", "shells", "leaves"},
        "quiet",
        tags={"spiral", "geometric"},
    ),
    "sunwheel": Pattern(
        "sunwheel",
        "sun wheel",
        "a geometric sun wheel with a round heart and careful rays",
        "the round heart-piece",
        {"pebbles", "tiles"},
        "golden",
        tags={"sun", "geometric"},
    ),
    "kite": Pattern(
        "kite",
        "kite",
        "a geometric kite shape, sharp at the top and broad at the wings",
        "the topmost tip",
        {"tiles", "leaves"},
        "playful",
        tags={"kite", "geometric"},
    ),
}

MATERIALS = {
    "pebbles": Material(
        "pebbles",
        "pebbles",
        "smooth river pebbles",
        plural=True,
        texture="cool and round",
        tags={"pebbles"},
    ),
    "shells": Material(
        "shells",
        "shells",
        "small white shells",
        plural=True,
        texture="pale and shining",
        tags={"shells"},
    ),
    "tiles": Material(
        "tiles",
        "tiles",
        "bright broken tiles",
        plural=True,
        texture="flat and colored",
        tags={"tiles"},
    ),
    "leaves": Material(
        "leaves",
        "leaves",
        "yellow leaves",
        plural=True,
        texture="light and rustling",
        tags={"leaves"},
    ),
}

ELDERS = {
    "grandmother": Elder(
        "grandmother",
        "grandmother",
        "Grandmother",
        "an old grandmother came with a basket on her arm",
        "sort the pieces by edge and color, then rebuild from the middle outward",
        {"pebbles", "shells", "tiles", "leaves"},
        "Curious hands are good hands when they also learn patience.",
        tags={"elder", "sorting"},
    ),
    "gardener": Elder(
        "gardener",
        "gardener",
        "the gardener",
        "the gardener came from the fig trees carrying a willow broom",
        "sweep the scattered pieces into little groups, then lay them back one ring at a time",
        {"leaves", "pebbles", "tiles"},
        "A pattern can be mended, and so can a friendship, if both are tended gently.",
        tags={"elder", "sweeping"},
    ),
    "ferryman": Elder(
        "ferryman",
        "ferryman",
        "the ferryman",
        "the ferryman stepped up from the landing with wet ropes over one shoulder",
        "match the shining edges and make a steady border before touching the center again",
        {"shells", "pebbles"},
        "Wonder is not wrong, but wonder must listen before it reaches.",
        tags={"elder", "matching"},
    ),
}

GIRL_NAMES = ["Lila", "Mira", "Tala", "Nara", "Suri", "Anya"]
BOY_NAMES = ["Ivo", "Milo", "Rian", "Tarin", "Niko", "Oren"]
TRAITS = ["curious", "gentle", "quick", "careful", "bright-eyed", "eager"]


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
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_pattern_disturbed(world: World) -> list[str]:
    out: list[str] = []
    pattern = world.get("pattern")
    if pattern.meters["disturbed"] < THRESHOLD:
        return out
    sig = ("pattern_disturbed",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pattern.meters["scattered"] += 1
    maker = world.get("maker")
    toucher = world.get("toucher")
    maker.memes["hurt"] += 1
    toucher.memes["guilt"] += 1
    out.append("__scatter__")
    return out


def _r_apology_softens(world: World) -> list[str]:
    out: list[str] = []
    maker = world.get("maker")
    toucher = world.get("toucher")
    if toucher.memes["apology"] < THRESHOLD:
        return out
    sig = ("apology_softens",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    maker.memes["anger"] = 0.0
    maker.memes["trust"] += 1
    out.append("__soften__")
    return out


def _r_rebuild_restores(world: World) -> list[str]:
    out: list[str] = []
    pattern = world.get("pattern")
    if pattern.meters["repaired"] < THRESHOLD:
        return out
    sig = ("rebuild_restores",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pattern.meters["whole"] += 1
    maker = world.get("maker")
    toucher = world.get("toucher")
    maker.memes["joy"] += 1
    toucher.memes["relief"] += 1
    maker.memes["friendship"] += 1
    toucher.memes["friendship"] += 1
    out.append("__whole__")
    return out


CAUSAL_RULES = [
    Rule("pattern_disturbed", "physical", _r_pattern_disturbed),
    Rule("apology_softens", "social", _r_apology_softens),
    Rule("rebuild_restores", "physical", _r_rebuild_restores),
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


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def pattern_supported(place: Place, pattern: Pattern, material: Material) -> bool:
    return material.id in place.afford_materials and material.id in pattern.allowed_materials


def elder_can_help(elder: Elder, material: Material) -> bool:
    return material.id in elder.can_repair


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for pattern_id, pattern in PATTERNS.items():
            for material_id, material in MATERIALS.items():
                if not pattern_supported(place, pattern, material):
                    continue
                for elder_id, elder in ELDERS.items():
                    if elder_can_help(elder, material):
                        combos.append((place_id, pattern_id, material_id, elder_id))
    return combos


def explain_rejection(place: Place, pattern: Pattern, material: Material, elder: Elder) -> str:
    if material.id not in place.afford_materials:
        return (
            f"(No story: {place.label} does not naturally offer {material.label}, "
            f"so the children would have no honest way to gather them there.)"
        )
    if material.id not in pattern.allowed_materials:
        return (
            f"(No story: {material.label} do not make a stable {pattern.label} in this world. "
            f"Choose a material that suits that geometric design.)"
        )
    if material.id not in elder.can_repair:
        return (
            f"(No story: {elder.label} is not the right elder to mend a pattern made from "
            f"{material.label}. Pick a helper with a fitting method.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Screenplay helpers
# ---------------------------------------------------------------------------
def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(place.opening)
    world.say(
        f"One was {a.id}, and the other was {b.id}, and each thought the other's company as welcome as shade at noon."
    )


def gather(world: World, maker: Entity, toucher: Entity, material: Material, pattern: Pattern) -> None:
    maker.memes["joy"] += 1
    toucher.memes["joy"] += 1
    pattern_ent = world.get("pattern")
    pattern_ent.meters["forming"] += 1
    world.say(
        f"They gathered {material.phrase}, {material.texture}, and set them down in a ring upon the earth."
    )
    world.say(
        f"Slowly they made {pattern.shape_text}. Even before it was finished, the little design looked as if it had been waiting there all along."
    )


def wonder(world: World, toucher: Entity, pattern: Pattern) -> None:
    toucher.memes["curiosity"] += 1
    world.say(
        f"{toucher.id} bent close and stared at {pattern.center_piece}. "
        f'"Why does the middle make the whole {pattern.label} hold together?" {toucher.pronoun()} asked.'
    )


def caution(world: World, maker: Entity, toucher: Entity, pattern: Pattern) -> None:
    maker.memes["care"] += 1
    world.say(
        f'{maker.id} answered softly, "Do not move {pattern.center_piece} yet. '
        f'If the heart shifts, the rest may wander after it."'
    )


def touch_center(world: World, toucher: Entity, pattern: Pattern, material: Material) -> None:
    toucher.memes["impulse"] += 1
    world.get("pattern").meters["disturbed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But curiosity stepped quicker than patience. {toucher.id} reached out and nudged {pattern.center_piece} with one finger."
    )
    world.say(
        f"At once the {material.label} slipped from their places. The neat {pattern.label} loosened, then scattered into a small untidy hush."
    )


def hurt(world: World, maker: Entity, toucher: Entity) -> None:
    maker.memes["anger"] += 1
    world.say(
        f'{maker.id} drew back. "I asked you to wait," {maker.pronoun()} said, and the hurt in the words was sharper than the sound itself.'
    )
    world.say(
        f"{toucher.id} wished at once that the finger had stayed still."
    )


def elder_arrives(world: World, elder: Entity) -> None:
    elder.memes["calm"] += 1
    world.say(
        f"As they stood in their silence, {world.facts['elder_cfg'].arrival}."
    )


def lesson(world: World, elder: Entity, toucher: Entity, maker: Entity, pattern: Pattern) -> None:
    pred = predict_disturbance(world)
    world.facts["predicted_scatter"] = pred["scatter"]
    world.say(
        f'{elder.label} looked at the loosened pieces and said, "{world.facts["elder_cfg"].lesson}"'
    )
    world.say(
        f'"A shape keeps its promise only when each part is allowed its place. '
        f'And friends are much the same."'
    )


def apology(world: World, toucher: Entity, maker: Entity) -> None:
    toucher.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{toucher.id} bowed {toucher.pronoun("possessive")} head. "I was too quick," {toucher.pronoun()} said. '
        f'"I wanted to know the secret of it, and I spoiled your work. Will you forgive me?"'
    )


def forgive(world: World, maker: Entity, toucher: Entity) -> None:
    maker.memes["forgiveness"] += 1
    world.say(
        f'{maker.id} looked at the scattered pieces, then at {toucher.id}. '
        f'"Yes," {maker.pronoun()} said at last. "But help me make it whole again."'
    )


def rebuild(world: World, maker: Entity, toucher: Entity, elder: Entity, pattern: Pattern, material: Material) -> None:
    world.get("pattern").meters["repaired"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, under {elder.label}'s patient eye, they began to {world.facts['elder_cfg'].method}."
    )
    world.say(
        f"Piece by piece the {material.label} came home to their places, until {pattern.shape_text} shone on the ground once more."
    )


def ending(world: World, maker: Entity, toucher: Entity, pattern: Pattern, place: Place) -> None:
    world.say(
        f"When the last piece rested true, {maker.id} and {toucher.id} smiled at each other as if a knot had been untied between them."
    )
    world.say(
        f"From then on, whenever they found some new and beautiful thing in {place.label}, they asked before they touched, and their friendship grew steadier than the geometric {pattern.label} at their feet."
    )


def predict_disturbance(world: World) -> dict:
    sim = world.copy()
    sim.get("pattern").meters["disturbed"] += 1
    propagate(sim, narrate=False)
    return {
        "scatter": sim.get("pattern").meters["scattered"] >= THRESHOLD,
        "maker_hurt": sim.get("maker").memes["hurt"] >= THRESHOLD,
    }


def tell(
    place: Place,
    pattern: Pattern,
    material: Material,
    elder_cfg: Elder,
    maker_name: str = "Lila",
    maker_gender: str = "girl",
    toucher_name: str = "Milo",
    toucher_gender: str = "boy",
    maker_trait: str = "gentle",
    toucher_trait: str = "curious",
) -> World:
    world = World()
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_gender, role="maker", traits=[maker_trait]))
    toucher = world.add(Entity(id=toucher_name, kind="character", type=toucher_gender, role="toucher", traits=[toucher_trait]))
    elder = world.add(Entity(id=elder_cfg.label, kind="character", type=elder_cfg.type, role="elder", label=elder_cfg.label))
    world.add(Entity(id="pattern", kind="thing", type="pattern", label=pattern.label))
    world.add(Entity(id="material", kind="thing", type="material", label=material.label))
    world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    world.facts.update(
        place=place,
        pattern_cfg=pattern,
        material_cfg=material,
        elder_cfg=elder_cfg,
        maker=maker,
        toucher=toucher,
        elder=elder,
    )

    introduce(world, maker, toucher, place)
    gather(world, maker, toucher, material, pattern)

    world.para()
    wonder(world, toucher, pattern)
    caution(world, maker, toucher, pattern)
    touch_center(world, toucher, pattern, material)
    hurt(world, maker, toucher)

    world.para()
    elder_arrives(world, elder)
    lesson(world, elder, toucher, maker, pattern)
    apology(world, toucher, maker)
    forgive(world, maker, toucher)
    rebuild(world, maker, toucher, elder, pattern, material)

    world.para()
    ending(world, maker, toucher, pattern, place)

    world.facts.update(
        place=place,
        pattern_cfg=pattern,
        material_cfg=material,
        elder_cfg=elder_cfg,
        maker=maker,
        toucher=toucher,
        elder=elder,
        disturbed=world.get("pattern").meters["disturbed"] >= THRESHOLD,
        repaired=world.get("pattern").meters["repaired"] >= THRESHOLD,
        reconciled=maker.memes["forgiveness"] >= THRESHOLD and toucher.memes["apology"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    pattern: str
    material: str
    elder: str
    maker: str
    maker_gender: str
    toucher: str
    toucher_gender: str
    maker_trait: str
    toucher_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "geometric": [(
        "What does geometric mean?",
        "Geometric means made from clear shapes and lines, such as circles, points, and patterns that fit together neatly."
    )],
    "pebbles": [(
        "What are pebbles?",
        "Pebbles are small smooth stones, often found near water. They are good for arranging because they can be set down one by one."
    )],
    "shells": [(
        "What are shells?",
        "Shells are the hard little homes sea creatures leave behind. Their edges and colors can make pretty patterns."
    )],
    "tiles": [(
        "What are tiles?",
        "Tiles are flat pieces of baked clay or stone. Because they have straight edges, people can line them up into shapes."
    )],
    "leaves": [(
        "Why are leaves hard to arrange carefully?",
        "Leaves are light and can slide or blow away. That means you must place them gently if you want the pattern to stay neat."
    )],
    "elder": [(
        "Why do folk tales often have an elder helper?",
        "An elder helper brings patience and wisdom. In many folk tales, the elder helps younger characters see what their feelings would not let them see alone."
    )],
    "apology": [(
        "What is an apology?",
        "An apology is when you say you were wrong and show that you want to repair the hurt you caused. A good apology is honest and leads to better actions."
    )],
    "forgiveness": [(
        "What is forgiveness?",
        "Forgiveness is choosing to let anger loosen after someone truly admits a wrong and tries to mend it. It does not erase what happened, but it can help friendship heal."
    )],
}
KNOWLEDGE_ORDER = ["geometric", "pebbles", "shells", "tiles", "leaves", "elder", "apology", "forgiveness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p, m, pat = f["place"], f["material_cfg"], f["pattern_cfg"]
    maker, toucher = f["maker"], f["toucher"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the word "geometric" and centers curiosity and reconciliation.',
        f"Tell a gentle folk tale where {maker.id} and {toucher.id} make a geometric {pat.label} from {m.label} in {p.label}, curiosity causes a mistake, and the friendship is mended.",
        f"Write a child-facing story in a folk-tale voice where touching a beautiful pattern too soon hurts a friend, and an elder teaches apology, forgiveness, and patient rebuilding.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker, toucher, elder = f["maker"], f["toucher"], f["elder"]
    place, pattern, material = f["place"], f["pattern_cfg"], f["material_cfg"]
    qa = [
        (
            "Who is the story about?",
            f"It is about two young friends, {maker.id} and {toucher.id}, and {elder.label}, who helps them when their trouble begins."
        ),
        (
            f"What were {maker.id} and {toucher.id} making?",
            f"They were arranging {material.phrase} into {pattern.shape_text}. The story calls it geometric because the shape was careful, even, and made from fitting parts."
        ),
        (
            f"Why did {toucher.id} touch the middle of the pattern?",
            f"{toucher.id} was curious and wanted to know why {pattern.center_piece} mattered so much. That question was honest, but {toucher.pronoun()} acted before waiting for the answer."
        ),
    ]
    if f["disturbed"]:
        qa.append((
            "What went wrong?",
            f"When {toucher.id} nudged {pattern.center_piece}, the pattern lost its order and the pieces scattered. That upset {maker.id} because the careful work had been spoiled in a single moment."
        ))
    if f["reconciled"]:
        qa.append((
            f"How did {elder.label} help the children reconcile?",
            f"{elder.label} helped them see that the pattern and the friendship both needed patience. Then {toucher.id} apologized, {maker.id} forgave, and they rebuilt the design together."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the pattern whole again in {place.label} and the friendship steadier than before. The children learned to ask before touching something precious."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"geometric", "elder", "apology", "forgiveness", f["material_cfg"].id}
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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
supported(Place, Pattern, Material) :-
    place(Place), pattern(Pattern), material(Material),
    affords(Place, Material), allows(Pattern, Material).

helpful(Elder, Material) :-
    elder(Elder), material(Material), can_repair(Elder, Material).

valid(Place, Pattern, Material, Elder) :-
    supported(Place, Pattern, Material),
    helpful(Elder, Material).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for material in sorted(place.afford_materials):
            lines.append(asp.fact("affords", pid, material))
    for pat_id, pattern in PATTERNS.items():
        lines.append(asp.fact("pattern", pat_id))
        for material in sorted(pattern.allowed_materials):
            lines.append(asp.fact("allows", pat_id, material))
    for mid in MATERIALS:
        lines.append(asp.fact("material", mid))
    for eid, elder in ELDERS.items():
        lines.append(asp.fact("elder", eid))
        for material in sorted(elder.can_repair):
            lines.append(asp.fact("can_repair", eid, material))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("riverbank", "spiral", "shells", "ferryman", "Lila", "girl", "Milo", "boy", "gentle", "curious"),
    StoryParams("courtyard", "sunwheel", "tiles", "grandmother", "Nara", "girl", "Ivo", "boy", "careful", "eager"),
    StoryParams("grove", "kite", "leaves", "gardener", "Suri", "girl", "Oren", "boy", "bright-eyed", "curious"),
    StoryParams("courtyard", "star", "pebbles", "gardener", "Mira", "girl", "Rian", "boy", "gentle", "quick"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: geometric curiosity and reconciliation in a folk-tale style."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pattern", choices=PATTERNS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.pattern and args.material and args.elder:
        place = PLACES[args.place]
        pattern = PATTERNS[args.pattern]
        material = MATERIALS[args.material]
        elder = ELDERS[args.elder]
        if not (pattern_supported(place, pattern, material) and elder_can_help(elder, material)):
            raise StoryError(explain_rejection(place, pattern, material, elder))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.pattern is None or c[1] == args.pattern)
        and (args.material is None or c[2] == args.material)
        and (args.elder is None or c[3] == args.elder)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, pattern, material, elder = rng.choice(sorted(combos))
    maker_gender = rng.choice(["girl", "boy"])
    toucher_gender = rng.choice(["girl", "boy"])
    maker = _pick_name(rng, maker_gender)
    toucher = _pick_name(rng, toucher_gender, avoid=maker)
    maker_trait = rng.choice(TRAITS)
    toucher_trait = rng.choice(TRAITS)
    return StoryParams(
        place, pattern, material, elder,
        maker, maker_gender, toucher, toucher_gender,
        maker_trait, toucher_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        PATTERNS[params.pattern],
        MATERIALS[params.material],
        ELDERS[params.elder],
        params.maker,
        params.maker_gender,
        params.toucher,
        params.toucher_gender,
        params.maker_trait,
        params.toucher_trait,
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
        print(f"{len(combos)} compatible (place, pattern, material, elder) combos:\n")
        for place, pattern, material, elder in combos:
            print(f"  {place:10} {pattern:9} {material:8} {elder}")
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
            header = f"### {p.maker} and {p.toucher}: {p.pattern} of {p.material} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
