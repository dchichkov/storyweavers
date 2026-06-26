#!/usr/bin/env python3
"""
storyworlds/worlds/dim_dialogue_rhyme_teamwork_fable.py
========================================================

A small fable-style story world about a dim place, a shared task, a bit of
rhyme, and teamwork.

Seed premise:
- The world is dim.
- A helper pair must solve a practical problem together.
- They speak in dialogue.
- They use a rhyme to guide their teamwork.
- The ending should prove a real change in the world state.

The story is intentionally classical and child-facing: one problem, one shared
turn, one warm resolution.
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
# Typed world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hare", "fox", "crow", "mouse", "owl"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    dim: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    action: str
    plural: bool = False


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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "barn": Setting(place="the dim barn", dim=True, affords={"find_lantern", "share_light"}),
    "cave": Setting(place="the dim cave", dim=True, affords={"find_lantern", "share_light"}),
    "shed": Setting(place="the dim shed", dim=True, affords={"find_lantern", "share_light"}),
}

TASKS = {
    "lantern": Task(
        id="lantern",
        verb="find the lantern",
        gerund="finding the lantern",
        risk="stay in the dark",
        keyword="dim",
        tags={"dim", "light"},
    ),
    "book": Task(
        id="book",
        verb="read the map",
        gerund="reading the map",
        risk="miss the path",
        keyword="dim",
        tags={"dim", "map"},
    ),
}

TOOLS = [
    Tool(
        id="lantern",
        label="a lantern",
        phrase="a little lantern",
        helps={"light"},
        action="light the lantern",
    ),
    Tool(
        id="lamp",
        label="a lamp",
        phrase="a small lamp",
        helps={"light"},
        action="carry the lamp together",
    ),
    Tool(
        id="mirror",
        label="a bright mirror",
        phrase="a bright mirror",
        helps={"light"},
        action="tilt the mirror toward the light",
    ),
]

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    task: str
    helper_a: str
    helper_b: str
    tool: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HARE_NAMES = ["Nia", "Pip", "Milo", "Tess", "Oren", "Lia", "Bram", "June"]
FOX_NAMES = ["Fern", "Rowan", "Kite", "Poppy", "Ash", "Dawn", "Moss", "Wren"]

FIRST_NAMES = {
    "hare": HARE_NAMES,
    "fox": FOX_NAMES,
}

RHYME_LINES = [
    "In a dim old place, two friends took a look,",
    "One held the lamp, one held the book.",
    "One said, 'Together we will see the way,'",
    "The other said, 'Yes, team up today.'",
]

FOCUS_ORDER = ["dim", "light", "teamwork"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Dim fable story world with dialogue, rhyme, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices={t.id for t in TOOLS})
    ap.add_argument("--helper-a")
    ap.add_argument("--helper-b")
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


def _is_valid_pair(a: str, b: str) -> bool:
    return a != b


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    tool = args.tool or rng.choice([t.id for t in TOOLS])

    helper_a = args.helper_a or rng.choice(FIRST_NAMES["hare"])
    helper_b = args.helper_b or rng.choice(FIRST_NAMES["fox"])
    if not _is_valid_pair(helper_a, helper_b):
        raise StoryError("The two helpers must be different characters.")

    if args.tool == "lamp" and task == "book":
        raise StoryError("A lamp does not solve the map-reading story well enough.")
    if args.task == "lantern" and tool not in {"lantern", "lamp", "mirror"}:
        raise StoryError("This task needs a light-making tool.")
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")

    return StoryParams(setting=setting, task=task, helper_a=helper_a, helper_b=helper_b, tool=tool)


def select_tool(tool_id: str) -> Tool:
    for t in TOOLS:
        if t.id == tool_id:
            return t
    raise StoryError(f"Unknown tool: {tool_id}")


def predict_success(setting: Setting, task: Task, tool: Tool) -> bool:
    return "light" in tool.helps and setting.dim and task.keyword == "dim"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def tell(setting: Setting, task: Task, tool: Tool, helper_a: str, helper_b: str) -> World:
    world = World(setting)
    a = world.add(Entity(id=helper_a, kind="character", type="hare"))
    b = world.add(Entity(id=helper_b, kind="character", type="fox"))
    obj = world.add(Entity(id=task.id, type="thing", label=task.id, phrase=task.keyword))

    a.memes["hope"] = 1.0
    b.memes["hope"] = 1.0
    a.meters["tired"] = 0.0
    b.meters["tired"] = 0.0
    obj.meters["dimness"] = 2.0 if setting.dim else 0.5

    world.say(f"In {setting.place}, the light was dim, and the corners looked quiet and gray.")
    world.say(f"{a.id} said, \"This place feels too dim.\"")
    world.say(f"{b.id} said, \"Then let's work together.\"")

    world.para()
    world.say(f"They went to {task.verb}, but the dimness made every step a little tricky.")
    world.say(f"{a.id} said, \"I can search here.\"")
    world.say(f"{b.id} said, \"And I can search there.\"")

    if predict_success(setting, task, tool):
        world.say(f"At last they found {tool.phrase}.")
        world.say(f"{a.id} said, \"I'll lift it.\"")
        world.say(f"{b.id} said, \"I'll steady it.\"")
        world.say(f"Together they {tool.action}, and the room grew bright and warm.")

        world.para()
        for line in RHYME_LINES:
            world.say(line)

        a.meters["effort"] = 1.0
        b.meters["effort"] = 1.0
        a.memes["pride"] = 1.0
        b.memes["pride"] = 1.0
        obj.meters["dimness"] = 0.0
        world.facts["resolved"] = True
        world.facts["tool_label"] = tool.label
    else:
        world.say(f"They tried, but this tool did not help enough.")
        world.say(f"{a.id} said, \"We need a better plan.\"")
        world.say(f"{b.id} said, \"Yes, one that fits the dim place.\"")
        world.facts["resolved"] = False
        world.facts["tool_label"] = tool.label

    world.facts.update(setting=setting, task=task, tool=tool, helper_a=a, helper_b=b, object=obj)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children about a dim place where two friends solve a problem by teamwork.',
        f'Write a story that includes dialogue and a small rhyme, and ends with {f["helper_a"].id} and {f["helper_b"].id} helping each other.',
        f'Write a gentle fable where a dim room becomes brighter because two helpers work together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["helper_a"], f["helper_b"]
    task: Task = f["task"]
    tool: Tool = f["tool"]
    setting: Setting = f["setting"]
    resolved = f["resolved"]

    out = [
        QAItem(
            question=f"Who were the two helpers in the story?",
            answer=f"The two helpers were {a.id} and {b.id}. They stayed kind and worked as a team.",
        ),
        QAItem(
            question=f"What made the place tricky at first?",
            answer=f"The place was dim, so it was hard to see clearly at {setting.place}.",
        ),
        QAItem(
            question=f"What were they trying to do?",
            answer=f"They were trying to {task.verb}.",
        ),
        QAItem(
            question=f"What did they use to help the job?",
            answer=f"They used {tool.label}, and they needed both helpers to use it well.",
        ),
    ]
    if resolved:
        out.append(
            QAItem(
                question="What changed by the end of the story?",
                answer="By the end, the dim place grew brighter because the friends worked together and succeeded.",
            )
        )
    else:
        out.append(
            QAItem(
                question="What did the friends decide when the tool was not enough?",
                answer="They decided to make a better plan together, because teamwork still mattered more than giving up.",
            )
        )
    return out


WORLD_KNOWLEDGE = {
    "dim": [
        QAItem(
            question="What does dim mean?",
            answer="Dim means there is only a little light, so things are hard to see.",
        )
    ],
    "light": [
        QAItem(
            question="What can a lantern do?",
            answer="A lantern can give light in a dark or dim place.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | {"dim", "teamwork"}
    if world.facts["resolved"]:
        tags.add("light")
    out: list[QAItem] = []
    for key in FOCUS_ORDER:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(shed).
setting(barn).
setting(cave).
dim(shed).
dim(barn).
dim(cave).

task(lantern).
task(book).

tool(lantern).
tool(lamp).
tool(mirror).

helps(lantern, light).
helps(lamp, light).
helps(mirror, light).

valid(Setting, Task, Tool) :- setting(Setting), task(Task), tool(Tool), dim(Setting), helps(Tool, light), Task = lantern.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        if SETTINGS[s].dim:
            lines.append(asp.fact("dim", s))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {
        (s, t, tool.id)
        for s, setting in SETTINGS.items()
        for t, task in TASKS.items()
        for tool in TOOLS
        if setting.dim and "light" in tool.helps and t == "lantern"
    }
    asp_set = set(asp_valid())
    if asp_set == python_set:
        print(f"OK: ASP matches Python ({len(asp_set)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(asp_set - python_set))
    print("Python only:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    tool = select_tool(params.tool)
    world = tell(setting, task, tool, params.helper_a, params.helper_b)
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
    StoryParams(setting="barn", task="lantern", helper_a="Nia", helper_b="Fern", tool="lantern"),
    StoryParams(setting="cave", task="lantern", helper_a="Pip", helper_b="Rowan", tool="mirror"),
    StoryParams(setting="shed", task="lantern", helper_a="Milo", helper_b="Wren", tool="lamp"),
]


def resolve_for_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        task=args.task or rng.choice(list(TASKS)),
        helper_a=args.helper_a or rng.choice(HARE_NAMES),
        helper_b=args.helper_b or rng.choice(FOX_NAMES),
        tool=args.tool or rng.choice([t.id for t in TOOLS]),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combinations:")
        for row in combos:
            print(" ", row)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.helper_a} and {p.helper_b} in {p.setting} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
