#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gem_spread_bike_lane_inner_monologue_heartwarming.py
================================================================================

A standalone story world about a child in a bike lane who notices a lost gem,
pulls over safely, and helps it find its way home. The world models a concrete
problem -- a sparkling object sitting where bikes roll -- and a concrete fix:
stop safely, pick it up, and use the help the place actually offers.

The stories are heartwarming, use short inner-monologue beats, and end with an
image that proves what changed: the lane is safer, the lost object is cared for,
and kindness spreads from one rider to another.

Run it
------
    python storyworlds/worlds/gpt-5.4/gem_spread_bike_lane_inner_monologue_heartwarming.py
    python storyworlds/worlds/gpt-5.4/gem_spread_bike_lane_inner_monologue_heartwarming.py --route park_lane --return call_out
    python storyworlds/worlds/gpt-5.4/gem_spread_bike_lane_inner_monologue_heartwarming.py --stop reach_down
    python storyworlds/worlds/gpt-5.4/gem_spread_bike_lane_inner_monologue_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/gem_spread_bike_lane_inner_monologue_heartwarming.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Route:
    id: str
    label: str
    scene: str
    destination: str
    owner_visible: bool
    helper_kind: str
    helper_label: str
    helper_place: str
    sun_line: str
    closing: str
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
class LostItem:
    id: str
    label: str
    phrase: str
    shine: str
    owner_phrase: str
    where_missing: str
    thanks: str
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
class StopPlan:
    id: str
    sense: int
    safe: bool
    motion: str
    pickup: str
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


@dataclass
class ReturnPlan:
    id: str
    sense: int
    needs_visible: bool = False
    needs_helper: bool = False
    immediate: bool = True
    text: str = ""
    reunion: str = ""
    later: str = ""
    qa_text: str = ""
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


