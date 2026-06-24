#!/usr/bin/env python3
"""
storyworlds/worlds/testicle_civil_ize_receipt_bravery_lesson_learned.py
======================================================================

A small comedic storyworld about a child, a mistaken errand, a stubborn
receipt, and a brave attempt to civil-ize a chaotic moment into something
polite enough to keep.

Seed tale, reimagined:
- A kid finds a receipt for a bizarre item with the word "testicle" on it.
- The family tries to civil-ize the confusion at the kitchen table.
- Bravery means asking the embarrassing question out loud.
- Lesson Learned means the end of the mix-up, with laughter and a corrected
  receipt proving what changed.

The world is intentionally tiny and state-driven:
- physical meters: paper, ink_smudge, mess, tidiness
- emotional memes: curiosity, embarrassment, bravery, relief, humor, patience
- the story turns on a misunderstanding, not on a frozen paragraph with swapped
  nouns.

This file follows the Storyweavers contract:
- imports shared results eagerly
- imports shared asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {
        "paper": 0.0,
        "ink_smudge": 0.0,
        "tidiness": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "curiosity": 0.0,
        "embarrassment": 0.0,
        "bravery": 0.0,
        "relief": 0.0,
        "humor": 0.0,
        "patience": 0.0,
    })


@dataclass
class Object:
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {
        "paper": 0.0,
        "ink_smudge": 0.0,
        "mess": 0.0,
    })


@dataclass
class Room:
    place: str
    style: str = "comedy"
    civilized: bool = False
    confusion: bool = True
    objects: dict[str, Object] = field(default_factory=dict)
    people: dict[str, Person] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class Setting:
    place: str
    time_of_day: str
    prop: str
    audience: str
    afford_civilizing: bool = True


@dataclass
class StoryParams:
    setting: str
    prop: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", time_of_day="after lunch", prop="receipt", audience="family"),
    "hallway": Setting(place="the hallway", time_of_day="before dinner", prop="receipt", audience="family"),
    "library": Setting(place="the library corner", time_of_day="on a rainy afternoon", prop="receipt", audience="neighbors"),
}

NAMES = ["Milo", "Nina", "Toby", "Lena", "Arlo", "June"]
HELPERS = ["mom", "dad", "grandma", "older sister"]
PROPS = {
    "receipt": Object(label="receipt", kind="paper"),
}

ASP_RULES = r"""
setting(kitchen). setting(hallway). setting(library).
prop(receipt).

civilize_possible(S) :- setting(S), prop(receipt).

confusion_to_lesson(S) :- civilize_possible(S).
#show civilize_possible/1.
#show confusion_to_lesson/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show civilize_possible/1."))
    return sorted(set(asp.atoms(model, "civilize_possible")))


def asp_verify() -> int:
    py = sorted((s,) for s in SETTINGS)
    cl = asp_valid()
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} settings).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  python:", py)
    print("  asp:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a receipt, bravery, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    prop = args.prop or "receipt"
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if prop not in PROPS:
        raise StoryError("The prop must be a receipt in this tiny world.")
    return StoryParams(setting=setting, prop=prop, name=name, helper=helper)


def _act(world: Room, who: Person, kind: str, amount: float = 1.0) -> None:
    who.memes[kind] += amount


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    world = Room(place=setting.place)
    child = Person(name=params.name, role="child")
    helper = Person(name=params.helper, role="helper")
    receipt = Object(label="receipt", kind="paper")
    receipt.meters["paper"] = 1.0
    world.people[child.name] = child
    world.people[helper.name] = helper
    world.objects["receipt"] = receipt

    word = "testicle"
    world.say(f"{child.name} found a {receipt.label} on the table, and one line on it said '{word}'.")
    _act(world, child, "curiosity")
    world.say(f"{child.name} blinked twice and asked if the word was supposed to be there.")
    world.para()

    child.memes["embarrassment"] += 1
    child.memes["bravery"] += 1
    helper.memes["patience"] += 1
    receipt.meters["ink_smudge"] += 1
    world.say(f"In {setting.place}, the family tried to civil-ize the confusion with a careful laugh.")
    world.say(f"{child.name} was brave enough to read the line out loud, even though the word sounded silly.")
    world.say(f"{helper.name} listened, then explained that the receipt was for a toy and had been printed wrong.")
    world.para()

    world.civilized = True
    world.confusion = False
    child.memes["relief"] += 1
    child.memes["humor"] += 1
    helper.memes["humor"] += 1
    receipt.label = "corrected receipt"
    receipt.meters["ink_smudge"] = 0.0
    world.say(f"After the fix, the corrected receipt looked neat again, and everybody giggled at the mix-up.")
    world.say(f"{child.name} learned that brave questions can turn a weird moment into a polite one.")

    world.facts.update(
        child=child,
        helper=helper,
        receipt=receipt,
        setting=setting,
        word=word,
        lesson=True,
        bravery=True,
        civilized=world.civilized,
    )

    prompts = [
        f"Write a short comedy story where a child finds a receipt with the word '{word}' on it.",
        f"Tell a gentle story set in {setting.place} about bravery, a confusing receipt, and a lesson learned.",
        f"Write a child-friendly story that uses the words 'civil-ize', 'receipt', and 'testicle' without being mean.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.name} find?",
            answer=f"{params.name} found a receipt with a strange printed word on it.",
        ),
        QAItem(
            question=f"How did {params.name} show bravery?",
            answer=f"{params.name} was brave by reading the strange word out loud and asking about it.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that a funny mistake can be fixed by asking kindly and checking the receipt.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a receipt?",
            answer="A receipt is a small paper that shows what someone bought or paid for.",
        ),
        QAItem(
            question="What does it mean to civil-ize something in this story?",
            answer="In this story, to civil-ize something means to calm it down and make it polite and orderly.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for obj in sample.world.objects.values():
            print(obj.label, obj.meters)
        for person in sample.world.people.values():
            print(person.name, person.role, person.meters, person.memes)
        print("civilized:", sample.world.civilized, "confusion:", sample.world.confusion)
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("== story qa ==")
        for item in sample.story_qa:
            print("Q:", item.question)
            print("A:", item.answer)
        print("== world qa ==")
        for item in sample.world_qa:
            print("Q:", item.question)
            print("A:", item.answer)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show confusion_to_lesson/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show civilize_possible/1."))
        print(asp.atoms(model, "civilize_possible"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(StoryParams(setting=s, prop="receipt", name=NAMES[i % len(NAMES)], helper=HELPERS[i % len(HELPERS)]))
                   for i, s in enumerate(SETTINGS)]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
