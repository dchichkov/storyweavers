#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/question_paint_foreshadowing_inner_monologue_rhyme_space.py
=======================================================================================

A standalone storyworld in a small space-adventure domain.

Premise
-------
A child on a moon station hears a little service robot ask a question about where
to go. Wanting to help fast, the child decides to paint a bright guide sign.
Sometimes the wiser helper talks the child out of rushing. Sometimes the child
rushes, a dust gust or drifting paint makes trouble, and a calm grown-up fixes
the plan in a more sensible way. The story always ends with a changed world:
either a safe painted sign glowing where it belongs, or a postponed mission that
teaches the crew to slow down and suit up first.

The domain uses:
- the required words "question" and "paint"
- foreshadowing (early hints of dust / wobble / warning lights)
- inner monologue (the hero's thought before the choice)
- rhyme (short child-facing lines in the robot's speech and ending)

Run it
------
python storyworlds/worlds/gpt-5.4/question_paint_foreshadowing_inner_monologue_rhyme_space.py
python storyworlds/worlds/gpt-5.4/question_paint_foreshadowing_inner_monologue_rhyme_space.py --surface rover_side --paint star_paint
python storyworlds/worlds/gpt-5.4/question_paint_foreshadowing_inner_monologue_rhyme_space.py --paint watercolors
python storyworlds/worlds/gpt-5.4/question_paint_foreshadowing_inner_monologue_rhyme_space.py --all --qa
python storyworlds/worlds/gpt-5.4/question_paint_foreshadowing_inner_monologue_rhyme_space.py --verify
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
SENSE_MIN = 2
COURAGE_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "patient"}


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
    inside: bool = True
    exterior: bool = False
    surface_type: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
    station: str
    robot_name: str
    robot_kind: str
    question_text: str
    answer_place: str
    sign_shape: str
    opening: str
    ending: str
    rhyme_open: str
    rhyme_close: str
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
class Surface:
    id: str
    label: str
    the: str
    place: str
    surface_type: str
    exterior: bool
    risk: int
    paint_phrase: str
    ending_glow: str
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
class Paint:
    id: str
    label: str
    phrase: str
    works_on: set[str]
    quick: bool
    shimmer: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "helper"}]

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


