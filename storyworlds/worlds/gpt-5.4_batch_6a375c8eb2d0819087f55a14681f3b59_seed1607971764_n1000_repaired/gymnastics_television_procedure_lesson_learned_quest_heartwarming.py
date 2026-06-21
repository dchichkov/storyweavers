#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gymnastics_television_procedure_lesson_learned_quest_heartwarming.py
================================================================================================

A standalone story world about a child who sees a gymnastics move on television,
wants to copy it as part of a little quest, and learns that a safe procedure
matters more than rushing. The world simulates body safety, helper guidance,
and the difference between trying on a risky surface versus preparing a proper
practice space.

Run it
------
    python storyworlds/worlds/gpt-5.4/gymnastics_television_procedure_lesson_learned_quest_heartwarming.py
    python storyworlds/worlds/gpt-5.4/gymnastics_television_procedure_lesson_learned_quest_heartwarming.py --goal sticker --surface rug
    python storyworlds/worlds/gpt-5.4/gymnastics_television_procedure_lesson_learned_quest_heartwarming.py --surface sofa
    python storyworlds/worlds/gpt-5.4/gymnastics_television_procedure_lesson_learned_quest_heartwarming.py --helper coach --trace
    python storyworlds/worlds/gpt-5.4/gymnastics_television_procedure_lesson_learned_quest_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/gymnastics_television_procedure_lesson_learned_quest_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/gymnastics_television_procedure_lesson_learned_quest_heartwarming.py --verify
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
SAFE_THRESHOLD = 4
BRAVE_START = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    stable: bool = False
    cushioned: bool = False
    supervises: bool = False
    teaches: bool = False
    # world axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "coach_woman"}
        male = {"boy", "father", "man", "coach_man"}
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
            "coach_woman": "coach",
            "coach_man": "coach",
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
class Move:
    id: str
    label: str
    quest_line: str
    seen_line: str
    need: str
    risk: int
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
class Surface:
    id: str
    label: str
    phrase: str
    stable: bool
    cushioned: bool
    score: int
    warning: str
    ending: str
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
class Goal:
    id: str
    label: str
    phrase: str
    ending: str
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
class HelperCfg:
    id: str
    person_type: str
    label: str
    opening: str
    calm_line: str
    procedure_wording: str
    reward_line: str
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
class ProcedureCfg:
    id: str
    label: str
    steps: tuple[str, str, str]
    adds: int
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


