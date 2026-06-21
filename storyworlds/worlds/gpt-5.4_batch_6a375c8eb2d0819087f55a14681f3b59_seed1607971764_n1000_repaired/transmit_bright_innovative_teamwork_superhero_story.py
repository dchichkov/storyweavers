#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/transmit_bright_innovative_teamwork_superhero_story.py
=================================================================================

A standalone story world about a small team of child-facing superheroes who must
work together to transmit a bright signal when something goes wrong.

The core premise:
- A child hero team is on watch in a colorful city place.
- A problem appears that makes people need guidance or help.
- One hero first thinks about solving it alone.
- The team uses an innovative signal tool to transmit a bright message together.
- If they coordinate in time, help arrives and the city scene becomes safe again.
- If they wait too long for a fast-moving problem, the rescue still happens later,
  but the team learns that teamwork works best early.

This world models:
- typed entities with physical meters and emotional memes
- a small causal engine
- explicit reasonableness constraints over valid combinations
- an inline ASP twin for the validity gate and the ending model
- three QA sets grounded in world state, not parsed from English

Run it
------
    python storyworlds/worlds/gpt-5.4/transmit_bright_innovative_teamwork_superhero_story.py
    python storyworlds/worlds/gpt-5.4/transmit_bright_innovative_teamwork_superhero_story.py --asp
    python storyworlds/worlds/gpt-5.4/transmit_bright_innovative_teamwork_superhero_story.py --verify
    python storyworlds/worlds/gpt-5.4/transmit_bright_innovative_teamwork_superhero_story.py -n 5 --seed 7 --qa
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
TEAMWORK_BONUS = 2
SOLO_LIMIT = 2


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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    perch: str
    crowd: str
    affords: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    label: str
    need: str
    scene: str
    target: str
    urgency: int
    needs: set[str] = field(default_factory=set)
    solo_ok: bool = False
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
class SignalTool:
    id: str
    label: str
    phrase: str
    action: str
    beam: str
    power: int
    supports: set[str] = field(default_factory=set)
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
    arrival: str
    fix: str
    aftermath: str
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

    def heroes(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "hero"]

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


