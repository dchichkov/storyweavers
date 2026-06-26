#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/try_shuttle_sanitary_dining_room_problem_solving.py
==============================================================================================================================

A small bedtime-story world about a child who tries to shuttle food safely in a
dining room, runs into a sanitary problem, and solves it with a gentle, funny
compromise.

Premise:
- A careful child wants to help carry supper through the dining room.
- The family cares about keeping the table sanitary.
- A slip, spill, or smudge creates a problem.

Turn:
- The child tries, but the task is trickier than expected.
- An adult or helper notices the sanitary risk.

Resolution:
- They solve the problem by changing the method, using cleaner gear, or
  separating clean and dirty things.
- The ending image proves the room is orderly again.

This world keeps the story child-facing, concrete, and bedtime-soft, while still
using simulated state to drive the prose.
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
# Core world model
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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    on_table: bool = False
    sanitary: bool = True
    clean: bool = True
    useful: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dining room"


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    mishap: str
    risk: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects: set[str]
    helps: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind != "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        return clone


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------
SETTINGS = {
    "dining_room": Setting(place="the dining room"),
}

TASKS = {
    "shuttle": Task(
        id="shuttle",
        verb="shuttle the warm bowls to the table",
        gerund="shuttling the warm bowls",
        mishap="a little spill on the napkin",
        risk="the table might stop being sanitary",
        fix_hint="use a tray and keep the cups steady",
        tags={"shuttle", "sanitary", "problem_solving"},
    ),
    "soup": Task(
        id="soup",
        verb="carry the soup carefully",
        gerund="carrying the soup",
        mishap="a tiny drip on the tablecloth",
        risk="the tablecloth might stop being sanitary",
        fix_hint="hold the spoon with two hands",
        tags={"sanitary", "problem_solving"},
    ),
    "crumbs": Task(
        id="crumbs",
        verb="move the crumb plate",
        gerund="moving the crumb plate",
        mishap="crumbs on the floor",
        risk="the floor might get messy",
        fix_hint="use a small dustpan",
        tags={"humor", "problem_solving"},
    ),
}

TOOLS = {
    "tray": Tool(
        id="tray",
        label="a bright tray",
        phrase="a bright tray with tall sides",
        protects={"sanitary"},
        helps={"shuttle"},
    ),
    "napkins": Tool(
        id="napkins",
        label="clean napkins",
        phrase="a stack of clean napkins",
        protects={"sanitary"},
        helps={"soup", "shuttle"},
        plural=True,
    ),
    "cloth": Tool(
        id="cloth",
        label="a clean cloth",
        phrase="a clean cloth for wiping",
        protects={"sanitary"},
        helps={"soup", "crumbs", "shuttle"},
    ),
    "small_spoon": Tool(
        id="small spoon",
        label="a small spoon",
        phrase="a small spoon that fit neatly in a tiny hand",
        protects=set(),
        helps={"soup"},
    ),
}

CHILD_NAMES = ["Milo", "Luna", "Nora", "Theo", "Ivy", "Owen", "Maya", "Leo"]
ADULT_NAMES = ["Mom", "Dad", "Aunt June", "Grandpa", "Abuela"]


@dataclass
class StoryParams:
    place: str = "dining_room"
    task: str = "shuttle"
    tool: str = "tray"
    name: str = "Milo"
    helper: str = "Mom"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------
def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    actor.meters[task.id] = actor.meters.get(task.id, 0.0) + 1.0
    actor.memes["pride"] = actor.memes.get("pride", 0.0) + 1.0
    actor.memes["worry"] = actor.memes.get("worry", 0.0) + 0.5

    if task.id == "shuttle":
        for item in world.items():
            if item.carried_by == actor.id and item.type == "bowl":
                item.meters["spill"] = item.meters.get("spill", 0.0) + 1.0
                item.clean = False
                item.sanitary = False
                actor.memes["oops"] = actor.memes.get("oops", 0.0) + 1.0
    elif task.id == "soup":
        for item in world.items():
            if item.carried_by == actor.id and item.type == "bowl":
                item.meters["drip"] = item.meters.get("drip", 0.0) + 1.0
                item.clean = False
                item.sanitary = False
                actor.memes["oops"] = actor.memes.get("oops", 0.0) + 1.0
    elif task.id == "crumbs":
        world.facts["crumbs_moved"] = True

    if narrate:
        world.say(f"{actor.id} tried to {task.verb}.")


