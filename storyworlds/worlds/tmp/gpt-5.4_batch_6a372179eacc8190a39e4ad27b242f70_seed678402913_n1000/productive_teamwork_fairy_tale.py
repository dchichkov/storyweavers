#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/productive_teamwork_fairy_tale.py
===========================================================

A standalone story world for gentle fairy-tale stories about a child and a
magical helper doing useful work together. The core pattern is:

    wish to finish a good task for others
    -> an obstacle makes solo work unproductive
    -> a helper with the right gift joins in
    -> teamwork clears the obstacle
    -> the useful work gets done before evening

The domain is intentionally small and constraint-checked. A story is only valid
when:
- the place can grow the chosen crop, and
- the obstacle can honestly be solved by the chosen tool and helper gift.

That keeps the turn grounded: the pair do not "work together" in name only. The
world state tracks progress, effort, blocked work, and feelings, and the prose
is rendered from those changes.

Run it
------
    python storyworlds/worlds/gpt-5.4/productive_teamwork_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/productive_teamwork_fairy_tale.py --place castle_garden --crop moonbeans
    python storyworlds/worlds/gpt-5.4/productive_teamwork_fairy_tale.py --obstacle hard_soil --helper rain_sprite --tool watering_can
    python storyworlds/worlds/gpt-5.4/productive_teamwork_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/productive_teamwork_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/productive_teamwork_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/productive_teamwork_fairy_tale.py --json
    python storyworlds/worlds/gpt-5.4/productive_teamwork_fairy_tale.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from inside this nested directory.
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
        female = {"girl", "mother", "woman", "princess"}
        male = {"boy", "father", "man", "prince"}
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
    scene: str
    afford_crops: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Crop:
    id: str
    label: str
    seeds: str
    ripe: str
    gift_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    problem_line: str
    solo_line: str
    clear_line: str
    need_tool: str
    need_gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    type: str
    phrase: str
    gift: str
    entrance: str
    work_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action_line: str
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


