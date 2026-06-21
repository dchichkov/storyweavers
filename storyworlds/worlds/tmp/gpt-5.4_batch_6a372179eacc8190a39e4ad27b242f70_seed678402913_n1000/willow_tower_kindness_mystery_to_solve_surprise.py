#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/willow_tower_kindness_mystery_to_solve_surprise.py
==============================================================================

A standalone storyworld for a heartwarming "kindness mystery" tale built around
a willow tree and a tower. A child makes a small tower in a cozy place, finds a
problem, follows a gentle clue, and discovers that a shy helper has been kind in
secret. The ending proves the change with a repaired tower and a warm surprise.

Run it
------
python storyworlds/worlds/gpt-5.4/willow_tower_kindness_mystery_to_solve_surprise.py
python storyworlds/worlds/gpt-5.4/willow_tower_kindness_mystery_to_solve_surprise.py --project book_tower --helper gardener
python storyworlds/worlds/gpt-5.4/willow_tower_kindness_mystery_to_solve_surprise.py --problem broken_base
python storyworlds/worlds/gpt-5.4/willow_tower_kindness_mystery_to_solve_surprise.py --all
python storyworlds/worlds/gpt-5.4/willow_tower_kindness_mystery_to_solve_surprise.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/willow_tower_kindness_mystery_to_solve_surprise.py --trace --seed 7
python storyworlds/worlds/gpt-5.4/willow_tower_kindness_mystery_to_solve_surprise.py --json
python storyworlds/worlds/gpt-5.4/willow_tower_kindness_mystery_to_solve_surprise.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    willow_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    material: str
    need: str
    top_piece: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    need: str
    effect: str
    question: str
    clue_prompt: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    type: str
    role_word: str
    skill: str
    clue_tag: str
    entrance: str
    kindness: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    text: str
    tag: str
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


def _r_tilt_worry(world: World) -> list[str]:
    out: list[str] = []
    tower = world.get("tower")
    child = world.get("child")
    if tower.meters["unstable"] >= THRESHOLD:
        sig = ("tilt_worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_mended_relief(world: World) -> list[str]:
    out: list[str] = []
    tower = world.get("tower")
    child = world.get("child")
    helper = world.get("helper")
    if tower.meters["repaired"] >= THRESHOLD:
        sig = ("mended_relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["gratitude"] += 1
            helper.memes["connection"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="tilt_worry", tag="emotion", apply=_r_tilt_worry),
    Rule(name="mended_relief", tag="emotion", apply=_r_mended_relief),
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
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def can_fix(project: Project, problem: Problem, helper: HelperCfg) -> bool:
    return project.need == problem.need == helper.skill


def clue_matches(helper: HelperCfg, clue: Clue) -> bool:
    return helper.clue_tag == clue.tag


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for project_id, project in PROJECTS.items():
            for problem_id, problem in PROBLEMS.items():
                for helper_id, helper in HELPERS.items():
                    for clue_id, clue in CLUES.items():
                        if can_fix(project, problem, helper) and clue_matches(helper, clue):
                            combos.append((place_id, project_id, problem_id, helper_id, clue_id))
    return combos


@dataclass
class StoryParams:
    place: str
    project: str
    problem: str
    helper: str
    clue: str
    child_name: str
    child_type: str
    grownup_type: str
    trait: str
    seed: Optional[int] = None


def build_setup(world: World, child: Entity, grownup: Entity, place: Place, project: Project) -> None:
    child.memes["joy"] += 1
    tower = world.get("tower")
    tower.meters["standing"] += 1
    world.say(
        f"On a soft morning, {child.id} hurried to {place.label}. {place.opening} {place.willow_line}"
    )
    world.say(
        f"With careful hands, {child.id} built {project.phrase}. Piece by piece, the {project.material} rose into a little tower that made {child.pronoun('object')} smile."
    )
    world.say(
        f'{grownup.label_word.capitalize()} watched from nearby and said, "That is a lovely tower." {child.id} stood a little taller when {child.pronoun()} heard that.'
    )


def discover_problem(world: World, child: Entity, project: Project, problem: Problem) -> None:
    tower = world.get("tower")
    tower.meters["unstable"] += 1
    tower.meters[problem.id] += 1
    propagate(world, narrate=False)
    child.memes["curiosity"] += 1
    world.say(
        f"But when {child.id} came back after chasing a drifting leaf, something was wrong. {problem.effect}"
    )
    world.say(
        f'{child.id} whispered, "{problem.question}" The mystery made the sunny place feel very quiet for one moment.'
    )


def predict_kind_fix(world: World, project: Project, problem: Problem, helper: HelperCfg) -> dict:
    sim = world.copy()
    tower = sim.get("tower")
    tower.meters["unstable"] += 0
    if can_fix(project, problem, helper):
        tower.meters["repaired"] += 1
        tower.meters["unstable"] = 0.0
        tower.meters["standing"] += 1
    propagate(sim, narrate=False)
    return {
        "repaired": tower.meters["repaired"] >= THRESHOLD,
        "relief": sim.get("child").memes["relief"] >= THRESHOLD,
    }


def search_for_clue(world: World, child: Entity, clue: Clue, problem: Problem) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} did not stomp or cry. Instead, {child.pronoun()} looked all around the willow roots and the grass near the tower."
    )
    world.say(
        f"{problem.clue_prompt} Then {child.pronoun()} noticed {clue.text}"
    )


