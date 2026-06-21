#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/volcano_oxygen_amigo_moral_value_sharing_magic.py
==============================================================================

A standalone story world for a tiny animal-story domain about a glowing volcano,
thin air, a magical source of oxygen, and two friends learning that sharing can
turn a scary moment into a safe adventure.

Premise
-------
Two young animal friends climb a gentle volcano path to see a magical glow at
sunset. One of them carries a magic object that can make extra oxygen bubbles in
the smoky air. At first the carrier wants to keep the bubbles all to themself.
Then the friend starts struggling to breathe. The turn is state-driven: fear and
care rise, the carrier decides to share, and the world changes from danger to
safe wonder. Some variants are near-miss stories where the friends turn back
wisely instead of reaching the top.

The model keeps:
- physical meters: breath, smoke, safety, glow, progress
- emotional memes: joy, fear, greed, care, trust, gratitude, lesson

Reasonableness constraint
-------------------------
Not every magic item is a good fit for every smoke level. A valid story requires
a magic item whose oxygen power can handle the chosen hazard if it is shared. The
world also refuses impossible hazards.

Run it
------
    python storyworlds/worlds/gpt-5.4/volcano_oxygen_amigo_moral_value_sharing_magic.py
    python storyworlds/worlds/gpt-5.4/volcano_oxygen_amigo_moral_value_sharing_magic.py --peak ember_rim --hazard ash_puff --magic bubble_fern
    python storyworlds/worlds/gpt-5.4/volcano_oxygen_amigo_moral_value_sharing_magic.py --hazard choking_smoke
    python storyworlds/worlds/gpt-5.4/volcano_oxygen_amigo_moral_value_sharing_magic.py --all
    python storyworlds/worlds/gpt-5.4/volcano_oxygen_amigo_moral_value_sharing_magic.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/volcano_oxygen_amigo_moral_value_sharing_magic.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/volcano_oxygen_amigo_moral_value_sharing_magic.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"          # fox | rabbit | item | place | elder ...
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain knobs
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


@dataclass
class Peak:
    id: str
    label: str
    path: str
    crater: str
    sky: str
    glow: str
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
class Hazard:
    id: str
    label: str
    smoke_text: str
    severity: int
    breath_word: str
    safe_move: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
    magic_text: str
    power: int
    shared_bonus: int
    gift_text: str
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
class Guide:
    id: str
    label: str
    species: str
    warning: str
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
class KidSpec:
    species: str
    name: str
    traits: list[str]
    color: str = ""


# ---------------------------------------------------------------------------
# World model
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.characters() if e.role in {"carrier", "friend"}]

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


def _r_smoke_hurts(world: World) -> list[str]:
    out: list[str] = []
    smoke = world.get("air").meters["smoke"]
    for kid in world.kids():
        if smoke < THRESHOLD:
            continue
        if kid.attrs.get("breathing_help", 0) >= smoke:
            continue
        sig = ("smoke_hurts", kid.id, int(smoke), int(kid.attrs.get("breathing_help", 0)))
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.meters["breath"] += 1
        kid.memes["fear"] += 1
        out.append("__breath__")
    return out


