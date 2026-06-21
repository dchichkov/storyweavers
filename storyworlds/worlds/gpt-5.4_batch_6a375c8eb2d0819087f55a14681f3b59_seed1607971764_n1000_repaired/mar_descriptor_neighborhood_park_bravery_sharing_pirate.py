#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mar_descriptor_neighborhood_park_bravery_sharing_pirate.py
=====================================================================================

A standalone story world about children turning a neighborhood park into a pirate
harbor. One child finds something exciting, keeps it first, faces a small fear,
and learns to share so the game can continue together.

The seed constraints for this world are built in:
- setting: neighborhood park
- features: bravery, sharing
- style: pirate tale
- required words in child-facing story text: "mar", "descriptor"

Run it
------
    python storyworlds/worlds/gpt-5.4/mar_descriptor_neighborhood_park_bravery_sharing_pirate.py
    python storyworlds/worlds/gpt-5.4/mar_descriptor_neighborhood_park_bravery_sharing_pirate.py --theme pirates --find shell_map
    python storyworlds/worlds/gpt-5.4/mar_descriptor_neighborhood_park_bravery_sharing_pirate.py --obstacle bridge --share keep
    python storyworlds/worlds/gpt-5.4/mar_descriptor_neighborhood_park_bravery_sharing_pirate.py --all
    python storyworlds/worlds/gpt-5.4/mar_descriptor_neighborhood_park_bravery_sharing_pirate.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mar_descriptor_neighborhood_park_bravery_sharing_pirate.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    shareable: bool = False
    # physical + emotional state
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Theme:
    id: str
    crew_word: str
    opening: str
    captain_title: str
    mate_title: str
    goal: str
    sendoff: str
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


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    sparkle: str
    clue: str
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
    place_phrase: str
    fear_text: str
    brave_act: str
    safe_crossing: str
    fear_kind: str
    difficulty: int
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
class ShareMode:
    id: str
    sense: int
    generous: bool
    first_line: str
    turn_line: str
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
class Guide:
    id: str
    label: str
    phrase: str
    use_text: str
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
        return [e for e in self.entities.values() if e.role in {"finder", "friend"}]

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


def _r_fear_makes_pause(world: World) -> list[str]:
    out: list[str] = []
    finder = world.get("finder")
    if finder.memes["fear"] >= THRESHOLD and finder.meters["crossed"] < THRESHOLD:
        sig = ("pause", finder.id)
        if sig not in world.fired:
            world.fired.add(sig)
            finder.memes["hesitation"] += 1
            out.append("__hesitate__")
    return out


def _r_bravery_crosses(world: World) -> list[str]:
    out: list[str] = []
    finder = world.get("finder")
    friend = world.get("friend")
    if finder.memes["courage"] >= THRESHOLD and friend.memes["support"] >= THRESHOLD:
        sig = ("cross", finder.id)
        if sig not in world.fired:
            world.fired.add(sig)
            finder.meters["crossed"] += 1
            finder.memes["pride"] += 1
            friend.memes["admiration"] += 1
            out.append("__crossed__")
    return out


