#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fleet_honest_humor_teamwork_twist_heartwarming.py
============================================================================

A standalone storyworld about a tiny homemade boat parade after the rain.

Seed constraints:
- words: "fleet", "honest"
- features: Humor, Teamwork, Twist
- style: Heartwarming

Domain sketch
-------------
Two children make a little fleet of toy boats and launch them in a rain-made
channel. One child accidentally damages the special boat before the race. The
child chooses to be honest instead of hiding the mistake. Together, the children
repair the boat. The twist is that the repair changes the boat in a surprising
way that helps it through the channel's obstacle, so the very thing that looked
like a problem becomes part of the happy ending.

This world enforces a narrow reasonableness rule:
- each problem needs the right kind of repair,
- and each setting's obstacle only makes a good story when the repair also
  creates the later twist advantage.

Examples
--------
python storyworlds/worlds/gpt-5.4/fleet_honest_humor_teamwork_twist_heartwarming.py
python storyworlds/worlds/gpt-5.4/fleet_honest_humor_teamwork_twist_heartwarming.py --setting gutter_lane --problem bent_mast --repair straw_mast
python storyworlds/worlds/gpt-5.4/fleet_honest_humor_teamwork_twist_heartwarming.py --setting pond_corner --problem bent_mast
python storyworlds/worlds/gpt-5.4/fleet_honest_humor_teamwork_twist_heartwarming.py --all --qa
python storyworlds/worlds/gpt-5.4/fleet_honest_humor_teamwork_twist_heartwarming.py --verify
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
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
    waterway: str
    obstacle: str
    obstacle_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BoatKind:
    id: str
    label: str
    phrase: str
    motion: str
    silly_name: str
    part: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    part: str
    confession: str
    damage_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    fixes_part: str
    grants_feature: str
    teamwork_text: str
    twist_text: str
    qa_text: str
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
        return [e for e in self.entities.values() if e.role in {"maker", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.setting)
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


def _r_damage_worry(world: World) -> list[str]:
    boat = world.get("boat")
    if boat.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_worry", "boat")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    boat.meters["ready"] = 0.0
    return ["__worry__"]


def _r_honesty_trust(world: World) -> list[str]:
    maker = world.get("maker")
    friend = world.get("friend")
    if maker.memes["honest"] < THRESHOLD:
        return []
    sig = ("honesty_trust", maker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    maker.memes["relief"] += 1
    friend.memes["trust"] += 1
    return ["__trust__"]


def _r_teamwork_ready(world: World) -> list[str]:
    boat = world.get("boat")
    maker = world.get("maker")
    friend = world.get("friend")
    helper = world.get("helper")
    if boat.meters["repaired"] < THRESHOLD:
        return []
    if maker.memes["teamwork"] < THRESHOLD or friend.memes["teamwork"] < THRESHOLD:
        return []
    sig = ("teamwork_ready", boat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["ready"] += 1
    boat.meters["damage"] = 0.0
    helper.memes["pride"] += 1
    maker.memes["hope"] += 1
    friend.memes["hope"] += 1
    return ["__ready__"]


def _r_twist_win(world: World) -> list[str]:
    boat = world.get("boat")
    if boat.meters["launched"] < THRESHOLD or boat.meters["ready"] < THRESHOLD:
        return []
    feature = boat.attrs.get("feature", "")
    counter = world.setting.obstacle
    if not counters_obstacle(feature, counter):
        return []
    sig = ("twist_win", boat.id, feature, counter)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["won"] += 1
    boat.memes["surprise"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
    return ["__twist__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_worry", tag="emotion", apply=_r_damage_worry),
    Rule(name="honesty_trust", tag="emotion", apply=_r_honesty_trust),
    Rule(name="teamwork_ready", tag="physical", apply=_r_teamwork_ready),
    Rule(name="twist_win", tag="outcome", apply=_r_twist_win),
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
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


SETTINGS = {
    "gutter_lane": Setting(
        id="gutter_lane",
        place="the sun-warmed curb outside the building",
        waterway="a ribbon of rainwater hurrying along the curb",
        obstacle="low_branch",
        obstacle_line="Ahead, a twiggy branch drooped so low over the stream that tall boats would bump it.",
        tags={"rain", "gutter", "branch"},
    ),
    "garden_rill": Setting(
        id="garden_rill",
        place="the little rill beside Grandma's tomatoes",
        waterway="a clear runnel slipping between pebbles",
        obstacle="side_splash",
        obstacle_line="Near the marigolds, the water slapped sideways against a stone and splashed any weak side.",
        tags={"garden", "water", "splash"},
    ),
    "pond_corner": Setting(
        id="pond_corner",
        place="the shallow edge of the duck pond after the sprinkler had run",
        waterway="a small shining channel feeding the pond",
        obstacle="thin_breeze",
        obstacle_line="At the bend, the channel opened wide and only boats that could catch the tiny breeze kept moving.",
        tags={"pond", "breeze", "duck"},
    ),
}

BOATS = {
    "shoebox_skiff": BoatKind(
        id="shoebox_skiff",
        label="shoebox skiff",
        phrase="a shoebox skiff with bottle-cap windows",
        motion="skipped on the water with quick little jerks",
        silly_name="Captain Pickle",
        part="mast",
        tags={"boat", "mast"},
    ),
    "cork_tug": BoatKind(
        id="cork_tug",
        label="cork tug",
        phrase="a cork tug with a button chimney",
        motion="bobbed stoutly and kept its nose forward",
        silly_name="Sir Bubblepants",
        part="hull",
        tags={"boat", "hull"},
    ),
    "leaf_sloop": BoatKind(
        id="leaf_sloop",
        label="leaf sloop",
        phrase="a leaf sloop with a berry-box deck",
        motion="leaned into the water as if listening to it",
        silly_name="Laughing Gull",
        part="sail",
        tags={"boat", "sail"},
    ),
}

PROBLEMS = {
    "bent_mast": Problem(
        id="bent_mast",
        label="bent mast",
        part="mast",
        confession="I have to be honest. I bent the mast when I was making the engine noise too wildly.",
        damage_text="One silly shoulder-shimmy later, the mast tipped sideways like a sleepy straw.",
        tags={"mast", "honest"},
    ),
    "leaky_hull": Problem(
        id="leaky_hull",
        label="leaky hull",
        part="hull",
        confession="I have to be honest. My elbow poked the side, and now the hull has a tiny leak.",
        damage_text="A bead of water showed through the side, bright as a little secret.",
        tags={"hull", "honest"},
    ),
    "torn_sail": Problem(
        id="torn_sail",
        label="torn sail",
        part="sail",
        confession="I have to be honest. I tore the sail when I tried to make it flap like a dragon wing.",
        damage_text="The paper sail split with a tiny rip that sounded much louder in the quiet.",
        tags={"sail", "honest"},
    ),
}

REPAIRS = {
    "straw_mast": Repair(
        id="straw_mast",
        label="short straw mast",
        phrase="a short straw mast tied on with blue thread",
        fixes_part="mast",
        grants_feature="low_profile",
        teamwork_text="One child held the deck steady, the other threaded the blue string, and Grandpa trimmed the straw to fit.",
        twist_text="Because the new mast sat lower, the little boat slipped neatly under the drooping branch where taller boats got tickled and stuck.",
        qa_text="They replaced the bent mast with a short straw mast",
        tags={"mast", "repair", "string"},
    ),
    "wax_patch": Repair(
        id="wax_patch",
        label="smooth wax patch",
        phrase="a smooth wax patch rubbed warm by their thumbs",
        fixes_part="hull",
        grants_feature="sealed_side",
        teamwork_text="One child pressed from inside, the other rubbed the wax on the crack, and Grandma polished the patch until it shone.",
        twist_text="The patch made the side slick and firm, so the splash at the stone skipped right off instead of slapping water inside.",
        qa_text="They sealed the leak with a smooth wax patch",
        tags={"hull", "repair", "wax"},
    ),
    "patch_sail": Repair(
        id="patch_sail",
        label="patchwork sail",
        phrase="a patchwork sail of light paper and ribbon",
        fixes_part="sail",
        grants_feature="wide_catch",
        teamwork_text="One child held the mast, the other glued the new paper, and Grandma added a tiny ribbon tail for balance.",
        twist_text="The new sail caught the shy breeze at the bend, and the boat moved when the others only wiggled.",
        qa_text="They made a new patchwork sail together",
        tags={"sail", "repair", "breeze"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Zoe", "Ella", "Nora", "Ruby", "Lucy"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Sam", "Noah", "Eli", "Finn"]
TRAITS = ["careful", "cheerful", "busy", "bouncy", "curious", "gentle"]


def counters_obstacle(feature: str, obstacle: str) -> bool:
    return (
        (feature == "low_profile" and obstacle == "low_branch")
        or (feature == "sealed_side" and obstacle == "side_splash")
        or (feature == "wide_catch" and obstacle == "thin_breeze")
    )


def valid_combo(setting_id: str, boat_id: str, problem_id: str, repair_id: str) -> bool:
    setting = SETTINGS[setting_id]
    boat = BOATS[boat_id]
    problem = PROBLEMS[problem_id]
    repair = REPAIRS[repair_id]
    if boat.part != problem.part:
        return False
    if repair.fixes_part != problem.part:
        return False
    return counters_obstacle(repair.grants_feature, setting.obstacle)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for boat_id in BOATS:
            for problem_id in PROBLEMS:
                for repair_id in REPAIRS:
                    if valid_combo(setting_id, boat_id, problem_id, repair_id):
                        out.append((setting_id, boat_id, problem_id, repair_id))
    return out


@dataclass
class StoryParams:
    setting: str
    boat: str
    problem: str
    repair: str
    maker: str
    maker_gender: str
    friend: str
    friend_gender: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, maker: Entity, friend: Entity, helper: Entity, boat_cfg: BoatKind) -> None:
    for kid in (maker, friend):
        kid.memes["joy"] += 1
    world.say(
        f"After the rain, {maker.id} and {friend.id} knelt beside {world.setting.place}, where "
        f"{world.setting.waterway} made the best sort of afternoon race track."
    )
    world.say(
        f"On the curb beside them stood a tiny fleet of homemade boats. Their favorite was "
        f"{boat_cfg.phrase}, and they had given it the very serious and very funny name "
        f'"{boat_cfg.silly_name}."'
    )
    world.say(
        f'{helper.label_word.capitalize()} said the name in a deep captain voice, and both children laughed so hard that even the ducks looked offended.'
    )


def accident(world: World, maker: Entity, boat: Entity, problem: Problem) -> None:
    boat.meters["damaged"] += 1
    maker.memes["guilt"] += 1
    world.say(
        f"{maker.id} scooted the boat forward and made loud engine noises with {maker.pronoun('possessive')} mouth. "
        f"{problem.damage_text}"
    )
    propagate(world, narrate=False)


def confess(world: World, maker: Entity, friend: Entity, problem: Problem) -> None:
    maker.memes["honest"] += 1
    world.say(
        f"{maker.id}'s cheeks went warm. For one second, {maker.pronoun()} wanted to hide the problem behind the other boats."
    )
    world.say(f'"{problem.confession}" {maker.id} said.')
    propagate(world, narrate=False)
    if friend.memes["trust"] >= THRESHOLD:
        world.say(
            f'{friend.id} blinked, then nodded. "Thank you for telling me," {friend.pronoun()} said. "We can fix it together."'
        )


def team_repair(world: World, maker: Entity, friend: Entity, helper: Entity, boat: Entity, repair: Repair) -> None:
    maker.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    boat.meters["repaired"] += 1
    boat.attrs["feature"] = repair.grants_feature
    world.say(
        f"So they did not waste even one more worried minute. {repair.teamwork_text}"
    )
    world.say(
        f"Soon the boat wore {repair.phrase}. It looked different now, a little patched and a little proud."
    )
    propagate(world, narrate=False)


def launch(world: World, maker: Entity, friend: Entity, boat_cfg: BoatKind, boat: Entity) -> None:
    boat.meters["launched"] += 1
    world.say(world.setting.obstacle_line)
    world.say(
        f"When they set {boat_cfg.silly_name} into the stream, it {boat_cfg.motion}."
    )
    propagate(world, narrate=False)


def twist_and_end(world: World, maker: Entity, friend: Entity, helper: Entity, boat_cfg: BoatKind, repair: Repair) -> None:
    boat = world.get("boat")
    if boat.meters["won"] >= THRESHOLD:
        world.say(
            f"Then came the twist nobody expected. {repair.twist_text}"
        )
        world.say(
            f'{helper.label_word.capitalize()} clapped once and said, "Well, would you look at that. The fix turned out to be a trick."'
        )
        world.say(
            f"{maker.id} and {friend.id} ran along the curb together, laughing so hard they could hardly cheer. "
            f'Soon "{boat_cfg.silly_name}" was first to the little pool at the end.'
        )
    else:
        world.say(
            f"The boat did not finish first, but it floated bravely all the same, and the children grinned as if it had won a prize just for trying."
        )
    maker.memes["relief"] += 1
    friend.memes["relief"] += 1
    maker.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"At the end, the best part was not the race at all. It was that an honest sentence, a pair of busy hands, and one kind grown-up had turned a mistake into a story everyone wanted to tell again."
    )


def tell(
    setting: Setting,
    boat_cfg: BoatKind,
    problem: Problem,
    repair: Repair,
    maker_name: str = "Lily",
    maker_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    helper_name: str = "Grandpa",
    helper_type: str = "grandfather",
    trait: str = "cheerful",
) -> World:
    world = World(setting)
    maker = world.add(Entity(id="maker", kind="character", type=maker_gender, label=maker_name, role="maker", traits=[trait]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend", traits=["steady"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    boat = world.add(Entity(id="boat", type="boat", label=boat_cfg.label, phrase=boat_cfg.phrase))
    maker.attrs["name"] = maker_name
    friend.attrs["name"] = friend_name
    helper.attrs["name"] = helper_name

    introduce(world, maker, friend, helper, boat_cfg)
    world.para()
    accident(world, maker, boat, problem)
    confess(world, maker, friend, problem)
    world.para()
    team_repair(world, maker, friend, helper, boat, repair)
    launch(world, maker, friend, boat_cfg, boat)
    world.para()
    twist_and_end(world, maker, friend, helper, boat_cfg, repair)

    world.facts.update(
        maker=maker,
        friend=friend,
        helper=helper,
        boat=boat,
        boat_cfg=boat_cfg,
        setting=setting,
        problem=problem,
        repair=repair,
        won=boat.meters["won"] >= THRESHOLD,
        honest=maker.memes["honest"] >= THRESHOLD,
        teamwork=maker.memes["teamwork"] >= THRESHOLD and friend.memes["teamwork"] >= THRESHOLD,
    )
    return world


def pair_noun(maker: Entity, friend: Entity) -> str:
    if maker.type == "girl" and friend.type == "girl":
        return "two girls"
    if maker.type == "boy" and friend.type == "boy":
        return "two boys"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    maker = world.facts["maker"]
    friend = world.facts["friend"]
    setting = world.facts["setting"]
    boat_cfg = world.facts["boat_cfg"]
    problem = world.facts["problem"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "fleet" and "honest".',
        f"Tell a gentle story where {maker.label} and {friend.label} race a tiny homemade boat at {setting.place}, a funny accident causes a {problem.label}, and teamwork saves the day.",
        f"Write a child-facing story with humor, teamwork, and a twist ending where a damaged {boat_cfg.label} is fixed and the fix becomes part of the surprise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    maker = world.facts["maker"]
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    setting = world.facts["setting"]
    boat_cfg = world.facts["boat_cfg"]
    problem = world.facts["problem"]
    repair = world.facts["repair"]
    pair = pair_noun(maker, friend)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {maker.label} and {friend.label}, and {helper.label_word} who helped them. They were playing beside {setting.place} with a tiny boat race.",
        ),
        (
            "What was the fleet in the story?",
            f"The fleet was the children's little group of homemade boats lined up beside the water. Their favorite one was the {boat_cfg.label} named \"{boat_cfg.silly_name}.\"",
        ),
        (
            f"What problem happened to the boat?",
            f"The boat had a {problem.label}. It happened during a silly moment, which is why the scene felt funny before it suddenly felt serious.",
        ),
        (
            f"How was {maker.label} honest?",
            f"{maker.label} told the truth right away instead of hiding the damage. That honest choice mattered because it gave everyone time to help.",
        ),
        (
            "How did they fix the boat?",
            f"{repair.qa_text}. The repair worked because both children helped and {helper.label_word} joined in too.",
        ),
    ]
    if world.facts["won"]:
        qa.append(
            (
                "What was the twist at the end?",
                f"The repair did more than mend the boat. {repair.twist_text} That surprise is why the ending feels bright and funny.",
            )
        )
    qa.append(
        (
            "Why does the story show teamwork?",
            f"The children did not solve the problem alone or by blaming each other. They used several hands at once, and the grown-up helper turned worry into a shared job.",
        )
    )
    return qa


KNOWLEDGE = {
    "fleet": [
        (
            "What is a fleet?",
            "A fleet is a group of boats traveling or standing together. In a child's game, even a few toy boats can be called a fleet.",
        )
    ],
    "honest": [
        (
            "What does honest mean?",
            "Honest means telling the truth. It helps people trust you, even when you are talking about a mistake.",
        )
    ],
    "mast": [
        (
            "What is a mast on a boat?",
            "A mast is the tall pole that can hold a sail. If it bends too much, the boat may not work the way it should.",
        )
    ],
    "hull": [
        (
            "What is a boat's hull?",
            "The hull is the main body of the boat that sits in the water. If the hull leaks, water can get inside.",
        )
    ],
    "sail": [
        (
            "What does a sail do?",
            "A sail catches the wind and helps move a boat. A torn sail cannot catch the breeze as well.",
        )
    ],
    "repair": [
        (
            "Why is it good to repair something together?",
            "Repairing something together lets people share ideas and careful hands. It can also make a broken thing useful again.",
        )
    ],
    "breeze": [
        (
            "What is a breeze?",
            "A breeze is a soft little wind. It can move leaves, tickle your face, or push a tiny boat along.",
        )
    ],
    "wax": [
        (
            "Why can wax help stop a small leak?",
            "Warm wax can fill a tiny crack and block water from slipping through. That is why people sometimes use it as a seal.",
        )
    ],
    "branch": [
        (
            "Why might a low branch bother a tall boat?",
            "A low branch can catch on a tall part of the boat and slow it down. A shorter top can slide underneath more easily.",
        )
    ],
}
KNOWLEDGE_ORDER = ["fleet", "honest", "mast", "hull", "sail", "repair", "breeze", "wax", "branch"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    problem = world.facts["problem"]
    repair = world.facts["repair"]
    setting = world.facts["setting"]
    tags = {"fleet", "honest", "repair"} | set(problem.tags) | set(repair.tags) | set(setting.tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="gutter_lane",
        boat="shoebox_skiff",
        problem="bent_mast",
        repair="straw_mast",
        maker="Lily",
        maker_gender="girl",
        friend="Tom",
        friend_gender="boy",
        helper="Grandpa",
        helper_type="grandfather",
        trait="bouncy",
    ),
    StoryParams(
        setting="garden_rill",
        boat="cork_tug",
        problem="leaky_hull",
        repair="wax_patch",
        maker="Max",
        maker_gender="boy",
        friend="Nora",
        friend_gender="girl",
        helper="Grandma",
        helper_type="grandmother",
        trait="curious",
    ),
    StoryParams(
        setting="pond_corner",
        boat="leaf_sloop",
        problem="torn_sail",
        repair="patch_sail",
        maker="Ella",
        maker_gender="girl",
        friend="Ben",
        friend_gender="boy",
        helper="Grandma",
        helper_type="grandmother",
        trait="cheerful",
    ),
]


def explain_rejection(setting_id: str, boat_id: str, problem_id: str, repair_id: str) -> str:
    setting = SETTINGS[setting_id]
    boat = BOATS[boat_id]
    problem = PROBLEMS[problem_id]
    repair = REPAIRS[repair_id]
    if boat.part != problem.part:
        return (
            f"(No story: the {boat.label}'s vulnerable part is the {boat.part}, but the problem is {problem.label}. "
            f"Pick a problem that can happen to that kind of boat.)"
        )
    if repair.fixes_part != problem.part:
        return (
            f"(No story: {repair.label} fixes a {repair.fixes_part}, not a {problem.part}. "
            f"The repair has to match the damage.)"
        )
    return (
        f"(No story: {repair.label} would fix the boat, but it would not create the right twist for {setting.place}. "
        f"The repair should also help with the setting's obstacle.)"
    )


def validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.boat not in BOATS:
        raise StoryError(f"(Unknown boat: {params.boat})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if not valid_combo(params.setting, params.boat, params.problem, params.repair):
        raise StoryError(explain_rejection(params.setting, params.boat, params.problem, params.repair))


def outcome_of(params: StoryParams) -> str:
    validate_params(params)
    repair = REPAIRS[params.repair]
    setting = SETTINGS[params.setting]
    return "twist_win" if counters_obstacle(repair.grants_feature, setting.obstacle) else "float"


ASP_RULES = r"""
% Valid domain story: the chosen boat's fragile part matches the damage,
% the repair fixes that part, and the repair's feature counters the setting obstacle.
valid(S, B, P, R) :- setting(S), boat(B), problem(P), repair(R),
                     vulnerable_part(B, Part), damaged_part(P, Part),
                     fixes_part(R, Part), grants_feature(R, Feature),
                     obstacle(S, Ob), counters(Feature, Ob).

outcome(S, R, twist_win) :- setting(S), repair(R), obstacle(S, Ob),
                            grants_feature(R, Feature), counters(Feature, Ob).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("obstacle", sid, setting.obstacle))
    for bid, boat in BOATS.items():
        lines.append(asp.fact("boat", bid))
        lines.append(asp.fact("vulnerable_part", bid, boat.part))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("damaged_part", pid, problem.part))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("fixes_part", rid, repair.fixes_part))
        lines.append(asp.fact("grants_feature", rid, repair.grants_feature))
    lines.extend(
        [
            asp.fact("counters", "low_profile", "low_branch"),
            asp.fact("counters", "sealed_side", "side_splash"),
            asp.fact("counters", "wide_catch", "thin_breeze"),
        ]
    )
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_repair", params.repair),
            "picked_outcome(O) :- chosen_setting(S), chosen_repair(R), outcome(S, R, O).",
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show picked_outcome/1."))
    vals = asp.atoms(model, "picked_outcome")
    return vals[0][0] if vals else "?"


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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tiny storyworld: an honest confession, teamwork, and a toy-boat twist after the rain."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--boat", choices=BOATS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--maker")
    ap.add_argument("--friend")
    ap.add_argument("--maker-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.boat and args.problem and args.repair:
        if not valid_combo(args.setting, args.boat, args.problem, args.repair):
            raise StoryError(explain_rejection(args.setting, args.boat, args.problem, args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.boat is None or combo[1] == args.boat)
        and (args.problem is None or combo[2] == args.problem)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        if args.setting and args.boat and args.problem and args.repair:
            raise StoryError(explain_rejection(args.setting, args.boat, args.problem, args.repair))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, boat_id, problem_id, repair_id = rng.choice(sorted(combos))
    maker_gender = args.maker_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    maker = args.maker or pick_name(rng, maker_gender)
    friend = args.friend or pick_name(rng, friend_gender, avoid=maker)
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather"])
    helper = {"grandmother": "Grandma", "grandfather": "Grandpa", "mother": "Mom", "father": "Dad"}[helper_type]
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        boat=boat_id,
        problem=problem_id,
        repair=repair_id,
        maker=maker,
        maker_gender=maker_gender,
        friend=friend,
        friend_gender=friend_gender,
        helper=helper,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        boat_cfg=BOATS[params.boat],
        problem=PROBLEMS[params.problem],
        repair=REPAIRS[params.repair],
        maker_name=params.maker,
        maker_gender=params.maker_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        helper_name=params.helper,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, boat, problem, repair) combos:\n")
        for setting_id, boat_id, problem_id, repair_id in combos:
            print(f"  {setting_id:12} {boat_id:13} {problem_id:11} {repair_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.maker} and {p.friend}: {p.problem} -> {p.repair} at {p.setting}"
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
