#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sheet_delay_sum_lesson_learned_repetition_myth.py
==============================================================================

A standalone storyworld in a small mythic domain: a child in an old hill
village helps guard drying offerings with a sacred sheet before night weather
arrives.

This world is built around three seed words -- sheet, delay, sum -- and two
narrative instruments:
- Lesson Learned
- Repetition

The stories use a repeated warning line in a myth-like voice. Simulated state,
not string swapping, decides whether the offering is saved whole or partly lost.

Run it
------
    python storyworlds/worlds/gpt-5.4/sheet_delay_sum_lesson_learned_repetition_myth.py
    python storyworlds/worlds/gpt-5.4/sheet_delay_sum_lesson_learned_repetition_myth.py --goods figs --sheet waxed_sheet --hazard sea_mist
    python storyworlds/worlds/gpt-5.4/sheet_delay_sum_lesson_learned_repetition_myth.py --goods grain --sheet linen_sheet
    python storyworlds/worlds/gpt-5.4/sheet_delay_sum_lesson_learned_repetition_myth.py --all
    python storyworlds/worlds/gpt-5.4/sheet_delay_sum_lesson_learned_repetition_myth.py --verify
"""

from __future__ import annotations

import argparse
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "priestess"}
        male = {"boy", "man", "father", "grandfather", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "priestess": "priestess",
            "priest": "priest",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Goods:
    id: str
    label: str
    phrase: str
    size: str
    vulnerable_to: str
    spoil_text: str
    saved_text: str
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
class SheetCfg:
    id: str
    label: str
    phrase: str
    size: str
    dew_guard: int
    wind_guard: int
    texture: str
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
class Hazard:
    id: str
    label: str
    kind: str
    severity: int
    omen: str
    hit_text: str
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
        self.facts: dict = {
            "hazard_kind": "",
            "hazard_severity": 0,
            "night_has_fallen": False,
        }

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


def _r_exposure(world: World) -> list[str]:
    goods = world.get("goods")
    if not world.facts.get("night_has_fallen"):
        return []
    if goods.attrs.get("covered"):
        return []
    sig = ("exposure", goods.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    goods.meters["exposed"] += 1
    return ["__exposed__"]


def _r_damage(world: World) -> list[str]:
    goods = world.get("goods")
    if goods.meters["exposed"] < THRESHOLD:
        return []
    kind = world.facts.get("hazard_kind")
    sev = int(world.facts.get("hazard_severity", 0))
    if kind == "dew":
        sig = ("dew_damage", goods.id, sev)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        goods.meters["wet"] += sev
        return ["__dew__"]
    if kind == "wind":
        sig = ("wind_damage", goods.id, sev)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        goods.meters["scattered"] += sev
        return ["__wind__"]
    return []


CAUSAL_RULES = [
    Rule(name="exposure", tag="physical", apply=_r_exposure),
    Rule(name="damage", tag="physical", apply=_r_damage),
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
                produced.extend(out)
    if narrate:
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


def size_fits(sheet: SheetCfg, goods: Goods) -> bool:
    order = {"small": 1, "large": 2}
    return order[sheet.size] >= order[goods.size]


def sheet_guard(sheet: SheetCfg, hazard: Hazard) -> int:
    if hazard.kind == "dew":
        return sheet.dew_guard
    if hazard.kind == "wind":
        return sheet.wind_guard
    return 0


def valid_combo(goods: Goods, sheet: SheetCfg, hazard: Hazard) -> bool:
    return size_fits(sheet, goods) and sheet_guard(sheet, hazard) >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for gid, goods in GOODS.items():
        for sid, sheet in SHEETS.items():
            for hid, hazard in HAZARDS.items():
                if valid_combo(goods, sheet, hazard):
                    out.append((gid, sid, hid))
    return out


def protect_power(sheet: SheetCfg, hazard: Hazard, helper_bonus: int = 0) -> int:
    return sheet_guard(sheet, hazard) + helper_bonus


def outcome_of(params: "StoryParams") -> str:
    goods = GOODS[params.goods]
    sheet = SHEETS[params.sheet]
    hazard = HAZARDS[params.hazard]
    power = protect_power(sheet, hazard, helper_bonus=1)
    pressure = hazard.severity + params.delay
    if pressure <= power:
        return "saved"
    return "partial"


def explain_rejection(goods: Goods, sheet: SheetCfg, hazard: Hazard) -> str:
    if not size_fits(sheet, goods):
        return (
            f"(No story: {sheet.phrase} is too small to cover {goods.phrase}. "
            f"The sheet must truly reach the offering.)"
        )
    return (
        f"(No story: {sheet.phrase} cannot honestly guard {goods.phrase} from "
        f"{hazard.label}. Pick a sheet suited to that danger.)"
    )


def knot_sum_for(goods: Goods) -> int:
    corners = 4
    stones = 6 if goods.size == "large" else 4
    return corners + stones


def predict_harm(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.facts["night_has_fallen"] = True
    sim.facts["hazard_severity"] = sim.facts["hazard_severity"] + delay
    propagate(sim, narrate=False)
    goods = sim.get("goods")
    return {
        "wet": goods.meters["wet"],
        "scattered": goods.meters["scattered"],
        "exposed": goods.meters["exposed"],
    }


def introduce(world: World, child: Entity, elder: Entity, goods: Goods, sheet: SheetCfg, hazard: Hazard) -> None:
    world.say(
        f"In the old days, when the hill people said the sky still listened to careful hands, "
        f"{child.id} helped {child.pronoun('possessive')} {elder.label_word} lay out {goods.phrase} "
        f"on the warm stones above the village shrine."
    )
    world.say(
        f"Beside the stones rested {sheet.phrase}, {sheet.texture}, waiting for the hour when "
        f"{hazard.omen} would come."
    )
    line = "Cover with the sheet before the sky remembers night."
    world.facts["refrain"] = line
    world.say(f'"{line}" {elder.label_word.capitalize()} said.')
    child.memes["wonder"] += 1


def explain_task(world: World, elder: Entity, goods: Goods, hazard: Hazard) -> None:
    world.say(
        f"{elder.label_word.capitalize()} touched the offering stones and said that {hazard.label} "
        f"would trouble {goods.phrase} if they were left bare."
    )
    world.say(
        f"The old rule was simple and spoken twice, as old rules often were: "
        f'"{world.facts["refrain"]}"'
    )


def temptation(world: World, child: Entity) -> None:
    child.memes["play"] += 1
    world.say(
        f"But the evening was full of little wonders. {child.id} heard the reed pipes in the lane, "
        f"saw swallows turning in gold light, and thought there was still time."
    )


def warning(world: World, child: Entity, elder: Entity, goods: Goods, hazard: Hazard, delay: int) -> None:
    pred = predict_harm(world, delay)
    world.facts["predicted_harm"] = pred
    child.memes["worry"] += 1
    second = ""
    if hazard.kind == "dew" and pred["wet"] >= THRESHOLD:
        second = f" The first cold beads would soon make {goods.label} {goods.spoil_text}."
    elif hazard.kind == "wind" and pred["scattered"] >= THRESHOLD:
        second = f" One sharp gust would toss {goods.label} into cracks and dust."
    world.say(
        f'{elder.label_word.capitalize()} looked at the darkening rim of the sky. '
        f'"{world.facts["refrain"]}" {elder.pronoun()} said again.{second}'
    )


def delay_beat(world: World, child: Entity, delay: int) -> None:
    if delay <= 0:
        world.say(
            f"This time {child.id} listened at once."
        )
        return
    child.memes["delay"] += float(delay)
    if delay == 1:
        world.say(
            f"Still, {child.id} made a little delay, only long enough for one song and one more look at the swallows."
        )
    else:
        world.say(
            f"Still, {child.id} made a longer delay, telling {child.pronoun('object')}self there was time for one song, "
            f"one race along the terrace, and one last shining glance at the west."
        )


def night_falls(world: World, goods: Goods, hazard: Hazard, delay: int) -> None:
    world.facts["night_has_fallen"] = True
    world.facts["hazard_severity"] = int(world.facts["hazard_severity"]) + delay
    propagate(world, narrate=False)
    if world.get("goods").meters["exposed"] >= THRESHOLD:
        world.say(
            f"Then the edge of day folded shut. {hazard.hit_text}"
        )


def cover_goods(world: World, child: Entity, elder: Entity, goods: Goods, sheet: SheetCfg, hazard: Hazard) -> None:
    goods_ent = world.get("goods")
    goods_ent.attrs["covered"] = True
    goods_ent.attrs["helper_bonus"] = 1
    knots = knot_sum_for(goods)
    world.facts["sum_knots"] = knots
    power = protect_power(sheet, hazard, helper_bonus=1)
    world.facts["protect_power"] = power
    world.say(
        f"{child.id} ran back at last. Together, {child.pronoun()} and {elder.label_word} spread the sheet wide "
        f"and tucked the edges under the offering stones."
    )
    world.say(
        f'{elder.label_word.capitalize()} counted the corners and the stones aloud. '
        f'"Four corners and {knots - 4} stones: the sum is {knots}," {elder.pronoun()} said, '
        f"and {child.id} repeated every number while tying each knot tight."
    )
    goods_ent.meters["guarded"] += power


def ending(world: World, child: Entity, elder: Entity, goods: Goods, hazard: Hazard) -> None:
    goods_ent = world.get("goods")
    if goods_ent.meters["wet"] < THRESHOLD and goods_ent.meters["scattered"] < THRESHOLD:
        goods_ent.meters["saved"] += 1
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
        world.say(
            f"When morning came, the sheet shone with beads of weather, but beneath it {goods.saved_text}."
        )
        world.say(
            f'{child.id} bowed to {elder.label_word} and said, '
            f'"I know the saying now: {world.facts["refrain"]}"'
        )
        world.say(
            f"So the hill people say that from then on {child.id} never let a small delay grow large, "
            f"and the shrine stones were always covered before dusk."
        )
    else:
        child.memes["guilt"] += 1
        child.memes["lesson"] += 1
        if hazard.kind == "dew":
            goods_ent.meters["lost"] += 1
            world.say(
                f"By morning, some of the offering had turned {goods.spoil_text}, though not all was lost."
            )
        else:
            goods_ent.meters["lost"] += 1
            world.say(
                f"By morning, some of the offering was gone to cracks and thorns, though enough remained for the shrine."
            )
        world.say(
            f'{child.id} touched the tied knots and whispered, '
            f'"A little delay can feed a larger loss."'
        )
        world.say(
            f'{elder.label_word.capitalize()} nodded and answered with the old line for the third time: '
            f'"{world.facts["refrain"]}" From that day on, {child.id} obeyed it before the first shadow reached the stones.'
        )


def tell(
    *,
    goods: Goods,
    sheet: SheetCfg,
    hazard: Hazard,
    child_name: str = "Ione",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    child_trait: str = "quick-footed",
    delay: int = 0,
) -> World:
    world = World()
    world.facts["hazard_kind"] = hazard.kind
    world.facts["hazard_severity"] = hazard.severity
    world.facts["night_has_fallen"] = False

    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[child_trait],
            attrs={},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="goods",
            kind="thing",
            type="offering",
            label=goods.label,
            phrase=goods.phrase,
            attrs={"covered": False, "helper_bonus": 0},
        )
    )
    world.add(
        Entity(
            id="sheet",
            kind="thing",
            type="sheet",
            label=sheet.label,
            phrase=sheet.phrase,
            attrs={"size": sheet.size},
        )
    )

    introduce(world, child, elder, goods, sheet, hazard)
    explain_task(world, elder, goods, hazard)

    world.para()
    temptation(world, child)
    warning(world, child, elder, goods, hazard, delay)
    delay_beat(world, child, delay)

    world.para()
    night_falls(world, goods, hazard, delay)
    cover_goods(world, child, elder, goods, sheet, hazard)

    world.para()
    ending(world, child, elder, goods, hazard)

    world.facts.update(
        child=child,
        elder=elder,
        goods_cfg=goods,
        sheet_cfg=sheet,
        hazard_cfg=hazard,
        delay=delay,
        outcome="saved" if world.get("goods").meters["lost"] < THRESHOLD else "partial",
    )
    return world


GOODS = {
    "figs": Goods(
        id="figs",
        label="figs",
        phrase="a row of honey-dark figs",
        size="small",
        vulnerable_to="dew",
        spoil_text="soft and wet",
        saved_text="the figs were sweet and whole",
        tags={"figs", "offerings"},
    ),
    "petals": Goods(
        id="petals",
        label="flower petals",
        phrase="bright flower petals for the shrine bowls",
        size="small",
        vulnerable_to="wind",
        spoil_text="damp and clinging",
        saved_text="the petals were still bright in their bowls",
        tags={"flowers", "offerings"},
    ),
    "grain": Goods(
        id="grain",
        label="grain",
        phrase="broad trays of drying grain",
        size="large",
        vulnerable_to="dew",
        spoil_text="heavy and wet",
        saved_text="the grain was dry enough to sing under the hand",
        tags={"grain", "offerings"},
    ),
    "seedcakes": Goods(
        id="seedcakes",
        label="seed cakes",
        phrase="round seed cakes cooling for the shrine feast",
        size="large",
        vulnerable_to="wind",
        spoil_text="damp and sticky",
        saved_text="the seed cakes rested whole on the stones",
        tags={"cakes", "offerings"},
    ),
}

SHEETS = {
    "linen_sheet": SheetCfg(
        id="linen_sheet",
        label="linen sheet",
        phrase="a pale linen sheet",
        size="small",
        dew_guard=1,
        wind_guard=1,
        texture="light as milkweed cloth",
        tags={"sheet", "linen"},
    ),
    "waxed_sheet": SheetCfg(
        id="waxed_sheet",
        label="waxed sheet",
        phrase="a waxed cedar-colored sheet",
        size="large",
        dew_guard=2,
        wind_guard=1,
        texture="smooth with old oil and cedar scent",
        tags={"sheet", "waxed"},
    ),
    "wool_sheet": SheetCfg(
        id="wool_sheet",
        label="wool sheet",
        phrase="a thick wool sheet",
        size="large",
        dew_guard=1,
        wind_guard=2,
        texture="heavy and warm as a shepherd's cloak",
        tags={"sheet", "wool"},
    ),
}

HAZARDS = {
    "moon_dew": Hazard(
        id="moon_dew",
        label="moon-dew",
        kind="dew",
        severity=1,
        omen="the silver breath of moon-dew",
        hit_text="Cold beads gathered first on the shrine rail, then on the bare offering stones.",
        tags={"dew", "night"},
    ),
    "sea_mist": Hazard(
        id="sea_mist",
        label="sea-mist",
        kind="dew",
        severity=2,
        omen="the sea-mist climbing from the dark valley",
        hit_text="A wet white breath climbed the hill and laid its chill hand over every bare thing.",
        tags={"mist", "night"},
    ),
    "hill_wind": Hazard(
        id="hill_wind",
        label="hill-wind",
        kind="wind",
        severity=1,
        omen="the hill-wind waking among the pines",
        hit_text="The first gust rattled the shrine bells and skated over the stones.",
        tags={"wind", "night"},
    ),
    "ravine_wind": Hazard(
        id="ravine_wind",
        label="ravine-wind",
        kind="wind",
        severity=2,
        omen="the ravine-wind leaping from the black gap below",
        hit_text="A hard gust sprang from the ravine and clawed at every loose thing on the terrace.",
        tags={"wind", "night"},
    ),
}

GIRL_NAMES = ["Ione", "Thaleia", "Myrto", "Daphne", "Rhea", "Lysa"]
BOY_NAMES = ["Theron", "Nikos", "Leandros", "Phaon", "Damon", "Aeson"]
TRAITS = ["quick-footed", "bright-eyed", "curious", "song-loving", "restless", "eager"]


@dataclass
class StoryParams:
    goods: str
    sheet: str
    hazard: str
    child_name: str
    child_gender: str
    elder_type: str
    child_trait: str
    delay: int = 0
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
    "sheet": [
        (
            "What is a sheet?",
            "A sheet is a broad piece of cloth. People can spread it over things to cover and protect them."
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is tiny drops of water that gather on cool things at night. It can make food and cloth wet by morning."
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a thin cloud close to the ground. It can leave everything damp because it is full of tiny drops of water."
        )
    ],
    "wind": [
        (
            "Why can wind be a problem for light things?",
            "Wind pushes and lifts light things. If something is loose, the wind can scatter it before you catch it."
        )
    ],
    "grain": [
        (
            "Why would people dry grain?",
            "People dry grain so it keeps well and can be stored or ground later. Wet grain can spoil."
        )
    ],
    "offerings": [
        (
            "What is an offering?",
            "An offering is something people set aside with care for thanks, prayer, or a feast. In old stories, offerings are often treated with great respect."
        )
    ],
    "flowers": [
        (
            "Why are flower petals easy to scatter?",
            "Flower petals are thin and light. A gust of wind can lift them much more easily than a heavy stone."
        )
    ],
    "cakes": [
        (
            "Why should food be covered outside?",
            "Food left outside can get wet, dusty, or blown away. Covering it keeps it cleaner and safer."
        )
    ],
}
KNOWLEDGE_ORDER = ["sheet", "dew", "mist", "wind", "grain", "offerings", "flowers", "cakes"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    goods = world.facts["goods_cfg"]
    hazard = world.facts["hazard_cfg"]
    return [
        'Write a short myth-like story for a 3-to-5-year-old that includes the words "sheet", "delay", and "sum".',
        f"Tell a small myth where {child.id} must cover {goods.phrase} before {hazard.label} arrives, and a repeated warning becomes a lesson learned.",
        "Write a gentle old-fashioned tale in which a child learns that a little delay can grow into a bigger problem, and include a counted sum of knots.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    goods = world.facts["goods_cfg"]
    sheet = world.facts["sheet_cfg"]
    hazard = world.facts["hazard_cfg"]
    delay = world.facts["delay"]
    knots = world.facts.get("sum_knots", knot_sum_for(goods))
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child helping {child.pronoun('possessive')} {elder.label_word} guard {goods.phrase}. "
            f"They were working on the shrine stones before night came."
        ),
        (
            "What was the child supposed to do with the sheet?",
            f"{child.id} was supposed to spread {sheet.phrase} over {goods.phrase} before {hazard.label} arrived. "
            f"The sheet was meant to keep the offering safe from the night danger."
        ),
        (
            "What was the repeated warning?",
            f'The repeated warning was, "{world.facts["refrain"]}" '
            f"It was said more than once so the child would remember it."
        ),
        (
            "What was the sum in the story?",
            f"The elder counted four corners and {knots - 4} stones, and the sum was {knots}. "
            f"That counted sum turned the covering into careful work instead of a rushed guess."
        ),
    ]
    if delay == 0:
        qa.append(
            (
                f"Did {child.id} delay?",
                f"No. {child.id} listened right away and helped cover the offering in time. "
                f"Because there was no delay, the weather touched the sheet and not the food beneath it."
            )
        )
    else:
        qa.append(
            (
                f"Why did the delay matter?",
                f"The delay gave {hazard.label} more time to reach the bare offering stones. "
                f"In this story, even a small wait made the danger stronger before the sheet was tied down."
            )
        )
    if outcome == "saved":
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with {goods.saved_text}. "
                f"{child.id} learned the warning by heart and stopped letting delay grow."
            )
        )
    else:
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned that a little delay can cause a larger loss. "
                f"Some of the offering was harmed first, so the lesson came from what the child could see in the morning."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["goods_cfg"].tags) | set(world.facts["sheet_cfg"].tags) | set(world.facts["hazard_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or isinstance(v, int)}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        goods="figs",
        sheet="linen_sheet",
        hazard="moon_dew",
        child_name="Ione",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="curious",
        delay=0,
    ),
    StoryParams(
        goods="grain",
        sheet="waxed_sheet",
        hazard="sea_mist",
        child_name="Theron",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="song-loving",
        delay=1,
    ),
    StoryParams(
        goods="petals",
        sheet="wool_sheet",
        hazard="ravine_wind",
        child_name="Daphne",
        child_gender="girl",
        elder_type="priestess",
        child_trait="bright-eyed",
        delay=1,
    ),
    StoryParams(
        goods="seedcakes",
        sheet="wool_sheet",
        hazard="ravine_wind",
        child_name="Aeson",
        child_gender="boy",
        elder_type="priest",
        child_trait="restless",
        delay=2,
    ),
    StoryParams(
        goods="grain",
        sheet="wool_sheet",
        hazard="sea_mist",
        child_name="Myrto",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="eager",
        delay=2,
    ),
]


ASP_RULES = r"""
size_rank(small,1).
size_rank(large,2).

