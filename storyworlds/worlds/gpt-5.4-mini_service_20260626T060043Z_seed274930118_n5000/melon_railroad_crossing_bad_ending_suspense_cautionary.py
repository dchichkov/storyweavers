#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/melon_railroad_crossing_bad_ending_suspense_cautionary.py
==================================================================================================

A small animal-story world set at a railroad crossing.

Seed tale used to build the model:
---
A young raccoon named Milo found a striped melon near a railroad crossing. He
wanted to roll it across the tracks because it looked funny and bouncy. His
older sister warned him that the crossing gate was down and a train was coming.
Milo did not listen. He rolled the melon anyway, and the train smashed it into
sticky green juice. Milo got scared, the melon was ruined, and he learned that
railroad crossings are not safe places to play.
---

This world intentionally produces a cautionary, suspenseful bad ending. The
tension comes from a visible train, a lowered gate, and an ignored warning. The
ending proves the lesson by changing the physical world: the melon is smashed,
the animal is startled, and the crossing remains unsafe for play.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    region: str = ""
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"raccoon", "fox", "bear", "wolf"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"rabbit", "mouse", "squirrel"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the railroad crossing"
    affords: set[str] = field(default_factory=lambda: {"roll_melon"})


@dataclass
class StoryParams:
    name: str
    animal: str
    helper: str
    seed: Optional[int] = None


ANIMALS = {
    "raccoon": {"gendered": "boy", "label": "young raccoon"},
    "rabbit": {"gendered": "girl", "label": "little rabbit"},
    "fox": {"gendered": "boy", "label": "young fox"},
    "mouse": {"gendered": "girl", "label": "small mouse"},
}
HELPERS = {
    "sister": "older sister",
    "mother": "mother",
    "brother": "older brother",
    "uncle": "uncle",
}

SETTING = Setting()

ASP_RULES = r"""
% A bad-ending cautionary story exists when a child animal ignores a warning
% at a railroad crossing and the melon is crushed by an oncoming train.
warning_ignored(A) :- animal(A), warned(A), stubborn(A).
bad_ending(A) :- warning_ignored(A), crossing(crossing), train_coming(crossing).
"""

CURATED = [
    StoryParams(name="Milo", animal="raccoon", helper="sister"),
    StoryParams(name="Pip", animal="rabbit", helper="mother"),
    StoryParams(name="Rudy", animal="fox", helper="brother"),
]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.gates_down = True
        self.train_coming = True

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world at a railroad crossing with a cautionary bad ending.")
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    animal = args.animal or rng.choice(sorted(ANIMALS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    if args.name:
        name = args.name
    else:
        names = {"raccoon": ["Milo", "Finn", "Perry"], "rabbit": ["Pip", "Mina", "Luna"], "fox": ["Rudy", "Toby", "Remy"], "mouse": ["Nia", "Dot", "Tess"]}
        name = rng.choice(names[animal])
    return StoryParams(name=name, animal=animal, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"Unknown animal: {params.animal}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    world = World()
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, label=ANIMALS[params.animal]["label"]))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=HELPERS[params.helper]))
    melon = world.add(Entity(id="melon", type="melon", label="melon", phrase="a striped melon", owner=hero.id, region="track"))
    train = world.add(Entity(id="train", type="train", label="train", protective=False))
    world.facts.update(hero=hero, helper=helper, melon=melon, train=train, setting=SETTING)

    world.say(f"{hero.id} was a {hero.label} who loved finding odd things to roll.")
    world.say(f"One morning, {hero.id} spotted {melon.phrase} beside {SETTING.place}.")
    world.say(f"{hero.id} thought it would be fun to roll {melon.it()} across the tracks, because it looked round and bouncy.")
    world.para()
    world.say(f"But the crossing gate was already down, and a train was coming.")
    world.say(f"{helper.label.capitalize()} saw the danger and called out, \"Stop! A railroad crossing is no place to play.\"")
    hero.memes["desire"] = 1
    hero.memes["warning_heard"] = 1
    helper.memes["fear"] = 1
    world.say(f"{hero.id} heard the warning, but {hero.pronoun('possessive')} paws kept edging forward.")
    hero.memes["stubborn"] = 1
    world.say(f"{hero.id} rolled the melon anyway.")
    world.para()
    melon.meters["rolling"] = 1
    melon.meters["on_tracks"] = 1
    world.say(f"Then the train thundered closer.")
    world.say(f"In a flash, the wheels crushed {melon.it()} into sticky green juice, and {hero.id} jumped back in fright.")
    melon.meters["smashed"] = 1
    hero.memes["fear"] = 1
    hero.memes["regret"] = 1
    world.say(f"{hero.id}'s fun was gone, and the crossing smelled sweet and messy instead of playful.")
    world.say(f"{helper.label.capitalize()} pulled {hero.pronoun('object')} away from the tracks and said, \"Next time, listen when the gate is down.\"")
    world.say(f"{hero.id} looked at the ruined melon and knew the warning had been true.")
    world.facts["bad_ending"] = True
    world.facts["warning"] = True
    world.facts["melon_smashed"] = True
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
    hero = f["hero"]
    helper = f["helper"]
    return [
        'Write a suspenseful animal story for a small child set at a railroad crossing that includes a melon and ends badly.',
        f"Tell a cautionary story about {hero.id} the {hero.type} who ignores {helper.label} at a railroad crossing.",
        "Write a short story where a child animal tries to roll a melon over train tracks even though the gate is down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    melon = f["melon"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the melon?",
            answer=f"{hero.id} wanted to roll {melon.it()} across the railroad tracks because it looked fun and bouncy.",
        ),
        QAItem(
            question=f"Why was {helper.label} worried?",
            answer=f"{helper.label.capitalize()} was worried because the gate was down and a train was coming at the railroad crossing.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=f"The train crushed the melon into sticky green juice, so the story ends as a bad ending and a cautionary lesson.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the train came?",
            answer=f"{hero.id} felt frightened and regretful after seeing the melon ruined.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a railroad crossing?",
            answer="A railroad crossing is a place where a road or path crosses train tracks, so people must be careful there.",
        ),
        QAItem(
            question="Why is a railroad crossing dangerous when a train is coming?",
            answer="It is dangerous because trains are big and fast, and they need a lot of space to pass safely.",
        ),
        QAItem(
            question="What is a melon?",
            answer="A melon is a round fruit with juicy flesh inside, and some melons have striped or green rinds.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("crossing", "crossing"),
        asp.fact("train_coming", "crossing"),
    ]
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/1.\n#show warning_ignored/1."))
    atoms = set(asp.atoms(model, "bad_ending"))
    expected = {("crossing",)}
    if atoms == expected:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP parity failure.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def asp_bad_endings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/1."))
    return sorted(set(asp.atoms(model, "bad_ending")))


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
        print(asp_program("#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_bad_endings())} bad-ending ASP outcome(s).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
