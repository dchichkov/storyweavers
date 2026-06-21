#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/heal_inner_monologue_reconciliation_bedtime_story.py
================================================================================

A standalone story world for a soft bedtime tale about a bedtime keepsake, hurt
feelings, and reconciliation. One child handles another child's special bedtime
object too roughly, it gets damaged, and the pair must tell the truth, repair
what they can, and let kind words heal the rest.

The world is built around:
- a concrete bedtime setting
- an accident driven by state, not slot-swapping
- inner-monologue beats grounded in guilt, hurt, and relief
- reconciliation through apology, repair, and a quiet ending image

Run it
------
    python storyworlds/worlds/gpt-5.4/heal_inner_monologue_reconciliation_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/heal_inner_monologue_reconciliation_bedtime_story.py --keepsake paper_moon --mishap tug --repair tape
    python storyworlds/worlds/gpt-5.4/heal_inner_monologue_reconciliation_bedtime_story.py --repair hide_it
    python storyworlds/worlds/gpt-5.4/heal_inner_monologue_reconciliation_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/heal_inner_monologue_reconciliation_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/heal_inner_monologue_reconciliation_bedtime_story.py --verify
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
    owner: str = ""
    material: str = ""
    fragile: bool = False
    comforting: bool = False
    attrs: dict = field(default_factory=dict)
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
class Bedroom:
    id: str
    phrase: str
    hush: str
    ending_image: str
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
class Keepsake:
    id: str
    label: str
    phrase: str
    material: str
    damage_word: str
    whole_description: str
    mended_description: str
    owner_hold: str
    bedtime_use: str
    severity_base: int
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
class Mishap:
    id: str
    action: str
    moment: str
    damage: str
    severity: int
    works_on: set[str] = field(default_factory=set)
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
    sense: int
    power: int
    can_fix: set[str] = field(default_factory=set)
    text: str = ""
    partial_text: str = ""
    qa_text: str = ""
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
class World:
    room: Bedroom
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"owner", "borrower"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return World(
            room=self.room,
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts={},
        )
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


