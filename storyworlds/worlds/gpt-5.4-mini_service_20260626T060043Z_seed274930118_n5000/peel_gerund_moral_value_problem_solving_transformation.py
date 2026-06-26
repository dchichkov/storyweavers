#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/peel_gerund_moral_value_problem_solving_transformation.py
======================================================================================================

A small rhyming storyworld about peeling fruit, making a kind choice, solving a
snack-time problem, and transforming a messy moment into a shared treat.

Seed tale premise:
---
A child wants to peel fruit by themself. The peel tears, the fruit slips, and a
friend looks disappointed. The child learns to slow down, ask for help, share
the snack, and turn the problem into a sweet little picnic.

World model:
---
- physical meters: slipperiness, bruise, tidiness, peel_intact, snack_ready
- emotional memes: pride, worry, kindness, shame, relief, joy, gratitude

Story shape:
---
1. Setup: a child loves peeling fruit.
2. Problem: the peel tears or the fruit slips, making a mess and upsetting a friend.
3. Turn: the child chooses a moral value, asks for help, and solves the problem.
4. Transformation: the fruit becomes a neat snack and the mood becomes warm and kind.
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
class Fruit:
    id: str
    label: str
    color: str
    peel_color: str
    peel_word: str
    taste: str
    needs_help: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"slipperiness": 0.0, "bruise": 0.0, "tidiness": 0.0, "peel_intact": 1.0, "snack_ready": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"pride": 0.0, "worry": 0.0, "kindness": 0.0, "shame": 0.0, "relief": 0.0, "joy": 0.0, "gratitude": 0.0})


@dataclass
class Character:
    id: str
    type: str
    label: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"mess": 0.0, "skill": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"pride": 0.0, "worry": 0.0, "kindness": 0.0, "shame": 0.0, "relief": 0.0, "joy": 0.0, "gratitude": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the sunny kitchen"
    mood: str = "bright"
    affords: set[str] = field(default_factory=lambda: {"peel"})


@dataclass
class StoryParams:
    place: str
    fruit: str
    child: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[getattr(ent, "id")] = ent
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


FRUITS = {
    "banana": Fruit("banana", "banana", "yellow", "golden", "peel", "sweet"),
    "orange": Fruit("orange", "orange", "orange", "bright", "skin", "citrusy"),
    "pear": Fruit("pear", "pear", "green", "green", "skin", "juicy"),
}

SETTINGS = {
    "kitchen": Setting("the sunny kitchen", "bright"),
    "picnic": Setting("the park picnic blanket", "breezy"),
}

CHILDREN = ["Mina", "Noah", "Luna", "Iris", "Theo", "Sage"]
HELPERS = ["Mom", "Dad", "Aunt Jo", "Grandpa", "Brother Ben", "Sister May"]

TRAITS = ["gentle", "curious", "careful", "sprightly", "kind"]


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def introduce(world: World, child: Character, fruit: Fruit) -> None:
    world.say(
        f"{child.label} was a {random.choice(TRAITS)} child who loved to peel a {fruit.label} with skill and zeal."
    )
    world.say(
        f"In {world.setting.place}, the air felt light, and snack time promised a happy bite."
    )


def start_problem(world: World, child: Character, helper: Character, fruit: Fruit) -> None:
    child.memes["pride"] += 1
    fruit.meters["slipperiness"] = 1.0
    fruit.meters["peel_intact"] = 1.0
    world.say(
        f"{child.label} grabbed the fruit and tried to peel it fast, but the shiny skin was made to last."
    )
    world.say(
        f"The peel tore crooked; the fruit slipped low, and a sticky spot began to show."
    )
    child.meters["mess"] += 1
    child.memes["worry"] += 1
    fruit.meters["bruise"] += 1.0
    helper.memes["worry"] += 1
    world.facts["problem"] = "slip_and_tear"


def moral_turn(world: World, child: Character, helper: Character, fruit: Fruit) -> None:
    child.memes["kindness"] += 1
    child.memes["shame"] += 1
    world.say(
        f"{child.label} took a breath and slowed the pace, then chose a kinder, steadier face."
    )
    world.say(
        f'"Please help me," {child.label} said with care. "I want to share this snack with you there."'
    )
    helper.memes["relief"] += 1
    helper.memes["kindness"] += 1
    child.meters["skill"] += 1
    world.facts["moral_value"] = "kindness"


