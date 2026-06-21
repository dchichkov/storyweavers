#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tangible_potassium_lesson_learned_inner_monologue_nursery.py
=======================================================================================

A standalone story world in a gentle nursery-rhyme style: a child spies a
potassium-rich snack on a shelf, reaches for it the wrong way, thinks an inner
thought, and learns a simple lesson about asking for help and using something
steady.

The world is deliberately small and classical:

- typed entities with physical meters and emotional memes
- a reasonableness gate over shelf height, risky reach method, and safe fix
- a state-driven story with two plausible outcomes:
    * paused: the child stops after the inner monologue and asks for help
    * tumbled: the child tries anyway, the snack tumbles, and a grown-up helps
- an inline ASP twin for the compatibility gate and outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/tangible_potassium_lesson_learned_inner_monologue_nursery.py
    python storyworlds/worlds/gpt-5.4/tangible_potassium_lesson_learned_inner_monologue_nursery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/tangible_potassium_lesson_learned_inner_monologue_nursery.py --all --qa
    python storyworlds/worlds/gpt-5.4/tangible_potassium_lesson_learned_inner_monologue_nursery.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CAREFUL_TRAITS = {"careful", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    amount: str
    potassium_line: str
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
class Shelf:
    id: str
    label: str
    level: int
    line: str
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
class Method:
    id: str
    label: str
    phrase: str
    boost: int
    risk: int
    wobble_line: str
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
class Fix:
    id: str
    label: str
    phrase: str
    reach: int
    sense: int
    line: str
    qa_line: str
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


def _r_wobble(world: World) -> list[str]:
    child = world.entities.get("child")
    room = world.entities.get("room")
    if child is None or room is None:
        return []
    if child.meters["wobble"] < THRESHOLD:
        return []
    sig = ("wobble", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    room.meters["noise"] += 1
    return []


def _r_spill(world: World) -> list[str]:
    child = world.entities.get("child")
    snack = world.entities.get("snack")
    if child is None or snack is None:
        return []
    if snack.meters["falling"] < THRESHOLD:
        return []
    sig = ("spill", "snack")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    snack.meters["spilled"] += 1
    snack.meters["bruised"] += 1
    child.memes["guilt"] += 1
    child.memes["fear"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def child_reach() -> int:
    return 1


def can_attempt(shelf: Shelf, method: Method) -> bool:
    return child_reach() + method.boost >= shelf.level


def hazard_at_risk(shelf: Shelf, method: Method) -> bool:
    return shelf.level > child_reach() and method.risk >= 1 and can_attempt(shelf, method)


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def fix_works(shelf: Shelf, fix: Fix) -> bool:
    return fix.reach >= shelf.level


def would_pause(trait: str, method: Method) -> bool:
    return trait in CAREFUL_TRAITS and method.risk >= 2


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    if would_pause(params.trait, method):
        return "paused"
    return "tumbled"


def predict_attempt(world: World, method_id: str) -> dict:
    sim = world.copy()
    child = sim.get("child")
    snack = sim.get("snack")
    method = METHODS[method_id]
    child.meters["wobble"] += float(method.risk)
    if method.risk >= 2:
        snack.meters["falling"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": child.meters["wobble"],
        "spill": snack.meters["spilled"],
        "fear": child.memes["fear"],
    }


def setup(world: World, child: Entity, toy: Entity, snack: Snack, shelf: Shelf) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In the hummy kitchen, {child.id} sang to {toy.label},"
        f" \"Clink and clatter, cup and spoon, we shall have a picnic soon.\""
    )
    world.say(
        f"Then {child.pronoun()} saw {snack.phrase} on {shelf.line}. "
        f"It looked like a tangible treat, not make-believe at all."
    )


def want(world: World, child: Entity, snack: Snack) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{child.id} patted {child.pronoun('possessive')} tummy and smiled a little smile. "
        f"{snack.amount.capitalize()} would make the game a feast."
    )


def inner_monologue(world: World, child: Entity, snack: Snack, method: Method) -> None:
    pred = predict_attempt(world, method.id)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_spill"] = pred["spill"]
    child.memes["thinking"] += 1
    world.say(
        f'Inside {child.pronoun("possessive")} head came a whispery rhyme: '
        f'"If I use {method.phrase}, will bump and wobble come in time?"'
    )
    world.say(
        f'Then came another thought, soft and bright: "{snack.potassium_line} '
        f'But a snack is no delight if I tumble in my hurry."'
    )


def choose_method(world: World, child: Entity, method: Method) -> None:
    child.memes["impulse"] += 1
    world.say(
        f"Still, the shelf looked tall, and {method.phrase} looked near. "
        f"The quick idea felt bold for one small beat."
    )


def pause_and_call(world: World, child: Entity, adult: Entity, fix: Fix) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} stopped {child.pronoun('possessive')} feet and whispered, "
        f"\"No hasty hop, no shaky cheer. I will ask {adult.label_word} who is near.\""
    )
    world.say(
        f"{adult.label_word.capitalize()} came with {fix.phrase}, and the kitchen felt calm again."
    )


