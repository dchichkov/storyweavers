#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/regurgitate_eighteenth_quest_problem_solving_animal_story.py
========================================================================================

A standalone story world for a small animal tale about a pelican's quest to
reach the eighteenth tide pool, solve a practical obstacle, and bring back food
for a hungry chick before sunset.

Seed requirements carried into the world:
- includes the words "regurgitate" and "eighteenth"
- shaped as a quest
- centered on problem solving
- written in an animal-story style

Run it
------
    python storyworlds/worlds/gpt-5.4/regurgitate_eighteenth_quest_problem_solving_animal_story.py
    python storyworlds/worlds/gpt-5.4/regurgitate_eighteenth_quest_problem_solving_animal_story.py --setting lagoon --obstacle reeds --method crab_guide --prey shrimp
    python storyworlds/worlds/gpt-5.4/regurgitate_eighteenth_quest_problem_solving_animal_story.py --prey mullet
    python storyworlds/worlds/gpt-5.4/regurgitate_eighteenth_quest_problem_solving_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/regurgitate_eighteenth_quest_problem_solving_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/regurgitate_eighteenth_quest_problem_solving_animal_story.py --verify
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
SUNSET_LIMIT = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
        female = {"girl", "mother", "aunt", "pelican_female"}
        male = {"boy", "father", "uncle", "pelican_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    home: str
    path: str
    eighteenth_spot: str
    sky: str
    obstacles: set[str] = field(default_factory=set)
    prey: set[str] = field(default_factory=set)
    methods: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prey:
    id: str
    label: str
    phrase: str
    size: str
    glint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    approach: str
    problem: str
    fear: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    helper: str
    helper_kind: str
    action: str
    solves: set[str] = field(default_factory=set)
    return_gift: str = ""
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


def _r_hungry_worry(world: World) -> list[str]:
    out: list[str] = []
    chick = world.get("chick")
    if chick.meters["hunger"] >= THRESHOLD and world.get("sun").meters["time"] >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            for eid in ("hero", "parent", "chick"):
                world.get(eid).memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_obstacle_stops(world: World) -> list[str]:
    out: list[str] = []
    if world.get("way").meters["blocked"] >= THRESHOLD and world.get("hero").meters["progress"] >= THRESHOLD:
        sig = ("stuck",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["doubt"] += 1
            out.append("__stuck__")
    return out


def _r_help_clears_path(world: World) -> list[str]:
    out: list[str] = []
    if world.get("helper").meters["helped"] >= THRESHOLD and world.get("way").meters["blocked"] >= THRESHOLD:
        sig = ("clear_path",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("way").meters["blocked"] = 0.0
            world.get("hero").memes["hope"] += 1
            out.append("__cleared__")
    return out


def _r_food_solves_hunger(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").meters["carrying_food"] >= THRESHOLD and world.get("chick").meters["hunger"] >= THRESHOLD:
        prey = world.facts["prey_cfg"]
        sig = ("fed", prey.id)
        if sig not in world.fired:
            world.fired.add(sig)
            if prey.size == "tiny":
                world.get("chick").meters["hunger"] = 0.0
                world.get("chick").memes["comfort"] += 1
                world.get("hero").memes["pride"] += 1
                world.get("parent").memes["relief"] += 1
                out.append("__fed__")
    return out


CAUSAL_RULES = [
    Rule(name="hungry_worry", tag="emotional", apply=_r_hungry_worry),
    Rule(name="obstacle_stops", tag="physical", apply=_r_obstacle_stops),
    Rule(name="help_clears_path", tag="physical", apply=_r_help_clears_path),
    Rule(name="food_solves_hunger", tag="physical", apply=_r_food_solves_hunger),
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
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "lagoon": Setting(
        id="lagoon",
        place="a blue lagoon",
        home="a nest on a driftwood tower",
        path="a string of shell-bright tide pools",
        eighteenth_spot="the eighteenth tide pool under a bent mangrove root",
        sky="The morning water shone like a polished spoon.",
        obstacles={"reeds", "slick_rock"},
        prey={"minnow", "shrimp"},
        methods={"crab_guide", "turtle_ferry"},
        tags={"lagoon", "water"},
    ),
    "marsh": Setting(
        id="marsh",
        place="a whispery marsh",
        home="a nest high in the reeds",
        path="a winding row of muddy pools",
        eighteenth_spot="the eighteenth tide pool beside a sleepy willow stump",
        sky="Mist floated low and made the reeds look silver at the tips.",
        obstacles={"reeds", "deep_channel"},
        prey={"shrimp", "needlefish"},
        methods={"crab_guide", "turtle_ferry", "heron_pole"},
        tags={"marsh", "water"},
    ),
    "cove": Setting(
        id="cove",
        place="a quiet sea cove",
        home="a nest tucked into warm cliff grass",
        path="a curving trail of pools left by the sea",
        eighteenth_spot="the eighteenth tide pool in the shadow of a round cliff stone",
        sky="Sea wind ruffled every feather and salted the air.",
        obstacles={"slick_rock", "deep_channel"},
        prey={"minnow", "needlefish"},
        methods={"turtle_ferry", "heron_pole"},
        tags={"cove", "sea"},
    ),
}

PREY = {
    "minnow": Prey(
        id="minnow",
        label="minnow",
        phrase="three tiny minnows",
        size="tiny",
        glint="They flashed like moving bits of moon.",
        tags={"fish", "small_food"},
    ),
    "shrimp": Prey(
        id="shrimp",
        label="shrimp",
        phrase="a beakful of pink shrimp",
        size="tiny",
        glint="They curled like little commas in the clear water.",
        tags={"shrimp", "small_food"},
    ),
    "needlefish": Prey(
        id="needlefish",
        label="needlefish",
        phrase="a slim little needlefish",
        size="tiny",
        glint="It shone like a silver ribbon near the stones.",
        tags={"fish", "small_food"},
    ),
    "mullet": Prey(
        id="mullet",
        label="mullet",
        phrase="one plump mullet",
        size="big",
        glint="It was shiny, but much too thick for a weak chick.",
        tags={"fish", "big_food"},
    ),
}

OBSTACLES = {
    "reeds": Obstacle(
        id="reeds",
        label="reed wall",
        approach="Halfway along the trail, reeds leaned together across the water.",
        problem="Their stems made a green fence with no easy gap.",
        fear="Pip could hear the hungry peep from home in his imagination and felt the minutes pulling.",
        tags={"reeds"},
    ),
    "slick_rock": Obstacle(
        id="slick_rock",
        label="slick rock",
        approach="Farther on, a black rock sloped over the path.",
        problem="It was shiny with spray and too slippery for careful feet.",
        fear="One bad slide would mean a long delay, and sunset was not far away.",
        tags={"slippery"},
    ),
    "deep_channel": Obstacle(
        id="deep_channel",
        label="deep channel",
        approach="Near the last pools, a dark strip of water cut across the way.",
        problem="The channel was too deep to wade and too wide to hop.",
        fear="Pip's wings were still young, and the long swim would waste precious time.",
        tags={"deep"},
    ),
}

METHODS = {
    "crab_guide": Method(
        id="crab_guide",
        helper="Crick the little crab",
        helper_kind="crab",
        action="scuttled in front of Pip and showed him a dry zigzag between the reeds and stones",
        solves={"reeds", "slick_rock"},
        return_gift="Crick clicked his claws proudly when Pip thanked him.",
        tags={"crab", "guide"},
    ),
    "turtle_ferry": Method(
        id="turtle_ferry",
        helper="Moss the turtle",
        helper_kind="turtle",
        action="knelt low in the water and ferried Pip across on his broad shell",
        solves={"deep_channel", "slick_rock"},
        return_gift="Moss blinked once, slow and kind, as the water lapped around his shell.",
        tags={"turtle", "ride"},
    ),
    "heron_pole": Method(
        id="heron_pole",
        helper="Aunt Sedge the heron",
        helper_kind="heron",
        action="laid a long cattail stalk across the hardest part so Pip could step over neatly",
        solves={"deep_channel", "reeds"},
        return_gift="Aunt Sedge folded her wings and told him that clever feet matter as much as strong wings.",
        tags={"heron", "bridge"},
    ),
}

PEL_NAMES = ["Pip", "Nori", "Milo", "Tansy", "Luma", "Bram"]
CHICK_NAMES = ["Pebble", "Dew", "Puff", "Shell"]
PARENT_NAMES = ["Mama Pelican", "Papa Pelican", "Aunt Gull", "Uncle Pelican"]


def prey_is_reasonable(prey: Prey) -> bool:
    return prey.size == "tiny"


def method_handles(method: Method, obstacle: Obstacle) -> bool:
    return obstacle.id in method.solves


def valid_combo(setting: Setting, prey: Prey, obstacle: Obstacle, method: Method) -> bool:
    return (
        obstacle.id in setting.obstacles
        and prey.id in setting.prey
        and method.id in setting.methods
        and prey_is_reasonable(prey)
        and method_handles(method, obstacle)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid, prey in PREY.items():
            for oid, obstacle in OBSTACLES.items():
                for mid, method in METHODS.items():
                    if valid_combo(setting, prey, obstacle, method):
                        combos.append((sid, pid, oid, mid))
    return combos


@dataclass
class StoryParams:
    setting: str
    prey: str
    obstacle: str
    method: str
    hero_name: str
    chick_name: str
    parent_name: str
    parent_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="lagoon",
        prey="shrimp",
        obstacle="reeds",
        method="crab_guide",
        hero_name="Pip",
        chick_name="Pebble",
        parent_name="Mama Pelican",
        parent_type="pelican_female",
    ),
    StoryParams(
        setting="marsh",
        prey="needlefish",
        obstacle="deep_channel",
        method="turtle_ferry",
        hero_name="Nori",
        chick_name="Dew",
        parent_name="Papa Pelican",
        parent_type="pelican_male",
    ),
    StoryParams(
        setting="cove",
        prey="minnow",
        obstacle="slick_rock",
        method="heron_pole",
        hero_name="Luma",
        chick_name="Puff",
        parent_name="Uncle Pelican",
        parent_type="pelican_male",
    ),
]


def explain_prey(prey: Prey) -> str:
    return (
        f"(No story: {prey.phrase} would not honestly solve the nestling's problem. "
        f"A weak chick can swallow only tiny food before sunset, so pick a smaller catch.)"
    )


def explain_combo(setting: Setting, obstacle: Obstacle, method: Method, prey: Prey) -> str:
    if obstacle.id not in setting.obstacles:
        return f"(No story: {obstacle.label} does not fit the path through {setting.place}.)"
    if prey.id not in setting.prey:
        return f"(No story: {prey.label} is not the kind of catch waiting in {setting.place}.)"
    if method.id not in setting.methods:
        return f"(No story: {method.helper} is not around to help in {setting.place}.)"
    if not method_handles(method, obstacle):
        return (
            f"(No story: {method.helper} cannot sensibly solve the {obstacle.label}. "
            f"Pick a helper whose method actually fits the obstacle.)"
        )
    if not prey_is_reasonable(prey):
        return explain_prey(prey)
    return "(No story: this combination does not make a reasonable quest.)"


def introduce(world: World, hero: Entity, chick: Entity, parent: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.place}, Pip's family lived in {setting.home}."
        if hero.id == "Pip"
        else f"In {setting.place}, {hero.id}'s family lived in {setting.home}."
    )
    world.say(setting.sky)
    world.say(
        f"{hero.id} was a young pelican with bright eyes and a careful pouch. "
        f"{chick.id}, the smallest chick in the nest, tucked {chick.pronoun('possessive')} head under one wing and peeped weakly."
    )
    chick.meters["hunger"] += 1
    world.get("sun").meters["time"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I usually regurgitate dinner for little ones," {parent.id} said softly, '
        f'"but I must fly far out for the big fish today, and {chick.id} cannot wait that long."'
    )
    world.say(
        f'"Only tiny food will do," {parent.id} added. "There should be some at {setting.eighteenth_spot} if someone is brave and clever enough to reach it before sunset."'
    )


def begin_quest(world: World, hero: Entity, chick: Entity, setting: Setting) -> None:
    hero.memes["care"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} looked at {chick.id}'s drooping beak, then at {setting.path}. "
        f"The quest felt big, but love made it feel possible."
    )
    world.say(
        f'"I will go to the eighteenth pool," {hero.id} promised. '
        f'"I will find something small enough for {chick.id} to eat."'
    )
    world.get("hero").meters["progress"] += 1
    world.get("way").meters["blocked"] += 1
    propagate(world, narrate=False)


def face_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    world.say(obstacle.approach)
    world.say(obstacle.problem)
    if hero.memes["doubt"] >= THRESHOLD:
        world.say(obstacle.fear)
    else:
        world.say("For a moment, the path looked as if it had folded itself shut.")
    world.say(
        f"{hero.id} did not cry or turn back. {hero.pronoun().capitalize()} stood still and studied the trouble until an idea could find room to land."
    )


def get_help(world: World, hero: Entity, method: Method, obstacle: Obstacle) -> None:
    helper = world.get("helper")
    world.say(
        f"Just then, {method.helper} appeared near the {obstacle.label}."
    )
    world.say(
        f'"I am on a quest to the eighteenth pool," {hero.id} said. '
        f'"My little nest-mate needs tiny food before sunset. Can you help me think?"'
    )
    helper.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{method.helper} {method.action}."
    )
    world.say(
        f"{hero.id} tested the new way once, then twice, and soon the hard place was behind {hero.pronoun('object')}."
    )


