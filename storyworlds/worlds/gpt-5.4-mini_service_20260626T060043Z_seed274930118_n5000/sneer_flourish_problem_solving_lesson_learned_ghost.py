#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sneer_flourish_problem_solving_lesson_learned_ghost.py
=============================================================================================

A compact ghost-story world about a spooky misunderstanding, problem solving,
and a lesson learned.

Seed tale:
---
A child hears a ghost sneer in the old house. The child feels scared at first,
but then notices the ghost is stuck because its ribbon is tangled in a window
latch and its lantern has gone dim. The child thinks carefully, finds a simple
fix, and helps the ghost flourish into a bright, friendly helper. In the end,
the child learns that scary faces can hide a problem that needs kindness.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    state: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    atmosphere: str
    haunts: str


@dataclass
class Problem:
    id: str
    trouble: str
    clue: str
    fix: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    problem: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly ghost story world with a spooky problem to solve.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_pairs() -> list[tuple[str, str]]:
    return [(s, p) for s in SETTINGS for p in PROBLEMS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pairs = valid_pairs()
    if args.setting and args.problem:
        if (args.setting, args.problem) not in pairs:
            raise StoryError("That setting and problem do not make a sensible ghost story.")
    if not pairs:
        raise StoryError("No valid story combinations available.")
    filtered = [
        (s, p) for (s, p) in pairs
        if (args.setting is None or s == args.setting)
        and (args.problem is None or p == args.problem)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem = rng.choice(sorted(filtered))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, problem=problem, child_name=child_name, child_gender=child_gender, parent_type=parent_type)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P) :- setting(S), problem(P).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_pairs():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.state:
            bits.append(f"state={e.state}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


def hero_name(gender: str) -> str:
    return "Mia" if gender == "girl" else "Noah"


SETTINGS = {
    "attic": Setting(place="the old attic", atmosphere="dusty beams and moonlight", haunts="a chilly draft"),
    "hall": Setting(place="the long hallway", atmosphere="echoes and creaky floorboards", haunts="a flickering lamp"),
    "garden_shed": Setting(place="the garden shed", atmosphere="rain on the roof", haunts="a rattling latch"),
}

PROBLEMS = {
    "tangled_ribbon": Problem(
        id="tangled_ribbon",
        trouble="its ribbon was tangled in the window latch",
        clue="the ribbon kept tugging the ghost back and making it snap its fingers",
        fix="the child opened the window, loosened the ribbon, and tied it neatly",
        lesson="a scary sneer can hide a simple problem",
    ),
    "dim_lantern": Problem(
        id="dim_lantern",
        trouble="its lantern had gone dim",
        clue="the ghost was bumping into chairs because it could not see well",
        fix="the child found a fresh candle and lit the lantern again",
        lesson="looking closely can turn fright into a fix",
    ),
    "stuck_latch": Problem(
        id="stuck_latch",
        trouble="its bony hand was stuck on a rusty latch",
        clue="every time the ghost tried to float away, the latch clicked and held it back",
        fix="the child put a little oil on the latch and wiggled it free",
        lesson="kind helpers can solve problems better than fear",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella"]
BOY_NAMES = ["Noah", "Leo", "Finn", "Theo", "Eli", "Max"]

CURATED = [
    StoryParams(setting="attic", problem="tangled_ribbon", child_name="Mia", child_gender="girl", parent_type="mother"),
    StoryParams(setting="hall", problem="dim_lantern", child_name="Noah", child_gender="boy", parent_type="father"),
    StoryParams(setting="garden_shed", problem="stuck_latch", child_name="Lily", child_gender="girl", parent_type="mother"),
]


def tell(setting: Setting, problem: Problem, child_name: str, child_gender: str, parent_type: str) -> World:
    w = World(setting)
    child = w.add(Entity(id=child_name, kind="character", type=child_gender, state="careful"))
    parent = w.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    ghost = w.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost", state="spooky"))
    tool = w.add(Entity(id="Tool", kind="thing", type="tool", label="a small lantern", phrase="a small lantern", owner=child.id))

    child.memes["fear"] = 1
    ghost.memes["grump"] = 1

    w.say(f"{child_name} was in {setting.place}, where {setting.atmosphere} made the house feel extra spooky.")
    w.say(f"Then {ghost.label} gave a sharp sneer from the dark, and {child_name} froze for a moment.")

    w.say(f"But {child_name} looked again and noticed {problem.clue}.")
    w.say(f"That meant the ghost was not mean at all; it had a real problem: {problem.trouble}.")

    child.memes["curiosity"] = 1
    child.memes["bravery"] = 1
    ghost.memes["hope"] = 1

    if problem.id == "tangled_ribbon":
        w.say(f"{child_name} took a breath, opened the window, and gently untangled the ribbon.")
        ghost.meters["freedom"] = 1
    elif problem.id == "dim_lantern":
        w.say(f"{child_name} found a fresh candle, and the lantern flourished into a warm little glow.")
        tool.state = "lit"
        ghost.meters["light"] = 1
    else:
        w.say(f"{child_name} found a little oil, eased the latch, and the ghost drifted free at once.")
        ghost.meters["freedom"] = 1

    ghost.state = "friendly"
    ghost.memes["joy"] = 1
    child.memes["fear"] = 0
    child.memes["pride"] = 1
    child.memes["lesson"] = 1

    w.say(f"The ghost's face changed from a sneer to a bright flourish, like a curtain opening to a happy surprise.")
    w.say(f"After that, {ghost.label} floated beside {child_name} instead of looming over {child_name}.")
    w.say(f"{child_name} learned {problem.lesson}, and the old house felt gentle by the end of the night.")

    w.facts.update(child=child, parent=parent, ghost=ghost, tool=tool, problem=problem, setting=setting)
    return w


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a small child in {f["setting"].place} that includes the words "sneer" and "flourish".',
        f"Tell a gentle spooky story where {f['child'].id} notices a ghost problem, thinks carefully, and helps instead of running away.",
        f"Write a child-friendly ghost story with a problem, a solution, and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    problem = f["problem"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Why did {child.id} stop feeling scared in {place}?",
            answer=f"{child.id} stopped feeling scared because {child.id} noticed that the ghost's sneer came from a problem, not from being mean.",
        ),
        QAItem(
            question=f"What was wrong with {ghost.label}?",
            answer=f"{ghost.label} had a problem: {problem.trouble}.",
        ),
        QAItem(
            question=f"What did {child.id} do to help?",
            answer=f"{child.id} solved the problem by {problem.fix.lower()}.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that {problem.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a sneer?", answer="A sneer is a mean-looking facial expression, often with a curled mouth or a scornful look."),
        QAItem(question="What does flourish mean?", answer="To flourish means to grow, shine, or do something in a lively, fancy, or successful way."),
        QAItem(question="Why do people check for the cause of a problem?", answer="People check for the cause so they can solve the real problem instead of guessing."),
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], params.child_name, params.child_gender, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        pairs = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(pairs)} compatible story combinations:\n")
        for s, p in pairs:
            print(f"  {s:12} {p}")
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
            header = f"### {p.child_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
