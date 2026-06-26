#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/flunk_bad_ending_teamwork_folk_tale.py
=============================================================================================================

A small folk-tale storyworld about a village team that tries hard, helps one
another, and sometimes still flunks the task. The stories are intended to feel
like old-fashioned village tales with concrete objects, simple turns, and a
clear ending image.

Seed premise:
- A little team in a folk-tale village tries to finish an important job.
- They work together with tools, rope, baskets, and shared courage.
- Something goes wrong; they flunk the task.
- The ending is a bad ending, but still a complete ending.

The world model uses a few physical meters and emotional memes:
- rope_tightness, load, height, wear
- hope, worry, pride, hurt, resolve

The narrative instruments are:
- setup: who gathers and why
- teamwork: who helps, how the load is shared
- flunk: the task fails for a grounded reason
- bad ending: the village is left with the consequence

This file is self-contained apart from the shared result/ASP helpers.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    noun: str
    load: str
    fail_reason: str
    failure_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    fragile: bool = False
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "green": Place(id="green", label="the village green", weather="windy", affords={"hoist", "carry"}),
    "bridge": Place(id="bridge", label="the old stone bridge", weather="misty", affords={"repair", "carry"}),
    "hill": Place(id="hill", label="the hilltop path", weather="windy", affords={"carry", "hoist"}),
}

TASKS = {
    "bell": Task(
        id="bell",
        verb="hang the bell",
        gerund="hanging the bell",
        noun="bell",
        load="heavy",
        fail_reason="the rope slipped",
        failure_image="the bell fell back into the mud",
        tags={"rope", "metal"},
    ),
    "bread": Task(
        id="bread",
        verb="carry the bread basket",
        gerund="carrying the bread basket",
        noun="bread basket",
        load="wobbly",
        fail_reason="the basket tipped",
        failure_image="the loaves rolled into the grass",
        tags={"basket", "food"},
    ),
    "lantern": Task(
        id="lantern",
        verb="raise the lantern",
        gerund="raising the lantern",
        noun="lantern",
        load="bright",
        fail_reason="the wick blew out",
        failure_image="the lantern went dark",
        tags={"light", "glass"},
    ),
}

TOOLS = [
    Tool(id="rope", label="a long rope", phrase="a long rope", helps={"bell", "bread"}, fragile=False),
    Tool(id="gloves", label="wool gloves", phrase="wool gloves", helps={"bell"}, fragile=False, plural=True),
    Tool(id="basket_cover", label="a linen cover", phrase="a linen cover", helps={"bread"}, fragile=False),
    Tool(id="glass_wrap", label="a little cloth wrap", phrase="a little cloth wrap", helps={"lantern"}, fragile=True),
]

NAMES = ["Anya", "Bram", "Cleo", "Dara", "Eli", "Faye", "Gavin", "Hilda"]
TITLES = ["woodcutter", "goatherd", "miller", "weaver", "baker", "herder"]
ROLES = ["elder", "child", "helper"]


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    helper: str
    elder: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def task_needs_team(task: Task) -> bool:
    return True


def compatible_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.helps:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, p in PLACES.items():
        for task_id, task in TASKS.items():
            if task.verb and task_needs_team(task) and compatible_tool(task) and task_id in p.affords or p.affords:
                combos.append((place, task_id))
    return combos


