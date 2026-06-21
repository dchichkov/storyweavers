#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scooter_machine_heap_twist_myth.py
=============================================================

A standalone storyworld in a tiny mythic domain: a child rides a scooter to a
sacred scrap heap to find the lost heart-piece of a village machine.

The shape is simple and state-driven:

- A hilltop machine that blesses the village has gone still.
- Two children go by scooter to the old bronze heap to look for a fitting part.
- A fearful sign at the heap seems like a monster or curse.
- Twist: the "heap spirit" is really the machine calling for its own missing part.
- The children repair the machine, and the ending image proves the world changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/scooter_machine_heap_twist_myth.py
    python storyworlds/worlds/gpt-5.4/scooter_machine_heap_twist_myth.py --machine dawn_wheel --part bell_gear
    python storyworlds/worlds/gpt-5.4/scooter_machine_heap_twist_myth.py --part rust_nail
    python storyworlds/worlds/gpt-5.4/scooter_machine_heap_twist_myth.py --all --qa
    python storyworlds/worlds/gpt-5.4/scooter_machine_heap_twist_myth.py --verify
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
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
class Machine:
    id: str
    label: str
    title: str
    gift: str
    stillness: str
    wake: str
    fit_tag: str
    sound: str
    light: str
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
class HeapPart:
    id: str
    label: str
    phrase: str
    fit_tag: str
    shine: str
    use_line: str
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
class Omen:
    id: str
    appear: str
    fear_name: str
    truth: str
    reveal: str
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
class Companion:
    id: str
    kind_name: str
    title: str
    help_line: str
    closing_line: str
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


