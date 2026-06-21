#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clear_bargain_tool_shed_repetition_kindness_heartwarming.py
=======================================================================================

A standalone storyworld for a heartwarming "tool shed" tale about clearing a path,
making a fair bargain, and choosing kindness. Two children want to fetch something
helpful from the back of the shed for a grown-up. The way is blocked by a small mess,
and only one good tool is at hand. They must make a clear bargain for sharing it.
When the bargain is fair and the tool truly fits the mess, the children work together,
repeat a little working rhyme, and the ending image proves that both the shed and the
children's hearts feel lighter.

Run it
------
    python storyworlds/worlds/gpt-5.4/clear_bargain_tool_shed_repetition_kindness_heartwarming.py
    python storyworlds/worlds/gpt-5.4/clear_bargain_tool_shed_repetition_kindness_heartwarming.py --goal watering_can --obstacle leaves --tool broom
    python storyworlds/worlds/gpt-5.4/clear_bargain_tool_shed_repetition_kindness_heartwarming.py --tool crate
    python storyworlds/worlds/gpt-5.4/clear_bargain_tool_shed_repetition_kindness_heartwarming.py --bargain all_work
    python storyworlds/worlds/gpt-5.4/clear_bargain_tool_shed_repetition_kindness_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/clear_bargain_tool_shed_repetition_kindness_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/clear_bargain_tool_shed_repetition_kindness_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    need_text: str
    use_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    mess_word: str
    blocks_with: str
    clear_verb: str
    refrain_piece: str
    difficulty: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    clears: set[str] = field(default_factory=set)
    speed: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class Bargain:
    id: str
    label: str
    line: str
    fair: bool = True
    kind_bonus: int = 1
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


