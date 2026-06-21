#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/saw_horned_banjo_mystery_to_solve_problem.py
=======================================================================

A standalone story world for a small child-facing mystery: a strange scraping
sound, a horned shadow, and a missing banjo part lead two children into a
gentle "what is really happening?" puzzle. The story is driven by simulated
state: clues create worry and curiosity, the children test a sensible plan, and
the ending image proves the mystery has been solved.

Core shape
----------
A child is getting ready for music time when a banjo goes wrong in some puzzling
way. From behind a door or curtain comes a scratchy sound that almost sounds
like a saw. A long shadow looks horned. The children first imagine something
scary, then slow down, gather clues, and solve the real problem.

Reasonableness constraint
-------------------------
Not every hidden cause can be fixed by every plan. This world only generates
stories where the chosen solve method actually matches the cause:

* a goat with festival horns can be led out with an apple or feed scoop
* a calf with a paper-horn costume can be coaxed with a grain bucket
* a drafty window blowing a horned hat onto a chair can be fixed by tying the
  window and moving the hat

The Python gate and inline ASP twin both enforce those compatible combinations.

Run it
------
    python storyworlds/worlds/gpt-5.4/saw_horned_banjo_mystery_to_solve_problem.py
    python storyworlds/worlds/gpt-5.4/saw_horned_banjo_mystery_to_solve_problem.py --place barn_loft
    python storyworlds/worlds/gpt-5.4/saw_horned_banjo_mystery_to_solve_problem.py --cause wind_hat
    python storyworlds/worlds/gpt-5.4/saw_horned_banjo_mystery_to_solve_problem.py --solve grain_bucket
    python storyworlds/worlds/gpt-5.4/saw_horned_banjo_mystery_to_solve_problem.py --all
    python storyworlds/worlds/gpt-5.4/saw_horned_banjo_mystery_to_solve_problem.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/saw_horned_banjo_mystery_to_solve_problem.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"           # character | thing | animal
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = True
    animal: bool = False
    horned: bool = False
    instrument: bool = False
    # two numeric dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
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
class Place:
    id: str
    label: str
    intro: str
    hiding_spot: str
    workshop_line: str
    clue_shadow: str
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
    culprit_type: str
    culprit_label: str
    culprit_phrase: str
    horn_text: str
    sound_text: str
    reveal_text: str
    snag_text: str
    fix_need: str
    living: bool = True
    horned: bool = True
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
class SolveMethod:
    id: str
    label: str
    action_text: str
    success_text: str
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
class BanjoProblem:
    id: str
    intro: str
    stuck_text: str
    ending_text: str
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


PLACES = {
    "barn_loft": Place(
        id="barn_loft",
        label="the barn loft",
        intro="The barn loft smelled like hay and old wood, and sunbeams made bright ladders in the dust.",
        hiding_spot="behind the feed-room door",
        workshop_line="Beside the wall stood a workbench with a little hand saw hanging safely on a peg.",
        clue_shadow="Across the floor stretched a long shadow that looked oddly horned.",
        tags={"barn", "music"},
    ),
    "fair_shed": Place(
        id="fair_shed",
        label="the fair shed",
        intro="The fair shed was full of ribbon boxes, stools, and music cases waiting for the afternoon show.",
        hiding_spot="behind the striped curtain by the tool shelf",
        workshop_line="Near the back shelf hung a small hand saw used for fixing loose boards.",
        clue_shadow="On the canvas wall wobbled a horned shadow with two sharp-looking points.",
        tags={"fair", "music"},
    ),
    "porch_room": Place(
        id="porch_room",
        label="the porch room",
        intro="The porch room held boots, coats, and a corner where instruments rested between songs.",
        hiding_spot="behind the half-open storage door",
        workshop_line="A tiny hand saw lay up high on a hook above the repair basket.",
        clue_shadow="The afternoon light made a bent, horned shadow reach across the rug.",
        tags={"house", "music"},
    ),
}

