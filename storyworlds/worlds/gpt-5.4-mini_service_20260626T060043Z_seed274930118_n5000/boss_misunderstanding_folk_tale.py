#!/usr/bin/env python3
"""
A tiny folk-tale storyworld about a boss, a misunderstanding, and a gentle
turn toward clarity.

This world models a small workday domain in which a boss and a helper share a
task, a misunderstanding grows from incomplete signs, and the ending resolves
through an explained action, a kind correction, or a simple proof.
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
    kind: str = "thing"  # "character" | "thing"
    role: str = ""
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.role in {"boss", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.role in {"woman", "mother", "woman-boss"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.role or self.id

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Task:
    id: str
    label: str
    signs: list[str]
    true_meaning: str
    misunderstood_as: str
    requires: str
    keywords: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    boss: Entity
    worker: Entity
    item: Entity
    task: Task
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_trace(self, text: str) -> None:
        self.trace.append(text)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hall": Place(id="hall", label="the village hall"),
    "market": Place(id="market", label="the market square"),
    "stable": Place(id="stable", label="the old stable"),
}

TASKS = {
    "bells": Task(
        id="bells",
        label="ring the bells",
        signs=["a bundle of rope", "a brass bell", "a wooden beam"],
        true_meaning="to call everyone together",
        misunderstood_as="to steal the bell",
        requires="rope",
        keywords={"bell", "rope", "call"},
    ),
    "bread": Task(
        id="bread",
        label="carry the bread",
        signs=["warm loaves", "a cloth basket", "flour on the sleeves"],
        true_meaning="to bring bread to the poor folk",
        misunderstood_as="to hide the bread for himself",
        requires="basket",
        keywords={"bread", "basket", "flour"},
    ),
    "lantern": Task(
        id="lantern",
        label="light the lantern",
        signs=["a wick", "oil in a jug", "a lantern hook"],
        true_meaning="to guide travelers home",
        misunderstood_as="to set the barn alight",
        requires="oil",
        keywords={"lantern", "oil", "light"},
    ),
}

BOSS_NAMES = ["Marta", "Edwin", "Rosa", "Hugh", "Nora"]
WORKER_NAMES = ["Jory", "Pip", "Mina", "Tobin", "Lena"]
TRAITS = ["careful", "cheerful", "busy", "quiet", "earnest"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    boss_name: str
    worker_name: str
    boss_role: str
    worker_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TASKS]


def reasonableness_error(place: str, task: str) -> str:
    return (
        f"(No story: the task {task!r} cannot be told at {place!r} in this small folk-tale world.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]

    boss = Entity(id=params.boss_name, kind="character", role=params.boss_role, label="boss")
    worker = Entity(id=params.worker_name, kind="character", role="worker", label="helper")
    item = Entity(id="item", kind="thing", label=task.signs[0], owner=worker.id)

    world = World(place=place, boss=boss, worker=worker, item=item, task=task)
    world.facts.update(place=place, task=task, boss=boss, worker=worker, item=item)

    # Setup
    world.say(
        f"In {place.label}, there lived a boss named {boss.id} and a helper named {worker.id}."
    )
    world.say(
        f"One day, {worker.id} was sent to {task.label}, and {worker.id} carried {task.signs[1]} and {task.signs[2]}."
    )
    world.say(
        f"{boss.id} meant {task.true_meaning}, but the signs looked like {task.misunderstood_as}."
    )

    # Turn
    world.para()
    boss.memes["worry"] = 1
    worker.memes["confusion"] = 1
    world.say(
        f"When {boss.id} saw the rope and the bell, {boss.pronoun('subject').capitalize()} frowned."
    )
    world.say(
        f'"Why are you holding those things?" {boss.id} asked. "It looks like you mean {task.misunderstood_as}."'
    )
    world.say(
        f"{worker.id} blinked, for {worker.pronoun('subject')} had only meant {task.true_meaning}."
    )

    # Resolution
    world.para()
    worker.memes["resolve"] = 1
    boss.memes["understanding"] = 1
    world.say(
        f"Then {worker.id} laid out the signs one by one and explained the work as plain as bread."
    )
    world.say(
        f"{boss.id} listened, and the worry left {boss.pronoun('possessive')} face."
    )
    world.say(
        f'"Ah," said {boss.id}, "I mistook the sign for the deed."'
    )
    world.say(
        f"So {worker.id} did the task at once, and soon the whole place knew the truth of it."
    )

    world.facts.update(misunderstanding=True, resolved=True)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    t = world.facts["task"]
    return [
        f"Write a short folk tale about a boss and a helper where {t.label} is misunderstood.",
        f"Tell a gentle story in which signs of {t.label} look suspicious at first, but the truth is kinder.",
        f"Compose a simple folk tale about a boss who learns not to judge the work by the first look.",
    ]


def story_qa(world: World) -> list[QAItem]:
    boss = world.facts["boss"]
    worker = world.facts["worker"]
    task = world.facts["task"]
    place = world.facts["place"].label

    return [
        QAItem(
            question=f"Who was the boss in the story at {place}?",
            answer=f"The boss was {boss.id}, and {worker.id} was the helper.",
        ),
        QAItem(
            question=f"What task did {worker.id} do that caused the misunderstanding?",
            answer=f"{worker.id} was doing {task.label}, and the signs looked like {task.misunderstood_as}.",
        ),
        QAItem(
            question=f"Why did {boss.id} get worried?",
            answer=f"{boss.id} got worried because the signs made the work look like {task.misunderstood_as}, even though it really meant {task.true_meaning}.",
        ),
        QAItem(
            question=f"How was the misunderstanding fixed?",
            answer=f"{worker.id} explained the signs plainly, and then {boss.id} understood the real meaning.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    task = world.facts["task"]
    out = [
        QAItem(
            question="What is a boss?",
            answer="A boss is a person who leads work or helps guide a group toward a job being done.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a sign, word, or action means one thing, but it really means another.",
        ),
    ]
    if "bell" in task.keywords:
        out.append(
            QAItem(
                question="What is a bell used for?",
                answer="A bell is often used to make a clear sound that can call people together or signal a message.",
            )
        )
    if "bread" in task.keywords:
        out.append(
            QAItem(
                question="Why do people carry bread in a basket?",
                answer="A basket helps hold bread safely so the loaves do not get crushed or dropped.",
            )
        )
    if "lantern" in task.keywords:
        out.append(
            QAItem(
                question="What does a lantern do?",
                answer="A lantern gives light, so people can see the way in the dark.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place: {world.place.label}")
    lines.append(f"boss: {world.boss.id} memes={world.boss.memes}")
    lines.append(f"worker: {world.worker.id} memes={world.worker.memes}")
    lines.append(f"task: {world.task.id} / {world.task.label}")
    lines.append(f"item: {world.item.label}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.
#show misunderstanding/3.

misunderstanding(P, T, B) :- place(P), task(T), boss(B), signlook(T).
valid_story(P, T, B) :- misunderstanding(P, T, B), has_fix(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("signlook", tid))
        lines.append(asp.fact("has_fix", tid))
        for kw in sorted(task.keywords):
            lines.append(asp.fact("keyword", tid, kw))
    for name in BOSS_NAMES:
        lines.append(asp.fact("boss", name.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set((p, t) for (p, t, _) in asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale storyworld about a boss and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--boss-name")
    ap.add_argument("--worker-name")
    ap.add_argument("--boss-role", default="boss")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.task and (args.place, args.task) not in valid_combos():
        raise StoryError(reasonableness_error(args.place, args.task))

    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, task = rng.choice(combos)
    return StoryParams(
        place=place,
        task=task,
        boss_name=args.boss_name or rng.choice(BOSS_NAMES),
        worker_name=args.worker_name or rng.choice(WORKER_NAMES),
        boss_role=args.boss_role,
        worker_trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story seeds:\n")
        for p, t, b in combos:
            print(f"  {p:10} {t:10} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="hall", task="bells", boss_name="Marta", worker_name="Jory", boss_role="boss", worker_trait="earnest"),
            StoryParams(place="market", task="bread", boss_name="Rosa", worker_name="Mina", boss_role="boss", worker_trait="careful"),
            StoryParams(place="stable", task="lantern", boss_name="Edwin", worker_name="Tobin", boss_role="boss", worker_trait="quiet"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
