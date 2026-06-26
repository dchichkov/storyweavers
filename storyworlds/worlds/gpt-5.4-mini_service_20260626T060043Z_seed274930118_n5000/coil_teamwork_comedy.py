#!/usr/bin/env python3
"""
Coil Teamwork Comedy
====================

A small storyworld about a coiled thing, a teamwork problem, and a funny fix.

Premise:
- A helper task needs a coil to work right.
- The coil starts tangled, too tight, or out of place.
- Two characters must work together to set it right.
- The ending should show the coil neatly in use and the team laughing.

This script is self-contained and follows the Storyweavers world contract.
"""

from __future__ import annotations

import argparse
import copy
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garage"


@dataclass
class CoilTask:
    id: str
    verb: str
    gerund: str
    mess: str
    trouble: str
    fix: str
    keyword: str = "coil"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name_a: str
    name_b: str
    role_a: str
    role_b: str
    seed: Optional[int] = None


SETTINGS = {
    "garage": Setting(place="the garage"),
    "shed": Setting(place="the shed"),
    "workbench": Setting(place="the workshop"),
}

TASKS = {
    "fan": CoilTask(
        id="fan",
        verb="fix the fan",
        gerund="fixing the fan",
        mess="wobbly",
        trouble="kept slipping sideways",
        fix="stop the coil from springing loose",
        tags={"coil", "teamwork", "comedy"},
    ),
    "kite": CoilTask(
        id="kite",
        verb="build the kite launcher",
        gerund="building the kite launcher",
        mess="springy",
        trouble="kept popping up like a jack-in-the-box",
        fix="hold the coil steady",
        tags={"coil", "teamwork", "comedy"},
    ),
    "toy": CoilTask(
        id="toy",
        verb="repair the toy robot",
        gerund="repairing the toy robot",
        mess="twisty",
        trouble="kept making the arm spin in circles",
        fix="keep the coil neat",
        tags={"coil", "teamwork", "comedy"},
    ),
}

TOOLS = {
    "hook": Tool(id="hook", label="a small hook", phrase="a small hook", helps={"coil"}),
    "clip": Tool(id="clip", label="a strong clip", phrase="a strong clip", helps={"coil"}),
    "gloves": Tool(id="gloves", label="pair of work gloves", phrase="a pair of work gloves", helps={"coil"}),
}

