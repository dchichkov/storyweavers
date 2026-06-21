#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prolong_parasol_vanquish_dialogue_problem_solving_space.py

A small standalone storyworld about two young space explorers who face a bright,
practical problem and solve it through dialogue. Every story includes the words
"prolong", "parasol", and "vanquish" in a child-facing way.

Domain sketch
-------------
Two children are out on a tiny space mission near their family base. A useful
thing in the bright light starts to overheat, wilt, or drip before an important
job is done. The children talk, think, and try to use a shiny parasol with some
kind of support. Good support can keep the shade steady long enough to prolong
the task and vanquish the harsh glare. Weak support can fail, leading to a safe
retreat and a gentler lesson about planning.

Run it
------
python storyworlds/worlds/gpt-5.4/prolong_parasol_vanquish_dialogue_problem_solving_space.py
python storyworlds/worlds/gpt-5.4/prolong_parasol_vanquish_dialogue_problem_solving_space.py --place crater_rim --problem rover --aid magnetic_stand
python storyworlds/worlds/gpt-5.4/prolong_parasol_vanquish_dialogue_problem_solving_space.py --problem map --aid hand_hold --delay 1
python storyworlds/worlds/gpt-5.4/prolong_parasol_vanquish_dialogue_problem_solving_space.py --all
python storyworlds/worlds/gpt-5.4/prolong_parasol_vanquish_dialogue_problem_solving_space.py --verify
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


@dataclass
class Place:
    id: str
    label: str
    scene: str
    sky: str
    base: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    subject: str
    subject_the: str
    need: str
    danger: str
    goal: str
    result: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    method: str
    fail: str
    qa_text: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


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
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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


