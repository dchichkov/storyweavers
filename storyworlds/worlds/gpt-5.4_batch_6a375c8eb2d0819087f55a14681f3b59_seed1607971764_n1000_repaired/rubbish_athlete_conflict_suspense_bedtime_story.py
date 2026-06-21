#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rubbish_athlete_conflict_suspense_bedtime_story.py
==============================================================================

A standalone story world about a little athlete, a piece of rubbish on a path,
and the tense choice between hurrying ahead and making the path safe first.

This domain aims for a gentle bedtime-story shape:

- a cozy evening setup
- a real conflict: the child wants one last dash before bed
- suspense: wind shifts the rubbish into danger
- a calm resolution that proves what changed before sleep

Run it
------
    python storyworlds/worlds/gpt-5.4/rubbish_athlete_conflict_suspense_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/rubbish_athlete_conflict_suspense_bedtime_story.py --place park_track --rubbish banana_peel --tool litter_picker
    python storyworlds/worlds/gpt-5.4/rubbish_athlete_conflict_suspense_bedtime_story.py --tool toy_rake
    python storyworlds/worlds/gpt-5.4/rubbish_athlete_conflict_suspense_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/rubbish_athlete_conflict_suspense_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rubbish_athlete_conflict_suspense_bedtime_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
EAGER_INIT = 6.0
STEADY_TRAITS = {"steady", "careful", "calm", "thoughtful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Place:
    id: str
    label: str
    opening: str
    lane: str
    edge: str
    ending: str
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
class Rubbish:
    id: str
    label: str
    phrase: str
    hazard: str
    drift: str
    risk: int
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
    handles: set[str] = field(default_factory=set)
    success: str = ""
    fail: str = ""
    qa_text: str = ""
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
class StoryParams:
    place: str
    rubbish: str
    tool: str
    athlete: str
    athlete_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    wind: int = 0
    athlete_age: int = 6
    helper_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    blanket: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"athlete", "helper"}]


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


