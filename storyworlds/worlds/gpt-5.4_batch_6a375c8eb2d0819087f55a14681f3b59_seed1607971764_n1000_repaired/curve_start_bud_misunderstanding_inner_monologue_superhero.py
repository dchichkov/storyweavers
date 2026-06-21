#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/curve_start_bud_misunderstanding_inner_monologue_superhero.py
=========================================================================================

A standalone story world for a tiny superhero-story domain: a child hero sees a
friend making a rushed move, misunderstands it, acts too fast, then learns what
was really happening and fixes the problem together.

This world is built around:
- a visible misunderstanding
- explicit inner monologue lines driven by world state
- a clear premise, turn, and repair
- superhero flavor without violence
- the required words: "curve", "start", and "bud"

The simulation models:
- physical meters: wind, wobble, spill, safety, bloom_risk
- emotional memes: pride, fear, guilt, relief, trust, jealousy, calm

The reasonableness gate is intentionally small and concrete:
- a hazard must plausibly threaten a fragile plant bud
- a helper action must actually protect the plant from that hazard
- an impulsive interception power must be the kind of move that can jolt or
  spill the plant, making the misunderstanding matter

Run it
------
    python storyworlds/worlds/gpt-5.4/curve_start_bud_misunderstanding_inner_monologue_superhero.py
    python storyworlds/worlds/gpt-5.4/curve_start_bud_misunderstanding_inner_monologue_superhero.py --hazard gust --helper_action move_inside
    python storyworlds/worlds/gpt-5.4/curve_start_bud_misunderstanding_inner_monologue_superhero.py --hazard bees --helper_action move_inside
    python storyworlds/worlds/gpt-5.4/curve_start_bud_misunderstanding_inner_monologue_superhero.py --all
    python storyworlds/worlds/gpt-5.4/curve_start_bud_misunderstanding_inner_monologue_superhero.py --qa
    python storyworlds/worlds/gpt-5.4/curve_start_bud_misunderstanding_inner_monologue_superhero.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = True
    fragile: bool = False
    protective: bool = False
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


# ---------------------------------------------------------------------------
# Domain config
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
class Setting:
    id: str
    place: str
    curve_phrase: str
    shelter: str
    crowd: str
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
class Hazard:
    id: str
    label: str
    threat: str
    threatens_bud: bool
    needs_action: str
    sign: str
    risk_line: str
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
class HelperAction:
    id: str
    label: str
    verb: str
    destination: str
    protects_from: set[str]
    visible_cue: str
    explanation: str
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
class Power:
    id: str
    label: str
    impulse_text: str
    jolt: int
    fixes: set[str]
    repair_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World container
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[str] = []
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

    def think(self, thinker: Entity, text: str) -> None:
        if text:
            self.paragraphs[-1].append(f'{text}')
            self.history.append(f"thought:{thinker.id}:{text}")

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
        clone.history = list(self.history)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
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


def _r_fragile_risk(world: World) -> list[str]:
    out: list[str] = []
    bud = world.get("bud")
    if bud.meters["unsafe"] < THRESHOLD:
        return out
    sig = ("risk", "bud")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bud.meters["bloom_risk"] += 1
    for eid in ("hero", "helper"):
        if eid in world.entities:
            world.get(eid).memes["fear"] += 1
    out.append("__risk__")
    return out


