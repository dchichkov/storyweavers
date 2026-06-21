#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rupture_reconciliation_detective_story.py
====================================================================

A standalone story world about two child detectives, a torn clue-object, a wrong
suspicion, and reconciliation.

The seed asked for:
- the word "rupture"
- the feature "Reconciliation"
- the style "Detective Story"

This world models a small detective-story domain for young children: a junior
detective club discovers a fresh tear in an important paper or cloth object, one
child briefly suspects the other, physical clues reveal the true cause, and the
children repair both the object and their friendship.

Run it
------
    python storyworlds/worlds/gpt-5.4/rupture_reconciliation_detective_story.py
    python storyworlds/worlds/gpt-5.4/rupture_reconciliation_detective_story.py --place library --object banner --cause gust --repair paste
    python storyworlds/worlds/gpt-5.4/rupture_reconciliation_detective_story.py --repair tape --cause scooter_handle
    python storyworlds/worlds/gpt-5.4/rupture_reconciliation_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/rupture_reconciliation_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rupture_reconciliation_detective_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/rupture_reconciliation_detective_story.py --json
    python storyworlds/worlds/gpt-5.4/rupture_reconciliation_detective_story.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"              # character | thing | relation | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    material: str = ""
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    afford_causes: set[str] = field(default_factory=set)
    detective_touch: str = ""
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
class MysteryObject:
    id: str
    label: str
    phrase: str
    material: str
    hangs_at: str
    purpose: str
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
    verb: str
    clue: str
    clue_place: str
    severity: int
    materials: set[str] = field(default_factory=set)
    places: set[str] = field(default_factory=set)
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
class Repair:
    id: str
    label: str
    action: str
    result: str
    qa_text: str
    power: int
    materials: set[str] = field(default_factory=set)
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


