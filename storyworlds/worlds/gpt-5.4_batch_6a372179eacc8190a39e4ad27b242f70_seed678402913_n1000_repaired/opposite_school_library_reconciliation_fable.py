#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/opposite_school_library_reconciliation_fable.py
============================================================================

A small storyworld for a fable-like school-library tale about two classmates
with opposite ideas who learn to reconcile.

The world models:
- two animal students in a school library
- a shared book display they must build together
- opposite impulses (up high vs spread wide)
- a calm method for reconciliation
- either a smooth compromise or a wobble that leads to guided reconciliation

The reasonableness gate only allows display arrangements that a chosen library
surface can really support, and only allows sensible reconciliation methods.
An inline ASP twin mirrors both the gate and the outcome model.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "sheep", "doe", "female"}
        male = {"boy", "buck", "male"}
        if self.attrs.get("gender") == "girl" or self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.attrs.get("gender") == "boy" or self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Surface:
    id: str
    label: str
    phrase: str
    width: int
    stability: int
    rolling: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Arrangement:
    id: str
    label: str
    phrase: str
    needs_width: int
    needs_stability: int
    fragility: int
    opening_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    calm_bonus: int
    helper: bool = False
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


@dataclass
class StoryParams:
    surface: str
    arrangement: str
    method: str
    student1: str
    student2: str
    species1: str
    species2: str
    gender1: str
    gender2: str
    trait1: str
    trait2: str
    librarian: str
    seed: Optional[int] = None


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


def _r_tension_spills(world: World) -> list[str]:
    display = world.get("display")
    if display.meters["pull"] < THRESHOLD:
        return []
    sig = ("tension", "display")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for sid in ("student1", "student2"):
        world.get(sid).memes["upset"] += 1
    display.meters["wobble"] += 1
    return ["__wobble__"]