def _r_path_danger(world: World) -> list[str]:
    out: list[str] = []
    rubbish = world.get("rubbish")
    lane = world.get("lane")
    if rubbish.meters["on_lane"] < THRESHOLD:
        return out
    sig = ("path_danger", rubbish.id, int(rubbish.meters["obstacle"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lane.meters["danger"] += rubbish.meters["obstacle"]
    for kid in world.kids():
        kid.memes["unease"] += 1
    out.append("__danger__")
    return out


def _r_stumble(world: World) -> list[str]:
    out: list[str] = []
    athlete = world.get("athlete")
    lane = world.get("lane")
    if athlete.meters["running"] < THRESHOLD or lane.meters["danger"] < THRESHOLD:
        return out
    sig = ("stumble", athlete.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    athlete.meters["stumble"] += 1
    athlete.meters["scrape"] += 1
    athlete.memes["fear"] += 1
    world.get("helper").memes["fear"] += 1
    out.append("__stumble__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="path_danger", tag="physical", apply=_r_path_danger),
    Rule(name="stumble", tag="physical", apply=_r_stumble),
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


PLACES = {
    "park_track": Place(
        id="park_track",
        label="the little park track",
        opening="Beside the little park track, the evening air smelled of grass and sleep.",
        lane="the red running lane",
        edge="the low fence by the flowerbeds",
        ending="the track lay quiet under the moon, ready for tomorrow",
        tags={"park", "running"},
    ),
    "school_path": Place(
        id="school_path",
        label="the schoolyard running path",
        opening="At the schoolyard path, the windows were golden and the sky was turning purple.",
        lane="the chalk-marked running path",
        edge="the bike rack",
        ending="the path looked neat and patient in the moonlight",
        tags={"school", "running"},
    ),
    "garden_lane": Place(
        id="garden_lane",
        label="the garden lane",
        opening="In the long garden lane, crickets sang while shadows stretched softly across the stones.",
        lane="the narrow garden lane",
        edge="the bean trellis",
        ending="the lane was still and silver, safe for another day",
        tags={"garden", "running"},
    ),
}

RUBBISH = {
    "banana_peel": Rubbish(
        id="banana_peel",
        label="banana peel",
        phrase="a curled banana peel",
        hazard="slippery",
        drift="slid and skittered",
        risk=2,
        tags={"rubbish", "slip", "banana_peel"},
    ),
    "paper_cup": Rubbish(
        id="paper_cup",
        label="paper cup",
        phrase="a squashed paper cup",
        hazard="crumpled",
        drift="rattled and rolled",
        risk=1,
        tags={"rubbish", "paper_cup", "litter"},
    ),
    "plastic_bag": Rubbish(
        id="plastic_bag",
        label="plastic bag",
        phrase="a thin plastic bag",
        hazard="tangly",
        drift="whispered and flew",
        risk=2,
        tags={"rubbish", "plastic_bag", "litter"},
    ),
    "bottle_cap": Rubbish(
        id="bottle_cap",
        label="bottle cap",
        phrase="a shiny bottle cap",
        hazard="hard",
        drift="clicked and spun",
        risk=1,
        tags={"rubbish", "bottle_cap", "litter"},
    ),
}

TOOLS = {
    "litter_picker": Tool(
        id="litter_picker",
        label="litter picker",
        phrase="a long litter picker",
        sense=3,
        power=3,
        handles={"banana_peel", "paper_cup", "plastic_bag", "bottle_cap"},
        success="reached out with the litter picker, pinched up the {rubbish}, and dropped it into the rubbish sack",
        fail="tried to catch the {rubbish} with the litter picker, but the wind kept dancing it away",
        qa_text="used the litter picker to pick up the {rubbish} and put it in the rubbish sack",
        tags={"litter_picker", "cleanup"},
    ),
    "broom": Tool(
        id="broom",
        label="broom",
        phrase="a small straw broom",
        sense=3,
        power=2,
        handles={"paper_cup", "bottle_cap"},
        success="swept the {rubbish} off the lane and into the waiting rubbish sack",
        fail="swept at the {rubbish}, but it kept skipping back across the lane",
        qa_text="swept the {rubbish} off the lane and into the rubbish sack",
        tags={"broom", "cleanup"},
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="a pair of garden gloves",
        sense=2,
        power=2,
        handles={"banana_peel", "plastic_bag", "paper_cup", "bottle_cap"},
        success="pulled on the gloves, scooped up the {rubbish}, and tucked it into the rubbish sack",
        fail="reached for the {rubbish}, but it slipped and fluttered away before the lane was clear",
        qa_text="used the gloves to pick up the {rubbish} and put it into the rubbish sack",
        tags={"gloves", "cleanup"},
    ),
    "toy_rake": Tool(
        id="toy_rake",
        label="toy rake",
        phrase="a tiny toy rake",
        sense=1,
        power=1,
        handles={"paper_cup"},
        success="nudged the {rubbish} with the toy rake until it fell aside",
        fail="poked at the {rubbish} with the toy rake, but it was far too fussy and slow",
        qa_text="nudged the {rubbish} aside with the toy rake",
        tags={"toy_rake", "cleanup"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Theo", "Jack", "Finn", "Noah", "Eli", "Owen"]
TRAITS = ["steady", "careful", "calm", "thoughtful", "patient", "gentle"]
BLANKETS = ["star blanket", "soft blue quilt", "moon-pattern blanket", "striped blanket"]

KNOWLEDGE = {
    "athlete": [
        (
            "What is an athlete?",
            "An athlete is a person who practices a sport or a physical game, like running or jumping. Athletes get stronger by practicing carefully and listening to safety rules.",
        )
    ],
    "rubbish": [
        (
            "What is rubbish?",
            "Rubbish is trash that does not belong on the ground. It should be put in a bin so places stay clean and safe.",
        )
    ],
    "cleanup": [
        (
            "Why should rubbish be picked up from a path?",
            "Rubbish on a path can make people slip, trip, or get tangled. Cleaning it up helps everyone walk or run safely.",
        )
    ],
    "litter_picker": [
        (
            "What is a litter picker?",
            "A litter picker is a long tool that helps you pick up rubbish without touching it. Grown-ups or careful helpers use it to keep places tidy.",
        )
    ],
    "broom": [
        (
            "What does a broom do?",
            "A broom sweeps light things off the ground into a pile. It works best when the mess is not too sticky or blowy.",
        )
    ],
    "gloves": [
        (
            "Why do people wear gloves for cleanup?",
            "Gloves protect your hands while you pick things up. They can help when something is slippery or crinkly.",
        )
    ],
    "running": [
        (
            "Why do runners look where they are going?",
            "Runners look ahead so they can see puddles, toys, or rubbish on the ground. Seeing danger early helps them stop or go around it.",
        )
    ],
    "slip": [
        (
            "Why is a banana peel slippery?",
            "A banana peel can be soft and slick, so a shoe can slide on it. That is why it should never be left on a walking or running path.",
        )
    ],
    "litter": [
        (
            "Why is litter bad for parks and schoolyards?",
            "Litter makes a place look messy, and it can bother animals or people using the space. Putting it in a bin keeps the place kinder for everyone.",
        )
    ],
}
KNOWLEDGE_ORDER = ["athlete", "rubbish", "cleanup", "running", "slip", "litter_picker", "broom", "gloves", "litter"]


def handles_rubbish(tool: Tool, rubbish: Rubbish) -> bool:
    return rubbish.id in tool.handles


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for rubbish_id, rubbish in RUBBISH.items():
            for tool_id, tool in TOOLS.items():
                if handles_rubbish(tool, rubbish) and tool.sense >= SENSE_MIN:
                    combos.append((place_id, rubbish_id, tool_id))
    return combos


def steady_score(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def would_avert(relation: str, athlete_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > athlete_age
    authority = steady_score(trait) + 1.0 + (3.0 if helper_older else 0.0)
    return helper_older and authority > EAGER_INIT


def hazard_severity(rubbish: Rubbish, wind: int) -> int:
    return rubbish.risk + wind


def is_cleared_in_time(tool: Tool, rubbish: Rubbish, wind: int) -> bool:
    return tool.power >= hazard_severity(rubbish, wind)


def explain_rejection(rubbish: Rubbish, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). Choose a safer cleanup tool.)"
        )
    return (
        f"(No story: {tool.label} is not a reasonable way to clear a {rubbish.label} "
        f"from a running lane in this world. Pick a tool that can really handle that rubbish.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.athlete_age, params.helper_age, params.trait):
        return "averted"
    return "cleared" if is_cleared_in_time(TOOLS[params.tool], RUBBISH[params.rubbish], params.wind) else "tumble"


def predict_stumble(world: World, rubbish_id: str) -> dict:
    sim = world.copy()
    rubbish = sim.get(rubbish_id)
    athlete = sim.get("athlete")
    rubbish.meters["on_lane"] = 1.0
    propagate(sim, narrate=False)
    athlete.meters["running"] = 1.0
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("lane").meters["danger"],
        "stumble": athlete.meters["stumble"] >= THRESHOLD,
    }


def bedtime_opening(world: World, place: Place, athlete: Entity, helper: Entity) -> None:
    athlete.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{place.opening} {athlete.id} loved pretending to be a real athlete, "
        f"counting soft steps and quick breaths in the dimming light."
    )
    world.say(
        f"{helper.id} sat near {place.edge} and listened as the evening grew quieter and quieter."
    )


def last_dash(world: World, place: Place, athlete: Entity) -> None:
    athlete.memes["eager"] += 1
    world.say(
        f'"Just one last dash along {place.lane}," {athlete.id} whispered. '
        f'The moon was beginning to shine, and the lane looked silver and inviting.'
    )


def spot_rubbish(world: World, helper: Entity, rubbish_cfg: Rubbish) -> None:
    world.say(
        f"But {helper.id} noticed {rubbish_cfg.phrase} resting right in the path like a tiny, troublesome secret."
    )


def warn(world: World, helper: Entity, athlete: Entity, parent: Entity, rubbish_cfg: Rubbish) -> None:
    pred = predict_stumble(world, "rubbish")
    world.facts["predicted_danger"] = pred["danger"]
    helper.memes["steady"] += 1
    extra = ""
    if helper.memes["steady"] >= 6:
        extra = f" {helper.pronoun().capitalize()} sounded so sure that even the crickets seemed to pause."
    world.say(
        f'"Wait," {helper.id} said. "That {rubbish_cfg.label} is on the lane. '
        f'If you run now, you could slip or stumble, and {parent.label_word} would have to help in the dark."{extra}'
    )


def back_down(world: World, athlete: Entity, helper: Entity, parent: Entity, place: Place) -> None:
    athlete.memes["eager"] = 0.0
    athlete.memes["relief"] += 1
    helper.memes["relief"] += 1
    relation_word = "big brother" if helper.type == "boy" else "big sister"
    world.say(
        f'{athlete.id} opened {athlete.pronoun("possessive")} mouth to argue, but {helper.id} was '
        f'{athlete.pronoun("possessive")} {relation_word}, and the warning landed in {athlete.pronoun("possessive")} chest.'
    )
    world.say(
        f'"You\'re right," {athlete.pronoun()} said at last. "A good athlete watches the lane first."'
    )
    world.say(
        f"They walked slowly to the edge of {place.lane} instead of racing across it."
    )


def defy(world: World, athlete: Entity, helper: Entity) -> None:
    athlete.memes["defiance"] += 1
    world.say(
        f'"It is only one little bit of rubbish," {athlete.id} said, and {athlete.pronoun()} leaned forward to run.'
    )
    if athlete.attrs.get("relation") == "siblings" and athlete.age > helper.age:
        world.say(
            f"{helper.id} hurried after {athlete.pronoun('object')}, still trying to make {athlete.pronoun('object')} stop."
        )


def gust(world: World, place: Place, rubbish_ent: Entity, rubbish_cfg: Rubbish, wind: int) -> None:
    rubbish_ent.meters["obstacle"] = float(hazard_severity(rubbish_cfg, wind))
    rubbish_ent.meters["on_lane"] = 1.0
    propagate(world, narrate=False)
    moon = ["a small breeze", "a firmer breeze", "a restless gust"][wind]
    world.say(
        f"Then {moon} slipped over {place.lane}, and the {rubbish_cfg.label} {rubbish_cfg.drift} straight into the runner's line."
    )
    world.say("For one hushy second, nobody knew whether the next footstep would land safely.")


def alarm(world: World, helper: Entity, athlete: Entity) -> None:
    helper.memes["fear"] += 1
    world.say(f'"Stop, {athlete.id}!" {helper.id} cried.')


def clear_path(world: World, parent: Entity, tool: Tool, rubbish_cfg: Rubbish) -> None:
    body = tool.success.replace("{rubbish}", rubbish_cfg.label)
    world.get("rubbish").meters["on_lane"] = 0.0
    world.get("rubbish").meters["obstacle"] = 0.0
    world.get("lane").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} stepped in at once, {body}."
    )
    world.say(
        "The lane looked open again, and the sharp feeling in the air loosened."
    )


def fail_clear(world: World, parent: Entity, tool: Tool, rubbish_cfg: Rubbish) -> None:
    body = tool.fail.replace("{rubbish}", rubbish_cfg.label)
    world.say(f"{parent.label_word.capitalize()} {body}.")
    athlete = world.get("athlete")
    athlete.meters["running"] = 1.0
    propagate(world, narrate=False)


def tumble(world: World, athlete: Entity, helper: Entity, rubbish_cfg: Rubbish) -> None:
    athlete.memes["fear"] += 1
    helper.memes["fear"] += 1
    world.say(
        f"{athlete.id}'s foot met the {rubbish_cfg.label}, and {athlete.pronoun()} gave a small surprised tumble onto {athlete.pronoun('possessive')} hands and knees."
    )
    world.say(
        "It was not a terrible fall, but it was enough to make the whole evening go very still."
    )


def gentle_lesson(world: World, parent: Entity, athlete: Entity, helper: Entity) -> None:
    athlete.memes["love"] += 1
    athlete.memes["lesson"] += 1
    helper.memes["love"] += 1
    helper.memes["lesson"] += 1
    athlete.memes["fear"] = 0.0
    helper.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} knelt beside them and pulled both children into a warm, close hug."
    )
    world.say(
        f'"Fast feet are wonderful," {parent.pronoun()} said softly, "but wise feet look first. '
        f'A true athlete does not race past danger."'
    )


def tidy_together(world: World, parent: Entity, athlete: Entity, helper: Entity, tool: Tool, rubbish_cfg: Rubbish) -> None:
    athlete.memes["care"] += 1
    helper.memes["care"] += 1
    world.say(
        f"After that, they all helped with the last little bit of rubbish together until the path was tidy."
    )
    world.say(
        f'{athlete.id} held the sack open while {helper.id} watched the edges of the lane, and soon there was nothing left to catch a running shoe.'
    )


def bedtime_end(world: World, place: Place, athlete: Entity, helper: Entity, parent: Entity, blanket: str, outcome: str) -> None:
    athlete.memes["sleepy"] += 1
    helper.memes["sleepy"] += 1
    if outcome == "averted":
        first = (
            f"Later, tucked under the {blanket}, {athlete.id} told {helper.id} that stopping had felt braver than dashing."
        )
    elif outcome == "cleared":
        first = (
            f"Later, tucked under the {blanket}, {athlete.id} remembered how close the lane had come to staying dangerous and felt grateful for the pause."
        )
    else:
        first = (
            f"Later, tucked under the {blanket}, {athlete.id} touched the little bandage on {athlete.pronoun('possessive')} knee and promised to look before running tomorrow."
        )
    world.say(first)
    world.say(
        f"Outside, {place.ending}, and inside the house everyone was quiet, safe, and ready for sleep."
    )


def tell(
    place: Place,
    rubbish_cfg: Rubbish,
    tool: Tool,
    athlete_name: str = "Leo",
    athlete_gender: str = "boy",
    helper_name: str = "Lily",
    helper_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "steady",
    wind: int = 0,
    athlete_age: int = 6,
    helper_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    blanket: str = "star blanket",
) -> World:
    world = World()
    athlete = world.add(
        Entity(
            id="athlete",
            kind="character",
            type=athlete_gender,
            label=athlete_name,
            role="athlete",
            age=athlete_age,
            attrs={"relation": relation, "name": athlete_name},
            traits=["eager"],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
            age=helper_age,
            attrs={"relation": relation, "name": helper_name},
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    lane = world.add(
        Entity(
            id="lane",
            kind="thing",
            type="lane",
            label=place.lane,
            role="lane",
        )
    )
    rubbish_ent = world.add(
        Entity(
            id="rubbish",
            kind="thing",
            type="rubbish",
            label=rubbish_cfg.label,
            role="rubbish",
            tags=set(rubbish_cfg.tags),
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            role="tool",
            tags=set(tool.tags),
        )
    )

    athlete.id = athlete_name
    helper.id = helper_name
    parent.id = "Parent"
    world.entities = {
        athlete_name: athlete,
        helper_name: helper,
        "Parent": parent,
        "lane": lane,
        "rubbish": rubbish_ent,
        "tool": tool_ent,
    }

    athlete.memes["eager"] = EAGER_INIT
    helper.memes["trust"] = float(trust)
    helper.memes["steady"] = steady_score(trait)
    lane.meters["danger"] = 0.0
    rubbish_ent.meters["on_lane"] = 0.0
    rubbish_ent.meters["obstacle"] = 0.0
    athlete.meters["running"] = 0.0
    athlete.meters["stumble"] = 0.0
    athlete.meters["scrape"] = 0.0

    world.facts["blanket"] = blanket

    bedtime_opening(world, place, athlete, helper)
    last_dash(world, place, athlete)
    spot_rubbish(world, helper, rubbish_cfg)

    world.para()
    warn(world, helper, athlete, parent, rubbish_cfg)
    averted = would_avert(relation, athlete_age, helper_age, trait)

    if averted:
        back_down(world, athlete, helper, parent, place)
        world.para()
        clear_path(world, parent, tool, rubbish_cfg)
        gentle_lesson(world, parent, athlete, helper)
        tidy_together(world, parent, athlete, helper, tool, rubbish_cfg)
        world.para()
        bedtime_end(world, place, athlete, helper, parent, blanket, "averted")
        outcome = "averted"
    else:
        defy(world, athlete, helper)
        world.para()
        gust(world, place, rubbish_ent, rubbish_cfg, wind)
        alarm(world, helper, athlete)
        contained = is_cleared_in_time(tool, rubbish_cfg, wind)
        world.para()
        if contained:
            clear_path(world, parent, tool, rubbish_cfg)
            athlete.memes["relief"] += 1
            helper.memes["relief"] += 1
            world.say(
                f"{athlete_name} stopped so fast that {athlete.pronoun('possessive')} toes curled over the front of {athlete.pronoun('possessive')} shoes."
            )
            gentle_lesson(world, parent, athlete, helper)
            tidy_together(world, parent, athlete, helper, tool, rubbish_cfg)
            world.para()
            bedtime_end(world, place, athlete, helper, parent, blanket, "cleared")
            outcome = "cleared"
        else:
            fail_clear(world, parent, tool, rubbish_cfg)
            tumble(world, athlete, helper, rubbish_cfg)
            world.say(
                f"{parent.label_word.capitalize()} brushed the dust from {athlete_name}'s pajamas and carried the last of the rubbish away from the lane."
            )
            gentle_lesson(world, parent, athlete, helper)
            world.para()
            bedtime_end(world, place, athlete, helper, parent, blanket, "tumble")
            outcome = "tumble"

    world.facts.update(
        place=place,
        rubbish_cfg=rubbish_cfg,
        tool_cfg=tool,
        athlete=athlete,
        helper=helper,
        parent=parent,
        lane=lane,
        relation=relation,
        outcome=outcome,
        wind=wind,
        severity=hazard_severity(rubbish_cfg, wind),
        averted=outcome == "averted",
        tumbled=outcome == "tumble",
        cleared=outcome == "cleared",
    )
    return world


def pair_noun(athlete: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if athlete.type == "boy" and helper.type == "boy":
            return "two brothers"
        if athlete.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    athlete = f["athlete"]
    helper = f["helper"]
    parent = f["parent"]
    rubbish_cfg = f["rubbish_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    name = athlete.label
    helper_name = helper.label
    if outcome == "averted":
        return [
            f'Write a bedtime story for a 3-to-5-year-old that includes the words "rubbish" and "athlete", where a child wants one last run but an older sibling helps them stop in time.',
            f"Tell a gentle suspense story set at {place.label} where {name} wants to race, {helper_name} notices rubbish on the lane, and they choose safety before sleep.",
            f"Write a cozy story where {name} learns that a careful athlete checks the path before running, and the ending feels calm enough for bedtime.",
        ]
    if outcome == "cleared":
        return [
            f'Write a bedtime story for a 3-to-5-year-old that includes the words "rubbish" and "athlete", with a tense moment on a running lane and a calm cleanup before anyone gets hurt.',
            f"Tell a suspenseful but gentle story where {name} almost runs too soon, {helper_name} warns about the rubbish, and {parent.label_word} clears the path just in time.",
            f"Write a story about an eager little athlete who learns to pause, tidy danger away, and go to sleep feeling wiser.",
        ]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "rubbish" and "athlete", with conflict, suspense, and a soft lesson after a small tumble.',
        f"Tell a gentle cautionary story set at {place.label} where {name} ignores a warning about rubbish on the lane and learns why careful runners look first.",
        f"Write a cozy nighttime story where a child wants one last dash, danger appears in the dark, and love matters more than winning or hurrying.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    athlete = f["athlete"]
    helper = f["helper"]
    parent = f["parent"]
    rubbish_cfg = f["rubbish_cfg"]
    tool = f["tool_cfg"]
    place = f["place"]
    pair = pair_noun(athlete, helper, f["relation"])
    name = athlete.label
    helper_name = helper.label
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {name} and {helper_name}, and their {pw}. {name} wanted to be a brave little athlete before bedtime.",
        ),
        (
            f"Why did {helper_name} tell {name} to wait?",
            f"{helper_name} saw {rubbish_cfg.phrase} on the running lane and knew it could make {name} slip or stumble. The warning came from noticing danger before the race began.",
        ),
        (
            f"What made the moment feel suspenseful?",
            f"A breeze pushed the rubbish into the runner's path just as {name} was about to move. For a second, nobody knew whether the next step would be safe.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How did {name} solve the problem?",
                f"{name} listened instead of running right away. Then {pw} cleared the rubbish, so the path was safe and the lesson came before any fall could happen.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly in bed, with {name} feeling proud for stopping in time. The calm ending shows that being a wise athlete matters more than rushing.",
            )
        )
    elif f["outcome"] == "cleared":
        qa.append(
            (
                f"How did {pw} help?",
                f"{pw.capitalize()} {tool.qa_text.replace('{rubbish}', rubbish_cfg.label)}. That quick cleanup took the danger off the lane before {name} ran into it.",
            )
        )
        qa.append(
            (
                f"What did {name} learn?",
                f"{name} learned that a real athlete looks first and runs second. The close call made the lesson feel important without anyone getting hurt.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when the path was not cleared in time?",
                f"{name} tripped on the {rubbish_cfg.label} and had a small tumble. It was not a terrible fall, but it showed how quickly one careless moment can change a game.",
            )
        )
        qa.append(
            (
                f"How was the ending still gentle?",
                f"{pw.capitalize()} comforted both children, cleaned up the lane, and tucked {name} into bed. The story ends with safety, love, and a promise to look before running tomorrow.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"athlete", "rubbish", "cleanup", "running"}
    tags |= set(f["rubbish_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
handles(T, R) :- tool(T), rubbish(R), can_handle(T, R).
sensible(T)   :- tool(T), sense(T, S), sense_min(M), S >= M.
valid(P, R, T) :- place(P), rubbish(R), tool(T), handles(T, R), sensible(T).

% --- outcome model ---------------------------------------------------------
steady_now(T)  :- trait(T), is_steady(T).
init_steady(5) :- trait(T), steady_now(T).
init_steady(3) :- trait(T), not steady_now(T).

helper_older :- relation(siblings), athlete_age(A), helper_age(H), H > A.
bonus(3)     :- helper_older.
bonus(0)     :- not helper_older.
authority(S + 1 + B) :- init_steady(S), bonus(B).
averted :- helper_older, authority(A), eager_init(E), A > E.

severity(Risk + W) :- chosen_rubbish(R), risk(R, Risk), wind(W).
cleared_in_time :- chosen_tool(T), power(T, P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(cleared) :- not averted, cleared_in_time.
outcome(tumble)  :- not averted, not cleared_in_time.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid, rubbish in RUBBISH.items():
        lines.append(asp.fact("rubbish", rid))
        lines.append(asp.fact("risk", rid, rubbish.risk))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        lines.append(asp.fact("power", tid, tool.power))
        for rid in sorted(tool.handles):
            lines.append(asp.fact("can_handle", tid, rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("eager_init", int(EAGER_INIT)))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("is_steady", trait))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_rubbish", params.rubbish),
            asp.fact("chosen_tool", params.tool),
            asp.fact("wind", params.wind),
            asp.fact("relation", params.relation),
            asp.fact("athlete_age", params.athlete_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        place="park_track",
        rubbish="banana_peel",
        tool="litter_picker",
        athlete="Leo",
        athlete_gender="boy",
        helper="Mia",
        helper_gender="girl",
        parent="mother",
        trait="careful",
        wind=0,
        athlete_age=6,
        helper_age=4,
        relation="siblings",
        trust=6,
        blanket="star blanket",
    ),
    StoryParams(
        place="school_path",
        rubbish="plastic_bag",
        tool="gloves",
        athlete="Ava",
        athlete_gender="girl",
        helper="Ben",
        helper_gender="boy",
        parent="father",
        trait="steady",
        wind=1,
        athlete_age=5,
        helper_age=7,
        relation="siblings",
        trust=5,
        blanket="soft blue quilt",
    ),
    StoryParams(
        place="garden_lane",
        rubbish="paper_cup",
        tool="broom",
        athlete="Noah",
        athlete_gender="boy",
        helper="Lucy",
        helper_gender="girl",
        parent="mother",
        trait="patient",
        wind=2,
        athlete_age=6,
        helper_age=5,
        relation="friends",
        trust=4,
        blanket="moon-pattern blanket",
    ),
    StoryParams(
        place="park_track",
        rubbish="banana_peel",
        tool="gloves",
        athlete="Rose",
        athlete_gender="girl",
        helper="Sam",
        helper_gender="boy",
        parent="father",
        trait="calm",
        wind=1,
        athlete_age=7,
        helper_age=6,
        relation="friends",
        trust=7,
        blanket="striped blanket",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a little athlete, some rubbish, and a tense choice to stop or hurry."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rubbish", choices=RUBBISH)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--wind", type=int, choices=[0, 1, 2], help="evening wind strength")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rubbish and args.tool:
        rubbish = RUBBISH[args.rubbish]
        tool = TOOLS[args.tool]
        if not (handles_rubbish(tool, rubbish) and tool.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(rubbish, tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        rubbish = RUBBISH[args.rubbish] if args.rubbish else next(iter(RUBBISH.values()))
        raise StoryError(explain_rejection(rubbish, TOOLS[args.tool]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.rubbish is None or combo[1] == args.rubbish)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, rubbish_id, tool_id = rng.choice(sorted(combos))
    athlete, athlete_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=athlete)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    wind = args.wind if args.wind is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    athlete_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    blanket = rng.choice(BLANKETS)
    return StoryParams(
        place=place_id,
        rubbish=rubbish_id,
        tool=tool_id,
        athlete=athlete,
        athlete_gender=athlete_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        wind=wind,
        athlete_age=athlete_age,
        helper_age=helper_age,
        relation=relation,
        trust=trust,
        blanket=blanket,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.rubbish not in RUBBISH:
        raise StoryError(f"(Unknown rubbish: {params.rubbish})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    rubbish = RUBBISH[params.rubbish]
    tool = TOOLS[params.tool]
    if not handles_rubbish(tool, rubbish) or tool.sense < SENSE_MIN:
        raise StoryError(explain_rejection(rubbish, tool))

    world = tell(
        place=PLACES[params.place],
        rubbish_cfg=rubbish,
        tool=tool,
        athlete_name=params.athlete,
        athlete_gender=params.athlete_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
        wind=params.wind,
        athlete_age=params.athlete_age,
        helper_age=params.helper_age,
        relation=params.relation,
        trust=params.trust,
        blanket=params.blanket,
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {tool.id for tool in sensible_tools()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible tools match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible tools: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("empty story")
        emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: smoke generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, rubbish, tool) combos:\n")
        for place_id, rubbish_id, tool_id in combos:
            print(f"  {place_id:12} {rubbish_id:12} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.athlete} & {p.helper}: {p.rubbish} at {p.place} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
