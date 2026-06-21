#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/carbohydrate_artificial_curiosity_whodunit.py
=======================================================================

A tiny whodunit-style storyworld about a curious child solving the mystery of a
missing edible display piece.

The world always includes the words "carbohydrate" and "artificial" in natural
story prose: the missing object is an edible display described by a grown-up as
a carbohydrate sculpture, and it is decorated with some artificial pieces meant
only for looking.

Run it
------
    python storyworlds/worlds/gpt-5.4/carbohydrate_artificial_curiosity_whodunit.py
    python storyworlds/worlds/gpt-5.4/carbohydrate_artificial_curiosity_whodunit.py --place classroom --culprit pigeon
    python storyworlds/worlds/gpt-5.4/carbohydrate_artificial_curiosity_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/carbohydrate_artificial_curiosity_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/carbohydrate_artificial_curiosity_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/carbohydrate_artificial_curiosity_whodunit.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so three parents up is
# the package dir storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | animal | machine | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "teacher", "baker"}
        male = {"boy", "man", "father"}
        neuter = {"robot", "machine"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neuter:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    open_window: bool = False
    has_robot: bool = False
    hosts_sibling: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Display:
    id: str
    label: str
    phrase: str
    shape: str
    scent: str
    topping: str
    edible: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CulpritCfg:
    id: str
    kind: str
    type: str
    label: str
    motive: str
    clue: str
    evidence: str
    trail: str
    hiding_place: str
    recovery: str
    ending_image: str
    needs_open_window: bool = False
    needs_robot: bool = False
    needs_sibling: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_missing_causes_alarm(world: World) -> list[str]:
    display = world.get("display")
    detective = world.get("detective")
    host = world.get("host")
    if display.meters["missing"] < THRESHOLD:
        return []
    sig = ("alarm", "display")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["curiosity"] += 1
    detective.memes["concern"] += 1
    host.memes["worry"] += 1
    return []


def _r_clue_points_to_suspect(world: World) -> list[str]:
    clue = world.get("clue")
    culprit = world.get("culprit")
    detective = world.get("detective")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("suspect", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.meters["certainty"] += 1
    culprit.meters["suspected"] += 1
    return []


def _r_confession_brings_relief(world: World) -> list[str]:
    culprit = world.get("culprit")
    detective = world.get("detective")
    host = world.get("host")
    display = world.get("display")
    if culprit.meters["found"] < THRESHOLD or display.meters["returned"] < THRESHOLD:
        return []
    sig = ("relief", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["relief"] += 1
    host.memes["relief"] += 1
    culprit.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_alarm", tag="social", apply=_r_missing_causes_alarm),
    Rule(name="clue_points", tag="epistemic", apply=_r_clue_points_to_suspect),
    Rule(name="relief", tag="social", apply=_r_confession_brings_relief),
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
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "classroom": Place(
        id="classroom",
        label="classroom",
        phrase="the bright classroom",
        open_window=False,
        has_robot=False,
        hosts_sibling=True,
        tags={"school"},
    ),
    "bakery": Place(
        id="bakery",
        label="bakery",
        phrase="the little bakery by the square",
        open_window=True,
        has_robot=False,
        hosts_sibling=False,
        tags={"bakery"},
    ),
    "library": Place(
        id="library",
        label="library",
        phrase="the children's corner of the library",
        open_window=False,
        has_robot=True,
        hosts_sibling=False,
        tags={"library"},
    ),
    "hall": Place(
        id="hall",
        label="community hall",
        phrase="the warm community hall",
        open_window=True,
        has_robot=True,
        hosts_sibling=True,
        tags={"community"},
    ),
}

DISPLAYS = {
    "cracker_castle": Display(
        id="cracker_castle",
        label="cracker castle",
        phrase="a cracker castle with walls of crisp squares",
        shape="castle",
        scent="butter and salt",
        topping="tiny artificial berries that shone like red buttons",
        tags={"cracker", "food_display"},
    ),
    "bread_moon": Display(
        id="bread_moon",
        label="bread moon",
        phrase="a bread moon cut from soft round slices",
        shape="moon",
        scent="warm toast",
        topping="a ring of artificial silver stars taped to the tray",
        tags={"bread", "food_display"},
    ),
    "noodle_nest": Display(
        id="noodle_nest",
        label="noodle nest",
        phrase="a noodle nest curled into a neat golden bowl",
        shape="nest",
        scent="sesame and soup",
        topping="a few artificial flowers tucked around the plate",
        tags={"noodles", "food_display"},
    ),
}

CULPRITS = {
    "sibling": CulpritCfg(
        id="sibling",
        kind="character",
        type="boy",
        label="the little brother",
        motive="thought the display was an extra snack",
        clue="a sticky thumbprint",
        evidence="sticky crumbs on a sleeve",
        trail="a dotted line of crumbs leading toward the coat hooks",
        hiding_place="behind the coat rack",
        recovery="holding the missing piece with wide, sorry eyes",
        ending_image="The mystery ended with shared bites at a small table instead of whispers in the room.",
        needs_sibling=True,
        tags={"family", "crumbs"},
    ),
    "pigeon": CulpritCfg(
        id="pigeon",
        kind="animal",
        type="animal",
        label="a bold pigeon",
        motive="snatched the crunchy shape through the open window",
        clue="a gray feather",
        evidence="one neat peck mark and a feather on the sill",
        trail="a flutter of feathers and crumbs along the window ledge",
        hiding_place="on the outside sill, puffed up like a feathery thief",
        recovery="guarding the missing piece under one foot",
        ending_image="The pigeon flapped off with only a tiny crust, while the rest of the display came safely back inside.",
        needs_open_window=True,
        tags={"bird", "window"},
    ),
    "robot": CulpritCfg(
        id="robot",
        kind="machine",
        type="robot",
        label="the cleaning robot",
        motive="mistook the fallen piece for litter",
        clue="two thin wheel lines",
        evidence="two wheel tracks beside a swept-clean patch",
        trail="a careful little path of wheel marks toward the charging nook",
        hiding_place="beside its charger, humming with the missing piece in its bin",
        recovery="whirring softly with the piece tucked safely inside",
        ending_image="Soon the tray was whole again, and the robot blinked its green light as if it had solved part of the puzzle too.",
        needs_robot=True,
        tags={"robot", "machine"},
    ),
}


def culprit_accessible(place: Place, culprit: CulpritCfg) -> bool:
    if culprit.needs_open_window and not place.open_window:
        return False
    if culprit.needs_robot and not place.has_robot:
        return False
    if culprit.needs_sibling and not place.hosts_sibling:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for display_id, display in DISPLAYS.items():
            for culprit_id, culprit in CULPRITS.items():
                if display.edible and culprit_accessible(place, culprit):
                    combos.append((place_id, display_id, culprit_id))
    return combos


@dataclass
class StoryParams:
    place: str
    display: str
    culprit: str
    detective_name: str
    detective_gender: str
    companion_name: str
    companion_gender: str
    host_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="classroom",
        display="cracker_castle",
        culprit="sibling",
        detective_name="Ada",
        detective_gender="girl",
        companion_name="Ben",
        companion_gender="boy",
        host_type="teacher",
    ),
    StoryParams(
        place="bakery",
        display="bread_moon",
        culprit="pigeon",
        detective_name="Leo",
        detective_gender="boy",
        companion_name="Mia",
        companion_gender="girl",
        host_type="baker",
    ),
    StoryParams(
        place="library",
        display="noodle_nest",
        culprit="robot",
        detective_name="Nora",
        detective_gender="girl",
        companion_name="Sam",
        companion_gender="boy",
        host_type="teacher",
    ),
    StoryParams(
        place="hall",
        display="bread_moon",
        culprit="robot",
        detective_name="Theo",
        detective_gender="boy",
        companion_name="Lily",
        companion_gender="girl",
        host_type="mother",
    ),
    StoryParams(
        place="hall",
        display="cracker_castle",
        culprit="pigeon",
        detective_name="Maya",
        detective_gender="girl",
        companion_name="Finn",
        companion_gender="boy",
        host_type="father",
    ),
]

