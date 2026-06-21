#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/latte_brig_problem_solving_kindness_twist_pirate.py
==============================================================================

A standalone story world for a tiny pirate-tale domain with problem solving,
kindness, and a twist ending. The core premise is simple:

A child pirate crew finds a note on a ship saying a tired grown-up in the brig
needs a latte. One child first imagines a selfish use for the only cup of milk,
but the crew chooses kindness, solves the kitchen problem with sensible tools,
and discovers a twist: the "prisoner" in the brig is not a villain at all, but
the ship's baker testing whether the children can care for others.

The world model tracks objects, simple physical meters, and emotional memes.
State drives the prose and the Q&A. A small reasonableness gate refuses invalid
stories such as making a hot latte with no heat source, or trying to carry it in
a leaky hat when there is a tray on board.

Run it
------
    python storyworlds/worlds/gpt-5.4/latte_brig_problem_solving_kindness_twist_pirate.py
    python storyworlds/worlds/gpt-5.4/latte_brig_problem_solving_kindness_twist_pirate.py --need latte --barrier locked_door
    python storyworlds/worlds/gpt-5.4/latte_brig_problem_solving_kindness_twist_pirate.py --carrier hat
    python storyworlds/worlds/gpt-5.4/latte_brig_problem_solving_kindness_twist_pirate.py --all
    python storyworlds/worlds/gpt-5.4/latte_brig_problem_solving_kindness_twist_pirate.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/latte_brig_problem_solving_kindness_twist_pirate.py --qa --json
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain_f"}
        male = {"boy", "father", "man", "captain_m"}
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
            "captain_f": "captain",
            "captain_m": "captain",
        }.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    deck_name: str
    opening: str
    ship_name: str
    pretend_job_1: str
    pretend_job_2: str
    map_line: str
    ending_line: str


@dataclass
class Need:
    id: str
    request_line: str
    drink_label: str
    drink_phrase: str
    steam_line: str
    comfort_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Barrier:
    id: str
    note_line: str
    fix_line: str
    carry_line: str
    fail_line: str
    requires_tool: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    helps_with: set[str] = field(default_factory=set)
    sturdy: bool = False
    heats: bool = False
    opens: bool = False
    mixes: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    steady: bool
    sense: int
    success_line: str
    fail_line: str
    tags: set[str] = field(default_factory=set)


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


def _r_heat_milk(world: World) -> list[str]:
    out: list[str] = []
    galley = world.get("galley")
    cup = world.get("cup")
    if galley.meters["milk_poured"] >= THRESHOLD and galley.meters["heat_ready"] >= THRESHOLD:
        sig = ("heat_milk",)
        if sig not in world.fired:
            world.fired.add(sig)
            galley.meters["milk_warm"] += 1
            out.append("Warm milk made the galley smell soft and sweet.")
    return out