def _r_sharing_joy(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("treasure")
    finder = world.get("finder")
    friend = world.get("friend")
    if prize.meters["shared"] >= THRESHOLD:
        sig = ("joy", prize.id)
        if sig not in world.fired:
            world.fired.add(sig)
            finder.memes["joy"] += 1
            friend.memes["joy"] += 1
            friend.memes["included"] += 1
            out.append("__shared__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="fear_pause", tag="emotional", apply=_r_fear_makes_pause),
    Rule(name="bravery_cross", tag="emotional", apply=_r_bravery_crosses),
    Rule(name="sharing_joy", tag="social", apply=_r_sharing_joy),
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
        for sent in produced:
            world.say(sent)
    return produced


def brave_enough(obstacle: Obstacle, support_style: str) -> bool:
    base = 1
    bonus = 1 if support_style in {"steady", "cheery"} else 0
    return base + bonus >= obstacle.difficulty


def healthy_sharing(share: ShareMode) -> bool:
    return share.sense >= SENSE_MIN and share.generous


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for find_id in TREASURES:
            for obstacle_id, obstacle in OBSTACLES.items():
                for share_id, share in SHARE_MODES.items():
                    if healthy_sharing(share) and brave_enough(obstacle, "steady"):
                        combos.append((theme_id, find_id, obstacle_id, share_id))
    return combos


def predict_outcome(obstacle: Obstacle, share: ShareMode, support_style: str) -> dict:
    crossed = brave_enough(obstacle, support_style)
    together = healthy_sharing(share)
    return {
        "crossed": crossed,
        "shared": together,
        "happy": crossed and together,
    }


def introduce(world: World, finder: Entity, friend: Entity, theme: Theme) -> None:
    finder.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"One sunny afternoon, {finder.id} and {friend.id} hurried to the neighborhood park "
        f"and turned it into {theme.opening}."
    )
    world.say(
        f'The slide became a ship, the sandbox became a golden shore, and the little footbridge '
        f'looked like a plank over the mar-green moat around their make-believe island.'
    )
    world.say(
        f'"{theme.captain_title} {finder.id} and {theme.mate_title} {friend.id}!" '
        f'{finder.id} cried. "Today we hunt {theme.goal}!"'
    )


def find_treasure(world: World, finder: Entity, friend: Entity, treasure: Treasure) -> None:
    prize = world.get("treasure")
    prize.meters["found"] += 1
    finder.memes["greed"] += 1
    world.say(
        f"Near the sandbox edge, {finder.id} spotted {treasure.phrase}. It {treasure.sparkle}, "
        f"and beside it lay {treasure.clue}."
    )
    world.say(
        f'{friend.id} gasped. "That must be the treasure marker!"'
    )


def clutch(world: World, finder: Entity, friend: Entity, share: ShareMode) -> None:
    prize = world.get("treasure")
    prize.meters["held_by_finder"] += 1
    friend.memes["left_out"] += 1
    world.say(
        f"{finder.id} scooped the treasure up and held it close. {share.first_line}"
    )
    world.say(
        f"{friend.id} stopped smiling. {friend.pronoun().capitalize()} wanted to help too, "
        f"but the game suddenly felt smaller."
    )


def challenge(world: World, finder: Entity, friend: Entity, obstacle: Obstacle, guide: Guide) -> None:
    finder.memes["fear"] += 1
    friend.memes["support"] += 1
    world.facts["predicted_cross"] = predict_outcome(obstacle, SHARE_MODES["share"], guide.id)["crossed"]
    world.say(
        f"To reach the hiding spot, they had to go past {obstacle.place_phrase}. "
        f"{obstacle.fear_text}"
    )
    world.say(
        f'{friend.id} pointed to {guide.phrase}. "{guide.use_text}"'
    )
    propagate(world, narrate=False)


def freeze(world: World, finder: Entity) -> None:
    if finder.memes["hesitation"] >= THRESHOLD:
        world.say(
            f"{finder.id} marched to the edge, then froze. The treasure felt heavy in "
            f"{finder.pronoun('possessive')} hands, and brave pirate words were harder to say "
            f"when the wobble was real."
        )


def choose(world: World, finder: Entity, friend: Entity, share: ShareMode) -> None:
    prize = world.get("treasure")
    if healthy_sharing(share):
        prize.meters["shared"] += 1
        finder.memes["courage"] += 1
        finder.memes["generosity"] += 1
        friend.memes["support"] += 1
        world.say(
            share.turn_line.format(finder=finder.id, friend=friend.id)
        )
        world.say(
            f"{friend.id} stepped close instead of hurrying ahead. With one hand on the guide rope "
            f"and one hand under the treasure, {friend.pronoun()} made room for both of them in the adventure."
        )
    else:
        world.say(
            f'{finder.id} shook {finder.pronoun("possessive")} head. "No, it is mine." '
            f'{friend.id} stayed nearby, but the brave feeling never grew.'
        )
    propagate(world, narrate=False)


def cross(world: World, finder: Entity, friend: Entity, obstacle: Obstacle, guide: Guide) -> None:
    world.say(
        f"Together they {obstacle.safe_crossing}, using {guide.label} as they went. "
        f"{obstacle.brave_act}"
    )
    world.say(
        f"On the other side, the park did not feel scary anymore. It felt wide and bright, "
        f"as if the pirate game had made space for both bravery and kindness."
    )


def bury_treasure(world: World, finder: Entity, friend: Entity, treasure: Treasure, theme: Theme) -> None:
    finder.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"They tucked {treasure.label} under the shady bench and marked the place with a twig X. "
        f"Then {finder.id} laughed. \"Descriptor is a funny word,\" {finder.pronoun()} said, "
        f"\"but today our best descriptor is shared.\""
    )
    world.say(
        f"When other children came by, {finder.id} and {friend.id} invited them into the crew. "
        f"This time the pirates {theme.sendoff} together."
    )


