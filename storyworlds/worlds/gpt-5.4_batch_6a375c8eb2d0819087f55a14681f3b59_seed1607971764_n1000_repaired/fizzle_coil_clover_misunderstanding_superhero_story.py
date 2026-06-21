#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fizzle_coil_clover_misunderstanding_superhero_story.py

A small standalone storyworld about two children playing superheroes when a
rescue gadget goes fizzle, a misunderstanding hurts feelings, and the truth is
found in a clover patch.

The domain is intentionally tight: every story includes a superhero rescue
mission, a spring-like coil gadget, a clover patch, and a misunderstanding.
The world model decides what the gadget can honestly rescue, whether the delay
caused by the misunderstanding is small enough for success, and how the ending
changes when the team works together again.
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
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    skyline: str
    clover_spot: str
    perch_kinds: set[str]
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
class Target:
    id: str
    label: str
    phrase: str
    article: str
    material: str
    perch: str
    difficulty: int
    drifts: bool
    opening: str
    ending_image: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"

    @property
    def The(self) -> str:
        return f"The {self.label}"
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
class Gadget:
    id: str
    label: str
    phrase: str
    works_on: set[str]
    reach: int
    launch_line: str
    rescue_line: str
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


def _r_urgency(world: World) -> list[str]:
    target = world.get("target")
    if target.meters["stuck"] < THRESHOLD:
        return []
    sig = ("urgency", "target")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "sidekick"):
        world.get(eid).memes["urgency"] += 1
    return []


def _r_fizzle(world: World) -> list[str]:
    gadget = world.get("gadget")
    if gadget.meters["tangled"] < THRESHOLD or gadget.meters["used"] < THRESHOLD:
        return []
    sig = ("fizzle", "gadget")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gadget.meters["fizzle"] += 1
    gadget.meters["power"] = 0.0
    return []


def _r_misunderstanding(world: World) -> list[str]:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if hero.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("hurt_feelings", "pair")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["frustration"] += 1
    sidekick.memes["hurt"] += 1
    return []


def _r_clarified(world: World) -> list[str]:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if hero.memes["clarity"] < THRESHOLD:
        return []
    sig = ("teamwork", "pair")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["frustration"] = 0.0
    sidekick.memes["hurt"] = 0.0
    hero.memes["trust"] += 1
    sidekick.memes["trust"] += 1
    hero.memes["teamwork"] += 1
    sidekick.memes["teamwork"] += 1
    return []


def _r_rescued(world: World) -> list[str]:
    target = world.get("target")
    if target.meters["rescued"] < THRESHOLD:
        return []
    sig = ("relief", "team")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "sidekick", "mentor"):
        world.get(eid).memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="urgency", tag="emotional", apply=_r_urgency),
    Rule(name="fizzle", tag="physical", apply=_r_fizzle),
    Rule(name="misunderstanding", tag="social", apply=_r_misunderstanding),
    Rule(name="clarified", tag="social", apply=_r_clarified),
    Rule(name="rescued", tag="emotional", apply=_r_rescued),
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
            world.say(line)
    return produced


def base_success(gadget: Gadget, target: Target) -> bool:
    return target.material in gadget.works_on and gadget.reach >= target.difficulty


def valid_for_story(gadget: Gadget, target: Target) -> bool:
    return base_success(gadget, target)


def needed_reach(target: Target, delay: int) -> int:
    extra = delay
    if target.drifts:
        extra += 1
    return target.difficulty + extra


def final_success(gadget: Gadget, target: Target, delay: int) -> bool:
    return gadget.reach >= needed_reach(target, delay)


def explain_rejection(gadget: Gadget, target: Target) -> str:
    if target.material not in gadget.works_on:
        works = ", ".join(sorted(gadget.works_on))
        return (
            f"(No story: {gadget.label} is built for {works}, but {target.the} is "
            f"{target.material}. The rescue tool and target have to match.)"
        )
    if gadget.reach < target.difficulty:
        return (
            f"(No story: {gadget.label} cannot honestly reach {target.the} on the "
            f"{target.perch}. Pick a stronger rescue gadget or an easier target.)"
        )
    return "(No story: this rescue setup is not reasonable.)"


