#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/thrill_pish_problem_solving_myth.py
==============================================================

A standalone storyworld about a child-sized mythic quest: a village spring goes
silent, a mountain basin is blocked, and a young hero solves the problem by
choosing a helper and a tool that truly fit the obstacle.

The seed asks for:
- the words "thrill" and "pish"
- a Problem Solving story
- a style close to Myth

So this world models a small mythic domain with concrete state:
water can be blocked, paths can be steep, tools can reach or cut, helpers can
climb or carry, and the ending image proves that the solved world now flows
again.

Run it
------
    python storyworlds/worlds/gpt-5.4/thrill_pish_problem_solving_myth.py
    python storyworlds/worlds/gpt-5.4/thrill_pish_problem_solving_myth.py --all
    python storyworlds/worlds/gpt-5.4/thrill_pish_problem_solving_myth.py --trace
    python storyworlds/worlds/gpt-5.4/thrill_pish_problem_solving_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/thrill_pish_problem_solving_myth.py --verify
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

# Make shared result containers importable when this nested script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
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
        female = {"girl", "woman", "mother", "goddess"}
        male = {"boy", "man", "father", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    spring_name: str
    height_word: str
    sky_image: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    symptom: str
    clue: str
    fix_verb: str
    needs: str                  # "hook" | "cut" | "lift"
    reach: int
    steep: bool
    danger_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    does: str                   # "hook" | "cut" | "lift"
    reach: int
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    climbs: bool
    carries: bool
    line: str
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


def solution_possible(obstacle: Obstacle, tool: Tool, helper: Helper) -> bool:
    if tool.does != obstacle.needs:
        return False
    if tool.reach < obstacle.reach:
        return False
    if obstacle.steep and not helper.climbs:
        return False
    if obstacle.needs == "lift" and not helper.carries:
        return False
    return True


def _r_water_returns(world: World) -> list[str]:
    basin = world.get("basin")
    spring = world.get("spring")
    hero = world.get("hero")
    if basin.meters["opened"] < THRESHOLD:
        return []
    sig = ("water_returns",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spring.meters["flow"] += 1
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="water_returns", tag="physical", apply=_r_water_returns),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            world.say(bit)
    return produced


SETTINGS = {
    "cedar_valley": Setting(
        id="cedar_valley",
        place="Cedar Valley",
        spring_name="the Silver Spring",
        height_word="a steep moonlit ledge",
        sky_image="clouds moving like sheep across the stars",
        closing_image="children filling bright cups beside the cedars",
        tags={"spring", "valley"},
    ),
    "sun_hill": Setting(
        id="sun_hill",
        place="Sun Hill",
        spring_name="the Dawn Pool",
        height_word="a bright windy ridge",
        sky_image="gold light resting on the stones",
        closing_image="old women laughing beside jars of shining water",
        tags={"spring", "hill"},
    ),
    "mist_hollow": Setting(
        id="mist_hollow",
        place="Mist Hollow",
        spring_name="the Blue Basin",
        height_word="a fern-dark cliff path",
        sky_image="mist curling under the morning moon",
        closing_image="small lamps glimmering beside the water steps",
        tags={"spring", "hollow"},
    ),
}

OBSTACLES = {
    "vine_snarl": Obstacle(
        id="vine_snarl",
        label="vine snarl",
        phrase="a black snarl of thorn-vines twisted across the stone mouth",
        symptom="Only a few sad drops fell where a bright stream should have sung.",
        clue="A torn leaf quivered high above the basin, showing where the water was trapped.",
        fix_verb="cut the vines away",
        needs="cut",
        reach=2,
        steep=True,
        danger_word="thorns",
        tags={"vines", "plants"},
    ),
    "fallen_branch": Obstacle(
        id="fallen_branch",
        label="fallen branch",
        phrase="a storm-thrown branch wedged across the narrow channel",
        symptom="The basin gave a sleepy glug, but the stream below stayed dry.",
        clue="Wet bark gleamed in the crack where the branch had jammed the run.",
        fix_verb="hook the branch loose",
        needs="hook",
        reach=2,
        steep=False,
        danger_word="slippery bark",
        tags={"branch", "wood"},
    ),
    "stone_plug": Obstacle(
        id="stone_plug",
        label="stone plug",
        phrase="a round stone lodged in the basin mouth like a giant stopper",
        symptom="The water shivered behind the rock and could not find its way out.",
        clue="Tiny bubbles crept around the edges of the stone and vanished.",
        fix_verb="lift the stone free",
        needs="lift",
        reach=1,
        steep=False,
        danger_word="heavy stone",
        tags={"stone", "weight"},
    ),
}

TOOLS = {
    "reed_hook": Tool(
        id="reed_hook",
        label="reed hook",
        phrase="a long reed hook braided by the basket-makers",
        does="hook",
        reach=2,
        line="The reed hook bent like a fishing moon.",
        tags={"hook", "reed"},
    ),
    "bronze_sickle": Tool(
        id="bronze_sickle",
        label="bronze sickle",
        phrase="a little bronze sickle from the temple shed",
        does="cut",
        reach=2,
        line="The bronze edge flashed like a thin sunrise.",
        tags={"cut", "bronze"},
    ),
    "lever_pole": Tool(
        id="lever_pole",
        label="lever pole",
        phrase="a stout ash pole smoothed by many hands",
        does="lift",
        reach=1,
        line="The ash pole was plain, but plain things can be mighty.",
        tags={"lift", "wood"},
    ),
}

HELPERS = {
    "goat": Helper(
        id="goat",
        label="goat",
        phrase="a sure-footed white goat",
        climbs=True,
        carries=False,
        line="The goat could dance where stones scared sandals.",
        tags={"goat", "climb"},
    ),
    "crane": Helper(
        id="crane",
        label="crane",
        phrase="a patient marsh crane",
        climbs=False,
        carries=False,
        line="The crane watched water the way scribes watch ink.",
        tags={"bird", "water"},
    ),
    "young_giant": Helper(
        id="young_giant",
        label="young giant",
        phrase="a gentle young giant from the upper terraces",
        climbs=False,
        carries=True,
        line="The young giant's hands were careful, though each was broad as a tray.",
        tags={"giant", "strength"},
    ),
}

GIRL_NAMES = ["Alia", "Mira", "Tala", "Nysa", "Rhea", "Iris"]
BOY_NAMES = ["Damon", "Lio", "Theron", "Panos", "Milo", "Aren"]
TRAITS = ["patient", "curious", "brave", "careful", "steady", "clever"]


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    tool: str
    helper: str
    hero_name: str
    hero_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="cedar_valley",
        obstacle="vine_snarl",
        tool="bronze_sickle",
        helper="goat",
        hero_name="Mira",
        hero_gender="girl",
        elder="woman",
        trait="patient",
        seed=1,
    ),
    StoryParams(
        setting="sun_hill",
        obstacle="fallen_branch",
        tool="reed_hook",
        helper="crane",
        hero_name="Lio",
        hero_gender="boy",
        elder="man",
        trait="clever",
        seed=2,
    ),
    StoryParams(
        setting="mist_hollow",
        obstacle="stone_plug",
        tool="lever_pole",
        helper="young_giant",
        hero_name="Tala",
        hero_gender="girl",
        elder="woman",
        trait="steady",
        seed=3,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for tool_id, tool in TOOLS.items():
                for helper_id, helper in HELPERS.items():
                    if solution_possible(obstacle, tool, helper):
                        combos.append((setting_id, obstacle_id, tool_id, helper_id))
    return combos


def explain_rejection(obstacle: Obstacle, tool: Tool, helper: Helper) -> str:
    reasons: list[str] = []
    if tool.does != obstacle.needs:
        reasons.append(
            f"{tool.label} can {tool.does}, but this problem needs someone to {obstacle.fix_verb}"
        )
    if tool.reach < obstacle.reach:
        reasons.append(
            f"{tool.label} is too short to reach the blockage safely"
        )
    if obstacle.steep and not helper.climbs:
        reasons.append(
            f"{helper.label} cannot help on the steep path to the basin"
        )
    if obstacle.needs == "lift" and not helper.carries:
        reasons.append(
            f"{helper.label} does not have the carrying strength for the heavy stone"
        )
    if not reasons:
        reasons.append("this combination does not solve the blockage in a sensible way")
    return "(No story: " + "; ".join(reasons) + ".)"


def observe_problem(world: World, hero: Entity, elder: Entity, obstacle: Obstacle, setting: Setting) -> None:
    spring = world.get("spring")
    spring.meters["flow"] = 0.0
    hero.memes["care"] += 1
    world.say(
        f"In {setting.place}, people said a spring had once been a gift from the sky. "
        f"It ran clear at dawn and silver at dusk, and every jar in the village loved its song."
    )
    world.say(
        f"But one morning {setting.spring_name} fell quiet. {obstacle.symptom}"
    )
    world.say(
        f"{hero.id}, a {next(iter([t for t in hero.traits if t != 'little']), 'young')} {hero.type}, "
        f"saw the empty jars by the steps and felt a sharp wish to help."
    )
    world.say(
        f'The village elder touched the dry stone and said, "Whoever listens well may wake the water again."'
    )


def journey(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["resolve"] += 1
    helper.memes["bond"] += 1
    world.say(
        f"So {hero.id} climbed toward {setting.height_word}, with {helper.phrase} beside {hero.pronoun('object')}. "
        f"Above them were {setting.sky_image}."
    )
    world.say(helper.attrs["line"])


def find_clue(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["insight"] += 1
    world.say(
        f"At the basin, {hero.id} did not rush. {hero.pronoun().capitalize()} knelt, listened, and watched. "
        f"{obstacle.clue}"
    )
    world.say(
        f'Then {hero.pronoun()} whispered, "The water is not gone. Something is holding it back."'
    )


def taunt(world: World, obstacle: Obstacle) -> None:
    imp = world.get("imp")
    imp.memes["mischief"] += 1
    world.say(
        f"From a crack in the rock peeped a dust-gray imp no taller than a loaf. "
        f'"Pish!" it chirped. "You are only one child, and the basin keeps its own secrets."'
    )


def choose_plan(world: World, hero: Entity, helper: Entity, tool: Entity, obstacle: Obstacle) -> None:
    world.say(tool.attrs["line"])
    world.say(
        f"{hero.id} looked from the blockage to the tool and then to {helper.label_word}. "
        f"{hero.pronoun().capitalize()} made a plan instead of a boast."
    )
    if obstacle.steep:
        world.say(
            f'"The path is too dangerous for me alone," {hero.pronoun()} said. '
            f'"{helper.label_word.capitalize()} can steady the climb, and I can use the {tool.label} when we are there."'
        )
    elif obstacle.needs == "lift":
        world.say(
            f'"The stone is too heavy for one pair of hands," {hero.pronoun()} said. '
            f'"I will guide the {tool.label}, and {helper.label_word} will lend strength at the right moment."'
        )
    else:
        world.say(
            f'"If I use the {tool.label} where the clue points, we can free the water without breaking the basin," '
            f"{hero.pronoun()} said."
        )


def solve(world: World, hero: Entity, helper: Entity, tool: Entity, obstacle: Obstacle) -> None:
    basin = world.get("basin")
    spring = world.get("spring")
    hero.memes["courage"] += 1
    if obstacle.id == "vine_snarl":
        world.say(
            f"The thorns scratched at sleeves, but {helper.label_word} found safe footing on the ledge. "
            f"{hero.id} reached in with the {tool.label} and cut the tightest twists one by one."
        )
    elif obstacle.id == "fallen_branch":
        world.say(
            f"{hero.id} slid the {tool.label} into the wet crack beneath the branch. "
            f"With one pull, then another, {helper.label_word} nudged from the side until the wood lurched free."
        )
    else:
        world.say(
            f"{hero.id} wedged the {tool.label} under the round stone. "
            f"When {hero.pronoun()} cried out, {helper.label_word} heaved with careful strength, and the stone rolled aside."
        )
    basin.meters["opened"] += 1
    propagate(world, narrate=False)
    spring.meters["flow"] += 0  # read back after propagation
    world.say(
        "For one breath the mountain seemed to wait."
    )


def water_returns(world: World, setting: Setting) -> None:
    hero = world.get("hero")
    world.say(
        f"Then the basin gave a deep answer. Water burst out laughing over the stone lip, "
        f"ran down the channel, and filled the air with cool music."
    )
    world.say(
        f"A thrill ran through {hero.id} from sandals to hair, because the plan had worked exactly where wild guessing would have failed."
    )
    world.say(
        f"Even the little imp blinked, sneezed mist, and slipped away without another word."
    )
    world.say(
        f"By sunset, {setting.spring_name} shone again, and {setting.closing_image}."
    )


def closing_lesson(world: World, hero: Entity, elder: Entity, obstacle: Obstacle) -> None:
    hero.memes["belonging"] += 1
    world.say(
        f'The elder laid a hand on {hero.id}\'s shoulder and said, '
        f'"You did not beat the mountain by shouting at it. You watched, you thought, and you chose the right help."'
    )
    world.say(
        f"From then on, whenever children passed the spring, they remembered that even an old trouble like {obstacle.label} can yield to a patient mind."
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    tool_cfg: Tool,
    helper_cfg: Helper,
    hero_name: str,
    hero_gender: str,
    elder_type: str,
    trait: str,
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=["little", trait],
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label="the elder",
        phrase="the village elder",
        role="elder",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="creature" if helper_cfg.id != "young_giant" else "man",
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={"line": helper_cfg.line},
        tags=set(helper_cfg.tags),
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        role="tool",
        attrs={"line": tool_cfg.line, "does": tool_cfg.does, "reach": tool_cfg.reach},
        tags=set(tool_cfg.tags),
    ))
    spring = world.add(Entity(
        id="spring",
        type="spring",
        label=setting.spring_name,
        phrase=setting.spring_name,
        role="spring",
    ))
    basin = world.add(Entity(
        id="basin",
        type="basin",
        label="the basin",
        phrase="the mountain basin",
        role="basin",
    ))
    imp = world.add(Entity(
        id="imp",
        kind="character",
        type="creature",
        label="imp",
        phrase="a dust-gray imp",
        role="trickster",
    ))

    observe_problem(world, hero, elder, obstacle, setting)
    world.para()
    journey(world, hero, helper, setting)
    find_clue(world, hero, obstacle)
    taunt(world, obstacle)
    world.para()
    choose_plan(world, hero, helper, tool, obstacle)
    solve(world, hero, helper, tool, obstacle)
    water_returns(world, setting)
    world.para()
    closing_lesson(world, hero, elder, obstacle)

    world.facts.update(
        hero=hero,
        elder=elder,
        helper=helper,
        tool=tool,
        spring=spring,
        basin=basin,
        obstacle=obstacle,
        setting=setting,
        solved=basin.meters["opened"] >= THRESHOLD and spring.meters["flow"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    obstacle = world.facts["obstacle"]
    setting = world.facts["setting"]
    tool = world.facts["tool"]
    helper = world.facts["helper"]
    return [
        'Write a child-facing myth that includes the words "thrill" and "pish" and centers on problem solving.',
        f"Tell a short mythic story set in {setting.place} where {hero.label} studies a blocked spring, ignores a mocking imp that says 'Pish!', and solves the trouble with {tool.phrase} and {helper.phrase}.",
        f"Write a myth-style story where the real victory comes from noticing clues and choosing the right help to deal with a {obstacle.label}.",
    ]


KNOWLEDGE = {
    "spring": [
        ("What is a spring?",
         "A spring is water that comes up from the ground and flows out by itself. People and animals often depend on it for drinking water.")
    ],
    "vines": [
        ("Why can thick vines block water?",
         "If many vines twist across a narrow opening, they can catch leaves and slow the flow. Then the water cannot move through easily.")
    ],
    "branch": [
        ("How can a fallen branch block a stream?",
         "A branch can wedge across a narrow place in the waterway. Leaves and sticks pile against it, and the stream gets stuck.")
    ],
    "stone": [
        ("Why is a heavy stone hard to move?",
         "A heavy stone takes a lot of force to lift or roll. One small person may need a tool or helper to move it safely.")
    ],
    "hook": [
        ("What is a hook good for?",
         "A hook is good for catching and pulling something that is hard to reach with bare hands. It helps you tug from a safer place.")
    ],
    "sickle": [
        ("What is a sickle?",
         "A sickle is a curved cutting tool. People use it to slice plants or stems with a careful pull.")
    ],
    "lever": [
        ("How can a lever help move something heavy?",
         "A lever lets you press on one end so the other end pushes up. It helps your strength do more work.")
    ],
    "goat": [
        ("Why are goats good on steep rocks?",
         "Goats have strong legs and careful feet, so they can balance on rough, steep ground better than many other animals.")
    ],
    "giant": [
        ("Why is a strong helper useful with a heavy load?",
         "A strong helper can add the force needed to lift or carry something safely. Some problems are easier when work is shared.")
    ],
    "clue": [
        ("What is a clue?",
         "A clue is a small sign that helps you understand something hidden. If you notice clues, you can make a smarter plan.")
    ],
}
KNOWLEDGE_ORDER = ["spring", "vines", "branch", "stone", "hook", "sickle", "lever", "goat", "giant", "clue"]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    obstacle = world.facts["obstacle"]
    helper = world.facts["helper"]
    tool = world.facts["tool"]
    setting = world.facts["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a young helper in {setting.place}. {hero.label} wanted to wake the village spring so everyone could have water again.",
        ),
        (
            "What was the problem at the beginning?",
            f"{setting.spring_name} had stopped flowing, so the village jars stayed empty. The real trouble was {obstacle.phrase}, which was holding the water back.",
        ),
        (
            "Why did the imp say 'Pish!'?",
            f"The imp was trying to make {hero.label} feel small and foolish. It mocked the quest before the problem was understood.",
        ),
        (
            f"How did {hero.label} figure out what to do?",
            f"{hero.pronoun('subject').capitalize()} slowed down and looked for a clue instead of guessing. {obstacle.clue} That sign showed where the water was trapped and helped {hero.pronoun('object')} choose a real plan.",
        ),
        (
            f"Why were {tool.label} and {helper.label} the right choice?",
            f"They matched the kind of blockage the basin had. The tool could {OBSTACLES[obstacle.id].needs} at the needed reach, and the helper could do the part of the climb or strength that the job required.",
        ),
        (
            "How did the story end?",
            f"The blockage was cleared, the water ran again, and a thrill went through {hero.label}. The ending proves the problem was truly solved because the spring sang again for the whole village.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    helper = world.facts["helper"]
    tags: set[str] = {"spring", "clue"}
    if obstacle.id == "vine_snarl":
        tags.add("vines")
    elif obstacle.id == "fallen_branch":
        tags.add("branch")
    else:
        tags.add("stone")
    if tool.id == "reed_hook":
        tags.add("hook")
    elif tool.id == "bronze_sickle":
        tags.add("sickle")
    else:
        tags.add("lever")
    if helper.id == "goat":
        tags.add("goat")
    elif helper.id == "young_giant":
        tags.add("giant")
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
        parts: list[str] = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            parts.append(f"attrs={ent.attrs}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A sensible story exists only when the chosen tool and helper really solve the blockage.
solution_possible(O, T, H) :- obstacle(O), tool(T), helper(H),
                              needs(O, A), tool_does(T, A),
                              required_reach(O, R1), tool_reach(T, R2), R2 >= R1,
                              not steep_needs_climber(O, H),
                              not heavy_needs_carrier(O, H).

steep_needs_climber(O, H) :- steep(O), not climbs(H).
heavy_needs_carrier(O, H) :- needs(O, lift), not carries(H).

valid(S, O, T, H) :- setting(S), solution_possible(O, T, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs", oid, obstacle.needs))
        lines.append(asp.fact("required_reach", oid, obstacle.reach))
        if obstacle.steep:
            lines.append(asp.fact("steep", oid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_does", tid, tool.does))
        lines.append(asp.fact("tool_reach", tid, tool.reach))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if helper.climbs:
            lines.append(asp.fact("climbs", hid))
        if helper.carries:
            lines.append(asp.fact("carries", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print("  only in asp:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "pish" not in sample.story.lower() or "thrill" not in sample.story.lower():
            raise StoryError("smoke test story missing expected seed words or text")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic problem-solving storyworld: a blocked spring, a clue, and the right helper."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--elder", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool and args.helper:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        helper = HELPERS[args.helper]
        if not solution_possible(obstacle, tool, helper):
            raise StoryError(explain_rejection(obstacle, tool, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, tool_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["woman", "man"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        tool=tool_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.setting]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    helper = HELPERS[params.helper]
    if not solution_possible(obstacle, tool, helper):
        raise StoryError(explain_rejection(obstacle, tool, helper))

    world = tell(
        setting=setting,
        obstacle=obstacle,
        tool_cfg=tool,
        helper_cfg=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (setting, obstacle, tool, helper) combos:\n")
        for setting_id, obstacle_id, tool_id, helper_id in combos:
            print(f"  {setting_id:13} {obstacle_id:13} {tool_id:13} {helper_id}")
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
            header = f"### {p.hero_name}: {p.obstacle} in {p.setting} with {p.tool} and {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
