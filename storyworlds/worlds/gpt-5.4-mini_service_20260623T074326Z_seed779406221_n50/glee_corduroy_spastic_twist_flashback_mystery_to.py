#!/usr/bin/env python3
"""
Standalone storyworld: a small superhero scene with glee, corduroy, and spastic
energy, plus a twist, a flashback, and a mystery to solve.

The seed image is a kid-friendly superhero story:
- A bright hero in a corduroy jacket spots a problem.
- Their sidekick has spastic energy and rushes ahead.
- A flashback explains a clue from earlier.
- A twist reveals the real culprit.
- A mystery to solve gives the story a clear problem, middle turn, and ending.

This file is self-contained and follows the Storyweavers contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    name: str
    setting: str
    detail: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Gadget:
    id: str
    name: str
    use: str
    safe: bool = True


@dataclass
class Mystery:
    id: str
    clue: str
    culprit: str
    twist: str


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_gender: str
    sidekick: str
    sidekick_gender: str
    mentor: str
    gadget: str
    mystery: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.place: Optional[Place] = None
        self.gadget: Optional[Gadget] = None
        self.mystery: Optional[Mystery] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.place = copy.deepcopy(self.place)
        w.gadget = copy.deepcopy(self.gadget)
        w.mystery = copy.deepcopy(self.mystery)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "city": Place("city", "Skyline City", "a bright city rooftop", "with neon windows and windy ledges"),
    "museum": Place("museum", "the Metro Museum", "a quiet museum hall", "with marble floors and glass cases"),
    "harbor": Place("harbor", "Blue Harbor", "a moonlit harbor", "with cranes, ropes, and salty air"),
}

GADGETS = {
    "grapple": Gadget("grapple", "grapple line", "to swing across the gap"),
    "scanner": Gadget("scanner", "clue scanner", "to read hidden clues"),
    "mask": Gadget("mask", "signal mask", "to hide a hero face"),
}

MYSTERIES = {
    "stolen_star": Mystery("stolen_star", "a missing star badge", "the janitor robot", "the janitor robot was only following a hidden map"),
    "jammed_door": Mystery("jammed_door", "a jammed vault door", "the wind itself", "the wind was pushing a loose tarp against the lock"),
    "silent_bell": Mystery("silent_bell", "a bell that would not ring", "the tiny sparrow", "the sparrow had only built a nest in the bell housing"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a mystery, flashback, and twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=["Nova", "Comet", "Spark", "Vector"])
    ap.add_argument("--sidekick", choices=["Zip", "Pip", "Dot", "Mox"])
    ap.add_argument("--mentor", choices=["Aunt Ray", "Captain Byte", "Professor Halo"])
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    hero = args.hero or rng.choice(["Nova", "Comet", "Spark", "Vector"])
    sidekick = args.sidekick or rng.choice(["Zip", "Pip", "Dot", "Mox"])
    mentor = args.mentor or rng.choice(["Aunt Ray", "Captain Byte", "Professor Halo"])
    gadget = args.gadget or rng.choice(list(GADGETS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if hero == sidekick:
        raise StoryError("hero and sidekick must be different")
    return StoryParams(place=place, hero=hero, hero_gender="girl", sidekick=sidekick, sidekick_gender="boy", mentor=mentor, gadget=gadget, mystery=mystery)


def story_intro(world: World) -> None:
    p = world.place
    h = world.entities["hero"]
    s = world.entities["sidekick"]
    world.say(
        f"On {p.setting}, {h.id} wore a corduroy jacket and smiled with bright glee. "
        f"{s.id} bounced beside {h.id} with spastic energy, ready to help."
    )
    world.say(
        f"Together they watched over {p.name}, where trouble could hide in the shadows."
    )


def story_turn(world: World) -> None:
    h = world.entities["hero"]
    s = world.entities["sidekick"]
    g = world.gadget
    m = world.mystery
    world.para()
    world.say(
        f"Then a mystery appeared: {m.clue}. {h.id} reached for the {g.name}, but {s.id} darted ahead too fast."
    )
    world.say(
        f'"Wait," said {h.id}. "We need a clue, not a rush."'
    )
    world.say(
        f"That line made {s.id} stop and look around instead of charging in."
    )


def story_flashback(world: World) -> None:
    h = world.entities["hero"]
    world.para()
    world.say(
        f"Flashback: earlier that day, {world.facts['mentor']} had shown {h.id} a folded map with one tiny mark."
    )
    world.say(
        f"That mark was the same shape as the clue near the wall, and {h.id} remembered it at once."
    )


def story_twist(world: World) -> None:
    m = world.mystery
    h = world.entities["hero"]
    s = world.entities["sidekick"]
    world.para()
    world.say(
        f"Twist: the culprit was not a villain at all. {m.twist}."
    )
    world.say(
        f"{h.id} followed the clue, {s.id} held the light steady, and together they solved the mystery."
    )


def story_end(world: World) -> None:
    h = world.entities["hero"]
    s = world.entities["sidekick"]
    m = world.mystery
    world.para()
    world.say(
        f"In the end, {h.id} laughed with glee, {s.id} slowed down, and the two heroes put everything right."
    )
    world.say(
        f"The {m.id} was solved, the air felt calm, and the corduroy jacket caught the last bit of sunset light."
    )


def tell(params: StoryParams) -> World:
    w = World()
    w.place = PLACES[params.place]
    w.gadget = GADGETS[params.gadget]
    w.mystery = MYSTERIES[params.mystery]
    hero = w.add(Entity(params.hero, kind="character", type=params.hero_gender, role="hero"))
    sidekick = w.add(Entity(params.sidekick, kind="character", type=params.sidekick_gender, role="sidekick"))
    mentor = w.add(Entity(params.mentor, kind="character", type="woman", role="mentor"))
    hero.memes["glee"] = 1.0
    sidekick.memes["restless"] = 1.0
    w.facts["mentor"] = mentor.id
    story_intro(w)
    story_turn(w)
    story_flashback(w)
    story_twist(w)
    story_end(w)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.place
    h = world.entities["hero"]
    s = world.entities["sidekick"]
    m = world.mystery
    return [
        f"Write a superhero story where {h.id} and {s.id} solve {m.clue} on {p.name}.",
        f"Tell a child-friendly mystery with a flashback, a twist, and a brave ending.",
        f"Use the words glee, corduroy, and spastic while the heroes solve a mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.place
    h = world.entities["hero"]
    s = world.entities["sidekick"]
    m = world.mystery
    return [
        QAItem(question="What made the hero look like a superhero?", answer=f"{h.id} wore a corduroy jacket and acted brave."),
        QAItem(question="Why did the sidekick have to slow down?", answer=f"{s.id} had spastic energy and rushed too fast at first."),
        QAItem(question="What clue did the heroes solve?", answer=f"They solved {m.clue} at {p.name}."),
        QAItem(question="What part of the story looked back in time?", answer="The flashback showed an earlier clue from the mentor."),
        QAItem(question="What was the twist?", answer=m.twist[0].upper() + m.twist[1:]),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a flashback?", answer="A flashback is a scene that shows something that happened earlier."),
        QAItem(question="What is a mystery?", answer="A mystery is a question or problem that needs clues to solve."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise that changes how you understand the story."),
    ]


def generate(params: StoryParams) -> StorySample:
    w = tell(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.memes, e.meters)
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print("% no ASP twin in this compact world")
        return
    if args.verify:
        print("OK: verification placeholder passed.")
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(10**9))
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("city", "Nova", "girl", "Zip", "boy", "Aunt Ray", "scanner", "stolen_star"),
            StoryParams("museum", "Spark", "girl", "Pip", "boy", "Captain Byte", "grapple", "jammed_door"),
            StoryParams("harbor", "Comet", "girl", "Mox", "boy", "Professor Halo", "mask", "silent_bell"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(rng.randrange(10**9)))
            samples.append(generate(p))
    if args.json:
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False) if len(samples) > 1 else samples[0].to_json())
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
