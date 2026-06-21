#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mistletoe_thingamajigger_chum_bad_ending_kindness_happy.py
======================================================================================

A standalone story world for a small superhero tale domain: a child hero and a
trusted chum must save a winter celebration after a giant piece of mistletoe
gets tangled somewhere important. An inventor offers a strange gadget called a
thingamajigger. In this world, kindness is not decoration; it changes what the
heroes are taught, how well they use the gadget, and whether the ending turns
happy or bad.

The world is intentionally small and constrained:
- an obstacle has a physical need (lift or untangle), a required strength, and
  sometimes fragility
- a gadget mode has a capability, strength, and gentleness
- only compatible mission/obstacle/mode combinations are valid stories
- kindness adds real help from the inventor, improving the chance of success
- delay can make even a kind attempt come too late, yielding a bad ending

Run it
------
python storyworlds/worlds/gpt-5.4/mistletoe_thingamajigger_chum_bad_ending_kindness_happy.py
python storyworlds/worlds/gpt-5.4/mistletoe_thingamajigger_chum_bad_ending_kindness_happy.py --all
python storyworlds/worlds/gpt-5.4/mistletoe_thingamajigger_chum_bad_ending_kindness_happy.py --qa
python storyworlds/worlds/gpt-5.4/mistletoe_thingamajigger_chum_bad_ending_kindness_happy.py --verify
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
class Mission:
    id: str
    place: str
    crowd: str
    opening: str
    goal: str
    ending_image: str
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
    the: str
    place: str
    problem: str
    need: str
    min_power: int
    fragile: bool = False
    hazard: str = ""
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
class Mode:
    id: str
    label: str
    phrase: str
    capability: str
    power: int
    gentle: bool
    action_text: str
    success_text: str
    fail_text: str
    qa_text: str
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
class Approach:
    id: str
    ask_line: str
    tone_text: str
    kind: bool
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
    def __init__(self, mission: Mission) -> None:
        self.mission = mission
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
        clone = World(self.mission)
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


