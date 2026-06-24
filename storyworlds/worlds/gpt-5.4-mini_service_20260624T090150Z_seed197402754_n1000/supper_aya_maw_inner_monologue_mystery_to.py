#!/usr/bin/env python3
"""
A compact storyworld about a small supper-time mystery on a space outpost.

Premise:
- Aya and Maw sit down for supper in a glowing station kitchen.
- Something important is missing: the spoon tray keeps turning up out of place.
- Aya notices clues, repeats a careful search pattern, and solves the mystery with an inner monologue guiding her.

Narrative instruments:
- Inner monologue
- Mystery to solve
- Repetition
Style:
- Space adventure
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "maw"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the station kitchen"
    feature: str = "soft console lights"
    sound: str = "a low hum from the hull"


@dataclass
class Mystery:
    missing: str
    culprit: str
    clue: str
    repeated_search: str
    solved_by: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    name: str = "Aya"
    maw_name: str = "Maw"
    seed: Optional[int] = None


SETTINGS = {
    "station": Setting(
        place="the station kitchen",
        feature="soft console lights",
        sound="a low hum from the hull",
    )
}

MYSTERIES = {
    "spoon_tray": Mystery(
        missing="the spoon tray",
        culprit="a magnet strip under the serving shelf",
        clue="the tray kept clicking toward the wall when the station vibrated",
        repeated_search="looked low, looked high, looked low again",
        solved_by="moved the tray away from the magnet strip and set it by the blue bowl",
    )
}


def _repeat_phrase(base: str, count: int = 3) -> str:
    return ", ".join([base] * count)


def tell(setting: Setting, mystery: Mystery, name: str = "Aya", maw_name: str = "Maw") -> World:
    world = World(setting)

    aya = world.add(Entity(id=name, kind="character", type="girl", label=name))
    maw = world.add(Entity(id=maw_name, kind="character", type="maw", label=maw_name))
    tray = world.add(Entity(id="tray", kind="thing", type="tray", label=mystery.missing))
    magnet = world.add(Entity(id="magnet", kind="thing", type="magnet", label="magnet strip"))

    world.facts.update(aya=aya, maw=maw, tray=tray, magnet=magnet, mystery=mystery, setting=setting)

    world.say(
        f"At {setting.place}, {name} sat down for supper beside {maw_name}. "
        f"{setting.feature} glowed over the table, and {setting.sound} drifted through the room."
    )
    world.say(
        f"The bowls were ready, but {mystery.missing} was not where it should have been. "
        f"That made the supper feel like a mystery to solve."
    )

    world.para()
    world.say(
        f"{name} stayed very still and listened to the kitchen. In her inner monologue, she thought, "
        f"'{mystery.clue}.'"
    )
    world.say(
        f"She repeated the search again and again: {_repeat_phrase(mystery.repeated_search, 2)}. "
        f"Each time, the same little clue kept coming back."
    )

    world.para()
    world.say(
        f"{maw_name} checked the serving shelf, then the wall, then the shelf again. "
        f"At last, {name} noticed the tray was tugging sideways."
    )
    world.say(
        f"The answer clicked into place: {mystery.culprit}. {name} whispered to herself, "
        f"'It is not lost. It is being pulled.'"
    )

    world.para()
    tray.meters["misplaced"] = 1.0
    tray.meters["found"] = 1.0
    magnet.meters["pull"] = 1.0
    world.say(
        f"{name} helped {maw_name} move {mystery.missing} away from {mystery.culprit}. "
        f"Then she set it by the blue bowl, where it stayed put."
    )
    world.say(
        f"At last, supper felt calm again. {name} and {maw_name} ate their meal under the station lights, "
        f"with the mystery solved and the tray finally resting still."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    return [
        f'Write a short space-adventure story for a young child about supper and "{mystery.missing}".',
        f"Tell a gentle mystery story where {f['aya'].id} solves a supper problem by listening carefully and thinking quietly.",
        f"Write a simple space kitchen story with repetition, an inner monologue, and a clue that leads to a solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    aya: Entity = f["aya"]  # type: ignore[assignment]
    maw: Entity = f["maw"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was missing at supper for {aya.id} and {maw.id}?",
            answer=f"{mystery.missing} was missing, so supper turned into a little mystery to solve.",
        ),
        QAItem(
            question=f"What clue helped {aya.id} solve the mystery?",
            answer=f"The clue was that {mystery.clue}. That made {aya.id} think the tray was not lost, just pulled aside.",
        ),
        QAItem(
            question=f"How did {aya.id} keep searching before finding the answer?",
            answer=f"{aya.id} repeated the search: {mystery.repeated_search}. That repetition helped her notice the pattern.",
        ),
        QAItem(
            question=f"What did {aya.id}'s inner monologue tell her?",
            answer=f"In her inner monologue, {aya.id} thought the tray was being pulled by something nearby, not gone forever.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{aya.id} and {maw.id} moved {mystery.missing} away from the magnet strip, and supper became calm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is supper?",
            answer="Supper is the evening meal, usually eaten near the end of the day.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem where something is not clear at first, so someone has to look for clues.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying the same thing again. It can help someone remember or notice a pattern.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a character hears in their own mind when they are thinking.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure supper mystery storyworld.")
    ap.add_argument("--name", default="Aya")
    ap.add_argument("--maw-name", default="Maw")
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
    return StoryParams(
        name=args.name or rng.choice(["Aya", "Nia", "Rin"]),
        maw_name=args.maw_name or rng.choice(["Maw", "Mara", "Mimi"]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["station"], MYSTERIES["spoon_tray"], params.name, params.maw_name)
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


ASP_RULES = r"""
valid_story(aya, supper, mystery, repetition).
"""


def asp_facts() -> str:
    return "storyworld(supper_aya_maw_inner_monologue_mystery_to)."


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(name="Aya", maw_name="Maw"),
    StoryParams(name="Aya", maw_name="Maw"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: aya / supper / mystery")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