NAMES = ["Mia", "Leo", "Zoe", "Ben", "Nora", "Finn", "Ava", "Max"]
ROLES = ["helper", "builder", "fixer", "planner", "mender", "picker"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for task in TASKS:
            for tool in TOOLS:
                combos.append((place, task, tool))
    return combos


def setup_story(world: World, hero_a: Entity, hero_b: Entity, task: CoilTask, tool: Tool) -> None:
    world.say(
        f"{hero_a.id} and {hero_b.id} were a team in {world.setting.place}, "
        f"trying to {task.verb}."
    )
    world.say(
        f"They had {tool.phrase}, but the coil {task.trouble}."
    )


def predict_fix(world: World, task: CoilTask, tool: Tool) -> bool:
    sim = world.copy()
    sim.facts["tool"] = tool
    return "coil" in tool.helps and task.id in {"fan", "kite", "toy"}


def conflict(world: World, hero_a: Entity, hero_b: Entity, task: CoilTask) -> None:
    hero_a.memes["frustration"] = hero_a.memes.get("frustration", 0) + 1
    hero_b.memes["frustration"] = hero_b.memes.get("frustration", 0) + 1
    world.say(
        f"{hero_a.id} tugged one way and {hero_b.id} tugged the other, "
        f"and the coil made a silly boing sound."
    )
    world.say(
        f"That only made the problem twistier."
    )


def teamwork_fix(world: World, hero_a: Entity, hero_b: Entity, task: CoilTask, tool: Tool) -> None:
    hero_a.memes["joy"] = hero_a.memes.get("joy", 0) + 1
    hero_b.memes["joy"] = hero_b.memes.get("joy", 0) + 1
    world.say(
        f"Then they laughed, slowed down, and worked together."
    )
    world.say(
        f"{hero_a.id} held the coil with {tool.label}, while {hero_b.id} guided it into a neat curve."
    )
    world.say(
        f"At last, the coil stayed put, and {task.verb} finally worked."
    )
    world.say(
        f"The whole thing ended with a happy little cheer and a few giggles at the wobbly start."
    )


def tell_story(place: str, task_id: str, tool_id: str, name_a: str, name_b: str,
               role_a: str, role_b: str) -> World:
    world = World(SETTINGS[place])
    task = TASKS[task_id]
    tool = TOOLS[tool_id]

    hero_a = world.add(Entity(id=name_a, kind="character", type="person", label=role_a))
    hero_b = world.add(Entity(id=name_b, kind="character", type="person", label=role_b))

    world.facts.update(task=task, tool=tool, hero_a=hero_a, hero_b=hero_b)

    setup_story(world, hero_a, hero_b, task, tool)
    world.para()
    world.say(
        f"{hero_a.id} wanted to hurry, but {hero_b.id} said the coil needed a gentler plan."
    )
    if predict_fix(world, task, tool):
        conflict(world, hero_a, hero_b, task)
        world.para()
        teamwork_fix(world, hero_a, hero_b, task, tool)
    else:
        raise StoryError("The chosen tool cannot reasonably help with the coil.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: CoilTask = f["task"]
    tool: Tool = f["tool"]
    hero_a: Entity = f["hero_a"]
    hero_b: Entity = f["hero_b"]
    return [
        f"Write a funny story about {hero_a.id} and {hero_b.id} working together to {task.verb} with {tool.phrase}.",
        f"Tell a child-friendly comedy where a coil causes trouble, but teamwork solves it.",
        f"Write a short story about a tricky coil, two helpers, and a silly but successful fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: CoilTask = f["task"]
    tool: Tool = f["tool"]
    hero_a: Entity = f["hero_a"]
    hero_b: Entity = f["hero_b"]
    return [
        QAItem(
            question=f"Who worked together in the story?",
            answer=f"{hero_a.id} and {hero_b.id} worked together as a team.",
        ),
        QAItem(
            question=f"What was the tricky thing in the story?",
            answer=f"The tricky thing was the coil, which kept causing trouble while they tried to {task.verb}.",
        ),
        QAItem(
            question=f"What helped them fix the problem?",
            answer=f"{tool.phrase} helped them keep the coil steady and finish the job.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the coil neatly in place and everyone laughing at the funny mistake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coil?",
            answer="A coil is something wound into circles or loops, like a spring or a looped wire.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together instead of alone.",
        ),
        QAItem(
            question="Why can comedy be funny?",
            answer="Comedy is funny because it can use silly trouble, surprise, or harmless mistakes that end well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
task_combo(P,T,O) :- place(P), task(T), tool(O).
supports_teamwork(O) :- tool(O), helps(O,coil).
good_story(P,T,O) :- task_combo(P,T,O), supports_teamwork(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for o, tool in TOOLS.items():
        lines.append(asp.fact("tool", o))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", o, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show task_combo/3."))
    return sorted(set(asp.atoms(model, "task_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Coil teamwork comedy storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--role-a")
    ap.add_argument("--role-b")
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    place, task, tool = rng.choice(filtered)
    name_a = args.name_a or rng.choice(NAMES)
    name_b = args.name_b or rng.choice([n for n in NAMES if n != name_a])
    role_a = args.role_a or rng.choice(ROLES)
    role_b = args.role_b or rng.choice([r for r in ROLES if r != role_a])
    return StoryParams(place=place, task=task, tool=tool, name_a=name_a, name_b=name_b, role_a=role_a, role_b=role_b)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params.place, params.task, params.tool, params.name_a, params.name_b, params.role_a, params.role_b)
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
    StoryParams(place="garage", task="fan", tool="hook", name_a="Mia", name_b="Leo", role_a="fixer", role_b="helper"),
    StoryParams(place="shed", task="kite", tool="clip", name_a="Zoe", name_b="Ben", role_a="planner", role_b="builder"),
    StoryParams(place="workbench", task="toy", tool="gloves", name_a="Ava", name_b="Finn", role_a="mender", role_b="picker"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show task_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
