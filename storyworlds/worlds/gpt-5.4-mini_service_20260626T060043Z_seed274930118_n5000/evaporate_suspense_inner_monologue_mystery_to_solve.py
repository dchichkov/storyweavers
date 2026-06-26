#!/usr/bin/env python3
"""
A tiny detective-story world about a missing clue, a suspicious puddle, and a
mystery that changes when the trail evaporates.
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
class Clue:
    id: str
    name: str
    kind: str
    location: str
    visible: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Detective:
    name: str
    title: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    name: str
    description: str
    clues: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    detective: Detective
    place: Place
    clues: dict[str, Clue]
    mystery: str
    suspect: str
    solution: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    clue: str
    detective_name: str
    suspect: str
    seed: Optional[int] = None


PLACES = {
    "greenhouse": Place(
        id="greenhouse",
        name="the greenhouse",
        description="Warm glass walls made the air soft and wet.",
        clues=["droplet", "note"],
    ),
    "library": Place(
        id="library",
        name="the library",
        description="Tall shelves stood still while whispers hid in the corners.",
        clues=["bookmark", "note"],
    ),
    "dock": Place(
        id="dock",
        name="the dock",
        description="The boards creaked above dark water and a salty wind kept moving.",
        clues=["rope", "shell"],
    ),
}

CLUES = {
    "droplet": Clue(
        id="droplet",
        name="a tiny droplet",
        kind="water",
        location="on the window",
    ),
    "note": Clue(
        id="note",
        name="a folded note",
        kind="paper",
        location="under a pot",
    ),
    "bookmark": Clue(
        id="bookmark",
        name="a ribbon bookmark",
        kind="cloth",
        location="inside a book",
    ),
    "rope": Clue(
        id="rope",
        name="a short rope fiber",
        kind="fiber",
        location="near the edge",
    ),
    "shell": Clue(
        id="shell",
        name="a small shell chip",
        kind="shell",
        location="by the steps",
    ),
}

SUSPECTS = {
    "cat": "the cat",
    "gardener": "the gardener",
    "librarian": "the librarian",
    "fisherman": "the fisherman",
}

DETECTIVES = [
    "Mina",
    "Noah",
    "June",
    "Eli",
    "Ruby",
    "Finn",
]

ASP_RULES = r"""
place(greenhouse). place(library). place(dock).
clue(droplet). clue(note). clue(bookmark). clue(rope). clue(shell).

needs_water(droplet).
needs_dry_place(note).
needs_dry_place(bookmark).
needs_dry_place(rope).
needs_dry_place(shell).

at_risk(C) :- needs_water(C), evaporates(C).
at_risk(C) :- needs_dry_place(C), wet_place(P).

valid_mystery(P,C) :- place(P), clue(C).
solvable(P,C) :- valid_mystery(P,C), not impossible(P,C).

impossible(P,C) :- wet_place(P), needs_dry_place(C), evaporates(C).
impossible(P,C) :- dry_place(P), needs_water(C), not evaporates(C).

#show at_risk/1.
#show valid_mystery/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for c in CLUES.values():
        lines.append(asp.fact("clue", c.id))
        if c.kind == "water":
            lines.append(asp.fact("evaporates", c.id))
    lines.append(asp.fact("wet_place", "greenhouse"))
    lines.append(asp.fact("wet_place", "dock"))
    lines.append(asp.fact("dry_place", "library"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_mystery/2."))
    asp_pairs = set(asp.atoms(model, "valid_mystery"))
    py_pairs = set()
    for p in PLACES:
        for c in CLUES:
            py_pairs.add((p, c))
    if asp_pairs == py_pairs:
        print(f"OK: ASP and Python both see {len(py_pairs)} mysteries.")
        return 0
    print("MISMATCH:")
    print("ASP only:", sorted(asp_pairs - py_pairs))
    print("PY only:", sorted(py_pairs - asp_pairs))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective story world with evaporating clues.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=DETECTIVES)
    ap.add_argument("--suspect", choices=list(SUSPECTS))
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in PLACES for c in PLACES[p].clues]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.clue and (args.place, args.clue) not in combos:
        raise StoryError("That clue does not belong in that place.")
    choices = [c for c in combos if (args.place is None or c[0] == args.place) and (args.clue is None or c[1] == args.clue)]
    if not choices:
        raise StoryError("No valid mystery matches those options.")
    place, clue = rng.choice(choices)
    name = args.name or rng.choice(DETECTIVES)
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    return StoryParams(place=place, clue=clue, detective_name=name, suspect=suspect)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    detective = Detective(name=params.detective_name, title="detective", location=place.id)
    w = World(
        detective=detective,
        place=place,
        clues={clue.id: Clue(**{**clue.__dict__})},
        mystery=f"Who moved the clue at {place.name}?",
        suspect=SUSPECTS[params.suspect],
        solution=f"{SUSPECTS[params.suspect]} waited until the clue could evaporate or vanish from sight.",
    )
    return w