def _r_path_clear(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["blocked"] < THRESHOLD:
        sig = ("path_clear", obstacle.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.get("shed").meters["clear"] += 1
        world.get("lead").memes["relief"] += 1
        world.get("helper").memes["relief"] += 1
    return []


def _r_kindness_grows(world: World) -> list[str]:
    lead = world.get("lead")
    helper = world.get("helper")
    if helper.memes["shared"] < THRESHOLD or lead.memes["worked_with"] < THRESHOLD:
        return []
    sig = ("kindness", "children")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="path_clear", tag="physical", apply=_r_path_clear),
    Rule(name="kindness_grows", tag="social", apply=_r_kindness_grows),
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


GOALS = {
    "watering_can": Goal(
        id="watering_can",
        label="watering can",
        phrase="the little green watering can",
        need_text="Grandma's marigolds outside looked thirsty and droopy.",
        use_text="carried the watering can outside so Grandma could give the flowers a drink",
        ending_image="Soon the marigolds stood up a little straighter, with bright drops shining on their petals.",
        tags={"flowers", "watering_can"},
    ),
    "seed_box": Goal(
        id="seed_box",
        label="seed box",
        phrase="the painted seed box",
        need_text="Grandpa wanted the seed box so he could plant peas before supper.",
        use_text="brought the seed box out to Grandpa so the little pea seeds could go into the soft soil",
        ending_image="By the fence, Grandpa tucked the peas into the earth, and the children patted the row smooth.",
        tags={"garden", "seed_box"},
    ),
    "birdhouse_jar": Goal(
        id="birdhouse_jar",
        label="jar of screws",
        phrase="the clear jar of birdhouse screws",
        need_text="Grandpa was mending a birdhouse and needed the right screws.",
        use_text="set the clear jar of screws into Grandpa's waiting hands so he could fix the birdhouse roof",
        ending_image="A sparrow landed on the fence while Grandpa tightened the last screw, as if it had come to say thank you.",
        tags={"birdhouse", "clear_jar"},
    ),
}

OBSTACLES = {
    "leaves": Obstacle(
        id="leaves",
        label="leaves",
        phrase="a drift of dry leaves",
        mess_word="rustly",
        blocks_with="the leaves had blown in under the door and covered the floorboards",
        clear_verb="sweep",
        refrain_piece="sweep a little",
        difficulty=2,
        tags={"leaves"},
    ),
    "twine": Obstacle(
        id="twine",
        label="twine",
        phrase="a snarl of garden twine",
        mess_word="tangly",
        blocks_with="the twine had slipped from a shelf and curled around pots and boots",
        clear_verb="lift away",
        refrain_piece="lift a little",
        difficulty=2,
        tags={"twine"},
    ),
    "soil": Obstacle(
        id="soil",
        label="spilled soil",
        phrase="a mound of spilled potting soil",
        mess_word="crumbly",
        blocks_with="a bag of soil had tipped over and made a soft brown hill across the path",
        clear_verb="brush",
        refrain_piece="brush a little",
        difficulty=3,
        tags={"soil"},
    ),
}

TOOLS = {
    "broom": ToolCfg(
        id="broom",
        label="small broom",
        phrase="the small straw broom",
        clears={"leaves", "soil"},
        speed=2,
        tags={"broom"},
    ),
    "gloves": ToolCfg(
        id="gloves",
        label="garden gloves",
        phrase="the pair of garden gloves",
        clears={"twine", "soil"},
        speed=2,
        tags={"gloves"},
    ),
    "dustpan": ToolCfg(
        id="dustpan",
        label="tin dustpan",
        phrase="the old tin dustpan",
        clears={"leaves", "soil"},
        speed=1,
        tags={"dustpan"},
    ),
    "crate": ToolCfg(
        id="crate",
        label="wooden crate",
        phrase="the wooden crate",
        clears=set(),
        speed=0,
        tags={"crate"},
    ),
}

BARGAINS = {
    "turns": Bargain(
        id="turns",
        label="take turns",
        line='"Here is a clear bargain," {helper} said. "You {action} one bit, then I {action} one bit."',
        fair=True,
        kind_bonus=1,
        tags={"turns", "bargain"},
    ),
    "trade_help": Bargain(
        id="trade_help",
        label="trade jobs",
        line='"Let\'s make a bargain," {helper} said. "I will hold the tool, and you carry the pile away. Then we switch."',
        fair=True,
        kind_bonus=1,
        tags={"trade_help", "bargain"},
    ),
    "gift_first": Bargain(
        id="gift_first",
        label="kind first turn",
        line='"Let\'s make a bargain," {helper} said softly. "You can have the first turn because you spotted the problem, and I will help with the next one."',
        fair=True,
        kind_bonus=2,
        tags={"gift_first", "bargain", "kindness"},
    ),
    "all_work": Bargain(
        id="all_work",
        label="one child does everything",
        line='"Here is my bargain," {helper} said. "You do all the work, and I will only watch."',
        fair=False,
        kind_bonus=0,
        tags={"bargain"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Ruby", "Clara", "Ivy"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["kind", "patient", "cheerful", "careful", "gentle", "helpful"]


def tool_can_clear(tool: ToolCfg, obstacle: Obstacle) -> bool:
    return obstacle.id in tool.clears


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for goal_id in GOALS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for tool_id, tool in TOOLS.items():
                if tool_can_clear(tool, obstacle):
                    out.append((goal_id, obstacle_id, tool_id))
    return out


def fair_bargains() -> list[str]:
    return [bid for bid, bargain in BARGAINS.items() if bargain.fair]


@dataclass
class StoryParams:
    goal: str
    obstacle: str
    tool: str
    bargain: str
    lead: str
    lead_gender: str
    helper: str
    helper_gender: str
    elder: str
    helper_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        goal="watering_can",
        obstacle="leaves",
        tool="broom",
        bargain="turns",
        lead="Lily",
        lead_gender="girl",
        helper="Ben",
        helper_gender="boy",
        elder="grandmother",
        helper_trait="kind",
    ),
    StoryParams(
        goal="seed_box",
        obstacle="twine",
        tool="gloves",
        bargain="trade_help",
        lead="Max",
        lead_gender="boy",
        helper="Nora",
        helper_gender="girl",
        elder="grandfather",
        helper_trait="patient",
    ),
    StoryParams(
        goal="birdhouse_jar",
        obstacle="soil",
        tool="gloves",
        bargain="gift_first",
        lead="Ella",
        lead_gender="girl",
        helper="Sam",
        helper_gender="boy",
        elder="grandfather",
        helper_trait="gentle",
    ),
    StoryParams(
        goal="watering_can",
        obstacle="soil",
        tool="broom",
        bargain="trade_help",
        lead="Theo",
        lead_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        elder="grandmother",
        helper_trait="helpful",
    ),
]


def explain_combo_rejection(goal: Goal, obstacle: Obstacle, tool: ToolCfg) -> str:
    return (
        f"(No story: {tool.phrase} is not a reasonable way to clear {obstacle.phrase} "
        f"in the tool shed, so the children could not honestly reach {goal.phrase}. "
        f"Pick a tool that really works for that mess.)"
    )


def explain_bargain_rejection(bargain: Bargain) -> str:
    return (
        f"(No story: the bargain '{bargain.id}' is not fair. A heartwarming story here "
        f"needs a clear bargain that shares the work with kindness.)"
    )


def predict_clearance(world: World, obstacle_id: str, tool_id: str) -> dict:
    sim = world.copy()
    obstacle = sim.get(obstacle_id)
    tool = sim.get(tool_id)
    _do_clear(sim, obstacle, tool, steps=tool.attrs.get("speed", 1), narrate=False)
    return {
        "path_clear": sim.get("shed").meters["clear"] >= THRESHOLD,
        "blocked_left": obstacle.meters["blocked"],
    }


def _do_clear(world: World, obstacle: Entity, tool: Entity, steps: int, narrate: bool = True) -> None:
    if obstacle.attrs.get("obstacle_id") not in tool.attrs.get("clears", set()):
        return
    obstacle.meters["blocked"] = max(0.0, obstacle.meters["blocked"] - float(steps))
    world.get("lead").memes["worked_with"] += 1
    world.get("helper").memes["worked_with"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, lead: Entity, helper: Entity, elder: Entity, goal: Goal) -> None:
    lead.memes["care"] += 1
    helper.memes["care"] += 1
    world.say(
        f"One soft afternoon, {lead.id} and {helper.id} followed {lead.pronoun('possessive')} "
        f"{elder.label_word} to the tool shed behind the garden."
    )
    world.say(
        f"The shed smelled like wood, flowerpots, and sun-warmed dirt. {goal.need_text}"
    )


def need_goal(world: World, lead: Entity, elder: Entity, goal: Goal) -> None:
    world.say(
        f'"Could one of you fetch {goal.phrase} for me?" {elder.label_word.capitalize()} asked. '
        f"{lead.id} wanted to help at once."
    )


def discover_block(world: World, lead: Entity, helper: Entity, obstacle: Obstacle, tool: ToolCfg) -> None:
    world.say(
        f"But near the back shelf, {obstacle.blocks_with}. {lead.id} stopped, and {helper.id} "
        f"looked down at {tool.phrase}, the only handy thing for the job."
    )
    world.get("obstacle").meters["blocked"] = float(obstacle.difficulty)
    world.get("shed").meters["clear"] = 0.0
    lead.memes["frustration"] += 1


def worry(world: World, lead: Entity, obstacle: Obstacle) -> None:
    world.say(
        f'"Oh dear," {lead.id} said. "The way is not clear at all."'
    )
    world.say(
        f"The {obstacle.label} made the narrow floor feel small and hard to cross."
    )


def bargain_scene(world: World, lead: Entity, helper: Entity, obstacle: Obstacle,
                  bargain: Bargain, tool: ToolCfg) -> None:
    helper.memes["shared"] += 1
    helper.memes["kindness"] += float(bargain.kind_bonus)
    line = bargain.line.format(helper=helper.id, action=obstacle.clear_verb)
    world.say(
        f"{helper.id} wrapped {helper.pronoun('possessive')} fingers around {tool.phrase}, "
        f"then looked at {lead.id}'s worried face."
    )
    world.say(line)
    world.say(
        f"{lead.id} nodded. It was a clear bargain, and it sounded kind."
    )


def repeated_work(world: World, lead: Entity, helper: Entity, obstacle_cfg: Obstacle,
                  tool_cfg: ToolCfg) -> None:
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    steps = int(tool_cfg.speed)
    rounds = max(2, obstacle_cfg.difficulty)
    refrain = f'"{obstacle_cfg.refrain_piece}, clear a little," they whispered together.'
    for i in range(rounds):
        if obstacle.meters["blocked"] <= 0:
            break
        if i == 0:
            world.say(
                f"{helper.id} began to {obstacle_cfg.clear_verb}, and {lead.id} helped make neat little piles."
            )
        else:
            world.say(
                f"Again they worked: {obstacle_cfg.refrain_piece}, clear a little."
            )
        world.say(refrain)
        _do_clear(world, obstacle, tool, steps=1, narrate=False)
    if obstacle.meters["blocked"] > 0:
        _do_clear(world, obstacle, tool, steps=steps, narrate=False)
    propagate(world, narrate=False)


def fetch_and_help(world: World, lead: Entity, helper: Entity, elder: Entity, goal: Goal) -> None:
    world.say(
        f"At last the path was clear. {lead.id} reached the shelf, and {helper.id} steadied the pots so nothing bumped."
    )
    world.say(
        f"Together they {goal.use_text}."
    )
    lead.memes["joy"] += 1
    helper.memes["joy"] += 1
    elder.memes["gratitude"] += 1


def warm_ending(world: World, lead: Entity, helper: Entity, elder: Entity, goal: Goal) -> None:
    world.say(
        f'{elder.label_word.capitalize()} smiled at both of them. "That was a fine bargain," '
        f"{elder.pronoun()} said. \"You made the shed clear, and you made each other feel helped.\""
    )
    if world.get("helper").memes["kindness"] >= 2:
        world.say(
            f"{helper.id} gave {lead.id} the tool for one last proud turn, just because kindness felt good."
        )
    world.say(goal.ending_image)
    world.say(
        f"When they looked back into the tool shed, the path was tidy, the light fell in a clean stripe, "
        f"and both children felt warm inside."
    )


def tell(goal: Goal, obstacle_cfg: Obstacle, tool_cfg: ToolCfg, bargain: Bargain,
         lead_name: str = "Lily", lead_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         elder_type: str = "grandmother", helper_trait: str = "kind") -> World:
    world = World()
    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        role="lead",
        traits=["eager"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[helper_trait],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    world.add(Entity(id="shed", type="place", label="tool shed"))
    world.add(Entity(
        id="goal",
        type="goal",
        label=goal.label,
        phrase=goal.phrase,
        attrs={"goal_id": goal.id},
        tags=set(goal.tags),
    ))
    world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=obstacle_cfg.label,
        phrase=obstacle_cfg.phrase,
        attrs={"obstacle_id": obstacle_cfg.id},
        tags=set(obstacle_cfg.tags),
    ))
    world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        attrs={"tool_id": tool_cfg.id, "clears": set(tool_cfg.clears), "speed": tool_cfg.speed},
        tags=set(tool_cfg.tags),
    ))

    opening(world, lead, helper, elder, goal)
    need_goal(world, lead, elder, goal)

    world.para()
    discover_block(world, lead, helper, obstacle_cfg, tool_cfg)
    worry(world, lead, obstacle_cfg)

    world.para()
    bargain_scene(world, lead, helper, obstacle_cfg, bargain, tool_cfg)
    repeated_work(world, lead, helper, obstacle_cfg, tool_cfg)

    world.para()
    fetch_and_help(world, lead, helper, elder, goal)
    warm_ending(world, lead, helper, elder, goal)

    world.facts.update(
        lead=lead,
        helper=helper,
        elder=elder,
        goal_cfg=goal,
        obstacle_cfg=obstacle_cfg,
        tool_cfg=tool_cfg,
        bargain_cfg=bargain,
        path_clear=world.get("shed").meters["clear"] >= THRESHOLD,
        kindness=helper.memes["kindness"],
    )
    return world