def _r_heat_worry(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    if not target or target.meters["heat"] < THRESHOLD:
        return out
    sig = ("worry", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    world.get("scene").meters["risk"] += 1
    out.append("__worry__")
    return out


def _r_shade_cools(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    parasol = world.entities.get("parasol")
    if not target or not parasol:
        return out
    if parasol.meters["steady"] < THRESHOLD or target.meters["heat"] < THRESHOLD:
        return out
    sig = ("cool", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["heat"] = 0.0
    target.meters["stable"] += 1
    out.append("__cool__")
    return out


CAUSAL_RULES = [
    Rule(name="heat_worry", tag="emotional", apply=_r_heat_worry),
    Rule(name="shade_cools", tag="physical", apply=_r_shade_cools),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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
    "crater_rim": Place(
        id="crater_rim",
        label="the crater rim",
        scene="a silver path along the edge of a round moon crater",
        sky="The stars looked close enough to scoop with a mitten.",
        base="the little round base below",
        tags={"space", "crater"},
    ),
    "glass_dome": Place(
        id="glass_dome",
        label="the glass dome garden",
        scene="a clear dome full of red dust pots and tiny glowing leaves",
        sky="Above them, Saturn-like rings shone through the glass.",
        base="the air-lock tunnel",
        tags={"space", "garden"},
    ),
    "ice_cave": Place(
        id="ice_cave",
        label="the blue ice cave mouth",
        scene="a blue cave where the light bounced off frozen walls",
        sky="Outside, a pale planet hung over the ridge.",
        base="the warm rover shed",
        tags={"space", "ice"},
    ),
}

PROBLEMS = {
    "sprout": Problem(
        id="sprout",
        subject="star sprout",
        subject_the="the star sprout",
        need="soft shade",
        danger="its tiny leaves were curling under the fierce beam from above",
        goal="wait until the watering mist finished",
        result="the little sprout lifted its silver leaves again",
        severity=1,
        tags={"plant", "shade"},
    ),
    "map": Problem(
        id="map",
        subject="ice map",
        subject_the="the ice map",
        need="steady shade",
        danger="bright light was making its careful frozen lines drip away",
        goal="last until the cave route was copied",
        result="the icy map kept its shape long enough to copy every turn",
        severity=2,
        tags={"ice", "map", "shade"},
    ),
    "rover": Problem(
        id="rover",
        subject="scout rover",
        subject_the="the scout rover",
        need="firm shade",
        danger="its battery case was growing hot while it tried to send the last part of a message",
        goal="finish the beacon upload",
        result="the little rover chirped when the final blue bar reached the end",
        severity=2,
        tags={"robot", "signal", "shade"},
    ),
}

AIDS = {
    "magnetic_stand": Aid(
        id="magnetic_stand",
        label="magnetic stand",
        phrase="a snap-open magnetic stand",
        method="snapped the parasol onto a magnetic stand so it stayed still even when they let go",
        fail="snapped the parasol onto a magnetic stand, but they were already too late to save the task outside",
        qa_text="snapped the parasol onto a magnetic stand and held the shade steady",
        sense=3,
        power=3,
        tags={"magnet", "tool"},
    ),
    "robot_arm": Aid(
        id="robot_arm",
        label="helper arm",
        phrase="the rover's helper arm",
        method="clipped the parasol to the rover's helper arm and tilted it until the shadow covered exactly the right spot",
        fail="clipped the parasol to the helper arm, but the heat had already run too far ahead",
        qa_text="clipped the parasol to the helper arm and aimed the shadow carefully",
        sense=3,
        power=2,
        tags={"robot", "tool"},
    ),
    "hand_hold": Aid(
        id="hand_hold",
        label="hand hold",
        phrase="their own gloved hands",
        method="took turns holding the parasol as still as they could",
        fail="took turns holding the parasol, but their arms shook and the shade kept slipping away",
        qa_text="took turns holding the parasol by hand",
        sense=2,
        power=1,
        tags={"hands", "tool"},
    ),
    "balloon_string": Aid(
        id="balloon_string",
        label="balloon string",
        phrase="a party balloon string from the supply drawer",
        method="tried to tie the parasol with a balloon string",
        fail="tried to tie the parasol with a balloon string, which was far too flimsy for a real space chore",
        qa_text="tried to tie the parasol with a balloon string",
        sense=1,
        power=0,
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nova", "Ayla", "Zuri", "Cleo", "Iris"]
BOY_NAMES = ["Jax", "Milo", "Orin", "Leo", "Finn", "Nico", "Rex", "Theo"]
TRAITS = ["careful", "brave", "curious", "clever", "steady", "thoughtful"]


def sensible_aids() -> list[Aid]:
    return [aid for aid in AIDS.values() if aid.sense >= SENSE_MIN]


def task_severity(problem: Problem, delay: int) -> int:
    return problem.severity + delay


def is_solved(aid: Aid, problem: Problem, delay: int) -> bool:
    return aid.power >= task_severity(problem, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for problem_id in PROBLEMS:
            for aid_id, aid in AIDS.items():
                if aid.sense >= SENSE_MIN:
                    combos.append((place_id, problem_id, aid_id))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    aid: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def introduce(world: World, leader: Entity, partner: Entity, place: Place) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
    world.say(
        f"{leader.id} and {partner.id} bounced along {place.scene}. {place.sky}"
    )
    world.say(
        f"They were junior space scouts, and today's job was simple: help, notice, and come back with a story."
    )


def discover_problem(world: World, leader: Entity, partner: Entity, place: Place, problem: Problem) -> None:
    target = world.get("target")
    target.meters["heat"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near {place.label}, they stopped short. {problem.subject_the.capitalize()} needed {problem.need}, but {problem.danger}."
    )
    world.say(
        f'"Oh no," said {partner.id}. "If we do nothing, it may not {problem.goal}."'
    )


def brainstorm(world: World, leader: Entity, partner: Entity, problem: Problem) -> None:
    leader.memes["focus"] += 1
    partner.memes["focus"] += 1
    world.say(
        f'{leader.id} looked at the bright beam, then at the folded silver parasol hanging from the supply hook. '
        f'"Maybe the parasol can help," {leader.pronoun()} said.'
    )
    world.say(
        f'"We do not need to fight the whole sky," said {partner.id}. "We only need to prolong a patch of shade until it can {problem.goal}."'
    )
    world.say(
        f'{leader.id} nodded. "Then let\'s think like real explorers and vanquish the glare one step at a time."'
    )


def choose_plan(world: World, leader: Entity, partner: Entity, aid: Aid) -> None:
    world.say(
        f'"What can hold it steady?" asked {partner.id}.'
    )
    if aid.id == "magnetic_stand":
        world.say(
            f'"The {aid.label}!" said {leader.id}. "If we use {aid.phrase}, the parasol can stand by itself."'
        )
    elif aid.id == "robot_arm":
        world.say(
            f'"The rover can help us," said {leader.id}. "Its {aid.label} can point the parasol exactly where we need it."'
        )
    elif aid.id == "hand_hold":
        world.say(
            f'"We can use {aid.phrase}," said {leader.id}. "I will count, and we can take turns so nobody gets tired too fast."'
        )
    else:
        world.say(
            f'"Maybe {aid.phrase} can work," said {leader.id}, though the idea already sounded wobbly.'
        )


def attempt_fix(world: World, aid: Aid, problem: Problem, delay: int) -> bool:
    parasol = world.get("parasol")
    target = world.get("target")
    if is_solved(aid, problem, delay):
        parasol.meters["steady"] += 1
        target.meters["protected"] += 1
        propagate(world, narrate=False)
        return True
    parasol.meters["steady"] += 0.2
    target.meters["heat"] += 1
    propagate(world, narrate=False)
    return False


def success_scene(world: World, leader: Entity, partner: Entity, aid: Aid, problem: Problem, place: Place) -> None:
    target = world.get("target")
    leader.memes["relief"] += 1
    partner.memes["relief"] += 1
    leader.memes["pride"] += 1
    partner.memes["pride"] += 1
    world.say(
        f"They hurried to work. {leader.id} opened the parasol wide, and {partner.id} {aid.method}."
    )
    if target.meters["stable"] >= THRESHOLD:
        world.say(
            f"At once, the hard light slid away from {problem.subject_the}, and the hot hurry in the moment softened."
        )
    world.say(
        f"They waited together, counting softly until {problem.result}."
    )
    world.say(
        f'"We did it," whispered {partner.id}. "{leader.id}, we really did prolong the good part."'
    )
    world.say(
        f"On the way back toward {place.base}, the folded parasol bumped against their pack like a little silver flag of victory."
    )


def fail_scene(world: World, leader: Entity, partner: Entity, aid: Aid, problem: Problem, place: Place) -> None:
    leader.memes["worry"] += 1
    partner.memes["worry"] += 1
    leader.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    world.say(
        f"They tried at once. {leader.id} opened the parasol wide, and {partner.id} {aid.fail}."
    )
    world.say(
        f"The children looked at each other and made the brave choice. They could not finish the job outside, but they could still protect everyone and save what they could."
    )
    world.say(
        f'"Back to {place.base}," said {leader.id}. "We can ask for better gear and try again."'
    )
    world.say(
        f"So they carried {problem.subject_the} toward shelter, still talking, still thinking, and proud that real explorers know when to change the plan."
    )


def tell(
    place: Place,
    problem: Problem,
    aid: Aid,
    leader_name: str = "Nova",
    leader_gender: str = "girl",
    partner_name: str = "Jax",
    partner_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "clever",
    delay: int = 0,
) -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=[trait],
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=["loyal"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    scene = world.add(Entity(id="scene", type="place", label=place.label))
    parasol = world.add(Entity(
        id="parasol",
        type="tool",
        label="parasol",
        phrase="a silver parasol",
        tags={"parasol", "shade"},
    ))
    target = world.add(Entity(
        id="target",
        type="target",
        label=problem.subject,
        phrase=problem.subject_the,
        tags=set(problem.tags),
    ))

    introduce(world, leader, partner, place)
    world.para()
    discover_problem(world, leader, partner, place, problem)
    brainstorm(world, leader, partner, problem)
    choose_plan(world, leader, partner, aid)
    world.para()

    solved = attempt_fix(world, aid, problem, delay)
    if solved:
        success_scene(world, leader, partner, aid, problem, place)
    else:
        fail_scene(world, leader, partner, aid, problem, place)

    world.facts.update(
        place=place,
        problem=problem,
        aid=aid,
        leader=leader,
        partner=partner,
        parent=parent,
        parasol=parasol,
        target=target,
        solved=solved,
        delay=delay,
        severity=task_severity(problem, delay),
    )
    return world


KNOWLEDGE = {
    "parasol": [
        (
            "What is a parasol?",
            "A parasol is like an umbrella for shade. It blocks bright light so something underneath stays cooler."
        )
    ],
    "shade": [
        (
            "Why can shade help something in bright light?",
            "Shade blocks some of the strong light and heat. That can keep a plant, a tool, or even a person from getting too hot."
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet can stick to some kinds of metal. That makes it useful for holding things in place."
        )
    ],
    "robot": [
        (
            "What is a rover?",
            "A rover is a small robot that can drive around and help explore a place. It can carry tools and send messages back home."
        )
    ],
    "signal": [
        (
            "What is a beacon message?",
            "A beacon message is a signal sent to tell others where you are or what you found. In space, clear signals help teams stay safe."
        )
    ],
    "plant": [
        (
            "Why do small plants sometimes need shade?",
            "Very strong light can be too much for a small plant, especially when it is already thirsty or tender. A little shade can help it recover."
        )
    ],
    "ice": [
        (
            "Why does ice change in bright warmth?",
            "Ice melts when it gets warm enough. If it melts too much, the shape and lines in it can disappear."
        )
    ],
    "problem_solving": [
        (
            "What does it mean to solve a problem?",
            "Solving a problem means noticing what is wrong, thinking of a plan, and trying a helpful step. Good problem solving often means changing the plan if the first idea is weak."
        )
    ],
}
KNOWLEDGE_ORDER = ["parasol", "shade", "magnet", "robot", "signal", "plant", "ice", "problem_solving"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    place = f["place"]
    problem = f["problem"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "prolong", "parasol", and "vanquish".',
        f"Tell a dialogue-rich story where {leader.id} and {partner.id} use problem solving near {place.label} to protect {problem.subject_the}.",
        f"Write a gentle story where two young space scouts notice trouble, talk through a plan, and use a parasol to help something last longer."
    ]


def pair_noun(leader: Entity, partner: Entity) -> str:
    if leader.type == "girl" and partner.type == "girl":
        return "two young space girls"
    if leader.type == "boy" and partner.type == "boy":
        return "two young space boys"
    return "two young space scouts"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    place = f["place"]
    problem = f["problem"]
    aid = f["aid"]
    solved = f["solved"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(leader, partner)}, {leader.id} and {partner.id}. They were out on a small mission near {place.label}."
        ),
        (
            "What problem did they notice?",
            f"They noticed that {problem.subject_the} was in trouble because {problem.danger}. That mattered because it still needed to {problem.goal}."
        ),
        (
            "How did the children try to solve the problem?",
            f"They talked the problem through and chose to use a parasol for shade. Then they used {aid.phrase} to keep the parasol where it needed to be."
        ),
    ]
    if solved:
        qa.append((
            "Why did their plan work?",
            f"Their plan worked because the shade stayed steady long enough to protect {problem.subject_the}. That let it {problem.goal}, which is why the story says they could prolong the good part."
        ))
        qa.append((
            "How did they vanquish the problem?",
            f"They did not fight with force. They vanquished the glare by understanding it, making a careful plan, and placing the parasol in the right spot."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily because {problem.result}. The children walked back toward safety with the parasol like a little sign that they had solved something together."
        ))
    else:
        qa.append((
            "Why did their first plan fail?",
            f"The idea was not silly, but it was too weak for how urgent the problem had become. The shade kept slipping, so {problem.subject_the} could not finish its job outside."
        ))
        qa.append((
            "What did the children do after that?",
            f"They chose safety and went back for better help instead of pretending the weak plan was enough. That is still good problem solving, because changing the plan can be the smartest step."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, though not perfectly. The children carried the problem back toward shelter and learned that brave explorers use stronger tools when a job needs them."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"parasol", "shade", "problem_solving"}
    tags |= set(f["problem"].tags)
    tags |= set(f["aid"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="crater_rim",
        problem="rover",
        aid="magnetic_stand",
        leader="Nova",
        leader_gender="girl",
        partner="Jax",
        partner_gender="boy",
        parent="mother",
        trait="clever",
        delay=0,
    ),
    StoryParams(
        place="glass_dome",
        problem="sprout",
        aid="hand_hold",
        leader="Mira",
        leader_gender="girl",
        partner="Leo",
        partner_gender="boy",
        parent="father",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        place="ice_cave",
        problem="map",
        aid="robot_arm",
        leader="Theo",
        leader_gender="boy",
        partner="Iris",
        partner_gender="girl",
        parent="mother",
        trait="thoughtful",
        delay=0,
    ),
    StoryParams(
        place="crater_rim",
        problem="map",
        aid="hand_hold",
        leader="Nico",
        leader_gender="boy",
        partner="Cleo",
        partner_gender="girl",
        parent="father",
        trait="steady",
        delay=1,
    ),
]


def explain_aid(aid_id: str) -> str:
    aid = AIDS[aid_id]
    better = ", ".join(sorted(a.id for a in sensible_aids()))
    return (
        f"(Refusing aid '{aid_id}': it scores too low on common sense "
        f"(sense={aid.sense} < {SENSE_MIN}). Try a steadier plan such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "solved" if is_solved(AIDS[params.aid], PROBLEMS[params.problem], params.delay) else "retreat"


ASP_RULES = r"""
sensible(A) :- aid(A), sense(A, S), sense_min(M), S >= M.
valid(P, Pr, A) :- place(P), problem(Pr), aid(A), sensible(A).

severity(Pr, V) :- chosen_problem(Pr), base_severity(Pr, B), delay(D), V = B + D.
solved :- chosen_aid(A), chosen_problem(Pr), power(A, P), severity(Pr, V), P >= V.
outcome(solved) :- solved.
outcome(retreat) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for prid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", prid))
        lines.append(asp.fact("base_severity", prid, problem.severity))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        lines.append(asp.fact("power", aid_id, aid.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_aid", params.aid),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    clingo_sens = set(asp_sensible())
    python_sens = {aid.id for aid in sensible_aids()}
    if clingo_sens == python_sens:
        print(f"OK: sensible aids match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print("MISMATCH in sensible aids:")
        print("  clingo:", sorted(clingo_sens))
        print("  python:", sorted(python_sens))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure storyworld: two children talk through a bright problem and use a parasol to solve it."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra urgency before the children act")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.aid and AIDS[args.aid].sense < SENSE_MIN:
        raise StoryError(explain_aid(args.aid))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, problem_id, aid_id = rng.choice(sorted(combos))
    leader, leader_gender = _pick_kid(rng)
    partner, partner_gender = _pick_kid(rng, avoid=leader)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)

    return StoryParams(
        place=place_id,
        problem=problem_id,
        aid=aid_id,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if AIDS[params.aid].sense < SENSE_MIN:
        raise StoryError(explain_aid(params.aid))

    world = tell(
        place=PLACES[params.place],
        problem=PROBLEMS[params.problem],
        aid=AIDS[params.aid],
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("", "#show sensible/1.\n#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible aids: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, problem, aid) combos:\n")
        for place, problem, aid in combos:
            print(f"  {place:12} {problem:8} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader} & {p.partner}: {p.problem} at {p.place} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
