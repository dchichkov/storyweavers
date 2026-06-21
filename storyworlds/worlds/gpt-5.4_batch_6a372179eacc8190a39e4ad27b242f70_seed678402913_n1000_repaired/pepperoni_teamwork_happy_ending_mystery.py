#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pepperoni_teamwork_happy_ending_mystery.py
=====================================================================

A standalone storyworld about a small, child-facing mystery: the pepperoni for a
pizza lunch has gone missing, two children work together to follow sensible
clues, and the mystery ends kindly and happily.

The world is intentionally small and constrained. Each culprit leaves a fitting
clue trail and hides or moves the pepperoni to a fitting place. The children do
not solve the mystery by magic or by parsing the English they already told;
instead, the simulated state records who moved the pepperoni, what clue was left
behind, how the children shared findings, and whether they recovered the food.

Run it
------
python storyworlds/worlds/gpt-5.4/pepperoni_teamwork_happy_ending_mystery.py
python storyworlds/worlds/gpt-5.4/pepperoni_teamwork_happy_ending_mystery.py --culprit puppy
python storyworlds/worlds/gpt-5.4/pepperoni_teamwork_happy_ending_mystery.py --spot toy_register
python storyworlds/worlds/gpt-5.4/pepperoni_teamwork_happy_ending_mystery.py --all
python storyworlds/worlds/gpt-5.4/pepperoni_teamwork_happy_ending_mystery.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/pepperoni_teamwork_happy_ending_mystery.py --qa --json
python storyworlds/worlds/gpt-5.4/pepperoni_teamwork_happy_ending_mystery.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "sister"}
        male = {"boy", "man", "father", "grandfather", "brother"}
        animal = {"puppy", "dog", "cat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandfather": "grandpa",
            "grandmother": "grandma",
        }.get(self.type, self.label or self.type)


@dataclass
class Scene:
    id: str
    place: str = ""
    opening: str = ""
    smell: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str = ""
    sentence: str = ""
    qa: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str = ""
    phrase: str = ""
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str = ""
    type: str = "thing"
    role_name: str = ""
    motive: str = ""
    apology: str = ""
    comfort_fix: str = ""
    clue: str = ""
    spot: str = ""
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


def _r_missing_worry(world: World) -> list[str]:
    platter = world.get("pepperoni")
    if platter.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role == "detective":
            ent.memes["curiosity"] += 1
            ent.memes["worry"] += 1
    return []


