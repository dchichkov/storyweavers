#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/valley_clamp_repetition_moral_value_superhero_story.py
==================================================================================

A standalone story world for a tiny superhero domain: a child hero in a valley
must fix a loose bridge rail before the market path becomes dangerous. The world
models a repeated safety method -- "hold, clamp, check" -- and a moral value:
real heroes help other people carefully, not show off.

Run it
------
    python storyworlds/worlds/gpt-5.4/valley_clamp_repetition_moral_value_superhero_story.py
    python storyworlds/worlds/gpt-5.4/valley_clamp_repetition_moral_value_superhero_story.py --hero capelet --problem rail --tool clamp
    python storyworlds/worlds/gpt-5.4/valley_clamp_repetition_moral_value_superhero_story.py --problem stone
    python storyworlds/worlds/gpt-5.4/valley_clamp_repetition_moral_value_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/valley_clamp_repetition_moral_value_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/valley_clamp_repetition_moral_value_superhero_story.py --trace
    python storyworlds/worlds/gpt-5.4/valley_clamp_repetition_moral_value_superhero_story.py --verify
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
CARE_MIN = 2
MAX_HURRY = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    sturdy: bool = False
    can_secure: bool = False
    # physical + emotional dimensions
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class HeroMode:
    id: str
    title: str
    outfit: str
    power_phrase: str
    landing: str
    close: str
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
    the: str
    place: str
    needs_tool: bool
    risk_to: str
    severity: int
    fix_text: str
    fail_text: str
    flake_text: str
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
class Tool:
    id: str
    label: str
    phrase: str
    can_secure: bool
    care: int
    action: str
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
    kind_word: str
    advice: str
    teaches_care: bool
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


def _r_gap_risk(world: World) -> list[str]:
    out: list[str] = []
    bridge = world.get("bridge")
    problem = world.get("problem")
    hero = world.get("hero")
    if problem.meters["loose"] >= THRESHOLD:
        sig = ("risk", problem.id)
        if sig not in world.fired:
            world.fired.add(sig)
            bridge.meters["danger"] += 1
            hero.memes["worry"] += 1
            out.append("__risk__")
    return out