def _r_torn_alarm(world: World) -> list[str]:
    obj = world.get("object")
    if obj.meters["torn"] < THRESHOLD:
        return []
    sig = ("torn_alarm", obj.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("case").meters["mystery"] += 1
    for eid in ("sleuth", "partner"):
        world.get(eid).memes["worry"] += 1
    return []


def _r_blame_rupture(world: World) -> list[str]:
    relation = world.get("bond")
    partner = world.get("partner")
    sleuth = world.get("sleuth")
    if partner.memes["blamed"] < THRESHOLD:
        return []
    sig = ("blame_rupture", partner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    relation.meters["rupture"] += 1
    partner.memes["hurt"] += 1
    sleuth.memes["guilt_seed"] += 1
    return []


def _r_clue_relief(world: World) -> list[str]:
    if world.get("clue").meters["found"] < THRESHOLD:
        return []
    sig = ("clue_relief", "clue")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("sleuth").memes["certainty"] += 1
    world.get("partner").memes["hope"] += 1
    return []


def _r_apology_reconcile(world: World) -> list[str]:
    relation = world.get("bond")
    if relation.meters["rupture"] < THRESHOLD:
        return []
    if world.get("sleuth").memes["apology"] < THRESHOLD:
        return []
    sig = ("apology_reconcile", "bond")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    relation.meters["rupture"] = 0.0
    relation.meters["reconciled"] += 1
    world.get("partner").memes["hurt"] = 0.0
    world.get("partner").memes["trust"] += 1
    world.get("sleuth").memes["relief"] += 1
    world.get("partner").memes["relief"] += 1
    return []


def _r_repair_pride(world: World) -> list[str]:
    obj = world.get("object")
    if obj.meters["repaired"] < THRESHOLD:
        return []
    sig = ("repair_pride", obj.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("sleuth", "partner"):
        world.get(eid).memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="torn_alarm", tag="physical", apply=_r_torn_alarm),
    Rule(name="blame_rupture", tag="social", apply=_r_blame_rupture),
    Rule(name="clue_relief", tag="detective", apply=_r_clue_relief),
    Rule(name="apology_reconcile", tag="social", apply=_r_apology_reconcile),
    Rule(name="repair_pride", tag="resolution", apply=_r_repair_pride),
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
                # already fired earlier; no new change from this check
                pass
        prev = len(world.fired)
        # detect new firings with no emitted sentences
        if len(world.fired) != prev:
            changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def cause_can_tear(place: Place, obj: MysteryObject, cause: Cause) -> bool:
    return (
        cause.id in place.afford_causes
        and obj.material in cause.materials
        and place.id in cause.places
    )


def repair_fits(obj: MysteryObject, cause: Cause, repair: Repair) -> bool:
    return obj.material in repair.materials and repair.power >= cause.severity


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for object_id, obj in OBJECTS.items():
            for cause_id, cause in CAUSES.items():
                if not cause_can_tear(place, obj, cause):
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair_fits(obj, cause, repair):
                        combos.append((place_id, object_id, cause_id, repair_id))
    return combos


def explain_combo_rejection(place: Place, obj: MysteryObject, cause: Cause) -> str:
    if cause.id not in place.afford_causes or place.id not in cause.places:
        return (
            f"(No story: {cause.label} is not a plausible cause in {place.label}. "
            f"Choose a place where that clue could honestly happen.)"
        )
    if obj.material not in cause.materials:
        return (
            f"(No story: {cause.label} would not make a believable tear in {obj.phrase}. "
            f"The physical cause and material do not match.)"
        )
    return "(No story: this cause does not fit this place and object.)"


def explain_repair_rejection(obj: MysteryObject, cause: Cause, repair: Repair) -> str:
    if obj.material not in repair.materials:
        return (
            f"(No story: {repair.label} is not the right kind of fix for {obj.material}. "
            f"Pick a repair that really works on that material.)"
        )
    return (
        f"(No story: {repair.label} is too weak for this tear. "
        f"The rupture from {cause.label} needs a stronger repair.)"
    )


def outcome_of(params: "StoryParams") -> str:
    return "deep_reconciliation" if params.suspicion == "accuse" else "gentle_reconciliation"


# ---------------------------------------------------------------------------
# Detective screenplay helpers
# ---------------------------------------------------------------------------
def discover_rupture(world: World, obj: Entity, obj_cfg: MysteryObject, place: Place) -> None:
    obj.meters["torn"] += 1
    obj.meters["severity"] = float(world.facts["cause"].severity)
    propagate(world, narrate=False)
    world.say(
        f"That morning, {place.scene} was ready for the Junior Sleuths. "
        f"Then both children stopped short. A fresh rupture ran across {obj_cfg.phrase} "
        f"at {obj_cfg.hangs_at}."
    )
    world.say(
        f"The little club needed it for {obj_cfg.purpose}, so the tear felt like a real case."
    )


def predict_cause(world: World) -> dict:
    sim = world.copy()
    obj = sim.get("object")
    obj.meters["torn"] += 1
    propagate(sim, narrate=False)
    return {
        "mystery": sim.get("case").meters["mystery"],
        "worry": sim.get("sleuth").memes["worry"] + sim.get("partner").memes["worry"],
    }


def introduce(world: World, sleuth: Entity, partner: Entity, place: Place) -> None:
    for kid in (sleuth, partner):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"{sleuth.id} and {partner.id} liked to call themselves the Junior Sleuths. "
        f"In {place.label}, they carried a stubby pencil, a notebook, and one bright idea after another."
    )
    world.say(place.detective_touch)


def suspicion_beat(world: World, sleuth: Entity, partner: Entity, params: "StoryParams") -> None:
    pred = predict_cause(world)
    world.facts["predicted_mystery"] = pred["mystery"]
    if params.suspicion == "accuse":
        partner.memes["blamed"] += 1
        sleuth.memes["certainty"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{sleuth.id} crouched beside the tear and whispered, "You were here first, {partner.id}. '
            f'Did you pull it by mistake?"'
        )
        world.say(
            f"{partner.id}'s face fell. For one quiet second, a sharper rupture opened between the two friends than the one in the torn object."
        )
    else:
        sleuth.memes["doubt"] += 1
        partner.memes["worry"] += 1
        world.say(
            f'{sleuth.id} pressed the notebook to {sleuth.pronoun("possessive")} chest. '
            f'"Something happened here," {sleuth.pronoun()} said softly. "But let\'s not blame anyone before we look."'
        )
        world.say(
            f"{partner.id} nodded, still worried, and stayed close enough for their shoulders to touch."
        )


def investigate(world: World, sleuth: Entity, partner: Entity, cause: Cause) -> None:
    clue = world.get("clue")
    clue.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They searched like real detectives. Soon {partner.id} spotted {cause.clue} {cause.clue_place}."
    )
    world.say(
        f"That clue pointed to {cause.label}, not to either child. The case turned at once."
    )


