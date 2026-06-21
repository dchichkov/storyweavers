#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/papaya_hideous_distraught_friendship_bravery_pirate_tale.py
=======================================================================================

A standalone storyworld for a tiny pirate-play tale about friendship, bravery,
and a lost papaya.

Premise
-------
Two children turn a shore-side place into a pirate world. Their papaya, meant to
be the treasure for a pirate feast, gets trapped in a dangerous spot. One child
grows distraught. The other does not act reckless; instead, that child shows
bravery by pausing, judging the danger, and using the right tool while their
friend helps. The ending proves that friendship made the brave plan possible.

Run it
------
    python storyworlds/worlds/gpt-5.4/papaya_hideous_distraught_friendship_bravery_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/papaya_hideous_distraught_friendship_bravery_pirate_tale.py --obstacle seaweed_rocks
    python storyworlds/worlds/gpt-5.4/papaya_hideous_distraught_friendship_bravery_pirate_tale.py --tool fruit_net --obstacle thorn_crate
    python storyworlds/worlds/gpt-5.4/papaya_hideous_distraught_friendship_bravery_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/papaya_hideous_distraught_friendship_bravery_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/papaya_hideous_distraught_friendship_bravery_pirate_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    feast: str
    launch: str
    ending: str
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
class Obstacle:
    id: str
    label: str
    area: str
    hideous: str
    hazard: str
    risk: int
    warning: str
    rescue_need: str
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
    guards: set[str] = field(default_factory=set)
    reach: int = 0
    move: str = ""
    share_line: str = ""
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
class StoryParams:
    theme: str
    obstacle: str
    tool: str
    captain_name: str
    captain_gender: str
    friend_name: str
    friend_gender: str
    captain_trait: str
    friend_trait: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_distraught(world: World) -> list[str]:
    papaya = world.get("papaya")
    friend = world.get("friend")
    if papaya.meters["stuck"] < THRESHOLD or papaya.meters["rescued"] >= THRESHOLD:
        return []
    sig = ("distraught",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["distraught"] += 1
    friend.memes["need_help"] += 1
    return ["__distraught__"]


def _r_friendship_bravery(world: World) -> list[str]:
    captain = world.get("captain")
    friend = world.get("friend")
    if friend.memes["distraught"] < THRESHOLD or captain.memes["care"] < THRESHOLD:
        return []
    sig = ("friendship_bravery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["bravery"] += 1
    captain.memes["friendship"] += 1
    friend.memes["trust"] += 1
    return ["__friendship__"]


def _r_relief(world: World) -> list[str]:
    papaya = world.get("papaya")
    if papaya.meters["rescued"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("captain").memes["relief"] += 1
    world.get("friend").memes["relief"] += 1
    world.get("captain").memes["joy"] += 1
    world.get("friend").memes["joy"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="distraught", tag="emotion", apply=_r_distraught),
    Rule(name="friendship_bravery", tag="emotion", apply=_r_friendship_bravery),
    Rule(name="relief", tag="emotion", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


THEMES = {
    "cove": Theme(
        id="cove",
        scene="a bright pirate cove",
        rig="A striped towel became their sail, a driftwood plank became their deck, and a basket by the sand held the feast.",
        feast="their pirate feast",
        launch="sailed their pretend ship along the warm edge of the shore",
        ending="ate sweet orange slices of papaya while the waves made soft pirate sounds",
        tags={"shore", "pirates"},
    ),
    "harbor": Theme(
        id="harbor",
        scene="a little harbor fort",
        rig="An old crate became their captain's table, a skipping rope became an anchor line, and a red pail became their treasure chest.",
        feast="their harbor feast",
        launch="marched up and down the dock like two tiny captains",
        ending="shared the rescued papaya on the crate while gulls cried overhead",
        tags={"dock", "pirates"},
    ),
    "island": Theme(
        id="island",
        scene="a secret island camp",
        rig="A blanket over two chairs became a cabin, a stick became a mast, and a tin cup waited for the first toast of treasure.",
        feast="their island feast",
        launch="set out to map every corner of their little island camp",
        ending="sat close together with sticky papaya smiles and watched the evening light turn gold",
        tags={"camp", "pirates"},
    ),
}

OBSTACLES = {
    "seaweed_rocks": Obstacle(
        id="seaweed_rocks",
        label="seaweed rocks",
        area="between two rocks at the edge of a tide pool",
        hideous="a hideous rope of green seaweed",
        hazard="water",
        risk=3,
        warning="the stones were slick, and the tide kept nipping at their shoes",
        rescue_need="something long enough to reach over the water without stepping onto the rocks",
        tags={"water", "tide_pool"},
    ),
    "thorn_crate": Obstacle(
        id="thorn_crate",
        label="thorn crate",
        area="under a broken crate wrapped in vine",
        hideous="a hideous snarl of sharp thorns",
        hazard="thorns",
        risk=2,
        warning="the thorns hooked anything that came too close",
        rescue_need="something that could pinch or lift the fruit without little fingers touching the thorns",
        tags={"thorns"},
    ),
    "mud_bank": Obstacle(
        id="mud_bank",
        label="mud bank",
        area="down the side of a little creek bank",
        hideous="a hideous patch of sucking mud",
        hazard="mud",
        risk=2,
        warning="the bank was soft, and one wrong step would send a child sliding",
        rescue_need="something that could reach down from firm ground",
        tags={"mud"},
    ),
}

TOOLS = {
    "boat_hook": Tool(
        id="boat_hook",
        label="boat hook",
        phrase="a smooth boat hook",
        guards={"water", "mud"},
        reach=3,
        move="slid the hook under the papaya and rolled it back across the safe ground",
        share_line="The hook let them stay back from the danger while they worked together.",
        tags={"boat_hook"},
    ),
    "fruit_net": Tool(
        id="fruit_net",
        label="fruit net",
        phrase="a little fruit net on a long pole",
        guards={"water"},
        reach=3,
        move="dipped the net low and lifted the papaya up before the tide could tug it away",
        share_line="The net turned a hard reach into one careful scoop.",
        tags={"net"},
    ),
    "long_tongs": Tool(
        id="long_tongs",
        label="long tongs",
        phrase="a pair of long kitchen tongs",
        guards={"thorns"},
        reach=2,
        move="pinched the stem gently and drew the papaya free without brushing the thorns",
        share_line="The tongs did the reaching so no small hand had to go into the prickles.",
        tags={"tongs"},
    ),
    "rope_loop": Tool(
        id="rope_loop",
        label="rope loop",
        phrase="a loop of rope tied to a stick",
        guards={"mud"},
        reach=2,
        move="dropped the loop around the papaya and pulled it up the bank inch by inch",
        share_line="The rope gave the papaya a path up without asking either child to step into the mud.",
        tags={"rope"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["steady", "careful", "bright", "bold", "kind", "quick-thinking"]


def tool_fits(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.hazard in tool.guards and tool.reach >= obstacle.risk


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for tool_id, tool in TOOLS.items():
                if tool_fits(obstacle, tool):
                    combos.append((theme_id, obstacle_id, tool_id))
    return combos


def explain_rejection(obstacle: Obstacle, tool: Tool) -> str:
    if obstacle.hazard not in tool.guards:
        return (
            f"(No story: {tool.label} does not solve the danger at {obstacle.label}. "
            f"The obstacle needs {obstacle.rescue_need}.)"
        )
    return (
        f"(No story: {tool.label} is not long enough for {obstacle.label}. "
        f"The obstacle needs {obstacle.rescue_need}.)"
    )


def predict_bare_hands(world: World) -> dict:
    sim = world.copy()
    obstacle = sim.facts["obstacle_cfg"]
    sim.get("captain").meters["too_close"] += 1
    if obstacle.hazard == "water":
        return {
            "safe": False,
            "reason": "the rocks would be too slippery for bare feet and quick hands",
        }
    if obstacle.hazard == "thorns":
        return {
            "safe": False,
            "reason": "the thorns would scratch skin before the papaya came loose",
        }
    return {
        "safe": False,
        "reason": "the mud would pull at ankles and make the bank slide away",
    }


def play_setup(world: World, captain: Entity, friend: Entity, theme: Theme) -> None:
    captain.memes["joy"] += 1
    friend.memes["joy"] += 1
    captain.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {friend.id} turned the shore into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f"They {theme.launch}. In the middle of it all sat a ripe papaya, round and golden, meant for {theme.feast}."
    )


def trouble(world: World, captain: Entity, friend: Entity, obstacle: Obstacle) -> None:
    papaya = world.get("papaya")
    papaya.meters["stuck"] += 1
    papaya.attrs["place"] = obstacle.area
    papaya.attrs["hazard"] = obstacle.hazard
    world.facts["stuck_place"] = obstacle.area
    propagate(world, narrate=False)
    world.say(
        f"Then the game turned. One bump of the basket sent the papaya rolling away until it stopped {obstacle.area}, half-caught beside {obstacle.hideous}."
    )
    if friend.memes["distraught"] >= THRESHOLD:
        world.say(
            f'{friend.id} stared at it and looked truly distraught. "Our feast!" {friend.pronoun().capitalize()} cried. "The papaya is trapped!"'
        )


def warn(world: World, captain: Entity, friend: Entity, obstacle: Obstacle) -> None:
    pred = predict_bare_hands(world)
    world.facts["bare_hands_reason"] = pred["reason"]
    world.say(
        f"{captain.id} took one step forward, then stopped and studied the place. {obstacle.warning}."
    )
    world.say(
        f'"If we grab it with bare hands, {pred["reason"]}," {captain.id} said. '
        f'"Brave pirates do not rush where their friends can get hurt."'
    )


def make_plan(world: World, captain: Entity, friend: Entity, tool: Tool) -> None:
    captain.memes["plan"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{friend.id} swallowed hard, but nodded. "{captain.id}, what do we do?"'
    )
    world.say(
        f'{captain.id} pointed to {tool.phrase}. "We use that. You hold the basket steady, and I will reach from the safe side."'
    )


def rescue(world: World, captain: Entity, friend: Entity, tool: Tool) -> None:
    papaya = world.get("papaya")
    papaya.meters["stuck"] = 0.0
    papaya.meters["rescued"] += 1
    world.facts["rescuer"] = captain.id
    world.facts["helper"] = friend.id
    propagate(world, narrate=False)
    world.say(
        f"Very slowly, with {friend.id} holding firm and {captain.id} leaning only as far as was safe, {captain.pronoun()} {tool.move}."
    )
    world.say(
        f"The papaya bumped back into the basket at last. {tool.share_line}"
    )


def ending(world: World, captain: Entity, friend: Entity, theme: Theme) -> None:
    captain.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    captain.memes["bravery"] += 1
    world.say(
        f"For a moment the two friends simply laughed with relief. Then {friend.id} broke the papaya open, and together they {theme.ending}."
    )
    world.say(
        f'"That was brave," {friend.id} said.'
    )
    world.say(
        f'"It was friendship too," {captain.id} answered. "The best pirates are the ones who keep each other safe."'
    )


def tell(
    theme: Theme,
    obstacle: Obstacle,
    tool: Tool,
    captain_name: str = "Tom",
    captain_gender: str = "boy",
    friend_name: str = "Lily",
    friend_gender: str = "girl",
    captain_trait: str = "steady",
    friend_trait: str = "kind",
) -> World:
    if not tool_fits(obstacle, tool):
        raise StoryError(explain_rejection(obstacle, tool))

    world = World()
    world.facts["theme_cfg"] = theme
    world.facts["obstacle_cfg"] = obstacle
    world.facts["tool_cfg"] = tool

    captain = world.add(
        Entity(
            id=captain_name,
            kind="character",
            type=captain_gender,
            role="captain",
            traits=[captain_trait],
            attrs={"trait": captain_trait},
            tags={"friendship", "bravery"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=[friend_trait],
            attrs={"trait": friend_trait},
            tags={"friendship"},
        )
    )
    papaya = world.add(
        Entity(
            id="papaya",
            kind="thing",
            type="fruit",
            label="papaya",
            attrs={"owner": friend_name},
            tags={"papaya"},
        )
    )
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            attrs={"reach": tool.reach, "guards": set(tool.guards)},
            tags=set(tool.tags),
        )
    )
    world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            attrs={"hazard": obstacle.hazard, "risk": obstacle.risk},
            tags=set(obstacle.tags),
        )
    )

    captain.memes["care"] = 1.0
    captain.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    friend.memes["trust"] = 1.0
    papaya.meters["stuck"] = 0.0
    papaya.meters["rescued"] = 0.0

    play_setup(world, captain, friend, theme)
    world.para()
    trouble(world, captain, friend, obstacle)
    warn(world, captain, friend, obstacle)
    world.para()
    make_plan(world, captain, friend, tool)
    rescue(world, captain, friend, tool)
    world.para()
    ending(world, captain, friend, theme)

    world.facts.update(
        captain=captain,
        friend=friend,
        papaya=papaya,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        theme_cfg=theme,
        brave_plan=True,
        rescued=papaya.meters["rescued"] >= THRESHOLD,
        distraught=friend.memes["distraught"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "papaya": [
        (
            "What is a papaya?",
            "A papaya is a soft tropical fruit with orange flesh and black seeds in the middle. When it is ripe, it tastes sweet and juicy."
        )
    ],
    "friendship": [
        (
            "What does friendship mean?",
            "Friendship means caring about another person and helping them when they are sad or worried. A good friend wants everyone to be safe, not just to win the game."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel worried. It does not mean rushing into danger without thinking."
        )
    ],
    "tide_pool": [
        (
            "Why can tide-pool rocks be slippery?",
            "Tide-pool rocks can be slippery because water and seaweed make them smooth and slick. Feet can slide on them very easily."
        )
    ],
    "thorns": [
        (
            "Why are thorns dangerous to touch?",
            "Thorns are sharp plant spikes that can poke and scratch skin. That is why people use care and the right tools around them."
        )
    ],
    "mud": [
        (
            "Why is a muddy bank hard to climb on?",
            "Mud makes the ground soft and slippery. A foot can sink or slide when the dirt is too wet."
        )
    ],
    "boat_hook": [
        (
            "What is a boat hook for?",
            "A boat hook is a long pole with a hook at the end. People use it to pull things closer without stepping into the water."
        )
    ],
    "net": [
        (
            "What is a net good for?",
            "A net can scoop up something gently from the water. It helps you lift an object without grabbing at it with your hands."
        )
    ],
    "tongs": [
        (
            "What are tongs used for?",
            "Tongs help you pinch and hold something from a short distance away. They are useful when fingers should stay out of a prickly place."
        )
    ],
    "rope": [
        (
            "Why can a rope help pull something up?",
            "A rope can catch around an object and give it a path to move. That lets someone pull from firm ground instead of stepping into danger."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "papaya",
    "friendship",
    "bravery",
    "tide_pool",
    "thorns",
    "mud",
    "boat_hook",
    "net",
    "tongs",
    "rope",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    theme = f["theme_cfg"]
    return [
        (
            f'Write a pirate-play story for a 3-to-5-year-old where two friends lose a papaya in {obstacle.area}, '
            f'one child becomes distraught, and the other shows real bravery by using {tool.label} instead of rushing in.'
        ),
        (
            f"Tell a gentle pirate tale about {captain.id} and {friend.id}, two friends in {theme.scene}, "
            f"who face a hideous problem and solve it together."
        ),
        (
            'Write a child-facing story that includes the words "papaya," "hideous," and "distraught," '
            "and ends by showing that friendship can make a brave plan safer."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    theme = f["theme_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {captain.id} and {friend.id}, who were pretending to be pirates in {theme.scene}. Their game mattered because the papaya was supposed to be part of their pirate feast."
        ),
        (
            f"Why did {friend.id} become distraught?",
            f"{friend.id} became distraught when the papaya rolled away and got trapped {obstacle.area}. The papaya felt important because it was the treasure for their feast, so losing it made the game suddenly feel sad."
        ),
        (
            f"Why did {captain.id} say they should not grab the papaya with bare hands?",
            f"{captain.id} saw that {obstacle.warning}. {f['bare_hands_reason'].capitalize()}, so rushing in would have been reckless instead of brave."
        ),
        (
            f"How did {captain.id} show bravery?",
            f"{captain.id} showed bravery by stopping to think and choosing {tool.label} instead of lunging at the danger. That kind of bravery protected both friends while still solving the problem."
        ),
        (
            "How did friendship help save the papaya?",
            f"They worked together: {friend.id} held steady while {captain.id} used {tool.label}. The rescue worked because each friend trusted the other and did one careful part of the plan."
        ),
        (
            "How did the story end?",
            f"The papaya was rescued, and the friends shared it together at the end. Their last pirate lesson was that keeping a friend safe is part of being brave."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"papaya", "friendship", "bravery"}
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    tags |= set(obstacle.tags)
    tags |= set(tool.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="cove",
        obstacle="seaweed_rocks",
        tool="boat_hook",
        captain_name="Tom",
        captain_gender="boy",
        friend_name="Lily",
        friend_gender="girl",
        captain_trait="steady",
        friend_trait="kind",
    ),
    StoryParams(
        theme="harbor",
        obstacle="seaweed_rocks",
        tool="fruit_net",
        captain_name="Mia",
        captain_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        captain_trait="quick-thinking",
        friend_trait="bright",
    ),
    StoryParams(
        theme="island",
        obstacle="thorn_crate",
        tool="long_tongs",
        captain_name="Nora",
        captain_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        captain_trait="careful",
        friend_trait="bold",
    ),
    StoryParams(
        theme="cove",
        obstacle="mud_bank",
        tool="rope_loop",
        captain_name="Eli",
        captain_gender="boy",
        friend_name="Rose",
        friend_gender="girl",
        captain_trait="bold",
        friend_trait="steady",
    ),
    StoryParams(
        theme="harbor",
        obstacle="mud_bank",
        tool="boat_hook",
        captain_name="Ava",
        captain_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        captain_trait="kind",
        friend_trait="quick-thinking",
    ),
]


ASP_RULES = r"""
valid(T, O, U) :- theme(T), obstacle(O), tool(U),
                  hazard(O, H), guards(U, H),
                  risk(O, Need), reach(U, Have), Have >= Need.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("hazard", obstacle_id, obstacle.hazard))
        lines.append(asp.fact("risk", obstacle_id, obstacle.risk))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        for guard in sorted(tool.guards):
            lines.append(asp.fact("guards", tool_id, guard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = [CURATED[0]]
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(7)))
    except StoryError as err:
        rc = 1
        print(f"SMOKE PARAM FAILURE: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "papaya" not in sample.story.lower():
                raise StoryError("story omitted papaya")
            if "hideous" not in sample.story.lower():
                raise StoryError("story omitted hideous")
            if "distraught" not in sample.story.lower():
                raise StoryError("story omitted distraught")
            emit(sample, trace=False, qa=False, header=f"### smoke {i}")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on case {i}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate friends, a trapped papaya, and a brave safe rescue."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not tool_fits(obstacle, tool):
            raise StoryError(explain_rejection(obstacle, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    captain_name, captain_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=captain_name)
    captain_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        theme=theme_id,
        obstacle=obstacle_id,
        tool=tool_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        captain_trait=captain_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    theme = THEMES[params.theme]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if not tool_fits(obstacle, tool):
        raise StoryError(explain_rejection(obstacle, tool))

    world = tell(
        theme=theme,
        obstacle=obstacle,
        tool=tool,
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        captain_trait=params.captain_trait,
        friend_trait=params.friend_trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, obstacle, tool) combos:\n")
        for theme_id, obstacle_id, tool_id in combos:
            print(f"  {theme_id:8} {obstacle_id:14} {tool_id}")
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
            header = f"### {p.captain_name} & {p.friend_name}: {p.obstacle} with {p.tool} ({p.theme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
