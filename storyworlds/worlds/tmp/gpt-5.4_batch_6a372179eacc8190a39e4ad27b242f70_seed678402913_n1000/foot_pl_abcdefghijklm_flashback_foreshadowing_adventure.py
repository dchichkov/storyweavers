#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/foot_pl_abcdefghijklm_flashback_foreshadowing_adventure.py
=====================================================================================

A standalone storyworld for a tiny adventure domain built around two children,
a scribbled map, and a hidden prize. The map always includes the odd words
"foot-pl" and "abcdefghijklm". The world uses:

- foreshadowing: an early sign that the path ahead is getting trickier
- flashback: a remembered lesson about the tool that makes the passage safe

The simulation models a small obstacle on the way to the prize. The children
can only have a story if the chosen place really contains that obstacle and the
chosen tool genuinely handles it. The ending varies by timing:

- same_day: the tool is strong enough for today's obstacle level
- next_morning: the children wisely stop, return with a grown-up, and finish later

Run it
------
python storyworlds/worlds/gpt-5.4/foot_pl_abcdefghijklm_flashback_foreshadowing_adventure.py
python storyworlds/worlds/gpt-5.4/foot_pl_abcdefghijklm_flashback_foreshadowing_adventure.py --all
python storyworlds/worlds/gpt-5.4/foot_pl_abcdefghijklm_flashback_foreshadowing_adventure.py --place pine_woods --obstacle cave --tool lantern
python storyworlds/worlds/gpt-5.4/foot_pl_abcdefghijklm_flashback_foreshadowing_adventure.py --obstacle marsh --tool gloves
python storyworlds/worlds/gpt-5.4/foot_pl_abcdefghijklm_flashback_foreshadowing_adventure.py --qa --json
python storyworlds/worlds/gpt-5.4/foot_pl_abcdefghijklm_flashback_foreshadowing_adventure.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so the package directory is
# three levels up from here.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type or self.label)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
    opening: str = ""
    horizon: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    base: int
    warning: str
    omen: str
    risk: str
    crossing: str
    help_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    power: int = 0
    flashback: str = ""
    use_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World + rules
# ---------------------------------------------------------------------------
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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.characters() if e.role in {"leader", "partner"}]

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


