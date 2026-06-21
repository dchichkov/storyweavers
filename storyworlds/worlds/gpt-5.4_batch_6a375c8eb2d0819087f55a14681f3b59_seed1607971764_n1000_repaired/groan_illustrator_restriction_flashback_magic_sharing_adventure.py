#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/groan_illustrator_restriction_flashback_magic_sharing_adventure.py
================================================================================================

A standalone storyworld about a small adventure powered by a magic drawing tool.
The central constraint is simple and child-legible: the old illustrator's magic
only works when it is shared. The world model carries physical meters and
emotional memes, includes a flashback beat, and rejects combinations where the
chosen magic tool cannot honestly solve the obstacle.

Run it
------
    python storyworlds/worlds/gpt-5.4/groan_illustrator_restriction_flashback_magic_sharing_adventure.py
    python storyworlds/worlds/gpt-5.4/groan_illustrator_restriction_flashback_magic_sharing_adventure.py --setting cliff_path --obstacle ravine
    python storyworlds/worlds/gpt-5.4/groan_illustrator_restriction_flashback_magic_sharing_adventure.py --tool chalk --obstacle dark_gate
    python storyworlds/worlds/gpt-5.4/groan_illustrator_restriction_flashback_magic_sharing_adventure.py --all
    python storyworlds/worlds/gpt-5.4/groan_illustrator_restriction_flashback_magic_sharing_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/groan_illustrator_restriction_flashback_magic_sharing_adventure.py --json
    python storyworlds/worlds/gpt-5.4/groan_illustrator_restriction_flashback_magic_sharing_adventure.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    goal: str
    vista: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    makes: str
    draw_verb: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Obstacle:
    id: str
    label: str
    trouble: str
    need: str
    solved_by: str
    danger: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Flashback:
    id: str
    keeper_type: str
    keeper_label: str
    memory: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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


def tool_solves(tool: Tool, obstacle: Obstacle) -> bool:
    return tool.makes == obstacle.solved_by


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for tool_id, tool in TOOLS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                if not tool_solves(tool, obstacle):
                    continue
                for treasure_id in TREASURES:
                    combos.append((setting_id, tool_id, obstacle_id, treasure_id))
    return combos


def explain_rejection(tool: Tool, obstacle: Obstacle) -> str:
    return (
        f"(No story: {tool.phrase} makes {tool.makes}, but {obstacle.label} needs "
        f"{obstacle.need}. Pick a tool that can honestly solve the obstacle.)"
    )


def introduce(world: World, leader: Entity, partner: Entity, setting: Setting, treasure: Treasure) -> None:
    leader.memes["wonder"] += 1
    partner.memes["wonder"] += 1
    world.say(
        f"At the edge of {setting.place}, {leader.id} and {partner.id} set off on an adventure "
        f"to find {treasure.phrase} at {setting.goal}. {setting.vista}"
    )
    world.say(
        f"They carried a satchel with crumbly paper, a compass, and one old drawing tool wrapped in blue cloth."
    )


def discover_magic(world: World, leader: Entity, partner: Entity, tool: Tool) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["glow"] += 1
    leader.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"When {leader.id} unwrapped the cloth, {tool.phrase} gave a tiny golden shimmer. "
        f'"This must be the magic one," {partner.id} whispered.'
    )


def state_restriction(world: World, leader: Entity, tool: Tool) -> None:
    leader.memes["greed"] += 1
    world.facts["restriction_heard"] = True
    world.say(
        f"On the handle, in silver letters, was one restriction: "
        f'"Pass the {tool.label} hand to hand, or the drawing will not wake."'
    )


def flashback(world: World, keeper: Entity, flash: Flashback, tool: Tool) -> None:
    keeper.memes["memory"] += 1
    world.facts["flashback_used"] = True
    world.say(
        f"That warning pulled a flashback into {keeper.id}'s mind. {flash.memory}"
    )
    world.say(
        f"In the memory, the old illustrator smiled and tapped {tool.phrase}. "
        f'"{flash.lesson}"'
    )


def approach_obstacle(world: World, leader: Entity, partner: Entity, obstacle: Obstacle) -> None:
    world.get("obstacle").meters["blocking"] += 1
    leader.memes["concern"] += 1
    partner.memes["concern"] += 1
    world.say(
        f"Farther up the trail they met {obstacle.label}. {obstacle.trouble}"
    )
    world.say(
        f"{partner.id} let out a small groan. If they turned back now, the adventure would end before they reached the top."
    )


