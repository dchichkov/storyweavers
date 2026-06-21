#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/smooth_escalator_bravery_space_adventure.py
======================================================================

A standalone story world about a child on an escalator who feels afraid, learns
a smooth stepping trick, accepts help, and reaches the top like a space
adventurer. The world model tracks physical balance and position plus emotional
fear and bravery, and the prose follows the simulated turn from hesitation to
safe success.

Run it
------
    python storyworlds/worlds/gpt-5.4/smooth_escalator_bravery_space_adventure.py
    python storyworlds/worlds/gpt-5.4/smooth_escalator_bravery_space_adventure.py --theme rocket --helper parent
    python storyworlds/worlds/gpt-5.4/smooth_escalator_bravery_space_adventure.py --helper none
    python storyworlds/worlds/gpt-5.4/smooth_escalator_bravery_space_adventure.py --verify
    python storyworlds/worlds/gpt-5.4/smooth_escalator_bravery_space_adventure.py --asp
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
MIN_READY = 3
SAFE_HELPERS = {"parent", "sibling", "worker"}
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful"}


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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
            "worker": "worker",
            "sister": "sister",
            "brother": "brother",
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
class Theme:
    id: str
    place_line: str
    pretend_name: str
    escalator_name: str
    goal: str
    sendoff: str
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
class Helper:
    id: str
    role_type: str
    label: str
    phrase: str
    action: str
    calm_line: str
    coaching: str
    brave_bonus: int
    safety: int
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
class StepMethod:
    id: str
    name: str
    foot_line: str
    hand_line: str
    feel_line: str
    ready_bonus: int
    balance_bonus: int
    safe: bool = True
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
class StoryParams:
    theme: str
    helper: str
    method: str
    child_name: str
    child_gender: str
    helper_name: str
    trait: str
    age: int = 4
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


