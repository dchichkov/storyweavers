#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/solar_wrinkle_herb_kindness_rhyming_story.py
=======================================================================

A standalone story world for a tiny rhyming tale about kindness, a solar light,
and a drooping herb. A child notices a worried grown-up, sees the wrinkle on
their brow, and kindly helps a potted herb get enough sun. The world model
tracks light, droop, charge, scent, and feelings; the prose is rendered from
that changing state in a simple rhyming style.

Run it
------
    python storyworlds/worlds/gpt-5.4/solar_wrinkle_herb_kindness_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/solar_wrinkle_herb_kindness_rhyming_story.py --place stoop --herb basil --fix share_mirror
    python storyworlds/worlds/gpt-5.4/solar_wrinkle_herb_kindness_rhyming_story.py --place shady_hall
    python storyworlds/worlds/gpt-5.4/solar_wrinkle_herb_kindness_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/solar_wrinkle_herb_kindness_rhyming_story.py --verify
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
CHARGE_MIN = 2
RECOVERY_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = False
    reflective: bool = False
    solar: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother", "aunt"}
        male = {"boy", "man", "grandfather", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    sun: int
    spare_sun_spot: bool
    outdoors: bool
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
class Herb:
    id: str
    label: str
    phrase: str
    need_sun: int
    smell: str
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
class SolarItem:
    id: str
    label: str
    phrase: str
    glow: str
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
    label: str
    power: int
    extra_charge: int
    need_spare_sun: bool
    need_outdoors: bool
    text: str
    qa_text: str
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


def _r_droop(world: World) -> list[str]:
    herb = world.get("herb")
    grown = world.get("grown")
    out: list[str] = []
    if herb.meters["sun"] >= herb.attrs["need_sun"]:
        return out
    sig = ("droop", herb.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    herb.meters["droop"] += 1
    herb.memes["need"] += 1
    grown.memes["worry"] += 1
    grown.meters["wrinkle"] += 1
    out.append("__droop__")
    return out


def _r_recover(world: World) -> list[str]:
    herb = world.get("herb")
    grown = world.get("grown")
    child = world.get("child")
    light = world.get("light")
    out: list[str] = []
    if herb.meters["sun"] < herb.attrs["need_sun"]:
        return out
    sig = ("recover", herb.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    herb.meters["perk"] += 1
    herb.meters["scent"] += 1
    herb.meters["droop"] = 0.0
    grown.meters["wrinkle"] = 0.0
    grown.memes["relief"] += 1
    child.memes["pride"] += 1
    if light.meters["charge"] >= CHARGE_MIN:
        light.meters["ready"] += 1
    out.append("__recover__")
    return out


CAUSAL_RULES = [
    Rule(name="droop", tag="physical", apply=_r_droop),
    Rule(name="recover", tag="physical", apply=_r_recover),
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
    "stoop": Place(
        id="stoop",
        label="the sunny stoop",
        scene="Warm bricks held the noon like soup, all golden on the stoop.",
        sun=1,
        spare_sun_spot=True,
        outdoors=True,
        tags={"sun", "garden"},
    ),
    "windowsill": Place(
        id="windowsill",
        label="the kitchen windowsill",
        scene="A square of light lay on the sill, bright and warm and still.",
        sun=1,
        spare_sun_spot=True,
        outdoors=False,
        tags={"sun", "window"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the little courtyard",
        scene="The courtyard stones were pale and bright, sipping up the light.",
        sun=2,
        spare_sun_spot=True,
        outdoors=True,
        tags={"sun", "garden"},
    ),
    "shady_hall": Place(
        id="shady_hall",
        label="the shady hall",
        scene="The hall was cool from wall to wall, with hardly any sun at all.",
        sun=0,
        spare_sun_spot=False,
        outdoors=False,
        tags={"shade", "indoors"},
    ),
}

HERBS = {
    "basil": Herb(
        id="basil",
        label="basil",
        phrase="a basil herb in a red clay pot",
        need_sun=2,
        smell="sweet and peppery",
        tags={"basil", "herb"},
    ),
    "mint": Herb(
        id="mint",
        label="mint",
        phrase="a mint herb in a striped tin pot",
        need_sun=2,
        smell="cool and bright",
        tags={"mint", "herb"},
    ),
    "thyme": Herb(
        id="thyme",
        label="thyme",
        phrase="a thyme herb in a blue stone pot",
        need_sun=1,
        smell="warm and tiny and green",
        tags={"thyme", "herb"},
    ),
}

SOLAR_ITEMS = {
    "lantern": SolarItem(
        id="lantern",
        label="solar lantern",
        phrase="a little solar lantern with star holes",
        glow="glowed through star-shaped holes",
        tags={"solar", "lantern"},
    ),
    "jar": SolarItem(
        id="jar",
        label="solar jar",
        phrase="a solar jar with painted moons",
        glow="shone with moon-blue dots",
        tags={"solar", "jar"},
    ),
    "bug_light": SolarItem(
        id="bug_light",
        label="solar bug light",
        phrase="a solar bug light shaped like a ladybug",
        glow="winked with a ladybug blink",
        tags={"solar", "light"},
    ),
}

FIXES = {
    "share_mirror": Fix(
        id="share_mirror",
        label="share a shiny tray",
        power=1,
        extra_charge=1,
        need_spare_sun=False,
        need_outdoors=False,
        text="slid a shiny baking tray beside the pot so the light could skip and hop toward the leaves",
        qa_text="used a shiny tray to bounce more light onto the herb",
        tags={"mirror", "kindness"},
    ),
    "swap_spot": Fix(
        id="swap_spot",
        label="give the herb the sunny spot",
        power=1,
        extra_charge=1,
        need_spare_sun=True,
        need_outdoors=False,
        text="gave the herb the very best sunny place and set the solar light on a nearby box instead",
        qa_text="gave the herb the best sunny spot and moved the solar light nearby",
        tags={"sharing", "kindness"},
    ),
    "carry_outside": Fix(
        id="carry_outside",
        label="carry the pot outside",
        power=2,
        extra_charge=2,
        need_spare_sun=False,
        need_outdoors=True,
        text="carried the pot outside with gentle hands, where both leaf and light could drink the day",
        qa_text="carried the herb outside into stronger sun",
        tags={"outside", "kindness"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ava", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Milo", "Theo", "Owen", "Eli", "Finn", "Leo", "Sam", "Noah"]


def herb_needs_met(place: Place, fix: Fix, herb: Herb) -> bool:
    return place.sun + fix.power >= herb.need_sun


def solar_ready(place: Place, fix: Fix) -> bool:
    return place.sun + fix.extra_charge >= CHARGE_MIN


def fix_allowed(place: Place, fix: Fix) -> bool:
    if fix.need_spare_sun and not place.spare_sun_spot:
        return False
    if fix.need_outdoors and not place.outdoors:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for herb_id, herb in HERBS.items():
            for solar_id in SOLAR_ITEMS:
                for fix_id, fix in FIXES.items():
                    if not fix_allowed(place, fix):
                        continue
                    if not herb_needs_met(place, fix, herb):
                        continue
                    if not solar_ready(place, fix):
                        continue
                    combos.append((place_id, herb_id, solar_id, fix_id))
    return combos


@dataclass
class StoryParams:
    place: str
    herb: str
    solar_item: str
    fix: str
    child_name: str
    child_gender: str
    grown_name: str
    grown_type: str
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


def predict_need(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    herb = sim.get("herb")
    grown = sim.get("grown")
    return {
        "droop": herb.meters["droop"],
        "wrinkle": grown.meters["wrinkle"],
    }


def introduce(world: World, child: Entity, grown: Entity, herb: Entity, light: Entity) -> None:
    world.say(
        f"{child.id} and {grown.id} stood by {world.place.label}; {world.place.scene}"
    )
    world.say(
        f"{child.id} had brought {light.phrase}, hoping it would sip the sun and sparkle later with delight."
    )
    world.say(
        f"Beside it sat {herb.phrase}, a soft green herb with leaves that ought to stand up proud and bright."
    )


def notice(world: World, child: Entity, grown: Entity, herb: Entity) -> None:
    pred = predict_need(world)
    world.facts["predicted_droop"] = pred["droop"]
    world.facts["predicted_wrinkle"] = pred["wrinkle"]
    if pred["droop"] >= THRESHOLD:
        world.say(
            f"But one leaf bent low with a weary curl, and a wrinkle touched {grown.id}'s brow like a worried pearl."
        )
        world.say(
            f'{child.id} looked twice and softly said, "That little herb seems sad instead."'
        )


def choose_fix(world: World, child: Entity, grown: Entity, herb: Entity, light: Entity, fix: Fix) -> None:
    child.memes["kindness"] += 1
    world.facts["fix_used"] = fix.id
    herb.meters["sun"] += fix.power
    light.meters["charge"] += fix.extra_charge
    world.say(
        f"{child.id} was kind and did not delay; {child.pronoun().capitalize()} {fix.text}."
    )
    world.say(
        f'{grown.id} blinked and smiled a little. "That is a gentle thought," {grown.pronoun()} said, warm and civil.'
    )


def resolve_scene(world: World, child: Entity, grown: Entity, herb: Entity, light: Entity) -> None:
    propagate(world, narrate=False)
    if herb.meters["perk"] >= THRESHOLD:
        world.say(
            f"Soon the leaves stopped sagging low and lifted up in a greener show."
        )
        world.say(
            f"The wrinkle left {grown.id}'s brow, and the {herb.label} smelled {herb.attrs['smell']} now."
        )
    if light.meters["ready"] >= THRESHOLD:
        world.say(
            f"By evening, the {light.label} was ready too, storing golden bits of blue."
        )


def ending(world: World, child: Entity, grown: Entity, herb: Entity, light: Entity) -> None:
    world.say(
        f"When dusk came in with velvet feet, the {light.label} {light.attrs['glow']} small and sweet."
    )
    world.say(
        f"{child.id} and {grown.id} stood near the pot; kindness had warmed the whole small spot."
    )
    world.say(
        f"The herb was tall, the light was bright, and both felt better by night."
    )


def tell(
    place: Place,
    herb_cfg: Herb,
    solar_cfg: SolarItem,
    fix: Fix,
    child_name: str = "Lina",
    child_gender: str = "girl",
    grown_name: str = "Grandma Wren",
    grown_type: str = "grandmother",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            traits=["kind"],
            tags={"child"},
        )
    )
    grown = world.add(
        Entity(
            id=grown_name,
            kind="character",
            type=grown_type,
            role="grown",
            label="the grown-up",
            traits=["gentle"],
            tags={"adult"},
        )
    )
    herb = world.add(
        Entity(
            id="herb",
            kind="thing",
            type="plant",
            label=herb_cfg.label,
            phrase=herb_cfg.phrase,
            role="herb",
            tags=set(herb_cfg.tags),
            portable=True,
            attrs={"need_sun": herb_cfg.need_sun, "smell": herb_cfg.smell},
        )
    )
    light = world.add(
        Entity(
            id="light",
            kind="thing",
            type="light",
            label=solar_cfg.label,
            phrase=solar_cfg.phrase,
            role="solar",
            tags=set(solar_cfg.tags),
            solar=True,
            attrs={"glow": solar_cfg.glow},
        )
    )

    herb.meters["sun"] = float(place.sun)
    light.meters["charge"] = float(place.sun)
    herb.meters["droop"] = 0.0
    herb.meters["perk"] = 0.0
    herb.meters["scent"] = 0.0
    grown.meters["wrinkle"] = 0.0
    child.memes["kindness"] = 0.0
    grown.memes["worry"] = 0.0
    grown.memes["relief"] = 0.0
    child.memes["pride"] = 0.0
    world.facts["place"] = place
    world.facts["herb_cfg"] = herb_cfg
    world.facts["solar_cfg"] = solar_cfg
    world.facts["fix_cfg"] = fix
    world.facts["child"] = child
    world.facts["grown"] = grown
    world.facts["herb"] = herb
    world.facts["light"] = light

    introduce(world, child, grown, herb, light)
    world.para()
    notice(world, child, grown, herb)
    propagate(world, narrate=False)
    world.para()
    choose_fix(world, child, grown, herb, light, fix)
    world.para()
    resolve_scene(world, child, grown, herb, light)
    ending(world, child, grown, herb, light)

    world.facts["recovered"] = herb.meters["perk"] >= THRESHOLD
    world.facts["charged"] = light.meters["ready"] >= THRESHOLD
    world.facts["kind"] = child.memes["kindness"] >= THRESHOLD
    world.facts["wrinkle_gone"] = grown.meters["wrinkle"] < THRESHOLD
    return world


KNOWLEDGE = {
    "solar": [
        (
            "What does solar mean?",
            "Solar means something uses energy from sunlight. A solar light drinks up the sun in the day so it can glow later."
        )
    ],
    "herb": [
        (
            "What is an herb?",
            "An herb is a small plant with leaves that often smell strong and nice. People may grow herbs for cooking, tea, or just to enjoy their scent."
        )
    ],
    "basil": [
        (
            "What does basil smell like?",
            "Basil often smells sweet and peppery. Many people use it in cooking because its leaves have a strong fresh scent."
        )
    ],
    "mint": [
        (
            "What does mint feel like?",
            "Mint smells cool and fresh. When you rub a leaf gently, the smell can seem bright and tingly."
        )
    ],
    "thyme": [
        (
            "What is thyme?",
            "Thyme is a tiny-leaved herb with a warm smell. It likes sunshine and is often grown in little pots or garden beds."
        )
    ],
    "mirror": [
        (
            "How can a shiny tray help a plant?",
            "A shiny tray can bounce light toward the leaves. That extra reflected light can help a plant get more of the sun it needs."
        )
    ],
    "sharing": [
        (
            "What is sharing?",
            "Sharing is letting someone else use something good too. It is a kind way to solve a problem together."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing what someone needs and trying to help in a gentle way. Small helpful choices can change how someone feels."
        )
    ],
    "outside": [
        (
            "Why do plants often grow better outside in sun?",
            "Outside, a plant may get stronger sunlight and more open air. That can help leaves perk up if the plant was too dim indoors."
        )
    ],
}
KNOWLEDGE_ORDER = ["solar", "herb", "basil", "mint", "thyme", "mirror", "sharing", "kindness", "outside"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    herb_cfg = f["herb_cfg"]
    solar_cfg = f["solar_cfg"]
    grown = f["grown"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "solar", "wrinkle", and "herb".',
        f"Tell a gentle kindness story where {child.id} notices a wrinkle of worry on {grown.id}'s brow and helps a {herb_cfg.label} herb while a {solar_cfg.label} charges in the sun.",
        "Write a simple rhyming tale in which a child shares light or space so that both a plant and a little light can end the day doing well.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grown = f["grown"]
    herb = f["herb"]
    light = f["light"]
    fix = f["fix_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {grown.id}, a potted {herb.label} herb, and a {light.label}. They are together at {place.label}."
        ),
        (
            f"Why did {grown.id} have a wrinkle on {grown.pronoun('possessive')} brow?",
            f"{grown.id} was worried because the herb did not have enough sun, so its leaf drooped. The wrinkle showed that {grown.pronoun()} could see the little plant was not doing well."
        ),
        (
            f"How did {child.id} show kindness?",
            f"{child.id} {fix.qa_text}. That kind choice helped the herb and also kept the solar light on its way to charging."
        ),
        (
            "What changed after the child helped?",
            f"The herb perked up and smelled nice, and the wrinkle went away from {grown.id}'s brow. By evening the {light.label} was ready to glow, which proves the day ended better for both."
        ),
        (
            "How did the story end?",
            f"It ended with the {light.label} glowing softly at dusk beside the happy herb. The final image shows that kindness made the whole small place feel warm and calm."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    herb_cfg = f["herb_cfg"]
    fix = f["fix_cfg"]
    solar_cfg = f["solar_cfg"]
    tags = {"solar", "herb", "kindness"} | set(herb_cfg.tags) | set(fix.tags) | set(solar_cfg.tags)
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
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="stoop",
        herb="basil",
        solar_item="lantern",
        fix="share_mirror",
        child_name="Lina",
        child_gender="girl",
        grown_name="Grandma Wren",
        grown_type="grandmother",
    ),
    StoryParams(
        place="windowsill",
        herb="thyme",
        solar_item="jar",
        fix="swap_spot",
        child_name="Milo",
        child_gender="boy",
        grown_name="Aunt June",
        grown_type="aunt",
    ),
    StoryParams(
        place="courtyard",
        herb="mint",
        solar_item="bug_light",
        fix="carry_outside",
        child_name="Ruby",
        child_gender="girl",
        grown_name="Grandpa Reed",
        grown_type="grandfather",
    ),
]


def explain_rejection(place: Place, herb: Herb, fix: Fix) -> str:
    if not fix_allowed(place, fix):
        if fix.need_outdoors and not place.outdoors:
            return (
                f"(No story: {fix.label} needs an outdoor patch of sun, but {place.label} is not outdoors.)"
            )
        if fix.need_spare_sun and not place.spare_sun_spot:
            return (
                f"(No story: {fix.label} needs a spare sunny spot, but {place.label} does not have one.)"
            )
    if not herb_needs_met(place, fix, herb):
        return (
            f"(No story: {place.label} plus {fix.label} still would not give the {herb.label} herb enough sun to recover.)"
        )
    if not solar_ready(place, fix):
        return (
            f"(No story: this setup would not give the solar light enough charge for the evening ending.)"
        )
    return "(No story: this combination does not fit the world.)"


ASP_RULES = r"""
fix_allowed(P,F) :- place(P), fix(F), not needs_outdoors(F), not needs_spare(F).
fix_allowed(P,F) :- place(P), fix(F), needs_outdoors(F), outdoors(P), not needs_spare(F).
fix_allowed(P,F) :- place(P), fix(F), needs_spare(F), spare_sun(P), not needs_outdoors(F).
fix_allowed(P,F) :- place(P), fix(F), needs_spare(F), spare_sun(P), needs_outdoors(F), outdoors(P).

enough_for_herb(P,H,F) :- base_sun(P,PS), herb_need(H,HN), fix_power(F,FP), PS + FP >= HN.
enough_for_light(P,F)  :- base_sun(P,PS), charge_bonus(F,CB), charge_min(M), PS + CB >= M.

valid(P,H,S,F) :- place(P), herb(H), solar_item(S), fix(F),
                  fix_allowed(P,F), enough_for_herb(P,H,F), enough_for_light(P,F).

outcome(P,H,F,thriving) :- valid(P,H,_,F), base_sun(P,PS), herb_need(H,HN), fix_power(F,FP), PS + FP >= HN.
#show valid/4.
#show outcome/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("base_sun", place_id, place.sun))
        if place.spare_sun_spot:
            lines.append(asp.fact("spare_sun", place_id))
        if place.outdoors:
            lines.append(asp.fact("outdoors", place_id))
    for herb_id, herb in HERBS.items():
        lines.append(asp.fact("herb", herb_id))
        lines.append(asp.fact("herb_need", herb_id, herb.need_sun))
    for solar_id in SOLAR_ITEMS:
        lines.append(asp.fact("solar_item", solar_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_power", fix_id, fix.power))
        lines.append(asp.fact("charge_bonus", fix_id, fix.extra_charge))
        if fix.need_spare_sun:
            lines.append(asp.fact("needs_spare", fix_id))
        if fix.need_outdoors:
            lines.append(asp.fact("needs_outdoors", fix_id))
    lines.append(asp.fact("charge_min", CHARGE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "solar" not in sample.story.lower():
            raise StoryError("smoke test story missing or missing 'solar'")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story:
                raise StoryError("empty story")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a solar light, a wrinkle of worry, an herb, and kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--herb", choices=HERBS)
    ap.add_argument("--solar-item", dest="solar_item", choices=SOLAR_ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grown-name")
    ap.add_argument("--grown-type", choices=["grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, gender: Optional[str], name: Optional[str]) -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    return name or rng.choice(pool), chosen_gender


def _pick_grown(rng: random.Random, grown_type: Optional[str], grown_name: Optional[str]) -> tuple[str, str]:
    gt = grown_type or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    defaults = {
        "grandmother": ["Grandma Wren", "Grandma Fern", "Grandma May"],
        "grandfather": ["Grandpa Reed", "Grandpa Moss", "Grandpa Glen"],
        "aunt": ["Aunt June", "Aunt Bee", "Aunt Fern"],
        "uncle": ["Uncle Ray", "Uncle Lee", "Uncle Ash"],
    }
    return grown_name or rng.choice(defaults[gt]), gt


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.herb and args.fix:
        place = PLACES[args.place]
        herb = HERBS[args.herb]
        fix = FIXES[args.fix]
        if not (fix_allowed(place, fix) and herb_needs_met(place, fix, herb) and solar_ready(place, fix)):
            raise StoryError(explain_rejection(place, herb, fix))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.herb is None or c[1] == args.herb)
        and (args.solar_item is None or c[2] == args.solar_item)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        if args.place and args.herb and args.fix:
            raise StoryError(explain_rejection(PLACES[args.place], HERBS[args.herb], FIXES[args.fix]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, herb_id, solar_id, fix_id = rng.choice(sorted(combos))
    child_name, child_gender = _pick_child(rng, args.child_gender, args.child_name)
    grown_name, grown_type = _pick_grown(rng, args.grown_type, args.grown_name)
    return StoryParams(
        place=place_id,
        herb=herb_id,
        solar_item=solar_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=child_gender,
        grown_name=grown_name,
        grown_type=grown_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.herb not in HERBS:
        raise StoryError(f"(Unknown herb: {params.herb})")
    if params.solar_item not in SOLAR_ITEMS:
        raise StoryError(f"(Unknown solar item: {params.solar_item})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    place = PLACES[params.place]
    herb = HERBS[params.herb]
    solar_item = SOLAR_ITEMS[params.solar_item]
    fix = FIXES[params.fix]
    if not (fix_allowed(place, fix) and herb_needs_met(place, fix, herb) and solar_ready(place, fix)):
        raise StoryError(explain_rejection(place, herb, fix))

    world = tell(
        place=place,
        herb_cfg=herb,
        solar_cfg=solar_item,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        grown_name=params.grown_name,
        grown_type=params.grown_type,
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
        print(f"{len(combos)} compatible (place, herb, solar_item, fix) combos:\n")
        for place, herb, solar_item, fix in combos:
            print(f"  {place:11} {herb:6} {solar_item:10} {fix}")
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
            header = f"### {p.child_name}: {p.herb} at {p.place} with {p.solar_item} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
