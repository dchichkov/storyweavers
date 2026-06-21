#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dingy_harrow_friendship_reconciliation_problem_solving_mystery.py
================================================================================================

A standalone storyworld about a small mystery between two friends: a treasured
planning item goes missing in a farm outbuilding, one friend hurts the other's
feelings with a quick accusation, and the pair must solve the mystery together
to make up.

The seed asked for:
- words: "dingy", "harrow"
- features: Friendship, Reconciliation, Problem Solving
- style: Mystery

This world keeps the domain deliberately small and concrete. The children are in
a dingy barn loft or shed corner, an item vanishes, clues point away from blame
and toward a simple physical explanation, and the ending image proves that both
the object and the friendship were recovered.

Run it
------
    python storyworlds/worlds/gpt-5.4/dingy_harrow_friendship_reconciliation_problem_solving_mystery.py
    python storyworlds/worlds/gpt-5.4/dingy_harrow_friendship_reconciliation_problem_solving_mystery.py --setting barn --item map
    python storyworlds/worlds/gpt-5.4/dingy_harrow_friendship_reconciliation_problem_solving_mystery.py --culprit goat --spot rafters
    python storyworlds/worlds/gpt-5.4/dingy_harrow_friendship_reconciliation_problem_solving_mystery.py --all
    python storyworlds/worlds/gpt-5.4/dingy_harrow_friendship_reconciliation_problem_solving_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dingy_harrow_friendship_reconciliation_problem_solving_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/dingy_harrow_friendship_reconciliation_problem_solving_mystery.py --verify
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
    movable: bool = True
    # world state axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"cat", "goat", "crow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    clubhouse: str
    entry_sound: str
    clue_surface: str
    has_rafters: bool = False
    has_hay: bool = False
    has_harrow: bool = False
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
class MissingItem:
    id: str
    label: str
    phrase: str
    use: str
    lure: str
    light: bool
    size: str
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
    type: str
    movement: str
    clue: str
    sound: str
    likes_shiny: bool = False
    likes_paper: bool = False
    likes_fabric: bool = False
    reaches_high: bool = False
    burrows_low: bool = False
    noses_around: bool = False
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
    clue_detail: str
    needs_high: bool = False
    needs_low: bool = False
    needs_hay: bool = False
    needs_harrow: bool = False
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"friend_a", "friend_b"}]

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
        clone.history = list(self.history)
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