def _r_make_latte(world: World) -> list[str]:
    out: list[str] = []
    galley = world.get("galley")
    cup = world.get("cup")
    if (
        galley.meters["milk_warm"] >= THRESHOLD
        and galley.meters["coffee_added"] >= THRESHOLD
        and galley.meters["foam_made"] >= THRESHOLD
    ):
        sig = ("latte_ready",)
        if sig not in world.fired:
            world.fired.add(sig)
            cup.meters["latte_ready"] += 1
            out.append("At last, the cup held a real latte with a pale, swirly top.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    cup = world.get("cup")
    if cup.meters["carried_badly"] >= THRESHOLD:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            cup.meters["spilled"] += 1
            cup.meters["latte_ready"] = 0.0
            out.append("__spill__")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    brig = world.get("brig")
    prisoner = world.get("prisoner")
    if brig.meters["drink_delivered"] >= THRESHOLD:
        sig = ("comfort",)
        if sig not in world.fired:
            world.fired.add(sig)
            prisoner.memes["relief"] += 1
            prisoner.memes["gratitude"] += 1
            out.append("__comfort__")
    return out


CAUSAL_RULES = [
    Rule(name="heat_milk", tag="physical", apply=_r_heat_milk),
    Rule(name="make_latte", tag="physical", apply=_r_make_latte),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="comfort", tag="social", apply=_r_comfort),
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
        for s in produced:
            world.say(s)
    return produced


THEMES = {
    "pirate_ship": Theme(
        id="pirate_ship",
        deck_name="sunny deck",
        opening="The old playroom became a pirate ship with a striped blanket for a sail and a chalk map on the floor.",
        ship_name="the Starry Gull",
        pretend_job_1="First Mate",
        pretend_job_2="Map Keeper",
        map_line="A chalk X by the toy chest marked where treasure ought to be.",
        ending_line="The little crew marched back across the deck feeling kinder and wiser than before.",
    ),
    "stormy_ship": Theme(
        id="stormy_ship",
        deck_name="windy deck",
        opening="The old playroom became a storm-tossed pirate ship, with chairs for masts and a blue sheet for the sea.",
        ship_name="the Moonshell",
        pretend_job_1="Captain's Helper",
        pretend_job_2="Lantern Watcher",
        map_line="A crayon map curled at the edges as if salty wind had licked it.",
        ending_line="The brave little crew crossed the deck again, grinning at how a caring idea had changed the whole voyage.",
    ),
}

NEEDS = {
    "latte": Need(
        id="latte",
        request_line='The note read, "Please bring a warm latte to the brig. Someone down there is tired and sad."',
        drink_label="latte",
        drink_phrase="a warm latte",
        steam_line="A little ribbon of steam curled up like a ghostly pirate flag.",
        comfort_line="The warm latte made the brig feel less lonely.",
        tags={"latte", "drink", "kindness"},
    ),
    "cocoa": Need(
        id="cocoa",
        request_line='The note read, "Please bring warm cocoa to the brig. Someone down there is tired and sad."',
        drink_label="cocoa",
        drink_phrase="a warm mug of cocoa",
        steam_line="A little chocolatey puff floated up from the cup.",
        comfort_line="The warm cocoa made the brig feel less lonely.",
        tags={"cocoa", "drink", "kindness"},
    ),
}

BARRIERS = {
    "locked_door": Barrier(
        id="locked_door",
        note_line="The brig door was shut tight with a little brass lock.",
        fix_line="They would need a sensible way to open the lock before anyone could sip a drink.",
        carry_line="Once the door opened, they still had to get the cup there without sloshing it.",
        fail_line="A shut lock keeps kindness standing in the hallway if nobody solves it.",
        requires_tool="key",
        tags={"lock", "brig"},
    ),
    "dark_stairs": Barrier(
        id="dark_stairs",
        note_line="The brig was down a short stairway that looked dim and wobbly.",
        fix_line="They would need a safe light so they could see each step clearly.",
        carry_line="After that, they still had to carry the cup with steady hands.",
        fail_line="In the dark, even a kind idea can turn into a tumble.",
        requires_tool="lantern",
        tags={"dark", "brig"},
    ),
    "sleepy_guard": Barrier(
        id="sleepy_guard",
        note_line="A sleepy guard nodded beside the brig and had not heard the note at all.",
        fix_line="They would need a polite way to wake the guard and explain what they were doing.",
        carry_line="Then they still had to bring the cup without spilling it.",
        fail_line="If nobody spoke kindly, the drink would never get through.",
        requires_tool="bell",
        tags={"guard", "brig"},
    ),
}

TOOLS = {
    "whisk": Tool(
        id="whisk",
        label="whisk",
        phrase="a little whisk",
        kind="mix",
        helps_with={"foam"},
        mixes=True,
        tags={"whisk"},
    ),
    "spoon": Tool(
        id="spoon",
        label="spoon",
        phrase="a silver spoon",
        kind="mix",
        helps_with={"foam"},
        mixes=True,
        tags={"spoon"},
    ),
    "kettle": Tool(
        id="kettle",
        label="kettle",
        phrase="the tiny galley kettle",
        kind="heat",
        helps_with={"heat"},
        heats=True,
        tags={"kettle", "heat"},
    ),
    "stove": Tool(
        id="stove",
        label="stove",
        phrase="the little ship stove",
        kind="heat",
        helps_with={"heat"},
        heats=True,
        tags={"stove", "heat"},
    ),
    "key": Tool(
        id="key",
        label="brass key",
        phrase="a brass key on a blue ribbon",
        kind="barrier",
        helps_with={"locked_door"},
        opens=True,
        tags={"key", "lock"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a safe lantern with a round glass belly",
        kind="barrier",
        helps_with={"dark_stairs"},
        tags={"lantern", "light"},
    ),
    "bell": Tool(
        id="bell",
        label="bell",
        phrase="a bright hand bell",
        kind="barrier",
        helps_with={"sleepy_guard"},
        tags={"bell", "guard"},
    ),
}

CARRIERS = {
    "tray": Carrier(
        id="tray",
        label="tray",
        phrase="a wooden tray with a little rim",
        steady=True,
        sense=3,
        success_line="The tray kept the cup from wobbling as they walked.",
        fail_line="",
        tags={"tray"},
    ),
    "both_hands": Carrier(
        id="both_hands",
        label="both hands",
        phrase="both careful hands around the cup",
        steady=True,
        sense=2,
        success_line="Holding the cup with both hands kept it level and warm.",
        fail_line="",
        tags={"hands"},
    ),
    "hat": Carrier(
        id="hat",
        label="hat",
        phrase="a floppy pirate hat",
        steady=False,
        sense=1,
        success_line="",
        fail_line="The floppy pirate hat tipped at once, and the drink sloshed away.",
        tags={"hat"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli"]
TRAITS = ["careful", "kind", "curious", "thoughtful", "steady", "brave"]


def tool_can_solve(barrier: Barrier, tool: Tool) -> bool:
    return barrier.id in tool.helps_with


def heat_available(heat_tool: Tool) -> bool:
    return heat_tool.heats


def mix_available(mix_tool: Tool) -> bool:
    return mix_tool.mixes


def carrier_sensible(carrier: Carrier) -> bool:
    return carrier.sense >= SENSE_MIN and carrier.steady


def valid_combo(theme_id: str, need_id: str, barrier_id: str, heat_tool_id: str,
                mix_tool_id: str, barrier_tool_id: str, carrier_id: str) -> bool:
    del theme_id
    del need_id
    barrier = BARRIERS[barrier_id]
    heat_tool = TOOLS[heat_tool_id]
    mix_tool = TOOLS[mix_tool_id]
    barrier_tool = TOOLS[barrier_tool_id]
    carrier = CARRIERS[carrier_id]
    return (
        heat_available(heat_tool)
        and mix_available(mix_tool)
        and tool_can_solve(barrier, barrier_tool)
        and carrier_sensible(carrier)
    )


def valid_combos() -> list[tuple[str, str, str, str, str, str, str]]:
    combos = []
    for theme_id in THEMES:
        for need_id in NEEDS:
            for barrier_id, barrier in BARRIERS.items():
                for heat_tool_id, heat_tool in TOOLS.items():
                    if not heat_tool.heats:
                        continue
                    for mix_tool_id, mix_tool in TOOLS.items():
                        if not mix_tool.mixes:
                            continue
                        for barrier_tool_id, barrier_tool in TOOLS.items():
                            if not tool_can_solve(barrier, barrier_tool):
                                continue
                            for carrier_id, carrier in CARRIERS.items():
                                if valid_combo(
                                    theme_id,
                                    need_id,
                                    barrier_id,
                                    heat_tool_id,
                                    mix_tool_id,
                                    barrier_tool_id,
                                    carrier_id,
                                ):
                                    combos.append(
                                        (
                                            theme_id,
                                            need_id,
                                            barrier_id,
                                            heat_tool_id,
                                            mix_tool_id,
                                            barrier_tool_id,
                                            carrier_id,
                                        )
                                    )
    return combos


@dataclass
class StoryParams:
    theme: str
    need: str
    barrier: str
    heat_tool: str
    mix_tool: str
    barrier_tool: str
    carrier: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    captain: str
    captain_gender: str
    trait1: str
    trait2: str
    selfish_first: bool = True
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="pirate_ship",
        need="latte",
        barrier="locked_door",
        heat_tool="kettle",
        mix_tool="whisk",
        barrier_tool="key",
        carrier="tray",
        child1="Tom",
        child1_gender="boy",
        child2="Lily",
        child2_gender="girl",
        captain="Captain Mara",
        captain_gender="captain_f",
        trait1="curious",
        trait2="kind",
        selfish_first=True,
    ),
    StoryParams(
        theme="stormy_ship",
        need="latte",
        barrier="dark_stairs",
        heat_tool="stove",
        mix_tool="spoon",
        barrier_tool="lantern",
        carrier="both_hands",
        child1="Mia",
        child1_gender="girl",
        child2="Ben",
        child2_gender="boy",
        captain="Captain Reed",
        captain_gender="captain_m",
        trait1="careful",
        trait2="thoughtful",
        selfish_first=False,
    ),
    StoryParams(
        theme="pirate_ship",
        need="cocoa",
        barrier="sleepy_guard",
        heat_tool="kettle",
        mix_tool="spoon",
        barrier_tool="bell",
        carrier="tray",
        child1="Sam",
        child1_gender="boy",
        child2="Zoe",
        child2_gender="girl",
        captain="Captain Mara",
        captain_gender="captain_f",
        trait1="brave",
        trait2="kind",
        selfish_first=True,
    ),
]


def predict_delivery(world: World, barrier: Barrier, barrier_tool: Tool, carrier: Carrier) -> dict:
    sim = world.copy()
    brig = sim.get("brig")
    cup = sim.get("cup")
    if tool_can_solve(barrier, barrier_tool):
        brig.meters["barrier_open"] += 1
    if not carrier_sensible(carrier):
        cup.meters["carried_badly"] += 1
    propagate(sim, narrate=False)
    return {
        "opened": brig.meters["barrier_open"] >= THRESHOLD,
        "spilled": cup.meters["spilled"] >= THRESHOLD,
        "delivered": brig.meters["barrier_open"] >= THRESHOLD and cup.meters["spilled"] < THRESHOLD,
    }


def setup_play(world: World, theme: Theme, a: Entity, b: Entity, captain: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{theme.opening} {theme.map_line} {a.id} was {theme.pretend_job_1}, "
        f"and {b.id} was {theme.pretend_job_2} aboard {theme.ship_name}."
    )
    world.say(
        f'"Crew to the {theme.deck_name}!" called {captain.id}. At once, the two little pirates came running.'
    )


def discover_note(world: World, need: Need, barrier: Barrier, a: Entity, b: Entity) -> None:
    world.say(
        f"Near the toy compass, {b.id} found a folded note tied with string. {need.request_line}"
    )
    world.say(barrier.note_line)
    a.memes["concern"] += 1
    b.memes["concern"] += 1


def selfish_idea(world: World, a: Entity, need: Need) -> None:
    a.memes["want_treat"] += 1
    world.say(
        f'{a.id} peeked toward the galley and whispered, "A {need.drink_label}? We could drink it ourselves while we hunt treasure."'
    )


def kind_correction(world: World, b: Entity, a: Entity, captain: Entity, need: Need) -> None:
    b.memes["kindness"] += 1
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "No," {b.pronoun()} said. '
        f'"If someone in the brig is tired and sad, {need.drink_phrase} should go to them."'
    )
    world.say(
        f"{captain.id} smiled at that. The room felt a little warmer just from hearing a kind answer."
    )
    a.memes["shame"] += 1
    a.memes["kindness"] += 1


def gather_ingredients(world: World, need: Need, heat_tool: Tool, mix_tool: Tool) -> None:
    galley = world.get("galley")
    world.say(
        f"In the toy galley they found milk, a pinch of coffee, {heat_tool.phrase}, and {mix_tool.phrase}."
    )
    galley.meters["milk_poured"] += 1
    galley.meters["coffee_added"] += 1
    if heat_tool.heats:
        galley.meters["heat_ready"] += 1
    if mix_tool.mixes:
        galley.meters["foam_made"] += 1
    propagate(world, narrate=True)
    if world.get("cup").meters["latte_ready"] >= THRESHOLD:
        world.say(need.steam_line)


def discuss_problem(world: World, barrier: Barrier, a: Entity, b: Entity, barrier_tool: Tool,
                    carrier: Carrier) -> None:
    pred = predict_delivery(world, barrier, barrier_tool, carrier)
    world.facts["predicted_opened"] = pred["opened"]
    world.facts["predicted_spilled"] = pred["spilled"]
    world.say(barrier.fix_line)
    if pred["spilled"]:
        world.say(
            f"{a.id} looked at {carrier.phrase} and frowned. Even before they moved, it seemed like a tippy plan."
        )
    else:
        world.say(barrier.carry_line)


def solve_barrier(world: World, barrier: Barrier, barrier_tool: Tool, a: Entity, b: Entity) -> None:
    brig = world.get("brig")
    if barrier.id == "locked_door":
        world.say(
            f"{b.id} remembered {barrier_tool.phrase} hanging by the map hook. {b.pronoun().capitalize()} fetched it and turned the little lock with a neat click."
        )
    elif barrier.id == "dark_stairs":
        world.say(
            f"{a.id} lit the way with {barrier_tool.phrase}, and the steep steps stopped looking spooky."
        )
    else:
        world.say(
            f"{b.id} rang {barrier_tool.phrase}. The sleepy guard blinked, sat up straight, and listened to the crew's polite explanation."
        )
    brig.meters["barrier_open"] += 1
    a.memes["confidence"] += 1
    b.memes["confidence"] += 1


def carry_drink(world: World, carrier: Carrier, a: Entity, b: Entity) -> None:
    cup = world.get("cup")
    if carrier.steady:
        world.say(
            f"{a.id} and {b.id} carried the cup using {carrier.phrase}. {carrier.success_line}"
        )
    else:
        world.say(
            f"{a.id} tried to carry the cup in {carrier.phrase}. {carrier.fail_line}"
        )
        cup.meters["carried_badly"] += 1
    propagate(world, narrate=False)


def spill_branch(world: World, captain: Entity, need: Need) -> None:
    world.say(
        f"A pale splash ran across the floorboards. The lovely smell was gone, and there was no {need.drink_label} left for the brig."
    )
    world.say(
        f"{captain.id} knelt beside the mess. \"Kind hearts still need good plans,\" {captain.pronoun()} said gently."
    )


def retry_kindly(world: World, heat_tool: Tool, mix_tool: Tool, carrier: Carrier, need: Need,
                 a: Entity, b: Entity) -> None:
    cup = world.get("cup")
    galley = world.get("galley")
    cup.meters["spilled"] = 0.0
    cup.meters["carried_badly"] = 0.0
    cup.meters["latte_ready"] = 0.0
    world.say(
        f"Instead of arguing, {a.id} and {b.id} cleaned the spill together and made the drink again."
    )
    world.say(
        f"This time they used {carrier.phrase} and moved more slowly."
    )
    galley.meters["milk_poured"] += 1
    galley.meters["coffee_added"] += 1
    galley.meters["heat_ready"] += 1 if heat_tool.heats else 0
    galley.meters["foam_made"] += 1 if mix_tool.mixes else 0
    propagate(world, narrate=False)
    cup.meters["latte_ready"] += 1
    world.say(need.steam_line)
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1


def deliver_drink(world: World, need: Need, a: Entity, b: Entity) -> None:
    brig = world.get("brig")
    brig.meters["drink_delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At the brig, {a.id} held out the cup and {b.id} said, \"We brought {need.drink_phrase}.\" {need.comfort_line}"
    )


def twist_reveal(world: World, captain: Entity, need: Need) -> None:
    prisoner = world.get("prisoner")
    prisoner.meters["revealed"] += 1
    world.say(
        f"Then came the twist. The tired prisoner pushed back the hood and started to laugh."
    )
    world.say(
        f'"I am not a crook at all," {prisoner.id} said. "I am the ship\'s baker, and {captain.id} asked me to hide here and see what kind of crew you would be."'
    )
    world.say(
        f"{captain.id} nodded. \"A crew that can solve a problem is useful,\" {captain.pronoun()} said. "
        f"\"A crew that solves it kindly is treasure.\""
    )
    world.say(
        f"The baker took a happy sip of the {need.drink_label}, and foam made a tiny white moustache over a big grin."
    )
    world.facts["twist"] = "baker_test"


def ending(world: World, theme: Theme, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"After that, treasure did not feel like the best prize anymore. {theme.ending_line}"
    )


def tell(theme: Theme, need: Need, barrier: Barrier, heat_tool: Tool, mix_tool: Tool,
         barrier_tool: Tool, carrier: Carrier, child1: str, child1_gender: str,
         child2: str, child2_gender: str, captain_name: str, captain_gender: str,
         trait1: str, trait2: str, selfish_first: bool) -> World:
    world = World()
    a = world.add(Entity(
        id=child1,
        kind="character",
        type=child1_gender,
        role="solver",
        traits=[trait1],
    ))
    b = world.add(Entity(
        id=child2,
        kind="character",
        type=child2_gender,
        role="helper",
        traits=[trait2],
    ))
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        label="the captain",
    ))
    prisoner = world.add(Entity(
        id="Baker Nibs",
        kind="character",
        type="man",
        role="prisoner",
        label="the prisoner",
    ))
    galley = world.add(Entity(id="galley", type="room", label="the galley"))
    brig_ent = world.add(Entity(id="brig", type="room", label="the brig"))
    cup = world.add(Entity(id="cup", type="cup", label=need.drink_label))

    setup_play(world, theme, a, b, captain)
    discover_note(world, need, barrier, a, b)

    world.para()
    if selfish_first:
        selfish_idea(world, a, need)
        kind_correction(world, b, a, captain, need)
    else:
        world.say(
            f"{a.id} felt hungry for treasure, but not for keeping the drink. \"Let's help first,\" {a.pronoun()} said."
        )
        a.memes["kindness"] += 1
        b.memes["kindness"] += 1
    gather_ingredients(world, need, heat_tool, mix_tool)

    world.para()
    discuss_problem(world, barrier, a, b, barrier_tool, carrier)
    solve_barrier(world, barrier, barrier_tool, a, b)
    carry_drink(world, carrier, a, b)

    spilled = cup.meters["spilled"] >= THRESHOLD
    if spilled:
        world.para()
        spill_branch(world, captain, need)
        retry_kindly(world, heat_tool, mix_tool, CARRIERS["tray"], need, a, b)
        world.say("With the cup safe on a tray, they tried again.")
    deliver_drink(world, need, a, b)

    world.para()
    twist_reveal(world, captain, need)
    ending(world, theme, a, b)

    world.facts.update(
        theme=theme,
        need=need,
        barrier=barrier,
        heat_tool=heat_tool,
        mix_tool=mix_tool,
        barrier_tool=barrier_tool,
        carrier=carrier if not spilled else CARRIERS["tray"],
        first_carrier=carrier,
        child1=a,
        child2=b,
        captain=captain,
        prisoner=prisoner,
        cup=cup,
        selfish_first=selfish_first,
        spilled=spilled,
        delivered=brig_ent.meters["drink_delivered"] >= THRESHOLD,
        twist=world.facts.get("twist", ""),
    )
    return world


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two little pirates"
    if a.type == "girl" and b.type == "girl":
        return "two little pirates"
    return "two little pirates"


