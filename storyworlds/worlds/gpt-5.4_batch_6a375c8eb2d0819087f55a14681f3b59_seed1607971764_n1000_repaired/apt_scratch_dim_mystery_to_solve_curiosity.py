#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/apt_scratch_dim_mystery_to_solve_curiosity.py
========================================================================

A standalone story world about a child in a small apt who hears a strange
scratch-dim sound and wants to know what is making it. The mystery is solved by
stateful clues, patience, and a sensible grown-up helper.

The stories aim for a gentle fable shape:
- a curious beginning
- a tense middle where the unknown feels bigger than it is
- a calm solving turn
- an ending image that shows how curiosity changed into wiser curiosity

Run it
------
    python storyworlds/worlds/gpt-5.4/apt_scratch_dim_mystery_to_solve_curiosity.py
    python storyworlds/worlds/gpt-5.4/apt_scratch_dim_mystery_to_solve_curiosity.py --nook coat_closet --cause kitten
    python storyworlds/worlds/gpt-5.4/apt_scratch_dim_mystery_to_solve_curiosity.py --method yank_broom
    python storyworlds/worlds/gpt-5.4/apt_scratch_dim_mystery_to_solve_curiosity.py --all
    python storyworlds/worlds/gpt-5.4/apt_scratch_dim_mystery_to_solve_curiosity.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/apt_scratch_dim_mystery_to_solve_curiosity.py --verify
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
SENSE_MIN = 2
STEADY_TRAITS = {"patient", "careful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    alive: bool = False
    hidden: bool = False
    movable: bool = False
    gives_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "neighbor_woman"}
        male = {"boy", "father", "man", "neighbor_man", "super"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "neighbor_woman": "neighbor",
            "neighbor_man": "neighbor",
            "super": "super",
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
class Nook:
    id: str
    label: str
    phrase: str
    dark_line: str
    clutter: str
    open_text: str
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
class Cause:
    id: str
    label: str
    type: str
    sound: str
    reveal: str
    ending_image: str
    creature: bool = False
    needs_wait: bool = False
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
    sense: int
    works_for: set[str]
    text: str
    reveal_text: str
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


def _r_mystery_signal(world: World) -> list[str]:
    child = world.get("child")
    nook = world.get("nook")
    cause = world.get("cause")
    if cause.meters["noise"] < THRESHOLD or nook.meters["dark"] < THRESHOLD:
        return []
    sig = ("mystery", cause.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["fear"] += 1
    world.get("apt").meters["mystery"] += 1
    return ["__mystery__"]


def _r_ask_help(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["asked_help"] < THRESHOLD:
        return []
    sig = ("trust", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["trust"] += 1
    helper.memes["care"] += 1
    return []


def _r_reveal_relief(world: World) -> list[str]:
    child = world.get("child")
    cause = world.get("cause")
    if cause.hidden or cause.meters["seen"] < THRESHOLD:
        return []
    sig = ("relief", cause.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    child.memes["wonder"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mystery_signal", tag="emotion", apply=_r_mystery_signal),
    Rule(name="ask_help", tag="social", apply=_r_ask_help),
    Rule(name="reveal_relief", tag="emotion", apply=_r_reveal_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def cause_fits(cause: Cause, nook: Nook) -> bool:
    return nook.id in ALLOWED_NOOKS[cause.id]


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_works(method: Method, cause: Cause) -> bool:
    return cause.id in method.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for nook_id, nook in NOOKS.items():
        for cause_id, cause in CAUSES.items():
            if not cause_fits(cause, nook):
                continue
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and method_works(method, cause):
                    combos.append((nook_id, cause_id, method_id))
    return combos


def is_steady(trait: str) -> bool:
    return trait in STEADY_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "steady_solve" if is_steady(params.trait) else "startled_solve"


def predict_identity(world: World, method: Method) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["asked_help"] += 1
    propagate(sim, narrate=False)
    reveal(sim, METHODS[method.id], narrate=False)
    cause = sim.get("cause")
    return {
        "solved": cause.meters["seen"] >= THRESHOLD,
        "label": cause.label,
    }


def introduce(world: World, child: Entity, nook_cfg: Nook) -> None:
    world.say(
        f"In a small apt at the end of a long hall, {child.id} liked to notice little things."
    )
    world.say(
        f"That evening the lamp by {nook_cfg.phrase} was low, and the corner looked {nook_cfg.dark_line}."
    )


def hear_sound(world: World, child: Entity, nook_cfg: Nook, cause_cfg: Cause) -> None:
    world.get("cause").meters["noise"] += 1
    world.get("nook").meters["dark"] += 1
    propagate(world, narrate=False)
    world.say(
        f"From {nook_cfg.phrase} came {cause_cfg.sound}, a scratch-dim little sound that seemed to hide behind {nook_cfg.clutter}."
    )
    world.say(
        f"{child.id} stopped in the hall and listened. Curiosity pulled one way, and a tiny shiver pulled the other."
    )


def lean_close(world: World, child: Entity, nook_cfg: Nook) -> None:
    child.memes["investigate"] += 1
    world.say(
        f"{child.pronoun().capitalize()} took two soft steps closer to {nook_cfg.phrase} and wondered whether the dark held a secret or only a mistake."
    )


def first_guess(world: World, child: Entity) -> None:
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"For one breath {child.id} imagined something much bigger than the truth, because unknown sounds often grow large in a child's mind."
        )
    else:
        world.say(
            f"{child.id} almost smiled, because a puzzle had begun to bloom where the hallway had been ordinary before."
        )


def touch_or_pause(world: World, child: Entity, nook_cfg: Nook, steady: bool) -> None:
    if steady:
        child.memes["patience"] += 1
        world.say(
            f"{child.id} did not fling {nook_cfg.open_text} open. {child.pronoun().capitalize()} laid one hand on the handle, then remembered that patient curiosity sees better than hurried curiosity."
        )
    else:
        child.memes["startle"] += 1
        child.memes["fear"] += 1
        world.get("cause").meters["noise"] += 1
        world.say(
            f"{child.id} gave {nook_cfg.open_text} a quick tug. Inside, the hidden thing bumped and rustled louder, and the hall suddenly felt smaller than before."
        )


def call_helper(world: World, child: Entity, helper: Entity) -> None:
    child.memes["asked_help"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{helper.label_word.capitalize()}, will you come listen?" {child.id} called. {helper.label_word.capitalize()} came with calm steps instead of hurrying steps, and that calm changed the whole hall.'
    )


def helper_reason(world: World, helper: Entity, nook_cfg: Nook, method: Method) -> None:
    pred = predict_identity(world, method)
    world.facts["predicted_identity"] = pred["label"]
    world.say(
        f'{helper.label_word.capitalize()} bent close to {nook_cfg.phrase} and listened too. "A true mystery is not a race," {helper.pronoun()} said. "First we look gently, and then the answer can come out by itself."'
    )


def reveal(world: World, method: Method, narrate: bool = True) -> None:
    cause = world.get("cause")
    cause.hidden = False
    cause.meters["seen"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(method.reveal_text.replace("{reveal}", world.facts["cause_cfg"].reveal))


def solve(world: World, helper: Entity, method: Method) -> None:
    world.say(
        f"{helper.label_word.capitalize()} {method.text}"
    )
    reveal(world, method, narrate=True)


def lesson(world: World, child: Entity, helper: Entity, cause_cfg: Cause) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'{helper.label_word.capitalize()} smiled at {child.id}. "Curiosity is a bright lantern," {helper.pronoun()} said, "but it shines best when patience carries it."'
    )
    if cause_cfg.creature:
        world.say(
            f"{child.id} nodded and moved more softly than before, because the small mystery had turned out to have a small heartbeat."
        )
    else:
        world.say(
            f"{child.id} nodded and laughed a little, because the great dark question had turned out to be a little object with a silly job."
        )


def ending(world: World, child: Entity, nook_cfg: Nook, cause_cfg: Cause) -> None:
    world.say(
        f"After that, {nook_cfg.phrase} no longer felt gloomy. {cause_cfg.ending_image}"
    )
    world.say(
        f"And whenever {child.id} heard a strange sound in the apt again, {child.pronoun()} remembered that wonder grows wiser when it walks beside patience."
    )


def tell(
    nook_cfg: Nook,
    cause_cfg: Cause,
    method: Method,
    child_name: str = "Nell",
    child_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "patient",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
        )
    )
    world.add(
        Entity(
            id="apt",
            type="apt",
            label="the apt",
            meters=defaultdict(float, {"mystery": 0.0}),
            memes=defaultdict(float),
        )
    )
    world.add(
        Entity(
            id="nook",
            type="nook",
            label=nook_cfg.label,
            hidden=False,
        )
    )
    world.add(
        Entity(
            id="cause",
            type=cause_cfg.type,
            label=cause_cfg.label,
            alive=cause_cfg.creature,
            hidden=True,
            movable=True,
        )
    )

    child.memes["curiosity"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["lesson"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["asked_help"] = 0.0
    child.memes["investigate"] = 0.0
    child.memes["startle"] = 0.0
    child.memes["patience"] = 1.0 if is_steady(trait) else 0.0
    helper.memes["care"] = 0.0

    world.facts.update(
        child=child,
        helper=helper,
        nook_cfg=nook_cfg,
        cause_cfg=cause_cfg,
        method=method,
        outcome="",
    )

    introduce(world, child, nook_cfg)
    hear_sound(world, child, nook_cfg, cause_cfg)
    lean_close(world, child, nook_cfg)
    world.para()
    first_guess(world, child)
    steady = is_steady(trait)
    touch_or_pause(world, child, nook_cfg, steady)
    call_helper(world, child, helper)
    helper_reason(world, helper, nook_cfg, method)
    world.para()
    solve(world, helper, method)
    lesson(world, child, helper, cause_cfg)
    world.para()
    ending(world, child, nook_cfg, cause_cfg)

    world.facts["outcome"] = "steady_solve" if steady else "startled_solve"
    world.facts["solved"] = world.get("cause").meters["seen"] >= THRESHOLD
    world.facts["steady"] = steady
    return world


NOOKS = {
    "coat_closet": Nook(
        id="coat_closet",
        label="coat closet",
        phrase="the coat closet",
        dark_line="like a folded piece of night",
        clutter="winter sleeves and a stack of shoe boxes",
        open_text="the closet door",
        tags={"closet", "home"},
    ),
    "pantry": Nook(
        id="pantry",
        label="pantry",
        phrase="the pantry door",
        dark_line="shadowy between the flour tin and the broom",
        clutter="paper sacks and tall jars",
        open_text="the pantry door",
        tags={"pantry", "home"},
    ),
    "laundry_nook": Nook(
        id="laundry_nook",
        label="laundry nook",
        phrase="the laundry nook",
        dark_line="soft and dim behind the hanging towels",
        clutter="a basket of warm clothes and one tipped slipper",
        open_text="the folding screen",
        tags={"laundry", "home"},
    ),
}

CAUSES = {
    "kitten": Cause(
        id="kitten",
        label="a lost kitten",
        type="kitten",
        sound="a tiny scrape and a shy mew",
        reveal="A dusty gray kitten blinked from behind the coats.",
        ending_image="Soon a saucer stood on the floor, and the kitten purred under the lamp as if the place had always been meant for warmth.",
        creature=True,
        needs_wait=True,
        tags={"kitten", "animal", "sound"},
    ),
    "toy_bug": Cause(
        id="toy_bug",
        label="a wind-up toy bug",
        type="toy",
        sound="a scratch-dim whirr and tick",
        reveal="A bright tin bug with a crooked wheel buzzed out and bumped the baseboard.",
        ending_image="Soon the little toy bug clicked across the rug in plain sight, and nobody mistook it for a monster again.",
        creature=False,
        needs_wait=False,
        tags={"toy", "machine", "sound"},
    ),
}

ALLOWED_NOOKS = {
    "kitten": {"coat_closet", "laundry_nook"},
    "toy_bug": {"pantry", "laundry_nook"},
}

METHODS = {
    "flashlight_and_bowl": Method(
        id="flashlight_and_bowl",
        sense=3,
        works_for={"kitten"},
        text="set down a saucer of water, lifted a flashlight low instead of high, and waited without any grabbing",
        reveal_text="{reveal} The answer came because quiet made room for it.",
        qa_text="used a low flashlight and waited with a little saucer so the hidden kitten could come out safely",
        tags={"flashlight", "patience", "animal"},
    ),
    "listen_and_lift": Method(
        id="listen_and_lift",
        sense=3,
        works_for={"toy_bug"},
        text="held the flashlight steady, listened for the tick, and lifted one paper sack at a time",
        reveal_text="{reveal} Once the clutter moved gently, the mystery stopped pretending to be enormous.",
        qa_text="listened for the ticking and lifted the paper sacks gently until the toy bug was found",
        tags={"flashlight", "listening", "toy"},
    ),
    "yank_broom": Method(
        id="yank_broom",
        sense=1,
        works_for=set(),
        text="jabbed a broom into the dark corner at once",
        reveal_text="{reveal}",
        qa_text="jabbed with a broom",
        tags={"rough"},
    ),
}


GIRL_NAMES = ["Nell", "Mira", "Lina", "Tess", "Rosa", "June", "Ivy", "Mina"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Nico", "Jules", "Finn", "Evan", "Luca"]
TRAITS = ["patient", "careful", "gentle", "eager", "bold", "restless"]


@dataclass
class StoryParams:
    nook: str
    cause: str
    method: str
    child_name: str
    child_gender: str
    helper: str
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


KNOWLEDGE = {
    "apt": [
        (
            "What is an apt?",
            "An apt is a short way to say apartment. It is a home inside a bigger building where other people may live nearby too.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the wish to know more about something. It can help you learn, especially when you stay calm and ask for help when you need it.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in a dark place?",
            "A flashlight helps you see what is really there. It can turn a scary guess into a clear answer without using anything hot or dangerous.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten hide in a dark place?",
            "A kitten may hide when it feels lost or scared. Dark little spaces can feel safe to a small animal until a gentle person helps it.",
        )
    ],
    "toy": [
        (
            "What is a wind-up toy?",
            "A wind-up toy is a toy that moves when a spring inside it is wound up. It can click, buzz, or tick as it goes.",
        )
    ],
    "patience": [
        (
            "Why does patience help solve a mystery?",
            "Patience slows you down enough to notice clues. When you rush, you may only hear your own worry instead of the true answer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["apt", "curiosity", "flashlight", "kitten", "toy", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    nook = f["nook_cfg"]
    cause = f["cause_cfg"]
    return [
        f'Write a short fable-style story for a 3-to-5-year-old about a child in an apt who hears a scratch-dim sound near {nook.phrase} and wants to solve the mystery.',
        f"Tell a gentle mystery where {child.label}, helped by {child.pronoun('possessive')} {helper.label_word}, learns that curiosity needs patience before it finds the truth.",
        f'Write a child-facing story that includes the words "apt" and "scratch-dim" and ends with the hidden cause turning out to be {cause.label}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    nook = f["nook_cfg"]
    cause = f["cause_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a curious child in a small apt, and {child.pronoun('possessive')} {helper.label_word} who helps solve a hallway mystery.",
        ),
        (
            "What was the mystery?",
            f"The mystery was the strange sound coming from {nook.phrase}. It sounded bigger than it really was because the place was dark and the cause was still hidden.",
        ),
        (
            f"Why did {child.label} feel two things at once?",
            f"{child.label} felt curious because {child.pronoun()} wanted to know what was making the noise, and {child.pronoun()} also felt scared because unknown sounds can seem larger in the dark. The scratch-dim sound let wonder and worry arrive together.",
        ),
    ]
    if f["steady"]:
        qa.append(
            (
                f"What did {child.label} do before opening {nook.open_text}?",
                f"{child.label} paused instead of rushing. That pause mattered because patient curiosity made room for help and clues instead of making the mystery louder.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child.label} tugged at {nook.open_text}?",
                f"The hidden thing rustled louder, so the hallway felt scarier for a moment. The quick tug did not solve the mystery, but it showed why hurrying can make worry grow.",
            )
        )
    qa.append(
        (
            f"How did {helper.label_word} solve the mystery?",
            f"{helper.label_word.capitalize()} {method.qa_text}. The method matched the clue and kept the hidden thing from being frightened or broken.",
        )
    )
    qa.append(
        (
            "What was making the sound in the end?",
            f"It was {cause.label}. The answer felt gentle once it could be seen, because mysteries often shrink when light and patience reach them.",
        )
    )
    qa.append(
        (
            "What is the lesson of the story?",
            "The lesson is that curiosity is good, but it works best with patience. When you slow down and ask for calm help, the truth can come out safely.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"apt", "curiosity", "patience"}
    tags |= set(f["method"].tags)
    tags |= set(f["cause_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("alive", e.alive), ("hidden", e.hidden), ("movable", e.movable), ("gives_light", e.gives_light)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        nook="coat_closet",
        cause="kitten",
        method="flashlight_and_bowl",
        child_name="Nell",
        child_gender="girl",
        helper="mother",
        trait="patient",
    ),
    StoryParams(
        nook="pantry",
        cause="toy_bug",
        method="listen_and_lift",
        child_name="Theo",
        child_gender="boy",
        helper="father",
        trait="eager",
    ),
    StoryParams(
        nook="laundry_nook",
        cause="kitten",
        method="flashlight_and_bowl",
        child_name="Mira",
        child_gender="girl",
        helper="neighbor_woman",
        trait="gentle",
    ),
    StoryParams(
        nook="laundry_nook",
        cause="toy_bug",
        method="listen_and_lift",
        child_name="Finn",
        child_gender="boy",
        helper="super",
        trait="bold",
    ),
]


def explain_rejection(nook: Nook, cause: Cause, method: Optional[Method] = None) -> str:
    if not cause_fits(cause, nook):
        allowed = ", ".join(sorted(ALLOWED_NOOKS[cause.id]))
        return (
            f"(No story: {cause.label} does not plausibly belong in {nook.phrase} here. "
            f"Try one of these nooks for that cause: {allowed}.)"
        )
    if method is not None and method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method.id}': it is too rough for this gentle mystery world. "
            f"Choose a calmer method such as {better}.)"
        )
    if method is not None and not method_works(method, cause):
        return (
            f"(No story: method '{method.id}' does not reasonably solve the mystery caused by {cause.label}.)"
        )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
fits(C,N) :- allowed(C,N).
sensible(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.
valid(N,C,M) :- nook(N), cause(C), method(M), fits(C,N), sensible(M), works_for(M,C).

steady_solve :- chosen_trait(T), steady_trait(T).
startled_solve :- chosen_trait(T), not steady_trait(T).

outcome(steady_solve) :- steady_solve.
outcome(startled_solve) :- startled_solve.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for nook_id in NOOKS:
        lines.append(asp.fact("nook", nook_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for cause_id, nook_ids in ALLOWED_NOOKS.items():
        for nook_id in sorted(nook_ids):
            lines.append(asp.fact("allowed", cause_id, nook_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for cause_id in sorted(method.works_for):
            lines.append(asp.fact("works_for", method_id, cause_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("steady_trait", trait))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {m.id for m in sensible_methods()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible methods match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible methods: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a scratch-dim mystery in a small apt, solved by calm curiosity."
    )
    ap.add_argument("--nook", choices=NOOKS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=["mother", "father", "neighbor_woman", "neighbor_man", "super"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.nook and args.cause:
        nook = NOOKS[args.nook]
        cause = CAUSES[args.cause]
        if not cause_fits(cause, nook):
            raise StoryError(explain_rejection(nook, cause))
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            nook = NOOKS[args.nook] if args.nook else next(iter(NOOKS.values()))
            cause = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
            raise StoryError(explain_rejection(nook, cause, method))
        if args.cause and not method_works(method, CAUSES[args.cause]):
            nook = NOOKS[args.nook] if args.nook else next(iter(NOOKS.values()))
            raise StoryError(explain_rejection(nook, CAUSES[args.cause], method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.nook is None or combo[0] == args.nook)
        and (args.cause is None or combo[1] == args.cause)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    nook_id, cause_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "neighbor_woman", "neighbor_man", "super"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        nook=nook_id,
        cause=cause_id,
        method=method_id,
        child_name=name,
        child_gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.nook not in NOOKS:
        raise StoryError(f"(Unknown nook: {params.nook})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    nook = NOOKS[params.nook]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]
    if not cause_fits(cause, nook):
        raise StoryError(explain_rejection(nook, cause))
    if method.sense < SENSE_MIN or not method_works(method, cause):
        raise StoryError(explain_rejection(nook, cause, method))

    world = tell(
        nook_cfg=nook,
        cause_cfg=cause,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
        trait=params.trait,
    )
    child = world.get("child")
    child.label = params.child_name

    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (nook, cause, method) combos:\n")
        for nook, cause, method in combos:
            print(f"  {nook:13} {cause:8} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.cause} in {p.nook} ({p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
