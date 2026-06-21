#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/puzzle_transformation_bravery_pirate_tale.py
========================================================================

A standalone story world for a small pirate-style tale about a child who must be
brave, reveal a hidden clue, solve a puzzle, and cross a small obstacle to reach
a treasure chest.

The domain is built around two linked changes:
- a physical transformation: a blank clue parchment changes and reveals marks
- an emotional transformation: a worried child grows into a brave captain

Run it
------
    python storyworlds/worlds/gpt-5.4/puzzle_transformation_bravery_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/puzzle_transformation_bravery_pirate_tale.py --setting cove --puzzle color_rings
    python storyworlds/worlds/gpt-5.4/puzzle_transformation_bravery_pirate_tale.py --setting dunes --aid rail
    python storyworlds/worlds/gpt-5.4/puzzle_transformation_bravery_pirate_tale.py --aid handhold --setting dunes
    python storyworlds/worlds/gpt-5.4/puzzle_transformation_bravery_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/puzzle_transformation_bravery_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/puzzle_transformation_bravery_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    rig: str
    obstacle: str
    reveal: str
    source_text: str
    source_action: str
    chest_place: str
    ending_path: str
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
    phrase: str
    risk: int
    worry: str
    crossing: str
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
class Reveal:
    id: str
    label: str
    action: str
    effect: str
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
class Aid:
    id: str
    label: str
    phrase: str
    bonus: int
    compatible: set[str] = field(default_factory=set)
    offer: str = ""
    use_text: str = ""
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
class Puzzle:
    id: str
    label: str
    needs_reveal: str
    marks: str
    solve_text: str
    open_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "attempt_cross": False,
            "inspected_clue": False,
        }

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


@dataclass
class Rule:
    name: str
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


