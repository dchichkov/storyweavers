#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


@dataclass
class StoryParams:
    name: str
    helper: str
    number: int
    seed: int | None = None


@dataclass(frozen=True)
class Mystery:
    object_name: str
    hiding_place: str
    clue: str
    answer: str
    rhyme: str
    reveal: str


NAMES = ["Luna", "Milo", "Nia", "Pip", "Tara"]
HELPERS = ["a kind fox", "a gentle crow", "a patient mouse", "a thoughtful rabbit"]
NUMBERS = [4, 5, 6, 7, 8]

MYSTERIES = [
    Mystery(
        "the blue marble",
        "beneath the round rug",
        "three tiny chalk stars beside the door",
        "The stars marked the third step, and the marble was beneath the round rug.",
        "Look low, look slow, kindness helps us know.",
        "Luna lifted the rug and found the blue marble shining like a little moon.",
    ),
    Mystery(
        "the silver bell",
        "inside the basket of clean scarves",
        "a thread of silver ribbon near the window",
        "The ribbon led to the basket, where the silver bell rested under the scarves.",
        "Search with care, clues hide there.",
        "They moved the scarves gently and heard the silver bell give one bright ring.",
    ),
    Mystery(
        "the red button",
        "beside the wooden counting board",
        "four neat dots of red paint on the floor",
        "The red dots made a trail to the counting board, where the red button waited.",
        "Count each spot, find the dot.",
        "Behind the counting board sat the red button, safe and round.",
    ),
    Mystery(
        "the paper star",
        "between two pages of the math book",
        "a folded corner on the page about pairs",
        "The folded corner pointed to the math book, where the paper star lay between two pages.",
        "Read the page, turn it with care.",
        "Luna opened the book and found the paper star tucked in its middle.",
    ),
]

MORALS = [
    "Kindness makes a mystery easier because a helper feels safe enough to share every clue.",
    "Math can guide our steps, but kindness helps us notice how others feel.",
    "Repeating a careful plan is not boring; it helps everyone search safely.",
]


def validate(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError(f"unknown name: {params.name}")
    if params.helper not in HELPERS:
        raise StoryError(f"unknown helper: {params.helper}")
    if params.number not in NUMBERS:
        raise StoryError(f"number must be one of {NUMBERS}")
    if params.number < 2:
        raise StoryError("the mystery needs at least two counting steps")


def solve_math(number: int) -> tuple[int, int, int]:
    first = number - 2
    second = 2
    total = first + second
    if total != number:
        raise StoryError("the counting riddle does not balance")
    return first, second, total


def build_world(params: StoryParams) -> World:
    validate(params)
    rng = random.Random(params.seed if params.seed is not None else sum(map(ord, params.name)))
    mystery = rng.choice(MYSTERIES)
    moral = rng.choice(MORALS)
    first, second, total = solve_math(params.number)

    world = World()
    hero = world.add(Entity(params.name, "child", params.name))
    helper = world.add(Entity("helper", "animal", params.helper))
    clue = world.add(Entity("clue", "sign", mystery.clue))
    missing = world.add(Entity("missing", "object", mystery.object_name))
    hero.meters.update(steps=0, worry=1)
    helper.memes.update(kindness=1, patience=1)
    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        missing=missing,
        mystery=mystery,
        first=first,
        second=second,
        total=total,
        moral=moral,
    )
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    first, second, total = f["first"], f["second"], f["total"]

    world.trace.append("begin: the object is missing")
    world.trace.append(f"math: {first} + {second} = {total}")
    world.trace.append("kindness: helper invites a calm search")
    world.trace.append("repetition: search words are spoken twice")
    world.trace.append("clue: " + mystery.clue)
    world.trace.append("reveal: " + mystery.answer)

    story = [
        f"{hero.label} was solving a small math mystery in the quiet room when {mystery.object_name} disappeared.",
        f"On the table were {first} yellow counters and {second} green counters. {hero.label} counted them aloud: "
        f"“{first} plus {second} makes {total}.”",
        f"{hero.label} looked worried. “I cannot find it.” {helper.label.capitalize()} came close and said, "
        "“We can search kindly. No blaming, no rushing.”",
        f"Together they repeated the plan: “Count, look, care. Count, look, care.” "
        f"They counted {first} counters, then {second} counters, and checked the total again.",
        f"Near the doorway they noticed {mystery.clue}. {helper.label.capitalize()} said, "
        f"“The clue may be small, but small clues can tell a tall tale.”",
        f"{hero.label} followed the clue one step at a time. {mystery.rhyme}",
        mystery.reveal,
        f"{hero.label} smiled. “The mystery is solved, and you helped me stay calm.” "
        f"{helper.label.capitalize()} answered, “A kind search is a smart search.”",
        f"They put the counters back in their box and repeated their lesson: “Count, look, care. "
        f"Count, look, care.” {f['moral']}",
    ]
    world.facts["story"] = " ".join(story)
    hero.meters["steps"] = total
    hero.meters["worry"] = 0
    hero.memes["confidence"] = 1
    helper.memes["joy"] = 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly math mystery using rhyme, repetition, and kindness.",
        f"Tell a mystery about {f['hero'].label} finding {f['missing'].label} with {f['helper'].label}.",
        f"Include the math fact {f['first']} + {f['second']} = {f['total']} and the repeated words “Count, look, care.”",
    ]


