#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/rewrite_teamwork_sound_effects_bad_ending_rhyming.py
==============================================================================================================

A compact story world for a rhyming teamwork tale with sound effects and a bad ending.

Seed tale idea:
- Two small friends want to build something together.
- They use teamwork and hear lots of sound effects.
- Their plan goes wrong at the end, leaving a disappointing result.

The simulation keeps explicit meters for physical state and memes for emotional state.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the yard"
    affords: set[str] = field(default_factory=set)


@dataclass
class BuildPlan:
    id: str
    thing: str
    verb: str
    sound_steps: list[str]
    final_sound: str
    fragility: str
    mess: str


@dataclass
class StoryParams:
    setting: str
    plan: str
    hero1: str
    hero2: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "yard": Setting(place="the yard", affords={"build"}),
    "porch": Setting(place="the porch", affords={"build"}),
    "playroom": Setting(place="the playroom", affords={"build"}),
}

PLANS = {
    "tower": BuildPlan(
        id="tower",
        thing="tower",
        verb="build a tall tower",
        sound_steps=["tap", "tap-tap", "stack", "stack"],
        final_sound="CRASH",
        fragility="wobbly",
        mess="blocks",
    ),
    "robot": BuildPlan(
        id="robot",
        thing="robot",
        verb="make a boxy robot",
        sound_steps=["click", "clack", "spin", "zip"],
        final_sound="CLANG",
        fragility="crooked",
        mess="tape",
    ),
    "rocket": BuildPlan(
        id="rocket",
        thing="rocket",
        verb="build a paper rocket",
        sound_steps=["fold", "fold", "whoosh", "peel"],
        final_sound="FLUMP",
        fragility="flimsy",
        mess="paper",
    ),
}

