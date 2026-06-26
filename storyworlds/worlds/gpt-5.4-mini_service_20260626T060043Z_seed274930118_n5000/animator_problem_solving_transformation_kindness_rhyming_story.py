#!/usr/bin/env python3
"""
storyworlds/worlds/animator_problem_solving_transformation_kindness_rhyming_story.py
====================================================================================

A tiny story world about an animator, a sticky problem, a kind helper, and a
bright transformation told in a simple rhyming-story style.

The world is grounded in a small simulation:
- an animator is making a short show
- a problem blocks the work
- kindness helps solve it
- the result transforms from plain and stuck to lively and bright

The story stays child-facing, concrete, and state-driven rather than frozen prose.
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

# Physical/emotional thresholds for narrating changes.
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the studio"
    light: str = "bright"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    problem: str
    transform: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)


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
    "studio": Setting(place="the studio", light="bright", affords={"sketch", "paint", "cut"}),
    "classroom": Setting(place="the classroom", light="soft", affords={"sketch", "paint"}),
    "attic": Setting(place="the attic", light="golden", affords={"sketch", "cut"}),
}

TASKS = {
    "sketch": Task(
        id="sketch",
        verb="draw a new scene",
        gerund="drawing new scenes",
        problem="the page was blank and lonely",
        transform="the blank page turned into a happy picture",
        zone={"hands"},
        tags={"draw", "blank", "picture"},
    ),
    "paint": Task(
        id="paint",
        verb="paint a bright frame",
        gerund="painting bright frames",
        problem="the colors were dull and dry",
        transform="the dull colors turned shiny and new",
        zone={"hands", "shirt"},
        tags={"paint", "color", "bright"},
    ),
    "cut": Task(
        id="cut",
        verb="cut a little paper star",
        gerund="cutting little paper stars",
        problem="the paper kept curling away",
        transform="the curled paper became a neat star",
        zone={"hands"},
        tags={"paper", "star", "shape"},
    ),
}

TOOLS = {
    "pencil": Tool(
        id="pencil",
        label="a pencil",
        phrase="a soft pencil",
        helps={"sketch"},
        covers={"hands"},
    ),
    "brush": Tool(
        id="brush",
        label="a brush",
        phrase="a little brush",
        helps={"paint"},
        covers={"hands"},
    ),
    "scissors": Tool(
        id="scissors",
        label="scissors",
        phrase="small scissors",
        helps={"cut"},
        covers={"hands"},
    ),
    "cloth": Tool(
        id="cloth",
        label="a damp cloth",
        phrase="a damp cloth",
        helps={"paint"},
        covers={"shirt", "hands"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ava", "Finn", "Zoe", "Ben", "Lily"]
GENDERS = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["kind", "gentle", "cheerful", "patient", "brave"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def task_needs_tool(task: Task, tool: Tool) -> bool:
    return task.id in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for tool_id, tool in TOOLS.items():
                if task_needs_tool(task, tool):
                    combos.append((place, task_id, tool_id))
    return combos


def explain_rejection(task: Task, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} doesn't really help with {task.gerund}. "
        f"Try a tool that fits the task better.)"
    )


# ---------------------------------------------------------------------------
# Rhyming story engine
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was an animator in the studio glow, "
        f"with ideas that danced and a smile that would grow."
    )


def loves_task(world: World, hero: Entity, task: Task) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} loved {task.gerund} in a tidy little row, "
        f"for stories could sparkle wherever colors would flow."
    )


def start_problem(world: World, hero: Entity, task: Task, tool: Tool) -> None:
    world.say(
        f"But {task.problem}, and the work slowed down so slow."
    )
    world.say(
        f"{hero.id} wanted to {task.verb}, yet {tool.label} seemed to go."
    )


def kind_help(world: World, hero: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0.0) + 1
    world.say(
        f"Then {helper.id} came kindly, with a grin soft and low, "
        f'and said, "Let us help you; together we\'ll show."'
    )
    world.say(
        f"{helper.id} brought {tool.phrase}, and the trouble let go."
    )


def solve_and_transform(world: World, hero: Entity, task: Task, tool: Tool) -> None:
    hero.meters[task.id] = hero.meters.get(task.id, 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"With patience and kindness, the plan found its glow:"
    )
    world.say(
        f"{task.transform}, and the room seemed to show "
        f"a new little magic where plain things used to be low."
    )
    world.say(
        f"{hero.id} kept working, and the picture would flow, "
        f"from stuck to bright-blooming, from weary to wow."
    )


def finish(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"At the end of the day, they both gave a bow."
    )
    world.say(
        f"{hero.id}'s small film was ready, and everyone said, \"How now!\""
    )


def tell(setting: Setting, task: Task, tool: Tool, hero_name: str, hero_type: str,
         helper_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="helper"))

    introduce(world, hero)
    loves_task(world, hero, task)
    world.para()
    start_problem(world, hero, task, tool)
    kind_help(world, hero, helper, task, tool)
    world.para()
    solve_and_transform(world, hero, task, tool)
    finish(world, hero, helper, task)

    world.facts.update(hero=hero, helper=helper, task=task, tool=tool, setting=setting)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
task_needs_tool(T, U) :- task(T), tool(U), helps(U, T).
valid_story(P, T, U) :- affords(P, T), task_needs_tool(T, U).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for t in sorted(u.helps):
            lines.append(asp.fact("helps", uid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python combos:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story about an animator named {f["hero"].id} who faces a problem and learns kindness.',
        f"Tell a child-friendly story where {f['hero'].id} wants to {f['task'].verb} but needs help from {f['helper'].id}.",
        f'Create a simple rhyme with the word "animator" that ends in a bright transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task, tool = f["hero"], f["helper"], f["task"], f["tool"]
    return [
        QAItem(
            question=f"What kind of work did {hero.id} do in the story?",
            answer=f"{hero.id} was an animator, and {hero.pronoun('subject')} made little pictures and scenes in the studio.",
        ),
        QAItem(
            question=f"What problem made it hard for {hero.id} to {task.verb}?",
            answer=f"The problem was that {task.problem}, so the work could not move forward at first.",
        ),
        QAItem(
            question=f"Who helped {hero.id}, and how did they help?",
            answer=f"{helper.id} helped kindly by bringing {tool.phrase}, which made the task easier and the problem smaller.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{task.transform}, so the plain work turned bright and new.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an animator do?",
            answer="An animator makes pictures or drawings that change a little at a time to tell a story or show movement.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring so someone else feels supported.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a good way to fix what is stopping the work from going well.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one thing into another, like plain turning bright or stuck turning smooth.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.tool:
        task, tool = TASKS[args.task], TOOLS[args.tool]
        if not task_needs_tool(task, tool):
            raise StoryError(explain_rejection(task, tool))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, task_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        task=task_id,
        tool=tool_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TASKS[params.task],
        TOOLS[params.tool],
        params.name,
        params.gender,
        params.helper,
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
CURATED = [
    StoryParams(place="studio", task="paint", tool="brush", name="Mia", gender="girl", helper="mother", trait="kind"),
    StoryParams(place="classroom", task="sketch", tool="pencil", name="Leo", gender="boy", helper="father", trait="gentle"),
    StoryParams(place="attic", task="cut", tool="scissors", name="Nora", gender="girl", helper="mother", trait="cheerful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: an animator, a problem, a kind helper, and a transformation in rhyme."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=PARENT_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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


def asp_program_text() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, tool) combos:\n")
        for place, task, tool in combos:
            print(f"  {place:10} {task:8} {tool}")
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
                params = valid_story_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.task} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
