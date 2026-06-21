#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/memorial_ring_conflict_fairy_tale.py
===============================================================

A standalone story world for a fairy-tale conflict about a memorial ring.

Premise
-------
Two royal children are on their way to a memorial ceremony for someone beloved.
A ring kept in memory of that person becomes the center of a quarrel: both want
a claim on it, or one wants to hide it while the other wants it honored in the
open. A wise grown-up does not solve the story with a lecture alone. The world
model checks whether the obvious idea -- wearing the ring while walking to the
memorial -- would be risky, then chooses a sensible shared way to carry it.
The ending image proves that the children changed: they stop fighting over the
ring and honor the memory together.

Run it
------
    python storyworlds/worlds/gpt-5.4/memorial_ring_conflict_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/memorial_ring_conflict_fairy_tale.py --place willow_hill --ring tiny_pearl
    python storyworlds/worlds/gpt-5.4/memorial_ring_conflict_fairy_tale.py --resolution promise_turns --place willow_hill
    python storyworlds/worlds/gpt-5.4/memorial_ring_conflict_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/memorial_ring_conflict_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/memorial_ring_conflict_fairy_tale.py --verify
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
        female = {"girl", "princess", "mother", "queen", "woman"}
        male = {"boy", "prince", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"queen": "queen", "king": "king", "mother": "mother", "father": "father"}.get(
            self.type, self.type
        )
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
    image: str
    windy: bool = False
    long_walk: bool = False
    ceremony: str = ""
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
class Memory:
    id: str
    title: str
    virtue: str
    gift_line: str
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
class RingCfg:
    id: str
    label: str
    phrase: str
    size: str
    heavy: bool = False
    fragile: bool = False
    shine: str = ""
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
class ConflictCfg:
    id: str
    desire_line_a: str
    desire_line_b: str
    reason_a: str
    reason_b: str
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
class Resolution:
    id: str
    sense: int
    text: str
    qa_text: str
    ending_image: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"older_child", "younger_child"}]

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
        clone.facts = dict(self.facts)
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


