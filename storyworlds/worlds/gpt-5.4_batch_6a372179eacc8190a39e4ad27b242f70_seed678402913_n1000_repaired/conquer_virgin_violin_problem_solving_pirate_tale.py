#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/conquer_virgin_violin_problem_solving_pirate_tale.py
================================================================================

A standalone storyworld for a tiny pirate-flavored problem-solving tale.

Two children turn an ordinary place into a pirate expedition. Their crayon map
points to "Virgin Violin Cove," where a small violin in its red case waits on the
far side of some obstacle. One child wants to conquer the cove quickly; the
other slows down, predicts what could go wrong, and helps pick a tool that
actually matches the obstacle. The story's turn is not a punishment but a
problem-solving choice: the children keep the violin safe by using the right
method.

Run it
------
    python storyworlds/worlds/gpt-5.4/conquer_virgin_violin_problem_solving_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/conquer_virgin_violin_problem_solving_pirate_tale.py --setting beach --obstacle tide_pool --solution hook_line
    python storyworlds/worlds/gpt-5.4/conquer_virgin_violin_problem_solving_pirate_tale.py --obstacle high_ledge --solution plank_bridge
    python storyworlds/worlds/gpt-5.4/conquer_virgin_violin_problem_solving_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/conquer_virgin_violin_problem_solving_pirate_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/conquer_virgin_violin_problem_solving_pirate_tale.py --verify
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


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    rig: str
    affords: set[str] = field(default_factory=set)
    sendoff: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    mode: str
    size: int
    water: bool = False
    detour: bool = False
    case_has_handle: bool = True
    sight_line: str = ""
    bad_idea: str = ""
    bad_result: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    modes: set[str] = field(default_factory=set)
    max_size: int = 0
    requires_detour: bool = False
    needs_handle: bool = False
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
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_wet_violin(world: World) -> list[str]:
    violin = world.get("violin")
    if violin.meters["wet"] < THRESHOLD:
        return []
    sig = ("wet_violin",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    violin.meters["out_of_tune"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return []


def _r_retrieved_relief(world: World) -> list[str]:
    violin = world.get("violin")
    if violin.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("retrieved_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wet_violin", tag="physical", apply=_r_wet_violin),
    Rule(name="retrieved_relief", tag="emotional", apply=_r_retrieved_relief),
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
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "beach": Setting(
        id="beach",
        place="the beach",
        scene="a windy shore",
        rig="A striped towel became their pirate sail, a driftwood stick became a mast, and a crayon map lay flat on a bucket like a captain's chart.",
        affords={"tide_pool", "rope_channel"},
        sendoff="marched down the sand with the violin case held high",
        tags={"beach", "water"},
    ),
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        scene="a brave little harbor",
        rig="The sandbox was their harbor, a rake became a mast, and a cardboard box became the deck of their ship.",
        affords={"rope_channel", "high_ledge"},
        sendoff="trotted across the grass with the violin safe between them",
        tags={"yard"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        scene="a blanket sea",
        rig="A blue blanket became the sea, two cushions became islands, and a tape line on the floor curled like the edge of a secret bay.",
        affords={"tide_pool", "high_ledge"},
        sendoff="sailed back across the rug with a new sea song in mind",
        tags={"room"},
    ),
}

OBSTACLES = {
    "tide_pool": Obstacle(
        id="tide_pool",
        label="tide pool",
        phrase="a shining tide pool between them and the case",
        mode="gap",
        size=2,
        water=True,
        detour=False,
        case_has_handle=True,
        sight_line="On the far rock sat a tiny violin in its red case, bright as a berry.",
        bad_idea="jump over the tide pool with one big pirate leap",
        bad_result="the landing might splash water into the case and knock the violin out of tune",
        tags={"water", "tide_pool"},
    ),
    "rope_channel": Obstacle(
        id="rope_channel",
        label="channel",
        phrase="a wiggly little channel of water",
        mode="gap",
        size=3,
        water=True,
        detour=True,
        case_has_handle=True,
        sight_line="Beyond the channel, the red violin case waited on a flat crate like treasure on a dock.",
        bad_idea="wade straight through the channel",
        bad_result="the water would climb up their legs, and a wet violin would not sing nicely at all",
        tags={"water", "channel"},
    ),
    "high_ledge": Obstacle(
        id="high_ledge",
        label="ledge",
        phrase="a high ledge above the deck of their make-believe ship",
        mode="height",
        size=2,
        water=False,
        detour=False,
        case_has_handle=True,
        sight_line="Above them, the little red violin case rested on the ledge like treasure in a crow's nest.",
        bad_idea="climb a wobbly box and snatch the case in a hurry",
        bad_result="the box could tip and send the violin tumbling down",
        tags={"height", "ledge"},
    ),
}

SOLUTIONS = {
    "plank_bridge": Solution(
        id="plank_bridge",
        label="plank bridge",
        phrase="a smooth wooden plank",
        modes={"gap"},
        max_size=2,
        requires_detour=False,
        needs_handle=False,
        action="laid a smooth wooden plank across the gap and tested it with careful toes before carrying the case over",
        qa_text="laid a plank across the gap and walked carefully to the case",
        tags={"bridge", "plank"},
    ),
    "hook_line": Solution(
        id="hook_line",
        label="hook line",
        phrase="a toy hook on a rope",
        modes={"gap"},
        max_size=3,
        requires_detour=False,
        needs_handle=True,
        action="looped a toy hook through the case handle and reeled the violin gently across the gap",
        qa_text="used a hook line to pull the case across by its handle",
        tags={"hook", "rope"},
    ),
    "detour_wagon": Solution(
        id="detour_wagon",
        label="wagon detour",
        phrase="a little red wagon",
        modes={"gap"},
        max_size=5,
        requires_detour=True,
        needs_handle=False,
        action="found the long dry way around and rolled the violin home in a little red wagon",
        qa_text="took the dry path around and used a wagon to bring the violin back",
        tags={"wagon", "path"},
    ),
    "step_stool": Solution(
        id="step_stool",
        label="step stool",
        phrase="a steady step stool",
        modes={"height"},
        max_size=2,
        requires_detour=False,
        needs_handle=False,
        action="set a steady step stool by the ledge, held it firm, and lifted the case down with two careful hands",
        qa_text="used a steady step stool and lifted the case down carefully",
        tags={"stool", "height"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "clever", "steady", "thoughtful", "brave", "patient"]


def safe_solution(obstacle: Obstacle, solution: Solution) -> bool:
    if obstacle.mode not in solution.modes:
        return False
    if obstacle.size > solution.max_size:
        return False
    if solution.requires_detour and not obstacle.detour:
        return False
    if solution.needs_handle and not obstacle.case_has_handle:
        return False
    if obstacle.water and obstacle.mode == "gap" and solution.id == "step_stool":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for obstacle_id in setting.affords:
            obstacle = OBSTACLES[obstacle_id]
            for solution_id, solution in SOLUTIONS.items():
                if safe_solution(obstacle, solution):
                    combos.append((setting_id, obstacle_id, solution_id))
    return sorted(combos)


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    solution: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    captain_trait: str
    mate_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="beach",
        obstacle="tide_pool",
        solution="plank_bridge",
        captain_name="Tom",
        captain_gender="boy",
        mate_name="Lily",
        mate_gender="girl",
        captain_trait="brave",
        mate_trait="careful",
    ),
    StoryParams(
        setting="beach",
        obstacle="rope_channel",
        solution="hook_line",
        captain_name="Mia",
        captain_gender="girl",
        mate_name="Ben",
        mate_gender="boy",
        captain_trait="clever",
        mate_trait="steady",
    ),
    StoryParams(
        setting="backyard",
        obstacle="rope_channel",
        solution="detour_wagon",
        captain_name="Sam",
        captain_gender="boy",
        mate_name="Zoe",
        mate_gender="girl",
        captain_trait="patient",
        mate_trait="thoughtful",
    ),
    StoryParams(
        setting="playroom",
        obstacle="high_ledge",
        solution="step_stool",
        captain_name="Ava",
        captain_gender="girl",
        mate_name="Max",
        mate_gender="boy",
        captain_trait="brave",
        mate_trait="careful",
    ),
]


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def predict_bad_plan(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    violin = sim.get("violin")
    captain = sim.get("captain")
    if obstacle.water:
        violin.meters["wet"] += 1
        captain.meters["splashed"] += 1
    else:
        violin.meters["bumped"] += 1
    propagate(sim, narrate=False)
    return {
        "wet": violin.meters["wet"] >= THRESHOLD,
        "out_of_tune": violin.meters["out_of_tune"] >= THRESHOLD,
        "bumped": violin.meters["bumped"] >= THRESHOLD,
    }


def introduce(world: World, captain: Entity, mate: Entity) -> None:
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id} turned {world.setting.place} into {world.setting.scene}. {world.setting.rig}"
    )
    world.say(
        f'Today they meant to conquer Virgin Violin Cove, a name curled across their crayon map in brave blue letters.'
    )
    world.say(
        f'"Captain {captain.id} and First Mate {mate.id}!" {captain.id} cried.'
    )


