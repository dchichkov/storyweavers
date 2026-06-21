#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/low_alls_simmer_cautionary_bravery_slice_of.py
==========================================================================

A standalone story world about a small kitchen scare: a pot is left on a low
simmer, a nearby object begins to smoke, and a child must choose between an
unsafe quick fix and the brave choice of calling a grown-up.

The stories are slice-of-life, cautionary, and grounded in a live world model.
They aim for a complete arc: ordinary home setup, a rising problem, a state-
driven turn, and an ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/low_alls_simmer_cautionary_bravery_slice_of.py
    python storyworlds/worlds/gpt-5.4/low_alls_simmer_cautionary_bravery_slice_of.py --meal soup --nearby towel
    python storyworlds/worlds/gpt-5.4/low_alls_simmer_cautionary_bravery_slice_of.py --nearby spoon
    python storyworlds/worlds/gpt-5.4/low_alls_simmer_cautionary_bravery_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/low_alls_simmer_cautionary_bravery_slice_of.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/low_alls_simmer_cautionary_bravery_slice_of.py --verify
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
SAFE_TEMPERAMENTS = {"careful", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    flammable: bool = False
    hot_surface: bool = False
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
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(
            self.type, self.type
        )
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
class Meal:
    id: str
    label: str
    pot_phrase: str
    smell: str
    ending_bowl: str
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
class HeatSource:
    id: str
    label: str
    low_phrase: str
    danger_phrase: str
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
class NearbyItem:
    id: str
    label: str
    the: str
    place: str
    first_sign: str
    flare_text: str
    severity: int
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class AdultResponse:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_heat_to_smoke(world: World) -> list[str]:
    out: list[str] = []
    stove = world.get("stove")
    nearby = world.get("nearby")
    if stove.meters["heat_on"] < THRESHOLD or nearby.flammable is False:
        return out
    if nearby.meters["too_close"] < THRESHOLD:
        return out
    sig = ("smoke", nearby.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    nearby.meters["smoke"] += 1
    world.get("room").meters["danger"] += 1
    for eid in ("hero", "sibling"):
        if eid in world.entities:
            world.get(eid).memes["fear"] += 1
    out.append("__smoke__")
    return out


def _r_smoke_to_fire(world: World) -> list[str]:
    out: list[str] = []
    nearby = world.get("nearby")
    if nearby.meters["smoke"] < THRESHOLD:
        return out
    if nearby.meters["untended"] < THRESHOLD:
        return out
    sig = ("fire", nearby.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    nearby.meters["burning"] += 1
    world.get("room").meters["danger"] += 1
    for eid in ("hero", "sibling"):
        if eid in world.entities:
            world.get(eid).memes["fear"] += 1
    out.append("__fire__")
    return out


CAUSAL_RULES = [
    Rule(name="heat_to_smoke", tag="physical", apply=_r_heat_to_smoke),
    Rule(name="smoke_to_fire", tag="physical", apply=_r_smoke_to_fire),
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


def hazard_at_risk(heat: HeatSource, nearby: NearbyItem) -> bool:
    return nearby.flammable and nearby.severity > 0 and bool(heat.label)


def sensible_responses() -> list[AdultResponse]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(nearby: NearbyItem, delay: int) -> int:
    return nearby.severity + delay


def is_contained(response: AdultResponse, nearby: NearbyItem, delay: int) -> bool:
    return response.power >= fire_severity(nearby, delay)


def would_call_for_help(temperament: str, sibling_age: int) -> bool:
    return temperament in SAFE_TEMPERAMENTS or sibling_age <= 3


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("nearby").meters["too_close"] = 1.0
    sim.get("nearby").meters["untended"] = 1.0
    propagate(sim, narrate=False)
    nearby = sim.get("nearby")
    return {
        "smoke": nearby.meters["smoke"] >= THRESHOLD,
        "fire": nearby.meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def kitchen_setup(world: World, hero: Entity, sibling: Entity, parent: Entity,
                  meal: Meal, heat: HeatSource, nearby: NearbyItem) -> None:
    hero.memes["calm"] += 1
    sibling.memes["hunger"] += 1
    world.say(
        f"After school, {parent.label_word} stood in the kitchen with {meal.pot_phrase} on the stove. "
        f"The burner was turned {heat.low_phrase}, and the whole room smelled {meal.smell}."
    )
    world.say(
        f"{hero.id} sat at the table with {sibling.id} while the pot began to simmer. "
        f'"Alls done yet?" {sibling.id} asked, swinging small feet under the chair.'
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled. "Not yet. Food on the stove needs patient eyes and patient hands."'
    )
    world.facts["used_words"] = {"low": True, "alls": True, "simmer": True}


def parent_steps_away(world: World, parent: Entity, nearby: NearbyItem) -> None:
    world.say(
        f"Then {parent.label_word} stepped only a few paces away to the counter to slice fruit and set out bowls."
    )
    world.say(
        f"Near the stove, {nearby.the} rested {nearby.place}."
    )


def notice_sign(world: World, hero: Entity, nearby: NearbyItem) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.get("nearby").meters["too_close"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"After a minute, {hero.id} noticed {nearby.first_sign}."
    )


def unsafe_reach(world: World, hero: Entity, sibling: Entity, nearby: NearbyItem) -> None:
    hero.memes["defiance"] += 1
    hero.memes["fear"] += 1
    world.get("nearby").meters["untended"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} felt a quick jump of worry and reached toward {nearby.the}, wanting to fix it alone before anyone saw."
    )
    if world.get("nearby").meters["burning"] >= THRESHOLD:
        world.say(
            f"But that made everything worse. {nearby.flare_text}"
        )
    else:
        world.say(
            f"The stove still hissed softly, and the kitchen did not feel safe."
        )
    world.say(f'"{parent.label_word.upper()}!" {sibling.id} cried.')


def brave_call(world: World, hero: Entity, sibling: Entity, parent: Entity, nearby: NearbyItem) -> None:
    hero.memes["bravery"] += 1
    hero.memes["fear"] += 1
    world.get("nearby").meters["untended"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id}'s heart thumped, but {hero.pronoun()} remembered the rule about hot things."
    )
    world.say(
        f'"{parent.label_word.capitalize()}, please come now!" {hero.id} called. "{nearby.The} is too close to the stove!"'
    )
    if world.get("nearby").meters["burning"] >= THRESHOLD:
        world.say(
            f"By the time {parent.label_word} turned, {nearby.flare_text.lower()}"
        )
    else:
        world.say(
            f"{sibling.id} scooted back from the table and watched with wide eyes."
        )


def adult_rescue(world: World, parent: Entity, response: AdultResponse,
                 nearby_cfg: NearbyItem) -> None:
    world.get("stove").meters["heat_on"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.get("nearby").meters["burning"] = 0.0
    world.get("nearby").meters["smoke"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} moved at once and {response.text.replace('{item}', nearby_cfg.label)}."
    )


def adult_fail(world: World, parent: Entity, response: AdultResponse,
               nearby_cfg: NearbyItem) -> None:
    world.get("room").meters["burning"] += 1
    world.say(
        f"{parent.label_word.capitalize()} tried to help and {response.fail.replace('{item}', nearby_cfg.label)}."
    )
    world.say(
        "Smoke rolled up to the ceiling, and the kitchen suddenly felt much too small."
    )


def lesson_safe(world: World, parent: Entity, hero: Entity, sibling: Entity,
                meal: Meal) -> None:
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    sibling.memes["relief"] += 1
    world.say(
        f"Then {parent.label_word} knelt beside the table and held both children close."
    )
    world.say(
        f'"You did the brave thing by calling me," {parent.pronoun()} said. "Brave does not mean touching danger. Brave means getting help before a small problem grows."'
    )
    world.say(
        f"A little later, the food was ready after all. They ate {meal.ending_bowl} together, and the stove stayed only a place for grown-up hands."
    )


def lesson_after_loss(world: World, parent: Entity, hero: Entity, sibling: Entity,
                      meal: Meal) -> None:
    hero.memes["lesson"] += 1
    hero.memes["sadness"] += 1
    sibling.memes["sadness"] += 1
    world.say(
        f"Outside on the front step, {parent.label_word} wrapped a blanket around the children until the smoke was gone."
    )
    world.say(
        f'"I am glad you are safe," {parent.pronoun()} said softly. "Next time, call right away. Hot kitchens do not need quick hands. They need careful ones."'
    )
    world.say(
        f"That night there was no {meal.ending_bowl}, only crackers and quiet voices. Even so, {hero.id} never forgot what a tiny kitchen trouble could become."
    )


def safer_habit(world: World, parent: Entity, hero: Entity, sibling: Entity) -> None:
    hero.memes["joy"] += 1
    sibling.memes["joy"] += 1
    world.say(
        f"The next evening, when a pot simmered again on low, {hero.id} pulled {sibling.id}'s chair back from the stove all by {hero.pronoun('object')}self."
    )
    world.say(
        f'"We wait here," {hero.pronoun()} said, and this time both children did.'
    )


def tell(meal: Meal, heat: HeatSource, nearby: NearbyItem, response: AdultResponse,
         hero_name: str = "Nora", hero_gender: str = "girl",
         sibling_name: str = "Ben", sibling_gender: str = "boy",
         parent_type: str = "mother", temperament: str = "careful",
         delay: int = 0, sibling_age: int = 3) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[temperament],
        attrs={"name": hero_name},
    ))
    sibling = world.add(Entity(
        id="sibling",
        kind="character",
        type=sibling_gender,
        label=sibling_name,
        role="sibling",
        attrs={"name": sibling_name, "age": sibling_age},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    stove = world.add(Entity(
        id="stove",
        type="stove",
        label=heat.label,
        hot_surface=True,
    ))
    pot = world.add(Entity(
        id="pot",
        type="pot",
        label="pot",
    ))
    nearby_ent = world.add(Entity(
        id="nearby",
        type="nearby",
        label=nearby.label,
        flammable=nearby.flammable,
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="kitchen",
    ))
    stove.meters["heat_on"] = 1.0
    nearby_ent.meters["too_close"] = 0.0
    nearby_ent.meters["untended"] = 0.0
    nearby_ent.meters["smoke"] = 0.0
    nearby_ent.meters["burning"] = 0.0
    room.meters["danger"] = 0.0

    kitchen_setup(world, hero, sibling, parent, meal, heat, nearby)
    world.para()
    parent_steps_away(world, parent, nearby)
    notice_sign(world, hero, nearby)

    brave = would_call_for_help(temperament, sibling_age)
    world.para()
    if brave:
        brave_call(world, hero, sibling, parent, nearby)
        actual_delay = delay
    else:
        unsafe_reach(world, hero, sibling, nearby)
        actual_delay = delay + 1

    contained = is_contained(response, nearby, actual_delay)

    world.para()
    if contained:
        adult_rescue(world, parent, response, nearby)
        lesson_safe(world, parent, hero, sibling, meal)
        world.para()
        safer_habit(world, parent, hero, sibling)
    else:
        adult_fail(world, parent, response, nearby)
        lesson_after_loss(world, parent, hero, sibling, meal)

    outcome = "contained" if contained else "burned"
    if brave and world.get("nearby").meters["burning"] < THRESHOLD and outcome == "contained":
        outcome = "called_early"

    world.facts.update(
        hero=hero,
        sibling=sibling,
        parent=parent,
        meal=meal,
        heat=heat,
        nearby_cfg=nearby,
        nearby=nearby_ent,
        response=response,
        brave_call=brave,
        delay=actual_delay,
        outcome=outcome,
        ignited=nearby_ent.meters["burning"] >= THRESHOLD or ("fire", "nearby") in {(a, b) for (a, b, *_) in [tuple(x) if isinstance(x, tuple) else (x,) for x in []]},
        sibling_age=sibling_age,
    )
    world.facts["ignited"] = ("fire", "nearby") in world.fired
    return world


MEALS = {
    "soup": Meal(
        id="soup",
        label="tomato soup",
        pot_phrase="a red pot of tomato soup",
        smell="warm and herby",
        ending_bowl="soup with toast cut into squares",
        tags={"soup", "kitchen"},
    ),
    "oatmeal": Meal(
        id="oatmeal",
        label="cinnamon oatmeal",
        pot_phrase="a silver pot of cinnamon oatmeal",
        smell="sweet and soft",
        ending_bowl="oatmeal with banana slices",
        tags={"oatmeal", "kitchen"},
    ),
    "beans": Meal(
        id="beans",
        label="beans",
        pot_phrase="a small pot of beans",
        smell="savory and homey",
        ending_bowl="beans in warm bowls",
        tags={"beans", "kitchen"},
    ),
}

HEATS = {
    "gas": HeatSource(
        id="gas",
        label="gas stove",
        low_phrase="to a low blue flame",
        danger_phrase="a real flame",
        tags={"stove", "heat"},
    ),
    "electric": HeatSource(
        id="electric",
        label="electric stove",
        low_phrase="to low heat",
        danger_phrase="a hot burner",
        tags={"stove", "heat"},
    ),
}

NEARBY = {
    "towel": NearbyItem(
        id="towel",
        label="dish towel",
        the="the dish towel",
        place="over the oven handle",
        first_sign="a thin gray thread of smoke curling from the edge of the dish towel",
        flare_text="The dish towel flashed orange at one corner.",
        severity=2,
        flammable=True,
        tags={"towel", "cloth", "fire"},
    ),
    "recipe_card": NearbyItem(
        id="recipe_card",
        label="recipe card",
        the="the recipe card",
        place="propped beside the stove",
        first_sign="the corner of the recipe card turning brown and curling inward",
        flare_text="The recipe card gave a quick papery flare.",
        severity=1,
        flammable=True,
        tags={"paper", "recipe", "fire"},
    ),
    "paper_bag": NearbyItem(
        id="paper_bag",
        label="paper grocery bag",
        the="the paper grocery bag",
        place="on the floor beside the stove",
        first_sign="a sharp burnt smell drifting from the paper grocery bag",
        flare_text="The paper grocery bag caught with a crackly little flame.",
        severity=3,
        flammable=True,
        tags={"paper", "bag", "fire"},
    ),
    "spoon": NearbyItem(
        id="spoon",
        label="wooden spoon",
        the="the wooden spoon",
        place="on a spoon rest by the wall",
        first_sign="nothing dangerous at all",
        flare_text="Nothing flared.",
        severity=0,
        flammable=False,
        tags={"spoon"},
    ),
}

RESPONSES = {
    "turn_and_move": AdultResponse(
        id="turn_and_move",
        sense=3,
        power=3,
        text="turned off the burner, moved the {item} away from the heat, and opened the window",
        fail="turned off the burner and grabbed at the {item}, but the flame had already spread too fast",
        qa_text="turned off the burner and moved the danger away from the heat",
        tags={"call_adult", "window", "burner"},
    ),
    "lid_and_move": AdultResponse(
        id="lid_and_move",
        sense=3,
        power=2,
        text="slid a lid over the pot, shut off the heat, and whisked the {item} into the sink",
        fail="reached for a lid and the {item}, but the kitchen was already too smoky and hot",
        qa_text="shut off the heat and moved the danger into the sink",
        tags={"call_adult", "sink", "burner"},
    ),
    "wave_towel": AdultResponse(
        id="wave_towel",
        sense=1,
        power=1,
        text="waved the {item} in the air, hoping the smoke would go away",
        fail="waved at the {item}, but the extra air only fed the trouble",
        qa_text="waved it in the air",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lucy", "Ava", "Ella", "Ruby", "Lena", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Finn", "Noah", "Eli", "Theo", "Max"]
TEMPERAMENTS = ["careful", "steady", "thoughtful", "curious", "bold", "hasty"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for meal_id in MEALS:
        for heat_id, heat in HEATS.items():
            for nearby_id, nearby in NEARBY.items():
                if hazard_at_risk(heat, nearby):
                    combos.append((meal_id, heat_id, nearby_id))
    return combos


@dataclass
class StoryParams:
    meal: str
    heat: str
    nearby: str
    response: str
    hero: str
    hero_gender: str
    sibling: str
    sibling_gender: str
    parent: str
    temperament: str
    delay: int = 0
    sibling_age: int = 3
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
    "stove": [
        (
            "Why should children be careful around a stove?",
            "A stove can stay very hot even when the food looks calm. A child should never touch it without a grown-up."
        )
    ],
    "simmer": [
        (
            "What does simmer mean?",
            "Simmer means food is cooking gently with small bubbles instead of a big rolling boil. It still stays hot enough to burn."
        )
    ],
    "cloth": [
        (
            "Why can a dish towel be dangerous near the stove?",
            "A dish towel is cloth, and cloth can burn if it gets too close to heat or flame. That is why grown-ups keep towels away from burners."
        )
    ],
    "paper": [
        (
            "Why is paper risky near a hot stove?",
            "Paper dries out and catches fire quickly when it gets too close to heat. Even a small corner can start smoking first."
        )
    ],
    "call_adult": [
        (
            "What is a brave thing to do when something hot looks unsafe?",
            "Call a grown-up right away and step back. Brave choices keep people safe instead of pretending danger is small."
        )
    ],
    "burner": [
        (
            "What does turning off a burner do?",
            "Turning off a burner stops adding more heat. That can keep a small problem from getting bigger."
        )
    ],
}
KNOWLEDGE_ORDER = ["stove", "simmer", "cloth", "paper", "call_adult", "burner"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = display_name(f["hero"])
    sibling = display_name(f["sibling"])
    meal = f["meal"]
    nearby = f["nearby_cfg"]
    outcome = f["outcome"]
    if outcome == "burned":
        return [
            f'Write a slice-of-life cautionary story for a 3-to-5-year-old where a pot begins to simmer on low and a nearby {nearby.label} causes trouble in the kitchen.',
            f"Tell a home story where {hero} wants to help too quickly, but that choice makes a small stove problem bigger.",
            f'Write a simple bravery story that teaches children to call for help instead of touching danger, and include the word "simmer".',
        ]
    return [
        f'Write a slice-of-life cautionary story for a 3-to-5-year-old where {hero} and {sibling} wait for {meal.label} while it simmers on low.',
        f"Tell a kitchen story where a child notices danger, feels scared, and bravely calls a grown-up instead of trying to fix it alone.",
        f'Write a gentle home story that includes the words "low", "alls", and "simmer", and ends with a safer family habit.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    parent = f["parent"]
    meal = f["meal"]
    nearby = f["nearby_cfg"]
    response = f["response"]
    hero_name = display_name(hero)
    sibling_name = display_name(sibling)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, {sibling_name}, and their {pw} in the kitchen. They were waiting for {meal.label} to finish cooking."
        ),
        (
            "What was cooking at the start?",
            f"{meal.label.capitalize()} was cooking on the stove on low heat. The pot had begun to simmer, which means it was gentle but still very hot."
        ),
        (
            f"What did {sibling_name} say while they waited?",
            f'{sibling_name} asked, "Alls done yet?" That small question made the scene feel ordinary before the kitchen scare began.'
        ),
        (
            f"What danger did {hero_name} notice?",
            f"{hero_name} noticed trouble with {nearby.the} near the stove. That mattered because {nearby.label} could start smoking and then catch if nobody helped."
        ),
    ]
    if f["brave_call"]:
        qa.append(
            (
                f"How was {hero_name} brave?",
                f"{hero_name} felt scared but called for {pw} instead of reaching into danger. That was brave because asking for help stopped a hot problem from being handled with unsafe hands."
            )
        )
    else:
        qa.append(
            (
                f"Why was {hero_name}'s first choice unsafe?",
                f"{hero_name} tried to fix the problem alone while feeling rushed. That made the danger worse because hot kitchens and flammable things need grown-up help, not quick grabbing."
            )
        )
    if f["outcome"] == "burned":
        qa.append(
            (
                "How did the story end?",
                f"It ended with a sad lesson after the kitchen filled with smoke. Everyone stayed safe, but the family lost their supper and learned that waiting to call for help can let a small problem grow."
            )
        )
    else:
        qa.append(
            (
                f"How did {pw} fix the problem?",
                f"{pw.capitalize()} {response.qa_text.replace('{item}', nearby.label)}. Acting quickly changed the kitchen from scary back to safe."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"By the end, the children had a new habit: they waited back from the stove and let the grown-up handle hot things. The final image shows that the family did not just feel better; they behaved more safely too."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"stove", "simmer", "call_adult", "burner"}
    nearby = world.facts["nearby_cfg"]
    if "cloth" in nearby.tags or nearby.id == "towel":
        tags.add("cloth")
    if "paper" in nearby.tags:
        tags.add("paper")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if e.flammable:
            bits.append("flammable=True")
        if e.hot_surface:
            bits.append("hot_surface=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        meal="soup",
        heat="gas",
        nearby="towel",
        response="turn_and_move",
        hero="Nora",
        hero_gender="girl",
        sibling="Ben",
        sibling_gender="boy",
        parent="mother",
        temperament="careful",
        delay=0,
        sibling_age=3,
    ),
    StoryParams(
        meal="oatmeal",
        heat="electric",
        nearby="recipe_card",
        response="lid_and_move",
        hero="Leo",
        hero_gender="boy",
        sibling="Mia",
        sibling_gender="girl",
        parent="father",
        temperament="steady",
        delay=0,
        sibling_age=4,
    ),
    StoryParams(
        meal="beans",
        heat="gas",
        nearby="paper_bag",
        response="lid_and_move",
        hero="Max",
        hero_gender="boy",
        sibling="Ruby",
        sibling_gender="girl",
        parent="mother",
        temperament="bold",
        delay=1,
        sibling_age=5,
    ),
    StoryParams(
        meal="soup",
        heat="electric",
        nearby="paper_bag",
        response="turn_and_move",
        hero="Ella",
        hero_gender="girl",
        sibling="Theo",
        sibling_gender="boy",
        parent="father",
        temperament="thoughtful",
        delay=0,
        sibling_age=2,
    ),
]


def explain_rejection(heat: HeatSource, nearby: NearbyItem) -> str:
    if not nearby.flammable:
        return (
            f"(No story: {nearby.the} is not a real stove hazard here, so the scene has no honest kitchen emergency. "
            f"Pick a nearby item like a towel, recipe card, or paper bag.)"
        )
    return (
        f"(No story: {nearby.the} does not make a plausible hazard with the chosen stove setup.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    brave = would_call_for_help(params.temperament, params.sibling_age)
    actual_delay = params.delay if brave else params.delay + 1
    contained = is_contained(RESPONSES[params.response], NEARBY[params.nearby], actual_delay)
    if contained and brave and actual_delay == 0:
        return "called_early"
    return "contained" if contained else "burned"


ASP_RULES = r"""
hazard(H, N) :- heat(H), nearby(N), flammable(N), severity(N, S), S > 0.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Ml, H, N) :- meal(Ml), heat(H), nearby(N), hazard(H, N).

safe_temperament(T) :- temperament(T), tagged_safe(T).
brave_call :- chosen_temperament(T), safe_temperament(T).
brave_call :- sibling_age(A), A <= 3.

actual_delay(D) :- chosen_delay(D), brave_call.
actual_delay(D + 1) :- chosen_delay(D), not brave_call.

contained :- chosen_nearby(N), chosen_response(R),
             power(R, P), actual_delay(D), severity(N, S), P >= S + D.

outcome(called_early) :- brave_call, actual_delay(0), contained.
outcome(contained) :- contained, not outcome(called_early).
outcome(burned) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for meal_id in MEALS:
        lines.append(asp.fact("meal", meal_id))
    for heat_id in HEATS:
        lines.append(asp.fact("heat", heat_id))
    for nearby_id, nearby in NEARBY.items():
        lines.append(asp.fact("nearby", nearby_id))
        if nearby.flammable:
            lines.append(asp.fact("flammable", nearby_id))
        lines.append(asp.fact("severity", nearby_id, nearby.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for t in TEMPERAMENTS:
        lines.append(asp.fact("temperament", t))
    for t in sorted(SAFE_TEMPERAMENTS):
        lines.append(asp.fact("tagged_safe", t))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_nearby", params.nearby),
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_temperament", params.temperament),
            asp.fact("chosen_delay", params.delay),
            asp.fact("sibling_age", params.sibling_age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a low simmer, a kitchen warning, and the brave choice to call for help."
    )
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--heat", choices=HEATS)
    ap.add_argument("--nearby", choices=NEARBY)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time before the grown-up reaches the stove")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.nearby:
        nearby = NEARBY[args.nearby]
        heat = HEATS[args.heat] if args.heat else next(iter(HEATS.values()))
        if not hazard_at_risk(heat, nearby):
            raise StoryError(explain_rejection(heat, nearby))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.meal is None or c[0] == args.meal)
        and (args.heat is None or c[1] == args.heat)
        and (args.nearby is None or c[2] == args.nearby)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    meal, heat, nearby = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero, hero_gender = _pick_child(rng)
    sibling, sibling_gender = _pick_child(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    temperament = rng.choice(TEMPERAMENTS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    sibling_age = rng.randint(2, 6)
    return StoryParams(
        meal=meal,
        heat=heat,
        nearby=nearby,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        sibling=sibling,
        sibling_gender=sibling_gender,
        parent=parent,
        temperament=temperament,
        delay=delay,
        sibling_age=sibling_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.meal not in MEALS:
        raise StoryError(f"(Unknown meal: {params.meal})")
    if params.heat not in HEATS:
        raise StoryError(f"(Unknown heat source: {params.heat})")
    if params.nearby not in NEARBY:
        raise StoryError(f"(Unknown nearby item: {params.nearby})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(Unknown temperament: {params.temperament})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(HEATS[params.heat], NEARBY[params.nearby]):
        raise StoryError(explain_rejection(HEATS[params.heat], NEARBY[params.nearby]))

    world = tell(
        meal=MEALS[params.meal],
        heat=HEATS[params.heat],
        nearby=NEARBY[params.nearby],
        response=RESPONSES[params.response],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        sibling_name=params.sibling,
        sibling_gender=params.sibling_gender,
        parent_type=params.parent,
        temperament=params.temperament,
        delay=params.delay,
        sibling_age=params.sibling_age,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", "").replace("sibling", ""),
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (meal, heat, nearby) combos:\n")
        for meal, heat, nearby in combos:
            print(f"  {meal:8} {heat:8} {nearby}")
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
            header = f"### {p.hero} and {p.sibling}: {p.meal}, {p.nearby}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