CAUSES = {
    "goat": Cause(
        id="goat",
        culprit_type="goat",
        culprit_label="goat",
        culprit_phrase="a small goat wearing soft parade horns made of felt",
        horn_text="The shadow looked horned because the little goat still had its felt festival horns tied on.",
        sound_text="Every time it shuffled, its tag tapped the banjo case and made a sharp, saw-saw scrape.",
        reveal_text="It was not a monster at all, only the farm goat with wide eyes and a tangled strap.",
        snag_text="One strap from the banjo case had looped around the peg by the door, and the goat had nosed it tighter.",
        fix_need="The goat needed to be coaxed to step back so the strap could come free.",
        living=True,
        horned=True,
        tags={"goat", "animal"},
    ),
    "calf": Cause(
        id="calf",
        culprit_type="calf",
        culprit_label="calf",
        culprit_phrase="a gentle calf wearing a paper costume with horned points",
        horn_text="The shadow looked horned because the calf's paper costume had two floppy points on top.",
        sound_text="When it bumped the wall, the loose banjo strings twanged and the chair leg rasped with a saw-like sound.",
        reveal_text="The mystery creature was only a curious calf that had wandered in after the morning parade practice.",
        snag_text="The calf had nudged the banjo stand sideways, so one string was caught under a chair rung.",
        fix_need="The calf needed to be lured away before anyone could straighten the stand.",
        living=True,
        horned=True,
        tags={"calf", "animal"},
    ),
    "wind_hat": Cause(
        id="wind_hat",
        culprit_type="draft",
        culprit_label="draft",
        culprit_phrase="a drafty window, a chair, and a hat with stitched horns",
        horn_text="The shadow looked horned because a dress-up hat with stitched horns had blown onto the chair back.",
        sound_text="The window kept flapping, and each puff made the banjo strings hum while the chair scraped with a saw-saw sound.",
        reveal_text="There was no animal there at all, only wind, a silly hat, and a banjo jiggling in the draft.",
        snag_text="The banjo strap had slid under the chair leg while the window rattled everything around it.",
        fix_need="The window had to be tied still before the hat and chair could be moved.",
        living=False,
        horned=False,
        tags={"wind", "hat"},
    ),
}

SOLVES = {
    "apple_slice": SolveMethod(
        id="apple_slice",
        label="an apple slice",
        action_text="held out an apple slice and spoke in a slow, soft voice",
        success_text="The goat followed the apple one careful step at a time, and the strap loosened enough to lift free.",
        qa_text="used an apple slice to coax the goat away from the tangled strap",
        tags={"food", "animal_help"},
    ),
    "grain_bucket": SolveMethod(
        id="grain_bucket",
        label="a grain bucket",
        action_text="shook a little grain bucket so the kind clatter drifted through the room",
        success_text="The calf blinked, followed the bucket toward the open gate, and left space for the stand to be set right again.",
        qa_text="shook a grain bucket to guide the calf away so they could fix the banjo stand",
        tags={"bucket", "animal_help"},
    ),
    "tie_window": SolveMethod(
        id="tie_window",
        label="a piece of string",
        action_text="used a piece of string to tie the window hook tight before touching anything else",
        success_text="Once the window stopped flapping, the humming ceased, the chair stayed still, and the banjo strap slipped out easily.",
        qa_text="tied the window still first, then moved the hat and chair so the banjo strap came loose",
        tags={"window", "string"},
    ),
}

PROBLEMS = {
    "missing_pick": BanjoProblem(
        id="missing_pick",
        intro="When it was time to practice, the little felt pick tied to the banjo strap was missing.",
        stuck_text="Without the pick, the banjo could not sing its bright plinky song.",
        ending_text="Soon the banjo was chiming again, and the missing pick dangled right where it belonged.",
        tags={"pick", "banjo"},
    ),
    "stuck_string": BanjoProblem(
        id="stuck_string",
        intro="Just before music time, one banjo string gave a sour buzz instead of a happy twang.",
        stuck_text="Something was pulling the string wrong, so the banjo sounded grumpy.",
        ending_text="After the fix, the banjo gave a round, happy twang that filled the room.",
        tags={"string", "banjo"},
    ),
    "crooked_case": BanjoProblem(
        id="crooked_case",
        intro="The old banjo case would not open, though the latch had always been easy before.",
        stuck_text="Until the case came free, the children could not get the banjo ready for the song.",
        ending_text="At last the case opened, and the banjo came out safe and shining.",
        tags={"case", "banjo"},
    ),
}

