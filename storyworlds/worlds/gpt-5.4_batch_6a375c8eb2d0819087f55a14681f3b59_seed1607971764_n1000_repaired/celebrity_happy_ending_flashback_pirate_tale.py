#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/celebrity_happy_ending_flashback_pirate_tale.py
===========================================================================

A standalone story world for a tiny pirate tale about a child who wants to make
a "celebrity pirate" show at the harbor fair, loses the crowd's flag to the
wind, remembers an earlier lesson, and uses that remembered lesson to solve the
problem kindly.

The world model is built around a simple, reasoned constraint:

    show plan + windy place + loose decoration -> it can blow away
    remembered knot lesson + suitable tie gear -> the decoration can be secured

So the story is not just nouns swapped into one paragraph. A concrete world is
simulated: children play pirates, a helpful adult once taught a knot, the wind
creates a real problem, the flashback changes the child's action, and the ending
shows the celebration safely working.

Run it
------
    python storyworlds/worlds/gpt-5.4/celebrity_happy_ending_flashback_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/celebrity_happy_ending_flashback_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/celebrity_happy_ending_flashback_pirate_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/celebrity_happy_ending_flashback_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/celebrity_happy_ending_flashback_pirate_tale.py --json
    python storyworlds/worlds/gpt-5.4/celebrity_happy_ending_flashback_pirate_tale.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
