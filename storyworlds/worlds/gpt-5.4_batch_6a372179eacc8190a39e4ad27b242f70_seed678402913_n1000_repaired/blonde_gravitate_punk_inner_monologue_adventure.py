#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/blonde_gravitate_punk_inner_monologue_adventure.py
=============================================================================

A standalone storyworld for a tiny child-facing adventure domain built from the
seed words "blonde", "gravitate", and "punk", with explicit inner monologue.

Premise
-------
A blonde child keeps gravitating toward high lookout places. One misty day, the
camp needs a signal from an old landmark before the fog thickens. A scruffy,
punk little animal companion helps the child face one path obstacle. Some
traits lead the child to listen and move carefully; others lead to a rushed
mistake, a small snag, and a wiser recovery.

Run it
------
python storyworlds/worlds/gpt-5.4/blonde_gravitate_punk_inner_monologue_adventure.py
python storyworlds/worlds/gpt-5.4/blonde_gravitate_punk_inner_monologue_adventure.py --landmark tower --obstacle creek --tool pole
python storyworlds/worlds/gpt-5.4/blonde_gravitate_punk_inner_monologue_adventure.py --tool lantern --obstacle creek
python storyworlds/worlds/gpt-5.4/blonde_gravitate_punk_inner_monologue_adventure.py --all
python storyworlds/worlds/gpt-5.4/blonde_gravitate_punk_inner_monologue_adventure.py --verify
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
HEED_TRAITS = {"careful", "thoughtful", "steady"}


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type or self.label)


@dataclass
class Landmark:
    id: str
    place: str
    opening: str
    signal_tool: str
    signal_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    scene: str
    warning: str
    snag: str
    careful: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    matches: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    phrase: str
    call: str
    clue: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_rush_snag(world: World) -> list[str]:
    hero = world.entities.get("hero")
    path = world.entities.get("path")
    if hero is None or path is None:
        return []
    if hero.memes["rushing"] < THRESHOLD:
        return []
    if ("snag", path.id) in world.fired:
        return []
    world.fired.add(("snag", path.id))
    hero.meters["snagged"] += 1
    hero.memes["fear"] += 1
    return ["__snag__"]


def _r_reach_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    landmark = world.entities.get("landmark")
    if hero is None or landmark is None:
        return []
    if hero.meters["at_landmark"] < THRESHOLD:
        return []
    if ("relief", landmark.id) in world.fired:
        return []
    world.fired.add(("relief", landmark.id))
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="rush_snag", apply=_r_rush_snag),
    Rule(name="reach_relief", apply=_r_reach_relief),
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
            if not line.startswith("__"):
                world.say(line)
    return produced


LANDMARKS = {
    "tower": Landmark(
        id="tower",
        place="the old watchtower on the hill",
        opening="From camp, the old watchtower stood above the pines like a waiting finger.",
        signal_tool="bell",
        signal_line="When the bell rang from the top, the people at camp would know which way to walk back through the fog.",
        ending_image="The bell sang out over the gray trees, and tiny answers floated back from camp.",
        tags={"tower", "bell"},
    ),
    "arch": Landmark(
        id="arch",
        place="the stone arch above the meadow",
        opening="Beyond camp, the stone arch on the ridge shone pale against the mist.",
        signal_tool="flag",
        signal_line="When the flag fluttered from the arch, the people below would spot the safe trail home.",
        ending_image="The flag snapped in the wind, and the meadow below seemed to smile back.",
        tags={"arch", "flag"},
    ),
    "beacon": Landmark(
        id="beacon",
        place="the cliff beacon by the sea path",
        opening="Past camp, the cliff beacon blinked softly where the sky met the water.",
        signal_tool="mirror",
        signal_line="If someone reached it and tipped the mirror just right, the lost hikers down the path would see the flash.",
        ending_image="One bright flash skipped across the mist, and a cheerful wave rose from far below.",
        tags={"beacon", "mirror"},
    ),
}