NAME_POOLS = {
    "girl": ["Lila", "Mina", "Ruth", "Nora", "Pia", "June", "Tessa", "Ivy"],
    "boy": ["Owen", "Milo", "Ben", "Theo", "Eli", "Ned", "Sam", "Finn"],
}
TRAITS = ["careful", "curious", "steady", "observant", "thoughtful"]
HELPERS = ["mother", "father", "aunt", "uncle"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_shadow_fear(world: World) -> list[str]:
    mystery = world.get("mystery")
    if mystery.meters["shadow_seen"] < THRESHOLD:
        return []
    sig = ("shadow_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["worry"] += 1
    helper.memes["alert"] += 1
    return []


def _r_sound_curiosity(world: World) -> list[str]:
    mystery = world.get("mystery")
    if mystery.meters["strange_sound"] < THRESHOLD:
        return []
    sig = ("sound_curiosity",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    hero.memes["curiosity"] += 1
    return []


def _r_clues_to_plan(world: World) -> list[str]:
    mystery = world.get("mystery")
    if mystery.meters["clues_checked"] < THRESHOLD:
        return []
    sig = ("plan",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["brave"] += 1
    helper.memes["calm"] += 1
    world.facts["plan_ready"] = True
    return []


def _r_solve_problem(world: World) -> list[str]:
    mystery = world.get("mystery")
    banjo = world.get("banjo")
    culprit = world.get("culprit")
    if mystery.meters["solve_attempted"] < THRESHOLD:
        return []
    if culprit.meters["calmed"] < THRESHOLD and culprit.type != "draft":
        return []
    if culprit.type == "draft" and culprit.meters["stilled"] < THRESHOLD:
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mystery.meters["solved"] += 1
    banjo.meters["ready"] += 1
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    helper.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="shadow_fear", tag="emotional", apply=_r_shadow_fear),
    Rule(name="sound_curiosity", tag="emotional", apply=_r_sound_curiosity),
    Rule(name="clues_to_plan", tag="cognitive", apply=_r_clues_to_plan),
    Rule(name="solve_problem", tag="physical", apply=_r_solve_problem),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


# ---------------------------------------------------------------------------
# Constraints / reasoning
# ---------------------------------------------------------------------------
def compatible(cause: Cause, solve: SolveMethod) -> bool:
    if cause.id == "goat":
        return solve.id == "apple_slice"
    if cause.id == "calf":
        return solve.id == "grain_bucket"
    if cause.id == "wind_hat":
        return solve.id == "tie_window"
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for cause_id, cause in CAUSES.items():
            for solve_id, solve in SOLVES.items():
                if not compatible(cause, solve):
                    continue
                for problem_id in PROBLEMS:
                    combos.append((place_id, cause_id, solve_id, problem_id))
    return combos


def explain_rejection(cause: Cause, solve: SolveMethod) -> str:
    return (
        f"(No story: {solve.label} does not fit the real cause here. "
        f"The cause is {cause.culprit_phrase}, so the solve must match that problem: {cause.fix_need})"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_reality(world: World, cause: Cause) -> dict:
    sim = world.copy()
    culprit = sim.get("culprit")
    mystery = sim.get("mystery")
    if cause.living:
        culprit.meters["present"] += 1
        culprit.meters["snagging"] += 1
    else:
        culprit.meters["drafting"] += 1
        culprit.meters["snagging"] += 1
    mystery.meters["shadow_seen"] += 1
    mystery.meters["strange_sound"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("hero").memes["worry"],
        "curiosity": sim.get("hero").memes["curiosity"],
        "snagging": culprit.meters["snagging"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, problem: BanjoProblem) -> None:
    trait = hero.traits[0] if hero.traits else "curious"
    world.say(
        f"{hero.id} was a {trait} {hero.type} who loved listening for small sounds that other people missed."
    )
    world.say(
        f"That morning, {hero.id} and {helper.label_word} were getting ready for music time. {problem.intro}"
    )


def set_scene(world: World, problem: BanjoProblem) -> None:
    world.say(world.place.intro)
    world.say(world.place.workshop_line)
    world.say(problem.stuck_text)


def first_clue(world: World, hero: Entity, cause: Cause) -> None:
    mystery = world.get("mystery")
    mystery.meters["strange_sound"] += 1
    mystery.meters["shadow_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, from {world.place.hiding_spot}, {hero.id} heard a scratchy noise that sounded almost like a saw whispering against wood."
    )
    world.say(world.place.clue_shadow)
    world.say(
        f'{hero.id} stopped still. "Did you hear that?" {hero.pronoun()} whispered.'
    )
    world.facts["heard_saw_sound"] = True
    world.facts["horned_shadow"] = True
    world.facts["cause_sound_text"] = cause.sound_text
    world.facts["cause_horn_text"] = cause.horn_text


def worry_and_decide(world: World, hero: Entity, helper: Entity, cause: Cause) -> None:
    pred = predict_reality(world, cause)
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["predicted_curiosity"] = pred["curiosity"]
    extra = " but it also made the mystery feel worth solving" if pred["curiosity"] >= THRESHOLD else ""
    world.say(
        f'{helper.label_word.capitalize()} listened too and did not laugh. "{world.place.hiding_spot.capitalize()} sounds busy," {helper.pronoun()} said softly.'
    )
    world.say(
        f"{hero.id}'s heart gave one quick jump,{extra}. Instead of rushing in, {hero.pronoun()} took a slow breath and looked for clues first."
    )


def inspect_clues(world: World, hero: Entity, cause: Cause, problem: BanjoProblem) -> None:
    mystery = world.get("mystery")
    mystery.meters["clues_checked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} noticed two true things at once: the strange sound came in little bumps, and the banjo trouble was coming from the same corner."
    )
    world.say(
        f"{cause.sound_text} {cause.horn_text}"
    )
    if problem.id == "missing_pick":
        world.say(
            f"That meant the missing pick was probably still near the banjo strap, not stolen away at all."
        )
    elif problem.id == "stuck_string":
        world.say(
            f"That meant something nearby was tugging the string, not magic and not a monster."
        )
    else:
        world.say(
            f"That meant the crooked case was being pulled from outside, not stuck for no reason."
        )


def choose_plan(world: World, hero: Entity, helper: Entity, cause: Cause, solve: SolveMethod) -> None:
    world.say(
        f'"Let\'s solve the real problem, not the pretend scary one," said {helper.label_word}.'
    )
    world.say(
        f'{hero.id} nodded. Because {cause.fix_need} {hero.pronoun()} and {helper.label_word} made a careful plan: {helper.pronoun()} {solve.action_text}.'
    )
    world.facts["plan_text"] = solve.action_text


def reveal(world: World, hero: Entity, helper: Entity, cause: Cause) -> None:
    culprit = world.get("culprit")
    if cause.living:
        culprit.meters["present"] += 1
    else:
        culprit.meters["drafting"] += 1
    culprit.meters["snagging"] += 1
    world.say(
        f"When {helper.label_word} eased the door wider, the mystery showed its true face. {cause.reveal_text}"
    )
    world.say(cause.snag_text)


def do_solve(world: World, cause: Cause, solve: SolveMethod) -> None:
    culprit = world.get("culprit")
    mystery = world.get("mystery")
    mystery.meters["solve_attempted"] += 1
    if cause.id == "goat":
        culprit.meters["calmed"] += 1
    elif cause.id == "calf":
        culprit.meters["calmed"] += 1
    elif cause.id == "wind_hat":
        culprit.meters["stilled"] += 1
    propagate(world, narrate=False)
    world.say(solve.success_text)


def ending(world: World, hero: Entity, helper: Entity, problem: BanjoProblem, solve: SolveMethod) -> None:
    world.say(
        f"{problem.ending_text} {hero.id} grinned so hard {hero.pronoun('possessive')} cheeks felt round."
    )
    world.say(
        f'"So the horned mystery was really a clue puzzle," {hero.id} said.'
    )
    world.say(
        f'{helper.label_word.capitalize()} smiled. "Yes. You saw the clues, stayed calm, and solved it."'
    )
    world.say(
        f"A moment later the banjo rang out, bright and friendly, and the once-strange corner felt ordinary again."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    cause: Cause,
    solve: SolveMethod,
    problem: BanjoProblem,
    hero_name: str = "Lila",
    hero_gender: str = "girl",
    helper_type: str = "aunt",
    trait: str = "careful",
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
        attrs={},
    ))
    banjo = world.add(Entity(
        id="banjo",
        kind="thing",
        type="banjo",
        label="banjo",
        instrument=True,
        movable=True,
        attrs={"problem": problem.id},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="animal" if cause.living else "thing",
        type=cause.culprit_type,
        label=cause.culprit_label,
        role="culprit",
        animal=cause.living,
        horned=cause.horned,
        attrs={},
    ))
    mystery = world.add(Entity(
        id="mystery",
        kind="thing",
        type="mystery",
        label="mystery",
        movable=False,
        attrs={},
    ))
    # initialize read-before-write facts
    world.facts["plan_ready"] = False
    world.facts["heard_saw_sound"] = False
    world.facts["horned_shadow"] = False

    introduce(world, hero, helper, problem)
    set_scene(world, problem)

    world.para()
    first_clue(world, hero, cause)
    worry_and_decide(world, hero, helper, cause)

    world.para()
    inspect_clues(world, hero, cause, problem)
    choose_plan(world, hero, helper, cause, solve)
    reveal(world, hero, helper, cause)
    do_solve(world, cause, solve)

    world.para()
    ending(world, hero, helper, problem, solve)

    world.facts.update(
        hero=hero,
        helper=helper,
        banjo=banjo,
        culprit=culprit,
        cause=cause,
        solve=solve,
        place=place,
        problem=problem,
        solved=world.get("mystery").meters["solved"] >= THRESHOLD,
        banjo_ready=banjo.meters["ready"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    cause: str
    solve: str
    problem: str
    hero_name: str
    hero_gender: str
    helper_type: str
    trait: str
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
    "banjo": [
        ("What is a banjo?",
         "A banjo is a string instrument with a round body and a bright, twangy sound. People pluck or strum its strings to make music.")
    ],
    "saw": [
        ("What is a saw?",
         "A saw is a tool for cutting wood. Children should not play with one, and in this story the sound only reminded them of a saw.")
    ],
    "goat": [
        ("Why might a goat make scratchy sounds near a case or door?",
         "A goat can bump, tug, or shuffle things when it is curious. Those little movements can make straps, tags, or wood scrape and rattle.")
    ],
    "calf": [
        ("What is a calf?",
         "A calf is a young cow. Calves are often curious and may nudge things with their noses when they explore.")
    ],
    "wind": [
        ("How can wind make a room sound strange?",
         "Wind can flap a window, move light objects, and make strings hum. When several little sounds happen together, they can seem mysterious at first.")
    ],
    "clues": [
        ("What is a clue?",
         "A clue is a small piece of information that helps you figure something out. Good problem solving means noticing clues before guessing too fast.")
    ],
    "calm": [
        ("Why is staying calm useful in a mystery?",
         "Staying calm helps you look carefully and think clearly. When you slow down, the real answer is easier to see.")
    ],
}
KNOWLEDGE_ORDER = ["banjo", "saw", "goat", "calf", "wind", "clues", "calm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    problem = f["problem"]
    cause = f["cause"]
    return [
        'Write a gentle mystery story for a 3-to-5-year-old that includes the words "saw", "horned", and "banjo".',
        f"Tell a short problem-solving mystery where {hero.label} hears a strange saw-like sound near a banjo in {place.label}, sees a horned shadow, and solves the real cause with {helper.label_word}.",
        f"Write a child-facing mystery in which a scary-looking clue turns out to have an ordinary answer. Use a banjo problem ({problem.id}) and make the true cause be {cause.culprit_phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    problem = f["problem"]
    cause = f["cause"]
    solve = f["solve"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a careful child, and {helper.label_word}, who were getting a banjo ready for music time. They worked together to solve a mystery in {place.label}."
        ),
        (
            "What made the mystery seem scary at first?",
            f"{hero.label} heard a scratchy sound that almost sounded like a saw and also saw a horned shadow. Those two clues made the corner feel spooky before they knew what was really there."
        ),
        (
            "Why did they stop to look for clues instead of rushing in?",
            f"They wanted to solve the real problem safely. Slowing down helped them notice where the sound came from and how it connected to the banjo trouble."
        ),
        (
            "What was the real answer to the mystery?",
            f"{cause.reveal_text} The horned shape and the strange sound had an ordinary cause once they looked closely."
        ),
        (
            "How did they solve the problem?",
            f"{helper.label_word.capitalize()} {solve.qa_text}. That worked because {cause.fix_need.lower()}"
        ),
        (
            "How did the ending show that the problem was solved?",
            f"{problem.ending_text} The happy banjo sound at the end proved the mystery was finished and the room felt safe again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"banjo", "saw", "clues", "calm"}
    cause = world.facts["cause"]
    if cause.id == "goat":
        tags.add("goat")
    elif cause.id == "calf":
        tags.add("calf")
    elif cause.id == "wind_hat":
        tags.add("wind")
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
# Trace / emit
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.horned:
            parts.append("horned=True")
        if ent.instrument:
            parts.append("instrument=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
compatible(C,S) :- cause(C), solve(S), fits(C,S).

valid(P,C,S,Pr) :- place(P), cause(C), solve(S), problem(Pr), compatible(C,S).

#show valid/4.
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    for sid in SOLVES:
        lines.append(asp.fact("solve", sid))
    for prid in PROBLEMS:
        lines.append(asp.fact("problem", prid))
    lines.append(asp.fact("fits", "goat", "apple_slice"))
    lines.append(asp.fact("fits", "calf", "grain_bucket"))
    lines.append(asp.fact("fits", "wind_hat", "tie_window"))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    p_valid = set(valid_combos())
    a_valid = set(asp_valid_combos())
    if p_valid == a_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(p_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if p_valid - a_valid:
            print("  only in python:", sorted(p_valid - a_valid))
        if a_valid - p_valid:
            print("  only in ASP:", sorted(a_valid - p_valid))

    p_compat = {(c, s) for c in CAUSES for s in SOLVES if compatible(CAUSES[c], SOLVES[s])}
    a_compat = set(asp_compatible())
    if p_compat == a_compat:
        print(f"OK: compatibility facts match ({len(p_compat)} cause/solve pairs).")
    else:
        rc = 1
        print("MISMATCH in cause/solve compatibility.")
        if p_compat - a_compat:
            print("  only in python:", sorted(p_compat - a_compat))
        if a_compat - p_compat:
            print("  only in ASP:", sorted(a_compat - p_compat))

    # Smoke-test ordinary generation and emit.
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not sample.story or "banjo" not in sample.story.lower():
            raise StoryError("Smoke test story was empty or missing banjo.")
        print("OK: smoke test generate()/emit() ran successfully.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


# ---------------------------------------------------------------------------
# Parser / resolve / generate
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a gentle mystery with a saw-like sound, a horned shadow, and a banjo problem."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--solve", choices=SOLVES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAME_POOLS[gender])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.solve:
        cause = CAUSES[args.cause]
        solve = SOLVES[args.solve]
        if not compatible(cause, solve):
            raise StoryError(explain_rejection(cause, solve))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
        and (args.solve is None or combo[2] == args.solve)
        and (args.problem is None or combo[3] == args.problem)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cause_id, solve_id, problem_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_type = args.helper_type or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        cause=cause_id,
        solve=solve_id,
        problem=problem_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.solve not in SOLVES:
        raise StoryError(f"(Unknown solve method: {params.solve})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown banjo problem: {params.problem})")
    if params.hero_gender not in NAME_POOLS:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")

    cause = CAUSES[params.cause]
    solve = SOLVES[params.solve]
    if not compatible(cause, solve):
        raise StoryError(explain_rejection(cause, solve))

    world = tell(
        place=PLACES[params.place],
        cause=cause,
        solve=solve,
        problem=PROBLEMS[params.problem],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="barn_loft",
        cause="goat",
        solve="apple_slice",
        problem="stuck_string",
        hero_name="Lila",
        hero_gender="girl",
        helper_type="aunt",
        trait="careful",
    ),
    StoryParams(
        place="fair_shed",
        cause="calf",
        solve="grain_bucket",
        problem="crooked_case",
        hero_name="Owen",
        hero_gender="boy",
        helper_type="uncle",
        trait="observant",
    ),
    StoryParams(
        place="porch_room",
        cause="wind_hat",
        solve="tie_window",
        problem="missing_pick",
        hero_name="Mina",
        hero_gender="girl",
        helper_type="mother",
        trait="thoughtful",
    ),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, cause, solve, problem) combos:\n")
        for place_id, cause_id, solve_id, problem_id in combos:
            print(f"  {place_id:10} {cause_id:9} {solve_id:12} {problem_id}")
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
            header = f"### {p.hero_name}: {p.cause} in {p.place} ({p.problem})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
