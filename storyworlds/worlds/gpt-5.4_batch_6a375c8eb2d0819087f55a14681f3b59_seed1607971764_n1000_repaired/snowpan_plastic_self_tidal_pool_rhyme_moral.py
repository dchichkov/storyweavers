#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/snowpan_plastic_self_tidal_pool_rhyme_moral.py
===========================================================================

A standalone story world for a rhyming tidal-pool tale about a child, a piece of
plastic, and the choice between keeping something for the self or helping a
small sea creature first.

The world model rebuilds a simple moral arc:

- a child explores a tidal pool and treasures a white shell nicknamed a
  "snowpan"
- a bright plastic object glitters in a little sea channel
- at first the child wants the shiny thing for the self
- the blocked water puts a tiny creature at risk
- the child, helped by a calm grown-up, removes the plastic and uses the
  snowpan shell to help cool or guide the creature
- the ending proves what changed: the child leaves with a cleaner shore and a
  kinder heart

The prose is written in a child-facing, lightly rhyming style.

Run it
------
    python storyworlds/worlds/gpt-5.4/snowpan_plastic_self_tidal_pool_rhyme_moral.py
    python storyworlds/worlds/gpt-5.4/snowpan_plastic_self_tidal_pool_rhyme_moral.py --creature goby --plastic bottle_cap
    python storyworlds/worlds/gpt-5.4/snowpan_plastic_self_tidal_pool_rhyme_moral.py --tool flip_flop
    python storyworlds/worlds/gpt-5.4/snowpan_plastic_self_tidal_pool_rhyme_moral.py --all
    python storyworlds/worlds/gpt-5.4/snowpan_plastic_self_tidal_pool_rhyme_moral.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/snowpan_plastic_self_tidal_pool_rhyme_moral.py --verify
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
    kind: str = "thing"            # "character" | "creature" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class PoolSpot:
    id: str
    label: str
    phrase: str
    channel_shape: str
    width: str                   # narrow | broad
    sparkle: str
    habitats: set[str] = field(default_factory=set)
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
class PlasticItem:
    id: str
    label: str
    phrase: str
    color: str
    fits: set[str] = field(default_factory=set)   # channel widths it can block
    drift_text: str = ""
    want_text: str = ""
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
class CreatureCfg:
    id: str
    label: str
    phrase: str
    move_text: str
    fragility: int
    habitats: set[str] = field(default_factory=set)
    plural: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    action_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


