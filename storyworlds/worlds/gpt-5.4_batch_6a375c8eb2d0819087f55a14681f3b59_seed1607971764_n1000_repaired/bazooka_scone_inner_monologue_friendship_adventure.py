#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bazooka_scone_inner_monologue_friendship_adventure.py
=================================================================================

A standalone storyworld for a tiny adventure tale about two friends, a pretend
bazooka, and a shared scone.

The heart of this world is simple and state-driven:

- two friends set out on a small adventure toward a goal,
- one child wants to keep carrying a big pretend bazooka prop,
- they also have one scone meant to be shared at the top,
- the path ahead is tricky enough that showing off and holding everything at
  once can squash the snack and hurt the friendship,
- a grounded warning, an inner-monologue hesitation, and a practical carrying
  plan decide whether the adventure ends warmly or hollowly.

The world enforces a reasonableness gate: there must be a real obstacle, and the
chosen carrying plan must be a sensible one.  A low-sense plan is known to the
world but refused.  Even a sensible plan can be too late if the hero spends too
long wobbling before listening.

Run it
------
    python storyworlds/worlds/gpt-5.4/bazooka_scone_inner_monologue_friendship_adventure.py
    python storyworlds/worlds/gpt-5.4/bazooka_scone_inner_monologue_friendship_adventure.py --route rope_bridge --bazooka cardboard_bazooka --scone berry_scone
    python storyworlds/worlds/gpt-5.4/bazooka_scone_inner_monologue_friendship_adventure.py --route meadow_path
    python storyworlds/worlds/gpt-5.4/bazooka_scone_inner_monologue_friendship_adventure.py --plan toss_it
    python storyworlds/worlds/gpt-5.4/bazooka_scone_inner_monologue_friendship_adventure.py --all
    python storyworlds/worlds/gpt-5.4/bazooka_scone_inner_monologue_friendship_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bazooka_scone_inner_monologue_friendship_adventure.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    obstacle: str
    scenery: str
    top_image: str
    risk: int
    need_hands: int
    need_compact: bool
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
class BazookaProp:
    id: str
    label: str
    phrase: str
    made_of: str
    imagine: str
    compact: bool
    bulk: int
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
class SconeCfg:
    id: str
    label: str
    phrase: str
    smell: str
    crumbs: str
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
class Goal:
    id: str
    label: str
    phrase: str
    victory: str
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
class CarryPlan:
    id: str
    sense: int
    power: int
    hands_free: int
    compact_ok: bool
    snack_safe: bool
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


def _r_wobble(world: World) -> list[str]:
    route = world.get("route")
    hero = world.get("hero")
    friend = world.get("friend")
    scone = world.get("scone")
    if not world.facts.get("crossing"):
        return []
    if world.facts.get("secured"):
        return []
    if route.attrs.get("risk", 0) <= 0:
        return []
    sig = ("wobble", world.facts.get("delay_stage", 0))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["wobble"] += 1
    scone.meters["squashed"] += 1
    friend.memes["worry"] += 1
    out = ["__wobble__"]
    if scone.meters["squashed"] >= THRESHOLD:
        out.append("__squash__")
    return out


