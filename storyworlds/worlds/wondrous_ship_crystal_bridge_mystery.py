#!/usr/bin/env python3
"""
storyworlds/worlds/wondrous_ship_crystal_bridge_mystery.py
==========================================================

A standalone storyworld sketch for a TinyStories-style mystery: a child must
discover why a wondrous ship cannot cross a crystal bridge. The tall-tale surface
is big and shiny, but the reasonableness gate is concrete: the ship must truly be
too heavy and unevenly loaded, the clue must point to both facts, and the fix
must make both facts safe before the bridge lets the ship cross.
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

    @property
    def name(self) -> str:
        return self.label or self.id

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Harbor:
    id: str
    label: str
    bridge: str
    bridge_phrase: str
    far_side: str
    keeper: str
    capacity: int
    tolerance: int
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Ship:
    id: str
    label: str
    phrase: str
    deck: str
    left_base: int
    right_base: int
    wonder: str
    horn: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Cargo:
    id: str
    label: str
    phrase: str
    left: int
    right: int
    clue_detail: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    find: str
    points_weight: bool
    points_balance: bool
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Fix:
    id: str
    label: str
    action: str
    qa_action: str
    unload: int
    move_left_to_right: int = 0
    move_right_to_left: int = 0
    lesson: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, params: "StoryParams") -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.params)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for ent in self.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if ent.role:
                bits.append(f"role={ent.role}")
            lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
        lines.append(f"  fired rules: {sorted(set(n for n, *_ in self.fired))}")
        return "\n".join(lines)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_bridge_refuses(world: World) -> list[str]:
    ship = world.get("ship")
    bridge = world.get("bridge")
    if ship.meters["attempted"] < THRESHOLD:
        return []
    if ship.meters["crossed"] >= THRESHOLD:
        return []
    too_heavy = ship.meters["total"] > bridge.meters["capacity"]
    unbalanced = ship.meters["imbalance"] > bridge.meters["tolerance"]
    if not (too_heavy or unbalanced):
        return []
    sig = ("refuse", too_heavy, unbalanced)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bridge.meters["humming"] += 1
    ship.memes["stuck"] += 1
    return ["__refused__"]


def _r_clue_understood(world: World) -> list[str]:
    hero = world.get("hero")
    clue = world.get("clue")
    if clue.meters["found"] < THRESHOLD:
        return []
    if not (clue.meters["points_weight"] and clue.meters["points_balance"]):
        return []
    sig = ("understand", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["insight"] += 1
    return ["__understood__"]


def _r_crosses_when_safe(world: World) -> list[str]:
    ship = world.get("ship")
    bridge = world.get("bridge")
    if ship.meters["adjusted"] < THRESHOLD:
        return []
    if ship.meters["total"] > bridge.meters["capacity"]:
        return []
    if ship.meters["imbalance"] > bridge.meters["tolerance"]:
        return []
    sig = ("cross", ship.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ship.meters["crossed"] += 1
    bridge.meters["settled"] += 1
    return ["__crossed__"]


CAUSAL_RULES = [
    Rule("bridge_refuses", "physical", _r_bridge_refuses),
    Rule("clue_understood", "mystery", _r_clue_understood),
    Rule("crosses_when_safe", "physical", _r_crosses_when_safe),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def total_load(ship: Ship, cargo: Cargo) -> int:
    return ship.left_base + ship.right_base + cargo.left + cargo.right


def imbalance(ship: Ship, cargo: Cargo) -> int:
    return abs((ship.left_base + cargo.left) - (ship.right_base + cargo.right))


def adjusted_sides(ship: Ship, cargo: Cargo, fix: Fix) -> tuple[int, int]:
    left = ship.left_base + cargo.left
    right = ship.right_base + cargo.right
    left -= fix.move_left_to_right
    right += fix.move_left_to_right
    right -= fix.move_right_to_left
    left += fix.move_right_to_left
    if fix.unload:
        heavier_left = left >= right
        if heavier_left:
            left -= fix.unload
        else:
            right -= fix.unload
    return max(0, left), max(0, right)


def adjusted_total(ship: Ship, cargo: Cargo, fix: Fix) -> int:
    left, right = adjusted_sides(ship, cargo, fix)
    return left + right


def adjusted_imbalance(ship: Ship, cargo: Cargo, fix: Fix) -> int:
    left, right = adjusted_sides(ship, cargo, fix)
    return abs(left - right)


def has_true_problem(harbor: Harbor, ship: Ship, cargo: Cargo) -> bool:
    return total_load(ship, cargo) > harbor.capacity and imbalance(ship, cargo) > harbor.tolerance


def clue_points_to_problem(clue: Clue) -> bool:
    return clue.points_weight and clue.points_balance


def fix_solves_problem(harbor: Harbor, ship: Ship, cargo: Cargo, fix: Fix) -> bool:
    return (
        adjusted_total(ship, cargo, fix) <= harbor.capacity
        and adjusted_imbalance(ship, cargo, fix) <= harbor.tolerance
    )


def valid_combo(harbor_id: str, ship_id: str, cargo_id: str, clue_id: str, fix_id: str) -> bool:
    harbor = HARBORS[harbor_id]
    ship = SHIPS[ship_id]
    cargo = CARGOES[cargo_id]
    clue = CLUES[clue_id]
    fix = FIXES[fix_id]
    return (
        has_true_problem(harbor, ship, cargo)
        and clue_points_to_problem(clue)
        and fix_solves_problem(harbor, ship, cargo, fix)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for harbor_id in HARBORS:
        for ship_id in SHIPS:
            for cargo_id in CARGOES:
                for clue_id in CLUES:
                    for fix_id in FIXES:
                        if valid_combo(harbor_id, ship_id, cargo_id, clue_id, fix_id):
                            combos.append((harbor_id, ship_id, cargo_id, clue_id, fix_id))
    return combos


def _article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


def _init_world(params: "StoryParams") -> tuple[World, Entity, Entity, Entity, Entity, Entity]:
    harbor = HARBORS[params.harbor]
    ship_cfg = SHIPS[params.ship]
    cargo = CARGOES[params.cargo]
    clue_cfg = CLUES[params.clue]
    world = World(params)
    hero = world.add(Entity("hero", "character", params.gender, params.name, "solver", [params.trait]))
    companion = world.add(Entity("companion", "character", "friend", params.companion, "helper"))
    bridge = world.add(Entity("bridge", "thing", "bridge", harbor.bridge, "bridge"))
    ship = world.add(Entity("ship", "thing", "ship", ship_cfg.label, "ship"))
    clue = world.add(Entity("clue", "thing", "clue", clue_cfg.label, "clue"))
    bridge.meters["capacity"] = float(harbor.capacity)
    bridge.meters["tolerance"] = float(harbor.tolerance)
    ship.meters["left"] = float(ship_cfg.left_base + cargo.left)
    ship.meters["right"] = float(ship_cfg.right_base + cargo.right)
    ship.meters["total"] = float(total_load(ship_cfg, cargo))
    ship.meters["imbalance"] = float(imbalance(ship_cfg, cargo))
    clue.meters["points_weight"] = 1.0 if clue_cfg.points_weight else 0.0
    clue.meters["points_balance"] = 1.0 if clue_cfg.points_balance else 0.0
    return world, hero, companion, bridge, ship, clue


def predict_crossing(world: World) -> dict[str, bool]:
    sim = world.copy()
    ship = sim.get("ship")
    ship.meters["attempted"] += 1
    propagate(sim, narrate=False)
    return {
        "refused": sim.get("bridge").meters["humming"] >= THRESHOLD,
        "crossed": sim.get("ship").meters["crossed"] >= THRESHOLD,
        "too_heavy": sim.get("ship").meters["total"] > sim.get("bridge").meters["capacity"],
        "unbalanced": sim.get("ship").meters["imbalance"] > sim.get("bridge").meters["tolerance"],
    }


def introduce(world: World, hero: Entity, companion: Entity, harbor: Harbor, ship: Ship) -> None:
    hero.memes["wonder"] += 1
    companion.memes["wonder"] += 1
    trait = "sharp" if hero.traits[0] == "sharp-eyed" else hero.traits[0]
    world.say(
        f"{hero.name} was {_article(hero.type)} {hero.type} with {trait} eyes and a pocket full of string."
    )
    world.say(
        f"One morning, {hero.name} and {companion.name} came to {harbor.label}, where "
        f"{harbor.bridge_phrase} stretched toward {harbor.far_side}. {harbor.detail}"
    )
    world.say(
        f"At the dock waited {ship.phrase}. {ship.wonder}, and its {ship.horn} gave "
        "one proud toot."
    )


def load_ship(world: World, cargo: Cargo) -> None:
    world.say(
        f"The sailors had packed {cargo.phrase} for {cargo.purpose}. "
        f"{cargo.clue_detail}"
    )


def first_attempt(world: World, hero: Entity, harbor: Harbor) -> None:
    ship = world.get("ship")
    ship.meters["attempted"] += 1
    pred = predict_crossing(world)
    propagate(world, narrate=False)
    world.facts["predicted"] = pred
    world.say(
        f'"Across we go!" called {harbor.keeper}. The {ship.label} rolled toward the '
        f"{harbor.bridge}, but the crystal sang ping-ping-ping and would not let "
        "the first wheel climb on."
    )
    world.say(
        f"Everyone guessed at once. Maybe the bridge was shy. Maybe the ship was "
        f"too wondrous. {hero.name} did not guess yet; {hero.pronoun()} listened."
    )


def search_for_clue(world: World, hero: Entity, companion: Entity, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    clue.meters["found"] += 1
    hero.memes["curiosity"] += 1
    companion.memes["teamwork"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.name} and {companion.name} crawled under the moon-bright rail and found "
        f"{clue_cfg.find}."
    )
    world.say(
        f"{hero.name} put one pebble on the left plank and one pebble on the right, "
        "then counted how the bridge answered. The answer was not magic being mean."
    )


def explain_mystery(world: World, hero: Entity, ship: Ship, cargo: Cargo) -> None:
    pred = world.facts["predicted"]
    if pred["too_heavy"] and pred["unbalanced"]:
        world.say(
            f'"The {ship.label} is carrying too much, and it is leaning to one side," '
            f"{hero.name} said. \"The {cargo.label} made the bridge feel both things at once.\""
        )
    else:
        world.say(
            f"{hero.name} frowned, because this was not the right mystery after all."
        )


def apply_fix(world: World, hero: Entity, fix: Fix) -> None:
    ship = world.get("ship")
    left, right = adjusted_sides(SHIPS[world.params.ship], CARGOES[world.params.cargo], fix)
    ship.meters["left"] = float(left)
    ship.meters["right"] = float(right)
    ship.meters["total"] = float(left + right)
    ship.meters["imbalance"] = float(abs(left - right))
    ship.meters["adjusted"] += 1
    hero.memes["care"] += 1
    world.say(f"So {hero.name} helped the crew {fix.action}.")
    world.say(
        "The deck gave a soft sigh, as if it had been holding its breath all morning."
    )


def final_crossing(world: World, hero: Entity, companion: Entity, harbor: Harbor,
                   ship: Ship, fix: Fix) -> None:
    propagate(world, narrate=False)
    if world.get("ship").meters["crossed"] < THRESHOLD:
        raise StoryError("(No story: the chosen fix did not let the ship cross.)")
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"This time the {harbor.bridge} glowed steady and clear. The {ship.label} "
        f"crossed slowly, straight as a bedtime ruler, with {hero.name} walking beside it."
    )
    world.say(
        f"On the far bank, {harbor.keeper} bowed to {hero.name}. "
        f'"Mysteries get smaller when you weigh them and balance them," {hero.pronoun()} said.'
    )
    world.say(
        f"That evening, the {harbor.bridge} shone with tiny stars, and the "
        f"{ship.label} rested safely beyond it, ready to carry {fix.lesson}."
    )


def tell(params: "StoryParams") -> World:
    if not valid_combo(params.harbor, params.ship, params.cargo, params.clue, params.fix):
        raise StoryError(explain_rejection(params.harbor, params.ship, params.cargo, params.clue, params.fix))
    harbor = HARBORS[params.harbor]
    ship_cfg = SHIPS[params.ship]
    cargo = CARGOES[params.cargo]
    clue = CLUES[params.clue]
    fix = FIXES[params.fix]
    world, hero, companion, _bridge, _ship, _clue = _init_world(params)
    introduce(world, hero, companion, harbor, ship_cfg)
    load_ship(world, cargo)
    world.para()
    first_attempt(world, hero, harbor)
    search_for_clue(world, hero, companion, clue)
    explain_mystery(world, hero, ship_cfg, cargo)
    world.para()
    apply_fix(world, hero, fix)
    final_crossing(world, hero, companion, harbor, ship_cfg, fix)
    world.facts.update(
        harbor=harbor, ship_cfg=ship_cfg, cargo=cargo, clue_cfg=clue, fix=fix,
        hero=hero, companion=companion, crossed=True,
        original_total=total_load(ship_cfg, cargo),
        original_imbalance=imbalance(ship_cfg, cargo),
        final_total=adjusted_total(ship_cfg, cargo, fix),
        final_imbalance=adjusted_imbalance(ship_cfg, cargo, fix),
    )
    return world


HARBORS = {
    "moon_harbor": Harbor(
        "moon_harbor", "Moon Harbor", "crystal bridge",
        "a crystal bridge clear as ice and warm as toast",
        "the peach orchard island", "the bridge keeper", 18, 2,
        "Little bells inside the stones rang whenever something stepped near.",
        tags={"bridge", "crystal", "weight"}),
    "starfish_bay": Harbor(
        "starfish_bay", "Starfish Bay", "glass-clear bridge",
        "a glass-clear bridge made from one long crystal shell",
        "the lighthouse meadow", "Captain Pearl", 20, 3,
        "Even the gulls tiptoed there, which was hard because they wore red boots.",
        tags={"bridge", "crystal", "balance"}),
    "cloudy_cove": Harbor(
        "cloudy_cove", "Cloudy Cove", "sparkle bridge",
        "a sparkle bridge that hummed like a spoon on a cup",
        "the blueberry hill", "Auntie Oar", 16, 2,
        "Fog curled around the rail in soft gray ribbons.",
        tags={"bridge", "crystal", "mystery"}),
}

SHIPS = {
    "wondrous_ship": Ship(
        "wondrous_ship", "wondrous ship", "a wondrous ship with silver sails",
        "silver deck", 5, 4,
        "Its mast was so tall that a cloud used it for a hat",
        "brass horn", tags={"ship", "tall_tale"}),
    "teacup_brig": Ship(
        "teacup_brig", "teacup brig", "a teacup brig with a blue spoon rudder",
        "painted deck", 4, 3,
        "Its anchor was a teaspoon, but it still made the sea say glug",
        "tiny horn", tags={"ship", "tall_tale"}),
    "feather_ferry": Ship(
        "feather_ferry", "feather ferry", "a feather ferry with lantern windows",
        "feather deck", 3, 4,
        "Its sails fluttered so gently that sleepy fish came closer to nap",
        "shell horn", tags={"ship", "tall_tale"}),
}

CARGOES = {
    "moon_melons": Cargo(
        "moon_melons", "moon-melons", "seven moon-melons and one sleepy goat-bell",
        10, 1, "All the round melons had rolled to the left rail.",
        "the island picnic", tags={"weight", "balance", "melon"}),
    "star_jars": Cargo(
        "star_jars", "star jars", "six jars of bottled starlight and a sack of brass spoons",
        2, 12, "The bright jars stood neatly, but the spoons sagged on the right.",
        "the lighthouse supper", tags={"weight", "balance", "stars"}),
    "giant_pears": Cargo(
        "giant_pears", "giant pears", "three giant pears, each bigger than a bathtub,",
        9, 2, "The pears leaned together on the left like whispering giants.",
        "the harvest feast", tags={"weight", "balance", "fruit"}),
    "cloud_pillows": Cargo(
        "cloud_pillows", "cloud pillows", "a mountain of cloud pillows tied with gold rope",
        8, 7, "The pillows looked soft, but each one held a pocket of rain.",
        "the nap parade", tags={"weight"}),
}

CLUES = {
    "singing_scale": Clue(
        "singing_scale", "singing scale",
        "a tiny singing scale tucked beside the first crystal post",
        True, True, tags={"scale", "weight", "balance"}),
    "tilt_shadow": Clue(
        "tilt_shadow", "tilting shadow",
        "the ship's shadow bending fat on one side and thin on the other",
        True, True, tags={"shadow", "weight", "balance"}),
    "loose_sparkle": Clue(
        "loose_sparkle", "loose sparkle",
        "a loose sparkle that jumped only when the heavy side bumped the bridge",
        True, True, tags={"crystal", "weight", "balance"}),
    "pretty_reflection": Clue(
        "pretty_reflection", "pretty reflection",
        "a pretty reflection of the sail winking in the water",
        False, False, tags={"reflection"}),
}

FIXES = {
    "split_and_share": Fix(
        "split_and_share", "split and share",
        "roll some cargo into the dock cart and spread the rest evenly from rail to rail",
        "rolled some cargo into the dock cart and spread the rest evenly from rail to rail",
        unload=4, move_left_to_right=4,
        lesson="picnic baskets and a much wiser crew", tags={"balance", "share"}),
    "count_and_shift": Fix(
        "count_and_shift", "count and shift",
        "count the heavy bundles, set two ashore, and shift the biggest ones toward the quiet side",
        "counted the heavy bundles, set two ashore, and shifted the biggest ones toward the quiet side",
        unload=2, move_left_to_right=0, move_right_to_left=5,
        lesson="lanterns, pears, and careful counting", tags={"count", "balance"}),
    "two_carts": Fix(
        "two_carts", "two carts",
        "fill two little dock carts first, then place the remaining bundles in matching rows",
        "filled two little dock carts first, then placed the remaining bundles in matching rows",
        unload=6, move_left_to_right=3,
        lesson="two carts full of useful extras", tags={"cart", "balance"}),
    "wave_flag": Fix(
        "wave_flag", "wave flag",
        "wave a blue flag and ask the bridge to be friendly",
        "waved a blue flag and asked the bridge to be friendly",
        unload=0, move_left_to_right=0,
        lesson="a blue flag", tags={"wrong_fix"}),
}

GENDERS = ["girl", "boy", "child"]
NAMES = {
    "girl": ["Mira", "Lina", "Nora", "Ada", "Zoe", "Tessa"],
    "boy": ["Milo", "Theo", "Eli", "Finn", "Noah", "Sam"],
    "child": ["Riley", "Sunny", "Kai", "Rowan", "Ari", "Pip"],
}
COMPANIONS = ["Pip", "Nell", "Ollie", "June", "Max", "Rose"]
TRAITS = ["curious", "careful", "bright", "patient", "sharp-eyed", "gentle"]


@dataclass
class StoryParams:
    harbor: str
    ship: str
    cargo: str
    clue: str
    fix: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("moon_harbor", "wondrous_ship", "moon_melons", "singing_scale",
                "split_and_share", "Mira", "girl", "Pip", "curious", 301),
    StoryParams("starfish_bay", "feather_ferry", "star_jars", "tilt_shadow",
                "count_and_shift", "Theo", "boy", "Nell", "careful", 302),
    StoryParams("cloudy_cove", "teacup_brig", "moon_melons", "loose_sparkle",
                "two_carts", "Riley", "child", "June", "sharp-eyed", 303),
    StoryParams("cloudy_cove", "feather_ferry", "giant_pears", "singing_scale",
                "split_and_share", "Ada", "girl", "Ollie", "patient", 304),
]


def explain_rejection(harbor_id: str, ship_id: str, cargo_id: str,
                      clue_id: str, fix_id: str) -> str:
    harbor, ship, cargo = HARBORS[harbor_id], SHIPS[ship_id], CARGOES[cargo_id]
    clue, fix = CLUES[clue_id], FIXES[fix_id]
    if not has_true_problem(harbor, ship, cargo):
        return (
            f"(No story: {ship.label} with {cargo.label} does not have both a true "
            "load problem and a true balance problem on this bridge.)"
        )
    if not clue_points_to_problem(clue):
        return (
            f"(No story: {clue.label} does not reveal both the load and balance clues, "
            "so the mystery would not be grounded.)"
        )
    if not fix_solves_problem(harbor, ship, cargo, fix):
        return (
            f"(No story: {fix.label} does not make the ship light enough and even "
            "enough for the crystal bridge.)"
        )
    return "(No story: the requested choices do not make one reasonable bridge mystery.)"


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        'Write a TinyStories-style mystery that includes "wondrous ship" and "crystal bridge".',
        f"Write a child-facing tall tale where {params.name} solves why a ship cannot cross a crystal bridge.",
        "Tell a concrete mystery story where the real answer is weight and balance, not magic.",
    ]


def story_qa(params: StoryParams, world: World) -> list[QAItem]:
    f = world.facts
    harbor: Harbor = f["harbor"]
    ship: Ship = f["ship_cfg"]
    cargo: Cargo = f["cargo"]
    clue: Clue = f["clue_cfg"]
    fix: Fix = f["fix"]
    hero: Entity = f["hero"]
    return [
        QAItem(
            f"Why could the {ship.label} not cross the {harbor.bridge} at first?",
            f"It could not cross because the {cargo.label} made it too heavy and uneven. "
            "The bridge was not being mean; it was responding to the real load and lean.",
        ),
        QAItem(
            f"What clue helped {hero.name} solve the mystery?",
            f"{hero.name} used the {clue.label} to notice both weight and balance. "
            "That clue matched what the bridge did when the ship tried to climb on.",
        ),
        QAItem(
            "How did the crew fix the problem?",
            f"They fixed it by using the {fix.label} plan: they {fix.qa_action}. "
            "After that, the ship was light enough and even enough to cross.",
        ),
        QAItem(
            f"What changed at the end for {hero.name}?",
            f"At the end, {hero.name} understood the true problem instead of guessing. "
            f"The {ship.label} rested safely beyond the bridge, which proved the idea worked.",
        ),
    ]


KNOWLEDGE = {
    "bridge": QAItem(
        "Why can a bridge have a weight limit?",
        "A bridge can only hold so much before it may bend or break. A weight limit keeps people, carts, and ships safe.",
    ),
    "balance": QAItem(
        "Why does balance matter when something crosses a narrow path?",
        "Balance matters because a leaning load pushes harder on one side. Spreading weight evenly helps the whole thing stay steady.",
    ),
    "scale": QAItem(
        "What does a scale help people learn?",
        "A scale helps people compare how heavy things are. In a mystery, it can turn guessing into checking.",
    ),
    "ship": QAItem(
        "Why should cargo be spread out on a ship?",
        "Cargo should be spread out so the ship does not lean too far to one side. An even deck is safer for people and cargo.",
    ),
    "crystal": QAItem(
        "Why might crystal seem magical in a story?",
        "Crystal can sparkle, ring, and shine in many colors. In this story it feels magical, but it still follows a clear rule.",
    ),
}


def world_qa(params: StoryParams) -> list[QAItem]:
    tags = set().union(
        HARBORS[params.harbor].tags,
        SHIPS[params.ship].tags,
        CARGOES[params.cargo].tags,
        CLUES[params.clue].tags,
        FIXES[params.fix].tags,
    )
    order = ["bridge", "balance", "scale", "ship", "crystal"]
    return [KNOWLEDGE[key] for key in order if key in tags][:4]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_qa(params, world),
        world_qa=world_qa(params),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print(format_qa(sample))
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())


ASP_RULES = r"""
true_problem(H,S,C) :- too_heavy(H,S,C), unbalanced(H,S,C).
good_clue(C) :- clue_weight(C), clue_balance(C).
solves(H,S,C,F) :- final_ok(H,S,C,F), final_balanced(H,S,C,F).
valid(H,S,C,L,F) :- harbor(H), ship(S), cargo(C), clue(L), fix(F),
                    true_problem(H,S,C), good_clue(L), solves(H,S,C,F).
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for hid, harbor in HARBORS.items():
        facts.append(asp.fact("harbor", hid))
        facts.append(asp.fact("capacity", hid, harbor.capacity))
        facts.append(asp.fact("tolerance", hid, harbor.tolerance))
    for sid in SHIPS:
        facts.append(asp.fact("ship", sid))
    for cid in CARGOES:
        facts.append(asp.fact("cargo", cid))
    for lid, clue in CLUES.items():
        facts.append(asp.fact("clue", lid))
        if clue.points_weight:
            facts.append(asp.fact("clue_weight", lid))
        if clue.points_balance:
            facts.append(asp.fact("clue_balance", lid))
    for fid in FIXES:
        facts.append(asp.fact("fix", fid))

    for hid, harbor in HARBORS.items():
        for sid, ship in SHIPS.items():
            for cid, cargo in CARGOES.items():
                if total_load(ship, cargo) > harbor.capacity:
                    facts.append(asp.fact("too_heavy", hid, sid, cid))
                if imbalance(ship, cargo) > harbor.tolerance:
                    facts.append(asp.fact("unbalanced", hid, sid, cid))
                for fid, fix in FIXES.items():
                    if adjusted_total(ship, cargo, fix) <= harbor.capacity:
                        facts.append(asp.fact("final_ok", hid, sid, cid, fid))
                    if adjusted_imbalance(ship, cargo, fix) <= harbor.tolerance:
                        facts.append(asp.fact("final_balanced", hid, sid, cid, fid))
    return "\n".join(facts) + "\n"