def follow_clue(world: World, child: Entity, helper: Entity, helper_cfg: HelperCfg, clue: Clue) -> None:
    child.memes["trust"] += 1
    helper.memes["shy"] += 1
    world.say(
        f"The clue did not look scary at all. It looked like someone had been helping very gently."
    )
    world.say(
        f"{child.id} followed it with small, hopeful steps until {helper_cfg.entrance}"
    )


def ask_kindly(world: World, child: Entity, helper: Entity, project: Project, problem: Problem) -> None:
    child.memes["kindness"] += 1
    helper.memes["seen"] += 1
    world.say(
        f'"Did you see what happened to my {project.label}?" {child.id} asked. {child.pronoun().capitalize()} kept {child.pronoun("possessive")} voice soft, because the mystery did not feel mean.'
    )
    world.say(
        f"{helper.id} looked at the ground first, then at the little tower, as if deciding whether a brave truth was safe to share."
    )


def reveal_and_fix(world: World, child: Entity, helper: Entity,
                   project: Project, problem: Problem, helper_cfg: HelperCfg) -> None:
    tower = world.get("tower")
    if not can_fix(project, problem, helper_cfg):
        raise StoryError("This helper cannot honestly solve this tower problem.")
    pred = predict_kind_fix(world, project, problem, helper_cfg)
    helper.memes["kindness"] += 1
    helper.memes["bravery"] += 1
    tower.meters["repaired"] += 1
    tower.meters["unstable"] = 0.0
    tower.meters["standing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I did," {helper.id} said at last. "I saw it start to wobble, so I {helper_cfg.kindness}."'
    )
    world.say(
        f"Together they set the pieces right again. Soon the little tower stood steady under the willow, and the mystery turned into relief."
    )
    if pred["repaired"] and pred["relief"]:
        world.say(
            f"{child.id} blinked in surprise. The stranger in the mystery had not been a taker at all, but a helper."
        )


def surprise_ending(world: World, child: Entity, helper: Entity, grownup: Entity,
                    project: Project, helper_cfg: HelperCfg) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then came one more surprise. {helper_cfg.surprise}"
    )
    world.say(
        f'{grownup.label_word.capitalize()} smiled and said, "Kindness can be quiet, but it still shines."'
    )
    world.say(
        f"{child.id} made room beside the tower and invited {helper.id} to stay. Under the willow branches, the two of them admired the steady little tower together, and the whole place felt warmer than before."
    )


