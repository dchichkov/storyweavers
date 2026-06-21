#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/full_hominy_inner_monologue_transformation_superhero_story.py
========================================================================================

A standalone story world for a small superhero-flavored domain:

    a child at a neighborhood event eats a full bowl of hominy,
    notices a real problem,
    has a burst of inner monologue,
    transforms into a small local hero,
    and solves the problem with the right practical tool.

The world is constrained on purpose. Not every setting supports every mission,
and not every tool can honestly solve every problem. The story only generates
reasonable combinations and rejects explicit invalid requests with a clear
explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/full_hominy_inner_monologue_transformation_superhero_story.py
    python storyworlds/worlds/gpt-5.4/full_hominy_inner_monologue_transformation_superhero_story.py --setting block_party --mission wagon --tool chock
    python storyworlds/worlds/gpt-5.4/full_hominy_inner_monologue_transformation_superhero_story.py --mission banner --tool mitts
    python storyworlds/worlds/gpt-5.4/full_hominy_inner_monologue_transformation_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/full_hominy_inner_monologue_transformation_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/full_hominy_inner_monologue_transformation_superhero_story.py --json
    python storyworlds/worlds/gpt-5.4/full_hominy_inner_monologue_transformation_superhero_story.py --asp
    python storyworlds/worlds/gpt-5.4/full_hominy_inner_monologue_transformation_superhero_story.py --verify
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
from contextlib import redirect_stdout
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
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
class Setting:
    id: str
    place: str
    event: str
    afford_missions: set[str] = field(default_factory=set)
    opening: str = ""
    ending_image: str = ""
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
class Mission:
    id: str
    label: str
    alarm: str
    target: str
    problem_line: str
    solved_line: str
    tool_ids: set[str] = field(default_factory=set)
    difficulty: int = 1
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    handles: set[str] = field(default_factory=set)
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
class HeroForm:
    id: str
    title: str
    costume: str
    vow: str
    landing: str
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
class Meal:
    id: str
    dish: str
    phrase: str
    steam: str
    comfort: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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

    def note(self, key: str) -> None:
        self.history.append(key)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
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


