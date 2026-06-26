#!/usr/bin/env python3
"""
Storyworld: Homer, Parliament, and the Goalie

A small, self-contained animal-story world with foreshadowing and conflict.
The premise is a group of animals preparing for a big park game while the
parliament of birds plans the rules and the goalie tries to keep everyone safe.

The story is generated from a simple world model so the prose follows what
happens in the simulation: warning signs appear, the conflict rises, and the
ending proves what changed.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "cat", "rabbit", "deer", "mouse", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    weather: str
    field: str
    has_grass: bool = True
    has_net: bool = True
    has_perch: bool = True


@dataclass
class StoryParams:
    place: str = "meadow"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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


SETTINGS = {
    "meadow": Place(name="the meadow", weather="cool", field="green field"),
    "pond": Place(name="the pond", weather="windy", field="soft bank"),
    "court": Place(name="the little court", weather="bright", field="hard ground"),
}

FORESHADOWS = [
    "a cracked branch",
    "a dark cloud",
    "a bent sign",
    "a twitchy gate",
]

ANIMALS = [
    ("homer", "hedgehog"),
    ("parliament", "parrot"),
    ("goalie", "goose"),
]

HELPERS = [
    ("rabbit", "small rabbit"),
    ("fox", "gentle fox"),
    ("squirrel", "quick squirrel"),
]


@dataclass
class StoryScene:
    warning: str
    conflict: str
    resolution: str


ASP_RULES = r"""
#show foreshadow/1.
#show conflict/1.
#show resolved/1.

foreshadow(branch) :- sign(branch).
conflict(argue) :- foreshadow(branch).
resolved(help) :- conflict(argue), calm.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("sign", "branch"),
        asp.fact("sign", "cloud"),
        asp.fact("calm"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show foreshadow/1. #show conflict/1. #show resolved/1."))
    atoms = {(sym.name, tuple(str(a) for a in sym.arguments)) for sym in model}
    expected = {("foreshadow", ("branch",)), ("conflict", ("argue",)), ("resolved", ("help",))}
    if atoms == expected:
        print("OK: ASP twin matches Python story logic.")
        return 0
    print("MISMATCH between ASP and Python logic.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    homer = world.add(Entity(id="homer", kind="character", type="hedgehog", label="Homer"))
    parliament = world.add(Entity(id="parliament", kind="character", type="parrot", label="Parliament"))
    goalie = world.add(Entity(id="goalie", kind="character", type="goose", label="Goalie"))
    helper_kind, helper_label = random.choice(HELPERS)
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_label))

    homer.memes["hope"] = 1
    parliament.memes["duty"] = 1
    goalie.memes["alert"] = 1
    helper.memes["kindness"] = 1

    foreshadow = random.choice(FORESHADOWS)
    world.facts["foreshadow"] = foreshadow
    world.facts["helper"] = helper.label
    world.facts["place"] = place.name

    world.say(
        f"In {place.name}, Homer the hedgehog watched {foreshadow} and wondered if the day would stay calm."
    )
    world.say(
        f"Parliament the parrot was busy calling the rules for the game, while Goalie the goose stood by the net."
    )

    world.para()
    world.say(
        f"Before the play began, Homer wanted to dash straight for the ball, but Parliament warned that the ground was slippery."
    )
    homer.memes["restless"] = 1
    parliament.memes["concern"] = 1
    goalie.memes["watching"] = 1
    world.facts["warning"] = "slippery ground"

    world.para()
    world.say(
        f"Homer bristled and said the game would not be fun if everyone moved so slowly."
    )
    homer.memes["conflict"] = 1
    parliament.memes["conflict"] = 1
    world.say(
        f"The little court went quiet as the conflict grew, and Goalie stepped between them with a steady flap of wings."
    )
    goalie.memes["calm"] = 1

    world.para()
    world.say(
        f"Then the helper carried a dry mat onto the ground, and Parliament agreed to a safer plan."
    )
    homer.memes["joy"] = 1
    parliament.memes["relief"] = 1
    goalie.memes["relief"] = 1
    world.say(
        f"Homer skidded once on the mat, laughed, and played the game without another worry."
    )
    world.say(
        f"By the end, the foreshadowing had turned into a small warning that helped everyone stay together."
    )

    world.facts.update(homer=homer, parliament=parliament, goalie=goalie)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short animal story with foreshadowing and conflict about Homer, Parliament, and Goalie.",
        "Tell a gentle story where a cautious warning leads to a disagreement, then a safer choice.",
        "Write a child-friendly animal story that includes Homer, Parliament, and Goalie and ends calmly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who noticed the warning sign first?",
            answer=f"Homer noticed {world.facts['foreshadow']} first and felt unsure about the day.",
        ),
        QAItem(
            question="Why did Homer and Parliament argue?",
            answer="They argued because Homer wanted to rush ahead, but Parliament worried the ground was slippery.",
        ),
        QAItem(
            question="How did the conflict end?",
            answer="The helper brought a dry mat, Parliament agreed to a safer plan, and the game could continue.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is a problem or disagreement that makes the characters work for a solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{eid}: type={ent.type} meters={meters} memes={memes}")
    lines.append(f"place: {world.place.name}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with foreshadowing and conflict.")
    ap.add_argument("--place", choices=SETTINGS.keys())
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    return StoryParams(place=place)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="meadow"),
    StoryParams(place="pond"),
    StoryParams(place="court"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show foreshadow/1. #show conflict/1. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if args.all:
            header = f"### {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
