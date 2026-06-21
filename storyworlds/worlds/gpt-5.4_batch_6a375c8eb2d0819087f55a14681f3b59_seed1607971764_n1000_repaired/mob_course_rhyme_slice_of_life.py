#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mob_course_rhyme_slice_of_life.py
============================================================

A standalone story world for a small slice-of-life tale about a child who sets
up a play course, then has to cope when a whole mob of eager kids wants to join.
The world models crowd pressure, turn-taking, and a rhyming chant that helps the
children slow down and share.

Reference seed vibe
-------------------
A child-facing, everyday story with rhyme and the words "mob" and "course":
one child makes a little play course; too many children rush in at once; a calm
helper suggests a sensible way to take turns; the group learns the chant and the
afternoon becomes joyful instead of chaotic.

Run it
------
    python storyworlds/worlds/gpt-5.4/mob_course_rhyme_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/mob_course_rhyme_slice_of_life.py --place courtyard --course scooter
    python storyworlds/worlds/gpt-5.4/mob_course_rhyme_slice_of_life.py --place living_room --fix cones
    python storyworlds/worlds/gpt-5.4/mob_course_rhyme_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/mob_course_rhyme_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mob_course_rhyme_slice_of_life.py --json
    python storyworlds/worlds/gpt-5.4/mob_course_rhyme_slice_of_life.py --asp
    python storyworlds/worlds/gpt-5.4/mob_course_rhyme_slice_of_life.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "sister"}
        male = {"boy", "father", "dad", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
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
class Place:
    id: str
    label: str
    scene: str
    surface: str
    afford_courses: set[str] = field(default_factory=set)
    allows_chalk: bool = False
    allows_cones: bool = False
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
class CourseKind:
    id: str
    label: str
    gear: str
    build_text: str
    move_text: str
    crowd_word: str
    need_space: bool = True
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
class Fix:
    id: str
    label: str
    needs_chalk: bool = False
    needs_cones: bool = False
    works_for: set[str] = field(default_factory=set)
    line_text: str = ""
    rhythm: str = ""
    qa_text: str = ""
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
class CrowdSize:
    id: str
    label: str
    count: int
    word: str
    risk: int
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_crowd_pressure(world: World) -> list[str]:
    out: list[str] = []
    crowd = world.get("crowd")
    course = world.get("course")
    if crowd.meters["waiting"] < THRESHOLD:
        return out
    sig = ("pressure", int(crowd.meters["waiting"]), int(course.meters["turns"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if course.meters["turns"] < THRESHOLD:
        course.meters["jammed"] += 1
        course.meters["risk"] += 1
        for kid in world.kids():
            kid.memes["frustration"] += 1
        out.append("__jam__")
    else:
        crowd.meters["line"] += 1
        for kid in world.kids():
            kid.memes["calm"] += 1
        out.append("__line__")
    return out


def _r_rhyme_settles(world: World) -> list[str]:
    out: list[str] = []
    crowd = world.get("crowd")
    course = world.get("course")
    if course.meters["chant"] < THRESHOLD or course.meters["turns"] < THRESHOLD:
        return out
    sig = ("chant_settle", int(crowd.meters["waiting"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if crowd.meters["waiting"] >= THRESHOLD:
        crowd.meters["pushing"] = 0.0
        course.meters["risk"] = max(0.0, course.meters["risk"] - 1.0)
        for kid in world.kids():
            kid.memes["joy"] += 1
            kid.memes["pride"] += 1
        out.append("__settled__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="crowd_pressure", tag="social", apply=_r_crowd_pressure),
    Rule(name="rhyme_settles", tag="social", apply=_r_rhyme_settles),
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
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        scene="the sunny courtyard between the brick buildings",
        surface="pavement",
        afford_courses={"scooter", "chalk_hop", "beanbag"},
        allows_chalk=True,
        allows_cones=True,
        tags={"outside", "courtyard"},
    ),
    "driveway": Place(
        id="driveway",
        label="the driveway",
        scene="the flat driveway by the little front garden",
        surface="pavement",
        afford_courses={"scooter", "chalk_hop"},
        allows_chalk=True,
        allows_cones=True,
        tags={"outside", "driveway"},
    ),
    "living_room": Place(
        id="living_room",
        label="the living room",
        scene="the living room with the rug pushed back",
        surface="floor",
        afford_courses={"beanbag"},
        allows_chalk=False,
        allows_cones=False,
        tags={"inside", "living_room"},
    ),
    "playroom": Place(
        id="playroom",
        label="the playroom",
        scene="the playroom with a shelf of games and soft mats",
        surface="mat",
        afford_courses={"beanbag"},
        allows_chalk=False,
        allows_cones=True,
        tags={"inside", "playroom"},
    ),
}

COURSES = {
    "scooter": CourseKind(
        id="scooter",
        label="scooter course",
        gear="small scooter",
        build_text="set out a looping scooter course with a start line, a slow turn, and a finish",
        move_text="zip around the corners on the scooter",
        crowd_word="riders",
        need_space=True,
        tags={"scooter", "movement"},
    ),
    "chalk_hop": CourseKind(
        id="chalk_hop",
        label="chalk hop course",
        gear="stubby box of chalk",
        build_text="drew a hop course with circles, stars, and a wiggly finish line",
        move_text="hop from shape to shape without stepping on the cracks",
        crowd_word="hoppers",
        need_space=False,
        tags={"chalk", "movement"},
    ),
    "beanbag": CourseKind(
        id="beanbag",
        label="beanbag course",
        gear="basket of beanbags",
        build_text="made a tiny beanbag course with a tape line, a cushion bridge, and a basket at the end",
        move_text="walk the path and toss a beanbag into the basket",
        crowd_word="players",
        need_space=False,
        tags={"beanbag", "movement"},
    ),
}

FIXES = {
    "dots": Fix(
        id="dots",
        label="chalk waiting dots",
        needs_chalk=True,
        needs_cones=False,
        works_for={"scooter", "chalk_hop"},
        line_text="drew waiting dots beside the course so each child had a place to stand",
        rhythm="Dot by dot, wait your spot. When it's clear, start from here.",
        qa_text="drew waiting dots and used a rhyming turn chant",
        tags={"chalk", "turns", "rhyme"},
    ),
    "cones": Fix(
        id="cones",
        label="soft cones and a start lane",
        needs_chalk=False,
        needs_cones=True,
        works_for={"scooter", "beanbag"},
        line_text="set soft cones in a neat lane so the children could queue without crowding the start",
        rhythm="One in line, one on course. Slow feet first, gentle force.",
        qa_text="set soft cones in a line and taught the children a rhyming chant",
        tags={"cones", "turns", "rhyme"},
    ),
    "cushions": Fix(
        id="cushions",
        label="cushion waiting path",
        needs_chalk=False,
        needs_cones=False,
        works_for={"beanbag"},
        line_text="laid down two cushions and a little waiting path so the next child had somewhere calm to stand",
        rhythm="Wait and sway, then you play. Toss, then grin, next friend in.",
        qa_text="made a cushion waiting path and gave everyone a rhyming turn chant",
        tags={"cushions", "turns", "rhyme"},
    ),
}

CROWDS = {
    "few": CrowdSize(
        id="few",
        label="a few children",
        count=3,
        word="a few",
        risk=1,
        tags={"few"},
    ),
    "mob": CrowdSize(
        id="mob",
        label="a mob of children",
        count=7,
        word="a little mob of",
        risk=2,
        tags={"mob"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Zoe", "Ivy", "Nora", "Tess", "Ruby", "Ella"]
BOY_NAMES = ["Milo", "Ben", "Leo", "Owen", "Finn", "Sam", "Theo", "Eli"]
TRAITS = ["careful", "bright", "patient", "cheerful", "steady", "kind"]


def place_supports_course(place: Place, course: CourseKind) -> bool:
    return course.id in place.afford_courses


def fix_supports(place: Place, course: CourseKind, fix: Fix) -> bool:
    if course.id not in fix.works_for:
        return False
    if fix.needs_chalk and not place.allows_chalk:
        return False
    if fix.needs_cones and not place.allows_cones:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for course_id, course in COURSES.items():
            if not place_supports_course(place, course):
                continue
            for fix_id, fix in FIXES.items():
                if fix_supports(place, course, fix):
                    combos.append((place_id, course_id, fix_id))
    return combos


def explain_combo(place: Place, course: CourseKind, fix: Fix) -> str:
    if not place_supports_course(place, course):
        return (
            f"(No story: {course.label} does not fit {place.label}. "
            f"That place does not support that kind of movement.)"
        )
    if fix.needs_chalk and not place.allows_chalk:
        return (
            f"(No story: {fix.label} needs chalk marks, but chalk does not belong on "
            f"{place.label}. Pick a place with pavement or choose another fix.)"
        )
    if fix.needs_cones and not place.allows_cones:
        return (
            f"(No story: {fix.label} needs cones, but that place does not have room "
            f"for them in this world.)"
        )
    if course.id not in fix.works_for:
        return (
            f"(No story: {fix.label} is not a sensible way to organize a {course.label}. "
            f"Choose a fix that matches the course.)"
        )
    return "(No story: that combination is not supported.)"


def predict_jam(world: World) -> dict:
    sim = world.copy()
    crowd = sim.get("crowd")
    course = sim.get("course")
    crowd.meters["waiting"] += 1
    crowd.meters["pushing"] += sim.facts["crowd_cfg"].risk
    course.meters["turns"] = 0.0
    propagate(sim, narrate=False)
    return {
        "jammed": course.meters["jammed"] >= THRESHOLD,
        "risk": course.meters["risk"],
    }


def introduce(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"After lunch, {hero.id} and {helper.id} went down to {place.scene}."
    )
    world.say(
        f"The afternoon felt ordinary in the nicest way, with sneakers scuffing "
        f"the {place.surface} and a warm breeze sneaking past the windows."
    )


def build_course(world: World, hero: Entity, course: CourseKind) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} had brought a {course.gear} and {course.build_text}. "
        f"Soon the little course looked just right for one careful turn after another."
    )


def admire(world: World, helper: Entity, hero: Entity, course: CourseKind) -> None:
    helper.memes["joy"] += 1
    world.say(
        f'"That is a fine {course.label}," {helper.id} said. '
        f'"I want to {course.move_text} too."'
    )


def crowd_arrives(world: World, crowd_cfg: CrowdSize, course: CourseKind) -> None:
    crowd = world.get("crowd")
    crowd.meters["waiting"] += 1
    crowd.meters["pushing"] += crowd_cfg.risk
    world.say(
        f"But then the gate clicked, and {crowd_cfg.word} neighborhood children came over. "
        f"In one blink, a whole mob of eager {course.crowd_word} was peeking at the start line."
    )
    world.say(
        "Everyone wanted to go first, and the happy noise turned buzzy and bumpy."
    )


def warn(world: World, helper: Entity, hero: Entity, course: CourseKind) -> None:
    pred = predict_jam(world)
    world.facts["predicted_risk"] = pred["risk"]
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} watched the children bunch together and said, '
        f'"If everyone rushes onto the course at once, somebody could bump and somebody could cry."'
    )


def jam(world: World, hero: Entity, helper: Entity) -> None:
    course = world.get("course")
    propagate(world, narrate=False)
    if course.meters["jammed"] >= THRESHOLD:
        hero.memes["frustration"] += 1
        world.say(
            f"{hero.id} tightened {hero.pronoun('possessive')} hands around the start line. "
            f"The course was getting jammed before anyone had a proper turn."
        )
        world.say(
            f'"Please do not push," {helper.id} said, but the line was not really a line yet.'
        )


def choose_fix(world: World, grownup: Entity, hero: Entity, helper: Entity, fix: Fix) -> None:
    course = world.get("course")
    crowd = world.get("crowd")
    grownup.memes["calm"] += 1
    course.meters["turns"] += 1
    course.meters["chant"] += 1
    crowd.meters["pushing"] = max(0.0, crowd.meters["pushing"] - 1.0)
    world.say(
        f"{hero.id}'s {grownup.label_word} came over from the bench, took one look, and smiled the kind of smile "
        f"that means a good idea is on the way."
    )
    world.say(
        f"{grownup.pronoun().capitalize()} {fix.line_text}. Then {grownup.pronoun()} clapped a soft beat and taught them a rhyme:"
    )
    world.say(f'"{fix.rhythm}"')


def settle(world: World, hero: Entity, helper: Entity, course_cfg: CourseKind) -> None:
    propagate(world, narrate=False)
    crowd = world.get("crowd")
    course = world.get("course")
    if crowd.meters["line"] >= THRESHOLD:
        world.say(
            f"The children tried it once, then again. Soon one child waited, one child moved through the course, "
            f"and the rest swayed along with the rhyme."
        )
    if course.meters["risk"] < THRESHOLD:
        world.say(
            f"{hero.id} went first, then {helper.id}, and after that the turns flowed as neatly as buttons in a row."
        )
    else:
        world.say(
            "The pushing eased, and the children finally had room to notice one another."
        )


def ending(world: World, hero: Entity, helper: Entity, course_cfg: CourseKind, fix: Fix) -> None:
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"By the time the sun slid lower, the mob did not feel wild anymore. "
        f"It felt like a shared game with space for everyone."
    )
    world.say(
        f"{hero.id} still loved the course, but now {hero.pronoun()} loved the waiting dots and the chant too. "
        f"When one more child trotted up late, the others sang, \"{fix.rhythm}\" and made room."
    )
    world.say(
        f"That was how the afternoon ended at {world.place.label}: one child on the course, one child next in line, "
        f"and a small rhyme keeping the whole thing kind."
    )


def tell(
    place: Place,
    course_cfg: CourseKind,
    fix: Fix,
    crowd_cfg: CrowdSize,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    grownup_type: str = "mother",
    trait: str = "patient",
) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["eager"]))
    grownup = world.add(Entity(id="Parent", kind="character", type=grownup_type, role="grownup", label="the grown-up"))
    crowd = world.add(Entity(id="crowd", kind="thing", type="crowd", label=crowd_cfg.label))
    course = world.add(Entity(id="course", kind="thing", type="course", label=course_cfg.label))

    crowd.meters["waiting"] = 0.0
    crowd.meters["pushing"] = 0.0
    crowd.meters["line"] = 0.0
    course.meters["jammed"] = 0.0
    course.meters["risk"] = 0.0
    course.meters["turns"] = 0.0
    course.meters["chant"] = 0.0

    world.facts.update(
        place=place,
        course_cfg=course_cfg,
        fix=fix,
        crowd_cfg=crowd_cfg,
        hero=hero,
        helper=helper,
        grownup=grownup,
    )

    introduce(world, hero, helper, place)
    build_course(world, hero, course_cfg)
    admire(world, helper, hero, course_cfg)

    world.para()
    crowd_arrives(world, crowd_cfg, course_cfg)
    warn(world, helper, hero, course_cfg)
    jam(world, hero, helper)

    world.para()
    choose_fix(world, grownup, hero, helper, fix)
    settle(world, hero, helper, course_cfg)
    ending(world, hero, helper, course_cfg, fix)

    world.facts.update(
        crowded=crowd.meters["waiting"] >= THRESHOLD,
        jammed=course.meters["jammed"] >= THRESHOLD,
        organized=course.meters["turns"] >= THRESHOLD and crowd.meters["line"] >= THRESHOLD,
        rhyme=course.meters["chant"] >= THRESHOLD,
        risk=max(0, int(course.meters["risk"])),
    )
    return world


KNOWLEDGE = {
    "mob": [
        (
            "What does mob mean in this story?",
            "Here mob means a big, busy group all bunched together. It does not mean the children are bad, only that there are many of them at once.",
        )
    ],
    "course": [
        (
            "What is a play course?",
            "A play course is a path or set of little challenges children follow in order. It can have a start, a middle, and a finish.",
        )
    ],
    "turns": [
        (
            "Why do children take turns?",
            "Taking turns gives each child a fair chance. It also keeps games calmer and safer when everyone wants the same thing.",
        )
    ],
    "rhyme": [
        (
            "Why can a rhyme help a group of children?",
            "A rhyme is easy to remember and easy to say together. Its beat helps children slow down and do the same safe steps in the same order.",
        )
    ],
    "chalk": [
        (
            "What is sidewalk chalk for?",
            "Sidewalk chalk is soft chalk for drawing on pavement. Children can use it to make pictures, lines, and game marks that can wash away later.",
        )
    ],
    "cones": [
        (
            "What are soft cones used for in play?",
            "Soft cones mark where to go or where to wait. They help children see the path without bumping into one another.",
        )
    ],
    "cushions": [
        (
            "Why can cushions help indoor play?",
            "Cushions make soft places to step or wait. They can turn a busy room into a calmer path for play.",
        )
    ],
}

KNOWLEDGE_ORDER = ["mob", "course", "turns", "rhyme", "chalk", "cones", "cushions"]


@dataclass
class StoryParams:
    place: str
    course: str
    fix: str
    crowd: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    grownup: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    course_cfg = f["course_cfg"]
    fix = f["fix"]
    return [
        f'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "mob" and "course" and uses a gentle rhyme.',
        f"Tell a story where {hero.id} makes a {course_cfg.label} at {place.label}, but a mob of children arrives and {helper.id} helps notice the problem before a grown-up organizes turns.",
        f"Write a simple everyday story with a rhyming chant, where children learn to share a course by using {fix.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    grownup = f["grownup"]
    place = f["place"]
    course_cfg = f["course_cfg"]
    fix = f["fix"]
    crowd_cfg = f["crowd_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {helper.id}, and {hero.id}'s {grownup.label_word} at {place.label}. They are spending an ordinary afternoon making and sharing a play course.",
        ),
        (
            f"What kind of course did {hero.id} make?",
            f"{hero.id} made a {course_cfg.label}. The course gave the children one fun path to follow from start to finish.",
        ),
        (
            "Why did the game become hard for a moment?",
            f"It became hard when {crowd_cfg.label} came over all at once and everyone wanted to start first. The crowding jammed the course and made bumping more likely.",
        ),
        (
            f"How did {helper.id} know something was wrong?",
            f"{helper.id} saw the children bunch together at the start and realized the course would not work if everyone rushed at once. {helper.pronoun().capitalize()} warned that somebody could bump and cry if no one took turns.",
        ),
        (
            f"What did {hero.id}'s {grownup.label_word} do to help?",
            f"{grownup.label_word.capitalize()} {fix.qa_text}. That gave each child a clear place and a clear order, so the pushing eased.",
        ),
        (
            "How did the rhyme help?",
            f"The rhyme gave the children the same words and beat to follow. Because they said it together, the course changed from a jam into a turn-taking game.",
        ),
        (
            "How did the story end?",
            f"It ended with the children making room for one another and singing the rhyme to a late-arriving child. The final picture shows that the course stayed fun after the children learned to share it kindly.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"mob", "course", "turns", "rhyme"}
    fix = world.facts["fix"]
    if fix.needs_chalk:
        tags.add("chalk")
    if fix.needs_cones:
        tags.add("cones")
    if fix.id == "cushions":
        tags.add("cushions")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="courtyard",
        course="scooter",
        fix="cones",
        crowd="mob",
        hero="Lina",
        hero_gender="girl",
        helper="Ben",
        helper_gender="boy",
        grownup="mother",
        trait="patient",
    ),
    StoryParams(
        place="driveway",
        course="chalk_hop",
        fix="dots",
        crowd="mob",
        hero="Milo",
        hero_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        grownup="father",
        trait="cheerful",
    ),
    StoryParams(
        place="playroom",
        course="beanbag",
        fix="cones",
        crowd="few",
        hero="Nora",
        hero_gender="girl",
        helper="Sam",
        helper_gender="boy",
        grownup="mother",
        trait="kind",
    ),
    StoryParams(
        place="living_room",
        course="beanbag",
        fix="cushions",
        crowd="mob",
        hero="Theo",
        hero_gender="boy",
        helper="Ivy",
        helper_gender="girl",
        grownup="father",
        trait="steady",
    ),
]


ASP_RULES = r"""
supports_course(P,C) :- place(P), course(C), affords(P,C).
supports_fix(P,C,F) :- supports_course(P,C), fix(F), works_for(F,C),
                       not needs_chalk(F);
                       supports_course(P,C), fix(F), works_for(F,C),
                       needs_chalk(F), allows_chalk(P);
                       supports_course(P,C), fix(F), works_for(F,C),
                       needs_cones(F), allows_cones(P);
                       supports_course(P,C), fix(F), works_for(F,C),
                       not needs_chalk(F), not needs_cones(F).

invalid_fix(P,C,F) :- supports_course(P,C), fix(F), works_for(F,C), needs_chalk(F), not allows_chalk(P).
invalid_fix(P,C,F) :- supports_course(P,C), fix(F), works_for(F,C), needs_cones(F), not allows_cones(P).

valid(P,C,F) :- supports_course(P,C), fix(F), works_for(F,C),
                not invalid_fix(P,C,F).

risky(Cr) :- crowd(Cr), crowd_risk(Cr,R), R >= 2.
organized :- chosen_fix(F), fix(F).
outcome(calm) :- organized.
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for cid in sorted(place.afford_courses):
            lines.append(asp.fact("affords", pid, cid))
        if place.allows_chalk:
            lines.append(asp.fact("allows_chalk", pid))
        if place.allows_cones:
            lines.append(asp.fact("allows_cones", pid))
    for cid in COURSES:
        lines.append(asp.fact("course", cid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for cid in sorted(fix.works_for):
            lines.append(asp.fact("works_for", fid, cid))
        if fix.needs_chalk:
            lines.append(asp.fact("needs_chalk", fid))
        if fix.needs_cones:
            lines.append(asp.fact("needs_cones", fid))
    for crowd_id, crowd in CROWDS.items():
        lines.append(asp.fact("crowd", crowd_id))
        lines.append(asp.fact("crowd_risk", crowd_id, crowd.risk))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    return "calm"


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_course", params.course),
            asp.fact("chosen_fix", params.fix),
            asp.fact("chosen_crowd", params.crowd),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print("resolve_params unexpectedly failed during verify.")
            break
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child-made course, a mob of eager kids, and a rhyming turn-taking fix."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--course", choices=COURSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--crowd", choices=CROWDS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.course and args.fix:
        place = PLACES[args.place]
        course = COURSES[args.course]
        fix = FIXES[args.fix]
        if (args.place, args.course, args.fix) not in set(valid_combos()):
            raise StoryError(explain_combo(place, course, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.course is None or combo[1] == args.course)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, course_id, fix_id = rng.choice(sorted(combos))
    crowd_id = args.crowd or rng.choice(sorted(CROWDS))
    hero, hero_gender = _pick_name(rng)
    helper, helper_gender = _pick_name(rng, avoid=hero)
    grownup = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        course=course_id,
        fix=fix_id,
        crowd=crowd_id,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        course_cfg = COURSES[params.course]
        fix = FIXES[params.fix]
        crowd_cfg = CROWDS[params.crowd]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]}.)")

    if (params.place, params.course, params.fix) not in set(valid_combos()):
        raise StoryError(explain_combo(place, course_cfg, fix))

    world = tell(
        place=place,
        course_cfg=course_cfg,
        fix=fix,
        crowd_cfg=crowd_cfg,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        grownup_type=params.grownup,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, course, fix) combos:\n")
        for place_id, course_id, fix_id in combos:
            print(f"  {place_id:11} {course_id:10} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero} at {p.place}: {p.course} with {p.fix} ({p.crowd})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
