#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/terrific_mate_bravery_folk_tale.py
=============================================================

A standalone storyworld for a small folk-tale domain: a village child and a
faithful animal mate must travel to a far spring or garden beyond a frightening
obstacle. The child's bravery is not empty boasting; it is a state in the
world, strengthened by preparation and companionship, and only some
place/obstacle/tool/mate/temper combinations make a sensible tale.

The engine keeps one compact world model with typed entities, physical meters,
emotional memes, a forward-chaining rule step, a Python reasonableness gate,
and an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/terrific_mate_bravery_folk_tale.py
    python storyworlds/worlds/gpt-5.4/terrific_mate_bravery_folk_tale.py --obstacle cave --tool lantern
    python storyworlds/worlds/gpt-5.4/terrific_mate_bravery_folk_tale.py --obstacle cave --tool boots
    python storyworlds/worlds/gpt-5.4/terrific_mate_bravery_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/terrific_mate_bravery_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/terrific_mate_bravery_folk_tale.py --verify
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

# Make the shared result containers importable when this script is run directly:
# /storyworlds/worlds/gpt-5.4/<file>.py -> add /storyworlds to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def title_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path: str
    home: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    place_phrase: str
    danger: str
    fear: int
    crossing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    matches: str
    comfort: int
    ready_text: str
    cross_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MateCfg:
    id: str
    label: str
    kind: str
    call: str
    help_text: str
    boost: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    source: str
    gift_text: str
    save_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trait:
    id: str
    label: str
    base: int


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    tool: str
    mate: str
    goal: str
    trait: str
    hero_name: str
    hero_gender: str
    elder_type: str
    seed: Optional[int] = None


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


