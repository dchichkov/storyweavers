#!/usr/bin/env python3
"""
prove_puller_bravery_folk_tale.py
=================================

A small folk-tale story world about a puller who must prove bravery.

Seed inspiration:
- a timid helper is asked to pull something difficult
- a feared sound, place, or creature makes the task feel impossible
- the helper finds courage, proves bravery, and earns a warm ending
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
class Person:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    worn_by: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class RopeTask:
    id: str
    label: str
    verb: str
    object_label: str
    risk: str
    prove_phrase: str
    reward: str
    needed_bravery: float = 1.0


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


TASKS = {
    "pull_well_bucket": RopeTask(
        id="pull_well_bucket",
        label="the well bucket",
        verb="pull up the well bucket",
        object_label="bucket",
        risk="the dark well yawned below",
        prove_phrase="prove their bravery",
        reward="cool water for the village",
        needed_bravery=1.0,
    ),
    "pull_gate_chain": RopeTask(
        id="pull_gate_chain",
        label="the iron gate",
        verb="pull open the old gate",
        object_label="gate",
        risk="the gate groaned like a grumpy giant",
        prove_phrase="show their brave heart",
        reward="the path to the hill",
        needed_bravery=1.0,
    ),
    "pull_cart_hill": RopeTask(
        id="pull_cart_hill",
        label="the trader's cart",
        verb="pull the cart up the hill",
        object_label="cart",
        risk="the hill was steep and long",
        prove_phrase="prove they were brave enough",
        reward="the cart of apples for the market",
        needed_bravery=1.0,
    ),
}

PLACES = {
    "well": Place(id="well", label="the village well"),
    "gate": Place(id="gate", label="the old gate"),
    "hill": Place(id="hill", label="the hill road"),
}

NAMES = ["Mira", "Bram", "Tessa", "Lio", "Anya", "Pell", "Nell", "Robin"]
TRAITS = ["small", "kind", "quiet", "swift", "earnest", "gentle"]


def reasonableness_gate(place: str, task: str) -> None:
    if place not in PLACES:
        raise StoryError("The place must be one of the known folk-tale places.")
    if task not in TASKS:
        raise StoryError("The task must be one of the known puller tasks.")


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("label", pid, place.label))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("needs_bravery", tid, int(task.needed_bravery)))
    return "\n".join(lines)


ASP_RULES = r"""
required(T) :- task(T), needs_bravery(T, N), N >= 1.
valid(T) :- required(T).
#show valid/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_tasks() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((t,) for t in TASKS)
    cl = asp_valid_tasks()
    if py == cl:
        print(f"OK: clingo gate matches Python reasonableness ({len(py)} tasks).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python:", py)
    print("clingo:", cl)
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    reasonableness_gate(args.place or "well", args.task or "pull_well_bucket")
    place = args.place or rng.choice(list(PLACES))
    task = args.task or rng.choice(list(TASKS))
    return StoryParams(
        place=place,
        task=task,
        name=args.name or rng.choice(NAMES),
        seed=None,
    )


def _intro(world: World, hero: Person, task: RopeTask) -> None:
    world.say(
        f"{hero.name_word()} was a {hero.traits[0]} little puller who lived near {world.place.label}."
    )
    world.say(
        f"Each morning, {hero.pronoun('subject')} wanted to {task.verb}, because {task.reward} mattered to everyone."
    )


def _tension(world: World, hero: Person, task: RopeTask) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.para()
    world.say(
        f"One day, the village needed help, but {task.risk}. {hero.name_word()} looked at the rope and swallowed hard."
    )
    world.say(
        f'"I want to help," {hero.pronoun("subject")} whispered, "but I do not know if I can {task.prove_phrase}."'
    )


def _turn(world: World, hero: Person, task: RopeTask) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    hero.meters["effort"] = hero.meters.get("effort", 0.0) + 1.0
    world.para()
    world.say(
        f"Then {hero.name_word()} took a breath, planted {hero.pronoun('possessive')} feet, and held the rope with both hands."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} pulled and pulled, slow as a steady song, until the task began to move."
    )


def _resolution(world: World, hero: Person, task: RopeTask) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.para()
    world.say(
        f"At last, {hero.name_word()} {task.verb}, and the village cheered."
    )
    world.say(
        f"That day, everyone saw that {hero.name_word()} had truly proven bravery, and {task.reward} was safely won."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    world = World(place)
    hero = world.add(Person(id=params.name, label=params.name, traits=["little", rng_trait(params.name)]))
    world.facts["hero"] = hero
    world.facts["task"] = task
    world.facts["place"] = place
    _intro(world, hero, task)
    _tension(world, hero, task)
    _turn(world, hero, task)
    _resolution(world, hero, task)
    return world


def rng_trait(name: str) -> str:
    return TRAITS[sum(ord(c) for c in name) % len(TRAITS)]


def generation_prompts(world: World) -> list[str]:
    hero: Person = world.facts["hero"]
    task: RopeTask = world.facts["task"]
    place: Place = world.facts["place"]
    return [
        f"Write a short folk tale about {hero.name_word()} at {place.label} who must {task.verb} and prove bravery.",
        f"Tell a gentle story where a small puller faces {task.risk} before helping the village.",
        f"Create a child-friendly tale with the words 'prove' and 'puller' about a brave helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Person = world.facts["hero"]
    task: RopeTask = world.facts["task"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.name_word()}, a little puller who lived near {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.name_word()} need to do?",
            answer=f"{hero.name_word()} needed to {task.verb} for the village.",
        ),
        QAItem(
            question=f"How did {hero.name_word()} finish the hard moment?",
            answer=f"{hero.name_word()} took a breath, pulled steadily, and proved bravery by finishing the task.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be brave?",
            answer="Being brave means doing something hard or scary even when you feel worried.",
        ),
        QAItem(
            question="What is a puller?",
            answer="A puller is someone or something that pulls with force, like with a rope or a cart.",
        ),
        QAItem(
            question="Why do people cheer when someone helps?",
            answer="People cheer because helping makes a hard job easier and shows a kind heart.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about a puller proving bravery.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--task", choices=list(TASKS))
    ap.add_argument("--name")
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
        print(format_qa(sample))


CURATED = [
    StoryParams(place="well", task="pull_well_bucket", name="Mira"),
    StoryParams(place="gate", task="pull_gate_chain", name="Bram"),
    StoryParams(place="hill", task="pull_cart_hill", name="Tessa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t[0]}" for t in asp_valid_tasks()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
