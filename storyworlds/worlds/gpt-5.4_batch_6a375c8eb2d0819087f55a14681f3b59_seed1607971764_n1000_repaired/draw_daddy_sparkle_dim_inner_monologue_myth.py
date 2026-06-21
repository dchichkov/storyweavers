#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/draw_daddy_sparkle_dim_inner_monologue_myth.py
=========================================================================

A standalone story world in a small mythic domain: a child goes with daddy to a
dawn shrine where the lamp has gone sparkle-dim, and helps by drawing an old
morning sign on a fitting surface with a fitting bright pigment.

The world is constraint-checked. A story is only valid when:
- the chosen setting actually has the chosen drawing surface,
- the chosen pigment truly works on that surface,
- the pigment is bright enough to wake the lamp,
- and a fluttering surface has a helper who can hold it still.

The story itself is state-driven:
- the lamp fading makes the child worry and daddy hurry,
- drawing the sign with a bright pigment makes the sign glow,
- presenting the glowing sign to the lamp restores the light,
- and the ending image proves the change in the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/draw_daddy_sparkle_dim_inner_monologue_myth.py
    python storyworlds/worlds/gpt-5.4/draw_daddy_sparkle_dim_inner_monologue_myth.py --all
    python storyworlds/worlds/gpt-5.4/draw_daddy_sparkle_dim_inner_monologue_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/draw_daddy_sparkle_dim_inner_monologue_myth.py --trace
    python storyworlds/worlds/gpt-5.4/draw_daddy_sparkle_dim_inner_monologue_myth.py --asp
    python storyworlds/worlds/gpt-5.4/draw_daddy_sparkle_dim_inner_monologue_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRIGHT_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"father": "daddy", "mother": "mama"}.get(self.type, self.type)
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
    image: str
    surfaces: set[str] = field(default_factory=set)
    breeze: str = "soft"
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
class Surface:
    id: str
    label: str
    phrase: str
    stable: bool = True
    ritual: str = ""
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
class Pigment:
    id: str
    label: str
    phrase: str
    brightness: int = 0
    works_on: set[str] = field(default_factory=set)
    stroke: str = ""
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
class Helper:
    id: str
    label: str
    phrase: str
    can_hold: bool = False
    action: str = ""
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_fading_lamp(world: World) -> list[str]:
    lamp = world.get("lamp")
    child = world.get("child")
    daddy = world.get("daddy")
    if lamp.meters["brightness"] >= THRESHOLD:
        return []
    sig = ("fading_lamp",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    daddy.memes["hurry"] += 1
    world.get("night").meters["darkness"] += 1
    return []


def _r_glowing_sign(world: World) -> list[str]:
    surface = world.get("surface")
    pigment = world.get("pigment")
    if surface.meters["drawn"] < THRESHOLD:
        return []
    if not surface.attrs.get("compatible"):
        return []
    if pigment.meters["brightness"] < BRIGHT_MIN:
        return []
    sig = ("glowing_sign",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    surface.meters["glow"] += 1
    child = world.get("child")
    child.memes["hope"] += 1
    return []


def _r_restore_lamp(world: World) -> list[str]:
    surface = world.get("surface")
    lamp = world.get("lamp")
    if surface.meters["glow"] < THRESHOLD or surface.meters["offered"] < THRESHOLD:
        return []
    sig = ("restore_lamp",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lamp.meters["brightness"] += 2
    lamp.meters["awake"] += 1
    world.get("night").meters["darkness"] = 0.0
    child = world.get("child")
    daddy = world.get("daddy")
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    daddy.memes["gratitude"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="fading_lamp", tag="mood", apply=_r_fading_lamp),
    Rule(name="glowing_sign", tag="ritual", apply=_r_glowing_sign),
    Rule(name="restore_lamp", tag="ritual", apply=_r_restore_lamp),
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
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "hill_shrine": Setting(
        id="hill_shrine",
        place="the hill shrine above the sleeping town",
        image="Below them the roofs looked like folded sheep, and above them the sky waited in a deep blue hush.",
        surfaces={"stone_tablet", "linen_banner"},
        breeze="high",
        tags={"shrine", "hill"},
    ),
    "river_gate": Setting(
        id="river_gate",
        place="the river gate where dawn first touched the water",
        image="The river held the stars in broken silver pieces, and reeds whispered at the banks.",
        surfaces={"clay_bowl", "linen_banner", "stone_tablet"},
        breeze="medium",
        tags={"river", "shrine"},
    ),
    "courtyard_niche": Setting(
        id="courtyard_niche",
        place="the courtyard niche beside the fig tree",
        image="The fig leaves made a roof of shadows, and the little niche smelled of warm stone.",
        surfaces={"clay_bowl", "stone_tablet"},
        breeze="soft",
        tags={"courtyard", "home"},
    ),
}

SURFACES = {
    "stone_tablet": Surface(
        id="stone_tablet",
        label="stone tablet",
        phrase="a pale stone tablet",
        stable=True,
        ritual="the old stone that remembered morning marks",
        tags={"stone", "tablet"},
    ),
    "clay_bowl": Surface(
        id="clay_bowl",
        label="clay bowl",
        phrase="a round clay bowl",
        stable=True,
        ritual="the bowl that caught first light",
        tags={"clay", "bowl"},
    ),
    "linen_banner": Surface(
        id="linen_banner",
        label="linen banner",
        phrase="a thin linen banner",
        stable=False,
        ritual="the hanging cloth of the dawn wind",
        tags={"banner", "cloth"},
    ),
    "water_tray": Surface(
        id="water_tray",
        label="water tray",
        phrase="a shallow tray of water",
        stable=False,
        ritual="a tray where every mark drifted apart",
        tags={"water"},
    ),
}

PIGMENTS = {
    "sun_chalk": Pigment(
        id="sun_chalk",
        label="sun chalk",
        phrase="a nub of sun chalk",
        brightness=3,
        works_on={"stone_tablet", "clay_bowl"},
        stroke="left a warm gold line that seemed to remember daylight",
        tags={"chalk", "light"},
    ),
    "star_ink": Pigment(
        id="star_ink",
        label="star ink",
        phrase="a shell of star ink",
        brightness=3,
        works_on={"linen_banner", "stone_tablet"},
        stroke="shone blue-white as if a tiny star had melted into the stroke",
        tags={"ink", "light"},
    ),
    "ember_paint": Pigment(
        id="ember_paint",
        label="ember paint",
        phrase="a little dish of ember paint",
        brightness=2,
        works_on={"clay_bowl", "linen_banner"},
        stroke="glimmered red-gold like a coal breathing in the dark",
        tags={"paint", "light"},
    ),
    "ash_dust": Pigment(
        id="ash_dust",
        label="ash dust",
        phrase="a pinch of gray ash dust",
        brightness=1,
        works_on={"stone_tablet"},
        stroke="made only a dry gray line",
        tags={"ash"},
    ),
}

HELPERS = {
    "none": Helper(
        id="none",
        label="no helper",
        phrase="no helper at all",
        can_hold=False,
        action="",
        tags=set(),
    ),
    "owl": Helper(
        id="owl",
        label="little owl",
        phrase="a little owl with round eyes",
        can_hold=True,
        action="settled on the banner rod and kept the cloth from whipping away",
        tags={"owl"},
    ),
    "goat": Helper(
        id="goat",
        label="white goat",
        phrase="a white goat with moon-curved horns",
        can_hold=False,
        action="waited nearby, patient as carved ivory",
        tags={"goat"},
    ),
}

GIRL_NAMES = ["Iria", "Nora", "Tala", "Mira", "Luma", "Sera"]
BOY_NAMES = ["Aren", "Tomas", "Leo", "Darin", "Pavel", "Ivo"]
TRAITS = ["steady", "careful", "dreamy", "bold", "thoughtful"]

KNOWLEDGE = {
    "chalk": [
        ("What is chalk?",
         "Chalk is a soft stone that can leave a line when you rub it on another surface. People use it to draw marks and pictures.")
    ],
    "ink": [
        ("What is ink?",
         "Ink is a colored liquid used for writing or drawing. It can soak into cloth or paper and leave a strong mark.")
    ],
    "banner": [
        ("Why can a banner be hard to draw on outside?",
         "A banner is cloth, so the wind can flap it and pull it around. That makes it harder to keep a line steady.")
    ],
    "owl": [
        ("Why are owls often linked with night in stories?",
         "Owls are awake when it is dark, so many stories make them wise guides at night. Their quiet flying makes them seem magical.")
    ],
    "shrine": [
        ("What is a shrine?",
         "A shrine is a special place where people keep a lamp, a statue, or an offering. People go there to remember, pray, or ask for help.")
    ],
    "light": [
        ("Why does light matter in dark places?",
         "Light helps people see where they are going and what is around them. In stories, it can also stand for hope and safety.")
    ],
    "clay": [
        ("What is clay?",
         "Clay is soft earth that can be shaped when wet and grows hard when baked or dried. Bowls and pots are often made from it.")
    ],
    "stone": [
        ("Why can stone hold a drawing well?",
         "Stone stays still and keeps its shape, so a careful mark can last on it. A steady surface helps a hand make a clear line.")
    ],
}

KNOWLEDGE_ORDER = ["shrine", "light", "stone", "clay", "banner", "chalk", "ink", "owl"]


@dataclass
class StoryParams:
    setting: str
    surface: str
    pigment: str
    helper: str
    child_name: str
    child_gender: str
    daddy_name: str = "Daddy"
    trait: str = "steady"
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


def surface_available(setting_id: str, surface_id: str) -> bool:
    return surface_id in SETTINGS[setting_id].surfaces


def pigment_fits_surface(pigment_id: str, surface_id: str) -> bool:
    return surface_id in PIGMENTS[pigment_id].works_on


def bright_enough(pigment_id: str) -> bool:
    return PIGMENTS[pigment_id].brightness >= BRIGHT_MIN


def helper_can_steady(surface_id: str, helper_id: str) -> bool:
    surface = SURFACES[surface_id]
    helper = HELPERS[helper_id]
    return surface.stable or helper.can_hold


def valid_combo(setting_id: str, surface_id: str, pigment_id: str, helper_id: str) -> bool:
    return (
        surface_available(setting_id, surface_id)
        and pigment_fits_surface(pigment_id, surface_id)
        and bright_enough(pigment_id)
        and helper_can_steady(surface_id, helper_id)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for surface_id in SURFACES:
            for pigment_id in PIGMENTS:
                for helper_id in HELPERS:
                    if valid_combo(setting_id, surface_id, pigment_id, helper_id):
                        combos.append((setting_id, surface_id, pigment_id, helper_id))
    return combos


def explain_rejection(setting_id: str, surface_id: str, pigment_id: str, helper_id: str) -> str:
    setting = SETTINGS[setting_id]
    surface = SURFACES[surface_id]
    pigment = PIGMENTS[pigment_id]
    helper = HELPERS[helper_id]
    if surface_id not in setting.surfaces:
        return (
            f"(No story: {surface.phrase} is not kept at {setting.place}, so the child has nothing there to draw on.)"
        )
    if surface_id not in pigment.works_on:
        return (
            f"(No story: {pigment.label} does not hold on the {surface.label}, so the dawn sign would not stay.)"
        )
    if pigment.brightness < BRIGHT_MIN:
        return (
            f"(No story: {pigment.label} is too dim to wake the lamp. Pick a brighter mark such as sun_chalk, star_ink, or ember_paint.)"
        )
    if not surface.stable and not helper.can_hold:
        return (
            f"(No story: the {surface.label} moves in the breeze, and {helper.label} cannot hold it still for a careful draw.)"
        )
    return "(No story: that combination does not make a reasonable dawn-sign ritual.)"


def child_thought(world: World, text: str) -> None:
    child = world.get("child")
    world.say(f'In {child.pronoun("possessive")} heart, {child.id} thought, "{text}"')


def predict_restoration(world: World) -> dict:
    sim = world.copy()
    surface = sim.get("surface")
    surface.meters["drawn"] += 1
    surface.attrs["compatible"] = True
    surface.meters["offered"] += 1
    propagate(sim, narrate=False)
    return {
        "lamp_awake": sim.get("lamp").meters["awake"] >= THRESHOLD,
        "brightness": sim.get("lamp").meters["brightness"],
    }


def introduce(world: World, child: Entity, daddy: Entity, setting: Setting) -> None:
    trait = next((t for t in child.traits if t != "little"), "")
    world.say(
        f"In the old days, when every morning had to be invited into the world, "
        f"{child.id} climbed with {child.pronoun('possessive')} {daddy.label_word} to {setting.place}."
    )
    world.say(
        f"{setting.image} {child.id} was a little {trait} {child.type} who watched everything as if it might turn into a sign."
    )


def reveal_trouble(world: World, child: Entity, daddy: Entity) -> None:
    lamp = world.get("lamp")
    propagate(world, narrate=False)
    if lamp.meters["brightness"] < THRESHOLD:
        world.say(
            f"At the shrine, the dawn lamp burned only sparkle-dim, a trembling bead of light inside its shell of glass."
        )
        world.say(
            f'{daddy.label_word.capitalize()} lifted it and frowned. "If the lamp sleeps too long, the valley wakes slowly," {daddy.pronoun()} said.'
        )
        child_thought(world, "The dark is listening. I want to help before it grows bigger.")


def daddy_prepares(world: World, daddy: Entity, surface: Surface, pigment: Pigment) -> None:
    world.say(
        f"{daddy.label_word.capitalize()} set out {SURFACES[surface.id].phrase} beside {PIGMENTS[pigment.id].phrase}."
    )
    world.say(
        f'"The old mark must be drawn true," {daddy.label_word} said. "A waking lamp knows a steady sign."'
    )


def offer_help(world: World, child: Entity, daddy: Entity, surface: Surface, pigment: Pigment) -> None:
    pred = predict_restoration(world)
    world.facts["predicted_awake"] = pred["lamp_awake"]
    world.facts["predicted_brightness"] = pred["brightness"]
    world.say(f'{child.id} touched {pigment.phrase} with one finger. "May I draw it, {daddy.label_word}?"')
    world.say(
        f"{daddy.label_word.capitalize()} looked at the little hand, then at the sleepy lamp, and nodded once."
    )
    child_thought(world, "My hand is small, but morning starts small too.")


def steady_surface(world: World, helper: Helper, surface: Surface) -> None:
    if not SURFACES[surface.id].stable and helper.id != "none":
        world.say(
            f"Then {helper.phrase} came near and {helper.action}."
        )
    elif not SURFACES[surface.id].stable and helper.id == "none":
        world.say(
            f"The {surface.label} twitched in the wind."
        )


def draw_sign(world: World, child: Entity, daddy: Entity, surface: Surface, pigment: Pigment) -> None:
    surface_ent = world.get("surface")
    child.memes["focus"] += 1
    world.say(
        f"{child.id} bent over {surface.phrase} and began to draw the dawn sign, the curling line that called light by its oldest name."
    )
    if child.memes["worry"] >= THRESHOLD and "steady" not in child.traits:
        child.memes["fear"] += 1
        world.say(
            f"The first small curve came out thin. For one breath, {child.id}'s hand trembled."
        )
        child_thought(world, "Do not let the line break. If it breaks, maybe the morning will not hear me.")
        world.say(
            f'{daddy.label_word.capitalize()} laid one warm finger on the edge of {surface.phrase}. "Take one more breath," {daddy.pronoun()} whispered.'
        )
    else:
        child_thought(world, "Hold still, hand. Be as calm as the moon before dawn.")
    surface_ent.meters["drawn"] += 1
    surface_ent.attrs["compatible"] = True
    world.say(
        f"The next stroke {pigment.stroke}, and the whole sign closed into a bright loop."
    )
    propagate(world, narrate=False)
    if surface_ent.meters["glow"] >= THRESHOLD:
        world.say(
            f"A hush moved over the shrine. The mark itself began to shine."
        )


def offer_sign(world: World, child: Entity, daddy: Entity, surface: Surface) -> None:
    surface_ent = world.get("surface")
    surface_ent.meters["offered"] += 1
    world.say(
        f"{daddy.label_word.capitalize()} raised the lamp, and {child.id} lifted the {surface.label} beneath it as if carrying a tiny sunrise."
    )
    propagate(world, narrate=False)


def lamp_answers(world: World, child: Entity, daddy: Entity) -> None:
    lamp = world.get("lamp")
    if lamp.meters["awake"] >= THRESHOLD:
        world.say(
            "The weak bead inside the glass opened like a golden eye. Light ran through the lamp ribs, over the shrine stones, and down toward the houses below."
        )
        world.say(
            f'{daddy.label_word.capitalize()} laughed softly. "You woke it," {daddy.pronoun()} said.'
        )
        child_thought(world, "It heard me. Morning was listening after all.")


def ending(world: World, child: Entity, daddy: Entity, setting: Setting, helper: Helper) -> None:
    world.say(
        f"From {setting.place}, the first birds began to answer the lamp."
    )
    if helper.id != "none" and helper.id in {"owl", "goat"}:
        world.say(f"Even {helper.label} seemed washed in gold.")
    world.say(
        f"{child.id} slipped a small hand into {child.pronoun('possessive')} {daddy.label_word}'s hand, and together they watched the valley turn from blue to honey."
    )


def tell(
    setting: Setting,
    surface: Surface,
    pigment: Pigment,
    helper: Helper,
    child_name: str = "Mira",
    child_gender: str = "girl",
    daddy_name: str = "Daddy",
    trait: str = "steady",
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["little", trait],
        tags={"child"},
    ))
    daddy = world.add(Entity(
        id=daddy_name,
        kind="character",
        type="father",
        label="the father",
        role="daddy",
        traits=["gentle", "keeper"],
        tags={"daddy"},
    ))
    lamp = world.add(Entity(
        id="lamp",
        kind="thing",
        type="lamp",
        label="dawn lamp",
        role="lamp",
        tags={"light", "shrine"},
    ))
    night = world.add(Entity(
        id="night",
        kind="thing",
        type="night",
        label="night",
        role="night",
        tags={"dark"},
    ))
    surface_ent = world.add(Entity(
        id="surface",
        kind="thing",
        type="surface",
        label=surface.label,
        role="surface",
        attrs={"stable": surface.stable, "compatible": False},
        tags=set(surface.tags),
    ))
    pigment_ent = world.add(Entity(
        id="pigment",
        kind="thing",
        type="pigment",
        label=pigment.label,
        role="pigment",
        tags=set(pigment.tags),
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="thing",
        type="helper",
        label=helper.label,
        role="helper",
        attrs={"can_hold": helper.can_hold},
        tags=set(helper.tags),
    ))

    lamp.meters["brightness"] = 0.0
    lamp.meters["awake"] = 0.0
    night.meters["darkness"] = 0.0
    pigment_ent.meters["brightness"] = float(pigment.brightness)
    surface_ent.meters["drawn"] = 0.0
    surface_ent.meters["glow"] = 0.0
    surface_ent.meters["offered"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["focus"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["joy"] = 0.0
    daddy.memes["hurry"] = 0.0
    daddy.memes["gratitude"] = 0.0

    world.facts.update(
        setting=setting,
        surface_cfg=surface,
        pigment_cfg=pigment,
        helper_cfg=helper,
        child=child,
        daddy=daddy,
        lamp=lamp,
        used_helper=helper.id != "none",
        surface_needed_holding=not surface.stable,
    )

    introduce(world, child, daddy, setting)
    reveal_trouble(world, child, daddy)

    world.para()
    daddy_prepares(world, daddy, surface, pigment)
    offer_help(world, child, daddy, surface, pigment)
    steady_surface(world, helper, surface)

    world.para()
    draw_sign(world, child, daddy, surface, pigment)
    offer_sign(world, child, daddy, surface)
    lamp_answers(world, child, daddy)

    world.para()
    ending(world, child, daddy, setting, helper)

    world.facts.update(
        restored=lamp.meters["awake"] >= THRESHOLD,
        lamp_bright=lamp.meters["brightness"] >= THRESHOLD,
        sign_glowed=surface_ent.meters["glow"] >= THRESHOLD,
        darkness_gone=night.meters["darkness"] == 0.0,
        child_worried=child.memes["worry"] >= THRESHOLD,
        child_relieved=child.memes["relief"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    surface = f["surface_cfg"]
    pigment = f["pigment_cfg"]
    return [
        'Write a short myth-like story for a 3-to-5-year-old that includes the words "draw", "daddy", and "sparkle-dim".',
        f"Tell a gentle myth where a child named {child.id} helps daddy wake a sleepy dawn lamp at {setting.place} by drawing a sign on {surface.phrase}.",
        f"Write a story with inner monologue in which a little {child.type} uses {pigment.label} to draw a bright mark and bring light back before morning.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    daddy = f["daddy"]
    setting = f["setting"]
    surface = f["surface_cfg"]
    pigment = f["pigment_cfg"]
    helper = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} daddy at {setting.place}. They are trying to wake the dawn lamp before morning comes."
        ),
        (
            "What was wrong with the lamp at the beginning?",
            "The lamp was sparkle-dim and barely glowing. That made the child worry because the valley needed the lamp to wake the morning."
        ),
        (
            f"How did {child.id} try to help?",
            f"{child.id} used {pigment.label} to draw the old dawn sign on {surface.phrase}. The drawing mattered because a true bright sign could wake the sleepy lamp."
        ),
    ]
    if f["surface_needed_holding"]:
        qa.append(
            (
                f"Why was {helper.label if helper.id != 'none' else 'the surface'} important?",
                f"The {surface.label} could move in the breeze, so it needed help staying still. {helper.label.capitalize()} kept it steady, which let {child.id} make a careful line."
                if helper.id != "none"
                else f"The {surface.label} was hard to hold still because the breeze tugged at it. In this story the chosen helper could steady it, so the drawing could be made clearly."
            )
        )
    qa.append(
        (
            "What happened after the child finished the drawing?",
            "The sign began to glow, and then the lamp woke and shone bright again. When the light returned, the dark feeling of danger went away too."
        )
    )
    qa.append(
        (
            f"How did {child.id} feel at the end?",
            f"{child.id} felt relieved and joyful. At first the child was scared the dark might win, but the bright sign worked and proved the little hand could truly help."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"shrine", "light"}
    surface = world.facts["surface_cfg"]
    pigment = world.facts["pigment_cfg"]
    helper = world.facts["helper_cfg"]
    tags |= set(surface.tags)
    tags |= set(pigment.tags)
    tags |= set(helper.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
    lines.append(f"  setting: {world.setting.id}")
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v or isinstance(v, bool)}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
available(S, Surf) :- setting(S), has_surface(S, Surf).
usable(P, Surf)    :- pigment(P), works_on(P, Surf).
bright(P)          :- pigment(P), brightness(P, B), bright_min(M), B >= M.
steadyable(Surf, H) :- surface(Surf), stable(Surf).
steadyable(Surf, H) :- surface(Surf), helper(H), holds(H), not stable(Surf).

valid(S, Surf, P, H) :- available(S, Surf), usable(P, Surf), bright(P), steadyable(Surf, H).

sign_glows :- chosen_surface(Surf), chosen_pigment(P), usable(P, Surf), bright(P).
lamp_restored :- sign_glows, chosen_helper(H), steadyable(Surf, H), chosen_surface(Surf).
:- chosen_setting(S), chosen_surface(Surf), not available(S, Surf).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, setting in SETTINGS.items():
        for surf in sorted(setting.surfaces):
            lines.append(asp.fact("has_surface", sid, surf))
    for surf_id, surf in SURFACES.items():
        lines.append(asp.fact("surface", surf_id))
        if surf.stable:
            lines.append(asp.fact("stable", surf_id))
    for pid, pigment in PIGMENTS.items():
        lines.append(asp.fact("pigment", pid))
        lines.append(asp.fact("brightness", pid, pigment.brightness))
        for surf in sorted(pigment.works_on):
            lines.append(asp.fact("works_on", pid, surf))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if helper.can_hold:
            lines.append(asp.fact("holds", hid))
    lines.append(asp.fact("bright_min", BRIGHT_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_restored(params: StoryParams) -> bool:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_surface", params.surface),
        asp.fact("chosen_pigment", params.pigment),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(scenario, "#show lamp_restored/0."))
    return bool(asp.atoms(model, "lamp_restored"))


CURATED = [
    StoryParams(
        setting="hill_shrine",
        surface="linen_banner",
        pigment="star_ink",
        helper="owl",
        child_name="Mira",
        child_gender="girl",
        daddy_name="Daddy",
        trait="dreamy",
    ),
    StoryParams(
        setting="river_gate",
        surface="clay_bowl",
        pigment="ember_paint",
        helper="goat",
        child_name="Aren",
        child_gender="boy",
        daddy_name="Daddy",
        trait="careful",
    ),
    StoryParams(
        setting="courtyard_niche",
        surface="stone_tablet",
        pigment="sun_chalk",
        helper="none",
        child_name="Luma",
        child_gender="girl",
        daddy_name="Daddy",
        trait="steady",
    ),
    StoryParams(
        setting="river_gate",
        surface="stone_tablet",
        pigment="star_ink",
        helper="none",
        child_name="Ivo",
        child_gender="boy",
        daddy_name="Daddy",
        trait="thoughtful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child helps daddy wake a sparkle-dim dawn lamp by drawing a bright sign."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--pigment", choices=PIGMENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.surface and args.pigment and args.helper:
        if not valid_combo(args.setting, args.surface, args.pigment, args.helper):
            raise StoryError(explain_rejection(args.setting, args.surface, args.pigment, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.surface is None or combo[1] == args.surface)
        and (args.pigment is None or combo[2] == args.pigment)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        if args.setting and args.surface and args.pigment and args.helper:
            raise StoryError(explain_rejection(args.setting, args.surface, args.pigment, args.helper))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, surface_id, pigment_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        surface=surface_id,
        pigment=pigment_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        daddy_name="Daddy",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Invalid surface: {params.surface})")
    if params.pigment not in PIGMENTS:
        raise StoryError(f"(Invalid pigment: {params.pigment})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if not valid_combo(params.setting, params.surface, params.pigment, params.helper):
        raise StoryError(explain_rejection(params.setting, params.surface, params.pigment, params.helper))

    world = tell(
        setting=SETTINGS[params.setting],
        surface=SURFACES[params.surface],
        pigment=PIGMENTS[params.pigment],
        helper=HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        daddy_name=params.daddy_name,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    for params in CURATED:
        py_restored = generate(params).world.facts["restored"]
        asp_ok = asp_restored(params)
        if py_restored != asp_ok:
            rc = 1
            print(f"MISMATCH in restored outcome for {params}: python={py_restored} asp={asp_ok}")
            break
    else:
        print(f"OK: restored outcome matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(123))
        sample = generate(params)
        if "sparkle-dim" not in sample.story or "daddy" not in sample.story.lower():
            raise StoryError("required seed language missing from default generation")
        print("OK: default seeded generation passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show lamp_restored/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, surface, pigment, helper) combos:\n")
        for setting_id, surface_id, pigment_id, helper_id in combos:
            print(f"  {setting_id:15} {surface_id:13} {pigment_id:12} {helper_id}")
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
            header = f"### {p.child_name}: {p.pigment} on {p.surface} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
