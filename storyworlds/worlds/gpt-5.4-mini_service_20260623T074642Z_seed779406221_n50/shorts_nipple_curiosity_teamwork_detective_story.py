#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/shorts_nipple_curiosity_teamwork_detective_story.py
===============================================================================================================

A tiny detective-style storyworld about curiosity, teamwork, and a lost item.

Seed tale idea:
A child detective notices that a pair of shorts has gone missing. The search leads
through a small home or yard scene where a bottle nipple, a toy basket, or a
laundry hook can become a clue. Curiosity pushes the search forward; teamwork
solves the puzzle.

This world intentionally stays small and classical:
- one child detective
- one helper
- one missing pair of shorts
- one clue involving a nipple/bottle nipple
- one location
- a clean turn from clue-seeking to shared discovery
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    clues: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    points_to: str
    setting_hint: str = ""


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "laundry_room": Place(
        id="laundry_room",
        label="the laundry room",
        indoors=True,
        clues=["hanger", "basket", "dryer"],
    ),
    "bedroom": Place(
        id="bedroom",
        label="the bedroom",
        indoors=True,
        clues=["toy_box", "bed", "drawer"],
    ),
    "backyard": Place(
        id="backyard",
        label="the backyard",
        indoors=False,
        clues=["line", "bucket", "bench"],
    ),
}

CLUES = {
    "bottle_nipple": Clue(
        id="bottle_nipple",
        label="a bottle nipple",
        phrase="a tiny bottle nipple from a baby bottle",
        points_to="drawer",
        setting_hint="It belonged with baby things and pointed toward the drawer.",
    ),
    "toy_nipple": Clue(
        id="toy_nipple",
        label="a rubber nipple",
        phrase="a soft rubber nipple from a toy baby bottle",
        points_to="toy_box",
        setting_hint="It looked like it had rolled out of the toy box.",
    ),
    "laundry_tag": Clue(
        id="laundry_tag",
        label="a laundry tag",
        phrase="a little tag pinned near the clothesline",
        points_to="hanger",
        setting_hint="It pointed toward the hanging clothes.",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Owen"]
HELPERS = ["mother", "father", "big sister", "big brother"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


ASP_RULES = r"""
missing(shorts).
curious(child) :- missing(shorts).
teamwork(child, helper) :- curious(child), clue(C).
solved(shorts) :- clue(C), points_to(C, L), found(L).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("shorts_item", "shorts"))
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for c in p.clues:
            lines.append(asp.fact("possible_clue", pid, c))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, c.points_to))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            combos.append((place, clue))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about shorts, a clue, curiosity, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
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
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    if (place, clue) not in valid_combos():
        raise StoryError("No valid detective case matches those choices.")
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, clue=clue, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper, label=params.helper))
    shorts = world.add(Entity(id="shorts", type="shorts", label="shorts", phrase="a pair of blue shorts"))

    child.memes["curiosity"] = 1.0
    child.memes["worry"] = 1.0
    world.facts.update(child=child, helper=helper, clue=clue, shorts=shorts, place=place)

    world.say(
        f"{params.name} was a little detective with a sharp eye for clues."
    )
    world.say(
        f"One morning, {params.name} noticed that the shorts were missing from their spot."
    )
    world.say(
        f"{params.name}'s curiosity made {params.name} look under a chair, beside a basket, and near the floor."
    )
    world.say(
        f"Then {params.name} found {clue.phrase}. {clue.setting_hint}"
    )
    world.say(
        f"{params.helper.capitalize()} helped {params.name} follow the clue through {place.label}."
    )
    world.say(
        f"At last, they found the shorts hidden where the clue had pointed, and teamwork solved the mystery."
    )
    if place.id == "backyard":
        world.say("The sunlight shone on the happy pair, and the little detective smiled.")
    else:
        world.say("The room felt tidy again, and the shorts were back where they belonged.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for young children about {f["child"].label}, a pair of shorts, and a clue.',
        f"Tell a gentle mystery where curiosity leads to a clue and teamwork helps find the missing shorts.",
        f'Write a child-friendly detective story that includes the word "shorts" and ends with a happy discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    clue = f["clue"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the little detective in the story?",
            answer=f"The little detective was {child.label}, who kept looking for the missing shorts.",
        ),
        QAItem(
            question=f"What clue helped them search?",
            answer=f"They found {clue.phrase}, and it pointed them toward where the shorts were hidden.",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{helper.label.capitalize()} helped with the search, so teamwork could solve the mystery.",
        ),
        QAItem(
            question=f"Where did the search happen?",
            answer=f"The search happened in {place.label}, where the clue and the shorts were both found.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other to do something together.",
        ),
        QAItem(
            question="What are shorts?",
            answer="Shorts are short pants that people wear when they want to stay cool and move easily.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a bottle nipple?",
            answer="A bottle nipple is the soft part of a baby bottle that a baby drinks from.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} label={e.label}")
    lines.append(f"  place={world.place.label}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - ap))
    print("only asp:", sorted(ap - py))
    return 1


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
    StoryParams(place="laundry_room", clue="bottle_nipple", name="Mia", helper="mother"),
    StoryParams(place="bedroom", clue="toy_nipple", name="Leo", helper="father"),
    StoryParams(place="backyard", clue="laundry_tag", name="Nora", helper="big sister"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