def _r_lane_risk(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    lane = world.get("lane")
    hero = world.get("hero")
    if item.meters["in_lane"] >= THRESHOLD:
        sig = ("lane_risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            lane.meters["risk"] += 1
            hero.memes["worry"] += 1
            hero.memes["care"] += 1
            out.append("__risk__")
    return out


def _r_clear_lane(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    lane = world.get("lane")
    if item.meters["picked_up"] >= THRESHOLD and lane.meters["risk"] >= THRESHOLD:
        sig = ("clear_lane",)
        if sig not in world.fired:
            world.fired.add(sig)
            lane.meters["risk"] = 0.0
            out.append("__clear__")
    return out


def _r_return_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    hero = world.get("hero")
    companion = world.get("companion")
    owner = world.get("owner")
    if item.meters["returned"] >= THRESHOLD:
        sig = ("return_relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["pride"] += 1
            hero.memes["joy"] += 1
            companion.memes["joy"] += 1
            owner.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="lane_risk", tag="physical", apply=_r_lane_risk),
    Rule(name="clear_lane", tag="physical", apply=_r_clear_lane),
    Rule(name="return_relief", tag="social", apply=_r_return_relief),
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


def sensible_stops() -> list[StopPlan]:
    return [p for p in STOPS.values() if p.sense >= SENSE_MIN and p.safe]


def sensible_returns() -> list[ReturnPlan]:
    return [p for p in RETURNS.values() if p.sense >= SENSE_MIN]


def return_works(route: Route, plan: ReturnPlan) -> bool:
    if plan.needs_visible and not route.owner_visible:
        return False
    if plan.needs_helper and not route.helper_kind:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for route_id in ROUTES:
        route = ROUTES[route_id]
        for item_id in ITEMS:
            for stop in sensible_stops():
                for ret in sensible_returns():
                    if return_works(route, ret):
                        combos.append((route_id, item_id, stop.id, ret.id))
    return combos


def explain_stop(stop_id: str) -> str:
    stop = STOPS[stop_id]
    return (
        f"(Refusing stop '{stop_id}': it is not a safe way to handle something in a "
        f"bike lane. Pick a plan that pulls over before anyone reaches for the object.)"
    )


def explain_return(route: Route, return_id: str) -> str:
    plan = RETURNS[return_id]
    if plan.needs_visible and not route.owner_visible:
        return (
            f"(No story: {route.label} does not make the owner easy to spot, so "
            f"'{return_id}' would not honestly work here. Try a helper-based return.)"
        )
    if plan.needs_helper and not route.helper_kind:
        return (
            f"(No story: {route.label} has no helper for '{return_id}'. Pick a route "
            f"or return plan that offers real help.)"
        )
    return "(No story: that return plan does not fit this route.)"


def predict_risk(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    lane = sim.get("lane")
    hero = sim.get("hero")
    return {
        "risk": lane.meters["risk"],
        "worry": hero.memes["worry"],
    }


def introduce(world: World, hero: Entity, companion: Entity, route: Route) -> None:
    world.say(
        f"{hero.id} rode beside {companion.id} in the {route.label}. {route.scene}"
    )
    world.say(
        f"They were heading toward {route.destination}, and {route.sun_line}"
    )


def warm_up(world: World, hero: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} liked the soft whirr of the tires. It made {hero.pronoun('object')} feel steady and brave."
    )


def notice(world: World, hero: Entity, item: LostItem) -> None:
    world.get("item").meters["in_lane"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then something bright winked on the paint between the white lane lines: {item.phrase}."
    )
    world.say(
        f'Inside, {hero.id} thought, "That little gem is too pretty to be ground under a wheel."'
    )


def worry(world: World, hero: Entity, item: LostItem) -> None:
    lane = world.get("lane")
    if lane.meters["risk"] >= THRESHOLD:
        world.say(
            f'Inside, {hero.id} thought, "If we leave it there, another rider could bump it, and someone might wobble."'
        )
    world.say(
        f"{hero.id} pointed. {item.shine.capitalize()} made it easy to see, but it was sitting in a bad place."
    )


def choose_stop(world: World, hero: Entity, companion: Entity, stop: StopPlan) -> None:
    hero.memes["care"] += 1
    world.say(
        f'"Let\'s get off the lane first," said {companion.id}. {hero.id} {stop.motion}.'
    )
    world.say(
        f'Inside, {hero.id} thought, "First safe, then helpful."'
    )


def pick_up(world: World, hero: Entity, item: LostItem, stop: StopPlan) -> None:
    ent = world.get("item")
    ent.meters["picked_up"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"When they were safely out of the way, {hero.id} {stop.pickup}"
    )
    world.say(
        f"The lane looked clear again, and {hero.id} felt {hero.pronoun('possessive')} shoulders loosen."
    )


def return_now(
    world: World,
    hero: Entity,
    companion: Entity,
    owner: Entity,
    route: Route,
    item: LostItem,
    plan: ReturnPlan,
) -> None:
    world.say(plan.text.format(hero=hero.id, companion=companion.id, owner=owner.id, helper=route.helper_label, item=item.label))
    world.say(plan.reunion.format(hero=hero.id, companion=companion.id, owner=owner.id, helper=route.helper_label, item=item.label))
    world.get("item").meters["returned"] = 1.0
    propagate(world, narrate=False)
    smile = "A warm smile spread across " + owner.id + "'s face."
    world.say(smile)
    world.say(item.thanks.format(hero=hero.id, owner=owner.id))


def return_later(
    world: World,
    hero: Entity,
    companion: Entity,
    owner: Entity,
    route: Route,
    item: LostItem,
    plan: ReturnPlan,
) -> None:
    helper = world.get("helper")
    helper.meters["holding"] = 1.0
    world.say(plan.text.format(hero=hero.id, companion=companion.id, owner=owner.id, helper=route.helper_label, item=item.label))
    world.say(plan.later.format(hero=hero.id, companion=companion.id, owner=owner.id, helper=route.helper_label, item=item.label))
    world.get("item").meters["returned"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f'Inside, {hero.id} thought, "We may not have seen the owner right away, but kindness still knows how to travel."'
    )
    world.say(item.thanks.format(hero=hero.id, owner=owner.id))


def closing(world: World, hero: Entity, companion: Entity, route: Route) -> None:
    world.say(
        f"They rode on again, and {route.closing}"
    )
    world.say(
        f"{hero.id} pedaled with a lighter heart, as if a tiny bit of that sparkle had stayed with {hero.pronoun('object')}."
    )


def tell(
    route: Route,
    item_cfg: LostItem,
    stop: StopPlan,
    return_plan: ReturnPlan,
    hero_name: str = "Mila",
    hero_gender: str = "girl",
    companion_name: str = "Grandma June",
    companion_type: str = "grandmother",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_type, role="companion"))
    owner_type = "girl" if "child" in item_cfg.owner_phrase else "woman"
    owner_name = {"girl": "Tess", "woman": "Ms. Rina"}[owner_type]
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_type, role="owner"))
    helper_type = "woman" if route.helper_kind in {"guard", "vendor", "librarian"} else "man"
    helper_name = {"guard": "Mr. Cole", "vendor": "Ms. Pru", "librarian": "Mr. Ben"}[route.helper_kind]
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=route.helper_label))
    lane = world.add(Entity(id="lane", type="bike_lane", label=route.label))
    item = world.add(Entity(id="item", type="lost_item", label=item_cfg.label, attrs={"shine": item_cfg.shine}))

    world.facts.update(
        route=route,
        item_cfg=item_cfg,
        stop=stop,
        return_plan=return_plan,
        hero=hero,
        companion=companion,
        owner=owner,
        helper=helper,
        outcome="immediate" if return_plan.immediate else "later",
    )

    introduce(world, hero, companion, route)
    warm_up(world, hero)

    world.para()
    notice(world, hero, item_cfg)
    worry(world, hero, item_cfg)

    world.para()
    choose_stop(world, hero, companion, stop)
    pick_up(world, hero, item_cfg, stop)

    world.para()
    if return_plan.immediate:
        return_now(world, hero, companion, owner, route, item_cfg, return_plan)
    else:
        return_later(world, hero, companion, owner, route, item_cfg, return_plan)

    world.para()
    closing(world, hero, companion, route)
    world.facts["lane_cleared"] = world.get("lane").meters["risk"] < THRESHOLD
    world.facts["returned"] = world.get("item").meters["returned"] >= THRESHOLD
    return world


