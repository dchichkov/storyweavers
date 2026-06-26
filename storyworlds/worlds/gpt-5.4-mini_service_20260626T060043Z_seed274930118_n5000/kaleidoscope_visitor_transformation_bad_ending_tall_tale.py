#!/usr/bin/env python3
"""
Standalone storyworld: kaleidoscope visitor transformation with a tall-tale style and a bad ending.

A visitor arrives carrying a kaleidoscope. The visitor loves peeking through it, but the
kaleidoscope has a strange echoing power: what is seen long enough can change the one who looks.
The story follows a big-voiced, small-domain simulation with a real turn and a bad ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    transformed: bool = False
    shape: str = "normal"

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"woman", "girl"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"man", "boy"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


@dataclass
class StoryParams:
    place: str = "the fairground"
    visitor_name: str = "Rufus"
    visitor_type: str = "man"
    witness_name: str = "Nell"
    witness_type: str = "girl"
    seed: Optional[int] = None


SETTINGS = {
    "fairground": "the fairground",
    "riverbend": "the river bend",
    "dusty_hill": "Dusty Hill",
}

VISITOR_NAMES = ["Rufus", "Mabel", "Ike", "Lottie", "Bram", "Nora"]
WITNESS_NAMES = ["Nell", "Otis", "Ada", "Jules", "Penny", "Wes"]


ASP_RULES = r"""
#show can_start/1.
#show can_transform/2.

can_start(P) :- place(P).

