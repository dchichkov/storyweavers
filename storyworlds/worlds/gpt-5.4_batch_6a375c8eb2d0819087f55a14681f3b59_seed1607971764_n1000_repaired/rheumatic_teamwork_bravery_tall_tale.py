#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rheumatic_teamwork_bravery_tall_tale.py
==================================================================

A standalone story world for a tiny Tall-Tale-style domain about teamwork and
bravery: two children on an enormous prairie must help ring a storm bell before
a wild wall of dust reaches the barns. Their old ranch helper has rheumatic
knees and cannot make the steep climb alone, so the children must choose a
reasonable route and a sensible way to carry the bell rope up the hill.

The world enforces a small common-sense constraint set:

- each hill has a steepness
- each route has a traction/safety level
- each helper has a carrying power and a boldness
- the old helper's rheumatic body makes some plans too slow or too risky

A valid story needs a route and helper that can really reach the bell in time.
The prose then follows the simulated state: setup, warning, struggle, brave turn,
and an ending image that proves the change.

Run it
------
    python storyworlds/worlds/gpt-5.4/rheumatic_teamwork_bravery_tall_tale.py
    python storyworlds/worlds/gpt-5.4/rheumatic_teamwork_bravery_tall_tale.py --hill thunder_rise
    python storyworlds/worlds/gpt-5.4/rheumatic_teamwork_bravery_tall_tale.py --route scree
    python storyworlds/worlds/gpt-5.4/rheumatic_teamwork_bravery_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/rheumatic_teamwork_bravery_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/rheumatic_teamwork_bravery_tall_tale.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | animal | thing | place
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "man", "uncle"}
        animal = {"horse", "mule", "ox", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"aunt": "aunt", "uncle": "uncle"}.get(self.type, self.label or self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
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
class Hill:
    id: str
    label: str
    image: str
    steepness: int
    wind: int
    size_boast: str
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
class Route:
    id: str
    label: str
    phrase: str
    traction: int
    speed: int
    sense: int
    danger_text: str
    climb_text: str
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
    type: str
    phrase: str
    power: int
    boldness: int
    surefoot: int
    sense: int
    boast: str
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
class Bell:
    id: str
    label: str
    phrase: str
    weight: int
    sound: str
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
class Weather:
    id: str
    label: str
    danger: int
    sky_text: str
    stakes_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "partner"}]


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    rancher = world.get("rancher")
    hill = world.facts["hill_cfg"]
    route = world.facts["route_cfg"]
    if rancher.meters["climbing"] < THRESHOLD:
        return out
    sig = ("strain", route.id, hill.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    strain = max(0, hill.steepness - route.traction)
    rancher.meters["pain"] += float(strain)
    if strain > 0:
        rancher.memes["worry"] += 1
        out.append("__strain__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    storm = world.get("storm")
    if storm.meters["approaching"] < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.children():
        kid.memes["fear"] += 1
    out.append("__fear__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="strain", tag="physical", apply=_r_strain),
    Rule(name="fear", tag="emotional", apply=_r_fear),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def helper_can_pull(helper: Helper, bell: Bell) -> bool:
    return helper.power >= bell.weight


def route_can_hold(helper: Helper, route: Route, hill: Hill) -> bool:
    need = max(hill.steepness - helper.surefoot, 1)
    return route.traction >= need


def brave_enough(helper: Helper, weather: Weather) -> bool:
    return helper.boldness >= weather.danger


def plan_score(helper: Helper, route: Route, hill: Hill, weather: Weather) -> int:
    return helper.power + helper.boldness + helper.surefoot + route.traction + route.speed - hill.steepness - weather.danger


def valid_plan(helper: Helper, route: Route, hill: Hill, bell: Bell, weather: Weather) -> bool:
    return (
        helper_can_pull(helper, bell)
        and route_can_hold(helper, route, hill)
        and brave_enough(helper, weather)
        and route.sense >= SENSE_MIN
        and helper.sense >= SENSE_MIN
        and plan_score(helper, route, hill, weather) >= 4
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hill_id, hill in HILLS.items():
        for route_id, route in ROUTES.items():
            for helper_id, helper in HELPERS.items():
                for weather_id, weather in WEATHERS.items():
                    if valid_plan(helper, route, hill, BELLS["prairie_bell"], weather):
                        combos.append((hill_id, route_id, helper_id, weather_id))
    return sorted(combos)


def explain_rejection(hill: Hill, route: Route, helper: Helper, weather: Weather) -> str:
    bell = BELLS["prairie_bell"]
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: {helper.label} is known in the world, but that helper is too wild "
            f"for a careful rescue plan. Pick a steadier helper.)"
        )
    if route.sense < SENSE_MIN:
        return (
            f"(No story: {route.label} is too risky for carrying {bell.label} toward "
            f"{hill.label} with a dust storm coming. Pick a safer route.)"
        )
    if not helper_can_pull(helper, bell):
        return (
            f"(No story: {helper.label} cannot pull {bell.label}. The plan needs enough "
            f"strength to move the rope and bell gear.)"
        )
    if not brave_enough(helper, weather):
        return (
            f"(No story: {helper.label} would balk at {weather.label}. A helper that freezes "
            f"at the storm cannot honestly reach the top.)"
        )
    if not route_can_hold(helper, route, hill):
        return (
            f"(No story: {route.label} does not give enough footing for {helper.label} on "
            f"{hill.label}. The climb would fail before the bell could ring.)"
        )
    return (
        f"(No story: that plan is too slow or weak for {weather.label} on {hill.label}. "
        f"Try a stronger helper or a better route.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_plan(world: World, hill: Hill, route: Route, helper: Helper, weather: Weather) -> dict:
    sim = world.copy()
    sim.facts["hill_cfg"] = hill
    sim.facts["route_cfg"] = route
    sim.facts["helper_cfg"] = helper
    sim.facts["weather_cfg"] = weather
    sim.get("storm").meters["approaching"] = 1.0
    sim.get("rancher").meters["climbing"] = 1.0
    propagate(sim, narrate=False)
    success = valid_plan(helper, route, hill, BELLS["prairie_bell"], weather)
    return {
        "pain": sim.get("rancher").meters["pain"],
        "success": success,
        "score": plan_score(helper, route, hill, weather),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup(world: World, lead: Entity, partner: Entity, rancher: Entity, hill: Hill, bell: Bell) -> None:
    for kid in (lead, partner):
        kid.memes["joy"] += 1
    rancher.memes["care"] += 1
    world.say(
        f"Out on the open prairie, {hill.label} stood so high that {hill.size_boast}. "
        f"At its top hung {bell.phrase}, a bell the ranch used when weather came galloping in."
    )
    world.say(
        f"{lead.id} and {partner.id} spent the morning stacking hay bales taller than porches "
        f"and telling each other which cloud looked most likely to bite."
    )
    world.say(
        f"Down below worked old {rancher.id}, whose rheumatic knees could still predict weather "
        f"better than any rooster, even if they groaned at every steep step."
    )


def warning(world: World, lead: Entity, partner: Entity, rancher: Entity, weather: Weather) -> None:
    storm = world.get("storm")
    storm.meters["approaching"] = 1.0
    propagate(world, narrate=False)
    rancher.memes["worry"] += 1
    world.say(weather.sky_text)
    world.say(
        f'Old {rancher.id} shaded {rancher.pronoun("possessive")} eyes and said, '
        f'"That sky means trouble. {weather.stakes_text}"'
    )


def need_bell(world: World, rancher: Entity, hill: Hill, bell: Bell) -> None:
    world.say(
        f'"We have to ring {bell.label} from the top of {hill.label}," {rancher.id} said. '
        f'"Folks will hear it all the way to the far fence."'
    )
    world.say(
        f"Then {rancher.pronoun()} took one step toward the hill and winced. "
        f"{rancher.pronoun('possessive').capitalize()} rheumatic knees were fierce in weather like this."
    )


def volunteer(world: World, lead: Entity, partner: Entity, rancher: Entity, helper: Helper) -> None:
    lead.memes["bravery"] += 1
    partner.memes["loyalty"] += 1
    world.say(
        f'"Then we will do it," said {lead.id}, drawing up so straight that even the grass seemed '
        f"to stand with {lead.pronoun('object')}."
    )
    world.say(
        f'{partner.id} nodded at once. "Together," {partner.pronoun()} said, and both children turned '
        f"to {helper.phrase}, because {helper.boast}."
    )


def choose_plan(world: World, lead: Entity, partner: Entity, rancher: Entity,
                hill: Hill, route: Route, helper: Helper, weather: Weather) -> None:
    pred = predict_plan(world, hill, route, helper, weather)
    world.facts["predicted_pain"] = pred["pain"]
    world.facts["predicted_score"] = pred["score"]
    world.say(
        f"They studied {route.phrase}. It looked {route.danger_text}, but it also climbed toward the bell."
    )
    if pred["pain"] >= THRESHOLD:
        world.say(
            f"{rancher.id} shook {rancher.pronoun('possessive')} head. "
            f'"That path is no friend to rheumatic joints, but it may still be the best road for {helper.label}."'
        )
    world.say(
        f"So the children looped the bell rope, checked the knots twice, and made a plan: "
        f"{lead.id} would lead, {partner.id} would steady the load, and {helper.label} would pull."
    )


def start_climb(world: World, lead: Entity, partner: Entity, rancher: Entity,
                hill: Hill, route: Route, helper: Helper) -> None:
    rancher.meters["climbing"] = 1.0
    propagate(world, narrate=False)
    helper_ent = world.get("helper")
    helper_ent.meters["hauling"] = 1.0
    for kid in (lead, partner):
        kid.meters["climbing"] += 1
    world.say(
        f"Up they went by {route.phrase}. {route.climb_text}"
    )
    world.say(
        f"{lead.id} leaned into the rope, {partner.id} braced from the side, and {helper.label} dug in so hard "
        f"that the dirt looked plowed behind {helper_ent.pronoun('object')}."
    )


def trouble(world: World, lead: Entity, partner: Entity, helper: Helper, route: Route) -> None:
    for kid in (lead, partner):
        kid.memes["fear"] += 1
    world.say(
        f"Halfway up, a mean gust slapped across {route.label}. Dust flew around them in brown sheets."
    )
    world.say(
        f"The load jerked sideways, and for one stomach-dropping moment it seemed the rope would slide back down."
    )


def brave_turn(world: World, lead: Entity, partner: Entity, helper: Helper) -> None:
    helper_ent = world.get("helper")
    lead.memes["bravery"] += 1
    partner.memes["bravery"] += 1
    lead.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    helper_ent.memes["teamwork"] += 1
    world.say(
        f"But {lead.id} planted both heels and shouted for {partner.id} to take the side pull. "
        f"{partner.id} jumped to the other line without a blink."
    )
    world.say(
        f"Then the two of them counted together -- one, two, three -- and {helper.label} answered with a mighty lunge."
    )
    world.say(
        "That was the brave part of the day: not one of them acting alone, but all three trusting the others at the same instant."
    )


def reach_top(world: World, lead: Entity, partner: Entity, helper: Helper, hill: Hill, bell: Bell) -> None:
    world.get("bell").meters["ready"] = 1.0
    world.say(
        f"Step by step they won the hill. At last they reached the top of {hill.label}, where the wind tried to comb the prairie flat."
    )
    world.say(
        f"{lead.id} and {partner.id} hauled the final loop into place, and together they yanked {bell.label} until {bell.sound}."
    )


def resolution(world: World, lead: Entity, partner: Entity, rancher: Entity, weather: Weather) -> None:
    world.get("storm").meters["warned"] = 1.0
    rancher.memes["pride"] += 1
    for kid in (lead, partner):
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"The sound rolled over the ranch, over the creek, and over the far pasture too. Barn doors banged shut, "
        f"horses were led in, and every loose thing on the place got tied down before {weather.label} arrived."
    )
    world.say(
        f"When the children came back down, old {rancher.id} put a hand on each shoulder and smiled. "
        f'"That was teamwork," {rancher.pronoun()} said. "And that was bravery done the sensible way."'
    )


def ending_image(world: World, lead: Entity, partner: Entity, rancher: Entity, helper: Helper, hill: Hill) -> None:
    for kid in (lead, partner):
        kid.memes["joy"] += 1
    world.say(
        f"By sunset the storm was only a purple bruise far away, and {hill.label} stood peaceful again."
    )
    world.say(
        f"{lead.id} and {partner.id} sat on the fence beside {helper.label}, sharing cornbread while old {rancher.id} rubbed "
        f"{rancher.pronoun('possessive')} rheumatic knees and laughed that next time the bell ought to ring itself."
    )
    world.say(
        "From then on, whenever a cloud came stomping over the plains, folks remembered how two small children and one steady helper had outworked the weather."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(hill: Hill, route: Route, helper: Helper, weather: Weather,
         lead_name: str = "June", lead_gender: str = "girl",
         partner_name: str = "Bo", partner_gender: str = "boy",
         rancher_name: str = "Aunt May", rancher_type: str = "aunt") -> World:
    bell = BELLS["prairie_bell"]
    world = World()

    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        label=lead_name,
        role="lead",
        traits=["bold"],
        attrs={},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        traits=["steady"],
        attrs={},
    ))
    rancher = world.add(Entity(
        id=rancher_name,
        kind="character",
        type=rancher_type,
        label="the rancher",
        role="rancher",
        traits=["wise", "rheumatic"],
        attrs={},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="animal",
        type=helper.type,
        label=helper.label,
        role="helper",
        traits=["strong"],
        attrs={},
    ))
    bell_ent = world.add(Entity(
        id="bell",
        kind="thing",
        type="bell",
        label=bell.label,
        role="bell",
        attrs={},
    ))
    storm = world.add(Entity(
        id="storm",
        kind="thing",
        type="storm",
        label=weather.label,
        role="storm",
        attrs={},
    ))
    world.add(Entity(
        id="hill",
        kind="place",
        type="hill",
        label=hill.label,
        role="hill",
        attrs={},
    ))

    world.facts.update(
        hill_cfg=hill,
        route_cfg=route,
        helper_cfg=helper,
        weather_cfg=weather,
        bell_cfg=bell,
        lead=lead,
        partner=partner,
        rancher=rancher,
        helper=helper_ent,
        bell=bell_ent,
        storm=storm,
        success=False,
        outcome="",
    )

    setup(world, lead, partner, rancher, hill, bell)
    world.para()
    warning(world, lead, partner, rancher, weather)
    need_bell(world, rancher, hill, bell)
    volunteer(world, lead, partner, rancher, helper)
    choose_plan(world, lead, partner, rancher, hill, route, helper, weather)
    world.para()
    start_climb(world, lead, partner, rancher, hill, route, helper)
    trouble(world, lead, partner, helper, route)
    brave_turn(world, lead, partner, helper)
    reach_top(world, lead, partner, helper, hill, bell)
    world.para()
    resolution(world, lead, partner, rancher, weather)
    ending_image(world, lead, partner, rancher, helper, hill)

    world.facts["success"] = True
    world.facts["outcome"] = "warned"
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
HILLS = {
    "thunder_rise": Hill(
        id="thunder_rise",
        label="Thunder Rise",
        image="a butte",
        steepness=4,
        wind=3,
        size_boast="cowboys said the moon sometimes stopped there to catch its breath",
        tags={"hill", "prairie"},
    ),
    "coyote_backbone": Hill(
        id="coyote_backbone",
        label="Coyote Backbone",
        image="a ridge",
        steepness=3,
        wind=2,
        size_boast="people joked that a shout from the top came back next Tuesday",
        tags={"hill", "prairie"},
    ),
    "sky_stair": Hill(
        id="sky_stair",
        label="Sky Stair",
        image="a mesa shoulder",
        steepness=5,
        wind=4,
        size_boast="it looked as if giants had once used it for a front porch step",
        tags={"hill", "prairie"},
    ),
}

ROUTES = {
    "switchbacks": Route(
        id="switchbacks",
        label="the switchback trail",
        phrase="the switchback trail",
        traction=3,
        speed=2,
        sense=3,
        danger_text="narrow in spots",
        climb_text="The trail twisted back and forth like a lazy snake, which made it longer but kinder underfoot.",
        tags={"trail", "safe"},
    ),
    "creek_side": Route(
        id="creek_side",
        label="the creek-side path",
        phrase="the creek-side path",
        traction=4,
        speed=3,
        sense=3,
        danger_text="slick with damp clay near the bottom",
        climb_text="The creek hummed beside them while the banks gave better footing than the open slope.",
        tags={"trail", "water"},
    ),
    "scree": Route(
        id="scree",
        label="the scree slide",
        phrase="the scree slide",
        traction=1,
        speed=3,
        sense=1,
        danger_text="like marbles poured over a roof",
        climb_text="Loose stones skittered away under every step, and the whole side of the hill acted as if it wanted to tumble first and think later.",
        tags={"trail", "risky"},
    ),
}

HELPERS = {
    "mule": Helper(
        id="mule",
        label="Molly the mule",
        type="mule",
        phrase="Molly the mule",
        power=3,
        boldness=3,
        surefoot=4,
        sense=3,
        boast="that mule could pull a gatepost out of the ground and still stop politely for a thistle",
        tags={"mule", "animal"},
    ),
    "ox": Helper(
        id="ox",
        label="Blue the ox",
        type="ox",
        phrase="Blue the ox",
        power=5,
        boldness=2,
        surefoot=2,
        sense=3,
        boast="Blue the ox was broad enough to make a barn look narrow",
        tags={"ox", "animal"},
    ),
    "goat": Helper(
        id="goat",
        label="Pepper the goat",
        type="goat",
        phrase="Pepper the goat",
        power=1,
        boldness=4,
        surefoot=5,
        sense=1,
        boast="Pepper could stand on a fence rail in a high wind and grin at thunder",
        tags={"goat", "animal"},
    ),
}

BELLS = {
    "prairie_bell": Bell(
        id="prairie_bell",
        label="the prairie bell",
        phrase="the prairie bell, a brass noisemaker big enough to wake fence posts",
        weight=3,
        sound="it boomed across the plains like a silver thunderclap",
        tags={"bell", "warning"},
    ),
}

WEATHERS = {
    "dust_wall": Weather(
        id="dust_wall",
        label="the dust wall",
        danger=3,
        sky_text="By noon a brown wall of dust was heaving up from the west, tall enough to make the horizon look folded.",
        stakes_text="Get the bell ringing before that dust wall hits, or half the ranch will be blind in it.",
        tags={"storm", "dust"},
    ),
    "black_gust": Weather(
        id="black_gust",
        label="the black gust",
        danger=2,
        sky_text="Soon a black gust came rolling over the grass, with tumbleweeds bowling ahead of it like scouts.",
        stakes_text="If we ring the bell now, the hands can bring in the stock before that black gust smacks the fences.",
        tags={"storm", "wind"},
    ),
    "hail_stampede": Weather(
        id="hail_stampede",
        label="the hail stampede",
        danger=4,
        sky_text="Great bruised clouds bunched together overhead, and the first hailstones began snapping sage leaves clean in half.",
        stakes_text="We must warn everybody this minute, before the hail stampede pounds the roofs and scatters the herd.",
        tags={"storm", "hail"},
    ),
}

GIRL_NAMES = ["June", "Tess", "Mabel", "Ruth", "Lula", "Pearl", "Nell"]
BOY_NAMES = ["Bo", "Cal", "Eli", "Wade", "Jeb", "Otis", "Finn"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hill: str
    route: str
    helper: str
    weather: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    rancher_name: str = "Aunt May"
    rancher_type: str = "aunt"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "rheumatic": [
        (
            "What does rheumatic mean?",
            "Rheumatic means a person's joints can ache and feel stiff, especially when the weather changes. That can make climbing and heavy work harder."
        )
    ],
    "mule": [
        (
            "Why are mules good on rough trails?",
            "Mules are strong and careful with their feet. They can stay steady on rocky ground better than many other animals."
        )
    ],
    "ox": [
        (
            "What is an ox good at?",
            "An ox is good at pulling heavy things because it is very strong. People have long used oxen for slow, powerful work."
        )
    ],
    "bell": [
        (
            "Why would a ranch use a warning bell?",
            "A warning bell can tell people far away that danger is coming. A loud bell helps everyone act quickly at the same time."
        )
    ],
    "dust": [
        (
            "Why is a dust storm dangerous?",
            "A dust storm can make it hard to see and hard to breathe. Animals and people can get lost or hurt if they are not warned in time."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another toward the same goal. They do different parts of the job so the whole job gets done better."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel scared. It is not being reckless; it is staying steady when something hard must be done."
        )
    ],
}
KNOWLEDGE_ORDER = ["rheumatic", "mule", "ox", "bell", "dust", "teamwork", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hill = f["hill_cfg"]
    route = f["route_cfg"]
    helper_cfg = f["helper_cfg"]
    weather = f["weather_cfg"]
    lead = f["lead"]
    partner = f["partner"]
    return [
        'Write a Tall Tale for a 3-to-5-year-old that includes the word "rheumatic" and shows teamwork and bravery.',
        f"Tell a prairie tall tale where {lead.id} and {partner.id} race to ring a warning bell on {hill.label} before {weather.label} arrives.",
        f"Write a story where children and {helper_cfg.label} use {route.label} to do a brave job together, while an older rancher with rheumatic knees guides them from below.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    rancher = f["rancher"]
    helper_cfg = f["helper_cfg"]
    hill = f["hill_cfg"]
    route = f["route_cfg"]
    weather = f["weather_cfg"]
    bell = f["bell_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {partner.id}, two children on a prairie ranch, old {rancher.id}, and {helper_cfg.label}. Together they had to warn the whole ranch."
        ),
        (
            f"Why did they need to ring {bell.label}?",
            f"They needed to ring it because {weather.label} was coming fast. The bell would warn people to shut the barns and bring animals in before the storm hit."
        ),
        (
            f"Why didn't old {rancher.id} climb {hill.label} alone?",
            f"{rancher.id} had rheumatic knees, so steep climbing hurt too much in weather like that. {rancher.pronoun().capitalize()} knew the job mattered, but {rancher.pronoun('possessive')} body could not safely do the whole climb alone."
        ),
        (
            f"How did {lead.id} and {partner.id} show teamwork?",
            f"They made one shared plan instead of rushing in separately. {lead.id} led, {partner.id} steadied the load, and {helper_cfg.label} pulled, so each one did the part that helped the others succeed."
        ),
        (
            "How did they show bravery?",
            f"They kept going when the wind hit and the rope jerked sideways. Their bravery was steady bravery, because they acted together and followed a sensible plan instead of doing something wild."
        ),
        (
            f"What was hard about {route.label}?",
            f"It was hard because the storm gusts shoved dust across it and made the load pull sideways. For a moment it looked as if the rope might slide back down the hill."
        ),
        (
            "How did the story end?",
            f"They reached the top, rang the bell, and warned the ranch in time. By sunset the hill was quiet again, which showed that their brave teamwork had changed a dangerous day into a safe one."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rheumatic", "bell", "teamwork", "bravery"}
    helper_cfg = world.facts["helper_cfg"]
    weather = world.facts["weather_cfg"]
    tags |= set(helper_cfg.tags)
    tags |= {"dust"} if "storm" in weather.tags else set()
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


# ---------------------------------------------------------------------------
# Trace / curated
# ---------------------------------------------------------------------------
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hill="thunder_rise",
        route="switchbacks",
        helper="mule",
        weather="dust_wall",
        lead_name="June",
        lead_gender="girl",
        partner_name="Bo",
        partner_gender="boy",
        rancher_name="Aunt May",
        rancher_type="aunt",
    ),
    StoryParams(
        hill="coyote_backbone",
        route="creek_side",
        helper="ox",
        weather="black_gust",
        lead_name="Tess",
        lead_gender="girl",
        partner_name="Cal",
        partner_gender="boy",
        rancher_name="Aunt May",
        rancher_type="aunt",
    ),
    StoryParams(
        hill="sky_stair",
        route="creek_side",
        helper="mule",
        weather="hail_stampede",
        lead_name="Pearl",
        lead_gender="girl",
        partner_name="Eli",
        partner_gender="boy",
        rancher_name="Aunt May",
        rancher_type="aunt",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(H,R,He,W) :-
    hill(H), route(R), helper(He), weather(W),
    bell(B), chosen_bell(B),
    power(He, HP), weight(B, BW), HP >= BW,
    sense_route(R, RS), sense_helper(He, HS), sense_min(M), RS >= M, HS >= M,
    steepness(H, St), surefoot(He, Sf), Need = St - Sf, Need <= 1, traction(R, Tr), Tr >= 1;
    hill(H), route(R), helper(He), weather(W),
    bell(B), chosen_bell(B),
    power(He, HP), weight(B, BW), HP >= BW,
    sense_route(R, RS), sense_helper(He, HS), sense_min(M), RS >= M, HS >= M,
    steepness(H, St), surefoot(He, Sf), Need = St - Sf, Need > 1, traction(R, Tr), Tr >= Need,
    danger(W, D), boldness(He, Bo), Bo >= D,
    Score = HP + Bo + Sf + Tr + speed(R) - St - D, Score >= 4.

valid2(H,R,He,W) :-
    hill(H), route(R), helper(He), weather(W),
    bell(B), chosen_bell(B),
    power(He, HP), weight(B, BW), HP >= BW,
    sense_route(R, RS), sense_helper(He, HS), sense_min(M), RS >= M, HS >= M,
    steepness(H, St), surefoot(He, Sf), Need = St - Sf, Need <= 1, traction(R, Tr), Tr >= 1,
    danger(W, D), boldness(He, Bo), Bo >= D,
    Score = HP + Bo + Sf + Tr + speed(R) - St - D, Score >= 4.

valid_plan(H,R,He,W) :- valid2(H,R,He,W).

#show valid_plan/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hill_id, hill in HILLS.items():
        lines.append(asp.fact("hill", hill_id))
        lines.append(asp.fact("steepness", hill_id, hill.steepness))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("traction", route_id, route.traction))
        lines.append(asp.fact("speed", route_id, route.speed))
        lines.append(asp.fact("sense_route", route_id, route.sense))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
        lines.append(asp.fact("boldness", helper_id, helper.boldness))
        lines.append(asp.fact("surefoot", helper_id, helper.surefoot))
        lines.append(asp.fact("sense_helper", helper_id, helper.sense))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("danger", weather_id, weather.danger))
    bell = BELLS["prairie_bell"]
    lines.append(asp.fact("bell", bell.id))
    lines.append(asp.fact("chosen_bell", bell.id))
    lines.append(asp.fact("weight", bell.id, bell.weight))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_plan/4."))
    return sorted(set(asp.atoms(model, "valid_plan")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if cl - py:
            print("  only in asp:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(17))
        sample = generate(params)
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("missing QA data from generated sample")
        print("OK: default resolve/generate/QA smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: children, a storm bell, teamwork, and bravery."
    )
    ap.add_argument("--hill", choices=HILLS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--lead-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP reasoner")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.hill is None or combo[0] == args.hill)
        and (args.route is None or combo[1] == args.route)
        and (args.helper is None or combo[2] == args.helper)
        and (args.weather is None or combo[3] == args.weather)
    ]

    if args.hill and args.route and args.helper and args.weather:
        hill = HILLS[args.hill]
        route = ROUTES[args.route]
        helper = HELPERS[args.helper]
        weather = WEATHERS[args.weather]
        if not valid_plan(helper, route, hill, BELLS["prairie_bell"], weather):
            raise StoryError(explain_rejection(hill, route, helper, weather))

    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hill_id, route_id, helper_id, weather_id = rng.choice(sorted(combos))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or _pick_name(rng, lead_gender)
    partner_name = args.partner_name or _pick_name(rng, partner_gender, avoid=lead_name)

    return StoryParams(
        hill=hill_id,
        route=route_id,
        helper=helper_id,
        weather=weather_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        rancher_name="Aunt May",
        rancher_type="aunt",
    )


def generate(params: StoryParams) -> StorySample:
    if params.hill not in HILLS:
        raise StoryError(f"(Unknown hill: {params.hill})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")

    hill = HILLS[params.hill]
    route = ROUTES[params.route]
    helper = HELPERS[params.helper]
    weather = WEATHERS[params.weather]
    bell = BELLS["prairie_bell"]

    if not valid_plan(helper, route, hill, bell, weather):
        raise StoryError(explain_rejection(hill, route, helper, weather))

    world = tell(
        hill=hill,
        route=route,
        helper=helper,
        weather=weather,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        rancher_name=params.rancher_name,
        rancher_type=params.rancher_type,
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
        print(asp_program("#show valid_plan/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hill, route, helper, weather) combos:\n")
        for hill, route, helper, weather in combos:
            print(f"  {hill:16} {route:11} {helper:6} {weather}")
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
            header = f"### {p.lead_name} & {p.partner_name}: {p.weather} on {p.hill} via {p.route} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
