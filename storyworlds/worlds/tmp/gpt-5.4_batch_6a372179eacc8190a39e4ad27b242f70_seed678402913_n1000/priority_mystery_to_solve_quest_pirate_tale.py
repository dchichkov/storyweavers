#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/priority_mystery_to_solve_quest_pirate_tale.py
=========================================================================

A small storyworld about a child-sized pirate quest: two young pirates find a
mysterious map, discover that an important clue is missing, and decide what must
be the *priority* before they continue. The world model checks whether their
chosen priority tool honestly matches the obstacle in the way. If it does, the
quest becomes a complete mystery-solving story with a safe ending. If not, the
script refuses the combination with a clear StoryError.

The domain is intentionally narrow: a mystery to solve, a short quest, pirate
pretend-play language, and a reasonableness gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/priority_mystery_to_solve_quest_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/priority_mystery_to_solve_quest_pirate_tale.py --obstacle dark_cave --priority lantern
    python storyworlds/worlds/gpt-5.4/priority_mystery_to_solve_quest_pirate_tale.py --obstacle dark_cave --priority wagon
    python storyworlds/worlds/gpt-5.4/priority_mystery_to_solve_quest_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/priority_mystery_to_solve_quest_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/priority_mystery_to_solve_quest_pirate_tale.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mystery:
    id: str
    opening: str
    missing_item: str
    clue_object: str
    answer_object: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    place_phrase: str
    risk_line: str
    solved_by: str
    effect_meter: str
    discovery_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PriorityTool:
    id: str
    label: str
    phrase: str
    use_line: str
    prevents_meter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    ending_image: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    if obstacle.meters["blocked"] < THRESHOLD:
        return out
    sig = ("worry", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__blocked__")
    return out


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    if obstacle.meters["blocked"] < THRESHOLD:
        return out
    if tool.meters["ready"] < THRESHOLD:
        return out
    needed = obstacle.attrs.get("needs")
    solves = tool.attrs.get("solves")
    if needed != solves:
        return out
    sig = ("progress", obstacle.id, tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obstacle.meters["blocked"] = 0.0
    obstacle.meters["cleared"] += 1
    world.get("map").meters["readable"] += 1
    for kid in world.kids():
        kid.memes["courage"] += 1
        kid.memes["relief"] += 1
    out.append("__cleared__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="progress", tag="physical", apply=_r_progress),
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


MYSTERIES = {
    "silver_key": Mystery(
        id="silver_key",
        opening="At low tide, the sand by the old dock was ribbed with tiny wave-lines.",
        missing_item="the silver key",
        clue_object="the crab-shaped mark on the map",
        answer_object="a silver key tied with blue string",
        reveal_line="The missing key had not vanished at all. A curious crab had dragged it into a shell ring beside the clue stone.",
        tags={"key", "mystery"},
    ),
    "bell_note": Mystery(
        id="bell_note",
        opening="Morning light shivered on the harbor water, and the gulls sounded like tiny trumpets.",
        missing_item="the bell note",
        clue_object="the bell drawing on the map",
        answer_object="a rolled paper note tucked inside the harbor bell",
        reveal_line="The note had been hidden where the wind loved to sing. It was curled inside the old bell, dry and safe.",
        tags={"bell", "mystery"},
    ),
    "compass_star": Mystery(
        id="compass_star",
        opening="The cove was quiet except for the hush of foam under the rocks.",
        missing_item="the brass compass star",
        clue_object="the star mark on the map",
        answer_object="a brass compass charm under a flat stone",
        reveal_line="The bright star had slid beneath a flat stone when the night tide bumped it loose from the chest lid.",
        tags={"compass", "mystery"},
    ),
}

OBSTACLES = {
    "dark_cave": Obstacle(
        id="dark_cave",
        label="dark cave",
        place_phrase="the mouth of a little sea cave under the cliff",
        risk_line="The cave was so dark that the last clue looked like a blur. Marching in blind would only make the mystery bigger.",
        solved_by="lantern",
        effect_meter="darkness",
        discovery_line="With a warm circle of light, the wet wall marks turned into arrows pointing to a shell ring.",
        tags={"dark", "cave"},
    ),
    "tide_pool": Obstacle(
        id="tide_pool",
        label="wide tide pool",
        place_phrase="a wide tide pool that cut the sandbar in two",
        risk_line="The clue stone sat across the pool, and the water swirled fast enough to splash small boots. Rushing first would mean a wet, muddled search.",
        solved_by="rope",
        effect_meter="distance",
        discovery_line="They looped the rope to a driftwood post and crossed one careful step at a time to the clue stone.",
        tags={"water", "crossing"},
    ),
    "heavy_chest": Obstacle(
        id="heavy_chest",
        label="heavy chest",
        place_phrase="a salt-stained chest half-buried beyond the dune grass",
        risk_line="They found the chest, but it was too heavy to drag through the sand by hand. Tugging wildly would only tire them before they solved anything.",
        solved_by="wagon",
        effect_meter="weight",
        discovery_line="The little wagon bumped over the sand, and the chest finally rolled into the sun where they could open it.",
        tags={"chest", "heavy"},
    ),
}

PRIORITIES = {
    "lantern": PriorityTool(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        use_line="The lantern made a bright gold pool on the stones, and every mark on the wall woke up.",
        prevents_meter="darkness",
        tags={"light", "lantern"},
    ),
    "rope": PriorityTool(
        id="rope",
        label="rope",
        phrase="a coil of sailor rope",
        use_line="The rope gave them something steady to hold, so the crossing stopped feeling like a slippery dare.",
        prevents_meter="distance",
        tags={"rope", "crossing"},
    ),
    "wagon": PriorityTool(
        id="wagon",
        label="wagon",
        phrase="a red beach wagon",
        use_line="The wagon turned hauling into a clattery little parade instead of a hard pull through the sand.",
        prevents_meter="weight",
        tags={"wagon", "hauling"},
    ),
}

REWARDS = {
    "pearls": Reward(
        id="pearls",
        label="pearls",
        phrase="a tin of moon-bright pearls",
        ending_image="The pearls clicked softly while the tide breathed in and out beside them.",
        tags={"treasure"},
    ),
    "stickers": Reward(
        id="stickers",
        label="star stickers",
        phrase="a packet of star stickers and a chocolate coin",
        ending_image="The stickers flashed in the sun like tiny captain stars.",
        tags={"treasure"},
    ),
    "shells": Reward(
        id="shells",
        label="painted shells",
        phrase="three painted shells and a shiny coin",
        ending_image="The painted shells glowed pink and blue in their open palms.",
        tags={"treasure"},
    ),
}


def valid_combo(obstacle_id: str, priority_id: str) -> bool:
    obstacle = OBSTACLES[obstacle_id]
    tool = PRIORITIES[priority_id]
    return obstacle.solved_by == tool.id and obstacle.effect_meter == tool.prevents_meter


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mystery_id in MYSTERIES:
        for obstacle_id in OBSTACLES:
            for priority_id in PRIORITIES:
                for reward_id in REWARDS:
                    if valid_combo(obstacle_id, priority_id):
                        combos.append((mystery_id, obstacle_id, priority_id, reward_id))
    return combos


@dataclass
class StoryParams:
    mystery: str
    obstacle: str
    priority: str
    reward: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    keeper_type: str
    captain_trait: str
    mate_trait: str
    seed: Optional[int] = None


def introduce(world: World, captain: Entity, mate: Entity, keeper: Entity, mystery: Mystery) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"{mystery.opening} {captain.id} and {mate.id} had turned the shore into a pirate kingdom all by themselves."
    )
    world.say(
        f'{captain.id} was Captain {captain.id}, and {mate.id} was First Mate {mate.id}. '
        f'Their map was wrinkled, their pockets were sandy, and the day felt ready for a quest.'
    )
    world.say(
        f"Harbor {keeper.label_word} had left them one promise: if they solved the dockside mystery, a small treasure would be theirs."
    )


def map_mystery(world: World, captain: Entity, mate: Entity, mystery: Mystery) -> None:
    world.get("map").meters["important"] += 1
    world.say(
        f"But when they spread the map on an overturned bucket, one clue was missing. "
        f"The place where {mystery.clue_object} should have told them more was smeared by salt water."
    )
    world.say(
        f'"That means we have a real mystery to solve," {mate.id} said. '
        f'"We must find {mystery.missing_item} before we can claim the treasure."'
    )


def choose_priority(world: World, captain: Entity, mate: Entity, obstacle: Obstacle, tool: PriorityTool) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["ready"] += 1
    world.say(
        f"They hurried to {obstacle.place_phrase}, and the trouble there showed itself at once. {obstacle.risk_line}"
    )
    world.get("obstacle").meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{captain.id} drew a long pirate breath. "Before we chase treasure, we need a priority," {captain.pronoun()} said.'
    )
    world.say(
        f'"Our priority is {tool.phrase}," {mate.id} answered. "A good crew solves the hard part first."'
    )


def overcome(world: World, captain: Entity, mate: Entity, obstacle: Obstacle, tool: PriorityTool) -> None:
    world.para()
    propagate(world, narrate=False)
    world.say(tool.use_line)
    world.say(obstacle.discovery_line)
    world.say(
        f"Now the map made sense again, and the two young pirates could follow the last clue instead of guessing."
    )
    world.get("map").meters["solved"] += 1
    for kid in (captain, mate):
        kid.memes["confidence"] += 1


def solve_reveal(world: World, mystery: Mystery, reward: Reward, captain: Entity, mate: Entity) -> None:
    world.para()
    world.say(
        f"Under the final marker they found {mystery.answer_object}, and with it the truth of the puzzle. {mystery.reveal_line}"
    )
    world.say(
        f"Beside it waited {reward.phrase}. The quest was over, not because they ran fastest, but because they chose the right thing first."
    )
    world.say(
        f'"Pirates with good priorities solve mysteries," {mate.id} said with a grin.'
    )
    world.say(
        f"{captain.id} tucked the map under one arm while {reward.ending_image} The harbor no longer felt puzzling. It felt earned."
    )
    world.facts["solved"] = True


def tell(
    mystery: Mystery,
    obstacle: Obstacle,
    tool: PriorityTool,
    reward: Reward,
    captain_name: str,
    captain_gender: str,
    mate_name: str,
    mate_gender: str,
    keeper_type: str,
    captain_trait: str,
    mate_trait: str,
) -> World:
    world = World()
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        label=captain_name,
        traits=[captain_trait, "brave"],
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        role="mate",
        label=mate_name,
        traits=[mate_trait, "careful"],
    ))
    keeper = world.add(Entity(
        id="Keeper",
        kind="character",
        type=keeper_type,
        role="keeper",
        label="the keeper",
    ))
    world.add(Entity(id="map", type="map", label="map"))
    world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=obstacle.label,
        attrs={"needs": obstacle.solved_by},
    ))
    world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        attrs={"solves": tool.id},
    ))
    world.add(Entity(id="reward", type="reward", label=reward.label))

    introduce(world, captain, mate, keeper, mystery)
    world.para()
    map_mystery(world, captain, mate, mystery)
    choose_priority(world, captain, mate, obstacle, tool)
    overcome(world, captain, mate, obstacle, tool)
    solve_reveal(world, mystery, reward, captain, mate)

    world.facts.update(
        mystery=mystery,
        obstacle_cfg=obstacle,
        priority_cfg=tool,
        reward_cfg=reward,
        captain=captain,
        mate=mate,
        keeper=keeper,
        solved=world.get("map").meters["solved"] >= THRESHOLD,
        captain_worry=captain.memes["worry"] >= THRESHOLD,
        map_readable=world.get("map").meters["readable"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    mystery = f["mystery"]
    obstacle = f["obstacle_cfg"]
    tool = f["priority_cfg"]
    return [
        'Write a short pirate tale for a 3-to-5-year-old that includes the word "priority" and centers on a mystery to solve.',
        f"Tell a quest story where {captain.id} and {mate.id} follow a pirate map, discover that {mystery.missing_item} is missing, and choose {tool.label} as their priority before facing {obstacle.label}.",
        f"Write a gentle mystery-and-quest story with child pirates who learn that solving treasure problems starts with the right priority, not just hurrying.",
    ]


def pair_noun(captain: Entity, mate: Entity) -> str:
    if captain.type == "boy" and mate.type == "boy":
        return "two young pirates"
    if captain.type == "girl" and mate.type == "girl":
        return "two young pirates"
    return "a young pirate pair"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    keeper = f["keeper"]
    mystery = f["mystery"]
    obstacle = f["obstacle_cfg"]
    tool = f["priority_cfg"]
    reward = f["reward_cfg"]
    pair = pair_noun(captain, mate)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain.id} and {mate.id}, and Harbor {keeper.label_word} who promised them a treasure if they solved the mystery.",
        ),
        (
            "What was the mystery?",
            f"The map had lost the clue about {mystery.missing_item}, so the children did not know exactly where to look next. That missing clue turned their treasure hunt into a real mystery to solve.",
        ),
        (
            f"What did {captain.id} say was the priority?",
            f"{captain.id} said they needed a priority before chasing treasure, and the crew chose {tool.label}. They picked it first because the problem at {obstacle.place_phrase} could not be solved safely without it.",
        ),
        (
            f"Why did they need {tool.label}?",
            f"They needed {tool.label} because {obstacle.risk_line} The tool changed the obstacle from a confusing problem into something they could handle.",
        ),
        (
            "How did they solve the mystery?",
            f"They used {tool.label} to get past {obstacle.label}, which let them read the last clue properly. After that, they found {mystery.answer_object} and understood what had really happened.",
        ),
        (
            "How did the story end?",
            f"They solved the pirate mystery and found {reward.phrase}. The ending shows that choosing the right priority helped them finish the quest wisely, not just quickly.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "priority": [
        (
            "What does priority mean?",
            "A priority is the thing you decide is most important to do first. It helps you solve a problem in a smart order.",
        )
    ],
    "map": [
        (
            "What does a treasure map do?",
            "A treasure map gives clues about where to go and what to look for. It helps adventurers follow a path instead of wandering."
        )
    ],
    "lantern": [
        (
            "What is a lantern for?",
            "A lantern gives light in a dark place so you can see safely. Pirates and campers use one when sunshine cannot reach."
        )
    ],
    "rope": [
        (
            "What is a rope useful for?",
            "A rope helps people pull, tie, climb, or cross carefully. It gives steady help when a place is slippery or far."
        )
    ],
    "wagon": [
        (
            "What is a wagon good for?",
            "A wagon helps carry heavy things without making your arms do all the work. Wheels make hauling easier."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip with a purpose, like finding something important or solving a problem on the way."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something puzzling that you do not understand yet. You solve it by noticing clues and thinking carefully."
        )
    ],
    "tide": [
        (
            "What is a tide pool?",
            "A tide pool is a little pool of seawater left behind by the ocean. It can be pretty, but it can also be slippery and deep for small feet."
        )
    ],
    "cave": [
        (
            "Why is a dark cave hard to explore?",
            "A dark cave is hard to explore because you cannot see where to step or what clues are around you. Good light makes it safer and clearer."
        )
    ],
    "treasure": [
        (
            "What is treasure?",
            "Treasure is something special people are glad to find, like coins, shells, or jewels. In stories, treasure often comes at the end of a quest."
        )
    ],
}
KNOWLEDGE_ORDER = ["priority", "mystery", "quest", "map", "lantern", "rope", "wagon", "tide", "cave", "treasure"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"priority", "mystery", "quest", "map", "treasure"}
    obstacle = world.facts["obstacle_cfg"]
    tool = world.facts["priority_cfg"]
    if obstacle.id == "dark_cave":
        tags.add("cave")
    if obstacle.id == "tide_pool":
        tags.add("tide")
    tags |= tool.tags
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(obstacle_id: str, priority_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    tool = PRIORITIES[priority_id]
    correct = obstacle.solved_by
    return (
        f"(No story: {tool.label} is not the right priority for {obstacle.label}. "
        f"That obstacle needs {correct}, so the quest would not honestly move forward.)"
    )


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]
TRAITS = ["brave", "careful", "curious", "thoughtful", "steady", "eager"]