def predict_problem(world: World, actor: Entity, task: Task) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    sanitary_risk = any((not item.sanitary) for item in sim.items() if item.type == "bowl")
    worry = actor.memes.get("worry", 0.0)
    return {"sanitary_risk": sanitary_risk, "worry": worry}


def apply_solution(world: World, actor: Entity, helper: Entity, task: Task, tool: Tool) -> bool:
    if task.id not in tool.helps:
        return False
    if "sanitary" not in tool.protects:
        return False

    world.facts["solution_tool"] = tool
    actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1.0
    actor.memes["worry"] = max(0.0, actor.memes.get("worry", 0.0) - 1.0)
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1.0

    for item in world.items():
        if item.type == "bowl":
            item.sanitary = True
            item.clean = True

    world.say(
        f"{helper.id} smiled and pointed to {tool.label}. "
        f'"Let\'s use {tool.phrase} and keep the table neat," {helper.pronoun()} said.'
    )
    world.say(
        f"{actor.id} nodded and tried again, this time with steady hands and a small laugh."
    )
    return True


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="boy" if params.name in {"Milo", "Theo", "Owen", "Leo"} else "girl",
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="mother" if params.helper in {"Mom"} else "man",
    ))
    bowl = world.add(Entity(
        id="bowl",
        type="bowl",
        label="soup bowl",
        phrase="a warm soup bowl",
        owner=child.id,
        caretaker=helper.id,
        carried_by=child.id,
        on_table=False,
        sanitary=True,
        clean=True,
        useful=True,
    ))
    table = world.add(Entity(
        id="table",
        type="table",
        label="the table",
        phrase="the dining table",
        on_table=True,
        sanitary=True,
        clean=True,
        useful=True,
    ))

    task = TASKS[params.task]
    tool = TOOLS[params.tool]

    world.say(
        f"In {world.setting.place}, {child.id} was a careful little helper with a big job to do."
    )
    world.say(
        f"{child.id} loved to {task.gerund}, because helping at supper felt almost as grand as a parade for spoons."
    )
    world.say(
        f"{child.id}'s {helper.id} had put out {bowl.phrase} and reminded {child.id} to keep everything sanitary."
    )

    world.para()
    world.say(
        f"Then {child.id} took a breath and decided to try."
    )
    pred = predict_problem(world, child, task)
    world.facts["predicted_risk"] = pred["sanitary_risk"]
    _do_task(world, child, task, narrate=True)

    if pred["sanitary_risk"] or child.memes.get("oops", 0.0) >= THRESHOLD:
        world.say(
            f"Oops! A tiny splash landed where it should not have, and even the napkins looked surprised."
        )
        world.say(
            f"That meant the dining room was not as sanitary as it should be."
        )
        helper.memes["concern"] = helper.memes.get("concern", 0.0) + 1.0
    else:
        world.say(
            f"Nothing spilled, but {child.id} still worried about the neatness of the table."
        )

    world.para()
    if apply_solution(world, child, helper, task, tool):
        world.say(
            f"Together they made the problem smaller by using {tool.label}, and the bowl stayed safe."
        )
        world.say(
            f"After that, {child.id} could finish {task.gerund} without making the table frown."
        )
    else:
        raise StoryError("No reasonable solution tool matches this task.")

    world.say(
        f"When supper was done, {table.label} was clean, {bowl.label} was steady, and {child.id} looked sleepy and pleased."
    )

    world.facts.update(child=child, helper=helper, bowl=bowl, table=table, task=task, tool=tool)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    return [
        f"Write a bedtime story about {child.id} trying to {task.verb} in the dining room.",
        f"Tell a gentle, funny story where a child learns how to keep a dining room sanitary while helping at supper.",
        f"Write a short story with a small problem and a tidy solution, featuring the word '{task.id}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    bowl: Entity = f["bowl"]
    task: Task = f["task"]
    tool: Tool = f["tool"]

    return [
        QAItem(
            question=f"What did {child.id} try to do in the dining room?",
            answer=f"{child.id} tried to {task.verb}.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry during the story?",
            answer=f"{helper.id} worried because a little spill could make the table less sanitary.",
        ),
        QAItem(
            question=f"What helped {child.id} solve the problem?",
            answer=f"{tool.label} helped {child.id} solve the problem and keep the {bowl.label} safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the dining room tidy, the {bowl.label} steady, and {child.id} feeling proud and sleepy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sanitary mean?",
            answer="Sanitary means clean and safe from dirt or germs.",
        ),
        QAItem(
            question="What is a tray for?",
            answer="A tray helps carry things more carefully so they are less likely to spill.",
        ),
        QAItem(
            question="Why do people wipe a table?",
            answer="People wipe a table to clean up crumbs, spills, and sticky spots.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.on_table:
            bits.append("on_table=True")
        if not e.sanitary:
            bits.append("sanitary=False")
        if not e.clean:
            bits.append("clean=False")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A task is risky if it can create a sanitary problem.
task_risky(T) :- task(T), risk(T, sanitary).

% A tool is a valid fix when it helps with the task and protects sanitation.
fix(T, U) :- task(T), tool(U), helps(U, T), protects(U, sanitary).

valid_story(T, U) :- task_risky(T), fix(T, U).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(task.tags):
            lines.append(asp.fact("tag", tid, tag))
        lines.append(asp.fact("risk", tid, "sanitary"))
    for uid, tool in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for p in sorted(tool.protects):
            lines.append(asp.fact("protects", uid, p))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", uid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_pairs_python() -> list[tuple[str, str]]:
    out = []
    for tid, task in TASKS.items():
        if "sanitary" not in task.tags and tid != "shuttle":
            continue
        for uid, tool in TOOLS.items():
            if tid in tool.helps and "sanitary" in tool.protects:
                out.append((tid, uid))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_pairs())
    b = set(valid_pairs_python())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} pairs).")
        return 0
    print("MISMATCH:")
    print(" only in clingo:", sorted(a - b))
    print(" only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="dining_room", task="shuttle", tool="tray", name="Milo", helper="Mom"),
    StoryParams(place="dining_room", task="soup", tool="napkins", name="Luna", helper="Dad"),
    StoryParams(place="dining_room", task="crumbs", tool="cloth", name="Nora", helper="Aunt June"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about trying to shuttle things safely in a dining room.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--task", choices=TASKS.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.tool:
        task = TASKS[args.task]
        tool = TOOLS[args.tool]
        if args.task not in tool.helps or "sanitary" not in tool.protects:
            raise StoryError("That tool does not solve the sanitary problem for this task.")

    candidates = [
        (t, u)
        for t, task in TASKS.items()
        for u, tool in TOOLS.items()
        if t in tool.helps and "sanitary" in tool.protects
    ]
    if args.task:
        candidates = [(t, u) for (t, u) in candidates if t == args.task]
    if args.tool:
        candidates = [(t, u) for (t, u) in candidates if u == args.tool]
    if not candidates:
        raise StoryError("No valid task/tool combination matches the given options.")

    task_id, tool_id = rng.choice(candidates)
    name = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(ADULT_NAMES)
    return StoryParams(
        place=args.place or "dining_room",
        task=task_id,
        tool=tool_id,
        name=name,
        helper=helper,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid task/tool pairs:\n")
        for t, u in pairs:
            print(f"  {t:10} {u}")
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
            header = f"### {p.name}: {p.task} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