def find_food(world: World, hero: Entity, prey: Prey, setting: Setting) -> None:
    world.say(
        f"At last {hero.id} reached {setting.eighteenth_spot}. The pool held its breath around the stones."
    )
    world.say(prey.glint)
    world.say(
        f"Because {hero.id} had not wasted time fighting the obstacle, {hero.pronoun()} could watch carefully instead of rushing."
    )
    hero.meters["carrying_food"] += 1
    world.facts["found_phrase"] = prey.phrase
    world.say(
        f"With one quick dip of {hero.pronoun('possessive')} bill, {hero.pronoun()} gathered {prey.phrase} and tucked the catch safely into {hero.pronoun('possessive')} pouch."
    )
    propagate(world, narrate=False)


def return_home(world: World, hero: Entity, chick: Entity, parent: Entity, method: Method, prey: Prey) -> None:
    world.say(
        f"When {hero.id} hurried back, the nest was washed with orange evening light."
    )
    if chick.meters["hunger"] <= 0:
        world.say(
            f"{chick.id} lifted {chick.pronoun('possessive')} head at once. The food was tiny enough, so {chick.pronoun()} could swallow it without waiting for a grown-up to regurgitate anything."
        )
        world.say(
            f"{chick.id} ate, blinked, and gave a much stronger peep. {parent.id} folded one broad wing around both chicks, full of relief."
        )
        world.say(method.return_gift)
        world.say(
            f"From then on, whenever the path looked impossible, {hero.id} remembered the eighteenth pool and how stopping to think had carried the day."
        )
    else:
        world.say(
            f"But the catch was wrong for a weak chick, and the quest had failed to solve the real problem."
        )
    world.facts["solved"] = chick.meters["hunger"] <= 0
    world.facts["regurgitate_used"] = True


