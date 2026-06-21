#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lass_virtual_road_repair_magic_fable.py
==================================================================

A standalone story world about a young lass in a road-repair village tale.
The world models a practical problem: a road has a dangerous hole or washout,
travelers need a safe path, and the hero is tempted by a quick but weak answer.
A magical helper teaches that a true repair must hold weight, not just look
smooth. The word "virtual" appears in the story as part of a child-facing
illusion: a shimmering virtual road made by magic that only pretends to be safe.

The story shape is fable-like:
- premise: a caring child notices a damaged road
- tension: a quick-looking but weak fix is tempting
- turn: a magical helper proves that appearance is not enough
- resolution: the road is repaired the honest way
- moral image: travelers cross safely because the work is real

Run it
------
python storyworlds/worlds/gpt-5.4/lass_virtual_road_repair_magic_fable.py
python storyworlds/worlds/gpt-5.4/lass_virtual_road_repair_magic_fable.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/lass_virtual_road_repair_magic_fable.py --all --qa
python storyworlds/worlds/gpt-5.4/lass_virtual_road_repair_magic_fable.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    solid: bool = False
    decorative: bool = False
    carries_load: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "fairy", "lass"}
        male = {"boy", "man", "father"}
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
class RoadKind:
    id: str
    label: str
    travelers: str
    burden: str
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
class Damage:
    id: str
    label: str
    cause: str
    risk: str
    severity: int
    needs: set[str] = field(default_factory=set)
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
class QuickFix:
    id: str
    label: str
    style: str
    sense: int
    strength: int
    decorative: bool
    shown_as: str
    lesson: str
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
class Material:
    id: str
    label: str
    strength: int
    work: str
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
class Helper:
    id: str
    label: str
    type: str
    arrival: str
    gift: str
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


