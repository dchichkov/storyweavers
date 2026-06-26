#!/usr/bin/env python3
"""
storyworlds/worlds/calm_homosexual_orchard_teamwork_bedtime_story.py
======================================================================

A small bedtime-story world set in an orchard, where calm teamwork helps a
child and two loving adults finish a gentle evening task together.

Seed image:
- A calm orchard at bedtime
- A child with a simple worry
- Two same-gender parents helping through teamwork
- A warm ending that feels settled and safe

This world keeps the action concrete and state-driven:
- physical meters track orchard work, tidiness, and tiredness
- emotional memes track calm, worry, and pride
- teamwork reduces strain and helps the bedtime routine end well
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["tidy", "tired", "done", "repair"]:
            self.meters.setdefault(key, 0.0)
        for key in ["calm", "worry", "pride", "love", "teamwork"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mother", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Orchard:
    place: str = "the orchard"
    bedtime: bool = True
    calm: bool = True
    affords: set[str] = field(default_factory=lambda: {"collect", "stow", "lamp"})

    def __post_init__(self) -> None:
        if self.bedtime:
            self.calm = True


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    labor: str
    result: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, orchard: Orchard) -> None:
        self.orchard = orchard
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy

        clone = World(self.orchard)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "orchard": Orchard(place="the orchard", bedtime=True),
}

TASKS = {
    "collect_apples": Task(
        id="collect_apples",
        verb="pick the fallen apples",
        gerund="picking up apples",
        rush="run to the apple trees",
        labor="gathering apples into baskets",
        result="the baskets were full and neat",
        keyword="apples",
        tags={"apple", "fruit", "basket"},
    ),
    "hang_lamps": Task(
        id="hang_lamps",
        verb="hang the little lamps",
        gerund="hanging little lamps",
        rush="hurry to the lamp hooks",
        labor="fastening the lamps along the path",
        result="the path glowed softly",
        keyword="lamps",
        tags={"lamp", "light"},
    ),
    "stack_crates": Task(
        id="stack_crates",
        verb="stack the small crates",
        gerund="stacking small crates",
        rush="carry the crates quickly",
        labor="setting the crates in a tidy row",
        result="the crate row stood still and safe",
        keyword="crates",
        tags={"crate", "wood"},
    ),
}

TOOLS = {
    "basket": Tool(
        id="basket",
        label="a basket",
        phrase="a woven basket",
        helps={"collect_apples"},
        covers={"hands"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="a small lantern with a brass handle",
        helps={"hang_lamps"},
        covers={"hands"},
    ),
    "crate_gloves": Tool(
        id="crate_gloves",
        label="soft gloves",
        phrase="soft gloves for carrying crates",
        helps={"stack_crates"},
        covers={"hands"},
        plural=True,
    ),
}

NAMES = {
    "girl": ["Lina", "Mara", "Tess", "Nia"],
    "boy": ["Owen", "Eli", "Noel", "Finn"],
}

TRAITS = ["calm", "gentle", "quiet", "kind"]


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    gender: str
    parent1: str
    parent2: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def task_needs_tool(task: Task) -> bool:
    return task.id in {"collect_apples", "hang_lamps", "stack_crates"}


def compatible_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS.values():
        if task.id in tool.helps:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for task_id in TASKS:
            if compatible_tool(TASKS[task_id]):
                combos.append((place, task_id))
    return combos


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _do_task(world: World, actor: Entity, task: Task) -> None:
    actor.memes["teamwork"] += 1
    actor.meters["done"] += 1
    actor.memes["calm"] += 1
    world.facts["task_done"] = task.id


def _help_each_other(world: World, child: Entity, parent_a: Entity, parent_b: Entity, task: Task) -> None:
    child.memes["worry"] += 1
    parent_a.memes["love"] += 1
    parent_b.memes["love"] += 1
    parent_a.memes["calm"] += 1
    parent_b.memes["calm"] += 1
    child.memes["calm"] += 1
    world.facts["teamwork"] = True


def tell(place: Orchard, task: Task, hero_name: str, hero_gender: str, parent1: str, parent2: str, trait: str) -> World:
    world = World(place)

    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        traits=["little", trait],
    ))
    mom1 = world.add(Entity(id="ParentA", kind="character", type="mother", label=parent1))
    mom2 = world.add(Entity(id="ParentB", kind="character", type="mother", label=parent2))
    tool = compatible_tool(task)
    if tool is None:
        raise StoryError("No compatible tool exists for this task.")

    world.facts.update(child=child, parent1=mom1, parent2=mom2, tool=tool, task=task, place=place)

    # Act 1: bedtime calm.
    world.say(
        f"At bedtime in the orchard, {hero_name} was a {trait} little {hero_gender} who liked the hush between the trees."
    )
    world.say(
        f"{mom1.label_word.capitalize()} and {mom2.label_word.capitalize()} were a calm family, and they loved working together."
    )
    world.say(
        f"That night, they all wanted to {task.verb}, but they needed the right tool first: {tool.phrase}."
    )

    # Act 2: a small worry, then teamwork.
    world.para()
    world.say(
        f"{hero_name} wanted to help right away, yet {hero_name.lower()} worried the work might take too long before sleep."
    )
    world.say(
        f"{mom1.label_word.capitalize()} smiled and said they could share the job, one step at a time."
    )
    world.say(
        f"{mom2.label_word.capitalize()} picked up {tool.label} and showed {hero_name} how to begin."
    )
    _help_each_other(world, child, mom1, mom2, task)
    _do_task(world, child, task)

    # Act 3: soft ending.
    world.para()
    world.say(
        f"Together they did the {task.gerund} and the little orchard felt peaceful."
    )
    world.say(
        f"{task.result.capitalize()}, and {hero_name} felt proud to have helped."
    )
    world.say(
        f"Then the three of them looked at the quiet trees, happy, calm, and ready for bedtime."
    )

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    task: Task = f["task"]
    tool: Tool = f["tool"]
    return [
        f'Write a gentle bedtime story set in an orchard where a calm child helps with "{task.keyword}" using "{tool.label}".',
        f"Tell a child-friendly story about teamwork in the orchard, with {child.id} and two loving mothers finishing a small job before sleep.",
        f'Write a soft story that includes the words "calm" and "teamwork" and ends with a peaceful orchard bedtime image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    task: Task = f["task"]
    tool: Tool = f["tool"]
    p1: Entity = f["parent1"]
    p2: Entity = f["parent2"]

    return [
        QAItem(
            question=f"Where did {child.id} help the family at bedtime?",
            answer=f"{child.id} helped in the orchard, where the trees were quiet and the night felt calm.",
        ),
        QAItem(
            question=f"What did {child.id} and the two mothers work on together?",
            answer=f"They worked on {task.verb}, using {tool.phrase} to make the job easier.",
        ),
        QAItem(
            question=f"Why did the story feel calm instead of rushed?",
            answer=(
                f"It felt calm because {p1.label_word} and {p2.label_word} shared the work, "
                f"and {child.id} could help one step at a time without any hurry."
            ),
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt proud and cozy, because the orchard task was done and bedtime could begin.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchard?",
            answer="An orchard is a place where fruit trees grow, often with apples or other fruit.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and share the work so a job gets done together.",
        ),
        QAItem(
            question="Why are lamps useful at bedtime outside?",
            answer="Lamps give a soft light so people can walk safely when the evening gets dark.",
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(orchar d).
task(collect_apples).
task(hang_lamps).
task(stack_crates).

needs_tool(collect_apples).
needs_tool(hang_lamps).
needs_tool(stack_crates).

tool(basket).
tool(lantern).
tool(crate_gloves).

helps(basket, collect_apples).
helps(lantern, hang_lamps).
helps(crate_gloves, stack_crates).

valid(Place, Task) :- place(Place), task(Task), needs_tool(Task), tool(T), helps(T, Task).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for task in TASKS.values():
        lines.append(asp.fact("task", task.id))
        if task_needs_tool(task):
            lines.append(asp.fact("needs_tool", task.id))
    for tool in TOOLS.values():
        lines.append(asp.fact("tool", tool.id))
        for t in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Calm orchard bedtime story world with teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent1")
    ap.add_argument("--parent2")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.task and (args.place, args.task) not in combos:
        raise StoryError("That orchard task does not have a reasonable tool-based version.")

    choices = [c for c in combos if (args.place is None or c[0] == args.place) and (args.task is None or c[1] == args.task)]
    if not choices:
        raise StoryError("No valid story matches those options.")

    place, task_id = rng.choice(choices)
    task = TASKS[task_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent1 = args.parent1 or "Mama"
    parent2 = args.parent2 or "Mommy"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, name=name, gender=gender, parent1=parent1, parent2=parent2, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TASKS[params.task],
        params.name,
        params.gender,
        params.parent1,
        params.parent2,
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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


def explain_rejection() -> str:
    return "No story: this orchard bedtime world needs a task that a tool can help with."


CURATED = [
    StoryParams(place="orchard", task="collect_apples", name="Lina", gender="girl", parent1="Mama", parent2="Mommy", trait="calm"),
    StoryParams(place="orchard", task="hang_lamps", name="Owen", gender="boy", parent1="Mama", parent2="Mommy", trait="gentle"),
    StoryParams(place="orchard", task="stack_crates", name="Nia", gender="girl", parent1="Mama", parent2="Mommy", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, task in combos:
            print(f"  {place:10} {task}")
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
            i += 1
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
            header = f"### {p.name}: {p.task} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
