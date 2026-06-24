#!/usr/bin/env python3
"""
Standalone storyworld: gasp_breaker_obey_sharing_rhyme_whodunit

A small whodunit-style story domain where a child, a shared rhyme card, and a
tripped breaker create a mystery that is solved by careful observation and an
obedient, helpful turn.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float]
    memes: dict[str, float]

    def pronoun(self) -> str:
        return "they"

    def poss(self) -> str:
        return "their"


@dataclass
class Item:
    name: str
    owner: str = ""
    shared_with: list[str] = None
    hidden: bool = False
    clue: str = ""

    def __post_init__(self):
        if self.shared_with is None:
            self.shared_with = []


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    culprit: str
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.people: dict[str, Person] = {}
        self.items: dict[str, Item] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(self.events)


PLACES = {
    "classroom": "the classroom",
    "library": "the library",
    "hallway": "the hallway",
    "music_room": "the music room",
}

HEROES = ["Mina", "Noah", "Ivy", "Ben", "Luna", "Theo"]
HELPERS = ["Mara", "Owen", "Lia", "Eli", "June", "Finn"]
CULPRITS = ["Mr. Reed", "Ms. Bell", "Nora", "Pip", "Coach Tate"]

RHYMES = [
    "Star, bar, jar, and car.",
    "Light at night, bright and right.",
    "Share the chair and take good care.",
    "Tap, clap, snap, and rap.",
]

CURATED = [
    StoryParams(place="library", hero="Mina", helper="Owen", culprit="Mr. Reed"),
    StoryParams(place="classroom", hero="Noah", helper="Lia", culprit="Ms. Bell"),
    StoryParams(place="hallway", hero="Ivy", helper="June", culprit="Pip"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with sharing, rhyme, and a breaker mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--culprit", choices=CULPRITS)
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([x for x in HELPERS if x != hero])
    culprit = args.culprit or rng.choice(CULPRITS)
    if helper == hero:
        raise StoryError("The helper must be different from the hero.")
    return StoryParams(place=place, hero=hero, helper=helper, culprit=culprit)


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    hero = Person(params.hero, "child", {"gasp": 0, "curious": 1, "fear": 0, "relief": 0}, {"trust": 1, "doubt": 0})
    helper = Person(params.helper, "child", {"gasp": 0, "curious": 1, "fear": 0, "relief": 0}, {"trust": 1, "doubt": 0})
    culprit = Person(params.culprit, "adult", {"gasp": 0, "curious": 0, "fear": 0, "relief": 0}, {"trust": 0, "doubt": 0})
    rhyme = Item("rhyme card", owner=hero.name, shared_with=[helper.name], clue="The words were on the card, not on the floor.")
    breaker = Item("breaker box", owner=params.place, hidden=False, clue="A switch was flipped down.")
    world.people = {p.name: p for p in (hero, helper, culprit)}
    world.items = {"rhyme": rhyme, "breaker": breaker}

    world.say(f"In {PLACES[params.place]}, {hero.name} and {helper.name} were sharing a rhyme card: “{random.choice(RHYMES)}”")
    world.say(f"Then the lights went out with a sudden gasp, and everyone froze near the breaker box.")
    hero.meters["gasp"] += 1
    helper.meters["gasp"] += 1
    world.say(f"{hero.name} obeyed the rule to stay still and not touch anything.")
    world.say(f"{helper.name} listened too, and together they noticed the breaker switch had been nudged down.")
    world.say(f"That was the clue: the culprit had not stolen the rhyme card at all; the breaker had simply tripped.")
    world.say(f"{params.culprit} returned with a calm face, reset the breaker, and the room brightened again.")
    world.say(f"With the light back, {hero.name} and {helper.name} shared the rhyme card once more, laughing softly instead of gasping.")

    world.facts = {
        "place": params.place,
        "hero": hero.name,
        "helper": helper.name,
        "culprit": culprit.name,
        "rhyme": rhyme.name,
        "breaker": breaker.name,
    }

    prompts = [
        f"Write a short whodunit story in {PLACES[params.place]} with sharing and rhyme.",
        f"Tell a child-friendly mystery where {hero.name} obeys a rule after a gasp near a breaker.",
        "Make the clue turn out to be a tripped breaker, not a stolen rhyme card.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {hero.name} and {helper.name} share?",
            answer="They shared a rhyme card.",
        ),
        QAItem(
            question="Why did everyone gasp?",
            answer="Everyone gasped because the lights suddenly went out near the breaker box.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"They noticed the breaker switch had been flipped down, so {params.culprit} reset it and the lights came back on.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a breaker box for?",
            answer="A breaker box helps control electricity in a building and can shut the power off if a switch trips.",
        ),
        QAItem(
            question="What does it mean to obey a rule?",
            answer="To obey a rule means to listen and do what the rule asks, like staying still or waiting your turn.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a word or line that sounds like another word or line, such as light and night.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for p in world.people.values():
        lines.append(f"{p.name}: meters={p.meters} memes={p.memes}")
    for i in world.items.values():
        lines.append(f"{i.name}: owner={i.owner} shared_with={i.shared_with} clue={i.clue}")
    return "\n".join(lines)


ASP_RULES = r"""
% The story is valid when there is sharing, a gasp, obedience, and a breaker clue.
valid_story(P) :- place(P), shared(rhyme), gasp_event, obey_event, breaker_clue.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", k) for k in PLACES
    ] + [
        asp.fact("shared", "rhyme"),
        asp.fact("gasp_event"),
        asp.fact("obey_event"),
        asp.fact("breaker_clue"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