NAMES = ["Mia", "Noah", "Luna", "Theo", "Ava", "Finn", "Zoe", "Max"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def rhymed_lines(name1: str, name2: str, plan: BuildPlan, place: str) -> list[str]:
    return [
        f"{name1} and {name2} went out to play, with bright little grins at the start of the day.",
        f"They wanted to {plan.verb} right there in {place}, and both of them smiled with a sparkly face.",
    ]


def setup(world: World, a: Entity, b: Entity, plan: BuildPlan) -> None:
    a.memes["joy"] = 1
    b.memes["joy"] = 1
    world.say(
        f"{a.id} and {b.id} were friends who liked to try a new thing side by side."
    )
    world.say(
        f"They wanted to {plan.verb}, and they said they would share the work with pride."
    )


def teamwork(world: World, a: Entity, b: Entity, plan: BuildPlan) -> None:
    a.memes["teamwork"] = 1
    b.memes["teamwork"] = 1
    world.facts["sound_steps"] = list(plan.sound_steps)
    world.say(
        f"{a.id} held the pieces. {b.id} found the glue. Together they worked as a happy two."
    )
    world.say(
        f"\"{plan.sound_steps[0].upper()}!\" went the first small part, then \"{plan.sound_steps[1].upper()}!\" from the other cart."
    )
    world.say(
        f"They went \"{plan.sound_steps[2]}\" and \"{plan.sound_steps[3]}\" while the little thing grew."
    )


def trouble(world: World, a: Entity, b: Entity, plan: BuildPlan) -> None:
    world.facts["trouble"] = True
    a.memes["worry"] = 1
    b.memes["worry"] = 1
    world.say(
        f"But their {plan.fragility} project leaned to one side, and the room grew still."
    )
    world.say(
        f"Then came a loud \"{plan.final_sound}!\" and the whole thing went spill."
    )


def bad_ending(world: World, a: Entity, b: Entity, plan: BuildPlan) -> None:
    world.facts["bad_ending"] = True
    world.facts["ruined"] = plan.id
    a.meters["broken"] = 1
    b.meters["broken"] = 1
    a.memes["sad"] = 1
    b.memes["sad"] = 1
    world.say(
        f"Their {plan.thing} ended in pieces, all tangled and bent."
    )
    world.say(
        f"{a.id} and {b.id} sat very quiet, and their big good plan was spent."
    )
    world.say(
        f"They tried to rewrite it, but the paper was torn, and the last little hope looked worn."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A plan is a teamwork story when two heroes work together on a build.
teamwork_story(P) :- plan(P), needs_two(P).

% Sound effects appear when a plan has multiple sound steps.
sound_effects_story(P) :- plan(P), many_sounds(P).

% A bad ending happens when the plan is ruined.
bad_ending_story(P) :- plan(P), ruined(P).

valid_story(P) :- teamwork_story(P), sound_effects_story(P), bad_ending_story(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("needs_two", pid))
        lines.append(asp.fact("many_sounds", pid))
        lines.append(asp.fact("ruined", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((pid,) for pid in PLANS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches registry ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python registry.")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_story(setting_id: str, plan_id: str, hero1: str, hero2: str) -> World:
    setting = SETTINGS[setting_id]
    plan = PLANS[plan_id]
    world = World(setting)

    a = world.add(Entity(id=hero1, kind="character", type="girl" if hero1 in {"Mia", "Luna", "Ava", "Zoe"} else "boy"))
    b = world.add(Entity(id=hero2, kind="character", type="girl" if hero2 in {"Mia", "Luna", "Ava", "Zoe"} else "boy"))

    world.say(rhymed_lines(hero1, hero2, plan, setting.place)[0])
    world.say(rhymed_lines(hero1, hero2, plan, setting.place)[1])

    world.para()
    setup(world, a, b, plan)

    world.para()
    teamwork(world, a, b, plan)

    world.para()
    trouble(world, a, b, plan)

    world.para()
    bad_ending(world, a, b, plan)

    world.facts.update(
        setting=setting,
        plan=plan,
        hero1=a,
        hero2=b,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    plan: BuildPlan = f["plan"]
    return [
        f'Write a short rhyming story about teamwork and a loud "{plan.final_sound}" sound.',
        f"Tell a child-friendly story where two friends work together to {plan.verb} and it ends badly.",
        f'Write a simple rhyming tale that includes the sound effects {", ".join(plan.sound_steps)} and ends with a sad mistake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = f["hero1"]
    b: Entity = f["hero2"]
    plan: BuildPlan = f["plan"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who worked together in {setting.place}?",
            answer=f"{a.id} and {b.id} worked together in {setting.place}. They shared the job and tried to make the plan work.",
        ),
        QAItem(
            question=f"What did they try to make?",
            answer=f"They tried to {plan.verb}. The project was small, but it needed both of them.",
        ),
        QAItem(
            question=f"What sound did the story end with?",
            answer=f"It ended with a loud {plan.final_sound}. That sound came right before the project fell apart.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended badly. The thing they built broke, and the two friends sat sadly beside the pieces.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other finish one job.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that copy noises, like bang, pop, tap, or crash.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when the problem is not fixed and the story finishes in a sad or disappointing way.",
        ),
    ]


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
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming teamwork story world with sound effects and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero1", choices=NAMES)
    ap.add_argument("--hero2", choices=NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    plan = args.plan or rng.choice(list(PLANS))
    hero1 = args.hero1 or rng.choice(NAMES)
    hero2 = args.hero2 or rng.choice([n for n in NAMES if n != hero1])
    if hero1 == hero2:
        raise StoryError("The two heroes must be different.")
    return StoryParams(setting=setting, plan=plan, hero1=hero1, hero2=hero2)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params.setting, params.plan, params.hero1, params.hero2)
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


CURATED = [
    StoryParams(setting="yard", plan="tower", hero1="Mia", hero2="Noah"),
    StoryParams(setting="porch", plan="robot", hero1="Luna", hero2="Theo"),
    StoryParams(setting="playroom", plan="rocket", hero1="Ava", hero2="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid story plans:")
        for (pid,) in vals:
            print(f"  {pid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero1} and {p.hero2}: {p.plan} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
