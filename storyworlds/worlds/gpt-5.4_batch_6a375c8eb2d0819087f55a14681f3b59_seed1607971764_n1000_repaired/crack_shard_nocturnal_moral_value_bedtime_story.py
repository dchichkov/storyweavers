#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crack_shard_nocturnal_moral_value_bedtime_story.py
=============================================================================

A standalone storyworld for a bedtime-scale tale about honesty after a small
accident. A child hears a nocturnal visitor outside, carries a glowing bedroom
lamp to the window, and drops it. If the lamp and surface make a real break
hazard, a crack appears. The child then either tells a grown-up right away or
tries to hide the damage. Honesty leads to a calm, safe ending; hiding the
break lets a dangerous shard slip free and turns the lesson into a cautionary
one.

The world models a few concrete things:

* a fragile night lamp
* a hard or soft surface under it
* a nocturnal creature outside the window
* a child's choice: tell or hide
* a grown-up's repair and comfort

The constraint gate is intentionally narrow: only combinations where a dropped
lamp would plausibly crack and pose a shard risk are accepted. A soft rug under
a squishy lamp is not enough story pressure for this domain, so it is refused.

Run it
------
    python storyworlds/worlds/gpt-5.4/crack_shard_nocturnal_moral_value_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/crack_shard_nocturnal_moral_value_bedtime_story.py --lamp glass_moon --surface floorboards --choice tell
    python storyworlds/worlds/gpt-5.4/crack_shard_nocturnal_moral_value_bedtime_story.py --lamp tin_lantern
    python storyworlds/worlds/gpt-5.4/crack_shard_nocturnal_moral_value_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/crack_shard_nocturnal_moral_value_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/crack_shard_nocturnal_moral_value_bedtime_story.py --verify
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
CRACK_MIN = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    brittle: bool = False
    glowing: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
class Visitor:
    id: str
    label: str
    call: str
    motion: str
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
class Lamp:
    id: str
    label: str
    phrase: str
    glow: str
    shell: str
    fragility: int
    fragile: bool = True
    brittle: bool = True
    sharp: bool = True
    safe_replacement: str = "a soft paper lantern"
    replacement_glow: str = "glowed like a small sleepy moon"
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
class Surface:
    id: str
    label: str
    phrase: str
    hardness: int
    sound: str
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


def crack_score(lamp: Lamp, surface: Surface) -> int:
    return lamp.fragility + surface.hardness


def cracks_for_real(lamp: Lamp, surface: Surface) -> bool:
    return lamp.fragile and lamp.brittle and lamp.sharp and crack_score(lamp, surface) >= CRACK_MIN


def predict_shatter(lamp: Lamp, surface: Surface, choice: str) -> dict:
    return {
        "will_crack": cracks_for_real(lamp, surface),
        "will_shatter_if_hidden": cracks_for_real(lamp, surface) and choice == "hide",
        "score": crack_score(lamp, surface),
    }


