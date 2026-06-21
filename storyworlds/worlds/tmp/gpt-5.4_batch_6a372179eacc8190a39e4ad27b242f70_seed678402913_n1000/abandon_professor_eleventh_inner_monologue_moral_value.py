#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/abandon_professor_eleventh_inner_monologue_moral_value.py
====================================================================================

A standalone storyworld about a child space student, a stranded robot friend, and
a professor who teaches that you should not abandon a teammate just because a
problem slows you down.

Seed requirements carried into the world:
- words: abandon, professor, eleventh
- features: Inner Monologue, Moral Value, Foreshadowing
- style: Space Adventure

The core domain:
    On the eleventh training voyage, a child explorer and a professor land in a
    wondrous place. A small robot helper gets stuck just as a warning sign
    hinted at earlier begins to matter. The child briefly considers whether to
    abandon the robot and rush back to safety. A sensible rescue tool and a
    moral lesson shape the ending.

The model prefers reasonable rescue methods only. It also carries an ASP twin
for the compatibility gate and the outcome model.
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

# Make shared result containers importable when this script is run directly from
# the repo root or from inside this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVE_INIT = 4.0
KIND_INIT = 5.0
STEADFAST_TRAITS = {"steady", "kind", "patient", "brave"}


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "professor_f"}
        male = {"boy", "man", "father", "professor_m"}
        robot = {"robot", "rover"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in robot:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type.startswith("professor"):
            return "professor"
        return self.type


# ---------------------------------------------------------------------------
# Domain configs.
# ---------------------------------------------------------------------------
@dataclass
class Mission:
    id: str
    place: str = ""
    scene: str = ""
    goal: str = ""
    shimmer: str = ""
    foreshadow: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str = ""
    phrase: str = ""
    severity: int = 1
    surface: str = ""
    sign: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str = ""
    phrase: str = ""
    sense: int = 2
    power: int = 2
    works_on: set[str] = field(default_factory=set)
    action: str = ""
    delayed_action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class CompanionCfg:
    id: str
    label: str = ""
    phrase: str = ""
    cargo: str = ""
    voice: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mission: str
    hazard: str
    tool: str
    companion: str
    child_name: str
    child_gender: str
    professor_name: str
    professor_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World and rules.
# ---------------------------------------------------------------------------
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

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stuck_worry(world: World) -> list[str]:
    out: list[str] = []
    robot = world.entities.get("companion")
    child = world.entities.get("child")
    if not robot or not child:
        return out
    if robot.meters["stuck"] < THRESHOLD:
        return out
    sig = ("stuck_worry", robot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["tempted_to_abandon"] += 1
    out.append("__stuck__")
    return out


def _r_warning_urgency(world: World) -> list[str]:
    out: list[str] = []
    robot = world.entities.get("companion")
    place = world.entities.get("place")
    prof = world.entities.get("professor")
    if not robot or not place or not prof:
        return out
    if robot.meters["stuck"] < THRESHOLD or place.meters["warning"] < THRESHOLD:
        return out
    sig = ("warning_urgency", robot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prof.memes["urgency"] += 1
    place.meters["risk"] += 1
    out.append("__urgency__")
    return out


CAUSAL_RULES = [
    Rule(name="stuck_worry", tag="social", apply=_r_stuck_worry),
    Rule(name="warning_urgency", tag="physical", apply=_r_warning_urgency),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraints and outcome model.
# ---------------------------------------------------------------------------
def compatible(tool: Tool, hazard: Hazard) -> bool:
    return hazard.id in tool.works_on


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id in MISSIONS:
        for companion_id in COMPANIONS:
            for hazard_id, hazard in HAZARDS.items():
                for tool_id, tool in TOOLS.items():
                    if tool.sense >= SENSE_MIN and compatible(tool, hazard):
                        combos.append((mission_id, hazard_id, tool_id, companion_id))
    return combos


def rescue_difficulty(hazard: Hazard, delay: int) -> int:
    return hazard.severity + delay


def is_immediate(tool: Tool, hazard: Hazard, delay: int) -> bool:
    return tool.power >= rescue_difficulty(hazard, delay)


def child_stands_fast(trait: str) -> bool:
    return trait in STEADFAST_TRAITS


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    hazard = HAZARDS[params.hazard]
    return "immediate" if is_immediate(tool, hazard, params.delay) else "return"


def explain_rejection(tool: Tool, hazard: Hazard) -> str:
    if tool.sense < SENSE_MIN:
        better = ", ".join(sorted(t.id for t in sensible_tools()))
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). Try a sensible rescue tool like {better}.)"
        )
    return (
        f"(No story: {tool.label} does not make sense for {hazard.phrase}. "
        f"Pick a tool that can really help on that kind of surface.)"
    )


# ---------------------------------------------------------------------------
# World actions.
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, professor: Entity, mission: Mission, companion: Entity) -> None:
    world.say(
        f"On the eleventh training voyage of the little school shuttle, {child.id} "
        f"buckled in beside Professor {professor.id} and their helper {companion.label}."
    )
    world.say(
        f"They were headed for {mission.place}, where {mission.scene}. Their job was to {mission.goal}."
    )
    child.memes["wonder"] += 1
    professor.memes["care"] += 1