OBSTACLES = {
    "creek": Obstacle(
        id="creek",
        label="creek",
        scene="a cold creek hurried across the trail, popping around slick stones",
        warning="The stones looked shiny and quick, the kind that liked to send muddy shoes skidding sideways.",
        snag="One foot slipped, cold water splashed up, and the path suddenly felt much bigger than before.",
        careful="The pole let the child feel each step before trusting it, and the creek stopped acting like a trick.",
        fix="With the right balance and smaller steps, the creek became a puzzle instead of a trap.",
        tags={"creek", "water"},
    ),
    "brambles": Obstacle(
        id="brambles",
        label="brambles",
        scene="a wall of brambles leaned over the trail, full of hooks and tiny thorns",
        warning="The thorns looked sleepy from far away, but close up they were grabby little fingers.",
        snag="A thorn caught at a sleeve, then another tugged at a sock, and the child froze in the scratchy hedge.",
        careful="The thick cloak turned the prickly hedge into a pushable curtain.",
        fix="Covered up and moving slowly, the brambles had nothing left to snatch.",
        tags={"brambles", "thorns"},
    ),
    "tunnel": Obstacle(
        id="tunnel",
        label="tunnel",
        scene="a short fallen tunnel cut through the hill, dark enough to swallow the sunny parts of a thought",
        warning="Inside, every drip sounded like a footstep, and the turns all looked the same.",
        snag="The dark pressed close, and for one breath the child could not tell which way the path bent.",
        careful="The lantern painted warm circles on the stone so each bend could be seen before it surprised anyone.",
        fix="Once light reached the walls, the tunnel stopped pretending it was endless.",
        tags={"tunnel", "dark"},
    ),
}

TOOLS = {
    "pole": Tool(
        id="pole",
        label="walking pole",
        phrase="a smooth walking pole",
        matches={"creek"},
        tags={"pole", "balance"},
    ),
    "cloak": Tool(
        id="cloak",
        label="patchwork cloak",
        phrase="a patchwork cloak",
        matches={"brambles"},
        tags={"cloak", "cover"},
    ),
    "lantern": Tool(
        id="lantern",
        label="tin lantern",
        phrase="a tin lantern",
        matches={"tunnel"},
        tags={"lantern", "light"},
    ),
    "rope": Tool(
        id="rope",
        label="coiled rope",
        phrase="a coiled rope",
        matches=set(),
        tags={"rope"},
    ),
}

COMPANIONS = {
    "starling": Companion(
        id="starling",
        label="punk starling",
        phrase="a punk starling with spiky black feathers",
        call="Tzik-tzik!",
        clue="It kept hopping to the steady places and tilting its head whenever the trail looked tricky.",
        tags={"bird", "punk"},
    ),
    "squirrel": Companion(
        id="squirrel",
        label="punk squirrel",
        phrase="a punk squirrel with a ragged tail and bold whiskers",
        call="Chrrr!",
        clue="It chattered at the safe gaps and twitched whenever the child leaned toward trouble.",
        tags={"squirrel", "punk"},
    ),
    "goat": Companion(
        id="goat",
        label="punk goat",
        phrase="a punk goat kid with a tuft sticking up like a tiny mohawk",
        call="Maa!",
        clue="It stamped at the firm ground and refused to step where the path was foolish.",
        tags={"goat", "punk"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nell", "Ruby", "Tessa", "Wren"]
BOY_NAMES = ["Finn", "Jory", "Milo", "Toby", "Arlo", "Reed"]
TRAITS = ["careful", "thoughtful", "steady", "bold", "restless", "hasty"]


@dataclass
class StoryParams:
    landmark: str
    obstacle: str
    tool: str
    companion: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        landmark="tower",
        obstacle="creek",
        tool="pole",
        companion="starling",
        name="Mara",
        gender="girl",
        parent="aunt",
        trait="careful",
    ),
    StoryParams(
        landmark="arch",
        obstacle="brambles",
        tool="cloak",
        companion="goat",
        name="Finn",
        gender="boy",
        parent="father",
        trait="bold",
    ),
    StoryParams(
        landmark="beacon",
        obstacle="tunnel",
        tool="lantern",
        companion="squirrel",
        name="Lina",
        gender="girl",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        landmark="tower",
        obstacle="tunnel",
        tool="lantern",
        companion="starling",
        name="Milo",
        gender="boy",
        parent="uncle",
        trait="restless",
    ),
    StoryParams(
        landmark="arch",
        obstacle="creek",
        tool="pole",
        companion="goat",
        name="Ruby",
        gender="girl",
        parent="mother",
        trait="steady",
    ),
]


def valid_combo(obstacle_id: str, tool_id: str) -> bool:
    return obstacle_id in OBSTACLES and tool_id in TOOLS and obstacle_id in TOOLS[tool_id].matches


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for landmark_id in LANDMARKS:
        for obstacle_id in OBSTACLES:
            for tool_id in TOOLS:
                if valid_combo(obstacle_id, tool_id):
                    out.append((landmark_id, obstacle_id, tool_id))
    return out


def explain_rejection(obstacle_id: str, tool_id: str) -> str:
    if obstacle_id not in OBSTACLES:
        return "(No story: unknown obstacle.)"
    if tool_id not in TOOLS:
        return "(No story: unknown tool.)"
    obstacle = OBSTACLES[obstacle_id]
    tool = TOOLS[tool_id]
    return (
        f"(No story: {tool.phrase} does not honestly solve the {obstacle.label}. "
        f"Pick a tool that fits the obstacle, such as "
        f"{', '.join(sorted(tid for tid, t in TOOLS.items() if obstacle_id in t.matches))}.)"
    )


def would_heed(trait: str) -> bool:
    return trait in HEED_TRAITS


def outcome_of(params: StoryParams) -> str:
    return "careful_success" if would_heed(params.trait) else "snag_then_success"


def introduce(world: World, hero: Entity, landmark: Landmark, parent: Entity, companion: Companion) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} was a blonde little {hero.type} who always seemed to gravitate toward the highest thing in sight."
    )
    world.say(
        f"{landmark.opening} {hero.id}'s {parent.label_word} pointed at it and said the camp needed help before the fog grew thicker."
    )
    world.say(
        f"At {hero.id}'s heel trotted {companion.phrase}. {companion.clue}"
    )


