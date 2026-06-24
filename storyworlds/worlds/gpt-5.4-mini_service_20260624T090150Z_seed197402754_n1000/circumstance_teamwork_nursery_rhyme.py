#!/usr/bin/env python3
"""
storyworlds/worlds/circumstance_teamwork_nursery_rhyme.py
=========================================================

A small nursery-rhyme story world about a circumstance that calls for teamwork.

Premise:
- A little child in a nursery setting faces a small problem.
- The problem is physical and concrete: something is too big, too high, too heavy,
  or too stuck for one helper alone.
- The child and friends solve it by working together.

Story shape:
- Gentle setup in a nursery-rhyme cadence.
- A clear circumstance that creates a need.
- A teamwork turn where helpers coordinate.
- A cheerful ending image proving the change.

The word "circumstance" is intentionally part of the world vocabulary and may
appear in prompts and stories.
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
    owner: Optional[str] = None
    keeper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("weight", "height", "reach", "order", "wobble", "tidy"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "cheer", "teamwork", "pride", "patience"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    circumstance: str
    problem: str
    teamwork_line: str
    ending_line: str
    needs: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(place="the nursery", affords={"blocks", "banner", "books", "bells"}),
}

TASKS = {
    "blocks": Task(
        id="blocks",
        verb="build the block tower",
        gerund="building a block tower",
        circumstance="the blocks were piled too high for one little pair of hands",
        problem="the tower was hard to lift and hard to stack",
        teamwork_line="one child held the base, one child passed the blocks, and one child counted softly",
        ending_line="the tower stood tall and steady at last",
        needs={"height", "order"},
        tags={"blocks", "tower", "high"},
    ),
    "banner": Task(
        id="banner",
        verb="hang the bright banner",
        gerund="hanging a bright banner",
        circumstance="the ribbon was tied up high and kept flopping in the breeze",
        problem="the banner would not stay straight by itself",
        teamwork_line="two friends held the corners while another tied the knot",
        ending_line="the banner fluttered like a little rainbow",
        needs={"height", "worry"},
        tags={"banner", "ribbon", "high"},
    ),
    "books": Task(
        id="books",
        verb="put the story books on the shelf",
        gerund="putting the story books away",
        circumstance="the shelf was just a bit too tall for one small helper",
        problem="the books could not reach the shelf by themselves",
        teamwork_line="one child lifted, one child steadied, and the teacher guided the way",
        ending_line="every book found its cozy place",
        needs={"height", "reach"},
        tags={"books", "shelf", "tall"},
    ),
    "bells": Task(
        id="bells",
        verb="bring the jingle bells inside",
        gerund="bringing the jingle bells in",
        circumstance="the bell basket was stuck behind a chair",
        problem="the basket would not budge on its own",
        teamwork_line="one child pulled the basket, one child slid the chair, and one child made room",
        ending_line="the bells sang a tiny ding-dong tune",
        needs={"weight", "order"},
        tags={"bells", "basket", "stuck"},
    ),
}

TOOLS = {
    "stool": Tool(
        id="stool",
        label="a little step stool",
        helps={"height", "reach"},
        covers={"height"},
        prep="bring over a little step stool",
        tail="set the stool back by the wall",
    ),
    "rope": Tool(
        id="rope",
        label="a short ribbon rope",
        helps={"order", "weight"},
        covers={"order"},
        prep="use a short ribbon rope to help together",
        tail="coil the ribbon rope into a neat loop",
    ),
    "basket": Tool(
        id="basket",
        label="a sturdy basket",
        helps={"weight"},
        covers={"weight"},
        prep="carry it in a sturdy basket",
        tail="put the sturdy basket back on the hook",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ivy", "Ava"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Theo", "Sam"]
TRAITS = ["bright", "gentle", "cheery", "curious", "spry"]


@dataclass
class StoryParams:
    task: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_needs(T, N) :- task(T), needs(T, N).
tool_fixes(Tool, Need) :- tool(Tool), helps(Tool, Need).
valid_combo(Task, Tool) :- task_needs(Task, Need), tool_fixes(Tool, Need).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for n in sorted(t.needs):
            lines.append(asp.fact("needs", tid, n))
    for tool in TOOLS.values():
        lines.append(asp.fact("tool", tool.id))
        for n in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasoning and narration
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for task_id, task in TASKS.items():
        for tool_id, tool in TOOLS.items():
            if task.needs & tool.helps:
                combos.append((task_id, tool_id))
    return combos


def select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS.values():
        if task.needs & tool.helps:
            return tool
    return None


def introduce(world: World, child: Entity, parent: Entity, task: Task) -> None:
    world.say(
        f"Little {child.id} in the nursery was a {child.type} so bright, "
        f"and {parent.pronoun('possessive')} {parent.type} smiled with delight."
    )
    world.say(
        f"They loved to {task.verb}, by the soft toy light, "
        f"though {task.circumstance} on that very night."
    )


def setup(world: World, child: Entity, parent: Entity, task: Task) -> None:
    child.memes["cheer"] += 1
    world.say(
        f"But the {task.id} day brought a circumstance: {task.circumstance}."
    )
    world.say(
        f"{task.problem.capitalize()}, and the child felt a little huff of worry."
    )
    parent.memes["patience"] += 1


def teamwork_turn(world: World, child: Entity, parent: Entity, task: Task, tool: Tool) -> None:
    child.memes["worry"] += 1
    child.memes["teamwork"] += 1
    parent.memes["teamwork"] += 1
    world.say(
        f"Then {parent.id} said, \"Let's do it side by side; two hands are better than one!\""
    )
    world.say(
        f"They {tool.prep}, and {task.teamwork_line}."
    )
    world.say(
        f"{tool.label.capitalize()} was just the thing for such a little song and run."
    )


def resolve(world: World, child: Entity, parent: Entity, task: Task, tool: Tool) -> None:
    child.memes["worry"] = 0.0
    child.memes["pride"] += 1
    child.memes["cheer"] += 2
    world.say(
        f"Together they kept a steady pace, and soon {task.ending_line}."
    )
    world.say(
        f"They {tool.tail}, and {child.id} clapped once more."
    )
    world.say(
        f"So in the nursery, under the soft lamp glow, the little team stood all snug and fine, "
        f"for the circumstance had turned to joy in a merry little line."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS["nursery"]
    task = TASKS[params.task]
    tool = select_tool(task)
    if tool is None:
        raise StoryError("No reasonable tool can solve this circumstance.")

    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent.capitalize(), kind="character", type="teacher"))

    child.memes["cheer"] += 1
    child.memes["teamwork"] += 1

    introduce(world, child, parent, task)
    world.para()
    setup(world, child, parent, task)
    world.para()
    teamwork_turn(world, child, parent, task, tool)
    world.para()
    resolve(world, child, parent, task, tool)

    world.facts.update(
        child=child,
        parent=parent,
        task=task,
        tool=tool,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    task: Task = f["task"]
    return [
        f'Write a short nursery-rhyme story that uses the word "circumstance" and shows teamwork.',
        f"Tell a gentle tale about {child.id} who wants to {task.verb}, but a circumstance makes it tricky, and then everyone helps.",
        f"Write a simple rhyme where a child, a helper, and a small tool solve a nursery circumstance together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    task: Task = f["task"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What did {child.id} want to do in the nursery?",
            answer=f"{child.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What circumstance made {task.verb} hard?",
            answer=task.circumstance.capitalize() + ".",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.id} solve the problem?",
            answer=f"They worked together and used {tool.label} to help {task.verb} safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is a circumstance?",
            answer="A circumstance is a situation or set of conditions that can make something easier or harder.",
        ),
        QAItem(
            question="Why can a step stool help?",
            answer="A step stool can help a small child reach something that is too high to touch alone.",
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


# ---------------------------------------------------------------------------
# Param resolution / generation / emit
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme story world about circumstance and teamwork.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["teacher"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    task = args.task or rng.choice(list(TASKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "teacher"
    trait = rng.choice(TRAITS)
    return StoryParams(task=task, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible task/tool combos:\n")
        for task, tool in combos:
            print(f"  {task:8} {tool:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for task in TASKS:
            params = StoryParams(
                task=task,
                name=GIRL_NAMES[0],
                gender="girl",
                parent="teacher",
                trait="cheery",
            )
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
