#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/monk_dim_science_elevator_sound_effects_teamwork.py
==============================================================================

A standalone storyworld about two children in an elevator on the way to a
science activity. A sudden elevator problem creates a small adventure. The
children use teamwork, silly sound effects, and a reasonable plan to stay calm
and solve the problem.

Run it
------
    python storyworlds/worlds/gpt-5.4/monk_dim_science_elevator_sound_effects_teamwork.py
    python storyworlds/worlds/gpt-5.4/monk_dim_science_elevator_sound_effects_teamwork.py --problem stuck --plan intercom
    python storyworlds/worlds/gpt-5.4/monk_dim_science_elevator_sound_effects_teamwork.py --problem dim --plan alarm_button
    python storyworlds/worlds/gpt-5.4/monk_dim_science_elevator_sound_effects_teamwork.py --all
    python storyworlds/worlds/gpt-5.4/monk_dim_science_elevator_sound_effects_teamwork.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/monk_dim_science_elevator_sound_effects_teamwork.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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


@dataclass
class Mission:
    id: str
    goal: str
    cargo: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    title: str
    burst: str
    worry: str
    resolved_by_help: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    handles: set[str]
    action: str
    success: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundGame:
    id: str
    call: str
    joke: str
    close: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return [e for e in self.entities.values() if e.role == "kid"]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_problem_fear(world: World) -> list[str]:
    out: list[str] = []
    elevator = world.get("elevator")
    if elevator.meters["trouble"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__trouble__")
    return out


def _r_teamwork_calm(world: World) -> list[str]:
    out: list[str] = []
    team = world.get("team")
    if team.meters["working_together"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("calm", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if kid.memes["fear"] > 0:
            kid.memes["fear"] -= 1
        kid.memes["calm"] += 1
        kid.memes["brave"] += 1
        out.append("__team__")
    return out


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
        for s in produced:
            world.say(s)
    return produced


CAUSAL_RULES = [
    Rule(name="problem_fear", apply=_r_problem_fear),
    Rule(name="teamwork_calm", apply=_r_teamwork_calm),
]


MISSIONS = {
    "rocket_demo": Mission(
        id="rocket_demo",
        goal="the roof for the junior science rocket demo",
        cargo="a cardboard rocket with silver paper fins",
        ending="When the doors finally opened, they marched out holding the rocket high like real explorers.",
        tags={"science", "rocket"},
    ),
    "bug_show": Mission(
        id="bug_show",
        goal="the museum floor for the science bug show",
        cargo="a clear box of paper beetle models",
        ending="When the doors slid apart, they hurried out with their beetles safe and their smiles even bigger.",
        tags={"science", "museum"},
    ),
    "star_club": Mission(
        id="star_club",
        goal="the top floor for after-school science club",
        cargo="a poster covered with stars, moons, and arrows",
        ending="When the elevator let them out, the poster rode between them like a bright flag.",
        tags={"science", "stars"},
    ),
}

PROBLEMS = {
    "stuck": Problem(
        id="stuck",
        title="stuck",
        burst="Ding-ding... thunk! The elevator gave a little hop and stopped between floors.",
        worry="The walls suddenly felt close, and the quiet after the thunk seemed much louder than before.",
        resolved_by_help=True,
        tags={"elevator", "help"},
    ),
    "dim": Problem(
        id="dim",
        title="dim",
        burst="Bzzzt! The ceiling lamp blinked and turned monk-dim, as if the elevator had put on sleepy eyebrows.",
        worry="The corners went fuzzy, and even the floor numbers looked shy.",
        resolved_by_help=False,
        tags={"elevator", "light"},
    ),
    "spill": Problem(
        id="spill",
        title="spill",
        burst="Clatter-clack! Their project box tipped, and bits of paper, tape, and rulers skittered across the elevator floor.",
        worry="For one second it looked as if their careful science work had turned into a tiny indoor storm.",
        resolved_by_help=False,
        tags={"elevator", "project"},
    ),
}

PLANS = {
    "alarm_button": Plan(
        id="alarm_button",
        label="the alarm button",
        handles={"stuck"},
        action="pressed the alarm button while the other child held the project steady and read the little safety sign out loud",
        success="A warm voice crackled from the speaker, and soon the elevator hummed back to life.",
        qa_text="They pressed the alarm button and waited together for help.",
        tags={"alarm", "help"},
    ),
    "intercom": Plan(
        id="intercom",
        label="the intercom button",
        handles={"stuck"},
        action="took turns speaking into the intercom so one child could explain the problem while the other remembered the floor number",
        success="The speaker answered right away, and after a short wait the car gave a friendly whirr and began moving again.",
        qa_text="They used the intercom and explained where they were.",
        tags={"intercom", "help"},
    ),
    "flashlight": Plan(
        id="flashlight",
        label="a backpack flashlight",
        handles={"dim"},
        action="found a small flashlight in the backpack, and one child aimed the beam while the other checked every corner for loose project pieces",
        success="The white beam made the little elevator feel less spooky, and the children could see exactly what they were doing.",
        qa_text="They used a flashlight so they could see clearly again.",
        tags={"flashlight", "light"},
    ),
    "glow_stickers": Plan(
        id="glow_stickers",
        label="their glow stickers",
        handles={"dim"},
        action="peeled two glow stickers from the project folder, put one by the buttons, and kept one beside the poster tube like a tiny moon",
        success="The glow was soft, but it was enough to turn the dark joke into a manageable puzzle.",
        qa_text="They used glow stickers to mark the dark buttons and their supplies.",
        tags={"glow", "light"},
    ),
    "sort_together": Plan(
        id="sort_together",
        label="sorting together",
        handles={"spill"},
        action="made a quick game of sorting, with one child gathering rulers while the other rescued paper pieces before shoes could crinkle them",
        success="In less than a minute the floor was clear again and their project looked neat instead of wild.",
        qa_text="They sorted the spilled pieces together so nothing important was lost.",
        tags={"sorting", "teamwork"},
    ),
    "checklist": Plan(
        id="checklist",
        label="a checklist",
        handles={"spill"},
        action="used a marker checklist from the folder, counting each piece in funny captain voices until every missing bit was found",
        success="Because they checked each part one by one, the science project ended up complete after all.",
        qa_text="They used a checklist and counted every piece until the project was complete.",
        tags={"checklist", "teamwork"},
    ),
}

SOUNDS = {
    "robot": SoundGame(
        id="robot",
        call='"Beep-boop, brave elevator crew!"',
        joke="The silly robot voice made both children snort instead of freezing up.",
        close="By the end, even the elevator seemed to answer with a polite little boop.",
        tags={"robot"},
    ),
    "drum": SoundGame(
        id="drum",
        call='"Bum-bum-ba-dum!"',
        joke="The pretend drumroll turned the scary moment into the start of an adventure.",
        close="When the ride was over, they tapped one last victory drum on the poster tube.",
        tags={"drum"},
    ),
    "spaceship": SoundGame(
        id="spaceship",
        call='"Fwoooosh to the science deck!"',
        joke="The spaceship noise was so grand inside such a tiny elevator that both children laughed.",
        close="At the end they stepped out as if they had just landed on a new planet.",
        tags={"spaceship"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli"]
TRAITS = ["steady", "curious", "careful", "sparky", "thoughtful", "brave"]

KNOWLEDGE = {
    "elevator": [
        (
            "What does an elevator do?",
            "An elevator is a small room that moves people up and down between floors in a building.",
        )
    ],
    "alarm": [
        (
            "What is an elevator alarm button for?",
            "An elevator alarm button is there to call for help if there is a problem. It lets grown-ups or building workers know that someone needs help.",
        )
    ],
    "intercom": [
        (
            "What is an intercom?",
            "An intercom is a speaker and microphone that lets people talk to each other from different places.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight makes light without a flame, so it helps you see where things are safely.",
        )
    ],
    "glow": [
        (
            "What are glow stickers?",
            "Glow stickers are stickers that shine softly after they have been in light. They can help you spot things in the dark.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other on the same job. One person can do one part while another person does another part.",
        )
    ],
    "checklist": [
        (
            "What is a checklist for?",
            "A checklist is a list you follow step by step so you do not forget important things.",
        )
    ],
    "science": [
        (
            "What is science?",
            "Science is a way of learning how the world works by noticing, asking questions, and testing ideas.",
        )
    ],
}
KNOWLEDGE_ORDER = ["elevator", "alarm", "intercom", "flashlight", "glow", "teamwork", "checklist", "science"]


def plan_fits(problem_id: str, plan_id: str) -> bool:
    return problem_id in PLANS[plan_id].handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for problem_id in PROBLEMS:
            for plan_id in PLANS:
                if plan_fits(problem_id, plan_id):
                    combos.append((mission_id, problem_id, plan_id))
    return combos


def predict_success(world: World, plan: Plan, problem: Problem) -> bool:
    sim = world.copy()
    elevator = sim.get("elevator")
    team = sim.get("team")
    team.meters["working_together"] += 1
    if problem.id == "stuck" and "stuck" in plan.handles:
        elevator.meters["trouble"] = 0
    elif problem.id == "dim" and "dim" in plan.handles:
        elevator.meters["dark"] = 0
        elevator.meters["trouble"] = 0
    elif problem.id == "spill" and "spill" in plan.handles:
        sim.get("cargo").meters["scattered"] = 0
        elevator.meters["trouble"] = 0
    propagate(sim, narrate=False)
    return elevator.meters["trouble"] < THRESHOLD


def introduce(world: World, a: Entity, b: Entity, adult: Entity, mission: Mission) -> None:
    world.say(
        f"{a.id} and {b.id} hurried into the elevator with {adult.label_word} and "
        f"{mission.cargo}. They were heading to {mission.goal}, and the whole trip felt like the start of an adventure."
    )
    world.say(
        f"Above the buttons, the tiny floor-number panel glowed monk-dim, but the children did not mind. "
        f"They were too busy talking about science and what might happen when they arrived."
    )


def build_playful_mood(world: World, a: Entity, b: Entity, sound: SoundGame) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f'{a.id} whispered {sound.call} {sound.joke}'
    )


def trouble_strikes(world: World, problem: Problem) -> None:
    elevator = world.get("elevator")
    elevator.meters["trouble"] += 1
    if problem.id == "dim":
        elevator.meters["dark"] += 1
    if problem.id == "spill":
        world.get("cargo").meters["scattered"] += 1
    propagate(world, narrate=False)
    world.say(problem.burst)
    world.say(problem.worry)


def react(world: World, a: Entity, b: Entity, mission: Mission, problem: Problem) -> None:
    cargo = world.get("cargo")
    if problem.id == "spill" and cargo.meters["scattered"] >= THRESHOLD:
        world.say(
            f'"Our {mission.cargo}!" {b.id} gasped. Bits of it were all over the floor.'
        )
    elif problem.id == "stuck":
        world.say(
            f"{a.id} grabbed the rail, and {b.id} hugged the {cargo.label}. For one beat, both children listened to the still elevator."
        )
    else:
        world.say(
            f"{b.id} blinked into the dimness, and {a.id} moved one step closer so they could stand shoulder to shoulder."
        )


def choose_plan(world: World, a: Entity, b: Entity, plan: Plan) -> None:
    team = world.get("team")
    team.meters["working_together"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {a.id} and {b.id} remembered they were a team. They {plan.action}."
    )


def solve(world: World, plan: Plan, problem: Problem, delay: int) -> None:
    elevator = world.get("elevator")
    cargo = world.get("cargo")
    if problem.id == "stuck":
        elevator.meters["trouble"] = 0
        if delay > 0:
            world.say(
                "First came a tiny wait. The children counted their breaths, listened to the fan, and stayed close together."
            )
        world.say(plan.success)
    elif problem.id == "dim":
        elevator.meters["dark"] = 0
        elevator.meters["trouble"] = 0
        world.say(plan.success)
    elif problem.id == "spill":
        cargo.meters["scattered"] = 0
        elevator.meters["trouble"] = 0
        world.say(plan.success)


def celebrate(world: World, a: Entity, b: Entity, adult: Entity, mission: Mission,
              sound: SoundGame, outcome: str) -> None:
    for kid in (a, b):
        kid.memes["pride"] += 1
        kid.memes["joy"] += 1
    world.say(
        f'{adult.label_word.capitalize()} smiled at them. "That was real teamwork," {adult.pronoun()} said.'
    )
    if outcome == "late_but_proud":
        world.say(
            "They might be a little late, but now they had a better story to tell than an ordinary elevator ride ever could."
        )
    else:
        world.say(
            "Best of all, the adventure ended before their big plan for the day had slipped away."
        )
    world.say(sound.close)
    world.say(mission.ending)


def tell(
    mission: Mission,
    problem: Problem,
    plan: Plan,
    sound: SoundGame,
    kid1_name: str,
    kid1_gender: str,
    kid2_name: str,
    kid2_gender: str,
    adult_type: str,
    trait1: str,
    trait2: str,
    delay: int,
) -> World:
    world = World()
    a = world.add(Entity(id=kid1_name, kind="character", type=kid1_gender, role="kid", traits=[trait1]))
    b = world.add(Entity(id=kid2_name, kind="character", type=kid2_gender, role="kid", traits=[trait2]))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the parent"))
    world.add(Entity(id="elevator", type="elevator", label="elevator", tags={"elevator"}))
    world.add(Entity(id="team", type="team", label="team"))
    cargo = world.add(Entity(id="cargo", type="project", label="project", phrase=mission.cargo, tags=set(mission.tags)))

    introduce(world, a, b, adult, mission)
    build_playful_mood(world, a, b, sound)

    world.para()
    trouble_strikes(world, problem)
    react(world, a, b, mission, problem)

    world.para()
    choose_plan(world, a, b, plan)
    solve(world, plan, problem, delay)

    world.para()
    outcome = "late_but_proud" if delay > 0 else "on_time"
    celebrate(world, a, b, adult, mission, sound, outcome)

    world.facts.update(
        kid1=a,
        kid2=b,
        adult=adult,
        mission=mission,
        problem=problem,
        plan=plan,
        sound=sound,
        cargo=cargo,
        delay=delay,
        outcome=outcome,
        resolved=True,
        teamwork=world.get("team").meters["working_together"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    mission: str
    problem: str
    plan: str
    sound: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    adult: str
    trait1: str
    trait2: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        mission="rocket_demo",
        problem="stuck",
        plan="alarm_button",
        sound="robot",
        kid1="Lily",
        kid1_gender="girl",
        kid2="Tom",
        kid2_gender="boy",
        adult="mother",
        trait1="careful",
        trait2="sparky",
        delay=0,
    ),
    StoryParams(
        mission="bug_show",
        problem="dim",
        plan="flashlight",
        sound="spaceship",
        kid1="Mia",
        kid1_gender="girl",
        kid2="Ben",
        kid2_gender="boy",
        adult="father",
        trait1="steady",
        trait2="curious",
        delay=0,
    ),
    StoryParams(
        mission="star_club",
        problem="spill",
        plan="checklist",
        sound="drum",
        kid1="Nora",
        kid1_gender="girl",
        kid2="Leo",
        kid2_gender="boy",
        adult="mother",
        trait1="thoughtful",
        trait2="brave",
        delay=0,
    ),
    StoryParams(
        mission="rocket_demo",
        problem="stuck",
        plan="intercom",
        sound="spaceship",
        kid1="Sam",
        kid1_gender="boy",
        kid2="Ella",
        kid2_gender="girl",
        adult="father",
        trait1="steady",
        trait2="careful",
        delay=1,
    ),
    StoryParams(
        mission="bug_show",
        problem="spill",
        plan="sort_together",
        sound="robot",
        kid1="Ava",
        kid1_gender="girl",
        kid2="Max",
        kid2_gender="boy",
        adult="mother",
        trait1="sparky",
        trait2="thoughtful",
        delay=0,
    ),
]


def explain_rejection(problem_id: str, plan_id: str) -> str:
    return (
        f"(No story: {PLANS[plan_id].label} does not solve the elevator problem "
        f"'{problem_id}'. Pick a plan that handles {problem_id}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "late_but_proud" if params.delay > 0 else "on_time"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid1, kid2 = f["kid1"], f["kid2"]
    mission, problem, plan = f["mission"], f["problem"], f["plan"]
    sound = f["sound"]
    return [
        'Write an adventure story for a 3-to-5-year-old set in an elevator that includes the words "monk-dim" and "science".',
        f"Tell a funny, child-friendly elevator adventure where {kid1.id} and {kid2.id} face a {problem.title} problem on the way to {mission.goal} and solve it with teamwork.",
        f"Write a short story with sound effects, a silly {sound.id}-style joke, and a sensible solution using {plan.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid1, kid2, adult = f["kid1"], f["kid2"], f["adult"]
    mission, problem, plan = f["mission"], f["problem"], f["plan"]
    cargo = f["cargo"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid1.id} and {kid2.id}, two children riding an elevator with their {adult.label_word}. They were carrying {mission.cargo} for a science adventure.",
        ),
        (
            "Where were they going?",
            f"They were going to {mission.goal}. That goal is why the elevator ride mattered so much to them.",
        ),
        (
            "What problem happened in the elevator?",
            f"The problem was that the elevator became {problem.title}. {problem.worry}",
        ),
        (
            "How did the children act like a team?",
            f"They stayed together and used {plan.label} instead of panicking. One child handled one part of the job while the other helped with the project, which made the problem easier to solve.",
        ),
        (
            "Why were the sound effects helpful?",
            f"The silly noises turned the scary moment into a joke they could share. Laughing together helped them feel calmer and braver inside the elevator.",
        ),
    ]
    if problem.id == "spill":
        qa.append(
            (
                f"What happened to their project?",
                f"The {cargo.label} spilled across the elevator floor. They fixed it by working carefully together so their science work was not ruined.",
            )
        )
    else:
        qa.append(
            (
                "How did they solve the elevator problem?",
                f"{plan.qa_text} Because they chose a plan that matched the problem, the ride became safe again.",
            )
        )
    if outcome == "late_but_proud":
        qa.append(
            (
                "Did they still feel good at the end?",
                "Yes. They were a little late, but they felt proud because they had solved the problem together and kept their adventure going.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily when the problem was solved and they continued toward {mission.goal}. The ending image shows them stepping out of the elevator feeling proud and ready.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"elevator", "teamwork", "science"}
    tags |= set(f["plan"].tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
solves(Plan, Problem) :- handles(Plan, Problem).

valid(Mission, Problem, Plan) :- mission(Mission), problem(Problem), plan(Plan), solves(Plan, Problem).

late :- chosen_delay(D), D > 0.
resolved :- chosen_problem(Problem), chosen_plan(Plan), solves(Plan, Problem).

outcome(on_time) :- resolved, not late.
outcome(late_but_proud) :- resolved, late.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        for handled in sorted(plan.handles):
            lines.append(asp.fact("handles", plan_id, handled))
    for sound_id in SOUNDS:
        lines.append(asp.fact("sound", sound_id))
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
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_plan", params.plan),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in ASP:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in Python:", sorted(p_valid - c_valid))

    scenarios = list(CURATED)
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        scenarios.append(params)

    mismatches = 0
    for params in scenarios:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcome model matches outcome_of() on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(scenarios)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Elevator adventure storyworld with teamwork, sound effects, and a small science mission."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = quick fix, 1 = short wait before the elevator moves again")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (mission, problem, plan) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.plan and not plan_fits(args.problem, args.plan):
        raise StoryError(explain_rejection(args.problem, args.plan))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.problem is None or combo[1] == args.problem)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, problem_id, plan_id = rng.choice(sorted(combos))
    sound_id = args.sound or rng.choice(sorted(SOUNDS))
    adult = args.adult or rng.choice(["mother", "father"])
    kid1, kid1_gender = pick_child(rng)
    kid2, kid2_gender = pick_child(rng, avoid=kid1)
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice([t for t in TRAITS if t != trait1] or TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1]) if problem_id == "stuck" else 0
    return StoryParams(
        mission=mission_id,
        problem=problem_id,
        plan=plan_id,
        sound=sound_id,
        kid1=kid1,
        kid1_gender=kid1_gender,
        kid2=kid2,
        kid2_gender=kid2_gender,
        adult=adult,
        trait1=trait1,
        trait2=trait2,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Unknown sound: {params.sound})")
    if params.adult not in {"mother", "father"}:
        raise StoryError(f"(Unknown adult type: {params.adult})")
    if not plan_fits(params.problem, params.plan):
        raise StoryError(explain_rejection(params.problem, params.plan))

    world = tell(
        mission=MISSIONS[params.mission],
        problem=PROBLEMS[params.problem],
        plan=PLANS[params.plan],
        sound=SOUNDS[params.sound],
        kid1_name=params.kid1,
        kid1_gender=params.kid1_gender,
        kid2_name=params.kid2,
        kid2_gender=params.kid2_gender,
        adult_type=params.adult,
        trait1=params.trait1,
        trait2=params.trait2,
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
        print(f"{len(combos)} compatible (mission, problem, plan) combos:\n")
        for mission_id, problem_id, plan_id in combos:
            print(f"  {mission_id:12} {problem_id:8} {plan_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.kid1} & {p.kid2}: {p.problem} -> {p.plan} ({p.mission})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