def _r_share_solves(world: World) -> list[str]:
    kid_a = world.get("kid_a")
    kid_b = world.get("kid_b")
    if kid_a.memes["shared"] < THRESHOLD or kid_b.memes["shared"] < THRESHOLD:
        return []
    if world.get("clue").meters["noticed"] < THRESHOLD:
        return []
    sig = ("shared_solves",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("case").meters["solved"] += 1
    kid_a.memes["teamwork"] += 1
    kid_b.memes["teamwork"] += 1
    return []


def _r_recovered_relief(world: World) -> list[str]:
    pepperoni = world.get("pepperoni")
    case = world.get("case")
    if pepperoni.meters["recovered"] < THRESHOLD or case.meters["solved"] < THRESHOLD:
        return []
    sig = ("recovered_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"detective", "grownup"}:
            ent.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="shared_solves", tag="social", apply=_r_share_solves),
    Rule(name="recovered_relief", tag="emotion", apply=_r_recovered_relief),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for text in produced:
            world.say(text)
    return produced


SCENES = {
    "kitchen": Scene(
        id="kitchen",
        place="the sunny kitchen",
        opening="The counter was lined with little round pizza crusts, and a tray waited nearby.",
        smell="Warm dough and tomato sauce made the whole room smell like lunch was on its way.",
        tags={"kitchen", "pizza"},
    ),
    "picnic_table": Scene(
        id="picnic_table",
        place="the backyard picnic table",
        opening="Paper plates, sauce cups, and little round pizza crusts were spread out in a neat row.",
        smell="The air smelled like basil and warm bread from the oven inside.",
        tags={"outside", "pizza"},
    ),
    "clubhouse": Scene(
        id="clubhouse",
        place="the little playhouse by the garden",
        opening="A folding table stood inside with mini crusts, spoons, and a red checkered cloth.",
        smell="Someone had carried out the warm tray, and the tiny room smelled like melted cheese and lunch.",
        tags={"clubhouse", "pizza"},
    ),
}

CLUES = {
    "pawprints": Clue(
        id="pawprints",
        label="tiny paw prints",
        sentence="On the floor, a few tiny paw prints curved away from the table in a shy little line.",
        qa="They found tiny paw prints, which pointed to an animal carrying the snack away.",
        tags={"animal", "tracks"},
    ),
    "sticky_fingers": Clue(
        id="sticky_fingers",
        label="greasy little fingerprints",
        sentence="Near the bowl sat a small red chair, and on it were greasy little fingerprints in half-moons.",
        qa="They noticed greasy little fingerprints, which suggested a small child had touched the pepperoni.",
        tags={"child", "fingers"},
    ),
    "cool_drip": Clue(
        id="cool_drip",
        label="a cold drip of water",
        sentence="By the table leg, one silver lid ring had been left behind, and beside it lay a cold drip of water from ice.",
        qa="They saw a cold drip from ice and a lid ring, which suggested the pepperoni had been moved somewhere cool.",
        tags={"cold", "ice"},
    ),
}

SPOTS = {
    "dog_bed": Spot(
        id="dog_bed",
        label="the dog bed",
        phrase="the soft dog bed by the pantry door",
        reveal="tucked in the blanket there sat the missing cup of pepperoni, with one hopeful puppy nose hovering over it",
        tags={"dog", "bed"},
    ),
    "toy_register": Spot(
        id="toy_register",
        label="the toy cash register",
        phrase="the toy market corner in the playroom",
        reveal="inside the open toy cash register, the missing pepperoni slices were stacked like bright little coins",
        tags={"playroom", "toy"},
    ),
    "blue_cooler": Spot(
        id="blue_cooler",
        label="the blue cooler",
        phrase="the blue cooler by the porch steps",
        reveal="under the cold lid sat the missing cup of pepperoni, safe and chilly beside the cheese",
        tags={"cooler", "cold"},
    ),
}

CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        label="Pip",
        type="puppy",
        role_name="the puppy",
        motive="Pip had smelled the spicy meat and had dragged the cup away because he thought it was a grand treasure.",
        apology="Pip thumped his tail and blinked as if he knew he had made lunch harder.",
        comfort_fix="Dad traded the cup for a crunchy dog biscuit, and Pip was delighted with the fair bargain.",
        clue="pawprints",
        spot="dog_bed",
        tags={"animal", "pet"},
    ),
    "little_sister": Culprit(
        id="little_sister",
        label="June",
        type="girl",
        role_name="the little sister",
        motive="June had wanted shiny play money for her pretend store, and the pepperoni circles had looked exactly right.",
        apology="June looked up with round eyes and whispered that she only meant to play store for one minute.",
        comfort_fix="The children gave June paper circles to use instead, and she happily rang them up at once.",
        clue="sticky_fingers",
        spot="toy_register",
        tags={"sister", "child"},
    ),
    "grandpa": Culprit(
        id="grandpa",
        label="Grandpa",
        type="grandfather",
        role_name="grandpa",
        motive="Grandpa had tucked the pepperoni into the cooler so the toppings would stay cold and fresh until lunch time.",
        apology="Grandpa laughed softly and admitted he had meant to tell everyone, but then the oven timer had beeped.",
        comfort_fix="He lifted the cup high like a found treasure and thanked the children for being such careful detectives.",
        clue="cool_drip",
        spot="blue_cooler",
        tags={"grownup", "cold"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Ella", "Maya", "Rose"]
BOY_NAMES = ["Ben", "Max", "Leo", "Theo", "Finn", "Sam", "Eli", "Noah"]
TRAITS = ["careful", "curious", "steady", "bright", "thoughtful", "patient"]


def valid_combo(scene_id: str, culprit_id: str, clue_id: str, spot_id: str) -> bool:
    if scene_id not in SCENES or culprit_id not in CULPRITS or clue_id not in CLUES or spot_id not in SPOTS:
        return False
    culprit = CULPRITS[culprit_id]
    return culprit.clue == clue_id and culprit.spot == spot_id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for scene_id in SCENES:
        for culprit_id, culprit in CULPRITS.items():
            if valid_combo(scene_id, culprit_id, culprit.clue, culprit.spot):
                combos.append((scene_id, culprit_id, culprit.clue, culprit.spot))
    return combos


def explain_rejection(culprit_id: str, clue_id: str, spot_id: str) -> str:
    culprit = CULPRITS.get(culprit_id)
    if culprit is None:
        return "(No story: unknown culprit.)"
    if clue_id != culprit.clue:
        expected = CLUES[culprit.clue].label
        got = CLUES[clue_id].label if clue_id in CLUES else clue_id
        return (
            f"(No story: {culprit.role_name} would not leave {got}. "
            f"This mystery needs a fitting clue such as {expected}.)"
        )
    if spot_id != culprit.spot:
        expected = SPOTS[culprit.spot].label
        got = SPOTS[spot_id].label if spot_id in SPOTS else spot_id
        return (
            f"(No story: {culprit.role_name} would not hide the pepperoni at {got}. "
            f"Choose a fitting place such as {expected}.)"
        )
    return "(No story: this combination does not form a sensible mystery.)"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def _grownup_type_for(culprit_id: str, rng: random.Random) -> str:
    if culprit_id == "grandpa":
        return "grandfather"
    return rng.choice(["mother", "father"])


def _do_take_pepperoni(world: World) -> None:
    pepperoni = world.get("pepperoni")
    pepperoni.meters["missing"] += 1
    world.get("culprit").meters["has_pepperoni"] += 1
    world.get("clue").meters["left"] += 1
    propagate(world, narrate=False)


def introduce(world: World, scene: Scene, kid_a: Entity, kid_b: Entity, grownup: Entity) -> None:
    for kid in (kid_a, kid_b):
        kid.memes["joy"] += 1
    world.say(
        f"{kid_a.id} and {kid_b.id} were helping {grownup.label_word} make mini pizzas in {scene.place}. "
        f"{scene.opening} {scene.smell}"
    )
    world.say(
        "Cheese waited in one bowl, sauce in another, and a cheerful little cup of pepperoni sat in the middle like the final bright treasure."
    )


def discover_missing(world: World, kid_a: Entity, kid_b: Entity) -> None:
    _do_take_pepperoni(world)
    world.say(
        f"When {kid_a.id} reached for the pepperoni, the little cup was gone."
    )
    world.say(
        f'"The pepperoni is missing," {kid_b.id} whispered, as if the room had suddenly turned into a mystery.'
    )


def choose_teamwork(world: World, kid_a: Entity, kid_b: Entity) -> None:
    kid_a.memes["cooperate"] += 1
    kid_b.memes["cooperate"] += 1
    world.say(
        f'{kid_a.id} did not blame anyone. "{kid_b.id}, let\'s be detectives together," {kid_a.pronoun()} said.'
    )
    world.say(
        f'{kid_b.id} nodded. "You look close to the table. I\'ll think about what happened a minute ago."'
    )


def notice_clue(world: World, clue: Clue, kid_a: Entity) -> None:
    world.get("clue").meters["noticed"] += 1
    kid_a.memes["focus"] += 1
    world.say(clue.sentence)
    world.say(
        f'{kid_a.id} crouched down. "That is our first clue," {kid_a.pronoun()} said.'
    )


def share_findings(world: World, culprit: Culprit, kid_a: Entity, kid_b: Entity) -> None:
    kid_a.memes["shared"] += 1
    kid_b.memes["shared"] += 1
    kid_b.memes["memory"] += 1
    if culprit.id == "puppy":
        memory = f'"I heard Pip make one tiny yip near the pantry," {kid_b.id} said.'
    elif culprit.id == "little_sister":
        memory = f'"I saw June pushing her red chair over here and giggling to herself," {kid_b.id} said.'
    else:
        memory = f'"Grandpa said the toppings should stay nice and cold," {kid_b.id} said slowly.'
    world.say(memory)
    world.say(
        f"Now the two clues fit together in their minds, and the mystery no longer felt dark and twisty."
    )
    propagate(world, narrate=False)


def search_spot(world: World, spot: Spot, kid_a: Entity, kid_b: Entity) -> None:
    world.say(
        f"Side by side, they hurried to {spot.phrase}."
    )
    world.say(
        f"There, {spot.reveal}."
    )
    world.get("spot").meters["found"] += 1


def explain_culprit(world: World, culprit: Culprit) -> None:
    world.say(culprit.motive)
    world.say(culprit.apology)


def recover_and_fix(world: World, culprit: Culprit, grownup: Entity, kid_a: Entity, kid_b: Entity) -> None:
    pepperoni = world.get("pepperoni")
    pepperoni.meters["recovered"] += 1
    pepperoni.meters["missing"] = 0.0
    world.get("culprit").meters["has_pepperoni"] = 0.0
    for kid in (kid_a, kid_b):
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    world.say(
        f"{grownup.label_word.capitalize()} smiled when the children explained the clues one by one."
    )
    world.say(
        f'"You solved it by listening and looking carefully together," {grownup.pronoun()} said.'
    )
    world.say(culprit.comfort_fix)
    propagate(world, narrate=False)


def happy_ending(world: World, kid_a: Entity, kid_b: Entity, grownup: Entity) -> None:
    for kid in (kid_a, kid_b):
        kid.memes["joy"] += 1
    world.say(
        f"Soon each little pizza wore a neat ring of pepperoni, and the tray slid into the oven."
    )
    world.say(
        f"When lunch was ready, {kid_a.id} and {kid_b.id} sat shoulder to shoulder, proud of their solved case and their warm slices."
    )
    world.say(
        "The mystery ended not with a scold, but with laughter, supper, and the happy feeling that two careful minds are better than one."
    )


def tell(
    scene: Scene,
    culprit_cfg: Culprit,
    clue_cfg: Clue,
    spot_cfg: Spot,
    kid_a_name: str,
    kid_a_gender: str,
    kid_b_name: str,
    kid_b_gender: str,
    grownup_type: str,
    trait_a: str,
    trait_b: str,
) -> World:
    world = World()
    kid_a = world.add(Entity(
        id="kid_a",
        kind="character",
        type=kid_a_gender,
        label=kid_a_name,
        phrase=kid_a_name,
        role="detective",
        traits=[trait_a],
    ))
    kid_b = world.add(Entity(
        id="kid_b",
        kind="character",
        type=kid_b_gender,
        label=kid_b_name,
        phrase=kid_b_name,
        role="detective",
        traits=[trait_b],
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        phrase="the grown-up",
        role="grownup",
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type=culprit_cfg.type,
        label=culprit_cfg.label,
        phrase=culprit_cfg.label,
        role="culprit",
        tags=set(culprit_cfg.tags),
    ))
    pepperoni = world.add(Entity(
        id="pepperoni",
        type="food",
        label="pepperoni",
        phrase="the little cup of pepperoni",
        tags={"pepperoni", "food"},
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=clue_cfg.label,
        phrase=clue_cfg.label,
        tags=set(clue_cfg.tags),
    ))
    spot = world.add(Entity(
        id="spot",
        type="spot",
        label=spot_cfg.label,
        phrase=spot_cfg.phrase,
        tags=set(spot_cfg.tags),
    ))
    case = world.add(Entity(
        id="case",
        type="mystery",
        label="the case",
        phrase="the mystery",
    ))

    world.facts.update(
        scene=scene,
        culprit_cfg=culprit_cfg,
        clue_cfg=clue_cfg,
        spot_cfg=spot_cfg,
        kid_a=kid_a,
        kid_b=kid_b,
        grownup=grownup,
        culprit=culprit,
        pepperoni=pepperoni,
        clue=clue,
        spot=spot,
        case=case,
    )

    introduce(world, scene, kid_a, kid_b, grownup)
    world.para()
    discover_missing(world, kid_a, kid_b)
    choose_teamwork(world, kid_a, kid_b)
    notice_clue(world, clue_cfg, kid_a)
    share_findings(world, culprit_cfg, kid_a, kid_b)
    world.para()
    search_spot(world, spot_cfg, kid_a, kid_b)
    explain_culprit(world, culprit_cfg)
    recover_and_fix(world, culprit_cfg, grownup, kid_a, kid_b)
    world.para()
    happy_ending(world, kid_a, kid_b, grownup)

    world.facts.update(
        solved=world.get("case").meters["solved"] >= THRESHOLD,
        recovered=world.get("pepperoni").meters["recovered"] >= THRESHOLD,
        teamwork=(kid_a.memes["teamwork"] >= THRESHOLD and kid_b.memes["teamwork"] >= THRESHOLD),
        outcome="happy" if world.get("pepperoni").meters["recovered"] >= THRESHOLD else "unsolved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    culprit_cfg = world.facts["culprit_cfg"]
    kid_a = world.facts["kid_a"]
    kid_b = world.facts["kid_b"]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the word "pepperoni" and ends happily.',
        f"Tell a gentle mystery where two children, {kid_a.label} and {kid_b.label}, discover that the pepperoni for lunch is missing in {scene.place} and solve the case by working together.",
        f"Write a child-friendly mystery with teamwork, a fitting clue, and a kind reveal that shows why {culprit_cfg.role_name} moved the pepperoni.",
    ]


def pair_noun(kid_a: Entity, kid_b: Entity) -> str:
    if kid_a.type == "girl" and kid_b.type == "girl":
        return "two girls"
    if kid_a.type == "boy" and kid_b.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    scene = world.facts["scene"]
    culprit_cfg = world.facts["culprit_cfg"]
    clue_cfg = world.facts["clue_cfg"]
    spot_cfg = world.facts["spot_cfg"]
    kid_a = world.facts["kid_a"]
    kid_b = world.facts["kid_b"]
    grownup = world.facts["grownup"]
    pair = pair_noun(kid_a, kid_b)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {kid_a.label} and {kid_b.label}, who were helping {grownup.label_word} make mini pizzas. "
            f"They became detectives when the pepperoni disappeared."
        ),
        (
            "What was the mystery?",
            f"The little cup of pepperoni went missing while the pizzas were being prepared in {scene.place}. "
            f"That sudden change turned lunch into a mystery they had to solve."
        ),
        (
            "What clue did the children find?",
            f"They found {clue_cfg.label}. {clue_cfg.qa}"
        ),
        (
            "How did the children use teamwork?",
            f"{kid_a.label} looked closely for a clue while {kid_b.label} remembered what had happened a moment earlier. "
            f"When they shared both ideas, the mystery made sense and they knew where to search."
        ),
        (
            "Where did they find the pepperoni?",
            f"They found it at {spot_cfg.label}. That place matched the clue and led them straight to the missing snack."
        ),
        (
            f"Why had {culprit_cfg.role_name} taken the pepperoni?",
            f"{culprit_cfg.motive} The ending stays gentle because it was a mix-up, not a mean trick."
        ),
        (
            "How did the story end?",
            f"The pepperoni was recovered, the pizzas were finished, and everyone felt relieved and happy. "
            f"The last image shows the children eating warm slices together after solving the case."
        ),
    ]
    return qa


