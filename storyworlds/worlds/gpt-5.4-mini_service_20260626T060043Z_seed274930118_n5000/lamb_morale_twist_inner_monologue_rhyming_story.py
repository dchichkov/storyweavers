#!/usr/bin/env python3
"""
A tiny story world where a lamb loses and lifts morale, with a twist and an
inner monologue, told in a gentle rhyming style.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"lamb", "sheep", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"ram", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    afford: str


@dataclass
class StoryParams:
    place: str
    task: str
    twist: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", mood="bright", afford="sing"),
    "hill": Setting(place="the hill", mood="windy", afford="climb"),
    "barnyard": Setting(place="the barnyard", mood="busy", afford="help"),
}

TASKS = {
    "sing": {
        "verb": "sing a tune",
        "gerund": "singing a tune",
        "risk": "her voice would shake",
        "turn": "kept her steady",
        "meter": "tremble",
    },
    "climb": {
        "verb": "climb the hill",
        "gerund": "climbing the hill",
        "risk": "her hooves would slip",
        "turn": "made the path safer",
        "meter": "worry",
    },
    "help": {
        "verb": "help the flock",
        "gerund": "helping the flock",
        "risk": "the work would feel too big",
        "turn": "made the load much lighter",
        "meter": "doubt",
    },
}

TWISTS = {
    "bell": "a little bell in her wool",
    "rain": "a soft rain pattering down",
    "kite": "a kite tangled in a bush",
}

NAMES = ["Mina", "Luna", "Pip", "Daisy", "Nell", "Tessa", "Bram"]
TRAITS = ["brave", "gentle", "shy", "cheery", "tiny"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(world: World, params: StoryParams) -> World:
    lamb = world.add(Entity(
        id=params.name,
        kind="character",
        type="lamb",
        label="lamb",
        phrase=f"a little {random.choice(TRAITS)} lamb",
        meters={"morale": 4.0},
        memes={"hope": 1.0, "curiosity": 1.0},
    ))
    world.say(f"In {world.setting.place}, there was {params.name}, a lamb so light and bright.")
    world.say(f"{params.name} loved to {TASKS[params.task]['verb']} from morning into night.")
    world.say(f"{params.name} looked at {world.setting.place} and felt the air feel right.")

    world.lines.append("")
    world.say(f"Then came the wish to {TASKS[params.task]['verb']}, a bubbly, bouncy plan.")
    lamb.memes["desire"] = lamb.memes.get("desire", 0.0) + 1.0
    lamb.meters["morale"] -= 1.0
    world.say(f"But {params.name} thought, “What if I fail? What if I’m not a can-do lamb?”")

    world.lines.append("")
    world.say(f"Her inner monologue swirled and twirled: “My {TASKS[params.task]['risk']}.")
    world.say(f"If I turn back now, my heart will frown; my cheer might sink and slip.”")

    world.lines.append("")
    world.say(f"Then came the twist: {TWISTS[params.twist]} near {world.setting.place}.")
    world.say(f"{params.name} noticed it first, and it changed her mind and pace.")
    world.say(f"She used the twist to {TASKS[params.task]['turn']}, with courage on her face.")

    lamb.meters["morale"] += 3.0
    lamb.memes["hope"] += 2.0
    lamb.memes["twist"] = 1.0

    world.lines.append("")
    if params.task == "sing":
        world.say(f"So {params.name} sang by the bell, and her song rang sweet and thin.")
        world.say(f"The wobble turned to a hum, and the whole day hummed right in.")
    elif params.task == "climb":
        world.say(f"So {params.name} climbed with care, one hop, then two, then three.")
        world.say(f"The hill felt less like a wall, and more like a friend to see.")
    else:
        world.say(f"So {params.name} helped the flock with kind small steps and cheer.")
        world.say(f"The work grew warm and easy, and everyone drew near.")

    world.say(f"By the end, {params.name} felt bold and bright; her morale climbed high and clear.")
    world.facts.update(lamb=lamb, task=params.task, twist=params.twist, setting=world.setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lamb: Entity = f["lamb"]  # type: ignore[assignment]
    task = TASKS[f["task"]]  # type: ignore[index]
    return [
        f'Write a short rhyming story for children about a lamb named {lamb.id} who wants to {task["verb"]}, then finds a surprise twist.',
        f"Tell a gentle story with an inner monologue in which {lamb.id} worries, then feels hopeful again.",
        f"Write a simple moral tale where a lamb's morale dips, then rises after a twist in the {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lamb: Entity = f["lamb"]  # type: ignore[assignment]
    task = TASKS[f["task"]]  # type: ignore[index]
    twist = TWISTS[f["twist"]]  # type: ignore[index]
    return [
        QAItem(
            question=f"What did {lamb.id} want to do in {world.setting.place}?",
            answer=f"{lamb.id} wanted to {task['verb']}, and she thought hard about it before trying.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was {twist}, and it helped {lamb.id} see the moment in a new way.",
        ),
        QAItem(
            question=f"How did {lamb.id}'s morale change by the end?",
            answer=f"Her morale started lower when she felt unsure, then rose after she acted bravely.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a lamb?",
        answer="A lamb is a young sheep. Lambs are small, soft, and often very gentle.",
    ),
    QAItem(
        question="What does morale mean?",
        answer="Morale means how hopeful, brave, or cheerful someone feels inside.",
    ),
    QAItem(
        question="What is an inner monologue?",
        answer="An inner monologue is the quiet stream of thoughts a character has in their own mind.",
    ),
    QAItem(
        question="What is a twist in a story?",
        answer="A twist is a surprising change that makes the story go in a new direction.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(meadow).
setting(hill).
setting(barnyard).

task(sing).
task(climb).
task(help).

twist(bell).
twist(rain).
twist(kite).

compatible(P,T,X) :- setting(P), task(T), twist(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for x in TWISTS:
        lines.append(asp.fact("twist", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def python_valid_combos() -> list[tuple[str, str, str]]:
    return sorted((p, t, x) for p in SETTINGS for t in TASKS for x in TWISTS)


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(python_valid_combos())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between ASP and python gates.")
    if a - p:
        print("  only in ASP:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming lamb story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name", choices=NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    twist = args.twist or rng.choice(list(TWISTS))
    name = args.name or rng.choice(NAMES)
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if task not in TASKS:
        raise StoryError("Unknown task.")
    if twist not in TWISTS:
        raise StoryError("Unknown twist.")
    return StoryParams(place=place, task=task, twist=twist, name=name)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    tell(world, params)
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
        lines.append(f"  {e.id:10} kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
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


CURATED = [
    StoryParams(place="meadow", task="sing", twist="bell", name="Mina"),
    StoryParams(place="hill", task="climb", twist="rain", name="Luna"),
    StoryParams(place="barnyard", task="help", twist="kite", name="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.task} at {p.place} (twist: {p.twist})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