def _r_spill_guilt(world: World) -> list[str]:
    out: list[str] = []
    bud = world.get("bud")
    hero = world.get("hero")
    if bud.meters["spill"] < THRESHOLD:
        return out
    sig = ("guilt", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["guilt"] += 1
    hero.memes["pride"] = 0.0
    out.append("__spill__")
    return out


def _r_repair_relief(world: World) -> list[str]:
    out: list[str] = []
    bud = world.get("bud")
    if bud.meters["safe"] < THRESHOLD:
        return out
    sig = ("relief", "all")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("hero", "helper", "mentor"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
    bud.meters["bloom_risk"] = 0.0
    out.append("__safe__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="fragile_risk", tag="physical", apply=_r_fragile_risk),
    Rule(name="spill_guilt", tag="emotional", apply=_r_spill_guilt),
    Rule(name="repair_relief", tag="emotional", apply=_r_repair_relief),
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
# Constraint logic
# ---------------------------------------------------------------------------
def action_protects(hazard: Hazard, helper_action: HelperAction) -> bool:
    return hazard.id in helper_action.protects_from and helper_action.id == hazard.needs_action


def risky_interception(power: Power) -> bool:
    return power.jolt > 0


def valid_combo(hazard: Hazard, helper_action: HelperAction, power: Power) -> bool:
    return hazard.threatens_bud and action_protects(hazard, helper_action) and risky_interception(power)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hazard_id, hazard in HAZARDS.items():
        for action_id, action in HELPER_ACTIONS.items():
            for power_id, power in POWERS.items():
                if valid_combo(hazard, action, power):
                    combos.append((hazard_id, action_id, power_id))
    return sorted(combos)


def predict_trouble(world: World, power: Power) -> dict:
    sim = world.copy()
    bud = sim.get("bud")
    bud.meters["wobble"] += float(power.jolt)
    if power.jolt >= 2:
        bud.meters["spill"] += 1
        bud.meters["unsafe"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": bud.meters["spill"] >= THRESHOLD,
        "bloom_risk": bud.meters["bloom_risk"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, mentor: Entity, bud: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} wore a bright cape and tried very hard to stand like a real hero. "
        f"{helper.id} was there too, and so was Coach Ray, who said every good team needed quick feet and kind hearts."
    )
    world.say(
        f"At the center of the practice space stood a silver planter with a tiny moon-lily bud inside. "
        f"It sat near {world.setting.curve_phrase}, where everyone could see it."
    )
    world.say(
        f'"At the start bell," Coach Ray said, "we race, rescue, and protect whatever is fragile."'
    )


def setup_pride(world: World, hero: Entity, helper: Entity, hazard: Hazard) -> None:
    hero.memes["pride"] += 1
    hero.memes["jealousy"] += 1
    world.say(
        f"{hero.id} wanted to be the first one to help today. {helper.id} had already earned two shiny star stickers this week, "
        f"and that made {hero.id} want to shine even more."
    )
    world.think(
        hero,
        f'"If trouble comes, I will be the fastest," {hero.id} thought.'
    )
    world.say(
        f"Then a new problem showed itself: {hazard.sign}"
    )


def danger_begins(world: World, hazard: Hazard, bud: Entity) -> None:
    bud.meters["unsafe"] += 1
    world.facts["hazard_seen"] = True
    propagate(world, narrate=False)
    world.say(
        f"The little bud looked too delicate for that. {hazard.risk_line}"
    )


def helper_moves(world: World, hero: Entity, helper: Entity, helper_action: HelperAction) -> None:
    helper.memes["calm"] += 1
    world.facts["helper_started"] = True
    world.say(
        f"Before {hero.id} could speak, {helper.id} hurried forward, {helper_action.visible_cue}, and {helper_action.verb} the planter."
    )
    world.think(
        hero,
        f'"Wait. Why is {helper.id} doing that?" {hero.id} thought.'
    )
    hero.memes["suspicion"] += 1


def misunderstanding(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["misunderstanding"] += 1
    world.say(
        f"From where {hero.id} stood, it looked as if {helper.id} was grabbing the moon-lily for a solo rescue."
    )
    world.think(
        hero,
        f'"{helper.id} is taking over. {helper.pronoun().capitalize()} thinks I am too slow," {hero.id} thought.'
    )


def intercept(world: World, hero: Entity, helper: Entity, power: Power, bud: Entity) -> None:
    hero.memes["impulse"] += 1
    world.facts["intercepted"] = True
    world.say(
        f"So {hero.id} did not ask a question. {hero.pronoun().capitalize()} leaped in and used {power.label}: {power.impulse_text}."
    )
    bud.meters["wobble"] += float(power.jolt)
    if power.jolt >= 2:
        bud.meters["spill"] += 1
        bud.meters["soil_loose"] += 1
        bud.meters["unsafe"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The planter jerked sideways around the curve of the path. Dark dirt hopped over the rim, and the little bud bent with a frightened bob."
    )


def reveal(world: World, mentor: Entity, helper: Entity, hazard: Hazard, helper_action: HelperAction) -> None:
    world.say(f'"Stop, team!" Coach Ray called.')
    world.say(
        f'{helper.id} blinked in surprise. "I was not trying to steal the rescue," {helper.pronoun()} said. '
        f'"I was {helper_action.explanation}"'
    )
    world.say(
        f'Coach Ray nodded. "That was the right idea. {hazard.threat} was the danger, and moving the planter toward {helper_action.destination} would have kept the bud safe."'
    )


def remorse(world: World, hero: Entity) -> None:
    hero.memes["guilt"] += 1
    hero.memes["trust"] -= 1
    world.think(
        hero,
        f'"Oh no. I did not even ask. I just guessed and charged in," {hero.id} thought.'
    )
    world.say(
        f"{hero.id}'s face grew warm under the mask. Being fast did not feel heroic anymore."
    )


def apologize(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["humility"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'"I am sorry," {hero.id} said. "I thought you were showing off, and I was wrong."'
    )
    world.say(
        f'{helper.id} steadied the pot with both hands. "Next time, just ask me," {helper.pronoun()} said. "Heroes can talk and run."'
    )


def repair(world: World, hero: Entity, helper: Entity, power: Power, helper_action: HelperAction, bud: Entity) -> None:
    world.say(
        f"Then the two young heroes worked together. {helper.id} held the planter steady while {hero.id} used {power.label} again, but gently this time: {power.repair_text}."
    )
    world.say(
        f"Together they {helper_action.verb} it to {helper_action.destination} and tucked the spilled dirt back around the roots."
    )
    bud.meters["safe"] += 1
    bud.meters["unsafe"] = 0.0
    bud.meters["spill"] = 0.0
    propagate(world, narrate=False)


def resolution(world: World, hero: Entity, helper: Entity, mentor: Entity, bud: Entity) -> None:
    hero.memes["trust"] += 2
    helper.memes["trust"] += 1
    hero.memes["misunderstanding"] = 0.0
    world.say(
        f"After a moment, the bud stood upright again. A tiny silver drop trembled on one green leaf, but the stem was still strong."
    )
    world.say(
        f'Coach Ray smiled. "A real hero does not only make a fast start," {mentor.pronoun()} said. "A real hero checks the truth before acting."'
    )
    world.think(
        hero,
        f'"Next time I will look, listen, and then move," {hero.id} thought.'
    )
    world.say(
        f"When practice ended, {hero.id} and {helper.id} placed a little shield sign beside the planter. "
        f"The moon-lily bud rested safely behind it, and both young heroes felt stronger than before."
    )


def tell(
    setting: Setting,
    hazard: Hazard,
    helper_action: HelperAction,
    power: Power,
    hero_name: str = "Nova",
    hero_type: str = "girl",
    helper_name: str = "Bolt",
    helper_type: str = "boy",
    mentor_type: str = "father",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    mentor = world.add(Entity(id="Coach Ray", kind="character", type=mentor_type, role="mentor", label="the coach"))
    bud = world.add(Entity(id="bud", kind="thing", type="plant", label="moon-lily bud", fragile=True, movable=True))
    planter = world.add(Entity(id="planter", kind="thing", type="pot", label="silver planter", movable=True))

    world.facts.update(
        setting=setting,
        hazard=hazard,
        helper_action=helper_action,
        power=power,
        hero=hero,
        helper=helper,
        mentor=mentor,
        bud=bud,
        hazard_seen=False,
        helper_started=False,
        intercepted=False,
    )

    introduce(world, hero, helper, mentor, bud)
    world.para()
    setup_pride(world, hero, helper, hazard)
    danger_begins(world, hazard, bud)
    helper_moves(world, hero, helper, helper_action)
    misunderstanding(world, hero, helper)

    world.para()
    intercept(world, hero, helper, power, bud)
    reveal(world, mentor, helper, hazard, helper_action)
    remorse(world, hero)
    apologize(world, hero, helper)

    world.para()
    repair(world, hero, helper, power, helper_action, bud)
    resolution(world, hero, helper, mentor, bud)

    world.facts.update(
        spill_happened=bud.meters["soil_loose"] >= THRESHOLD or "soil_loose" in bud.meters,
        saved=bud.meters["safe"] >= THRESHOLD,
        misunderstood=hero.memes["misunderstanding"] < THRESHOLD and hero.memes["humility"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "roof": Setting(
        id="roof",
        place="the roof garden of Starbright School",
        curve_phrase="a painted curve on the training track",
        shelter="the glass door to the indoor hall",
        crowd="students in capes",
        tags={"school", "garden"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the library courtyard of Hero Hill",
        curve_phrase="a stone curve around the fountain",
        shelter="the arched reading room",
        crowd="quiet readers and junior heroes",
        tags={"library", "garden"},
    ),
    "plaza": Setting(
        id="plaza",
        place="the museum hero plaza",
        curve_phrase="a glowing curve in the practice lane",
        shelter="the marble entry hall",
        crowd="families and tour guides",
        tags={"museum", "garden"},
    ),
}

HAZARDS = {
    "gust": Hazard(
        id="gust",
        label="a hard gust",
        threat="the wind could snap the stem or dump the pot",
        threatens_bud=True,
        needs_action="move_inside",
        sign="a hard gust whistled across the roof and made the planter tremble",
        risk_line="One more push from the wind might tip the whole planter over.",
        tags={"wind", "plant"},
    ),
    "sprinkler": Hazard(
        id="sprinkler",
        label="a wild sprinkler burst",
        threat="the water could hammer the tiny bud flat and wash the soil loose",
        threatens_bud=True,
        needs_action="cover_bud",
        sign="a broken sprinkler gave a sudden start and sprayed a sharp spinning fan of water",
        risk_line="The spray was too strong for a new bud that small.",
        tags={"water", "plant"},
    ),
    "bees": Hazard(
        id="bees",
        label="a buzzing bee swirl",
        threat="the bees could crowd the opening flower and make people flail near it",
        threatens_bud=True,
        needs_action="carry_away",
        sign="a buzzing swirl of bees drifted low beside the planter",
        risk_line="The bud itself was gentle, but startled hands could crush it in a second.",
        tags={"bees", "plant"},
    ),
    "shade": Hazard(
        id="shade",
        label="a passing cloud",
        threat="the light would be dim for a minute",
        threatens_bud=False,
        needs_action="wait",
        sign="a soft cloud crossed the sun",
        risk_line="It looked gloomy, but the bud was not in real danger.",
        tags={"weather"},
    ),
}

HELPER_ACTIONS = {
    "move_inside": HelperAction(
        id="move_inside",
        label="move it inside",
        verb="rolled",
        destination="the glass door and into the hall",
        protects_from={"gust"},
        visible_cue="leaning low and gripping the rim like a racer",
        explanation="trying to move it inside before the gust could knock it over.",
        tags={"shelter"},
    ),
    "cover_bud": HelperAction(
        id="cover_bud",
        label="cover it with a shield dome",
        verb="slid",
        destination="the dry side of the planter stand",
        protects_from={"sprinkler"},
        visible_cue="throwing a clear shield dome over one arm",
        explanation="trying to cover the bud before the broken sprinkler hit it.",
        tags={"shield"},
    ),
    "carry_away": HelperAction(
        id="carry_away",
        label="carry it away from the bees",
        verb="carried",
        destination="a quieter bench near the wall",
        protects_from={"bees"},
        visible_cue="hugging the planter close under a flapping cape",
        explanation="carrying it away so nobody would swat at bees right beside the stem.",
        tags={"move"},
    ),
    "wait": HelperAction(
        id="wait",
        label="stand nearby",
        verb="watched",
        destination="the same place",
        protects_from={"shade"},
        visible_cue="standing still with hands on hips",
        explanation="waiting because nothing dangerous was happening.",
        tags={"wait"},
    ),
}

POWERS = {
    "wind_loop": Power(
        id="wind_loop",
        label="Wind Loop",
        impulse_text="a bright ring of air meant to stop the planter in place",
        jolt=2,
        fixes={"gust", "bees"},
        repair_text="a soft ribbon of air that slowed every shake without bumping the pot",
        tags={"wind"},
    ),
    "magnet_pull": Power(
        id="magnet_pull",
        label="Magnet Pull",
        impulse_text="a silver tug meant to yank the planter back",
        jolt=2,
        fixes={"bees"},
        repair_text="a tiny careful pull that lined the metal stand up straight",
        tags={"magnet"},
    ),
    "light_shield": Power(
        id="light_shield",
        label="Light Shield",
        impulse_text="a quick flashing wall meant to block the way",
        jolt=1,
        fixes={"sprinkler", "gust"},
        repair_text="a wide, quiet shield that held back the spray while the soil was patted down",
        tags={"shield"},
    ),
    "shadow_stop": Power(
        id="shadow_stop",
        label="Shadow Stop",
        impulse_text="a dark blanket of shadow meant to freeze the scene",
        jolt=0,
        fixes={"shade"},
        repair_text="a calm patch of shade that let everyone think",
        tags={"shadow"},
    ),
}

GIRL_NAMES = ["Nova", "Skye", "Luna", "Mira", "Ruby", "Kira"]
BOY_NAMES = ["Bolt", "Dash", "Jett", "Finn", "Rio", "Max"]
PARENTS = ["mother", "father"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hazard: str
    helper_action: str
    power: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    mentor_type: str
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
    "wind": [
        (
            "Why can a strong gust be dangerous for a potted plant?",
            "A strong gust can push the pot, spill the dirt, or bend a thin stem too far. Small plants need steady support because they are still delicate."
        )
    ],
    "water": [
        (
            "Why can a broken sprinkler hurt a tiny plant bud?",
            "A tiny bud can handle gentle water, but a hard spray can smack it flat and wash soil away from the roots. Too much force is the problem."
        )
    ],
    "bees": [
        (
            "Are bees always bad for flowers?",
            "No. Bees help many flowers, but people can panic when bees buzz close. In a busy place, sudden swatting hands can be the bigger danger."
        )
    ],
    "shield": [
        (
            "What does a shield do in a superhero story?",
            "A shield protects something from being hit. A good shield makes danger smaller without knocking things around."
        )
    ],
    "plant": [
        (
            "What is a bud on a plant?",
            "A bud is a small, closed beginning of a flower or leaf. It is the start of new growth, so it can be delicate."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what another person means, but they are wrong. Asking a question can clear it up."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork important for heroes?",
            "Heroes do better when they share information and help each other. Being brave matters, but listening matters too."
        )
    ],
}
KNOWLEDGE_ORDER = ["plant", "wind", "water", "bees", "shield", "misunderstanding", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    hazard = f["hazard"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "curve", "start", and "bud".',
        f"Tell a superhero story where {hero.id} misunderstands why {helper.id} rushes toward a tiny bud, and the mistake is fixed with an apology and teamwork.",
        f"Write a gentle action story with inner monologue, where a hero sees {hazard.label}, jumps to the wrong conclusion, and learns to ask before acting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mentor = f["mentor"]
    hazard = f["hazard"]
    helper_action = f["helper_action"]
    power = f["power"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young hero in training, and {helper.id}, the teammate {hero.pronoun()} misunderstood. Coach Ray helped them slow down and understand what was really happening."
        ),
        (
            "What problem did the heroes see at the start?",
            f"They saw {hazard.label} threatening a tiny moon-lily bud. The bud was fragile, so even a small mistake could have hurt it."
        ),
        (
            f"Why did {hero.id} think {helper.id} was doing the wrong thing?",
            f"{hero.id} saw {helper.id} rush forward without hearing the reason first, so it looked like {helper.pronoun()} was trying to grab the rescue alone. That misunderstanding grew because {hero.id} felt proud and wanted to be first."
        ),
        (
            f"What did {hero.id} do when {hero.pronoun()} misunderstood the scene?",
            f"{hero.id} used {power.label} to cut in front of {helper.id}. The move was fast, but it jolted the planter and made the bud wobble."
        ),
        (
            f"What was {helper.id} really trying to do?",
            f"{helper.id} was trying to {helper_action.label}. That plan matched the danger because {hazard.threat}."
        ),
        (
            f"How was the problem solved?",
            f"{hero.id} apologized, and then the two children worked together to protect the planter. The bud became safe because {helper.id} steadied it while {hero.id} used {power.label} more carefully."
        ),
        (
            "What did the hero learn?",
            f"{hero.id} learned that being quick is not enough by itself. A real hero can make a fast start, but still needs to ask, listen, and understand the truth."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"plant", "misunderstanding", "teamwork"} | set(world.facts["hazard"].tags)
    if "shield" in world.facts["power"].tags or "shield" in world.facts["helper_action"].tags:
        tags.add("shield")
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


# ---------------------------------------------------------------------------
# Trace
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    if world.history:
        lines.append("  history:")
        for item in world.history:
            lines.append(f"    - {item}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hazard_real(H) :- hazard(H), threatens_bud(H).
action_protects(H,A) :- helper_action(A), hazard(H), needs_action(H,A), protects(A,H).
risky_power(P) :- power(P), jolt(P,J), J > 0.
valid(H,A,P) :- hazard_real(H), action_protects(H,A), risky_power(P).

spill(P) :- chosen_power(P), jolt(P,J), J >= 2.
outcome(repaired) :- chosen_hazard(H), chosen_action(A), chosen_power(P), valid(H,A,P).
misread :- chosen_hazard(H), chosen_action(A), chosen_power(P), valid(H,A,P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.threatens_bud:
            lines.append(asp.fact("threatens_bud", hid))
        lines.append(asp.fact("needs_action", hid, h.needs_action))
    for aid, a in HELPER_ACTIONS.items():
        lines.append(asp.fact("helper_action", aid))
        for h in sorted(a.protects_from):
            lines.append(asp.fact("protects", aid, h))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        lines.append(asp.fact("jolt", pid, p.jolt))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    seeds_checked = 0
    parser = build_parser()
    for s in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            seeds_checked += 1
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {s}: {err}")
            break
    if rc == 0:
        print(f"OK: random generation smoke-tested on {seeds_checked} seeds.")
    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="roof",
        hazard="gust",
        helper_action="move_inside",
        power="wind_loop",
        hero_name="Nova",
        hero_type="girl",
        helper_name="Bolt",
        helper_type="boy",
        mentor_type="father",
        seed=1,
    ),
    StoryParams(
        setting="courtyard",
        hazard="sprinkler",
        helper_action="cover_bud",
        power="light_shield",
        hero_name="Skye",
        hero_type="girl",
        helper_name="Finn",
        helper_type="boy",
        mentor_type="mother",
        seed=2,
    ),
    StoryParams(
        setting="plaza",
        hazard="bees",
        helper_action="carry_away",
        power="magnet_pull",
        hero_name="Mira",
        hero_type="girl",
        helper_name="Dash",
        helper_type="boy",
        mentor_type="father",
        seed=3,
    ),
]


# ---------------------------------------------------------------------------
# Explanations
# ---------------------------------------------------------------------------
def explain_rejection(hazard: Hazard, helper_action: HelperAction, power: Power) -> str:
    if not hazard.threatens_bud:
        return (
            f"(No story: {hazard.label} does not put the bud in real danger, so there is no honest superhero rescue to misunderstand.)"
        )
    if not action_protects(hazard, helper_action):
        return (
            f"(No story: {helper_action.label} does not actually protect the bud from {hazard.label}. The helper's move must make sense before the misunderstanding can matter.)"
        )
    if not risky_interception(power):
        return (
            f"(No story: {power.label} is too gentle to jolt the planter, so the impulsive mistake would not create a meaningful turn.)"
        )
    return "(No story: this combination is not valid.)"


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero misunderstanding around a fragile bud."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--helper_action", choices=HELPER_ACTIONS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--hero_name")
    ap.add_argument("--helper_name")
    ap.add_argument("--hero_type", choices=["girl", "boy"])
    ap.add_argument("--helper_type", choices=["girl", "boy"])
    ap.add_argument("--mentor_type", choices=PARENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.helper_action and args.power:
        hazard = HAZARDS[args.hazard]
        action = HELPER_ACTIONS[args.helper_action]
        power = POWERS[args.power]
        if not valid_combo(hazard, action, power):
            raise StoryError(explain_rejection(hazard, action, power))

    combos = [
        combo for combo in valid_combos()
        if (args.hazard is None or combo[0] == args.hazard)
        and (args.helper_action is None or combo[1] == args.helper_action)
        and (args.power is None or combo[2] == args.power)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hazard_id, action_id, power_id = rng.choice(combos)
    setting_id = args.setting or rng.choice(sorted(SETTINGS.keys()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    helper_name = args.helper_name or _pick_name(rng, helper_type, avoid=hero_name)
    mentor_type = args.mentor_type or rng.choice(PARENTS)

    return StoryParams(
        setting=setting_id,
        hazard=hazard_id,
        helper_action=action_id,
        power=power_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        mentor_type=mentor_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.helper_action not in HELPER_ACTIONS:
        raise StoryError(f"(Unknown helper action: {params.helper_action})")
    if params.power not in POWERS:
        raise StoryError(f"(Unknown power: {params.power})")

    hazard = HAZARDS[params.hazard]
    action = HELPER_ACTIONS[params.helper_action]
    power = POWERS[params.power]
    if not valid_combo(hazard, action, power):
        raise StoryError(explain_rejection(hazard, action, power))

    world = tell(
        setting=SETTINGS[params.setting],
        hazard=hazard,
        helper_action=action,
        power=power,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        mentor_type=params.mentor_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1.\n#show spill/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hazard, helper_action, power) combos:\n")
        for hazard, action, power in combos:
            print(f"  {hazard:10} {action:12} {power}")
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
            header = f"### {p.hero_name}: {p.hazard} / {p.helper_action} / {p.power}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