def clear_friend(world: World, sleuth: Entity, partner: Entity, params: "StoryParams") -> None:
    if params.suspicion == "accuse":
        sleuth.memes["apology"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{sleuth.id} looked at the clue, then at {partner.id}. "I was wrong," {sleuth.pronoun()} said. '
            f'"I should have trusted you."'
        )
        world.say(
            f"{partner.id} took a slow breath. The hurt did not vanish in one blink, but the apology stitched the friendship closed enough for both of them to smile again."
        )
    else:
        world.get("bond").meters["reconciled"] += 1
        partner.memes["relief"] += 1
        sleuth.memes["relief"] += 1
        world.say(
            f"{sleuth.id} grinned with relief. The mystery had nearly made trouble, but the two detectives had stayed on the same side."
        )


def repair_object(world: World, sleuth: Entity, partner: Entity, repair: Repair, obj_cfg: MysteryObject) -> None:
    obj = world.get("object")
    obj.meters["repaired"] += 1
    obj.meters["torn"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Now they turned from solving the case to fixing the damage. Together they {repair.action}."
    )
    world.say(
        f"When they finished, {repair.result} and the club could still use it for {obj_cfg.purpose}."
    )


def ending(world: World, sleuth: Entity, partner: Entity, place: Place, params: "StoryParams") -> None:
    if params.suspicion == "accuse":
        world.say(
            f"Before they packed up the notebook, {partner.id} bumped {sleuth.id}'s shoulder and said, "
            f'"Next time, Detective, follow the clues first."'
        )
        world.say(
            f"{sleuth.id} laughed, and the sound echoed warmly through {place.label}. The case was closed, the rupture was mended, and the friendship was stronger because truth and apology had both been brave."
        )
    else:
        world.say(
            f"At the end, the repaired clue-object hung steady while the two children stood under it, shoulder to shoulder like partners in a proper detective story."
        )
        world.say(
            f"In {place.label}, they had solved the mystery without letting fear push them apart, and that gentle kind of reconciliation felt like its own bright clue."
        )
