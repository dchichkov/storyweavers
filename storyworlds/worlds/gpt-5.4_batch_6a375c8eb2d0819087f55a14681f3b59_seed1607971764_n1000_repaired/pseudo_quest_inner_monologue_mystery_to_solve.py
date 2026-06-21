#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pseudo_quest_inner_monologue_mystery_to_solve.py
============================================================================

A standalone story world for a tiny pirate-flavored mystery quest.

Premise
-------
Two children turn a room into a pirate adventure, but the tiny "pseudo pearl"
they need for their pretend treasure chest has gone missing. The lead child
follows real clues, thinks quietly to themself, and solves the mystery in a
way that fits what the world state allows.

This world is deliberately small and constrained:
- a cause can only hide the pearl in spots it could really reach,
- the clue method must match the cause,
- a high place needs grown-up help,
- invalid explicit choices are rejected with a clear reason.

Run it
------
    python storyworlds/worlds/gpt-5.4/pseudo_quest_inner_monologue_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/pseudo_quest_inner_monologue_mystery_to_solve.py --cause puppy --spot high_shelf
    python storyworlds/worlds/gpt-5.4/pseudo_quest_inner_monologue_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/pseudo_quest_inner_monologue_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4/pseudo_quest_inner_monologue_mystery_to_solve.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        animal = {"puppy", "dog", "kitten", "cat"}
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
    rig: str
    titles: tuple[str, str]
    goal: str
    ending: str
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
class Cause:
    id: str
    actor_type: str
    actor_label: str
    access: set[str]
    clue_kind: str
    sign_text: str
    think_text: str
    carry_style: str
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
class Spot:
    id: str
    label: str
    phrase: str
    height: str
    reveal_text: str
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
class Method:
    id: str
    clue_kind: str
    sense: int
    text: str
    qa_text: str
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
class HelperMove:
    id: str
    sense: int
    handles: set[str]
    text: str
    qa_text: str
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


