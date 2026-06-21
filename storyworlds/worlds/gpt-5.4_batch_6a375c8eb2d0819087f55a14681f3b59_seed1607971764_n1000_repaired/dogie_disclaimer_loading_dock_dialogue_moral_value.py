#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dogie_disclaimer_loading_dock_dialogue_moral_value.py
================================================================================

A standalone story world for a tiny "space-adventure loading dock" domain.

Premise
-------
A child helper and a small robot dogie are at a loading dock in a bright space
harbor. Something important is just out of easy reach. The child is tempted to
use a quick, unsafe shortcut. The dogie repeats a funny safety disclaimer,
help arrives, and the pair solve the problem the right way.

The world model carries:
- physical meters ("danger", "jammed", "retrieved", "organized")
- emotional memes ("wonder", "impatience", "fear", "trust", "pride", "lesson")

The prose is driven by the simulated state, not by one frozen template.  The
domain emphasizes dialogue, repetition, and a clear moral value: asking for
help and choosing the safe way is brave.

Run it
------
    python storyworlds/worlds/gpt-5.4/dogie_disclaimer_loading_dock_dialogue_moral_value.py
    python storyworlds/worlds/gpt-5.4/dogie_disclaimer_loading_dock_dialogue_moral_value.py --lost helmet_badge --shortcut belt_reach
    python storyworlds/worlds/gpt-5.4/dogie_disclaimer_loading_dock_dialogue_moral_value.py --fix wait_button
    python storyworlds/worlds/gpt-5.4/dogie_disclaimer_loading_dock_dialogue_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/dogie_disclaimer_loading_dock_dialogue_moral_value.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dogie_disclaimer_loading_dock_dialogue_moral_value.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/dogie_disclaimer_loading_dock_dialogue_moral_value.py --json
    python storyworlds/worlds/gpt-5.4/dogie_disclaimer_loading_dock_dialogue_moral_value.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    machine: bool = False
    # Unified physical / emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain_female"}
        male = {"boy", "father", "man", "captain_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        if self.type in {"mother", "father", "captain_female", "captain_male"}:
            return "captain"
        return self.type


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
class LostThing:
    id: str
    label: str
    phrase: str
    need: str
    place_text: str
    location_kind: str          # under_belt | high_stack | closing_door
    consequence: str
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
class Shortcut:
    id: str
    label: str
    action_text: str
    risk_text: str
    zone: str                   # under_belt | high_stack | closing_door
    danger: int
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
class Fix:
    id: str
    label: str
    solve_text: str
    method_text: str
    works_for: set[str] = field(default_factory=set)
    calm_text: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def _r_hazard(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    dock = world.get("dock")
    dogie = world.get("dogie")
    if hero.meters["unsafe_try"] < THRESHOLD:
        return out
    sig = ("hazard", world.facts.get("shortcut"))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dock.meters["danger"] += 1
    hero.memes["fear"] += 1
    dogie.memes["alarm"] += 1
    out.append("__hazard__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    dogie = world.get("dogie")
    dock = world.get("dock")
    item = world.get("item")
    if item.meters["retrieved"] < THRESHOLD:
        return out
    sig = ("relief", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dock.meters["danger"] = 0.0
    hero.memes["relief"] += 1
    dogie.memes["joy"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hazard", tag="physical", apply=_r_hazard),
    Rule(name="relief", tag="social", apply=_r_relief),
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


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def hazard_at_risk(lost: LostThing, shortcut: Shortcut) -> bool:
    return lost.location_kind == shortcut.zone


def fix_works(lost: LostThing, fix: Fix) -> bool:
    return lost.location_kind in fix.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for lost_id, lost in LOST.items():
        for sid, shortcut in SHORTCUTS.items():
            if not hazard_at_risk(lost, shortcut):
                continue
            for fix_id, fix in FIXES.items():
                if fix_works(lost, fix):
                    combos.append((lost_id, sid, fix_id))
    return combos


def explain_rejection(lost: LostThing, shortcut: Shortcut, fix: Optional[Fix] = None) -> str:
    if not hazard_at_risk(lost, shortcut):
        return (
            f"(No story: trying to use {shortcut.label} does not honestly fit "
            f"{lost.place_text}. Pick a shortcut that matches where the item is.)"
        )
    if fix is not None and not fix_works(lost, fix):
        return (
            f"(No story: {fix.label} would not solve the problem of something "
            f"{lost.place_text}. Pick a fix that really reaches that spot.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["unsafe_try"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("dock").meters["danger"],
        "fear": hero.memes["fear"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, dogie: Entity, lost: LostThing) -> None:
    hero.memes["wonder"] += 1
    dogie.memes["loyalty"] += 1
    world.say(
        f"Blue loading lights blinked along the loading dock like little stars, "
        f"and {hero.id} marched between stacked moon-crates with {dogie.id}, a small silver dogie whose tail-light winked blue-blue-blue."
    )
    world.say(
        f"They were helping sort cargo for the morning shuttle when {hero.id} noticed {lost.phrase} {lost.place_text}."
    )
    world.say(
        f'"Oh no," {hero.id} whispered. "We need it because {lost.need}."'
    )


def describe_need(world: World, captain: Entity, lost: LostThing) -> None:
    world.say(
        f'From farther down the dock, the {captain.title_word} was calling numbers to the cargo bots. '
        f'The whole place hummed and clicked and hummed again.'
    )
    world.say(
        f"{lost.consequence}"
    )


def temptation(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f'{hero.id} took one eager step closer. "Maybe I can {shortcut.action_text}," {hero.pronoun()} said.'
    )


def disclaimer_warning(world: World, dogie: Entity, hero: Entity, shortcut: Shortcut) -> None:
    pred = predict_trouble(world)
    dogie.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{dogie.id} planted all four paws and beeped, "Dock disclaimer! Dock disclaimer! {shortcut.risk_text}."'
    )
    world.say(
        f'"No quick zip. No quick slip. No quick squeeze," {dogie.id} added.'
    )
    world.say(
        f'{hero.id} looked again, and the loading dock suddenly felt bigger and busier than before.'
    )


def unsafe_try(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.meters["unsafe_try"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Still, the shining thing looked so close that {hero.id} leaned in to {shortcut.action_text}.'
    )
    world.say(
        f"At once, a warning light flashed amber, and the dock answered with a sharp little beep-beep-beep."
    )


def pull_back(world: World, dogie: Entity, hero: Entity) -> None:
    dogie.memes["care"] += 1
    hero.memes["trust"] += 1
    world.say(
        f'{dogie.id} gave a tiny worried bark and nudged {hero.id} back with a soft metal nose.'
    )
    world.say(
        f'"Back, back, back," {dogie.id} said. "Safe paws. Safe hands."'
    )


def captain_arrives(world: World, captain: Entity) -> None:
    captain.memes["calm"] += 1
    world.say(
        f'The {captain.title_word} came over at once, boots ringing on the dock. '
        f'"I heard that alarm," {captain.pronoun()} said, but {captain.pronoun()} kept {captain.pronoun("possessive")} voice low and steady.'
    )


def explain_and_help(world: World, hero: Entity, captain: Entity, lost: LostThing, fix: Fix) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f'"I wanted to hurry," {hero.id} admitted. "I thought I could do it alone."'
    )
    world.say(
        f'"Thank you for telling the truth," the {captain.title_word} said. "{fix.calm_text}"'
    )
    world.say(
        f'Then the {captain.title_word} used {fix.label} and {fix.method_text}.'
    )
    item = world.get("item")
    item.meters["retrieved"] += 1
    item.meters["safe"] += 1
    world.get("dock").meters["organized"] += 1
    propagate(world, narrate=False)
    world.say(fix.solve_text.replace("{item}", lost.label))


def lesson(world: World, hero: Entity, dogie: Entity, captain: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["pride"] += 1
    dogie.memes["pride"] += 1
    world.say(
        f'The {captain.title_word} crouched beside them. "Fast is not the same as brave," {captain.pronoun()} said. "Brave is stopping, speaking up, and choosing the safe way."'
    )
    world.say(
        f'{hero.id} nodded. "{hero.pronoun("possessive").capitalize()} brave can ask for help," {hero.pronoun()} said slowly.'
    )
    world.say(
        f'"Correct," said {dogie.id}. "Dock disclaimer: asking for help is star-smart."'
    )


def ending(world: World, hero: Entity, dogie: Entity, lost: LostThing) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f'Soon the loading dock was humming happily again. {hero.id} clipped {lost.label} into place, and the next cargo pod rolled exactly where it should.'
    )
    world.say(
        f'{dogie.id} trotted in a proud circle, tail-light blinking blue-blue-blue.'
    )
    world.say(
        f'And when another tiny problem popped up later, {hero.id} smiled first and said, "Safe way, then space way."'
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    lost: LostThing,
    shortcut: Shortcut,
    fix: Fix,
    *,
    hero_name: str = "Nova",
    hero_type: str = "girl",
    dogie_name: str = "Comet",
    captain_type: str = "captain_female",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    dogie = world.add(Entity(id="dogie", kind="character", type="robot_dog", label=dogie_name, role="dogie"))
    captain = world.add(Entity(id="captain", kind="character", type=captain_type, label="the captain", role="captain"))
    dock = world.add(Entity(id="dock", kind="thing", type="loading_dock", label="loading dock", role="setting", machine=True))
    item = world.add(Entity(id="item", kind="thing", type="lost", label=lost.label, role="lost_item", movable=True))

    # Initialize state read by rules before any propagation.
    hero.meters["unsafe_try"] = 0.0
    hero.memes["fear"] = 0.0
    dogie.memes["alarm"] = 0.0
    dock.meters["danger"] = 0.0
    dock.meters["organized"] = 0.0
    item.meters["retrieved"] = 0.0

    world.facts.update(
        lost=lost,
        shortcut=shortcut.id,
        shortcut_cfg=shortcut,
        fix=fix,
        hero=hero,
        dogie=dogie,
        captain=captain,
        item=item,
    )

    introduce(world, hero, dogie, lost)
    describe_need(world, captain, lost)

    world.para()
    temptation(world, hero, shortcut)
    disclaimer_warning(world, dogie, hero, shortcut)
    unsafe_try(world, hero, shortcut)
    pull_back(world, dogie, hero)

    world.para()
    captain_arrives(world, captain)
    explain_and_help(world, hero, captain, lost, fix)
    lesson(world, hero, dogie, captain)

    world.para()
    ending(world, hero, dogie, lost)

    world.facts.update(
        danger_happened=world.get("dock").meters["danger"] < THRESHOLD and hero.meters["unsafe_try"] >= THRESHOLD,
        retrieved=item.meters["retrieved"] >= THRESHOLD,
        organized=world.get("dock").meters["organized"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
LOST = {
    "helmet_badge": LostThing(
        id="helmet_badge",
        label="the little star badge",
        phrase="the little star badge from a cargo helmet",
        need="the cargo teams used that badge to mark the shuttle for takeoff",
        place_text="under the slow-moving belt at the edge of the dock",
        location_kind="under_belt",
        consequence="Without it, one silver crate could be sent to the wrong rocket bay.",
        tags={"badge", "belt", "loading_dock"},
    ),
    "route_chip": LostThing(
        id="route_chip",
        label="the route chip",
        phrase="the glowing route chip",
        need="the route chip told the supply cart which stack to visit next",
        place_text="on top of the tallest stack of moon-crates",
        location_kind="high_stack",
        consequence="Without it, the supply cart would blink in circles and waste the whole morning.",
        tags={"chip", "stack", "loading_dock"},
    ),
    "bay_key": LostThing(
        id="bay_key",
        label="the bay key",
        phrase="the tiny bay key",
        need="the dock doors needed that key to know which shuttle to welcome",
        place_text="just inside the sliding cargo doors",
        location_kind="closing_door",
        consequence="Without it, the door lights would keep flashing red-red-red.",
        tags={"key", "door", "loading_dock"},
    ),
}

SHORTCUTS = {
    "belt_reach": Shortcut(
        id="belt_reach",
        label="the moving belt",
        action_text="duck under the belt and snatch it quickly",
        risk_text="moving belts can bump heads and pinch sleeves",
        zone="under_belt",
        danger=2,
        tags={"belt", "unsafe"},
    ),
    "crate_climb": Shortcut(
        id="crate_climb",
        label="the wobbly crate stack",
        action_text="climb the wobbly crates and grab it from the top",
        risk_text="wobbly stacks can tip and tumble",
        zone="high_stack",
        danger=2,
        tags={"stack", "unsafe"},
    ),
    "door_reach": Shortcut(
        id="door_reach",
        label="the sliding cargo doors",
        action_text="slip a hand between the doors before they close",
        risk_text="sliding doors can squeeze fingers and surprise you",
        zone="closing_door",
        danger=2,
        tags={"door", "unsafe"},
    ),
}

FIXES = {
    "belt_stop_grabber": Fix(
        id="belt_stop_grabber",
        label="the red stop switch and a long grabber",
        method_text="stopped the belt, reached under safely with the grabber, and lifted the item out",
        solve_text='In one smooth move, the danger was gone, and {item} came up safe and shining.',
        works_for={"under_belt"},
        calm_text="The dock likes helpers who ask first.",
        tags={"belt", "grabber", "safe_tool"},
    ),
    "ladder_hook": Fix(
        id="ladder_hook",
        label="the dock ladder and a magnet hook",
        method_text="set the ladder flat and steady, climbed it carefully, and lifted the item down with the hook",
        solve_text='A moment later, {item} was back in careful hands instead of wobbling above everyone.',
        works_for={"high_stack"},
        calm_text="We use steady tools for high places.",
        tags={"ladder", "hook", "safe_tool"},
    ),
    "wait_button": Fix(
        id="wait_button",
        label="the hold-open button and a padded reach stick",
        method_text="pressed the hold-open button, waited for the doors to pause, and drew the item out with the reach stick",
        solve_text='The red-red-red door lights softened to green, and {item} slid free without a single squeezed finger.',
        works_for={"closing_door"},
        calm_text="Machines work best when people give them time.",
        tags={"button", "door", "safe_tool"},
    ),
}

GIRL_NAMES = ["Nova", "Lina", "Mira", "Tess", "Ayla", "Vega"]
BOY_NAMES = ["Orion", "Milo", "Jett", "Nico", "Pax", "Arlo"]
DOGIE_NAMES = ["Comet", "Spark", "Pebble", "Orbit", "Zip"]
TRAITS = ["eager", "curious", "bright", "helpful", "quick", "hopeful"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    lost: str
    shortcut: str
    fix: str
    hero_name: str
    hero_type: str
    dogie_name: str
    captain_type: str
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
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
    "loading_dock": [
        (
            "What is a loading dock?",
            "A loading dock is a place where boxes and cargo are moved on and off trucks or ships. In a space harbor story, it is where supplies get sorted for rockets and shuttles."
        )
    ],
    "belt": [
        (
            "Why can a moving belt be dangerous?",
            "A moving belt keeps rolling even when you are in a hurry. If someone reaches into the wrong place, it can bump them or catch clothes and make them fall."
        )
    ],
    "stack": [
        (
            "Why should you not climb a wobbly stack of boxes?",
            "A wobbly stack can tip if the boxes shift under your feet. That means the boxes can tumble and someone can get hurt."
        )
    ],
    "door": [
        (
            "Why should you keep your hands away from closing doors?",
            "Closing doors can squeeze fingers before you pull them back. It is safer to wait for a grown-up or use the proper button."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that helps you pick something up from far away. It lets you reach without putting your hands in a dangerous spot."
        )
    ],
    "ladder": [
        (
            "Why is a steady ladder safer than climbing boxes?",
            "A ladder is made for climbing and standing on. Boxes can slide and wobble, but a ladder gives your feet a firmer place."
        )
    ],
    "button": [
        (
            "Why do machines sometimes need a special button?",
            "A special button tells the machine exactly what to do, like stopping or holding still. Using the right control is safer than trying to beat the machine."
        )
    ],
    "safe_tool": [
        (
            "What is the safe way to solve a hard problem at work?",
            "The safe way is to stop, look carefully, and use the right tool or ask a grown-up helper. Going slowly can protect people and still fix the problem."
        )
    ],
    "unsafe": [
        (
            "Is hurrying always brave?",
            "No. Hurrying can make people skip the safe choice. Real bravery can mean slowing down, telling the truth, and asking for help."
        )
    ],
}
KNOWLEDGE_ORDER = ["loading_dock", "belt", "stack", "door", "grabber", "ladder", "button", "safe_tool", "unsafe"]


def generation_prompts(world: World) -> list[str]:
    lost = world.facts["lost"]
    shortcut = world.facts["shortcut_cfg"]
    hero = world.facts["hero"]
    dogie = world.facts["dogie"]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old set at a loading dock. Include the words "dogie" and "disclaimer".',
        f"Tell a gentle loading-dock story where {hero.label} and a robot dogie named {dogie.label} need {lost.label}, but a quick idea involving {shortcut.label} turns out to be unsafe.",
        'Write a story with lots of dialogue and a repeated safety line, where the moral value is that asking for help is brave.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    dogie = world.facts["dogie"]
    captain = world.facts["captain"]
    lost = world.facts["lost"]
    shortcut = world.facts["shortcut_cfg"]
    fix = world.facts["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child helper on a loading dock, and {dogie.label}, a small robot dogie. They were trying to get {lost.label} back so the dock could do its job."
        ),
        (
            f"Why did {hero.label} want {lost.label} back?",
            f"{hero.label} wanted it back because {lost.need}. If it stayed lost, {lost.consequence.lower()}"
        ),
        (
            f"What warning did {dogie.label} give?",
            f'{dogie.label} repeated a safety disclaimer about {shortcut.risk_text}. The repeated warning mattered because {hero.label} was feeling impatient and about to try a shortcut.'
        ),
        (
            f"Why was {hero.label}'s quick idea unsafe?",
            f"The quick idea was to {shortcut.action_text}, and that could cause trouble because {shortcut.risk_text}. The danger fit the exact place where the missing item had ended up."
        ),
        (
            "How was the problem solved?",
            f"The captain used {fix.label} and {fix.method_text}. That fixed the problem without anyone getting pinched, squeezed, or knocked over."
        ),
        (
            "What is the moral of the story?",
            f"The story teaches that asking for help and using the safe way is a brave choice. {hero.label} learned that telling the truth and slowing down can protect everyone on the dock."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["lost"].tags) | set(world.facts["shortcut_cfg"].tags) | set(world.facts["fix"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hazard(L,S) :- lost(L), shortcut(S), location_kind(L,Z), zone(S,Z).
works(L,F)  :- lost(L), fix(F), location_kind(L,Z), fix_for(F,Z).
valid(L,S,F) :- hazard(L,S), works(L,F).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lost_id, lost in LOST.items():
        lines.append(asp.fact("lost", lost_id))
        lines.append(asp.fact("location_kind", lost_id, lost.location_kind))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("zone", sid, shortcut.zone))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for zone in sorted(fix.works_for):
            lines.append(asp.fact("fix_for", fix_id, zone))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    # Smoke tests for ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Random smoke test failed: empty story.)")
        print("OK: random resolve+generate smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        lost="helmet_badge",
        shortcut="belt_reach",
        fix="belt_stop_grabber",
        hero_name="Nova",
        hero_type="girl",
        dogie_name="Comet",
        captain_type="captain_female",
        trait="eager",
    ),
    StoryParams(
        lost="route_chip",
        shortcut="crate_climb",
        fix="ladder_hook",
        hero_name="Orion",
        hero_type="boy",
        dogie_name="Orbit",
        captain_type="captain_male",
        trait="bright",
    ),
    StoryParams(
        lost="bay_key",
        shortcut="door_reach",
        fix="wait_button",
        hero_name="Mira",
        hero_type="girl",
        dogie_name="Spark",
        captain_type="captain_female",
        trait="helpful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a loading dock, a dogie, a safety disclaimer, and a brave safe choice."
    )
    ap.add_argument("--lost", choices=LOST)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--dogie-name")
    ap.add_argument("--captain-type", choices=["captain_female", "captain_male"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lost and args.shortcut:
        lost = LOST[args.lost]
        shortcut = SHORTCUTS[args.shortcut]
        if not hazard_at_risk(lost, shortcut):
            raise StoryError(explain_rejection(lost, shortcut))
    if args.lost and args.fix:
        lost = LOST[args.lost]
        fix = FIXES[args.fix]
        if not fix_works(lost, fix):
            shortcut = SHORTCUTS[args.shortcut] if args.shortcut else next(iter(SHORTCUTS.values()))
            raise StoryError(explain_rejection(lost, shortcut, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.lost is None or combo[0] == args.lost)
        and (args.shortcut is None or combo[1] == args.shortcut)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lost_id, shortcut_id, fix_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    dogie_name = args.dogie_name or rng.choice(DOGIE_NAMES)
    captain_type = args.captain_type or rng.choice(["captain_female", "captain_male"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        lost=lost_id,
        shortcut=shortcut_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_type=hero_type,
        dogie_name=dogie_name,
        captain_type=captain_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.lost not in LOST:
        raise StoryError(f"(Invalid lost item: {params.lost})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Invalid shortcut: {params.shortcut})")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")

    lost = LOST[params.lost]
    shortcut = SHORTCUTS[params.shortcut]
    fix = FIXES[params.fix]
    if not hazard_at_risk(lost, shortcut):
        raise StoryError(explain_rejection(lost, shortcut))
    if not fix_works(lost, fix):
        raise StoryError(explain_rejection(lost, shortcut, fix))

    world = tell(
        lost=lost,
        shortcut=shortcut,
        fix=fix,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        dogie_name=params.dogie_name,
        captain_type=params.captain_type,
    )

    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    story = sample.story
    hero_name = sample.params.hero_name
    dogie_name = sample.params.dogie_name
    story = story.replace("hero", hero_name).replace("dogie", dogie_name)
    if header:
        print(header)
    print(story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lost, shortcut, fix) combos:\n")
        for lost, shortcut, fix in combos:
            print(f"  {lost:12} {shortcut:12} {fix}")
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
            header = f"### {p.hero_name} & {p.dogie_name}: {p.lost} / {p.shortcut} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