def mission(world: World, hero: Entity, landmark: Landmark) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'Today\'s job felt like a real adventure: reach {landmark.place} and use the {landmark.signal_tool}. {landmark.signal_line}'
    )


def inner_pull(world: World, hero: Entity, obstacle: Obstacle, tool: Tool, companion: Companion) -> None:
    world.say(
        f"Soon the trail narrowed until {obstacle.scene}. {obstacle.warning}"
    )
    world.say(
        f'{companion.call} {hero.id} looked at the obstacle, then at {tool.phrase}. '
        f'"I keep wanting to rush because rushing looks brave," {hero.id} thought. '
        f'"But maybe real bravery is noticing what the trail is telling me."'
    )


def choose_careful(world: World, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    hero.memes["listening"] += 1
    world.say(
        f'{hero.id} took a slow breath. "I do not have to race the hill," {hero.pronoun()} thought. '
        f'"I can move the smart way."'
    )
    world.say(
        f"With {tool.phrase}, {hero.id} crossed the {obstacle.label} carefully. {obstacle.careful}"
    )


def choose_rush(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["rushing"] += 1
    hero.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} felt the old pull of hurry. "If I dash now, I will look like a storybook hero," {hero.pronoun()} thought.'
    )
    world.say(
        f"But the trail was not interested in looking impressed. {obstacle.snag}"
    )


def recover(world: World, hero: Entity, obstacle: Obstacle, tool: Tool, companion: Companion) -> None:
    hero.memes["humility"] += 1
    hero.memes["listening"] += 1
    world.say(
        f'{companion.call} The little {companion.label} hopped back to {tool.phrase}, as if reminding {hero.pronoun("object")} what had been wise all along.'
    )
    world.say(
        f'"All right," {hero.id} thought, heart thumping. "I do not need to win against the path. I need to understand it."'
    )
    world.say(
        f"{hero.id} tried again with {tool.phrase}. {obstacle.fix}"
    )


def arrive(world: World, hero: Entity, landmark: Landmark) -> None:
    hero.meters["at_landmark"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Step by step, the trail opened at last, and {hero.id} reached {landmark.place}."
    )


def signal(world: World, hero: Entity, landmark: Landmark, parent: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} lifted the {landmark.signal_tool} and did exactly what the camp had hoped."
    )
    world.say(
        f"{landmark.ending_image} Far away, {hero.id}'s {parent.label_word} answered with a happy shout."
    )


def reflection(world: World, hero: Entity, outcome: str, companion: Companion) -> None:
    if outcome == "careful_success":
        world.say(
            f'"Good," {hero.id} thought as {companion.label} bobbed beside {hero.pronoun("object")}. '
            f'"I can still gravitate toward adventure without letting hurry boss me around."'
        )
    else:
        world.say(
            f'"Now I know," {hero.id} thought as {companion.label} nuzzled close. '
            f'"Adventure is not about acting like a punk storm. It is about learning, steadying myself, and trying again."'
        )


