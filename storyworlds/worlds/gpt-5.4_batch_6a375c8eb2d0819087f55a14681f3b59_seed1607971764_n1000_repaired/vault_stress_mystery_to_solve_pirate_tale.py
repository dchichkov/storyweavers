#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vault_stress_mystery_to_solve_pirate_tale.py
=======================================================================

A standalone storyworld about a tiny pirate mystery: two children are playing
pirates, open their pretend treasure vault, and discover that an important
treasure is missing. One child feels a knot of stress, the other treats the
problem like a mystery to solve, and the world model decides which clues exist,
where the treasure really went, whether the chosen search method is sensible,
and whether the crew solves the mystery alone or with calm grown-up help.

The domain is intentionally small and constraint-checked:
- a culprit must plausibly be able to move the missing treasure
- a hideout must be reachable for that culprit
- the chosen method must pass a common-sense gate
- the ending depends on search power versus the mystery's difficulty

Run it
------
    python storyworlds/worlds/gpt-5.4/vault_stress_mystery_to_solve_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/vault_stress_mystery_to_solve_pirate_tale.py --culprit parrot --treasure compass
    python storyworlds/worlds/gpt-5.4/vault_stress_mystery_to_solve_pirate_tale.py --method accuse_friend
    python storyworlds/worlds/gpt-5.4/vault_stress_mystery_to_solve_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/vault_stress_mystery_to_solve_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/vault_stress_mystery_to_solve_pirate_tale.py --verify
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
    # two axes
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
    chant: str
    vault_name: str
    goal: str
    send_off: str
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
    article: str
    light: bool = False
    shiny: bool = False
    chewy: bool = False
    crinkly: bool = False
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
class Culprit:
    id: str
    label: str
    clue: str
    trace: str
    likes: set[str] = field(default_factory=set)
    reaches: set[str] = field(default_factory=set)
    sneak: int = 1
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
class Hideout:
    id: str
    label: str
    phrase: str
    depth: int = 1
    place_word: str = ""
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
    sense: int
    power: int
    text: str
    fail: str
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


def _r_missing_stress(world: World) -> list[str]:
    out: list[str] = []
    vault = world.get("vault")
    treasure = world.get("treasure")
    if vault.meters["opened"] >= THRESHOLD and treasure.attrs.get("missing", False):
        sig = ("missing_stress", treasure.id)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["mystery"] += 1
            mate = world.facts.get("mate_ent")
            if mate is not None:
                mate.memes["stress"] += 2
            captain = world.facts.get("captain_ent")
            if captain is not None:
                captain.memes["stress"] += 1
            out.append("__missing__")
    return out


