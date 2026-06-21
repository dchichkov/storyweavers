#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jam_dim_surprise_moral_value_teamwork_slice.py
========================================================================

A standalone storyworld about two children making a small breakfast surprise in a
quiet morning kitchen. The stories are slice-of-life tales with a clear turn:
the children want to bring bread and jam to someone they love, but one practical
problem appears, and teamwork solves it in a gentle, believable way.

Seed notes
----------
Required seed word:
    jam-dim

Featured instruments:
    Surprise, Moral Value, Teamwork

World idea
----------
Two children get up a little early to make a breakfast surprise for a grown-up.
They can handle the simple setup, but one obstacle appears:

* the jam jar is on a high shelf
* the jam lid is too tight
* the breakfast tray is too heavy for one child

One child starts to do the hard part alone. The other foresees the risk by
running the world model forward on a copy. Then they choose a teamwork method
that actually fits the obstacle. The story ends with a warm surprise and a small
spoken moral: doing a kind thing together is better than doing it in a risky,
show-off way alone.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
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
class Setting:
    id: str
    place: str
    light: str
    window: str
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
class Breakfast:
    id: str
    item: str
    phrase: str
    warm_line: str
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
class JamKind:
    id: str
    flavor: str
    color: str
    spoon_line: str
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
class Obstacle:
    id: str
    label: str
    need_support: bool = False
    need_grip: bool = False
    need_balance: bool = False
    solo_risk: str = ""
    solved_text: str = ""
    proof_text: str = ""
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
    support: bool = False
    grip: bool = False
    balance: bool = False
    sense: int = 0
    action_text: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "helper"}]


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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("instigator")
    jam = world.entities.get("jam")
    obstacle = world.facts.get("obstacle_cfg")
    if not kid or not jam or not obstacle:
        return out
    if not obstacle.need_support:
        return out
    if kid.meters["solo_attempt"] < THRESHOLD:
        return out
    if kid.meters["supported"] >= THRESHOLD:
        return out
    sig = ("wobble", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.meters["risk"] += 1
    kid.memes["fear"] += 1
    jam.meters["wobble"] += 1
    out.append("__risk__")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("instigator")
    jam = world.entities.get("jam")
    obstacle = world.facts.get("obstacle_cfg")
    if not kid or not jam or not obstacle:
        return out
    if not obstacle.need_grip:
        return out
    if kid.meters["solo_attempt"] < THRESHOLD:
        return out
    if jam.meters["gripped"] >= THRESHOLD:
        return out
    sig = ("slip", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.meters["risk"] += 1
    kid.memes["fear"] += 1
    jam.meters["slippery"] += 1
    out.append("__risk__")
    return out


def _r_tilt(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("instigator")
    tray = world.entities.get("tray")
    obstacle = world.facts.get("obstacle_cfg")
    if not kid or not tray or not obstacle:
        return out
    if not obstacle.need_balance:
        return out
    if kid.meters["solo_attempt"] < THRESHOLD:
        return out
    if tray.meters["carried_together"] >= THRESHOLD:
        return out
    sig = ("tilt", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.meters["risk"] += 1
    kid.memes["fear"] += 1
    tray.meters["tilting"] += 1
    out.append("__risk__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="tilt", tag="physical", apply=_r_tilt),
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
# Reasonableness gate
# ---------------------------------------------------------------------------
def method_fits(obstacle: Obstacle, method: Method) -> bool:
    if obstacle.need_support and not method.support:
        return False
    if obstacle.need_grip and not method.grip:
        return False
    if obstacle.need_balance and not method.balance:
        return False
    return method.sense >= SENSE_MIN


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for breakfast_id in BREAKFASTS:
            for jam_id in JAMS:
                for obstacle_id, obstacle in OBSTACLES.items():
                    for method_id, method in METHODS.items():
                        if method_fits(obstacle, method):
                            combos.append((setting_id, breakfast_id, jam_id, obstacle_id, method_id))
    return combos


def explain_method_rejection(obstacle: Obstacle, method: Method) -> str:
    need_bits = []
    if obstacle.need_support:
        need_bits.append("steady support")
    if obstacle.need_grip:
        need_bits.append("a strong grip")
    if obstacle.need_balance:
        need_bits.append("shared balance")
    need = ", ".join(need_bits) if need_bits else "the right kind of help"
    if method.sense < SENSE_MIN:
        return (
            f"(No story: '{method.id}' is known in the world but refused because it is "
            f"not sensible enough for children to model. Pick a calmer teamwork method.)"
        )
    return (
        f"(No story: {obstacle.label} needs {need}, but '{method.id}' does not provide it. "
        f"The teamwork solution must actually solve the problem.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_solo_risk(world: World) -> dict:
    sim = world.copy()
    instigator = sim.get("instigator")
    instigator.meters["solo_attempt"] += 1
    propagate(sim, narrate=False)
    jam = sim.get("jam")
    tray = sim.get("tray")
    return {
        "risk": instigator.meters["risk"],
        "wobble": jam.meters["wobble"],
        "slippery": jam.meters["slippery"],
        "tilting": tray.meters["tilting"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def open_scene(world: World, a: Entity, b: Entity, recipient: Entity,
               breakfast: Breakfast, jam: JamKind) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
        kid.memes["excitement"] += 1
    world.say(
        f"Early one morning, {a.id} and {b.id} padded into {world.setting.place} "
        f"before {recipient.label_word} woke up. {world.setting.light}"
    )
    world.say(
        f'{a.id} whispered, "Let\'s make a breakfast surprise for {recipient.label_word}." '
        f"{b.id} nodded at once."
    )
    world.say(
        f"On the counter they set out {breakfast.phrase}, a small plate, and the "
        f"{jam.flavor} jam jar. {breakfast.warm_line}"
    )


def jam_dim_line(world: World, jam: JamKind) -> None:
    world.say(
        f"The kitchen was still jam-dim, as {world.get('helper').id} liked to call "
        f"the soft {jam.color} morning light shining through the glass by {world.setting.window}."
    )


def notice_problem(world: World, obstacle: Obstacle) -> None:
    world.say(obstacle.solo_risk)


def start_alone(world: World, a: Entity, obstacle: Obstacle) -> None:
    a.meters["solo_attempt"] += 1
    a.memes["determination"] += 1
    if obstacle.id == "high_shelf":
        world.say(
            f'"I can do it by myself," {a.id} whispered, reaching up and rising on tiptoe.'
        )
    elif obstacle.id == "tight_lid":
        world.say(
            f'"I can open it," {a.id} whispered, hugging the jar and twisting hard.'
        )
    else:
        world.say(
            f'"I can carry it alone," {a.id} whispered, sliding both hands under the tray.'
        )


def warn(world: World, a: Entity, b: Entity, obstacle: Obstacle) -> None:
    pred = predict_solo_risk(world)
    world.facts["predicted_risk"] = pred
    b.memes["care"] += 1
    if obstacle.id == "high_shelf":
        world.say(
            f'{b.id} caught {a.id}\'s sleeve. "Wait. If you stretch like that alone, '
            f'''the jar might wobble and you might wobble too," {b.pronoun()} said."'''
        )
    elif obstacle.id == "tight_lid":
        world.say(
            f'{b.id} put a hand on the jar. "Wait. If it slips, sticky jam will go '
            f'''everywhere, and you could bang your fingers," {b.pronoun()} said."'''
        )
    else:
        world.say(
            f'{b.id} peered at the tray. "Wait. If one side dips, the toast and jam '
            f'''could slide right off," {b.pronoun()} said."'''
        )


def teamwork(world: World, a: Entity, b: Entity, obstacle: Obstacle, method: Method) -> None:
    a.meters["supported"] = 1.0 if method.support else a.meters["supported"]
    jam = world.get("jam")
    tray = world.get("tray")
    if method.grip:
        jam.meters["gripped"] += 1
    if method.balance:
        tray.meters["carried_together"] += 1
    a.meters["solo_attempt"] = 0.0
    a.meters["risk"] = 0.0
    a.memes["fear"] = 0.0
    b.memes["fear"] = 0.0
    jam.meters["wobble"] = 0.0
    jam.meters["slippery"] = 0.0
    tray.meters["tilting"] = 0.0

    if obstacle.id == "high_shelf":
        jam.meters["reached"] += 1
    elif obstacle.id == "tight_lid":
        jam.meters["opened"] += 1
    else:
        tray.meters["delivered"] += 1

    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    world.say(method.action_text.format(a=a.id, b=b.id))
    world.say(obstacle.solved_text)


def finish_breakfast(world: World, breakfast: Breakfast, jam: JamKind, obstacle: Obstacle) -> None:
    tray = world.get("tray")
    jam_ent = world.get("jam")
    tray.meters["ready"] += 1
    jam_ent.meters["served"] += 1
    if obstacle.id != "heavy_tray":
        tray.meters["delivered"] += 1
    world.say(
        f"Soon the {breakfast.item} wore bright little swirls of {jam.flavor} jam, "
        f"and the plate looked neat and special instead of rushed."
    )


def deliver_surprise(world: World, a: Entity, b: Entity, recipient: Entity, breakfast: Breakfast) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    recipient.memes["surprise"] += 1
    recipient.memes["love"] += 1
    world.say(
        f"They carried the breakfast to {recipient.label_word} together and set it down "
        f"with a tiny clink. {recipient.label_word.capitalize()} blinked, sat up, and smiled wide."
    )
    world.say(
        f'"For me?" {recipient.pronoun()} asked. The room felt warmer than the toast.'
    )
    world.say(
        f'"It was our surprise," {a.id} and {b.id} said together.'
    )


def moral(world: World, recipient: Entity, a: Entity, b: Entity, obstacle: Obstacle) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
    world.say(
        f'{recipient.label_word.capitalize()} hugged them close. "The breakfast is lovely," '
        f'{recipient.pronoun()} said, "but what I love most is the way you helped each other."'
    )
    world.say(
        f"{obstacle.proof_text} After that, {a.id} no longer tried to be the whole plan alone, "
        f"and {b.id} felt brave about speaking up when help was needed."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    breakfast: str
    jam: str
    obstacle: str
    method: str
    instigator: str
    instigator_gender: str
    helper: str
    helper_gender: str
    recipient: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "jam": [
        (
            "What is jam?",
            "Jam is fruit that has been cooked with sugar until it turns soft and spreadable. People put it on toast, rolls, or biscuits."
        )
    ],
    "stool": [
        (
            "Why should someone hold a stool steady?",
            "A stool can wobble if nobody steadies it. Holding it still helps the person on it stay safe."
        )
    ],
    "towel": [
        (
            "Why can a towel help open a jar?",
            "A dry towel gives your hands more grip on smooth glass or a slippery lid. Better grip makes it easier to twist without slipping."
        )
    ],
    "tray": [
        (
            "Why is carrying a tray together helpful?",
            "Two people can share the weight and keep both sides level. That helps plates and cups stay in place."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other do one job together. It often makes a hard job safer and easier."
        )
    ],
    "surprise": [
        (
            "What makes a surprise kind?",
            "A kind surprise is something thoughtful that is meant to make someone feel loved. It should help or cheer them, not scare them."
        )
    ],
}
KNOWLEDGE_ORDER = ["jam", "stool", "towel", "tray", "teamwork", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    recipient = f["recipient"]
    breakfast = f["breakfast"]
    jam = f["jam_cfg"]
    obstacle = f["obstacle_cfg"]
    return [
        (
            f'Write a slice-of-life story for a 3-to-5-year-old about two children making a breakfast '
            f'surprise with {jam.flavor} jam. Include the exact word "jam-dim".'
        ),
        (
            f"Tell a gentle teamwork story where {a.id} and {b.id} try to make {recipient.label_word} "
            f"a surprise breakfast with {breakfast.item}, but {obstacle.label} causes a small problem "
            f"that they solve together."
        ),
        (
            "Write a simple moral story where children learn that doing a kind thing together is safer "
            "and better than trying to do everything alone."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    recipient = f["recipient"]
    breakfast = f["breakfast"]
    jam = f["jam_cfg"]
    obstacle = f["obstacle_cfg"]
    method = f["method"]
    pred = f.get("predicted_risk", {})
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children who wanted to make a breakfast surprise for {recipient.label_word}. "
            f"They were trying to do something loving before {recipient.label_word} woke up."
        ),
        (
            "What surprise did the children want to make?",
            f"They wanted to bring {recipient.label_word} {breakfast.item} with {jam.flavor} jam. "
            f"The small breakfast was their quiet morning surprise."
        ),
        (
            "What does jam-dim mean in the story?",
            f"In the story, jam-dim is the children's funny name for the soft colored morning light around the jam jar. "
            f"It shows how early and gentle the kitchen felt."
        ),
    ]
    if obstacle.id == "high_shelf":
        qa.append(
            (
                f"Why did {b.id} stop {a.id}?",
                f"{b.id} stopped {a.id} because the jam jar was too high to reach safely alone. "
                f"In the predicted risk, the jar could wobble, and {a.id} could wobble too."
            )
        )
    elif obstacle.id == "tight_lid":
        qa.append(
            (
                f"Why did {b.id} say to wait?",
                f"{b.id} knew the tight lid could make the jar slip from {a.id}'s hands. "
                f"If that happened, sticky jam could spread everywhere and {a.id} might hurt {a.pronoun('possessive')} fingers."
            )
        )
    else:
        qa.append(
            (
                "Why was the tray a problem?",
                f"The tray had become heavy once the breakfast was all set on it. "
                f"If one side dipped, the food could slide off before they reached {recipient.label_word}."
            )
        )

    qa.append(
        (
            "How did the children solve the problem?",
            f"They solved it by working together: {method.qa_text} "
            f"That teamwork matched the real problem instead of only hoping it would be fine."
        )
    )
    qa.append(
        (
            "What is the moral of the story?",
            f"The moral is that a kind surprise should be made with care, not with showing off. "
            f"By helping each other, the children kept the breakfast safe and made {recipient.label_word} feel loved."
        )
    )
    if pred:
        risk_parts = []
        if pred.get("wobble", 0) >= THRESHOLD:
            risk_parts.append("the jar might wobble")
        if pred.get("slippery", 0) >= THRESHOLD:
            risk_parts.append("the jar might slip")
        if pred.get("tilting", 0) >= THRESHOLD:
            risk_parts.append("the tray might tilt")
        if risk_parts:
            qa.append(
                (
                    "What might have gone wrong if one child kept going alone?",
                    f"{', '.join(risk_parts).capitalize()}. "
                    f"Because the other child spoke up in time, the surprise stayed neat and safe."
                )
            )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"jam", "teamwork", "surprise"}
    tags |= set(f["method"].tags)
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
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CURATED
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="apartment_kitchen",
        breakfast="toast",
        jam="strawberry",
        obstacle="high_shelf",
        method="hold_stool",
        instigator="Mina",
        instigator_gender="girl",
        helper="Ben",
        helper_gender="boy",
        recipient="mother",
    ),
    StoryParams(
        setting="rowhouse_kitchen",
        breakfast="rolls",
        jam="apricot",
        obstacle="tight_lid",
        method="towel_twist",
        instigator="Leo",
        instigator_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        recipient="father",
    ),
    StoryParams(
        setting="cottage_kitchen",
        breakfast="biscuits",
        jam="blueberry",
        obstacle="heavy_tray",
        method="carry_together",
        instigator="Nora",
        instigator_gender="girl",
        helper="Sam",
        helper_gender="boy",
        recipient="grandmother",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% reasonable methods
fits(O, M) :- obstacle(O), method(M), support_need(O), support(M), sensible(M).
fits(O, M) :- obstacle(O), method(M), grip_need(O), grip(M), sensible(M).
fits(O, M) :- obstacle(O), method(M), balance_need(O), balance(M), sensible(M).

% exact-need obstacles in this world: each one has one kind of practical need.
valid(S, B, J, O, M) :- setting(S), breakfast(B), jam(J), obstacle(O), method(M), fits(O, M).

risk(wobble)  :- chosen_obstacle(high_shelf), not chosen_support.
risk(slip)    :- chosen_obstacle(tight_lid), not chosen_grip.
risk(tilt)    :- chosen_obstacle(heavy_tray), not chosen_balance.

chosen_support :- chosen_method(M), support(M).
chosen_grip    :- chosen_method(M), grip(M).
chosen_balance :- chosen_method(M), balance(M).

solved :- chosen_obstacle(O), chosen_method(M), fits(O, M).
#show valid/5.
#show solved/0.
#show risk/1.
#show sensible/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BREAKFASTS:
        lines.append(asp.fact("breakfast", bid))
    for jid in JAMS:
        lines.append(asp.fact("jam", jid))
    for oid, o in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        if o.need_support:
            lines.append(asp.fact("support_need", oid))
        if o.need_grip:
            lines.append(asp.fact("grip_need", oid))
        if o.need_balance:
            lines.append(asp.fact("balance_need", oid))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        if m.support:
            lines.append(asp.fact("support", mid))
        if m.grip:
            lines.append(asp.fact("grip", mid))
        if m.balance:
            lines.append(asp.fact("balance", mid))
        if m.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", mid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_solved(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "solved"))


def asp_predicted_risks(obstacle_id: str, method_id: str) -> set[str]:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", obstacle_id),
            asp.fact("chosen_method", method_id),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return {r for (r,) in asp.atoms(model, "risk")}


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

    py_sensible = {m.id for m in sensible_methods()}
    asp_sensible = set(asp_sensible_methods())
    if py_sensible == asp_sensible:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={sorted(py_sensible)} clingo={sorted(asp_sensible)}")

    for params in CURATED:
        if not asp_solved(params):
            rc = 1
            print(f"MISMATCH: curated params not solved in ASP: {params}")
        predicted = asp_predicted_risks(params.obstacle, params.method)
        if predicted:
            rc = 1
            print(f"MISMATCH: solved method should remove risk but ASP still predicts {sorted(predicted)} for {params}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "jam-dim" not in sample.story:
            raise StoryError("smoke test story was empty or missed required word")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a breakfast surprise, a small obstacle, and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--breakfast", choices=BREAKFASTS)
    ap.add_argument("--jam", choices=JAMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--recipient", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.method:
        obstacle = OBSTACLES[args.obstacle]
        method = METHODS[args.method]
        if not method_fits(obstacle, method):
            raise StoryError(explain_method_rejection(obstacle, method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.breakfast is None or combo[1] == args.breakfast)
        and (args.jam is None or combo[2] == args.jam)
        and (args.obstacle is None or combo[3] == args.obstacle)
        and (args.method is None or combo[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, breakfast_id, jam_id, obstacle_id, method_id = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=instigator)
    recipient = args.recipient or rng.choice(["mother", "father", "grandmother", "grandfather"])

    return StoryParams(
        setting=setting_id,
        breakfast=breakfast_id,
        jam=jam_id,
        obstacle=obstacle_id,
        method=method_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        helper=helper,
        helper_gender=helper_gender,
        recipient=recipient,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.breakfast not in BREAKFASTS:
        raise StoryError(f"(Unknown breakfast: {params.breakfast})")
    if params.jam not in JAMS:
        raise StoryError(f"(Unknown jam: {params.jam})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.recipient not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown recipient: {params.recipient})")

    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    if not method_fits(obstacle, method):
        raise StoryError(explain_method_rejection(obstacle, method))

    world = tell(
        setting=SETTINGS[params.setting],
        breakfast=BREAKFASTS[params.breakfast],
        jam=JAMS[params.jam],
        obstacle=obstacle,
        method=method,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        helper=params.helper,
        helper_gender=params.helper_gender,
        recipient_type=params.recipient,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible_methods()
        print(f"sensible methods: {', '.join(sensible)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, breakfast, jam, obstacle, method) combos:\n")
        for combo in combos:
            print(f"  {combo[0]:18} {combo[1]:9} {combo[2]:10} {combo[3]:11} {combo[4]}")
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
            header = (
                f"### {p.instigator} & {p.helper}: {p.breakfast} with {p.jam} jam "
                f"({p.obstacle}, {p.method})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def tell(setting: Setting, breakfast: Breakfast, jam: JamKind, obstacle: Obstacle, method: Method,
         instigator: str = "Mina", instigator_gender: str = "girl",
         helper: str = "Ben", helper_gender: str = "boy",
         recipient_type: str = "mother") -> World:
    world = World(setting)
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["eager"],
        attrs={},
    ))
    b = world.add(Entity(
        id=helper,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["careful"],
        attrs={},
    ))
    recipient = world.add(Entity(
        id="Recipient",
        kind="character",
        type=recipient_type,
        role="recipient",
        label="the grown-up",
        attrs={},
    ))
    world.add(Entity(id="jam", type="jar", label=f"{jam.flavor} jam jar", attrs={}))
    world.add(Entity(id="tray", type="tray", label="breakfast tray", attrs={}))
    world.add(Entity(id="room", type="room", label=setting.place, attrs={}))

    world.facts.update(
        setting=setting,
        breakfast=breakfast,
        jam_cfg=jam,
        obstacle_cfg=obstacle,
        method=method,
        instigator=a,
        helper=b,
        recipient=recipient,
    )

    open_scene(world, a, b, recipient, breakfast, jam)
    jam_dim_line(world, jam)

    world.para()
    notice_problem(world, obstacle)
    start_alone(world, a, obstacle)
    warn(world, a, b, obstacle)

    world.para()
    teamwork(world, a, b, obstacle, method)
    finish_breakfast(world, breakfast, jam, obstacle)

    world.para()
    deliver_surprise(world, a, b, recipient, breakfast)
    moral(world, recipient, a, b, obstacle)

    world.facts.update(
        solved=True,
        delivered=world.get("tray").meters["delivered"] >= THRESHOLD,
        surprised=recipient.memes["surprise"] >= THRESHOLD,
        lesson=a.memes["lesson"] >= THRESHOLD and b.memes["lesson"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "apartment_kitchen": Setting(
        id="apartment_kitchen",
        place="the little apartment kitchen",
        light="The sky outside was pale, and the first light touched the tiles in a sleepy square.",
        window="the sink window",
        tags={"kitchen", "morning"},
    ),
    "rowhouse_kitchen": Setting(
        id="rowhouse_kitchen",
        place="the narrow rowhouse kitchen",
        light="A faint stripe of dawn lay across the table, and the house still sounded half asleep.",
        window="the back window",
        tags={"kitchen", "morning"},
    ),
    "cottage_kitchen": Setting(
        id="cottage_kitchen",
        place="the bright cottage kitchen",
        light="Birds were already fussing outside, but inside the room still held the hush of early morning.",
        window="the small curtain window",
        tags={"kitchen", "morning"},
    ),
}

BREAKFASTS = {
    "toast": Breakfast(
        id="toast",
        item="toast",
        phrase="two pieces of toast",
        warm_line="The toast gave off a warm, sweet smell that made the whole idea feel real.",
        tags={"toast"},
    ),
    "rolls": Breakfast(
        id="rolls",
        item="soft rolls",
        phrase="two soft rolls",
        warm_line="The rolls were still a little warm, and the children smiled at the bakery smell.",
        tags={"rolls"},
    ),
    "biscuits": Breakfast(
        id="biscuits",
        item="biscuits",
        phrase="a plate of biscuits",
        warm_line="The biscuits looked plain at first, but the children knew jam could turn them into a treat.",
        tags={"biscuits"},
    ),
}

JAMS = {
    "strawberry": JamKind(
        id="strawberry",
        flavor="strawberry",
        color="pink-red",
        spoon_line="The strawberry jam shone like a tiny ruby when the spoon dipped in.",
        tags={"jam", "strawberry"},
    ),
    "apricot": JamKind(
        id="apricot",
        flavor="apricot",
        color="gold-orange",
        spoon_line="The apricot jam glowed softly on the spoon, almost like little sunlight.",
        tags={"jam", "apricot"},
    ),
    "blueberry": JamKind(
        id="blueberry",
        flavor="blueberry",
        color="purple-blue",
        spoon_line="The blueberry jam looked deep and shiny, like evening sky caught in a jar.",
        tags={"jam", "blueberry"},
    ),
}

OBSTACLES = {
    "high_shelf": Obstacle(
        id="high_shelf",
        label="a high shelf",
        need_support=True,
        solo_risk="The jam jar was waiting on the highest pantry shelf, just a little too far for small hands.",
        solved_text="With the stool held steady and two pairs of eyes watching, the jar came down safely.",
        proof_text="The surprise reached the bed because one child steadied while the other reached.",
        tags={"shelf", "safety"},
    ),
    "tight_lid": Obstacle(
        id="tight_lid",
        label="a tight lid",
        need_grip=True,
        solo_risk="But the lid had been screwed on tight, and the smooth glass kept turning in small hands.",
        solved_text="The lid gave a soft pop at last, and nobody dropped a thing.",
        proof_text="The surprise stayed calm and tidy because one child held firm while the other twisted.",
        tags={"lid", "safety"},
    ),
    "heavy_tray": Obstacle(
        id="heavy_tray",
        label="a heavy tray",
        need_balance=True,
        solo_risk="When the toast, plate, spoon, and jam were all together, the breakfast tray felt heavier than it had looked.",
        solved_text="Held from both sides, the tray stayed level, and even the spoon did not rattle much.",
        proof_text="The surprise made it to the room in one piece because both children shared the weight.",
        tags={"tray", "balance"},
    ),
}

METHODS = {
    "hold_stool": Method(
        id="hold_stool",
        label="hold the stool steady",
        support=True,
        sense=3,
        action_text="{b} fetched the little folding stool, planted both feet, and held it steady while {a} reached up carefully.",
        qa_text="One child held the stool steady while the other reached for the jar.",
        tags={"stool", "teamwork"},
    ),
    "towel_twist": Method(
        id="towel_twist",
        label="use a towel and twist together",
        grip=True,
        sense=3,
        action_text="{b} wrapped a dry towel around the jar, held it tight, and {a} twisted the lid with both hands.",
        qa_text="One child used a towel to hold the jar still while the other twisted the lid.",
        tags={"towel", "teamwork"},
    ),
    "carry_together": Method(
        id="carry_together",
        label="carry the tray together",
        balance=True,
        sense=3,
        action_text="{a} took one handle and {b} took the other, and they lifted the tray together on the count of three.",
        qa_text="They each carried one side of the tray so it would stay level.",
        tags={"tray", "teamwork"},
    ),
    "pull_harder": Method(
        id="pull_harder",
        label="just pull harder",
        sense=1,
        action_text="",
        qa_text="",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ava", "Nora", "Ruby", "Tess", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Finn", "Eli", "Max", "Sam", "Theo"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