def _r_prepared_space(world: World) -> list[str]:
    child = world.get("child")
    surface = world.get("surface")
    if child.meters["procedure_done"] < THRESHOLD:
        return []
    sig = ("prepared_space", surface.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if surface.stable:
        child.meters["safety"] += 2
    if surface.cushioned:
        child.meters["safety"] += 1
    return []


def _r_helper_support(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.meters["asked_help"] < THRESHOLD:
        return []
    sig = ("helper_support", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if helper.supervises:
        child.meters["safety"] += 1
    if helper.teaches:
        child.memes["trust"] += 1
        child.memes["confidence"] += 1
    return []


def _r_attempt_result(world: World) -> list[str]:
    child = world.get("child")
    move = world.get("move")
    if child.meters["attempted"] < THRESHOLD:
        return []
    sig = ("attempt_result", move.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    score = child.meters["safety"] - move.meters["risk"]
    if score >= 0:
        child.meters["success"] += 1
        child.memes["joy"] += 1
        child.memes["relief"] += 1
    else:
        child.meters["wobble"] += 1
        child.memes["fear"] += 1
        child.memes["lesson"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="prepared_space", tag="physical", apply=_r_prepared_space),
    Rule(name="helper_support", tag="social", apply=_r_helper_support),
    Rule(name="attempt_result", tag="outcome", apply=_r_attempt_result),
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
        for sent in produced:
            world.say(sent)
    return produced


def safety_score(surface: Surface, procedure: ProcedureCfg, helper: HelperCfg) -> int:
    return surface.score + procedure.adds + (1 if helper.id else 0)


def valid_combo(move: Move, surface: Surface, procedure: ProcedureCfg, helper: HelperCfg) -> bool:
    return safety_score(surface, procedure, helper) >= move.risk


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for move_id, move in MOVES.items():
        for surface_id, surface in SURFACES.items():
            for procedure_id, procedure in PROCEDURES.items():
                for helper_id, helper in HELPERS.items():
                    if valid_combo(move, surface, procedure, helper):
                        out.append((move_id, surface_id, procedure_id, helper_id))
    return out


def predicted_outcome(move: Move, surface: Surface, procedure: ProcedureCfg, helper: HelperCfg) -> str:
    return "success" if valid_combo(move, surface, procedure, helper) else "wobble"


def predict_attempt(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["procedure_done"] = 1
    sim.get("child").meters["asked_help"] = 1
    sim.get("child").meters["attempted"] = 1
    propagate(sim, narrate=False)
    return {
        "safe": sim.get("child").meters["success"] >= THRESHOLD,
        "wobble": sim.get("child").meters["wobble"] >= THRESHOLD,
        "safety": sim.get("child").meters["safety"],
    }


def setup_scene(world: World, child: Entity, helper: Entity, move: Move, goal: Goal) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After breakfast, {child.id} curled up by the television and watched a children's gymnastics show."
    )
    world.say(
        f"On the screen, a smiling team practiced {move.label}, and {move.seen_line}"
    )
    world.say(
        f"{helper.attrs['opening_name']} was nearby, folding a blanket and listening as {child.id} whispered about a quest."
    )
    world.say(
        f'{child.id} wanted to earn {goal.phrase}, and {move.quest_line}'
    )


def announce_quest(world: World, child: Entity, move: Move, goal: Goal) -> None:
    child.memes["desire"] += 1
    world.say(
        f'"If I can do {move.label}, maybe I can earn {goal.phrase} today," {child.id} said.'
    )
    world.say(
        f"The idea made {child.pronoun('possessive')} heart feel bright and busy."
    )


def hurry_toward_try(world: World, child: Entity, surface: Surface) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} hurried toward {surface.phrase}, ready to try at once."
    )


def warn_and_predict(world: World, child: Entity, helper: Entity, move: Move,
                     procedure: ProcedureCfg, surface: Surface) -> None:
    pred = predict_attempt(world)
    world.facts["predicted_safe"] = pred["safe"]
    world.facts["predicted_safety"] = pred["safety"]
    world.say(
        f'{helper.attrs["opening_name"]} knelt beside {child.id}. "{helper.attrs["calm_line"]}"'
    )
    world.say(
        f'{helper.attrs["opening_name"]} pointed at {surface.label} and added, '
        f'"Before gymnastics, we follow a procedure: {procedure.steps[0]}, '
        f'{procedure.steps[1]}, and {procedure.steps[2]}."'
    )
    if pred["safe"]:
        world.say(
            f'"Then your body will be ready for {move.need}," {helper.pronoun()} said.'
        )
    else:
        world.say(
            f'"Without those steps, {surface.warning}," {helper.pronoun()} said.'
        )


def ask_for_help(world: World, child: Entity, helper: Entity) -> None:
    child.meters["asked_help"] = 1
    child.memes["trust"] += 1
    world.say(
        f"{child.id} looked up and took a slower breath. "
        f'"Will you help me do it the right way?" {child.pronoun()} asked.'
    )


def do_procedure(world: World, child: Entity, procedure: ProcedureCfg) -> None:
    child.meters["procedure_done"] = 1
    child.memes["patience"] += 1
    world.say(
        f"Together they followed the procedure. First, they {procedure.steps[0]}. "
        f"Next, they {procedure.steps[1]}. Last, they {procedure.steps[2]}."
    )


def attempt_move(world: World, child: Entity, move: Move, surface: Surface) -> None:
    child.meters["attempted"] = 1
    propagate(world, narrate=False)
    if child.meters["success"] >= THRESHOLD:
        world.say(
            f"When {child.id} tried {move.label} on {surface.phrase}, {child.pronoun('possessive')} hands and feet knew where to go."
        )
        world.say(
            f"The move was not perfect, but it was careful, steady, and real."
        )
    else:
        world.say(
            f"When {child.id} tried {move.label} on {surface.phrase}, {child.pronoun('possessive')} body wobbled."
        )
        world.say(
            f"{child.pronoun().capitalize()} dropped to {child.pronoun('possessive')} knees with a surprised little gasp, but {child.pronoun()} was not hurt."
        )


def lesson_or_praise(world: World, child: Entity, helper: Entity, surface: Surface, move: Move) -> None:
    if child.meters["success"] >= THRESHOLD:
        child.memes["lesson"] += 1
        world.say(
            f'{helper.attrs["opening_name"]} clapped softly. "{helper.attrs["reward_line"]}"'
        )
        world.say(
            f"{child.id} understood that the safest way had helped the quest along."
        )
    else:
        child.meters["procedure_done"] = 1
        child.meters["asked_help"] = 1
        child.meters["attempted"] = 0
        child.meters["success"] = 0
        child.meters["wobble"] = 0
        world.say(
            f'{helper.attrs["opening_name"]} wrapped an arm around {child.id}. "{helper.attrs["procedure_wording"]}"'
        )
        world.say(
            f"{child.id} nodded. The television had shown a shining move, but not the quiet steps that made it safe."
        )
        world.para()
        world.say(
            f"So they started over. They {world.facts['procedure'].steps[0]}, "
            f"{world.facts['procedure'].steps[1]}, and {world.facts['procedure'].steps[2]}."
        )
        world.get("child").meters["attempted"] = 1
        propagate(world, narrate=False)
        world.say(
            f"This time, on {surface.phrase}, {child.id} moved more carefully and landed with a proud smile."
        )
        world.say(
            f"The lesson stayed with {child.pronoun('object')}: brave hearts still need safe steps."
        )


def reward_ending(world: World, child: Entity, helper: Entity, goal: Goal, surface: Surface) -> None:
    child.memes["joy"] += 1
    world.say(
        f'At the end, {helper.attrs["opening_name"]} gave {child.pronoun("object")} {goal.phrase}.'
    )
    world.say(
        f"{goal.ending} {surface.ending}"
    )


MOVES = {
    "forward_roll": Move(
        id="forward_roll",
        label="a forward roll",
        quest_line="that little tumble looked like the first shining step of a grand quest.",
        seen_line="the children on television tucked their chins and rolled like smooth pebbles down a hill.",
        need="a tucked chin and a clear path",
        risk=3,
        tags={"gymnastics", "television"},
    ),
    "cartwheel": Move(
        id="cartwheel",
        label="a cartwheel",
        quest_line="that turning move looked like a doorway into a bigger quest.",
        seen_line="the children on television reached long arms toward the floor and spun like bright pinwheels.",
        need="space for wide arms and a steady landing",
        risk=4,
        tags={"gymnastics", "television"},
    ),
    "handstand": Move(
        id="handstand",
        label="a handstand",
        quest_line="that upside-down moment looked like the bravest step of all in the quest.",
        seen_line="the children on television stacked their bodies tall and still, with grown-ups nearby.",
        need="strong arms, spotting help, and careful balance",
        risk=5,
        tags={"gymnastics", "television"},
    ),
}

SURFACES = {
    "mat": Surface(
        id="mat",
        label="the practice mat",
        phrase="the blue practice mat",
        stable=True,
        cushioned=True,
        score=3,
        warning="you could slip into a scare before your body is ready",
        ending="The mat waited in the middle of the room like a small safe island.",
        tags={"mat", "procedure"},
    ),
    "rug": Surface(
        id="rug",
        label="the rug",
        phrase="the thick living-room rug",
        stable=True,
        cushioned=False,
        score=2,
        warning="the floor underneath is hard, so a wobble would feel much bigger",
        ending="The rug looked ordinary, but it had become a place for careful practice instead of rushing.",
        tags={"rug", "procedure"},
    ),
    "grass": Surface(
        id="grass",
        label="the grass",
        phrase="the soft grass in the yard",
        stable=False,
        cushioned=True,
        score=2,
        warning="the ground can shift under your feet when you turn",
        ending="Outside, the grass sparkled in the sun, and even the yard felt like part of the new routine.",
        tags={"grass", "procedure"},
    ),
    "sofa": Surface(
        id="sofa",
        label="the sofa",
        phrase="the springy sofa cushions",
        stable=False,
        cushioned=True,
        score=1,
        warning="springy cushions can throw you sideways instead of helping",
        ending="The sofa was left for sitting and story time, not for flips.",
        tags={"sofa", "procedure"},
    ),
}

GOALS = {
    "sticker": Goal(
        id="sticker",
        label="star sticker",
        phrase="a gold star sticker",
        ending="The tiny star shone on the chart by the kitchen door.",
        tags={"reward"},
    ),
    "ribbon": Goal(
        id="ribbon",
        label="paper ribbon",
        phrase="a paper ribbon",
        ending="The ribbon fluttered from a shelf and made the whole room feel proud.",
        tags={"reward"},
    ),
    "stamp": Goal(
        id="stamp",
        label="sparkle stamp",
        phrase="a sparkle stamp on the quest page",
        ending="The stamped page went into the family notebook for safe brave tries.",
        tags={"reward"},
    ),
}

HELPERS = {
    "mother": HelperCfg(
        id="mother",
        person_type="mother",
        label="mom",
        opening="Mom was nearby",
        calm_line="I love how excited you are, but excitement goes with careful choices.",
        procedure_wording="Big moves need a safe procedure first. We can learn, but we do not rush.",
        reward_line="You earned your prize by listening, asking for help, and following the procedure.",
        tags={"adult_help", "procedure"},
    ),
    "father": HelperCfg(
        id="father",
        person_type="father",
        label="dad",
        opening="Dad was nearby",
        calm_line="That looks fun, but fun is best when your body is ready.",
        procedure_wording="The lesson is not 'never try.' The lesson is 'follow the procedure before you try.'",
        reward_line="You did not just finish the move. You finished it safely.",
        tags={"adult_help", "procedure"},
    ),
    "coach": HelperCfg(
        id="coach",
        person_type="coach_woman",
        label="coach",
        opening="Coach Mira was nearby",
        calm_line="A brave gymnast slows down enough to practice wisely.",
        procedure_wording="Television shows the big moment. Real practice includes the warm-up, the mat, and a helper.",
        reward_line="That was the kind of try gymnasts can build on.",
        tags={"adult_help", "procedure", "coach"},
    ),
}

PROCEDURES = {
    "full": ProcedureCfg(
        id="full",
        label="full safe procedure",
        steps=("cleared toys out of the way", "stretched arms and legs", "put the safest surface in the best spot and checked it together"),
        adds=2,
        tags={"procedure"},
    ),
    "warmup": ProcedureCfg(
        id="warmup",
        label="warm-up procedure",
        steps=("shook out arms and legs", "counted a few slow stretches", "asked where the best place to practice would be"),
        adds=1,
        tags={"procedure"},
    ),
    "spotting": ProcedureCfg(
        id="spotting",
        label="spotting procedure",
        steps=("made space around the practice area", "warmed up shoulders and wrists", "agreed on where the helper would stand and when to stop"),
        adds=2,
        tags={"procedure"},
    ),
}


@dataclass
class StoryParams:
    move: str
    surface: str
    goal: str
    helper: str
    procedure: str
    child_name: str
    child_gender: str
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


GIRL_NAMES = ["Lina", "Maya", "Ava", "Nora", "Lucy", "Ella", "Zoe", "Ruby"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Leo", "Max", "Owen", "Theo", "Sam"]


def tell(move: Move, surface: Surface, goal: Goal, helper_cfg: HelperCfg,
         procedure: ProcedureCfg, child_name: str = "Lina",
         child_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"name": child_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.person_type,
        label=helper_cfg.label,
        role="helper",
        supervises=True,
        teaches=True,
        attrs={
            "opening_name": helper_cfg.opening.split()[0] if helper_cfg.id != "coach" else "Coach Mira",
            "calm_line": helper_cfg.calm_line,
        },
    ))
    surface_ent = world.add(Entity(
        id="surface",
        type="surface",
        label=surface.label,
        stable=surface.stable,
        cushioned=surface.cushioned,
    ))
    move_ent = world.add(Entity(
        id="move",
        type="move",
        label=move.label,
    ))
    move_ent.meters["risk"] = float(move.risk)

    helper.attrs["reward_line"] = helper_cfg.reward_line
    helper.attrs["procedure_wording"] = helper_cfg.procedure_wording
    helper.attrs["opening_name"] = "Coach Mira" if helper_cfg.id == "coach" else helper_cfg.label_word.capitalize()

    child.id = child_name
    world.entities[child_name] = world.entities.pop("child")
    helper.id = helper_cfg.label_word.capitalize() if helper_cfg.id != "coach" else "Coach Mira"
    world.entities[helper.id] = world.entities.pop("helper")
    surface_ent.id = "surface"
    move_ent.id = "move"

    # stable lookup aliases for rules/prediction
    world.entities["child"] = child
    world.entities["helper"] = helper

    child.memes["bravery"] = BRAVE_START
    child.meters["procedure_done"] = 0
    child.meters["asked_help"] = 0
    child.meters["attempted"] = 0
    child.meters["safety"] = 0
    child.meters["success"] = 0
    child.meters["wobble"] = 0
    child.memes["fear"] = 0
    child.memes["lesson"] = 0
    child.memes["confidence"] = 0
    child.memes["trust"] = 0
    helper.meters["attention"] = 1

    world.facts.update(
        move=move,
        surface=surface,
        goal=goal,
        helper_cfg=helper_cfg,
        procedure=procedure,
        child=child,
        helper=helper,
    )

    setup_scene(world, child, helper, move, goal)
    announce_quest(world, child, move, goal)

    world.para()
    hurry_toward_try(world, child, surface)
    warn_and_predict(world, child, helper, move, procedure, surface)
    ask_for_help(world, child, helper)

    world.para()
    do_procedure(world, child, procedure)
    attempt_move(world, child, move, surface)
    lesson_or_praise(world, child, helper, surface, move)

    world.para()
    reward_ending(world, child, helper, goal, surface)

    outcome = "success" if child.meters["success"] >= THRESHOLD else "wobble_then_success"
    world.facts.update(
        outcome=outcome,
        succeeded=child.meters["success"] >= THRESHOLD,
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    move = f["move"]
    goal = f["goal"]
    helper_cfg = f["helper_cfg"]
    procedure = f["procedure"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "gymnastics", "television", and "procedure".',
        f"Tell a gentle quest story where {child.id} sees {move.label} on television, wants {goal.phrase}, and learns to follow a safe procedure with help from {helper_cfg.label}.",
        f"Write a cozy lesson-learned story about a child practicing gymnastics, slowing down, and discovering that a careful procedure can help a brave dream come true.",
    ]


KNOWLEDGE = {
    "gymnastics": [(
        "What is gymnastics?",
        "Gymnastics is a kind of movement play and sport where people balance, roll, jump, and stretch. It works best when children practice with space, soft surfaces, and grown-up help."
    )],
    "television": [(
        "Why should you be careful about copying something from television?",
        "Television often shows the exciting part but not every safety step. A grown-up can help you slow down and choose the right way to practice."
    )],
    "procedure": [(
        "What is a procedure?",
        "A procedure is a set of steps you follow in order. Safe procedures help your body get ready and help you remember what to do."
    )],
    "mat": [(
        "Why is a practice mat helpful?",
        "A practice mat gives you a softer place to land and a clear place to practice. It does not make a move magic, but it can make practice safer."
    )],
    "adult_help": [(
        "Why should a child ask a grown-up for help before trying a tricky move?",
        "A grown-up can watch, teach the steps, and stop the practice if something feels unsafe. Asking for help is a smart part of being brave."
    )],
    "warmup": [(
        "Why do people warm up before moving a lot?",
        "Warming up helps muscles and joints get ready to move. It can make practice feel steadier and more comfortable."
    )],
}

KNOWLEDGE_ORDER = ["gymnastics", "television", "procedure", "mat", "adult_help", "warmup"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    move = f["move"]
    surface = f["surface"]
    goal = f["goal"]
    helper_cfg = f["helper_cfg"]
    procedure = f["procedure"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who watched gymnastics on television and wanted to complete a little quest. {helper_cfg.label.capitalize()} stayed close to help {child.pronoun('object')} practice safely."
        ),
        (
            f"What did {child.id} want to do?",
            f"{child.id} wanted to try {move.label} and earn {goal.phrase}. The quest made the move feel exciting and important."
        ),
        (
            "Why did the grown-up talk about a procedure?",
            f"The grown-up knew that tricky movement should not begin with rushing. {helper_cfg.label.capitalize()} wanted {child.id} to clear space, warm up, and choose the best place before trying the move."
        ),
        (
            f"How did the television matter in the story?",
            f"The television gave {child.id} the idea and showed the shining finished move. But it did not show every careful step, which is why the helper explained the safe procedure."
        ),
    ]
    if outcome == "success":
        qa.append((
            f"How did {child.id} succeed?",
            f"{child.id} asked for help and followed the procedure step by step. That made the practice space safer and helped {child.pronoun('object')} do {move.label} more steadily."
        ))
    else:
        qa.append((
            f"What lesson did {child.id} learn?",
            f"{child.id} learned that a brave wish is not enough by itself. After a wobble, {child.pronoun()} understood that gymnastics needs safe steps, help, and patience."
        ))
    qa.append((
        "How did the story end?",
        f"It ended warmly with {child.id} receiving {goal.phrase} after practicing the careful way. The ending shows that the quest was really about learning how to do things safely."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"gymnastics", "television", "procedure", "adult_help", "warmup"}
    if f["surface"].id == "mat":
        tags.add("mat")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for eid, ent in world.entities.items():
        if eid in {"child", "helper"}:
            continue
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.stable:
            bits.append("stable=True")
        if ent.cushioned:
            bits.append("cushioned=True")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {eid:12} ({ent.type:10}) {' '.join(bits)}")
    child = world.facts["child"]
    helper = world.facts["helper"]
    for ent in (child, helper):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(move: Move, surface: Surface, procedure: ProcedureCfg, helper: HelperCfg) -> str:
    score = safety_score(surface, procedure, helper)
    return (
        f"(No story: {move.label} is too advanced for {surface.phrase} with "
        f"{procedure.label}. This setup scores {score} safety points, but the move "
        f"needs at least {move.risk}. Pick a steadier surface, a stronger procedure, "
        f"or more guided practice.)"
    )


ASP_RULES = r"""
safety_total(M,S,P,H,Score) :-
    chosen_move(M), chosen_surface(S), chosen_procedure(P), chosen_helper(H),
    surface_score(S,SS), procedure_adds(P,PA), helper_adds(H,HA),
    Score = SS + PA + HA.

valid(M,S,P,H) :-
    move(M), surface(S), procedure(P), helper(H),
    safety_total(M,S,P,H,Score), move_risk(M,Risk), Score >= Risk.

outcome(success) :-
    chosen_move(M), chosen_surface(S), chosen_procedure(P), chosen_helper(H),
    safety_total(M,S,P,H,Score), move_risk(M,Risk), Score >= Risk.

outcome(wobble) :-
    chosen_move(M), chosen_surface(S), chosen_procedure(P), chosen_helper(H),
    safety_total(M,S,P,H,Score), move_risk(M,Risk), Score < Risk.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for move_id, move in MOVES.items():
        lines.append(asp.fact("move", move_id))
        lines.append(asp.fact("move_risk", move_id, move.risk))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        lines.append(asp.fact("surface_score", surface_id, surface.score))
    for procedure_id, procedure in PROCEDURES.items():
        lines.append(asp.fact("procedure", procedure_id))
        lines.append(asp.fact("procedure_adds", procedure_id, procedure.adds))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_adds", helper_id, 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_move", params.move),
        asp.fact("chosen_surface", params.surface),
        asp.fact("chosen_procedure", params.procedure),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        move="forward_roll",
        surface="mat",
        goal="sticker",
        helper="mother",
        procedure="full",
        child_name="Lina",
        child_gender="girl",
    ),
    StoryParams(
        move="cartwheel",
        surface="rug",
        goal="ribbon",
        helper="father",
        procedure="spotting",
        child_name="Eli",
        child_gender="boy",
    ),
    StoryParams(
        move="handstand",
        surface="mat",
        goal="stamp",
        helper="coach",
        procedure="spotting",
        child_name="Maya",
        child_gender="girl",
    ),
    StoryParams(
        move="forward_roll",
        surface="grass",
        goal="ribbon",
        helper="father",
        procedure="full",
        child_name="Noah",
        child_gender="boy",
    ),
    StoryParams(
        move="cartwheel",
        surface="mat",
        goal="stamp",
        helper="coach",
        procedure="full",
        child_name="Ruby",
        child_gender="girl",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: gymnastics on television, a careful procedure, and a heartwarming lesson."
    )
    ap.add_argument("--move", choices=sorted(MOVES))
    ap.add_argument("--surface", choices=sorted(SURFACES))
    ap.add_argument("--goal", choices=sorted(GOALS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--procedure", choices=sorted(PROCEDURES))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story setups from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.move and args.surface and args.procedure and args.helper:
        move = MOVES[args.move]
        surface = SURFACES[args.surface]
        procedure = PROCEDURES[args.procedure]
        helper = HELPERS[args.helper]
        if not valid_combo(move, surface, procedure, helper):
            raise StoryError(explain_rejection(move, surface, procedure, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.move is None or combo[0] == args.move)
        and (args.surface is None or combo[1] == args.surface)
        and (args.procedure is None or combo[2] == args.procedure)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    move_id, surface_id, procedure_id, helper_id = rng.choice(sorted(combos))
    goal_id = args.goal or rng.choice(sorted(GOALS))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, gender)

    return StoryParams(
        move=move_id,
        surface=surface_id,
        goal=goal_id,
        helper=helper_id,
        procedure=procedure_id,
        child_name=child_name,
        child_gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        move = MOVES[params.move]
        surface = SURFACES[params.surface]
        goal = GOALS[params.goal]
        helper = HELPERS[params.helper]
        procedure = PROCEDURES[params.procedure]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]!r})") from None

    if not valid_combo(move, surface, procedure, helper):
        raise StoryError(explain_rejection(move, surface, procedure, helper))

    world = tell(
        move=move,
        surface=surface,
        goal=goal,
        helper_cfg=helper,
        procedure=procedure,
        child_name=params.child_name,
        child_gender=params.child_gender,
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


def outcome_of(params: StoryParams) -> str:
    return predicted_outcome(
        move=MOVES[params.move],
        surface=SURFACES[params.surface],
        procedure=PROCEDURES[params.procedure],
        helper=HELPERS[params.helper],
    )


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    check_cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        check_cases.append(params)

    bad = 0
    for params in check_cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(check_cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(check_cases)} outcomes differ.")

    try:
        smoke = generate(check_cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (move, surface, procedure, helper) combos:\n")
        for move, surface, procedure, helper in combos:
            print(f"  {move:13} {surface:7} {procedure:8} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.move} on {p.surface} "
                f"({p.procedure}, {p.helper}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