def outcome_of(params: "StoryParams") -> str:
    target = TARGETS[params.target]
    gadget = GADGETS[params.gadget]
    return "rescued" if final_success(gadget, target, params.delay) else "lost"


def predict_outcome(world: World, delay: int) -> dict:
    sim = world.copy()
    target_cfg = sim.facts["target_cfg"]
    gadget_cfg = sim.facts["gadget_cfg"]
    return {
        "needed_reach": needed_reach(target_cfg, delay),
        "rescued": final_success(gadget_cfg, target_cfg, delay),
    }


def introduce(world: World, hero: Entity, sidekick: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"After school, {hero.id} and {sidekick.id} raced into {setting.place} as if "
        f"the whole place were their city to protect. {setting.skyline}"
    )
    world.say(
        f"{hero.id} called them Captain Brightbolt, and {sidekick.id} was Spark Patch, "
        f"the quickest sidekick in the neighborhood."
    )


def mission(world: World, hero: Entity, sidekick: Entity, target: Target) -> None:
    tgt = world.get("target")
    tgt.meters["stuck"] = 1.0
    propagate(world, narrate=False)
    world.say(target.opening)
    world.say(
        f'"Rescue mission!" {hero.id} said, already standing taller as if a cape had '
        f"snapped open behind {hero.pronoun('object')}."
    )


def prepare_gadget(world: World, hero: Entity, gadget: Gadget) -> None:
    g = world.get("gadget")
    g.meters["power"] = 1.0
    world.say(
        f"From the rescue box, {hero.id} lifted {gadget.phrase}. Its silver coil "
        f"gleamed like a tiny hero spring."
    )
    world.say(gadget.launch_line)


def snag_in_clover(world: World) -> None:
    gadget = world.get("gadget")
    clover = world.get("clover")
    gadget.meters["used"] = 1.0
    gadget.meters["tangled"] = 1.0
    clover.meters["holding"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But the line gave a twitch, then a little fizzle. Down by {world.setting.clover_spot}, "
        f"the coil had caught in the clover."
    )


def misunderstand(world: World, hero: Entity, sidekick: Entity, target: Target) -> None:
    hero.memes["misunderstanding"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} spun around. "Spark Patch, did you yank it?" {hero.pronoun()} asked. '
        f'"I almost had {target.the}!"'
    )
    world.say(
        f'{sidekick.id} blinked in surprise. "{hero.id}, no! I was trying to point at '
        f'the ground."'
    )


def hurt_beat(world: World, hero: Entity, sidekick: Entity) -> None:
    if sidekick.memes["hurt"] >= THRESHOLD:
        world.say(
            f"For one small, sore moment, being superheroes felt less like flying and "
            f"more like standing still."
        )
        world.say(
            f"{sidekick.id} hugged {sidekick.pronoun('possessive')} elbows and looked "
            f"down. {hero.id} heard how sharp the accusation had sounded."
        )


def clarify(world: World, hero: Entity, sidekick: Entity, mentor: Entity) -> None:
    hero.memes["clarity"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {sidekick.id} knelt and lifted the line just enough to show the truth: "
        f"three clover stems were wrapped around the coil."
    )
    world.say(
        f'{mentor.label_word.capitalize()} pointed too. "The gadget went fizzle because '
        f'the coil snagged. {sidekick.id} was helping, not spoiling," {mentor.pronoun()} said.'
    )
    world.say(
        f'{hero.id} felt {hero.pronoun("possessive")} hot cheeks cool. "I got it wrong," '
        f'{hero.pronoun()} said softly.'
    )


def repair(world: World, hero: Entity, sidekick: Entity, gadget: Gadget) -> None:
    g = world.get("gadget")
    clover = world.get("clover")
    g.meters["tangled"] = 0.0
    g.meters["power"] = 1.0
    clover.meters["holding"] = 0.0
    world.say(
        f"Together they teased the stems free without hurting the clover patch, then "
        f"wound the coil smooth again."
    )
    world.say(
        f'{hero.id} handed the handle to {sidekick.id}. "Team launch?" {hero.pronoun()} asked.'
    )


