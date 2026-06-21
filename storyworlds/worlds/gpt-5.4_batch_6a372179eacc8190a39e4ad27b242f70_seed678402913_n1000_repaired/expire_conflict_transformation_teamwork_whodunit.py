#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/expire_conflict_transformation_teamwork_whodunit.py
=============================================================================

A standalone story world about a child-scale whodunit in a kitchen: a team of
young detectives is trying to bake something soft and puffy, but the dough
stays flat. They first blame each other, then follow clues, discover that the
yeast has gone past its date and will expire / has expired, and solve the case
together by finding a fresh packet. The central transformation is physical and
visible: flat dough becomes round and airy once the right ingredient is used.

The world model keeps the logic small and explicit:

    stale yeast + rise recipe     -> dough does not rise
    fresh yeast + rise recipe     -> dough rises
    accusation                    -> conflict between teammates
    shared clue-finding           -> teamwork grows
    solved mystery                -> conflict drops, trust grows

This script follows the storyworld contract:
- one self-contained stdlib script
- eager import of results.py
- lazy ASP import inside helpers
- standard CLI including --asp / --verify / --show-asp
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather"}
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
class Setting:
    id: str
    place: str
    detail: str
    storage: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Recipe:
    id: str
    name: str
    dough: str
    result: str
    shape: str
    aroma: str
    requires_rise: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TeamFrame:
    id: str
    title: str
    case_name: str
    clue_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AdultRole:
    id: str
    type: str
    entry: str
    wisdom: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    uses_fresh_yeast: bool = False
    can_help_rise: bool = False
    action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rise(world: World) -> list[str]:
    dough = world.entities.get("dough")
    yeast = world.entities.get("yeast")
    if dough is None or yeast is None:
        return []
    if not dough.attrs.get("requires_rise"):
        return []
    if dough.meters["mixed"] < THRESHOLD:
        return []
    if yeast.meters["fresh"] >= THRESHOLD:
        sig = ("rise", "fresh")
        if sig in world.fired:
            return []
        world.fired.add(sig)
        dough.meters["risen"] += 1
        dough.meters["flat"] = 0.0
        return ["__rise__"]
    if yeast.meters["expired"] >= THRESHOLD:
        sig = ("rise", "expired")
        if sig in world.fired:
            return []
        world.fired.add(sig)
        dough.meters["flat"] += 1
        return ["__flat__"]
    return []


def _r_accuse(world: World) -> list[str]:
    lead = world.entities.get("lead")
    pal = world.entities.get("pal")
    if lead is None or pal is None:
        return []
    if world.facts.get("accused") and ("conflict",) not in world.fired:
        world.fired.add(("conflict",))
        lead.memes["conflict"] += 1
        pal.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def _r_teamwork(world: World) -> list[str]:
    lead = world.entities.get("lead")
    pal = world.entities.get("pal")
    if lead is None or pal is None:
        return []
    clues = int(world.facts.get("clues_found", 0))
    sig = ("teamwork", clues)
    if clues >= 2 and sig not in world.fired:
        world.fired.add(sig)
        lead.memes["teamwork"] += 1
        pal.memes["teamwork"] += 1
        return ["__teamwork__"]
    return []


def _r_solved(world: World) -> list[str]:
    dough = world.entities.get("dough")
    if dough is None:
        return []
    if not world.facts.get("solved"):
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["conflict"] = 0.0
        kid.memes["trust"] += 1
        kid.memes["relief"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="rise", tag="physical", apply=_r_rise),
    Rule(name="accuse", tag="social", apply=_r_accuse),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
    Rule(name="solved", tag="social", apply=_r_solved),
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
        for s in produced:
            world.say(s)
    return produced


def recipe_needs_yeast(recipe: Recipe) -> bool:
    return recipe.requires_rise


def fix_works(recipe: Recipe, fix: Fix) -> bool:
    return recipe.requires_rise and fix.uses_fresh_yeast and fix.can_help_rise


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for recipe_id, recipe in RECIPES.items():
            for team_id in TEAM_FRAMES:
                for fix_id, fix in FIXES.items():
                    if recipe_needs_yeast(recipe) and fix_works(recipe, fix):
                        combos.append((setting_id, recipe_id, team_id, fix_id))
    return combos


