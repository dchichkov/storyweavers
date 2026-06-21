#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trouser_malfunction_inner_monologue_quest_sound_effects.py
=====================================================================================

A standalone story world for a small fable-like domain: a child sets out on a
quest, a trouser malfunction threatens the mission, an inner monologue helps the
child reason about the danger, and a wise helper offers the right repair.

The world model keeps both physical meters and emotional memes. A small causal
engine turns trouser trouble into delay, worry, and risk to the quest parcel.
The story prose follows those state changes instead of filling in one frozen
template.

Run it
------
    python storyworlds/worlds/gpt-5.4/trouser_malfunction_inner_monologue_quest_sound_effects.py
    python storyworlds/worlds/gpt-5.4/trouser_malfunction_inner_monologue_quest_sound_effects.py --route hill_path --malfunction torn_pocket
    python storyworlds/worlds/gpt-5.4/trouser_malfunction_inner_monologue_quest_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4/trouser_malfunction_inner_monologue_quest_sound_effects.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/trouser_malfunction_inner_monologue_quest_sound_effects.py --asp
    python storyworlds/worlds/gpt-5.4/trouser_malfunction_inner_monologue_quest_sound_effects.py --verify
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
        female = {"girl", "hen", "mother", "she-fox", "doe"}
        male = {"boy", "father", "he-fox", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Route:
    id: str
    place: str
    opening: str
    obstacle: str
    goal_place: str
    steep: bool = False
    snaggy: bool = False
    long_walk: bool = True
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
class Parcel:
    id: str
    label: str
    phrase: str
    recipient: str
    purpose: str
    carry_mode: str
    arrival_image: str
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
class Malfunction:
    id: str
    label: str
    sound: str
    discovery: str
    inward: str
    problem: str
    threatens_pocket: bool = False
    threatens_stride: bool = False
    threatens_snag: bool = False
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
class Fix:
    id: str
    label: str
    helper_name: str
    helper_type: str
    helper_place: str
    action: str
    flourish: str
    solves: set[str] = field(default_factory=set)
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


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


def _r_pocket_risk(world: World) -> list[str]:
    hero = world.get("hero")
    trousers = world.get("trousers")
    parcel = world.get("parcel")
    if world.facts["walking"] < THRESHOLD:
        return []
    if trousers.meters["pocket_open"] < THRESHOLD:
        return []
    if parcel.attrs.get("carry_mode") != "pocket":
        return []
    sig = ("pocket_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parcel.meters["at_risk"] += 1
    hero.memes["worry"] += 1
    return ["__risk__"]


def _r_slip_delay(world: World) -> list[str]:
    hero = world.get("hero")
    trousers = world.get("trousers")
    route = world.get("route")
    if world.facts["walking"] < THRESHOLD:
        return []
    if trousers.meters["slipping"] < THRESHOLD:
        return []
    sig = ("slip_delay",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["delay"] += 1
    route.meters["delay"] += 1
    hero.memes["worry"] += 1
    return ["__delay__"]


def _r_snag_delay(world: World) -> list[str]:
    hero = world.get("hero")
    trousers = world.get("trousers")
    route = world.get("route")
    if world.facts["walking"] < THRESHOLD:
        return []
    if trousers.meters["dragging"] < THRESHOLD:
        return []
    if not route.attrs.get("snaggy") and not route.attrs.get("steep"):
        return []
    sig = ("snag_delay",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trousers.meters["snagged"] += 1
    hero.meters["delay"] += 1
    route.meters["delay"] += 1
    hero.memes["worry"] += 1
    return ["__snag__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="pocket_risk", tag="physical", apply=_r_pocket_risk),
    Rule(name="slip_delay", tag="physical", apply=_r_slip_delay),
    Rule(name="snag_delay", tag="physical", apply=_r_snag_delay),
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


def quest_at_risk(route: Route, parcel: Parcel, malfunction: Malfunction) -> bool:
    if malfunction.threatens_pocket and parcel.carry_mode == "pocket":
        return True
    if malfunction.threatens_stride and route.long_walk:
        return True
    if malfunction.threatens_snag and (route.snaggy or route.steep):
        return True
    return False


def compatible_fix(malfunction: Malfunction, fix: Fix) -> bool:
    return malfunction.id in fix.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for route_id, route in ROUTES.items():
        for parcel_id, parcel in PARCELS.items():
            for mal_id, malfunction in MALFUNCTIONS.items():
                if not quest_at_risk(route, parcel, malfunction):
                    continue
                for fix_id, fix in FIXES.items():
                    if compatible_fix(malfunction, fix):
                        out.append((route_id, parcel_id, mal_id, fix_id))
    return sorted(out)


def explain_rejection(route: Route, parcel: Parcel, malfunction: Malfunction) -> str:
    if malfunction.threatens_pocket and parcel.carry_mode != "pocket":
        return (
            f"(No story: {parcel.phrase} is carried by hand, so a torn pocket would not "
            f"threaten the quest on {route.place}. Pick a pocket-sized parcel instead.)"
        )
    if malfunction.threatens_snag and not (route.snaggy or route.steep):
        return (
            f"(No story: a dragging trouser hem needs brambles or hard climbing to cause "
            f"real trouble, and {route.place} does not provide that obstacle.)"
        )
    if malfunction.threatens_stride and not route.long_walk:
        return (
            f"(No story: a loose waist matters on a real walk, but this route is too short "
            f"for the malfunction to shape a quest.)"
        )
    return "(No story: this malfunction does not honestly endanger this quest.)"


def explain_fix(malfunction: Malfunction, fix: Fix) -> str:
    return (
        f"(Refusing fix '{fix.id}': {fix.label} does not solve a {malfunction.label}. "
        f"Choose a helper whose repair fits the trouble.)"
    )


def _set_malfunction_state(trousers: Entity, malfunction: Malfunction) -> None:
    trousers.meters["pocket_open"] = 1.0 if malfunction.threatens_pocket else 0.0
    trousers.meters["slipping"] = 1.0 if malfunction.threatens_stride else 0.0
    trousers.meters["dragging"] = 1.0 if malfunction.threatens_snag else 0.0
    trousers.meters["mended"] = 0.0
    trousers.meters["belted"] = 0.0
    trousers.meters["hemmed"] = 0.0
    trousers.meters["snagged"] = 0.0


def predict_trouble(route: Route, parcel: Parcel, malfunction: Malfunction) -> dict:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type="fox", label="the fox"))
    route_ent = world.add(Entity(id="route", type="route", label=route.place, attrs={
        "snaggy": route.snaggy,
        "steep": route.steep,
        "long_walk": route.long_walk,
    }))
    parcel_ent = world.add(Entity(id="parcel", type="parcel", label=parcel.label, attrs={
        "carry_mode": parcel.carry_mode,
    }))
    trousers = world.add(Entity(id="trousers", type="trouser", label="trouser"))
    world.facts["walking"] = 1.0
    hero.meters["delay"] = 0.0
    route_ent.meters["delay"] = 0.0
    parcel_ent.meters["at_risk"] = 0.0
    hero.memes["worry"] = 0.0
    _set_malfunction_state(trousers, malfunction)
    propagate(world, narrate=False)
    return {
        "delay": hero.meters["delay"],
        "parcel_risk": parcel_ent.meters["at_risk"],
        "snagged": trousers.meters["snagged"],
    }


def opening(world: World, hero: Entity, elder: Entity, route: Route, parcel: Parcel) -> None:
    hero.memes["duty"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"In a quiet valley, {hero.id} the young fox was given {parcel.phrase} to carry "
        f"to {parcel.recipient} at {route.goal_place}. {parcel.purpose}"
    )
    world.say(
        f'Old {elder.id}, who had seen many seasons, said, "Small errands make strong hearts '
        f'when they are done faithfully."'
    )
    world.say(route.opening)


def set_out(world: World, hero: Entity, route: Route, parcel: Parcel) -> None:
    carry_text = {
        "pocket": f"He tucked {parcel.label} into his trouser pocket.",
        "hand": f"He held {parcel.label} carefully in both paws.",
    }[parcel.carry_mode]
    world.say(
        f"{hero.id} set out along {route.place}, meaning to walk straight and quick. {carry_text}"
    )
    world.say(f"The road promised {route.obstacle}.")


def trouble(world: World, hero: Entity, trousers: Entity, malfunction: Malfunction) -> None:
    world.facts["walking"] = 1.0
    world.say(
        f'{malfunction.sound} went his trouser at the first troublesome turn. {malfunction.discovery}'
    )
    propagate(world, narrate=False)
    if trousers.meters["pocket_open"] >= THRESHOLD:
        world.say("He clapped a paw over the pocket at once.")
    if trousers.meters["slipping"] >= THRESHOLD:
        world.say("He grabbed the waistband before it could slide lower.")
    if trousers.meters["dragging"] >= THRESHOLD:
        world.say("He lifted the cloth before it could kiss the mud and thorns.")


def inner_monologue(world: World, hero: Entity, route: Route, parcel: Parcel,
                    malfunction: Malfunction) -> None:
    pred = predict_trouble(route, parcel, malfunction)
    world.facts["predicted_delay"] = pred["delay"]
    world.facts["predicted_parcel_risk"] = pred["parcel_risk"]
    world.facts["predicted_snagged"] = pred["snagged"]
    world.say(
        f'Inside his own head, {hero.id} thought, "{malfunction.inward}"'
    )
    if pred["parcel_risk"] >= THRESHOLD:
        world.say(
            f'He thought again, "If I hurry foolishly, {parcel.label} may tumble out before I reach '
            f'{parcel.recipient}."'
        )
    elif pred["snagged"] >= THRESHOLD:
        world.say(
            f'He thought again, "If I drag on, this cloth will catch on root or thorn, and my feet '
            f'will lose their honest pace."'
        )
    elif pred["delay"] >= THRESHOLD:
        world.say(
            f'He thought again, "A quest goes slowly when a traveler spends every step rescuing '
            f'his clothes."'
        )
    hero.memes["prudence"] += 1


def choose_helper(world: World, hero: Entity, fix: Fix) -> Entity:
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=fix.helper_type,
        label=fix.helper_name,
        role="helper",
    ))
    world.say(
        f"So {hero.id} turned his steps toward {fix.helper_place}, for even a small hero may seek "
        f"wise hands on a true quest."
    )
    world.say(
        f"There he found {fix.helper_name}, who listened without laughing."
    )
    return helper


def repair(world: World, hero: Entity, helper: Entity, trousers: Entity, fix: Fix,
           malfunction: Malfunction) -> None:
    hero.memes["hope"] += 1
    helper.memes["kindness"] += 1
    if malfunction.id == "torn_pocket":
        trousers.meters["pocket_open"] = 0.0
        trousers.meters["mended"] += 1
    elif malfunction.id == "loose_drawstring":
        trousers.meters["slipping"] = 0.0
        trousers.meters["belted"] += 1
    elif malfunction.id == "dragging_hem":
        trousers.meters["dragging"] = 0.0
        trousers.meters["hemmed"] += 1
    world.fired.clear()
    world.facts["walking"] = 0.0
    world.say(
        f'{fix.flourish} {fix.helper_name} {fix.action}.'
    )
    world.say(
        f'"A quest does not grow smaller because you mend before you move," {helper.label} said.'
    )
    hero.memes["relief"] += 1
    hero.memes["resolve"] += 1
    world.facts["repair_done"] = fix.id


def resume(world: World, hero: Entity, route_ent: Entity, parcel: Entity, trousers: Entity) -> None:
    world.facts["walking"] = 1.0
    world.fired.clear()
    hero.meters["delay"] = 0.0
    route_ent.meters["delay"] = 0.0
    parcel.meters["at_risk"] = 0.0
    trousers.meters["snagged"] = 0.0
    propagate(world, narrate=False)
    hero.memes["confidence"] += 1
    world.say(
        f"{hero.id} thanked the helper, straightened his back, and took the road again."
    )
    if trousers.meters["mended"] >= THRESHOLD:
        world.say("Now the pocket sat neat and close, with nothing eager to escape.")
    if trousers.meters["belted"] >= THRESHOLD:
        world.say("Now the waistband held firm, and his steps could mind the road instead of his clothes.")
    if trousers.meters["hemmed"] >= THRESHOLD:
        world.say("Now the cloth stayed above root and thorn, and the path could no longer nibble at it.")


def arrival(world: World, hero: Entity, parcel: Parcel, route: Route) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"By and by he came to {route.goal_place}, where {parcel.recipient} was waiting."
    )
    world.say(
        f"He delivered {parcel.label} safely, and {parcel.arrival_image}"
    )
    world.say(
        "So the valley remembered that day: the clever traveler is not the one who never meets trouble, "
        "but the one who listens to sense before pride."
    )


