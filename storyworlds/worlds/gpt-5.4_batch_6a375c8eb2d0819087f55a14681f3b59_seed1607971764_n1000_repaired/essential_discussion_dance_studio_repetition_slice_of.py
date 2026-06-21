#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/essential_discussion_dance_studio_repetition_slice_of.py
====================================================================================

A standalone story world for a small slice-of-life dance-studio tale.

Premise:
    A child in a dance studio is excited for a small class showing, but keeps
    stumbling over one essential part of a short routine. A calm discussion with
    a teacher or dance friend leads to the right kind of practice help, and
    repetition turns the hard part into something steady and joyful.

The world model is deliberately narrow and concrete:
- a studio setting
- one routine with one snag
- one helper
- one kind of support cue
- repeated practice rounds that change physical meters and emotional memes

The reasonableness gate only allows stories where the chosen support cue actually
fits the snag. The inline ASP twin mirrors that gate and the simple outcome
model.

Run it
------
    python storyworlds/worlds/gpt-5.4/essential_discussion_dance_studio_repetition_slice_of.py
    python storyworlds/worlds/gpt-5.4/essential_discussion_dance_studio_repetition_slice_of.py --routine waltz_turn --snag count --cue clap_count
    python storyworlds/worlds/gpt-5.4/essential_discussion_dance_studio_repetition_slice_of.py --cue water_break
    python storyworlds/worlds/gpt-5.4/essential_discussion_dance_studio_repetition_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/essential_discussion_dance_studio_repetition_slice_of.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/essential_discussion_dance_studio_repetition_slice_of.py --verify
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
PRACTICE_GOAL = 3


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
        female = {"girl", "woman", "teacher_female"}
        male = {"boy", "man", "teacher_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {"teacher_female": "teacher", "teacher_male": "teacher"}
        return mapping.get(self.type, self.type)
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
class Routine:
    id: str
    label: str
    phrase: str
    music: str
    essential_piece: str
    opening: str
    finish: str
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
class Snag:
    id: str
    label: str
    problem_line: str
    missing: str
    result_line: str
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
class Cue:
    id: str
    label: str
    helps: set[str]
    method_line: str
    repeat_line: str
    success_line: str
    knowledge_tag: str
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
    label: str
    role: str
    type: str
    discussion_line: str
    closing_line: str
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
class Studio:
    id: str
    label: str
    detail: str
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
        self.history: list[str] = []

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

    def note(self, item: str) -> None:
        self.history.append(item)

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
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


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    snag = world.facts["snag"]
    cue = world.facts.get("cue_cfg")
    if cue is None:
        return out
    if child.meters["practice_round"] < THRESHOLD:
        return out
    rounds = int(child.meters["practice_round"])
    for idx in range(1, rounds + 1):
        sig = ("progress", idx)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if snag.id in cue.helps:
            child.meters["accuracy"] += 1
            child.meters["stumble"] = max(0.0, child.meters["stumble"] - 1.0)
            child.memes["confidence"] += 1
            child.memes["frustration"] = max(0.0, child.memes["frustration"] - 0.5)
            out.append("__improve__")
        else:
            child.meters["stumble"] += 1
            child.memes["frustration"] += 1
            out.append("__stuck__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="progress", tag="practice", apply=_r_progress),
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


def cue_fits(snag: Snag, cue: Cue) -> bool:
    return snag.id in cue.helps


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for studio_id in STUDIOS:
        for routine_id in ROUTINES:
            for snag_id in SNAGS:
                for cue_id, cue in CUES.items():
                    if cue_fits(SNAGS[snag_id], cue):
                        combos.append((studio_id, routine_id, snag_id, cue_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    return "smooth" if params.rounds >= PRACTICE_GOAL else "almost"


def predict_success(world: World, rounds: int) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["practice_round"] += rounds
    propagate(sim, narrate=False)
    return {
        "accuracy": int(child.meters["accuracy"]),
        "smooth": child.meters["accuracy"] >= PRACTICE_GOAL,
    }


def introduce(world: World, studio: Studio, child: Entity, routine: Routine) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After school, {child.id} hurried into the {studio.label}. {studio.detail}"
    )
    world.say(
        f"Class was getting ready to practice {routine.phrase}, a little routine with {routine.music}."
    )
    world.say(
        f"{child.id} loved the way {routine.label} made the room feel bright and busy."
    )
    world.note("arrived at the studio")


def first_try(world: World, child: Entity, routine: Routine, snag: Snag) -> None:
    child.meters["stumble"] += 1
    child.memes["frustration"] += 1
    world.say(
        f"When the music began, {child.id} tried the {routine.opening}. Then {snag.problem_line}"
    )
    world.say(
        f"{snag.result_line} {child.id} knew that part was essential, and that made {child.pronoun('object')} sigh."
    )
    world.note("first try had a stumble")


def discussion(world: World, child: Entity, helper: Entity, helper_cfg: HelperCfg, snag: Snag, routine: Routine) -> None:
    child.memes["heard"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} noticed and came over for a quiet discussion by the mirror."
    )
    world.say(
        f'"{helper_cfg.discussion_line} You already know the {routine.finish}. It is the {snag.missing} that needs help," {helper.pronoun()} said.'
    )
    world.say(
        f'{child.id} nodded. "{routine.essential_piece} is the part I keep missing," {child.pronoun()} admitted.'
    )
    world.note("had a discussion about the hard part")


def choose_cue(world: World, helper: Entity, cue: Cue) -> None:
    world.facts["cue_cfg"] = cue
    world.say(
        f'"Let\'s try something simple," {helper.pronoun()} said. {cue.method_line}'
    )
    world.note(f"chose cue {cue.id}")


def practice_rounds(world: World, child: Entity, helper: Entity, cue: Cue, rounds: int) -> None:
    before = int(child.meters["practice_round"])
    for idx in range(1, rounds + 1):
        child.meters["practice_round"] += 1
        propagate(world, narrate=False)
        current = before + idx
        if current == 1:
            world.say(
                f"They tried it once. {cue.repeat_line}"
            )
        elif current == 2:
            world.say(
                f"They tried it again. {cue.repeat_line}"
            )
        else:
            world.say(
                f"They tried it again, and again. {cue.repeat_line}"
            )
        world.note(f"practice round {current}")
    if child.meters["accuracy"] >= PRACTICE_GOAL:
        world.say(
            f"Little by little, the hard part stopped feeling tangled. {cue.success_line}"
        )
        world.note("practice made the step smooth")
    else:
        world.say(
            f"The step was better than before, but {child.id} still had to think very hard about it."
        )
        world.note("practice helped a little but not enough")


def showing(world: World, child: Entity, helper: Entity, helper_cfg: HelperCfg, routine: Routine, snag: Snag) -> None:
    smooth = child.meters["accuracy"] >= PRACTICE_GOAL
    child.memes["relief"] += 1
    if smooth:
        child.memes["pride"] += 1
        world.say(
            f"When the class danced the whole piece, {child.id} found the {snag.missing} right on time."
        )
        world.say(
            f"The {routine.opening} flowed into the {routine.finish}, and {child.id} smiled at the mirror instead of frowning."
        )
        world.say(
            f'After the music ended, {helper.id} gave a small clap. "{helper_cfg.closing_line}"'
        )
        world.note("final run was smooth")
    else:
        world.say(
            f"When the class danced the whole piece, {child.id} still paused for one tiny breath at the hard spot, but did not give up."
        )
        world.say(
            f'{helper.id} smiled and said, "{helper_cfg.closing_line} Tomorrow it will feel even easier."'
        )
        world.note("final run was almost smooth")


def tell(
    studio: Studio,
    routine: Routine,
    snag: Snag,
    cue: Cue,
    helper_cfg: HelperCfg,
    *,
    child_name: str = "Lena",
    child_type: str = "girl",
    helper_name: str = "Ms. June",
    rounds: int = 3,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_cfg.type, role="helper"))
    world.add(Entity(id="studio", kind="thing", type="room", label=studio.label))
    world.facts["studio"] = studio
    world.facts["routine"] = routine
    world.facts["snag"] = snag
    world.facts["helper_cfg"] = helper_cfg
    world.facts["planned_rounds"] = rounds
    world.facts["cue_cfg"] = cue

    child.meters["accuracy"] = 0.0
    child.meters["stumble"] = 0.0
    child.meters["practice_round"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["frustration"] = 0.0
    child.memes["confidence"] = 0.0
    child.memes["heard"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["pride"] = 0.0
    helper.memes["care"] = 0.0

    introduce(world, studio, child, routine)
    world.para()
    first_try(world, child, routine, snag)
    world.para()
    discussion(world, child, helper, helper_cfg, snag, routine)
    choose_cue(world, helper, cue)
    practice_rounds(world, child, helper, cue, rounds)
    world.para()
    showing(world, child, helper, helper_cfg, routine, snag)

    world.facts.update(
        child=child,
        helper=helper,
        success=child.meters["accuracy"] >= PRACTICE_GOAL,
        outcome="smooth" if child.meters["accuracy"] >= PRACTICE_GOAL else "almost",
        practiced=int(child.meters["practice_round"]),
    )
    return world


STUDIOS = {
    "sunny": Studio(
        id="sunny",
        label="dance studio",
        detail="The wooden floor shone, the barres ran along one wall, and a soft piano track was already waiting in the speakers.",
        tags={"studio"},
    ),
    "corner": Studio(
        id="corner",
        label="dance studio",
        detail="Scarves hung in a basket, water bottles sat under the bench, and the mirror caught every small movement.",
        tags={"studio"},
    ),
}

ROUTINES = {
    "waltz_turn": Routine(
        id="waltz_turn",
        label="the waltz turn",
        phrase="a gentle waltz turn",
        music="slow counting and soft piano",
        essential_piece="the three-count turn",
        opening="step, sweep, and turn",
        finish="small curtsy at the end",
        tags={"count", "turn"},
    ),
    "ribbon_skip": Routine(
        id="ribbon_skip",
        label="the ribbon skip",
        phrase="a ribbon skip",
        music="bright bells and light drums",
        essential_piece="the ribbon path",
        opening="skip, lift, and circle",
        finish="ribbon held high at the end",
        tags={"space", "timing"},
    ),
    "jazz_line": Routine(
        id="jazz_line",
        label="the jazz line",
        phrase="a quick jazz line",
        music="snappy claps and a cheerful beat",
        essential_piece="the landing beat",
        opening="step-ball-change and reach",
        finish="hands on hips at the end",
        tags={"timing", "balance"},
    ),
}

SNAGS = {
    "count": Snag(
        id="count",
        label="counting the beat",
        problem_line="the counts slipped away from her, and the turn arrived too soon.",
        missing="count",
        result_line="One foot hurried and the other foot followed in a little scramble.",
        tags={"count"},
    ),
    "space": Snag(
        id="space",
        label="remembering where to go",
        problem_line="the ribbon loop wandered too close to the next dancer.",
        missing="path through the air",
        result_line="The pretty shape in the air became a lopsided wiggle.",
        tags={"space"},
    ),
    "balance": Snag(
        id="balance",
        label="holding steady at the landing",
        problem_line="the last step tipped forward, and the finish bobbled.",
        missing="steady landing",
        result_line="Her arms flew wide while she caught herself.",
        tags={"balance"},
    ),
    "timing": Snag(
        id="timing",
        label="entering at the right moment",
        problem_line="the move started a beat late, so the rest of the line had to wait for him.",
        missing="exact entrance beat",
        result_line="The class stayed kind, but the shape of the dance loosened.",
        tags={"timing"},
    ),
}

CUES = {
    "clap_count": Cue(
        id="clap_count",
        label="clapped counting",
        helps={"count", "timing"},
        method_line='The helper clapped softly and counted, "one-two-three, one-two-three."',
        repeat_line='The counting came back: "one-two-three, one-two-three."',
        success_line="Soon the counts felt like a friendly rail to hold onto.",
        knowledge_tag="counting",
        tags={"counting"},
    ),
    "tape_marks": Cue(
        id="tape_marks",
        label="floor tape marks",
        helps={"space"},
        method_line="The helper laid two small pieces of blue tape on the floor to show where the feet and ribbon should travel.",
        repeat_line="The blue marks gave the movement a clear path.",
        success_line="Soon the ribbon drew a neat, easy curve instead of wandering.",
        knowledge_tag="markers",
        tags={"markers"},
    ),
    "spot_and_breathe": Cue(
        id="spot_and_breathe",
        label="spot and breathe",
        helps={"balance"},
        method_line='The helper touched a finger to the mirror and said, "Look here, breathe, and land softly."',
        repeat_line="Each try ended with eyes up and a slower breath.",
        success_line="Soon the finish felt planted instead of wobbly.",
        knowledge_tag="balance",
        tags={"balance_help"},
    ),
    "water_break": Cue(
        id="water_break",
        label="a quick water break",
        helps=set(),
        method_line="The helper suggested a sip of water and a shoulder shake.",
        repeat_line="The pause felt nice, but it did not explain the hard part.",
        success_line="The child felt refreshed, though the missing step still needed a real practice tool.",
        knowledge_tag="breaks",
        tags={"breaks"},
    ),
}

HELPERS = {
    "teacher": HelperCfg(
        id="teacher",
        label="teacher",
        role="teacher",
        type="teacher_female",
        discussion_line="Let's slow it down and talk about what is happening.",
        closing_line="There it is. You found the essential part by practicing it patiently.",
        tags={"teacher"},
    ),
    "friend": HelperCfg(
        id="friend",
        label="friend",
        role="friend",
        type="girl",
        discussion_line="Want to say the tricky bit out loud with me first?",
        closing_line="You did it. Repetition really helped that part settle in.",
        tags={"friend"},
    ),
}

GIRL_NAMES = ["Lena", "Mia", "Zoe", "Ruby", "Nina", "Ella", "Tess", "Anna"]
BOY_NAMES = ["Evan", "Noah", "Milo", "Theo", "Ben", "Leo", "Finn", "Owen"]
HELPER_NAMES = {
    "teacher": ["Ms. June", "Ms. Rosa", "Ms. Helen"],
    "friend": ["Maya", "Ivy", "Sara"],
}


@dataclass
class StoryParams:
    studio: str
    routine: str
    snag: str
    cue: str
    helper: str
    child_name: str
    child_type: str
    helper_name: str
    rounds: int = 3
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
    "counting": [
        (
            "Why do dancers count?",
            "Counting helps dancers know when a move should begin and end. It gives the body a steady pattern to follow."
        )
    ],
    "markers": [
        (
            "Why do teachers use floor marks in dance?",
            "Floor marks show where feet or props should travel. They make space easier to remember."
        )
    ],
    "balance": [
        (
            "Why does looking at one spot help with balance?",
            "Looking at one spot gives your body a stable point to organize around. That can make turns and landings feel steadier."
        )
    ],
    "breaks": [
        (
            "Why can a short break help in class?",
            "A short break can help your body relax and breathe. But a break does not replace practicing the exact hard part."
        )
    ],
    "studio": [
        (
            "What do people practice in a dance studio?",
            "People practice steps, timing, and how to move safely with music. A studio gives them space, mirrors, and a smooth floor."
        )
    ],
}
KNOWLEDGE_ORDER = ["studio", "counting", "markers", "balance", "breaks"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    routine = f["routine"]
    snag = f["snag"]
    cue = f["cue_cfg"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old set in a dance studio. Include the words "essential" and "discussion".',
        f"Tell a gentle story where {child.id} keeps missing an essential part of {routine.label}, then a calm discussion with {helper.id} leads to {cue.label} and repeated practice.",
        f"Write a simple story about repetition helping with {snag.label} during dance class, ending with a small happy change the child can feel.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    routine = f["routine"]
    snag = f["snag"]
    cue = f["cue_cfg"]
    outcome = f["outcome"]
    practiced = f["practiced"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was practicing {routine.phrase} in a dance studio, and {helper.id}, who came to help. The story stays close to one small class moment."
        ),
        (
            f"What was hard for {child.id}?",
            f"The hard part was {snag.label}. {snag.result_line} shows how that trouble changed the dance in the middle."
        ),
        (
            f"What happened during the discussion?",
            f"{helper.id} stopped with {child.id} for a quiet discussion by the mirror. They named the exact essential part that was going wrong so the practice could match the real problem."
        ),
        (
            f"How did they practice?",
            f"They used {cue.label} and tried the move {practiced} times. The repetition mattered because the same small help came back again and again instead of changing every turn."
        ),
    ]
    if outcome == "smooth":
        qa.append(
            (
                f"How did {child.id} change by the end?",
                f"By the end, {child.id} found the hard part on time and danced more smoothly. Repetition built confidence because each round made the same essential piece easier to feel in {child.pronoun('possessive')} body."
            )
        )
    else:
        qa.append(
            (
                f"Did everything become perfect right away?",
                f"No. {child.id} was better, but still had to think hard at the tricky spot. The ending is gentle because progress happened first, and more practice can come later."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"studio", world.facts["cue_cfg"].knowledge_tag}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        studio="sunny",
        routine="waltz_turn",
        snag="count",
        cue="clap_count",
        helper="teacher",
        child_name="Lena",
        child_type="girl",
        helper_name="Ms. June",
        rounds=3,
    ),
    StoryParams(
        studio="corner",
        routine="ribbon_skip",
        snag="space",
        cue="tape_marks",
        helper="friend",
        child_name="Ruby",
        child_type="girl",
        helper_name="Maya",
        rounds=3,
    ),
    StoryParams(
        studio="sunny",
        routine="jazz_line",
        snag="balance",
        cue="spot_and_breathe",
        helper="teacher",
        child_name="Theo",
        child_type="boy",
        helper_name="Ms. Rosa",
        rounds=2,
    ),
    StoryParams(
        studio="corner",
        routine="jazz_line",
        snag="timing",
        cue="clap_count",
        helper="friend",
        child_name="Ben",
        child_type="boy",
        helper_name="Ivy",
        rounds=4,
    ),
]


def explain_rejection(snag: Snag, cue: Cue) -> str:
    return (
        f"(No story: {cue.label} does not directly help with {snag.label}. "
        f"The support in this world must match the exact problem the child is practicing.)"
    )


ASP_RULES = r"""
fits(S, C) :- snag(S), cue(C), helps(C, S).
valid(St, R, S, C) :- studio(St), routine(R), snag(S), cue(C), fits(S, C).

smooth :- rounds(N), practice_goal(G), N >= G.
outcome(smooth) :- smooth.
outcome(almost) :- not smooth.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for studio_id in STUDIOS:
        lines.append(asp.fact("studio", studio_id))
    for routine_id in ROUTINES:
        lines.append(asp.fact("routine", routine_id))
    for snag_id in SNAGS:
        lines.append(asp.fact("snag", snag_id))
    for cue_id, cue in CUES.items():
        lines.append(asp.fact("cue", cue_id))
        for snag_id in sorted(cue.helps):
            lines.append(asp.fact("helps", cue_id, snag_id))
    lines.append(asp.fact("practice_goal", PRACTICE_GOAL))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("rounds", params.rounds),
    ])
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
    for i in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(i))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child in a dance studio solves one small practice problem through discussion and repetition."
    )
    ap.add_argument("--studio", choices=STUDIOS)
    ap.add_argument("--routine", choices=ROUTINES)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--rounds", type=int, choices=[1, 2, 3, 4])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snag and args.cue:
        if not cue_fits(SNAGS[args.snag], CUES[args.cue]):
            raise StoryError(explain_rejection(SNAGS[args.snag], CUES[args.cue]))

    combos = [
        c for c in valid_combos()
        if (args.studio is None or c[0] == args.studio)
        and (args.routine is None or c[1] == args.routine)
        and (args.snag is None or c[2] == args.snag)
        and (args.cue is None or c[3] == args.cue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    studio_id, routine_id, snag_id, cue_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = rng.choice(HELPER_NAMES[helper_id])
    rounds = args.rounds if args.rounds is not None else rng.randint(2, 4)
    return StoryParams(
        studio=studio_id,
        routine=routine_id,
        snag=snag_id,
        cue=cue_id,
        helper=helper_id,
        child_name=child_name,
        child_type=gender,
        helper_name=helper_name,
        rounds=rounds,
    )


def generate(params: StoryParams) -> StorySample:
    if params.studio not in STUDIOS:
        raise StoryError(f"(Unknown studio: {params.studio})")
    if params.routine not in ROUTINES:
        raise StoryError(f"(Unknown routine: {params.routine})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.cue not in CUES:
        raise StoryError(f"(Unknown cue: {params.cue})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not cue_fits(SNAGS[params.snag], CUES[params.cue]):
        raise StoryError(explain_rejection(SNAGS[params.snag], CUES[params.cue]))
    if params.rounds not in {1, 2, 3, 4}:
        raise StoryError("(Rounds must be one of 1, 2, 3, or 4.)")

    world = tell(
        STUDIOS[params.studio],
        ROUTINES[params.routine],
        SNAGS[params.snag],
        CUES[params.cue],
        HELPERS[params.helper],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        rounds=params.rounds,
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
        print(f"{len(combos)} compatible (studio, routine, snag, cue) combos:\n")
        for studio_id, routine_id, snag_id, cue_id in combos:
            print(f"  {studio_id:7} {routine_id:12} {snag_id:8} {cue_id}")
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
            header = f"### {p.child_name}: {p.routine} / {p.snag} / {p.cue} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