def tell(world: World) -> None:
    d = world.detective
    p = world.place
    clue = next(iter(world.clues.values()))
    world.say(f"{d.name} was a small detective who liked quiet puzzles.")
    world.say(f"One afternoon, {d.name} arrived at {p.name}. {p.description}")
    world.say(f"On the way in, {d.name} noticed {clue.name} {clue.location}.")
    world.say(f"'{world.mystery}' {d.name} thought, and the question felt bigger than the room.")

    if clue.kind == "water":
        world.say(
            f"Then the warm air made the clue evaporate little by little, and the trail grew thinner."
        )
        world.say(
            f"{d.name} held still and listened to a private inner monologue: 'If water disappears, I must look for what it touched.'"
        )
    else:
        world.say(
            f"{d.name} felt suspense creep in, because the clue could be carried away before it said enough."
        )
        world.say(
            f"Inside {d.name}'s head, a careful inner monologue whispered, 'A good detective follows the smallest sign.'"
        )

    world.para()
    if clue.kind == "water":
        world.say(
            f"{d.name} looked for a dry mark beside the place where the droplet had been. That pointed toward {world.suspect}."
        )
        world.say(
            f"The mystery to solve was not the droplet itself, but what it proved before it evaporated."
        )
    else:
        world.say(
            f"{d.name} found the clue still waiting and matched it with the scene. That pointed toward {world.suspect}."
        )
        world.say(
            f"The mystery to solve was who had been there, and why the small sign mattered."
        )

    world.para()
    world.say(
        f"In the end, {d.name} solved it: {world.solution} {world.suspect} was not a monster, only part of a careful little secret."
    )
    world.say(
        f"The last image was simple: {d.name} stood in {p.name} with the answer in hand, and the evaporated clue had become a solved mystery."
    )
    world.facts.update(
        detective=d,
        place=p,
        clue=clue,
        suspect=world.suspect,
        evaporate=(clue.kind == "water"),
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for children that includes the word "evaporate".',
        f"Tell a suspenseful mystery about {f['detective'].name} in {f['place'].name} where a clue may evaporate before it can be read.",
        "Write a simple detective story with inner monologue, suspense, and a clear mystery to solve.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is {d.name}. {d.name} is the one who watches the clues and thinks carefully.",
        ),
        QAItem(
            question=f"What happened to {clue.name} in the story?",
            answer=(
                f"It started as a clue in {world.place.name}. Because the air was warm, it could evaporate and leave only a faint sign behind."
            ),
        ),
        QAItem(
            question="What mystery did the detective solve?",
            answer=f"{d.name} solved the mystery of who moved the clue and why the small sign mattered.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does evaporate mean?",
            answer="To evaporate means to change from a liquid into a gas or thin vapor that disappears into the air.",
        ),
        QAItem(
            question="Why is suspense useful in a detective story?",
            answer="Suspense keeps the reader wondering what will happen next, so the mystery feels exciting.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private thinking a character does inside their head.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  detective: {world.detective.name} at {world.place.name}")
    for clue in world.clues.values():
        lines.append(f"  clue: {clue.name} visible={clue.visible} kind={clue.kind} location={clue.location}")
    lines.append(f"  suspect: {world.suspect}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
    StoryParams(place="greenhouse", clue="droplet", detective_name="Mina", suspect="gardener"),
    StoryParams(place="library", clue="note", detective_name="June", suspect="librarian"),
    StoryParams(place="dock", clue="rope", detective_name="Eli", suspect="fisherman"),
]


def asp_valid_mysteries() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_mystery/2."))
    return sorted(set(asp.atoms(model, "valid_mystery")))


def asp_verify_gate() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    asp_pairs = set(asp_valid_mysteries())
    if len(asp_pairs) != len(py):
        print("MISMATCH between ASP and Python.")
        print("ASP:", sorted(asp_pairs))
        print("PY:", sorted(py))
        return 1
    print(f"OK: ASP and Python agree on {len(py)} place/clue pairs.")
    return 0


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_mystery/2."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        pairs = asp_valid_mysteries()
        print(f"{len(pairs)} compatible mysteries:")
        for place, clue in pairs:
            print(f"  {place:11} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = build_story_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