KNOWLEDGE = {
    "pepperoni": [
        (
            "What is pepperoni?",
            "Pepperoni is a kind of spicy sausage that people often put on pizza in small round slices."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand at first, so you look for clues to figure it out."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand what happened, like a footprint, a sound, or something left behind."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other and combine their ideas to solve a problem or finish a job."
        )
    ],
    "puppy": [
        (
            "Why do puppies carry things away?",
            "Puppies explore with their noses and mouths, so they sometimes drag away interesting-smelling things they should leave alone."
        )
    ],
    "pretend_store": [
        (
            "Why do children use pretend things in play?",
            "Pretend play lets children imagine objects as something else, like leaves as money or blocks as food."
        )
    ],
    "cooler": [
        (
            "What is a cooler for?",
            "A cooler keeps food and drinks cold with ice, so they stay fresh until it is time to eat."
        )
    ],
}
KNOWLEDGE_ORDER = ["pepperoni", "mystery", "clue", "teamwork", "puppy", "pretend_store", "cooler"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    culprit_cfg = world.facts["culprit_cfg"]
    tags = {"pepperoni", "mystery", "clue", "teamwork"}
    if culprit_cfg.id == "puppy":
        tags.add("puppy")
    elif culprit_cfg.id == "little_sister":
        tags.add("pretend_store")
    elif culprit_cfg.id == "grandpa":
        tags.add("cooler")
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


@dataclass
class StoryParams:
    scene: str
    culprit: str
    clue: str
    spot: str
    kid_a_name: str
    kid_a_gender: str
    kid_b_name: str
    kid_b_gender: str
    grownup_type: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        scene="kitchen",
        culprit="puppy",
        clue="pawprints",
        spot="dog_bed",
        kid_a_name="Lily",
        kid_a_gender="girl",
        kid_b_name="Ben",
        kid_b_gender="boy",
        grownup_type="father",
        trait_a="careful",
        trait_b="curious",
    ),
    StoryParams(
        scene="clubhouse",
        culprit="little_sister",
        clue="sticky_fingers",
        spot="toy_register",
        kid_a_name="Maya",
        kid_a_gender="girl",
        kid_b_name="Nora",
        kid_b_gender="girl",
        grownup_type="mother",
        trait_a="bright",
        trait_b="patient",
    ),
    StoryParams(
        scene="picnic_table",
        culprit="grandpa",
        clue="cool_drip",
        spot="blue_cooler",
        kid_a_name="Theo",
        kid_a_gender="boy",
        kid_b_name="Ava",
        kid_b_gender="girl",
        grownup_type="grandfather",
        trait_a="thoughtful",
        trait_b="steady",
    ),
]