def _r_alarm(world: World) -> list[str]:
    mission = world.get("mission")
    hero = world.get("hero")
    crowd = world.get("crowd")
    if mission.meters["active"] < THRESHOLD:
        return []
    sig = ("alarm", mission.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    crowd.memes["alarm"] += 1
    return []


def _r_full_to_energy(world: World) -> list[str]:
    hero = world.get("hero")
    bowl = world.get("meal")
    if bowl.meters["eaten"] < THRESHOLD:
        return []
    sig = ("energy", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["energy"] += 1
    hero.memes["comfort"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["transformed"] < THRESHOLD or hero.meters["energy"] < THRESHOLD:
        return []
    sig = ("transform", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    hero.memes["focus"] += 1
    return []


def _r_solve(world: World) -> list[str]:
    hero = world.get("hero")
    mission = world.get("mission")
    tool = world.get("tool")
    mentor = world.get("mentor")
    crowd = world.get("crowd")
    if mission.meters["active"] < THRESHOLD:
        return []
    if tool.meters["used"] < THRESHOLD:
        return []
    sig = ("solve", mission.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mission.meters["active"] = 0.0
    mission.meters["resolved"] += 1
    crowd.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.memes["worry"] = 0.0
    if mission.attrs.get("difficulty", 1) > 1:
        mentor.memes["teamwork"] += 1
        hero.memes["teamwork"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="alarm", tag="social", apply=_r_alarm),
    Rule(name="full_to_energy", tag="physical", apply=_r_full_to_energy),
    Rule(name="transform", tag="emotional", apply=_r_transform),
    Rule(name="solve", tag="physical", apply=_r_solve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for text in produced:
            world.say(text)
    return produced


SETTINGS = {
    "block_party": Setting(
        id="block_party",
        place="Maple Street",
        event="the neighborhood block party",
        afford_missions={"wagon", "banner"},
        opening="Paper stars swung from string over the sidewalk, and every table looked bright and busy.",
        ending_image="The string lights blinked on above the laughing neighbors.",
        tags={"party", "neighbors"},
    ),
    "school_fair": Setting(
        id="school_fair",
        place="the school yard",
        event="the school fair",
        afford_missions={"banner", "soup"},
        opening="Booths lined the fence, and the art table glowed with strips of red and gold paper.",
        ending_image="The last raffle ticket fluttered into a box as the crowd clapped.",
        tags={"school", "fair"},
    ),
    "garden_supper": Setting(
        id="garden_supper",
        place="the community garden",
        event="the garden supper",
        afford_missions={"soup", "wagon"},
        opening="Tomato vines curled around their stakes, and folding chairs made a little ring under the evening sky.",
        ending_image="Fireflies winked over the bean rows while everyone ate together.",
        tags={"garden", "supper"},
    ),
}

MISSIONS = {
    "wagon": Mission(
        id="wagon",
        label="runaway wagon",
        alarm='"The wagon is rolling!" somebody shouted.',
        target="the donation wagon",
        problem_line="A donation wagon had slipped free and was bumping toward the cake table.",
        solved_line="The wagon gave one last wobble and stopped before it could crash into the cakes.",
        tool_ids={"chock"},
        difficulty=2,
        tags={"wagon", "rolling", "help"},
    ),
    "banner": Mission(
        id="banner",
        label="snagged banner",
        alarm='"Our hero banner is stuck!" cried a child in a paper mask.',
        target="the superhero banner",
        problem_line="The big superhero banner had snapped loose and tangled itself high around a branch.",
        solved_line="The banner floated free, then sailed back down in one bright sheet of color.",
        tool_ids={"grabber"},
        difficulty=1,
        tags={"banner", "wind", "help"},
    ),
    "soup": Mission(
        id="soup",
        label="tipping soup pot",
        alarm='"The soup pot is sliding!" called the server.',
        target="the pot of soup",
        problem_line="A steaming pot of supper was tilting toward the table edge, close to a row of empty bowls.",
        solved_line="The pot settled safely in the middle of the table, and not one drop splashed onto the floor.",
        tool_ids={"mitts"},
        difficulty=2,
        tags={"soup", "hot", "help"},
    ),
}

TOOLS = {
    "chock": Tool(
        id="chock",
        label="wheel chock",
        phrase="a wedge-shaped wheel chock",
        action="slid the chock snug against the wagon wheel",
        handles={"wagon"},
        tags={"chock", "wagon"},
    ),
    "grabber": Tool(
        id="grabber",
        label="grabber pole",
        phrase="a long grabber pole",
        action="hooked the banner loop and tugged it free",
        handles={"banner"},
        tags={"grabber", "banner"},
    ),
    "mitts": Tool(
        id="mitts",
        label="oven mitts",
        phrase="thick oven mitts",
        action="gripped the hot handles and nudged the pot back to safety",
        handles={"soup"},
        tags={"mitts", "soup"},
    ),
}

HERO_FORMS = {
    "comet": HeroForm(
        id="comet",
        title="Comet Kid",
        costume="a shiny red cape made from a picnic cloth",
        vow="Fast hands, calm heart, help first.",
        landing="The cape snapped once behind {name}, and suddenly {name} stood taller.",
        tags={"cape", "hero"},
    ),
    "thunder": HeroForm(
        id="thunder",
        title="Thunder Spark",
        costume="a paper star mask and a blue scarf",
        vow="See the trouble. Fix the trouble.",
        landing="{name} pulled the mask into place and felt the whole world click into focus.",
        tags={"mask", "hero"},
    ),
    "lantern": HeroForm(
        id="lantern",
        title="Lantern Leaf",
        costume="a green apron tied like a brave little tunic",
        vow="Small hero, bright help.",
        landing="With the apron tied snug, {name} felt bright on the inside, like a lantern with fresh batteries.",
        tags={"apron", "hero"},
    ),
}

MEALS = {
    "hominy_bowl": Meal(
        id="hominy_bowl",
        dish="hominy stew",
        phrase="a full bowl of buttery hominy stew",
        steam="Soft steam curled up from the bowl and warmed {name}'s cheeks.",
        comfort="The warm spoonfuls settled in {name}'s middle and made the world feel steadier.",
        tags={"hominy", "meal"},
    ),
    "hominy_chili": Meal(
        id="hominy_chili",
        dish="hominy chili",
        phrase="a full bowl of hominy chili",
        steam="The bowl smelled savory and rich, and a puff of steam fogged the tip of {name}'s nose.",
        comfort="Each bite made {name}'s chest loosen a little, the way courage sometimes starts as warmth.",
        tags={"hominy", "meal"},
    ),
}

GIRL_NAMES = ["Lena", "Maya", "Zoe", "Ava", "Nora", "Ivy", "Rosa", "June"]
BOY_NAMES = ["Theo", "Miles", "Ben", "Eli", "Noah", "Finn", "Leo", "Owen"]
TRAITS = ["quiet", "observant", "gentle", "eager", "careful", "quick-thinking"]


def valid_combo(setting_id: str, mission_id: str, tool_id: str) -> bool:
    if setting_id not in SETTINGS or mission_id not in MISSIONS or tool_id not in TOOLS:
        return False
    setting = SETTINGS[setting_id]
    mission = MISSIONS[mission_id]
    tool = TOOLS[tool_id]
    return mission.id in setting.afford_missions and mission.id in tool.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for mission_id in sorted(setting.afford_missions):
            for tool_id, tool in TOOLS.items():
                if mission_id in tool.handles and mission_id in MISSIONS and mission_id in setting.afford_missions:
                    combos.append((setting_id, mission_id, tool_id))
    return sorted(combos)


def outcome_for_mission(mission_id: str) -> str:
    if mission_id not in MISSIONS:
        raise StoryError(f"(Unknown mission '{mission_id}'.)")
    return "team" if MISSIONS[mission_id].difficulty > 1 else "solo"


def explain_rejection(setting_id: str, mission_id: str, tool_id: str) -> str:
    if setting_id in SETTINGS and mission_id in MISSIONS:
        setting = SETTINGS[setting_id]
        mission = MISSIONS[mission_id]
        if mission_id not in setting.afford_missions:
            return (
                f"(No story: {setting.event} at {setting.place} does not naturally include "
                f"{mission.label}. Pick a mission that fits this setting.)"
            )
    if mission_id in MISSIONS and tool_id in TOOLS:
        mission = MISSIONS[mission_id]
        tool = TOOLS[tool_id]
        if mission_id not in tool.handles:
            choices = ", ".join(sorted(TOOLS[t].label for t in mission.tool_ids))
            return (
                f"(No story: {tool.label} does not solve {mission.label}. "
                f"Use {choices} instead.)"
            )
    return "(No valid combination matches the given options.)"


@dataclass
class StoryParams:
    setting: str
    mission: str
    tool: str
    hero_form: str
    meal: str
    name: str
    gender: str
    mentor: str
    trait: str
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


def meal_scene(world: World, hero: Entity, mentor: Entity, meal: Meal) -> None:
    bowl = world.get("meal")
    world.say(
        f"At {world.setting.event} on {world.setting.place}, {hero.id} sat beside "
        f"{hero.pronoun('possessive')} {mentor.label_word} with {meal.phrase}."
    )
    world.say(meal.steam.format(name=hero.id))
    bowl.meters["full"] = 1.0
    bowl.meters["eaten"] = 1.0
    propagate(world, narrate=False)
    world.say(meal.comfort.format(name=hero.id))
    world.say(world.setting.opening)
    world.note("meal")


def problem_appears(world: World, hero: Entity, mission_cfg: Mission) -> None:
    mission = world.get("mission")
    mission.meters["active"] = 1.0
    propagate(world, narrate=False)
    world.say(mission_cfg.problem_line)
    world.say(mission_cfg.alarm)
    world.note("problem")


def think_it_through(world: World, hero: Entity, mission_cfg: Mission, form: HeroForm) -> None:
    worry = "My knees feel wiggly" if hero.memes["worry"] >= THRESHOLD else "I can do this"
    fuel = "That warm hominy is still like a little sun inside me" if hero.meters["energy"] >= THRESHOLD else "I need a brave thought"
    world.say(
        f'{hero.id} felt {hero.pronoun("possessive")} heart bump once, hard. '
        f'"{worry}," {hero.pronoun()} thought. '
        f'"But heroes do not wait for perfect feelings. {fuel}."'
    )
    world.say(
        f'{hero.pronoun().capitalize()} looked at {mission_cfg.target} and made a quiet plan. '
        f'"I do not have to be huge," {hero.pronoun()} thought. '
        f'"I just have to help the next thing in front of me."'
    )
    world.facts["inner_monologue"] = True
    world.note("monologue")
    hero.attrs["vow"] = form.vow


def transform(world: World, hero: Entity, form: HeroForm) -> None:
    hero.meters["transformed"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} took {form.costume} from the supply chair and became {form.title}."
    )
    world.say(form.landing.format(name=hero.id))
    world.say(f'"{form.vow}" {hero.pronoun()} whispered to {hero.pronoun("object")}self.')
    world.note("transform")


def fetch_tool(world: World, hero: Entity, tool_cfg: Tool) -> None:
    world.say(
        f"{hero.id} darted to the helpers' table, grabbed {tool_cfg.phrase}, and ran back."
    )
    world.note("tool")


def solve(world: World, hero: Entity, mentor: Entity, mission_cfg: Mission, tool_cfg: Tool) -> None:
    tool = world.get("tool")
    mission = world.get("mission")
    if mission_cfg.difficulty > 1:
        world.say(
            f'"{mentor.label_word.capitalize()}, with me!" {hero.id} called.'
        )
        world.say(
            f"{mentor.label_word.capitalize()} moved beside {hero.pronoun('object')} at once, calm and fast."
        )
    else:
        world.say(
            f"{hero.id} planted {hero.pronoun('possessive')} feet like a comic-book hero and reached up."
        )
    tool.meters["used"] = 1.0
    propagate(world, narrate=False)
    world.say(f"{hero.id} {tool_cfg.action}.")
    world.say(mission_cfg.solved_line)
    world.note("solve")


def celebration(world: World, hero: Entity, mentor: Entity, mission_cfg: Mission, form: HeroForm) -> None:
    crowd = world.get("crowd")
    if mission_cfg.difficulty > 1:
        world.say(
            f"The grown-ups let out the breath they had been holding, and the children cheered for {form.title} and {mentor.label_word.capitalize()} together."
        )
    else:
        world.say(
            f"A round of cheers hopped across the crowd, and one little child pointed as if a real comic-book hero had landed."
        )
    if crowd.memes["relief"] >= THRESHOLD:
        world.say(
            f"{hero.id} suddenly felt lighter than before. The problem was gone, and the whole place seemed to stand up straighter."
        )
    world.say(
        f'{mentor.label_word.capitalize()} squeezed {hero.id}\'s shoulder. '
        f'"A hero notices, thinks, and helps," {mentor.pronoun()} said.'
    )
    world.say(
        f"{hero.id} looked down at the empty bowl, the borrowed costume, and the smiling neighbors. "
        f"{hero.pronoun().capitalize()} knew the transformation would not vanish when the costume came off."
    )
    world.say(world.setting.ending_image)
    world.note("ending")


def tell(
    setting: Setting,
    mission_cfg: Mission,
    tool_cfg: Tool,
    form: HeroForm,
    meal: Meal,
    *,
    name: str = "Lena",
    gender: str = "girl",
    mentor_type: str = "grandmother",
    trait: str = "observant",
) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        role="hero",
        traits=[trait],
        attrs={},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type=mentor_type,
        role="mentor",
        label="the mentor",
        attrs={},
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="character",
        type="group",
        role="crowd",
        label="the crowd",
        attrs={},
    ))
    bowl = world.add(Entity(
        id="meal",
        kind="thing",
        type="bowl",
        label=meal.dish,
        role="meal",
        attrs={},
    ))
    mission = world.add(Entity(
        id="mission",
        kind="thing",
        type="mission",
        label=mission_cfg.label,
        role="mission",
        attrs={"difficulty": mission_cfg.difficulty},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        role="tool",
        attrs={},
    ))

    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 0.0
    hero.memes["focus"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["comfort"] = 0.0
    crowd.memes["alarm"] = 0.0
    crowd.memes["relief"] = 0.0
    mentor.memes["teamwork"] = 0.0
    hero.memes["teamwork"] = 0.0
    bowl.meters["full"] = 0.0
    bowl.meters["eaten"] = 0.0
    hero.meters["energy"] = 0.0
    hero.meters["transformed"] = 0.0
    mission.meters["active"] = 0.0
    mission.meters["resolved"] = 0.0
    tool.meters["used"] = 0.0

    world.facts.update(
        setting=setting,
        mission_cfg=mission_cfg,
        tool_cfg=tool_cfg,
        form=form,
        meal_cfg=meal,
        hero=hero,
        mentor=mentor,
        crowd=crowd,
        mission=mission,
        tool=tool,
        outcome=outcome_for_mission(mission_cfg.id),
        inner_monologue=False,
    )

    meal_scene(world, hero, mentor, meal)
    world.para()
    problem_appears(world, hero, mission_cfg)
    think_it_through(world, hero, mission_cfg, form)
    world.para()
    transform(world, hero, form)
    fetch_tool(world, hero, tool_cfg)
    solve(world, hero, mentor, mission_cfg, tool_cfg)
    world.para()
    celebration(world, hero, mentor, mission_cfg, form)

    world.facts.update(
        resolved=mission.meters["resolved"] >= THRESHOLD,
        teamwork=mentor.memes["teamwork"] >= THRESHOLD,
        transformed=hero.meters["transformed"] >= THRESHOLD,
        courage=hero.memes["courage"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "hominy": [
        (
            "What is hominy?",
            "Hominy is corn that has been specially prepared until the kernels get soft and puffy. People often eat it in soups, stews, or warm bowls.",
        )
    ],
    "cape": [
        (
            "What is a cape?",
            "A cape is a cloth that hangs from the shoulders or neck. In superhero stories it often shows a bold hero style, even though real helping comes from choices and actions.",
        )
    ],
    "mask": [
        (
            "Why do superheroes wear masks in stories?",
            "In stories, a mask can help a character feel brave and ready for a mission. The mask does not make the hero good; the hero's choices do that.",
        )
    ],
    "wagon": [
        (
            "Why can a wagon be dangerous if it starts rolling?",
            "A rolling wagon can bump into people or tables if nobody stops it. That is why it helps to block the wheel quickly and keep everyone back.",
        )
    ],
    "banner": [
        (
            "Why would a banner get stuck in a tree or on a branch?",
            "Wind can twist light cloth and string around high places. Once it catches, someone needs a safe way to reach and free it.",
        )
    ],
    "soup": [
        (
            "Why should you be careful around a hot soup pot?",
            "A hot pot can spill and burn skin if it tips or slides. Grown-ups and helpers use care, steady hands, and the right protection around hot food.",
        )
    ],
    "grabber": [
        (
            "What is a grabber pole for?",
            "A grabber pole helps you reach something that is high or far away without climbing. It gives you extra reach while you stay on the ground.",
        )
    ],
    "mitts": [
        (
            "What do oven mitts do?",
            "Oven mitts help protect hands from heat when someone moves a hot dish or pot. They do not make something cold, but they make careful handling safer.",
        )
    ],
    "chock": [
        (
            "What does a wheel chock do?",
            "A wheel chock is a wedge that presses against a wheel so it cannot keep rolling. It helps hold carts and wagons still.",
        )
    ],
    "hero": [
        (
            "What makes someone a hero?",
            "A hero notices trouble and chooses to help, even while feeling nervous. Being brave does not mean having no fear; it means doing the helpful thing anyway.",
        )
    ],
}
KNOWLEDGE_ORDER = ["hominy", "wagon", "banner", "soup", "grabber", "mitts", "chock", "cape", "mask", "hero"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission_cfg = f["mission_cfg"]
    form = f["form"]
    setting = f["setting"]
    meal = f["meal_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "full" and "hominy" and features a child\'s inner monologue.',
        f"Tell a neighborhood superhero story where {hero.id} eats {meal.phrase}, notices a problem at {setting.event}, and transforms into {form.title} to help.",
        f"Write a gentle transformation story in which a small hero solves a {mission_cfg.label} problem with the right tool and learns that helping is the real superpower.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    mission_cfg = f["mission_cfg"]
    tool_cfg = f["tool_cfg"]
    form = f["form"]
    meal = f["meal_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who becomes {form.title} for one important moment, and {hero.pronoun('possessive')} {mentor.label_word} who stays close by. The story shows how a small person can become brave through helping.",
        ),
        (
            f"What was {hero.id} eating at the beginning?",
            f"{hero.id} was eating {meal.phrase}. The warm bowl helped {hero.pronoun('object')} feel steady before the trouble began.",
        ),
        (
            "What problem happened?",
            f"{mission_cfg.problem_line} People got worried because the problem could have made a mess or caused someone to get hurt.",
        ),
        (
            f"What did {hero.id} think to {hero.pronoun('object')}self?",
            f'{hero.id} admitted that {hero.pronoun("possessive")} body felt nervous, then reminded {hero.pronoun("object")}self that heroes help the next thing in front of them. That inner monologue matters because it turns worry into a plan.',
        ),
        (
            f"How did the transformation happen?",
            f"{hero.id} put on {form.costume} and became {form.title}. The costume did not do the helping by itself; it gave {hero.pronoun('object')} a brave shape for the courage already growing inside.",
        ),
        (
            f"How was the problem solved?",
            f"{hero.id} used {tool_cfg.phrase} and {tool_cfg.action}. That worked because {tool_cfg.label} was the right tool for this exact problem.",
        ),
    ]
    if outcome == "team":
        qa.append(
            (
                f"Did {hero.id} solve it alone?",
                f"No. {hero.id} called {mentor.label_word.capitalize()} in for the hard part, and they worked together. The story makes the teamwork important because asking for help is also heroic.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} need help at the end?",
                f"{hero.id} solved this one mostly alone while {mentor.label_word} watched nearby. That worked because the problem needed reach and calm more than heavy lifting.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the neighbors cheering and the whole event feeling safe again. {hero.id} learned that the real transformation was not only the costume, but the choice to notice, think, and help.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"hero"}
    tags |= set(f["meal_cfg"].tags)
    tags |= set(f["mission_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
    tags |= set(f["form"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% a setting supports a mission if it affords it
supports(S, M) :- affords(S, M).

% a tool is suitable if it handles that mission
suitable(M, T) :- handles(T, M).

valid(S, M, T) :- supports(S, M), suitable(M, T).

outcome(M, team) :- mission(M), difficulty(M, D), D > 1.
outcome(M, solo) :- mission(M), difficulty(M, D), D <= 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for mission_id in sorted(setting.afford_missions):
            lines.append(asp.fact("affords", setting_id, mission_id))
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        lines.append(asp.fact("difficulty", mission_id, mission.difficulty))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for mission_id in sorted(tool.handles):
            lines.append(asp.fact("handles", tool_id, mission_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(mission_id: str) -> str:
    import asp

    program = asp_program("", f"#show outcome/2.")
    model = asp.one_model(program)
    pairs = {m: out for (m, out) in asp.atoms(model, "outcome")}
    return pairs.get(mission_id, "?")


CURATED = [
    StoryParams(
        setting="block_party",
        mission="wagon",
        tool="chock",
        hero_form="comet",
        meal="hominy_bowl",
        name="Maya",
        gender="girl",
        mentor="grandmother",
        trait="quick-thinking",
        seed=None,
    ),
    StoryParams(
        setting="school_fair",
        mission="banner",
        tool="grabber",
        hero_form="thunder",
        meal="hominy_chili",
        name="Theo",
        gender="boy",
        mentor="father",
        trait="observant",
        seed=None,
    ),
    StoryParams(
        setting="garden_supper",
        mission="soup",
        tool="mitts",
        hero_form="lantern",
        meal="hominy_bowl",
        name="Rosa",
        gender="girl",
        mentor="grandmother",
        trait="gentle",
        seed=None,
    ),
    StoryParams(
        setting="school_fair",
        mission="soup",
        tool="mitts",
        hero_form="comet",
        meal="hominy_chili",
        name="Ben",
        gender="boy",
        mentor="mother",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        setting="garden_supper",
        mission="wagon",
        tool="chock",
        hero_form="thunder",
        meal="hominy_bowl",
        name="June",
        gender="girl",
        mentor="grandfather",
        trait="eager",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child with a full bowl of hominy becomes a neighborhood superhero."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-form", choices=HERO_FORMS)
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (setting, mission, tool) combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mission and args.tool and not valid_combo(args.setting, args.mission, args.tool):
        raise StoryError(explain_rejection(args.setting, args.mission, args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mission is None or combo[1] == args.mission)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mission_id, tool_id = rng.choice(combos)
    hero_form = args.hero_form or rng.choice(sorted(HERO_FORMS))
    meal = args.meal or rng.choice(sorted(MEALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = args.mentor or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        mission=mission_id,
        tool=tool_id,
        hero_form=hero_form,
        meal=meal,
        name=name,
        gender=gender,
        mentor=mentor,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission '{params.mission}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool '{params.tool}'.)")
    if params.hero_form not in HERO_FORMS:
        raise StoryError(f"(Unknown hero form '{params.hero_form}'.)")
    if params.meal not in MEALS:
        raise StoryError(f"(Unknown meal '{params.meal}'.)")
    if not valid_combo(params.setting, params.mission, params.tool):
        raise StoryError(explain_rejection(params.setting, params.mission, params.tool))

    world = tell(
        SETTINGS[params.setting],
        MISSIONS[params.mission],
        TOOLS[params.tool],
        HERO_FORMS[params.hero_form],
        MEALS[params.meal],
        name=params.name,
        gender=params.gender,
        mentor_type=params.mentor,
        trait=params.trait,
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

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos() matches ASP ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    bad_outcomes = []
    for mission_id in sorted(MISSIONS):
        py_out = outcome_for_mission(mission_id)
        asp_out = asp_outcome(mission_id)
        if py_out != asp_out:
            bad_outcomes.append((mission_id, py_out, asp_out))
    if not bad_outcomes:
        print(f"OK: mission outcomes match ASP ({len(MISSIONS)} missions).")
    else:
        rc = 1
        print("MISMATCH in mission outcomes:")
        for row in bad_outcomes:
            print("  ", row)

    try:
        params = CURATED[0]
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        random_params = resolve_params(args, random.Random(17))
        random_params.seed = 17
        sample = generate(random_params)
        if not sample.story.strip():
            raise StoryError("Random story was empty.")
        print("OK: default-style seeded generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, mission, tool) combos:\n")
        for setting_id, mission_id, tool_id in combos:
            print(f"  {setting_id:13} {mission_id:8} {tool_id}")
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
            header = (
                f"### {p.name}: {p.setting}, {p.mission}, {p.tool} "
                f"({outcome_for_mission(p.mission)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