def _r_hidden_danger(world: World) -> list[str]:
    out: list[str] = []
    road = world.get("road")
    fix = world.get("fix")
    if road.meters["broken"] < THRESHOLD:
        return out
    if fix.meters["placed"] < THRESHOLD:
        return out
    sig = ("hidden_danger",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if fix.decorative and not fix.carries_load:
        road.meters["looks_safe"] += 1
        road.meters["still_unsafe"] += 1
        for eid in ("hero", "helper"):
            if eid in world.entities:
                world.get(eid).memes["worry"] += 1
        out.append("__looks_safe_but_is_not__")
    return out


def _r_real_repair(world: World) -> list[str]:
    out: list[str] = []
    road = world.get("road")
    repair = world.get("repair")
    if road.meters["broken"] < THRESHOLD:
        return out
    if repair.meters["built"] < THRESHOLD:
        return out
    sig = ("real_repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    road.meters["broken"] = 0.0
    road.meters["safe"] += 1
    road.meters["open"] += 1
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["pride"] += 1
    hero.memes["care"] += 1
    helper.memes["approval"] += 1
    out.append("__road_repaired__")
    return out


CAUSAL_RULES = [
    Rule(name="hidden_danger", tag="physical", apply=_r_hidden_danger),
    Rule(name="real_repair", tag="physical", apply=_r_real_repair),
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


def damage_needs_real_support(damage: Damage, material: Material) -> bool:
    return material.id in damage.needs


def sensible_quick_fixes() -> list[QuickFix]:
    return [f for f in QUICK_FIXES.values() if f.sense >= SENSE_MIN]


def can_truly_repair(damage: Damage, material: Material) -> bool:
    return material.strength >= damage.severity and damage_needs_real_support(damage, material)


def explain_damage_rejection(damage: Damage, material: Material) -> str:
    if material.id not in damage.needs:
        return (
            f"(No story: {material.label} is the wrong kind of road repair for {damage.label}. "
            f"This damage needs a different sort of support under travelers' feet.)"
        )
    if material.strength < damage.severity:
        return (
            f"(No story: {material.label} is too weak for {damage.label}. "
            f"The repair would not safely hold the road.)"
        )
    return "(No story: this repair does not make a safe road.)"


def explain_quick_fix_rejection(fid: str) -> str:
    fx = QUICK_FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_quick_fixes()))
    return (
        f"(Refusing quick fix '{fid}': it scores too low on common sense "
        f"(sense={fx.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_crossing(world: World) -> dict:
    sim = world.copy()
    road = sim.get("road")
    fix = sim.get("fix")
    if fix.meters["placed"] >= THRESHOLD and fix.decorative and not fix.carries_load:
        road.meters["looks_safe"] += 1
        road.meters["still_unsafe"] += 1
    return {
        "looks_safe": road.meters["looks_safe"] >= THRESHOLD,
        "unsafe": road.meters["still_unsafe"] >= THRESHOLD or road.meters["broken"] >= THRESHOLD,
    }


def opening(world: World, hero: Entity, road_kind: RoadKind, damage: Damage) -> None:
    hero.memes["care"] += 1
    world.say(
        f"In a valley where carts and neighbors shared one {road_kind.label}, there lived a careful lass named {hero.id}."
    )
    world.say(
        f"Each morning she watched {road_kind.travelers} pass along it with {road_kind.burden}."
    )
    world.say(
        f"Then {damage.cause}, and a {damage.label} opened in the road. Everyone could see the danger."
    )


def concern(world: World, hero: Entity, road_kind: RoadKind, damage: Damage) -> None:
    world.say(
        f'{hero.id} pressed her hand to her heart. "If no one mends it, {damage.risk}," she said.'
    )
    world.facts["goal"] = f"make the {road_kind.label} safe again"


def choose_quick_fix(world: World, hero: Entity, quick_fix: QuickFix) -> None:
    fix = world.get("fix")
    fix.decorative = quick_fix.decorative
    fix.carries_load = quick_fix.strength >= 2 and not quick_fix.decorative
    fix.meters["placed"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"Being young, she first reached for {quick_fix.label}. With a flick and a whisper, she made {quick_fix.shown_as}."
    )


def magical_warning(world: World, helper: Entity, quick_fix: QuickFix) -> None:
    pred = predict_crossing(world)
    world.facts["predicted_looks_safe"] = pred["looks_safe"]
    world.facts["predicted_unsafe"] = pred["unsafe"]
    helper.memes["care"] += 1
    world.say(helper.attrs["arrival"])
    if pred["looks_safe"] and pred["unsafe"]:
        world.say(
            f'"Child," said {helper.id}, "that is a virtual road only to the eye. {quick_fix.lesson}"'
        )


def test_turn(world: World, hero: Entity, road_kind: RoadKind) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{helper_name(world)} tapped the shining patch with a silver reed. Light shimmered, but the reed sank through, and the {road_kind.label} remained unsafe."
    )
    world.say(
        f"Then {hero.id} understood that smooth-looking magic is not the same as honest strength."
    )


def helper_name(world: World) -> str:
    return world.get("helper").id


def abandon_quick_fix(world: World, hero: Entity) -> None:
    fix = world.get("fix")
    fix.meters["placed"] = 0.0
    fix.decorative = False
    fix.carries_load = False
    hero.memes["humility"] += 1
    world.say(
        f'{hero.id} bowed her head. "Then I must not hide the trouble," she said. "I must mend it for real."'
    )


def true_repair(world: World, hero: Entity, helper: Entity, material: Material, damage: Damage) -> None:
    repair = world.get("repair")
    repair.meters["built"] += 1
    repair.carries_load = True
    repair.solid = True
    hero.meters["work_done"] += 1
    helper.meters["aid_given"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} gave her {helper.attrs['gift']}, and together they {material.work}."
    )
    world.say(
        f"The work was slower than a spell of glitter, but stone sat on stone, and the road stopped trembling at the edge of the {damage.label}."
    )


def ending(world: World, hero: Entity, road_kind: RoadKind) -> None:
    world.say(
        f"By sunset, {road_kind.travelers} crossed again without fear. Wheels rolled true, feet found firm ground, and {hero.id} smiled to hear the sound."
    )
    world.say(
        "From that day on, the village remembered a plain lesson: what only seems safe may fail, but careful work and kindly wisdom can bear the weight of many."
    )


