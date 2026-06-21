#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/geranium_magic_happy_ending_fairy_tale.py
====================================================================

A standalone story world for a tiny fairy-tale domain: a child cares for a
beloved geranium, a magical helper understands what the flower truly needs, and
the blossom recovers in time to cast a gentle happy light.

The world is built around a simple reasonableness constraint: a remedy must
match the plant's actual trouble. Water helps a thirsty geranium, sunlight
helps a shaded geranium, and warmth helps a chilled geranium. The prose comes
from the simulated state: droop, recovery, bloom, and glow.

Run it
------
    python storyworlds/worlds/gpt-5.4/geranium_magic_happy_ending_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/geranium_magic_happy_ending_fairy_tale.py --place tower --trouble shaded --remedy sun_mirror
    python storyworlds/worlds/gpt-5.4/geranium_magic_happy_ending_fairy_tale.py --trouble thirsty --remedy ember_cloak
    python storyworlds/worlds/gpt-5.4/geranium_magic_happy_ending_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/geranium_magic_happy_ending_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/geranium_magic_happy_ending_fairy_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "woman", "fairy", "queen"}
        male = {"boy", "father", "man", "elf", "wizard", "sprite"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    phrase: str
    goal: str
    evening_image: str
    troubles: set[str] = field(default_factory=set)
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
class Trouble:
    id: str
    label: str
    cause_line: str
    droop_line: str
    need: str
    threat_line: str
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
class Remedy:
    id: str
    label: str
    helper_id: str
    cures: str
    action_line: str
    qa_line: str
    magic_word: str
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
    type: str
    name: str
    entrance: str
    promise: str
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
class Color:
    id: str
    label: str
    bloom_line: str
    glow_line: str
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


def _r_need_makes_wilt(world: World) -> list[str]:
    plant = world.get("plant")
    out: list[str] = []
    for need in ("thirst", "shade", "cold"):
        if plant.meters[need] >= THRESHOLD:
            sig = ("wilt", need)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            plant.meters["wilt"] += 1
            world.get("hero").memes["worry"] += 1
            out.append("__wilt__")
    return out


def _r_cure_thirst(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["thirst"] < THRESHOLD or plant.meters["watered"] < THRESHOLD:
        return []
    sig = ("cure", "thirst")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["thirst"] = 0.0
    plant.meters["wilt"] = max(0.0, plant.meters["wilt"] - 1)
    plant.meters["bloom"] += 1
    world.get("hero").memes["hope"] += 1
    return ["__recover__"]


def _r_cure_shade(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["shade"] < THRESHOLD or plant.meters["sunlit"] < THRESHOLD:
        return []
    sig = ("cure", "shade")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["shade"] = 0.0
    plant.meters["wilt"] = max(0.0, plant.meters["wilt"] - 1)
    plant.meters["bloom"] += 1
    world.get("hero").memes["hope"] += 1
    return ["__recover__"]


def _r_cure_cold(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["cold"] < THRESHOLD or plant.meters["warmed"] < THRESHOLD:
        return []
    sig = ("cure", "cold")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["cold"] = 0.0
    plant.meters["wilt"] = max(0.0, plant.meters["wilt"] - 1)
    plant.meters["bloom"] += 1
    world.get("hero").memes["hope"] += 1
    return ["__recover__"]


def _r_bloom_glows(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["bloom"] < THRESHOLD or plant.meters["blessed"] < THRESHOLD:
        return []
    sig = ("glow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["glow"] += 1
    world.get("place").meters["light"] += 1
    world.get("hero").memes["joy"] += 1
    return ["__glow__"]


RULES = [
    Rule(name="need_makes_wilt", tag="physical", apply=_r_need_makes_wilt),
    Rule(name="cure_thirst", tag="physical", apply=_r_cure_thirst),
    Rule(name="cure_shade", tag="physical", apply=_r_cure_shade),
    Rule(name="cure_cold", tag="physical", apply=_r_cure_cold),
    Rule(name="bloom_glows", tag="magic", apply=_r_bloom_glows),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for sent in out:
            if not sent.startswith("__"):
                world.say(sent)
    return out


def remedy_matches(trouble: Trouble, remedy: Remedy) -> bool:
    return trouble.need == remedy.cures


def helper_matches(remedy: Remedy, helper: Helper) -> bool:
    return remedy.helper_id == helper.id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for trouble_id in sorted(place.troubles):
            trouble = TROUBLES[trouble_id]
            for remedy_id, remedy in REMEDIES.items():
                if not remedy_matches(trouble, remedy):
                    continue
                helper = HELPERS[remedy.helper_id]
                combos.append((place_id, trouble_id, remedy_id, helper.id))
    return combos


def predict_without_help(world: World) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    propagate(sim, narrate=False)
    return {
        "wilted": plant.meters["wilt"] >= THRESHOLD,
        "glow": plant.meters["glow"],
    }


def introduce(world: World, hero: Entity, plant: Entity, place: Place, color: Color) -> None:
    hero.memes["love"] += 1
    world.say(
        f"In {place.phrase}, a child named {hero.id} cared for a {color.label} geranium in a painted clay pot."
    )
    world.say(
        f"Every evening, {hero.pronoun()} set the flower where it could watch {place.goal}, as if it were part of the old tale of the house."
    )


def wish(world: World, hero: Entity, place: Place) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"That very night, the people there were waiting for {place.goal}, and {hero.id} wished the little geranium could shine in it."
    )


def trouble_comes(world: World, hero: Entity, plant: Entity, trouble: Trouble) -> None:
    plant.meters[trouble.need] += 1
    propagate(world, narrate=False)
    world.say(trouble.cause_line)
    world.say(
        f"By dusk, the geranium looked unhappy. {trouble.droop_line}"
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id} touched one leaf with careful fingers and felt a worried lump grow in {hero.pronoun('possessive')} throat."
        )


def call_for_help(world: World, hero: Entity, helper: Helper, trouble: Trouble) -> None:
    pred = predict_without_help(world)
    world.facts["predicted_wilted"] = pred["wilted"]
    world.say(
        f'"Please," whispered {hero.id}, "I only want my flower to be well."'
    )
    world.say(helper.entrance)
    if pred["wilted"]:
        world.say(
            f'"I can see the true trouble," {helper.name} said. "{trouble.threat_line} {helper.promise}"'
        )


def cast_remedy(world: World, hero: Entity, helper: Helper, remedy: Remedy, trouble: Trouble) -> None:
    plant = world.get("plant")
    helper_ent = world.get("helper")
    helper_ent.memes["kindness"] += 1
    if remedy.cures == "thirst":
        plant.meters["watered"] += 1
    elif remedy.cures == "shade":
        plant.meters["sunlit"] += 1
    elif remedy.cures == "cold":
        plant.meters["warmed"] += 1
    plant.meters["blessed"] += 1
    world.say(
        f'{helper.name} lifted {helper.pronoun("possessive")} hand and said, "{remedy.magic_word}." {remedy.action_line}'
    )
    before_bloom = plant.meters["bloom"]
    before_glow = plant.meters["glow"]
    propagate(world, narrate=False)
    if plant.meters["bloom"] > before_bloom:
        world.say(
            f"The geranium answered at once. {world.facts['color_cfg'].bloom_line}"
        )
    if plant.meters["glow"] > before_glow:
        world.say(
            world.facts["color_cfg"].glow_line
        )
    hero.memes["worry"] = 0.0


def ending(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"Soon {place.evening_image}"
    )
    world.say(
        f"{hero.id} smiled to see that the smallest living thing on the sill had helped make the whole evening gentle and bright."
    )


def tell(
    *,
    place: Place,
    trouble: Trouble,
    remedy: Remedy,
    helper: Helper,
    color: Color,
    hero_name: str,
    hero_gender: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper.type, role="helper", label=helper.name))
    plant = world.add(Entity(id="plant", type="flower", label="geranium"))
    world.add(Entity(id="place", type="place", label=place.label))

    world.facts["color_cfg"] = color
    introduce(world, hero, plant, place, color)
    wish(world, hero, place)

    world.para()
    trouble_comes(world, hero, plant, trouble)

    world.para()
    call_for_help(world, hero, helper, trouble)
    cast_remedy(world, hero, helper, remedy, trouble)

    world.para()
    ending(world, hero, place)

    world.facts.update(
        hero=hero,
        helper=helper_ent,
        helper_cfg=helper,
        plant=plant,
        place_cfg=place,
        trouble=trouble,
        remedy=remedy,
        color=color,
        healed=plant.meters["bloom"] >= THRESHOLD,
        glowing=plant.meters["glow"] >= THRESHOLD,
    )
    return world


PLACES = {
    "cottage": Place(
        id="cottage",
        label="cottage window",
        phrase="a mossy cottage at the edge of the wood",
        goal="the lane of returning neighbors",
        evening_image="the lane filled with soft steps, and the flower's glow lay over the stones like a little blessing",
        troubles={"thirsty", "shaded"},
        tags={"home", "window"},
    ),
    "tower": Place(
        id="tower",
        label="tower stair",
        phrase="a moon-washed tower above the village roofs",
        goal="the lantern stair winding down to supper",
        evening_image="the tower stair shone warmly, and no one missed a step on the winding way down",
        troubles={"shaded", "chilly"},
        tags={"tower", "stairs"},
    ),
    "bridge": Place(
        id="bridge",
        label="bridge house",
        phrase="a little bridge-house over a singing brook",
        goal="the bridge where families crossed home at dusk",
        evening_image="the bridge gleamed above the water, and every traveler crossed with an easy heart",
        troubles={"thirsty", "chilly"},
        tags={"bridge", "brook"},
    ),
}

TROUBLES = {
    "thirsty": Trouble(
        id="thirsty",
        label="thirsty",
        cause_line="All day the sun had sipped faster than the little pot could give.",
        droop_line="Its leaves hung low, and the earth around its roots had turned pale and crumbly.",
        need="thirst",
        threat_line="A thirsty root cannot hold up a brave blossom.",
        tags={"water", "plant"},
    ),
    "shaded": Trouble(
        id="shaded",
        label="shaded",
        cause_line="A gray cloud-bank and a crooked shutter had hidden the good light from it.",
        droop_line="Its buds stayed folded, as if they had forgotten how to wake.",
        need="shade",
        threat_line="A flower kept from light will keep its color tucked away.",
        tags={"sun", "plant"},
    ),
    "chilly": Trouble(
        id="chilly",
        label="chilly",
        cause_line="By afternoon, a sharp wind had crept through the cracks and nipped the window ledge.",
        droop_line="Its stem trembled, and even its brightest leaves looked pinched by the cold.",
        need="cold",
        threat_line="A cold stem cannot carry cheer to the top of its petals.",
        tags={"warmth", "plant"},
    ),
}

HELPERS = {
    "rain_sprite": Helper(
        id="rain_sprite",
        type="sprite",
        name="Pip the Rain-Sprite",
        entrance="A silver drop leapt from the window latch and became Pip the Rain-Sprite, no bigger than a robin.",
        promise="Give it a kind drink, and it will remember its own song.",
        tags={"water", "magic"},
    ),
    "sun_fairy": Helper(
        id="sun_fairy",
        type="fairy",
        name="Aurelia the Sun-Fairy",
        entrance="From the dim pane stepped Aurelia the Sun-Fairy, carrying a strip of sunshine like a ribbon.",
        promise="Turn its face to brightness, and it will open like a tiny royal fan.",
        tags={"sun", "magic"},
    ),
    "hearth_elf": Helper(
        id="hearth_elf",
        type="elf",
        name="Brindle the Hearth-Elf",
        entrance="Out of the hearth ash climbed Brindle the Hearth-Elf with warm sparks braided in his beard.",
        promise="Wrap it in gentle warmth, and its courage will return.",
        tags={"warmth", "magic"},
    ),
}

REMEDIES = {
    "dew_water": Remedy(
        id="dew_water",
        label="dew-water",
        helper_id="rain_sprite",
        cures="thirst",
        action_line="He tipped a shell of moonlit dew into the pot until the dry soil darkened and breathed again.",
        qa_line="Pip gave the geranium moonlit dew to drink.",
        magic_word="Drop by drop, wake and sip",
        tags={"water", "magic"},
    ),
    "sun_mirror": Remedy(
        id="sun_mirror",
        label="sun-mirror",
        helper_id="sun_fairy",
        cures="shade",
        action_line="She set a tiny gold mirror beside the flower, and a clean beam of light slipped over every folded bud.",
        qa_line="Aurelia brought a beam of sunlight with her little golden mirror.",
        magic_word="Bright gold, find the hidden red",
        tags={"sun", "magic"},
    ),
    "ember_cloak": Remedy(
        id="ember_cloak",
        label="ember-cloak",
        helper_id="hearth_elf",
        cures="cold",
        action_line="He laid a cloak of ember-warm wool around the pot, and the bitter draft curled away from it.",
        qa_line="Brindle wrapped the pot in an ember-warm cloak.",
        magic_word="Coals that glow, be kind and near",
        tags={"warmth", "magic"},
    ),
}

COLORS = {
    "red": Color(
        id="red",
        label="red",
        bloom_line="One by one, red petals lifted and spread until the whole geranium looked proud again.",
        glow_line="Then a rosy light kindled in the heart of the bloom, gentle as candle-shine and twice as merry.",
        tags={"red"},
    ),
    "pink": Color(
        id="pink",
        label="pink",
        bloom_line="Soft pink petals opened like small silk fans, fresh and brave after the drooping hour.",
        glow_line="Then a pink glow shimmered through the flower, like dawn learning to sing.",
        tags={"pink"},
    ),
    "coral": Color(
        id="coral",
        label="coral",
        bloom_line="Coral petals unfurled in a happy ring, and the plant stood up as if it had remembered a dance.",
        glow_line="Then a coral gleam spilled from the blossom and warmed the sill with fairy light.",
        tags={"coral"},
    ),
}

GIRL_NAMES = ["Elin", "Mara", "Nella", "Tessa", "Wren", "Lina", "Iris", "Poppy"]
BOY_NAMES = ["Robin", "Milo", "Alden", "Theo", "Jory", "Finn", "Bram", "Nico"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    remedy: str
    helper: str
    color: str
    hero_name: str
    hero_gender: str
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


KNOWLEDGE = {
    "geranium": [
        (
            "What is a geranium?",
            "A geranium is a garden flower with round clusters of blossoms and soft green leaves. People often grow it in pots or window boxes."
        )
    ],
    "water": [
        (
            "Why does a thirsty plant droop?",
            "Plants need water to keep their stems and leaves firm. When they do not get enough, they begin to droop and look tired."
        )
    ],
    "sun": [
        (
            "Why do many flowers need sunlight?",
            "Sunlight helps flowers make the food they need to grow. Without enough light, buds may stay closed and weak."
        )
    ],
    "warmth": [
        (
            "Why can cold weather hurt a potted flower?",
            "Cold can slow a flower down and make its stem and leaves weak. A small potted plant has less shelter than a plant deep in the ground."
        )
    ],
    "magic": [
        (
            "What is magic in a fairy tale?",
            "In a fairy tale, magic is a special power that can help hidden goodness appear. It usually works best when someone is kind, careful, and brave."
        )
    ],
}

KNOWLEDGE_ORDER = ["geranium", "water", "sun", "warmth", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place_cfg"]
    trouble = f["trouble"]
    remedy = f["remedy"]
    helper = f["helper_cfg"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the word "geranium" and ends happily.',
        f"Tell a gentle magical story where {hero.id} tries to help a geranium in {place.label}, and {helper.name} brings the right help for a {trouble.label} flower.",
        f"Write a fairy tale in which a child learns that careful kindness matters more than wishing alone, and the {remedy.label} helps the blossom shine by dusk.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    remedy = f["remedy"]
    helper_cfg = f["helper_cfg"]
    place = f["place_cfg"]
    plant = f["plant"]
    color = f["color"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child caring for a {color.label} geranium, and {helper_cfg.name}, the magical helper who comes when the flower is in trouble."
        ),
        (
            "What problem did the geranium have?",
            f"The geranium was {trouble.label}. {trouble.droop_line} That showed it needed {trouble.cures if hasattr(trouble, 'cures') else trouble.need}."
        ),
        (
            f"Why was {hero.id} worried?",
            f"{hero.id} wanted the flower to shine for {place.goal}, but the geranium was too unwell to do that. If nothing changed, it would stay droopy instead of glowing."
        ),
        (
            f"How did {helper_cfg.name} help the geranium?",
            f"{remedy.qa_line} That worked because the flower's real trouble was being {trouble.label}, so the magic matched what the plant needed."
        ),
    ]
    if plant.meters["glow"] >= THRESHOLD:
        qa.append(
            (
                "How did the story end?",
                f"The geranium bloomed and glowed, and its light helped {place.goal}. The ending is happy because the flower was healed and everyone could enjoy the gentle evening."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"geranium", "magic"}
    tags |= set(world.facts["trouble"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(r[0] for r in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="cottage",
        trouble="thirsty",
        remedy="dew_water",
        helper="rain_sprite",
        color="red",
        hero_name="Elin",
        hero_gender="girl",
    ),
    StoryParams(
        place="tower",
        trouble="shaded",
        remedy="sun_mirror",
        helper="sun_fairy",
        color="pink",
        hero_name="Robin",
        hero_gender="boy",
    ),
    StoryParams(
        place="bridge",
        trouble="chilly",
        remedy="ember_cloak",
        helper="hearth_elf",
        color="coral",
        hero_name="Mara",
        hero_gender="girl",
    ),
    StoryParams(
        place="bridge",
        trouble="thirsty",
        remedy="dew_water",
        helper="rain_sprite",
        color="pink",
        hero_name="Theo",
        hero_gender="boy",
    ),
]


def explain_rejection(place: Place, trouble: Trouble, remedy: Remedy, helper: Helper) -> str:
    if trouble.id not in place.troubles:
        return (
            f"(No story: {place.label} does not create the trouble '{trouble.id}' in this world. "
            f"Choose one of: {', '.join(sorted(place.troubles))}.)"
        )
    if not remedy_matches(trouble, remedy):
        return (
            f"(No story: {remedy.label} helps a flower that is {remedy.cures}, but this geranium is {trouble.label}. "
            f"The remedy must match the plant's real need.)"
        )
    if not helper_matches(remedy, helper):
        return (
            f"(No story: {helper.name} is not the helper who brings {remedy.label}. "
            f"Pick the matching magical helper.)"
        )
    return "(No story: these choices do not fit together.)"


ASP_RULES = r"""
trouble_possible(P,T) :- place(P), trouble(T), place_trouble(P,T).
matching(T,R) :- trouble(T), remedy(R), needs(T,N), cures(R,N).
matching_helper(R,H) :- remedy(R), helper(H), remedy_helper(R,H).

valid(P,T,R,H) :- trouble_possible(P,T), matching(T,R), matching_helper(R,H).

healed(P,T,R,H) :- valid(P,T,R,H).
glowing(P,T,R,H) :- healed(P,T,R,H), blesses(R).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tid in sorted(place.troubles):
            lines.append(asp.fact("place_trouble", pid, tid))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("needs", tid, trouble.need))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("cures", rid, remedy.cures))
        lines.append(asp.fact("remedy_helper", rid, remedy.helper_id))
        lines.append(asp.fact("blesses", rid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if a_set == p_set:
        print(f"OK: ASP gate matches valid_combos() ({len(a_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_set - p_set:
            print("  only in ASP:", sorted(a_set - p_set))
        if p_set - a_set:
            print("  only in Python:", sorted(p_set - a_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "geranium" not in sample.story.lower():
            raise StoryError("smoke test story did not render as expected")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story:
                raise StoryError("empty story")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break

    if rc == 0:
        print("OK: ordinary generation paths worked.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a child, a geranium, the right kind of magic, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--color", choices=COLORS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.trouble:
        place = PLACES[args.place]
        trouble = TROUBLES[args.trouble]
        if trouble.id not in place.troubles:
            remedy = REMEDIES[args.remedy] if args.remedy else next(iter(REMEDIES.values()))
            helper = HELPERS[args.helper] if args.helper else HELPERS[remedy.helper_id]
            raise StoryError(explain_rejection(place, trouble, remedy, helper))
    if args.trouble and args.remedy:
        trouble = TROUBLES[args.trouble]
        remedy = REMEDIES[args.remedy]
        helper = HELPERS[args.helper] if args.helper else HELPERS[remedy.helper_id]
        if not remedy_matches(trouble, remedy):
            place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
            raise StoryError(explain_rejection(place, trouble, remedy, helper))
    if args.remedy and args.helper:
        remedy = REMEDIES[args.remedy]
        helper = HELPERS[args.helper]
        if not helper_matches(remedy, helper):
            place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
            trouble = TROUBLES[args.trouble] if args.trouble else TROUBLES[next(iter(sorted(TROUBLES)))]
            raise StoryError(explain_rejection(place, trouble, remedy, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.remedy is None or combo[2] == args.remedy)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, trouble_id, remedy_id, helper_id = rng.choice(sorted(combos))
    color = args.color or rng.choice(sorted(COLORS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        hero_name = args.name
    else:
        hero_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

    return StoryParams(
        place=place_id,
        trouble=trouble_id,
        remedy=remedy_id,
        helper=helper_id,
        color=color,
        hero_name=hero_name,
        hero_gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.color not in COLORS:
        raise StoryError(f"(Unknown color: {params.color})")

    place = PLACES[params.place]
    trouble = TROUBLES[params.trouble]
    remedy = REMEDIES[params.remedy]
    helper = HELPERS[params.helper]
    color = COLORS[params.color]

    if trouble.id not in place.troubles or not remedy_matches(trouble, remedy) or not helper_matches(remedy, helper):
        raise StoryError(explain_rejection(place, trouble, remedy, helper))

    world = tell(
        place=place,
        trouble=trouble,
        remedy=remedy,
        helper=helper,
        color=color,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
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
        print(f"{len(combos)} valid (place, trouble, remedy, helper) combos:\n")
        for place, trouble, remedy, helper in combos:
            print(f"  {place:8} {trouble:8} {remedy:11} {helper}")
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.trouble} geranium at {p.place} with {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