def try_and_tumble(world: World, child: Entity, snack_ent: Entity, method: Method) -> None:
    child.meters["wobble"] += float(method.risk)
    if method.risk >= 2:
        snack_ent.meters["falling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} tried {method.phrase}. {method.wobble_line}"
    )
    if snack_ent.meters["spilled"] >= THRESHOLD:
        world.say(
            f"Down came the snack with a patter-plop sound, and one soft piece rolled round and round."
        )


def adult_helps(world: World, child: Entity, adult: Entity, snack: Snack, shelf: Shelf, fix: Fix) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    adult.memes["care"] += 1
    world.say(
        f"{adult.label_word.capitalize()} hurried in, not cross and not loud, "
        f"and gathered the scattered pieces from the floor."
    )
    world.say(
        f'"Let us try the steady way," {adult.pronoun()} said. '
        f"With {fix.phrase}, {adult.pronoun()} reached {shelf.label} and brought down {snack.phrase}."
    )


def share_and_end(world: World, child: Entity, adult: Entity, toy: Entity, snack: Snack, fix: Fix, outcome: str) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    world.say(
        f"Soon the picnic cloth was smooth, the cup was snug, and {toy.label} sat ready for a crumb."
    )
    if outcome == "paused":
        world.say(
            f"{child.id} held {snack.label} in both hands and grinned. "
            f'"A steady plan brings a sweeter bite," {child.pronoun()} sang.'
        )
    else:
        world.say(
            f"{child.id} took the snack gently this time and grinned a shy grin. "
            f'"A rushed little reach makes a muddly plight, but a steady plan sets it right," '
            f'{child.pronoun()} sang.'
        )
    world.say(
        f"And so they munched and hummed till noon: ask for help, use something steady, and good things come quite soon."
    )


SNACKS = {
    "banana": Snack(
        id="banana",
        label="banana",
        phrase="a yellow banana",
        amount="one yellow banana",
        potassium_line="Bananas have potassium to help a body grow strong.",
        tags={"banana", "potassium"},
    ),
    "banana_slices": Snack(
        id="banana_slices",
        label="banana slices",
        phrase="a little bowl of banana slices",
        amount="that little bowl of banana slices",
        potassium_line="Banana slices still carry potassium, a strong-body word.",
        tags={"banana", "potassium"},
    ),
    "apricots": Snack(
        id="apricots",
        label="dried apricots",
        phrase="a small bowl of dried apricots",
        amount="that small bowl of dried apricots",
        potassium_line="Apricots can bring potassium too, though they sat just as high.",
        tags={"apricot", "potassium"},
    ),
}