def rescue(world: World, hero: Entity, sidekick: Entity, gadget: Gadget, target: Target) -> None:
    tgt = world.get("target")
    tgt.meters["rescued"] = 1.0
    tgt.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        gadget.rescue_line.format(target=target.label, perch=target.perch)
    )
    world.say(
        f"In one brave swoop, {target.the} was safe again."
    )
    world.say(
        f"{target.ending_image}"
    )


def loss(world: World, hero: Entity, sidekick: Entity, gadget: Gadget, target: Target) -> None:
    tgt = world.get("target")
    tgt.meters["lost"] = 1.0
    tgt.meters["stuck"] = 0.0
    world.say(
        f"They freed the coil at last and aimed again, but the delay had changed the mission."
    )
    if target.drifts:
        world.say(
            f"A breeze tugged {target.the} away before the launcher could catch up, and it "
            f"sailed farther and farther into the evening sky."
        )
    else:
        world.say(
            f"{target.The} slipped to a place even their little gadget could not safely reach."
        )
    world.say(
        f"{hero.id} did not pretend to feel grand. {hero.pronoun().capitalize()} stood very still, "
        f"then took {sidekick.id}'s hand."
    )


def closing_lesson(world: World, hero: Entity, sidekick: Entity, mentor: Entity, target: Target, outcome: str) -> None:
    if outcome == "rescued":
        world.say(
            f'{mentor.label_word.capitalize()} smiled. "Real heroes look twice before they blame, '
            f'and they work together when something goes wrong."'
        )
        world.say(
            f'{hero.id} bumped shoulders with {sidekick.id}. "Next time I will listen first," '
            f'{hero.pronoun()} promised.'
        )
        world.say(
            f"Above the clover patch, the whole rescue team suddenly looked exactly right again."
        )
    else:
        world.say(
            f'{mentor.label_word.capitalize()} knelt beside them. "You could not save the mission this '
            f'time, but you can still learn from it," {mentor.pronoun()} said.'
        )
        world.say(
            f'{hero.id} nodded. "Next time I will listen first and check what really happened."'
        )
        world.say(
            f"The clover leaves moved in the breeze while the little heroes stood close together, "
            f"sadder but wiser."
        )


def tell(
    setting: Setting,
    target_cfg: Target,
    gadget_cfg: Gadget,
    hero_name: str = "Maya",
    hero_gender: str = "girl",
    sidekick_name: str = "Theo",
    sidekick_gender: str = "boy",
    mentor_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=sidekick_gender, label=sidekick_name, role="sidekick"))
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_type, label="the parent", role="mentor"))
    target = world.add(Entity(id="target", kind="thing", type="target", label=target_cfg.label, role="target"))
    gadget = world.add(Entity(id="gadget", kind="thing", type="gadget", label=gadget_cfg.label, role="gadget"))
    clover = world.add(Entity(id="clover", kind="thing", type="plant", label="clover patch", role="clover"))

    for ent in (hero, sidekick, mentor, target, gadget, clover):
        ent.attrs["ready"] = True
        ent.meters["seen"] = 0.0
        ent.memes["trust"] = 0.0
    target.meters["stuck"] = 0.0
    target.meters["rescued"] = 0.0
    target.meters["lost"] = 0.0
    gadget.meters["used"] = 0.0
    gadget.meters["tangled"] = 0.0
    gadget.meters["fizzle"] = 0.0
    gadget.meters["power"] = 1.0
    clover.meters["holding"] = 0.0
    hero.memes["misunderstanding"] = 0.0
    hero.memes["clarity"] = 0.0

    world.facts.update(
        setting=setting,
        target_cfg=target_cfg,
        gadget_cfg=gadget_cfg,
        hero=hero,
        sidekick=sidekick,
        mentor=mentor,
        delay=delay,
    )

    introduce(world, hero, sidekick, setting)
    mission(world, hero, sidekick, target_cfg)

    world.para()
    prepare_gadget(world, hero, gadget_cfg)
    snag_in_clover(world)
    misunderstand(world, hero, sidekick, target_cfg)
    hurt_beat(world, hero, sidekick)

    prediction = predict_outcome(world, delay)
    world.facts["predicted_needed_reach"] = prediction["needed_reach"]

    world.para()
    clarify(world, hero, sidekick, mentor)
    repair(world, hero, sidekick, gadget_cfg)

    outcome = "rescued" if prediction["rescued"] else "lost"
    world.facts["outcome"] = outcome

    world.para()
    if outcome == "rescued":
        rescue(world, hero, sidekick, gadget_cfg, target_cfg)
    else:
        loss(world, hero, sidekick, gadget_cfg, target_cfg)
    closing_lesson(world, hero, sidekick, mentor, target_cfg, outcome)

    world.facts.update(
        misunderstanding=True,
        clover_snag=True,
        fizzle=gadget.meters["fizzle"] >= THRESHOLD,
        rescued=outcome == "rescued",
        target=target,
        gadget=gadget,
        clover=clover,
    )
    return world