CAUSAL_RULES = [
    Rule(name="tension_spills", tag="social", apply=_r_tension_spills),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SURFACES = {
    "reading_table": Surface(
        id="reading_table",
        label="reading table",
        phrase="the broad reading table by the picture-book rug",
        width=3,
        stability=3,
        rolling=False,
        tags={"table", "library"},
    ),
    "display_cart": Surface(
        id="display_cart",
        label="display cart",
        phrase="the rolling display cart near the front desk",
        width=2,
        stability=2,
        rolling=True,
        tags={"cart", "library"},
    ),
    "window_sill": Surface(
        id="window_sill",
        label="window sill",
        phrase="the sunny window sill beside the beanbag chairs",
        width=1,
        stability=2,
        rolling=False,
        tags={"window", "library"},
    ),
}

ARRANGEMENTS = {
    "tower": Arrangement(
        id="tower",
        label="tower",
        phrase="a tall tower of bright books",
        needs_width=1,
        needs_stability=3,
        fragility=2,
        opening_line="stacked straight up like a tiny castle",
        ending_image="The books stood in one neat tall tower, with a small card at the bottom so nobody had to tug again.",
        tags={"tower", "books"},
    ),
    "row": Arrangement(
        id="row",
        label="row",
        phrase="a long row of bright books",
        needs_width=3,
        needs_stability=1,
        fragility=1,
        opening_line="spread in a long row so every cover could be seen",
        ending_image="The books stretched in a cheerful row, cover beside cover, like friends standing shoulder to shoulder.",
        tags={"row", "books"},
    ),
    "arch": Arrangement(
        id="arch",
        label="arch",
        phrase="a little rainbow arch of bright books",
        needs_width=2,
        needs_stability=2,
        fragility=2,
        opening_line="curved into a little arch, half high and half wide",
        ending_image="The books made a gentle arch, and it looked as if each side was holding the other up.",
        tags={"arch", "books"},
    ),
    "paired": Arrangement(
        id="paired",
        label="paired stacks",
        phrase="two matching little stacks with room between them",
        needs_width=2,
        needs_stability=1,
        fragility=1,
        opening_line="split into two matching stacks, one for each idea",
        ending_image="Two small stacks framed the sign, and the empty space between them felt calm instead of lonely.",
        tags={"paired", "books"},
    ),
}

METHODS = {
    "measure_together": Method(
        id="measure_together",
        label="measure together",
        sense=3,
        calm_bonus=2,
        helper=False,
        text="set a ruler down on the table and asked them to measure the space before either one moved another book",
        qa_text="They measured the space together before moving the books.",
        tags={"ruler", "cooperate"},
    ),
    "whisper_turns": Method(
        id="whisper_turns",
        label="whisper turns",
        sense=3,
        calm_bonus=1,
        helper=False,
        text="asked them to use whisper voices and take turns naming one good thing in the other one's idea",
        qa_text="They used whisper voices and took turns saying one good thing about the other idea.",
        tags={"whisper", "cooperate"},
    ),
    "ask_librarian": Method(
        id="ask_librarian",
        label="ask the librarian",
        sense=3,
        calm_bonus=1,
        helper=True,
        text="came over with a warm smile and asked each child to give one hand to the sign instead of pulling it apart",
        qa_text="The librarian guided them and had each child help with the same sign instead of pulling against the other.",
        tags={"librarian", "cooperate"},
    ),
    "grab_first": Method(
        id="grab_first",
        label="grab first",
        sense=1,
        calm_bonus=0,
        helper=False,
        text="let them snatch books first and talk later",
        qa_text="They grabbed first instead of talking.",
        tags={"grab"},
    ),
}

SPECIES = {
    "mouse": {"type": "mouse", "word": "mouse"},
    "rabbit": {"type": "rabbit", "word": "rabbit"},
    "turtle": {"type": "turtle", "word": "turtle"},
    "squirrel": {"type": "squirrel", "word": "squirrel"},
    "fox": {"type": "fox", "word": "fox"},
    "duck": {"type": "duck", "word": "duck"},
}

GIRL_NAMES = ["Mina", "Poppy", "Lila", "Tess", "Nora", "Bree"]
BOY_NAMES = ["Pip", "Otis", "Finn", "Milo", "Jasper", "Toby"]
TRAITS = ["patient", "careful", "gentle", "proud", "hasty", "stubborn"]
CALM_TRAITS = {"patient", "careful", "gentle"}

KNOWLEDGE = {
    "library": [
        (
            "What is a library?",
            "A library is a place full of books where people read, borrow stories, and use quiet voices so everyone can think.",
        )
    ],
    "table": [
        (
            "Why is a broad table good for a book display?",
            "A broad table gives books enough space to rest without crowding each other. When things fit well, they are less likely to wobble or fall.",
        )
    ],
    "cart": [
        (
            "Why can a rolling cart make a stack wobble?",
            "A rolling cart can move a little when someone bumps or pulls near it. That tiny movement can make a careful stack lean.",
        )
    ],
    "window": [
        (
            "Why is a narrow window sill hard to use for many books?",
            "A narrow sill does not give books much room. When there is not enough room, the books can slide or get crowded.",
        )
    ],
    "tower": [
        (
            "Why does a tall tower of books need a steady place?",
            "A tall stack needs a strong, still base under it. If the place is shaky, the top can lean even when the bottom looks fine.",
        )
    ],
    "row": [
        (
            "Why is a row of books easy to see?",
            "A row lets many covers face outward at once. That helps readers notice colors, titles, and pictures more easily.",
        )
    ],
    "arch": [
        (
            "Why does an arch shape need balance on both sides?",
            "An arch only looks right when both sides help hold the shape. If one side is pushed too hard, the whole curve can slip.",
        )
    ],
    "ruler": [
        (
            "How can measuring help people stop arguing?",
            "Measuring gives both people the same clear fact to look at. That can calm a quarrel because the choice is no longer only about feelings.",
        )
    ],
    "whisper": [
        (
            "Why do whisper voices help in a library?",
            "Whisper voices keep the room peaceful for readers. They also slow people down enough to listen to each other.",
        )
    ],
    "librarian": [
        (
            "What does a librarian do besides lend books?",
            "A librarian helps people care for books and share the room kindly. Sometimes a librarian also helps solve small problems fairly.",
        )
    ],
    "cooperate": [
        (
            "What does it mean to cooperate?",
            "To cooperate means to work together toward one goal. People cooperate when they listen, share, and let both hands help the same job.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "library",
    "table",
    "cart",
    "window",
    "tower",
    "row",
    "arch",
    "ruler",
    "whisper",
    "librarian",
    "cooperate",
]


def support_surface(surface: Surface, arrangement: Arrangement) -> bool:
    return surface.width >= arrangement.needs_width and surface.stability >= arrangement.needs_stability


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, surface in SURFACES.items():
        for aid, arrangement in ARRANGEMENTS.items():
            if support_surface(surface, arrangement):
                combos.append((sid, aid))
    return combos


def trait_calm_value(trait: str) -> int:
    return 1 if trait in CALM_TRAITS else 0


def pressure_of(surface: Surface, arrangement: Arrangement, trait1: str, trait2: str) -> int:
    pressure = 4 + arrangement.fragility
    if surface.rolling:
        pressure += 1
    if trait1 in {"proud", "stubborn", "hasty"}:
        pressure += 1
    if trait2 in {"proud", "stubborn", "hasty"}:
        pressure += 1
    return pressure


def calm_of(method: Method, trait1: str, trait2: str) -> int:
    calm = method.calm_bonus + trait_calm_value(trait1) + trait_calm_value(trait2)
    if method.helper:
        calm += 1
    return calm


def outcome_of(params: StoryParams) -> str:
    if params.surface not in SURFACES or params.arrangement not in ARRANGEMENTS or params.method not in METHODS:
        raise StoryError("(Invalid params: unknown surface, arrangement, or method.)")
    return "smooth" if calm_of(METHODS[params.method], params.trait1, params.trait2) >= pressure_of(
        SURFACES[params.surface],
        ARRANGEMENTS[params.arrangement],
        params.trait1,
        params.trait2,
    ) else "guided"


def explain_surface(surface: Surface, arrangement: Arrangement) -> str:
    return (
        f"(No story: {arrangement.phrase} does not fit safely on {surface.phrase}. "
        f"It needs width {arrangement.needs_width} and stability {arrangement.needs_stability}, "
        f"but that surface only has width {surface.width} and stability {surface.stability}.)"
    )


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_wobble(world: World, arrangement: Arrangement) -> dict:
    sim = world.copy()
    display = sim.get("display")
    display.meters["pull"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": display.meters["wobble"] >= THRESHOLD,
        "upset": sum(sim.get(sid).memes["upset"] for sid in ("student1", "student2")),
        "pressure": sim.facts["pressure"],
    }


def introduce(world: World, s1: Entity, s2: Entity, librarian: Entity, surface: Surface) -> None:
    world.say(
        f"In the school library, {librarian.id} asked {s1.id} the {s1.type} and {s2.id} the {s2.type} "
        f"to make a welcome display on {surface.phrase}."
    )
    world.say(
        f"The morning sun touched the covers of the books, and the whole room smelled like paper, glue, and quiet."
    )


def show_opposites(world: World, s1: Entity, s2: Entity) -> None:
    s1.memes["wish_up"] += 1
    s2.memes["wish_wide"] += 1
    world.say(
        f'{s1.id} wanted the books up high where everyone could notice them at once, '
        f'but {s2.id} wanted them spread low so every cover could shine. Their ideas felt opposite from the very start.'
    )
    world.say(
        f'"High is best," said {s1.id}. "Wide is best," said {s2.id}.'
    )


def assignment(world: World, arrangement: Arrangement) -> None:
    world.say(
        f"They were meant to build {arrangement.phrase}, {arrangement.opening_line}."
    )


def warning(world: World, librarian: Entity, arrangement: Arrangement) -> None:
    pred = predict_wobble(world, arrangement)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_upset"] = pred["upset"]
    world.say(
        f'{librarian.id} watched their paws creep toward the same pile and said softly, '
        f'"When two helpers pull against each other, books do not feel helped."'
    )


def pull_apart(world: World, s1: Entity, s2: Entity) -> None:
    display = world.get("display")
    display.meters["pull"] += 1
    s1.memes["defiance"] += 1
    s2.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {s1.id} nudged one stack upward at the very same moment {s2.id} tugged another stack sideways."
    )


def smooth_reconcile(
    world: World,
    s1: Entity,
    s2: Entity,
    librarian: Entity,
    arrangement: Arrangement,
    method: Method,
) -> None:
    world.say(
        f"{librarian.id} {method.text}."
    )
    s1.memes["listened"] += 1
    s2.memes["listened"] += 1
    s1.memes["trust"] += 1
    s2.memes["trust"] += 1
    world.say(
        f"Soon {s1.id} noticed that {s2.id}'s idea could help, and {s2.id} noticed the same about {s1.id}'s idea."
    )
    world.say(
        f"Instead of tugging in opposite ways, they used both ideas at once and built the display together."
    )
    world.say(arrangement.ending_image)


def guided_reconcile(
    world: World,
    s1: Entity,
    s2: Entity,
    librarian: Entity,
    arrangement: Arrangement,
    method: Method,
) -> None:
    display = world.get("display")
    display.meters["slipped"] += 1
    world.say("The top books gave a tiny shiver. One slid, then another, and the whole little display slumped with a papery sigh.")
    world.say(
        f"{s1.id} stepped back. {s2.id} stepped back too. Neither child liked the sound of books falling."
    )
    world.para()
    world.say(
        f"{librarian.id} {method.text}."
    )
    world.say(
        f'"First, each of you tell one true good thing about the other idea," said {librarian.id}.'
    )
    world.say(
        f'{s1.id} admitted that a wide shape helped readers see more covers. {s2.id} admitted that a taller shape helped the sign get noticed.'
    )
    s1.memes["apology"] += 1
    s2.memes["apology"] += 1
    s1.memes["trust"] += 1
    s2.memes["trust"] += 1
    world.say(
        f'Then {s1.id} said, "I am sorry for pulling." {s2.id} said, "I am sorry too."'
    )
    world.say(
        f"Together they rebuilt the books with slower paws and kinder voices."
    )
    world.say(arrangement.ending_image)


def moral(world: World, outcome: str) -> None:
    world.para()
    if outcome == "smooth":
        world.say("And so the library kept its quiet, the books kept their places, and two opposite ideas became one gentle plan.")
    else:
        world.say("And so the library grew quiet again, because even opposite hearts can meet in the middle when pride steps aside.")
    world.say("Moral: In a shared room, the kindest hands do not pull against each other; they work together.")


def tell(
    surface: Surface,
    arrangement: Arrangement,
    method: Method,
    student1_name: str,
    student2_name: str,
    species1: str,
    species2: str,
    gender1: str,
    gender2: str,
    trait1: str,
    trait2: str,
    librarian_name: str,
) -> World:
    world = World()
    s1 = world.add(
        Entity(
            id=student1_name,
            kind="character",
            type=species1,
            role="student1",
            traits=[trait1],
            attrs={"gender": gender1},
        )
    )
    s2 = world.add(
        Entity(
            id=student2_name,
            kind="character",
            type=species2,
            role="student2",
            traits=[trait2],
            attrs={"gender": gender2},
        )
    )
    librarian = world.add(
        Entity(
            id=librarian_name,
            kind="character",
            type="owl",
            role="librarian",
            traits=["calm", "fair"],
            attrs={"gender": "girl"},
        )
    )
    display = world.add(
        Entity(
            id="display",
            type="display",
            label=arrangement.label,
            phrase=arrangement.phrase,
            tags=set(arrangement.tags) | set(surface.tags),
        )
    )

    pressure = pressure_of(surface, arrangement, trait1, trait2)
    calm = calm_of(method, trait1, trait2)
    outcome = "smooth" if calm >= pressure else "guided"
    world.facts["pressure"] = pressure
    world.facts["calm"] = calm

    introduce(world, s1, s2, librarian, surface)
    assignment(world, arrangement)

    world.para()
    show_opposites(world, s1, s2)
    warning(world, librarian, arrangement)
    pull_apart(world, s1, s2)

    world.para()
    if outcome == "smooth":
        smooth_reconcile(world, s1, s2, librarian, arrangement, method)
    else:
        guided_reconcile(world, s1, s2, librarian, arrangement, method)

    moral(world, outcome)

    world.facts.update(
        student1=s1,
        student2=s2,
        librarian=librarian,
        surface=surface,
        arrangement=arrangement,
        method=method,
        outcome=outcome,
        reconciled=True,
        slipped=display.meters["slipped"] >= THRESHOLD,
        opposite=True,
    )
    return world


def pair_noun(s1: Entity, s2: Entity) -> str:
    return f"two classmates, {s1.id} and {s2.id}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s1, s2 = f["student1"], f["student2"]
    arrangement, method = f["arrangement"], f["method"]
    outcome = f["outcome"]
    base = (
        f'Write a short fable for a 3-to-5-year-old set in a school library where two animal classmates have opposite ideas about a book display and must reconcile. Include the word "opposite".'
    )
    if outcome == "smooth":
        return [
            base,
            f"Tell a gentle story where {s1.id} and {s2.id} pause before a quarrel grows, then use {method.label} to build {arrangement.phrase} together.",
            "Write a child-facing fable in which two helpers stop pulling against each other and discover that both ideas can belong in the same plan.",
        ]
    return [
        base,
        f"Tell a fable where {s1.id} and {s2.id} tug in opposite directions, the books slump, and then reconciliation begins with a calm grown-up's guidance.",
        "Write a school-library story where pride makes a shared task wobble, but apology and teamwork rebuild it into something peaceful.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    s1, s2 = f["student1"], f["student2"]
    librarian = f["librarian"]
    surface, arrangement, method = f["surface"], f["arrangement"], f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(s1, s2)} and {librarian.id}, the calm librarian. They were working together in the school library.",
        ),
        (
            "What problem did the two classmates have?",
            f"They had opposite ideas about how to build the book display. {s1.id} wanted the books high, while {s2.id} wanted them wide and low.",
        ),
        (
            "Where were they building the display?",
            f"They were building it on {surface.phrase}. That detail matters because some book shapes need more room or steadiness than others.",
        ),
        (
            "Why did the librarian warn them?",
            f"{librarian.id} could see that both children were reaching for the same books in opposite ways. If they pulled against each other, the display could wobble and feelings could get hurt too.",
        ),
    ]
    if outcome == "smooth":
        qa.append(
            (
                "How did they reconcile before anything fell?",
                f"They used {method.label} and slowed themselves down. That gave them time to notice one good thing in each idea and build one shared plan instead of two fighting plans.",
            )
        )
    else:
        qa.append(
            (
                "What happened when they tugged in opposite directions?",
                "The little display slumped and some books slipped out of place. The wobble showed them that pulling against each other was hurting the job instead of helping it.",
            )
        )
        qa.append(
            (
                "How did they make peace after the books slipped?",
                f"{librarian.id} stepped in and helped each child name one good thing in the other idea. Then they apologized and rebuilt the display together with slower, kinder hands.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the books arranged as {arrangement.phrase} and the room feeling peaceful again. The final picture proves they were reconciled because both children were helping the same display instead of pulling apart.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"library"} | set(f["surface"].tags) | set(f["arrangement"].tags) | set(f["method"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} calm={world.facts.get('calm')} pressure={world.facts.get('pressure')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        surface="reading_table",
        arrangement="arch",
        method="measure_together",
        student1="Pip",
        student2="Mina",
        species1="mouse",
        species2="rabbit",
        gender1="boy",
        gender2="girl",
        trait1="patient",
        trait2="careful",
        librarian="Ms. Olive",
    ),
    StoryParams(
        surface="display_cart",
        arrangement="paired",
        method="ask_librarian",
        student1="Finn",
        student2="Tess",
        species1="fox",
        species2="turtle",
        gender1="boy",
        gender2="girl",
        trait1="proud",
        trait2="gentle",
        librarian="Ms. Olive",
    ),
    StoryParams(
        surface="reading_table",
        arrangement="row",
        method="whisper_turns",
        student1="Nora",
        student2="Milo",
        species1="duck",
        species2="squirrel",
        gender1="girl",
        gender2="boy",
        trait1="stubborn",
        trait2="careful",
        librarian="Ms. Olive",
    ),
    StoryParams(
        surface="reading_table",
        arrangement="tower",
        method="ask_librarian",
        student1="Poppy",
        student2="Otis",
        species1="rabbit",
        species2="mouse",
        gender1="girl",
        gender2="boy",
        trait1="hasty",
        trait2="patient",
        librarian="Ms. Olive",
    ),
]