def lonely_end(world: World, finder: Entity, friend: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"{finder.id} kept the treasure tucked to {finder.pronoun('possessive')} chest and stared at "
        f"{obstacle.label}. Without a helping hand, the place stayed too scary to cross."
    )
    world.say(
        f"At last {finder.id} sighed and walked back to the grass beside {friend.id}. "
        f"The park was still lovely, but the game had lost its sparkle because treasure is not much fun all alone."
    )


def tell(
    theme: Theme,
    treasure: Treasure,
    obstacle: Obstacle,
    share: ShareMode,
    guide: Guide,
    finder_name: str = "Mara",
    finder_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    support_trait: str = "steady",
) -> World:
    world = World()
    finder = world.add(Entity(
        id="finder",
        kind="character",
        type=finder_gender,
        label=finder_name,
        role="finder",
        traits=["eager"],
        attrs={"name": finder_name, "support_trait": support_trait},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=[support_trait],
        attrs={"name": friend_name},
    ))
    world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure.label,
        portable=True,
        shareable=True,
    ))

    world.facts["support_trait"] = support_trait
    world.facts["guide"] = guide
    world.facts["share_choice"] = share.id
    world.facts["crossed"] = False
    world.facts["shared"] = False

    introduce(world, finder, friend, theme)
    find_treasure(world, finder, friend, treasure)

    world.para()
    clutch(world, finder, friend, share)
    challenge(world, finder, friend, obstacle, guide)
    freeze(world, finder)

    world.para()
    choose(world, finder, friend, share)

    prize = world.get("treasure")
    crossed = world.get("finder").meters["crossed"] >= THRESHOLD
    shared = prize.meters["shared"] >= THRESHOLD
    world.facts["crossed"] = crossed
    world.facts["shared"] = shared

    if crossed and shared:
        cross(world, finder, friend, obstacle, guide)
        world.para()
        bury_treasure(world, finder, friend, treasure, theme)
        outcome = "shared_bravery"
    else:
        lonely_end(world, finder, friend, obstacle)
        outcome = "lonely"

    world.facts.update(
        theme=theme,
        treasure_cfg=treasure,
        obstacle_cfg=obstacle,
        finder=finder,
        friend=friend,
        parent=world.get("parent"),
        outcome=outcome,
        guide=guide,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        crew_word="pirates",
        opening="a bright pirate harbor with one crooked ship and one sandy cove",
        captain_title="Captain",
        mate_title="First Mate",
        goal="the hidden park treasure",
        sendoff="ran from ship to shore, sharing every clue",
    ),
    "corsairs": Theme(
        id="corsairs",
        crew_word="corsairs",
        opening="a busy sea port with a foam-blue bay and a sandy island fort",
        captain_title="Captain",
        mate_title="Deck Mate",
        goal="the silver clue of the bay",
        sendoff="hurried from fort to ship, calling the whole crew along",
    ),
}

TREASURES = {
    "shell_map": Treasure(
        id="shell_map",
        label="the shell map",
        phrase="a shell tied to a folded paper map",
        sparkle="winked in the sun like a tiny coin",
        clue="a penciled arrow pointing toward the bridge",
        tags={"shell", "map", "sharing"},
    ),
    "gold_button": Treasure(
        id="gold_button",
        label="the gold button",
        phrase="a shiny gold-colored button wrapped in a scrap of blue ribbon",
        sparkle="glittered like a pirate doubloon",
        clue="a chalk mark shaped like a wave",
        tags={"button", "treasure", "sharing"},
    ),
    "compass_cap": Treasure(
        id="compass_cap",
        label="the compass cap",
        phrase="a round bottle cap painted with a compass star",
        sparkle="flashed bright whenever it tilted",
        clue="a little line of pebbles leading onward",
        tags={"compass", "treasure", "sharing"},
    ),
}

