#!/usr/bin/env python3
"""
Standalone storyworld: a tiny ghost story about novelty, law, magic, and reconciliation.

A child meets a harmless ghost in an old law library. The ghost's magic cannot rest
because a new rule has been posted, and the child helps the ghost reconcile with the
new law by finding the right place for the rule and the right way to remember it.
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


@dataclass
class StoryParams:
    place: str
    child: str
    ghost: str
    law: str
    novelty: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    memo: str = ""
    alive: bool = True

    def p(self) -> str:
        if self.type in {"girl", "woman", "mother"}:
            return "she"
        if self.type in {"boy", "man", "father"}:
            return "he"
        return "it"

    def obj(self) -> str:
        if self.type in {"girl", "woman", "mother"}:
            return "her"
        if self.type in {"boy", "man", "father"}:
            return "him"
        return "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


PLACES = {
    "old_library": "the old library",
    "attic": "the attic",
    "hall": "the hallway",
}

CHILDREN = [
    ("Maya", "girl"),
    ("Noah", "boy"),
    ("Lena", "girl"),
    ("Eli", "boy"),
]

GHOSTS = [
    "gentle ghost",
    "small ghost",
    "pale ghost",
    "shy ghost",
]

LAWS = [
    "keep the candles out of the stacks",
    "return every book before midnight",
    "do not shout in the reading room",
    "leave the windows latched in winter",
]

NOVELTIES = [
    "a glowing bookmark",
    "a new notice stamped in blue ink",
    "a tiny bell tied to the rule board",
    "a bright ribbon on the door",
]


class Story:
    def __init__(self, world: World) -> None:
        self.world = world

    def setup(self, child: Entity, ghost: Entity, law: Entity, novelty: Entity) -> None:
        w = self.world
        child.memes["curiosity"] = 1
        ghost.memes["worry"] = 1
        law.meters["importance"] = 1
        novelty.meters["newness"] = 1
        w.say(
            f"{child.id} lived near {w.place} and liked quiet, strange rooms."
        )
        w.say(
            f"One evening, {child.id} saw {ghost.label} near the dust and moonlight."
        )
        w.say(
            f"On the wall, {novelty.label} shone beside the old law: {law.memo}."
        )

    def tension(self, child: Entity, ghost: Entity, law: Entity, novelty: Entity) -> None:
        w = self.world
        ghost.memes["uneasy"] = 1
        child.memes["wonder"] = 1
        w.say(
            f"{ghost.id} whispered that the new thing felt too fresh for an old place."
        )
        w.say(
            f"It feared the rule would chase away the magic that kept the rooms gentle."
        )
        w.say(
            f"But {child.id} noticed the law was not angry; it only wanted care."
        )

    def turn(self, child: Entity, ghost: Entity, law: Entity, novelty: Entity) -> None:
        w = self.world
        ghost.memes["hope"] = 1
        child.memes["kindness"] = 1
        w.say(
            f"{child.id} took the {novelty.label} down and read the rule slowly."
        )
        w.say(
            f"Then {child.id} found a small frame and set the notice where everyone could see it."
        )
        w.say(
            f"The ghost's magic twinkled, because the law was no longer hiding in the dark."
        )

    def resolution(self, child: Entity, ghost: Entity, law: Entity, novelty: Entity) -> None:
        w = self.world
        ghost.memes["reconciled"] = 1
        child.memes["joy"] = 1
        w.say(
            f"{ghost.id} bowed with a soft smile and thanked {child.id} for the help."
        )
        w.say(
            f"Now the old room had both things at once: a clear law and a little magic."
        )
        w.say(
            f"At the end, {child.id} went home with moon dust on {child.obj()} hands, "
            f"and {ghost.id} rested peacefully beside the rule that had been understood."
        )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost storyworld with novelty, law, magic, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child")
    ap.add_argument("--ghost")
    ap.add_argument("--law")
    ap.add_argument("--novelty")
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
    child = args.child or rng.choice([c for c, _ in CHILDREN])
    ghost = args.ghost or rng.choice(GHOSTS)
    law = args.law or rng.choice(LAWS)
    novelty = args.novelty or rng.choice(NOVELTIES)
    return StoryParams(place=place, child=child, ghost=ghost, law=law, novelty=novelty)


def generate(params: StoryParams) -> StorySample:
    world = World(place=PLACES[params.place])
    child_type = next(t for n, t in CHILDREN if n == params.child)
    child = world.add(Entity(id=params.child, kind="character", type=child_type, label=params.child))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost))
    law = world.add(Entity(id="law", kind="thing", type="law", label="the law", memo=params.law))
    novelty = world.add(Entity(id="novelty", kind="thing", type="novelty", label=params.novelty))

    story = Story(world)
    story.setup(child, ghost, law, novelty)
    world.lines.append("")
    story.tension(child, ghost, law, novelty)
    world.lines.append("")
    story.turn(child, ghost, law, novelty)
    world.lines.append("")
    story.resolution(child, ghost, law, novelty)

    world.facts.update(child=child.id, child_type=child.type, ghost=ghost.label, law=law.memo, novelty=novelty.label, place=world.place)

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
        f'Write a short ghost story for children set in {f["place"]} about novelty and law.',
        f'Write a gentle story where {f["child"]} helps a ghost understand a new rule without losing the magic.',
        f'Write a tiny reconciliation story with a ghost, a fresh notice, and a calm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who helped the ghost understand the new law?",
            answer=f'{f["child"]} helped by reading the notice carefully and placing it where everyone could see it.'
        ),
        QAItem(
            question=f"What was the new thing in the story?",
            answer=f'The new thing was {f["novelty"]}, which went with the law and made the room feel newly watched over.'
        ),
        QAItem(
            question=f"How did the story end for the ghost?",
            answer="The ghost felt peaceful at the end because the law was clear and the magic could rest beside it."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a ghost story?",
            answer="A ghost is usually a spooky but often lonely spirit character who can whisper, float, and worry about unfinished things."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a problem so the people or things can fit together again."
        ),
        QAItem(
            question="What is a law?",
            answer="A law is a rule that tells people what is allowed or expected in a place."
        ),
    ]


def verify_reasonableness(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("unknown place")
    if params.law not in LAWS:
        raise StoryError("unknown law")


ASP_RULES = r"""
place(old_library). place(attic). place(hall).
law(keep_the_candles_out_of_the_stacks).
law(return_every_book_before_midnight).
law(do_not_shout_in_the_reading_room).
law(leave_the_windows_latched_in_winter).
novelty(glowing_bookmark).
novelty(new_notice_stamped_in_blue_ink).
novelty(tiny_bell_tied_to_the_rule_board).
novelty(bright_ribbon_on_the_door).
compatible(P, L, N) :- place(P), law(L), novelty(N).
#show compatible/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("place", p) for p in PLACES]
    lines += [asp.fact("law", "keep_the_candles_out_of_the_stacks")]
    lines += [asp.fact("law", "return_every_book_before_midnight")]
    lines += [asp.fact("law", "do_not_shout_in_the_reading_room")]
    lines += [asp.fact("law", "leave_the_windows_latched_in_winter")]
    lines += [asp.fact("novelty", "glowing_bookmark")]
    lines += [asp.fact("novelty", "new_notice_stamped_in_blue_ink")]
    lines += [asp.fact("novelty", "tiny_bell_tied_to_the_rule_board")]
    lines += [asp.fact("novelty", "bright_ribbon_on_the_door")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(json.dumps(dataclasses.asdict(sample.params), indent=2))
    if qa:
        print()
        for section, items in (("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)):
            print(section + ":")
            if section == "Prompts":
                for item in items:
                    print(f"- {item}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("old_library", "Maya", "gentle ghost", "do not shout in the reading room", "a glowing bookmark"),
            StoryParams("attic", "Noah", "small ghost", "return every book before midnight", "a new notice stamped in blue ink"),
            StoryParams("hall", "Lena", "shy ghost", "keep the candles out of the stacks", "a tiny bell tied to the rule board"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))
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
