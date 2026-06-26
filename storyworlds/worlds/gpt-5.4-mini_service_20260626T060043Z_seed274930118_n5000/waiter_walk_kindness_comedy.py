#!/usr/bin/env python3
"""
storyworlds/worlds/waiter_walk_kindness_comedy.py
==================================================

A small comedy storyworld about a waiter, a walk, and a kind choice.

Premise:
- A waiter needs to walk a tray across a busy little café.
- Along the way, something awkward or silly happens.
- Kindness turns the mishap into a happy ending.

The world is intentionally compact: it simulates a waiter, a route, a tray,
a small obstacle, and the emotional effect of choosing kindness over haste.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wore: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"waiter", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the café"
    route: str = "the narrow aisle"
    ambience: str = "bright and busy"


@dataclass
class Tray:
    id: str
    label: str
    contents: str
    wobble_risk: float = 1.0


@dataclass
class StoryParams:
    name: str
    helper_name: str
    dish: str
    obstacle: str
    setting: str = "cafe"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cafe": Setting(place="the café", route="the narrow aisle", ambience="bright and busy"),
    "bakery": Setting(place="the bakery", route="the warm hallway", ambience="sweet and buzzy"),
    "diner": Setting(place="the diner", route="the shiny counter path", ambience="lively and clattery"),
}

DISHES = {
    "tea": "a steaming cup of tea",
    "soup": "a bowl of soup",
    "pie": "a tiny berry pie",
    "cookies": "a plate of cookies",
}

OBSTACLES = {
    "puddle": "a little puddle from the mop bucket",
    "cat": "a sleepy cat stretched across the path",
    "balloon": "a drifting balloon string tangled near the tray",
    "toycar": "a tiny toy car left in the aisle",
}

NAMES = ["Milo", "Nina", "Owen", "Pia", "June", "Leo", "Ada", "Nora", "Ben", "Maya"]
HELPER_NAMES = ["Toby", "Iris", "Zane", "Lily", "Theo", "Ruby", "Elena", "Sam"]
TRAITS = ["cheerful", "patient", "bouncy", "gentle", "quick", "kind"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    waiter = world.add(Entity(
        id=params.name,
        kind="character",
        type="waiter",
        label="waiter",
        meters={"steps": 0.0, "balance": 0.0},
        memes={"kindness": 0.0, "hurry": 0.0, "amusement": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="customer",
        label="helper",
        meters={"steps": 0.0},
        memes={"kindness": 0.0, "amusement": 0.0},
    ))
    tray = world.add(Entity(
        id="tray",
        type="tray",
        label="tray",
        phrase=DISHES[params.dish],
        owner=waiter.id,
        caretaker=waiter.id,
        meters={"wobble": 0.0, "spill": 0.0},
    ))
    obstacle = world.add(Entity(
        id="obstacle",
        type=params.obstacle,
        label=OBSTACLES[params.obstacle],
        meters={"blocking": 1.0},
    ))

    world.facts.update(
        waiter=waiter,
        helper=helper,
        tray=tray,
        obstacle=obstacle,
        dish=params.dish,
        obstacle_key=params.obstacle,
        setting=params.setting,
    )
    return world


def _step(world: World, actor: Entity, distance: float = 1.0) -> None:
    actor.meters["steps"] = actor.meters.get("steps", 0.0) + distance
    actor.meters["balance"] = actor.meters.get("balance", 0.0) + 0.2


def _wobble(world: World, tray: Entity, amount: float = 1.0) -> None:
    tray.meters["wobble"] = tray.meters.get("wobble", 0.0) + amount
    if tray.meters["wobble"] >= 2.0:
        tray.meters["spill"] = tray.meters.get("spill", 0.0) + 1.0


def _kind_act(world: World, waiter: Entity, helper: Entity, obstacle: Entity, tray: Entity) -> None:
    waiter.memes["kindness"] += 1.0
    helper.memes["kindness"] += 1.0
    waiter.memes["amusement"] += 1.0
    tray.meters["wobble"] = max(0.0, tray.meters.get("wobble", 0.0) - 0.75)
    world.fired.add(("kindness", obstacle.id))
    obstacle.meters["blocking"] = 0.0


def tell(params: StoryParams) -> World:
    world = build_world(params)
    waiter = world.get(params.name)
    helper = world.get(params.helper_name)
    tray = world.get("tray")
    obstacle = world.get("obstacle")
    setting = world.setting

    trait = random.choice(TRAITS)

    # Beginning
    world.say(
        f"{waiter.id} was a {trait} waiter at {setting.place}. "
        f"{waiter.pronoun().capitalize()} liked the busy hum of the room and always walked fast with a tray."
    )
    world.say(
        f"One day {waiter.id} carried {tray.phrase} down {setting.route}, hoping to serve it without a single wobble."
    )

    # Middle turn
    world.para()
    _step(world, waiter)
    _wobble(world, tray, 1.0)
    world.say(
        f"Then {waiter.id} found {obstacle.label} in the way. "
        f"The tray tipped a little, and the walk turned into a very silly wobble."
    )
    world.say(
        f"{waiter.id} could have hurried past, but {waiter.pronoun('subject')} noticed {helper.id} trying to reach the same path."
    )
    world.say(
        f"Instead of grumbling, {waiter.id} smiled and helped {helper.id} move {obstacle.label} aside."
    )
    _kind_act(world, waiter, helper, obstacle, tray)

    # Resolution
    world.para()
    _step(world, waiter)
    world.say(
        f"With the path clear, {waiter.id} walked on more carefully. "
        f"{helper.id} carried the napkins, and together they made the little trip feel like a parade."
    )
    world.say(
        f"{waiter.id} delivered {tray.phrase} with a grin. "
        f"The guests laughed when they saw the tiny relief on {waiter.id}'s face, because the hardest walk had become the kindest one."
    )
    world.say(
        f"At the end, the tray was safe, the café was calm, and {waiter.id} was smiling at the neat, happy table."
    )

    world.facts.update(
        resolved=True,
        kindness=waiter.memes["kindness"],
        spill=tray.meters.get("spill", 0.0),
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, dish: str, obstacle: str) -> bool:
    if setting not in SETTINGS or dish not in DISHES or obstacle not in OBSTACLES:
        return False
    if dish == "soup" and obstacle == "balloon":
        return True
    if dish in {"tea", "pie", "cookies"}:
        return True
    return True


def explain_rejection(setting: str, dish: str, obstacle: str) -> str:
    return f"(No story: that combination does not make a good comic walk through {SETTINGS[setting].place}.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_name(S).
dish(D) :- dish_name(D).
obstacle(O) :- obstacle_name(O).

valid(S,D,O) :- setting(S), dish(D), obstacle(O).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
    for d in DISHES:
        lines.append(asp.fact("dish_name", d))
    for o in OBSTACLES:
        lines.append(asp.fact("obstacle_name", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, d, o) for s in SETTINGS for d in DISHES for o in OBSTACLES if valid_combo(s, d, o)}
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python validity.")
    print("only in python:", sorted(py - asps))
    print("only in clingo:", sorted(asps - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    waiter = f["waiter"]
    dish = f["dish"]
    obstacle = f["obstacle_key"]
    return [
        f"Write a funny short story about a waiter named {waiter.id} who has to walk carefully with {DISHES[dish]}.",
        f"Tell a comedy story where a waiter uses kindness to solve a small problem on the way to the table.",
        f"Write a gentle café story with a walk, a tray, and a silly obstacle like {OBSTACLES[obstacle]}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    waiter: Entity = f["waiter"]
    helper: Entity = f["helper"]
    tray: Entity = f["tray"]
    obstacle: Entity = f["obstacle"]
    setting: str = f["setting"]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=(
                f"It is about {waiter.id}, a waiter at {SETTINGS[setting].place}, "
                f"who had to walk carefully with {tray.phrase}."
            ),
        ),
        QAItem(
            question=f"What silly thing blocked the walk?",
            answer=(
                f"The walk was blocked by {obstacle.label}, which made the tray wobble and turn the trip into a funny mess."
            ),
        ),
        QAItem(
            question=f"How did {waiter.id} solve the problem?",
            answer=(
                f"{waiter.id} chose kindness, helped {helper.id}, and moved {obstacle.label} aside instead of rushing past it."
            ),
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=(
                f"The tray stayed safe, the table got served, and the café ended in a cheerful, laughing kind of calm."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a waiter do?",
            answer="A waiter brings food and drinks to people at tables and tries to keep the meals steady and friendly.",
        ),
        QAItem(
            question="Why should someone walk carefully with a tray?",
            answer="A tray can tip if it moves too fast, so careful walking helps keep the food from spilling.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping someone, being gentle, and making things better for another person.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a waiter, a walk, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    dish = args.dish or rng.choice(list(DISHES))
    obstacle = args.obstacle or rng.choice(list(OBSTACLES))
    if args.setting and args.dish and args.obstacle and not valid_combo(args.setting, args.dish, args.obstacle):
        raise StoryError(explain_rejection(args.setting, args.dish, args.obstacle))
    name = args.name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != name])
    return StoryParams(name=name, helper_name=helper_name, dish=dish, obstacle=obstacle, setting=setting)


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
    StoryParams(name="Milo", helper_name="Iris", dish="tea", obstacle="puddle", setting="cafe"),
    StoryParams(name="Nina", helper_name="Theo", dish="pie", obstacle="cat", setting="bakery"),
    StoryParams(name="Ben", helper_name="Ruby", dish="soup", obstacle="balloon", setting="diner"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid combos:")
        for item in combos:
            print(" ", item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