def tell(place: Place, project: Project, problem: Problem, helper_cfg: HelperCfg, clue: Clue,
         child_name: str = "Mia", child_type: str = "girl", grownup_type: str = "grandmother",
         trait: str = "gentle") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=[trait],
        label=child_name,
    ))
    grownup = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the grown-up",
    ))
    helper = world.add(Entity(
        id=helper_cfg.label,
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.label,
        phrase=helper_cfg.role_word,
        tags=set(helper_cfg.tags),
    ))
    tower = world.add(Entity(
        id="tower",
        kind="thing",
        type="tower",
        label=project.label,
        phrase=project.phrase,
        attrs={"material": project.material},
        tags=set(project.tags),
    ))
    world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        tags=set(place.tags),
    ))

    build_setup(world, child, grownup, place, project)
    world.para()
    discover_problem(world, child, project, problem)
    search_for_clue(world, child, clue, problem)
    world.para()
    follow_clue(world, child, helper, helper_cfg, clue)
    ask_kindly(world, child, helper, project, problem)
    reveal_and_fix(world, child, helper, project, problem, helper_cfg)
    world.para()
    surprise_ending(world, child, helper, grownup, project, helper_cfg)

    world.facts.update(
        place=place,
        project=project,
        problem=problem,
        helper_cfg=helper_cfg,
        clue=clue,
        child=child,
        helper=helper,
        grownup=grownup,
        tower=tower,
        mystery_solved=tower.meters["repaired"] >= THRESHOLD,
        kindness_shown=helper.memes["kindness"] >= THRESHOLD,
    )
    return world


PLACES = {
    "pond": Place(
        id="pond",
        label="the little pond path",
        opening="A bent bench sat by the path, and ducks whispered on the water.",
        willow_line="Near the edge of the pond, an old willow let its long green branches trail like a curtain.",
        tags={"pond", "willow"},
    ),
    "school_garden": Place(
        id="school_garden",
        label="the school garden",
        opening="Beds of mint and marigolds made the air smell sweet and bright.",
        willow_line="At the corner of the garden, a willow tree spread a soft green shade over a flat patch of grass.",
        tags={"garden", "willow"},
    ),
    "village_green": Place(
        id="village_green",
        label="the village green",
        opening="A stone path curved past flower boxes and a tiny clock tower.",
        willow_line="Beside the path, a willow tree leaned over a sunny spot that felt made for secret projects.",
        tags={"green", "willow", "tower"},
    ),
}

PROJECTS = {
    "book_tower": Project(
        id="book_tower",
        label="book tower",
        phrase="a tower of bright picture books",
        material="books",
        need="stack",
        top_piece="the red book on top",
        tags={"books", "tower"},
    ),
    "pebble_tower": Project(
        id="pebble_tower",
        label="pebble tower",
        phrase="a tower of smooth pond pebbles",
        material="pebbles",
        need="balance",
        top_piece="the flat silver pebble on top",
        tags={"pebbles", "tower"},
    ),
    "twig_tower": Project(
        id="twig_tower",
        label="twig tower",
        phrase="a tower of twigs tied with ribbon",
        material="twigs",
        need="tie",
        top_piece="the blue ribbon bow at the top",
        tags={"twigs", "tower"},
    ),
}

PROBLEMS = {
    "fallen_top": Problem(
        id="fallen_top",
        label="fallen top",
        need="stack",
        effect="The top pieces had slipped down, and the tower leaned to one side like it was too tired to stand.",
        question="Who touched my tower?",
        clue_prompt="There was no crash, no broken pieces, and no muddy footprints.",
        tags={"mystery", "stack"},
    ),
    "broken_base": Problem(
        id="broken_base",
        label="broken base",
        need="balance",
        effect="One stone at the bottom had rolled away, and the tower quivered with the tiniest shake.",
        question="How did my tower start wobbling?",
        clue_prompt="Nothing was smashed. It looked as if someone had tried to stop the fall before it got worse.",
        tags={"mystery", "balance"},
    ),
    "loose_ribbon": Problem(
        id="loose_ribbon",
        label="loose ribbon",
        need="tie",
        effect="The ribbon bow had come loose, and the twigs had spread apart like fingers opening.",
        question="Who was here before me?",
        clue_prompt="The ribbon was not gone. It had been folded neatly on a stone, as if waiting for kind hands.",
        tags={"mystery", "tie"},
    ),
}