fits(Sheet, Goods) :- sheet_size(Sheet, SS), goods_size(Goods, GS),
                      size_rank(SS, SN), size_rank(GS, GN), SN >= GN.

guard(Sheet, Hazard, G) :- hazard_kind(Hazard, dew), dew_guard(Sheet, G).
guard(Sheet, Hazard, G) :- hazard_kind(Hazard, wind), wind_guard(Sheet, G).

valid(Goods, Sheet, Hazard) :- goods(Goods), sheet(Sheet), hazard(Hazard),
                               fits(Sheet, Goods), guard(Sheet, Hazard, G), G >= 1.

power(P) :- chosen_sheet(S), chosen_hazard(H), guard(S, H, G), helper_bonus(B), P = G + B.
pressure(V) :- chosen_hazard(H), severity(H, S), delay(D), V = S + D.

outcome(saved) :- power(P), pressure(V), P >= V.
outcome(partial) :- power(P), pressure(V), P < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid, goods in GOODS.items():
        lines.append(asp.fact("goods", gid))
        lines.append(asp.fact("goods_size", gid, goods.size))
    for sid, sheet in SHEETS.items():
        lines.append(asp.fact("sheet", sid))
        lines.append(asp.fact("sheet_size", sid, sheet.size))
        lines.append(asp.fact("dew_guard", sid, sheet.dew_guard))
        lines.append(asp.fact("wind_guard", sid, sheet.wind_guard))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("hazard_kind", hid, hazard.kind))
        lines.append(asp.fact("severity", hid, hazard.severity))
    lines.append(asp.fact("helper_bonus", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_sheet", params.sheet),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=False, header="SMOKE")
        finally:
            sys.stdout = old
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child, a sacred sheet, and the cost of delay in a mythic hill village."
    )
    ap.add_argument("--goods", choices=GOODS)
    ap.add_argument("--sheet", choices=SHEETS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the child waits before helping")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "priestess", "priest"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goods and args.sheet and args.hazard:
        goods = GOODS[args.goods]
        sheet = SHEETS[args.sheet]
        hazard = HAZARDS[args.hazard]
        if not valid_combo(goods, sheet, hazard):
            raise StoryError(explain_rejection(goods, sheet, hazard))

    combos = [
        combo
        for combo in valid_combos()
        if (args.goods is None or combo[0] == args.goods)
        and (args.sheet is None or combo[1] == args.sheet)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goods_id, sheet_id, hazard_id = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "priestess", "priest"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        goods=goods_id,
        sheet=sheet_id,
        hazard=hazard_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
        child_trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        goods = GOODS[params.goods]
        sheet = SHEETS[params.sheet]
        hazard = HAZARDS[params.hazard]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not valid_combo(goods, sheet, hazard):
        raise StoryError(explain_rejection(goods, sheet, hazard))

    world = tell(
        goods=goods,
        sheet=sheet,
        hazard=hazard,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (goods, sheet, hazard) combos:\n")
        for goods, sheet, hazard in combos:
            print(f"  {goods:10} {sheet:12} {hazard}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.goods} with {p.sheet} against {p.hazard} (delay {p.delay}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