def _r_clue_hope(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["clue_seen"] >= THRESHOLD:
        sig = ("clue_hope",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["hope"] += 1
                if kid.memes["stress"] > 0:
                    kid.memes["stress"] -= 1
            out.append("__clue__")
    return out


def _r_solved_relief(world: World) -> list[str]:
    out: list[str] = []
    treasure = world.get("treasure")
    if treasure.attrs.get("found", False):
        sig = ("solved_relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["relief"] += 2
                kid.memes["joy"] += 1
                kid.memes["stress"] = 0.0
            out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_stress", tag="emotional", apply=_r_missing_stress),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_hope),
    Rule(name="solved_relief", tag="emotional", apply=_r_solved_relief),
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


def treasure_tags(treasure: Treasure) -> set[str]:
    tags: set[str] = set()
    if treasure.shiny:
        tags.add("shiny")
    if treasure.light:
        tags.add("light")
    if treasure.chewy:
        tags.add("chewy")
    if treasure.crinkly:
        tags.add("crinkly")
    return tags


def culprit_can_move(culprit: Culprit, treasure: Treasure) -> bool:
    return bool(culprit.likes & treasure_tags(treasure))


def culprit_can_hide(culprit: Culprit, hideout: Hideout) -> bool:
    return hideout.id in culprit.reaches


def valid_combo(culprit: Culprit, treasure: Treasure, hideout: Hideout) -> bool:
    return culprit_can_move(culprit, treasure) and culprit_can_hide(culprit, hideout)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for culprit_id, culprit in CULPRITS.items():
        for treasure_id, treasure in TREASURES.items():
            for hideout_id, hideout in HIDEOUTS.items():
                if valid_combo(culprit, treasure, hideout):
                    combos.append((culprit_id, treasure_id, hideout_id))
    return combos


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def mystery_difficulty(culprit: Culprit, hideout: Hideout) -> int:
    return culprit.sneak + hideout.depth


def solved_by_crew(method: Method, culprit: Culprit, hideout: Hideout) -> bool:
    return method.power >= mystery_difficulty(culprit, hideout)


def explain_combo_rejection(culprit: Culprit, treasure: Treasure, hideout: Hideout) -> str:
    if not culprit_can_move(culprit, treasure):
        return (
            f"(No story: {culprit.label} would not plausibly carry {treasure.article} "
            f"{treasure.label}. Pick a treasure that matches what {culprit.label} likes.)"
        )
    if not culprit_can_hide(culprit, hideout):
        return (
            f"(No story: {culprit.label} cannot plausibly stash treasure in {hideout.phrase}. "
            f"Pick a reachable hideout.)"
        )
    return "(No story: this mystery setup is unreasonable.)"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = " / ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try: {better}.)"
    )


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a bright little pirate ship",
        rig="The sofa was the deck, a blanket over two chairs was a sea cave, and an old wooden box with a brass clasp was their treasure vault.",
        chant='"Captain on deck! Treasure watch!"',
        vault_name="treasure vault",
        goal="guard the crew's secret riches",
        send_off="set sail again with their clues tucked safely in a notebook",
    ),
    "storm_pirates": Theme(
        id="storm_pirates",
        scene="a storm-tossed pirate cabin",
        rig="The sofa was the deck, a blue sheet became a noisy sea, and an old toy chest with a tiny lock was their treasure vault.",
        chant='"Batten down the hatches! Count the treasure!"',
        vault_name="storm vault",
        goal="keep the captain's treasure safe through the pretend storm",
        send_off="went back to their ship game with calmer hearts and wiser pirate rules",
    ),
}

TREASURES = {
    "compass": Treasure(
        id="compass",
        label="tiny brass compass",
        phrase="a tiny brass compass with a blue star painted on the lid",
        article="a",
        light=True,
        shiny=True,
        tags={"compass", "shiny", "vault"},
    ),
    "pearl_key": Treasure(
        id="pearl_key",
        label="pearl key",
        phrase="a pearl key tied to a blue ribbon",
        article="a",
        light=True,
        shiny=True,
        tags={"key", "shiny", "vault"},
    ),
    "cracker_map": Treasure(
        id="cracker_map",
        label="cracker map",
        phrase="a crinkly treasure map that still smelled faintly of crackers",
        article="a",
        light=True,
        crinkly=True,
        chewy=True,
        tags={"map", "vault"},
    ),
    "rope_ring": Treasure(
        id="rope_ring",
        label="rope ring",
        phrase="a little rope ring with a red knot",
        article="a",
        chewy=True,
        tags={"rope", "vault"},
    ),
}

CULPRITS = {
    "parrot": Culprit(
        id="parrot",
        label="the parrot",
        clue="a bright green feather",
        trace="a single bright green feather",
        likes={"shiny", "light"},
        reaches={"curtain_fold", "mast_shelf"},
        sneak=2,
        tags={"parrot", "clue"},
    ),
    "puppy": Culprit(
        id="puppy",
        label="the puppy",
        clue="tiny muddy pawprints",
        trace="a line of tiny muddy pawprints",
        likes={"chewy", "crinkly"},
        reaches={"boot_basket", "flowerpot"},
        sneak=1,
        tags={"puppy", "clue"},
    ),
    "wind": Culprit(
        id="wind",
        label="the breeze",
        clue="a fluttering corner and a faint rustle",
        trace="a fluttering trail of paper and ribbon",
        likes={"light", "crinkly"},
        reaches={"curtain_fold", "flowerpot"},
        sneak=2,
        tags={"wind", "clue"},
    ),
}

