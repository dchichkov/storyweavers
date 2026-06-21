#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rail_sticky_branch_suspense_transformation_quest_whodunit.py
=========================================================================================

A standalone storyworld for a small whodunit-shaped quest: a child detective
finds a toy train stopped at a branch in the garden track because one rail has
turned sticky. The mystery feels suspenseful, but the solution is gentle: the
"culprit" is someone who left a sweet, sticky trace by accident. The quest is
to follow clues, test suspects, and fix the track so the train can run again.

The world model is deliberately small and classical:
- typed entities with physical meters and emotional memes
- a tiny causal engine
- a reasonableness gate over valid mystery combinations
- a declarative ASP twin for the same gate and outcome logic

Run it
------
    python storyworlds/worlds/gpt-5.4/rail_sticky_branch_suspense_transformation_quest_whodunit.py
    python storyworlds/worlds/gpt-5.4/rail_sticky_branch_suspense_transformation_quest_whodunit.py --culprit sibling --residue jam
    python storyworlds/worlds/gpt-5.4/rail_sticky_branch_suspense_transformation_quest_whodunit.py --culprit bird --residue mud
    python storyworlds/worlds/gpt-5.4/rail_sticky_branch_suspense_transformation_quest_whodunit.py --all --qa
    python storyworlds/worlds/gpt-5.4/rail_sticky_branch_suspense_transformation_quest_whodunit.py --verify
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
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        neutral_person = {"child", "friend", "sibling"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral_person:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    hiding_spot: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    type: str
    motive: str
    trail: str
    accidental: bool
    can_carry_food: bool
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Residue:
    id: str
    label: str
    sticky: bool
    edible: bool
    clue: str
    smear: str
    clean_with: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    action: str
    works_on: set[str]
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class BranchSpot:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stall(world: World) -> list[str]:
    train = world.get("train")
    rail = world.get("rail")
    out: list[str] = []
    if rail.meters["sticky"] >= THRESHOLD and train.meters["rolling"] >= THRESHOLD:
        sig = ("stall",)
        if sig not in world.fired:
            world.fired.add(sig)
            train.meters["stalled"] += 1
            train.meters["rolling"] = 0.0
            world.get("detective").memes["worry"] += 1
            out.append("__stall__")
    return out


def _r_clue(world: World) -> list[str]:
    culprit = world.get("culprit")
    residue = world.get("residue")
    if culprit.meters["passed_branch"] >= THRESHOLD and residue.meters["smeared"] >= THRESHOLD:
        sig = ("clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("detective").memes["curiosity"] += 1
            return ["__clue__"]
    return []


CAUSAL_RULES = [
    Rule(name="stall", tag="physical", apply=_r_stall),
    Rule(name="clue", tag="mystery", apply=_r_clue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for item in produced:
            if item == "__stall__":
                world.say("The little train gave a tiny jerk, then stopped with one wheel clicking in place.")
            elif item == "__clue__":
                world.say("That meant the mess was not magic at all. Someone had passed this way and left a clue behind.")
    return produced


def hazard_exists(culprit: Culprit, residue: Residue) -> bool:
    return residue.sticky and (culprit.can_carry_food or not residue.edible)


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def tool_can_fix(tool: Tool, residue: Residue) -> bool:
    return residue.id in tool.works_on and tool.sense >= SENSE_MIN


def outcome_of(params: "StoryParams") -> str:
    culprit = CULPRITS[params.culprit]
    residue = RESIDUES[params.residue]
    tool = TOOLS[params.tool]
    if not hazard_exists(culprit, residue):
        return "?"
    solved = tool_can_fix(tool, residue)
    return "solved" if solved else "stuck"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for culprit_id, culprit in CULPRITS.items():
            for residue_id, residue in RESIDUES.items():
                if hazard_exists(culprit, residue):
                    combos.append((setting_id, culprit_id, residue_id))
    return combos


def predict_stall(world: World) -> dict:
    sim = world.copy()
    sim.get("train").meters["rolling"] += 1
    propagate(sim, narrate=False)
    return {
        "stalled": sim.get("train").meters["stalled"] >= THRESHOLD,
        "sticky": sim.get("rail").meters["sticky"] >= THRESHOLD,
    }


def introduce(world: World, detective: Entity, helper: Entity, setting: Setting) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After breakfast, {detective.id} carried a little red train into {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f"{helper.id} came too, and together they pushed the train around the loop "
        f"until it hummed softly over each rail."
    )


def branch_setup(world: World, branch: BranchSpot) -> None:
    world.say(
        f"At one side of the track was {branch.phrase}. It was the sort of place where a mystery might hide."
    )


def stall_discovery(world: World, detective: Entity, branch: BranchSpot) -> None:
    world.get("train").meters["rolling"] += 1
    propagate(world, narrate=True)
    world.say(
        f'"That is odd," {detective.id} whispered. The train had stopped right by the {branch.label}.'
    )
    world.say(
        f"{detective.id} bent close and saw that one rail looked dark and sticky in the morning light."
    )


def suspicion(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["suspense"] += 1
    helper.memes["suspense"] += 1
    world.say(
        f"Neither child touched it at first. A sticky rail in the middle of a fine train line felt like a clue from a whodunit."
    )
    world.say(
        f'"Who did it?" {helper.id} asked in a small, thrilled voice.'
    )


def inspect_clue(world: World, detective: Entity, culprit_cfg: Culprit, residue_cfg: Residue) -> None:
    culprit = world.get("culprit")
    residue = world.get("residue")
    culprit.meters["passed_branch"] += 1
    residue.meters["smeared"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{detective.id} found {residue_cfg.clue} leading away from the branch. {culprit_cfg.trail}"
    )


def question_suspects(world: World, detective: Entity, helper: Entity, culprit_cfg: Culprit) -> None:
    world.say(
        f"The two detectives set off on a short quest around {world.setting.place} to test their guesses."
    )
    if culprit_cfg.kind == "person":
        world.say(
            f"They checked the toy box, the watering can, and the snack bench before they found {culprit_cfg.label} looking surprised."
        )
    else:
        world.say(
            f"They peered under leaves, beside flower pots, and behind a stone until they spotted {culprit_cfg.label}."
        )
    world.say(
        f"At last the clues matched. {helper.id} looked at the trail again and knew they had found the true answer."
    )


def reveal(world: World, detective: Entity, helper: Entity, culprit_cfg: Culprit, residue_cfg: Residue) -> None:
    culprit = world.get("culprit")
    detective.memes["understanding"] += 1
    detective.memes["suspense"] = 0.0
    helper.memes["suspense"] = 0.0
    if culprit_cfg.kind == "person":
        world.say(
            f'"It was {culprit_cfg.label}," {detective.id} said, but not in an angry way. {culprit_cfg.label.capitalize()} had {culprit_cfg.motive}.'
        )
    else:
        world.say(
            f'"It was {culprit_cfg.label}," {detective.id} said softly. {culprit_cfg.label.capitalize()} had {culprit_cfg.motive}.'
        )
    if culprit_cfg.accidental:
        world.say(
            f"No one had tried to ruin the game. {residue_cfg.label.capitalize()} had simply been left behind by accident, and the sticky smear grabbed the train wheel."
        )
    else:
        world.say(
            f"The mess still had not been meant as meanness. It was a muddled choice, not a wicked one, and the sticky smear grabbed the train wheel."
        )
    culprit.memes["forgiven"] += 1


def clean_track(world: World, detective: Entity, helper: Entity, tool_cfg: Tool, residue_cfg: Residue) -> None:
    rail = world.get("rail")
    train = world.get("train")
    if not tool_can_fix(tool_cfg, residue_cfg):
        world.say(
            f"{detective.id} tried {tool_cfg.label}, but it only pushed the mess around. The rail stayed sticky, and the train could not move."
        )
        world.facts["solved"] = False
        return
    rail.meters["sticky"] = 0.0
    rail.meters["clean"] += 1
    train.meters["rolling"] += 1
    train.meters["stalled"] = 0.0
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'Then {helper.id} brought {tool_cfg.label}, and together they {tool_cfg.action}.'
    )
    world.say(
        f"The rail shone again. When {detective.id} set the train down, it rolled past the branch without the tiniest click."
    )
    world.facts["solved"] = True


def transformed_ending(world: World, detective: Entity, helper: Entity, culprit_cfg: Culprit) -> None:
    if world.facts.get("solved"):
        world.say(
            f"The mystery had transformed the morning. It began with suspense and whispers, but it ended with wiser eyes and a kinder heart for {culprit_cfg.label}."
        )
        world.say(
            world.setting.ending_image
        )
    else:
        world.say(
            f"The mystery was understood, even if the track was not fixed yet. {detective.id} knew the next step was to ask a grown-up for the right help."
        )


def tell(
    setting: Setting,
    culprit_cfg: Culprit,
    residue_cfg: Residue,
    tool_cfg: Tool,
    branch_cfg: BranchSpot,
    detective_name: str,
    detective_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
) -> World:
    world = World(setting=setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    culprit = world.add(Entity(id="culprit", kind="character" if culprit_cfg.kind == "person" else "thing",
                               type=culprit_cfg.type, role="culprit", label=culprit_cfg.label, tags=set(culprit_cfg.tags)))
    rail = world.add(Entity(id="rail", type="rail", label="rail"))
    train = world.add(Entity(id="train", type="train", label="train"))
    residue = world.add(Entity(id="residue", type="mess", label=residue_cfg.label, tags=set(residue_cfg.tags)))
    branch = world.add(Entity(id="branch", type="branch", label=branch_cfg.label))
    tool = world.add(Entity(id="tool", type="tool", label=tool_cfg.label, tags=set(tool_cfg.tags)))

    rail.meters["sticky"] += 1
    world.facts.update(
        detective=detective,
        helper=helper,
        parent=parent,
        culprit=culprit,
        culprit_cfg=culprit_cfg,
        residue_cfg=residue_cfg,
        tool_cfg=tool_cfg,
        branch_cfg=branch_cfg,
        setting=setting,
        predicted=predict_stall(world),
        solved=False,
    )

    introduce(world, detective, helper, setting)
    branch_setup(world, branch_cfg)

    world.para()
    stall_discovery(world, detective, branch_cfg)
    suspicion(world, detective, helper)

    world.para()
    inspect_clue(world, detective, culprit_cfg, residue_cfg)
    question_suspects(world, detective, helper, culprit_cfg)
    reveal(world, detective, helper, culprit_cfg, residue_cfg)

    world.para()
    clean_track(world, detective, helper, tool_cfg, residue_cfg)
    transformed_ending(world, detective, helper, culprit_cfg)
    return world


KNOWLEDGE = {
    "rail": [
        ("What is a rail?", "A rail is one of the long, narrow strips a train rides on. The wheels need the rail to stay smooth so the train can roll properly.")
    ],
    "branch": [
        ("What is a branch in a train track?", "A branch is a place where the track can split and send the train one way or another. It is like a fork in a path.")
    ],
    "sticky": [
        ("Why is something sticky hard for wheels?", "Sticky stuff can grab a wheel and slow it down. If enough of it gets on a rail, the train may stop instead of gliding along.")
    ],
    "jam": [
        ("Why is jam sticky?", "Jam is made from fruit and sugar, so it clings to spoons and fingers. That same sweetness can leave a sticky smear on other things.")
    ],
    "honey": [
        ("Why is honey sticky?", "Honey is thick and sweet, so it spreads slowly and clings to surfaces. That is why it can make a mess if it drips.")
    ],
    "sap": [
        ("What is tree sap?", "Tree sap is a sticky liquid that comes from inside a tree. It can glue leaves and dirt to your fingers if you touch it.")
    ],
    "suspense": [
        ("What is suspense in a story?", "Suspense is the feeling that something important is about to be discovered. It makes you lean forward and wonder what will happen next.")
    ],
    "quest": [
        ("What is a quest?", "A quest is a journey with a goal. In a story, the characters move from place to place to solve a problem or find an answer.")
    ],
    "whodunit": [
        ("What is a whodunit?", "A whodunit is a mystery story where people look for clues to find out who caused the problem. The fun comes from solving the puzzle.")
    ],
    "cloth": [
        ("Why can a damp cloth clean sticky messes?", "A damp cloth can lift soft sticky messes away when you wipe gently. Water helps loosen the mess so it does not cling as hard.")
    ],
    "brush": [
        ("What does a scrub brush do?", "A scrub brush has stiff bristles that can rub dirt or sticky bits off a surface. It helps when a cloth alone is not enough.")
    ],
}
KNOWLEDGE_ORDER = ["rail", "branch", "sticky", "jam", "honey", "sap", "suspense", "quest", "whodunit", "cloth", "brush"]


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the back garden",
        detail="A loop of toy track ran between mint leaves and smooth stones.",
        hiding_spot="behind the watering can",
        ending_image="The red train circled the mint patch, and the children smiled as if they had solved the grandest case in the whole garden.",
        tags={"garden"},
    ),
    "porch": Setting(
        id="porch",
        place="the sunny porch",
        detail="A loop of toy track wound past flower pots and a striped doormat.",
        hiding_spot="under the bench",
        ending_image="The train flashed through the porch sunlight, and the mystery felt small now, like a shadow that had moved away.",
        tags={"porch"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the little orchard path",
        detail="A toy track curved beside fallen leaves and two low apple trees.",
        hiding_spot="behind a wooden crate",
        ending_image="The train ran under the apple leaves, and the children laughed because the scary question had turned into a solved and shining thing.",
        tags={"orchard"},
    ),
}

CULPRITS = {
    "sibling": Culprit(
        id="sibling",
        label="the older sibling",
        type="sibling",
        motive="been carrying toast with jam to a blanket fort",
        trail="There were careful shoe marks beside the track and one bright red dot on a leaf.",
        accidental=True,
        can_carry_food=True,
        kind="person",
        tags={"person"},
    ),
    "bird": Culprit(
        id="bird",
        label="a little bird",
        type="bird",
        motive="stolen a sweet crumb and landed on the rail for one hop",
        trail="Tiny prints tapped across the dirt, and one feather lay beside the stone by the track.",
        accidental=True,
        can_carry_food=True,
        kind="animal",
        tags={"animal"},
    ),
    "gardener": Culprit(
        id="gardener",
        label="the gardener",
        type="person",
        motive="trimmed a low tree and brushed past fresh sap without noticing",
        trail="A snapped twig and a green leaf pointed the way, as if the branch itself had tried to tell the story.",
        accidental=True,
        can_carry_food=False,
        kind="person",
        tags={"person"},
    ),
}

RESIDUES = {
    "jam": Residue(
        id="jam",
        label="jam",
        sticky=True,
        edible=True,
        clue="a shiny red smear and a sweet smell",
        smear="red and shining",
        clean_with={"cloth", "brush"},
        tags={"sticky", "jam"},
    ),
    "honey": Residue(
        id="honey",
        label="honey",
        sticky=True,
        edible=True,
        clue="a gold drop that glimmered beside the sleeper",
        smear="gold and slow",
        clean_with={"cloth", "brush"},
        tags={"sticky", "honey"},
    ),
    "sap": Residue(
        id="sap",
        label="sap",
        sticky=True,
        edible=False,
        clue="a clear amber bead caught on the side of the rail",
        smear="amber and stringy",
        clean_with={"brush"},
        tags={"sticky", "sap"},
    ),
    "mud": Residue(
        id="mud",
        label="mud",
        sticky=False,
        edible=False,
        clue="a dull brown patch with no shine at all",
        smear="brown and crumbly",
        clean_with={"cloth"},
        tags=set(),
    ),
}

TOOLS = {
    "cloth": Tool(
        id="cloth",
        label="a damp cloth",
        action="wiped the rail until the sticky trail came away on the fabric",
        works_on={"jam", "honey"},
        sense=3,
        tags={"cloth"},
    ),
    "brush": Tool(
        id="brush",
        label="a scrub brush",
        action="scrubbed gently along the metal until every sticky bit let go",
        works_on={"jam", "honey", "sap"},
        sense=3,
        tags={"brush"},
    ),
    "leaf": Tool(
        id="leaf",
        label="a dry leaf",
        action="rubbed at the mess with the leaf",
        works_on=set(),
        sense=1,
        tags=set(),
    ),
}

BRANCHES = {
    "switch": BranchSpot(
        id="switch",
        label="branch switch",
        phrase="a small branch switch where the track split around a marigold pot",
        tags={"branch"},
    ),
    "fork": BranchSpot(
        id="fork",
        label="branch fork",
        phrase="a neat branch fork where one line slipped past the stones and the other curved toward the herbs",
        tags={"branch"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    culprit: str
    residue: str
    tool: str
    branch: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="garden",
        culprit="sibling",
        residue="jam",
        tool="cloth",
        branch="switch",
        detective_name="Nora",
        detective_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="porch",
        culprit="bird",
        residue="honey",
        tool="cloth",
        branch="fork",
        detective_name="Leo",
        detective_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        setting="orchard",
        culprit="gardener",
        residue="sap",
        tool="brush",
        branch="switch",
        detective_name="Ava",
        detective_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="garden",
        culprit="gardener",
        residue="sap",
        tool="cloth",
        branch="fork",
        detective_name="Max",
        detective_gender="boy",
        helper_name="Lucy",
        helper_gender="girl",
        parent="father",
    ),
]


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


def explain_rejection(culprit: Culprit, residue: Residue) -> str:
    if not residue.sticky:
        return (
            f"(No story: {residue.label} is not sticky enough to stop a train on a rail, "
            "so there is no real mystery to solve. Pick jam, honey, or sap.)"
        )
    if residue.edible and not culprit.can_carry_food:
        return (
            f"(No story: {culprit.label} is not a plausible source of {residue.label} here, "
            "so the clue trail would feel weak. Pick a culprit who could carry something sweet.)"
        )
    return "(No story: this combination does not make a good sticky-rail mystery.)"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense "
        f"(sense={tool.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    culprit_cfg = f["culprit_cfg"]
    residue_cfg = f["residue_cfg"]
    branch_cfg = f["branch_cfg"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the words "rail", "sticky", and "branch".',
        f"Tell a suspenseful but kind mystery where {detective.id} and {helper.id} follow clues after a toy train stops by a {branch_cfg.label} because a rail is sticky with {residue_cfg.label}.",
        f"Write a quest story where child detectives discover that {culprit_cfg.label} caused the problem by accident, and the ending transforms fear into understanding.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    culprit_cfg = f["culprit_cfg"]
    residue_cfg = f["residue_cfg"]
    tool_cfg = f["tool_cfg"]
    branch_cfg = f["branch_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id} and {helper.id}, two children playing train detectives. They find a mystery at the {branch_cfg.label} and set out to solve it."
        ),
        (
            "What was the mystery?",
            f"Their toy train stopped because one rail had turned sticky near the {branch_cfg.label}. That strange stop is what made the children think a clue had been left behind."
        ),
        (
            f"What clues helped {detective.id} solve the case?",
            f"{detective.id} noticed {residue_cfg.clue}. Then the children followed the trail away from the track until the clues matched {culprit_cfg.label}."
        ),
        (
            f"Why did {culprit_cfg.label} make the rail sticky?",
            f"{culprit_cfg.label.capitalize()} had {culprit_cfg.motive}. It was an accident, not a mean trick, and that changed the mystery from scary to understandable."
        ),
    ]
    if world.facts.get("solved"):
        out.append(
            (
                "How did they fix the problem?",
                f"They used {tool_cfg.label} and cleaned the rail carefully until the sticky mess came away. After that, the train rolled past the branch again, which proved the quest was finished."
            )
        )
        out.append(
            (
                "How did the children change by the end?",
                f"They began in suspense, whispering about who had done it. By the end, they understood the truth and felt relief instead of fear."
            )
        )
    else:
        out.append(
            (
                "Did they solve everything?",
                f"They solved who caused the mess, but they could not clean the rail with the tool they had. The next step was to ask a grown-up for better help."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"rail", "branch", "whodunit", "quest", "suspense"}
    tags |= set(f["residue_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% valid mystery combinations
hazard(C, R) :- culprit(C), residue(R), sticky(R), can_source(C, R).
valid(S, C, R) :- setting(S), hazard(C, R).

can_source(C, R) :- edible(R), carries_food(C).
can_source(C, R) :- not edible(R), culprit(C).

% sensible tools and outcomes
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
solved(R, T) :- residue(R), tool(T), sensible_tool(T), works_on(T, R).
outcome(solved) :- chosen_residue(R), chosen_tool(T), solved(R, T).
outcome(stuck) :- chosen_residue(R), chosen_tool(T), not solved(R, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        if culprit.can_carry_food:
            lines.append(asp.fact("carries_food", culprit_id))
    for residue_id, residue in RESIDUES.items():
        lines.append(asp.fact("residue", residue_id))
        if residue.sticky:
            lines.append(asp.fact("sticky", residue_id))
        if residue.edible:
            lines.append(asp.fact("edible", residue_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for rid in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tool_id, rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_residue", params.residue),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    py_tools = {tool.id for tool in sensible_tools()}
    asp_tools = set(asp_sensible_tools())
    if py_tools == asp_tools:
        print(f"OK: sensible tools match ({sorted(py_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(asp_tools)} python={sorted(py_tools)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a sticky rail mystery with suspense, quest, and a kind whodunit ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--residue", choices=RESIDUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--branch", choices=BRANCHES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.residue:
        culprit = CULPRITS[args.culprit]
        residue = RESIDUES[args.residue]
        if not hazard_exists(culprit, residue):
            raise StoryError(explain_rejection(culprit, residue))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.residue is None or combo[2] == args.residue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, culprit_id, residue_id = rng.choice(sorted(combos))
    tool_choices = [tool.id for tool in sensible_tools()]
    tool_id = args.tool or rng.choice(sorted(tool_choices))
    branch_id = args.branch or rng.choice(sorted(BRANCHES))
    detective_name, detective_gender = pick_child(rng)
    helper_name, helper_gender = pick_child(rng, avoid=detective_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        culprit=culprit_id,
        residue=residue_id,
        tool=tool_id,
        branch=branch_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.residue not in RESIDUES:
        raise StoryError(f"(Unknown residue: {params.residue})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.branch not in BRANCHES:
        raise StoryError(f"(Unknown branch: {params.branch})")

    culprit_cfg = CULPRITS[params.culprit]
    residue_cfg = RESIDUES[params.residue]
    if not hazard_exists(culprit_cfg, residue_cfg):
        raise StoryError(explain_rejection(culprit_cfg, residue_cfg))
    if TOOLS[params.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))

    world = tell(
        setting=SETTINGS[params.setting],
        culprit_cfg=culprit_cfg,
        residue_cfg=residue_cfg,
        tool_cfg=TOOLS[params.tool],
        branch_cfg=BRANCHES[params.branch],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show sensible_tool/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        tools = asp_sensible_tools()
        print(f"sensible tools: {', '.join(tools)}\n")
        print(f"{len(combos)} compatible (setting, culprit, residue) combos:\n")
        for setting_id, culprit_id, residue_id in combos:
            print(f"  {setting_id:8} {culprit_id:9} {residue_id}")
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
            header = f"### {p.detective_name} & {p.helper_name}: {p.culprit} / {p.residue} / {p.branch}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