def clutch_and_fail(world: World, leader: Entity, partner: Entity, tool: Tool, obstacle: Obstacle) -> None:
    leader.memes["selfish"] += 1
    leader.memes["frustration"] += 1
    partner.memes["hurt"] += 1
    tool_ent = world.get("tool")
    tool_ent.meters["silent"] += 1
    world.facts["solo_failed"] = True
    world.say(
        f"{leader.id} hugged the {tool.label} to {leader.pronoun('possessive')} chest. "
        f'"I can do it myself," {leader.pronoun()} said, and {leader.pronoun()} {tool.draw_verb} a quick line in the air.'
    )
    world.say(
        f"But the line only flickered and vanished. The magic stayed still, because the restriction had been broken."
    )
    if obstacle.id == "ravine":
        world.say(
            f"Below them, pebbles skipped into the gap, and the empty space answered with a long windy sound."
        )
    elif obstacle.id == "dark_gate":
        world.say(
            f"The stone arch gave a low cavey echo, as if the dark itself were waiting."
        )
    else:
        world.say(
            f"The thorns rustled and bent, but they did not open enough to let anyone through."
        )


def share_and_solve(world: World, leader: Entity, partner: Entity, tool: Tool, obstacle: Obstacle) -> None:
    leader.memes["sharing"] += 1
    partner.memes["sharing"] += 1
    leader.memes["trust"] += 1
    partner.memes["trust"] += 1
    leader.memes["frustration"] = 0.0
    partner.memes["hurt"] = 0.0
    tool_ent = world.get("tool")
    tool_ent.meters["glow"] += 1
    tool_ent.meters["shared"] += 1
    world.get("obstacle").meters["blocking"] = 0.0
    world.get("obstacle").meters["solved"] += 1
    world.facts["shared"] = True
    world.say(
        f"{leader.id} took a breath, remembered the flashback, and passed the {tool.label} to {partner.id}. "
        f"Then they held it together, one small hand above the other."
    )
    if obstacle.solved_by == "bridge":
        world.say(
            f"As they traced a shining bridge from one side to the other, boards bloomed out of the air and settled across the ravine. "
            f"The magic worked because they were sharing it."
        )
    elif obstacle.solved_by == "light":
        world.say(
            f"As they drew a bright lantern shape together, warm light poured from the line and filled the gate tunnel. "
            f"The magic worked because they were sharing it."
        )
    else:
        world.say(
            f"As they sketched a curling key-vine together, the thorn wall gently untwisted and opened a safe doorway. "
            f"The magic worked because they were sharing it."
        )


def reach_goal(world: World, leader: Entity, partner: Entity, setting: Setting, treasure: Treasure) -> None:
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.get("treasure").meters["found"] += 1
    world.say(
        f"Past the obstacle, the path finally lifted them to {setting.goal}, where they found {treasure.phrase}."
    )
    world.say(
        f"They did not grab it apart. Instead they opened it together, and {treasure.ending}"
    )


def closing_image(world: World, leader: Entity, partner: Entity, tool: Tool) -> None:
    world.say(
        f"On the way home, the {tool.label} rode between them in the same blue cloth, and neither child tried to keep it alone. "
        f"The adventure had taught them the oldest magic in the satchel: sharing makes the picture real."
    )


def tell(
    setting: Setting,
    tool: Tool,
    obstacle: Obstacle,
    treasure: Treasure,
    flash: Flashback,
    leader_name: str = "Mira",
    leader_gender: str = "girl",
    partner_name: str = "Tao",
    partner_gender: str = "boy",
) -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    keeper = world.add(Entity(id=flash.keeper_label, kind="character", type=flash.keeper_type, role="keeper", label=flash.keeper_label))
    world.add(Entity(id="tool", type="tool", label=tool.label))
    world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label))
    world.add(Entity(id="treasure", type="treasure", label=treasure.label))

    world.facts.update(
        leader=leader,
        partner=partner,
        keeper=keeper,
        setting=setting,
        tool_cfg=tool,
        obstacle_cfg=obstacle,
        treasure_cfg=treasure,
        flash_cfg=flash,
        restriction_heard=False,
        flashback_used=False,
        solo_failed=False,
        shared=False,
    )

    introduce(world, leader, partner, setting, treasure)
    discover_magic(world, leader, partner, tool)

    world.para()
    state_restriction(world, leader, tool)
    flashback(world, keeper, flash, tool)
    approach_obstacle(world, leader, partner, obstacle)

    world.para()
    clutch_and_fail(world, leader, partner, tool, obstacle)
    share_and_solve(world, leader, partner, tool, obstacle)

    world.para()
    reach_goal(world, leader, partner, setting, treasure)
    closing_image(world, leader, partner, tool)

    world.facts["success"] = world.get("obstacle").meters["solved"] >= THRESHOLD
    return world