def story_questions(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            "What was missing?",
            f"{f['missing'].label.capitalize()} was missing.",
        ),
        QAItem(
            "What math problem did the characters solve?",
            f"They solved {f['first']} + {f['second']} = {f['total']}.",
        ),
        QAItem(
            "What clue did they notice?",
            f"They noticed {mystery.clue}.",
        ),
        QAItem(
            "How did the helper show kindness?",
            "The helper stayed calm, invited a gentle search, and did not blame anyone.",
        ),
        QAItem(
            "Where was the missing object?",
            mystery.answer,
        ),
        QAItem(
            "What words did they repeat?",
            "They repeated, “Count, look, care.”",
        ),
        QAItem(
            "What lesson did they learn?",
            f"{f['moral']}",
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem("What is addition?", "Addition is putting numbers together to find how many there are in all."),
        QAItem("What is a clue?", "A clue is a small sign or piece of information that helps solve a mystery."),
        QAItem("Why can repetition help?", "Repetition can help people remember a plan or notice an important idea."),
        QAItem("What is kindness?", "Kindness means treating others with care, patience, and respect."),
        QAItem("What is a rhyme?", "A rhyme is a pair of words that have matching or similar ending sounds."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append("events:")
    lines.extend(f"  - {event}" for event in world.trace)
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.facts["story"],
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ACTIONS = {
    "count": {"kind": "math", "power": 1},
    "look": {"kind": "clue", "power": 1},
    "care": {"kind": "kindness", "power": 1},
}
MYSTERY_OBJECTS = {item.object_name: item.hiding_place for item in MYSTERIES}


def asp_facts() -> str:
    import asp
    lines = []
    for action, data in ACTIONS.items():
        lines.append(asp.fact("action", action))
        lines.append(asp.fact("kind", action, data["kind"]))
    for name, place in MYSTERY_OBJECTS.items():
        lines.append(asp.fact("object", name))
        lines.append(asp.fact("place", name, place))
    return "\n".join(lines)


ASP_RULES = r"""
ready :- action(count), kind(count,math), action(look), kind(look,clue),
         action(care), kind(care,kindness).
valid_mystery(O) :- object(O), place(O,P), ready.
#show valid_mystery/1.
"""


def asp_program(show: str = "#show valid_mystery/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str]]:
    return [(name,) for name in sorted(MYSTERY_OBJECTS)]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    actual = sorted(set(asp.atoms(model, "valid_mystery")))
    expected = valid_combos()
    if actual != expected:
        print(f"ASP mismatch: expected {expected}, got {actual}")
        return 1
    for seed in range(5):
        sample = generate(StoryParams("Luna", "a kind fox", 4, seed))
        if "Count, look, care" not in sample.story:
            print("generated story verification failed")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(expected)} mysteries).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A math rhyme repetition kindness mystery.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--number", type=int, choices=NUMBERS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    number = args.number or rng.choice(NUMBERS)
    return StoryParams(name=name, helper=helper, number=number, seed=args.seed)


CURATED = [
    StoryParams("Luna", "a kind fox", 4, 11),
    StoryParams("Milo", "a gentle crow", 5, 22),
    StoryParams("Nia", "a patient mouse", 6, 33),
    StoryParams("Pip", "a thoughtful rabbit", 7, 44),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "valid_mystery"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
