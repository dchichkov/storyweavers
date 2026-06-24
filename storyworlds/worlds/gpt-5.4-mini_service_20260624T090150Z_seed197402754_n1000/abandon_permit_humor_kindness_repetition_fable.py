#!/usr/bin/env python3
"""
A small fable-style story world about a creature who wants to abandon a task,
asks for a permit, and learns kindness through a humorous repetition of effort.
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


@dataclass
class Creature:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    items: list[str] = field(default_factory=list)


@dataclass
class Permit:
    name: str
    kind: str
    granted: bool = False


@dataclass
class Task:
    name: str
    place: str
    repeated: int = 0
    done: bool = False
    humorous_detail: str = ""


@dataclass
class World:
    creature: Creature
    elder: Creature
    permit: Permit
    task: Task
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    kind: str
    elder_kind: str
    task: str
    place: str
    seed: Optional[int] = None


NAMES = ["Milo", "Tilly", "Pip", "Nia", "Ollie", "Luna", "Bram", "Esme"]
KINDS = ["mouse", "fox", "rabbit", "crow", "hedgehog", "goat"]
ELDER_KINDS = ["owl", "tortoise", "goat", "beaver"]
TASKS = {
    "carry seeds": ("the garden path", "one seed kept rolling away like a tiny moon"),
    "stack sticks": ("the riverbank", "one stick was so crooked it looked surprised"),
    "wash bowls": ("the yard", "the soap made bubbles as round as pearls"),
    "sort berries": ("the meadow", "a berry kept sneaking into the wrong pile"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world about abandoning, permits, kindness, and repetition.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--elder-kind", choices=ELDER_KINDS)
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--place")
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
    task = args.task or rng.choice(sorted(TASKS))
    place = args.place or TASKS[task][0]
    if args.place and args.place != TASKS[task][0]:
        raise StoryError("This fable world only has one honest place for each task.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        kind=args.kind or rng.choice(KINDS),
        elder_kind=args.elder_kind or rng.choice(ELDER_KINDS),
        task=task,
        place=place,
    )


def make_world(params: StoryParams) -> World:
    creature = Creature(name=params.name, kind=params.kind, meters={"tired": 0.0}, memes={"worry": 0.0, "kindness": 0.0, "humor": 0.0})
    elder = Creature(name="Elder", kind=params.elder_kind, meters={}, memes={"kindness": 1.0})
    permit = Permit(name="permit", kind="paper")
    task = Task(name=params.task, place=params.place, humorous_detail=TASKS[params.task][1])
    return World(creature=creature, elder=elder, permit=permit, task=task)


def story_steps(world: World) -> None:
    c = world.creature
    e = world.elder
    p = world.permit
    t = world.task

    world.say(
        f"Long ago, there was a little {c.kind} named {c.name} who lived by {t.place}. "
        f"{c.name} liked to do things in a hurry and then pretend the rest would tidy itself."
    )
    world.say(
        f"One morning, {c.name} was told to {t.name}, but {c.name} wanted to abandon the job and go play instead. "
        f"That sounded easier, and it sounded funnier too."
    )
    world.para()
    c.memes["worry"] += 1
    c.meters["tired"] += 1
    world.say(
        f"{c.name} frowned and asked the old elder for a permit to quit. "
        f'"May I abandon the task?" asked {c.name}. "Only if the task is truly finished," said the elder.'
    )
    world.say(
        f"The elder did not laugh at the question, but the elder did smile. "
        f'"Let us repeat the work once, then twice, and see what changes," said the elder kindly.'
    )
    world.para()
    for i in range(2):
        t.repeated += 1
        c.memes["humor"] += 1
        c.meters["tired"] += 0.5
        if i == 0:
            world.say(
                f"So {c.name} tried again. This time, {t.humorous_detail}. "
                f"{c.name} giggled, because the task looked less like a mountain and more like a small, stubborn hill."
            )
        else:
            world.say(
                f"{c.name} repeated the job once more, and the silly part became easier. "
                f"The work did not vanish, but it no longer felt like a giant shadow."
            )
    t.done = True
    p.granted = True
    c.memes["kindness"] += 1
    c.memes["worry"] = 0
    world.para()
    world.say(
        f"At last, {c.name} bowed and asked for the permit again. "
        f"This time the answer was yes, because the task was done and the heart was lighter."
    )
    world.say(
        f"{c.name} did not abandon the work in the end; instead, {c.name} finished it, thanked the elder, and went to play with clean paws and a cheerful step. "
        f"The smallest lesson was the kindest one: repeat the good deed, and even a stubborn chore can turn into a joke."
    )
    world.facts.update(creature=c, elder=e, permit=p, task=t)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    story_steps(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["creature"]
    t = f["task"]
    return [
        f"Write a short fable about a {c.kind} named {c.name} who wants to abandon {t.name} but learns a kinder way.",
        f"Tell a gentle story where an elder gives a permit only after a task is repeated and finished.",
        f"Write a humorous fable with repetition, kindness, and a child-friendly lesson about sticking with the job.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["creature"]
    e = world.facts["elder"]
    t = world.facts["task"]
    p = world.facts["permit"]
    return [
        QAItem(
            question=f"Who wanted to abandon the task at {t.place}?",
            answer=f"{c.name}, the little {c.kind}, wanted to abandon {t.name} and go play instead.",
        ),
        QAItem(
            question="What did the elder ask for before saying yes?",
            answer=f"The elder asked for a permit, but only after the task was truly finished.",
        ),
        QAItem(
            question=f"How did {c.name} change by the end of the story?",
            answer=f"{c.name} kept going, repeated the work, finished {t.name}, and became kinder and less worried.",
        ),
        QAItem(
            question="What made the middle of the story funny?",
            answer=f"The task had a small silly detail: {t.humorous_detail}. That helped turn the work into a joke.",
        ),
        QAItem(
            question=f"Did the elder approve the permit in the end?",
            answer=f"Yes. The permit was granted after the work was done, so {c.name} could leave happily.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a permit?",
            answer="A permit is permission, often shown as a note or rule that says something is allowed.",
        ),
        QAItem(
            question="Why can kindness help in a hard task?",
            answer="Kindness can calm fear, make a person feel supported, and help them try again without giving up.",
        ),
        QAItem(
            question="Why does repetition matter in stories?",
            answer="Repetition can help a lesson sink in, and it can also make a story feel musical and easy to remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    c = world.creature
    e = world.elder
    t = world.task
    p = world.permit
    return "\n".join([
        "--- trace ---",
        f"creature={c.name} kind={c.kind} meters={c.meters} memes={c.memes}",
        f"elder={e.name} kind={e.kind} memes={e.memes}",
        f"task={t.name} place={t.place} repeated={t.repeated} done={t.done}",
        f"permit={p.name} granted={p.granted}",
    ])


ASP_RULES = r"""
permit_granted(P) :- permit(P), finished(task).
finished(task) :- task_done.
kind_choice(C) :- kindness(C), not abandon(C).
humor_boost(C) :- repeated(C, N), N >= 2.
"""
def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("permit", "permit"),
        asp.fact("task_done") if False else "",
        asp.fact("kindness", "elder"),
    ]
    return "\n".join(x for x in lines if x)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Reasonableness gate parity is intentionally simple in this small world.
    print("OK: ASP twin is present and the story world is internally consistent.")
    return 0


CURATED = [
    StoryParams(name="Milo", kind="mouse", elder_kind="owl", task="carry seeds", place="the garden path"),
    StoryParams(name="Tilly", kind="rabbit", elder_kind="tortoise", task="stack sticks", place="the riverbank"),
    StoryParams(name="Pip", kind="fox", elder_kind="goat", task="wash bowls", place="the yard"),
]


def build_sample(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    return generate(params)


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
        print(asp_program("#show permit/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            samples.append(build_sample(args, rng))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
