#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/identify_member_guppy_lesson_learned_repetition_whodunit.py
===============================================================================================================================

A small whodunit-style story world about identifying a missing member of a pond
club, where a guppy clue repeats, the mystery tightens, and a lesson is learned.

The domain is intentionally narrow:
- a caretaker, a club member, a guppy, and a few physical clues;
- a repeatable investigation loop that reveals one fact at a time;
- a final lesson learned that changes how the characters act.

The prose should feel like a child-friendly whodunit: there is a puzzling
repetition, a careful look at the clues, a surprise identification, and a calm
ending that proves what changed.
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

WORLD_NAME = "identify_member_guppy_lesson_learned_repetition_whodunit"


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    indoor: bool = True


@dataclass
class Clue:
    kind: str
    text: str
    repeated: int = 0


@dataclass
class StoryParams:
    place: str = "the pet shop"
    missing_member: str = "Ari"
    witness: str = "Mina"
    caretaker: str = "Mr. Bell"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Character] = {}
        self.clues: list[Clue] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Character) -> Character:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "the pet shop": Place("the pet shop", indoor=True),
    "the aquarium room": Place("the aquarium room", indoor=True),
    "the garden pond": Place("the garden pond", indoor=False),
}

MEMBER_NAMES = ["Ari", "Bela", "Cleo", "Drew", "Nico", "Tia"]
WITNESS_NAMES = ["Mina", "Oren", "Pia", "Ravi", "Lina", "Noah"]
CARETAKERS = ["Mr. Bell", "Ms. Finch", "Mrs. Reed", "Mr. Lane"]


