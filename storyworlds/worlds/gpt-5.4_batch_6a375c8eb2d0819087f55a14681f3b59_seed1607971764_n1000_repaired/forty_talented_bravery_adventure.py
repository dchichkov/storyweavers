#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/forty_talented_bravery_adventure.py
==============================================================

A standalone story world for a tiny child-facing adventure tale: two children
set out on a make-believe expedition to recover a lost trail flag before the
neighborhood treasure walk begins. Inside the flag tube are forty shiny star
stickers for the finishers, so the mission matters to them in a concrete way.

This world models a simple, state-driven adventure:
- a brave-but-hesitant child wants to reach the far side of a small obstacle
- a talented friend or sibling has a specific useful skill
- the pair either choose the right tool for the obstacle and cross safely, or
  realize the mismatch and turn back for help instead

The reasonableness gate is physical:
- each obstacle demands a certain kind of crossing support
- each tool supports some obstacle types
- each helper skill can make one kind of tool safe to use
- the story refuses unreasonable combinations

Run it
------
    python storyworlds/worlds/gpt-5.4/forty_talented_bravery_adventure.py
    python storyworlds/worlds/gpt-5.4/forty_talented_bravery_adventure.py --obstacle creek --tool rope
    python storyworlds/worlds/gpt-5.4/forty_talented_bravery_adventure.py --obstacle ravine --tool stepping_stones
    python storyworlds/worlds/gpt-5.4/forty_talented_bravery_adventure.py --all
    python storyworlds/worlds/gpt-5.4/forty_talented_bravery_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/forty_talented_bravery_adventure.py --trace
    python storyworlds/worlds/gpt-5.4/forty_talented_bravery_adventure.py --json
    python storyworlds/worlds/gpt-5.4/forty_talented_bravery_adventure.py --verify
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
BRAVERY_BASE = 4.0
BRAVERY_NEED = 5.0
CAREFUL_TRAITS = {"steady", "patient", "thoughtful", "careful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Setting:
    id: str
    place: str
    trail: str
    landmark: str
    sky: str
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
class Obstacle:
    id: str
    label: str
    phrase: str
    trouble: str
    crossing_need: str
    danger: str
    far_side: str
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
    supports: set[str] = field(default_factory=set)
    with_skill: str = ""
    action: str = ""
    ending_image: str = ""
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
class Skill:
    id: str
    adjective: str
    label: str
    steadies: set[str] = field(default_factory=set)
    boast: str = ""
    method: str = ""
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
class Prize:
    id: str
    label: str
    phrase: str
    count: int
    purpose: str
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


def _r_shaky(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    helper = world.get("helper")
    if obstacle.meters["blocked"] < THRESHOLD:
        return out
    if hero.meters["attempt_cross"] < THRESHOLD:
        return out
    if tool.attrs.get("supports") == obstacle.attrs.get("need") and tool.attrs.get("safe"):
        return out
    sig = ("shaky", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    obstacle.meters["risk"] += 1
    helper.memes["care"] += 1
    world.history.append("crossing_looked_shaky")
    out.append("__shaky__")
    return out


def _r_success(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    helper = world.get("helper")
    if obstacle.meters["blocked"] < THRESHOLD:
        return out
    if hero.meters["attempt_cross"] < THRESHOLD:
        return out
    if not (tool.attrs.get("supports") == obstacle.attrs.get("need") and tool.attrs.get("safe")):
        return out
    sig = ("success", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obstacle.meters["blocked"] = 0.0
    hero.meters["across"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["bravery"] += 1
    helper.memes["pride"] += 1
    world.history.append("crossed_safely")
    out.append("__success__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="shaky", tag="physical", apply=_r_shaky),
    Rule(name="success", tag="physical", apply=_r_success),
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


def tool_fits(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.crossing_need in tool.supports


def skill_helps(tool: Tool, skill: Skill) -> bool:
    return tool.id in skill.steadies


def valid_combo(obstacle: Obstacle, tool: Tool, skill: Skill) -> bool:
    return tool_fits(obstacle, tool) and skill_helps(tool, skill)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for oid, obstacle in OBSTACLES.items():
            for tid, tool in TOOLS.items():
                for kid, skill in SKILLS.items():
                    if valid_combo(obstacle, tool, skill):
                        combos.append((sid, oid, tid, kid))
    return combos


def bravery_boost(trait: str, relation: str) -> float:
    bonus = 1.0 if trait in CAREFUL_TRAITS else 0.0
    if relation == "siblings":
        bonus += 1.0
    return bonus


def brave_enough(trait: str, relation: str) -> bool:
    return BRAVERY_BASE + bravery_boost(trait, relation) >= BRAVERY_NEED


def predict_crossing(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["attempt_cross"] += 1
    propagate(sim, narrate=False)
    return {
        "safe": hero.meters["across"] >= THRESHOLD,
        "risk": sim.get("obstacle").meters["risk"],
        "fear": hero.memes["fear"],
    }


def introduce(world: World, hero: Entity, helper: Entity, prize: Prize) -> None:
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On {world.setting.sky}, {hero.id} and {helper.id} followed {world.setting.trail} at "
        f"{world.setting.place}. They were hunting for a bright flag tube that held "
        f"{prize.count} star stickers for {prize.purpose}."
    )
    world.say(
        f"{hero.id} felt as if the whole morning was an adventure. {helper.id} was a "
        f"{helper.attrs['skill_adj']} and talented trail partner who noticed the useful things first."
    )


def spot_problem(world: World, hero: Entity, obstacle: Obstacle, prize: Prize) -> None:
    world.get("obstacle").meters["blocked"] = 1.0
    world.say(
        f"At last they saw the flag tube {obstacle.far_side}. But {obstacle.phrase} lay in the way, "
        f"and {obstacle.trouble}."
    )
    world.say(
        f"If they could not get across, the children at the finish would have no stickers at all. "
        f"The little tube with its forty stars suddenly felt very far away."
    )
    hero.memes["worry"] += 1


def choose_tool(world: World, hero: Entity, helper: Entity, tool: Tool, skill: Skill) -> None:
    tool_ent = world.get("tool")
    tool_ent.attrs["safe"] = skill_helps(tool, skill) and tool_fits(OBSTACLES[world.facts["obstacle_cfg"].id], tool)
    world.say(
        f'{hero.id} pointed at {tool.phrase}. "{tool.action.capitalize()}," {hero.pronoun()} whispered.'
    )
    world.say(
        f'{helper.id} nodded. "{skill.boast}"'
    )


def warning(world: World, hero: Entity, helper: Entity, obstacle: Obstacle, tool: Tool) -> None:
    pred = predict_crossing(world)
    world.facts["predicted_safe"] = pred["safe"]
    world.facts["predicted_risk"] = pred["risk"]
    if pred["safe"]:
        world.say(
            f"{helper.id} tested the way with careful eyes. It looked possible, but only if they moved slowly and stayed steady together."
        )
    else:
        world.say(
            f"{helper.id} looked once, then twice, and shook {helper.pronoun('possessive')} head. "
            f'"That would be too shaky. {obstacle.danger} with {tool.label} like this."'
        )
    helper.memes["care"] += 1
    hero.memes["fear"] += float(pred["risk"])


def attempt(world: World, hero: Entity, relation: str) -> None:
    hero.meters["attempt_cross"] += 1
    hero.memes["bravery"] += BRAVERY_BASE + bravery_boost(hero.attrs["trait"], relation)
    world.say(
        f"{hero.id} drew in a long breath. {hero.pronoun().capitalize()} was scared, but bravery did not make the fear disappear; it helped {hero.pronoun('object')} take one careful step anyway."
    )
    propagate(world, narrate=False)


def succeed(world: World, hero: Entity, helper: Entity, obstacle: Obstacle, tool: Tool, skill: Skill, prize: Prize) -> None:
    world.history.append("helper_guided_crossing")
    world.say(
        f"{helper.id} {skill.method} while {hero.id} used {tool.phrase}. Together they crossed {obstacle.label} without slipping."
    )
    world.say(
        f"On the far side, {hero.id} scooped up the flag tube and held it high. Inside, the forty star stickers rattled like tiny treasure."
    )
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.facts["outcome"] = "crossed"
    world.facts["retrieved"] = True
    world.facts["called_adult"] = False
    world.facts["ending_image"] = tool.ending_image


def turn_back(world: World, hero: Entity, helper: Entity, obstacle: Obstacle, prize: Prize, adult: Entity) -> None:
    hero.memes["bravery"] += 1
    hero.memes["fear"] = 0.0
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} stopped at the edge instead of rushing on. That was brave too. {hero.pronoun().capitalize()} listened when the path stopped making sense."
    )
    world.say(
        f'Together they hurried back to {adult.label_word}, explained about {obstacle.label}, and asked for help. '
        f'Soon the grown-up brought the safe bridge board from the shed and fetched the flag tube for them.'
    )
    world.say(
        f"When they opened it, all forty star stickers were still dry and shining. The adventure ended with help, not hurt, and that made the prize feel even better."
    )
    world.facts["outcome"] = "helped"
    world.facts["retrieved"] = True
    world.facts["called_adult"] = True
    world.facts["ending_image"] = "the stickers gleaming safely in the grown-up's hands"


def celebrate(world: World, hero: Entity, helper: Entity, prize: Prize) -> None:
    hero.memes["joy"] += 1
    helper.memes["pride"] += 1
    relation_word = "team" if world.facts["relation"] == "friends" else "pair"
    world.say(
        f"By the time the treasure walk began, the brave {relation_word} had the flag ready again. The children lined up, and the forty stickers shone in the sun like a row of little rewards."
    )


def tell(setting: Setting, obstacle: Obstacle, tool: Tool, skill: Skill, prize: Prize,
         hero_name: str = "Mira", hero_gender: str = "girl",
         helper_name: str = "Finn", helper_gender: str = "boy",
         relation: str = "friends", trait: str = "careful",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["eager", trait],
        attrs={"trait": trait, "relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[skill.adjective],
        attrs={"skill": skill.id, "skill_adj": skill.adjective, "relation": relation},
    ))
    adult = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="adult",
        label="the parent",
    ))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=obstacle.label,
        attrs={"need": obstacle.crossing_need},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        attrs={"supports": next(iter(sorted(tool.supports))) if tool.supports else "", "safe": False},
    ))
    prize_ent = world.add(Entity(
        id="prize",
        type="prize",
        label=prize.label,
    ))

    hero.memes["bravery"] = BRAVERY_BASE
    hero.memes["fear"] = 0.0
    helper.memes["care"] = 0.0
    obstacle_ent.meters["risk"] = 0.0
    obstacle_ent.meters["blocked"] = 0.0
    tool_ent.meters["ready"] = 1.0
    prize_ent.meters["safe"] = 1.0

    world.facts.update(
        setting=setting,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        skill_cfg=skill,
        prize_cfg=prize,
        hero=hero,
        helper=helper,
        adult=adult,
        relation=relation,
        retrieved=False,
        predicted_safe=False,
        predicted_risk=0.0,
        outcome="",
        called_adult=False,
    )

    introduce(world, hero, helper, prize)
    spot_problem(world, hero, obstacle, prize)

    world.para()
    choose_tool(world, hero, helper, tool, skill)
    warning(world, hero, helper, obstacle, tool)

    world.para()
    if valid_combo(obstacle, tool, skill) and brave_enough(trait, relation):
        attempt(world, hero, relation)
        succeed(world, hero, helper, obstacle, tool, skill, prize)
    else:
        turn_back(world, hero, helper, obstacle, prize, adult)

    world.para()
    celebrate(world, hero, helper, prize)
    return world


SETTINGS = {
    "pine_hollow": Setting(
        id="pine_hollow",
        place="Pine Hollow Park",
        trail="the needle-soft path",
        landmark="old pines",
        sky="a bright blue sky",
        tags={"park", "woods"},
    ),
    "sunny_bank": Setting(
        id="sunny_bank",
        place="Sunny Bank Trail",
        trail="the winding dirt path",
        landmark="tall grass",
        sky="a windy golden afternoon",
        tags={"trail", "field"},
    ),
    "fern_glen": Setting(
        id="fern_glen",
        place="Fern Glen",
        trail="the mossy path",
        landmark="ferns and stones",
        sky="a cool green morning",
        tags={"glen", "woods"},
    ),
}

OBSTACLES = {
    "creek": Obstacle(
        id="creek",
        label="the creek",
        phrase="a narrow creek with cold water flashing over stones",
        trouble="the stepping places were far apart",
        crossing_need="steps",
        danger="One wrong jump and they would splash straight into the cold water",
        far_side="on the opposite bank beside a stump",
        tags={"water", "creek"},
    ),
    "ravine": Obstacle(
        id="ravine",
        label="the ravine",
        phrase="a small ravine with a sharp, leafy drop",
        trouble="the ground crumbled at the edge",
        crossing_need="bridge",
        danger="A bad wobble there would mean a tumble into the leaves below",
        far_side="on a flat rock beyond the gap",
        tags={"gap", "heights"},
    ),
    "slope": Obstacle(
        id="slope",
        label="the muddy slope",
        phrase="a muddy slope that slid down to the lower path",
        trouble="boots could skid if they hurried",
        crossing_need="support",
        danger="If they rushed, they could slide all the way to the bottom",
        far_side="hooked on a branch halfway up the bank",
        tags={"mud", "hill"},
    ),
}

TOOLS = {
    "stepping_stones": Tool(
        id="stepping_stones",
        label="stepping stones",
        phrase="the stepping stones",
        supports={"steps"},
        with_skill="balance",
        action="we can try the stones",
        ending_image="the two children hopping back with the flag tube",
        tags={"stones", "balance"},
    ),
    "rope": Tool(
        id="rope",
        label="a rope",
        phrase="a rope tied low and tight",
        supports={"support"},
        with_skill="knots",
        action="we can use the rope",
        ending_image="the rope humming in the wind while the children grin on the far side",
        tags={"rope", "knots"},
    ),
    "plank": Tool(
        id="plank",
        label="a plank",
        phrase="a sturdy plank",
        supports={"bridge"},
        with_skill="planning",
        action="we can lay the plank across",
        ending_image="the plank resting steady while the recovered tube gleams",
        tags={"plank", "bridge"},
    ),
    "vine": Tool(
        id="vine",
        label="a vine",
        phrase="a hanging vine",
        supports={"support"},
        with_skill="balance",
        action="maybe the vine will help",
        ending_image="the vine swinging quietly after the children pass",
        tags={"vine", "swing"},
    ),
}

SKILLS = {
    "balance": Skill(
        id="balance",
        adjective="steady",
        label="balancing",
        steadies={"stepping_stones", "vine"},
        boast="I'm talented at keeping my feet steady. Hold your arms out like mine.",
        method="went first, showing each slow step",
        tags={"balance"},
    ),
    "knots": Skill(
        id="knots",
        adjective="knot-tying",
        label="tying knots",
        steadies={"rope"},
        boast="I'm talented with knots. I can make the rope stay where we need it.",
        method="looped the rope around a root and pulled it snug",
        tags={"rope", "knots"},
    ),
    "planning": Skill(
        id="planning",
        adjective="thoughtful",
        label="planning",
        steadies={"plank"},
        boast="I'm talented at planning safe ways across. Let's place it flat before we step.",
        method="tested the plank twice and set it down where the ground was firmest",
        tags={"planning"},
    ),
}

PRIZES = {
    "flag_tube": Prize(
        id="flag_tube",
        label="flag tube",
        phrase="a bright red flag tube",
        count=40,
        purpose="the children who finished the treasure walk",
        tags={"stickers", "treasure"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    tool: str
    skill: str
    prize: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    relation: str
    trait: str
    parent: str
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
    "creek": [
        (
            "Why can a creek be tricky to cross?",
            "A creek can be slippery because water runs over rocks and mud. Even a small creek needs careful feet."
        )
    ],
    "ravine": [
        (
            "What is a ravine?",
            "A ravine is a small deep gap in the ground. The sides can be steep, so people should not jump across it carelessly."
        )
    ],
    "slope": [
        (
            "Why is a muddy slope slippery?",
            "Mud is slick under shoes. When the ground is muddy, feet can slide instead of gripping the dirt."
        )
    ],
    "stones": [
        (
            "What are stepping stones for?",
            "Stepping stones give your feet places to land above the water or mud. They help when the safe way is one careful step at a time."
        )
    ],
    "rope": [
        (
            "How can a rope help on a trail?",
            "A rope can give your hands something steady to hold. It only helps if it is tied well and used carefully."
        )
    ],
    "plank": [
        (
            "What does a plank do in a crossing?",
            "A plank can make a flat bridge over a small gap. It works best when someone places it on firm ground."
        )
    ],
    "knots": [
        (
            "Why are good knots useful?",
            "Good knots keep a rope from slipping loose. That makes a rope much safer to trust."
        )
    ],
    "balance": [
        (
            "What does balance mean?",
            "Balance means keeping your body steady so you do not tip or fall. Slow steps and open arms can help."
        )
    ],
    "planning": [
        (
            "Why is planning part of bravery?",
            "Planning helps you choose a safe way before you act. Brave choices are better when they are thoughtful choices."
        )
    ],
    "help": [
        (
            "Is it brave to ask a grown-up for help?",
            "Yes. Asking for help can be very brave because it means you care more about safety than about showing off."
        )
    ],
    "stickers": [
        (
            "Why would forty stickers matter in a game?",
            "Forty stickers can be enough for many children to share a prize. In a treasure walk, a small reward can make the finish feel special."
        )
    ],
}
KNOWLEDGE_ORDER = ["creek", "ravine", "slope", "stones", "rope", "plank", "knots", "balance", "planning", "help", "stickers"]

GIRL_NAMES = ["Mira", "Lina", "Ava", "Nora", "Zoe", "Maya", "Iris", "Ella"]
BOY_NAMES = ["Finn", "Leo", "Max", "Toby", "Eli", "Noah", "Jack", "Owen"]
TRAITS = ["careful", "steady", "thoughtful", "eager", "curious"]


def explain_rejection(obstacle: Obstacle, tool: Tool, skill: Skill) -> str:
    if not tool_fits(obstacle, tool):
        return (
            f"(No story: {tool.label} is not a sensible way across {obstacle.label}. "
            f"{obstacle.label.capitalize()} needs {obstacle.crossing_need}, so choose a tool that truly fits the obstacle.)"
        )
    if not skill_helps(tool, skill):
        return (
            f"(No story: the helper's skill is {skill.label}, but that does not make {tool.label} safe to use. "
            f"Choose a skill that really supports the chosen tool.)"
        )
    return "(No story: this adventure setup is unreasonable.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obstacle = f["obstacle_cfg"]
    prize = f["prize_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    if outcome == "crossed":
        return [
            f'Write an adventure story for a young child where {hero.id} shows bravery to cross {obstacle.label} and recover a prize holding forty stars.',
            f"Tell a gentle adventure about a talented helper and a brave child using {tool.label} the safe way.",
            f'Write a story that includes the words "forty" and "talented" and ends with a recovered treasure for other children.'
        ]
    return [
        f'Write an adventure story for a young child where {hero.id} wants to cross {obstacle.label} for a prize with forty stars but chooses help instead of danger.',
        f"Tell a story where {helper.id} is talented enough to notice a bad plan and the children act bravely by turning back.",
        f'Write a story that includes the words "forty" and "talented" and shows that asking for help can be part of bravery.'
    ]


def relation_phrase(relation: str) -> str:
    return "friends" if relation == "friends" else "siblings"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    adult = f["adult"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    skill = f["skill_cfg"]
    prize = f["prize_cfg"]
    relation = relation_phrase(f["relation"])
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {relation}, {hero.id} and {helper.id}, on a small adventure trail. They wanted to recover a red tube holding forty star stickers."
        ),
        (
            "Why did the children care about the tube?",
            f"They cared because the tube held forty star stickers for the children finishing the treasure walk. Losing it would disappoint everyone waiting at the end."
        ),
        (
            f"What problem stood in {hero.id}'s way?",
            f"{obstacle.label.capitalize()} blocked the path to the tube. It was dangerous because {obstacle.danger.lower()}."
        ),
        (
            f"Why was {helper.id} described as talented?",
            f"{helper.id} was talented at {skill.label}, which mattered on the trail. That skill helped {helper.pronoun('object')} judge whether the crossing plan was safe."
        ),
    ]
    if outcome == "crossed":
        qa.append(
            (
                f"How did {hero.id} show bravery?",
                f"{hero.id} felt scared but still took careful steps instead of rushing. {helper.id}'s skill with {tool.label} made the crossing safe enough to try."
            )
        )
        qa.append(
            (
                f"How did they get the tube back?",
                f"They used {tool.phrase} while {helper.id} {skill.method}. Because the tool fit the obstacle and they moved carefully together, they reached the far side safely."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the flag ready again for the treasure walk. The forty stickers shining at the end showed that their brave, careful choice had worked."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} show bravery if {hero.pronoun()} did not cross?",
                f"{hero.id} was brave by stopping before a bad plan became dangerous. Then {hero.pronoun()} told {adult.label_word} the truth and asked for help."
            )
        )
        qa.append(
            (
                "Why did they turn back?",
                f"They turned back because the plan with {tool.label} was too shaky for {obstacle.label}. {helper.id}'s talented judgment showed that the path did not make sense that way."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with a grown-up helping recover the tube and the forty stickers still shining. The ending proves that careful help can finish an adventure well."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["obstacle_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["skill_cfg"].tags) | set(f["prize_cfg"].tags)
    if f["outcome"] == "helped":
        tags.add("help")
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
            shown = {k: v for k, v in e.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="pine_hollow",
        obstacle="creek",
        tool="stepping_stones",
        skill="balance",
        prize="flag_tube",
        hero_name="Mira",
        hero_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        relation="friends",
        trait="careful",
        parent="mother",
    ),
    StoryParams(
        setting="sunny_bank",
        obstacle="ravine",
        tool="plank",
        skill="planning",
        prize="flag_tube",
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Ava",
        helper_gender="girl",
        relation="siblings",
        trait="thoughtful",
        parent="father",
    ),
    StoryParams(
        setting="fern_glen",
        obstacle="slope",
        tool="rope",
        skill="knots",
        prize="flag_tube",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        relation="friends",
        trait="steady",
        parent="mother",
    ),
    StoryParams(
        setting="pine_hollow",
        obstacle="ravine",
        tool="rope",
        skill="knots",
        prize="flag_tube",
        hero_name="Iris",
        hero_gender="girl",
        helper_name="Toby",
        helper_gender="boy",
        relation="friends",
        trait="eager",
        parent="father",
    ),
]


ASP_RULES = r"""
fits(O,T) :- obstacle(O), tool(T), needs(O,N), supports(T,N).
helps(T,S) :- tool(T), skill(S), steadies(S,T).
valid(Place,O,T,S) :- setting(Place), obstacle(O), tool(T), skill(S), fits(O,T), helps(T,S).

boost(1) :- trait(T), careful_trait(T).
boost(0) :- trait(T), not careful_trait(T).
rel_bonus(1) :- relation(siblings).
rel_bonus(0) :- not relation(siblings).
bravery_now(B + X + Y) :- bravery_base(B), boost(X), rel_bonus(Y).
brave_enough :- bravery_now(N), bravery_need(M), N >= M.

outcome(crossed) :- chosen_obstacle(O), chosen_tool(T), chosen_skill(S), fits(O,T), helps(T,S), brave_enough.
outcome(helped) :- not outcome(crossed).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs", oid, obstacle.crossing_need))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for need in sorted(tool.supports):
            lines.append(asp.fact("supports", tid, need))
    for kid, skill in SKILLS.items():
        lines.append(asp.fact("skill", kid))
        for tid in sorted(skill.steadies):
            lines.append(asp.fact("steadies", kid, tid))
    lines.append(asp.fact("bravery_base", int(BRAVERY_BASE)))
    lines.append(asp.fact("bravery_need", int(BRAVERY_NEED)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_skill", params.skill),
        asp.fact("relation", params.relation),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    skill = SKILLS[params.skill]
    if valid_combo(obstacle, tool, skill) and brave_enough(params.trait, params.relation):
        return "crossed"
    return "helped"


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
    for seed in range(60):
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a brave trail adventure with a talented helper."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--skill", choices=SKILLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible adventure setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool and args.skill:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        skill = SKILLS[args.skill]
        if not valid_combo(obstacle, tool, skill):
            raise StoryError(explain_rejection(obstacle, tool, skill))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.tool is None or c[2] == args.tool)
        and (args.skill is None or c[3] == args.skill)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, obstacle, tool, skill = rng.choice(sorted(combos))
    prize = args.prize or "flag_tube"
    if prize not in PRIZES:
        raise StoryError(f"(No story: unknown prize '{prize}'.)")
    relation = args.relation or rng.choice(["friends", "siblings"])
    parent = args.parent or rng.choice(["mother", "father"])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=hero_name)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        obstacle=obstacle,
        tool=tool,
        skill=skill,
        prize=prize,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        relation=relation,
        trait=trait,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{params.tool}'.)")
    if params.skill not in SKILLS:
        raise StoryError(f"(No story: unknown skill '{params.skill}'.)")
    if params.prize not in PRIZES:
        raise StoryError(f"(No story: unknown prize '{params.prize}'.)")
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    skill = SKILLS[params.skill]
    if not valid_combo(obstacle, tool, skill):
        raise StoryError(explain_rejection(obstacle, tool, skill))

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle=obstacle,
        tool=tool,
        skill=skill,
        prize=PRIZES[params.prize],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        relation=params.relation,
        trait=params.trait,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, tool, skill) combos:\n")
        for setting, obstacle, tool, skill in combos:
            print(f"  {setting:12} {obstacle:8} {tool:16} {skill}")
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.obstacle} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