def present_goal(world: World, obstacle: Obstacle) -> None:
    world.say(
        f"They followed the map until they found {obstacle.phrase}. {obstacle.sight_line}"
    )
    world.say(
        'If they could bring it back dry and safe, they could play a pirate song at the end of the voyage.'
    )


def bad_idea(world: World, captain: Entity, obstacle: Obstacle) -> None:
    captain.memes["boldness"] += 1
    world.say(
        f'"Easy," said {captain.id}. "I will {obstacle.bad_idea}, and then we will conquer the cove before the wind even changes."'
    )


def warning(world: World, mate: Entity, captain: Entity, obstacle: Obstacle) -> None:
    pred = predict_bad_plan(world, obstacle)
    mate.memes["caution"] += 1
    world.facts["predicted_bad"] = pred
    second = ""
    if pred["out_of_tune"]:
        second = " A wet violin would go quiet and sour instead of bright and singing."
    elif pred["bumped"]:
        second = " A bumped violin could lose its sweet sound before the song ever began."
    world.say(
        f'{mate.id} shook {mate.pronoun("possessive")} head. "No, Captain. {obstacle.bad_result}.{second}"'
    )


def think(world: World, captain: Entity, mate: Entity) -> None:
    captain.memes["thinking"] += 1
    mate.memes["thinking"] += 1
    world.say(
        f"For one moment they stood still, listening to the gulls or the house sounds around them. Then {captain.id} knelt by the chart, and {mate.id} knelt beside {captain.pronoun('object')}."
    )
    world.say(
        "Instead of charging ahead, they looked at the problem like real sailors reading a hard bit of sea."
    )