def _r_reveal(world: World) -> list[str]:
    clue = world.get("clue")
    setting = world.facts["setting_cfg"]
    puzzle = world.facts["puzzle_cfg"]
    if clue.meters["exposed"] < THRESHOLD:
        return []
    if puzzle.needs_reveal != setting.reveal:
        return []
    sig = ("reveal", setting.id, puzzle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["visible"] += 1
    world.facts["clue_revealed"] = True
    return ["__reveal__"]


def _r_solve(world: World) -> list[str]:
    clue = world.get("clue")
    chest = world.get("chest")
    if clue.meters["visible"] < THRESHOLD or not world.facts["inspected_clue"]:
        return []
    sig = ("solve", world.facts["puzzle_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chest.meters["solved"] += 1
    world.facts["puzzle_solved"] = True
    return ["__solve__"]


def _r_cross(world: World) -> list[str]:
    hero = world.get("hero")
    chest = world.get("chest")
    if not world.facts["attempt_cross"] or chest.meters["solved"] < THRESHOLD:
        return []
    if hero.memes["courage"] < float(world.facts["obstacle_cfg"].risk):
        return []
    sig = ("cross", world.facts["obstacle_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["across"] += 1
    world.facts["crossed"] = True
    return ["__cross__"]


def _r_open(world: World) -> list[str]:
    hero = world.get("hero")
    chest = world.get("chest")
    if hero.meters["across"] < THRESHOLD or chest.meters["solved"] < THRESHOLD:
        return []
    sig = ("open", world.facts["prize_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chest.meters["open"] += 1
    hero.memes["joy"] += 1
    hero.memes["brave"] += 1
    hero.memes["fear"] = 0.0
    world.facts["opened"] = True
    return ["__open__"]


CAUSAL_RULES = [
    Rule(name="reveal", apply=_r_reveal),
    Rule(name="solve", apply=_r_solve),
    Rule(name="cross", apply=_r_cross),
    Rule(name="open", apply=_r_open),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    return produced


SETTINGS = {
    "cove": Setting(
        id="cove",
        label="windy cove",
        scene="a windy cove with bright waves",
        rig="A striped towel was their pirate ship, a driftwood stick was their mast, and a little tin box was the treasure chest they hoped to find.",
        obstacle="stepping_stones",
        reveal="splash",
        source_text="sea spray",
        source_action="when the waves splashed over it",
        chest_place="on a flat rock past the stepping stones",
        ending_path="splashed back along the stepping stones",
        tags={"beach", "sea"},
    ),
    "dunes": Setting(
        id="dunes",
        label="golden dunes",
        scene="golden dunes above the shore",
        rig="A picnic blanket was their pirate ship, a red shovel was their mast, and a weathered crate in the sand looked like an old captain's chest.",
        obstacle="gangplank",
        reveal="sun",
        source_text="sunlight",
        source_action="when they held it up in the sunshine",
        chest_place="at the far end of a narrow driftwood gangplank",
        ending_path="tiptoed proudly back across the gangplank",
        tags={"beach", "sun"},
    ),
    "grotto": Setting(
        id="grotto",
        label="rocky grotto",
        scene="a rocky grotto where the tide whispered in and out",
        rig="A smooth log was their pirate ship, a shell bucket was their mast, and a tiny brass-bound chest waited in a nook beyond the shadows.",
        obstacle="cave_tunnel",
        reveal="rubbing",
        source_text="a soft charcoal rub",
        source_action="when they rubbed it with a smudgy bit of charcoal",
        chest_place="in a nook beyond the cave tunnel",
        ending_path="came back through the tunnel with lantern-light dancing on the walls",
        tags={"cave", "shore"},
    ),
}

OBSTACLES = {
    "stepping_stones": Obstacle(
        id="stepping_stones",
        label="stepping stones",
        phrase="a line of slippery stepping stones",
        risk=2,
        worry="They looked shiny and a little wobbly with spray.",
        crossing="stepped from stone to stone",
        tags={"stones", "balance"},
    ),
    "gangplank": Obstacle(
        id="gangplank",
        label="gangplank",
        phrase="a narrow driftwood gangplank",
        risk=3,
        worry="It was only a plank, and the sand below made it look very high.",
        crossing="walked slowly across the plank",
        tags={"plank", "balance"},
    ),
    "cave_tunnel": Obstacle(
        id="cave_tunnel",
        label="cave tunnel",
        phrase="a dim cave tunnel",
        risk=2,
        worry="The tunnel was not far, but it was shadowy and full of echoy drips.",
        crossing="went through the tunnel with careful steps",
        tags={"cave", "dark"},
    ),
}

REVEALS = {
    "splash": Reveal(
        id="splash",
        label="sea spray",
        action="splashed the parchment with a little seawater",
        effect="blue rings and marks bloomed across the blank paper",
        tags={"water", "transformation", "puzzle"},
    ),
    "sun": Reveal(
        id="sun",
        label="sunlight",
        action="held the parchment up to the bright sun",
        effect="golden arrows shone through the pale paper",
        tags={"sun", "transformation", "puzzle"},
    ),
    "rubbing": Reveal(
        id="rubbing",
        label="charcoal rubbing",
        action="rubbed the paper with a smudgy charcoal stick",
        effect="hidden shell shapes rose out of the blank page",
        tags={"charcoal", "transformation", "puzzle"},
    ),
}

AIDS = {
    "handhold": Aid(
        id="handhold",
        label="handhold",
        phrase="a steady hand",
        bonus=1,
        compatible={"stepping_stones", "cave_tunnel"},
        offer="held out a hand and promised not to let go",
        use_text="with one hand tucked safely in a friend's hand",
        tags={"help", "hands"},
    ),
    "rope": Aid(
        id="rope",
        label="rope",
        phrase="a knotted rope",
        bonus=2,
        compatible={"stepping_stones", "gangplank"},
        offer="looped a knotted rope around a post so there was something strong to hold",
        use_text="with fingers curled around the rope",
        tags={"rope", "help"},
    ),
    "rail": Aid(
        id="rail",
        label="rail",
        phrase="a driftwood rail",
        bonus=1,
        compatible={"gangplank"},
        offer="pointed to a driftwood rail along one side of the plank",
        use_text="with a hand sliding along the rail",
        tags={"rail", "help"},
    ),
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        bonus=1,
        compatible={"cave_tunnel"},
        offer="clicked on a little lantern so the dark corners turned gentle and gold",
        use_text="with the lantern making a warm path ahead",
        tags={"lantern", "light"},
    ),
}

PUZZLES = {
    "color_rings": Puzzle(
        id="color_rings",
        label="ring puzzle",
        needs_reveal="splash",
        marks="three blue rings curled onto the page, with tiny dots showing which ring should be pressed first, second, and third.",
        solve_text="They pressed the rings on the lid in the order the water marks showed.",
        open_text="The lid gave a cheerful click.",
        tags={"puzzle", "colors"},
    ),
    "sun_arrows": Puzzle(
        id="sun_arrows",
        label="arrow puzzle",
        needs_reveal="sun",
        marks="thin golden arrows pointed left, right, and then straight ahead toward a turning brass dial.",
        solve_text="They turned the brass dial the way the arrows pointed.",
        open_text="With a soft clack, the lock sprang free.",
        tags={"puzzle", "arrows"},
    ),
    "shell_shapes": Puzzle(
        id="shell_shapes",
        label="shell puzzle",
        needs_reveal="rubbing",
        marks="spirals, stars, and scallop shapes appeared in a neat little row across the page.",
        solve_text="They matched the shell buttons on the chest to the shapes on the clue.",
        open_text="The chest popped open with a bright ping.",
        tags={"puzzle", "shapes"},
    ),
}

PRIZES = {
    "sash": Prize(
        id="sash",
        label="captain sash",
        phrase="a red captain sash",
        ending="When it fluttered across %s's shoulder, %s felt less like a worried deckhand and more like a real captain.",
        tags={"clothes", "captain"},
    ),
    "compass": Prize(
        id="compass",
        label="brass compass",
        phrase="a tiny brass compass",
        ending="The little compass needle trembled, then settled, and %s smiled as if %s own heart had settled too.",
        tags={"compass", "captain"},
    ),
    "star_lantern": Prize(
        id="star_lantern",
        label="star lantern",
        phrase="a star-cut lantern",
        ending="When the lantern shone through its star holes, warm dots of light danced over %s face, and %s stood taller at once.",
        tags={"lantern", "light", "captain"},
    ),
}

TRAIT_BASE = {
    "shy": 1,
    "careful": 2,
    "curious": 2,
    "steady": 3,
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    setting: str
    puzzle: str
    aid: str
    prize: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str
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


def courage_score(trait: str, aid: str) -> int:
    if trait not in TRAIT_BASE or aid not in AIDS:
        raise StoryError("(Unknown trait or aid.)")
    return TRAIT_BASE[trait] + AIDS[aid].bonus


def compatible(setting_id: str, puzzle_id: str, aid_id: str, trait: str) -> bool:
    if setting_id not in SETTINGS or puzzle_id not in PUZZLES or aid_id not in AIDS or trait not in TRAIT_BASE:
        return False
    setting = SETTINGS[setting_id]
    puzzle = PUZZLES[puzzle_id]
    aid = AIDS[aid_id]
    obstacle = OBSTACLES[setting.obstacle]
    if puzzle.needs_reveal != setting.reveal:
        return False
    if setting.obstacle not in aid.compatible:
        return False
    return courage_score(trait, aid_id) >= obstacle.risk


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for puzzle_id in PUZZLES:
            for aid_id in AIDS:
                for trait in TRAIT_BASE:
                    if compatible(setting_id, puzzle_id, aid_id, trait):
                        combos.append((setting_id, puzzle_id, aid_id, trait))
    return sorted(combos)


def mood_of(params: StoryParams) -> str:
    score = courage_score(params.trait, params.aid)
    risk = OBSTACLES[SETTINGS[params.setting].obstacle].risk
    return "bold" if score > risk else "steady"


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright afternoon, {hero.id} and {friend.id} turned the shore into {setting.scene}. "
        f"{setting.rig}"
    )
    world.say(
        f'"Captain {hero.id} and Scout {friend.id}!" {friend.id} cheered. "Let\'s hunt for treasure!"'
    )


def discover(world: World, hero: Entity, friend: Entity, setting: Setting, obstacle: Obstacle) -> None:
    world.say(
        f"Soon they spotted a tiny chest {setting.chest_place}, beyond {obstacle.phrase}. "
        f"{obstacle.worry}"
    )
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} took one step forward and then stopped. {hero.pronoun().capitalize()} wanted the treasure very much, but {hero.pronoun('possessive')} brave voice felt small."
    )


def find_clue(world: World, hero: Entity, friend: Entity) -> None:
    clue = world.get("clue")
    clue.meters["found"] += 1
    world.say(
        f"Then {friend.id} found a rolled parchment tucked under a shell. "
        f'It looked blank at first. "A puzzle clue!" {friend.id} whispered.'
    )


def encourage(world: World, hero: Entity, friend: Entity, aid: Aid, obstacle: Obstacle) -> None:
    hero.memes["courage"] += float(AIDS[aid.id].bonus)
    world.say(
        f'"We do not have to rush," {friend.id} said. {friend.pronoun().capitalize()} {aid.offer}. '
        f'"Real pirates can be careful and brave at the same time."'
    )
    world.facts["helper"] = friend.id
    world.facts["encouraged"] = True
    if courage_score(world.facts["trait"], aid.id) >= obstacle.risk:
        world.say(
            f"{hero.id} took a slow breath. The chest still looked far away, but it no longer looked impossible."
        )


def reveal_clue(world: World, setting: Setting, reveal: Reveal, puzzle: Puzzle) -> None:
    clue = world.get("clue")
    clue.meters["exposed"] += 1
    world.facts["inspected_clue"] = True
    propagate(world)
    world.say(
        f"They {reveal.action}, and the plain parchment changed {setting.source_action}. "
        f"{reveal.effect}"
    )
    world.say(
        f"Now the puzzle was clear: {puzzle.marks}"
    )


def solve_puzzle(world: World, puzzle: Puzzle) -> None:
    propagate(world)
    world.say(puzzle.solve_text)
    world.say(puzzle.open_text)


def cross_and_open(world: World, hero: Entity, setting: Setting, obstacle: Obstacle, aid: Aid, prize: Prize) -> None:
    world.facts["attempt_cross"] = True
    propagate(world)
    if not world.facts.get("crossed"):
        raise StoryError("(The child was not brave enough to cross with this aid.)")
    world.say(
        f"Then {hero.id} {obstacle.crossing}, {aid.use_text}. Step by step, {hero.pronoun()} reached the little chest."
    )
    world.say(
        f"Inside was {prize.phrase}."
    )
    sub = hero.pronoun("subject")
    pos = hero.pronoun("possessive")
    world.say(prize.ending % (pos, pos))
    world.say(
        f"When {hero.id} {setting.ending_path}, {hero.pronoun()} was still the same child, but not with the same small feeling inside."
    )


def finish(world: World, hero: Entity, friend: Entity, parent: Entity) -> None:
    mood = world.facts["mood"]
    if mood == "bold":
        world.say(
            f'"Captain {hero.id}!" laughed {friend.id}. Even {parent.label_word} clapped from the dry sand as the two pirates marched home with shining eyes.'
        )
    else:
        world.say(
            f'{friend.id} gave {hero.id} a proud grin, and {parent.label_word} smiled too. The shore felt friendlier now, as if it knew a new brave captain when it saw one.'
        )


def tell(
    setting: Setting,
    puzzle: Puzzle,
    aid: Aid,
    prize: Prize,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, role="hero", label=hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, role="friend", label=friend_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent"))
    clue = world.add(Entity(id="clue", type="parchment", label="parchment clue"))
    chest = world.add(Entity(id="chest", type="chest", label="treasure chest"))

    hero.attrs["name"] = hero_name
    friend.attrs["name"] = friend_name
    parent.attrs["name"] = parent.label_word
    hero.memes["courage"] = float(TRAIT_BASE[trait])
    hero.memes["fear"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["brave"] = 0.0
    clue.meters["exposed"] = 0.0
    clue.meters["visible"] = 0.0
    chest.meters["solved"] = 0.0
    chest.meters["open"] = 0.0

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        clue=clue,
        chest=chest,
        hero_name=hero_name,
        friend_name=friend_name,
        setting_cfg=setting,
        obstacle_cfg=OBSTACLES[setting.obstacle],
        reveal_cfg=REVEALS[setting.reveal],
        puzzle_cfg=puzzle,
        aid_cfg=aid,
        prize_cfg=prize,
        trait=trait,
        mood="",
        clue_revealed=False,
        puzzle_solved=False,
        crossed=False,
        opened=False,
        encouraged=False,
        helper=friend_name,
    )

    mood = "bold" if courage_score(trait, aid.id) > OBSTACLES[setting.obstacle].risk else "steady"
    world.facts["mood"] = mood

    introduce(world, hero, friend, setting)
    discover(world, hero, friend, setting, OBSTACLES[setting.obstacle])

    world.para()
    find_clue(world, hero, friend)
    encourage(world, hero, friend, aid, OBSTACLES[setting.obstacle])
    reveal_clue(world, setting, REVEALS[setting.reveal], puzzle)
    solve_puzzle(world, puzzle)

    world.para()
    cross_and_open(world, hero, setting, OBSTACLES[setting.obstacle], aid, prize)
    finish(world, hero, friend, parent)

    return world


KNOWLEDGE = {
    "puzzle": [
        (
            "What is a puzzle?",
            "A puzzle is a problem with pieces, clues, or steps that fit together in a special way. You solve it by looking carefully and thinking about what comes next."
        )
    ],
    "rope": [
        (
            "Why can a rope help someone cross carefully?",
            "A rope gives your hands something strong to hold onto. That can help your body feel steadier when your feet are nervous."
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern makes dark places easier to see. Good light can make a place feel safer and help you notice where to step."
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass points north, so it helps travelers know which way they are facing. Pirates in stories often use one to keep from getting lost."
        )
    ],
    "brave": [
        (
            "What does being brave mean?",
            "Being brave does not mean never feeling scared. It means doing the right careful thing even when your heart is thumping."
        )
    ],
    "transformation": [
        (
            "What is a transformation?",
            "A transformation is a change from one state to another. A thing can change on the outside, like blank paper showing hidden marks, or on the inside, like a child feeling braver."
        )
    ],
}
KNOWLEDGE_ORDER = ["puzzle", "rope", "lantern", "compass", "brave", "transformation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting_cfg"]
    puzzle = f["puzzle_cfg"]
    prize = f["prize_cfg"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the word "puzzle" and a brave child finding treasure by the sea.',
        f"Tell a gentle pirate tale where {hero.attrs['name']} and {friend.attrs['name']} discover a blank clue that transforms in {setting.source_text}, solve a {puzzle.label}, and reach a chest.",
        f"Write a short story about transformation and bravery, ending with {hero.attrs['name']} finding {prize.phrase} and feeling changed inside.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    setting = f["setting_cfg"]
    obstacle = f["obstacle_cfg"]
    puzzle = f["puzzle_cfg"]
    aid = f["aid_cfg"]
    prize = f["prize_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['name']} and {friend.attrs['name']}, two children pretending to be pirates by the shore. {parent.label_word.capitalize()} was nearby while they explored."
        ),
        (
            "What made the story feel like a pirate adventure?",
            f"They turned the shore into {setting.scene} and hunted for a tiny treasure chest. The pretend ship and the treasure hunt made the day feel like a pirate game."
        ),
        (
            "What was the puzzle clue like at first, and how did it change?",
            f"At first the parchment looked blank. Then it changed when they used {setting.source_text}, and hidden marks appeared, so the children could finally read the puzzle."
        ),
        (
            f"Why was {hero.attrs['name']} nervous?",
            f"{hero.attrs['name']} was worried about {obstacle.phrase} because it looked tricky and uncertain. The chest was on the other side, so the brave part of the story began when fear met something worth trying for."
        ),
        (
            f"How did {friend.attrs['name']} help {hero.attrs['name']}?",
            f"{friend.attrs['name']} helped by offering {aid.phrase} and by speaking calmly instead of rushing. That support made the crossing feel possible, because bravery grew together with steadiness."
        ),
        (
            "How did they open the chest?",
            f"They solved the clue first, and the puzzle showed them exactly what to press or turn. Because they understood the marks, the chest could open instead of staying locked."
        ),
        (
            f"How did {hero.attrs['name']} change by the end?",
            f"By the end, {hero.attrs['name']} had gone from feeling small and worried to feeling brave and steady. Finding {prize.phrase} gave a final picture of that change, because the treasure matched the courage {hero.pronoun()} had just shown."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"puzzle", "brave", "transformation"}
    aid = f["aid_cfg"]
    prize = f["prize_cfg"]
    if "rope" in aid.tags:
        tags.add("rope")
    if "lantern" in aid.tags or "lantern" in prize.tags:
        tags.add("lantern")
    if "compass" in prize.tags:
        tags.add("compass")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: crossed={world.facts.get('crossed')} clue_revealed={world.facts.get('clue_revealed')} opened={world.facts.get('opened')} mood={world.facts.get('mood')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cove",
        puzzle="color_rings",
        aid="handhold",
        prize="sash",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        setting="dunes",
        puzzle="sun_arrows",
        aid="rope",
        prize="compass",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
        trait="shy",
    ),
    StoryParams(
        setting="grotto",
        puzzle="shell_shapes",
        aid="lantern",
        prize="star_lantern",
        hero_name="Zoe",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        setting="dunes",
        puzzle="sun_arrows",
        aid="rope",
        prize="sash",
        hero_name="Leo",
        hero_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        parent="father",
        trait="steady",
    ),
]


def explain_rejection(setting_id: str, puzzle_id: str, aid_id: str, trait: str) -> str:
    setting = SETTINGS.get(setting_id)
    puzzle = PUZZLES.get(puzzle_id)
    aid = AIDS.get(aid_id)
    if setting and puzzle and puzzle.needs_reveal != setting.reveal:
        return (
            f"(No story: {setting.label} reveals clues with {setting.source_text}, but the "
            f"{puzzle.label} needs {REVEALS[puzzle.needs_reveal].label}. Pick a puzzle that matches the setting's clue transformation.)"
        )
    if setting and aid and setting.obstacle not in aid.compatible:
        obstacle = OBSTACLES[setting.obstacle]
        return (
            f"(No story: {aid.label} does not fit {obstacle.label}. Choose an aid that can reasonably help with that obstacle.)"
        )
    if setting and aid and trait in TRAIT_BASE:
        obstacle = OBSTACLES[setting.obstacle]
        score = courage_score(trait, aid_id)
        if score < obstacle.risk:
            return (
                f"(No story: with trait '{trait}' and aid '{aid_id}', the courage score is {score}, "
                f"but crossing {obstacle.label} needs at least {obstacle.risk}. Pick stronger help or a steadier trait.)"
            )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
valid(S, P, A, T) :- setting(S), puzzle(P), aid(A), trait(T),
                     reveals_with(S, R), needs_reveal(P, R),
                     has_obstacle(S, O), helps_on(A, O),
                     base_courage(T, C), aid_bonus(A, B), obstacle_risk(O, K),
                     C + B >= K.

margin(S, A, T, M) :- has_obstacle(S, O), base_courage(T, C), aid_bonus(A, B),
                      obstacle_risk(O, K), M = C + B - K.

mood(S, A, T, bold) :- margin(S, A, T, M), M > 0.
mood(S, A, T, steady) :- margin(S, A, T, 0).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("reveals_with", sid, setting.reveal))
        lines.append(asp.fact("has_obstacle", sid, setting.obstacle))
    for pid, puzzle in PUZZLES.items():
        lines.append(asp.fact("puzzle", pid))
        lines.append(asp.fact("needs_reveal", pid, puzzle.needs_reveal))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("aid_bonus", aid_id, aid.bonus))
        for obstacle in sorted(aid.compatible):
            lines.append(asp.fact("helps_on", aid_id, obstacle))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_risk", oid, obstacle.risk))
    for trait, base in TRAIT_BASE.items():
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("base_courage", trait, base))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_mood(setting: str, aid: str, trait: str) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_setting", setting),
        asp.fact("chosen_aid", aid),
        asp.fact("chosen_trait", trait),
        "chosen_mood(M) :- chosen_setting(S), chosen_aid(A), chosen_trait(T), mood(S, A, T, M).",
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_mood/1."))
    moods = asp.atoms(model, "chosen_mood")
    return moods[0][0] if moods else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate-style treasure hunt with a transforming clue and a brave crossing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--trait", choices=sorted(TRAIT_BASE))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.puzzle and args.aid and args.trait:
        if not compatible(args.setting, args.puzzle, args.aid, args.trait):
            raise StoryError(explain_rejection(args.setting, args.puzzle, args.aid, args.trait))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.puzzle is None or combo[1] == args.puzzle)
        and (args.aid is None or combo[2] == args.aid)
        and (args.trait is None or combo[3] == args.trait)
    ]
    if not combos:
        s = args.setting or next(iter(SETTINGS))
        p = args.puzzle or next(iter(PUZZLES))
        a = args.aid or next(iter(AIDS))
        t = args.trait or next(iter(TRAIT_BASE))
        raise StoryError(explain_rejection(s, p, a, t))

    setting_id, puzzle_id, aid_id, trait = rng.choice(sorted(combos))
    prize_id = args.prize or rng.choice(sorted(PRIZES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        puzzle=puzzle_id,
        aid=aid_id,
        prize=prize_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.puzzle not in PUZZLES:
        raise StoryError(f"(Unknown puzzle: {params.puzzle})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.trait not in TRAIT_BASE:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if not compatible(params.setting, params.puzzle, params.aid, params.trait):
        raise StoryError(explain_rejection(params.setting, params.puzzle, params.aid, params.trait))

    world = tell(
        setting=SETTINGS[params.setting],
        puzzle=PUZZLES[params.puzzle],
        aid=AIDS[params.aid],
        prize=PRIZES[params.prize],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
    )

    story = world.render().replace("hero", params.hero_name).replace("friend", params.friend_name)
    story = story.replace("parent", world.get("parent").label_word)
    story = story.replace(f"{params.hero_name}.attrs", params.hero_name)

    # Replace entity ids used in direct narration with display names.
    story = story.replace("hero", params.hero_name)
    story = story.replace("friend", params.friend_name)

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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    rng = random.Random(123)
    for _ in range(12):
        p = resolve_params(build_parser().parse_args([]), rng)
        cases.append(p)

    bad = 0
    for p in cases:
        py_mood = mood_of(p)
        clingo_mood = asp_mood(p.setting, p.aid, p.trait)
        if py_mood != clingo_mood:
            bad += 1
    if bad == 0:
        print(f"OK: mood model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} mood results differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show mood/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, puzzle, aid, trait) combos:\n")
        for setting, puzzle, aid, trait in combos:
            print(f"  {setting:8} {puzzle:12} {aid:9} {trait}")
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
            header = f"### {p.hero_name}: {p.setting}, {p.puzzle}, {p.aid}, {mood_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