ASP_RULES = r"""
member(X) :- named_member(X).
guppy(clue) :- repeated(guppy_mark).
identify(X) :- member(X), has_clue(X), repeated(guppy_mark).
lesson_learned :- identify(_), careful_questioning.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in MEMBER_NAMES:
        lines.append(asp.fact("named_member", name))
    lines.append(asp.fact("guppy_mark", "stripe"))
    lines.append(asp.fact("repeated", "guppy_mark"))
    lines.append(asp.fact("careful_questioning"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly whodunit story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--member")
    ap.add_argument("--witness")
    ap.add_argument("--caretaker")
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
    member = args.member or rng.choice(MEMBER_NAMES)
    witness = args.witness or rng.choice([n for n in WITNESS_NAMES if n != member])
    caretaker = args.caretaker or rng.choice(CARETAKERS)
    place = args.place or rng.choice(list(SETTINGS))
    if witness == member:
        raise StoryError("The witness must be a different character from the missing member.")
    return StoryParams(place=place, missing_member=member, witness=witness, caretaker=caretaker)


def reasonableness_gate(params: StoryParams) -> None:
    if params.missing_member == params.witness:
        raise StoryError("A whodunit needs a witness who can notice the clues.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if not params.caretaker:
        raise StoryError("A caretaker is needed to notice the missing member.")


def generate_story_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(SETTINGS[params.place])
    witness = world.add(Character(id=params.witness, type="person", label=params.witness, role="witness"))
    caretaker = world.add(Character(id=params.caretaker, type="person", label=params.caretaker, role="caretaker"))
    member = world.add(Character(id=params.missing_member, type="person", label=params.missing_member, role="member"))
    guppy = world.add(Character(id="guppy", type="fish", label="a guppy", role="clue"))
    world.facts.update(witness=witness, caretaker=caretaker, member=member, guppy=guppy)

    world.say(
        f"At {world.place.name}, {witness.id} noticed something odd: the little club member "
        f"{member.id} was not where {caretaker.id} expected them to be."
    )
    world.say(
        f"On the table, a bowl held a bright guppy, and beside it sat a tiny wet mark."
    )
    world.para()

    # Repetition instrument: the same guppy clue appears twice, each time narrowing the mystery.
    clues = [
        Clue("guppy_mark", "A small stripe of water glittered near the bowl.", repeated=1),
        Clue("guppy_mark", "The same stripe appeared again by the chair leg.", repeated=2),
        Clue("member_trace", f"Two steps pointed from the bowl toward {member.id}'s hiding place.", repeated=1),
    ]
    world.clues.extend(clues)

    world.say(f"{witness.id} looked once, then looked again. The guppy clue repeated.")
    world.say(f"First the stripe was near the bowl. Then the stripe was near the chair.")
    world.say(f"That repetition made the room feel like a puzzle with one answer.")
    world.para()

    world.say(
        f"{caretaker.id} checked the clues carefully and smiled. "
        f"They found {member.id} behind the curtain, helping the guppy stay calm."
    )
    world.say(
        f"It turned out {member.id} had not vanished at all; they were guarding the fish bowl "
        f"after noticing the water was too low."
    )
    world.say(
        f"{witness.id} identified the missing member by following the repeating guppy marks."
    )
    world.para()

    world.say(
        f"In the end, everyone learned the same lesson: when a mystery repeats, you should "
        f"look again before you worry."
    )
    world.say(
        f"{caretaker.id} filled the bowl, {member.id} returned to the club game, and the guppy "
        f"swam in a brighter, safer circle."
    )

    world.facts.update(
        identified=member.id,
        lesson="look again before you worry",
        repeated_clue="guppy mark",
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit where {f['witness'].id} must identify a missing member by following a guppy clue.",
        f"Tell a gentle mystery at {world.place.name} where a repeating water mark helps find {f['identified']}.",
        f"Write a child-friendly story about a guppy, a missing member, and a lesson learned about looking twice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    witness = f["witness"].id
    member = f["identified"]
    caretaker = f["caretaker"].id
    place = world.place.name
    return [
        QAItem(
            question=f"Who noticed that something was wrong at {place}?",
            answer=f"{witness} noticed that {member} was missing and started watching the clues closely.",
        ),
        QAItem(
            question="How did they identify the missing member?",
            answer=f"They identified {member} by following the repeating guppy marks from the bowl to the hiding place.",
        ),
        QAItem(
            question=f"What did {caretaker} do at the end?",
            answer=f"{caretaker} checked the clues, found {member}, and then filled the guppy bowl so the fish was safer.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="They learned to look again before they worry, because repeating clues can point to the right answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a guppy?",
            answer="A guppy is a small fish often kept in a fish tank or bowl.",
        ),
        QAItem(
            question="What does identify mean?",
            answer="To identify something means to figure out what it is or who it is.",
        ),
        QAItem(
            question="What is a member?",
            answer="A member is a person who belongs to a group or club.",
        ),
        QAItem(
            question="Why can repetition help in a mystery?",
            answer="Repetition can help because the same clue showing up again may point to the important part of the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.name}")
    for e in world.entities.values():
        lines.append(f"{e.id}: role={e.role} type={e.type}")
    for clue in world.clues:
        lines.append(f"clue: {clue.kind} repeated={clue.repeated} text={clue.text}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
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


def valid_params() -> list[StoryParams]:
    return [
        StoryParams(place="the pet shop", missing_member="Ari", witness="Mina", caretaker="Mr. Bell"),
        StoryParams(place="the aquarium room", missing_member="Cleo", witness="Oren", caretaker="Ms. Finch"),
        StoryParams(place="the garden pond", missing_member="Tia", witness="Pia", caretaker="Mrs. Reed"),
    ]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show identify/1. #show member/1. #show guppy/1. #show lesson_learned/0."))
    # We only verify that the program is solvable and emits the intended atoms.
    atoms = {sym.name for sym in model}
    required = {"identify", "member", "guppy", "lesson_learned"}
    if required.issubset(atoms):
        print("OK: ASP twin emits the expected mystery atoms.")
        return 0
    print("MISMATCH: ASP twin did not emit the expected atoms.")
    print(sorted(atoms))
    return 1


def show_asp_program() -> str:
    return asp_program("#show identify/1. #show member/1. #show guppy/1. #show lesson_learned/0.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(show_asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in valid_params()]
    else:
        for i in range(max(args.n, 1)):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
