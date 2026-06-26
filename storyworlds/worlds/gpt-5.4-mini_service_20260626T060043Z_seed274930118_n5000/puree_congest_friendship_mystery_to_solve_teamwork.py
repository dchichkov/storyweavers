#!/usr/bin/env python3
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

SETTING_REGISTRY = {
    "sunny_kitchen": {
        "place": "the sunny kitchen",
        "indoor": True,
        "affords": {"mixing", "searching", "sharing"},
    },
    "garden_table": {
        "place": "the garden table",
        "indoor": False,
        "affords": {"mixing", "searching", "sharing"},
    },
}

FRIENDS = ["Mina", "Toby", "Lila", "Noah", "Ruby", "Eli"]
HELPERS = ["grandma", "grandpa", "aunt", "uncle", "neighbor"]
TRAITS = ["kind", "curious", "gentle", "cheerful", "helpful"]

@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    helper: str
    trait: str
    seed: Optional[int] = None

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

class World:
    def __init__(self, setting: dict) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

@dataclass
class PureeTask:
    id: str
    ingredient: str
    reason: str
    action: str
    clue: str
    solved_with: str
    requires: str

TASKS = {
    "pear": PureeTask(
        id="pear",
        ingredient="pears",
        reason="to make something soft for a congested helper",
        action="puree the pears",
        clue="the spoon kept clicking against the side of the bowl",
        solved_with="a careful stir",
        requires="blender",
    ),
    "apple": PureeTask(
        id="apple",
        ingredient="apples",
        reason="to make a gentle snack for a stuffed-up helper",
        action="puree the apples",
        clue="the bowl was too full to mix well",
        solved_with="sharing the apples into two bowls",
        requires="extra bowl",
    ),
    "banana": PureeTask(
        id="banana",
        ingredient="bananas",
        reason="to make a smooth snack for a congested friend",
        action="puree the bananas",
        clue="the lid was on backwards",
        solved_with="turning the lid the right way",
        requires="lid",
    ),
}

ASP_RULES = r"""
setting(sunny_kitchen).
setting(garden_table).

task(pear).
task(apple).
task(banana).

can_help(T) :- task(T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        if s["indoor"]:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s["affords"]):
            lines.append(asp.fact("affords", sid, a))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming friendship storyworld about a puree mystery and teamwork.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero", choices=FRIENDS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    task = args.task or rng.choice(list(TASKS))
    hero = args.hero or rng.choice(FRIENDS)
    friend = args.friend or rng.choice([x for x in FRIENDS if x != hero])
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    if args.friend and args.hero and args.friend == args.hero:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(setting=setting, hero=hero, friend=friend, helper=helper, trait=trait, seed=args.seed)

def generate(params: StoryParams) -> StorySample:
    task = TASKS[params.task] if hasattr(params, "task") else None
    if task is None:
        task = TASKS[random.choice(list(TASKS))]
    setting = SETTING_REGISTRY[params.setting]
    world = World(setting)
    world.add(Entity(id=params.hero, kind="character", label=params.hero, memes={"hope": 1.0}))
    world.add(Entity(id=params.friend, kind="character", label=params.friend, memes={"curiosity": 1.0}))
    world.add(Entity(id=params.helper, kind="character", label=params.helper, memes={"need": 1.0}))
    world.add(Entity(id="bowl", label="a big bowl"))
    world.add(Entity(id="fruit", label=task.ingredient, meters={"fresh": 1.0}))

    world.say(f"{params.hero} was a {params.trait} child who loved helping friends.")
    world.say(f"One day, {params.friend} came by with a {task.reason}.")
    world.say(f"They decided to {task.action} in {setting['place']}, because friendship can make a small job feel easy.")

    world.para()
    world.say(f"But a little mystery popped up: {task.clue}.")
    world.say(f"{params.friend} was disappointed, and {params.hero} did not want the snack to fail.")
    world.say(f"So the two friends asked {params.helper} to join them, and together they looked carefully at the bowl.")

    world.para()
    world.say(f"At last, they found the problem and fixed it with {task.solved_with}.")
    world.say(f"The fruit turned into a smooth puree, and everyone shared a happy spoonful together.")
    world.say(f"{params.friend} smiled, less congested and much cheerier, while {params.hero} felt proud of their teamwork.")

    world.facts.update(task=task, params=params, setting=setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    task = world.facts["task"]
    return [
        f"Write a heartwarming story about friends who try to {task.action} and solve a small mystery together.",
        f"Tell a gentle children's story with the words puree and congest, where {p.hero} helps {p.friend}.",
        f"Write a teamwork story set in {world.setting['place']} that ends with everyone sharing puree.",
    ]

def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    task = world.facts["task"]
    return [
        QAItem(
            question=f"Who tried to help {p.friend} in the story?",
            answer=f"{p.hero} tried to help {p.friend}, and {p.helper} joined them when the mystery needed extra teamwork.",
        ),
        QAItem(
            question="What was the mystery they had to solve?",
            answer=f"They had to solve why it was hard to {task.action}; the clue was that {task.clue}.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The friends fixed the problem, made a smooth puree, and ended the day smiling together.",
        ),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is puree?",
            answer="Puree is soft food that has been mashed or blended until it is smooth.",
        ),
        QAItem(
            question="What does congest mean?",
            answer="To be congested means to feel stuffed up, often in the nose, so breathing can feel harder.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to finish something.",
        ),
    ]

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {' '.join(bits) if bits else 'empty'}")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)

def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show setting/1."))
    got = set(asp.atoms(model, "setting"))
    want = set((sid,) for sid in SETTING_REGISTRY)
    if got == want:
        print(f"OK: ASP parity for settings ({len(got)}).")
        return 0
    print("ASP mismatch.")
    print("got:", sorted(got))
    print("want:", sorted(want))
    return 1

CURATED = [
    StoryParams(setting="sunny_kitchen", hero="Mina", friend="Toby", helper="grandma", trait="gentle"),
    StoryParams(setting="garden_table", hero="Ruby", friend="Lila", helper="aunt", trait="curious"),
]

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
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            p.task = "pear" if not hasattr(p, "task") else p.task
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.task = args.task or random.Random(base_seed + i).choice(list(TASKS))
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