ROUTES = {
    "school_lane": Route(
        id="school_lane",
        label="bike lane by the school",
        scene="Backpacks bobbed on nearby handlebars, and the morning air smelled like toast from open windows.",
        destination="the school garden gate",
        owner_visible=True,
        helper_kind="guard",
        helper_label="the crossing guard",
        helper_place="by the crosswalk",
        sun_line="sunlight spread in pale stripes across the lane",
        closing="the lane felt a little kinder than before",
        tags={"bike_lane", "school", "helper"},
    ),
    "park_lane": Route(
        id="park_lane",
        label="bike lane beside the park",
        scene="Trees leaned over the path, and ducks muttered from the pond beyond the fence.",
        destination="the little bridge by the pond",
        owner_visible=True,
        helper_kind="vendor",
        helper_label="the fruit cart lady",
        helper_place="beside the park gate",
        sun_line="the afternoon light spread softly over the handlebars",
        closing="even the leaves seemed to wave them along",
        tags={"bike_lane", "park", "helper"},
    ),
    "library_lane": Route(
        id="library_lane",
        label="bike lane near the library",
        scene="The brick wall kept one side cool, and a row of planters buzzed with bees.",
        destination="the library bike rack",
        owner_visible=False,
        helper_kind="librarian",
        helper_label="the librarian at the front desk",
        helper_place="inside the library",
        sun_line="a bright patch of sun spread near the curb",
        closing="the quiet street looked safe and tidy behind them",
        tags={"bike_lane", "library", "helper"},
    ),
}

ITEMS = {
    "bracelet_gem": LostItem(
        id="bracelet_gem",
        label="bracelet",
        phrase="a tiny silver bracelet with one blue gem",
        shine="the blue gem flashed like a raindrop",
        owner_phrase="a child from the park",
        where_missing="from a small wrist",
        thanks="{owner} slipped the bracelet back on and said, \"Thank you, {hero}. You kept my special thing safe.\"",
        tags={"gem", "lost_item", "bracelet"},
    ),
    "bag_charm": LostItem(
        id="bag_charm",
        label="bag charm",
        phrase="a zipper charm shaped like a star with a green gem in the middle",
        shine="the little green gem blinked in the sun",
        owner_phrase="a grown-up with a book bag",
        where_missing="from a book bag zipper",
        thanks="{owner} clipped the charm back where it belonged and laughed a happy little laugh.",
        tags={"gem", "lost_item", "bag"},
    ),
    "helmet_pin": LostItem(
        id="helmet_pin",
        label="helmet pin",
        phrase="a round helmet pin with a red gem at its center",
        shine="the red gem glowed like a berry",
        owner_phrase="a child on a scooter",
        where_missing="from the side of a helmet",
        thanks="{owner} tapped the pin gently and said it made the whole helmet feel brave again.",
        tags={"gem", "lost_item", "helmet"},
    ),
}

