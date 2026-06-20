#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/daughter_twist_dialogue_folk_tale.py
===============================================================

A small folk-tale storyworld about a mother, a daughter, a forest road, and a
stranger who is not what they seem.

Seeded premise
--------------
A mother sends her daughter along the old path to Grandmother's cottage with a
small provision. On the way, the daughter meets a shabby stranger who asks for a
share. The daughter must decide whether to open her hand or close it. The twist
is that the stranger is a hidden spirit of the road, and the spirit's gift only
helps if the daughter's heart is open.

The world is intentionally narrow and strongly constrained:

* A boon must actually solve the obstacle it is paired with.
* Invalid explicit choices are rejected with a clear StoryError.
* The middle turn is simulated from state: help or refusal changes trust,
  gratitude, fear, blockage, and arrival.
* Every story includes dialogue and a reveal-twist in a folk-tale tone.

Run it
------
    python storyworlds/worlds/gpt-5.4/daughter_twist_dialogue_folk_tale.py
    python storyworlds/worlds/gpt-5.4/daughter_twist_dialogue_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/daughter_twist_dialogue_folk_tale.py --obstacle river --boon moth_lantern
    python storyworlds/worlds/gpt-5.4/daughter_twist_dialogue_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/daughter_twist_dialogue_folk_tale.py --verify
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
    kind: str = "thing"        # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "grandmother": "grandmother",
        }.get(self.type, self.type)


