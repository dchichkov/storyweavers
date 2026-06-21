#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bazaar_abcdefghijklmnop_moral_value_humor_foreshadowing_rhyming.py
================================================================================================

A standalone story world for a tiny bazaar tale told in a lightly rhyming voice.

Premise
-------
A child in a bazaar is asked to carry something small and important from one
stall to another. The child feels proud and wants to carry it the flashy way.
The world itself decides whether that is silly or sensible: each cargo has a
physical risk, and only some tools truly protect it. A careful child may listen
to good advice before trouble starts; otherwise there is a funny near-spill,
then a lesson, then a safer second try.

Required seed notes folded into the world
-----------------------------------------
* Every story happens in a bazaar.
* Every story includes the string ``abcdefghijklmnop`` as part of a silly
  alphabet banner hanging over the lane.
* The stories aim for moral value (carefulness / listening / responsibility),
  mild humor, foreshadowing, and a child-facing rhyming style.

Run it
------
    python storyworlds/worlds/gpt-5.4/bazaar_abcdefghijklmnop_moral_value_humor_foreshadowing_rhyming.py
    python storyworlds/worlds/gpt-5.4/bazaar_abcdefghijklmnop_moral_value_humor_foreshadowing_rhyming.py --cargo tart --tool box
    python storyworlds/worlds/gpt-5.4/bazaar_abcdefghijklmnop_moral_value_humor_foreshadowing_rhyming.py --cargo banner --tool tray
    python storyworlds/worlds/gpt-5.4/bazaar_abcdefghijklmnop_moral_value_humor_foreshadowing_rhyming.py --all
    python storyworlds/worlds/gpt-5.4/bazaar_abcdefghijklmnop_moral_value_humor_foreshadowing_rhyming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bazaar_abcdefghijklmnop_moral_value_humor_foreshadowing_rhyming.py --verify
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
PRIDE_INIT = 5.0
LISTENING_TRAITS = {"careful", "patient", "thoughtful"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    guards: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "seller_woman"}
        male = {"boy", "father", "man", "uncle", "seller_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
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
    color_line: str
    foreshadow: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    risk: str
    hazard_line: str
    owner_type: str
    destination: str
    nearspill_line: str
    recovery_line: str
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
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    carry_line: str
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
class Helper:
    id: str
    label: str
    kind: str
    bonus: int
    entrance: str
    warning: str
    mishap: str
    ending: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
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
# Causal rules
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


def cargo_protected(world: World, cargo: Entity) -> bool:
    for ent in list(world.entities.values()):
        if ent.type == "tool" and ent.carried_by == cargo.carried_by and ent.protective:
            if world.facts.get("risk") in ent.guards:
                return True
    return False


def _r_unsecured_wobble(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.entities.get("cargo")
    if cargo is None or cargo.carried_by is None:
        return out
    if cargo.meters["delivered"] >= THRESHOLD:
        return out
    if cargo_protected(world, cargo):
        return out
    sig = ("wobble", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["wobble"] += 1
    hero = world.get(cargo.carried_by)
    elder = world.get("elder")
    hero.memes["worry"] += 1
    elder.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_wobble_to_nearspill(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.entities.get("cargo")
    if cargo is None or cargo.meters["wobble"] < THRESHOLD:
        return out
    sig = ("nearspill", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["nearspill"] += 1
    hero = world.get(cargo.carried_by) if cargo.carried_by else world.get("hero")
    hero.memes["alarm"] += 1
    out.append("__nearspill__")
    return out


def _r_returned_relief(world: World) -> list[str]:
    cargo = world.entities.get("cargo")
    if cargo is None or cargo.meters["delivered"] < THRESHOLD:
        return []
    sig = ("relief", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    elder = world.get("elder")
    hero.memes["relief"] += 1
    elder.memes["relief"] += 1
    hero.memes["pride"] = 0.0
    hero.memes["humility"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="unsecured_wobble", tag="physical", apply=_r_unsecured_wobble),
    Rule(name="wobble_to_nearspill", tag="physical", apply=_r_wobble_to_nearspill),
    Rule(name="returned_relief", tag="emotional", apply=_r_returned_relief),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def tool_fits(cargo: Cargo, tool: Tool) -> bool:
    return cargo.risk in tool.guards


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for cargo_id in sorted(place.affords):
            cargo = CARGO[cargo_id]
            for tool_id, tool in TOOLS.items():
                if tool_fits(cargo, tool):
                    combos.append((place_id, cargo_id, tool_id))
    return combos


def listening_score(trait: str, helper_id: str) -> int:
    base = 5 if trait in LISTENING_TRAITS else 3
    return base + HELPERS[helper_id].bonus


def would_listen(trait: str, helper_id: str) -> bool:
    return listening_score(trait, helper_id) > int(PRIDE_INIT)


def explain_rejection(cargo: Cargo, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} does not truly protect {cargo.phrase}. "
        f"{cargo.label.capitalize()} is at risk from {cargo.risk}, so pick a tool "
        f"that guards that problem.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_trip(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    cargo = sim.get("cargo")
    return {
        "wobble": cargo.meters["wobble"] >= THRESHOLD,
        "nearspill": cargo.meters["nearspill"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs / beats
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, elder: Entity, cargo_cfg: Cargo, helper_cfg: Helper) -> None:
    world.say(
        f"In the bazaar, bright and bizarre, {hero.id} helped {hero.pronoun('possessive')} "
        f"{elder.label_word} at a busy little barrow. {world.place.color_line}"
    )
    world.say(
        'Above one stall, both skinny and tall, hung a flappy cloth sign that read '
        '"abcdefghijklmnop," and everyone giggled when it flapped like a rope.'
    )
    world.say(
        f"{helper_cfg.entrance} Even the bazaar seemed to grin, as if some small muddle "
        f"might soon begin."
    )


def errand(world: World, hero: Entity, elder: Entity, cargo_cfg: Cargo) -> None:
    world.say(
        f'"Please carry {cargo_cfg.phrase} to {cargo_cfg.destination}," said '
        f'''{elder.label_word}. \"Walk with care from here to there.\"'''
    )
    hero.memes["duty"] += 1


def foreshadow(world: World, cargo_cfg: Cargo) -> None:
    world.say(
        f"But the lane gave a hint, almost soft as a squint: {world.place.foreshadow} "
        f"{cargo_cfg.hazard_line}"
    )
    world.facts["foreshadowed"] = True


def boast(world: World, hero: Entity, tool_cfg: Tool) -> None:
    hero.memes["pride"] = PRIDE_INIT
    world.say(
        f'{hero.id} puffed up with a skip and a hop. "I do not need {tool_cfg.phrase}; '
        f"I can dash to the stop!"
    )


def warn(world: World, hero: Entity, elder: Entity, cargo_cfg: Cargo, tool_cfg: Tool, helper_cfg: Helper) -> None:
    pred = predict_trip(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_nearspill"] = pred["nearspill"]
    if pred["nearspill"]:
        world.say(
            f'{elder.label_word.capitalize()} shook {elder.pronoun("possessive")} head. '
            f'"Fast feet can be neat, but not with {cargo_cfg.label} in tow. '
            f'Use {tool_cfg.phrase}, and easy you go."'
        )
    else:
        world.say(
            f'{elder.label_word.capitalize()} smiled and said, "A safe little way '
            f'beats a showy parade."'
        )
    world.say(helper_cfg.warning)


def use_tool(world: World, hero: Entity, tool_cfg: Tool) -> None:
    tool = world.get("tool")
    tool.protective = True
    tool.carried_by = hero.id
    hero.memes["care"] += 1
    world.say(
        f"So {hero.id} reached for {tool_cfg.phrase} and {tool_cfg.carry_line}. "
        f"Slow was the way, and safe was the play."
    )


def attempt_showoff(world: World, hero: Entity, helper_cfg: Helper) -> None:
    world.say(
        f'But {hero.id} tried first with one proud little burst, balancing the load '
        f"with a twirl and a verse."
    )
    propagate(world, narrate=False)
    if world.get("cargo").meters["nearspill"] >= THRESHOLD:
        world.say(helper_cfg.mishap)


def nearspill(world: World, hero: Entity, cargo_cfg: Cargo) -> None:
    cargo = world.get("cargo")
    if cargo.meters["nearspill"] < THRESHOLD:
        return
    cargo.meters["smudged"] += 1
    hero.memes["pride"] = 0.0
    hero.memes["humility"] += 1
    world.say(
        f"{cargo_cfg.nearspill_line} {cargo_cfg.recovery_line} "
        f'''{hero.id} blinked and whispered, \"Oh dear. I should have used the safe way here.\"'''
    )


def deliver(world: World, hero: Entity, cargo_cfg: Cargo, helper_cfg: Helper) -> None:
    cargo = world.get("cargo")
    cargo.meters["delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last {hero.id} reached {cargo_cfg.destination} with {cargo_cfg.phrase} safe and sound. "
        f"Nothing was lost, and nothing was found on the ground."
    )
    world.say(
        f"{helper_cfg.ending} {hero.id} stood taller in a quieter way: not proud of a trick, "
        f"but proud of a careful day."
    )


def closing_lesson(world: World, elder: Entity) -> None:
    world.say(
        f'{elder.label_word.capitalize()} gave a nod, gentle and true: "When hands are careful, '
        f"tasks smile back at you. A steady pace and listening ear can carry joy from here to there."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    cargo: str
    tool: str
    helper: str
    name: str
    gender: str
    elder: str
    trait: str
    age: int = 6
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "bazaar": [
        (
            "What is a bazaar?",
            "A bazaar is a busy market with many small stalls close together. People go there to buy, sell, and talk.",
        )
    ],
    "wind": [
        (
            "Why can wind be a problem when you carry cloth?",
            "Wind can catch light cloth and pull it open or blow it away. That is why long cloth is safer when it is rolled or tucked in.",
        )
    ],
    "bump": [
        (
            "Why is glass risky in a crowded place?",
            "Glass can knock into things when people bump close by. If it is carried carefully on something steady, it is much safer.",
        )
    ],
    "tilt": [
        (
            "Why does a pie or tart need to stay level?",
            "A tart can slide if it tilts too much. Keeping it level helps the filling stay where it belongs.",
        )
    ],
    "tube": [
        (
            "What is a cardboard tube good for?",
            "A cardboard tube can keep a rolled paper or cloth from flapping around. It gives the long thing a firm shape while you carry it.",
        )
    ],
    "tray": [
        (
            "Why does a tray help carry a jar?",
            "A tray gives the jar a flat place to sit. Holding the tray with two hands can make the jar steadier.",
        )
    ],
    "box": [
        (
            "Why does a box help protect a tart?",
            "A box keeps the tart together and makes it easier to carry level. The lid also helps stop little bumps from bothering it.",
        )
    ],
    "careful_carry": [
        (
            "Why is listening important when you carry something important?",
            "Listening can help you choose the safe way before a problem grows. A careful choice often saves time and trouble later.",
        )
    ],
    "letters": [
        (
            "What are letters of the alphabet for?",
            "Letters are the shapes we use to build words. Putting them in order helps us read and write.",
        )
    ],
    "animal": [
        (
            "Can animals in a market be funny?",
            "Yes. Animals can make people laugh with waddles, sneezes, or silly sounds. Even so, people still need to stay careful around them.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bazaar", "wind", "bump", "tilt", "tube", "tray", "box", "careful_carry", "letters", "animal"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cargo_cfg = f["cargo_cfg"]
    helper_cfg = f["helper_cfg"]
    outcome = f["outcome"]
    if outcome == "listened_first":
        return [
            'Write a short rhyming story for a 3-to-5-year-old set in a bazaar that includes the exact string "abcdefghijklmnop".',
            f"Tell a gentle bazaar story where {hero.id} is asked to carry {cargo_cfg.phrase}, listens to advice right away, and learns that careful choices beat showy tricks.",
            f"Write a funny, child-facing rhyme with foreshadowing, a {helper_cfg.label}, and a moral about responsibility.",
        ]
    return [
        'Write a short rhyming story for a 3-to-5-year-old set in a bazaar that includes the exact string "abcdefghijklmnop".',
        f"Tell a bazaar story where {hero.id} almost makes a mess carrying {cargo_cfg.phrase}, then switches to the safe way and finishes the errand.",
        f"Write a humorous rhyming story with foreshadowing, a {helper_cfg.label}, and a moral about listening before showing off.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    cargo_cfg = f["cargo_cfg"]
    tool_cfg = f["tool_cfg"]
    helper_cfg = f["helper_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was helping {hero.pronoun('possessive')} {elder.label_word} in the bazaar. A funny {helper_cfg.label} was nearby too.",
        ),
        (
            f"What was {hero.id} asked to carry?",
            f"{hero.id} was asked to carry {cargo_cfg.phrase} to {cargo_cfg.destination}. It was important to keep it safe on the way.",
        ),
        (
            "How did the story foreshadow trouble?",
            f"The lane gave a warning before the mistake happened: {world.place.foreshadow.lower()} {cargo_cfg.hazard_line} That clue hinted the cargo could wobble if {hero.id} tried to carry it the flashy way.",
        ),
    ]
    if f["predicted_nearspill"]:
        qa.append(
            (
                f"Why did {hero.id}'s {elder.label_word} warn {hero.pronoun('object')}?",
                f"{elder.label_word.capitalize()} warned {hero.id} because the cargo was at risk from {cargo_cfg.risk}. Without {tool_cfg.phrase}, it could wobble and almost spill, so the warning came from a real danger, not from fussing.",
            )
        )
    if outcome == "listened_first":
        qa.append(
            (
                f"Did {hero.id} listen right away?",
                f"Yes. {hero.id} chose {tool_cfg.phrase} before trouble started, so the errand stayed calm and tidy. Listening early kept the problem small enough that it never became a real mess.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} tried to show off?",
                f"The cargo nearly spilled, and {hero.id} felt alarmed at once. That scary little wobble taught {hero.pronoun('object')} that tricks were not worth the risk.",
            )
        )
        qa.append(
            (
                f"How did {hero.id} fix the problem?",
                f"After the near-spill, {hero.id} used {tool_cfg.phrase} and carried the cargo the safe way. The second try worked because the tool really matched the danger.",
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f"The story teaches that careful listening is wiser than showing off. A steady choice helped {hero.id} finish the job and protect something that mattered.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bazaar", f["risk"]} | set(f["cargo_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["helper_cfg"].tags)
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.protective:
            bits.append(f"guards={sorted(e.guards)}")
        elif e.guards:
            bits.append(f"tool_guards={sorted(e.guards)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} listened_first={world.facts.get('listened_first')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="cloth_lane",
        cargo="banner",
        tool="tube",
        helper="parrot",
        name="Mina",
        gender="girl",
        elder="aunt",
        trait="careful",
        age=6,
    ),
    StoryParams(
        place="spice_arch",
        cargo="jar",
        tool="tray",
        helper="duck",
        name="Omar",
        gender="boy",
        elder="uncle",
        trait="bold",
        age=7,
    ),
    StoryParams(
        place="pie_square",
        cargo="tart",
        tool="box",
        helper="goat",
        name="Lila",
        gender="girl",
        elder="mother",
        trait="showy",
        age=5,
    ),
    StoryParams(
        place="spice_arch",
        cargo="jar",
        tool="basket",
        helper="parrot",
        name="Eli",
        gender="boy",
        elder="father",
        trait="patient",
        age=6,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
fits(Cg, Tl) :- cargo(Cg), tool(Tl), risk(Cg, R), guards(Tl, R).
valid(Pl, Cg, Tl) :- place(Pl), affords(Pl, Cg), fits(Cg, Tl).

% --- listening / outcome model --------------------------------------------
care_score(5) :- trait(T), listening_trait(T).
care_score(3) :- trait(T), not listening_trait(T).
listen_score(C + B) :- care_score(C), chosen_helper(H), bonus(H, B).
listened_first :- pride_init(P), listen_score(S), S > P.

outcome(listened_first) :- listened_first.
outcome(learned_after_nearspill) :- not listened_first.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for cargo_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, cargo_id))
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("risk", cargo_id, cargo.risk))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for risk in sorted(tool.guards):
            lines.append(asp.fact("guards", tool_id, risk))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("bonus", helper_id, helper.bonus))
    for trait in sorted(LISTENING_TRAITS):
        lines.append(asp.fact("listening_trait", trait))
    lines.append(asp.fact("pride_init", int(PRIDE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "listened_first" if would_listen(params.trait, params.helper) else "learned_after_nearspill"


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
    parser = build_parser()
    for s in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome disagreements.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a careful errand in a bazaar, told in a rhyming voice."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--age", type=int, choices=[4, 5, 6, 7])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.tool:
        cargo = CARGO[args.cargo]
        tool = TOOLS[args.tool]
        if not tool_fits(cargo, tool):
            raise StoryError(explain_rejection(cargo, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, cargo, tool = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    elder = args.elder or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    age = args.age if args.age is not None else rng.choice([4, 5, 6, 7])

    return StoryParams(
        place=place,
        cargo=cargo,
        tool=tool,
        helper=helper,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
        age=age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cargo not in CARGO:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.elder not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown elder: {params.elder})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    place = PLACES[params.place]
    cargo_cfg = CARGO[params.cargo]
    tool_cfg = TOOLS[params.tool]
    helper_cfg = HELPERS[params.helper]

    if params.cargo not in place.affords:
        raise StoryError(f"(No story: {place.label} is not the right route for {cargo_cfg.phrase}.)")
    if not tool_fits(cargo_cfg, tool_cfg):
        raise StoryError(explain_rejection(cargo_cfg, tool_cfg))

    world = tell(
        place=place,
        cargo_cfg=cargo_cfg,
        tool_cfg=tool_cfg,
        helper_cfg=helper_cfg,
        hero_name=params.name,
        hero_type=params.gender,
        elder_type=params.elder,
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
        print(f"{len(combos)} compatible (place, cargo, tool) combos:\n")
        for place, cargo, tool in combos:
            print(f"  {place:11} {cargo:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.cargo} at {p.place} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def tell(
    place: Place,
    cargo_cfg: Cargo,
    tool_cfg: Tool,
    helper_cfg: Helper,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    elder_type: str = "aunt",
    trait: str = "careful",
    age: int = 6,
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            role="hero",
            traits=[trait],
            attrs={"age": age},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            attrs={"age": 30},
        )
    )
    world.add(
        Entity(
            id="helper",
            kind="thing",
            type=helper_cfg.kind,
            role="helper",
            label=helper_cfg.label,
            attrs={"bonus": helper_cfg.bonus},
        )
    )
    cargo = world.add(
        Entity(
            id="cargo",
            kind="thing",
            type="cargo",
            label=cargo_cfg.label,
            owner=elder.id,
            carried_by=hero.id,
        )
    )
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool_cfg.label,
            protective=False,
            guards=set(tool_cfg.guards),
            owner=elder.id,
        )
    )

    world.facts.update(
        hero=hero,
        elder=elder,
        helper_cfg=helper_cfg,
        cargo_cfg=cargo_cfg,
        tool_cfg=tool_cfg,
        place=place,
        risk=cargo_cfg.risk,
        listened_first=False,
        outcome="",
        foreshadowed=False,
        predicted_wobble=False,
        predicted_nearspill=False,
    )

    introduce(world, hero, elder, cargo_cfg, helper_cfg)
    errand(world, hero, elder, cargo_cfg)
    foreshadow(world, cargo_cfg)

    world.para()
    boast(world, hero, tool_cfg)
    warn(world, hero, elder, cargo_cfg, tool_cfg, helper_cfg)

    first_listen = would_listen(trait, helper_cfg.id)
    world.facts["listened_first"] = first_listen

    world.para()
    if first_listen:
        use_tool(world, hero, tool_cfg)
        deliver(world, hero, cargo_cfg, helper_cfg)
        world.facts["outcome"] = "listened_first"
    else:
        attempt_showoff(world, hero, helper_cfg)
        nearspill(world, hero, cargo_cfg)
        world.say("This time the lesson arrived before disaster could stay.")
        use_tool(world, hero, tool_cfg)
        deliver(world, hero, cargo_cfg, helper_cfg)
        world.facts["outcome"] = "learned_after_nearspill"

    world.para()
    closing_lesson(world, elder)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "cloth_lane": Place(
        id="cloth_lane",
        label="Cloth Lane",
        color_line="Scarves swished high, low, to and fro, in strips of saffron, indigo, and glow.",
        foreshadow="A teasing breeze kept tugging hems and tassels.",
        affords={"banner"},
    ),
    "spice_arch": Place(
        id="spice_arch",
        label="Spice Arch",
        color_line="Jars winked with cumin and cinnamon, and the air made every nose want to sing.",
        foreshadow="A crowd kept squeezing through the arch in little shoulder-bumping parcels.",
        affords={"jar"},
    ),
    "pie_square": Place(
        id="pie_square",
        label="Pie Square",
        color_line="Pies shone like moons on wooden boards, and spoons clinked cheerful little chords.",
        foreshadow="The stones were lumpy and the handcart wheels went bumpity-bump.",
        affords={"tart"},
    ),
}

CARGO = {
    "banner": Cargo(
        id="banner",
        label="banner",
        phrase="a rolled letter banner",
        risk="wind",
        hazard_line="A long cloth thing could catch the air and flap where it ought to glide.",
        owner_type="aunt",
        destination="the school stall",
        nearspill_line="The banner sprang half-open like a kite in a stormy stew.",
        recovery_line="Letters nearly flew in a blue windy queue.",
        tags={"banner", "letters", "wind"},
    ),
    "jar": Cargo(
        id="jar",
        label="jar of cumin",
        phrase="a warm glass jar of cumin",
        risk="bump",
        hazard_line="A glassy jar and a crowded jostle are not the best of friends.",
        owner_type="uncle",
        destination="the tea stall",
        nearspill_line="The jar knocked the rail with a clink-clank sound.",
        recovery_line="Only a tiny puff of spice escaped and danced around.",
        tags={"jar", "spice", "bump"},
    ),
    "tart": Cargo(
        id="tart",
        label="plum tart",
        phrase="a little plum tart",
        risk="tilt",
        hazard_line="A wobbling tart on a bumpy path likes level hands, not tricks.",
        owner_type="mother",
        destination="the baker's bench",
        nearspill_line="The tart slid sideways with a slippery sigh.",
        recovery_line="One plum wobbled like a sleepy eye.",
        tags={"tart", "baking", "tilt"},
    ),
}

TOOLS = {
    "tube": Tool(
        id="tube",
        label="cardboard tube",
        phrase="a sturdy cardboard tube",
        guards={"wind"},
        carry_line="slipped the banner snug inside",
        tags={"tube", "careful_carry"},
    ),
    "tray": Tool(
        id="tray",
        label="wooden tray",
        phrase="a flat wooden tray",
        guards={"bump"},
        carry_line="set the jar in the middle and held the sides with two hands",
        tags={"tray", "careful_carry"},
    ),
    "box": Tool(
        id="box",
        label="pie box",
        phrase="a pie box with a lid",
        guards={"tilt"},
        carry_line="nestled the tart inside and kept the box level as a table",
        tags={"box", "careful_carry"},
    ),
    "basket": Tool(
        id="basket",
        label="open basket",
        phrase="an open basket",
        guards={"bump"},
        carry_line="placed the load inside and gripped the handle",
        tags={"basket"},
    ),
}

HELPERS = {
    "goat": Helper(
        id="goat",
        label="goat",
        kind="goat",
        bonus=0,
        entrance="A goat in a blue ribbon chewed a cabbage leaf and stared as if it knew a secret joke.",
        warning='"Baa," said the goat, which was not a speech, but somehow it sounded like, "Do not make a mess of each."',
        mishap="Right then the goat sneezed -- bhaa-choo! -- and even that tiny noise made the wobble feel twice as true.",
        ending="The goat wagged its beard as if to say, \"Now that was a tidy way.\"",
        tags={"goat", "animal"},
    ),
    "duck": Helper(
        id="duck",
        label="duck",
        kind="duck",
        bonus=1,
        entrance="A duck waddled by in a puddle of shine, quacking as if it were keeper of the line.",
        warning='"Quack, quack, back up the track," said the duck, and everyone laughed because the quack fit the fact.',
        mishap="The duck flapped once, not meaning harm, but the sudden flurry set off alarm.",
        ending="The duck gave two proud quacks and a bounce, as if approving the careful route ounce by ounce.",
        tags={"duck", "animal"},
    ),
    "parrot": Helper(
        id="parrot",
        label="parrot",
        kind="parrot",
        bonus=2,
        entrance="On a pole sat a parrot in a pepper-red cap, bobbing and blinking beside the nap.",
        warning='"Carry it steady!" squawked the parrot. "Not showy, not ready? Then do not start it!"',
        mishap="The parrot cried, \"Whoa below!\" so loudly that the whole lane gasped in a row.",
        ending="The parrot clicked its beak and sang, \"Slow is strong all day long!\"",
        tags={"parrot", "animal"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zuri", "Tara", "Sana", "Maya"]
BOY_NAMES = ["Omar", "Eli", "Rafi", "Noah", "Theo", "Arun", "Milo", "Ben"]
TRAITS = ["careful", "patient", "thoughtful", "bouncy", "bold", "showy"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