def _r_damage_hurts(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    owner = world.get(world.facts["owner_id"])
    borrower = world.get(world.facts["borrower_id"])
    if keepsake.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_hurts", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["hurt"] += 1
    borrower.memes["guilt"] += 1
    world.get("room").memes["uneasy"] += 1
    return ["__hurt__"]


def _r_apology_softens(world: World) -> list[str]:
    owner = world.get(world.facts["owner_id"])
    borrower = world.get(world.facts["borrower_id"])
    if borrower.memes["apologized"] < THRESHOLD:
        return []
    sig = ("apology_softens", borrower.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["hurt"] = max(0.0, owner.memes["hurt"] - 1.0)
    owner.memes["trust"] += 1
    borrower.memes["hope"] += 1
    return ["__apology__"]


def _r_repair_calms(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    owner = world.get(world.facts["owner_id"])
    borrower = world.get(world.facts["borrower_id"])
    if keepsake.meters["mended"] < THRESHOLD:
        return []
    sig = ("repair_calms", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["calm"] += 1
    borrower.memes["relief"] += 1
    world.get("room").memes["uneasy"] = 0.0
    return ["__repair__"]


CAUSAL_RULES = [
    Rule(name="damage_hurts", tag="emotion", apply=_r_damage_hurts),
    Rule(name="apology_softens", tag="emotion", apply=_r_apology_softens),
    Rule(name="repair_calms", tag="emotion", apply=_r_repair_calms),
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


def mishap_possible(keepsake: Keepsake, mishap: Mishap) -> bool:
    return keepsake.material in mishap.works_on


def repair_possible(keepsake: Keepsake, repair: Repair) -> bool:
    return keepsake.material in repair.can_fix


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for room_id in BEDROOMS:
        for keepsake_id, keepsake in KEEPSAKES.items():
            for mishap_id, mishap in MISHAPS.items():
                if not mishap_possible(keepsake, mishap):
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair.sense < SENSE_MIN:
                        continue
                    if repair_possible(keepsake, repair):
                        combos.append((room_id, keepsake_id, mishap_id, repair_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    keepsake = KEEPSAKES[params.keepsake]
    mishap = MISHAPS[params.mishap]
    repair = REPAIRS[params.repair]
    severity = keepsake.severity_base + mishap.severity
    return "mended" if repair.power >= severity else "comforted"


def explain_mishap(keepsake: Keepsake, mishap: Mishap) -> str:
    return (
        f"(No story: {mishap.action} does not fit {keepsake.phrase}. "
        f"The accident needs to be something that could really damage {keepsake.label}.)"
    )


def explain_repair(keepsake: Keepsake, repair: Repair) -> str:
    if repair.sense < SENSE_MIN:
        return (
            f"(Refusing repair '{repair.id}': it scores too low on common sense "
            f"(sense={repair.sense} < {SENSE_MIN}). A bedtime story should prefer "
            f"honest, gentle repair over hiding the problem.)"
        )
    return (
        f"(No story: {repair.id} does not suit {keepsake.phrase}. "
        f"The fix must match the material of the damaged keepsake.)"
    )


def predict_damage(world: World, mishap: Mishap) -> dict:
    sim = world.copy()
    do_mishap(sim, mishap, narrate=False)
    keepsake = sim.get("keepsake")
    owner = sim.get(sim.facts["owner_id"])
    borrower = sim.get(sim.facts["borrower_id"])
    return {
        "damaged": keepsake.meters["damaged"] >= THRESHOLD,
        "hurt": owner.memes["hurt"],
        "guilt": borrower.memes["guilt"],
    }


def inner_thought_hurt(owner: Entity) -> str:
    if owner.memes["hurt"] >= 1:
        return (
            f'Inside, {owner.id} thought, "I wish {owner.pronoun("subject")} had asked. '
            f'That was special to me."'
        )
    return ""


def inner_thought_guilt(borrower: Entity) -> str:
    if borrower.memes["guilt"] >= 1:
        return (
            f'Inside, {borrower.id} thought, "I did not mean to hurt anything. '
            f'I should tell the truth and help."'
        )
    return ""


def introduce(world: World, owner: Entity, borrower: Entity, keepsake: Keepsake) -> None:
    room = world.room
    world.say(
        f"In {room.phrase}, the day had nearly folded itself away. {room.hush}"
    )
    world.say(
        f"{owner.id} and {borrower.id} were getting ready for bed while the shadows "
        f"grew soft around the rug."
    )
    world.say(
        f"{owner.id} had {keepsake.phrase}, and every night {owner.pronoun('subject')} "
        f"{keepsake.bedtime_use}."
    )
    world.say(keepsake.whole_description)


def tempt(world: World, borrower: Entity, keepsake: Keepsake) -> None:
    borrower.memes["want"] += 1
    world.say(
        f"{borrower.id} edged closer and wanted to hold it too. "
        f'"Just for one tiny look," {borrower.pronoun("subject")} whispered.'
    )


def warn(world: World, owner: Entity, borrower: Entity, mishap: Mishap) -> None:
    pred = predict_damage(world, mishap)
    world.facts["predicted_damage"] = pred["damaged"]
    world.facts["predicted_hurt"] = pred["hurt"]
    world.say(
        f"{owner.id} hugged the keepsake a little closer. "
        f'"Please be gentle," {owner.pronoun("subject")} said. '
        f'"It can {mishap.damage} if someone moves too fast."'
    )


def do_mishap(world: World, mishap: Mishap, narrate: bool = True) -> None:
    keepsake = world.get("keepsake")
    keepsake.meters["damaged"] += 1
    keepsake.meters[mishap.damage] += 1
    keepsake.meters["severity"] = float(
        world.facts["keepsake_cfg"].severity_base + mishap.severity
    )
    propagate(world, narrate=narrate)


def accident(world: World, borrower: Entity, keepsake: Keepsake, mishap: Mishap) -> None:
    borrower.memes["rush"] += 1
    world.say(mishap.moment)
    do_mishap(world, mishap)
    world.say(
        f"There was a tiny sound, and then {keepsake.label} was {keepsake.damage_word}."
    )
    world.say(inner_thought_hurt(world.get(world.facts["owner_id"])))
    world.say(inner_thought_guilt(borrower))


def helper_enters(world: World, helper: Entity) -> None:
    world.say(
        f"{helper.label_word.capitalize()} came to the doorway when the room went quiet."
    )


def helper_guides(world: World, helper: Entity, borrower: Entity, owner: Entity) -> None:
    owner.memes["seen"] += 1
    borrower.memes["seen"] += 1
    world.say(
        f'"Slow breaths," {helper.label_word} said softly. '
        f'"We can tell the truth first, and kind words can help heal a hurt heart."'
    )
    world.say(
        f"{borrower.id} looked at {owner.id}, and {owner.id} looked back without speaking."
    )


def apology(world: World, borrower: Entity, owner: Entity) -> None:
    borrower.memes["apologized"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I am sorry," {borrower.id} said. "I grabbed too fast, and I hurt your special thing."'
    )
    if owner.memes["trust"] >= THRESHOLD:
        world.say(
            f"{owner.id}'s shoulders loosened a little. "
            f'"Thank you for telling me the truth," {owner.pronoun("subject")} said.'
        )


def repair_scene(world: World, helper: Entity, keepsake: Keepsake, repair: Repair) -> None:
    item = world.get("keepsake")
    severity = int(item.meters["severity"])
    if repair.power >= severity:
        item.meters["mended"] += 1
        item.meters["damaged"] = 0.0
        propagate(world, narrate=False)
        world.say(
            f"{helper.label_word.capitalize()} {repair.text.format(keepsake=keepsake.label)}."
        )
        world.say(keepsake.mended_description)
    else:
        world.say(
            f"{helper.label_word.capitalize()} {repair.partial_text.format(keepsake=keepsake.label)}."
        )
        world.say(
            f"It was still a little {keepsake.damage_word}, but now it looked safe enough "
            f"to keep close at bedtime."
        )


def reconcile(world: World, owner: Entity, borrower: Entity, keepsake: Keepsake) -> None:
    owner.memes["forgiveness"] += 1
    borrower.memes["relief"] += 1
    owner.memes["calm"] += 1
    world.get("room").memes["uneasy"] = 0.0
    world.say(
        f'"Would you like to {keepsake.owner_hold} with me while we look at it?" '
        f"{owner.id} asked."
    )
    world.say(
        f"{borrower.id} nodded. The two of them sat shoulder to shoulder, much quieter now."
    )
    world.say(
        f"That was the moment the room stopped feeling tight and started feeling gentle again."
    )


def ending(world: World, owner: Entity, borrower: Entity, keepsake: Keepsake) -> None:
    room = world.room
    if world.facts["outcome"] == "mended":
        world.say(
            f"Soon both children were tucked in, and {keepsake.label} rested nearby as {room.ending_image}."
        )
    else:
        world.say(
            f"Soon both children were tucked in, and even with its small mark, {keepsake.label} rested nearby as {room.ending_image}."
        )
    world.say(
        f"{borrower.id} whispered good night to {owner.id}, and {owner.id} whispered it back."
    )
    world.say(
        "The hurt had not vanished like magic, but it had been met with truth, care, and love, and that helped it heal."
    )


def tell(
    room: Bedroom,
    keepsake: Keepsake,
    mishap: Mishap,
    repair: Repair,
    owner_name: str,
    owner_gender: str,
    borrower_name: str,
    borrower_gender: str,
    helper_type: str,
) -> World:
    world = World(room=room)
    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=owner_gender,
            role="owner",
            label=owner_name,
            attrs={},
        )
    )
    borrower = world.add(
        Entity(
            id=borrower_name,
            kind="character",
            type=borrower_gender,
            role="borrower",
            label=borrower_name,
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
            attrs={},
        )
    )
    room_ent = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=room.phrase,
            attrs={},
        )
    )
    room_ent.memes["uneasy"] = 0.0
    world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            label=keepsake.label,
            owner=owner.id,
            material=keepsake.material,
            comforting=True,
            fragile=True,
            attrs={},
        )
    )

    owner.memes["hurt"] = 0.0
    owner.memes["trust"] = 0.0
    owner.memes["calm"] = 0.0
    borrower.memes["guilt"] = 0.0
    borrower.memes["hope"] = 0.0
    borrower.memes["relief"] = 0.0

    world.facts["owner_id"] = owner.id
    world.facts["borrower_id"] = borrower.id
    world.facts["room_cfg"] = room
    world.facts["keepsake_cfg"] = keepsake
    world.facts["mishap_cfg"] = mishap
    world.facts["repair_cfg"] = repair

    introduce(world, owner, borrower, keepsake)
    world.para()
    tempt(world, borrower, keepsake)
    warn(world, owner, borrower, mishap)
    accident(world, borrower, keepsake, mishap)
    world.para()
    helper_enters(world, helper)
    helper_guides(world, helper, borrower, owner)
    apology(world, borrower, owner)
    repair_scene(world, helper, keepsake, repair)
    reconcile(world, owner, borrower, keepsake)
    world.para()
    world.facts["outcome"] = "mended" if world.get("keepsake").meters["mended"] >= THRESHOLD else "comforted"
    ending(world, owner, borrower, keepsake)

    world.facts.update(
        owner=owner,
        borrower=borrower,
        helper=helper,
        keepsake=world.get("keepsake"),
        severity=int(world.get("keepsake").meters["severity"]),
        apologized=borrower.memes["apologized"] >= THRESHOLD,
        mended=world.get("keepsake").meters["mended"] >= THRESHOLD,
    )
    return world


BEDROOMS = {
    "shared_room": Bedroom(
        id="shared_room",
        phrase="their shared room under the sloping roof",
        hush="A night-lamp made a small golden puddle on the wall, and the blankets smelled clean and warm.",
        ending_image="the little lamp painted a sleepy moon-shape across the ceiling",
        tags={"bedroom", "lamp"},
    ),
    "nursery_corner": Bedroom(
        id="nursery_corner",
        phrase="the nursery corner beside the window",
        hush="The curtains swayed a little, and the stars outside looked as if they were blinking very slowly.",
        ending_image="the curtains breathed in and out with the kind wind",
        tags={"bedroom", "window"},
    ),
    "grandma_room": Bedroom(
        id="grandma_room",
        phrase="the guest room at grandma's house",
        hush="The quilt was tucked smooth, and the whole room smelled faintly of soap and lavender.",
        ending_image="the lavender smell and the hush of the house wrapped around them",
        tags={"bedroom", "grandma"},
    ),
}

KEEPSAKES = {
    "paper_moon": Keepsake(
        id="paper_moon",
        label="the paper moon mobile",
        phrase="a paper moon mobile with silver stars",
        material="paper",
        damage_word="torn",
        whole_description="It hung over the bed and turned slowly whenever the air moved, as if it were dreaming before the children did.",
        mended_description="The moon still turned when the air moved, and the silver stars gave one soft blink as if they were grateful to stay together.",
        owner_hold="watch the moon turn",
        bedtime_use="liked to watch it spin before sleep",
        severity_base=1,
        tags={"paper", "bedtime", "moon"},
    ),
    "patchwork_quilt": Keepsake(
        id="patchwork_quilt",
        label="the patchwork quilt",
        phrase="a patchwork quilt with little stitched boats",
        material="cloth",
        damage_word="snagged",
        whole_description="It lay at the foot of the bed, bright with squares of blue, red, and cream, and it always made the bed feel especially safe.",
        mended_description="The quilt looked smooth again, and the stitched boats seemed ready to sail quietly through another night's sleep.",
        owner_hold="hold the quilt edge",
        bedtime_use="liked to pull it up to the chin while listening to a last story",
        severity_base=1,
        tags={"cloth", "bedtime", "quilt"},
    ),
    "star_box": Keepsake(
        id="star_box",
        label="the wooden star box",
        phrase="a small wooden star box that played a bedtime tune",
        material="wood",
        damage_word="cracked",
        whole_description="When its lid was opened, a tiny tune came out so softly that everyone in the room wanted to lower their voices.",
        mended_description="The star box still held its tune, and now it sat carefully on the shelf where small hands could admire it without jostling it.",
        owner_hold="listen to the tune",
        bedtime_use="liked to open it once before sleep and hear the little melody",
        severity_base=2,
        tags={"wood", "music", "bedtime"},
    ),
}

MISHAPS = {
    "tug": Mishap(
        id="tug",
        action="a quick tug",
        moment="But excitement jumped ahead of careful hands. One quick tug came before anyone could stop it.",
        damage="tear",
        severity=1,
        works_on={"paper", "cloth"},
        tags={"grab", "rough"},
    ),
    "drop": Mishap(
        id="drop",
        action="a sleepy drop",
        moment="Sleepy fingers slipped. The keepsake tipped, wobbled once, and fell before anyone could catch it.",
        damage="crack",
        severity=2,
        works_on={"wood"},
        tags={"drop", "rough"},
    ),
    "twist": Mishap(
        id="twist",
        action="a twist in the wrong direction",
        moment="A curious twist turned just a little too far, and the whole thing pulled against itself.",
        damage="snag",
        severity=1,
        works_on={"paper", "cloth"},
        tags={"grab", "twist"},
    ),
}

REPAIRS = {
    "tape": Repair(
        id="tape",
        sense=3,
        power=2,
        can_fix={"paper"},
        text="smoothed the torn edge and used a neat strip of clear tape to join {keepsake} again",
        partial_text="pressed the paper flat and added a little tape to steady {keepsake}",
        qa_text="used clear tape to mend it",
        tags={"tape", "paper"},
    ),
    "stitch": Repair(
        id="stitch",
        sense=3,
        power=2,
        can_fix={"cloth"},
        text="threaded a needle and made small patient stitches to mend {keepsake}",
        partial_text="made a few careful stitches so {keepsake} would not pull any farther",
        qa_text="sewed it with small stitches",
        tags={"stitch", "cloth"},
    ),
    "wood_glue": Repair(
        id="wood_glue",
        sense=3,
        power=4,
        can_fix={"wood"},
        text="set the pieces straight, added wood glue, and held {keepsake} gently until it settled",
        partial_text="added glue and set {keepsake} safely aside to rest",
        qa_text="used wood glue and held the pieces in place",
        tags={"glue", "wood"},
    ),
    "ribbon_tie": Repair(
        id="ribbon_tie",
        sense=2,
        power=1,
        can_fix={"paper", "cloth"},
        text="looped a soft ribbon around the weak spot to hold {keepsake} together for now",
        partial_text="tied a soft ribbon around the weak place on {keepsake}",
        qa_text="wrapped it with a ribbon",
        tags={"ribbon", "gentle"},
    ),
    "hide_it": Repair(
        id="hide_it",
        sense=1,
        power=0,
        can_fix={"paper", "cloth", "wood"},
        text="tucked {keepsake} under a pillow and pretended nothing had happened",
        partial_text="hid {keepsake} under the pillow",
        qa_text="hid it",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    room: str
    keepsake: str
    mishap: str
    repair: str
    owner_name: str
    owner_gender: str
    borrower_name: str
    borrower_gender: str
    helper: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    borrower = f["borrower"]
    keepsake = f["keepsake_cfg"]
    room = f["room_cfg"]
    outcome = f["outcome"]
    last = "and ends with the keepsake mended" if outcome == "mended" else "and ends with the children reconciled even though the keepsake still shows a tiny mark"
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the word "heal" and features inner monologue and reconciliation.',
        f"Tell a gentle nighttime story in {room.phrase} where {borrower.id} accidentally damages {owner.id}'s {keepsake.label}, feels sorry inside, and learns to tell the truth.",
        f"Write a soft story about hurt feelings that {last}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    borrower = f["borrower"]
    helper = f["helper"]
    keepsake_cfg = f["keepsake_cfg"]
    mishap = f["mishap_cfg"]
    repair = f["repair_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id} and {borrower.id} at bedtime, with {helper.label_word} helping them when feelings were hurt. The story stays close to the room and to the small problem between them.",
        ),
        (
            f"Why was {keepsake_cfg.label} important to {owner.id}?",
            f"It was part of {owner.id}'s bedtime comfort, and {owner.pronoun('subject')} used it every night before sleep. That is why the damage felt big even though the object itself was small.",
        ),
        (
            f"What happened to {keepsake_cfg.label}?",
            f"{borrower.id} moved too fast, and {mishap.action} left it {keepsake_cfg.damage_word}. The accident mattered because the keepsake was special and fragile.",
        ),
        (
            f"What was {borrower.id} thinking inside after the accident?",
            f"{borrower.id} felt guilty and thought about telling the truth. The inner thought mattered because it led to the apology instead of hiding the mistake.",
        ),
        (
            f"How did {helper.label_word} help heal the problem?",
            f"{helper.label_word.capitalize()} slowed the room down and told the children to start with the truth. That made space for an apology, and then for a gentle repair.",
        ),
    ]
    if outcome == "mended":
        qa.append(
            (
                "Did they fix the keepsake completely?",
                f"Mostly yes. {helper.label_word.capitalize()} {repair.qa_text}, and the keepsake could stay near the bed again. The careful repair helped both the object and the feelings settle.",
            )
        )
    else:
        qa.append(
            (
                "Was everything made perfect again?",
                f"No, not perfectly. The keepsake still had a small mark, but the children told the truth, stayed together, and felt calmer by the end. Their relationship began to heal even before the object did.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended quietly, with both children tucked in and the room feeling gentle again. The ending image proves that the quarrel changed into closeness.",
        )
    )
    return qa


KNOWLEDGE = {
    "paper": [
        (
            "Why can paper tear easily?",
            "Paper is thin, so a quick pull can split it. That is why paper things need slow, careful hands."
        )
    ],
    "cloth": [
        (
            "What does it mean when cloth is snagged?",
            "A snag is when threads get pulled out of place. Small stitches can often help hold the cloth together again."
        )
    ],
    "wood": [
        (
            "Why can wood crack when it falls?",
            "Wood is hard, but a hard bump can split it. If the crack is small, a grown-up may be able to glue it carefully."
        )
    ],
    "tape": [
        (
            "What does clear tape do?",
            "Clear tape can hold light paper pieces together. It works best when the torn edges are lined up neatly."
        )
    ],
    "stitch": [
        (
            "What are stitches for?",
            "Stitches are little loops of thread that hold cloth together. They can help mend a rip or a snag."
        )
    ],
    "glue": [
        (
            "What does glue do?",
            "Glue helps pieces stick together again. Some glues need a grown-up because the pieces must be held still while they dry."
        )
    ],
    "bedtime": [
        (
            "Why do bedtime routines help children?",
            "Bedtime routines help children know what comes next. That makes the body and mind feel calmer and readier for sleep."
        )
    ],
    "apology": [
        (
            "Why is saying sorry important?",
            "Saying sorry shows that you know you caused hurt. Honest words can help another person feel seen and can start to heal the problem."
        )
    ],
}
KNOWLEDGE_ORDER = ["paper", "cloth", "wood", "tape", "stitch", "glue", "bedtime", "apology"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["keepsake_cfg"].tags) | set(f["repair_cfg"].tags) | {"bedtime", "apology"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.material:
            bits.append(f"material={ent.material}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="shared_room",
        keepsake="paper_moon",
        mishap="tug",
        repair="tape",
        owner_name="Lily",
        owner_gender="girl",
        borrower_name="Tom",
        borrower_gender="boy",
        helper="mother",
    ),
    StoryParams(
        room="nursery_corner",
        keepsake="patchwork_quilt",
        mishap="twist",
        repair="stitch",
        owner_name="Mia",
        owner_gender="girl",
        borrower_name="Ben",
        borrower_gender="boy",
        helper="father",
    ),
    StoryParams(
        room="grandma_room",
        keepsake="star_box",
        mishap="drop",
        repair="wood_glue",
        owner_name="Zoe",
        owner_gender="girl",
        borrower_name="Max",
        borrower_gender="boy",
        helper="grandmother",
    ),
    StoryParams(
        room="shared_room",
        keepsake="patchwork_quilt",
        mishap="tug",
        repair="ribbon_tie",
        owner_name="Sam",
        owner_gender="boy",
        borrower_name="Nora",
        borrower_gender="girl",
        helper="father",
    ),
]


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(Room, K, M, R) :- bedroom(Room), keepsake(K), mishap(M), repair(R),
                        works_on(M, Mat), material(K, Mat),
                        can_fix(R, Mat), sense(R, S), sense_min(Min), S >= Min.

% --- outcome model ---------------------------------------------------------
severity(V) :- chosen_keepsake(K), chosen_mishap(M), base_severity(K, B),
               mishap_severity(M, S), V = B + S.
mended :- chosen_repair(R), power(R, P), severity(V), P >= V.
outcome(mended) :- mended.
outcome(comforted) :- not mended.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id in BEDROOMS:
        lines.append(asp.fact("bedroom", room_id))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("material", keepsake_id, keepsake.material))
        lines.append(asp.fact("base_severity", keepsake_id, keepsake.severity_base))
    for mishap_id, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mishap_id))
        lines.append(asp.fact("mishap_severity", mishap_id, mishap.severity))
        for mat in sorted(mishap.works_on):
            lines.append(asp.fact("works_on", mishap_id, mat))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("power", repair_id, repair.power))
        for mat in sorted(repair.can_fix):
            lines.append(asp.fact("can_fix", repair_id, mat))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_keepsake", params.keepsake),
            asp.fact("chosen_mishap", params.mishap),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime keepsake, hurt feelings, and reconciliation."
    )
    ap.add_argument("--room", choices=BEDROOMS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.keepsake and args.mishap:
        keepsake = KEEPSAKES[args.keepsake]
        mishap = MISHAPS[args.mishap]
        if not mishap_possible(keepsake, mishap):
            raise StoryError(explain_mishap(keepsake, mishap))
    if args.keepsake and args.repair:
        keepsake = KEEPSAKES[args.keepsake]
        repair = REPAIRS[args.repair]
        if not repair_possible(keepsake, repair) or repair.sense < SENSE_MIN:
            raise StoryError(explain_repair(keepsake, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.mishap is None or combo[2] == args.mishap)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, keepsake_id, mishap_id, repair_id = rng.choice(sorted(combos))
    owner_name, owner_gender = _pick_child(rng)
    borrower_name, borrower_gender = _pick_child(rng, avoid=owner_name)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(
        room=room_id,
        keepsake=keepsake_id,
        mishap=mishap_id,
        repair=repair_id,
        owner_name=owner_name,
        owner_gender=owner_gender,
        borrower_name=borrower_name,
        borrower_gender=borrower_gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in BEDROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.mishap not in MISHAPS:
        raise StoryError(f"(Unknown mishap: {params.mishap})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    keepsake = KEEPSAKES[params.keepsake]
    mishap = MISHAPS[params.mishap]
    repair = REPAIRS[params.repair]

    if not mishap_possible(keepsake, mishap):
        raise StoryError(explain_mishap(keepsake, mishap))
    if not repair_possible(keepsake, repair) or repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(keepsake, repair))

    world = tell(
        room=BEDROOMS[params.room],
        keepsake=keepsake,
        mishap=mishap,
        repair=repair,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        borrower_name=params.borrower_name,
        borrower_gender=params.borrower_gender,
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure on seed {s}")
            break

    bad = 0
    for params in cases:
        try:
            if asp_outcome(params) != outcome_of(params):
                bad += 1
        except Exception as exc:  # pragma: no cover
            rc = 1
            print(f"Outcome verification crashed for {params}: {exc}")
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, keepsake, mishap, repair) combos:\n")
        for room_id, keepsake_id, mishap_id, repair_id in combos:
            print(f"  {room_id:14} {keepsake_id:15} {mishap_id:8} {repair_id}")
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
                f"### {p.owner_name} & {p.borrower_name}: {p.keepsake} / "
                f"{p.mishap} / {p.repair} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