def _r_blocked_discourages(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    patch = world.entities.get("patch")
    if child is None or patch is None:
        return out
    if patch.meters["blocked"] < THRESHOLD:
        return out
    sig = ("blocked_discourages",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("__blocked__")
    return out


def _r_progress_hope(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.meters["progress"] < 2 * THRESHOLD:
        return out
    sig = ("progress_hope",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hope"] += 1
    out.append("__hope__")
    return out


def _r_teamwork_joy(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if child is None or helper is None:
        return out
    if child.meters["shared_work"] < THRESHOLD:
        return out
    sig = ("teamwork_joy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    child.memes["trust"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked_discourages", tag="emotion", apply=_r_blocked_discourages),
    Rule(name="progress_hope", tag="emotion", apply=_r_progress_hope),
    Rule(name="teamwork_joy", tag="emotion", apply=_r_teamwork_joy),
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


def place_supports(place: Place, crop: Crop) -> bool:
    return crop.id in place.afford_crops


def obstacle_solved_by(obstacle: Obstacle, helper: HelperKind, tool: Tool) -> bool:
    return helper.gift == obstacle.need_gift and tool.id == obstacle.need_tool


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for crop_id, crop in CROPS.items():
            if not place_supports(place, crop):
                continue
            for obstacle_id, obstacle in OBSTACLES.items():
                for helper_id, helper in HELPERS.items():
                    for tool_id, tool in TOOLS.items():
                        if obstacle_solved_by(obstacle, helper, tool):
                            combos.append((place_id, crop_id, obstacle_id, helper_id, tool_id))
    return combos


def predict_solo(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    patch = sim.get("patch")
    child.meters["effort"] += 1
    patch.meters["blocked"] += 1
    patch.meters["progress"] += 0
    propagate(sim, narrate=False)
    return {
        "blocked": patch.meters["blocked"] >= THRESHOLD,
        "progress": patch.meters["progress"],
        "worry": child.memes["worry"],
    }


def introduce(world: World, child: Entity, parent: Entity, crop: Crop) -> None:
    world.say(
        f"Once, in {world.place.scene}, there lived {child.id}, a little {child.type} "
        f"who loved doing useful things with small careful hands."
    )
    world.say(
        f"One morning, {child.id}'s {parent.label_word} gave {child.pronoun('object')} "
        f"{crop.seeds} and said, \"If these are planted well, they will grow into "
        f"{crop.ripe} for everyone to share.\""
    )
    child.memes["purpose"] += 1


def choose_task(world: World, child: Entity, crop: Crop) -> None:
    world.say(
        f"{child.id} skipped to the patch of earth beside the path and decided to make "
        f"the day truly productive. {child.pronoun().capitalize()} wanted the little bed "
        f"of soil to be full of {crop.label} before evening bells."
    )
    child.memes["determination"] += 1


def solo_try(world: World, child: Entity, obstacle: Obstacle) -> None:
    pred = predict_solo(world)
    world.facts["predicted_blocked"] = pred["blocked"]
    child.meters["effort"] += 1
    patch = world.get("patch")
    patch.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.problem_line)
    world.say(
        f"{child.id} bent to the work alone, but {obstacle.solo_line}"
    )
    if pred["blocked"]:
        world.say(
            f"Soon the row looked stubborn and unfinished, and {child.id} felt the morning "
            f"slipping away."
        )


def helper_arrives(world: World, helper_ent: Entity, helper_cfg: HelperKind) -> None:
    world.say(helper_cfg.entrance)
    world.say(
        f"\"You look as if the work wants two pairs of hands,\" said {helper_ent.id}."
    )
    helper_ent.memes["care"] += 1


def explain_problem(world: World, child: Entity, obstacle: Obstacle, crop: Crop) -> None:
    child.memes["worry"] += 1
    world.say(
        f"\"I want these {crop.label} to grow for the village supper,\" said {child.id}, "
        f"\"but {obstacle.label}, and I cannot finish in time by myself.\""
    )


def join_forces(world: World, child: Entity, helper_ent: Entity,
                helper_cfg: HelperKind, tool_cfg: Tool, obstacle: Obstacle) -> None:
    patch = world.get("patch")
    child.meters["shared_work"] += 1
    helper_ent.meters["shared_work"] += 1
    child.meters["effort"] += 1
    helper_ent.meters["effort"] += 1
    patch.meters["blocked"] = 0.0
    patch.meters["progress"] += 2
    world.facts["cleared_obstacle"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} took {tool_cfg.phrase}, and {helper_ent.id} used "
        f"{helper_cfg.work_line}."
    )
    world.say(tool_cfg.action_line)
    world.say(obstacle.clear_line)
    world.say(
        f"Working side by side, they found a steady rhythm: one started each task, "
        f"and the other finished it neatly."
    )


def finish_work(world: World, child: Entity, helper_ent: Entity, crop: Crop) -> None:
    patch = world.get("patch")
    patch.meters["planted"] += 1
    patch.meters["growing"] += 1
    child.meters["progress"] += 1
    helper_ent.meters["progress"] += 1
    child.memes["joy"] += 1
    child.memes["gratitude"] += 1
    helper_ent.memes["joy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before the sun tipped gold, the last seeds were tucked in, watered, and covered. "
        f"The whole bed looked straight and hopeful, as if it were smiling up at the sky."
    )
    world.say(
        f"A soft spell of evening passed over the ground, and by the path there rose "
        f"{crop.ripe}."
    )


def share_result(world: World, child: Entity, helper_ent: Entity,
                 parent: Entity, crop: Crop) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} filled a basket, and {helper_ent.id} carried the other handle so the "
        f"load would not tip. Together they brought {crop.gift_line} to {parent.label_word} "
        f"and the waiting neighbors."
    )
    world.say(
        f"\"Now I know the best kind of productive work,\" said {child.id}. "
        f"\"It is the kind that grows faster when friends do it together.\""
    )
    world.say(
        f"And from that day on, whenever a task in {world.place.label} seemed too large for "
        f"one small worker, two cheerful helpers could soon be seen making it light."
    )


def tell(place: Place, crop: Crop, obstacle: Obstacle, helper_cfg: HelperKind,
         tool_cfg: Tool, child_name: str = "Elin", child_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(place=place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        phrase=child_name,
        role="child",
        tags={"child"},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
        tags={"adult"},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={"gift": helper_cfg.gift},
        tags=set(helper_cfg.tags),
    ))
    patch = world.add(Entity(
        id="patch",
        kind="thing",
        type="garden_patch",
        label="garden patch",
        phrase="the garden patch",
        role="patch",
        tags={"garden"},
    ))

    world.facts.update(
        child=child,
        parent=parent,
        helper=helper_ent,
        place=place,
        crop=crop,
        obstacle=obstacle,
        helper_cfg=helper_cfg,
        tool=tool_cfg,
        teamwork=True,
        cleared_obstacle=False,
    )

    introduce(world, child, parent, crop)
    choose_task(world, child, crop)

    world.para()
    solo_try(world, child, obstacle)
    helper_arrives(world, helper_ent, helper_cfg)
    explain_problem(world, child, obstacle, crop)

    world.para()
    join_forces(world, child, helper_ent, helper_cfg, tool_cfg, obstacle)
    finish_work(world, child, helper_ent, crop)

    world.para()
    share_result(world, child, helper_ent, parent, crop)
    return world


PLACES = {
    "castle_garden": Place(
        id="castle_garden",
        label="the castle garden",
        scene="the castle garden behind the silver kitchens",
        afford_crops={"moonbeans", "sun_carrots", "dew_peas"},
        tags={"garden", "castle"},
    ),
    "forest_clearing": Place(
        id="forest_clearing",
        label="the forest clearing",
        scene="a bright forest clearing ringed with fern and foxglove",
        afford_crops={"moonbeans", "dew_peas"},
        tags={"forest"},
    ),
    "cottage_meadow": Place(
        id="cottage_meadow",
        label="the cottage meadow",
        scene="the cottage meadow where bees hummed over clover",
        afford_crops={"sun_carrots", "dew_peas"},
        tags={"meadow"},
    ),
}

CROPS = {
    "moonbeans": Crop(
        id="moonbeans",
        label="moonbeans",
        seeds="a little pouch of pearl-white moonbean seeds",
        ripe="a row of pale moonbeans hanging like tiny lanterns",
        gift_line="the first moonbeans",
        tags={"beans", "garden_food"},
    ),
    "sun_carrots": Crop(
        id="sun_carrots",
        label="sun-carrots",
        seeds="a ribbon-tied packet of sun-carrot seeds",
        ripe="a cluster of bright sun-carrots glowing under their feathery tops",
        gift_line="a bundle of sun-carrots",
        tags={"carrots", "garden_food"},
    ),
    "dew_peas": Crop(
        id="dew_peas",
        label="dew peas",
        seeds="a small blue paper fold of dew-pea seeds",
        ripe="a curtain of dew peas sparkling with silver drops",
        gift_line="the sweet dew peas",
        tags={"peas", "garden_food"},
    ),
}

OBSTACLES = {
    "hard_soil": Obstacle(
        id="hard_soil",
        label="the earth was packed hard as old bread",
        problem_line="But the patch had slept too long in the sun.",
        solo_line="every push only scratched the top, and the seeds had nowhere soft to rest",
        clear_line="The tight ground loosened into dark crumbly earth, ready to welcome every seed.",
        need_tool="spade",
        need_gift="strong",
        tags={"soil", "digging"},
    ),
    "thirsty_soil": Obstacle(
        id="thirsty_soil",
        label="the earth was dry and thirsty",
        problem_line="But the warm wind had stolen the damp from the ground.",
        solo_line="the rows turned dusty again, and the seeds would have dried before they could wake",
        clear_line="Soon the patch drank deeply, and the soil turned cool and kind.",
        need_tool="watering_can",
        need_gift="rain_calling",
        tags={"water", "soil"},
    ),
    "weedy_patch": Obstacle(
        id="weedy_patch",
        label="tangles of sharp little weeds crowded every row",
        problem_line="But a prickly net of weeds had crept in first.",
        solo_line="one handful came free while two more seemed to spring up laughing",
        clear_line="In a little while the weeds were gone, and the rows lay clean and open.",
        need_tool="rake",
        need_gift="swift",
        tags={"weeds", "clean_work"},
    ),
}

HELPERS = {
    "mole_cobbler": HelperKind(
        id="mole_cobbler",
        label="Moss the mole-cobbler",
        type="mole",
        phrase="a brown mole-cobbler in a neat leaf apron",
        gift="strong",
        entrance="Just then up popped Moss the mole-cobbler from a velvet tunnel, brushing soil from a tiny apron.",
        work_line="his strong digging paws",
        tags={"mole", "strong"},
    ),
    "rain_sprite": HelperKind(
        id="rain_sprite",
        label="Nim the rain-sprite",
        type="sprite",
        phrase="a rain-sprite with a bright drop-shaped cap",
        gift="rain_calling",
        entrance="Just then Nim the rain-sprite drifted down on a ribbon of mist, trailing cool silver drops.",
        work_line="a rain-song no bigger than a whisper",
        tags={"sprite", "water_magic"},
    ),
    "hedgehog_tailor": HelperKind(
        id="hedgehog_tailor",
        label="Pip the hedgehog-tailor",
        type="hedgehog",
        phrase="a hedgehog-tailor with a berry-red satchel",
        gift="swift",
        entrance="Just then Pip the hedgehog-tailor came hurrying along the path, quick as a sewing needle through cloth.",
        work_line="quick tidy paws",
        tags={"hedgehog", "swift"},
    ),
}

TOOLS = {
    "spade": Tool(
        id="spade",
        label="spade",
        phrase="the little moon-spade",
        action_line="The moon-spade bit down with a bright chink, and each turn opened a new line for planting.",
        tags={"digging_tool"},
    ),
    "watering_can": Tool(
        id="watering_can",
        label="watering can",
        phrase="the blue watering can",
        action_line="The blue watering can tipped in glittering arcs, and each pour stayed where it was needed.",
        tags={"watering_tool"},
    ),
    "rake": Tool(
        id="rake",
        label="rake",
        phrase="the willow-leaf rake",
        action_line="The willow-leaf rake combed the rows smooth while small roots and nettles gathered into easy heaps.",
        tags={"rake_tool"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Lila", "Nora", "Tessa", "Ivy"]
BOY_NAMES = ["Oren", "Tobin", "Finn", "Milo", "Ari", "Jasper"]
TRAITS = ["gentle", "busy", "cheerful", "careful", "hopeful"]


@dataclass
class StoryParams:
    place: str
    crop: str
    obstacle: str
    helper: str
    tool: str
    child_name: str
    child_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="castle_garden",
        crop="moonbeans",
        obstacle="hard_soil",
        helper="mole_cobbler",
        tool="spade",
        child_name="Elin",
        child_type="girl",
        parent_type="mother",
        trait="careful",
    ),
    StoryParams(
        place="forest_clearing",
        crop="dew_peas",
        obstacle="thirsty_soil",
        helper="rain_sprite",
        tool="watering_can",
        child_name="Oren",
        child_type="boy",
        parent_type="father",
        trait="hopeful",
    ),
    StoryParams(
        place="cottage_meadow",
        crop="sun_carrots",
        obstacle="weedy_patch",
        helper="hedgehog_tailor",
        tool="rake",
        child_name="Mira",
        child_type="girl",
        parent_type="mother",
        trait="cheerful",
    ),
]


KNOWLEDGE = {
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more people help each other do one job. They can often finish faster and better because each one adds something useful."
        )
    ],
    "productive": [
        (
            "What does productive mean?",
            "Productive means your work is really getting something good done. It is not just being busy; it means the job moves forward."
        )
    ],
    "garden": [
        (
            "Why do seeds need soft soil?",
            "Seeds need soft soil so their tiny roots can push through it and find water. If the ground is too hard, they have trouble starting to grow."
        )
    ],
    "water": [
        (
            "Why do seeds need water?",
            "Seeds need water to wake up and begin growing. Without enough water, they can stay dry and never sprout."
        )
    ],
    "weeds": [
        (
            "Why do gardeners pull weeds?",
            "Gardeners pull weeds because weeds steal space, water, and sunlight from the plants they want to grow. Clear rows help good plants grow strong."
        )
    ],
    "spade": [
        (
            "What is a spade for?",
            "A spade is a tool for digging and turning soil. It helps make holes and soft rows for planting."
        )
    ],
    "watering_can": [
        (
            "What is a watering can for?",
            "A watering can carries water to thirsty plants and soil. Its spout helps pour water gently where it is needed."
        )
    ],
    "rake": [
        (
            "What does a rake do?",
            "A rake gathers leaves, weeds, or loose soil into neat lines or piles. It helps make the ground tidy and ready for work."
        )
    ],
}
KNOWLEDGE_ORDER = ["productive", "teamwork", "garden", "water", "weeds", "spade", "watering_can", "rake"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    crop = f["crop"]
    obstacle = f["obstacle"]
    helper_cfg = f["helper_cfg"]
    tool = f["tool"]
    return [
        (
            f'Write a short fairy tale for a 3-to-5-year-old that includes the word '
            f'"productive" and shows teamwork helping a child finish useful garden work.'
        ),
        (
            f"Tell a fairy-tale story where {child.label} wants to plant {crop.label}, "
            f"but {obstacle.label}, and {helper_cfg.label} arrives to help with a {tool.label}."
        ),
        (
            f"Write a gentle story with a magical helper, a small obstacle in a garden, "
            f"and an ending that proves shared work can be more productive than working alone."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper_ent = f["helper"]
    crop = f["crop"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a little {child.type}, and {helper_ent.label}, who helped with the planting. {child.label}'s {parent.label_word} begins the job by giving the seeds."
        ),
        (
            f"What useful work did {child.label} want to do?",
            f"{child.label} wanted to plant {crop.label} so there would be something good to share later. The work mattered because the crop was meant for other people, not just for play."
        ),
        (
            f"Why could {child.label} not finish alone?",
            f"{obstacle.problem_line} {obstacle.label.capitalize()}, so the work would not move forward quickly enough. Alone, {child.label} was trying hard, but the patch stayed blocked instead of becoming ready for seeds."
        ),
        (
            f"How did {helper_ent.label} help?",
            f"{helper_ent.label} brought the right kind of help for that exact problem, while {child.label} used {tool.phrase}. Because the helper's gift and the tool matched the obstacle, they could clear it together and keep planting."
        ),
        (
            "Why was their teamwork productive?",
            f"The work became productive when it truly began moving forward: the obstacle was cleared, the rows were planted, and the crop could grow. They were not only busy; together they finished something useful before evening."
        ),
        (
            "How did the story end?",
            f"It ended with the harvest ready to share and the two of them carrying it together. The last image shows that the task changed from a stuck little patch into a gift for the whole place."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"productive", "teamwork", "garden"}
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    if obstacle.id == "thirsty_soil":
        tags.add("water")
    if obstacle.id == "weedy_patch":
        tags.add("weeds")
    tags.add(tool.id)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, crop: Crop, obstacle: Obstacle,
                      helper: HelperKind, tool: Tool) -> str:
    if not place_supports(place, crop):
        supported = ", ".join(sorted(place.afford_crops))
        return (
            f"(No story: {crop.label} do not belong in {place.label} here. "
            f"That place supports {supported}, so the planting would not feel honest.)"
        )
    if tool.id != obstacle.need_tool and helper.gift != obstacle.need_gift:
        return (
            f"(No story: {obstacle.label} needs {obstacle.need_tool} and a helper with "
            f"the gift '{obstacle.need_gift}'. This tool and helper do not truly solve it.)"
        )
    if tool.id != obstacle.need_tool:
        return (
            f"(No story: {obstacle.label} cannot be solved with the {tool.label}. "
            f"It needs {obstacle.need_tool} so the work can change in a believable way.)"
        )
    return (
        f"(No story: {helper.label} does not have the right gift for {obstacle.label}. "
        f"Choose a helper with the gift '{obstacle.need_gift}'.)"
    )


ASP_RULES = r"""
supports(Place, Crop) :- place(Place), crop(Crop), affords(Place, Crop).
solves(Obstacle, Helper, Tool) :- obstacle(Obstacle), helper(Helper), tool(Tool),
                                  need_tool(Obstacle, Tool),
                                  need_gift(Obstacle, Gift),
                                  helper_gift(Helper, Gift).
valid(Place, Crop, Obstacle, Helper, Tool) :- supports(Place, Crop), solves(Obstacle, Helper, Tool).
#show valid/5.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for crop_id in sorted(place.afford_crops):
            lines.append(asp.fact("affords", place_id, crop_id))
    for crop_id in CROPS:
        lines.append(asp.fact("crop", crop_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("need_tool", obstacle_id, obstacle.need_tool))
        lines.append(asp.fact("need_gift", obstacle_id, obstacle.need_gift))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_gift", helper_id, helper.gift))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("SMOKE FAIL during default resolve:", err)
        smoke_cases = list(CURATED)

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "productive" not in " ".join(sample.prompts).lower() and "productive" not in sample.story.lower():
                raise StoryError("required seed word missing")
            print(f"OK: smoke story {idx} generated ({params.place}, {params.crop}, {params.obstacle}).")
        except Exception as err:  # pragma: no cover - defensive verify path
            rc = 1
            print(f"SMOKE FAIL on case {idx}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: productive teamwork in a magical garden."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.place not in PLACES:
        raise StoryError(f"(Unknown place: {args.place})")
    if args.crop is not None and args.crop not in CROPS:
        raise StoryError(f"(Unknown crop: {args.crop})")
    if args.obstacle is not None and args.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {args.obstacle})")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")
    if args.tool is not None and args.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {args.tool})")

    if all(x is not None for x in (args.place, args.crop, args.obstacle, args.helper, args.tool)):
        place = PLACES[args.place]
        crop = CROPS[args.crop]
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        tool = TOOLS[args.tool]
        if not (place_supports(place, crop) and obstacle_solved_by(obstacle, helper, tool)):
            raise StoryError(explain_rejection(place, crop, obstacle, helper, tool))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.crop is None or c[1] == args.crop)
        and (args.obstacle is None or c[2] == args.obstacle)
        and (args.helper is None or c[3] == args.helper)
        and (args.tool is None or c[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, crop_id, obstacle_id, helper_id, tool_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        crop=crop_id,
        obstacle=obstacle_id,
        helper=helper_id,
        tool=tool_id,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place in params: {params.place})")
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop in params: {params.crop})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle in params: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper in params: {params.helper})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool in params: {params.tool})")

    place = PLACES[params.place]
    crop = CROPS[params.crop]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    tool = TOOLS[params.tool]
    if not place_supports(place, crop) or not obstacle_solved_by(obstacle, helper, tool):
        raise StoryError(explain_rejection(place, crop, obstacle, helper, tool))

    world = tell(
        place=place,
        crop=crop,
        obstacle=obstacle,
        helper_cfg=helper,
        tool_cfg=tool,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
    )
    child = world.get("child")
    if params.trait:
        child.traits.append(params.trait)

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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, crop, obstacle, helper, tool) combos:\n")
        for place, crop, obstacle, helper, tool in combos:
            print(f"  {place:15} {crop:12} {obstacle:13} {helper:16} {tool}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.crop} at {p.place} "
                f"({p.obstacle}, {p.helper}, {p.tool})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