def _r_blocked_pool(world: World) -> list[str]:
    out: list[str] = []
    spot = world.get("spot")
    creature = world.get("creature")
    child = world.get("child")
    if spot.meters["blocked"] < THRESHOLD:
        return out
    sig = ("blocked_pool",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.meters["risk"] += float(world.facts["creature_cfg"].fragility)
    creature.meters["warm"] += 1.0
    child.memes["concern"] += 1.0
    out.append("__risk__")
    return out


def _r_struggle_seen(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    child = world.get("child")
    if creature.meters["risk"] < THRESHOLD:
        return out
    sig = ("struggle_seen",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["empathy"] += 2.0
    child.memes["self_pull"] = max(0.0, child.memes["self_pull"] - 1.0)
    out.append("__struggle__")
    return out


def _r_water_returns(world: World) -> list[str]:
    out: list[str] = []
    spot = world.get("spot")
    creature = world.get("creature")
    child = world.get("child")
    if spot.meters["blocked"] >= THRESHOLD:
        return out
    if spot.meters["opened"] < THRESHOLD:
        return out
    sig = ("water_returns",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spot.meters["water_flow"] += 1.0
    creature.meters["relief"] += 1.0
    child.memes["hope"] += 1.0
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked_pool", tag="physical", apply=_r_blocked_pool),
    Rule(name="struggle_seen", tag="emotional", apply=_r_struggle_seen),
    Rule(name="water_returns", tag="physical", apply=_r_water_returns),
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


# ---------------------------------------------------------------------------
# Constraints and outcome logic
# ---------------------------------------------------------------------------
def hazard_at_risk(spot: PoolSpot, plastic: PlasticItem, creature: CreatureCfg) -> bool:
    return (
        spot.width in plastic.fits
        and creature.id in spot.habitats
        and spot.id in creature.habitats
    )


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def severity_of(creature: CreatureCfg, delay: int) -> int:
    return creature.fragility + delay


def outcome_of(params: "StoryParams") -> str:
    creature = CREATURES[params.creature]
    sev = severity_of(creature, params.delay)
    return "urgent_help" if sev >= 4 else "steady_help"


def remove_works(tool: Tool) -> bool:
    return tool.power >= 1


def explain_rejection(spot: PoolSpot, plastic: PlasticItem, creature: CreatureCfg) -> str:
    if spot.width not in plastic.fits:
        return (
            f"(No story: {plastic.phrase} would not truly jam {spot.phrase}. "
            f"The blockage has to be plausible so the rescue can be honest.)"
        )
    if creature.id not in spot.habitats or spot.id not in creature.habitats:
        return (
            f"(No story: {creature.phrase} does not belong in {spot.phrase}. "
            f"Pick a creature that could really be there.)"
        )
    return "(No story: this combination does not make a reasonable tidal-pool hazard.)"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = " / ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense "
        f"(sense={tool.sense} < {SENSE_MIN}). Try: {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_trouble(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    creature = sim.get("creature")
    return {
        "risk": creature.meters["risk"],
        "warm": creature.meters["warm"],
    }


# ---------------------------------------------------------------------------
# Rhyming helpers
# ---------------------------------------------------------------------------
def rhyme_close(a: str, b: str) -> str:
    return f"{a}; {b}."


def child_trait_line(trait: str) -> str:
    return {
        "gentle": "gentle and bright",
        "curious": "curious and bright",
        "careful": "careful and bright",
        "cheerful": "cheerful and bright",
        "thoughtful": "thoughtful and bright",
        "eager": "eager and bright",
    }.get(trait, "little and bright")


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, adult: Entity, spot_cfg: PoolSpot) -> None:
    world.say(
        rhyme_close(
            f"{child.id} walked by the tidal pool with {child_trait_line(world.facts['trait'])}",
            f"and {adult.label_word} came too, with a smile in the blue"
        )
    )
    world.say(
        rhyme_close(
            f"There in {spot_cfg.phrase}, where the sea made a jewel",
            f"each pebble winked softly inside the cool pool"
        )
    )


def find_snowpan(world: World, child: Entity) -> None:
    shell = world.get("snowpan")
    child.memes["wonder"] += 1.0
    world.say(
        rhyme_close(
            f"{child.id} found a white shell, smooth, shallow, and grand",
            f'"I\'ll call this my snowpan," {child.pronoun()} sang in the sand'
        )
    )
    shell.meters["held"] += 1.0


def spot_plastic(world: World, child: Entity, plastic_cfg: PlasticItem, spot_cfg: PoolSpot) -> None:
    child.memes["self_pull"] += 2.0
    world.say(
        rhyme_close(
            f"Then {plastic_cfg.phrase} flashed {plastic_cfg.color} by {spot_cfg.channel_shape}",
            plastic_cfg.drift_text
        )
    )
    world.say(
        rhyme_close(
            f"{child.id} thought, {plastic_cfg.want_text}",
            f"for the shiny little thing seemed a fine prize for the self to keep"
        )
    )


def warn(world: World, adult: Entity, child: Entity, plastic_cfg: PlasticItem, creature_cfg: CreatureCfg) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_warm"] = pred["warm"]
    world.say(
        rhyme_close(
            f'"Wait," said {adult.label_word}, "that plastic may stop the sea\'s song',
            f'and leave {creature_cfg.phrase} warm where cool water belongs"'
        )
    )


def hesitate(world: World, child: Entity) -> None:
    child.memes["hesitation"] += 1.0
    world.say(
        rhyme_close(
            f"{child.id} curled little fingers and paused for a beat",
            "for keeping bright treasure can feel like a treat"
        )
    )


def show_struggle(world: World, creature_cfg: CreatureCfg) -> None:
    propagate(world, narrate=False)
    creature = world.get("creature")
    creature.meters["seen"] += 1.0
    world.say(
        rhyme_close(
            creature_cfg.move_text,
            "and the small pool looked smaller beneath the hot sky"
        )
    )


def choose_help(world: World, child: Entity) -> None:
    child.memes["kindness"] += 1.0
    child.memes["self_pull"] = 0.0
    world.say(
        rhyme_close(
            f'"Not just for my self," whispered {child.id} at last',
            "for helping first matters more than holding things fast"
        )
    )


def lift_plastic(world: World, adult: Entity, child: Entity, tool_cfg: Tool, plastic_cfg: PlasticItem) -> None:
    spot = world.get("spot")
    plastic = world.get("plastic")
    if not remove_works(tool_cfg):
        raise StoryError(f"(No story: {tool_cfg.label} cannot remove the plastic safely.)")
    plastic.meters["removed"] += 1.0
    spot.meters["blocked"] = 0.0
    spot.meters["opened"] += 1.0
    child.memes["bravery"] += 1.0
    propagate(world, narrate=False)
    world.say(
        rhyme_close(
            f"{adult.label_word.capitalize()} and {child.id} used {tool_cfg.phrase}",
            tool_cfg.action_text.replace("{plastic}", plastic_cfg.label)
        )
    )


def steady_rescue(world: World, child: Entity, creature_cfg: CreatureCfg) -> None:
    creature = world.get("creature")
    creature.meters["safe"] += 1.0
    creature.meters["risk"] = 0.0
    creature.meters["warm"] = 0.0
    child.memes["relief"] += 1.0
    world.say(
        rhyme_close(
            "Soon a thin silver trickle came skipping once more",
            f"and {creature_cfg.phrase} rested in cool water by shore"
        )
    )


def urgent_rescue(world: World, child: Entity, creature_cfg: CreatureCfg) -> None:
    creature = world.get("creature")
    shell = world.get("snowpan")
    creature.meters["safe"] += 1.0
    creature.meters["guided"] += 1.0
    creature.meters["risk"] = 0.0
    creature.meters["warm"] = 0.0
    shell.meters["used_to_help"] += 1.0
    child.memes["relief"] += 1.0
    child.memes["pride"] += 1.0
    world.say(
        rhyme_close(
            f"The water returned, but {creature_cfg.phrase} was still warm from the sun",
            "so the help was not finished when the opening was done"
        )
    )
    world.say(
        rhyme_close(
            f"{child.id} dipped the snowpan shell, cool as moonlight at sea",
            f"and poured gentle water to guide {creature_cfg.label} free"
        )
    )
    world.say(
        rhyme_close(
            f"Wave by wave, with the snowpan, {child.pronoun()} helped with care",
            "until the small swimmer reached deeper blue there"
        )
    )


def moral_end(world: World, child: Entity, adult: Entity, plastic_cfg: PlasticItem, spot_cfg: PoolSpot) -> None:
    child.memes["lesson"] += 1.0
    child.meters["cleanup"] += 1.0
    world.say(
        rhyme_close(
            f"{child.id} did not tuck {plastic_cfg.label} away as a toy",
            f"{child.pronoun().capitalize()} carried it out, and the clean shore brought joy"
        )
    )
    world.say(
        rhyme_close(
            f'"A kind heart grows wide," said {adult.label_word}, "like the pull of the tide"',
            "and what we do for others leaves bright ripples inside"
        )
    )
    world.say(
        rhyme_close(
            f"Back by {spot_cfg.phrase}, the pool gave a glimmering gleam",
            "and the snowpan shell shone like the start of a dream"
        )
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    spot_cfg: PoolSpot,
    plastic_cfg: PlasticItem,
    creature_cfg: CreatureCfg,
    tool_cfg: Tool,
    child_name: str = "Mina",
    child_gender: str = "girl",
    adult_type: str = "mother",
    trait: str = "thoughtful",
    delay: int = 1,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            attrs={},
            tags={"child"},
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the adult",
            attrs={},
            tags={"adult"},
        )
    )
    world.add(
        Entity(
            id="spot",
            kind="thing",
            type="pool",
            label=spot_cfg.label,
            attrs={"width": spot_cfg.width},
            tags=set(spot_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="plastic",
            kind="thing",
            type="plastic",
            label=plastic_cfg.label,
            attrs={},
            tags=set(plastic_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="creature",
            kind="creature",
            type="creature",
            label=creature_cfg.label,
            attrs={},
            tags=set(creature_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="snowpan",
            kind="thing",
            type="shell",
            label="snowpan shell",
            attrs={},
            tags={"shell", "snowpan"},
        )
    )

    world.facts.update(
        spot_cfg=spot_cfg,
        plastic_cfg=plastic_cfg,
        creature_cfg=creature_cfg,
        tool_cfg=tool_cfg,
        child=child,
        adult=adult,
        trait=trait,
        delay=delay,
        outcome="",
    )

    spot = world.get("spot")
    creature = world.get("creature")
    plastic = world.get("plastic")
    spot.meters["blocked"] = 1.0
    spot.meters["opened"] = 0.0
    spot.meters["water_flow"] = 0.0
    creature.meters["risk"] = 0.0
    creature.meters["warm"] = 0.0
    creature.meters["safe"] = 0.0
    creature.meters["guided"] = 0.0
    plastic.meters["removed"] = 0.0
    child.memes["self_pull"] = 0.0
    child.memes["empathy"] = 0.0
    child.memes["concern"] = 0.0
    child.memes["kindness"] = 0.0
    child.memes["hesitation"] = 0.0
    child.memes["relief"] = 0.0

    introduce(world, child, adult, spot_cfg)
    find_snowpan(world, child)
    world.para()
    spot_plastic(world, child, plastic_cfg, spot_cfg)
    warn(world, adult, child, plastic_cfg, creature_cfg)

    if delay > 0:
        hesitate(world, child)

    show_struggle(world, creature_cfg)
    choose_help(world, child)

    world.para()
    lift_plastic(world, adult, child, tool_cfg, plastic_cfg)

    outcome = "urgent_help" if severity_of(creature_cfg, delay) >= 4 else "steady_help"
    world.facts["outcome"] = outcome
    if outcome == "urgent_help":
        urgent_rescue(world, child, creature_cfg)
    else:
        steady_rescue(world, child, creature_cfg)

    world.para()
    moral_end(world, child, adult, plastic_cfg, spot_cfg)
    world.facts.update(
        rescued=True,
        creature_safe=creature.meters["safe"] >= THRESHOLD,
        plastic_removed=plastic.meters["removed"] >= THRESHOLD,
        guided=creature.meters["guided"] >= THRESHOLD,
        snowpan_helped=world.get("snowpan").meters["used_to_help"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SPOTS = {
    "runnel": PoolSpot(
        id="runnel",
        label="runnel",
        phrase="a ribbon-thin runnel",
        channel_shape="the narrow runnel",
        width="narrow",
        sparkle="sun-silver",
        habitats={"hermit_crab", "goby"},
        tags={"tide_pool", "channel"},
    ),
    "rock_cup": PoolSpot(
        id="rock_cup",
        label="rock cup",
        phrase="a round rock cup",
        channel_shape="the rock lip",
        width="broad",
        sparkle="green-gold",
        habitats={"sea_snail", "goby"},
        tags={"tide_pool", "rock"},
    ),
    "seaweed_gap": PoolSpot(
        id="seaweed_gap",
        label="seaweed gap",
        phrase="a seaweed-framed gap",
        channel_shape="the green seaweed gap",
        width="narrow",
        sparkle="emerald",
        habitats={"sea_snail", "hermit_crab"},
        tags={"tide_pool", "seaweed"},
    ),
}

PLASTICS = {
    "bottle_cap": PlasticItem(
        id="bottle_cap",
        label="bottle cap",
        phrase="a little plastic bottle cap",
        color="blue",
        fits={"narrow"},
        drift_text="it had wedged in the crack where the wavelets should sweep",
        want_text='"It would fit in my snowpan and look nice and neat,"',
        tags={"plastic", "litter", "bottle_cap"},
    ),
    "wrapper": PlasticItem(
        id="wrapper",
        label="wrapper",
        phrase="a crinkly plastic wrapper",
        color="silver",
        fits={"narrow", "broad"},
        drift_text="it lay across the gap like a sail gone to sleep",
        want_text='"It shines like a fish-scale; I could keep it with my shell,"',
        tags={"plastic", "litter", "wrapper"},
    ),
    "spoon": PlasticItem(
        id="spoon",
        label="spoon",
        phrase="a snapped plastic spoon",
        color="white",
        fits={"broad"},
        drift_text="it had caught on the stones where the foam used to creep",
        want_text='"Its handle looks handy; it might make my game swell,"',
        tags={"plastic", "litter", "spoon"},
    ),
}

CREATURES = {
    "hermit_crab": CreatureCfg(
        id="hermit_crab",
        label="the hermit crab",
        phrase="a tiny hermit crab",
        move_text="A tiny hermit crab tapped at a pebble and turned with a sigh",
        fragility=1,
        habitats={"runnel", "seaweed_gap"},
        tags={"crab", "tidal_pool_creature"},
    ),
    "sea_snail": CreatureCfg(
        id="sea_snail",
        label="the sea snail",
        phrase="a small sea snail",
        move_text="A small sea snail clung low and slow as the damp ring ran dry",
        fragility=2,
        habitats={"rock_cup", "seaweed_gap"},
        tags={"snail", "tidal_pool_creature"},
    ),
    "goby": CreatureCfg(
        id="goby",
        label="the goby",
        phrase="a tiny goby",
        move_text="A tiny goby gave one quick flick and one worried small fly",
        fragility=3,
        habitats={"runnel", "rock_cup"},
        tags={"fish", "tidal_pool_creature"},
    ),
}

TOOLS = {
    "drift_stick": Tool(
        id="drift_stick",
        label="drift stick",
        phrase="a smooth drift stick",
        sense=3,
        power=2,
        action_text="till the {plastic} tipped loose and the channel ran free",
        qa_text="used a smooth drift stick to pry the plastic loose",
        tags={"cleanup_tool", "stick"},
    ),
    "beach_gloves": Tool(
        id="beach_gloves",
        label="beach gloves",
        phrase="beach gloves",
        sense=3,
        power=2,
        action_text="and lifted the {plastic} away from the little sea lane",
        qa_text="put on beach gloves and lifted the plastic away",
        tags={"cleanup_tool", "gloves"},
    ),
    "shell_tongs": Tool(
        id="shell_tongs",
        label="shell tongs",
        phrase="little shell tongs",
        sense=2,
        power=1,
        action_text="until the {plastic} came free without a scrape or a strain",
        qa_text="used little shell tongs to pull the plastic free",
        tags={"cleanup_tool", "tongs"},
    ),
    "flip_flop": Tool(
        id="flip_flop",
        label="flip-flop",
        phrase="an old flip-flop",
        sense=1,
        power=1,
        action_text="but it was clumsy and silly for careful clean-up",
        qa_text="poked at the plastic with a flip-flop",
        tags={"cleanup_tool"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Ruby", "Tessa", "Maya", "Lena"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Eli", "Jude", "Nico", "Arlo"]
TRAITS = ["gentle", "curious", "careful", "cheerful", "thoughtful", "eager"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for spot_id, spot in SPOTS.items():
        for plastic_id, plastic in PLASTICS.items():
            for creature_id, creature in CREATURES.items():
                if hazard_at_risk(spot, plastic, creature):
                    combos.append((spot_id, plastic_id, creature_id))
    return combos


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    spot: str
    plastic: str
    creature: str
    tool: str
    child_name: str
    child_gender: str
    adult: str
    trait: str
    delay: int = 1
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
    "plastic": [
        (
            "Why is plastic a problem in a tidal pool?",
            "Plastic does not belong in a tidal pool. It can block water, trap little animals, and stay there for a very long time."
        )
    ],
    "tide_pool": [
        (
            "What is a tidal pool?",
            "A tidal pool is a small pocket of sea water left behind when the tide goes out. Tiny sea creatures live there until the water returns."
        )
    ],
    "channel": [
        (
            "Why does a tiny sea channel matter?",
            "A tiny sea channel lets fresh sea water slip in and out. If it gets blocked, a small pool can grow warmer and less safe for animals."
        )
    ],
    "crab": [
        (
            "What is a hermit crab?",
            "A hermit crab is a small crab that lives inside a borrowed shell. It needs sea water and a safe shore to move around."
        )
    ],
    "snail": [
        (
            "What is a sea snail?",
            "A sea snail is a small sea animal with a shell. It often clings to wet rocks and needs moisture to stay safe."
        )
    ],
    "fish": [
        (
            "What is a goby?",
            "A goby is a tiny fish that can live in shallow sea places like rock pools. It still needs cool, moving water to do well."
        )
    ],
    "cleanup_tool": [
        (
            "Why should a grown-up help remove litter near sea creatures?",
            "A grown-up can help choose a careful way to clean up. That keeps both the child and the tiny animals safer."
        )
    ],
    "shell": [
        (
            "What is a shell good for at the beach?",
            "A shell can be something pretty to look at or a gentle scoop for water in a pretend game. It should not be used to hurt animals or leave litter behind."
        )
    ],
}
KNOWLEDGE_ORDER = ["tide_pool", "channel", "plastic", "crab", "snail", "fish", "cleanup_tool", "shell"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    plastic = f["plastic_cfg"]
    creature = f["creature_cfg"]
    return [
        (
            f'Write a rhyming story for a 3-to-5-year-old set in a tidal pool that uses '
            f'the words "snowpan", "plastic", and "self", and teaches kindness.'
        ),
        (
            f"Tell a gentle moral tale where {child.id} first wants a shiny {plastic.label} for the self, "
            f"but then helps {creature.phrase} instead with a snowpan shell and {adult.label_word}'s help."
        ),
        (
            f"Write a short rhyming beach story where a child chooses helping over keeping, "
            f"cleans litter from a tidal pool, and ends with a clear moral image."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    spot = f["spot_cfg"]
    plastic = f["plastic_cfg"]
    creature = f["creature_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child exploring a tidal pool, and {adult.label_word} who helps. "
            f"They notice a small sea creature in trouble and work together to help it."
        ),
        (
            "What was the snowpan?",
            f"The snowpan was the white shell {child.id} found at the shore. "
            f"It started as a treasure for play, but later it became part of the helping."
        ),
        (
            f"Why was the plastic a problem?",
            f"The {plastic.label} was blocking water near {spot.phrase}. "
            f"That mattered because {creature.phrase} needed cool sea water to keep the pool safe."
        ),
        (
            f"Why did {child.id} have to choose between the self and helping?",
            f"{child.id} liked how the shiny plastic looked and wanted to keep it for a game. "
            f"Then {child.pronoun().capitalize()} saw that keeping it there would leave {creature.phrase} in trouble, so the choice became a moral one."
        ),
        (
            f"How did {child.id} and {adult.label_word} help?",
            f"They {tool.qa_text}. "
            f"Removing the blockage let the water move again and changed the whole little pool."
        ),
    ]
    if outcome == "urgent_help":
        qa.append(
            (
                "Why did they use the snowpan shell after moving the plastic?",
                f"They used the snowpan shell because the creature was still warm and needed gentler help right away. "
                f"{child.id} used the shell to carry cool water and guide the little animal toward deeper safety."
            )
        )
    else:
        qa.append(
            (
                "What changed after the plastic was removed?",
                f"A trickle of sea water could move through the channel again, and the creature settled safely in the pool. "
                f"The danger shrank as soon as the blockage was gone."
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f"The story teaches that a kind choice matters more than keeping a pretty thing for the self. "
            f"When {child.id} helped first, both the creature and the shore were better for it."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"plastic", "tide_pool", "channel", "shell", "cleanup_tool"}
    tags |= set(f["creature_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        spot="runnel",
        plastic="bottle_cap",
        creature="hermit_crab",
        tool="drift_stick",
        child_name="Mina",
        child_gender="girl",
        adult="mother",
        trait="thoughtful",
        delay=0,
    ),
    StoryParams(
        spot="rock_cup",
        plastic="spoon",
        creature="goby",
        tool="beach_gloves",
        child_name="Owen",
        child_gender="boy",
        adult="father",
        trait="curious",
        delay=1,
    ),
    StoryParams(
        spot="seaweed_gap",
        plastic="wrapper",
        creature="sea_snail",
        tool="shell_tongs",
        child_name="Lila",
        child_gender="girl",
        adult="aunt",
        trait="gentle",
        delay=2,
    ),
    StoryParams(
        spot="runnel",
        plastic="wrapper",
        creature="goby",
        tool="drift_stick",
        child_name="Theo",
        child_gender="boy",
        adult="uncle",
        trait="careful",
        delay=1,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(S, P, C) :- spot(S), plastic(P), creature(C),
                   width(S, W), fits(P, W),
                   lives_in_spot(C, S), spot_has(S, C).

sensible(T) :- tool(T), sense(T, V), sense_min(M), V >= M.

valid(S, P, C) :- hazard(S, P, C).

% --- outcome model ---------------------------------------------------------
severity(F + D) :- chosen_creature(C), fragility(C, F), delay(D).
urgent_help :- severity(V), V >= 4.
steady_help :- not urgent_help.

outcome(urgent_help) :- urgent_help.
outcome(steady_help) :- steady_help.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("width", sid, spot.width))
        for creature_id in sorted(spot.habitats):
            lines.append(asp.fact("spot_has", sid, creature_id))
    for pid, plastic in PLASTICS.items():
        lines.append(asp.fact("plastic", pid))
        for width in sorted(plastic.fits):
            lines.append(asp.fact("fits", pid, width))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("fragility", cid, creature.fragility))
        for spot_id in sorted(creature.habitats):
            lines.append(asp.fact("lives_in_spot", cid, spot_id))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
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
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_creature", params.creature),
            asp.fact("delay", params.delay),
        ]
    )
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
    p_sense = {tool.id for tool in sensible_tools()}
    if c_sense == p_sense:
        print(f"OK: sensible tools match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {seed}.")
            break

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: generate() smoke test succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rhyming tidal-pool story about plastic, kindness, and choosing help over self."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--plastic", choices=PLASTICS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the child pauses before helping")
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP model")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, gender: str = "") -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    return rng.choice(pool), chosen_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    if args.spot and args.plastic and args.creature:
        spot = SPOTS[args.spot]
        plastic = PLASTICS[args.plastic]
        creature = CREATURES[args.creature]
        if not hazard_at_risk(spot, plastic, creature):
            raise StoryError(explain_rejection(spot, plastic, creature))

    combos = [
        combo
        for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.plastic is None or combo[1] == args.plastic)
        and (args.creature is None or combo[2] == args.creature)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot_id, plastic_id, creature_id = rng.choice(sorted(combos))
    tool_id = args.tool or rng.choice(sorted(tool.id for tool in sensible_tools()))
    child_name, child_gender = _pick_child(rng, args.child_gender or "")
    if args.child_name:
        child_name = args.child_name
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        spot=spot_id,
        plastic=plastic_id,
        creature=creature_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=child_gender,
        adult=adult,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.plastic not in PLASTICS:
        raise StoryError(f"(Unknown plastic item: {params.plastic})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if TOOLS[params.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))
    if not hazard_at_risk(SPOTS[params.spot], PLASTICS[params.plastic], CREATURES[params.creature]):
        raise StoryError(explain_rejection(SPOTS[params.spot], PLASTICS[params.plastic], CREATURES[params.creature]))

    world = tell(
        spot_cfg=SPOTS[params.spot],
        plastic_cfg=PLASTICS[params.plastic],
        creature_cfg=CREATURES[params.creature],
        tool_cfg=TOOLS[params.tool],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, plastic, creature) combos:\n")
        for spot, plastic, creature in combos:
            print(f"  {spot:12} {plastic:12} {creature}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.plastic} in {p.spot} with {p.creature} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