def _r_hidden_tension(world: World) -> list[str]:
    pearl = world.get("pearl")
    seeker = world.get("seeker")
    mate = world.get("mate")
    if pearl.meters["hidden"] < THRESHOLD:
        return []
    sig = ("hidden_tension",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["worry"] += 1
    mate.memes["worry"] += 1
    world.get("room").meters["mystery"] += 1
    return []


def _r_clue_resolve(world: World) -> list[str]:
    seeker = world.get("seeker")
    if seeker.meters["clue"] < THRESHOLD:
        return []
    sig = ("clue_resolve",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["resolve"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    pearl = world.get("pearl")
    if pearl.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("seeker", "mate"):
        world.get(eid).memes["worry"] = 0.0
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["joy"] += 1
    world.get("room").meters["mystery"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="hidden_tension", tag="mystery", apply=_r_hidden_tension),
    Rule(name="clue_resolve", tag="mystery", apply=_r_clue_resolve),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def cause_can_reach(cause: Cause, spot: Spot) -> bool:
    return spot.id in cause.access


def method_matches(cause: Cause, method: Method) -> bool:
    return cause.clue_kind == method.clue_kind


def helper_needed(spot: Spot) -> str:
    return "high" if spot.height == "high" else "low"


def sensible_helpers() -> list[HelperMove]:
    return [m for m in HELPERS.values() if m.sense >= SENSE_MIN]


def helper_handles(spot: Spot, helper: HelperMove) -> bool:
    return helper_needed(spot) in helper.handles


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for cause_id, cause in CAUSES.items():
            for spot_id, spot in SPOTS.items():
                if not cause_can_reach(cause, spot):
                    continue
                for method_id, method in METHODS.items():
                    if method_matches(cause, method):
                        combos.append((theme_id, cause_id, spot_id, method_id))
    return combos


def explain_cause_spot(cause: Cause, spot: Spot) -> str:
    return (
        f"(No story: {cause.actor_label} could not reasonably carry the pseudo pearl "
        f"to {spot.phrase}. Pick a spot that {cause.actor_label} can reach.)"
    )


def explain_method(cause: Cause, method: Method) -> str:
    return (
        f"(No story: '{method.id}' does not fit the clue this mystery leaves behind. "
        f"For {cause.actor_label}, use a method that follows {cause.clue_kind} clues.)"
    )


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    better = ", ".join(sorted(h.id for h in sensible_helpers()))
    return (
        f"(Refusing helper move '{helper_id}': it scores too low on common sense "
        f"(sense={helper.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def explain_helper_fit(helper: HelperMove, spot: Spot) -> str:
    needed = helper_needed(spot)
    return (
        f"(No story: '{helper.id}' cannot handle a {spot.height} hiding place. "
        f"This search needs a helper move for {needed} places.)"
    )


def predict_spot(world: World, cause: Cause, spot: Spot, method: Method) -> dict:
    sim = world.copy()
    pearl = sim.get("pearl")
    seeker = sim.get("seeker")
    pearl.meters["hidden"] += 1
    sim.facts["cause"] = cause
    sim.facts["spot"] = spot
    propagate(sim, narrate=False)
    if method_matches(cause, method):
        seeker.meters["clue"] += 1
        propagate(sim, narrate=False)
    return {
        "mystery": sim.get("room").meters["mystery"],
        "resolve": seeker.memes["resolve"],
    }


def play_setup(world: World, seeker: Entity, mate: Entity, theme: Theme) -> None:
    seeker.memes["joy"] += 1
    mate.memes["joy"] += 1
    cap, scout = theme.titles
    world.say(
        f"On a bright afternoon, {seeker.id} and {mate.id} turned the room into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{cap} {seeker.id} and {scout} {mate.id}!" {seeker.id} said. '
        f'"Today we finish {theme.goal}."'
    )


def need_pearl(world: World, seeker: Entity, mate: Entity) -> None:
    world.say(
        f"They had one last thing to do before the pretend treasure chest could open: "
        f"fit the tiny pseudo pearl into the little star-shaped hole on its lid."
    )
    world.say(
        f'But when {mate.id} reached for it, the pearl was gone.'
    )


def discover_mystery(world: World, seeker: Entity, mate: Entity, cause_actor: Entity) -> None:
    pearl = world.get("pearl")
    pearl.meters["hidden"] += 1
    cause_actor.meters["moved_item"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"It was right here," {mate.id} whispered. Suddenly the whole room felt hush-hush and important.'
    )
    world.say(
        f"{seeker.id} looked at the chest, then at the floor, and felt the quest turn into a mystery."
    )


def first_clue(world: World, seeker: Entity, cause: Cause) -> None:
    seeker.meters["clue"] += 1
    propagate(world, narrate=False)
    world.say(cause.sign_text)
    world.say(
        f'{seeker.id} thought, "{cause.think_text}"'
    )


def choose_method(world: World, seeker: Entity, method: Method, spot: Spot) -> None:
    pred = predict_spot(world, world.facts["cause"], spot, method)
    world.facts["predicted_mystery"] = pred["mystery"]
    world.facts["predicted_resolve"] = pred["resolve"]
    seeker.memes["focus"] += 1
    world.say(
        f"{method.text}."
    )


def search_low(world: World, seeker: Entity, mate: Entity, spot: Spot, helper: HelperMove) -> None:
    world.say(
        f"{seeker.id} and {mate.id} went on tiptoe-quiet pirate feet, while {helper.text}."
    )
    world.say(spot.reveal_text)


def search_high(world: World, seeker: Entity, mate: Entity, parent: Entity, spot: Spot, helper: HelperMove) -> None:
    world.say(
        f"{seeker.id} stared up at {spot.phrase}. It was too high for pirate fingers."
    )
    world.say(
        f"So they hurried to {parent.label_word} and {helper.text}."
    )
    world.say(spot.reveal_text)


def find_pearl(world: World, seeker: Entity, mate: Entity, pearl: Entity, cause_actor: Entity, spot: Spot) -> None:
    pearl.meters["hidden"] = 0.0
    pearl.meters["found"] += 1
    propagate(world, narrate=False)
    seeker.memes["pride"] += 1
    mate.memes["admiration"] += 1
    world.say(
        f"There was the pseudo pearl at last, tucked in {spot.phrase}. {cause_actor.label.capitalize()} had left the mystery behind without meaning to."
    )
    world.say(
        f'{mate.id} laughed with relief. "{seeker.id}, you solved it!"'
    )


def lesson_and_end(world: World, seeker: Entity, mate: Entity, parent: Entity, theme: Theme) -> None:
    seeker.memes["care"] += 1
    mate.memes["care"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled and set a tiny shell bowl beside the chest. "
        f'"Treasure pieces need a home when the game pauses," {parent.pronoun()} said.'
    )
    world.say(
        f"{seeker.id} placed the pearl in the bowl until the next clue was ready. Then the pearl clicked into the lid, the chest popped open, and {theme.ending}"
    )


def tell(
    theme: Theme,
    cause: Cause,
    spot: Spot,
    method: Method,
    helper: HelperMove,
    seeker_name: str = "Lily",
    seeker_gender: str = "girl",
    mate_name: str = "Tom",
    mate_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    seeker = world.add(Entity(id="seeker", kind="character", type=seeker_gender, label=seeker_name, role="seeker"))
    mate = world.add(Entity(id="mate", kind="character", type=mate_gender, label=mate_name, role="mate"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    cause_actor = world.add(Entity(id="cause_actor", kind="character", type=cause.actor_type, label=cause.actor_label, role="cause"))
    pearl = world.add(Entity(id="pearl", type="pearl", label="pseudo pearl"))
    world.add(Entity(id="room", type="room", label="the room"))

    for eid in ("seeker", "mate", "parent", "cause_actor", "pearl", "room"):
        ent = world.get(eid)
        ent.meters["hidden"] += 0.0
        ent.meters["found"] += 0.0
        ent.meters["clue"] += 0.0
        ent.meters["mystery"] += 0.0
        ent.meters["moved_item"] += 0.0
        ent.memes["joy"] += 0.0
        ent.memes["worry"] += 0.0
        ent.memes["resolve"] += 0.0
        ent.memes["relief"] += 0.0
        ent.memes["focus"] += 0.0
        ent.memes["pride"] += 0.0
        ent.memes["care"] += 0.0

    world.facts.update(
        theme=theme,
        cause=cause,
        spot=spot,
        method=method,
        helper=helper,
        seeker=seeker,
        mate=mate,
        parent=parent,
        cause_actor=cause_actor,
        pearl=pearl,
    )

    play_setup(world, seeker, mate, theme)
    need_pearl(world, seeker, mate)

    world.para()
    discover_mystery(world, seeker, mate, cause_actor)
    first_clue(world, seeker, cause)
    choose_method(world, seeker, method, spot)

    world.para()
    if spot.height == "high":
        search_high(world, seeker, mate, parent, spot, helper)
    else:
        search_low(world, seeker, mate, spot, helper)
    find_pearl(world, seeker, mate, pearl, cause_actor, spot)

    world.para()
    lesson_and_end(world, seeker, mate, parent, theme)

    world.facts.update(
        solved=pearl.meters["found"] >= THRESHOLD,
        needed_parent=spot.height == "high",
        helper_kind=helper_needed(spot),
    )
    return world


THEMES = {
    "storm_ship": Theme(
        id="storm_ship",
        scene="a storm-tossed pirate ship",
        rig="A blanket over two chairs became the captain's cabin, a broom stood like a mast, and a toy chest waited as the locked treasure hold.",
        titles=("Captain", "Lookout"),
        goal="the Moon-Marked Chest Quest",
        ending="the two pirates cheered and shared the paper gold inside",
    ),
    "island_cove": Theme(
        id="island_cove",
        scene="a secret island cove",
        rig="The rug was their sandy shore, a blue scarf was the sea, and the toy chest sat beyond a row of cushions like a hidden cave.",
        titles=("Captain", "Map-Keeper"),
        goal="the Hidden Cove Quest",
        ending="the young pirates whooped and poured out shiny beads and stickers",
    ),
    "fog_fort": Theme(
        id="fog_fort",
        scene="a foggy pirate fort",
        rig="The sofa became the fort wall, a laundry basket turned into a supply boat, and the toy chest waited under a scarf flag like a prize from the sea.",
        titles=("Captain", "Scout"),
        goal="the Fort Lantern Quest",
        ending="the brave crew opened the chest and found cinnamon biscuits wrapped in paper",
    ),
}

CAUSES = {
    "puppy": Cause(
        id="puppy",
        actor_type="puppy",
        actor_label="the puppy",
        access={"under_sofa", "dog_bed"},
        clue_kind="trail",
        sign_text="On the floor, tiny dusty pawprints curved away from the chest.",
        think_text="Pawprints mean the puppy nosed the pearl and carried it somewhere low.",
        carry_style="nosed",
        tags={"puppy", "trail"},
    ),
    "breeze": Cause(
        id="breeze",
        actor_type="thing",
        actor_label="the open-window breeze",
        access={"curtain_fold", "book_nook"},
        clue_kind="flutter",
        sign_text="The curtain gave a small flutter, and the treasure map corner rustled on the floor.",
        think_text="A breeze cannot hide things on purpose, but it can scoot light treasures into soft or papery places.",
        carry_style="blew",
        tags={"wind", "flutter"},
    ),
    "little_sister": Cause(
        id="little_sister",
        actor_type="girl",
        actor_label="little Nora",
        access={"block_bucket", "high_shelf"},
        clue_kind="habit",
        sign_text="Beside the chest sat a crooked tower of blocks, built the wobbly way little Nora always liked.",
        think_text="That block tower looks like Nora's work. When she borrows shiny things, she tucks them near the toys she is already using.",
        carry_style="carried",
        tags={"family", "habit"},
    ),
}

SPOTS = {
    "under_sofa": Spot(
        id="under_sofa",
        label="under the sofa",
        phrase="the dark dust-line under the sofa",
        height="low",
        reveal_text="They knelt and peeped into the dim gap under the sofa.",
        tags={"low_place"},
    ),
    "dog_bed": Spot(
        id="dog_bed",
        label="the dog bed",
        phrase="the crumpled blanket in the dog bed",
        height="low",
        reveal_text="They crept to the dog bed and lifted one warm corner of the blanket.",
        tags={"low_place", "pet"},
    ),
    "curtain_fold": Spot(
        id="curtain_fold",
        label="the curtain fold",
        phrase="the deep fold of the curtain",
        height="low",
        reveal_text="They parted the curtain gently, and something pale winked from the cloth.",
        tags={"curtain"},
    ),
    "book_nook": Spot(
        id="book_nook",
        label="the book nook",
        phrase="the open picture book by the window",
        height="low",
        reveal_text="They turned the half-open picture book, and a round white bead rolled from the pages.",
        tags={"book"},
    ),
    "block_bucket": Spot(
        id="block_bucket",
        label="the block bucket",
        phrase="the yellow block bucket",
        height="low",
        reveal_text="They peered into the block bucket, where wooden cubes hid a glimmering bead.",
        tags={"toy"},
    ),
    "high_shelf": Spot(
        id="high_shelf",
        label="the high shelf",
        phrase="the top shelf above the art table",
        height="high",
        reveal_text="From the shelf, tucked beside a paper crown, the little pearl gleamed back at them.",
        tags={"high_place"},
    ),
}

METHODS = {
    "follow_trail": Method(
        id="follow_trail",
        clue_kind="trail",
        sense=3,
        text="Keeping very still, the captain followed the little trail of marks across the floor like a pirate reading tracks in sand",
        qa_text="followed the little trail on the floor",
        tags={"trail"},
    ),
    "notice_flutter": Method(
        id="notice_flutter",
        clue_kind="flutter",
        sense=3,
        text="Watching the room the way sailors watch a sail, the captain followed the fluttering cloth and rustling paper",
        qa_text="watched for the fluttering cloth and paper",
        tags={"flutter"},
    ),
    "remember_habit": Method(
        id="remember_habit",
        clue_kind="habit",
        sense=3,
        text="Thinking about what little hands usually do, the captain remembered where Nora liked to tuck shiny borrowed things",
        qa_text="remembered Nora's toy-hiding habit",
        tags={"habit"},
    ),
    "guess_wildly": Method(
        id="guess_wildly",
        clue_kind="none",
        sense=1,
        text="The captain shut both eyes and made a wild guess without looking at any real clue",
        qa_text="made a wild guess",
        tags={"bad_idea"},
    ),
}

HELPERS = {
    "kneel_and_peek": HelperMove(
        id="kneel_and_peek",
        sense=3,
        handles={"low"},
        text="they knelt and peeked into every tucked-away pirate place they could really reach",
        qa_text="knelt and peeked in the reachable hiding places",
        tags={"search"},
    ),
    "lift_and_look": HelperMove(
        id="lift_and_look",
        sense=3,
        handles={"high"},
        text="asked for a careful lift so they could look on the high shelf without climbing",
        qa_text="asked a grown-up for a careful lift to check the high shelf",
        tags={"adult_help"},
    ),
    "chair_climb": HelperMove(
        id="chair_climb",
        sense=1,
        handles={"high"},
        text="dragged over a wobbly chair to climb up alone",
        qa_text="climbed a chair alone",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    theme: str
    cause: str
    spot: str
    method: str
    helper: str
    seeker_name: str
    seeker_gender: str
    mate_name: str
    mate_gender: str
    parent: str
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
    "pseudo": [
        (
            "What does pseudo mean?",
            "Pseudo means something that only pretends to be the real thing. A pseudo pearl in this story is a play pearl, not a real treasure from the sea."
        )
    ],
    "trail": [
        (
            "What can pawprints tell you?",
            "Pawprints can show where an animal went. If they lead away from a place, they can help you guess where to look next."
        )
    ],
    "flutter": [
        (
            "How can a breeze move light things?",
            "A breeze can push light paper, cloth, or tiny beads. That is why open windows can make little things slide or roll away."
        )
    ],
    "habit": [
        (
            "What is a habit?",
            "A habit is something a person often does the same way again and again. Remembering a habit can help you solve a small mystery."
        )
    ],
    "adult_help": [
        (
            "Why should children ask a grown-up for help with high shelves?",
            "High shelves are hard to reach safely. A grown-up can help without wobbling chairs or risky climbing."
        )
    ],
    "puppy": [
        (
            "Why do puppies carry small things away?",
            "Puppies explore with their noses and mouths, and small objects can seem like toys to them. That is why they sometimes wander off with things they find."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a question you do not know the answer to yet. You solve it by noticing clues and thinking carefully."
        )
    ],
}
KNOWLEDGE_ORDER = ["pseudo", "mystery", "puppy", "trail", "flutter", "habit", "adult_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    mate = f["mate"]
    theme = f["theme"]
    cause = f["cause"]
    spot = f["spot"]
    need_help = f.get("needed_parent", False)
    base = (
        'Write a pirate-flavored story for a 3-to-5-year-old that includes the word "pseudo", '
        "features a quest, and contains a small mystery to solve."
    )
    if need_help:
        return [
            base,
            f"Tell a gentle mystery story where {seeker.label} and {mate.label} lose a pseudo pearl during {theme.goal}, "
            f"follow clues from {cause.actor_label}, and ask a grown-up for help checking {spot.label}.",
            f"Write a story with one quiet inner monologue line where a child pirate solves a missing-treasure clue and ends the quest safely."
        ]
    return [
        base,
        f"Tell a pirate tale where {seeker.label} notices clues left by {cause.actor_label}, thinks quietly to {seeker.pronoun('object')}self, "
        f"and finds the pseudo pearl in {spot.label}.",
        f"Write a simple quest story with a mystery turn, a child-sized deduction, and a happy ending that proves the treasure game can continue."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    mate = f["mate"]
    parent = f["parent"]
    cause = f["cause"]
    spot = f["spot"]
    method = f["method"]
    theme = f["theme"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.label} and {mate.label}, two children playing pirates, and the missing pseudo pearl they needed for {theme.goal}. The quest becomes a mystery when the little treasure piece disappears."
        ),
        (
            "What was the mystery?",
            "The mystery was where the pseudo pearl had gone. The children needed it to open their pretend treasure chest, so the game could not continue until they found it."
        ),
        (
            f"What clue helped {seeker.label} start solving the mystery?",
            f"{cause.sign_text.split('.')[0]}. That first clue pointed {seeker.label} toward the right kind of hiding place."
        ),
        (
            f"What did {seeker.label} think in the inner monologue part?",
            f'{seeker.label} thought, "{cause.think_text}" That quiet thought turns the clue into a plan instead of a random guess.'
        ),
        (
            f"How did {seeker.label} solve the mystery?",
            f"{seeker.label} {method.qa_text} and searched near {spot.label}. The clue and the search method matched each other, so the children could look in a sensible place."
        ),
    ]
    if f.get("needed_parent"):
        qa.append(
            (
                f"Why did they ask {pw} for help?",
                f"They asked {pw} for help because the pearl was in a high place they could not safely reach alone. Getting help let them finish the quest without climbing on something wobbly."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"The children found the pseudo pearl and clicked it into the chest. Then the pirate game could begin again, and the shell bowl showed they had learned where to keep little treasure pieces."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"pseudo", "mystery"}
    tags |= set(f["method"].tags)
    tags |= set(f["helper"].tags)
    if f["cause"].id == "puppy":
        tags.add("puppy")
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
        if e.label and e.id != e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="storm_ship",
        cause="puppy",
        spot="dog_bed",
        method="follow_trail",
        helper="kneel_and_peek",
        seeker_name="Lily",
        seeker_gender="girl",
        mate_name="Tom",
        mate_gender="boy",
        parent="mother",
    ),
    StoryParams(
        theme="island_cove",
        cause="breeze",
        spot="curtain_fold",
        method="notice_flutter",
        helper="kneel_and_peek",
        seeker_name="Mia",
        seeker_gender="girl",
        mate_name="Ben",
        mate_gender="boy",
        parent="father",
    ),
    StoryParams(
        theme="fog_fort",
        cause="little_sister",
        spot="block_bucket",
        method="remember_habit",
        helper="kneel_and_peek",
        seeker_name="Sam",
        seeker_gender="boy",
        mate_name="Zoe",
        mate_gender="girl",
        parent="mother",
    ),
    StoryParams(
        theme="storm_ship",
        cause="little_sister",
        spot="high_shelf",
        method="remember_habit",
        helper="lift_and_look",
        seeker_name="Eli",
        seeker_gender="boy",
        mate_name="Nora",
        mate_gender="girl",
        parent="father",
    ),
]


ASP_RULES = r"""
% Reasonableness gate.
valid(T,C,S,M) :- theme(T), cause(C), spot(S), method(M),
                  access(C,S), clue_of(C,K), method_clue(M,K).

sensible_helper(H) :- helper(H), sense(H,S), sense_min(Min), S >= Min.
needs(S,high) :- spot_height(S,high).
needs(S,low)  :- spot_height(S,low).
helper_fits(H,S) :- helper(H), handles(H,Need), needs(S,Need).

% Story outcome.
solved :- chosen_theme(T), chosen_cause(C), chosen_spot(S), chosen_method(M),
          valid(T,C,S,M), chosen_helper(H), sensible_helper(H), helper_fits(H,S).

outcome(found) :- solved.
outcome(bad_helper) :- chosen_helper(H), not sensible_helper(H).
outcome(mismatch) :- chosen_theme(T), chosen_cause(C), chosen_spot(S), chosen_method(M),
                     not valid(T,C,S,M), theme(T), cause(C), spot(S), method(M).

#defined chosen_theme/1.
#defined chosen_cause/1.
#defined chosen_spot/1.
#defined chosen_method/1.
#defined chosen_helper/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("clue_of", cid, cause.clue_kind))
        for spot_id in sorted(cause.access):
            lines.append(asp.fact("access", cid, spot_id))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("spot_height", sid, spot.height))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_clue", mid, method.clue_kind))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        for handle in sorted(helper.handles):
            lines.append(asp.fact("handles", hid, handle))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_helpers() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_helper/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible_helper"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_theme", params.theme),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.theme not in THEMES or params.cause not in CAUSES or params.spot not in SPOTS or params.method not in METHODS or params.helper not in HELPERS:
        return "mismatch"
    cause = CAUSES[params.cause]
    spot = SPOTS[params.spot]
    method = METHODS[params.method]
    helper = HELPERS[params.helper]
    if helper.sense < SENSE_MIN:
        return "bad_helper"
    if not cause_can_reach(cause, spot):
        return "mismatch"
    if not method_matches(cause, method):
        return "mismatch"
    if not helper_handles(spot, helper):
        return "mismatch"
    return "found"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {h.id for h in sensible_helpers()}
    asp_sensible = set(asp_sensible_helpers())
    if py_sensible == asp_sensible:
        print(f"OK: sensible helpers match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible helpers:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(asp_sensible))

    cases = list(CURATED)
    for seed in range(60):
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-flavored mystery quest: a missing pseudo pearl, a clue, and a solved little mystery."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--seeker-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.spot:
        cause = CAUSES[args.cause]
        spot = SPOTS[args.spot]
        if not cause_can_reach(cause, spot):
            raise StoryError(explain_cause_spot(cause, spot))
    if args.cause and args.method:
        cause = CAUSES[args.cause]
        method = METHODS[args.method]
        if not method_matches(cause, method):
            raise StoryError(explain_method(cause, method))
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_helper(args.helper))
    if args.helper and args.spot:
        helper = HELPERS[args.helper]
        spot = SPOTS[args.spot]
        if not helper_handles(spot, helper):
            raise StoryError(explain_helper_fit(helper, spot))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.cause is None or combo[1] == args.cause)
        and (args.spot is None or combo[2] == args.spot)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, cause_id, spot_id, method_id = rng.choice(sorted(combos))
    spot = SPOTS[spot_id]

    helper_choices = [
        hid for hid, helper in HELPERS.items()
        if helper.sense >= SENSE_MIN and helper_handles(spot, helper)
        and (args.helper is None or hid == args.helper)
    ]
    if not helper_choices:
        raise StoryError("(No sensible helper move matches the given options.)")
    helper_id = rng.choice(sorted(helper_choices))

    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    seeker_name = args.seeker_name or _pick_name(rng, seeker_gender)
    mate_name = args.mate_name or _pick_name(rng, mate_gender, avoid=seeker_name)
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        theme=theme_id,
        cause=cause_id,
        spot=spot_id,
        method=method_id,
        helper=helper_id,
        seeker_name=seeker_name,
        seeker_gender=seeker_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    required = {
        "theme": THEMES,
        "cause": CAUSES,
        "spot": SPOTS,
        "method": METHODS,
        "helper": HELPERS,
    }
    for field_name, registry in required.items():
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Invalid {field_name}: {value!r})")

    cause = CAUSES[params.cause]
    spot = SPOTS[params.spot]
    method = METHODS[params.method]
    helper = HELPERS[params.helper]
    if not cause_can_reach(cause, spot):
        raise StoryError(explain_cause_spot(cause, spot))
    if not method_matches(cause, method):
        raise StoryError(explain_method(cause, method))
    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper(params.helper))
    if not helper_handles(spot, helper):
        raise StoryError(explain_helper_fit(helper, spot))

    world = tell(
        theme=THEMES[params.theme],
        cause=cause,
        spot=spot,
        method=method,
        helper=helper,
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
    )

    seeker = world.get("seeker")
    mate = world.get("mate")
    world.story_names = {"seeker": seeker.label, "mate": mate.label}

    story = world.render().replace("seeker", seeker.label).replace("mate", mate.label)

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
        print(asp_program("", "#show valid/4.\n#show sensible_helper/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible helpers: {', '.join(asp_sensible_helpers())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, cause, spot, method) combos:\n")
        for theme, cause, spot, method in combos:
            print(f"  {theme:11} {cause:13} {spot:12} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.seeker_name} & {p.mate_name}: {p.cause} -> {p.spot} ({p.theme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
