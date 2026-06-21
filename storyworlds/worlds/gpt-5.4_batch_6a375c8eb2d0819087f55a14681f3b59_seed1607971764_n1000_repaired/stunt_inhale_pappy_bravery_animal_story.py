#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stunt_inhale_pappy_bravery_animal_story.py
=====================================================================

A standalone story world for a gentle Animal Story about a young woodland animal,
a flashy stunt, a calming inhale, and a pappy who teaches what bravery really is.

Reference seed:
---------------
Write a story that includes the following words and narrative instruments.
Words: stunt, inhale, pappy
Features: Bravery
Style: Animal Story

This world rebuilds that seed as a small simulation:

- a little animal and a friend lose something across a hazard,
- the young hero wants to try a showy stunt,
- Pappy explains that bravery is not showing off,
- the hero either listens right away or learns after a small oops,
- the ending image proves the hero has changed.

The reasonableness constraint here is concrete:
a chosen tool must actually solve the specific hazard, and the lost item must make
sense in that place. A hooked branch can pull from thorns, a plank can span a brook,
and a guide rope can steady a windy ledge. Unreasonable combinations are refused.

Run it
------
python storyworlds/worlds/gpt-5.4/stunt_inhale_pappy_bravery_animal_story.py
python storyworlds/worlds/gpt-5.4/stunt_inhale_pappy_bravery_animal_story.py --obstacle brook --prize toy_boat --tool plank
python storyworlds/worlds/gpt-5.4/stunt_inhale_pappy_bravery_animal_story.py --obstacle thornbush --tool plank
python storyworlds/worlds/gpt-5.4/stunt_inhale_pappy_bravery_animal_story.py --all
python storyworlds/worlds/gpt-5.4/stunt_inhale_pappy_bravery_animal_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/stunt_inhale_pappy_bravery_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"rabbit_girl", "squirrel_girl", "fox_girl", "mother"}
        male = {"rabbit_boy", "squirrel_boy", "fox_boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"father": "pappy", "mother": "mama"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
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
class Species:
    id: str
    child_type: str
    parent_type: str
    home: str
    foot: str
    move: str
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
    place: str
    hazard: str
    stunt_line: str
    trouble_line: str
    safe_arrive: str
    hazard_word: str
    requires: set[str] = field(default_factory=set)
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
class Prize:
    id: str
    label: str
    phrase: str
    found_line: str
    places: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_trouble(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    pappy = world.get("pappy")
    if hero.meters["off_balance"] < THRESHOLD:
        return []
    sig = ("trouble", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.meters["stuck"] += 1
    pappy.memes["alarm"] += 1
    obstacle.meters["danger"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="trouble", tag="physical", apply=_r_trouble),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_fits(obstacle: Obstacle, prize: Prize) -> bool:
    return obstacle.id in prize.places


def tool_solves(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.id in tool.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for species_id in SPECIES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for prize_id, prize in PRIZES.items():
                if not prize_fits(obstacle, prize):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_solves(obstacle, tool):
                        combos.append((species_id, obstacle_id, prize_id, tool_id))
    return combos


def explain_rejection(obstacle: Obstacle, prize: Prize, tool: Tool) -> str:
    if not prize_fits(obstacle, prize):
        return (
            f"(No story: {prize.phrase} does not belong at {obstacle.place}. "
            f"Pick an item that could reasonably be lost there.)"
        )
    if not tool_solves(obstacle, tool):
        return (
            f"(No story: {tool.phrase} does not solve trouble at {obstacle.place}. "
            f"Choose a tool that really works for {obstacle.label}.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


def outcome_of(params: "StoryParams") -> str:
    return "heeded" if params.courage == "steady" else "rescued"


# ---------------------------------------------------------------------------
# Screenplay helpers
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity, species: Species) -> None:
    hero.memes["hope"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"In {species.home}, {hero.id} was a little {species.id} who loved bright mornings "
        f"and brave ideas. {friend.id}, {hero.pronoun('possessive')} friend, liked to follow "
        f"close behind and see what adventure would come next."
    )


def discover(world: World, hero: Entity, friend: Entity, obstacle: Obstacle, prize: Prize) -> None:
    world.say(
        f"That day they wandered to {obstacle.place}, where {obstacle.label} made the path feel "
        f"wild and interesting. {prize.found_line}"
    )
    world.say(
        f'"Oh!" cried {friend.id}. "Our {prize.label} is over there."'
    )
    hero.memes["eager"] += 1


def tempt(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["showoff"] += 1
    world.say(
        f'{hero.id} stood tall on {hero.pronoun("possessive")} {world.facts["species"].foot} and said, '
        f'"I know a stunt that will get it back."'
    )
    world.say(obstacle.stunt_line)


def pappy_warns(world: World, hero: Entity, pappy: Entity, obstacle: Obstacle) -> None:
    hero.memes["heard_warning"] += 1
    world.say(
        f"Just then {pappy.label_word.capitalize()} came along the path with kind eyes and quick steps. "
        f'"Bravery is not the same as showing off," {pappy.label_word} said. '
        f'"First inhale one slow breath and look at the real trouble."'
    )
    world.say(
        f"{hero.id} did one long inhale, and the noisy idea in {hero.pronoun('possessive')} head grew quieter."
    )


def listen(world: World, hero: Entity, pappy: Entity, tool: Tool) -> None:
    hero.memes["calm"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} looked at {pappy.label_word} and nodded. It felt smaller to listen than to leap, "
        f"but inside, that choice was the braver one."
    )
    world.say(
        f'{pappy.label_word.capitalize()} fetched {tool.phrase}. "{tool.action}," {pappy.label_word} said.'
    )


def attempt_stunt(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.meters["off_balance"] += 1
    hero.memes["bravery"] += 0.5
    propagate(world, narrate=False)
    world.say(
        f"But the wish to look grand tugged harder than the warning. {hero.id} dashed ahead, trying the stunt anyway."
    )
    world.say(obstacle.trouble_line)


def call_for_help(world: World, hero: Entity, pappy: Entity) -> None:
    world.say(
        f'{hero.id} swallowed hard. "{pappy.label_word.capitalize()}!" {hero.pronoun()} called. '
        f'This time the voice was not boastful. It was honest and small.'
    )


def rescue(world: World, hero: Entity, pappy: Entity, tool: Tool, obstacle: Obstacle) -> None:
    hero.meters["stuck"] = 0.0
    hero.meters["off_balance"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    pappy.memes["care"] += 1
    world.say(
        f'{pappy.label_word.capitalize()} stayed calm, brought {tool.phrase}, and said, '
        f'"{tool.action}."'
    )
    world.say(
        f"With {pappy.label_word}'s help, {hero.id} came back from the edge of the trouble and stood safely again at {obstacle.safe_arrive}."
    )


def recover_prize(world: World, hero: Entity, friend: Entity, pappy: Entity, tool: Tool, prize: Prize) -> None:
    hero.meters["holding_prize"] += 1
    hero.memes["bravery"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Then {hero.id} took another slow inhale, used {tool.phrase} with careful paws, and brought back {prize.phrase}."
    )
    world.say(
        f'{friend.id} clapped. "{hero.id}, you did it!"'
    )
    world.say(
        f'"Yes," said {pappy.label_word}, smiling. "And you did it bravely, because you were steady."'
    )


def ending(world: World, hero: Entity, friend: Entity, pappy: Entity, obstacle: Obstacle, prize: Prize) -> None:
    hero.memes["lesson"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"After that, {hero.id} no longer called every risky idea brave. {hero.pronoun().capitalize()} called brave the thing that kept everyone safe."
    )
    world.say(
        f"When a gust rustled {obstacle.place} again, {friend.id} grew nervous, but {hero.id} gently said, "
        f'"Let us inhale first and think."'
    )
    world.say(
        f"So the little friends went home with {prize.phrase}, close beside {pappy.label_word}, and the path behind them looked wiser than before."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(
    species: Species,
    obstacle: Obstacle,
    prize: Prize,
    tool: Tool,
    hero_name: str,
    friend_name: str,
    gender: str,
    courage: str,
) -> World:
    world = World()
    hero_type = f"{species.id}_{gender}"
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_type,
            label=hero_name,
            role="hero",
            attrs={"display_name": hero_name, "courage": courage},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type=hero_type,
            label=friend_name,
            role="friend",
            attrs={"display_name": friend_name},
        )
    )
    pappy = world.add(
        Entity(
            id="pappy",
            kind="character",
            type=species.parent_type,
            label="the parent",
            role="parent",
            attrs={"display_name": "Pappy"},
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle.label,
            attrs={"hazard": obstacle.hazard},
        )
    )
    prize_ent = world.add(
        Entity(
            id="prize",
            type="prize",
            label=prize.label,
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
        )
    )

    world.facts["species"] = species
    world.facts["obstacle_cfg"] = obstacle
    world.facts["prize_cfg"] = prize
    world.facts["tool_cfg"] = tool
    world.facts["hero_name"] = hero_name
    world.facts["friend_name"] = friend_name
    world.facts["courage"] = courage

    introduce(world, hero, friend, species)
    discover(world, hero, friend, obstacle, prize)

    world.para()
    tempt(world, hero, obstacle)
    pappy_warns(world, hero, pappy, obstacle)

    world.para()
    if courage == "steady":
        listen(world, hero, pappy, tool)
        recover_prize(world, hero, friend, pappy, tool, prize)
        outcome = "heeded"
    else:
        attempt_stunt(world, hero, obstacle)
        call_for_help(world, hero, pappy)
        rescue(world, hero, pappy, tool, obstacle)
        recover_prize(world, hero, friend, pappy, tool, prize)
        outcome = "rescued"

    world.para()
    ending(world, hero, friend, pappy, obstacle, prize)

    world.facts.update(
        hero=hero,
        friend=friend,
        pappy=pappy,
        obstacle=obstacle_ent,
        prize=prize_ent,
        tool=tool_ent,
        outcome=outcome,
        trouble_happened=outcome == "rescued",
        steady_choice=outcome == "heeded",
        prize_recovered=hero.meters["holding_prize"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SPECIES = {
    "rabbit": Species(
        id="rabbit",
        child_type="rabbit_boy",
        parent_type="father",
        home="a sunny meadow at the edge of the woods",
        foot="hind feet",
        move="hop",
        tags={"rabbit", "animal"},
    ),
    "squirrel": Species(
        id="squirrel",
        child_type="squirrel_boy",
        parent_type="father",
        home="an oak grove full of leaves and chatter",
        foot="small paws",
        move="scamper",
        tags={"squirrel", "animal"},
    ),
    "fox": Species(
        id="fox",
        child_type="fox_boy",
        parent_type="father",
        home="a ferny hollow near the hill",
        foot="soft paws",
        move="trot",
        tags={"fox", "animal"},
    ),
}

OBSTACLES = {
    "brook": Obstacle(
        id="brook",
        label="a narrow brook",
        place="the brook",
        hazard="slippery water",
        stunt_line="A mossy stump leaned near the water, and beyond it a slick stone blinked in the sun. It looked exactly like the sort of place where a child might dream up a stunt.",
        trouble_line="The stump was springy, the stone was slick, and in one blink splash went the little hero into the chilly shallows, with water up to the ankles and surprise in the chest.",
        safe_arrive="the dry bank",
        hazard_word="slippery",
        requires={"plank"},
        tags={"brook", "water"},
    ),
    "thornbush": Obstacle(
        id="thornbush",
        label="a thornbush",
        place="the thornbush",
        hazard="sharp thorns",
        stunt_line="A flat rock sat beside the brambles, and from there the jump looked fast and fancy. It was the kind of stunt that shone from far away and hurt up close.",
        trouble_line="The jump was not clean at all. A sleeve of fur snagged, a tail froze, and the little hero had to stand very still among the prickles.",
        safe_arrive="the soft grass",
        hazard_word="sharp",
        requires={"hook"},
        tags={"thorns", "bush"},
    ),
    "windy_ledge": Obstacle(
        id="windy_ledge",
        label="a windy ledge",
        place="the windy ledge",
        hazard="gusty drop",
        stunt_line="A fallen log pointed toward the ledge, and it looked like a brave runway. But the wind kept tugging at leaves and ears, making every step less certain than it seemed.",
        trouble_line="Halfway along, a gust pushed sideways. The little hero froze, wobbling with the wide air below and nowhere safe to dash next.",
        safe_arrive="the broad hillside path",
        hazard_word="windy",
        requires={"rope"},
        tags={"ledge", "wind"},
    ),
}

PRIZES = {
    "toy_boat": Prize(
        id="toy_boat",
        label="toy boat",
        phrase="the little toy boat",
        found_line="There, caught by reeds near the other side, bobbed the little toy boat they had been sailing earlier.",
        places={"brook"},
        tags={"boat", "water"},
    ),
    "red_scarf": Prize(
        id="red_scarf",
        label="red scarf",
        phrase="the red scarf",
        found_line="There, bright as a berry, the red scarf had been snagged where little paws could not easily reach.",
        places={"thornbush", "windy_ledge"},
        tags={"scarf", "clothing"},
    ),
    "berry_basket": Prize(
        id="berry_basket",
        label="berry basket",
        phrase="the berry basket",
        found_line="There sat the berry basket, tipped just far enough away to be troublesome and precious at the same time.",
        places={"brook", "windy_ledge"},
        tags={"berries", "basket"},
    ),
}

TOOLS = {
    "plank": Tool(
        id="plank",
        label="plank",
        phrase="a smooth little plank",
        action="Set it down flat, cross slowly, and keep your eyes on where your feet belong",
        solves={"brook"},
        tags={"bridge", "plank"},
    ),
    "hook": Tool(
        id="hook",
        label="hooked branch",
        phrase="a long hooked branch",
        action="Stay back from the prickles and pull gently from here",
        solves={"thornbush"},
        tags={"branch", "thorns"},
    ),
    "rope": Tool(
        id="rope",
        label="guide rope",
        phrase="a looped guide rope",
        action="Hold tight, lean low, and let the rope be steadier than the wind",
        solves={"windy_ledge"},
        tags={"rope", "wind"},
    ),
}

NAMES = {
    "rabbit": ["Milo", "Pip", "Nibbles", "Toby"],
    "squirrel": ["Hazel", "Pip", "Nutkin", "Rory"],
    "fox": ["Rusty", "Pip", "Ember", "Finn"],
}
FRIEND_NAMES = ["Moss", "Bramble", "Tansy", "Pebble"]
COURAGE_KINDS = ["steady", "showy"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    species: str = "rabbit"
    obstacle: str = "brook"
    prize: str = "toy_boat"
    tool: str = "plank"
    hero_name: str = "Pip"
    friend_name: str = "Moss"
    gender: str = "boy"
    courage: str = "steady"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel scared or excited. It is not the same as rushing into danger just to look bold.",
        )
    ],
    "inhale": [
        (
            "Why can one slow inhale help when you feel upset?",
            "A slow inhale can help your body settle down and your mind notice what is really happening. When you are calmer, it is easier to make a careful choice.",
        )
    ],
    "brook": [
        (
            "Why can a brook be slippery?",
            "Water can make stones and mud slick, so little feet may slide. That is why crossing slowly or with a bridge is safer.",
        )
    ],
    "thorns": [
        (
            "Why are thornbushes hard to reach into?",
            "Thornbushes have sharp points that can poke fur or skin. It is safer to use a long tool than to jump into them.",
        )
    ],
    "wind": [
        (
            "Why is wind dangerous near a ledge?",
            "A strong gust can push your body when you are trying to balance. Near a ledge, even a small push can make you stumble.",
        )
    ],
    "plank": [
        (
            "What does a plank do over a little brook?",
            "A plank makes a flat path across the water. It helps you step over instead of leaping where you might slip.",
        )
    ],
    "hook": [
        (
            "What is a hooked branch useful for?",
            "A hooked branch can pull something closer from a safe distance. That way you do not have to put your paws into the thorns.",
        )
    ],
    "rope": [
        (
            "What can a guide rope help with?",
            "A guide rope gives your paws something steady to hold. In windy places, that extra support can keep you balanced.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bravery", "inhale", "brook", "thorns", "wind", "plank", "hook", "rope"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display_name", ent.id)


def generation_prompts(world: World) -> list[str]:
    hero = display_name(world.facts["hero"])
    friend = display_name(world.facts["friend"])
    obstacle = world.facts["obstacle_cfg"]
    prize = world.facts["prize_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "heeded":
        return [
            f'Write an Animal Story for ages 3 to 5 that includes the words "stunt", "inhale", and "pappy", where a little animal wants to do a stunt at {obstacle.place} but learns that real bravery is steady.',
            f"Tell a gentle story about {hero} and {friend}, who lose {prize.phrase} and are tempted by a flashy stunt until pappy teaches a calmer brave choice.",
            "Write a simple woodland tale where a child takes one slow inhale, listens to pappy, and shows bravery by choosing the safe way instead of the showy way.",
        ]
    return [
        f'Write an Animal Story for ages 3 to 5 that includes the words "stunt", "inhale", and "pappy", where a little animal tries a stunt, gets into small trouble, and then learns what bravery means.',
        f"Tell a woodland story about {hero}, who wants to look grand while getting back {prize.phrase}, but must call for pappy's help and then try again the careful way.",
        "Write a child-facing story where bravery first looks noisy and flashy, then becomes quiet and steady after a rescue and a lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    pappy = world.facts["pappy"]
    obstacle = world.facts["obstacle_cfg"]
    prize = world.facts["prize_cfg"]
    tool = world.facts["tool_cfg"]
    hero_name = display_name(hero)
    friend_name = display_name(friend)
    pappy_name = pappy.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little {world.facts['species'].id} named {hero_name}, {hero.pronoun('possessive')} friend {friend_name}, and {pappy_name}. Together they face a problem at {obstacle.place}.",
        ),
        (
            f"What problem did {hero_name} and {friend_name} find?",
            f"They found that {prize.phrase} was stuck or stranded at {obstacle.place}. That is what tempted {hero_name} to think of a quick stunt.",
        ),
        (
            f"What did {pappy_name} tell {hero_name} to do first?",
            f"{pappy_name.capitalize()} told {hero_name} to inhale one slow breath and look at the real trouble. The breath helped turn a noisy, show-off idea into a calmer one.",
        ),
    ]
    if world.facts["outcome"] == "heeded":
        qa.append(
            (
                f"How did {hero_name} show bravery?",
                f"{hero_name} showed bravery by listening, calming down, and using {tool.phrase} instead of leaping into danger. That choice looked less flashy, but it solved the problem safely.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero_name} tried the stunt?",
                f"{hero_name} got into trouble at {obstacle.place} and had to call for {pappy_name}'s help. The risky plan failed because the place was more {obstacle.hazard_word} than it first looked.",
            )
        )
        qa.append(
            (
                f"How did {pappy_name} help?",
                f"{pappy_name.capitalize()} stayed calm and used {tool.phrase} to get {hero_name} safe again. Then {hero_name} used the same careful method to bring back {prize.phrase}.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {hero_name} bringing home {prize.phrase} and understanding bravery in a new way. At the end, {hero.pronoun()} even reminded {friend_name} to inhale and think before rushing.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bravery", "inhale"}
    obstacle_id = world.facts["obstacle_cfg"].id
    tool_id = world.facts["tool_cfg"].id
    if obstacle_id == "brook":
        tags.add("brook")
    elif obstacle_id == "thornbush":
        tags.add("thorns")
    elif obstacle_id == "windy_ledge":
        tags.add("wind")
    tags.add(tool_id)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CURATED
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        species="rabbit",
        obstacle="brook",
        prize="toy_boat",
        tool="plank",
        hero_name="Pip",
        friend_name="Moss",
        gender="boy",
        courage="steady",
    ),
    StoryParams(
        species="squirrel",
        obstacle="thornbush",
        prize="red_scarf",
        tool="hook",
        hero_name="Hazel",
        friend_name="Pebble",
        gender="boy",
        courage="showy",
    ),
    StoryParams(
        species="fox",
        obstacle="windy_ledge",
        prize="berry_basket",
        tool="rope",
        hero_name="Rusty",
        friend_name="Tansy",
        gender="boy",
        courage="showy",
    ),
    StoryParams(
        species="rabbit",
        obstacle="windy_ledge",
        prize="red_scarf",
        tool="rope",
        hero_name="Milo",
        friend_name="Bramble",
        gender="boy",
        courage="steady",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_fits(O, P) :- obstacle(O), prize(P), appears_at(P, O).
tool_solves(O, T) :- obstacle(O), tool(T), solves(T, O).

valid(S, O, P, T) :- species(S), obstacle(O), prize(P), tool(T),
                     prize_fits(O, P), tool_solves(O, T).

outcome(heeded) :- courage(steady).
outcome(rescued) :- courage(showy).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SPECIES:
        lines.append(asp.fact("species", sid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        for place in sorted(prize.places):
            lines.append(asp.fact("appears_at", pid, place))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for place in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, place))
    for courage in COURAGE_KINDS:
        lines.append(asp.fact("courage_kind", courage))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("courage", params.courage),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

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
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=False, qa=True)
        if not smoke_sample.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story world: a flashy stunt, one slow inhale, and a pappy who teaches bravery."
    )
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--courage", choices=COURAGE_KINDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.prize and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        prize = PRIZES[args.prize]
        tool = TOOLS[args.tool]
        if not (prize_fits(obstacle, prize) and tool_solves(obstacle, tool)):
            raise StoryError(explain_rejection(obstacle, prize, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.species is None or combo[0] == args.species)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.prize is None or combo[2] == args.prize)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    species_id, obstacle_id, prize_id, tool_id = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(NAMES[species_id])
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    courage = args.courage or rng.choice(COURAGE_KINDS)
    return StoryParams(
        species=species_id,
        obstacle=obstacle_id,
        prize=prize_id,
        tool=tool_id,
        hero_name=hero_name,
        friend_name=friend_name,
        gender="boy",
        courage=courage,
    )


def generate(params: StoryParams) -> StorySample:
    if params.species not in SPECIES:
        raise StoryError(f"(Unknown species: {params.species})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.courage not in COURAGE_KINDS:
        raise StoryError(f"(Unknown courage kind: {params.courage})")

    species = SPECIES[params.species]
    obstacle = OBSTACLES[params.obstacle]
    prize = PRIZES[params.prize]
    tool = TOOLS[params.tool]
    if not prize_fits(obstacle, prize) or not tool_solves(obstacle, tool):
        raise StoryError(explain_rejection(obstacle, prize, tool))

    world = tell(
        species=species,
        obstacle=obstacle,
        prize=prize,
        tool=tool,
        hero_name=params.hero_name,
        friend_name=params.friend_name,
        gender=params.gender,
        courage=params.courage,
    )

    story = world.render()
    story = story.replace("hero", params.hero_name).replace("friend", params.friend_name)

    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (species, obstacle, prize, tool) combos:\n")
        for species_id, obstacle_id, prize_id, tool_id in combos:
            print(f"  {species_id:8} {obstacle_id:12} {prize_id:12} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
                f"### {p.hero_name}: {p.obstacle}, {p.prize}, {p.tool} "
                f"({p.species}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
