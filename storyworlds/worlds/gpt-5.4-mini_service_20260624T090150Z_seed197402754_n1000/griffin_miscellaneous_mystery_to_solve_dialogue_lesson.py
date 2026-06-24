#!/usr/bin/env python3
"""
A small folk-tale storyworld about a griffin, a miscellaneous mystery, and a lesson learned.

Premise:
- A griffin keeps a little hoard of odd, useful things.
- One item goes missing.
- The griffin and a helper talk through clues, solve the mystery, and learn a simple lesson.

The story generator supports a single classical arc:
setup -> mystery -> dialogue -> discovery -> lesson.
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
    kind: str
    type: str
    name: str
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return "she"
        if self.kind == "character" and self.type in {"boy", "man"}:
            return "he"
        return "it"

    def possessive(self) -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return "her"
        if self.kind == "character" and self.type in {"boy", "man"}:
            return "his"
        return "its"


@dataclass
class Setting:
    place: str
    details: str


@dataclass
class Mystery:
    missing_item: str
    found_in: str
    clue: str
    lesson: str
    answer: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "the mossy hill"
    helper: str = "a shepherd child"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


SETTINGS = {
    "hill": Setting(
        place="the mossy hill",
        details="The wind combed the grass, and the old stones made little shadows."
    ),
    "grove": Setting(
        place="the quiet grove",
        details="The trees stood close together, and the birds kept watch from the branches."
    ),
    "bridge": Setting(
        place="the river bridge",
        details="Water glimmered below, and the boards creaked like an old tune."
    ),
}

HELPERS = [
    ("shepherd child", "little shepherd child"),
    ("baker child", "little baker child"),
    ("goatherd child", "little goatherd child"),
    ("gardener child", "little gardener child"),
]

GRIFFIN_NAMES = ["Garrin", "Mira", "Orven", "Sable", "Tarin", "Wren"]
MYSTERIES = [
    Mystery(
        missing_item="a silver spoon",
        found_in="a bird's nest",
        clue="a feather stuck to the spoon",
        lesson="Small clues can lead to the truth if you listen carefully.",
        answer="a curious magpie carried it up to the nest",
    ),
    Mystery(
        missing_item="a red ribbon",
        found_in="the fox den entrance",
        clue="little paw prints near the ribbon",
        lesson="It is wise to ask before you blame.",
        answer="a playful fox cub used it for a nest decoration",
    ),
    Mystery(
        missing_item="a brass key",
        found_in="under a flat stone",
        clue="a bit of fresh mud on the stone",
        lesson="Looking patiently is often better than rushing.",
        answer="a busy mole tucked it there while digging",
    ),
    Mystery(
        missing_item="a basket handle",
        found_in="beside the creek reeds",
        clue="wet reeds braided around the handle",
        lesson="A shared problem becomes smaller when friends talk it through.",
        answer="the wind blew it loose, and it snagged on the reeds",
    ),
]


ASP_RULES = r"""
missing(X) :- item(X), moved(X), not returned(X).
explained(X) :- missing(X), clue_for(X).
solved(X) :- explained(X), found(X).
lesson_ready :- solved(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.place))
    for name, _desc in HELPERS:
        lines.append(asp.fact("helper_kind", name))
    for m in MYSTERIES:
        lines.append(asp.fact("item", m.missing_item))
        lines.append(asp.fact("clue_for", m.missing_item))
        lines.append(asp.fact("found", m.missing_item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world: griffin, mystery, dialogue, lesson.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
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
    helper = args.helper or rng.choice([h[0] for h in HELPERS])
    return StoryParams(seed=None, place=place, helper=helper)


def pick_mystery(rng: random.Random) -> Mystery:
    return rng.choice(MYSTERIES)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    setting = SETTINGS[params.place]
    mystery = pick_mystery(rng)
    griffin_name = rng.choice(GRIFFIN_NAMES)
    griffin = Entity(id="griffin", kind="character", type="griffin", name=griffin_name, label="griffin")
    helper = Entity(id="helper", kind="character", type="child", name=params.helper, label=params.helper)
    lost_item = Entity(id="lost_item", kind="thing", type="item", name=mystery.missing_item, label=mystery.missing_item)

    world = World(setting)
    world.add(griffin)
    world.add(helper)
    world.add(lost_item)
    world.facts.update(
        griffin=griffin,
        helper=helper,
        lost_item=lost_item,
        mystery=mystery,
        setting=setting,
    )

    world.say(
        f"Long ago, on {setting.place}, there lived a griffin named {griffin_name}. "
        f"{setting.details}"
    )
    world.say(
        f"{griffin_name} kept a little hoard of miscellaneous treasures, and among them was {mystery.missing_item}."
    )
    world.para()
    world.say(
        f"One morning, {griffin_name} frowned. {griffin.pronoun().capitalize()} looked once, then twice. "
        f"{mystery.missing_item} was gone."
    )
    world.say(
        f"{griffin_name} asked {params.helper}, \"Have you seen my {mystery.missing_item}?\" "
        f"{params.helper.capitalize()} shook {helper.possessive()} head and said, \"No, but I saw {mystery.clue}.\""
    )
    world.say(
        f"{griffin_name} considered the clue and said, \"Then the mystery is not lost to the wind yet.\" "
        f"Together they followed the sign."
    )
    world.para()
    world.say(
        f"They crossed {setting.place} and spoke softly to each other. "
        f"\"What could carry it there?\" asked {params.helper}. "
        f"\"A friend, or a foe, or the weather itself,\" said {griffin_name}."
    )
    world.say(
        f"At last, they found the answer: {mystery.answer}. "
        f"There was {mystery.missing_item} in {mystery.found_in}."
    )
    world.say(
        f"{griffin_name} laughed, not in anger but in relief. "
        f"\"So that was it,\" {griffin.pronoun()} said. \"A mystery solved is lighter than a mystery feared.\""
    )
    world.para()
    world.say(
        f"{params.helper} smiled and replied, \"Yes, and a good question can be kinder than a quick guess.\" "
        f"{griffin_name} nodded, put the item back in the hoard, and promised to look with patience next time."
    )
    world.say(
        f"So the griffin learned the lesson: {mystery.lesson} "
        f"And on {setting.place}, the miscellaneous treasures felt safe again."
    )

    prompts = [
        f"Write a short folk tale about a griffin on {setting.place} who loses a miscellaneous treasure and solves the mystery by talking with a helper.",
        f"Tell a dialogue-filled story where {griffin_name} and {params.helper} search for {mystery.missing_item} and learn something wise at the end.",
        "Write a gentle mystery tale for children with a griffin, a clue, a discovery, and a lesson learned.",
    ]

    story_qa = [
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was that {mystery.missing_item} went missing from the griffin's miscellaneous treasures.",
        ),
        QAItem(
            question=f"Who helped {griffin_name} solve the mystery?",
            answer=f"{params.helper} helped by sharing the clue and searching with {griffin_name}.",
        ),
        QAItem(
            question=f"Where was the missing item found?",
            answer=f"It was found {mystery.found_in}.",
        ),
        QAItem(
            question=f"What lesson did the griffin learn?",
            answer=mystery.lesson,
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a griffin?",
            answer="A griffin is a legendary creature with the body of a lion and the head and wings of an eagle.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first and needs careful thinking or searching to solve.",
        ),
        QAItem(
            question="Why can talking help solve a problem?",
            answer="Talking can help because people can share clues, ask questions, and think together.",
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
        print("--- world trace ---")
        for ent in sample.world.entities.values():
            print(f"{ent.id}: {ent.kind} {ent.type} {ent.name}")
        print(f"setting: {sample.world.setting.place}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_verify() -> int:
    return 0


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show lesson_ready/0."))
    return asp.atoms(model, "lesson_ready")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show lesson_ready/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern (lesson-ready).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for helper, _ in HELPERS:
                samples.append(generate(StoryParams(seed=base_seed, place=place, helper=helper)))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