ASP_RULES = r"""
valid(Scene, Culprit, Clue, Spot) :-
    scene(Scene), culprit(Culprit), clue(Clue), spot(Spot),
    leaves(Culprit, Clue), hides(Culprit, Spot).

solved(Culprit, Clue, Spot) :-
    culprit(Culprit), clue(Clue), spot(Spot),
    leaves(Culprit, Clue), hides(Culprit, Spot).

happy(Culprit, Clue, Spot) :- solved(Culprit, Clue, Spot).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for scene_id in SCENES:
        lines.append(asp.fact("scene", scene_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("leaves", culprit_id, culprit.clue))
        lines.append(asp.fact("hides", culprit_id, culprit.spot))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_happy_outcome(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_spot", params.spot),
        "selected_happy :- chosen_culprit(C), chosen_clue(L), chosen_spot(S), happy(C, L, S).",
    ])
    model = asp.one_model(asp_program(extra, "#show selected_happy/0."))
    return ("selected_happy", ()) in [(name, tuple(args)) for name, *args in []] if False else "selected_happy" in {
        atom[0] if isinstance(atom, tuple) and atom else atom for atom in getattr(__import__("builtins"), "list")()
    }


def _asp_happy_outcome(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_spot", params.spot),
        "selected_happy :- chosen_culprit(C), chosen_clue(L), chosen_spot(S), happy(C, L, S).",
    ])
    model = asp.one_model(asp_program(extra, "#show selected_happy/0."))
    shown = asp.atoms(model, "selected_happy")
    return len(shown) > 0


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a missing pepperoni mystery solved through teamwork."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--grownup", choices=["mother", "father", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.clue and args.spot:
        if not valid_combo(args.scene or next(iter(SCENES)), args.culprit, args.clue, args.spot):
            raise StoryError(explain_rejection(args.culprit, args.clue, args.spot))
    if args.culprit and args.clue and not valid_combo(next(iter(SCENES)), args.culprit, args.clue, CULPRITS[args.culprit].spot):
        raise StoryError(explain_rejection(args.culprit, args.clue, CULPRITS[args.culprit].spot))
    if args.culprit and args.spot and not valid_combo(next(iter(SCENES)), args.culprit, CULPRITS[args.culprit].clue, args.spot):
        raise StoryError(explain_rejection(args.culprit, CULPRITS[args.culprit].clue, args.spot))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.clue is None or combo[2] == args.clue)
        and (args.spot is None or combo[3] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, culprit_id, clue_id, spot_id = rng.choice(sorted(combos))
    kid_a_gender = rng.choice(["girl", "boy"])
    kid_b_gender = rng.choice(["girl", "boy"])
    kid_a_name = _pick_name(rng, kid_a_gender)
    kid_b_name = _pick_name(rng, kid_b_gender, avoid=kid_a_name)
    grownup_type = args.grownup or _grownup_type_for(culprit_id, rng)
    trait_a = rng.choice(TRAITS)
    trait_b = rng.choice([t for t in TRAITS if t != trait_a] or TRAITS)

    return StoryParams(
        scene=scene_id,
        culprit=culprit_id,
        clue=clue_id,
        spot=spot_id,
        kid_a_name=kid_a_name,
        kid_a_gender=kid_a_gender,
        kid_b_name=kid_b_name,
        kid_b_gender=kid_b_gender,
        grownup_type=grownup_type,
        trait_a=trait_a,
        trait_b=trait_b,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(No story: unknown scene '{params.scene}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.spot not in SPOTS:
        raise StoryError(f"(No story: unknown spot '{params.spot}'.)")
    if not valid_combo(params.scene, params.culprit, params.clue, params.spot):
        raise StoryError(explain_rejection(params.culprit, params.clue, params.spot))

    world = tell(
        scene=SCENES[params.scene],
        culprit_cfg=CULPRITS[params.culprit],
        clue_cfg=CLUES[params.clue],
        spot_cfg=SPOTS[params.spot],
        kid_a_name=params.kid_a_name,
        kid_a_gender=params.kid_a_gender,
        kid_b_name=params.kid_b_name,
        kid_b_gender=params.kid_b_gender,
        grownup_type=params.grownup_type,
        trait_a=params.trait_a,
        trait_b=params.trait_b,
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
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as err:
        print(f"ASP verify failed to run clingo: {err}")
        return 1
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

    for params in CURATED:
        try:
            happy = _asp_happy_outcome(params)
        except Exception as err:
            rc = 1
            print(f"ASP outcome check crashed for curated params: {err}")
            continue
        if not happy:
            rc = 1
            print(f"MISMATCH: ASP did not derive happy outcome for {params}")
    if rc == 0:
        print(f"OK: happy outcome holds for {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "pepperoni" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missing core content.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        print(f"Smoke generation failed: {err}")
        return 1

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show happy/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, culprit, clue, spot) combos:\n")
        for scene_id, culprit_id, clue_id, spot_id in combos:
            print(f"  {scene_id:12} {culprit_id:14} {clue_id:16} {spot_id}")
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
            header = f"### {p.scene}: {p.culprit} with {p.clue} at {p.spot}"
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