def _r_hurt(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    scone = world.get("scone")
    if scone.meters["squashed"] < THRESHOLD:
        return []
    sig = ("hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["guilt"] += 1
    friend.memes["hurt"] += 1
    return ["__hurt__"]


def _r_repair(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if not world.facts.get("apologized"):
        return []
    sig = ("repair",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    friend.memes["hurt"] = 0.0
    hero.memes["guilt"] = 0.0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    return ["__repair__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="repair", tag="social", apply=_r_repair),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for item in produced:
            if item.startswith("__"):
                continue
            world.say(item)
    return produced


def hazard_exists(route: Route, bazooka: BazookaProp) -> bool:
    return route.risk > 0 and (route.need_compact or route.need_hands > 0 or bazooka.bulk > 0)


def sensible_plans() -> list[CarryPlan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def is_secured(plan: CarryPlan, route: Route, bazooka: BazookaProp, delay: int) -> bool:
    compact_ok = (not route.need_compact) or plan.compact_ok or bazooka.compact
    enough_hands = plan.hands_free >= route.need_hands
    enough_power = plan.power >= route.risk + delay
    return compact_ok and enough_hands and enough_power and plan.snack_safe


def best_plan() -> CarryPlan:
    return max(PLANS.values(), key=lambda p: (p.sense, p.power))


def predict_crossing(world: World, route: Route, bazooka: BazookaProp) -> dict:
    sim = world.copy()
    sim.facts["crossing"] = True
    sim.facts["secured"] = False
    sim.facts["delay_stage"] = 0
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("hero").meters["wobble"],
        "squashed": sim.get("scone").meters["squashed"],
        "hurt": sim.get("friend").memes["hurt"],
        "compact_need": route.need_compact,
        "need_hands": route.need_hands,
        "bazooka_compact": bazooka.compact,
    }


def setting_line(goal: Goal) -> str:
    return {
        "beacon": "The whole garden looked like a secret kingdom, with clover fields, stone ridges, and one bright place to reach.",
        "fort": "The yard seemed to stretch into a map of cliffs and caves, all leading toward a brave little fort.",
        "bell": "Every stepping stone felt like part of a lost trail, and somewhere ahead waited a bell worth finding.",
    }[goal.id]


def introduce(world: World, hero: Entity, friend: Entity, bazooka: BazookaProp,
              scone: Entity, goal: Goal) -> None:
    hero.memes["pride"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    friend.memes["care"] += 1
    world.say(
        f"{hero.id} and {friend.id} were best friends, and that morning they turned the yard into an adventure trail."
    )
    world.say(setting_line(goal))
    world.say(
        f"{hero.id} carried {bazooka.phrase}, made of {bazooka.made_of}, and pretended it was {bazooka.imagine}."
    )
    world.say(
        f"{friend.id} brought {scone.phrase}. It smelled {SCONES[world.facts['scone_cfg'].id].smell}, and they meant to split it at {goal.phrase}."
    )


def approach(world: World, route: Route, goal: Goal) -> None:
    world.say(
        f"At last they reached {route.phrase}, the hard part of the trail before {goal.phrase}. {route.scenery}"
    )
    world.say(
        f'Beyond it, they could already see {goal.victory}.'
    )


def warn(world: World, friend: Entity, hero: Entity, route: Route, bazooka: BazookaProp) -> None:
    pred = predict_crossing(world, route, bazooka)
    world.facts["predicted_squash"] = pred["squashed"]
    world.facts["predicted_need_hands"] = pred["need_hands"]
    world.facts["predicted_compact"] = pred["compact_need"]
    need = "both hands free" if route.need_hands >= 2 else "a steady hand"
    extra = ""
    if route.need_compact and not bazooka.compact:
        extra = f" And that big bazooka will catch on {route.obstacle}."
    world.say(
        f'"Wait," said {friend.id}. "This part needs {need}, and the scone will get squashed if you try to carry everything at once.{extra}"'
    )


def inner_monologue(world: World, hero: Entity, bazooka: BazookaProp, friend: Entity) -> None:
    hero.memes["stubborn"] += 1
    world.say(
        f"In {hero.id}'s head, a noisy thought stomped around: If I put the bazooka down now, maybe I will not look like the brave scout anymore."
    )
    world.say(
        f"Then another thought, quieter but harder to ignore, asked whether looking brave mattered more than reaching the top with {friend.id}."
    )


def hesitate(world: World, hero: Entity, friend: Entity, route: Route, delay: int) -> None:
    if delay <= 0:
        return
    world.facts["crossing"] = True
    world.facts["secured"] = False
    for step in range(delay):
        world.facts["delay_stage"] = step + 1
        propagate(world, narrate=False)
        if step == 0:
            world.say(
                f"{hero.id} took one stubborn step onto {route.label} with the bazooka tucked awkwardly under one arm and the scone in the other hand."
            )
        else:
            world.say(
                f"{hero.pronoun().capitalize()} tried another step, and the whole brave idea felt less brave and more wobbly."
            )
    if world.get("hero").meters["wobble"] >= THRESHOLD:
        world.say(
            f"The path shifted under {hero.pronoun('possessive')} shoes. The bazooka bumped first, and the scone gave a soft, unhappy squash."
        )
    if world.get("friend").memes["hurt"] >= THRESHOLD:
        world.say(
            f"{friend.id} looked at the squashed snack and went quiet. That hurt more than the wobble."
        )
    world.facts["crossing"] = False


def choose_plan(world: World, hero: Entity, friend: Entity, plan: CarryPlan,
                route: Route, bazooka: BazookaProp) -> None:
    world.facts["selected_plan"] = plan.id
    if is_secured(plan, route, bazooka, int(world.facts.get("delay", 0))):
        world.facts["secured"] = True
        world.say(
            f"{hero.id} let out a long breath. \"You're right,\" {hero.pronoun()} said. Then {hero.pronoun()} {plan.text}."
        )
    else:
        world.facts["secured"] = False
        world.say(
            f"{hero.id} tried to fix things fast and {plan.fail}."
        )


def cross_success(world: World, hero: Entity, friend: Entity, route: Route, goal: Goal) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.facts["crossing"] = False
    world.say(
        f"Together they crossed {route.label}. This time the hard part felt like a puzzle they were solving side by side."
    )
    world.say(
        f"When they reached {goal.phrase}, the wind seemed brighter somehow, as if the adventure liked teams better than show-offs."
    )


def apology_and_share(world: World, hero: Entity, friend: Entity, scone: Entity, goal: Goal) -> None:
    world.facts["apologized"] = True
    propagate(world, narrate=False)
    scone.meters["shared"] += 1
    world.say(
        f'"I wanted to look grand," {hero.id} admitted, "but I nearly spoiled our snack and our climb. I\'m sorry."'
    )
    world.say(
        f"{friend.id} smiled a little and bumped shoulders with {hero.pronoun('object')}. They broke the scone in two and ate it at {goal.phrase}, with {SCONES[world.facts['scone_cfg'].id].crumbs} on their fingers."
    )
    world.say(
        f"Beside them, the bazooka was only a prop again, and that made room for the best part of the adventure: the friendship stayed big."
    )


def cross_fail(world: World, hero: Entity, friend: Entity, route: Route, goal: Goal,
               plan: CarryPlan) -> None:
    world.facts["crossing"] = True
    world.facts["secured"] = False
    world.facts["delay_stage"] = int(world.facts.get("delay", 0)) + 10
    propagate(world, narrate=False)
    world.facts["crossing"] = False
    hero.memes["lonely"] += 1
    friend.memes["sad"] += 1
    world.say(
        f"But it was too late. {plan.fail.capitalize()}, and the scone slumped into a crumby mess."
    )
    world.say(
        f"They still made it across {route.label}, yet {goal.phrase} did not feel triumphant at all."
    )
    world.say(
        f"The view was wide, but the victory felt small. {hero.id} set down the bazooka and wished {hero.pronoun()} had listened before the adventure turned thin and lonely."
    )


def late_lesson(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f'"Next time," {friend.id} said softly, "let the team matter first."'
    )
    world.say(
        f"{hero.id} nodded. In {hero.pronoun('possessive')} head, the loud show-off thought had finally gone quiet."
    )


def tell(route: Route, bazooka: BazookaProp, scone_cfg: SconeCfg, goal: Goal,
         plan: CarryPlan, hero_name: str = "Nia", hero_type: str = "girl",
         friend_name: str = "Owen", friend_type: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    world.facts.update(
        route_cfg=route,
        bazooka_cfg=bazooka,
        scone_cfg=scone_cfg,
        goal_cfg=goal,
        plan_cfg=plan,
        crossing=False,
        secured=False,
        delay=delay,
        delay_stage=0,
        apologized=False,
    )

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=["brave", "imaginative"],
        attrs={},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        role="friend",
        traits=["steady", "kind"],
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="grownup",
        label="the parent",
        attrs={},
    ))
    route_ent = world.add(Entity(
        id="route",
        type="route",
        label=route.label,
        phrase=route.phrase,
        attrs={
            "risk": route.risk,
            "need_hands": route.need_hands,
            "need_compact": route.need_compact,
            "obstacle": route.obstacle,
        },
    ))
    bazooka_ent = world.add(Entity(
        id="bazooka",
        type="prop",
        label=bazooka.label,
        phrase=bazooka.phrase,
        attrs={"compact": bazooka.compact, "bulk": bazooka.bulk},
    ))
    scone = world.add(Entity(
        id="scone",
        type="snack",
        label=scone_cfg.label,
        phrase=scone_cfg.phrase,
        attrs={"shared_for": "both friends"},
    ))
    world.facts.update(hero=hero, friend=friend, parent=parent, route=route_ent,
                       bazooka=bazooka_ent, scone=scone)

    introduce(world, hero, friend, bazooka, scone, goal)
    world.para()
    approach(world, route, goal)
    warn(world, friend, hero, route, bazooka)
    inner_monologue(world, hero, bazooka, friend)
    hesitate(world, hero, friend, route, delay)
    world.para()
    choose_plan(world, hero, friend, plan, route, bazooka)

    success = is_secured(plan, route, bazooka, delay)
    if success:
        cross_success(world, hero, friend, route, goal)
        apology_and_share(world, hero, friend, scone, goal)
        outcome = "mended"
    else:
        cross_fail(world, hero, friend, route, goal, plan)
        late_lesson(world, hero, friend)
        outcome = "lonely"

    world.facts.update(
        outcome=outcome,
        success=success,
        squashed=scone.meters["squashed"] >= THRESHOLD,
        repaired=world.facts.get("apologized", False),
    )
    return world


ROUTES = {
    "rope_bridge": Route(
        id="rope_bridge",
        label="the rope bridge",
        phrase="the rope bridge over the fern ditch",
        obstacle="the side ropes",
        scenery="It swayed over a little ditch full of ferns, and the planks were only wide enough for careful feet.",
        top_image="a smooth stone where the sun made a bright coin of light",
        risk=3,
        need_hands=2,
        need_compact=True,
        tags={"bridge", "adventure"},
    ),
    "log_crossing": Route(
        id="log_crossing",
        label="the fallen log",
        phrase="the fallen log over the creek",
        obstacle="the overhanging branch",
        scenery="Below it, the creek made silver wrinkles, and one branch leaned low over the middle like a gate.",
        top_image="the old stump lookout with the wind brushing the grass",
        risk=2,
        need_hands=1,
        need_compact=False,
        tags={"log", "adventure"},
    ),
    "stone_tunnel": Route(
        id="stone_tunnel",
        label="the stone tunnel",
        phrase="the short stone tunnel under the blackberry hedge",
        obstacle="the low stone arch",
        scenery="It was cool and echoey, and anyone carrying something long had to duck and turn sideways.",
        top_image="the tiny fort of stacked flowerpots at the far side",
        risk=2,
        need_hands=1,
        need_compact=True,
        tags={"tunnel", "adventure"},
    ),
    "meadow_path": Route(
        id="meadow_path",
        label="the meadow path",
        phrase="the wide meadow path",
        obstacle="nothing at all",
        scenery="It was easy and sunny, with nothing to climb, squeeze past, or balance on.",
        top_image="a patch of daisies at the end",
        risk=0,
        need_hands=0,
        need_compact=False,
        tags={"meadow"},
    ),
}

BAZOOKAS = {
    "cardboard_bazooka": BazookaProp(
        id="cardboard_bazooka",
        label="cardboard bazooka",
        phrase="a grand cardboard bazooka painted with red stars",
        made_of="a tube, tape, and brave imagination",
        imagine="a thunder-launcher for a mountain scout",
        compact=False,
        bulk=2,
        tags={"bazooka", "pretend"},
    ),
    "cushion_bazooka": BazookaProp(
        id="cushion_bazooka",
        label="cushion bazooka",
        phrase="a soft cushion bazooka tied from pillows and a blanket roll",
        made_of="pillows, string, and a blanket roll",
        imagine="a cloud-buster for a sky explorer",
        compact=True,
        bulk=1,
        tags={"bazooka", "pretend"},
    ),
    "silver_bazooka": BazookaProp(
        id="silver_bazooka",
        label="silver bazooka",
        phrase="a shiny toy bazooka made from a silver mailing tube",
        made_of="a silver tube and paper fins",
        imagine="a gleaming cave-finder for a daring captain",
        compact=False,
        bulk=2,
        tags={"bazooka", "pretend"},
    ),
}

SCONES = {
    "berry_scone": SconeCfg(
        id="berry_scone",
        label="berry scone",
        phrase="one warm berry scone wrapped in a napkin",
        smell="sweet and buttery",
        crumbs="purple crumbs and sugar sparkles",
        tags={"scone", "snack"},
    ),
    "honey_scone": SconeCfg(
        id="honey_scone",
        label="honey scone",
        phrase="one honey scone folded in wax paper",
        smell="golden and warm",
        crumbs="soft crumbs and a sticky little shine of honey",
        tags={"scone", "snack"},
    ),
    "apple_scone": SconeCfg(
        id="apple_scone",
        label="apple scone",
        phrase="one apple-cinnamon scone tucked in a napkin",
        smell="like apples and toast",
        crumbs="small cinnamon crumbs and apple bits",
        tags={"scone", "snack"},
    ),
}

GOALS = {
    "beacon": Goal(
        id="beacon",
        label="beacon stone",
        phrase="the beacon stone",
        victory="a smooth stone where the sun made a bright coin of light",
        tags={"goal"},
    ),
    "fort": Goal(
        id="fort",
        label="flowerpot fort",
        phrase="the flowerpot fort",
        victory="the tiny fort of stacked flowerpots at the far side",
        tags={"goal"},
    ),
    "bell": Goal(
        id="bell",
        label="garden bell",
        phrase="the garden bell",
        victory="a bent brass bell hanging from a low branch",
        tags={"goal"},
    ),
}

PLANS = {
    "park_then_fetch": CarryPlan(
        id="park_then_fetch",
        sense=3,
        power=4,
        hands_free=2,
        compact_ok=True,
        snack_safe=True,
        text="parked the bazooka by a flat stone, slid the scone into the satchel, and promised to fetch the prop after the crossing",
        fail="parked the bazooka for a second, but only after too much wobbling and too much damage",
        qa_text="parked the bazooka safely and put the scone into the satchel before crossing",
        tags={"satchel", "sharing"},
    ),
    "satchel_and_sling": CarryPlan(
        id="satchel_and_sling",
        sense=3,
        power=3,
        hands_free=2,
        compact_ok=False,
        snack_safe=True,
        text="slid the scone into the satchel and slung the bazooka across the back so both hands could help with the climb",
        fail="slid the scone into the satchel and slung the bazooka back, but the long tube still snagged where the path narrowed",
        qa_text="put the scone in the satchel and carried the bazooka on the back to free both hands",
        tags={"satchel", "sharing"},
    ),
    "carry_together": CarryPlan(
        id="carry_together",
        sense=2,
        power=2,
        hands_free=1,
        compact_ok=True,
        snack_safe=True,
        text="handed the bazooka to the friend for the squeeze through and kept both hands ready for the tricky part",
        fail="handed the bazooka over for a moment, but there still were not enough free hands for the hardest part",
        qa_text="let the friend help carry the bazooka while the hero focused on the path",
        tags={"friendship", "sharing"},
    ),
    "toss_it": CarryPlan(
        id="toss_it",
        sense=1,
        power=0,
        hands_free=2,
        compact_ok=True,
        snack_safe=False,
        text="tossed the scone ahead and hoped it would land safely",
        fail="tossed the scone ahead, which only made a mess",
        qa_text="threw the scone ahead",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Nia", "Mara", "Lila", "Poppy", "Ivy", "Tess", "Rina", "June"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Jude", "Eli", "Ben", "Max"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    if not sensible_plans():
        return combos
    for route_id, route in ROUTES.items():
        for bazooka_id, bazooka in BAZOOKAS.items():
            for scone_id in SCONES:
                for goal_id in GOALS:
                    if hazard_exists(route, bazooka):
                        combos.append((route_id, bazooka_id, scone_id, goal_id))
    return combos


@dataclass
class StoryParams:
    route: str
    bazooka: str
    scone: str
    goal: str
    plan: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
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
    "bazooka": [(
        "What is a bazooka in this story?",
        "In this story, the bazooka is only a pretend prop made for play. It is not a real weapon, and children should only use soft or make-believe adventure gear."
    )],
    "scone": [(
        "What is a scone?",
        "A scone is a soft baked snack, a little like a biscuit or a small cake. People often split one and eat it with a drink or as a treat."
    )],
    "bridge": [(
        "Why do you need both hands on a rope bridge?",
        "A rope bridge can sway and wiggle under your feet. Using both hands helps you hold the ropes and keep your balance."
    )],
    "log": [(
        "Why is a fallen log tricky to cross?",
        "A fallen log can be narrow and slippery. You have to step carefully so you do not wobble and fall off."
    )],
    "tunnel": [(
        "Why can a long thing be hard to carry in a tunnel?",
        "A long thing can bump the walls or catch on the low roof. That makes it harder to move carefully through a tight space."
    )],
    "sharing": [(
        "Why is sharing a snack kind?",
        "Sharing shows that you are thinking about the other person too. It helps a small treat feel like part of being together."
    )],
    "friendship": [(
        "What can a good friend do on a hard path?",
        "A good friend can warn you, help you carry something, or wait while you try again. Friendship means the adventure matters for both people, not just one."
    )],
    "satchel": [(
        "Why is a satchel useful on an adventure?",
        "A satchel keeps your hands free and protects what you are carrying. That makes it easier to climb or balance safely."
    )],
}
KNOWLEDGE_ORDER = ["bazooka", "scone", "bridge", "log", "tunnel", "sharing", "friendship", "satchel"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    route = f["route_cfg"]
    goal = f["goal_cfg"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "bazooka" and "scone" and uses inner monologue.',
        f"Tell a friendship adventure where {hero.id} and {friend.id} head toward {goal.phrase}, but a pretend bazooka and a shared scone make {route.label} tricky.",
        "Write a gentle story where a child has a proud thought inside, listens to a friend, and learns that adventures are better when both friends can enjoy the ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    route = f["route_cfg"]
    bazooka = f["bazooka_cfg"]
    scone = f["scone_cfg"]
    goal = f["goal_cfg"]
    plan = f["plan_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {hero.id} and {friend.id}, going on a little adventure together. {hero.id} carried the pretend {bazooka.label}, and they planned to share a {scone.label} at {goal.phrase}."
        ),
        (
            "Why did the path become a problem?",
            f"The hard part of the trail needed careful carrying, but {hero.id} wanted to hold both the bazooka and the scone at once. {friend.id} could see that the tricky path might squash the snack and spoil the climb."
        ),
        (
            f"What was {hero.id} thinking inside?",
            f"In {hero.id}'s inner monologue, one thought worried that putting the bazooka down would make {hero.pronoun('object')} seem less brave. Then a quieter thought asked whether being a good friend mattered more than showing off."
        ),
    ]
    if outcome == "mended":
        qa.append((
            f"How did they solve the problem on {route.label}?",
            f"{hero.id} listened to {friend.id} and {plan.qa_text}. That gave them a safer way to cross and protected the scone too."
        ))
        qa.append((
            "How did the story end?",
            f"They reached {goal.phrase}, shared the scone, and the friendship felt warm again. The ending proves the adventure worked because they acted like a team."
        ))
    else:
        qa.append((
            "Why did the ending feel lonely?",
            f"The plan came too late, so the scone was already squashed and the proud moment had gone flat. Even though they reached {goal.phrase}, the friendship had been hurt by not listening soon enough."
        ))
        qa.append((
            f"What did {hero.id} learn?",
            f"{hero.id} learned that carrying the bazooka proudly was not as important as caring for the friend beside {hero.pronoun('object')}. The quiet thought in {hero.pronoun('possessive')} head turned out to be the wiser one."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    route = world.facts["route_cfg"]
    bazooka = world.facts["bazooka_cfg"]
    scone = world.facts["scone_cfg"]
    plan = world.facts["plan_cfg"]
    tags |= bazooka.tags
    tags |= scone.tags
    tags |= plan.tags
    if route.id == "rope_bridge":
        tags.add("bridge")
    if route.id == "log_crossing":
        tags.add("log")
    if route.id == "stone_tunnel":
        tags.add("tunnel")
    tags.add("friendship")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} delay={world.facts.get('delay')} plan={world.facts.get('selected_plan', world.facts.get('plan_cfg').id)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="rope_bridge",
        bazooka="cardboard_bazooka",
        scone="berry_scone",
        goal="beacon",
        plan="park_then_fetch",
        hero_name="Nia",
        hero_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        route="stone_tunnel",
        bazooka="silver_bazooka",
        scone="apple_scone",
        goal="fort",
        plan="park_then_fetch",
        hero_name="Milo",
        hero_gender="boy",
        friend_name="June",
        friend_gender="girl",
        parent="father",
        delay=1,
    ),
    StoryParams(
        route="log_crossing",
        bazooka="cushion_bazooka",
        scone="honey_scone",
        goal="bell",
        plan="carry_together",
        hero_name="Lila",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        route="rope_bridge",
        bazooka="silver_bazooka",
        scone="berry_scone",
        goal="beacon",
        plan="satchel_and_sling",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        parent="father",
        delay=2,
    ),
    StoryParams(
        route="stone_tunnel",
        bazooka="cardboard_bazooka",
        scone="honey_scone",
        goal="fort",
        plan="carry_together",
        hero_name="Poppy",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        delay=1,
    ),
]


def explain_rejection(route: Route, bazooka: BazookaProp) -> str:
    if route.risk <= 0:
        return (
            f"(No story: {route.phrase} is too easy. Without a real obstacle, the bazooka and scone never create an honest adventure problem.)"
        )
    if not hazard_exists(route, bazooka):
        return (
            f"(No story: {bazooka.label} does not create a carrying problem on {route.phrase}, so there is no turn for the friendship to solve.)"
        )
    return "(No story: this combination has no grounded obstacle.)"


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    better = ", ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it scores too low on common sense (sense={plan.sense} < {SENSE_MIN}). Try one of the sensible plans: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "mended" if is_secured(PLANS[params.plan], ROUTES[params.route], BAZOOKAS[params.bazooka], params.delay) else "lonely"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(R, B) :- route(R), bazooka(B), risk(R, V), V > 0, bulk(B, K), K > 0.
sensible(P)  :- plan(P), sense(P, S), sense_min(M), S >= M.
valid(R, B, S, G) :- route(R), bazooka(B), scone(S), goal(G), hazard(R, B).

% --- outcome model ---------------------------------------------------------
compact_passes(R, B, P) :- route(R), bazooka(B), plan(P), not needs_compact(R).
compact_passes(R, B, P) :- route(R), bazooka(B), plan(P), needs_compact(R), compact(B).
compact_passes(R, B, P) :- route(R), bazooka(B), plan(P), needs_compact(R), compact_ok(P).

hands_pass(R, P) :- need_hands(R, N), hands_free(P, H), H >= N.
power_pass(R, P, D) :- risk(R, V), power(P, Q), Q >= V + D.
safe_plan(P) :- snack_safe(P).

secured :- chosen_route(R), chosen_bazooka(B), chosen_plan(P), delay(D),
           compact_passes(R, B, P), hands_pass(R, P), power_pass(R, P, D), safe_plan(P).

outcome(mended) :- secured.
outcome(lonely) :- not secured.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("risk", route_id, route.risk))
        lines.append(asp.fact("need_hands", route_id, route.need_hands))
        if route.need_compact:
            lines.append(asp.fact("needs_compact", route_id))
    for bazooka_id, bazooka in BAZOOKAS.items():
        lines.append(asp.fact("bazooka", bazooka_id))
        lines.append(asp.fact("bulk", bazooka_id, bazooka.bulk))
        if bazooka.compact:
            lines.append(asp.fact("compact", bazooka_id))
    for scone_id in SCONES:
        lines.append(asp.fact("scone", scone_id))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("power", plan_id, plan.power))
        lines.append(asp.fact("hands_free", plan_id, plan.hands_free))
        if plan.compact_ok:
            lines.append(asp.fact("compact_ok", plan_id))
        if plan.snack_safe:
            lines.append(asp.fact("snack_safe", plan_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_bazooka", params.bazooka),
        asp.fact("chosen_plan", params.plan),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    c_sense = set(asp_sensible())
    p_sense = {p.id for p in sensible_plans()}
    if c_sense == p_sense:
        print(f"OK: sensible plans match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bazooka, a scone, inner monologue, and friendship on a small adventure."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--bazooka", choices=BAZOOKAS)
    ap.add_argument("--scone", choices=SCONES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the hero keeps wobbling before listening")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_pair(rng: random.Random) -> tuple[str, str, str, str]:
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    friend_pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
    hero_name = rng.choice(hero_pool)
    friend_name = rng.choice([n for n in friend_pool if n != hero_name])
    return hero_name, hero_gender, friend_name, friend_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route is not None:
        route = ROUTES[args.route]
        bazooka_for_check = BAZOOKAS[args.bazooka] if args.bazooka else next(iter(BAZOOKAS.values()))
        if not hazard_exists(route, bazooka_for_check):
            raise StoryError(explain_rejection(route, bazooka_for_check))
    if args.bazooka is not None and args.route is not None:
        route = ROUTES[args.route]
        bazooka = BAZOOKAS[args.bazooka]
        if not hazard_exists(route, bazooka):
            raise StoryError(explain_rejection(route, bazooka))
    if args.plan is not None and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(args.plan))

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.bazooka is None or combo[1] == args.bazooka)
        and (args.scone is None or combo[2] == args.scone)
        and (args.goal is None or combo[3] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, bazooka_id, scone_id, goal_id = rng.choice(sorted(combos))
    plan_id = args.plan or rng.choice(sorted(p.id for p in sensible_plans()))
    hero_name, hero_gender, friend_name, friend_gender = _pick_pair(rng)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        route=route_id,
        bazooka=bazooka_id,
        scone=scone_id,
        goal=goal_id,
        plan=plan_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        delay=delay,
    )


def _must_lookup(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    route = _must_lookup(ROUTES, params.route, "route")
    bazooka = _must_lookup(BAZOOKAS, params.bazooka, "bazooka")
    scone = _must_lookup(SCONES, params.scone, "scone")
    goal = _must_lookup(GOALS, params.goal, "goal")
    plan = _must_lookup(PLANS, params.plan, "plan")
    if not hazard_exists(route, bazooka):
        raise StoryError(explain_rejection(route, bazooka))
    if plan.sense < SENSE_MIN:
        raise StoryError(explain_plan(plan.id))

    world = tell(
        route=route,
        bazooka=bazooka,
        scone_cfg=scone,
        goal=goal,
        plan=plan,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible plans: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, bazooka, scone, goal) combos:\n")
        for route, bazooka, scone, goal in combos:
            print(f"  {route:12} {bazooka:18} {scone:12} {goal}")
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.route} with {p.bazooka} ({p.plan}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