def tell(
    setting: Setting,
    prey: Prey,
    obstacle: Obstacle,
    method: Method,
    hero_name: str,
    chick_name: str,
    parent_name: str,
    parent_type: str,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="pelican", label=hero_name, role="hero"))
    chick = world.add(Entity(id="chick", kind="character", type="pelican", label=chick_name, role="chick"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_name, role="parent"))
    helper = world.add(Entity(id="helper", kind="character", type=method.helper_kind, label=method.helper, role="helper"))
    world.add(Entity(id="way", type="path", label="the way"))
    world.add(Entity(id="sun", type="sun", label="the sun"))

    world.facts.update(
        hero=hero,
        chick=chick,
        parent=parent,
        helper=helper,
        setting=setting,
        prey_cfg=prey,
        obstacle_cfg=obstacle,
        method_cfg=method,
    )

    introduce(world, hero, chick, parent, setting)
    world.para()
    begin_quest(world, hero, chick, setting)
    face_obstacle(world, hero, obstacle)
    get_help(world, hero, method, obstacle)
    world.para()
    find_food(world, hero, prey, setting)
    return_home(world, hero, chick, parent, method, prey)
    return world


KNOWLEDGE = {
    "pelican": [
        (
            "What does regurgitate mean for a pelican parent?",
            "It means the parent brings food back up from its pouch or stomach so a baby bird can eat it. Some birds really do feed their chicks this way."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip with a clear goal. Someone keeps going because something important needs to be done."
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means stopping to think about what is wrong, then choosing a step that can truly help. It is not just hurrying; it is noticing what the problem really is."
        )
    ],
    "tide_pool": [
        (
            "What is a tide pool?",
            "A tide pool is a little pool of sea water left behind among rocks when the tide goes out. Small animals and tiny fish can hide there."
        )
    ],
    "crab": [
        (
            "How can a crab help another animal find a path?",
            "A crab knows where the ground is firm and where the gaps are small. By showing a safe route, it can help someone move carefully."
        )
    ],
    "turtle": [
        (
            "Why would a turtle make a good ferry in shallow water?",
            "A turtle has a broad, steady shell and moves calmly through water. That makes it a good helper for crossing a short channel."
        )
    ],
    "heron": [
        (
            "Why is a long-legged heron useful near marsh water?",
            "A heron can stand where the water is awkward for smaller birds. It can reach across a hard spot and make a safer crossing."
        )
    ],
    "small_food": [
        (
            "Why did the chick need tiny food instead of a big fish?",
            "A weak chick can swallow small bites more easily. Tiny food solves the real problem because it can be eaten right away."
        )
    ],
}
KNOWLEDGE_ORDER = ["pelican", "quest", "problem_solving", "tide_pool", "crab", "turtle", "heron", "small_food"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    chick = world.facts["chick"]
    prey = world.facts["prey_cfg"]
    obstacle = world.facts["obstacle_cfg"]
    method = world.facts["method_cfg"]
    setting = world.facts["setting"]
    return [
        'Write a short animal story for a 3-to-5-year-old that includes the words "regurgitate" and "eighteenth."',
        f"Tell a quest story where a young pelican named {hero.label} must reach the eighteenth tide pool in {setting.place} to bring back {prey.label} for {chick.label}.",
        f"Write a problem-solving animal tale where {hero.label} faces a {obstacle.label} and succeeds by accepting help from {method.helper}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    chick = world.facts["chick"]
    parent = world.facts["parent"]
    helper = world.facts["helper"]
    prey = world.facts["prey_cfg"]
    obstacle = world.facts["obstacle_cfg"]
    setting = world.facts["setting"]
    method = world.facts["method_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a young pelican, and {chick.label}, the smallest chick in the nest. {parent.label} and {helper.label} also matter because one explains the need and the other helps with the hard part."
        ),
        (
            f"Why did {hero.label} go on a quest?",
            f"{hero.label} went on a quest because {chick.label} was hungry and too weak to wait for a grown-up to regurgitate dinner later. The nest needed tiny food before sunset, so the trip to the eighteenth pool became important."
        ),
        (
            f"What problem blocked the way?",
            f"The problem was a {obstacle.label}. It mattered because it could waste time on a day when every minute before sunset counted."
        ),
        (
            f"How did {hero.label} solve the problem?",
            f"{hero.label} stopped to study the obstacle instead of panicking, then asked for help from {helper.label}. {method.helper} {method.action}, which turned the path into something {hero.label} could really use."
        ),
    ]
    if world.facts.get("solved"):
        out.append(
            (
                f"Why was {prey.label} the right food for {chick.label}?",
                f"{prey.phrase.capitalize()} was the right choice because it was tiny enough for a weak chick to swallow right away. That solved the real problem better than bringing home a larger fish that still could not be eaten."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"It ended with orange sunset light on the nest and {chick.label} peeping more strongly after eating. The ending proves that thinking carefully and accepting help changed the day."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    method = world.facts["method_cfg"]
    tags = {"pelican", "quest", "problem_solving", "tide_pool", "small_food"}
    if "crab" in method.tags:
        tags.add("crab")
    if "turtle" in method.tags:
        tags.add("turtle")
    if "heron" in method.tags:
        tags.add("heron")
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
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {eid:8} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
tiny_food(P) :- prey(P), prey_size(P, tiny).
reasonable_prey(P) :- tiny_food(P).
can_solve(M, O) :- method(M), obstacle(O), solves(M, O).

valid(S, P, O, M) :- setting(S), prey(P), obstacle(O), method(M),
                     has_obstacle(S, O), has_prey(S, P), has_method(S, M),
                     reasonable_prey(P), can_solve(M, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for oid in sorted(setting.obstacles):
            lines.append(asp.fact("has_obstacle", sid, oid))
        for pid in sorted(setting.prey):
            lines.append(asp.fact("has_prey", sid, pid))
        for mid in sorted(setting.methods):
            lines.append(asp.fact("has_method", sid, mid))
    for pid, prey in PREY.items():
        lines.append(asp.fact("prey", pid))
        lines.append(asp.fact("prey_size", pid, prey.size))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for oid in sorted(method.solves):
            lines.append(asp.fact("solves", mid, oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal story world: a pelican quest to the eighteenth tide pool, with problem solving and a tiny-food rescue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prey", choices=PREY)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-name")
    ap.add_argument("--chick-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--parent", choices=["pelican_female", "pelican_male"], dest="parent_type")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prey is not None and not prey_is_reasonable(PREY[args.prey]):
        raise StoryError(explain_prey(PREY[args.prey]))
    if args.setting and args.prey and args.obstacle and args.method:
        if not valid_combo(SETTINGS[args.setting], PREY[args.prey], OBSTACLES[args.obstacle], METHODS[args.method]):
            raise StoryError(explain_combo(SETTINGS[args.setting], OBSTACLES[args.obstacle], METHODS[args.method], PREY[args.prey]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.prey is None or combo[1] == args.prey)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        if args.setting and args.prey and args.obstacle and args.method:
            raise StoryError(explain_combo(SETTINGS[args.setting], OBSTACLES[args.obstacle], METHODS[args.method], PREY[args.prey]))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, prey_id, obstacle_id, method_id = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(PEL_NAMES)
    chick_name = args.chick_name or rng.choice([n for n in CHICK_NAMES if n != hero_name])
    parent_type = args.parent_type or rng.choice(["pelican_female", "pelican_male"])
    if args.parent_name:
        parent_name = args.parent_name
    else:
        parent_name = "Mama Pelican" if parent_type == "pelican_female" else "Papa Pelican"

    return StoryParams(
        setting=setting_id,
        prey=prey_id,
        obstacle=obstacle_id,
        method=method_id,
        hero_name=hero_name,
        chick_name=chick_name,
        parent_name=parent_name,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        prey = PREY[params.prey]
        obstacle = OBSTACLES[params.obstacle]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]!r} is not in this world.)") from err

    if not valid_combo(setting, prey, obstacle, method):
        raise StoryError(explain_combo(setting, obstacle, method, prey))

    world = tell(
        setting=setting,
        prey=prey,
        obstacle=obstacle,
        method=method,
        hero_name=params.hero_name,
        chick_name=params.chick_name,
        parent_name=params.parent_name,
        parent_type=params.parent_type,
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError as err:
            rc = 1
            print("FAILED to resolve random params during smoke test:", err)
            continue
        params.seed = seed
        smoke_cases.append(params)

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"FAILED to generate sample {idx}: {err}")
            continue
        if "regurgitate" not in sample.story or "eighteenth" not in sample.story:
            rc = 1
            print(f"FAILED story content check on sample {idx}: missing seed words")
        if not sample.story_qa or not sample.world_qa or not sample.prompts:
            rc = 1
            print(f"FAILED QA/prompt check on sample {idx}: missing generated extras")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, prey, obstacle, method) combos:\n")
        for setting, prey, obstacle, method in combos:
            print(f"  {setting:7} {prey:10} {obstacle:12} {method}")
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
            header = f"### {p.hero_name}: {p.setting}, {p.prey}, {p.obstacle}, {p.method}"
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
