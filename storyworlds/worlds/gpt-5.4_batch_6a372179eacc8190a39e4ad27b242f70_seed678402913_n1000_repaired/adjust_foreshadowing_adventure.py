#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/adjust_foreshadowing_adventure.py
============================================================

A standalone story world about a child-sized adventure with an early clue, a
needed adjustment, and a changed ending. The core pattern is:

    exciting quest -> foreshadowing clue -> warning grounded in the world model
    -> adjust the right gear and move carefully, or rush and have to turn back

The seed asked for the word "adjust", the narrative feature "Foreshadowing", and
an Adventure style, so this world makes the adjustment itself part of the plot.
The clue is not decorative: it predicts the obstacle's danger, changes what the
characters decide, and supports the later Q&A.

Run it
------
    python storyworlds/worlds/gpt-5.4/adjust_foreshadowing_adventure.py
    python storyworlds/worlds/gpt-5.4/adjust_foreshadowing_adventure.py --setting forest --obstacle rope_bridge
    python storyworlds/worlds/gpt-5.4/adjust_foreshadowing_adventure.py --obstacle low_tunnel --adjustment lower_lantern
    python storyworlds/worlds/gpt-5.4/adjust_foreshadowing_adventure.py --obstacle rope_bridge --adjustment lower_lantern
    python storyworlds/worlds/gpt-5.4/adjust_foreshadowing_adventure.py --all
    python storyworlds/worlds/gpt-5.4/adjust_foreshadowing_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/adjust_foreshadowing_adventure.py --qa --json
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
from contextlib import redirect_stdout
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
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather", "ranger"}
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
            "grandfather": "grandpa",
            "grandmother": "grandma",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    goal: str
    goal_image: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    hazard: str
    severity: int
    clue: str
    warning: str
    crossing: str
    near_miss: str
    retreat: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Adjustment:
    id: str
    label: str
    action: str
    sloppy: str
    guards: set[str] = field(default_factory=set)
    power: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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
        clone.facts = dict(self.facts)
        return clone