def predict_dough(world: World, yeast_fresh: bool) -> dict:
    sim = world.copy()
    yeast = sim.get("yeast")
    dough = sim.get("dough")
    yeast.meters["fresh"] = 1.0 if yeast_fresh else 0.0
    yeast.meters["expired"] = 0.0 if yeast_fresh else 1.0
    dough.meters["mixed"] = 1.0
    propagate(sim, narrate=False)
    return {
        "risen": dough.meters["risen"] >= THRESHOLD,
        "flat": dough.meters["flat"] >= THRESHOLD,
    }


def introduce_team(world: World, lead: Entity, pal: Entity, frame: TeamFrame) -> None:
    lead.memes["joy"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"{lead.id} and {pal.id} called themselves {frame.title}. "
        f"Whenever something odd happened, they loved to whisper, \"A case!\""
    )
    world.say(
        f"That afternoon they stood in {world.setting.place}, where {world.setting.detail}. "
        f"They were helping make {world.facts['recipe_cfg'].result} for a snack table."
    )


def mix_dough(world: World, lead: Entity, pal: Entity, recipe: Recipe) -> None:
    dough = world.get("dough")
    dough.meters["mixed"] += 1
    world.say(
        f"They stirred flour, warm water, and yeast into {recipe.dough}. "
        f"Then they tucked the bowl under a clean towel and waited for the dough to transform."
    )
    world.say(
        f'"Soon it should turn from a small lump into {recipe.shape}," {lead.id} said.'
    )


def discover_problem(world: World, lead: Entity, pal: Entity, recipe: Recipe) -> None:
    dough = world.get("dough")
    yeast = world.get("yeast")
    if yeast.meters["expired"] >= THRESHOLD:
        yeast.attrs["status_word"] = "expired"
    propagate(world, narrate=False)
    if dough.meters["flat"] >= THRESHOLD:
        world.say(
            f"But when {pal.id} lifted the towel, the bowl looked almost the same. "
            f"The {recipe.dough} had stayed flat and sleepy instead of turning into {recipe.shape}."
        )
    else:
        world.say(
            f"When the towel came off, the dough had puffed up into {recipe.shape} right on time."
        )


def accuse(world: World, lead: Entity, pal: Entity) -> None:
    world.facts["accused"] = True
    propagate(world, narrate=False)
    lead.memes["suspicion"] += 1
    pal.memes["suspicion"] += 1
    world.say(
        f'"Did you forget to stir enough?" {lead.id} asked.'
    )
    world.say(
        f'"I stirred and stirred," {pal.id} said, cheeks turning pink. '
        f'"Maybe you poured the water too cold."'
    )


def adult_enters(world: World, adult: Entity) -> None:
    world.say(
        f"Just then, {adult.label_word.capitalize()} {world.facts['adult_cfg'].entry}. "
        f"{adult.pronoun().capitalize()} did not solve the case for them."
    )
    world.say(
        f'"Good detectives look for clues before they blame people," {adult.pronoun()} said.'
    )


def find_clue_bowl(world: World, lead: Entity, pal: Entity) -> None:
    world.facts["clues_found"] = world.facts.get("clues_found", 0) + 1
    propagate(world, narrate=False)
    world.say(
        f"{lead.id} touched the bowl. It was nicely warm, not cold at all. "
        f'"Then the warm water was not the problem," {lead.id} murmured.'
    )


def find_clue_packet(world: World, lead: Entity, pal: Entity) -> None:
    yeast = world.get("yeast")
    world.facts["clues_found"] = world.facts.get("clues_found", 0) + 1
    propagate(world, narrate=False)
    if yeast.meters["expired"] >= THRESHOLD:
        world.say(
            f"{pal.id} picked up the empty yeast packet from {world.setting.storage}. "
            f'"Wait," {pal.pronoun()} whispered. "The little date says it can expire, and this one already did."'
        )
    else:
        world.say(
            f"{pal.id} studied the yeast packet and found the date was still good."
        )


