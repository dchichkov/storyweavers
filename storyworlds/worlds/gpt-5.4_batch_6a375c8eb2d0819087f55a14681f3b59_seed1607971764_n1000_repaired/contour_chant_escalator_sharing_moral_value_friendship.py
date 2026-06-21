#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/contour_chant_escalator_sharing_moral_value_friendship.py
=====================================================================================

A standalone storyworld for a small fable-like domain:

Two young animal friends ride an escalator toward a high indoor garden. One of
them clutches a useful load and does not want to share it. The ridged contour of
the moving steps makes the load wobble. A calm friend uses a little chant and
offers the right kind of help. By sharing the burden, they reach the top safely
and discover that friendship grows stronger when paws work together.

Run it
------
    python storyworlds/worlds/gpt-5.4/contour_chant_escalator_sharing_moral_value_friendship.py
    python storyworlds/worlds/gpt-5.4/contour_chant_escalator_sharing_moral_value_friendship.py --cargo seed_tray --remedy opposite_corners
    python storyworlds/worlds/gpt-5.4/contour_chant_escalator_sharing_moral_value_friendship.py --cargo ribbon_roll --remedy one_each_handle
    python storyworlds/worlds/gpt-5.4/contour_chant_escalator_sharing_moral_value_friendship.py --all
    python storyworlds/worlds/gpt-5.4/contour_chant_escalator_sharing_moral_value_friendship.py --qa --json
    python storyworlds/worlds/gpt-5.4/contour_chant_escalator_sharing_moral_value_friendship.py --verify
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
RISK_MIN = 2


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
        female = {"girl", "mother", "hen", "duck", "goose"}
        male = {"boy", "father", "fox", "bear", "badger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Cargo:
    id: str
    label: str
    phrase: str
    destination: str
    reward: str
    contour_line: str
    risk: int
    weight: int
    wide: bool = False
    handles: int = 0
    divisible: bool = False
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
class Remedy:
    id: str
    label: str
    power: int
    needs_wide: bool = False
    needs_handles: int = 0
    needs_divisible: bool = False
    text: str = ""
    qa_text: str = ""
    chant_line: str = ""
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


def _r_wobble_alarm(world: World) -> list[str]:
    load = world.get("load")
    if load.meters["wobble"] < THRESHOLD:
        return []
    sig = ("wobble_alarm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("escalator").meters["danger"] += 1
    world.get("holder").memes["fear"] += 1
    world.get("helper").memes["fear"] += 1
    return ["__wobble__"]


def _r_spill_loss(world: World) -> list[str]:
    load = world.get("load")
    if load.meters["spill"] < THRESHOLD:
        return []
    sig = ("spill_loss",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    load.meters["fullness"] -= 1
    world.get("holder").memes["regret"] += 1
    world.get("helper").memes["concern"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wobble_alarm", tag="physical", apply=_r_wobble_alarm),
    Rule(name="spill_loss", tag="physical", apply=_r_spill_loss),
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


def remedy_fits(cargo: Cargo, remedy: Remedy) -> bool:
    if remedy.needs_wide and not cargo.wide:
        return False
    if remedy.needs_handles and cargo.handles < remedy.needs_handles:
        return False
    if remedy.needs_divisible and not cargo.divisible:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for cargo_id, cargo in CARGO.items():
        if cargo.risk < RISK_MIN:
            continue
        for remedy_id, remedy in REMEDIES.items():
            if remedy_fits(cargo, remedy):
                combos.append((cargo_id, remedy_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    cargo = CARGO[params.cargo]
    remedy = REMEDIES[params.remedy]
    if params.generous_start:
        return "shared_early"
    severity = cargo.risk + params.delay
    return "steady" if remedy.power >= severity else "spilled"


def predict_wobble(world: World, cargo: Cargo, generous_start: bool, delay: int) -> dict:
    sim = world.copy()
    load = sim.get("load")
    if generous_start:
        load.meters["shared"] += 1
        load.meters["stable"] += 1
    else:
        load.meters["wobble"] += 1
        if cargo.risk + delay > 3:
            load.meters["spill"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": load.meters["wobble"] >= THRESHOLD,
        "spill": load.meters["spill"] >= THRESHOLD,
        "danger": sim.get("escalator").meters["danger"],
    }


def introduce(world: World, a: Entity, b: Entity, cargo: Cargo) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In a bright market hall, {a.id} the {a.type} and {b.id} the {b.type} were the best of friends. "
        f"They stood at the foot of a tall escalator that rose toward {cargo.destination}."
    )
    world.say(
        f"On the shining step before them, the dark grooves made a moving contour like little comb teeth, "
        f"and the ride hummed softly all the way up."
    )


def gift_load(world: World, a: Entity, cargo: Cargo) -> None:
    world.say(
        f"A kind shopkeeper handed {a.id} {cargo.phrase} and said it would be perfect for {cargo.reward}."
    )
    world.say(
        f"{a.id}'s eyes grew round with delight. {a.pronoun().capitalize()} wanted to carry the whole thing by {a.pronoun('object')}self."
    )


def desire_and_refusal(world: World, a: Entity, b: Entity, cargo: Cargo, generous_start: bool) -> None:
    if generous_start:
        a.memes["generosity"] += 1
        b.memes["trust"] += 1
        world.say(
            f'"Let us carry it together from the start," said {a.id}. "{cargo.reward.capitalize()} should be shared."'
        )
        return
    a.memes["selfishness"] += 1
    b.memes["sadness"] += 1
    world.say(
        f'"I can carry the {cargo.label} myself," said {a.id}, tucking it close. '
        f'"You may watch, {b.id}, but this special job is mine."'
    )
    world.say(
        f"{b.id} did not answer sharply. {b.pronoun().capitalize()} only looked at the long ride up and stayed near."
    )


def step_on(world: World, a: Entity, b: Entity, cargo: Cargo, generous_start: bool, delay: int) -> None:
    load = world.get("load")
    if generous_start:
        load.meters["shared"] += 1
        load.meters["stable"] += 1
        world.say(
            f"They stepped onto the escalator side by side, each with careful paws, and the {cargo.label} rode between them."
        )
        return
    load.meters["wobble"] += 1
    if cargo.risk + delay > 3:
        load.meters["spill"] += 1
    propagate(world, narrate=False)
    world.say(
        f"As the step lifted them, the ridged contour under the {cargo.label} made it tip. "
        f"{cargo.contour_line}"
    )
    if load.meters["spill"] >= THRESHOLD:
        world.say(
            f"A few pieces slipped loose and skittered down one step. {a.id}'s heart thumped at once."
        )
    else:
        world.say(
            f"The load gave one nervous wobble, and both friends felt the danger of carrying too much alone."
        )


def warning(world: World, a: Entity, b: Entity, cargo: Cargo, remedy: Remedy, generous_start: bool, delay: int) -> None:
    pred = predict_wobble(world, cargo, generous_start, delay)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_spill"] = pred["spill"]
    if generous_start:
        return
    b.memes["care"] += 1
    spill_clause = "and something may tumble away" if pred["spill"] else "before it tips any more"
    world.say(
        f'"Friend," said {b.id} gently, "one pair of paws is not enough here. '
        f'Let me help {spill_clause}."'
    )


def chant_and_offer(world: World, b: Entity, remedy: Remedy) -> None:
    b.memes["calm"] += 1
    world.say(
        f"To keep both hearts steady, {b.id} began a little chant: "
        f'"{remedy.chant_line}"'
    )


def accept_help(world: World, a: Entity, b: Entity, cargo: Cargo, remedy: Remedy, delay: int, generous_start: bool) -> None:
    load = world.get("load")
    if generous_start:
        return
    a.memes["selfishness"] = 0.0
    a.memes["humility"] += 1
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    load.meters["shared"] += 1
    load.meters["stable"] += 1
    body = remedy.text.format(cargo=cargo.label)
    world.say(
        f"{a.id} looked at the wobbling {cargo.label}, then at {b.id}, and felt wisdom arrive. "
        f'"Please help me," {a.pronoun()} said. Together they {body}.'
    )
    if remedy.power >= cargo.risk + delay:
        load.meters["wobble"] = 0.0
        world.get("escalator").meters["danger"] = 0.0
    else:
        load.meters["spill"] += 1
        propagate(world, narrate=False)


def arrival(world: World, a: Entity, b: Entity, cargo: Cargo, remedy: Remedy, outcome: str) -> None:
    load = world.get("load")
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["generosity"] += 1
    b.memes["generosity"] += 1
    if outcome == "shared_early":
        world.say(
            f"At the top, they stepped off as neatly as two swallows landing on a branch. "
            f"The {cargo.label} was still full, and both friends smiled because the climb had felt light."
        )
    elif outcome == "steady":
        world.say(
            f"Before the top was reached, the wobble stopped. The rest of the ride became easy, "
            f"and the escalator carried them upward as gently as a song."
        )
        world.say(
            f"When they stepped onto the upper floor, the {cargo.label} was safe in both sets of paws."
        )
    else:
        world.say(
            f"They reached the top with most of the {cargo.label} saved, though a small part had been lost on the ride."
        )
    if cargo.id == "seed_tray":
        finish = "They scattered the seeds for the roof doves, which bobbed and cooed in a happy ring."
    elif cargo.id == "berry_basket":
        finish = "They shared the berries with the old tortoise in the garden kiosk, who thanked them with a deep smile."
    else:
        finish = "They carried the ribbon rolls to the little gift table and decorated the place together."
    world.say(finish)
    world.say(
        f"Then {a.id} made room for {b.id} at {a.pronoun('possessive')} side, and they shared the last sweet part of the errand between them."
    )
    if outcome == "spilled":
        world.say(
            "So the escalator taught them this: when pride holds too tightly, some good things may slip away; "
            "when friends share the work, more goodness reaches the top."
        )
    else:
        world.say(
            "So the escalator taught them this: a burden shared between friends grows smaller, and friendship itself grows large."
        )
    world.facts["remaining_fullness"] = load.meters["fullness"]
def tell(
    remedy: Remedy,
    holder_name: str,
    holder_type: HolderType,
    helper_name: str,
    helper_type: HelperType,
    generous_start: GenerousStart,
    delay: Delay,
    cargo=None,
) -> World:
    world = World()
    a = world.add(Entity(id=holder_name, kind="character", type=holder_type, role="holder"))
    b = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="escalator", type="place", label="the escalator"))
    load = world.add(Entity(id="load", type="cargo", label=cargo.label))
    load.meters["fullness"] = 2.0
    load.meters["wobble"] = 0.0
    load.meters["spill"] = 0.0
    load.meters["shared"] = 0.0
    load.meters["stable"] = 0.0
    world.get("escalator").meters["danger"] = 0.0
    a.memes["selfishness"] = 0.0
    a.memes["generosity"] = 0.0
    a.memes["friendship"] = 0.0
    b.memes["friendship"] = 0.0
    b.memes["care"] = 0.0
    b.memes["trust"] = 0.0
    world.facts["delay"] = delay

    introduce(world, a, b, cargo)
    gift_load(world, a, cargo)

    world.para()
    desire_and_refusal(world, a, b, cargo, generous_start)
    step_on(world, a, b, cargo, generous_start, delay)
    warning(world, a, b, cargo, remedy, generous_start, delay)

    world.para()
    chant_and_offer(world, b, remedy)
    accept_help(world, a, b, cargo, remedy, delay, generous_start)
    outcome = outcome_of(
        StoryParams(
            cargo=cargo.id,
            remedy=remedy.id,
            holder_name=holder_name,
            holder_type=holder_type,
            helper_name=helper_name,
            helper_type=helper_type,
            generous_start=generous_start,
            delay=delay,
            seed=None,
        )
    )
    arrival(world, a, b, cargo, remedy, outcome)

    world.facts.update(
        holder=a,
        helper=b,
        cargo_cfg=cargo,
        remedy=remedy,
        load=load,
        outcome=outcome,
        generous_start=generous_start,
        ride_shared=load.meters["shared"] >= THRESHOLD,
        little_loss=load.meters["spill"] >= THRESHOLD,
    )
    return world
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


CARGO = {
    "seed_tray": Cargo(
        id="seed_tray",
        label="seed tray",
        phrase="a broad tray of sunflower seeds",
        destination="the little roof garden",
        reward="feeding the roof doves",
        contour_line="The tray rocked across the grooves, and the seeds whispered against one another.",
        risk=3,
        weight=3,
        wide=True,
        handles=0,
        divisible=False,
        tags={"seeds", "birds", "sharing"},
    ),
    "berry_basket": Cargo(
        id="berry_basket",
        label="berry basket",
        phrase="a basket of red berries with two looped handles",
        destination="the sunny tea balcony",
        reward="sharing a berry snack with an old tortoise",
        contour_line="The basket swung from one side to the other, and the berries rolled against the wicker.",
        risk=2,
        weight=2,
        wide=False,
        handles=2,
        divisible=False,
        tags={"berries", "basket", "sharing"},
    ),
    "ribbon_roll": Cargo(
        id="ribbon_roll",
        label="ribbon rolls",
        phrase="a bundle of bright ribbon rolls tied with soft string",
        destination="the small gift table above the toy shop",
        reward="decorating the table for everyone",
        contour_line="The rolls shifted together like sleepy snails and almost slipped from the stack.",
        risk=2,
        weight=2,
        wide=False,
        handles=0,
        divisible=True,
        tags={"ribbon", "sharing", "decorating"},
    ),
    "feather_box": Cargo(
        id="feather_box",
        label="feather box",
        phrase="a tiny box of feathers",
        destination="the hat stall upstairs",
        reward="adding a feather to one fine hat",
        contour_line="The box barely moved at all.",
        risk=1,
        weight=1,
        wide=False,
        handles=0,
        divisible=False,
        tags={"feather"},
    ),
}

REMEDIES = {
    "opposite_corners": Remedy(
        id="opposite_corners",
        label="hold opposite corners",
        power=3,
        needs_wide=True,
        needs_handles=0,
        needs_divisible=False,
        text="took opposite corners of the {cargo} and kept it level",
        qa_text="held opposite corners of the load and kept it level",
        chant_line="Step, paw, share, and rise.",
        tags={"share_load", "chant"},
    ),
    "one_each_handle": Remedy(
        id="one_each_handle",
        label="take one handle each",
        power=2,
        needs_wide=False,
        needs_handles=2,
        needs_divisible=False,
        text="took one handle each and walked the sway out of the {cargo}",
        qa_text="took one handle each and steadied the basket together",
        chant_line="Rail, handle, breathe, and rise.",
        tags={"handles", "chant"},
    ),
    "divide_bundle": Remedy(
        id="divide_bundle",
        label="divide the bundle",
        power=2,
        needs_wide=False,
        needs_handles=0,
        needs_divisible=False,
        text="untied the bundle, gave half the {cargo} to each friend, and carried the smaller parts safely",
        qa_text="divided the bundle so each friend carried part of it",
        chant_line="Half for you, half for me, up we go in harmony.",
        tags={"divide", "chant"},
    ),
}

ANIMALS = [
    ("Pip", "fox"),
    ("Mina", "duck"),
    ("Tavi", "badger"),
    ("Luma", "hen"),
    ("Brin", "bear"),
    ("Nell", "goose"),
]


KNOWLEDGE = {
    "escalator": [
        (
            "What is an escalator?",
            "An escalator is a moving staircase that carries people up or down. You stand still on the steps and hold the rail while it moves."
        )
    ],
    "share_load": [
        (
            "Why is sharing a heavy load helpful?",
            "Sharing a load means two bodies help keep it balanced. That makes it easier to carry and less likely to tip."
        )
    ],
    "chant": [
        (
            "What can a chant do when someone feels nervous?",
            "A chant can give a steady rhythm for breathing and moving. It helps people remember what to do one small step at a time."
        )
    ],
    "handles": [
        (
            "Why are two handles useful on a basket?",
            "Two handles let two helpers hold the basket evenly. When both sides are supported, the basket is less likely to swing."
        )
    ],
    "divide": [
        (
            "Why can splitting things into smaller parts help?",
            "Smaller parts are often easier to hold and balance. Each helper can carry one part without struggling so much."
        )
    ],
    "seeds": [
        (
            "Why do birds like seeds?",
            "Many birds eat seeds because they are small and full of food energy. Seeds are easy for little beaks to pick up."
        )
    ],
    "berries": [
        (
            "What is a berry basket for?",
            "A berry basket holds soft fruit so it can be carried gently. The basket keeps the berries together while people walk."
        )
    ],
    "ribbon": [
        (
            "What are ribbons used for?",
            "Ribbons are long strips of cloth used for tying and decorating. They can make a plain place look cheerful."
        )
    ],
    "friendship": [
        (
            "What does friendship mean?",
            "Friendship means caring about another person and treating them kindly. Friends help one another instead of trying to shine alone."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "escalator",
    "share_load",
    "chant",
    "handles",
    "divide",
    "seeds",
    "berries",
    "ribbon",
    "friendship",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    holder = f["holder"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    return [
        f'Write a short fable for a 3-to-5-year-old set on an escalator that includes the words "contour" and "chant".',
        f"Tell a gentle story about friendship where {holder.id} and {helper.id} must carry a {cargo.label} upward and learn to share the work.",
        f"Write a moral story in which a proud friend begins by wanting the whole task, but a calm chant and shared effort bring everyone safely to the top.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {holder.id} the {holder.type} and {helper.id} the {helper.type}. They were riding an escalator with a {cargo.label}."
        ),
        (
            f"Why did the {cargo.label} become a problem on the escalator?",
            f"The moving step contour made the {cargo.label} wobble while {holder.id} tried to manage it alone. One pair of paws could not keep it balanced on the ride."
        ),
        (
            f"What did {helper.id} do when things started to go wrong?",
            f"{helper.id} stayed calm, spoke gently, and began a chant to steady the moment. Then {helper.pronoun()} offered the right kind of help instead of scolding."
        ),
    ]
    if outcome == "shared_early":
        qa.append(
            (
                "Was there a big accident?",
                f"No. {holder.id} chose sharing from the beginning, so the ride stayed smooth and the {cargo.label} remained safe. The lesson came before any loss had to happen."
            )
        )
    elif outcome == "steady":
        qa.append(
            (
                f"How did the friends fix the problem?",
                f"They {remedy.qa_text}. Sharing the work made the load stable, so the danger faded before anything important fell away."
            )
        )
    else:
        qa.append(
            (
                f"Did they lose everything from the {cargo.label}?",
                f"No. They saved most of it once they worked together, but a little had already been lost. That small loss helped {holder.id} understand why sharing sooner would have been wiser."
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            "The moral is that pride makes a burden harder, but friendship and sharing make it lighter. When friends help each other, more good reaches its destination."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cargo = f["cargo_cfg"]
    remedy = f["remedy"]
    tags = {"escalator", "friendship"} | set(cargo.tags) | set(remedy.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    cargo: str
    remedy: str
    holder_name: str
    holder_type: str
    helper_name: str
    helper_type: str
    generous_start: bool = False
    delay: int = 0
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        cargo="seed_tray",
        remedy="opposite_corners",
        holder_name="Pip",
        holder_type="fox",
        helper_name="Mina",
        helper_type="duck",
        generous_start=False,
        delay=0,
        seed=None,
    ),
    StoryParams(
        cargo="berry_basket",
        remedy="one_each_handle",
        holder_name="Luma",
        holder_type="hen",
        helper_name="Tavi",
        helper_type="badger",
        generous_start=False,
        delay=0,
        seed=None,
    ),
    StoryParams(
        cargo="ribbon_roll",
        remedy="divide_bundle",
        holder_name="Brin",
        holder_type="bear",
        helper_name="Nell",
        helper_type="goose",
        generous_start=False,
        delay=1,
        seed=None,
    ),
    StoryParams(
        cargo="seed_tray",
        remedy="opposite_corners",
        holder_name="Mina",
        holder_type="duck",
        helper_name="Pip",
        helper_type="fox",
        generous_start=True,
        delay=0,
        seed=None,
    ),
]


def explain_rejection(cargo: Cargo, remedy: Remedy) -> str:
    if cargo.risk < RISK_MIN:
        return (
            f"(No story: the {cargo.label} is too easy to carry on an escalator, so there is no honest wobble or lesson about sharing.)"
        )
    if remedy.needs_wide and not cargo.wide:
        return (
            f"(No story: '{remedy.id}' only makes sense for a wide load, and the {cargo.label} is not wide enough for opposite-corner sharing.)"
        )
    if remedy.needs_handles and cargo.handles < remedy.needs_handles:
        return (
            f"(No story: the {cargo.label} does not have enough handles for that remedy.)"
        )
    if remedy.needs_divisible and not cargo.divisible:
        return (
            f"(No story: the {cargo.label} cannot sensibly be divided into smaller shares.)"
        )
    return "(No story: this cargo and remedy do not form a reasonable sharing problem.)"


ASP_RULES = r"""
risky(C) :- cargo(C), risk(C, R), risk_min(M), R >= M.

fits(C, Rm) :- cargo(C), remedy(Rm), wide(C), needs_wide(Rm).
fits(C, Rm) :- cargo(C), remedy(Rm), handles(C, H), needs_handles(Rm, N), H >= N.
fits(C, Rm) :- cargo(C), remedy(Rm), divisible(C), needs_divisible(Rm).

valid(C, Rm) :- risky(C), fits(C, Rm).

severity(S) :- chosen_cargo(C), risk(C, R), delay(D), S = R + D.
outcome(shared_early) :- generous_start.
outcome(steady) :- not generous_start, chosen_remedy(Rm), power(Rm, P), severity(S), P >= S.
outcome(spilled) :- not generous_start, chosen_remedy(Rm), power(Rm, P), severity(S), P < S.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("risk", cargo_id, cargo.risk))
        lines.append(asp.fact("handles", cargo_id, cargo.handles))
        if cargo.wide:
            lines.append(asp.fact("wide", cargo_id))
        if cargo.divisible:
            lines.append(asp.fact("divisible", cargo_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("power", remedy_id, remedy.power))
        if remedy.needs_wide:
            lines.append(asp.fact("needs_wide", remedy_id))
        if remedy.needs_handles:
            lines.append(asp.fact("needs_handles", remedy_id, remedy.needs_handles))
        if remedy.needs_divisible:
            lines.append(asp.fact("needs_divisible", remedy_id))
    lines.append(asp.fact("risk_min", RISK_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("delay", params.delay),
            asp.fact("generous_start") if params.generous_start else "",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def _smoke_emit(sample: StorySample) -> None:
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable-like storyworld: two friends, an escalator, a wobbling load, and a lesson in sharing."
    )
    ap.add_argument("--cargo", choices=sorted(CARGO))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--generous-start", action="store_true", help="start with sharing already chosen")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the proud friend waits before accepting help")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid cargo/remedy pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_animals(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    first, second = rng.sample(ANIMALS, 2)
    return first, second


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.cargo not in CARGO:
        raise StoryError(f"(No story: unknown cargo '{args.cargo}'.)")
    if args.remedy and args.remedy not in REMEDIES:
        raise StoryError(f"(No story: unknown remedy '{args.remedy}'.)")

    if args.cargo and args.remedy:
        cargo = CARGO[args.cargo]
        remedy = REMEDIES[args.remedy]
        if not remedy_fits(cargo, remedy) or cargo.risk < RISK_MIN:
            raise StoryError(explain_rejection(cargo, remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.remedy is None or combo[1] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, remedy_id = rng.choice(sorted(combos))
    (holder_name, holder_type), (helper_name, helper_type) = _pick_animals(rng)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    generous_start = bool(args.generous_start) or (rng.random() < 0.2)
    if generous_start:
        delay = 0
    return StoryParams(
        cargo=cargo_id,
        remedy=remedy_id,
        holder_name=holder_name,
        holder_type=holder_type,
        helper_name=helper_name,
        helper_type=helper_type,
        generous_start=generous_start,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGO:
        raise StoryError(f"(No story: unknown cargo '{params.cargo}'.)")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(No story: unknown remedy '{params.remedy}'.)")
    cargo = CARGO[params.cargo]
    remedy = REMEDIES[params.remedy]
    if not remedy_fits(cargo, remedy) or cargo.risk < RISK_MIN:
        raise StoryError(explain_rejection(cargo, remedy))

    world = tell(
        cargo=cargo,
        remedy=remedy,
        holder_name=params.holder_name,
        holder_type=params.holder_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        generous_start=params.generous_start,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cargo, remedy) pairs:\n")
        for cargo_id, remedy_id in combos:
            print(f"  {cargo_id:12} {remedy_id}")
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
            header = f"### {p.holder_name} & {p.helper_name}: {p.cargo} with {p.remedy} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
