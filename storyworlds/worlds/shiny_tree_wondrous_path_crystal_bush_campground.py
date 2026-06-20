#!/usr/bin/env python3
"""
storyworlds/worlds/shiny_tree_wondrous_path_crystal_bush_campground.py
========================================================================

A standalone storyworld for a seed prompt:

    Words: shiny tree, wondrous path, crystal bush
    Setting: campground
    Features: Problem Solving, Reconciliation
    Style: Slice of Life

Internal source tale:
    Two campers are getting the campground's morning welcome walk ready.
    The shiny tree is the meeting place, the wondrous path leads to cocoa by
    the crystal bush, and a small trail marker setup goes wrong. One child
    blames the other too quickly because of a clue that seems to fit. They
    inspect the path together, find the real cause, use the right camp gear to
    fix it, and make peace before the younger campers arrive.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Campground:
    id: str
    name: str
    tree_detail: str
    path_detail: str
    bush_detail: str
    drink: str
    helper_title: str
    ending_sound: str


@dataclass
class Clue:
    id: str
    mark: str
    worn: str
    clue: str
    accusation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    mark: str
    need: str
    event: str
    discovery: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    need: str
    gear: str
    action: str
    qa: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, campground: Campground) -> None:
        self.campground = campground
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.history: list[tuple[str, str]] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def note(self, tag: str, detail: str) -> None:
        self.history.append((tag, detail))

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.campground)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_quarrel_slows_setup(world: World) -> list[str]:
    accuser = world.get("accuser")
    suspect = world.get("suspect")
    setup = world.get("trail_setup")
    if accuser.memes["blaming"] < THRESHOLD or suspect.memes["hurt"] < THRESHOLD:
        return []
    sig = ("quarrel", accuser.id, suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accuser.memes["conflict"] += 1
    suspect.memes["conflict"] += 1
    setup.meters["delay"] += 1
    world.note("quarrel", f"{accuser.id} blamed {suspect.id} before checking the path.")
    return []


def _r_shared_work_steadies_path(world: World) -> list[str]:
    accuser = world.get("accuser")
    suspect = world.get("suspect")
    setup = world.get("trail_setup")
    if accuser.memes["working_together"] < THRESHOLD or suspect.memes["working_together"] < THRESHOLD:
        return []
    if setup.meters["fixed"] < THRESHOLD:
        return []
    sig = ("steady_path", setup.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    setup.meters["ready"] += 1
    setup.meters["delay"] = 0.0
    accuser.memes["calm"] += 1
    suspect.memes["calm"] += 1
    world.note("ready", "The welcome walk was steady again once both campers worked together.")
    return [
        "With both sets of hands on the camp gear, the welcome markers sat straight again."
    ]


def _r_reconciliation(world: World) -> list[str]:
    accuser = world.get("accuser")
    suspect = world.get("suspect")
    setup = world.get("trail_setup")
    if accuser.memes["apology"] < THRESHOLD or setup.meters["ready"] < THRESHOLD:
        return []
    sig = ("reconciled", accuser.id, suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accuser.memes["conflict"] = 0.0
    suspect.memes["conflict"] = 0.0
    accuser.memes["trust"] += 1
    suspect.memes["trust"] += 1
    setup.meters["warm"] += 1
    world.note("reconciliation", f"{accuser.id} apologized and {suspect.id} accepted.")
    return []


CAUSAL_RULES = [
    Rule("quarrel_slows_setup", "social", _r_quarrel_slows_setup),
    Rule("shared_work_steadies_path", "repair", _r_shared_work_steadies_path),
    Rule("reconciliation", "social", _r_reconciliation),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def clue_can_mislead(clue: Clue, cause: Cause) -> bool:
    return clue.mark == cause.mark


def fix_fits(cause: Cause, fix: Fix) -> bool:
    return cause.need == fix.need


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for camp_id in CAMPGROUNDS:
        for clue_id, clue in CLUES.items():
            for cause_id, cause in CAUSES.items():
                for fix_id, fix in FIXES.items():
                    if clue_can_mislead(clue, cause) and fix_fits(cause, fix):
                        out.append((camp_id, clue_id, cause_id, fix_id))
    return out


def predict_delay(world: World) -> dict[str, float]:
    sim = world.copy()
    sim.get("accuser").memes["blaming"] += 1
    sim.get("suspect").memes["hurt"] += 1
    propagate(sim, narrate=False)
    return {
        "delay": sim.get("trail_setup").meters["delay"],
        "conflict": sim.get("accuser").memes["conflict"],
    }


def introduce(world: World, accuser: Entity, suspect: Entity, helper: Entity, clue: Clue) -> None:
    camp = world.campground
    accuser.memes["care"] += 1
    suspect.memes["care"] += 1
    world.note("premise", f"{accuser.id} and {suspect.id} prepared the campground welcome walk.")
    world.say(
        f"At {camp.name}, {accuser.id} and {suspect.id} liked morning chores because they got to work under the shiny tree."
    )
    world.say(
        f"The shiny tree stood by the campground circle, and {camp.tree_detail}."
    )
    world.say(
        f"From there, the wondrous path curled past the tents toward the creek, and {camp.path_detail}."
    )
    world.say(
        f"At the bend grew the crystal bush, where {camp.bush_detail}. {helper.id}, the {camp.helper_title}, asked the two friends to mark the path for breakfast {camp.drink}."
    )
    world.say(
        f"{suspect.id} wore {clue.worn}, and both campers carried a small bag of trail supplies."
    )


def set_task(world: World) -> None:
    world.get("trail_setup").meters["planned"] += 1
    world.say(
        "They stretched a welcome line from the shiny tree toward the crystal bush so the younger campers could follow it after they woke up."
    )
    world.note("goal", "The campers wanted the welcome walk ready before breakfast.")


def discover_problem(world: World, accuser: Entity, clue: Clue, cause: Cause) -> None:
    setup = world.get("trail_setup")
    setup.meters["crooked"] += 1
    world.say(
        f"Just as the campground started to smell like warm {world.campground.drink}, {accuser.id} saw that the trail setup had gone crooked."
    )
    world.say(
        f"Near the first turn of the wondrous path, {accuser.id} found {clue.clue}. {cause.event}"
    )
    world.note("problem", cause.risk)


def accuse(world: World, accuser: Entity, suspect: Entity, clue: Clue) -> None:
    accuser.memes["blaming"] += 1
    suspect.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{suspect.id}, this looks like yours," {accuser.id} said. "{clue.accusation}"'
    )
    world.say(
        f"{suspect.id} folded {suspect.pronoun('possessive')} arms. \"I was helping, not ruining it,\" {suspect.pronoun()} said."
    )


def helper_warns(world: World, helper: Entity) -> None:
    pred = predict_delay(world)
    if pred["delay"] >= THRESHOLD:
        world.facts["predicted_delay"] = pred["delay"]
        world.say(
            f'{helper.id} knelt beside the shiny tree and spoke gently. "If you keep arguing, the little campers will reach the path before it is safe and clear. Check the real problem first, then decide what happened."'
        )


def investigate(world: World, accuser: Entity, suspect: Entity, cause: Cause) -> None:
    accuser.memes["curiosity"] += 1
    suspect.memes["curiosity"] += 1
    accuser.memes["working_together"] += 1
    suspect.memes["working_together"] += 1
    world.say(
        f"So the two friends walked the wondrous path side by side, looking closely at the markers, the ground, and the line by the crystal bush."
    )
    end = "" if cause.discovery.endswith((".", "!", "?")) else "."
    world.say(f"There they found the truth: {cause.discovery}{end}")
    world.note("discovery", cause.discovery)


def repair(world: World, accuser: Entity, suspect: Entity, fix: Fix) -> None:
    setup = world.get("trail_setup")
    setup.meters["fixed"] += 1
    accuser.memes["responsibility"] += 1
    suspect.memes["helping"] += 1
    world.say(
        f"{suspect.id} pulled out {fix.gear}, and {accuser.id} held the line steady. {fix.action}"
    )
    propagate(world)
    world.note("repair", fix.qa)


def apologize(world: World, accuser: Entity, suspect: Entity) -> None:
    accuser.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{accuser.id} looked down at the pebbles. "I am sorry I blamed you before we even checked," {accuser.pronoun()} said.'
    )
    world.say(
        f'{suspect.id} gave a small nod. "I am glad we fixed it together," {suspect.pronoun()} answered.'
    )


def closing(world: World, accuser: Entity, suspect: Entity, fix: Fix) -> None:
    setup = world.get("trail_setup")
    camp = world.campground
    if setup.meters["warm"] >= THRESHOLD:
        world.say(
            f"Soon the younger campers came out with sleepy smiles and tin cups in their hands. They followed the wondrous path from the shiny tree all the way to the crystal bush without any trouble."
        )
        world.say(
            f"{fix.ending_image} The campground felt easy again, and {accuser.id} and {suspect.id} stood together listening to {camp.ending_sound}."
        )
        world.note("ending", "The repaired path and apology changed the morning for the whole campground.")


def tell(
    campground: Campground,
    clue: Clue,
    cause: Cause,
    fix: Fix,
    accuser_name: str = "Mina",
    accuser_gender: str = "girl",
    suspect_name: str = "Theo",
    suspect_gender: str = "boy",
    helper_name: str = "Ranger Bea",
    helper_gender: str = "woman",
    trait: str = "careful",
) -> World:
    world = World(campground)
    accuser = world.add(
        Entity(
            id=accuser_name,
            kind="character",
            type=accuser_gender,
            label=accuser_name,
            role="accuser",
            traits=[trait],
        )
    )
    suspect = world.add(
        Entity(
            id=suspect_name,
            kind="character",
            type=suspect_gender,
            label=suspect_name,
            role="suspect",
            traits=["steady"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
        )
    )
    world.add(Entity("trail_setup", type="camp_marker", label="welcome line"))

    introduce(world, accuser, suspect, helper, clue)
    set_task(world)

    world.para()
    discover_problem(world, accuser, clue, cause)
    accuse(world, accuser, suspect, clue)
    helper_warns(world, helper)

    world.para()
    investigate(world, accuser, suspect, cause)
    repair(world, accuser, suspect, fix)
    apologize(world, accuser, suspect)
    closing(world, accuser, suspect, fix)

    world.facts.update(
        accuser=accuser,
        suspect=suspect,
        helper=helper,
        campground=campground,
        clue=clue,
        cause=cause,
        fix=fix,
        trail_setup=world.get("trail_setup"),
        reconciled=world.get("trail_setup").meters["warm"] >= THRESHOLD,
        ready=world.get("trail_setup").meters["ready"] >= THRESHOLD,
    )
    return world


CAMPGROUNDS = {
    "fern_loop": Campground(
        "fern_loop",
        "Fern Loop Campground",
        "its pale bark caught the first sunlight and made the trunk look brushed with silver",
        "flat stones made it feel like a tiny parade route through the grass",
        "clear seed pods clicked together like little cups whenever the breeze moved",
        "cocoa",
        "camp host",
        "spoons clinking against warm mugs",
    ),
    "pine_ridge": Campground(
        "pine_ridge",
        "Pine Ridge Campground",
        "the bark shone after every cool night, so the children always called it the shiny tree",
        "its pebbles glimmered after the dew and made ordinary chores feel special",
        "its glassy leaves held drops of water that flashed like marbles",
        "apple cider",
        "trail ranger",
        "camp chairs scraping softly over packed dirt",
    ),
    "creek_rest": Campground(
        "creek_rest",
        "Creek Rest Campground",
        "a smooth ribbon of light ran down one side of the trunk each morning",
        "it curved between the tents so neatly that every child in camp called it the wondrous path",
        "its dry pods tapped together like tiny bells when the creek wind reached them",
        "mint tea",
        "morning leader",
        "quiet laughter near the picnic tables",
    ),
}

CLUES = {
    "blue_ribbon": Clue(
        "blue_ribbon",
        "blue_ribbon",
        "a blue headband with ribbon tails",
        "a damp blue ribbon strip on the path",
        "You must have pulled the welcome line loose while your headband brushed it.",
        tags={"clue", "ribbon"},
    ),
    "tent_peg": Clue(
        "tent_peg",
        "tent_peg",
        "a tin bracelet looped with spare tent pegs",
        "one shiny tent peg tipped on its side",
        "You must have bumped the trail marker when you were moving pegs around.",
        tags={"clue", "peg"},
    ),
    "twine_loop": Clue(
        "twine_loop",
        "twine_loop",
        "a braided twine bracelet from crafts hour",
        "a curled loop of twine caught in the grass",
        "You must have tied the path line in a hurry and left it that way.",
        tags={"clue", "twine"},
    ),
}

CAUSES = {
    "dew_slip": Cause(
        "dew_slip",
        "blue_ribbon",
        "clip",
        "A cold drop slid from the line and landed on the toe of a boot.",
        "the blue ribbon at the first turn had grown slick with dew and slipped halfway through its knot beside the crystal bush",
        "the younger campers would follow a sagging line and miss the breakfast stop",
        tags={"dew", "ribbon", "problem_solving"},
    ),
    "soft_ground": Cause(
        "soft_ground",
        "tent_peg",
        "brace",
        "The dirt by the path sign was darker than the rest, as if it had been watered in the night.",
        "the ground near the sign had softened, and one tent peg had worked loose until the arrow leaned toward the ferns",
        "the path marker could topple before the small children reached the turn",
        tags={"ground", "peg", "problem_solving"},
    ),
    "wind_snag": Cause(
        "wind_snag",
        "twine_loop",
        "retie",
        "A thin line trembled every time the breeze came down from the creek.",
        "the guide twine had wrapped around a low branch of the crystal bush when the wind turned it in the night",
        "the path line would keep twisting until someone set it shorter and straighter",
        tags={"wind", "twine", "problem_solving"},
    ),
}

FIXES = {
    "clothespins": Fix(
        "clothespins",
        "clip",
        "two wooden clothespins from the drying line",
        "Together they clipped the wet ribbon flat against the marker string and pulled the knot snug again.",
        "used wooden clothespins to hold the damp ribbon in place while they tightened the knot",
        "By the time the first mugs were poured, the blue line ran neat and bright from the shiny tree toward the crystal bush.",
        tags={"ribbon", "tool"},
    ),
    "stone_brace": Fix(
        "stone_brace",
        "brace",
        "a pair of spare pegs and a flat creek stone",
        "They pushed the loose peg back in, packed the earth around it, and braced the sign with the stone until it stood firm.",
        "used spare pegs and a flat stone to brace the leaning marker",
        "When the breakfast bell rang, the arrow by the wondrous path stood straight and easy to read.",
        tags={"peg", "tool"},
    ),
    "short_retie": Fix(
        "short_retie",
        "retie",
        "a safety pin and a short length of fresh twine",
        "They eased the old loop free from the branch, shortened the line, and tied it again with a clean square knot.",
        "freed the snagged twine and retied the path line shorter so the wind could not catch it again",
        "A neat line lifted over the path, and the crystal bush no longer tugged at it when the breeze passed.",
        tags={"twine", "tool"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "June", "Nora", "Evie", "Ruth"]
BOY_NAMES = ["Theo", "Milo", "Ben", "Owen", "Cal", "Jude"]
TRAITS = ["careful", "helpful", "curious", "earnest", "practical", "gentle"]


@dataclass
class StoryParams:
    campground: str
    clue: str
    cause: str
    fix: str
    accuser: str
    accuser_gender: str
    suspect: str
    suspect_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "campground": [
        (
            "What is a campground?",
            "A campground is a place where people stay outdoors in tents or cabins. They usually share paths, fire circles, and places to eat.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. A clue can point in the right direction, but it does not always tell the whole story.",
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people make peace after a hurt or disagreement. They listen, repair the problem, and decide to be close again.",
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means looking carefully at what went wrong and choosing steps that actually fix it. It often works better when people share ideas and tools.",
        )
    ],
    "dew": [
        (
            "Why can dew make a knot slip?",
            "Dew makes cloth and rope wet. A wet knot can loosen more easily than a dry one.",
        )
    ],
    "peg": [
        (
            "What does a tent peg do?",
            "A tent peg holds something steady in the ground. Campers use pegs for tents, lines, and small signs.",
        )
    ],
    "ground": [
        (
            "Why can soft ground be a problem at camp?",
            "Soft ground does not hold stakes very well. A sign or line can lean if the dirt loosens around it.",
        )
    ],
    "twine": [
        (
            "What is twine?",
            "Twine is a thin string used for tying things together. It can catch on branches if it is left too loose.",
        )
    ],
    "wind": [
        (
            "How can wind change something that was tied up outside?",
            "Wind keeps pulling on the same place again and again. If a line is loose, the breeze can twist it into a branch or knot.",
        )
    ],
    "ribbon": [
        (
            "Why do camps use ribbons or markers on a path?",
            "Markers help people know where to walk. They are especially useful for younger children who are still learning the campsite.",
        )
    ],
    "tool": [
        (
            "Why do the right tools matter when fixing a problem?",
            "The right tool matches the real problem. A careful fix lasts longer and keeps other people safer.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "campground",
    "clue",
    "reconciliation",
    "problem_solving",
    "dew",
    "peg",
    "ground",
    "twine",
    "wind",
    "ribbon",
    "tool",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["accuser"]
    b = f["suspect"]
    camp = f["campground"]
    return [
        'Write a slice-of-life campground story for young children that includes the phrases "shiny tree," "wondrous path," and "crystal bush," and uses problem solving plus reconciliation.',
        f"Tell a gentle camp story at {camp.name} where {a.id} blames {b.id} for a broken trail setup, then learns the real cause and apologizes.",
        "Write about two campers getting a morning path ready for younger children, fixing the problem with camp gear, and ending with everyone walking together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["accuser"]
    b = f["suspect"]
    helper = f["helper"]
    cause = f["cause"]
    clue = f["clue"]
    fix = f["fix"]
    camp = f["campground"]
    return [
        (
            "Where does the story happen?",
            f"It happens at {camp.name}. The campers begin under the shiny tree and work along the wondrous path to the crystal bush.",
        ),
        (
            f"Why did {a.id} blame {b.id} at first?",
            f"{a.id} found {clue.clue}, and it seemed to match what {b.id} was wearing: {clue.worn}. That clue felt convincing at first, but it did not explain the whole problem.",
        ),
        (
            "What was the real problem on the path?",
            f"The real problem was that {cause.discovery}. That made the trail setup unsafe or confusing for the younger campers.",
        ),
        (
            "How did the friends solve the problem?",
            f"They {fix.qa}. The fix worked because it matched what had actually gone wrong on the path.",
        ),
        (
            f"How did {helper.id} help without doing the work for them?",
            f"{helper.id} reminded the children to check the real problem before deciding who was at fault. That gentle warning pushed them to investigate together instead of staying angry.",
        ),
        (
            "How did the story end?",
            f"The path was ready again, and the two friends reconciled after the apology. The younger campers could follow the markers from the shiny tree to the crystal bush for breakfast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {
        "campground",
        "clue",
        "reconciliation",
    } | set(world.facts["cause"].tags) | set(world.facts["fix"].tags) | set(world.facts["clue"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    seen: set[int] = set()
    for ent in world.entities.values():
        if id(ent) in seen:
            continue
        seen.add(id(ent))
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    if world.history:
        lines.append("  history:")
        for tag, detail in world.history:
            lines.append(f"    - {tag}: {detail}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        "fern_loop",
        "blue_ribbon",
        "dew_slip",
        "clothespins",
        "Mina",
        "girl",
        "Theo",
        "boy",
        "Ranger Bea",
        "woman",
        "careful",
    ),
    StoryParams(
        "pine_ridge",
        "tent_peg",
        "soft_ground",
        "stone_brace",
        "Owen",
        "boy",
        "Lila",
        "girl",
        "Ranger Sol",
        "man",
        "practical",
    ),
    StoryParams(
        "creek_rest",
        "twine_loop",
        "wind_snag",
        "short_retie",
        "June",
        "girl",
        "Milo",
        "boy",
        "Leader Ana",
        "woman",
        "gentle",
    ),
]


def explain_rejection(clue: Clue, cause: Cause, fix: Fix) -> str:
    if not clue_can_mislead(clue, cause):
        return (
            f"(No story: {clue.clue} points to the mark '{clue.mark}', but the true cause uses '{cause.mark}'. "
            "The misunderstanding would not feel fair.)"
        )
    return (
        f"(No story: {cause.id} needs a fix for '{cause.need}', but '{fix.id}' solves '{fix.need}'. "
        "The repair has to match the real campsite problem.)"
    )


ASP_RULES = r"""
ambiguous(Clue, Cause) :- clue(Clue), cause(Cause), clue_mark(Clue, M), cause_mark(Cause, M).
effective(Cause, Fix) :- cause(Cause), fix(Fix), cause_need(Cause, N), fix_need(Fix, N).
valid(Camp, Clue, Cause, Fix) :- campground(Camp), ambiguous(Clue, Cause), effective(Cause, Fix).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for camp_id in CAMPGROUNDS:
        lines.append(asp.fact("campground", camp_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_mark", clue_id, clue.mark))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_mark", cause_id, cause.mark))
        lines.append(asp.fact("cause_need", cause_id, cause.need))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_need", fix_id, fix.need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def _exercise_samples() -> None:
    for idx, params in enumerate(CURATED):
        seeded = StoryParams(**vars(params))
        seeded.seed = 1000 + idx
        sample = generate(seeded)
        lower_story = sample.story.lower()
        for needle in ("shiny tree", "wondrous path", "crystal bush"):
            if needle not in lower_story:
                raise StoryError(f"Verification sample missing required phrase: {needle}")
        if not sample.story_qa or not sample.world_qa or not sample.prompts:
            raise StoryError("Verification sample is missing one of the required QA or prompt sets.")
        if not sample.world.facts["ready"] or not sample.world.facts["reconciled"]:
            raise StoryError("Verification sample failed to reach a repaired and reconciled ending.")


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1
    try:
        _exercise_samples()
    except StoryError as err:
        print(f"VERIFY FAILED: {err}")
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    print("OK: curated samples render required landmarks, QA sets, and repaired endings.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: campground morning path, problem solving, reconciliation. Unspecified choices are randomized."
    )
    ap.add_argument("--campground", choices=CAMPGROUNDS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--accuser")
    ap.add_argument("--accuser-gender", choices=["girl", "boy"])
    ap.add_argument("--suspect")
    ap.add_argument("--suspect-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.cause and args.fix:
        clue = CLUES[args.clue]
        cause = CAUSES[args.cause]
        fix = FIXES[args.fix]
        if not (clue_can_mislead(clue, cause) and fix_fits(cause, fix)):
            raise StoryError(explain_rejection(clue, cause, fix))
    if args.clue and args.cause and not clue_can_mislead(CLUES[args.clue], CAUSES[args.cause]):
        raise StoryError(explain_rejection(CLUES[args.clue], CAUSES[args.cause], next(iter(FIXES.values()))))
    if args.cause and args.fix and not fix_fits(CAUSES[args.cause], FIXES[args.fix]):
        clue = CLUES[args.clue] if args.clue else next(c for c in CLUES.values() if c.mark == CAUSES[args.cause].mark)
        raise StoryError(explain_rejection(clue, CAUSES[args.cause], FIXES[args.fix]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.campground is None or combo[0] == args.campground)
        and (args.clue is None or combo[1] == args.clue)
        and (args.cause is None or combo[2] == args.cause)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    campground, clue, cause, fix = rng.choice(sorted(combos))
    accuser_gender = args.accuser_gender or rng.choice(["girl", "boy"])
    suspect_gender = args.suspect_gender or rng.choice(["girl", "boy"])
    accuser = args.accuser or _pick_name(rng, accuser_gender)
    suspect = args.suspect or _pick_name(rng, suspect_gender, avoid=accuser)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or ("Ranger Bea" if helper_gender == "woman" else "Ranger Sol")
    return StoryParams(
        campground,
        clue,
        cause,
        fix,
        accuser,
        accuser_gender,
        suspect,
        suspect_gender,
        helper,
        helper_gender,
        rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CAMPGROUNDS[params.campground],
        CLUES[params.clue],
        CAUSES[params.cause],
        FIXES[params.fix],
        params.accuser,
        params.accuser_gender,
        params.suspect,
        params.suspect_gender,
        params.helper,
        params.helper_gender,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(f"{len(combos)} compatible (campground, clue, cause, fix) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.accuser} and {p.suspect}: {p.clue} / {p.cause}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