def solve_case(world: World, lead: Entity, pal: Entity, adult: Entity, fix: Fix, recipe: Recipe) -> None:
    world.facts["solved"] = True
    propagate(world, narrate=False)
    world.say(
        f'{lead.id} gasped. "So nobody spoiled the dough on purpose."'
    )
    world.say(
        f'"The real culprit was the expired yeast," {pal.id} said. '
        f'"It could not wake the dough up and make it rise."'
    )
    world.say(
        f"{adult.label_word.capitalize()} smiled. {adult.wisdom} "
        f"Together they {fix.action}."
    )
    dough = world.get("dough")
    yeast = world.get("yeast")
    dough.meters["mixed"] = 1.0
    dough.meters["flat"] = 0.0
    dough.meters["risen"] = 0.0
    yeast.meters["expired"] = 0.0
    yeast.meters["fresh"] = 1.0
    world.facts["used_fix"] = fix.id
    propagate(world, narrate=False)
    if dough.meters["risen"] >= THRESHOLD:
        world.say(
            f"This time the {recipe.dough} slowly swelled into {recipe.shape}. "
            f"The whole room filled with {recipe.aroma}."
        )


def ending(world: World, lead: Entity, pal: Entity, recipe: Recipe, frame: TeamFrame) -> None:
    world.say(
        f"Later, when the {recipe.result} came out warm and golden, {lead.id} and {pal.id} set them on the table like solved evidence."
    )
    world.say(
        f'"Case closed," they said together. They had started with blame, but they finished as a team, and the best clue of all was the dough itself, transformed at last.'
    )
    world.facts["ending_image"] = f"warm {recipe.result} on the table"


def tell(
    setting: Setting,
    recipe: Recipe,
    team: TeamFrame,
    adult_cfg: AdultRole,
    fix: Fix,
    lead_name: str = "Mia",
    lead_type: str = "girl",
    pal_name: str = "Ben",
    pal_type: str = "boy",
) -> World:
    world = World(setting)
    lead = world.add(Entity(id="lead", kind="character", type=lead_type, label=lead_name, role="leader"))
    pal = world.add(Entity(id="pal", kind="character", type=pal_type, label=pal_name, role="partner"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_cfg.type, label="the adult", role="adult"))
    dough = world.add(Entity(id="dough", type="dough", label=recipe.dough, phrase=recipe.dough, attrs={"requires_rise": recipe.requires_rise}))
    yeast = world.add(Entity(id="yeast", type="ingredient", label="yeast packet", phrase="a yeast packet"))
    yeast.meters["expired"] = 1.0
    bowl = world.add(Entity(id="bowl", type="tool", label="mixing bowl"))
    bowl.meters["warm"] = 1.0

    world.facts.update(
        lead=lead,
        pal=pal,
        adult=adult,
        recipe_cfg=recipe,
        team_cfg=team,
        adult_cfg=adult_cfg,
        fix_cfg=fix,
        setting_cfg=setting,
        clues_found=0,
        accused=False,
        solved=False,
        culprit="expired yeast",
    )

    introduce_team(world, lead, pal, team)
    mix_dough(world, lead, pal, recipe)

    world.para()
    discover_problem(world, lead, pal, recipe)
    accuse(world, lead, pal)
    adult_enters(world, adult)

    world.para()
    find_clue_bowl(world, lead, pal)
    find_clue_packet(world, lead, pal)
    solve_case(world, lead, pal, adult, fix, recipe)

    world.para()
    ending(world, lead, pal, recipe, team)
    return world


SETTINGS = {
    "home_kitchen": Setting(
        id="home_kitchen",
        place="the sunny kitchen at home",
        detail="jars clicked softly on the shelf and afternoon light made the counter shine",
        storage="the flour tin",
        tags={"kitchen"},
    ),
    "school_kitchen": Setting(
        id="school_kitchen",
        place="the little school kitchen",
        detail="aprons hung in a row and the big clock ticked above the sink",
        storage="the class baking shelf",
        tags={"school", "kitchen"},
    ),
    "bakery_corner": Setting(
        id="bakery_corner",
        place="the bakery lesson corner",
        detail="wooden spoons rested in a crock and the air already smelled sweet",
        storage="the ingredient cubby",
        tags={"bakery"},
    ),
}

RECIPES = {
    "buns": Recipe(
        id="buns",
        name="milk buns",
        dough="soft bun dough",
        result="little buns",
        shape="round puffy pillows",
        aroma="a warm, buttery smell",
        requires_rise=True,
        tags={"yeast", "bread"},
    ),
    "rolls": Recipe(
        id="rolls",
        name="dinner rolls",
        dough="roll dough",
        result="fluffy rolls",
        shape="a high, cloud-like mound",
        aroma="a toasty bread smell",
        requires_rise=True,
        tags={"yeast", "bread"},
    ),
    "twists": Recipe(
        id="twists",
        name="cinnamon twists",
        dough="cinnamon dough",
        result="golden twists",
        shape="a soft, swollen rope",
        aroma="sweet cinnamon steam",
        requires_rise=True,
        tags={"yeast", "cinnamon"},
    ),
}

