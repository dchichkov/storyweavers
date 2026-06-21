#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/continue_marinara_pollen_mystery_to_solve_dialogue.py
==============================================================================

A standalone storyworld about a funny little mystery: two children are making a
pretend restaurant sign when odd red-and-yellow blotches appear on it. One child
briefly blames the other. Through dialogue, they investigate, discover a small
marinara drip plus sticky pollen, laugh at the mix-up, clean the sign, and
reconcile so they can continue their game.

The world prefers a narrow set of plausible combinations:
- the place must plausibly contain the chosen marinara source,
- the place must plausibly contain the chosen pollen source,
- the project must be a surface that can actually show sauce and pollen marks.

The story shape is always:
premise -> odd clue appears -> funny accusation / hurt feeling ->
investigation through dialogue -> true cause discovered -> apology and repair ->
an ending image showing the play can continue.
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
# This file lives in storyworlds/worlds/gpt-5.4/, so the package dir is three
# levels up.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Core entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    show_marks: bool = False
    sticky: bool = False
    edible: bool = False
    powdery: bool = False
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


# ---------------------------------------------------------------------------
# Domain config.
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    scene: str
    food_sources: set[str] = field(default_factory=set)
    pollen_sources: set[str] = field(default_factory=set)
    draft: str = ""
    flower_phrase: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SauceSource:
    id: str
    label: str
    phrase: str
    spill_line: str
    trail: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class PollenSource:
    id: str
    label: str
    phrase: str
    drift_line: str
    sneeze_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    role_word: str
    show_marks: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Cleaner:
    id: str
    label: str
    phrase: str
    action: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World state and narration.
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"maker", "friend"}]

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
# Rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mystery_visible(world: World) -> list[str]:
    project = world.get("project")
    if project.meters["sauce_mark"] < THRESHOLD or project.meters["pollen_mark"] < THRESHOLD:
        return []
    sig = ("mystery_visible", project.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    project.meters["mystery"] += 1
    for kid in world.kids():
        kid.memes["curiosity"] += 1
    return ["__mystery__"]


def _r_hurt_feelings(world: World) -> list[str]:
    maker = world.get("maker")
    friend = world.get("friend")
    if maker.memes["blame"] < THRESHOLD:
        return []
    sig = ("hurt_feelings", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    maker.memes["worry"] += 1
    return ["__hurt__"]


def _r_solved(world: World) -> list[str]:
    maker = world.get("maker")
    friend = world.get("friend")
    project = world.get("project")
    if maker.memes["investigating"] < THRESHOLD or friend.memes["investigating"] < THRESHOLD:
        return []
    if project.meters["sauce_mark"] < THRESHOLD or project.meters["pollen_mark"] < THRESHOLD:
        return []
    sig = ("solved", project.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    project.meters["solved"] += 1
    maker.memes["relief"] += 1
    friend.memes["relief"] += 1
    maker.memes["trust"] += 1
    friend.memes["trust"] += 1
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="mystery_visible", tag="physical", apply=_r_mystery_visible),
    Rule(name="hurt_feelings", tag="social", apply=_r_hurt_feelings),
    Rule(name="solved", tag="social", apply=_r_solved),
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
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def place_allows(place: Place, sauce: SauceSource, pollen: PollenSource) -> bool:
    return sauce.id in place.food_sources and pollen.id in place.pollen_sources


def project_works(project: Project) -> bool:
    return project.show_marks


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for sauce_id, sauce in SAUCES.items():
            for pollen_id, pollen in POLLENS.items():
                for project_id, project in PROJECTS.items():
                    if place_allows(place, sauce, pollen) and project_works(project):
                        combos.append((place_id, sauce_id, pollen_id, project_id))
    return combos


def explain_rejection(place: Place, sauce: SauceSource, pollen: PollenSource, project: Project) -> str:
    if sauce.id not in place.food_sources:
        return (
            f"(No story: {place.label} does not plausibly contain {sauce.phrase}, "
            f"so there is no honest marinara clue to investigate there.)"
        )
    if pollen.id not in place.pollen_sources:
        return (
            f"(No story: {place.label} does not plausibly have {pollen.label}, "
            f"so the yellow clue would have no source.)"
        )
    if not project.show_marks:
        return (
            f"(No story: {project.phrase} would not show sticky red marinara and "
            f"pollen clearly enough for a child-sized mystery to solve.)"
        )
    return "(No story: this combination does not make a visible mystery.)"


def outcome_of(params: "StoryParams") -> str:
    return "apology_reconcile" if params.talk_style == "blurt_first" else "quick_reconcile"


# ---------------------------------------------------------------------------
# Simulation helpers.
# ---------------------------------------------------------------------------
def predict_mystery(world: World) -> dict:
    sim = world.copy()
    sim.get("project").meters["sauce_mark"] += 1
    sim.get("project").meters["pollen_mark"] += 1
    propagate(sim, narrate=False)
    project = sim.get("project")
    return {
        "mystery": project.meters["mystery"] >= THRESHOLD,
        "funny": project.meters["sauce_mark"] >= THRESHOLD and project.meters["pollen_mark"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs.
# ---------------------------------------------------------------------------
def setup(world: World, maker: Entity, friend: Entity, place: Place, project: Project) -> None:
    maker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon in {place.label}, {maker.id} and {friend.id} decided to open "
        f"a pretend noodle restaurant. {place.scene}"
    )
    world.say(
        f"They spread out {project.phrase} and worked very hard on their grand {project.role_word}."
    )
    world.say(
        f'"Our restaurant needs the fanciest sign in the world," {maker.id} said.'
    )
    world.say(
        f'"And maybe a bell that goes ding-ding every time someone orders extra spaghetti," '
        f"{friend.id} said."
    )


def lunch_nearby(world: World, maker: Entity, sauce: SauceSource) -> None:
    world.say(
        f"Nearby sat {sauce.phrase}, because lunch had not been cleaned up yet."
    )
    world.say(
        f'{maker.id} sniffed the air. "Mmm. Marinara," {maker.pronoun()} said, trying to sound like a serious chef.'
    )


def mystery_appears(world: World, place: Place, sauce: SauceSource, pollen: PollenSource, project: Project) -> None:
    proj = world.get("project")
    proj.meters["sauce_mark"] += 1
    proj.meters["sticky"] += 1
    world.say(sauce.spill_line)
    proj.meters["pollen_mark"] += 1
    world.say(pollen.drift_line.format(draft=place.draft))
    propagate(world, narrate=False)
    world.say(
        f"When the children looked back, their {project.label} wore a strange red blob sprinkled with yellow dust."
    )


def accuse_or_ask(world: World, maker: Entity, friend: Entity, talk_style: str, project: Project) -> None:
    if talk_style == "blurt_first":
        maker.memes["blame"] += 1
        propagate(world, narrate=False)
        world.say(
            f'"{friend.id}, did you boop sauce onto the {project.label}?" {maker.id} blurted.'
        )
        world.say(
            f'"I did not boop anything," {friend.id} said, looking wounded. "That is a very rude noodle accusation."'
        )
    else:
        maker.memes["care"] += 1
        world.say(
            f'"That is odd," {maker.id} said. "Did you touch the {project.label}, or did the blob arrive by itself?"'
        )
        world.say(
            f'"I did not touch it," {friend.id} said. "But I am willing to interview the blob."'
        )


def inspect_clues(world: World, maker: Entity, friend: Entity, sauce: SauceSource, pollen: PollenSource) -> None:
    maker.memes["investigating"] += 1
    friend.memes["investigating"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Look," {friend.id} said. "There is a tiny red trail. It came from {sauce.trail}."'
    )
    world.say(
        pollen.sneeze_line
    )
    world.say(
        f'{maker.id} leaned close. "And this yellow fluff is not cheese. It is pollen!"'
    )


def solve(world: World, maker: Entity, friend: Entity, sauce: SauceSource, pollen: PollenSource, project: Project) -> None:
    maker.memes["laughter"] += 1
    friend.memes["laughter"] += 1
    world.say(
        f"All at once, the mystery made silly sense: a dab of marinara had landed first, and the sticky spot had caught drifting {pollen.label}."
    )
    world.say(
        f'The red blob and the yellow dust together made the {project.label} look as if it had sneezed spaghetti freckles.'
    )


def reconcile(world: World, maker: Entity, friend: Entity, talk_style: str) -> None:
    maker.memes["love"] += 1
    friend.memes["love"] += 1
    if talk_style == "blurt_first":
        maker.memes["apology"] += 1
        friend.memes["forgive"] += 1
        world.say(
            f'"Sorry," {maker.id} said. "I blamed you before I solved the mystery."'
        )
        world.say(
            f'"It is all right," {friend.id} said. "Next time, please question the sauce before you question me."'
        )
    else:
        world.say(
            f'"Good thing we asked before getting grumpy," {maker.id} said.'
        )
        world.say(
            f'"Yes," {friend.id} said. "The sauce was suspicious enough already."'
        )


def clean_and_continue(world: World, maker: Entity, friend: Entity, parent: Entity, cleaner: Cleaner, project: Project) -> None:
    proj = world.get("project")
    proj.meters["clean"] += 1
    proj.meters["sauce_mark"] = 0.0
    proj.meters["pollen_mark"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} handed them {cleaner.phrase}, and together they {cleaner.action}."
    )
    world.say(
        f'Soon the {project.label} was neat again. "Can we continue now?" {friend.id} asked.'
    )
    world.say(
        f'"Absolutely," {maker.id} said. "But from now on, our restaurant has a strict no-floating-clues rule."'
    )
    world.say(
        f"They rang their pretend dinner bell, giggled at the very serious noodles, and got back to work side by side."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    sauce: SauceSource,
    pollen: PollenSource,
    project_cfg: Project,
    cleaner: Cleaner,
    maker_name: str,
    maker_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    talk_style: str,
) -> World:
    world = World()
    maker = world.add(Entity(
        id="maker",
        kind="character",
        type=maker_gender,
        label=maker_name,
        phrase=maker_name,
        role="maker",
        traits=["imaginative"],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        phrase=friend_name,
        role="friend",
        traits=["funny"],
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    project = world.add(Entity(
        id="project",
        kind="thing",
        type=project_cfg.id,
        label=project_cfg.label,
        phrase=project_cfg.phrase,
        show_marks=project_cfg.show_marks,
        tags=set(project_cfg.tags),
    ))
    world.add(Entity(
        id="sauce",
        kind="thing",
        type="sauce",
        label=sauce.label,
        phrase=sauce.phrase,
        edible=True,
        sticky=True,
        tags=set(sauce.tags),
    ))
    world.add(Entity(
        id="pollen",
        kind="thing",
        type="pollen",
        label=pollen.label,
        phrase=pollen.phrase,
        powdery=True,
        tags=set(pollen.tags),
    ))

    world.para()
    setup(world, maker, friend, place, project_cfg)
    lunch_nearby(world, maker, sauce)

    world.para()
    mystery_appears(world, place, sauce, pollen, project_cfg)
    accuse_or_ask(world, maker, friend, talk_style, project_cfg)

    world.para()
    inspect_clues(world, maker, friend, sauce, pollen)
    solve(world, maker, friend, sauce, pollen, project_cfg)
    reconcile(world, maker, friend, talk_style)

    world.para()
    clean_and_continue(world, maker, friend, parent, cleaner, project_cfg)

    world.facts.update(
        place=place,
        sauce_cfg=sauce,
        pollen_cfg=pollen,
        project_cfg=project_cfg,
        cleaner=cleaner,
        maker=maker,
        friend=friend,
        parent=parent,
        project=project,
        talk_style=talk_style,
        outcome=outcome_of(StoryParams(
            place=place.id,
            sauce=sauce.id,
            pollen=pollen.id,
            project=project_cfg.id,
            cleaner=cleaner.id,
            maker_name=maker_name,
            maker_gender=maker_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            parent=parent_type,
            talk_style=talk_style,
            seed=None,
        )),
        mystery_visible=project.meters["mystery"] >= THRESHOLD,
        friend_hurt=friend.memes["hurt"] >= THRESHOLD,
        solved=project.meters["solved"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
PLACES = {
    "patio": Place(
        id="patio",
        label="the sunny back patio",
        scene="A little table sat under striped shade, with crayons, paper, and two upside-down colanders pretending to be chef hats.",
        food_sources={"bowl", "spoon"},
        pollen_sources={"daisy", "lily"},
        draft="a warm little puff of wind from the garden",
        flower_phrase="pots of flowers leaned near the table",
        tags={"patio", "flowers"},
    ),
    "balcony": Place(
        id="balcony",
        label="the apartment balcony",
        scene="The railing was wrapped with toy lights, and a cardboard box had been promoted to the very important noodle counter.",
        food_sources={"cup", "spoon"},
        pollen_sources={"lily", "dandelion"},
        draft="a swirly breeze from above the street",
        flower_phrase="window boxes of flowers nodded along the rail",
        tags={"balcony", "flowers"},
    ),
    "garden_table": Place(
        id="garden_table",
        label="the garden table",
        scene="A checked cloth flapped at the corners, and every chair had been announced to be a royal pasta throne.",
        food_sources={"bowl", "cup"},
        pollen_sources={"daisy", "dandelion"},
        draft="a busy breeze between the flowerbeds",
        flower_phrase="the flowerbeds hummed with bees and bright petals",
        tags={"garden", "flowers"},
    ),
}

SAUCES = {
    "bowl": SauceSource(
        id="bowl",
        label="bowl of marinara",
        phrase="a bowl of marinara beside the breadsticks",
        spill_line="A tiny wobble in the table sent one brave red drop hopping out of the bowl.",
        trail="the bowl of marinara",
        tags={"marinara", "sauce"},
    ),
    "spoon": SauceSource(
        id="spoon",
        label="sauce spoon",
        phrase="a spaghetti spoon with one last shiny stripe of marinara on it",
        spill_line="The spoon tipped and kissed the paper with a neat red plop.",
        trail="the spaghetti spoon",
        tags={"marinara", "sauce"},
    ),
    "cup": SauceSource(
        id="cup",
        label="dip cup",
        phrase="a little dip cup of marinara from lunch",
        spill_line="A tiny red drip slid down the cup and landed with a comic splat.",
        trail="the little dip cup",
        tags={"marinara", "sauce"},
    ),
}

POLLENS = {
    "daisy": PollenSource(
        id="daisy",
        label="daisy pollen",
        phrase="daisy pollen",
        drift_line="Then {draft} whisked pale yellow daisy pollen across the sticky spot.",
        sneeze_line='"Achoo!" said {friend}. "That settles it. Something powdery is on the case."'.format(friend="friend"),
        tags={"pollen", "flowers"},
    ),
    "lily": PollenSource(
        id="lily",
        label="lily pollen",
        phrase="lily pollen",
        drift_line="Then {draft} brushed golden lily pollen onto the sticky red dab.",
        sneeze_line='"Achoo!" said friend. "That is definitely not noodle dust."',
        tags={"pollen", "flowers"},
    ),
    "dandelion": PollenSource(
        id="dandelion",
        label="dandelion pollen",
        phrase="dandelion pollen",
        drift_line="Then {draft} carried soft dandelion pollen over and sprinkled it on top.",
        sneeze_line='"Achoo!" said friend. "I think the flowers are trying to leave clues."',
        tags={"pollen", "flowers"},
    ),
}

PROJECTS = {
    "menu": Project(
        id="menu",
        label="menu",
        phrase="a paper menu with curly noodle borders",
        role_word="menu",
        show_marks=True,
        tags={"paper", "menu"},
    ),
    "sign": Project(
        id="sign",
        label="sign",
        phrase="a big poster sign that said WELCOME TO THE GRAND SPAGHETTI PALACE",
        role_word="sign",
        show_marks=True,
        tags={"paper", "sign"},
    ),
    "castle": Project(
        id="castle",
        label="cardboard castle",
        phrase="a cardboard castle where the pretend meatballs were supposed to live",
        role_word="castle",
        show_marks=True,
        tags={"cardboard", "castle"},
    ),
    "tray": Project(
        id="tray",
        label="plastic tray",
        phrase="a shiny plastic tray for pretend plates",
        role_word="tray",
        show_marks=False,
        tags={"plastic", "tray"},
    ),
}

CLEANERS = {
    "cloth": Cleaner(
        id="cloth",
        label="damp cloth",
        phrase="a damp cloth",
        action="wiped the sticky spot clean in patient little circles",
        tags={"cloth", "clean"},
    ),
    "sponge": Cleaner(
        id="sponge",
        label="kitchen sponge",
        phrase="a soft kitchen sponge",
        action="dabbed the marinara away and brushed off the pollen",
        tags={"sponge", "clean"},
    ),
    "towel": Cleaner(
        id="towel",
        label="paper towel",
        phrase="a folded paper towel",
        action="blotted the sauce, then lifted the pollen gently away",
        tags={"towel", "clean"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]


# ---------------------------------------------------------------------------
# Per-world params.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    sauce: str
    pollen: str
    project: str
    cleaner: str
    maker_name: str
    maker_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    talk_style: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "marinara": [
        (
            "What is marinara?",
            "Marinara is a tomato sauce. It is red, a little wet, and often eaten with pasta."
        )
    ],
    "pollen": [
        (
            "What is pollen?",
            "Pollen is a tiny yellow dust made by flowers. Wind or insects can carry it from place to place."
        )
    ],
    "sticky": [
        (
            "Why can pollen stick to sauce?",
            "Sauce is wet and sticky, so light bits of pollen can cling to it. That is why a red sauce spot can catch yellow dust."
        )
    ],
    "dialogue": [
        (
            "Why is talking helpful during a mystery?",
            "Talking helps people compare clues instead of guessing wildly. When everyone shares what they saw, the true answer is easier to find."
        )
    ],
    "apology": [
        (
            "Why do apologies help friends?",
            "An apology shows that someone knows they caused hurt and wants to make things better. It helps trust come back."
        )
    ],
    "clean": [
        (
            "Why do people wipe up sauce quickly?",
            "Wiping sauce quickly keeps it from spreading and staining more things. It also makes cleanup easier."
        )
    ],
}
KNOWLEDGE_ORDER = ["marinara", "pollen", "sticky", "dialogue", "apology", "clean"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maker = f["maker"]
    friend = f["friend"]
    project = f["project_cfg"]
    place = f["place"]
    style_line = "Make it playful and funny, with lively dialogue and a reconciled ending."
    return [
        f'Write a comedy for a 3-to-5-year-old where two children find a strange marinara-and-pollen clue on a {project.label}.',
        f"Tell a small mystery-to-solve story set in {place.label} where {maker.label} and {friend.label} investigate a silly mess through dialogue, then make up.",
        f'Write a story that includes the exact words "continue", "marinara", and "pollen". {style_line}',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker = f["maker"]
    friend = f["friend"]
    place = f["place"]
    sauce = f["sauce_cfg"]
    pollen = f["pollen_cfg"]
    project = f["project_cfg"]
    cleaner = f["cleaner"]
    parent = f["parent"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {maker.label} and {friend.label}, two children playing restaurant together in {place.label}. Their grown-up helps them clean up at the end."
        ),
        (
            f"What mystery did they have to solve?",
            f"They found a red-and-yellow blotch on their {project.label} and had to figure out where it came from. The funny-looking clue made them stop their game and investigate."
        ),
        (
            f"What were the two clues?",
            f"One clue was red marinara, and the other was drifting {pollen.label}. The sticky sauce caught the powdery pollen, which is why the mess looked so odd."
        ),
    ]
    if f["talk_style"] == "blurt_first":
        qa.append(
            (
                f"Why did {friend.label}'s feelings get hurt?",
                f"{maker.label} first blurted out a blamey question and made it sound as if {friend.label} had caused the mess. That stung because {friend.label} had not touched the {project.label} at all."
            )
        )
        qa.append(
            (
                f"How did they reconcile?",
                f"After they solved the mystery, {maker.label} apologized for blaming {friend.label} too quickly. {friend.label} forgave {maker.pronoun('object')}, so they could laugh together and keep playing."
            )
        )
    else:
        qa.append(
            (
                "How did talking help them solve the mystery?",
                f"They asked each other questions instead of fighting. Because they stayed calm, they could notice the red trail from {sauce.trail} and the yellow {pollen.label} clue."
            )
        )
        qa.append(
            (
                "How did the story show reconciliation?",
                f"The children stayed kind, solved the problem together, and ended up giggling on the same side again. Their teamwork is what let the play continue."
            )
        )
    qa.append(
        (
            f"How did the grown-up help?",
            f"{parent.label_word.capitalize()} handed them {cleaner.phrase} so they could clean the {project.label}. The cleanup turned the solved mystery into a fresh start."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children cleaning the mess, laughing about the silly clue, and asking to continue their pretend restaurant. The final image shows that the friendship is tidy again too."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"marinara", "pollen", "sticky", "dialogue", "clean"}
    if world.facts["talk_style"] == "blurt_first":
        tags.add("apology")
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
# Trace.
# ---------------------------------------------------------------------------
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
        flags = [name for name, on in (
            ("show_marks", e.show_marks),
            ("sticky", e.sticky),
            ("edible", e.edible),
            ("powdery", e.powdery),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="patio",
        sauce="bowl",
        pollen="daisy",
        project="sign",
        cleaner="cloth",
        maker_name="Lily",
        maker_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent="mother",
        talk_style="blurt_first",
        seed=None,
    ),
    StoryParams(
        place="balcony",
        sauce="cup",
        pollen="lily",
        project="menu",
        cleaner="sponge",
        maker_name="Max",
        maker_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
        talk_style="ask_first",
        seed=None,
    ),
    StoryParams(
        place="garden_table",
        sauce="bowl",
        pollen="dandelion",
        project="castle",
        cleaner="towel",
        maker_name="Zoe",
        maker_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        talk_style="blurt_first",
        seed=None,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A combination is valid when the place really has the chosen marinara source,
% the place really has the chosen pollen source, and the project can show marks.
valid(Place, Sauce, Pollen, Project) :-
    place(Place), sauce(Sauce), pollen(Pollen), project(Project),
    has_food(Place, Sauce), has_pollen(Place, Pollen), shows_marks(Project).

outcome(apology_reconcile) :- chosen_talk(blurt_first).
outcome(quick_reconcile)   :- chosen_talk(ask_first).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for sauce in sorted(place.food_sources):
            lines.append(asp.fact("has_food", place_id, sauce))
        for pollen in sorted(place.pollen_sources):
            lines.append(asp.fact("has_pollen", place_id, pollen))
    for sauce_id in SAUCES:
        lines.append(asp.fact("sauce", sauce_id))
    for pollen_id in POLLENS:
        lines.append(asp.fact("pollen", pollen_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        if project.show_marks:
            lines.append(asp.fact("shows_marks", project_id))
    lines.append(asp.fact("talk_style", "blurt_first"))
    lines.append(asp.fact("talk_style", "ask_first"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(
        asp_program(
            extra=f"chosen_talk({params.talk_style}).",
            show="#show outcome/1.",
        )
    )
    atoms = asp.atoms(model, "outcome")
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

    cases = list(CURATED)
    for style in ["blurt_first", "ask_first"]:
        cases.append(
            StoryParams(
                place="patio",
                sauce="bowl",
                pollen="daisy",
                project="sign",
                cleaner="cloth",
                maker_name="Lily",
                maker_gender="girl",
                friend_name="Tom",
                friend_gender="boy",
                parent="mother",
                talk_style=style,
                seed=0,
            )
        )
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A funny mystery storyworld about marinara, pollen, dialogue, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sauce", choices=SAUCES)
    ap.add_argument("--pollen", choices=POLLENS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--cleaner", choices=CLEANERS)
    ap.add_argument("--talk-style", choices=["blurt_first", "ask_first"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: Optional[str] = None, avoid: str = "") -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), chosen_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sauce and args.pollen and args.project:
        place = PLACES[args.place]
        sauce = SAUCES[args.sauce]
        pollen = POLLENS[args.pollen]
        project = PROJECTS[args.project]
        if not (place_allows(place, sauce, pollen) and project_works(project)):
            raise StoryError(explain_rejection(place, sauce, pollen, project))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sauce is None or combo[1] == args.sauce)
        and (args.pollen is None or combo[2] == args.pollen)
        and (args.project is None or combo[3] == args.project)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sauce_id, pollen_id, project_id = rng.choice(sorted(combos))
    cleaner_id = args.cleaner or rng.choice(sorted(CLEANERS))
    maker_name, maker_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=maker_name)
    parent = args.parent or rng.choice(["mother", "father"])
    talk_style = args.talk_style or rng.choice(["blurt_first", "ask_first"])
    return StoryParams(
        place=place_id,
        sauce=sauce_id,
        pollen=pollen_id,
        project=project_id,
        cleaner=cleaner_id,
        maker_name=maker_name,
        maker_gender=maker_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        talk_style=talk_style,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        sauce = SAUCES[params.sauce]
        pollen = POLLENS[params.pollen]
        project = PROJECTS[params.project]
        cleaner = CLEANERS[params.cleaner]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not (place_allows(place, sauce, pollen) and project_works(project)):
        raise StoryError(explain_rejection(place, sauce, pollen, project))
    if params.talk_style not in {"blurt_first", "ask_first"}:
        raise StoryError("(Invalid talk style. Choose blurt_first or ask_first.)")
    if params.parent not in {"mother", "father"}:
        raise StoryError("(Invalid parent type. Choose mother or father.)")

    world = tell(
        place=place,
        sauce=sauce,
        pollen=pollen,
        project_cfg=project,
        cleaner=cleaner,
        maker_name=params.maker_name,
        maker_gender=params.maker_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        talk_style=params.talk_style,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sauce, pollen, project) combos:\n")
        for place, sauce, pollen, project in combos:
            print(f"  {place:12} {sauce:7} {pollen:10} {project}")
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
            header = (
                f"### {p.maker_name} & {p.friend_name}: {p.sauce} + {p.pollen} "
                f"at {p.place} on {p.project} ({outcome_of(p)})"
            )
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