SETTINGS = {
    "park": Setting(
        id="park",
        place="the park",
        skyline="The slide looked like a silver tower, and the benches made tidy little rooftops for make-believe patrols.",
        clover_spot="the clover patch beside the path",
        perch_kinds={"tree", "bench", "lamp"},
        tags={"park", "outside"},
    ),
    "schoolyard": Setting(
        id="schoolyard",
        place="the schoolyard",
        skyline="The jungle gym rose like a training base, and the blacktop shone under the afternoon sun.",
        clover_spot="the clover patch by the fence",
        perch_kinds={"bars", "fence", "lamp"},
        tags={"schoolyard", "outside"},
    ),
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        skyline="The shed stood like a headquarters, and the birdbath glittered like a signal beacon.",
        clover_spot="the clover patch near the stepping stones",
        perch_kinds={"tree", "shed", "line"},
        tags={"backyard", "outside"},
    ),
}

TARGETS = {
    "cape": Target(
        id="cape",
        label="cape",
        phrase="a red play cape",
        article="a",
        material="fabric",
        perch="fence",
        difficulty=1,
        drifts=False,
        opening="A gust had flipped a red play cape up onto the fence, where it fluttered like a trapped hero flag.",
        ending_image="The red cape snapped free and streamed behind them so brightly that even the fence looked defeated.",
        tags={"cape", "fabric"},
    ),
    "kite": Target(
        id="kite",
        label="kite",
        phrase="a starry kite",
        article="a",
        material="fabric",
        perch="tree",
        difficulty=2,
        drifts=False,
        opening="High in a tree, a starry kite hung between two branches, trembling every time the wind poked at it.",
        ending_image="Soon the kite was bobbing in friendly hands instead of lonely branches.",
        tags={"kite", "fabric", "wind"},
    ),
    "lunchbox": Target(
        id="lunchbox",
        label="lunchbox",
        phrase="a shiny lunchbox",
        article="a",
        material="metal",
        perch="bars",
        difficulty=2,
        drifts=False,
        opening="Somehow a shiny lunchbox had landed on top of the monkey bars, glinting far above their heads.",
        ending_image="The lunchbox came down with a neat click, safe and square and ready to be carried home.",
        tags={"lunchbox", "metal"},
    ),
    "robot": Target(
        id="robot",
        label="toy robot",
        phrase="a tin toy robot",
        article="a",
        material="metal",
        perch="shed",
        difficulty=3,
        drifts=False,
        opening="On the shed roof, a tin toy robot leaned at the edge as if one sneeze of wind could send it sliding.",
        ending_image="The toy robot rode back down like a rescued mayor returning to city hall.",
        tags={"robot", "metal"},
    ),
    "balloon": Target(
        id="balloon",
        label="balloon ribbon",
        phrase="a gold balloon ribbon",
        article="a",
        material="light",
        perch="lamp",
        difficulty=1,
        drifts=True,
        opening="A gold balloon ribbon had wrapped itself around the tall park lamp, dancing and twitching above the grass.",
        ending_image="The ribbon curled into their hands, and the balloon bobbed overhead like a cheer.",
        tags={"balloon", "light", "wind"},
    ),
}

