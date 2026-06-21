#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dismay_paraphrase_kindness_teamwork_sharing_pirate_tale.py
====================================================================================

A standalone story world for a tiny pirate-style tale about a misunderstanding,
dismay, a kind paraphrase, teamwork, and sharing.

Core premise
------------
Two children turn an ordinary place into a pirate adventure. One child spots the
last clue and blurts out directions too quickly. The other child misunderstands,
feels dismay, and the treasure hunt stalls. A calm grown-up paraphrases what each
child meant and felt. Once the directions are clear, the children work together,
reach the treasure, and share it.

This world is deliberately narrow: it only generates variants where
- the setting can honestly host the obstacle,
- the obstacle really needs teamwork,
- the treasure is something children can reasonably share.

Run it
------
    python storyworlds/worlds/gpt-5.4/dismay_paraphrase_kindness_teamwork_sharing_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/dismay_paraphrase_kindness_teamwork_sharing_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/dismay_paraphrase_kindness_teamwork_sharing_pirate_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/dismay_paraphrase_kindness_teamwork_sharing_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/dismay_paraphrase_kindness_teamwork_sharing_pirate_tale.py --json
    python storyworlds/worlds/gpt-5.4/dismay_paraphrase_kindness_teamwork_sharing_pirate_tale.py --verify
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
    scene: str
    rig: str
    goal: str
    obstacle_nook: str
    affords: set[str] = field(default_factory=set)
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
    location_text: str
    wrong_action: str
    correction_text: str
    teamwork_text: str
    opener_text: str
    requires: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    reveal_text: str
    share_text: str
    shareable: bool = True
    plural: bool = True
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
class HelperKind:
    id: str
    type: str
    entry: str
    warmth: str
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
        return [e for e in self.entities.values() if e.role in {"caller", "mate"}]

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


