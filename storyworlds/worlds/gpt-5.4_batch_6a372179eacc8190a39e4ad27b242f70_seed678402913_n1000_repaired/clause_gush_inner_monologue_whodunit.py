#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clause_gush_inner_monologue_whodunit.py
==================================================================

A small whodunit storyworld with inner monologue. A child notices that an
important paper clue has been ruined by a sudden gush of liquid, studies the
scene, and figures out who spilled it. The world model tracks physical state
(wet papers, colored stains, sticky hands, moved objects) and emotional state
(worry, suspicion, relief, honesty), and the rendered prose follows those
changes.

The seed words "clause" and "gush" are built into the domain:
- each place has a house rule with a careful clause about liquids
- the accident itself is narrated as a gush of the chosen liquid

Run it
------
    python storyworlds/worlds/gpt-5.4/clause_gush_inner_monologue_whodunit.py
    python storyworlds/worlds/gpt-5.4/clause_gush_inner_monologue_whodunit.py --place library --paper guestbook
    python storyworlds/worlds/gpt-5.4/clause_gush_inner_monologue_whodunit.py --liquid berry_juice --paper wax_card
    python storyworlds/worlds/gpt-5.4/clause_gush_inner_monologue_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/clause_gush_inner_monologue_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/clause_gush_inner_monologue_whodunit.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "teacher"}
        male = {"boy", "father", "man", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    keeper_type: str
    keeper_word: str
    scene_open: str
    object_phrase: str
    rule_clause: str
    solving_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Liquid:
    id: str
    label: str
    phrase: str
    color: str
    smell: str
    residue: str
    allowed_places: set[str] = field(default_factory=set)
    safe_for_paper: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Paper:
    id: str
    label: str
    phrase: str
    purpose: str
    absorbent: bool = True
    fragile: bool = True
    protected: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectRole:
    id: str
    label: str
    habit: str
    excuse: str
    movement: str
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


def _r_soak_paper(world: World) -> list[str]:
    out: list[str] = []
    liquid = world.get("liquid")
    paper = world.get("paper")
    if liquid.meters["spilled"] < THRESHOLD:
        return out
    if paper.meters["wet"] >= THRESHOLD:
        return out
    sig = ("soak", paper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    paper.meters["wet"] += 1
    if paper.attrs.get("absorbent"):
        paper.meters["stained"] += 1
    if paper.attrs.get("fragile"):
        paper.meters["curled"] += 1
    out.append("__wet_paper__")
    return out


def _r_mark_culprit(world: World) -> list[str]:
    out: list[str] = []
    liquid = world.get("liquid")
    culprit = world.get("culprit")
    if liquid.meters["spilled"] < THRESHOLD:
        return out
    sig = ("mark", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    culprit.meters["sticky_hands"] += 1
    culprit.meters["smell"] += 1
    culprit.meters["panic_steps"] += 1
    out.append("__marked__")
    return out


def _r_room_worry(world: World) -> list[str]:
    out: list[str] = []
    paper = world.get("paper")
    if paper.meters["wet"] < THRESHOLD:
        return out
    sig = ("worry", "room")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("detective").memes["worry"] += 1
    world.get("keeper").memes["worry"] += 1
    world.get("culprit").memes["guilt"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="soak_paper", tag="physical", apply=_r_soak_paper),
    Rule(name="mark_culprit", tag="physical", apply=_r_mark_culprit),
    Rule(name="room_worry", tag="social", apply=_r_room_worry),
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
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(place: Place, liquid: Liquid, paper: Paper) -> bool:
    return place.id in liquid.allowed_places and paper.absorbent and not liquid.safe_for_paper


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for liquid_id, liquid in LIQUIDS.items():
            for paper_id, paper in PAPERS.items():
                if valid_combo(place, liquid, paper):
                    combos.append((place_id, liquid_id, paper_id))
    return combos


def explain_rejection(place: Place, liquid: Liquid, paper: Paper) -> str:
    if place.id not in liquid.allowed_places:
        return (
            f"(No story: {liquid.label} does not belong in {place.label}, so the scene "
            f"would feel forced. Pick a liquid that plausibly appears there.)"
        )
    if not paper.absorbent:
        return (
            f"(No story: {paper.phrase} will not soak up a spill, so there is no ruined "
            f"clue to investigate. Pick a paper item that can get wet and stained.)"
        )
    if liquid.safe_for_paper:
        return (
            f"(No story: {liquid.label} would not leave a meaningful stain here, so the "
            f"detective would have almost nothing to solve.)"
        )
    return "(No story: this combination does not make a reasonable soaked-paper mystery.)"


def culprit_signature(liquid: Liquid) -> str:
    return f"{liquid.color}|{liquid.smell}|{liquid.residue}"


def suspect_evidence_line(name: str, liquid: Liquid) -> str:
    return f"{name} had {liquid.color} spots and smelled faintly of {liquid.smell}."


def predict_scene(world: World) -> dict:
    sim = world.copy()
    liquid = sim.get("liquid")
    liquid.meters["spilled"] += 1
    propagate(sim, narrate=False)
    culprit = sim.get("culprit")
    paper = sim.get("paper")
    return {
        "paper_wet": paper.meters["wet"] >= THRESHOLD,
        "paper_stained": paper.meters["stained"] >= THRESHOLD,
        "culprit_marked": culprit.meters["sticky_hands"] >= THRESHOLD,
        "signature": culprit_signature(LIQUIDS[sim.facts["liquid_cfg"].id]),
    }


def introduce(world: World, place: Place, detective: Entity, keeper: Entity, paper: Entity) -> None:
    world.say(
        f"{place.scene_open} On a small table lay {paper.phrase}, the very paper that held "
        f"{paper.attrs['purpose']}."
    )
    world.say(
        f"{detective.id} loved small puzzles, so {detective.pronoun()} had come early just to look around."
    )
    world.say(
        f"Near the door, {keeper.label_word} had pinned up a neat house rule with a careful clause: "
        f'"{place.rule_clause}"'
    )


def gather_suspects(world: World, suspects: list[Entity], roles: list[SuspectRole]) -> None:
    bits = []
    for suspect, role in zip(suspects, roles):
        bits.append(f"{suspect.id} the {role.label} {role.movement}")
    world.say("Three children were nearby: " + ", ".join(bits[:-1]) + ", and " + bits[-1] + ".")
    world.say("It felt like the beginning of a real whodunit, only smaller and much stickier.")


def accident(world: World, liquid: Liquid, paper: Entity) -> None:
    world.get("liquid").meters["spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the trouble. A sudden gush of {liquid.phrase} tipped across the table and splashed onto "
        f"{paper.label}."
    )
    if paper.meters["wet"] >= THRESHOLD:
        world.say(
            f"The paper darkened at once. Its corners curled, and a {liquid.color} stain spread over the writing."
        )


def keeper_distress(world: World, keeper: Entity, paper: Entity) -> None:
    world.say(
        f'"Oh dear," said {keeper.label_word}, hurrying over. "{paper.attrs["purpose"].capitalize()} is smudged now."'
    )
    world.say("Nobody cried. Still, the room went quiet in the way rooms do when something important has gone wrong.")


def inner_monologue(world: World, detective: Entity, liquid: Liquid) -> None:
    detective.memes["focus"] += 1
    pred = predict_scene(world)
    world.facts["predicted_signature"] = pred["signature"]
    world.say(
        f'{detective.id} looked at the stain and thought, "All right. Do not guess. Think."'
    )
    world.say(
        f'"The spill left {liquid.color} marks, smells like {liquid.smell}, and would leave {liquid.residue} on the one '
        f'who made it," {detective.pronoun()} told {detective.pronoun("object")}self.'
    )


def inspect_suspects(world: World, detective: Entity, suspects: list[Entity], culprit: Entity, liquid: Liquid) -> None:
    lines = []
    for suspect in suspects:
        if suspect.id == culprit.id:
            suspect.attrs["evidence"] = suspect_evidence_line(suspect.id, liquid)
            lines.append(
                f"{suspect.id} tried to hide {suspect.pronoun('possessive')} hands, but {detective.id} noticed "
                f"{liquid.color} specks and the smell of {liquid.smell}."
            )
        else:
            suspect.attrs["evidence"] = f"{suspect.id} looked clean and did not smell like the spill."
            lines.append(
                f"{suspect.id} looked worried too, but there were no {liquid.color} spots on {suspect.pronoun('possessive')} fingers."
            )
    for line in lines:
        world.say(line)


def solve(world: World, detective: Entity, culprit: Entity, keeper: Entity, liquid: Liquid, paper: Entity) -> None:
    detective.memes["certainty"] += 1
    world.say(
        f'{detective.id} took one breath and said, "I know who did it. It was {culprit.id}."'
    )
    world.say(
        f'"I can tell because the paper was hit by {liquid.phrase}, and {culprit.id} still has {liquid.color} spots '
        f'and smells like {liquid.smell}. The clue is on {culprit.pronoun("possessive")} hands, not just on the table."'
    )
    world.say(
        f"{keeper.label_word.capitalize()} looked from the stain to {culprit.id}, then slowly nodded."
    )
    culprit.memes["honesty"] += 1
    world.say(
        f'{culprit.id} swallowed. "I only meant to peek at {paper.label}," {culprit.pronoun()} admitted. '
        f'"My cup slipped when I leaned too close."'
    )


def repair(world: World, culprit: Entity, detective: Entity, keeper: Entity, place: Place, paper: Entity) -> None:
    paper.meters["saved"] += 1
    culprit.memes["relief"] += 1
    detective.memes["relief"] += 1
    keeper.memes["relief"] += 1
    world.say(
        f"{keeper.label_word.capitalize()} was not cross for long. {keeper.pronoun().capitalize()} brought a soft cloth, "
        f"copied the blurred lines onto fresh paper, and asked {culprit.id} to help."
    )
    world.say(
        f"{culprit.id} helped carefully this time, and {detective.id} stood nearby, proud that the truth had been found "
        f"without any shouting."
    )
    world.say(
        f"Before they left, {keeper.label_word} tapped the little rule again. That gentle clause suddenly felt wise to everyone."
    )
    world.say(place.solving_image)


def tell(
    place: Place,
    liquid: Liquid,
    paper_cfg: Paper,
    detective_name: str = "Nora",
    detective_gender: str = "girl",
    keeper_name: str = "Ms. Bell",
    suspect_names: Optional[list[str]] = None,
    culprit_index: int = 0,
    role_ids: Optional[list[str]] = None,
) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    keeper = world.add(
        Entity(
            id=keeper_name,
            kind="character",
            type=place.keeper_type,
            label=place.keeper_word,
            role="keeper",
        )
    )
    paper = world.add(
        Entity(
            id="paper",
            type="paper",
            label=paper_cfg.label,
            phrase=paper_cfg.phrase,
            attrs={
                "purpose": paper_cfg.purpose,
                "absorbent": paper_cfg.absorbent,
                "fragile": paper_cfg.fragile,
                "protected": paper_cfg.protected,
            },
            tags=set(paper_cfg.tags),
        )
    )
    liquid_ent = world.add(
        Entity(
            id="liquid",
            type="liquid",
            label=liquid.label,
            phrase=liquid.phrase,
            attrs={"color": liquid.color, "smell": liquid.smell, "residue": liquid.residue},
            tags=set(liquid.tags),
        )
    )

    suspect_names = suspect_names or ["Milo", "Tess", "Ivy"]
    role_ids = role_ids or ["sketcher", "helper", "reader"]
    roles = [ROLES[rid] for rid in role_ids]
    suspects: list[Entity] = []
    for idx, name in enumerate(suspect_names):
        role = roles[idx]
        suspects.append(
            world.add(
                Entity(
                    id=name,
                    kind="character",
                    type="girl" if name in GIRL_NAMES else "boy",
                    label=role.label,
                    role="suspect",
                    attrs={"role_id": role.id, "habit": role.habit, "excuse": role.excuse},
                    tags=set(role.tags),
                )
            )
        )
    culprit = suspects[culprit_index]
    culprit.role = "culprit"

    introduce(world, place, detective, keeper, paper)
    gather_suspects(world, suspects, roles)

    world.para()
    accident(world, liquid, paper)
    keeper_distress(world, keeper, paper)

    world.para()
    inner_monologue(world, detective, liquid)
    inspect_suspects(world, detective, suspects, culprit, liquid)

    world.para()
    solve(world, detective, culprit, keeper, liquid, paper)
    repair(world, culprit, detective, keeper, place, paper)

    world.facts.update(
        place=place,
        liquid_cfg=liquid,
        paper_cfg=paper_cfg,
        detective=detective,
        keeper=keeper,
        paper=paper,
        liquid=liquid_ent,
        suspects=suspects,
        culprit=culprit,
        roles=roles,
        signature=culprit_signature(liquid),
        solved=True,
    )
    return world


PLACES = {
    "library": Place(
        id="library",
        label="the library corner",
        keeper_type="librarian",
        keeper_word="the librarian",
        scene_open="After school, the library corner smelled like paper, pencils, and quiet thinking.",
        object_phrase="a ribbon bookmark and a small brass bell",
        rule_clause="Please keep drinks on the side shelf so the papers stay dry.",
        solving_image="Soon the copied page lay flat under the brass bell, and the little mystery felt neatly tucked away.",
        tags={"library", "rules"},
    ),
    "museum": Place(
        id="museum",
        label="the museum workroom",
        keeper_type="teacher",
        keeper_word="the curator",
        scene_open="At the museum workroom, dust motes drifted in the sun and every object seemed to hold a secret.",
        object_phrase="a tray of old labels and a careful pencil",
        rule_clause="Visitors may look closely, but cups must stay off the history table.",
        solving_image="When the new label was finished, it rested beside the old shell exhibit, and the room felt peaceful again.",
        tags={"museum", "rules"},
    ),
    "clubhouse": Place(
        id="clubhouse",
        label="the detective clubhouse",
        keeper_type="mother",
        keeper_word="the club leader",
        scene_open="In the backyard clubhouse, painted stars shone on the walls and a toy magnifying glass hung from a peg.",
        object_phrase="a tin badge and a notebook with checkboxes",
        rule_clause="Snacks may come inside, but cups must stay by the window crate.",
        solving_image="By sunset the fresh note was pinned straight on the wall, and even the toy magnifying glass looked satisfied.",
        tags={"clubhouse", "rules"},
    ),
}

LIQUIDS = {
    "berry_juice": Liquid(
        id="berry_juice",
        label="berry juice",
        phrase="berry juice",
        color="purple",
        smell="berries",
        residue="sticky sweetness",
        allowed_places={"library", "clubhouse"},
        safe_for_paper=False,
        tags={"juice", "spill"},
    ),
    "orange_drink": Liquid(
        id="orange_drink",
        label="orange drink",
        phrase="orange drink",
        color="orange",
        smell="oranges",
        residue="sweet stickiness",
        allowed_places={"museum", "clubhouse"},
        safe_for_paper=False,
        tags={"juice", "spill"},
    ),
    "ink_wash": Liquid(
        id="ink_wash",
        label="inky rinse water",
        phrase="inky rinse water",
        color="blue-black",
        smell="ink",
        residue="smudgy water",
        allowed_places={"library", "museum"},
        safe_for_paper=False,
        tags={"ink", "spill"},
    ),
    "sparkle_water": Liquid(
        id="sparkle_water",
        label="sparkle water",
        phrase="sparkle water",
        color="clear",
        smell="almost nothing",
        residue="hardly any mark",
        allowed_places={"library", "museum", "clubhouse"},
        safe_for_paper=True,
        tags={"water"},
    ),
}

PAPERS = {
    "guestbook": Paper(
        id="guestbook",
        label="the guestbook page",
        phrase="the guestbook page where visitors had signed their names",
        purpose="the names of today's visitors",
        absorbent=True,
        fragile=True,
        protected=False,
        tags={"paper", "guestbook"},
    ),
    "treasure_map": Paper(
        id="treasure_map",
        label="the treasure map",
        phrase="the treasure map with three red X marks and a folded corner",
        purpose="the club's hidden-snack map",
        absorbent=True,
        fragile=True,
        protected=False,
        tags={"paper", "map"},
    ),
    "label_card": Paper(
        id="label_card",
        label="the exhibit label",
        phrase="the exhibit label card written in tiny careful letters",
        purpose="the shell exhibit's name card",
        absorbent=True,
        fragile=True,
        protected=False,
        tags={"paper", "museum"},
    ),
    "wax_card": Paper(
        id="wax_card",
        label="the waxy clue card",
        phrase="the waxy clue card with a shiny coat",
        purpose="the clue written in grease pencil",
        absorbent=False,
        fragile=False,
        protected=True,
        tags={"paper"},
    ),
}

ROLES = {
    "sketcher": SuspectRole(
        id="sketcher",
        label="sketcher",
        habit="liked leaning over the table to draw every detail",
        excuse="I was only looking closely.",
        movement="with a notebook under one arm",
        tags={"drawing"},
    ),
    "helper": SuspectRole(
        id="helper",
        label="helper",
        habit="liked carrying supplies even when nobody asked",
        excuse="I was trying to be useful.",
        movement="with pockets full of string and clips",
        tags={"helping"},
    ),
    "reader": SuspectRole(
        id="reader",
        label="reader",
        habit="liked whisper-reading every sign aloud",
        excuse="I was just sounding out the words.",
        movement="with eyebrows scrunched in thought",
        tags={"reading"},
    ),
}

GIRL_NAMES = ["Nora", "Ivy", "Tess", "Mia", "Lila", "Ruby"]
BOY_NAMES = ["Milo", "Owen", "Ben", "Leo", "Finn", "Sam"]


@dataclass
class StoryParams:
    place: str
    liquid: str
    paper: str
    detective_name: str
    detective_gender: str
    keeper_name: str
    suspect_a: str
    suspect_b: str
    suspect_c: str
    role_a: str
    role_b: str
    role_c: str
    culprit_index: int
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    liquid = f["liquid_cfg"]
    paper = f["paper_cfg"]
    place = f["place"]
    return [
        f'Write a cozy child-friendly whodunit with inner monologue set in {place.label} that includes the words "clause" and "gush".',
        f"Tell a short mystery where {detective.id} studies a spill on {paper.label} and quietly reasons out that {culprit.id} did it.",
        f"Write a simple detective story for young readers about {liquid.label} ruining an important paper, with the clue solved by careful thinking instead of shouting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    keeper = f["keeper"]
    culprit = f["culprit"]
    liquid = f["liquid_cfg"]
    paper = f["paper_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child who likes puzzles, and the small group in {place.label}. "
            f"The mystery matters because {paper.label} held {paper.purpose}.",
        ),
        (
            f"What went wrong at the beginning of the mystery?",
            f"A gush of {liquid.phrase} splashed onto {paper.label} and smeared it. "
            f"That turned an ordinary quiet room into a little whodunit.",
        ),
        (
            f"What was the careful clause on the rule sign?",
            f'The sign said, "{place.rule_clause}" That clause mattered because the spill broke exactly the rule meant to protect the paper.',
        ),
        (
            f"How did {detective.id} use inner monologue to solve the case?",
            f"{detective.id} told {detective.pronoun('object')}self not to guess and listed the clues in {detective.pronoun('possessive')} head: the stain color, the smell, and the sticky residue. "
            f"Thinking quietly helped {detective.pronoun('object')} match the spill to the right suspect instead of blaming someone at random.",
        ),
        (
            f"Why did {detective.id} decide that {culprit.id} was the culprit?",
            f"{culprit.id} still had {liquid.color} spots and smelled like {liquid.smell}, which matched the stain on the paper. "
            f"The same spill that soaked the clue also marked the one who made it.",
        ),
        (
            f"How did the story end?",
            f"{keeper.label_word.capitalize()} copied the blurred writing onto fresh paper, and {culprit.id} helped fix the problem. "
            f"The ending shows that the truth made the room calmer and kinder, not meaner.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "paper": [
        (
            "Why does paper wrinkle when it gets wet?",
            "Paper is made from tiny fibers. When water soaks into them, they swell and dry unevenly, so the paper curls and wrinkles.",
        )
    ],
    "spill": [
        (
            "What is a spill?",
            "A spill is when a drink or other liquid tips out where it does not belong. It can spread fast and make a mess.",
        )
    ],
    "juice": [
        (
            "Why can juice leave sticky marks?",
            "Juice has sugar and color in it. When it dries, some of that stays behind as a sticky, colored residue.",
        )
    ],
    "ink": [
        (
            "Why does ink smudge paper so easily?",
            "Ink is made to spread color onto surfaces. On paper, it can soak in quickly and blur the writing.",
        )
    ],
    "rules": [
        (
            "What is a clause in a rule?",
            "A clause is one careful part of a sentence that adds an important detail. In a rule, it can explain exactly what people should or should not do.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues and uses them to figure out what happened. Good detectives think carefully before they decide.",
        )
    ],
    "inner_monologue": [
        (
            "What is inner monologue?",
            "Inner monologue is the voice of a person's thoughts inside their head. In a mystery, it can show how the detective reasons through the clues.",
        )
    ],
}
KNOWLEDGE_ORDER = ["paper", "spill", "juice", "ink", "rules", "detective", "inner_monologue"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"paper", "spill", "rules", "detective", "inner_monologue"}
    liquid = f["liquid_cfg"]
    if "juice" in liquid.tags:
        tags.add("juice")
    if "ink" in liquid.tags:
        tags.add("ink")
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="library",
        liquid="berry_juice",
        paper="guestbook",
        detective_name="Nora",
        detective_gender="girl",
        keeper_name="Ms. Bell",
        suspect_a="Milo",
        suspect_b="Tess",
        suspect_c="Ivy",
        role_a="sketcher",
        role_b="helper",
        role_c="reader",
        culprit_index=0,
        seed=1,
    ),
    StoryParams(
        place="museum",
        liquid="ink_wash",
        paper="label_card",
        detective_name="Owen",
        detective_gender="boy",
        keeper_name="Mr. Dale",
        suspect_a="Ruby",
        suspect_b="Ben",
        suspect_c="Lila",
        role_a="helper",
        role_b="reader",
        role_c="sketcher",
        culprit_index=2,
        seed=2,
    ),
    StoryParams(
        place="clubhouse",
        liquid="orange_drink",
        paper="treasure_map",
        detective_name="Mia",
        detective_gender="girl",
        keeper_name="Coach Ana",
        suspect_a="Finn",
        suspect_b="Ivy",
        suspect_c="Sam",
        role_a="reader",
        role_b="sketcher",
        role_c="helper",
        culprit_index=1,
        seed=3,
    ),
]


ASP_RULES = r"""
valid(Place, Liquid, Paper) :-
    place(Place), liquid(Liquid), paper(Paper),
    allowed(Liquid, Place), absorbent(Paper), not safe_for_paper(Liquid).

culprit_name(A) :- culprit_index(0), suspect_slot(a, A).
culprit_name(B) :- culprit_index(1), suspect_slot(b, B).
culprit_name(C) :- culprit_index(2), suspect_slot(c, C).

signature(Color, Smell, Residue) :-
    chosen_liquid(Liquid), liquid_color(Liquid, Color), liquid_smell(Liquid, Smell), liquid_residue(Liquid, Residue).

paper_ruined :- chosen_paper(P), absorbent(P), chosen_liquid(L), not safe_for_paper(L).
culprit_marked :- paper_ruined.
solvable :- paper_ruined, culprit_marked.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for liquid_id, liquid in LIQUIDS.items():
        lines.append(asp.fact("liquid", liquid_id))
        for place_id in sorted(liquid.allowed_places):
            lines.append(asp.fact("allowed", liquid_id, place_id))
        lines.append(asp.fact("liquid_color", liquid_id, liquid.color))
        lines.append(asp.fact("liquid_smell", liquid_id, liquid.smell))
        lines.append(asp.fact("liquid_residue", liquid_id, liquid.residue))
        if liquid.safe_for_paper:
            lines.append(asp.fact("safe_for_paper", liquid_id))
    for paper_id, paper in PAPERS.items():
        lines.append(asp.fact("paper", paper_id))
        if paper.absorbent:
            lines.append(asp.fact("absorbent", paper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_signature_and_solvable(params: StoryParams) -> tuple[str, bool]:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_liquid", params.liquid),
            asp.fact("chosen_paper", params.paper),
            asp.fact("culprit_index", params.culprit_index),
            asp.fact("suspect_slot", "a", params.suspect_a),
            asp.fact("suspect_slot", "b", params.suspect_b),
            asp.fact("suspect_slot", "c", params.suspect_c),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show signature/3.\n#show solvable/0."))
    sig_atoms = asp.atoms(model, "signature")
    solvable = bool(asp.atoms(model, "solvable"))
    if sig_atoms:
        color, smell, residue = sig_atoms[0]
        return f"{color}|{smell}|{residue}", solvable
    return "", solvable


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cozy child whodunit with inner monologue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--liquid", choices=LIQUIDS)
    ap.add_argument("--paper", choices=PAPERS)
    ap.add_argument("--culprit-index", type=int, choices=[0, 1, 2])
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper-name")
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


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.liquid and args.paper:
        place = PLACES[args.place]
        liquid = LIQUIDS[args.liquid]
        paper = PAPERS[args.paper]
        if not valid_combo(place, liquid, paper):
            raise StoryError(explain_rejection(place, liquid, paper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.liquid is None or combo[1] == args.liquid)
        and (args.paper is None or combo[2] == args.paper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, liquid_id, paper_id = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender, set())
    keeper_name = args.keeper_name or rng.choice(["Ms. Bell", "Mr. Dale", "Coach Ana", "Aunt June"])
    all_names = GIRL_NAMES + BOY_NAMES
    suspects = rng.sample([n for n in all_names if n != detective_name], 3)
    roles = rng.sample(sorted(ROLES.keys()), 3)
    culprit_index = args.culprit_index if args.culprit_index is not None else rng.choice([0, 1, 2])

    return StoryParams(
        place=place_id,
        liquid=liquid_id,
        paper=paper_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        keeper_name=keeper_name,
        suspect_a=suspects[0],
        suspect_b=suspects[1],
        suspect_c=suspects[2],
        role_a=roles[0],
        role_b=roles[1],
        role_c=roles[2],
        culprit_index=culprit_index,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        liquid = LIQUIDS[params.liquid]
        paper = PAPERS[params.paper]
        roles = [params.role_a, params.role_b, params.role_c]
        for role_id in roles:
            if role_id not in ROLES:
                raise StoryError(f"(Invalid role: {role_id})")
        if params.culprit_index not in (0, 1, 2):
            raise StoryError("(Invalid culprit index: must be 0, 1, or 2.)")
        if not valid_combo(place, liquid, paper):
            raise StoryError(explain_rejection(place, liquid, paper))
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from exc

    world = tell(
        place=place,
        liquid=liquid,
        paper_cfg=paper,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        keeper_name=params.keeper_name,
        suspect_names=[params.suspect_a, params.suspect_b, params.suspect_c],
        culprit_index=params.culprit_index,
        role_ids=roles,
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


def asp_verify() -> int:
    rc = 0
    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: ASP gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))

    cases = list(CURATED)
    for seed in range(10):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    for params in cases:
        py_sig = culprit_signature(LIQUIDS[params.liquid])
        asp_sig, solvable = asp_signature_and_solvable(params)
        if py_sig != asp_sig or not solvable:
            rc = 1
            print(f"MISMATCH in scenario signature/solvable for seed={params.seed} params={params}")
            break

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show signature/3.\n#show solvable/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, liquid, paper) combos:\n")
        for place, liquid, paper in combos:
            print(f"  {place:10} {liquid:12} {paper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            culprit_name = [p.suspect_a, p.suspect_b, p.suspect_c][p.culprit_index]
            header = f"### {p.place}: {p.paper} ruined by {p.liquid} (culprit: {culprit_name})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