def _r_problem_spreads(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    if problem.meters["active"] < THRESHOLD:
        return out
    sig = ("problem_spreads",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("city").meters["risk"] += problem.meters["urgency"]
    for hero in world.heroes():
        hero.memes["concern"] += 1
    out.append("__risk__")
    return out


def _r_signal_ready(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    if tool.meters["charged"] < THRESHOLD:
        return out
    enough_positions = sum(1 for hero in world.heroes() if hero.meters["in_place"] >= THRESHOLD)
    if enough_positions < 2:
        return out
    sig = ("signal_ready",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tool.meters["aligned"] += 1
    out.append("__aligned__")
    return out


def _r_transmit(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    if tool.meters["aligned"] < THRESHOLD or tool.meters["raised"] < THRESHOLD:
        return out
    sig = ("transmit",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tool.meters["transmitting"] += 1
    world.get("helper").meters["summoned"] += 1
    for hero in world.heroes():
        hero.memes["hope"] += 1
    out.append("__transmit__")
    return out


CAUSAL_RULES = [
    Rule(name="problem_spreads", tag="physical", apply=_r_problem_spreads),
    Rule(name="signal_ready", tag="physical", apply=_r_signal_ready),
    Rule(name="transmit", tag="physical", apply=_r_transmit),
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


def compatible(place: Place, problem: Problem, tool: SignalTool) -> bool:
    return (
        tool.id in place.affords
        and problem.needs.issubset(tool.supports)
        and tool.power >= problem.urgency
    )


def teamwork_strength(problem: Problem, tool: SignalTool, delay: int) -> int:
    return tool.power + TEAMWORK_BONUS - delay


def solo_strength(tool: SignalTool, delay: int) -> int:
    return min(tool.power, SOLO_LIMIT) - delay


def solo_possible(problem: Problem, tool: SignalTool, delay: int) -> bool:
    return problem.solo_ok and compatible(PLACES["sky_school_roof"], problem, tool) and solo_strength(tool, delay) >= problem.urgency


def team_success(problem: Problem, tool: SignalTool, delay: int) -> bool:
    return teamwork_strength(problem, tool, delay) >= problem.urgency


def predict_signal(world: World, problem: Problem, tool: SignalTool) -> dict:
    sim = world.copy()
    sim.get("problem").meters["active"] = 1.0
    sim.get("problem").meters["urgency"] = float(problem.urgency)
    propagate(sim, narrate=False)
    sim.get("tool").meters["charged"] = 1.0
    for hero in sim.heroes():
        hero.meters["in_place"] = 1.0
    sim.get("tool").meters["raised"] = 1.0
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("city").meters["risk"],
        "summoned": sim.get("helper").meters["summoned"] >= THRESHOLD,
    }


def introduce_team(world: World, lead: Entity, partner: Entity, place: Place) -> None:
    for hero in (lead, partner):
        hero.memes["joy"] += 1
        hero.memes["duty"] += 1
    world.say(
        f"In {place.label}, two young superheroes kept watch from {place.perch}. "
        f"{lead.id} wore a {lead.attrs['color']} cape, and {partner.id} wore a {partner.attrs['color']} mask."
    )
    world.say(
        f"They called themselves the {world.facts['team_name']}, and they loved helping together whenever {place.crowd}."
    )


def problem_appears(world: World, problem: Problem) -> None:
    p = world.get("problem")
    p.meters["active"] = 1.0
    p.meters["urgency"] = float(problem.urgency)
    world.say(problem.scene)
    propagate(world, narrate=False)
    world.say(
        f"People needed a signal to {problem.need}, but the usual alarm could not reach {problem.target}."
    )


def solo_idea(world: World, lead: Entity, tool: SignalTool) -> None:
    lead.memes["bravery"] += 1
    world.say(
        f'"I can do it myself," {lead.id} said, gripping {tool.phrase}. '
        f'For one moment, the mission felt like a race for a single hero.'
    )


def warning(world: World, partner: Entity, lead: Entity, problem: Problem, tool: SignalTool) -> None:
    pred = predict_signal(world, problem, tool)
    world.facts["predicted_risk"] = pred["risk"]
    partner.memes["teamwork"] += 1
    world.say(
        f'{partner.id} looked across the city and shook {partner.pronoun("possessive")} head. '
        f'"Not alone," {partner.pronoun()} said. "This problem is moving fast, and we have to transmit a bright signal together."'
    )
    world.say(
        f'{partner.pronoun().capitalize()} pointed at {tool.label}. "That innovative tool works best when one of us steadies it and the other lines up the beam."'
    )


def choose_team(world: World, lead: Entity, partner: Entity) -> None:
    lead.memes["teamwork"] += 1
    partner.memes["trust"] += 1
    world.say(
        f'{lead.id} took a breath and nodded. "{partner.id}, you take the far mark. I\'ll hold the center."'
    )
    world.say(
        f"At once, the mission stopped feeling lonely. It became a teamwork plan."
    )


def heroes_move(world: World, lead: Entity, partner: Entity, place: Place) -> None:
    lead.meters["in_place"] = 1.0
    partner.meters["in_place"] = 1.0
    world.say(
        f"{lead.id} sprinted to the middle of {place.perch}, while {partner.id} climbed to the edge where the wind was clearest."
    )


def ready_tool(world: World, tool: SignalTool) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["charged"] = 1.0
    tool_ent.meters["raised"] = 1.0
    world.say(
        f"Together they lifted {tool.phrase} and set it just right. {tool.action.capitalize()}, ready to flash across the sky."
    )
    propagate(world, narrate=False)


def transmit_signal(world: World, tool: SignalTool) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then the heroes made the tool sing with light. It began to transmit {tool.beam} that leapt over roofs and rails."
    )


def helper_arrives(world: World, helper: Helper, problem: Problem) -> None:
    world.get("problem").meters["active"] = 0.0
    world.get("city").meters["risk"] = 0.0
    world.say(helper.arrival)
    world.say(helper.fix.format(problem=problem.label, target=problem.target))
    world.say(helper.aftermath)


def late_but_safe(world: World, helper: Helper, problem: Problem) -> None:
    world.get("problem").meters["active"] = 0.0
    world.get("city").meters["risk"] = 0.0
    for hero in world.heroes():
        hero.memes["regret"] += 1
    world.say(
        "The first beam came too late to stop all the confusion. The street stayed noisy and worried until extra helpers rushed in from nearby blocks."
    )
    world.say(helper.fix.format(problem=problem.label, target=problem.target))
    world.say(
        "When the danger was over, the two young heroes looked at each other and understood that teamwork works best before a problem grows big."
    )


def closing_win(world: World, lead: Entity, partner: Entity, tool: SignalTool, place: Place) -> None:
    for hero in (lead, partner):
        hero.memes["relief"] += 1
        hero.memes["pride"] += 1
    world.say(
        f'"Team signal complete!" {partner.id} cheered.'
    )
    world.say(
        f"High above {place.label}, {tool.phrase} still glimmered in the air, bright as a tiny new star."
    )


def closing_lesson(world: World, lead: Entity, partner: Entity, tool: SignalTool) -> None:
    for hero in (lead, partner):
        hero.memes["lesson"] += 1
        hero.memes["relief"] += 1
    world.say(
        f'{lead.id} bumped fists with {partner.id}. "Next time," {lead.pronoun()} said, "we start together."'
    )
    world.say(
        f"They lowered {tool.phrase} carefully. Even after the rush was over, its bright glow reminded them that an innovative plan shines best when shared."
    )


def tell(
    place: Place,
    problem: Problem,
    tool: SignalTool,
    helper: Helper,
    lead_name: str = "Nova",
    lead_gender: str = "girl",
    partner_name: str = "Bolt",
    partner_gender: str = "boy",
    lead_color: str = "golden",
    partner_color: str = "blue",
    parent_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(place)
    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        role="hero",
        attrs={"color": lead_color},
        tags={"hero"},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="hero",
        attrs={"color": partner_color},
        tags={"hero"},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type=parent_type,
        role="mentor",
        label="the mentor",
        tags={"mentor"},
    ))
    city = world.add(Entity(
        id="city",
        kind="thing",
        type="city",
        label=place.label,
        tags={"city"},
    ))
    problem_ent = world.add(Entity(
        id="problem",
        kind="thing",
        type="problem",
        label=problem.label,
        tags=set(problem.tags),
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        tags=set(tool.tags),
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="thing",
        type="helper",
        label=helper.label,
        tags=set(helper.tags),
    ))
    for hero in (lead, partner):
        hero.meters["in_place"] = 0.0
        hero.memes["teamwork"] = 0.0
        hero.memes["trust"] = 0.0
        hero.memes["hope"] = 0.0
        hero.memes["relief"] = 0.0
        hero.memes["lesson"] = 0.0
        hero.memes["regret"] = 0.0
    city.meters["risk"] = 0.0
    problem_ent.meters["active"] = 0.0
    problem_ent.meters["urgency"] = 0.0
    tool_ent.meters["charged"] = 0.0
    tool_ent.meters["raised"] = 0.0
    tool_ent.meters["aligned"] = 0.0
    tool_ent.meters["transmitting"] = 0.0
    helper_ent.meters["summoned"] = 0.0

    world.facts.update(
        team_name=f"{lead_name} and {partner_name}",
        place=place,
        problem_cfg=problem,
        tool_cfg=tool,
        helper_cfg=helper,
        lead=lead,
        partner=partner,
        mentor=mentor,
        delay=delay,
    )

    introduce_team(world, lead, partner, place)
    world.para()
    problem_appears(world, problem)
    solo_idea(world, lead, tool)
    warning(world, partner, lead, problem, tool)
    choose_team(world, lead, partner)
    world.para()
    heroes_move(world, lead, partner, place)
    ready_tool(world, tool)
    transmit_signal(world, tool)

    success = team_success(problem, tool, delay)
    world.para()
    if success:
        helper_arrives(world, helper, problem)
        closing_win(world, lead, partner, tool, place)
        outcome = "saved"
    else:
        late_but_safe(world, helper, problem)
        closing_lesson(world, lead, partner, tool)
        outcome = "late"

    world.facts.update(
        outcome=outcome,
        compatible=compatible(place, problem, tool),
        transmitted=tool_ent.meters["transmitting"] >= THRESHOLD,
        helper_summoned=helper_ent.meters["summoned"] >= THRESHOLD,
        city_safe=city.meters["risk"] < THRESHOLD,
    )
    return world


PLACES = {
    "sky_school_roof": Place(
        id="sky_school_roof",
        label="Sparkle City",
        scene="the painted roof of Sky School",
        perch="the painted roof of Sky School",
        crowd="children below laughed and pointed at the clouds",
        affords={"prism_relay", "beam_kites", "mirror_badges"},
        tags={"city", "roof"},
    ),
    "harbor_clocktower": Place(
        id="harbor_clocktower",
        label="Harbor Harborfront",
        scene="the windy clocktower above the harbor",
        perch="the windy clocktower balcony",
        crowd="boats rocked by the shining docks",
        affords={"prism_relay", "beam_kites"},
        tags={"harbor", "tower"},
    ),
    "sunny_train_yard": Place(
        id="sunny_train_yard",
        label="Railway Square",
        scene="the signal arch above Railway Square",
        perch="the red signal arch",
        crowd="families waited beside the little city train",
        affords={"prism_relay", "mirror_badges"},
        tags={"train", "square"},
    ),
}

PROBLEMS = {
    "fog_ferry": Problem(
        id="fog_ferry",
        label="the foggy ferry lane",
        need="guide the ferry back toward the dock",
        scene="A silver blanket of fog rolled over the harbor, and the ferry horn sounded lost and far away.",
        target="the dock",
        urgency=3,
        needs={"long_range", "steady"},
        solo_ok=False,
        tags={"fog", "harbor"},
    ),
    "dark_tunnel": Problem(
        id="dark_tunnel",
        label="the dark tunnel entrance",
        need="show the way to the station stairs",
        scene="All at once, the tunnel lights blinked off, and the station mouth turned dark as a cave.",
        target="the station stairs",
        urgency=2,
        needs={"steady", "aimed"},
        solo_ok=True,
        tags={"dark", "station"},
    ),
    "stray_balloon": Problem(
        id="stray_balloon",
        label="the runaway parade balloon",
        need="warn the parade team where the balloon was drifting",
        scene="A giant star balloon broke free from its ribbon and floated between the parade roofs.",
        target="the parade team",
        urgency=2,
        needs={"aimed"},
        solo_ok=True,
        tags={"parade", "sky"},
    ),
    "smoke_garden": Problem(
        id="smoke_garden",
        label="the smoky rooftop garden",
        need="point the rescue crew toward the right building",
        scene="Gray cooking smoke swirled across the roof gardens and hid the little footbridge between them.",
        target="the right building",
        urgency=3,
        needs={"long_range", "aimed"},
        solo_ok=False,
        tags={"smoke", "roof"},
    ),
}

TOOLS = {
    "prism_relay": SignalTool(
        id="prism_relay",
        label="prism relay",
        phrase="the prism relay",
        action="its crystal fins opened",
        beam="a bright ribbon of rainbow light",
        power=3,
        supports={"long_range", "steady", "aimed"},
        tags={"prism", "light"},
    ),
    "beam_kites": SignalTool(
        id="beam_kites",
        label="beam kites",
        phrase="the beam kites",
        action="their silver tails stretched tight",
        beam="a bright zigzag line of light",
        power=3,
        supports={"long_range", "steady"},
        tags={"kite", "light"},
    ),
    "mirror_badges": SignalTool(
        id="mirror_badges",
        label="mirror badges",
        phrase="the mirror badges",
        action="their polished faces caught the sun",
        beam="a bright flashing pattern",
        power=2,
        supports={"aimed", "steady"},
        tags={"mirror", "light"},
    ),
}

HELPERS = {
    "rescue_train": Helper(
        id="rescue_train",
        label="the Rescue Train",
        arrival="Far below, the Rescue Train answered with a bell and rolled into view.",
        fix="Its driver followed the signal and led everyone safely past {problem} toward {target}.",
        aftermath="Soon the worried crowd was moving again, and brave cheers bounced off the walls.",
        tags={"rescue", "train"},
    ),
    "harbor_glider": Helper(
        id="harbor_glider",
        label="the Harbor Glider",
        arrival="From the clouds came the Harbor Glider, wings shining over the water.",
        fix="Its pilot followed the signal and guided help straight past {problem} toward {target}.",
        aftermath="The mist no longer felt scary once the shining wings were overhead.",
        tags={"rescue", "glider"},
    ),
    "street_team": Helper(
        id="street_team",
        label="the Street Team",
        arrival="A quick Street Team van turned the corner with its rooftop lamp blinking.",
        fix="The crew followed the signal and hurried past {problem} toward {target}.",
        aftermath="Soon the block sounded cheerful again instead of worried.",
        tags={"rescue", "team"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Skye", "Ruby", "Iris", "Zara", "Ember"]
BOY_NAMES = ["Bolt", "Jett", "Max", "Leo", "Finn", "Kai", "Ace", "Nico"]
COLORS = ["golden", "blue", "scarlet", "violet", "green", "silver"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for problem_id, problem in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if compatible(place, problem, tool):
                    combos.append((place_id, problem_id, tool_id))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    helper: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    lead_color: str
    partner_color: str
    mentor: str
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
    "transmit": [
        (
            "What does transmit mean?",
            "Transmit means to send something from one place to another. A signal can transmit light, sound, or a message so someone far away can notice it."
        )
    ],
    "bright": [
        (
            "What does bright mean?",
            "Bright means giving off a lot of light or looking very clear and shiny. A bright signal is easier to see from far away."
        )
    ],
    "innovative": [
        (
            "What does innovative mean?",
            "Innovative means using a new or clever idea. An innovative tool solves a problem in a smart way that people may not have tried before."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork helpful?",
            "Teamwork helps because two or more people can share jobs and help each other. When everyone does a part, hard problems can become easier and safer."
        )
    ],
    "prism": [
        (
            "What is a prism?",
            "A prism is a clear shape that can bend and split light. It can make light spread in useful directions."
        )
    ],
    "mirror": [
        (
            "What does a mirror do with light?",
            "A mirror bounces light away from its shiny surface. That is why mirrors can help aim a flash of light."
        )
    ],
    "kite": [
        (
            "Why can a kite carry a signal?",
            "A kite can hold something up high in the air where it is easier to see. If it has bright ribbons or lights, people far away can notice it."
        )
    ],
    "fog": [
        (
            "Why is fog hard to see through?",
            "Fog is made of tiny water drops floating in the air. Those drops scatter light, so faraway things look blurry."
        )
    ],
    "smoke": [
        (
            "Why can smoke hide things?",
            "Smoke is full of tiny bits floating in the air, and they block or blur what you see. That is why clear signals matter when smoke is around."
        )
    ],
    "rescue": [
        (
            "What does a rescue team do?",
            "A rescue team helps people get out of danger and find the safe way. They follow signals, maps, and careful plans to reach the right place."
        )
    ],
}
KNOWLEDGE_ORDER = ["transmit", "bright", "innovative", "teamwork", "prism", "mirror", "kite", "fog", "smoke", "rescue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    problem = f["problem_cfg"]
    tool = f["tool_cfg"]
    place = f["place"]
    return [
        f'Write a superhero story for a 3-to-5-year-old that uses the words "transmit," "bright," and "innovative," and shows teamwork.',
        f"Tell a gentle superhero story where {lead.id} and {partner.id} use {tool.label} to send a signal across {place.label} when {problem.label} causes trouble.",
        f"Write a short city-rescue story where two young heroes first think about working alone, then choose teamwork to solve a fast-moving problem."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    place = f["place"]
    problem = f["problem_cfg"]
    tool = f["tool_cfg"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young superheroes, {lead.id} and {partner.id}. They watch over {place.label} together and try to help when trouble appears."
        ),
        (
            "What problem did the heroes notice?",
            f"They noticed {problem.label}. People needed help because the heroes had to {problem.need}."
        ),
        (
            f"Why did {partner.id} say they should work together?",
            f"{partner.id} knew the signal tool worked best when one hero steadied it and the other lined up the beam. {partner.pronoun().capitalize()} also understood that the problem was moving fast, so teamwork would make the message stronger."
        ),
        (
            f"How did the heroes transmit the signal?",
            f"They took two positions, lifted {tool.phrase}, and lined it up together. That teamwork made a bright signal leap across the city so help could see it."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How was the city helped at the end?",
                f"{helper.label.capitalize()} followed the signal and fixed the danger near {problem.target}. Because the heroes worked together quickly, the worried scene became safe again."
            )
        )
        qa.append(
            (
                "How did the ending prove something changed?",
                f"At first the mission felt like a job for one hero, but the ending showed a whole city answering a team signal. The glowing tool above the city proved their shared plan really worked."
            )
        )
    else:
        qa.append(
            (
                "Did the heroes still learn something even though they were late?",
                f"Yes. Help still arrived, but the team saw that waiting made the trouble bigger. Afterward they understood they should begin together the next time a mission starts."
            )
        )
        qa.append(
            (
                "How did the ending prove something changed?",
                f"In the beginning, {lead.id} wanted to handle the mission alone. At the end, {lead.pronoun()} said they should start together, showing the heroes had learned a teamwork lesson."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"transmit", "bright", "innovative", "teamwork", "rescue"}
    tool = f["tool_cfg"]
    problem = f["problem_cfg"]
    if tool.id == "prism_relay":
        tags.add("prism")
    if tool.id == "mirror_badges":
        tags.add("mirror")
    if tool.id == "beam_kites":
        tags.add("kite")
    if "fog" in problem.tags:
        tags.add("fog")
    if "smoke" in problem.tags:
        tags.add("smoke")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="sky_school_roof",
        problem="dark_tunnel",
        tool="mirror_badges",
        helper="rescue_train",
        lead_name="Nova",
        lead_gender="girl",
        partner_name="Bolt",
        partner_gender="boy",
        lead_color="golden",
        partner_color="blue",
        mentor="mother",
        delay=0,
    ),
    StoryParams(
        place="harbor_clocktower",
        problem="fog_ferry",
        tool="prism_relay",
        helper="harbor_glider",
        lead_name="Luna",
        lead_gender="girl",
        partner_name="Jett",
        partner_gender="boy",
        lead_color="silver",
        partner_color="green",
        mentor="father",
        delay=0,
    ),
    StoryParams(
        place="sunny_train_yard",
        problem="stray_balloon",
        tool="mirror_badges",
        helper="street_team",
        lead_name="Mira",
        lead_gender="girl",
        partner_name="Max",
        partner_gender="boy",
        lead_color="violet",
        partner_color="scarlet",
        mentor="mother",
        delay=1,
    ),
    StoryParams(
        place="sky_school_roof",
        problem="smoke_garden",
        tool="prism_relay",
        helper="street_team",
        lead_name="Iris",
        lead_gender="girl",
        partner_name="Kai",
        partner_gender="boy",
        lead_color="blue",
        partner_color="golden",
        mentor="father",
        delay=2,
    ),
]


def explain_rejection(place: Place, problem: Problem, tool: SignalTool) -> str:
    if tool.id not in place.affords:
        return (
            f"(No story: {tool.label} does not fit {place.label}. "
            f"That place cannot support this signal tool.)"
        )
    missing = sorted(problem.needs - tool.supports)
    if missing:
        return (
            f"(No story: {tool.label} cannot handle {problem.label}. "
            f"It is missing the needed signal features {missing}.)"
        )
    if tool.power < problem.urgency:
        return (
            f"(No story: {tool.label} is too weak for {problem.label}. "
            f"The problem is more urgent than that tool's signal power.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    return "saved" if team_success(problem, tool, params.delay) else "late"


ASP_RULES = r"""
compatible(Place, Prob, Tool) :-
    affords(Place, Tool),
    problem(Prob),
    tool(Tool),
    not missing_need(Prob, Tool),
    power(Tool, P),
    urgency(Prob, U),
    P >= U.

missing_need(Prob, Tool) :-
    needs(Prob, Need),
    not supports(Tool, Need).

team_strength(Prob, Tool, Delay, P + Bonus - Delay) :-
    compatible(_, Prob, Tool),
    power(Tool, P),
    teamwork_bonus(Bonus),
    delay(Delay).

outcome(saved) :-
    chosen_problem(Prob),
    chosen_tool(Tool),
    delay(Delay),
    compatible(chosen_place_value, Prob, Tool),
    team_strength(Prob, Tool, Delay, Strength),
    urgency(Prob, U),
    Strength >= U.

outcome(late) :-
    chosen_problem(Prob),
    chosen_tool(Tool),
    delay(Delay),
    compatible(chosen_place_value, Prob, Tool),
    team_strength(Prob, Tool, Delay, Strength),
    urgency(Prob, U),
    Strength < U.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for tool_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, tool_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("urgency", problem_id, problem.urgency))
        for need in sorted(problem.needs):
            lines.append(asp.fact("needs", problem_id, need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        for support in sorted(tool.supports):
            lines.append(asp.fact("supports", tool_id, support))
    lines.append(asp.fact("teamwork_bonus", TEAMWORK_BONUS))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    chosen_alias = "chosen_place_value :- chosen_place(P), place(P)."
    return f"{asp_facts()}\n{chosen_alias}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_tool", params.tool),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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
    for s in range(60):
        try:
            args = build_parser().parse_args([])
            p = resolve_params(args, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story in verify smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child superhero team transmits a bright signal together."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_hero(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.problem and args.tool:
        place = PLACES[args.place]
        problem = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        if not compatible(place, problem, tool):
            raise StoryError(explain_rejection(place, problem, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, problem_id, tool_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    lead_name, lead_gender = _pick_hero(rng)
    partner_name, partner_gender = _pick_hero(rng, avoid=lead_name)
    lead_color, partner_color = rng.sample(COLORS, 2)
    mentor = args.mentor or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 3)
    return StoryParams(
        place=place_id,
        problem=problem_id,
        tool=tool_id,
        helper=helper_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        lead_color=lead_color,
        partner_color=partner_color,
        mentor=mentor,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        problem = PROBLEMS[params.problem]
        tool = TOOLS[params.tool]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not compatible(place, problem, tool):
        raise StoryError(explain_rejection(place, problem, tool))

    world = tell(
        place=place,
        problem=problem,
        tool=tool,
        helper=helper,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        lead_color=params.lead_color,
        partner_color=params.partner_color,
        parent_type=params.mentor,
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
        print(asp_program("", "#show compatible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, tool) combos:\n")
        for place, problem, tool in combos:
            print(f"  {place:18} {problem:14} {tool}")
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
            header = f"### {p.lead_name} & {p.partner_name}: {p.problem} at {p.place} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