def _r_crack(world: World) -> list[str]:
    child = world.get("child")
    lamp = world.get("lamp")
    surface = world.get("surface")
    if lamp.meters["dropped"] < THRESHOLD:
        return []
    sig = ("crack", lamp.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if lamp.fragile and lamp.brittle and surface.attrs.get("hardness", 0) + lamp.attrs.get("fragility", 0) >= CRACK_MIN:
        lamp.meters["cracked"] += 1
        child.memes["fear"] += 1
        world.get("room").meters["danger"] += 1
        world.facts["heard_crack"] = True
        return ["__crack__"]
    return []


def _r_shatter(world: World) -> list[str]:
    child = world.get("child")
    lamp = world.get("lamp")
    if lamp.meters["cracked"] < THRESHOLD or child.memes["hiding"] < THRESHOLD:
        return []
    sig = ("shatter", lamp.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if lamp.brittle:
        lamp.meters["shattered"] += 1
        lamp.meters["shards"] += 3
        world.get("room").meters["danger"] += 2
        child.memes["fear"] += 1
        return ["__shatter__"]
    return []


def _r_cut(world: World) -> list[str]:
    child = world.get("child")
    lamp = world.get("lamp")
    if lamp.meters["shattered"] < THRESHOLD or child.meters["touching_broken"] < THRESHOLD:
        return []
    sig = ("cut", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["cut"] += 1
    child.memes["pain"] += 1
    child.memes["fear"] += 1
    return ["__cut__"]


CAUSAL_RULES = [
    Rule(name="crack", tag="physical", apply=_r_crack),
    Rule(name="shatter", tag="physical", apply=_r_shatter),
    Rule(name="cut", tag="physical", apply=_r_cut),
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


VISITORS = {
    "owl": Visitor(
        id="owl",
        label="owl",
        call="a soft whoo-whoo",
        motion="its round eyes blinked from the branch outside",
        tags={"owl", "night_animals"},
    ),
    "moth": Visitor(
        id="moth",
        label="moth",
        call="the hush of wings at the window",
        motion="it fluttered in small silver loops by the glass",
        tags={"moth", "night_animals"},
    ),
    "hedgehog": Visitor(
        id="hedgehog",
        label="hedgehog",
        call="a tiny rustle in the leaves",
        motion="it nosed through the moonlit flower bed",
        tags={"hedgehog", "night_animals"},
    ),
}

LAMPS = {
    "glass_moon": Lamp(
        id="glass_moon",
        label="moon lamp",
        phrase="a little glass moon lamp",
        glow="glowed pale and milky beside the bed",
        shell="thin glass",
        fragility=3,
        fragile=True,
        brittle=True,
        sharp=True,
        safe_replacement="a paper moon lantern",
        replacement_glow="glowed warm and steady",
        tags={"glass", "lamp", "broken_glass"},
    ),
    "porcelain_star": Lamp(
        id="porcelain_star",
        label="star lamp",
        phrase="a porcelain star lamp",
        glow="shone with a sleepy golden star inside",
        shell="painted porcelain",
        fragility=3,
        fragile=True,
        brittle=True,
        sharp=True,
        safe_replacement="a cloth-covered bedside lantern",
        replacement_glow="cast a soft amber puddle on the blanket",
        tags={"porcelain", "lamp", "broken_glass"},
    ),
    "tin_lantern": Lamp(
        id="tin_lantern",
        label="tin lantern",
        phrase="a little tin lantern with punched stars",
        glow="made dots of light on the wall",
        shell="light tin",
        fragility=1,
        fragile=False,
        brittle=False,
        sharp=False,
        safe_replacement="a cloth-covered bedside lantern",
        replacement_glow="cast a soft amber puddle on the blanket",
        tags={"lamp"},
    ),
}

SURFACES = {
    "floorboards": Surface(
        id="floorboards",
        label="floorboards",
        phrase="the bare floorboards",
        hardness=2,
        sound="tok",
        tags={"wood_floor"},
    ),
    "stone_sill": Surface(
        id="stone_sill",
        label="stone sill",
        phrase="the cold stone sill",
        hardness=3,
        sound="tack",
        tags={"stone"},
    ),
    "rug": Surface(
        id="rug",
        label="rug",
        phrase="the thick rug",
        hardness=0,
        sound="muff",
        tags={"rug"},
    ),
}

CHOICES = {
    "tell": "tell",
    "hide": "hide",
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Ivy", "Zoe", "Ruby", "Clara"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Theo", "Leo", "Eli", "Sam", "Ben"]
TRAITS = ["gentle", "curious", "sleepy", "careful", "kind", "quiet"]

KNOWLEDGE = {
    "night_animals": [
        (
            "What does nocturnal mean?",
            "Nocturnal means awake at night and asleep in the daytime. Some animals, like owls and hedgehogs, move around most when the sky is dark.",
        )
    ],
    "owl": [
        (
            "Why are owls awake at night?",
            "Owls are nocturnal birds, so nighttime is when they hunt and fly best. Their big eyes and quiet wings help them in the dark.",
        )
    ],
    "moth": [
        (
            "Why do moths fly at night?",
            "Many moths are nocturnal, so they come out when the air is cool and dark. Their soft wings help them flutter quietly through the night.",
        )
    ],
    "hedgehog": [
        (
            "When do hedgehogs come out?",
            "Hedgehogs are usually nocturnal, so they often rustle around after sunset. They look for food when the garden is quiet.",
        )
    ],
    "broken_glass": [
        (
            "Why should a child not touch broken glass?",
            "Broken glass can have a sharp edge or a tiny shard that cuts skin quickly. A grown-up should clean it up carefully.",
        )
    ],
    "honesty": [
        (
            "Why is it good to tell the truth after an accident?",
            "Telling the truth helps grown-ups keep everyone safe. It also shows courage, because honesty matters even when you feel worried.",
        )
    ],
    "lamp": [
        (
            "What does a bedside lamp do?",
            "A bedside lamp gives a gentle light when the room is dark. Soft light can make bedtime feel calm and cozy.",
        )
    ],
}
KNOWLEDGE_ORDER = ["night_animals", "owl", "moth", "hedgehog", "broken_glass", "honesty", "lamp"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for visitor_id in VISITORS:
        for lamp_id, lamp in LAMPS.items():
            for surface_id, surface in SURFACES.items():
                if cracks_for_real(lamp, surface):
                    combos.append((visitor_id, lamp_id, surface_id))
    return combos


@dataclass
class StoryParams:
    visitor: str
    lamp: str
    surface: str
    choice: str
    name: str
    gender: str
    helper: str
    trait: str
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


def introduce(world: World, child: Entity, lamp_cfg: Lamp) -> None:
    trait = child.traits[0] if child.traits else "sleepy"
    world.say(
        f"One hush-soft night, {child.id} lay in bed feeling {trait} and wide-eyed all at once. "
        f"Beside the pillow, {lamp_cfg.phrase} {lamp_cfg.glow}."
    )


def hear_visitor(world: World, child: Entity, visitor: Visitor) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Then {child.pronoun('subject')} heard {visitor.call}. A {visitor.label} was outside the window; "
        f"{visitor.motion}. It was such a lovely nocturnal visitor that {child.id} wanted a closer look."
    )


def carry_lamp(world: World, child: Entity, surface: Surface) -> None:
    child.meters["carrying"] += 1
    world.say(
        f"{child.id} lifted the little lamp with both hands and padded toward the window above {surface.phrase}."
    )


def drop_lamp(world: World, child: Entity, lamp: Entity, surface_cfg: Surface) -> None:
    lamp.meters["dropped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But one foot caught in the blanket fringe. The lamp slipped, bumped {surface_cfg.phrase} with a {surface_cfg.sound}, "
        f"and a thin crack ran across it like a crooked silver thread."
    )


def feel_worry(world: World, child: Entity, lamp_cfg: Lamp, helper: Entity) -> None:
    child.memes["worry"] += 1
    pred = predict_shatter(lamp_cfg, SURFACES[world.facts["surface_id"]], "hide")
    world.facts["predicted_hide"] = pred["will_shatter_if_hidden"]
    world.facts["predicted_score"] = pred["score"]
    world.say(
        f"{child.id}'s heart gave a guilty little thump. {child.pronoun('subject').capitalize()} knew a crack in {lamp_cfg.shell} "
        f"could turn into a dangerous shard if nobody helped."
    )
    world.say(
        f"{helper.label_word.capitalize()} was just down the hall, but for one breath {child.id} wondered whether to whisper the truth or hide the trouble under the quilt."
    )


def tell_truth(world: World, child: Entity, helper: Entity) -> None:
    child.memes["honesty"] += 1
    child.memes["relief"] += 1
    world.say(
        f'"{helper.label_word.capitalize()}," {child.id} called softly, "I dropped my lamp, and now it has a crack."'
    )


def helper_secures(world: World, child: Entity, helper: Entity, lamp_cfg: Lamp) -> None:
    lamp = world.get("lamp")
    room = world.get("room")
    room.meters["danger"] = 0.0
    child.memes["fear"] = 0.0
    helper.memes["care"] += 1
    lamp.meters["retired"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came in with calm feet, took the lamp gently away, and said that telling the truth fast was the safest thing. "
        f"{helper.pronoun('subject').capitalize()} wrapped the broken lamp in a towel before any shard could shake loose."
    )
    world.say(
        f"Then {helper.pronoun('subject')} set {lamp_cfg.safe_replacement} on the table. It {lamp_cfg.replacement_glow}."
    )


def hide_damage(world: World, child: Entity) -> None:
    child.memes["hiding"] += 1
    child.meters["touching_broken"] += 1
    world.say(
        f"{child.id} pulled the blanket close and tried to turn the cracked lamp so the broken side faced the wall. "
        f"{child.pronoun('subject').capitalize()} hoped morning might somehow fix it."
    )


def shatter_scene(world: World, child: Entity, helper: Entity) -> None:
    lamp = world.get("lamp")
    propagate(world, narrate=False)
    world.say(
        f"But the crack widened with a dry little tick. A bright shard snapped free, skipped across the floor, and nicked {child.id}'s finger."
    )
    if child.meters["cut"] >= THRESHOLD:
        world.say(
            f"{child.id} gasped, more frightened than hurt, and called for {helper.label_word} at once."
        )


def helper_after_shatter(world: World, child: Entity, helper: Entity, lamp_cfg: Lamp) -> None:
    room = world.get("room")
    lamp = world.get("lamp")
    helper.memes["care"] += 1
    room.meters["danger"] = 0.0
    lamp.meters["retired"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{helper.label_word.capitalize()} hurried in, lifted {child.id} onto the bed, washed the tiny cut, and swept up every shard carefully."
    )
    world.say(
        f'"Broken things are not for hiding," {helper.pronoun("subject")} said gently. "When you tell me right away, I can keep you safe."'
    )
    world.say(
        f"After that, {helper.pronoun('subject')} brought {lamp_cfg.safe_replacement}, which {lamp_cfg.replacement_glow}."
    )


def closing_safe(world: World, child: Entity, helper: Entity, visitor: Visitor) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Together they looked out once more. The nocturnal {visitor.label} was still there for a moment, and the room felt quiet again."
    )
    world.say(
        f"Soon {child.id} tucked under the blankets, warm and truthful, while the new light kept watch in the corner."
    )


def closing_caution(world: World, child: Entity, helper: Entity, visitor: Visitor) -> None:
    world.say(
        f"The nocturnal {visitor.label} had already slipped back into the dark garden, but the room felt safe again."
    )
    world.say(
        f"{child.id} curled close to {helper.label_word} and learned that a small truth told early is gentler than a bigger fright later."
    )


def tell_story(
    visitor_cfg: Visitor,
    lamp_cfg: Lamp,
    surface_cfg: Surface,
    choice: str,
    name: str,
    gender: str,
    helper_type: str,
    trait: str,
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
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label="the grown-up",
            role="helper",
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="bedroom",
            label="bedroom",
        )
    )
    lamp = world.add(
        Entity(
            id="lamp",
            type="lamp",
            label=lamp_cfg.label,
            fragile=lamp_cfg.fragile,
            brittle=lamp_cfg.brittle,
            glowing=True,
            attrs={"fragility": lamp_cfg.fragility, "shell": lamp_cfg.shell},
        )
    )
    surface = world.add(
        Entity(
            id="surface",
            type="surface",
            label=surface_cfg.label,
            attrs={"hardness": surface_cfg.hardness},
        )
    )

    world.facts["visitor_id"] = visitor_cfg.id
    world.facts["lamp_id"] = lamp_cfg.id
    world.facts["surface_id"] = surface_cfg.id
    world.facts["choice"] = choice

    introduce(world, child, lamp_cfg)
    hear_visitor(world, child, visitor_cfg)

    world.para()
    carry_lamp(world, child, surface_cfg)
    drop_lamp(world, child, lamp, surface_cfg)
    feel_worry(world, child, lamp_cfg, helper)

    world.para()
    if choice == "tell":
        tell_truth(world, child, helper)
        helper_secures(world, child, helper, lamp_cfg)
        world.para()
        closing_safe(world, child, helper, visitor_cfg)
        outcome = "safe"
    else:
        hide_damage(world, child)
        propagate(world, narrate=False)
        shatter_scene(world, child, helper)
        helper_after_shatter(world, child, helper, lamp_cfg)
        world.para()
        closing_caution(world, child, helper, visitor_cfg)
        outcome = "shatter"

    world.facts.update(
        child=child,
        helper=helper,
        room=room,
        lamp=lamp,
        lamp_cfg=lamp_cfg,
        surface_cfg=surface_cfg,
        visitor=visitor_cfg,
        outcome=outcome,
        cracked=lamp.meters["cracked"] >= THRESHOLD,
        shattered=lamp.meters["shattered"] >= THRESHOLD,
        cut=child.meters["cut"] >= THRESHOLD,
        honest=child.memes["honesty"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    visitor = world.facts["visitor"]
    lamp_cfg = world.facts["lamp_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "safe":
        return [
            f'Write a bedtime story for a 3-to-5-year-old that includes the words "crack", "shard", and "nocturnal".',
            f"Tell a gentle bedtime story where {child.id} hears a nocturnal {visitor.label}, drops {lamp_cfg.phrase}, and tells the truth right away.",
            "Write a moral bedtime story where honesty after a small accident leads to comfort and safety.",
        ]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "crack", "shard", and "nocturnal".',
        f"Tell a cautionary bedtime story where {child.id} hears a nocturnal {visitor.label}, hides a crack in {lamp_cfg.phrase}, and learns why broken things must be shown to a grown-up.",
        "Write a moral bedtime story where hiding damage makes the problem bigger, but a calm grown-up still helps at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    visitor = world.facts["visitor"]
    lamp_cfg = world.facts["lamp_cfg"]
    surface_cfg = world.facts["surface_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was trying to look at a nocturnal {visitor.label} at bedtime, and {child.pronoun('possessive')} {helper.label_word} who helped afterward.",
        ),
        (
            f"Why did {child.id} pick up the lamp?",
            f"{child.id} heard {visitor.call} and wanted to see the nocturnal {visitor.label} more clearly. The soft nighttime wonder is what made {child.pronoun('object')} carry the lamp to the window.",
        ),
        (
            f"What happened to the lamp?",
            f"It slipped and hit {surface_cfg.phrase}, and a crack ran across it. Because the lamp was made of {lamp_cfg.shell}, that break could turn dangerous.",
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                f"What did {child.id} do after the lamp cracked?",
                f"{child.id} called for {helper.label_word} and told the truth right away. That quick honesty let the grown-up take the lamp away before any shard could come loose.",
            )
        )
        qa.append(
            (
                f"How did the story end?",
                f"It ended safely and softly. {helper.label_word.capitalize()} brought {lamp_cfg.safe_replacement}, and {child.id} settled back into bed feeling relieved and truthful.",
            )
        )
    else:
        qa.append(
            (
                f"Why did a shard come loose?",
                f"A shard came loose because {child.id} tried to hide the crack instead of showing it to a grown-up. The broken lamp was still being handled, so the damage grew worse.",
            )
        )
        qa.append(
            (
                f"What lesson did {child.id} learn?",
                f"{child.id} learned to tell the truth as soon as something breaks. A small truth would have brought help early and kept the scary moment from growing bigger.",
            )
        )
        if world.facts["cut"]:
            qa.append(
                (
                    f"Was {child.id} badly hurt?",
                    f"No, it was only a tiny cut. Still, it happened because broken things and sharp shard pieces are not safe for children to hide or touch.",
                )
            )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["visitor"].tags) | set(world.facts["lamp_cfg"].tags) | {"honesty"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("fragile", ent.fragile), ("brittle", ent.brittle), ("glowing", ent.glowing)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(lamp: Lamp, surface: Surface) -> str:
    if not lamp.fragile or not lamp.brittle or not lamp.sharp:
        return (
            f"(No story: {lamp.phrase} on {surface.phrase} would not make a real crack-and-shard hazard here. "
            "This world only tells cases where a broken lamp truly needs quick adult help.)"
        )
    return (
        f"(No story: dropping {lamp.phrase} on {surface.phrase} is too mild to guarantee a dangerous crack. "
        "Pick a more fragile lamp or a harder surface.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "safe" if params.choice == "tell" else "shatter"


ASP_RULES = r"""
valid(V, L, S) :- visitor(V), lamp(L), surface(S), fragile(L), brittle(L), sharp(L),
                  fragility(L, F), hardness(S, H), crack_min(M), F + H >= M.

outcome(safe) :- choice(tell).
outcome(shatter) :- choice(hide).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for visitor_id in VISITORS:
        lines.append(asp.fact("visitor", visitor_id))
    for lamp_id, lamp in LAMPS.items():
        lines.append(asp.fact("lamp", lamp_id))
        lines.append(asp.fact("fragility", lamp_id, lamp.fragility))
        if lamp.fragile:
            lines.append(asp.fact("fragile", lamp_id))
        if lamp.brittle:
            lines.append(asp.fact("brittle", lamp_id))
        if lamp.sharp:
            lines.append(asp.fact("sharp", lamp_id))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        lines.append(asp.fact("hardness", surface_id, surface.hardness))
    lines.append(asp.fact("crack_min", CRACK_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("choice", params.choice)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        visitor="owl",
        lamp="glass_moon",
        surface="floorboards",
        choice="tell",
        name="Lina",
        gender="girl",
        helper="mother",
        trait="curious",
    ),
    StoryParams(
        visitor="moth",
        lamp="porcelain_star",
        surface="stone_sill",
        choice="hide",
        name="Owen",
        gender="boy",
        helper="father",
        trait="gentle",
    ),
    StoryParams(
        visitor="hedgehog",
        lamp="glass_moon",
        surface="stone_sill",
        choice="tell",
        name="Maya",
        gender="girl",
        helper="grandmother",
        trait="quiet",
    ),
    StoryParams(
        visitor="owl",
        lamp="porcelain_star",
        surface="floorboards",
        choice="hide",
        name="Finn",
        gender="boy",
        helper="grandfather",
        trait="sleepy",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a nocturnal visitor, a cracked lamp, and the moral value of honesty."
    )
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lamp and args.surface:
        lamp = LAMPS[args.lamp]
        surface = SURFACES[args.surface]
        if not cracks_for_real(lamp, surface):
            raise StoryError(explain_rejection(lamp, surface))

    combos = [
        combo
        for combo in valid_combos()
        if (args.visitor is None or combo[0] == args.visitor)
        and (args.lamp is None or combo[1] == args.lamp)
        and (args.surface is None or combo[2] == args.surface)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    visitor_id, lamp_id, surface_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    choice = args.choice or rng.choice(["tell", "hide"])
    return StoryParams(
        visitor=visitor_id,
        lamp=lamp_id,
        surface=surface_id,
        choice=choice,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.visitor not in VISITORS:
        raise StoryError(f"(Unknown visitor: {params.visitor})")
    if params.lamp not in LAMPS:
        raise StoryError(f"(Unknown lamp: {params.lamp})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.choice not in CHOICES:
        raise StoryError(f"(Unknown choice: {params.choice})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.helper not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown helper: {params.helper})")

    lamp_cfg = LAMPS[params.lamp]
    surface_cfg = SURFACES[params.surface]
    if not cracks_for_real(lamp_cfg, surface_cfg):
        raise StoryError(explain_rejection(lamp_cfg, surface_cfg))

    world = tell_story(
        visitor_cfg=VISITORS[params.visitor],
        lamp_cfg=lamp_cfg,
        surface_cfg=surface_cfg,
        choice=params.choice,
        name=params.name,
        gender=params.gender,
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
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generated a normal story.")
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
        print(f"{len(combos)} compatible (visitor, lamp, surface) combos:\n")
        for visitor_id, lamp_id, surface_id in combos:
            print(f"  {visitor_id:9} {lamp_id:15} {surface_id}")
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
            header = f"### {p.name}: {p.visitor}, {p.lamp}, {p.surface}, {p.choice}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