STOPS = {
    "pull_over": StopPlan(
        id="pull_over",
        sense=3,
        safe=True,
        motion="squeezed both brakes, rolled to the curb, and put one sneaker down",
        pickup="bent carefully, picked up the lost thing, and brushed one grain of grit from the gem.",
        qa_text="pulled over to the curb and stopped before picking it up",
        tags={"bike_safety", "curb"},
    ),
    "walk_bikes": StopPlan(
        id="walk_bikes",
        sense=3,
        safe=True,
        motion="coasted out of the lane, hopped off, and walked the bikes back a few careful steps",
        pickup="stooped beside the painted line and lifted the sparkly thing in both hands.",
        qa_text="got out of the lane, got off the bikes, and walked back carefully",
        tags={"bike_safety", "walk"},
    ),
    "reach_down": StopPlan(
        id="reach_down",
        sense=1,
        safe=False,
        motion="leaned down while still rolling",
        pickup="snatched for the object before the wheels had even stopped.",
        qa_text="reached down while still riding",
        tags={"unsafe"},
    ),
    "stop_middle": StopPlan(
        id="stop_middle",
        sense=1,
        safe=False,
        motion="hit the brakes in the middle of the lane",
        pickup="grabbed the object while blocking the path.",
        qa_text="stopped in the middle of the lane",
        tags={"unsafe"},
    ),
}

RETURNS = {
    "call_out": ReturnPlan(
        id="call_out",
        sense=3,
        needs_visible=True,
        needs_helper=False,
        immediate=True,
        text="{hero} held the sparkly find up and called, \"Did someone lose this?\"",
        reunion="{owner} turned at once and touched {owner_id_missing}. Then {companion} pointed to the {item}, and {owner} hurried over with hopeful eyes.",
        later="",
        qa_text="called out to the nearby owner and returned it right away",
        tags={"return", "owner_nearby"},
    ),
    "ask_helper": ReturnPlan(
        id="ask_helper",
        sense=3,
        needs_visible=False,
        needs_helper=True,
        immediate=False,
        text="{hero} and {companion} took the find to {helper} and explained where they had seen it lying in the lane.",
        reunion="",
        later="{helper} promised to keep it safe. The next afternoon, when they passed again, {helper} waved and said the owner had come back smiling for it.",
        qa_text="gave it to a trusted helper who returned it later",
        tags={"return", "helper"},
    ),
    "show_helper_owner": ReturnPlan(
        id="show_helper_owner",
        sense=2,
        needs_visible=True,
        needs_helper=True,
        immediate=True,
        text="{hero} carried the find to {helper}, just as a worried owner came looking along the edge of the lane.",
        reunion="{helper} checked whose it was, and when {owner} described the little gem exactly, the lost thing was passed back into the right hands.",
        later="",
        qa_text="used the nearby helper to make sure it went to the right owner",
        tags={"return", "helper", "owner_nearby"},
    ),
}

# Repair one format string field with a small indirection at render time.
RETURNS["call_out"].reunion = (
    "{owner} turned at once and touched {owner_possessive} wrist or bag in surprise. "
    "Then {companion} pointed to the {item}, and {owner} hurried over with hopeful eyes."
)