HIDEOUTS = {
    "curtain_fold": Hideout(
        id="curtain_fold",
        label="curtain fold",
        phrase="a soft fold in the long curtain",
        depth=1,
        place_word="by the window",
        tags={"curtain"},
    ),
    "mast_shelf": Hideout(
        id="mast_shelf",
        label="high shelf",
        phrase="the highest shelf above the playroom books",
        depth=2,
        place_word="up high",
        tags={"shelf"},
    ),
    "boot_basket": Hideout(
        id="boot_basket",
        label="boot basket",
        phrase="the wicker basket where muddy boots slept",
        depth=1,
        place_word="near the door",
        tags={"basket"},
    ),
    "flowerpot": Hideout(
        id="flowerpot",
        label="flowerpot",
        phrase="the biggest flowerpot on the porch",
        depth=2,
        place_word="outside on the porch",
        tags={"flowerpot"},
    ),
}

METHODS = {
    "follow_clues": Method(
        id="follow_clues",
        sense=3,
        power=3,
        text="knelt down, studied every little sign, and followed the trail with pirate care",
        fail="followed the first clue bravely, but the trail grew faint before they could be sure",
        qa_text="followed the clues carefully",
        tags={"clue_following"},
    ),
    "retrace_steps": Method(
        id="retrace_steps",
        sense=2,
        power=2,
        text="went back over the whole game, checking each place the treasure had been last",
        fail="retraced their steps, but the hiding place was still too tricky to guess",
        qa_text="retraced their steps through the game",
        tags={"memory"},
    ),
    "ask_parent": Method(
        id="ask_parent",
        sense=3,
        power=4,
        text="called for their grown-up first and then searched together, slowly and carefully",
        fail="asked for help, but even that took a while because the trail was very sneaky",
        qa_text="asked a grown-up for help and searched together",
        tags={"help"},
    ),
    "accuse_friend": Method(
        id="accuse_friend",
        sense=1,
        power=0,
        text="pointed at each other instead of looking at the room",
        fail="wasted time blaming each other while the mystery stayed unsolved",
        qa_text="blamed each other",
        tags={"blame"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "steady", "clever", "thoughtful", "brave"]


@dataclass
class StoryParams:
    theme: str = "pirates"
    culprit: str = "parrot"
    treasure: str = "compass"
    hideout: str = "curtain_fold"
    method: str = "follow_clues"
    captain: str = "Tom"
    captain_gender: str = "boy"
    mate: str = "Lily"
    mate_gender: str = "girl"
    parent: str = "mother"
    captain_trait: str = "brave"
    mate_trait: str = "careful"
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


def play_setup(world: World, captain: Entity, mate: Entity, theme: Theme, treasure: Treasure) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id} turned the living room into {theme.scene}. {theme.rig}"
    )
    world.say(
        f"{theme.chant} {captain.id} cried. They had been using {treasure.article} {treasure.label} as the most important piece of treasure while they tried to {theme.goal}."
    )


def open_vault(world: World, captain: Entity, mate: Entity, theme: Theme) -> None:
    vault = world.get("vault")
    vault.meters["opened"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {mate.id} lifted the lid of the {theme.vault_name}, the place where the special treasure should have been was empty."
    )
    if mate.memes["stress"] >= 2:
        world.say(
            f"A hard little knot of stress gathered in {mate.id}'s tummy. \"The vault is empty,\" {mate.pronoun()} whispered."
        )
    world.say(
        f"{captain.id} blinked at the empty velvet square. For one moment, the whole pirate game went very still."
    )


def notice_clue(world: World, captain: Entity, mate: Entity, culprit: Culprit) -> None:
    room = world.get("room")
    room.meters["clue_seen"] += 1
    propagate(world, narrate=False)
    clue_text = culprit.clue
    world.say(
        f"Then {captain.id} spotted {clue_text} beside the vault. \"Wait,\" {captain.pronoun()} said. \"Treasure does not walk away by itself.\""
    )
    if mate.memes["hope"] >= 1:
        world.say(
            f"The knot of stress loosened a little. A clue meant this was a mystery to solve, not magic."
        )


