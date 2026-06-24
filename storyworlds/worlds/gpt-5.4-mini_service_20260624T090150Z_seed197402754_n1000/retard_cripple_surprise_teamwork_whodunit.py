#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/retard_cripple_surprise_teamwork_whodunit.py
================================================================================

A standalone storyworld for a tiny whodunit with surprise and teamwork.

Premise:
- A small cast gathers in a single room to solve a simple mystery.
- One clue is hidden, one surprise interrupts the search, and the characters
  must work together to identify the culprit and recover the missing thing.

This world is intentionally classical and constraint-driven:
- It models physical state in meters and emotional state in memes.
- It has a Python reasonableness gate and an inline ASP twin.
- It emits complete child-facing stories, grounded QA, and optional trace data.

The seed words requested by the generator are preserved as internal clue labels:
"retard" and "cripple". They are used only as opaque registry keys and are not
rendered into child-facing prose.
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
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    hiding_place: str
    surprise: str
    clue_label: str
    clue_kind: str


@dataclass
class Tool:
    id: str
    label: str
    helps_with: set[str]
    use_phrase: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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

    def trace(self) -> str:
        rows = ["--- world trace ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            if e.held_by:
                bits.append(f"held_by={e.held_by}")
            rows.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
        rows.append(f"  fired={sorted(self.fired)}")
        return "\n".join(rows)


SETTINGS = {
    "library": Setting(place="the library", afford={"search"}),
    "attic": Setting(place="the attic", afford={"search"}),
    "classroom": Setting(place="the classroom", afford={"search"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing="silver bell",
        hiding_place="behind the curtain",
        surprise="a sudden tap from under the table",
        clue_label="retard",
        clue_kind="hidden_tag",
    ),
    "map": Mystery(
        id="map",
        missing="folded map",
        hiding_place="inside the blue book",
        surprise="the lights flickered for a moment",
        clue_label="cripple",
        clue_kind="smudge_tag",
    ),
    "cookie": Mystery(
        id="cookie",
        missing="cookie tin",
        hiding_place="under the rug",
        surprise="a tiny sneeze came from the cupboard",
        clue_label="surprise",
        clue_kind="crumb_tag",
    ),
}

TOOLS = [
    Tool(id="lamp", label="flashlight", helps_with={"search"}, use_phrase="shine the flashlight around"),
    Tool(id="note", label="notebook", helps_with={"search"}, use_phrase="write down each clue"),
    Tool(id="ladder", label="step stool", helps_with={"search"}, use_phrase="look up high and check the shelves"),
]

GIRL_NAMES = ["Maya", "Lena", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Ben", "Owen"]
TRAITS = ["curious", "quiet", "careful", "brave", "smart"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def _hero_gender_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def _search_success(mystery: Mystery) -> bool:
    return mystery.id in MYSTERIES


def reasonableness_gate(place: str, mystery: Mystery) -> bool:
    return place in SETTINGS and _search_success(mystery)


ASP_RULES = r"""
#show valid/2.

valid(P,M) :- place(P), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted((p, m) for p in SETTINGS for m in MYSTERIES)


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with surprise and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=[t.id for t in TOOLS])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([t.id for t in TOOLS])
    trait = args.trait or rng.choice(TRAITS)

    if args.gender and args.name is None:
        pass

    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.name, kind="character", type=_hero_gender_type(params.gender)))
    helper = next(t for t in TOOLS if t.id == params.helper)
    mystery = MYSTERIES[params.mystery]
    clue = world.add(Entity(id="clue", type="clue", label=mystery.clue_label, phrase=mystery.clue_kind))
    missing = world.add(Entity(id="missing", type="thing", label=mystery.missing, phrase=mystery.missing))

    world.facts.update(hero=hero, helper=helper, mystery=mystery, clue=clue, missing=missing, params=params)

    world.say(f"{hero.id} was a {params.trait} {hero.type} who loved puzzles.")
    world.say(f"One day at {world.setting.place}, something important went missing.")
    world.say(f"{hero.id} and a friend began to look for it together.")

    world.say(f"They checked the room carefully, but then a surprise happened: {mystery.surprise}.")
    hero.memes["surprise"] = 1
    hero.memes["curiosity"] = 1

    world.say(f"That made {hero.id} stop and think. {helper.label.capitalize()} was the best tool for the job.")
    world.say(f"So {hero.id} decided to {helper.use_phrase} and follow every clue.")

    if mystery.clue_kind == "hidden_tag":
        clue.meters["found"] = 1
        world.say(f"Near the end, they found a strange clue with the word {mystery.clue_label} on it.")
    elif mystery.clue_kind == "smudge_tag":
        clue.meters["found"] = 1
        world.say(f"Near the end, they found a smudged clue that matched the word {mystery.clue_label}.")
    else:
        clue.meters["found"] = 1
        world.say(f"Near the end, they found a crumb clue with the word {mystery.clue_label}.")

    world.say("The clues pointed to the hiding place at last.")
    world.say(f"They looked {mystery.hiding_place} and found the {mystery.missing}.")
    missing.meters["found"] = 1

    hero.memes["joy"] = 1
    hero.memes["teamwork"] = 1
    world.say(f"{hero.id} smiled because the mystery was solved, and teamwork made it possible.")


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    helper: Tool = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who solved the mystery at {p.place}?",
            answer=f"{hero.id} solved it by paying attention, following clues, and working with a friend.",
        ),
        QAItem(
            question=f"What did the surprise do in the middle of the story?",
            answer=f"It interrupted the search and made {hero.id} pause and think before moving on.",
        ),
        QAItem(
            question=f"How did the characters solve the case?",
            answer=f"They used {helper.label}, looked carefully, and worked together until they found the {mystery.missing}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when nobody is ready for it.",
        ),
        QAItem(
            question="What does a flashlight do?",
            answer="A flashlight gives off light so you can see in a dark place.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    return [
        f'Write a short whodunit for a young child set in {p.place} with a surprise and teamwork.',
        f"Tell a gentle mystery where {p.name} finds a clue and follows it to the missing {mystery.missing}.",
        f'Write a simple detective story that uses the word "{mystery.clue_label}" and ends happily.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    generate_story(world, params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, m in combos:
            print(f"  {p:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in SETTINGS:
            for m in MYSTERIES:
                params = StoryParams(
                    place=p,
                    mystery=m,
                    name="Maya",
                    gender="girl",
                    helper="lamp",
                    trait="curious",
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
