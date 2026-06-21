#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cappuccino_symbol_steep_hill_path_reconciliation_mystery.py
======================================================================================

A small story world about a mysterious trail of symbols on a steep hill path.

Two children have had a falling-out after one of them blamed the other for a
missing keepsake. On the next day, a repeating symbol appears along the hill
path. The seeker follows the clues uphill, growing less suspicious and more
curious, until the trail leads to a hilltop café, a warm cappuccino on the
counter, and the friend who had quietly been trying to make peace.

This world keeps the shape required by STORY.md:
- typed entities with physical meters and emotional memes
- a reasonableness gate over symbol/marker combinations
- an inline ASP twin for the gate and the simple ending model
- world-grounded rendering and QA
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
from contextlib import redirect_stdout
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "cafe_keeper": "café keeper",
            "grandfather": "grandpa",
            "aunt": "aunt",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class SymbolCfg:
    id: str
    label: str
    shape_text: str
    memory_text: str
    foam_text: str
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
class KeepsakeCfg:
    id: str
    label: str
    phrase: str
    found_place: str
    repair_text: str
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
class MarkerCfg:
    id: str
    label: str
    plural: bool
    hill_safe: bool
    supports: set[str]
    clue_text: str
    reveal_text: str
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
class HelperCfg:
    id: str
    type: str
    label: str
    arrival_text: str
    reveal_text: str
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


SYMBOLS = {
    "spiral": SymbolCfg(
        id="spiral",
        label="spiral",
        shape_text="a curling spiral",
        memory_text="the little spiral they used to draw when they wanted to mean still friends",
        foam_text="a cinnamon spiral floating on the foam",
        tags={"symbol"},
    ),
    "star": SymbolCfg(
        id="star",
        label="star",
        shape_text="a neat five-pointed star",
        memory_text="the bright star they once put on every secret note they shared",
        foam_text="a cocoa star resting on the foam",
        tags={"symbol"},
    ),
    "leaf": SymbolCfg(
        id="leaf",
        label="leaf",
        shape_text="a simple pointed leaf",
        memory_text="the leaf they had chosen as their sign for walks and found things",
        foam_text="a leaf shape dusted on the foam",
        tags={"symbol"},
    ),
}

KEEPSAKES = {
    "sketchbook": KeepsakeCfg(
        id="sketchbook",
        label="sketchbook",
        phrase="a small sketchbook with a paper band around it",
        found_place="under the bench by the lower turn",
        repair_text="Its bent corner had been smoothed, and the paper band had been tied again.",
        tags={"sketchbook"},
    ),
    "compass_charm": KeepsakeCfg(
        id="compass_charm",
        label="compass charm",
        phrase="a tiny brass compass charm on a blue string",
        found_place="caught beside a loose root near the path",
        repair_text="The blue string had been retied with careful fingers.",
        tags={"compass"},
    ),
    "friendship_badge": KeepsakeCfg(
        id="friendship_badge",
        label="friendship badge",
        phrase="a round friendship badge with a pin on the back",
        found_place="tucked in the grass beside the first stone wall",
        repair_text="The pin had been straightened, and the front had been wiped clean.",
        tags={"badge"},
    ),
}

MARKERS = {
    "chalk": MarkerCfg(
        id="chalk",
        label="chalk marks",
        plural=True,
        hill_safe=True,
        supports={"spiral", "star", "leaf"},
        clue_text="a pale drawing on the flat side of a rock",
        reveal_text="I knew the rocks would stay where I left them, and chalk shows up from far away.",
        tags={"chalk"},
    ),
    "pebbles": MarkerCfg(
        id="pebbles",
        label="pebble patterns",
        plural=True,
        hill_safe=True,
        supports={"spiral", "star", "leaf"},
        clue_text="small pebbles set into a careful little pattern",
        reveal_text="The pebbles would not blow off the path, and I could shape them slowly.",
        tags={"pebbles"},
    ),
    "ribbon": MarkerCfg(
        id="ribbon",
        label="ribbon ties",
        plural=True,
        hill_safe=True,
        supports={"spiral"},
        clue_text="a blue ribbon curled into a tiny sign around a fence post",
        reveal_text="The ribbon could curl into our sign, and I tied it tight so the wind would not steal it.",
        tags={"ribbon"},
    ),
    "paper": MarkerCfg(
        id="paper",
        label="paper arrows",
        plural=True,
        hill_safe=False,
        supports={"spiral", "star", "leaf"},
        clue_text="a paper arrow tucked under a stone",
        reveal_text="",
        tags={"paper"},
    ),
}