def tell(
    road_kind: RoadKind,
    damage: Damage,
    quick_fix: QuickFix,
    material: Material,
    helper_cfg: Helper,
    hero_name_value: str = "Mira",
    hero_trait: str = "careful",
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name_value, kind="character", type="lass", role="hero", traits=[hero_trait]))
    helper = world.add(
        Entity(
            id=helper_cfg.label,
            kind="character",
            type=helper_cfg.type,
            role="helper",
            attrs={"arrival": helper_cfg.arrival, "gift": helper_cfg.gift},
        )
    )
    world.add(Entity(id="road", type="road", label=road_kind.label, solid=True))
    world.add(Entity(id="fix", type="quick_fix", label=quick_fix.label, decorative=quick_fix.decorative))
    world.add(Entity(id="repair", type="repair", label=material.label))
    world.add(Entity(id="damage", type="damage", label=damage.label))
    world.get("road").meters["broken"] = 1.0
    world.get("hero").memes["care"] = 1.0
    world.get("helper").memes["care"] = 0.0
    world.get("fix").meters["placed"] = 0.0
    world.get("repair").meters["built"] = 0.0
    world.facts["parent_type"] = parent_type

    opening(world, hero, road_kind, damage)
    concern(world, hero, road_kind, damage)

    world.para()
    choose_quick_fix(world, hero, quick_fix)
    propagate(world, narrate=False)
    magical_warning(world, helper, quick_fix)
    test_turn(world, hero, road_kind)
    abandon_quick_fix(world, hero)

    world.para()
    true_repair(world, hero, helper, material, damage)
    ending(world, hero, road_kind)

    world.facts.update(
        hero=hero,
        helper=helper,
        road_kind=road_kind,
        damage_cfg=damage,
        quick_fix=quick_fix,
        material=material,
        helper_cfg=helper_cfg,
        outcome="repaired" if world.get("road").meters["safe"] >= THRESHOLD else "failed",
        moral="appearance_is_not_strength",
        road_safe=world.get("road").meters["safe"] >= THRESHOLD,
        quick_fix_abandoned=world.get("fix").meters["placed"] < THRESHOLD,
    )
    return world


ROADS = {
    "village_lane": RoadKind(
        id="village_lane",
        label="village lane",
        travelers="milk carts, bakers, and children",
        burden="bread, pails, and news",
        tags={"road", "village"},
    ),
    "market_road": RoadKind(
        id="market_road",
        label="market road",
        travelers="donkeys, merchants, and neighbors",
        burden="baskets of apples and bolts of cloth",
        tags={"road", "market"},
    ),
    "bridge_path": RoadKind(
        id="bridge_path",
        label="bridge path",
        travelers="wheelbarrows, shepherds, and old friends",
        burden="kindling, cheese, and wool",
        tags={"road", "bridge"},
    ),
}

DAMAGES = {
    "pothole": Damage(
        id="pothole",
        label="pothole",
        cause="spring rain washed the packed earth away",
        risk="a wheel may crack and a traveler may stumble",
        severity=2,
        needs={"gravel", "stone"},
        tags={"hole", "repair"},
    ),
    "washout": Damage(
        id="washout",
        label="washout",
        cause="a swollen stream bit the roadbank in the night",
        risk="a cart may tip where the edge gives way",
        severity=3,
        needs={"stone"},
        tags={"washout", "repair"},
    ),
    "rut": Damage(
        id="rut",
        label="deep rut",
        cause="heavy wagons pressed one groove lower and lower",
        risk="a small cart may catch and jerk sideways",
        severity=2,
        needs={"gravel"},
        tags={"rut", "repair"},
    ),
}

