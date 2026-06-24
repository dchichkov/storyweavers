#!/usr/bin/env python3
"""
A bedtime-story world about a sleepy child, a small caregiving task, and a
gentle teamwork turn.

Seed tale:
---
At bedtime, Pippa the little rabbit loved to make her room cozy. One night she
noticed her toy bird had a tiny crumb in its beak, and the bird kept making a
soft sniffle. Pippa fetched a little straw and tried to aspirate the crumb out,
but the toy bird's tube was narrow and the straw kept slipping.

Her brother Milo brought a tiny brush, and Pippa held the bird still while Milo
waved a fan to keep the feathers calm. Together they worked slowly until the
crumb was gone. The bird gave one last sniffle, then sat tall and peaceful.
Pippa yawned, proud of their teamwork, and the room felt safe and sleepy again.

Story shape:
- bedtime setup
- a small problem that needs care
- a foreshadowed warning about rushing
- teamwork to finish the job
- a calm ending image proving the change
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

ASP_RULES = r"""
#show valid_story/4.
#show needs_help/3.
#show resolves/4.
#show foreshadows/3.

needs_help(C, Task, Tool) :- child(C), task(Task), tool(Tool), requires(Task, Tool).
foreshadows(C, Task, Clue) :- child(C), task(Task), clue(Clue), warns(Clue, Task).
resolves(C, Task, Tool, Helper) :- needs_help(C, Task, Tool), helper(Helper), uses(Helper, Tool).
valid_story(C, Task, Tool, Helper) :- child(C), task(Task), tool(Tool), helper(Helper), resolves(C, Task, Tool, Helper).
"""

def _load_asp():
    import asp  # lazy import
    return asp

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class Setting:
    place: str = "the bedroom"
    bedtime: bool = True
    affords: set[str] = field(default_factory=set)

@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    problem: str
    clue: str
    requires_tool: str
    tag: str
    foreshadow: str

@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fits: set[str]
    helps: set[str]
    action: str

@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    uses_tool: str
    role: str

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

WORLD_SETTING = Setting()
TASKS = {
    "aspirate": Task(
        id="aspirate",
        verb="aspirate the crumb",
        gerund="carefully aspirating the crumb",
        rush="squeeze the little straw too hard",
        problem="the crumb might stay stuck",
        clue="The toy bird gave a tiny sniffle, as if it needed a slow hand.",
        requires_tool="straw",
        tag="aspirate",
        foreshadow="A tiny sniffle warned that the crumb needed patience.",
    ),
}
TOOLS = {
    "straw": Tool(
        id="straw",
        label="tiny straw",
        phrase="a tiny straw",
        fits={"beak"},
        helps={"aspirate"},
        action="suck out the crumb slowly",
    ),
    "brush": Tool(
        id="brush",
        label="soft brush",
        phrase="a soft brush",
        fits={"beak"},
        helps={"aspirate"},
        action="brush away the crumb gently",
    ),
}
HELPERS = {
    "milo": Helper(
        id="Milo",
        label="Milo",
        phrase="Pippa's brother Milo",
        uses_tool="brush",
        role="helper",
    ),
    "pippa": Helper(
        id="Pippa",
        label="Pippa",
        phrase="Pippa",
        uses_tool="straw",
        role="child",
    ),
}

@dataclass
class StoryParams:
    child: str = "Pippa"
    helper: str = "Milo"
    task: str = "aspirate"
    tool: str = "straw"
    seed: Optional[int] = None

NAMES = ["Pippa", "Milo", "Nora", "Toby", "Luna", "Ivy"]
HELPER_NAMES = ["Milo", "Nora", "Toby", "Luna"]
TASK_ORDER = ["aspirate"]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-story world: a child, a small fix, teamwork, and foreshadowing.")
    ap.add_argument("--child", choices=NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
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

def _valid_pair(task: Task, tool: Tool) -> bool:
    return task.id in tool.helps

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    task = TASKS[args.task] if args.task else rng.choice(list(TASKS.values()))
    tool = TOOLS[args.tool] if args.tool else rng.choice(list(TOOLS.values()))
    if not _valid_pair(task, tool):
        raise StoryError("That tool cannot reasonably help with this bedtime task.")
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    return StoryParams(child=child, helper=helper, task=task.id, tool=tool.id)

def asp_facts() -> str:
    asp = _load_asp()
    lines = []
    for c in NAMES:
        lines.append(asp.fact("child", c))
    for t in TASKS:
        lines.append(asp.fact("task", t))
        lines.append(asp.fact("requires", t, TASKS[t].requires_tool))
        lines.append(asp.fact("clue", TASKS[t].tag))
        lines.append(asp.fact("warns", TASKS[t].tag, t))
    for u in TOOLS:
        lines.append(asp.fact("tool", u))
    for h in HELPER_NAMES:
        lines.append(asp.fact("helper", h))
    for t in TASKS.values():
        for u in TOOLS.values():
            if t.id in u.helps:
                lines.append(asp.fact("uses", "Milo" if u.id == "brush" else "Pippa", u.id))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    asp = _load_asp()
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = {("Pippa", "aspirate", "straw", "Milo"), ("Pippa", "aspirate", "brush", "Milo")}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: clingo gate matches python gate ({len(cl)} stories).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1

def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f"Write a gentle bedtime story about {p['child']} and {p['helper']} doing a careful {p['task']} task.",
        f"Tell a bedtime story where a tiny problem needs teamwork, and a little clue foreshadows the fix.",
        f"Make a cozy story using the word '{p['task']}' and end with everyone feeling sleepy and safe.",
    ]

def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    return [
        QAItem(question=f"Who was the child in the story?", answer=f"The child was {p['child']}."),
        QAItem(question=f"Why did the child need help?", answer=f"{p['child']} needed help because the crumb was stuck and needed a careful {p['task']}."),
        QAItem(question=f"Who helped in the teamwork part?", answer=f"{p['helper']} helped by bringing the {p['tool_label']} and working beside {p['child']}."),
        QAItem(question=f"What foreshadowing clue warned the characters?", answer=p["foreshadow"]),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is teamwork?", answer="Teamwork means people work together to do something well."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a small clue that hints at what will matter later."),
        QAItem(question="Why is bedtime a good time for a calm story?", answer="Bedtime is a good time for a calm story because gentle words help little listeners feel sleepy and safe."),
    ]

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7})")
    return "\n".join(lines)

def tell(params: StoryParams) -> World:
    world = World(WORLD_SETTING)
    child = world.add(Entity(id=params.child, kind="character", type="child", label=params.child))
    helper = world.add(Entity(id=params.helper, kind="character", type="child", label=params.helper))
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    world.facts.update(child=child.id, helper=helper.id, task=task.id, tool_label=tool.label, foreshadow=task.foreshadow)

    world.say(f"At bedtime, {child.id} was in {world.setting.place}, ready to make the room cozy.")
    world.say(f"{child.id} noticed a tiny crumb in the toy bird's beak, and the bird gave a small sniffle.")
    world.say(task.foreshadow)
    world.para()
    world.say(f"{child.id} wanted to {task.verb}, but the little straw kept slipping because the opening was narrow.")
    world.say(f"That meant the job needed a slower way, not a rushed one.")
    world.para()
    world.say(f"Then {helper.id} came over with {tool.phrase}, and {child.id} held the bird still.")
    world.say(f"Together they worked as a team: {child.id} kept the bird calm while {helper.id} used the {tool.label} to {tool.action}.")
    world.say(f"At last the crumb came free, the sniffle stopped, and the bird sat quiet and tall.")
    world.para()
    world.say(f"{child.id} yawned, proud of the teamwork, and the bedroom felt soft and safe again.")
    return world

def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid stories:")
        for row in vals:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(child="Pippa", helper="Milo", task="aspirate", tool="straw"))]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