GADGETS = {
    "loop_launcher": Gadget(
        id="loop_launcher",
        label="Loop Launcher",
        phrase="the Loop Launcher",
        works_on={"fabric", "light"},
        reach=2,
        launch_line='"Loop ready!" {hero} cried, aiming the padded loop toward the mission.',
        rescue_line="The Loop Launcher zipped up, slipped around the {target}, and tugged it neatly free from the {perch}.",
        tags={"loop_launcher", "fabric", "superhero"},
    ),
    "magnet_coil": Gadget(
        id="magnet_coil",
        label="Magnet Coil",
        phrase="the Magnet Coil",
        works_on={"metal"},
        reach=2,
        launch_line='"Magnet Coil, be mighty!" {hero} cried, sending the little hook upward.',
        rescue_line="The Magnet Coil hummed, kissed the {target} with a click, and drew it away from the {perch}.",
        tags={"magnet_coil", "metal", "coil"},
    ),
    "sky_saver": Gadget(
        id="sky_saver",
        label="Sky Saver",
        phrase="the Sky Saver",
        works_on={"fabric", "light", "metal"},
        reach=3,
        launch_line='"Sky Saver, up!" {hero} cried, and the bright line shot out in a sparkling arc.',
        rescue_line="The Sky Saver rose high, steadied itself, and brought the {target} down from the {perch} as gently as a superhero hand.",
        tags={"sky_saver", "superhero", "coil"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Ava", "Nora", "Zoe", "Ivy", "Ruby", "Ella"]
BOY_NAMES = ["Theo", "Max", "Leo", "Finn", "Eli", "Ben", "Noah", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for tid, target in TARGETS.items():
            if target.perch not in setting.perch_kinds:
                continue
            for gid, gadget in GADGETS.items():
                if valid_for_story(gadget, target):
                    combos.append((sid, tid, gid))
    return combos


@dataclass
class StoryParams:
    setting: str
    target: str
    gadget: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
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
    "clover": [
        (
            "What is clover?",
            "Clover is a small plant with round little leaves. It often grows in soft patches close to the ground."
        )
    ],
    "coil": [
        (
            "What is a coil?",
            "A coil is something wound in loops like a spring. When a coil gets tangled, it cannot move the smooth way it should."
        )
    ],
    "fizzle": [
        (
            "What does fizzle mean?",
            "Fizzle means making a weak sputtering sound instead of working strongly. A toy or gadget might fizzle when it is tangled or losing power."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what happened but gets it wrong. Talking and checking the facts can fix it."
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet pulls some kinds of metal toward it. That can help pick up a metal thing from a hard place."
        )
    ],
    "fabric": [
        (
            "Why would a loop help rescue cloth?",
            "A soft loop can catch cloth without poking holes in it. That makes it a gentle tool for a cape or kite."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork helpful in a rescue?",
            "Teamwork helps because one person can notice what another person missed. Working together often solves a problem faster and more kindly."
        )
    ],
}
KNOWLEDGE_ORDER = ["clover", "coil", "fizzle", "misunderstanding", "magnet", "fabric", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    target = world.facts["target_cfg"]
    gadget = world.facts["gadget_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "rescued":
        return [
            'Write a short superhero story for a 3-to-5-year-old that includes the words "fizzle", "coil", and "clover", and centers on a misunderstanding.',
            f"Tell a gentle superhero rescue story where {hero.label} wrongly thinks {sidekick.label} caused a problem, but the truth is that a coil snagged in clover while they were trying to save {target.the}.",
            f"Write a child-friendly story where {gadget.label} goes fizzle during a mission, feelings get hurt for a moment, and the heroes fix both the gadget and the misunderstanding.",
        ]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "fizzle", "coil", and "clover", and centers on a misunderstanding.',
        f"Tell a superhero story where {hero.label} blames {sidekick.label} too quickly after a gadget goes fizzle, and although they learn the truth about the coil in the clover, they are too late to save {target.the}.",
        "Write a gentle cautionary superhero tale showing that listening first matters, even when a mission does not end the way the heroes hoped.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    mentor = world.facts["mentor"]
    target = world.facts["target_cfg"]
    gadget = world.facts["gadget_cfg"]
    outcome = world.facts["outcome"]
    delay = world.facts["delay"]
    needed = world.facts["predicted_needed_reach"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the heroes in the story?",
            f"The heroes are {hero.label}, who called {hero.pronoun('object')}self Captain Brightbolt, and {sidekick.label}, the sidekick Spark Patch. They were pretending their ordinary play place was a city that needed saving."
        ),
        (
            "What was the rescue mission?",
            f"They were trying to save {target.the} from the {target.perch}. It looked stuck and needed a careful superhero tool to bring it down."
        ),
        (
            f"Why did the gadget go fizzle?",
            f"It went fizzle because the coil snagged in the clover patch. The problem was on the ground, not something {sidekick.label} did."
        ),
        (
            f"What was the misunderstanding?",
            f"{hero.label} thought {sidekick.label} had yanked the line and spoiled the rescue. That was a misunderstanding, because {sidekick.label} was only trying to point out the clover wrapped around the coil."
        ),
    ]
    if outcome == "rescued":
        qa.append(
            (
                "How did they fix the problem?",
                f"They looked closely, freed the clover stems from the coil, and worked together on the next launch. Once the misunderstanding was cleared, their teamwork made the rescue possible."
            )
        )
        qa.append(
            (
                f"How did the story end?",
                f"It ended happily, with {target.the} rescued and the team feeling close again. {hero.label} also learned to listen before blaming, so the ending showed a change in both the mission and the friendship."
            )
        )
    else:
        qa.append(
            (
                "Why were they too late?",
                f"They lost time while the misunderstanding hurt feelings and paused the rescue. The mission needed reach {needed}, and that extra delay made it harder than their little gadget could manage."
            )
        )
        qa.append(
            (
                "What did the heroes learn even though the rescue failed?",
                f"They learned to stop, listen, and check the real cause before blaming someone. That lesson matters because superhero courage also means being fair and thoughtful."
            )
        )
    if delay:
        qa.append(
            (
                "Did the delay matter?",
                f"Yes. The misunderstanding cost them time, and in a rescue even a small pause can change what a gadget can still reach. That is why the story treats the hurt feelings as part of the real danger."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    target = world.facts["target_cfg"]
    gadget = world.facts["gadget_cfg"]
    tags = {"clover", "coil", "fizzle", "misunderstanding", "teamwork"}
    if target.material == "metal":
        tags.add("magnet")
    if target.material in {"fabric", "light"}:
        tags.add("fabric")
    for tag in gadget.tags:
        if tag == "metal":
            tags.add("magnet")
        if tag == "fabric":
            tags.add("fabric")
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
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {eid:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="park",
        target="balloon",
        gadget="loop_launcher",
        hero_name="Maya",
        hero_gender="girl",
        sidekick_name="Theo",
        sidekick_gender="boy",
        mentor="mother",
        delay=0,
    ),
    StoryParams(
        setting="schoolyard",
        target="lunchbox",
        gadget="magnet_coil",
        hero_name="Leo",
        hero_gender="boy",
        sidekick_name="Ivy",
        sidekick_gender="girl",
        mentor="father",
        delay=0,
    ),
    StoryParams(
        setting="backyard",
        target="robot",
        gadget="sky_saver",
        hero_name="Nora",
        hero_gender="girl",
        sidekick_name="Finn",
        sidekick_gender="boy",
        mentor="mother",
        delay=0,
    ),
    StoryParams(
        setting="park",
        target="balloon",
        gadget="loop_launcher",
        hero_name="Ruby",
        hero_gender="girl",
        sidekick_name="Max",
        sidekick_gender="boy",
        mentor="father",
        delay=1,
    ),
    StoryParams(
        setting="park",
        target="balloon",
        gadget="loop_launcher",
        hero_name="Ava",
        hero_gender="girl",
        sidekick_name="Sam",
        sidekick_gender="boy",
        mentor="mother",
        delay=2,
    ),
]


ASP_RULES = r"""
valid(S,T,G) :- setting(S), target(T), gadget(G), perch_ok(S,T), works_on(G,M), material(T,M), reach(G,R), difficulty(T,D), R >= D.

need(T,N) :- chosen_target(T), difficulty(T,D), delay(L), drifts(T), N = D + L + 1.
need(T,N) :- chosen_target(T), difficulty(T,D), delay(L), not drifts(T), N = D + L.

rescued :- chosen_target(T), chosen_gadget(G), need(T,N), reach(G,R), R >= N.
outcome(rescued) :- rescued.
outcome(lost) :- not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for perch in sorted(setting.perch_kinds):
            lines.append(asp.fact("supports", sid, perch))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("difficulty", tid, target.difficulty))
        lines.append(asp.fact("material", tid, target.material))
        lines.append(asp.fact("perch", tid, target.perch))
        if target.drifts:
            lines.append(asp.fact("drifts", tid))
    for gid, gadget in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        lines.append(asp.fact("reach", gid, gadget.reach))
        for mat in sorted(gadget.works_on):
            lines.append(asp.fact("works_on", gid, mat))
    for sid, setting in SETTINGS.items():
        for tid, target in TARGETS.items():
            if target.perch in setting.perch_kinds:
                lines.append(asp.fact("perch_ok", sid, tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_gadget", params.gadget),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
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
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a superhero misunderstanding around a fizzle, a coil, and a clover patch."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time lost because of the misunderstanding")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include QA output")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target is not None and args.gadget is not None:
        target = TARGETS[args.target]
        gadget = GADGETS[args.gadget]
        if not valid_for_story(gadget, target):
            raise StoryError(explain_rejection(gadget, target))
    if args.setting is not None and args.target is not None:
        if TARGETS[args.target].perch not in SETTINGS[args.setting].perch_kinds:
            raise StoryError(
                f"(No story: {TARGETS[args.target].the} cannot reasonably be on the "
                f"{TARGETS[args.target].perch} in {SETTINGS[args.setting].place}.)"
            )

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.target is None or combo[1] == args.target)
        and (args.gadget is None or combo[2] == args.gadget)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, target_id, gadget_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    sidekick_name = args.sidekick_name or _pick_name(rng, sidekick_gender, avoid=hero_name)
    mentor = args.mentor or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])

    return StoryParams(
        setting=setting_id,
        target=target_id,
        gadget=gadget_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        mentor=mentor,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        target = TARGETS[params.target]
        gadget = GADGETS[params.gadget]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]})") from None

    if target.perch not in setting.perch_kinds or not valid_for_story(gadget, target):
        raise StoryError(explain_rejection(gadget, target))

    world = tell(
        setting=setting,
        target_cfg=target,
        gadget_cfg=gadget,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        mentor_type=params.mentor,
        delay=params.delay,
    )

    story_text = world.render()
    story_text = story_text.replace(" {hero} ", f' {params.hero_name} ')

    # Repair launch lines after rendering, since the configs deliberately keep a simple placeholder.
    hero_label = params.hero_name
    story_text = story_text.replace('{hero}', hero_label)

    return StorySample(
        params=params,
        story=story_text,
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
        print(f"{len(combos)} compatible (setting, target, gadget) combos:\n")
        for setting, target, gadget in combos:
            print(f"  {setting:10} {target:10} {gadget}")
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
            header = f"### {p.hero_name} & {p.sidekick_name}: {p.target} in {p.setting} with {p.gadget} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