def tell(
    landmark: Landmark,
    obstacle: Obstacle,
    tool: Tool,
    companion_cfg: Companion,
    name: str,
    gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=gender,
            label=name,
            phrase=name,
            role="hero",
            traits=[trait, "blonde"],
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label=f"the {parent_type}",
            phrase=f"the {parent_type}",
            role="parent",
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            type="animal",
            label=companion_cfg.label,
            phrase=companion_cfg.phrase,
            role="companion",
            tags=set(companion_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="path",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.scene,
            role="obstacle",
            tags=set(obstacle.tags),
        )
    )
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            phrase=tool.phrase,
            role="tool",
            tags=set(tool.tags),
        )
    )
    world.add(
        Entity(
            id="landmark",
            kind="thing",
            type="landmark",
            label=landmark.place,
            phrase=landmark.place,
            role="landmark",
            tags=set(landmark.tags),
        )
    )

    introduce(world, hero, landmark, parent, companion_cfg)
    mission(world, hero, landmark)

    world.para()
    inner_pull(world, hero, obstacle, tool, companion_cfg)

    outcome = "careful_success" if would_heed(trait) else "snag_then_success"
    if outcome == "careful_success":
        choose_careful(world, hero, obstacle, tool)
    else:
        choose_rush(world, hero, obstacle)
        recover(world, hero, obstacle, tool, companion_cfg)

    world.para()
    arrive(world, hero, landmark)
    signal(world, hero, landmark, parent)
    reflection(world, hero, outcome, companion_cfg)

    world.facts.update(
        hero=hero,
        hero_name=name,
        parent=parent,
        landmark_cfg=landmark,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        companion_cfg=companion_cfg,
        outcome=outcome,
        heed=outcome == "careful_success",
        snagged=hero.meters["snagged"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    landmark = f["landmark_cfg"]
    obstacle = f["obstacle_cfg"]
    companion = f["companion_cfg"]
    outcome = f["outcome"]
    if outcome == "careful_success":
        return [
            'Write a short adventure story for a 3-to-5-year-old that includes the words "blonde", "gravitate", and "punk", and uses inner monologue.',
            f"Tell an adventure about a blonde child named {f['hero_name']} who seems to gravitate toward high places, travels with a {companion.label}, and reaches {landmark.place} by thinking carefully.",
            f"Write a gentle quest where {hero.pronoun('possessive')} inner thoughts help {f['hero_name']} cross a {obstacle.label} the smart way and finish with a bright signal from {landmark.place}.",
        ]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "blonde", "gravitate", and "punk", and uses inner monologue.',
        f"Tell an adventure where a blonde child named {f['hero_name']} first rushes, gets briefly stuck at a {obstacle.label}, then listens to a {companion.label} and tries again.",
        f"Write a child-friendly quest in which inner monologue turns a mistake into wisdom before the hero reaches {landmark.place} and sends the signal.",
    ]


KNOWLEDGE = {
    "tower": [
        (
            "What is a watchtower?",
            "A watchtower is a tall place where you can look far away. People use high places like that to see paths, weather, or friends below.",
        )
    ],
    "arch": [
        (
            "What is a stone arch?",
            "A stone arch is a curved shape made of rock or blocks. If it stands on a hill, people can see it from far away.",
        )
    ],
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a signal place or light that helps people notice where to go. A bright flash or glow can guide someone from far away.",
        )
    ],
    "water": [
        (
            "Why can creek stones be slippery?",
            "Water makes smooth stones slick. Your feet can slide unless you slow down and balance carefully.",
        )
    ],
    "thorns": [
        (
            "What are thorns for?",
            "Thorns are sharp little spikes on some plants. They help protect the plant, but they can catch clothes and scratch skin.",
        )
    ],
    "dark": [
        (
            "Why does a lantern help in a tunnel?",
            "A lantern makes light so you can see walls, bends, and where to step. Seeing clearly helps your body stay calm and careful.",
        )
    ],
    "balance": [
        (
            "How can a walking pole help?",
            "A walking pole gives you another point of balance. It helps you test the ground before putting all your weight down.",
        )
    ],
    "cover": [
        (
            "Why would a thick cloak help with brambles?",
            "A thick cloak can cover your clothes and skin so small thorns grab less. That makes it easier to move slowly through prickly plants.",
        )
    ],
    "light": [
        (
            "What does light do when you feel unsure?",
            "Light helps your eyes understand the place around you. When you can see better, it is easier to choose safe steps.",
        )
    ],
    "punk": [
        (
            "What does punk mean in this story?",
            "Here, punk means scruffy, bold, and a little wild-looking. It does not mean mean; it just gives the animal a spiky, lively style.",
        )
    ],
}
KNOWLEDGE_ORDER = ["tower", "arch", "beacon", "water", "thorns", "dark", "balance", "cover", "light", "punk"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    landmark = f["landmark_cfg"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    companion = f["companion_cfg"]
    name = f["hero_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a blonde child named {name}, a {companion.label}, and {name}'s {parent.label_word}. They are trying to reach {landmark.place} for an important signal.",
        ),
        (
            f"Why did {name} go to {landmark.place}?",
            f"{name} went there because the camp needed someone to use the {landmark.signal_tool} before the fog grew thicker. The signal would help people know the safe way back.",
        ),
        (
            f"What obstacle blocked the trail?",
            f"The trail was blocked by a {obstacle.label}. That is the problem that turned the walk into a real adventure.",
        ),
        (
            f"How did inner monologue matter in the story?",
            f"{name} talked silently inside {hero.pronoun('possessive')} own mind about wanting to rush and about what real bravery meant. Those thoughts shaped whether {hero.pronoun()} acted carefully right away or learned from a mistake first.",
        ),
    ]
    if f["outcome"] == "careful_success":
        qa.append(
            (
                f"How did {name} solve the problem?",
                f"{name} listened to the trail and used {tool.phrase} to cross the {obstacle.label} carefully. Moving slowly made the obstacle manageable instead of scary.",
            )
        )
        qa.append(
            (
                f"Why does the story use the word gravitate?",
                f"It says {name} seemed to gravitate toward high places because {hero.pronoun()} loved lookout spots and adventures. Later, {name} also learns not to gravitate toward hurry just because hurry feels exciting.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {name} rushed?",
                f"{name} got briefly snagged at the {obstacle.label} and felt a burst of fear. That small scare taught {hero.pronoun('object')} that speed was not the same as wisdom.",
            )
        )
        qa.append(
            (
                f"How did {name} fix the mistake?",
                f"After the snag, {name} listened to the {companion.label} and tried again with {tool.phrase}. The second try worked because {hero.pronoun()} stopped fighting the path and started understanding it.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the signal from {landmark.place} reaching the camp. The ending image proves that {name} changed from merely eager into truly adventure-ready.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["landmark_cfg"].tags) | set(f["obstacle_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["companion_cfg"].tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(O, T) :- obstacle(O), tool(T), match(T, O).
valid(L, O, T) :- landmark(L), fits(O, T).
heeds(Trait) :- trait(Trait), heed_trait(Trait).

outcome(careful_success) :- chosen_trait(Trait), heeds(Trait).
outcome(snag_then_success) :- chosen_trait(Trait), not heeds(Trait).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for landmark_id in LANDMARKS:
        lines.append(asp.fact("landmark", landmark_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for obstacle_id in sorted(tool.matches):
            lines.append(asp.fact("match", tool_id, obstacle_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(HEED_TRAITS):
        lines.append(asp.fact("heed_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    _ = sample.story
    _ = sample.to_dict()
    if sample.world is None:
        raise StoryError("Smoke test failed: generated sample is missing its world.")


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

    cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        params = resolve_params(default_args, random.Random(7))
        cases.append(params)
    except StoryError as err:
        rc = 1
        print("Default resolve_params failed during verify:", err)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        _smoke_emit(sample)
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print("SMOKE TEST FAILED:", err)

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a blonde child, a punk companion, inner monologue, and a small adventure."
    )
    ap.add_argument("--landmark", choices=LANDMARKS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool and not valid_combo(args.obstacle, args.tool):
        raise StoryError(explain_rejection(args.obstacle, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.landmark is None or combo[0] == args.landmark)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    landmark_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    companion_id = args.companion or rng.choice(sorted(COMPANIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        landmark=landmark_id,
        obstacle=obstacle_id,
        tool=tool_id,
        companion=companion_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.landmark not in LANDMARKS:
        raise StoryError(f"(No story: unknown landmark '{params.landmark}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{params.tool}'.)")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(No story: unknown companion '{params.companion}'.)")
    if not valid_combo(params.obstacle, params.tool):
        raise StoryError(explain_rejection(params.obstacle, params.tool))

    world = tell(
        landmark=LANDMARKS[params.landmark],
        obstacle=OBSTACLES[params.obstacle],
        tool=TOOLS[params.tool],
        companion_cfg=COMPANIONS[params.companion],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.name),
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
        print(f"{len(combos)} compatible (landmark, obstacle, tool) combos:\n")
        for landmark_id, obstacle_id, tool_id in combos:
            print(f"  {landmark_id:8} {obstacle_id:10} {tool_id}")
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
            header = f"### {p.name}: {p.obstacle} -> {p.landmark} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
