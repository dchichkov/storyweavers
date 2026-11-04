#!/usr/bin/env python3
"""
A small, stand-alone whodunit storyworld about a missing garden bell.

A mistaken message sends the young detectives looking in the wrong place.
Curiosity, careful questions, and kind advice help them discover that the bell
has not been stolen at all: a breeze has carried it into a basket of soft
garden clippings.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child: str
    partner: str
    gardener: str
    animal: str
    place: str
    clue: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CHILDREN = ["Luna", "Milo", "Nia", "Theo", "Pippa", "Ravi"]
PARTNERS = ["Bea", "Ollie", "Jun", "Kit", "Sasha", "Tess"]
GARDENERS = ["Aunt Fern", "Mr. Moss", "Gran Ivy", "Nana Rose"]
ANIMALS = ["a robin", "a squirrel", "a rabbit", "a curious cat"]
PLACES = ["the school garden", "the cottage garden", "the park greenhouse"]
CLUES = ["a trail of damp leaves", "a silver thread", "three tiny petals", "a faint ringing sound"]

# The question is always solvable: the gardeners' basket is the true location,
# and each clue is something the detectives can reasonably notice there.
VALID_CLUES = {
    ("a trail of damp leaves", "the school garden"),
    ("a silver thread", "the cottage garden"),
    ("three tiny petals", "the park greenhouse"),
    ("a faint ringing sound", "the school garden"),
    ("a faint ringing sound", "the cottage garden"),
    ("a trail of damp leaves", "the park greenhouse"),
}


ASP_RULES = r"""
#show valid/2.
#show valid_case/3.

clue(C) :- clue_name(C).
place(P) :- place_name(P).