class Harbor:
    id: str
    label: str
    detail: str
    windy: bool
    breeze_word: str
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
class ShowPlan:
    id: str
    title: str
    boast: str
    decoration: str
    problem_name: str
    flashback_hook: str
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
class Decoration:
    id: str
    label: str
    phrase: str
    loose_word: str
    can_blow: bool
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
    type: str
    label: str
    lesson_text: str
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
class TieGear:
    id: str
    label: str
    phrase: str
    safe_for: set[str] = field(default_factory=set)
    sense: int = 0
    success_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_wind_steals(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    banner = world.get("decoration")
    if place.meters["wind"] < THRESHOLD:
        return out
    if banner.meters["loose"] < THRESHOLD:
        return out
    sig = ("wind_steals", banner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    banner.meters["adrift"] += 1
    for eid in ("hero", "mate"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    out.append("__adrift__")
    return out


def _r_tied_safe(world: World) -> list[str]:
    out: list[str] = []
    banner = world.get("decoration")
    if banner.meters["secured"] < THRESHOLD:
        return out
    sig = ("tied_safe", banner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    banner.meters["adrift"] = 0.0
    world.get("place").meters["trouble"] = 0.0
    for eid in ("hero", "mate"):
        if eid in world.entities:
            kid = world.get(eid)
            kid.memes["relief"] += 1
            kid.memes["pride"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wind_steals", tag="physical", apply=_r_wind_steals),
    Rule(name="tied_safe", tag="physical", apply=_r_tied_safe),
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


def hazard_at_risk(place: Harbor, decoration: Decoration) -> bool:
    return place.windy and decoration.can_blow


def sensible_gears() -> list[TieGear]:
    return [g for g in TIE_GEAR.values() if g.sense >= SENSE_MIN]


def can_secure(gear: TieGear, decoration: Decoration) -> bool:
    return decoration.id in gear.safe_for and gear.sense >= SENSE_MIN


def predict_drift(world: World) -> dict:
    sim = world.copy()
    sim.get("place").meters["wind"] = 1.0
    sim.get("decoration").meters["loose"] = 1.0
    propagate(sim, narrate=False)
    return {
        "adrift": sim.get("decoration").meters["adrift"] >= THRESHOLD,
        "worry": sim.get("hero").memes["worry"] + sim.get("mate").memes["worry"],
    }


def play_setup(world: World, hero: Entity, mate: Entity, place: Harbor, plan: ShowPlan) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On fair day, {hero.id} and {mate.id} hurried to {place.label}. "
        f"{place.detail}"
    )
    world.say(
        f"They had turned an old crate and a striped blanket into a tiny pirate stage. "
        f'{hero.id} whispered, "Today our ship will be the {plan.title}!"'
    )
    world.say(
        f'{mate.id} grinned. "And everyone will cheer for the {plan.boast}!"'
    )


def mention_celebrity(world: World, hero: Entity, plan: ShowPlan) -> None:
    hero.memes["dream"] += 1
    world.say(
        f"{hero.id} loved the thought of being a harbor celebrity for one bright afternoon, "
        f"with small children waving and grown-ups clapping at the pirate show."
    )


def raise_decoration(world: World, hero: Entity, mate: Entity, decoration: Decoration, plan: ShowPlan) -> None:
    banner = world.get("decoration")
    banner.meters["loose"] = 1.0
    world.say(
        f"They lifted {decoration.phrase} onto the mast of a broom handle. "
        f"It looked splendid, but the knot sat {decoration.loose_word}."
    )
    world.say(
        f'"Quick, before the crowd comes," said {hero.id}. "{plan.problem_name} first, and knots later."'
    )


def wind_problem(world: World, hero: Entity, mate: Entity, place: Harbor, decoration: Decoration) -> None:
    world.get("place").meters["wind"] = 1.0
    propagate(world, narrate=False)
    world.get("place").meters["trouble"] = 1.0
    world.say(
        f"Then {place.breeze_word} came frisking along the harbor. It caught {decoration.phrase}, "
        f"snapped it once, and whisked it off the broom handle."
    )
    world.say(
        f'{mate.id} gasped. "Our flag!"'
    )


def chase(world: World, hero: Entity, mate: Entity, decoration: Decoration) -> None:
    banner = world.get("decoration")
    banner.meters["soggy"] += 1
    hero.memes["worry"] += 1
    mate.memes["worry"] += 1
    world.say(
        f"The little flag skittered over the boards and landed against a damp coil of rope. "
        f"The pirate stage looked bare at once."
    )
    world.say(
        f'{hero.id} felt the proud celebrity dream wobble. "{hero.pronoun("subject").capitalize()} was supposed to look grand," '
        f'{hero.pronoun("subject")} thought.'
    )


def flashback(world: World, hero: Entity, helper: Entity, plan: ShowPlan) -> None:
    hero.memes["memory"] += 1
    world.facts["flashback_used"] = True
    world.say(
        f"Just then, {plan.flashback_hook}, and a memory rose bright in {hero.id}'s mind."
    )
    world.say(
        f"Last week, {helper.label_word} had knelt beside a laundry line and said, "
        f'"{helper.attrs["lesson_text"]}"'
    )
    world.say(
        f"{hero.id} could almost feel {helper.label_word}'s steady hands guiding the loop and tuck again."
    )


def choose_fix(world: World, hero: Entity, mate: Entity, gear: TieGear, decoration: Decoration) -> None:
    world.get("decoration").meters["secured"] += 1
    propagate(world, narrate=False)
    hero.memes["confidence"] += 1
    mate.memes["hope"] += 1
    world.say(
        f'"I remember now," said {hero.id}. "We do not need to grab and hope. We need {gear.phrase}."'
    )
    world.say(
        gear.success_text.replace("{decoration}", decoration.label).replace("{hero}", hero.id).replace("{mate}", mate.id)
    )


def celebrate(world: World, hero: Entity, mate: Entity, plan: ShowPlan, decoration: Decoration) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"Soon the little crowd gathered after all. {decoration.phrase.capitalize()} fluttered safely above the stage instead of flying away."
    )
    world.say(
        f'{mate.id} bowed low and cried, "Make way for the {plan.boast}!"'
    )
    world.say(
        f"The children laughed, the gulls wheeled overhead, and for a happy minute {hero.id} truly did feel like a celebrity pirate."
    )
    world.say(
        f"But the best part was not the cheering. It was knowing the ship stayed brave and tidy because {hero.id} remembered and used a careful lesson."
    )


def tell(
    place: Harbor,
    plan: ShowPlan,
    decoration: Decoration,
    helper_cfg: Helper,
    gear: TieGear,
    *,
    hero_name: str = "Nell",
    hero_gender: str = "girl",
    mate_name: str = "Finn",
    mate_gender: str = "boy",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    mate = world.add(Entity(id="mate", kind="character", type=mate_gender, label=mate_name, role="mate"))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            role="helper",
            attrs={"lesson_text": helper_cfg.lesson_text},
        )
    )
    place_ent = world.add(Entity(id="place", type="place", label=place.label))
    deco_ent = world.add(Entity(id="decoration", type="decoration", label=decoration.label))

    place_ent.meters["wind"] = 0.0
    place_ent.meters["trouble"] = 0.0
    deco_ent.meters["loose"] = 0.0
    deco_ent.meters["adrift"] = 0.0
    deco_ent.meters["secured"] = 0.0
    deco_ent.meters["soggy"] = 0.0
    hero.memes["worry"] = 0.0
    mate.memes["worry"] = 0.0
    hero.memes["memory"] = 0.0
    mate.memes["hope"] = 0.0
    world.facts["flashback_used"] = False

    play_setup(world, hero, mate, place, plan)
    mention_celebrity(world, hero, plan)

    world.para()
    raise_decoration(world, hero, mate, decoration, plan)
    if not hazard_at_risk(place, decoration):
        raise StoryError(
            f"(No story: {decoration.phrase} would not be in real danger at {place.label}, "
            f"so the flashback would have nothing honest to solve.)"
        )

    pred = predict_drift(world)
    world.facts["predicted_adrift"] = pred["adrift"]
    world.facts["predicted_worry"] = pred["worry"]

    wind_problem(world, hero, mate, place, decoration)
    chase(world, hero, mate, decoration)

    world.para()
    flashback(world, hero, helper, plan)
    if not can_secure(gear, decoration):
        raise StoryError(
            f"(No story: {gear.label} is not a sensible way to secure {decoration.label}. "
            f"Pick gear that can really tie it safely.)"
        )
    choose_fix(world, hero, mate, gear, decoration)

    world.para()
    celebrate(world, hero, mate, plan, decoration)

    world.facts.update(
        hero=hero,
        mate=mate,
        helper=helper,
        place_cfg=place,
        plan=plan,
        decoration_cfg=decoration,
        place=place_ent,
        decoration=deco_ent,
        gear=gear,
        problem_happened=deco_ent.meters["soggy"] >= THRESHOLD or deco_ent.meters["adrift"] == 0.0,
        solved=deco_ent.meters["secured"] >= THRESHOLD,
        happy_ending=hero.memes["joy"] >= 2.0 and mate.memes["joy"] >= 2.0,
    )
    return world


HARBORS = {
    "sunny_dock": Harbor(
        id="sunny_dock",
        label="the sunny dock",
        detail="Bright pennants winked between posts, and the tide slapped softly under the boards.",
        windy=True,
        breeze_word="a playful sea breeze",
        tags={"harbor", "wind"},
    ),
    "fish_pier": Harbor(
        id="fish_pier",
        label="the fish pier",
        detail="Little boats rocked in their slips, and silver scales shone on buckets nearby.",
        windy=True,
        breeze_word="a brisk harbor gust",
        tags={"harbor", "wind"},
    ),
    "cove_stage": Harbor(
        id="cove_stage",
        label="the cove stage",
        detail="A driftwood sign leaned by the rail, and gulls cried above the water.",
        windy=True,
        breeze_word="a salty breeze",
        tags={"harbor", "wind"},
    ),
}

SHOW_PLANS = {
    "star_captain": ShowPlan(
        id="star_captain",
        title="Star Captain",
        boast="most splendid pirate captain in the bay",
        decoration="a shining star flag",
        problem_name="raise the flag",
        flashback_hook="the loose rope brushed {hero}'s wrist".replace("{hero}", "the child"),
        tags={"pirate", "show"},
    ),
    "moon_treasure": ShowPlan(
        id="moon_treasure",
        title="Moon Treasure",
        boast="finest treasure finder on the sea",
        decoration="a moon-blue banner",
        problem_name="hang the banner",
        flashback_hook="the wet rope smelled exactly like the wash line at home",
        tags={"pirate", "show"},
    ),
    "parrot_queen": ShowPlan(
        id="parrot_queen",
        title="Parrot Queen",
        boast="boldest pirate singer on the wharf",
        decoration="a green parrot pennant",
        problem_name="hoist the pennant",
        flashback_hook="the broom-handle mast knocked softly against the rail",
        tags={"pirate", "show"},
    ),
}

DECORATIONS = {
    "paper_flag": Decoration(
        id="paper_flag",
        label="paper flag",
        phrase="the paper flag",
        loose_word="far too loose",
        can_blow=True,
        tags={"flag", "paper"},
    ),
    "cloth_banner": Decoration(
        id="cloth_banner",
        label="cloth banner",
        phrase="the cloth banner",
        loose_word="wobbly and weak",
        can_blow=True,
        tags={"banner", "cloth"},
    ),
    "parrot_pennant": Decoration(
        id="parrot_pennant",
        label="parrot pennant",
        phrase="the parrot pennant",
        loose_word="slippery and small",
        can_blow=True,
        tags={"pennant", "cloth"},
    ),
    "painted_sign": Decoration(
        id="painted_sign",
        label="painted sign",
        phrase="the painted wooden sign",
        loose_word="crooked",
        can_blow=False,
        tags={"sign", "wood"},
    ),
}

HELPERS = {
    "mother": Helper(
        id="mother",
        type="mother",
        label="the mother",
        lesson_text="A neat knot is slower at the start, but it saves tears later.",
        tags={"grownup", "knot"},
    ),
    "father": Helper(
        id="father",
        type="father",
        label="the father",
        lesson_text="Loop, tuck, and pull snug. Let the knot do the holding for you.",
        tags={"grownup", "knot"},
    ),
    "aunt": Helper(
        id="aunt",
        type="aunt",
        label="the aunt",
        lesson_text="When wind is cheeky, tie kindly and tie twice.",
        tags={"grownup", "knot"},
    ),
}

TIE_GEAR = {
    "twine": TieGear(
        id="twine",
        label="twine",
        phrase="a piece of twine",
        safe_for={"paper_flag", "cloth_banner", "parrot_pennant"},
        sense=3,
        success_text="{hero} fetched a piece of twine, wrapped it through the corner loops, and tied the {decoration} snug to the little mast.",
        fail_text="{hero} waved the twine at the air, but never tied a real knot, so the {decoration} slipped free again.",
        qa_text="used twine and tied a snug knot",
        tags={"twine", "knot"},
    ),
    "ribbon": TieGear(
        id="ribbon",
        label="ribbon",
        phrase="a spare ribbon",
        safe_for={"cloth_banner", "parrot_pennant"},
        sense=2,
        success_text="{mate} held the mast steady while {hero} used a spare ribbon and tied the {decoration} in a careful double bow that the wind could not steal.",
        fail_text="{hero} used a soft ribbon on the wrong thing, and it slipped loose.",
        qa_text="used a spare ribbon and tied a careful double bow",
        tags={"ribbon", "knot"},
    ),
    "tape": TieGear(
        id="tape",
        label="tape",
        phrase="sticky tape",
        safe_for=set(),
        sense=1,
        success_text="{hero} pressed tape onto the {decoration}, but it did not truly hold.",
        fail_text="{hero} stuck on tape, but the damp air peeled it away at once.",
        qa_text="tried tape",
        tags={"tape"},
    ),
}

GIRL_NAMES = ["Nell", "Mira", "Lucy", "Ava", "Rosa", "Tess", "June", "Maya"]
BOY_NAMES = ["Finn", "Owen", "Leo", "Max", "Jack", "Eli", "Theo", "Ben"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in HARBORS.items():
        for plan_id in SHOW_PLANS:
            for deco_id, deco in DECORATIONS.items():
                if not hazard_at_risk(place, deco):
                    continue
                for gear_id, gear in TIE_GEAR.items():
                    if can_secure(gear, deco):
                        combos.append((place_id, plan_id, deco_id, gear_id))
    return combos


@dataclass
class StoryParams:
    place: str
    plan: str
    decoration: str
    helper: str
    gear: str
    hero_name: str
    hero_gender: str
    mate_name: str
    mate_gender: str
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
    "celebrity": [
        (
            "What is a celebrity?",
            "A celebrity is a person many people know and notice. In this story, the child only dreams of being famous for the fair, not important above others."
        )
    ],
    "harbor": [
        (
            "What is a harbor?",
            "A harbor is a safe place by the water where boats can stop. Piers, ropes, and docks are often found there."
        )
    ],
    "wind": [
        (
            "Why can wind carry a flag away?",
            "Wind pushes on light things like paper and cloth. If they are loose, the air can tug them right out of your hands."
        )
    ],
    "knot": [
        (
            "Why is a good knot useful?",
            "A good knot holds things together so they do not slip away. It helps when wind or pulling would make something loose."
        )
    ],
    "twine": [
        (
            "What is twine?",
            "Twine is a thin strong string. People use it to tie light things together."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a soft strip of cloth. It can tie light decorations, though some jobs need something stronger."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story briefly remembers something from earlier. That memory helps explain what a character does now."
        )
    ],
}
KNOWLEDGE_ORDER = ["celebrity", "harbor", "wind", "knot", "twine", "ribbon", "flashback"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    plan = f["plan"]
    decoration = f["decoration_cfg"]
    gear = f["gear"]
    return [
        'Write a short pirate tale for a 3-to-5-year-old that includes the word "celebrity", uses a flashback, and ends happily.',
        f"Tell a harbor pirate story where {hero.label} wants to feel like a celebrity during a pretend show, but {decoration.label} blows loose and a remembered lesson helps fix it.",
        f"Write a gentle story in which {mate.label} helps {hero.label} use {gear.label} to save the pirate show after a windy mishap, with a cheerful ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    helper = f["helper"]
    place = f["place_cfg"]
    plan = f["plan"]
    decoration = f["decoration_cfg"]
    gear = f["gear"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {mate.label}, two children making a pirate show at {place.label}. A grown-up had taught {hero.label} a knot lesson earlier, and that memory matters later."
        ),
        (
            "Why did the children make the pirate stage?",
            f"They wanted to put on {plan.title}, a pretend pirate show for the harbor fair. {hero.label} even hoped to feel like a celebrity for a little while because people might cheer."
        ),
        (
            "What problem happened in the middle of the story?",
            f"The wind stole the loose {decoration.label} from the little mast. That made the stage look bare and turned a proud moment into a worried one."
        ),
        (
            "What was the flashback about?",
            f"{hero.label} remembered {helper.label_word} teaching a careful knot lesson earlier. The memory mattered because it showed exactly how to solve the windy problem instead of just chasing harder."
        ),
        (
            "How did the children fix the problem?",
            f"They used {gear.label} and tied the {decoration.label} properly. The remembered lesson helped them choose a real fix, so the flag could stay up when the breeze returned."
        ),
        (
            "How do you know the ending was happy?",
            f"The crowd still came, the pirate show began, and the decoration fluttered safely above the stage. {hero.label} felt joyful in the cheers, but also proud for being careful and kind."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"celebrity", "harbor", "wind", "knot", "flashback"}
    gear = world.facts["gear"]
    if "twine" in gear.tags:
        tags.add("twine")
    if "ribbon" in gear.tags:
        tags.add("ribbon")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:11} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="sunny_dock",
        plan="star_captain",
        decoration="paper_flag",
        helper="mother",
        gear="twine",
        hero_name="Nell",
        hero_gender="girl",
        mate_name="Finn",
        mate_gender="boy",
    ),
    StoryParams(
        place="fish_pier",
        plan="moon_treasure",
        decoration="cloth_banner",
        helper="father",
        gear="twine",
        hero_name="Mira",
        hero_gender="girl",
        mate_name="Leo",
        mate_gender="boy",
    ),
    StoryParams(
        place="cove_stage",
        plan="parrot_queen",
        decoration="parrot_pennant",
        helper="aunt",
        gear="ribbon",
        hero_name="June",
        hero_gender="girl",
        mate_name="Eli",
        mate_gender="boy",
    ),
]


def explain_rejection(place: Harbor, decoration: Decoration) -> str:
    if not place.windy:
        return f"(No story: {place.label} is not windy enough to threaten {decoration.phrase}, so there is no honest problem.)"
    if not decoration.can_blow:
        return f"(No story: {decoration.phrase} would not blow away like a light flag or banner, so the pirate mishap would not happen.)"
    return "(No story: that combination has no windy flag problem.)"


def explain_gear(gear_id: str, decoration_id: str) -> str:
    gear = TIE_GEAR[gear_id]
    decoration = DECORATIONS[decoration_id]
    return (
        f"(No story: {gear.label} is not a sensible way to secure {decoration.label}. "
        f"Choose gear that can really tie it in this world.)"
    )


ASP_RULES = r"""
hazard(P,D) :- windy(P), can_blow(D).
sensible(G) :- gear(G), sense(G,S), sense_min(M), S >= M.
secures(G,D) :- supports(G,D), sensible(G).
valid(P,Pl,D,G) :- harbor(P), plan(Pl), decoration(D), gear(G), hazard(P,D), secures(G,D).

#show valid/4.
#show sensible/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in HARBORS.items():
        lines.append(asp.fact("harbor", place_id))
        if place.windy:
            lines.append(asp.fact("windy", place_id))
    for plan_id in SHOW_PLANS:
        lines.append(asp.fact("plan", plan_id))
    for deco_id, deco in DECORATIONS.items():
        lines.append(asp.fact("decoration", deco_id))
        if deco.can_blow:
            lines.append(asp.fact("can_blow", deco_id))
    for gear_id, gear in TIE_GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        lines.append(asp.fact("sense", gear_id, gear.sense))
        for deco_id in sorted(gear.safe_for):
            lines.append(asp.fact("supports", gear_id, deco_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(g for (g,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    py_sensible = {g.id for g in sensible_gears()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible gear matches ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible gear: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            generate(params)
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests succeeded.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate show, a windy mishap, a flashback, and a happy ending."
    )
    ap.add_argument("--place", choices=HARBORS)
    ap.add_argument("--plan", choices=SHOW_PLANS)
    ap.add_argument("--decoration", choices=DECORATIONS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gear", choices=TIE_GEAR)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.decoration:
        place = HARBORS[args.place]
        decoration = DECORATIONS[args.decoration]
        if not hazard_at_risk(place, decoration):
            raise StoryError(explain_rejection(place, decoration))
    if args.gear and args.decoration:
        if not can_secure(TIE_GEAR[args.gear], DECORATIONS[args.decoration]):
            raise StoryError(explain_gear(args.gear, args.decoration))
    if args.gear and TIE_GEAR[args.gear].sense < SENSE_MIN:
        raise StoryError(
            f"(No story: {TIE_GEAR[args.gear].label} is known here, but it is too weak and flimsy to count as a sensible fix.)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.plan is None or combo[1] == args.plan)
        and (args.decoration is None or combo[2] == args.decoration)
        and (args.gear is None or combo[3] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, plan_id, decoration_id, gear_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS.keys()))
    hero_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = _pick_name(rng, hero_gender)
    mate_name = _pick_name(rng, mate_gender, avoid=hero_name)
    return StoryParams(
        place=place_id,
        plan=plan_id,
        decoration=decoration_id,
        helper=helper_id,
        gear=gear_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in HARBORS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.plan not in SHOW_PLANS:
        raise StoryError(f"Unknown plan: {params.plan}")
    if params.decoration not in DECORATIONS:
        raise StoryError(f"Unknown decoration: {params.decoration}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.gear not in TIE_GEAR:
        raise StoryError(f"Unknown gear: {params.gear}")

    place = HARBORS[params.place]
    decoration = DECORATIONS[params.decoration]
    gear = TIE_GEAR[params.gear]
    if not hazard_at_risk(place, decoration):
        raise StoryError(explain_rejection(place, decoration))
    if not can_secure(gear, decoration):
        raise StoryError(explain_gear(params.gear, params.decoration))

    world = tell(
        place=place,
        plan=SHOW_PLANS[params.plan],
        decoration=decoration,
        helper_cfg=HELPERS[params.helper],
        gear=gear,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
    )
    return StorySample(
        params=params,
        story=world.render().replace(" hero ", " ").replace(" mate ", " "),
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
        sensible = asp_sensible()
        print(f"sensible gear: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, plan, decoration, gear) combos:\n")
        for place_id, plan_id, decoration_id, gear_id in combos:
            print(f"  {place_id:11} {plan_id:13} {decoration_id:14} {gear_id}")
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
            header = f"### {p.hero_name} & {p.mate_name}: {p.plan} at {p.place} ({p.decoration}, {p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