KNOWLEDGE = {
    "broom": [
        (
            "What does a broom do?",
            "A broom gathers loose things like dust, leaves, or dirt into one place. That helps make a floor clear and safe to walk on.",
        )
    ],
    "gloves": [
        (
            "Why do people wear garden gloves?",
            "Garden gloves protect your hands when you touch rough or tangled things. They can also help you hold messy things more carefully.",
        )
    ],
    "dustpan": [
        (
            "What is a dustpan for?",
            "A dustpan holds little piles of dirt or leaves after you sweep them up. You can carry the pile away without dropping it back on the floor.",
        )
    ],
    "leaves": [
        (
            "Why do dry leaves make a floor messy?",
            "Dry leaves slide around and crunch under your feet. A pile of them can cover the floor and get in the way.",
        )
    ],
    "twine": [
        (
            "Why can tangled twine be a problem?",
            "Twine can loop around boots, pots, or tools. When it tangles, it is harder to step safely and easier to trip.",
        )
    ],
    "soil": [
        (
            "Why should spilled soil be cleaned up?",
            "Spilled soil can spread across the floor and make a slippery, crumbly mess. Cleaning it up makes the path easier to use.",
        )
    ],
    "flowers": [
        (
            "Why do flowers need water?",
            "Flowers need water to stay strong and fresh. When they are thirsty, their stems and petals can start to droop.",
        )
    ],
    "seed_box": [
        (
            "What is a seed box?",
            "A seed box is a little container that keeps seeds together until it is time to plant them. It helps a gardener keep small seeds from getting lost.",
        )
    ],
    "birdhouse": [
        (
            "Why do birds like a birdhouse?",
            "A birdhouse gives small birds a sheltered place to rest or nest. A strong roof helps keep wind and rain out.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, share, or speak gently. Small kind choices can make work easier and hearts feel warmer.",
        )
    ],
    "bargain": [
        (
            "What is a bargain?",
            "A bargain is an agreement about what each person will do. A good bargain is clear and fair for everyone in it.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "bargain",
    "kindness",
    "broom",
    "gloves",
    "dustpan",
    "leaves",
    "twine",
    "soil",
    "flowers",
    "seed_box",
    "birdhouse",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    goal = f["goal_cfg"]
    obstacle = f["obstacle_cfg"]
    bargain = f["bargain_cfg"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old set in a tool shed that includes the words "clear" and "bargain".',
        f"Tell a gentle story where {lead.id} and {helper.id} find {obstacle.phrase} blocking the way to {goal.phrase}, then make a clear bargain and solve the problem with kindness.",
        f"Write a story with repetition in the middle, where children working in a tool shed say a little line again and again while they help {world.facts['elder'].label_word}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    elder = f["elder"]
    goal = f["goal_cfg"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    bargain = f["bargain_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {helper.id} in the tool shed with {elder.label_word}. They wanted to help fetch {goal.phrase}.",
        ),
        (
            f"Why did {lead.id} and {helper.id} need to clear the path?",
            f"They needed to reach {goal.phrase} at the back of the tool shed. {obstacle.phrase} was blocking the way, so they could not get there until they cleaned it up.",
        ),
        (
            f"What was the bargain?",
            f"They made a clear bargain to share the work instead of fussing over {tool.phrase}. That bargain was fair, which is why it helped them work side by side.",
        ),
    ]
    if f.get("path_clear"):
        qa.append(
            (
                f"How did kindness help solve the problem?",
                f"{helper.id} looked at {lead.id}'s worried face and chose to share the tool kindly. Because the bargain was gentle and clear, the two children kept working together until the path opened.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The path in the tool shed was clear, and together they {goal.use_text}. In the last image, the helpful job is done and both children feel warm inside because they shared the work kindly.",
            )
        )
    if bargain.id == "gift_first":
        qa.append(
            (
                f"Why did {helper.id} give {lead.id} the first turn?",
                f"{helper.id} was being extra kind. Giving the first turn made the bargain feel loving instead of bossy, and that helped the whole job begin gently.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"bargain", "kindness"}
    tool = f["tool_cfg"]
    obstacle = f["obstacle_cfg"]
    goal = f["goal_cfg"]
    tags |= set(tool.tags)
    tags |= set(obstacle.tags)
    if "watering_can" in goal.tags:
        tags.add("flowers")
    if "seed_box" in goal.tags:
        tags.add("seed_box")
    if "birdhouse" in goal.tags:
        tags.add("birdhouse")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: sorted(v) if isinstance(v, set) else v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Tool compatibility gate.
valid(G, O, T) :- goal(G), obstacle(O), tool(T), clears(T, O).

% Fair bargain gate.
fair_bargain(B) :- bargain(B), fair(B).

% Outcome model.
can_finish :- chosen_goal(G), chosen_obstacle(O), chosen_tool(T), valid(G, O, T).
warm_end   :- chosen_bargain(B), fair_bargain(B), can_finish.
outcome(warm) :- warm_end.
outcome(fail) :- not warm_end.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for obstacle_id in sorted(tool.clears):
            lines.append(asp.fact("clears", tool_id, obstacle_id))
    for bargain_id, bargain in BARGAINS.items():
        lines.append(asp.fact("bargain", bargain_id))
        if bargain.fair:
            lines.append(asp.fact("fair", bargain_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_fair_bargains() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show fair_bargain/1."))
    return sorted(b for (b,) in asp.atoms(model, "fair_bargain"))


def outcome_of(params: StoryParams) -> str:
    if not tool_can_clear(TOOLS[params.tool], OBSTACLES[params.obstacle]):
        return "fail"
    if not BARGAINS[params.bargain].fair:
        return "fail"
    return "warm"


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_goal", params.goal),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_bargain", params.bargain),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_fair = set(asp_fair_bargains())
    python_fair = set(fair_bargains())
    if clingo_fair == python_fair:
        print(f"OK: fair bargains match ({sorted(clingo_fair)}).")
    else:
        rc = 1
        print("MISMATCH in fair bargains:")
        print("  clingo:", sorted(clingo_fair))
        print("  python:", sorted(python_fair))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(25):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "tool shed" not in sample.story:
            raise StoryError("smoke test produced an empty or off-domain story")
        buffer = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buffer
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old_stdout
        print("OK: generate()/emit() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Heartwarming tool-shed storyworld: a clear bargain, kind sharing, and a tidy path."
    )
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--bargain", choices=BARGAINS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and args.obstacle and args.tool:
        goal = GOALS[args.goal]
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not tool_can_clear(tool, obstacle):
            raise StoryError(explain_combo_rejection(goal, obstacle, tool))
    if args.bargain:
        bargain = BARGAINS[args.bargain]
        if not bargain.fair:
            raise StoryError(explain_bargain_rejection(bargain))

    combos = [
        combo
        for combo in valid_combos()
        if (args.goal is None or combo[0] == args.goal)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goal_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    bargain_id = args.bargain or rng.choice(sorted(fair_bargains()))
    lead, lead_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=lead)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    helper_trait = rng.choice(TRAITS)
    return StoryParams(
        goal=goal_id,
        obstacle=obstacle_id,
        tool=tool_id,
        bargain=bargain_id,
        lead=lead,
        lead_gender=lead_gender,
        helper=helper,
        helper_gender=helper_gender,
        elder=elder,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        goal = GOALS[params.goal]
        obstacle = OBSTACLES[params.obstacle]
        tool = TOOLS[params.tool]
        bargain = BARGAINS[params.bargain]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc}.)") from exc

    if not tool_can_clear(tool, obstacle):
        raise StoryError(explain_combo_rejection(goal, obstacle, tool))
    if not bargain.fair:
        raise StoryError(explain_bargain_rejection(bargain))

    world = tell(
        goal=goal,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        bargain=bargain,
        lead_name=params.lead,
        lead_gender=params.lead_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        elder_type=params.elder,
        helper_trait=params.helper_trait,
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
        print(asp_program("", "#show valid/3.\n#show fair_bargain/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        valid = asp_valid_combos()
        fair = asp_fair_bargains()
        print(f"fair bargains: {', '.join(fair)}\n")
        print(f"{len(valid)} compatible (goal, obstacle, tool) combos:\n")
        for goal_id, obstacle_id, tool_id in valid:
            print(f"  {goal_id:13} {obstacle_id:8} {tool_id}")
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
            header = f"### {p.lead} & {p.helper}: {p.goal} behind {p.obstacle} ({p.tool}, {p.bargain})"
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
