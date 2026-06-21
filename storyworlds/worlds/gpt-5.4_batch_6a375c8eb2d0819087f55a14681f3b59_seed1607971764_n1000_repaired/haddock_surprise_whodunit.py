#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/haddock_surprise_whodunit.py
=======================================================

A standalone story world for a child-facing whodunit about a missing haddock
surprise. A child helps prepare a secret supper, the dish vanishes, clues point
in the wrong direction for a moment, and the ending reveals that a careful
helper hid it to keep the surprise safe.

The world model tracks a few physical meters (cooling, hidden, danger, crumbs,
pawprints, feathers, raindrops) and emotional memes (pride, worry, suspicion,
relief, delight). The prose is driven by that state rather than by simple slot
swapping.

Run it
------
    python storyworlds/worlds/gpt-5.4/haddock_surprise_whodunit.py
    python storyworlds/worlds/gpt-5.4/haddock_surprise_whodunit.py --setting cottage --threat gull
    python storyworlds/worlds/gpt-5.4/haddock_surprise_whodunit.py --hideout bench
    python storyworlds/worlds/gpt-5.4/haddock_surprise_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/haddock_surprise_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/haddock_surprise_whodunit.py --verify
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
    access: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "sister", "grandmother"}
        male = {"boy", "father", "uncle", "man", "brother", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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


@dataclass
class Setting:
    id: str
    place: str
    room: str
    window_text: str
    outside_threats: set[str] = field(default_factory=set)
    hideouts: set[str] = field(default_factory=set)
    opening_image: str = ""
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
class SurpriseDish:
    id: str
    label: str
    phrase: str
    cooling_spot: str
    reveal_text: str
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
class Threat:
    id: str
    label: str
    sign: str
    clue: str
    danger_text: str
    protect_tags: set[str] = field(default_factory=set)
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
class Hideout:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    access_tags: set[str] = field(default_factory=set)
    clue_text: str = ""
    ending_image: str = ""
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
class HelperRole:
    id: str
    label: str
    type: str
    relation: str
    access_tags: set[str] = field(default_factory=set)
    speech: str = ""
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
    setting: Setting
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
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
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


def _r_window_danger(world: World) -> list[str]:
    out: list[str] = []
    dish = world.get("dish")
    threat = world.get("threat")
    if dish.meters["cooling"] < THRESHOLD or dish.meters["hidden"] >= THRESHOLD:
        return out
    if threat.meters["present"] < THRESHOLD:
        return out
    sig = ("window_danger", world.facts.get("threat_id", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dish.meters["danger"] += 1
    child = world.get("child")
    child.memes["worry"] += 1
    out.append("__danger__")
    return out


def _r_move_hides(world: World) -> list[str]:
    out: list[str] = []
    dish = world.get("dish")
    helper = world.get("helper")
    if dish.meters["carried"] < THRESHOLD or dish.meters["hidden"] >= THRESHOLD:
        return out
    sig = ("hide_dish", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dish.meters["hidden"] += 1
    dish.meters["cooling"] = 0.0
    helper.meters["smelled_of_haddock"] += 1
    out.append("__hidden__")
    return out


def _r_cat_pawprints(world: World) -> list[str]:
    out: list[str] = []
    threat = world.get("threat")
    if world.facts.get("threat_id") != "cat" or threat.meters["present"] < THRESHOLD:
        return out
    sig = ("cat_clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("windowsill").meters["pawprints"] += 1
    out.append("__clue__")
    return out


def _r_gull_feathers(world: World) -> list[str]:
    out: list[str] = []
    threat = world.get("threat")
    if world.facts.get("threat_id") != "gull" or threat.meters["present"] < THRESHOLD:
        return out
    sig = ("gull_clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("windowsill").meters["feathers"] += 1
    out.append("__clue__")
    return out


def _r_rain_drops(world: World) -> list[str]:
    out: list[str] = []
    threat = world.get("threat")
    if world.facts.get("threat_id") != "rain" or threat.meters["present"] < THRESHOLD:
        return out
    sig = ("rain_clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("windowsill").meters["raindrops"] += 1
    out.append("__clue__")
    return out


CAUSAL_RULES = [
    Rule(name="window_danger", tag="physical", apply=_r_window_danger),
    Rule(name="hide_dish", tag="physical", apply=_r_move_hides),
    Rule(name="cat_pawprints", tag="physical", apply=_r_cat_pawprints),
    Rule(name="gull_feathers", tag="physical", apply=_r_gull_feathers),
    Rule(name="rain_drops", tag="physical", apply=_r_rain_drops),
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


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="the little harbor cottage",
        room="the kitchen",
        window_text="the open kitchen window faced the pier",
        outside_threats={"gull", "rain", "cat"},
        hideouts={"pantry", "icebox", "cupboard"},
        opening_image="The harbor smelled of salt, and the blue cottage windows blinked in the morning light.",
        tags={"harbor", "home"},
    ),
    "boathouse": Setting(
        id="boathouse",
        place="the warm boathouse kitchen",
        room="the kitchen",
        window_text="the wide boathouse window looked straight at the water",
        outside_threats={"gull", "rain"},
        hideouts={"icebox", "cupboard"},
        opening_image="Ropes hung drying by the door, and little waves tapped against the posts outside.",
        tags={"harbor", "boats"},
    ),
    "cafe": Setting(
        id="cafe",
        place="the market café kitchen",
        room="the kitchen",
        window_text="the back window opened over the alley",
        outside_threats={"cat", "rain"},
        hideouts={"pantry", "cupboard"},
        opening_image="The café smelled of bread and tea, and the floorboards whispered under quick feet.",
        tags={"market", "cafe"},
    ),
}

DISHES = {
    "pie": SurpriseDish(
        id="pie",
        label="haddock pie",
        phrase="a golden haddock pie",
        cooling_spot="the windowsill",
        reveal_text="the flaky crust still shone like a small gold roof",
        tags={"pie", "haddock"},
    ),
    "cakes": SurpriseDish(
        id="cakes",
        label="haddock cakes",
        phrase="a plate of crisp haddock cakes",
        cooling_spot="the windowsill",
        reveal_text="the little round cakes still looked neat and warm",
        tags={"cakes", "haddock"},
    ),
    "parcel": SurpriseDish(
        id="parcel",
        label="haddock parcel",
        phrase="a haddock parcel wrapped in pastry",
        cooling_spot="the windowsill",
        reveal_text="the pastry still held its tidy folded corners",
        tags={"parcel", "haddock"},
    ),
}

THREATS = {
    "gull": Threat(
        id="gull",
        label="a greedy seagull",
        sign="a sharp cry outside the window",
        clue="a white feather on the sill",
        danger_text="A gull with a bold yellow beak kept hopping along the rail outside.",
        protect_tags={"covered", "closed", "high"},
        tags={"gull", "bird"},
    ),
    "cat": Threat(
        id="cat",
        label="the stripy harbor cat",
        sign="a soft thump under the window",
        clue="dusty pawprints near the sill",
        danger_text="The stripy harbor cat was winding around the doorstep and staring up.",
        protect_tags={"closed", "high"},
        tags={"cat", "animal"},
    ),
    "rain": Threat(
        id="rain",
        label="a sudden rain shower",
        sign="a patter on the glass",
        clue="a string of raindrops under the sill",
        danger_text="Dark clouds rolled in, and damp drops began to tap at the window frame.",
        protect_tags={"closed", "inside"},
        tags={"rain", "weather"},
    ),
}

HIDEOUTS = {
    "pantry": Hideout(
        id="pantry",
        label="pantry",
        phrase="the cool pantry",
        protects={"closed", "inside"},
        access_tags={"pantry_key"},
        clue_text="A tiny dusting of flour lay by the pantry latch.",
        ending_image="When the pantry door opened, the secret supper waited there in the cool dark.",
        tags={"pantry"},
    ),
    "icebox": Hideout(
        id="icebox",
        label="icebox",
        phrase="the blue icebox",
        protects={"closed", "inside"},
        access_tags={"icebox_key"},
        clue_text="A silver handle on the icebox wore a cloudy thumb mark.",
        ending_image="Inside the icebox, the surprise sat safe and chilly on its tray.",
        tags={"icebox"},
    ),
    "cupboard": Hideout(
        id="cupboard",
        label="high cupboard",
        phrase="the high cupboard above the sink",
        protects={"closed", "high"},
        access_tags={"stool"},
        clue_text="A little wooden stool stood crooked under the cupboard.",
        ending_image="Up in the cupboard, the surprise rested above curious paws and pecking beaks.",
        tags={"cupboard"},
    ),
    "bench": Hideout(
        id="bench",
        label="bench",
        phrase="the bench by the door",
        protects=set(),
        access_tags=set(),
        clue_text="The bench by the door had nothing on it but a folded cloth.",
        ending_image="The bench stayed empty, proving it had never been a safe hiding place at all.",
        tags={"bench"},
    ),
}

HELPERS = {
    "aunt": HelperRole(
        id="aunt",
        label="Aunt May",
        type="aunt",
        relation="aunt",
        access_tags={"pantry_key", "icebox_key"},
        speech="I had to save our surprise before it was spoiled.",
        tags={"family"},
    ),
    "grandpa": HelperRole(
        id="grandpa",
        label="Grandpa Ben",
        type="grandfather",
        relation="grandpa",
        access_tags={"stool", "icebox_key"},
        speech="A careful cook never lets the sea or the cat steal supper.",
        tags={"family"},
    ),
    "sister": HelperRole(
        id="sister",
        label="Nell",
        type="sister",
        relation="older sister",
        access_tags={"stool", "pantry_key"},
        speech="I wanted the surprise to stay secret and safe.",
        tags={"family"},
    ),
    "neighbor": HelperRole(
        id="neighbor",
        label="Mr. Pike",
        type="man",
        relation="neighbor",
        access_tags={"pantry_key"},
        speech="I saw the danger first, so I tucked it away.",
        tags={"neighbor"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Ruby", "Poppy", "Nora", "Etta", "Wren"]
BOY_NAMES = ["Otis", "Finn", "Eli", "Milo", "Jude", "Theo", "Benji", "Arlo"]
TRAITS = ["careful", "curious", "bright", "patient", "eager", "thoughtful"]


def hideout_protects(threat: Threat, hideout: Hideout) -> bool:
    return bool(threat.protect_tags & hideout.protects)


def helper_can_use(helper: HelperRole, hideout: Hideout) -> bool:
    return hideout.access_tags <= helper.access_tags


def setting_allows(setting: Setting, threat: Threat, hideout: Hideout) -> bool:
    return threat.id in setting.outside_threats and hideout.id in setting.hideouts


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for threat_id, threat in THREATS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                for helper_id, helper in HELPERS.items():
                    if (
                        setting_allows(setting, threat, hideout)
                        and hideout_protects(threat, hideout)
                        and helper_can_use(helper, hideout)
                    ):
                        combos.append((setting_id, threat_id, hideout_id, helper_id))
    return sorted(combos)


def explain_rejection(setting: Setting, threat: Threat, hideout: Hideout, helper: HelperRole) -> str:
    if threat.id not in setting.outside_threats:
        return (
            f"(No story: {threat.label} is not a natural danger at {setting.place}, "
            f"so there is no honest mystery about moving the supper.)"
        )
    if hideout.id not in setting.hideouts:
        return (
            f"(No story: {hideout.phrase} does not belong in {setting.place}, "
            f"so nobody could sensibly tuck the surprise there.)"
        )
    if not hideout_protects(threat, hideout):
        return (
            f"(No story: {hideout.phrase} does not really protect the haddock surprise "
            f"from {threat.label}. The hiding place must actually solve the danger.)"
        )
    if not helper_can_use(helper, hideout):
        return (
            f"(No story: {helper.label} cannot reasonably use {hideout.phrase}. "
            f"The helper needs the right access, such as a key or a stool.)"
        )
    return "(No story: that combination is not reasonable here.)"


def suspect_line(threat_id: str) -> str:
    return {
        "gull": "Maybe a seagull had flown off with supper.",
        "cat": "Maybe the harbor cat had sneaked in for a fishy snack.",
        "rain": "Maybe the rain had spoiled the surprise and someone had rushed it away.",
    }[threat_id]


def clue_reading(world: World) -> str:
    sill = world.get("windowsill")
    bits: list[str] = []
    if sill.meters["feathers"] >= THRESHOLD:
        bits.append("a white feather on the sill")
    if sill.meters["pawprints"] >= THRESHOLD:
        bits.append("dusty pawprints by the sill")
    if sill.meters["raindrops"] >= THRESHOLD:
        bits.append("fresh raindrops under the sill")
    if not bits:
        return "The sill looked strangely neat."
    if len(bits) == 1:
        return f"There was {bits[0]}."
    return "There were " + ", and ".join([", ".join(bits[:-1]), bits[-1]]) + "."


def predict_danger(setting: Setting, threat: Threat, hideout: Hideout) -> dict:
    return {
        "at_window": threat.id in setting.outside_threats,
        "safe_if_hidden": hideout_protects(threat, hideout),
    }


def introduce(world: World, child: Entity, host: Entity, dish_cfg: SurpriseDish) -> None:
    child.memes["pride"] += 1
    world.say(world.setting.opening_image)
    world.say(
        f"In {world.setting.room}, {child.id} helped {host.label_word} brush butter over "
        f"{dish_cfg.phrase}. Tonight it was meant to be a Surprise for a dear guest."
    )
    world.say(
        f'"No peeking, no telling," {host.label_word.capitalize()} whispered. '
        f'"We want everyone to gasp when they see the {dish_cfg.label}."'
    )


def cool_dish(world: World, child: Entity, dish_cfg: SurpriseDish, threat: Threat) -> None:
    dish = world.get("dish")
    threat_ent = world.get("threat")
    dish.meters["cooling"] = 1.0
    threat_ent.meters["present"] = 1.0
    world.say(
        f"They set the {dish_cfg.label} on {dish_cfg.cooling_spot} because the crust was still singing with heat. "
        f"{world.setting.window_text}, and soon {threat.danger_text}"
    )
    propagate(world, narrate=False)


def vanish(world: World, child: Entity, dish_cfg: SurpriseDish) -> None:
    child.memes["worry"] += 1
    world.say(
        f"When {child.id} came back with plates, {dish_cfg.phrase} was gone."
    )
    world.say(
        f"{child.id} stopped in the middle of the floor. This was not just missing supper. "
        f"It felt like the beginning of a tiny whodunit."
    )


def inspect_sill(world: World, child: Entity, threat: Threat) -> None:
    child.memes["suspicion"] += 1
    world.say(
        f'{child.id} looked at the sill like a little detective. "{threat.sign.capitalize()}... and now no supper?"'
    )
    world.say(clue_reading(world))
    world.say(suspect_line(world.facts["threat_id"]))


def search(world: World, child: Entity, helper: Entity, hideout: Hideout) -> None:
    child.memes["suspicion"] += 1
    helper.meters["crumbs"] += 1
    world.say(
        f"Then {child.id} noticed a softer clue: a buttery smell on {helper.label}'s sleeve and "
        f"a crumb no bigger than a star near {hideout.label}."
    )
    world.say(
        f"{hideout.clue_text} That clue did not look like stealing. It looked like carrying."
    )


def reveal(world: World, child: Entity, helper: Entity, dish_cfg: SurpriseDish, hideout: Hideout) -> None:
    child.memes["relief"] += 1
    child.memes["delight"] += 1
    helper.memes["care"] += 1
    world.say(
        f'"{helper.label}!" cried {child.id}. "Did you take the {dish_cfg.label}?"'
    )
    world.say(
        f'{helper.label} smiled and held a finger to {helper.pronoun("possessive")} lips. '
        f'"I moved it, yes," {helper.pronoun()} said. "{HELPERS[world.facts["helper_id"]].speech}"'
    )
    world.say(
        f"{hideout.ending_image} {dish_cfg.reveal_text}, and not a single bite was missing."
    )


def ending(world: World, child: Entity, host: Entity, dish_cfg: SurpriseDish) -> None:
    child.memes["joy"] += 1
    host.memes["joy"] += 1
    world.say(
        f"At supper, the covered dish was carried out at just the right moment. The guest blinked, smiled wide, "
        f"and laughed in happy surprise at the secret {dish_cfg.label}."
    )
    world.say(
        f"{child.id} felt proud instead of worried now. In this whodunit, the answer was not a thief at all, "
        f"but a careful helper guarding the Surprise."
    )


def tell(
    setting: Setting,
    dish_cfg: SurpriseDish,
    threat: Threat,
    hideout: Hideout,
    helper_cfg: HelperRole,
    child_name: str = "Mina",
    child_gender: str = "girl",
    host_type: str = "grandmother",
    child_trait: str = "curious",
) -> World:
    world = World(setting=setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            traits=[child_trait],
            role="detective",
            attrs={},
        )
    )
    host = world.add(
        Entity(
            id="Host",
            kind="character",
            type=host_type,
            label="the cook",
            role="host",
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            role="helper",
            attrs={"relation": helper_cfg.relation},
            access=set(helper_cfg.access_tags),
            tags=set(helper_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="dish",
            kind="thing",
            type="food",
            label=dish_cfg.label,
            role="surprise",
            attrs={},
            tags=set(dish_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="threat",
            kind="thing",
            type="threat",
            label=threat.label,
            role="threat",
            attrs={},
            tags=set(threat.tags),
        )
    )
    world.add(
        Entity(
            id="windowsill",
            kind="thing",
            type="place",
            label="windowsill",
            role="clue_spot",
            attrs={},
        )
    )

    world.facts.update(
        setting_id=setting.id,
        dish_id=dish_cfg.id,
        threat_id=threat.id,
        hideout_id=hideout.id,
        helper_id=helper_cfg.id,
        child_name=child_name,
        host_type=host_type,
        child_trait=child_trait,
        wrong_suspect=threat.label,
    )

    introduce(world, child, host, dish_cfg)
    world.para()
    cool_dish(world, child, dish_cfg, threat)
    dish = world.get("dish")
    dish.meters["carried"] += 1
    propagate(world, narrate=False)
    vanish(world, child, dish_cfg)
    inspect_sill(world, child, threat)
    world.para()
    search(world, child, helper, hideout)
    reveal(world, child, helper, dish_cfg, hideout)
    world.para()
    ending(world, child, host, dish_cfg)

    world.facts.update(
        child=child,
        host=host,
        helper=helper,
        dish_cfg=dish_cfg,
        threat_cfg=threat,
        hideout_cfg=hideout,
        dish_hidden=dish.meters["hidden"] >= THRESHOLD,
        dish_safe=(dish.meters["hidden"] >= THRESHOLD and dish.meters["danger"] >= THRESHOLD),
        sill_clues={
            "pawprints": world.get("windowsill").meters["pawprints"] >= THRESHOLD,
            "feathers": world.get("windowsill").meters["feathers"] >= THRESHOLD,
            "raindrops": world.get("windowsill").meters["raindrops"] >= THRESHOLD,
        },
    )
    return world


KNOWLEDGE = {
    "haddock": [
        (
            "What is haddock?",
            "Haddock is a kind of fish from the sea. People often cook it in pies, cakes, or other suppers."
        )
    ],
    "gull": [
        (
            "Why might a gull be a problem near food?",
            "Gulls are bold birds, and they will swoop at food if they think they can grab it. That is why cooks keep food covered or indoors."
        )
    ],
    "cat": [
        (
            "Why do cats sniff around kitchens?",
            "Cats have strong noses and often come to places where they smell fish or meat. A careful cook keeps supper where paws cannot reach it."
        )
    ],
    "rain": [
        (
            "Why should warm food not sit in the rain?",
            "Rain can make crusts soggy and spoil the look of a dish. Keeping food dry helps it stay tasty and neat."
        )
    ],
    "pantry": [
        (
            "What is a pantry?",
            "A pantry is a cupboard or little room where food is kept. It is often cooler and safer than an open windowsill."
        )
    ],
    "icebox": [
        (
            "What is an icebox?",
            "An icebox is an old cold cupboard used to keep food cool. Before modern fridges, people used iceboxes to help food stay fresh."
        )
    ],
    "cupboard": [
        (
            "Why put food in a high cupboard?",
            "A high cupboard keeps food above small hands, paws, and pecking beaks. Height can be part of staying safe."
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you work out what happened. A feather, a pawprint, or a crumb can all be clues."
        )
    ],
    "surprise": [
        (
            "What makes a surprise fun?",
            "A surprise is fun when it is kept secret until the right moment. Then everyone gets to feel a happy jolt all at once."
        )
    ],
}
KNOWLEDGE_ORDER = ["haddock", "gull", "cat", "rain", "pantry", "icebox", "cupboard", "clue", "surprise"]


@dataclass
class StoryParams:
    setting: str
    dish: str
    threat: str
    hideout: str
    helper: str
    child_name: str
    child_gender: str
    host_type: str
    child_trait: str
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
    child = f["child"]
    dish = f["dish_cfg"]
    threat = f["threat_cfg"]
    helper = f["helper"]
    hideout = f["hideout_cfg"]
    return [
        f'Write a short child-friendly whodunit that includes the word "haddock" and ends with a happy Surprise.',
        f"Tell a tiny mystery where {child.id} helps prepare a {dish.label}, the dish goes missing, and clues first point toward {threat.label} before revealing that {helper.label} hid it in {hideout.phrase}.",
        f"Write a gentle detective story for ages 3 to 5 set in a kitchen, with a missing supper, small clues, and the final reveal that the missing thing was protected rather than stolen.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    host = f["host"]
    helper = f["helper"]
    dish = f["dish_cfg"]
    threat = f["threat_cfg"]
    hideout = f["hideout_cfg"]
    sill = f["sill_clues"]

    clue_answer = []
    if sill["feathers"]:
        clue_answer.append("a white feather")
    if sill["pawprints"]:
        clue_answer.append("dusty pawprints")
    if sill["raindrops"]:
        clue_answer.append("fresh raindrops")
    clue_text = ", ".join(clue_answer) if clue_answer else "no clear clue"

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little kitchen detective, and the grown-ups helping prepare a secret {dish.label}. The mystery starts when the supper vanishes before the Surprise."
        ),
        (
            f"Why did {child.id} think something was wrong?",
            f"{child.id} came back and saw that the {dish.label} was missing from the windowsill. Because it had been there a moment before, the empty place felt like a real mystery."
        ),
        (
            "What clue did the child notice first?",
            f"{child.id} noticed {clue_text} near the sill. That made {child.pronoun('object')} suspect {threat.label} before finding the truer clue."
        ),
        (
            f"Who really moved the {dish.label}, and why?",
            f"{helper.label} moved it to {hideout.phrase}. {helper.pronoun().capitalize()} was trying to protect the supper from {threat.label}, not steal it."
        ),
        (
            "How was the mystery solved?",
            f"The child found a buttery smell and a tiny crumb near the hiding place, which showed that someone had carried the dish carefully. Then the helper admitted moving it, and the safe supper could still be part of the Surprise."
        ),
        (
            "How did the story end?",
            f"It ended happily when the hidden {dish.label} was brought out at supper. The ending proves the dish stayed safe and the Surprise worked just as everyone hoped."
        ),
    ]
    if world.get("dish").meters["danger"] >= THRESHOLD:
        qa.append(
            (
                f"Why was moving the {dish.label} a good idea?",
                f"It was a good idea because the dish was cooling at an open window while {threat.label} was nearby. Moving it to {hideout.phrase} kept the supper safe for the big reveal."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"haddock", "clue", "surprise"}
    threat = world.facts["threat_cfg"]
    hideout = world.facts["hideout_cfg"]
    if threat.id in KNOWLEDGE:
        tags.add(threat.id)
    if hideout.id in KNOWLEDGE:
        tags.add(hideout.id)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.access:
            bits.append(f"access={sorted(ent.access)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cottage",
        dish="pie",
        threat="gull",
        hideout="cupboard",
        helper="grandpa",
        child_name="Mina",
        child_gender="girl",
        host_type="grandmother",
        child_trait="curious",
        seed=101,
    ),
    StoryParams(
        setting="cafe",
        dish="cakes",
        threat="cat",
        hideout="pantry",
        helper="aunt",
        child_name="Otis",
        child_gender="boy",
        host_type="mother",
        child_trait="bright",
        seed=102,
    ),
    StoryParams(
        setting="boathouse",
        dish="parcel",
        threat="rain",
        hideout="icebox",
        helper="grandpa",
        child_name="Ruby",
        child_gender="girl",
        host_type="father",
        child_trait="thoughtful",
        seed=103,
    ),
    StoryParams(
        setting="cottage",
        dish="cakes",
        threat="rain",
        hideout="pantry",
        helper="neighbor",
        child_name="Finn",
        child_gender="boy",
        host_type="grandmother",
        child_trait="patient",
        seed=104,
    ),
    StoryParams(
        setting="cottage",
        dish="parcel",
        threat="cat",
        hideout="cupboard",
        helper="sister",
        child_name="Lila",
        child_gender="girl",
        host_type="mother",
        child_trait="eager",
        seed=105,
    ),
]


ASP_RULES = r"""
possible(S,T,H,He) :- setting(S), threat(T), hideout(H), helper(He),
                      outside_risk(S,T), has_hideout(S,H).
valid(S,T,H,He) :- possible(S,T,H,He),
                   protect_from(H,T),
                   can_use(He,H).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for threat_id in sorted(setting.outside_threats):
            lines.append(asp.fact("outside_risk", setting_id, threat_id))
        for hideout_id in sorted(setting.hideouts):
            lines.append(asp.fact("has_hideout", setting_id, hideout_id))
    for threat_id in THREATS:
        lines.append(asp.fact("threat", threat_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        for protect in sorted(hideout.protects):
            lines.append(asp.fact("hideout_tag", hideout_id, protect))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for access in sorted(helper.access_tags):
            lines.append(asp.fact("helper_tag", helper_id, access))

    for hideout_id, hideout in HIDEOUTS.items():
        for threat_id, threat in THREATS.items():
            if hideout_protects(threat, hideout):
                lines.append(asp.fact("protect_from", hideout_id, threat_id))
    for helper_id, helper in HELPERS.items():
        for hideout_id, hideout in HIDEOUTS.items():
            if helper_can_use(helper, hideout):
                lines.append(asp.fact("can_use", helper_id, hideout_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Child-friendly whodunit: the case of the missing haddock surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--host-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.threat and args.hideout and args.helper:
        setting = SETTINGS[args.setting]
        threat = THREATS[args.threat]
        hideout = HIDEOUTS[args.hideout]
        helper = HELPERS[args.helper]
        if not (
            setting_allows(setting, threat, hideout)
            and hideout_protects(threat, hideout)
            and helper_can_use(helper, hideout)
        ):
            raise StoryError(explain_rejection(setting, threat, hideout, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.threat is None or combo[1] == args.threat)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        if args.setting and args.threat and args.hideout and args.helper:
            raise StoryError(
                explain_rejection(
                    SETTINGS[args.setting],
                    THREATS[args.threat],
                    HIDEOUTS[args.hideout],
                    HELPERS[args.helper],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, threat_id, hideout_id, helper_id = rng.choice(combos)
    dish_id = args.dish or rng.choice(sorted(DISHES))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    host_type = args.host_type or rng.choice(["mother", "father", "grandmother", "grandfather"])
    child_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        dish=dish_id,
        threat=threat_id,
        hideout=hideout_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        host_type=host_type,
        child_trait=child_trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.dish not in DISHES:
        raise StoryError(f"(Unknown dish: {params.dish})")
    if params.threat not in THREATS:
        raise StoryError(f"(Unknown threat: {params.threat})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.setting]
    threat = THREATS[params.threat]
    hideout = HIDEOUTS[params.hideout]
    helper = HELPERS[params.helper]
    if not (
        setting_allows(setting, threat, hideout)
        and hideout_protects(threat, hideout)
        and helper_can_use(helper, hideout)
    ):
        raise StoryError(explain_rejection(setting, threat, hideout, helper))

    world = tell(
        setting=setting,
        dish_cfg=DISHES[params.dish],
        threat=threat,
        hideout=hideout,
        helper_cfg=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        host_type=params.host_type,
        child_trait=params.child_trait,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in [0, 1, 2, 7, 11]:
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED for seed {seed}: {err}")
            break
    else:
        print("OK: random seeded generation succeeded.")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, threat, hideout, helper) combos:\n")
        for setting_id, threat_id, hideout_id, helper_id in combos:
            print(f"  {setting_id:10} {threat_id:6} {hideout_id:8} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.dish} in {p.setting} "
                f"({p.threat} -> {p.hideout} by {p.helper})"
            )
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
