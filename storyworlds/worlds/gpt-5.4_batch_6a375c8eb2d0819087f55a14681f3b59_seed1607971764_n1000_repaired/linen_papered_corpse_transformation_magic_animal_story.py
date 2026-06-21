#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/linen_papered_corpse_transformation_magic_animal_story.py
====================================================================================

A small storyworld about woodland animals who find a still little bundle that
looks frightening at first, then discover that patient care and gentle magic
are helping a sleeping creature transform.

The seed asked for the words "linen", "papered", and "corpse", plus
Transformation and Magic in an Animal Story style. This world turns that into a
constraint-checked domain: a wrapped cocoon-like sleeper can only transform when
its wrapping is breathable and warm enough, the chosen place supports the chosen
kind of magic, and the animals wait long enough.

Run it
------
    python storyworlds/worlds/gpt-5.4/linen_papered_corpse_transformation_magic_animal_story.py
    python storyworlds/worlds/gpt-5.4/linen_papered_corpse_transformation_magic_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/linen_papered_corpse_transformation_magic_animal_story.py --qa --seed 7
    python storyworlds/worlds/gpt-5.4/linen_papered_corpse_transformation_magic_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4/linen_papered_corpse_transformation_magic_animal_story.py --verify
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
    breathable: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "doe", "ewe", "mother"}
        male = {"buck", "stag", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    moonlit: bool = False
    dewy: bool = False
    sheltered: bool = False
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
class Sleeper:
    id: str
    label: str
    sleeping_name: str
    transformed_name: str
    shell_word: str
    need_warmth: int
    need_wait: int
    color: str
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
class Wrapping:
    id: str
    label: str
    phrase: str
    warmth: int
    breathable: bool = True
    papered: bool = False
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
class Magic:
    id: str
    label: str
    sense: int
    needs: str
    sparkle: str
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
class StoryParams:
    place: str
    sleeper: str
    wrapping: str
    magic: str
    nights: int
    finder_name: str
    finder_species: str
    doubter_name: str
    doubter_species: str
    elder_name: str
    elder_species: str
    finder_trait: str
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


def _r_ready_by_wrapping(world: World) -> list[str]:
    out: list[str] = []
    sleeper = world.get("sleeper")
    wrapping = world.get("wrapping")
    cfg = world.facts["sleeper_cfg"]
    if not wrapping.breathable:
        return out
    sig = ("wrap_ready",)
    if sig in world.fired:
        return out
    if wrapping.meters["warmth"] >= cfg.need_warmth:
        world.fired.add(sig)
        sleeper.meters["readiness"] += 1
        out.append("__readiness__")
    return out


def _r_ready_by_magic(world: World) -> list[str]:
    out: list[str] = []
    sleeper = world.get("sleeper")
    place = world.get("place")
    magic = world.facts["magic_cfg"]
    sig = ("magic_ready", magic.id)
    if sig in world.fired:
        return out
    if magic_ok(world.facts["place_cfg"], magic):
        world.fired.add(sig)
        place.meters["magic"] += 1
        sleeper.meters["readiness"] += 1
        out.append("__magic__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    sleeper = world.get("sleeper")
    cfg = world.facts["sleeper_cfg"]
    sig = ("transform",)
    if sig in world.fired:
        return out
    if sleeper.meters["readiness"] >= 2 and world.facts["nights_waited"] >= cfg.need_wait:
        world.fired.add(sig)
        sleeper.meters["transformed"] += 1
        sleeper.meters["still"] = 0.0
        sleeper.memes["alive_revealed"] += 1
        for eid in ("finder", "doubter", "elder"):
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["wonder"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule(name="ready_by_wrapping", tag="physical", apply=_r_ready_by_wrapping),
    Rule(name="ready_by_magic", tag="magic", apply=_r_ready_by_magic),
    Rule(name="transform", tag="change", apply=_r_transform),
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


PLACES = {
    "moon_garden": Place(
        id="moon_garden",
        label="the moon garden",
        scene="where white flowers opened after dusk and silver light pooled on the stones",
        moonlit=True,
        sheltered=False,
        tags={"moon", "garden"},
    ),
    "dew_meadow": Place(
        id="dew_meadow",
        label="the dew meadow",
        scene="where tall grass caught the morning drops and bent softly in the wind",
        dewy=True,
        sheltered=False,
        tags={"dew", "meadow"},
    ),
    "linen_loft": Place(
        id="linen_loft",
        label="the linen loft",
        scene="under old rafters where a cracked window let in a stripe of moonlight",
        moonlit=True,
        sheltered=True,
        tags={"moon", "loft"},
    ),
    "muddy_ditch": Place(
        id="muddy_ditch",
        label="the muddy ditch",
        scene="where water sat cold in the reeds and everything smelled of wet clay",
        moonlit=False,
        dewy=False,
        sheltered=False,
        tags={"ditch"},
    ),
}

SLEEPERS = {
    "caterpillar": Sleeper(
        id="caterpillar",
        label="caterpillar",
        sleeping_name="the curled caterpillar",
        transformed_name="a painted butterfly",
        shell_word="cocoon",
        need_warmth=1,
        need_wait=1,
        color="sunny orange and blue",
        tags={"butterfly", "change"},
    ),
    "silkworm": Sleeper(
        id="silkworm",
        label="silkworm",
        sleeping_name="the pale silkworm",
        transformed_name="a moon moth",
        shell_word="silken shell",
        need_warmth=2,
        need_wait=2,
        color="soft green with silver spots",
        tags={"moth", "change"},
    ),
    "woollybear": Sleeper(
        id="woollybear",
        label="woolly bear",
        sleeping_name="the fuzzy woolly bear",
        transformed_name="a tiger moth",
        shell_word="woolly case",
        need_warmth=2,
        need_wait=1,
        color="cream wings with tiny cinnamon marks",
        tags={"moth", "change"},
    ),
}

WRAPPINGS = {
    "linen_nest": Wrapping(
        id="linen_nest",
        label="linen nest",
        phrase="a little linen nest tucked with moss",
        warmth=2,
        breathable=True,
        papered=False,
        tags={"linen", "nest"},
    ),
    "papered_basket": Wrapping(
        id="papered_basket",
        label="papered basket",
        phrase="a berry basket papered with flower petals and lined with linen thread",
        warmth=1,
        breathable=True,
        papered=True,
        tags={"paper", "linen"},
    ),
    "glass_jar": Wrapping(
        id="glass_jar",
        label="glass jar",
        phrase="a shiny glass jar with a tight lid and one strip of linen underneath",
        warmth=1,
        breathable=False,
        papered=False,
        tags={"jar"},
    ),
}

MAGICS = {
    "moonbeam": Magic(
        id="moonbeam",
        label="moonbeam magic",
        sense=3,
        needs="moonlit",
        sparkle="a silver hush slid over the bundle like milk poured from the sky",
        tags={"moon", "magic"},
    ),
    "dew_blessing": Magic(
        id="dew_blessing",
        label="dew blessing",
        sense=3,
        needs="dewy",
        sparkle="round bright drops trembled and flashed like tiny bells of light",
        tags={"dew", "magic"},
    ),
    "crackle_spell": Magic(
        id="crackle_spell",
        label="crackle spell",
        sense=1,
        needs="none",
        sparkle="sharp sparks snapped much too close to the sleeping shell",
        tags={"magic"},
    ),
}

FINDER_SPECIES = ["Mouse", "Squirrel", "Rabbit", "Mole"]
ELDER_SPECIES = ["Owl", "Tortoise", "Badger"]
TRAITS = ["gentle", "curious", "careful", "brave", "patient"]

GIRL_NAMES = ["Mimi", "Pip", "Tansy", "Clover", "Fern", "Poppy"]
BOY_NAMES = ["Nip", "Bram", "Moss", "Twig", "Puck", "Nettle"]


def magic_ok(place: Place, magic: Magic) -> bool:
    if magic.needs == "moonlit":
        return place.moonlit
    if magic.needs == "dewy":
        return place.dewy
    return True


def transform_possible(place: Place, sleeper: Sleeper, wrapping: Wrapping,
                       magic: Magic, nights: int) -> bool:
    if magic.sense < SENSE_MIN:
        return False
    if not wrapping.breathable:
        return False
    if wrapping.warmth < sleeper.need_warmth:
        return False
    if nights < sleeper.need_wait:
        return False
    if not magic_ok(place, magic):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, int]]:
    combos: list[tuple[str, str, str, str, int]] = []
    for place_id, place in PLACES.items():
        for sleeper_id, sleeper in SLEEPERS.items():
            for wrapping_id, wrapping in WRAPPINGS.items():
                for magic_id, magic in MAGICS.items():
                    for nights in (1, 2):
                        if transform_possible(place, sleeper, wrapping, magic, nights):
                            combos.append((place_id, sleeper_id, wrapping_id, magic_id, nights))
    return combos


def explain_rejection(place: Place, sleeper: Sleeper, wrapping: Wrapping,
                      magic: Magic, nights: int) -> str:
    if magic.sense < SENSE_MIN:
        return (
            f"(No story: {magic.label} is too rough for a sleeping {sleeper.label}. "
            f"This world prefers gentle magic that helps instead of startling.)"
        )
    if not wrapping.breathable:
        return (
            f"(No story: {wrapping.label} is not breathable, so a sleeping "
            f"{sleeper.label} would not rest safely inside it.)"
        )
    if wrapping.warmth < sleeper.need_warmth:
        return (
            f"(No story: {wrapping.label} is too chilly for a {sleeper.label}. "
            f"It needs more warmth before a transformation can finish.)"
        )
    if nights < sleeper.need_wait:
        return (
            f"(No story: a {sleeper.label} needs at least {sleeper.need_wait} "
            f"night(s) of waiting before it can emerge.)"
        )
    if not magic_ok(place, magic):
        if magic.needs == "moonlit":
            need = "moonlight"
        elif magic.needs == "dewy":
            need = "fresh dawn dew"
        else:
            need = "the right kind of magic air"
        return (
            f"(No story: {place.label} does not offer {need}, so {magic.label} "
            f"cannot work there.)"
        )
    return "(No story: that combination does not make a reasonable transformation.)"


def prediction(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    sleeper = sim.get("sleeper")
    return {
        "transforms": sleeper.meters["transformed"] >= THRESHOLD,
        "readiness": sleeper.meters["readiness"],
    }


def find_bundle(world: World, finder: Entity, doubter: Entity,
                place: Place, wrapping: Wrapping, sleeper: Sleeper) -> None:
    finder.memes["care"] += 1
    doubter.memes["fear"] += 1
    world.say(
        f"One hush-soft evening, {finder.id} the {finder.type.lower()} and "
        f"{doubter.id} the {doubter.type.lower()} wandered into {place.label}, "
        f"{place.scene}."
    )
    world.say(
        f"Under a root they found {wrapping.phrase}. A scrap of paper still clung "
        f"to one side, so the little bundle looked oddly papered, even in the dim light."
    )
    world.say(
        f"Inside lay {sleeper.sleeping_name}, curled so still that {doubter.id} "
        f"whispered, \"It looks like a tiny corpse.\""
    )


def comfort(world: World, finder: Entity, doubter: Entity) -> None:
    world.say(
        f'"Do not say it so hard," {finder.id} murmured. '
        f'{finder.pronoun().capitalize()} smoothed the linen with one paw and tried '
        f"to keep brave."
    )
    finder.memes["hope"] += 1
    doubter.memes["fear"] += 1


def ask_elder(world: World, elder: Entity, sleeper: Sleeper) -> None:
    elder.memes["wisdom"] += 1
    world.say(
        f"Just then {elder.id} the {elder.type.lower()} came by and peered in. "
        f"\"That is no little corpse,\" {elder.pronoun()} said. "
        f"\"It is a sleeper in a {sleeper.shell_word}, halfway between one life and the next.\""
    )


def warn_and_predict(world: World, elder: Entity, place: Place, wrapping: Wrapping,
                     magic: Magic, sleeper: Sleeper) -> None:
    pred = prediction(world)
    world.facts["predicted_readiness"] = pred["readiness"]
    world.facts["predicted_transforms"] = pred["transforms"]
    if pred["transforms"]:
        world.say(
            f'{elder.id} touched the edge of the {wrapping.label}. '
            f'"Keep it warm, let {magic.label} do its gentle work in {place.label}, '
            f'and wait. By the right hour, this {sleeper.label} will not be still at all."'
        )
    else:
        world.say(
            f'"Something is missing," said {elder.id}. "Without the right care, '
            f'this sleeper cannot finish its change."'
        )


def carry_to_safety(world: World, finder: Entity, doubter: Entity, place: Place,
                    wrapping: Wrapping) -> None:
    world.say(
        f"So {finder.id} and {doubter.id} carried the bundle carefully to the safest patch of "
        f"{place.label}. They tucked the linen flat, steadied the papered edge, and set the "
        f"{wrapping.label} where no boot, beak, or wind could trouble it."
    )
    finder.memes["care"] += 1
    doubter.memes["care"] += 1


def wait_nights(world: World, finder: Entity, doubter: Entity, elder: Entity,
                magic: Magic, nights: int) -> None:
    world.facts["nights_waited"] = nights
    if nights == 1:
        world.say(
            f"They waited one whole night. {magic.sparkle.capitalize()}, and none of them said a word for fear of hurrying the mystery."
        )
    else:
        world.say(
            f"They waited two quiet nights. Each time {magic.sparkle}, and each time "
            f"{finder.id}, {doubter.id}, and {elder.id} watched with held breath."
        )
    propagate(world, narrate=False)


def emerge(world: World, finder: Entity, doubter: Entity, elder: Entity,
           sleeper: Sleeper) -> None:
    world.say(
        f"At last the shell gave a tiny shiver. What had seemed silent and lost "
        f"split open, and out climbed {sleeper.transformed_name}, {sleeper.color}."
    )
    world.say(
        f'{doubter.id} blinked hard. "It was alive all along," {doubter.pronoun()} breathed. '
        f'{elder.id} smiled, and {finder.id} laughed with pure relief.'
    )


def resolution(world: World, finder: Entity, doubter: Entity, elder: Entity,
               place: Place, sleeper: Sleeper) -> None:
    finder.memes["joy"] += 1
    doubter.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"The new creature flexed its wings, rose above {place.label}, and drifted through the night air as if it had been stitched from moonlight itself."
    )
    world.say(
        f"From then on, whenever {finder.id} and {doubter.id} found some small still thing, "
        f"they looked twice before naming it. In {place.label}, they had learned that quiet can be the doorway to transformation."
    )


def tell(place: Place, sleeper_cfg: Sleeper, wrapping_cfg: Wrapping, magic_cfg: Magic,
         nights: int, finder_name: str, finder_species: str, doubter_name: str,
         doubter_species: str, elder_name: str, elder_species: str,
         finder_trait: str) -> World:
    world = World()
    finder = world.add(Entity(
        id=finder_name,
        kind="character",
        type=finder_species.lower(),
        label=finder_species.lower(),
        role="finder",
        traits=[finder_trait],
        attrs={"species_title": finder_species},
    ))
    doubter = world.add(Entity(
        id=doubter_name,
        kind="character",
        type=doubter_species.lower(),
        label=doubter_species.lower(),
        role="doubter",
        traits=["jumpy"],
        attrs={"species_title": doubter_species},
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_species.lower(),
        label=elder_species.lower(),
        role="elder",
        traits=["wise"],
        attrs={"species_title": elder_species},
    ))
    place_ent = world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        role="place",
        attrs={"moonlit": place.moonlit, "dewy": place.dewy, "sheltered": place.sheltered},
    ))
    wrapping_ent = world.add(Entity(
        id="wrapping",
        type="wrapping",
        label=wrapping_cfg.label,
        role="wrapping",
        breathable=wrapping_cfg.breathable,
    ))
    sleeper_ent = world.add(Entity(
        id="sleeper",
        type="sleeper",
        label=sleeper_cfg.label,
        role="sleeper",
    ))

    wrapping_ent.meters["warmth"] = float(wrapping_cfg.warmth)
    wrapping_ent.meters["papered"] = 1.0 if wrapping_cfg.papered else 0.0
    sleeper_ent.meters["still"] = 1.0
    sleeper_ent.meters["readiness"] = 0.0
    place_ent.meters["magic"] = 0.0
    finder.memes["hope"] = 0.0
    finder.memes["care"] = 0.0
    doubter.memes["fear"] = 1.0
    doubter.memes["care"] = 0.0
    elder.memes["wisdom"] = 0.0

    world.facts.update(
        place_cfg=place,
        sleeper_cfg=sleeper_cfg,
        wrapping_cfg=wrapping_cfg,
        magic_cfg=magic_cfg,
        nights_waited=0,
        finder=finder,
        doubter=doubter,
        elder=elder,
    )

    find_bundle(world, finder, doubter, place, wrapping_cfg, sleeper_cfg)
    comfort(world, finder, doubter)

    world.para()
    ask_elder(world, elder, sleeper_cfg)
    warn_and_predict(world, elder, place, wrapping_cfg, magic_cfg, sleeper_cfg)

    world.para()
    carry_to_safety(world, finder, doubter, place, wrapping_cfg)
    wait_nights(world, finder, doubter, elder, magic_cfg, nights)

    world.para()
    if sleeper_ent.meters["transformed"] >= THRESHOLD:
        emerge(world, finder, doubter, elder, sleeper_cfg)
        resolution(world, finder, doubter, elder, place, sleeper_cfg)

    world.facts.update(
        transformed=sleeper_ent.meters["transformed"] >= THRESHOLD,
        place=place,
        sleeper=sleeper_cfg,
        wrapping=wrapping_cfg,
        magic=magic_cfg,
        nights=nights,
        outcome="transformed" if sleeper_ent.meters["transformed"] >= THRESHOLD else "still",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sleeper = f["sleeper"]
    place = f["place"]
    magic = f["magic"]
    return [
        'Write a gentle animal story for a 3-to-5-year-old that includes the words "linen", "papered", and "corpse", but ends tenderly rather than sadly.',
        f"Tell an animal story where small woodland friends find a still {sleeper.label} in {place.label} and learn that magic and patience can help a hidden transformation finish.",
        f"Write a magical transformation story in which a frightened animal first mistakes a sleeping creature for something dead, then sees {magic.label} reveal a beautiful new life.",
    ]


KNOWLEDGE = {
    "butterfly": [
        ("What happens when a caterpillar changes into a butterfly?",
         "A caterpillar makes a resting case around itself and changes slowly inside it. When the change is finished, it comes out as a butterfly with wings.")
    ],
    "moth": [
        ("What is a moth?",
         "A moth is a soft-winged insect a little like a butterfly. Many moths come out in the evening or at night.")
    ],
    "change": [
        ("Why do some animals stay very still while they change?",
         "Some small animals need quiet time while their bodies transform. Staying still helps the change happen safely.")
    ],
    "moon": [
        ("What is moonlight?",
         "Moonlight is sunlight bouncing off the moon and reaching us at night. It looks soft and silver.")
    ],
    "dew": [
        ("What is dew?",
         "Dew is tiny drops of water that gather on grass and leaves when the air turns cool. You often see it in the early morning.")
    ],
    "magic": [
        ("What is magic in a story?",
         "Magic in a story is a special wonder that helps surprising things happen. It makes the world feel bright and full of possibility.")
    ],
    "linen": [
        ("What is linen?",
         "Linen is a kind of cloth made from plant fibers. It feels light and soft, and people can use it to wrap or cover things.")
    ],
}


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    doubter = f["doubter"]
    elder = f["elder"]
    sleeper = f["sleeper"]
    wrapping = f["wrapping"]
    place = f["place"]
    magic = f["magic"]
    nights = f["nights"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {finder.id} the {finder.type}, {doubter.id} the {doubter.type}, and {elder.id} the {elder.type}. Together they care for a sleeping {sleeper.label}."
        ),
        (
            "Why did the bundle seem scary at first?",
            f"It was wrapped in linen and had a papered side, and the little body inside was perfectly still. That is why {doubter.id} whispered that it looked like a tiny corpse."
        ),
        (
            f"Why did {elder.id} tell them to wait in {place.label}?",
            f"{elder.id} knew the sleeper needed gentle conditions, not poking or panic. {magic.label.capitalize()} could work there, and the waiting gave the transformation time to finish."
        ),
    ]
    if f["transformed"]:
        qa.extend([
            (
                "How did the animals help the transformation happen?",
                f"They carried the bundle carefully, kept the wrapping safe, and waited {nights} night"
                f"{'' if nights == 1 else 's'} instead of disturbing it. Their patience mattered because the {sleeper.label} needed warmth, quiet, and the right magic."
            ),
            (
                "What came out of the bundle at the end?",
                f"{sleeper.transformed_name.capitalize()} came out. The still bundle only seemed lifeless at first, but it was really a changing creature inside."
            ),
            (
                f"What did {finder.id} and {doubter.id} learn?",
                f"They learned not to judge a quiet little body too quickly. What looked sad and final was really the middle of a change, and careful kindness helped them see that."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    sleeper = world.facts["sleeper"]
    place = world.facts["place"]
    magic = world.facts["magic"]
    wrapping = world.facts["wrapping"]
    tags = set(sleeper.tags) | set(place.tags) | set(magic.tags) | set(wrapping.tags)
    ordered = ["butterfly", "moth", "change", "moon", "dew", "magic", "linen"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.breathable:
            bits.append("breathable=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_garden",
        sleeper="caterpillar",
        wrapping="papered_basket",
        magic="moonbeam",
        nights=1,
        finder_name="Mimi",
        finder_species="Mouse",
        doubter_name="Bram",
        doubter_species="Rabbit",
        elder_name="Old Owl",
        elder_species="Owl",
        finder_trait="gentle",
    ),
    StoryParams(
        place="linen_loft",
        sleeper="silkworm",
        wrapping="linen_nest",
        magic="moonbeam",
        nights=2,
        finder_name="Pip",
        finder_species="Squirrel",
        doubter_name="Moss",
        doubter_species="Mole",
        elder_name="Aunt Badger",
        elder_species="Badger",
        finder_trait="careful",
    ),
    StoryParams(
        place="dew_meadow",
        sleeper="woollybear",
        wrapping="linen_nest",
        magic="dew_blessing",
        nights=1,
        finder_name="Fern",
        finder_species="Rabbit",
        doubter_name="Twig",
        doubter_species="Mouse",
        elder_name="Slow Tortoise",
        elder_species="Tortoise",
        finder_trait="patient",
    ),
]


ASP_RULES = r"""
warm_enough(S,W) :- sleeper(S), wrapping(W), need_warmth(S,N), warmth(W,T), T >= N.
wait_enough(S,Nt) :- sleeper(S), nights(Nt), need_wait(S,N), Nt >= N.
magic_ok(P,M) :- place(P), magic(M), needs(M,moonlit), moonlit(P).
magic_ok(P,M) :- place(P), magic(M), needs(M,dewy), dewy(P).
magic_ok(P,M) :- place(P), magic(M), needs(M,none).

gentle_magic(M) :- magic(M), sense(M,S), sense_min(Min), S >= Min.
valid(P,S,W,M,Nt) :- place(P), sleeper(S), wrapping(W), magic(M), nights(Nt),
                     breathable(W), warm_enough(S,W), gentle_magic(M),
                     magic_ok(P,M), wait_enough(S,Nt).

outcome(transformed) :- chosen_place(P), chosen_sleeper(S), chosen_wrapping(W),
                        chosen_magic(M), chosen_nights(Nt), valid(P,S,W,M,Nt).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.moonlit:
            lines.append(asp.fact("moonlit", pid))
        if place.dewy:
            lines.append(asp.fact("dewy", pid))
    for sid, sleeper in SLEEPERS.items():
        lines.append(asp.fact("sleeper", sid))
        lines.append(asp.fact("need_warmth", sid, sleeper.need_warmth))
        lines.append(asp.fact("need_wait", sid, sleeper.need_wait))
    for wid, wrapping in WRAPPINGS.items():
        lines.append(asp.fact("wrapping", wid))
        lines.append(asp.fact("warmth", wid, wrapping.warmth))
        if wrapping.breathable:
            lines.append(asp.fact("breathable", wid))
    for mid, magic in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("sense", mid, magic.sense))
        lines.append(asp.fact("needs", mid, magic.needs))
    for nights in (1, 2):
        lines.append(asp.fact("nights", nights))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_sleeper", params.sleeper),
        asp.fact("chosen_wrapping", params.wrapping),
        asp.fact("chosen_magic", params.magic),
        asp.fact("chosen_nights", params.nights),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "still"


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.sleeper not in SLEEPERS or params.wrapping not in WRAPPINGS or params.magic not in MAGICS:
        return "still"
    ok = transform_possible(
        PLACES[params.place],
        SLEEPERS[params.sleeper],
        WRAPPINGS[params.wrapping],
        MAGICS[params.magic],
        params.nights,
    )
    return "transformed" if ok else "still"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: animals find a still bundle and gentle magic reveals transformation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sleeper", choices=SLEEPERS)
    ap.add_argument("--wrapping", choices=WRAPPINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--nights", type=int, choices=[1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: set[str]) -> str:
    pool = [n for n in GIRL_NAMES + BOY_NAMES if n not in avoid]
    return rng.choice(pool)


def _pick_species(rng: random.Random, pool: list[str], avoid: set[str]) -> str:
    choices = [p for p in pool if p not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sleeper and args.wrapping and args.magic and args.nights is not None:
        place = PLACES[args.place]
        sleeper = SLEEPERS[args.sleeper]
        wrapping = WRAPPINGS[args.wrapping]
        magic = MAGICS[args.magic]
        if not transform_possible(place, sleeper, wrapping, magic, args.nights):
            raise StoryError(explain_rejection(place, sleeper, wrapping, magic, args.nights))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sleeper is None or combo[1] == args.sleeper)
        and (args.wrapping is None or combo[2] == args.wrapping)
        and (args.magic is None or combo[3] == args.magic)
        and (args.nights is None or combo[4] == args.nights)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sleeper_id, wrapping_id, magic_id, nights = rng.choice(sorted(combos))
    finder_name = _pick_name(rng, set())
    doubter_name = _pick_name(rng, {finder_name})
    elder_name = rng.choice(["Old Owl", "Aunt Badger", "Slow Tortoise"])
    finder_species = _pick_species(rng, FINDER_SPECIES, set())
    doubter_species = _pick_species(rng, FINDER_SPECIES, {finder_species})
    elder_species = "Owl" if "Owl" in elder_name else ("Badger" if "Badger" in elder_name else "Tortoise")
    finder_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        sleeper=sleeper_id,
        wrapping=wrapping_id,
        magic=magic_id,
        nights=nights,
        finder_name=finder_name,
        finder_species=finder_species,
        doubter_name=doubter_name,
        doubter_species=doubter_species,
        elder_name=elder_name,
        elder_species=elder_species,
        finder_trait=finder_trait,
    )


def generate(params: StoryParams) -> StorySample:
    missing = []
    if params.place not in PLACES:
        missing.append(f"place={params.place}")
    if params.sleeper not in SLEEPERS:
        missing.append(f"sleeper={params.sleeper}")
    if params.wrapping not in WRAPPINGS:
        missing.append(f"wrapping={params.wrapping}")
    if params.magic not in MAGICS:
        missing.append(f"magic={params.magic}")
    if params.nights not in (1, 2):
        missing.append(f"nights={params.nights}")
    if missing:
        raise StoryError("(Invalid params: " + ", ".join(missing) + ")")

    place = PLACES[params.place]
    sleeper = SLEEPERS[params.sleeper]
    wrapping = WRAPPINGS[params.wrapping]
    magic = MAGICS[params.magic]

    if not transform_possible(place, sleeper, wrapping, magic, params.nights):
        raise StoryError(explain_rejection(place, sleeper, wrapping, magic, params.nights))

    world = tell(
        place=place,
        sleeper_cfg=sleeper,
        wrapping_cfg=wrapping,
        magic_cfg=magic,
        nights=params.nights,
        finder_name=params.finder_name,
        finder_species=params.finder_species,
        doubter_name=params.doubter_name,
        doubter_species=params.doubter_species,
        elder_name=params.elder_name,
        elder_species=params.elder_species,
        finder_trait=params.finder_trait,
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
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_params.seed = 0
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sleeper, wrapping, magic, nights) combos:\n")
        for place, sleeper, wrapping, magic, nights in combos:
            print(f"  {place:11} {sleeper:11} {wrapping:14} {magic:13} {nights}")
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
            header = f"### {p.finder_name} & {p.doubter_name}: {p.sleeper} in {p.wrapping} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