def foreshadow(world: World, mission: Mission, hazard: Hazard) -> None:
    place = world.get("place")
    place.meters["warning"] += 1
    world.say(
        f"As they stepped out, {mission.shimmer}. {mission.foreshadow} It was a tiny sign, "
        f"but it matched the way Professor {world.get('professor').id} glanced at the ground."
    )
    world.facts["foreshadow_text"] = hazard.sign


def bond(world: World, child: Entity, companion: Entity) -> None:
    child.memes["care"] += 1
    world.say(
        f"{companion.label.capitalize()} rolled ahead with a cheerful {companion.voice} and carried {companion.attrs['cargo']}."
    )
    world.say(
        f"{child.id} liked the way it always turned back to be sure nobody was left behind."
    )


def slip(world: World, child: Entity, companion: Entity, hazard: Hazard) -> None:
    companion.meters["stuck"] += 1
    companion.meters["risk"] += float(hazard.severity)
    propagate(world, narrate=False)
    world.say(
        f"Then the trouble came. {companion.label.capitalize()} reached {hazard.phrase} and dropped with a clunk."
    )
    world.say(
        f"One wheel spun in the air, and {companion.pronoun()} gave a worried {companion.voice}."
    )


def inner_monologue(world: World, child: Entity, companion: Entity, hazard: Hazard) -> None:
    child.memes["doubt"] += 1
    if child_stands_fast(child.traits[0]):
        thought = (
            f"{child.id} felt a fast little thought flicker through {child.pronoun('possessive')} head: "
            f'"If I hurry, maybe we can get back before the dust moves in. But I do not want to abandon {companion.label}."'
        )
    else:
        thought = (
            f"{child.id} felt a scared thought thump inside {child.pronoun('possessive')} helmet: "
            f'"If we abandon {companion.label} now, we can still run back before {hazard.label} gets worse."'
        )
    world.say(thought)


def professor_lesson(world: World, child: Entity, professor: Entity, companion: Entity) -> None:
    professor.memes["lesson"] += 1
    child.memes["shame"] += 1
    world.say(
        f'Professor {professor.id} knelt beside the track marks and spoke calmly. '
        f'"A true space crew does not abandon a teammate for the sake of speed," {professor.pronoun()} said.'
    )
    world.say(
        f'"We stop, think, and help. That is how brave hearts work when fear starts making noisy ideas."'
    )


def choose_rescue(world: World, child: Entity, professor: Entity, tool: Tool, hazard: Hazard, companion: Entity) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"{child.id} took one deep breath and reached for {tool.phrase}. Together they {tool.action}."
    )
    world.facts["used_tool"] = tool.label
    world.facts["hazard_phrase"] = hazard.phrase
    world.facts["considered_abandon"] = True
    world.facts["moral"] = "Do not abandon a teammate when you can stop and help wisely."


def rescue_now(world: World, child: Entity, professor: Entity, tool: Tool, companion: Entity, mission: Mission) -> None:
    companion.meters["stuck"] = 0.0
    companion.meters["safe"] += 1
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    world.say(
        f"In one strong pull, {companion.label} bumped free. Dust puffed around its wheels, "
        f"but soon it was beside them again, bright lens blinking happily."
    )
    world.say(
        f'"Thank you," beeped {companion.label}, and even the stars seemed to sparkle harder over {mission.place}.'
    )


