#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/collision_prawn_bedroom_surprise_ghost_story.py
===========================================================================

A standalone story world about a child in a bedroom who thinks a ghost has come,
only to discover a surprising, gentle explanation: a moving bedroom object made
a spooky shadow and a tapping collision in the dark.

This world is built to satisfy a small, constraint-checked domain:

- Setting: bedroom
- Required words: "collision", "prawn"
- Feature: Surprise
- Style: Ghost Story

The world model tracks physical meters (dark, swinging, noise) and emotional
memes (fear, relief, wonder). A draft source moves a dangling object; the moving
object bumps a hard surface; the sound and shadow make the child think of a
ghost. A helper turns on a light, investigates, and fixes the real cause so the
bedroom feels safe again.

Run it
------
    python storyworlds/worlds/gpt-5.4/collision_prawn_bedroom_surprise_ghost_story.py
    python storyworlds/worlds/gpt-5.4/collision_prawn_bedroom_surprise_ghost_story.py --breeze open_window
    python storyworlds/worlds/gpt-5.4/collision_prawn_bedroom_surprise_ghost_story.py --target pillow
    python storyworlds/worlds/gpt-5.4/collision_prawn_bedroom_surprise_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/collision_prawn_bedroom_surprise_ghost_story.py --qa
    python storyworlds/worlds/gpt-5.4/collision_prawn_bedroom_surprise_ghost_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
    casts_shadow: bool = False
    dangling: bool = False
    hard_surface: bool = False
    movable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Breeze:
    id: str
    label: str
    line: str
    airflow: int
    spooky_touch: str
    fixes: set[str] = field(default_factory=set)
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
class Dangly:
    id: str
    label: str
    phrase: str
    shadow_shape: str
    hardness: int
    casts_shadow: bool
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
class Target:
    id: str
    label: str
    phrase: str
    sound: str
    noise: int
    hard_surface: bool
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
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    fixes: set[str] = field(default_factory=set)
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


def _r_swing(world: World) -> list[str]:
    room = world.get("room")
    breeze = world.get("breeze")
    dangly = world.get("dangly")
    sig = ("swing", breeze.id, dangly.id)
    if room.meters["dark"] < THRESHOLD:
        return []
    if breeze.meters["airflow"] < THRESHOLD:
        return []
    if not dangly.dangling:
        return []
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dangly.meters["swinging"] += 1
    if dangly.casts_shadow:
        room.meters["shadow"] += 1
    return ["__swing__"]


def _r_collision(world: World) -> list[str]:
    dangly = world.get("dangly")
    target = world.get("target")
    room = world.get("room")
    sig = ("collision", dangly.id, target.id)
    if dangly.meters["swinging"] < THRESHOLD:
        return []
    if target.meters["touching"] < THRESHOLD:
        return []
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if target.hard_surface and target.meters["noise_value"] >= THRESHOLD:
        room.meters["noise"] += 1
        dangly.meters["bumped"] += 1
        target.meters["bumped"] += 1
        return ["__collision__"]
    return []