KNOWLEDGE = {
    "latte": [
        (
            "What is a latte?",
            "A latte is a warm drink made with milk and coffee. Grown-ups often drink it when they want something warm and gentle."
        )
    ],
    "cocoa": [
        (
            "What is cocoa?",
            "Cocoa is a warm chocolate drink. It tastes sweet and can help someone feel cozy."
        )
    ],
    "brig": [
        (
            "What is a brig on a ship?",
            "A brig is a little locked room on a ship. It is used to keep someone in one place for a while."
        )
    ],
    "lock": [
        (
            "What does a key do?",
            "A key opens a lock when it is the right shape. That lets a closed door open the safe way."
        )
    ],
    "light": [
        (
            "Why is a lantern helpful in dark stairs?",
            "A lantern helps people see where they are stepping. Good light makes walking safer."
        )
    ],
    "guard": [
        (
            "Why is it kind to wake someone politely?",
            "A polite voice helps people listen without feeling scared or cross. Kind words can solve a problem faster."
        )
    ],
    "heat": [
        (
            "Why does warm milk matter in a latte or cocoa?",
            "Warm milk makes the drink feel cozy and smooth. Heat changes a cold drink into a comforting one."
        )
    ],
    "tray": [
        (
            "Why is a tray good for carrying a drink?",
            "A tray gives the cup a flat place to rest. That helps keep the drink from spilling."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing to help someone and care about how they feel. It is not just thinking about yourself."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is in the way and picking a good way around it. Sometimes you need the right tool and a calm idea."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "latte",
    "cocoa",
    "brig",
    "lock",
    "light",
    "guard",
    "heat",
    "tray",
    "kindness",
    "problem_solving",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    need = f["need"]
    barrier = f["barrier"]
    return [
        f'Write a short pirate tale for a 3-to-5-year-old that includes the words "{need.drink_label}" and "brig".',
        f"Tell a pirate story where {a.id} and {b.id} must solve a shipboard problem to bring {need.drink_phrase} to someone in the brig, and the ending has a kind twist.",
        f"Write a gentle adventure about young pirates choosing kindness over greed, solving a {barrier.id.replace('_', ' ')} problem, and learning what treasure really is.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    captain = f["captain"]
    need = f["need"]
    barrier = f["barrier"]
    barrier_tool = f["barrier_tool"]
    first_carrier = f["first_carrier"]
    used_carrier = f["carrier"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, and {captain.id} on their pretend pirate ship. The crew finds a note about someone lonely in the brig."
        ),
        (
            f"Why did the children make {need.drink_phrase}?",
            f"They made it because the note said someone in the brig was tired and sad. Their kindness turned the drink into a way of helping, not just a treat."
        ),
        (
            f"What problem did the crew have to solve before reaching the brig?",
            f"They had to deal with {barrier.id.replace('_', ' ')}. They used {barrier_tool.phrase} because that tool matched the problem and helped them move forward."
        ),
    ]
    if f["selfish_first"]:
        qa.append(
            (
                f"What unkind idea came first, and what changed?",
                f"At first, {a.id} wanted to keep the drink for the treasure hunt instead of sharing it. Then {b.id} reminded {a.pronoun('object')} that someone sad in the brig needed it more, so the plan changed from selfish to kind."
            )
        )
    if f["spilled"]:
        qa.append(
            (
                "Did everything work on the first try?",
                f"No. The first carrying plan used {first_carrier.phrase}, and the drink spilled. After that, the children cleaned up, remade the drink, and used {used_carrier.phrase}, which was steadier."
            )
        )
    else:
        qa.append(
            (
                "How did they keep the drink safe on the way?",
                f"They carried it with {used_carrier.phrase}. That worked because the cup stayed level instead of wobbling."
            )
        )
    qa.append(
        (
            "What was the twist in the brig?",
            f"The person in the brig was not a bad prisoner at all. He was the ship's baker hiding there to test whether the crew would be kind while solving a problem."
        )
    )
    qa.append(
        (
            "What did the children learn at the end?",
            f"They learned that clever ideas matter most when they help someone. The ending shows that kindness can be a better treasure than gold."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"brig", "kindness", "problem_solving"}
    need = f["need"]
    barrier = f["barrier"]
    carrier = f["carrier"]
    heat_tool = f["heat_tool"]
    tags |= set(need.tags)
    tags |= set(barrier.tags)
    tags |= set(carrier.tags)
    tags |= set(heat_tool.tags)
    if "dark" in tags:
        tags.add("light")
    if "lock" in tags:
        tags.add("lock")
    if "guard" in tags:
        tags.add("guard")
    if "heat" in tags:
        tags.add("heat")
    if "tray" in tags:
        tags.add("tray")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


def explain_rejection(barrier: Barrier, barrier_tool: Tool, carrier: Carrier,
                      heat_tool: Tool, mix_tool: Tool) -> str:
    if not heat_tool.heats:
        return (
            f"(No story: {heat_tool.label} cannot warm milk, so the crew cannot make a real warm drink. "
            f"Choose a heat tool like kettle or stove.)"
        )
    if not mix_tool.mixes:
        return (
            f"(No story: {mix_tool.label} is not a good mixing tool here, so the drink never comes together properly. "
            f"Choose a spoon or whisk.)"
        )
    if not tool_can_solve(barrier, barrier_tool):
        return (
            f"(No story: {barrier_tool.label} does not solve the {barrier.id.replace('_', ' ')} problem. "
            f"Pick the tool that matches that barrier.)"
        )
    if carrier.sense < SENSE_MIN or not carrier.steady:
        return (
            f"(No story: carrying a hot drink in {carrier.phrase} is too wobbly for this world. "
            f"Choose a steadier carrier like a tray or both hands.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
valid_theme(T) :- theme(T).
valid_need(N) :- need(N).

good_heat(H) :- tool(H), heats(H).
good_mix(M)  :- tool(M), mixes(M).
solves(B, T) :- barrier(B), tool(T), needs_tool(B, T).
good_carrier(C) :- carrier(C), steady(C), sense(C, S), sense_min(M), S >= M.

valid(T, N, B, H, M, BT, C) :-
    valid_theme(T), valid_need(N), barrier(B),
    good_heat(H), good_mix(M),
    solves(B, BT), good_carrier(C).

spills(C) :- carrier(C), not steady(C).
spills(C) :- carrier(C), sense(C, S), sense_min(M), S < M.

story_outcome(B, BT, C, smooth) :-
    barrier(B), tool(BT), carrier(C), solves(B, BT), good_carrier(C).

story_outcome(B, BT, C, retry) :-
    barrier(B), tool(BT), carrier(C), solves(B, BT), spills(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for barrier_id, barrier in BARRIERS.items():
        lines.append(asp.fact("barrier", barrier_id))
        lines.append(asp.fact("needs_tool", barrier_id, barrier.requires_tool))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.heats:
            lines.append(asp.fact("heats", tool_id))
        if tool.mixes:
            lines.append(asp.fact("mixes", tool_id))
    for carrier_id, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", carrier_id))
        if carrier.steady:
            lines.append(asp.fact("steady", carrier_id))
        lines.append(asp.fact("sense", carrier_id, carrier.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/7."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(barrier_id: str, barrier_tool_id: str, carrier_id: str) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_barrier", barrier_id),
        asp.fact("chosen_tool", barrier_tool_id),
        asp.fact("chosen_carrier", carrier_id),
        f"story_pick({barrier_id},{barrier_tool_id},{carrier_id})." if False else "",
        f"chosen_outcome(smooth) :- solves({barrier_id},{barrier_tool_id}), good_carrier({carrier_id}).",
        f"chosen_outcome(retry) :- solves({barrier_id},{barrier_tool_id}), spills({carrier_id}).",
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_outcome/1."))
    atoms = asp.atoms(model, "chosen_outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    barrier = BARRIERS[params.barrier]
    barrier_tool = TOOLS[params.barrier_tool]
    carrier = CARRIERS[params.carrier]
    if not tool_can_solve(barrier, barrier_tool):
        return "invalid"
    if carrier_sensible(carrier):
        return "smooth"
    return "retry"


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

    for params in CURATED:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params.barrier, params.barrier_tool, params.carrier)
        if py_out != asp_out:
            rc = 1
            print(f"MISMATCH outcome for curated params: python={py_out} asp={asp_out} {params}")
            break
    else:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate crew solves a kindness problem with a twist ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--barrier", choices=BARRIERS)
    ap.add_argument("--heat-tool", choices=TOOLS)
    ap.add_argument("--mix-tool", choices=TOOLS)
    ap.add_argument("--barrier-tool", choices=TOOLS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--captain", choices=["Captain Mara", "Captain Reed"])
    ap.add_argument("--selfish-first", action="store_true")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    heat_tool_id = args.heat_tool
    mix_tool_id = args.mix_tool
    barrier_tool_id = args.barrier_tool
    carrier_id = args.carrier

    if heat_tool_id and heat_tool_id not in TOOLS:
        raise StoryError("(No story: unknown heat tool.)")
    if mix_tool_id and mix_tool_id not in TOOLS:
        raise StoryError("(No story: unknown mix tool.)")
    if barrier_tool_id and barrier_tool_id not in TOOLS:
        raise StoryError("(No story: unknown barrier tool.)")

    if args.barrier and args.barrier_tool:
        barrier = BARRIERS[args.barrier]
        barrier_tool = TOOLS[args.barrier_tool]
        carrier = CARRIERS[args.carrier] if args.carrier else CARRIERS["tray"]
        heat_tool = TOOLS[args.heat_tool] if args.heat_tool else TOOLS["kettle"]
        mix_tool = TOOLS[args.mix_tool] if args.mix_tool else TOOLS["whisk"]
        if not valid_combo(
            args.theme or next(iter(THEMES)),
            args.need or next(iter(NEEDS)),
            args.barrier,
            args.heat_tool or "kettle",
            args.mix_tool or "whisk",
            args.barrier_tool,
            args.carrier or "tray",
        ):
            raise StoryError(explain_rejection(barrier, barrier_tool, carrier, heat_tool, mix_tool))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.need is None or c[1] == args.need)
        and (args.barrier is None or c[2] == args.barrier)
        and (args.heat_tool is None or c[3] == args.heat_tool)
        and (args.mix_tool is None or c[4] == args.mix_tool)
        and (args.barrier_tool is None or c[5] == args.barrier_tool)
        and (args.carrier is None or c[6] == args.carrier)
    ]
    if not combos:
        if args.barrier and args.barrier_tool:
            barrier = BARRIERS[args.barrier]
            barrier_tool = TOOLS[args.barrier_tool]
            carrier = CARRIERS[args.carrier] if args.carrier else CARRIERS["tray"]
            heat_tool = TOOLS[args.heat_tool] if args.heat_tool else TOOLS["kettle"]
            mix_tool = TOOLS[args.mix_tool] if args.mix_tool else TOOLS["whisk"]
            raise StoryError(explain_rejection(barrier, barrier_tool, carrier, heat_tool, mix_tool))
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, need_id, barrier_id, heat_tool_id, mix_tool_id, barrier_tool_id, carrier_id = rng.choice(sorted(combos))
    child1, child1_gender = _pick_child(rng)
    child2, child2_gender = _pick_child(rng, avoid=child1)
    captain_name = args.captain or rng.choice(["Captain Mara", "Captain Reed"])
    captain_gender = "captain_f" if captain_name == "Captain Mara" else "captain_m"
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice([t for t in TRAITS if t != trait1] or TRAITS)
    selfish_first = True if args.selfish_first else rng.choice([True, False])
    return StoryParams(
        theme=theme_id,
        need=need_id,
        barrier=barrier_id,
        heat_tool=heat_tool_id,
        mix_tool=mix_tool_id,
        barrier_tool=barrier_tool_id,
        carrier=carrier_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        captain=captain_name,
        captain_gender=captain_gender,
        trait1=trait1,
        trait2=trait2,
        selfish_first=selfish_first,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in [
        ("theme", THEMES),
        ("need", NEEDS),
        ("barrier", BARRIERS),
        ("heat_tool", TOOLS),
        ("mix_tool", TOOLS),
        ("barrier_tool", TOOLS),
        ("carrier", CARRIERS),
    ]:
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(No story: unknown {field_name.replace('_', ' ')} '{value}'.)")
    if not valid_combo(
        params.theme,
        params.need,
        params.barrier,
        params.heat_tool,
        params.mix_tool,
        params.barrier_tool,
        params.carrier,
    ):
        raise StoryError(
            explain_rejection(
                BARRIERS[params.barrier],
                TOOLS[params.barrier_tool],
                CARRIERS[params.carrier],
                TOOLS[params.heat_tool],
                TOOLS[params.mix_tool],
            )
        )

    world = tell(
        theme=THEMES[params.theme],
        need=NEEDS[params.need],
        barrier=BARRIERS[params.barrier],
        heat_tool=TOOLS[params.heat_tool],
        mix_tool=TOOLS[params.mix_tool],
        barrier_tool=TOOLS[params.barrier_tool],
        carrier=CARRIERS[params.carrier],
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        trait1=params.trait1,
        trait2=params.trait2,
        selfish_first=params.selfish_first,
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
        print(asp_program("", "#show valid/7.\n#show story_outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  " + " | ".join(combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
                f"### {p.child1} & {p.child2}: {p.need} to the brig "
                f"({p.barrier}, {p.carrier})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