def explain_rejection(task: Task) -> str:
    return f"(No story: there is no fair tool or believable teamwork path for {task.gerund}.)"


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def _set(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _add(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _mem(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def predict_fail(world: World, task: Task) -> bool:
    sim = world.copy()
    team = sim.characters()
    if len(team) < 2:
        return True
    _add(team[0], "load", 1)
    _add(team[1], "load", 1)
    return True


def tell(place: Place, task: Task, hero: str, helper: str, elder: str) -> World:
    world = World(place)
    child = world.add(Entity(id=hero, kind="character", type="child"))
    helper_ent = world.add(Entity(id=helper, kind="character", type="helper"))
    elder_ent = world.add(Entity(id=elder, kind="character", type="elder"))
    tool = compatible_tool(task)
    if tool is None:
        raise StoryError(explain_rejection(task))
    world.add(Entity(id=tool.id, type="thing", label=tool.label, phrase=tool.phrase, plural=tool.plural))

    _mem(child, "hope", 1)
    _mem(helper_ent, "hope", 1)
    _mem(elder_ent, "worry", 1)

    world.say(
        f"On {place.label}, {child.id} and {helper_ent.id} came to help {elder_ent.id} with {task.verb}."
    )
    world.say(
        f"They carried {tool.phrase} because the job looked too hard for one pair of hands."
    )

    world.para()
    _add(child, "load", 1)
    _add(helper_ent, "load", 1)
    _mem(child, "resolve", 1)
    _mem(helper_ent, "resolve", 1)
    world.say(
        f"{child.id} took one end and {helper_ent.id} took the other, so the work could move step by step."
    )
    world.say(
        f"The three of them leaned into the wind, and for a little while the teamwork looked strong."
    )

    world.para()
    _add(child, "wear", 1)
    _add(helper_ent, "wear", 1)
    _add(tool_entity(world, tool.id), "wear", 1)
    _mem(elder_ent, "worry", 1)
    _mem(child, "hope", 1)

    if task.id == "bell":
        _add(child, "rope_tightness", -1)
    elif task.id == "bread":
        _add(helper_ent, "balance", -1)
    else:
        _add(child, "wind", 1)

    world.say(
        f"But then {task.fail_reason}. {task.failure_image}."
    )
    world.say(
        f"The team tried to fix it together, yet the bad luck beat their hands and their good hearts."
    )

    world.para()
    _mem(child, "hurt", 1)
    _mem(helper_ent, "hurt", 1)
    _mem(elder_ent, "hurt", 1)
    _mem(child, "hope", -1)
    _mem(helper_ent, "hope", -1)
    _mem(elder_ent, "worry", 1)

    world.say(
        f"In the end, they flunked the task. {task.gerund.capitalize()} did not save the day."
    )
    world.say(
        f"{elder_ent.id} stood by the empty workspot, and {child.id} and {helper_ent.id} watched the ruined thing go still."
    )

    world.facts.update(
        child=child,
        helper=helper_ent,
        elder=elder_ent,
        tool=tool,
        task=task,
        place=place,
        failed=True,
    )
    return world


def tool_entity(world: World, tool_id: str) -> Entity:
    for e in world.entities.values():
        if e.id == tool_id:
            return e
    raise KeyError(tool_id)


# ---------------------------------------------------------------------------
# Story text helpers
# ---------------------------------------------------------------------------

def intro_line(world: World) -> str:
    f = world.facts
    return f"{f['child'].id} and {f['helper'].id} were known in the village for helping when work was too heavy for one person alone."


def ending_line(world: World) -> str:
    f = world.facts
    return f"By dusk, the village green was quiet again, with the broken job left where the wind could worry it."


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    place = f["place"]
    return [
        f'Write a short folk tale about teamwork at {place.label} that includes the word "flunk".',
        f"Tell a gentle village story where {f['child'].id} and {f['helper'].id} try to {task.verb} but fail in the end.",
        f"Write a sad ending story about helpers, an old tool, and a task that goes wrong on the {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task = f["task"]
    child = f["child"]
    helper = f["helper"]
    elder = f["elder"]
    tool = f["tool"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who tried to {task.verb} at {place.label}?",
            answer=f"{child.id}, {helper.id}, and {elder.id} all joined the job, but the two helpers did most of the carrying.",
        ),
        QAItem(
            question=f"What did the team use to help with {task.gerund}?",
            answer=f"They used {tool.phrase} because the task was too heavy and awkward to do by bare hands alone.",
        ),
        QAItem(
            question="Did the folk-tale teamwork work out?",
            answer=f"No. They worked together, but the job still flunked when {task.fail_reason}.",
        ),
        QAItem(
            question=f"What was the bad ending image in the story?",
            answer=f"The ending showed how {task.failure_image}, so the village was left with a failed task instead of a finished one.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "rope": [("What is a rope for?",
              "A rope is a long cord used for tying, pulling, lifting, or holding things together.")],
    "basket": [("What is a basket?",
                "A basket is a container with open spaces made for carrying food, flowers, or other small things.")],
    "lantern": [("What is a lantern?",
                 "A lantern is a light that helps people see when it is dark or misty.")],
    "teamwork": [("What is teamwork?",
                  "Teamwork is when people help each other and do a job together.")],
    "flunk": [("What does flunk mean?",
               "To flunk means to fail a test or not do a job well enough.")],
    "bad_ending": [("What is a bad ending?",
                    "A bad ending is when a story finishes with a problem still not fixed.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"teamwork", "flunk", "bad_ending"}
    tags.update(f["task"].tags)
    out: list[QAItem] = []
    for key in ["teamwork", "flunk", "bad_ending", "rope", "basket", "lantern"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[key])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task(task_bell).
task(task_bread).
task(task_lantern).

tool(rope).
tool(gloves).
tool(basket_cover).
tool(glass_wrap).

helps(rope, task_bell).
helps(rope, task_bread).
helps(gloves, task_bell).
helps(basket_cover, task_bread).
helps(glass_wrap, task_lantern).

valid(Task, Tool) :- task(Task), tool(Tool), helps(Tool, Task).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in TASKS:
        lines.append(asp.fact("task", f"task_{t}"))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for task in tool.helps:
            lines.append(asp.fact("helps", tool.id, f"task_{task}"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(f"task_{task}", tool.id) for task, tool in ((k, compatible_tool(v)) for k, v in TASKS.items()) if tool}
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} valid task/tool pairs).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about teamwork and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
    place = args.place or rng.choice(list(PLACES))
    task = args.task or rng.choice(list(TASKS))
    if task not in TASKS:
        raise StoryError("Unknown task.")
    if not compatible_tool(TASKS[task]):
        raise StoryError(explain_rejection(TASKS[task]))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    elder = args.elder or rng.choice([n for n in NAMES if n not in {hero, helper}])
    return StoryParams(place=place, task=task, hero=hero, helper=helper, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TASKS[params.task], params.hero, params.helper, params.elder)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'empty'}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(place="green", task="bell", hero="Anya", helper="Bram", elder="Hilda"),
    StoryParams(place="bridge", task="bread", hero="Cleo", helper="Dara", elder="Eli"),
    StoryParams(place="hill", task="lantern", hero="Faye", helper="Gavin", elder="Hilda"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid task/tool pairs:")
        for item in vals:
            print(" ", item)
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
            header = f"### {p.hero} / {p.helper} / {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