def _r_ready(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["guided"] >= THRESHOLD and ("ready", child.id) not in world.fired:
        world.fired.add(("ready", child.id))
        child.meters["ready"] += 2
        child.memes["bravery"] += 1
        out.append("__ready__")
    if child.meters["prepared"] >= THRESHOLD and ("prepared_ready", child.id) not in world.fired:
        world.fired.add(("prepared_ready", child.id))
        child.meters["ready"] += 1
        out.append("__ready__")
    return out


def _r_board(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["ready"] >= MIN_READY and child.meters["boarded"] < THRESHOLD:
        sig = ("board", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["boarded"] += 1
            child.meters["riding"] += 1
            child.memes["fear"] = max(0.0, child.memes["fear"] - 2.0)
            child.memes["bravery"] += 1
            out.append("__boarded__")
    return out


def _r_arrive(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["riding"] >= THRESHOLD and ("arrive", child.id) not in world.fired:
        world.fired.add(("arrive", child.id))
        child.meters["arrived"] += 1
        child.memes["joy"] += 1
        out.append("__arrived__")
    return out


CAUSAL_RULES = [
    Rule(name="ready", tag="social", apply=_r_ready),
    Rule(name="board", tag="physical", apply=_r_board),
    Rule(name="arrive", tag="physical", apply=_r_arrive),
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
            if not s.startswith("__"):
                world.say(s)
    return produced


THEMES = {
    "rocket": Theme(
        id="rocket",
        place_line="At the mall, the bright escalator rose between the floors like a silver rocket ramp.",
        pretend_name="space captain",
        escalator_name="rocket ramp",
        goal="the star station at the top",
        sendoff="rode upward as if launching into the stars",
        tags={"escalator", "space"},
    ),
    "moon": Theme(
        id="moon",
        place_line="At the mall, the escalator hummed softly, as smooth and shining as a moon bridge.",
        pretend_name="moon explorer",
        escalator_name="moon bridge",
        goal="the quiet moon deck above",
        sendoff="glided upward like a small explorer crossing the moon",
        tags={"escalator", "space"},
    ),
    "galaxy": Theme(
        id="galaxy",
        place_line="At the mall, the escalator carried people upward in a smooth silver line, like a path through the galaxy.",
        pretend_name="galaxy scout",
        escalator_name="galaxy path",
        goal="the bright shop at the top",
        sendoff="rose upward like a scout heading into the galaxy",
        tags={"escalator", "space"},
    ),
}

HELPERS = {
    "parent": Helper(
        id="parent",
        role_type="mother",
        label="parent",
        phrase="a calm parent",
        action="held out a warm hand",
        calm_line='"I will stay right beside you,"',
        coaching="Watch one step, hold the rail, and step on when a flat step comes.",
        brave_bonus=2,
        safety=3,
        tags={"adult", "help"},
    ),
    "sibling": Helper(
        id="sibling",
        role_type="sister",
        label="older sibling",
        phrase="an older sibling",
        action="stood close and showed the timing first",
        calm_line='"You can do it with me,"',
        coaching="We will count together, hold the rail, and step on smoothly.",
        brave_bonus=1,
        safety=2,
        tags={"family", "help"},
    ),
    "worker": Helper(
        id="worker",
        role_type="worker",
        label="store worker",
        phrase="a kind store worker",
        action="smiled and slowed the moment down with a gentle voice",
        calm_line='"Take your time,"',
        coaching="Face forward, hold the rail, and step onto the flat step when you are ready.",
        brave_bonus=1,
        safety=2,
        tags={"worker", "help"},
    ),
    "none": Helper(
        id="none",
        role_type="thing",
        label="no helper",
        phrase="no helper",
        action="waited far away",
        calm_line='""',
        coaching="",
        brave_bonus=0,
        safety=0,
        tags=set(),
    ),
}

METHODS = {
    "rail_and_count": StepMethod(
        id="rail_and_count",
        name="rail and count",
        foot_line="The child watched the steps, counted one, two, three, and chose a flat step.",
        hand_line="One hand held the rail.",
        feel_line="That made the moving stairs feel less jumpy and more smooth.",
        ready_bonus=2,
        balance_bonus=2,
        safe=True,
        tags={"rail", "counting"},
    ),
    "big_step": StepMethod(
        id="big_step",
        name="big step",
        foot_line="The child bent a little, looked straight ahead, and took one clear step forward.",
        hand_line="One hand reached for the rail at once.",
        feel_line="The clear move felt smooth because there was no stopping halfway.",
        ready_bonus=2,
        balance_bonus=1,
        safe=True,
        tags={"rail", "step"},
    ),
    "stand_and_breathe": StepMethod(
        id="stand_and_breathe",
        name="stand and breathe",
        foot_line="The child took a deep breath, watched the step arrive, and stepped on when it was flat.",
        hand_line="Small fingers closed around the rail.",
        feel_line="Breathing slowly made the ride feel smooth enough to trust.",
        ready_bonus=1,
        balance_bonus=2,
        safe=True,
        tags={"breathing", "rail"},
    ),
    "jump": StepMethod(
        id="jump",
        name="jump",
        foot_line="The child tried to jump at the moving step.",
        hand_line="The rail was missed.",
        feel_line="The rushed move was not smooth at all.",
        ready_bonus=0,
        balance_bonus=0,
        safe=False,
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Ava", "Nora", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Leo", "Max", "Sam", "Theo", "Noah", "Eli", "Finn", "Milo"]
TRAITS = ["careful", "steady", "curious", "thoughtful", "eager", "quiet"]


def helper_ready_bonus(helper: Helper, trait: str) -> int:
    bonus = helper.brave_bonus
    if trait in CAUTIOUS_TRAITS:
        bonus += 1
    return bonus


def can_succeed(helper: Helper, method: StepMethod, trait: str) -> bool:
    if not method.safe:
        return False
    ready = 1 + method.ready_bonus + method.balance_bonus + helper_ready_bonus(helper, trait)
    return helper.id in SAFE_HELPERS and ready >= MIN_READY


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for helper_id, helper in HELPERS.items():
            for method_id, method in METHODS.items():
                if can_succeed(helper, method, "careful"):
                    combos.append((theme_id, helper_id, method_id))
    return combos


def explain_rejection(helper: Helper, method: StepMethod) -> str:
    if helper.id == "none":
        return ("(No story: in this world, a small child does not ride the escalator alone. "
                "Pick a helper like parent, sibling, or worker.)")
    if not method.safe:
        return ("(No story: jumping onto an escalator is not a safe or sensible method. "
                "Pick a smooth stepping method with the rail.)")
    return ("(No story: this helper and method do not make a believable safe ride in this world.)")


def predict_success(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    method = sim.facts["method_cfg"]
    helper = sim.facts["helper_cfg"]
    child.meters["prepared"] += 1
    child.meters["ready"] += method.ready_bonus + method.balance_bonus + helper_ready_bonus(helper, child.attrs["trait"])
    if helper.id in SAFE_HELPERS:
        child.meters["guided"] += 1
    propagate(sim, narrate=False)
    return {
        "boarded": sim.get("child").meters["boarded"] >= THRESHOLD,
        "arrived": sim.get("child").meters["arrived"] >= THRESHOLD,
        "ready": sim.get("child").meters["ready"],
    }


def introduce(world: World, child: Entity, theme: Theme) -> None:
    world.say(
        f"{theme.place_line} {child.id} stopped at the bottom and stared up."
    )
    world.say(
        f"To {child.id}, the moving stairs looked like a {theme.escalator_name} leading to {theme.goal}."
    )


def want_up(world: World, child: Entity, theme: Theme) -> None:
    child.memes["wonder"] += 1
    world.say(
        f'{child.id} wanted to be a {theme.pretend_name} and go up right away.'
    )


def hesitate(world: World, child: Entity) -> None:
    child.memes["fear"] += 2
    child.meters["paused"] += 1
    world.say(
        f'''But when the steps slid out from under the metal comb, {child.pronoun()} tucked close and whispered, '''
        f'"It is moving too fast for me."'
    )


def helper_arrives(world: World, child: Entity, helper_ent: Entity, helper: Helper) -> None:
    child.memes["trust"] += 1
    world.say(
        f"{helper_ent.id} came near, {helper.action}. {helper.calm_line} {helper_ent.id} said. "
        f'"{helper.coaching}"'
    )


def coach(world: World, child: Entity, helper_ent: Entity, helper: Helper, method: StepMethod) -> None:
    child.meters["prepared"] += 1
    child.meters["ready"] += method.ready_bonus
    child.meters["balance"] += method.balance_bonus
    if helper.id in SAFE_HELPERS:
        child.meters["guided"] += 1
    child.memes["bravery"] += helper_ready_bonus(helper, child.attrs["trait"])
    world.say(method.foot_line)
    world.say(method.hand_line)
    world.say(method.feel_line)
    pred = predict_success(world)
    world.facts["pred_ready"] = pred["ready"]
    world.facts["pred_boarded"] = pred["boarded"]


def board(world: World, child: Entity, theme: Theme) -> None:
    propagate(world, narrate=False)
    if child.meters["boarded"] < THRESHOLD:
        raise StoryError("The child was not ready to board the escalator safely.")
    world.say(
        f"Then {child.id} stepped on. The step carried {child.pronoun('object')} upward, and {child.pronoun('possessive')} knees stopped wobbling."
    )


def ride(world: World, child: Entity, helper_ent: Entity, theme: Theme) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{child.id} stood tall, held the rail, and rode beside {helper_ent.id} as if the {theme.escalator_name} really were a path to space."
    )


def arrive(world: World, child: Entity, helper_ent: Entity, theme: Theme) -> None:
    propagate(world, narrate=False)
    if child.meters["arrived"] < THRESHOLD:
        raise StoryError("The ride never reached its ending state.")
    child.memes["pride"] += 1
    world.say(
        f"At the top, {child.id} stepped off with one last smooth step."
    )
    world.say(
        f'{helper_ent.id} smiled. "{child.id}, that was real bravery," {helper_ent.pronoun()} said.'
    )
    world.say(
        f"{child.id} looked back down the shining escalator and grinned. Now the {theme.escalator_name} did not seem scary anymore; it {theme.sendoff}."
    )


def tell(theme: Theme, helper: Helper, method: StepMethod,
         child_name: str = "Luna", child_gender: str = "girl",
         helper_name: str = "Mom", trait: str = "careful", age: int = 4) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={"trait": trait, "age": age},
    ))
    helper_ent = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper.role_type,
        role="helper",
        label=helper.label,
        attrs={"helper_id": helper.id},
    ))
    world.add(Entity(id="escalator", type="escalator", label="escalator"))
    child.meters["prepared"] = 0.0
    child.meters["guided"] = 0.0
    child.meters["ready"] = 0.0
    child.meters["balance"] = 0.0
    child.meters["boarded"] = 0.0
    child.meters["riding"] = 0.0
    child.meters["arrived"] = 0.0
    child.meters["paused"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["bravery"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["pride"] = 0.0
    child.memes["wonder"] = 0.0
    world.facts["theme_cfg"] = theme
    world.facts["helper_cfg"] = helper
    world.facts["method_cfg"] = method
    world.facts["child"] = child
    world.facts["helper"] = helper_ent

    introduce(world, child, theme)
    want_up(world, child, theme)

    world.para()
    hesitate(world, child)

    if helper.id not in SAFE_HELPERS:
        raise StoryError(explain_rejection(helper, method))
    if not method.safe:
        raise StoryError(explain_rejection(helper, method))

    helper_arrives(world, child, helper_ent, helper)
    coach(world, child, helper_ent, helper, method)

    world.para()
    board(world, child, theme)
    ride(world, child, helper_ent, theme)
    arrive(world, child, helper_ent, theme)

    world.facts.update(
        succeeded=child.meters["arrived"] >= THRESHOLD,
        brave=child.memes["bravery"] >= THRESHOLD,
        smooth=method.safe,
        helper_used=helper.id,
        method_used=method.id,
    )
    return world


KNOWLEDGE = {
    "escalator": [
        ("What is an escalator?",
         "An escalator is a moving staircase that carries people up or down. You step on a flat step, ride, and step off at the end.")
    ],
    "rail": [
        ("Why should you hold the rail on an escalator?",
         "Holding the rail helps you stay balanced while the stairs move. It gives your body something steady to trust.")
    ],
    "counting": [
        ("Why can counting help when something feels scary?",
         "Counting gives your mind a simple job and helps you slow down. That can make a big moving thing feel more manageable.")
    ],
    "breathing": [
        ("Why does slow breathing help with fear?",
         "Slow breathing helps your body calm down. When your body feels calmer, brave choices are easier.")
    ],
    "help": [
        ("What should a child do if an escalator feels scary?",
         "Stay close to a trusted grown-up or helper and ask for help. Waiting for calm guidance is a brave choice.")
    ],
    "space": [
        ("Why do children pretend ordinary things are part of space adventures?",
         "Pretend play helps children turn a new place into a story they understand. That can make them feel more curious and brave.")
    ],
}
KNOWLEDGE_ORDER = ["escalator", "rail", "counting", "breathing", "help", "space"]


def generation_prompts(world: World) -> list[str]:
    theme = world.facts["theme_cfg"]
    child = world.facts["child"]
    helper = world.facts["helper_cfg"]
    method = world.facts["method_cfg"]
    return [
        f'Write a short story for a 3-to-5-year-old about bravery on an escalator, using the word "smooth" and a space-adventure feeling.',
        f"Tell a gentle story where a {child.type} named {child.id} feels nervous on an escalator, but {helper.phrase} helps with a {method.name} trick.",
        f"Write a child-facing story in which an escalator becomes a {theme.escalator_name} and the ending shows the child acting brave at the top.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper_ent = world.facts["helper"]
    helper = world.facts["helper_cfg"]
    method = world.facts["method_cfg"]
    theme = world.facts["theme_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a young child at an escalator, and {helper_ent.id}, who helps from nearby. Together they turn the ride into a little space adventure."
        ),
        (
            f"Why did {child.id} stop at the bottom of the escalator?",
            f"{child.id} wanted to go up, but the moving steps looked fast and strange, so fear made {child.pronoun('object')} pause. The scary part was not the destination; it was the moment of stepping onto the moving stair."
        ),
        (
            f"How did {helper_ent.id} help {child.id}?",
            f"{helper_ent.id} stayed close, spoke calmly, and showed {child.id} how to wait for a flat step and hold the rail. That help gave {child.pronoun('object')} enough trust and readiness to step on safely."
        ),
        (
            f"What made the escalator feel smooth instead of scary?",
            f"The smooth feeling came when {child.id} used the {method.name} method instead of rushing. Holding the rail and choosing the right step turned the moving stairs into something {child.pronoun()} could understand."
        ),
        (
            f"How did {child.id} show bravery?",
            f"{child.id} showed bravery by stepping onto the escalator even after feeling afraid. The brave moment happened because {child.pronoun()} listened, prepared carefully, and did the safe thing anyway."
        ),
        (
            "How did the story end?",
            f"It ended with {child.id} stepping off at the top with a grin and looking back at the {theme.escalator_name}. The ending image shows that the same escalator now felt like part of an adventure instead of a threat."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    helper = world.facts["helper_cfg"]
    method = world.facts["method_cfg"]
    theme = world.facts["theme_cfg"]
    tags = {"escalator", "help", "space"} | set(method.tags) | set(theme.tags)
    if helper.id in SAFE_HELPERS:
        tags.add("help")
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
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="rocket",
        helper="parent",
        method="rail_and_count",
        child_name="Luna",
        child_gender="girl",
        helper_name="Mom",
        trait="careful",
        age=4,
    ),
    StoryParams(
        theme="moon",
        helper="sibling",
        method="big_step",
        child_name="Leo",
        child_gender="boy",
        helper_name="Maya",
        trait="steady",
        age=5,
    ),
    StoryParams(
        theme="galaxy",
        helper="worker",
        method="stand_and_breathe",
        child_name="Ava",
        child_gender="girl",
        helper_name="Nina",
        trait="thoughtful",
        age=4,
    ),
]


ASP_RULES = r"""
safe_helper(H) :- helper(H), safety(H,S), S >= 2.
valid(T,H,M) :- theme(T), helper(H), method(M), safe_helper(H), safe_method(M).

ready_score(H,M,Tr, 1 + RB + BB + HB + TB) :-
    helper(H), method(M), trait(Tr),
    method_ready(M,RB), method_balance(M,BB), helper_brave(H,HB), trait_bonus(Tr,TB).

trait_bonus(Tr,1) :- cautious_trait(Tr).
trait_bonus(Tr,0) :- trait(Tr), not cautious_trait(Tr).

can_succeed(H,M,Tr) :- safe_helper(H), safe_method(M), ready_score(H,M,Tr,S), min_ready(MR), S >= MR.

scenario_valid :- chosen_theme(T), chosen_helper(H), chosen_method(M), chosen_trait(Tr), valid(T,H,M), can_succeed(H,M,Tr).
outcome(success) :- scenario_valid.
outcome(fail) :- not scenario_valid.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("safety", hid, helper.safety))
        lines.append(asp.fact("helper_brave", hid, helper.brave_bonus))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_ready", mid, method.ready_bonus))
        lines.append(asp.fact("method_balance", mid, method.balance_bonus))
        if method.safe:
            lines.append(asp.fact("safe_method", mid))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("min_ready", MIN_READY))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_theme", params.theme),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "fail"


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    method = METHODS[params.method]
    return "success" if can_succeed(helper, method, params.trait) else "fail"


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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly at seed {seed}")
            break
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child finds bravery on an escalator in a space-adventure mood."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--age", type=int, choices=[3, 4, 5, 6])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.method:
        helper = HELPERS[args.helper]
        method = METHODS[args.method]
        if not can_succeed(helper, method, args.trait or "careful"):
            raise StoryError(explain_rejection(helper, method))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.helper is None or combo[1] == args.helper)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, helper_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or {
        "parent": "Mom" if gender == "girl" else "Dad",
        "sibling": rng.choice(["Maya", "Ruby", "Finn", "Theo"]),
        "worker": rng.choice(["Nina", "Alex", "Joy"]),
    }[helper_id]
    trait = args.trait or rng.choice(TRAITS)
    age = args.age if args.age is not None else rng.choice([4, 5])
    params = StoryParams(
        theme=theme,
        helper=helper_id,
        method=method_id,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        trait=trait,
        age=age,
    )
    if outcome_of(params) != "success":
        raise StoryError("(Internal error: resolve_params selected an invalid scenario.)")
    return params


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"Unknown theme: {params.theme}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.method not in METHODS:
        raise StoryError(f"Unknown method: {params.method}")
    helper = HELPERS[params.helper]
    method = METHODS[params.method]
    if not can_succeed(helper, method, params.trait):
        raise StoryError(explain_rejection(helper, method))
    world = tell(
        theme=THEMES[params.theme],
        helper=helper,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        trait=params.trait,
        age=params.age,
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
        print(f"{len(combos)} compatible (theme, helper, method) combos:\n")
        for theme, helper, method in combos:
            print(f"  {theme:8} {helper:8} {method}")
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
            header = f"### {p.child_name}: {p.theme}, {p.helper}, {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