def _r_gust(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    surface = world.get("surface")
    if hero.meters["painting"] < THRESHOLD:
        return out
    if not surface.exterior:
        return out
    sig = ("gust", surface.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("station").meters["danger"] += 1
    hero.memes["fear"] += 1
    world.get("helper").memes["worry"] += 1
    out.append("__gust__")
    return out


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    surface = world.get("surface")
    paint = world.get("paint")
    hero = world.get("hero")
    if hero.meters["painting"] < THRESHOLD:
        return out
    if surface.surface_type in set(paint.attrs.get("works_on", [])):
        return out
    sig = ("smear", surface.id, paint.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    surface.meters["smeared"] += 1
    hero.memes["frustration"] += 1
    out.append("__smear__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="gust", tag="physical", apply=_r_gust),
    Rule(name="smear", tag="physical", apply=_r_smear),
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


def paint_compatible(paint: Paint, surface: Surface) -> bool:
    return surface.surface_type in paint.works_on


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for mission_id in MISSIONS:
        for surface_id, surface in SURFACES.items():
            for paint_id, paint in PAINTS.items():
                if paint_compatible(paint, surface):
                    combos.append((mission_id, surface_id, paint_id))
    return combos


def severity_of(surface: Surface, delay: int) -> int:
    return surface.risk + delay


def is_contained(response: Response, surface: Surface, delay: int) -> bool:
    return response.power >= severity_of(surface, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = initial_caution(trait) + 1.0 + (3.0 if helper_older else 0.0)
    return helper_older and authority > COURAGE_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["painting"] += 1
    propagate(sim, narrate=False)
    surface = sim.get("surface")
    return {
        "gust": sim.get("station").meters["danger"] >= THRESHOLD,
        "smeared": surface.meters["smeared"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, mission: Mission) -> None:
    world.say(
        f"On {mission.station}, {hero.id} and {helper.id} loved pretending every hallway "
        f"was a star lane and every blinking button was part of {mission.opening}."
    )
    world.say(
        f"That afternoon, {mission.robot_name}, the {mission.robot_kind}, rolled up with a soft ping "
        f"and asked a question: \"{mission.question_text}\""
    )
    world.say(
        f"{mission.robot_name} always liked to rhyme. \"{mission.rhyme_open},\" {mission.pronoun if hasattr(mission, 'pronoun') else 'it'} chirped in a bright little voice."
    )


def frame_need(world: World, hero: Entity, mission: Mission, surface: Surface) -> None:
    hero.memes["excitement"] += 1
    world.say(
        f"{hero.id} clapped. \"We can help!\" {hero.pronoun()} said. "
        f"{hero.pronoun().capitalize()} wanted to paint {surface.paint_phrase} on {surface.the} "
        f"so the way to {mission.answer_place} would be easy to see."
    )


def foreshadow(world: World, helper: Entity, surface: Surface) -> None:
    if surface.exterior:
        world.say(
            f"Beyond the dome glass, silver dust curled around the station rails. "
            f"The tether rings on the wall gave a tiny clink, as if they already knew someone "
            f"might need them soon."
        )
    else:
        world.say(
            f"Even inside, the low station fans hummed and the lights blinked over the corridor. "
            f"It felt like the walls were waiting to see whether the sign would be made the careful way."
        )
    helper.memes["worry"] += 1


def tempt(world: World, hero: Entity, paint: Paint, surface: Surface) -> None:
    hero.memes["hurry"] += 1
    world.say(
        f"{hero.id} grabbed {paint.phrase}. In {hero.pronoun('possessive')} head, a quick thought skipped ahead: "
        f"Maybe I can do this fast and be back before anyone says wait."
    )
    if surface.exterior:
        world.say(
            f'"Just a quick dash, a quick splash, a bright little flash," {hero.pronoun()} whispered.'
        )
    else:
        world.say(
            f'"A bright sign, right on time," {hero.pronoun()} whispered.'
        )


def warn(world: World, helper: Entity, hero: Entity, mentor: Entity, mission: Mission,
         surface: Surface, paint: Paint) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_gust"] = pred["gust"]
    world.facts["predicted_smear"] = pred["smeared"]
    helper.memes["caution"] += 1
    parts: list[str] = []
    if pred["gust"]:
        parts.append(f"the dust could shove the brush away from {surface.the}")
    if pred["smeared"]:
        parts.append(f"{paint.label} could slide and smear on {surface.the}")
    clause = " and ".join(parts) if parts else "something could go wrong"
    world.say(
        f'{helper.id} touched {hero.id}\'s sleeve. "{hero.id}, wait," {helper.pronoun()} said. '
        f'"If you rush, {clause}. Why not ask {mentor.label_word} first?"'
    )
    world.say(
        f"{hero.id} looked at {surface.the} and then at {mission.robot_name}. "
        f"The little robot waited, wheels still, for the answer to its own question."
    )


def back_down(world: World, hero: Entity, helper: Entity, mentor: Entity,
              mission: Mission, surface: Surface, paint: Paint, response: Response) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{hero.id} took one breath, then another. "You are right," {hero.pronoun()} said. '
        f'"Fast is not always safe."'
    )
    world.say(
        f"They left {paint.phrase} on the worktable and went to {mentor.label_word} together. "
        f"{mentor.label_word.capitalize()} smiled, listened to the question, and chose a calmer plan."
    )
    world.para()
    safe_finish(world, hero, helper, mentor, mission, surface, response, averted=True)


def begin_painting(world: World, hero: Entity, surface: Entity, paint: Paint, surface_cfg: Surface) -> None:
    hero.meters["painting"] += 1
    surface.meters["wet_paint"] += 1
    propagate(world, narrate=False)
    if surface_cfg.exterior and surface.meters["smeared"] < THRESHOLD:
        world.say(
            f"{hero.id} hurried through the hatch with {paint.phrase}. "
            f"The stars looked close enough to tap, but the gray dust began to dance around {surface_cfg.the}."
        )
    elif surface_cfg.exterior:
        world.say(
            f"{hero.id} hurried through the hatch with {paint.phrase}. "
            f"Before the first arrow was done, the dust and the drifting paint tugged the line into a wobble."
        )
    elif surface.meters["smeared"] >= THRESHOLD:
        world.say(
            f"{hero.id} lifted the brush and made the first shining line, but the paint slid on {surface_cfg.the} "
            f"and bent the arrow into a crooked splash."
        )
    else:
        world.say(
            f"{hero.id} lifted the brush and started the first glowing line on {surface_cfg.the}."
        )


def alarm(world: World, helper: Entity, hero: Entity, surface: Surface, mentor: Entity) -> None:
    if world.get("station").meters["danger"] >= THRESHOLD or world.get("surface").meters["smeared"] >= THRESHOLD:
        cry = []
        if world.get("station").meters["danger"] >= THRESHOLD:
            cry.append("the dust is pushing the paint")
        if world.get("surface").meters["smeared"] >= THRESHOLD:
            cry.append(f"the sign is smearing on {surface.the}")
        joined = " and ".join(cry)
        world.say(f'"{mentor.label_word.upper()}! {joined}!" {helper.id} called.')


def rescue_success(world: World, mentor: Entity, response: Response, mission: Mission,
                   surface: Surface, paint: Paint) -> None:
    world.get("surface").meters["wet_paint"] = 0.0
    world.get("surface").meters["smeared"] = 0.0
    world.get("station").meters["danger"] = 0.0
    body = response.text.replace("{surface}", surface.label).replace("{paint}", paint.label)
    world.say(
        f"{mentor.label_word.capitalize()} came at once and {body}."
    )
    world.say(
        f"Soon the arrow pointed cleanly toward {mission.answer_place}, and even the moon dust seemed to settle down and watch."
    )


def rescue_fail(world: World, mentor: Entity, response: Response, surface: Surface, paint: Paint) -> None:
    world.get("surface").meters["wet_paint"] = 0.0
    world.get("surface").meters["smeared"] += 1
    world.get("station").meters["danger"] += 1
    body = response.fail.replace("{surface}", surface.label).replace("{paint}", paint.label)
    world.say(
        f"{mentor.label_word.capitalize()} hurried over and {body}."
    )
    world.say(
        f"The half-made arrow sagged into a messy blur, and nobody could trust it to guide a robot anywhere."
    )


def lesson(world: World, mentor: Entity, hero: Entity, helper: Entity, mission: Mission) -> None:
    for kid in (hero, helper):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"Then {mentor.label_word} knelt between them. "
        f"\"A space station loves clear thinking,\" {mentor.pronoun()} said softly. "
        f"\"When a job feels exciting, that is the very moment to slow your hands and ask one more question.\""
    )
    world.say(
        f"{hero.id} nodded. Inside, a new thought glowed warmer than the old one: "
        f"I can still be brave when I choose the careful way."
    )
    world.say(
        f'"Slow and bright, safe and right," {mission.robot_name} sang.'
    )


def safe_finish(world: World, hero: Entity, helper: Entity, mentor: Entity,
                mission: Mission, surface: Surface, response: Response,
                averted: bool = False) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.memes["pride"] += 1
    if averted:
        body = response.text.replace("{surface}", surface.label).replace("{paint}", "the proper paint")
        world.say(
            f"{mentor.label_word.capitalize()} {body}, and this time {hero.id} helped at a steady pace instead of a rushing one."
        )
    world.say(
        f"When the work was done, {surface.the} shone with {surface.ending_glow}. "
        f"{mission.robot_name} rolled along the path, read the sign, and turned exactly toward {mission.answer_place}."
    )
    world.say(
        f'"{mission.rhyme_close}," {mission.robot_name} chimed. '
        f"{mission.ending}"
    )


def postponed_finish(world: World, hero: Entity, helper: Entity, mentor: Entity,
                     mission: Mission, surface: Surface) -> None:
    hero.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"They did not finish the guide sign that day. Instead, {mentor.label_word} led them back inside, "
        f"and {mission.robot_name} had to follow a plain blinking map until morning."
    )
    world.say(
        f"Before bed, {hero.id} drew a neat practice arrow on scrap paper and promised to start slowly next time. "
        f"The real sign would wait, but the lesson was already glowing."
    )


def tell(mission: Mission, surface: Surface, paint: Paint, response: Response,
         hero_name: str = "Nova", hero_gender: str = "girl",
         helper_name: str = "Orion", helper_gender: str = "boy",
         helper_trait: str = "careful", parent_type: str = "mother",
         delay: int = 0, hero_age: int = 5, helper_age: int = 4,
         relation: str = "siblings") -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        age=hero_age,
        attrs={"name": hero_name, "relation": relation},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        age=helper_age,
        traits=[helper_trait],
        attrs={"name": helper_name, "relation": relation},
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type=parent_type,
        label="the grown-up",
        role="mentor",
    ))
    robot = world.add(Entity(
        id="robot",
        kind="thing",
        type="robot",
        label=mission.robot_name,
        role="robot",
        attrs={"kind": mission.robot_kind},
    ))
    station = world.add(Entity(
        id="station",
        kind="thing",
        type="station",
        label=mission.station,
        role="setting",
        inside=True,
    ))
    surface_ent = world.add(Entity(
        id="surface",
        kind="thing",
        type="surface",
        label=surface.label,
        exterior=surface.exterior,
        inside=not surface.exterior,
        surface_type=surface.surface_type,
        role="surface",
    ))
    paint_ent = world.add(Entity(
        id="paint",
        kind="thing",
        type="paint",
        label=paint.label,
        role="paint",
        attrs={"works_on": sorted(paint.works_on)},
    ))

    hero.memes["courage"] = COURAGE_INIT
    helper.memes["caution"] = initial_caution(helper_trait)
    world.facts.update(
        mission=mission,
        surface_cfg=surface,
        paint_cfg=paint,
        response=response,
        relation=relation,
        delay=delay,
    )

    introduce(world, hero, helper, mission)
    frame_need(world, hero, mission, surface)
    foreshadow(world, helper, surface)

    world.para()
    tempt(world, hero, paint, surface)
    warn(world, helper, hero, mentor, mission, surface, paint)

    averted = would_avert(relation, hero_age, helper_age, helper_trait)
    if averted:
        back_down(world, hero, helper, mentor, mission, surface, paint, response)
        outcome = "averted"
        contained = True
    else:
        world.say(
            f'"I can do it," {hero.label} said, and {hero.pronoun()} hurried before {mentor.label_word} could answer.'
        )
        world.para()
        begin_painting(world, hero, surface_ent, paint, surface)
        alarm(world, helper, hero, surface, mentor)

        world.para()
        contained = is_contained(response, surface, delay)
        if contained:
            rescue_success(world, mentor, response, mission, surface, paint)
            lesson(world, mentor, hero, helper, mission)
            world.para()
            safe_finish(world, hero, helper, mentor, mission, surface, response)
            outcome = "contained"
        else:
            rescue_fail(world, mentor, response, surface, paint)
            lesson(world, mentor, hero, helper, mission)
            world.para()
            postponed_finish(world, hero, helper, mentor, mission, surface)
            outcome = "smeared"

    world.facts.update(
        hero=hero,
        helper=helper,
        mentor=mentor,
        robot=robot,
        station=station,
        surface=surface_ent,
        paint=paint_ent,
        averted=averted,
        outcome=outcome,
        severity=severity_of(surface, delay) if not averted else 0,
        contained=contained,
        sign_finished=(outcome in {"averted", "contained"}),
        sign_smeared=(outcome == "smeared"),
        question_text=mission.question_text,
        answer_place=mission.answer_place,
    )
    return world


MISSIONS = {
    "garden_route": Mission(
        id="garden_route",
        station="Moonbeam Station",
        robot_name="Pip",
        robot_kind="seed-cart robot",
        question_text="Which way is the sprout garden?",
        answer_place="the sprout garden",
        sign_shape="a leaf-arrow",
        opening="a tiny moon mission",
        ending="The whole station felt a little kinder because someone had answered a lost robot with care.",
        rhyme_open="Find and mind, be bright and kind",
        rhyme_close="Glow and show, this is the way to go",
        tags={"robot", "garden", "question"},
    ),
    "comet_mail": Mission(
        id="comet_mail",
        station="Starlight Port",
        robot_name="Zip",
        robot_kind="mail rover",
        question_text="Where do I leave the comet postcards?",
        answer_place="the mail bay",
        sign_shape="a tail-arrow",
        opening="a great dockside adventure",
        ending="Little postcard tubes slid into the right basket, and the port hummed happily under the stars.",
        rhyme_open="Zip and zing, hear the metal sing",
        rhyme_close="Right and bright, cargo home tonight",
        tags={"robot", "mail", "question"},
    ),
    "rocket_snacks": Mission(
        id="rocket_snacks",
        station="Pebble Ring Outpost",
        robot_name="Blink",
        robot_kind="snack-tray rover",
        question_text="Which tunnel leads to the warm galley?",
        answer_place="the warm galley",
        sign_shape="a spoon-arrow",
        opening="a brave lunch-time expedition",
        ending="Soon the rover was serving warm moon buns to everyone who had waited patiently.",
        rhyme_open="Clink and clank, thank the galley tank",
        rhyme_close="Snack and track, I found the way back",
        tags={"robot", "galley", "question"},
    ),
}

SURFACES = {
    "hall_wall": Surface(
        id="hall_wall",
        label="hall wall",
        the="the hall wall",
        place="the main corridor",
        surface_type="wall",
        exterior=False,
        risk=0,
        paint_phrase="a bright arrow and a little moon",
        ending_glow="a neat guide sign under the ceiling lights",
        tags={"wall", "inside"},
    ),
    "dome_window": Surface(
        id="dome_window",
        label="dome window",
        the="the dome window",
        place="the observation dome",
        surface_type="glass",
        exterior=False,
        risk=0,
        paint_phrase="a floating star-arrow",
        ending_glow="a gentle sign that seemed to hover among the stars outside",
        tags={"glass", "inside"},
    ),
    "airlock_door": Surface(
        id="airlock_door",
        label="airlock door",
        the="the airlock door",
        place="the outer hatch",
        surface_type="metal",
        exterior=True,
        risk=2,
        paint_phrase="a bold arrow for tired rovers",
        ending_glow="a crisp silver sign on the hatch",
        tags={"metal", "outside"},
    ),
    "rover_side": Surface(
        id="rover_side",
        label="rover side",
        the="the rover side",
        place="the loading pad",
        surface_type="metal",
        exterior=True,
        risk=3,
        paint_phrase="a shining arrow on the rover shell",
        ending_glow="a star-bright sign on the rover shell",
        tags={"metal", "outside"},
    ),
    "fabric_banner": Surface(
        id="fabric_banner",
        label="fabric banner",
        the="the fabric banner",
        place="the welcome rack",
        surface_type="fabric",
        exterior=False,
        risk=0,
        paint_phrase="a soft arrow and tiny planets",
        ending_glow="a cheerful banner swaying above the corridor",
        tags={"fabric", "inside"},
    ),
}

PAINTS = {
    "mural_paint": Paint(
        id="mural_paint",
        label="mural paint",
        phrase="a tray of mural paint",
        works_on={"wall"},
        quick=False,
        shimmer="smooth and steady",
        tags={"paint", "wall"},
    ),
    "cling_paint": Paint(
        id="cling_paint",
        label="cling paint",
        phrase="a tube of cling paint",
        works_on={"glass"},
        quick=False,
        shimmer="clear and pearly",
        tags={"paint", "glass"},
    ),
    "star_paint": Paint(
        id="star_paint",
        label="star paint",
        phrase="a can of star paint",
        works_on={"metal"},
        quick=True,
        shimmer="silver-blue",
        tags={"paint", "metal"},
    ),
    "fabric_paint": Paint(
        id="fabric_paint",
        label="fabric paint",
        phrase="a bottle of fabric paint",
        works_on={"fabric"},
        quick=False,
        shimmer="soft and bright",
        tags={"paint", "fabric"},
    ),
    "watercolors": Paint(
        id="watercolors",
        label="watercolors",
        phrase="a little pan of watercolors",
        works_on={"paper"},
        quick=False,
        shimmer="wet and runny",
        tags={"paint", "decoy"},
    ),
}

RESPONSES = {
    "steady_arms": Response(
        id="steady_arms",
        sense=3,
        power=1,
        text="guided {hero} back to a table, brought the proper tools, and helped make the sign with slow, steady arms",
        fail="tried to steady the work by hand alone, but the rushing moment had already spoiled the line",
        qa_text="helped the children remake the sign slowly with the proper tools",
        tags={"careful", "slow"},
    ),
    "tether_rig": Response(
        id="tether_rig",
        sense=3,
        power=3,
        text="clicked on the tether rig, shielded the brush from the dust, and let the crew finish the sign safely on the {surface}",
        fail="fastened the tether rig, but the dust had already whipped the paint into a blur on the {surface}",
        qa_text="used a tether rig and shielded the painting from the dust",
        tags={"tether", "outside"},
    ),
    "service_canopy": Response(
        id="service_canopy",
        sense=2,
        power=2,
        text="rolled a service canopy over the work spot and turned a shaky job into a calm one",
        fail="rolled a service canopy into place, but the half-made sign on the {surface} had already smeared too badly",
        qa_text="rolled a service canopy over the work spot so the painting could continue calmly",
        tags={"canopy", "outside"},
    ),
    "hold_breath": Response(
        id="hold_breath",
        sense=1,
        power=0,
        text="told everyone to hold very still and hope the paint behaved",
        fail="told everyone to hold very still, but hope was not enough for a careful space job",
        qa_text="tried to rely on staying still and hoping for the best",
        tags={"bad_idea"},
    ),
}


GIRL_NAMES = ["Nova", "Luna", "Mira", "Ada", "Ivy", "Zia", "Tess", "Nia"]
BOY_NAMES = ["Orion", "Leo", "Milo", "Kai", "Jude", "Eli", "Finn", "Remy"]
TRAITS = ["careful", "steady", "thoughtful", "patient", "curious", "brisk"]
RELATIONS = ["siblings", "friends"]


@dataclass
class StoryParams:
    mission: str
    surface: str
    paint: str
    response: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    helper_trait: str
    delay: int = 0
    hero_age: int = 5
    helper_age: int = 4
    relation: str = "siblings"
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
    "question": [
        (
            "What is a question?",
            "A question is something you ask when you want to know an answer. It often helps people solve a problem together.",
        )
    ],
    "paint": [
        (
            "What does paint do?",
            "Paint adds color to a surface. Different kinds of paint work best on different materials, like walls, glass, or fabric.",
        )
    ],
    "robot": [
        (
            "What is a robot?",
            "A robot is a machine that can help with jobs. Some robots roll, some lift, and some carry messages or tools.",
        )
    ],
    "tether": [
        (
            "What is a tether?",
            "A tether is a strong safety line that keeps a person or tool connected to a safe place. On a space station, that helps stop drifting and keeps work steadier.",
        )
    ],
    "glass": [
        (
            "Why does glass need special paint?",
            "Glass is smooth, so some paint can slide right off it. Cling paint is made to stick better to shiny, slick surfaces.",
        )
    ],
    "metal": [
        (
            "Why can outside metal be hard to paint in space stories?",
            "Metal can be cold and smooth, and outside work may have dust or shaking to deal with. That means the crew needs the right paint and careful tools.",
        )
    ],
    "fabric": [
        (
            "Why is fabric paint different?",
            "Fabric bends and wrinkles, so fabric paint needs to move with the cloth. That keeps the picture from cracking or flaking off.",
        )
    ],
    "careful": [
        (
            "Why is slowing down sometimes the brave choice?",
            "Slowing down gives you time to notice danger and ask for help. A careful choice can protect both people and the job they are trying to do.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "question",
    "paint",
    "robot",
    "tether",
    "glass",
    "metal",
    "fabric",
    "careful",
]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    surface_cfg = f["surface_cfg"]
    paint_cfg = f["paint_cfg"]
    hero = f["hero"]
    helper = f["helper"]
    outcome = f["outcome"]
    base = (
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the words '
        f'"question" and "paint". A child should try to help a robot by painting a guide sign.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {hero.label} wants to hurry and paint {surface_cfg.the}, "
            f"but {helper.label} asks the right question and helps {hero.pronoun('object')} slow down before anything goes wrong.",
            f'Write a child-facing moon-station story with foreshadowing, one line of inner monologue, and a little rhyme, ending in a safe painted sign.',
        ]
    if outcome == "smeared":
        return [
            base,
            f"Tell a cautionary space story where {hero.label} rushes to use {paint_cfg.label} on {surface_cfg.the}, the sign gets ruined, and the children learn to slow down and ask for help.",
            f'Write a simple moon-base story with foreshadowing, inner monologue, and rhyme, ending with a postponed mission but a clear lesson.',
        ]
    return [
        base,
        f"Tell a moon-station story where {hero.label} tries to paint a guide sign for a lost robot, trouble begins, and a calm grown-up fixes the plan in a sensible way.",
        f'Write a child-facing space adventure with foreshadowing, inner monologue, and rhyme that ends with a glowing sign showing what changed.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mentor = f["mentor"]
    mission = f["mission"]
    surface_cfg = f["surface_cfg"]
    paint_cfg = f["paint_cfg"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(hero, helper, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.label} and {helper.label}, on {mission.station}. It is also about {mission.robot_name}, the little {mission.robot_kind} who needed help finding {mission.answer_place}.",
        ),
        (
            "What question did the robot ask?",
            f'{mission.robot_name} asked, "{mission.question_text}" That question is what started the whole adventure, because the children wanted to answer it with a painted sign.',
        ),
        (
            f"Why did {hero.label} want to paint {surface_cfg.the}?",
            f"{hero.label} wanted to make the way to {mission.answer_place} easy to see. The painted arrow would answer the robot's question without needing anyone to explain it again and again.",
        ),
        (
            f"What warning signs came before the trouble?",
            (
                "The story hinted that rushing might be a mistake before anything went wrong. "
                + (
                    "The dust outside curled around the rails and the tether rings gave a little clink, which foreshadowed that outside work could wobble."
                    if surface_cfg.exterior
                    else "The humming fans and blinking lights made the corridor feel watchful, which foreshadowed that the job needed care."
                )
            ),
        ),
        (
            f"What was {hero.label} thinking before the choice?",
            f"{hero.label} thought about doing the job fast before anyone could say wait. That inner thought shows why the rushing plan felt tempting, even though it was not the safest idea.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How did {helper.label} help stop the problem?",
                f"{helper.label} warned that rushing could make the sign go wrong and asked {hero.label} to check with {mentor.label_word} first. Because {hero.label} listened, the crew changed plans before the paint or the dust could cause trouble.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a safe glowing sign that guided {mission.robot_name} toward {mission.answer_place}. The ending proves something changed, because the children answered the question carefully instead of rushing.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"How did {mentor.label_word} fix the problem?",
                f"{mentor.label_word.capitalize()} {response.qa_text}. That sensible help turned a shaky moment into a safe one and let the sign be finished clearly.",
            )
        )
        qa.append(
            (
                f"What did {hero.label} learn?",
                f"{hero.label} learned that exciting jobs still need calm hands and one more question. The lesson mattered because the danger started when {hero.pronoun()} tried to hurry instead of checking first.",
            )
        )
    else:
        qa.append(
            (
                "Did the guide sign work that day?",
                f"No. The sign smeared and could not be trusted to guide the robot, so the mission had to wait until morning. That consequence came from rushing before the work was steady enough.",
            )
        )
        qa.append(
            (
                f"What did the children learn from the ruined sign?",
                f"They learned that hoping and hurrying are not enough for a careful space job. Next time they would slow down, ask for help, and start with the safer plan.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    surface_cfg = f["surface_cfg"]
    response = f["response"]
    tags = {"question", "paint", "robot", "careful"}
    if surface_cfg.surface_type == "glass":
        tags.add("glass")
    if surface_cfg.surface_type == "metal":
        tags.add("metal")
    if surface_cfg.surface_type == "fabric":
        tags.add("fabric")
    if "tether" in response.tags or surface_cfg.exterior:
        tags.add("tether")
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
        if e.exterior:
            bits.append("exterior=True")
        if e.surface_type:
            bits.append(f"surface_type={e.surface_type}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="garden_route",
        surface="hall_wall",
        paint="mural_paint",
        response="steady_arms",
        hero_name="Nova",
        hero_gender="girl",
        helper_name="Orion",
        helper_gender="boy",
        parent="mother",
        helper_trait="careful",
        delay=0,
        hero_age=5,
        helper_age=7,
        relation="siblings",
    ),
    StoryParams(
        mission="comet_mail",
        surface="dome_window",
        paint="cling_paint",
        response="steady_arms",
        hero_name="Milo",
        hero_gender="boy",
        helper_name="Luna",
        helper_gender="girl",
        parent="father",
        helper_trait="curious",
        delay=0,
        hero_age=6,
        helper_age=5,
        relation="friends",
    ),
    StoryParams(
        mission="rocket_snacks",
        surface="airlock_door",
        paint="star_paint",
        response="tether_rig",
        hero_name="Ada",
        hero_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        parent="mother",
        helper_trait="thoughtful",
        delay=0,
        hero_age=6,
        helper_age=5,
        relation="siblings",
    ),
    StoryParams(
        mission="garden_route",
        surface="rover_side",
        paint="star_paint",
        response="service_canopy",
        hero_name="Finn",
        hero_gender="boy",
        helper_name="Nia",
        helper_gender="girl",
        parent="father",
        helper_trait="brisk",
        delay=1,
        hero_age=6,
        helper_age=5,
        relation="friends",
    ),
    StoryParams(
        mission="comet_mail",
        surface="fabric_banner",
        paint="fabric_paint",
        response="steady_arms",
        hero_name="Mira",
        hero_gender="girl",
        helper_name="Zia",
        helper_gender="girl",
        parent="mother",
        helper_trait="patient",
        delay=0,
        hero_age=4,
        helper_age=6,
        relation="siblings",
    ),
]


def explain_rejection(surface: Surface, paint: Paint) -> str:
    if not paint_compatible(paint, surface):
        return (
            f"(No story: {paint.label} does not belong on {surface.the}. "
            f"This world only paints signs when the chosen paint really fits the surface.)"
        )
    return "(No story: this combination does not make a reasonable painting job.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    surface = SURFACES[params.surface]
    if would_avert(params.relation, params.hero_age, params.helper_age, params.helper_trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], surface, params.delay) else "smeared"


ASP_RULES = r"""
compatible(S, P) :- surface(S), paint(P), works_on(P, T), surface_type(S, T).
sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.
valid(Ms, S, P) :- mission(Ms), compatible(S, P).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
helper_older :- relation(siblings), hero_age(H), helper_age(K), K > H.
bonus(3) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), courage_init(CO), A > CO.

severity(R + D) :- chosen_surface(S), risk(S, R), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(smeared) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        lines.append(asp.fact("surface_type", surface_id, surface.surface_type))
        lines.append(asp.fact("risk", surface_id, surface.risk))
        if surface.exterior:
            lines.append(asp.fact("exterior", surface_id))
    for paint_id, paint in PAINTS.items():
        lines.append(asp.fact("paint", paint_id))
        for kind in sorted(paint.works_on):
            lines.append(asp.fact("works_on", paint_id, kind))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("courage_init", int(COURAGE_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_surface", params.surface),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.helper_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_test() -> None:
    params = StoryParams(
        mission="garden_route",
        surface="hall_wall",
        paint="mural_paint",
        response="steady_arms",
        hero_name="Nova",
        hero_gender="girl",
        helper_name="Orion",
        helper_gender="boy",
        parent="mother",
        helper_trait="careful",
        delay=0,
        hero_age=5,
        helper_age=7,
        relation="siblings",
        seed=999,
    )
    sample = generate(params)
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit(sample, trace=True, qa=True, header="### smoke")
    rendered = buf.getvalue()
    if "question" not in sample.story.lower() or "paint" not in sample.story.lower():
        raise AssertionError("smoke story missing required seed words")
    if "### smoke" not in rendered:
        raise AssertionError("emit smoke test failed")


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sens, python_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

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
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test passed for generate()/emit().")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child answers a robot's question by painting a sign on a moon station."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--paint", choices=PAINTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra trouble before the grown-up takes over")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface and args.paint:
        surface = SURFACES[args.surface]
        paint = PAINTS[args.paint]
        if not paint_compatible(paint, surface):
            raise StoryError(explain_rejection(surface, paint))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.surface is None or combo[1] == args.surface)
        and (args.paint is None or combo[2] == args.paint)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, surface_id, paint_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name, hero_gender = _pick_name(rng)
    helper_name, helper_gender = _pick_name(rng, avoid=hero_name)
    helper_trait = rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(RELATIONS)
    hero_age, helper_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        mission=mission_id,
        surface=surface_id,
        paint=paint_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        helper_trait=helper_trait,
        delay=delay,
        hero_age=hero_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.paint not in PAINTS:
        raise StoryError(f"(Unknown paint: {params.paint})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    mission = MISSIONS[params.mission]
    surface = SURFACES[params.surface]
    paint = PAINTS[params.paint]
    response = RESPONSES[params.response]
    if not paint_compatible(paint, surface):
        raise StoryError(explain_rejection(surface, paint))

    world = tell(
        mission=mission,
        surface=surface,
        paint=paint,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        parent_type=params.parent,
        delay=params.delay,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        relation=params.relation,
    )
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    return sample


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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, surface, paint) combos:\n")
        for mission_id, surface_id, paint_id in combos:
            print(f"  {mission_id:13} {surface_id:13} {paint_id}")
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
            header = (
                f"### {p.hero_name} & {p.helper_name}: {p.paint} on {p.surface} "
                f"({p.mission}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