def _r_scare(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.entities.get("obstacle")
    if obstacle is None or obstacle.meters["unsafe_try"] < THRESHOLD:
        return out
    sig = ("scare", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obstacle.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__scare__")
    return out


def _r_reward(world: World) -> list[str]:
    out: list[str] = []
    prize = world.entities.get("prize")
    if prize is None or prize.meters["found"] < THRESHOLD:
        return out
    sig = ("reward", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    out.append("__reward__")
    return out


CAUSAL_RULES = [
    Rule(name="scare", tag="physical", apply=_r_scare),
    Rule(name="reward", tag="emotional", apply=_r_reward),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def tool_fits(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.id in tool.handles


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for obstacle_id in sorted(setting.affords):
            obstacle = OBSTACLES[obstacle_id]
            for tool_id, tool in TOOLS.items():
                if not tool_fits(obstacle, tool):
                    continue
                for prize_id in PRIZES:
                    combos.append((place_id, obstacle_id, tool_id, prize_id))
    return combos


def severity_of(obstacle: Obstacle, delay: int) -> int:
    return obstacle.base + delay


def same_day_success(obstacle: Obstacle, tool: Tool, delay: int) -> bool:
    return tool.power >= severity_of(obstacle, delay)


def predict_risk(world: World) -> dict:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    obstacle.meters["unsafe_try"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": obstacle.meters["danger"],
        "fear": sum(k.memes["fear"] for k in sim.kids()),
    }


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def introduce_map(world: World, leader: Entity, partner: Entity, parent: Entity) -> None:
    leader.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"After breakfast, {leader.id} and {partner.id} found a rolled paper tube on the step. "
        f"It was tied with blue string, and {parent.label_word} had drawn a tiny star on the knot."
    )
    world.say(
        f"When {leader.id} opened it, a hand-drawn map curled across {leader.pronoun('possessive')} knees. "
        f"Near one corner it said 'foot-pl', and under that someone had written "
        f"'abcdefghijklm' in neat little letters."
    )


def explain_quest(world: World, leader: Entity, partner: Entity, prize: Prize) -> None:
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f'A note on the back said, "Follow the clue trail and find {prize.phrase} before the day grows tricky." '
        f"At once the two children stood taller, as if they had just been made captains of an adventure."
    )
    world.say(
        f"They decided that 'foot-pl' must mean the place where the first footprints should begin, "
        f"so they tucked the map close and hurried toward {world.setting.place}."
    )


def arrive(world: World, leader: Entity, partner: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"{world.setting.opening} {world.setting.horizon}"
    )
    world.say(
        f"The map line for this part ended at {obstacle.phrase}. "
        f"{partner.id} pointed to the dark mark on the page and whispered, "
        f'"That must be the next gate."'
    )


def foreshadow(world: World, obstacle: Obstacle) -> None:
    world.facts["omen_text"] = obstacle.omen
    world.say(
        f"But before they went farther, {obstacle.omen} "
        f"It was the sort of small sign that made the adventure feel larger than a game."
    )


def warn(world: World, partner: Entity, obstacle: Obstacle) -> None:
    pred = predict_risk(world)
    world.facts["predicted_danger"] = pred["danger"]
    partner.memes["care"] += 1
    world.say(
        f'{partner.id} studied {obstacle.label} and said, "{obstacle.warning}" '
        f"{partner.pronoun().capitalize()} could almost picture the trouble already, "
        f"because one rushed step there would turn exciting in the wrong way."
    )


def rush(world: World, leader: Entity, obstacle_ent: Entity, obstacle: Obstacle) -> None:
    leader.memes["boldness"] += 1
    obstacle_ent.meters["unsafe_try"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{leader.id} took one quick step toward {obstacle.phrase}, ready to dash through by guesswork alone."
    )
    if obstacle_ent.meters["danger"] >= THRESHOLD:
        world.say(
            f"Then {leader.pronoun('possessive')} stomach gave a little flip. {obstacle.risk}"
        )


def flashback(world: World, leader: Entity, parent: Entity, tool: Tool) -> None:
    leader.memes["memory"] += 1
    world.facts["flashback_text"] = tool.flashback
    world.say(
        f"That was when a flashback rose in {leader.id}'s mind: {tool.flashback} "
        f"The memory landed so clearly that it felt like a lantern being lit inside {leader.pronoun('possessive')} thoughts."
    )


def choose_tool(world: World, leader: Entity, partner: Entity, tool: Tool) -> None:
    leader.memes["resolve"] += 1
    partner.memes["trust"] += 1
    world.say(
        f'"Wait," {leader.id} said. "We brought {tool.phrase} for a reason." '
        f"{partner.id} grinned and reached for it at once."
    )


def cross_same_day(world: World, leader: Entity, partner: Entity, obstacle_ent: Entity,
                   obstacle: Obstacle, tool: Tool) -> None:
    obstacle_ent.meters["passed"] += 1
    world.say(
        f"Using {tool.phrase}, they {tool.use_text}. "
        f"{obstacle.crossing}"
    )
    world.say(
        f"On the far side, the path felt wide again, and both children breathed out at the same time."
    )


def find_prize(world: World, leader: Entity, partner: Entity, prize_ent: Entity, prize: Prize) -> None:
    prize_ent.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Behind a flat stone they found {prize.phrase}. Inside lay a paper star and a folded card that repeated "
        f"'abcdefghijklm' as if it were the song of the trail."
    )
    world.say(
        f"On the last line the card said, 'Brave feet do not rush. Brave feet notice.' "
        f"{leader.id} laughed softly. Suddenly the silly map word 'foot-pl' seemed perfect after all."
    )
    world.say(prize.ending_image)


def turn_back(world: World, leader: Entity, partner: Entity, parent: Entity,
              obstacle: Obstacle, tool: Tool) -> None:
    leader.memes["wisdom"] += 1
    partner.memes["relief"] += 1
    world.say(
        f"They held {tool.phrase} ready, but another look at {obstacle.phrase} told them the day had turned too tricky. "
        f'"Not every brave plan has to happen right now," {partner.id} said.'
    )
    world.say(
        f"{leader.id} nodded. This time bravery meant turning back while the path was still theirs to choose."
    )
    world.say(
        f"They hurried home, showed the map to {parent.label_word}, and told the whole story from the first clue to the warning sign."
    )


def return_next_morning(world: World, leader: Entity, partner: Entity, parent: Entity,
                        obstacle: Obstacle, tool: Tool, prize_ent: Entity, prize: Prize) -> None:
    parent.memes["care"] += 1
    world.say(
        f"The next morning, with the sun steady and {parent.label_word} beside them, they returned to {world.setting.place}. "
        f"{obstacle.help_line}"
    )
    world.say(
        f"Together they used {tool.phrase}, and this time the way opened without hurry."
    )
    prize_ent.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Beyond {obstacle.phrase} they found {prize.phrase}, still dry and waiting. "
        f"Inside was the same paper star and the same line of 'abcdefghijklm', but now it felt less like a secret code and more like a cheer."
    )
    world.say(
        f"{leader.id} tapped the map and smiled at 'foot-pl'. It was not just the start of footprints anymore. "
        f"It was the place where they had learned when to go on and when to wait."
    )
    world.say(prize.ending_image)


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(setting: Setting, obstacle: Obstacle, tool: Tool, prize: Prize,
         leader_name: str = "Nora", leader_type: str = "girl",
         partner_name: str = "Finn", partner_type: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World(setting)
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_type, role="leader"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type, role="partner"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    obstacle_ent = world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label, phrase=obstacle.phrase))
    prize_ent = world.add(Entity(id="prize", type="prize", label=prize.label, phrase=prize.phrase, owner=leader.id))
    map_ent = world.add(Entity(id="map", type="map", label="map", phrase="a rolled map"))
    map_ent.attrs["mark1"] = "foot-pl"
    map_ent.attrs["mark2"] = "abcdefghijklm"

    introduce_map(world, leader, partner, parent)
    explain_quest(world, leader, partner, prize)

    world.para()
    arrive(world, leader, partner, obstacle)
    foreshadow(world, obstacle)
    warn(world, partner, obstacle)
    rush(world, leader, obstacle_ent, obstacle)

    world.para()
    flashback(world, leader, parent, tool)
    choose_tool(world, leader, partner, tool)

    same_day = same_day_success(obstacle, tool, delay)
    if same_day:
        cross_same_day(world, leader, partner, obstacle_ent, obstacle, tool)
        world.para()
        find_prize(world, leader, partner, prize_ent, prize)
        outcome = "same_day"
    else:
        turn_back(world, leader, partner, parent, obstacle, tool)
        world.para()
        return_next_morning(world, leader, partner, parent, obstacle, tool, prize_ent, prize)
        outcome = "next_morning"

    world.facts.update(
        leader=leader,
        partner=partner,
        parent=parent,
        obstacle_cfg=obstacle,
        obstacle=obstacle_ent,
        tool=tool,
        prize_cfg=prize,
        prize=prize_ent,
        map=map_ent,
        place=setting,
        delay=delay,
        severity=severity_of(obstacle, delay),
        outcome=outcome,
        same_day=same_day,
        predicted_danger=world.facts.get("predicted_danger", 0),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "river_trail": Setting(
        id="river_trail",
        place="the river trail",
        affords={"marsh", "thorns"},
        opening="The river trail curled between silver reeds and flat stepping stones.",
        horizon="Far ahead, dragonflies flashed like tiny badges over the water.",
        tags={"river", "trail"},
    ),
    "pine_woods": Setting(
        id="pine_woods",
        place="the pine woods",
        affords={"thorns", "cave"},
        opening="The pine woods smelled sharp and green, and the ground was soft with old needles.",
        horizon="Between the trunks, the path kept slipping into pockets of shadow.",
        tags={"woods", "trail"},
    ),
    "cliff_cove": Setting(
        id="cliff_cove",
        place="the cliff cove",
        affords={"cave", "marsh"},
        opening="The cliff cove glittered with salt light, and gulls wheeled above the rocks.",
        horizon="Every sound bounced from stone to stone and came back a little grander.",
        tags={"sea", "cove"},
    ),
}