def tell(route: Route, parcel: Parcel, malfunction: Malfunction, fix: Fix,
         hero_name: str = "Pip", elder_name: str = "Moss") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="fox",
        label=hero_name,
        role="hero",
        traits=["young", "earnest"],
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type="tortoise",
        label=elder_name,
        role="elder",
        traits=["patient", "wise"],
    ))
    route_ent = world.add(Entity(
        id="route",
        type="route",
        label=route.place,
        attrs={"snaggy": route.snaggy, "steep": route.steep, "long_walk": route.long_walk},
    ))
    parcel_ent = world.add(Entity(
        id="parcel",
        type="parcel",
        label=parcel.label,
        phrase=parcel.phrase,
        attrs={"carry_mode": parcel.carry_mode},
    ))
    trousers = world.add(Entity(
        id="trousers",
        type="trouser",
        label="trouser",
        phrase="a pair of brown travel trousers",
    ))

    world.facts["walking"] = 0.0
    world.facts["repair_done"] = ""
    world.facts["predicted_delay"] = 0.0
    world.facts["predicted_parcel_risk"] = 0.0
    world.facts["predicted_snagged"] = 0.0
    route_ent.meters["delay"] = 0.0
    parcel_ent.meters["at_risk"] = 0.0
    hero.meters["delay"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["prudence"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["resolve"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["confidence"] = 0.0
    _set_malfunction_state(trousers, malfunction)

    opening(world, hero, elder, route, parcel)
    set_out(world, hero, route, parcel)

    world.para()
    trouble(world, hero, trousers, malfunction)
    inner_monologue(world, hero, route, parcel, malfunction)

    world.para()
    helper = choose_helper(world, hero, fix)
    repair(world, hero, helper, trousers, fix, malfunction)

    world.para()
    resume(world, hero, route_ent, parcel_ent, trousers)
    arrival(world, hero, parcel, route)

    world.facts.update(
        hero=hero,
        elder=elder,
        helper=helper,
        route_cfg=route,
        parcel_cfg=parcel,
        malfunction=malfunction,
        fix=fix,
        parcel=parcel_ent,
        trousers=trousers,
        delivered=True,
    )
    return world


ROUTES = {
    "hill_path": Route(
        id="hill_path",
        place="the hill path",
        opening="At dawn, the hill path shone pale with dew, curling up toward the bell garden.",
        obstacle="stones that liked to roll under quick feet and a climb that asked for balance",
        goal_place="the bell garden",
        steep=True,
        snaggy=False,
        long_walk=True,
        tags={"hill", "quest"},
    ),
    "bramble_lane": Route(
        id="bramble_lane",
        place="the bramble lane",
        opening="The lane to the orchard ran under hedges where brambles leaned in like nosy neighbors.",
        obstacle="roots underfoot and little hooks of thorn waiting at the edge",
        goal_place="the orchard gate",
        steep=False,
        snaggy=True,
        long_walk=True,
        tags={"bramble", "quest"},
    ),
    "mill_steps": Route(
        id="mill_steps",
        place="the mill steps",
        opening="The old mill stood beyond a stair of worn stones beside the stream.",
        obstacle="many patient steps and a climb that punished fidgeting",
        goal_place="the mill door",
        steep=True,
        snaggy=False,
        long_walk=True,
        tags={"steps", "quest"},
    ),
}

PARCELS = {
    "seed_packet": Parcel(
        id="seed_packet",
        label="the seed packet",
        phrase="a seed packet wrapped in wax paper",
        recipient="Robin the gardener",
        purpose="It was needed before the morning watering, so the beans could be sown in the soft ground.",
        carry_mode="pocket",
        arrival_image="Robin smiled, opened the packet, and the small seeds rattled like a happy little rain.",
        tags={"seeds", "garden"},
    ),
    "moon_map": Parcel(
        id="moon_map",
        label="the moon-map leaf",
        phrase="a moon-map leaf folded with silver marks",
        recipient="Badger the miller",
        purpose="It showed where to turn the night wheel, and the miller had promised to keep the flour ready for the village.",
        carry_mode="pocket",
        arrival_image="Badger spread the leaf on the table, and the silver marks gleamed in the window light.",
        tags={"map", "mill"},
    ),
    "honey_jar": Parcel(
        id="honey_jar",
        label="the honey jar",
        phrase="a small honey jar with a cloth lid",
        recipient="Hedgehog the host",
        purpose="It was meant for the supper table, where guests would soon gather and tell kind stories.",
        carry_mode="hand",
        arrival_image="Hedgehog lifted the jar, and the supper room seemed warmer at once.",
        tags={"honey", "supper"},
    ),
}

MALFUNCTIONS = {
    "torn_pocket": Malfunction(
        id="torn_pocket",
        label="torn pocket",
        sound="Rrrip",
        discovery="The seam of his right pocket split open with a sly grin.",
        inward="If I trust a torn pocket, I shall be asking the road to guard my things for me.",
        problem="A hole in the pocket lets small things slip away.",
        threatens_pocket=True,
        tags={"pocket", "mend"},
    ),
    "loose_drawstring": Malfunction(
        id="loose_drawstring",
        label="loose drawstring",
        sound="Fwip",
        discovery="The drawstring slithered free, and his waistband forgot its duty.",
        inward="If I keep tugging at my clothes, I shall not give my mind to the path.",
        problem="A loose waist makes walking clumsy and slow.",
        threatens_stride=True,
        tags={"belt", "walk"},
    ),
    "dragging_hem": Malfunction(
        id="dragging_hem",
        label="dragging hem",
        sound="Snick-snick",
        discovery="One damp hem came loose and began to trail where roots and thorns could gossip with it.",
        inward="Cloth that drags invites the road to hold it back.",
        problem="A dragging hem snags on rough ground.",
        threatens_snag=True,
        tags={"hem", "snag"},
    ),
}

FIXES = {
    "spider_stitch": Fix(
        id="spider_stitch",
        label="a spider stitch",
        helper_name="Nettle the spider",
        helper_type="spider",
        helper_place="a neat web-workshop under the bridge",
        action="sewed the pocket shut with bright, fine thread",
        flourish="Tik-tik, whisk, pull",
        solves={"torn_pocket"},
        tags={"stitch", "spider"},
    ),
    "reed_belt": Fix(
        id="reed_belt",
        label="a reed belt",
        helper_name="Caro the otter",
        helper_type="otter",
        helper_place="a reed bench by the stream",
        action="braided a green belt and tied the loose waist snug",
        flourish="Swish-swish, tug, pat",
        solves={"loose_drawstring"},
        tags={"belt", "otter"},
    ),
    "hem_knot": Fix(
        id="hem_knot",
        label="a hem knot",
        helper_name="Bram the goat",
        helper_type="goat",
        helper_place="a little gate by the lane",
        action="folded the dragging cloth twice and knotted it high and tidy",
        flourish="Flip, fold, nip",
        solves={"dragging_hem"},
        tags={"hem", "goat"},
    ),
    "thorn_pin": Fix(
        id="thorn_pin",
        label="a thorn pin",
        helper_name="Thistle the hedgehog",
        helper_type="hedgehog",
        helper_place="a mossy doorstep beside the hedge",
        action="fastened the torn pocket with a polished thorn until it sat safe and flat",
        flourish="Prick, press, click",
        solves={"torn_pocket"},
        tags={"pin", "hedgehog"},
    ),
}


@dataclass
class StoryParams:
    route: str
    parcel: str
    malfunction: str
    fix: str
    hero_name: str
    elder_name: str
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


GIRL_NAMES = ["Fern", "Mira", "Nell", "Ivy", "Lark", "Tansy"]
BOY_NAMES = ["Pip", "Rowan", "Ash", "Bramble", "Tobin", "Clover"]
ELDER_NAMES = ["Moss", "Thorn", "Willow", "Pebble", "Aster"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    route = world.facts["route_cfg"]
    parcel = world.facts["parcel_cfg"]
    malfunction = world.facts["malfunction"]
    fix = world.facts["fix"]
    return [
        f'Write a child-friendly fable about a fox on a quest along {route.place}, and include the words "trouser" and "malfunction".',
        f"Tell a short fable where {hero.id} must carry {parcel.label} to {parcel.recipient}, but a {malfunction.label} forces an inner monologue and a wise detour for help.",
        f"Write a gentle quest story with sound effects, a clothing mishap, and a lesson about stopping for the right repair, ending with {fix.helper_name}'s help making success possible.",
    ]


KNOWLEDGE = {
    "pocket": [
        ("Why is a torn pocket a problem?",
         "A torn pocket cannot hold small things safely. If you keep walking, they may slip out without you noticing.")
    ],
    "belt": [
        ("What does a belt do?",
         "A belt helps hold clothing in place around the waist. When clothes stay put, it is easier to walk and work.")
    ],
    "hem": [
        ("Why can a long hem be troublesome?",
         "A long hem can drag on the ground and catch on roots or thorns. That can slow you down or make you stumble.")
    ],
    "quest": [
        ("What is a quest?",
         "A quest is a journey with a purpose. Someone sets out to do an important thing and keeps going until it is done.")
    ],
    "mend": [
        ("What does it mean to mend something?",
         "To mend something is to fix what is torn, loose, or broken so it can be used properly again. Small repairs can prevent bigger problems.")
    ],
    "seeds": [
        ("Why are seeds important in a garden?",
         "Seeds are the beginning of many plants. If they are planted at the right time, they can grow into food or flowers.")
    ],
    "map": [
        ("What is a map for?",
         "A map helps show where things are and how to get from one place to another. It can guide someone who needs to find the right way.")
    ],
    "honey": [
        ("Why do people share honey at a meal?",
         "Honey is sweet, so sharing it can make a meal feel welcoming and special. Food often carries kindness as well as taste.")
    ],
}
KNOWLEDGE_ORDER = ["quest", "pocket", "belt", "hem", "mend", "seeds", "map", "honey"]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    route = world.facts["route_cfg"]
    parcel = world.facts["parcel_cfg"]
    malfunction = world.facts["malfunction"]
    fix = world.facts["fix"]
    helper = world.facts["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young fox sent on a quest along {route.place}. He wanted to carry {parcel.label} safely to {parcel.recipient}."
        ),
        (
            f"What was {hero.id}'s quest?",
            f"His quest was to bring {parcel.label} to {parcel.recipient} at {route.goal_place}. The errand mattered because {parcel.purpose.lower()}"
        ),
        (
            "What went wrong on the road?",
            f"A trouser malfunction happened: {malfunction.discovery.lower()} That mattered because {malfunction.problem.lower()}"
        ),
        (
            "Why did the hero stop instead of rushing on?",
            f"He listened to his inner monologue and understood the risk before the road made it worse. He stopped because he wanted to protect the quest, not just his pride."
        ),
    ]
    if world.facts["predicted_parcel_risk"] >= THRESHOLD:
        qa.append((
            f"Why was {parcel.label} in danger?",
            f"{parcel.label.capitalize()} was small enough to be carried in a pocket, and the torn pocket could have let it fall out. {hero.id} saw that losing the parcel would end the quest before he reached {parcel.recipient}."
        ))
    if world.facts["predicted_snagged"] >= THRESHOLD:
        qa.append((
            "Why was the road especially hard for this trouser problem?",
            f"{route.place.capitalize()} had rough places that could catch trailing cloth. The dragging hem could have snagged there and slowed {hero.id} at exactly the wrong time."
        ))
    if world.facts["predicted_delay"] >= THRESHOLD and world.facts["predicted_parcel_risk"] < THRESHOLD:
        qa.append((
            "How could the malfunction have slowed the quest?",
            f"The loose or dragging cloth would have forced {hero.id} to fuss with his clothes instead of walking well. That would have turned a clear errand into a slow and clumsy one."
        ))
    qa.append((
        f"Who helped {hero.id}, and how?",
        f"{helper.label} helped by giving him {fix.label}. The repair matched the exact trouble, so after that he could walk properly and finish the quest."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with {hero.id} delivering {parcel.label} safely at {route.goal_place}. The ending proves he changed, because he chose wise repair over foolish hurry."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["route_cfg"].tags)
    tags |= set(world.facts["parcel_cfg"].tags)
    tags |= set(world.facts["malfunction"].tags)
    tags |= set(world.facts["fix"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="hill_path",
        parcel="seed_packet",
        malfunction="torn_pocket",
        fix="spider_stitch",
        hero_name="Pip",
        elder_name="Moss",
    ),
    StoryParams(
        route="bramble_lane",
        parcel="moon_map",
        malfunction="dragging_hem",
        fix="hem_knot",
        hero_name="Fern",
        elder_name="Willow",
    ),
    StoryParams(
        route="mill_steps",
        parcel="honey_jar",
        malfunction="loose_drawstring",
        fix="reed_belt",
        hero_name="Ash",
        elder_name="Pebble",
    ),
    StoryParams(
        route="hill_path",
        parcel="moon_map",
        malfunction="torn_pocket",
        fix="thorn_pin",
        hero_name="Nell",
        elder_name="Aster",
    ),
    StoryParams(
        route="bramble_lane",
        parcel="honey_jar",
        malfunction="loose_drawstring",
        fix="reed_belt",
        hero_name="Rowan",
        elder_name="Thorn",
    ),
]


ASP_RULES = r"""
quest_at_risk(R,P,M) :- route(R), parcel(P), malfunction(M), threatens_pocket(M), carry_mode(P,pocket).
quest_at_risk(R,P,M) :- route(R), parcel(P), malfunction(M), threatens_stride(M), long_walk(R).
quest_at_risk(R,P,M) :- route(R), parcel(P), malfunction(M), threatens_snag(M), snaggy(R).
quest_at_risk(R,P,M) :- route(R), parcel(P), malfunction(M), threatens_snag(M), steep(R).

compatible_fix(M,F) :- fix(F), solves(F,M).
valid(R,P,M,F) :- quest_at_risk(R,P,M), compatible_fix(M,F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        if route.steep:
            lines.append(asp.fact("steep", route_id))
        if route.snaggy:
            lines.append(asp.fact("snaggy", route_id))
        if route.long_walk:
            lines.append(asp.fact("long_walk", route_id))
    for parcel_id, parcel in PARCELS.items():
        lines.append(asp.fact("parcel", parcel_id))
        lines.append(asp.fact("carry_mode", parcel_id, parcel.carry_mode))
    for mal_id, malfunction in MALFUNCTIONS.items():
        lines.append(asp.fact("malfunction", mal_id))
        if malfunction.threatens_pocket:
            lines.append(asp.fact("threatens_pocket", mal_id))
        if malfunction.threatens_stride:
            lines.append(asp.fact("threatens_stride", mal_id))
        if malfunction.threatens_snag:
            lines.append(asp.fact("threatens_snag", mal_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for solved in sorted(fix.solves):
            lines.append(asp.fact("solves", fix_id, solved))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_cases: list[StoryParams] = list(CURATED[:2])
    try:
        default_args = build_parser().parse_args([])
        smoke_cases.append(resolve_params(default_args, random.Random(123)))
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: default resolve_params raised StoryError: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise AssertionError("empty story")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                emit(sample, trace=False, qa=True, header=f"### smoke {i}")
            rendered = buf.getvalue()
            if "smoke" not in rendered or sample.story.splitlines()[0] not in rendered:
                raise AssertionError("emit() did not print expected content")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL on case {i}: {err}")
    if rc == 0:
        print("OK: generate()/emit() smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable story world: a quest, a trouser malfunction, an inner monologue, and the right repair."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--malfunction", choices=MALFUNCTIONS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route is not None and args.route not in ROUTES:
        raise StoryError(f"(Unknown route: {args.route})")
    if args.parcel is not None and args.parcel not in PARCELS:
        raise StoryError(f"(Unknown parcel: {args.parcel})")
    if args.malfunction is not None and args.malfunction not in MALFUNCTIONS:
        raise StoryError(f"(Unknown malfunction: {args.malfunction})")
    if args.fix is not None and args.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {args.fix})")

    if args.route and args.parcel and args.malfunction:
        route = ROUTES[args.route]
        parcel = PARCELS[args.parcel]
        malfunction = MALFUNCTIONS[args.malfunction]
        if not quest_at_risk(route, parcel, malfunction):
            raise StoryError(explain_rejection(route, parcel, malfunction))
    if args.malfunction and args.fix:
        malfunction = MALFUNCTIONS[args.malfunction]
        fix = FIXES[args.fix]
        if not compatible_fix(malfunction, fix):
            raise StoryError(explain_fix(malfunction, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.parcel is None or combo[1] == args.parcel)
        and (args.malfunction is None or combo[2] == args.malfunction)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, parcel_id, malfunction_id, fix_id = rng.choice(combos)
    hero_name = args.hero_name or rng.choice(sorted(GIRL_NAMES + BOY_NAMES))
    elder_name = args.elder_name or rng.choice(sorted(ELDER_NAMES))
    return StoryParams(
        route=route_id,
        parcel=parcel_id,
        malfunction=malfunction_id,
        fix=fix_id,
        hero_name=hero_name,
        elder_name=elder_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.parcel not in PARCELS:
        raise StoryError(f"(Unknown parcel: {params.parcel})")
    if params.malfunction not in MALFUNCTIONS:
        raise StoryError(f"(Unknown malfunction: {params.malfunction})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    route = ROUTES[params.route]
    parcel = PARCELS[params.parcel]
    malfunction = MALFUNCTIONS[params.malfunction]
    fix = FIXES[params.fix]

    if not quest_at_risk(route, parcel, malfunction):
        raise StoryError(explain_rejection(route, parcel, malfunction))
    if not compatible_fix(malfunction, fix):
        raise StoryError(explain_fix(malfunction, fix))

    world = tell(
        route=route,
        parcel=parcel,
        malfunction=malfunction,
        fix=fix,
        hero_name=params.hero_name,
        elder_name=params.elder_name,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, parcel, malfunction, fix) combos:\n")
        for route_id, parcel_id, malfunction_id, fix_id in combos:
            print(f"  {route_id:12} {parcel_id:11} {malfunction_id:16} {fix_id}")
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
            header = f"### {p.hero_name}: {p.malfunction} on {p.route} carrying {p.parcel}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
