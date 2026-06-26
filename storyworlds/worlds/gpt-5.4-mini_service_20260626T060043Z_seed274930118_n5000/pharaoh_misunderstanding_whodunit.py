#!/usr/bin/env python3
"""
Standalone storyworld: pharaoh misunderstanding whodunit.

A small classical simulation in a palace setting where a Pharaoh's lost
treasure, a mistaken clue, and a careful reveal produce a child-facing mystery
story with a true turn and a clear ending.
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
class Person:
    id: str
    kind: str = "character"
    role: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.role in {"pharaoh", "man", "boy", "prince", "guard"}:
            return "he"
        if self.role in {"queen", "woman", "girl", "maid", "servant"}:
            return "she"
        return "they"

    def possessive(self) -> str:
        return "his" if self.pronoun() == "he" else "her" if self.pronoun() == "she" else "their"


@dataclass
class Clue:
    id: str
    label: str
    place: str
    owner: str
    visible_mark: str
    true_source: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Nefru"
    helper: str = "Sefi"
    culprit: str = "the cat"
    clue: str = "sand print"
    room: str = "the sunlit hall"


PEOPLE = {
    "pharaoh": {"role": "pharaoh", "label": "the Pharaoh", "traits": ["stern", "proud", "careful"]},
    "helper": {"role": "scribe", "label": "the small scribe", "traits": ["quiet", "clever"]},
    "guard": {"role": "guard", "label": "the guard", "traits": ["steady", "kind"]},
}

CULPRITS = [
    ("the cat", "pawprint", "the cat brushed past the dust and left the mark"),
    ("the wind", "swirl", "the wind blew sand in a little curve"),
    ("the servant with a broom", "brush streak", "the servant swept the floor and made the line"),
]

ROOMS = [
    "the sunlit hall",
    "the treasure room",
    "the cool archive",
    "the palace courtyard",
]

CLUES = [
    ("sand print", "small sand print"),
    ("smudge", "dark smudge"),
    ("broken seal", "broken seal"),
    ("tiny scratch", "tiny scratch"),
]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Person] = {}
        self.clue: Optional[Clue] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, person: Person) -> Person:
        self.entities[person.id] = person
        return person

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def setup_world(params: StoryParams) -> World:
    world = World()
    pharaoh = world.add(Person(id=params.name, **PEOPLE["pharaoh"]))
    helper = world.add(Person(id=params.helper, **PEOPLE["helper"]))
    guard = world.add(Person(id="Hori", **PEOPLE["guard"]))

    culprit_label, visible_mark, true_source = next(
        item for item in CULPRITS if item[0] == params.culprit
    )
    clue_label = next(item[1] for item in CLUES if item[0] == params.clue)

    world.clue = Clue(
        id="clue",
        label=clue_label,
        place=params.room,
        owner=pharaoh.id,
        visible_mark=visible_mark,
        true_source=true_source,
    )

    world.facts.update(
        pharaoh=pharaoh,
        helper=helper,
        guard=guard,
        culprit=culprit_label,
        clue=world.clue,
        room=params.room,
        misunderstanding=False,
        solved=False,
    )
    return world


def tell_story(world: World) -> None:
    f = world.facts
    pharaoh: Person = f["pharaoh"]
    helper: Person = f["helper"]
    guard: Person = f["guard"]
    clue: Clue = f["clue"]

    pharaoh.memes["worry"] = 1
    pharaoh.memes["pride"] = 1
    world.say(
        f"In the palace, {pharaoh.id} the Pharaoh found a {clue.label} near {clue.place}."
    )
    world.say(
        f"{pharaoh.id} frowned. \"Someone is stealing from my rooms,\" {pharaoh.pronoun()} said."
    )

    world.para()
    helper.memes["curiosity"] = 1
    world.say(
        f"{helper.id} looked closer and spotted {clue.visible_mark} on the floor."
    )
    world.say(
        f"{helper.id} thought the mark meant the treasure thief had worn dusty shoes."
    )

    world.para()
    pharaoh.memes["fear"] = 1
    world.say(
        f"{guard.id} searched the hall, but the hall was too quiet to prove anything."
    )
    world.say(
        f"{pharaoh.id} began to suspect the guard, then the cook, then even {helper.id}."
    )
    f["misunderstanding"] = True

    world.para()
    culprit_label = f["culprit"]
    world.say(
        f"At last, {helper.id} found the real answer: {clue.true_source}."
    )
    world.say(
        f"{culprit_label.capitalize()} had made the mark by accident, so it was not a thief at all."
    )
    world.say(
        f"{pharaoh.id} nodded and put away {pharaoh.possessive()} sharp guess."
    )

    world.para()
    pharaoh.memes["relief"] = 1
    f["solved"] = True
    world.say(
        f"The Pharaoh thanked {helper.id} and {guard.id} for looking carefully."
    )
    world.say(
        f"That night, the palace was calm again, and the little {clue.label} was only a clue, not a crime."
    )


def valid_choices() -> list[tuple[str, str, str]]:
    return [(room, clue[0], culprit[0]) for room in ROOMS for clue in CLUES for culprit in CULPRITS]


def explain_invalid(room: str, clue: str, culprit: str) -> str:
    if room not in ROOMS:
        raise StoryError("Unknown room for the palace mystery.")
    if clue not in {c[0] for c in CLUES}:
        raise StoryError("Unknown clue type for this world.")
    if culprit not in {c[0] for c in CULPRITS}:
        raise StoryError("Unknown culprit source for this world.")
    return "That combination cannot support a clean misunderstanding."


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for children about a pharaoh in {f["room"]} who spots a {f["clue"].label}.',
        f"Tell a mystery where the Pharaoh first blames the wrong person, then learns the real source of the mark.",
        f'Write a gentle palace detective story that includes a "{f["clue"].label}" and ends with everyone calm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pharaoh: Person = f["pharaoh"]
    helper: Person = f["helper"]
    clue: Clue = f["clue"]
    return [
        QAItem(
            question=f"What did {pharaoh.id} find in {f['room']}?",
            answer=f"{pharaoh.id} found a {clue.label} near {f['room']}.",
        ),
        QAItem(
            question=f"Who looked closely at the clue for the Pharaoh?",
            answer=f"{helper.id} looked closely and tried to make sense of the {clue.label}.",
        ),
        QAItem(
            question=f"Why was this a misunderstanding?",
            answer=(
                f"It was a misunderstanding because {pharaoh.id} first thought someone was stealing, "
                f"but the {clue.label} turned out to come from {clue.true_source}."
            ),
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=(
                f"The mystery ended when {helper.id} found the real source of the clue and "
                f"{pharaoh.id} stopped blaming the wrong person."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pharaoh?",
            answer="A pharaoh was an ancient ruler of Egypt, like a king who lived long ago.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="Why do detectives look carefully?",
            answer="Detectives look carefully so they do not make a wrong guess about what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for room in ROOMS:
        lines.append(asp.fact("room", room))
    for clue, _, _ in CULPRITS:
        lines.append(asp.fact("culprit", clue))
    for clue, _ in CLUES:
        lines.append(asp.fact("clue_kind", clue))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(R, C, U) :- room(R), clue_kind(C), culprit(U).
#show valid_story/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Pharaoh misunderstanding whodunit story world.")
    ap.add_argument("--place", choices=ROOMS)
    ap.add_argument("--clue", choices=[c[0] for c in CLUES])
    ap.add_argument("--culprit", choices=[c[0] for c in CULPRITS])
    ap.add_argument("--name", default="Nefru")
    ap.add_argument("--helper", default="Sefi")
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
    room = args.place or rng.choice(ROOMS)
    clue = args.clue or rng.choice([c[0] for c in CLUES])
    culprit = args.culprit or rng.choice([c[0] for c in CULPRITS])
    if args.place and args.clue and args.culprit:
        if (args.place, args.clue, args.culprit) not in valid_choices():
            raise StoryError(explain_invalid(args.place, args.clue, args.culprit))
    return StoryParams(
        seed=args.seed,
        name=args.name,
        helper=args.helper,
        culprit=culprit,
        clue=clue,
        room=room,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
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
        print("--- trace ---")
        for key, value in sample.world.facts.items():
            if key in {"pharaoh", "helper", "guard"}:
                print(f"{key}: {value.id} ({value.role})")
            elif key == "clue":
                print(f"clue: {value.label} in {value.place}")
            else:
                print(f"{key}: {value}")
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    program = asp_program()
    models = asp.solve(program, models=1)
    if not models:
        print("ASP failed: no model")
        return 1
    print("OK: ASP program produced a model.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.solve(asp_program(), models=0)
        atoms = sorted({tuple(a.arguments) for m in models for a in []})
        print(f"{len(models)} model(s) available.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for room in ROOMS:
            for clue, _, culprit in CULPRITS:
                params = StoryParams(seed=base_seed, name=args.name, helper=args.helper, culprit=culprit, clue=clue, room=room)
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
