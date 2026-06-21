#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lorry_lesson_learned_suspense_repetition_myth.py
============================================================================

A standalone storyworld for a small myth-like cautionary tale about a child, a
narrow road, and a rumbling lorry. The domain is built around a repeated
warning: when the signs come, step aside and wait.

The world models a simple physical danger:
- a heavy lorry must pass along a route,
- the route affords certain warning omens,
- the child can only stay safe by using a refuge that truly fits that route.

The prose is state-driven rather than template-swapped:
- the elder teaches a repeated road rule,
- the child sets out carrying an offering,
- suspense rises as the omen appears again and again,
- the child either remembers early, remembers late, or learns through loss,
- the ending image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/lorry_lesson_learned_suspense_repetition_myth.py
    python storyworlds/worlds/gpt-5.4/lorry_lesson_learned_suspense_repetition_myth.py --route cliff_road --omen tremor --refuge niche
    python storyworlds/worlds/gpt-5.4/lorry_lesson_learned_suspense_repetition_myth.py --refuge ditch
    python storyworlds/worlds/gpt-5.4/lorry_lesson_learned_suspense_repetition_myth.py --all
    python storyworlds/worlds/gpt-5.4/lorry_lesson_learned_suspense_repetition_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lorry_lesson_learned_suspense_repetition_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