def mark_and_return(world: World, child: Entity, professor: Entity, tool: Tool, companion: Entity, mission: Mission) -> None:
    child.memes["patience"] += 1
    child.memes["relief"] += 1
    world.say(
        f"The tool was not strong enough to free {companion.label} right away. Instead of leaving in a panic, "
        f"Professor {professor.id} clipped a warm locator light onto the rim and covered {companion.pronoun('possessive')} case with a heat cloth."
    )
    world.say(
        f'"We are not abandoning {companion.label}," {professor.pronoun()} said. "We are making a safe plan and coming back."'
    )
    world.say(
        f"They returned to the shuttle, fetched the bigger rescue arm, and came back before the sky turned dark. "
        f"This time {companion.label} rolled free, and the little team cheered under {mission.ending}."
    )
    companion.meters["stuck"] = 0.0
    companion.meters["safe"] += 1
    world.facts["returned_later"] = True


def ending(world: World, child: Entity, professor: Entity, companion: Entity, mission: Mission) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"On the ride home, {child.id} looked out at the stars and thought about the noisy idea {child.pronoun()} had almost followed."
    )
    world.say(
        f"{child.pronoun().capitalize()} was glad {child.pronoun()} had listened instead. {mission.ending.capitalize()} felt like proof that kindness could shine as brightly as any rocket."
    )


def tell(
    mission: Mission,
    hazard: Hazard,
    tool: Tool,
    companion_cfg: CompanionCfg,
    child_name: str,
    child_gender: str,
    professor_name: str,
    professor_gender: str,
    trait: str,
    delay: int,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
    ))
    professor_type = "professor_f" if professor_gender == "woman" else "professor_m"
    professor = world.add(Entity(
        id=professor_name,
        kind="character",
        type=professor_type,
        role="professor",
        traits=["calm", "wise"],
    ))
    companion = world.add(Entity(
        id="companion",
        kind="thing",
        type="robot",
        label=companion_cfg.label,
        phrase=companion_cfg.phrase,
        role="companion",
        tags=set(companion_cfg.tags),
        attrs={"cargo": companion_cfg.cargo},
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=mission.place,
        phrase=mission.place,
    ))

    introduce(world, child, professor, mission, companion)
    bond(world, child, companion)
    world.para()
    foreshadow(world, mission, hazard)
    slip(world, child, companion, hazard)
    inner_monologue(world, child, companion, hazard)
    world.para()
    professor_lesson(world, child, professor, companion)
    choose_rescue(world, child, professor, tool, hazard, companion)

    if is_immediate(tool, hazard, delay):
        rescue_now(world, child, professor, tool, companion, mission)
        outcome = "immediate"
    else:
        mark_and_return(world, child, professor, tool, companion, mission)
        outcome = "return"

    world.para()
    ending(world, child, professor, companion, mission)
    world.facts.update(
        child=child,
        professor=professor,
        companion=companion,
        mission=mission,
        hazard=hazard,
        tool=tool,
        delay=delay,
        outcome=outcome,
        immediate=(outcome == "immediate"),
        considered_abandon=True,
        moral_value="loyalty",
    )
    return world


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
MISSIONS = {
    "moon_garden": Mission(
        id="moon_garden",
        place="the Moon Garden Dome",
        scene="silver leaves floated under a glass sky",
        goal="collect dew pearls for the classroom greenhouse",
        shimmer="the dome windows held a thin blue shine",
        foreshadow="Far above them, one warning light on the shuttle blinked and then went still",
        ending="the dome glass glowing like a bowl of morning",
        tags={"space", "moon"},
    ),
    "ring_caves": Mission(
        id="ring_caves",
        place="the Ring Caves of Selene",
        scene="crystal walls threw rainbow bands across the dust",
        goal="map a safe path for the next class",
        shimmer="the cave mouths glittered like frozen bells",
        foreshadow="From deep inside came a small shiver, as if the cave was clearing its throat",
        ending="the rainbow cave walls softly glowing behind them",
        tags={"space", "cave"},
    ),
    "comet_bay": Mission(
        id="comet_bay",
        place="Comet Bay",
        scene="blue ice hummed beside a slow river of stars",
        goal="plant bright marker flags for the astronomy club",
        shimmer="the ice gave off a pearly light under their boots",
        foreshadow="A soft groan moved through the frozen ground, gentle now but not friendly",
        ending="the comet plain shining with quiet blue light",
        tags={"space", "comet"},
    ),
}