def _r_share_relief(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("shared"):
        return out
    for kid in world.kids():
        if kid.meters["breath"] < THRESHOLD:
            continue
        sig = ("share_relief", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.meters["breath"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["gratitude"] += 1
        out.append("__relief__")
    return out


def _r_arrival_wonder(world: World) -> list[str]:
    out: list[str] = []
    if world.get("path").meters["progress"] < THRESHOLD:
        return out
    if world.get("air").meters["safe"] < THRESHOLD:
        return out
    sig = ("arrival_wonder",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    world.get("peak").meters["glow"] += 1
    out.append("__arrival__")
    return out


CAUSAL_RULES = [
    Rule(name="smoke_hurts", tag="physical", apply=_r_smoke_hurts),
    Rule(name="share_relief", tag="social", apply=_r_share_relief),
    Rule(name="arrival_wonder", tag="resolution", apply=_r_arrival_wonder),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def effective_oxygen(item: MagicItem) -> int:
    return item.power + item.shared_bonus


def valid_magic_for_hazard(item: MagicItem, hazard: Hazard) -> bool:
    return effective_oxygen(item) >= hazard.severity


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for peak_id in PEAKS:
        for hazard_id, hazard in HAZARDS.items():
            for magic_id, magic in MAGIC_ITEMS.items():
                if not valid_magic_for_hazard(magic, hazard):
                    continue
                for guide_id in GUIDES:
                    combos.append((peak_id, hazard_id, magic_id, guide_id))
    return combos


def explain_rejection(hazard: Hazard, magic: MagicItem) -> str:
    return (
        f"(No story: {magic.phrase} cannot make enough oxygen for {hazard.label}. "
        f"It can handle strength {effective_oxygen(magic)}, but this smoke needs "
        f"{hazard.severity}. Pick gentler smoke or stronger magic.)"
    )


def sharing_can_reach_top(params: "StoryParams") -> bool:
    hazard = HAZARDS[params.hazard]
    magic = MAGIC_ITEMS[params.magic]
    return effective_oxygen(magic) >= hazard.severity


def outcome_of(params: "StoryParams") -> str:
    if params.share_style == "early":
        return "shared_top"
    if params.share_style == "late":
        return "shared_top" if sharing_can_reach_top(params) else "shared_turn_back"
    return "turn_back"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_without_sharing(world: World) -> dict:
    sim = world.copy()
    sim.facts["shared"] = False
    sim.get("air").meters["safe"] = 0.0
    for kid in sim.kids():
        kid.attrs["breathing_help"] = 0
    propagate(sim, narrate=False)
    struggling = [kid.id for kid in sim.kids() if kid.meters["breath"] >= THRESHOLD]
    return {
        "struggling": struggling,
        "danger": len(struggling),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, carrier: Entity, friend: Entity, peak: Peak) -> None:
    carrier.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At the foot of {peak.label}, {carrier.id} and {friend.id} looked up at "
        f"the warm red mountain. It was a volcano, but a sleepy one, and its top "
        f"glimmered under {peak.sky}."
    )
    world.say(
        f"{carrier.id} twitched {carrier.pronoun('possessive')} little nose and said, "
        f'"Come on, amigo, let\'s see the glow before the fireflies wake."'
    )


def give_goal(world: World, peak: Peak) -> None:
    world.say(
        f"They wanted to reach {peak.crater}, where {peak.glow}. The path curled "
        f"up through black stones and bright moss."
    )


def gift_magic(world: World, guide: Entity, carrier: Entity, magic: MagicItem) -> None:
    carrier.attrs["owns_magic"] = True
    carrier.attrs["breathing_help"] = 0
    world.say(
        f"Before they began, {guide.id} the {guide.type} gave {carrier.id} "
        f"{magic.phrase}. {magic.gift_text}"
    )
    world.say(
        f'"Remember," {guide.id} said, "{guide.attrs["warning"]}"'
    )


def start_climb(world: World, peak: Peak, hazard: Hazard) -> None:
    world.get("path").meters["progress"] += 1
    world.say(
        f"Up they went along {peak.path}. Soon {hazard.smoke_text}, and the air "
        f"felt short on oxygen."
    )


def first_greed(world: World, carrier: Entity, friend: Entity, magic: MagicItem) -> None:
    carrier.memes["greed"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{carrier.id} held {magic.label} close. {carrier.pronoun().capitalize()} liked "
        f"the shimmer so much that {carrier.pronoun()} did not offer it right away."
    )
    world.say(
        f'{friend.id} smiled and stayed near. "{carrier.id}, that magic looks lovely," '
        f"{friend.pronoun()} said."
    )


def smoke_tightens(world: World, carrier: Entity, friend: Entity, hazard: Hazard) -> None:
    world.get("air").meters["smoke"] = float(hazard.severity)
    for kid in world.kids():
        kid.attrs["breathing_help"] = 0
    propagate(world, narrate=False)
    if friend.meters["breath"] >= THRESHOLD:
        world.say(
            f"But the smoke grew thicker. {friend.id} slowed down and took "
            f"{hazard.breath_word} breaths."
        )
    else:
        world.say(
            f"The smoky air brushed their faces, but they still padded on carefully."
        )
    if carrier.meters["breath"] >= THRESHOLD:
        world.say(
            f"Even {carrier.id} felt {carrier.pronoun('possessive')} chest squeeze a little."
        )


def warning_choice(world: World, guide: Entity, carrier: Entity, friend: Entity, magic: MagicItem) -> None:
    pred = predict_without_sharing(world)
    world.facts["predicted_danger"] = pred["danger"]
    if pred["struggling"]:
        names = " and ".join(pred["struggling"])
        world.say(
            f"{carrier.id} remembered what {guide.id} had said. Without sharing the "
            f"magic, {names} could not breathe easily."
        )
    else:
        world.say(
            f"{carrier.id} remembered {guide.id}'s warning and looked at the glowing magic again."
        )
    world.say(
        f"{carrier.id} could make {magic.magic_text}, but only if {carrier.pronoun()} opened "
        f"{carrier.pronoun('possessive')} paw instead of closing it."
    )


def share_early(world: World, carrier: Entity, friend: Entity, magic: MagicItem) -> None:
    world.facts["shared"] = True
    help_power = effective_oxygen(magic)
    for kid in world.kids():
        kid.attrs["breathing_help"] = help_power
    world.get("air").meters["safe"] = 1.0
    carrier.memes["care"] += 1
    carrier.memes["lesson"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{carrier.id} stopped at once. "A real amigo shares," {carrier.pronoun()} said.'
    )
    world.say(
        f"{carrier.pronoun().capitalize()} lifted {magic.label}, and {magic.magic_text} "
        f"rose around both friends like clear blue marbles."
    )
    propagate(world, narrate=False)


def share_late(world: World, carrier: Entity, friend: Entity, magic: MagicItem) -> None:
    world.facts["shared"] = True
    help_power = effective_oxygen(magic)
    for kid in world.kids():
        kid.attrs["breathing_help"] = help_power
    world.get("air").meters["safe"] = 1.0 if help_power >= int(world.get("air").meters["smoke"]) else 0.0
    carrier.memes["care"] += 1
    carrier.memes["lesson"] += 1
    carrier.memes["greed"] = 0.0
    friend.memes["gratitude"] += 1
    world.say(
        f"When {carrier.id} heard {friend.id}'s breathing turn small and shaky, "
        f"{carrier.pronoun()} felt a hard pinch in {carrier.pronoun('possessive')} heart."
    )
    world.say(
        f'"Oh, amigo, this magic is not just for me," {carrier.id} said.'
    )
    world.say(
        f"{carrier.pronoun().capitalize()} opened {carrier.pronoun('possessive')} paw, and "
        f"{magic.magic_text} floated around them together."
    )
    propagate(world, narrate=False)


def choose_turn_back(world: World, carrier: Entity, friend: Entity, hazard: Hazard) -> None:
    world.get("air").meters["safe"] = 1.0
    for kid in world.kids():
        kid.meters["breath"] = 0.0
        kid.memes["relief"] += 1
    carrier.memes["care"] += 1
    carrier.memes["lesson"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f"The path above was still too smoky, so the two friends did not march on just to be brave."
    )
    world.say(
        f"Instead they {hazard.safe_move}, side by side, until the air felt easy again."
    )


def reach_glow(world: World, peak: Peak, carrier: Entity, friend: Entity) -> None:
    world.get("path").meters["progress"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With enough oxygen around them, {carrier.id} and {friend.id} climbed the last bend to {peak.crater}."
    )
    world.say(
        f"There they saw {peak.glow}. The light painted their whiskers gold and made the volcano look kind instead of scary."
    )


def closing_lesson_top(world: World, carrier: Entity, friend: Entity, guide: Entity) -> None:
    carrier.memes["gratitude"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f'{friend.id} leaned against {carrier.id} and whispered, "Thank you for sharing, amigo."'
    )
    world.say(
        f"When they came down, {guide.id} smiled to hear the tale. From then on, both friends knew that magic shines brightest when it is shared."
    )


def closing_lesson_turn_back(world: World, carrier: Entity, friend: Entity, guide: Entity) -> None:
    world.say(
        f"At a low warm rock, they watched the mountain glow from a safe distance instead."
    )
    world.say(
        f'{friend.id} said, "We did not reach the top, but you still shared, amigo." '
        f"{guide.id} nodded when they returned, proud that they had chosen caring over showing off."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    peak: Peak,
    hazard: Hazard,
    magic: MagicItem,
    guide_cfg: Guide,
    carrier_spec: KidSpec,
    friend_spec: KidSpec,
    share_style: str = "late",
) -> World:
    world = World()

    carrier = world.add(
        Entity(
            id=carrier_spec.name,
            kind="character",
            type=carrier_spec.species,
            role="carrier",
            traits=list(carrier_spec.traits),
            attrs={"owns_magic": False, "breathing_help": 0},
            tags={carrier_spec.species},
        )
    )
    friend = world.add(
        Entity(
            id=friend_spec.name,
            kind="character",
            type=friend_spec.species,
            role="friend",
            traits=list(friend_spec.traits),
            attrs={"breathing_help": 0},
            tags={friend_spec.species},
        )
    )
    guide = world.add(
        Entity(
            id=guide_cfg.label,
            kind="character",
            type=guide_cfg.species,
            role="guide",
            attrs={"warning": guide_cfg.warning},
            tags=set(guide_cfg.tags),
        )
    )
    world.add(Entity(id="air", type="air", label="the air"))
    world.add(Entity(id="path", type="path", label="the path"))
    world.add(Entity(id="peak", type="peak", label=peak.label))

    world.facts.update(
        peak=peak,
        hazard=hazard,
        magic=magic,
        guide_cfg=guide_cfg,
        carrier=carrier,
        friend=friend,
        guide=guide,
        shared=False,
        share_style=share_style,
    )

    introduce(world, carrier, friend, peak)
    give_goal(world, peak)

    world.para()
    gift_magic(world, guide, carrier, magic)
    start_climb(world, peak, hazard)
    first_greed(world, carrier, friend, magic)
    smoke_tightens(world, carrier, friend, hazard)
    warning_choice(world, guide, carrier, friend, magic)

    world.para()
    if share_style == "early":
        share_early(world, carrier, friend, magic)
        reach_glow(world, peak, carrier, friend)
        closing_lesson_top(world, carrier, friend, guide)
        outcome = "shared_top"
    elif share_style == "late":
        share_late(world, carrier, friend, magic)
        if effective_oxygen(magic) >= hazard.severity:
            reach_glow(world, peak, carrier, friend)
            closing_lesson_top(world, carrier, friend, guide)
            outcome = "shared_top"
        else:
            choose_turn_back(world, carrier, friend, hazard)
            closing_lesson_turn_back(world, carrier, friend, guide)
            outcome = "shared_turn_back"
    else:
        raise StoryError(f"(Unknown share style: {share_style})")

    world.facts.update(
        outcome=outcome,
        reached_top=outcome == "shared_top",
        turned_back=outcome == "shared_turn_back",
        struggling=friend.meters["breath"] >= THRESHOLD or carrier.meters["breath"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PEAKS = {
    "ember_rim": Peak(
        id="ember_rim",
        label="Ember Rim",
        path="a soft zigzag trail of cinders",
        crater="the little rim near the top",
        sky="a peach-colored evening sky",
        glow="tiny rivers of red light slid under the stone like sleeping fire",
        tags={"volcano"},
    ),
    "mango_mountain": Peak(
        id="mango_mountain",
        label="Mango Mountain",
        path="a curvy path between warm orange rocks",
        crater="the bright top ledge",
        sky="a lavender evening sky",
        glow="the cracks in the stone glowed like jam in a pie crust",
        tags={"volcano"},
    ),
    "spark_nest": Peak(
        id="spark_nest",
        label="Spark Nest",
        path="a narrow path with shiny black pebbles",
        crater="the nest-shaped lookout",
        sky="a blue-and-gold sunset",
        glow="a ring of molten light winked deep below, gentle as a lantern",
        tags={"volcano"},
    ),
}

HAZARDS = {
    "misty_steam": Hazard(
        id="misty_steam",
        label="misty steam",
        smoke_text="a little ribbon of warm steam drifted across the path",
        severity=1,
        breath_word="slow",
        safe_move="sat on a low stone and waited for the steam to pass",
        tags={"steam", "oxygen"},
    ),
    "ash_puff": Hazard(
        id="ash_puff",
        label="an ash puff",
        smoke_text="a gray puff of ash rolled out and tickled their throats",
        severity=2,
        breath_word="short",
        safe_move="padded down to a cleaner bend in the path",
        tags={"ash", "oxygen"},
    ),
    "choking_smoke": Hazard(
        id="choking_smoke",
        label="choking smoke",
        smoke_text="a thick smoky cloud curled over the stones and dimmed the sunset",
        severity=3,
        breath_word="tiny",
        safe_move="hurried back to the spring at the foot of the hill",
        tags={"smoke", "oxygen"},
    ),
}

MAGIC_ITEMS = {
    "bubble_fern": MagicItem(
        id="bubble_fern",
        label="the bubble fern",
        phrase="a bubble fern tucked in a shell cup",
        magic_text="bright round bubbles of cool oxygen",
        power=1,
        shared_bonus=1,
        gift_text="Its leaves trembled with blue light.",
        tags={"magic", "oxygen", "sharing"},
    ),
    "moon_pearl": MagicItem(
        id="moon_pearl",
        label="the moon pearl",
        phrase="a moon pearl on a moss string",
        magic_text="silver breaths of clean oxygen",
        power=2,
        shared_bonus=1,
        gift_text="It hummed softly, as if the night sky were singing inside it.",
        tags={"magic", "oxygen", "sharing"},
    ),
    "star_lantern": MagicItem(
        id="star_lantern",
        label="the star lantern",
        phrase="a star lantern no bigger than an apple",
        magic_text="golden floating beads of fresh oxygen",
        power=3,
        shared_bonus=1,
        gift_text="Every tiny window on it glittered with sleepy starlight.",
        tags={"magic", "oxygen", "sharing"},
    ),
}

GUIDES = {
    "tortoise": Guide(
        id="tortoise",
        label="Toma",
        species="tortoise",
        warning="magic is strongest when friends share it",
        tags={"elder", "sharing"},
    ),
    "parrot": Guide(
        id="parrot",
        label="Pico",
        species="parrot",
        warning="if the air grows thin, share first and climb second",
        tags={"elder", "sharing"},
    ),
    "lemur": Guide(
        id="lemur",
        label="Mimi",
        species="lemur",
        warning="a kind paw makes brave magic",
        tags={"elder", "sharing"},
    ),
}

CARRIER_SPECS = [
    KidSpec(species="fox", name="Fifi", traits=["quick", "bright"]),
    KidSpec(species="rabbit", name="Nuno", traits=["springy", "eager"]),
    KidSpec(species="otter", name="Lolo", traits=["curious", "playful"]),
    KidSpec(species="mouse", name="Pip", traits=["small", "hopeful"]),
]

FRIEND_SPECS = [
    KidSpec(species="panda", name="Bobo", traits=["gentle", "patient"]),
    KidSpec(species="deer", name="Dina", traits=["careful", "sweet"]),
    KidSpec(species="capybara", name="Rumi", traits=["calm", "warm"]),
    KidSpec(species="badger", name="Tavi", traits=["steady", "loyal"]),
]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    peak: str
    hazard: str
    magic: str
    guide: str
    carrier_species: str
    carrier_name: str
    friend_species: str
    friend_name: str
    share_style: str = "late"
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
    "volcano": [
        (
            "What is a volcano?",
            "A volcano is a mountain with hot melted rock deep inside it. Sometimes it lets out steam, ash, or glowing lava."
        )
    ],
    "oxygen": [
        (
            "What is oxygen?",
            "Oxygen is part of the air that animals and people breathe. Your body needs oxygen so you can keep moving and feeling strong."
        )
    ],
    "sharing": [
        (
            "Why is sharing important?",
            "Sharing lets more than one friend have what they need. It can turn a problem into something kinder and safer for everyone."
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is a special power that can do surprising things. It often helps show a big feeling or lesson in a bright way."
        )
    ],
    "ash": [
        (
            "Why can ash and smoke make breathing hard?",
            "Ash and smoke can bother your nose and throat and make the air feel dirty. That is why it can feel harder to take a good breath."
        )
    ],
    "elder": [
        (
            "Why do young ones listen to an elder in a story?",
            "An elder has lived through more things and often gives careful advice. Listening can keep everyone safe when a choice gets tricky."
        )
    ],
}
KNOWLEDGE_ORDER = ["volcano", "oxygen", "sharing", "magic", "ash", "elder"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    carrier = f["carrier"]
    friend = f["friend"]
    peak = f["peak"]
    magic = f["magic"]
    hazard = f["hazard"]
    outcome = f["outcome"]
    if outcome == "shared_turn_back":
        return [
            f'Write a gentle animal story for ages 3 to 5 that includes the words "volcano", "oxygen", and "amigo".',
            f"Tell a magical story where {carrier.id} and {friend.id} climb {peak.label}, share {magic.label}, but wisely turn back when {hazard.label} stays too thick.",
            "Write a story about sharing where friends choose safety over showing off, and the lesson still feels warm and happy.",
        ]
    return [
        f'Write a gentle animal story for ages 3 to 5 that includes the words "volcano", "oxygen", and "amigo".',
        f"Tell a magical sharing story where {carrier.id} first wants to keep {magic.label}, then shares it with {friend.id} on a volcano path.",
        "Write a child-facing animal story with a clear moral that magic becomes stronger when it is shared.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    carrier = f["carrier"]
    friend = f["friend"]
    guide = f["guide"]
    peak = f["peak"]
    hazard = f["hazard"]
    magic = f["magic"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {carrier.id} the {carrier.type} and {friend.id} the {friend.type}. They are two young animal friends climbing a volcano together."
        ),
        (
            "What magic did they have?",
            f"They had {magic.label}, which could make {magic.magic_text}. The magic mattered because the smoky air felt short on oxygen."
        ),
        (
            f"Why did the climb become hard?",
            f"The climb became hard when {hazard.smoke_text}. That made the air feel thin and made breathing harder for the friends."
        ),
        (
            f"Why did {carrier.id} decide to share?",
            f"{carrier.id} first held the magic close, but then noticed that the smoky air was hurting {friend.id}. Remembering {guide.id}'s warning helped {carrier.pronoun('object')} choose care over keeping the magic alone."
        ),
    ]
    if outcome == "shared_top":
        qa.append(
            (
                "How did sharing change the story?",
                f"Sharing gave both friends enough oxygen to keep climbing safely. Because of that, they reached {peak.crater} and saw the warm glow together."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                "The moral is that sharing can be a brave kind of magic. When a friend needs help, kindness can change fear into safety and joy."
            )
        )
    else:
        qa.append(
            (
                "Did they reach the top?",
                f"No, they turned back safely when the path stayed too smoky. Even so, the sharing still mattered because it helped them breathe and make a wise choice together."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                "The moral is that sharing is good, and being wise is good too. A caring friend does not have to prove anything by pushing into danger."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"volcano", "oxygen", "sharing", "magic", "elder"}
    if f["hazard"].id in {"ash_puff", "choking_smoke"}:
        tags.add("ash")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v not in (0, "", None, False)}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        peak="ember_rim",
        hazard="misty_steam",
        magic="bubble_fern",
        guide="tortoise",
        carrier_species="fox",
        carrier_name="Fifi",
        friend_species="panda",
        friend_name="Bobo",
        share_style="late",
    ),
    StoryParams(
        peak="mango_mountain",
        hazard="ash_puff",
        magic="moon_pearl",
        guide="parrot",
        carrier_species="rabbit",
        carrier_name="Nuno",
        friend_species="deer",
        friend_name="Dina",
        share_style="late",
    ),
    StoryParams(
        peak="spark_nest",
        hazard="choking_smoke",
        magic="star_lantern",
        guide="lemur",
        carrier_species="otter",
        carrier_name="Lolo",
        friend_species="capybara",
        friend_name="Rumi",
        share_style="late",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Peak, Hazard, Magic, Guide) :-
    peak(Peak), hazard(Hazard), magic(Magic), guide(Guide),
    severity(Hazard, S), power(Magic, P), shared_bonus(Magic, B), P + B >= S.

reach_top(Peak, Hazard, Magic, Guide, early) :-
    valid(Peak, Hazard, Magic, Guide).
reach_top(Peak, Hazard, Magic, Guide, late) :-
    valid(Peak, Hazard, Magic, Guide).

outcome(shared_top) :-
    chosen_peak(Peak), chosen_hazard(Hazard), chosen_magic(Magic),
    chosen_guide(Guide), share_style(Style),
    reach_top(Peak, Hazard, Magic, Guide, Style).

outcome(shared_turn_back) :-
    chosen_peak(Peak), chosen_hazard(Hazard), chosen_magic(Magic),
    chosen_guide(Guide), share_style(Style),
    valid(Peak, Hazard, Magic, Guide),
    not reach_top(Peak, Hazard, Magic, Guide, Style).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for peak_id in PEAKS:
        lines.append(asp.fact("peak", peak_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("severity", hazard_id, hazard.severity))
    for magic_id, magic in MAGIC_ITEMS.items():
        lines.append(asp.fact("magic", magic_id))
        lines.append(asp.fact("power", magic_id, magic.power))
        lines.append(asp.fact("shared_bonus", magic_id, magic.shared_bonus))
    for guide_id in GUIDES:
        lines.append(asp.fact("guide", guide_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_peak", params.peak),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_magic", params.magic),
            asp.fact("chosen_guide", params.guide),
            asp.fact("share_style", params.share_style),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"Smoke test failed: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a volcano climb, magical oxygen, and a lesson about sharing."
    )
    ap.add_argument("--peak", choices=PEAKS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--share-style", choices=["early", "late"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_two_specs(rng: random.Random) -> tuple[KidSpec, KidSpec]:
    carrier = copy.deepcopy(rng.choice(CARRIER_SPECS))
    friend = copy.deepcopy(rng.choice(FRIEND_SPECS))
    if carrier.name == friend.name:
        friend.name = f"{friend.name}o"
    return carrier, friend


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.magic:
        hazard = HAZARDS[args.hazard]
        magic = MAGIC_ITEMS[args.magic]
        if not valid_magic_for_hazard(magic, hazard):
            raise StoryError(explain_rejection(hazard, magic))

    combos = [
        combo
        for combo in valid_combos()
        if (args.peak is None or combo[0] == args.peak)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.magic is None or combo[2] == args.magic)
        and (args.guide is None or combo[3] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    peak_id, hazard_id, magic_id, guide_id = rng.choice(sorted(combos))
    carrier, friend = _pick_two_specs(rng)
    share_style = args.share_style or rng.choice(["late", "early"])
    return StoryParams(
        peak=peak_id,
        hazard=hazard_id,
        magic=magic_id,
        guide=guide_id,
        carrier_species=carrier.species,
        carrier_name=carrier.name,
        friend_species=friend.species,
        friend_name=friend.name,
        share_style=share_style,
    )


def _spec_from_params(species: str, name: str, role: str) -> KidSpec:
    if role == "carrier":
        source = CARRIER_SPECS
    else:
        source = FRIEND_SPECS
    for spec in source:
        if spec.species == species:
            return KidSpec(species=species, name=name, traits=list(spec.traits), color=spec.color)
    raise StoryError(f"(Unknown {role} species: {species})")


def generate(params: StoryParams) -> StorySample:
    if params.peak not in PEAKS:
        raise StoryError(f"(Unknown peak: {params.peak})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.magic not in MAGIC_ITEMS:
        raise StoryError(f"(Unknown magic item: {params.magic})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.share_style not in {"early", "late"}:
        raise StoryError(f"(Unknown share style: {params.share_style})")
    if not valid_magic_for_hazard(MAGIC_ITEMS[params.magic], HAZARDS[params.hazard]):
        raise StoryError(explain_rejection(HAZARDS[params.hazard], MAGIC_ITEMS[params.magic]))

    world = tell(
        peak=PEAKS[params.peak],
        hazard=HAZARDS[params.hazard],
        magic=MAGIC_ITEMS[params.magic],
        guide_cfg=GUIDES[params.guide],
        carrier_spec=_spec_from_params(params.carrier_species, params.carrier_name, "carrier"),
        friend_spec=_spec_from_params(params.friend_species, params.friend_name, "friend"),
        share_style=params.share_style,
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (peak, hazard, magic, guide) combos:\n")
        for peak_id, hazard_id, magic_id, guide_id in combos:
            print(f"  {peak_id:14} {hazard_id:14} {magic_id:12} {guide_id}")
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
                f"### {p.carrier_name} & {p.friend_name}: {p.magic} on {p.peak} "
                f"({p.hazard}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