TEAM_FRAMES = {
    "detective_club": TeamFrame(
        id="detective_club",
        title="the Crumb Detectives",
        case_name="The Case of the Sleeping Dough",
        clue_word="clue",
        tags={"mystery"},
    ),
    "apron_agents": TeamFrame(
        id="apron_agents",
        title="the Apron Agents",
        case_name="The Mystery of the Flat Bowl",
        clue_word="evidence",
        tags={"mystery"},
    ),
    "whisk_watch": TeamFrame(
        id="whisk_watch",
        title="Whisk Watch",
        case_name="The Curious Yeast Case",
        clue_word="sign",
        tags={"mystery"},
    ),
}

ADULTS = {
    "grandma": AdultRole(
        id="grandma",
        type="grandmother",
        entry="came over with flour on her hands",
        wisdom="\"Sometimes the clue is not who did it, but what changed,\" she said.",
        tags={"grandma"},
    ),
    "dad": AdultRole(
        id="dad",
        type="father",
        entry="looked up from washing the measuring cups",
        wisdom="\"Mysteries grow smaller when everyone shares the clues,\" he said.",
        tags={"dad"},
    ),
    "teacher": AdultRole(
        id="teacher",
        type="woman",
        entry="stepped closer from the sink with a gentle smile",
        wisdom="\"A good team checks the facts before it points fingers,\" she said.",
        tags={"teacher"},
    ),
}