OBSTACLES = {
    "marsh": Obstacle(
        id="marsh",
        label="the reed marsh",
        phrase="a reed marsh with wobbling grass islands",
        base=2,
        warning="If we rush, one foot will slide into the cold mud and the map will go with it.",
        omen="the thin water between the reeds was already spreading over the stepping grass",
        risk="The ground ahead looked less like a path and more like a trap that smiled politely.",
        crossing="Step by step, they reached the firm bank without losing so much as a shoelace.",
        help_line="With slower light and calmer water, the marsh no longer looked hungry.",
        tags={"marsh", "wet"},
    ),
    "thorns": Obstacle(
        id="thorns",
        label="the thorn arch",
        phrase="a thorn arch where blackberry vines hooked across the path",
        base=2,
        warning="If we push in bare-handed, those hooks will grab us and tear the map.",
        omen="the wind shook the blackberry vines until their little hooks flashed in the sun",
        risk="What had looked like a doorway a minute earlier now looked very much like it could bite.",
        crossing="The thorny arch opened a safe little lane, just wide enough for two determined explorers.",
        help_line="In the morning, even the vines seemed less wild, as if night had taught them manners.",
        tags={"thorns", "plants"},
    ),
    "cave": Obstacle(
        id="cave",
        label="the echo cave",
        phrase="an echo cave with a low stone mouth",
        base=2,
        warning="If we go in dark, we could miss the safe ledge and bump into the wet wall.",
        omen="the cave mouth was already filling with shadow even though the afternoon was not over yet",
        risk="The dark inside did not feel empty. It felt full of places where a wrong step could hide.",
        crossing="Their light slid over the wall, found the narrow ledge, and led them through the cool hush.",
        help_line="Morning light waited at the cave mouth, and with a grown-up near, the dark stopped feeling bossy.",
        tags={"cave", "dark"},
    ),
}