def asp_program(show: str = "#show valid/5.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(x) for x in atom))  # type: ignore[arg-type]
    return sorted(combos)


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set != clingo_set:
        print("Python/ASP mismatch")
        print("Only Python:", sorted(python_set - clingo_set))
        print("Only ASP:", sorted(clingo_set - python_set))
        return 1

    for combo in sorted(python_set):
        params = StoryParams(*combo, name="Mira", gender="girl", companion="Pip",
                             trait="curious", seed=0)
        sample = generate(params)
        if "safely beyond" not in sample.story:
            print("Generated story did not reach payoff for", combo)
            return 1
        if len(sample.story_qa) < 3 or any(len(q.answer.split(".")) < 2 for q in sample.story_qa[:3]):
            print("QA quality gate failed for", combo)
            return 1
    print(f"OK: Python and ASP agree on {len(python_set)} valid wondrous ship mysteries.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harbor", choices=sorted(HARBORS))
    parser.add_argument("--ship", choices=sorted(SHIPS))
    parser.add_argument("--cargo", choices=sorted(CARGOES))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--fix", choices=sorted(FIXES))
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=GENDERS)
    parser.add_argument("--companion")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1, help="number of stories to generate")
    parser.add_argument("--all", action="store_true", help="render the curated set")
    parser.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    parser.add_argument("--trace", action="store_true", help="dump world-model state")
    parser.add_argument("--qa", action="store_true", help="include grounded Q&A")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    parser.add_argument("--verify", action="store_true", help="check the inline ASP gate and quality smoke")
    parser.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo for combo in valid_combos()
        if (args.harbor is None or combo[0] == args.harbor)
        and (args.ship is None or combo[1] == args.ship)
        and (args.cargo is None or combo[2] == args.cargo)
        and (args.clue is None or combo[3] == args.clue)
        and (args.fix is None or combo[4] == args.fix)
    ]
    if not choices:
        harbor = args.harbor or sorted(HARBORS)[0]
        ship = args.ship or sorted(SHIPS)[0]
        cargo = args.cargo or sorted(CARGOES)[0]
        clue = args.clue or sorted(CLUES)[0]
        fix = args.fix or sorted(FIXES)[0]
        raise StoryError(explain_rejection(harbor, ship, cargo, clue, fix))
    harbor, ship, cargo, clue, fix = rng.choice(choices)
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice([n for n in COMPANIONS if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(harbor, ship, cargo, clue, fix, name, gender, companion, trait, args.seed)


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    target = max(1, args.n)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    while len(samples) < target and attempts < target * 50:
        seed = base_seed + attempts
        attempts += 1
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (harbor, ship, cargo, clue, fix) combos:")
        for combo in combos:
            print(" ".join(combo))
        return 0
    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
        return 2

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples, 1):
        header = ""
        if args.all:
            p = sample.params
            header = f"=== {p.name}: {p.ship} with {p.cargo} at {p.harbor} ==="
        elif len(samples) > 1:
            header = f"=== wondrous_ship_crystal_bridge_mystery #{idx} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