def solve_problem(world: World, child: Character, helper: Character, fruit: Fruit) -> None:
    world.say(
        f"{helper.label} showed how to hold the fruit just right, and the peel came off in a soft, smooth stripe."
    )
    fruit.meters["peel_intact"] = 0.0
    fruit.meters["snack_ready"] = 1.0
    fruit.meters["tidiness"] = 1.0
    child.meters["mess"] = max(0.0, child.meters["mess"] - 1.0)
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["gratitude"] += 1
    world.say(
        f"They wiped the juice, shared the slices, and turned the trouble into a tidy prize."
    )
    world.say(
        f"The little spill was soon made neat, and the snack smelled sweet as a summer treat."
    )
    world.facts["solution"] = "ask_for_help_and_share"
    world.facts["transformation"] = "mess_to_shared_snack"


def end_image(world: World, child: Character, helper: Character, fruit: Fruit) -> None:
    world.say(
        f"By the end, {child.label} was smiling wide, with {helper.label} beside {child.pronoun('object')} and fruit to share inside."
    )
    world.say(
        f"The peel was gone, the plate was clean, and kindness made the whole day gleam."
    )


def tell(setting: Setting, fruit: Fruit, child_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Character(child_name, "child", child_name, "peeler"))
    helper = world.add(Character(helper_name, "helper", helper_name, "guide"))
    fr = world.add(fruit)

    introduce(world, child, fr)
    world.para()
    start_problem(world, child, helper, fr)
    moral_turn(world, child, helper, fr)
    world.para()
    solve_problem(world, child, helper, fr)
    end_image(world, child, helper, fr)

    world.facts.update(child=child, helper=helper, fruit=fr, setting=setting)
    return world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for fruit in FRUITS:
            out.append((place, fruit))
    return out


@dataclass
class Registry:
    place: str
    fruit: str
    child: str
    helper: str


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about peeling fruit, kindness, and repair.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
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
    if args.place and args.fruit and (args.place, args.fruit) not in valid_combos():
        raise StoryError("That place and fruit do not make a reasonable peeling story.")
    place = args.place or rng.choice(list(SETTINGS))
    fruit = args.fruit or rng.choice(list(FRUITS))
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, fruit=fruit, child=child, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a small child about "{f["fruit"].label}" peeling, a kind choice, and a tidy ending.',
        f'Tell a gentle story where {f["child"].label} tries to peel a {f["fruit"].label}, makes a little mess, and learns to ask {f["helper"].label} for help.',
        f'Write a moral-value story with problem solving and transformation about peeling fruit in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    fruit = world.facts["fruit"]
    return [
        QAItem(
            question=f"What did {child.label} want to do at first?",
            answer=f"{child.label} wanted to peel the {fruit.label} by {child.pronoun('object')}self."
        ),
        QAItem(
            question=f"What problem happened when {child.label} tried too fast?",
            answer=f"The peel tore and the fruit slipped, so a sticky little mess appeared."
        ),
        QAItem(
            question=f"What kind choice helped fix the problem?",
            answer=f"{child.label} slowed down, asked {helper.label} for help, and shared the snack."
        ),
        QAItem(
            question=f"How did the fruit change by the end?",
            answer=f"The fruit became a neat, ready-to-eat snack, and the mood changed from worry to joy."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    fruit = world.facts["fruit"]
    return [
        QAItem(
            question="What does a peel do?",
            answer="A peel is the outside skin of some fruits. People take it off before eating the fruit inside."
        ),
        QAItem(
            question="Why is it helpful to ask for help when something is tricky?",
            answer="Asking for help can make a hard job safer, easier, and kinder when you are still learning."
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is when something changes into a new form or a new kind of situation."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = getattr(ent, "meters", {})
        memes = getattr(ent, "memes", {})
        lines.append(f"  {ent.id}: meters={ {k:v for k,v in meters.items() if v} } memes={ {k:v for k,v in memes.items() if v} }")
    return "\n".join(lines)


ASP_RULES = r"""
place(kitchen).
place(picnic).

fruit(banana).
fruit(orange).
fruit(pear).

moral_value(kindness).
problem(slip_and_tear).
transformation(mess_to_shared_snack).

compatible(P, F) :- place(P), fruit(F).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for f in FRUITS:
        lines.append(asp.fact("fruit", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - ac:
        print("only in python:", sorted(py - ac))
    if ac - py:
        print("only in clingo:", sorted(ac - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], FRUITS[params.fruit], params.child, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place, fruit in valid_combos():
            params = StoryParams(place=place, fruit=fruit, child=CHILDREN[0], helper=HELPERS[0])
            samples.append(generate(params))
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