CURATED = [
    StoryParams(
        mystery="silver_key",
        obstacle="dark_cave",
        priority="lantern",
        reward="pearls",
        captain_name="Tom",
        captain_gender="boy",
        mate_name="Lily",
        mate_gender="girl",
        keeper_type="father",
        captain_trait="eager",
        mate_trait="thoughtful",
    ),
    StoryParams(
        mystery="bell_note",
        obstacle="tide_pool",
        priority="rope",
        reward="shells",
        captain_name="Mia",
        captain_gender="girl",
        mate_name="Ben",
        mate_gender="boy",
        keeper_type="mother",
        captain_trait="brave",
        mate_trait="steady",
    ),
    StoryParams(
        mystery="compass_star",
        obstacle="heavy_chest",
        priority="wagon",
        reward="stickers",
        captain_name="Leo",
        captain_gender="boy",
        mate_name="Nora",
        mate_gender="girl",
        keeper_type="father",
        captain_trait="curious",
        mate_trait="careful",
    ),
]


ASP_RULES = r"""
valid(M, O, P, R) :- mystery(M), obstacle(O), priority(P), reward(R),
                     solved_by(O, P), effect_meter(O, E), prevents_meter(P, E).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mystery_id in MYSTERIES:
        lines.append(asp.fact("mystery", mystery_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("solved_by", obstacle_id, obstacle.solved_by))
        lines.append(asp.fact("effect_meter", obstacle_id, obstacle.effect_meter))
    for priority_id, tool in PRIORITIES.items():
        lines.append(asp.fact("priority", priority_id))
        lines.append(asp.fact("prevents_meter", priority_id, tool.prevents_meter))
    for reward_id in REWARDS:
        lines.append(asp.fact("reward", reward_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))

    smoke_cases = [CURATED[0]]
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(11)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 11
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Random smoke test failed: empty story.)")
        print("OK: random generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate mystery quest storyworld where the crew must choose the right priority."
    )
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--priority", choices=sorted(PRIORITIES))
    ap.add_argument("--reward", choices=sorted(REWARDS))
    ap.add_argument("--captain-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.priority and not valid_combo(args.obstacle, args.priority):
        raise StoryError(explain_rejection(args.obstacle, args.priority))

    combos = [
        combo for combo in valid_combos()
        if (args.mystery is None or combo[0] == args.mystery)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.priority is None or combo[2] == args.priority)
        and (args.reward is None or combo[3] == args.reward)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mystery_id, obstacle_id, priority_id, reward_id = rng.choice(sorted(combos))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    captain_name = args.captain_name or pick_name(rng, captain_gender)
    mate_name = args.mate_name or pick_name(rng, mate_gender, avoid=captain_name)
    keeper_type = args.keeper or rng.choice(["mother", "father"])
    captain_trait = rng.choice(TRAITS)
    mate_trait = rng.choice([trait for trait in TRAITS if trait != captain_trait] or TRAITS)
    return StoryParams(
        mystery=mystery_id,
        obstacle=obstacle_id,
        priority=priority_id,
        reward=reward_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        keeper_type=keeper_type,
        captain_trait=captain_trait,
        mate_trait=mate_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.priority not in PRIORITIES:
        raise StoryError(f"(Unknown priority: {params.priority})")
    if params.reward not in REWARDS:
        raise StoryError(f"(Unknown reward: {params.reward})")
    if not valid_combo(params.obstacle, params.priority):
        raise StoryError(explain_rejection(params.obstacle, params.priority))

    world = tell(
        mystery=MYSTERIES[params.mystery],
        obstacle=OBSTACLES[params.obstacle],
        tool=PRIORITIES[params.priority],
        reward=REWARDS[params.reward],
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        keeper_type=params.keeper_type,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mystery, obstacle, priority, reward) combos:\n")
        for mystery_id, obstacle_id, priority_id, reward_id in combos:
            print(f"  {mystery_id:13} {obstacle_id:11} {priority_id:8} {reward_id}")
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
            header = f"### {p.captain_name} & {p.mate_name}: {p.mystery}, {p.obstacle}, priority={p.priority}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
