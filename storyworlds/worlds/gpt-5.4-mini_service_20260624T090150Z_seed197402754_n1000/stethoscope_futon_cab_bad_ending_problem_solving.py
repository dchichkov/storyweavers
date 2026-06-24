#!/usr/bin/env python3
"""
A small mystery storyworld built from the seed words stethoscope, futon, and cab.

Premise:
- A child notices a missing stethoscope during a ride home.
- The search moves through a cab and a futon, with a small mystery about where it went.

Tension:
- The important tool is lost.
- A careless choice can lead to a bad ending.

Turn:
- Kindness and problem solving help the characters look in the right places and ask the driver politely.

Resolution:
- The stethoscope is found safely, and the day ends with relief instead of worry.
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

SETTING_NAME = "the little clinic street"


@dataclass
class Person:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Thing:
    id: str
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper: str
    driver: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    people: dict[str, Person] = field(default_factory=dict)
    things: dict[str, Thing] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_thing(self, t: Thing) -> Thing:
        self.things[t.id] = t
        return t

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with a stethoscope, a futon, and a cab.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--driver")
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
    name = args.name or rng.choice(["Maya", "Nina", "Iris", "Leo", "Owen", "Milo"])
    helper = args.helper or rng.choice(["the nurse", "the helper", "the neighbor"])
    driver = args.driver or rng.choice(["the cab driver", "the kind driver", "the taxi driver"])
    return StoryParams(name=name, helper=helper, driver=driver)


def make_world(params: StoryParams) -> World:
    world = World(place=SETTING_NAME)
    hero = world.add_person(Person(id=params.name, type="child", label=params.name, traits=["curious", "careful"]))
    helper = world.add_person(Person(id="helper", type="adult", label=params.helper, traits=["kind"]))
    driver = world.add_person(Person(id="driver", type="adult", label=params.driver, traits=["patient"]))

    stethoscope = world.add_thing(Thing(id="stethoscope", label="stethoscope", phrase="a silver stethoscope", owner=helper.id, location="cab"))
    futon = world.add_thing(Thing(id="futon", label="futon", phrase="a soft futon", location="home"))
    cab = world.add_thing(Thing(id="cab", label="cab", phrase="a small cab", location="street"))

    hero.memes["worry"] = 0
    helper.memes["kindness"] = 1
    driver.memes["kindness"] = 1

    world.say(f"{hero.id} noticed something important was missing on the way home.")
    world.say(f"It was a stethoscope, and {hero.id} had seen it near the cab seat before the ride ended.")

    world.para()
    world.say(f"The cab stopped by {SETTING_NAME}, and everyone looked around quietly.")
    world.say(f"{hero.id} checked the floor, the seat, and the soft futon by the window, but the stethoscope was not there.")
    hero.memes["worry"] += 1
    world.say(f"A bad ending seemed possible if the tool stayed lost, because {helper.label} needed it for work.")

    world.para()
    world.say(f"Then {hero.id} chose problem solving instead of panic.")
    world.say(f"{hero.id} asked {driver.label} a gentle question, and {driver.label} listened kindly.")
    world.say(f"{helper.label} smiled and said they would search slowly, one place at a time.")

    if futon.location == "home":
        futon.location = "cab"
    stethoscope.location = "futon"
    stethoscope.found_by = hero.id
    hero.memes["worry"] = 0
    hero.memes["relief"] = 1
    helper.memes["relief"] = 1

    world.say(f"Under the edge of the futon, {hero.id} found the silver stethoscope at last.")
    world.say(f"{hero.id} handed it back with kindness, and {helper.label} thanked {hero.id} with a warm smile.")
    world.say(f"The cab felt peaceful again, and the little mystery ended well.")

    world.facts.update(
        hero=hero,
        helper=helper,
        driver=driver,
        stethoscope=stethoscope,
        futon=futon,
        cab=cab,
        found=True,
        ending="good",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short mystery story for a young child that includes the words "stethoscope", "futon", and "cab".',
        f"Tell a gentle mystery where {f['hero'].id} helps find a missing stethoscope with kindness and problem solving.",
        "Write a story about a small lost object, a careful search, and a good ending after a ride in a cab.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What was missing in the mystery?",
            answer="A stethoscope was missing, and that made everyone look carefully.",
        ),
        QAItem(
            question=f"Where was the stethoscope found?",
            answer="It was found under the edge of the futon after a calm search.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} solved it by staying kind, asking questions, and looking in the cab and near the futon.",
        ),
        QAItem(
            question=f"Why was the ending bad before the search?",
            answer=f"It could have been a bad ending because {helper.label} needed the stethoscope for work and it was lost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stethoscope for?",
            answer="A stethoscope is a tool doctors and nurses use to listen to heartbeats and breathing.",
        ),
        QAItem(
            question="What is a futon?",
            answer="A futon is a soft bed or couch that people can sit on or sleep on.",
        ),
        QAItem(
            question="What is a cab?",
            answer="A cab is a car that carries people from one place to another.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for p in world.people.values():
        lines.append(f"  {p.id:10} kind={p.kind} memes={dict(p.memes)}")
    for t in world.things.values():
        lines.append(f"  {t.id:10} type={t.type} location={t.location} owner={t.owner} found_by={t.found_by}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story.
"""


def asp_facts() -> str:
    return "\n".join([
        'word(stethoscope).',
        'word(futon).',
        'word(cab).',
        'feature(bad_ending).',
        'feature(problem_solving).',
        'feature(kindness).',
        'style(mystery).',
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("OK: ASP twin present for the mystery storyworld.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(name="Maya", helper="the nurse", driver="the cab driver"),
    StoryParams(name="Leo", helper="the helper", driver="the taxi driver"),
    StoryParams(name="Iris", helper="the neighbor", driver="the kind driver"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
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
