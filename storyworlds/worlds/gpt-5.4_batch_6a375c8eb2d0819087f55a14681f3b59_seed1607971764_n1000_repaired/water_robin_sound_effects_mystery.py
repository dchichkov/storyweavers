#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/water_robin_sound_effects_mystery.py
===============================================================

A standalone story world for a small child-facing mystery: strange night sounds
seem to come from a porch, garden, or shed path after water has been left
dripping somewhere nearby. A child hears "plink," "tap-tap," or "flutter" in
the dim light and wonders what secret visitor has come. The mystery resolves
when the child and a calm grown-up follow the clues and discover both halves of
the sound: water striking a resonant surface, and a robin making the second
noise beside it.

The world model is intentionally small and classical:

* physical meters track wetness, puddles, sound, and clues
* emotional memes track fear, curiosity, calm, relief, and pride
* a few causal rules turn active water + a surface into a real sound, and a
  robin near water into extra clues and extra sound
* the rendered prose comes from simulated state and chosen outcome

There are two grounded endings:
* quiet approach  -> the child actually sees the robin solve the mystery
* hurried approach -> the robin flies off first, but the clues still solve it

Run it
------
    python storyworlds/worlds/gpt-5.4/water_robin_sound_effects_mystery.py
    python storyworlds/worlds/gpt-5.4/water_robin_sound_effects_mystery.py --all
    python storyworlds/worlds/gpt-5.4/water_robin_sound_effects_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/water_robin_sound_effects_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/water_robin_sound_effects_mystery.py --verify
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
LOUD_MIN = 1


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
    label: str
    opening: str
    hiding_spot: str
    affords_sources: set[str] = field(default_factory=set)
    affords_surfaces: set[str] = field(default_factory=set)
    robin_friendly: bool = True
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
class WaterSource:
    id: str
    label: str
    phrase: str
    sound: str
    clue: str
    provides_open_water: bool = True
    reaches: set[str] = field(default_factory=set)
    fix: str = ""
    ending: str = ""
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
class Surface:
    id: str
    label: str
    phrase: str
    resonance: int
    plink: str
    wet_mark: str
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
class RobinAction:
    id: str
    sound: str
    trace: str
    clue: str
    needs_water: bool = True
    seen_text: str = ""
    inferred_text: str = ""
    ending_text: str = ""
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
class Approach:
    id: str
    first_steps: str
    mood: str
    quiet: bool
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