HELPERS = {
    "keeper": HelperCfg(
        id="keeper",
        type="cafe_keeper",
        label="the café keeper",
        arrival_text="At the top of the hill, the little café door stood open, and warm air drifted out.",
        reveal_text="The café keeper had agreed to wait with the found keepsake until the trail did its work.",
        tags={"cafe", "cappuccino"},
    ),
    "grandpa": HelperCfg(
        id="grandpa",
        type="grandfather",
        label="Grandpa Niko",
        arrival_text="At the top of the hill, Grandpa Niko was resting beside the little café railing.",
        reveal_text="Grandpa Niko had promised to stay nearby so the apology would not feel lonely.",
        tags={"cafe", "cappuccino"},
    ),
    "aunt": HelperCfg(
        id="aunt",
        type="aunt",
        label="Aunt Rosa",
        arrival_text="At the top of the hill, Aunt Rosa was waiting by the little café window with kind eyes.",
        reveal_text="Aunt Rosa had helped keep the meeting gentle and brave.",
        tags={"cafe", "cappuccino"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Eva", "Tess", "Ivy", "Rosa", "June"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Sam", "Milo", "Eli", "Nico", "Ben"]
TRAITS = ["careful", "quiet", "curious", "thoughtful", "gentle", "stubborn"]


# ---------------------------------------------------------------------------
# World + rules
# ---------------------------------------------------------------------------
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


def _r_suspicion_softens(world: World) -> list[str]:
    seeker = world.get("seeker")
    if seeker.meters["clues_seen"] < THRESHOLD:
        return []
    sig = ("soften", int(seeker.meters["clues_seen"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["curiosity"] += 1
    seeker.memes["suspicion"] = max(0.0, seeker.memes["suspicion"] - 1.0)
    return []


def _r_memory_wakes(world: World) -> list[str]:
    seeker = world.get("seeker")
    if seeker.meters["clues_seen"] < 2:
        return []
    if ("memory",) in world.fired:
        return []
    world.fired.add(("memory",))
    seeker.memes["remembering"] += 1
    seeker.memes["hope"] += 1
    return []


def _r_reconciliation(world: World) -> list[str]:
    seeker = world.get("seeker")
    friend = world.get("friend")
    keepsake = world.get("keepsake")
    if seeker.memes["apology"] < THRESHOLD:
        return []
    if friend.memes["forgiveness"] < THRESHOLD:
        return []
    if keepsake.meters["returned"] < THRESHOLD:
        return []
    if ("reconciled",) in world.fired:
        return []
    world.fired.add(("reconciled",))
    seeker.memes["relief"] += 1
    friend.memes["relief"] += 1
    seeker.memes["trust"] += 2
    friend.memes["trust"] += 2
    world.facts["outcome"] = "reconciled"
    return []


CAUSAL_RULES = [
    Rule(name="suspicion_softens", tag="emotional", apply=_r_suspicion_softens),
    Rule(name="memory_wakes", tag="emotional", apply=_r_memory_wakes),
    Rule(name="reconciliation", tag="social", apply=_r_reconciliation),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def marker_can_show(marker: MarkerCfg, symbol: SymbolCfg) -> bool:
    return symbol.id in marker.supports


def valid_combo(symbol: SymbolCfg, keepsake: KeepsakeCfg, marker: MarkerCfg) -> bool:
    return marker.hill_safe and marker_can_show(marker, symbol)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sym_id, sym in SYMBOLS.items():
        for keep_id, keep in KEEPSAKES.items():
            for marker_id, marker in MARKERS.items():
                if valid_combo(sym, keep, marker):
                    combos.append((sym_id, keep_id, marker_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    symbol = SYMBOLS.get(params.symbol)
    keepsake = KEEPSAKES.get(params.keepsake)
    marker = MARKERS.get(params.marker)
    helper = HELPERS.get(params.helper)
    if symbol is None or keepsake is None or marker is None or helper is None:
        return "unresolved"
    return "reconciled" if valid_combo(symbol, keepsake, marker) else "unresolved"


def explain_rejection(symbol: SymbolCfg, marker: MarkerCfg) -> str:
    if not marker.hill_safe:
        return (
            f"(No story: {marker.label} are too flimsy for a steep hill path. "
            f"The wind can scatter them, so the mystery trail would not hold together.)"
        )
    return (
        f"(No story: {marker.label} cannot clearly carry the {symbol.label} symbol. "
        f"The clue must stay readable all the way up the hill.)"
    )


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def set_scene(world: World, seeker: Entity, friend: Entity, keepsake: KeepsakeCfg) -> None:
    world.say(
        f"The steep hill path climbed between rough stones and bent grass, and the morning air felt cool enough to keep every whisper. "
        f"{seeker.id} walked there alone, thinking about {keepsake.phrase} and about {friend.id}."
    )
    world.say(
        f"The day before, the keepsake had gone missing, and in a burst of hurt {seeker.id} had blamed {friend.id}. "
        f"Now the path felt like a mystery with its mouth shut."
    )


def establish_hurt(world: World, seeker: Entity, friend: Entity) -> None:
    seeker.memes["worry"] += 1
    seeker.memes["suspicion"] += 2
    friend.memes["hurt"] += 2
    seeker.memes["regret_seed"] += 1
    world.facts["quarrel"] = True


def first_clue(world: World, seeker: Entity, symbol: SymbolCfg, marker: MarkerCfg) -> None:
    seeker.meters["clues_seen"] += 1
    seeker.meters["distance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near the first bend, {seeker.id} noticed {marker.clue_text}: {symbol.shape_text}. "
        f"It was too careful to be an accident."
    )
    world.say(
        f"{seeker.pronoun().capitalize()} stopped and stared. A sign on a lonely path could have meant anything, and that made it feel even stranger."
    )


def second_clue(world: World, seeker: Entity, symbol: SymbolCfg, marker: MarkerCfg) -> None:
    seeker.meters["clues_seen"] += 1
    seeker.meters["distance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Higher up the steep hill path, another clue waited on the next turn: again the {symbol.label}, again made with {marker.label}."
    )
    if seeker.memes["remembering"] >= THRESHOLD:
        world.say(
            f"Then a memory opened. It was {symbol.memory_text}, and for the first time the mystery felt less sharp than sad."
        )
    else:
        world.say(
            f"{seeker.id} felt a small shiver. Two clues in the same shape meant someone had planned them."
        )


def third_clue(world: World, seeker: Entity, symbol: SymbolCfg, marker: MarkerCfg) -> None:
    seeker.meters["clues_seen"] += 1
    seeker.meters["distance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"By the last rise, a third clue waited where the path narrowed. It pointed uphill without using any words at all."
    )
    world.say(
        f"{seeker.id}'s steps slowed, but {seeker.pronoun('possessive')} fear had already started giving way to curiosity. "
        f"If the trail belonged to {friend.id}, then perhaps it was asking to be followed, not feared."
    )


def arrive_top(world: World, seeker: Entity, friend: Entity, symbol: SymbolCfg, keepsake: KeepsakeCfg, helper: HelperCfg) -> None:
    helper_ent = world.get("helper")
    world.say(helper.arrival_text)
    world.say(
        f"Inside, a cup of cappuccino sent up a sweet cloud of steam, and on top of the foam sat {symbol.foam_text}."
    )
    world.say(
        f"Beside the cup stood {friend.id}, holding {keepsake.phrase}. The answer had been waiting at the top all along."
    )
    world.facts["cappuccino_seen"] = True
    world.facts["helper_line"] = helper.reveal_text


def reveal_truth(world: World, seeker: Entity, friend: Entity, symbol: SymbolCfg, keepsake: KeepsakeCfg, marker: MarkerCfg, helper: HelperCfg) -> None:
    keepsake_ent = world.get("keepsake")
    keepsake_ent.meters["found"] = 1
    world.say(
        f'"I found it {keepsake.found_place}," {friend.id} said softly. "{marker.reveal_text} I did not know how to start talking after what happened yesterday."'
    )
    world.say(
        f"{helper.label.capitalize()} nodded and kept the room gentle and quiet. {helper.reveal_text}"
    )
    world.say(keepsake.repair_text)
    world.facts["found_place"] = keepsake.found_place
    world.facts["friend_explained"] = True


def apologize(world: World, seeker: Entity, friend: Entity) -> None:
    seeker.memes["apology"] += 1
    seeker.memes["regret"] += 1
    friend.memes["forgiveness"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{seeker.id} felt the old blame fall away. "I was wrong to blame you," {seeker.pronoun()} said. "I was scared, and I made the scary part into your fault."'
    )
    world.say(
        f'{friend.id} looked hurt for one more quiet second, then breathed out. "I was hurt," {friend.pronoun()} admitted, "but I wanted us to fix it."'
    )


def return_keepsake(world: World, seeker: Entity, friend: Entity) -> None:
    keepsake_ent = world.get("keepsake")
    keepsake_ent.meters["returned"] = 1
    propagate(world, narrate=False)
    world.say(
        f"{friend.id} placed the keepsake in {seeker.id}'s hands instead of hanging on to it. That small trusting motion finished what the clues had started."
    )


def ending(world: World, seeker: Entity, friend: Entity, symbol: SymbolCfg) -> None:
    seeker.memes["peace"] += 1
    friend.memes["peace"] += 1
    world.say(
        f"When they stepped back outside, the steep hill path no longer looked secretive. It only looked steep, bright, and ready to carry two friends down together."
    )
    world.say(
        f"As they began the walk home, {seeker.id} glanced once more at the remembered {symbol.label} and smiled. It was a symbol again, but not a warning now — a promise kept."
    )


def tell(
    *,
    symbol: SymbolCfg,
    keepsake: KeepsakeCfg,
    marker: MarkerCfg,
    helper: HelperCfg,
    seeker_name: str,
    seeker_gender: str,
    friend_name: str,
    friend_gender: str,
    seeker_trait: str,
    friend_trait: str,
) -> World:
    world = World()

    seeker = world.add(
        Entity(
            id="seeker",
            kind="character",
            type=seeker_gender,
            label=seeker_name,
            role="seeker",
            attrs={"name": seeker_name, "trait": seeker_trait},
            tags={"child"},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            attrs={"name": friend_name, "trait": friend_trait},
            tags={"child"},
        )
    )
    helper_ent = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper.type,
            label=helper.label,
            role="helper",
            tags=set(helper.tags),
        )
    )
    keepsake_ent = world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            label=keepsake.label,
            role="keepsake",
            tags=set(keepsake.tags),
        )
    )
    trail = world.add(
        Entity(
            id="trail",
            kind="thing",
            type="path",
            label="steep hill path",
            role="place",
            tags={"steep_hill"},
        )
    )

    seeker.meters["clues_seen"] = 0
    seeker.meters["distance"] = 0
    keepsake_ent.meters["found"] = 0
    keepsake_ent.meters["returned"] = 0
    trail.meters["steepness"] = 1
    trail.meters["height"] = 1
    seeker.memes["suspicion"] = 0
    seeker.memes["curiosity"] = 0
    seeker.memes["remembering"] = 0
    seeker.memes["hope"] = 0
    seeker.memes["apology"] = 0
    seeker.memes["trust"] = 0
    friend.memes["hurt"] = 0
    friend.memes["forgiveness"] = 0
    friend.memes["trust"] = 0

    world.facts.update(
        symbol=symbol,
        keepsake_cfg=keepsake,
        marker=marker,
        helper=helper,
        seeker=seeker,
        friend=friend,
        helper_entity=helper_ent,
        keepsake=keepsake_ent,
        place="steep hill path",
        outcome="unresolved",
    )

    establish_hurt(world, seeker, friend)
    set_scene(world, seeker, friend, keepsake)

    world.para()
    first_clue(world, seeker, symbol, marker)
    second_clue(world, seeker, symbol, marker)
    third_clue(world, seeker, symbol, marker)

    world.para()
    arrive_top(world, seeker, friend, symbol, keepsake, helper)
    reveal_truth(world, seeker, friend, symbol, keepsake, marker, helper)
    apologize(world, seeker, friend)
    return_keepsake(world, seeker, friend)

    world.para()
    ending(world, seeker, friend, symbol)

    world.facts["clues_seen"] = int(seeker.meters["clues_seen"])
    world.facts["reconciled"] = world.facts.get("outcome") == "reconciled"
    return world


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    symbol: str
    keepsake: str
    marker: str
    helper: str
    seeker_name: str
    seeker_gender: str
    friend_name: str
    friend_gender: str
    seeker_trait: str = "curious"
    friend_trait: str = "gentle"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "symbol": [
        (
            "What is a symbol?",
            "A symbol is a mark or shape that stands for an idea, a message, or a memory. People use symbols when they want one small sign to mean something bigger.",
        )
    ],
    "cappuccino": [
        (
            "What is a cappuccino?",
            "A cappuccino is a coffee drink made with milk foam on top. Grown-ups often drink it warm, and the foam can hold a little pattern for a moment.",
        )
    ],
    "chalk": [
        (
            "Why does chalk show up well on rocks?",
            "Chalk is pale and dusty, so it can make bright marks on a dark rock. That makes it easy to spot from a little distance.",
        )
    ],
    "pebbles": [
        (
            "Why can pebbles make a good trail clue?",
            "Pebbles are small stones that stay put better than paper in the wind. If someone arranges them carefully, they can point the way without using words.",
        )
    ],
    "ribbon": [
        (
            "Why might a tied ribbon stay on a windy path?",
            "If a ribbon is knotted tightly around something sturdy, it can stay in place better than a loose paper note. The knot helps the clue last longer.",
        )
    ],
    "steep_hill": [
        (
            "What is a steep hill path?",
            "A steep hill path is a walking path that climbs sharply upward. It can make the walk slower, and every turn can hide what is farther ahead.",
        )
    ],
    "apology": [
        (
            "Why does an apology help after a quarrel?",
            "An apology tells the hurt person that you know your choice caused pain. It cannot erase the moment, but it can begin to rebuild trust.",
        )
    ],
    "cafe": [
        (
            "What is a café?",
            "A café is a small place where people can sit, rest, and have drinks or snacks. It can feel warm and safe after a long walk outside.",
        )
    ],
}
KNOWLEDGE_ORDER = ["symbol", "cappuccino", "chalk", "pebbles", "ribbon", "steep_hill", "apology", "cafe"]


def generation_prompts(world: World) -> list[str]:
    symbol = world.facts["symbol"]
    keepsake = world.facts["keepsake_cfg"]
    seeker = world.facts["seeker"]
    friend = world.facts["friend"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old set on a steep hill path. Include the words "cappuccino" and "symbol".',
        f"Tell a mystery where {seeker.label} follows a trail of {symbol.label} clues after a quarrel with {friend.label}, and the trail leads to reconciliation.",
        f"Write a child-facing story about a missing {keepsake.label}, a repeating symbol, and two friends making peace at the top of a hill.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    seeker = world.facts["seeker"]
    friend = world.facts["friend"]
    symbol = world.facts["symbol"]
    keepsake = world.facts["keepsake_cfg"]
    marker = world.facts["marker"]
    helper = world.facts["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.label} and {friend.label}, two children who had a quarrel after {keepsake.label} went missing. The mystery begins because {seeker.label} walks the steep hill path still thinking about that hurt moment.",
        ),
        (
            f"Why did the steep hill path feel mysterious to {seeker.label}?",
            f"It felt mysterious because a trail of {symbol.label} clues kept appearing higher and higher up the hill. Each clue seemed planned, so {seeker.label} knew someone wanted to be followed.",
        ),
        (
            f"What changed in {seeker.label}'s feelings while following the clues?",
            f"At first {seeker.label} felt suspicious and worried. After seeing the same sign again and remembering what it used to mean, suspicion softened into curiosity and hope.",
        ),
        (
            "What was waiting at the top?",
            f"At the top there was a little café, {helper.label}, and a cup of cappuccino with the same {symbol.label} shape on the foam. {friend.label} was there too, holding the missing {keepsake.label}, so the mystery finally made sense.",
        ),
        (
            f"How did {friend.label} try to make peace?",
            f"{friend.label} found the missing {keepsake.label} {keepsake.found_place} and left a trail of {marker.label} to guide {seeker.label} uphill. That gave the apology a path to follow before either child had to say the hardest words.",
        ),
        (
            "How was the quarrel resolved?",
            f"{seeker.label} apologized for blaming {friend.label}, and {friend.label} admitted being hurt but still wanting to fix things. When the keepsake was returned, the two children could trust each other again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"symbol", "steep_hill", "apology", "cappuccino", "cafe"}
    marker = world.facts["marker"]
    tags |= set(marker.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        symbol="spiral",
        keepsake="sketchbook",
        marker="chalk",
        helper="keeper",
        seeker_name="Mira",
        seeker_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        seeker_trait="curious",
        friend_trait="gentle",
    ),
    StoryParams(
        symbol="star",
        keepsake="friendship_badge",
        marker="pebbles",
        helper="aunt",
        seeker_name="Leo",
        seeker_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        seeker_trait="thoughtful",
        friend_trait="quiet",
    ),
    StoryParams(
        symbol="leaf",
        keepsake="compass_charm",
        marker="chalk",
        helper="grandpa",
        seeker_name="Ivy",
        seeker_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        seeker_trait="careful",
        friend_trait="gentle",
    ),
    StoryParams(
        symbol="spiral",
        keepsake="friendship_badge",
        marker="ribbon",
        helper="keeper",
        seeker_name="Sam",
        seeker_gender="boy",
        friend_name="June",
        friend_gender="girl",
        seeker_trait="stubborn",
        friend_trait="thoughtful",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Sym, Keep, Marker) :- symbol(Sym), keepsake(Keep), marker(Marker),
                            hill_safe(Marker), supports(Marker, Sym).

outcome(reconciled) :- chosen_symbol(Sym), chosen_keepsake(Keep), chosen_marker(Marker),
                       chosen_helper(_), valid(Sym, Keep, Marker).
outcome(unresolved) :- chosen_symbol(Sym), chosen_keepsake(Keep), chosen_marker(Marker),
                       chosen_helper(_), not valid(Sym, Keep, Marker).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SYMBOLS:
        lines.append(asp.fact("symbol", sid))
    for kid in KEEPSAKES:
        lines.append(asp.fact("keepsake", kid))
    for mid, marker in MARKERS.items():
        lines.append(asp.fact("marker", mid))
        if marker.hill_safe:
            lines.append(asp.fact("hill_safe", mid))
        for sym in sorted(marker.supports):
            lines.append(asp.fact("supports", mid, sym))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_symbol", params.symbol),
            asp.fact("chosen_keepsake", params.keepsake),
            asp.fact("chosen_marker", params.marker),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
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
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        smoke_sample = generate(smoke_params)
        with redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=False, qa=True, header="smoke")
        if not smoke_sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery story world: a repeating symbol, a steep hill path, and reconciliation."
    )
    ap.add_argument("--symbol", choices=SYMBOLS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--seeker-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.symbol and args.marker:
        if not valid_combo(SYMBOLS[args.symbol], KEEPSAKES[next(iter(KEEPSAKES))], MARKERS[args.marker]):
            raise StoryError(explain_rejection(SYMBOLS[args.symbol], MARKERS[args.marker]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.symbol is None or combo[0] == args.symbol)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.marker is None or combo[2] == args.marker)
    ]
    if not combos:
        if args.symbol and args.marker:
            raise StoryError(explain_rejection(SYMBOLS[args.symbol], MARKERS[args.marker]))
        raise StoryError("(No valid combination matches the given options.)")

    symbol_id, keepsake_id, marker_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS.keys()))
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    seeker_name = args.seeker_name or _pick_name(rng, seeker_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=seeker_name)
    seeker_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != seeker_trait] or TRAITS)

    return StoryParams(
        symbol=symbol_id,
        keepsake=keepsake_id,
        marker=marker_id,
        helper=helper_id,
        seeker_name=seeker_name,
        seeker_gender=seeker_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        seeker_trait=seeker_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    symbol = SYMBOLS.get(params.symbol)
    keepsake = KEEPSAKES.get(params.keepsake)
    marker = MARKERS.get(params.marker)
    helper = HELPERS.get(params.helper)
    if symbol is None:
        raise StoryError(f"(Unknown symbol: {params.symbol})")
    if keepsake is None:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if marker is None:
        raise StoryError(f"(Unknown marker: {params.marker})")
    if helper is None:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not valid_combo(symbol, keepsake, marker):
        raise StoryError(explain_rejection(symbol, marker))

    world = tell(
        symbol=symbol,
        keepsake=keepsake,
        marker=marker,
        helper=helper,
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        seeker_trait=params.seeker_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (symbol, keepsake, marker) combos:\n")
        for symbol, keepsake, marker in combos:
            print(f"  {symbol:8} {keepsake:16} {marker}")
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
            header = f"### {p.seeker_name} and {p.friend_name}: {p.symbol} trail with {p.marker} ({p.keepsake})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