GIRL_NAMES = ["Mila", "Nora", "Zoe", "Ava", "Lena", "Ivy"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Max", "Sam", "Theo"]
COMPANIONS = [
    {"name": "Mom", "type": "mother"},
    {"name": "Dad", "type": "father"},
    {"name": "Grandma June", "type": "grandmother"},
    {"name": "Grandpa Ray", "type": "grandfather"},
]


@dataclass
class StoryParams:
    route: str
    item: str
    stop: str
    return_plan: str
    hero_name: str
    hero_gender: str
    companion_name: str
    companion_type: str
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
    route = world.facts["route"]
    item = world.facts["item_cfg"]
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    outcome = world.facts["outcome"]
    prompts = [
        f'Write a heartwarming story for a 3-to-5-year-old set in a bike lane that includes the word "gem" and one short inner-monologue line.',
        f"Tell a gentle story where {hero.id} notices {item.phrase} in {route.label}, pulls over safely, and tries to help the owner.",
    ]
    if outcome == "immediate":
        prompts.append(
            f"Write a warm story where kindness spreads quickly: {hero.id} finds a lost sparkly object in {route.label} and returns it the same day."
        )
    else:
        prompts.append(
            f"Write a cozy story where {hero.id} finds a lost sparkly object in {route.label}, leaves it with a trusted helper, and learns that kindness can still travel later."
        )
    return prompts


KNOWLEDGE = {
    "bike_lane": [
        (
            "What is a bike lane?",
            "A bike lane is a part of the road marked for bikes. It helps riders move in their own space more safely."
        )
    ],
    "bike_safety": [
        (
            "What should you do if you see something in a bike lane?",
            "You should move to a safe place and stop first. Reaching while you are still rolling can make you wobble or fall."
        )
    ],
    "gem": [
        (
            "What is a gem?",
            "A gem is a small shiny stone or jewel. People use gems to decorate jewelry and other special things."
        )
    ],
    "lost_item": [
        (
            "Why is it kind to return a lost thing?",
            "Returning a lost thing helps the person who was missing it feel relieved. It also shows that you care about other people."
        )
    ],
    "helper": [
        (
            "Who is a trusted helper when you find something lost?",
            "A trusted helper can be a crossing guard, a librarian, or another responsible grown-up nearby. They can help keep the item safe and find the owner."
        )
    ],
    "helmet": [
        (
            "Why do riders wear helmets?",
            "Helmets help protect your head if you fall. They are important safety gear for biking and scootering."
        )
    ],
}

KNOWLEDGE_ORDER = ["bike_lane", "bike_safety", "gem", "lost_item", "helper", "helmet"]


def story_qa(world: World) -> list[tuple[str, str]]:
    route = world.facts["route"]
    item = world.facts["item_cfg"]
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    owner = world.facts["owner"]
    stop = world.facts["stop"]
    ret = world.facts["return_plan"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was riding with {companion.id} in {route.label}. They noticed a lost sparkly thing and decided to help."
        ),
        (
            f"What did {hero.id} see in the bike lane?",
            f"{hero.id} saw {item.phrase}. It was bright enough to catch the eye, but it was sitting where bike wheels pass."
        ),
        (
            f"Why did {hero.id} think stopping mattered?",
            f"{hero.id} worried the lost thing could be crushed or make another rider wobble. That is why {hero.pronoun('subject')} chose help over hurrying on."
        ),
        (
            f"How did {hero.id} handle the lost thing safely?",
            f"{hero.id} {stop.qa_text}. That kept the bike lane clear and made it safe to pick the object up."
        ),
    ]
    if outcome == "immediate":
        qa.append(
            (
                "How did the lost thing get back to its owner?",
                f"They {ret.qa_text}. The owner recognized the sparkly item and felt relieved right away."
            )
        )
    else:
        qa.append(
            (
                "How did the lost thing get back to its owner?",
                f"They {ret.qa_text}. Even though the owner was not there at once, a trusted helper made sure it was returned later."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the lane safe again and {hero.id} riding on with a lighter heart. The kind choice changed both the road and the mood around it."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["route"].tags) | set(world.facts["item_cfg"].tags) | set(world.facts["stop"].tags) | set(world.facts["return_plan"].tags)
    if "helmet" in world.facts["item"]:
        tags.add("helmet")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="park_lane",
        item="bracelet_gem",
        stop="pull_over",
        return_plan="call_out",
        hero_name="Mila",
        hero_gender="girl",
        companion_name="Grandma June",
        companion_type="grandmother",
    ),
    StoryParams(
        route="school_lane",
        item="helmet_pin",
        stop="walk_bikes",
        return_plan="show_helper_owner",
        hero_name="Owen",
        hero_gender="boy",
        companion_name="Dad",
        companion_type="father",
    ),
    StoryParams(
        route="library_lane",
        item="bag_charm",
        stop="pull_over",
        return_plan="ask_helper",
        hero_name="Nora",
        hero_gender="girl",
        companion_name="Mom",
        companion_type="mother",
    ),
]