def _r_quarrel(world: World) -> list[str]:
    a = world.get("child_a")
    b = world.get("child_b")
    if a.memes["claim"] < THRESHOLD or b.memes["claim"] < THRESHOLD:
        return []
    sig = ("quarrel",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["hurt"] += 1
    b.memes["hurt"] += 1
    a.memes["grief"] += 1
    b.memes["grief"] += 1
    return ["__quarrel__"]


def _r_wear_risk(world: World) -> list[str]:
    ring = world.get("ring")
    if ring.meters["worn"] < THRESHOLD:
        return []
    risky = world.place.windy or world.place.long_walk or ring.attrs.get("size") == "tiny" or ring.attrs.get("fragile")
    if not risky:
        return []
    sig = ("wear_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ring.meters["lost_risk"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__risk__"]


def _r_secure(world: World) -> list[str]:
    ring = world.get("ring")
    if ring.meters["on_ribbon"] < THRESHOLD and ring.meters["on_cushion"] < THRESHOLD and ring.meters["turns"] < THRESHOLD:
        return []
    sig = ("secure",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ring.meters["secure"] += 1
    ring.meters["lost_risk"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="wear_risk", tag="physical", apply=_r_wear_risk),
    Rule(name="secure", tag="physical", apply=_r_secure),
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


def wearing_is_risky(place: Place, ring: RingCfg) -> bool:
    return place.windy or place.long_walk or ring.size == "tiny" or ring.fragile


def resolution_allowed(place: Place, conflict: ConflictCfg, ring: RingCfg, resolution: Resolution) -> bool:
    if resolution.sense < SENSE_MIN:
        return False
    if resolution.id == "promise_turns":
        if conflict.id != "both_want_to_wear":
            return False
        if wearing_is_risky(place, ring):
            return False
        if ring.heavy or ring.fragile or ring.size == "tiny":
            return False
        return True
    if resolution.id == "blue_ribbon":
        if ring.heavy and place.long_walk:
            return False
        return True
    if resolution.id == "velvet_cushion":
        return True
    return False


def sensible_resolutions(place: Place, conflict: ConflictCfg, ring: RingCfg) -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if resolution_allowed(place, conflict, ring, r)]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for conflict_id, conflict in CONFLICTS.items():
            for ring_id, ring in RINGS.items():
                if sensible_resolutions(place, conflict, ring):
                    combos.append((place_id, conflict_id, ring_id))
    return combos


def explain_resolution(place: Place, conflict: ConflictCfg, ring: RingCfg, resolution: Resolution) -> str:
    if resolution.id == "promise_turns" and conflict.id != "both_want_to_wear":
        return (
            "(No story: taking turns wearing the memorial ring only fits a quarrel where both "
            "children want to wear it. This conflict needs a different kind of peace.)"
        )
    if resolution.id == "promise_turns" and wearing_is_risky(place, ring):
        return (
            f"(No story: wearing {ring.phrase} on the way to {place.label} would be too risky. "
            "The memorial ring could slip away before the ceremony, so choose a safer shared carrying plan.)"
        )
    if resolution.id == "promise_turns" and (ring.heavy or ring.fragile or ring.size == "tiny"):
        return (
            f"(No story: {ring.phrase} is not a good ring for taking turns wearing. "
            "It needs a steadier way to be carried to the memorial.)"
        )
    if resolution.id == "blue_ribbon" and ring.heavy and place.long_walk:
        return (
            f"(No story: {ring.phrase} is too heavy to trust to a ribbon on the long walk to {place.label}. "
            "A steadier cushion is the sensible choice.)"
        )
    return "(No story: that resolution does not fit this memorial-ring conflict.)"


def explain_combo(place: Place, conflict: ConflictCfg, ring: RingCfg) -> str:
    return (
        f"(No story: no sensible way to settle the conflict over {ring.phrase} at {place.label} "
        "was found. Try a different ring or a calmer resolution.)"
    )


def predict_wear_risk(world: World) -> dict:
    sim = world.copy()
    ring = sim.get("ring")
    ring.meters["worn"] += 1
    propagate(sim, narrate=False)
    return {
        "risky": ring.meters["lost_risk"] >= THRESHOLD,
        "lost_risk": ring.meters["lost_risk"],
    }


def opening(world: World, a: Entity, b: Entity, guardian: Entity, memory: Memory, ring: RingCfg) -> None:
    world.say(
        f"In the old kingdom where doves nested in the palace eaves, {a.id} and {b.id} woke before the bells. "
        f"That evening the castle would hold a memorial for {memory.title}, who was remembered for being {memory.virtue}."
    )
    world.say(
        f"{guardian.id}, the {guardian.label_word}, opened a carved cedar box and showed them {ring.phrase}. "
        f"{memory.gift_line}"
    )
    world.say(
        f"The ring gave a small {ring.shine}, as if it had saved one bright thought from yesterday."
    )


def arrive(world: World, place: Place) -> None:
    world.say(
        f"They set out for {place.label}, where {place.image} and where the people would gather for {place.ceremony}."
    )


def spark_conflict(world: World, a: Entity, b: Entity, conflict: ConflictCfg) -> None:
    a.memes["claim"] += 1
    b.memes["claim"] += 1
    propagate(world, narrate=False)
    world.say(f'"{conflict.desire_line_a}" said {a.id}. "{conflict.reason_a}"')
    world.say(f'"{conflict.desire_line_b}" said {b.id}. "{conflict.reason_b}"')
    world.say(
        "Their footsteps slowed. What had begun as remembrance turned sharp, and the quiet path filled with hurt voices."
    )


def guardian_warning(world: World, guardian: Entity, ring: RingCfg, place: Place) -> None:
    pred = predict_wear_risk(world)
    world.facts["predicted_risk"] = pred["risky"]
    if pred["risky"]:
        world.say(
            f'The {guardian.label_word} lifted a hand. "Hush now," {guardian.pronoun()} said. '
            f'"If one of you wears the memorial ring all the way to {place.label}, it may slip away before we arrive."'
        )
    else:
        world.say(
            f'The {guardian.label_word} listened carefully. "Hush now," {guardian.pronoun()} said. '
            '"The ring is precious enough that it must be carried with care, not tugged back and forth by two sad hearts."'
        )


def apply_resolution(world: World, a: Entity, b: Entity, guardian: Entity, resolution: Resolution) -> None:
    ring = world.get("ring")
    if resolution.id == "blue_ribbon":
        ring.meters["on_ribbon"] += 1
        world.say(
            f'The {guardian.label_word} drew a soft blue ribbon from {guardian.pronoun("possessive")} sleeve and threaded it through the ring. '
            f'"Then neither hand owns it alone," {guardian.pronoun()} said. "You may carry it together."'
        )
        world.say(
            f"{a.id} took one end of the ribbon, and {b.id} took the other. The ring swung between them like a little moon."
        )
    elif resolution.id == "velvet_cushion":
        ring.meters["on_cushion"] += 1
        world.say(
            f'The {guardian.label_word} set the ring on a square velvet cushion. '
            f'"Two pairs of hands can bear one memory," {guardian.pronoun()} said. "Carry it side by side."'
        )
        world.say(
            f"{a.id} held one corner, and {b.id} held the other two nearest corners together, walking so gently that not even the velvet wrinkled."
        )
    elif resolution.id == "promise_turns":
        ring.meters["turns"] += 1
        world.say(
            f'The {guardian.label_word} smiled a little. "Then let the path itself teach fairness," {guardian.pronoun()} said. '
            '"One of you may wear the ring to the silver gate, and the other may wear it from the gate to the memorial stone."'
        )
        world.say(
            f"{a.id} nodded first, and {b.id} nodded after. Between the gate and the stone, the ring changed hands without another cross word."
        )
    else:
        raise StoryError("(Internal error: unknown resolution.)")
    propagate(world, narrate=False)
    a.memes["claim"] = 0.0
    b.memes["claim"] = 0.0
    a.memes["peace"] += 1
    b.memes["peace"] += 1


def ceremony(world: World, a: Entity, b: Entity, guardian: Entity, memory: Memory, place: Place, resolution: Resolution) -> None:
    world.say(
        f"When they reached {place.label}, the quarrel had gone out of them. Together they laid the ring before the candles and spoke of {memory.title}."
    )
    world.say(
        f"{a.id} remembered how {memory.title} had been {memory.virtue}, and {b.id} remembered the same goodness in a different story."
    )
    world.say(
        f"The {guardian.label_word} bowed {guardian.pronoun('possessive')} head. {resolution.ending_image}"
    )


def closing(world: World, a: Entity, b: Entity, ring: RingCfg) -> None:
    world.say(
        f"After that day, whenever the cedar box was opened and the ring shone again, {a.id} and {b.id} no longer asked, "
        f'"Whose is it?" They asked, "How shall we honor the memory together?"'
    )
def tell(
    memory: Memory,
    ring_cfg: Ring,
    conflict: Conflict,
    resolution: Resolution,
    child_a_name: str,
    child_a_type: ChildAType,
    child_b_name: str,
    child_b_type: ChildBType,
    guardian_type: GuardianType,
    place=None,
) -> World:
    world = World(place=place)
    a = world.add(Entity(id="child_a", kind="character", type=child_a_type, role="older_child", label=child_a_name))
    b = world.add(Entity(id="child_b", kind="character", type=child_b_type, role="younger_child", label=child_b_name))
    guardian = world.add(Entity(id="guardian", kind="character", type=guardian_type, role="guardian", label="the guardian"))
    ring = world.add(
        Entity(
            id="ring",
            kind="thing",
            type="ring",
            label=ring_cfg.label,
            attrs={"size": ring_cfg.size, "heavy": ring_cfg.heavy, "fragile": ring_cfg.fragile},
        )
    )

    a.memes["grief"] = 1.0
    b.memes["grief"] = 1.0
    ring.meters["lost_risk"] = 0.0
    ring.meters["secure"] = 0.0
    ring.meters["worn"] = 0.0
    ring.meters["on_ribbon"] = 0.0
    ring.meters["on_cushion"] = 0.0
    ring.meters["turns"] = 0.0

    world.para()
    opening(world, a, b, guardian, memory, ring_cfg)
    arrive(world, place)

    world.para()
    spark_conflict(world, a, b, conflict)
    guardian_warning(world, guardian, ring_cfg, place)

    world.para()
    apply_resolution(world, a, b, guardian, resolution)
    ceremony(world, a, b, guardian, memory, place, resolution)

    world.para()
    closing(world, a, b, ring_cfg)

    world.facts.update(
        place=place,
        memory=memory,
        ring_cfg=ring_cfg,
        conflict=conflict,
        resolution=resolution,
        child_a=a,
        child_b=b,
        guardian=guardian,
        ring=ring,
        predicted_risk=world.facts.get("predicted_risk", False),
        outcome=outcome_of(
            StoryParams(
                place=place.id,
                memory=memory.id,
                ring=ring_cfg.id,
                conflict=conflict.id,
                resolution=resolution.id,
                child_a_name=child_a_name,
                child_a_type=child_a_type,
                child_b_name=child_b_name,
                child_b_type=child_b_type,
                guardian=guardian_type,
                seed=None,
            )
        ),
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


PLACES = {
    "moon_garden": Place(
        id="moon_garden",
        label="the Moon Garden",
        image="white roses leaned over the path",
        windy=False,
        long_walk=False,
        ceremony="the evening lamp-lighting",
        tags={"garden", "memorial"},
    ),
    "willow_hill": Place(
        id="willow_hill",
        label="Willow Hill",
        image="the grass bent under a hill wind",
        windy=True,
        long_walk=True,
        ceremony="the lantern circle",
        tags={"wind", "memorial"},
    ),
    "chapel_court": Place(
        id="chapel_court",
        label="the Chapel Court",
        image="stone birds watched from the fountain rim",
        windy=False,
        long_walk=True,
        ceremony="the bell-song at dusk",
        tags={"chapel", "memorial"},
    ),
}

MEMORIES = {
    "grandmother_queen": Memory(
        id="grandmother_queen",
        title="their grandmother the queen",
        virtue="gentle and brave",
        gift_line="She had worn it on feast days, and later it was kept as a memorial of her kindness.",
        tags={"grandmother", "memorial"},
    ),
    "old_king": Memory(
        id="old_king",
        title="the old king",
        virtue="steady and just",
        gift_line="He had kept it beside his writing desk, and now it rested in the cedar box as a memorial of his fair heart.",
        tags={"king", "memorial"},
    ),
    "forest_healer": Memory(
        id="forest_healer",
        title="the forest healer",
        virtue="wise and patient",
        gift_line="The healer had once pressed it into the queen's hand, and now the ring was kept as a memorial of many quiet mercies.",
        tags={"healer", "memorial"},
    ),
}

RINGS = {
    "tiny_pearl": RingCfg(
        id="tiny_pearl",
        label="pearl ring",
        phrase="a tiny pearl ring",
        size="tiny",
        heavy=False,
        fragile=False,
        shine="milk-white gleam",
        tags={"ring", "pearl"},
    ),
    "silver_flower": RingCfg(
        id="silver_flower",
        label="silver flower ring",
        phrase="a silver flower ring",
        size="small",
        heavy=False,
        fragile=False,
        shine="cool silver flash",
        tags={"ring", "silver"},
    ),
    "broad_signet": RingCfg(
        id="broad_signet",
        label="signet ring",
        phrase="a broad signet ring",
        size="large",
        heavy=True,
        fragile=False,
        shine="deep gold glimmer",
        tags={"ring", "gold"},
    ),
    "crystal_ring": RingCfg(
        id="crystal_ring",
        label="crystal ring",
        phrase="a crystal ring",
        size="small",
        heavy=False,
        fragile=True,
        shine="clear blue spark",
        tags={"ring", "crystal"},
    ),
}

CONFLICTS = {
    "both_want_to_wear": ConflictCfg(
        id="both_want_to_wear",
        desire_line_a="I should wear the ring",
        desire_line_b="No, I should wear it",
        reason_a="Grandmother told me the oldest story about it.",
        reason_b="And she sang to me while I watched it shine.",
        tags={"conflict", "sharing"},
    ),
    "keep_vs_share": ConflictCfg(
        id="keep_vs_share",
        desire_line_a="I want to hide the ring in my pocket until we arrive",
        desire_line_b="No, the people should see it at once",
        reason_a="If no one sees it on the road, no one can drop it.",
        reason_b="If no one sees it, the memorial will feel lonely before it begins.",
        tags={"conflict", "memorial"},
    ),
    "fear_of_loss": ConflictCfg(
        id="fear_of_loss",
        desire_line_a="I can carry the ring myself",
        desire_line_b="No, you must not, because it might be lost",
        reason_a="I will hold it very tightly.",
        reason_b="Tight hands can still stumble when hearts are sad.",
        tags={"conflict", "worry"},
    ),
}

RESOLUTIONS = {
    "blue_ribbon": Resolution(
        id="blue_ribbon",
        sense=3,
        text="threaded the ring on a blue ribbon so both children could carry it together",
        qa_text="The guardian put the ring on a blue ribbon so both children could share the duty of carrying it.",
        ending_image="The candles trembled, the ribbon lay still between the children, and peace looked brighter than gold.",
        tags={"ribbon", "sharing"},
    ),
    "velvet_cushion": Resolution(
        id="velvet_cushion",
        sense=3,
        text="set the ring on a velvet cushion and had the children carry it side by side",
        qa_text="The guardian set the ring on a velvet cushion and let the children carry it together with careful hands.",
        ending_image="The cushion moved as smoothly as a swan on water, and the two children walked in step at last.",
        tags={"cushion", "sharing"},
    ),
    "promise_turns": Resolution(
        id="promise_turns",
        sense=2,
        text="had the children take fair turns wearing the ring along different parts of the path",
        qa_text="The guardian made a fair plan so each child wore the ring for part of the walk and neither kept it alone.",
        ending_image="By the time the last bell faded, fairness had turned the quarrel into a promise kept.",
        tags={"fairness", "sharing"},
    ),
}

GIRL_NAMES = ["Elia", "Mira", "Nella", "Iris", "Talia", "Vera"]
BOY_NAMES = ["Rowan", "Alder", "Finn", "Lucan", "Orin", "Milo"]


KNOWLEDGE = {
    "memorial": [
        (
            "What is a memorial?",
            "A memorial is something people do or keep to remember someone they loved. It helps the heart say, 'I still remember you.'",
        )
    ],
    "ring": [
        (
            "What is a ring?",
            "A ring is a small circle of metal or another hard material that people can wear or keep safely. Some rings are special because they remind a family of someone important.",
        )
    ],
    "ribbon": [
        (
            "Why might someone put a ring on a ribbon?",
            "A ribbon can help carry a ring more safely, especially if the ring is small. It can also let two people share the job together.",
        )
    ],
    "cushion": [
        (
            "Why would a precious object be carried on a cushion?",
            "A cushion keeps a precious object steady and easy to see. It shows care and honor at the same time.",
        )
    ],
    "wind": [
        (
            "Why can wind make a small object harder to carry?",
            "Wind can shake hands, clothing, and ribbons, and it can distract people on a walk. That makes a tiny object easier to drop or lose.",
        )
    ],
    "sharing": [
        (
            "Why does sharing sometimes end a quarrel?",
            "Sharing can calm a quarrel because neither person is shut out. It turns 'mine' into 'ours,' which makes room for kindness again.",
        )
    ],
    "fairness": [
        (
            "What does fairness mean?",
            "Fairness means trying to treat people in an even and honest way. It does not always mean the same thing for everyone, but it should feel careful and kind.",
        )
    ],
}

KNOWLEDGE_ORDER = ["memorial", "ring", "ribbon", "cushion", "wind", "sharing", "fairness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    memory = f["memory"]
    ring = f["ring_cfg"]
    conflict = f["conflict"]
    resolution = f["resolution"]
    a = f["child_a"].label
    b = f["child_b"].label
    return [
        f'Write a fairy tale for a 3-to-5-year-old that includes a memorial and a ring, and centers on a conflict between two children on the way to {place.label}.',
        f"Tell a gentle palace fairy tale where {a} and {b} quarrel over {ring.phrase} kept for {memory.title}, and a wise grown-up helps them make peace.",
        f'Write a story with the words "memorial" and "ring" that begins with grief, turns into conflict, and ends with {resolution.id.replace("_", " ")} and shared remembrance.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    guardian = f["guardian"]
    place = f["place"]
    memory = f["memory"]
    ring = f["ring_cfg"]
    conflict = f["conflict"]
    resolution = f["resolution"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label}, two royal children, and the {guardian.label_word} who guided them. The story follows them on the way to a memorial for {memory.title}.",
        ),
        (
            "Why was the ring important?",
            f"The ring was important because it was kept as a memorial of {memory.title}. It mattered to both children because love and sadness were mixed together inside that memory.",
        ),
        (
            "What caused the conflict?",
            f"The conflict began when {a.label} and {b.label} both wanted a special claim on the ring. Their reasons came from love, but the hurt feeling grew because each child spoke as if the memory belonged to only one of them.",
        ),
    ]
    if f.get("predicted_risk"):
        qa.append(
            (
                f"Why did the {guardian.label_word} stop them from simply wearing the ring?",
                f"The {guardian.label_word} knew wearing the ring all the way to {place.label} would be risky. The ring was small or delicate enough, or the path rough enough, that it could have been lost before the memorial began.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the {guardian.label_word} still make them slow down?",
                f"The {guardian.label_word} wanted them to stop tugging the ring back and forth. Even without great danger, the memorial needed careful and peaceful hands instead of quarrelling ones.",
            )
        )
    qa.append(
        (
            "How was the problem solved?",
            f"{resolution.qa_text} That solved both the practical problem and the hurt feeling, because the children could honor the memory together instead of fighting over it.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children reaching the memorial in peace and speaking together about {memory.title}. The ending image shows they had changed, because they no longer asked who owned the ring alone.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"memorial", "ring", "sharing"}
    if f["resolution"].id == "blue_ribbon":
        tags.add("ribbon")
    if f["resolution"].id == "velvet_cushion":
        tags.add("cushion")
    if f["resolution"].id == "promise_turns":
        tags.add("fairness")
    if f["place"].windy:
        tags.add("wind")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(
        f"  place={world.place.id} windy={world.place.windy} long_walk={world.place.long_walk} ceremony={world.place.ceremony!r}"
    )
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    memory: str
    ring: str
    conflict: str
    resolution: str
    child_a_name: str
    child_a_type: str
    child_b_name: str
    child_b_type: str
    guardian: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="moon_garden",
        memory="grandmother_queen",
        ring="silver_flower",
        conflict="both_want_to_wear",
        resolution="promise_turns",
        child_a_name="Elia",
        child_a_type="princess",
        child_b_name="Rowan",
        child_b_type="prince",
        guardian="queen",
        seed=None,
    ),
    StoryParams(
        place="willow_hill",
        memory="old_king",
        ring="tiny_pearl",
        conflict="both_want_to_wear",
        resolution="blue_ribbon",
        child_a_name="Mira",
        child_a_type="princess",
        child_b_name="Alder",
        child_b_type="prince",
        guardian="king",
        seed=None,
    ),
    StoryParams(
        place="chapel_court",
        memory="forest_healer",
        ring="broad_signet",
        conflict="keep_vs_share",
        resolution="velvet_cushion",
        child_a_name="Iris",
        child_a_type="princess",
        child_b_name="Finn",
        child_b_type="prince",
        guardian="queen",
        seed=None,
    ),
    StoryParams(
        place="moon_garden",
        memory="forest_healer",
        ring="crystal_ring",
        conflict="fear_of_loss",
        resolution="velvet_cushion",
        child_a_name="Talia",
        child_a_type="princess",
        child_b_name="Orin",
        child_b_type="prince",
        guardian="king",
        seed=None,
    ),
]


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    child_type = rng.choice(["princess", "prince"])
    pool = [n for n in (GIRL_NAMES if child_type == "princess" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), child_type


def outcome_of(params: StoryParams) -> str:
    if params.resolution in {"blue_ribbon", "velvet_cushion"}:
        return "shared_carry"
    if params.resolution == "promise_turns":
        return "fair_turns"
    return "?"


ASP_RULES = r"""
sensible_resolution(P,C,R,blue_ribbon) :-
    place(P), conflict(C), ring(R), resolution(blue_ribbon),
    sense(blue_ribbon,S), sense_min(M), S >= M,
    not ribbon_bad(P,R).

ribbon_bad(P,R) :- heavy(R), long_walk(P).

sensible_resolution(P,C,R,velvet_cushion) :-
    place(P), conflict(C), ring(R), resolution(velvet_cushion),
    sense(velvet_cushion,S), sense_min(M), S >= M.

sensible_resolution(P,C,R,promise_turns) :-
    place(P), conflict(C), ring(R), resolution(promise_turns),
    sense(promise_turns,S), sense_min(M), S >= M,
    conflict_is(C,both_want_to_wear),
    not windy(P), not long_walk(P),
    not tiny(R), not fragile(R), not heavy(R).

valid(P,C,R) :- place(P), conflict(C), ring(R), sensible_resolution(P,C,R,_).

outcome(shared_carry) :- chosen_resolution(blue_ribbon).
outcome(shared_carry) :- chosen_resolution(velvet_cushion).
outcome(fair_turns)   :- chosen_resolution(promise_turns).

#show sensible_resolution/4.
#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.windy:
            lines.append(asp.fact("windy", place_id))
        if place.long_walk:
            lines.append(asp.fact("long_walk", place_id))
    for conflict_id in CONFLICTS:
        lines.append(asp.fact("conflict", conflict_id))
        lines.append(asp.fact("conflict_is", conflict_id, conflict_id))
    for ring_id, ring in RINGS.items():
        lines.append(asp.fact("ring", ring_id))
        if ring.size == "tiny":
            lines.append(asp.fact("tiny", ring_id))
        if ring.heavy:
            lines.append(asp.fact("heavy", ring_id))
        if ring.fragile:
            lines.append(asp.fact("fragile", ring_id))
    for resolution_id, resolution in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", resolution_id))
        lines.append(asp.fact("sense", resolution_id, resolution.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_resolutions(place_id: str, conflict_id: str, ring_id: str) -> list[str]:
    import asp

    extra = "\n".join(
        [
            asp.fact("query_place", place_id),
            asp.fact("query_conflict", conflict_id),
            asp.fact("query_ring", ring_id),
            "#show allowed/1.",
            "allowed(X) :- sensible_resolution(P,C,R,X), query_place(P), query_conflict(C), query_ring(R).",
        ]
    )
    model = asp.one_model(asp_program(extra))
    return sorted(x for (x,) in asp.atoms(model, "allowed"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_resolution", params.resolution),
            "#show outcome/1.",
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))
        if cl_valid - py_valid:
            print("  only in asp:", sorted(cl_valid - py_valid))

    for place_id, conflict_id, ring_id in sorted(list(py_valid))[:8]:
        py = sorted(r.id for r in sensible_resolutions(PLACES[place_id], CONFLICTS[conflict_id], RINGS[ring_id]))
        cl = asp_sensible_resolutions(place_id, conflict_id, ring_id)
        if py != cl:
            rc = 1
            print(f"MISMATCH sensible resolutions for {(place_id, conflict_id, ring_id)}: python={py} asp={cl}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Verify failed: generated empty story.)")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a memorial ring, a quarrel, and a shared resolution."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--ring", choices=RINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--guardian", choices=["queen", "king"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos and sensible resolutions from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.conflict and args.ring:
        place = PLACES[args.place]
        conflict = CONFLICTS[args.conflict]
        ring = RINGS[args.ring]
        if not sensible_resolutions(place, conflict, ring):
            raise StoryError(explain_combo(place, conflict, ring))
        if args.resolution and not resolution_allowed(place, conflict, ring, RESOLUTIONS[args.resolution]):
            raise StoryError(explain_resolution(place, conflict, ring, RESOLUTIONS[args.resolution]))
    elif args.resolution and args.place and args.ring and args.conflict:
        place = PLACES[args.place]
        conflict = CONFLICTS[args.conflict]
        ring = RINGS[args.ring]
        if not resolution_allowed(place, conflict, ring, RESOLUTIONS[args.resolution]):
            raise StoryError(explain_resolution(place, conflict, ring, RESOLUTIONS[args.resolution]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.conflict is None or combo[1] == args.conflict)
        and (args.ring is None or combo[2] == args.ring)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, conflict_id, ring_id = rng.choice(sorted(combos))
    memory_id = args.memory or rng.choice(sorted(MEMORIES))
    place = PLACES[place_id]
    conflict = CONFLICTS[conflict_id]
    ring = RINGS[ring_id]

    allowed = [r.id for r in sensible_resolutions(place, conflict, ring)]
    if args.resolution:
        if args.resolution not in allowed:
            raise StoryError(explain_resolution(place, conflict, ring, RESOLUTIONS[args.resolution]))
        resolution_id = args.resolution
    else:
        resolution_id = rng.choice(sorted(allowed))

    child_a_name, child_a_type = _pick_child(rng)
    child_b_name, child_b_type = _pick_child(rng, avoid=child_a_name)
    guardian = args.guardian or rng.choice(["queen", "king"])

    return StoryParams(
        place=place_id,
        memory=memory_id,
        ring=ring_id,
        conflict=conflict_id,
        resolution=resolution_id,
        child_a_name=child_a_name,
        child_a_type=child_a_type,
        child_b_name=child_b_name,
        child_b_type=child_b_type,
        guardian=guardian,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        memory = MEMORIES[params.memory]
        ring = RINGS[params.ring]
        conflict = CONFLICTS[params.conflict]
        resolution = RESOLUTIONS[params.resolution]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not sensible_resolutions(place, conflict, ring):
        raise StoryError(explain_combo(place, conflict, ring))
    if not resolution_allowed(place, conflict, ring, resolution):
        raise StoryError(explain_resolution(place, conflict, ring, resolution))

    world = tell(
        place=place,
        memory=memory,
        ring_cfg=ring,
        conflict=conflict,
        resolution=resolution,
        child_a_name=params.child_a_name,
        child_a_type=params.child_a_type,
        child_b_name=params.child_b_name,
        child_b_type=params.child_b_type,
        guardian_type=params.guardian,
    )

    return StorySample(
        params=params,
        story=world.render().replace("child_a", params.child_a_name).replace("child_b", params.child_b_name).replace("guardian", "Guardian"),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a.replace("child_a", params.child_a_name).replace("child_b", params.child_b_name)) for q, a in story_qa(world)],
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
        print(f"{len(combos)} compatible (place, conflict, ring) combos:\n")
        for place_id, conflict_id, ring_id in combos:
            allowed = asp_sensible_resolutions(place_id, conflict_id, ring_id)
            print(f"  {place_id:12} {conflict_id:18} {ring_id:12} [{', '.join(allowed)}]")
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
            header = (
                f"### {p.child_a_name} and {p.child_b_name}: {p.ring} at {p.place} "
                f"({p.conflict}, {p.resolution}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
