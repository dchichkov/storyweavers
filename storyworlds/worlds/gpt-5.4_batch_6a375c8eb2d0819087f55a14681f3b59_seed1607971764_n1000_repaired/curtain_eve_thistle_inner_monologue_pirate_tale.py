#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/curtain_eve_thistle_inner_monologue_pirate_tale.py
=============================================================================

A standalone story world about Captain Eve, a curtain-cave, and a treasure that
gets stuck too high during a pirate game. The world keeps a small simulated
state with physical meters and emotional memes, uses a gentle reasonableness
gate, includes an inline ASP twin, and renders either a near-miss ending or a
scared-then-safe ending.

Seed requirements folded into the world:
- uses the words "curtain", "eve", and "thistle"
- features inner monologue
- keeps a Pirate Tale feel
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


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
    stable: bool = True
    hanging: bool = False
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
class Pretend:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    goal: str
    sendoff: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    cheer: str
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
class Spot:
    id: str
    label: str
    phrase: str
    height: int
    in_curtain: bool
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
class RiskyMove:
    id: str
    label: str
    kind: str
    reach: int
    risk: int
    stable: bool
    action: str
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
class SafeMethod:
    id: str
    label: str
    max_height: int
    text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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
    eve = world.get("eve")
    support = world.entities.get("support")
    if support is None:
        return out
    if eve.meters["climbing"] < THRESHOLD or support.stable:
        return out
    sig = ("wobble", support.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    support.meters["wobble"] += 1
    world.get("room").meters["danger"] += 1
    eve.memes["fear"] += 1
    for kid in world.kids():
        if kid.id != "eve":
            kid.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_loose_curtain(world: World) -> list[str]:
    out: list[str] = []
    curtain = world.get("curtain")
    if curtain.meters["yanked"] < THRESHOLD or not curtain.hanging:
        return out
    sig = ("loose", curtain.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    curtain.meters["loose"] += 1
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__loose__")
    return out


def _r_drop_treasure(world: World) -> list[str]:
    out: list[str] = []
    curtain = world.get("curtain")
    treasure = world.get("treasure")
    if curtain.meters["loose"] < THRESHOLD or treasure.attrs.get("spot") != "rod_fold":
        return out
    sig = ("drop", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.meters["dropped"] += 1
    treasure.attrs["spot"] = "floor"
    out.append("__drop__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="loose_curtain", tag="physical", apply=_r_loose_curtain),
    Rule(name="drop_treasure", tag="physical", apply=_r_drop_treasure),
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


def move_reaches(move: RiskyMove, spot: Spot) -> bool:
    if move.kind == "tug" and not spot.in_curtain:
        return False
    return move.reach >= spot.height


def method_reaches(method: SafeMethod, spot: Spot) -> bool:
    return method.max_height >= spot.height


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for pretend_id in PRETENDS:
        for treasure_id in TREASURES:
            for spot_id, spot in SPOTS.items():
                for move_id, move in RISKY_MOVES.items():
                    if not move_reaches(move, spot):
                        continue
                    for method_id, method in SAFE_METHODS.items():
                        if method_reaches(method, spot):
                            combos.append((pretend_id, treasure_id, spot_id, move_id, method_id))
    return combos


def compatible_methods(spot_id: str) -> list[str]:
    if spot_id not in SPOTS:
        return []
    spot = SPOTS[spot_id]
    return [mid for mid, method in SAFE_METHODS.items() if method_reaches(method, spot)]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, eve_age: int, mate_age: int, mate_trait: str) -> bool:
    mate_older = relation == "siblings" and mate_age > eve_age
    authority = (initial_caution(mate_trait) + 1.0) + (4.0 if mate_older else 0.0)
    return mate_older and authority > BRAVERY_INIT


def predict_hazard(world: World, move: RiskyMove) -> dict:
    sim = world.copy()
    eve = sim.get("eve")
    if move.kind == "climb":
        eve.meters["climbing"] += 1
    else:
        sim.get("curtain").meters["yanked"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "wobble": sim.entities.get("support").meters["wobble"] if "support" in sim.entities else 0.0,
        "loose": sim.get("curtain").meters["loose"],
        "drop": sim.get("treasure").meters["dropped"],
    }


def play_setup(world: World, pretend: Pretend, mate: Entity, pet: Entity) -> None:
    eve = world.get("eve")
    eve.memes["joy"] += 1
    mate.memes["joy"] += 1
    pet.memes["curious"] += 1
    cap, mate_title = pretend.titles
    world.say(
        f"On a blustery eve, Eve and {mate.id} turned the sitting room into {pretend.scene}. "
        f"{pretend.rig}"
    )
    world.say(
        f'The curtain by the window became the mouth of a hidden sea cave. '
        f'Their orange cat, {pet.id}, whisked through it with a tail puffed up like a little thistle.'
    )
    world.say(
        f'"{cap} Eve and {mate_title} {mate.id}!" Eve cried. '
        f'"Tonight we hunt {pretend.goal}!"'
    )


def lose_treasure(world: World, treasure: Treasure, spot: Spot, pet: Entity) -> None:
    world.get("treasure").attrs["spot"] = spot.id
    world.say(
        f"But when {pet.id} patted at {treasure.phrase}, it slid away and landed {spot.phrase}."
    )
    world.say(
        f'Eve gasped. "{treasure.cheer} It\'s stuck!"'
    )


def inner_thought(world: World, move: RiskyMove, spot: Spot) -> None:
    eve = world.get("eve")
    pred = predict_hazard(world, move)
    world.facts["predicted_danger"] = pred["danger"]
    first = (
        f'Inside her head, Eve thought, "If I {move.action}, I can reach {spot.label} all by myself."'
    )
    if pred["wobble"] >= THRESHOLD:
        second = (
            'Then another thought tapped back, "But wobbly things scoot like sneaky waves."'
        )
    elif pred["loose"] >= THRESHOLD:
        second = (
            'Then another thought tapped back, "But the curtain might yank the whole cave down with it."'
        )
    else:
        second = (
            'Then another thought tapped back, "Easy plans do not always stay easy."'
        )
    eve.memes["thinking"] += 1
    world.say(first)
    world.say(second)


def mate_warn(world: World, mate: Entity, move: RiskyMove, spot: Spot, parent: Entity) -> None:
    mate.memes["caution"] += 1
    if move.kind == "climb":
        detail = "that thing rocks under your feet"
    else:
        detail = "the curtain rod could rattle loose"
    world.say(
        f'{mate.id} lowered {mate.pronoun("possessive")} pirate voice. '
        f'"Wait, Eve. {move.warning}, and {detail}. Let\'s call {parent.label_word} instead."'
    )


def back_down(world: World, mate: Entity, parent: Entity) -> None:
    eve = world.get("eve")
    eve.memes["relief"] += 1
    mate.memes["relief"] += 1
    eve.memes["bravery"] = 0.0
    world.say(
        f'Eve took one breath, then another. Inside her head, she thought, '
        f'"Real captains do not have to do every hard thing alone."'
    )
    world.say(
        f'So she stepped back from the curtain-cave and called, "{parent.label_word.capitalize()}, can you help our ship?"'
    )


def attempt_move(world: World, move: RiskyMove) -> None:
    eve = world.get("eve")
    support = world.entities.get("support")
    if move.kind == "climb":
        eve.meters["climbing"] += 1
        eve.memes["defiance"] += 1
        if support is not None:
            support.meters["used"] += 1
    else:
        world.get("curtain").meters["yanked"] += 1
        eve.memes["defiance"] += 1
    propagate(world, narrate=False)


def scare(world: World, move: RiskyMove, spot: Spot, treasure: Treasure, mate: Entity) -> None:
    support = world.entities.get("support")
    curtain = world.get("curtain")
    treasure_ent = world.get("treasure")
    if move.kind == "climb" and support is not None and support.meters["wobble"] >= THRESHOLD:
        world.say(
            f"Eve tried to {move.action}, but the {move.label} gave a sly little wiggle. "
            f"Her pirate grin vanished at once."
        )
        world.say(
            f'"Eve!" {mate.id} cried, as the room seemed to tip like a deck in rough water.'
        )
    elif curtain.meters["loose"] >= THRESHOLD:
        world.say(
            f"Eve tugged hard. The curtain hissed along its ring, and the rod above gave a sharp clack."
        )
        if treasure_ent.meters["dropped"] >= THRESHOLD:
            world.say(
                f"The {treasure.label} plopped to the floor, but the cave no longer felt playful."
            )
        else:
            world.say(
                f"The cloth sagged and swayed, and suddenly even the treasure looked less important than staying safe."
            )
    else:
        world.say(
            f"Eve tried to {move.action}, but the brave idea felt much smaller once it was happening."
        )
    world.say(
        f'Inside her head, Eve thought, "This is not the kind of pirate surprise I wanted."'
    )


def call_for_help(world: World, mate: Entity, parent: Entity) -> None:
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.say(f'"{parent.label_word.upper()}!" Eve and {mate.id} shouted together.')


def rescue(world: World, parent: Entity, method: SafeMethod, spot: Spot, treasure: Treasure) -> None:
    eve = world.get("eve")
    mate = next(k for k in world.kids() if k.id != "eve")
    world.get("room").meters["danger"] = 0.0
    world.get("curtain").meters["loose"] = 0.0
    if "support" in world.entities:
        world.get("support").meters["wobble"] = 0.0
    world.get("treasure").attrs["spot"] = "retrieved"
    eve.memes["fear"] = 0.0
    mate.memes["fear"] = 0.0
    eve.memes["relief"] += 1
    mate.memes["relief"] += 1
    eve.memes["lesson"] += 1
    mate.memes["lesson"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came in fast, saw the trouble at the curtain, and {method.text}."
    )
    world.say(
        f'In a blink, the {treasure.label} was safe in {parent.pronoun("possessive")} hand instead of stranded {spot.phrase}.'
    )


def lesson(world: World, parent: Entity, move: RiskyMove) -> None:
    eve = world.get("eve")
    mate = next(k for k in world.kids() if k.id != "eve")
    world.say(
        f'Then {parent.label_word} crouched beside them. "I am glad you called me," '
        f'{parent.pronoun()} said softly. "A game can stay a game only when everyone stays safe."'
    )
    if move.kind == "climb":
        world.say(
            f'"Next time, no climbing on {move.label} for treasure," {parent.pronoun()} added. '
            f'"Ships need steady decks."'
        )
    else:
        world.say(
            f'"Next time, no yanking the curtain for treasure," {parent.pronoun()} added. '
            f'"Caves made of cloth can tumble down."'
        )
    world.say(
        f'Eve nodded. Inside her head, she thought, "Calling for help can be part of being brave." '
        f'{mate.id} nodded too.'
    )


def safe_end(world: World, pretend: Pretend, treasure: Treasure, parent: Entity, method: SafeMethod, pet: Entity) -> None:
    eve = world.get("eve")
    mate = next(k for k in world.kids() if k.id != "eve")
    eve.memes["joy"] += 1
    mate.memes["joy"] += 1
    eve.memes["safety"] += 1
    mate.memes["safety"] += 1
    world.say(
        f'Soon the treasure was back on the rug, the curtain was tied neatly aside, and {parent.label_word} stayed to watch the game.'
    )
    world.say(
        f'Eve spread out the {treasure.label} again. This time she smiled and said, '
        f'"A wise crew uses safe tools first."'
    )
    world.say(
        f'{mate.id} tapped the map, {pet.id} curled beside it, and the little pirate crew {pretend.sendoff} with quieter feet and brighter hearts.'
    )
    world.facts["ending_image"] = f"{pet.id} curled beside the {treasure.label}"


def tell(
    pretend: Pretend,
    treasure: Treasure,
    spot: Spot,
    move: RiskyMove,
    method: SafeMethod,
    *,
    mate_name: str,
    mate_gender: str,
    mate_trait: str,
    parent_type: str,
    relation: str,
    eve_age: int,
    mate_age: int,
) -> World:
    world = World()
    eve = world.add(Entity(
        id="Eve",
        kind="character",
        type="girl",
        label="Eve",
        role="captain",
        age=eve_age,
        attrs={"relation": relation},
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        label=mate_name,
        role="mate",
        age=mate_age,
        traits=[mate_trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    pet = world.add(Entity(
        id="Thistle",
        kind="character",
        type="cat",
        label="Thistle",
        role="pet",
    ))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="curtain", type="curtain", label="curtain", hanging=True))
    world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure.label,
        attrs={"spot": "", "treasure_id": treasure.id},
    ))
    if move.kind == "climb":
        world.add(Entity(
            id="support",
            type="support",
            label=move.label,
            stable=move.stable,
            attrs={"move_id": move.id},
        ))
    else:
        world.add(Entity(
            id="support",
            type="support",
            label="floor",
            stable=True,
            attrs={"move_id": move.id},
        ))

    eve.memes["bravery"] = BRAVERY_INIT
    mate.memes["caution"] = initial_caution(mate_trait)

    play_setup(world, pretend, mate, pet)
    lose_treasure(world, treasure, spot, pet)

    world.para()
    inner_thought(world, move, spot)
    mate_warn(world, mate, move, spot, parent)

    averted = would_avert(relation, eve_age, mate_age, mate_trait)
    if averted:
        back_down(world, mate, parent)
        world.para()
        rescue(world, parent, method, spot, treasure)
        lesson(world, parent, move)
        world.para()
        safe_end(world, pretend, treasure, parent, method, pet)
        outcome = "averted"
    else:
        world.say(f'Eve lifted her chin. "Fast hands for the captain," she said.')
        world.para()
        attempt_move(world, move)
        scare(world, move, spot, treasure, mate)
        call_for_help(world, mate, parent)
        world.para()
        rescue(world, parent, method, spot, treasure)
        lesson(world, parent, move)
        world.para()
        safe_end(world, pretend, treasure, parent, method, pet)
        outcome = "rescued"

    world.facts.update(
        pretend=pretend,
        treasure_cfg=treasure,
        spot_cfg=spot,
        move_cfg=move,
        method_cfg=method,
        eve=eve,
        mate=mate,
        parent=parent,
        pet=pet,
        relation=relation,
        outcome=outcome,
        averted=averted,
        danger_seen=world.get("room").meters["danger"] <= 0.0,
        curtain_wobbled=world.get("curtain").meters["loose"] >= THRESHOLD or ("loose", "curtain") in world.fired,
        support_wobbled=world.get("support").meters["wobble"] >= THRESHOLD or ("wobble", "support") in world.fired,
        treasure_dropped=world.get("treasure").meters["dropped"] >= THRESHOLD,
        retrieved=True,
    )
    return world


PRETENDS = {
    "pirates": Pretend(
        id="pirates",
        scene="a lantern-lit pirate ship riding the window waves",
        rig="The sofa was the captain's deck, a cushion was the treasure chest, and a striped blanket made the stormy sea.",
        titles=("Captain", "Lookout"),
        goal="the silver map",
        sendoff="sailed on with their map spread wide",
    ),
    "corsairs": Pretend(
        id="corsairs",
        scene="a swift corsair ship gliding past dark rocks",
        rig="The armchair was the stern, a broom was the mast, and three pillows made a row of sea-smacked islands.",
        titles=("Captain", "First Mate"),
        goal="the hidden chart",
        sendoff="set course again under the tied-back curtain-cave",
    ),
    "raiders": Pretend(
        id="raiders",
        scene="a brave raider ship looking for a moonlit harbor",
        rig="The ottoman was the prow, a scarf was the sail, and a wooden spoon became the helm.",
        titles=("Captain", "Mate"),
        goal="the harbor mark",
        sendoff="finished the voyage with safer pirate tricks",
    ),
}

TREASURES = {
    "map": Treasure(
        id="map",
        label="map",
        phrase="their crinkly silver map",
        cheer="The map",
        tags={"map", "pirate"},
    ),
    "spyglass": Treasure(
        id="spyglass",
        label="spyglass",
        phrase="their cardboard spyglass",
        cheer="The spyglass",
        tags={"spyglass", "pirate"},
    ),
    "key": Treasure(
        id="key",
        label="shell key",
        phrase="their shell key on a blue string",
        cheer="The shell key",
        tags={"key", "pirate"},
    ),
}

SPOTS = {
    "hem": Spot(
        id="hem",
        label="the hem of the curtain",
        phrase="in the hem of the curtain",
        height=1,
        in_curtain=True,
        tags={"curtain"},
    ),
    "sill": Spot(
        id="sill",
        label="the window sill",
        phrase="on the window sill behind the curtain",
        height=2,
        in_curtain=False,
        tags={"window", "curtain"},
    ),
    "rod_fold": Spot(
        id="rod_fold",
        label="the high curtain folds",
        phrase="up in the high folds near the curtain rod",
        height=3,
        in_curtain=True,
        tags={"curtain"},
    ),
}

RISKY_MOVES = {
    "swivel_stool": RiskyMove(
        id="swivel_stool",
        label="swivel stool",
        kind="climb",
        reach=2,
        risk=2,
        stable=False,
        action="hop onto the swivel stool and stretch high",
        warning="That stool has little rolling feet",
        tags={"stool", "climb"},
    ),
    "toy_chest": RiskyMove(
        id="toy_chest",
        label="toy chest",
        kind="climb",
        reach=1,
        risk=2,
        stable=False,
        action="climb onto the toy chest and grab fast",
        warning="The lid of that chest can shift",
        tags={"chest", "climb"},
    ),
    "curtain_tug": RiskyMove(
        id="curtain_tug",
        label="curtain edge",
        kind="tug",
        reach=3,
        risk=3,
        stable=True,
        action="give the curtain a sharp pirate tug",
        warning="Pulling cloth can pull down more than cloth",
        tags={"curtain", "tug"},
    ),
}

SAFE_METHODS = {
    "step_stool": SafeMethod(
        id="step_stool",
        label="step stool",
        max_height=2,
        text="set down a steady step stool, held it firm, and reached the treasure safely",
        qa_text="used a steady step stool and reached the treasure safely",
        tags={"stool", "ask_grownup"},
    ),
    "grabber": SafeMethod(
        id="grabber",
        label="grabber",
        max_height=3,
        text="brought the long grabber from the hall closet and pinched the treasure free",
        qa_text="used a long grabber to pinch the treasure free",
        tags={"grabber", "ask_grownup"},
    ),
    "lift": SafeMethod(
        id="lift",
        label="grown-up lift",
        max_height=3,
        text="lifted Eve up with two careful hands until the treasure was within easy reach",
        qa_text="lifted Eve carefully so she could take the treasure without wobbling",
        tags={"lift", "ask_grownup"},
    ),
}

MATE_NAMES = {
    "girl": ["Lily", "Mia", "Zoe", "Nora", "Ada"],
    "boy": ["Tom", "Ben", "Finn", "Max", "Leo"],
}
MATE_TRAITS = ["careful", "cautious", "steady", "curious", "thoughtful", "sensible"]


@dataclass
class StoryParams:
    pretend: str
    treasure: str
    spot: str
    move: str
    method: str
    mate_name: str
    mate_gender: str
    mate_trait: str
    parent: str
    relation: str = "siblings"
    eve_age: int = 5
    mate_age: int = 6
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
    "curtain": [(
        "What is a curtain?",
        "A curtain is a piece of cloth that hangs by a window. It can block light or make a cozy hiding place, but it is not meant for climbing or tugging."
    )],
    "pirate": [(
        "What is a pirate map in pretend play?",
        "A pirate map is a make-believe chart that shows where treasure might be hidden. Children use it in games to imagine adventures."
    )],
    "stool": [(
        "Why can a stool be unsafe for climbing if it wobbles?",
        "A wobbly stool can slide or tip when you stand on it. That can make you fall before you are ready."
    )],
    "grabber": [(
        "What is a grabber tool?",
        "A grabber is a long tool that helps you pick something up from far away or from high places. It lets a grown-up reach without stretching unsafely."
    )],
    "ask_grownup": [(
        "Why is it smart to ask a grown-up for help reaching something high?",
        "A grown-up can use steadier hands or the right tool. Asking for help keeps the game safe while the problem gets solved."
    )],
    "thistle": [(
        "What is a thistle?",
        "A thistle is a plant with prickly parts and a fuzzy flower head. People sometimes use the word because it sounds sharp or spiky."
    )],
}
KNOWLEDGE_ORDER = ["curtain", "pirate", "stool", "grabber", "ask_grownup", "thistle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pretend = f["pretend"]
    treasure = f["treasure_cfg"]
    move = f["move_cfg"]
    method = f["method_cfg"]
    mate = f["mate"]
    if f["outcome"] == "averted":
        return [
            f'Write a pirate-style story for a 3-to-5-year-old where Eve wants to reach a {treasure.label} by the curtain, but an older child talks her out of it. Include inner thoughts and the word "curtain".',
            f"Tell a gentle near-miss story where Eve listens to {mate.id}, calls a grown-up, and learns that safe help can still feel brave.",
            f'Write a story set on a windy eve with a cat named Thistle, a pretend pirate ship, and a calm ending where {method.label} solves the problem safely.',
        ]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old where Eve tries a risky way to reach a {treasure.label} near the curtain, gets scared, and then a grown-up helps. Include inner thoughts.',
        f"Tell a story where {mate.id} warns Eve, but she still tries to {move.action}; after the scare, the crew learns a safer rule.",
        f'Write a simple pirate tale set on a windy eve with Thistle the cat and a happy ending that proves asking for help can be brave.',
    ]


def pair_noun(eve: Entity, mate: Entity, relation: str) -> str:
    if relation != "siblings":
        return "two friends"
    if mate.type == "girl":
        return "two sisters"
    return "a sister and a brother"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    eve = f["eve"]
    mate = f["mate"]
    parent = f["parent"]
    pet = f["pet"]
    pretend = f["pretend"]
    treasure = f["treasure_cfg"]
    spot = f["spot_cfg"]
    move = f["move_cfg"]
    method = f["method_cfg"]
    relation = f["relation"]
    pair = pair_noun(eve, mate, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, Eve and {mate.id}, and their cat {pet.id}. They are playing pirates when their treasure ends up too high by the curtain."
        ),
        (
            f"Why did the {treasure.label} become a problem?",
            f"{pet.id} batted it away, and it landed {spot.phrase}. That made Eve want a fast pirate solution instead of a safe one."
        ),
        (
            "What do Eve's inner thoughts show?",
            f"They show that Eve wants to be bold, but she also starts to notice the danger. Her thoughts make the choice feel real before anything scary happens."
        ),
        (
            f"Why was {mate.id} worried?",
            f"{mate.id} was worried because {move.warning.lower()}, and the treasure was high enough to tempt a risky move. The warning came before the scare, not after it."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            "What changed Eve's mind?",
            f"{mate.id}'s warning and Eve's own second thought changed her mind. She stepped back and called for {parent.label_word}, which kept the game from turning scary."
        ))
    else:
        if f["support_wobbled"]:
            qa.append((
                "What happened when Eve tried to reach the treasure?",
                f"The support wobbled under Eve, and the room suddenly felt unsafe. That quick scare is what made the crew call for help at once."
            ))
        elif f["curtain_wobbled"]:
            qa.append((
                "What happened when Eve tugged the curtain?",
                f"The curtain and rod shifted with a sharp clack, and everyone got scared. Even when the treasure moved, the game stopped feeling fun because the cave itself seemed to fall apart."
            ))
        qa.append((
            f"How did {parent.label_word} help?",
            f"{parent.label_word.capitalize()} {method.qa_text}. The safe method solved the problem without more wobbling or pulling."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the pirate game continuing in a safer way, and {f.get('ending_image', 'the cat beside the treasure')} proved the room felt calm again. The ending image shows what changed: the treasure mattered less than keeping everyone safe."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"thistle"}
    tags |= set(f["treasure_cfg"].tags)
    tags |= set(f["spot_cfg"].tags)
    tags |= set(f["move_cfg"].tags)
    tags |= set(f["method_cfg"].tags)
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.age:
            parts.append(f"age={ent.age}")
        if not ent.stable:
            parts.append("stable=False")
        if ent.hanging:
            parts.append("hanging=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None)}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        pretend="pirates",
        treasure="map",
        spot="sill",
        move="swivel_stool",
        method="step_stool",
        mate_name="Tom",
        mate_gender="boy",
        mate_trait="careful",
        parent="mother",
        relation="siblings",
        eve_age=5,
        mate_age=7,
    ),
    StoryParams(
        pretend="corsairs",
        treasure="spyglass",
        spot="rod_fold",
        move="curtain_tug",
        method="grabber",
        mate_name="Mia",
        mate_gender="girl",
        mate_trait="thoughtful",
        parent="father",
        relation="friends",
        eve_age=6,
        mate_age=6,
    ),
    StoryParams(
        pretend="raiders",
        treasure="key",
        spot="hem",
        move="toy_chest",
        method="lift",
        mate_name="Finn",
        mate_gender="boy",
        mate_trait="steady",
        parent="mother",
        relation="siblings",
        eve_age=6,
        mate_age=4,
    ),
    StoryParams(
        pretend="pirates",
        treasure="map",
        spot="rod_fold",
        move="curtain_tug",
        method="lift",
        mate_name="Nora",
        mate_gender="girl",
        mate_trait="cautious",
        parent="father",
        relation="siblings",
        eve_age=4,
        mate_age=7,
    ),
    StoryParams(
        pretend="corsairs",
        treasure="key",
        spot="sill",
        move="swivel_stool",
        method="lift",
        mate_name="Ben",
        mate_gender="boy",
        mate_trait="curious",
        parent="mother",
        relation="friends",
        eve_age=5,
        mate_age=5,
    ),
]


def explain_combo_rejection(move: RiskyMove, spot: Spot, method: SafeMethod) -> str:
    if not move_reaches(move, spot):
        if move.kind == "tug" and not spot.in_curtain:
            return (
                f"(No story: pulling the curtain cannot honestly reach something at {spot.label}; "
                f"that treasure is behind the cloth, not caught in it.)"
            )
        return (
            f"(No story: {move.label} is not enough to reach {spot.label}, so the risky temptation would not make sense.)"
        )
    if not method_reaches(method, spot):
        return (
            f"(No story: {method.label} cannot reach {spot.label}. The grown-up fix must truly solve the problem.)"
        )
    return "(No story: that combination does not fit this world.)"


ASP_RULES = r"""
reaches(M,S) :- risky_move(M), spot(S), move_reach(M,R), spot_height(S,H), R >= H, climb_move(M).
reaches(M,S) :- risky_move(M), spot(S), move_reach(M,R), spot_height(S,H), R >= H, tug_move(M), in_curtain(S).

safe_reaches(Safe,S) :- safe_method(Safe), spot(S), method_height(Safe,R), spot_height(S,H), R >= H.

valid_combo(P,T,S,M,Safe) :- pretend(P), treasure(T), spot(S), risky_move(M), safe_method(Safe),
                             reaches(M,S), safe_reaches(Safe,S).

cautious_now(T) :- mate_trait(T), is_cautious(T).
init_caution(5) :- mate_trait(T), cautious_now(T).
init_caution(3) :- mate_trait(T), not cautious_now(T).
mate_older :- relation(siblings), mate_age(MA), eve_age(EA), MA > EA.
bonus(4) :- mate_older.
bonus(0) :- not mate_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- mate_older, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(rescued) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PRETENDS:
        lines.append(asp.fact("pretend", pid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("spot_height", sid, spot.height))
        if spot.in_curtain:
            lines.append(asp.fact("in_curtain", sid))
    for mid, move in RISKY_MOVES.items():
        lines.append(asp.fact("risky_move", mid))
        lines.append(asp.fact("move_reach", mid, move.reach))
        if move.kind == "climb":
            lines.append(asp.fact("climb_move", mid))
        if move.kind == "tug":
            lines.append(asp.fact("tug_move", mid))
    for sid, method in SAFE_METHODS.items():
        lines.append(asp.fact("safe_method", sid))
        lines.append(asp.fact("method_height", sid, method.max_height))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_combo/5."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("mate_age", params.mate_age),
        asp.fact("eve_age", params.eve_age),
        asp.fact("mate_trait", params.mate_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.eve_age, params.mate_age, params.mate_trait) else "rescued"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Eve, a curtain-cave, and a pirate treasure that is too high to reach safely."
    )
    ap.add_argument("--pretend", choices=PRETENDS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--move", choices=RISKY_MOVES)
    ap.add_argument("--method", choices=SAFE_METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--mate-trait", dest="mate_trait", choices=MATE_TRAITS)
    ap.add_argument("--mate-gender", dest="mate_gender", choices=["girl", "boy"])
    ap.add_argument("--mate-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.move and args.spot and args.method:
        move = RISKY_MOVES[args.move]
        spot = SPOTS[args.spot]
        method = SAFE_METHODS[args.method]
        if not (move_reaches(move, spot) and method_reaches(method, spot)):
            raise StoryError(explain_combo_rejection(move, spot, method))

    combos = [
        combo for combo in valid_combos()
        if (args.pretend is None or combo[0] == args.pretend)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.spot is None or combo[2] == args.spot)
        and (args.move is None or combo[3] == args.move)
        and (args.method is None or combo[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pretend, treasure, spot, move, method = rng.choice(sorted(combos))
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    mate_name = args.mate_name or rng.choice([n for n in MATE_NAMES[mate_gender] if n != "Eve"])
    mate_trait = args.mate_trait or rng.choice(MATE_TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    eve_age, mate_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        pretend=pretend,
        treasure=treasure,
        spot=spot,
        move=move,
        method=method,
        mate_name=mate_name,
        mate_gender=mate_gender,
        mate_trait=mate_trait,
        parent=parent,
        relation=relation,
        eve_age=eve_age,
        mate_age=mate_age,
    )


def _validate_params(params: StoryParams) -> None:
    missing = []
    if params.pretend not in PRETENDS:
        missing.append(f"pretend={params.pretend}")
    if params.treasure not in TREASURES:
        missing.append(f"treasure={params.treasure}")
    if params.spot not in SPOTS:
        missing.append(f"spot={params.spot}")
    if params.move not in RISKY_MOVES:
        missing.append(f"move={params.move}")
    if params.method not in SAFE_METHODS:
        missing.append(f"method={params.method}")
    if params.parent not in {"mother", "father"}:
        missing.append(f"parent={params.parent}")
    if params.relation not in {"siblings", "friends"}:
        missing.append(f"relation={params.relation}")
    if params.mate_gender not in {"girl", "boy"}:
        missing.append(f"mate_gender={params.mate_gender}")
    if missing:
        raise StoryError("(Invalid story parameters: " + ", ".join(missing) + ")")
    combo = (params.pretend, params.treasure, params.spot, params.move, params.method)
    if combo not in set(valid_combos()):
        raise StoryError(explain_combo_rejection(RISKY_MOVES[params.move], SPOTS[params.spot], SAFE_METHODS[params.method]))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        PRETENDS[params.pretend],
        TREASURES[params.treasure],
        SPOTS[params.spot],
        RISKY_MOVES[params.move],
        SAFE_METHODS[params.method],
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        mate_trait=params.mate_trait,
        parent_type=params.parent,
        relation=params.relation,
        eve_age=params.eve_age,
        mate_age=params.mate_age,
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

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(80):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="smoke")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_combo/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (pretend, treasure, spot, move, method) combos:\n")
        for pretend, treasure, spot, move, method in combos:
            print(f"  {pretend:8} {treasure:8} {spot:9} {move:13} {method}")
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
                f"### Eve & {p.mate_name}: {p.treasure} at {p.spot} "
                f"({p.move}, {p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