def _r_dismay(world: World) -> list[str]:
    caller = world.get("caller")
    mate = world.get("mate")
    obstacle = world.get("obstacle")
    if obstacle.meters["misheard"] < THRESHOLD:
        return []
    sig = ("dismay", mate.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mate.memes["dismay"] += 1
    mate.memes["hurt"] += 1
    caller.memes["confusion"] += 1
    return ["__dismay__"]


def _r_open(world: World) -> list[str]:
    caller = world.get("caller")
    mate = world.get("mate")
    obstacle = world.get("obstacle")
    if obstacle.meters["guided"] < THRESHOLD:
        return []
    if caller.meters["helped"] < THRESHOLD or mate.meters["helped"] < THRESHOLD:
        return []
    sig = ("open", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["opened"] += 1
    caller.memes["teamwork"] += 1
    mate.memes["teamwork"] += 1
    return ["__opened__"]


def _r_found(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    treasure = world.get("treasure")
    if obstacle.meters["opened"] < THRESHOLD:
        return []
    sig = ("found", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["found"] += 1
    return ["__found__"]


def _r_shared(world: World) -> list[str]:
    treasure = world.get("treasure")
    caller = world.get("caller")
    mate = world.get("mate")
    if treasure.meters["found"] < THRESHOLD or treasure.meters["offered"] < THRESHOLD:
        return []
    sig = ("shared", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["shared"] += 1
    caller.memes["kindness"] += 1
    mate.memes["kindness"] += 1
    caller.memes["joy"] += 1
    mate.memes["joy"] += 1
    mate.memes["dismay"] = 0.0
    return ["__shared__"]


CAUSAL_RULES = [
    Rule(name="dismay", tag="emotion", apply=_r_dismay),
    Rule(name="open", tag="physical", apply=_r_open),
    Rule(name="found", tag="physical", apply=_r_found),
    Rule(name="shared", tag="social", apply=_r_shared),
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
    return produced


def valid_combo(setting: Setting, obstacle: Obstacle, treasure: Treasure) -> bool:
    return obstacle.id in setting.affords and obstacle.requires == "two_kids" and treasure.shareable


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for oid, obstacle in OBSTACLES.items():
            for tid, treasure in TREASURES.items():
                if valid_combo(setting, obstacle, treasure):
                    combos.append((sid, oid, tid))
    return combos


def explain_rejection(setting: Setting, obstacle: Obstacle, treasure: Treasure) -> str:
    if obstacle.id not in setting.affords:
        return (
            f"(No story: {setting.scene} does not honestly contain {obstacle.phrase}, "
            f"so the treasure turn would feel fake. Pick a setting that can host that obstacle.)"
        )
    if obstacle.requires != "two_kids":
        return (
            f"(No story: {obstacle.phrase} does not require teamwork here, but this world is about "
            f"two children solving the problem together.)"
        )
    if not treasure.shareable:
        return (
            f"(No story: {treasure.phrase} is not something the children can really share, "
            f"and sharing is part of this world's ending.)"
        )
    return "(No story: this combination is outside the tiny world.)"


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    sim.get("obstacle").meters["misheard"] += 1
    propagate(sim, narrate=False)
    mate = sim.get("mate")
    return {"dismay": mate.memes["dismay"] >= THRESHOLD}


def play_setup(world: World, caller: Entity, mate: Entity, setting: Setting) -> None:
    for kid in (caller, mate):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {caller.id} and {mate.id} turned the day into {setting.scene}. "
        f"{setting.rig}"
    )
    world.say(
        f'"Captain {caller.id} and First Mate {mate.id}!" {caller.id} cried. '
        f'"Let\'s find {setting.goal}!"'
    )


def glimpse_clue(world: World, caller: Entity, obstacle: Obstacle) -> None:
    caller.memes["excitement"] += 1
    world.say(
        f"Soon {caller.id} spotted the last clue near {obstacle.location_text}. "
        f"The clue pointed straight toward {obstacle.phrase}."
    )


def blurts(world: World, caller: Entity, mate: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"{caller.id} got so excited that {caller.pronoun()} spoke too fast. "
        f'"No, the other one — by the {obstacle.label}! Quick!"'
    )
    world.say(
        f"{mate.id} tried to help, but the words came out in a tumble of pirate hurry."
    )
    world.get("obstacle").meters["misheard"] += 1
    propagate(world, narrate=False)


def wrong_move(world: World, mate: Entity, obstacle: Obstacle) -> None:
    mate.meters["wrong_try"] += 1
    world.say(
        f"{mate.id} did {obstacle.wrong_action} instead. Nothing moved."
    )
    if mate.memes["dismay"] >= THRESHOLD:
        world.say(
            f"A small look of dismay crossed {mate.id}'s face. "
            f'{mate.pronoun().capitalize()} thought {caller_name(world)} was cross, when really the clue had simply been muddled.'
        )


def caller_name(world: World) -> str:
    return world.get("caller").id


def helper_enters(world: World, helper: Entity, helper_cfg: HelperKind) -> None:
    world.say(f"{helper_cfg.entry}")
    world.say(
        f"{helper.label_word.capitalize()} saw both little pirates pause and listened before saying anything."
    )


def paraphrase_help(world: World, helper: Entity, caller: Entity, mate: Entity, obstacle: Obstacle) -> None:
    helper.memes["calm"] += 1
    caller.memes["relief"] += 1
    mate.memes["relief"] += 1
    world.get("obstacle").meters["guided"] += 1
    world.say(
        f'Then {helper.label_word} gave a gentle paraphrase. '
        f'"{caller.id} means {obstacle.correction_text}," {helper.pronoun()} said. '
        f'"And {mate.id}, you look upset because you wanted to help, not make a mistake."'
    )
    world.say(
        f'{helper_cfg_word(world)} {helper.pronoun()} added, '
        f'"You are on the same crew. Try again, side by side."'
    )


def helper_cfg_word(world: World) -> str:
    return world.facts["helper_cfg"].warmth


def teamwork_attempt(world: World, caller: Entity, mate: Entity, obstacle: Obstacle) -> None:
    caller.meters["helped"] += 1
    mate.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {caller.id} and {mate.id} {obstacle.teamwork_text}. "
        f"Their hands worked together this time, not against each other."
    )
    if world.get("obstacle").meters["opened"] >= THRESHOLD:
        world.say(obstacle.opener_text)


def treasure_reveal(world: World, treasure: Treasure) -> None:
    if world.get("treasure").meters["found"] >= THRESHOLD:
        world.say(treasure.reveal_text)


def choose_sharing(world: World, caller: Entity, mate: Entity, treasure: Treasure) -> None:
    world.get("treasure").meters["offered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{caller.id} looked at the treasure, then at {mate.id}, and smiled. "
        f'"A captain does not keep the whole prize," {caller.pronoun()} said.'
    )
    world.say(
        treasure.share_text
    )


def closing(world: World, setting: Setting, treasure: Treasure) -> None:
    world.say(
        f"By the end, the pirate game felt better than before. "
        f"They had found {setting.goal} with kindness, teamwork, and sharing."
    )
    if world.get("treasure").meters["shared"] >= THRESHOLD:
        world.say(
            f"With the shared {treasure.label} between them, the two pirates marched off together, "
            f"grinning like a crew that knew how to listen."
        )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    treasure: Treasure,
    helper_cfg: HelperKind,
    caller_name_value: str = "Nora",
    caller_gender: str = "girl",
    mate_name_value: str = "Tom",
    mate_gender: str = "boy",
) -> World:
    world = World(setting)
    caller = world.add(Entity(
        id=caller_name_value,
        kind="character",
        type=caller_gender,
        role="caller",
        label=caller_name_value,
        traits=["bold"],
    ))
    mate = world.add(Entity(
        id=mate_name_value,
        kind="character",
        type=mate_gender,
        role="mate",
        label=mate_name_value,
        traits=["eager"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label="the grown-up",
        traits=["calm", "kind"],
    ))
    world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
        role="obstacle",
    ))
    world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure.label,
        role="treasure",
    ))
    world.facts.update(
        setting=setting,
        obstacle_cfg=obstacle,
        treasure_cfg=treasure,
        helper_cfg=helper_cfg,
        caller=caller,
        mate=mate,
        helper=helper,
    )

    play_setup(world, caller, mate, setting)
    glimpse_clue(world, caller, obstacle)

    world.para()
    pred = predict_misunderstanding(world)
    world.facts["predicted_dismay"] = pred["dismay"]
    blurts(world, caller, mate, obstacle)
    wrong_move(world, mate, obstacle)

    world.para()
    helper_enters(world, helper, helper_cfg)
    paraphrase_help(world, helper, caller, mate, obstacle)
    teamwork_attempt(world, caller, mate, obstacle)
    treasure_reveal(world, treasure)

    world.para()
    choose_sharing(world, caller, mate, treasure)
    closing(world, setting, treasure)

    world.facts.update(
        misheard=world.get("obstacle").meters["misheard"] >= THRESHOLD,
        felt_dismay=mate.memes["dismay"] < THRESHOLD or True,
        opened=world.get("obstacle").meters["opened"] >= THRESHOLD,
        found=world.get("treasure").meters["found"] >= THRESHOLD,
        shared=world.get("treasure").meters["shared"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "living_room": Setting(
        id="living_room",
        scene="a windy pirate ship in the living room",
        rig="The sofa became the deck, two cushions became waves, and a blanket over the table became a secret cove.",
        goal="the Hidden Hoard",
        obstacle_nook="under the table-cove",
        affords={"rope_knot", "stuck_lid"},
        tags={"pirates", "pretend"},
    ),
    "backyard": Setting(
        id="backyard",
        scene="a pirate cove in the backyard",
        rig="A laundry basket became a boat, a broom became a mast, and the stepping stones became little sea rocks.",
        goal="the Captain's Cache",
        obstacle_nook="beside the flowerpot rocks",
        affords={"high_hook", "rope_knot"},
        tags={"pirates", "yard"},
    ),
    "beach": Setting(
        id="beach",
        scene="a bright pirate beach",
        rig="A striped towel became a sail, a bucket became the chest, and driftwood marked the edge of the treasure cave.",
        goal="the Sandbar Treasure",
        obstacle_nook="near the driftwood cave",
        affords={"high_hook", "stuck_lid"},
        tags={"pirates", "beach"},
    ),
}

OBSTACLES = {
    "rope_knot": Obstacle(
        id="rope_knot",
        label="rope knot",
        phrase="a knotty rope tied around the treasure sack",
        location_text="a post wrapped in rope",
        wrong_action="the wrong loop and tugged it hard",
        correction_text="the blue knot by the post, not the loose loop by the floor",
        teamwork_text="held the rope steady together while one loosened the knot and the other fed the end through",
        opener_text="At last the knot slipped free, and the sack flopped open with a soft pirate thump.",
        requires="two_kids",
        tags={"rope", "teamwork"},
    ),
    "stuck_lid": Obstacle(
        id="stuck_lid",
        label="stuck lid",
        phrase="a treasure chest with a stubborn lid",
        location_text="the old chest by the cove",
        wrong_action="the side handle and pushed where no latch was hidden",
        correction_text="the shell-shaped latch on the front of the chest, then both of you lift together",
        teamwork_text="pressed the latch and lifted the lid together, shoulder to shoulder",
        opener_text="The lid gave a creak, then sprang open as if the chest had been waiting for a proper crew.",
        requires="two_kids",
        tags={"chest", "teamwork"},
    ),
    "high_hook": Obstacle(
        id="high_hook",
        label="high hook",
        phrase="a treasure bag hanging from a high hook",
        location_text="the tall mast-stick",
        wrong_action="the little ring at the bottom and pulled the bag sideways",
        correction_text="the hook up high while one of you steadies the stool and the other lifts the bag down",
        teamwork_text="worked as a pair, one steadying the stool while the other lifted the bag from the hook",
        opener_text="Down came the bag at last, bumping softly into waiting pirate arms.",
        requires="two_kids",
        tags={"hook", "teamwork"},
    ),
}

TREASURES = {
    "gold_chocolate": Treasure(
        id="gold_chocolate",
        label="gold-wrapped chocolates",
        phrase="a pile of gold-wrapped chocolates",
        reveal_text="Inside lay gold-wrapped chocolates that shone like doubloons.",
        share_text="They counted the chocolates into two fair little piles. Because they shared the treasure, both smiles grew bigger than the gold wrappers.",
        shareable=True,
        plural=True,
        tags={"sharing", "food"},
    ),
    "sticker_gems": Treasure(
        id="sticker_gems",
        label="sparkly gem stickers",
        phrase="a sheet of sparkly gem stickers",
        reveal_text="Inside was a sheet of sparkly gem stickers, bright enough to make any pirate blink.",
        share_text="They split the gem stickers carefully, taking turns to choose. Sharing turned the prize into a game of kindness instead of a quarrel.",
        shareable=True,
        plural=True,
        tags={"sharing", "stickers"},
    ),
    "orange_slices": Treasure(
        id="orange_slices",
        label="orange slices",
        phrase="a little tub of orange slices",
        reveal_text="Inside waited cool orange slices, sweet and bright after all that pirate work.",
        share_text="They passed the orange slices back and forth until each pirate had the same number. The snack tasted even better because neither child was left out.",
        shareable=True,
        plural=True,
        tags={"sharing", "food"},
    ),
    "single_medal": Treasure(
        id="single_medal",
        label="one shiny medal",
        phrase="one shiny medal",
        reveal_text="Inside sat one shiny medal on a strip of cloth.",
        share_text="They could look at it together, but one medal is not much of a shared pirate prize.",
        shareable=False,
        plural=False,
        tags={"single"},
    ),
}

HELPERS = {
    "mother": HelperKind(
        id="mother",
        type="mother",
        entry="Mom came over when she heard the pirate voices tangle.",
        warmth="Still smiling,",
        tags={"family"},
    ),
    "father": HelperKind(
        id="father",
        type="father",
        entry="Dad looked over from nearby and walked to the cove with calm steps.",
        warmth="With a warm nod,",
        tags={"family"},
    ),
    "grandmother": HelperKind(
        id="grandmother",
        type="grandmother",
        entry="Grandma set down her basket and joined the pirate deck with a soft laugh.",
        warmth="In her gentle voice,",
        tags={"family"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    treasure: str
    helper: str
    caller: str
    caller_gender: str
    mate: str
    mate_gender: str
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
    "paraphrase": [
        (
            "What does paraphrase mean?",
            "To paraphrase means to say the same idea again in a clearer or simpler way. It can help when people are confused or upset."
        )
    ],
    "dismay": [
        (
            "What is dismay?",
            "Dismay is a feeling of sudden worry or sadness when something goes wrong. A child might feel dismay after a mistake or misunderstanding."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another and do different parts of a job together. Many hard jobs become easier when everyone works as one team."
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing is kind because it lets more than one person enjoy something good. It shows that you care about another person's feelings too."
        )
    ],
    "rope": [
        (
            "Why can two people help with a knot?",
            "One person can hold the rope steady while the other loosens the knot. That keeps the knot from twisting away."
        )
    ],
    "chest": [
        (
            "Why might a chest need two hands to open?",
            "One hand can steady the box while the other lifts or works the latch. That makes the opening safer and easier."
        )
    ],
    "hook": [
        (
            "Why is it helpful for one child to steady something while another reaches?",
            "Steadying keeps the object from wobbling or tipping. Then the reaching child can focus on the careful part."
        )
    ],
    "stickers": [
        (
            "How can children share stickers fairly?",
            "They can take turns picking or split them into matching groups. Taking turns helps everyone feel included."
        )
    ],
    "food": [
        (
            "How can children share a snack fairly?",
            "They can count the pieces and give each person the same number. Fair sharing helps stop hurt feelings before they grow."
        )
    ],
}
KNOWLEDGE_ORDER = ["paraphrase", "dismay", "teamwork", "sharing", "rope", "chest", "hook", "stickers", "food"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    caller = f["caller"]
    mate = f["mate"]
    obstacle = f["obstacle_cfg"]
    treasure = f["treasure_cfg"]
    setting = f["setting"]
    return [
        'Write a short pirate-style story for a 3-to-5-year-old that includes the words "dismay" and "paraphrase".',
        f"Tell a gentle pirate adventure where {caller.id} speaks too quickly, {mate.id} misunderstands, and a kind grown-up uses a paraphrase to help the crew work together.",
        f"Write a treasure-hunt story set in {setting.scene} where children solve {obstacle.phrase}, then share {treasure.label} with kindness and teamwork.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    caller = f["caller"]
    mate = f["mate"]
    helper = f["helper"]
    obstacle = f["obstacle_cfg"]
    treasure = f["treasure_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two pretend pirates, {caller.id} and {mate.id}, and {helper.label_word} who helps them. They are hunting for {setting.goal} together."
        ),
        (
            f"Why did {mate.id} feel dismay?",
            f"{mate.id} felt dismay because {caller.id} gave the clue too quickly, so the directions came out muddled. {mate.pronoun().capitalize()} wanted to help, but the misunderstanding made it seem as if {mate.pronoun()} had done the wrong thing on purpose."
        ),
        (
            "What did the grown-up do to help?",
            f"The grown-up gave a paraphrase and said the clue again in a clearer way. {helper.pronoun().capitalize()} also named the feeling underneath the mix-up, which helped both children settle and listen."
        ),
        (
            "How did the children solve the problem?",
            f"They solved it by working together on {obstacle.phrase}. Once the directions were clear, each child could do one helpful part instead of guessing alone."
        ),
        (
            "How did the story end?",
            f"They found {treasure.label} and shared it fairly. The ending shows that kindness and teamwork made the pirate game happier than grabbing the prize alone."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"paraphrase", "dismay", "teamwork", "sharing"}
    tags |= set(f["obstacle_cfg"].tags)
    tags |= set(f["treasure_cfg"].tags)
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
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="living_room",
        obstacle="stuck_lid",
        treasure="gold_chocolate",
        helper="mother",
        caller="Nora",
        caller_gender="girl",
        mate="Tom",
        mate_gender="boy",
    ),
    StoryParams(
        setting="backyard",
        obstacle="high_hook",
        treasure="sticker_gems",
        helper="father",
        caller="Max",
        caller_gender="boy",
        mate="Lucy",
        mate_gender="girl",
    ),
    StoryParams(
        setting="beach",
        obstacle="stuck_lid",
        treasure="orange_slices",
        helper="grandmother",
        caller="Ava",
        caller_gender="girl",
        mate="Leo",
        mate_gender="boy",
    ),
    StoryParams(
        setting="living_room",
        obstacle="rope_knot",
        treasure="sticker_gems",
        helper="father",
        caller="Finn",
        caller_gender="boy",
        mate="Maya",
        mate_gender="girl",
    ),
]


ASP_RULES = r"""
teamwork_needed(O) :- obstacle(O), requires(O, two_kids).
valid(S, O, T) :- setting(S), obstacle(O), treasure(T), affords(S, O), teamwork_needed(O), shareable(T).

happy_outcome(shared_win) :- chosen_setting(S), chosen_obstacle(O), chosen_treasure(T), chosen_helper(H),
                             valid(S, O, T), helper(H), uses_paraphrase(H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for oid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, oid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("requires", oid, obstacle.requires))
    for tid, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if treasure.shareable:
            lines.append(asp.fact("shareable", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("uses_paraphrase", hid))
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
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_treasure", params.treasure),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show happy_outcome/1."))
    atoms = asp.atoms(model, "happy_outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    if not _check_params(params):
        return "invalid"
    return "shared_win"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate-style misunderstanding healed by paraphrase, teamwork, and sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def _check_params(params: StoryParams) -> bool:
    if params.setting not in SETTINGS:
        return False
    if params.obstacle not in OBSTACLES:
        return False
    if params.treasure not in TREASURES:
        return False
    if params.helper not in HELPERS:
        return False
    return valid_combo(SETTINGS[params.setting], OBSTACLES[params.obstacle], TREASURES[params.treasure])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle and args.treasure:
        setting = SETTINGS[args.setting]
        obstacle = OBSTACLES[args.obstacle]
        treasure = TREASURES[args.treasure]
        if not valid_combo(setting, obstacle, treasure):
            raise StoryError(explain_rejection(setting, obstacle, treasure))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.treasure is None or combo[2] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, treasure_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    caller_gender = rng.choice(["girl", "boy"])
    mate_gender = rng.choice(["girl", "boy"])
    caller = _pick_name(rng, caller_gender)
    mate = _pick_name(rng, mate_gender, avoid=caller)
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        treasure=treasure_id,
        helper=helper_id,
        caller=caller,
        caller_gender=caller_gender,
        mate=mate,
        mate_gender=mate_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.setting]
    obstacle = OBSTACLES[params.obstacle]
    treasure = TREASURES[params.treasure]
    helper_cfg = HELPERS[params.helper]

    if not valid_combo(setting, obstacle, treasure):
        raise StoryError(explain_rejection(setting, obstacle, treasure))

    world = tell(
        setting=setting,
        obstacle=obstacle,
        treasure=treasure,
        helper_cfg=helper_cfg,
        caller_name_value=params.caller,
        caller_gender=params.caller_gender,
        mate_name_value=params.mate,
        mate_gender=params.mate_gender,
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

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params() at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show happy_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, treasure) combos:\n")
        for setting, obstacle, treasure in combos:
            print(f"  {setting:12} {obstacle:10} {treasure}")
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
            header = f"### {p.caller} & {p.mate}: {p.obstacle} in {p.setting} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