def _r_secure(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    bridge = world.get("bridge")
    hero = world.get("hero")
    tool = world.get("tool")
    if hero.meters["held"] >= THRESHOLD and hero.meters["clamped"] >= THRESHOLD and hero.meters["checked"] >= THRESHOLD:
        sig = ("secure", problem.id)
        if sig not in world.fired:
            world.fired.add(sig)
            problem.meters["loose"] = 0.0
            problem.meters["secure"] += 1
            bridge.meters["danger"] = 0.0
            hero.memes["relief"] += 1
            if tool.can_secure:
                out.append("__secure__")
    return out


CAUSAL_RULES = [
    Rule(name="gap_risk", tag="physical", apply=_r_gap_risk),
    Rule(name="secure", tag="physical", apply=_r_secure),
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


def problem_can_be_fixed(problem: Problem, tool: Tool) -> bool:
    return (not problem.needs_tool) or tool.can_secure


def careful_enough(tool: Tool) -> bool:
    return tool.care >= CARE_MIN


def success_possible(problem: Problem, tool: Tool, hurry: int) -> bool:
    return problem_can_be_fixed(problem, tool) and careful_enough(tool) and hurry <= MAX_HURRY


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hero in HEROES:
        for problem_id, problem in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if success_possible(problem, tool, 0):
                    combos.append((hero, problem_id, tool_id))
    return combos


def predict_fix(world: World, hurry: int) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    tool = sim.get("tool")
    problem = sim.get("problem")
    if problem.needs_tool and not tool.can_secure:
        return {"safe": False, "danger": sim.get("bridge").meters["danger"] + 1}
    if tool.care < CARE_MIN:
        return {"safe": False, "danger": sim.get("bridge").meters["danger"] + 1}
    if hurry > MAX_HURRY:
        hero.meters["held"] += 1
        hero.meters["clamped"] += 1
        hero.meters["checked"] = 0
        problem.meters["loose"] += 1
        propagate(sim, narrate=False)
        return {"safe": False, "danger": sim.get("bridge").meters["danger"]}
    hero.meters["held"] += 1
    hero.meters["clamped"] += 1
    hero.meters["checked"] += 1
    propagate(sim, narrate=False)
    return {"safe": sim.get("problem").meters["secure"] >= THRESHOLD, "danger": sim.get("bridge").meters["danger"]}


def introduce(world: World, hero: Entity, mode: HeroMode, valley_name: str) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {valley_name}, a little hero named {hero.id} pulled on {mode.outfit} and became {mode.title}. "
        f"{mode.landing}."
    )
    world.say(
        f"{hero.id} loved using {mode.power_phrase} to help neighbors before breakfast, after breakfast, and whenever anyone sighed, \"Oh dear.\""
    )


def discover(world: World, hero: Entity, problem: Problem, helper: Helper, valley_name: str) -> None:
    problem_ent = world.get("problem")
    problem_ent.meters["loose"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That morning, a worried {helper.kind_word} waved from the path above the valley stream. "
        f"{problem.The} at {problem.place} had come loose."
    )
    world.say(
        f"Children and carts used that path to reach the berry market, so the loose piece could hurt {problem.risk_to} if nobody fixed it soon."
    )


def boast(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'"I can finish this in one swoop!" {hero.id} said, puffing out {hero.pronoun("possessive")} chest.'
    )


def warn(world: World, hero: Entity, helper: Helper, hurry: int) -> None:
    pred = predict_fix(world, hurry)
    world.facts["predicted_safe"] = pred["safe"]
    world.facts["predicted_danger"] = pred["danger"]
    extra = " Real heroes help carefully." if helper.teaches_care else ""
    world.say(
        f'"{helper.advice} Hold, clamp, check," said the {helper.kind_word}.{extra}'
    )
    if not pred["safe"]:
        world.say(
            f'{hero.id} looked again and understood that rushing would leave the path unsafe.'
        )


def repeat_method(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["focus"] += 1
    hero.meters["held"] += 1
    world.say(f'{hero.id} took a steady breath. "Hold," {hero.pronoun()} whispered, and kept the shaky piece still.')
    hero.meters["clamped"] += 1
    world.say(f'"Clamp," {hero.pronoun()} said next, using {tool.phrase} to {tool.action}.')
    hero.meters["checked"] += 1
    propagate(world, narrate=False)
    world.say(f'"Check," {hero.pronoun()} finished, tugging twice to make sure nothing wobbled anymore.')


def rush_method(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["hurry"] += 1
    hero.meters["held"] += 1
    hero.meters["clamped"] += 1
    hero.meters["checked"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} grabbed {tool.phrase} and hurried through the job, but skipped the last check."
    )


def success_scene(world: World, hero: Entity, mode: HeroMode, problem: Problem, helper: Helper, valley_name: str) -> None:
    hero.memes["kindness"] += 1
    hero.memes["lesson"] += 1
    world.say(problem.fix_text)
    world.say(
        f'Soon the path above the valley stream was safe again. The {helper.kind_word} smiled, and {hero.id} smiled back even wider.'
    )
    world.say(
        f'"Hold, clamp, check," the children heading to market repeated as they crossed, and {mode.close}.'
    )


def fail_scene(world: World, hero: Entity, problem: Problem, helper: Helper) -> None:
    hero.memes["shame"] += 1
    world.say(problem.flake_text)
    world.say(problem.fail_text)
    world.say(
        f"The {helper.kind_word} was not angry. Instead, {helper.pronoun('subject') if hasattr(helper, 'pronoun') else 'they'} reminded {hero.id} that helping other people means taking enough time to do the job right."
    )


def repair_after_lesson(world: World, hero: Entity, tool: Tool, problem: Problem, helper: Helper, mode: HeroMode) -> None:
    hero.memes["pride"] = 0.0
    hero.memes["kindness"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{hero.id}'s cheeks grew warm, but {hero.pronoun()} nodded. This time {hero.pronoun()} listened."
    )
    repeat_method(world, hero, tool)
    world.say(problem.fix_text)
    world.say(
        f'The {helper.kind_word} patted {hero.id} on the shoulder. "That is superhero work," {helper.pronoun("subject") if hasattr(helper, "pronoun") else "they"} said.'
    )
    world.say(
        f'When the path stayed firm, {hero.id} learned that a helpful heart is stronger than a show-off shout, and {mode.close}.'
    )


def tell(
    mode: HeroMode,
    problem_cfg: Problem,
    tool_cfg: Tool,
    helper_cfg: Helper,
    *,
    hero_name: str = "Nia",
    hero_gender: str = "girl",
    helper_gender: str = "woman",
    valley_name: str = "Sunbeam Valley",
    hurry: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_gender,
        role="helper",
        label=helper_cfg.label,
        attrs={"kind_word": helper_cfg.kind_word, "advice": helper_cfg.advice},
    ))
    bridge = world.add(Entity(id="bridge", type="bridge", label="bridge"))
    problem = world.add(Entity(
        id="problem",
        type="problem",
        label=problem_cfg.label,
        role="problem",
        attrs={"place": problem_cfg.place},
        sturdy=False,
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        role="tool",
        can_secure=tool_cfg.can_secure,
    ))

    hero.meters["held"] = 0.0
    hero.meters["clamped"] = 0.0
    hero.meters["checked"] = 0.0
    bridge.meters["danger"] = 0.0
    problem.meters["loose"] = 0.0
    problem.meters["secure"] = 0.0
    world.facts["valley_name"] = valley_name

    introduce(world, hero, mode, valley_name)
    discover(world, hero, problem_cfg, helper_cfg, valley_name)

    world.para()
    boast(world, hero)
    warn(world, hero, helper_cfg, hurry)

    world.para()
    if hurry > MAX_HURRY or not success_possible(problem_cfg, tool_cfg, hurry):
        rush_method(world, hero, tool_cfg)
        fail_scene(world, hero, problem_cfg, helper)
        world.para()
        repeat_method(world, hero, tool_cfg)
        success_scene(world, hero, mode, problem_cfg, helper_cfg, valley_name)
        outcome = "learned"
    else:
        repeat_method(world, hero, tool_cfg)
        success_scene(world, hero, mode, problem_cfg, helper_cfg, valley_name)
        outcome = "careful"

    world.facts.update(
        hero=hero,
        helper=helper,
        mode=mode,
        tool_cfg=tool_cfg,
        problem_cfg=problem_cfg,
        helper_cfg=helper_cfg,
        tool=tool,
        problem=problem,
        bridge=bridge,
        hurry=hurry,
        outcome=outcome,
        moral="Helping carefully is more heroic than showing off.",
        repeated_words=["Hold", "clamp", "check"],
    )
    return world


HEROES = {
    "capelet": HeroMode(
        id="capelet",
        title="Captain Capelet",
        outfit="a bright red cape and silver boots",
        power_phrase="quick hands and a brave smile",
        landing="From the hill above the bridge, the cape snapped in the wind like a tiny flag",
        close="Captain Capelet did not feel biggest when the cape flew highest. Captain Capelet felt biggest when other people could walk safely home",
        tags={"superhero", "cape"},
    ),
    "glowguard": HeroMode(
        id="glowguard",
        title="Glow Guard",
        outfit="a shining blue scarf and a belt full of gadgets",
        power_phrase="clever tools and calm thinking",
        landing="When the morning sun touched the hills, the scarf gleamed like a strip of sky",
        close="Glow Guard raised one hand to the valley and watched everyone pass by with easy steps",
        tags={"superhero", "gadget"},
    ),
    "pebbleflash": HeroMode(
        id="pebbleflash",
        title="Pebble Flash",
        outfit="golden gloves and a small star badge",
        power_phrase="swift feet and a careful heart",
        landing="The badge winked in the light as if it knew a mission was coming",
        close="Pebble Flash laughed softly and kept watch until the last basket reached the market",
        tags={"superhero", "badge"},
    ),
}

PROBLEMS = {
    "rail": Problem(
        id="rail",
        label="bridge rail",
        the="the bridge rail",
        place="the old wooden bridge",
        needs_tool=True,
        risk_to="the children carrying berry baskets",
        severity=2,
        fix_text="The clamp bit down snugly, the rail stopped shaking, and the whole bridge gave a firm, safe little creak.",
        fail_text="The rail wobbled again with a clack, so nobody could cross yet.",
        flake_text="For one hopeful second the bridge seemed fixed. Then the loose rail gave a sly wiggle.",
        tags={"bridge", "safety"},
    ),
    "sign": Problem(
        id="sign",
        label="path sign",
        the="the path sign",
        place="the fork in the trail",
        needs_tool=True,
        risk_to="families heading to the goat meadow",
        severity=1,
        fix_text="The sign stood straight at last, pointing the right way instead of spinning in the breeze.",
        fail_text="The sign turned sideways again, which could still send walkers the wrong way.",
        flake_text="The sign held still for a blink, then slowly twisted back around.",
        tags={"sign", "safety"},
    ),
    "gate": Problem(
        id="gate",
        label="garden gate latch",
        the="the garden gate latch",
        place="the little market gate",
        needs_tool=True,
        risk_to="the market hens and everyone carrying vegetables",
        severity=2,
        fix_text="The latch clicked shut cleanly, and the gate stayed put instead of yawning open.",
        fail_text="The gate drifted open again, and that meant more trouble could spill onto the path.",
        flake_text="The gate seemed shut, but then it sagged and opened with a squeak.",
        tags={"gate", "safety"},
    ),
    "stone": Problem(
        id="stone",
        label="path stone",
        the="the path stone",
        place="the steep turn above the stream",
        needs_tool=False,
        risk_to="the feet of anyone hurrying downhill",
        severity=1,
        fix_text="The stone settled neatly back into the dirt and stopped rocking under every step.",
        fail_text="The stone still rocked in place, making the turn risky.",
        flake_text="The stone shifted back with a crunchy scrape.",
        tags={"path", "safety"},
    ),
}

TOOLS = {
    "clamp": Tool(
        id="clamp",
        label="clamp",
        phrase="the steel clamp",
        can_secure=True,
        care=3,
        action="pin the loose part tight",
        tags={"clamp", "tool"},
    ),
    "ribbon": Tool(
        id="ribbon",
        label="ribbon",
        phrase="a shiny ribbon",
        can_secure=False,
        care=1,
        action="wrap it in a pretty bow",
        tags={"ribbon"},
    ),
    "sticky_tape": Tool(
        id="sticky_tape",
        label="sticky tape",
        phrase="a roll of sticky tape",
        can_secure=False,
        care=1,
        action="press it down in a hurry",
        tags={"tape"},
    ),
    "rope_loop": Tool(
        id="rope_loop",
        label="rope loop",
        phrase="a sturdy rope loop",
        can_secure=True,
        care=2,
        action="pull the loose part snug and hold it while fastening",
        tags={"rope", "tool"},
    ),
}

HELPERS = {
    "baker": Helper(
        id="baker",
        label="Mrs. Palla",
        kind_word="baker",
        advice="Slow hands save fast walkers.",
        teaches_care=True,
        tags={"adult", "care"},
    ),
    "goatherd": Helper(
        id="goatherd",
        label="Mr. Tovin",
        kind_word="goatherd",
        advice="A hero checks twice.",
        teaches_care=True,
        tags={"adult", "care"},
    ),
    "gardener": Helper(
        id="gardener",
        label="Auntie Fern",
        kind_word="gardener",
        advice="Good help should hold strong and stay strong.",
        teaches_care=True,
        tags={"adult", "care"},
    ),
}

GIRL_NAMES = ["Nia", "Mira", "Ava", "Luma", "Tess", "Rina", "Pia", "Suri"]
BOY_NAMES = ["Kai", "Milo", "Theo", "Joss", "Eli", "Ren", "Finn", "Davi"]
TRAITS = ["brave", "eager", "kind", "quick", "helpful", "bright"]
VALLEYS = ["Sunbeam Valley", "Willow Valley", "Bluebell Valley", "Golden Valley"]


@dataclass
class StoryParams:
    hero: str
    problem: str
    tool: str
    helper: str
    name: str
    gender: str
    helper_gender: str
    valley_name: str
    hurry: int = 0
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "clamp": [(
        "What does a clamp do?",
        "A clamp holds things tightly in place so they do not wiggle apart. It is useful when something loose needs to stay still while you fix it."
    )],
    "bridge": [(
        "Why is a loose bridge rail dangerous?",
        "A loose bridge rail can wobble when people lean on it, and that can make crossing unsafe. Safe paths matter because many people depend on them."
    )],
    "safety": [(
        "Why should you check your work after fixing something?",
        "Checking your work helps you notice problems before someone gets hurt. Careful checking is one way to help other people."
    )],
    "superhero": [(
        "What makes someone a real superhero?",
        "A real superhero helps other people and chooses the safe, kind thing to do. Big costumes are fun, but good choices matter more."
    )],
    "care": [(
        "Why is helping carefully important?",
        "When you help carefully, the fix lasts and people can trust it. Rushing can leave the problem behind for someone else."
    )],
    "rope": [(
        "What can a rope loop be used for?",
        "A rope loop can pull something snug and hold it in place. It helps when you need strong, steady pulling."
    )],
}
KNOWLEDGE_ORDER = ["superhero", "clamp", "bridge", "safety", "care", "rope"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mode = f["mode"]
    problem_cfg = f["problem_cfg"]
    valley_name = f["valley_name"]
    return [
        f'Write a superhero story for a 3-to-5-year-old set in {valley_name} and include the word "valley" and the word "clamp".',
        f"Tell a story where {hero.id}, also called {mode.title}, finds that {problem_cfg.the} is loose and learns that careful help matters more than showing off.",
        'Write a short story that repeats the line "Hold, clamp, check" and ends with a clear moral about helping others carefully.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mode = f["mode"]
    problem_cfg = f["problem_cfg"]
    tool_cfg = f["tool_cfg"]
    valley_name = f["valley_name"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little hero called {mode.title}, in {valley_name}. It is also about {helper.label}, who helps {hero.id} remember how to do the job safely."
        ),
        (
            "What problem did the hero find?",
            f"{hero.id} found that {problem_cfg.the} at {problem_cfg.place} had come loose. That was dangerous because it could hurt {problem_cfg.risk_to}."
        ),
        (
            'What words did the hero repeat while fixing it?',
            f'{hero.id} repeated, "Hold, clamp, check." The repeated words helped {hero.pronoun("object")} slow down and do each part in the right order.'
        ),
    ]
    if outcome == "careful":
        qa.append((
            f"How did {hero.id} fix the problem?",
            f"{hero.id} used {tool_cfg.phrase} and followed each step carefully: hold, clamp, check. Because {hero.pronoun()} checked at the end, the path stayed safe for everyone crossing."
        ))
        qa.append((
            "What is the moral of the story?",
            f"The moral is that helping carefully is more heroic than showing off. {hero.id} solved the problem by being steady and kind, not by rushing."
        ))
    else:
        qa.append((
            f"Why did the first try fail?",
            f"The first try failed because {hero.id} hurried and skipped the last check. That left the problem unsafe, so {hero.pronoun()} had to listen and try again the careful way."
        ))
        qa.append((
            "What did the hero learn in the end?",
            f"{hero.id} learned that a superhero should help people carefully, even when {hero.pronoun()} wants to look fast and impressive. The second try worked because {hero.pronoun()} listened to the advice and checked the fix."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["mode"].tags) | set(f["problem_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["helper_cfg"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.can_secure:
            bits.append("can_secure=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="capelet",
        problem="rail",
        tool="clamp",
        helper="baker",
        name="Nia",
        gender="girl",
        helper_gender="woman",
        valley_name="Sunbeam Valley",
        hurry=0,
    ),
    StoryParams(
        hero="glowguard",
        problem="sign",
        tool="rope_loop",
        helper="goatherd",
        name="Kai",
        gender="boy",
        helper_gender="man",
        valley_name="Willow Valley",
        hurry=0,
    ),
    StoryParams(
        hero="pebbleflash",
        problem="gate",
        tool="clamp",
        helper="gardener",
        name="Mira",
        gender="girl",
        helper_gender="woman",
        valley_name="Bluebell Valley",
        hurry=2,
    ),
    StoryParams(
        hero="capelet",
        problem="stone",
        tool="clamp",
        helper="baker",
        name="Theo",
        gender="boy",
        helper_gender="woman",
        valley_name="Golden Valley",
        hurry=0,
    ),
]


def explain_rejection(problem: Problem, tool: Tool, hurry: int) -> str:
    if problem.needs_tool and not tool.can_secure:
        return (
            f"(No story: {tool.phrase} cannot truly secure {problem.the}. "
            f"Pick a real fastening tool like the clamp or the rope loop.)"
        )
    if tool.care < CARE_MIN:
        return (
            f"(No story: {tool.label} is too flimsy and careless for a safety repair. "
            f"This world only tells stories where the final fix can honestly work.)"
        )
    if hurry > MAX_HURRY:
        return (
            f"(No story: hurry={hurry} is too rushed for a dependable repair in this world. "
            f"Pick 0 or 1, or let the script choose.)"
        )
    return "(No story: this combination does not make a believable safety repair.)"


ASP_RULES = r"""
% reasonableness gate
valid(H,P,T) :- hero(H), problem(P), tool(T), not needs_tool_false(P), can_secure(T), careful(T).
valid(H,P,T) :- hero(H), problem(P), tool(T), needs_tool_false(P), careful(T).

needs_tool_false(P) :- problem(P), not needs_tool(P).

careful(T) :- tool(T), care(T,C), care_min(M), C >= M.

% scenario outcome
safe_fix :- chosen_problem(P), needs_tool(P), chosen_tool(T), can_secure(T), careful(T), hurry(H), max_hurry(M), H <= M.
safe_fix :- chosen_problem(P), needs_tool_false(P), chosen_tool(T), careful(T), hurry(H), max_hurry(M), H <= M.

outcome(careful) :- safe_fix.
outcome(learned) :- not safe_fix.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if problem.needs_tool:
            lines.append(asp.fact("needs_tool", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("care", tid, tool.care))
        if tool.can_secure:
            lines.append(asp.fact("can_secure", tid))
    lines.append(asp.fact("care_min", CARE_MIN))
    lines.append(asp.fact("max_hurry", MAX_HURRY))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_tool", params.tool),
        asp.fact("hurry", params.hurry),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("(No story: unknown problem or tool.)")
    return "careful" if success_possible(PROBLEMS[params.problem], TOOLS[params.tool], params.hurry) else "learned"


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

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a little superhero in a valley learns to fix things carefully."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--valley-name")
    ap.add_argument("--hurry", type=int, choices=[0, 1, 2])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        problem = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        hurry = args.hurry if args.hurry is not None else 0
        if not success_possible(problem, tool, hurry):
            raise StoryError(explain_rejection(problem, tool, hurry))

    combos = [
        c for c in valid_combos()
        if (args.hero is None or c[0] == args.hero)
        and (args.problem is None or c[1] == args.problem)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, problem_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    valley_name = args.valley_name or rng.choice(VALLEYS)
    hurry = args.hurry if args.hurry is not None else rng.choice([0, 0, 1, 2])
    return StoryParams(
        hero=hero_id,
        problem=problem_id,
        tool=tool_id,
        helper=helper_id,
        name=name,
        gender=gender,
        helper_gender=helper_gender,
        valley_name=valley_name,
        hurry=hurry,
    )


def _validate_params(params: StoryParams) -> None:
    if params.hero not in HEROES:
        raise StoryError("(No story: unknown hero mode.)")
    if params.problem not in PROBLEMS:
        raise StoryError("(No story: unknown problem.)")
    if params.tool not in TOOLS:
        raise StoryError("(No story: unknown tool.)")
    if params.helper not in HELPERS:
        raise StoryError("(No story: unknown helper.)")
    if not params.name:
        raise StoryError("(No story: hero needs a name.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("(No story: invalid hero gender.)")
    if params.helper_gender not in {"woman", "man"}:
        raise StoryError("(No story: invalid helper gender.)")
    if params.hurry not in {0, 1, 2}:
        raise StoryError("(No story: hurry must be 0, 1, or 2.)")


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        HEROES[params.hero],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        HELPERS[params.helper],
        hero_name=params.name,
        hero_gender=params.gender,
        helper_gender=params.helper_gender,
        valley_name=params.valley_name,
        hurry=params.hurry,
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
        print(f"{len(combos)} compatible (hero, problem, tool) combos:\n")
        for hero, problem, tool in combos:
            print(f"  {hero:11} {problem:8} {tool}")
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
            header = f"### {p.name}: {p.problem} in {p.valley_name} ({p.hero}, {p.tool}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