QUICK_FIXES = {
    "glamour": QuickFix(
        id="glamour",
        label="a glamour of smooth gold dust",
        style="illusion",
        sense=2,
        strength=0,
        decorative=True,
        shown_as="a bright skin over the broken place",
        lesson="A fair shine can trick the eyes and still leave danger underneath.",
        tags={"magic", "illusion"},
    ),
    "virtual_ribbon": QuickFix(
        id="virtual_ribbon",
        label="a virtual ribbon of blue light",
        style="illusion",
        sense=2,
        strength=0,
        decorative=True,
        shown_as="a neat blue path that floated over the gap",
        lesson="A path made only of light cannot carry a wheel or a foot.",
        tags={"magic", "virtual"},
    ),
    "petals": QuickFix(
        id="petals",
        label="a drift of dancing petals",
        style="covering",
        sense=1,
        strength=0,
        decorative=True,
        shown_as="petals swirling so thick that the broken ground seemed hidden",
        lesson="What hides a danger does not heal it.",
        tags={"magic", "flowers"},
    ),
}

MATERIALS = {
    "gravel": Material(
        id="gravel",
        label="gravel",
        strength=2,
        work="carried baskets of gravel and packed them firmly into place",
        tags={"gravel", "repair"},
    ),
    "stone": Material(
        id="stone",
        label="flat stone",
        strength=3,
        work="set flat stones in a careful bed and tamped earth around them",
        tags={"stone", "repair"},
    ),
    "sand": Material(
        id="sand",
        label="loose sand",
        strength=1,
        work="poured sand into the hollow and brushed it level",
        tags={"sand", "repair"},
    ),
}

HELPERS = {
    "road_fairy": Helper(
        id="road_fairy",
        label="Nettle the road fairy",
        type="fairy",
        arrival="At that moment a road fairy stepped from the hedge, her cloak stitched with tiny mile-stones.",
        gift="a moonlit hammer no bigger than a sparrow",
        tags={"magic", "fairy"},
    ),
    "lantern_sprite": Helper(
        id="lantern_sprite",
        label="Pip the lantern sprite",
        type="fairy",
        arrival="Then a lantern sprite rose from a cracked milestone, carrying a glow like warm honey.",
        gift="a little trowel that sang when it struck true",
        tags={"magic", "sprite"},
    ),
    "moss_witch": Helper(
        id="moss_witch",
        label="Brindle the moss witch",
        type="woman",
        arrival="Out of the ditch came a moss witch with green sleeves and bright, laughing eyes.",
        gift="a patient spade cut from ash wood",
        tags={"magic", "witch"},
    ),
}