def _r_fear(world: World) -> list[str]:
    room = world.get("room")
    child = world.get("child")
    sig = ("fear", child.id)
    if room.meters["noise"] < THRESHOLD:
        return []
    if room.meters["shadow"] < THRESHOLD:
        return []
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    room.meters["mystery"] += 1
    return ["__fear__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="swing", tag="physical", apply=_r_swing),
    Rule(name="collision", tag="physical", apply=_r_collision),
    Rule(name="fear", tag="emotional", apply=_r_fear),
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


def spooky_possible(breeze: Breeze, dangly: Dangly, target: Target) -> bool:
    return (
        breeze.airflow > 0
        and dangly.hardness > 0
        and dangly.casts_shadow
        and target.hard_surface
        and target.noise > 0
    )


def compatible_responses_for(breeze_id: str) -> list[str]:
    if breeze_id not in BREEZES:
        return []
    return sorted(
        rid for rid, resp in RESPONSES.items()
        if resp.sense >= SENSE_MIN and breeze_id in resp.fixes
    )


def predict_spookiness(world: World) -> dict:
    sim = world.copy()
    sim.get("breeze").meters["airflow"] = sim.facts["breeze_cfg"].airflow
    sim.get("target").meters["touching"] = 1.0
    sim.get("target").meters["noise_value"] = float(sim.facts["target_cfg"].noise)
    propagate(sim, narrate=False)
    return {
        "collision": sim.get("dangly").meters["bumped"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"] >= THRESHOLD,
        "noise": sim.get("room").meters["noise"],
        "shadow": sim.get("room").meters["shadow"],
    }


def bedtime_setup(world: World, child: Entity, helper: Entity, breeze: Breeze, prawn: Entity) -> None:
    child.memes["sleepy"] += 1
    child.memes["trust"] += 1
    world.say(
        f"It was bedtime in {child.attrs['room_name']}, and the bedroom felt hushed and silver. "
        f"{child.id} tucked {prawn.phrase} under one arm while {helper.label_word} pulled the blanket smooth."
    )
    world.say(
        f"{breeze.line} Moonlight spilled across the floorboards and made even quiet things look a little strange."
    )


def room_detail(world: World, child: Entity, dangly: Dangly, target: Target) -> None:
    world.say(
        f"Above the bed hung {dangly.phrase}, and nearby stood {target.phrase}. "
        f"In the dark, their edges looked taller and thinner than they did in the day."
    )
    if "curious" in child.traits:
        world.say(f"{child.id} tried to be brave and watched the corners of the room anyway.")


def stir_the_air(world: World, breeze: Breeze, target: Target) -> None:
    world.get("breeze").meters["airflow"] = float(breeze.airflow)
    world.get("target").meters["touching"] = 1.0
    world.get("target").meters["noise_value"] = float(target.noise)
    propagate(world, narrate=False)


def first_spook(world: World, child: Entity, breeze: Breeze, dangly: Dangly, target: Target) -> None:
    world.say(
        f"After the lamp clicked off, {breeze.spooky_touch}. "
        f"{dangly.phrase.capitalize()} began to sway."
    )
    if world.get("dangly").meters["bumped"] >= THRESHOLD:
        world.say(
            f"Then came a soft collision: {target.sound}, {target.sound} against {target.label}. "
            f"The tiny sound seemed much bigger in the dark."
        )
    if world.get("room").meters["shadow"] >= THRESHOLD:
        world.say(
            f"On the wall, a shadow stretched into {dangly.shadow_shape}. "
            f"For one breath, it looked exactly like the sort of ghost a bedtime story would invent."
        )
    if child.memes["fear"] >= THRESHOLD:
        child.memes["alarm"] += 1
        world.say(
            f"{child.id} sat up fast, clutching the prawn so tightly that its stitched tail bent. "
            f'"There is something in my room," {child.pronoun()} whispered.'
        )


def call_for_help(world: World, child: Entity, helper: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{child.id} called for {helper.label_word}, and warm footsteps came at once. '
        f'{helper.label_word.capitalize()} did not laugh or scold.'
    )


def inspect(world: World, child: Entity, helper: Entity, dangly: Dangly, target: Target) -> None:
    room = world.get("room")
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    helper.memes["care"] += 1
    room.meters["dark"] = 0.0
    room.meters["mystery"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} switched on the bedside lamp, and the ghost vanished all at once. "
        f"In the yellow light, the room looked ordinary again."
    )
    world.say(
        f"Together they followed the sound to {target.phrase}. "
        f"There, {dangly.phrase} was still quivering from its little collision."
    )


def reveal(world: World, child: Entity, helper: Entity, breeze: Breeze, dangly: Dangly, target: Target) -> None:
    child.memes["surprise"] += 1
    world.say(
        f'"Look," said {helper.label_word}. "{breeze.label} was nudging {dangly.label}, '
        f'and it kept tapping {target.label}. That is all the ghost was."'
    )
    world.say(
        f"{child.id} blinked, then looked again. The scary shape was only {dangly.label} and moonlight, "
        f"mixed with the round shadow of the pink prawn pillow on the chair. The surprise made {child.pronoun()} laugh a tiny laugh."
    )


def fix_room(world: World, helper: Entity, response: Response, child: Entity) -> None:
    world.get("breeze").meters["airflow"] = 0.0
    world.get("dangly").meters["swinging"] = 0.0
    world.get("target").meters["touching"] = 0.0
    world.get("room").meters["noise"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} {response.text}. "
        f"After that, the bedroom stayed still."
    )
    world.say(
        f"No more tapping came. No more ghost shape climbed the wall."
    )
    child.memes["safe"] += 1
    child.memes["fear"] = 0.0