OBSTACLES = {
    "bridge": Obstacle(
        id="bridge",
        label="the footbridge",
        place_phrase="the little footbridge over the shallow stream",
        fear_text="The boards were safe, but they gave a tiny wobble under small shoes, and that made the crossing feel big.",
        brave_act="Step by step, {finder} kept going until the wobbly part was behind them.".format(finder="the captain"),
        safe_crossing="walked across the bridge slowly",
        fear_kind="height",
        difficulty=2,
        tags={"bridge", "bravery"},
    ),
    "tunnel": Obstacle(
        id="tunnel",
        label="the tube tunnel",
        place_phrase="the tube tunnel by the climbing hill",
        fear_text="Inside it was dim and echoey, and the hollow sound made even a sunny park seem mysterious.",
        brave_act="One careful crawl later, the dark part was over and laughter bounced out after them.",
        safe_crossing="crawled through the tunnel together",
        fear_kind="dark",
        difficulty=1,
        tags={"tunnel", "bravery"},
    ),
    "stepping_stones": Obstacle(
        id="stepping_stones",
        label="the stepping stones",
        place_phrase="the stepping stones near the flower bed",
        fear_text="Each stone was dry and safe, yet the spaces between them looked longer when the treasure was in hand.",
        brave_act="With a deep breath and a steady pace, the jumps turned small again.",
        safe_crossing="crossed the stepping stones one by one",
        fear_kind="balance",
        difficulty=2,
        tags={"stones", "bravery"},
    ),
}

SHARE_MODES = {
    "share": ShareMode(
        id="share",
        sense=3,
        generous=True,
        first_line='"I found it first," {finder} said, hugging it for a moment.'.format(finder="the captain"),
        turn_line='"Wait," said {finder}. "If we both hold it, we can be brave together."'.format(
            finder="{finder}", friend="{friend}"
        ),
        tags={"sharing", "kindness"},
    ),
    "trade_turns": ShareMode(
        id="trade_turns",
        sense=2,
        generous=True,
        first_line='"I found it first," {finder} said, tucking it under one arm.'.format(finder="the captain"),
        turn_line='"Let us take turns carrying it," said {finder}. "You help me cross first, then it can be your turn."'.format(
            finder="{finder}", friend="{friend}"
        ),
        tags={"sharing", "turns"},
    ),
    "keep": ShareMode(
        id="keep",
        sense=1,
        generous=False,
        first_line='"I found it, so I get all of it," {finder} said.'.format(finder="the captain"),
        turn_line="",
        tags={"selfish"},
    ),
}

GUIDES = {
    "steady": Guide(
        id="steady",
        label="the rope rail",
        phrase="the rope rail along the side",
        use_text="We can use the rope rail. I will stay right beside you.",
        tags={"support", "bravery"},
    ),
    "cheery": Guide(
        id="cheery",
        label="the painted handprints",
        phrase="the painted handprints on the tunnel wall",
        use_text="Let us follow the handprints like pirate signs. I will count with you.",
        tags={"support", "counting"},
    ),
}