def tell(
    obj_cfg: Obj,
    cause: Cause,
    repair: Repair,
    sleuth_name: str,
    sleuth_gender: str,
    partner_name: str,
    partner_gender: str,
    suspicion: Suspicion,
    helper_type: HelperType,
    place=None,
) -> World:
    world = World()
    world.facts["place"] = place
    world.facts["object_cfg"] = obj_cfg
    world.facts["cause"] = cause
    world.facts["repair"] = repair
    world.facts["suspicion"] = suspicion

    sleuth = world.add(Entity(
        id=sleuth_name,
        kind="character",
        type=sleuth_gender,
        role="sleuth",
        traits=["careful", "observant"],
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=["steady", "kind"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    world.add(Entity(id="place", kind="place", type="place", label=place.label))
    world.add(Entity(
        id="object",
        kind="thing",
        type=obj_cfg.id,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        material=obj_cfg.material,
    ))
    world.add(Entity(id="clue", kind="thing", type="clue", label="the clue"))
    world.add(Entity(id="case", kind="thing", type="case", label="the case"))
    world.add(Entity(id="bond", kind="relation", type="friendship", label="their friendship"))

    introduce(world, sleuth, partner, place)
    world.para()
    discover_rupture(world, world.get("object"), obj_cfg, place)
    suspicion_beat(world, sleuth, partner, StoryParams(
        place=place.id,
        object=obj_cfg.id,
        cause=cause.id,
        repair=repair.id,
        suspicion=suspicion,
        sleuth=sleuth_name,
        sleuth_gender=sleuth_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        helper=helper_type,
        seed=None,
    ))
    world.para()
    investigate(world, sleuth, partner, cause)
    clear_friend(world, sleuth, partner, StoryParams(
        place=place.id,
        object=obj_cfg.id,
        cause=cause.id,
        repair=repair.id,
        suspicion=suspicion,
        sleuth=sleuth_name,
        sleuth_gender=sleuth_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        helper=helper_type,
        seed=None,
    ))
    repair_object(world, sleuth, partner, repair, obj_cfg)
    world.para()
    ending(world, sleuth, partner, place, StoryParams(
        place=place.id,
        object=obj_cfg.id,
        cause=cause.id,
        repair=repair.id,
        suspicion=suspicion,
        sleuth=sleuth_name,
        sleuth_gender=sleuth_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        helper=helper_type,
        seed=None,
    ))

    world.facts.update(
        sleuth=sleuth,
        partner=partner,
        helper=helper,
        object=world.get("object"),
        clue=world.get("clue"),
        relation=world.get("bond"),
        outcome="deep_reconciliation" if suspicion == "accuse" else "gentle_reconciliation",
        repaired=True,
        rupture_happened=world.get("bond").meters["reconciled"] >= THRESHOLD or suspicion == "accuse",
    )
    return world


# ---------------------------------------------------------------------------
# Content
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


PLACES = {
    "library": Place(
        id="library",
        label="the library reading room",
        scene="Sunlight lay across the carpet and the low shelves stood like rows of patient witnesses.",
        afford_causes={"gust"},
        detective_touch="Everything felt hushed except for the tiny scratch of their pencil, which made the room seem full of important clues.",
    ),
    "hall": Place(
        id="hall",
        label="the school hallway",
        scene="The hallway smelled like crayons and floor wax, and every bulletin board looked ready to hide a secret.",
        afford_causes={"gust", "scooter_handle"},
        detective_touch="Their shoes tapped along the tiles as if they were following clues in a grand city mystery.",
    ),
    "gate": Place(
        id="gate",
        label="the garden gate",
        scene="The gate stood between marigolds and beans, with leaves flicking in the breeze like green little hands.",
        afford_causes={"puppy_paw", "gust", "scooter_handle"},
        detective_touch="The children whispered over each detail as if the flowers themselves might overhear the case.",
    ),
}

OBJECTS = {
    "banner": MysteryObject(
        id="banner",
        label="banner",
        phrase="the Mystery Club banner",
        material="paper",
        hangs_at="the string above the table",
        purpose="their afternoon detective meeting",
        tags={"paper", "banner"},
    ),
    "map": MysteryObject(
        id="map",
        label="map",
        phrase="the hand-drawn clue map",
        material="paper",
        hangs_at="the corkboard",
        purpose="their treasure hunt investigation",
        tags={"paper", "map"},
    ),
    "sash": MysteryObject(
        id="sash",
        label="sash",
        phrase="the cloth detective sash",
        material="cloth",
        hangs_at="the hook by the door",
        purpose="the grand closing of the case",
        tags={"cloth", "sash"},
    ),
}

CAUSES = {
    "gust": Cause(
        id="gust",
        label="a gust from an open window",
        verb="snapped the hanging edge hard",
        clue="one pin bent sideways and a curtain puffing out",
        clue_place="beside the window",
        severity=1,
        materials={"paper"},
        places={"library", "hall", "gate"},
        tags={"wind", "window"},
    ),
    "puppy_paw": Cause(
        id="puppy_paw",
        label="a puppy's playful paw",
        verb="caught the edge and tugged",
        clue="a muddy paw print and one loose thread",
        clue_place="near the bottom hook",
        severity=2,
        materials={"cloth"},
        places={"gate"},
        tags={"puppy", "cloth"},
    ),
    "scooter_handle": Cause(
        id="scooter_handle",
        label="a scooter handle passing too close",
        verb="hooked the edge and yanked",
        clue="a silver scrape and a line in the dust",
        clue_place="along the wall",
        severity=2,
        materials={"paper", "cloth"},
        places={"hall", "gate"},
        tags={"scooter", "scrape"},
    ),
}

REPAIRS = {
    "tape": Repair(
        id="tape",
        label="clear tape",
        action="smoothed clear tape over the tear from both sides",
        result="the patch lay flat and tidy",
        qa_text="smoothed clear tape over the tear",
        power=1,
        materials={"paper"},
        tags={"tape", "paper_fix"},
    ),
    "paste": Repair(
        id="paste",
        label="paper paste",
        action="brushed a little paper paste under the torn flap and pressed it gently",
        result="the paper dried almost as neat as before",
        qa_text="used paper paste and pressed the torn flap back into place",
        power=2,
        materials={"paper"},
        tags={"paste", "paper_fix"},
    ),
    "stitches": Repair(
        id="stitches",
        label="small stitches",
        action="set tiny stitches along the split with careful fingers",
        result="the cloth looked strong again, with only a slim line to show the accident",
        qa_text="sewed tiny stitches along the split",
        power=2,
        materials={"cloth"},
        tags={"stitches", "cloth_fix"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lucy", "Ava", "June", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Finn", "Owen", "Sam", "Eli"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "wind": [
        (
            "What can a gust of wind do to paper?",
            "A gust of wind can flap paper very hard. If the paper is pinned or caught, it can tear."
        )
    ],
    "window": [
        (
            "Why can an open window change what happens in a room?",
            "An open window lets moving air come in. That air can push light things like curtains and paper."
        )
    ],
    "puppy": [
        (
            "Why do puppies sometimes damage things by accident?",
            "Puppies are playful and curious. They can snag or tug things without meaning to be naughty."
        )
    ],
    "scooter": [
        (
            "How can a scooter handle snag something?",
            "A handle sticks out from the side. If it passes too close to cloth or paper, it can catch and pull."
        )
    ],
    "tape": [
        (
            "What is clear tape for?",
            "Clear tape holds two paper edges together. It is a simple way to patch a small tear."
        )
    ],
    "paste": [
        (
            "What does paper paste do?",
            "Paper paste helps a torn flap stick back down. When it dries, the paper can lie smooth again."
        )
    ],
    "stitches": [
        (
            "Why do stitches help cloth?",
            "Stitches hold the fabric together with thread. They are a strong way to mend a split in cloth."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people come back together after hurt or anger. It often needs truth, apology, and kindness."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries not to guess too fast. Good detectives let evidence lead the way."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "reconciliation", "wind", "window", "puppy", "scooter", "tape", "paste", "stitches"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    obj = f["object_cfg"]
    cause = f["cause"]
    suspicion = f["suspicion"]
    if suspicion == "accuse":
        return [
            f'Write a detective story for a 3-to-5-year-old that includes the word "rupture" and ends in reconciliation.',
            f"Tell a gentle mystery where two child detectives find a tear in {obj.phrase} at {place.label}, one friend is wrongly suspected, and a clue proves {cause.label} caused the damage.",
            f"Write a short case story where an apology matters as much as solving the mystery, and the children mend both the torn object and their friendship.",
        ]
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the word "rupture" and features reconciliation without a big fight.',
        f"Tell a mystery where two child detectives find a tear in {obj.phrase} at {place.label}, stay calm, discover that {cause.label} caused it, and fix the damage together.",
        f"Write a small detective tale where clues prevent unfair blame and the ending shows two children standing together again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    partner = f["partner"]
    place = f["place"]
    obj = f["object_cfg"]
    cause = f["cause"]
    repair = f["repair"]
    outcome = f["outcome"]
    relation = f["relation"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two child detectives, {sleuth.id} and {partner.id}. They were working together in {place.label} when they found the damage."
        ),
        (
            "What was the mystery?",
            f"The mystery was a fresh rupture in {obj.phrase}. The object mattered because the club needed it for {obj.purpose}."
        ),
        (
            "What clue solved the case?",
            f"The children found {cause.clue} {cause.clue_place}. That clue showed that {cause.label} had made the tear, not either child."
        ),
    ]
    if outcome == "deep_reconciliation":
        qa.append(
            (
                f"Why did {partner.id} feel hurt?",
                f"{partner.id} felt hurt because {sleuth.id} wrongly suspected {partner.pronoun('object')} before checking the clues. That false blame opened a friendship rupture, not just a tear in the object."
            )
        )
        qa.append(
            (
                "How did the children reconcile?",
                f"{sleuth.id} apologized after the clue proved the truth, and {partner.id} accepted the apology. Then they repaired the object together, which helped show that trust had come back."
            )
        )
    else:
        qa.append(
            (
                "How did they avoid a fight?",
                f"They chose to look for evidence before blaming anyone. Because they stayed on the same side of the mystery, fear never turned into a bigger friendship rupture."
            )
        )
    qa.append(
        (
            "How did they fix the damaged object?",
            f"They {repair.qa_text}. Fixing the object mattered because it let them continue {obj.purpose} after the mystery was solved."
        )
    )
    repaired_line = "Their friendship ended stronger after the apology." if relation.meters["reconciled"] >= THRESHOLD else "Their teamwork stayed gentle and steady."
    qa.append(
        (
            "How did the story end?",
            f"It ended with the case solved, the object mended, and the two children together again. {repaired_line}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "reconciliation"} | set(world.facts["cause"].tags) | set(world.facts["repair"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.material:
            bits.append(f"material={ent.material}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    object: str
    cause: str
    repair: str
    suspicion: str
    sleuth: str
    sleuth_gender: str
    partner: str
    partner_gender: str
    helper: str = "librarian"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="library",
        object="banner",
        cause="gust",
        repair="paste",
        suspicion="accuse",
        sleuth="Nora",
        sleuth_gender="girl",
        partner="Ben",
        partner_gender="boy",
        helper="librarian",
        seed=None,
    ),
    StoryParams(
        place="hall",
        object="map",
        cause="scooter_handle",
        repair="paste",
        suspicion="wonder",
        sleuth="Leo",
        sleuth_gender="boy",
        partner="Mia",
        partner_gender="girl",
        helper="teacher",
        seed=None,
    ),
    StoryParams(
        place="gate",
        object="sash",
        cause="puppy_paw",
        repair="stitches",
        suspicion="accuse",
        sleuth="June",
        sleuth_gender="girl",
        partner="Finn",
        partner_gender="boy",
        helper="mother",
        seed=None,
    ),
    StoryParams(
        place="hall",
        object="banner",
        cause="gust",
        repair="tape",
        suspicion="wonder",
        sleuth="Ella",
        sleuth_gender="girl",
        partner="Theo",
        partner_gender="boy",
        helper="teacher",
        seed=None,
    ),
    StoryParams(
        place="gate",
        object="sash",
        cause="scooter_handle",
        repair="stitches",
        suspicion="accuse",
        sleuth="Ruby",
        sleuth_gender="girl",
        partner="Max",
        partner_gender="boy",
        helper="father",
        seed=None,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P,O,C,R) :- place(P), object(O), cause(C), repair(R),
                  affords(P,C), occurs_in(C,P),
                  material_of(O,M), tears(C,M),
                  fixes(R,M), power(R,RP), severity(C,CS), RP >= CS.

deep_reconciliation :- suspicion(accuse).
gentle_reconciliation :- suspicion(wonder).

outcome(deep_reconciliation) :- deep_reconciliation.
outcome(gentle_reconciliation) :- gentle_reconciliation.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for cause_id in sorted(place.afford_causes):
            lines.append(asp.fact("affords", pid, cause_id))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("material_of", oid, obj.material))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("severity", cid, cause.severity))
        for mat in sorted(cause.materials):
            lines.append(asp.fact("tears", cid, mat))
        for place_id in sorted(cause.places):
            lines.append(asp.fact("occurs_in", cid, place_id))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("power", rid, repair.power))
        for mat in sorted(repair.materials):
            lines.append(asp.fact("fixes", rid, mat))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("suspicion", params.suspicion)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective story world: a torn clue-object, a wrong suspicion, and reconciliation."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--object", choices=sorted(OBJECTS))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--repair", choices=sorted(REPAIRS))
    ap.add_argument("--suspicion", choices=["accuse", "wonder"])
    ap.add_argument("--helper", choices=["librarian", "teacher", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.object and args.cause:
        place = PLACES[args.place]
        obj = OBJECTS[args.object]
        cause = CAUSES[args.cause]
        if not cause_can_tear(place, obj, cause):
            raise StoryError(explain_combo_rejection(place, obj, cause))
    if args.object and args.cause and args.repair:
        obj = OBJECTS[args.object]
        cause = CAUSES[args.cause]
        repair = REPAIRS[args.repair]
        if not repair_fits(obj, cause, repair):
            raise StoryError(explain_repair_rejection(obj, cause, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.object is None or combo[1] == args.object)
        and (args.cause is None or combo[2] == args.cause)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, object_id, cause_id, repair_id = rng.choice(sorted(combos))
    suspicion = args.suspicion or rng.choice(["accuse", "wonder"])
    sleuth_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    sleuth_name = pick_name(rng, sleuth_gender)
    partner_name = pick_name(rng, partner_gender, avoid=sleuth_name)
    helper = args.helper or rng.choice(["librarian", "teacher", "mother", "father"])

    return StoryParams(
        place=place_id,
        object=object_id,
        cause=cause_id,
        repair=repair_id,
        suspicion=suspicion,
        sleuth=sleuth_name,
        sleuth_gender=sleuth_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        helper=helper,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.object not in OBJECTS:
        raise StoryError(f"(Unknown object: {params.object})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.suspicion not in {"accuse", "wonder"}:
        raise StoryError(f"(Unknown suspicion mode: {params.suspicion})")

    place = PLACES[params.place]
    obj = OBJECTS[params.object]
    cause = CAUSES[params.cause]
    repair = REPAIRS[params.repair]

    if not cause_can_tear(place, obj, cause):
        raise StoryError(explain_combo_rejection(place, obj, cause))
    if not repair_fits(obj, cause, repair):
        raise StoryError(explain_repair_rejection(obj, cause, repair))

    world = tell(
        place=place,
        obj_cfg=obj,
        cause=cause,
        repair=repair,
        sleuth_name=params.sleuth,
        sleuth_gender=params.sleuth_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        suspicion=params.suspicion,
        helper_type=params.helper,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, object, cause, repair) combos:\n")
        for place, obj, cause, repair in combos:
            print(f"  {place:8} {obj:7} {cause:15} {repair}")
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
            header = f"### {p.sleuth} & {p.partner}: {p.object} at {p.place} ({p.cause}, {p.repair}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