HELPERS = {
    "librarian": HelperCfg(
        id="librarian",
        label="Mrs. Vale",
        type="woman",
        role_word="the librarian",
        skill="stack",
        clue_tag="bookmark",
        entrance="Mrs. Vale stepped out from behind the little free shelf with a soft smile",
        kindness="caught the falling books and set them down in a neat pile so none of the pages would bend",
        surprise='Mrs. Vale reached into her apron pocket and pulled out a shiny star bookmark. "This can watch over the top book," she said.',
        tags={"books", "grownup", "quiet"},
    ),
    "gardener": HelperCfg(
        id="gardener",
        label="Mr. Reed",
        type="man",
        role_word="the gardener",
        skill="balance",
        clue_tag="leaf_glove",
        entrance="Mr. Reed looked up from the flower bed with dirt on his gloves and kindness in his eyes",
        kindness="nudged the rolling stone back and kept the others from tumbling while he looked for the right base piece",
        surprise='Mr. Reed opened his hand and showed a small, heart-shaped pebble. "I saved this one because it looked special," he said.',
        tags={"garden", "grownup", "steady"},
    ),
    "neighbor": HelperCfg(
        id="neighbor",
        label="Tessa",
        type="girl",
        role_word="the neighbor girl",
        skill="tie",
        clue_tag="blue_thread",
        entrance="Tessa peeked out from behind the willow trunk, twisting a bit of ribbon between her fingers",
        kindness="picked up the ribbon and tried to keep the twigs together because she did not want the tower to unravel",
        surprise='Tessa held out a tiny paper butterfly she had folded. "I made this for the top," she said. "I hoped it would make your tower smile."',
        tags={"neighbor", "child", "shy"},
    ),
}