def _r_missing_strain(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    a = world.get("friend_a")
    b = world.get("friend_b")
    if item.meters["missing"] >= THRESHOLD and a.memes["accused"] >= THRESHOLD:
        sig = ("strain",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["worry"] += 1
            b.memes["hurt"] += 1
            a.memes["distance"] += 1
            b.memes["distance"] += 1
            out.append("__strain__")
    return out


def _r_clues_build_reason(world: World) -> list[str]:
    out: list[str] = []
    investigator = world.get("friend_a")
    if investigator.meters["clues_found"] >= 2 and investigator.memes["distance"] >= THRESHOLD:
        sig = ("reason",)
        if sig not in world.fired:
            world.fired.add(sig)
            investigator.memes["understanding"] += 1
            out.append("__reason__")
    return out


def _r_apology_repair(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("friend_a")
    b = world.get("friend_b")
    item = world.get("item")
    if item.meters["found"] >= THRESHOLD and a.memes["sorry"] >= THRESHOLD:
        sig = ("repair",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["distance"] = 0.0
            b.memes["distance"] = 0.0
            a.memes["relief"] += 1
            b.memes["relief"] += 1
            a.memes["friendship"] += 1
            b.memes["friendship"] += 1
            out.append("__repair__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_strain", tag="social", apply=_r_missing_strain),
    Rule(name="clues_build_reason", tag="mental", apply=_r_clues_build_reason),
    Rule(name="apology_repair", tag="social", apply=_r_apology_repair),
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


SETTINGS = {
    "barn": Setting(
        id="barn",
        place="the old barn",
        mood="a dingy loft above the stalls",
        clubhouse="their secret loft club",
        entry_sound="the boards gave a low creak",
        clue_surface="dusty floorboards",
        has_rafters=True,
        has_hay=True,
        has_harrow=True,
        tags={"barn", "mystery"},
    ),
    "shed": Setting(
        id="shed",
        place="the tool shed",
        mood="a dingy back corner beside sacks of seed",
        clubhouse="their rainy-day planning corner",
        entry_sound="the latch clicked and the door sighed",
        clue_surface="the dusty plank floor",
        has_rafters=False,
        has_hay=False,
        has_harrow=True,
        tags={"shed", "mystery"},
    ),
    "stable": Setting(
        id="stable",
        place="the stable room",
        mood="a dingy tack nook that smelled of hay and leather",
        clubhouse="their quiet nook by the window",
        entry_sound="the half-door tapped in the wind",
        clue_surface="the straw-dusted floor",
        has_rafters=False,
        has_hay=True,
        has_harrow=False,
        tags={"stable", "mystery"},
    ),
}

ITEMS = {
    "map": MissingItem(
        id="map",
        label="map",
        phrase="their hand-drawn mystery map",
        use="follow clues to the hidden berry patch",
        lure="crinkly paper edges",
        light=False,
        size="flat",
        tags={"map", "paper"},
    ),
    "ribbon": MissingItem(
        id="ribbon",
        label="blue ribbon",
        phrase="a bright blue ribbon for their prize jar",
        use="tie the prize jar closed at the end",
        lure="fluttering cloth",
        light=False,
        size="light",
        tags={"ribbon", "fabric"},
    ),
    "bell": MissingItem(
        id="bell",
        label="bell",
        phrase="a little brass bell for their secret signal",
        use="ring the start of the game",
        lure="a tiny shiny gleam",
        light=True,
        size="small",
        tags={"bell", "shiny"},
    ),
}

CULPRITS = {
    "crow": Culprit(
        id="crow",
        label="crow",
        type="crow",
        movement="hopped and flapped",
        clue="a black feather",
        sound="a sharp caw from above",
        likes_shiny=True,
        likes_paper=True,
        reaches_high=True,
        tags={"bird", "crow"},
    ),
    "goat": Culprit(
        id="goat",
        label="goat",
        type="goat",
        movement="nudged and tugged",
        clue="a chewed corner and a few white hairs",
        sound="a muffled bleat nearby",
        likes_paper=True,
        likes_fabric=True,
        noses_around=True,
        tags={"goat", "farm_animal"},
    ),
    "cat": Culprit(
        id="cat",
        label="barn cat",
        type="cat",
        movement="slipped and pounced",
        clue="small pawprints in the dust",
        sound="a soft mew under something low",
        likes_fabric=True,
        burrows_low=True,
        tags={"cat", "farm_animal"},
    ),
}

SPOTS = {
    "rafters": Spot(
        id="rafters",
        label="rafters",
        phrase="up in the rafters, tucked beside an old nest",
        clue_detail="The clue pointed upward.",
        needs_high=True,
        tags={"high"},
    ),
    "harrow": Spot(
        id="harrow",
        label="harrow",
        phrase="under the old harrow leaning by the wall",
        clue_detail="The clue pointed to a low metal shadow.",
        needs_low=True,
        needs_harrow=True,
        tags={"harrow", "low"},
    ),
    "hay": Spot(
        id="hay",
        label="hay bale",
        phrase="inside a split hay bale by the window",
        clue_detail="The clue pointed to the sweet-smelling hay.",
        needs_low=True,
        needs_hay=True,
        tags={"hay", "low"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Theo", "Finn", "Max", "Noah", "Eli"]
TRAITS = ["careful", "bright", "patient", "curious", "steady", "kind"]


def culprit_moves_item(culprit: Culprit, item: MissingItem) -> bool:
    if item.id == "bell":
        return culprit.likes_shiny or culprit.likes_fabric
    if item.id == "map":
        return culprit.likes_paper
    if item.id == "ribbon":
        return culprit.likes_fabric
    return False


def spot_fits(setting: Setting, culprit: Culprit, spot: Spot) -> bool:
    if spot.needs_high and not culprit.reaches_high:
        return False
    if spot.needs_low and not (culprit.burrows_low or culprit.noses_around):
        return False
    if spot.needs_hay and not setting.has_hay:
        return False
    if spot.needs_harrow and not setting.has_harrow:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for culprit_id, culprit in CULPRITS.items():
                if not culprit_moves_item(culprit, item):
                    continue
                for spot_id, spot in SPOTS.items():
                    if spot_fits(setting, culprit, spot):
                        combos.append((setting_id, item_id, culprit_id, spot_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    item: str
    culprit: str
    spot: str
    friend_a: str
    friend_a_gender: str
    friend_b: str
    friend_b_gender: str
    trait_a: str
    trait_b: str
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


def explain_invalid(setting: Setting, item: MissingItem, culprit: Culprit, spot: Spot) -> str:
    if not culprit_moves_item(culprit, item):
        return (
            f"(No story: a {culprit.label} would not reasonably carry {item.phrase}. "
            f"This mystery depends on real clues, so pick a culprit that would be drawn to it.)"
        )
    if spot.needs_high and not culprit.reaches_high:
        return (
            f"(No story: {culprit.label} cannot reach {spot.label}. "
            f"The hiding place has to match how the culprit moves.)"
        )
    if spot.needs_low and not (culprit.burrows_low or culprit.noses_around):
        return (
            f"(No story: {culprit.label} would not hide things in {spot.label}. "
            f"The hiding place has to fit the culprit's habits.)"
        )
    if spot.needs_hay and not setting.has_hay:
        return (
            f"(No story: {setting.place} has no hay bale, so that clue trail would not make sense there.)"
        )
    if spot.needs_harrow and not setting.has_harrow:
        return (
            f"(No story: {setting.place} has no harrow, so that ending image cannot happen there.)"
        )
    return "(No story: that combination does not make a reasonable mystery.)"


ASP_RULES = r"""
moves_item(C,I) :- culprit(C), item(I), likes_shiny(C), shiny(I).
moves_item(C,I) :- culprit(C), item(I), likes_paper(C), paper(I).
moves_item(C,I) :- culprit(C), item(I), likes_fabric(C), fabric(I).

spot_ok(S,C,P) :- setting(S), culprit(C), spot(P),
                  not needs_high(P), not needs_low(P), not needs_hay(P), not needs_harrow(P).
spot_ok(S,C,P) :- setting(S), culprit(C), spot(P),
                  needs_high(P), reaches_high(C),
                  not needs_low(P), not needs_hay(P), not needs_harrow(P).
spot_ok(S,C,P) :- setting(S), culprit(C), spot(P),
                  needs_low(P), low_hider(C),
                  not needs_high(P), not needs_hay(P), not needs_harrow(P).
spot_ok(S,C,P) :- setting(S), culprit(C), spot(P),
                  needs_low(P), low_hider(C), needs_hay(P), has_hay(S),
                  not needs_high(P), not needs_harrow(P).
spot_ok(S,C,P) :- setting(S), culprit(C), spot(P),
                  needs_low(P), low_hider(C), needs_harrow(P), has_harrow(S),
                  not needs_high(P), not needs_hay(P).

valid(S,I,C,P) :- setting(S), item(I), culprit(C), spot(P), moves_item(C,I), spot_ok(S,C,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.has_hay:
            lines.append(asp.fact("has_hay", sid))
        if setting.has_harrow:
            lines.append(asp.fact("has_harrow", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if "shiny" in item.tags:
            lines.append(asp.fact("shiny", iid))
        if "paper" in item.tags:
            lines.append(asp.fact("paper", iid))
        if "fabric" in item.tags:
            lines.append(asp.fact("fabric", iid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        if culprit.likes_shiny:
            lines.append(asp.fact("likes_shiny", cid))
        if culprit.likes_paper:
            lines.append(asp.fact("likes_paper", cid))
        if culprit.likes_fabric:
            lines.append(asp.fact("likes_fabric", cid))
        if culprit.reaches_high:
            lines.append(asp.fact("reaches_high", cid))
        if culprit.burrows_low or culprit.noses_around:
            lines.append(asp.fact("low_hider", cid))
    for pid, spot in SPOTS.items():
        lines.append(asp.fact("spot", pid))
        if spot.needs_high:
            lines.append(asp.fact("needs_high", pid))
        if spot.needs_low:
            lines.append(asp.fact("needs_low", pid))
        if spot.needs_hay:
            lines.append(asp.fact("needs_hay", pid))
        if spot.needs_harrow:
            lines.append(asp.fact("needs_harrow", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def predict_clue_count(setting: Setting, culprit: Culprit, spot: Spot) -> int:
    clues = 1
    if culprit.sound:
        clues += 1
    if spot.needs_hay and setting.has_hay:
        clues += 1
    if spot.needs_harrow and setting.has_harrow:
        clues += 1
    if spot.needs_high and setting.has_rafters:
        clues += 1
    return clues


def introduce(world: World, a: Entity, b: Entity, item: MissingItem) -> None:
    setting = world.setting
    world.say(
        f"One gray afternoon, {a.id} and {b.id} climbed into {setting.mood} in {setting.place}. "
        f"It was {setting.clubhouse}, and the place felt wonderfully mysterious."
    )
    world.say(
        f"They had brought {item.phrase} so they could {item.use}. "
        f"When {setting.entry_sound}, they huddled close and grinned at their secret plan."
    )


def friendship_setup(world: World, a: Entity, b: Entity) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"{a.id} trusted {b.id} to notice small things, and {b.id} trusted {a.id} to keep brave hands steady. "
        f"That was why they made such a good team."
    )


def item_goes_missing(world: World, a: Entity, b: Entity, item: Entity, culprit: Culprit) -> None:
    item.meters["missing"] += 1
    world.facts["missing_before"] = True
    world.facts["first_sound"] = culprit.sound
    world.say(
        f"But when {a.id} reached for the {item.label}, it was gone. "
        f"Only an empty patch lay on {world.setting.clue_surface} where it had been."
    )


def accuse(world: World, a: Entity, b: Entity, item_cfg: MissingItem) -> None:
    a.memes["accused"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Did you move the {item_cfg.label}?" {a.id} asked too fast. '
        f'"You were standing closest."'
    )
    world.say(
        f"{b.id}'s face fell. "
        f'"No," {b.pronoun()} said. "I would have told you."'
    )


def choose_to_solve(world: World, a: Entity, b: Entity) -> None:
    a.memes["investigate"] += 1
    b.memes["investigate"] += 1
    world.say(
        f"For a moment the dingy room felt colder than before. "
        f"Then {b.id} took a breath and said, "
        f'"Instead of guessing, let\'s solve it."'
    )
    world.say(
        f"{a.id} nodded. It was the first good idea since the trouble had started."
    )


def find_first_clue(world: World, a: Entity, culprit: Culprit) -> None:
    a.meters["clues_found"] += 1
    world.history.append(culprit.clue)
    world.say(
        f"Together they crouched down. On the floor they found {culprit.clue}. "
        f"That clue did not belong to either child."
    )


def find_second_clue(world: World, a: Entity, setting: Setting, culprit: Culprit, spot: Spot) -> None:
    a.meters["clues_found"] += 1
    propagate(world, narrate=False)
    extra = spot.clue_detail
    world.history.append(culprit.sound)
    world.say(
        f"Then they heard {culprit.sound}. {extra} "
        f"{a.id} looked from the sound to the marks on {setting.clue_surface}, and the pieces began to fit."
    )


def reason_out(world: World, a: Entity, b: Entity, culprit: Culprit, item: MissingItem, spot: Spot) -> None:
    a.memes["reasoning"] += 1
    b.memes["reasoning"] += 1
    if spot.id == "rafters":
        because = f"The {culprit.label} liked {item.lure} and could reach high places."
    elif spot.id == "harrow":
        because = f"The {culprit.label} could nose things into low places, and the old harrow made a dark hiding shadow."
    else:
        because = f"The {culprit.label} could tug small things into soft places, and the hay would hide them well."
    world.say(
        f'"It was not you," {a.id} said at last. "{because}"'
    )
    world.say(
        f"Now the mystery had an answer they could test, not just a hurt feeling to sit with."
    )


def recover_item(world: World, a: Entity, b: Entity, item: Entity, item_cfg: MissingItem, spot: Spot) -> None:
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    world.facts["found_spot"] = spot.label
    world.say(
        f"They searched {spot.phrase}, and there was {item_cfg.phrase}. "
        f"{b.id} picked it up carefully while {a.id} laughed with relief."
    )


def apologize(world: World, a: Entity, b: Entity) -> None:
    a.memes["sorry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{a.id} looked at {b.id} and swallowed. '
        f'"I am sorry I blamed you before we looked for clues," {a.pronoun()} said. '
        f'"That was not fair."'
    )
    world.say(
        f'{b.id} gave a small nod. "Thank you for saying that," {b.pronoun()} answered. '
        f'"I was hurt, but I still wanted to help."'
    )


def reconcile(world: World, a: Entity, b: Entity, item_cfg: MissingItem) -> None:
    world.say(
        f"Then the tight feeling between them loosened. "
        f"They spread {item_cfg.phrase} between them again, this time shoulder to shoulder."
    )
    world.say(
        f"The mystery was solved, but the better thing was this: they were acting like friends again."
    )


def ending_image(world: World, a: Entity, b: Entity, item_cfg: MissingItem, spot: Spot) -> None:
    tag = "the old harrow" if spot.id == "harrow" else spot.label
    world.say(
        f"Soon they were back to their plan, whispering over {item_cfg.label} lines and laughing whenever a floorboard creaked. "
        f"Behind them, {tag} stayed quiet, and the dingy room no longer felt lonely at all."
    )


def tell(
    setting: Setting,
    item_cfg: MissingItem,
    culprit_cfg: Culprit,
    spot_cfg: Spot,
    friend_a: str = "Lily",
    friend_a_gender: str = "girl",
    friend_b: str = "Ben",
    friend_b_gender: str = "boy",
    trait_a: str = "careful",
    trait_b: str = "curious",
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id="friend_a",
        kind="character",
        type=friend_a_gender,
        label=friend_a,
        role="friend_a",
        traits=[trait_a],
    ))
    b = world.add(Entity(
        id="friend_b",
        kind="character",
        type=friend_b_gender,
        label=friend_b,
        role="friend_b",
        traits=[trait_b],
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        role="missing_item",
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type=culprit_cfg.type,
        label=culprit_cfg.label,
        role="culprit",
    ))
    spot = world.add(Entity(
        id="spot",
        kind="thing",
        type="spot",
        label=spot_cfg.label,
        role="spot",
        movable=False,
    ))

    world.facts.update(
        setting=setting,
        item_cfg=item_cfg,
        culprit_cfg=culprit_cfg,
        spot_cfg=spot_cfg,
        friend_a_name=friend_a,
        friend_b_name=friend_b,
    )

    introduce(world, a, b, item_cfg)
    friendship_setup(world, a, b)

    world.para()
    item_goes_missing(world, a, b, item, culprit_cfg)
    accuse(world, a, b, item_cfg)
    choose_to_solve(world, a, b)

    world.para()
    find_first_clue(world, a, culprit_cfg)
    find_second_clue(world, a, setting, culprit_cfg, spot_cfg)
    reason_out(world, a, b, culprit_cfg, item_cfg, spot_cfg)

    world.para()
    recover_item(world, a, b, item, item_cfg, spot_cfg)
    apologize(world, a, b)
    reconcile(world, a, b, item_cfg)
    ending_image(world, a, b, item_cfg, spot_cfg)

    world.facts.update(
        friend_a=a,
        friend_b=b,
        item=item,
        culprit=culprit,
        spot=spot,
        clue_count=int(a.meters["clues_found"]),
        friendship_repaired=a.memes["friendship"] >= 2 and b.memes["friendship"] >= 2,
        apology=a.memes["sorry"] >= THRESHOLD,
        found=item.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "crow": [(
        "Why do crows sometimes take things?",
        "Crows notice bright or interesting objects and sometimes carry them away to inspect them. They are clever birds and like unusual little finds."
    )],
    "goat": [(
        "Why might a goat grab a ribbon or paper?",
        "Goats explore with their noses and mouths, so they may tug at loose things just to see what they are. That can move an object even if the goat does not want to keep it."
    )],
    "cat": [(
        "Why do cats bat small things under furniture?",
        "Cats like to pounce on light, fluttery objects and swipe them into hiding places. They are following play instincts, not trying to be mean."
    )],
    "map": [(
        "What does a map do?",
        "A map helps you find where things are. It turns places and paths into clues you can follow."
    )],
    "ribbon": [(
        "What is a ribbon used for?",
        "A ribbon can tie, mark, or decorate something. Because it is light and fluttery, it can also blow or get tugged away easily."
    )],
    "bell": [(
        "Why does a little bell make a good signal?",
        "A bell makes a clear sound that people can hear from across a room or yard. That is why it works well for calling someone or starting a game."
    )],
    "mystery": [(
        "What helps solve a mystery?",
        "You solve a mystery by noticing clues, asking what fits those clues, and checking your idea. Good problem solving means not guessing too soon."
    )],
    "apology": [(
        "Why does saying sorry matter in a friendship?",
        "A real apology shows that you understand the hurt you caused. It helps trust grow back when both people are honest and kind."
    )],
    "harrow": [(
        "What is a harrow?",
        "A harrow is a farm tool with metal teeth or bars used to break up soil. In an old shed or barn, it can make a dark place where small things get stuck underneath."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "map", "ribbon", "bell", "crow", "goat", "cat", "apology", "harrow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    return [
        f'Write a child-facing mystery story that includes the word "dingy" and the word "harrow".',
        f"Tell a gentle farm mystery where two friends in {setting.place} lose {item.phrase}, hurt each other's feelings for a moment, and then solve the problem together.",
        f"Write a story about friendship and reconciliation in which a quick accusation is corrected by clues, and the real culprit turns out to be a {culprit.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    item_cfg = f["item_cfg"]
    culprit_cfg = f["culprit_cfg"]
    spot_cfg = f["spot_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label}, two friends in {setting.place}. They start the story as a good team, and the mystery tests that friendship for a little while."
        ),
        (
            f"What went missing?",
            f"{item_cfg.phrase} went missing. The children needed it to {item_cfg.use}, so losing it spoiled their plan and started the mystery."
        ),
        (
            f"Why were {a.label} and {b.label} upset with each other?",
            f"{a.label} asked too quickly if {b.label} had moved the {item_cfg.label}. That hurt {b.label}'s feelings because {b.pronoun()} had done nothing wrong."
        ),
        (
            "How did they solve the mystery?",
            f"They stopped guessing and looked for clues together. They found {culprit_cfg.clue} and heard {culprit_cfg.sound}, which helped them work out where to search next."
        ),
        (
            f"Where did they find the missing {item_cfg.label}?",
            f"They found it {spot_cfg.phrase}. The hiding place fit the clues, so their idea turned into a real answer instead of just a guess."
        ),
        (
            "How did the friends make up?",
            f"{a.label} apologized for blaming {b.label} before checking the facts, and {b.label} accepted the apology. Their friendship felt steady again because they solved the problem side by side."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item_cfg = f["item_cfg"]
    culprit_cfg = f["culprit_cfg"]
    spot_cfg = f["spot_cfg"]
    tags = {"mystery", "apology"}
    tags |= set(item_cfg.tags)
    tags |= set(culprit_cfg.tags)
    if "harrow" in spot_cfg.tags:
        tags.add("harrow")
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
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="barn",
        item="map",
        culprit="goat",
        spot="harrow",
        friend_a="Lily",
        friend_a_gender="girl",
        friend_b="Ben",
        friend_b_gender="boy",
        trait_a="careful",
        trait_b="curious",
    ),
    StoryParams(
        setting="barn",
        item="bell",
        culprit="crow",
        spot="rafters",
        friend_a="Maya",
        friend_a_gender="girl",
        friend_b="Theo",
        friend_b_gender="boy",
        trait_a="bright",
        trait_b="steady",
    ),
    StoryParams(
        setting="stable",
        item="ribbon",
        culprit="cat",
        spot="hay",
        friend_a="Nora",
        friend_a_gender="girl",
        friend_b="Ella",
        friend_b_gender="girl",
        trait_a="patient",
        trait_b="kind",
    ),
    StoryParams(
        setting="shed",
        item="map",
        culprit="goat",
        spot="harrow",
        friend_a="Sam",
        friend_a_gender="boy",
        friend_b="Lucy",
        friend_b_gender="girl",
        trait_a="steady",
        trait_b="bright",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a gentle mystery about a missing object, a quick accusation, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.culprit and args.spot:
        setting = SETTINGS[args.setting]
        item = ITEMS[args.item]
        culprit = CULPRITS[args.culprit]
        spot = SPOTS[args.spot]
        if not (culprit_moves_item(culprit, item) and spot_fits(setting, culprit, spot)):
            raise StoryError(explain_invalid(setting, item, culprit, spot))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.spot is None or combo[3] == args.spot)
    ]
    if not combos:
        if args.setting and args.item and args.culprit and args.spot:
            raise StoryError(
                explain_invalid(
                    SETTINGS[args.setting],
                    ITEMS[args.item],
                    CULPRITS[args.culprit],
                    SPOTS[args.spot],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, culprit_id, spot_id = rng.choice(sorted(combos))
    gender_a = rng.choice(["girl", "boy"])
    gender_b = rng.choice(["girl", "boy"])
    name_a = _pick_name(rng, gender_a)
    name_b = _pick_name(rng, gender_b, avoid=name_a)
    trait_a = rng.choice(TRAITS)
    trait_b = rng.choice([t for t in TRAITS if t != trait_a] or TRAITS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        culprit=culprit_id,
        spot=spot_id,
        friend_a=name_a,
        friend_a_gender=gender_a,
        friend_b=name_b,
        friend_b_gender=gender_b,
        trait_a=trait_a,
        trait_b=trait_b,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Invalid culprit: {params.culprit})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")

    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    spot = SPOTS[params.spot]
    if not culprit_moves_item(culprit, item) or not spot_fits(setting, culprit, spot):
        raise StoryError(explain_invalid(setting, item, culprit, spot))

    world = tell(
        setting=setting,
        item_cfg=item,
        culprit_cfg=culprit,
        spot_cfg=spot,
        friend_a=params.friend_a,
        friend_a_gender=params.friend_a_gender,
        friend_b=params.friend_b,
        friend_b_gender=params.friend_b_gender,
        trait_a=params.trait_a,
        trait_b=params.trait_b,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for p in CURATED:
        try:
            generate(p)
        except Exception as err:
            rc = 1
            print(f"CURATED CASE FAILED: {p} -> {err}")
            break
    else:
        print(f"OK: curated generation passed ({len(CURATED)} cases).")

    for s in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            generate(params)
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {s}: {err}")
            break
    else:
        print("OK: random generation smoke test passed (25 seeds).")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, culprit, spot) combos:\n")
        for setting, item, culprit, spot in combos:
            print(f"  {setting:7} {item:6} {culprit:7} {spot}")
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
            header = f"### {p.friend_a} & {p.friend_b}: {p.item} in {p.setting} ({p.culprit}, {p.spot})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