SHELVES = {
    "middle": Shelf(
        id="middle",
        label="the middle pantry shelf",
        level=2,
        line="the middle pantry shelf by the blue mixing bowl",
        tags={"shelf"},
    ),
    "high": Shelf(
        id="high",
        label="the high pantry shelf",
        level=3,
        line="the high pantry shelf above the cookie tin",
        tags={"shelf"},
    ),
}

METHODS = {
    "rolling_chair": Method(
        id="rolling_chair",
        label="rolling chair",
        phrase="the rolling chair",
        boost=2,
        risk=3,
        wobble_line="The wheels gave a tiny skitter, then a bigger wobble.",
        tags={"chair", "unsafe"},
    ),
    "wobbly_box": Method(
        id="wobbly_box",
        label="wobbly box",
        phrase="the wobbly box",
        boost=2,
        risk=2,
        wobble_line="The cardboard sighed and bent with a wriggly wobble.",
        tags={"box", "unsafe"},
    ),
    "tiptoes": Method(
        id="tiptoes",
        label="tiptoes",
        phrase="tiptoes on one foot and then the other",
        boost=1,
        risk=1,
        wobble_line="The reach was long, the stretch was thin, and the bowl gave a little shift.",
        tags={"stretch", "unsafe"},
    ),
}

FIXES = {
    "ask_adult": Fix(
        id="ask_adult",
        label="ask a grown-up",
        phrase="a grown-up's steady hands",
        reach=3,
        sense=3,
        line="asked a grown-up for help",
        qa_line="asked a grown-up to reach the snack safely",
        tags={"adult_help", "safe"},
    ),
    "step_stool": Fix(
        id="step_stool",
        label="step stool",
        phrase="the small step stool with rubber feet",
        reach=3,
        sense=3,
        line="used a step stool with rubber feet",
        qa_line="used a steady step stool with rubber feet",
        tags={"step_stool", "safe"},
    ),
    "wooden_crate": Fix(
        id="wooden_crate",
        label="wooden crate",
        phrase="the old wooden crate",
        reach=2,
        sense=1,
        line="used an old wooden crate",
        qa_line="used an old wooden crate",
        tags={"crate"},
    ),
}