GIRL_NAMES = ["Ada", "Lily", "Mia", "Nora", "Zoe", "Ella", "Maya", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Theo", "Finn", "Jack", "Noah", "Eli"]


def explain_rejection(place: Place, culprit: CulpritCfg) -> str:
    if culprit.needs_open_window and not place.open_window:
        return (
            f"(No story: {culprit.label} only works where an open window or open stall gives "
            f"it access, but {place.phrase} does not.)"
        )
    if culprit.needs_robot and not place.has_robot:
        return (
            f"(No story: {culprit.label} only works in a place that actually has a cleaning robot, "
            f"but {place.phrase} does not.)"
        )
    if culprit.needs_sibling and not place.hosts_sibling:
        return (
            f"(No story: {culprit.label} needs a family-style event where a younger sibling is present, "
            f"but {place.phrase} does not fit that setup.)"
        )
    return "(No story: that culprit cannot reasonably take the missing display here.)"


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def host_word(host: Entity) -> str:
    return {"teacher": "teacher", "baker": "baker", "mother": "mom", "father": "dad"}.get(
        host.type, host.type
    )


def setup_story(world: World, detective: Entity, companion: Entity, host: Entity, display: Entity, display_cfg: Display) -> None:
    detective.memes["curiosity"] += 1
    companion.memes["interest"] += 1
    world.say(
        f"On the morning of the little display contest in {world.place.phrase}, "
        f"{detective.id} walked in beside {companion.id} and stopped at the snack table."
    )
    world.say(
        f"In the middle stood {display_cfg.phrase}. {host.label_word.capitalize()} smiled and said "
        f"it was a carbohydrate sculpture for the children to admire before snack time."
    )
    world.say(
        f"It smelled of {display_cfg.scent}, and around it were {display_cfg.topping}. "
        f"{detective.id} loved mysteries almost as much as lunch, so {detective.pronoun()} leaned close to study every detail."
    )


def disappearance(world: World, detective: Entity, host: Entity, display: Entity) -> None:
    display.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when everyone turned to hang coats and set down bags, a gasp rose from the table. "
        f"The {display.label} was gone."
    )
    world.say(
        f'"Oh dear," said the {host_word(host)}. "{display.label.capitalize()} was here a moment ago."'
    )
    if detective.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"{detective.id}'s eyes widened. Instead of stepping back, {detective.pronoun()} stepped closer. "
            f"A mystery had just opened like a little door."
        )


