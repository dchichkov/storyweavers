#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/adventurous_segmentation_lesson_learned_misunderstanding_problem_solving.py
======================================================================================================

A standalone storyworld about an adventurous space crew, a misunderstood word,
and a careful fix. The crew must do "segmentation" on a route map so a tiny
rover can cross a strange moon. A helper robot misunderstands the job and
segments the wrong thing. The children clarify the word, solve the problem with
the right marker kit, and learn to explain important words before starting.

Run it
------
    python storyworlds/worlds/gpt-5.4/adventurous_segmentation_lesson_learned_misunderstanding_problem_solving.py
    python storyworlds/worlds/gpt-5.4/adventurous_segmentation_lesson_learned_misunderstanding_problem_solving.py --course crystal_moon --misunderstanding ribbon --marker laser_chalk
    python storyworlds/worlds/gpt-5.4/adventurous_segmentation_lesson_learned_misunderstanding_problem_solving.py --course dust_dunes --marker magnet_arrows
    python storyworlds/worlds/gpt-5.4/adventurous_segmentation_lesson_learned_misunderstanding_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/adventurous_segmentation_lesson_learned_misunderstanding_problem_solving.py --verify
"""

from __future__ import annotations

import argparse
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Course:
    id: str
    place: str
    sky: str
    ground: str
    map_label: str
    surface: str
    mission: str
    treasure: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    wrong_object: str
    action_text: str
    result_text: str
    severity: int = 1
    blocks_markers: set[str] = field(default_factory=set)
    lesson_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Marker:
    id: str
    label: str
    phrase: str
    works_on: set[str] = field(default_factory=set)
    solve_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    course: str
    misunderstanding: str
    marker: str
    captain: str
    captain_gender: str
    partner: str
    partner_gender: str
    robot_name: str
    trait: str
    seed: Optional[int] = None


COURSES = {
    "crystal_moon": Course(
        id="crystal_moon",
        place="the Crystal Moon",
        sky="violet space full of slow silver stars",
        ground="glass-bright crystal hills",
        map_label="a glowing floor map",
        surface="floor",
        mission="guide the tiny rover through the crystal lanes",
        treasure="a singing moon seed",
        tags={"moon", "rover"},
    ),
    "ring_station": Course(
        id="ring_station",
        place="Ring Station Nine",
        sky="a round window full of blue planets and quiet rings",
        ground="smooth metal halls",
        map_label="a magnetic route board",
        surface="metal",
        mission="guide the tiny rover through the spinning service paths",
        treasure="a missing star battery",
        tags={"station", "rover"},
    ),
    "dust_dunes": Course(
        id="dust_dunes",
        place="the Dust Dunes of Mars",
        sky="a copper sky under a thin pale moon",
        ground="soft red sand that held every footprint",
        map_label="a tray of moon-sand for planning routes",
        surface="sand",
        mission="guide the tiny rover between the dunes and the little rock arches",
        treasure="a bright water pebble",
        tags={"mars", "rover"},
    ),
}

MISUNDERSTANDINGS = {
    "ribbon": Misunderstanding(
        id="ribbon",
        wrong_object="the trail ribbon",
        action_text="snipped the long trail ribbon into many tiny pieces",
        result_text="Instead of a guide line, the table was sprinkled with little curls of ribbon.",
        severity=2,
        blocks_markers={"trail_flags"},
        lesson_text="The mix-up happened because the robot heard the word segmentation and thought it meant cutting something into segments.",
        tags={"misunderstanding", "ribbon"},
    ),
    "stickers": Misunderstanding(
        id="stickers",
        wrong_object="the star sticker sheet",
        action_text="peeled the star stickers off their sheet and sorted them into neat little piles",
        result_text="The piles looked tidy, but the route map still had no path on it.",
        severity=1,
        blocks_markers={"star_stickers"},
        lesson_text="The mix-up happened because the robot heard the word segmentation and thought it meant sorting little pieces into groups.",
        tags={"misunderstanding", "stickers"},
    ),
    "snack": Misunderstanding(
        id="snack",
        wrong_object="the comet bread for lunch",
        action_text="cut the soft comet bread into careful little wedges",
        result_text="The lunch looked very organized, but the mission board was still blank.",
        severity=0,
        blocks_markers=set(),
        lesson_text="The mix-up happened because the robot heard the word segmentation and thought it meant dividing anything at hand into parts.",
        tags={"misunderstanding", "snack"},
    ),
}

MARKERS = {
    "laser_chalk": Marker(
        id="laser_chalk",
        label="laser chalk",
        phrase="a stick of blue laser chalk",
        works_on={"floor"},
        solve_text="used the laser chalk to draw bright route sections across the glowing floor map",
        qa_text="drew bright route sections with laser chalk",
        tags={"segmentation", "map"},
    ),
    "magnet_arrows": Marker(
        id="magnet_arrows",
        label="magnet arrows",
        phrase="a box of little magnet arrows",
        works_on={"metal"},
        solve_text="set the magnet arrows on the board in small ordered sections that showed the rover where to turn",
        qa_text="placed magnet arrows in ordered sections on the board",
        tags={"segmentation", "map"},
    ),
    "trail_flags": Marker(
        id="trail_flags",
        label="trail flags",
        phrase="a bundle of tiny trail flags",
        works_on={"sand"},
        solve_text="pressed the trail flags into the sand tray to mark one safe section after another",
        qa_text="pressed trail flags into the sand tray to mark safe sections",
        tags={"segmentation", "map"},
    ),
    "star_stickers": Marker(
        id="star_stickers",
        label="star stickers",
        phrase="a sheet of shiny star stickers",
        works_on={"floor", "metal"},
        solve_text="placed star stickers in short color rows so each section of the route was easy to follow",
        qa_text="placed star stickers in color rows to show each section",
        tags={"segmentation", "map"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nova", "Tess", "Ayla", "Zuri", "Ivy", "Nora"]
BOY_NAMES = ["Leo", "Max", "Finn", "Eli", "Noah", "Jace", "Theo", "Milo"]
ROBOT_NAMES = ["Pip", "Orbit", "Bloop", "Tinker", "Comet"]
TRAITS = ["careful", "clever", "patient", "bright", "kind", "steady"]

KNOWLEDGE = {
    "segmentation": [
        (
            "What does segmentation mean?",
            "Segmentation means dividing something into clear parts or sections so it is easier to study or follow. In a route map, the sections help you see one safe step at a time.",
        )
    ],
    "rover": [
        (
            "What is a rover?",
            "A rover is a small exploring vehicle that rolls over the ground to look at places people cannot reach right away. Space rovers help scientists and explorers study moons and planets.",
        )
    ],
    "moon": [
        (
            "What is a moon?",
            "A moon is a round world that moves around a planet. Some moons are rocky, icy, dusty, or bright with crystals.",
        )
    ],
    "mars": [
        (
            "What is Mars often called?",
            "Mars is often called the red planet because its dust and rocks look reddish. It is a cold world with wide plains and dusty ground.",
        )
    ],
    "station": [
        (
            "What is a space station?",
            "A space station is a place built for people to live and work in space. It can have rooms, tools, windows, and machines for many jobs.",
        )
    ],
    "misunderstanding": [
        (
            "What should you do when you do not understand a big word?",
            "You should stop and ask what the word means before you act. Asking first can prevent mistakes and help everyone work together.",
        )
    ],
    "map": [
        (
            "Why do explorers use maps with sections?",
            "Sections make a map easier to read because you can follow one part at a time. That helps you notice the safe path and the places to avoid.",
        )
    ],
}
KNOWLEDGE_ORDER = ["segmentation", "rover", "moon", "mars", "station", "map", "misunderstanding"]


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]


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
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_stall(world: World) -> list[str]:
    robot = world.entities.get("robot")
    mission = world.entities.get("mission")
    if robot is None or mission is None:
        return []
    if robot.memes["confused"] < THRESHOLD:
        return []
    sig = ("stall",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mission.meters["stalled"] += 1
    for ent in world.entities.values():
        if ent.role in {"captain", "partner"}:
            ent.memes["worry"] += 1
    return []


def _r_route_ready(world: World) -> list[str]:
    mission = world.entities.get("mission")
    route = world.entities.get("route")
    rover = world.entities.get("rover")
    if mission is None or route is None or rover is None:
        return []
    if route.meters["segmented"] < THRESHOLD:
        return []
    sig = ("ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mission.meters["stalled"] = 0.0
    rover.meters["ready"] += 1
    for ent in world.entities.values():
        if ent.role in {"captain", "partner"}:
            ent.memes["hope"] += 1
    return []


def _r_finish(world: World) -> list[str]:
    rover = world.entities.get("rover")
    mission = world.entities.get("mission")
    if rover is None or mission is None:
        return []
    if rover.meters["launched"] < THRESHOLD or rover.meters["ready"] < THRESHOLD:
        return []
    sig = ("finish",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mission.meters["success"] += 1
    for ent in world.entities.values():
        if ent.role in {"captain", "partner", "robot"}:
            ent.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stall", apply=_r_stall),
    Rule(name="route_ready", apply=_r_route_ready),
    Rule(name="finish", apply=_r_finish),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out or any(True for _ in [rule] if False):
                pass
            if rule.name == "stall" and ("stall",) in world.fired:
                changed = True if ("stall",) not in getattr(propagate, "_seen", set()) else changed
            if rule.name == "route_ready" and ("ready",) in world.fired:
                changed = True if ("ready",) not in getattr(propagate, "_seen", set()) else changed
            if rule.name == "finish" and ("finish",) in world.fired:
                changed = True if ("finish",) not in getattr(propagate, "_seen", set()) else changed
        propagate._seen = set(world.fired)  # type: ignore[attr-defined]


def marker_fits(course: Course, marker: Marker) -> bool:
    return course.surface in marker.works_on


def recovery_possible(mis: Misunderstanding, marker: Marker) -> bool:
    return marker.id not in mis.blocks_markers


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for course_id, course in COURSES.items():
        for mis_id, mis in MISUNDERSTANDINGS.items():
            for marker_id, marker in MARKERS.items():
                if marker_fits(course, marker) and recovery_possible(mis, marker):
                    combos.append((course_id, mis_id, marker_id))
    return combos


def explain_rejection(course: Course, mis: Misunderstanding, marker: Marker) -> str:
    if not marker_fits(course, marker):
        return (
            f"(No story: {marker.label} does not work on {course.map_label}. "
            f"That map needs a marker that fits a {course.surface} surface.)"
        )
    return (
        f"(No story: after the {mis.wrong_object} mix-up, {marker.label} would not be available "
        f"for the repair. Pick a different marker kit.)"
    )


def intro(world: World, captain: Entity, partner: Entity, robot: Entity, course: Course) -> None:
    captain.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"{captain.id} and {partner.id} were an adventurous little space crew, and {robot.id} was their round helper robot. "
        f"One silver morning, their ship floated down beside {course.place}, under {course.sky}."
    )
    world.say(
        f"The ground below was {course.ground}, and the crew had one exciting job: {course.mission} and bring back {course.treasure}."
    )


def map_need(world: World, captain: Entity, partner: Entity, robot: Entity, course: Course) -> None:
    world.say(
        f"Inside the ship, {course.map_label} glowed on the planning table. "
        f'"Before the rover rolls," {captain.id} said, "we need segmentation so the safe path is split into easy little sections."'
    )
    world.say(
        f'{partner.id} nodded. "{robot.id}, can you help us mark the route?"'
    )
    robot.memes["attention"] += 1


def misunderstanding_beat(world: World, captain: Entity, partner: Entity, robot: Entity, mis: Misunderstanding) -> None:
    robot.memes["confused"] += 1
    propagate(world)
    world.say(
        f"But {robot.id} blinked its blue light, zipped to {mis.wrong_object}, and {mis.action_text}. "
        f"{mis.result_text}"
    )
    if mis.severity >= 2:
        world.say(
            f'{partner.id} gasped. "Oh no. We needed that for the mission table, not for cutting!"'
        )
    elif mis.severity == 1:
        world.say(
            f'{captain.id} stared for a moment. "That is very tidy," {captain.pronoun()} said, "but it is not what I meant."'
        )
    else:
        world.say(
            f'{captain.id} could not help smiling a little, but the mission still had not begun.'
        )


def feelings_beat(world: World, captain: Entity, partner: Entity, robot: Entity, mis: Misunderstanding) -> None:
    if captain.memes["worry"] >= THRESHOLD or partner.memes["worry"] >= THRESHOLD:
        world.say(
            f"For a moment, the cabin felt small and worried. The rover waited by the door, and even {robot.id}'s light drooped."
        )
    world.say(
        f'{partner.id}, who was especially {partner.traits[0]}, took a breath and said, "Segmentation does not mean chopping the nearest thing into pieces. It means making clear sections on the route map so the rover can follow them."'
    )
    robot.memes["confused"] = 0.0
    robot.memes["understanding"] += 1
    captain.memes["patience"] += 1
    partner.memes["patience"] += 1
    robot.memes["trust"] += 1


def solve(world: World, captain: Entity, partner: Entity, robot: Entity, course: Course, marker: Marker) -> None:
    route = world.get("route")
    rover = world.get("rover")
    mission = world.get("mission")
    route.meters["segmented"] += 1
    propagate(world)
    world.say(
        f"Then the three of them worked side by side. {captain.id} pointed to the turns, {partner.id} counted the safe spaces, and {robot.id} {marker.solve_text}."
    )
    world.say(
        f'Soon the path no longer looked like a jumble. It looked like a story the rover could read: first this section, then that one, then the shining place where {course.treasure} waited.'
    )
    rover.meters["launched"] += 1
    propagate(world)
    mission.meters["launched"] += 1


def ending(world: World, captain: Entity, partner: Entity, robot: Entity, course: Course, mis: Misunderstanding) -> None:
    world.say(
        f"The tiny rover rolled out with a brave hum, crossed the marked sections one by one, and reached {course.treasure}. "
        f"When it beeped its happy return signal, the whole cabin seemed to sparkle."
    )
    world.say(
        f'{robot.id} gave a soft whirr. "Next time I will ask what a big word means first," it said.'
    )
    world.say(
        f'{captain.id} patted its smooth side. "{mis.lesson_text} Asking questions is part of being a good explorer too."'
    )
    world.say(
        f"On the way home, {partner.id} looked out at {course.place} and smiled. Their mission had worked because they stopped, explained, and solved the problem together."
    )


def tell(
    course: Course,
    mis: Misunderstanding,
    marker: Marker,
    captain_name: str,
    captain_gender: str,
    partner_name: str,
    partner_gender: str,
    robot_name: str,
    trait: str,
) -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain", traits=["bold"]))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner", traits=[trait]))
    robot = world.add(Entity(id="robot", kind="character", type="robot", label=robot_name, phrase=robot_name, role="helper"))
    robot.id = robot_name
    world.entities[robot_name] = world.entities.pop("robot")
    robot = world.get(robot_name)

    world.add(Entity(id="mission", type="mission", label="mission"))
    world.add(Entity(id="route", type="route", label=course.map_label))
    world.add(Entity(id="rover", type="rover", label="tiny rover"))

    intro(world, captain, partner, robot, course)
    map_need(world, captain, partner, robot, course)

    world.para()
    misunderstanding_beat(world, captain, partner, robot, mis)
    feelings_beat(world, captain, partner, robot, mis)

    world.para()
    solve(world, captain, partner, robot, course, marker)
    ending(world, captain, partner, robot, course, mis)

    world.facts.update(
        captain=captain,
        partner=partner,
        robot=robot,
        course=course,
        misunderstanding=mis,
        marker=marker,
        mission=world.get("mission"),
        route=world.get("route"),
        rover=world.get("rover"),
        lesson_learned=robot.memes["understanding"] >= THRESHOLD,
        worried=(captain.memes["worry"] >= THRESHOLD or partner.memes["worry"] >= THRESHOLD),
        success=world.get("mission").meters["success"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    course = f["course"]
    mis = f["misunderstanding"]
    marker = f["marker"]
    robot = f["robot"]
    return [
        'Write a short Space Adventure story for a 3-to-5-year-old that includes the words "adventurous" and "segmentation".',
        f"Tell a gentle story where {captain.id}, {partner.id}, and a helper robot named {robot.id} misunderstand the word segmentation during a mission at {course.place}, then solve the problem together.",
        f"Write a child-facing story with a misunderstanding about {mis.wrong_object}, a problem-solving fix using {marker.label}, and a clear lesson about asking what words mean.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    robot = f["robot"]
    course = f["course"]
    mis = f["misunderstanding"]
    marker = f["marker"]
    rover = f["rover"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {captain.id} and {partner.id}, two young space explorers, and their helper robot {robot.id}. Together they were trying to guide a tiny rover on a mission.",
        ),
        (
            "What did the crew need to do before the rover rolled out?",
            f"They needed to do segmentation on {course.map_label} so the safe path was split into clear sections. That way the rover could follow one part at a time instead of facing a confusing jumble.",
        ),
        (
            f"What misunderstanding happened when they said the word segmentation?",
            f"{robot.id} misunderstood the word and worked on {mis.wrong_object} instead of the route map. {mis.lesson_text}",
        ),
        (
            "How did they solve the problem?",
            f"They stopped the mission for a moment, explained what segmentation really meant, and then {robot.id} {marker.qa_text}. The children helped by pointing out the turns and counting the safe spaces.",
        ),
        (
            "What lesson did the robot learn?",
            f"{robot.id} learned to ask what a big word means before acting. That helped the crew turn a mistake into a good solution instead of letting the confusion grow.",
        ),
    ]
    if f.get("worried"):
        qa.append(
            (
                "How did the crew feel in the middle of the story, and why?",
                f"They felt worried because the rover was waiting and the mission could not start until the route was clear. The misunderstanding stalled the plan, so they had to pause and explain the job carefully.",
            )
        )
    if f.get("success"):
        qa.append(
            (
                f"What happened at the end of the mission?",
                f"The rover followed the marked sections and reached {course.treasure}. The happy ending shows that careful explanation and problem solving can save an adventurous mission.",
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"segmentation", "misunderstanding", "map"}
    tags |= set(f["course"].tags)
    tags |= set(f["marker"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        course="crystal_moon",
        misunderstanding="ribbon",
        marker="laser_chalk",
        captain="Nova",
        captain_gender="girl",
        partner="Leo",
        partner_gender="boy",
        robot_name="Pip",
        trait="careful",
    ),
    StoryParams(
        course="ring_station",
        misunderstanding="snack",
        marker="magnet_arrows",
        captain="Finn",
        captain_gender="boy",
        partner="Mira",
        partner_gender="girl",
        robot_name="Orbit",
        trait="patient",
    ),
    StoryParams(
        course="dust_dunes",
        misunderstanding="snack",
        marker="trail_flags",
        captain="Ayla",
        captain_gender="girl",
        partner="Max",
        partner_gender="boy",
        robot_name="Bloop",
        trait="clever",
    ),
    StoryParams(
        course="ring_station",
        misunderstanding="ribbon",
        marker="magnet_arrows",
        captain="Theo",
        captain_gender="boy",
        partner="Ivy",
        partner_gender="girl",
        robot_name="Comet",
        trait="steady",
    ),
    StoryParams(
        course="crystal_moon",
        misunderstanding="stickers",
        marker="laser_chalk",
        captain="Nora",
        captain_gender="girl",
        partner="Eli",
        partner_gender="boy",
        robot_name="Tinker",
        trait="kind",
    ),
]


ASP_RULES = r"""
marker_fits(C, K) :- course_surface(C, S), works_on(K, S).
recovery_ok(M, K) :- misunderstanding(M), marker(K), not blocks(M, K).
valid(C, M, K) :- course(C), misunderstanding(M), marker(K), marker_fits(C, K), recovery_ok(M, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for course_id, course in COURSES.items():
        lines.append(asp.fact("course", course_id))
        lines.append(asp.fact("course_surface", course_id, course.surface))
    for mis_id in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mis_id))
    for mis_id, mis in MISUNDERSTANDINGS.items():
        for marker_id in sorted(mis.blocks_markers):
            lines.append(asp.fact("blocks", mis_id, marker_id))
    for marker_id, marker in MARKERS.items():
        lines.append(asp.fact("marker", marker_id))
        for surface in sorted(marker.works_on):
            lines.append(asp.fact("works_on", marker_id, surface))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: adventurous space crew, segmentation misunderstanding, and problem solving."
    )
    ap.add_argument("--course", choices=COURSES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    course_id = args.course
    mis_id = args.misunderstanding
    marker_id = args.marker

    if course_id and marker_id:
        course = COURSES[course_id]
        marker = MARKERS[marker_id]
        if not marker_fits(course, marker):
            mis = MISUNDERSTANDINGS[mis_id] if mis_id else next(iter(MISUNDERSTANDINGS.values()))
            raise StoryError(explain_rejection(course, mis, marker))
    if mis_id and marker_id:
        mis = MISUNDERSTANDINGS[mis_id]
        marker = MARKERS[marker_id]
        if not recovery_possible(mis, marker):
            course = COURSES[course_id] if course_id else next(iter(COURSES.values()))
            raise StoryError(explain_rejection(course, mis, marker))

    combos = [
        combo
        for combo in valid_combos()
        if (course_id is None or combo[0] == course_id)
        and (mis_id is None or combo[1] == mis_id)
        and (marker_id is None or combo[2] == marker_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    chosen_course, chosen_mis, chosen_marker = rng.choice(sorted(combos))
    captain, captain_gender = _pick_name(rng)
    partner, partner_gender = _pick_name(rng, avoid=captain)
    robot_name = rng.choice(ROBOT_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        course=chosen_course,
        misunderstanding=chosen_mis,
        marker=chosen_marker,
        captain=captain,
        captain_gender=captain_gender,
        partner=partner,
        partner_gender=partner_gender,
        robot_name=robot_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.course not in COURSES:
        raise StoryError(f"(Unknown course: {params.course})")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(f"(Unknown misunderstanding: {params.misunderstanding})")
    if params.marker not in MARKERS:
        raise StoryError(f"(Unknown marker: {params.marker})")

    course = COURSES[params.course]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    marker = MARKERS[params.marker]
    if not marker_fits(course, marker) or not recovery_possible(mis, marker):
        raise StoryError(explain_rejection(course, mis, marker))

    world = tell(
        course=course,
        mis=mis,
        marker=marker,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        robot_name=params.robot_name,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Random smoke test failed: generated story was empty.)")
        print("OK: random resolve_params() + generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (course, misunderstanding, marker) combos:\n")
        for course_id, mis_id, marker_id in combos:
            print(f"  {course_id:13} {mis_id:14} {marker_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.captain}, {p.partner}, and {p.robot_name}: {p.course} / {p.misunderstanding} / {p.marker}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
