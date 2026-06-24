#!/usr/bin/env python3
"""
storyworlds/worlds/heck_mould_lesson_learned_heartwarming.py
============================================================

A small heartwarming storyworld about a child, a messy mould problem, and a
lesson learned. The domain is intentionally tiny: a child discovers that a
spoiled snack or forgotten food has grown mould, feels upset, then learns a
kind, practical lesson about cleaning up, asking for help, and not leaving food
out.

Seed words: heck, mould
Style: heartwarming
Feature: lesson learned
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Location:
    id: str
    label: str
    cozy: bool = False


@dataclass
class StoryParams:
    place: str
    snack: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Location(id="kitchen", label="the kitchen", cozy=True),
    "pantry": Location(id="pantry", label="the pantry", cozy=False),
    "table": Location(id="table", label="the dining table", cozy=True),
    "shed": Location(id="shed", label="the garden shed", cozy=False),
}

SNACKS = {
    "bread": {"label": "bread", "phrase": "a soft loaf of bread"},
    "berries": {"label": "berries", "phrase": "a little box of berries"},
    "cereal": {"label": "cereal", "phrase": "a paper bowl of cereal"},
    "jam": {"label": "jam", "phrase": "a sweet jar of jam"},
}

GIRL_NAMES = ["Mia", "Lena", "Ivy", "Nora", "Sage", "Lily"]
BOY_NAMES = ["Finn", "Eli", "Noah", "Leo", "Theo", "Max"]


class World:
    def __init__(self, place: Location) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming mould lesson learned storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    snack = args.snack or rng.choice(list(SNACKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, snack=snack, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        type=params.snack,
        label=SNACKS[params.snack]["label"],
        phrase=SNACKS[params.snack]["phrase"],
        owner=child.id,
        caretaker=parent.id,
    ))
    snack.meters["mould"] = 1.0

    child.memes["disgust"] = 1.0
    child.memes["worry"] = 1.0
    child.memes["lesson"] = 1.0

    story = (
        f"One morning, {child.id} tiptoed into {world.place.label} and saw {child.pronoun('possessive')} "
        f"{snack.phrase} sitting all forgotten on the counter."
    )
    story += " " + (
        f"\"Heck,\" {child.pronoun('subject')} said softly, because little fuzzy spots of mould had grown on it."
    )
    story += " " + (
        f"{child.id} felt a tiny pinch in {child.pronoun('possessive')} chest and wanted to pretend the mess was not there."
    )

    world.say(f"One morning, {child.id} tiptoed into {world.place.label} and saw {child.pronoun('possessive')} {snack.phrase} sitting all forgotten on the counter.")
    world.say(f"\"Heck,\" {child.pronoun('subject')} said softly, because little fuzzy spots of mould had grown on it.")
    world.para()
    world.say(f"{child.id} felt a tiny pinch in {child.pronoun('possessive')} chest and wanted to pretend the mess was not there.")
    world.say(f"But {child.pronoun('subject')} knew mould could spread and make food too yucky to eat.")
    world.say(f"So {child.id} ran to find {child.pronoun('possessive')} {parent.type}.")
    world.para()
    world.say(f"{child.pronoun('possessive').capitalize()} {parent.type} came with a warm smile, wrapped the mouldy snack away, and showed {child.id} how to throw it out.")
    world.say(f"Then they wiped the counter together until it shone again.")
    world.say(f"{child.id} learned a simple lesson: if food sits out too long, it can grow mould, and it is kinder to clean it up right away.")
    world.say(f"After that, {child.id} washed {child.pronoun('possessive')} hands and felt proud for telling the truth.")

    world.facts = {
        "child": child,
        "parent": parent,
        "snack": snack,
        "place": params.place,
        "lesson": "clean up forgotten food quickly",
    }

    prompts = [
        "Write a heartwarming story about a child who finds mouldy food and learns a lesson.",
        f"Tell a gentle story set in {world.place.label} with the word 'heck' and the word 'mould'.",
        "Write a short story where a child asks for help, cleans up a mess, and learns what to do next time.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {child.id} find in {world.place.label}?",
            answer=f"{child.id} found {child.pronoun('possessive')} {snack.label} with mould growing on it.",
        ),
        QAItem(
            question=f"Why did {child.id} say \"heck\"?",
            answer=f"{child.id} said \"heck\" because the snack had mould and could not stay on the counter anymore.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer="The lesson was to clean up forgotten food quickly and ask a grown-up for help.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is mould?",
            answer="Mould is a fuzzy growth that can appear on old or wet food when it has been left out too long.",
        ),
        QAItem(
            question="Why should spoiled food be thrown away?",
            answer="Spoiled food should be thrown away because it is not safe to eat and can make a kitchen messy.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print("\n--- prompts ---")
        for p in sample.prompts:
            print(f"- {p}")
        print("\n--- story qa ---")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n--- world qa ---")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
% Tiny declarative twin for the basic reasonableness gate.
place(kitchen;pantry;table;shed).
snack(bread;berries;cereal;jam).
compatible(P,S) :- place(P), snack(S).
#show compatible/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("place", "kitchen"),
        asp.fact("place", "pantry"),
        asp.fact("place", "table"),
        asp.fact("place", "shed"),
        asp.fact("snack", "bread"),
        asp.fact("snack", "berries"),
        asp.fact("snack", "cereal"),
        asp.fact("snack", "jam"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = {(p, s) for p in PLACES for s in SNACKS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python")
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in PLACES for s in SNACKS]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("kitchen", "bread", "Mia", "girl", "mother"),
            StoryParams("pantry", "berries", "Finn", "boy", "father"),
            StoryParams("table", "cereal", "Lily", "girl", "mother"),
            StoryParams("shed", "jam", "Noah", "boy", "father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