valid(C, P) :- clue_name(C), place_name(P), leads_to_basket(C, P).
valid_case(C, P, A) :- valid(C, P), animal_name(A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for clue, place in sorted(VALID_CLUES):
        lines.append(asp.fact("leads_to_basket", clue, place))
    for clue in CLUES:
        lines.append(asp.fact("clue_name", clue))
    for place in PLACES:
        lines.append(asp.fact("place_name", place))
    for animal in ANIMALS:
        lines.append(asp.fact("animal_name", animal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted(VALID_CLUES)


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted((clue, place) for clue, place in asp.atoms(model, "valid"))


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    clingo_pairs = set(asp_valid_combos())
    if python_pairs == clingo_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} cases).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_pairs - clingo_pairs:
        print("  only in Python:", sorted(python_pairs - clingo_pairs))
    if clingo_pairs - python_pairs:
        print("  only in clingo:", sorted(clingo_pairs - python_pairs))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A curious, child-friendly garden whodunit storyworld."
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--gardener", choices=GARDENERS)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")

    choices = valid_combos()
    if args.place:
        choices = [pair for pair in choices if pair[1] == args.place]
    if args.clue:
        choices = [pair for pair in choices if pair[0] == args.clue]
    if not choices:
        raise StoryError(
            "No story fits those options: that clue cannot lead to the garden basket in that place."
        )
    clue, place = rng.choice(choices)
    return StoryParams(
        child=args.child or rng.choice(CHILDREN),
        partner=args.partner or rng.choice(PARTNERS),
        gardener=args.gardener or rng.choice(GARDENERS),
        animal=args.animal or rng.choice(ANIMALS),
        place=place,
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    if (params.clue, params.place) not in VALID_CLUES:
        raise StoryError(
            "That clue and place do not make a reasonable solution to the garden mystery."
        )

    w = World()
    child = w.add(
        Entity(
            id="child",
            kind="character",
            label=params.child,
            memes={"curiosity": 0.3, "confidence": 0.4},
        )
    )
    partner = w.add(
        Entity(id="partner", kind="character", label=params.partner, memes={"curiosity": 0.5})
    )
    gardener = w.add(
        Entity(id="gardener", kind="character", label=params.gardener, memes={"worry": 0.4})
    )
    animal = w.add(
        Entity(id="animal", kind="animal", label=params.animal, memes={"innocence": 1.0})
    )
    bell = w.add(
        Entity(
            id="bell",
            kind="object",
            label="the little brass garden bell",
            meters={"location_known": 0.0},
            memes={"mystery": 1.0},
        )
    )
    basket = w.add(
        Entity(
            id="basket",
            kind="object",
            label="the basket of soft garden clippings",
            meters={"bell_inside": 0.0},
        )
    )

    w.say(
        f"In {params.place}, {params.gardener} hung a little brass bell beside the gate. "
        f"{params.child} and {params.partner} had come to help water the flowers, while {params.animal} watched from the path."
    )
    w.say(
        f"When the bell was gone, {params.gardener} frowned. “I told someone to take it in,” "
        f"{params.gardener} said, “but I may have said to take the *pail* in.” "
        f"{params.partner} blinked. “Could that mix-up be the whole mystery?”"
    )

    w.para()
    child.memes["curiosity"] = 1.0
    partner.memes["curiosity"] = 1.0
    w.say(
        f"{params.child} looked closely instead of blaming the animal. “Let’s follow what we can see,” "
        f"{params.child} advised. {params.partner} nodded, and together they noticed {params.clue} leading toward the garden beds."
    )
    w.say(
        f"At the far end, {params.animal} nosed a basket but did not run away. "
        f"{params.gardener} asked, “Should we tip it out?” “No,” said {params.child}. "
        f"“Let’s lift the clippings gently, so nothing gets hurt.”"
    )

    w.para()
    bell.meters["location_known"] = 1.0
    bell.memes["mystery"] = 0.0
    basket.meters["bell_inside"] = 1.0
    gardener.memes["worry"] = 0.0
    child.memes["confidence"] = 1.0
    w.say(
        f"Under the soft leaves lay the bell, safe and clean. A breeze had swung it off its hook, "
        f"and it had landed in the basket. The animal had only been sniffing the leafy smell."
    )
    w.say(
        f"{params.gardener} smiled. “Thank you for asking questions before guessing.” "
        f"{params.partner} hung the bell back on its hook, and {params.child} tied it with a short, sturdy ribbon."
    )
    w.say(
        f"That evening, the bell rang above the flowers whenever the breeze passed. "
        f"{params.animal} settled nearby, and the two young detectives watered the beds, pleased that a small misunderstanding had ended in a kinder garden."
    )

    w.facts.update(
        clue=params.clue,
        place=params.place,
        solution="The breeze knocked the bell into the basket of garden clippings.",
        misunderstanding="The gardener mixed up a request about the bell and the pail.",
        helper=params.partner,
        animal=params.animal,
        resolved=True,
    )

    prompts = [
        "Write a child-friendly garden whodunit about a missing bell, a misunderstanding, and curious young detectives.",
        f"Tell a complete mystery in which {params.child} advises everyone to follow a clue instead of blaming {params.animal}.",
        "Include a brief back-and-forth conversation, a gentle solution, and a happy ending that shows what changed.",
    ]
    story_qa = [
        QAItem(
            question="What went missing from the garden?",
            answer="The little brass garden bell went missing from its hook by the gate.",
        ),
        QAItem(
            question="What misunderstanding added to the mystery?",
            answer=(
                f"{params.gardener} had mixed up a request about bringing in the bell with a request "
                "about bringing in the pail."
            ),
        ),
        QAItem(
            question="How did the detectives discover where the bell was?",
            answer=(
                f"{params.child} advised everyone to follow clues, and the detectives followed "
                f"{params.clue} to the basket of garden clippings."
            ),
        ),
        QAItem(
            question="What had happened to the bell?",
            answer=(
                "A breeze had swung the bell off its hook, and it landed safely in the basket "
                "of soft garden clippings."
            ),
        ),
        QAItem(
            question="How did the ending show that the problem was solved?",
            answer=(
                f"{params.partner} hung the bell back on its hook, and {params.child} secured it "
                "with a sturdy ribbon so it could ring above the flowers again."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and asks careful questions to learn what happened.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people hear or understand something differently from what was meant.",
        ),
        QAItem(
            question="Why is it helpful to follow clues?",
            answer="Following clues can help people find out what happened before they decide who is responsible.",
        ),
        QAItem(
            question="How can a breeze move a hanging object?",
            answer="A breeze can push or swing a light object, especially if it is hanging loosely.",
        ),
    ]

    return StorySample(
        params=params,
        story=w.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=w,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.kind:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            child="Luna",
            partner="Bea",
            gardener="Aunt Fern",
            animal="a robin",
            place="the school garden",
            clue="a trail of damp leaves",
        ),
        StoryParams(
            child="Milo",
            partner="Ollie",
            gardener="Mr. Moss",
            animal="a squirrel",
            place="the cottage garden",
            clue="a silver thread",
        ),
        StoryParams(
            child="Nia",
            partner="Jun",
            gardener="Gran Ivy",
            animal="a rabbit",
            place="the park greenhouse",
            clue="three tiny petals",
        ),
        StoryParams(
            child="Theo",
            partner="Kit",
            gardener="Nana Rose",
            animal="a curious cat",
            place="the school garden",
            clue="a faint ringing sound",
        ),
    ]


CURATED = build_curated()


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program("#show valid/2.\n#show valid_case/3."))
        return
    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                print("FAIL: generated story is missing prose or story questions.")
                sys.exit(1)
            if "?”" not in sample.story and "?" not in sample.story:
                print("FAIL: generated story is missing spoken dialogue.")
                sys.exit(1)
        print(f"OK: generated and checked {len(CURATED)} complete stories.")
        return
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} reasonable (clue, place) cases:\n")
        for clue, place in pairs:
            print(f"  {clue} -> {place}")
        return

    if args.n < 1 and not args.all:
        raise StoryError("The number of stories must be at least one.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for offset in range(args.n):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child}: the missing garden bell"
        elif len(samples) > 1:
            header = f"### mystery {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