def reason_about_clue(world: World, captain: Entity, mate: Entity, culprit: Culprit, hideout: Hideout) -> None:
    world.say(
        f"They looked around the room like tiny detectives on a pirate ship. {captain.id} remembered that {culprit.label} had been near {hideout.place_word} earlier."
    )
    world.say(
        f"\"If we look carefully,\" {mate.id} said, \"the room will tell us where the treasure sailed.\""
    )


def search(world: World, captain: Entity, mate: Entity, method: Method, culprit: Culprit, treasure: Treasure, hideout: Hideout) -> bool:
    world.say(
        f"So the two pirates {method.text}."
    )
    if solved_by_crew(method, culprit, hideout):
        treasure_ent = world.get("treasure")
        treasure_ent.attrs["found"] = True
        treasure_ent.attrs["missing"] = False
        treasure_ent.attrs["where_found"] = hideout.id
        propagate(world, narrate=False)
        if culprit.id == "parrot":
            extra = f"Above them, {culprit.label} gave a proud squawk."
        elif culprit.id == "puppy":
            extra = f"Beside them, {culprit.label} thumped its tail as if the whole thing had been a fine game."
        else:
            extra = "At the window, the curtain lifted and settled again with a soft hush."
        world.say(
            f"At last they found {treasure.article} {treasure.label} tucked in {hideout.phrase}. {extra}"
        )
        return True
    world.say(
        f"But {method.fail}."
    )
    return False


def parent_help(world: World, parent: Entity, captain: Entity, mate: Entity, culprit: Culprit, treasure: Treasure, hideout: Hideout) -> None:
    treasure_ent = world.get("treasure")
    treasure_ent.attrs["found"] = True
    treasure_ent.attrs["missing"] = False
    treasure_ent.attrs["where_found"] = hideout.id
    propagate(world, narrate=False)
    world.say(
        f"At last {captain.id} called for {parent.label_word}. {parent.label_word.capitalize()} came in, saw {culprit.trace}, and smiled the calm smile grown-ups use when a puzzle begins to open."
    )
    world.say(
        f'Together they checked {hideout.phrase}, and there was {treasure.article} {treasure.label}, hidden away at last. "{mate.id}," {parent.pronoun()} said softly, "good mysteries feel smaller when everyone looks carefully together."'
    )


def lesson_and_end(world: World, parent: Entity, captain: Entity, mate: Entity, theme: Theme, treasure: Treasure, solved_alone: bool) -> None:
    vault = world.get("vault")
    vault.meters["latched"] += 1
    for kid in (captain, mate):
        kid.memes["trust"] += 1
        kid.memes["lesson"] += 1
    if solved_alone:
        world.say(
            f"{mate.id} hugged the {treasure.label} to {mate.pronoun('possessive')} chest and let out the longest breath. The stress was gone now, washed away by relief and a little pride."
        )
    else:
        world.say(
            f"{mate.id} hugged the {treasure.label} to {mate.pronoun('possessive')} chest and let out the longest breath. The stress was gone now, because help had turned the puzzle into something safe and solvable."
        )
    world.say(
        f'Then they put the treasure back into the vault and clicked the clasp shut. "{theme.vault_name.capitalize()} closed before snack time," {captain.id} announced, trying out a new pirate rule.'
    )
    world.say(
        f"After that, they {theme.send_off}. This time the crew kept a better watch, and the room felt brave instead of worried."
    )