CLUES = {
    "bookmark": Clue(
        id="bookmark",
        label="bookmark",
        text="a shiny paper bookmark tucked under one book, with a little painted star on it.",
        tag="bookmark",
        tags={"books", "clue"},
    ),
    "leaf_glove": Clue(
        id="leaf_glove",
        label="leaf-shaped glove mark",
        text="a clean glove print beside the stones, with two willow leaves pressed gently into the damp earth.",
        tag="leaf_glove",
        tags={"garden", "clue"},
    ),
    "blue_thread": Clue(
        id="blue_thread",
        label="blue thread",
        text="a tiny blue thread caught on the willow bark, the same color as the ribbon from the tower.",
        tag="blue_thread",
        tags={"ribbon", "clue"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Ella", "Ruby", "Zoe", "Clara"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Sam", "Finn", "Eli", "Theo", "Max"]
TRAITS = ["gentle", "patient", "curious", "hopeful", "thoughtful"]


KNOWLEDGE = {
    "willow": [(
        "What is a willow tree?",
        "A willow is a tree with long, bendy branches that hang down softly. Its shade can feel calm and cozy."
    )],
    "tower": [(
        "What makes a tower stand up?",
        "A tower stands best when its bottom is steady and its pieces are placed carefully. If the base wobbles, the whole tower can lean."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is doing something gentle or helpful for someone else. Sometimes it is quiet, but it still matters a lot."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is something you do not understand yet and want to figure out. You solve it by noticing clues and asking careful questions."
    )],
    "bookmark": [(
        "What is a bookmark for?",
        "A bookmark helps you keep your place in a book. It can also make a book feel special."
    )],
    "ribbon": [(
        "What does a ribbon do?",
        "A ribbon can tie things together or decorate them. If it comes loose, the things it held may spread apart."
    )],
    "pebble": [(
        "Why are flat pebbles good for stacking?",
        "Flat pebbles balance more easily than round ones because they have a steadier surface. That helps a little tower stay up."
    )],
}
KNOWLEDGE_ORDER = ["willow", "tower", "kindness", "mystery", "bookmark", "ribbon", "pebble"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    project = f["project"]
    problem = f["problem"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "willow" and "tower".',
        f"Tell a gentle mystery where {child.id} builds a {project.label} at {place.label}, notices that something is wrong, and solves the mystery by following a clue.",
        f"Write a kind story where a child asks a soft question instead of getting angry, and discovers that the mystery behind the {problem.label} was really an act of kindness.",
    ]


def pair_noun(helper_cfg: HelperCfg) -> str:
    return helper_cfg.role_word


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    grownup = f["grownup"]
    place = f["place"]
    project = f["project"]
    problem = f["problem"]
    clue = f["clue"]
    helper_cfg = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who built a little {project.label} under a willow, and {helper.id}, who had been helping in secret."
        ),
        (
            f"What was {child.id} making?",
            f"{child.id} was making {project.phrase}. Building it made the quiet place feel bright and special."
        ),
        (
            f"What was the mystery to solve?",
            f"The mystery was why the {project.label} was suddenly wrong. {problem.effect} so {child.id} wondered who had been there."
        ),
        (
            f"What clue did {child.id} find?",
            f"{child.id} found {clue.text} That clue felt gentle, not mean, so it helped {child.pronoun('object')} look for a helper instead of a culprit."
        ),
        (
            f"Who had touched the tower, and why?",
            f"It was {helper.id}, {pair_noun(helper_cfg)}. {helper.pronoun().capitalize()} had touched it to help, because {helper_cfg.kindness}."
        ),
        (
            f"How was the mystery solved?",
            f"{child.id} solved it by staying calm, noticing the clue, and asking a kind question. Because {child.pronoun()} spoke gently, {helper.id} felt safe enough to tell the truth and help fix the tower."
        ),
        (
            "What was the surprise at the end?",
            f"The surprise was that the secret behind the mystery was kindness, and then {helper_cfg.surprise} That made the ending feel warm instead of sad."
        ),
        (
            "How did the story end?",
            f"It ended with the tower standing steady again under the willow. {child.id} and {helper.id} stayed together beside it, which showed that the mystery had turned into a new friendship."
        ),
    ]
    if grownup:
        qa.append((
            f"What did the grown-up say about kindness?",
            f"{grownup.label_word.capitalize()} said that kindness can be quiet, but it still shines. That helped explain why the secret helper had mattered all along."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"willow", "tower", "kindness", "mystery"}
    project = f["project"]
    helper_cfg = f["helper_cfg"]
    clue = f["clue"]
    if project.id == "book_tower" or clue.id == "bookmark":
        tags.add("bookmark")
    if project.id == "twig_tower" or clue.id == "blue_thread":
        tags.add("ribbon")
    if project.id == "pebble_tower" or helper_cfg.id == "gardener":
        tags.add("pebble")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pond",
        project="book_tower",
        problem="fallen_top",
        helper="librarian",
        clue="bookmark",
        child_name="Mia",
        child_type="girl",
        grownup_type="grandmother",
        trait="gentle",
        seed=1,
    ),
    StoryParams(
        place="school_garden",
        project="pebble_tower",
        problem="broken_base",
        helper="gardener",
        clue="leaf_glove",
        child_name="Leo",
        child_type="boy",
        grownup_type="grandfather",
        trait="patient",
        seed=2,
    ),
    StoryParams(
        place="village_green",
        project="twig_tower",
        problem="loose_ribbon",
        helper="neighbor",
        clue="blue_thread",
        child_name="Ruby",
        child_type="girl",
        grownup_type="mother",
        trait="curious",
        seed=3,
    ),
]