ASP_RULES = r"""
supports(S, A) :- surface(S), arrangement(A),
                  width(S, W), need_width(A, NW), W >= NW,
                  stability(S, St), need_stability(A, NS), St >= NS.

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(S, A) :- supports(S, A).

calm_trait(T) :- trait_kind(T), calm_value(T, 1).
spiky_trait(T) :- trait_kind(T), spiky_value(T, 1).

pressure(P) :-
    chosen_surface(S), chosen_arrangement(A),
    fragility(A, F),
    rolling_value(S, R),
    chosen_trait1(T1), spiky_value(T1, S1),
    chosen_trait2(T2), spiky_value(T2, S2),
    P = 4 + F + R + S1 + S2.

calm(C) :-
    chosen_method(M),
    calm_bonus(M, B),
    helper_value(M, H),
    chosen_trait1(T1), calm_value(T1, C1),
    chosen_trait2(T2), calm_value(T2, C2),
    C = B + H + C1 + C2.

outcome(smooth) :- calm(C), pressure(P), C >= P.
outcome(guided) :- calm(C), pressure(P), C < P.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, surface in SURFACES.items():
        lines.append(asp.fact("surface", sid))
        lines.append(asp.fact("width", sid, surface.width))
        lines.append(asp.fact("stability", sid, surface.stability))
        lines.append(asp.fact("rolling_value", sid, 1 if surface.rolling else 0))
    for aid, arrangement in ARRANGEMENTS.items():
        lines.append(asp.fact("arrangement", aid))
        lines.append(asp.fact("need_width", aid, arrangement.needs_width))
        lines.append(asp.fact("need_stability", aid, arrangement.needs_stability))
        lines.append(asp.fact("fragility", aid, arrangement.fragility))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("calm_bonus", mid, method.calm_bonus))
        lines.append(asp.fact("helper_value", mid, 1 if method.helper else 0))
    for trait in TRAITS:
        lines.append(asp.fact("trait_kind", trait))
        lines.append(asp.fact("calm_value", trait, 1 if trait in CALM_TRAITS else 0))
        lines.append(asp.fact("spiky_value", trait, 1 if trait in {"proud", "stubborn", "hasty"} else 0))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_surface", params.surface),
            asp.fact("chosen_arrangement", params.arrangement),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_trait1", params.trait1),
            asp.fact("chosen_trait2", params.trait2),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  clingo:", sorted(asp_sens))
        print("  python:", sorted(py_sensible))

    cases = list(CURATED)
    for seed in range(60):
        rng = random.Random(seed)
        try:
            p = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)
    mismatches = []
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches.append((p, asp_outcome(p), outcome_of(p)))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")
        for p, aout, pout in mismatches[:5]:
            print(f"  {p} -> clingo={aout} python={pout}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not buf.getvalue().strip():
            raise StoryError("(Smoke test failed: emit produced no output.)")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: opposite ideas in a school library become reconciliation."
    )
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--arrangement", choices=ARRANGEMENTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--trait1", choices=TRAITS)
    ap.add_argument("--trait2", choices=TRAITS)
    ap.add_argument("--student1")
    ap.add_argument("--student2")
    ap.add_argument("--species1", choices=SPECIES)
    ap.add_argument("--species2", choices=SPECIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (surface, arrangement) combos and sensible methods from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface and args.arrangement:
        surface = SURFACES[args.surface]
        arrangement = ARRANGEMENTS[args.arrangement]
        if not support_surface(surface, arrangement):
            raise StoryError(explain_surface(surface, arrangement))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.surface is None or combo[0] == args.surface)
        and (args.arrangement is None or combo[1] == args.arrangement)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    surface_id, arrangement_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    gender1 = rng.choice(["girl", "boy"])
    gender2 = rng.choice(["girl", "boy"])
    student1 = args.student1 or _pick_name(rng, gender1)
    student2 = args.student2 or _pick_name(rng, gender2, avoid=student1)
    species1 = args.species1 or rng.choice(sorted(SPECIES))
    species2 = args.species2 or rng.choice(sorted(SPECIES))
    trait1 = args.trait1 or rng.choice(TRAITS)
    trait2 = args.trait2 or rng.choice(TRAITS)
    return StoryParams(
        surface=surface_id,
        arrangement=arrangement_id,
        method=method_id,
        student1=student1,
        student2=student2,
        species1=species1,
        species2=species2,
        gender1=gender1,
        gender2=gender2,
        trait1=trait1,
        trait2=trait2,
        librarian="Ms. Olive",
    )


def generate(params: StoryParams) -> StorySample:
    if params.surface not in SURFACES:
        raise StoryError(f"(Invalid params: unknown surface '{params.surface}'.)")
    if params.arrangement not in ARRANGEMENTS:
        raise StoryError(f"(Invalid params: unknown arrangement '{params.arrangement}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid params: unknown method '{params.method}'.)")
    if params.species1 not in SPECIES or params.species2 not in SPECIES:
        raise StoryError("(Invalid params: unknown species.)")
    if params.trait1 not in TRAITS or params.trait2 not in TRAITS:
        raise StoryError("(Invalid params: unknown trait.)")

    surface = SURFACES[params.surface]
    arrangement = ARRANGEMENTS[params.arrangement]
    method = METHODS[params.method]

    if not support_surface(surface, arrangement):
        raise StoryError(explain_surface(surface, arrangement))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        surface=surface,
        arrangement=arrangement,
        method=method,
        student1_name=params.student1,
        student2_name=params.student2,
        species1=params.species1,
        species2=params.species2,
        gender1=params.gender1,
        gender2=params.gender2,
        trait1=params.trait1,
        trait2=params.trait2,
        librarian_name=params.librarian,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (surface, arrangement) combos:\n")
        for surface, arrangement in combos:
            print(f"  {surface:14} {arrangement}")
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
            header = f"### {p.student1} and {p.student2}: {p.arrangement} on {p.surface} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
