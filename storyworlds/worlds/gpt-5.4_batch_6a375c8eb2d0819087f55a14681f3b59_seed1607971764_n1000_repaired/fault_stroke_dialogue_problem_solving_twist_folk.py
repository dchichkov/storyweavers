#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fault_stroke_dialogue_problem_solving_twist_folk.py
===============================================================================

A standalone story world for a small folk-tale-like domain: a village bell is
supposed to ring at dawn, but something goes wrong. A child helper is blamed,
dialogue carries the search for the truth, a practical repair solves the
problem, and the twist is that the blamed child was not at fault after all.

The world models:

- typed entities with physical meters and emotional memes
- a short causal chain from hidden fault -> bell silence -> blame/fear
- investigation with dialogue and problem solving
- a twist outcome: the supposed culprit is innocent once the true cause is found
- constraint-checked cause/fix pairs with an inline ASP twin

Run it
------
    python storyworlds/worlds/gpt-5.4/fault_stroke_dialogue_problem_solving_twist_folk.py
    python storyworlds/worlds/gpt-5.4/fault_stroke_dialogue_problem_solving_twist_folk.py --cause frayed_rope
    python storyworlds/worlds/gpt-5.4/fault_stroke_dialogue_problem_solving_twist_folk.py --fix oil_hinge
    python storyworlds/worlds/gpt-5.4/fault_stroke_dialogue_problem_solving_twist_folk.py --all
    python storyworlds/worlds/gpt-5.4/fault_stroke_dialogue_problem_solving_twist_folk.py --qa --json
    python storyworlds/worlds/gpt-5.4/fault_stroke_dialogue_problem_solving_twist_folk.py --verify
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
CARE_MIN = 2


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
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
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
class Bell:
    id: str
    tower: str
    shine: str
    echo: str
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
class Cause:
    id: str
    clue: str
    trouble: str
    true_fault: str
    severity: int
    repair_need: str
    repair_text: str
    twist_line: str
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
    tool: str
    method: str
    cures: set[str] = field(default_factory=set)
    care: int = 0
    success_text: str = ""
    fail_text: str = ""
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


def _r_silence(world: World) -> list[str]:
    bell = world.get("bell")
    if bell.meters["jammed"] < THRESHOLD:
        return []
    sig = ("silence", "bell")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    square = world.get("square")
    child = world.get("child")
    elder = world.get("elder")
    square.meters["lateness"] += 1
    child.memes["worry"] += 1
    elder.memes["suspicion"] += 1
    return ["__silence__"]


