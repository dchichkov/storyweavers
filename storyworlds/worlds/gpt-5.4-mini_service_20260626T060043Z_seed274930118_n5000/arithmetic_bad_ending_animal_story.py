#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/arithmetic_bad_ending_animal_story.py
===============================================================================================================

A small animal storyworld about arithmetic practice, a tempting count, and a bad ending.

Premise:
- A young animal wants to do simple arithmetic with small objects.
- A rule, tool, or pile makes the count matter.

Turn:
- The animal guesses wrong, forgets something, or chooses a bad method.
- The world state changes in a way that causes a loss or disappointment.

Resolution:
- There is no cheerful fix; the ending image shows the consequence.

This world is intentionally close to Animal Story: child-facing animals, concrete objects,
simple actions, and narrated feelings. It uses arithmetic as the central mechanism and
supports bad-ending variants that remain plausible and state-driven.
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
class Entity:
    id: str
    kind: str = "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.kind == "character":
            if self.species in {"cat", "lion", "tiger", "fox", "wolf", "bear", "rabbit", "mouse"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affordance: str
    countable: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    count: int
    fragile: bool = False


@dataclass
class StoryParams:
    place: str
    animal: str
    task: str
    item: str
    number: int
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


PLACES = {
    "table": Place(name="the kitchen table", affordance="counting", countable="buttons"),
    "barn": Place(name="the red barn floor", affordance="sorting", countable="apples"),
    "patch": Place(name="the garden patch", affordance="gathering", countable="pebbles"),
}

ANIMALS = {
    "cat": ("cat", "curious"),
    "rabbit": ("rabbit", "busy"),
    "fox": ("fox", "proud"),
    "mouse": ("mouse", "tiny"),
    "bear": ("bear", "serious"),
}

TASKS = {
    "add": {
        "verb": "add the little piles together",
        "gerund": "adding the little piles",
        "ask": "how many there would be after adding",
        "mistake": "added the wrong piles",
        "feel": "gleeful",
    },
    "take": {
        "verb": "take some away",
        "gerund": "taking some away",
        "ask": "how many would be left after taking some away",
        "mistake": "took away too many",
        "feel": "careful",
    },
    "share": {
        "verb": "share them into equal groups",
        "gerund": "sharing them into equal groups",
        "ask": "how many each animal would get",
        "mistake": "made one pile too small",
        "feel": "hopeful",
    },
}

ITEMS = {
    "buttons": Item(id="buttons", label="buttons", phrase="a little bowl of buttons", count=6, fragile=False),
    "apples": Item(id="apples", label="apples", phrase="a basket of apples", count=7, fragile=True),
    "pebbles": Item(id="pebbles", label="pebbles", phrase="a jar of pebbles", count=8, fragile=False),
}

GREETINGS = {
    "cat": "a small cat with bright eyes",
    "rabbit": "a rabbit with quick paws",
    "fox": "a fox with a neat tail",
    "mouse": "a tiny mouse with a soft voice",
    "bear": "a bear with a slow, careful walk",
}


ASP_RULES = r"""
place(table). place(barn). place(patch).

animal(cat). animal(rabbit). animal(fox). animal(mouse). animal(bear).

task(add). task(take). task(share).

item(buttons). item(apples). item(pebbles).

can_do(table, add, buttons).
can_do(barn, take, apples).
can_do(patch, share, pebbles).

bad_end(P, A, T, I) :- can_do(P, T, I), animal(A), task(T), item(I), place(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    lines.extend([
        asp.fact("can_do", "table", "cat", "add", "buttons"),
        asp.fact("can_do", "barn", "rabbit", "take", "apples"),
        asp.fact("can_do", "patch", "fox", "share", "pebbles"),
        asp.fact("can_do", "table", "mouse", "add", "buttons"),
        asp.fact("can_do", "barn", "bear", "take", "apples"),
        asp.fact("can_do", "patch", "cat", "share", "pebbles"),
    ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_do/4."))
    asp_set = set(asp.atoms(model, "can_do"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, task, item in [
        ("table", "add", "buttons"),
        ("barn", "take", "apples"),
        ("patch", "share", "pebbles"),
        ("table", "add", "buttons"),
        ("barn", "take", "apples"),
        ("patch", "share", "pebbles"),
    ]:
        combos.append((place, ANIMAL_FOR_TASK(task), task, item))
    return sorted(set(combos))


def ANIMAL_FOR_TASK(task: str) -> str:
    return {"add": "cat", "take": "rabbit", "share": "fox"}[task]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with arithmetic and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=ITEMS)
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
    if args.task and args.place and args.item:
        if (args.place, args.task, args.item) not in {
            ("table", "add", "buttons"),
            ("barn", "take", "apples"),
            ("patch", "share", "pebbles"),
        }:
            raise StoryError("That animal and arithmetic task do not fit together in this world.")

    combos = [
        (p, a, t, i)
        for (p, a, t, i) in valid_combos()
        if (args.place is None or p == args.place)
        and (args.animal is None or a == args.animal)
        and (args.task is None or t == args.task)
        and (args.item is None or i == args.item)
    ]
    if not combos:
        raise StoryError("No valid arithmetic animal story matches the given options.")

    place, animal, task, item = rng.choice(combos)
    return StoryParams(place=place, animal=animal, task=task, item=item, number=rng.choice([2, 3]), seed=args.seed)


def _story_for(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    animal_species, trait = ANIMALS[params.animal]
    hero = world.add(Entity(id="hero", kind="character", species=animal_species, label=params.animal))
    box = world.add(Entity(id="item", kind="thing", label=ITEMS[params.item].label, phrase=ITEMS[params.item].phrase))
    task = TASKS[params.task]
    total = ITEMS[params.item].count
    number = params.number

    world.say(f"{GREETINGS[params.animal].capitalize()} named Pip liked to sit at {world.place.name} and do arithmetic.")
    world.say(f"Pip wanted to {task['verb']} with {box.phrase}, because counting felt nice and neat.")
    world.say(f"Pip asked, 'If I start with {number} and change the pile, how many will I have?'")
    world.para()

    if params.task == "add":
        world.say(f"Pip lined up {number} buttons, then tried to add more from the bowl.")
        world.say(f"But Pip {task['mistake']}, so the answer was wrong and the buttons rolled away.")
        lost = 1
        final = number + lost
        world.say(f"One button slipped under the table and could not be found, so the pile stayed at {final} instead of growing.")
        world.say("Pip's ears drooped, because the picture in the mind was not the picture on the floor.")
    elif params.task == "take":
        world.say(f"Pip counted {total} apples, then tried to take away {number}.")
        world.say(f"But Pip {task['mistake']}, and the basket tipped while the apples bumped across the floor.")
        final = max(0, total - (number + 2))
        world.say(f"When the rolling stopped, only {final} apples were left in the basket, and one had a bruise on its side.")
        world.say("Pip sat very still, because the counting game had turned into a mess.")
    else:
        group = 3
        world.say(f"Pip tried to share {total} pebbles into {group} equal groups.")
        world.say(f"But Pip {task['mistake']}, and one group got too few pebbles.")
        final = total // group
        world.say(f"The last pebble landed in the dirt, so one group had only {final} pebbles instead of a fair share.")
        world.say("Pip looked at the uneven piles and felt the sadness of a game gone wrong.")

    world.para()
    world.say(f"At the end, {hero.pronoun('subject').capitalize()} sat by the table with the {box.label}, quiet and unhappy.")
    world.facts.update(hero=hero, box=box, task=task, number=number, total=total, place=params.place, animal=params.animal)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short animal story about {f['animal']} arithmetic at {world.place.name}.",
        f"Tell a simple story where a {f['animal']} tries to {f['task']['verb']} and the plan ends badly.",
        f"Write a child-friendly story with counting, a mistake, and a sad ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        QAItem(
            question="Who was trying to do arithmetic in the story?",
            answer=f"A small {hero.species} named Pip was trying to do arithmetic at {world.place.name}.",
        ),
        QAItem(
            question="What did Pip want to do with the pile?",
            answer=f"Pip wanted to {f['task']['verb']} with the {f['box'].label}.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer="The arithmetic went wrong, so the count became a mess and Pip ended up sad instead of proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is arithmetic?",
            answer="Arithmetic is doing number work like adding, taking away, or sharing things fairly.",
        ),
        QAItem(
            question="What does it mean to add?",
            answer="To add means to put numbers together to make a bigger number.",
        ),
        QAItem(
            question="What does it mean to share equally?",
            answer="Sharing equally means giving each group the same amount.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} species={e.species} label={e.label}")
    lines.append(f"place={world.place.name}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="table", animal="cat", task="add", item="buttons", number=2),
    StoryParams(place="barn", animal="rabbit", task="take", item="apples", number=3),
    StoryParams(place="patch", animal="fox", task="share", item="pebbles", number=3),
]


def generate(params: StoryParams) -> StorySample:
    world = _story_for(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_do/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_do/4."))
        print(f"{len(asp.atoms(model, 'can_do'))} valid can_do facts:")
        for atom in sorted(set(asp.atoms(model, "can_do"))):
            print(atom)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