GIRL_NAMES = ["Mara", "Lily", "Nora", "Ava", "Mia", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Tom", "Max", "Sam", "Leo", "Finn", "Eli"]


@dataclass
class StoryParams:
    theme: str
    find: str
    obstacle: str
    share: str
    guide: str
    finder_name: str
    finder_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    support_trait: str
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


KNOWLEDGE = {
    "sharing": [(
        "Why is sharing helpful in a game?",
        "Sharing helps everyone join in, so the game stays fun for more than one person. It can also make a hard moment feel easier because friends help each other."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery means doing the right or needed thing even when you feel a little scared. It does not mean never feeling fear."
    )],
    "bridge": [(
        "Why can a little bridge feel scary?",
        "A little bridge can feel scary if it wobbles or sits over water, even when it is safe. Small bodies can notice that wobble very strongly."
    )],
    "tunnel": [(
        "Why can a tunnel feel scary?",
        "A tunnel can feel scary because it is darker and sounds echo inside it. When you go through with a friend, it often feels easier."
    )],
    "stones": [(
        "Why do stepping stones need careful feet?",
        "Stepping stones need careful feet because you have to balance from one to the next. Going slowly helps your body stay steady."
    )],
    "shell": [(
        "What is a shell?",
        "A shell is the hard outer covering from a sea animal. People often find empty shells washed up near water."
    )],
    "map": [(
        "What is a map?",
        "A map is a drawing that helps show where places are and which way to go. Treasure maps use clues to guide a search."
    )],
    "compass": [(
        "What does a compass show?",
        "A compass helps show direction, like north and south. It can help travelers know which way they are facing."
    )],
    "turns": [(
        "What does taking turns mean?",
        "Taking turns means one person uses or carries something first and another person gets a turn next. It is one fair way to share."
    )],
}
KNOWLEDGE_ORDER = ["sharing", "bravery", "bridge", "tunnel", "stones", "shell", "map", "compass", "turns"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    obstacle = f["obstacle_cfg"]
    treasure = f["treasure_cfg"]
    return [
        'Write a pirate-style story for a 3-to-5-year-old set in a neighborhood park that includes the words "mar" and "descriptor."',
        f"Tell a gentle story where {finder.attrs['name']} finds {treasure.label}, feels unsure about {obstacle.label}, and learns that sharing can help bravery grow.",
        f"Write a simple story about two children pretending to be pirates, facing one small fear together, and ending with the treasure being shared."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    treasure = f["treasure_cfg"]
    obstacle = f["obstacle_cfg"]
    guide = f["guide"]
    outcome = f["outcome"]
    finder_name = finder.attrs["name"]
    friend_name = friend.attrs["name"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {finder_name} and {friend_name}, two children playing pirates in the neighborhood park. They turn ordinary park places into parts of a treasure adventure."
        ),
        (
            f"What treasure did {finder_name} find?",
            f"{finder_name} found {treasure.phrase}. It looked special, so the treasure felt important to the game right away."
        ),
        (
            f"Why did {finder_name} stop before the obstacle?",
            f"{finder_name} stopped because {obstacle.label} felt scary in that moment. Even though it was safe, the wobble or dimness made the crossing feel much bigger."
        ),
    ]
    if outcome == "shared_bravery":
        qa.extend([
            (
                f"How did sharing help {finder_name} become brave?",
                f"{finder_name} shared the treasure instead of clutching it alone, and that let {friend_name} help with the hard part. Because they carried the moment together, bravery grew enough for the crossing."
            ),
            (
                f"What did {friend_name} do to help?",
                f"{friend_name} stayed close and used {guide.label} to guide the way. That support mattered because {finder_name} was scared and needed a calm helper nearby."
            ),
            (
                "How did the story end?",
                f"It ended with the treasure hidden safely and the pirate game opened to other children too. The ending shows that the park became happier once bravery and sharing were joined together."
            ),
        ])
    else:
        qa.extend([
            (
                f"Why did the adventure shrink when {finder_name} would not share?",
                f"The adventure shrank because {finder_name} tried to carry the treasure and the fear alone. Without shared help, the scary place still felt too big to cross."
            ),
            (
                "How did the story end?",
                f"It ended quietly, with the children back on the grass and the game feeling less sparkly. The ending shows that keeping everything to yourself can make a fun game smaller."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    treasure = f["treasure_cfg"]
    obstacle = f["obstacle_cfg"]
    share = SHARE_MODES[f["share_choice"]]
    tags: set[str] = set(obstacle.tags) | set(treasure.tags) | set(share.tags) | {"bravery", "sharing"}
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        find="shell_map",
        obstacle="bridge",
        share="share",
        guide="steady",
        finder_name="Mara",
        finder_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        support_trait="steady",
    ),
    StoryParams(
        theme="pirates",
        find="gold_button",
        obstacle="tunnel",
        share="trade_turns",
        guide="cheery",
        finder_name="Tom",
        finder_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        parent="father",
        support_trait="cheery",
    ),
    StoryParams(
        theme="corsairs",
        find="compass_cap",
        obstacle="stepping_stones",
        share="keep",
        guide="steady",
        finder_name="Ava",
        finder_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
        support_trait="steady",
    ),
]


def explain_share(share_id: str) -> str:
    share = SHARE_MODES[share_id]
    return (
        f"(Refusing share mode '{share_id}': it makes the finder keep the treasure instead of sharing it. "
        f"This world centers bravery growing through sharing, so choose a generous mode such as "
        f"{', '.join(sorted(k for k, v in SHARE_MODES.items() if healthy_sharing(v)))}.)"
    )


ASP_RULES = r"""
healthy_share(S) :- share_mode(S), share_sense(S,N), sense_min(M), N >= M, generous(S).
support_bonus(steady,1).
support_bonus(cheery,1).
support_bonus(other,0).

crosses(O,Support) :- obstacle(O), obstacle_diff(O,D), support_bonus(Support,B), 1 + B >= D.
valid(T,F,O,S) :- theme(T), treasure(F), obstacle(O), share_mode(S), healthy_share(S), crosses(O,steady).

happy(T,F,O,S,Support) :- theme(T), treasure(F), obstacle(O), share_mode(S),
                          healthy_share(S), crosses(O,Support).
outcome(shared_bravery) :- chosen_theme(T), chosen_find(F), chosen_obstacle(O), chosen_share(S), chosen_support(Support),
                           happy(T,F,O,S,Support).
outcome(lonely) :- chosen_theme(_), not outcome(shared_bravery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid in TREASURES:
        lines.append(asp.fact("treasure", fid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_diff", oid, obstacle.difficulty))
    for sid, share in SHARE_MODES.items():
        lines.append(asp.fact("share_mode", sid))
        lines.append(asp.fact("share_sense", sid, share.sense))
        if share.generous:
            lines.append(asp.fact("generous", sid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        asp.fact("chosen_theme", params.theme),
        asp.fact("chosen_find", params.find),
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_share", params.share),
        asp.fact("chosen_support", params.support_trait if params.support_trait in {"steady", "cheery"} else "other"),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if healthy_sharing(SHARE_MODES[params.share]) and brave_enough(OBSTACLES[params.obstacle], params.support_trait):
        return "shared_bravery"
    return "lonely"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcome checks differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirate play in a neighborhood park, where sharing helps bravery grow."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--find", choices=TREASURES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--share", choices=SHARE_MODES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.share and not healthy_sharing(SHARE_MODES[args.share]):
        raise StoryError(explain_share(args.share))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.find is None or combo[1] == args.find)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.share is None or combo[3] == args.share)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, find, obstacle, share = rng.choice(sorted(combos))
    guide = args.guide or ("cheery" if obstacle == "tunnel" else "steady")
    finder_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    finder_name = _pick_name(rng, finder_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=finder_name)
    parent = args.parent or rng.choice(["mother", "father"])
    support_trait = "cheery" if guide == "cheery" else "steady"

    return StoryParams(
        theme=theme,
        find=find,
        obstacle=obstacle,
        share=share,
        guide=guide,
        finder_name=finder_name,
        finder_gender=finder_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        support_trait=support_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.find not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.find})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.share not in SHARE_MODES:
        raise StoryError(f"(Unknown share mode: {params.share})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if not healthy_sharing(SHARE_MODES[params.share]):
        raise StoryError(explain_share(params.share))

    world = tell(
        theme=THEMES[params.theme],
        treasure=TREASURES[params.find],
        obstacle=OBSTACLES[params.obstacle],
        share=SHARE_MODES[params.share],
        guide=GUIDES[params.guide],
        finder_name=params.finder_name,
        finder_gender=params.finder_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        support_trait=params.support_trait,
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
        print(f"{len(combos)} compatible (theme, find, obstacle, share) combos:\n")
        for theme, find, obstacle, share in combos:
            print(f"  {theme:8} {find:12} {obstacle:16} {share}")
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
            header = f"### {p.finder_name} & {p.friend_name}: {p.find} at {p.obstacle} ({p.share})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