TOOLS = {
    "boots": Tool(
        id="boots",
        label="boots",
        phrase="their tall marsh boots",
        handles={"marsh"},
        power=2,
        flashback="last week, their mom had laughed in the yard while showing them how to test soft ground with one boot before trusting the next step",
        use_text="they tapped each patch of grass before stepping and kept the map high and dry",
        tags={"boots", "wet"},
    ),
    "wading_board": Tool(
        id="wading_board",
        label="wading board",
        phrase="the flat wading board they had dragged from the shed",
        handles={"marsh"},
        power=3,
        flashback="their dad once laid a board over a muddy ditch and said that adventures went better when your feet had a plan",
        use_text="they slid the board from tuft to tuft and crossed on a path of their own making",
        tags={"board", "wet"},
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="their garden gloves",
        handles={"thorns"},
        power=2,
        flashback="their aunt had shown them in the tomato patch how thick gloves turned grabbing vines from a sting into simple work",
        use_text="they lifted the curling vines aside and made a careful doorway through the hooks",
        tags={"gloves", "plants"},
    ),
    "clippers": Tool(
        id="clippers",
        label="clippers",
        phrase="the little berry clippers wrapped in a cloth",
        handles={"thorns"},
        power=3,
        flashback="their uncle had once snipped dead blackberry canes and said sharp tools were for patient hands, never hurrying hands",
        use_text="they clipped only the tangles blocking the path and left the berries nodding safely above them",
        tags={"clippers", "plants"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="their small brass lantern",
        handles={"cave"},
        power=2,
        flashback="one stormy evening, their mom had turned off the hall light and taught them how a steady lantern showed edges, puddles, and places not to trust",
        use_text="they held the lantern low, let the light find the ledge, and followed it instead of guessing",
        tags={"lantern", "dark"},
    ),
    "headlamp": Tool(
        id="headlamp",
        label="headlamp",
        phrase="the bright headlamp from the camping shelf",
        handles={"cave"},
        power=3,
        flashback="their dad had buckled the headlamp on a camping night and said that the best adventure light left both hands free for careful balance",
        use_text="they clicked on the headlamp and kept both hands ready against the cool stone while the beam searched ahead",
        tags={"headlamp", "dark"},
    ),
}

PRIZES = {
    "star_box": Prize(
        id="star_box",
        label="star box",
        phrase="a small tin star box",
        ending_image="They carried the star box home between them, and even the plain path back felt like part of the map now.",
        tags={"treasure", "box"},
    ),
    "compass_tin": Prize(
        id="compass_tin",
        label="compass tin",
        phrase="a red compass tin",
        ending_image="The red tin glowed in their hands, and the afternoon suddenly seemed to point in the right direction too.",
        tags={"treasure", "compass"},
    ),
    "ribbon_flag": Prize(
        id="ribbon_flag",
        label="ribbon flag",
        phrase="a rolled ribbon flag",
        ending_image="When the ribbon flag fluttered open, it made the air around them feel as brave and bright as a parade.",
        tags={"treasure", "flag"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Maya", "Lucy", "Anna", "Rose"]
BOY_NAMES = ["Finn", "Leo", "Ben", "Max", "Sam", "Theo", "Noah", "Jack", "Eli", "Tom"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    obstacle: str
    tool: str
    prize: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="river_trail",
        obstacle="marsh",
        tool="boots",
        prize="star_box",
        leader_name="Nora",
        leader_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        place="pine_woods",
        obstacle="cave",
        tool="lantern",
        prize="compass_tin",
        leader_name="Leo",
        leader_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        parent="father",
        delay=1,
    ),
    StoryParams(
        place="river_trail",
        obstacle="thorns",
        tool="clippers",
        prize="ribbon_flag",
        leader_name="Ava",
        leader_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        parent="aunt",
        delay=1,
    ),
    StoryParams(
        place="cliff_cove",
        obstacle="marsh",
        tool="wading_board",
        prize="compass_tin",
        leader_name="Sam",
        leader_gender="boy",
        partner_name="Rose",
        partner_gender="girl",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        place="pine_woods",
        obstacle="thorns",
        tool="gloves",
        prize="star_box",
        leader_name="Ella",
        leader_gender="girl",
        partner_name="Tom",
        partner_gender="boy",
        parent="uncle",
        delay=2,
    ),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story shows a small hint early that tells you something important may happen later. It helps the middle of the story feel connected instead of sudden."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short memory from earlier that pops into the story. It can explain why a character knows what to do now."
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map helps you find where things are and which way to go. It gives clues so you do not have to wander by guessing."
        )
    ],
    "boots": [
        (
            "Why are boots good in wet ground?",
            "Boots help keep your feet dry and steady in wet, muddy places. They also make it easier to test the ground before putting your full weight down."
        )
    ],
    "board": [
        (
            "Why can a board help over mud?",
            "A flat board spreads your weight over more ground, so you are less likely to sink. It can turn a squishy patch into a steadier path."
        )
    ],
    "gloves": [
        (
            "Why do gloves help with thorny plants?",
            "Gloves cover your hands so sharp thorns do not poke your skin as easily. They let you move a vine carefully instead of yanking it bare-handed."
        )
    ],
    "clippers": [
        (
            "What are clippers for in a garden?",
            "Clippers are small cutting tools for trimming stems and vines. Grown-ups or careful helpers use them slowly so they cut only what needs cutting."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful in the dark?",
            "A lantern makes a steady light so you can see edges, puddles, and safe places to step. Good light turns guessing into noticing."
        )
    ],
    "headlamp": [
        (
            "Why might someone use a headlamp instead of holding a flashlight?",
            "A headlamp shines where you look and leaves both hands free. That helps when you need to balance or touch a wall carefully."
        )
    ],
    "marsh": [
        (
            "What is a marsh?",
            "A marsh is a wet place with shallow water, mud, and plants like reeds. Some spots look firm but can feel soft when you step on them."
        )
    ],
    "thorns": [
        (
            "What are thorns?",
            "Thorns are sharp points on some plants. They help protect the plant, but they can scratch your skin if you grab them carelessly."
        )
    ],
    "cave": [
        (
            "Why can a cave feel tricky to walk through?",
            "Caves can be dark, damp, and full of uneven ground. Without enough light, it is easy to miss where the safe path is."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "foreshadowing",
    "flashback",
    "map",
    "boots",
    "board",
    "gloves",
    "clippers",
    "lantern",
    "headlamp",
    "marsh",
    "thorns",
    "cave",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool"]
    prize = f["prize_cfg"]
    outcome = f["outcome"]
    if outcome == "same_day":
        ending = "and they reach the prize before sunset"
    else:
        ending = "and they wisely return with a grown-up the next morning"
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the exact words "foot-pl" and "abcdefghijklm", uses both foreshadowing and a flashback, and ends happily.',
        f"Tell an adventure about {leader.id} and {partner.id} following a strange map to {prize.phrase}, facing {obstacle.phrase}, remembering how to use {tool.phrase}, {ending}.",
        f'Write a child-facing quest story where an early warning sign hints at trouble ahead, a memory helps solve the problem, and the odd clue words "foot-pl" and "abcdefghijklm" both matter to the adventure.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    parent = f["parent"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool"]
    prize = f["prize_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What started the adventure?",
            f"The children found a rolled map with the words 'foot-pl' and 'abcdefghijklm' on it. The map promised a hidden prize, so they set off to follow the clues."
        ),
        (
            "What was the foreshadowing in the story?",
            f"The foreshadowing was the early warning sign at {obstacle.phrase}: {f.get('omen_text', obstacle.omen)}. That hint told the reader the path might get harder before the prize was found."
        ),
        (
            f"What flashback helped {leader.id}?",
            f"{leader.id} remembered this earlier lesson: {f.get('flashback_text', tool.flashback)}. That memory mattered because it explained why {leader.pronoun()} knew how to use {tool.phrase} instead of rushing."
        ),
        (
            f"Why was {partner.id} worried about the path?",
            f"{partner.id} could see that a careless step at {obstacle.phrase} would be unsafe. The warning mattered because the children were excited, and excitement can make feet move faster than thinking."
        ),
    ]
    if outcome == "same_day":
        qa.append(
            (
                f"How did they get past {obstacle.label}?",
                f"They used {tool.phrase} and moved carefully instead of guessing. That worked because {tool.label} matched the problem the path was giving them."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They found {prize.phrase} the same day and read the note inside. The ending proves they changed, because they won the adventure by noticing and slowing down."
            )
        )
    else:
        qa.append(
            (
                "Why did they turn back at first?",
                f"They had the right tool, but the path had become too tricky for that day. Turning back was wise because waiting kept the adventure safe instead of reckless."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They returned the next morning with {parent.label_word} and then found {prize.phrase}. The ending proves they changed, because they learned that brave explorers do not always hurry."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"foreshadowing", "flashback", "map"}
    tags |= set(f["tool"].tags)
    tags |= set(f["obstacle_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


# ---------------------------------------------------------------------------
# Trace / rejection help
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place_id: str, obstacle_id: str, tool_id: str) -> str:
    setting = SETTINGS[place_id]
    obstacle = OBSTACLES[obstacle_id]
    tool = TOOLS[tool_id]
    if obstacle_id not in setting.affords:
        options = ", ".join(sorted(setting.affords))
        return (
            f"(No story: {setting.place} does not contain {obstacle.label} in this world. "
            f"That place supports only: {options}.)"
        )
    if not tool_fits(obstacle, tool):
        options = ", ".join(sorted(tid for tid, t in TOOLS.items() if tool_fits(obstacle, t)))
        return (
            f"(No story: {tool.label} is not a reasonable way through {obstacle.label}. "
            f"Try one of: {options}.)"
        )
    return "(No story: this combination does not fit the world.)"


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    return "same_day" if same_day_success(obstacle, tool, params.delay) else "next_morning"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P, O, T, Z) :- place(P), prize(Z), affords(P, O), handles(T, O).

severity(B + D) :- chosen_obstacle(O), base(O, B), delay(D).
same_day        :- chosen_tool(T), power(T, P), severity(S), P >= S.

outcome(same_day)      :- same_day.
outcome(next_morning)  :- not same_day.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("base", obstacle_id, obstacle.base))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        for obstacle_id in sorted(tool.handles):
            lines.append(asp.fact("handles", tool_id, obstacle_id))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_tool", params.tool),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        if smoke.world is None:
            raise StoryError("missing world in smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld with a clue map, foreshadowing, flashback, and a safe obstacle crossing."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how tricky the day has become by the time they reach the obstacle")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place
    obstacle_id = args.obstacle
    tool_id = args.tool
    prize_id = args.prize

    if place_id and obstacle_id and tool_id:
        if obstacle_id not in SETTINGS[place_id].affords or not tool_fits(OBSTACLES[obstacle_id], TOOLS[tool_id]):
            raise StoryError(explain_rejection(place_id, obstacle_id, tool_id))
    elif place_id and obstacle_id and obstacle_id not in SETTINGS[place_id].affords:
        sample_tool = next(iter(TOOLS))
        raise StoryError(explain_rejection(place_id, obstacle_id, sample_tool))
    elif obstacle_id and tool_id and not tool_fits(OBSTACLES[obstacle_id], TOOLS[tool_id]):
        sample_place = next(pid for pid, s in SETTINGS.items() if obstacle_id in s.affords)
        raise StoryError(explain_rejection(sample_place, obstacle_id, tool_id))

    combos = [
        combo for combo in valid_combos()
        if (place_id is None or combo[0] == place_id)
        and (obstacle_id is None or combo[1] == obstacle_id)
        and (tool_id is None or combo[2] == tool_id)
        and (prize_id is None or combo[3] == prize_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, tool_id, prize_id = rng.choice(sorted(combos))
    leader_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    leader_name = _pick_name(rng, leader_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=leader_name)
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        tool=tool_id,
        prize=prize_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.obstacle not in SETTINGS[params.place].affords:
        raise StoryError(explain_rejection(params.place, params.obstacle, params.tool))
    if not tool_fits(OBSTACLES[params.obstacle], TOOLS[params.tool]):
        raise StoryError(explain_rejection(params.place, params.obstacle, params.tool))

    world = tell(
        setting=SETTINGS[params.place],
        obstacle=OBSTACLES[params.obstacle],
        tool=TOOLS[params.tool],
        prize=PRIZES[params.prize],
        leader_name=params.leader_name,
        leader_type=params.leader_gender,
        partner_name=params.partner_name,
        partner_type=params.partner_gender,
        parent_type=params.parent,
        delay=params.delay,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, tool, prize) combos:\n")
        for place_id, obstacle_id, tool_id, prize_id in combos:
            print(f"  {place_id:11} {obstacle_id:8} {tool_id:12} {prize_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.leader_name} & {p.partner_name}: {p.place}, {p.obstacle}, "
                f"{p.tool}, {outcome_of(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