HAZARDS = {
    "crack": Hazard(
        id="crack",
        label="the widening crack",
        phrase="a widening crack in the silver ground",
        severity=2,
        surface="gap",
        sign="A crack was going to matter if anyone stepped too carelessly.",
        tags={"gap", "space"},
    ),
    "ice_rim": Hazard(
        id="ice_rim",
        label="the slick ice rim",
        phrase="a slick ice rim beside a frozen trench",
        severity=1,
        surface="slick",
        sign="The smooth ice meant one wrong slide could trap a wheel.",
        tags={"ice", "space"},
    ),
    "dust_slope": Hazard(
        id="dust_slope",
        label="the loose dust slope",
        phrase="a loose dust slope near a rock shelf",
        severity=2,
        surface="dust",
        sign="Loose dust can swallow little wheels faster than it looks.",
        tags={"dust", "space"},
    ),
}

TOOLS = {
    "tether": Tool(
        id="tether",
        label="rescue tether",
        phrase="the rescue tether",
        sense=3,
        power=2,
        works_on={"crack", "ice_rim"},
        action="hooked the tether to the robot's harness and leaned back together",
        delayed_action="left a tether marker and returned with a stronger arm",
        qa_text="They used a rescue tether to pull the robot toward safe ground",
        tags={"tether", "rescue"},
    ),
    "magnet_winch": Tool(
        id="magnet_winch",
        label="magnet winch",
        phrase="the magnet winch",
        sense=3,
        power=3,
        works_on={"crack", "ice_rim", "dust_slope"},
        action="clicked the magnet winch onto the robot's side rail and reeled slowly",
        delayed_action="marked the place and returned with the shuttle arm",
        qa_text="They used a magnet winch to reel the robot out carefully",
        tags={"winch", "rescue"},
    ),
    "foam_ramp": Tool(
        id="foam_ramp",
        label="foam ramp",
        phrase="the foam ramp pack",
        sense=2,
        power=1,
        works_on={"ice_rim", "dust_slope"},
        action="sprayed out a bumpy foam ramp so the wheels could try to climb",
        delayed_action="left a warm light and came back with a stronger tool",
        qa_text="They sprayed a foam ramp to help the robot climb",
        tags={"foam", "rescue"},
    ),
    "wave_hands": Tool(
        id="wave_hands",
        label="waving hands",
        phrase="nothing but their empty hands",
        sense=1,
        power=0,
        works_on=set(),
        action="waved their hands over the ground and hoped",
        delayed_action="did not really solve the problem",
        qa_text="They only waved their hands, which is not a real rescue method",
        tags={"bad_idea"},
    ),
}

COMPANIONS = {
    "pip": CompanionCfg(
        id="pip",
        label="Pip",
        phrase="a round scout robot",
        cargo="a tray of tiny glow-seeds",
        voice="beep-beep",
        tags={"robot"},
    ),
    "mote": CompanionCfg(
        id="mote",
        label="Mote",
        phrase="a little map rover",
        cargo="a box of star maps",
        voice="whirr",
        tags={"robot"},
    ),
    "luma": CompanionCfg(
        id="luma",
        label="Luma",
        phrase="a lantern rover",
        cargo="three moon bulbs for the greenhouse",
        voice="ping",
        tags={"robot"},
    ),
}

CHILD_NAMES = ["Kai", "Mina", "Juno", "Tess", "Rafi", "Niko", "Ivy", "Lio"]
PROFESSOR_NAMES = ["Sol", "Vega", "Nova", "Lyra"]
TRAITS = ["steady", "kind", "patient", "curious", "hasty", "brave"]


