#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fluorescence_suspense_mystery_to_solve_adventure.py
===============================================================================

A standalone story world about a small adventure with suspense and a mystery to
solve. Two children find glowing clues, worry that something strange is hiding
nearby, and then solve the mystery by noticing fluorescence with the right tool.

Run it
------
    python storyworlds/worlds/gpt-5.4/fluorescence_suspense_mystery_to_solve_adventure.py
    python storyworlds/worlds/gpt-5.4/fluorescence_suspense_mystery_to_solve_adventure.py --place sea_cave --source algae --trail footprints
    python storyworlds/worlds/gpt-5.4/fluorescence_suspense_mystery_to_solve_adventure.py --trail leaves
    python storyworlds/worlds/gpt-5.4/fluorescence_suspense_mystery_to_solve_adventure.py --method shout_for_monster
    python storyworlds/worlds/gpt-5.4/fluorescence_suspense_mystery_to_solve_adventure.py --all
    python storyworlds/worlds/gpt-5.4/fluorescence_suspense_mystery_to_solve_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fluorescence_suspense_mystery_to_solve_adventure.py --verify
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
        female = {"girl", "mother", "woman", "ranger_woman"}
        male = {"boy", "father", "man", "ranger_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "ranger_woman": "guide",
            "ranger_man": "guide",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path_text: str
    hush_text: str
    final_image: str
    supports: set[str] = field(default_factory=set)
    trail_kinds: set[str] = field(default_factory=set)
    guide_type: str = "ranger_woman"
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    owner: str
    glow_text: str
    reveal_text: str
    creature: str
    supports: set[str] = field(default_factory=set)
    trail_kinds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Trail:
    id: str
    label: str
    phrase: str
    marks_text: str
    location_text: str
    leads_text: str
    trail_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    requires_uv: bool
    suspense_text: str
    solve_text: str
    fail_text: str
    qa_text: str
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
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.fired = set(self.fired)
        new.paragraphs = [[]]
        new.facts = copy.deepcopy(self.facts)
        return new


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear_from_dark(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role != "child":
            continue
        if ent.meters["darkness"] < THRESHOLD:
            continue
        sig = ("fear_dark", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] += 1
        out.append("__suspense__")
    return out


def _r_uv_reveals(world: World) -> list[str]:
    source = world.entities.get("source")
    trail = world.entities.get("trail")
    tool = world.entities.get("tool")
    if not source or not trail or not tool:
        return []
    if tool.meters["uv_on"] < THRESHOLD:
        return []
    sig = ("uv_reveal", source.id, trail.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trail.meters["bright_glow"] += 1
    source.meters["identified"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "child":
            ent.memes["curiosity"] += 1
            ent.memes["fear"] = max(0.0, ent.memes["fear"] - 1.0)
            ent.memes["relief"] += 1
    return [source.attrs.get("reveal_line", "")]


CAUSAL_RULES = [
    Rule(name="fear_from_dark", tag="emotion", apply=_r_fear_from_dark),
    Rule(name="uv_reveals", tag="physical", apply=_r_uv_reveals),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def trail_fits(place: Place, trail: Trail) -> bool:
    return trail.trail_kind in place.trail_kinds


def source_fits(place: Place, source: Source, trail: Trail) -> bool:
    return (
        source.id in place.supports
        and source.id in trail.tags
        and trail.trail_kind in source.trail_kinds
    )


def method_sensible(method: Method) -> bool:
    return method.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            for trail_id, trail in TRAILS.items():
                if trail_fits(place, trail) and source_fits(place, source, trail):
                    combos.append((place_id, source_id, trail_id))
    return combos


def explain_combo_rejection(place: Place, source: Source, trail: Trail) -> str:
    if not trail_fits(place, trail):
        return (
            f"(No story: {trail.phrase} do not fit {place.label}. "
            f"Pick a trail that could really appear there.)"
        )
    return (
        f"(No story: {source.phrase} would not plausibly leave {trail.phrase} in "
        f"{place.label}. The mystery clues need a believable fluorescent source.)"
    )


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(mid for mid, m in METHODS.items() if method_sensible(m)))
    return (
        f"(Refusing method '{method_id}': it is too unreasonable for solving a "
        f"mystery safely. Try one of: {better}.)"
    )


def predict_solution(world: World, method: Method) -> dict:
    sim = world.copy()
    if method.requires_uv:
        sim.get("tool").meters["uv_on"] += 1
    if method_sensible(method):
        sim.facts["solved"] = True
    propagate(sim, narrate=False)
    return {
        "solved": sim.get("source").meters["identified"] >= THRESHOLD or sim.facts.get("solved", False),
        "glow": sim.get("trail").meters["bright_glow"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    for child in (a, b):
        child.memes["joy"] += 1
    world.say(
        f"At dusk, {a.id} and {b.id} set out on a small adventure in {place.label}. "
        f"{place.opening}"
    )
    world.say(place.path_text)


def discover(world: World, a: Entity, b: Entity, trail: Trail) -> None:
    for child in (a, b):
        child.memes["curiosity"] += 1
        child.meters["darkness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {b.id} stopped short. {trail.marks_text} {trail.location_text}."
    )
    world.say(
        f'"Did you see that?" {b.id} whispered. "Those {trail.label} look almost alive."'
    )


def worry(world: World, a: Entity, b: Entity, place: Place, source: Source) -> None:
    world.say(
        f"The farther they looked, the quieter everything felt. {place.hush_text}"
    )
    guess = random.choice([
        f"maybe a cave creature had gone past",
        f"maybe something hidden was watching them",
        f"maybe the strange glow belonged to {source.creature}",
    ])
    world.say(
        f'{a.id} swallowed hard and wondered if {guess}.'
    )


def call_guide(world: World, guide: Entity, a: Entity, b: Entity) -> None:
    for child in (a, b):
        child.memes["trust"] += 1
    world.say(
        f"Just then, the guide came along the path and saw the children staring. "
        f'"Stay close," {guide.pronoun()} said. "We can solve this together."'
    )


def inspect(world: World, method: Method, guide: Entity, trail: Trail) -> None:
    world.say(method.suspense_text.format(
        guide=guide.label_word,
        trail=trail.label,
    ))


def solve(world: World, guide: Entity, source: Source, trail: Trail, method: Method, place: Place) -> None:
    if method.requires_uv:
        world.get("tool").meters["uv_on"] += 1
    propagate(world, narrate=False)
    world.say(method.solve_text.format(
        guide=guide.label_word,
        trail=trail.label,
        source=source.label,
    ))
    if world.get("trail").meters["bright_glow"] >= THRESHOLD:
        world.say(
            f"In the violet beam, the clue shone with bright fluorescence, and the pattern finally made sense."
        )
    world.say(
        source.reveal_text.format(place=place.label)
    )


def ending(world: World, a: Entity, b: Entity, place: Place, source: Source) -> None:
    for child in (a, b):
        child.memes["wonder"] += 1
        child.memes["fear"] = 0.0
    world.say(
        f"{a.id} laughed first, and then {b.id} laughed too. The scary mystery had turned into a true answer."
    )
    world.say(
        f"They followed the last glowing clues with steady feet, and {place.final_image}."
    )
    world.say(
        f"Now when they thought of the glow, they did not think of monsters. They thought of {source.label} and the clever way light can reveal a secret."
    )


def tell(
    place: Place,
    source: Source,
    trail: Trail,
    method: Method,
    child1_name: str = "Mira",
    child1_type: str = "girl",
    child2_name: str = "Finn",
    child2_type: str = "boy",
    guide_type: str = "ranger_woman",
) -> World:
    world = World()
    a = world.add(Entity(id=child1_name, kind="character", type=child1_type, role="child"))
    b = world.add(Entity(id=child2_name, kind="character", type=child2_type, role="child"))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, role="guide", label="the guide"))
    src = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source.label,
        phrase=source.phrase,
        tags=set(source.tags),
        attrs={"reveal_line": source.glow_text},
    ))
    tr = world.add(Entity(
        id="trail",
        kind="thing",
        type="trail",
        label=trail.label,
        phrase=trail.phrase,
        tags=set(trail.tags),
    ))
    world.add(Entity(id="tool", kind="thing", type="tool", label="violet lamp"))

    introduce(world, a, b, place)
    world.para()
    discover(world, a, b, trail)
    worry(world, a, b, place, source)
    world.para()
    call_guide(world, guide, a, b)
    inspect(world, method, guide, trail)
    solve(world, guide, source, trail, method, place)
    world.para()
    ending(world, a, b, place, source)

    world.facts.update(
        place=place,
        source_cfg=source,
        trail_cfg=trail,
        method=method,
        child1=a,
        child2=b,
        guide=guide,
        solved=src.meters["identified"] >= THRESHOLD,
        glow_seen=tr.meters["bright_glow"] >= THRESHOLD,
    )
    return world


PLACES = {
    "sea_cave": Place(
        id="sea_cave",
        label="the sea cave",
        opening="Salt wind slipped through the stone arch, and the tide muttered below.",
        path_text="Their lantern made a golden circle on the damp rocks while the cave mouth opened like the start of a treasure map.",
        hush_text="Even the dripping water seemed to pause between one tiny sound and the next.",
        final_image="the cave no longer felt like a mouth in the dark but like a room full of sea secrets",
        supports={"algae", "shell_dust"},
        trail_kinds={"footprints", "speckles"},
        guide_type="ranger_woman",
        tags={"cave", "ocean"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the old greenhouse",
        opening="Moonlight silvered the glass roof, and every leaf made a quiet shadow on the floor.",
        path_text="Warm plant-smell and the soft tick of hanging pots made the place feel secret and brave at the same time.",
        hush_text="The long rows of leaves rustled so softly that the children could hear their own breathing.",
        final_image="the glass walls glimmered, and the greenhouse felt more magical than spooky",
        supports={"pollen", "paint"},
        trail_kinds={"leaves", "handprints"},
        guide_type="ranger_man",
        tags={"plants", "glass"},
    ),
    "museum_hall": Place(
        id="museum_hall",
        label="the museum hall",
        opening="The dinosaur bones were only shadows now, and the long floor shone under the night lights.",
        path_text="Every display case looked like it was waiting for one more clue to wake it up.",
        hush_text="Somewhere far away, a clock clicked once, and the big hall seemed to hold its breath.",
        final_image="the museum looked friendly again, as if every case had been smiling all along",
        supports={"paint", "shell_dust"},
        trail_kinds={"handprints", "speckles"},
        guide_type="ranger_woman",
        tags={"museum", "night"},
    ),
}

SOURCES = {
    "algae": Source(
        id="algae",
        label="fluorescent algae",
        phrase="a smear of fluorescent algae",
        owner="tide pool",
        glow_text="The guide aimed the violet lamp low, and the damp marks flashed green all at once.",
        reveal_text="A tiny crab had brushed through {place} after climbing over a patch of fluorescent algae from the tide pools, leaving the glow behind.",
        creature="a small crab",
        supports={"sea_cave"},
        trail_kinds={"footprints", "speckles"},
        tags={"algae", "fluorescence", "ocean"},
    ),
    "pollen": Source(
        id="pollen",
        label="flower pollen",
        phrase="a dusting of flower pollen",
        owner="night flowers",
        glow_text="When the violet light touched the trail, the dust glimmered in a soft yellow-green shimmer.",
        reveal_text="A moth had bumped from bloom to bloom in {place}, and flower pollen had brushed onto everything in its path.",
        creature="a big moth",
        supports={"greenhouse"},
        trail_kinds={"leaves"},
        tags={"pollen", "fluorescence", "plants"},
    ),
    "paint": Source(
        id="paint",
        label="museum poster paint",
        phrase="a streak of poster paint",
        owner="children's table",
        glow_text="Under the lamp, the marks lit up in neat glowing edges that looked less wild and more careful.",
        reveal_text="Someone from the afternoon craft table had carried washable poster paint on a sleeve, and the paint in {place} fluoresced under the violet beam.",
        creature="a ghost",
        supports={"greenhouse", "museum_hall"},
        trail_kinds={"handprints"},
        tags={"paint", "fluorescence", "craft"},
    ),
    "shell_dust": Source(
        id="shell_dust",
        label="crushed shell dust",
        phrase="a chalky trail of shell dust",
        owner="shell basket",
        glow_text="The pale dust answered the lamp with a cool blue-white shine.",
        reveal_text="A dropped basket of shell dust had spilled in {place}, and a small rolling toy wheel had scattered it into a bright trail.",
        creature="something with wheels",
        supports={"sea_cave", "museum_hall"},
        trail_kinds={"speckles"},
        tags={"shell", "fluorescence", "dust"},
    ),
}

TRAILS = {
    "footprints": Trail(
        id="footprints",
        label="footprints",
        phrase="glowing footprints",
        marks_text="A row of tiny glowing footprints curved away into the dark",
        location_text="They were too small for a grown-up and too bright to ignore",
        leads_text="The footprints led to a wet crack in the rock",
        trail_kind="footprints",
        tags={"algae", "ocean"},
    ),
    "handprints": Trail(
        id="handprints",
        label="handprints",
        phrase="glowing handprints",
        marks_text="Three glowing handprints gleamed in a little row",
        location_text="They shone on the wall as if someone had pressed a secret there",
        leads_text="The handprints ended near a work table",
        trail_kind="handprints",
        tags={"paint", "craft"},
    ),
    "leaves": Trail(
        id="leaves",
        label="leaf-speckles",
        phrase="glowing specks on leaves",
        marks_text="Little glowing specks twinkled across the broad leaves",
        location_text="They made a trail from one flower bed to the next",
        leads_text="The bright specks led toward the night-blooming flowers",
        trail_kind="leaves",
        tags={"pollen", "plants"},
    ),
    "speckles": Trail(
        id="speckles",
        label="speckles",
        phrase="glowing speckles",
        marks_text="A spray of glowing speckles dotted the floor",
        location_text="The bright dust looked like a star map dropped near their shoes",
        leads_text="The speckles wandered toward a low corner",
        trail_kind="speckles",
        tags={"shell_dust", "ocean", "shell"},
    ),
}

METHODS = {
    "violet_lamp": Method(
        id="violet_lamp",
        label="violet lamp",
        sense=3,
        requires_uv=True,
        suspense_text='"First we look, not guess," the {guide} said, lifting a violet lamp and letting the children follow the beam toward the {trail}.',
        solve_text='The {guide} held the lamp steady over the {trail}, and the glowing pattern sharpened until they could see exactly what kind of {source} had made it.',
        fail_text="",
        qa_text="The guide used a violet lamp to reveal the real glowing pattern.",
        tags={"uv", "light"},
    ),
    "sample_card": Method(
        id="sample_card",
        label="sample card",
        sense=2,
        requires_uv=True,
        suspense_text='The {guide} set a little sample card beside the {trail} and whispered for the children to watch for matching colors in the violet light.',
        solve_text='By comparing the {trail} with the sample card under the lamp, the {guide} matched the glow to the right {source}.',
        fail_text="",
        qa_text="The guide compared the glow under violet light with a sample card.",
        tags={"uv", "compare"},
    ),
    "wait_and_watch": Method(
        id="wait_and_watch",
        label="wait and watch",
        sense=2,
        requires_uv=True,
        suspense_text='The {guide} dimmed the lantern, then raised the violet lamp and waited quietly beside the {trail} until the hidden pattern showed itself.',
        solve_text='Waiting calmly in the right light, the {guide} saw the glow clearly and traced it back to the true {source}.',
        fail_text="",
        qa_text="The guide waited quietly and used the right light until the clue showed itself.",
        tags={"uv", "patience"},
    ),
    "shout_for_monster": Method(
        id="shout_for_monster",
        label="shout into the dark",
        sense=0,
        requires_uv=False,
        suspense_text="",
        solve_text="",
        fail_text="The children only frightened themselves more and learned nothing useful.",
        qa_text="",
        tags={"bad_choice"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tess", "Ava", "Nora", "June", "Ruby", "Ivy"]
BOY_NAMES = ["Finn", "Leo", "Max", "Theo", "Ben", "Eli", "Noah", "Owen"]


@dataclass
class StoryParams:
    place: str
    source: str
    trail: str
    method: str
    child1_name: str
    child1_type: str
    child2_name: str
    child2_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "fluorescence": [
        (
            "What is fluorescence?",
            "Fluorescence is when something takes in one kind of light and gives back a bright glow. Some things look plain at first, but under the right light they shine."
        )
    ],
    "uv": [
        (
            "What does a violet or UV lamp do?",
            "It shines a special kind of light that can make some hidden marks glow. That helps people notice clues they could not see well before."
        )
    ],
    "algae": [
        (
            "What is algae?",
            "Algae are simple living things that grow in water or on wet rocks. Some kinds can glow or look bright under special light."
        )
    ],
    "pollen": [
        (
            "What is pollen?",
            "Pollen is tiny dust made by flowers. It can stick to insects, petals, and leaves as the insects move from flower to flower."
        )
    ],
    "paint": [
        (
            "Why can poster paint glow under special light?",
            "Some paints have bright ingredients that react to special light. Under that light, the paint can look much brighter than it did before."
        )
    ],
    "shell": [
        (
            "What is shell dust?",
            "Shell dust is made from tiny crushed bits of shells. Pale shell dust can reflect or glow brightly under certain light."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery safely?",
            "You stay calm, look closely, and gather clues instead of making wild guesses. A real answer usually comes from patient noticing."
        )
    ],
}

KNOWLEDGE_ORDER = ["fluorescence", "uv", "algae", "pollen", "paint", "shell", "mystery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    source = f["source_cfg"]
    trail = f["trail_cfg"]
    child1 = f["child1"]
    child2 = f["child2"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the word "fluorescence" and centers on a glowing mystery.',
        f"Tell a suspenseful but gentle adventure where {child1.id} and {child2.id} find {trail.phrase} in {place.label} and solve the mystery safely.",
        f"Write a mystery-to-solve story where children first fear something strange, then learn that the glow came from {source.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    guide = f["guide"]
    place = f["place"]
    source = f["source_cfg"]
    trail = f["trail_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children on an adventure, and a guide who helps them solve a mystery."
        ),
        (
            "What mystery did they find?",
            f"They found {trail.phrase} in {place.label}. At first the glowing trail felt spooky because they did not know what had made it."
        ),
        (
            "Why did the children feel nervous?",
            f"The place was dark and quiet, and the clues looked strange in the half-light. Without an answer yet, their imaginations made the mystery feel bigger."
        ),
        (
            "How did the guide help them solve the mystery?",
            f"{guide.label_word.capitalize()} stayed calm and used {method.label}. {method.qa_text} That gave the children a real clue instead of a scary guess."
        ),
        (
            "What was really making the glow?",
            f"The glow came from {source.label}. The mystery changed once the children understood that the bright marks had a real cause."
        ),
        (
            "What did they learn at the end?",
            "They learned that careful looking can turn a scary mystery into a true answer. The ending shows them feeling wonder instead of fear."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fluorescence", "mystery"}
    tags |= set(world.facts["source_cfg"].tags)
    tags |= set(world.facts["method"].tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="sea_cave",
        source="algae",
        trail="footprints",
        method="violet_lamp",
        child1_name="Mira",
        child1_type="girl",
        child2_name="Finn",
        child2_type="boy",
    ),
    StoryParams(
        place="greenhouse",
        source="pollen",
        trail="leaves",
        method="wait_and_watch",
        child1_name="Ruby",
        child1_type="girl",
        child2_name="Leo",
        child2_type="boy",
    ),
    StoryParams(
        place="museum_hall",
        source="paint",
        trail="handprints",
        method="sample_card",
        child1_name="Nora",
        child1_type="girl",
        child2_name="Max",
        child2_type="boy",
    ),
    StoryParams(
        place="sea_cave",
        source="shell_dust",
        trail="speckles",
        method="violet_lamp",
        child1_name="Ivy",
        child1_type="girl",
        child2_name="Theo",
        child2_type="boy",
    ),
]


ASP_RULES = r"""
trail_fits(P,T) :- place(P), trail(T), trail_kind(T,K), place_trail(P,K).
source_fits(P,S,T) :- place(P), source(S), trail(T),
                      supports(P,S), source_tag(S,Tag), trail_tag(T,Tag),
                      trail_kind(T,K), source_trail(S,K).
valid(P,S,T) :- trail_fits(P,T), source_fits(P,S,T).

sensible(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.
solves(M) :- sensible(M), requires_uv(M).
solves(M) :- sensible(M), not requires_uv(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for sid in sorted(place.supports):
            lines.append(asp.fact("supports", place_id, sid))
        for tk in sorted(place.trail_kinds):
            lines.append(asp.fact("place_trail", place_id, tk))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for tk in sorted(source.trail_kinds):
            lines.append(asp.fact("source_trail", source_id, tk))
        for tag in sorted(source.tags):
            lines.append(asp.fact("source_tag", source_id, tag))
    for trail_id, trail in TRAILS.items():
        lines.append(asp.fact("trail", trail_id))
        lines.append(asp.fact("trail_kind", trail_id, trail.trail_kind))
        for tag in sorted(trail.tags):
            lines.append(asp.fact("trail_tag", trail_id, tag))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.requires_uv:
            lines.append(asp.fact("requires_uv", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


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

    clingo_methods = set(asp_sensible_methods())
    python_methods = {mid for mid, method in METHODS.items() if method_sensible(method)}
    if clingo_methods == python_methods:
        print(f"OK: sensible methods match ({sorted(clingo_methods)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  clingo:", sorted(clingo_methods))
        print("  python:", sorted(python_methods))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test story generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a glowing mystery solved by careful adventure."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--trail", choices=TRAILS)
    ap.add_argument("--method", choices=METHODS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [x for x in pool if x != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and not method_sensible(METHODS[args.method]):
        raise StoryError(explain_method_rejection(args.method))

    if args.place and args.source and args.trail:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        trail = TRAILS[args.trail]
        if not (trail_fits(place, trail) and source_fits(place, source, trail)):
            raise StoryError(explain_combo_rejection(place, source, trail))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.trail is None or combo[2] == args.trail)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, trail_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(mid for mid, method in METHODS.items() if method_sensible(method)))
    g1 = rng.choice(["girl", "boy"])
    g2 = rng.choice(["girl", "boy"])
    n1 = _pick_name(rng, g1)
    n2 = _pick_name(rng, g2, avoid=n1)
    return StoryParams(
        place=place_id,
        source=source_id,
        trail=trail_id,
        method=method_id,
        child1_name=n1,
        child1_type=g1,
        child2_name=n2,
        child2_type=g2,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.trail not in TRAILS:
        raise StoryError(f"(Unknown trail: {params.trail})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    place = PLACES[params.place]
    source = SOURCES[params.source]
    trail = TRAILS[params.trail]
    method = METHODS[params.method]

    if not (trail_fits(place, trail) and source_fits(place, source, trail)):
        raise StoryError(explain_combo_rejection(place, source, trail))
    if not method_sensible(method):
        raise StoryError(explain_method_rejection(params.method))

    world = tell(
        place=place,
        source=source,
        trail=trail,
        method=method,
        child1_name=params.child1_name,
        child1_type=params.child1_type,
        child2_name=params.child2_name,
        child2_type=params.child2_type,
        guide_type=place.guide_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, trail) combos:\n")
        for place, source, trail in combos:
            print(f"  {place:12} {source:10} {trail}")
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
            header = f"### {p.place}: {p.source} with {p.trail} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