ASP_RULES = r"""
sensible_stop(S) :- stop(S), stop_sense(S, V), sense_min(M), V >= M, safe_stop(S).
sensible_return(R) :- return_plan(R), return_sense(R, V), sense_min(M), V >= M.

works(Route, R) :- route(Route), return_plan(R),
                   not needs_visible(R), not needs_helper(R).
works(Route, R) :- route(Route), return_plan(R),
                   needs_visible(R), owner_visible(Route), not needs_helper(R).
works(Route, R) :- route(Route), return_plan(R),
                   needs_helper(R), helper_present(Route), not needs_visible(R).
works(Route, R) :- route(Route), return_plan(R),
                   needs_helper(R), helper_present(Route),
                   needs_visible(R), owner_visible(Route).

valid(Route, Item, Stop, Return) :-
    route(Route), item(Item), sensible_stop(Stop), sensible_return(Return),
    works(Route, Return).

outcome(immediate) :- chosen_return(R), return_immediate(R).
outcome(later) :- chosen_return(R), not return_immediate(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        if route.owner_visible:
            lines.append(asp.fact("owner_visible", rid))
        if route.helper_kind:
            lines.append(asp.fact("helper_present", rid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for sid, stop in STOPS.items():
        lines.append(asp.fact("stop", sid))
        lines.append(asp.fact("stop_sense", sid, stop.sense))
        if stop.safe:
            lines.append(asp.fact("safe_stop", sid))
    for rid, ret in RETURNS.items():
        lines.append(asp.fact("return_plan", rid))
        lines.append(asp.fact("return_sense", rid, ret.sense))
        if ret.needs_visible:
            lines.append(asp.fact("needs_visible", rid))
        if ret.needs_helper:
            lines.append(asp.fact("needs_helper", rid))
        if ret.immediate:
            lines.append(asp.fact("return_immediate", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_return", params.return_plan)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "immediate" if RETURNS[params.return_plan].immediate else "later"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a lost gem in a bike lane, a safe stop, and a kind return."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--stop", choices=STOPS)
    ap.add_argument("--return", dest="return_plan", choices=RETURNS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=[c["name"] for c in COMPANIONS])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _companion_by_name(name: str) -> dict:
    for item in COMPANIONS:
        if item["name"] == name:
            return dict(item)
    raise StoryError(f"(Unknown companion '{name}').")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stop and args.stop not in {p.id for p in sensible_stops()}:
        raise StoryError(explain_stop(args.stop))
    if args.route and args.return_plan:
        route = ROUTES[args.route]
        if not return_works(route, RETURNS[args.return_plan]):
            raise StoryError(explain_return(route, args.return_plan))
    if args.return_plan and RETURNS[args.return_plan].sense < SENSE_MIN:
        raise StoryError(f"(Refusing return plan '{args.return_plan}': it is below the world's common-sense threshold.)")

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.item is None or combo[1] == args.item)
        and (args.stop is None or combo[2] == args.stop)
        and (args.return_plan is None or combo[3] == args.return_plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, item_id, stop_id, return_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)

    comp = _companion_by_name(args.companion) if args.companion else dict(rng.choice(COMPANIONS))
    return StoryParams(
        route=route_id,
        item=item_id,
        stop=stop_id,
        return_plan=return_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        companion_name=comp["name"],
        companion_type=comp["type"],
    )


def _owner_possessive(item: LostItem) -> str:
    if item.id == "bracelet_gem":
        return "her"
    if item.id == "helmet_pin":
        return "her"
    return "her"


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route '{params.route}').")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item '{params.item}').")
    if params.stop not in STOPS:
        raise StoryError(f"(Unknown stop '{params.stop}').")
    if params.return_plan not in RETURNS:
        raise StoryError(f"(Unknown return plan '{params.return_plan}').")
    if params.stop not in {p.id for p in sensible_stops()}:
        raise StoryError(explain_stop(params.stop))
    route = ROUTES[params.route]
    ret = RETURNS[params.return_plan]
    if not return_works(route, ret):
        raise StoryError(explain_return(route, params.return_plan))

    world = tell(
        route=route,
        item_cfg=ITEMS[params.item],
        stop=STOPS[params.stop],
        return_plan=ret,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        companion_name=params.companion_name,
        companion_type=params.companion_type,
    )

    story = world.render()
    owner_pos = _owner_possessive(ITEMS[params.item])
    story = story.replace("{owner_possessive}", owner_pos).replace("{owner_id_missing}", "")
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, item, stop, return) combos:\n")
        for route, item, stop, ret in combos:
            print(f"  {route:12} {item:12} {stop:10} {ret}")
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
            header = f"### {p.hero_name}: {p.item} in {p.route} ({p.stop}, {p.return_plan})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