GIRL_NAMES = ["Molly", "Daisy", "Lulu", "Tess", "Nina", "Poppy", "Ruby", "Maisie"]
BOY_NAMES = ["Ned", "Toby", "Ollie", "Finn", "Milo", "Benny", "Jasper", "Theo"]
TOYS = ["a cloth rabbit", "a sleepy bear", "a tin duck", "a patchwork mouse"]
TRAITS = ["careful", "patient", "thoughtful", "curious", "bouncy", "hasty"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for shelf_id, shelf in SHELVES.items():
        for method_id, method in METHODS.items():
            if not hazard_at_risk(shelf, method):
                continue
            for fix_id, fix in FIXES.items():
                if fix.sense >= SENSE_MIN and fix_works(shelf, fix):
                    combos.append((shelf_id, method_id, fix_id))
    return combos


@dataclass
class StoryParams:
    snack: str
    shelf: str
    method: str
    fix: str
    name: str
    gender: str
    parent: str
    trait: str
    toy: str
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "banana": [
        (
            "Why do bananas make a handy snack?",
            "Bananas are soft, easy to hold, and easy to eat, so they make a simple snack for children. They also give the body energy."
        )
    ],
    "apricot": [
        (
            "What are dried apricots?",
            "Dried apricots are apricots with much of the water taken out. They are chewy and sweet, so grown-ups often serve only a little bowl."
        )
    ],
    "potassium": [
        (
            "What is potassium?",
            "Potassium is something in food that helps muscles and nerves do their jobs well. Children do not need to measure it; they just need a good mix of healthy foods."
        )
    ],
    "adult_help": [
        (
            "Why is it smart to ask a grown-up for help with a high shelf?",
            "A grown-up can reach higher and keep things steady. Asking for help can stop a fall before it starts."
        )
    ],
    "step_stool": [
        (
            "What makes a step stool safer than a rolling chair?",
            "A step stool is made for standing and usually stays still on the floor. A rolling chair can slide away when someone climbs on it."
        )
    ],
    "chair": [
        (
            "Why can a rolling chair be unsafe to stand on?",
            "Its wheels can move when you do not expect them to. That makes your body wobble and can cause a fall."
        )
    ],
    "box": [
        (
            "Why can a box be wobbly?",
            "A box can bend, squash, or slide if weight shifts on top of it. That makes it poor for climbing."
        )
    ],
}
KNOWLEDGE_ORDER = ["banana", "apricot", "potassium", "adult_help", "step_stool", "chair", "box"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    snack = f["snack_cfg"]
    method = f["method"]
    fix = f["fix"]
    outcome = f["outcome"]
    if outcome == "paused":
        return [
            f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "tangible" and "potassium". A child sees {snack.phrase} on a shelf, thinks an inner thought, and chooses the safe way instead of using {method.phrase}.',
            f"Tell a gentle rhyming story where {child.id} almost uses {method.phrase} to reach a snack, but the child's inner monologue leads to a lesson learned and a calm ending with {fix.label}.",
            f'Write a small musical story with an inner monologue and a clear lesson: quick reaching is risky, but asking for help makes the treat feel sweeter and more tangible.'
        ]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "tangible" and "potassium". A child sees {snack.phrase} on a shelf, tries {method.phrase}, and learns a lesson after the snack tumbles.',
        f"Tell a rhyming story where {child.id} hears an inner warning, ignores it for one moment, and then learns the safe way with {fix.label}.",
        f'Write a gentle cautionary rhyme in which a child wants a tangible snack high up on a shelf, and the ending teaches a lesson about steady choices.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    toy = f["toy"]
    snack = f["snack_cfg"]
    shelf = f["shelf"]
    method = f["method"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {toy.label}, and {child.pronoun('possessive')} {adult.label_word}. They are in the kitchen getting ready for a pretend picnic with a real snack."
        ),
        (
            "What did the child want?",
            f"{child.id} wanted {snack.phrase} from {shelf.label}. The snack felt tangible because it was a real treat the child could actually hold and share."
        ),
        (
            "What was the child's inner monologue about?",
            f"{child.id} wondered whether {method.phrase} would lead to wobbling. The thought also remembered that the snack had potassium, but that a strong snack is no help if you hurry into trouble."
        ),
    ]
    if outcome == "paused":
        qa.append(
            (
                f"Why did {child.id} stop before trying {method.phrase}?",
                f"{child.pronoun().capitalize()} listened to the worried thought inside {child.pronoun('possessive')} head and imagined the wobble first. That inner warning helped {child.pronoun('object')} choose the steadier plan before anything fell."
            )
        )
        qa.append(
            (
                f"How did {child.id}'s {adult.label_word} help?",
                f"{adult.label_word.capitalize()} came with {fix.phrase} and got the snack down safely. The help worked because the fix was steady and high enough for the shelf."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child.id} tried {method.phrase}?",
                f"The reach turned wobbly, and the snack tumbled down with a little clatter. That happened because the quick method was not steady enough for the high shelf."
            )
        )
        qa.append(
            (
                f"Was {child.id}'s {adult.label_word} angry?",
                f"No. {adult.label_word.capitalize()} stayed calm, helped pick up the snack, and showed the safer way instead. The lesson came with comfort, not scolding."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned that hurried reaching can make a bigger mess, but a steady plan keeps everyone safe. Asking for help or using {fix.label} turned the picnic bright again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["snack_cfg"].tags) | set(f["method"].tags) | set(f["fix"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {entity.id:8} ({entity.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def tell(
    snack: Snack,
    shelf: Shelf,
    method: Method,
    fix: Fix,
    name: str = "Molly",
    gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    toy_label: str = "a cloth rabbit",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            role="child",
            traits=[trait],
            attrs={"toy": toy_label},
        )
    )
    adult = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="adult",
            attrs={"nearby": True},
        )
    )
    toy = world.add(
        Entity(
            id="toy",
            type="toy",
            label=toy_label,
            phrase=toy_label,
            role="toy",
        )
    )
    snack_ent = world.add(
        Entity(
            id="snack",
            type="snack",
            label=snack.label,
            phrase=snack.phrase,
            role="snack",
            attrs={"potassium": True},
        )
    )
    world.add(Entity(id="room", type="room", label="the kitchen", role="room"))

    setup(world, child, toy, snack, shelf)
    want(world, child, snack)

    world.para()
    inner_monologue(world, child, snack, method)
    choose_method(world, child, method)

    paused = would_pause(trait, method)
    world.para()
    if paused:
        pause_and_call(world, child, adult, fix)
        outcome = "paused"
    else:
        try_and_tumble(world, child, snack_ent, method)
        adult_helps(world, child, adult, snack, shelf, fix)
        outcome = "tumbled"

    world.para()
    share_and_end(world, child, adult, toy, snack, fix, outcome)

    world.facts.update(
        child=child,
        adult=adult,
        toy=toy,
        snack_cfg=snack,
        shelf=shelf,
        method=method,
        fix=fix,
        outcome=outcome,
        tumbled=snack_ent.meters["spilled"] >= THRESHOLD,
        predicted_wobble=world.facts.get("predicted_wobble", 0),
        predicted_spill=world.facts.get("predicted_spill", 0),
    )
    return world


CURATED = [
    StoryParams(
        snack="banana",
        shelf="high",
        method="rolling_chair",
        fix="ask_adult",
        name="Molly",
        gender="girl",
        parent="mother",
        trait="careful",
        toy="a cloth rabbit",
    ),
    StoryParams(
        snack="banana_slices",
        shelf="middle",
        method="wobbly_box",
        fix="step_stool",
        name="Ned",
        gender="boy",
        parent="father",
        trait="curious",
        toy="a sleepy bear",
    ),
    StoryParams(
        snack="apricots",
        shelf="middle",
        method="tiptoes",
        fix="ask_adult",
        name="Daisy",
        gender="girl",
        parent="mother",
        trait="patient",
        toy="a tin duck",
    ),
    StoryParams(
        snack="banana",
        shelf="high",
        method="wobbly_box",
        fix="step_stool",
        name="Theo",
        gender="boy",
        parent="father",
        trait="hasty",
        toy="a patchwork mouse",
    ),
]


def explain_rejection(shelf: Shelf, method: Method, fix: Optional[Fix] = None) -> str:
    if not can_attempt(shelf, method):
        return (
            f"(No story: {method.phrase} would not even reach {shelf.label}. "
            f"The child needs a tempting but plausible unsafe try before the lesson.)"
        )
    if not hazard_at_risk(shelf, method):
        return (
            f"(No story: {method.phrase} is not risky enough for {shelf.label}, "
            f"so there is no honest wobble or lesson here.)"
        )
    if fix is not None and fix.sense < SENSE_MIN:
        return (
            f"(No story: {fix.label} is too weak a fix for this world. "
            f"Choose a steadier solution like ask_adult or step_stool.)"
        )
    if fix is not None and not fix_works(shelf, fix):
        return (
            f"(No story: {fix.label} cannot reach {shelf.label}. "
            f"The repair must actually solve the problem.)"
        )
    return "(No story: this combination is unreasonable.)"


ASP_RULES = r"""
% compatibility gate
hazard(S, M) :- shelf(S), method(M), shelf_level(S, L), child_reach(C), L > C,
                boost(M, B), C + B >= L, risk(M, R), R >= 1.
sensible(F) :- fix(F), sense(F, S), sense_min(Min), S >= Min.
works(S, F) :- shelf(S), fix(F), shelf_level(S, L), fix_reach(F, R), R >= L.
valid(S, M, F) :- hazard(S, M), sensible(F), works(S, F).

% outcome model
careful_trait(T) :- trait_name(T), careful(T).
paused :- chosen_method(M), chosen_trait(T), careful_trait(T), risk(M, R), R >= 2.
outcome(paused) :- paused.
outcome(tumbled) :- not paused.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("child_reach", child_reach()), asp.fact("sense_min", SENSE_MIN)]
    for shelf_id, shelf in SHELVES.items():
        lines.append(asp.fact("shelf", shelf_id))
        lines.append(asp.fact("shelf_level", shelf_id, shelf.level))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("boost", method_id, method.boost))
        lines.append(asp.fact("risk", method_id, method.risk))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_reach", fix_id, fix.reach))
        lines.append(asp.fact("sense", fix_id, fix.sense))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
        if trait in CAREFUL_TRAITS:
            lines.append(asp.fact("careful", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a child reaches for a potassium-rich snack, thinks a little thought, and learns a steady lesson."
    )
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--shelf", choices=SHELVES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (shelf, method, fix) triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shelf is not None and args.method is not None:
        shelf = SHELVES[args.shelf]
        method = METHODS[args.method]
        if not hazard_at_risk(shelf, method):
            raise StoryError(explain_rejection(shelf, method))
    if args.fix is not None:
        fix = FIXES[args.fix]
        if fix.sense < SENSE_MIN:
            shelf = SHELVES[args.shelf] if args.shelf else next(iter(SHELVES.values()))
            method = METHODS[args.method] if args.method else next(iter(METHODS.values()))
            raise StoryError(explain_rejection(shelf, method, fix))
    if args.shelf is not None and args.fix is not None:
        shelf = SHELVES[args.shelf]
        fix = FIXES[args.fix]
        if not fix_works(shelf, fix):
            method = METHODS[args.method] if args.method else next(iter(METHODS.values()))
            raise StoryError(explain_rejection(shelf, method, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.shelf is None or combo[0] == args.shelf)
        and (args.method is None or combo[1] == args.method)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shelf_id, method_id, fix_id = rng.choice(sorted(combos))
    snack_id = args.snack or rng.choice(sorted(SNACKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    toy = rng.choice(TOYS)
    return StoryParams(
        snack=snack_id,
        shelf=shelf_id,
        method=method_id,
        fix=fix_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        toy=toy,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        snack = SNACKS[params.snack]
        shelf = SHELVES[params.shelf]
        method = METHODS[params.method]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(No story: unknown option {err.args[0]!r}.)") from None

    if not hazard_at_risk(shelf, method):
        raise StoryError(explain_rejection(shelf, method))
    if fix.sense < SENSE_MIN or not fix_works(shelf, fix):
        raise StoryError(explain_rejection(shelf, method, fix))
    if params.gender not in {"girl", "boy"}:
        raise StoryError("(No story: gender must be 'girl' or 'boy'.)")
    if not params.name:
        raise StoryError("(No story: name must not be empty.)")

    world = tell(
        snack=snack,
        shelf=shelf,
        method=method,
        fix=fix,
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
        toy_label=params.toy,
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
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("empty story from smoke test")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(smoke_sample, trace=False, qa=True, header="### smoke")
        out = buf.getvalue()
        if "potassium" not in smoke_sample.story:
            raise StoryError("smoke story did not include 'potassium'")
        if "tangible" not in smoke_sample.story:
            raise StoryError("smoke story did not include 'tangible'")
        if "### smoke" not in out:
            raise StoryError("emit() smoke test did not print header")
        print("OK: smoke-tested generate() and emit().")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shelf, method, fix) combos:\n")
        for shelf_id, method_id, fix_id in combos:
            print(f"  {shelf_id:7} {method_id:14} {fix_id}")
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
            header = f"### {p.name}: {p.snack} on {p.shelf} via {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