@dataclass
class Provision:
    id: str
    label: str
    phrase: str
    share_piece: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    sight: str
    danger: str
    solved_by: str
    crossing: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Boon:
    id: str
    label: str
    phrase: str
    solves: str
    gift_line: str
    work_line: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Disguise:
    id: str
    intro: str
    request: str
    reveal: str
    true_name: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Heart:
    id: str
    label: str
    shares: bool
    first_reply: str
    ending_trait: str


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
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_blocked_worry(world: World) -> list[str]:
    out: list[str] = []
    daughter = world.get("daughter")
    obstacle = world.get("obstacle")
    if obstacle.meters["blocking"] >= THRESHOLD:
        sig = ("worry", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            daughter.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_boon_clears(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    boon = world.get("boon")
    daughter = world.get("daughter")
    if boon.meters["active"] < THRESHOLD or obstacle.meters["blocking"] < THRESHOLD:
        return out
    if world.facts["boon_cfg"].solves != world.facts["obstacle_cfg"].id:
        return out
    sig = ("clear", obstacle.id, boon.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obstacle.meters["blocking"] = 0.0
    obstacle.meters["cleared"] += 1
    daughter.memes["hope"] += 1
    out.append("__cleared__")
    return out


def _r_arrival(world: World) -> list[str]:
    out: list[str] = []
    road = world.get("road")
    obstacle = world.get("obstacle")
    grandmother = world.get("grandmother")
    daughter = world.get("daughter")
    if road.meters["journey"] < THRESHOLD or obstacle.meters["blocking"] >= THRESHOLD:
        return out
    sig = ("arrival", grandmother.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    grandmother.memes["relief"] += 1
    daughter.meters["arrived"] += 1
    out.append("__arrival__")
    return out


CAUSAL_RULES = [
    Rule("blocked_worry", "emotional", _r_blocked_worry),
    Rule("boon_clears", "physical", _r_boon_clears),
    Rule("arrival", "physical", _r_arrival),
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
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PROVISIONS = {
    "oatcake": Provision(
        "oatcake",
        "oat cake",
        "a warm oat cake wrapped in a cloth",
        "half the oat cake",
        tags={"bread", "sharing"},
    ),
    "berry_tart": Provision(
        "berry_tart",
        "berry tart",
        "a small berry tart with a shiny crust",
        "a neat slice of the tart",
        tags={"berry", "sharing"},
    ),
    "honey_bread": Provision(
        "honey_bread",
        "honey bread",
        "a loaf of honey bread still smelling of the oven",
        "a thick heel of the honey bread",
        tags={"bread", "sharing"},
    ),
}

OBSTACLES = {
    "river": Obstacle(
        "river",
        "swollen river",
        "the little river had grown broad and quick after the night's rain",
        "the stepping stones had vanished under the water",
        "fish_bridge",
        "silver backs broke the water and made a living bridge from bank to bank",
        "At Grandmother's step, a few bright scales still shone on the daughter's shoes.",
        tags={"river"},
    ),
    "thorns": Obstacle(
        "thorns",
        "thorn hedge",
        "a wall of black thorns had knitted itself across the path",
        "every branch hooked like a crooked finger",
        "rowan_comb",
        "the hedge sighed apart and left a narrow green door",
        "By the cottage gate, one soft thorn blossom still clung to the daughter's sleeve.",
        tags={"thorns"},
    ),
    "darkness": Obstacle(
        "darkness",
        "dark wood",
        "the pines stood so close that noon looked like twilight",
        "the path vanished under roots and shadow",
        "moth_lantern",
        "golden moths whirled ahead and stitched a bright thread through the dark",
        "When she knocked at Grandmother's door, one small moth still glowed above the latch.",
        tags={"darkness"},
    ),
}

BOONS = {
    "fish_bridge": Boon(
        "fish_bridge",
        "silver fish",
        "three silver fish scales in her palm",
        "river",
        '"Take these to the water," the stranger said. "Kindness is never wasted on a river."',
        "The daughter laid the scales on the current, and the river answered at once.",
        "The river that had snarled at her went quiet beneath shining backs.",
        tags={"river"},
    ),
    "rowan_comb": Boon(
        "rowan_comb",
        "rowan comb",
        "a comb carved from red rowan wood",
        "thorns",
        '"Comb once through what scratches, and it will remember gentler hands," the stranger said.',
        "The daughter drew the comb through the air before the hedge, and the branches trembled.",
        "The thorns that had clutched like claws opened like a curtain.",
        tags={"thorns"},
    ),
    "moth_lantern": Boon(
        "moth_lantern",
        "moth lantern",
        "a tiny lantern made from a moon-pale shell",
        "darkness",
        '"Lift this when the world grows dim," the stranger said. "Light follows a merciful hand."',
        "The daughter raised the shell lantern, and a ring of golden moths woke inside it.",
        "The dark wood lost its teeth when the little lantern began to glow.",
        tags={"darkness"},
    ),
}

DISGUISES = {
    "beggar": Disguise(
        "beggar",
        "by the old ash tree sat a ragged beggar with rain in the hem of the coat",
        '"Child, I have eaten only the smell of bread today. Will you spare me a bite?"',
        "the beggar stood straight as a pine and the torn coat shone like woven leaves",
        "the Keeper of the Road",
        tags={"sharing"},
    ),
    "old_woman": Disguise(
        "old_woman",
        "on a mossy stone rested a bent old woman with bright, watchful eyes",
        '"Little daughter, my hands shake too much to bake. Will you share a mouthful with me?"',
        "the old woman's back uncurled, and her gray shawl flashed green as spring bark",
        "the Old Mother of the Path",
        tags={"sharing"},
    ),
    "peddler": Disguise(
        "peddler",
        "at the bend waited a dusty peddler with an empty pack and a polite bow",
        '"Fair maid, my road is long and my stomach light. Have you a crumb to spare?"',
        "the peddler's pack filled with stars, and the dusty cap became a crown of fern",
        "the Hidden Warden of the Wood",
        tags={"sharing"},
    ),
}

HEARTS = {
    "kind": Heart(
        "kind",
        "kind",
        True,
        '"I can spare a little. A road feels shorter when two people are less hungry," said the daughter.',
        "kinder",
    ),
    "proud": Heart(
        "proud",
        "proud",
        False,
        '"No. This was baked for my grandmother, and I will not break it for a stranger," said the daughter.',
        "wiser",
    ),
}

GIRL_NAMES = ["Mara", "Elin", "Nessa", "Tilda", "Anya", "Bela", "Iris", "Mina"]
PARENT_TYPES = ["mother", "father"]


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def boon_fits(obstacle: Obstacle, boon: Boon) -> bool:
    return boon.solves == obstacle.id and obstacle.solved_by == boon.id


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for obstacle_id, obstacle in OBSTACLES.items():
        for boon_id, boon in BOONS.items():
            if boon_fits(obstacle, boon):
                combos.append((obstacle_id, boon_id))
    return combos


def explain_rejection(obstacle: Obstacle, boon: Boon) -> str:
    return (
        f"(No story: {boon.label} does not reasonably solve the {obstacle.label}. "
        f"In this world, the {obstacle.label} is overcome by {BOONS[obstacle.solved_by].label}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    return "blessed" if HEARTS[params.heart].shares else "humbled"


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, daughter: Entity, parent: Entity, grandmother: Entity,
              provision: Provision) -> None:
    daughter.memes["duty"] += 1
    world.say(
        f"In a cottage at the edge of the pine wood lived {daughter.id}, a {HEARTS[world.facts['heart_cfg'].id].label} "
        f"daughter who listened when the kettle sang and the floorboards creaked."
    )
    world.say(
        f"One morning {daughter.id}'s {parent.label_word} wrapped {provision.phrase} and said, "
        f'"Take this to your grandmother before the light grows thin."'
    )
    world.say(
        f'"I will go by the old path and come back before the shadows are long," said {daughter.id}.'
    )
    grandmother.memes["waiting"] += 1


def meet_stranger(world: World, daughter: Entity, disguise: Disguise) -> None:
    stranger = world.get("stranger")
    world.say(
        f"She set out with the basket on her arm, and {disguise.intro}. "
        f'The stranger looked up and said, {disguise.request}'
    )
    stranger.memes["need"] += 1


def choose(world: World, daughter: Entity, provision: Provision, heart: Heart) -> None:
    basket = world.get("basket")
    if heart.shares:
        daughter.memes["kindness"] += 1
        basket.meters["fullness"] -= 1
        world.say(
            f"{heart.first_reply} She broke off {provision.share_piece} and laid it in the stranger's hand."
        )
    else:
        daughter.memes["pride"] += 1
        world.say(heart.first_reply)


def reveal_and_gift(world: World, disguise: Disguise, boon: Boon) -> None:
    stranger = world.get("stranger")
    daughter = world.get("daughter")
    boon_ent = world.get("boon")
    stranger.memes["gratitude"] += 1
    stranger.memes["magic"] += 1
    daughter.memes["wonder"] += 1
    world.say(
        f"Then the road went still. The stranger rose, and {disguise.reveal}. "
        f'"I am {disguise.true_name}," the stranger said. {boon.gift_line}'
    )
    boon_ent.meters["given"] += 1
    world.say(f"In the daughter's hand there lay {boon.phrase}.")


def refuse_reveal(world: World, disguise: Disguise) -> None:
    stranger = world.get("stranger")
    daughter = world.get("daughter")
    stranger.memes["sadness"] += 1
    stranger.memes["magic"] += 1
    daughter.memes["wonder"] += 1
    world.say(
        f"The stranger lowered hungry eyes for a moment. Then {disguise.reveal}. "
        f'"I am {disguise.true_name}," the stranger said. "A closed hand makes a hard road."'
    )


def face_obstacle(world: World, obstacle: Obstacle) -> None:
    road = world.get("road")
    obs = world.get("obstacle")
    road.meters["journey"] += 1
    obs.meters["blocking"] += 1
    world.say(
        f"Not far ahead, {obstacle.sight}. {obstacle.danger}, and the daughter stopped with her breath caught."
    )
    propagate(world, narrate=False)


def use_boon(world: World, boon: Boon, obstacle: Obstacle) -> None:
    boon_ent = world.get("boon")
    world.say(boon.work_line)
    boon_ent.meters["active"] += 1
    propagate(world, narrate=False)
    if world.get("obstacle").meters["blocking"] < THRESHOLD:
        world.say(obstacle.crossing)


def turned_back(world: World, daughter: Entity, parent: Entity, obstacle: Obstacle) -> None:
    daughter.memes["shame"] += 1
    daughter.meters["returned"] += 1
    world.say(
        f"She tried the path once, and then again, but {obstacle.danger}. At last she turned back through the trees, "
        f"with the basket still heavy on her arm."
    )
    world.say(
        f'When she reached the cottage, "{daughter.id}, why are you home so soon?" asked her {parent.label_word}.'
    )


def confession(world: World, daughter: Entity, parent: Entity, disguise: Disguise) -> None:
    daughter.memes["truth"] += 1
    daughter.memes["lesson"] += 1
    world.say(
        f'"I met a stranger who asked for a share, and I would not give one," said {daughter.id}. '
        f'"Then the stranger became {disguise.true_name}. I think the road remembered what I did."'
    )
    world.say(
        f'The {parent.label_word} drew {daughter.pronoun("object")} close and said, '
        f'"Bread kept too tightly can make the heart hungry. Tomorrow we will set out again with enough for two."'
    )


def arrival(world: World, daughter: Entity, grandmother: Entity, obstacle: Obstacle,
            provision: Provision) -> None:
    daughter.memes["relief"] += 1
    daughter.memes["lesson"] += 1
    world.say(
        f"By sunset she came to her grandmother's door. The old woman opened it and said, "
        f'"Dear heart, you have come through trouble to bring me {provision.label}."'
    )
    world.say(
        f'"The road was hard at first," said {daughter.id}, "but kindness walked beside me in the end."'
    )
    world.say(obstacle.ending)


def blessing(world: World, daughter: Entity, parent: Entity, grandmother: Entity,
             boon: Boon) -> None:
    daughter.memes["blessing"] += 1
    world.say(
        f"That night the grandmother shared the basket, and each piece seemed to feed three mouths instead of one. "
        f'When {daughter.id} came home, her {parent.label_word} listened, smiled, and said, '
        f'"A gift comes back brighter when it is first given away."'
    )
    world.say(boon.ending)


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(provision: Provision, obstacle: Obstacle, boon: Boon, disguise: Disguise,
         heart: Heart, daughter_name: str = "Mara", parent_type: str = "mother") -> World:
    world = World()
    daughter = world.add(Entity(id="daughter", kind="character", type="girl",
                                label=daughter_name, role="daughter", traits=[heart.label]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type,
                              label=parent_type, role="parent"))
    grandmother = world.add(Entity(id="grandmother", kind="character", type="grandmother",
                                   label="grandmother", role="grandmother"))
    stranger = world.add(Entity(id="stranger", kind="character", type="woman",
                                label="stranger", role="stranger"))
    basket = world.add(Entity(id="basket", type="basket", label="basket"))
    road = world.add(Entity(id="road", type="road", label="road"))
    obstacle_ent = world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label,
                                    attrs={"kind": obstacle.id}))
    boon_ent = world.add(Entity(id="boon", type="boon", label=boon.label,
                                attrs={"solves": boon.solves}))
    basket.meters["fullness"] = 2.0

    world.facts.update(
        provision_cfg=provision,
        obstacle_cfg=obstacle,
        boon_cfg=boon,
        disguise_cfg=disguise,
        heart_cfg=heart,
        daughter=daughter,
        parent=parent,
        grandmother=grandmother,
        stranger=stranger,
        basket=basket,
    )

    introduce(world, daughter, parent, grandmother, provision)
    world.para()
    meet_stranger(world, daughter, disguise)
    choose(world, daughter, provision, heart)

    world.para()
    if heart.shares:
        reveal_and_gift(world, disguise, boon)
    else:
        refuse_reveal(world, disguise)

    world.para()
    face_obstacle(world, obstacle)
    if heart.shares:
        use_boon(world, boon, obstacle)
        arrival(world, daughter, grandmother, obstacle, provision)
        world.para()
        blessing(world, daughter, parent, grandmother, boon)
    else:
        turned_back(world, daughter, parent, obstacle)
        confession(world, daughter, parent, disguise)
        world.say(
            f"At dawn the next day, {daughter_name} cut the loaf in two before setting out again, and the basket felt lighter than before."
        )

    world.facts.update(
        outcome="blessed" if heart.shares else "humbled",
        arrived=world.get("daughter").meters["arrived"] >= THRESHOLD,
        shared=heart.shares,
        obstacle_cleared=world.get("obstacle").meters["cleared"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    provision: str
    obstacle: str
    boon: str
    disguise: str
    heart: str
    name: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "sharing": [
        (
            "Why does sharing matter in many folk tales?",
            "Sharing often shows what kind of heart a person has. In folk tales, a small generous act can open the way to help later."
        )
    ],
    "river": [
        (
            "Why can a river be dangerous to cross?",
            "A fast river can push your feet away and hide the safe stones under the water. That is why people must cross carefully or find another way."
        )
    ],
    "thorns": [
        (
            "Why do thorn bushes block a path?",
            "Thorns catch sleeves and scratch skin, so they can turn a narrow path into a hard wall. Even a short hedge can stop someone from passing."
        )
    ],
    "darkness": [
        (
            "Why is a dark wood hard to walk through?",
            "In deep shade, roots and turns are hard to see. When you cannot see the path, it is easy to get lost or stumble."
        )
    ],
    "bread": [
        (
            "What is a loaf of bread?",
            "A loaf is bread baked in one whole piece. People can slice it or break off pieces to share."
        )
    ],
    "berry": [
        (
            "What is a tart?",
            "A tart is a small baked pie with fruit or something sweet inside. It has a crust that holds the filling."
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "river", "thorns", "darkness", "bread", "berry"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    daughter = f["daughter"]
    obstacle = f["obstacle_cfg"]
    disguise = f["disguise_cfg"]
    outcome = f["outcome"]
    if outcome == "blessed":
        return [
            f'Write a short folk tale about a daughter on an errand who meets {disguise.intro.split(" sat ")[-1] if " sat " in disguise.intro else "a stranger"} and faces a {obstacle.label}. Include dialogue and a twist.',
            f"Tell a folk-style story where a daughter shares food with a stranger on the forest road, then learns the stranger is magical and receives help crossing a {obstacle.label}.",
            f'Write a gentle twist tale with spoken lines, where {daughter.label} is sent to Grandmother\'s house and kindness changes the road itself.',
        ]
    return [
        f"Write a folk tale about a daughter carrying food to Grandmother who refuses a stranger and then discovers the stranger was magical. Include dialogue and a clear lesson.",
        f"Tell a twist story where a proud daughter meets a hidden spirit on the road and must turn back from a {obstacle.label} before she learns to be generous.",
        f'Write a simple folk-style cautionary tale using the word "daughter" and ending with the child choosing a kinder way the next morning.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    daughter = f["daughter"]
    parent = f["parent"]
    grandmother = f["grandmother"]
    obstacle = f["obstacle_cfg"]
    boon = f["boon_cfg"]
    disguise = f["disguise_cfg"]
    provision = f["provision_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a daughter named {daughter.label}, her {parent.label_word}, and her grandmother. The story also turns on a stranger by the forest road."
        ),
        (
            f"Why did {daughter.label} leave home?",
            f"She was carrying {provision.phrase} to her grandmother. The errand matters because it sends her onto the old path where the test happens."
        ),
        (
            "What did the stranger ask for?",
            f"The stranger asked for a share of the food in the basket. That request tested whether the daughter would keep everything for herself or open her hand."
        ),
    ]
    if f["shared"]:
        qa.extend([
            (
                "What was the twist in the story?",
                f"The shabby stranger was really {disguise.true_name}. The reveal matters because the daughter's kindness is answered by hidden help."
            ),
            (
                f"How did {daughter.label} get past the {obstacle.label}?",
                f"She used the {boon.label} the stranger gave her, and it solved the trouble on the road. Because she had shared first, the gift turned the blocked path into a passable one."
            ),
            (
                "How did the story end?",
                f"She reached her grandmother safely and the family shared the food together. The ending image shows that generosity changed both the road and the daughter's heart."
            ),
        ])
    else:
        qa.extend([
            (
                "What was the twist in the story?",
                f"The hungry stranger was really {disguise.true_name}. The daughter only learned that after refusing to share."
            ),
            (
                f"Why did {daughter.label} turn back from the {obstacle.label}?",
                f"She had no help to clear the road, and the obstacle stayed dangerous. Her refusal earlier left her with a full basket but no easy way forward."
            ),
            (
                "What did the daughter learn at the end?",
                f"She learned that holding too tightly to her food had made the road harder. The next morning she chose to bring enough for two, which shows she had grown wiser."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["obstacle_cfg"].tags) | set(f["disguise_cfg"].tags) | set(f["provision_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:11} ({ent.type:11}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(O, B) :- obstacle(O), boon(B), solves(B, O), solved_by(O, B).
valid(O, B) :- fits(O, B).

shares :- chosen_heart(H), heart_shares(H).
outcome(blessed) :- shares.
outcome(humbled) :- not shares.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("solved_by", oid, obstacle.solved_by))
    for bid, boon in BOONS.items():
        lines.append(asp.fact("boon", bid))
        lines.append(asp.fact("solves", bid, boon.solves))
    for hid, heart in HEARTS.items():
        lines.append(asp.fact("heart", hid))
        if heart.shares:
            lines.append(asp.fact("heart_shares", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_heart", params.heart)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(30):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: ASP outcomes match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# CLI / interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("oatcake", "river", "fish_bridge", "old_woman", "kind", "Mara", "mother"),
    StoryParams("berry_tart", "thorns", "rowan_comb", "beggar", "kind", "Elin", "father"),
    StoryParams("honey_bread", "darkness", "moth_lantern", "peddler", "kind", "Nessa", "mother"),
    StoryParams("oatcake", "river", "fish_bridge", "beggar", "proud", "Tilda", "mother"),
    StoryParams("berry_tart", "thorns", "rowan_comb", "old_woman", "proud", "Mina", "father"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a daughter on an errand meets a hidden spirit."
    )
    ap.add_argument("--provision", choices=PROVISIONS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--boon", choices=BOONS)
    ap.add_argument("--disguise", choices=DISGUISES)
    ap.add_argument("--heart", choices=HEARTS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid obstacle/boon pairs from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.boon:
        obstacle = OBSTACLES[args.obstacle]
        boon = BOONS[args.boon]
        if not boon_fits(obstacle, boon):
            raise StoryError(explain_rejection(obstacle, boon))

    combos = [
        c for c in valid_combos()
        if (args.obstacle is None or c[0] == args.obstacle)
        and (args.boon is None or c[1] == args.boon)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    obstacle_id, boon_id = rng.choice(sorted(combos))
    provision = args.provision or rng.choice(sorted(PROVISIONS))
    disguise = args.disguise or rng.choice(sorted(DISGUISES))
    heart = args.heart or rng.choice(sorted(HEARTS))
    name = args.name or rng.choice(GIRL_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(provision, obstacle_id, boon_id, disguise, heart, name, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PROVISIONS[params.provision],
        OBSTACLES[params.obstacle],
        BOONS[params.boon],
        DISGUISES[params.disguise],
        HEARTS[params.heart],
        params.name,
        params.parent,
    )
    world.get("daughter").label = params.name
    return StorySample(
        params=params,
        story=world.render().replace("daughter", "daughter"),
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (obstacle, boon) pairs:\n")
        for obstacle, boon in combos:
            print(f"  {obstacle:10} {boon}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.heart} heart, {p.obstacle}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