# ---------------------------------------------------------------------------
# Q&A content.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "robot": [(
        "What is a rover robot?",
        "A rover robot is a small machine that can roll across the ground and help people carry tools or learn about a place."
    )],
    "tether": [(
        "What is a rescue tether?",
        "A rescue tether is a strong line used to pull something toward safety without getting too close to danger."
    )],
    "winch": [(
        "What does a winch do?",
        "A winch winds a line or cable so it can pull something heavy in a careful, steady way."
    )],
    "foam": [(
        "What is a foam ramp?",
        "A foam ramp is a quick path made from expanding foam so wheels can climb over a slippery or dusty edge."
    )],
    "space": [(
        "Why do space explorers make careful plans?",
        "Space can be beautiful, but it can also be risky. Careful plans help explorers stay safe and help each other."
    )],
    "loyalty": [(
        "What does it mean to be loyal?",
        "Being loyal means you do not leave a friend behind when they need help. You stay kind and dependable."
    )],
    "moon": [(
        "What is a dome garden?",
        "A dome garden is a plant space covered by a clear roof so air and warmth can be kept inside."
    )],
    "cave": [(
        "Why can caves be tricky?",
        "Caves can have hidden drops, slippery places, and echoes that make danger hard to judge."
    )],
    "comet": [(
        "What is a comet?",
        "A comet is a small icy body in space that can shine when sunlight warms it."
    )],
}
KNOWLEDGE_ORDER = ["robot", "tether", "winch", "foam", "space", "loyalty", "moon", "cave", "comet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    professor = f["professor"]
    mission = f["mission"]
    companion = f["companion"]
    hazard = f["hazard"]
    tool = f["tool"]
    if f["outcome"] == "immediate":
        return [
            f'Write a Space Adventure story for a young child that includes the words "abandon", "professor", and "eleventh".',
            f"Tell a gentle space story where {child.id} almost thinks about abandoning {companion.label}, but Professor {professor.id} teaches loyalty and they rescue the robot with {tool.phrase}.",
            f"Write a story set at {mission.place} with clear inner monologue, a small foreshadowing clue, and a moral value about helping a teammate in danger near {hazard.phrase}.",
        ]
    return [
        f'Write a Space Adventure story for a young child that includes the words "abandon", "professor", and "eleventh".',
        f"Tell a space story where {child.id} is tempted to abandon {companion.label}, but Professor {professor.id} teaches patience and they make a safe plan to come back.",
        f"Write a story set at {mission.place} with clear inner monologue, foreshadowing, and a moral value about not leaving a teammate behind even when the first rescue try is too weak.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    professor = f["professor"]
    companion = f["companion"]
    mission = f["mission"]
    hazard = f["hazard"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, Professor {professor.id}, and the robot helper {companion.label}. They go on the eleventh training voyage together."
        ),
        (
            "What was the first clue that trouble might come later?",
            f"The story gives a small warning early on: {mission.foreshadow.lower()}. That foreshadowing hinted that the place was not as calm as it first looked."
        ),
        (
            f"Why did {child.id} think about the word 'abandon'?",
            f"{child.id} got scared when {companion.label} became stuck near {hazard.phrase}. In {child.pronoun('possessive')} inner monologue, {child.pronoun()} worried that leaving fast might feel safer than stopping to help."
        ),
        (
            f"What did Professor {professor.id} teach?",
            f'Professor {professor.id} taught that a real crew does not abandon a teammate just to move faster. The lesson was a moral one: bravery should stay kind, not selfish.'
        ),
    ]
    if f["outcome"] == "immediate":
        qa.append((
            f"How did they save {companion.label}?",
            f"They used the {tool.label} right away and freed {companion.label} from the danger. Their quick help worked because the tool matched the problem and they stayed calm."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the whole team safe together and the stars seeming brighter above {mission.place}. The ending image shows that kindness and courage changed fear into relief."
        ))
    else:
        qa.append((
            f"Why did they leave for a little while without abandoning {companion.label}?",
            f"The first tool was not strong enough for an immediate rescue, so they made a safe plan instead of panicking. They marked the place, promised to return, and came back with better help."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {companion.label} rescued after they returned with stronger equipment. The ending proves the lesson because planning to come back is different from abandoning someone."
        ))
    return qa


def world_knowledge_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["tool"].tags) | set(f["companion"].tags) | set(f["mission"].tags) | {"space", "loyalty"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Reasonableness gate: a tool must be sensible and compatible with the hazard.
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
compatible(T, H) :- works_on(T, H).
valid(M, H, T, C) :- mission(M), hazard(H), tool(T), companion(C),
                     sensible_tool(T), compatible(T, H).

% Outcome: immediate if the chosen tool power beats the hazard severity plus delay.
difficulty(V) :- chosen_hazard(H), severity(H, S), delay(D), V = S + D.
immediate :- chosen_tool(T), power(T, P), difficulty(V), P >= V.
outcome(immediate) :- immediate.
outcome(return) :- not immediate.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("severity", hazard_id, hazard.severity))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
        for hazard_id in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tool_id, hazard_id))
    for companion_id in COMPANIONS:
        lines.append(asp.fact("companion", companion_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_tool", params.tool),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    py_sensible = {tool.id for tool in sensible_tools()}
    asp_sensible = set(asp_sensible_tools())
    if py_sensible == asp_sensible:
        print(f"OK: sensible tools match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: python={sorted(py_sensible)} clingo={sorted(asp_sensible)}")

    cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"Default resolve failed during verify: {err}")

    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in outcome for {params}: asp={asp_outcome(params)} python={outcome_of(params)}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        mission="moon_garden",
        hazard="crack",
        tool="magnet_winch",
        companion="pip",
        child_name="Kai",
        child_gender="boy",
        professor_name="Nova",
        professor_gender="woman",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        mission="ring_caves",
        hazard="ice_rim",
        tool="foam_ramp",
        companion="mote",
        child_name="Mina",
        child_gender="girl",
        professor_name="Sol",
        professor_gender="man",
        trait="curious",
        delay=1,
    ),
    StoryParams(
        mission="comet_bay",
        hazard="dust_slope",
        tool="magnet_winch",
        companion="luma",
        child_name="Rafi",
        child_gender="boy",
        professor_name="Lyra",
        professor_gender="woman",
        trait="kind",
        delay=0,
    ),
    StoryParams(
        mission="moon_garden",
        hazard="ice_rim",
        tool="tether",
        companion="pip",
        child_name="Ivy",
        child_gender="girl",
        professor_name="Vega",
        professor_gender="woman",
        trait="hasty",
        delay=0,
    ),
    StoryParams(
        mission="comet_bay",
        hazard="dust_slope",
        tool="foam_ramp",
        companion="mote",
        child_name="Niko",
        child_gender="boy",
        professor_name="Nova",
        professor_gender="woman",
        trait="patient",
        delay=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child space explorer, a professor, and the choice not to abandon a teammate."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--professor-name")
    ap.add_argument("--professor-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra difficulty before the rescue works")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump the world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool is not None:
        tool = TOOLS[args.tool]
        if tool.sense < SENSE_MIN:
            raise StoryError(explain_rejection(tool, HAZARDS[args.hazard] if args.hazard else next(iter(HAZARDS.values()))))
    if args.tool is not None and args.hazard is not None:
        tool = TOOLS[args.tool]
        hazard = HAZARDS[args.hazard]
        if not compatible(tool, hazard):
            raise StoryError(explain_rejection(tool, hazard))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.tool is None or combo[2] == args.tool)
        and (args.companion is None or combo[3] == args.companion)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, hazard_id, tool_id, companion_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    professor_gender = args.professor_gender or rng.choice(["woman", "man"])
    professor_name = args.professor_name or rng.choice(PROFESSOR_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        mission=mission_id,
        hazard=hazard_id,
        tool=tool_id,
        companion=companion_id,
        child_name=child_name,
        child_gender=child_gender,
        professor_name=professor_name,
        professor_gender=professor_gender,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(Unknown companion: {params.companion})")

    mission = MISSIONS[params.mission]
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]
    companion = COMPANIONS[params.companion]

    if tool.sense < SENSE_MIN:
        raise StoryError(explain_rejection(tool, hazard))
    if not compatible(tool, hazard):
        raise StoryError(explain_rejection(tool, hazard))

    world = tell(
        mission=mission,
        hazard=hazard,
        tool=tool,
        companion_cfg=companion,
        child_name=params.child_name,
        child_gender=params.child_gender,
        professor_name=params.professor_name,
        professor_gender=params.professor_gender,
        trait=params.trait,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_items(world)],
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
        print(asp_program("", "#show valid/4.\n#show sensible_tool/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        print(f"{len(combos)} compatible (mission, hazard, tool, companion) combos:\n")
        for mission_id, hazard_id, tool_id, companion_id in combos:
            print(f"  {mission_id:12} {hazard_id:10} {tool_id:12} {companion_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.child_name} at {p.mission} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