def _r_cross(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    if obstacle.meters["faced"] < THRESHOLD or tool.meters["ready"] < THRESHOLD:
        return []
    if obstacle.meters["crossed"] >= THRESHOLD:
        return []
    if hero.memes["bravery"] >= obstacle.attrs["fear"]:
        world.fired.add(("cross", obstacle.id))
        obstacle.meters["crossed"] = 1.0
        hero.meters["progress"] += 1
        return ["__crossed__"]
    return []


def _r_claim_goal(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    goal = world.get("goal")
    hero = world.get("hero")
    if obstacle.meters["crossed"] < THRESHOLD or goal.meters["found"] >= THRESHOLD:
        return []
    goal.meters["found"] = 1.0
    hero.meters["carrying"] = 1.0
    hero.memes["relief"] += 1
    world.get("village").memes["hope"] += 1
    return ["__found_goal__"]


CAUSAL_RULES = [
    Rule(name="cross", tag="physical", apply=_r_cross),
    Rule(name="claim_goal", tag="physical", apply=_r_claim_goal),
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
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


PLACES = {
    "cedar_ford": Place(
        id="cedar_ford",
        label="Cedar Ford",
        opening="In the days when cedar smoke curled above every roof, there was a small village by the ford.",
        path="The path out of the village ran between ferny stones and old cedar roots.",
        home="By dusk the village windows shone like little honey squares.",
        affords={"river", "cave"},
    ),
    "moon_hill": Place(
        id="moon_hill",
        label="Moon Hill",
        opening="Long ago, below a round hill that caught the moonlight, stood a ring of cottages.",
        path="A sheep track wound away from the cottages and up through silver grass.",
        home="At evening the hill held the last light while the cottages glowed below.",
        affords={"cave", "thorns"},
    ),
    "fern_vale": Place(
        id="fern_vale",
        label="Fern Vale",
        opening="Once, in a green vale where fern fronds brushed every doorway, there lived a careful little village.",
        path="Beyond the last garden gate, the road bent through nettles, moss, and birdsong.",
        home="When shadows lengthened, the vale smelled of soup pots and warm bread.",
        affords={"river", "thorns"},
    ),
}

OBSTACLES = {
    "river": Obstacle(
        id="river",
        label="river",
        place_phrase="the cold river that hurried over black stones",
        danger="The water spoke in a quick, slippery voice, and it looked deep enough to steal small feet away.",
        fear=4,
        crossing="past the river lay the shining spring meadow",
        tags={"river"},
    ),
    "thorns": Obstacle(
        id="thorns",
        label="thorn patch",
        place_phrase="a thorn patch knotted thick across the path",
        danger="The briars hooked at sleeves and hems, and every branch seemed to whisper, Not this way, little one.",
        fear=3,
        crossing="beyond the briars stood the old herb garden",
        tags={"thorns"},
    ),
    "cave": Obstacle(
        id="cave",
        label="cave",
        place_phrase="the cave under the hill mouth",
        danger="The dark there was so full and still that even brave thoughts felt small at first.",
        fear=5,
        crossing="through the cave opened the secret moon spring",
        tags={"cave"},
    ),
}

TOOLS = {
    "boat": Tool(
        id="boat",
        label="reed boat",
        phrase="a little reed boat",
        matches="river",
        comfort=1,
        ready_text="set a little reed boat in the shallows and tested it with one steady hand",
        cross_text="pushed the reed boat into the current, climbed in with careful knees, and let the boat nose across the shining water",
        tags={"boat"},
    ),
    "boots": Tool(
        id="boots",
        label="thorn boots",
        phrase="a pair of thorn boots",
        matches="thorns",
        comfort=1,
        ready_text="pulled on a pair of thorn boots stitched with thick leather toes",
        cross_text="stepped into the briars, and the cruel little hooks scraped the boots instead of skin",
        tags={"boots"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        matches="cave",
        comfort=1,
        ready_text="lifted a brass lantern until its gold circle pushed back the dark",
        cross_text="held the lantern high and walked where the warm light made a road through the black cave",
        tags={"lantern"},
    ),
}

MATES = {
    "dog": MateCfg(
        id="dog",
        label="dog",
        kind="animal",
        call="little dog",
        help_text="The little dog pressed close to the child's leg and gave one stout bark, as if to say that two hearts could do what one heart feared.",
        boost=1,
        tags={"dog"},
    ),
    "goat": MateCfg(
        id="goat",
        label="goat",
        kind="animal",
        call="sure-footed goat",
        help_text="The sure-footed goat stamped once and leaned forward, showing the path the way a bold old shepherd might.",
        boost=1,
        tags={"goat"},
    ),
    "raven": MateCfg(
        id="raven",
        label="raven",
        kind="animal",
        call="bright raven",
        help_text="The bright raven flew ahead, then back again, croaking as if it had already measured the fear and found it smaller than it looked.",
        boost=2,
        tags={"raven"},
    ),
}

GOALS = {
    "moonwater": Goal(
        id="moonwater",
        label="moonwater",
        phrase="a silver flask for moonwater",
        source="the secret moon spring",
        gift_text="There, clear moonwater trembled in a stone basin, and the child filled the silver flask to the brim.",
        save_text="When the flask was poured into the village well, the water tasted sweet again.",
        tags={"water"},
    ),
    "sunherb": Goal(
        id="sunherb",
        label="sunherb",
        phrase="a willow basket for sunherb",
        source="the old herb garden",
        gift_text="There, warm sunherb grew in a ring of yellow leaves, and the child gathered a basket full.",
        save_text="When the herb was steeped in a pot, the coughing in the cottages softened and the rooms grew restful.",
        tags={"herb"},
    ),
    "bellseed": Goal(
        id="bellseed",
        label="bellseed",
        phrase="a red pouch for bellseed",
        source="the shining spring meadow",
        gift_text="There, bright bellseed shone among the grass, and the child filled the red pouch with the tiny ringing seeds.",
        save_text="When the bellseed was planted by the meeting tree, new bells bloomed and the village square sang in the wind.",
        tags={"seed"},
    ),
}

TRAITS = {
    "gentle": Trait(id="gentle", label="gentle", base=2),
    "steady": Trait(id="steady", label="steady", base=3),
    "bold": Trait(id="bold", label="bold", base=4),
}

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Elsa", "Rosa", "Anya", "Pippa"]
BOY_NAMES = ["Tobin", "Milo", "Ivo", "Rowan", "Eli", "Bram", "Ned", "Otto"]


def courage_score(trait: Trait, mate: MateCfg, tool: Tool) -> int:
    return trait.base + mate.boost + tool.comfort


def tool_fits(tool: Tool, obstacle: Obstacle) -> bool:
    return tool.matches == obstacle.id


def place_allows(place: Place, obstacle: Obstacle) -> bool:
    return obstacle.id in place.affords


def feasible(place: Place, obstacle: Obstacle, tool: Tool, mate: MateCfg, trait: Trait) -> bool:
    return place_allows(place, obstacle) and tool_fits(tool, obstacle) and courage_score(trait, mate, tool) >= obstacle.fear


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for tool_id, tool in TOOLS.items():
                for mate_id, mate in MATES.items():
                    for trait_id, trait in TRAITS.items():
                        if feasible(place, obstacle, tool, mate, trait):
                            combos.append((place_id, obstacle_id, tool_id, mate_id, trait_id))
    return combos


def explain_rejection(place: Place, obstacle: Obstacle, tool: Tool, mate: MateCfg, trait: Trait) -> str:
    if not place_allows(place, obstacle):
        return (
            f"(No story: {place.label} does not lead to {obstacle.place_phrase}, "
            f"so that obstacle does not belong on this road.)"
        )
    if not tool_fits(tool, obstacle):
        return (
            f"(No story: {tool.phrase} is not a sensible way past {obstacle.place_phrase}. "
            f"Choose the tool that truly fits the obstacle.)"
        )
    score = courage_score(trait, mate, tool)
    return (
        f"(No story: a {trait.label} child with a {mate.label} and {tool.phrase} "
        f"only reaches courage {score}, but this {obstacle.label} asks for {obstacle.fear}. "
        f"Pick a steadier heart or a stronger mate for this folk tale.)"
    )


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    mate = MATES[params.mate]
    trait = TRAITS[params.trait]
    return "triumph" if feasible(place, obstacle, tool, mate, trait) else "ask_help"


def introduce(world: World, hero: Entity, elder: Entity, goal: Goal, trait: Trait, mate: MateCfg) -> None:
    world.say(world.place.opening)
    world.say(
        f"In that village lived {hero.id}, a {trait.label} little {hero.type}, "
        f"and {hero.pronoun('possessive')} {mate.label}, the finest mate a young traveler could hope for."
    )
    world.say(
        f"One lean season, the people needed {goal.label}, so {hero.id}'s {elder.title_word} "
        f"placed {goal.phrase} in {hero.pronoun('possessive')} hands."
    )


def charge(world: World, hero: Entity, elder: Entity, goal: Goal) -> None:
    world.say(
        f'"Beyond the old road lies {goal.source}," said the {elder.title_word}. '
        f'"Bring back what the village needs, and do not let fear choose your steps."'
    )
    world.say(world.place.path)


def approach_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    ent = world.get("obstacle")
    hero.memes["fear"] += obstacle.fear
    ent.meters["faced"] = 1.0
    world.say(
        f"Before long they came to {obstacle.place_phrase}. {obstacle.danger}"
    )
    world.say(
        f"{hero.id} stood still for a moment. {hero.pronoun('possessive').capitalize()} heart thumped like a small drum inside a wooden chest."
    )


def mate_encourages(world: World, hero: Entity, mate_ent: Entity, mate: MateCfg) -> None:
    hero.memes["trust"] += 1
    mate_ent.memes["loyalty"] += 1
    hero.memes["bravery"] += mate.boost
    world.say(
        f'{hero.id} looked at {mate_ent.label} and whispered, "Stay with me, mate."'
    )
    world.say(mate.help_text)


def ready_tool(world: World, hero: Entity, tool: Tool) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["ready"] = 1.0
    hero.memes["bravery"] += tool.comfort
    world.say(
        f"Then {hero.id} {tool.ready_text}."
    )


def cross_and_claim(world: World, hero: Entity, mate_ent: Entity, obstacle: Obstacle, tool: Tool, goal: Goal) -> None:
    markers = propagate(world, narrate=False)
    if "__crossed__" in markers:
        world.say(
            f"Bravery did not make the road less hard, but it made {hero.id}'s feet keep moving. "
            f"{hero.pronoun().capitalize()} {tool.cross_text}, with {mate_ent.label} close beside."
        )
        world.say(
            f"Step by step, they went on, and soon {obstacle.crossing}."
        )
    if "__found_goal__" in markers:
        world.say(goal.gift_text)


def return_and_resolve(world: World, hero: Entity, elder: Entity, goal: Goal, mate: MateCfg) -> None:
    hero.memes["joy"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"{world.place.home} {hero.id} came back before the lamps were low, with {goal.label} safe at last."
    )
    world.say(goal.save_text)
    world.say(
        f'The {elder.title_word} smiled and said, "That was terrific, and your {mate.label} was a true mate indeed."'
    )
    world.say(
        f"After that, when storms, thorns, or darkness troubled the road, the village remembered how a small brave heart and a faithful companion had gone first."
    )


def tell(
    place: Place,
    obstacle: Obstacle,
    tool: Tool,
    mate: MateCfg,
    goal: Goal,
    trait: Trait,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    elder_type: str = "grandmother",
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    mate_ent = world.add(Entity(id="mate", kind="character", type="animal", label=f"the {mate.label}", role="mate"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=f"the {elder_type}", role="elder"))
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type=obstacle.id,
            label=obstacle.label,
            role="obstacle",
            attrs={"fear": obstacle.fear},
            tags=set(obstacle.tags),
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            kind="thing",
            type=tool.id,
            label=tool.label,
            phrase=tool.phrase,
            role="tool",
            tags=set(tool.tags),
        )
    )
    goal_ent = world.add(
        Entity(
            id="goal",
            kind="thing",
            type=goal.id,
            label=goal.label,
            phrase=goal.phrase,
            role="goal",
            tags=set(goal.tags),
        )
    )
    village = world.add(Entity(id="village", kind="place", type="village", label=place.label, role="village"))

    hero.attrs["name"] = hero_name
    hero.memes["bravery"] = trait.base
    hero.memes["duty"] = 1

    introduce(world, hero, elder, goal, trait, mate)
    charge(world, hero, elder, goal)

    world.para()
    approach_obstacle(world, hero, obstacle)
    mate_encourages(world, hero, mate_ent, mate)
    ready_tool(world, hero, tool)

    world.para()
    cross_and_claim(world, hero, mate_ent, obstacle, tool, goal)
    return_and_resolve(world, hero, elder, goal, mate)

    world.facts.update(
        hero=hero,
        hero_name=hero_name,
        mate_cfg=mate,
        mate=mate_ent,
        elder=elder,
        place=place,
        obstacle_cfg=obstacle,
        obstacle=obstacle_ent,
        tool_cfg=tool,
        tool=tool_ent,
        goal_cfg=goal,
        goal=goal_ent,
        trait=trait,
        score=courage_score(trait, mate, tool),
        outcome="triumph",
        returned=goal_ent.meters["found"] >= THRESHOLD,
        village_helped=village.memes["hope"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel afraid. It does not mean having no fear at all."
        )
    ],
    "river": [
        (
            "Why can a river be hard to cross?",
            "A river moves and can be slippery or deep. Fast water can knock small feet off balance."
        )
    ],
    "thorns": [
        (
            "Why are thorn bushes painful?",
            "Thorns are sharp, hard points on some plants. They can scratch skin and catch on clothes."
        )
    ],
    "cave": [
        (
            "Why can a cave feel scary?",
            "A cave can be dark, echoing, and hard to see through. When you cannot see well, your body often feels more afraid."
        )
    ],
    "boat": [
        (
            "What does a small boat help you do?",
            "A small boat helps you float across water instead of walking through it. It keeps your feet out of the current."
        )
    ],
    "boots": [
        (
            "What are sturdy boots for?",
            "Sturdy boots protect your feet when the ground is rough or prickly. Thick soles and leather can block scratches."
        )
    ],
    "lantern": [
        (
            "What is a lantern for?",
            "A lantern makes light that helps you see in dark places. Seeing the path clearly can make a hard walk safer."
        )
    ],
    "dog": [
        (
            "Why can a dog be a good companion?",
            "A dog can stay close, warn you, and make you feel less alone. A steady companion can help a person feel braver."
        )
    ],
    "goat": [
        (
            "Why are goats good on rough paths?",
            "Goats are sure-footed and good at finding careful steps. People notice that and feel steadier beside them."
        )
    ],
    "raven": [
        (
            "Why do folk tales often use ravens as helpers?",
            "Ravens are clever birds, so folk tales often treat them as watchful guides. They can seem wise because they notice things from above."
        )
    ],
    "water": [
        (
            "Why is clean water important to a village?",
            "People need clean water for drinking and cooking every day. A good water source helps the whole village stay well."
        )
    ],
    "herb": [
        (
            "What is an herb?",
            "An herb is a useful plant with leaves, flowers, or stems people can gather. Some herbs are used for flavor and some are used for comfort or healing."
        )
    ],
    "seed": [
        (
            "What grows from a seed?",
            "A seed can grow into a new plant when it has soil, water, and time. Tiny seeds can make very big changes."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "bravery",
    "river",
    "thorns",
    "cave",
    "boat",
    "boots",
    "lantern",
    "dog",
    "goat",
    "raven",
    "water",
    "herb",
    "seed",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    mate = f["mate_cfg"]
    goal = f["goal_cfg"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the words "terrific" and "mate".',
        f"Tell a folk tale about a little {hero.type} and a faithful {mate.label} who must go through {obstacle.place_phrase} near {place.label} to fetch {goal.label}.",
        f"Write a bravery story where a child uses {tool.phrase} in a sensible way, faces fear, and returns with help for the village.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    mate = f["mate_cfg"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    goal = f["goal_cfg"]
    place = f["place"]
    score = f["score"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['name']}, a little {hero.type}, and a faithful {mate.label} who travels as {hero.pronoun('possessive')} mate. They live in {place.label} and go on a brave errand for the village."
        ),
        (
            "What did the village need?",
            f"The village needed {goal.label}, so {hero.attrs['name']}'s {elder.title_word} sent {hero.pronoun('object')} to {goal.source}. That need is what sends the child onto the road."
        ),
        (
            f"Why did {hero.attrs['name']} stop at first?",
            f"{hero.attrs['name']} stopped because {obstacle.place_phrase} looked frightening. The world made {hero.pronoun('object')} feel fear before bravery carried {hero.pronoun('object')} forward."
        ),
        (
            f"How did the {mate.label} help {hero.attrs['name']}?",
            f"The {mate.label} stayed close and encouraged {hero.attrs['name']}. That companionship raised the child's courage so the hard path felt possible."
        ),
        (
            f"Why was {tool.phrase} important?",
            f"{tool.phrase.capitalize()} was the right tool for this obstacle. It did not remove all fear, but it gave {hero.attrs['name']} a safe way to keep going."
        ),
        (
            "How does the story show bravery?",
            f"The story shows bravery because {hero.attrs['name']} feels afraid and still chooses the right road. With courage score {score} against fear {obstacle.fear}, preparation and friendship turn fear into action."
        ),
        (
            "How did the story end?",
            f"{hero.attrs['name']} brought back {goal.label}, and the village was helped. The ending image proves the change because the people remember both the brave child and the true mate who went first."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bravery"} | set(f["obstacle_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["mate_cfg"].tags) | set(f["goal_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="cedar_ford",
        obstacle="river",
        tool="boat",
        mate="dog",
        goal="bellseed",
        trait="bold",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        place="moon_hill",
        obstacle="thorns",
        tool="boots",
        mate="goat",
        goal="sunherb",
        trait="steady",
        hero_name="Tobin",
        hero_gender="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        place="moon_hill",
        obstacle="cave",
        tool="lantern",
        mate="raven",
        goal="moonwater",
        trait="steady",
        hero_name="Lina",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        place="cedar_ford",
        obstacle="cave",
        tool="lantern",
        mate="raven",
        goal="moonwater",
        trait="gentle",
        hero_name="Rowan",
        hero_gender="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        place="fern_vale",
        obstacle="river",
        tool="boat",
        mate="goat",
        goal="bellseed",
        trait="bold",
        hero_name="Rosa",
        hero_gender="girl",
        elder_type="grandmother",
    ),
]


ASP_RULES = r"""
usable_tool(T, O) :- matches(T, O).
path_exists(P, O) :- affords(P, O).
courage(Tr, M, T, B + MB + C) :- trait_base(Tr, B), mate_boost(M, MB), tool_comfort(T, C).

valid(P, O, T, M, Tr) :- place(P), obstacle(O), tool(T), mate(M), trait(Tr),
                         path_exists(P, O), usable_tool(T, O),
                         courage(Tr, M, T, S), fear(O, F), S >= F.

outcome(triumph) :- chosen_place(P), chosen_obstacle(O), chosen_tool(T), chosen_mate(M), chosen_trait(Tr),
                    path_exists(P, O), usable_tool(T, O),
                    courage(Tr, M, T, S), fear(O, F), S >= F.
outcome(ask_help) :- chosen_place(P), chosen_obstacle(O), chosen_tool(T), chosen_mate(M), chosen_trait(Tr),
                     not outcome(triumph).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("fear", obstacle_id, obstacle.fear))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("matches", tool_id, tool.matches))
        lines.append(asp.fact("tool_comfort", tool_id, tool.comfort))
    for mate_id, mate in MATES.items():
        lines.append(asp.fact("mate", mate_id))
        lines.append(asp.fact("mate_boost", mate_id, mate.boost))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("trait_base", trait_id, trait.base))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_mate", params.mate),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    scenarios: list[StoryParams] = list(CURATED)
    for place in PLACES:
        for obstacle in OBSTACLES:
            for tool in TOOLS:
                for mate in MATES:
                    for trait in TRAITS:
                        scenarios.append(
                            StoryParams(
                                place=place,
                                obstacle=obstacle,
                                tool=tool,
                                mate=mate,
                                goal="moonwater",
                                trait=trait,
                                hero_name="Mira",
                                hero_gender="girl",
                                elder_type="grandmother",
                            )
                        )
    bad = 0
    for params in scenarios:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(scenarios)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a folk-tale child and a faithful mate face a frightening road."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mate", choices=MATES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story choices derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.tool and args.mate and args.trait:
        place = PLACES[args.place]
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        mate = MATES[args.mate]
        trait = TRAITS[args.trait]
        if not feasible(place, obstacle, tool, mate, trait):
            raise StoryError(explain_rejection(place, obstacle, tool, mate, trait))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
        and (args.mate is None or combo[3] == args.mate)
        and (args.trait is None or combo[4] == args.trait)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, tool_id, mate_id, trait_id = rng.choice(sorted(combos))
    goal_id = args.goal or rng.choice(sorted(GOALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        tool=tool_id,
        mate=mate_id,
        goal=goal_id,
        trait=trait_id,
        hero_name=name,
        hero_gender=gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.mate not in MATES:
        raise StoryError(f"(Unknown mate: {params.mate})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    mate = MATES[params.mate]
    trait = TRAITS[params.trait]
    if not feasible(place, obstacle, tool, mate, trait):
        raise StoryError(explain_rejection(place, obstacle, tool, mate, trait))

    world = tell(
        place=place,
        obstacle=obstacle,
        tool=tool,
        mate=mate,
        goal=GOALS[params.goal],
        trait=trait,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, tool, mate, trait) combos:\n")
        for place, obstacle, tool, mate, trait in combos:
            print(f"  {place:10} {obstacle:8} {tool:8} {mate:6} {trait}")
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
            header = (
                f"### {p.hero_name}: {p.obstacle} at {p.place} with {p.tool}, "
                f"{p.mate}, and {p.trait} courage"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