PRIDE_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "patient", "steady", "thoughtful"}


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
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
    phrase: str
    shrine: str
    cargo: str
    scene: str
    first_line: str
    second_line: str
    rumble_line: str
    omens: set[str] = field(default_factory=set)
    refuges: set[str] = field(default_factory=set)
    severity: int = 2
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
class Omen:
    id: str
    first_sign: str
    second_sign: str
    seen_from: str
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
class Refuge:
    id: str
    label: str
    phrase: str
    action: str
    finish: str
    sense: int
    power: int
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
class Offering:
    id: str
    label: str
    phrase: str
    fragile: bool
    loss_text: str
    safe_text: str
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    road = world.entities.get("road")
    lorry = world.entities.get("lorry")
    if not child or not road or not lorry:
        return out
    if lorry.meters["approaching"] < THRESHOLD:
        return out
    if child.attrs.get("place") != "road":
        return out
    sig = ("danger", child.id, int(lorry.meters["approaching"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    road.meters["danger"] += 1
    child.memes["fear"] += 1
    child.meters["dust"] += 1
    out.append("__danger__")
    return out


def _r_rattle_offering(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    offering = world.entities.get("offering")
    road = world.entities.get("road")
    if not child or not offering or not road:
        return out
    if road.meters["danger"] < THRESHOLD:
        return out
    if child.attrs.get("place") != "road":
        return out
    sig = ("rattle", int(road.meters["danger"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    offering.meters["shaken"] += 1
    out.append("__rattle__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="rattle_offering", tag="physical", apply=_r_rattle_offering),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def omen_fits(route: Route, omen: Omen) -> bool:
    return omen.id in route.omens


def refuge_fits(route: Route, refuge: Refuge) -> bool:
    return refuge.id in route.refuges and refuge.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for route_id, route in ROUTES.items():
        for omen_id, omen in OMENS.items():
            if not omen_fits(route, omen):
                continue
            for refuge_id, refuge in REFUGES.items():
                if refuge_fits(route, refuge):
                    combos.append((route_id, omen_id, refuge_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_heed_early(relation: str, trait: str, trust: int) -> bool:
    authority = initial_caution(trait) + (2.0 if relation in {"grandmother", "grandfather"} else 1.0)
    return authority + (1.0 if trust >= 7 else 0.0) > PRIDE_INIT


def road_severity(route: Route, delay: int) -> int:
    return route.severity + delay


def sheltered(refuge: Refuge, route: Route, delay: int) -> bool:
    return refuge.power >= road_severity(route, delay)


def predict_pass(world: World, route: Route, refuge: Refuge) -> dict:
    sim = world.copy()
    child = sim.get("child")
    lorry = sim.get("lorry")
    child.attrs["place"] = "road"
    lorry.meters["approaching"] += 1
    propagate(sim, narrate=False)
    child.attrs["place"] = "refuge"
    return {
        "danger": sim.get("road").meters["danger"],
        "shaken": sim.get("offering").meters["shaken"],
        "safe": sheltered(refuge, route, 0),
    }


def introduction(world: World, child: Entity, elder: Entity, route: Route, offering: Offering) -> None:
    child.memes["love"] += 1
    world.say(
        f"In the old days, when people still said the hills could remember footsteps, "
        f"there was a child named {child.id}."
    )
    world.say(
        f"One dawn, {elder.label_word} placed {offering.phrase} into {child.id}'s hands "
        f"and asked {child.pronoun('object')} to carry it along {route.phrase} to {route.shrine}."
    )
    world.say(route.scene)


def teach_rule(world: World, child: Entity, elder: Entity, route: Route, omen: Omen, refuge: Refuge) -> None:
    pred = predict_pass(world, route, refuge)
    child.memes["trust"] = float(child.memes["trust"])
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'Before {child.id} left, {elder.label_word} touched the basket and said, '
        f'"{route.first_line}"'
    )
    world.say(
        f'"{route.second_line}"'
    )
    world.say(
        f'"{route.rumble_line}"'
    )
    world.say(
        f'{elder.label_word.capitalize()} pointed to {refuge.phrase}. '
        f'"That is where you must stand, because the lorry comes {omen.seen_from} and does not bend for little feet."'
    )


def set_out(world: World, child: Entity, route: Route, offering: Offering) -> None:
    child.attrs["place"] = "road"
    child.memes["pride"] = PRIDE_INIT
    world.say(
        f"So {child.id} set out on {route.label}, carrying {offering.label} as carefully as a person carries a promise."
    )


def first_omen(world: World, child: Entity, route: Route, omen: Omen) -> None:
    world.say(omen.first_sign)
    world.say(f'{child.id} remembered the first saying: "{route.first_line}"')


def almost_hurry(world: World, child: Entity, route: Route) -> None:
    child.memes["pride"] += 1
    world.say(
        f"But the path was long, and {child.id} thought, perhaps just this once I can be quicker than the warning."
    )


def step_aside_early(world: World, child: Entity, refuge: Refuge) -> None:
    child.attrs["place"] = "refuge"
    child.memes["caution"] += 1
    child.memes["relief"] += 1
    world.say(
        f"So {child.id} {refuge.action} and stood very still."
    )


def second_omen(world: World, child: Entity, route: Route, omen: Omen) -> None:
    lorry = world.get("lorry")
    lorry.meters["approaching"] += 1
    propagate(world, narrate=False)
    world.say(omen.second_sign)
    world.say(f'{child.id} remembered the second saying: "{route.second_line}"')


def late_choice(world: World, child: Entity, refuge: Refuge) -> None:
    child.attrs["place"] = "refuge"
    child.memes["fear"] += 1
    child.memes["caution"] += 1
    world.say(
        f"At last {child.id} stopped trying to be faster than the road and {refuge.action}."
    )


def lorry_pass(world: World, child: Entity, route: Route, refuge: Refuge) -> None:
    lorry = world.get("lorry")
    lorry.meters["approaching"] += 1
    propagate(world, narrate=False)
    world.say(route.rumble_line)
    world.say(
        f"Then the lorry appeared, heavy with {route.cargo}, filling the narrow way with thunder and dust."
    )
    world.say(
        f"It went by so close that {refuge.finish}"
    )


def keep_offering_safe(world: World, child: Entity, offering: Entity, offering_cfg: Offering) -> None:
    child.memes["relief"] += 1
    child.memes["wisdom"] += 1
    offering.meters["safe"] += 1
    world.say(
        f"When the dust settled, {child.id} looked down and saw that {offering_cfg.safe_text}."
    )


def lose_offering(world: World, child: Entity, offering: Entity, offering_cfg: Offering) -> None:
    child.memes["sorrow"] += 1
    child.memes["wisdom"] += 1
    offering.meters["lost"] += 1
    world.say(
        f"When the dust settled, {child.id} looked down and saw that {offering_cfg.loss_text}."
    )


def arrival(world: World, child: Entity, elder: Entity, route: Route, offering_cfg: Offering, outcome: str) -> None:
    if outcome == "safe":
        world.say(
            f"{child.id} reached {route.shrine} before noon, set the gift down gently, and the old stone seemed to shine back in approval."
        )
    else:
        world.say(
            f"{child.id} still reached {route.shrine}, but with tears on {child.pronoun('possessive')} face and a lighter basket than before."
        )
    world.say(
        f"When {child.id} came home, {elder.label_word} did not scold."
    )


def lesson(world: World, child: Entity, elder: Entity, route: Route, outcome: str) -> None:
    if outcome == "safe":
        world.say(
            f'{elder.label_word.capitalize()} smiled and said, "Now you know why the road is older than your hurry."'
        )
        world.say(
            f'And {child.id} answered, "{route.first_line} {route.second_line} {route.rumble_line}"'
        )
    else:
        world.say(
            f'{elder.label_word.capitalize()} held {child.id} close and said, "A warning repeated is mercy repeated."'
        )
        world.say(
            f'{child.id} whispered, "I should have listened at the first sign, not the last."'
        )


def ending_image(world: World, child: Entity, route: Route, refuge: Refuge, outcome: str) -> None:
    child.memes["changed"] += 1
    if outcome == "safe":
        world.say(
            f"After that day, whenever {child.id} walked {route.label}, {child.pronoun()} greeted {refuge.label} as if it were a faithful friend."
        )
        world.say(
            f"And whenever the hills gave their first little warning, {child.pronoun()} stepped aside before the lorry came, and the road kept peace with {child.pronoun('object')}."
        )
    else:
        world.say(
            f"After that day, whenever {child.id} walked {route.label}, {child.pronoun()} no longer argued with the warning in the dust."
        )
        world.say(
            f"At the first sign, not the second and never the last, {child.pronoun()} stepped into {refuge.label} and waited for the lorry to pass."
        )


def tell(
    route: Route,
    omen: Omen,
    refuge: Refuge,
    offering_cfg: Offering,
    *,
    child_name: str = "Toma",
    child_gender: str = "boy",
    elder_type: str = "grandmother",
    trait: str = "careful",
    relation: str = "grandmother",
    trust: int = 8,
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            attrs={"place": "house"},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            attrs={"relation": relation},
        )
    )
    road = world.add(
        Entity(
            id="road",
            type="road",
            label=route.label,
            role="road",
        )
    )
    lorry = world.add(
        Entity(
            id="lorry",
            type="lorry",
            label="the lorry",
            role="lorry",
        )
    )
    offering = world.add(
        Entity(
            id="offering",
            type="offering",
            label=offering_cfg.label,
            role="offering",
        )
    )

    child.memes["trust"] = float(trust)
    child.memes["caution"] = initial_caution(trait)
    child.memes["pride"] = PRIDE_INIT
    road.meters["danger"] = 0.0
    lorry.meters["approaching"] = 0.0
    offering.meters["shaken"] = 0.0

    introduction(world, child, elder, route, offering_cfg)
    world.para()
    teach_rule(world, child, elder, route, omen, refuge)
    set_out(world, child, route, offering_cfg)

    early = would_heed_early(relation, trait, trust)
    world.para()
    first_omen(world, child, route, omen)

    if early:
        step_aside_early(world, child, refuge)
        world.para()
        lorry_pass(world, child, route, refuge)
        keep_offering_safe(world, child, offering, offering_cfg)
        outcome = "safe"
        timing = "early"
    else:
        almost_hurry(world, child, route)
        world.para()
        second_omen(world, child, route, omen)
        late_choice(world, child, refuge)
        world.para()
        lorry_pass(world, child, route, refuge)
        if sheltered(refuge, route, delay):
            keep_offering_safe(world, child, offering, offering_cfg)
            outcome = "safe"
        else:
            lose_offering(world, child, offering, offering_cfg)
            outcome = "lost"
        timing = "late"

    world.para()
    arrival(world, child, elder, route, offering_cfg, outcome)
    lesson(world, child, elder, route, outcome)
    ending_image(world, child, route, refuge, outcome)

    world.facts.update(
        child=child,
        elder=elder,
        route=route,
        omen=omen,
        refuge=refuge,
        offering_cfg=offering_cfg,
        offering=offering,
        delay=delay,
        trust=trust,
        relation=relation,
        early=early,
        timing=timing,
        outcome=outcome,
        sheltered=sheltered(refuge, route, delay),
    )
    return world


ROUTES = {
    "cliff_road": Route(
        id="cliff_road",
        label="the cliff road",
        phrase="the cliff road under the red hill",
        shrine="the Shrine of First Light",
        cargo="cut stone",
        scene="The road was only a ledge scratched between rock on one side and empty sky on the other.",
        first_line="When the ground hums, step aside.",
        second_line="When the dust lifts, step aside.",
        rumble_line="When the lorry comes, stand still and let it pass.",
        omens={"tremor", "dust"},
        refuges={"niche", "fig_gate"},
        severity=3,
        tags={"road", "cliff", "lorry"},
    ),
    "olive_lane": Route(
        id="olive_lane",
        label="the olive lane",
        phrase="the olive lane by the old wall",
        shrine="the Well of Quiet Water",
        cargo="green jars",
        scene="Olive leaves flickered over the lane, but the way was narrow where the wall bent in and the wagons had once cut deep grooves.",
        first_line="When the bell rings, step aside.",
        second_line="When the dust lifts, step aside.",
        rumble_line="When the lorry comes, stand still and let it pass.",
        omens={"bell", "dust"},
        refuges={"courtyard", "stone_steps"},
        severity=2,
        tags={"road", "olive", "lorry"},
    ),
    "river_bend": Route(
        id="river_bend",
        label="the river bend path",
        phrase="the river bend path by the reeds",
        shrine="the Little Stone by the Ferry",
        cargo="timber",
        scene="The path bent around reeds and river stones, and in one place it narrowed between the water and a bank of packed earth.",
        first_line="When the bell rings, step aside.",
        second_line="When the bank shivers, step aside.",
        rumble_line="When the lorry comes, stand still and let it pass.",
        omens={"bell", "tremor"},
        refuges={"willow_gap", "stone_steps"},
        severity=2,
        tags={"road", "river", "lorry"},
    ),
}

OMENS = {
    "tremor": Omen(
        id="tremor",
        first_sign="Soon the pebbles underfoot gave a tiny shake, as if the hill were clearing its throat.",
        second_sign="A little later the bank shivered again, stronger this time, and the basket handle quivered in the child's hand.",
        seen_from="before it can be seen",
        tags={"warning", "earth"},
    ),
    "dust": Omen(
        id="dust",
        first_sign="Soon a pale thread of dust lifted far along the road and hung in the sun.",
        second_sign="A little later the dust rose thicker and came rolling forward like dry breath.",
        seen_from="before it rounds the bend",
        tags={"warning", "dust"},
    ),
    "bell": Omen(
        id="bell",
        first_sign="Soon a bronze bell began to ring from far away: one note, then another, then another.",
        second_sign="A little later the bell rang louder, and the sound bounced from wall to wall until the lane itself seemed to listen.",
        seen_from="long before it is near",
        tags={"warning", "bell"},
    ),
}

REFUGES = {
    "niche": Refuge(
        id="niche",
        label="the carved stone niche",
        phrase="a carved stone niche in the cliff",
        action="slipped into the carved stone niche",
        finish="the wind of its passing tugged at the child's hair but could not touch the basket",
        sense=3,
        power=4,
        tags={"refuge", "stone"},
    ),
    "fig_gate": Refuge(
        id="fig_gate",
        label="the fig-tree gate",
        phrase="the fig-tree gate set back from the road",
        action="ducked behind the fig-tree gate",
        finish="fig leaves flew everywhere and dust slapped the gate like rain",
        sense=2,
        power=3,
        tags={"refuge", "gate"},
    ),
    "courtyard": Refuge(
        id="courtyard",
        label="the little courtyard",
        phrase="a little courtyard open behind an arch",
        action="stepped into the little courtyard",
        finish="the jars on the wall rattled, yet the arch kept the child safe",
        sense=3,
        power=3,
        tags={"refuge", "arch"},
    ),
    "stone_steps": Refuge(
        id="stone_steps",
        label="the high stone steps",
        phrase="high stone steps above the road",
        action="climbed onto the high stone steps",
        finish="the air shook beneath the steps while the wheels roared past below",
        sense=2,
        power=2,
        tags={"refuge", "steps"},
    ),
    "willow_gap": Refuge(
        id="willow_gap",
        label="the willow gap",
        phrase="a willow gap where the roots made a hollow",
        action="pressed into the willow gap",
        finish="the willow leaves whipped and hissed as the lorry thundered past",
        sense=2,
        power=2,
        tags={"refuge", "willow"},
    ),
    "ditch": Refuge(
        id="ditch",
        label="the ditch",
        phrase="a muddy ditch at the roadside",
        action="jumped into the muddy ditch",
        finish="mud splashed high and the edge crumbled under the shaking road",
        sense=1,
        power=1,
        tags={"refuge", "ditch"},
    ),
}

OFFERINGS = {
    "oil_jug": Offering(
        id="oil_jug",
        label="the little oil jug",
        phrase="a little oil jug wrapped in cloth",
        fragile=True,
        loss_text="the little oil jug had cracked, and a dark gold tear of oil was running through the cloth",
        safe_text="the little oil jug was still whole inside its cloth",
        tags={"oil", "fragile"},
    ),
    "honey_cakes": Offering(
        id="honey_cakes",
        label="the honey cakes",
        phrase="a tray of honey cakes covered with a linen cloth",
        fragile=False,
        loss_text="the honey cakes had slid and broken apart under the cloth",
        safe_text="the honey cakes were still neat and sweet under the linen cloth",
        tags={"food"},
    ),
    "flower_bowl": Offering(
        id="flower_bowl",
        label="the flower bowl",
        phrase="a shallow bowl of white flowers",
        fragile=True,
        loss_text="the flower bowl had chipped, and white petals were stuck to the wet crack",
        safe_text="the flower bowl was still bright and unbroken",
        tags={"flowers", "fragile"},
    ),
    "salt_loaf": Offering(
        id="salt_loaf",
        label="the salt loaf",
        phrase="a round salt loaf in a reed basket",
        fragile=False,
        loss_text="the salt loaf had split down the middle from the hard shaking",
        safe_text="the salt loaf still sat firm in the reed basket",
        tags={"bread"},
    ),
}

GIRL_NAMES = ["Mira", "Eleni", "Dara", "Sana", "Nia", "Lina", "Thale", "Rena"]
BOY_NAMES = ["Toma", "Ivo", "Nerin", "Pavel", "Sorin", "Darin", "Leos", "Maro"]
TRAITS = ["careful", "patient", "steady", "thoughtful", "quick", "bold", "proud"]


@dataclass
class StoryParams:
    route: str
    omen: str
    refuge: str
    offering: str
    child_name: str
    child_gender: str
    elder: str
    trait: str
    delay: int = 0
    relation: str = "grandmother"
    trust: int = 8
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
    "lorry": [
        (
            "What is a lorry?",
            "A lorry is a big heavy truck used to carry things from one place to another. Because it is large and heavy, it needs more room to pass safely than a person does."
        )
    ],
    "warning": [
        (
            "Why should you listen to an early warning?",
            "An early warning gives you time to choose a safe place before danger is close. If you wait until the last moment, you have fewer good choices."
        )
    ],
    "dust": [
        (
            "Why can dust rise before a lorry arrives?",
            "A moving lorry shakes the road and pushes air ahead of it, so dust can lift before the truck is right beside you. That makes dust a useful sign that something big is coming."
        )
    ],
    "bell": [
        (
            "Why might a bell help people on a road?",
            "A bell lets people hear something coming before they can see it. That extra warning gives them time to move somewhere safe."
        )
    ],
    "earth": [
        (
            "Why can the ground shake when a heavy vehicle comes?",
            "A heavy vehicle presses hard on the road, and that force can make the ground tremble a little. Feeling that shake can warn you to step aside."
        )
    ],
    "refuge": [
        (
            "Why is a safe place beside a road important?",
            "A safe place gives you somewhere to stand that is away from wheels and away from the narrowest part of the road. Good safety means planning where to go before danger is right in front of you."
        )
    ],
    "fragile": [
        (
            "What does fragile mean?",
            "Fragile means something can crack or break easily if it is bumped or shaken. That is why fragile things must be carried gently."
        )
    ],
}
KNOWLEDGE_ORDER = ["lorry", "warning", "dust", "bell", "earth", "refuge", "fragile"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    route = f["route"]
    outcome = f["outcome"]
    offering = f["offering_cfg"]
    if outcome == "safe" and f["timing"] == "early":
        return [
            f'Write a short myth-like story for a 3-to-5-year-old that includes the word "lorry" and uses repetition as a road warning.',
            f"Tell a suspenseful little myth where {child.id} remembers an elder's repeated advice at the first omen and waits in safety while a lorry passes.",
            f"Write a lesson-learned story about carrying {offering.label} along {route.label}, hearing the warning early, and choosing patience over hurry.",
        ]
    if outcome == "safe":
        return [
            f'Write a short myth-like story for a 3-to-5-year-old that includes the word "lorry" and builds suspense through repeated warnings.',
            f"Tell a little myth where {child.id} almost hurries, remembers the lesson just in time, and waits in a safe place as the lorry thunders by.",
            f"Write a lesson-learned story in which a child reaches safety late but still learns to listen to the first warning next time.",
        ]
    return [
        f'Write a short myth-like story for a 3-to-5-year-old that includes the word "lorry" and uses repetition to teach caution.',
        f"Tell a suspenseful road myth where {child.id} waits too long to obey an elder's warning, and the gift in the basket is lost even though the child is safe.",
        f"Write a lesson-learned story in which repeated warnings come before a lorry, and the child understands at last why early listening matters.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    route = f["route"]
    omen = f["omen"]
    refuge = f["refuge"]
    offering = f["offering_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child carrying {offering.label} along {route.label}, and the elder who taught the road rule. The story follows whether {child.id} listens before the lorry arrives."
        ),
        (
            f"What warning did {elder.label_word} teach {child.id}?",
            f"{elder.label_word.capitalize()} taught {child.id} to step aside when the warning signs began and to stand still while the lorry passed. The repeated saying mattered because the road was too narrow to share safely."
        ),
        (
            f"What was the first sign that made the story feel suspenseful?",
            f"The first sign was this: {omen.first_sign.lower()} That small warning made the child choose between hurrying on and trusting the lesson."
        ),
    ]
    if f["timing"] == "early":
        qa.append(
            (
                f"How did {child.id} stay safe?",
                f"{child.id} listened at the first warning and went straight to {refuge.label}. That gave enough time to wait calmly before the lorry filled the road."
            )
        )
    else:
        qa.append(
            (
                f"Why did the danger grow before {child.id} stepped aside?",
                f"{child.id} wanted to be quicker than the warning and waited for a stronger sign. That delay made the lorry come much closer before {child.pronoun()} moved into safety."
            )
        )
    if outcome == "safe":
        qa.append(
            (
                f"What happened to {offering.label}?",
                f"{offering.safe_text[0].upper()}{offering.safe_text[1:]}. It stayed safe because {child.id} reached a real refuge before the lorry was too close."
            )
        )
    else:
        qa.append(
            (
                f"What lesson did {child.id} learn when the lorry passed?",
                f"{offering.loss_text[0].upper()}{offering.loss_text[1:]}. {child.id} was safe, but the loss showed that listening late can still cost something precious."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {child.id} changed. After that day, {child.pronoun()} stepped aside at the first warning instead of arguing with the road."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"lorry", "warning", "refuge"}
    tags |= set(f["omen"].tags)
    if f["offering_cfg"].fragile:
        tags.add("fragile")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="cliff_road",
        omen="tremor",
        refuge="niche",
        offering="oil_jug",
        child_name="Toma",
        child_gender="boy",
        elder="grandmother",
        trait="careful",
        delay=0,
        relation="grandmother",
        trust=9,
    ),
    StoryParams(
        route="olive_lane",
        omen="bell",
        refuge="courtyard",
        offering="honey_cakes",
        child_name="Mira",
        child_gender="girl",
        elder="grandfather",
        trait="quick",
        delay=0,
        relation="grandfather",
        trust=6,
    ),
    StoryParams(
        route="river_bend",
        omen="bell",
        refuge="stone_steps",
        offering="flower_bowl",
        child_name="Darin",
        child_gender="boy",
        elder="grandmother",
        trait="bold",
        delay=1,
        relation="grandmother",
        trust=5,
    ),
    StoryParams(
        route="cliff_road",
        omen="dust",
        refuge="fig_gate",
        offering="salt_loaf",
        child_name="Eleni",
        child_gender="girl",
        elder="grandfather",
        trait="patient",
        delay=0,
        relation="grandfather",
        trust=8,
    ),
    StoryParams(
        route="river_bend",
        omen="tremor",
        refuge="willow_gap",
        offering="oil_jug",
        child_name="Sorin",
        child_gender="boy",
        elder="grandmother",
        trait="proud",
        delay=1,
        relation="grandmother",
        trust=4,
    ),
]


def explain_rejection(route: Route, omen: Omen, refuge: Refuge) -> str:
    if omen.id not in route.omens:
        return (
            f"(No story: {route.label} does not honestly give the omen '{omen.id}'. "
            f"This road supports warnings that fit its terrain and sound.)"
        )
    if refuge.sense < SENSE_MIN:
        return (
            f"(No story: {refuge.label} is not a sensible safe place. A storyworld should prefer a real refuge beside the road.)"
        )
    if refuge.id not in route.refuges:
        return (
            f"(No story: {refuge.label} does not belong on {route.label}, so the child would have no believable place to step aside.)"
        )
    return "(No story: this combination is unreasonable.)"


def outcome_of(params: StoryParams) -> str:
    route = ROUTES[params.route]
    refuge = REFUGES[params.refuge]
    if would_heed_early(params.relation, params.trait, params.trust):
        return "safe"
    return "safe" if sheltered(refuge, route, params.delay) else "lost"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(Route, Omen, Refuge) :- route(Route), omen(Omen), refuge(Refuge),
                              affords_omen(Route, Omen),
                              allows_refuge(Route, Refuge),
                              sense(Refuge, S), sense_min(M), S >= M.

% --- timing and outcome ----------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- cautious_now(T), trait(T).
init_caution(3) :- trait(T), not cautious_now(T).
relation_bonus(2) :- relation(grandmother).
relation_bonus(2) :- relation(grandfather).
relation_bonus(1) :- relation(mother).
relation_bonus(1) :- relation(father).
trust_bonus(1) :- trust(V), V >= 7.
trust_bonus(0) :- trust(V), V < 7.
authority(C + R + T) :- init_caution(C), relation_bonus(R), trust_bonus(T).
heed_early :- authority(A), pride_init(P), A > P.

severity(S + D) :- chosen_route(R), route_severity(R, S), delay(D).
safe_from_refuge :- chosen_refuge(Ref), refuge_power(Ref, P), severity(V), P >= V.

outcome(safe) :- heed_early.
outcome(safe) :- not heed_early, safe_from_refuge.
outcome(lost) :- not heed_early, not safe_from_refuge.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("route_severity", route_id, route.severity))
        for omen_id in sorted(route.omens):
            lines.append(asp.fact("affords_omen", route_id, omen_id))
        for refuge_id in sorted(route.refuges):
            lines.append(asp.fact("allows_refuge", route_id, refuge_id))
    for omen_id in OMENS:
        lines.append(asp.fact("omen", omen_id))
    for refuge_id, refuge in REFUGES.items():
        lines.append(asp.fact("refuge", refuge_id))
        lines.append(asp.fact("sense", refuge_id, refuge.sense))
        lines.append(asp.fact("refuge_power", refuge_id, refuge.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("pride_init", int(PRIDE_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_refuge", params.refuge),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("trait", params.trait),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        buf = io.StringIO()
        saved = sys.stdout
        try:
            sys.stdout = buf
            emit(smoke, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = saved
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a myth-like warning about a narrow road, repeated signs, and a lorry."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--refuge", choices=REFUGES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how late the child moves after warning signs; higher makes loss more likely")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible route/omen/refuge combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.omen and args.refuge:
        route = ROUTES[args.route]
        omen = OMENS[args.omen]
        refuge = REFUGES[args.refuge]
        if not (omen_fits(route, omen) and refuge_fits(route, refuge)):
            raise StoryError(explain_rejection(route, omen, refuge))
    if args.refuge and REFUGES[args.refuge].sense < SENSE_MIN:
        route = ROUTES[args.route] if args.route else next(iter(ROUTES.values()))
        omen = OMENS[args.omen] if args.omen else next(iter(OMENS.values()))
        raise StoryError(explain_rejection(route, omen, REFUGES[args.refuge]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.omen is None or combo[1] == args.omen)
        and (args.refuge is None or combo[2] == args.refuge)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, omen_id, refuge_id = rng.choice(sorted(combos))
    offering_id = args.offering or rng.choice(sorted(OFFERINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    elder = args.elder or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    trust = rng.randint(4, 9)
    relation = elder
    return StoryParams(
        route=route_id,
        omen=omen_id,
        refuge=refuge_id,
        offering=offering_id,
        child_name=name,
        child_gender=gender,
        elder=elder,
        trait=trait,
        delay=delay,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.omen not in OMENS:
        raise StoryError(f"(Unknown omen: {params.omen})")
    if params.refuge not in REFUGES:
        raise StoryError(f"(Unknown refuge: {params.refuge})")
    if params.offering not in OFFERINGS:
        raise StoryError(f"(Unknown offering: {params.offering})")
    route = ROUTES[params.route]
    omen = OMENS[params.omen]
    refuge = REFUGES[params.refuge]
    offering = OFFERINGS[params.offering]
    if not (omen_fits(route, omen) and refuge_fits(route, refuge)):
        raise StoryError(explain_rejection(route, omen, refuge))

    world = tell(
        route=route,
        omen=omen,
        refuge=refuge,
        offering_cfg=offering,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder,
        trait=params.trait,
        relation=params.relation,
        trust=params.trust,
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
        print(f"{len(combos)} compatible (route, omen, refuge) combos:\n")
        for route, omen, refuge in combos:
            print(f"  {route:11} {omen:8} {refuge}")
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
            header = f"### {p.child_name}: {p.route}, {p.omen}, {p.refuge} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