SETTINGS = {
    "cliff_path": Setting(
        id="cliff_path",
        place="the windy cliff path above the sea",
        goal="the lookout nest",
        vista="Gulls wheeled overhead, and the water flashed far below like broken glass.",
        tags={"cliff", "adventure"},
    ),
    "forest_ruin": Setting(
        id="forest_ruin",
        place="the ferny forest trail behind the old mill",
        goal="the ivy tower",
        vista="Roots twisted over stones, and every turn looked like the start of a secret.",
        tags={"forest", "adventure"},
    ),
    "moon_hill": Setting(
        id="moon_hill",
        place="the long moonlit hill above the village",
        goal="the star platform",
        vista="The grass bent silver in the night breeze, and the path climbed like a ribbon.",
        tags={"hill", "adventure"},
    ),
}

TOOLS = {
    "pencil": Tool(
        id="pencil",
        label="pencil",
        phrase="a cedar pencil with a silver nib",
        makes="bridge",
        draw_verb="drew",
        tags={"pencil", "magic"},
    ),
    "chalk": Tool(
        id="chalk",
        label="chalk",
        phrase="a moon-white stick of chalk",
        makes="light",
        draw_verb="swished",
        tags={"chalk", "magic"},
    ),
    "brush": Tool(
        id="brush",
        label="brush",
        phrase="a tiny travel brush with green bristles",
        makes="vine_key",
        draw_verb="painted",
        tags={"brush", "magic"},
    ),
}

OBSTACLES = {
    "ravine": Obstacle(
        id="ravine",
        label="a ravine cut across the path",
        trouble="A stretch of the trail had fallen away, leaving a gap too wide for a jump.",
        need="a bridge",
        solved_by="bridge",
        danger="They could not cross the broken path safely.",
        tags={"ravine", "bridge"},
    ),
    "dark_gate": Obstacle(
        id="dark_gate",
        label="a dark gate tunnel",
        trouble="A stone gate waited ahead, but its inside was so black that the next step could not be seen.",
        need="light",
        solved_by="light",
        danger="Going in blind would be unsafe.",
        tags={"dark", "light"},
    ),
    "thorn_wall": Obstacle(
        id="thorn_wall",
        label="a thorn wall curled over the trail",
        trouble="Twisty thorns locked together like fingers and covered the way forward.",
        need="a living key-vine",
        solved_by="vine_key",
        danger="Pushing through would scratch their hands and faces.",
        tags={"thorns", "path"},
    ),
}

TREASURES = {
    "shell_box": Treasure(
        id="shell_box",
        label="shell box",
        phrase="a brass shell box full of sea-glass pieces",
        ending="inside, the sea-glass shone blue and green, so they split the pieces into two laughing piles.",
        tags={"treasure", "sharing"},
    ),
    "story_flags": Treasure(
        id="story_flags",
        label="story flags",
        phrase="a roll of old story flags painted with stars",
        ending="they took turns holding the fluttering flags high, letting the wind make the whole hill look festive.",
        tags={"treasure", "sharing"},
    ),
    "berry_tin": Treasure(
        id="berry_tin",
        label="berry tin",
        phrase="a round tin of sugared berries left in the hideout",
        ending="they counted the berries aloud and shared them one by one until the tin was empty.",
        tags={"treasure", "sharing"},
    ),
}