can_transform(visitor, kaleidoscope) :- can_start(_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("object", "kaleidoscope"))
    lines.append(asp.fact("character_kind", "visitor"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_can_start() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show can_start/1."))
    return sorted(set(asp.atoms(model, "can_start")))


def asp_can_transform() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show can_transform/2."))
    return sorted(set(asp.atoms(model, "can_transform")))


def asp_verify() -> int:
    py = {("fairground",), ("riverbend",), ("dusty_hill",)}
    cl = set(asp_can_start())
    if cl != py:
        print("MISMATCH between clingo and python:", sorted(cl ^ py))
        return 1
    print(f"OK: clingo gate matches python ({len(cl)} places).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld: a visitor and a kaleidoscope.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--witness")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    name = args.name or rng.choice(VISITOR_NAMES)
    witness = args.witness or rng.choice(WITNESS_NAMES)
    if witness == name:
        witness = rng.choice([n for n in WITNESS_NAMES if n != name])
    return StoryParams(
        place=place,
        visitor_name=name,
        visitor_type="man" if name in {"Rufus", "Ike", "Bram"} else "woman",
        witness_name=witness,
        witness_type="girl" if witness in {"Nell", "Ada", "Penny"} else "boy",
    )


def too_close_to_magic(world: World, visitor: Entity, kaleidoscope: Entity) -> bool:
    return visitor.memes.get("wonder", 0) >= 1 and kaleidoscope.meters.get("gleam", 0) >= 2


def apply_transformation(world: World, visitor: Entity, kaleidoscope: Entity) -> None:
    if "transform" in world.fired:
        return
    if not too_close_to_magic(world, visitor, kaleidoscope):
        return
    world.fired.add("transform")
    visitor.transformed = True
    visitor.shape = "swirl"
    visitor.meters["self"] = 0
    visitor.memes["confusion"] = visitor.memes.get("confusion", 0) + 2
    kaleidoscope.meters["gleam"] = kaleidoscope.meters.get("gleam", 0) + 1


def generate(params: StoryParams) -> StorySample:
    world = World(place=SETTINGS[params.place])

    visitor = world.add(Entity(
        id=params.visitor_name,
        kind="character",
        label="visitor",
        type=params.visitor_type,
        memes={"wonder": 0, "greed": 0, "confusion": 0, "fear": 0},
        meters={"steps": 0},
    ))
    witness = world.add(Entity(
        id=params.witness_name,
        kind="character",
        label="witness",
        type=params.witness_type,
        memes={"alarm": 0, "sadness": 0},
    ))
    kaleidoscope = world.add(Entity(
        id="kaleidoscope",
        kind="thing",
        label="kaleidoscope",
        type="toy",
        owner=visitor.id,
        held_by=visitor.id,
        meters={"gleam": 0},
    ))

    world.say(f"At {world.place}, a visitor named {visitor.id} came walking in with a kaleidoscope tucked under {visitor.pronoun('possessive')} arm.")
    world.say(f"{visitor.id} was a big-hearted {visitor.type} who loved a shining thing and a strange thing, and the kaleidoscope had both in it at once.")
    world.para()
    world.say(f"{visitor.id} held the kaleidoscope up to the light and laughed at the little glass mountains inside it.")
    visitor.memes["wonder"] += 1
    visitor.meters["steps"] += 1
    kaleidoscope.meters["gleam"] += 1
    world.say(f"{witness.id} watched from the fence and said the toy looked like a summer storm trapped in a bottle.")

    world.para()
    world.say(f"The visitor peered again, and again, and again, because tall tales grow taller when nobody stops to blink.")
    visitor.memes["wonder"] += 1
    visitor.meters["steps"] += 1
    kaleidoscope.meters["gleam"] += 1
    apply_transformation(world, visitor, kaleidoscope)

    if visitor.transformed:
        witness.memes["alarm"] += 1
        world.say(f"Then the glass flashed so bright it seemed the whole fairground tipped sideways.")
        world.say(f"{visitor.id} did not stay quite a person after that; {visitor.pronoun('subject')} turned into a swirl of colors, with boots, hat, and grin all mixed together.")
        world.say(f"{witness.id} cried out, but the kaleidoscope only kept humming, and the visitor's voice came back thin as a ribbon in the wind.")
    else:
        # ensure a transformation in the requested world
        visitor.memes["wonder"] += 1
        kaleidoscope.meters["gleam"] += 1
        apply_transformation(world, visitor, kaleidoscope)
        witness.memes["alarm"] += 1
        world.say(f"The glass flashed so bright it seemed the whole fairground tipped sideways.")
        world.say(f"{visitor.id} did not stay quite a person after that; {visitor.pronoun('subject')} turned into a swirl of colors, with boots, hat, and grin all mixed together.")
        world.say(f"{witness.id} cried out, but the kaleidoscope only kept humming, and the visitor's voice came back thin as a ribbon in the wind.")

    world.para()
    world.say(f"By sundown, the visitor could only answer in spinning reflections, and {witness.id} carried the dull little toy away with a shaking hand.")
    world.say(f"The stars came out over {world.place}, and the last thing anyone saw was a lonely shimmer where a visitor had once stood.")

    world.facts.update(
        visitor=visitor,
        witness=witness,
        kaleidoscope=kaleidoscope,
        transformed=visitor.transformed,
        place=params.place,
    )

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
    visitor = f["visitor"]
    return [
        "Write a tall tale about a visitor and a kaleidoscope that changes the visitor after too much looking.",
        f"Tell a strange, child-facing story where {visitor.id} brings a kaleidoscope to {world.place} and the ending goes wrong.",
        "Make the story feel like a tall tale, with a wonder-filled middle and a bad ending."
    ]


def story_qa(world: World) -> list[QAItem]:
    v = world.facts["visitor"]
    w = world.facts["witness"]
    return [
        QAItem(
            question=f"Who came to {world.place} with the kaleidoscope?",
            answer=f"The visitor named {v.id} came to {world.place} with the kaleidoscope tucked under {v.pronoun('possessive')} arm."
        ),
        QAItem(
            question=f"What happened when {v.id} looked too long through the kaleidoscope?",
            answer=f"{v.id} was changed into a swirl of colors and did not stay quite a person after the bright flash."
        ),
        QAItem(
            question=f"How did the story end for {v.id}?",
            answer=f"It ended badly, with {v.id} trapped in spinning reflections while {w.id} carried the dull little toy away."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kaleidoscope?",
            answer="A kaleidoscope is a tube with mirrors and colored pieces inside it that make changing patterns when you look through it."
        ),
        QAItem(
            question="What is a visitor?",
            answer="A visitor is someone who comes to a place for a while and is not the regular person who lives there."
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when the story finishes with something sad, scary, or unfair instead of a happy fix."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes} "
            f"transformed={e.transformed} shape={e.shape}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show can_start/1."))
    return sorted(set(asp.atoms(model, "can_start")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_start/1.\n#show can_transform/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_places())
        print(asp_can_transform())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, place in enumerate(list(SETTINGS)):
            p = StoryParams(place=place, seed=base_seed + i)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