def tell(
    theme: Theme,
    culprit: Culprit,
    treasure: Treasure,
    hideout: Hideout,
    method: Method,
    captain_name: str = "Tom",
    captain_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    parent_type: str = "mother",
    captain_trait: str = "brave",
    mate_trait: str = "careful",
) -> World:
    world = World()
    captain = world.add(
        Entity(
            id=captain_name,
            kind="character",
            type=captain_gender,
            role="captain",
            traits=[captain_trait],
            attrs={},
        )
    )
    mate = world.add(
        Entity(
            id=mate_name,
            kind="character",
            type=mate_gender,
            role="mate",
            traits=[mate_trait],
            attrs={},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            attrs={},
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="room",
            label="playroom",
            attrs={},
        )
    )
    vault = world.add(
        Entity(
            id="vault",
            type="vault",
            label=theme.vault_name,
            attrs={},
        )
    )
    treasure_ent = world.add(
        Entity(
            id="treasure",
            type="treasure",
            label=treasure.label,
            movable=True,
            attrs={"missing": True, "found": False, "where_found": ""},
        )
    )

    world.facts.update(
        theme=theme,
        culprit=culprit,
        treasure_cfg=treasure,
        hideout=hideout,
        method=method,
        captain_ent=captain,
        mate_ent=mate,
        parent_ent=parent,
        solved_alone=False,
        outcome="",
    )

    play_setup(world, captain, mate, theme, treasure)
    world.para()
    open_vault(world, captain, mate, theme)
    notice_clue(world, captain, mate, culprit)
    reason_about_clue(world, captain, mate, culprit, hideout)
    world.para()
    solved_alone = search(world, captain, mate, method, culprit, treasure, hideout)

    if not solved_alone:
        world.para()
        parent_help(world, parent, captain, mate, culprit, treasure, hideout)

    world.para()
    lesson_and_end(world, parent, captain, mate, theme, treasure, solved_alone)

    world.facts.update(
        solved_alone=solved_alone,
        outcome="crew_found" if solved_alone else "helped_found",
        found_location=hideout.id,
        clue_seen=room.meters["clue_seen"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "vault": [
        (
            "What is a vault?",
            "A vault is a place made to keep important things safe. In this story it is a pretend treasure box, but real vaults are strong locked places."
        )
    ],
    "stress": [
        (
            "What is stress?",
            "Stress is the tight worried feeling your body can get when something seems wrong or hard. It often feels smaller when you slow down, breathe, and get help."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. A feather, pawprint, or rustling ribbon can all be clues in a mystery."
        )
    ],
    "parrot": [
        (
            "Why might a parrot grab something shiny?",
            "Parrots notice bright shiny things because those things catch their eyes. That can make a shiny toy look interesting to carry away."
        )
    ],
    "puppy": [
        (
            "Why does a puppy carry things away sometimes?",
            "Puppies like to mouth, drag, and hide objects because they are playful and curious. Soft or crinkly things can seem especially fun."
        )
    ],
    "wind": [
        (
            "How can wind move light things?",
            "Wind pushes on light things like paper or ribbon. If an object is light enough, a breeze can slide or flutter it somewhere else."
        )
    ],
    "compass": [
        (
            "What is a compass?",
            "A compass is a tool that shows direction. Sailors use it to help know which way they are going."
        )
    ],
    "key": [
        (
            "What does a key do?",
            "A key opens or locks something. In stories, a special key often protects a secret place or treasure."
        )
    ],
    "map": [
        (
            "What is a treasure map?",
            "A treasure map is a picture that shows where treasure might be hidden. Pirates in stories use maps to guide their search."
        )
    ],
    "help": [
        (
            "Why can asking a grown-up help with a problem?",
            "A grown-up can help you slow down and notice details you missed. Working together often makes a puzzle easier."
        )
    ],
    "clue_following": [
        (
            "Why is following clues better than blaming someone?",
            "Following clues uses real signs from the world. Blaming someone without looking does not solve the mystery."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "vault",
    "stress",
    "clue",
    "parrot",
    "puppy",
    "wind",
    "compass",
    "key",
    "map",
    "help",
    "clue_following",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    culprit = f["culprit"]
    treasure = f["treasure_cfg"]
    theme = f["theme"]
    outcome = f["outcome"]
    if outcome == "crew_found":
        return [
            f'Write a pirate-style mystery for a 3-to-5-year-old that includes the words "vault" and "stress". Two children discover that {treasure.article} {treasure.label} is missing from a {theme.vault_name}, find a clue, and solve the mystery themselves.',
            f"Tell a gentle story where a child feels stress when treasure goes missing, but a clue from {culprit.label} helps the pirate crew think carefully and find it.",
            f"Write a complete pirate tale with a mystery to solve, a missing treasure, and a happy ending where the children close the vault safely at the end.",
        ]
    return [
        f'Write a pirate-style mystery for a 3-to-5-year-old that includes the words "vault" and "stress". Two children discover that {treasure.article} {treasure.label} is missing from a {theme.vault_name}, follow clues, and then ask a grown-up for help.',
        f"Tell a gentle pirate story where stress turns into relief after a missing treasure mystery is solved with calm help.",
        f"Write a story with a clue, a missing treasure, and a grown-up who helps the pirate crew finish the mystery kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain_ent"]
    mate = f["mate_ent"]
    parent = f["parent_ent"]
    culprit = f["culprit"]
    treasure = f["treasure_cfg"]
    hideout = f["hideout"]
    method = f["method"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {captain.id} and {mate.id}, who were pretending to be pirates. Their game changed when {treasure.article} {treasure.label} vanished from the vault."
        ),
        (
            "Why did the mystery begin?",
            f"The mystery began because the children opened their pretend vault and found the special treasure missing. That made the pirate game suddenly feel serious and gave {mate.id} a knot of stress."
        ),
        (
            "What clue did they find?",
            f"They found {culprit.clue} beside the vault. That clue mattered because it showed that something in the room had really moved the treasure."
        ),
        (
            f"How did the children try to solve the mystery?",
            f"They {method.qa_text}. They were not just guessing, because they used the clue and the room around them to decide where to look."
        ),
    ]
    if outcome == "crew_found":
        qa.append(
            (
                "Where was the missing treasure?",
                f"They found it in {hideout.phrase}. The clue led them there, and finding it turned the mystery into relief."
            )
        )
        qa.append(
            (
                f"How did {mate.id}'s stress change?",
                f"At first {mate.id} felt stress because the vault was empty and the treasure seemed gone. Then the clue gave hope, and the stress disappeared once the treasure was found."
            )
        )
    else:
        qa.append(
            (
                "Did the children solve the mystery alone?",
                f"No. They tried first, but the hiding place was too tricky. Then {parent.label_word} helped notice the trail and find the treasure with them."
            )
        )
        qa.append(
            (
                f"Why did asking {parent.label_word} help?",
                f"Asking {parent.label_word} helped because a calm grown-up could look slowly and see the clue clearly. Working together made the mystery feel smaller and safer."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the treasure back in the vault and a new pirate rule to close it carefully. The last image shows the game starting again with brave hearts instead of worry."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"vault", "stress", "clue"}
    culprit = f["culprit"]
    treasure = f["treasure_cfg"]
    method = f["method"]
    tags |= culprit.tags
    tags |= treasure.tags
    tags |= method.tags
    if f["outcome"] == "helped_found":
        tags.add("help")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        culprit="parrot",
        treasure="compass",
        hideout="curtain_fold",
        method="follow_clues",
        captain="Tom",
        captain_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        captain_trait="brave",
        mate_trait="careful",
    ),
    StoryParams(
        theme="storm_pirates",
        culprit="puppy",
        treasure="cracker_map",
        hideout="boot_basket",
        method="retrace_steps",
        captain="Mia",
        captain_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="father",
        captain_trait="clever",
        mate_trait="steady",
    ),
    StoryParams(
        theme="pirates",
        culprit="wind",
        treasure="pearl_key",
        hideout="flowerpot",
        method="ask_parent",
        captain="Nora",
        captain_gender="girl",
        mate="Sam",
        mate_gender="boy",
        parent="mother",
        captain_trait="thoughtful",
        mate_trait="curious",
    ),
    StoryParams(
        theme="storm_pirates",
        culprit="parrot",
        treasure="pearl_key",
        hideout="mast_shelf",
        method="retrace_steps",
        captain="Eli",
        captain_gender="boy",
        mate="Zoe",
        mate_gender="girl",
        parent="father",
        captain_trait="brave",
        mate_trait="careful",
    ),
]


ASP_RULES = r"""
% --- validity gate ----------------------------------------------------------
treasure_tag(T, shiny)  :- shiny(T).
treasure_tag(T, light)  :- light(T).
treasure_tag(T, chewy)  :- chewy(T).
treasure_tag(T, crinkly):- crinkly(T).

can_move(C, T) :- likes(C, Tag), treasure_tag(T, Tag).
can_hide(C, H) :- reaches(C, H).
valid(C, T, H) :- culprit(C), treasure(T), hideout(H), can_move(C, T), can_hide(C, H).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

% --- outcome model ----------------------------------------------------------
difficulty(V) :- chosen_culprit(C), chosen_hideout(H), sneak(C, S), depth(H, D), V = S + D.
crew_found    :- chosen_method(M), power(M, P), difficulty(V), P >= V.
helped_found  :- not crew_found.

outcome(crew_found)   :- crew_found.
outcome(helped_found) :- helped_found.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        if treasure.shiny:
            lines.append(asp.fact("shiny", treasure_id))
        if treasure.light:
            lines.append(asp.fact("light", treasure_id))
        if treasure.chewy:
            lines.append(asp.fact("chewy", treasure_id))
        if treasure.crinkly:
            lines.append(asp.fact("crinkly", treasure_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("sneak", culprit_id, culprit.sneak))
        for tag in sorted(culprit.likes):
            lines.append(asp.fact("likes", culprit_id, tag))
        for hideout_id in sorted(culprit.reaches):
            lines.append(asp.fact("reaches", culprit_id, hideout_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        lines.append(asp.fact("depth", hideout_id, hideout.depth))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_treasure", params.treasure),
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.culprit not in CULPRITS or params.hideout not in HIDEOUTS or params.method not in METHODS:
        raise StoryError("(No story: unknown culprit, hideout, or method.)")
    return "crew_found" if solved_by_crew(METHODS[params.method], CULPRITS[params.culprit], HIDEOUTS[params.hideout]) else "helped_found"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate mystery, missing treasure, clues, and relief."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery setups from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.treasure and args.hideout:
        culprit = CULPRITS[args.culprit]
        treasure = TREASURES[args.treasure]
        hideout = HIDEOUTS[args.hideout]
        if not valid_combo(culprit, treasure, hideout):
            raise StoryError(explain_combo_rejection(culprit, treasure, hideout))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.culprit is None or combo[0] == args.culprit)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.hideout is None or combo[2] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    culprit_id, treasure_id, hideout_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    theme_id = args.theme or rng.choice(sorted(THEMES))
    captain_name, captain_gender = _pick_kid(rng)
    mate_name, mate_gender = _pick_kid(rng, avoid=captain_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    captain_trait = rng.choice(TRAITS)
    mate_trait = rng.choice(TRAITS)
    return StoryParams(
        theme=theme_id,
        culprit=culprit_id,
        treasure=treasure_id,
        hideout=hideout_id,
        method=method_id,
        captain=captain_name,
        captain_gender=captain_gender,
        mate=mate_name,
        mate_gender=mate_gender,
        parent=parent_type,
        captain_trait=captain_trait,
        mate_trait=mate_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(No story: unknown theme '{params.theme}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.treasure not in TREASURES:
        raise StoryError(f"(No story: unknown treasure '{params.treasure}'.)")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(No story: unknown hideout '{params.hideout}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{params.method}'.)")
    culprit = CULPRITS[params.culprit]
    treasure = TREASURES[params.treasure]
    hideout = HIDEOUTS[params.hideout]
    method = METHODS[params.method]
    if not valid_combo(culprit, treasure, hideout):
        raise StoryError(explain_combo_rejection(culprit, treasure, hideout))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        THEMES[params.theme],
        culprit,
        treasure,
        hideout,
        method,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        captain_trait=params.captain_trait,
        mate_trait=params.mate_trait,
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


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=True, header="### smoke")
    finally:
        sys.stdout = old
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    if "vault" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not include 'vault'.")
    if "stress" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not include 'stress'.")


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

    clingo_methods = set(asp_sensible())
    python_methods = {m.id for m in sensible_methods()}
    if clingo_methods == python_methods:
        print(f"OK: sensible methods match ({sorted(clingo_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(clingo_methods)} python={sorted(python_methods)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
            cl = asp_outcome(params)
        except Exception as err:
            print(f"ERROR during outcome check for {params}: {err}")
            rc = 1
            bad += 1
            continue
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test passed for ordinary generate/emit.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (culprit, treasure, hideout) combos:\n")
        for culprit, treasure, hideout in combos:
            print(f"  {culprit:8} {treasure:11} {hideout}")
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
            header = f"### {p.captain} & {p.mate}: {p.treasure} missing from vault ({p.culprit}, {p.hideout}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
