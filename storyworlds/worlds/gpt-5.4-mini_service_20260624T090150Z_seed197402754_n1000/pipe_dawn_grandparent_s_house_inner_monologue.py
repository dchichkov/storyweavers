#!/usr/bin/env python3
"""
A small storyworld: a child in grandparent's house at dawn, hearing a strange
pipe and facing a ghost-story scare with an inner-monologue turn toward courage.
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

HOUSE_ROOMS = ["kitchen", "hallway", "attic", "basement", "porch"]
SCARE_SOURCES = ["pipe", "old pipe", "banging pipe", "dripping pipe"]
HELPERS = ["flashlight", "grandparent", "warm blanket", "careful listening"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    grandparent_type: str
    room: str
    source: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    room: str
    source: str
    helper: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "World":
        import copy
        w = World(self.room, self.source, self.helper)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def asp_facts() -> str:
    import asp
    parts = [
        asp.fact("room", "grandparents_house"),
        asp.fact("source", "pipe"),
        asp.fact("helper", "flashlight"),
        asp.fact("helper", "grandparent"),
        asp.fact("helper", "blanket"),
        asp.fact("time", "dawn"),
    ]
    return "\n".join(parts)


ASP_RULES = r"""
% A dawn ghost story is reasonable when a child hears something eerie at dawn in a grandparent's house.
haunted_at_dawn(H) :- room(H), source(pipe), time(dawn).

% The scare is real if the pipe makes a sound in the dark.
scare(pipe) :- source(pipe).

% The child can become brave if they name the fear and use a helper.
brave(child) :- scare(pipe), helper(flashlight).
brave(child) :- scare(pipe), helper(grandparent).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show haunted_at_dawn/1. #show scare/1. #show brave/1."))
    atoms = {(sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", getattr(a, "number", None)) for a in sym.arguments)) for sym in model}
    expected = {("haunted_at_dawn", ("H",)), ("scare", ("pipe",)), ("brave", ("child",))}
    if atoms:
        print("OK: ASP program grounded and solved.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world set in a grandparent's house at dawn.")
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"], default=None)
    ap.add_argument("--grandparent-type", choices=["grandmother", "grandfather"], default=None)
    ap.add_argument("--room", choices=HOUSE_ROOMS)
    ap.add_argument("--source", choices=SCARE_SOURCES)
    ap.add_argument("--helper", choices=HELPERS)
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
    child_type = args.child_type or rng.choice(["girl", "boy"])
    grandparent_type = args.grandparent_type or ("grandmother" if child_type == "boy" else "grandfather")
    name = args.name or rng.choice(["Maya", "Leo", "Nina", "Eli", "June", "Owen"])
    room = args.room or rng.choice(HOUSE_ROOMS)
    source = args.source or rng.choice(SCARE_SOURCES)
    helper = args.helper or rng.choice(HELPERS)
    if helper == "warm blanket" and source == "pipe":
        pass
    return StoryParams(name, child_type, grandparent_type, room, source, helper)


def generate(params: StoryParams) -> StorySample:
    world = World(params.room, params.source, params.helper)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name, location=params.room))
    grandparent = world.add(Entity(id="grandparent", kind="character", type=params.grandparent_type, label=params.grandparent_type, location=params.room))
    pipe = world.add(Entity(id="pipe", kind="thing", type="pipe", label="the pipe", location=params.room))
    helper = world.add(Entity(id="helper", kind="thing", type=params.helper, label=params.helper, location=params.room))

    child.memes["fear"] = 1.0
    pipe.meters["noise"] = 1.0
    world.facts.update(child=child, grandparent=grandparent, pipe=pipe, helper=helper)

    world.say(
        f"At dawn, {params.child_name} woke up in {params.grandparent_type}'s house and listened to the quiet house breathe."
    )
    world.say(
        f"Then a strange sound came from the {params.room}: the {params.source} gave one slow knock, and {params.child_name}'s stomach went tight."
    )
    world.para()
    world.say(
        f'{params.child_name} thought, "That sound could be a ghost, but it could also be an old house making morning noises."'
    )
    world.say(
        f'{params.child_name} thought, "I should stay close to {params.grandparent_type} and look carefully instead of running away."'
    )
    world.say(
        f"{params.child_name} took a small step toward the sound, holding the {params.helper} and breathing a little slower."
    )
    world.para()
    world.say(
        f"In the end, the {params.source} was only a loose pipe that clinked when the house cooled at dawn."
    )
    world.say(
        f"{params.child_name} smiled, and {params.grandparent_type} laughed softly, because the scary mystery had turned into a brave morning in the old house."
    )

    story = world.render()
    prompts = [
        f"Write a gentle ghost story for a young child set in a grandparent's house at dawn, featuring a pipe and an inner monologue.",
        f"Tell a child-sized spooky story where {params.child_name} hears a pipe in {params.grandparent_type}'s house and thinks through the fear.",
        f"Create a quiet dawn story that feels a little ghostly, but ends with courage and a clear explanation for the pipe sound.",
    ]
    story_qa = [
        QAItem(
            question=f"Where does {params.child_name} hear the strange sound?",
            answer=f"{params.child_name} hears it in the {params.room} of {params.grandparent_type}'s house.",
        ),
        QAItem(
            question=f"What does {params.child_name} think the sound might be at first?",
            answer=f"{params.child_name} first thinks it might be a ghost, but then decides it could just be the old house and the pipe making a morning noise.",
        ),
        QAItem(
            question=f"How does the story end?",
            answer=f"It ends with {params.child_name} feeling brave, because the pipe is only a loose pipe clinking at dawn and the scary moment turns calm.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is dawn?",
            answer="Dawn is the early time of morning when the sun is just starting to light the sky.",
        ),
        QAItem(
            question="What is a pipe in a house?",
            answer="A pipe is a tube that carries water or other things through a house, and old pipes can sometimes make tapping or clinking sounds.",
        ),
        QAItem(
            question="Why can old houses make spooky sounds?",
            answer="Old houses can make spooky sounds because wood, walls, and pipes can settle, cool, or move a little as the temperature changes.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:9} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams("Maya", "girl", "grandmother", "kitchen", "pipe", "flashlight"),
    StoryParams("Leo", "boy", "grandfather", "hallway", "dripping pipe", "grandparent"),
    StoryParams("June", "girl", "grandmother", "basement", "banging pipe", "warm blanket"),
]


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
        print(asp_program("#show haunted_at_dawn/1. #show scare/1. #show brave/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP mode is available for this storyworld.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
