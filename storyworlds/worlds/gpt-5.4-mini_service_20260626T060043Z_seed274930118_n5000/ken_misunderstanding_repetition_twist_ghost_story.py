#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ken_misunderstanding_repetition_twist_ghost_story.py
================================================================================================

A tiny ghost-story world with a child-facing, state-driven premise:
Ken hears something strange in a quiet house, mistakes the spooky repeats
for a warning, and learns that the "ghost" is not scary at all.

Story shape:
- Beginning: Ken enters a quiet place with an eerie sound.
- Middle: repeated tapping and whispers cause a misunderstanding.
- Turn: the ghost's odd pattern is explained.
- Ending: the truth changes the mood from scared to relieved.

This world keeps the tale close to a classic ghost story, but the fright is
soft and the resolution is warm and concrete.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""
    visible: bool = True

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    eerie: bool = False
    repeat_sound: str = "tap"
    twist_sound: str = "tap tap"


@dataclass
class StoryParams:
    place: str
    name: str = "Ken"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _event_key(*parts: object) -> tuple:
    return tuple(parts)


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    ken = world.add(Entity(id=params.name, kind="character", type="boy", label=params.name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="a ghost", visible=False))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="a small lantern", owner=ken.id))
    world.facts.update(ken=ken, ghost=ghost, lantern=lantern, place=place)
    return world


def opening(world: World) -> None:
    ken: Entity = world.facts["ken"]
    place: Place = world.facts["place"]
    world.say(f"{ken.label} came to {place.label} when the house was very quiet.")
    world.say(f"At first, the only sound was a tiny {place.repeat_sound} from somewhere in the dark.")


def build_misunderstanding(world: World) -> None:
    ken: Entity = world.facts["ken"]
    place: Place = world.facts["place"]
    ghost: Entity = world.facts["ghost"]
    ken.memes["unease"] = ken.memes.get("unease", 0.0) + 1
    ken.memes["curiosity"] = ken.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{ken.label} heard {place.repeat_sound} again and then again, and {ken.pronoun()} "
        f"thought the house was trying to whisper a warning."
    )
    world.say(
        f"That was the misunderstanding: the sound seemed spooky, so {ken.label} imagined "
        f"a ghost hiding nearby."
    )
    ghost.meters["nearby"] = 1
    ghost.memes["mischief"] = 1


def repetition(world: World) -> None:
    place: Place = world.facts["place"]
    ken: Entity = world.facts["ken"]
    world.say(f"Then the sound came back: {place.repeat_sound}.")
    world.say(f"Again: {place.repeat_sound}. Again: {place.repeat_sound}.")
    ken.memes["fear"] = ken.memes.get("fear", 0.0) + 1


def twist(world: World) -> None:
    ken: Entity = world.facts["ken"]
    ghost: Entity = world.facts["ghost"]
    lantern: Entity = world.facts["lantern"]
    place: Place = world.facts["place"]
    ghost.visible = True
    ghost.label = "the friendly ghost"
    ghost.meters["nearby"] = 0
    ghost.memes["mischief"] = 0
    lantern.visible = True
    ken.memes["fear"] = max(0.0, ken.memes.get("fear", 0.0) - 1)
    ken.memes["relief"] = ken.memes.get("relief", 0.0) + 1
    world.say(
        f"At last, the twist appeared: the ghost was not trying to scare {ken.label} at all."
    )
    world.say(
        f"It was softly knocking the old wall in a pattern so someone could find the hidden "
        f"lantern, and the little {place.twist_sound} was only a clue."
    )
    world.say(
        f"{ken.label} picked up {lantern.label}, and the dark room stopped feeling spooky."
    )


def ending(world: World) -> None:
    ken: Entity = world.facts["ken"]
    place: Place = world.facts["place"]
    world.say(
        f"{ken.label} smiled at the friendly ghost, and the quiet house felt warm instead of scary."
    )
    world.say(
        f"By the end, the repeated tapping had turned into a useful clue, and {ken.label} walked "
        f"home with a bright lantern and a brave new story to tell about {place.label}."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    opening(world)
    world.para()
    build_misunderstanding(world)
    repetition(world)
    world.para()
    twist(world)
    ending(world)
    return world


SETTINGS = {
    "old_house": Place(id="old_house", label="the old house", eerie=True, repeat_sound="tap", twist_sound="tap tap"),
    "attic": Place(id="attic", label="the attic", eerie=True, repeat_sound="thump", twist_sound="thump thump"),
    "garden_shed": Place(id="garden_shed", label="the garden shed", eerie=True, repeat_sound="scratch", twist_sound="scratch scratch"),
}


@dataclass
class StoryModel:
    place: str = "old_house"
    name: str = "Ken"


def generation_prompts(world: World) -> list[str]:
    place: Place = world.facts["place"]
    ken: Entity = world.facts["ken"]
    return [
        f"Write a gentle ghost story about {ken.label} in {place.label} with a misunderstanding, repetition, and a twist.",
        f"Tell a child-friendly spooky story where {ken.label} hears {place.repeat_sound} again and again before learning the truth.",
        f"Create a short ghost story about a quiet place, a repeated sound, and a friendly explanation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    ken: Entity = world.facts["ken"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {ken.label}, who goes to {place.label} and hears a strange sound.",
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=f"The misunderstanding happened because {ken.label} heard the repeated {place.repeat_sound} sound and thought a ghost was warning him.",
        ),
        QAItem(
            question="What was the twist at the end?",
            answer=f"The twist was that the ghost was friendly and was using the repeated sound to help {ken.label} find a lantern.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is often a spooky-looking character, but in a gentle story it can be friendly or helpful.",
        ),
        QAItem(
            question="What does repetition do in a story?",
            answer="Repetition repeats a word or sound more than once, which can make a story feel spooky, funny, or memorable.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals something the reader did not expect.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if not e.visible:
            bits.append("hidden")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.eerie:
            lines.append(asp.fact("eerie", pid))
        lines.append(asp.fact("repeat_sound", pid, place.repeat_sound))
        lines.append(asp.fact("twist_sound", pid, place.twist_sound))
    return "\n".join(lines)


ASP_RULES = r"""
% A place is suitable for the ghost story if it is eerie.
ghost_story(P) :- place(P), eerie(P).

% Repetition is present when the same sound is heard more than once.
repetition(P) :- repeat_sound(P, S), twist_sound(P, T), S != T.

% A twist exists when the final explanation changes the meaning of the sound.
twist(P) :- ghost_story(P), repetition(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show ghost_story/1."))
    return sorted(set(asp.atoms(model, "ghost_story")))


def asp_verify() -> int:
    python_set = {p for p, in [(pid,) for pid, pl in PLACES.items() if pl.eerie]}
    clingo_set = set(asp_valid_places())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python eerie places ({len(clingo_set)}).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("only in python:", sorted(python_set - clingo_set))
    print("only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about Ken, repetition, and a twist.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name", default="Ken")
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
    place = args.place or rng.choice(sorted(PLACES.keys()))
    return StoryParams(place=place, name=args.name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


PLACES = {
    "old_house": Place(id="old_house", label="the old house", eerie=True, repeat_sound="tap", twist_sound="tap tap"),
    "attic": Place(id="attic", label="the attic", eerie=True, repeat_sound="thump", twist_sound="thump thump"),
    "garden_shed": Place(id="garden_shed", label="the garden shed", eerie=True, repeat_sound="scratch", twist_sound="scratch scratch"),
}


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ghost_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(f"{p[0]}" for p in asp_valid_places()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(PLACES.keys()):
            params = StoryParams(place=place, name=args.name, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
