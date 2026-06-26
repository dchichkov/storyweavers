#!/usr/bin/env python3
"""
storyworlds/worlds/scrape_clack_teamwork_suspense_twist_animal_story.py
=======================================================================

A small animal-story world about teamwork, suspense, and a twist.

Premise:
- A little animal wants to get something important across a tricky place.
- The path makes scrape and clack sounds.
- The first plan seems risky.
- Friends work together, and the twist reveals the noisy thing was useful, not harmful.

The prose engine simulates a tiny causal world:
- physical meters: load, friction, progress, stuckness, scrape, clack
- emotional memes: worry, hope, trust, pride, relief, surprise

The story stays grounded in what the animals actually do, what they carry,
and how the helpers change the outcome.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"otter", "fox", "rabbit", "mole", "mouse", "badger"}
        male = {"bear", "hedgehog", "squirrel", "raccoon", "frog", "crow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    surface: str
    obstacle: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    label: str
    phrase: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"any"})


@dataclass
class HelperGear:
    id: str
    label: str
    prep: str
    reveal: str
    helps: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bridge": Setting(
        place="the old bridge",
        surface="wooden planks",
        obstacle="a small gap",
        affords={"crossing"},
    ),
    "dock": Setting(
        place="the windy dock",
        surface="wet boards",
        obstacle="a wobbling crate stack",
        affords={"crossing"},
    ),
    "hill": Setting(
        place="the grassy hill",
        surface="rough path",
        obstacle="a muddy dip",
        affords={"crossing"},
    ),
}

TASKS = {
    "crossing": Task(
        id="crossing",
        verb="cross the way",
        gerund="crossing the way",
        risk="could slip and stall",
        zone={"paws", "feet"},
        keyword="clack",
        tags={"scrape", "clack", "teamwork", "suspense", "twist"},
    ),
}

GOALS = {
    "parcel": Goal(
        label="parcel",
        phrase="a small wrapped parcel",
        type="parcel",
        plural=False,
        genders={"any"},
    ),
    "bucket": Goal(
        label="bucket",
        phrase="a shiny pail",
        type="bucket",
        plural=False,
        genders={"any"},
    ),
    "basket": Goal(
        label="basket",
        phrase="a light berry basket",
        type="basket",
        plural=False,
        genders={"any"},
    ),
}

GEAR = {
    "log": HelperGear(
        id="log",
        label="a long log",
        prep="roll a long log into place",
        reveal="the log was a bridge for the missing gap",
        helps={"crossing"},
        plural=False,
    ),
    "rope": HelperGear(
        id="rope",
        label="a rope line",
        prep="tie a rope line to the posts",
        reveal="the rope kept the wobbling load steady",
        helps={"crossing"},
        plural=False,
    ),
    "plank": HelperGear(
        id="plank",
        label="extra planks",
        prep="slide extra planks across the slick spot",
        reveal="the planks covered the muddy dip",
        helps={"crossing"},
        plural=True,
    ),
}

CHARACTER_TYPES = ["otter", "bear", "fox", "rabbit", "mole", "hedgehog", "squirrel", "raccoon"]
NAMES = {
    "otter": ["Pip", "Tilly", "Ollie", "Mara"],
    "bear": ["Bruno", "Moss", "Tobin", "June"],
    "fox": ["Fenn", "Ruby", "Sage", "Lark"],
    "rabbit": ["Nim", "Poppy", "Bram", "Dori"],
    "mole": ["Mina", "Tuck", "Wren", "Dot"],
    "hedgehog": ["Hugo", "Ivy", "Pace", "Nell"],
    "squirrel": ["Skip", "Acorn", "Pip", "Tessa"],
    "raccoon": ["Nori", "Milo", "Bean", "Clover"],
}
TRAITS = ["small", "brave", "curious", "gentle", "busy", "quick"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    goal: str
    hero_type: str
    hero_name: str
    helper_type: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def task_at_risk(task: Task, goal: Goal) -> bool:
    return True


def choose_gear(task: Task, goal: Goal) -> Optional[HelperGear]:
    # In this small world, all gear is about the crossing task.
    return next(iter(GEAR.values()))


def predict_stuck(world: World, hero: Entity, task: Task) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["load"] += 1
    sim.get(hero.id).meters["friction"] += 1
    return sim.get(hero.id).meters["friction"] >= THRESHOLD


def do_action(world: World, hero: Entity, task: Task, goal: Entity, narrate: bool = True) -> None:
    hero.meters["load"] += 1
    hero.meters["friction"] += 1
    hero.memes["worry"] += 1
    if narrate:
        world.say(f"{hero.id} tried to {task.verb}, but the path made a scrape and clack under {hero.pronoun('possessive')} paws.")
    if hero.meters["friction"] >= THRESHOLD:
        hero.meters["stuck"] += 1
        hero.memes["hope"] += 1


def teamwork_step(world: World, hero: Entity, helper: Entity, gear: HelperGear) -> None:
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    world.say(
        f"{helper.id} hurried over, and together they decided to {gear.prep}."
    )


def resolution(world: World, hero: Entity, helper: Entity, goal: Entity, gear: HelperGear, task: Task) -> None:
    hero.meters["progress"] += 1
    hero.meters["stuck"] = 0
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Then came the twist: {gear.reveal}. Once it was in place, {hero.id} could {task.verb} without slipping."
    )
    world.say(
        f"{hero.id} and {helper.id} carried {goal.pronoun('object')} across together, and the scrape and clack turned into a happy rhythm."
    )
    world.say(
        f"At the end, {goal.id} stayed safe, and {hero.id} looked back with bright eyes at the path they had crossed."
    )


def tell(setting: Setting, task: Task, goal_cfg: Goal, hero_type: str, hero_name: str, helper_type: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"load": 0.0, "friction": 0.0, "progress": 0.0, "stuck": 0.0},
        memes={"worry": 0.0, "hope": 0.0, "trust": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        meters={"load": 0.0, "friction": 0.0, "progress": 0.0, "stuck": 0.0},
        memes={"worry": 0.0, "hope": 0.0, "trust": 0.0, "pride": 0.0},
    ))
    goal = world.add(Entity(
        id=goal_cfg.label,
        kind="thing",
        type=goal_cfg.type,
        label=goal_cfg.label,
        phrase=goal_cfg.phrase,
        plural=goal_cfg.plural,
        owner=hero.id,
        meters={"safe": 0.0},
    ))

    world.say(f"{hero.id} was a {trait} {hero.type} who wanted to help carry {goal.phrase} across {setting.place}.")
    world.say(f"{helper.id} was nearby, and both of them listened to the little scrape and clack of the boards.")
    world.para()
    world.say(f"The trouble was {setting.obstacle}, and the load made {hero.id} slow down.")
    do_action(world, hero, task, goal, narrate=True)
    world.para()
    world.say(f"{hero.id} worried that {task.risk}.")
    teamwork_step(world, hero, helper, choose_gear(task, goal))
    world.say(f"They checked the path and found a careful way forward.")
    world.para()
    resolution(world, hero, helper, goal, choose_gear(task, goal), task)

    world.facts.update(
        hero=hero,
        helper=helper,
        goal=goal,
        task=task,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    goal = f["goal"]
    setting = f["setting"]
    return [
        f"Write a short animal story about {hero.id} and {helper.id} working together at {setting.place}.",
        f"Tell a suspenseful children's story that includes scrape and clack and ends with a twist.",
        f"Write a gentle teamwork story where {hero.id} helps carry {goal.phrase} across {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    goal = f["goal"]
    setting = f["setting"]
    task = f["task"]
    return [
        QAItem(
            question=f"Who were the two animals working together in the story?",
            answer=f"The story was about {hero.id} and {helper.id}, who worked together to carry {goal.phrase} across {setting.place}.",
        ),
        QAItem(
            question=f"What sounds did the path make while they tried to cross?",
            answer=f"The path made a scrape and clack sound as they moved along the boards.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the noisy gear was actually the helpful fix, so the tricky path became safe to cross.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried at first?",
            answer=f"{hero.id} felt worried because the path was tricky and the load could slip, so {task.risk}.",
        ),
        QAItem(
            question=f"How did teamwork help in the end?",
            answer=f"Teamwork helped because {hero.id} and {helper.id} used a careful plan together, and that let them carry {goal.label} across safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people or animals help each other and share the job so the whole task becomes easier.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of wondering what will happen next when something is uncertain or risky.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the listener expected.",
        ),
        QAItem(
            question="What do scrape and clack sound like?",
            answer="Scrape sounds rough and dragging, and clack sounds hard and quick, like pieces tapping together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when a task creates tension, teamwork helps, and a twist resolves it.
valid_story(P, T, G) :- place(P), task(T), goal(G), at_risk(T, G), has_teamwork(T), has_twist(T).

at_risk(T, G) :- task(T), goal(G).
has_teamwork(T) :- teamwork(T).
has_twist(T) :- twist(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("teamwork", tid))
        lines.append(asp.fact("suspense", tid))
        lines.append(asp.fact("twist", tid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, t, g) for p in SETTINGS for t in TASKS for g in GOALS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, g) for p in SETTINGS for t in TASKS for g in GOALS]


CURATED = [
    StoryParams("bridge", "crossing", "parcel", "otter", "Pip", "bear", "Bruno", "curious"),
    StoryParams("dock", "crossing", "bucket", "fox", "Ruby", "raccoon", "Nori", "brave"),
    StoryParams("hill", "crossing", "basket", "rabbit", "Poppy", "hedgehog", "Ivy", "gentle"),
]


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.task and args.task not in TASKS:
        raise StoryError("Unknown task.")
    if args.goal and args.goal not in GOALS:
        raise StoryError("Unknown goal.")

    places = [args.place] if args.place else list(SETTINGS)
    tasks = [args.task] if args.task else list(TASKS)
    goals = [args.goal] if args.goal else list(GOALS)
    combos = [(p, t, g) for p in places for t in tasks for g in goals]
    if not combos:
        raise StoryError("No valid combination matches the options.")

    place, task, goal = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(CHARACTER_TYPES)
    helper_type = args.helper_type or rng.choice([t for t in CHARACTER_TYPES if t != hero_type])
    hero_name = args.hero_name or rng.choice(NAMES[hero_type])
    helper_name = args.helper_name or rng.choice(NAMES[helper_type])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, task, goal, hero_type, hero_name, helper_type, helper_name, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TASKS[params.task],
        GOALS[params.goal],
        params.hero_type,
        params.hero_name,
        params.helper_type,
        params.helper_name,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal teamwork storyworld with scrape, clack, suspense, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--hero-type", choices=CHARACTER_TYPES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-type", choices=CHARACTER_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:\n")
        for p, t, g in triples:
            print(f"  {p:8} {t:10} {g}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.place} / {p.goal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