NAMES = ["Mira", "Tansy", "Elin", "Bryn", "Orla", "Nessa", "Willa", "Mae"]
TRAITS = ["careful", "kind", "steady", "thoughtful", "brave"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for did, damage in DAMAGES.items():
        for mid, material in MATERIALS.items():
            if can_truly_repair(damage, material):
                combos.append((did, mid))
    return combos


@dataclass
class StoryParams:
    road: str
    damage: str
    quick_fix: str
    material: str
    helper: str
    name: str
    trait: str
    parent: str = "mother"
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


KNOWLEDGE = {
    "road": [
        (
            "Why do roads need to be repaired?",
            "Roads need repair because holes and weak edges can make wheels slip and people trip. Fixing them keeps travel safer for everyone."
        )
    ],
    "repair": [
        (
            "Why is a real repair better than just covering a hole?",
            "A real repair fills and supports the broken place so it can hold weight. A cover may hide the problem without making it safe."
        )
    ],
    "magic": [
        (
            "Can magic be used wisely in a story?",
            "Yes. In a fable, magic can help a person see the truth or do good work, but it should not excuse a careless choice."
        )
    ],
    "virtual": [
        (
            "What does virtual mean in this story?",
            "Here, virtual means something that looks real but is only a made image. It can fool the eyes without holding a cart or a foot."
        )
    ],
    "gravel": [
        (
            "What is gravel used for on a road?",
            "Gravel is made of small hard stones. Packed tightly, it helps fill holes and make a road firmer."
        )
    ],
    "stone": [
        (
            "Why can flat stone help mend a bad road edge?",
            "Flat stone is strong and steady. Set carefully, it can support weight where the road was weak."
        )
    ],
    "fairy": [
        (
            "What does a fairy often do in a fable?",
            "A fairy often gives a test, a warning, or a bit of help. The lesson still depends on the human character choosing what is right."
        )
    ],
}

KNOWLEDGE_ORDER = ["road", "repair", "magic", "virtual", "gravel", "stone", "fairy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    road_kind = f["road_kind"]
    damage = f["damage_cfg"]
    quick_fix = f["quick_fix"]
    material = f["material"]
    return [
        f'Write a short fable about a lass who helps repair a {road_kind.label}. Include the word "virtual" and a magical helper.',
        f"Tell a child-friendly road-repair story where {hero.id} first tries {quick_fix.label} over a {damage.label}, then learns to mend it with {material.label}.",
        "Write a gentle moral tale showing that something which only looks safe is not as good as work that is truly strong.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    road_kind = f["road_kind"]
    damage = f["damage_cfg"]
    quick_fix = f["quick_fix"]
    material = f["material"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a young lass named {hero.id} and {helper.id}, a magical helper. They work together to make the {road_kind.label} safe again."
        ),
        (
            "What was wrong with the road?",
            f"The road had a {damage.label} after {damage.cause}. That made travel dangerous because {damage.risk}."
        ),
        (
            f"What did {hero.id} try first?",
            f"She first tried {quick_fix.label}. It made the broken place look neat, but it did not truly support the road."
        ),
        (
            f"Why did the magical helper say the quick fix was not enough?",
            f"{helper.id} showed that the shining patch was only a virtual-looking cover and not a real repair. It fooled the eye, but a wheel or foot could still sink where the road was weak."
        ),
        (
            "How did they really solve the problem?",
            f"They used {material.label} and patient work to mend the damaged place for real. The repair held weight, so travelers could cross safely again."
        ),
        (
            "What is the lesson of the story?",
            "The lesson is that a thing that only seems safe can still hide danger. Honest work and truthful wisdom protect others better than pretty tricks."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["road_kind"].tags) | set(f["damage_cfg"].tags) | set(f["quick_fix"].tags) | set(f["material"].tags) | set(f["helper_cfg"].tags)
    wanted = {"road", "repair", "magic"}
    if "virtual" in tags:
        wanted.add("virtual")
    if "gravel" in tags:
        wanted.add("gravel")
    if "stone" in tags:
        wanted.add("stone")
    if "fairy" in tags or "sprite" in tags or "witch" in tags:
        wanted.add("fairy")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in wanted:
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
        flags = [n for n, on in (("solid", e.solid), ("decorative", e.decorative), ("carries_load", e.carries_load)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:16} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        road="village_lane",
        damage="pothole",
        quick_fix="virtual_ribbon",
        material="gravel",
        helper="road_fairy",
        name="Mira",
        trait="careful",
        parent="mother",
    ),
    StoryParams(
        road="market_road",
        damage="washout",
        quick_fix="glamour",
        material="stone",
        helper="moss_witch",
        name="Tansy",
        trait="steady",
        parent="father",
    ),
    StoryParams(
        road="bridge_path",
        damage="rut",
        quick_fix="virtual_ribbon",
        material="gravel",
        helper="lantern_sprite",
        name="Elin",
        trait="kind",
        parent="mother",
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
real_fix(D, M) :- damage(D), material(M), needs(D, M), severity(D, S), strength(M, T), T >= S.
sensible_fix(F) :- quick_fix(F), sense(F, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
decorative_chosen :- chosen_fix(F), decorative(F).
virtual_appearance :- chosen_fix(F), tag(F, virtual).
weak_cover :- chosen_fix(F), strength_fix(F, 0).
looks_safe :- decorative_chosen.
unsafe_underneath :- damage(D), chosen_material(M), not real_fix(D, M).
unsafe_underneath :- weak_cover.
repaired :- damage(D), chosen_material(M), real_fix(D, M).
outcome(repaired) :- repaired.
outcome(failed) :- not repaired.

#show real_fix/2.
#show sensible_fix/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in ROADS:
        lines.append(asp.fact("road", rid))
    for did, d in DAMAGES.items():
        lines.append(asp.fact("damage", did))
        lines.append(asp.fact("severity", did, d.severity))
        for need in sorted(d.needs):
            lines.append(asp.fact("needs", did, need))
        for tag in sorted(d.tags):
            lines.append(asp.fact("tag", did, tag))
    for fid, f in QUICK_FIXES.items():
        lines.append(asp.fact("quick_fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("strength_fix", fid, f.strength))
        if f.decorative:
            lines.append(asp.fact("decorative", fid))
        for tag in sorted(f.tags):
            lines.append(asp.fact("tag", fid, tag))
    for mid, m in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        lines.append(asp.fact("strength", mid, m.strength))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for tag in sorted(h.tags):
            lines.append(asp.fact("tag", hid, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    program = f"""{asp_facts()}
real_fix(D, M) :- damage(D), material(M), needs(D, M), severity(D, S), strength(M, T), T >= S.
valid(D, M) :- real_fix(D, M).
#show valid/2.
"""
    model = asp.one_model(program)
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(f for (f,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_fix", params.quick_fix),
            asp.fact("chosen_material", params.material),
            asp.fact("damage", params.damage),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "repaired" if can_truly_repair(DAMAGES[params.damage], MATERIALS[params.material]) else "failed"


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

    c_sens = set(asp_sensible())
    p_sens = {f.id for f in sensible_quick_fixes()}
    if c_sens == p_sens:
        print(f"OK: sensible quick fixes match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible quick fixes: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    parser = build_parser()
    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0] if cases else CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a lass, a broken road, a magical lesson about real repair."
    )
    ap.add_argument("--road", choices=ROADS)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--quick-fix", dest="quick_fix", choices=QUICK_FIXES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.damage:
        if not can_truly_repair(DAMAGES[args.damage], MATERIALS[args.material]):
            raise StoryError(explain_damage_rejection(DAMAGES[args.damage], MATERIALS[args.material]))
    if args.quick_fix and QUICK_FIXES[args.quick_fix].sense < SENSE_MIN:
        raise StoryError(explain_quick_fix_rejection(args.quick_fix))

    combos = [
        c
        for c in valid_combos()
        if (args.damage is None or c[0] == args.damage)
        and (args.material is None or c[1] == args.material)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    damage_id, material_id = rng.choice(sorted(combos))
    road = args.road or rng.choice(sorted(ROADS))
    quick_fix = args.quick_fix or rng.choice(sorted(f.id for f in sensible_quick_fixes()))
    helper = args.helper or rng.choice(sorted(HELPERS))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        road=road,
        damage=damage_id,
        quick_fix=quick_fix,
        material=material_id,
        helper=helper,
        name=name,
        trait=trait,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.road not in ROADS:
        raise StoryError(f"(Unknown road '{params.road}'.)")
    if params.damage not in DAMAGES:
        raise StoryError(f"(Unknown damage '{params.damage}'.)")
    if params.quick_fix not in QUICK_FIXES:
        raise StoryError(f"(Unknown quick fix '{params.quick_fix}'.)")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material '{params.material}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if QUICK_FIXES[params.quick_fix].sense < SENSE_MIN:
        raise StoryError(explain_quick_fix_rejection(params.quick_fix))
    if not can_truly_repair(DAMAGES[params.damage], MATERIALS[params.material]):
        raise StoryError(explain_damage_rejection(DAMAGES[params.damage], MATERIALS[params.material]))

    world = tell(
        road_kind=ROADS[params.road],
        damage=DAMAGES[params.damage],
        quick_fix=QUICK_FIXES[params.quick_fix],
        material=MATERIALS[params.material],
        helper_cfg=HELPERS[params.helper],
        hero_name_value=params.name,
        hero_trait=params.trait,
        parent_type=params.parent,
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
        print(asp_program("", "#show real_fix/2.\n#show sensible_fix/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible quick fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (damage, material) combos:\n")
        for damage, material in combos:
            print(f"  {damage:10} {material}")
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
            header = f"### {p.name}: {p.damage} on {p.road} ({p.quick_fix} -> {p.material})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