FLASHBACKS = {
    "grandpa_ilo": Flashback(
        id="grandpa_ilo",
        keeper_type="uncle",
        keeper_label="Uncle Ren",
        memory="Uncle Ren remembered being younger and standing beside Grandpa Ilo, the village illustrator, while pages fluttered on a clothesline in the sun.",
        lesson="These tools do not like grabbing. They wake for children who pass them along.",
        tags={"illustrator", "flashback"},
    ),
    "aunt_suri": Flashback(
        id="aunt_suri",
        keeper_type="aunt",
        keeper_label="Aunt Suri",
        memory="Aunt Suri remembered the attic studio, where an old illustrator once painted maps that seemed ready to rustle and move.",
        lesson="If one child clutches the magic, the drawing sleeps. If two children share, the path appears.",
        tags={"illustrator", "flashback"},
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Ava", "Lila", "Zora", "Pia"]
BOY_NAMES = ["Tao", "Ben", "Kai", "Noel", "Omar", "Rui"]


@dataclass
class StoryParams:
    setting: str
    tool: str
    obstacle: str
    treasure: str
    flashback: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(
        setting="cliff_path",
        tool="pencil",
        obstacle="ravine",
        treasure="shell_box",
        flashback="grandpa_ilo",
        leader_name="Mira",
        leader_gender="girl",
        partner_name="Tao",
        partner_gender="boy",
    ),
    StoryParams(
        setting="forest_ruin",
        tool="brush",
        obstacle="thorn_wall",
        treasure="berry_tin",
        flashback="aunt_suri",
        leader_name="Kai",
        leader_gender="boy",
        partner_name="Lila",
        partner_gender="girl",
    ),
    StoryParams(
        setting="moon_hill",
        tool="chalk",
        obstacle="dark_gate",
        treasure="story_flags",
        flashback="grandpa_ilo",
        leader_name="Nia",
        leader_gender="girl",
        partner_name="Rui",
        partner_gender="boy",
    ),
]


KNOWLEDGE = {
    "illustrator": [
        (
            "What does an illustrator do?",
            "An illustrator makes pictures for stories, maps, or books. The pictures help other people imagine what is happening."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a moment when a story remembers something that happened earlier. It helps explain why a character knows or feels something now."
        )
    ],
    "sharing": [
        (
            "Why can sharing help on an adventure?",
            "Sharing lets people use their ideas and tools together. That often makes a hard job easier and kinder."
        )
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "Magic is something wondrous that does not work like ordinary life. In a story, magic often follows special rules."
        )
    ],
    "restriction": [
        (
            "What is a restriction?",
            "A restriction is a rule or limit about what you may do. It helps tell people the safe or proper way to use something."
        )
    ],
    "bridge": [
        (
            "Why is a bridge useful?",
            "A bridge lets people cross over a gap, river, or ravine safely. It connects two sides that would be hard to reach otherwise."
        )
    ],
    "light": [
        (
            "Why do people need light in a dark place?",
            "Light helps you see where to step and what is ahead. Without light, a dark place can be confusing or unsafe."
        )
    ],
    "thorns": [
        (
            "Why can thorns be a problem on a path?",
            "Thorns are sharp and can scratch skin or snag clothes. A thick thorn wall can block the way forward."
        )
    ],
}
KNOWLEDGE_ORDER = ["illustrator", "flashback", "magic", "sharing", "restriction", "bridge", "light", "thorns"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    tool = f["tool_cfg"]
    obstacle = f["obstacle_cfg"]
    setting = f["setting"]
    return [
        f'Write a short adventure story for ages 3 to 5 that includes the words "groan", "illustrator", and "restriction".',
        f"Tell a magical adventure where {leader.id} and {partner.id} travel through {setting.place}, face {obstacle.label}, and learn that the old illustrator's tool only works when it is shared.",
        f"Write a child-facing story with a flashback, a magic drawing tool, and a clear rule about sharing before the children can continue their adventure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    tool = f["tool_cfg"]
    obstacle = f["obstacle_cfg"]
    treasure = f["treasure_cfg"]
    keeper = f["keeper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {partner.id}, two children on an adventure, and {keeper.id}, whose remembered lesson helps them. They are trying to reach {treasure.phrase}."
        ),
        (
            f"What was the restriction on the magic {tool.label}?",
            f"The restriction said the {tool.label} had to be passed hand to hand or the drawing would not wake. That rule mattered because the magic only worked when the children shared it."
        ),
        (
            "Why was there a flashback in the story?",
            f"The flashback helped {keeper.id}'s old memory come back at the right moment. It reminded the children that the illustrator's magic followed a sharing rule, so they knew how to solve the problem."
        ),
        (
            f"Why did {partner.id} make a groan?",
            f"{partner.id} made a groan when they reached {obstacle.label} and the way forward seemed blocked. The sound showed that the adventure might end unless they found another way."
        ),
    ]
    if f.get("solo_failed"):
        qa.append(
            (
                f"Why did the first drawing fail?",
                f"The first drawing failed because {leader.id} tried to use the {tool.label} alone. The magic stayed still because that broke the restriction instead of following it."
            )
        )
    if f.get("shared"):
        if obstacle.solved_by == "bridge":
            solve_text = "They drew a shining bridge together across the ravine."
        elif obstacle.solved_by == "light":
            solve_text = "They drew a bright lantern shape together and filled the tunnel with light."
        else:
            solve_text = "They sketched a key-vine together and the thorn wall opened."
        qa.append(
            (
                f"How did the children get past the obstacle?",
                f"{solve_text} The magic worked only after they shared the tool, so the solution came from cooperation instead of grabbing."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They reached {treasure.phrase} and shared what they found instead of fighting over it. The last image shows them carrying the magic tool together, proving they had changed."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"flashback", "magic", "sharing", "restriction"}
    tags |= set(f["flash_cfg"].tags)
    if f["obstacle_cfg"].solved_by == "bridge":
        tags.add("bridge")
    if f["obstacle_cfg"].solved_by == "light":
        tags.add("light")
    if f["obstacle_cfg"].id == "thorn_wall":
        tags.add("thorns")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
solves(Tool, Ob) :- tool_makes(Tool, Need), obstacle_needs(Ob, Need).
valid(S, T, O, Tr) :- setting(S), tool(T), obstacle(O), treasure(Tr), solves(T, O).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_makes", tid, tool.makes))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_needs", oid, obstacle.solved_by))
    for trid in TREASURES:
        lines.append(asp.fact("treasure", trid))
    return "\n".join(lines)


def asp_program(show_override: str = "") -> str:
    if show_override:
        return f"{asp_facts()}\n{ASP_RULES.replace('#show valid/4.', show_override)}\n"
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Magic-sharing adventure storyworld. Unspecified choices are selected at random from valid combinations."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kids(rng: random.Random) -> tuple[str, str, str, str]:
    leader_gender = rng.choice(["girl", "boy"])
    if leader_gender == "girl":
        leader_name = rng.choice(GIRL_NAMES)
        partner_gender = "boy"
        partner_name = rng.choice([n for n in BOY_NAMES if n != leader_name])
    else:
        leader_name = rng.choice(BOY_NAMES)
        partner_gender = "girl"
        partner_name = rng.choice([n for n in GIRL_NAMES if n != leader_name])
    return leader_name, leader_gender, partner_name, partner_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.obstacle:
        if not tool_solves(TOOLS[args.tool], OBSTACLES[args.obstacle]):
            raise StoryError(explain_rejection(TOOLS[args.tool], OBSTACLES[args.obstacle]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.tool is None or c[1] == args.tool)
        and (args.obstacle is None or c[2] == args.obstacle)
        and (args.treasure is None or c[3] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, tool_id, obstacle_id, treasure_id = rng.choice(sorted(combos))
    flashback_id = args.flashback or rng.choice(sorted(FLASHBACKS))
    leader_name, leader_gender, partner_name, partner_gender = _pick_kids(rng)
    return StoryParams(
        setting=setting_id,
        tool=tool_id,
        obstacle=obstacle_id,
        treasure=treasure_id,
        flashback=flashback_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        tool = TOOLS[params.tool]
        obstacle = OBSTACLES[params.obstacle]
        treasure = TREASURES[params.treasure]
        flash = FLASHBACKS[params.flashback]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc.args[0]})") from None

    if not tool_solves(tool, obstacle):
        raise StoryError(explain_rejection(tool, obstacle))

    world = tell(
        setting=setting,
        tool=tool,
        obstacle=obstacle,
        treasure=treasure,
        flash=flash,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    smoke_cases = list(CURATED)
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        if "restriction" not in sample.story or "groan" not in sample.story or "illustrator" not in sample.story:
            raise StoryError("required seed words missing from smoke story")
        print("OK: smoke generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    for seed in range(10):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as exc:
            rc = 1
            print(f"resolve_params failed during verify for seed {seed}: {exc}")
            break

    crash_count = 0
    for params in smoke_cases:
        try:
            _ = generate(params)
        except Exception as exc:  # pragma: no cover
            crash_count += 1
            print(f"Generation crash for {params}: {exc}")
    if crash_count == 0:
        print(f"OK: generated {len(smoke_cases)} verification stories without crashing.")
    else:
        rc = 1
        print(f"MISMATCH: {crash_count} verification generations crashed.")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, tool, obstacle, treasure) combos:\n")
        for setting_id, tool_id, obstacle_id, treasure_id in combos:
            print(f"  {setting_id:12} {tool_id:7} {obstacle_id:10} {treasure_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader_name} & {p.partner_name}: {p.tool} at {p.setting} ({p.obstacle} -> {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