def _r_blame(world: World) -> list[str]:
    child = world.get("child")
    elder = world.get("elder")
    if elder.memes["suspicion"] < THRESHOLD or child.memes["worry"] < THRESHOLD:
        return []
    sig = ("blame", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hurt"] += 1
    child.memes["resolve"] += 1
    return ["__blame__"]


def _r_clear_name(world: World) -> list[str]:
    child = world.get("child")
    elder = world.get("elder")
    bell = world.get("bell")
    if world.facts.get("true_cause_found") != True:
        return []
    sig = ("clear_name", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    elder.memes["remorse"] += 1
    elder.memes["suspicion"] = 0.0
    if bell.meters["ringing"] >= THRESHOLD:
        child.memes["joy"] += 1
    return ["__cleared__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="silence", tag="physical", apply=_r_silence),
    Rule(name="blame", tag="social", apply=_r_blame),
    Rule(name="clear_name", tag="social", apply=_r_clear_name),
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


def valid_fix_for(cause: Cause, fix: Fix) -> bool:
    return cause.id in fix.cures


def sensible_fixes() -> list[Fix]:
    return [fx for fx in FIXES.values() if fx.care >= CARE_MIN]


def repair_succeeds(cause: Cause, fix: Fix) -> bool:
    return valid_fix_for(cause, fix) and fix.care >= CARE_MIN


def explain_cause_mismatch(cause: Cause, fix: Fix) -> str:
    return (
        f"(No story: {fix.method} does not solve {cause.trouble}. "
        f"The hidden fault here is {cause.true_fault}, so the repair must match that.)"
    )


def explain_fix_care(fix: Fix) -> str:
    return (
        f"(Refusing fix '{fix.id}': it is too rough or careless for this folk tale "
        f"(care={fix.care} < {CARE_MIN}). Choose a steadier repair.)"
    )


def predict_bell(world: World, cause_id: str) -> dict:
    sim = world.copy()
    cause = CAUSES[cause_id]
    bell = sim.get("bell")
    bell.meters["jammed"] += 1
    bell.attrs["cause"] = cause.id
    sim.facts["cause_found"] = False
    sim.facts["true_cause_found"] = False
    propagate(sim, narrate=False)
    return {
        "silent": bell.meters["jammed"] >= THRESHOLD,
        "lateness": sim.get("square").meters["lateness"],
        "suspicion": sim.get("elder").memes["suspicion"],
    }


def dawn_setup(world: World, child: Entity, elder: Entity, bell_cfg: Bell) -> None:
    child.memes["duty"] += 1
    world.say(
        f"At the stroke of dawn, when the roofs were still silver with mist, "
        f"{child.id} climbed the steps of {bell_cfg.tower}. Above the village hung "
        f"{bell_cfg.shine}, and everyone waited for its morning song."
    )
    world.say(
        f"{elder.id}, the old keeper of the tower, stood below and called, "
        f'"Pull true, little one, and let the day begin."'
    )


def attempt_ring(world: World, child: Entity, cause: Cause, bell_cfg: Bell) -> None:
    bell = world.get("bell")
    bell.meters["jammed"] += 1
    bell.attrs["cause"] = cause.id
    bell.meters["strain"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} drew the rope with both hands. Yet instead of {bell_cfg.echo}, "
        f"there came only a dull shiver in the beam. {cause.trouble.capitalize()}."
    )


def first_blame(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f'"What have you done?" cried {elder.id}. '
        f'"This looks like your fault."'
    )
    world.say(
        f'{child.id} stepped back with hot cheeks. "I pulled as I always do," '
        f'{child.pronoun()} said. "If there is a fault, let us find it before we name it mine."'
    )


def helper_enters(world: World, helper: Entity) -> None:
    world.say(
        f"From the stair came {helper.id}, carrying a small lamp and an older patience. "
        f'"Tongues are quick," {helper.pronoun()} said, "but truth walks on careful feet."'
    )


def inspect(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    child.memes["resolve"] += 1
    helper.memes["care"] += 1
    world.facts["inspection_place"] = cause.repair_need
    world.say(
        f'Together they looked where the trouble would live: {cause.clue}. '
        f'"See here," said {helper.id}.'
    )
    world.say(
        f'"So it was not my hands after all?" asked {child.id}. '
        f'"No," said {helper.id}, "the true fault sleeps in the bell itself."'
    )
    world.facts["cause_found"] = True
    world.facts["true_cause_found"] = True
    propagate(world, narrate=False)


def repair(world: World, child: Entity, helper: Entity, cause: Cause, fix: Fix, bell_cfg: Bell) -> None:
    bell = world.get("bell")
    if repair_succeeds(cause, fix):
        bell.meters["jammed"] = 0.0
        bell.meters["ringing"] += 1
        child.memes["hope"] += 1
        helper.memes["pride"] += 1
        world.say(
            f'"Then hand me the {fix.tool}," said {helper.id}. '
            f'Together they {fix.success_text}.'
        )
        world.say(
            f"Once more {child.id} took the rope. This time the bell answered with "
            f"{bell_cfg.echo}, and the sound ran over the roofs like bread smell on a cold morning."
        )
    else:
        bell.meters["ringing"] = 0.0
        bell.meters["jammed"] += 1
        child.memes["worry"] += 1
        world.say(
            f'"Try the {fix.tool}," said {helper.id}, though the guess was poor. '
            f'Together they {fix.fail_text}.'
        )
        world.say(
            f"But when {child.id} pulled again, the bell only trembled in silence, "
            f"and the tower seemed lonelier than before."
        )


def apology_and_twist(world: World, child: Entity, elder: Entity, cause: Cause) -> None:
    elder.memes["kindness"] += 1
    world.say(
        f'{elder.id} bowed {elder.pronoun("possessive")} head. '
        f'"Child, the fault was not yours," {elder.pronoun()} said. '
        f'"My tongue ran ahead of my wisdom."'
    )
    world.say(
        f'{cause.twist_line} The old keeper had watched the child\'s hands, '
        f"when the mischief had been hidden higher up all along."
    )


def ending(world: World, child: Entity, helper: Entity, elder: Entity, bell_cfg: Bell) -> None:
    child.memes["joy"] += 1
    child.memes["hurt"] = 0.0
    world.say(
        f'That morning the villagers said the bell had never sounded so clear. '
        f'{elder.id} let {child.id} stand beside the rope with an untroubled smile, '
        f'and {helper.id} said, "A careful heart mends more than bronze."'
    )
    world.say(
        f"From then on, whenever dawn came to {bell_cfg.tower}, the keeper listened first, "
        f"asked second, and blamed last."
    )


def ending_sad(world: World, child: Entity, helper: Entity, elder: Entity, bell_cfg: Bell) -> None:
    world.say(
        f"When the sun rose full above {bell_cfg.tower}, the village still had no bell-song. "
        f"{elder.id} sighed, and even the pigeons on the beams sat quiet."
    )
    world.say(
        f'{helper.id} put a hand on {child.id}\'s shoulder. '
        f'"The fault is not yours," {helper.pronoun()} said, '
        f'"but we must fetch a wiser craftsperson before another stroke of dawn."'
    )


def tell(
    bell_cfg: Bell,
    cause: Cause,
    fix: Fix,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_name: str = "Old Bran",
    elder_type: str = "man",
    helper_name: str = "Nanna Reed",
    helper_type: str = "grandmother",
    village: str = "Hazel Hollow",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    bell = world.add(Entity(id="bell", kind="thing", type="bell", label="the morning bell"))
    square = world.add(Entity(id="square", kind="thing", type="square", label="the village square"))

    world.facts.update(
        bell_cfg=bell_cfg,
        cause_cfg=cause,
        fix_cfg=fix,
        village=village,
        cause_found=False,
        true_cause_found=False,
        solved=False,
        outcome="",
    )

    dawn_setup(world, child, elder, bell_cfg)

    world.para()
    attempt_ring(world, child, cause, bell_cfg)
    first_blame(world, child, elder)

    world.para()
    helper_enters(world, helper)
    inspect(world, child, helper, cause)
    repair(world, child, helper, cause, fix, bell_cfg)

    world.para()
    if repair_succeeds(cause, fix):
        world.facts["solved"] = True
        world.facts["outcome"] = "cleared"
        propagate(world, narrate=False)
        apology_and_twist(world, child, elder, cause)
        ending(world, child, helper, elder, bell_cfg)
    else:
        world.facts["solved"] = False
        world.facts["outcome"] = "unsolved"
        apology_and_twist(world, child, elder, cause)
        ending_sad(world, child, helper, elder, bell_cfg)

    world.facts.update(
        child=child,
        elder=elder,
        helper=helper,
        bell=bell,
    )
    return world


BELLS = {
    "bronze_bell": Bell(
        id="bronze_bell",
        tower="the bell tower of Hazel Hollow",
        shine="a bronze bell as round as a harvest moon",
        echo="a bright bronze voice",
        tags={"bell", "dawn"},
    ),
    "river_bell": Bell(
        id="river_bell",
        tower="the river tower above Willow Ford",
        shine="a green-brown bell with river-light on its lip",
        echo="a deep note that rolled like water over stones",
        tags={"bell", "dawn"},
    ),
    "oak_bell": Bell(
        id="oak_bell",
        tower="the oak tower at Fern Gate",
        shine="an old bell darkened by years of smoke and rain",
        echo="a warm note that seemed to wake even the crows kindly",
        tags={"bell", "dawn"},
    ),
}

CAUSES = {
    "frayed_rope": Cause(
        id="frayed_rope",
        clue="where the rope rubbed against the beam",
        trouble="the rope had worn thin and caught in its own loose hairs",
        true_fault="a frayed rope",
        severity=1,
        repair_need="the rope above the beam",
        repair_text="spliced the rope",
        twist_line="The rope had been gnawed and scraped over many mornings, not spoiled by the child's pull",
        tags={"rope", "repair"},
    ),
    "stuck_clapper": Cause(
        id="stuck_clapper",
        clue="inside the bell where the clapper should swing free",
        trouble="the clapper was held fast by a braid of ivy blown through a crack",
        true_fault="ivy tangled around the clapper",
        severity=1,
        repair_need="inside the bell mouth",
        repair_text="cut the ivy away",
        twist_line="In the night wind, ivy had crept where no sleepy eye had looked",
        tags={"ivy", "repair"},
    ),
    "swallow_nest": Cause(
        id="swallow_nest",
        clue="the wooden brace above the bell mouth",
        trouble="a swallow had tucked straw into the brace until the bell could scarcely swing",
        true_fault="a swallow nest wedged in the brace",
        severity=1,
        repair_need="the brace above the bell",
        repair_text="lifted the straw free and set the nest on the window ledge",
        twist_line="The bell had been hushed by a swallow's housekeeping, not by the child's hands",
        tags={"bird", "nest", "repair"},
    ),
}

FIXES = {
    "splice_rope": Fix(
        id="splice_rope",
        tool="twine and a knife",
        method="splice the rope with fresh twine",
        cures={"frayed_rope"},
        care=3,
        success_text="trimmed the loose fibers and spliced the rope with fresh twine",
        fail_text="trimmed a little at the rope and tied it prettier, but never reached the true trouble",
        qa_text="They spliced the worn rope with fresh twine",
        tags={"rope", "tool"},
    ),
    "clear_ivy": Fix(
        id="clear_ivy",
        tool="a hook knife",
        method="cut away the ivy around the clapper",
        cures={"stuck_clapper"},
        care=3,
        success_text="reached into the bell mouth and cut away the ivy that held the clapper fast",
        fail_text="scraped at a few leaves below, but the clapper stayed trapped",
        qa_text="They cut away the ivy that trapped the clapper",
        tags={"ivy", "tool"},
    ),
    "move_nest": Fix(
        id="move_nest",
        tool="a willow basket",
        method="lift the swallow nest away gently",
        cures={"swallow_nest"},
        care=3,
        success_text="lifted the swallow nest into a willow basket and set it safely on the ledge",
        fail_text="shifted some straw on the floor, but the brace above the bell stayed wedged tight",
        qa_text="They gently moved the swallow nest from the brace",
        tags={"bird", "nest"},
    ),
    "oil_hinge": Fix(
        id="oil_hinge",
        tool="a little oil flask",
        method="oil the hinge below the platform",
        cures=set(),
        care=2,
        success_text="oiled the lower hinge until it shone",
        fail_text="oiled the lower hinge until it shone, but the bell was still held silent by another fault",
        qa_text="They oiled the lower hinge",
        tags={"oil", "tool"},
    ),
    "hit_bell": Fix(
        id="hit_bell",
        tool="a heavy mallet",
        method="strike the bell hard",
        cures=set(),
        care=1,
        success_text="struck the bell hard",
        fail_text="struck the bell hard and frightened the swallows, yet solved nothing",
        qa_text="They struck the bell with a mallet",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Mira", "Tansy", "Elin", "Poppy", "Ruth", "Nella"]
BOY_NAMES = ["Tobin", "Hale", "Rowan", "Finn", "Perrin", "Jory"]
HELPERS = [
    {"name": "Nanna Reed", "type": "grandmother"},
    {"name": "Grandfather Moss", "type": "grandfather"},
    {"name": "Aunt Willow", "type": "woman"},
]
ELDERS = [
    {"name": "Old Bran", "type": "man"},
    {"name": "Keeper Holt", "type": "man"},
    {"name": "Dame Ash", "type": "woman"},
]
VILLAGES = ["Hazel Hollow", "Willow Ford", "Fern Gate", "Moss End"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for bell_id in BELLS:
        for cause_id, cause in CAUSES.items():
            for fix_id, fix in FIXES.items():
                if repair_succeeds(cause, fix):
                    combos.append((bell_id, cause_id, fix_id))
    return combos


@dataclass
class StoryParams:
    bell: str
    cause: str
    fix: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_type: str
    helper_name: str
    helper_type: str
    village: str
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
    "bell": [
        (
            "What does a bell do in a village?",
            "A village bell tells people something important, like the start of the day or a call to gather. Its sound travels far, so many ears can hear it at once.",
        )
    ],
    "dawn": [
        (
            "What is dawn?",
            "Dawn is the early time when night is ending and morning begins. The sky grows lighter before the sun is fully up.",
        )
    ],
    "rope": [
        (
            "What happens when a rope gets frayed?",
            "A frayed rope has worn, broken fibers and becomes weak or tangly. It may catch, snap, or stop working smoothly.",
        )
    ],
    "ivy": [
        (
            "What is ivy?",
            "Ivy is a climbing plant that can creep over walls and beams. If nobody trims it, it can wind into places where it should not be.",
        )
    ],
    "bird": [
        (
            "Why do birds build nests?",
            "Birds build nests to keep their eggs and chicks safe. They gather straw, grass, and twigs to make a small home.",
        )
    ],
    "nest": [
        (
            "Why should people move a bird nest gently?",
            "A bird nest should be moved gently so the eggs or chicks are not harmed. Kind problem solving tries to help people without being cruel to animals.",
        )
    ],
    "repair": [
        (
            "What is a repair?",
            "A repair is when you fix something that is broken or stuck so it can work again. Good repairs match the real problem, not just a guess.",
        )
    ],
    "tool": [
        (
            "Why do people use the right tool for a job?",
            "The right tool helps you work safely and carefully. A wrong tool can waste time or make a problem worse.",
        )
    ],
    "rough": [
        (
            "Why is hitting a broken thing not always wise?",
            "Hitting something hard may damage it or scare others without fixing the real trouble. Careful looking usually comes before rough force.",
        )
    ],
    "oil": [
        (
            "What does oil help with?",
            "Oil can help parts move smoothly when they are rubbing or squeaking. But it only helps if rubbing is the real problem.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bell", "dawn", "rope", "ivy", "bird", "nest", "repair", "tool", "oil", "rough"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    helper = f["helper"]
    cause = f["cause_cfg"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the words "fault" and "stroke".',
        f"Tell a village bell story where {child.id} is blamed too quickly, {helper.id} helps investigate, and the true fault turns out to be {cause.true_fault}.",
        f"Write a dialogue-rich folk tale in which {elder.id} speaks in haste, then learns to look for the real cause before blaming anyone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    helper = f["helper"]
    bell_cfg = f["bell_cfg"]
    cause = f["cause_cfg"]
    fix = f["fix_cfg"]
    solved = f["solved"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, the young bell-puller, {elder.id}, the old keeper, and {helper.id}, who helps find the truth. They all meet in {bell_cfg.tower} when the morning bell fails.",
        ),
        (
            "What problem began the story?",
            f"The bell would not ring at the stroke of dawn. Because the village was waiting for its morning sound, the silence made everyone worry at once.",
        ),
        (
            f"Why did {elder.id} think it was {child.id}'s fault?",
            f"{elder.id} saw {child.id} at the rope when the bell failed and spoke too quickly. The keeper noticed the child first, but the real trouble was hidden in the bell.",
        ),
        (
            f"How did {child.id} and {helper.id} solve the problem?",
            f"They did not argue about blame; they looked for clues where the bell was stuck. Then they found {cause.true_fault} and tried a repair that matched it.",
        ),
    ]
    if solved:
        qa.append(
            (
                "What was the twist in the story?",
                f"The twist was that the child who seemed guilty had done nothing wrong. The true fault was {cause.true_fault}, hidden above or inside the bell where nobody had looked at first.",
            )
        )
        qa.append(
            (
                f"How was the bell fixed?",
                f"{fix.qa_text}. Because the repair matched the hidden trouble, the bell could swing and sing again.",
            )
        )
        qa.append(
            (
                f"What did {elder.id} learn?",
                f"{elder.id} learned not to blame somebody before searching for the truth. The ending shows this because the keeper listens first and blames last from then on.",
            )
        )
    else:
        qa.append(
            (
                "Did they solve the problem that morning?",
                f"No. They found the true fault, but their first repair did not match it well enough. The story ends with a plan to fetch a wiser craftsperson before another stroke of dawn.",
            )
        )
        qa.append(
            (
                f"Was it really {child.id}'s fault?",
                f"No, it was not {child.id}'s fault at all. Even before the bell was fully fixed, the hidden cause proved the child had been blamed unfairly.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["bell_cfg"].tags) | set(world.facts["cause_cfg"].tags) | set(world.facts["fix_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:14} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  world facts: outcome={world.facts.get('outcome')} solved={world.facts.get('solved')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        bell="bronze_bell",
        cause="frayed_rope",
        fix="splice_rope",
        child_name="Mira",
        child_gender="girl",
        elder_name="Old Bran",
        elder_type="man",
        helper_name="Nanna Reed",
        helper_type="grandmother",
        village="Hazel Hollow",
    ),
    StoryParams(
        bell="river_bell",
        cause="stuck_clapper",
        fix="clear_ivy",
        child_name="Tobin",
        child_gender="boy",
        elder_name="Keeper Holt",
        elder_type="man",
        helper_name="Aunt Willow",
        helper_type="woman",
        village="Willow Ford",
    ),
    StoryParams(
        bell="oak_bell",
        cause="swallow_nest",
        fix="move_nest",
        child_name="Elin",
        child_gender="girl",
        elder_name="Dame Ash",
        elder_type="woman",
        helper_name="Grandfather Moss",
        helper_type="grandfather",
        village="Fern Gate",
    ),
]


ASP_RULES = r"""
valid_fix(Fx, C) :- fix(Fx), cause(C), cures(Fx, C).
sensible(Fx) :- fix(Fx), care(Fx, N), care_min(M), N >= M.
valid(B, C, Fx) :- bell(B), cause(C), fix(Fx), valid_fix(Fx, C), sensible(Fx).

solved :- chosen_cause(C), chosen_fix(Fx), valid_fix(Fx, C), sensible(Fx).
outcome(cleared) :- solved.
outcome(unsolved) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for bell_id in BELLS:
        lines.append(asp.fact("bell", bell_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("care", fix_id, fix.care))
        for cure in sorted(fix.cures):
            lines.append(asp.fact("cures", fix_id, cure))
    lines.append(asp.fact("care_min", CARE_MIN))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    cause = CAUSES[params.cause]
    fix = FIXES[params.fix]
    return "cleared" if repair_succeeds(cause, fix) else "unsolved"


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

    c_sensible = set(asp_sensible())
    p_sensible = {fx.id for fx in sensible_fixes()}
    if c_sensible == p_sensible:
        print(f"OK: sensible fixes match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    cases = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolution failed for seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a dawn bell, a quick blame, a careful search, and a folk-tale twist."
    )
    ap.add_argument("--bell", choices=BELLS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--village")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].care < CARE_MIN:
        raise StoryError(explain_fix_care(FIXES[args.fix]))
    if args.cause and args.fix:
        cause = CAUSES[args.cause]
        fix = FIXES[args.fix]
        if not valid_fix_for(cause, fix):
            raise StoryError(explain_cause_mismatch(cause, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.bell is None or combo[0] == args.bell)
        and (args.cause is None or combo[1] == args.cause)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    bell_id, cause_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name
    if not child_name:
        child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_def = rng.choice(ELDERS)
    helper_def = rng.choice(HELPERS)
    village = args.village or rng.choice(VILLAGES)

    return StoryParams(
        bell=bell_id,
        cause=cause_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=gender,
        elder_name=elder_def["name"],
        elder_type=elder_def["type"],
        helper_name=helper_def["name"],
        helper_type=helper_def["type"],
        village=village,
    )


def generate(params: StoryParams) -> StorySample:
    if params.bell not in BELLS:
        raise StoryError(f"(Unknown bell: {params.bell})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    cause = CAUSES[params.cause]
    fix = FIXES[params.fix]
    if fix.care < CARE_MIN:
        raise StoryError(explain_fix_care(fix))
    if not valid_fix_for(cause, fix):
        raise StoryError(explain_cause_mismatch(cause, fix))

    world = tell(
        bell_cfg=BELLS[params.bell],
        cause=cause,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        village=params.village,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (bell, cause, fix) combos:\n")
        for bell_id, cause_id, fix_id in combos:
            print(f"  {bell_id:12} {cause_id:14} {fix_id}")
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
            header = f"### {p.child_name}: {p.cause} with {p.fix} at {p.bell}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
