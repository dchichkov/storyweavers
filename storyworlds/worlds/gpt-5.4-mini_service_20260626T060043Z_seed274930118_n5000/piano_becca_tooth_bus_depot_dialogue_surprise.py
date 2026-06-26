#!/usr/bin/env python3
"""
Story world: Becca, the piano, the bus depot, and a tall-tale surprise.

A small simulated story domain with dialogue, surprise, and flashback.
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
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the bus depot"
    afford: set[str] = field(default_factory=lambda: {"wait", "play_piano", "load_piano"})


@dataclass
class Action:
    id: str
    verb: str
    outcome: str
    risk: str
    surprise: str
    flashback_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "bus_depot"
    action: str = "play"
    object: str = "piano"
    name: str = "Becca"
    seed: Optional[int] = None


SETTING = Setting()
ACTIONS = {
    "play": Action(
        id="play",
        verb="play the piano",
        outcome="make the whole depot sing",
        risk="the bus would leave before the music was done",
        surprise="the piano was hiding a second sound inside it",
        flashback_hint="Grandpa had once told her that a real song can turn a waiting room into a parade",
        tags={"piano", "dialogue", "surprise", "flashback"},
    )
}
OBJECTS = {
    "piano": Entity(
        id="piano",
        kind="thing",
        label="piano",
        phrase="a grand old piano with a lid like a black river",
        type="piano",
        location="bus depot",
    ),
}
NAMES = ["Becca"]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def _hero_line(name: str) -> str:
    return name


def build_world(params: StoryParams) -> World:
    if params.place != "bus_depot" or params.object != "piano" or params.action != "play":
        raise StoryError("This little world only knows a bus depot story about Becca and the piano.")

    world = World()
    becca = world.add(Entity(id=params.name, kind="character", type="girl", label="Becca", location=SETTING.place))
    bus_driver = world.add(Entity(id="driver", kind="character", type="adult", label="the bus driver", location=SETTING.place))
    piano = world.add(Entity(id="piano", kind="thing", label="piano", phrase="a grand old piano", location=SETTING.place))
    tooth = world.add(Entity(id="tooth", kind="thing", label="tooth", phrase="a loose tooth", location="becca_mouth"))

    becca.memes["want"] = 2
    becca.memes["wonder"] = 1
    becca.meters["heartbeat"] = 1
    piano.meters["weight"] = 5
    piano.meters["shine"] = 2
    tooth.meters["loose"] = 1

    world.facts.update(hero=becca, driver=bus_driver, piano=piano, tooth=tooth, action=ACTIONS["play"], setting=SETTING)
    return world


def tell_story(world: World) -> str:
    f = world.facts
    becca: Entity = f["hero"]  # type: ignore[assignment]
    driver: Entity = f["driver"]  # type: ignore[assignment]
    piano: Entity = f["piano"]  # type: ignore[assignment]
    tooth: Entity = f["tooth"]  # type: ignore[assignment]
    action: Action = f["action"]  # type: ignore[assignment]

    world.say(f"At the bus depot, {becca.label} found {piano.phrase} waiting under the timetable board.")
    world.say(f'She grinned so wide that her loose {tooth.label} wiggled and said, "Today feels like a song with boots on it."')
    world.say(f'"Can I play it before the bus comes?" {becca.label} asked.')
    world.say(f'"You can try," said {driver.label}, "but that old piano is as stubborn as a mule in a thunderstorm."')

    world.say(f"{becca.label} sat on the bench and played anyway, and the depot gave back a note so deep it rattled the candy jar.")
    world.say(f"Then came a surprise: {action.surprise}.")
    world.say(f"As the keys trembled, {tooth.label} popped free, landed on middle C, and rang like a tiny silver bell.")
    world.say(f'{driver.label} blinked. "Well butter my hat," he said, "that is the brightest tooth I ever heard make music."')

    world.say(f"That sound brought back a flashback for {becca.label}: {action.flashback_hint}.")
    world.say(f'She remembered the lesson, nodded, and said, "A song can wait for a bus, but it should never be locked in a box."')

    world.say(f'So {driver.label} opened the cargo bay, and together they rolled the piano aboard with a careful heave and a cheerful count.')
    world.say(f"By the time the bus growled away, {becca.label} had a new grin, a safe little envelope for the tooth, and a piano riding toward town like it owned the road.")
    return world.render()


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall-tale style story set in a bus depot with dialogue, a surprise, and a flashback.',
        'Tell a child-friendly story about Becca, a piano, and a loose tooth at the bus depot.',
        'Write a short whimsical story where a bus depot piano becomes part of an unexpected adventure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Where was Becca when the story happened?",
            answer="Becca was at the bus depot, where the timetable board hung above the waiting area and the bus was almost ready to leave.",
        ),
        QAItem(
            question="What did Becca want to do with the piano?",
            answer="Becca wanted to play the piano before the bus came, because she thought the depot should hear one good song first.",
        ),
        QAItem(
            question="What unexpected thing happened with Becca's tooth?",
            answer="Becca's loose tooth popped free during the music and landed on middle C, where it made a bright little ringing sound.",
        ),
        QAItem(
            question="Why did the story have a flashback?",
            answer="The flashback reminded Becca of Grandpa's advice that a real song can turn a waiting room into a parade, which helped her keep going.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The bus driver opened the cargo bay, the piano was loaded safely, and Becca rode away with a new grin and her tooth tucked into an envelope.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses stop, wait, load people or things, and get ready to travel.",
        ),
        QAItem(
            question="What is a piano?",
            answer="A piano is a musical instrument with keys that make sounds when you press them.",
        ),
        QAItem(
            question="What is a loose tooth?",
            answer="A loose tooth is a tooth that wiggles in a mouth before it falls out and makes room for a new one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(bus_depot).
character(becca).
thing(piano).
thing(tooth).
action(play).

valid_story(bus_depot, becca, piano, tooth) :- place(bus_depot), character(becca), thing(piano), thing(tooth), action(play).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "bus_depot"),
            asp.fact("character", "becca"),
            asp.fact("thing", "piano"),
            asp.fact("thing", "tooth"),
            asp.fact("action", "play"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("bus_depot", "becca", "piano", "tooth")}
    clingo = set(asp_valid())
    if py == clingo:
        print("OK: ASP and Python parity match.")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("asp:", sorted(clingo))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.location:
            bits.append(f"location={ent.location}")
        lines.append(f"{ent.id}: {ent.kind} {', '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: Becca, a piano, and a bus depot surprise.")
    ap.add_argument("--place", choices=["bus_depot"], default=None)
    ap.add_argument("--action", choices=["play"], default=None)
    ap.add_argument("--object", choices=["piano"], default=None)
    ap.add_argument("--name", choices=NAMES, default=None)
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
    if args.place and args.place != "bus_depot":
        raise StoryError("This story only happens at the bus depot.")
    if args.action and args.action != "play":
        raise StoryError("This story only supports playing the piano.")
    if args.object and args.object != "piano":
        raise StoryError("This story only supports the piano.")
    return StoryParams(
        place="bus_depot",
        action="play",
        object="piano",
        name=args.name or "Becca",
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = tell_story(world)
    return StorySample(
        params=params,
        story=story,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story:")
        for row in asp_valid():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(place="bus_depot", action="play", object="piano", name="Becca", seed=base_seed)
        samples = [generate(params)]
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
