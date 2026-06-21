#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/balk_mow_teamwork_fable.py
=====================================================

A standalone story world for a small fable about a creature who must mow a shared
place, balks when the task looks too hard, and learns what teamwork can do.

Reference seed, rebuilt as a world model rather than a frozen paragraph:
-----------------------------------------------------------------------
A young field animal is asked to mow an overgrown path or green before others
need it. The grass is thicker, steeper, or stonier than it first looked, so the
hero begins to balk. A friend offers help suited to the tool. If the hero shares
the work early, the mowing goes smoothly; if the hero refuses, the tool snags or
the work drags until the hero learns to accept help. The ending shows the place
changed by teamwork, and the moral is plain without sounding like a lecture.

Run it
------
    python storyworlds/worlds/gpt-5.4/balk_mow_teamwork_fable.py
    python storyworlds/worlds/gpt-5.4/balk_mow_teamwork_fable.py --field brook_lane --tool reel_mower
    python storyworlds/worlds/gpt-5.4/balk_mow_teamwork_fable.py --tool hand_shears --field hill_meadow
    python storyworlds/worlds/gpt-5.4/balk_mow_teamwork_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/balk_mow_teamwork_fable.py --all
    python storyworlds/worlds/gpt-5.4/balk_mow_teamwork_fable.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/balk_mow_teamwork_fable.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        female = {"hen", "goose", "ewe", "mare", "doe"}
        male = {"donkey", "goat", "mule", "ram", "ox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class FieldCfg:
    id: str
    label: str
    phrase: str
    need: str
    benefit: str
    size: int
    steep: bool = False
    stones: int = 0
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    verb: str
    max_size: int
    works_on_steep: bool
    wheels: bool
    solo_power: int
    team_bonus: int
    helper_task: str
    team_line: str
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
class AnimalCfg:
    id: str
    name: str
    type: str
    strength: int
    temperament: str
    opening: str
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
class HelperCfg:
    id: str
    name: str
    type: str
    skill: int
    offer: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_balk(world: World) -> list[str]:
    hero = world.get("hero")
    demand = int(world.facts["demand"])
    solo_cap = int(world.facts["solo_cap"])
    if demand <= solo_cap:
        return []
    sig = ("balk", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hesitation"] += 1
    hero.memes["balk"] += 1
    return ["__balk__"]


def _r_snag(world: World) -> list[str]:
    field_cfg = world.facts["field_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    if not tool_cfg.wheels or field_cfg.stones <= 0 or world.facts["teamwork"]:
        return []
    sig = ("snag", field_cfg.id, tool_cfg.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("tool").meters["snagged"] += 1
    world.get("hero").memes["frustration"] += 1
    return ["__snag__"]


def _r_clear(world: World) -> list[str]:
    field_ent = world.get("field")
    if field_ent.meters["effort"] < world.facts["demand"]:
        return []
    sig = ("clear", field_ent.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    field_ent.meters["trimmed"] = 1
    field_ent.meters["clear"] = 1
    world.get("village").meters["benefit"] += 1
    world.get("hero").memes["pride"] += 1
    if world.facts["teamwork"]:
        world.get("helper").memes["pride"] += 1
        world.get("hero").memes["gratitude"] += 1
    return ["__clear__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="balk", tag="emotion", apply=_r_balk),
    Rule(name="snag", tag="physical", apply=_r_snag),
    Rule(name="clear", tag="physical", apply=_r_clear),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


FIELDS = {
    "brook_lane": FieldCfg(
        id="brook_lane",
        label="brook lane",
        phrase="the lane beside the brook",
        need="ducklings and carts needed a clean lane to pass",
        benefit="little ducklings could waddle through without vanishing in the grass",
        size=2,
        steep=False,
        stones=1,
        tags={"lane", "grass", "stones"},
    ),
    "orchard_ring": FieldCfg(
        id="orchard_ring",
        label="orchard ring",
        phrase="the ring path around the orchard",
        need="the orchard path had to be opened before the fruit baskets came",
        benefit="the orchard looked neat again, and the wheelbarrows could roll in a tidy circle",
        size=1,
        steep=False,
        stones=0,
        tags={"orchard", "grass"},
    ),
    "hill_meadow": FieldCfg(
        id="hill_meadow",
        label="hill meadow",
        phrase="the steep meadow above the mill",
        need="the geese needed a safe, short way up the hill before evening",
        benefit="a bright strip of meadow shone across the hill like a green ribbon cut neat",
        size=3,
        steep=True,
        stones=1,
        tags={"hill", "grass", "stones"},
    ),
}

TOOLS = {
    "reel_mower": ToolCfg(
        id="reel_mower",
        label="reel mower",
        phrase="a little reel mower with singing wheels",
        verb="mow",
        max_size=2,
        works_on_steep=False,
        wheels=True,
        solo_power=2,
        team_bonus=2,
        helper_task="skip ahead and flick stones from the wheels' path",
        team_line="One pushed while the other cleared the way, and the mower stopped grumbling.",
        tags={"mower", "teamwork"},
    ),
    "scythe": ToolCfg(
        id="scythe",
        label="scythe",
        phrase="a long scythe with a smooth ash handle",
        verb="mow",
        max_size=3,
        works_on_steep=True,
        wheels=False,
        solo_power=2,
        team_bonus=2,
        helper_task="gather each swath and lay it aside before the next swing",
        team_line="One cut in a shining arc while the other gathered the grass into neat rows.",
        tags={"scythe", "teamwork"},
    ),
    "hand_shears": ToolCfg(
        id="hand_shears",
        label="hand shears",
        phrase="a pair of hand shears bright as minnows",
        verb="clip and mow",
        max_size=1,
        works_on_steep=True,
        wheels=False,
        solo_power=1,
        team_bonus=1,
        helper_task="hold the cut grass in bundles so the clipping stayed even",
        team_line="One clipped while the other bundled, and the small path yielded inch by inch.",
        tags={"shears", "teamwork"},
    ),
}

ANIMALS = {
    "nib": AnimalCfg(
        id="nib",
        name="Nib",
        type="goat",
        strength=2,
        temperament="quick but doubtful",
        opening="liked to begin briskly and finish proudly",
        tags={"goat"},
    ),
    "bram": AnimalCfg(
        id="bram",
        name="Bram",
        type="donkey",
        strength=3,
        temperament="steady but stubborn",
        opening="believed a strong back could answer most troubles",
        tags={"donkey"},
    ),
    "thistle": AnimalCfg(
        id="thistle",
        name="Thistle",
        type="ewe",
        strength=2,
        temperament="gentle and careful",
        opening="was patient with knots, gates, and all slow things",
        tags={"ewe"},
    ),
}

HELPERS = {
    "pip": HelperCfg(
        id="pip",
        name="Pip",
        type="mouse",
        skill=1,
        offer="I am small, but small feet can dart where big hooves cannot.",
        tags={"mouse", "teamwork"},
    ),
    "fern": HelperCfg(
        id="fern",
        name="Fern",
        type="goose",
        skill=1,
        offer="I may not pull, but I can keep the work straight and the path clear.",
        tags={"goose", "teamwork"},
    ),
    "moss": HelperCfg(
        id="moss",
        name="Moss",
        type="ox",
        skill=2,
        offer="A heavy task grows lighter when two lean into it.",
        tags={"ox", "teamwork"},
    ),
}


def demand_of(field_cfg: FieldCfg) -> int:
    return field_cfg.size + (1 if field_cfg.steep else 0) + field_cfg.stones


def solo_capacity(hero_cfg: AnimalCfg, tool_cfg: ToolCfg, field_cfg: FieldCfg) -> int:
    snag_penalty = 1 if tool_cfg.wheels and field_cfg.stones > 0 else 0
    return hero_cfg.strength + tool_cfg.solo_power - snag_penalty


def team_capacity(hero_cfg: AnimalCfg, helper_cfg: HelperCfg, tool_cfg: ToolCfg) -> int:
    return hero_cfg.strength + helper_cfg.skill + tool_cfg.team_bonus


def combo_reason(field_cfg: FieldCfg, tool_cfg: ToolCfg) -> Optional[str]:
    if field_cfg.size > tool_cfg.max_size:
        return (
            f"(No story: {tool_cfg.label} is too small a tool for {field_cfg.phrase}. "
            f"The grass there asks for a stronger way to mow.)"
        )
    if field_cfg.steep and not tool_cfg.works_on_steep:
        return (
            f"(No story: {tool_cfg.label} is a poor choice on {field_cfg.phrase}. "
            f"A wheeled mower would fight the slope instead of cutting it well.)"
        )
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for field_id, field_cfg in FIELDS.items():
        for tool_id, tool_cfg in TOOLS.items():
            if combo_reason(field_cfg, tool_cfg) is None:
                combos.append((field_id, tool_id))
    return combos


def predict_outcome(hero_cfg: AnimalCfg, helper_cfg: HelperCfg, field_cfg: FieldCfg,
                    tool_cfg: ToolCfg, choice: str) -> str:
    if choice == "accept":
        return "shared_early"
    if solo_capacity(hero_cfg, tool_cfg, field_cfg) >= demand_of(field_cfg):
        return "solo"
    return "shared_late"


def predict_facts(hero_cfg: AnimalCfg, helper_cfg: HelperCfg, field_cfg: FieldCfg,
                  tool_cfg: ToolCfg, choice: str) -> dict:
    return {
        "demand": demand_of(field_cfg),
        "solo_cap": solo_capacity(hero_cfg, tool_cfg, field_cfg),
        "team_cap": team_capacity(hero_cfg, helper_cfg, tool_cfg),
        "outcome": predict_outcome(hero_cfg, helper_cfg, field_cfg, tool_cfg, choice),
    }


def introduce(world: World, hero: Entity, field_cfg: FieldCfg, tool_cfg: ToolCfg) -> None:
    world.say(
        f"In a little valley where beasts spoke plainly and the grass grew according to its own opinion, "
        f"{hero.id} the {hero.type} {world.facts['hero_cfg'].opening}."
    )
    world.say(
        f"One morning, the elders looked toward {field_cfg.phrase}, where the grass had risen shaggy and high. "
        f"{field_cfg.need}."
    )
    world.say(
        f'So {hero.id} was given {tool_cfg.phrase} and told, "Go and {tool_cfg.verb} a clean way before the sun leans west."'
    )


def approach_task(world: World, hero: Entity, field_cfg: FieldCfg, tool: Entity) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"{hero.id} set off with the {tool.label}. But when {hero.pronoun()} reached {field_cfg.phrase}, "
        f"{hero.pronoun()} saw how the stems leaned thickly across one another like a crowd unwilling to budge."
    )
    propagate(world, narrate=False)
    if hero.memes["balk"] >= THRESHOLD:
        hero.memes["worry"] += 1
        world.say(
            f"{hero.pronoun().capitalize()} gave the handle a doubtful tug, then began to balk. "
            f'"This is more meadow than it looked from the gate," {hero.pronoun()} muttered.'
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} tested the first strip of grass and found the task honest, if not easy."
        )


def offer_help(world: World, helper: Entity, hero: Entity, tool_cfg: ToolCfg) -> None:
    helper.memes["care"] += 1
    world.say(
        f"Just then {helper.id} the {helper.type} came by and watched for a moment. "
        f'"{HELPERS[world.facts["helper_cfg"].id].offer}" {helper.pronoun()} said.'
    )
    world.say(
        f'"If you take the handle, I can {tool_cfg.helper_task}," {helper.id} offered.'
    )


def accept_help(world: World, hero: Entity, helper: Entity, field_ent: Entity, tool_cfg: ToolCfg) -> None:
    world.facts["teamwork"] = True
    hero.memes["humility"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'{hero.id} lowered {hero.pronoun("possessive")} ears, then nodded. '
        f'"A shared field is best served by shared work," {hero.pronoun()} said.'
    )
    effort = float(world.facts["team_cap"])
    field_ent.meters["effort"] += effort
    propagate(world, narrate=False)
    world.say(tool_cfg.team_line)
    if world.get("tool").meters["snagged"] >= THRESHOLD:
        world.say("Even the snags seemed ashamed to remain when two minds watched the ground.")
    if field_ent.meters["clear"] >= THRESHOLD:
        world.say(
            f"Before long, the hard patch gave way, and the cut path lay open from end to end."
        )


def refuse_and_struggle(world: World, hero: Entity, field_ent: Entity, tool_cfg: ToolCfg) -> None:
    hero.memes["stubbornness"] += 1
    world.say(
        f'But {hero.id} shook {hero.pronoun("possessive")} head. '
        f'"If the task is mine, the praise should be mine as well," {hero.pronoun()} said.'
    )
    field_ent.meters["effort"] += float(max(world.facts["solo_cap"], 0))
    propagate(world, narrate=False)
    if world.get("tool").meters["snagged"] >= THRESHOLD:
        world.say(
            f"The wheels caught on hidden stones, and the {tool_cfg.label} complained louder than a crow on a fence."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} worked alone for a while, but the grass fell slower than the shadow moved."
        )
    world.say(
        f"Soon {hero.id}'s shoulders ached, and the uncut strip ahead looked almost as long as before."
    )


def ask_again(world: World, helper: Entity, hero: Entity) -> None:
    world.say(
        f'{helper.id} did not laugh. "{hero.id}," {helper.pronoun()} said gently, '
        f'"a narrow path is still made of many blades. Let us answer them together."'
    )


def late_teamwork(world: World, hero: Entity, helper: Entity, field_ent: Entity, tool_cfg: ToolCfg) -> None:
    world.facts["teamwork"] = True
    hero.memes["humility"] += 1
    hero.memes["gratitude"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{hero.id} looked at the stubborn grass, then at {helper.id}, and let out the breath {hero.pronoun()} had been using for pride."
    )
    world.say(f'"Very well," {hero.pronoun()} said. "Stand with me, and we shall mow it properly."')
    field_ent.meters["effort"] += float(world.facts["team_cap"])
    propagate(world, narrate=False)
    world.say(tool_cfg.team_line)
    world.say(
        f"This time the work moved as work should move: not in jerks and sighs, but in a steady answer from both of them."
    )


def solo_finish(world: World, hero: Entity, field_ent: Entity) -> None:
    hero.memes["weariness"] += 1
    field_ent.meters["effort"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"At last the final tuft bent, and the path stood open. Yet {hero.id} felt more worn than proud."
    )


def ending(world: World, hero: Entity, helper: Entity, field_cfg: FieldCfg) -> None:
    outcome = world.facts["outcome"]
    village = world.get("village")
    if village.meters["benefit"] < THRESHOLD:
        village.meters["benefit"] = 1
    world.para()
    if outcome == "shared_early":
        world.say(
            f"So the lane was opened while the day was still young, and {field_cfg.benefit}."
        )
        world.say(
            f"{hero.id} smiled at {helper.id} and said, "
            f'"Two willing hearts can mow what one proud heart only stares at."'
        )
        world.say(
            "From then on, whenever a chore looked wide, the valley folk looked first for a friend and only second for a handle."
        )
    elif outcome == "shared_late":
        world.say(
            f"Together they finished before dusk, and {field_cfg.benefit}."
        )
        world.say(
            f'{hero.id} bowed {hero.pronoun("possessive")} head to {helper.id}. '
            f'"I lost more time to pride than I would ever have lost to sharing," {hero.pronoun()} said.'
        )
        world.say(
            "And the creatures who passed that evening saw not only a neat path, but a lesson cut into it as plainly as any furrow."
        )
    else:
        world.say(
            f"The path was opened at last, and {field_cfg.benefit}."
        )
        world.say(
            f'Yet while the others praised the clear way, {hero.id} remembered the offer {helper.id} had made and answered only, '
            f'"Even a strong back should not despise a willing wing or paw."'
        )
        world.say(
            "So the fable was told afterward like this: work done alone may finish the field, but shared work sweetens the day."
        )


def tell(hero_cfg: AnimalCfg, helper_cfg: HelperCfg, field_cfg: FieldCfg,
         tool_cfg: ToolCfg, choice: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_cfg.name,
        kind="character",
        type=hero_cfg.type,
        label=hero_cfg.name,
        role="hero",
        traits=[hero_cfg.temperament],
        attrs={"strength": hero_cfg.strength},
    ))
    helper = world.add(Entity(
        id=helper_cfg.name,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.name,
        role="helper",
        attrs={"skill": helper_cfg.skill},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        attrs={"wheels": tool_cfg.wheels},
    ))
    field_ent = world.add(Entity(
        id="field",
        kind="thing",
        type="field",
        label=field_cfg.label,
        attrs={"size": field_cfg.size, "steep": field_cfg.steep, "stones": field_cfg.stones},
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="commons",
        label="the commons",
    ))

    world.facts.update(
        hero_cfg=hero_cfg,
        helper_cfg=helper_cfg,
        field_cfg=field_cfg,
        tool_cfg=tool_cfg,
        choice=choice,
        demand=demand_of(field_cfg),
        solo_cap=solo_capacity(hero_cfg, tool_cfg, field_cfg),
        team_cap=team_capacity(hero_cfg, helper_cfg, tool_cfg),
        teamwork=False,
        outcome=predict_outcome(hero_cfg, helper_cfg, field_cfg, tool_cfg, choice),
    )

    introduce(world, hero, field_cfg, tool_cfg)
    world.para()
    approach_task(world, hero, field_cfg, tool)
    offer_help(world, helper, hero, tool_cfg)
    world.para()

    if world.facts["outcome"] == "shared_early":
        accept_help(world, hero, helper, field_ent, tool_cfg)
    elif world.facts["outcome"] == "shared_late":
        refuse_and_struggle(world, hero, field_ent, tool_cfg)
        ask_again(world, helper, hero)
        late_teamwork(world, hero, helper, field_ent, tool_cfg)
    else:
        refuse_and_struggle(world, hero, field_ent, tool_cfg)
        solo_finish(world, hero, field_ent)

    ending(world, hero, helper, field_cfg)
    world.facts.update(
        hero=hero,
        helper=helper,
        field=field_ent,
        tool=tool,
        village=village,
        balked=hero.memes["balk"] >= THRESHOLD,
        cleared=field_ent.meters["clear"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more people or animals share a job and help each other do it. A hard task often becomes easier because each helper can do one part well."
        )
    ],
    "mower": [
        (
            "What does it mean to mow?",
            "To mow means to cut grass so it becomes short and tidy. People can mow with a mower, and in stories animals may do it too."
        )
    ],
    "scythe": [
        (
            "What is a scythe?",
            "A scythe is a long tool with a curved blade for cutting tall grass. It works best when someone swings it carefully in wide arcs."
        )
    ],
    "shears": [
        (
            "What are hand shears?",
            "Hand shears are two blades joined together for clipping plants or grass by hand. They are good for small places, but slow on a big field."
        )
    ],
    "grass": [
        (
            "Why does tall grass need to be cut sometimes?",
            "Tall grass can hide paths, stones, and little animals. Cutting a clear strip can make walking safer and easier."
        )
    ],
    "stones": [
        (
            "Why can stones make mowing harder?",
            "Stones can block a blade or catch under wheels. That means the tool jerks, stops, or needs someone to clear the way."
        )
    ],
    "hill": [
        (
            "Why is work harder on a hill?",
            "A hill makes you push or pull against the slope, so your body tires faster. Tools with wheels can be awkward there too."
        )
    ],
    "lane": [
        (
            "What is a lane?",
            "A lane is a small road or path. In a village it may be used by walkers, carts, and little animals moving from place to place."
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "mower", "scythe", "shears", "grass", "stones", "hill", "lane"]


@dataclass
class StoryParams:
    hero: str
    helper: str
    field: str
    tool: str
    choice: str = "accept"
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


CURATED = [
    StoryParams(
        hero="nib",
        helper="pip",
        field="brook_lane",
        tool="reel_mower",
        choice="accept",
    ),
    StoryParams(
        hero="bram",
        helper="fern",
        field="brook_lane",
        tool="reel_mower",
        choice="refuse",
    ),
    StoryParams(
        hero="thistle",
        helper="moss",
        field="hill_meadow",
        tool="scythe",
        choice="accept",
    ),
    StoryParams(
        hero="nib",
        helper="moss",
        field="hill_meadow",
        tool="scythe",
        choice="refuse",
    ),
    StoryParams(
        hero="thistle",
        helper="pip",
        field="orchard_ring",
        tool="hand_shears",
        choice="refuse",
    ),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    field_cfg = world.facts["field_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "shared_early":
        return [
            f'Write a short fable for a 3-to-5-year-old that uses the words "balk" and "mow" and teaches teamwork.',
            f"Tell a fable where {hero.id} is asked to mow {field_cfg.phrase}, begins to balk, and wisely accepts help from {helper.id}.",
            f"Write a child-friendly animal fable about shared work, with {tool_cfg.label} used to clear {field_cfg.phrase} before others need it.",
        ]
    if outcome == "shared_late":
        return [
            f'Write a short fable for a 3-to-5-year-old that uses the words "balk" and "mow" and teaches teamwork.',
            f"Tell a fable where {hero.id} refuses help at first while trying to mow {field_cfg.phrase}, then learns that pride wastes time.",
            f"Write a simple moral tale in which {helper.id} helps {hero.id} finish a hard mowing job after a stubborn beginning.",
        ]
    return [
        f'Write a short fable for a 3-to-5-year-old that uses the words "balk" and "mow" and teaches teamwork.',
        f"Tell a fable where {hero.id} manages to mow {field_cfg.phrase} alone but learns that help should not be scorned.",
        f"Write a gentle animal story where the task gets finished, yet the moral still praises willing helpers over pride.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    field_cfg = world.facts["field_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, who was asked to mow {field_cfg.phrase}, and {helper.id} the {helper.type}, who offered help."
        ),
        (
            f"Why did {hero.id} have to mow the grass?",
            f"{field_cfg.need.capitalize()}. The job mattered because the place was shared by other creatures, not only by {hero.id}."
        ),
        (
            f"Why did {hero.id} begin to balk?",
            f"{hero.id} saw that the grass was thicker and more troublesome than it had looked from far away. The task felt heavy, and that made {hero.pronoun()} hesitate before the real work even began."
        ),
        (
            f"What help did {helper.id} offer?",
            f"{helper.id} offered to {tool_cfg.helper_task}. That mattered because the helper's part matched the tool instead of being random extra fuss."
        ),
    ]
    if outcome == "shared_early":
        qa.append(
            (
                f"How did teamwork help them finish?",
                f"They divided the job so each of them handled one useful part. Because one worked the tool and the other supported the tricky part, the grass gave way quickly and the path opened while the day was still young."
            )
        )
        qa.append(
            (
                "What changed at the end of the story?",
                f"{field_cfg.benefit.capitalize()}. The ending image proves the work was truly done and that sharing the labor changed the world around them."
            )
        )
    elif outcome == "shared_late":
        qa.append(
            (
                f"What happened when {hero.id} tried to work alone first?",
                f"The job dragged, and the tool or the heavy grass fought back. That failure showed {hero.id} that pride was costing more than help would have cost."
            )
        )
        qa.append(
            (
                f"What lesson did {hero.id} learn from {helper.id}?",
                f"{hero.id} learned that accepting help is not weakness. By working together at last, the two of them finished in time and turned a stubborn struggle into a shared success."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} finish alone?",
                f"Yes, but the work left {hero.pronoun()} tired instead of glad. The story says the field was cut, yet the sweeter lesson was that willing help should have been welcomed."
            )
        )
        qa.append(
            (
                "What is the moral of this version?",
                "A task may be finished by one creature, but kindness and shared effort make the labor lighter and the ending better. The fable praises humility, not just strength."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"teamwork", "grass"}
    field_cfg = world.facts["field_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    tags |= set(field_cfg.tags)
    tags |= set(tool_cfg.tags)
    tags |= set(helper_cfg.tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(
        f"  facts: outcome={world.facts.get('outcome')} demand={world.facts.get('demand')} "
        f"solo_cap={world.facts.get('solo_cap')} team_cap={world.facts.get('team_cap')} "
        f"teamwork={world.facts.get('teamwork')}"
    )
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(field_cfg: FieldCfg, tool_cfg: ToolCfg) -> str:
    reason = combo_reason(field_cfg, tool_cfg)
    return reason if reason is not None else "(No story: this combination is unreasonable.)"


ASP_RULES = r"""
valid(Field, Tool) :- field(Field), tool(Tool),
                      field_size(Field, FS), tool_max_size(Tool, TS), FS <= TS,
                      not bad_slope(Field, Tool).

bad_slope(Field, Tool) :- steep(Field), not works_on_steep(Tool).

demand(Field, D) :- field_size(Field, FS), stones(Field, ST), steep(Field), D = FS + ST + 1.
demand(Field, D) :- field_size(Field, FS), stones(Field, ST), not steep(Field), D = FS + ST.

solo_cap(Hero, Field, Tool, C) :-
    strength(Hero, HS), solo_power(Tool, TP), wheels(Tool), stones(Field, ST), ST > 0,
    C = HS + TP - 1.
solo_cap(Hero, Field, Tool, C) :-
    strength(Hero, HS), solo_power(Tool, TP), not wheels(Tool),
    C = HS + TP.
solo_cap(Hero, Field, Tool, C) :-
    strength(Hero, HS), solo_power(Tool, TP), wheels(Tool), stones(Field, 0),
    C = HS + TP.

team_cap(Hero, Helper, Tool, C) :-
    strength(Hero, HS), helper_skill(Helper, SK), team_bonus(Tool, TB),
    C = HS + SK + TB.

outcome(shared_early) :- choice(accept).
outcome(solo) :- choice(refuse), chosen(Hero, Helper, Field, Tool),
                 solo_cap(Hero, Field, Tool, SC), demand(Field, D), SC >= D.
outcome(shared_late) :- choice(refuse), chosen(Hero, Helper, Field, Tool),
                        solo_cap(Hero, Field, Tool, SC), demand(Field, D), SC < D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for field_id, field_cfg in FIELDS.items():
        lines.append(asp.fact("field", field_id))
        lines.append(asp.fact("field_size", field_id, field_cfg.size))
        lines.append(asp.fact("stones", field_id, field_cfg.stones))
        if field_cfg.steep:
            lines.append(asp.fact("steep", field_id))
    for tool_id, tool_cfg in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_max_size", tool_id, tool_cfg.max_size))
        lines.append(asp.fact("solo_power", tool_id, tool_cfg.solo_power))
        lines.append(asp.fact("team_bonus", tool_id, tool_cfg.team_bonus))
        if tool_cfg.works_on_steep:
            lines.append(asp.fact("works_on_steep", tool_id))
        if tool_cfg.wheels:
            lines.append(asp.fact("wheels", tool_id))
    for hero_id, hero_cfg in ANIMALS.items():
        lines.append(asp.fact("hero", hero_id))
        lines.append(asp.fact("strength", hero_id, hero_cfg.strength))
    for helper_id, helper_cfg in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_skill", helper_id, helper_cfg.skill))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen", params.hero, params.helper, params.field, params.tool),
        asp.fact("choice", params.choice),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an animal balks at a mowing task and learns teamwork in a fable shape."
    )
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--field", choices=FIELDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--choice", choices=["accept", "refuse"],
                    help="whether the hero accepts help at once or refuses it at first")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (field, tool) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.field and args.tool:
        reason = combo_reason(FIELDS[args.field], TOOLS[args.tool])
        if reason is not None:
            raise StoryError(reason)

    combos = [
        combo for combo in valid_combos()
        if (args.field is None or combo[0] == args.field)
        and (args.tool is None or combo[1] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    field_id, tool_id = rng.choice(sorted(combos))
    hero_id = args.hero or rng.choice(sorted(ANIMALS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    choice = args.choice or rng.choice(["accept", "refuse"])
    return StoryParams(
        hero=hero_id,
        helper=helper_id,
        field=field_id,
        tool=tool_id,
        choice=choice,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in ANIMALS:
        raise StoryError(f"(Unknown hero '{params.hero}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if params.field not in FIELDS:
        raise StoryError(f"(Unknown field '{params.field}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool '{params.tool}'.)")
    if params.choice not in {"accept", "refuse"}:
        raise StoryError(f"(Unknown choice '{params.choice}'.)")
    reason = combo_reason(FIELDS[params.field], TOOLS[params.tool])
    if reason is not None:
        raise StoryError(reason)

    world = tell(
        hero_cfg=ANIMALS[params.hero],
        helper_cfg=HELPERS[params.helper],
        field_cfg=FIELDS[params.field],
        tool_cfg=TOOLS[params.tool],
        choice=params.choice,
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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(50):
        try:
            ns = build_parser().parse_args([])
            cases.append(resolve_params(ns, random.Random(seed)))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve_params failure at seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        py = predict_outcome(ANIMALS[params.hero], HELPERS[params.helper], FIELDS[params.field], TOOLS[params.tool], params.choice)
        cl = asp_outcome(params)
        if py != cl:
            mismatches += 1
            print(f"Outcome mismatch for {params}: python={py} clingo={cl}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(smoke, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (field, tool) combos:\n")
        for field_id, tool_id in combos:
            print(f"  {field_id:12} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {ANIMALS[p.hero].name} with {HELPERS[p.helper].name}: {p.tool} at {p.field} ({predict_outcome(ANIMALS[p.hero], HELPERS[p.helper], FIELDS[p.field], TOOLS[p.tool], p.choice)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
