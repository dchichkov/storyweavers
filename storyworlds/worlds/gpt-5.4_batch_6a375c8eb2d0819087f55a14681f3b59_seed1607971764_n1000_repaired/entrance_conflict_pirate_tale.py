#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/entrance_conflict_pirate_tale.py
===========================================================

A standalone story world for a tiny pirate-tale domain: two children build a
pretend pirate mission, but the entrance to their treasure place is blocked by
someone else who wants the same spot for a different game. The conflict can be
solved kindly with sharing, a trade, or teamwork. Unkind moves are known to the
world but refused by the reasonableness gate.

The stories are state-driven: characters have physical meters and emotional
memes, the central conflict changes those states, and the ending image proves
the relationship changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/entrance_conflict_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/entrance_conflict_pirate_tale.py --spot cave --obstacle goose
    python storyworlds/worlds/gpt-5.4/entrance_conflict_pirate_tale.py --resolution shove
    python storyworlds/worlds/gpt-5.4/entrance_conflict_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/entrance_conflict_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/entrance_conflict_pirate_tale.py --trace
    python storyworlds/worlds/gpt-5.4/entrance_conflict_pirate_tale.py --asp
    python storyworlds/worlds/gpt-5.4/entrance_conflict_pirate_tale.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    guarding: bool = False
    shares_space: bool = False
    # world axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"goose", "dog", "parrot", "cat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    scene: str
    props: str
    titles: tuple[str, str]
    goal: str
    voyage: str
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
class Spot:
    id: str
    label: str
    the: str
    entrance: str
    inside: str
    clue: str
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
    kind: str
    label: str
    the: str
    entrance_pose: str
    demand: str
    calming_move: str
    can_share: bool
    movable: bool
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
    sparkle: str
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
class Resolution:
    id: str
    sense: int
    needs_shareable: bool = False
    needs_movable: bool = False
    kind: str = "kind"
    line: str = ""
    act: str = ""
    ending: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_conflict_sting(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mate = world.get("mate")
    blocker = world.get("blocker")
    if blocker.memes["refusal"] >= THRESHOLD and hero.memes["desire"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["frustration"] += 1
            mate.memes["worry"] += 1
            blocker.memes["guard_pride"] += 1
            out.append("__conflict__")
    return out


def _r_kind_peace(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mate = world.get("mate")
    blocker = world.get("blocker")
    if world.facts.get("peace_offer") and blocker.memes["calm"] >= THRESHOLD:
        sig = ("peace",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            mate.memes["joy"] += 1
            blocker.memes["trust"] += 1
            world.get("entrance").meters["open"] = 1.0
            out.append("__peace__")
    return out


CAUSAL_RULES = [
    Rule(name="conflict_sting", tag="social", apply=_r_conflict_sting),
    Rule(name="kind_peace", tag="social", apply=_r_kind_peace),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a windy little island",
        props="The sofa was their ship, a mop became a mast, and a crayon map showed where the treasure might be hiding.",
        titles=("Captain", "First Mate"),
        goal="the treasure before sunset",
        voyage="sailed off grinning, sure that the best pirates were the ones who could share a shore",
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a stormy cove",
        props="A blanket over two chairs made the deck, a cardboard tube was a spyglass, and a drawn map pointed toward secret gold.",
        titles=("Captain", "Lookout"),
        goal="the hidden gold",
        voyage="marched back to their ship with light feet and new friends for the next voyage",
    ),
    "buccaneers": Theme(
        id="buccaneers",
        scene="a brave sea fort",
        props="The rug was the sea, a laundry basket was the boat, and a wrinkled paper map promised treasure nearby.",
        titles=("Captain", "Map Keeper"),
        goal="the buried chest",
        voyage="hurried off laughing, already planning another safe and friendly raid",
    ),
}

SPOTS = {
    "cave": Spot(
        id="cave",
        label="cave",
        the="the cave",
        entrance="the cave entrance under the table",
        inside="the cool cave under the table",
        clue="a dark gap that looked perfect for hiding treasure",
        tags={"cave", "entrance"},
    ),
    "fort": Spot(
        id="fort",
        label="fort",
        the="the fort",
        entrance="the blanket-fort entrance by the couch",
        inside="the shadowy blanket fort",
        clue="a flap of cloth that looked like the mouth of a secret fort",
        tags={"fort", "entrance"},
    ),
    "tunnel": Spot(
        id="tunnel",
        label="tunnel",
        the="the tunnel",
        entrance="the tunnel entrance behind the curtains",
        inside="the dim tunnel behind the curtains",
        clue="a narrow opening that felt like the start of a pirate tunnel",
        tags={"tunnel", "entrance"},
    ),
}

OBSTACLES = {
    "goose": Obstacle(
        id="goose",
        kind="animal",
        label="goose",
        the="the goose",
        entrance_pose="stood at the entrance with its wings out wide and a loud, bossy honk",
        demand="It had decided that the best shady spot belonged to it alone.",
        calming_move="a soft trail of oat crackers",
        can_share=False,
        movable=True,
        tags={"goose", "animal"},
    ),
    "sibling": Obstacle(
        id="sibling",
        kind="child",
        label="older child",
        the="the older child",
        entrance_pose="sat across the entrance with folded arms and a captainly frown",
        demand='\"This is my fort now,\" the older child said.',
        calming_move="a fair turn with the shiny spyglass",
        can_share=True,
        movable=True,
        tags={"sharing", "turn_taking"},
    ),
    "dog": Obstacle(
        id="dog",
        kind="animal",
        label="sleepy dog",
        the="the sleepy dog",
        entrance_pose="curled in a furry ball right across the entrance",
        demand="It had found the coziest spot in the room and did not want to move.",
        calming_move="a squeaky rope toy tossed a little way away",
        can_share=False,
        movable=True,
        tags={"dog", "animal"},
    ),
    "keeper": Obstacle(
        id="keeper",
        kind="child",
        label="yard keeper",
        the="the yard keeper",
        entrance_pose="stood by the entrance clutching a box of shells like a stern guard",
        demand='\"No one comes in unless they help sort the shells,\" the keeper said.',
        calming_move="helping sort the shells together",
        can_share=True,
        movable=False,
        tags={"sharing", "helping"},
    ),
}

PRIZES = {
    "chest": Prize(
        id="chest",
        label="treasure chest",
        phrase="a shoebox treasure chest",
        sparkle="gold paper coins and blue glass pebbles",
        tags={"treasure"},
    ),
    "pearl": Prize(
        id="pearl",
        label="pearl jar",
        phrase="a jar of pretend pearls",
        sparkle="white beads that shone like moon-drops",
        tags={"treasure"},
    ),
    "crown": Prize(
        id="crown",
        label="crown",
        phrase="a tin-foil crown",
        sparkle="silver points that winked in the light",
        tags={"treasure"},
    ),
}

RESOLUTIONS = {
    "share_map": Resolution(
        id="share_map",
        sense=3,
        needs_shareable=True,
        kind="kind",
        line="What if we look together and split the treasure the pirate way?",
        act="offered to share the map and count the treasure together",
        ending="Soon all three were crouched inside, whispering over the map and taking turns finding the glittering prize.",
        qa_text="They solved the problem by sharing the pirate game and the treasure hunt.",
        tags={"sharing", "friendship"},
    ),
    "trade_tool": Resolution(
        id="trade_tool",
        sense=3,
        needs_movable=True,
        kind="kind",
        line="What if you use this special pirate tool, and we go through the entrance?",
        act="offered a fun trade instead of arguing",
        ending="The blocker happily took the offered toy, and the entrance opened as if the whole room had let out a breath.",
        qa_text="They solved the problem by making a fair trade.",
        tags={"trade", "friendship"},
    ),
    "help_task": Resolution(
        id="help_task",
        sense=3,
        needs_shareable=True,
        kind="kind",
        line="We can help first, and then can we all go in?",
        act="stopped to help with the little job at the entrance",
        ending="The work was finished together, and then the hidden place felt bigger and friendlier than before.",
        qa_text="They solved the problem by helping first and then entering together.",
        tags={"helping", "friendship"},
    ),
    "wait_turn": Resolution(
        id="wait_turn",
        sense=2,
        needs_shareable=True,
        kind="patient",
        line="All right. We can wait for our turn and guard the outside.",
        act="chose patience and a fair turn",
        ending="When their turn came, they entered with calm hearts, and no one was cross anymore.",
        qa_text="They solved the problem by waiting for a fair turn.",
        tags={"turn_taking", "patience"},
    ),
    "shove": Resolution(
        id="shove",
        sense=1,
        kind="unkind",
        line="Move! Pirates first!",
        act="tried to force the way open",
        ending="No cheerful story ends well after shoving at the entrance.",
        qa_text="They tried to force the entrance open by shoving.",
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "bright", "curious", "steady", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    theme: str = "pirates"
    spot: str = "cave"
    obstacle: str = "sibling"
    prize: str = "chest"
    resolution: str = "share_map"
    hero_name: str = "Tom"
    hero_gender: str = "boy"
    mate_name: str = "Lily"
    mate_gender: str = "girl"
    parent: str = "mother"
    trait: str = "careful"
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


def obstacle_allows(obstacle: Obstacle, resolution: Resolution) -> bool:
    if resolution.sense < SENSE_MIN:
        return False
    if resolution.needs_shareable and not obstacle.can_share:
        return False
    if resolution.needs_movable and not obstacle.movable:
        return False
    if resolution.id == "help_task" and obstacle.id != "keeper":
        return False
    if resolution.id == "wait_turn" and not obstacle.can_share:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for spot_id in SPOTS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for resolution_id, resolution in RESOLUTIONS.items():
                    if obstacle_allows(obstacle, resolution):
                        combos.append((theme_id, spot_id, obstacle_id, resolution_id))
    return combos


def explain_rejection(obstacle: Obstacle, resolution: Resolution) -> str:
    if resolution.sense < SENSE_MIN:
        return (
            f"(Refusing resolution '{resolution.id}': it is too unkind for this story world. "
            f"Pirate quarrels here must be solved with a fairer move.)"
        )
    if resolution.needs_shareable and not obstacle.can_share:
        return (
            f"(No story: {obstacle.the} cannot really share the entrance, so "
            f"'{resolution.id}' does not fit. Try a trade or a movable obstacle.)"
        )
    if resolution.needs_movable and not obstacle.movable:
        return (
            f"(No story: {obstacle.the} is not the sort of blocker that can be moved by a trade. "
            f"Try sharing or helping instead.)"
        )
    if resolution.id == "help_task" and obstacle.id != "keeper":
        return "(No story: there is no little job to help with at this entrance.)"
    return "(No story: that obstacle and resolution do not make a reasonable conflict.)"


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= SENSE_MIN]


def predict_conflict(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    blocker = sim.get("blocker")
    hero.memes["desire"] += 1
    blocker.memes["refusal"] += 1
    propagate(sim, narrate=False)
    return {
        "frustration": hero.memes["frustration"],
        "worry": sim.get("mate").memes["worry"],
    }


def setup_play(world: World, theme: Theme, hero: Entity, mate: Entity, prize: Prize, spot: Spot) -> None:
    captain_title, mate_title = theme.titles
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {mate.id} turned the room into {theme.scene}. "
        f"{theme.props}"
    )
    world.say(
        f'Today {hero.id} was {captain_title} {hero.id}, and {mate.id} was {mate_title} {mate.id}. '
        f'They were hunting {theme.goal}, and their map pointed straight toward {spot.entrance}.'
    )
    world.say(
        f"In the middle of their game, they tucked {prize.phrase} under the table and decided it held "
        f"{prize.sparkle}."
    )


def find_entrance(world: World, hero: Entity, mate: Entity, spot: Spot) -> None:
    world.say(
        f"At last they reached {spot.entrance}. It was {spot.clue}, and both children knew at once "
        f"that this must be the entrance to their secret pirate place."
    )
    world.say(
        f'"There it is!" {hero.id} whispered. "{spot.The if hasattr(spot, "The") else spot.the.capitalize()} entrance!"'
    )


def block_entrance(world: World, blocker: Entity, obstacle: Obstacle, hero: Entity, mate: Entity) -> None:
    hero.memes["desire"] += 1
    blocker.memes["refusal"] += 1
    world.get("entrance").meters["open"] = 0.0
    propagate(world, narrate=False)
    if obstacle.kind == "child":
        world.say(
            f"But {obstacle.the} {obstacle.entrance_pose} {obstacle.demand}"
        )
    else:
        world.say(
            f"But {obstacle.the} {obstacle.entrance_pose} {obstacle.demand}"
        )
    if hero.memes["frustration"] >= THRESHOLD:
        world.say(
            f"{hero.id} stopped so fast that the map crinkled in {hero.pronoun('possessive')} hands. "
            f"{mate.id} looked from the blocked entrance to {hero.id} and felt a little worried."
        )


def warn_against_force(world: World, mate: Entity, hero: Entity, blocker: Entity) -> None:
    pred = predict_conflict(world)
    world.facts["predicted_frustration"] = pred["frustration"]
    world.facts["predicted_worry"] = pred["worry"]
    mate.memes["care"] += 1
    world.say(
        f'{mate.id} touched {hero.id}\'s sleeve. "If we shout or push, the whole game will turn sour," '
        f'{mate.pronoun()} said. "Let\'s think like clever pirates instead."'
    )


def propose_fix(world: World, hero: Entity, mate: Entity, blocker: Entity,
                obstacle: Obstacle, resolution: Resolution) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"{hero.id} took a slow breath. Then {hero.pronoun()} looked at {blocker.label} and said, "
        f'"{resolution.line}"'
    )
    if resolution.id == "trade_tool":
        tool = world.facts.get("trade_item", "spyglass")
        world.say(
            f"{mate.id} held out the {tool}, shiny and tempting in the light."
        )
    elif resolution.id == "help_task":
        world.say(
            f"Right away, the two young pirates knelt beside the shells instead of trying to rush past."
        )
    elif resolution.id == "share_map":
        world.say(
            f"{mate.id} spread the map open so everyone could see the crooked treasure mark."
        )
    elif resolution.id == "wait_turn":
        world.say(
            f"{mate.id} nodded and sat beside the entrance so the waiting felt fair instead of lonely."
        )
    world.facts["peace_offer"] = resolution.id


def resolve_peace(world: World, blocker: Entity, obstacle: Obstacle, resolution: Resolution) -> None:
    blocker.memes["calm"] += 1
    if resolution.id == "share_map":
        blocker.memes["belonging"] += 1
        world.say(
            f"{obstacle.The} blinked, then scooted aside. A shared treasure hunt sounded better than a lonely guard."
        )
    elif resolution.id == "trade_tool":
        blocker.memes["interest"] += 1
        trade_item = world.facts.get("trade_item", "spyglass")
        world.say(
            f"{obstacle.The} brightened at the sight of the {trade_item} and moved away from the entrance."
        )
    elif resolution.id == "help_task":
        blocker.memes["trust"] += 1
        world.say(
            f"{obstacle.The} watched them help for a moment, and then the stern look melted. "
            f'"All right," the keeper said. "You may come in too."'
        )
    elif resolution.id == "wait_turn":
        blocker.memes["trust"] += 1
        world.say(
            f"{obstacle.The} saw that nobody was trying to grab the place away. After a short while, the blocker smiled and waved them in."
        )
    propagate(world, narrate=False)
    world.facts["opened_by"] = resolution.id


def enter_and_find(world: World, hero: Entity, mate: Entity, blocker: Entity,
                   spot: Spot, prize: Prize, resolution: Resolution) -> None:
    hero.meters["inside"] += 1
    mate.meters["inside"] += 1
    blocker.meters["inside"] += 1
    hero.memes["wonder"] += 1
    mate.memes["wonder"] += 1
    world.say(
        f"They ducked through the entrance together and reached {spot.inside}. In the dim little space, "
        f"their hands found {prize.phrase}, and inside it lay {prize.sparkle}."
    )
    world.say(resolution.ending)
    world.say(
        f"When the game was done, the treasure mattered less than the new feeling at the entrance: "
        f"it was not a place to fight over anymore, but a place friends could open together."
    )


def tell(theme: Theme, spot: Spot, obstacle: Obstacle, prize: Prize, resolution: Resolution,
         hero_name: str = "Tom", hero_gender: str = "boy",
         mate_name: str = "Lily", mate_gender: str = "girl",
         parent_type: str = "mother", trait: str = "careful") -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="captain",
        traits=["bold"],
        attrs={"name": hero_name},
    ))
    mate = world.add(Entity(
        id="mate",
        kind="character",
        type=mate_gender,
        label=mate_name,
        role="mate",
        traits=[trait],
        attrs={"name": mate_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    blocker_type = {
        "animal": obstacle.id,
        "child": "girl" if mate_gender == "girl" else "boy",
    }[obstacle.kind]
    blocker_name = {
        "goose": "Gus",
        "dog": "Moss",
        "sibling": "Nell" if blocker_type == "girl" else "Ned",
        "keeper": "Pearl" if blocker_type == "girl" else "Pip",
    }[obstacle.id]
    blocker = world.add(Entity(
        id="blocker",
        kind="character" if obstacle.kind == "child" else "thing",
        type=blocker_type,
        label=blocker_name if obstacle.kind == "child" else obstacle.label,
        role="blocker",
        attrs={"display": blocker_name},
        movable=obstacle.movable,
        guarding=True,
        shares_space=obstacle.can_share,
    ))
    entrance = world.add(Entity(
        id="entrance",
        kind="thing",
        type="entrance",
        label=spot.entrance,
        role="entrance",
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="prize",
        label=prize.label,
        role="prize",
    ))

    # Initialize rule-read states before any propagate().
    hero.memes["desire"] = 0.0
    hero.memes["frustration"] = 0.0
    mate.memes["worry"] = 0.0
    blocker.memes["refusal"] = 0.0
    blocker.memes["calm"] = 0.0
    entrance.meters["open"] = 1.0
    world.facts["peace_offer"] = ""
    world.facts["trade_item"] = random.choice(["spyglass", "captain's hat", "rope ring"])
    world.facts["hero_name"] = hero_name
    world.facts["mate_name"] = mate_name
    world.facts["blocker_name"] = blocker_name if obstacle.kind == "child" else obstacle.label

    named_hero = hero.label
    named_mate = mate.label

    setup_play(world, theme, Entity(id=named_hero, type=hero.type, label=named_hero, role=hero.role, attrs=hero.attrs),
               Entity(id=named_mate, type=mate.type, label=named_mate, role=mate.role, attrs=mate.attrs),
               prize, spot)
    find_entrance(world, Entity(id=named_hero, type=hero.type, label=named_hero, role=hero.role, attrs=hero.attrs),
                  Entity(id=named_mate, type=mate.type, label=named_mate, role=mate.role, attrs=mate.attrs), spot)

    world.para()
    # Use temporary named wrappers for prose while world state stays on canonical ids.
    block_entrance(world, blocker, obstacle,
                   Entity(id=named_hero, type=hero.type, label=named_hero, role=hero.role, attrs=hero.attrs, memes=hero.memes),
                   Entity(id=named_mate, type=mate.type, label=named_mate, role=mate.role, attrs=mate.attrs, memes=mate.memes))
    warn_against_force(world,
                       Entity(id=named_mate, type=mate.type, label=named_mate, role=mate.role, attrs=mate.attrs, memes=mate.memes),
                       Entity(id=named_hero, type=hero.type, label=named_hero, role=hero.role, attrs=hero.attrs, memes=hero.memes),
                       blocker)

    world.para()
    propose_fix(world,
                Entity(id=named_hero, type=hero.type, label=named_hero, role=hero.role, attrs=hero.attrs, memes=hero.memes),
                Entity(id=named_mate, type=mate.type, label=named_mate, role=mate.role, attrs=mate.attrs, memes=mate.memes),
                blocker, obstacle, resolution)
    resolve_peace(world, blocker, obstacle, resolution)
    enter_and_find(world,
                   Entity(id=named_hero, type=hero.type, label=named_hero, role=hero.role, attrs=hero.attrs, memes=hero.memes, meters=hero.meters),
                   Entity(id=named_mate, type=mate.type, label=named_mate, role=mate.role, attrs=mate.attrs, memes=mate.memes, meters=mate.meters),
                   blocker, spot, prize, resolution)

    hero.memes["lesson"] += 1
    mate.memes["lesson"] += 1

    world.facts.update(
        theme=theme,
        spot=spot,
        obstacle_cfg=obstacle,
        prize_cfg=prize,
        resolution_cfg=resolution,
        hero=hero,
        mate=mate,
        blocker=blocker,
        parent=parent,
        entrance=entrance,
        treasure=treasure,
        success=entrance.meters["open"] >= THRESHOLD,
        conflict=hero.memes["frustration"] >= THRESHOLD,
    )
    world.facts["display_names"] = {
        "hero": named_hero,
        "mate": named_mate,
        "blocker": blocker_name if obstacle.kind == "child" else obstacle.label,
    }
    return world


KNOWLEDGE = {
    "entrance": [(
        "What is an entrance?",
        "An entrance is the way into a place. It is the opening you go through to get inside."
    )],
    "sharing": [(
        "What does sharing mean?",
        "Sharing means letting someone else enjoy something too. It helps a game feel fair and friendly."
    )],
    "turn_taking": [(
        "What is taking turns?",
        "Taking turns means one person goes first and another person goes next. It is a fair way to solve many small conflicts."
    )],
    "friendship": [(
        "How can a conflict turn into friendship?",
        "A conflict can soften when people stop pushing and start listening. Kind offers, fair turns, or helping can make everyone feel safer."
    )],
    "trade": [(
        "What is a fair trade?",
        "A fair trade is when two people swap things in a way that feels balanced to both of them. No one should feel tricked or left out."
    )],
    "helping": [(
        "Why does helping often calm a quarrel?",
        "Helping shows that you care about the other person's problem. That can make them trust you more and feel less cross."
    )],
    "goose": [(
        "Why might a goose block your way?",
        "A goose may spread its wings or honk if it wants to guard its space. Animals do not understand games the way children do."
    )],
    "dog": [(
        "Why do dogs like cozy spots?",
        "Dogs often curl up in soft or shady places because they feel safe and comfortable there. A sleepy dog may not want to move right away."
    )],
    "treasure": [(
        "What is treasure in a pirate story?",
        "Treasure is something special pirates hope to find, like coins, jewels, or shiny things. In a pretend game, treasure can be any object that feels magical."
    )],
}
KNOWLEDGE_ORDER = ["entrance", "sharing", "turn_taking", "friendship", "trade", "helping", "goose", "dog", "treasure"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    names = f["display_names"]
    theme = f["theme"]
    spot = f["spot"]
    obstacle = f["obstacle_cfg"]
    resolution = f["resolution_cfg"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the word "entrance" and centers on a conflict at {spot.entrance}.',
        f"Tell a gentle story where {names['hero']} and {names['mate']} reach a pirate entrance, meet {obstacle.the}, and solve the problem by being kind instead of pushy.",
        f"Write a complete little adventure where the treasure matters less than the way the children settle the quarrel, ending with {resolution.kind} peace and a shared pirate game.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    names = f["display_names"]
    spot = f["spot"]
    obstacle = f["obstacle_cfg"]
    resolution = f["resolution_cfg"]
    prize = f["prize_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {names['hero']} and {names['mate']}, two children playing pirates, and {names['blocker']} at the entrance. They all matter because the treasure hunt cannot continue until the conflict is settled."
        ),
        (
            "What was the problem at the entrance?",
            f"The children found {spot.entrance}, but {obstacle.the} was blocking the way. That stopped the pirate game right at the moment when they thought they were about to reach the treasure."
        ),
        (
            f"Why did the conflict feel important?",
            f"It felt important because the blocked entrance stood between the children and {prize.label}. It also threatened to spoil the whole game by turning excitement into cross feelings."
        ),
    ]
    if f.get("conflict"):
        qa.append((
            f"Why did {names['mate']} warn against pushing or shouting?",
            f"{names['mate']} could see that everyone was already getting upset. Pushing would have made the blocked entrance into a bigger quarrel instead of opening it."
        ))
    qa.append((
        "How did they solve the problem?",
        f"{resolution.qa_text} Because they chose a fair move, the blocker calmed down and the entrance opened without anyone being hurt or left out."
    ))
    qa.append((
        "How did the story end?",
        f"They went through the entrance together and found {prize.phrase} full of {prize.sparkle}. The ending shows that the biggest change was not only finding treasure, but turning a quarrel into a shared adventure."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["spot"].tags) | set(f["prize_cfg"].tags) | set(f["resolution_cfg"].tags) | set(f["obstacle_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        flags = [name for name, on in (("movable", e.movable), ("guarding", e.guarding), ("shares_space", e.shares_space)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% reasonableness gate
sensible_resolution(R) :- resolution(R), sense(R,S), sense_min(M), S >= M.
valid(T,S,O,R) :- theme(T), spot(S), obstacle(O), resolution(R),
                  sensible_resolution(R),
                  not needs_shareable(R), not needs_movable(R), not help_only(R).
valid(T,S,O,R) :- theme(T), spot(S), obstacle(O), resolution(R),
                  sensible_resolution(R), needs_shareable(R), shareable(O),
                  not needs_movable(R), not help_only(R).
valid(T,S,O,R) :- theme(T), spot(S), obstacle(O), resolution(R),
                  sensible_resolution(R), needs_movable(R), movable(O),
                  not needs_shareable(R), not help_only(R).
valid(T,S,O,R) :- theme(T), spot(S), obstacle(O), resolution(R),
                  sensible_resolution(R), needs_shareable(R), shareable(O),
                  needs_movable(R), movable(O),
                  not help_only(R).
valid(T,S,O,R) :- theme(T), spot(S), obstacle(O), resolution(help_task),
                  sensible_resolution(help_task), help_only(help_task), job_obstacle(O).

% simple outcome model for this world: valid combos always resolve peacefully
outcome(peaceful) :- chosen_theme(T), chosen_spot(S), chosen_obstacle(O), chosen_resolution(R), valid(T,S,O,R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid in SPOTS:
        lines.append(asp.fact("spot", sid))
    for oid, o in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        if o.can_share:
            lines.append(asp.fact("shareable", oid))
        if o.movable:
            lines.append(asp.fact("movable", oid))
        if oid == "keeper":
            lines.append(asp.fact("job_obstacle", oid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        if r.needs_shareable:
            lines.append(asp.fact("needs_shareable", rid))
        if r.needs_movable:
            lines.append(asp.fact("needs_movable", rid))
        if rid == "help_task":
            lines.append(asp.fact("help_only", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    # smoke test ordinary story generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    # parity over curated + seeded random resolutions
    cases = list(CURATED)
    parser = build_parser()
    for s in range(25):
        rng = random.Random(s)
        try:
            params = resolve_params(parser.parse_args([]), rng)
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break
    for params in cases:
        extra = "\n".join([
            f"chosen_theme({params.theme}).",
            f"chosen_spot({params.spot}).",
            f"chosen_obstacle({params.obstacle}).",
            f"chosen_resolution({params.resolution}).",
        ])
        import asp
        model = asp.one_model(asp_program(extra, "#show outcome/1."))
        atoms = asp.atoms(model, "outcome")
        asp_outcome = atoms[0][0] if atoms else "?"
        py_outcome = "peaceful" if (params.theme, params.spot, params.obstacle, params.resolution) in py else "?"
        if asp_outcome != py_outcome:
            rc = 1
            print("MISMATCH outcome:", params, asp_outcome, py_outcome)
            break
    if rc == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    return rc


CURATED = [
    StoryParams(
        theme="pirates",
        spot="cave",
        obstacle="sibling",
        prize="chest",
        resolution="share_map",
        hero_name="Tom",
        hero_gender="boy",
        mate_name="Lily",
        mate_gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        theme="corsairs",
        spot="fort",
        obstacle="dog",
        prize="pearl",
        resolution="trade_tool",
        hero_name="Mia",
        hero_gender="girl",
        mate_name="Ben",
        mate_gender="boy",
        parent="father",
        trait="gentle",
    ),
    StoryParams(
        theme="buccaneers",
        spot="tunnel",
        obstacle="keeper",
        prize="crown",
        resolution="help_task",
        hero_name="Max",
        hero_gender="boy",
        mate_name="Zoe",
        mate_gender="girl",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        theme="pirates",
        spot="fort",
        obstacle="sibling",
        prize="pearl",
        resolution="wait_turn",
        hero_name="Ella",
        hero_gender="girl",
        mate_name="Noah",
        mate_gender="boy",
        parent="father",
        trait="steady",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate game, a blocked entrance, and a kind solution."
    )
    ap.add_argument("--theme", choices=sorted(THEMES))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--resolution", choices=sorted(RESOLUTIONS))
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.resolution:
        obstacle = OBSTACLES[args.obstacle]
        resolution = RESOLUTIONS[args.resolution]
        if not obstacle_allows(obstacle, resolution):
            raise StoryError(explain_rejection(obstacle, resolution))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.spot is None or combo[1] == args.spot)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.resolution is None or combo[3] == args.resolution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, spot_id, obstacle_id, resolution_id = rng.choice(sorted(combos))
    prize_id = args.prize or rng.choice(sorted(PRIZES))
    hero_name, hero_gender = _pick_name(rng)
    mate_name, mate_gender = _pick_name(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        theme=theme_id,
        spot=spot_id,
        obstacle=obstacle_id,
        prize=prize_id,
        resolution=resolution_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"Unknown theme: {params.theme}")
    if params.spot not in SPOTS:
        raise StoryError(f"Unknown spot: {params.spot}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.prize not in PRIZES:
        raise StoryError(f"Unknown prize: {params.prize}")
    if params.resolution not in RESOLUTIONS:
        raise StoryError(f"Unknown resolution: {params.resolution}")

    obstacle = OBSTACLES[params.obstacle]
    resolution = RESOLUTIONS[params.resolution]
    if not obstacle_allows(obstacle, resolution):
        raise StoryError(explain_rejection(obstacle, resolution))

    seed_value = 0 if params.seed is None else params.seed
    saved_state = random.getstate()
    random.seed(seed_value)
    try:
        world = tell(
            theme=THEMES[params.theme],
            spot=SPOTS[params.spot],
            obstacle=obstacle,
            prize=PRIZES[params.prize],
            resolution=resolution,
            hero_name=params.hero_name,
            hero_gender=params.hero_gender,
            mate_name=params.mate_name,
            mate_gender=params.mate_gender,
            parent_type=params.parent,
            trait=params.trait,
        )
    finally:
        random.setstate(saved_state)

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
        print(f"{len(combos)} compatible (theme, spot, obstacle, resolution) combos:\n")
        for theme_id, spot_id, obstacle_id, resolution_id in combos:
            print(f"  {theme_id:10} {spot_id:8} {obstacle_id:8} {resolution_id}")
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
            header = f"### {p.hero_name} & {p.mate_name}: {p.obstacle} at {p.spot} ({p.resolution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
