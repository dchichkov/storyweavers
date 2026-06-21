#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/compression_culprit_sound_effects_adventure.py
========================================================================

A standalone story world about a small adventure that turns spooky for one
moment when a mysterious sound follows two children down a trail. The noise has
a real physical cause: compression inside their pack. They first imagine a
monster or sneaky culprit in the shadows, then discover the true culprit is one
of their own supplies being squeezed by another object. They fix the pack and
finish the adventure more bravely.

Run it
------
    python storyworlds/worlds/gpt-5.4/compression_culprit_sound_effects_adventure.py
    python storyworlds/worlds/gpt-5.4/compression_culprit_sound_effects_adventure.py --setting cave --noisy whistle --heavy stone_sample
    python storyworlds/worlds/gpt-5.4/compression_culprit_sound_effects_adventure.py --fix shake_pack   # rejected
    python storyworlds/worlds/gpt-5.4/compression_culprit_sound_effects_adventure.py --all
    python storyworlds/worlds/gpt-5.4/compression_culprit_sound_effects_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/compression_culprit_sound_effects_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    compressible: bool = False
    makes_sound: bool = False
    # two axes: physical meters + emotional memes
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


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
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
class Setting:
    id: str
    place: str
    opening: str
    goal: str
    tight_spot: str
    ending: str
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
class NoisyItem:
    id: str
    label: str
    phrase: str
    sound: str
    verb: str
    explain: str
    sensitivity: int
    compressible: bool = True
    makes_sound: bool = True
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
class HeavyItem:
    id: str
    label: str
    phrase: str
    pressure: int
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_compression_sound(world: World) -> list[str]:
    out: list[str] = []
    pack = world.get("pack")
    noisy = world.get("noisy")
    if noisy.meters["compression"] < THRESHOLD or not noisy.makes_sound:
        return out
    sig = ("compression_sound", noisy.id, int(noisy.meters["compression"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pack.meters["noise"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__sound__")
    return out


def _r_found_relief(world: World) -> list[str]:
    out: list[str] = []
    noisy = world.get("noisy")
    if noisy.meters["found"] < THRESHOLD:
        return out
    sig = ("found_relief", noisy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        if kid.memes["fear"] > 0:
            kid.memes["fear"] -= 1
        kid.memes["bravery"] += 1
        kid.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="compression_sound", tag="physical", apply=_r_compression_sound),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def compression_hazard(noisy: NoisyItem, heavy: HeavyItem) -> bool:
    return noisy.compressible and noisy.makes_sound and heavy.pressure >= noisy.sensitivity


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def sound_strength(noisy: NoisyItem, heavy: HeavyItem) -> int:
    return heavy.pressure


def can_solve(noisy: NoisyItem, heavy: HeavyItem, fix: Fix) -> bool:
    return fix.power >= sound_strength(noisy, heavy)


def explain_rejection(noisy: NoisyItem, heavy: HeavyItem) -> str:
    if not noisy.compressible or not noisy.makes_sound:
        return (
            f"(No story: {noisy.phrase} would not make a mystery sound under pressure, "
            f"so there is no culprit for the children to discover.)"
        )
    if heavy.pressure < noisy.sensitivity:
        return (
            f"(No story: {heavy.phrase} is too gentle to squeeze {noisy.phrase} enough "
            f"to make {noisy.sound}. Pick a heavier object or a more easily squeezed item.)"
        )
    return "(No story: this combination does not create a compression mystery.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of the sensible fixes: {better}.)"
    )


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup_adventure(world: World, leader: Entity, partner: Entity, setting: Setting) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
        kid.memes["curiosity"] += 1
        kid.memes["bravery"] += 1
    world.say(
        f"One bright afternoon, {leader.id} and {partner.id} set out for {setting.place}. "
        f"{setting.opening}"
    )
    world.say(
        f'"Today we are explorers," {leader.id} said. "We are going to find {setting.goal}."'
    )


def pack_supplies(world: World, leader: Entity, noisy: NoisyItem, heavy: HeavyItem) -> None:
    world.say(
        f"In their little adventure pack they carried {noisy.phrase} and {heavy.phrase}. "
        f"Everything seemed ready for a grand journey."
    )
    leader.memes["pride"] += 1


def enter_tight_spot(world: World, partner: Entity, setting: Setting) -> None:
    world.say(
        f"Soon they reached {setting.tight_spot}. {partner.id} ducked low and held the map close."
    )


def squeeze_pack(world: World, noisy_ent: Entity, heavy: HeavyItem, noisy: NoisyItem) -> None:
    noisy_ent.meters["compression"] = float(heavy.pressure)
    noisy_ent.meters["sound_strength"] = float(sound_strength(noisy, heavy))
    propagate(world, narrate=False)
    world.say(
        f"As the pack scraped through the narrow place, it gave a squeeze of compression."
    )
    if world.get("pack").meters["noise"] >= THRESHOLD:
        world.say(
            f'"{noisy.sound}" went the pack. Then again: "{noisy.sound}!"'
        )


def guess_monster(world: World, leader: Entity, partner: Entity) -> None:
    leader.memes["alarm"] += 1
    partner.memes["alarm"] += 1
    world.say(
        f'{partner.id} froze. "Did you hear that?" {partner.pronoun()} whispered.'
    )
    world.say(
        f'"Maybe a tunnel beast is following us," {leader.id} said, though {leader.pronoun()} tried to sound brave.'
    )


def inspect_pack(world: World, leader: Entity, partner: Entity, noisy: NoisyItem, heavy: HeavyItem) -> None:
    world.say(
        f"But {partner.id} listened again and noticed the sound came only when {leader.id} hugged the pack."
    )
    world.say(
        f'"Wait," {partner.id} said. "The culprit might be inside our own bag."'
    )
    world.say(
        f"They opened the flap and found {heavy.phrase} pressing on {noisy.phrase}."
    )
    world.say(
        f"It was not a beast at all. It was simple compression: {heavy.label} {noisy.explain}."
    )


def apply_fix(world: World, fix: Fix, noisy_ent: Entity, heavy_ent: Entity, noisy: NoisyItem) -> None:
    noisy_ent.meters["compression"] = max(0.0, noisy_ent.meters["compression"] - fix.power)
    heavy_ent.meters["repacked"] += 1
    noisy_ent.meters["found"] += 1
    if noisy_ent.meters["compression"] < THRESHOLD:
        world.get("pack").meters["noise"] = 0.0
    propagate(world, narrate=False)
    world.say(fix.text.replace("{noisy}", noisy.label))


def sound_returns(world: World, noisy: NoisyItem) -> None:
    world.get("pack").meters["noise"] = 1.0
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.say(
        f'For one hopeful moment the trail was quiet. Then: "{noisy.sound}!" The pack squealed again.'
    )


def finish_bravely(world: World, leader: Entity, partner: Entity, setting: Setting) -> None:
    for kid in (leader, partner):
        kid.memes["confidence"] += 1
    world.say(
        f'{leader.id} laughed first. "So that was the culprit!" {leader.pronoun().capitalize()} said.'
    )
    world.say(
        f"With the pack sitting properly, they walked on to {setting.ending}. "
        f"This time, every shadow looked smaller, and the trail sounded like an adventure again instead of a warning."
    )


def retreat_wisely(world: World, leader: Entity, partner: Entity, setting: Setting) -> None:
    for kid in (leader, partner):
        kid.memes["caution"] += 1
    world.say(
        f'{partner.id} held the map against {partner.pronoun("possessive")} chest. "Real explorers can try again tomorrow," {partner.pronoun()} said.'
    )
    world.say(
        f"So they turned back from {setting.tight_spot} and headed home, still talking about the sound. "
        f"At the kitchen table they promised to pack more carefully next time, and the next adventure would begin with wiser hands."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    noisy: NoisyItem,
    heavy: HeavyItem,
    fix: Fix,
    leader_name: str = "Nora",
    leader_gender: str = "girl",
    partner_name: str = "Finn",
    partner_gender: str = "boy",
) -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    pack = world.add(Entity(id="pack", type="pack", label="adventure pack"))
    noisy_ent = world.add(
        Entity(
            id="noisy",
            type="supply",
            label=noisy.label,
            compressible=noisy.compressible,
            makes_sound=noisy.makes_sound,
        )
    )
    heavy_ent = world.add(Entity(id="heavy", type="supply", label=heavy.label))

    world.facts.update(
        setting=setting,
        noisy_cfg=noisy,
        heavy_cfg=heavy,
        fix=fix,
        leader=leader,
        partner=partner,
        pack=pack,
        noisy=noisy_ent,
        heavy=heavy_ent,
        sound_happened=False,
        culprit_found=False,
        outcome="unknown",
    )

    setup_adventure(world, leader, partner, setting)
    pack_supplies(world, leader, noisy, heavy)

    world.para()
    enter_tight_spot(world, partner, setting)
    squeeze_pack(world, noisy_ent, heavy, noisy)
    if pack.meters["noise"] >= THRESHOLD:
        world.facts["sound_happened"] = True
    guess_monster(world, leader, partner)

    world.para()
    inspect_pack(world, leader, partner, noisy, heavy)
    world.facts["culprit_found"] = True
    apply_fix(world, fix, noisy_ent, heavy_ent, noisy)

    solved = can_solve(noisy, heavy, fix)
    if solved:
        world.facts["outcome"] = "solved"
        world.para()
        finish_bravely(world, leader, partner, setting)
    else:
        world.facts["outcome"] = "retreat"
        sound_returns(world, noisy)
        world.para()
        retreat_wisely(world, leader, partner, setting)

    world.facts["solved"] = solved
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cave": Setting(
        id="cave",
        place="the old hill cave",
        opening="A ribbon of path wound between ferns and stones, and the cave mouth waited like a secret door.",
        goal="the glitter room at the back",
        tight_spot="a low tunnel where the walls pinched close together",
        ending="the glitter room, where tiny crystals flashed like stars",
        tags={"cave", "adventure"},
    ),
    "ruins": Setting(
        id="ruins",
        place="the ivy ruins behind the orchard",
        opening="Broken steps and sleepy statues made the place feel like a forgotten kingdom.",
        goal="the round tower stair",
        tight_spot="a cracked stone archway with hardly room for the pack",
        ending="the round tower stair, where the wind hummed through the ivy",
        tags={"ruins", "adventure"},
    ),
    "canyon": Setting(
        id="canyon",
        place="the red canyon trail",
        opening="Dusty rocks and little echoing turns made every bend feel like a map waiting to be read.",
        goal="the lookout ledge",
        tight_spot="a narrow pass between two warm red walls",
        ending="the lookout ledge, where the whole valley opened wide",
        tags={"canyon", "adventure"},
    ),
}

NOISY_ITEMS = {
    "whistle": NoisyItem(
        id="whistle",
        label="whistle",
        phrase="a tin whistle",
        sound="Peeeep",
        verb="peeped",
        explain="pressed the whistle just enough to make it peep",
        sensitivity=1,
        tags={"whistle", "sound"},
    ),
    "juice_pouch": NoisyItem(
        id="juice_pouch",
        label="juice pouch",
        phrase="a round juice pouch",
        sound="Glup-glup",
        verb="glupped",
        explain="squeezed the pouch until the straw made a glup-glup noise",
        sensitivity=2,
        tags={"juice", "sound"},
    ),
    "squeaky_frog": NoisyItem(
        id="squeaky_frog",
        label="squeaky frog",
        phrase="a rubber squeaky frog",
        sound="Squeeeak",
        verb="squeaked",
        explain="squashed the rubber frog until it squeaked",
        sensitivity=1,
        tags={"toy", "sound"},
    ),
    "rope": NoisyItem(
        id="rope",
        label="rope",
        phrase="a coil of rope",
        sound="",
        verb="",
        explain="would not make a sudden mystery sound",
        sensitivity=3,
        compressible=False,
        makes_sound=False,
        tags={"rope"},
    ),
}

HEAVY_ITEMS = {
    "canteen": HeavyItem(
        id="canteen",
        label="the canteen",
        phrase="a sloshing canteen",
        pressure=2,
        tags={"canteen"},
    ),
    "compass_tin": HeavyItem(
        id="compass_tin",
        label="the compass tin",
        phrase="a metal compass tin",
        pressure=1,
        tags={"compass"},
    ),
    "stone_sample": HeavyItem(
        id="stone_sample",
        label="the stone sample",
        phrase="a smooth stone sample",
        pressure=3,
        tags={"rock"},
    ),
}

FIXES = {
    "repack": Fix(
        id="repack",
        sense=3,
        power=3,
        text="They stopped, spread a scarf on a flat rock, and repacked the bag so the heavy things sat low and the {noisy} rested safely on top.",
        fail="They shifted a few things around, but the heavy item still pressed too hard.",
        qa_text="They repacked the bag so the heavy item was no longer pressing on it",
        tags={"repack"},
    ),
    "pad_scarf": Fix(
        id="pad_scarf",
        sense=3,
        power=2,
        text="They tucked a soft scarf around the {noisy}, making a little nest so the hard edge could not press on it anymore.",
        fail="They tucked in a scarf, but the pressure was still too strong.",
        qa_text="They padded it with a scarf so it would not be squeezed",
        tags={"padding"},
    ),
    "loosen_strap": Fix(
        id="loosen_strap",
        sense=2,
        power=1,
        text="They loosened the straps and shifted the bag on smaller shoulders, hoping the {noisy} would stop being squeezed.",
        fail="They loosened the straps, but the heavy object still leaned on it.",
        qa_text="They loosened the straps so the pack would squeeze less tightly",
        tags={"straps"},
    ),
    "shake_pack": Fix(
        id="shake_pack",
        sense=1,
        power=0,
        text="They shook the bag hard, which only jumbled everything together.",
        fail="They shook the bag, but that did not fix the pressure at all.",
        qa_text="They shook the pack",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Ava", "Lily", "Zoe", "Ella", "Maya", "Anna"]
BOY_NAMES = ["Finn", "Leo", "Max", "Sam", "Theo", "Eli", "Noah", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_fixes():
        return combos
    for sid in SETTINGS:
        for nid, noisy in NOISY_ITEMS.items():
            for hid, heavy in HEAVY_ITEMS.items():
                if compression_hazard(noisy, heavy):
                    combos.append((sid, nid, hid))
    return combos


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    noisy: str
    heavy: str
    fix: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
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
    "compression": [
        (
            "What is compression?",
            "Compression happens when something gets squeezed into a smaller space. When objects press on each other, compression can bend, squash, or change the way they sound."
        )
    ],
    "sound": [
        (
            "Why can squeezed things make sounds?",
            "When something soft or hollow gets pressed, air or moving parts can make a noise. That is why a whistle, pouch, or squeaky toy may sound different when squeezed."
        )
    ],
    "whistle": [
        (
            "What is a whistle?",
            "A whistle is a small object that makes a sharp sound when air moves through it. Even a little push or puff can make it peep."
        )
    ],
    "juice": [
        (
            "Why can a juice pouch make a glup-glup sound?",
            "When a juice pouch is squeezed, the juice and air inside shift around. That movement can make the straw or pouch burble and glup."
        )
    ],
    "toy": [
        (
            "Why do squeaky toys squeak?",
            "A squeaky toy has a tiny part inside that moves air when the toy is pressed. The air makes the squeak sound."
        )
    ],
    "repack": [
        (
            "Why does repacking a bag help?",
            "Repacking helps because heavy things can be placed where they do not crush softer things. A well-packed bag is easier to carry and keeps supplies safer."
        )
    ],
    "padding": [
        (
            "What does padding do inside a bag?",
            "Padding makes a soft space around an object. It helps stop bumps and pressure from pressing too hard on that object."
        )
    ],
    "straps": [
        (
            "Why might loosening a strap change how a bag feels?",
            "A tight strap can pull a bag into a squeezed shape. Loosening it can change the pressure, though sometimes that alone is not enough."
        )
    ],
    "adventure": [
        (
            "What makes something feel like an adventure?",
            "An adventure feels like a journey with a goal, a surprise, and a brave choice. It can happen on a small trail if the people on it use imagination and courage."
        )
    ],
}
KNOWLEDGE_ORDER = ["compression", "sound", "whistle", "juice", "toy", "repack", "padding", "straps", "adventure"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    noisy = f["noisy_cfg"]
    outcome = f["outcome"]
    if outcome == "solved":
        return [
            f'Write a short adventure story for a 3-to-5-year-old that includes the words "compression" and "culprit" and uses sound effects like "{noisy.sound}!"',
            f"Tell a gentle adventure where two children hear a spooky sound in {setting.place}, think something is following them, and then discover the culprit is inside their own pack.",
            f"Write a child-facing mystery-adventure with a narrow passage, a surprising sound effect, and a brave ending where the children solve the problem themselves.",
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "compression" and "culprit" and uses sound effects like "{noisy.sound}!"',
        f"Tell an adventure where two children find the culprit behind a spooky pack sound, but their first fix is too weak, so they head home and plan better for next time.",
        f"Write a simple trail mystery with sound effects, a real physical cause, and an ending that says stopping to be wise can be brave too.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    setting = f["setting"]
    noisy = f["noisy_cfg"]
    heavy = f["heavy_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {partner.id}, two children on a small adventure. They were exploring {setting.place} with a pack full of supplies."
        ),
        (
            "What made the children feel nervous?",
            f"They heard '{noisy.sound}!' from the pack while they were in {setting.tight_spot}. The sound came at a spooky moment, so at first they wondered if something was following them."
        ),
        (
            "What was the culprit really?",
            f"The real culprit was not a beast at all. It was {heavy.phrase} pressing on {noisy.phrase}, and that compression made the sound."
        ),
    ]
    if outcome == "solved":
        qa.append(
            (
                "How did they solve the problem?",
                f"They looked inside the pack and {fix.qa_text}. That worked because the heavy object stopped pressing on the noisy item, so the sound did not come back."
            )
        )
        qa.append(
            (
                "How did the adventure end?",
                f"They kept going and reached {setting.ending}. The ending shows they were braver after learning the sound had an ordinary cause."
            )
        )
    else:
        qa.append(
            (
                "Why did they turn back instead of going on?",
                f"They did find the culprit, but their fix was not strong enough, so the sound came back. They chose to go home and pack more carefully, which was a wise and brave choice."
            )
        )
        qa.append(
            (
                "What did they learn?",
                f"They learned that a scary noise can have a real cause inside their own gear. They also learned that careful packing matters when heavy things can squeeze softer things."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"compression", "sound", "adventure"} | set(f["noisy_cfg"].tags) | set(f["fix"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
            bits.append(f"attrs={e.attrs}")
        flags = [n for n, on in (("compressible", e.compressible), ("makes_sound", e.makes_sound)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="cave",
        noisy="whistle",
        heavy="stone_sample",
        fix="repack",
        leader="Nora",
        leader_gender="girl",
        partner="Finn",
        partner_gender="boy",
    ),
    StoryParams(
        setting="ruins",
        noisy="juice_pouch",
        heavy="canteen",
        fix="pad_scarf",
        leader="Leo",
        leader_gender="boy",
        partner="Mia",
        partner_gender="girl",
    ),
    StoryParams(
        setting="canyon",
        noisy="squeaky_frog",
        heavy="stone_sample",
        fix="loosen_strap",
        leader="Ava",
        leader_gender="girl",
        partner="Ben",
        partner_gender="boy",
    ),
]


def outcome_of(params: StoryParams) -> str:
    if params.noisy not in NOISY_ITEMS or params.heavy not in HEAVY_ITEMS or params.fix not in FIXES:
        raise StoryError("(Invalid params: unknown registry key.)")
    return "solved" if can_solve(NOISY_ITEMS[params.noisy], HEAVY_ITEMS[params.heavy], FIXES[params.fix]) else "retreat"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- compression gate ------------------------------------------------------
hazard(N, H) :- noisy(N), heavy(H), compressible(N), makes_sound(N),
                sensitivity(N, S), pressure(H, P), P >= S.
valid(St, N, H) :- setting(St), hazard(N, H).

% --- sensible fixes --------------------------------------------------------
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.

% --- outcomes --------------------------------------------------------------
strength(P) :- chosen_heavy(H), pressure(H, P).
solved :- chosen_fix(F), power(F, Q), strength(P), Q >= P.
outcome(solved) :- solved.
outcome(retreat) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid, noisy in NOISY_ITEMS.items():
        lines.append(asp.fact("noisy", nid))
        lines.append(asp.fact("sensitivity", nid, noisy.sensitivity))
        if noisy.compressible:
            lines.append(asp.fact("compressible", nid))
        if noisy.makes_sound:
            lines.append(asp.fact("makes_sound", nid))
    for hid, heavy in HEAVY_ITEMS.items():
        lines.append(asp.fact("heavy", hid))
        lines.append(asp.fact("pressure", hid, heavy.pressure))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_heavy", params.heavy),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_fixes = {f.id for f in sensible_fixes()}
    clingo_fixes = set(asp_sensible_fixes())
    if python_fixes == clingo_fixes:
        print(f"OK: sensible fixes match ({sorted(python_fixes)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_fixes)} python={sorted(python_fixes)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params failed on seed-like case {s}.")
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

    # smoke test ordinary generation + emit + JSON/QA formatting
    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        _ = sample.to_json()
        _ = format_qa(sample)
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke test passed for generate()/emit()/json.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a pack mystery caused by compression on an adventure."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--noisy", choices=NOISY_ITEMS)
    ap.add_argument("--heavy", choices=HEAVY_ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--leader")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [x for x in pool if x != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.noisy and args.heavy:
        noisy = NOISY_ITEMS[args.noisy]
        heavy = HEAVY_ITEMS[args.heavy]
        if not compression_hazard(noisy, heavy):
            raise StoryError(explain_rejection(noisy, heavy))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.noisy is None or combo[1] == args.noisy)
        and (args.heavy is None or combo[2] == args.heavy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, noisy, heavy = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    leader = args.leader or _pick_name(rng, leader_gender)
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    partner = args.partner or _pick_name(rng, partner_gender, avoid=leader)

    return StoryParams(
        setting=setting,
        noisy=noisy,
        heavy=heavy,
        fix=fix,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        noisy = NOISY_ITEMS[params.noisy]
        heavy = HEAVY_ITEMS[params.heavy]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid params: unknown key {err.args[0]!r}.)") from None

    if not compression_hazard(noisy, heavy):
        raise StoryError(explain_rejection(noisy, heavy))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        setting=setting,
        noisy=noisy,
        heavy=heavy,
        fix=fix,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
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
        print(asp_program("", "#show valid/3.\n#show sensible_fix/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        fixes = asp_sensible_fixes()
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(fixes)}\n")
        print(f"{len(combos)} compatible (setting, noisy, heavy) combos:\n")
        for setting, noisy, heavy in combos:
            print(f"  {setting:8} {noisy:12} {heavy}")
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
            header = f"### {p.leader} & {p.partner}: {p.noisy} under {p.heavy} ({p.setting}, {p.fix}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