def _r_stuck_worries(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    crowd = world.get("crowd")
    if obstacle.meters["stuck"] < THRESHOLD:
        return []
    sig = ("worry", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.memes["worry"] += 1
    world.get("town").meters["delay"] += 1
    return ["__worry__"]


def _r_hurt_drops_trust(world: World) -> list[str]:
    inventor = world.get("inventor")
    if inventor.memes["hurt"] < THRESHOLD:
        return []
    sig = ("hurt", inventor.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    inventor.memes["trust"] = 0.0
    inventor.memes["help"] = 0.0
    return ["__hurt__"]


def _r_fixed_cheers(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["fixed"] < THRESHOLD:
        return []
    sig = ("cheer", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("town").meters["delay"] = 0.0
    world.get("crowd").memes["joy"] += 1
    world.get("hero").memes["relief"] += 1
    world.get("chum").memes["relief"] += 1
    world.get("inventor").memes["pride"] += 1
    return ["__cheer__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck_worries", tag="social", apply=_r_stuck_worries),
    Rule(name="hurt_drops_trust", tag="social", apply=_r_hurt_drops_trust),
    Rule(name="fixed_cheers", tag="social", apply=_r_fixed_cheers),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def compatible(mode: Mode, obstacle: Obstacle) -> bool:
    if mode.capability != obstacle.need:
        return False
    if mode.power < obstacle.min_power:
        return False
    if obstacle.fragile and not mode.gentle:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for mode_id, mode in MODES.items():
                if compatible(mode, obstacle):
                    out.append((mission_id, obstacle_id, mode_id))
    return out


def help_bonus(approach: Approach) -> int:
    return 1 if approach.kind else 0


def success_threshold(obstacle: Obstacle, delay: int) -> int:
    return obstacle.min_power + delay


def outcome_for(mode: Mode, obstacle: Obstacle, approach: Approach, delay: int) -> str:
    if not approach.kind:
        return "bad"
    total = mode.power + help_bonus(approach)
    return "happy" if total >= success_threshold(obstacle, delay) else "bad"


def explain_rejection(obstacle: Obstacle, mode: Mode) -> str:
    if mode.capability != obstacle.need:
        return (
            f"(No story: {mode.phrase} is built to {mode.capability}, but {obstacle.the} "
            f"needs someone to {obstacle.need}. Pick a matching mode.)"
        )
    if mode.power < obstacle.min_power:
        return (
            f"(No story: {mode.phrase} is too weak for {obstacle.the}. This rescue "
            f"needs at least power {obstacle.min_power}.)"
        )
    if obstacle.fragile and not mode.gentle:
        return (
            f"(No story: {obstacle.the} is too delicate for {mode.phrase}. Choose a "
            f"gentler thingamajigger mode.)"
        )
    return "(No story: this obstacle and mode do not fit together.)"


def predict_attempt(world: World, mode: Mode, approach: Approach, delay: int) -> dict:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    if approach.kind:
        sim.get("inventor").memes["help"] += 1
    else:
        sim.get("inventor").memes["hurt"] += 1
        propagate(sim, narrate=False)
    total = mode.power + help_bonus(approach)
    need = obstacle.attrs["need_power"] + delay
    if approach.kind and total >= need:
        obstacle.meters["fixed"] += 1
        obstacle.meters["stuck"] = 0.0
        propagate(sim, narrate=False)
    else:
        obstacle.meters["worse"] += 1
        sim.get("town").meters["delay"] += 1
    return {
        "kind_help": approach.kind,
        "total": total,
        "need": need,
        "success": obstacle.meters["fixed"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, chum: Entity, mission: Mission) -> None:
    hero.memes["brave"] += 1
    chum.memes["loyal"] += 1
    world.say(
        f"In {mission.place}, {hero.id} zipped along the rooftops in a bright cape, "
        f"with {chum.id} flying close behind like a true chum. {mission.opening}"
    )
    world.say(
        f'"To the sky, chum!" {hero.id} cried. "Tonight we guard {mission.goal}."'
    )


def reveal_problem(world: World, obstacle: Obstacle, crowd: Entity) -> None:
    thing = world.get("obstacle")
    thing.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But a winter gust had shoved a huge bunch of mistletoe into trouble. "
        f"{obstacle.problem}"
    )
    if crowd.memes["worry"] >= THRESHOLD:
        world.say(
            f"{crowd.label.capitalize()} looked up with worried faces, because "
            f"{obstacle.hazard}."
        )


def meet_inventor(world: World, inventor: Entity, mode: Mode) -> None:
    inventor.memes["hope"] += 1
    world.say(
        f"Down in the square stood Professor Tilda, the city's gentle inventor, "
        f"holding {mode.phrase}."
    )
    world.say(
        f'"My newest thingamajigger can help," {inventor.id} said, cradling it carefully.'
    )


def debate(world: World, hero: Entity, chum: Entity, approach: Approach, obstacle: Obstacle) -> None:
    hero.memes["hurry"] += 1
    if approach.kind:
        chum.memes["kindness"] += 1
        world.say(
            f'{chum.id} touched {hero.id}\'s sleeve. "Easy, hero," {chum.pronoun()} said. '
            f'"Big rescues still need kind words."'
        )
    else:
        hero.memes["pride"] += 1
        world.say(
            f'{hero.id} saw the clock ticking and puffed out {hero.pronoun("possessive")} chest. '
            f'"There is no time for slow talk," {hero.pronoun()} said.'
        )
    world.say(
        f"The whole square waited while the heroes chose how to ask for help with {obstacle.the}."
    )


def ask(world: World, hero: Entity, inventor: Entity, approach: Approach, mode: Mode) -> None:
    if approach.kind:
        hero.memes["kindness"] += 1
        inventor.memes["trust"] += 1
        inventor.memes["help"] += 1
        world.say(
            f'{hero.id} landed softly and said, "{approach.ask_line} Please show us how the '
            f"{mode.label} works."
        )
        world.say(
            f"{inventor.id} smiled at once. {approach.tone_text} She pointed to a blue switch "
            f"and a little silver dial."
        )
    else:
        inventor.memes["hurt"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{hero.id} reached too fast and said, "{approach.ask_line}"'
        )
        world.say(
            f"{inventor.id}'s face fell. {approach.tone_text} Her hands closed around the "
            f"thingamajigger for one hurt second before she stepped back."
        )


def attempt_rescue(world: World, hero: Entity, chum: Entity, inventor: Entity,
                   obstacle: Obstacle, mode: Mode, approach: Approach, delay: int) -> None:
    pred = predict_attempt(world, mode, approach, delay)
    world.facts["predicted_strength"] = pred["total"]
    world.facts["predicted_need"] = pred["need"]
    world.facts["predicted_success"] = pred["success"]
    world.say(
        f"{hero.id} and {chum.id} aimed the thingamajigger toward {obstacle.the}. "
        f"{mode.action_text}"
    )
    if approach.kind and pred["success"]:
        world.get("obstacle").meters["fixed"] += 1
        world.get("obstacle").meters["stuck"] = 0.0
        world.get("inventor").memes["help"] += 1
        propagate(world, narrate=False)
        world.say(mode.success_text.format(obstacle=obstacle.the))
    else:
        world.get("obstacle").meters["worse"] += 1
        world.get("town").meters["delay"] += 1
        world.get("crowd").memes["worry"] += 1
        world.get("hero").memes["remorse"] += 1
        world.get("chum").memes["sadness"] += 1
        world.say(mode.fail_text.format(obstacle=obstacle.the))


def happy_ending(world: World, hero: Entity, chum: Entity, inventor: Entity,
                 mission: Mission, obstacle: Obstacle, mode: Mode) -> None:
    hero.memes["joy"] += 1
    chum.memes["joy"] += 1
    inventor.memes["joy"] += 1
    world.say(
        f"{obstacle.The} was safe again, and the whole crowd let out one big cheer."
    )
    world.say(
        f'{inventor.id} laughed and said, "The best button on any thingamajigger is kindness." '
        f'{hero.id} grinned, and {chum.id} grinned back.'
    )
    world.say(
        f"Soon {mission.ending_image}, and {hero.id} knew that being strong was good, "
        f"but being kind made the strength land in the right place."
    )


def bad_ending(world: World, hero: Entity, chum: Entity, inventor: Entity,
               mission: Mission, obstacle: Obstacle, approach: Approach) -> None:
    town = world.get("town")
    town.meters["gloom"] += 1
    if approach.kind:
        line = (
            f"{inventor.id} had tried to help, but the rescue came too late. The crowd went quiet "
            f"as workers carried ladders out and the celebration was called off for the night."
        )
    else:
        line = (
            f"{inventor.id} tucked the thingamajigger against her coat and turned away hurt. "
            f"Without her help, the trouble only spread, and the celebration was called off for the night."
        )
    world.say(line)
    world.say(
        f"{hero.id} looked at {chum.id} and finally understood how much one rushed choice could change. "
        f"{chum.id} squeezed {hero.pronoun('possessive')} hand, because even in a bad ending, a friend can still be gentle."
    )
    world.say(
        f"The square stayed dim under the mistletoe, and {mission.crowd} walked home quietly. "
        f"It was a hard lesson, but a real one."
    )
@dataclass
class StoryParams:
    mission: str
    obstacle: str
    mode: str
    approach: str
    hero_name: str
    hero_gender: str
    chum_name: str
    chum_gender: str
    inventor_type: str
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
    "mistletoe": [
        (
            "What is mistletoe?",
            "Mistletoe is a green plant with little white berries that people sometimes hang up in winter. It is light, but a big bunch of it can still get tangled around things."
        )
    ],
    "gadget": [
        (
            "What is a thingamajigger?",
            "A thingamajigger is a playful word for a gadget or machine when its name sounds funny or complicated. It usually means some clever little tool."
        )
    ],
    "kindness": [
        (
            "Why can kindness help in a rescue?",
            "Kindness helps people trust each other and share what they know. When everyone works together calmly, a problem is often easier to fix."
        )
    ],
    "superhero": [
        (
            "What makes someone a superhero?",
            "A superhero helps other people when something is wrong. Big muscles can help, but brave choices and kind choices matter too."
        )
    ],
    "lift": [
        (
            "When should you lift something gently?",
            "You lift something gently when it is delicate or when something breakable is attached. A soft touch keeps the problem from getting worse."
        )
    ],
    "untangle": [
        (
            "What does untangle mean?",
            "Untangle means to loosen loops or knots so something can move freely again. It is often slower than yanking, but much safer."
        )
    ],
}

KNOWLEDGE_ORDER = ["superhero", "mistletoe", "gadget", "kindness", "lift", "untangle"]


CURATED = [
    StoryParams(
        mission="parade",
        obstacle="bell",
        mode="knot_nudger",
        approach="kind",
        hero_name="Nova",
        hero_gender="girl",
        chum_name="Dash",
        chum_gender="boy",
        inventor_type="woman",
        delay=0,
    ),
    StoryParams(
        mission="toy_drive",
        obstacle="basket",
        mode="loop_lifter",
        approach="kind",
        hero_name="Ruby",
        hero_gender="girl",
        chum_name="Finn",
        chum_gender="boy",
        inventor_type="woman",
        delay=1,
    ),
    StoryParams(
        mission="lantern_night",
        obstacle="star",
        mode="sky_crank",
        approach="kind",
        hero_name="Jett",
        hero_gender="boy",
        chum_name="Luna",
        chum_gender="girl",
        inventor_type="woman",
        delay=0,
    ),
    StoryParams(
        mission="parade",
        obstacle="star",
        mode="sky_crank",
        approach="grabby",
        hero_name="Mina",
        hero_gender="girl",
        chum_name="Leo",
        chum_gender="boy",
        inventor_type="woman",
        delay=0,
    ),
    StoryParams(
        mission="parade",
        obstacle="bell",
        mode="knot_nudger",
        approach="kind",
        hero_name="Astra",
        hero_gender="girl",
        chum_name="Nico",
        chum_gender="boy",
        inventor_type="woman",
        delay=2,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return outcome_for(MODES[params.mode], OBSTACLES[params.obstacle], APPROACHES[params.approach], params.delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    obstacle = f["obstacle_cfg"]
    mode = f["mode"]
    approach = f["approach"]
    outcome = f["outcome"]
    if outcome == "happy":
        return [
            f'Write a short superhero story for a 3-to-5-year-old that includes the words "mistletoe", "thingamajigger", and "chum".',
            f"Tell a bright rescue story where {hero.id} and a loyal chum save {mission.goal} with help from an inventor and a gadget called the {mode.label}.",
            f"Write a gentle superhero story where kindness helps fix {obstacle.the} and the ending proves the city celebration can continue."
        ]
    if approach.kind:
        return [
            f'Write a short superhero story for a 3-to-5-year-old that includes the words "mistletoe", "thingamajigger", and "chum".',
            f"Tell a story where {hero.id} is kind to an inventor, but the heroes are too late to save {mission.goal}.",
            f"Write a bittersweet superhero story showing that kindness matters even when a rescue does not work in time."
        ]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "mistletoe", "thingamajigger", and "chum".',
        f"Tell a superhero story where a hero rushes, hurts someone's feelings, and the rescue ends badly.",
        f"Write a cautionary superhero tale where the wrong way to ask for help turns a hard problem into a bad ending."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    chum = f["chum"]
    inventor = f["inventor"]
    mission = f["mission"]
    obstacle = f["obstacle_cfg"]
    mode = f["mode"]
    approach = f["approach"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about the young superhero {hero.id}, {chum.id} the loyal chum, and Professor Tilda the inventor. Together they try to save {mission.goal} in Sparkle City."
        ),
        (
            f"What problem did the heroes find?",
            f"They found that mistletoe had trapped {obstacle.the}. That was a problem because {obstacle.hazard}."
        ),
        (
            "What was the thingamajigger for?",
            f"The thingamajigger was a rescue gadget with a mode called the {mode.label}. It was meant to {mode.capability} the trouble safely."
        ),
    ]
    if approach.kind:
        qa.append(
            (
                f"How did {hero.id} ask Professor Tilda for help?",
                f"{hero.id} asked kindly and listened to the inventor's instructions. That kindness made Professor Tilda trust the heroes and share how the gadget really worked."
            )
        )
    else:
        qa.append(
            (
                f"Why did the rescue start going wrong?",
                f"The rescue started going wrong when {hero.id} rushed and spoke too sharply to Professor Tilda. Hurt feelings meant the hero did not get the calm help the thingamajigger needed."
            )
        )
    if outcome == "happy":
        qa.append(
            (
                "How was the problem solved?",
                f"The heroes {mode.qa_text} and fixed {obstacle.the}. Because they worked with Professor Tilda, the rescue had enough careful strength to succeed."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with {mission.goal} glowing again. The cheering crowd showed that kindness had changed the whole night."
            )
        )
    else:
        if approach.kind:
            qa.append(
                (
                    "Why was there still a bad ending even though the heroes were kind?",
                    f"The heroes were kind, but they had waited too long and the problem needed more strength than they had in time. Their good hearts mattered, yet the celebration still had to be called off."
                )
            )
        else:
            qa.append(
                (
                    "Why was the ending bad?",
                    f"The ending was bad because rushing replaced teamwork. Once Professor Tilda was hurt, the heroes lost the extra help that could have made the rescue work."
                )
            )
        qa.append(
            (
                "What did the hero learn?",
                f"{hero.id} learned that bravery without kindness can make a hard problem worse. Even superhero rescues need gentle words and patient help."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"superhero", "mistletoe", "gadget"}
    tags |= set(f["mission"].tags)
    tags |= set(f["mode"].tags)
    tags |= set(f["approach"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:16} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
fragile_conflict(Md, Ob) :- obstacle(Ob), mode(Md), fragile(Ob), not gentle(Md).
compatible(Md, Ob) :- capability(Md, C), need(Ob, C),
                      power(Md, P), min_power(Ob, MP), P >= MP,
                      not fragile_conflict(Md, Ob).
valid(Mis, Ob, Md) :- mission(Mis), obstacle(Ob), mode(Md), compatible(Md, Ob).

% --- outcome model ---------------------------------------------------------
help_bonus(1) :- approach(kind).
help_bonus(0) :- approach(grabby).

strength(P + B) :- chosen_mode(Md), power(Md, P), help_bonus(B).
needed(MP + D) :- chosen_obstacle(Ob), min_power(Ob, MP), delay(D).

happy :- approach(kind), strength(S), needed(N), S >= N.
outcome(happy) :- happy.
outcome(bad) :- not happy.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("need", obstacle_id, obstacle.need))
        lines.append(asp.fact("min_power", obstacle_id, obstacle.min_power))
        if obstacle.fragile:
            lines.append(asp.fact("fragile", obstacle_id))
    for mode_id, mode in MODES.items():
        lines.append(asp.fact("mode", mode_id))
        lines.append(asp.fact("capability", mode_id, mode.capability))
        lines.append(asp.fact("power", mode_id, mode.power))
        if mode.gentle:
            lines.append(asp.fact("gentle", mode_id))
    for approach_id in APPROACHES:
        lines.append(asp.fact("approach_type", approach_id))
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
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_mode", params.mode),
        asp.fact("delay", params.delay),
        asp.fact("approach", params.approach),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if c_set == p_set:
        print(f"OK: compatibility gate matches valid_combos() ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as exc:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero rescue where kindness changes how a thingamajigger works."
    )
    ap.add_argument("--mission", choices=sorted(MISSIONS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--mode", choices=sorted(MODES))
    ap.add_argument("--approach", choices=sorted(APPROACHES))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the trouble gets before the rescue")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--chum-name")
    ap.add_argument("--chum-gender", choices=["girl", "boy"])
    ap.add_argument("--inventor-type", choices=["woman", "man"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.mode:
        obstacle = OBSTACLES[args.obstacle]
        mode = MODES[args.mode]
        if not compatible(mode, obstacle):
            raise StoryError(explain_rejection(obstacle, mode))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.mode is None or combo[2] == args.mode)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, obstacle_id, mode_id = rng.choice(sorted(combos))
    approach_id = args.approach or rng.choice(sorted(APPROACHES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    chum_gender = args.chum_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    chum_name = args.chum_name or pick_name(rng, chum_gender, avoid=hero_name)
    inventor_type = args.inventor_type or "woman"

    return StoryParams(
        mission=mission_id,
        obstacle=obstacle_id,
        mode=mode_id,
        approach=approach_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        chum_name=chum_name,
        chum_gender=chum_gender,
        inventor_type=inventor_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.mode not in MODES:
        raise StoryError(f"(Unknown mode: {params.mode})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.chum_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown chum gender: {params.chum_gender})")
    if params.inventor_type not in {"woman", "man"}:
        raise StoryError(f"(Unknown inventor type: {params.inventor_type})")

    mission = MISSIONS[params.mission]
    obstacle = OBSTACLES[params.obstacle]
    mode = MODES[params.mode]
    approach = APPROACHES[params.approach]

    if not compatible(mode, obstacle):
        raise StoryError(explain_rejection(obstacle, mode))

    world = tell(
        mission=mission,
        obstacle_cfg=obstacle,
        mode=mode,
        approach=approach,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        chum_name=params.chum_name,
        chum_gender=params.chum_gender,
        inventor_type=params.inventor_type,
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
        print(f"{len(combos)} compatible (mission, obstacle, mode) combos:\n")
        for mission_id, obstacle_id, mode_id in combos:
            print(f"  {mission_id:12} {obstacle_id:10} {mode_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} & {p.chum_name}: {p.obstacle} with {p.mode} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(mission: Mission, obstacle_cfg: Obstacle, mode: Mode, approach: Approach,
         hero_name: str = "Nova", hero_gender: str = "girl",
         chum_name: str = "Dash", chum_gender: str = "boy",
         inventor_type: str = "woman", delay: int = 0) -> World:
    world = World(mission)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    chum = world.add(Entity(id=chum_name, kind="character", type=chum_gender, role="chum"))
    inventor = world.add(Entity(id="Professor Tilda", kind="character", type=inventor_type,
                                role="inventor", label="the inventor",
                                tags={"kindness", "gadget"}))
    crowd = world.add(Entity(id="crowd", type="crowd", label=mission.crowd))
    town = world.add(Entity(id="town", type="town", label="the town"))
    obstacle = world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=obstacle_cfg.label,
        role="obstacle",
        attrs={"need": obstacle_cfg.need, "need_power": obstacle_cfg.min_power,
               "fragile": obstacle_cfg.fragile, "delay": delay},
        tags=set(obstacle_cfg.tags),
    ))

    crowd.memes["worry"] = 0.0
    town.meters["delay"] = 0.0
    town.meters["gloom"] = 0.0
    obstacle.meters["stuck"] = 0.0
    obstacle.meters["fixed"] = 0.0
    obstacle.meters["worse"] = 0.0
    inventor.memes["trust"] = 0.0
    inventor.memes["help"] = 0.0
    inventor.memes["hurt"] = 0.0

    introduce(world, hero, chum, mission)
    reveal_problem(world, obstacle_cfg, crowd)

    world.para()
    meet_inventor(world, inventor, mode)
    debate(world, hero, chum, approach, obstacle_cfg)
    ask(world, hero, inventor, approach, mode)

    world.para()
    attempt_rescue(world, hero, chum, inventor, obstacle_cfg, mode, approach, delay)
    outcome = outcome_for(mode, obstacle_cfg, approach, delay)

    world.para()
    if outcome == "happy":
        happy_ending(world, hero, chum, inventor, mission, obstacle_cfg, mode)
    else:
        bad_ending(world, hero, chum, inventor, mission, obstacle_cfg, approach)

    world.facts.update(
        hero=hero,
        chum=chum,
        inventor=inventor,
        mission=mission,
        obstacle_cfg=obstacle_cfg,
        obstacle=obstacle,
        mode=mode,
        approach=approach,
        delay=delay,
        outcome=outcome,
        fixed=obstacle.meters["fixed"] >= THRESHOLD,
        kind=approach.kind,
    )
    return world


MISSIONS = {
    "parade": Mission(
        id="parade",
        place="Sparkle City",
        crowd="the parade families",
        opening="Below them, the Winter Kindness Parade shimmered with capes, lanterns, and paper stars.",
        goal="the Winter Kindness Parade",
        ending_image="the parade rolled on beneath strings of lights, and children waved from glittering floats",
        tags={"superhero", "kindness"},
    ),
    "toy_drive": Mission(
        id="toy_drive",
        place="Sparkle City",
        crowd="the toy-drive families",
        opening="Below them, the Hero Toy Drive glowed outside the town hall with boxes, ribbons, and smiling volunteers.",
        goal="the Hero Toy Drive",
        ending_image="the toy tables sparkled again, and children marched in with gifts tucked under mittened arms",
        tags={"superhero", "kindness"},
    ),
    "lantern_night": Mission(
        id="lantern_night",
        place="Sparkle City",
        crowd="the lantern-night families",
        opening="Below them, Lantern Night flickered across the square, where every window had a candle-safe paper light.",
        goal="Lantern Night",
        ending_image="soft lanterns bobbed across the square, and the rooftops glowed like a blanket of stars",
        tags={"superhero", "kindness"},
    ),
}

OBSTACLES = {
    "bell": Obstacle(
        id="bell",
        label="clock bell rope",
        the="the clock bell rope",
        place="the old clock tower",
        problem="A giant loop of mistletoe had wrapped itself around the clock bell rope at the old tower, pinning it so the starting bell could not ring.",
        need="untangle",
        min_power=2,
        fragile=False,
        hazard="without the bell, nobody would know when the celebration began",
        tags={"mistletoe", "tower"},
    ),
    "basket": Obstacle(
        id="basket",
        label="gift basket cable",
        the="the gift basket cable",
        place="the toy-drive crane",
        problem="A giant knot of mistletoe had snagged the gift basket cable, and one wobbling basket of presents hung high above the square.",
        need="lift",
        min_power=2,
        fragile=True,
        hazard="if the basket jerked too hard, all the presents might tumble into the slush",
        tags={"mistletoe", "gifts"},
    ),
    "star": Obstacle(
        id="star",
        label="star lantern frame",
        the="the star lantern frame",
        place="the center arch",
        problem="A thick bunch of mistletoe had jammed the star lantern frame over the center arch, leaving the biggest lantern dark and crooked.",
        need="lift",
        min_power=3,
        fragile=False,
        hazard="without the star lantern, the whole square felt dim and unfinished",
        tags={"mistletoe", "lantern"},
    ),
}

MODES = {
    "loop_lifter": Mode(
        id="loop_lifter",
        label="Loop-Lifter",
        phrase="a brass thingamajigger called the Loop-Lifter",
        capability="lift",
        power=2,
        gentle=True,
        action_text="A soft gold ring floated out of the machine with a careful hum.",
        success_text="{obstacle} rose just enough for the knot to slip free, and everything settled back into place with a neat little click.",
        fail_text="The gold ring wobbled, but {obstacle} would not budge enough. The trouble stayed right where it was, and the square groaned.",
        qa_text="used the gentle Loop-Lifter to raise it just enough for the knot to slide free",
        tags={"gadget", "lift"},
    ),
    "sky_crank": Mode(
        id="sky_crank",
        label="Sky-Crank",
        phrase="a silver thingamajigger called the Sky-Crank",
        capability="lift",
        power=3,
        gentle=False,
        action_text="A bright blue beam pushed upward with a mighty whoosh.",
        success_text="{obstacle} jumped free in one strong motion, and the arch straightened with a flash of light.",
        fail_text="The beam hit too roughly, and {obstacle} shook without helping the knot at all. People below gasped and stepped back.",
        qa_text="used the strong Sky-Crank to shove it free in one motion",
        tags={"gadget", "lift"},
    ),
    "knot_nudger": Mode(
        id="knot_nudger",
        label="Knot-Nudger",
        phrase="a copper thingamajigger called the Knot-Nudger",
        capability="untangle",
        power=2,
        gentle=True,
        action_text="Tiny spinning fingers of light twirled out and teased at the loops one by one.",
        success_text="The glowing fingers loosened {obstacle} until the mistletoe slid away in a green tumble.",
        fail_text="The little spinning fingers picked and picked, but {obstacle} stayed jammed. The clock still could not ring.",
        qa_text="used the Knot-Nudger to tease the loops apart one by one",
        tags={"gadget", "untangle"},
    ),
    "whirl_wrench": Mode(
        id="whirl_wrench",
        label="Whirl-Wrench",
        phrase="a whirring thingamajigger called the Whirl-Wrench",
        capability="untangle",
        power=3,
        gentle=False,
        action_text="A fast purple corkscrew of air spun out with superhero speed.",
        success_text="The corkscrew air snapped the knot open, and the trapped rope sprang loose at last.",
        fail_text="The purple spin whipped the mistletoe around, but {obstacle} only tangled tighter. The trouble grew messier instead of better.",
        qa_text="used the Whirl-Wrench to spin the knot apart",
        tags={"gadget", "untangle"},
    ),
}

APPROACHES = {
    "kind": Approach(
        id="kind",
        ask_line="Professor Tilda, will you help us save the night",
        tone_text="Her kind voice turned the whole hurry softer.",
        kind=True,
        tags={"kindness"},
    ),
    "grabby": Approach(
        id="grabby",
        ask_line="Hand me the thingamajigger and I will do it myself",
        tone_text="The rush in the words made them sound more bossy than brave.",
        kind=False,
        tags={"bad_ending"},
    ),
}

GIRL_NAMES = ["Nova", "Ruby", "Skye", "Mina", "Luna", "Astra", "Poppy", "Nia"]
BOY_NAMES = ["Dash", "Toby", "Leo", "Finn", "Max", "Eli", "Jett", "Nico"]

if __name__ == "__main__":
    main()