def _r_water_sound(world: World) -> list[str]:
    source = world.get("source")
    surface = world.get("surface")
    child = world.get("child")
    if source.meters["active"] < THRESHOLD or surface.meters["ready"] < THRESHOLD:
        return []
    sig = ("water_sound", source.id, surface.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    surface.meters["wet"] += 1
    surface.meters["sound"] += 1
    child.memes["curiosity"] += 1
    child.memes["fear"] += 1
    world.facts["water_sound_heard"] = True
    return ["__water__"]


def _r_robin_clue(world: World) -> list[str]:
    robin = world.get("robin")
    source = world.get("source")
    child = world.get("child")
    if robin.meters["nearby"] < THRESHOLD:
        return []
    if world.facts["action_needs_water"] and source.meters["active"] < THRESHOLD:
        return []
    sig = ("robin_clue", world.facts["action_id"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    robin.meters["clue"] += 1
    robin.meters["sound"] += 1
    child.memes["curiosity"] += 1
    world.facts["robin_sound_heard"] = True
    world.facts["robin_clue_found"] = True
    return ["__robin__"]


CAUSAL_RULES = [
    Rule(name="water_sound", tag="physical", apply=_r_water_sound),
    Rule(name="robin_clue", tag="physical", apply=_r_robin_clue),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
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


def combo_reasonable(setting: Setting, source: WaterSource, surface: Surface, action: RobinAction) -> bool:
    if source.id not in setting.affords_sources:
        return False
    if surface.id not in setting.affords_surfaces:
        return False
    if surface.id not in source.reaches:
        return False
    if surface.resonance < LOUD_MIN:
        return False
    if action.needs_water and not source.provides_open_water:
        return False
    if not setting.robin_friendly:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for wid, source in WATER_SOURCES.items():
            for sfid, surface in SURFACES.items():
                for aid, action in ROBIN_ACTIONS.items():
                    if combo_reasonable(setting, source, surface, action):
                        out.append((sid, wid, sfid, aid))
    return sorted(out)


def outcome_of(params: "StoryParams") -> str:
    return "seen" if APPROACHES[params.approach].quiet else "inferred"


def explain_rejection(setting: Optional[Setting], source: Optional[WaterSource],
                      surface: Optional[Surface], action: Optional[RobinAction]) -> str:
    if setting and source and source.id not in setting.affords_sources:
        return (
            f"(No story: {source.phrase} does not belong in {setting.label}, so the mystery has no plausible water source there.)"
        )
    if setting and surface and surface.id not in setting.affords_surfaces:
        return (
            f"(No story: {surface.phrase} is not really part of {setting.label}, so the sound would not fit that place.)"
        )
    if source and surface and surface.id not in source.reaches:
        return (
            f"(No story: {source.phrase} would not hit {surface.phrase}, so there is no honest {surface.plink} sound to investigate.)"
        )
    if surface and surface.resonance < LOUD_MIN:
        return (
            f"(No story: {surface.phrase} is too soft and quiet to make a good mystery sound.)"
        )
    if source and action and action.needs_water and not source.provides_open_water:
        return (
            f"(No story: a robin cannot really {action.id.replace('_', ' ')} there without nearby water, so the clue chain would be weak.)"
        )
    return "(No story: this combination does not make a plausible small mystery.)"


def predict_solution(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "water_sound": bool(sim.facts.get("water_sound_heard")),
        "robin_clue": bool(sim.facts.get("robin_clue_found")),
        "fear": sim.get("child").memes["fear"],
        "curiosity": sim.get("child").memes["curiosity"],
    }


def introduce(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["calm"] = 1.0
    child.memes["curiosity"] = 1.0
    world.say(
        f"That evening, {child.id} stood with {helper.label_word} near {setting.label}. {setting.opening}"
    )
    world.say(
        f"The air smelled cool after water had been out all day, and the shadows around {setting.hiding_spot} looked full of secrets."
    )


def first_sound(world: World, child: Entity, source: WaterSource, surface: Surface) -> None:
    source.meters["active"] = 1.0
    surface.meters["ready"] = 1.0
    propagate(world, narrate=False)
    child.meters["heard_water"] = 1.0
    world.say(
        f"Then {source.sound} -- {surface.plink}! A drop from {source.phrase} landed on {surface.phrase}, and the little sound hopped through the dim air."
    )


def second_sound(world: World, child: Entity, robin: Entity, action: RobinAction) -> None:
    robin.meters["nearby"] = 1.0
    propagate(world, narrate=False)
    child.meters["heard_robin"] = 1.0
    world.say(
        f"A moment later came another noise: {action.sound}! It was not the same sound at all, and that made the mystery feel deeper."
    )


def worry(world: World, child: Entity, helper: Entity) -> None:
    pred = predict_solution(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_curiosity"] = pred["curiosity"]
    child.memes["wonder"] += 1
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f'{child.id} moved closer to {helper.label_word} and whispered, "Something is out there."'
        )
    else:
        world.say(
            f'{child.id} tipped {child.pronoun("possessive")} head and whispered, "That sounds like a puzzle."'
        )
    world.say(
        f'{helper.label_word.capitalize()} listened too. "{helper.pronoun().capitalize()} hear it," {helper.pronoun()} said. "Let\'s find out kindly."'
    )


def investigate(world: World, child: Entity, helper: Entity, approach: Approach, setting: Setting) -> None:
    child.memes["calm"] += 1
    helper.memes["calm"] += 1
    if approach.quiet:
        child.memes["brave"] += 1
    else:
        child.memes["fear"] += 1
    world.say(
        f"They {approach.first_steps} toward {setting.hiding_spot}. Every tiny sound seemed bigger because the yard was so {approach.mood}."
    )


def reveal_seen(world: World, child: Entity, helper: Entity, source: WaterSource,
                surface: Surface, action: RobinAction) -> None:
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    world.facts["saw_robin"] = True
    world.facts["solved"] = True
    world.say(
        f"There, in the silver-dark light, {child.id} finally saw the answer. {action.seen_text}"
    )
    world.say(
        f'"It was two sounds!" {child.id} said. "The water went {surface.plink}, and the robin went {action.sound}."'
    )
    world.say(
        f'{helper.label_word.capitalize()} smiled. "{helper.pronoun().capitalize()} solved it," {helper.pronoun()} said softly.'
    )


def reveal_inferred(world: World, child: Entity, helper: Entity, source: WaterSource,
                    surface: Surface, action: RobinAction) -> None:
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    child.memes["fear"] = 0.0
    world.facts["saw_robin"] = False
    world.facts["solved"] = True
    world.say(
        f"Just then there was a quick flutter, and the small visitor vanished into the dark before {child.id} could get a good look."
    )
    world.say(
        f"But the clues were waiting: {surface.wet_mark}, and {action.clue}. {helper.label_word.capitalize()} pointed gently and said that the mystery still had an answer."
    )
    world.say(
        f'{child.id} looked from the water to the clues and nodded. "{action.inferred_text} And the drop made the {surface.plink} sound," {child.pronoun()} said.'
    )


def settle(world: World, child: Entity, helper: Entity, source: WaterSource,
           action: RobinAction) -> None:
    child.memes["calm"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Together they {source.fix}. That changed the sharp little mystery noise without taking the water away from the robin."
    )
    world.say(
        f"Soon the yard sounded different. {source.ending} {action.ending_text}"
    )


def closing_image(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f'{child.id} took a deep breath and smiled. The night still held shadows, but now they felt like friendly corners instead of secrets.'
    )
    world.say(
        f"As they went back inside with {helper.label_word}, {child.id} listened once more and heard not a mystery anymore, but a small true story hidden in the dark."
    )


SETTINGS = {
    "porch": Setting(
        id="porch",
        label="the back porch",
        opening="A porch light made a soft gold circle on the floorboards.",
        hiding_spot="the steps and the flower pots",
        affords_sources={"gutter_chain", "watering_can"},
        affords_surfaces={"bucket", "step"},
        robin_friendly=True,
        tags={"porch", "night"},
    ),
    "garden": Setting(
        id="garden",
        label="the moonlit garden",
        opening="The bean poles threw long shadows across the soil.",
        hiding_spot="the birdbath and the stepping stones",
        affords_sources={"watering_can", "birdbath_overflow"},
        affords_surfaces={"stone", "lid"},
        robin_friendly=True,
        tags={"garden", "night"},
    ),
    "shed_path": Setting(
        id="shed_path",
        label="the little path beside the shed",
        opening="The shed wall held one stripe of moonlight and one stripe of shade.",
        hiding_spot="the old rake, the wall, and the narrow path",
        affords_sources={"gutter_chain", "watering_can"},
        affords_surfaces={"bucket", "stone"},
        robin_friendly=True,
        tags={"shed", "night"},
    ),
}

WATER_SOURCES = {
    "gutter_chain": WaterSource(
        id="gutter_chain",
        label="gutter chain",
        phrase="the loose rain chain under the gutter",
        sound="drip-drip",
        clue="a string of fresh drops on the boards",
        provides_open_water=True,
        reaches={"bucket", "step", "stone"},
        fix="looped the chain neatly so the drops fell straight down into a waiting pot",
        ending="The plinky drip faded to one soft drop now and then.",
        tags={"water", "rain"},
    ),
    "watering_can": WaterSource(
        id="watering_can",
        label="watering can",
        phrase="a watering can tipped a little on its side",
        sound="tip... drip",
        clue="a dark wet patch spreading from the can's mouth",
        provides_open_water=True,
        reaches={"stone", "lid", "bucket"},
        fix="set the watering can upright so the extra drops stopped slipping out",
        ending="The fussy dripping stopped completely.",
        tags={"water", "garden"},
    ),
    "birdbath_overflow": WaterSource(
        id="birdbath_overflow",
        label="birdbath",
        phrase="the birdbath brimmed too full after being topped up",
        sound="plip-plip",
        clue="a bead of water sliding over the rim",
        provides_open_water=True,
        reaches={"stone", "lid"},
        fix="moved a flat pebble inside the bath so the water settled instead of spilling over the edge",
        ending="The rim held still, and only a gentle shimmer stayed on the water.",
        tags={"water", "birdbath"},
    ),
}

SURFACES = {
    "bucket": Surface(
        id="bucket",
        label="bucket",
        phrase="an upside-down metal bucket",
        resonance=2,
        plink="plink",
        wet_mark="tiny silver drops shone on the bucket's side",
        tags={"metal", "sound"},
    ),
    "stone": Surface(
        id="stone",
        label="stepping stone",
        phrase="a flat stepping stone",
        resonance=1,
        plink="tik",
        wet_mark="a dark round spot spread over the stone",
        tags={"stone", "sound"},
    ),
    "lid": Surface(
        id="lid",
        label="potting-tin lid",
        phrase="a loose tin lid by a flower pot",
        resonance=2,
        plink="ting",
        wet_mark="the tin lid held a shining bead of water",
        tags={"metal", "sound"},
    ),
    "moss": Surface(
        id="moss",
        label="moss patch",
        phrase="a mossy patch by the wall",
        resonance=0,
        plink="soft pat",
        wet_mark="the moss looked darker where it was wet",
        tags={"soft"},
    ),
}

ROBIN_ACTIONS = {
    "bath_splash": RobinAction(
        id="bath_splash",
        sound="splish-splish",
        trace="water jumped in tiny bright arcs",
        clue="three neat robin prints dotted the edge nearby",
        needs_water=True,
        seen_text="A robin stood in the shallow water, shaking its red chest and flicking bright drops everywhere.",
        inferred_text="The robin must have been splashing in the water",
        ending_text="A robin came back, dipped once, and gave only one small cheerful splash.",
        tags={"robin", "water", "bird"},
    ),
    "beak_tap": RobinAction(
        id="beak_tap",
        sound="tap-tap",
        trace="a little beak knocked at the edge",
        clue="a tiny pale feather rested beside the wet place",
        needs_water=True,
        seen_text="A robin leaned over the water and tapped the edge with its beak before taking a quick sip.",
        inferred_text="The robin must have tapped the edge before it drank",
        ending_text="The robin perched quietly and drank without making a fuss.",
        tags={"robin", "bird"},
    ),
    "wing_shake": RobinAction(
        id="wing_shake",
        sound="frrt-flutter",
        trace="wet wings shivered in the air",
        clue="a few wet feathers clung to the ground nearby",
        needs_water=True,
        seen_text="A robin hopped up from the wet place and shook its wings so fast they whispered in the air.",
        inferred_text="The robin must have shaken its wet wings before flying off",
        ending_text="Then the robin lifted its wings once and settled into a branch, quiet at last.",
        tags={"robin", "bird", "wings"},
    ),
}

APPROACHES = {
    "quiet": Approach(
        id="quiet",
        first_steps="tiptoed slowly",
        mood="still",
        quiet=True,
        tags={"quiet"},
    ),
    "hurried": Approach(
        id="hurried",
        first_steps="hurried a little too fast",
        mood="jumpy",
        quiet=False,
        tags={"hurried"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Lucy", "Anna", "Rose"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Eli", "Theo", "Finn", "Jack"]
CHILD_TRAITS = ["curious", "careful", "bright-eyed", "thoughtful", "gentle"]


@dataclass
class StoryParams:
    setting: str
    source: str
    surface: str
    action: str
    approach: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
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


CURATED = [
    StoryParams(
        setting="porch",
        source="gutter_chain",
        surface="bucket",
        action="beak_tap",
        approach="quiet",
        child_name="Mia",
        child_gender="girl",
        helper_type="mother",
        trait="curious",
        seed=101,
    ),
    StoryParams(
        setting="garden",
        source="birdbath_overflow",
        surface="lid",
        action="bath_splash",
        approach="quiet",
        child_name="Ben",
        child_gender="boy",
        helper_type="father",
        trait="thoughtful",
        seed=102,
    ),
    StoryParams(
        setting="shed_path",
        source="watering_can",
        surface="stone",
        action="wing_shake",
        approach="hurried",
        child_name="Nora",
        child_gender="girl",
        helper_type="aunt",
        trait="careful",
        seed=103,
    ),
    StoryParams(
        setting="garden",
        source="watering_can",
        surface="stone",
        action="beak_tap",
        approach="hurried",
        child_name="Leo",
        child_gender="boy",
        helper_type="uncle",
        trait="bright-eyed",
        seed=104,
    ),
    StoryParams(
        setting="shed_path",
        source="gutter_chain",
        surface="bucket",
        action="bath_splash",
        approach="quiet",
        child_name="Rose",
        child_gender="girl",
        helper_type="mother",
        trait="gentle",
        seed=105,
    ),
]


KNOWLEDGE = {
    "water": [
        (
            "Why can a tiny drop of water make a sound?",
            "A drop of water can make a sound when it lands on something firm, like metal or stone. The surface shakes a little, and that tiny shake becomes a noise your ears can hear.",
        )
    ],
    "robin": [
        (
            "What is a robin?",
            "A robin is a small bird with a warm red or orange chest. Robins hop, drink, splash in shallow water, and often live near gardens and yards.",
        )
    ],
    "echo": [
        (
            "Why does metal sound louder than moss when water hits it?",
            "Metal is hard and springy, so it rings when something taps it. Moss is soft, so it swallows the little bump and makes much less sound.",
        )
    ],
    "mystery": [
        (
            "What is a clue in a mystery?",
            "A clue is a small true sign that helps you figure something out. It can be a sound, a feather, a wet mark, or anything else that points toward the answer.",
        )
    ],
    "night": [
        (
            "Why do sounds seem bigger at night?",
            "At night there are often fewer busy noises around. That makes tiny sounds stand out more and feel sharper to your ears.",
        )
    ],
    "birdbath": [
        (
            "Why do birds like shallow water?",
            "Birds like shallow water because they can drink from it safely and splash in it to clean their feathers. Very deep water is harder for a small bird to use.",
        )
    ],
}
KNOWLEDGE_ORDER = ["water", "robin", "echo", "mystery", "night", "birdbath"]


def tell(setting: Setting, source_cfg: WaterSource, surface_cfg: Surface, action_cfg: RobinAction,
         approach_cfg: Approach, child_name: str = "Mia", child_gender: str = "girl",
         helper_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    robin = world.add(
        Entity(
            id="robin",
            kind="character",
            type="bird",
            role="mystery_visitor",
            label="the robin",
        )
    )
    source = world.add(
        Entity(
            id="source",
            type="water_source",
            label=source_cfg.label,
            attrs={"phrase": source_cfg.phrase},
        )
    )
    surface = world.add(
        Entity(
            id="surface",
            type="surface",
            label=surface_cfg.label,
            attrs={"phrase": surface_cfg.phrase},
        )
    )

    world.facts.update(
        setting=setting,
        source_cfg=source_cfg,
        surface_cfg=surface_cfg,
        action_cfg=action_cfg,
        approach_cfg=approach_cfg,
        child=child,
        helper=helper,
        robin=robin,
        action_id=action_cfg.id,
        action_needs_water=action_cfg.needs_water,
        water_sound_heard=False,
        robin_sound_heard=False,
        robin_clue_found=False,
        saw_robin=False,
        solved=False,
        outcome=outcome_of(
            StoryParams(
                setting=setting.id,
                source=source_cfg.id,
                surface=surface_cfg.id,
                action=action_cfg.id,
                approach=approach_cfg.id,
                child_name=child_name,
                child_gender=child_gender,
                helper_type=helper_type,
                trait=trait,
            )
        ),
    )

    introduce(world, child, helper, setting)
    first_sound(world, child, source_cfg, surface_cfg)
    second_sound(world, child, robin, action_cfg)

    world.para()
    worry(world, child, helper)
    investigate(world, child, helper, approach_cfg, setting)

    world.para()
    if approach_cfg.quiet:
        reveal_seen(world, child, helper, source_cfg, surface_cfg, action_cfg)
    else:
        reveal_inferred(world, child, helper, source_cfg, surface_cfg, action_cfg)

    world.para()
    settle(world, child, helper, source_cfg, action_cfg)
    closing_image(world, child, helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    source = f["source_cfg"]
    action = f["action_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the words "water" and "robin" and uses sound effects.'
    )
    if outcome == "seen":
        return [
            base,
            f"Tell a night-time yard mystery where {child.id} hears {source.sound} and {action.sound}, follows the clues quietly, and sees a robin causing part of the sound.",
            f"Write a small mystery on {setting.label} where two different noises seem spooky at first, but a child solves them kindly and the ending becomes calm.",
        ]
    return [
        base,
        f"Tell a mystery where {child.id} hurries toward a strange sound, the robin flies away, and the answer is solved from wet clues instead of a full sighting.",
        f"Write a child-facing mystery set near {setting.label} where water makes one sound, a robin makes another, and the child figures it out after the visitor disappears.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    source = f["source_cfg"]
    surface = f["surface_cfg"]
    action = f["action_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.label_word}, who heard a small mystery near {setting.label}. The mystery turned out to be made by water and a robin together.",
        ),
        (
            "What made the mystery begin?",
            f"It began when a drop from {source.phrase} landed on {surface.phrase} and made a {surface.plink} sound. Then another different sound came, so it seemed as if something secret was hiding nearby.",
        ),
        (
            f"Why did the sounds feel mysterious to {child.id}?",
            f"The sounds came from the dim yard, where shadows hid the real cause. One sound was watery and one was fluttery, so they did not match at first and that made the puzzle feel bigger.",
        ),
    ]
    if outcome == "seen":
        qa.append(
            (
                f"What did {child.id} discover?",
                f"{child.id} quietly saw a robin by the water. The robin made the {action.sound} sound, while the water made the {surface.plink} sound on {surface.label}.",
            )
        )
    else:
        qa.append(
            (
                f"How was the mystery solved even though the robin flew away?",
                f"{child.id} and {helper.label_word} followed the clues instead of giving up. The wet marks and small feathers showed that a robin had been there, and the drop still explained the {surface.plink} sound.",
            )
        )
    qa.append(
        (
            "How did they change things at the end?",
            f"They {source.fix}. That stopped the sharp extra noise, but it still left a kinder place for the robin to drink or wash.",
        )
    )
    qa.append(
        (
            f"How did {child.id} feel at the end?",
            f"{child.id} felt relieved and proud. The dark place did not feel spooky anymore because the sounds finally had a true answer.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"water", "robin", "echo", "mystery", "night"}
    if world.facts["source_cfg"].id == "birdbath_overflow" or world.facts["action_cfg"].id == "bath_splash":
        tags.add("birdbath")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
source_in_setting(S, W) :- setting(S), source(W), affords_source(S, W).
surface_in_setting(S, F) :- setting(S), surface(F), affords_surface(S, F).
reachable(W, F) :- reaches(W, F).
loud_enough(F) :- surface(F), resonance(F, R), loud_min(M), R >= M.
water_ready(W) :- source(W), open_water(W).

valid(S, W, F, A) :- setting(S), source(W), surface(F), action(A),
                     source_in_setting(S, W),
                     surface_in_setting(S, F),
                     reachable(W, F),
                     loud_enough(F),
                     (not action_needs_water(A); water_ready(W)).

outcome(seen) :- chosen_approach(quiet).
outcome(inferred) :- chosen_approach(hurried).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for wid in sorted(SETTINGS[sid].affords_sources):
            lines.append(asp.fact("affords_source", sid, wid))
        for sfid in sorted(SETTINGS[sid].affords_surfaces):
            lines.append(asp.fact("affords_surface", sid, sfid))
    for wid, source in WATER_SOURCES.items():
        lines.append(asp.fact("source", wid))
        if source.provides_open_water:
            lines.append(asp.fact("open_water", wid))
        for sfid in sorted(source.reaches):
            lines.append(asp.fact("reaches", wid, sfid))
    for sfid, surface in SURFACES.items():
        lines.append(asp.fact("surface", sfid))
        lines.append(asp.fact("resonance", sfid, surface.resonance))
    for aid, action in ROBIN_ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if action.needs_water:
            lines.append(asp.fact("action_needs_water", aid))
    lines.append(asp.fact("loud_min", LOUD_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_approach", params.approach)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _verify_generate_smoke() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise AssertionError("smoke test generated an empty story")
    if "robin" not in sample.story.lower() or "water" not in sample.story.lower():
        raise AssertionError("smoke test story missed required seed words")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=True, qa=True, header="### smoke")
    out = buf.getvalue()
    if "### smoke" not in out or "Q:" not in out:
        raise AssertionError("emit smoke test did not produce expected output")


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
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
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
        _verify_generate_smoke()
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a small mystery made from water sounds and a robin."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=WATER_SOURCES)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--action", choices=ROBIN_ACTIONS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--trait", choices=CHILD_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    source = WATER_SOURCES.get(args.source) if args.source else None
    surface = SURFACES.get(args.surface) if args.surface else None
    action = ROBIN_ACTIONS.get(args.action) if args.action else None

    if any(x is not None for x in (setting, source, surface, action)):
        chosen = {
            "setting": setting,
            "source": source,
            "surface": surface,
            "action": action,
        }
        filled = {k: v for k, v in chosen.items() if v is not None}
        if len(filled) == 4 and not combo_reasonable(setting, source, surface, action):
            raise StoryError(explain_rejection(setting, source, surface, action))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.source is None or combo[1] == args.source)
        and (args.surface is None or combo[2] == args.surface)
        and (args.action is None or combo[3] == args.action)
    ]
    if not combos:
        raise StoryError(explain_rejection(setting, source, surface, action))

    setting_id, source_id, surface_id, action_id = rng.choice(combos)
    approach_id = args.approach or rng.choice(sorted(APPROACHES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(CHILD_TRAITS)

    return StoryParams(
        setting=setting_id,
        source=source_id,
        surface=surface_id,
        action=action_id,
        approach=approach_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.source not in WATER_SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.action not in ROBIN_ACTIONS:
        raise StoryError(f"(Unknown action: {params.action})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")

    setting = SETTINGS[params.setting]
    source = WATER_SOURCES[params.source]
    surface = SURFACES[params.surface]
    action = ROBIN_ACTIONS[params.action]
    if not combo_reasonable(setting, source, surface, action):
        raise StoryError(explain_rejection(setting, source, surface, action))

    world = tell(
        setting=setting,
        source_cfg=source,
        surface_cfg=surface,
        action_cfg=action,
        approach_cfg=APPROACHES[params.approach],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (setting, source, surface, action) combos:\n")
        for setting_id, source_id, surface_id, action_id in combos:
            print(f"  {setting_id:10} {source_id:18} {surface_id:8} {action_id}")
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
            header = (
                f"### {p.child_name}: {p.setting}, {p.source}, {p.surface}, {p.action}, {outcome_of(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