def inspect_clue(world: World, detective: Entity, culprit_cfg: CulpritCfg) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} knelt by the tray and found {culprit_cfg.clue}. "
        f"There was also {culprit_cfg.evidence}."
    )
    world.say(
        f'"That is not a random mess," {detective.pronoun()} whispered. '
        f'"It is a clue."'
    )


def follow_trail(world: World, detective: Entity, companion: Entity, culprit_cfg: CulpritCfg) -> None:
    detective.meters["searching"] += 1
    companion.memes["trust"] += 1
    world.say(
        f"Very carefully, {detective.id} and {companion.id} followed {culprit_cfg.trail}. "
        f"The farther they went, the more certain {detective.id} felt."
    )


def reveal(world: World, detective: Entity, culprit: Entity, culprit_cfg: CulpritCfg, display: Entity) -> None:
    culprit.meters["found"] += 1
    display.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"And there, in {culprit_cfg.hiding_place}, was {culprit_cfg.recovery}."
    )
    if culprit_cfg.id == "sibling":
        world.say(
            f'"I thought nobody wanted it yet," {culprit.label} mumbled. '
            f'{detective.id} saw at once that {culprit.pronoun()} looked more embarrassed than sneaky.'
        )
    elif culprit_cfg.id == "pigeon":
        world.say(
            f"The bird tilted its head at them as if it had no idea a detective was on the case. "
            f"{detective.id} coaxed it away with a few safe crumbs from another tray."
        )
    else:
        world.say(
            f'"Beep: cleaning complete," said the robot. Then it opened its bin, neat as a drawer. '
            f'{detective.id} laughed softly. "So you were helping in your own way."'
        )


def resolution(world: World, detective: Entity, companion: Entity, host: Entity, culprit: Entity, culprit_cfg: CulpritCfg, display: Entity) -> None:
    detective.memes["kindness"] += 1
    host.memes["pride"] += 1
    world.say(
        f"The {host_word(host)} took back the {display.label} and thanked {detective.id} for noticing what everyone else had missed."
    )
    if culprit_cfg.id == "sibling":
        world.say(
            f"Instead of scolding, the grown-up broke off a fresh piece for the little brother and explained that the display came first and sharing came after. "
            f"{companion.id} grinned when the room grew cheerful again."
        )
    elif culprit_cfg.id == "pigeon":
        world.say(
            f"The children moved the tray farther from the window and laughed with relief. "
            f"{companion.id} said it had been the boldest thief in town, and nobody disagreed."
        )
    else:
        world.say(
            f"The grown-up emptied the robot's bin, patted its lid, and moved the tray up to a higher shelf. "
            f"{companion.id} said a good detective must understand helpers as well as troublemakers."
        )
    world.say(culprit_cfg.ending_image)