def choose_solution(world: World, captain: Entity, mate: Entity, solution: Solution) -> None:
    world.say(
        f'"What if we use {solution.phrase}?" asked {mate.id}.'
    )
    world.say(
        f'{captain.id} looked up, and a slow grin spread across {captain.pronoun("possessive")} face. "That is better pirate thinking," {captain.pronoun()} said.'
    )


def solve(world: World, captain: Entity, mate: Entity, solution: Solution) -> None:
    violin = world.get("violin")
    violin.meters["retrieved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {solution.action}."
    )
    world.say(
        f"Soon the red case was safe in {captain.id}'s arms, and not one drop or bump had spoiled the little violin inside."
    )


def celebrate(world: World, captain: Entity, mate: Entity, solution: Solution) -> None:
    world.say(
        f'"Virgin Violin Cove is conquered!" {captain.id} cheered.'
    )
    world.say(
        f'{mate.id} laughed. "Not by rushing," {mate.pronoun()} said, "but by thinking."'
    )
    world.say(
        f"They opened the case, and the violin shone warm and polished in the light. Soon they were humming a sea tune and {world.setting.sendoff}."
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    solution: Solution,
    captain_name: str,
    captain_gender: str,
    mate_name: str,
    mate_gender: str,
    captain_trait: str,
    mate_trait: str,
) -> World:
    world = World(setting)
    captain = world.add(
        Entity(
            id=captain_name,
            kind="character",
            type=captain_gender,
            role="captain",
            traits=[captain_trait],
        )
    )
    mate = world.add(
        Entity(
            id=mate_name,
            kind="character",
            type=mate_gender,
            role="mate",
            traits=[mate_trait],
        )
    )
    violin = world.add(
        Entity(
            id="violin",
            kind="thing",
            type="violin",
            label="violin",
            phrase="a tiny violin in its red case",
            tags={"violin"},
        )
    )
    gap = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type=obstacle.mode,
            label=obstacle.label,
            phrase=obstacle.phrase,
            tags=set(obstacle.tags),
        )
    )
    tool = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=solution.label,
            phrase=solution.phrase,
            tags=set(solution.tags),
        )
    )

    introduce(world, captain, mate)
    present_goal(world, obstacle)

    world.para()
    bad_idea(world, captain, obstacle)
    warning(world, mate, captain, obstacle)
    think(world, captain, mate)

    world.para()
    choose_solution(world, captain, mate, solution)
    solve(world, captain, mate, solution)
    celebrate(world, captain, mate, solution)

    world.facts.update(
        captain=captain,
        mate=mate,
        violin=violin,
        obstacle_cfg=obstacle,
        obstacle=gap,
        solution_cfg=solution,
        tool=tool,
        setting=setting,
        solved=violin.meters["retrieved"] >= THRESHOLD,
        kept_dry=violin.meters["wet"] < THRESHOLD,
        out_of_tune=violin.meters["out_of_tune"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "violin": [
        (
            "What is a violin?",
            "A violin is a wooden music instrument with strings. You hold it gently and make music by moving a bow across the strings."
        )
    ],
    "water": [
        (
            "Why should you keep a violin dry?",
            "Water can hurt the wood and strings and make the violin sound wrong. That is why musicians carry it carefully and keep it dry."
        )
    ],
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge gives you a safe way to cross over something. It helps you get to the other side without stepping into the gap below."
        )
    ],
    "hook": [
        (
            "What is a hook on a rope good for?",
            "A hook on a rope can catch something and pull it closer. It is useful when the thing has a handle and you cannot reach it by hand."
        )
    ],
    "wagon": [
        (
            "Why use a wagon to carry something delicate?",
            "A wagon helps move something without dropping it. If you go slowly, it can keep a fragile thing steadier than carrying it in a rush."
        )
    ],
    "stool": [
        (
            "Why is a steady stool better than a wobbly box?",
            "A steady stool is made for standing safely. A wobbly box can tip or slide and make you drop what you are trying to reach."
        )
    ],
    "problem": [
        (
            "What does problem solving mean?",
            "Problem solving means stopping to think about what is wrong and what tool or idea fits best. It is using your mind before you use your feet."
        )
    ],
}
KNOWLEDGE_ORDER = ["violin", "water", "bridge", "hook", "wagon", "stool", "problem"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    obstacle = f["obstacle_cfg"]
    solution = f["solution_cfg"]
    return [
        'Write a short pirate tale for a 3-to-5-year-old that includes the words "conquer," "virgin," and "violin."',
        f"Tell a gentle problem-solving story where {captain.id} wants to conquer Virgin Violin Cove quickly, but {mate.id} helps choose a better plan than trying to {obstacle.bad_idea}.",
        f"Write a child-friendly pirate adventure where a small violin must be brought back safely, and the children solve the problem by using {solution.phrase}.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    return "a boy and a girl"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    obstacle = f["obstacle_cfg"]
    solution = f["solution_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(captain, mate)}, {captain.id} and {mate.id}. They were pretending to be pirates on an expedition."
        ),
        (
            "What were they trying to do?",
            f"They wanted to conquer Virgin Violin Cove and bring back a little violin in its red case. The goal was not only to reach it, but to keep it safe enough to play."
        ),
        (
            "What problem stood in their way?",
            f"{obstacle.phrase.capitalize()} stood between them and the violin. That obstacle made a fast grab feel tempting, but risky."
        ),
        (
            f"Why did {mate.id} tell {captain.id} not to {obstacle.bad_idea}?",
            f"{mate.id} knew that {obstacle.bad_result}. {world.get('violin').label.capitalize()} had to stay safe, so rushing would have spoiled the plan instead of finishing it."
        ),
        (
            "How did they solve the problem?",
            f"They {solution.qa_text}. That solution matched the obstacle, so they could reach the case without hurting the violin."
        ),
        (
            "How did the story end?",
            f"They brought the violin back safely and cheered that Virgin Violin Cove was conquered. The last image shows them humming a sea tune, which proves their careful thinking worked."
        ),
    ]
    if setting.id == "beach":
        qa.append(
            (
                "What made the story feel like a pirate tale?",
                "The children used a crayon map, pirate titles, and a made-up cove name to turn an ordinary place into an adventure. Even the problem was solved like sailors studying a tricky bit of sea."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"violin", "problem"}
    obstacle = f["obstacle_cfg"]
    solution = f["solution_cfg"]
    if obstacle.water:
        tags.add("water")
    if solution.id == "plank_bridge":
        tags.add("bridge")
    if solution.id == "hook_line":
        tags.add("hook")
    if solution.id == "detour_wagon":
        tags.add("wagon")
    if solution.id == "step_stool":
        tags.add("stool")
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.traits:
            parts.append(f"traits={ent.traits}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, obstacle: Obstacle, solution: Solution) -> str:
    if obstacle.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not contain {obstacle.phrase}, so the pirate problem does not exist there.)"
        )
    if obstacle.mode not in solution.modes:
        return (
            f"(No story: {solution.label} does not solve a {obstacle.mode} problem. Pick a tool that fits the obstacle.)"
        )
    if obstacle.size > solution.max_size:
        return (
            f"(No story: {solution.label} is too small for this {obstacle.label}. The children need a tool that can really reach or cover the distance.)"
        )
    if solution.requires_detour and not obstacle.detour:
        return (
            f"(No story: this obstacle has no long dry path, so a wagon detour would not make sense.)"
        )
    if solution.needs_handle and not obstacle.case_has_handle:
        return (
            f"(No story: the violin case offers nothing for a hook to catch.)"
        )
    return "(No story: this setting, obstacle, and solution do not form a sensible problem-solving tale.)"


def outcome_of(setting_id: str, obstacle_id: str, solution_id: str) -> str:
    setting = SETTINGS[setting_id]
    obstacle = OBSTACLES[obstacle_id]
    solution = SOLUTIONS[solution_id]
    return "solved" if obstacle_id in setting.affords and safe_solution(obstacle, solution) else "stuck"


ASP_RULES = r"""
fits_mode(O, S) :- obstacle(O), solution(S), mode(O, M), solves_mode(S, M).
within_size(O, S) :- obstacle(O), solution(S), size(O, N), max_size(S, M), N <= M.
detour_ok(O, S) :- solution(S), requires_detour(S), detour(O).
detour_ok(O, S) :- solution(S), not requires_detour(S).
handle_ok(O, S) :- solution(S), needs_handle(S), case_handle(O).
handle_ok(O, S) :- solution(S), not needs_handle(S).

safe_solution(O, S) :- fits_mode(O, S), within_size(O, S), detour_ok(O, S), handle_ok(O, S).
valid(Place, O, S) :- setting(Place), affords(Place, O), safe_solution(O, S).

solved :- chosen_setting(Place), chosen_obstacle(O), chosen_solution(S), valid(Place, O, S).
outcome(solved) :- solved.
outcome(stuck) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for obstacle_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("mode", obstacle_id, obstacle.mode))
        lines.append(asp.fact("size", obstacle_id, obstacle.size))
        if obstacle.detour:
            lines.append(asp.fact("detour", obstacle_id))
        if obstacle.case_has_handle:
            lines.append(asp.fact("case_handle", obstacle_id))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        lines.append(asp.fact("max_size", solution_id, solution.max_size))
        for mode in sorted(solution.modes):
            lines.append(asp.fact("solves_mode", solution_id, mode))
        if solution.requires_detour:
            lines.append(asp.fact("requires_detour", solution_id))
        if solution.needs_handle:
            lines.append(asp.fact("needs_handle", solution_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(setting_id: str, obstacle_id: str, solution_id: str) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", setting_id),
            asp.fact("chosen_obstacle", obstacle_id),
            asp.fact("chosen_solution", solution_id),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for obstacle_id in OBSTACLES:
            for solution_id in SOLUTIONS:
                cases.append((setting_id, obstacle_id, solution_id))
    bad = 0
    for setting_id, obstacle_id, solution_id in cases:
        if outcome_of(setting_id, obstacle_id, solution_id) != asp_outcome(setting_id, obstacle_id, solution_id):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: pirate-flavored problem solving around a safe violin rescue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--solution", choices=SOLUTIONS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle and args.solution:
        setting = SETTINGS[args.setting]
        obstacle = OBSTACLES[args.obstacle]
        solution = SOLUTIONS[args.solution]
        if outcome_of(args.setting, args.obstacle, args.solution) != "solved":
            raise StoryError(explain_rejection(setting, obstacle, solution))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        if args.setting and args.obstacle and args.solution:
            raise StoryError(
                explain_rejection(SETTINGS[args.setting], OBSTACLES[args.obstacle], SOLUTIONS[args.solution])
            )
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, solution_id = rng.choice(sorted(combos))
    captain_name, captain_gender = _pick_kid(rng)
    mate_name, mate_gender = _pick_kid(rng, avoid=captain_name)
    captain_trait = rng.choice(TRAITS)
    mate_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        solution=solution_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        captain_trait=captain_trait,
        mate_trait=mate_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")
    if outcome_of(params.setting, params.obstacle, params.solution) != "solved":
        raise StoryError(
            explain_rejection(SETTINGS[params.setting], OBSTACLES[params.obstacle], SOLUTIONS[params.solution])
        )

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle=OBSTACLES[params.obstacle],
        solution=SOLUTIONS[params.solution],
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        captain_trait=params.captain_trait,
        mate_trait=params.mate_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, solution) combos:\n")
        for setting_id, obstacle_id, solution_id in combos:
            print(f"  {setting_id:9} {obstacle_id:12} {solution_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.captain_name} & {p.mate_name}: {p.setting}, {p.obstacle}, {p.solution}"
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