def _r_still_machine(world: World) -> list[str]:
    out: list[str] = []
    machine = world.get("machine")
    village = world.get("village")
    if machine.meters["broken"] >= THRESHOLD:
        sig = ("still", machine.id)
        if sig not in world.fired:
            world.fired.add(sig)
            village.meters["need"] += 1
            out.append("__still__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    machine = world.get("machine")
    part = world.get("part")
    village = world.get("village")
    if machine.attrs.get("fit_tag") != part.attrs.get("fit_tag"):
        return out
    if part.meters["installed"] < THRESHOLD:
        return out
    sig = ("repair", machine.id, part.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    machine.meters["broken"] = 0.0
    machine.meters["working"] += 1
    village.meters["need"] = 0.0
    village.meters["blessing"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["relief"] += 1
            ent.memes["wonder"] += 1
            ent.memes["fear"] = 0.0
    out.append("__repaired__")
    return out


def _r_hum(world: World) -> list[str]:
    out: list[str] = []
    machine = world.get("machine")
    part = world.get("part")
    if machine.meters["broken"] < THRESHOLD:
        return out
    if part.attrs.get("fit_tag") != machine.attrs.get("fit_tag"):
        return out
    if part.meters["near_machine"] < THRESHOLD:
        return out
    sig = ("hum", machine.id, part.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    machine.meters["humming"] += 1
    out.append("__hum__")
    return out


CAUSAL_RULES = [
    Rule(name="still_machine", tag="physical", apply=_r_still_machine),
    Rule(name="repair", tag="physical", apply=_r_repair),
    Rule(name="hum", tag="physical", apply=_r_hum),
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


def compatible(machine: Machine, part: HeapPart) -> bool:
    return machine.fit_tag == part.fit_tag


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for machine_id, machine in MACHINES.items():
        for part_id, part in PARTS.items():
            if compatible(machine, part):
                for omen_id in OMENS:
                    combos.append((machine_id, part_id, omen_id))
    return combos


def explain_rejection(machine: Machine, part: HeapPart) -> str:
    return (
        f"(No story: {part.phrase} does not fit {machine.title}. "
        f"The machine needs a {machine.fit_tag.replace('_', ' ')}, "
        f"so the village would have no honest repair.)"
    )


def predict_hum(world: World, machine_id: str, part_id: str) -> bool:
    sim = world.copy()
    sim.get(part_id).meters["near_machine"] += 1
    propagate(sim, narrate=False)
    return sim.get(machine_id).meters["humming"] >= THRESHOLD


def introduce(world: World, hero: Entity, companion: Companion, elder: Entity, machine: Machine) -> None:
    world.say(
        f"In the old days, the people of the valley said the gods had left "
        f"{machine.title} on the hill above the fig trees."
    )
    world.say(
        f"When it turned, {machine.gift}; when it slept, {machine.stillness}."
    )
    world.say(
        f"In that valley lived {hero.id}, a child quick on a red scooter, and "
        f"{companion.title}, {hero.pronoun('possessive')} {companion.kind_name}, who liked to run beside the wheels."
    )
    world.say(
        f"{elder.id}, the keeper of the hill, taught {hero.id} to bow to old bronze "
        f"and listen before touching sacred things."
    )


def discover_break(world: World, hero: Entity, machine: Machine, elder: Entity) -> None:
    hero.memes["care"] += 1
    world.para()
    world.say(
        f"One dawn, {hero.id} rode the scooter up the stone path and found {machine.title} standing still."
    )
    world.say(
        f'Not one {machine.sound} came from it. "{machine.stillness}," said {elder.id}, laying a hand on the cold frame.'
    )
    world.say(
        f'"Its heart-piece is gone. Without it, the hill cannot wake the valley."'
    )


def send_quest(world: World, hero: Entity, elder: Entity, machine: Machine) -> None:
    world.say(
        f"{elder.id} pointed toward the old bronze heap behind the shrine wall, "
        f"where broken cups, bent bells, and forgotten wheels had lain for years."
    )
    world.say(
        f'"Among that heap sleeps a piece that belongs to {machine.label}," '
        f"{elder.pronoun()} said. "
        f'"Go gently. Bring back only what truly answers."'
    )


def ride_to_heap(world: World, hero: Entity, companion_cfg: Companion) -> None:
    hero.memes["bravery"] += 1
    world.para()
    world.say(
        f"So {hero.id} pushed off on the scooter, and the little wheels sang over the dust."
    )
    world.say(companion_cfg.help_line)
    world.say(
        "Behind the shrine wall waited the heap, green with age and bright in a hundred small places where the sun still found metal."
    )


def omen_appears(world: World, hero: Entity, omen: Omen) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"Then {omen.appear}."
    )
    world.say(
        f"{hero.id} gripped the scooter handles. In the valley tales, children gave that shape a name: {omen.fear_name}."
    )


def search_heap(world: World, hero: Entity, part: HeapPart) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"But under a bent plate and a drift of old chains, {hero.id} saw {part.phrase}, {part.shine}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} lifted it carefully. It was heavier than it looked, and it felt warm, as if it had been waiting."
    )


def twist_realization(world: World, hero: Entity, machine: Machine, part: HeapPart, omen: Omen) -> None:
    world.para()
    world.say(
        f"{hero.id} carried the piece back to the hill, one hand on the scooter and one arm around the bronze find."
    )
    world.get("part").meters["near_machine"] += 1
    if predict_hum(world, "machine", "part"):
        world.get("part").meters["near_machine"] = 0.0
        world.say(
            f"Before the piece even touched the frame, {machine.title} gave a low hum."
        )
        world.say(
            f"At once {hero.id} understood the twist in the old tale: {omen.truth}"
        )
    else:
        world.get("part").meters["near_machine"] = 0.0
        world.say(
            f"{hero.id} held the piece toward the frame and felt the hill grow suddenly quiet, as if waiting for a true answer."
        )


def repair_machine(world: World, hero: Entity, elder: Entity, machine: Machine, part: HeapPart, omen: Omen, companion_cfg: Companion) -> None:
    world.say(
        f'"This is the one," {hero.id} whispered. {part.use_line}'
    )
    world.get("part").meters["installed"] += 1
    propagate(world, narrate=False)
    world.para()
    if world.get("machine").meters["working"] >= THRESHOLD:
        world.say(
            f"{elder.id} set the piece in place, and {machine.title} woke."
        )
        world.say(
            f"{machine.wake}. {machine.light}"
        )
        world.say(
            omen.reveal
        )
        world.say(
            f"{companion_cfg.closing_line} {hero.id} laughed and rested a foot on the scooter as the whole valley listened."
        )
    else:
        raise StoryError("The chosen part did not repair the machine.")


def ending(world: World, hero: Entity, machine: Machine) -> None:
    world.say(
        f"After that morning, {hero.id} never called the old heap cursed again."
    )
    world.say(
        f"People said the hill had taught a child the oldest lesson of all: "
        f"what looks like a heap of scraps may be a sleeping answer, waiting to be heard."
    )


MACHINES = {
    "dawn_wheel": Machine(
        id="dawn_wheel",
        label="the Dawn Wheel",
        title="the Dawn Wheel",
        gift="warm gold light spilled across the roofs and woke the figs before the birds",
        stillness="the valley kept its blue sleep too long, and even the roosters sounded unsure",
        wake="Its rings began to turn and the hanging bells poured bright notes down the slope",
        fit_tag="bell_gear",
        sound="bell-note",
        light="The first true sunbeam broke over the orchard as if the machine had pulled it by a thread",
        tags={"dawn", "machine", "bell"},
    ),
    "rain_harp": Machine(
        id="rain_harp",
        label="the Rain Harp",
        title="the Rain Harp",
        gift="thin silver water fell on the thirsty terraces and filled the jars by noon",
        stillness="the cisterns yawned empty, and the herbs along the wall curled at their tips",
        wake="Its tall strings trembled and a cool song ran out over the fields",
        fit_tag="cup_leaf",
        sound="harp-string",
        light="A soft rain began to patter on the leaves, and the dust darkened into earth again",
        tags={"rain", "machine", "water"},
    ),
    "wind_lantern": Machine(
        id="wind_lantern",
        label="the Wind Lantern",
        title="the Wind Lantern",
        gift="a clean hill wind came down to turn mills, cool bread, and carry swallows higher",
        stillness="the sails below hung flat, and the noon air sat on the village like a blanket",
        wake="Its bronze vanes spun and its tall glass heart flashed blue-white",
        fit_tag="copper_vane",
        sound="whir",
        light="The fig leaves turned their pale undersides to the breeze, and every prayer ribbon woke at once",
        tags={"wind", "machine", "air"},
    ),
}

PARTS = {
    "bell_gear": HeapPart(
        id="bell_gear",
        label="bell gear",
        phrase="a round bell gear with three neat teeth left",
        fit_tag="bell_gear",
        shine="still holding a rim of dawn-colored shine",
        use_line="The teeth slid against the sleeping cogs as if they had known each other forever",
        tags={"gear", "bronze", "heap"},
    ),
    "cup_leaf": HeapPart(
        id="cup_leaf",
        label="cup leaf",
        phrase="a bronze cup leaf shaped like a little open hand",
        fit_tag="cup_leaf",
        shine="beaded with cool drops though the morning was dry",
        use_line="It nested into the upper socket like rain finding a leaf",
        tags={"cup", "bronze", "heap"},
    ),
    "copper_vane": HeapPart(
        id="copper_vane",
        label="copper vane",
        phrase="a slim copper vane curved like a swallow's wing",
        fit_tag="copper_vane",
        shine="edged in green and sudden fire",
        use_line="It caught the first wandering breeze and answered with a brave little spin",
        tags={"vane", "bronze", "heap"},
    ),
    "rust_nail": HeapPart(
        id="rust_nail",
        label="rust nail",
        phrase="a crooked rust nail",
        fit_tag="nail",
        shine="hardly shining at all",
        use_line="It scraped uselessly against the sacred frame",
        tags={"nail", "heap"},
    ),
    "cracked_mask": HeapPart(
        id="cracked_mask",
        label="cracked mask",
        phrase="a cracked festival mask",
        fit_tag="mask",
        shine="with one bright eye still painted on",
        use_line="It belonged to a song, not to a machine",
        tags={"mask", "heap"},
    ),
}

OMENS = {
    "serpent_shadow": Omen(
        id="serpent_shadow",
        appear="a long shape slid over the heap and coiled among the broken bowls",
        fear_name="the Heap Serpent",
        truth="the feared serpent was only the machine's own shadow, cast crooked through the shrine gate to guide the seeker",
        reveal="In the fuller light, the serpent melted into shadow-lines on the stones, and the children saw that no beast had ever slept there.",
        tags={"shadow", "twist"},
    ),
    "speaking_heap": Omen(
        id="speaking_heap",
        appear="a whisper rose from the heap, metal on metal, like old lips learning a prayer",
        fear_name="the Talking Heap",
        truth="the whisper had not come from a spirit in the scraps at all, but from the broken machine calling softly for its lost heart",
        reveal="When the machine turned again, the heap fell silent, and everyone understood that its murmuring had been an answer-seeking song.",
        tags={"voice", "twist"},
    ),
    "bronze_eyes": Omen(
        id="bronze_eyes",
        appear="two pale gleams opened inside the heap and watched from under a bent shield",
        fear_name="the Bronze Eyes",
        truth="the shining eyes were only moon-shell beads fixed in an old shrine toy, lit by the waking machine's first stir",
        reveal="The terrible eyes proved to be little shell beads in a toy ram, and the hill seemed to smile at its own joke.",
        tags={"eyes", "twist"},
    ),
}

COMPANIONS = {
    "sparrow": Companion(
        id="sparrow",
        kind_name="sparrow",
        title="a temple sparrow",
        help_line="A temple sparrow hopped after the scooter, scolding every stone as if the quest were its own.",
        closing_line="The sparrow flew straight through the new light and came back chirping as if it had borrowed a gold feather.",
        tags={"bird"},
    ),
    "goat": Companion(
        id="goat",
        kind_name="goat",
        title="a sure-footed goat kid",
        help_line="A goat kid trotted along, nosing at the heap and stamping whenever the bronze clinked too sharply.",
        closing_line="The goat kid kicked once in the new breeze and bounded in a wild little circle.",
        tags={"goat"},
    ),
    "dog": Companion(
        id="dog",
        kind_name="dog",
        title="a small shrine dog",
        help_line="A small shrine dog padded beside the scooter and barked at the heap as if warning away bad luck.",
        closing_line="The little dog barked at the ringing hill, then wagged so hard its whole body seemed made of joy.",
        tags={"dog"},
    ),
}

ELDERS = {
    "priestess": {"name": "Ione", "type": "woman"},
    "keeper": {"name": "Theron", "type": "man"},
}

GIRL_NAMES = ["Leda", "Mira", "Nora", "Tala", "Eris", "Dara"]
BOY_NAMES = ["Orin", "Leo", "Panos", "Timo", "Ari", "Soren"]
TRAITS = ["careful", "steady", "bright", "brave", "gentle"]


@dataclass
class StoryParams:
    machine: str
    part: str
    omen: str
    companion: str
    child_name: str
    child_gender: str
    elder_role: str
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


def tell(
    machine_cfg: Machine,
    part_cfg: HeapPart,
    omen_cfg: Omen,
    companion_cfg: Companion,
    child_name: str,
    child_gender: str,
    elder_role: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="hero",
            traits=[trait],
            attrs={},
        )
    )
    elder_info = ELDERS[elder_role]
    elder = world.add(
        Entity(
            id=elder_info["name"],
            kind="character",
            type=elder_info["type"],
            role="elder",
            label="the elder",
            attrs={},
        )
    )
    village = world.add(
        Entity(
            id="village",
            type="place",
            label="the valley village",
            attrs={},
        )
    )
    machine = world.add(
        Entity(
            id="machine",
            type="machine",
            label=machine_cfg.label,
            attrs={"fit_tag": machine_cfg.fit_tag, "machine_id": machine_cfg.id},
        )
    )
    part = world.add(
        Entity(
            id="part",
            type="part",
            label=part_cfg.label,
            attrs={"fit_tag": part_cfg.fit_tag, "part_id": part_cfg.id},
        )
    )
    scooter = world.add(
        Entity(
            id="scooter",
            type="scooter",
            label="scooter",
            attrs={},
        )
    )

    machine.meters["broken"] = 1.0
    machine.meters["working"] = 0.0
    machine.meters["humming"] = 0.0
    part.meters["near_machine"] = 0.0
    part.meters["installed"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["relief"] = 0.0
    village.meters["need"] = 0.0
    village.meters["blessing"] = 0.0
    propagate(world, narrate=False)

    introduce(world, hero, companion_cfg, elder, machine_cfg)
    discover_break(world, hero, machine_cfg, elder)
    send_quest(world, hero, elder, machine_cfg)
    ride_to_heap(world, hero, companion_cfg)
    omen_appears(world, hero, omen_cfg)
    search_heap(world, hero, part_cfg)
    twist_realization(world, hero, machine_cfg, part_cfg, omen_cfg)
    repair_machine(world, hero, elder, machine_cfg, part_cfg, omen_cfg, companion_cfg)
    ending(world, hero, machine_cfg)

    world.facts.update(
        hero=hero,
        elder=elder,
        machine_cfg=machine_cfg,
        part_cfg=part_cfg,
        omen_cfg=omen_cfg,
        companion_cfg=companion_cfg,
        machine=machine,
        part=part,
        scooter=scooter,
        village=village,
        repaired=machine.meters["working"] >= THRESHOLD,
        feared=hero.memes["fear"] >= THRESHOLD,
        twist_truth=omen_cfg.truth,
    )
    return world


KNOWLEDGE = {
    "machine": [
        (
            "What is a machine?",
            "A machine is something made of parts that work together to do a job. If one important part is missing, the whole machine can stop."
        )
    ],
    "heap": [
        (
            "What is a heap?",
            "A heap is a big pile of things lying together. In a story, an old heap can hide useful things among the scraps."
        )
    ],
    "scooter": [
        (
            "What is a scooter?",
            "A scooter is a small ride-on toy or vehicle with wheels and a handle. A child can push with one foot to glide along."
        )
    ],
    "gear": [
        (
            "What does a gear do?",
            "A gear is a toothed wheel that helps one part of a machine turn another. If the right gear is missing, the machine may not move."
        )
    ],
    "wind": [
        (
            "What does wind do?",
            "Wind can push leaves, turn vanes, and help some machines move. You cannot see it directly, but you can see what it changes."
        )
    ],
    "rain": [
        (
            "Why is rain important for plants?",
            "Plants need water to grow. Rain soaks into the ground so roots can drink."
        )
    ],
    "shadow": [
        (
            "What is a shadow?",
            "A shadow is a dark shape made when something blocks light. A shadow can look strange until you find what made it."
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is when the truth turns out to be different from what characters first believed. It surprises you, but it still fits the story."
        )
    ],
}
KNOWLEDGE_ORDER = ["scooter", "machine", "heap", "gear", "wind", "rain", "shadow", "twist"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    machine_cfg = world.facts["machine_cfg"]
    part_cfg = world.facts["part_cfg"]
    omen_cfg = world.facts["omen_cfg"]
    return [
        'Write a short mythic story for a 3-to-5-year-old that includes the words "scooter", "machine", and "heap".',
        f"Tell a gentle myth where {hero.id} rides a scooter to an old heap to find a lost piece for {machine_cfg.title}.",
        f"Write a story with a twist where {omen_cfg.fear_name} seems frightening at first, but the truth helps {hero.id} repair a sacred machine using {part_cfg.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    machine_cfg = f["machine_cfg"]
    part_cfg = f["part_cfg"]
    omen_cfg = f["omen_cfg"]
    companion_cfg = f["companion_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child with a scooter, and {elder.id}, the keeper of the sacred hill. {companion_cfg.title.capitalize()} goes along too."
        ),
        (
            f"Why did {hero.id} go to the heap?",
            f"{hero.id} went because {machine_cfg.title} had gone still and the valley needed its blessing again. {elder.id} believed the lost heart-piece was hiding in the old heap."
        ),
        (
            f"What did {hero.id} find there?",
            f"{hero.id} found {part_cfg.phrase}. It stood out in the heap because it still seemed alive with a special shine."
        ),
        (
            "What was the twist?",
            f"At first {hero.id} thought the strange sign at the heap might be {omen_cfg.fear_name}. Then the truth turned out to be different: {omen_cfg.truth}."
        ),
        (
            f"How was the machine fixed?",
            f"{elder.id} set the piece into the machine, and it fit at once. Because it was the true missing part, the machine woke and its gift returned to the valley."
        ),
        (
            "How did the story end?",
            f"It ended with the hill alive again and the valley changed for the better. The new sound and light showed that what looked like a heap of scraps had been hiding an answer."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    machine_cfg = world.facts["machine_cfg"]
    omen_cfg = world.facts["omen_cfg"]
    tags = {"scooter", "machine", "heap", "twist"}
    if machine_cfg.id == "dawn_wheel":
        tags |= {"gear"}
    if machine_cfg.id == "wind_lantern":
        tags |= {"wind"}
    if machine_cfg.id == "rain_harp":
        tags |= {"rain"}
    if omen_cfg.id == "serpent_shadow":
        tags |= {"shadow"}
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        machine="dawn_wheel",
        part="bell_gear",
        omen="serpent_shadow",
        companion="sparrow",
        child_name="Mira",
        child_gender="girl",
        elder_role="priestess",
        trait="careful",
        seed=101,
    ),
    StoryParams(
        machine="rain_harp",
        part="cup_leaf",
        omen="speaking_heap",
        companion="goat",
        child_name="Orin",
        child_gender="boy",
        elder_role="keeper",
        trait="steady",
        seed=102,
    ),
    StoryParams(
        machine="wind_lantern",
        part="copper_vane",
        omen="bronze_eyes",
        companion="dog",
        child_name="Tala",
        child_gender="girl",
        elder_role="priestess",
        trait="brave",
        seed=103,
    ),
]


ASP_RULES = r"""
compatible(M,P) :- machine(M), part(P), needs(M,T), fits(P,T).
valid(M,P,O) :- compatible(M,P), omen(O).

#show valid/3.
#show compatible/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for machine_id, machine in MACHINES.items():
        lines.append(asp.fact("machine", machine_id))
        lines.append(asp.fact("needs", machine_id, machine.fit_tag))
    for part_id, part in PARTS.items():
        lines.append(asp.fact("part", part_id))
        lines.append(asp.fact("fits", part_id, part.fit_tag))
    for omen_id in OMENS:
        lines.append(asp.fact("omen", omen_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(777))
        params.seed = 777
        sample = generate(params)
        if "scooter" not in sample.story or "machine" not in sample.story or "heap" not in sample.story:
            raise StoryError("Required seed words missing from generated story.")
        print("OK: default seeded generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a child on a scooter seeks a lost heart-piece in a bronze heap to wake a sacred machine."
    )
    ap.add_argument("--machine", choices=sorted(MACHINES))
    ap.add_argument("--part", choices=sorted(PARTS))
    ap.add_argument("--omen", choices=sorted(OMENS))
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-role", choices=sorted(ELDERS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render curated stories")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid machine/part/omen combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.machine and args.part:
        machine = MACHINES[args.machine]
        part = PARTS[args.part]
        if not compatible(machine, part):
            raise StoryError(explain_rejection(machine, part))

    combos = [
        combo
        for combo in valid_combos()
        if (args.machine is None or combo[0] == args.machine)
        and (args.part is None or combo[1] == args.part)
        and (args.omen is None or combo[2] == args.omen)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    machine_id, part_id, omen_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(sorted(COMPANIONS))
    elder_role = args.elder_role or rng.choice(sorted(ELDERS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        machine=machine_id,
        part=part_id,
        omen=omen_id,
        companion=companion,
        child_name=child_name,
        child_gender=child_gender,
        elder_role=elder_role,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.machine not in MACHINES:
        raise StoryError(f"Unknown machine: {params.machine}")
    if params.part not in PARTS:
        raise StoryError(f"Unknown part: {params.part}")
    if params.omen not in OMENS:
        raise StoryError(f"Unknown omen: {params.omen}")
    if params.companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {params.companion}")
    if params.elder_role not in ELDERS:
        raise StoryError(f"Unknown elder role: {params.elder_role}")
    machine_cfg = MACHINES[params.machine]
    part_cfg = PARTS[params.part]
    if not compatible(machine_cfg, part_cfg):
        raise StoryError(explain_rejection(machine_cfg, part_cfg))

    world = tell(
        machine_cfg=machine_cfg,
        part_cfg=part_cfg,
        omen_cfg=OMENS[params.omen],
        companion_cfg=COMPANIONS[params.companion],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_role=params.elder_role,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (machine, part, omen) combos:\n")
        for machine_id, part_id, omen_id in combos:
            print(f"  {machine_id:13} {part_id:12} {omen_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.child_name}: {p.machine} with {p.part} ({p.omen})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