def _r_threat(world: World) -> list[str]:
    obstacle = world.entities.get("obstacle")
    hero = world.entities.get("hero")
    buddy = world.entities.get("buddy")
    if obstacle is None or hero is None or buddy is None:
        return []
    if obstacle.meters["risk"] < THRESHOLD:
        return []
    sig = ("threat",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    buddy.memes["fear"] += 1
    return ["__threat__"]


def _r_near_miss(world: World) -> list[str]:
    obstacle = world.entities.get("obstacle")
    hero = world.entities.get("hero")
    if obstacle is None or hero is None:
        return []
    if obstacle.meters["risk"] < THRESHOLD or hero.meters["crossing"] < THRESHOLD:
        return []
    if hero.meters["stability"] >= obstacle.meters["risk"]:
        return []
    sig = ("near_miss",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["shaken"] += 1
    hero.memes["fear"] += 1
    return ["__near_miss__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="threat", tag="emotion", apply=_r_threat),
    Rule(name="near_miss", tag="physical", apply=_r_near_miss),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(setting_id: str, obstacle_id: str, adjustment_id: str) -> bool:
    if setting_id not in SETTINGS or obstacle_id not in OBSTACLES or adjustment_id not in ADJUSTMENTS:
        return False
    setting = SETTINGS[setting_id]
    obstacle = OBSTACLES[obstacle_id]
    adjustment = ADJUSTMENTS[adjustment_id]
    return obstacle_id in setting.affords and obstacle.hazard in adjustment.guards


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for obstacle_id in sorted(setting.affords):
            obstacle = OBSTACLES[obstacle_id]
            for adjustment_id, adjustment in ADJUSTMENTS.items():
                if obstacle.hazard in adjustment.guards:
                    combos.append((setting_id, obstacle_id, adjustment_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.setting not in SETTINGS or params.obstacle not in OBSTACLES or params.adjustment not in ADJUSTMENTS:
        raise StoryError("(Invalid params: unknown setting, obstacle, or adjustment.)")
    if not valid_combo(params.setting, params.obstacle, params.adjustment):
        raise StoryError(explain_rejection(SETTINGS[params.setting], OBSTACLES[params.obstacle],
                                           ADJUSTMENTS[params.adjustment]))
    obstacle = OBSTACLES[params.obstacle]
    adjustment = ADJUSTMENTS[params.adjustment]
    pace_bonus = 1 if params.pace == "careful" else 0
    if adjustment.power + pace_bonus >= obstacle.severity:
        return "success"
    return "retreat"


def predict_crossing(world: World, obstacle_id: str, adjustment_id: str, pace: str) -> dict:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    hero = sim.get("hero")
    obstacle_cfg = OBSTACLES[obstacle_id]
    adjustment_cfg = ADJUSTMENTS[adjustment_id]
    obstacle.meters["risk"] = float(obstacle_cfg.severity)
    hero.meters["stability"] = 0.0
    if pace == "careful":
        hero.meters["stability"] += 1
    hero.meters["stability"] += adjustment_cfg.power
    propagate(sim, narrate=False)
    return {
        "risk": obstacle.meters["risk"],
        "stability": hero.meters["stability"],
        "safe": hero.meters["stability"] >= obstacle.meters["risk"],
    }


def introduce(world: World, hero: Entity, buddy: Entity, guide: Entity, setting: Setting) -> None:
    hero.memes["wonder"] += 1
    buddy.memes["wonder"] += 1
    world.say(
        f"{hero.id} and {buddy.id} set out with {guide.label_word} on {setting.opening}. "
        f"They called themselves the Morning Explorers, and today they were hunting for {setting.goal}."
    )


def goal_seen(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"Far ahead, past brambles and sunlit stones, {hero.id} could just make out {setting.goal_image}."
    )


def clue_beat(world: World, buddy: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"Before anyone reached {obstacle.phrase}, {buddy.id} stopped. {obstacle.clue}"
    )


def warn_from_prediction(world: World, guide: Entity, buddy: Entity, obstacle: Obstacle,
                         adjustment: Adjustment, pace: str) -> None:
    pred = predict_crossing(world, obstacle.id, adjustment.id, pace)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_stability"] = pred["stability"]
    buddy.memes["caution"] += 1
    extra = "if nobody paused to adjust properly" if pace == "rushing" else "unless they moved carefully"
    world.say(
        f'{guide.label_word.capitalize()} listened to the quiet clue and nodded. '
        f'"That sound is a warning," {guide.pronoun()} said. "{obstacle.warning}, {extra}."'
    )


def decide(world: World, hero: Entity, adjustment: Adjustment, pace: str) -> None:
    if pace == "careful":
        hero.memes["courage"] += 1
        world.say(
            f"So {hero.id} stopped right there to {adjustment.action}. "
            f'"Adventure can wait for one smart breath," {hero.pronoun()} said.'
        )
    else:
        hero.memes["impatience"] += 1
        world.say(
            f"But {hero.id} was eager to hurry. {adjustment.sloppy} "
            f'"We can fix the little things later," {hero.pronoun()} said.'
        )


def attempt_crossing(world: World, hero: Entity, buddy: Entity, guide: Entity,
                     obstacle: Obstacle, adjustment: Adjustment, pace: str) -> None:
    obstacle_ent = world.get("obstacle")
    hero.meters["crossing"] += 1
    obstacle_ent.meters["risk"] = float(obstacle.severity)
    if pace == "careful":
        hero.meters["stability"] += 1
    hero.meters["stability"] += adjustment.power
    propagate(world, narrate=False)
    if hero.meters["stability"] >= obstacle_ent.meters["risk"]:
        hero.memes["relief"] += 1
        buddy.memes["relief"] += 1
        world.say(
            f"Then they started across. {obstacle.crossing}, and this time the path answered with steadiness instead of trouble."
        )
    else:
        world.say(
            f"Then they started across. {obstacle.near_miss}"
        )


def success_ending(world: World, hero: Entity, buddy: Entity, guide: Entity,
                   setting: Setting, obstacle: Obstacle, adjustment: Adjustment) -> None:
    hero.memes["joy"] += 1
    buddy.memes["joy"] += 1
    world.say(
        f"On the far side, they found {setting.goal_image}. {buddy.id} laughed, and {guide.label_word} tapped the map with a proud finger."
    )
    world.say(
        f'"The clue tried to tell us what the trail needed," {hero.id} said. '
        f'"We listened, we made the right adjust, and the adventure opened."'
    )


def retreat_ending(world: World, hero: Entity, buddy: Entity, guide: Entity,
                   setting: Setting, obstacle: Obstacle, adjustment: Adjustment) -> None:
    hero.memes["relief"] += 1
    buddy.memes["relief"] += 1
    world.say(
        f"{guide.label_word.capitalize()} caught the moment before it turned worse, and all three backed away from {obstacle.label}. {obstacle.retreat}"
    )
    world.say(
        f"They took the longer path instead, and though it was slower, it led them safely to {setting.goal_image}. "
        f"By sunset, {hero.id} was glad they had learned that real explorers adjust first and rush second."
    )


def tell(setting: Setting, obstacle_cfg: Obstacle, adjustment_cfg: Adjustment,
         hero_name: str = "Nora", hero_type: str = "girl",
         buddy_name: str = "Finn", buddy_type: str = "boy",
         guide_type: str = "grandfather", pace: str = "careful") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero",
                            label=hero_name, traits=["brave", "curious"]))
    buddy = world.add(Entity(id=buddy_name, kind="character", type=buddy_type, role="buddy",
                             label=buddy_name, traits=["watchful", "kind"]))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, role="guide",
                             label="the guide"))
    obstacle_ent = world.add(Entity(id="obstacle", kind="thing", type="obstacle",
                                    label=obstacle_cfg.label, phrase=obstacle_cfg.phrase))
    gear = world.add(Entity(id="adjustment", kind="thing", type="gear",
                            label=adjustment_cfg.label, phrase=adjustment_cfg.label))

    world.facts["pace"] = pace
    world.facts["hero"] = hero
    world.facts["buddy"] = buddy
    world.facts["guide"] = guide
    world.facts["setting"] = setting
    world.facts["obstacle_cfg"] = obstacle_cfg
    world.facts["adjustment_cfg"] = adjustment_cfg
    world.facts["obstacle"] = obstacle_ent
    world.facts["gear"] = gear

    introduce(world, hero, buddy, guide, setting)
    goal_seen(world, hero, setting)

    world.para()
    clue_beat(world, buddy, obstacle_cfg)
    warn_from_prediction(world, guide, buddy, obstacle_cfg, adjustment_cfg, pace)
    decide(world, hero, adjustment_cfg, pace)

    world.para()
    attempt_crossing(world, hero, buddy, guide, obstacle_cfg, adjustment_cfg, pace)

    outcome = "success" if hero.meters["stability"] >= obstacle_ent.meters["risk"] else "retreat"
    world.facts["outcome"] = outcome
    world.facts["safe"] = outcome == "success"

    world.para()
    if outcome == "success":
        success_ending(world, hero, buddy, guide, setting, obstacle_cfg, adjustment_cfg)
    else:
        retreat_ending(world, hero, buddy, guide, setting, obstacle_cfg, adjustment_cfg)

    return world


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
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


SETTINGS = {
    "forest": Setting(
        id="forest",
        place="the old forest trail behind the greenhouse",
        opening="a bright walk along the old forest trail behind the greenhouse",
        goal="the brass compass marker hidden near the fern hill",
        goal_image="a brass compass marker shining under fern leaves",
        affords={"rope_bridge", "stone_slope"},
        tags={"forest", "adventure"},
    ),
    "cliffs": Setting(
        id="cliffs",
        place="the cliff path above the cove",
        opening="a windy walk along the cliff path above the cove",
        goal="the red lookout flag by the weather post",
        goal_image="a red lookout flag snapping beside the weather post",
        affords={"rope_bridge", "low_tunnel"},
        tags={"cliff", "adventure", "wind"},
    ),
    "canyon": Setting(
        id="canyon",
        place="the dry canyon path by the tall rocks",
        opening="a dusty walk along the dry canyon path by the tall rocks",
        goal="the bell tied near the cool spring",
        goal_image="a little silver bell hanging above the cool spring",
        affords={"stone_slope", "low_tunnel"},
        tags={"canyon", "adventure"},
    ),
}

OBSTACLES = {
    "rope_bridge": Obstacle(
        id="rope_bridge",
        label="the rope bridge",
        phrase="the rope bridge",
        hazard="swing",
        severity=3,
        clue="One rope gave a small twang, and the bridge answered with a long slow sway.",
        warning="A swinging bridge can pull a hurrying explorer sideways",
        crossing="The ropes still moved under their hands, but the swing stayed small and easy to answer",
        near_miss="The bridge lurched harder than expected, and the boards knocked together with a sharp clack beneath their feet",
        retreat="Even from the bank, they could see it was a day for the lower stepping-stone route, not the bridge.",
        tags={"bridge", "balance"},
    ),
    "stone_slope": Obstacle(
        id="stone_slope",
        label="the stone slope",
        phrase="the stone slope",
        hazard="slip",
        severity=2,
        clue="Tiny pebbles clicked downhill before any boot touched the path.",
        warning="Loose stones like these can slide under fast feet",
        crossing="Their feet found the firm edges first, and each step stayed where it belonged",
        near_miss="The stones skittered away in a quick silver rush, and one of the children had to hop back to keep from sliding",
        retreat="They chose the grassy switchback instead of the loose slope and watched the pebbles keep slipping all by themselves.",
        tags={"stones", "slippery"},
    ),
    "low_tunnel": Obstacle(
        id="low_tunnel",
        label="the low tunnel",
        phrase="the low tunnel",
        hazard="bump",
        severity=2,
        clue="A crumb of dust drifted from the low roof and floated through the beam of light.",
        warning="A low roof can bump a hurrying head or catch a lamp held too high",
        crossing="They bent low together, and the light slid neatly along the tunnel wall instead of striking the roof",
        near_miss="The tunnel pinched tighter than it had looked, and the lamp knocked the stone with a bright unhappy tap",
        retreat="They waited for the wider side passage to open in the rocks where everyone could crouch safely.",
        tags={"tunnel", "cave"},
    ),
}

ADJUSTMENTS = {
    "adjust_pack": Adjustment(
        id="adjust_pack",
        label="the pack straps",
        action="adjust the pack straps so the little map bag hugged close instead of swinging wide",
        sloppy="The straps were still loose, and there was no time, he thought, to adjust them properly.",
        guards={"swing"},
        power=2,
        tags={"backpack", "balance"},
    ),
    "balance_pole": Adjustment(
        id="balance_pole",
        label="the walking pole",
        action="adjust the walking pole to the right height and test the ground ahead",
        sloppy="The pole was grabbed in a hurry, without adjusting it to the right height first.",
        guards={"swing", "slip"},
        power=2,
        tags={"pole", "balance"},
    ),
    "tighten_boots": Adjustment(
        id="tighten_boots",
        label="the boot laces",
        action="adjust the boot laces until both boots held snugly at the ankles",
        sloppy="One lace still flapped, because there was no pause to adjust it well.",
        guards={"slip"},
        power=1,
        tags={"boots", "feet"},
    ),
    "lower_lantern": Adjustment(
        id="lower_lantern",
        label="the lantern strap",
        action="adjust the lantern strap lower and practice one crouching step before going in",
        sloppy="The lantern stayed too high because nobody stopped to adjust the strap properly.",
        guards={"bump"},
        power=1,
        tags={"lantern", "cave"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Ava", "Ruby", "Tess", "Zoe", "Ivy"]
BOY_NAMES = ["Finn", "Leo", "Sam", "Max", "Eli", "Theo", "Owen", "Jack"]
GUIDES = ["mother", "father", "grandfather", "grandmother"]


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    adjustment: str
    pace: str
    hero_name: str
    hero_type: str
    buddy_name: str
    buddy_type: str
    guide_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bridge": [
        ("Why can a rope bridge be tricky?",
         "A rope bridge moves when you step on it, so your body has to keep balancing as the bridge swings. Moving slowly helps you answer the swing instead of fighting it.")
    ],
    "stones": [
        ("Why do loose stones make a path slippery?",
         "Loose stones can roll under your feet instead of staying still. That makes it easy to slide or lose balance.")
    ],
    "tunnel": [
        ("Why should you crouch in a low tunnel?",
         "A low tunnel has a roof close above you, so crouching keeps your head and hands from hitting the stone. It also helps you move more carefully.")
    ],
    "backpack": [
        ("Why does a tight backpack feel safer on a narrow path?",
         "A snug backpack stays close to your body instead of swinging from side to side. That makes balancing easier on a wobbly path.")
    ],
    "pole": [
        ("What does a walking pole help you do?",
         "A walking pole gives you another point to steady yourself with. It can also test the ground before you put all your weight down.")
    ],
    "boots": [
        ("Why do tied boots help on a rocky slope?",
         "Boots that fit snugly around your feet and ankles are less likely to slip or wobble. Good footing matters on loose stones.")
    ],
    "lantern": [
        ("Why should a lantern be carried low in a tight tunnel?",
         "A low lantern is less likely to bang into the ceiling. It also lets you see the wall and floor while you crouch.")
    ],
    "foreshadowing": [
        ("What is foreshadowing in a story?",
         "Foreshadowing is an early clue that hints at something important that may happen later. It helps the reader notice danger or change before the big moment arrives.")
    ],
    "adventure": [
        ("What makes something feel like an adventure?",
         "An adventure usually has a goal, a path, and a problem to solve on the way. It feels exciting because the characters must be brave and thoughtful.")
    ],
}
KNOWLEDGE_ORDER = ["foreshadowing", "adventure", "bridge", "stones", "tunnel",
                   "backpack", "pole", "boots", "lantern"]


CURATED = [
    StoryParams(
        setting="forest",
        obstacle="rope_bridge",
        adjustment="adjust_pack",
        pace="careful",
        hero_name="Nora",
        hero_type="girl",
        buddy_name="Finn",
        buddy_type="boy",
        guide_type="grandfather",
        seed=1,
    ),
    StoryParams(
        setting="canyon",
        obstacle="stone_slope",
        adjustment="tighten_boots",
        pace="careful",
        hero_name="Max",
        hero_type="boy",
        buddy_name="Ruby",
        buddy_type="girl",
        guide_type="mother",
        seed=2,
    ),
    StoryParams(
        setting="cliffs",
        obstacle="low_tunnel",
        adjustment="lower_lantern",
        pace="careful",
        hero_name="Ivy",
        hero_type="girl",
        buddy_name="Leo",
        buddy_type="boy",
        guide_type="father",
        seed=3,
    ),
    StoryParams(
        setting="forest",
        obstacle="stone_slope",
        adjustment="balance_pole",
        pace="rushing",
        hero_name="Sam",
        hero_type="boy",
        buddy_name="Tess",
        buddy_type="girl",
        guide_type="grandmother",
        seed=4,
    ),
    StoryParams(
        setting="cliffs",
        obstacle="rope_bridge",
        adjustment="balance_pole",
        pace="rushing",
        hero_name="Ava",
        hero_type="girl",
        buddy_name="Theo",
        buddy_type="boy",
        guide_type="grandfather",
        seed=5,
    ),
]


def explain_rejection(setting: Setting, obstacle: Obstacle, adjustment: Adjustment) -> str:
    if obstacle.id not in setting.affords:
        return (
            f"(No story: {obstacle.label} is not part of the adventure in {setting.place}. "
            f"Pick an obstacle that belongs in that setting.)"
        )
    return (
        f"(No story: {adjustment.label} does not address the danger of {obstacle.label}. "
        f"This world only allows adjustments that match the obstacle's risk.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    buddy = f["buddy"]
    guide = f["guide"]
    setting = f["setting"]
    obstacle = f["obstacle_cfg"]
    adjustment = f["adjustment_cfg"]
    pace = f["pace"]
    if f["outcome"] == "success":
        return [
            f'Write an adventure story for a 3-to-5-year-old that includes the word "adjust" and uses foreshadowing.',
            f"Tell a child-sized adventure where {hero.id} and {buddy.id} notice an early clue at {obstacle.label}, listen to {guide.label_word}, and {adjustment.action}.",
            f"Write a gentle quest set on {setting.place} where a warning clue matters later and careful preparation helps the explorers succeed.",
        ]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the word "adjust" and uses foreshadowing.',
        f"Tell a story where {hero.id} sees an early warning at {obstacle.label} but hurries anyway, so the explorers must turn back and choose the safer route.",
        f"Write a gentle adventure about learning that real explorers listen to clues, pause to adjust their gear, and do not rush into danger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    buddy = f["buddy"]
    guide = f["guide"]
    setting = f["setting"]
    obstacle = f["obstacle_cfg"]
    adjustment = f["adjustment_cfg"]
    pace = f["pace"]
    qa: list[tuple[str, str]] = [
        (
            "Who went on the adventure?",
            f"{hero.id}, {buddy.id}, and {hero.pronoun('possessive')} {guide.label_word} went exploring together. They were looking for {setting.goal}.",
        ),
        (
            "What clue appeared before the hard part of the path?",
            f"The clue was that {obstacle.clue[0].lower() + obstacle.clue[1:]} It foreshadowed that {obstacle.label} might be harder than it first looked.",
        ),
        (
            f"Why did {guide.label_word} tell them to be careful?",
            f"{guide.label_word.capitalize()} used the clue to predict danger at {obstacle.label}. {guide.pronoun().capitalize()} knew that {obstacle.warning.lower()}, so the clue mattered before anyone stepped forward.",
        ),
    ]
    if pace == "careful":
        qa.append(
            (
                f"What did {hero.id} do to get ready?",
                f"{hero.id} stopped to {adjustment.action}. That adjustment matched the obstacle, so it gave the explorers enough steadiness to go on safely.",
            )
        )
    else:
        qa.append(
            (
                f"What mistake did {hero.id} make?",
                f"{hero.id} hurried instead of slowing down to adjust properly. Because of that, the early warning almost turned into a real accident.",
            )
        )
    if f["outcome"] == "success":
        qa.append(
            (
                "How did the story end?",
                f"They crossed safely and found {setting.goal_image}. The ending proves the clue mattered because listening to it changed what they did next.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"They backed away and took the longer safe route instead. The ending proves the clue mattered because it kept the adventure from becoming a bigger problem.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"foreshadowing", "adventure"} | set(f["obstacle_cfg"].tags) | set(f["adjustment_cfg"].tags)
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


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(S, O, A) :- setting(S), obstacle(O), adjustment(A),
                  affords(S, O), hazard_of(O, H), guards(A, H).

% --- outcome model ---------------------------------------------------------
pace_bonus(1) :- pace(careful).
pace_bonus(0) :- pace(rushing).
score(P) :- chosen_adjustment(A), power(A, AP), pace_bonus(PB), P = AP + PB.
success :- chosen_obstacle(O), severity(O, S), score(P), P >= S.
outcome(success) :- success.
outcome(retreat) :- not success.
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
        lines.append(asp.fact("hazard_of", obstacle_id, obstacle.hazard))
        lines.append(asp.fact("severity", obstacle_id, obstacle.severity))
    for adjustment_id, adjustment in ADJUSTMENTS.items():
        lines.append(asp.fact("adjustment", adjustment_id))
        lines.append(asp.fact("power", adjustment_id, adjustment.power))
        for hazard in sorted(adjustment.guards):
            lines.append(asp.fact("guards", adjustment_id, hazard))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_adjustment", params.adjustment),
        asp.fact("pace", params.pace),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
        except StoryError:
            bad += 1
            continue
        asp_val = asp_outcome(params)
        if py != asp_val:
            bad += 1
            print(f"MISMATCH outcome for {params}: python={py} asp={asp_val}")
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcome cases differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        with redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke generate/emit run succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure story world with foreshadowing, a needed adjustment, and a safe ending or turn-back."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--adjustment", choices=ADJUSTMENTS)
    ap.add_argument("--pace", choices=["careful", "rushing"])
    ap.add_argument("--hero-name")
    ap.add_argument("--buddy-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--buddy-type", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle and args.adjustment:
        if not valid_combo(args.setting, args.obstacle, args.adjustment):
            raise StoryError(explain_rejection(SETTINGS[args.setting], OBSTACLES[args.obstacle],
                                               ADJUSTMENTS[args.adjustment]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.adjustment is None or combo[2] == args.adjustment)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, adjustment_id = rng.choice(sorted(combos))
    pace = args.pace or rng.choice(["careful", "rushing"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    buddy_type = args.buddy_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    buddy_name = args.buddy_name or _pick_name(rng, buddy_type, avoid=hero_name)
    guide_type = args.guide or rng.choice(GUIDES)

    params = StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        adjustment=adjustment_id,
        pace=pace,
        hero_name=hero_name,
        hero_type=hero_type,
        buddy_name=buddy_name,
        buddy_type=buddy_type,
        guide_type=guide_type,
        seed=None,
    )
    outcome_of(params)
    return params


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.adjustment not in ADJUSTMENTS:
        raise StoryError(f"(Invalid adjustment: {params.adjustment})")
    if params.pace not in {"careful", "rushing"}:
        raise StoryError(f"(Invalid pace: {params.pace})")
    if not valid_combo(params.setting, params.obstacle, params.adjustment):
        raise StoryError(explain_rejection(SETTINGS[params.setting], OBSTACLES[params.obstacle],
                                           ADJUSTMENTS[params.adjustment]))

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle_cfg=OBSTACLES[params.obstacle],
        adjustment_cfg=ADJUSTMENTS[params.adjustment],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        buddy_name=params.buddy_name,
        buddy_type=params.buddy_type,
        guide_type=params.guide_type,
        pace=params.pace,
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
        print(f"{len(combos)} compatible (setting, obstacle, adjustment) combos:\n")
        for setting_id, obstacle_id, adjustment_id in combos:
            print(f"  {setting_id:8} {obstacle_id:12} {adjustment_id}")
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
            header = f"### {p.hero_name} & {p.buddy_name}: {p.obstacle} at {p.setting} ({p.adjustment}, {p.pace}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