FIXES = {
    "fresh_packet": Fix(
        id="fresh_packet",
        label="a fresh yeast packet",
        uses_fresh_yeast=True,
        can_help_rise=True,
        action="opened a fresh yeast packet and mixed a new bowl together",
        qa_text="They used a fresh yeast packet and mixed the dough again",
        tags={"yeast", "fresh"},
    ),
    "new_jar": Fix(
        id="new_jar",
        label="fresh yeast from a new jar",
        uses_fresh_yeast=True,
        can_help_rise=True,
        action="scooped fresh yeast from a new jar and started over together",
        qa_text="They scooped fresh yeast from a new jar and started over",
        tags={"yeast", "fresh"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Anna", "Nora", "Lucy", "Ella", "Ava"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Jack", "Noah"]


@dataclass
class StoryParams:
    setting: str
    recipe: str
    team: str
    adult: str
    fix: str
    lead_name: str
    lead_type: str
    pal_name: str
    pal_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "yeast": [
        (
            "What does yeast do in dough?",
            "Yeast is a tiny living ingredient that makes bubbles in dough. Those bubbles help the dough rise and become soft and puffy."
        )
    ],
    "fresh": [
        (
            "Why does a baker check dates on ingredients?",
            "Dates help you know whether an ingredient is still good to use. If something has expired, it may not work the way you expect."
        )
    ],
    "bread": [
        (
            "Why does dough change shape when it rises?",
            "When dough rises, tiny bubbles spread through it and push it outward. That is why a small lump can transform into a bigger, softer shape."
        )
    ],
    "cinnamon": [
        (
            "Why does warm cinnamon smell strong in the oven?",
            "Heat helps the sweet smell move into the air. That is why warm cinnamon treats can make a room smell cozy."
        )
    ],
    "mystery": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what really happened. Good detectives look at several clues before they decide."
        )
    ],
    "kitchen": [
        (
            "Why do people work together in a kitchen?",
            "Cooking has many small jobs, like measuring, stirring, and watching. Teamwork helps people do the jobs carefully and share what they notice."
        )
    ],
    "grandma": [
        (
            "Why do grown-ups sometimes ask children to slow down and check facts?",
            "Slowing down helps people notice the real problem instead of guessing. Facts can stop an argument and help everyone solve the problem together."
        )
    ],
    "dad": [
        (
            "Why is sharing clues better than blaming someone right away?",
            "Sharing clues helps everyone compare what they saw. Blaming too early can hurt feelings and hide the real answer."
        )
    ],
    "teacher": [
        (
            "Why does a class do better when children act like a team?",
            "A team listens, shares turns, and fixes problems together. That makes it easier to learn and easier to solve mistakes."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "yeast", "fresh", "bread", "cinnamon", "kitchen", "grandma", "dad", "teacher"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    pal = f["pal"]
    recipe = f["recipe_cfg"]
    adult = f["adult_cfg"]
    return [
        'Write a gentle whodunit story for a 3-to-5-year-old that includes the word "expire" and ends with teamwork in a kitchen.',
        f"Tell a child-friendly mystery where {lead.label} and {pal.label} think one of them ruined some {recipe.result}, but the real culprit is expired yeast.",
        f"Write a story in which conflict turns into cooperation after {adult.id} reminds two children to follow clues instead of blaming each other.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    pal = f["pal"]
    adult = f["adult"]
    adult_cfg = f["adult_cfg"]
    recipe = f["recipe_cfg"]
    fix = f["fix_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.label} and {pal.label}, two children playing at being detectives while they baked with {adult.label_word}. They wanted to solve a kitchen mystery."
        ),
        (
            f"What was the mystery in the story?",
            f"The mystery was why the {recipe.dough} stayed flat instead of changing into {recipe.shape}. That strange failure made the children wonder who had caused the problem."
        ),
        (
            "Why did the children argue at first?",
            f"They argued because the dough did not rise, and each child thought the other might have made a mistake. The flat dough created conflict before they had any real clues."
        ),
        (
            "What clues helped them solve the case?",
            f"They noticed the bowl was warm enough, so cold water was not the problem. Then they checked the yeast packet and saw the date had passed, which showed the yeast had expired."
        ),
        (
            "Who was the real culprit?",
            f"The real culprit was not a person at all. It was the expired yeast, which could not help the dough rise."
        ),
        (
            "How did the problem get fixed?",
            f"{fix.qa_text}. With fresh yeast, the dough finally transformed and puffed up the way it should."
        ),
        (
            "How did the children change by the end?",
            f"They stopped blaming each other and started working as a team. Solving the mystery together turned the conflict into trust."
        ),
    ]
    if recipe.id == "twists":
        qa.append(
            (
                "What proved that things were better at the end?",
                "The dough swelled properly, and the room filled with sweet cinnamon steam. The warm golden twists on the table showed that the mystery had truly been solved."
            )
        )
    else:
        qa.append(
            (
                "What proved that things were better at the end?",
                f"The dough finally rose, and later the warm {recipe.result} sat on the table. That ending image showed the kitchen problem had been solved the right way."
            )
        )
    if adult_cfg.id == "grandma":
        qa.append(
            (
                f"What did {adult.label_word} teach them?",
                f"{adult.label_word.capitalize()} taught them to look for what changed before blaming a person. That advice helped them notice the expired yeast and solve the case fairly."
            )
        )
    elif adult_cfg.id == "dad":
        qa.append(
            (
                f"What did {adult.label_word} teach them?",
                f"{adult.label_word.capitalize()} taught them to share clues instead of pointing fingers. That made it possible for both children to help solve the mystery."
            )
        )
    else:
        qa.append(
            (
                "What did the grown-up teach them?",
                "The grown-up taught them to check facts before they accused anyone. That calm lesson helped the children work together and find the true answer."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"mystery", "yeast", "fresh", "bread", "kitchen"}
    recipe = world.facts["recipe_cfg"]
    adult = world.facts["adult_cfg"]
    if recipe.id == "twists":
        tags.add("cinnamon")
    tags |= adult.tags
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  clues_found: {world.facts.get('clues_found', 0)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="home_kitchen",
        recipe="buns",
        team="detective_club",
        adult="grandma",
        fix="fresh_packet",
        lead_name="Mia",
        lead_type="girl",
        pal_name="Ben",
        pal_type="boy",
    ),
    StoryParams(
        setting="school_kitchen",
        recipe="rolls",
        team="apron_agents",
        adult="teacher",
        fix="new_jar",
        lead_name="Zoe",
        lead_type="girl",
        pal_name="Max",
        pal_type="boy",
    ),
    StoryParams(
        setting="bakery_corner",
        recipe="twists",
        team="whisk_watch",
        adult="dad",
        fix="fresh_packet",
        lead_name="Leo",
        lead_type="boy",
        pal_name="Nora",
        pal_type="girl",
    ),
]


def explain_rejection(recipe_id: str, fix_id: str) -> str:
    recipe = RECIPES.get(recipe_id)
    fix = FIXES.get(fix_id)
    if recipe is None or fix is None:
        return "(No story: unknown recipe or fix.)"
    if not recipe.requires_rise:
        return f"(No story: {recipe.result} do not need a rising mystery here.)"
    if not fix_works(recipe, fix):
        return (
            f"(No story: {fix.label} would not honestly solve flat {recipe.dough}. "
            f"Pick a fix that uses fresh yeast so the transformation can really happen.)"
        )
    return "(No story: that combination does not make sense in this world.)"


ASP_RULES = r"""
needs_yeast(R) :- recipe(R), requires_rise(R).
working_fix(F) :- fix(F), fresh_yeast(F), helps_rise(F).
valid(S, R, T, F) :- setting(S), team(T), needs_yeast(R), working_fix(F).

outcome(solved) :- chosen_recipe(R), chosen_fix(F), needs_yeast(R), working_fix(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, recipe in RECIPES.items():
        lines.append(asp.fact("recipe", rid))
        if recipe.requires_rise:
            lines.append(asp.fact("requires_rise", rid))
    for tid in TEAM_FRAMES:
        lines.append(asp.fact("team", tid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        if fix.uses_fresh_yeast:
            lines.append(asp.fact("fresh_yeast", fid))
        if fix.can_help_rise:
            lines.append(asp.fact("helps_rise", fid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_recipe", params.recipe),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    recipe = RECIPES[params.recipe]
    fix = FIXES[params.fix]
    return "solved" if recipe_needs_yeast(recipe) and fix_works(recipe, fix) else "?"


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

    checked = 0
    for params in CURATED:
        checked += 1
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            rc = 1
            print(f"MISMATCH outcome for {params}: asp={ao} python={po}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    if rc == 0:
        print(f"OK: outcome model matches on {checked} curated scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A child-friendly baking whodunit where expired yeast is the real culprit."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--team", choices=TEAM_FRAMES)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--lead-name")
    ap.add_argument("--lead-type", choices=["girl", "boy"])
    ap.add_argument("--pal-name")
    ap.add_argument("--pal-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.recipe is not None and args.fix is not None:
        if not fix_works(RECIPES[args.recipe], FIXES[args.fix]):
            raise StoryError(explain_rejection(args.recipe, args.fix))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.recipe is None or c[1] == args.recipe)
        and (args.team is None or c[2] == args.team)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, recipe, team, fix = rng.choice(sorted(combos))
    lead_type = args.lead_type or rng.choice(["girl", "boy"])
    pal_type = args.pal_type or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or pick_name(rng, lead_type)
    pal_name = args.pal_name or pick_name(rng, pal_type, avoid=lead_name)
    adult = args.adult or rng.choice(sorted(ADULTS))
    return StoryParams(
        setting=setting,
        recipe=recipe,
        team=team,
        adult=adult,
        fix=fix,
        lead_name=lead_name,
        lead_type=lead_type,
        pal_name=pal_name,
        pal_type=pal_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.recipe not in RECIPES:
        raise StoryError(f"(No story: unknown recipe '{params.recipe}'.)")
    if params.team not in TEAM_FRAMES:
        raise StoryError(f"(No story: unknown team '{params.team}'.)")
    if params.adult not in ADULTS:
        raise StoryError(f"(No story: unknown adult '{params.adult}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}'.)")
    if not fix_works(RECIPES[params.recipe], FIXES[params.fix]):
        raise StoryError(explain_rejection(params.recipe, params.fix))

    world = tell(
        SETTINGS[params.setting],
        RECIPES[params.recipe],
        TEAM_FRAMES[params.team],
        ADULTS[params.adult],
        FIXES[params.fix],
        lead_name=params.lead_name,
        lead_type=params.lead_type,
        pal_name=params.pal_name,
        pal_type=params.pal_type,
    )

    story = world.render().replace("lead", world.facts["lead"].label).replace("pal", world.facts["pal"].label)
    story = story.replace("adult", world.facts["adult"].label_word)
    story = story.replace("  ", " ")

    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (setting, recipe, team, fix) combos:\n")
        for setting, recipe, team, fix in combos:
            print(f"  {setting:14} {recipe:8} {team:15} {fix}")
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
            header = f"### {p.lead_name} & {p.pal_name}: {p.recipe} at {p.setting} ({p.team})"
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