def tell(
    place: Place,
    display_cfg: Display,
    culprit_cfg: CulpritCfg,
    detective_name: str,
    detective_gender: str,
    companion_name: str,
    companion_gender: str,
    host_type: str,
) -> World:
    if not culprit_accessible(place, culprit_cfg):
        raise StoryError(explain_rejection(place, culprit_cfg))

    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    host = world.add(Entity(id="Host", kind="character", type=host_type, role="host", label=host_type))
    display = world.add(
        Entity(
            id="display",
            kind="thing",
            type="food_display",
            role="display",
            label=display_cfg.label,
            phrase=display_cfg.phrase,
            tags=set(display_cfg.tags),
        )
    )
    culprit = world.add(
        Entity(
            id="culprit",
            kind=culprit_cfg.kind,
            type=culprit_cfg.type,
            role="culprit",
            label=culprit_cfg.label,
            attrs={"motive": culprit_cfg.motive},
            tags=set(culprit_cfg.tags),
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            kind="thing",
            type="clue",
            role="clue",
            label=culprit_cfg.clue,
        )
    )

    setup_story(world, detective, companion, host, display, display_cfg)
    world.para()
    disappearance(world, detective, host, display)
    inspect_clue(world, detective, culprit_cfg)
    world.para()
    follow_trail(world, detective, companion, culprit_cfg)
    reveal(world, detective, culprit, culprit_cfg, display)
    world.para()
    resolution(world, detective, companion, host, culprit, culprit_cfg, display)

    world.facts.update(
        place=place,
        display_cfg=display_cfg,
        culprit_cfg=culprit_cfg,
        detective=detective,
        companion=companion,
        host=host,
        display=display,
        culprit=culprit,
        clue=clue,
        solved=culprit.meters["found"] >= THRESHOLD,
        returned=display.meters["returned"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "carbohydrate": [
        (
            "What is a carbohydrate?",
            "A carbohydrate is a kind of food that gives your body energy. Bread, crackers, rice, and noodles all have carbohydrates in them.",
        )
    ],
    "artificial": [
        (
            "What does artificial mean?",
            "Artificial means something is made to look like the real thing, but it is not the real thing. Artificial berries or flowers can decorate a table without being food.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Detectives look for clues because tiny details can tell a big story.",
        )
    ],
    "pigeon": [
        (
            "Why do pigeons peck at food?",
            "Pigeons look for crumbs and small bites to eat. If food is left near an open window, a bird may try to snatch some.",
        )
    ],
    "robot": [
        (
            "What does a cleaning robot do?",
            "A cleaning robot rolls around picking up dust and small bits from the floor. Sometimes it can mistake something important for trash if it is in the wrong place.",
        )
    ],
    "sharing": [
        (
            "Why is it good to ask before taking food?",
            "Asking first shows respect for other people and their plans. It also helps everyone know when it is time to share.",
        )
    ],
}
KNOWLEDGE_ORDER = ["carbohydrate", "artificial", "clue", "pigeon", "robot", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    culprit_cfg = f["culprit_cfg"]
    display_cfg = f["display_cfg"]
    place = f["place"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old about a curious child who solves the mystery of a missing {display_cfg.label}. Include the words "carbohydrate" and "artificial".',
        f"Tell a small detective story set in {place.phrase} where {detective.id} follows clues to find out who took the {display_cfg.label}.",
        f"Write a child-facing mystery where curiosity leads to kindness, and the culprit turns out to be {culprit_cfg.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    companion = f["companion"]
    host = f["host"]
    display_cfg = f["display_cfg"]
    culprit_cfg = f["culprit_cfg"]
    culprit = f["culprit"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a curious child who notices small details, and {companion.id}, who follows along while the mystery is solved.",
        ),
        (
            f"What was missing?",
            f"The missing thing was the {display_cfg.label}, an edible display the grown-up had called a carbohydrate sculpture. It was supposed to stay on the table until snack time.",
        ),
        (
            f"Why did {detective.id} start investigating?",
            f"{detective.id} saw that the {display_cfg.label} had vanished and noticed a strange clue beside the tray. Curiosity pushed {detective.pronoun('object')} closer instead of farther away.",
        ),
        (
            "What clue helped solve the mystery?",
            f"The big clue was {culprit_cfg.clue}, along with {culprit_cfg.evidence}. Those details matched the real culprit and pointed the search in the right direction.",
        ),
        (
            f"Who took the {display_cfg.label}?",
            f"{culprit.label.capitalize()} took it. {culprit_cfg.motive.capitalize()}, so the mystery was solved by understanding the clue and the reason.",
        ),
    ]
    if f["returned"]:
        qa.append(
            (
                "How did the story end?",
                f"The {display_cfg.label} was brought back, and the room felt calm again. The ending shows that solving a mystery can lead to kindness instead of anger.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"carbohydrate", "artificial", "clue", "sharing"}
    culprit_id = f["culprit_cfg"].id
    if culprit_id == "pigeon":
        tags.add("pigeon")
    if culprit_id == "robot":
        tags.add("robot")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- accessibility gate ----------------------------------------------------
accessible(P, C) :- place(P), culprit(C), needs_open_window(C), open_window(P).
accessible(P, C) :- place(P), culprit(C), needs_robot(C), has_robot(P).
accessible(P, C) :- place(P), culprit(C), needs_sibling(C), hosts_sibling(P).
accessible(P, C) :- place(P), culprit(C),
                    not needs_open_window(C),
                    not needs_robot(C),
                    not needs_sibling(C).

valid(P, D, C) :- place(P), display(D), culprit(C), edible(D), accessible(P, C).

% --- deterministic clue mapping -------------------------------------------
points_to(C, Cl) :- culprit_clue(C, Cl).

% --- story success ---------------------------------------------------------
solved(P, D, C) :- valid(P, D, C), points_to(C, _).
returned(P, D, C) :- solved(P, D, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.open_window:
            lines.append(asp.fact("open_window", place_id))
        if place.has_robot:
            lines.append(asp.fact("has_robot", place_id))
        if place.hosts_sibling:
            lines.append(asp.fact("hosts_sibling", place_id))
    for display_id, display in DISPLAYS.items():
        lines.append(asp.fact("display", display_id))
        if display.edible:
            lines.append(asp.fact("edible", display_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("culprit_clue", culprit_id, culprit.clue.replace(" ", "_")))
        if culprit.needs_open_window:
            lines.append(asp.fact("needs_open_window", culprit_id))
        if culprit.needs_robot:
            lines.append(asp.fact("needs_robot", culprit_id))
        if culprit.needs_sibling:
            lines.append(asp.fact("needs_sibling", culprit_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_points_to(culprit_id: str) -> str:
    import asp

    extra = f"chosen({culprit_id}). points_to_chosen(Cl) :- chosen(C), points_to(C, Cl)."
    model = asp.one_model(asp_program(extra, "#show points_to_chosen/1."))
    atoms = asp.atoms(model, "points_to_chosen")
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

    for culprit_id, culprit in CULPRITS.items():
        got = asp_points_to(culprit_id)
        expected = culprit.clue.replace(" ", "_")
        if got != expected:
            rc = 1
            print(f"MISMATCH in clue mapping for {culprit_id}: clingo={got} python={expected}")

    smoke_cases = list(CURATED[:2])
    try:
        smoke_cases.append(
            resolve_params(
                build_parser().parse_args([]),
                random.Random(123),
            )
        )
    except StoryError as err:
        rc = 1
        print(f"SMOKE setup failed during resolve_params: {err}")
        smoke_cases = smoke_cases[:2]

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header=f"### smoke {idx}")
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"SMOKE generation failed on case {idx}: {err}")

    if rc == 0:
        print("OK: smoke generation passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny whodunit storyworld about a curious child solving the mystery of a missing snack display."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--display", choices=DISPLAYS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--host", choices=["teacher", "baker", "mother", "father"])
    ap.add_argument("--detective-name")
    ap.add_argument("--companion-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.culprit:
        place = PLACES[args.place]
        culprit = CULPRITS[args.culprit]
        if not culprit_accessible(place, culprit):
            raise StoryError(explain_rejection(place, culprit))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.display is None or c[1] == args.display)
        and (args.culprit is None or c[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, display_id, culprit_id = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or pick_name(rng, detective_gender)
    companion_name = args.companion_name or pick_name(rng, companion_gender, avoid=detective_name)
    host_type = args.host or rng.choice(["teacher", "baker", "mother", "father"])

    if place_id == "bakery" and host_type not in {"baker", "mother", "father", "teacher"}:
        raise StoryError("(No story: invalid host choice.)")

    return StoryParams(
        place=place_id,
        display=display_id,
        culprit=culprit_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
        host_type=host_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.display not in DISPLAYS:
        raise StoryError(f"(Unknown display: {params.display})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")

    world = tell(
        place=PLACES[params.place],
        display_cfg=DISPLAYS[params.display],
        culprit_cfg=CULPRITS[params.culprit],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        companion_name=params.companion_name,
        companion_gender=params.companion_gender,
        host_type=params.host_type,
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
        print(asp_program("", "#show valid/3.\n#show points_to/2.\n#show solved/3.\n#show returned/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, display, culprit) combos:\n")
        for place, display, culprit in combos:
            print(f"  {place:10} {display:15} {culprit}")
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
            header = f"### {p.detective_name}: {p.display} in {p.place} ({p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