def cozy_end(world: World, child: Entity, helper: Entity, prawn: Entity) -> None:
    world.say(
        f"{helper.label_word.capitalize()} tucked the blanket back around {child.id} and settled {prawn.phrase} beside the pillow."
    )
    world.say(
        f"Soon the bedroom was only a bedroom again, with a quiet lamp, a soft bed, and moonlight resting where it belonged. "
        f"{child.id} hugged the prawn, smiled into the dark, and was not afraid of ghosts anymore."
    )


def tell(
    breeze: Breeze,
    dangly: Dangly,
    target: Target,
    response: Response,
    *,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"room_name": "the bedroom"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    room = world.add(Entity(
        id="room",
        type="bedroom",
        label="bedroom",
        phrase="the bedroom",
        movable=False,
    ))
    breeze_ent = world.add(Entity(
        id="breeze",
        type="air",
        label=breeze.label,
        phrase=breeze.label,
        movable=True,
    ))
    dangly_ent = world.add(Entity(
        id="dangly",
        type="dangly",
        label=dangly.label,
        phrase=dangly.phrase,
        dangling=True,
        casts_shadow=dangly.casts_shadow,
        movable=True,
    ))
    target_ent = world.add(Entity(
        id="target",
        type="target",
        label=target.label,
        phrase=target.phrase,
        hard_surface=target.hard_surface,
    ))
    prawn = world.add(Entity(
        id="prawn",
        type="toy",
        label="prawn pillow",
        phrase="a pink prawn pillow",
        movable=True,
    ))

    room.meters["dark"] = 1.0
    room.meters["noise"] = 0.0
    room.meters["shadow"] = 0.0
    room.meters["mystery"] = 0.0
    breeze_ent.meters["airflow"] = 0.0
    dangly_ent.meters["swinging"] = 0.0
    dangly_ent.meters["bumped"] = 0.0
    target_ent.meters["touching"] = 0.0
    target_ent.meters["noise_value"] = 0.0
    target_ent.meters["bumped"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["surprise"] = 0.0
    child.memes["safe"] = 0.0
    child.memes["alarm"] = 0.0
    helper.memes["care"] = 0.0

    world.facts.update(
        child=child,
        helper=helper,
        room=room,
        prawn=prawn,
        breeze_cfg=breeze,
        dangly_cfg=dangly,
        target_cfg=target,
        response=response,
    )

    bedtime_setup(world, child, helper, breeze, prawn)
    room_detail(world, child, dangly, target)

    world.para()
    stir_the_air(world, breeze, target)
    first_spook(world, child, breeze, dangly, target)
    call_for_help(world, child, helper)

    world.para()
    inspect(world, child, helper, dangly, target)
    reveal(world, child, helper, breeze, dangly, target)
    fix_room(world, helper, response, child)

    world.para()
    cozy_end(world, child, helper, prawn)

    world.facts.update(
        collision=world.get("dangly").meters["bumped"] >= THRESHOLD,
        shadow=world.get("room").meters["shadow"] >= THRESHOLD,
        feared=world.facts["child"].memes["alarm"] >= THRESHOLD,
        resolved=world.facts["child"].memes["safe"] >= THRESHOLD,
    )
    return world


BREEZES = {
    "open_window": Breeze(
        id="open_window",
        label="the open window",
        line="The window was open a crack, and cool air slipped in from the night.",
        airflow=2,
        spooky_touch="A thin breath of night air touched the room",
        fixes={"close_window", "move_mobile"},
        tags={"window", "breeze"},
    ),
    "ceiling_fan": Breeze(
        id="ceiling_fan",
        label="the ceiling fan",
        line="The ceiling fan was still turning on its slow bedtime setting.",
        airflow=1,
        spooky_touch="The slow fan kept stirring the room overhead",
        fixes={"fan_off", "move_mobile"},
        tags={"fan", "breeze"},
    ),
    "hall_draft": Breeze(
        id="hall_draft",
        label="the open door to the hall",
        line="The bedroom door stood open, and hallway air drifted through in little waves.",
        airflow=1,
        spooky_touch="The hallway draft slipped across the bedroom floor",
        fixes={"close_door", "move_mobile"},
        tags={"door", "breeze"},
    ),
}

DANGLIES = {
    "moon_mobile": Dangly(
        id="moon_mobile",
        label="the moon mobile",
        phrase="a moon mobile with silver stars",
        shadow_shape="a long gray ghost with crooked arms",
        hardness=1,
        casts_shadow=True,
        tags={"mobile", "shadow"},
    ),
    "prawn_mobile": Dangly(
        id="prawn_mobile",
        label="the prawn mobile",
        phrase="a funny prawn mobile made of pink card and string",
        shadow_shape="a bent little ghost with whiskers",
        hardness=1,
        casts_shadow=True,
        tags={"mobile", "shadow", "prawn"},
    ),
    "shell_chime": Dangly(
        id="shell_chime",
        label="the shell chime",
        phrase="a shell chime from the seaside",
        shadow_shape="a wiggly white ghost with a fluttering skirt",
        hardness=2,
        casts_shadow=True,
        tags={"shadow", "shell"},
    ),
}

TARGETS = {
    "wardrobe": Target(
        id="wardrobe",
        label="the wardrobe door",
        phrase="the tall wardrobe door",
        sound="tok",
        noise=2,
        hard_surface=True,
        tags={"wardrobe", "collision"},
    ),
    "lamp": Target(
        id="lamp",
        label="the metal lamp base",
        phrase="the metal lamp on the little table",
        sound="ting",
        noise=1,
        hard_surface=True,
        tags={"lamp", "collision"},
    ),
    "bedpost": Target(
        id="bedpost",
        label="the wooden bedpost",
        phrase="the bedpost at the corner of the bed",
        sound="tup",
        noise=1,
        hard_surface=True,
        tags={"bed", "collision"},
    ),
    "pillow": Target(
        id="pillow",
        label="the spare pillow",
        phrase="the spare pillow on the chair",
        sound="puff",
        noise=0,
        hard_surface=False,
        tags={"pillow"},
    ),
}

RESPONSES = {
    "close_window": Response(
        id="close_window",
        sense=3,
        text="walked over and shut the window gently",
        qa_text="shut the window so the air stopped pushing things around",
        fixes={"open_window"},
        tags={"window"},
    ),
    "fan_off": Response(
        id="fan_off",
        sense=3,
        text="reached up and switched the ceiling fan off",
        qa_text="turned the fan off so the room stopped moving",
        fixes={"ceiling_fan"},
        tags={"fan"},
    ),
    "close_door": Response(
        id="close_door",
        sense=3,
        text="pulled the bedroom door almost closed until the hallway draft was gone",
        qa_text="closed the door enough to stop the hallway draft",
        fixes={"hall_draft"},
        tags={"door"},
    ),
    "move_mobile": Response(
        id="move_mobile",
        sense=2,
        text="moved the hanging thing farther from the hard edge it had been bumping",
        qa_text="moved the dangling thing so it could not bump anything anymore",
        fixes={"open_window", "ceiling_fan", "hall_draft"},
        tags={"mobile"},
    ),
    "hide_under_blanket": Response(
        id="hide_under_blanket",
        sense=1,
        text="hid under the blanket and hoped the sound would stop by itself",
        qa_text="hid under the blanket",
        fixes=set(),
        tags={"blanket"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Rose", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Max", "Eli", "Noah", "Finn", "Leo"]
TRAITS = ["curious", "quiet", "brave", "sleepy", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for breeze_id, breeze in BREEZES.items():
        for dangly_id, dangly in DANGLIES.items():
            for target_id, target in TARGETS.items():
                if spooky_possible(breeze, dangly, target):
                    combos.append((breeze_id, dangly_id, target_id))
    return combos


@dataclass
class StoryParams:
    breeze: str
    dangly: str
    target: str
    response: str
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


CURATED = [
    StoryParams(
        breeze="open_window",
        dangly="prawn_mobile",
        target="wardrobe",
        response="close_window",
        child_name="Mina",
        child_gender="girl",
        helper="mother",
        trait="curious",
    ),
    StoryParams(
        breeze="ceiling_fan",
        dangly="moon_mobile",
        target="lamp",
        response="fan_off",
        child_name="Theo",
        child_gender="boy",
        helper="father",
        trait="quiet",
    ),
    StoryParams(
        breeze="hall_draft",
        dangly="shell_chime",
        target="bedpost",
        response="close_door",
        child_name="Nora",
        child_gender="girl",
        helper="mother",
        trait="careful",
    ),
    StoryParams(
        breeze="open_window",
        dangly="moon_mobile",
        target="bedpost",
        response="move_mobile",
        child_name="Ben",
        child_gender="boy",
        helper="father",
        trait="brave",
    ),
]


KNOWLEDGE = {
    "collision": [
        (
            "What is a collision?",
            "A collision is when one thing bumps into another thing. Sometimes it makes a sound, especially if the things are hard.",
        )
    ],
    "prawn": [
        (
            "What is a prawn?",
            "A prawn is a small sea animal with a curved body and long feelers. In this story, the word also appears on a toy shaped like one.",
        )
    ],
    "shadow": [
        (
            "What makes a shadow on the wall at night?",
            "A shadow happens when light shines and something blocks part of it. In a dark room, even a small moving thing can make a shape look big and strange.",
        )
    ],
    "window": [
        (
            "Why can an open window make things move?",
            "Air can slip through an open window and push on light things like paper, strings, and curtains. That moving air is called a draft or a breeze.",
        )
    ],
    "fan": [
        (
            "How can a fan change a room even when it is quiet?",
            "A fan keeps air moving, even if it does not sound loud. That moving air can make hanging things sway.",
        )
    ],
    "door": [
        (
            "Why can an open door make a draft?",
            "Air moves from one place to another when a doorway is open. If the hallway air is moving, it can drift right into a bedroom.",
        )
    ],
    "mobile": [
        (
            "What is a mobile in a bedroom?",
            "A mobile is something light that hangs and moves gently in the air. People often hang them over a bed or near a window.",
        )
    ],
    "shell": [
        (
            "Why do shells make clicky sounds when they knock together?",
            "Shells are hard, so they make little tapping sounds when they bump. In a quiet room, those tiny sounds can seem louder than they really are.",
        )
    ],
}
KNOWLEDGE_ORDER = ["collision", "prawn", "shadow", "window", "fan", "door", "mobile", "shell"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    breeze = world.facts["breeze_cfg"]
    dangly = world.facts["dangly_cfg"]
    target = world.facts["target_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old set in a bedroom that includes the words "collision" and "prawn".',
        f"Tell a bedtime story where {child.id} hears a spooky sound in the bedroom, but the surprise ending shows that {breeze.label} made {dangly.label} bump {target.label}.",
        "Write a child-facing story with a ghost-story mood, a scary shadow, a kind grown-up, and a comforting explanation that turns fear into laughter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    breeze = world.facts["breeze_cfg"]
    dangly = world.facts["dangly_cfg"]
    target = world.facts["target_cfg"]
    response = world.facts["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was trying to fall asleep in the bedroom, and {helper.label_word}, who came to help. The story also keeps the pink prawn pillow close by, so the room feels personal and real.",
        ),
        (
            "Why did the bedroom seem haunted at first?",
            f"In the dark, moving air made {dangly.label} sway and tap {target.label}, so the room suddenly had both a strange sound and a strange shadow. Those two things together made it feel ghostly, even though nothing magical was there.",
        ),
        (
            "What caused the collision sound?",
            f"The sound came when {breeze.label} pushed {dangly.label} until it bumped {target.label}. The collision was tiny, but bedtime quiet made it seem much bigger.",
        ),
        (
            "What was the surprise?",
            f"The surprise was that the ghost shape was not a ghost at all. It was only moonlight, {dangly.label}, and the round shadow of the prawn pillow mixing together on the wall.",
        ),
        (
            f"How did {helper.label_word} make the room feel safe again?",
            f"{helper.label_word.capitalize()} turned on the lamp first, so everyone could see clearly, and then {response.qa_text}. Once the real cause was fixed, the scary tapping stopped and {child.id} could relax.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            (
                f"How did {child.id} feel at the end?",
                f"{child.id} felt relieved and even a little proud. The same bedroom that had seemed full of ghosts now felt quiet and friendly again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"collision", "shadow", "prawn"}
    tags |= set(world.facts["breeze_cfg"].tags)
    tags |= set(world.facts["dangly_cfg"].tags)
    tags |= set(world.facts["target_cfg"].tags)
    tags |= set(world.facts["response"].tags)
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
        flags = [name for name, on in (
            ("casts_shadow", ent.casts_shadow),
            ("dangling", ent.dangling),
            ("hard_surface", ent.hard_surface),
            ("movable", ent.movable),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo_rejection(breeze: Breeze, dangly: Dangly, target: Target) -> str:
    if not target.hard_surface or target.noise <= 0:
        return (
            f"(No story: {dangly.label} might sway, but {target.label} is too soft or too quiet to make a spooky collision. "
            f"Pick a harder target like the wardrobe door, lamp, or bedpost.)"
        )
    if not dangly.casts_shadow:
        return (
            f"(No story: {dangly.label} would move, but it would not cast the kind of shadow that makes the bedroom feel haunted.)"
        )
    return "(No story: this combination does not make a believable bedroom ghost scare.)"


def explain_response_rejection(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(rid for rid, r in RESPONSES.items() if r.sense >= SENSE_MIN))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of these instead: {better}.)"
    )


def explain_response_mismatch(breeze_id: str, response_id: str) -> str:
    return (
        f"(No story: response '{response_id}' does not honestly fix '{breeze_id}'. "
        f"Choose a response that stops that moving air or moves the dangling object.)"
    )


ASP_RULES = r"""
spooky(B,D,T) :- breeze(B), dangly(D), target(T),
                 airflow(B,A), hardness(D,H), hard_target(T), noise(T,N), casts_shadow(D),
                 A > 0, H > 0, N > 0.

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
compatible(B,R) :- fixes(B,R).
valid(B,D,T) :- spooky(B,D,T).
valid_story(B,D,T,R) :- valid(B,D,T), compatible(B,R), sensible(R).

resolved :- chosen_breeze(B), chosen_response(R), compatible(B,R), sensible(R).
outcome(resolved) :- resolved.
outcome(unresolved) :- not resolved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bid, breeze in BREEZES.items():
        lines.append(asp.fact("breeze", bid))
        lines.append(asp.fact("airflow", bid, breeze.airflow))
        for rid in sorted(breeze.fixes):
            lines.append(asp.fact("fixes", bid, rid))
    for did, dangly in DANGLIES.items():
        lines.append(asp.fact("dangly", did))
        lines.append(asp.fact("hardness", did, dangly.hardness))
        if dangly.casts_shadow:
            lines.append(asp.fact("casts_shadow", did))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("noise", tid, target.noise))
        if target.hard_surface:
            lines.append(asp.fact("hard_target", tid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_breeze", params.breeze),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def python_outcome(params: StoryParams) -> str:
    response = RESPONSES[params.response]
    if response.sense >= SENSE_MIN and params.breeze in response.fixes:
        return "resolved"
    return "unresolved"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedroom ghost-story world: a spooky sound, a surprising explanation, and a calm bedtime ending."
    )
    ap.add_argument("--breeze", choices=BREEZES)
    ap.add_argument("--dangly", choices=DANGLIES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump the world model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.breeze and args.dangly and args.target:
        breeze = BREEZES[args.breeze]
        dangly = DANGLIES[args.dangly]
        target = TARGETS[args.target]
        if not spooky_possible(breeze, dangly, target):
            raise StoryError(explain_combo_rejection(breeze, dangly, target))
    if args.response:
        if RESPONSES[args.response].sense < SENSE_MIN:
            raise StoryError(explain_response_rejection(args.response))
        if args.breeze and args.breeze not in RESPONSES[args.response].fixes:
            raise StoryError(explain_response_mismatch(args.breeze, args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.breeze is None or combo[0] == args.breeze)
        and (args.dangly is None or combo[1] == args.dangly)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    breeze_id, dangly_id, target_id = rng.choice(sorted(combos))
    if args.response:
        response_id = args.response
    else:
        valid_responses = compatible_responses_for(breeze_id)
        if not valid_responses:
            raise StoryError("(No sensible response fits the chosen moving-air source.)")
        response_id = rng.choice(valid_responses)

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        breeze=breeze_id,
        dangly=dangly_id,
        target=target_id,
        response=response_id,
        child_name=name,
        child_gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.breeze not in BREEZES:
        raise StoryError(f"(Unknown breeze: {params.breeze})")
    if params.dangly not in DANGLIES:
        raise StoryError(f"(Unknown dangly object: {params.dangly})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.helper not in {"mother", "father"}:
        raise StoryError(f"(Unknown helper type: {params.helper})")

    breeze = BREEZES[params.breeze]
    dangly = DANGLIES[params.dangly]
    target = TARGETS[params.target]
    response = RESPONSES[params.response]

    if not spooky_possible(breeze, dangly, target):
        raise StoryError(explain_combo_rejection(breeze, dangly, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(params.response))
    if params.breeze not in response.fixes:
        raise StoryError(explain_response_mismatch(params.breeze, params.response))

    world = tell(
        breeze=breeze,
        dangly=dangly,
        target=target,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
        trait=params.trait,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {rid for rid, r in RESPONSES.items() if r.sense >= SENSE_MIN}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    py_story_set = {
        (breeze_id, dangly_id, target_id, response_id)
        for breeze_id, dangly_id, target_id in valid_combos()
        for response_id in compatible_responses_for(breeze_id)
    }
    asp_story_set = set(asp_valid_stories())
    if py_story_set == asp_story_set:
        print(f"OK: valid stories match ({len(py_story_set)} combinations with responses).")
    else:
        rc = 1
        print("MISMATCH in valid stories:")
        if asp_story_set - py_story_set:
            print("  only in clingo:", sorted(asp_story_set - py_story_set))
        if py_story_set - asp_story_set:
            print("  only in python:", sorted(py_story_set - asp_story_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed during verification at seed {seed}.")
            break

    outcome_bad = 0
    for params in cases:
        if asp_outcome(params) != python_outcome(params):
            outcome_bad += 1
    if outcome_bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {outcome_bad}/{len(cases)} outcomes differ.")

    smoke_targets = list(CURATED[:2])
    if cases:
        smoke_targets.append(cases[-1])
    for idx, params in enumerate(smoke_targets, 1):
        try:
            sample = generate(params)
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=False, qa=True, header=f"smoke {idx}")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE TEST FAILED on case {idx}: {err!r}")
    if rc == 0:
        print("OK: generation/emit smoke tests passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_story/4.\n#show outcome/1.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (breeze, dangly, target, response) combinations:\n")
        for breeze_id, dangly_id, target_id, response_id in stories:
            print(f"  {breeze_id:12} {dangly_id:12} {target_id:8} {response_id}")
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
            header = f"### {p.child_name}: {p.breeze}, {p.dangly}, {p.target}, {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