def explain_rejection(project: Project, problem: Problem, helper: HelperCfg, clue: Clue) -> str:
    if not can_fix(project, problem, helper):
        return (
            f"(No story: {helper.label} is good at {helper.skill}, but a {project.label} with "
            f"the problem '{problem.label}' needs {problem.need}. Pick a helper whose skill matches the tower problem.)"
        )
    if not clue_matches(helper, clue):
        return (
            f"(No story: the clue '{clue.label}' does not honestly point to {helper.label}. "
            f"Pick the clue that matches this helper's habits.)"
        )
    return "(No story: this combination does not make a coherent kindness mystery.)"


ASP_RULES = r"""
needs(Project, Need) :- project_need(Project, Need).
needs(Problem, Need) :- problem_need(Problem, Need).

can_fix(Project, Problem, Helper) :-
    project(Project), problem(Problem), helper(Helper),
    project_need(Project, Need), problem_need(Problem, Need), helper_skill(Helper, Need).

clue_matches(Helper, Clue) :-
    helper(Helper), clue(Clue), helper_clue(Helper, Tag), clue_tag(Clue, Tag).

valid(Place, Project, Problem, Helper, Clue) :-
    place(Place), project(Project), problem(Problem), helper(Helper), clue(Clue),
    can_fix(Project, Problem, Helper), clue_matches(Helper, Clue).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("project_need", project_id, project.need))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("problem_need", problem_id, problem.need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_skill", helper_id, helper.skill))
        lines.append(asp.fact("helper_clue", helper_id, helper.clue_tag))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_tag", clue_id, clue.tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        default_params.seed = 123
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("SMOKE FAIL during param resolution:", err)

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated story was empty.")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"SMOKE FAIL for params {params}: {err}")
            break

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a willow-side tower, a gentle mystery, and a kind surprise."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.problem and args.helper:
        project = PROJECTS[args.project]
        problem = PROBLEMS[args.problem]
        helper = HELPERS[args.helper]
        clue_obj = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        if not (can_fix(project, problem, helper) and clue_matches(helper, clue_obj)):
            raise StoryError(explain_rejection(project, problem, helper, clue_obj))
    if args.helper and args.clue:
        helper = HELPERS[args.helper]
        clue = CLUES[args.clue]
        if not clue_matches(helper, clue):
            project = PROJECTS[args.project] if args.project else next(iter(PROJECTS.values()))
            problem = PROBLEMS[args.problem] if args.problem else next(iter(PROBLEMS.values()))
            raise StoryError(explain_rejection(project, problem, helper, clue))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.project is None or c[1] == args.project)
        and (args.problem is None or c[2] == args.problem)
        and (args.helper is None or c[3] == args.helper)
        and (args.clue is None or c[4] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, project, problem, helper, clue = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    grownup_type = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        project=project,
        problem=problem,
        helper=helper,
        clue=clue,
        child_name=name,
        child_type=child_type,
        grownup_type=grownup_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        project = PROJECTS[params.project]
        problem = PROBLEMS[params.problem]
        helper = HELPERS[params.helper]
        clue = CLUES[params.clue]
    except KeyError as err:
        raise StoryError(f"Unknown story parameter: {err}") from err

    if not can_fix(project, problem, helper) or not clue_matches(helper, clue):
        raise StoryError(explain_rejection(project, problem, helper, clue))

    world = tell(
        place=place,
        project=project,
        problem=problem,
        helper_cfg=helper,
        clue=clue,
        child_name=params.child_name,
        child_type=params.child_type,
        grownup_type=params.grownup_type,
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
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, project, problem, helper, clue) combos:\n")
        for place, project, problem, helper, clue in combos:
            print(f"  {place:13} {project:12} {problem:12} {helper:10} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.child_name}: {p.project} at {p.place} ({p.problem}, {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
